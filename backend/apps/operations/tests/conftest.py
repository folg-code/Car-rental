from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV", slug="suv-ops-views", deposit=Decimal("500")
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    pl = PriceList.objects.create(
        name="Ops views",
        slug="ops-views",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(price_list=pl, category=category, amount=Decimal("100"))
    return pl


@pytest.fixture
def scheduled_rental(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@ops-views.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1OPS02",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
        mileage=10_000,
    )
    start = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 10, 0, tzinfo=UTC)
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    return RentalService.convert_from_reservation(reservation)
