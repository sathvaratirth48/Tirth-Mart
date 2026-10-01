# Refactor Notes — Tirth Mart

This document explains what changed structurally (not functionally) in this
refactor, and how to verify it yourself.

## What did NOT change
- Database schema — verified with `python manage.py makemigrations --check`.
  Only **one** new migration exists (`userapp/migrations/0009_alter_customuser_managers.py`)
  and it is a pure Django *metadata* change (registers a custom manager) with
  **zero SQL / ALTER TABLE** — confirmed by inspecting its `operations` list.
- URLs, URL names, templates, static files, media paths.
- Business logic / calculations / notification text / status flows.
- The look and behaviour of every page (verified with an end-to-end smoke
  test against the real `db.sqlite3` you uploaded — see below).

## What changed (structure only)
Each app (`userapp`, `adminapp`, `deliveryapp`) now follows the same layout:

| File | Purpose |
|---|---|
| `models.py` | Schema (unchanged fields), model methods, calculated properties |
| `choices.py` | `TextChoices` enums replacing hardcoded tuples (same DB values) |
| `constants.py` | Magic numbers (delivery charge, promo codes, thresholds) |
| `managers.py` | Custom QuerySet/Manager methods (`Product.objects.low_stock()`, etc.) |
| `forms.py` | `ModelForm`s — views no longer read `request.POST` by hand |
| `validators.py` | Reusable validation functions used by forms |
| `services.py` | All business logic (checkout, cancellation, analytics, RBAC-safe queries) |
| `permissions.py` | Group-based RBAC helpers |
| `signals.py` | Keeps Django `Group` membership in sync with the `role` field |
| `mixins.py` / `utils.py` | Small reusable helpers (AJAX envelopes, formatting) |
| `views.py` | Thin: parse request → call service/form → render/redirect |

## RBAC (requirement #9)
The `role` CharField on `CustomUser` is preserved exactly (no schema change).
A `post_save` signal additionally mirrors it onto a Django `Group` of the
same name ("Admin" / "User" / "Delivery"). `permissions.is_admin(user)` etc.
check the Group **and** fall back to the `role` field, so:
- Existing accounts in your DB keep working immediately (their Group gets
  synced automatically the next time they're saved, or you can run
  `python manage.py shell` and re-save all users once to eagerly sync).
- New Django `Permission`/`Group` machinery is now in place for you to build
  on (e.g. `request.user.groups.filter(name="Admin")`, `user.has_perm(...)`).

## Verification performed
1. `python manage.py check` → 0 issues.
2. `python manage.py makemigrations --check --dry-run` → only the one
   no-op manager migration.
3. Applied that migration to a **copy** of your real `db.sqlite3` and ran a
   full end-to-end smoke test: home → register → login → browse/search →
   add to cart → wishlist → checkout (COD) → order tracking/poll → cancel
   (with restock) → notifications → contact form → admin login → analytics
   → order/product/category/delivery/payment/contact admin screens →
   delivery-boy login → delivery dashboard. All 200 OK, all data correct.
4. `ruff check` (config in `pyproject.toml`) → all checks passed.

## Running it
```bash
pip install -r requirements.txt   # if you don't already have Django installed
python manage.py migrate          # applies the one no-op manager migration
python manage.py runserver
```

## One incidental fix worth knowing about
`update_Product` in `adminapp` now goes through `ProductForm`, which
validates `price > 0` (the same rule already used on product *creation*).
Previously, editing a product did not re-validate price. This only matters
if you were relying on being able to set a product's price to 0 via the
edit screen — everything else behaves identically.
