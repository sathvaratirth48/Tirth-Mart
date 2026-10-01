from django.core.exceptions import ValidationError


def validate_positive_price(price):
    if price is not None and price <= 0:
        raise ValidationError("Price must be greater than 0.")
