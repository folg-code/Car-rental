from __future__ import annotations

from apps.bookings.models import BLOCKING_RENTAL_STATUSES, Rental
from apps.payments.selectors.payment import rental_has_balance_due


def count_unpaid_rentals() -> int:
    """Liczba wynajmow operacyjnych z niesplacona naleznoscia za wynajem."""
    return sum(
        1
        for rental_id in Rental.objects.filter(
            status__in=BLOCKING_RENTAL_STATUSES,
        ).values_list("pk", flat=True)
        if rental_has_balance_due(rental_id)
    )


def list_unpaid_rentals(*, limit: int = 50) -> list[Rental]:
    """Wynajmy z saldem do zaplaty — do kolejki na pulpicie (task 8.6)."""
    unpaid: list[Rental] = []
    rentals = (
        Rental.objects.filter(status__in=BLOCKING_RENTAL_STATUSES)
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
        )
        .order_by("-scheduled_start_at")
    )
    for rental in rentals:
        if rental_has_balance_due(rental.pk):
            unpaid.append(rental)
        if len(unpaid) >= limit:
            break
    return unpaid
