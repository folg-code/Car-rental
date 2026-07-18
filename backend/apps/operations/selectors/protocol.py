from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone

from apps.bookings.models import Rental, RentalStatus
from apps.operations.models import HandoverProtocol, ReturnProtocol


def _search_filter(query: str) -> Q:
    q = query.strip()
    if not q:
        return Q()
    return (
        Q(pk__iexact=q)
        | Q(reservation__pk__iexact=q)
        | Q(reservation__customer__first_name__icontains=q)
        | Q(reservation__customer__last_name__icontains=q)
        | Q(reservation__customer__email__icontains=q)
        | Q(reservation__customer__phone__icontains=q)
        | Q(reservation__car__registration_number__icontains=q)
        | Q(reservation__car__make__icontains=q)
        | Q(reservation__car__model__icontains=q)
    )


def list_rentals_pending_handover(search: str = "") -> QuerySet[Rental]:
    """Scheduled rentals awaiting handover; overdue and today first."""
    now = timezone.now()
    qs = (
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
    )
    if search.strip():
        qs = qs.filter(_search_filter(search))
    return qs.order_by("queue_priority", "scheduled_start_at")


def list_rentals_pending_return(search: str = "") -> QuerySet[Rental]:
    """Active rentals with completed handover; overdue returns first."""
    now = timezone.now()
    qs = (
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
    )
    if search.strip():
        qs = qs.filter(_search_filter(search))
    return qs.order_by("queue_priority", "scheduled_end_at")


def get_handover_for_rental(rental_id: int) -> HandoverProtocol | None:
    return (
        HandoverProtocol.objects.select_related(
            "rental",
            "rental__reservation",
            "rental__reservation__customer",
            "rental__reservation__car",
            "driver",
        )
        .prefetch_related(
            "photos",
            "damage_snapshots",
            "damage_markers",
            "equipment_lines",
            "signature",
        )
        .filter(rental_id=rental_id)
        .first()
    )


def get_return_for_rental(rental_id: int) -> ReturnProtocol | None:
    return (
        ReturnProtocol.objects.select_related(
            "rental",
            "handover",
            "rental__reservation__car",
            "rental__reservation__customer",
        )
        .prefetch_related(
            "photos",
            "damage_snapshots",
            "damage_markers",
            "equipment_lines",
            "settlement_lines",
            "signature",
        )
        .filter(rental_id=rental_id)
        .first()
    )
