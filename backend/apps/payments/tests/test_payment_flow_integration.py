"""
Pelna integracja platnosci online (Sprint 9.10).

Przeplyw: rezerwacja publiczna -> intent -> mock checkout / webhook
-> confirm + Payment.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.bookings.models import Rental, Reservation, ReservationStatus
from apps.fleet.models import Car, CarStatus
from apps.payments.models import (
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentMethod,
    PaymentProviderEvent,
    PaymentType,
)
from apps.pricing.models import DailyRate


@pytest.fixture
def flow_car(db, category, default_price_list) -> Car:
    DailyRate.objects.filter(
        price_list=default_price_list,
        category=category,
    ).update(amount=Decimal("100.00"))
    return Car.objects.create(
        category=category,
        registration_number="FLOW001",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )


def _submit_public_booking(client, car: Car) -> Reservation:
    client.post(
        reverse("website:public_booking"),
        {
            "car": str(car.pk),
            "start_at": "2026-06-10T10:00",
            "end_at": "2026-06-15T10:00",
            "first_name": "Anna",
            "last_name": "Platnik",
            "email": "anna-flow@example.com",
            "accept_terms": "on",
        },
    )
    client.get(reverse("website:booking_confirmation"))
    return Reservation.objects.get()


def _start_online_payment(client, reservation: Reservation) -> PaymentIntent:
    response = client.get(
        reverse(
            "website:start_payment",
            kwargs={"reservation_id": reservation.pk},
        ),
    )
    assert response.status_code == 302
    intent = PaymentIntent.objects.get(reservation=reservation)
    assert intent.status == PaymentIntentStatus.PENDING
    assert intent.external_reference
    return intent


def _mock_checkout_url(intent: PaymentIntent) -> str:
    return (
        f"{reverse('website:mock_payment_checkout')}"
        f"?ref={intent.external_reference}&intent={intent.pk}"
    )


def _webhook_payload(
    *, event_id: str, external_reference: str, event_type: str
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "event_type": event_type,
            "external_reference": external_reference,
        },
    ).encode()


def _assert_fulfilled_online_payment(
    reservation: Reservation,
    intent: PaymentIntent,
    *,
    expected_amount: Decimal,
) -> None:
    reservation.refresh_from_db()
    intent.refresh_from_db()

    assert reservation.status == ReservationStatus.CONFIRMED
    assert intent.status == PaymentIntentStatus.SUCCEEDED
    assert not Rental.objects.filter(reservation=reservation).exists()

    payments = Payment.objects.filter(reservation=reservation, intent=intent)
    assert payments.count() == 1
    payment = payments.get()
    assert payment.amount == expected_amount
    assert payment.payment_type == PaymentType.RENTAL_FEE
    assert payment.method == PaymentMethod.ONLINE_GATEWAY
    assert payment.rental_id is None

    assert PaymentProviderEvent.objects.filter(intent=intent).count() == 1


@pytest.mark.django_db
class TestOnlinePaymentFlowIntegration:
    def test_booking_to_mock_checkout_fulfills_payment(
        self,
        client,
        flow_car: Car,
    ) -> None:
        reservation = _submit_public_booking(client, flow_car)
        assert reservation.status == ReservationStatus.PENDING_PAYMENT

        intent = _start_online_payment(client, reservation)
        expected_amount = intent.amount

        mock_url = _mock_checkout_url(intent)
        assert client.get(mock_url).status_code == 200

        response = client.post(mock_url)
        assert response.status_code == 302
        assert response.url == reverse(
            "website:payment_success",
            kwargs={"reservation_id": reservation.pk},
        )

        _assert_fulfilled_online_payment(
            reservation,
            intent,
            expected_amount=expected_amount,
        )

    def test_booking_to_webhook_endpoint_fulfills_payment(
        self,
        client,
        flow_car: Car,
    ) -> None:
        reservation = _submit_public_booking(client, flow_car)
        intent = _start_online_payment(client, reservation)

        payload = _webhook_payload(
            event_id="evt_flow_webhook_1",
            external_reference=intent.external_reference,
            event_type="payment.succeeded",
        )
        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        _assert_fulfilled_online_payment(
            reservation,
            intent,
            expected_amount=intent.amount,
        )

    def test_webhook_idempotent_does_not_double_payment(
        self,
        client,
        flow_car: Car,
    ) -> None:
        reservation = _submit_public_booking(client, flow_car)
        intent = _start_online_payment(client, reservation)
        payload = _webhook_payload(
            event_id="evt_flow_dup",
            external_reference=intent.external_reference,
            event_type="payment.succeeded",
        )
        url = reverse("payments_webhook:webhook")

        first = client.post(url, data=payload, content_type="application/json")
        second = client.post(url, data=payload, content_type="application/json")

        assert first.json()["status"] == "ok"
        assert second.json()["status"] == "duplicate"
        assert Payment.objects.filter(reservation=reservation).count() == 1
        assert PaymentProviderEvent.objects.filter(intent=intent).count() == 1

    def test_failed_webhook_leaves_reservation_pending(
        self,
        client,
        flow_car: Car,
    ) -> None:
        reservation = _submit_public_booking(client, flow_car)
        intent = _start_online_payment(client, reservation)

        payload = _webhook_payload(
            event_id="evt_flow_failed",
            external_reference=intent.external_reference,
            event_type="payment.failed",
        )
        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 200

        reservation.refresh_from_db()
        intent.refresh_from_db()
        assert reservation.status == ReservationStatus.PENDING_PAYMENT
        assert intent.status == PaymentIntentStatus.FAILED
        assert Payment.objects.filter(reservation=reservation).count() == 0

    def test_payment_amount_matches_five_day_reservation_total(
        self,
        client,
        flow_car: Car,
    ) -> None:
        reservation = _submit_public_booking(client, flow_car)
        intent = _start_online_payment(client, reservation)

        assert intent.amount == Decimal("500.00")

        client.post(_mock_checkout_url(intent))
        _assert_fulfilled_online_payment(
            reservation,
            intent,
            expected_amount=Decimal("500.00"),
        )
