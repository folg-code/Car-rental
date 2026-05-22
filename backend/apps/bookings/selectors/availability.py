from datetime import datetime

from django.db.models import QuerySet

from apps.bookings.models import (
    BLOCKING_RENTAL_STATUSES,
    BLOCKING_RESERVATION_STATUSES,
    Rental,
    Reservation,
)


def get_overlapping_reservations(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_reservation_id: int | None = None,
) -> QuerySet[Reservation]:
    """Rezerwacje blokujace dostepnosc, nakladajace sie z przedzialem."""
    qs = Reservation.objects.filter(
        car_id=car_id,
        status__in=BLOCKING_RESERVATION_STATUSES,
        start_at__lt=end_at,
        end_at__gt=start_at,
    )
    if exclude_reservation_id is not None:
        qs = qs.exclude(pk=exclude_reservation_id)
    return qs


def get_overlapping_rentals(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_rental_id: int | None = None,
) -> QuerySet[Rental]:
    """Wynajmy blokujace dostepnosc, nakladajace sie z przedzialem."""
    qs = Rental.objects.filter(
        reservation__car_id=car_id,
        status__in=BLOCKING_RENTAL_STATUSES,
        scheduled_start_at__lt=end_at,
        scheduled_end_at__gt=start_at,
    )
    if exclude_rental_id is not None:
        qs = qs.exclude(pk=exclude_rental_id)
    return qs


def get_car_busy_intervals(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_reservation_id: int | None = None,
    exclude_rental_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    """Przedzialy zajete przez rezerwacje i wynajmy (dla fleet.AvailabilityService)."""
    intervals: list[tuple[datetime, datetime]] = [
        (row.start_at, row.end_at)
        for row in get_overlapping_reservations(
            car_id,
            start_at,
            end_at,
            exclude_reservation_id=exclude_reservation_id,
        ).only("start_at", "end_at")
    ]
    intervals.extend(
        (row.scheduled_start_at, row.scheduled_end_at)
        for row in get_overlapping_rentals(
            car_id,
            start_at,
            end_at,
            exclude_rental_id=exclude_rental_id,
        ).only("scheduled_start_at", "scheduled_end_at")
    )
    return intervals
