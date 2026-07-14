from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.bookings.models import ReservationStatus
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.payments.adapters.gateway import GatewayCheckoutSession
from apps.payments.models import PaymentIntent, PaymentIntentStatus
from apps.payments.services.gateway import PaymentGatewayService, WebhookHandleResult
from apps.website.selectors.public_booking import get_public_reservation_summary


class PublicPaymentOrchestrator:
    """Orkiestracja platnosci online po publicznej rezerwacji (task 9.5)."""

    @staticmethod
    def start_online_payment(
        reservation_id: int,
        *,
        success_url: str,
        cancel_url: str,
    ) -> GatewayCheckoutSession:
        reservation = get_public_reservation_summary(reservation_id)
        if reservation is None:
            raise ValidationError("Nie znaleziono rezerwacji.")
        if reservation.status != ReservationStatus.PENDING_PAYMENT:
            raise ValidationError("Rezerwacja nie oczekuje na platnosc.")

        total = PriceSnapshotService.reservation_total(reservation)
        if total <= 0:
            raise ValidationError("Kwota do zaplaty musi byc wieksza od zera.")

        intent = PaymentIntent.objects.filter(
            reservation_id=reservation_id,
            status=PaymentIntentStatus.PENDING,
        ).first()
        if intent is None:
            intent = PaymentGatewayService.create_intent(
                reservation_id=reservation_id,
                amount=total,
            )

        return PaymentGatewayService.initiate_checkout(
            intent_id=intent.pk,
            success_url=success_url,
            cancel_url=cancel_url,
            description=f"Rezerwacja #{reservation_id}",
        )

    @staticmethod
    def complete_mock_payment(*, external_reference: str) -> WebhookHandleResult:
        payload = json.dumps(
            {
                "id": f"mock_evt_{external_reference}",
                "event_type": "payment.succeeded",
                "external_reference": external_reference,
            },
        ).encode()
        return PaymentGatewayService.handle_webhook(payload=payload)

    @staticmethod
    def build_success_url(reservation_id: int) -> str:
        return reverse(
            "website:payment_success",
            kwargs={"reservation_id": reservation_id},
        )

    @staticmethod
    def build_cancel_url(reservation_id: int) -> str:
        return reverse(
            "website:booking_confirmation_by_id",
            kwargs={"reservation_id": reservation_id},
        )
