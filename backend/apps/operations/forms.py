"""Formulare krokowe protokolow wydania/zwrotu."""

from django import forms

from apps.fleet.models import DamageType
from apps.operations.models import (
    EquipmentLineStatus,
    ProtocolPhotoCategory,
    SettlementLineDecision,
    SignatureOutcome,
)


class _SignatureMixin(forms.Form):
    signer_name = forms.CharField(
        max_length=120, required=False, label="Imie i nazwisko"
    )
    signature_image = forms.ImageField(required=False)
    signature_data_url = forms.CharField(required=False, widget=forms.HiddenInput())
    customer_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Uwagi klienta",
    )

    def clean(self):
        cleaned = super().clean()
        return cleaned


class DriverStepForm(forms.Form):
    first_name = forms.CharField(max_length=80, label="Imie")
    last_name = forms.CharField(max_length=80, label="Nazwisko")
    email = forms.EmailField(required=False, label="E-mail")
    phone = forms.CharField(max_length=30, required=False, label="Telefon")
    address = forms.CharField(max_length=255, required=False, label="Adres")
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Data urodzenia",
    )
    id_document_type = forms.CharField(
        max_length=40, required=False, label="Rodzaj dokumentu"
    )
    id_document_number = forms.CharField(
        max_length=60, required=False, label="Numer dokumentu"
    )
    id_document_country = forms.CharField(
        max_length=60, required=False, label="Kraj wydania dokumentu"
    )
    license_number = forms.CharField(
        max_length=60, required=False, label="Numer prawa jazdy"
    )
    license_country = forms.CharField(
        max_length=60, required=False, label="Kraj wydania PJ"
    )
    license_issued_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Data wydania PJ",
    )
    license_expires_at = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Waznosc PJ",
    )
    document_verified = forms.BooleanField(
        required=False, label="Zgodnosc z dokumentem"
    )
    license_valid = forms.BooleanField(required=False, label="Prawo jazdy wazne")
    license_category_ok = forms.BooleanField(
        required=False,
        label="Uprawnienia do kategorii pojazdu",
    )


class OdometerStepForm(forms.Form):
    mileage = forms.IntegerField(min_value=0, label="Przebieg (km)")
    fuel_level_percent = forms.IntegerField(
        min_value=0,
        max_value=100,
        label="Poziom paliwa (%)",
        widget=forms.NumberInput(
            attrs={
                "type": "range",
                "min": "0",
                "max": "100",
                "step": "1",
                "class": "w-full",
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Uwagi",
    )
    odometer_photo = forms.ImageField(required=False, label="Zdjecie licznika")
    fuel_photo = forms.ImageField(required=False, label="Zdjecie wskaznika paliwa")
    actual_return_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Rzeczywisty zwrot",
    )
    return_location = forms.CharField(
        max_length=200, required=False, label="Miejsce zwrotu"
    )
    organizational_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Uwagi organizacyjne",
    )


class DamageMarkerForm(forms.Form):
    damage_type = forms.ChoiceField(choices=DamageType.choices, label="Typ")
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Opis",
    )
    size_note = forms.CharField(max_length=80, required=False, label="Rozmiar")
    pos_x = forms.DecimalField(min_value=0, max_value=100, label="X %")
    pos_y = forms.DecimalField(min_value=0, max_value=100, label="Y %")
    photo = forms.ImageField(required=False, label="Zdjecie")


class InteriorStepForm(forms.Form):
    interior_ok = forms.BooleanField(
        required=False, initial=True, label="Wnetrze bez uwag"
    )
    interior_issues = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("dirt", "Zabrudzenie"),
            ("upholstery", "Uszkodzenie tapicerki"),
            ("smoke", "Slady palenia"),
            ("smell", "Nieprzyjemny zapach"),
            ("damage", "Uszkodzenie elementu wnetrza"),
            ("missing", "Brak elementu"),
            ("other", "Inne"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Problemy wnetrza",
    )
    interior_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Opis wnetrza",
    )
    inspection_ok = forms.BooleanField(
        required=False,
        initial=True,
        label="Brak widocznych problemow technicznych",
    )
    inspection_issues = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("warning_lights", "Aktywne kontrolki"),
            ("technical_damage", "Widoczne uszkodzenie techniczne"),
            ("other", "Inne uwagi"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Kontrola podstawowa",
    )
    inspection_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Uwagi techniczne",
    )


class CleanlinessStepForm(forms.Form):
    body = forms.ChoiceField(
        choices=[
            ("clean", "Pojazd czysty"),
            ("normal", "Standardowo zabrudzony"),
            ("dirty_return", "Zwrot brudnego pojazdu"),
            ("blocks_assessment", "Zabrudzenie utrudniajace ocene"),
        ],
        label="Nadwozie",
    )
    interior = forms.ChoiceField(
        choices=[
            ("clean", "Wnetrze czyste"),
            ("normal", "Standardowe slady uzytkowania"),
            ("excessive", "Ponadstandardowe zabrudzenie"),
            ("upholstery_dirty", "Zabrudzenie tapicerki"),
            ("needs_wash", "Tapicerka wymagajaca prania"),
            ("smoke", "Slady palenia"),
            ("pets", "Siersc / zwierzeta"),
            ("other", "Inne"),
        ],
        label="Wnetrze",
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Opis zabrudzenia",
    )
    photo = forms.ImageField(required=False, label="Zdjecie czystosci")
    fee_suggestion = forms.DecimalField(
        required=False,
        min_value=0,
        label="Propozycja oplaty (PLN)",
    )


class SignatureStepForm(_SignatureMixin):
    outcome = forms.ChoiceField(
        choices=SignatureOutcome.choices,
        initial=SignatureOutcome.SIGNED,
        label="Wynik podpisu",
    )
    closure_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Przyczyna zamkniecia bez podpisu",
    )


# --- Legacy monolithic forms (zachowane dla kompatybilnosci testow widokow) ---


class HandoverProtocolForm(_SignatureMixin):
    mileage = forms.IntegerField(min_value=0, label="Przebieg (km)")
    fuel_level_percent = forms.IntegerField(
        min_value=0,
        max_value=100,
        label="Paliwo %",
        widget=forms.NumberInput(attrs={"type": "range", "min": 0, "max": 100}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    new_damage_description = forms.CharField(required=False)
    new_damage_location = forms.CharField(required=False)
    new_damage_severity = forms.CharField(required=False)

    def clean(self):
        cleaned = super().clean()
        has_img = cleaned.get("signature_image")
        has_url = (cleaned.get("signature_data_url") or "").startswith("data:image/")
        if not has_img and not has_url:
            raise forms.ValidationError("Wymagany podpis.")
        if not (cleaned.get("signer_name") or "").strip():
            raise forms.ValidationError("Podaj imie i nazwisko.")
        return cleaned


class ReturnProtocolForm(HandoverProtocolForm):
    surcharge_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


PHOTO_CATEGORY_LABELS = dict(ProtocolPhotoCategory.choices)
EQUIPMENT_STATUS_CHOICES = EquipmentLineStatus.choices
SETTLEMENT_DECISION_CHOICES = SettlementLineDecision.choices
