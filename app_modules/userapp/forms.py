from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .choices import CheckoutPaymentOption
from .models import CustomUser, Order
from .validators import validate_delivery_address, validate_phone_number


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = (
            "username", "first_name", "last_name", "email", "phone_number", "address",
            "date_of_birth", "aadhaar_number", "pan_number", "aadhaar_image", "pan_image",
            "other_document_image",
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "phone_number", "address", "date_of_birth", "profile_image")
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "address": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class PlaceOrderForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=CheckoutPaymentOption.choices,
        initial=CheckoutPaymentOption.COD,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Order
        fields = ("contact_name", "contact_phone", "delivery_address")
        widgets = {
            "contact_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name for delivery"}),
            "contact_phone": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "10-digit mobile number",
                "maxlength": "10", "pattern": r"\d{10}",
            }),
            "delivery_address": forms.Textarea(attrs={
                "rows": 3, "class": "form-control",
                "placeholder": "House no, street, area, city, pincode",
            }),
        }

    def clean_contact_name(self):
        name = self.cleaned_data.get("contact_name", "").strip()
        if not name:
            raise forms.ValidationError("Please enter the full name for delivery.")
        return name

    def clean_contact_phone(self):
        phone = self.cleaned_data.get("contact_phone", "")
        validate_phone_number(phone)
        return phone.strip()

    def clean_delivery_address(self):
        address = self.cleaned_data.get("delivery_address", "")
        validate_delivery_address(address)
        return address.strip()


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
