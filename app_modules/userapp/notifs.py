"""
Central notification dispatcher for Tirth Mart.
Call these helpers from any view/service to fire the right notification to
the right recipient.
"""
from .models import CustomUser, Notification


def _send(receiver, title, message):
    Notification.objects.create(receiver=receiver, title=title, message=message)


def _send_all_admins(title, message):
    for admin_user in CustomUser.objects.approved_admins():
        _send(admin_user, title, message)


def _send_all_delivery_boys(title, message):
    from app_modules.deliveryapp.models import DeliveryBoy

    for delivery_boy in DeliveryBoy.objects.filter(is_verified=True).select_related("user"):
        _send(delivery_boy.user, title, message)


# ─── Customer ────────────────────────────────────────────────────────────────
def notif_order_placed(order):
    _send(order.customer, "✅ Order Placed", f"Your {order.display_id} has been placed successfully.")
    _send_all_admins(
        "🛒 New Order Received",
        f"New {order.display_id} from {order.customer.get_full_name_or_username()} · ₹{order.total_amount}.",
    )


def notif_payment_received(order):
    _send(
        order.customer,
        "💳 Payment Received",
        f"Payment of ₹{order.total_amount} for {order.display_id} received successfully.",
    )
    _send_all_admins("💳 Payment Received", f"Payment confirmed for {order.display_id} · ₹{order.total_amount}.")


def notif_payment_failed(order):
    _send(
        order.customer,
        "❌ Payment Failed",
        f"Payment for {order.display_id} failed. Your order has been cancelled automatically.",
    )
    _send_all_admins(
        "❌ Payment Failed",
        f"Payment failed for {order.display_id} by {order.customer.get_full_name_or_username()}.",
    )


def notif_order_processing(order):
    _send(order.customer, "📦 Order Processing", f"Your {order.display_id} is being prepared by our team.")


def notif_order_assigned(order, delivery_boy_name):
    _send(
        order.customer,
        "🚚 Delivery Boy Assigned",
        f"Your {order.display_id} has been assigned to {delivery_boy_name}.",
    )
    _send_all_admins("🚚 Delivery Assigned", f"{order.display_id} assigned to delivery boy {delivery_boy_name}.")


def notif_order_out_for_delivery(order):
    _send(
        order.customer, "🛵 Out for Delivery",
        f"Your {order.display_id} is out for delivery! You'll receive it soon.",
    )


def notif_order_delivered(order):
    _send(order.customer, "🎉 Order Delivered", f"Your {order.display_id} has been delivered successfully. Enjoy!")
    _send_all_admins(
        "✅ Order Delivered",
        f"{order.display_id} for {order.customer.get_full_name_or_username()} delivered successfully.",
    )


def notif_order_cancelled(order, reason=""):
    msg = f"Your {order.display_id} has been cancelled."
    if reason:
        msg += f" Reason: {reason}"
    _send(order.customer, "❌ Order Cancelled", msg)
    _send_all_admins(
        "❌ Order Cancelled",
        f"{order.display_id} by {order.customer.get_full_name_or_username()} was cancelled.",
    )


def notif_refund_processed(order):
    _send(
        order.customer, "💰 Refund Processed",
        f"Your refund of ₹{order.total_amount} for {order.display_id} has been processed. "
        f"It will reflect within 5-7 working days.",
    )


def notif_order_returned(order):
    _send(order.customer, "📦 Order Return", f"Your return request for {order.display_id} has been received.")
    _send_all_admins(
        "📦 Order Returned",
        f"{order.display_id} return request from {order.customer.get_full_name_or_username()}.",
    )


def notif_welcome(user):
    _send(
        user,
        "👋 Welcome to Tirth Mart!",
        "Thank you for joining Tirth Mart. Explore our fresh snacks, sweets, and more!",
    )


def notif_profile_updated(user):
    _send(user, "👤 Profile Updated", "Your profile has been updated successfully.")


# ─── Delivery Boy ─────────────────────────────────────────────────────────────
def notif_delivery_new_assignment(delivery_user, order):
    _send(
        delivery_user,
        "📦 New Order Assigned",
        f"New {order.display_id} has been assigned to you. Please accept and proceed with pickup.",
    )


def notif_delivery_pickup_reminder(delivery_user, order):
    _send(delivery_user, "📦 Pickup Order", f"Please pick up {order.display_id} from the store.")


def notif_delivery_completed(delivery_user, order):
    _send(delivery_user, "✅ Delivery Completed", f"You have successfully delivered {order.display_id}. Great job!")


def notif_delivery_delayed(delivery_user, order):
    _send(
        delivery_user,
        "⏰ Delivery Delayed",
        f"{order.display_id} delivery is running late. Please update the customer.",
    )


def notif_delivery_failed(delivery_user, order):
    _send(delivery_user, "❌ Delivery Failed", f"Delivery of {order.display_id} failed. Please contact admin.")


# ─── Inventory ─────────────────────────────────────────────────────────────
def notif_low_stock(product):
    _send_all_admins(
        "⚠️ Low Stock Alert",
        f"Low stock: {product.name} only {product.stock_quantity} units left. Restock soon.",
    )


def notif_out_of_stock(product):
    _send_all_admins("❌ Out of Stock", f"Product out of stock: {product.name}. Restock immediately.")


def notif_stock_updated(product, added_qty):
    _send_all_admins(
        "📦 Stock Updated",
        f"Stock for {product.name} updated. Added {added_qty} units. Total: {product.stock_quantity}.",
    )


# ─── Admin / Users ────────────────────────────────────────────────────────────
def notif_new_customer(user):
    _send_all_admins(
        "👥 New Customer Registered",
        f"New customer {user.get_full_name_or_username()} ({user.email}) joined Tirth Mart.",
    )


def notif_customer_deleted(user_name):
    _send_all_admins("👤 Customer Left", f"Customer '{user_name}' deleted their account.")
