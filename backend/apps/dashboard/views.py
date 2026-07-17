from __future__ import annotations

from datetime import date

from django.shortcuts import render
from django.utils.dateparse import parse_date

from apps.accounts.permissions import staff_required
from apps.dashboard.selectors.financial_reports import (
    PAYMENT_METHOD_LABELS,
    default_period_end,
    default_period_start,
    get_financial_period_report,
    list_invoices_for_report,
    list_payments_in_period,
)
from apps.dashboard.selectors.fleet_alerts import list_fleet_expiry_alerts
from apps.dashboard.selectors.unpaid_rentals import list_unpaid_rentals
from apps.dashboard.services.metrics import DashboardMetricsService
from apps.payments.models import PaymentType

DASHBOARD_QUEUE_LIMIT = 5


def _resolve_report_period(request) -> tuple[date, date]:
    today = default_period_end()
    start = parse_date(request.GET.get("from", "")) or default_period_start(as_of=today)
    end = parse_date(request.GET.get("to", "")) or default_period_end(as_of=today)
    if start > end:
        start, end = end, start
    return start, end


@staff_required
def panel_entry(request):
    """Start screen: choose admin desk vs field ops (Sprint 12.6)."""
    return render(request, "dashboard/panel_entry.html")


@staff_required
def panel_home(request):
    metrics = DashboardMetricsService.get_home_metrics()
    return render(
        request,
        "dashboard/panel.html",
        {
            "metrics": metrics,
            "today": date.today(),
            "unpaid_rentals_queue": list_unpaid_rentals(limit=DASHBOARD_QUEUE_LIMIT),
            "fleet_document_alerts": list_fleet_expiry_alerts(
                limit=DASHBOARD_QUEUE_LIMIT
            ),
        },
    )


@staff_required
def financial_report(request):
    period_start, period_end = _resolve_report_period(request)
    report = get_financial_period_report(
        start_date=period_start,
        end_date=period_end,
    )
    payment_type_labels = dict(PaymentType.choices)
    revenue_by_method_rows = [
        (PAYMENT_METHOD_LABELS.get(method, method), amount)
        for method, amount in sorted(report.revenue_by_method.items())
    ]
    return render(
        request,
        "dashboard/financial_report.html",
        {
            "report": report,
            "period_start": period_start,
            "period_end": period_end,
            "payments_in_period": list_payments_in_period(
                period_start,
                period_end,
            ),
            "invoices_in_period": list_invoices_for_report(
                period_start,
                period_end,
            ),
            "payment_type_labels": payment_type_labels,
            "revenue_by_method_rows": revenue_by_method_rows,
        },
    )


@staff_required
def module_placeholder(request, module_name: str):
    return render(
        request,
        "dashboard/module_placeholder.html",
        {"module_name": module_name},
    )
