from decimal import Decimal

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.bookings.models import Reservation, ReservationStatus
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.models import PaymentIntent, PaymentIntentStatus
from apps.pricing.models import DailyRate, PriceList
from apps.website.services.public_payment import PublicPaymentOrchestrator


@pytest.fixture
def pay_car(db) -> Car:
    category = CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-pay-ui",
    )
    price_list = PriceList.objects.create(
        name="Test pay ui",
        slug="test-pay-ui",
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
        registration_number="PAYUI01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _book(client, car: Car) -> Reservation:
    client.post(
        reverse("website:public_booking"),
        {
            "car": str(car.pk),
            "start_at": "2026-06-10T10:00",
            "end_at": "2026-06-15T10:00",
            "first_name": "Anna",
            "last_name": "Platnik",
            "email": "anna-pay@example.com",
            "accept_terms": "on",
        },
    )
    client.get(reverse("website:booking_confirmation"))
    return Reservation.objects.get()


@pytest.mark.django_db
class TestPublicPaymentViews:
    def test_confirmation_shows_pay_button(self, client, pay_car: Car) -> None:
        _book(client, pay_car)
        reservation = Reservation.objects.get()
        response = client.get(
            reverse(
                "website:booking_confirmation_by_id",
                kwargs={"reservation_id": reservation.pk},
            ),
        )
        assert response.status_code == 200
        assert b"online" in response.content
        pay_url = reverse(
            "website:start_payment",
            kwargs={"reservation_id": reservation.pk},
        )
        assert pay_url.encode() in response.content

    def test_start_payment_redirects_to_mock_checkout(
        self, client, pay_car: Car
    ) -> None:
        reservation = _book(client, pay_car)
        response = client.get(
            reverse(
                "website:start_payment",
                kwargs={"reservation_id": reservation.pk},
            ),
        )
        assert response.status_code == 302
        assert "/platnosc/mock/" in response.url
        assert PaymentIntent.objects.filter(reservation=reservation).exists()

    def test_mock_checkout_completes_payment(self, client, pay_car: Car) -> None:
        reservation = _book(client, pay_car)
        client.get(
            reverse(
                "website:start_payment",
                kwargs={"reservation_id": reservation.pk},
            ),
        )
        intent = PaymentIntent.objects.get(reservation=reservation)
        mock_url = (
            f"{reverse('website:mock_payment_checkout')}"
            f"?ref={intent.external_reference}&intent={intent.pk}"
        )
        get_response = client.get(mock_url)
        assert get_response.status_code == 200
        assert b"500" in get_response.content

        post_response = client.post(mock_url)
        assert post_response.status_code == 302
        assert post_response.url == reverse(
            "website:payment_success",
            kwargs={"reservation_id": reservation.pk},
        )

        intent.refresh_from_db()
        assert intent.status == PaymentIntentStatus.SUCCEEDED

        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.CONFIRMED

        success = client.get(post_response.url)
        assert success.status_code == 200
        assert "Płatność przyjęta".encode() in success.content

    @override_settings(PAYMENT_GATEWAY_WEBHOOK_SECRET="prod-like-secret")
    def test_mock_checkout_completes_payment_with_webhook_secret(
        self,
        client,
        pay_car: Car,
    ) -> None:
        """Regresja: mock checkout musi działać gdy sekret webhooka jest ustawiony."""
        reservation = _book(client, pay_car)
        client.get(
            reverse(
                "website:start_payment",
                kwargs={"reservation_id": reservation.pk},
            ),
        )
        intent = PaymentIntent.objects.get(reservation=reservation)
        mock_url = (
            f"{reverse('website:mock_payment_checkout')}"
            f"?ref={intent.external_reference}&intent={intent.pk}"
        )
        post_response = client.post(mock_url)
        assert post_response.status_code == 302
        assert post_response.url == reverse(
            "website:payment_success",
            kwargs={"reservation_id": reservation.pk},
        )
        reservation.refresh_from_db()
        assert reservation.status == ReservationStatus.CONFIRMED

    def test_start_payment_rejects_confirmed_reservation(
        self,
        client,
        pay_car: Car,
    ) -> None:
        reservation = _book(client, pay_car)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status", "updated_at"])
        response = client.get(
            reverse(
                "website:start_payment",
                kwargs={"reservation_id": reservation.pk},
            ),
        )
        assert response.status_code == 400
        assert b"nie oczekuje" in response.content


@pytest.mark.django_db
class TestPublicPaymentOrchestrator:
    def test_reuses_pending_intent(self, pay_car: Car, client) -> None:
        reservation = _book(client, pay_car)
        first = PublicPaymentOrchestrator.start_online_payment(
            reservation.pk,
            success_url="http://testserver/sukces/",
            cancel_url="http://testserver/anuluj/",
        )
        second = PublicPaymentOrchestrator.start_online_payment(
            reservation.pk,
            success_url="http://testserver/sukces/",
            cancel_url="http://testserver/anuluj/",
        )
        assert PaymentIntent.objects.filter(reservation=reservation).count() == 1
        assert first.external_reference != second.external_reference
