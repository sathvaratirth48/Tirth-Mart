"""
Reusable validation helpers for userapp.

These are plain functions (not ``django.core.validators`` field validators)
so they can be called from ``Form.clean()`` methods without changing any
model field's ``deconstruct()`` signature - i.e. without triggering new,
unnecessary database migrations.
"""
from django.core.exceptions import ValidationError

from .constants import DOB_INVALID_YEAR_MAX, DOB_INVALID_YEAR_MIN


def validate_dob_year(date_of_birth):
    """Reject a date of birth whose year falls in the disallowed range.

    Mirrors the original inline check: users born between
    ``DOB_INVALID_YEAR_MIN`` and ``DOB_INVALID_YEAR_MAX`` (inclusive) are
    considered invalid registrations (e.g. someone claiming to be a toddler).
    """
    if date_of_birth is None:
        return
    if DOB_INVALID_YEAR_MIN <= date_of_birth.year <= DOB_INVALID_YEAR_MAX:
        raise ValidationError(
            "Invalid Date of Birth. Please select a valid year "
            f"({DOB_INVALID_YEAR_MIN - 1} or earlier)."
        )


def validate_dob_year_string(dob_str):
    """Same rule as ``validate_dob_year`` but accepts the raw ``YYYY-MM-DD``
    string as submitted by an HTML date input (used before the value is
    parsed into a model instance). Silently ignores unparseable input,
    mirroring the original inline behaviour."""
    if not dob_str:
        return
    try:
        dob_year = int(dob_str.split("-")[0])
    except (ValueError, IndexError):
        return
    if DOB_INVALID_YEAR_MIN <= dob_year <= DOB_INVALID_YEAR_MAX:
        raise ValidationError(
            "Invalid Date of Birth. Please select a valid year "
            f"({DOB_INVALID_YEAR_MIN - 1} or earlier)."
        )


def validate_phone_number(phone, length=10):
    """A phone number must be exactly ``length`` digits."""
    phone = (phone or "").strip()
    if not phone.isdigit() or len(phone) != length:
        raise ValidationError(f"Please enter a valid {length}-digit phone number.")
    return phone


def validate_delivery_address(address, min_length=10):
    address = (address or "").strip()
    if len(address) < min_length:
        raise ValidationError("Please enter a complete delivery address.")
    return address
