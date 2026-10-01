from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import DeliveryBoy


def delivery_required(view_func):
    """Allow only verified delivery boys."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            delivery_boy = request.user.delivery_profile
        except DeliveryBoy.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect("login")
        if not delivery_boy.is_verified:
            messages.warning(request, "Your account is pending verification.")
            return redirect("delivery_pending")
        return view_func(request, *args, **kwargs)

    return wrapper
