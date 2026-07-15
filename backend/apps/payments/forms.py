from django import forms
from django.utils import timezone

from apps.payments.models import PaymentMethod, PaymentType

_DATETIME_INPUT_FORMATS = [
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]


class PaymentRecordForm(forms.Form):
    payment_type = forms.ChoiceField(
        label="Typ platnosci",
        choices=PaymentType.choices,
        initial=PaymentType.RENTAL_FEE,
    )
    method = forms.ChoiceField(
        label="Metoda",
        choices=[
            (PaymentMethod.CASH, "Gotowka"),
            (PaymentMethod.BANK_TRANSFER, "Przelew"),
            (PaymentMethod.CARD, "Karta"),
            (PaymentMethod.BLIK, "BLIK"),
        ],
    )
    amount = forms.DecimalField(
        label="Kwota (PLN)",
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
    )
    paid_at = forms.DateTimeField(
        label="Data płatności",
        required=False,
        input_formats=_DATETIME_INPUT_FORMATS,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    notes = forms.CharField(
        label="Notatka",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Opcjonalnie"}),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            now = timezone.localtime()
            self.fields["paid_at"].initial = now.strftime("%Y-%m-%dT%H:%M")

    def clean_paid_at(self):
        value = self.cleaned_data.get("paid_at")
        if value is not None and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value
