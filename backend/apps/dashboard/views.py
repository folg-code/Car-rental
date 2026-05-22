from django.shortcuts import render

from apps.accounts.permissions import staff_required
from apps.bookings.selectors.dashboard import get_bookings_dashboard_metrics


@staff_required
def panel_home(request):
    metrics = get_bookings_dashboard_metrics()
    return render(
        request,
        "dashboard/panel.html",
        {"metrics": metrics},
    )


@staff_required
def module_placeholder(request, module_name: str):
    return render(
        request,
        "dashboard/module_placeholder.html",
        {"module_name": module_name},
    )
