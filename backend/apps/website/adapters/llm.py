from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from django.conf import settings


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str


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


def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER
    if provider == "mock":
        return MockLLMClient()
    msg = f"Nieznany provider LLM: {provider}"
    raise ValueError(msg)
