from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, Reservation, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import AvailabilityBlockType, Car, CarCategory, CarStatus
from apps.fleet.services.availability import AvailabilityService
from apps.fleet.services.maintenance import FleetMaintenanceService


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="SUV", slug="suv")


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="KR1RES01",
        make="Skoda",
        model="Kodiaq",
        year=2023,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@example.com",
    )


def _interval(
    start_day: int = 10,
    end_day: int = 15,
) -> tuple[datetime, datetime]:
    return (
        datetime(2026, 6, start_day, 10, 0, tzinfo=UTC),
        datetime(2026, 6, end_day, 10, 0, tzinfo=UTC),
    )


@pytest.mark.django_db
class TestReservationModel:
    def test_invalid_interval_rejected(self, customer: Customer, car: Car) -> None:
        start, end = _interval(15, 10)
        reservation = Reservation(
            customer=customer,
            car=car,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        with pytest.raises(ValidationError):
            reservation.save()

    def test_blocks_availability_property(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        draft = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        confirmed = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 7, 5, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        assert draft.blocks_availability is False
        assert confirmed.blocks_availability is True


@pytest.mark.django_db
class TestReservationService:
    def test_create_draft_without_blocking_car(
        self, customer: Customer, car: Car
    ) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        assert reservation.status == ReservationStatus.DRAFT
        assert AvailabilityService.is_car_available(car, start, end) is True

    def test_create_confirmed_checks_availability(
        self, customer: Customer, car: Car
    ) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        assert reservation.pk is not None
        assert AvailabilityService.is_car_available(car, start, end) is False

    def test_overlapping_confirmed_rejected(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        with pytest.raises(ValidationError, match="rezerwacja"):
            ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=datetime(2026, 6, 12, 10, 0, tzinfo=UTC),
                end_at=datetime(2026, 6, 14, 10, 0, tzinfo=UTC),
                status=ReservationStatus.CONFIRMED,
            )

    def test_unavailable_when_fleet_block_exists(
        self, customer: Customer, car: Car
    ) -> None:
        start, end = _interval()
        FleetMaintenanceService.create_availability_block(
            car_id=car.pk,
            start_at=datetime(2026, 6, 11, 0, 0, tzinfo=UTC),
            end_at=datetime(2026, 6, 13, 0, 0, tzinfo=UTC),
            reason="Serwis",
            block_type=AvailabilityBlockType.SERVICE,
        )
        with pytest.raises(ValidationError, match="niedostepny"):
            ReservationService.create(
                customer_id=customer.pk,
                car_id=car.pk,
                start_at=start,
                end_at=end,
                status=ReservationStatus.CONFIRMED,
            )

    def test_confirm_from_draft(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        confirmed = ReservationService.confirm(reservation)
        assert confirmed.status == ReservationStatus.CONFIRMED
        assert AvailabilityService.is_car_available(car, start, end) is False

    def test_cancel(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        cancelled = ReservationService.cancel(reservation, reason="Klient zrezygnowal")
        assert cancelled.status == ReservationStatus.CANCELLED
        assert cancelled.cancellation_reason == "Klient zrezygnowal"
        assert cancelled.cancelled_at is not None
        assert AvailabilityService.is_car_available(car, start, end) is True

    def test_expire(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.PENDING_PAYMENT,
        )
        expired = ReservationService.expire(reservation)
        assert expired.status == ReservationStatus.EXPIRED

    def test_cannot_cancel_terminal(self, customer: Customer, car: Car) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        ReservationService.cancel(reservation)
        with pytest.raises(ValidationError, match="koncowym"):
            ReservationService.cancel(reservation)
