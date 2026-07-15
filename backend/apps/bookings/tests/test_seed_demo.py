import pytest
from django.core.management import call_command

from apps.bookings.demo_seed.catalog import (
    CARS,
    CUSTOMERS,
    DEMO_CUSTOMER_PASSWORD,
    DEMO_CUSTOMER_USERNAME,
    DEMO_PANEL_PASSWORD,
    DEMO_PANEL_USERNAME,
    SCENARIOS,
    demo_note,
)
from apps.bookings.models import Customer, Rental, Reservation, ReservationStatus
from apps.documents.models import Invoice
from apps.fleet.models import (
    AvailabilityBlock,
    Car,
    CarCategory,
    CarDocument,
    Damage,
)
from apps.notifications.models import SmsLog
from apps.payments.models import Payment, PaymentIntent, RentalCharge


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
        payments_after_first = Payment.objects.count()
        intents_after_first = PaymentIntent.objects.count()

        call_command("seed_demo")

        assert Car.objects.count() == cars_after_first
        assert Customer.objects.count() == customers_after_first
        assert (
            Reservation.objects.filter(notes__startswith="DEMO_SEED:").count()
            == reservations_after_first
        )
        assert Rental.objects.count() == rentals_after_first
        assert CarCategory.objects.count() == categories_after_first
        assert Payment.objects.count() == payments_after_first
        assert PaymentIntent.objects.count() == intents_after_first

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
        assert Rental.objects.filter(status="returned").exists()
        assert Reservation.objects.filter(
            notes__startswith=demo_note("res-draft")
        ).exists()
        assert Reservation.objects.filter(
            notes__startswith=demo_note("res-pending-payment")
        ).exists()

    def test_seed_demo_workflow_coverage(self) -> None:
        call_command("seed_demo")

        assert Reservation.objects.filter(
            notes__startswith=demo_note("res-expired"),
            status=ReservationStatus.EXPIRED,
        ).exists()
        assert Reservation.objects.filter(
            notes__startswith=demo_note("res-price-list")
        ).exists()
        assert Reservation.objects.filter(
            notes__startswith=demo_note("res-custom-total")
        ).exists()
        assert Reservation.objects.filter(
            notes__startswith=demo_note("pay-intent-succeeded"),
            status=ReservationStatus.CONFIRMED,
        ).exists()
        assert PaymentIntent.objects.filter(
            reservation__notes__startswith=demo_note("res-pending-payment")
        ).exists()
        assert RentalCharge.objects.filter(
            rental__reservation__notes__startswith=demo_note("ops-return-surcharges")
        ).exists()
        assert Payment.objects.filter(
            rental__reservation__notes__startswith=demo_note("history-closed-1")
        ).exists()
        assert Invoice.objects.filter(
            rental__reservation__notes__startswith=demo_note("history-closed-1")
        ).exists()
        assert CarDocument.objects.filter(notes__startswith="DEMO_SEED:").exists()
        assert AvailabilityBlock.objects.filter(
            reason__startswith="DEMO_SEED:"
        ).exists()
        assert Damage.objects.filter(description__startswith="DEMO_SEED:").exists()
        assert SmsLog.objects.filter(body__contains=demo_note("sms:")).exists()

    def test_seed_demo_creates_panel_superuser(self, client) -> None:
        from apps.accounts.models import User

        call_command("seed_demo")
        assert User.objects.filter(
            username=DEMO_PANEL_USERNAME,
            is_superuser=True,
            is_staff=True,
        ).exists()
        assert client.login(
            username=DEMO_PANEL_USERNAME,
            password=DEMO_PANEL_PASSWORD,
        )

    def test_seed_demo_portal_customer_login(self, client) -> None:
        call_command("seed_demo")
        assert client.login(
            username=DEMO_CUSTOMER_USERNAME,
            password=DEMO_CUSTOMER_PASSWORD,
        )
