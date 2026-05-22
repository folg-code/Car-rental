from datetime import timedelta

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


def get_bookings_dashboard_metrics() -> dict[str, int]:
    """Metryki bookings na pulpicie (rezerwacje + wynajmy)."""
    now = timezone.now()
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

    return {
        "active_reservations": active_reservations,
        "active_rentals": active_rentals,
        "free_cars": free_cars,
        "upcoming_returns": upcoming_returns,
    }
