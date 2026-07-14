from datetime import datetime
from decimal import Decimal

from django.db.models import QuerySet, Sum

from apps.bookings.models import Rental
from apps.bookings.services.price_snapshot import PriceSnapshotService
from apps.payments.models import (
    REVENUE_PAYMENT_TYPES,
    Payment,
    PaymentType,
    RentalCharge,
)


def list_payments(
    *,
    rental_id: int | None = None,
    limit: int | None = None,
) -> QuerySet[Payment]:
    qs = Payment.objects.select_related(
        "rental",
        "rental__reservation",
        "rental__reservation__customer",
        "rental__reservation__car",
        "recorded_by",
    ).order_by("-paid_at", "-pk")
    if rental_id is not None:
        qs = qs.filter(rental_id=rental_id)
    if limit is not None:
        qs = qs[:limit]
    return qs


def _sum_by_type(rental_id: int, payment_type: str) -> Decimal:
    total = Payment.objects.filter(
        rental_id=rental_id,
        payment_type=payment_type,
    ).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0")


def get_rental_deposit_balance(rental_id: int) -> Decimal:
    """Saldo kaucji = wplaty deposit - zwroty refund."""
    deposits = _sum_by_type(rental_id, PaymentType.DEPOSIT)
    refunds = _sum_by_type(rental_id, PaymentType.REFUND)
    return (deposits - refunds).quantize(Decimal("0.01"))


def get_rental_revenue_total(rental_id: int) -> Decimal:
    """Przychod operacyjny — bez kaucji i zwrotow."""
    total = Payment.objects.filter(
        rental_id=rental_id,
        payment_type__in=REVENUE_PAYMENT_TYPES,
    ).aggregate(total=Sum("amount"))["total"]
    return (total or Decimal("0")).quantize(Decimal("0.01"))


def get_revenue_total_in_period(
    start_at: datetime,
    end_at: datetime,
) -> Decimal:
    """Suma platnosci przychodowych w przedziale [start_at, end_at] (paid_at)."""
    total = Payment.objects.filter(
        payment_type__in=REVENUE_PAYMENT_TYPES,
        paid_at__gte=start_at,
        paid_at__lte=end_at,
    ).aggregate(total=Sum("amount"))["total"]
    return (total or Decimal("0")).quantize(Decimal("0.01"))


def _sum_charges(rental_id: int, payment_type: str) -> Decimal:
    total = RentalCharge.objects.filter(
        rental_id=rental_id,
        payment_type=payment_type,
    ).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0")


def _charge_due(accrued: Decimal, paid: Decimal) -> Decimal:
    due = (accrued - paid).quantize(Decimal("0.01"))
    if due < 0:
        return Decimal("0")
    return due


def get_rental_payment_summary(rental_id: int) -> dict[str, Decimal]:
    rental = Rental.objects.select_related("reservation").filter(pk=rental_id).first()
    if rental is None:
        return {}

    reservation = rental.reservation
    price_total = PriceSnapshotService.reservation_total(reservation)
    rental_fees = _sum_by_type(rental_id, PaymentType.RENTAL_FEE)
    extra_charges = _sum_by_type(rental_id, PaymentType.EXTRA_CHARGE)
    damage_charges = _sum_by_type(rental_id, PaymentType.DAMAGE_CHARGE)
    extra_accrued = _sum_charges(rental_id, PaymentType.EXTRA_CHARGE)
    damage_accrued = _sum_charges(rental_id, PaymentType.DAMAGE_CHARGE)
    deposits = _sum_by_type(rental_id, PaymentType.DEPOSIT)
    refunds = _sum_by_type(rental_id, PaymentType.REFUND)
    revenue = get_rental_revenue_total(rental_id)
    deposit_balance = (deposits - refunds).quantize(Decimal("0.01"))
    fees_due = (price_total - rental_fees).quantize(Decimal("0.01"))
    if fees_due < 0:
        fees_due = Decimal("0")
    extra_charges_due = _charge_due(extra_accrued, extra_charges)
    damage_charges_due = _charge_due(damage_accrued, damage_charges)
    total_due = (fees_due + extra_charges_due + damage_charges_due).quantize(
        Decimal("0.01")
    )

    return {
        "price_total": price_total,
        "rental_fees_paid": rental_fees,
        "extra_charges_paid": extra_charges,
        "extra_charges_accrued": extra_accrued,
        "extra_charges_due": extra_charges_due,
        "damage_charges_paid": damage_charges,
        "damage_charges_accrued": damage_accrued,
        "damage_charges_due": damage_charges_due,
        "deposits_paid": deposits,
        "refunds_paid": refunds,
        "deposit_balance": deposit_balance,
        "revenue_total": revenue,
        "rental_fee_due": fees_due,
        "total_due": total_due,
        "deposit_expected": rental.deposit_amount,
    }


def get_rental_balance_due(rental_id: int) -> Decimal:
    """Suma naleznosci: wynajem + doplaty + szkody minus wplaty."""
    summary = get_rental_payment_summary(rental_id)
    if not summary:
        return Decimal("0")
    return summary["total_due"]


def rental_has_balance_due(rental_id: int) -> bool:
    return get_rental_balance_due(rental_id) > Decimal("0")
