from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app_modules.adminapp.models import Category, Product

from . import services
from .forms import PlaceOrderForm, ProfileForm, RegisterForm, UserPasswordChangeForm
from .mixins import ajax_error, ajax_success
from .models import Cart, CartItem, Notification, Order, Wishlist
from .permissions import is_admin
from .utils import parse_float, parse_int, serialize_notification

User = get_user_model()


# ─── HOME ────────────────────────────────────────────────────────────────
def home_page(request):
    base_qs = Product.objects.filter(status=Product.ACTIVE, stock_quantity__gt=0).select_related("category")

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))

    all_products = list(base_qs)
    featured_products = list(base_qs.order_by("-created_at")[:8])
    new_arrivals = sorted(all_products, key=lambda p: p.created_at, reverse=True)[:4]
    # "Best Sellers" -> highest avg rating; "Popular" -> highest review count.
    best_sellers = sorted(all_products, key=lambda p: p.avg_rating, reverse=True)[:4]
    popular_products = sorted(all_products, key=lambda p: p.review_count, reverse=True)[:4]

    return render(request, "userapp/index.html", {
        "products": base_qs,
        "featured_products": featured_products,
        "best_sellers": best_sellers,
        "new_arrivals": new_arrivals,
        "popular_products": popular_products,
        "wishlist_ids": wishlist_ids,
    })


# ─── AUTH ────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method != "POST":
        return render(request, "userapp/register.html", {"form": RegisterForm()})

    form = RegisterForm(request.POST, request.FILES)
    role = request.POST.get("role")

    precheck_error = services.precheck_registration(
        role=role,
        dob=request.POST.get("date_of_birth"),
        aadhaar_number=request.POST.get("aadhaar_number"),
        aadhaar_image=request.FILES.get("aadhaar_image"),
    )
    if precheck_error:
        messages.error(request, precheck_error)
        return render(request, "userapp/register.html", {"form": form})

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return render(request, "userapp/register.html", {"form": form})

    services.complete_registration(form, role, request)
    messages.success(request, "Registration successful! Wait for admin approval.")
    return redirect("user_login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid Username or Password!")
        else:
            redirect_name, warning = services.resolve_post_login_redirect(user)
            if redirect_name:
                login(request, user)
                return redirect(redirect_name)
            messages.warning(request, warning) if user.is_customer_role else messages.error(request, warning)

    return render(request, "userapp/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("user_login")


# ─── ADMIN DASHBOARD (in userapp for backward compat) ─────────────────────
@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect("user_login")
    return render(request, "adminapp/dashboard_admin.html", services.user_dashboard_buckets())


@login_required
def user_dashboard(request):
    return render(request, "userapp/dashboard_user.html")


@login_required
def approve_user(request, user_id):
    if not is_admin(request.user):
        return redirect("user_login")
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f"{user.username} approved!")
    return redirect("admin_dashboard")


@login_required
def reject_user(request, user_id):
    if not is_admin(request.user):
        return redirect("user_login")
    user = get_object_or_404(User, id=user_id)
    user.is_approved = False
    user.save()
    messages.warning(request, f"{user.username} rejected!")
    return redirect("admin_dashboard")


# ─── PROFILE ───────────────────────────────────────────────────────────────
@login_required
def profile_view(request):
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")[:5]
    notifications = Notification.objects.filter(receiver=request.user, is_read=False)[:5]
    return render(request, "userapp/profile.html", {"orders": orders, "notifications": notifications})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile_view")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "userapp/profile_edit.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect("profile_view")
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, "userapp/change_password.html", {"form": form})


@login_required
def delete_profile_image(request):
    if request.user.profile_image:
        request.user.profile_image.delete()
        request.user.save()
        messages.success(request, "Profile image removed.")
    return redirect("profile_edit")


# ─── SHOP ────────────────────────────────────────────────────────────────
def shop_page(request):
    products = Product.objects.filter(status=Product.ACTIVE).select_related("category")
    categories = Category.objects.all()

    q = request.GET.get("q", "").strip()
    selected_cats = request.GET.getlist("category")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    rating = request.GET.get("rating", "")
    sort = request.GET.get("sort", "default")

    if q:
        products = products.filter(name__icontains=q)
    if selected_cats:
        products = products.filter(category__name__in=selected_cats)
    if min_price:
        min_price_int = parse_int(min_price)
        if min_price_int is not None:
            products = products.filter(price__gte=min_price_int)
    if max_price:
        max_price_int = parse_int(max_price)
        if max_price_int is not None:
            products = products.filter(price__lte=max_price_int)

    products = list(products)

    if rating:
        min_rating = parse_float(rating)
        if min_rating is not None:
            products = [p for p in products if p.avg_rating >= min_rating]

    if sort == "low":
        products.sort(key=lambda p: p.price)
    elif sort == "high":
        products.sort(key=lambda p: p.price, reverse=True)
    elif sort == "rating":
        products.sort(key=lambda p: p.avg_rating, reverse=True)

    total_count = len(products)
    paginator = Paginator(products, 12)
    page = paginator.get_page(request.GET.get("page"))

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))

    # Build querystring (without 'page') so pagination links preserve all active filters
    qd = request.GET.copy()
    qd.pop("page", None)
    querystring = qd.urlencode()

    return render(request, "userapp/shop.html", {
        "products": page,
        "categories": categories,
        "q": q,
        "selected_cats": selected_cats,
        "min_price": min_price,
        "max_price": max_price,
        "rating": rating,
        "sort": sort,
        "wishlist_ids": wishlist_ids,
        "total_count": total_count,
        "querystring": querystring,
    })


