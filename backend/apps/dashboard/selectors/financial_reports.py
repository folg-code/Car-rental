from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal

from django.utils import timezone

from apps.documents.selectors.invoice_data import (
    get_invoice_totals_in_period,
    list_invoices_in_period,
)
from apps.payments.models import PaymentMethod, PaymentType
from apps.payments.selectors.payment import (
    get_charges_accrued_in_period,
    get_payment_type_totals_in_period,
    get_revenue_by_method_in_period,
    get_revenue_total_in_period,
    list_payments,
)


@dataclass(frozen=True, slots=True)
class RevenueBreakdown:
    rental_fees: Decimal
    extra_charges: Decimal
    damage_charges: Decimal

    @property
    def total(self) -> Decimal:
        return (self.rental_fees + self.extra_charges + self.damage_charges).quantize(
            Decimal("0.01")
        )


@dataclass(frozen=True, slots=True)
class FinancialPeriodReport:
    period_start: date
    period_end: date
    revenue: RevenueBreakdown
    revenue_total: Decimal
    deposits_collected: Decimal
    refunds_paid: Decimal
    deposit_net: Decimal
    charges_accrued: Decimal
    invoice_total: Decimal
    invoice_count: int
    revenue_by_method: dict[str, Decimal]


def period_bounds_from_dates(
    start_date: date,
    end_date: date,
) -> tuple[datetime, datetime]:
    """Konwertuje daty kalendarzowe na przedzial paid_at w biezacej strefie czasowej."""
    tz = timezone.get_current_timezone()
    start_at = timezone.make_aware(datetime.combine(start_date, time.min), tz)
    end_at = timezone.make_aware(datetime.combine(end_date, time.max), tz)
    return start_at, end_at


def default_period_end(*, as_of: date | None = None) -> date:
    return as_of or timezone.localdate()


def default_period_start(*, as_of: date | None = None) -> date:
    today = default_period_end(as_of=as_of)
    return today.replace(day=1)


def get_financial_period_report(
    *,
    start_date: date,
    end_date: date,
) -> FinancialPeriodReport:
    start_at, end_at = period_bounds_from_dates(start_date, end_date)
    type_totals = get_payment_type_totals_in_period(start_at, end_at)
    revenue = RevenueBreakdown(
        rental_fees=type_totals[PaymentType.RENTAL_FEE],
        extra_charges=type_totals[PaymentType.EXTRA_CHARGE],
        damage_charges=type_totals[PaymentType.DAMAGE_CHARGE],
    )
    deposits = type_totals[PaymentType.DEPOSIT]
    refunds = type_totals[PaymentType.REFUND]
    invoice_total, invoice_count = get_invoice_totals_in_period(start_date, end_date)

    return FinancialPeriodReport(
        period_start=start_date,
        period_end=end_date,
        revenue=revenue,
        revenue_total=get_revenue_total_in_period(start_at, end_at),
        deposits_collected=deposits,
        refunds_paid=refunds,
        deposit_net=(deposits - refunds).quantize(Decimal("0.01")),
        charges_accrued=get_charges_accrued_in_period(start_at, end_at),
        invoice_total=invoice_total,
        invoice_count=invoice_count,
        revenue_by_method=get_revenue_by_method_in_period(start_at, end_at),
    )


def list_payments_in_period(
    start_date: date,
    end_date: date,
    *,
    limit: int = 50,
):
    start_at, end_at = period_bounds_from_dates(start_date, end_date)
    qs = list_payments().filter(
        paid_at__gte=start_at,
        paid_at__lte=end_at,
    )
    return qs[:limit]


def list_invoices_for_report(
    start_date: date,
    end_date: date,
    *,
    limit: int = 50,
):
    return list_invoices_in_period(start_date, end_date, limit=limit)


PAYMENT_METHOD_LABELS = dict(PaymentMethod.choices)
