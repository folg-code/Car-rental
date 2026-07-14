from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.chat_tools import (
    build_booking_deep_link,
    execute_estimate_price,
    execute_get_faq_snippet,
    execute_get_my_reservation_status,
    execute_search_available_cars,
    format_tool_results,
)


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(name="Kompakt", slug="kompakt-tools")


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Test cennik tools",
        slug="test-tools",
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
        registration_number="TOOL001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _interval() -> tuple[datetime, datetime]:
    return (
        datetime(2026, 9, 10, 10, 0, tzinfo=UTC),
        datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
    )


@pytest.mark.django_db
class TestChatTools:
    def test_search_available_cars_returns_booking_links(self, car: Car) -> None:
        start, end = _interval()
        result = execute_search_available_cars(start_at=start, end_at=end)
        assert result.data["count"] == 1
        assert "booking_link" in result.data["cars"][0]
        assert f"car={car.pk}" in result.data["cars"][0]["booking_link"]

    def test_estimate_price_returns_total(self, car: Car) -> None:
        start, end = _interval()
        result = execute_estimate_price(car_id=car.pk, start_at=start, end_at=end)
        assert result.data["total"] == "500.00"
        assert "Orientacyjna" in result.data["disclaimer"]

    def test_build_booking_deep_link(self, car: Car) -> None:
        start, end = _interval()
        link = build_booking_deep_link(car_id=car.pk, start_at=start, end_at=end)
        assert f"car={car.pk}" in link
        assert "start_at=" in link

    def test_faq_snippet_filters_topic(self) -> None:
        result = execute_get_faq_snippet(topic="kaucj")
        assert result.data["snippets"]
        assert any("kaucj" in s["question"].lower() for s in result.data["snippets"])

    def test_reservation_status_requires_login(self) -> None:
        result = execute_get_my_reservation_status(user=None)
        assert "error" in result.data

    def test_format_tool_results_search(self, car: Car) -> None:
        start, end = _interval()
        search = execute_search_available_cars(start_at=start, end_at=end)
        text = format_tool_results((search,))
        assert "Toyota" in text
        assert "Rezerwacja:" in text
