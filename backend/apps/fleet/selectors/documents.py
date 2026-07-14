from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Q, QuerySet

from apps.fleet.models import CarDocument, CarDocumentType, CarStatus

FLEET_EXPIRY_ALERT_DOCUMENT_TYPES = frozenset(
    {
        CarDocumentType.INSURANCE,
        CarDocumentType.INSPECTION,
    }
)
DEFAULT_EXPIRY_ALERT_DAYS = 30


def get_expiring_car_documents(
    *,
    within_days: int = DEFAULT_EXPIRY_ALERT_DAYS,
    as_of: date | None = None,
) -> QuerySet[CarDocument]:
    """
    Dokumenty OC/przeglądu aut ACTIVE z terminem wygasniecia w przeszlosci
    lub w ciagu ``within_days`` od ``as_of``.
    """
    today = as_of or date.today()
    horizon = today + timedelta(days=within_days)
    return (
        CarDocument.objects.filter(
            document_type__in=FLEET_EXPIRY_ALERT_DOCUMENT_TYPES,
            valid_until__isnull=False,
            car__status=CarStatus.ACTIVE,
        )
        .filter(Q(valid_until__lt=today) | Q(valid_until__lte=horizon))
        .select_related("car", "car__category")
        .order_by("valid_until", "car__registration_number")
    )


def count_expiring_car_documents(
    *,
    within_days: int = DEFAULT_EXPIRY_ALERT_DAYS,
    as_of: date | None = None,
) -> int:
    return get_expiring_car_documents(within_days=within_days, as_of=as_of).count()
