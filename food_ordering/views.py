from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Food, Order
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, ReviewForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
import requests  
from django.db.models import Avg, Count
from .models import Review
from .forms import ReviewForm
from .models import Food, Review
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
from .forms import UserProfileForm
from .forms import ProfileUpdateForm, PasswordChangeForm


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != "Completed":  # Ensure completed orders cannot be canceled
        order.status = "Cancelled"
        order.save()
        
        messages.success(request, "Your order has been cancelled.")
    else:
        messages.error(request, "Completed orders cannot be cancelled.")

    return redirect("order_history")

@login_required
def payment_success(request):
    reference = request.GET.get("reference", "")

    print("🔹 Payment success function called!")  
    print("🔹 Reference:", reference)  

    # ✅ Verify payment with Paystack
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    result = response.json()

    print("🔹 Paystack response:", result)  

    if result["status"] and result["data"]["status"] == "success":
        print("✅ Payment verified successfully!")  

        # ✅ Retrieve food ID and quantity from session
        food_id = request.session.get("food_id", None)
        quantity = request.session.get("quantity", 1)

        # ✅ Debugging print statements
        print("🔹 Food ID from session:", food_id)
        print("🔹 Quantity from session:", quantity)

        if not food_id:
            messages.error(request, "Payment verified but no food order found.")
            return redirect("menu")

        # ✅ Convert food_id and quantity to integer before using them
        food_id = int(food_id)
        quantity = int(quantity)

        food = get_object_or_404(Food, id=food_id)

        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to complete your order.")
            return redirect("login")

        print("🔹 User authenticated:", request.user)

        # ✅ Save the order in the database now that payment is confirmed
        order = Order.objects.create(
            user=request.user,
            food=food,
            quantity=quantity,
            status="Pending"
        )

        # ✅ Remove session data to prevent duplicate orders
        request.session.pop("food_id", None)
        request.session.pop("quantity", None)

        print("✅ Order saved after payment:", order)

        return redirect("order_history")

    else:
        print("❌ Payment verification failed!")  
        messages.error(request, "Payment verification failed. Please try again.")
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
    return JsonResponse({"message": "Order status updated successfully!"})

def menu(request):
    query = request.GET.get("q", "")
    food_type = request.GET.get("food_type", "")

    foods = Food.objects.all()

    if query:
        foods = foods.filter(name__icontains=query)

    if food_type:
        foods = foods.filter(food_type=food_type)

    # ✅ Annotate each food with average rating & review count
    foods = foods.annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))

    return render(request, 'food_ordering/menu.html', {'foods': foods})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')  # Show all orders
    return render(request, 'food_ordering/order_history.html', {'orders': orders})

@login_required
def order_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))

        # ✅ Save the order immediately (NO PAYSTACK)
        order = Order.objects.create(
            user=request.user,
            food=food,
            quantity=quantity,
            status="Pending"  # Order starts as "Pending"
        )

        print("✅ Order created successfully:", order)  # Debugging

        return redirect("order_history")  # ✅ Redirect to order history immediately

    return render(request, "food_ordering/checkout.html", {"food": food})


def home(request):
    return render(request, 'food_ordering/home.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in after signup
            return redirect("home")  # Redirect to homepage
    else:
        form = RegisterForm()
    return render(request, "food_ordering/register.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
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
    
    # Prevent duplicate reviews
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


@login_required
def update_profile_picture(request):
    if request.method == "POST" and request.FILES.get("profile_picture"):
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.profile_picture = request.FILES["profile_picture"]
        user_profile.save()
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "No image uploaded"})
