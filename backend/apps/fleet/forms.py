from django import forms

from apps.fleet.models import (
    AvailabilityBlock,
    AvailabilityBlockType,
    Car,
    CarCategory,
    Damage,
    DamageSeverity,
)


class CarCategoryForm(forms.ModelForm):
    class Meta:
        model = CarCategory
        fields = ["name", "slug", "description", "sort_order", "deposit"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "slug": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
            "sort_order": forms.NumberInput(attrs={"class": "form-input"}),
            "deposit": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.01", "min": "0"}
            ),
        }


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            "category",
            "registration_number",
            "make",
            "model",
            "year",
            "vin",
            "color",
            "status",
            "fuel_type",
            "mileage",
            "seats",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class AvailabilityBlockForm(forms.ModelForm):
    class Meta:
        model = AvailabilityBlock
        fields = ["start_at", "end_at", "block_type", "reason"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "reason": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["block_type"].initial = AvailabilityBlockType.SERVICE


class DamageForm(forms.ModelForm):
    class Meta:
        model = Damage
        fields = ["description", "location", "severity"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "severity": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["severity"].initial = DamageSeverity.MINOR
