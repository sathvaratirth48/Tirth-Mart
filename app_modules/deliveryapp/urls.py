from django.urls import path

from app_modules.deliveryapp import views

urlpatterns = [
    path("register/", views.delivery_register, name="delivery_register"),
    path("pending/", views.delivery_pending, name="delivery_pending"),
    path("dashboard/", views.delivery_dashboard, name="delivery_dashboard"),
    path("assignments/", views.assignment_list, name="delivery_assignment_list"),
    path("assignments/<int:pk>/", views.assignment_detail, name="delivery_assignment_detail"),
    path("toggle/", views.toggle_availability, name="delivery_toggle"),
    path("api/notifications/recent/", views.delivery_notif_recent, name="delivery_notif_recent"),
    path("api/notifications/<int:pk>/read/", views.delivery_notif_mark_read, name="delivery_notif_mark_read"),
    path("notifications/clear/", views.delivery_notif_clear, name="delivery_notif_clear"),
]
