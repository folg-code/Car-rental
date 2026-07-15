from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db.models import Q, Sum

from apps.bookings.models import BLOCKING_RENTAL_STATUSES, PriceLine, Rental
from apps.payments.models import Payment, PaymentType, RentalCharge


def count_unpaid_rentals() -> int:
    """Liczba wynajmow operacyjnych z niesplacona naleznoscia za wynajem."""
    rentals = list(
        Rental.objects.filter(status__in=BLOCKING_RENTAL_STATUSES).values(
            "pk",
            "reservation_id",
        )
    )
    balances = _get_balance_due_by_rental_rows(rentals)
    return sum(1 for due in balances.values() if due > Decimal("0"))


def list_unpaid_rentals(*, limit: int = 50) -> list[Rental]:
    """Wynajmy z saldem do zaplaty — do kolejki na pulpicie (task 8.6)."""
    rentals = list(
        Rental.objects.filter(status__in=BLOCKING_RENTAL_STATUSES)
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
        )
        .order_by("-scheduled_start_at")
    )
    balances = _get_balance_due_by_rental_rows(
        [
            {"pk": rental.pk, "reservation_id": rental.reservation_id}
            for rental in rentals
        ]
    )
    return [
        rental
        for rental in rentals
        if balances.get(rental.pk, Decimal("0")) > Decimal("0")
    ][:limit]


def _get_balance_due_by_rental_rows(
    rental_rows: list[dict[str, int]],
) -> dict[int, Decimal]:
    rental_ids = [row["pk"] for row in rental_rows]
    reservation_ids = [row["reservation_id"] for row in rental_rows]
    rental_by_reservation_id = {row["reservation_id"]: row["pk"] for row in rental_rows}

    price_totals = _sum_price_lines_by_reservation(reservation_ids)
    payment_totals = _sum_payments_by_rental(
        rental_ids=rental_ids,
        reservation_to_rental=rental_by_reservation_id,
    )
    charge_totals = _sum_charges_by_rental(rental_ids)

    balances: dict[int, Decimal] = {}
    for row in rental_rows:
        rental_id = row["pk"]
        reservation_id = row["reservation_id"]
        rental_fees_paid = payment_totals[rental_id][PaymentType.RENTAL_FEE]
        extra_paid = payment_totals[rental_id][PaymentType.EXTRA_CHARGE]
        damage_paid = payment_totals[rental_id][PaymentType.DAMAGE_CHARGE]
        price_total = price_totals[reservation_id]
        extra_accrued = charge_totals[rental_id][PaymentType.EXTRA_CHARGE]
        damage_accrued = charge_totals[rental_id][PaymentType.DAMAGE_CHARGE]

        rental_fee_due = _positive_due(price_total, rental_fees_paid)
        extra_due = _positive_due(extra_accrued, extra_paid)
        damage_due = _positive_due(damage_accrued, damage_paid)
        balances[rental_id] = (rental_fee_due + extra_due + damage_due).quantize(
            Decimal("0.01")
        )
    return balances


def _sum_price_lines_by_reservation(
    reservation_ids: list[int],
) -> defaultdict[int, Decimal]:
    totals: defaultdict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    rows = (
        PriceLine.objects.filter(reservation_id__in=reservation_ids)
        .values("reservation_id")
        .annotate(total=Sum("total_amount"))
    )
    for row in rows:
        totals[row["reservation_id"]] = (row["total"] or Decimal("0")).quantize(
            Decimal("0.01")
        )
    return totals


def _sum_payments_by_rental(
    *,
    rental_ids: list[int],
    reservation_to_rental: dict[int, int],
) -> defaultdict[int, defaultdict[str, Decimal]]:
    totals: defaultdict[int, defaultdict[str, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal("0"))
    )
    reservation_ids = list(reservation_to_rental)
    rows = (
        Payment.objects.filter(
            Q(rental_id__in=rental_ids)
            | Q(reservation_id__in=reservation_ids, rental__isnull=True)
        )
        .values("rental_id", "reservation_id", "payment_type")
        .annotate(total=Sum("amount"))
    )
    for row in rows:
        rental_id = row["rental_id"] or reservation_to_rental.get(row["reservation_id"])
        if rental_id is None:
            continue
        totals[rental_id][row["payment_type"]] += row["total"] or Decimal("0")
    return totals


def _sum_charges_by_rental(
    rental_ids: list[int],
) -> defaultdict[int, defaultdict[str, Decimal]]:
    totals: defaultdict[int, defaultdict[str, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal("0"))
    )
    rows = (
        RentalCharge.objects.filter(rental_id__in=rental_ids)
        .values("rental_id", "payment_type")
        .annotate(total=Sum("amount"))
    )
    for row in rows:
        totals[row["rental_id"]][row["payment_type"]] = row["total"] or Decimal("0")
    return totals


def _positive_due(accrued: Decimal, paid: Decimal) -> Decimal:
    due = (accrued - paid).quantize(Decimal("0.01"))
    if due < 0:
        return Decimal("0")
    return due
