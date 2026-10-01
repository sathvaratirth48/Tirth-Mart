from django.db import models


class DeliveryBoyStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    BUSY = "busy", "Busy"
    OFFLINE = "offline", "Offline"


class VehicleType(models.TextChoices):
    BIKE = "bike", "Bike"
    BICYCLE = "bicycle", "Bicycle"
    SCOOTER = "scooter", "Scooter"


class AssignmentStatus(models.TextChoices):
    ASSIGNED = "assigned", "Assigned"
    PICKED_UP = "picked_up", "Picked Up"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
