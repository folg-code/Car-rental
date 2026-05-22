# AI konsultant klienta (chatbot)

Publiczny asystent konwersacyjny na stronie wynajmu — odpowiada na pytania i pomaga w wyborze auta / rezerwacji. **Nie zastępuje** formularza rezerwacji ani płatności.

Powiązane dokumenty: [`AGENT_CONTEXT.md`](../AGENT_CONTEXT.md), [`backend/ARCHITECTURE.md`](../backend/ARCHITECTURE.md), [`backend/apps/website/README.md`](../backend/apps/website/README.md).

---

## Cel biznesowy

- Obniżyć barierę kontaktu (24/7 FAQ po polsku).
- Prowadzić klienta: daty → dostępne auta → szacunek ceny → link do rezerwacji.
- Odciążyć obsługę od powtarzalnych pytań (kaucja, dokumenty, godziny).

---

## Umiejscowienie w architekturze

| Warstwa | Lokalizacja |
|---------|-------------|
| UI (widget, strona `/asystent/`) | `website` — szablony + HTMX/fetch |
| Orkiestracja | `website.services.consultant_chat.ConsultantChatService` |
| Zewnętrzne API LLM | `website.adapters.llm` (adapter, nie logika domenowa) |
| Persystencja rozmów | `website.models` — `ChatSession`, `ChatMessage` |
| Dane operacyjne | **Tylko odczyt** przez selektory/serwisy: `fleet`, `bookings`, `pricing` |

**Nie** tworzymy osobnej aplikacji Django — moduł żyje w `website`, zgodnie z kanałem publicznym.

---

## Co chatbot może / nie może

### Może (IN scope)

- FAQ firmy (regulamin, kaucja, wiek kierowcy, paliwo — treści z config/FAQ w DB lub markdown).
- Zapytanie o dostępność: klient podaje daty → `AvailabilityService` + lista aut.
- Orientacyjna wycena: `PricingService.calculate` → opis słowny (z disclaimerem).
- Link do formularza rezerwacji z parametrami (`?from=&to=&car=`).
- Zalogowany klient: status **własnej** rezerwacji (selektor `bookings`, bez innych klientów).

### Nie może (OUT of scope)

- Utworzenie/anulowanie rezerwacji bez przejścia przez `ReservationService`.
- Init płatności, zwroty, faktury.
- Dane wewnętrzne (panel, marże, lista wszystkich klientów).
- Porady prawne/księgowe wykraczające poza szablony polityki firmy.
- Gwarancja ceny — tylko rezerwacja ze snapshotem `PriceLine` jest wiążąca.

---

## Przepływ techniczny

```text
1. Klient wysyła wiadomość (POST /asystent/wiadomosc/ lub HTMX)
2. ConsultantChatService:
   a. Pobierz/utwórz ChatSession (cookie session_id lub user_id)
   b. Zapisz ChatMessage (role=user)
   c. Zbuduj kontekst: ostatnie N wiadomości + FAQ + (opcjonalnie) wynik tool calls
   d. Wywołaj LLMClient.complete(messages, tools?)
   e. Jeśli tool_call: wykonaj read-only (np. search_cars) → ponowne complete
   f. Zapisz ChatMessage (role=assistant)
   g. Zwróć fragment HTML/JSON do UI
3. Rate limit per IP / per session (np. django-ratelimit lub cache)
```

---

## Adapter LLM

```python
# website/adapters/llm.py — kontrakt (szkic)

class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...
```

- Implementacja: OpenAI-compatible API (konfiguracja przez env).
- Klucze API **tylko** w `.env` / secrets — nigdy w repo.
- Timeout, retry z backoff, max tokens — w adapterze.
- Logowanie request_id; **nie** logować pełnej treści wiadomości z PII na produkcji (lub maskowanie).

Zmienne env (planowane):

```env
LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=1024
CHAT_RATE_LIMIT_PER_HOUR=30
```

---

## Tool calling (read-only)

Funkcje udostępniane modelowi — implementacja woła serwisy domenowe:

| Tool | Wywołuje | Zwraca |
|------|----------|--------|
| `search_available_cars` | `AvailabilityService`, selektory `fleet` | Lista aut (marka, kategoria, cena od) |
| `estimate_price` | `PricingService` | Orientacyjny koszt (bez zapisu) |
| `get_my_reservation_status` | `bookings` selektor (user zalogowany) | Status rezerwacji klienta |
| `get_faq_snippet` | FAQ w DB / pliku | Fragment regulaminu |

Model **nie** dostaje surowego SQL ani querysetów — tylko wynik JSON z serwisu.

---

## Bezpieczeństwo i RODO

- Informacja na starcie: „Rozmowa z asystentem AI; nie podawaj numeru PESEL w czacie”.
- Retencja `ChatMessage`: polityka retention (np. 90 dni) — do ustalenia.
- Anonimowe sesje: powiązanie z cookie, opcjonalnie merge po logowaniu.
- Moderacja: lista zakazanych tematów w system prompt; opcjonalnie filter odpowiedzi.
- CSRF na POST; throttle anty-spam.

---

## UI

- Widget na dole strony (publiczny layout `base.html`) — przycisk „Pomoc / Chat”.
- Pełna strona `/asystent/` dla dłuższych rozmów.
- HTMX: partial update listy wiadomości (spójne z resztą projektu).
- Mobile-first, czytelne bąbelki, wskaźnik „pisze…”.

---

## Zależności od innych sprintów

| Sprint | Wymagane dla pełnej funkcji chatu |
|--------|-----------------------------------|
| 2 fleet | Wyszukiwanie dostępnych aut |
| 3 bookings | Status rezerwacji klienta |
| 4 pricing | Orientacyjne wyceny |
| 8 website | Layout publiczny, widget, routing |

**MVP chatu (Sprint 8b):** samo FAQ + ogólne odpowiedzi bez tool calls — można wdrożyć wcześniej; rozszerzenie o tools po sprintach 3–4.

---

## Testy (planowane)

- Mock `LLMClient` — deterministyczne odpowiedzi w pytest.
- `ConsultantChatService` — zapis wiadomości, limit historii.
- Tool `search_available_cars` — integracja z `AvailabilityService` (db).
- Rate limit — przekroczenie zwraca 429.
- Brak wycieku: anonimowa sesja nie wywołuje `get_my_reservation_status`.

---

## Metryki (opcjonalnie, później)

- Liczba sesji / dzień, średnia długość rozmowy.
- Konwersja: sesja chat → otwarcie formularza rezerwacji.
- Eskalacja do kontaktu ludzkiego (przycisk „Zadzwoń / email”).
