from __future__ import annotations

from datetime import date

from apps.fleet.models import CarDocument
from apps.fleet.selectors.documents import (
    DEFAULT_EXPIRY_ALERT_DAYS,
    count_expiring_car_documents,
    get_expiring_car_documents,
)


def count_fleet_expiry_alerts(
    *,
    within_days: int = DEFAULT_EXPIRY_ALERT_DAYS,
    as_of: date | None = None,
) -> int:
    """Liczba alertow dokumentow floty (OC / przeglad) na pulpicie."""
    return count_expiring_car_documents(within_days=within_days, as_of=as_of)


def list_fleet_expiry_alerts(
    *,
    within_days: int = DEFAULT_EXPIRY_ALERT_DAYS,
    as_of: date | None = None,
    limit: int = 50,
) -> list[CarDocument]:
    """Lista dokumentow do widgetu alertow (task 8.6)."""
    return list(
        get_expiring_car_documents(within_days=within_days, as_of=as_of)[:limit]
    )
