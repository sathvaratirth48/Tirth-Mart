"""Small, pure calculation helpers extracted out of Product's rating
properties so the formulas have names and can be unit tested in isolation."""


def fallback_avg_rating(product_id):
    """Deterministic per-product placeholder rating so product cards never
    look "empty" before real reviews exist. Doesn't jump around on refresh."""
    return round(4.0 + (product_id % 10) / 10, 1)


def fallback_review_count(product_id):
    return 80 + (product_id * 37) % 250


def discount_percent(mrp, price):
    if mrp and mrp > price:
        return round((mrp - price) * 100 / mrp)
    return 0


def star_breakdown(avg_rating):
    """Returns (full_stars, has_half_star, empty_stars) for a 5-star widget."""
    full_stars = int(avg_rating)
    has_half_star = (avg_rating - full_stars) >= 0.3
    empty_stars = 5 - full_stars - (1 if has_half_star else 0)
    return full_stars, has_half_star, empty_stars
