from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str


class LLMClientError(Exception):
    """Błąd komunikacji lub odpowiedzi zewnętrznego LLM."""


class LLMClient(Protocol):
    """Kontrakt klienta LLM — implementacje wymienialne (mock, OpenAI, …)."""

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> LLMResponse: ...


class MockLLMClient:
    """Deterministyczny mock dla dev/test — odpowiedzi oparte na slowach kluczowych."""

    provider_name = "mock"

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        del max_tokens
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        last = user_messages[-1].lower() if user_messages else ""

        if "kaucj" in last:
            return LLMResponse(
                content=(
                    "Kaucja jest blokowana na karcie i zwracana po zakonczeniu "
                    "wynajmu, jesli auto zostanie oddane bez uszkodzen. "
                    "Szczegoly znajdziesz w regulaminie."
                ),
            )
        if "rezerw" in last or "zarezerw" in last:
            return LLMResponse(
                content=(
                    "Rezerwacji dokonasz przez formularz online: sprawdz dostepnosc, "
                    "zobacz wycene i wypelnij dane kontaktowe. "
                    "Nie wymagamy konta — wystarczy e-mail lub telefon."
                ),
            )
        if "anul" in last:
            return LLMResponse(
                content=(
                    "Zasady anulowania rezerwacji opisuje regulamin. "
                    "W razie watpliwosci skontaktuj sie z nami przez strone Kontakt."
                ),
            )
        return LLMResponse(
            content=(
                "Dziekuje za pytanie. Jestem asystentem wypozyczalni samochodow — "
                "moge pomoc w kwestiach rezerwacji, kaucji i ogolnych zasad wynajmu. "
                "Nie moge tworzyc rezerwacji ani przyjmowac platnosci w czacie."
            ),
        )


class OpenAICompatibleLLMClient:
    """Klient Chat Completions zgodny z OpenAI API (OpenAI, LiteLLM, proxy)."""

    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        default_max_tokens: int,
    ) -> None:
        if not api_key.strip():
            msg = "LLM_API_KEY jest wymagany dla providera openai"
            raise ValueError(msg)
        self._api_key = api_key.strip()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._default_max_tokens = default_max_tokens

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens or self._default_max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                status = getattr(response, "status", 200)
                raw = response.read()
        except urllib.error.HTTPError as exc:
            logger.warning(
                "LLM HTTP error provider=%s status=%s",
                self.provider_name,
                exc.code,
            )
            msg = f"LLM HTTP {exc.code}"
            raise LLMClientError(msg) from exc
        except urllib.error.URLError as exc:
            logger.warning(
                "LLM connection error provider=%s",
                self.provider_name,
            )
            msg = "LLM connection failed"
            raise LLMClientError(msg) from exc
        except TimeoutError as exc:
            logger.warning("LLM timeout provider=%s", self.provider_name)
            msg = "LLM request timed out"
            raise LLMClientError(msg) from exc

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("LLM invalid JSON provider=%s", self.provider_name)
            msg = "LLM returned invalid JSON"
            raise LLMClientError(msg) from exc

        content = self._extract_content(data)
        if not content:
            logger.warning(
                "LLM empty content provider=%s status=%s",
                self.provider_name,
                status,
            )
            msg = "LLM returned empty content"
            raise LLMClientError(msg)
        return LLMResponse(content=content)

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        return content.strip() if isinstance(content, str) else ""


def get_llm_client() -> LLMClient:
    provider = (settings.LLM_PROVIDER or "mock").strip().lower()
    if provider == "mock":
        return MockLLMClient()
    if provider in {"openai", "openai_compatible"}:
        return OpenAICompatibleLLMClient(
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            default_max_tokens=settings.LLM_MAX_TOKENS,
        )
    msg = f"Nieznany provider LLM: {provider}"
    raise ValueError(msg)
