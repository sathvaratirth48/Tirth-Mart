from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from app_modules.deliveryapp.forms import OrderAssignmentForm
from app_modules.deliveryapp.models import DeliveryBoy
from app_modules.userapp.choices import UserRole
from app_modules.userapp.models import Cart, ContactMessage, CustomUser, Notification, Order, Payment
from app_modules.userapp.services import user_dashboard_buckets

from . import services
from .forms import AdminProfileForm, CategoryForm, DeliveryBoyAdminForm, OrderAdminForm, ProductForm
from .models import Category, Product
from .permissions import is_admin

User = get_user_model()


def index(request):
    return redirect("analytics")


@staff_member_required
def analytics(request):
    return render(request, "adminapp/analytics.html", services.build_analytics_context())


# ─────────────────────────────────────────────
#  DeliveryBoy
# ─────────────────────────────────────────────
@staff_member_required
def list_DeliveryBoys(request):
    delivery_boys = DeliveryBoy.objects.select_related("user").order_by("-joined_at")
    return render(request, "adminapp/list_DeliveryBoys.html", {"delivery_boys": delivery_boys})


@staff_member_required
def update_DeliveryBoy(request, id):
    deliveryboy = get_object_or_404(DeliveryBoy, id=id)

    if request.method == "POST":
        form = DeliveryBoyAdminForm(request.POST, instance=deliveryboy)
        if form.is_valid():
            form.save()
            return redirect("list_DeliveryBoys")

    users = CustomUser.objects.all()
    return render(request, "adminapp/update_DeliveryBoy.html", {"deliveryboy": deliveryboy, "users": users})


@staff_member_required
def delete_DeliveryBoy(request, id):
    deliveryboy = get_object_or_404(DeliveryBoy, id=id)
    deliveryboy.delete()
    return redirect("list_DeliveryBoys")


# ─────────────────────────────────────────────
#  Category
# ─────────────────────────────────────────────
@staff_member_required
def create_Category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("list_Category")
    return render(request, "adminapp/create_Category.html", {"form": form, "title": "Add Category"})


@staff_member_required
def list_Category(request):
    categories = Category.objects.all()
    return render(request, "adminapp/list_Category.html", {"categories": categories})


@staff_member_required
def update_Category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("list_Category")

    return render(request, "adminapp/update_Category.html", {"category": category})


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect("list_Category")


# ─────────────────────────────────────────────
#  Product
# ─────────────────────────────────────────────
@staff_member_required
def create_Product(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Product created.")
        return redirect("list_Product")

    return render(request, "adminapp/create_Product.html", {
        "form": form, "categories": Category.objects.all(), "title": "Add Product",
    })


@staff_member_required
def list_Product(request):
    products = Product.objects.select_related("category").all()
    return render(request, "adminapp/list_Product.html", {"products": products})


@staff_member_required
def update_Product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("list_Product")

    return render(request, "adminapp/update_Product.html", {
        "product": product, "categories": Category.objects.all(), "title": "Update Product",
    })


@staff_member_required
def delete_Product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect("list_Product")


# ─────────────────────────────────────────────
#  Orders (legacy CRUD screens)
# ─────────────────────────────────────────────
@staff_member_required
def list_Orders(request):
    orders = Order.objects.select_related("customer").all()
    return render(request, "adminapp/list_Orders.html", {"orders": orders})


@staff_member_required
def update_Orders(request, id):
    order = get_object_or_404(Order, id=id)
    users = CustomUser.objects.customers()

    if request.method == "POST":
        form = OrderAdminForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Order Updated Successfully")
            return redirect("list_Orders")

    return render(request, "adminapp/update_Orders.html", {"order": order, "users": users})


@staff_member_required
def delete_Orders(request, id):
    order = get_object_or_404(Order, id=id)
    order.delete()
    messages.success(request, "Order Deleted Successfully")
    return redirect("list_Orders")


# ─────────────────────────────────────────────
#  Cart (read-only admin view)
# ─────────────────────────────────────────────
@staff_member_required
def list_Cart(request):
    carts = Cart.objects.select_related("user").prefetch_related("items__product").order_by("-updated_at")
    return render(request, "adminapp/list_cart.html", {"carts": carts})


# ─────────────────────────────────────────────
#  Admin auth
# ─────────────────────────────────────────────
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        password = request.POST.get("password")
        password1 = request.POST.get("password1")

        if password != password1:
            messages.error(request, "Passwords do not match!")
            return redirect("admin_register")

        if User.objects.filter(username=username).exists():
            messages.warning(request, "Username already exists!")
            return redirect("admin_register")

        user = User.objects.create_user(username=username, email=email, password=password, role=UserRole.ADMIN)
        user.phone_number = phone_number
        user.is_approved = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        messages.success(request, "Admin registered successfully!")
        return redirect("admin_login")

    return render(request, "adminapp/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
        elif not is_admin(user):
            messages.error(request, "Access denied! Only Admins can login here.")
            return redirect("admin_login")
        else:
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("admin_dashboard")

    return render(request, "adminapp/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("admin_login")


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, "You are not authorized!")
        return redirect("admin_login")

    buckets = user_dashboard_buckets()
    return render(request, "adminapp/dashboard_admin.html", {
        "all_users": buckets["all_users"],
        "approved_users": buckets["approved_users"],
        "rejected_users": buckets["pending_users"],
    })


@login_required
def approve_user(request, user_id):
    if not is_admin(request.user):
        messages.error(request, "Unauthorized!")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)
    if user.role == UserRole.ADMIN:
        messages.warning(request, "Cannot approve Admin!")
        return redirect("admin_dashboard")

    user.is_approved = True
    user.save()
    messages.success(request, f"{user.username} approved!")
    return redirect("admin_dashboard")


@login_required
def reject_user(request, user_id):
    if not is_admin(request.user):
        messages.error(request, "Unauthorized!")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)
    if user.role == UserRole.ADMIN:
        messages.warning(request, "Cannot reject Admin!")
        return redirect("admin_dashboard")

    user.is_approved = False
    user.save()
    messages.error(request, f"{user.username} rejected!")
    return redirect("admin_dashboard")


