from django import forms

from apps.fleet.models import DamageSeverity


class HandoverProtocolForm(forms.Form):
    mileage = forms.IntegerField(
        label="Przebieg (km)",
        min_value=0,
        widget=forms.NumberInput(
            attrs={"class": "op-input", "inputmode": "numeric", "min": "0"}
        ),
    )
    fuel_level_percent = forms.IntegerField(
        label="Poziom paliwa (%)",
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": "op-input",
                "type": "range",
                "min": "0",
                "max": "100",
            }
        ),
    )
    notes = forms.CharField(
        label="Uwagi",
        required=False,
        widget=forms.Textarea(attrs={"class": "op-input", "rows": 2}),
    )
    signer_name = forms.CharField(
        label="Imie i nazwisko klienta (podpis)",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "op-input", "autocomplete": "name"}),
    )
    signature_image = forms.ImageField(
        label="Podpis (zdjecie)",
        widget=forms.ClearableFileInput(
            attrs={"class": "op-input", "accept": "image/*", "capture": "environment"}
        ),
    )
    new_damage_description = forms.CharField(
        label="Nowe uszkodzenie (opis)",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "op-input", "placeholder": "Opcjonalnie"}
        ),
    )
    new_damage_location = forms.CharField(
        label="Lokalizacja uszkodzenia",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "op-input"}),
    )
    new_damage_severity = forms.ChoiceField(
        label="Stopien",
        required=False,
        choices=[("", "—")] + list(DamageSeverity.choices),
        widget=forms.Select(attrs={"class": "op-input"}),
    )


class ReturnProtocolForm(forms.Form):
    mileage = forms.IntegerField(
        label="Przebieg przy zwrocie (km)",
        min_value=0,
        widget=forms.NumberInput(
            attrs={"class": "op-input", "inputmode": "numeric", "min": "0"}
        ),
    )
    fuel_level_percent = forms.IntegerField(
        label="Poziom paliwa (%)",
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(
            attrs={"class": "op-input", "type": "range", "min": "0", "max": "100"}
        ),
    )
    notes = forms.CharField(
        label="Uwagi",
        required=False,
        widget=forms.Textarea(attrs={"class": "op-input", "rows": 2}),
    )
    surcharge_notes = forms.CharField(
        label="Doplaty (recznie)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "op-input",
                "rows": 2,
                "placeholder": "Np. myjnia, brakujace akcesoria",
            }
        ),
    )
    signer_name = forms.CharField(
        label="Imie i nazwisko klienta (podpis)",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "op-input", "autocomplete": "name"}),
    )
    signature_image = forms.ImageField(
        label="Podpis (zdjecie)",
        widget=forms.ClearableFileInput(
            attrs={"class": "op-input", "accept": "image/*", "capture": "environment"}
        ),
    )
    new_damage_description = forms.CharField(
        label="Nowe uszkodzenie (opis)",
        required=False,
        widget=forms.TextInput(attrs={"class": "op-input"}),
    )
    new_damage_location = forms.CharField(
        label="Lokalizacja",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "op-input"}),
    )
    new_damage_severity = forms.ChoiceField(
        label="Stopien",
        required=False,
        choices=[("", "—")] + list(DamageSeverity.choices),
        widget=forms.Select(attrs={"class": "op-input"}),
    )
