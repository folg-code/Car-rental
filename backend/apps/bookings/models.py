from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
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
    }
)

TERMINAL_RESERVATION_STATUSES = frozenset(
    {
        ReservationStatus.CANCELLED,
        ReservationStatus.EXPIRED,
        ReservationStatus.CONVERTED_TO_RENTAL,
    }
)


class ReservationPricingMode(models.TextChoices):
    AUTO = "auto", "Automatyczny (cennik na date)"
    PRICE_LIST = "price_list", "Wybrany cennik"
    CUSTOM = "custom", "Kwota reczna"


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
    pricing_mode = models.CharField(
        max_length=16,
        choices=ReservationPricingMode.choices,
        default=ReservationPricingMode.AUTO,
    )
    price_list = models.ForeignKey(
        "pricing.PriceList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )
    custom_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Uzywane gdy pricing_mode=custom.",
    )
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
        if self.pricing_mode == ReservationPricingMode.PRICE_LIST:
            if self.price_list_id is None:
                raise ValidationError(
                    {"price_list": "Wybierz cennik lub zmien sposob naliczania ceny."}
                )
        elif self.pricing_mode == ReservationPricingMode.CUSTOM:
            if self.custom_total is None:
                raise ValidationError(
                    {"custom_total": "Podaj kwote reczna dla tej rezerwacji."}
                )
        else:
            self.price_list_id = None
            self.custom_total = None

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class RentalStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Zaplanowany"
    ACTIVE = "active", "Aktywny"
    RETURNED = "returned", "Zwrocony"
    CLOSED = "closed", "Zamkniety"
    CANCELLED = "cancelled", "Anulowany"


BLOCKING_RENTAL_STATUSES = frozenset(
    {
        RentalStatus.SCHEDULED,
        RentalStatus.ACTIVE,
        RentalStatus.RETURNED,
    }
)

TERMINAL_RENTAL_STATUSES = frozenset(
    {
        RentalStatus.CLOSED,
        RentalStatus.CANCELLED,
    }
)


class Rental(models.Model):
    """
    Operacyjny wynajem — powstaje z potwierdzonej rezerwacji (max jeden na rezerwacje).

    Terminy planowane kopiowane z rezerwacji; faktyczne daty wydania/zwrotu uzupelniane
    przy zmianie statusu (protokoly w operations — Sprint 6).
    """

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.PROTECT,
        related_name="rental",
    )
    status = models.CharField(
        max_length=16,
        choices=RentalStatus.choices,
        default=RentalStatus.SCHEDULED,
        db_index=True,
    )
    scheduled_start_at = models.DateTimeField()
    scheduled_end_at = models.DateTimeField()
    actual_start_at = models.DateTimeField(null=True, blank=True)
    actual_end_at = models.DateTimeField(null=True, blank=True)
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Snapshot kaucji z kategorii auta w momencie konwersji.",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rentals_created",
    )
    cancellation_reason = models.CharField(max_length=255, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_start_at"]
        verbose_name = "wynajem"
        verbose_name_plural = "wynajmy"
        indexes = [
            models.Index(fields=["status", "scheduled_start_at"]),
            models.Index(fields=["status", "scheduled_end_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Wynajem #{self.pk or '—'} — "
            f"rezerwacja #{self.reservation_id or '—'} "
            f"({self.get_status_display()})"
        )

    @property
    def customer(self) -> Customer:
        return self.reservation.customer

    @property
    def car(self):
        return self.reservation.car

    @property
    def blocks_availability(self) -> bool:
        return self.status in BLOCKING_RENTAL_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_RENTAL_STATUSES

    def clean(self) -> None:
        super().clean()
        if (
            self.scheduled_start_at
            and self.scheduled_end_at
            and self.scheduled_start_at >= self.scheduled_end_at
        ):
            raise ValidationError(
                "Planowana data zakonczenia musi byc pozniejsza niz rozpoczecia."
            )
        if self.actual_start_at and self.actual_end_at:
            if self.actual_start_at >= self.actual_end_at:
                raise ValidationError(
                    "Faktyczna data zwrotu musi byc pozniejsza niz wydania."
                )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class PriceLineType(models.TextChoices):
    """Typ pozycji snapshotu — zgodny z wynikiem kalkulacji pricing."""

    DAILY_RENTAL = "daily_rental", "Wynajem dzienny"
    WEEKEND_SURCHARGE = "weekend_surcharge", "Doplata weekendowa"
    HOLIDAY_SURCHARGE = "holiday_surcharge", "Doplata swiateczna"
    SEASON_SURCHARGE = "season_surcharge", "Doplata sezonowa"
    DISCOUNT = "discount", "Rabat"
    EXTRA_SERVICE = "extra_service", "Usluga dodatkowa"
    MANUAL = "manual", "Pozycja reczna"


class PriceLine(models.Model):
    """
    Snapshot ceny na rezerwacji — niemutowalny po zatwierdzeniu.

    Powstaje z wyniku PricingService; pricing nie trzyma FK do Reservation.
    """

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="price_lines",
    )
    line_type = models.CharField(max_length=32, choices=PriceLineType.choices)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Liczba dni lub jednostek.",
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    source_code = models.CharField(
        max_length=64,
        blank=True,
        help_text="Kod zrodla (np. extra child_seat, regula weekend).",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["reservation", "sort_order", "pk"]
        verbose_name = "pozycja ceny"
        verbose_name_plural = "pozycje ceny"

    def __str__(self) -> str:
        return f"{self.description}: {self.total_amount}"

    def clean(self) -> None:
        super().clean()
        expected = (self.quantity * self.unit_price).quantize(Decimal("0.01"))
        actual = self.total_amount.quantize(Decimal("0.01"))
        if expected != actual:
            raise ValidationError(
                "Suma pozycji musi rownac quantity * unit_price (snapshot)."
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
