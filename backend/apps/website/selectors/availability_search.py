from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.fleet.models import Car
from apps.fleet.services.availability import AvailabilityService


@dataclass(frozen=True, slots=True)
class AvailabilitySearchResult:
    """Wynik wyszukiwania dostepnosci na stronie publicznej (task 8.10)."""

    start_at: datetime
    end_at: datetime
    cars: tuple[Car, ...]
    category_id: int | None


def search_available_cars(
    start_at: datetime,
    end_at: datetime,
    *,
    category_id: int | None = None,
) -> AvailabilitySearchResult:
    """Wolne auta w przedziale — delegacja do ``AvailabilityService``."""
    cars = tuple(
        AvailabilityService.list_available_cars(
            start_at,
            end_at,
            category_id=category_id,
        )
    )
    return AvailabilitySearchResult(
        start_at=start_at,
        end_at=end_at,
        cars=cars,
        category_id=category_id,
    )
