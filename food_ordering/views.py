from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db.models import Avg, Count
import requests
from .models import Food, Order, Review, UserProfile
from .forms import RegisterForm, ReviewForm, UserProfileForm, ProfileUpdateForm
from django.contrib.auth.models import User
from django.http import HttpResponse
import cloudinary.uploader
from django.views.decorators.csrf import csrf_exempt
from food_ordering.models import UserProfile
from django.db import IntegrityError



@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != "Completed":
        order.status = "Cancelled"
        order.save()
        messages.success(request, "Your order has been cancelled.")
    else:
        messages.error(request, "Completed orders cannot be cancelled.")
    return redirect("order_history")

@login_required
def payment_success(request):
    reference = request.GET.get("reference", "")

    if not reference:
        messages.error(request, "No payment reference provided.")
        return redirect("menu")

    # ✅ Verify payment with Paystack
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    response = requests.get(f"{settings.PAYSTACK_VERIFY_URL}{reference}", headers=headers)
    result = response.json()

    if result.get("status") and result["data"]["status"] == "success":
        # ✅ Payment verified, process order
        food_id = request.session.get("food_id")
        quantity = request.session.get("quantity", 1)

        if not food_id:
            messages.error(request, "Payment successful but no food order found.")
            return redirect("menu")

        food = get_object_or_404(Food, id=int(food_id))

        Order.objects.create(user=request.user, food=food, quantity=int(quantity), status="Pending")

        # ✅ Clear session to prevent duplicate orders
        request.session.pop("food_id", None)
        request.session.pop("quantity", None)

        messages.success(request, f"✅ Payment successful! Order for {food.name} placed.")
        return redirect("order_history")

    else:
        messages.error(request, "❌ Payment verification failed. Please try again.")
        return redirect("menu")


@login_required
def fetch_order_status(request):
    orders = Order.objects.filter(user=request.user)
    data = {"orders": [{"id": order.id, "status": order.status} for order in orders]}
    return JsonResponse(data)

@staff_member_required
def manage_food(request):
    return redirect('/admin/food_ordering/food/')

def update_order_status(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)
    order.status = status
    order.save()
    
    messages.success(request, f"✅ Order #{order.id} marked as {status}!")
    return redirect("manage_orders")  # ✅ Redirect to the Manage Orders page

def menu(request):
    query = request.GET.get("q", "")
    food_type = request.GET.get("food_type", "")
    foods = Food.objects.all()

    if query:
        foods = foods.filter(name__icontains=query)
    if food_type:
        foods = foods.filter(category=food_type)

    foods = foods.annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))
    return render(request, 'food_ordering/menu.html', {'foods': foods})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    return render(request, 'food_ordering/order_history.html', {'orders': orders})

@login_required
def order_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        Order.objects.create(user=request.user, food=food, quantity=quantity)
        messages.success(request, f"Your order for {food.name} has been placed!")
        return redirect("order_history")
    return render(request, "food_ordering/order_food.html", {"food": food})

def home(request):
    return render(request, 'food_ordering/home.html')

def register(request):
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password1"]

        full_name = f"{first_name} {last_name}"  # ✅ Combine first & last name

        # ✅ Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "❌ Username is already taken. Please choose another.")
            return redirect("register")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "❌ Email is already taken. Please choose another.")
            return redirect("register")

        try:
            # ✅ Create User & Save First & Last Name
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # ✅ Create UserProfile & Store Full Name
            UserProfile.objects.create(user=user, full_name=full_name)

            messages.success(request, "✅ Registration successful! You can now log in.")
            return redirect("login")  # Redirect to login after successful registration

        except IntegrityError:
            messages.error(request, "❌ An error occurred during registration. Try again.")
            return redirect("register")

    return render(request, "food_ordering/register.html")

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(f"✅ User {user.username} logged in!")  # Debug
            login(request, user)
            return redirect("menu")
        else:
            print("❌ Invalid username or password")  # Debug
    else:
        form = AuthenticationForm()
    return render(request, "food_ordering/login.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect("home")

def send_order_email(user, order):
    subject = "Order Confirmation"
    message = f"""
    Hello {user.username},

    Your order for {order.food.name} (x{order.quantity}) has been received.
    Total: ${order.total_price}

    Thank you for ordering!
    """
    recipient_list = [user.email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)

@login_required
def user_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("user_profile")
        if "update_password" in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully.")
                return redirect("user_profile")
    else:
        profile_form = ProfileUpdateForm(instance=user_profile)
        password_form = PasswordChangeForm(request.user)
    return render(request, "food_ordering/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form
    })

@staff_member_required
def manage_orders(request):
    orders = Order.objects.all().order_by("-ordered_at")  # Show newest orders first
    return render(request, "food_ordering/manage_orders.html", {"orders": orders})


@login_required
def submit_review(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    existing_review = Review.objects.filter(user=request.user, food=food).first()
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.food = food
            review.save()
            messages.success(request, "Review submitted successfully!")
            return redirect("menu")
    else:
        form = ReviewForm(instance=existing_review)
    return render(request, "food_ordering/review_form.html", {"form": form, "food": food})

@csrf_exempt  # Allow AJAX requests
@login_required
def update_profile_picture(request):
    if request.method == "POST" and request.FILES.get("profile_picture"):
        user_profile = request.user.userprofile
        uploaded_file = request.FILES["profile_picture"]

        # ✅ Upload image to Cloudinary
        upload_result = cloudinary.uploader.upload(uploaded_file)

        if upload_result.get("secure_url"):
            user_profile.profile_picture = upload_result["secure_url"]  # Save Cloudinary URL
            user_profile.save()
            return JsonResponse({"success": True, "image_url": upload_result["secure_url"]})

    return JsonResponse({"success": False, "error": "Upload failed"})


def login_user(request):  # ✅ Make sure this exists in views.py
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "✅ Logged in successfully!")
            return redirect("menu")
        else:
            messages.error(request, "❌ Invalid username or password!")
            return redirect("login")

    return render(request, "food_ordering/login.html")


@login_required
def checkout(request, food_id):
    food = get_object_or_404(Food, id=food_id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        total_price = food.price * quantity

        # ✅ Store food & quantity in session before payment
        request.session["food_id"] = food.id
        request.session["quantity"] = quantity

        # ✅ Paystack API request to initialize transaction
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "email": request.user.email,
            "amount": int(total_price * 100),  # Convert to kobo (Paystack requires amounts in kobo)
            "currency": "NGN",
            "callback_url": request.build_absolute_uri("/payment-success/"),
        }

        response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
        response_data = response.json()

        if response_data.get("status"):
            # ✅ Redirect to Paystack payment page
            return redirect(response_data["data"]["authorization_url"])
        else:
            # ❌ Payment initialization failed
            return render(request, "food_ordering/checkout.html", {"food": food, "error": "Payment failed. Try again."})

    return render(request, "food_ordering/checkout.html", {"food": food})

def create_admin_user(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@email.com", "admin123")
        return HttpResponse("✅ Admin user created successfully! Username: admin, Password: admin123")
    return HttpResponse("❌ Admin user already exists!")