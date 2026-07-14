from __future__ import annotations

from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.fleet.models import Car, CarCategory
from apps.fleet.selectors.car import list_active_cars
from apps.fleet.services.availability import AvailabilityService
from apps.pricing.selectors.price_list import (
    get_price_list_for_date,
    list_active_extras,
)


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


class PriceQuoteForm(forms.Form):
    """Formularz orientacyjnej wyceny (task 8.11)."""

    car = forms.ModelChoiceField(
        label="Pojazd",
        queryset=Car.objects.none(),
        empty_label="Wybierz pojazd",
    )
    start_at = forms.DateTimeField(
        label="Data odbioru",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    end_at = forms.DateTimeField(
        label="Data zwrotu",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    extras = forms.MultipleChoiceField(
        label="Uslugi dodatkowe",
        required=False,
        choices=(),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["car"].queryset = list_active_cars()
        self.fields["car"].label_from_instance = lambda car: (
            f"{car.make} {car.model} ({car.category.name})"
        )
        self._set_extra_choices()

    def _start_date_for_extras(self) -> date | None:
        if self.is_bound:
            raw = self.data.get("start_at")
            if raw:
                parsed = forms.DateTimeField(
                    input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]
                ).to_python(raw)
                if parsed is not None:
                    return parsed.date()
        initial_start = self.initial.get("start_at")
        if isinstance(initial_start, datetime):
            return initial_start.date()
        return timezone.now().date()

    def _set_extra_choices(self) -> None:
        price_list = get_price_list_for_date(self._start_date_for_extras())
        if price_list is None:
            self.fields["extras"].choices = []
            return
        self.fields["extras"].choices = [
            (extra.code, extra.name) for extra in list_active_extras(price_list)
        ]

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


class PublicBookingForm(forms.Form):
    """Formularz rezerwacji online (task 8.12)."""

    car = forms.ModelChoiceField(
        label="Pojazd",
        queryset=Car.objects.none(),
        empty_label="Wybierz pojazd",
    )
    start_at = forms.DateTimeField(
        label="Data odbioru",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    end_at = forms.DateTimeField(
        label="Data zwrotu",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    first_name = forms.CharField(label="Imie", max_length=80)
    last_name = forms.CharField(label="Nazwisko", max_length=80)
    email = forms.EmailField(label="E-mail", required=False)
    phone = forms.CharField(label="Telefon", max_length=32, required=False)
    extras = forms.MultipleChoiceField(
        label="Uslugi dodatkowe",
        required=False,
        choices=(),
        widget=forms.CheckboxSelectMultiple,
    )
    notes = forms.CharField(
        label="Uwagi",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    accept_terms = forms.BooleanField(
        label="Akceptuje regulamin wynajmu",
        required=True,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["car"].queryset = list_active_cars()
        self.fields["car"].label_from_instance = lambda car: (
            f"{car.make} {car.model} ({car.category.name})"
        )
        self._set_extra_choices()

    def _start_date_for_extras(self) -> date | None:
        if self.is_bound:
            raw = self.data.get("start_at")
            if raw:
                parsed = forms.DateTimeField(
                    input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]
                ).to_python(raw)
                if parsed is not None:
                    return parsed.date()
        initial_start = self.initial.get("start_at")
        if isinstance(initial_start, datetime):
            return initial_start.date()
        return timezone.now().date()

    def _set_extra_choices(self) -> None:
        price_list = get_price_list_for_date(self._start_date_for_extras())
        if price_list is None:
            self.fields["extras"].choices = []
            return
        self.fields["extras"].choices = [
            (extra.code, extra.name) for extra in list_active_extras(price_list)
        ]

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
        email = (cleaned.get("email") or "").strip()
        phone = (cleaned.get("phone") or "").strip()
        if not email and not phone:
            raise forms.ValidationError(
                "Podaj co najmniej adres e-mail lub numer telefonu."
            )
        if start_at and end_at:
            try:
                AvailabilityService.validate_interval(start_at, end_at)
            except ValidationError as exc:
                message = exc.messages[0] if exc.messages else str(exc)
                raise forms.ValidationError(message) from exc
        return cleaned
