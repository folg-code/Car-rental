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
from apps.dashboard.selectors.fleet_alerts import count_fleet_expiry_alerts
from apps.dashboard.selectors.unpaid_rentals import count_unpaid_rentals
from apps.fleet.services.availability import AvailabilityService


@dataclass(frozen=True, slots=True)
class DashboardMetrics:
    """Podstawowe KPI pulpitu operacyjnego (Sprint 3 / task 8.1)."""

    active_reservations: int
    active_rentals: int
    free_cars: int
    upcoming_returns: int
    unpaid_rentals: int
    expiring_fleet_documents: int


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

    free_cars = AvailabilityService.count_available_cars_at(now)

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

    unpaid_rentals = count_unpaid_rentals()
    expiring_fleet_documents = count_fleet_expiry_alerts()

    return DashboardMetrics(
        active_reservations=active_reservations,
        active_rentals=active_rentals,
        free_cars=free_cars,
        upcoming_returns=upcoming_returns,
        unpaid_rentals=unpaid_rentals,
        expiring_fleet_documents=expiring_fleet_documents,
    )
