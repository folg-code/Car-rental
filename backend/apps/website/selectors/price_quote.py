from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apps.fleet.models import Car
from apps.pricing.dto import PricingResult
from apps.pricing.services.pricing import PricingService


@dataclass(frozen=True, slots=True)
class PriceQuoteResult:
    """Orientacyjna wycena na stronie publicznej (task 8.11)."""

    car: Car
    start_at: datetime
    end_at: datetime
    pricing: PricingResult
    extra_codes: tuple[str, ...]


def get_price_quote(
    *,
    car: Car,
    start_at: datetime,
    end_at: datetime,
    extra_codes: list[str] | None = None,
) -> PriceQuoteResult:
    """Kalkulacja read-only — bez zapisu rezerwacji ani PriceLine."""
    codes = tuple(extra_codes or ())
    pricing = PricingService.calculate(
        car=car,
        start_at=start_at,
        end_at=end_at,
        extra_codes=list(codes) or None,
    )
    return PriceQuoteResult(
        car=car,
        start_at=start_at,
        end_at=end_at,
        pricing=pricing,
        extra_codes=codes,
    )
