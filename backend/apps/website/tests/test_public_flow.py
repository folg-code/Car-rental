"""Integracja flow publicznego: dostepnosc -> wycena -> rezerwacja (task 8.14)."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bookings.models import Reservation, ReservationStatus
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def flow_car(db) -> Car:
    category = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-flow",
    )
    price_list = PriceList.objects.create(
        name="Test cennik flow",
        slug="test-flow",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("120.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="FLOW001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


START_AT = "2026-06-10T10:00"
END_AT = "2026-06-15T10:00"


def _offer_url(car: Car) -> str:
    return (
        f"{reverse('website:car_offer')}?krok=wycena&car={car.pk}"
        f"&start_at={START_AT}&end_at={END_AT}"
    )


def _booking_url(car: Car) -> str:
    return (
        f"{reverse('website:public_booking')}?car={car.pk}"
        f"&start_at={START_AT}&end_at={END_AT}"
    )


@pytest.mark.django_db
class TestPublicWebsiteFlow:
    def test_availability_search_quote_and_booking(self, client, flow_car: Car) -> None:
        """Pelny flow klienta przez widoki website."""
        search_response = client.post(
            reverse("website:availability_search"),
            {"start_at": START_AT, "end_at": END_AT},
        )
        assert search_response.status_code == 200
        assert b"Znaleziono 1 wolnych aut" in search_response.content
        assert b"Toyota" in search_response.content
        assert reverse("website:car_offer") in search_response.content.decode()
        assert "Sprawdź ofertę".encode() in search_response.content

        quote_response = client.get(_offer_url(flow_car))
        assert quote_response.status_code == 200
        assert b"600" in quote_response.content
        assert b"PLN" in quote_response.content
        assert "Przejdź do rezerwacji".encode() in quote_response.content

        book_response = client.post(
            reverse("website:public_booking"),
            {
                "car": str(flow_car.pk),
                "start_at": START_AT,
                "end_at": END_AT,
                "first_name": "Ewa",
                "last_name": "Flow",
                "email": "ewa-flow@example.com",
                "phone": "+48111222333",
                "accept_terms": "on",
            },
        )
        assert book_response.status_code == 302
        assert book_response.url == reverse("website:booking_confirmation")

        confirm_response = client.get(reverse("website:booking_confirmation"))
        assert confirm_response.status_code == 200
        assert "Rezerwacja przyjęta".encode() in confirm_response.content
        assert b"Ewa" in confirm_response.content
        assert b"600" in confirm_response.content

        reservation = Reservation.objects.get()
        assert reservation.status == ReservationStatus.PENDING_PAYMENT
        assert reservation.car_id == flow_car.pk
        assert reservation.price_lines.exists()

    def test_booking_blocks_car_in_follow_up_search(
        self, client, flow_car: Car
    ) -> None:
        client.post(
            reverse("website:public_booking"),
            {
                "car": str(flow_car.pk),
                "start_at": START_AT,
                "end_at": END_AT,
                "first_name": "Jan",
                "last_name": "Flow",
                "email": "jan-flow@example.com",
                "accept_terms": "on",
            },
        )
        search_response = client.post(
            reverse("website:availability_search"),
            {"start_at": START_AT, "end_at": END_AT},
        )
        assert search_response.status_code == 200
        assert b"Brak wolnych aut" in search_response.content

    def test_public_pages_accessible_from_landing(self, client, flow_car: Car) -> None:
        landing = client.get(reverse("website:home"))
        assert landing.status_code == 200
        urls = (
            reverse("website:fleet_list"),
            reverse("website:availability_search"),
            reverse("website:terms"),
            reverse("website:contact"),
            reverse("website:faq"),
        )
        content = landing.content.decode()
        for url in urls:
            assert url in content

        fleet = client.get(reverse("website:fleet_list"))
        assert fleet.status_code == 200
        assert b"FLOW001" not in fleet.content
        assert b"Yaris" in fleet.content

    def test_quote_deep_link_prefills_booking_form(self, client, flow_car: Car) -> None:
        booking_get = client.get(_booking_url(flow_car), follow=True)
        assert booking_get.status_code == 200
        assert str(flow_car.pk).encode() in booking_get.content
