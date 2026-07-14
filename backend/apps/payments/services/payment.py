from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Rental, Reservation
from apps.payments.models import (
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentMethod,
    PaymentType,
)


class PaymentService:
    @staticmethod
    def _get_rental(rental_id: int) -> Rental:
        rental = (
            Rental.objects.select_related("reservation").filter(pk=rental_id).first()
        )
        if rental is None:
            raise ValidationError(f"Wynajem {rental_id} nie istnieje.")
        return rental

    @staticmethod
    def _get_reservation(reservation_id: int) -> Reservation:
        reservation = Reservation.objects.filter(pk=reservation_id).first()
        if reservation is None:
            raise ValidationError(f"Rezerwacja {reservation_id} nie istnieje.")
        return reservation

    @staticmethod
    def _get_intent(intent_id: int | None) -> PaymentIntent | None:
        if intent_id is None:
            return None
        intent = PaymentIntent.objects.filter(pk=intent_id).first()
        if intent is None:
            raise ValidationError("Nie znaleziono intencji platnosci.")
        return intent

    @staticmethod
    def _existing_payment_for_intent(intent_id: int | None) -> Payment | None:
        if intent_id is None:
            return None
        return Payment.objects.filter(intent_id=intent_id).first()

    @staticmethod
    @transaction.atomic
    def record_reservation_payment(
        *,
        reservation_id: int,
        amount: Decimal,
        payment_type: str,
        method: str,
        paid_at: datetime | None = None,
        notes: str = "",
        recorded_by_id: int | None = None,
        intent_id: int | None = None,
    ) -> Payment:
        if payment_type not in PaymentType.values:
            msg = f"Nieprawidlowy typ platnosci: {payment_type}"
            raise ValueError(msg)
        if method not in PaymentMethod.values:
            msg = f"Nieprawidlowa metoda platnosci: {method}"
            raise ValueError(msg)

        existing = PaymentService._existing_payment_for_intent(intent_id)
        if existing is not None:
            return existing

        amount = amount.quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValidationError("Kwota platnosci musi byc wieksza od zera.")

        reservation = PaymentService._get_reservation(reservation_id)
        intent = PaymentService._get_intent(intent_id)
        if intent is not None and intent.reservation_id != reservation_id:
            raise ValidationError("Intencja nie dotyczy tej rezerwacji.")

        payment = Payment(
            rental=None,
            reservation=reservation,
            intent=intent,
            payment_type=payment_type,
            method=method,
            amount=amount,
            paid_at=paid_at or timezone.now(),
            notes=notes,
            recorded_by_id=recorded_by_id,
        )
        payment.save()
        return payment

    @staticmethod
    @transaction.atomic
    def record_payment(
        *,
        rental_id: int,
        amount: Decimal,
        payment_type: str,
        method: str,
        paid_at: datetime | None = None,
        notes: str = "",
        recorded_by_id: int | None = None,
        intent_id: int | None = None,
    ) -> Payment:
        if payment_type not in PaymentType.values:
            msg = f"Nieprawidlowy typ platnosci: {payment_type}"
            raise ValueError(msg)
        if method not in PaymentMethod.values:
            msg = f"Nieprawidlowa metoda platnosci: {method}"
            raise ValueError(msg)

        amount = amount.quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValidationError("Kwota platnosci musi byc wieksza od zera.")

        existing = PaymentService._existing_payment_for_intent(intent_id)
        if existing is not None:
            return existing

        rental = PaymentService._get_rental(rental_id)
        intent = PaymentService._get_intent(intent_id)
        if (
            intent is not None
            and intent.rental_id is not None
            and intent.rental_id != rental_id
        ):
            raise ValidationError("Intencja nie dotyczy tego wynajmu.")

        payment = Payment(
            rental=rental,
            reservation_id=rental.reservation_id,
            intent=intent,
            payment_type=payment_type,
            method=method,
            amount=amount,
            paid_at=paid_at or timezone.now(),
            notes=notes,
            recorded_by_id=recorded_by_id,
        )
        payment.save()

        if intent is not None and intent.status == PaymentIntentStatus.PENDING:
            intent.status = PaymentIntentStatus.SUCCEEDED
            intent.save(update_fields=["status", "updated_at"])

        if rental_id is not None:
            from apps.payments.services.settlement import SettlementService

            SettlementService.try_close_rental_if_settled(rental_id)

        return payment

    @staticmethod
    def record_deposit(
        *,
        rental_id: int,
        amount: Decimal | None = None,
        method: str = PaymentMethod.CASH,
        paid_at: datetime | None = None,
        notes: str = "",
        recorded_by_id: int | None = None,
    ) -> Payment:
        rental = PaymentService._get_rental(rental_id)
        if amount is None:
            amount = rental.deposit_amount
        if amount <= 0:
            raise ValidationError(
                "Kaucja dla tego wynajmu wynosi zero — podaj kwote recznie."
            )
        return PaymentService.record_payment(
            rental_id=rental_id,
            amount=amount,
            payment_type=PaymentType.DEPOSIT,
            method=method,
            paid_at=paid_at,
            notes=notes or "Kaucja zwrotna",
            recorded_by_id=recorded_by_id,
        )

    @staticmethod
    def record_rental_fee(
        *,
        rental_id: int,
        amount: Decimal,
        method: str = PaymentMethod.CASH,
        paid_at: datetime | None = None,
        notes: str = "",
        recorded_by_id: int | None = None,
    ) -> Payment:
        return PaymentService.record_payment(
            rental_id=rental_id,
            amount=amount,
            payment_type=PaymentType.RENTAL_FEE,
            method=method,
            paid_at=paid_at,
            notes=notes,
            recorded_by_id=recorded_by_id,
        )

    @staticmethod
    @transaction.atomic
    def refund_deposit(
        *,
        rental_id: int,
        amount: Decimal | None = None,
        method: str = PaymentMethod.CASH,
        paid_at: datetime | None = None,
        notes: str = "",
        recorded_by_id: int | None = None,
    ) -> Payment:
        from apps.payments.selectors.payment import get_rental_deposit_balance

        balance = get_rental_deposit_balance(rental_id)
        if balance <= 0:
            raise ValidationError("Brak kaucji do zwrotu dla tego wynajmu.")

        refund_amount = (amount or balance).quantize(Decimal("0.01"))
        if refund_amount <= 0:
            raise ValidationError("Kwota zwrotu musi byc wieksza od zera.")
        if refund_amount > balance:
            raise ValidationError(
                f"Kwota zwrotu ({refund_amount}) przekracza saldo kaucji ({balance})."
            )

        return PaymentService.record_payment(
            rental_id=rental_id,
            amount=refund_amount,
            payment_type=PaymentType.REFUND,
            method=method,
            paid_at=paid_at,
            notes=notes or "Zwrot kaucji",
            recorded_by_id=recorded_by_id,
        )
