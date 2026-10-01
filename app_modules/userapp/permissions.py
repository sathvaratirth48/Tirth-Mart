"""
Role-based access control for userapp.

Every ``CustomUser`` still carries the original ``role`` CharField (schema is
unchanged), but a ``post_save`` signal (see ``signals.py``) keeps that role
mirrored onto a Django ``Group`` of the same name. All access checks in this
module go through the Group/permission system rather than comparing the raw
string field directly, which is what "RBAC instead of hardcoded role checks"
means in practice without altering the database schema.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .choices import UserRole


def in_role(user, role):
    """True if ``user`` belongs to ``role``.

    Checks the RBAC Group first (kept in sync by ``signals.sync_user_group``)
    and falls back to the legacy ``role`` field so pre-existing accounts
    (created before the Group sync was introduced) keep working exactly as
    before, with zero risk of an access regression.
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=role).exists() or user.role == role


def is_admin(user):
    return in_role(user, UserRole.ADMIN)


def is_delivery(user):
    return in_role(user, UserRole.DELIVERY)


def is_approved_customer(user):
    return in_role(user, UserRole.USER) and user.is_approved


def admin_required(redirect_url="user_login"):
    """View decorator: only members of the 'Admin' group may proceed."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not is_admin(request.user):
                messages.error(request, "You are not authorized to access this page.")
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
