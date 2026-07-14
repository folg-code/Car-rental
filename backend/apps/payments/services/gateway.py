from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bookings.models import Rental, Reservation
from apps.payments.adapters.gateway import (
    GatewayCheckoutRequest,
    GatewayCheckoutSession,
    PaymentGatewayClient,
    get_payment_gateway,
)
from apps.payments.models import (
    PaymentIntent,
    PaymentIntentStatus,
    PaymentProviderEvent,
    PaymentType,
)

SUCCESS_EVENT_TYPES = frozenset(
    {
        "payment.succeeded",
        "checkout.session.completed",
    }
)
FAILURE_EVENT_TYPES = frozenset(
    {
        "payment.failed",
        "payment.cancelled",
    }
)


@dataclass(frozen=True, slots=True)
class WebhookHandleResult:
    duplicate: bool
    intent: PaymentIntent | None
    provider_event: PaymentProviderEvent | None


class PaymentGatewayService:
    @staticmethod
    def _get_reservation(reservation_id: int) -> Reservation:
        reservation = Reservation.objects.filter(pk=reservation_id).first()
        if reservation is None:
            raise ValidationError(f"Rezerwacja {reservation_id} nie istnieje.")
        return reservation

    @staticmethod
    def _get_rental(rental_id: int) -> Rental:
        rental = Rental.objects.filter(pk=rental_id).first()
        if rental is None:
            raise ValidationError(f"Wynajem {rental_id} nie istnieje.")
        return rental

    @staticmethod
    @transaction.atomic
    def create_intent(
        *,
        amount: Decimal,
        payment_type: str = PaymentType.RENTAL_FEE,
        reservation_id: int | None = None,
        rental_id: int | None = None,
    ) -> PaymentIntent:
        if payment_type not in PaymentType.values:
            msg = f"Nieprawidlowy typ platnosci: {payment_type}"
            raise ValueError(msg)

        amount = amount.quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValidationError("Kwota intencji musi byc wieksza od zera.")

        if (reservation_id is None) == (rental_id is None):
            raise ValidationError("Podaj reservation_id lub rental_id.")

        reservation = None
        rental = None
        if reservation_id is not None:
            reservation = PaymentGatewayService._get_reservation(reservation_id)
        if rental_id is not None:
            rental = PaymentGatewayService._get_rental(rental_id)

        return PaymentIntent.objects.create(
            reservation=reservation,
            rental=rental,
            amount=amount,
            payment_type=payment_type,
            status=PaymentIntentStatus.PENDING,
        )

    @staticmethod
    @transaction.atomic
    def initiate_checkout(
        *,
        intent_id: int,
        success_url: str,
        cancel_url: str,
        description: str = "",
        gateway: PaymentGatewayClient | None = None,
    ) -> GatewayCheckoutSession:
        intent = PaymentIntent.objects.select_for_update().filter(pk=intent_id).first()
        if intent is None:
            raise ValidationError("Nie znaleziono intencji platnosci.")
        if intent.status != PaymentIntentStatus.PENDING:
            raise ValidationError("Intencja nie oczekuje na platnosc.")

        client = gateway or get_payment_gateway()
        session = client.create_checkout_session(
            GatewayCheckoutRequest(
                intent_id=intent.pk,
                amount=intent.amount,
                description=description,
                success_url=success_url,
                cancel_url=cancel_url,
            ),
        )
        intent.external_reference = session.external_reference
        intent.save(update_fields=["external_reference", "updated_at"])
        return session

    @staticmethod
    def _provider_event_id(
        *,
        event_type: str,
        external_reference: str,
        payload: dict[str, Any],
        event_id: str = "",
    ) -> str:
        if event_id:
            return event_id
        for key in ("id", "event_id", "provider_event_id"):
            value = payload.get(key)
            if value:
                return str(value)
        raw = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(
            f"{event_type}:{external_reference}:{raw}".encode(),
        ).hexdigest()
        return f"hash_{digest[:32]}"

    @staticmethod
    @transaction.atomic
    def handle_webhook(
        *,
        payload: bytes,
        signature: str | None = None,
        gateway: PaymentGatewayClient | None = None,
    ) -> WebhookHandleResult:
        client = gateway or get_payment_gateway()
        if not client.verify_webhook_signature(payload=payload, signature=signature):
            raise ValidationError("Nieprawidlowy podpis webhooka bramki.")

        event = client.parse_webhook_event(payload)
        provider_event_id = PaymentGatewayService._provider_event_id(
            event_type=event.event_type,
            external_reference=event.external_reference,
            payload=event.payload,
            event_id=event.event_id,
        )

        existing = (
            PaymentProviderEvent.objects.filter(provider_event_id=provider_event_id)
            .select_related("intent")
            .first()
        )
        if existing is not None:
            return WebhookHandleResult(
                duplicate=True,
                intent=existing.intent,
                provider_event=existing,
            )

        intent = (
            PaymentIntent.objects.select_for_update()
            .filter(external_reference=event.external_reference)
            .first()
        )
        if intent is None:
            raise ValidationError(
                f"Nie znaleziono intencji dla referencji {event.external_reference}."
            )

        provider_event = PaymentProviderEvent.objects.create(
            intent=intent,
            provider_event_id=provider_event_id,
            event_type=event.event_type,
            payload=payload.decode("utf-8"),
        )

        if event.event_type in SUCCESS_EVENT_TYPES:
            PaymentGatewayService._mark_intent_succeeded(intent)
        elif event.event_type in FAILURE_EVENT_TYPES:
            PaymentGatewayService._mark_intent_failed(intent)

        return WebhookHandleResult(
            duplicate=False,
            intent=intent,
            provider_event=provider_event,
        )

    @staticmethod
    def _mark_intent_succeeded(intent: PaymentIntent) -> None:
        if intent.status == PaymentIntentStatus.PENDING:
            intent.status = PaymentIntentStatus.SUCCEEDED
            intent.save(update_fields=["status", "updated_at"])

    @staticmethod
    def _mark_intent_failed(intent: PaymentIntent) -> None:
        if intent.status == PaymentIntentStatus.PENDING:
            intent.status = PaymentIntentStatus.FAILED
            intent.save(update_fields=["status", "updated_at"])
