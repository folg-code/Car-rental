from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Customer(models.Model):
    """Kontrahent wynajmu — dane biznesowe, oddzielne od konta logowania."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_profile",
    )
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    company_name = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="NIP",
        help_text="Numer identyfikacji podatkowej (opcjonalnie)",
    )
    street = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="PL")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "klient"
        verbose_name_plural = "klienci"
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self) -> str:
        name = self.full_name
        if self.company_name:
            return f"{name} ({self.company_name})"
        return name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self) -> None:
        super().clean()
        if not self.email and not self.phone:
            raise ValidationError("Podaj co najmniej adres e-mail lub numer telefonu.")

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class ReservationStatus(models.TextChoices):
    DRAFT = "draft", "Szkic"
    PENDING_PAYMENT = "pending_payment", "Oczekuje platnosci"
    CONFIRMED = "confirmed", "Potwierdzona"
    CANCELLED = "cancelled", "Anulowana"
    EXPIRED = "expired", "Wygasla"
    CONVERTED_TO_RENTAL = "converted_to_rental", "Przeksztalcona w wynajem"


BLOCKING_RESERVATION_STATUSES = frozenset(
    {
        ReservationStatus.PENDING_PAYMENT,
        ReservationStatus.CONFIRMED,
        ReservationStatus.CONVERTED_TO_RENTAL,
    }
)

TERMINAL_RESERVATION_STATUSES = frozenset(
    {
        ReservationStatus.CANCELLED,
        ReservationStatus.EXPIRED,
        ReservationStatus.CONVERTED_TO_RENTAL,
    }
)


class Reservation(models.Model):
    """Intent rezerwacji — oddzielny od operacyjnego wynajmu (Rental)."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    car = models.ForeignKey(
        "fleet.Car",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=32,
        choices=ReservationStatus.choices,
        default=ReservationStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations_created",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_at"]
        verbose_name = "rezerwacja"
        verbose_name_plural = "rezerwacje"
        indexes = [
            models.Index(fields=["car", "start_at", "end_at"]),
            models.Index(fields=["status", "start_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Rezerwacja #{self.pk or '—'} — "
            f"{self.customer} / {self.car} "
            f"({self.start_at:%Y-%m-%d} – {self.end_at:%Y-%m-%d})"
        )

    @property
    def blocks_availability(self) -> bool:
        return self.status in BLOCKING_RESERVATION_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_RESERVATION_STATUSES

    def clean(self) -> None:
        super().clean()
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError(
                "Data zakonczenia musi byc pozniejsza niz data rozpoczecia."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
