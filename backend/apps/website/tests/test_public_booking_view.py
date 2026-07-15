from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bookings.models import Reservation, ReservationStatus
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.views import PUBLIC_BOOKING_SESSION_KEY


@pytest.fixture
def booking_car(db) -> Car:
    category = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-booking-ui",
    )
    price_list = PriceList.objects.create(
        name="Test booking ui",
        slug="test-booking-ui",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("100.00"),
    )
    return Car.objects.create(
        category=category,
        registration_number="BOKUI01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _booking_payload(car: Car) -> dict[str, str]:
    return {
        "car": str(car.pk),
        "start_at": "2026-06-10T10:00",
        "end_at": "2026-06-15T10:00",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "jan-ui@example.com",
        "phone": "+48123456789",
        "accept_terms": "on",
    }


@pytest.mark.django_db
class TestPublicBookingView:
    def test_get_redirects_to_offer_booking_step(self, client) -> None:
        response = client.get(reverse("website:public_booking"), follow=True)
        assert response.status_code == 200
        assert "Złóż rezerwację".encode() in response.content
        assert reverse("website:car_offer") in response.redirect_chain[-1][0]

    def test_post_creates_reservation_and_redirects(
        self, client, booking_car: Car
    ) -> None:
        response = client.post(
            reverse("website:public_booking"),
            _booking_payload(booking_car),
        )
        assert response.status_code == 302
        assert response.url == reverse("website:booking_confirmation")
        reservation = Reservation.objects.get()
        assert reservation.status == ReservationStatus.PENDING_PAYMENT
        assert reservation.car_id == booking_car.pk

    def test_confirmation_requires_session(self, client, booking_car: Car) -> None:
        client.post(
            reverse("website:public_booking"),
            _booking_payload(booking_car),
        )
        response = client.get(reverse("website:booking_confirmation"))
        assert response.status_code == 200
        assert "Rezerwacja przyjęta".encode() in response.content
        assert b"500" in response.content

        response_again = client.get(reverse("website:booking_confirmation"))
        assert response_again.status_code == 302

    def test_post_rejects_missing_contact(self, client, booking_car: Car) -> None:
        payload = _booking_payload(booking_car)
        payload.pop("email")
        payload.pop("phone")
        response = client.post(reverse("website:public_booking"), payload)
        assert response.status_code == 200
        assert b"e-mail lub numer telefonu" in response.content

    def test_get_prefills_car_from_query(self, client, booking_car: Car) -> None:
        url = (
            f"{reverse('website:public_booking')}?car={booking_car.pk}"
            "&start_at=2026-06-10T10:00&end_at=2026-06-15T10:00"
        )
        response = client.get(url, follow=True)
        assert response.status_code == 200
        assert str(booking_car.pk).encode() in response.content

    def test_confirmation_without_session_redirects_home(self, client) -> None:
        session = client.session
        session[PUBLIC_BOOKING_SESSION_KEY] = 99999
        session.save()
        response = client.get(reverse("website:booking_confirmation"))
        assert response.status_code == 302
        assert response.url == reverse("website:home")
