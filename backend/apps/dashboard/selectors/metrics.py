from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.utils import timezone

from apps.bookings.models import (
    BLOCKING_RENTAL_STATUSES,
    BLOCKING_RESERVATION_STATUSES,
    Rental,
    RentalStatus,
    Reservation,
    ReservationStatus,
)
from apps.fleet.models import Car, CarStatus


@dataclass(frozen=True, slots=True)
class DashboardMetrics:
    """Podstawowe KPI pulpitu operacyjnego (Sprint 3 / task 8.1)."""

    active_reservations: int
    active_rentals: int
    free_cars: int
    upcoming_returns: int


def get_dashboard_metrics(*, as_of: datetime | None = None) -> DashboardMetrics:
    """Agreguje metryki bookings i floty na pulpit wewnętrzny."""
    now = as_of or timezone.now()
    week_ahead = now + timedelta(days=7)

    active_reservations = Reservation.objects.filter(
        status__in=BLOCKING_RESERVATION_STATUSES,
        end_at__gt=now,
    ).count()

    active_rentals = Rental.objects.filter(
        status__in=BLOCKING_RENTAL_STATUSES,
        scheduled_end_at__gt=now,
    ).count()

    busy_reservation_car_ids = set(
        Reservation.objects.filter(
            status__in=BLOCKING_RESERVATION_STATUSES,
            start_at__lt=now,
            end_at__gt=now,
        ).values_list("car_id", flat=True)
    )
    busy_rental_car_ids = set(
        Rental.objects.filter(
            status__in=BLOCKING_RENTAL_STATUSES,
            scheduled_start_at__lt=now,
            scheduled_end_at__gt=now,
        ).values_list("reservation__car_id", flat=True)
    )
    busy_now = len(busy_reservation_car_ids | busy_rental_car_ids)
    total_active_cars = Car.objects.filter(status=CarStatus.ACTIVE).count()
    free_cars = max(0, total_active_cars - busy_now)

    upcoming_returns = (
        Reservation.objects.filter(
            status=ReservationStatus.CONFIRMED,
            end_at__gte=now,
            end_at__lte=week_ahead,
        ).count()
        + Rental.objects.filter(
            status__in=(RentalStatus.SCHEDULED, RentalStatus.ACTIVE),
            scheduled_end_at__gte=now,
            scheduled_end_at__lte=week_ahead,
        ).count()
    )

    return DashboardMetrics(
        active_reservations=active_reservations,
        active_rentals=active_rentals,
        free_cars=free_cars,
        upcoming_returns=upcoming_returns,
    )
