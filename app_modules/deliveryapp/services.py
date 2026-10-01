from django.utils import timezone

from app_modules.userapp import notifs as N
from app_modules.userapp.models import Order

from .choices import AssignmentStatus
from .models import DeliveryBoy


def apply_assignment_status_update(assignment, updated, delivery_user):
    """Given an in-memory (unsaved) ``updated`` OrderAssignment instance,
    applies the matching Order status transition + notifications, then saves
    both. Mirrors the delivery boy's manual status update exactly."""
    order = assignment.order
    delivery_boy = assignment.delivery_boy

    if updated.status == AssignmentStatus.DELIVERED:
        updated.delivered_at = timezone.now()
        delivery_boy.go_available()
        order.set_status(Order.DELIVERED)
        N.notif_order_delivered(order)
        N.notif_delivery_completed(delivery_user, order)
    elif updated.status == AssignmentStatus.PICKED_UP:
        order.set_status(Order.PICKED_UP)
        N.notif_delivery_pickup_reminder(delivery_user, order)
    elif updated.status == AssignmentStatus.OUT_FOR_DELIVERY:
        order.set_status(Order.OUT_FOR_DELIVERY)
        N.notif_order_out_for_delivery(order)
    elif updated.status == AssignmentStatus.ASSIGNED:
        order.set_status(Order.ACCEPTED)
        N.notif_order_processing(order)

    updated.save()


def toggle_delivery_boy_availability(delivery_boy):
    """Returns the message to show the delivery boy after toggling."""
    if delivery_boy.status == DeliveryBoy.OFFLINE:
        delivery_boy.go_available()
        return "You are now Online."
    if delivery_boy.status == DeliveryBoy.AVAILABLE:
        delivery_boy.go_offline()
        return "You are now Offline."
    return None