def search_suggestions_ajax(request):
    q = request.GET.get("q", "").strip()
    suggestions = []
    if len(q) >= 2:
        products = Product.objects.filter(status=Product.ACTIVE, name__icontains=q).select_related("category")[:8]
        suggestions = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.name if p.category else "",
                "price": p.price,
                "image": p.image.url if p.image else "",
                "url": f"/product/{p.id}/",
            }
            for p in products
        ]
    return JsonResponse({"suggestions": suggestions})


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, status=Product.ACTIVE)
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    reviews = product.reviews.select_related("user").all()
    related_products = Product.objects.filter(
        category=product.category, status=Product.ACTIVE
    ).exclude(pk=product.pk)[:4]
    user_has_reviewed = request.user.is_authenticated and reviews.filter(user=request.user).exists()
    return render(request, "userapp/product-details.html", {
        "product": product,
        "in_wishlist": in_wishlist,
        "reviews": reviews,
        "related_products": related_products,
        "user_has_reviewed": user_has_reviewed,
    })


@login_required
def submit_review(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        rating_raw = request.POST.get("rating", "5")
        comment = request.POST.get("comment", "")
        services.submit_product_review(product, request.user, rating_raw, comment)
        messages.success(request, "Thanks for your review!")
    return redirect("product_detail", pk=product.pk)


# ─── CART ────────────────────────────────────────────────────────────────
@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product").all()
    return render(request, "userapp/cart.html", {"cart": cart, "items": items})


@login_required
@require_POST
def add_to_cart_ajax(request):
    product = get_object_or_404(Product, id=request.POST.get("product_id"), status=Product.ACTIVE)
    ok, message, cart = services.add_product_to_cart(request.user, product)
    if not ok:
        return ajax_error(message)
    return ajax_success(message, cart_count=cart.total_quantity)


@require_POST
@login_required
def remove_cart_ajax(request):
    item = get_object_or_404(CartItem, id=request.POST.get("item_id"), cart__user=request.user)
    item.delete()
    return ajax_success("Item removed")


@require_POST
@login_required
def update_cart_ajax(request):
    item = get_object_or_404(CartItem, id=request.POST.get("item_id"), cart__user=request.user)
    qty = int(request.POST.get("quantity"))
    ok, message = services.update_cart_item_quantity(item, qty)
    if not ok:
        return ajax_error(message)
    return ajax_success(subtotal=item.cart.total_price)


@login_required
def get_cart_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = [
        {
            "id": i.id,
            "product_id": i.product.id,
            "name": i.product.name,
            "price": i.product.price,
            "qty": i.quantity,
            "img": i.product.image.url if i.product.image else "",
            "subtotal": i.subtotal,
        }
        for i in cart.items.select_related("product")
    ]
    return JsonResponse({"cart": items, "total": cart.total_price})


# ─── WISHLIST ──────────────────────────────────────────────────────────────
@login_required
def toggle_wishlist_ajax(request):
    product = get_object_or_404(Product, id=request.POST.get("product_id"))
    added, count = services.toggle_wishlist(request.user, product)
    return ajax_success(
        f"{product.name} {'added to' if added else 'removed from'} wishlist",
        added=added, wishlist_count=count,
    )


@login_required
def get_wishlist_count_ajax(request):
    return JsonResponse({"wishlist_count": Wishlist.objects.filter(user=request.user).count()})


@login_required
def get_cart_count_ajax(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({"cart_count": cart.total_quantity})


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "userapp/wishlist.html", {"items": items})


# ─── CHECKOUT & ORDERS ───────────────────────────────────────────────────
@login_required
@require_POST
def validate_promo(request):
    """AJAX endpoint: validate promo code, return discount info."""
    return JsonResponse(services.evaluate_promo_code(request.user, request.POST.get("code", "")))


@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related("product").all()
    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("cart")

    form = PlaceOrderForm(request.POST or None, initial={
        "delivery_address": request.user.address or "",
        "contact_name": request.user.get_full_name_or_username(),
        "contact_phone": request.user.phone_number or "",
    })

    if request.method == "POST" and form.is_valid():
        result = services.place_order(
            request.user, cart, items, form, request.POST.get("promo_code", ""), request,
        )
        if result.payment_method == "cod":
            result.order.set_status(Order.CONFIRMED)
            messages.success(request, f"{result.order.display_id} placed successfully! Pay cash on delivery.")
            return redirect("order_detail", pk=result.order.pk)
        return render(request, "userapp/upi_payment.html", services.build_upi_payment_context(
            result.order, result.total, result.transaction_ref, result.payment_method,
        ))

    subtotal = cart.total_price
    delivery_charge = services.compute_delivery_charge(subtotal)
    return render(request, "userapp/checkout.html", {
        "form": form, "cart": cart, "items": items,
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "grand_total": subtotal + delivery_charge,
    })


@login_required
def confirm_upi_payment(request, pk):
    """Customer self-reports they've completed the UPI payment.
    Marks it pending-verification; admin confirms manually from the Payments page
    since there's no payment-gateway webhook wired up."""
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    services.confirm_upi_payment_claim(order, request.user)
    messages.success(request, "Thanks! We'll verify your payment shortly and confirm your order.")
    return redirect("order_detail", pk=order.pk)


def order_list_view(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related("items")
    return render(request, "userapp/order_list.html", {"orders": orders})


@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    items = order.items.select_related("product").all()
    delivery_boy_name, delivery_boy_phone = services.order_delivery_contact(order)
    return render(request, "userapp/order_detail.html", {
        "order": order, "items": items,
        "delivery_boy_name": delivery_boy_name,
        "delivery_boy_phone": delivery_boy_phone,
        "tracking_steps": Order.AUTO_PROGRESSION,
    })


@login_required
def order_status_poll(request, pk):
    """AJAX endpoint for order tracking. Returns current status from DB only.
    Status updates ONLY happen when the delivery boy manually changes it."""
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return JsonResponse(services.order_tracking_snapshot(order))


@login_required
def cancel_order_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    if request.method != "POST":
        return redirect("order_detail", pk=order.pk)

    if not order.can_cancel:
        messages.error(request, "This order cannot be cancelled at this stage.")
        return redirect("order_detail", pk=order.pk)

    result = services.cancel_order(order)
    if result.is_late:
        if result.refund_amount is not None:
            messages.success(
                request,
                f"{order.display_id} cancelled. Refund of ₹{result.refund_amount:.0f} initiated "
                f"(delivery charge deducted). Reflects in 5–7 working days.",
            )
        else:
            messages.success(request, f"{order.display_id} cancelled. Refund will be processed as applicable.")
    else:
        messages.success(request, f"{order.display_id} has been cancelled successfully.")

    return redirect("order_detail_cancelled", pk=order.pk)


@login_required
def order_detail_cancelled(request, pk):
    """Shown immediately after cancel. Auto-redirects to home after 60 seconds."""
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, "userapp/order_cancelled.html", {"order": order})


# ─── NOTIFICATIONS ─────────────────────────────────────────────────────────
@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(receiver=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, "userapp/notifications.html", {"notifications": notifs})


@login_required
def clear_notifications(request):
    if request.method == "POST":
        Notification.objects.filter(receiver=request.user).delete()
    return redirect("notifications")


@login_required
def notif_count_ajax(request):
    count = Notification.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({"count": count})


@login_required
def notif_recent_ajax(request):
    notifs = Notification.objects.filter(receiver=request.user).order_by("-created_at")[:10]
    data = [serialize_notification(n) for n in notifs]
    unread = Notification.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({"notifications": data, "unread": unread})


@login_required
def notif_mark_read_ajax(request, pk):
    Notification.objects.filter(pk=pk, receiver=request.user).update(is_read=True)
    return JsonResponse({"ok": True})


@login_required
def clear_all_notifications(request):
    """Delete all notifications for the current user."""
    if request.method == "POST":
        Notification.objects.filter(receiver=request.user).delete()
        messages.success(request, "All notifications cleared.")
    return redirect("notifications")


# ─── ABOUT & CONTACT ────────────────────────────────────────────────────────
def about_view(request):
    return render(request, "userapp/about.html")


def contact_view(request):
    if request.method == "POST":
        created = services.submit_contact_message(request.POST, request.user)
        if created:
            messages.success(request, "✅ Your message has been sent! We'll get back to you within 24 hours.")
            return redirect("contact")
        messages.error(request, "Please fill in all required fields.")
    return render(request, "userapp/contact.html")
