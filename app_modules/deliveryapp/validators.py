from django.core.exceptions import ValidationError

from app_modules.userapp.models import CustomUser


def validate_username_available(username):
    if CustomUser.objects.filter(username=username).exists():
        raise ValidationError("This username is already taken.")
