from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class PriceList(models.Model):
    """Cennik — zestaw stawek i reguł obowiazujacy w danym okresie."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default="PLN")
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Domyslny cennik przy braku dopasowania dat.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name = "cennik"
        verbose_name_plural = "cenniki"

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError(
                "Data konca obowiazywania musi byc nie wczesniejsza niz poczatek."
            )


class DailyRate(models.Model):
    """Stawka dzienna za kategorie pojazdu w ramach cennika."""

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name="daily_rates",
    )
    category = models.ForeignKey(
        "fleet.CarCategory",
        on_delete=models.PROTECT,
        related_name="daily_rates",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Kwota za dobe (PLN).",
    )

    class Meta:
        ordering = ["price_list", "category__sort_order", "category__name"]
        verbose_name = "stawka dzienna"
        verbose_name_plural = "stawki dzienne"
        constraints = [
            models.UniqueConstraint(
                fields=["price_list", "category"],
                name="pricing_unique_daily_rate_per_list_category",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.category} — {self.amount} {self.price_list.currency}/doba"


class PricingRuleType(models.TextChoices):
    WEEKEND_SURCHARGE = "weekend_surcharge", "Doplata weekendowa"
    HOLIDAY_SURCHARGE = "holiday_surcharge", "Doplata swiateczna"
    SEASON_SURCHARGE = "season_surcharge", "Doplata sezonowa"
    LONG_RENTAL_DISCOUNT = "long_rental_discount", "Rabat dlugoterminowy"
    MANUAL_DISCOUNT = "manual_discount", "Rabat reczny (panel)"


class AmountType(models.TextChoices):
    PERCENT = "percent", "Procent od sumy bazowej"
    FIXED = "fixed", "Kwota stala (cala rezerwacja)"
    PER_DAY = "per_day", "Kwota za kazdy dzien"


class PricingRule(models.Model):
    """Regula modyfikujaca cene (doplata lub rabat)."""

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    rule_type = models.CharField(max_length=32, choices=PricingRuleType.choices)
    name = models.CharField(max_length=120)
    amount_type = models.CharField(max_length=16, choices=AmountType.choices)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        help_text="Okres obowiazywania (sezon, swieta).",
    )
    valid_to = models.DateField(null=True, blank=True)
    min_rental_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Min. liczba dni wynajmu (rabat dlugoterminowy).",
    )
    priority = models.PositiveSmallIntegerField(
        default=100,
        help_text="Nizszy numer = wczesniejsza kolejnosc naliczania.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price_list", "priority", "name"]
        verbose_name = "regula cenowa"
        verbose_name_plural = "reguly cenowe"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_rule_type_display()})"

    def clean(self) -> None:
        super().clean()
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError("Nieprawidlowy zakres dat reguly.")

        if self.amount_type == AmountType.PERCENT and self.value > Decimal("100"):
            raise ValidationError("Procent nie moze przekraczac 100.")

        if (
            self.rule_type == PricingRuleType.LONG_RENTAL_DISCOUNT
            and self.min_rental_days is None
        ):
            raise ValidationError(
                "Rabat dlugoterminowy wymaga minimalnej liczby dni wynajmu."
            )


class ExtraServiceChargeType(models.TextChoices):
    PER_RENTAL = "per_rental", "Za caly wynajem"
    PER_DAY = "per_day", "Za dobe"
    PER_UNIT = "per_unit", "Za jednostke (np. km)"


class ExtraService(models.Model):
    """Oplata dodatkowa (fotelik, kierowca, dostawa itd.)."""

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name="extra_services",
    )
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    charge_type = models.CharField(
        max_length=16,
        choices=ExtraServiceChargeType.choices,
        default=ExtraServiceChargeType.PER_RENTAL,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["price_list", "sort_order", "name"]
        verbose_name = "usluga dodatkowa"
        verbose_name_plural = "uslugi dodatkowe"
        constraints = [
            models.UniqueConstraint(
                fields=["price_list", "code"],
                name="pricing_unique_extra_code_per_list",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.amount} {self.price_list.currency})"
