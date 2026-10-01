from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "stock_quantity", "status", "is_in_stock", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "category__name")
    list_editable = ("price", "stock_quantity", "status")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
