"""
Business logic for adminapp, kept out of views so views stay thin
request/response glue.
"""
import json
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from app_modules.deliveryapp.models import DeliveryBoy, OrderAssignment
from app_modules.userapp import notifs as N
from app_modules.userapp.choices import UserRole
from app_modules.userapp.models import CustomUser, Notification, Order, OrderItem, Payment

from .choices import ProductStatus
from .models import Product

LOW_STOCK_THRESHOLD = 10


# ─── Dashboard KPIs ─────────────────────────────────────────────────────────
def _kpi_cards(now, thirty_days_ago):
    total_orders = Order.objects.count()
    total_revenue = Payment.objects.filter(payment_status=Payment.SUCCESS).aggregate(t=Sum("amount"))["t"] or 0
    total_customers = CustomUser.objects.customers().count()
    total_products = Product.objects.active().count()
    pending_orders = Order.objects.filter(status__in=["pending", "confirmed", "processing"]).count()
    delivered_orders = Order.objects.filter(status=Order.DELIVERED).count()
    cancelled_orders = Order.objects.filter(status=Order.CANCELLED).count()
    active_delivery_boys = DeliveryBoy.objects.filter(is_verified=True).count()

    monthly_revenue = Payment.objects.filter(
        payment_status=Payment.SUCCESS, created_at__gte=thirty_days_ago
    ).aggregate(t=Sum("amount"))["t"] or 0
    prev_month_revenue = Payment.objects.filter(
        payment_status=Payment.SUCCESS,
        created_at__gte=now - timedelta(days=60),
        created_at__lt=thirty_days_ago,
    ).aggregate(t=Sum("amount"))["t"] or 0
    revenue_change = round(
        ((float(monthly_revenue) - float(prev_month_revenue)) / max(float(prev_month_revenue), 1)) * 100, 1
    )

    prev_month_orders = Order.objects.filter(
        created_at__gte=now - timedelta(days=60), created_at__lt=thirty_days_ago
    ).count()
    monthly_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    orders_change = round(((monthly_orders - prev_month_orders) / max(prev_month_orders, 1)) * 100, 1)

    return {
        "total_orders": total_orders, "total_revenue": total_revenue,
        "total_customers": total_customers, "total_products": total_products,
        "pending_orders": pending_orders, "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders, "active_delivery_boys": active_delivery_boys,
        "monthly_revenue": monthly_revenue, "prev_month_revenue": prev_month_revenue,
        "revenue_change": revenue_change, "orders_change": orders_change, "monthly_orders": monthly_orders,
    }


def _revenue_trend(today):
    trend = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        rev = (
            Payment.objects.filter(payment_status=Payment.SUCCESS, created_at__date=d)
            .aggregate(t=Sum("amount"))["t"]
            or 0
        )
        trend.append({"date": d.strftime("%d %b"), "revenue": float(rev)})
    return trend


def _order_status_counts(delivered_orders, cancelled_orders):
    return {
        "pending": Order.objects.filter(status__in=["pending", "payment_successful", "confirmed"]).count(),
        "processing": Order.objects.filter(status="processing").count(),
        "assigned": Order.objects.filter(status__in=["assigned", "accepted"]).count(),
        "out_for_delivery": Order.objects.filter(status__in=["out_for_delivery", "near_location", "picked_up"]).count(),
        "delivered": delivered_orders,
        "cancelled": cancelled_orders,
    }


def _delivery_analytics():
    total_delivery_boys = DeliveryBoy.objects.count()
    busy = DeliveryBoy.objects.filter(status="busy").count()
    offline = DeliveryBoy.objects.filter(status="offline").count()
    available = DeliveryBoy.objects.filter(status="available").count()
    completed_deliveries = OrderAssignment.objects.filter(status="delivered").count()
    pending_deliveries = OrderAssignment.objects.filter(status="assigned").count()
    accepted_deliveries = OrderAssignment.objects.filter(status="accepted").count()
    vehicle_bike = DeliveryBoy.objects.filter(vehicle_type="bike").count()
    vehicle_scooter = DeliveryBoy.objects.filter(vehicle_type="scooter").count()
    vehicle_bicycle = DeliveryBoy.objects.filter(vehicle_type="bicycle").count()
    return {
        "total_delivery_boys": total_delivery_boys,
        "busy_delivery_boys": busy,
        "offline_delivery_boys": offline,
        "available_delivery_boys": available,
        "completed_deliveries": completed_deliveries,
        "pending_deliveries": pending_deliveries,
        "accepted_deliveries": accepted_deliveries,
        "vehicle_bike": vehicle_bike,
        "vehicle_scooter": vehicle_scooter,
        "vehicle_bicycle": vehicle_bicycle,
    }


