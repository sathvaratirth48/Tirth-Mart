from django.db import models

from app_modules.userapp.models import CustomUser, Order

from .choices import AssignmentStatus, DeliveryBoyStatus, VehicleType


class DeliveryBoy(models.Model):
    AVAILABLE = DeliveryBoyStatus.AVAILABLE
    BUSY = DeliveryBoyStatus.BUSY
    OFFLINE = DeliveryBoyStatus.OFFLINE
    STATUS_CHOICES = DeliveryBoyStatus.choices

    BIKE = VehicleType.BIKE
    BICYCLE = VehicleType.BICYCLE
    SCOOTER = VehicleType.SCOOTER
    VEHICLE_CHOICES = VehicleType.choices

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="delivery_profile")
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.BIKE)
    vehicle_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=DeliveryBoyStatus.choices, default=DeliveryBoyStatus.OFFLINE)
    is_verified = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Delivery Boy"
        verbose_name_plural = "Delivery Boys"

    def __str__(self):
        return f"{self.user.username} [{self.status}]"

    def go_available(self):
        self.status = DeliveryBoyStatus.AVAILABLE
        self.save(update_fields=["status"])

    def go_offline(self):
        self.status = DeliveryBoyStatus.OFFLINE
        self.save(update_fields=["status"])

    def go_busy(self):
        self.status = DeliveryBoyStatus.BUSY
        self.save(update_fields=["status"])


class OrderAssignment(models.Model):
    ASSIGNED = AssignmentStatus.ASSIGNED
    PICKED_UP = AssignmentStatus.PICKED_UP
    OUT_FOR_DELIVERY = AssignmentStatus.OUT_FOR_DELIVERY
    DELIVERED = AssignmentStatus.DELIVERED
    FAILED = AssignmentStatus.FAILED
    STATUS_CHOICES = AssignmentStatus.choices

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="assignment")
    delivery_boy = models.ForeignKey(DeliveryBoy, on_delete=models.SET_NULL, null=True, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus.choices, default=AssignmentStatus.ASSIGNED)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"Order #{self.order.id} -> {self.delivery_boy}"
