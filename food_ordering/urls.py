from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('order/<int:food_id>/', views.order_food, name='order_food'),
    path('order-history/', views.order_history, name='order_history'),
    path('manage-food/', views.manage_food, name='manage_food'),
    path('fetch-order-status/', views.fetch_order_status, name='fetch_order_status'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('update-order-status/<int:order_id>/<str:status>/', views.update_order_status, name='update_order_status'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('profile/', views.user_profile, name='user_profile'),
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('review/<int:food_id>/', views.submit_review, name="submit_review"),
    path("submit-review/<int:food_id>/", views.submit_review, name="submit_review"),
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
    path("login/", views.user_login, name="login"),
    path("checkout/<int:food_id>/", views.checkout, name="checkout"),
    path("manage-orders/", views.manage_orders, name="manage_orders"),

]


