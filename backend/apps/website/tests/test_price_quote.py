from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.selectors.price_quote import get_price_quote


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-quote")


@pytest.fixture
def price_list(db) -> PriceList:
    return PriceList.objects.create(
        name="Test cennik quote",
        slug="test-quote",
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def car(db, category: CarCategory, price_list: PriceList) -> Car:
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("120.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="QUOTE01",
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
class TestPriceQuoteSelector:
    def test_returns_pricing_result(self, car: Car) -> None:
        start, end = _interval()
        result = get_price_quote(car=car, start_at=start, end_at=end)
        assert result.car.pk == car.pk
        assert result.pricing.total == Decimal("600.00")
        assert result.pricing.currency == "PLN"
        assert len(result.pricing.lines) == 1

    def test_rejects_invalid_interval(self, car: Car) -> None:
        start = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 10, 10, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            get_price_quote(car=car, start_at=start, end_at=end)

    def test_raises_when_no_daily_rate(
        self, category: CarCategory, price_list: PriceList
    ) -> None:
        car = Car.objects.create(
            category=category,
            registration_number="QUOTE02",
            make="Skoda",
            model="Fabia",
            year=2021,
            status=CarStatus.ACTIVE,
        )
        DailyRate.objects.filter(price_list=price_list, category=category).delete()
        start, end = _interval()
        with pytest.raises(ValidationError, match="stawki"):
            get_price_quote(car=car, start_at=start, end_at=end)
