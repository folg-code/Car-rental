from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.chat_tool_router import (
    ChatToolRouter,
    parse_date_range,
    parse_relative_date_range,
    resolve_date_range,
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


class TestParseRelativeDateRange:
    def test_jutro(self) -> None:
        today = date(2026, 7, 17)
        result = parse_relative_date_range("wolne auta na jutro", today=today)
        assert result is not None
        start, end = result
        warsaw = ZoneInfo("Europe/Warsaw")
        assert start == datetime(2026, 7, 18, 10, 0, tzinfo=warsaw)
        assert end == datetime(2026, 7, 19, 10, 0, tzinfo=warsaw)

    def test_weekend(self) -> None:
        today = date(2026, 7, 15)  # Wednesday
        result = parse_relative_date_range("auto na weekend", today=today)
        assert result is not None
        start, end = result
        assert start.date() == date(2026, 7, 18)
        assert end.date() == date(2026, 7, 19)

    def test_weekday_range(self) -> None:
        today = date(2026, 7, 13)  # Monday
        result = parse_relative_date_range(
            "od piatku do niedzieli",
            today=today,
        )
        assert result is not None
        start, end = result
        assert start.date() == date(2026, 7, 17)
        assert end.date() == date(2026, 7, 19)


@pytest.mark.django_db
class TestChatToolRouter:
    def test_routes_availability_question(self, car) -> None:
        del car
        results = ChatToolRouter.run_for_message(
            "Jakie auta sa wolne 2026-09-10 i 2026-09-15?",
        )
        assert len(results) == 1
        assert results[0].tool_name == "search_available_cars"

    def test_asks_clarifying_when_no_dates(self) -> None:
        results = ChatToolRouter.run_for_message("Sprawdz dostepnosc samochodow")
        assert len(results) == 1
        assert results[0].tool_name == "ask_clarifying_question"
        assert "termin" in results[0].data["question"].lower()

    def test_how_to_booking_does_not_force_tools(self) -> None:
        assert ChatToolRouter.run_for_message("Jak zarezerwowac auto?") == ()

    @patch(
        "apps.website.services.chat_tool_router.timezone.localdate",
        return_value=date(2026, 7, 17),
    )
    def test_routes_relative_jutro(self, _mock_today, car) -> None:
        del car
        results = ChatToolRouter.run_for_message("Czy sa wolne auta na jutro?")
        assert any(r.tool_name == "search_available_cars" for r in results)
        search = next(r for r in results if r.tool_name == "search_available_cars")
        assert "2026-07-18" in search.data["start_at"]

    def test_routes_deposit_for_category(self, category: CarCategory) -> None:
        category.deposit = Decimal("1500.00")
        category.save(update_fields=["deposit"])
        results = ChatToolRouter.run_for_message("Jaka kaucja za kompakt?")
        assert results[0].tool_name == "get_deposit_info"
        assert results[0].data["categories"][0]["id"] == category.pk
        assert results[0].data["categories"][0]["deposit"] == "1500.00"

    def test_routes_faq_without_dates(self) -> None:
        results = ChatToolRouter.run_for_message("Co mowi regulamin o anulowaniu?")
        assert len(results) == 1
        assert results[0].tool_name == "get_faq_snippet"

    def test_routes_documents_to_faq(self) -> None:
        results = ChatToolRouter.run_for_message("Jakie dokumenty sa potrzebne?")
        assert len(results) == 1
        assert results[0].tool_name == "get_faq_snippet"
        assert results[0].data["snippets"]

    def test_anonymous_reservation_status(self) -> None:
        results = ChatToolRouter.run_for_message("Jaki status mojej rezerwacji?")
        assert results[0].tool_name == "get_my_reservation_status"
        assert "error" in results[0].data

    def test_no_tools_for_generic_greeting(self) -> None:
        assert ChatToolRouter.run_for_message("Czesc") == ()

    def test_resolve_prefers_iso_over_relative(self) -> None:
        result = resolve_date_range(
            "wolne 2026-09-10 i 2026-09-12 jutro",
        )
        assert result is not None
        assert result[0].date() == date(2026, 9, 10)
