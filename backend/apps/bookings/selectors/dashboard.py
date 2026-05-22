from datetime import timedelta

from django.utils import timezone

from apps.bookings.models import (
    BLOCKING_RESERVATION_STATUSES,
    Reservation,
    ReservationStatus,
)
from apps.fleet.models import Car, CarStatus


def get_bookings_dashboard_metrics() -> dict[str, int]:
    """Metryki bookings na pulpicie (Sprint 3 — bez Rental)."""
    now = timezone.now()
    week_ahead = now + timedelta(days=7)

    active_reservations = Reservation.objects.filter(
        status__in=BLOCKING_RESERVATION_STATUSES,
        end_at__gt=now,
    ).count()

    busy_now_car_ids = (
        Reservation.objects.filter(
            status__in=BLOCKING_RESERVATION_STATUSES,
            start_at__lt=now,
            end_at__gt=now,
        )
        .values_list("car_id", flat=True)
        .distinct()
    )
    total_active_cars = Car.objects.filter(status=CarStatus.ACTIVE).count()
    busy_now = len(list(busy_now_car_ids))
    free_cars = max(0, total_active_cars - busy_now)

    upcoming_returns = Reservation.objects.filter(
        status=ReservationStatus.CONFIRMED,
        end_at__gte=now,
        end_at__lte=week_ahead,
    ).count()

    return {
        "active_reservations": active_reservations,
        "free_cars": free_cars,
        "upcoming_returns": upcoming_returns,
    }
