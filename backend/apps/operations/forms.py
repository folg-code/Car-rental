from django import forms

from apps.fleet.models import DamageSeverity


class _SignatureMixin(forms.Form):
    signer_name = forms.CharField(
        label="Imie i nazwisko klienta (podpis)",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "op-input", "autocomplete": "name"}),
    )
    signature_image = forms.ImageField(
        label="Podpis (zdjecie — opcjonalnie)",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"class": "op-input", "accept": "image/*", "capture": "environment"}
        ),
    )
    signature_data_url = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_signature_data_url"}),
    )

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get("signature_image")
        data_url = (cleaned.get("signature_data_url") or "").strip()
        if not image and not data_url.startswith("data:image/"):
            self.add_error(
                None,
                "Wymagany podpis klienta — narysuj na ekranie albo dolacz zdjecie.",
            )
        return cleaned


class HandoverProtocolForm(_SignatureMixin):
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


class ReturnProtocolForm(_SignatureMixin):
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
