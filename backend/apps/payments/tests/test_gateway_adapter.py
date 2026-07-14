import json
from decimal import Decimal

import pytest
from django.test import override_settings

from apps.payments.adapters.gateway import (
    GatewayCheckoutRequest,
    MockPaymentGateway,
    get_payment_gateway,
)


@pytest.mark.django_db
class TestMockPaymentGateway:
    def test_create_checkout_session(self) -> None:
        gateway = MockPaymentGateway(base_url="http://testserver")
        session = gateway.create_checkout_session(
            GatewayCheckoutRequest(
                intent_id=42,
                amount=Decimal("500.00"),
                description="Oplata za rezerwacje",
            ),
        )
        assert session.external_reference.startswith("mock_42_")
        assert session.checkout_url.startswith(
            "http://testserver/platnosc/mock/?ref=mock_42_"
        )
        assert "intent=42" in session.checkout_url

    def test_verify_webhook_without_secret(self) -> None:
        gateway = MockPaymentGateway()
        assert gateway.verify_webhook_signature(payload=b"{}", signature=None) is True

    @override_settings(PAYMENT_GATEWAY_WEBHOOK_SECRET="test-secret")
    def test_verify_webhook_with_secret(self) -> None:
        gateway = MockPaymentGateway()
        assert (
            gateway.verify_webhook_signature(
                payload=b"{}",
                signature="test-secret",
            )
            is True
        )
        assert (
            gateway.verify_webhook_signature(
                payload=b"{}",
                signature="wrong",
            )
            is False
        )

    def test_parse_webhook_event(self) -> None:
        gateway = MockPaymentGateway()
        payload = json.dumps(
            {
                "event_type": "payment.succeeded",
                "external_reference": "mock_1_abc123",
                "amount": "500.00",
            },
        ).encode()
        event = gateway.parse_webhook_event(payload)
        assert event.event_type == "payment.succeeded"
        assert event.external_reference == "mock_1_abc123"
        assert event.payload["amount"] == "500.00"


class TestGetPaymentGateway:
    @override_settings(PAYMENT_GATEWAY_PROVIDER="mock")
    def test_returns_mock_by_default(self) -> None:
        gateway = get_payment_gateway()
        assert isinstance(gateway, MockPaymentGateway)

    @override_settings(PAYMENT_GATEWAY_PROVIDER="unknown")
    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Nieznany provider"):
            get_payment_gateway()
