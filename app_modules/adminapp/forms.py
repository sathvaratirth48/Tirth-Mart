from django import forms

from app_modules.deliveryapp.models import DeliveryBoy
from app_modules.userapp.models import CustomUser, Notification, Order

from .models import Category, Product
from .validators import validate_positive_price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "description", "price", "stock_quantity", "image", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_price(self):
        price = self.cleaned_data.get("price")
        validate_positive_price(price)
        return price


class OrderAdminForm(forms.ModelForm):
    """Used by the admin "edit order" screen (customer / total / status /
    address are all hand-editable there)."""

    class Meta:
        model = Order
        fields = ("customer", "total_amount", "status", "delivery_address")


class DeliveryBoyAdminForm(forms.ModelForm):
    class Meta:
        model = DeliveryBoy
        fields = ("user", "vehicle_type", "vehicle_number", "status", "is_verified")


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ("receiver", "title", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}


class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "phone_number", "address", "profile_image")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
