import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.bookings.models import Customer, ReservationStatus
from apps.bookings.services.reservation import ReservationService
from apps.fleet.models import Car, CarCategory, CarStatus
from apps.payments.adapters.gateway import MockPaymentGateway
from apps.payments.models import PaymentIntentStatus, PaymentProviderEvent, PaymentType
from apps.payments.services.gateway import PaymentGatewayService
from apps.pricing.models import DailyRate, PriceList


@pytest.fixture
def category(db) -> CarCategory:
    return CarCategory.objects.create(
        name="Kompakt",
        slug="kompakt-gateway-svc",
        deposit=Decimal("1000.00"),
    )


@pytest.fixture(autouse=True)
def default_price_list(db, category: CarCategory) -> PriceList:
    price_list = PriceList.objects.create(
        name="Cennik gateway svc",
        slug="test-gateway-svc",
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
        email="jan@gateway-svc.test",
    )
    car = Car.objects.create(
        category=category,
        registration_number="KR1GWS01",
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


def _webhook_payload(
    *,
    event_type: str,
    external_reference: str,
    event_id: str = "evt_test_1",
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "event_type": event_type,
            "external_reference": external_reference,
        },
    ).encode()


@pytest.mark.django_db
class TestPaymentGatewayService:
    def test_create_intent_for_reservation(self, reservation) -> None:
        intent = PaymentGatewayService.create_intent(
            reservation_id=reservation.pk,
            amount=Decimal("800.00"),
        )
        assert intent.reservation_id == reservation.pk
        assert intent.status == PaymentIntentStatus.PENDING
        assert intent.amount == Decimal("800.00")

    def test_create_intent_requires_single_target(self) -> None:
        with pytest.raises(ValidationError, match="reservation_id lub rental_id"):
            PaymentGatewayService.create_intent(amount=Decimal("100.00"))

    def test_initiate_checkout_sets_external_reference(self, reservation) -> None:
        intent = PaymentGatewayService.create_intent(
            reservation_id=reservation.pk,
            amount=Decimal("500.00"),
        )
        gateway = MockPaymentGateway(base_url="http://testserver")
        session = PaymentGatewayService.initiate_checkout(
            intent_id=intent.pk,
            success_url="http://testserver/sukces/",
            cancel_url="http://testserver/anuluj/",
            gateway=gateway,
        )
        intent.refresh_from_db()
        assert session.external_reference == intent.external_reference
        assert intent.external_reference.startswith(f"mock_{intent.pk}_")

    def test_initiate_checkout_rejects_non_pending(self, reservation) -> None:
        intent = PaymentGatewayService.create_intent(
            reservation_id=reservation.pk,
            amount=Decimal("500.00"),
        )
        intent.status = PaymentIntentStatus.SUCCEEDED
        intent.save(update_fields=["status", "updated_at"])
        with pytest.raises(ValidationError, match="nie oczekuje"):
            PaymentGatewayService.initiate_checkout(
                intent_id=intent.pk,
                success_url="/sukces/",
                cancel_url="/anuluj/",
                gateway=MockPaymentGateway(base_url="http://testserver"),
            )

    def test_handle_webhook_success(self, reservation) -> None:
        intent = PaymentGatewayService.create_intent(
            reservation_id=reservation.pk,
            amount=Decimal("500.00"),
            payment_type=PaymentType.RENTAL_FEE,
        )
        gateway = MockPaymentGateway(base_url="http://testserver")
        session = PaymentGatewayService.initiate_checkout(
            intent_id=intent.pk,
            success_url="/sukces/",
            cancel_url="/anuluj/",
            gateway=gateway,
        )
        payload = _webhook_payload(
            event_type="payment.succeeded",
            external_reference=session.external_reference,
        )
        result = PaymentGatewayService.handle_webhook(payload=payload, gateway=gateway)
        intent.refresh_from_db()
        assert result.duplicate is False
        assert intent.status == PaymentIntentStatus.SUCCEEDED
        assert PaymentProviderEvent.objects.filter(intent=intent).count() == 1

    def test_handle_webhook_failure(self, reservation) -> None:
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
        payload = _webhook_payload(
            event_type="payment.failed",
            external_reference=session.external_reference,
            event_id="evt_failed_1",
        )
        PaymentGatewayService.handle_webhook(payload=payload, gateway=gateway)
        intent.refresh_from_db()
        assert intent.status == PaymentIntentStatus.FAILED

    def test_handle_webhook_idempotent(self, reservation) -> None:
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
        payload = _webhook_payload(
            event_type="payment.succeeded",
            external_reference=session.external_reference,
            event_id="evt_dup_1",
        )
        first = PaymentGatewayService.handle_webhook(payload=payload, gateway=gateway)
        second = PaymentGatewayService.handle_webhook(payload=payload, gateway=gateway)
        intent.refresh_from_db()
        assert first.duplicate is False
        assert second.duplicate is True
        assert PaymentProviderEvent.objects.filter(intent=intent).count() == 1

    def test_handle_webhook_invalid_signature(self, reservation) -> None:
        del reservation

        class RejectingGateway(MockPaymentGateway):
            def verify_webhook_signature(
                self, *, payload: bytes, signature: str | None
            ) -> bool:
                return False

        with pytest.raises(ValidationError, match="podpis webhooka"):
            PaymentGatewayService.handle_webhook(
                payload=b"{}",
                gateway=RejectingGateway(base_url="http://testserver"),
            )
