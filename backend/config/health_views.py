"""Liveness/readiness probe for production monitoring."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


def _ping_database() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def _ping_redis() -> None:
    import redis

    client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
    try:
        client.ping()
    finally:
        client.close()


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    checks: dict[str, str] = {}
    failed = False

    for name, probe in (("database", _ping_database), ("redis", _ping_redis)):
        try:
            probe()
            checks[name] = "ok"
        except Exception as exc:  # noqa: BLE001 — aggregate probe failures for ops
            checks[name] = f"error: {exc}"
            failed = True

    payload: dict[str, Any] = {
        "status": "degraded" if failed else "ok",
        "checks": checks,
    }
    return JsonResponse(payload, status=503 if failed else 200)
