from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.models import (
    REVENUE_PAYMENT_TYPES,
    PaymentMethod,
    PaymentType,
)
from apps.payments.selectors.payment import (
    get_rental_balance_due,
    get_rental_deposit_balance,
    get_rental_payment_summary,
    get_rental_revenue_total,
    get_revenue_total_in_period,
    rental_has_balance_due,
)
from apps.payments.services.payment import PaymentService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-pay",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik platnosci",
        slug="test-platnosci",
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
        first_name="Anna",
        last_name="Nowak",
        email="anna@pay.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1PAY01",
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
class TestPaymentService:
    def test_record_rental_fee(self, rental) -> None:
        payment = PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("800.00"),
        )
        assert payment.payment_type == PaymentType.RENTAL_FEE
        assert payment.amount == Decimal("800.00")
        assert payment.is_revenue is True

    def test_record_deposit_default_amount(self, rental) -> None:
        payment = PaymentService.record_deposit(rental_id=rental.pk)
        assert payment.payment_type == PaymentType.DEPOSIT
        assert payment.amount == Decimal("1000.00")
        assert payment.is_revenue is False

    def test_deposit_not_counted_as_revenue(self, rental) -> None:
        PaymentService.record_deposit(rental_id=rental.pk)
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("500.00"),
        )
        assert get_rental_revenue_total(rental.pk) == Decimal("500.00")
        assert get_rental_deposit_balance(rental.pk) == Decimal("1000.00")

    def test_refund_deposit(self, rental) -> None:
        PaymentService.record_deposit(rental_id=rental.pk)
        refund = PaymentService.refund_deposit(
            rental_id=rental.pk,
            amount=Decimal("400.00"),
        )
        assert refund.payment_type == PaymentType.REFUND
        assert get_rental_deposit_balance(rental.pk) == Decimal("600.00")

    def test_refund_exceeds_balance_rejected(self, rental) -> None:
        PaymentService.record_deposit(rental_id=rental.pk, amount=Decimal("100.00"))
        with pytest.raises(ValidationError, match="przekracza saldo"):
            PaymentService.refund_deposit(
                rental_id=rental.pk,
                amount=Decimal("200.00"),
            )

    def test_payment_summary(self, rental) -> None:
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("200.00"),
        )
        summary = get_rental_payment_summary(rental.pk)
        assert summary["rental_fees_paid"] == Decimal("200.00")
        assert summary["price_total"] > 0
        assert summary["rental_fee_due"] == summary["price_total"] - Decimal("200.00")

    def test_balance_due_helpers(self, rental) -> None:
        assert get_rental_balance_due(rental.pk) > 0
        assert rental_has_balance_due(rental.pk) is True
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("10000.00"),
        )
        assert get_rental_balance_due(rental.pk) == Decimal("0")
        assert rental_has_balance_due(rental.pk) is False

    def test_revenue_total_in_period_excludes_deposit(self, rental) -> None:
        paid_at = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("400.00"),
            paid_at=paid_at,
        )
        PaymentService.record_deposit(rental_id=rental.pk, paid_at=paid_at)
        start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 23, 59, tzinfo=UTC)
        assert get_revenue_total_in_period(start, end) == Decimal("400.00")

    def test_revenue_types_constant(self) -> None:
        assert PaymentType.DEPOSIT not in REVENUE_PAYMENT_TYPES
        assert PaymentType.REFUND not in REVENUE_PAYMENT_TYPES
        assert PaymentType.RENTAL_FEE in REVENUE_PAYMENT_TYPES

    def test_reservation_payment_included_in_rental_summary(self, rental) -> None:
        reservation = rental.reservation
        PaymentService.record_reservation_payment(
            reservation_id=reservation.pk,
            amount=Decimal("300.00"),
            payment_type=PaymentType.RENTAL_FEE,
            method=PaymentMethod.ONLINE_GATEWAY,
        )
        summary = get_rental_payment_summary(rental.pk)
        assert summary["rental_fees_paid"] == Decimal("300.00")
        assert summary["revenue_total"] == Decimal("300.00")

    def test_convert_links_reservation_payments_to_rental(self, rental) -> None:
        from apps.bookings.models import Customer, ReservationStatus
        from apps.bookings.services.reservation import ReservationService
        from apps.fleet.models import Car, CarStatus
        from apps.payments.models import Payment

        reservation = rental.reservation
        PaymentService.record_reservation_payment(
            reservation_id=reservation.pk,
            amount=Decimal("150.00"),
            payment_type=PaymentType.RENTAL_FEE,
            method=PaymentMethod.CARD,
        )
        customer = Customer.objects.create(
            first_name="B",
            last_name="Test",
            email="b2@test.com",
        )
        car = Car.objects.create(
            category=reservation.car.category,
            registration_number="LINK01",
            make="Test",
            model="Car",
            year=2024,
            status=CarStatus.ACTIVE,
        )
        other = ReservationService.create(
            customer_id=customer.pk,
            car_id=car.pk,
            start_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            end_at=datetime(2026, 9, 5, 10, 0, tzinfo=UTC),
            status=ReservationStatus.CONFIRMED,
        )
        PaymentService.record_reservation_payment(
            reservation_id=other.pk,
            amount=Decimal("99.00"),
            payment_type=PaymentType.RENTAL_FEE,
            method=PaymentMethod.CASH,
        )
        other_rental = RentalService.convert_from_reservation(other)
        assert (
            Payment.objects.filter(
                reservation_id=other.pk,
                rental_id=other_rental.pk,
            ).count()
            == 1
        )
        summary = get_rental_payment_summary(other_rental.pk)
        assert summary["rental_fees_paid"] == Decimal("99.00")
