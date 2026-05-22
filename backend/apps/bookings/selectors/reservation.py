from datetime import datetime

from django.db.models import QuerySet

from apps.bookings.models import Reservation


def get_reservation_by_id(reservation_id: int) -> Reservation | None:
    return (
        Reservation.objects.select_related("customer", "car", "car__category")
        .filter(pk=reservation_id)
        .first()
    )


def list_reservations(
    *,
    status: str | None = None,
    car_id: int | None = None,
    customer_id: int | None = None,
) -> QuerySet[Reservation]:
    qs = Reservation.objects.select_related(
        "customer", "car", "car__category", "created_by"
    ).order_by("-start_at")
    if status:
        qs = qs.filter(status=status)
    if car_id is not None:
        qs = qs.filter(car_id=car_id)
    if customer_id is not None:
        qs = qs.filter(customer_id=customer_id)
    return qs


def list_reservations_in_period(
    start_at: datetime,
    end_at: datetime,
    *,
    status: str | None = None,
) -> QuerySet[Reservation]:
    qs = Reservation.objects.filter(
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).select_related("customer", "car")
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("start_at")