def _category_sales():
    cat_sales = list(
        OrderItem.objects.values("product__category__name").annotate(total=Sum("quantity")).order_by("-total")[:8]
    )
    labels = [c["product__category__name"] or "Unknown" for c in cat_sales]
    values = [c["total"] for c in cat_sales]
    return labels, values


def _customer_growth(now):
    growth = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = CustomUser.objects.filter(
            role=UserRole.USER, date_joined__gte=month_start, date_joined__lt=month_end
        ).count()
        growth.append({"month": month_start.strftime("%b %Y"), "count": count})
    return growth


def _payment_method_breakdown():
    payment_methods = list(Payment.objects.values("payment_method").annotate(count=Count("id")).order_by("-count"))
    labels = [p["payment_method"].upper() for p in payment_methods]
    values = [p["count"] for p in payment_methods]
    return labels, values


def _top_products():
    return list(
        OrderItem.objects.values("product__name", "product__category__name")
        .annotate(total_qty=Sum("quantity"), total_revenue=Sum("price"), total_orders=Count("order", distinct=True))
        .order_by("-total_qty")[:8]
    )


def _inventory_summary():
    in_stock = Product.objects.filter(stock_quantity__gt=LOW_STOCK_THRESHOLD, status=ProductStatus.ACTIVE).count()
    low_stock_count = Product.objects.low_stock(LOW_STOCK_THRESHOLD).filter(status=ProductStatus.ACTIVE).count()
    out_of_stock_count = Product.objects.out_of_stock().filter(status=ProductStatus.ACTIVE).count()
    low_stock_products = (
        Product.objects.filter(stock_quantity__lte=LOW_STOCK_THRESHOLD, status=ProductStatus.ACTIVE)
        .select_related("category").order_by("stock_quantity")[:10]
    )
    return in_stock, low_stock_count, out_of_stock_count, low_stock_products


def _business_insights(monthly_revenue, prev_month_revenue, revenue_change, out_of_stock_count, low_stock_count,
                        pending_orders, cancelled_orders, delivered_orders, total_orders, active_delivery_boys,
                        total_customers):
    insights = []

    def add(kind, icon, text):
        insights.append({"type": kind, "icon": icon, "text": text})

    if float(monthly_revenue) > float(prev_month_revenue):
        add("success", "📈", f"Revenue grew {revenue_change}% this month vs last month. Keep up the momentum!")
    elif prev_month_revenue > 0:
        add("warning", "📉", f"Revenue dropped {abs(revenue_change)}% vs last month. Consider running a promotion.")

    if out_of_stock_count > 0:
        add(
            "danger", "🚨",
            f"{out_of_stock_count} product(s) are out of stock! Restock immediately to avoid losing sales.",
        )
    if low_stock_count > 0:
        add("warning", "⚠️", f"{low_stock_count} product(s) have low stock (≤10 units). Reorder soon.")
    if pending_orders > 5:
        add("info", "📦", f"{pending_orders} orders are pending. Assign delivery boys to reduce delays.")
    if cancelled_orders > delivered_orders and total_orders > 0:
        add("danger", "❌", "Cancellation rate is high! Review product quality and delivery speed.")
    if active_delivery_boys == 0:
        add("warning", "🚴", "No verified delivery boys are active. Verify delivery partners to fulfill orders.")
    if total_customers > 0 and total_orders / total_customers < 1.5:
        add(
            "info", "💡",
            "Average orders per customer is low. Try loyalty offers or push notifications to boost repeat purchases.",
        )
    if not insights:
        add("success", "✅", "Business is running smoothly! All key metrics look healthy.")
    return insights


