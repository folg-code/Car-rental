from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.bookings.tasks import expire_stale_pending_reservations_task
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-expire-task")


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Expire task",
        slug="expire-task",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    return price_list


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="EXP001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Jan",
        last_name="Test",
        email="expire-task@example.com",
        phone="+48111111111",
    )


@pytest.mark.django_db
def test_expire_stale_pending_reservations_task(
    car: Car,
    customer: Customer,
) -> None:
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
        end_at=datetime(2026, 11, 5, 10, 0, tzinfo=UTC),
        status=ReservationStatus.PENDING_PAYMENT,
    )
    from apps.bookings.models import Reservation

    Reservation.objects.filter(pk=reservation.pk).update(
        created_at=timezone.now() - timedelta(hours=50),
    )
    assert expire_stale_pending_reservations_task() == 1
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.EXPIRED
