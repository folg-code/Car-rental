from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.fleet.models import CarCategory
from apps.pricing.models import (
    AmountType,
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
    PricingRule,
    PricingRuleType,
)


@pytest.fixture
def price_list(db) -> PriceList:
    return PriceList.objects.create(
        name="Cennik 2026",
        slug="cennik-2026",
        is_default=True,
    )


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-pricing")


@pytest.mark.django_db
class TestPriceList:
    def test_invalid_date_range(self) -> None:
        pl = PriceList(
            name="Test",
            slug="test-invalid",
            valid_from="2026-12-01",
            valid_to="2026-01-01",
        )
        with pytest.raises(ValidationError):
            pl.full_clean()


@pytest.mark.django_db
class TestDailyRate:
    def test_create_daily_rate(
        self, price_list: PriceList, category: CarCategory
    ) -> None:
        rate = DailyRate.objects.create(
            price_list=price_list,
            category=category,
            amount=Decimal("120.00"),
        )
        assert rate.pk is not None
        assert "120" in str(rate)

    def test_unique_per_list_and_category(
        self, price_list: PriceList, category: CarCategory
    ) -> None:
        DailyRate.objects.create(
            price_list=price_list,
            category=category,
            amount=Decimal("100.00"),
        )
        with pytest.raises(IntegrityError):
            DailyRate.objects.create(
                price_list=price_list,
                category=category,
                amount=Decimal("200.00"),
            )


@pytest.mark.django_db
class TestPricingRule:
    def test_long_rental_requires_min_days(self, price_list: PriceList) -> None:
        rule = PricingRule(
            price_list=price_list,
            rule_type=PricingRuleType.LONG_RENTAL_DISCOUNT,
            name="Rabat 7+ dni",
            amount_type=AmountType.PERCENT,
            value=Decimal("10"),
        )
        with pytest.raises(ValidationError):
            rule.full_clean()

    def test_percent_over_100_rejected(self, price_list: PriceList) -> None:
        rule = PricingRule(
            price_list=price_list,
            rule_type=PricingRuleType.WEEKEND_SURCHARGE,
            name="Weekend",
            amount_type=AmountType.PERCENT,
            value=Decimal("150"),
        )
        with pytest.raises(ValidationError):
            rule.full_clean()


@pytest.mark.django_db
class TestExtraService:
    def test_create_extra(self, price_list: PriceList) -> None:
        extra = ExtraService.objects.create(
            price_list=price_list,
            code="child_seat",
            name="Fotelik dzieciecy",
            charge_type=ExtraServiceChargeType.PER_RENTAL,
            amount=Decimal("40.00"),
        )
        assert extra.pk is not None
