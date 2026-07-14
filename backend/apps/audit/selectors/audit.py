from __future__ import annotations

from django.db.models import QuerySet

from apps.audit.models import AuditLog


def list_audit_logs_for_rental(
    rental_id: int,
    *,
    limit: int | None = None,
) -> QuerySet[AuditLog]:
    qs = (
        AuditLog.objects.filter(rental_id=rental_id)
        .select_related("actor", "payment", "reservation")
        .order_by("-created_at", "-pk")
    )
    if limit is not None:
        qs = qs[:limit]
    return qs


def list_audit_logs_for_reservation(
    reservation_id: int,
    *,
    limit: int | None = None,
) -> QuerySet[AuditLog]:
    qs = (
        AuditLog.objects.filter(reservation_id=reservation_id)
        .select_related("actor", "payment", "rental")
        .order_by("-created_at", "-pk")
    )
    if limit is not None:
        qs = qs[:limit]
    return qs
