import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.adapters.gateway import MockPaymentGateway
from apps.payments.models import PaymentIntentStatus, PaymentProviderEvent
from apps.payments.services.gateway import PaymentGatewayService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-webhook",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik webhook",
        slug="test-webhook",
        is_default=True,
        is_active=True,
    )
    DailyRate.objects.create(
        price_list=price_list,
        category=category,
        amount=Decimal("200.00"),
    )
    return price_list


@pytest.fixture
def reservation(db, category: CarCategory):
    customer = Customer.objects.create(
        first_name="Jan",
        last_name="Kowalski",
        email="jan@webhook.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1WHK01",
        make="Toyota",
        model="Yaris",
        year=2022,
        status=CarStatus.ACTIVE,
    )
    start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    end = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    return ReservationService.create(
        customer_id=customer.pk,
        car_id=car.pk,
        start_at=start,
        end_at=end,
        status=ReservationStatus.PENDING_PAYMENT,
    )


def _start_checkout(reservation) -> str:
    intent = PaymentGatewayService.create_intent(
        reservation_id=reservation.pk,
        amount=Decimal("500.00"),
    )
    gateway = MockPaymentGateway(base_url="http://testserver")
    session = PaymentGatewayService.initiate_checkout(
        intent_id=intent.pk,
        success_url="/sukces/",
        cancel_url="/anuluj/",
        gateway=gateway,
    )
    return session.external_reference


@pytest.mark.django_db
class TestPaymentWebhookView:
    def test_webhook_success_without_login(self, client, reservation) -> None:
        external_reference = _start_checkout(reservation)
        payload = json.dumps(
            {
                "id": "evt_view_1",
                "event_type": "payment.succeeded",
                "external_reference": external_reference,
            },
        )
        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["intent_id"] is not None

    def test_webhook_rejects_get(self, client) -> None:
        response = client.get(reverse("payments_webhook:webhook"))
        assert response.status_code == 405

    @override_settings(PAYMENT_GATEWAY_WEBHOOK_SECRET="test-secret")
    def test_webhook_requires_signature_when_secret_set(
        self,
        client,
        reservation,
    ) -> None:
        external_reference = _start_checkout(reservation)
        payload = json.dumps(
            {
                "id": "evt_view_2",
                "event_type": "payment.succeeded",
                "external_reference": external_reference,
            },
        )
        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 400

        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYMENT_SIGNATURE="test-secret",
        )
        assert response.status_code == 200

    def test_webhook_idempotent_response(self, client, reservation) -> None:
        external_reference = _start_checkout(reservation)
        payload = json.dumps(
            {
                "id": "evt_view_dup",
                "event_type": "payment.succeeded",
                "external_reference": external_reference,
            },
        )
        url = reverse("payments_webhook:webhook")
        first = client.post(url, data=payload, content_type="application/json")
        second = client.post(url, data=payload, content_type="application/json")
        assert first.json()["status"] == "ok"
        assert second.json()["status"] == "duplicate"
        assert PaymentProviderEvent.objects.count() == 1

    def test_webhook_unknown_reference_returns_400(self, client) -> None:
        payload = json.dumps(
            {
                "id": "evt_view_3",
                "event_type": "payment.succeeded",
                "external_reference": "mock_missing_ref",
            },
        )
        response = client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_webhook_marks_intent_succeeded(self, client, reservation) -> None:
        external_reference = _start_checkout(reservation)
        payload = json.dumps(
            {
                "id": "evt_view_4",
                "event_type": "payment.succeeded",
                "external_reference": external_reference,
            },
        )
        client.post(
            reverse("payments_webhook:webhook"),
            data=payload,
            content_type="application/json",
        )
        intent = PaymentProviderEvent.objects.get(
            provider_event_id="evt_view_4",
        ).intent
        assert intent.status == PaymentIntentStatus.SUCCEEDED
