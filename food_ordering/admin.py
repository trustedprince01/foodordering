from django.contrib import admin
from .models import Food, Order, Review, UserProfile
from django.db.models import Sum


# ✅ Sales Summary (without Order registration)
class SalesSummaryAdmin(admin.ModelAdmin):
    change_list_template = "admin/sales_summary.html"

    def changelist_view(self, request, extra_context=None):
        total_revenue = Order.objects.aggregate(total=Sum("food__price"))["total"] or 0
        total_orders = Order.objects.count()
        extra_context = extra_context or {}
        extra_context["total_revenue"] = f"${total_revenue:.2f}"
        extra_context["total_orders"] = total_orders

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "available", "category")
    list_filter = ("available", "category")
    search_fields = ("name", "description")
    list_editable = ("available", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "food", "quantity", "total_price", "status", "ordered_at")
    list_filter = ("status", "ordered_at")  # Filter by status
    search_fields = ("user__username", "food__name")  # Search orders
    ordering = ("-ordered_at",)  # Show latest orders first
    list_editable = ("status",)  # Allow quick edits on status

    def total_price(self, obj):
        if obj.food is None:
            return "$0.00"
        return f"${obj.food.price * obj.quantity:.2f}"

    COMPLETED_STATUSES = ["Completed", "Cancelled"]

    def get_readonly_fields(self, request, obj=None):
        """Prevent users from editing orders once completed/cancelled"""
        if obj and obj.status in self.COMPLETED_STATUSES:
            return ["status", "user", "food", "quantity", "ordered_at"]
        return super().get_readonly_fields(request, obj)



@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "food", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "food__name")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "phone")
