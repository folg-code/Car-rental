from django.conf import settings
from django.db import models


class CarCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "kategoria pojazdu"
        verbose_name_plural = "kategorie pojazdow"

    def __str__(self) -> str:
        return self.name


class CarStatus(models.TextChoices):
    ACTIVE = "active", "Aktywny"
    INACTIVE = "inactive", "Nieaktywny"
    RETIRED = "retired", "Wycofany"


class FuelType(models.TextChoices):
    PETROL = "petrol", "Benzyna"
    DIESEL = "diesel", "Diesel"
    ELECTRIC = "electric", "Elektryczny"
    HYBRID = "hybrid", "Hybryda"
    LPG = "lpg", "LPG"


class Car(models.Model):
    category = models.ForeignKey(
        CarCategory,
        on_delete=models.PROTECT,
        related_name="cars",
    )
    registration_number = models.CharField(max_length=20, unique=True, db_index=True)
    make = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    year = models.PositiveSmallIntegerField()
    vin = models.CharField(max_length=17, blank=True)
    color = models.CharField(max_length=40, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CarStatus.choices,
        default=CarStatus.ACTIVE,
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.PETROL,
    )
    mileage = models.PositiveIntegerField(default=0, help_text="Przebieg w km")
    seats = models.PositiveSmallIntegerField(default=5)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["make", "model", "registration_number"]
        verbose_name = "pojazd"
        verbose_name_plural = "pojazdy"

    def __str__(self) -> str:
        return f"{self.make} {self.model} ({self.registration_number})"

    @property
    def display_name(self) -> str:
        return str(self)


class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="fleet/cars/%Y/%m/")
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-uploaded_at"]
        verbose_name = "zdjecie pojazdu"
        verbose_name_plural = "zdjecia pojazdow"

    def __str__(self) -> str:
        return f"Zdjecie {self.car.registration_number}"


class CarDocumentType(models.TextChoices):
    INSURANCE = "insurance", "Ubezpieczenie OC/AC"
    INSPECTION = "inspection", "Przeglad techniczny"
    REGISTRATION = "registration", "Dowod rejestracyjny"
    OTHER = "other", "Inny"


class CarDocument(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=20, choices=CarDocumentType.choices)
    file = models.FileField(upload_to="fleet/documents/%Y/%m/")
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-valid_until", "-uploaded_at"]
        verbose_name = "dokument pojazdu"
        verbose_name_plural = "dokumenty pojazdow"

    def __str__(self) -> str:
        return f"{self.get_document_type_display()} — {self.car.registration_number}"


class AvailabilityBlockType(models.TextChoices):
    SERVICE = "service", "Serwis"
    MANUAL = "manual", "Reczna blokada"
    OTHER = "other", "Inna"


class AvailabilityBlock(models.Model):
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="availability_blocks",
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    block_type = models.CharField(
        max_length=20,
        choices=AvailabilityBlockType.choices,
        default=AvailabilityBlockType.SERVICE,
    )
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="availability_blocks_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at"]
        verbose_name = "blokada dostepnosci"
        verbose_name_plural = "blokady dostepnosci"

    def __str__(self) -> str:
        return f"{self.car.registration_number}: {self.start_at} — {self.end_at}"


class DamageSeverity(models.TextChoices):
    MINOR = "minor", "Drobne"
    MODERATE = "moderate", "Srednie"
    MAJOR = "major", "Poważne"


class DamageStatus(models.TextChoices):
    ACTIVE = "active", "Aktywne"
    REPAIRED = "repaired", "Naprawione"
    WRITTEN_OFF = "written_off", "Odpisane"


class Damage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="damages")
    description = models.TextField()
    location = models.CharField(
        max_length=120,
        blank=True,
        help_text="Np. zderzak przedni, drzwi lewe przednie",
    )
    severity = models.CharField(
        max_length=20,
        choices=DamageSeverity.choices,
        default=DamageSeverity.MINOR,
    )
    status = models.CharField(
        max_length=20,
        choices=DamageStatus.choices,
        default=DamageStatus.ACTIVE,
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    repaired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reported_at"]
        verbose_name = "uszkodzenie"
        verbose_name_plural = "uszkodzenia"

    def __str__(self) -> str:
        return f"{self.car.registration_number}: {self.description[:50]}"


class DamagePhoto(models.Model):
    damage = models.ForeignKey(Damage, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="fleet/damages/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "zdjecie uszkodzenia"
        verbose_name_plural = "zdjecia uszkodzen"


class RepairRecord(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="repairs")
    description = models.TextField()
    performed_at = models.DateField()
    mileage_at_service = models.PositiveIntegerField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_at"]
        verbose_name = "wpis serwisowy"
        verbose_name_plural = "wpisy serwisowe"

    def __str__(self) -> str:
        return f"{self.car.registration_number} — {self.performed_at}"
