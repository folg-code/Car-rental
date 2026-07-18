from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.fleet.fuel import (
    FUEL_LEVEL_CHOICES,
    fuel_level_to_percent,
    percent_to_fuel_level,
)
from apps.fleet.models import DamageSeverity, DamageStatus, DamageType


class ProtocolStatus(models.TextChoices):
    DRAFT = "draft", "Szkic"
    READY_FOR_SIGNATURE = "ready_for_signature", "Gotowy do podpisu"
    COMPLETED = "completed", "Zakonczony"
    CLOSED_WITHOUT_SIGNATURE = "closed_without_signature", "Zamkniety bez podpisu"


class ProtocolPhotoCategory(models.TextChoices):
    ODOMETER = "odometer", "Licznik"
    FUEL_GAUGE = "fuel_gauge", "Wskaznik paliwa"
    FRONT = "front", "Przod"
    REAR = "rear", "Tyl"
    LEFT = "left", "Lewy bok"
    RIGHT = "right", "Prawy bok"
    INTERIOR_FRONT = "interior_front", "Wnetrze przod"
    INTERIOR_REAR = "interior_rear", "Wnetrze tyl"
    TRUNK = "trunk", "Bagaznik"
    DETAIL = "detail", "Szczegol"
    OTHER = "other", "Inne"


class EquipmentLineStatus(models.TextChoices):
    PENDING = "pending", "Do potwierdzenia"
    HANDED = "handed", "Przekazano"
    MISSING = "missing", "Brak"
    RETURNED = "returned", "Zwrocono"
    RETURNED_DAMAGED = "returned_damaged", "Zwrocono uszkodzone"
    NOT_RETURNED = "not_returned", "Nie zwrocono"
    NOTE = "note", "Uwaga"


class DamageMarkerResolution(models.TextChoices):
    ACTIVE = "active", "Aktywne"
    MISTAKEN = "mistaken", "Dodane omylkowo"
    REPAIRED = "repaired", "Naprawione"
    OBSOLETE = "obsolete", "Nieaktualne"
    NEEDS_ASSESSMENT = "needs_assessment", "Wymaga oceny"
    NEEDS_QUOTE = "needs_quote", "Wymaga wyceny"
    REPORTED_AT_RETURN = "reported_at_return", "Zgloszone przy zwrocie"


class SettlementLineDecision(models.TextChoices):
    PENDING = "pending", "Do decyzji"
    APPROVED = "approved", "Zatwierdzona"
    REJECTED = "rejected", "Odrzucona"
    DEFERRED = "deferred", "Do pozniejszej wyceny"


class SignatureOutcome(models.TextChoices):
    SIGNED = "signed", "Podpisano"
    SIGNED_WITH_NOTES = "signed_with_notes", "Podpisano z uwagami"
    REFUSED = "refused", "Odmowa podpisu"
    ABSENT = "absent", "Klient nieobecny"


HANDOVER_STEPS: tuple[str, ...] = (
    "select",
    "driver",
    "odometer",
    "damages",
    "photos",
    "interior",
    "equipment",
    "summary",
    "signature",
)

RETURN_STEPS: tuple[str, ...] = (
    "select",
    "odometer",
    "damages",
    "photos",
    "equipment",
    "cleanliness",
    "settlement",
    "summary",
    "signature",
)

RETURN_REQUIRED_PHOTO_CATEGORIES: tuple[str, ...] = (
    ProtocolPhotoCategory.FRONT,
    ProtocolPhotoCategory.REAR,
    ProtocolPhotoCategory.LEFT,
    ProtocolPhotoCategory.RIGHT,
    ProtocolPhotoCategory.INTERIOR_FRONT,
    ProtocolPhotoCategory.INTERIOR_REAR,
    ProtocolPhotoCategory.TRUNK,
)


