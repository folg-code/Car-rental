from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def search_category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-search-ui",
    )


@pytest.fixture(autouse=True)
def default_price_list(db, search_category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Test cennik search ui",
        slug="test-search-ui",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=search_category,
        amount=Decimal("100.00"),
    )
    return price_list


@pytest.fixture
def search_car(db, search_category: CarCategory) -> Car:
    return Car.objects.create(
        category=search_category,
        registration_number="SRCHUI01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


@pytest.fixture
def customer(db) -> Customer:
    return Customer.objects.create(
        first_name="Anna",
        last_name="Nowak",
        email="anna@example.com",
        phone="+48987654321",
    )


def _search_url() -> str:
    return reverse("website:availability_search")


def _search_payload(
    start: datetime | None = None,
    end: datetime | None = None,
    *,
    category_id: int | None = None,
) -> dict[str, str]:
    start_at = start or datetime(2026, 6, 10, 10, 0, tzinfo=UTC)
    end_at = end or datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
    payload = {
        "start_at": start_at.strftime("%Y-%m-%dT%H:%M"),
        "end_at": end_at.strftime("%Y-%m-%dT%H:%M"),
    }
    if category_id is not None:
        payload["category"] = str(category_id)
    return payload


@pytest.mark.django_db
class TestAvailabilitySearchView:
    def test_get_returns_form(self, client) -> None:
        response = client.get(_search_url())
        assert response.status_code == 200
        assert b"Sprawdz dostepnosc" in response.content
        assert b"Szukaj wolnych aut" in response.content

    def test_post_shows_available_car(self, client, search_car: Car) -> None:
        response = client.post(_search_url(), _search_payload())
        assert response.status_code == 200
        assert b"Znaleziono 1 wolnych aut" in response.content
        assert b"Toyota" in response.content
        assert b"Yaris" in response.content
        assert b"SRCHUI01" not in response.content

    def test_post_shows_empty_when_car_reserved(
        self, client, customer: Customer, search_car: Car
    ) -> None:
        start = datetime(2026, 6, 10, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
        ReservationService.create(
            customer_id=customer.pk,
            car_id=search_car.pk,
            start_at=start,
            end_at=end,
            status=ReservationStatus.CONFIRMED,
        )
        response = client.post(_search_url(), _search_payload(start, end))
        assert response.status_code == 200
        assert b"Brak wolnych aut" in response.content

    def test_post_rejects_invalid_interval(self, client, search_car: Car) -> None:
        start = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
        end = datetime(2026, 6, 10, 10, 0, tzinfo=UTC)
        response = client.post(_search_url(), _search_payload(start, end))
        assert response.status_code == 200
        assert b"pozniejsza" in response.content.lower()

    def test_landing_links_to_search(self, client) -> None:
        response = client.get(reverse("website:home"))
        assert response.status_code == 200
        assert reverse("website:availability_search") in response.content.decode()