def parent_dashboard(request):
    return render(request, "adminapp/dashboard_parent.html")


def user_dashboard(request):
    return render(request, "adminapp/dashboard_user.html")


# ─────────────────────────────────────────────
#  Order Management
# ─────────────────────────────────────────────
@staff_member_required
def order_list(request):
    orders = Order.objects.select_related("customer").prefetch_related("payment").order_by("-created_at")
    return render(request, "adminapp/order_list.html", {"orders": orders})


@staff_member_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related("product").all()
    return render(request, "adminapp/order_detail.html", {
        "order": order,
        "items": items,
        "payment": getattr(order, "payment", None),
        "assignment": getattr(order, "assignment", None),
        "assign_form": OrderAssignmentForm(),
    })


@staff_member_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST" and services.update_order_status(order, request.POST.get("status")):
        messages.success(request, "Order status updated.")
    return redirect("admin_order_detail", pk=pk)


# ─────────────────────────────────────────────
#  Order Assignment
# ─────────────────────────────────────────────
@staff_member_required
def assign_order(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    form = OrderAssignmentForm(request.POST or None)
    if form.is_valid():
        assignment = form.save(commit=False)
        delivery_user = services.assign_delivery_boy(order, assignment)
        messages.success(request, f"{order.display_id} assigned to {delivery_user.get_full_name_or_username()}.")
    return redirect("admin_order_detail", pk=order_pk)


# ─────────────────────────────────────────────
#  Payment Management
# ─────────────────────────────────────────────
@staff_member_required
def payment_list(request):
    payments = Payment.objects.select_related("order", "order__customer").order_by("-created_at")
    return render(request, "adminapp/payment_list.html", {"payments": payments})


@staff_member_required
def update_payment_status(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    new_status = request.POST.get("status")
    if services.update_payment_status(payment, new_status):
        messages.success(request, f"Payment #{payment.id} marked as {payment.get_payment_status_display()}.")
    return redirect("admin_payment_list")


# ─────────────────────────────────────────────
#  Notifications
# ─────────────────────────────────────────────
@staff_member_required
def notification_list(request):
    notifications = services.admin_notifications_for(request.user)
    return render(request, "adminapp/notification_list.html", {"notifications": notifications})


@staff_member_required
def admin_clear_notifications(request):
    if request.method == "POST":
        Notification.objects.filter(receiver=request.user).delete()
    return redirect("admin_notification_list")


# ─────────────────────────────────────────────
#  Admin Profile
# ─────────────────────────────────────────────
@staff_member_required
def admin_profile_view(request):
    return render(request, "adminapp/profile.html", {})


@staff_member_required
def admin_profile_edit(request):
    if request.method == "POST":
        form = AdminProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("admin_profile_view")
    else:
        form = AdminProfileForm(instance=request.user)
    return render(request, "adminapp/profile_edit.html", {"form": form})


# ─────────────────────────────────────────────
#  Contact Messages
# ─────────────────────────────────────────────
@staff_member_required
def contact_list(request):
    return render(request, "adminapp/contact_list.html", {"contact_msgs": ContactMessage.objects.all()})


@staff_member_required
def contact_update_status(request, pk):
    if request.method == "POST":
        ContactMessage.objects.filter(pk=pk).update(status=request.POST.get("status"))
    return redirect("admin_contact_list")


@staff_member_required
def contact_delete(request, pk):
    if request.method == "POST":
        ContactMessage.objects.filter(pk=pk).delete()
        messages.success(request, "Contact message deleted.")
    return redirect("admin_contact_list")
