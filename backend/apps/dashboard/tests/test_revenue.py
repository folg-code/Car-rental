from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.rental import RentalService
from apps.bookings.services.reservation import ReservationService
from apps.dashboard.selectors.revenue import get_month_revenue
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.models import PaymentMethod, PaymentType
from apps.payments.selectors.payment import get_revenue_total_in_period
from apps.payments.services.payment import PaymentService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-revenue",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik revenue",
        slug="test-revenue",
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
        first_name="Ewa",
        last_name="Nowak",
        email="ewa@revenue.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1REV01",
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
class TestMonthRevenueSelector:
    def test_month_revenue_sums_revenue_payments_only(self, rental) -> None:
        as_of = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("500.00"),
            paid_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
        )
        PaymentService.record_deposit(
            rental_id=rental.pk,
            paid_at=datetime(2026, 7, 10, 10, 0, tzinfo=UTC),
        )
        PaymentService.record_payment(
            rental_id=rental.pk,
            amount=Decimal("50.00"),
            payment_type=PaymentType.EXTRA_CHARGE,
            method=PaymentMethod.CASH,
            paid_at=datetime(2026, 7, 12, 14, 0, tzinfo=UTC),
        )

        assert get_month_revenue(as_of=as_of) == Decimal("550.00")

    def test_excludes_payments_outside_current_month(self, rental) -> None:
        as_of = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("300.00"),
            paid_at=datetime(2026, 6, 30, 23, 0, tzinfo=UTC),
        )
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("200.00"),
            paid_at=datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
        )

        assert get_month_revenue(as_of=as_of) == Decimal("200.00")

    def test_period_selector_matches_month_bounds(self, rental) -> None:
        as_of = datetime(2026, 7, 20, 18, 0, tzinfo=UTC)
        month_start = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
        PaymentService.record_rental_fee(
            rental_id=rental.pk,
            amount=Decimal("100.00"),
            paid_at=datetime(2026, 7, 5, 8, 0, tzinfo=UTC),
        )

        assert get_revenue_total_in_period(month_start, as_of) == get_month_revenue(
            as_of=as_of
        )
