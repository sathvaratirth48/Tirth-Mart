from django.contrib.auth.models import UserManager
from django.db import models

from .choices import OrderStatus, UserRole


class CustomUserManager(UserManager):
    """Adds role/approval-aware convenience querysets on top of the
    default Django ``UserManager`` (so ``createsuperuser`` etc. still work)."""

    def customers(self):
        return self.filter(role=UserRole.USER)

    def admins(self):
        return self.filter(role=UserRole.ADMIN)

    def delivery_boys(self):
        return self.filter(role=UserRole.DELIVERY)

    def non_admins(self):
        return self.exclude(role=UserRole.ADMIN)

    def approved_customers(self):
        return self.filter(role=UserRole.USER, is_approved=True)

    def pending_customers(self):
        return self.filter(role=UserRole.USER, is_approved=False)

    def approved_admins(self):
        return self.filter(role=UserRole.ADMIN, is_approved=True)


class OrderQuerySet(models.QuerySet):
    def for_customer(self, user):
        return self.filter(customer=user)

    def with_items(self):
        return self.prefetch_related("items__product")

    def active(self):
        return self.exclude(status__in=OrderStatus.terminal_statuses())

    def pending_admin_action(self):
        return self.filter(status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING])


OrderManager = OrderQuerySet.as_manager
