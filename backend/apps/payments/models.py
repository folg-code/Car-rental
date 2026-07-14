from decimal import Decimal

import django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def _check_constraint(name: str, q: models.Q) -> models.CheckConstraint:
    """Django 5.1+ / 6.x use ``condition``; Django 4.x used ``check``."""
    kw = "condition" if django.VERSION >= (5, 1) else "check"
    return models.CheckConstraint(**{kw: q}, name=name)


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Gotowka"
    BANK_TRANSFER = "bank_transfer", "Przelew"
    CARD = "card", "Karta"
    BLIK = "blik", "BLIK"
    ONLINE_GATEWAY = "online_gateway", "Bramka online"


class PaymentType(models.TextChoices):
    RENTAL_FEE = "rental_fee", "Oplata za wynajem"
    DEPOSIT = "deposit", "Kaucja"
    REFUND = "refund", "Zwrot"
    EXTRA_CHARGE = "extra_charge", "Oplata dodatkowa"
    DAMAGE_CHARGE = "damage_charge", "Oplata za szkody"


REVENUE_PAYMENT_TYPES = frozenset(
    {
        PaymentType.RENTAL_FEE,
        PaymentType.EXTRA_CHARGE,
        PaymentType.DAMAGE_CHARGE,
    }
)


class PaymentIntentStatus(models.TextChoices):
    PENDING = "pending", "Oczekuje"
    SUCCEEDED = "succeeded", "Zaksiegowana"
    FAILED = "failed", "Nieudana"
    CANCELLED = "cancelled", "Anulowana"


class PaymentIntent(models.Model):
    """Przygotowanie pod bramke online — MVP: reczna ksiegowanie przez Payment."""

    rental = models.ForeignKey(
        "bookings.Rental",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_intents",
    )
    reservation = models.ForeignKey(
        "bookings.Reservation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_intents",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_type = models.CharField(
        max_length=32,
        choices=PaymentType.choices,
        default=PaymentType.RENTAL_FEE,
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentIntentStatus.choices,
        default=PaymentIntentStatus.PENDING,
        db_index=True,
    )
    external_reference = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "intencja platnosci"
        verbose_name_plural = "intencje platnosci"
        constraints = [
            _check_constraint(
                "paymentintent_requires_rental_or_reservation",
                models.Q(rental__isnull=False) | models.Q(reservation__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        if self.rental_id is not None:
            target = f"wynajem #{self.rental_id}"
        else:
            target = f"rezerwacja #{self.reservation_id}"
        return (
            f"Intent #{self.pk or '—'} ({target}) — "
            f"{self.amount} PLN ({self.get_status_display()})"
        )

    def clean(self) -> None:
        super().clean()
        if self.rental_id is None and self.reservation_id is None:
            raise ValidationError(
                "Intencja musi byc powiazana z wynajmem lub rezerwacja."
            )
        if (
            self.rental_id is not None
            and self.reservation_id is not None
            and self.rental.reservation_id != self.reservation_id
        ):
            raise ValidationError(
                "Rezerwacja intencji nie zgadza sie z rezerwacja wynajmu."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Ruch pieniezny — zrodlo prawdy o tym, ile i kiedy wplynelo."""

    rental = models.ForeignKey(
        "bookings.Rental",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    reservation = models.ForeignKey(
        "bookings.Reservation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    intent = models.ForeignKey(
        PaymentIntent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    payment_type = models.CharField(max_length=32, choices=PaymentType.choices)
    method = models.CharField(max_length=32, choices=PaymentMethod.choices)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    paid_at = models.DateTimeField()
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_recorded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at", "-pk"]
        verbose_name = "platnosc"
        verbose_name_plural = "platnosci"
        indexes = [
            models.Index(fields=["rental", "payment_type"]),
            models.Index(fields=["paid_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Platnosc #{self.pk or '—'} — "
            f"{self.get_payment_type_display()} {self.amount} PLN"
        )

    @property
    def is_revenue(self) -> bool:
        return self.payment_type in REVENUE_PAYMENT_TYPES

    def clean(self) -> None:
        super().clean()
        if self.payment_type == PaymentType.REFUND and self.amount <= 0:
            raise ValidationError({"amount": "Kwota zwrotu musi byc dodatnia."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class PaymentProviderEvent(models.Model):
    """Log zdarzen z bramki (webhook) — przygotowanie pod integracje online."""

    intent = models.ForeignKey(
        PaymentIntent,
        on_delete=models.CASCADE,
        related_name="provider_events",
    )
    event_type = models.CharField(max_length=64)
    payload = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "zdarzenie bramki"
        verbose_name_plural = "zdarzenia bramki"

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.received_at:%Y-%m-%d %H:%M}"
