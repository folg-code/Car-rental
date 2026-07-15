from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_returns_ok_when_database_and_redis_are_up() -> None:
    with patch("config.health_views._ping_redis"):
        response = Client().get("/health/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"


@pytest.mark.django_db
def test_health_returns_503_when_redis_is_down() -> None:
    with patch(
        "config.health_views._ping_redis",
        side_effect=ConnectionError("redis unavailable"),
    ):
        response = Client().get("/health/")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "ok"
    assert "redis unavailable" in body["checks"]["redis"]
