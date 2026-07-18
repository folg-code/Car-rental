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
# website/adapters/llm.py

class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
    ) -> LLMResponse: ...
```

Implementacje:

| `LLM_PROVIDER` | Klient | Uwagi |
|----------------|--------|--------|
| `mock` (default) | `MockLLMClient` | Deterministyczne odpowiedzi po słowach kluczowych — bez sieci |
| `openai` / `openai_compatible` | `OpenAICompatibleLLMClient` | HTTP `POST {LLM_BASE_URL}/chat/completions` (OpenAI, LiteLLM, kompatybilne proxy) |

- Klucze API **tylko** w `.env` / secrets — nigdy w repo.
- Timeout (`LLM_TIMEOUT_SECONDS`), `max_tokens` — w adapterze.
- Błędy HTTP/timeout → `LLMClientError` → w serwisie komunikat dla użytkownika (bez logowania treści PII).

Zmienne env:

```env
LLM_PROVIDER=mock
# LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=1024
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_SECONDS=30
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

## Plan dopracowania asystenta

Obecny problem UX: asystent odpowiada zbyt generycznie na pytania typu „czy są wolne auta na jutro?” albo „sprawdź dostępność samochodów”. Docelowo ma rozpoznawać intencję, zebrać brakujące dane i przeprowadzić klienta do rezerwacji.

### Intencje do obsłużenia

| Intencja klienta | Przykłady | Oczekiwane zachowanie |
|------------------|-----------|------------------------|
| Dostępność aut | „czy są wolne auta na jutro”, „sprawdź dostępność samochodów” | Jeśli brakuje dat/godzin — dopytaj. Jeśli daty są jasne — użyj `search_available_cars` i pokaż dostępne auta/kategorie. |
| Cena / kaucja | „ile kosztuje SUV na weekend”, „jaka kaucja za kombi” | Użyj `estimate_price` albo FAQ/kategorii auta; jasno oznacz wycenę jako orientacyjną. |
| Zasady wynajmu | „czy mogę oddać po godzinach”, „jakie dokumenty są potrzebne” | Odpowiedz z FAQ/polityk firmy, bez wymyślania warunków. |
| Status rezerwacji | „co z moją rezerwacją” | Dla zalogowanego klienta: tylko jego dane; anonimowego skieruj do panelu klienta/logowania po rezerwacji. |
| Przejście do rezerwacji | „chcę zarezerwować”, „wezmę to auto” | Podaj link do formularza rezerwacji z parametrami, ale nie twórz rezerwacji w czacie. |

### Daty i doprecyzowanie

- Obsłużyć daty względne po polsku: „jutro”, „pojutrze”, „w weekend”, „od piątku do niedzieli”.
- Jeśli użytkownik poda tylko dzień, dopytać o godzinę odbioru i zwrotu albo użyć bezpiecznej domyślnej pary godzin z konfiguracji.
- Jeśli pytanie brzmi tylko „sprawdź dostępność samochodów”, asystent powinien zapytać: „Na jaki termin mam sprawdzić dostępność?” zamiast odpowiadać ogólnikiem.
- Jeśli brak kategorii auta, pokazać kilka kategorii lub zapytać o preferencję: małe, rodzinne, SUV, dostawcze.

### Wynik dla klienta

Dobra odpowiedź asystenta powinna zawierać:

1. krótkie potwierdzenie zrozumienia pytania,
2. ewentualne pytanie doprecyzowujące albo listę wyników,
3. cenę/kaucję tylko wtedy, gdy da się ją policzyć,
4. link lub CTA do formularza rezerwacji,
5. informację, że rezerwacja i płatność odbywają się poza czatem.

### Przykładowe scenariusze testowe

- „czy są wolne auta na jutro” → asystent rozpoznaje datę względną, dopytuje o godzinę albo pokazuje dostępność dla domyślnych godzin.
- „sprawdź dostępność samochodów” → asystent dopytuje o termin.
- „ile kaucji za SUV” → asystent odpowiada na podstawie kategorii/FAQ.
- „chcę zarezerwować auto rodzinne na weekend” → asystent prowadzi do wyboru terminu i linku rezerwacji.
- Anonimowy klient pyta o status rezerwacji → asystent nie ujawnia danych, kieruje do panelu klienta.

### Implementacja (Sprint 12.1)

Heurystyczny router (`ChatToolRouter`) rozpoznaje:

- daty ISO oraz względne: `jutro`, `pojutrze`, `dzisiaj`, `weekend`, `od piątku do niedzieli`;
- brak terminu przy pytaniu o dostępność/cenę → tool `ask_clarifying_question`;
- kaucję wg kategorii → tool `get_deposit_info` (pole `CarCategory.deposit`);
- domyślne godziny odbioru/zwrotu: `CHAT_DEFAULT_PICKUP_HOUR` / `CHAT_DEFAULT_RETURN_HOUR` (domyślnie 10).

Scenariusze pokryte testami w `test_chat_tool_router.py` oraz `test_consultant_tools_integration.py`.

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
