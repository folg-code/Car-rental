from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import Customer, Reservation, ReservationStatus
from apps.fleet.models import Car, CarCategory, CarStatus, FuelType


class Command(BaseCommand):
    help = "Tworzy dane demo: kategorie, auta, klientow (idempotentne)."

    def handle(self, *args, **options) -> None:
        kompakt, _ = CarCategory.objects.get_or_create(
            slug="kompakt",
            defaults={"name": "Kompakt", "sort_order": 1},
        )
        suv, _ = CarCategory.objects.get_or_create(
            slug="suv",
            defaults={"name": "SUV", "sort_order": 2},
        )

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

        now = timezone.now()
        if not Reservation.objects.filter(notes="DEMO_SEED").exists():
            Reservation.objects.create(
                customer=customers[0],
                car=cars[0],
                start_at=now + timedelta(days=3),
                end_at=now + timedelta(days=7),
                status=ReservationStatus.CONFIRMED,
                notes="DEMO_SEED",
            )
            self.stdout.write("  Utworzono przykladowa rezerwacje (confirmed)")

        self.stdout.write(self.style.SUCCESS("Seed demo zakonczony."))
