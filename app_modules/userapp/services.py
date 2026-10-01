"""
Business logic for userapp, kept out of views so views stay thin
request/response glue. Every function here is framework-adjacent (may take
a ``request`` for things like IP address) but contains no template
rendering - that stays in views.py.
"""
from django.contrib.auth import get_user_model
from django.db import transaction

from . import notifs as N
from .choices import UserRole
from .constants import (
    FREE_DELIVERY_THRESHOLD,
    LATE_CANCELLATION_DEDUCTION,
    PROMO_CODES,
    STANDARD_DELIVERY_CHARGE,
)
from .models import (
    Cart,
    CustomUser,
    Notification,
    Order,
    OrderItem,
    Payment,
    PromoUsage,
    Review,
    Wishlist,
)
from .utils import build_upi_deep_link, generate_transaction_ref, parse_int
from .validators import validate_dob_year_string

User = get_user_model()


# ─── Registration ───────────────────────────────────────────────────────────
def precheck_registration(role, dob, aadhaar_number, aadhaar_image):
    """Validates the parts of registration that live outside the ModelForm
    (role selection, DOB sanity, KYC-mandatory-for-delivery). Returns an
    error message string, or ``None`` if everything checks out."""
    if role not in (UserRole.USER, UserRole.DELIVERY):
        return "Please select a valid role."

    from django.core.exceptions import ValidationError

    try:
        validate_dob_year_string(dob)
    except ValidationError as exc:
        return exc.messages[0] if hasattr(exc, "messages") else str(exc)

    if role == UserRole.DELIVERY and (not aadhaar_number or not aadhaar_image):
        return "Aadhaar Number and Aadhaar Card Image are required for Delivery Boy registration."

    return None


def complete_registration(form, role, request):
    """Persists a new user (and their Cart / DeliveryBoy profile) once the
    form and pre-checks have both passed."""
    user = form.save(commit=False)
    user.set_password(form.cleaned_data["password"])
    user.role = role
    user.is_approved = False
    user.registration_ip = request.META.get("REMOTE_ADDR")

    # KYC fields are for Delivery Boys only.
    if role == UserRole.USER:
        user.aadhaar_number = None
        user.pan_number = None
        user.aadhaar_image = None
        user.pan_image = None
        user.other_document_image = None

    user.save()
    Cart.objects.get_or_create(user=user)

    if role == UserRole.DELIVERY:
        from app_modules.deliveryapp.models import DeliveryBoy

        DeliveryBoy.objects.get_or_create(
            user=user,
            defaults={
                "vehicle_type": request.POST.get("vehicle_type", "bike"),
                "vehicle_number": request.POST.get("vehicle_number", ""),
            },
        )

    N.notif_welcome(user)
    N.notif_new_customer(user)
    return user


def resolve_post_login_redirect(user):
    """Where to send a user right after a successful login, or a warning
    message if they can't log in yet. Returns ``(redirect_name, warning)``
    - exactly one of which is ``None``."""
    if user.role == UserRole.ADMIN:
        return "admin_dashboard", None
    if user.role == UserRole.DELIVERY:
        return "delivery_dashboard", None
    if user.role == UserRole.USER and user.is_approved:
        return "index", None
    if user.role == UserRole.USER and not user.is_approved:
        return None, "Your account is pending admin approval!"
    return None, "Access denied."


def user_dashboard_buckets():
    """Shared by both the userapp and adminapp admin-dashboard views."""
    return {
        "all_users": User.objects.non_admins(),
        "approved_users": User.objects.approved_customers(),
        "pending_users": User.objects.pending_customers(),
    }


# ─── Cart ───────────────────────────────────────────────────────────────────
def add_product_to_cart(user, product):
    """Returns (ok, message, cart). Increments quantity if already present,
    respecting stock; leaves everything untouched if out of stock."""
    cart, _ = Cart.objects.get_or_create(user=user)
    item, created = cart.items.get_or_create(product=product)
    if created:
        return True, f"{product.name} added to cart", cart
    if item.quantity < product.stock_quantity:
        item.quantity += 1
        item.save()
        return True, f"{product.name} added to cart", cart
    return False, "Out of stock", cart


