from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.fleet.models import Car
from apps.pricing.dto import CalculatedPriceLine, PricingResult
from apps.pricing.models import (
    AmountType,
    ExtraServiceChargeType,
    PricingRule,
    PricingRuleType,
)
from apps.pricing.selectors.price_list import (
    get_active_rules,
    get_daily_rate,
    get_extra_by_code,
    get_price_list_for_date,
)

MONEY_QUANT = Decimal("0.01")
WEEKEND_WEEKDAYS = frozenset({4, 5, 6})  # pt–nd


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT)


@dataclass(frozen=True, slots=True)
class _RentalPeriod:
    dates: tuple[date, ...]
    days: int


class PricingService:
    @staticmethod
    def _rental_period(start_at: datetime, end_at: datetime) -> _RentalPeriod:
        if start_at >= end_at:
            raise ValidationError(
                "Data zakonczenia musi byc pozniejsza niz data rozpoczecia."
            )
        start_d = start_at.date()
        end_d = end_at.date()
        day_count = max(1, (end_d - start_d).days)
        dates = tuple(start_d + timedelta(days=i) for i in range(day_count))
        return _RentalPeriod(dates=dates, days=day_count)

    @staticmethod
    def _rule_applies_on_date(rule: PricingRule, on_date: date) -> bool:
        if rule.valid_from and on_date < rule.valid_from:
            return False
        if rule.valid_to and on_date > rule.valid_to:
            return False
        return True

    @staticmethod
    def _count_weekend_days(dates: tuple[date, ...]) -> int:
        return sum(1 for d in dates if d.weekday() in WEEKEND_WEEKDAYS)

    @staticmethod
    def _count_rule_days(rule: PricingRule, dates: tuple[date, ...]) -> int:
        return sum(1 for d in dates if PricingService._rule_applies_on_date(rule, d))

    @staticmethod
    def _apply_amount(
        *,
        amount_type: str,
        value: Decimal,
        base: Decimal,
        day_count: int,
        unit_days: int,
    ) -> Decimal:
        if amount_type == AmountType.PERCENT:
            portion = base * value / Decimal("100")
            return _money(portion)
        if amount_type == AmountType.PER_DAY:
            return _money(value * Decimal(unit_days))
        return _money(value)

    @staticmethod
    def _line_type_for_rule(rule_type: str) -> str:
        mapping = {
            PricingRuleType.WEEKEND_SURCHARGE: "weekend_surcharge",
            PricingRuleType.HOLIDAY_SURCHARGE: "holiday_surcharge",
            PricingRuleType.SEASON_SURCHARGE: "season_surcharge",
            PricingRuleType.LONG_RENTAL_DISCOUNT: "discount",
            PricingRuleType.MANUAL_DISCOUNT: "discount",
        }
        return mapping.get(rule_type, "discount")

    @staticmethod
    def calculate(
        *,
        car: Car,
        start_at: datetime,
        end_at: datetime,
        extra_codes: list[str] | None = None,
    ) -> PricingResult:
        period = PricingService._rental_period(start_at, end_at)
        price_list = get_price_list_for_date(period.dates[0])
        if price_list is None:
            raise ValidationError("Brak aktywnego cennika dla wybranego terminu.")

        daily_rate = get_daily_rate(price_list, car.category_id)
        if daily_rate is None:
            raise ValidationError(
                f"Brak stawki dziennej dla kategorii {car.category.name} w cenniku."
            )

        lines: list[CalculatedPriceLine] = []
        sort_order = 0
        unit_price = daily_rate.amount
        base_total = _money(unit_price * Decimal(period.days))

        lines.append(
            CalculatedPriceLine(
                line_type="daily_rental",
                description=(
                    f"Wynajem {period.days} dni — {car.category.name} "
                    f"({unit_price} {price_list.currency}/doba)"
                ),
                quantity=Decimal(period.days),
                unit_price=unit_price,
                total_amount=base_total,
                source_code=f"daily_rate:{car.category.slug}",
                sort_order=sort_order,
            )
        )
        sort_order += 1
        running_base = base_total

        for rule in get_active_rules(price_list):
            line_type = PricingService._line_type_for_rule(rule.rule_type)
            total = Decimal("0")
            unit_days = 0
            description = rule.name

            if rule.rule_type == PricingRuleType.WEEKEND_SURCHARGE:
                unit_days = PricingService._count_weekend_days(period.dates)
                if unit_days == 0:
                    continue
                weekend_base = _money(unit_price * Decimal(unit_days))
                total = PricingService._apply_amount(
                    amount_type=rule.amount_type,
                    value=rule.value,
                    base=weekend_base,
                    day_count=period.days,
                    unit_days=unit_days,
                )
                description = f"{rule.name} ({unit_days} dni weekendowych)"

            elif rule.rule_type in (
                PricingRuleType.HOLIDAY_SURCHARGE,
                PricingRuleType.SEASON_SURCHARGE,
            ):
                unit_days = PricingService._count_rule_days(rule, period.dates)
                if unit_days == 0:
                    continue
                period_base = _money(unit_price * Decimal(unit_days))
                total = PricingService._apply_amount(
                    amount_type=rule.amount_type,
                    value=rule.value,
                    base=period_base,
                    day_count=period.days,
                    unit_days=unit_days,
                )
                description = f"{rule.name} ({unit_days} dni)"

            elif rule.rule_type == PricingRuleType.LONG_RENTAL_DISCOUNT:
                if rule.min_rental_days and period.days < rule.min_rental_days:
                    continue
                total = PricingService._apply_amount(
                    amount_type=rule.amount_type,
                    value=rule.value,
                    base=running_base,
                    day_count=period.days,
                    unit_days=period.days,
                )
                total = -abs(total)
                description = f"{rule.name} (od {rule.min_rental_days} dni)"

            else:
                continue

            if total == 0:
                continue

            qty = Decimal("1")
            line_unit = total
            if rule.amount_type == AmountType.PER_DAY and unit_days > 0:
                qty = Decimal(unit_days)
                line_unit = _money(total / qty) if qty else total

            lines.append(
                CalculatedPriceLine(
                    line_type=line_type,
                    description=description,
                    quantity=qty,
                    unit_price=line_unit,
                    total_amount=total,
                    source_code=f"rule:{rule.rule_type}:{rule.pk}",
                    sort_order=sort_order,
                )
            )
            sort_order += 1
            if total < 0:
                running_base += total

        for code in extra_codes or []:
            extra = get_extra_by_code(price_list, code)
            if extra is None:
                raise ValidationError(f"Nieznana usluga dodatkowa: {code}")

            if extra.charge_type == ExtraServiceChargeType.PER_DAY:
                qty = Decimal(period.days)
                line_total = _money(extra.amount * qty)
                line_unit = extra.amount
            elif extra.charge_type == ExtraServiceChargeType.PER_UNIT:
                qty = Decimal("1")
                line_total = _money(extra.amount)
                line_unit = extra.amount
            else:
                qty = Decimal("1")
                line_total = _money(extra.amount)
                line_unit = extra.amount

            lines.append(
                CalculatedPriceLine(
                    line_type="extra_service",
                    description=extra.name,
                    quantity=qty,
                    unit_price=line_unit,
                    total_amount=line_total,
                    source_code=f"extra:{extra.code}",
                    sort_order=sort_order,
                )
            )
            sort_order += 1

        return PricingResult(
            price_list_id=price_list.pk,
            currency=price_list.currency,
            lines=tuple(lines),
        )