def build_analytics_context():
    """Assembles the full context dict for the admin analytics dashboard."""
    now = timezone.now()
    today = now.date()
    thirty_days_ago = now - timedelta(days=30)

    kpis = _kpi_cards(now, thirty_days_ago)
    revenue_trend = _revenue_trend(today)
    order_status_counts = _order_status_counts(kpis["delivered_orders"], kpis["cancelled_orders"])
    delivery = _delivery_analytics()
    cat_labels, cat_values = _category_sales()
    customer_growth = _customer_growth(now)
    pm_labels, pm_values = _payment_method_breakdown()
    top_products = _top_products()
    in_stock, low_stock_count, out_of_stock_count, low_stock_products = _inventory_summary()

    recent_orders = (
        Order.objects.select_related("customer").prefetch_related("items").order_by("-created_at")[:10]
    )
    recent_activities = Notification.objects.filter(
        Q(title__icontains="Order") | Q(title__icontains="Payment")
        | Q(title__icontains="Delivered") | Q(title__icontains="New")
    ).select_related("receiver").order_by("-created_at")[:12]

    insights = _business_insights(
        kpis["monthly_revenue"], kpis["prev_month_revenue"], kpis["revenue_change"],
        out_of_stock_count, low_stock_count, kpis["pending_orders"], kpis["cancelled_orders"],
        kpis["delivered_orders"], kpis["total_orders"], kpis["active_delivery_boys"], kpis["total_customers"],
    )

    delivery_combined = {
        "availability": {
            "Available": delivery["available_delivery_boys"],
            "Busy": delivery["busy_delivery_boys"],
            "Offline": delivery["offline_delivery_boys"],
        },
        "assignment": {
            "Assigned": delivery["pending_deliveries"],
            "Accepted": delivery["accepted_deliveries"],
            "Completed": delivery["completed_deliveries"],
        },
        "vehicle": {
            "Bike": delivery["vehicle_bike"],
            "Scooter": delivery["vehicle_scooter"],
            "Bicycle": delivery["vehicle_bicycle"],
        },
    }

    context = dict(kpis)
    context.update(delivery)
    context.update({
        "revenue_trend_json": json.dumps(revenue_trend),
        "cat_labels_json": json.dumps(cat_labels),
        "cat_values_json": json.dumps(cat_values),
        "customer_growth_json": json.dumps(customer_growth),
        "pm_labels_json": json.dumps(pm_labels),
        "pm_values_json": json.dumps(pm_values),
        "order_status_json": json.dumps(order_status_counts),
        "top_products": top_products,
        "low_stock_products": low_stock_products,
        "recent_orders": recent_orders,
        "recent_activities": recent_activities,
        "delivery_combined_json": json.dumps(delivery_combined),
        "in_stock": in_stock, "low_stock_count": low_stock_count, "out_of_stock_count": out_of_stock_count,
        "insights": insights,
    })
    return context


# ─── Order / Payment management ─────────────────────────────────────────────
def update_order_status(order, new_status):
    if new_status not in dict(Order.STATUS_CHOICES):
        return False
    order.status = new_status
    order.save()
    Notification.objects.create(
        receiver=order.customer,
        title="Order Update",
        message=f"Your {order.display_id} status changed to {order.get_status_display()}.",
    )
    return True


def assign_delivery_boy(order, assignment):
    """``assignment`` is an unsaved OrderAssignment (from OrderAssignmentForm)."""
    assignment.order = order
    assignment.save()
    delivery_boy = assignment.delivery_boy
    delivery_boy.go_busy()
    order.set_status(Order.ASSIGNED)
    delivery_user = delivery_boy.user
    N.notif_order_assigned(order, delivery_user.get_full_name_or_username())
    N.notif_delivery_new_assignment(delivery_user, order)
    return delivery_user


def update_payment_status(payment, new_status):
    if new_status not in dict(Payment.STATUS_CHOICES):
        return False
    payment.payment_status = new_status
    payment.save()
    order = payment.order

    if new_status == Payment.SUCCESS and order.status == Order.PENDING:
        order.set_status(Order.PAYMENT_SUCCESSFUL)
        Notification.objects.create(
            receiver=order.customer,
            title="Payment Successful",
            message=f"Payment for {order.display_id} was successful. Your order is now confirmed.",
        )
    elif new_status == Payment.FAILED:
        for item in order.items.select_related("product"):
            item.product.stock_quantity += item.quantity
            item.product.save()
        order.set_status(Order.CANCELLED)
        Notification.objects.create(
            receiver=order.customer,
            title="Payment Failed - Order Cancelled",
            message=f"Payment for {order.display_id} failed, so the order has been automatically cancelled.",
        )
    return True


# ─── Notifications ──────────────────────────────────────────────────────────
ADMIN_NOTIFICATION_KEYWORDS = [
    "New Order", "Order Cancelled", "Order Delivered", "Order Returned",
    "Payment Received", "Payment Failed", "❌ Order", "🛒 New Order",
    "💳 Payment", "Out of Stock", "Low Stock", "👥 New Customer",
]


def admin_notifications_for(user):
    kw_q = Q()
    for keyword in ADMIN_NOTIFICATION_KEYWORDS:
        kw_q |= Q(title__icontains=keyword)
    return Notification.objects.filter(kw_q, receiver=user).order_by("-created_at")
