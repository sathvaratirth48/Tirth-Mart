from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from app_modules.userapp.models import Notification
from app_modules.userapp.utils import serialize_notification

from . import services
from .forms import DeliveryBoyRegistrationForm, UpdateAssignmentStatusForm
from .models import OrderAssignment
from .permissions import delivery_required


# ─── Auth Views ────────────────────────────────────────────────────────────
def delivery_register(request):
    form = DeliveryBoyRegistrationForm(request.POST or None)
    if form.is_valid():
        delivery_boy = form.save()
        login(request, delivery_boy.user)
        messages.success(request, "Registered! Await admin verification.")
        return redirect("delivery_pending")
    return render(request, "deliveryapp/register.html", {"form": form})


def delivery_pending(request):
    return render(request, "deliveryapp/pending.html")


# ─── Dashboard ───────────────────────────────────────────────────────────
@delivery_required
def delivery_dashboard(request):
    delivery_boy = request.user.delivery_profile
    active = OrderAssignment.objects.filter(
        delivery_boy=delivery_boy, status__in=[OrderAssignment.ASSIGNED, OrderAssignment.PICKED_UP]
    ).select_related("order__customer")
    completed = OrderAssignment.objects.filter(delivery_boy=delivery_boy, status=OrderAssignment.DELIVERED).count()
    return render(request, "deliveryapp/dashboard.html", {
        "delivery_boy": delivery_boy,
        "active_assignments": active,
        "completed_count": completed,
    })


# ─── Assignment Views ──────────────────────────────────────────────────────
@delivery_required
def assignment_list(request):
    delivery_boy = request.user.delivery_profile
    assignments = OrderAssignment.objects.filter(
        delivery_boy=delivery_boy
    ).select_related("order__customer").order_by("-assigned_at")
    return render(request, "deliveryapp/assignment_list.html", {"assignments": assignments})


@delivery_required
def assignment_detail(request, pk):
    delivery_boy = request.user.delivery_profile
    assignment = get_object_or_404(OrderAssignment, pk=pk, delivery_boy=delivery_boy)
    form = UpdateAssignmentStatusForm(request.POST or None, instance=assignment)
    if form.is_valid():
        updated = form.save(commit=False)
        services.apply_assignment_status_update(assignment, updated, request.user)
        messages.success(request, "Assignment status updated.")
        return redirect("delivery_dashboard")
    return render(request, "deliveryapp/assignment_detail.html", {"assignment": assignment, "form": form})


# ─── Toggle Availability ───────────────────────────────────────────────────
@delivery_required
def toggle_availability(request):
    delivery_boy = request.user.delivery_profile
    result_message = services.toggle_delivery_boy_availability(delivery_boy)
    if result_message:
        messages.success(request, result_message)
    return redirect("delivery_dashboard")


# ─── Notification APIs for Delivery Boy ─────────────────────────────────────
@delivery_required
def delivery_notif_recent(request):
    notifs = Notification.objects.filter(receiver=request.user).order_by("-created_at")[:10]
    data = [serialize_notification(n) for n in notifs]
    unread = Notification.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({"notifications": data, "unread": unread})


@delivery_required
def delivery_notif_mark_read(request, pk):
    Notification.objects.filter(pk=pk, receiver=request.user).update(is_read=True)
    return JsonResponse({"ok": True})


@delivery_required
def delivery_notif_clear(request):
    if request.method == "POST":
        Notification.objects.filter(receiver=request.user).delete()
    return redirect("delivery_dashboard")
