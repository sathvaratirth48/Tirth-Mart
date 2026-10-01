from django import forms

from app_modules.userapp.choices import UserRole
from app_modules.userapp.models import CustomUser

from .models import DeliveryBoy, OrderAssignment
from .validators import validate_username_available


class OrderAssignmentForm(forms.ModelForm):
    class Meta:
        model = OrderAssignment
        fields = ("delivery_boy", "notes")
        widgets = {
            "delivery_boy": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control", "placeholder": "Notes (optional)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_boy"].queryset = DeliveryBoy.objects.filter(
            status=DeliveryBoy.AVAILABLE, is_verified=True
        )
        self.fields["delivery_boy"].empty_label = "-- Select Delivery Boy --"


class UpdateAssignmentStatusForm(forms.ModelForm):
    class Meta:
        model = OrderAssignment
        fields = ("status", "notes")
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }


class DeliveryBoyProfileForm(forms.ModelForm):
    class Meta:
        model = DeliveryBoy
        fields = ("vehicle_type", "vehicle_number")


class DeliveryBoyRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = DeliveryBoy
        fields = ["vehicle_type", "vehicle_number"]

    def clean_username(self):
        username = self.cleaned_data["username"]
        validate_username_available(username)
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = CustomUser(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            email=self.cleaned_data["email"],
            phone_number=self.cleaned_data["phone_number"],
            role=UserRole.DELIVERY,
            is_approved=False,
        )
        user.set_password(self.cleaned_data["password"])
        user.save()

        delivery_boy = super().save(commit=False)
        delivery_boy.user = user
        if commit:
            delivery_boy.save()
        return delivery_boy
