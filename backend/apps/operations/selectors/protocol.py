from django.db.models import QuerySet

from apps.bookings.models import Rental, RentalStatus
from apps.operations.models import HandoverProtocol, ReturnProtocol


def list_rentals_pending_handover() -> QuerySet[Rental]:
    return (
        Rental.objects.filter(status=RentalStatus.SCHEDULED)
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
        )
        .order_by("scheduled_start_at")
    )


def list_rentals_pending_return() -> QuerySet[Rental]:
    return (
        Rental.objects.filter(status=RentalStatus.ACTIVE)
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
            "handover_protocol",
        )
        .order_by("scheduled_end_at")
    )


def get_handover_for_rental(rental_id: int) -> HandoverProtocol | None:
    return (
        HandoverProtocol.objects.select_related("rental", "rental__reservation")
        .prefetch_related("photos", "damage_snapshots", "signature")
        .filter(rental_id=rental_id)
        .first()
    )


def get_return_for_rental(rental_id: int) -> ReturnProtocol | None:
    return (
        ReturnProtocol.objects.select_related("rental", "handover")
        .prefetch_related("photos", "damage_snapshots", "signature")
        .filter(rental_id=rental_id)
        .first()
    )
