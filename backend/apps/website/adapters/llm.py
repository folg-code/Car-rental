from __future__ import annotations

import json
import logging
import unicodedata
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
    """Deterministyczny mock dla demo/dev — odpowiedzi po intencji (PL)."""

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
        folded = self._fold(last)

        if self._any(folded, ("czesc", "cześć", "hej", "dzien dobry", "dzień dobry")):
            return LLMResponse(
                content=(
                    "Cześć! Mogę pomóc z dostępnością aut, orientacyjną wyceną, "
                    "kaucją i zasadami wynajmu. Podaj termin (np. „jutro” albo "
                    "„weekend”) albo wybierz jedno z przykładowych pytań."
                ),
            )
        if self._any(folded, ("dzieki", "dzięki", "dziekuje", "dziękuję")):
            return LLMResponse(
                content=(
                    "Nie ma za co. Jeśli chcesz, sprawdź dostępność albo "
                    "przejdź do formularza rezerwacji na stronie."
                ),
            )
        if self._any(folded, ("kontakt", "telefon", "mail", "email", "e-mail")):
            return LLMResponse(
                content=(
                    "Dane kontaktowe znajdziesz na stronie Kontakt. "
                    "W czacie odpowiadam na pytania o flotę, ceny i zasady — "
                    "rezerwacji i płatności nie finalizuję tutaj."
                ),
            )
        if self._any(folded, ("kaucj", "depozyt")):
            return LLMResponse(
                content=(
                    "Kaucja jest blokowana na karcie przy wydaniu i zwracana "
                    "po rozliczeniu zwrotu, jeśli auto wróci bez uszkodzeń "
                    "i dopłat. Wysokość zależy od kategorii — zapytaj np. "
                    "„ile kaucji za SUV?” albo zajrzyj do regulaminu."
                ),
            )
        if self._any(folded, ("dokument", "prawo jazdy", "dowod", "dowód")):
            return LLMResponse(
                content=(
                    "Do odbioru potrzebujesz ważnego prawa jazdy kat. B "
                    "oraz dokumentu tożsamości. Szczegóły wieku i stażu "
                    "kierowcy są w regulaminie."
                ),
            )
        if self._any(folded, ("wiek", "ile lat", "mlody", "młody")):
            return LLMResponse(
                content=(
                    "Wynajem jest dla osób pełnoletnich z ważnym prawem jazdy. "
                    "Niektóre kategorie mogą mieć wyższy limit wieku lub stażu — "
                    "sprawdź regulamin przed rezerwacją."
                ),
            )
        if self._any(folded, ("paliw", "tankow", "bak")):
            return LLMResponse(
                content=(
                    "Oddajesz auto z poziomem paliwa zgodnym z protokołem "
                    "wydania. Niedobór może oznaczać dopłatę przy zwrocie."
                ),
            )
        if self._any(folded, ("godzin", "otwarcia", "biuro")):
            return LLMResponse(
                content=(
                    "Termin odbioru i zwrotu wybierasz przy rezerwacji. "
                    "Jeśli nie podasz godziny, przyjmuję domyślnie 10:00. "
                    "Godziny biura — strona Kontakt."
                ),
            )
        if self._any(folded, ("anul", "odwol", "odwoł")):
            return LLMResponse(
                content=(
                    "Zasady anulowania rezerwacji opisuje regulamin. "
                    "W razie wątpliwości skorzystaj ze strony Kontakt."
                ),
            )
        if self._any(folded, ("rezerw", "zarezerw", "jak wynaj")):
            return LLMResponse(
                content=(
                    "Rezerwacji dokonasz przez formularz online: sprawdź "
                    "dostępność → wycena → dane kontaktowe → płatność. "
                    "Konta nie wymagamy. Mogę też sprawdzić wolne auta — "
                    "napisz termin, np. „wolne auta na jutro”."
                ),
            )
        if self._any(folded, ("kategori", "jakie auta", "jaka flota", "rodzaje")):
            return LLMResponse(
                content=(
                    "We flocie są m.in. kategorie kompakt, SUV, premium "
                    "i rodzinne. Mogę sprawdzić dostępność na termin albo "
                    "podać kaucję dla wybranej kategorii."
                ),
            )
        return LLMResponse(
            content=(
                "Jestem asystentem wypożyczalni — pomagam z dostępnością, "
                "wyceną orientacyjną, kaucją i zasadami wynajmu. "
                "Nie tworzę rezerwacji ani nie przyjmuję płatności w czacie. "
                "Spróbuj: „wolne auta na jutro”, „ile kaucji za SUV” "
                "albo „jakie dokumenty są potrzebne?”."
            ),
        )

    @staticmethod
    def _fold(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @staticmethod
    def _any(folded: str, keywords: tuple[str, ...]) -> bool:
        return any(MockLLMClient._fold(keyword) in folded for keyword in keywords)


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
