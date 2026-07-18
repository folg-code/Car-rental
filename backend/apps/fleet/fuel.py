"""Przeliczanie poziomu paliwa: procent ↔ litry (pojemność baku)."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum


class FuelLevel(StrEnum):
    """Opcjonalna etykieta przybliżona (kompatybilność / wyświetlanie)."""

    RESERVE = "reserve"
    QUARTER = "quarter"
    HALF = "half"
    THREE_QUARTER = "three_quarter"
    FULL = "full"


FUEL_LEVEL_FRACTIONS: dict[str, Decimal] = {
    FuelLevel.RESERVE.value: Decimal("0.05"),
    FuelLevel.QUARTER.value: Decimal("0.25"),
    FuelLevel.HALF.value: Decimal("0.50"),
    FuelLevel.THREE_QUARTER.value: Decimal("0.75"),
    FuelLevel.FULL.value: Decimal("1.00"),
}

FUEL_LEVEL_LABELS: dict[str, str] = {
    FuelLevel.RESERVE.value: "Rezerwa",
    FuelLevel.QUARTER.value: "1/4",
    FuelLevel.HALF.value: "1/2",
    FuelLevel.THREE_QUARTER.value: "3/4",
    FuelLevel.FULL.value: "Pełny",
}

FUEL_LEVEL_CHOICES: tuple[tuple[str, str], ...] = tuple(
    (key, FUEL_LEVEL_LABELS[key]) for key in FUEL_LEVEL_FRACTIONS
)


def fuel_level_to_percent(level: str) -> int:
    fraction = FUEL_LEVEL_FRACTIONS.get(level, Decimal("0"))
    return int((fraction * 100).quantize(Decimal("1")))


def percent_to_fuel_level(percent: int) -> str:
    """Przybliżenie procentu do najbliższej etykiety skali (opcjonalne)."""
    clamped = max(0, min(100, percent))
    best = FuelLevel.RESERVE.value
    best_delta = 101
    for level, fraction in FUEL_LEVEL_FRACTIONS.items():
        candidate = int((fraction * 100).quantize(Decimal("1")))
        delta = abs(candidate - clamped)
        if delta < best_delta:
            best = level
            best_delta = delta
    return best


def percent_to_liters(
    percent: int,
    tank_capacity_liters: Decimal | None,
) -> Decimal:
    """Litry ≈ (procent / 100) × pojemność baku."""
    if tank_capacity_liters is None:
        return Decimal("0")
    clamped = max(0, min(100, percent))
    return (tank_capacity_liters * Decimal(clamped) / Decimal("100")).quantize(
        Decimal("0.1")
    )


def fuel_level_to_liters(level: str, tank_capacity_liters: Decimal | None) -> Decimal:
    return percent_to_liters(fuel_level_to_percent(level), tank_capacity_liters)


def fuel_delta_liters_from_percent(
    *,
    handover_percent: int,
    return_percent: int,
    tank_capacity_liters: Decimal | None,
) -> Decimal:
    """Ile litrów brakuje przy zwrocie względem wydania (>= 0)."""
    start = percent_to_liters(handover_percent, tank_capacity_liters)
    end = percent_to_liters(return_percent, tank_capacity_liters)
    delta = start - end
    return delta if delta > 0 else Decimal("0")


def fuel_delta_liters(
    *,
    handover_level: str,
    return_level: str,
    tank_capacity_liters: Decimal | None,
) -> Decimal:
    """Kompatybilność ze skalą dyskretną — preferuj fuel_delta_liters_from_percent."""
    return fuel_delta_liters_from_percent(
        handover_percent=fuel_level_to_percent(handover_level),
        return_percent=fuel_level_to_percent(return_level),
        tank_capacity_liters=tank_capacity_liters,
    )
