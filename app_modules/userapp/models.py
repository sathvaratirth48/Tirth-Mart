from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .choices import (
    ContactReason,
    ContactStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    ReviewRating,
    UserRole,
)
from .managers import CustomUserManager, OrderManager


class CustomUser(AbstractUser):
    """Single user model for customers, admins and delivery boys,
    distinguished by ``role``. KYC fields are only populated for the
    Delivery role (see ``services.registration``)."""

    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    is_approved = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True, unique=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True, unique=True)
    aadhaar_image = models.ImageField(upload_to="kyc/aadhaar/", null=True, blank=True)
    pan_image = models.ImageField(upload_to="kyc/pan/", null=True, blank=True)
    other_document_image = models.ImageField(upload_to="kyc/other/", null=True, blank=True)
    is_kyc_verified = models.BooleanField(default=False)
    registration_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = CustomUserManager()

    def get_full_name_or_username(self):
        return super().get_full_name() or self.username

    def save(self, *args, **kwargs):
        # Unique+blank CharFields must be stored as NULL, never "", or the
        # unique constraint would reject a second blank value.
        self.pan_number = self.pan_number or None
        self.aadhaar_number = self.aadhaar_number or None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == UserRole.ADMIN

    @property
    def is_delivery_role(self):
        return self.role == UserRole.DELIVERY

    @property
    def is_customer_role(self):
        return self.role == UserRole.USER


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("adminapp.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey("adminapp.Product", on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} ❤ {self.product.name}"


class Order(models.Model):
    # Backward-compatible flat constants (many call-sites compare against
    # e.g. ``Order.PENDING``) that simply mirror ``OrderStatus`` members.
    PENDING = OrderStatus.PENDING
    PAYMENT_FAILED = OrderStatus.PAYMENT_FAILED
    PAYMENT_SUCCESSFUL = OrderStatus.PAYMENT_SUCCESSFUL
    CONFIRMED = OrderStatus.CONFIRMED
    PROCESSING = OrderStatus.PROCESSING
    ASSIGNED = OrderStatus.ASSIGNED
    ACCEPTED = OrderStatus.ACCEPTED
    PICKED_UP = OrderStatus.PICKED_UP
    OUT_FOR_DELIVERY = OrderStatus.OUT_FOR_DELIVERY
    NEAR_LOCATION = OrderStatus.NEAR_LOCATION
    DELIVERED = OrderStatus.DELIVERED
    CANCELLED = OrderStatus.CANCELLED
    RETURNED = OrderStatus.RETURNED
    REFUNDED = OrderStatus.REFUNDED

    STATUS_CHOICES = OrderStatus.choices
    AUTO_PROGRESSION = OrderStatus.auto_progression()
    TERMINAL_STATUSES = OrderStatus.terminal_statuses()
    CANCELLABLE_BEFORE = OrderStatus.cancellable_before()
    CANCELLABLE_LATE = OrderStatus.cancellable_late()

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    delivery_address = models.TextField()
    contact_name = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_updated_at = models.DateTimeField(default=timezone.now)

    objects = OrderManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.display_id} by {self.customer.username}"

    @property
    def display_id(self):
        """Human-readable order ID: 📦 Order TM20260018"""
        year = self.created_at.year if self.created_at else 2026
        return f"📦 Order TM{year}{self.id:04d}"

    @property
    def short_display_id(self):
        """Short form: TM20260018"""
        year = self.created_at.year if self.created_at else 2026
        return f"TM{year}{self.id:04d}"

    def set_status(self, new_status):
        self.status = new_status
        self.status_updated_at = timezone.now()
        self.save(update_fields=["status", "status_updated_at"])

    @property
    def is_cancellable(self):
        return self.status in self.CANCELLABLE_BEFORE

    @property
    def is_cancellable_late(self):
        """Can still cancel but payment already made - refund will be processed."""
        return self.status in self.CANCELLABLE_LATE

    @property
    def can_cancel(self):
        return self.is_cancellable or self.is_cancellable_late


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("adminapp.Product", on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.order.display_id})"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Payment(models.Model):
    COD = PaymentMethod.COD
    ONLINE = PaymentMethod.ONLINE
    UPI = PaymentMethod.UPI
    CARD = PaymentMethod.CARD
    METHOD_CHOICES = PaymentMethod.choices

    PENDING = PaymentStatus.PENDING
    SUCCESS = PaymentStatus.SUCCESS
    FAILED = PaymentStatus.FAILED
    REFUNDED = PaymentStatus.REFUNDED
    STATUS_CHOICES = PaymentStatus.choices

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.payment_status}"


class Notification(models.Model):
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.receiver.username}] {self.title}"


class Review(models.Model):
    RATING_CHOICES = ReviewRating.choices

    product = models.ForeignKey("adminapp.Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=ReviewRating.choices, default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.user.username} rated {self.product.name} - {self.rating}★"

    @property
    def full_stars_range(self):
        return range(self.rating)

    @property
    def empty_stars_range(self):
        return range(5 - self.rating)


class PromoUsage(models.Model):
    """Tracks which user has already used a promo code."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="promo_usages")
    code = models.CharField(max_length=30)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "code")

    def __str__(self):
        return f"{self.user.username} used {self.code}"


class ContactMessage(models.Model):
    """Stores contact form submissions from visitors/customers."""

    REASON_CHOICES = ContactReason.choices
    STATUS_CHOICES = ContactStatus.choices

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    reason = models.CharField(max_length=30, choices=ContactReason.choices, default=ContactReason.OTHER)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=ContactStatus.choices, default=ContactStatus.NEW)
    submitted_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="contact_messages"
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} — {self.subject}"
