from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import PriceLine
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import (
    AmountType,
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
    PricingRule,
    PricingRuleType,
)
from apps.pricing.services.pricing import PricingService


@pytest.fixture
def price_list(db) -> PriceList:
    return PriceList.objects.create(
        name="Test cennik",
        slug="test-cennik",
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-calc")


@pytest.fixture
def car(db, category: CarCategory) -> Car:
    return Car.objects.create(
        category=category,
        registration_number="CALC001",
        make="Test",
        model="Car",
        year=2024,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def daily_rate(db, price_list: PriceList, category: CarCategory) -> DailyRate:
    return DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )


@pytest.mark.django_db
class TestPricingService:
    def test_base_daily_rental(
        self,
        car: Car,
        daily_rate: DailyRate,
    ) -> None:
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 6, 10, 0, tzinfo=UTC)
        result = PricingService.calculate(car=car, start_at=start, end_at=end)
        assert result.total == Decimal("500.00")
        assert len(result.lines) == 1
        assert result.lines[0].line_type == "daily_rental"

    def test_weekend_surcharge_per_day(
        self,
        car: Car,
        daily_rate: DailyRate,
        price_list: PriceList,
    ) -> None:
        PricingRule.objects.create(
            price_list=price_list,
            rule_type=PricingRuleType.WEEKEND_SURCHARGE,
            name="Weekend",
            amount_type=AmountType.PER_DAY,
            value=Decimal("20.00"),
            priority=10,
        )
        # Pt 2026-06-05 – Nd 2026-06-07 (3 doby, wszystkie weekendowe)
        start = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 8, 10, 0, tzinfo=UTC)
        result = PricingService.calculate(car=car, start_at=start, end_at=end)
        assert result.total == Decimal("360.00")  # 300 base + 60 weekend

    def test_long_rental_discount(
        self,
        car: Car,
        daily_rate: DailyRate,
        price_list: PriceList,
    ) -> None:
        PricingRule.objects.create(
            price_list=price_list,
            rule_type=PricingRuleType.LONG_RENTAL_DISCOUNT,
            name="Rabat 7 dni",
            amount_type=AmountType.PERCENT,
            value=Decimal("10"),
            min_rental_days=7,
            priority=20,
        )
        start = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
        result = PricingService.calculate(car=car, start_at=start, end_at=end)
        assert result.total == Decimal("720.00")  # 800 - 10%

    def test_extra_child_seat(
        self,
        car: Car,
        daily_rate: DailyRate,
        price_list: PriceList,
    ) -> None:
        ExtraService.objects.create(
            price_list=price_list,
            code="child_seat",
            name="Fotelik",
            charge_type=ExtraServiceChargeType.PER_RENTAL,
            amount=Decimal("40.00"),
        )
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 3, 10, 0, tzinfo=UTC)
        result = PricingService.calculate(
            car=car,
            start_at=start,
            end_at=end,
            extra_codes=["child_seat"],
        )
        assert result.total == Decimal("240.00")  # 200 + 40

    def test_snapshot_immutable_when_pricelist_changes(
        self,
        car: Car,
        daily_rate: DailyRate,
        price_list: PriceList,
    ) -> None:
        from apps.bookings.models import Customer, Reservation, ReservationStatus

        customer = Customer.objects.create(
            first_name="A",
            last_name="B",
            email="ab@test.com",
        )
        start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 8, 4, 10, 0, tzinfo=UTC)
        reservation = Reservation.objects.create(
            customer=customer,
            car=car,
            start_at=start,
            end_at=end,
            status=ReservationStatus.DRAFT,
        )
        PriceSnapshotService.freeze(reservation)
        total_before = PriceSnapshotService.reservation_total(reservation)

        daily_rate.amount = Decimal("999.00")
        daily_rate.save()

        assert PriceSnapshotService.reservation_total(reservation) == total_before
        assert PriceLine.objects.filter(reservation=reservation).count() == 1

    def test_missing_daily_rate(self, car: Car, price_list: PriceList) -> None:
        start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 3, 10, 0, tzinfo=UTC)
        with pytest.raises(ValidationError, match="stawki"):
            PricingService.calculate(car=car, start_at=start, end_at=end)
