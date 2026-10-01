from django.contrib import admin

from .models import DeliveryBoy, OrderAssignment


@admin.register(DeliveryBoy)
class DeliveryBoyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "vehicle_type", "vehicle_number", "status", "is_verified", "joined_at")
    list_filter = ("status", "vehicle_type", "is_verified")
    search_fields = ("user__username", "user__phone_number", "vehicle_number")
    list_editable = ("status", "is_verified")
    ordering = ("-joined_at",)


@admin.register(OrderAssignment)
class OrderAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "delivery_boy", "status", "assigned_at", "delivered_at")
    list_filter = ("status",)
    search_fields = ("order__id", "delivery_boy__user__username")
    ordering = ("-assigned_at",)
    readonly_fields = ("assigned_at",)
