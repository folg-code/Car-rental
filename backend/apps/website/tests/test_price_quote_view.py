from decimal import Decimal
from urllib.parse import urlencode

import pytest
from django.urls import reverse

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import (
    DailyRate,
    ExtraService,
    ExtraServiceChargeType,
    PriceList,
)


@pytest.fixture
def quote_car(db) -> Car:
    category = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-quote-ui",
    )
    price_list = PriceList.objects.create(
        name="Test cennik quote ui",
        slug="test-quote-ui",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    ExtraService.objects.create(
        price_list=price_list,
        code="child_seat",
        name="Fotelik",
        charge_type=ExtraServiceChargeType.PER_RENTAL,
        amount=Decimal("40.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="QTEUI01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _quote_url(**params: str) -> str:
    base = reverse("website:price_quote")
    if not params:
        return base
    return f"{base}?{urlencode(params)}"


def _quote_params(
    car: Car,
    *,
    extras: list[str] | None = None,
) -> dict[str, str]:
    payload = {
        "car": str(car.pk),
        "start_at": "2026-06-10T10:00",
        "end_at": "2026-06-15T10:00",
    }
    if extras:
        payload["extras"] = extras
    return payload


@pytest.mark.django_db
class TestPriceQuoteView:
    def test_get_returns_form(self, client) -> None:
        response = client.get(reverse("website:price_quote"))
        assert response.status_code == 200
        assert b"Orientacyjna wycena" in response.content
        assert b"Oblicz wycene" in response.content

    def test_get_with_params_shows_quote(self, client, quote_car: Car) -> None:
        response = client.get(_quote_url(**_quote_params(quote_car)))
        assert response.status_code == 200
        assert b"500,00" in response.content
        assert b"PLN" in response.content
        assert b"orientacyjnie" in response.content.lower()
        assert b"Toyota" in response.content

    def test_get_with_extra_includes_extra_line(self, client, quote_car: Car) -> None:
        url = (
            f"{reverse('website:price_quote')}"
            f"?car={quote_car.pk}&start_at=2026-06-10T10:00"
            f"&end_at=2026-06-15T10:00&extras=child_seat"
        )
        response = client.get(url)
        assert response.status_code == 200
        assert b"Fotelik" in response.content
        assert b"540,00" in response.content

    def test_get_rejects_invalid_interval(self, client, quote_car: Car) -> None:
        response = client.get(
            _quote_url(
                car=str(quote_car.pk),
                start_at="2026-06-15T10:00",
                end_at="2026-06-10T10:00",
            )
        )
        assert response.status_code == 200
        assert b"pozniejsza" in response.content.lower()

    def test_availability_search_links_to_quote(self, client, quote_car: Car) -> None:
        search_url = reverse("website:availability_search")
        response = client.post(
            search_url,
            {
                "start_at": "2026-06-10T10:00",
                "end_at": "2026-06-15T10:00",
            },
        )
        assert response.status_code == 200
        assert reverse("website:price_quote") in response.content.decode()
        assert f"car={quote_car.pk}" in response.content.decode()
