from datetime import datetime

from django.db.models import QuerySet

from apps.fleet.models import AvailabilityBlock, Car


def get_overlapping_blocks(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_block_id: int | None = None,
) -> QuerySet[AvailabilityBlock]:
    """Zwraca blokady nakladajace sie z przedzialem [start_at, end_at)."""
    qs = AvailabilityBlock.objects.filter(
        car_id=car_id,
        start_at__lt=end_at,
        end_at__gt=start_at,
    )
    if exclude_block_id is not None:
        qs = qs.exclude(pk=exclude_block_id)
    return qs


def get_blocks_in_period(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
) -> QuerySet[AvailabilityBlock]:
    return AvailabilityBlock.objects.filter(
        car_id=car_id,
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).order_by("start_at")


def get_booking_busy_intervals(
    car_id: int,
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_reservation_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    """Przedzialy zajete przez rezerwacje/wynajmy (app bookings)."""
    try:
        from apps.bookings.selectors.availability import (  # noqa: PLC0415
            get_car_busy_intervals,
        )

        return get_car_busy_intervals(
            car_id,
            start_at,
            end_at,
            exclude_reservation_id=exclude_reservation_id,
        )
    except ImportError:
        return []


def filter_available_cars(
    cars: QuerySet[Car],
    start_at: datetime,
    end_at: datetime,
) -> QuerySet[Car]:
    """Auta bez blokady w podanym przedziale (bez rezerwacji — bookings w Sprint 3)."""
    blocked_ids = (
        AvailabilityBlock.objects.filter(
            start_at__lt=end_at,
            end_at__gt=start_at,
        )
        .values_list("car_id", flat=True)
        .distinct()
    )
    return cars.exclude(pk__in=blocked_ids)
