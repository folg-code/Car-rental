from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    RESERVATION_CONFIRMED = "reservation_confirmed", "Rezerwacja potwierdzona"
    RESERVATION_CANCELLED = "reservation_cancelled", "Rezerwacja anulowana"
    RENTAL_CREATED = "rental_created", "Wynajem utworzony"
    RENTAL_STARTED = "rental_started", "Wynajem rozpoczety"
    RENTAL_RETURNED = "rental_returned", "Wynajem zwrocony"
    RENTAL_CLOSED = "rental_closed", "Wynajem zamkniety"
    RENTAL_CANCELLED = "rental_cancelled", "Wynajem anulowany"
    PAYMENT_RECORDED = "payment_recorded", "Platnosc zarejestrowana"
    HANDOVER_COMPLETED = "handover_completed", "Protokol wydania zakonczony"
    RETURN_COMPLETED = "return_completed", "Protokol zwrotu zakonczony"


class AuditLog(models.Model):
    """Niemutowalny zapis operacji krytycznych — append-only."""

    action = models.CharField(max_length=64, choices=AuditAction.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    reservation = models.ForeignKey(
        "bookings.Reservation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    rental = models.ForeignKey(
        "bookings.Rental",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    object_type = models.CharField(max_length=32, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "wpis audytu"
        verbose_name_plural = "wpisy audytu"
        indexes = [
            models.Index(fields=["rental", "-created_at"]),
            models.Index(fields=["reservation", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} #{self.pk}"

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            raise ValueError("Wpis audytu nie moze byc modyfikowany.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        raise ValueError("Wpis audytu nie moze byc usuniety.")
