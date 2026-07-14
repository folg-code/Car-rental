from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from apps.payments.selectors.payment import get_revenue_total_in_period


def get_month_revenue(*, as_of: datetime | None = None) -> Decimal:
    """Przychod operacyjny od poczatku biezacego miesiaca do chwili ``as_of``."""
    now = as_of or timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return get_revenue_total_in_period(month_start, now)
