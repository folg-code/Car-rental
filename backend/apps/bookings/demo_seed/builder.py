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

from apps.accounts.models import User, UserRole
from apps.accounts.services.user import UserService
from apps.bookings.demo_seed.accounts_seed import link_portal_customer, seed_staff_user
from apps.bookings.demo_seed.catalog import (
    CARS,
    CATEGORIES,
    CUSTOMERS,
    DAILY_RATES,
    DEMO_PANEL_EMAIL,
    DEMO_PANEL_PASSWORD,
    DEMO_PANEL_USERNAME,
    PROMO_DAILY_RATES,
    SCENARIOS,
    CarSpec,
    CustomerSpec,
    ScenarioSpec,
    demo_note,
)
from apps.bookings.demo_seed.fleet_extras import seed_fleet_extras
from apps.bookings.demo_seed.payments_seed import (
    apply_payment_profile,
    seed_demo_invoice,
)
from apps.bookings.demo_seed.protocols import (
    seed_completed_handover,
    seed_completed_return,
)
from apps.bookings.models import (
    Customer,
    Rental,
    RentalStatus,
    Reservation,
    ReservationPricingMode,
    ReservationStatus,
)
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarImage
from apps.notifications.models import SmsLog, SmsStatus
from apps.operations.services.surcharge_preview import SurchargePreviewService
from apps.payments.services.rental_charge import AccruedChargeLine, RentalChargeService
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
    panel_users: int = 0
    payments: int = 0
    invoices: int = 0
    fleet_docs: int = 0
    fleet_blocks: int = 0
    fleet_damages: int = 0
    sms_logs: int = 0


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
        self._price_lists: dict[str, PriceList] = {}
        self._panel_user: User | None = None

    def run(self) -> SeedSummary:
        self._seed_panel_user()
        seed_staff_user()
        self._seed_categories()
        self._seed_cars()
        self._seed_customers()
        self._seed_price_lists()
        self._seed_scenarios()
        self._seed_fleet_auxiliary()
        self._migrate_legacy_seed()
        return self.summary

    def _log(self, message: str) -> None:
        self.stdout.write(message)

    def _seed_panel_user(self) -> None:
        """Konto superuser do logowania w panelu (dev / demo)."""
        user = User.objects.filter(username=DEMO_PANEL_USERNAME).first()
        if user is None:
            user = UserService.create_user(
                username=DEMO_PANEL_USERNAME,
                password=DEMO_PANEL_PASSWORD,
                role=UserRole.OWNER,
                email=DEMO_PANEL_EMAIL,
                first_name="Demo",
                last_name="Administrator",
                is_staff=True,
                is_superuser=True,
            )
            self.summary.panel_users = 1
            self._log(f"  Uzytkownik panelu: {DEMO_PANEL_USERNAME}")
        else:
            user.email = DEMO_PANEL_EMAIL
            user.first_name = "Demo"
            user.last_name = "Administrator"
            user.role = UserRole.OWNER
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(DEMO_PANEL_PASSWORD)
            user.save()
            self._log(f"  Uzytkownik panelu: {DEMO_PANEL_USERNAME} (zaktualizowany)")
        self._panel_user = user

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

    def _seed_price_lists(self) -> None:
        default_list, _ = PriceList.objects.get_or_create(
            slug="domyslny-2026",
            defaults={
                "name": "Cennik domyslny 2026",
                "is_default": True,
                "is_active": True,
            },
        )
        self._upsert_price_list_rates(default_list, DAILY_RATES)
        self._seed_pricing_rules(default_list)
        self._seed_extra_services(default_list)
        self._price_lists["domyslny-2026"] = default_list
        self._log(f"  Cennik: {default_list.name}")

        promo_list, created = PriceList.objects.get_or_create(
            slug="promo-2026",
            defaults={
                "name": "Promocja wiosenna 2026",
                "is_default": False,
                "is_active": True,
            },
        )
        self._upsert_price_list_rates(promo_list, PROMO_DAILY_RATES)
        if created:
            self._seed_extra_services(promo_list)
        self._price_lists["promo-2026"] = promo_list
        self._log(f"  Cennik: {promo_list.name}")

    def _upsert_price_list_rates(
        self,
        price_list: PriceList,
        rates: dict[str, Decimal],
    ) -> None:
        for slug, amount in rates.items():
            category = self._categories[slug]
            DailyRate.objects.get_or_create(
                price_list=price_list,
                category=category,
                defaults={"amount": amount},
            )

    def _seed_pricing_rules(self, price_list: PriceList) -> None:
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

    def _seed_extra_services(self, price_list: PriceList) -> None:
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

    def _scenario_datetimes(self, spec: ScenarioSpec) -> tuple[datetime, datetime]:
        if spec.date_mode == "weekend_past":
            return self._weekend_past_datetimes()
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

    @staticmethod
    def _weekend_past_datetimes() -> tuple[datetime, datetime]:
        today = timezone.localdate()
        target = today - timedelta(days=32)
        while target.weekday() != 5:
            target -= timedelta(days=1)
        start = timezone.make_aware(datetime.combine(target, time(hour=10, minute=0)))
        end = timezone.make_aware(
            datetime.combine(target + timedelta(days=3), time(hour=10, minute=0))
        )
        return start, end

    @transaction.atomic
    def _seed_scenarios(self) -> None:
        for spec in SCENARIOS:
            self._seed_scenario(spec)

    def _pricing_kwargs(self, spec: ScenarioSpec) -> dict:
        kwargs: dict = {}
        if spec.pricing_mode == "price_list":
            kwargs["pricing_mode"] = ReservationPricingMode.PRICE_LIST
            price_list = self._price_lists.get(spec.price_list_slug)
            if price_list is not None:
                kwargs["price_list_id"] = price_list.pk
        elif spec.pricing_mode == "custom":
            kwargs["pricing_mode"] = ReservationPricingMode.CUSTOM
            if spec.custom_total is not None:
                kwargs["custom_total"] = spec.custom_total
        return kwargs

    def _seed_scenario(self, spec: ScenarioSpec) -> None:
        marker = demo_note(spec.key)
        if Reservation.objects.filter(notes__startswith=marker).exists():
            return

        car = self._cars[spec.car_registration]
        customer = self._customers[spec.customer_email]
        start_at, end_at = self._scenario_datetimes(spec)
        pricing_kwargs = self._pricing_kwargs(spec)
        panel_id = self._panel_user.pk if self._panel_user else None

        needs_confirm = (
            spec.rental_state is not None
            or spec.reservation_status == ReservationStatus.CONFIRMED
            or spec.payment_profile == "online_succeeded"
        )

        if needs_confirm and spec.reservation_status != ReservationStatus.CANCELLED:
            reservation = ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
                status=ReservationStatus.DRAFT,
                notes=marker,
                **pricing_kwargs,
            )
            PriceSnapshotService.freeze(
                reservation,
                extra_codes=list(spec.extra_codes),
            )
            if spec.reservation_status == ReservationStatus.PENDING_PAYMENT:
                reservation.status = ReservationStatus.PENDING_PAYMENT
                reservation.save(update_fields=["status", "updated_at"])
            else:
                ReservationService.confirm(reservation)
        elif spec.reservation_status == ReservationStatus.CANCELLED:
            reservation = ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start_at,
                end_at=end_at,
                status=ReservationStatus.DRAFT,
                notes=marker,
                **pricing_kwargs,
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
                **pricing_kwargs,
            )
            if spec.pricing_mode in ("price_list", "custom") or spec.extra_codes:
                PriceSnapshotService.freeze(
                    reservation,
                    extra_codes=list(spec.extra_codes),
                )

        if spec.expire_after_create:
            ReservationService.expire(reservation)

        rental: Rental | None = None
        if spec.rental_state is not None:
            rental = RentalService.convert_from_reservation(reservation)
            self._apply_rental_state(rental, spec, start_at, end_at)
            if spec.rental_cancelled:
                RentalService.cancel(rental, reason=spec.cancel_reason)

        if spec.link_customer_user:
            link_portal_customer(customer)

        payments_created = apply_payment_profile(
            scenario_key=spec.key,
            reservation=reservation,
            rental=rental,
            profile=spec.payment_profile,
            panel_user_id=panel_id,
        )
        self.summary.payments += payments_created

        if rental is not None and spec.create_invoice:
            if seed_demo_invoice(rental=rental, scenario_key=spec.key):
                self.summary.invoices += 1

        if spec.seed_sms:
            self.summary.sms_logs += self._seed_demo_sms(reservation)

        self.summary.reservations += 1
        if rental is not None:
            self.summary.rentals += 1
        label = spec.key.replace("-", " ")
        self._log(f"  Scenariusz: {label} (#{reservation.pk})")

    def _apply_rental_state(
        self,
        rental: Rental,
        spec: ScenarioSpec,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        state = spec.rental_state
        if state is None:
            return
        if state == "scheduled":
            return

        handover = seed_completed_handover(rental, at=start_at)
        if rental.status == RentalStatus.SCHEDULED:
            RentalService.start(rental, at=start_at)

        if state == "active":
            return

        if spec.ops_profile == "surcharges":
            return_protocol = seed_completed_return(
                rental,
                handover,
                at=end_at,
                driven_km=400,
                fuel_level_percent=60,
            )
            preview = SurchargePreviewService.preview(
                handover_mileage=handover.mileage,
                handover_fuel=handover.fuel_level_percent,
                return_mileage=return_protocol.mileage,
                return_fuel=return_protocol.fuel_level_percent,
            )
            lines = tuple(
                AccruedChargeLine(
                    source_code=line.code,
                    description=line.description,
                    amount=line.total,
                )
                for line in preview.lines
            )
            RentalChargeService.accrue_return_surcharges(
                rental_id=rental.pk,
                return_protocol_id=return_protocol.pk,
                lines=lines,
            )
        else:
            seed_completed_return(rental, handover, at=end_at)

        RentalService.mark_returned(rental, at=end_at)
        if state == "returned":
            return
        if state == "closed":
            RentalService.close(rental)

    def _seed_demo_sms(self, reservation: Reservation) -> int:
        marker = demo_note(f"sms:{reservation.pk}")
        if SmsLog.objects.filter(body__contains=marker).exists():
            return 0
        SmsLog.objects.create(
            reservation=reservation,
            recipient_phone=reservation.customer.phone or "+48000000000",
            body=f"{marker} Potwierdz rezerwacje w panelu.",
            status=SmsStatus.SENT,
            sent_at=timezone.now(),
            sent_by_id=self._panel_user.pk if self._panel_user else None,
        )
        return 1

    def _seed_fleet_auxiliary(self) -> None:
        panel_id = self._panel_user.pk if self._panel_user else None
        docs, blocks, damages = seed_fleet_extras(
            cars=self._cars,
            panel_user_id=panel_id,
        )
        self.summary.fleet_docs = docs
        self.summary.fleet_blocks = blocks
        self.summary.fleet_damages = damages

    def _migrate_legacy_seed(self) -> None:
        legacy = Reservation.objects.filter(notes="DEMO_SEED").first()
        if legacy is None:
            return
        if legacy.notes == demo_note("ops-scheduled-near"):
            return
        legacy.notes = demo_note("legacy-migrated")
        legacy.save(update_fields=["notes", "updated_at"])
        self._log("  Zmigrowano legacy DEMO_SEED -> DEMO_SEED:legacy-migrated")
