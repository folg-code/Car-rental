from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from django.conf import settings


@dataclass(frozen=True, slots=True)
class GatewayCheckoutRequest:
    intent_id: int
    amount: Decimal
    currency: str = "PLN"
    description: str = ""
    success_url: str = ""
    cancel_url: str = ""


@dataclass(frozen=True, slots=True)
class GatewayCheckoutSession:
    external_reference: str
    checkout_url: str


@dataclass(frozen=True, slots=True)
class GatewayWebhookEvent:
    event_type: str
    external_reference: str
    payload: dict[str, Any]
    event_id: str = ""


class PaymentGatewayClient(Protocol):
    """Kontrakt bramki płatności — implementacje wymienialne (mock, Stripe, …)."""

    def create_checkout_session(
        self,
        request: GatewayCheckoutRequest,
    ) -> GatewayCheckoutSession: ...

    def verify_webhook_signature(
        self,
        *,
        payload: bytes,
        signature: str | None,
    ) -> bool: ...

    def parse_webhook_event(self, payload: bytes) -> GatewayWebhookEvent: ...


class MockPaymentGateway:
    """Mock bramki dla dev/test — deterministyczny kontrakt bez zewnętrznego API."""

    provider_name = "mock"

    def __init__(self, *, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.PAYMENT_GATEWAY_MOCK_BASE_URL).rstrip(
            "/"
        )

    def create_checkout_session(
        self,
        request: GatewayCheckoutRequest,
    ) -> GatewayCheckoutSession:
        external_reference = f"mock_{request.intent_id}_{uuid.uuid4().hex[:12]}"
        checkout_url = (
            f"{self._base_url}/platnosc/mock/"
            f"?ref={external_reference}&intent={request.intent_id}"
        )
        return GatewayCheckoutSession(
            external_reference=external_reference,
            checkout_url=checkout_url,
        )

    def verify_webhook_signature(
        self,
        *,
        payload: bytes,
        signature: str | None,
    ) -> bool:
        del payload
        secret = settings.PAYMENT_GATEWAY_WEBHOOK_SECRET
        if not secret:
            return True
        return signature == secret

    def parse_webhook_event(self, payload: bytes) -> GatewayWebhookEvent:
        data = json.loads(payload.decode("utf-8"))
        event_id = str(data.get("id") or data.get("event_id") or "")
        return GatewayWebhookEvent(
            event_type=str(data["event_type"]),
            external_reference=str(data["external_reference"]),
            payload=data,
            event_id=event_id,
        )


def get_payment_gateway() -> PaymentGatewayClient:
    provider = settings.PAYMENT_GATEWAY_PROVIDER
    if provider == "mock":
        return MockPaymentGateway()
    msg = f"Nieznany provider bramki platnosci: {provider}"
    raise ValueError(msg)
