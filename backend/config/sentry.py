"""Optional Sentry error reporting (enabled when SENTRY_DSN is set)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def init_sentry(
    *,
    dsn: str,
    environment: str,
    release: str = "",
    traces_sample_rate: float = 0.0,
    send_default_pii: bool = False,
) -> bool:
    """
    Initialize the Sentry SDK.

    Returns True when init ran, False when DSN is empty (no-op for local/demo).
    """
    if not dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    options: dict[str, Any] = {
        "dsn": dsn,
        "environment": environment,
        "integrations": [
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        "traces_sample_rate": traces_sample_rate,
        "send_default_pii": send_default_pii,
    }
    if release:
        options["release"] = release

    sentry_sdk.init(**options)
    logger.info("Sentry initialized (environment=%s)", environment)
    return True
