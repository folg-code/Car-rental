import pytest
from django.core.management import call_command

from apps.bookings.demo_seed.catalog import CARS, CUSTOMERS, SCENARIOS, demo_note
from apps.bookings.models import Customer, Rental, Reservation
from apps.fleet.models import Car, CarCategory


@pytest.mark.django_db
class TestSeedDemoCommand:
    def test_seed_demo_is_idempotent(self) -> None:
        call_command("seed_demo")
        cars_after_first = Car.objects.count()
        customers_after_first = Customer.objects.count()
        reservations_after_first = Reservation.objects.filter(
            notes__startswith="DEMO_SEED:"
        ).count()
        rentals_after_first = Rental.objects.count()
        categories_after_first = CarCategory.objects.count()

        call_command("seed_demo")

        assert Car.objects.count() == cars_after_first
        assert Customer.objects.count() == customers_after_first
        assert (
            Reservation.objects.filter(notes__startswith="DEMO_SEED:").count()
            == reservations_after_first
        )
        assert Rental.objects.count() == rentals_after_first
        assert CarCategory.objects.count() == categories_after_first

    def test_seed_demo_populates_catalog(self) -> None:
        call_command("seed_demo")

        assert CarCategory.objects.filter(slug="premium").exists()
        assert Car.objects.count() >= len(CARS)
        assert Customer.objects.count() >= len(CUSTOMERS)
        assert Reservation.objects.filter(
            notes__startswith="DEMO_SEED:"
        ).count() >= len(SCENARIOS)
        assert Rental.objects.filter(status="active").exists()
        assert Rental.objects.filter(status="scheduled").exists()
        assert Rental.objects.filter(status="closed").exists()
        assert Reservation.objects.filter(notes=demo_note("res-draft")).exists()
        assert Reservation.objects.filter(
            notes=demo_note("res-pending-payment")
        ).exists()
