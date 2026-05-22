from django import forms
from django.utils import timezone

from apps.bookings.models import (
    Customer,
    Reservation,
    ReservationStatus,
)
from apps.fleet.models import Car, CarStatus
from apps.pricing.models import PriceList


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "company_name",
            "tax_id",
            "street",
            "city",
            "postal_code",
            "country",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            "customer",
            "car",
            "start_at",
            "end_at",
            "status",
            "pricing_mode",
            "price_list",
            "custom_total",
            "notes",
        ]
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["car"].queryset = Car.objects.filter(
            status=CarStatus.ACTIVE
        ).select_related("category")
        self.fields["customer"].queryset = Customer.objects.order_by(
            "last_name", "first_name"
        )
        self.fields["price_list"].queryset = PriceList.objects.filter(
            is_active=True
        ).order_by("-is_default", "name")
        self.fields["price_list"].required = False
        self.fields["custom_total"].required = False
        self.fields["custom_total"].widget.attrs.update(
            {"step": "0.01", "min": "0.01", "placeholder": "np. 1500.00"}
        )
        if self.instance.pk:
            editable_statuses = [
                ReservationStatus.DRAFT,
                ReservationStatus.PENDING_PAYMENT,
                ReservationStatus.CONFIRMED,
            ]
            if self.instance.status not in editable_statuses:
                self.fields["status"].disabled = True

    def _make_aware(self, value):
        if value is not None and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    def clean_start_at(self):
        return self._make_aware(self.cleaned_data.get("start_at"))

    def clean_end_at(self):
        return self._make_aware(self.cleaned_data.get("end_at"))


class ReservationCancelForm(forms.Form):
    reason = forms.CharField(
        label="Powod anulowania",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2"}),
    )
