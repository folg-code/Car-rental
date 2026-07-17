from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.utils import timezone

from apps.bookings.models import Rental, RentalStatus
from apps.operations.models import HandoverProtocol, ReturnProtocol


def list_rentals_pending_handover() -> QuerySet[Rental]:
    """Scheduled rentals awaiting handover; overdue and today first."""
    now = timezone.now()
    return (
        Rental.objects.filter(status=RentalStatus.SCHEDULED)
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
        )
        .annotate(
            queue_priority=Case(
                When(scheduled_start_at__lt=now, then=Value(0)),
                When(scheduled_start_at__date=now.date(), then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        )
        .order_by("queue_priority", "scheduled_start_at")
    )


def list_rentals_pending_return() -> QuerySet[Rental]:
    """Active rentals with completed handover; overdue returns first."""
    now = timezone.now()
    return (
        Rental.objects.filter(
            status=RentalStatus.ACTIVE,
            handover_protocol__completed_at__isnull=False,
        )
        .select_related(
            "reservation",
            "reservation__customer",
            "reservation__car",
            "handover_protocol",
        )
        .annotate(
            queue_priority=Case(
                When(scheduled_end_at__lt=now, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        .order_by("queue_priority", "scheduled_end_at")
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
