"""Business constants for userapp. Centralising these avoids magic numbers
scattered across views/services and makes the business rules easy to find."""

# ─── Checkout ──────────────────────────────────────────────────────────────
FREE_DELIVERY_THRESHOLD = 499
STANDARD_DELIVERY_CHARGE = 49

# ₹ delivery handling charge deducted when a customer cancels a UPI-paid
# order after it has already been picked up / gone out for delivery.
LATE_CANCELLATION_DEDUCTION = 20

# Promo code registry - could be DB-driven later. For now one hardcoded code.
PROMO_CODES = {
    "TIRTH50": {"discount_pct": 10, "description": "10% off on your order"},
}

# ─── Registration ──────────────────────────────────────────────────────────
# DOB year restriction: users claiming a birth year in this (inclusive) range
# are rejected as invalid during registration.
DOB_INVALID_YEAR_MIN = 2020
DOB_INVALID_YEAR_MAX = 2026

# ─── Inventory ─────────────────────────────────────────────────────────────
LOW_STOCK_THRESHOLD = 10

# ─── Notifications ─────────────────────────────────────────────────────────
RECENT_NOTIFICATIONS_LIMIT = 10
