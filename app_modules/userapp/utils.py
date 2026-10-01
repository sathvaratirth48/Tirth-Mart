from urllib.parse import quote

from django.conf import settings
from django.utils import timezone
from django.utils.timesince import timesince


def generate_transaction_ref(order):
    """Deterministic-ish reference used to correlate an order with a UPI
    payment attempt."""
    return f"TM{order.id}{int(timezone.now().timestamp())}"


def build_upi_deep_link(order, amount, transaction_ref):
    """Builds a ``upi://pay`` deep link that opens the user's UPI app
    (GPay/PhonePe/Paytm/etc.) pre-filled with the store's payee details."""
    payee_name = quote(settings.UPI_PAYEE_NAME)
    note = quote(f"Order #{order.id} Tirth Mart")
    return (
        f"upi://pay?pa={settings.UPI_PAYEE_VPA}"
        f"&pn={payee_name}"
        f"&am={amount}&cu=INR"
        f"&tn={note}"
        f"&tr={transaction_ref}"
    )


def serialize_notification(notification):
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "time": timesince(notification.created_at) + " ago",
    }


def parse_int(value, default=None):
    """``int(value)`` that returns ``default`` instead of raising."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
