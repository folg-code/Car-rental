from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.bookings.demo_seed.catalog import (
    CARS,
    CATEGORIES,
    CUSTOMERS,
    DAILY_RATES,
    SCENARIOS,
    CarSpec,
    CustomerSpec,
    ScenarioSpec,
    demo_note,
)
from apps.bookings.models import (
    Customer,
    Rental,
    Reservation,
    ReservationStatus,
)
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarImage
from apps.pricing.models import (
    AmountType,
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
    PricingRule,
    PricingRuleType,
)

if TYPE_CHECKING:
    from django.core.management.base import OutputWrapper


@dataclass
class SeedSummary:
    categories: int = 0
    cars: int = 0
    customers: int = 0
    reservations: int = 0
    rentals: int = 0


class DemoSeedBuilder:
    _CAR_IMAGE_FILES = {
        "suv": "car-suv.png",
        "kompakt": "car-compact.png",
        "premium": "car-compact.png",
    }

    def __init__(self, stdout: OutputWrapper) -> None:
        self.stdout = stdout
        self.summary = SeedSummary()
        self._categories: dict[str, CarCategory] = {}
        self._cars: dict[str, Car] = {}
        self._customers: dict[str, Customer] = {}

    def run(self) -> SeedSummary:
        self._seed_categories()
        self._seed_cars()
        self._seed_customers()
        self._seed_price_list()
        self._seed_scenarios()
        self._migrate_legacy_seed()
        return self.summary

    def _log(self, message: str) -> None:
        self.stdout.write(message)

    def _seed_categories(self) -> None:
        for spec in CATEGORIES:
            category, created = CarCategory.objects.get_or_create(
                slug=spec.slug,
                defaults={
                    "name": spec.name,
                    "sort_order": spec.sort_order,
                    "deposit": spec.deposit,
                },
            )
            if category.deposit == 0:
                category.deposit = spec.deposit
                category.save(update_fields=["deposit"])
            self._categories[spec.slug] = category
            if created:
                self.summary.categories += 1
                self._log(f"  Utworzono kategorie: {category.name}")

    def _seed_cars(self) -> None:
        for spec in CARS:
            car = self._upsert_car(spec)
            self._attach_demo_car_image(car, spec.category_slug)

    def _upsert_car(self, spec: CarSpec) -> Car:
        category = self._categories[spec.category_slug]
        car, created = Car.objects.update_or_create(
            registration_number=spec.registration_number,
            defaults={
                "category": category,
                "make": spec.make,
                "model": spec.model,
                "year": spec.year,
                "color": spec.color,
                "status": spec.status,
                "fuel_type": spec.fuel_type,
                "mileage": spec.mileage,
                "seats": spec.seats,
            },
        )
        if created:
            self.summary.cars += 1
            self._log(f"  Utworzono auto: {car.registration_number}")
        self._cars[spec.registration_number] = car
        return car

    def _attach_demo_car_image(self, car: Car, category_slug: str) -> None:
        if car.images.exists():
            return
        filename = self._CAR_IMAGE_FILES.get(category_slug, "car-compact.png")
        path = Path(settings.BASE_DIR) / "static" / "images" / "cars" / filename
        if not path.is_file():
            return
        CarImage.objects.create(
            car=car,
            image=ContentFile(path.read_bytes(), name=filename),
            is_primary=True,
            caption=f"{car.make} {car.model}",
        )

    def _seed_customers(self) -> None:
        for spec in CUSTOMERS:
            self._upsert_customer(spec)

    def _upsert_customer(self, spec: CustomerSpec) -> Customer:
        customer, created = Customer.objects.get_or_create(
            email=spec.email,
            defaults={
                "first_name": spec.first_name,
                "last_name": spec.last_name,
                "phone": spec.phone,
                "company_name": spec.company_name,
                "city": spec.city,
            },
        )
        if not created:
            updates: list[str] = []
            for field in ("first_name", "last_name", "phone", "company_name", "city"):
                value = getattr(spec, field)
                if value and getattr(customer, field) != value:
                    setattr(customer, field, value)
                    updates.append(field)
            if updates:
                customer.save(update_fields=[*updates, "updated_at"])
        else:
            self.summary.customers += 1
            self._log(f"  Utworzono klienta: {customer.full_name}")
        self._customers[spec.email] = customer
        return customer

    def _seed_price_list(self) -> None:
        price_list, _ = PriceList.objects.get_or_create(
            slug="domyslny-2026",
            defaults={
                "name": "Cennik domyslny 2026",
                "is_default": True,
                "is_active": True,
            },
        )
        for slug, amount in DAILY_RATES.items():
            category = self._categories[slug]
            DailyRate.objects.get_or_create(
                price_list=price_list,
                category=category,
                defaults={"amount": amount},
            )
        PricingRule.objects.get_or_create(
            price_list=price_list,
            rule_type=PricingRuleType.WEEKEND_SURCHARGE,
            name="Doplata weekendowa",
            defaults={
                "amount_type": AmountType.PER_DAY,
                "value": Decimal("25.00"),
                "priority": 10,
            },
        )
        PricingRule.objects.get_or_create(
            price_list=price_list,
            rule_type=PricingRuleType.LONG_RENTAL_DISCOUNT,
            name="Rabat 7+ dni",
            defaults={
                "amount_type": AmountType.PERCENT,
                "value": Decimal("10"),
                "min_rental_days": 7,
                "priority": 20,
            },
        )
        for code, name, amount, charge_type in (
            (
                "child_seat",
                "Fotelik dzieciecy",
                Decimal("40.00"),
                ExtraServiceChargeType.PER_RENTAL,
            ),
            (
                "fuel_refill",
                "Uzupelnienie paliwa",
                Decimal("5.00"),
                ExtraServiceChargeType.PER_UNIT,
            ),
            (
                "extra_km",
                "Dodatkowy kilometr",
                Decimal("1.50"),
                ExtraServiceChargeType.PER_UNIT,
            ),
        ):
            ExtraService.objects.get_or_create(
                price_list=price_list,
                code=code,
                defaults={
                    "name": name,
                    "charge_type": charge_type,
                    "amount": amount,
                },
            )
        self._log(f"  Cennik: {price_list.name}")

    def _scenario_datetimes(self, spec: ScenarioSpec) -> tuple[datetime, datetime]:
        base = timezone.localdate()
        start = timezone.make_aware(
            datetime.combine(
                base + timedelta(days=spec.start_offset_days),
                time(hour=10, minute=0),
            )
        )
        end = timezone.make_aware(
            datetime.combine(
                base + timedelta(days=spec.end_offset_days),
                time(hour=10, minute=0),
            )
        )
        return start, end

    @transaction.atomic
    def _seed_scenarios(self) -> None:
        for spec in SCENARIOS:
            self._seed_scenario(spec)

    def _seed_scenario(self, spec: ScenarioSpec) -> None:
        marker = demo_note(spec.key)
        if Reservation.objects.filter(notes=marker).exists():
            return

        car = self._cars[spec.car_registration]
        customer = self._customers[spec.customer_email]
        start_at, end_at = self._scenario_datetimes(spec)

        if spec.rental_state or spec.reservation_status == ReservationStatus.CONFIRMED:
            reservation = ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
                status=ReservationStatus.DRAFT,
                notes=marker,
            )
            PriceSnapshotService.freeze(
                reservation,
                extra_codes=list(spec.extra_codes),
            )
            ReservationService.confirm(reservation)
        elif spec.reservation_status == ReservationStatus.CANCELLED:
            reservation = ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
                status=ReservationStatus.DRAFT,
                notes=marker,
            )
            PriceSnapshotService.freeze(reservation)
            ReservationService.cancel(reservation, reason=spec.cancel_reason)
        else:
            reservation = ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
                status=spec.reservation_status,
                notes=marker,
            )

        rental: Rental | None = None
        if spec.rental_state is not None:
            rental = RentalService.convert_from_reservation(reservation)
            self._apply_rental_state(rental, spec.rental_state, start_at, end_at)

        self.summary.reservations += 1
        if rental is not None:
            self.summary.rentals += 1
        label = spec.key.replace("-", " ")
        self._log(f"  Scenariusz: {label} (#{reservation.pk})")

    @staticmethod
    def _apply_rental_state(
        rental: Rental,
        state: str,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        if state == "scheduled":
            return
        RentalService.start(rental, at=start_at)
        if state == "active":
            return
        RentalService.mark_returned(rental, at=end_at)
        if state == "returned":
            return
        if state == "closed":
            RentalService.close(rental)

    def _migrate_legacy_seed(self) -> None:
        legacy = Reservation.objects.filter(notes="DEMO_SEED").first()
        if legacy is None:
            return
        if legacy.notes == demo_note("ops-scheduled-near"):
            return
        legacy.notes = demo_note("legacy-migrated")
        legacy.save(update_fields=["notes", "updated_at"])
        self._log("  Zmigrowano legacy DEMO_SEED -> DEMO_SEED:legacy-migrated")
