from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CalculatedPriceLine:
    """Pozycja wyniku kalkulacji — do skopiowania do bookings.PriceLine."""

    line_type: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    source_code: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class PricingResult:
    price_list_id: int
    currency: str
    lines: tuple[CalculatedPriceLine, ...]

    @property
    def total(self) -> Decimal:
        return sum((line.total_amount for line in self.lines), Decimal("0"))
