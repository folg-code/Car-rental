from django import forms

from apps.fleet.models import (
    AvailabilityBlock,
    AvailabilityBlockType,
    Car,
    CarCategory,
    CarDocument,
    CarDocumentType,
    CarImage,
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


class CarImageForm(forms.ModelForm):
    class Meta:
        model = CarImage
        fields = ["image", "caption", "is_primary"]
        widgets = {
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,image/gif"}
            ),
            "caption": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2"}
            ),
        }


class CarDocumentForm(forms.ModelForm):
    class Meta:
        model = CarDocument
        fields = [
            "document_type",
            "file",
            "valid_from",
            "valid_until",
            "notes",
        ]
        widgets = {
            "document_type": forms.Select(
                attrs={"class": "w-full border rounded px-3 py-2"}
            ),
            "file": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/*"}
            ),
            "valid_from": forms.DateInput(
                attrs={"type": "date", "class": "w-full border rounded px-3 py-2"}
            ),
            "valid_until": forms.DateInput(
                attrs={"type": "date", "class": "w-full border rounded px-3 py-2"}
            ),
            "notes": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].initial = CarDocumentType.INSURANCE