def update_cart_item_quantity(item, quantity):
    """Returns (ok, message)."""
    if quantity <= 0:
        item.delete()
        return True, None
    if quantity <= item.product.stock_quantity:
        item.quantity = quantity
        item.save()
        return True, None
    return False, "Not enough stock"


def toggle_wishlist(user, product):
    """Returns (added: bool, wishlist_count: int)."""
    existing = Wishlist.objects.filter(user=user, product=product).first()
    if existing:
        existing.delete()
        added = False
    else:
        Wishlist.objects.create(user=user, product=product)
        added = True
    return added, Wishlist.objects.filter(user=user).count()


# ─── Promo codes ────────────────────────────────────────────────────────────
def evaluate_promo_code(user, code):
    """Returns a dict describing validity, matching the AJAX response shape
    the frontend already expects."""
    code = (code or "").strip().upper()
    if not code:
        return {"valid": False, "message": "Please enter a promo code."}
    promo = PROMO_CODES.get(code)
    if not promo:
        return {"valid": False, "message": f'"{code}" is not a valid promo code.'}
    if PromoUsage.objects.filter(user=user, code=code).exists():
        return {"valid": False, "message": f'You have already used promo code "{code}".'}
    return {
        "valid": True,
        "code": code,
        "discount_pct": promo["discount_pct"],
        "description": promo["description"],
        "message": f'✅ Promo code applied! {promo["description"]}',
    }


def compute_delivery_charge(subtotal):
    return 0 if subtotal > FREE_DELIVERY_THRESHOLD else STANDARD_DELIVERY_CHARGE


# ─── Checkout ───────────────────────────────────────────────────────────────
class CheckoutResult:
    def __init__(self, order, payment_method, total, transaction_ref=None):
        self.order = order
        self.payment_method = payment_method
        self.total = total
        self.transaction_ref = transaction_ref


@transaction.atomic
def place_order(user, cart, items, form, promo_code, request):
    """Creates the Order/OrderItems/Payment, decrements stock, records promo
    usage, empties the cart and fires notifications - all atomically."""
    subtotal = cart.total_price
    delivery_charge = compute_delivery_charge(subtotal)

    promo_code = (promo_code or "").strip().upper()
    promo_discount = 0
    promo_applied = False
    if promo_code:
        promo = PROMO_CODES.get(promo_code)
        already_used = PromoUsage.objects.filter(user=user, code=promo_code).exists()
        if promo and not already_used:
            promo_discount = round(subtotal * promo["discount_pct"] / 100)
            promo_applied = True

    total = subtotal + delivery_charge - promo_discount
    payment_method = form.cleaned_data["payment_method"]

    order = Order.objects.create(
        customer=user,
        total_amount=total,
        delivery_address=form.cleaned_data["delivery_address"],
        contact_name=form.cleaned_data["contact_name"],
        contact_phone=form.cleaned_data["contact_phone"],
    )
    for item in items:
        OrderItem.objects.create(
            order=order, product=item.product, quantity=item.quantity, price=item.product.price,
        )
        item.product.stock_quantity -= item.quantity
        item.product.save()

    transaction_ref = generate_transaction_ref(order)
    Payment.objects.create(
        order=order,
        amount=total,
        payment_method=Payment.COD if payment_method == "cod" else Payment.UPI,
        payment_status=Payment.PENDING,
        transaction_id=transaction_ref if payment_method != "cod" else "",
    )
    if promo_applied:
        PromoUsage.objects.get_or_create(user=user, code=promo_code)

    items.delete()
    N.notif_order_placed(order)
    if payment_method != "cod":
        N.notif_payment_received(order)

    return CheckoutResult(order, payment_method, total, transaction_ref)


def build_upi_payment_context(order, total, transaction_ref, payment_method):
    from django.conf import settings

    return {
        "order": order,
        "upi_link": build_upi_deep_link(order, total, transaction_ref),
        "upi_id": settings.UPI_PAYEE_VPA,
        "amount": total,
        "payment_method": payment_method,
    }


def confirm_upi_payment_claim(order, user):
    if hasattr(order, "payment"):
        order.payment.payment_status = Payment.PENDING
        order.payment.save()
        Notification.objects.create(
            receiver=user,
            title="Payment Submitted",
            message=(
                f"We've recorded your UPI payment claim for {order.display_id}. "
                f"It will be verified by our team shortly."
            ),
        )