class HandoverProtocol(models.Model):
    """Protokol wydania pojazdu — draft od startu, niemutowalny po zakonczeniu."""

    rental = models.OneToOneField(
        "bookings.Rental",
        on_delete=models.PROTECT,
        related_name="handover_protocol",
    )
    status = models.CharField(
        max_length=32,
        choices=ProtocolStatus.choices,
        default=ProtocolStatus.DRAFT,
        db_index=True,
    )
    current_step = models.CharField(max_length=32, default="driver")
    mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Przebieg przy wydaniu (km).",
    )
    fuel_level = models.CharField(
        max_length=20,
        choices=FUEL_LEVEL_CHOICES,
        blank=True,
        default="",
    )
    fuel_level_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Kompatybilnosc wsteczna / cache procentu.",
    )
    interior_notes = models.JSONField(default=dict, blank=True)
    inspection_notes = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handovers_completed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "protokol wydania"
        verbose_name_plural = "protokoly wydania"

    def __str__(self) -> str:
        return f"Wydanie — wynajem #{self.rental_id}"

    @property
    def is_completed(self) -> bool:
        return (
            self.status
            in {
                ProtocolStatus.COMPLETED,
                ProtocolStatus.CLOSED_WITHOUT_SIGNATURE,
            }
            or self.completed_at is not None
        )

    @property
    def is_locked(self) -> bool:
        return self.is_completed

    def sync_fuel_percent(self) -> None:
        """Uzupelnij brakujace pole skali lub procentu (bez nadpisywania)."""
        if self.fuel_level and self.fuel_level_percent is None:
            self.fuel_level_percent = fuel_level_to_percent(self.fuel_level)
        elif self.fuel_level_percent is not None and not self.fuel_level:
            self.fuel_level = percent_to_fuel_level(self.fuel_level_percent)

    def clean(self) -> None:
        super().clean()
        if self.is_completed and self.mileage is None:
            raise ValidationError("Uzupelnij przebieg przed zakonczeniem protokolu.")
        if (
            self.is_completed
            and not self.fuel_level
            and self.fuel_level_percent is None
        ):
            raise ValidationError("Uzupelnij poziom paliwa przed zakonczeniem.")


class ReturnProtocol(models.Model):
    """Protokol zwrotu pojazdu — wymaga zakonczonego protokolu wydania."""

    rental = models.OneToOneField(
        "bookings.Rental",
        on_delete=models.PROTECT,
        related_name="return_protocol",
    )
    handover = models.OneToOneField(
        HandoverProtocol,
        on_delete=models.PROTECT,
        related_name="return_protocol",
    )
    status = models.CharField(
        max_length=32,
        choices=ProtocolStatus.choices,
        default=ProtocolStatus.DRAFT,
        db_index=True,
    )
    current_step = models.CharField(max_length=32, default="odometer")
    mileage = models.PositiveIntegerField(null=True, blank=True)
    fuel_level = models.CharField(
        max_length=20,
        choices=FUEL_LEVEL_CHOICES,
        blank=True,
        default="",
    )
    fuel_level_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    actual_return_at = models.DateTimeField(null=True, blank=True)
    return_location = models.CharField(max_length=200, blank=True)
    organizational_notes = models.TextField(blank=True)
    cleanliness = models.JSONField(default=dict, blank=True)
    surcharge_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    signature_outcome = models.CharField(
        max_length=32,
        choices=SignatureOutcome.choices,
        blank=True,
        default="",
    )
    closure_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returns_completed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "protokol zwrotu"
        verbose_name_plural = "protokoly zwrotu"

    def __str__(self) -> str:
        return f"Zwrot — wynajem #{self.rental_id}"

    @property
    def is_completed(self) -> bool:
        return (
            self.status
            in {
                ProtocolStatus.COMPLETED,
                ProtocolStatus.CLOSED_WITHOUT_SIGNATURE,
            }
            or self.completed_at is not None
        )

    @property
    def is_locked(self) -> bool:
        return self.is_completed

    @property
    def mileage_driven(self) -> int | None:
        if (
            self.handover_id
            and self.mileage is not None
            and self.handover.mileage is not None
        ):
            return max(0, self.mileage - self.handover.mileage)
        return None

    def sync_fuel_percent(self) -> None:
        """Uzupelnij brakujace pole skali lub procentu (bez nadpisywania)."""
        if self.fuel_level and self.fuel_level_percent is None:
            self.fuel_level_percent = fuel_level_to_percent(self.fuel_level)
        elif self.fuel_level_percent is not None and not self.fuel_level:
            self.fuel_level = percent_to_fuel_level(self.fuel_level_percent)


