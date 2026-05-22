from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import (
    Rental,
    RentalStatus,
    Reservation,
    ReservationStatus,
)
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.services.availability import AvailabilityService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="SUV",
        slug="suv-rental",
        deposit=Decimal("2000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik wynajmu test",
        slug="test-wynajem",
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
        registration_number="KR1RNT01",
        make="Skoda",
        model="Kodiaq",
        year=2023,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def customer(db):
    from apps.bookings.models import Customer

    return Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@rental.test",
    )


def _interval(
    start_day: int = 10,
    end_day: int = 15,
) -> tuple[datetime, datetime]:
    return (
        datetime(2026, 6, start_day, 10, 0, tzinfo=UTC),
        datetime(2026, 6, end_day, 10, 0, tzinfo=UTC),
    )


def _confirmed_reservation(customer, car: Car) -> Reservation:
    start, end = _interval()
    reservation = ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.CONFIRMED,
    )
    if not reservation.price_lines.exists():
        PriceSnapshotService.freeze(reservation)
    return reservation


@pytest.mark.django_db
class TestRentalModel:
    def test_convert_requires_price_lines(self, customer, car: Car) -> None:
        start, end = _interval()
        reservation = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        with pytest.raises(ValidationError, match="snapshotu"):
            RentalService.convert_from_reservation(reservation)

    def test_convert_only_from_confirmed(self, customer, car: Car) -> None:
        start, end = _interval()
        reservation = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        PriceSnapshotService.freeze(reservation)
        with pytest.raises(ValidationError, match="potwierdzonej"):
            RentalService.convert_from_reservation(reservation)


@pytest.mark.django_db
class TestRentalService:
    def test_convert_from_reservation(
        self, customer, car: Car, category: CarCategory
    ) -> None:
        reservation = _confirmed_reservation(customer, car)
        rental = RentalService.convert_from_reservation(reservation)

        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.CONVERTED_TO_RENTAL
        assert rental.status == RentalStatus.SCHEDULED
        assert rental.deposit_amount == category.deposit
        assert rental.scheduled_start_at == reservation.start_at
        assert rental.reservation_id == reservation.pk

    def test_reservation_service_convert_wrapper(self, customer, car: Car) -> None:
        reservation = _confirmed_reservation(customer, car)
        rental = ReservationService.convert_to_rental(reservation)
        assert isinstance(rental, Rental)

    def test_lifecycle_scheduled_active_returned_closed(
        self, customer, car: Car
    ) -> None:
        reservation = _confirmed_reservation(customer, car)
        rental = RentalService.convert_from_reservation(reservation)

        RentalService.start(rental)
        rental.refresh_from_db()
        assert rental.status == RentalStatus.ACTIVE
        assert rental.actual_start_at is not None

        RentalService.mark_returned(rental)
        rental.refresh_from_db()
        assert rental.status == RentalStatus.RETURNED
        assert rental.actual_end_at is not None

        RentalService.close(rental)
        rental.refresh_from_db()
        assert rental.status == RentalStatus.CLOSED
        assert rental.closed_at is not None

    def test_cancel_scheduled_only(self, customer, car: Car) -> None:
        reservation = _confirmed_reservation(customer, car)
        rental = RentalService.convert_from_reservation(reservation)
        RentalService.cancel(rental, reason="Zmiana planow")
        rental.refresh_from_db()
        assert rental.status == RentalStatus.CANCELLED

        reservation2 = _confirmed_reservation(customer, car)
        rental2 = RentalService.convert_from_reservation(
            reservation2,
        )
        RentalService.start(rental2)
        with pytest.raises(ValidationError, match="zaplanowany"):
            RentalService.cancel(rental2)

    def test_rental_blocks_availability(self, customer, car: Car) -> None:
        reservation = _confirmed_reservation(customer, car)
        RentalService.convert_from_reservation(reservation)
        start, end = _interval(12, 14)
        assert AvailabilityService.is_car_available(car, start, end) is False

    def test_converted_reservation_not_blocking_via_reservation_status(
        self, customer, car: Car
    ) -> None:
        reservation = _confirmed_reservation(customer, car)
        RentalService.convert_from_reservation(reservation)
        reservation.refresh_from_db()
        assert reservation.blocks_availability is False
        assert reservation.status == ReservationStatus.CONVERTED_TO_RENTAL

    def test_duplicate_rental_rejected(self, customer, car: Car) -> None:
        reservation = _confirmed_reservation(customer, car)
        RentalService.convert_from_reservation(reservation)
        with pytest.raises(ValidationError, match="przypisany"):
            RentalService.convert_from_reservation(reservation)

    def test_overlapping_rental_rejected(self, customer, car: Car) -> None:
        reservation1 = _confirmed_reservation(customer, car)
        RentalService.convert_from_reservation(reservation1)

        start, end = _interval(12, 14)
        reservation2 = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        PriceSnapshotService.freeze(reservation2)
        with pytest.raises(ValidationError, match="wynajem"):
            RentalService.convert_from_reservation(reservation2)
