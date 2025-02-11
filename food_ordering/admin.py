from django.contrib import admin
from .models import Food, Order, Review

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "available", "category")
    list_filter = ("available", "category")
    search_fields = ("name", "description")

# ✅ Order Admin Panel
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "food", "quantity", "total_price", "status", "ordered_at")
    list_filter = ("status", "ordered_at")
    search_fields = ("user__username", "food__name")
    ordering = ("-ordered_at",)
    list_editable = ("status",)  # Allows editing status directly in admin panel

    def get_readonly_fields(self, request, obj=None):
        """Prevent users from editing orders once completed/cancelled"""
        if obj and obj.status in ["Completed", "Cancelled"]:
            return ["status", "user", "food", "quantity", "ordered_at"]
        return super().get_readonly_fields(request, obj)


# ✅ Review Admin Panel
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "food", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "food__name")
