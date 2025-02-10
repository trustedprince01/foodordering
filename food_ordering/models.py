from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings


class Food(models.Model):
    FOOD_TYPES = [
        ("Veg", "Vegetarian"),
        ("Non-Veg", "Non-Vegetarian"),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="food_images/")
    food_type = models.CharField(max_length=10, choices=FOOD_TYPES, default="Veg")  # ✅ Add this

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)  # ✅ Add this if missing
    phone = models.CharField(max_length=15, blank=True, null=True)  # ✅ Add this if missing
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True, default="profile_pictures/default_profile.jpg")

    def __str__(self):
        return self.user.usernameclear


class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    def total_price(self):
        return self.food.price * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.food.name} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save method but disable email sending for now"""
        if self.pk:  # Check if the order already exists
            original = Order.objects.get(pk=self.pk)
            if original.status != self.status:
                print(f"✅ Order status changed: {original.status} → {self.status}")  # Debugging
                # self.send_status_email()  # ❌ Disable email sending
        super().save(*args, **kwargs)  # ✅ Correct indentation

    def send_status_email(self):
        """Send an email when the order status is updated"""
        subject = f"Order Status Update: {self.food.name}"
        message = f"""
        Hello {self.user.username},

        Your order for {self.food.name} (x{self.quantity}) has been updated.

        ✅ New Status: {self.status}
        💰 Total Price: ${self.total_price()}

        Thank you for using our service!
        """
        send_mail(subject, message, settings.EMAIL_HOST_USER, [self.user.email])


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "food")  # Prevent duplicate reviews

