from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import PriceLine, ReservationStatus
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.availability import AvailabilityService
from apps.pricing.models import (
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
)
from apps.website.services.public_booking import PublicBookingOrchestrator


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-booking")


@pytest.fixture
def price_list(db) -> PriceList:
    return PriceList.objects.create(
        name="Test cennik booking",
        slug="test-booking",
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def car(db, category: CarCategory, price_list: PriceList) -> Car:
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="BOOK01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _interval() -> tuple[datetime, datetime]:
    return (
        datetime(2026, 6, 10, 10, 0, tzinfo=UTC),
        datetime(2026, 6, 15, 10, 0, tzinfo=UTC),
    )


@pytest.mark.django_db
class TestPublicBookingOrchestrator:
    def test_submit_creates_pending_payment_reservation(self, car: Car) -> None:
        start, end = _interval()
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=start,
            end_at=end,
            first_name="Jan",
            last_name="Kowalski",
            email="jan-book@example.com",
            phone="+48123456789",
        )
        assert result.reservation.status == ReservationStatus.PENDING_PAYMENT
        assert result.customer_created is True
        assert PriceLine.objects.filter(reservation=result.reservation).exists()
        assert PriceSnapshotService.reservation_total(result.reservation) == Decimal(
            "500.00"
        )
        assert AvailabilityService.is_car_available(car, start, end) is False

    def test_submit_reuses_customer_by_email(self, car: Car) -> None:
        start, end = _interval()
        first = PublicBookingOrchestrator.submit(
            car=car,
            start_at=start,
            end_at=end,
            first_name="Jan",
            last_name="Kowalski",
            email="reuse@example.com",
            phone="+48111111111",
        )
        other_car = Car.objects.create(
            category=car.category,
            registration_number="BOOK02",
            make="Skoda",
            model="Fabia",
            year=2021,
            status=CarStatus.ACTIVE,
        )
        other_start = datetime(2026, 7, 10, 10, 0, tzinfo=UTC)
        other_end = datetime(2026, 7, 15, 10, 0, tzinfo=UTC)
        second = PublicBookingOrchestrator.submit(
            car=other_car,
            start_at=other_start,
            end_at=other_end,
            first_name="Jan",
            last_name="Kowalski",
            email="reuse@example.com",
            phone="+48222222222",
        )
        assert first.customer_created is True
        assert second.customer_created is False
        assert second.customer.pk == first.customer.pk

    def test_submit_with_extra_service(self, car: Car, price_list: PriceList) -> None:
        ExtraService.objects.create(
            price_list=price_list,
            code="child_seat",
            name="Fotelik",
            charge_type=ExtraServiceChargeType.PER_RENTAL,
            amount=Decimal("40.00"),
        )
        start, end = _interval()
        result = PublicBookingOrchestrator.submit(
            car=car,
            start_at=start,
            end_at=end,
            first_name="Anna",
            last_name="Nowak",
            email="anna-book@example.com",
            extra_codes=["child_seat"],
        )
        assert PriceSnapshotService.reservation_total(result.reservation) == Decimal(
            "540.00"
        )

    def test_submit_rejects_inactive_car(self, car: Car) -> None:
        car.status = CarStatus.INACTIVE
        car.save()
        start, end = _interval()
        with pytest.raises(ValidationError, match="nie jest dostepne"):
            PublicBookingOrchestrator.submit(
                car=car,
                start_at=start,
                end_at=end,
                first_name="Jan",
                last_name="Kowalski",
                email="inactive@example.com",
            )
