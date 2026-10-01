from django.db import models

from .choices import ProductStatus


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=ProductStatus.ACTIVE)

    def in_stock(self):
        return self.filter(stock_quantity__gt=0)

    def low_stock(self, threshold=10):
        return self.filter(stock_quantity__gt=0, stock_quantity__lte=threshold)

    def out_of_stock(self):
        return self.filter(stock_quantity=0)

    def with_category(self):
        return self.select_related("category")


ProductManager = ProductQuerySet.as_manager
