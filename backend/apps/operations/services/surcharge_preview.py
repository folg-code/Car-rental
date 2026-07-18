from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.pricing.models import ExtraService, ExtraServiceChargeType
from apps.pricing.selectors.price_list import get_extra_by_code, get_price_list_for_date

FUEL_REFILL_CODE = "fuel_refill"
EXTRA_KM_CODE = "extra_km"


@dataclass(frozen=True)
class SurchargeLine:
    code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal


@dataclass(frozen=True)
class SurchargePreview:
    lines: tuple[SurchargeLine, ...]
    total: Decimal
    summary_notes: str


class SurchargePreviewService:
    @staticmethod
    def _line_from_extra(
        extra: ExtraService,
        *,
        code: str,
        quantity: Decimal,
        label: str,
    ) -> SurchargeLine | None:
        if quantity <= 0:
            return None

        if extra.charge_type == ExtraServiceChargeType.PER_UNIT:
            unit_price = extra.amount
            total = (unit_price * quantity).quantize(Decimal("0.01"))
            qty_display = quantity
        elif extra.charge_type == ExtraServiceChargeType.PER_RENTAL:
            unit_price = extra.amount
            total = unit_price.quantize(Decimal("0.01"))
            qty_display = Decimal("1")
        else:
            unit_price = extra.amount
            total = unit_price.quantize(Decimal("0.01"))
            qty_display = Decimal("1")

        return SurchargeLine(
            code=code,
            description=label,
            quantity=qty_display,
            unit_price=unit_price,
            total=total,
        )

    @staticmethod
    def _build_summary_notes(
        *,
        fuel_delta: int,
        driven_km: int,
        lines: tuple[SurchargeLine, ...],
        priced: bool,
    ) -> str:
        notes: list[str] = []
        if fuel_delta > 0:
            if priced and any(line.code == FUEL_REFILL_CODE for line in lines):
                fuel_line = next(
                    line for line in lines if line.code == FUEL_REFILL_CODE
                )
                notes.append(
                    f"Dopelnienie paliwa: -{fuel_delta} p.p. "
                    f"(szac. {fuel_line.total} PLN)."
                )
            else:
                notes.append(f"Dopelnienie paliwa: brak {fuel_delta} p.p.")
        if driven_km > 0:
            if priced and any(line.code == EXTRA_KM_CODE for line in lines):
                km_line = next(line for line in lines if line.code == EXTRA_KM_CODE)
                notes.append(
                    f"Przejechane km: {driven_km} (szac. {km_line.total} PLN)."
                )
            else:
                notes.append(f"Przejechane km: {driven_km}.")
        return " ".join(notes)

    @staticmethod
    def preview(
        *,
        handover_mileage: int,
        handover_fuel: int,
        return_mileage: int,
        return_fuel: int,
        on_date: date | None = None,
        tank_capacity_liters: Decimal | None = None,
        handover_fuel_level: str = "",
        return_fuel_level: str = "",
    ) -> SurchargePreview:
        driven_km = max(0, return_mileage - handover_mileage)

        # Preferuj litry z procentów × pojemność baku.
        if tank_capacity_liters is not None:
            from apps.fleet.fuel import fuel_delta_liters_from_percent

            fuel_liters = fuel_delta_liters_from_percent(
                handover_percent=handover_fuel,
                return_percent=return_fuel,
                tank_capacity_liters=tank_capacity_liters,
            )
            fuel_delta = int(fuel_liters) if fuel_liters > 0 else 0
            fuel_qty: Decimal = fuel_liters if fuel_liters > 0 else Decimal("0")
            fuel_unit_label = "L"
        else:
            fuel_delta = max(0, handover_fuel - return_fuel)
            fuel_qty = Decimal(fuel_delta)
            fuel_unit_label = "p.p."

        price_list = get_price_list_for_date(on_date or date.today())
        lines: list[SurchargeLine] = []

        if price_list is not None and fuel_qty > 0:
            fuel_extra = get_extra_by_code(price_list, FUEL_REFILL_CODE)
            if fuel_extra is not None:
                quantity = (
                    fuel_qty
                    if fuel_extra.charge_type == ExtraServiceChargeType.PER_UNIT
                    else Decimal("1")
                )
                line = SurchargePreviewService._line_from_extra(
                    fuel_extra,
                    code=FUEL_REFILL_CODE,
                    quantity=quantity,
                    label=f"{fuel_extra.name} ({fuel_unit_label})",
                )
                if line is not None:
                    lines.append(line)

        if price_list is not None and driven_km > 0:
            km_extra = get_extra_by_code(price_list, EXTRA_KM_CODE)
            if km_extra is not None:
                quantity = (
                    Decimal(driven_km)
                    if km_extra.charge_type == ExtraServiceChargeType.PER_UNIT
                    else Decimal("1")
                )
                line = SurchargePreviewService._line_from_extra(
                    km_extra,
                    code=EXTRA_KM_CODE,
                    quantity=quantity,
                    label=km_extra.name,
                )
                if line is not None:
                    lines.append(line)

        line_tuple = tuple(lines)
        total = sum((line.total for line in line_tuple), Decimal("0")).quantize(
            Decimal("0.01")
        )
        summary = SurchargePreviewService._build_summary_notes(
            fuel_delta=fuel_delta,
            driven_km=driven_km,
            lines=line_tuple,
            priced=price_list is not None,
        )
        return SurchargePreview(lines=line_tuple, total=total, summary_notes=summary)
