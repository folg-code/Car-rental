from __future__ import annotations

from datetime import date

from django.shortcuts import render

from apps.accounts.permissions import staff_required
from apps.dashboard.selectors.fleet_alerts import list_fleet_expiry_alerts
from apps.dashboard.selectors.unpaid_rentals import list_unpaid_rentals
from apps.dashboard.services.metrics import DashboardMetricsService
from apps.operations.selectors.protocol import (
    list_rentals_pending_handover,
    list_rentals_pending_return,
)

DASHBOARD_QUEUE_LIMIT = 5


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
            "pending_handover": list(
                list_rentals_pending_handover()[:DASHBOARD_QUEUE_LIMIT]
            ),
            "pending_return": list(
                list_rentals_pending_return()[:DASHBOARD_QUEUE_LIMIT]
            ),
        },
    )


@staff_required
def module_placeholder(request, module_name: str):
    return render(
        request,
        "dashboard/module_placeholder.html",
        {"module_name": module_name},
    )
