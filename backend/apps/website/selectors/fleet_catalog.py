from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Count, Q

from apps.fleet.models import Car, CarCategory, CarStatus
from apps.fleet.selectors.car import list_active_cars, list_categories


@dataclass(frozen=True, slots=True)
class PublicFleetCatalog:
    """Dane katalogu floty na stronie publicznej (task 8.9)."""

    categories: tuple[CarCategory, ...]
    cars: tuple[Car, ...]
    selected_category_slug: str | None


def get_public_fleet_catalog(
    *,
    category_slug: str | None = None,
) -> PublicFleetCatalog:
    """Aktywne auta i kategorie z licznikiem — tylko odczyt z fleet."""
    categories = tuple(
        list_categories().annotate(
            active_car_count=Count(
                "cars",
                filter=Q(cars__status=CarStatus.ACTIVE),
            )
        )
    )
    cars_qs = list_active_cars().prefetch_related("images")
    selected_slug = (category_slug or "").strip() or None
    if selected_slug:
        cars_qs = cars_qs.filter(category__slug=selected_slug)

    return PublicFleetCatalog(
        categories=categories,
        cars=tuple(cars_qs),
        selected_category_slug=selected_slug,
    )
