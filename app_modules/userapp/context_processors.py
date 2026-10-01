from .models import Cart, Order, Wishlist


def header_counts(request):
    """Provide cart_count, wishlist_count and recent orders for the header on every page."""
    cart_count = 0
    wishlist_count = 0
    recent_orders = []
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.total_quantity
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        if request.user.is_customer_role:
            recent_orders = Order.objects.filter(customer=request.user).prefetch_related("items")[:3]
    return {
        "header_cart_count": cart_count,
        "header_wishlist_count": wishlist_count,
        "header_recent_orders": recent_orders,
    }
