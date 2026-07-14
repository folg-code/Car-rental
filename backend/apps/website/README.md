# website — granice odpowiedzialności

## Cel aplikacji

**Kanał publiczny i self-service klienta** — prezentacja floty, wyszukiwanie dostępności, składanie rezerwacji, płatność online (inicjacja), portal dokumentów i historii.

Plan sprintu: [`../../../PROJECT_PLAN.md`](../../../PROJECT_PLAN.md) — Sprint 8, taski **8.8–8.14**.  
Chat AI: Sprint **8b** — [`../../../docs/AI_CONSULTANT.md`](../../../docs/AI_CONSULTANT.md).

---

## Co robi (IN scope)

- Widoki publiczne pod `/` (osobny layout od `/panel/`)
- Lista floty, filtry kategorii — dane przez selektory `fleet`
- Wyszukiwanie dostępności (daty) — `fleet.AvailabilityService`
- Formularz rezerwacji — orkiestracja: `PricingService` → `ReservationService`
- Inicjacja płatności online — `PublicPaymentOrchestrator` → `PaymentGatewayService` (task **9.5** ✅)
- Portal klienta (zalogowany `customer`): historia rezerwacji, pobranie dokumentów (linki `documents`) — backlog Sprint 8
- SEO-friendly strony statyczne (regulamin, kontakt) — szablony w tej app
- Rate limiting / podstawowa ochrona formularzy publicznych

---

## Sprint 8 — taski implementacji

| ID | Task | Pliki (plan) | Status |
|----|------|--------------|--------|
| **8.8** | Infrastruktura | `urls.py`, `views.py`, `templates/website/base_public.html`, routing w `config/urls.py` | ✅ |
| **8.9** | Katalog floty | `/flota/` — selektory `fleet`, szablon listy | ✅ |
| **8.10** | Wyszukiwarka dostępności | formularz dat → `AvailabilityService` | ✅ |
| **8.11** | Orientacyjna wycena | `PricingService.calculate()` read-only na stronie | ✅ |
| **8.12** | Rezerwacja online | `services/public_booking.py` → `ReservationService` | ✅ |
| **8.13** | Strony informacyjne | regulamin, kontakt, FAQ (placeholdery) | ✅ |
| **8.14** | Testy | `tests/test_public_flow.py` + istniejace testy widokow | ✅ |

### Stan wyjściowy

- Aplikacja `website` w `INSTALLED_APPS`
- Kanał publiczny kompletny (taski **8.8–8.14**)
- Test integracyjny: dostepnosc → wycena → rezerwacja → potwierdzenie

---

## Czego nie robi (OUT of scope)

| Obszar | Właściwa aplikacja |
|--------|-------------------|
| Definicja auta, zdjęć, cennika | `fleet`, `pricing` |
| Trwały zapis rezerwacji / PriceLine | `bookings` |
| Webhook bramki płatności | `payments` |
| PDF, email | `documents` |
| Protokół wydania/zwrotu | `operations` |
| Panel wewnętrzny pracownika | `dashboard` |
| Role i hasła pracowników | `accounts` |

**Zasada:** `website` to **cienka warstwa prezentacji + orkiestracja** wywołań serwisów domenowych.

---

## Modele (planowane)

Minimalne — np. `ContactFormSubmission`, `Page` (CMS light).  
**Brak** duplikacji `Car`, `Reservation`, `Customer`.

### Chat AI (Sprint 8b — Faza A ✅)

- `ChatSession`, `ChatMessage` — modele + migracja `website.0001_chat_models`
- `adapters/llm.py` — `LLMClient`, `MockLLMClient`, `get_llm_client()`
- `ConsultantChatService` — FAQ-only, rate limit (cache), system prompt
- `/asystent/` + widget „Pomoc / Chat” w `base_public.html`
- Env: `LLM_PROVIDER`, `CHAT_RATE_LIMIT_PER_HOUR` — [`docs/AI_CONSULTANT.md`](../../../docs/AI_CONSULTANT.md)

### Chat AI (Sprint 8b — Faza B ✅)

- `services/chat_tools.py` — read-only tools + deep link do rezerwacji
- `services/chat_tool_router.py` — heurystyki (mock provider) → tool calls
- Tooli: `search_available_cars`, `estimate_price`, `get_my_reservation_status`, `get_faq_snippet`

### Chat AI (opcjonalnie)

## Serwisy (planowane)

- `PublicBookingOrchestrator` — jeden punkt wejścia: search → quote → reserve (Task **8.12**)
- Opcjonalnie `CustomerPortalService` — lista dokumentów do pobrania (selektory `documents` + auth)
- `ConsultantChatService` — Sprint 8b Faza A ✅ — orchestracja czatu (FAQ-only)
- `adapters/llm.py` — Sprint 8b Faza A ✅ — `LLMClient` z env

Logika biznesowa w serwisach **innych** app — `website` tylko koordynuje.

---

## Zależności

| Kierunek | Aplikacja | Powód |
|----------|-----------|--------|
| → wywołuje | `fleet`, `pricing`, `bookings`, `payments`, `documents` | Publiczny flow |
| ← | `accounts` | Login klienta |
| → nie mutuje bezpośrednio | Tabele `bookings` / `payments` | Tylko przez serwisy |

---

## Reguły integracji

- Publiczny POST rezerwacji nigdy nie zapisuje `PriceLine` ręcznie — zawsze przez `bookings` + wynik `pricing`.
- Callback płatności: URL w `payments`, nie w `website` (website może mieć stronę „thank you”).
- Dane wrażliwe (PESEL, pełne dane) — minimalizacja na publicznym formularzu; reszta w `bookings.Customer`.

---

## Antywzorce

- Kalkulacja ceny w widoku szablonu
- Model `Payment` w `website`
- Omijanie `ReservationService` przy zapisie z formularza
- Kopiowanie querysetów floty z duplikacją filtrów dostępności
- Tworzenie rezerwacji lub płatności bezpośrednio z odpowiedzi LLM
- Wysyłanie do modelu pełnych tabel DB lub danych innych klientów
- Wywołanie API LLM z widoku szablonu (tylko przez `ConsultantChatService` → adapter)
