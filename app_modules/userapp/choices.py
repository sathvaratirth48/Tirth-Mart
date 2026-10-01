"""
Centralised choice/enum definitions for userapp.

Using Django's ``TextChoices`` instead of raw list-of-tuples keeps the same
on-the-wire values (so no database schema change is required) while giving
us named constants, autocompletion and a single source of truth.
"""
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "Admin", "Admin"
    USER = "User", "User"
    DELIVERY = "Delivery", "Delivery"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    PAYMENT_SUCCESSFUL = "payment_successful", "Payment Successful"
    CONFIRMED = "confirmed", "Confirmed"
    PROCESSING = "processing", "Processing"
    ASSIGNED = "assigned", "Assigned"
    ACCEPTED = "accepted", "Accepted"
    PICKED_UP = "picked_up", "Picked Up"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
    NEAR_LOCATION = "near_location", "Near Location"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    RETURNED = "returned", "Returned"
    REFUNDED = "refunded", "Refunded"

    # Ordered progression used by the simulated auto-tracking poller.
    # Only "happy path" steps are auto-advanced; failure/cancel states are terminal.
    @classmethod
    def auto_progression(cls):
        return [
            cls.PENDING, cls.PAYMENT_SUCCESSFUL, cls.CONFIRMED, cls.PROCESSING,
            cls.ASSIGNED, cls.ACCEPTED, cls.PICKED_UP, cls.OUT_FOR_DELIVERY,
            cls.NEAR_LOCATION, cls.DELIVERED,
        ]

    @classmethod
    def terminal_statuses(cls):
        return [cls.DELIVERED, cls.CANCELLED, cls.RETURNED, cls.REFUNDED, cls.PAYMENT_FAILED]

    @classmethod
    def cancellable_before(cls):
        return [cls.PENDING, cls.PAYMENT_SUCCESSFUL, cls.CONFIRMED, cls.PROCESSING]

    @classmethod
    def cancellable_late(cls):
        return [cls.ASSIGNED, cls.ACCEPTED, cls.PICKED_UP, cls.OUT_FOR_DELIVERY]


class PaymentMethod(models.TextChoices):
    COD = "cod", "Cash on Delivery"
    ONLINE = "online", "Online"
    UPI = "upi", "UPI"
    CARD = "card", "Card"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class ReviewRating(models.IntegerChoices):
    ONE = 1, "1"
    TWO = 2, "2"
    THREE = 3, "3"
    FOUR = 4, "4"
    FIVE = 5, "5"


class ContactReason(models.TextChoices):
    ORDER = "order", "Order Issue"
    PAYMENT = "payment", "Payment Problem"
    DELIVERY = "delivery", "Delivery Problem"
    PRODUCT = "product", "Product Query"
    REFUND = "refund", "Refund Request"
    OTHER = "other", "Other"


class ContactStatus(models.TextChoices):
    NEW = "new", "New"
    READ = "read", "Read"
    REPLIED = "replied", "Replied"


# Checkout payment-method options shown on the "place order" form. Kept
# separate from PaymentMethod (the DB-level enum) because the form exposes
# more granular UPI-app choices that all map back to Payment.UPI in the DB.
class CheckoutPaymentOption(models.TextChoices):
    COD = "cod", "Cash on Delivery"
    GPAY = "gpay", "Google Pay (UPI)"
    PHONEPE = "phonepe", "PhonePe (UPI)"
    PAYTM = "paytm", "Paytm (UPI)"
    UPI = "upi", "Other UPI App"
