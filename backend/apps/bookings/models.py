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
