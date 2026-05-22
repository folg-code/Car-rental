from django import forms

from apps.fleet.models import CarCategory
from apps.pricing.models import (
    DailyRate,
    ExtraService,
    PriceList,
    PricingRule,
)


class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = [
            "name",
            "slug",
            "description",
            "currency",
            "valid_from",
            "valid_to",
            "is_active",
            "is_default",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_to": forms.DateInput(attrs={"type": "date"}),
        }


class DailyRateForm(forms.ModelForm):
    class Meta:
        model = DailyRate
        fields = ["category", "amount"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = CarCategory.objects.order_by(
            "sort_order", "name"
        )


class PricingRuleForm(forms.ModelForm):
    class Meta:
        model = PricingRule
        fields = [
            "rule_type",
            "name",
            "amount_type",
            "value",
            "valid_from",
            "valid_to",
            "min_rental_days",
            "priority",
            "is_active",
        ]
        widgets = {
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_to": forms.DateInput(attrs={"type": "date"}),
            "value": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "min_rental_days": forms.NumberInput(attrs={"min": "1"}),
            "priority": forms.NumberInput(attrs={"min": "0"}),
        }


class ExtraServiceForm(forms.ModelForm):
    class Meta:
        model = ExtraService
        fields = [
            "code",
            "name",
            "description",
            "charge_type",
            "amount",
            "sort_order",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }
