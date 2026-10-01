from datetime import timedelta

from django.db import models
from django.utils import timezone

from .choices import ProductStatus
from .managers import ProductManager
from .utils import discount_percent, fallback_avg_rating, fallback_review_count, star_breakdown


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    ACTIVE = ProductStatus.ACTIVE
    INACTIVE = ProductStatus.INACTIVE
    STATUS_CHOICES = ProductStatus.choices

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(default=0)
    mrp = models.PositiveIntegerField(default=0, blank=True, help_text="Original price before discount (optional)")
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def discount_percent(self):
        return discount_percent(self.mrp, self.price)

    @property
    def is_new(self):
        return self.created_at >= timezone.now() - timedelta(days=14)

    @property
    def avg_rating(self):
        avg = self.reviews.aggregate(avg=models.Avg("rating"))["avg"]
        if avg:
            return round(avg, 1)
        return fallback_avg_rating(self.id)

    @property
    def review_count(self):
        count = self.reviews.count()
        return count if count else fallback_review_count(self.id)

    @property
    def full_stars(self):
        return star_breakdown(self.avg_rating)[0]

    @property
    def has_half_star(self):
        return star_breakdown(self.avg_rating)[1]

    @property
    def empty_stars(self):
        return star_breakdown(self.avg_rating)[2]

    @property
    def full_stars_range(self):
        return range(self.full_stars)

    @property
    def empty_stars_range(self):
        return range(self.empty_stars)
