from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.chat_tool_router import (
    ChatToolRouter,
    parse_date_range,
)


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-router")


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Test router",
        slug="test-router",
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
        registration_number="ROUTE01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


class TestParseDateRange:
    def test_parses_two_iso_dates(self) -> None:
        result = parse_date_range(
            "Czy macie wolne auta 2026-09-10 i 2026-09-15?",
        )
        assert result is not None
        start, end = result
        assert start == datetime(2026, 9, 10, 10, 0, tzinfo=UTC)
        assert end == datetime(2026, 9, 15, 10, 0, tzinfo=UTC)

    def test_returns_none_for_single_date(self) -> None:
        assert parse_date_range("2026-09-10") is None


@pytest.mark.django_db
class TestChatToolRouter:
    def test_routes_availability_question(self, car) -> None:
        del car
        results = ChatToolRouter.run_for_message(
            "Jakie auta sa wolne 2026-09-10 i 2026-09-15?",
        )
        assert len(results) == 1
        assert results[0].tool_name == "search_available_cars"

    def test_routes_faq_without_dates(self) -> None:
        results = ChatToolRouter.run_for_message("Co mowi regulamin o anulowaniu?")
        assert len(results) == 1
        assert results[0].tool_name == "get_faq_snippet"

    def test_anonymous_reservation_status(self) -> None:
        results = ChatToolRouter.run_for_message("Jaki status mojej rezerwacji?")
        assert results[0].tool_name == "get_my_reservation_status"
        assert "error" in results[0].data

    def test_no_tools_for_generic_greeting(self) -> None:
        assert ChatToolRouter.run_for_message("Czesc") == ()
