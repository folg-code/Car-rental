from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.fleet.models import DamageSeverity, DamageStatus


class HandoverProtocol(models.Model):
    """Protokol wydania pojazdu — jeden na wynajem, niemutowalny po zakonczeniu."""

    rental = models.OneToOneField(
        "bookings.Rental",
        on_delete=models.PROTECT,
        related_name="handover_protocol",
    )
    mileage = models.PositiveIntegerField(help_text="Przebieg przy wydaniu (km).")
    fuel_level_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Poziom paliwa 0–100%.",
    )
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
        return self.completed_at is not None

    def clean(self) -> None:
        super().clean()
        if self.completed_at and not self.mileage:
            raise ValidationError("Uzupelnij przebieg przed zakonczeniem protokolu.")


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
    mileage = models.PositiveIntegerField(help_text="Przebieg przy zwrocie (km).")
    fuel_level_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    surcharge_notes = models.TextField(
        blank=True,
        help_text="Uwagi do doplat (np. paliwo, przekroczony limit km) — MVP tekst.",
    )
    notes = models.TextField(blank=True)
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
        return self.completed_at is not None

    @property
    def mileage_driven(self) -> int | None:
        if self.handover_id and self.mileage:
            return max(0, self.mileage - self.handover.mileage)
        return None


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
    image = models.ImageField(upload_to="operations/signatures/%Y/%m/")
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
