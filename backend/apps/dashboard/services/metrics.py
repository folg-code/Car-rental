from __future__ import annotations

from datetime import datetime

from apps.dashboard.selectors.metrics import DashboardMetrics, get_dashboard_metrics


class DashboardMetricsService:
    """Punkt wejścia dla widoków pulpitu — deleguje do selektorów KPI."""

    @staticmethod
    def get_home_metrics(*, as_of: datetime | None = None) -> DashboardMetrics:
        return get_dashboard_metrics(as_of=as_of)
