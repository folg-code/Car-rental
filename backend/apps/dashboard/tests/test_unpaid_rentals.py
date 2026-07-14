from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.dashboard.selectors.unpaid_rentals import (
    count_unpaid_rentals,
    list_unpaid_rentals,
)
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.services.payment import PaymentService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-unpaid",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik unpaid",
        slug="test-unpaid",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("200.00"),
    )
    return price_list


@pytest.fixture
def rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@unpaid.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1UNP01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )
    start = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 7, 5, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestUnpaidRentalsSelector:
    def test_counts_rental_with_balance_due(self, rental) -> None:
        assert count_unpaid_rentals() == 1
        assert len(list_unpaid_rentals()) == 1
        assert list_unpaid_rentals()[0].pk == rental.pk

    def test_excludes_fully_paid_rental(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("10000.00"),
        )
        assert count_unpaid_rentals() == 0
        assert list_unpaid_rentals() == []

    def test_partial_payment_still_unpaid(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("200.00"),
        )
        assert count_unpaid_rentals() == 1
