# website — granice odpowiedzialności

## Cel aplikacji

**Kanał publiczny i self-service klienta** — prezentacja floty, wyszukiwanie dostępności, składanie rezerwacji, płatność online (inicjacja), portal dokumentów i historii.

---

## Co robi (IN scope)

- Widoki publiczne pod `/` (osobny layout od `/panel/`)
- Lista floty, filtry kategorii — dane przez selektory `fleet`
- Wyszukiwanie dostępności (daty) — `fleet.AvailabilityService`
- Formularz rezerwacji — orkiestracja: `PricingService` → `ReservationService`
- Inicjacja płatności online — `payments.PaymentGatewayService`
- Portal klienta (zalogowany `customer`): historia rezerwacji, pobranie dokumentów (linki `documents`)
- SEO-friendly strony statyczne (regulamin, kontakt) — szablony w tej app
- Rate limiting / podstawowa ochrona formularzy publicznych
- **Chat AI — konsultant klienta** (widget + endpoint wiadomości) — patrz [`../../docs/AI_CONSULTANT.md`](../../docs/AI_CONSULTANT.md)

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

### Chat AI (planowane)

- `ChatSession` — sesja (anonimowa lub powiązana z `User` role=customer)
- `ChatMessage` — rola user/assistant/system, treść, timestamp (audyt)

---

## Serwisy (planowane)

- `PublicBookingOrchestrator` — jeden punkt wejścia: search → quote → reserve → payment intent
- Opcjonalnie `CustomerPortalService` — lista dokumentów do pobrania (selektory `documents` + auth)
- `ConsultantChatService` — orchestracja czatu: kontekst → LLM → odpowiedź; wywołania **read-only** do innych app
- `adapters/llm.py` — `LLMClient` (interfejs), implementacja providera z env (`OPENAI_API_KEY` itd.)

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
