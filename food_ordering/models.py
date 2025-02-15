from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from cloudinary.models import CloudinaryField

class Food(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(
        max_length=50,
        choices=[("Veg", "Veg"), ("Non-Veg", "Non-Veg")],
        default="Veg"
    )
    available = models.BooleanField(default=True)  
    image = CloudinaryField('image', blank=True, null=True)  # ✅ Cloudinary storage

    def __str__(self):
        return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = CloudinaryField('profile_pictures', blank=True, null=True)  # ✅ Store in Cloudinary

    def __str__(self):
        return self.user.username

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
        if self.pk:
            original = Order.objects.get(pk=self.pk)
            if original.status != self.status:
                print(f"✅ Order status changed: {original.status} → {self.status}")
                # self.send_status_email()  # Enable this if you want email notifications
        super().save(*args, **kwargs)

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
