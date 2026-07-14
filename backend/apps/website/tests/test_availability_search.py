from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import AvailabilityBlockType, Car, CarCategory, CarStatus
from apps.fleet.services.maintenance import FleetMaintenanceService
from apps.pricing.models import DailyRate, PriceList
from apps.website.selectors.availability_search import search_available_cars


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-search")


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Test cennik search",
        slug="test-search",
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
        registration_number="SEARCH01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@example.com",
        phone="+48123456789",
    )


def _interval() -> tuple[datetime, datetime]:
    return (
        datetime(2026, 6, 10, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 15, 10, 0, tzinfo=UTC),
    )


@pytest.mark.django_db
class TestAvailabilitySearchSelector:
    def test_returns_available_car(self, car: Car) -> None:
        start, end = _interval()
        result = search_available_cars(start, end)
        assert result.start_at == start
        assert result.end_at == end
        assert len(result.cars) == 1
        assert result.cars[0].pk == car.pk

    def test_excludes_car_with_confirmed_reservation(
        self, customer: Customer, car: Car
    ) -> None:
        start, end = _interval()
        ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        result = search_available_cars(start, end)
        assert result.cars == ()

    def test_excludes_blocked_car(self, car: Car) -> None:
        start, end = _interval()
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 6, 11, 0, 0, tzinfo=UTC),
            end_at=datetime(2026, 6, 13, 0, 0, tzinfo=UTC),
            reason="Serwis",
            block_type=AvailabilityBlockType.SERVICE,
        )
        result = search_available_cars(start, end)
        assert result.cars == ()

    def test_filters_by_category(self, category: CarCategory, car: Car) -> None:
        other = CarCategory.objects.create(name="SUV", slug="suv-search")
        Car.objects.create(
            category=other,
            registration_number="SEARCH02",
            make="Skoda",
            model="Kodiaq",
            year=2023,
            status=CarStatus.ACTIVE,
        )
        start, end = _interval()
        result = search_available_cars(start, end, category_id=category.pk)
        assert len(result.cars) == 1
        assert result.cars[0].pk == car.pk
        assert result.category_id == category.pk

    def test_rejects_invalid_interval(self, car: Car) -> None:
        start = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 10, 10, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            search_available_cars(start, end)
