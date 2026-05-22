from datetime import datetime

from django.db.models import QuerySet

from apps.bookings.models import Rental, RentalStatus


def get_rental_by_id(rental_id: int) -> Rental | None:
    return (
        Rental.objects.select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
            "reservation__car__category",
            "created_by",
        )
        .prefetch_related("reservation__price_lines")
        .filter(pk=rental_id)
        .first()
    )


def list_rentals(
    *,
    status: str | None = None,
    car_id: int | None = None,
    customer_id: int | None = None,
) -> QuerySet[Rental]:
    qs = Rental.objects.select_related(
        "reservation",
        "reservation__customer",
        "reservation__car",
        "reservation__car__category",
    ).order_by("-scheduled_start_at")
    if status:
        qs = qs.filter(status=status)
    if car_id is not None:
        qs = qs.filter(reservation__car_id=car_id)
    if customer_id is not None:
        qs = qs.filter(reservation__customer_id=customer_id)
    return qs


def list_active_rentals(*, as_of: datetime | None = None) -> QuerySet[Rental]:
    """Wynajmy operacyjnie aktywne
    (zaplanowany, w trakcie lub po zwrocie, przed zamknieciem)."""
    return Rental.objects.filter(
        status__in=(
            RentalStatus.SCHEDULED,
            RentalStatus.ACTIVE,
            RentalStatus.RETURNED,
        )
    ).select_related("reservation", "reservation__customer", "reservation__car")
