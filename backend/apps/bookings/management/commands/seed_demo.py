from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import Customer, Reservation, ReservationStatus
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.fleet.models import Car, CarCategory, CarStatus, FuelType
from apps.pricing.models import (
    AmountType,
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
    PricingRule,
    PricingRuleType,
)


class Command(BaseCommand):
    help = "Tworzy dane demo: kategorie, auta, klientow (idempotentne)."

    def handle(self, *args, **options) -> None:
        kompakt, _ = CarCategory.objects.get_or_create(
            slug="kompakt",
            defaults={
                "name": "Kompakt",
                "sort_order": 1,
                "deposit": Decimal("1500.00"),
            },
        )
        suv, _ = CarCategory.objects.get_or_create(
            slug="suv",
            defaults={"name": "SUV", "sort_order": 2, "deposit": Decimal("3000.00")},
        )
        if kompakt.deposit == 0:
            kompakt.deposit = Decimal("1500.00")
            kompakt.save(update_fields=["deposit"])
        if suv.deposit == 0:
            suv.deposit = Decimal("3000.00")
            suv.save(update_fields=["deposit"])

        cars_data = [
            {
                "registration_number": "KR1DEMO1",
                "category": kompakt,
                "make": "Toyota",
                "model": "Yaris",
                "year": 2022,
                "color": "bialy",
            },
            {
                "registration_number": "KR1DEMO2",
                "category": kompakt,
                "make": "Volkswagen",
                "model": "Polo",
                "year": 2021,
                "color": "szary",
            },
            {
                "registration_number": "KR1DEMO3",
                "category": suv,
                "make": "Skoda",
                "model": "Kodiaq",
                "year": 2023,
                "color": "czarny",
            },
        ]
        cars: list[Car] = []
        for data in cars_data:
            car, created = Car.objects.get_or_create(
                registration_number=data["registration_number"],
                defaults={
                    "category": data["category"],
                    "make": data["make"],
                    "model": data["model"],
                    "year": data["year"],
                    "color": data["color"],
                    "status": CarStatus.ACTIVE,
                    "fuel_type": FuelType.PETROL,
                    "mileage": 45000,
                    "seats": 5,
                },
            )
            cars.append(car)
            action = "Utworzono" if created else "Istnieje"
            self.stdout.write(f"  {action} auto: {car.registration_number}")

        customers_data = [
            {
                "email": "jan.kowalski@demo.pl",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "phone": "+48111111111",
            },
            {
                "email": "anna.nowak@demo.pl",
                "first_name": "Anna",
                "last_name": "Nowak",
                "phone": "+48222222222",
                "company_name": "Nowak Transport",
            },
        ]
        customers: list[Customer] = []
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "phone": data["phone"],
                    "company_name": data.get("company_name", ""),
                },
            )
            customers.append(customer)
            action = "Utworzono" if created else "Istnieje"
            self.stdout.write(f"  {action} klient: {customer.full_name}")

        price_list, _ = PriceList.objects.get_or_create(
            slug="domyslny-2026",
            defaults={
                "name": "Cennik domyslny 2026",
                "is_default": True,
                "is_active": True,
            },
        )
        for category, amount in ((kompakt, "120.00"), (suv, "180.00")):
            DailyRate.objects.get_or_create(
                price_list=price_list,
                category=category,
                defaults={"amount": Decimal(amount)},
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
        ExtraService.objects.get_or_create(
            price_list=price_list,
            code="child_seat",
            defaults={
                "name": "Fotelik dzieciecy",
                "charge_type": ExtraServiceChargeType.PER_RENTAL,
                "amount": Decimal("40.00"),
            },
        )
        self.stdout.write(f"  Cennik: {price_list.name}")

        now = timezone.now()
        if not Reservation.objects.filter(notes="DEMO_SEED").exists():
            reservation = Reservation.objects.create(
                customer=customers[0],
                car=cars[0],
                start_at=now + timedelta(days=3),
                end_at=now + timedelta(days=7),
                status=ReservationStatus.CONFIRMED,
                notes="DEMO_SEED",
            )
            PriceSnapshotService.freeze(reservation, extra_codes=["child_seat"])
            self.stdout.write("  Utworzono przykladowa rezerwacje (confirmed + cena)")
            rental = RentalService.convert_from_reservation(reservation)
            self.stdout.write(
                f"  Utworzono przykladowy wynajem #{rental.pk} (zaplanowany)"
            )

        self.stdout.write(self.style.SUCCESS("Seed demo zakonczony."))
