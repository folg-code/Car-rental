from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.fleet.models import CarCategory
from apps.fleet.services.availability import AvailabilityService


class AvailabilitySearchForm(forms.Form):
    """Formularz dat odbioru i zwrotu (task 8.10)."""

    start_at = forms.DateTimeField(
        label="Data odbioru",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    end_at = forms.DateTimeField(
        label="Data zwrotu",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    category = forms.ModelChoiceField(
        label="Kategoria",
        queryset=CarCategory.objects.none(),
        required=False,
        empty_label="Wszystkie kategorie",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = CarCategory.objects.order_by(
            "sort_order",
            "name",
        )

    def _make_aware(self, value):
        if value is not None and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    def clean_start_at(self):
        return self._make_aware(self.cleaned_data.get("start_at"))

    def clean_end_at(self):
        return self._make_aware(self.cleaned_data.get("end_at"))

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        end_at = cleaned.get("end_at")
        if start_at and end_at:
            try:
                AvailabilityService.validate_interval(start_at, end_at)
            except ValidationError as exc:
                message = exc.messages[0] if exc.messages else str(exc)
                raise forms.ValidationError(message) from exc
        return cleaned