class ProtocolDriver(models.Model):
    """Snapshot danych kierowcy przy wydaniu (nie zastepuje Customer)."""

    handover = models.OneToOneField(
        HandoverProtocol,
        on_delete=models.CASCADE,
        related_name="driver",
    )
    is_additional = models.BooleanField(default=False)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    id_document_type = models.CharField(max_length=40, blank=True)
    id_document_number = models.CharField(max_length=60, blank=True)
    id_document_country = models.CharField(max_length=60, blank=True)
    license_number = models.CharField(max_length=60, blank=True)
    license_country = models.CharField(max_length=60, blank=True)
    license_issued_at = models.DateField(null=True, blank=True)
    license_expires_at = models.DateField(null=True, blank=True)
    document_verified = models.BooleanField(default=False)
    license_valid = models.BooleanField(default=False)
    license_category_ok = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "kierowca protokolu"
        verbose_name_plural = "kierowcy protokolu"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or f"Kierowca #{self.pk}"


class ProtocolPhoto(models.Model):
    handover = models.ForeignKey(
        HandoverProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="photos",
    )
    return_protocol = models.ForeignKey(
        ReturnProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="photos",
    )
    damage_marker = models.ForeignKey(
        "ProtocolDamageMarker",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="photos",
    )
    category = models.CharField(
        max_length=32,
        choices=ProtocolPhotoCategory.choices,
        default=ProtocolPhotoCategory.OTHER,
    )
    image = models.ImageField(upload_to="operations/protocols/%Y/%m/")
    caption = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "zdjecie protokolu"
        verbose_name_plural = "zdjecia protokolu"

    def clean(self) -> None:
        super().clean()
        if bool(self.handover_id) == bool(self.return_protocol_id):
            raise ValidationError(
                "Zdjecie musi nalezec do protokolu wydania lub zwrotu."
            )


class Signature(models.Model):
    handover = models.OneToOneField(
        HandoverProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="signature",
    )
    return_protocol = models.OneToOneField(
        ReturnProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="signature",
    )
    signer_name = models.CharField(max_length=120)
    image = models.ImageField(
        upload_to="operations/signatures/%Y/%m/",
        null=True,
        blank=True,
    )
    customer_notes = models.TextField(blank=True)
    outcome = models.CharField(
        max_length=32,
        choices=SignatureOutcome.choices,
        default=SignatureOutcome.SIGNED,
    )
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "podpis"
        verbose_name_plural = "podpisy"

    def clean(self) -> None:
        super().clean()
        if bool(self.handover_id) == bool(self.return_protocol_id):
            raise ValidationError(
                "Podpis musi nalezec do protokolu wydania lub zwrotu."
            )


