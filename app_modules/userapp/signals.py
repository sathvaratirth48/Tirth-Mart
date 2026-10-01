"""
Keeps each user's Django ``Group`` membership (used for RBAC permission
checks in ``permissions.py``) in sync with their ``role`` field whenever the
user is saved. This is additive only - it never changes the ``role`` field
or the database schema.
"""
import logging

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .choices import UserRole
from .models import CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def sync_user_group(sender, instance, **kwargs):
    try:
        target_group, _ = Group.objects.get_or_create(name=instance.role)
        # Remove from the other role groups, add to the current one.
        other_roles = [r for r in UserRole.values if r != instance.role]
        instance.groups.remove(*Group.objects.filter(name__in=other_roles))
        instance.groups.add(target_group)
    except Exception:  # pragma: no cover - never let a sync issue block a save
        logger.warning("Could not sync RBAC group for user %s", instance.pk, exc_info=True)
