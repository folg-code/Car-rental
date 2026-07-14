from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.models import PaymentIntent, PaymentType
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-intent",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik intent",
        slug="test-intent",
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
def reservation(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@intent.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1INT01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )
    start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    return ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.PENDING_PAYMENT,
    )


@pytest.fixture
def rental(reservation):
    confirmed = ReservationService.confirm(reservation)
    return RentalService.convert_from_reservation(confirmed)


@pytest.mark.django_db
class TestPaymentIntent:
    def test_create_for_rental(self, rental) -> None:
        intent = PaymentIntent.objects.create(
            rental=rental,
            amount=Decimal("500.00"),
            payment_type=PaymentType.RENTAL_FEE,
        )
        assert intent.rental_id == rental.pk
        assert intent.reservation_id is None
        assert "wynajem" in str(intent)

    def test_create_for_reservation_without_rental(self, reservation) -> None:
        intent = PaymentIntent.objects.create(
            reservation=reservation,
            amount=Decimal("800.00"),
            payment_type=PaymentType.RENTAL_FEE,
        )
        assert intent.rental_id is None
        assert intent.reservation_id == reservation.pk
        assert reservation.payment_intents.count() == 1
        assert "rezerwacja" in str(intent)

    def test_requires_rental_or_reservation(self) -> None:
        intent = PaymentIntent(amount=Decimal("100.00"))
        with pytest.raises(ValidationError, match="wynajmem lub rezerwacja"):
            intent.save()

    def test_rejects_mismatched_reservation_for_rental(self, rental, category) -> None:
        other_customer = Customer.objects.create(
            first_name="Ewa",
            last_name="Nowak",
            email="ewa@intent.test",
        )
        other_car = Car.objects.create(
            category=category,
            registration_number="KR1INT02",
            make="VW",
            model="Polo",
            year=2021,
            status=CarStatus.ACTIVE,
        )
        other_reservation = ReservationService.create(
            customer_id=other_customer.pk,
            car_id=other_car.pk,
            start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
            status=ReservationStatus.PENDING_PAYMENT,
        )
        intent = PaymentIntent(
            rental=rental,
            reservation=other_reservation,
            amount=Decimal("500.00"),
        )
        with pytest.raises(ValidationError, match="nie zgadza sie"):
            intent.save()
