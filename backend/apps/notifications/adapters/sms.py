from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SmsSendResult:
    external_id: str


class SmsClient(Protocol):
    """Kontrakt dostawcy SMS — implementacje wymienialne (mock, Twilio, …)."""

    provider_name: str

    def send_message(
        self,
        *,
        to: str,
        body: str,
        from_number: str,
    ) -> SmsSendResult: ...


class NoOpSmsClient:
    """Gdy SMS wylaczone — nic nie wysyla."""

    provider_name = "disabled"

    def send_message(
        self,
        *,
        to: str,
        body: str,
        from_number: str,
    ) -> SmsSendResult:
        del to, body, from_number
        msg = "SMS wylaczone (SMS_ENABLED=False)"
        raise RuntimeError(msg)


class MockSmsClient:
    """Mock dostawcy dla dev/test — loguje tresc bez zewnetrznego API."""

    provider_name = "mock"

    def send_message(
        self,
        *,
        to: str,
        body: str,
        from_number: str,
    ) -> SmsSendResult:
        external_id = f"mock_sms_{uuid.uuid4().hex[:12]}"
        logger.info(
            "Mock SMS [%s -> %s]: %s",
            from_number,
            to,
            body[:160],
        )
        return SmsSendResult(external_id=external_id)


class TwilioSmsClient:
    """Stub Twilio — wymaga credentials w settings (Sprint prod)."""

    provider_name = "twilio"

    def __init__(
        self,
        *,
        account_sid: str,
        auth_token: str,
    ) -> None:
        self._account_sid = account_sid
        self._auth_token = auth_token

    def send_message(
        self,
        *,
        to: str,
        body: str,
        from_number: str,
    ) -> SmsSendResult:
        del to, body, from_number
        msg = (
            "Twilio SMS nie jest jeszcze skonfigurowany. "
            "Ustaw SMS_PROVIDER=mock lub dodaj integracje Twilio."
        )
        raise NotImplementedError(msg)


def get_sms_client() -> SmsClient:
    if not settings.SMS_ENABLED:
        return NoOpSmsClient()
    provider = settings.SMS_PROVIDER
    if provider == "mock":
        return MockSmsClient()
    if provider == "twilio":
        return TwilioSmsClient(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
        )
    msg = f"Nieznany provider SMS: {provider}"
    raise ValueError(msg)
