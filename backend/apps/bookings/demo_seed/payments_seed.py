"""Platnosci i intencje bramki dla scenariuszy demo."""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from apps.bookings.demo_seed.catalog import demo_note
from apps.bookings.models import Rental, Reservation, ReservationStatus
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.bookings.services.reservation import ReservationService
from apps.payments.models import Payment, PaymentMethod, PaymentType, RentalCharge
from apps.payments.services.gateway import PaymentGatewayService
from apps.payments.services.payment import PaymentService


def _payment_marker(scenario_key: str, suffix: str) -> str:
    return demo_note(f"payment:{scenario_key}:{suffix}")


def _has_payment(marker: str) -> bool:
    return Payment.objects.filter(notes=marker).exists()


def _reservation_total(reservation: Reservation) -> Decimal:
    if reservation.price_lines.exists():
        return PriceSnapshotService.reservation_total(reservation)
    return Decimal("0.01")


def apply_payment_profile(
    *,
    scenario_key: str,
    reservation: Reservation,
    rental: Rental | None,
    profile: str,
    panel_user_id: int | None = None,
) -> int:
    """Zastosuj profil platnosci; zwraca liczbe nowo utworzonych platnosci."""
    if not profile:
        return 0

    if profile == "unpaid":
        return 0

    if profile == "online_pending":
        return _seed_online_pending(scenario_key, reservation)

    if profile == "online_succeeded":
        return _seed_online_succeeded(scenario_key, reservation, panel_user_id)

    if rental is None:
        return 0

    if profile == "deposit_only":
        return _seed_deposit_only(scenario_key, rental, panel_user_id)

    if profile == "partial":
        return _seed_partial_rental_fee(scenario_key, rental, panel_user_id)

    if profile == "settled":
        return _seed_settled(scenario_key, rental, panel_user_id)

    return 0


def _seed_online_pending(scenario_key: str, reservation: Reservation) -> int:
    if reservation.payment_intents.filter(amount__gt=0).exists():
        return 0
    total = _reservation_total(reservation)
    PaymentGatewayService.create_intent(
        reservation_id=reservation.pk,
        amount=total,
        payment_type=PaymentType.RENTAL_FEE,
    )
    return 0


def _seed_online_succeeded(
    scenario_key: str,
    reservation: Reservation,
    panel_user_id: int | None,
) -> int:
    marker = _payment_marker(scenario_key, "online")
    if _has_payment(marker):
        return 0

    total = _reservation_total(reservation)
    intent = PaymentGatewayService.create_intent(
        reservation_id=reservation.pk,
        amount=total,
        payment_type=PaymentType.RENTAL_FEE,
    )
    PaymentService.record_reservation_payment(
        reservation_id=reservation.pk,
        amount=total,
        payment_type=PaymentType.RENTAL_FEE,
        method=PaymentMethod.ONLINE_GATEWAY,
        notes=marker,
        recorded_by_id=panel_user_id,
        intent_id=intent.pk,
    )
    if reservation.status == ReservationStatus.PENDING_PAYMENT:
        ReservationService.confirm(reservation)
    return 1


def _seed_deposit_only(
    scenario_key: str,
    rental: Rental,
    panel_user_id: int | None,
) -> int:
    marker = _payment_marker(scenario_key, "deposit")
    if _has_payment(marker):
        return 0
    PaymentService.record_deposit(
        rental_id=rental.pk,
        method=PaymentMethod.CARD,
        notes=marker,
        recorded_by_id=panel_user_id,
    )
    return 1


def _seed_partial_rental_fee(
    scenario_key: str,
    rental: Rental,
    panel_user_id: int | None,
) -> int:
    marker = _payment_marker(scenario_key, "partial")
    if _has_payment(marker):
        return 0
    total = _reservation_total(rental.reservation)
    amount = (total / 2).quantize(Decimal("0.01"))
    if amount <= 0:
        return 0
    PaymentService.record_payment(
        rental_id=rental.pk,
        amount=amount,
        payment_type=PaymentType.RENTAL_FEE,
        method=PaymentMethod.BANK_TRANSFER,
        notes=marker,
        recorded_by_id=panel_user_id,
    )
    return 1


def _seed_settled(
    scenario_key: str,
    rental: Rental,
    panel_user_id: int | None,
) -> int:
    created = 0
    reservation = rental.reservation
    total = _reservation_total(reservation)

    fee_marker = _payment_marker(scenario_key, "fee")
    if not _has_payment(fee_marker) and total > 0:
        PaymentService.record_payment(
            rental_id=rental.pk,
            amount=total,
            payment_type=PaymentType.RENTAL_FEE,
            method=PaymentMethod.CASH,
            notes=fee_marker,
            recorded_by_id=panel_user_id,
        )
        created += 1

    deposit_marker = _payment_marker(scenario_key, "deposit")
    if not _has_payment(deposit_marker) and rental.deposit_amount > 0:
        PaymentService.record_deposit(
            rental_id=rental.pk,
            method=PaymentMethod.CARD,
            notes=deposit_marker,
            recorded_by_id=panel_user_id,
        )
        created += 1

    for charge in RentalCharge.objects.filter(rental_id=rental.pk):
        charge_marker = _payment_marker(scenario_key, f"charge:{charge.pk}")
        if _has_payment(charge_marker):
            continue
        PaymentService.record_payment(
            rental_id=rental.pk,
            amount=charge.amount,
            payment_type=charge.payment_type,
            method=PaymentMethod.CASH,
            notes=charge_marker,
            recorded_by_id=panel_user_id,
        )
        created += 1

    return created


def seed_demo_invoice(
    *,
    rental: Rental,
    scenario_key: str,
) -> bool:
    from apps.documents.selectors.invoice_data import rental_has_active_invoice
    from apps.documents.services.invoice import InvoiceService

    if rental_has_active_invoice(rental.pk):
        return False
    issue = timezone.localdate()
    InvoiceService.create_from_rental(
        rental.pk,
        issue_date=issue,
        notes=demo_note(f"invoice:{scenario_key}"),
    )
    return True