class DamageSnapshot(models.Model):
    """
    Zamrozony stan uszkodzenia w chwili protokolu.

    Nie aktualizowac po zmianie fleet.Damage — tylko odczyt historyczny.
    """

    handover = models.ForeignKey(
        HandoverProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="damage_snapshots",
    )
    return_protocol = models.ForeignKey(
        ReturnProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="damage_snapshots",
    )
    source_damage = models.ForeignKey(
        "fleet.Damage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocol_snapshots",
    )
    description = models.TextField()
    location = models.CharField(max_length=120, blank=True)
    severity = models.CharField(max_length=20, choices=DamageSeverity.choices)
    status_at_capture = models.CharField(max_length=20, choices=DamageStatus.choices)
    damage_type = models.CharField(
        max_length=1,
        choices=DamageType.choices,
        default=DamageType.OTHER,
    )
    pos_x = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    pos_y = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_new_at_protocol = models.BooleanField(
        default=False,
        help_text="True gdy uszkodzenie zgloszone przy tym protokole.",
    )
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["captured_at", "pk"]
        verbose_name = "snapshot uszkodzenia"
        verbose_name_plural = "snapshoty uszkodzen"

    def __str__(self) -> str:
        prefix = "NOWE" if self.is_new_at_protocol else "istniejace"
        return f"{prefix}: {self.description[:40]}"

    def clean(self) -> None:
        super().clean()
        if bool(self.handover_id) == bool(self.return_protocol_id):
            raise ValidationError(
                "Snapshot musi nalezec do protokolu wydania lub zwrotu."
            )


class ProtocolDamageMarker(models.Model):
    """Punkt na diagramie uszkodzen w ramach protokolu (edytowalny w drafcie)."""

    handover = models.ForeignKey(
        HandoverProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="damage_markers",
    )
    return_protocol = models.ForeignKey(
        ReturnProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="damage_markers",
    )
    source_damage = models.ForeignKey(
        "fleet.Damage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="protocol_markers",
    )
    damage_type = models.CharField(
        max_length=1,
        choices=DamageType.choices,
        default=DamageType.OTHER,
    )
    description = models.TextField(blank=True)
    size_note = models.CharField(max_length=80, blank=True)
    pos_x = models.DecimalField(max_digits=5, decimal_places=2)
    pos_y = models.DecimalField(max_digits=5, decimal_places=2)
    is_new = models.BooleanField(default=True)
    resolution = models.CharField(
        max_length=32,
        choices=DamageMarkerResolution.choices,
        default=DamageMarkerResolution.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = "marker uszkodzenia"
        verbose_name_plural = "markery uszkodzen"

    def clean(self) -> None:
        super().clean()
        if bool(self.handover_id) == bool(self.return_protocol_id):
            raise ValidationError(
                "Marker musi nalezec do protokolu wydania lub zwrotu."
            )


class ProtocolEquipmentLine(models.Model):
    handover = models.ForeignKey(
        HandoverProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="equipment_lines",
    )
    return_protocol = models.ForeignKey(
        ReturnProtocol,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="equipment_lines",
    )
    equipment_item = models.ForeignKey(
        "fleet.EquipmentItem",
        on_delete=models.PROTECT,
        related_name="protocol_lines",
    )
    name_snapshot = models.CharField(max_length=120)
    quantity_expected = models.PositiveSmallIntegerField(default=1)
    quantity_actual = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=EquipmentLineStatus.choices,
        default=EquipmentLineStatus.PENDING,
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["pk"]
        verbose_name = "linia wyposazenia protokolu"
        verbose_name_plural = "linie wyposazenia protokolu"

    def clean(self) -> None:
        super().clean()
        if bool(self.handover_id) == bool(self.return_protocol_id):
            raise ValidationError(
                "Linia wyposazenia musi nalezec do protokolu wydania lub zwrotu."
            )


class ProtocolSettlementLine(models.Model):
    """Propozycja oplaty przy zwrocie — zatwierdzenie / odrzucenie przez pracownika."""

    return_protocol = models.ForeignKey(
        ReturnProtocol,
        on_delete=models.CASCADE,
        related_name="settlement_lines",
    )
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=160)
    basis = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    decision = models.CharField(
        max_length=20,
        choices=SettlementLineDecision.choices,
        default=SettlementLineDecision.PENDING,
    )
    staff_note = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        verbose_name = "pozycja rozliczenia"
        verbose_name_plural = "pozycje rozliczenia"
