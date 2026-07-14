from __future__ import annotations

from apps.bookings.models import Reservation
from apps.bookings.services.price_snapshot import PriceSnapshotService


def get_public_reservation_summary(reservation_id: int) -> Reservation | None:
    """Rezerwacja z rozpisem ceny na stronie potwierdzenia (read-only)."""
    return (
        Reservation.objects.select_related("customer", "car", "car__category")
        .prefetch_related("price_lines")
        .filter(pk=reservation_id)
        .first()
    )


def reservation_display_total(reservation: Reservation):
    return PriceSnapshotService.reservation_total(reservation)
