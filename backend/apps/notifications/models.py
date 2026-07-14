from __future__ import annotations

from django.conf import settings
from django.db import models


class SmsStatus(models.TextChoices):
    PENDING = "pending", "oczekuje"
    SENT = "sent", "wyslany"
    FAILED = "failed", "blad"
    SKIPPED = "skipped", "pominieto"


class SmsLog(models.Model):
    """Log wysylek SMS — append-only audyt, retry przez serwis powiadomien."""

    reservation = models.ForeignKey(
        "bookings.Reservation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sms_logs",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sms_logs",
    )
    recipient_phone = models.CharField(max_length=32)
    body = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=SmsStatus.choices,
        default=SmsStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    external_id = models.CharField(max_length=128, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_sent",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "log SMS"
        verbose_name_plural = "logi SMS"

    def __str__(self) -> str:
        return f"{self.recipient_phone} — {self.get_status_display()}"