# ─── Order cancellation ─────────────────────────────────────────────────────
class CancellationResult:
    def __init__(self, refund_amount, is_late):
        self.refund_amount = refund_amount
        self.is_late = is_late


@transaction.atomic
def cancel_order(order):
    """Restocks items, marks the order cancelled, handles refund/notifications
    and frees up the assigned delivery boy. Returns a ``CancellationResult``."""
    is_late = order.is_cancellable_late  # after assignment/OFD

    for item in order.items.select_related("product"):
        item.product.stock_quantity += item.quantity
        item.product.save()
        if item.product.stock_quantity <= 10:
            N.notif_low_stock(item.product)

    order.set_status(Order.CANCELLED)

    refund_amount = None
    if hasattr(order, "payment"):
        pmt = order.payment
        if pmt.payment_status == Payment.SUCCESS:
            if is_late and pmt.payment_method == Payment.UPI:
                refund_amount = max(float(order.total_amount) - LATE_CANCELLATION_DEDUCTION, 0)
            pmt.payment_status = Payment.REFUNDED
            pmt.save()
            N.notif_refund_processed(order)
        elif pmt.payment_status == Payment.PENDING:
            pmt.payment_status = Payment.FAILED
            pmt.save()

    if is_late:
        reason = (
            f"Order picked up/out for delivery at cancellation. "
            f"₹{LATE_CANCELLATION_DEDUCTION} delivery charge deducted. "
            f"Refund of ₹{refund_amount:.0f} initiated."
            if refund_amount is not None
            else "Order was picked up / out for delivery at the time of cancellation."
        )
        N.notif_order_cancelled(order, reason)
    else:
        N.notif_order_cancelled(order)

    if hasattr(order, "assignment"):
        db = order.assignment.delivery_boy
        if db:
            db.status = db.AVAILABLE
            db.save()
            N.notif_delivery_failed(db.user, order)

    return CancellationResult(refund_amount, is_late)


# ─── Reviews ────────────────────────────────────────────────────────────────
def submit_product_review(product, user, rating_raw, comment):
    rating = parse_int(rating_raw, default=5)
    if rating is None or rating < 1 or rating > 5:
        rating = 5
    Review.objects.update_or_create(
        product=product, user=user, defaults={"rating": rating, "comment": (comment or "").strip()},
    )


# ─── Contact form ───────────────────────────────────────────────────────────
def submit_contact_message(data, user):
    """``data`` is a dict of the raw POST fields. Returns the created
    ContactMessage, or ``None`` if required fields were missing."""
    from .models import ContactMessage

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    reason = data.get("reason", "other")
    subject = (data.get("subject") or "").strip()
    message_text = (data.get("message") or "").strip()

    if not (name and email and subject and message_text):
        return None

    contact_message = ContactMessage.objects.create(
        name=name, email=email, phone=phone, reason=reason, subject=subject, message=message_text,
        user=user if user.is_authenticated else None,
    )
    for admin in CustomUser.objects.approved_admins():
        Notification.objects.create(
            receiver=admin,
            title=f"📩 New Contact: {subject[:40]}",
            message=f"From {name} ({email}): {message_text[:80]}",
        )
    return contact_message


# ─── Order status polling ───────────────────────────────────────────────────
def order_tracking_snapshot(order):
    order.refresh_from_db()
    delivery_boy_name = None
    delivery_boy_phone = None
    if hasattr(order, "assignment") and order.assignment.delivery_boy:
        db_user = order.assignment.delivery_boy.user
        delivery_boy_name = db_user.get_full_name_or_username()
        delivery_boy_phone = db_user.phone_number
    return {
        "status": order.status,
        "status_display": order.get_status_display(),
        "status_updated_at": order.status_updated_at.strftime("%d %b %Y, %I:%M %p"),
        "is_cancellable": order.is_cancellable,
        "is_cancellable_late": order.is_cancellable_late,
        "delivery_boy_name": delivery_boy_name,
        "delivery_boy_phone": delivery_boy_phone,
        "display_id": order.display_id,
    }


def order_delivery_contact(order):
    """(name, phone) of the assigned delivery boy, or (None, None)."""
    if hasattr(order, "assignment") and order.assignment.delivery_boy:
        db_user = order.assignment.delivery_boy.user
        return db_user.get_full_name_or_username(), db_user.phone_number
    return None, None
