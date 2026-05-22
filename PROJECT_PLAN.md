# Plan prac — Car Rental Operations Platform

> **Jak używać tego pliku**
> - Aktualizuj sekcję **Status projektu** po każdej większej zmianie.
> - Zaznaczaj `[x]` przy ukończonych zadaniach; zostaw `[ ]` dla otwartych.
> - Nowe bieżące zadania dopisuj w **Aktywne TODO**; po zakończeniu przenoś do **Zrobione**.
> - Szczegóły architektury i reguły biznesowe: [`AGENT_CONTEXT.md`](./AGENT_CONTEXT.md).
> - Chat AI (konsultant klienta): [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md).

---

## Status projektu

| Pole | Wartość |
|------|---------|
| **Aktualny etap** | Sprint 4 — pricing (kolejny) |
| **Następny krok** | Sprint 4 — `PriceList`, `PricingService`, `PriceLine` |
| **Postęp ogólny** | ~60% (Sprint 0–3 zamkniete) |
| **Ostatnia aktualizacja** | 2026-05-22 |
| **Branch** | `feature/customer` (lub merge do `main`) |
| **Repozytorium** | 4+ commity; `backend/apps/` w repo (commit: *introduce architecture*) |

### Legenda postępu sprintu

- `⬜ nie rozpoczęty`
- `🟡 w toku`
- `✅ ukończony`

| Sprint | Nazwa | Status | Postęp |
|--------|-------|--------|--------|
| 0 | Fundament techniczny | ✅ | 100% |
| 1 | Struktura apps + accounts | ✅ | 100% |
| 2 | fleet (flota) | ✅ | 100% |
| 3 | bookings (rezerwacje) | ✅ | 100% |
| 4 | pricing (cennik + snapshoty) | 🟡 | ~25% |
| 5 | Rental + payments MVP | ⬜ | 0% |
| 6 | operations (wydanie/zwrot) | ⬜ | 0% |
| 7 | documents (PDF, faktury) | ⬜ | 0% |
| 8 | dashboard + website | ⬜ | 0% |
| 8b | Chat AI — konsultant klienta | ⬜ | 0% |
| CI/CD | GitHub Actions (CI + deploy) | ✅ | 100% |
| 9+ | Produkcja i integracje | ⬜ | backlog |

---

## Następne kroki (kolejność)

1. ~~**Integracja Django (Sprint 1a)**~~ ✅
2. ~~**Accounts (Sprint 1b)**~~ ✅
3. ~~**Panel wewnętrzny (Sprint 1c + 1d)**~~ ✅
4. ~~**Sprint 2 — fleet**~~ ✅
5. ~~**Sprint 3 — bookings**~~ ✅
6. **Sprint 4 — pricing** — cennik + snapshoty `PriceLine`
7. **Sprint 5–8** — rental, payments, operations, documents, website
8. **Sprint 8b — Chat AI** — po podstawowym `website` (lub MVP FAQ wcześniej) — [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md)

---

## Aktywne TODO

<!-- Bieżące zadania — edytuj na bieżąco -->

- [ ] Upload zdjec/dokumentow w panelu floty (obecnie admin) — backlog / Sprint 2+

---

## Zrobione (ostatnie)

<!-- Przenoś tu ukończone TODO z sekcji powyżej -->

- [x] Bootstrap Django + PostgreSQL
- [x] Docker Compose (db + web)
- [x] TailwindCSS + HTMX w szablonie bazowym
- [x] Pytest + Ruff + pre-commit
- [x] Dokumentacja architektury (`AGENT_CONTEXT.md`)
- [x] Strona startowa `/` + Django admin
- [x] `PROJECT_PLAN.md` — plan sprintów i śledzenie postępu
- [x] `backend/ARCHITECTURE.md` — przegląd architektury backendu
- [x] 9 aplikacji domenowych + `services/` / `selectors/` (szkielet)
- [x] `README.md` z granicami odpowiedzialności w każdej appce
- [x] Usunięto `apps/core`; struktura zgodna z `AGENT_CONTEXT`
- [x] Commit *introduce architecture* (`backend/apps/`)
- [x] Sprint 1a: `INSTALLED_APPS`, `apps.<nazwa>` w `AppConfig`, `dashboard/apps.py`
- [x] `django check` OK (lokalnie + Docker)
- [x] `migrate` OK w Docker Compose
- [x] Usunięto pozostałości `apps/core/`
- [x] Poprawka ładowania `.env` (`.env.local` nie nadpisuje `POSTGRES_HOST` w Compose)
- [x] Sprint 1b: custom `User`, role, `AUTH_USER_MODEL`, login/logout, `/panel/`
- [x] `UserService`, selektory, testy auth (8 testów, SQLite w pytest)
- [x] Sprint 1c: `base_internal.html`, nawigacja panelu, locale PL, `MEDIA_*` / `STATIC_ROOT`
- [x] Placeholdery URL modułów (`/panel/flota/`, …); `/panel/rezerwacje/` aktywne od Sprint 3
- [x] 12 testów pytest (auth + panel + settings)
- [x] CI/CD: GitHub Actions (`ci.yml` na PR, `deploy.yml` na merge do `main`)
- [x] `Dockerfile.prod`, `docker-compose.prod.yml`, `docs/CICD.md`
- [x] Sprint 2: fleet — modele, panel `/panel/flota/`, `AvailabilityService`, testy (PR #7)
- [x] Sprint 3: `Customer` + migracja `bookings.0001_initial`
- [x] Sprint 3: CRUD klientow `/panel/rezerwacje/klienci/`
- [x] Sprint 3: `Reservation` + statusy + migracja `bookings.0002_reservation`
- [x] Sprint 3: `ReservationService` (create, confirm, cancel, expire, update)
- [x] Sprint 3: integracja dostepnosci z `fleet` (`get_car_busy_intervals`, `exclude_reservation_id`)
- [x] Sprint 3: CRUD rezerwacji `/panel/rezerwacje/` (lista, formularz, potwierdz, anuluj)
- [x] Sprint 3: testy bookings (~27: model, serwis, widoki klientow i rezerwacji)
- [x] Sprint 3: UI „Wygas” rezerwacje + metryki pulpitu (rezerwacje, wolne auta, koniec w 7 dni)
- [x] Sprint 3: `manage.py seed_demo` (kategorie, 3 auta, 2 klientow, przykladowa rezerwacja)
- [x] Sprint 3 — **zamkniety** (Definition of Done spelnione)

---

## Dziennik postępów

<!-- Krótkie wpisy: data — co zrobiono -->

| Data | Sprint | Opis |
|------|--------|------|
| 2026-05-20 | 0 | Utworzono plan prac; potwierdzono stan: infrastruktura gotowa, domena 0% |
| 2026-05-20 | 1 | Architektura backendu: 9 apps, README granic, ARCHITECTURE.md, szkielet services/selectors |
| 2026-05-20 | 1 | Naprawiono kodowanie `__init__.py` (UTF-8); usunięto boilerplate Django z pustych modułów |
| 2026-05-20 | 1a | Integracja Django: `INSTALLED_APPS`, `apps.*` w `AppConfig`, migrate w Docker |
| 2026-05-20 | 1c | `base_internal.html`, nawigacja, PL locale, MEDIA/STATIC, 12 testów — Sprint 1 zamknięty |
| 2026-05-20 | 2 | Fleet: modele, panel, AvailabilityService, merge PR #7 |
| 2026-05-22 | 3 | Bookings: Customer + Reservation, serwisy, panel CRUD, testy |
| 2026-05-22 | 3 | Domkniecie Sprint 3: wygaszenie UI, seed_demo, metryki pulpitu |
| | | |

---

## Blokery i notatki

<!-- Problemy, decyzje, ryzyka -->

| Data | Opis | Status |
|------|------|--------|
| 2026-05-20 | `apps/core` — konflikt ze strukturą docelową | **zamknięty** (usunięty) |
| 2026-05-20 | Apps nie w `INSTALLED_APPS` | **zamknięty** |
| 2026-05-20 | `apps.py` — błędne `name` | **zamknięty** |
| 2026-05-20 | `dashboard` bez `apps.py` | **zamknięty** |
| | | |

---

# Sprint 0 — Fundament techniczny ✅

**Cel:** działające środowisko dev bez logiki biznesowej.

### Infrastruktura

- [x] Projekt Django 6 + `config`
- [x] PostgreSQL przez `django-environ`
- [x] Docker Compose (`db`, `web`)
- [x] Pliki `.env` / `.env.docker` / `.env.local`
- [x] `Dockerfile` + `pyproject.toml`

### Frontend / UI

- [x] `base.html` + Tailwind (`output.css`)
- [x] HTMX w szablonie
- [x] Widok `home` na `/`

### Jakość kodu

- [x] Pytest + `pytest-django`
- [x] Ruff + pre-commit
- [x] Test placeholder (`tests/test_example.py`)

### Dokumentacja

- [x] `AGENT_CONTEXT.md` — pełna specyfikacja systemu

**Definition of Done:** `docker compose up` uruchamia app; migracje przechodzą; testy przechodzą.

---

# Sprint 1 — Struktura aplikacji + accounts ✅

**Cel:** gotowa baza pod domenę — auth, layout wewnętrzny, konwencje kodu.

### Struktura projektu

- [x] Uporządkować `backend/apps/` (usunięto `core`, 9 appów domenowych)
- [x] Szkielet katalogów: `services/`, `selectors/` we wszystkich appkach (oprócz `dashboard` — do uzupełnienia)
- [x] `README.md` — granice odpowiedzialności per app (co robi / czego nie robi)
- [x] `backend/ARCHITECTURE.md` — mapa zależności i konwencje
- [x] Commit struktury apps (*introduce architecture*)
- [x] Konwencja `apps.<nazwa>` w `INSTALLED_APPS` i `AppConfig.name`
- [x] Uzupełnić szkielet `apps/dashboard/` (`apps.py`)
- [x] `django check` + migracje Django (admin/auth) w Docker

### App `accounts`

- [x] Model użytkownika (`User` + `UserRole`)
- [x] Role: owner, manager, employee, accountant, customer
- [x] Login / logout (`/konto/logowanie/`, `/konto/wylogowanie/`)
- [x] `AUTH_USER_MODEL`, `UserService`, selektory, `@staff_required`
- [x] Migracja `accounts.0001_initial`
- [x] Testy logowania i dostępu do panelu

### Ustawienia i UI

- [x] `base_internal.html` — layout panelu (sidebar + header)
- [x] Nawigacja wewnętrzna + placeholdery `/panel/flota/`, …
- [x] `LANGUAGE_CODE=pl`, `TIME_ZONE=Europe/Warsaw`
- [x] `MEDIA_ROOT`, `MEDIA_URL`, `STATIC_ROOT`, serwowanie media w DEBUG
- [x] `ALLOWED_HOSTS` z env, `DEBUG` z env, szkic komentarza dev/prod

### Testy

- [x] Test logowania
- [x] Test dostępu do widoku wewnętrznego
- [x] Test layoutu panelu i ustawień locale/media

**Definition of Done:** zalogowany pracownik widzi pusty panel wewnętrzny; migracje w Dockerze OK.

### Podział prac (Sprint 1)

| Faza | Zakres | Status |
|------|--------|--------|
| 1a | Integracja Django (`INSTALLED_APPS`, `apps.py`, `dashboard`) | ✅ |
| 1b | `accounts` — model, role, auth | ✅ |
| 1c | Panel `/panel/` — layout + routing | ✅ |
| 1d | Ustawienia locale/media + testy | ✅ |

---

# Sprint 2 — fleet (flota) ✅

**Cel:** zarządzanie pojazdami i blokadami dostępności (~15 aut).

### Modele

- [x] `CarCategory`
- [x] `Car`
- [x] `CarImage`
- [x] `CarDocument`
- [x] `AvailabilityBlock`
- [x] `Damage` (historia globalna, niezależna od protokołów)
- [x] `DamagePhoto`
- [x] `RepairRecord`
- [x] Migracja `fleet.0001_initial`

### UI / admin

- [x] CRUD aut w panelu (`/panel/flota/`)
- [x] CRUD kategorii
- [x] Blokady dostępności (dodawanie/usuwanie)
- [x] Rejestracja uszkodzen
- [x] Django admin (wszystkie modele)

### Logika

- [x] `AvailabilityService` — dostępność **wyliczana**, bez `is_available`
- [x] `FleetMaintenanceService`, `DamageService`, `CarService`
- [x] Selektory (`car`, `availability`)
- [x] Hook pod `bookings` (`get_booking_busy_intervals` — aktywny od Sprint 3)

### Testy

- [x] Nakładające się `AvailabilityBlock` — odrzucenie
- [x] `is_car_available` z blokada i statusem auta
- [x] Widoki panelu (9 testow fleet)

**Definition of Done:** pełna flota w systemie; ręczna blokada serwisowa działa.

---

# Sprint 3 — bookings (rezerwacje + klienci) ✅

**Cel:** intent rezerwacji z walidacją dostępności.

### Modele

- [x] `Customer` — `bookings.0001_initial`, `CustomerService`, admin
- [x] `Reservation` + statusy: draft, pending_payment, confirmed, cancelled, expired, converted_to_rental — `bookings.0002_reservation`

### UI

- [x] Panel `/panel/rezerwacje/` — lista rezerwacji + filtr statusu
- [x] Formularz tworzenia/edycji rezerwacji (auto + daty + klient + status)
- [x] Potwierdzanie i anulowanie (z powodem) na szczegółach rezerwacji
- [x] CRUD klientow `/panel/rezerwacje/klienci/` (zakładki Rezerwacje | Klienci)
- [x] UI akcji „Wygas rezerwacje” (`/wygas/` + przycisk na szczegolach)

### Logika

- [x] `ReservationService` — create, confirm, cancel, expire, update
- [x] `CustomerService`, selektory (`customer`, `reservation`, `availability`)
- [x] Walidacja dostępności przez `AvailabilityService` + nakładanie rezerwacji
- [x] Statusy blokujace: pending_payment, confirmed, converted_to_rental; szkic nie blokuje

### Testy

- [x] Konflikt dat / nakladanie rezerwacji — odrzucenie
- [x] Przejscia statusow (confirm, cancel, expire)
- [x] Widoki panelu (klient + rezerwacja)
- [x] Integracja z blokadami floty
- [x] Metryki pulpitu (`get_bookings_dashboard_metrics`)
- [x] `python backend/manage.py seed_demo`

**Definition of Done:** pracownik zakłada rezerwację z poprawną walidacją dostępności. — **spełnione**

---

# Sprint 4 — pricing (cennik + snapshoty) ⬜

**Cel:** naliczanie opłat oddzielone od płatności i faktur (§8 AGENT_CONTEXT).

### Modele

- [x] `PriceList`, `DailyRate`, `PricingRule`, `ExtraService` — `pricing.0001_initial`
- [x] `PriceLine` — snapshot przy rezerwacji (`bookings.0003_priceline`)

### Logika

- [ ] `PricingService` — stawka dzienna, weekend, święto, rabat długoterminowy
- [ ] Dodatki: fotelik, dodatkowy kierowca, opłaty jednorazowe
- [ ] Zamrożenie `PriceLine` przy zapisie rezerwacji

### Testy

- [ ] Scenariusz: kilka dni + weekend + extra
- [ ] Zmiana cennika **nie zmienia** istniejącej rezerwacji

**Definition of Done:** rezerwacja ma historyczny rozpis kosztów.

---

# Sprint 5 — Rental + payments MVP ⬜

**Cel:** `Reservation → Rental` + rejestracja płatności bez bramki online.

### bookings (cd.)

- [ ] Model `Rental` + statusy: scheduled, active, returned, closed, cancelled
- [ ] `ReservationService.convert_to_rental()` tylko z `confirmed`

### payments

- [ ] `Payment`, `PaymentIntent`
- [ ] Typy: rental_fee, deposit, refund, extra_charge, damage_charge
- [ ] Metody: cash, bank_transfer, card (ręczna rejestracja)
- [ ] **Kaucja ≠ przychód** — reguła w serwisie/raporcie

### Testy

- [ ] Konwersja tylko z poprawnego statusu
- [ ] Depozyt nie wliczany do revenue

**Definition of Done:** operacyjny wynajem z opłatą i kaucją w systemie.

---

# Sprint 6 — operations (wydanie / zwrot) ⬜

**Cel:** mobilny workflow na tablecie/telefonie.

### Modele

- [ ] `HandoverProtocol`, `ReturnProtocol`
- [ ] `ProtocolPhoto`, `Signature`
- [ ] `DamageSnapshot` — zamrożenie stanu uszkodzeń

### UI (mobile-first)

- [ ] Formularze touch-friendly
- [ ] Upload zdjęć: `capture="environment"`
- [ ] HTMX — partial updates kroków workflow

### Logika

- [ ] `HandoverService` — km, paliwo, zdjęcia, podpis, snapshot uszkodzeń
- [ ] `ReturnService` — porównanie, nowe szkody, dopłaty

### Testy

- [ ] Protokół niezmienny po edycji `Damage` w flocie

**Definition of Done:** pełny cykl wydania i zwrotu z podpisem i zdjęciami.

---

# Sprint 7 — documents (PDF, faktury, email) ⬜

**Cel:** artefakty **niemutowalne** — generowane ze snapshotów, nie z live DB.

### Modele

- [ ] `Document`, `DocumentTemplate`, `EmailLog`
- [ ] `Invoice`, `InvoiceItem` (oddzielone od `Payment`)

### Funkcje

- [ ] PDF protokołu wydania/zwrotu
- [ ] Prywatne storage mediów
- [ ] Email MVP po wydaniu
- [ ] Log wysyłek

### Testy

- [ ] PDF nie zmienia się po zmianie danych operacyjnych

**Definition of Done:** PDF i faktura po zamknięciu wynajmu; dokumenty w private storage.

---

# Sprint 8 — dashboard + website ⬜

**Cel:** widoczność operacji + kanał rezerwacji dla klienta.

### dashboard

- [ ] Aktywne wynajmy
- [ ] Wolne auta (z `AvailabilityService`)
- [ ] Nadchodzące zwroty
- [ ] Nieopłacone wynajmy
- [ ] Alerty: wygasające ubezpieczenie, przeglądy (jeśli dane w `fleet`)

### website

- [ ] Publiczna lista floty
- [ ] Wyszukiwanie dostępności (daty)
- [ ] Formularz rezerwacji online
- [ ] (Opcjonalnie) portal klienta — historia, pobranie dokumentów

**Definition of Done:** właściciel widzi stan firmy; klient może złożyć rezerwację online.

---

# Sprint 8b — Chat AI (konsultant klienta) ⬜

**Cel:** publiczny asystent AI na stronie — FAQ, pomoc w wyborze auta, prowadzenie do rezerwacji (bez zapisu rezerwacji z czatu).

Dokumentacja techniczna: [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md)

**Zależności:** Sprint 8 (layout `website`); pełne tool calls po Sprint 2–4 (fleet, bookings, pricing).

### MVP (Faza A — możliwe przed pełnym website)

- [ ] `ChatSession`, `ChatMessage` — modele + migracje
- [ ] Adapter `LLMClient` + konfiguracja env (`LLM_API_KEY`, `LLM_MODEL`)
- [ ] `ConsultantChatService` — FAQ-only, system prompt z polityką firmy
- [ ] Widok `/asystent/` + widget na `base.html`
- [ ] Rate limiting, CSRF, komunikat RODO/disclaimer
- [ ] Testy z mockiem LLM

### Rozszerzenie (Faza B — po bookings + pricing)

- [ ] Tool `search_available_cars` → `AvailabilityService`
- [ ] Tool `estimate_price` → `PricingService` (disclaimer: orientacyjnie)
- [ ] Tool `get_my_reservation_status` — tylko zalogowany `customer`
- [ ] Deep link do formularza rezerwacji z parametrami dat/auto
- [ ] Retencja wiadomości / polityka czyszczenia
- [ ] (Opcjonalnie) panel wewnętrzny: podgląd rozmów dla supportu

### Bezpieczeństwo

- [ ] Klucze API tylko w secrets / `.env`
- [ ] Brak PII innych klientów w kontekście LLM
- [ ] Jawny zakaz tworzenia rezerwacji/płatności przez model (prompt + brak tooli mutujących)

**Definition of Done:** klient na stronie publicznej prowadzi rozmowę z botem; bot odpowiada po polsku na FAQ; po Sprint 4 — potrafi podać wolne auta i orientacyjną cenę; konwersja kończy się linkiem do formularza rezerwacji.

---

# Sprint 9+ — Backlog (produkcja i integracje)

<!-- Nie przypisane do konkretnego sprintu — priorytetyzuj przed startem -->

### Płatności online

- [ ] Integracja bramki płatności
- [ ] `PaymentProviderEvent` + webhooki

### Bezpieczeństwo i compliance

- [ ] HTTPS na produkcji
- [ ] Szyfrowane PDF
- [ ] Audit log operacji krytycznych
- [ ] Bezpieczne uploady (walidacja typu/rozmiaru)

### Infrastruktura produkcyjna

- [ ] Deploy VPS: Docker Compose + Gunicorn + Caddy/Nginx
- [ ] Backup PostgreSQL + media + offsite
- [ ] Test odtworzenia z backupu

### Rozszerzenia biznesowe

- [ ] Zaawansowany dynamic pricing
- [ ] Raporty finansowe (przychód vs kaucje vs faktury)
- [ ] Powiadomienia SMS/push
- [ ] Wielojęzyczność UI
- [ ] Chat AI — eskalacja do człowieka, analityka konwersji (jeśli nie w Sprint 8b)

---

## Mapa zależności (kolejność obowiązkowa)

```text
Sprint 0 (fundament)
    ↓
Sprint 1 (accounts + struktura)
    ↓
Sprint 2 (fleet)
    ↓
Sprint 3 (bookings: rezerwacje)
    ↓
Sprint 4 (pricing + snapshoty)
    ↓
Sprint 5 (rental + payments)
    ↓
Sprint 6 (operations)
    ↓
Sprint 7 (documents)  ← wymaga snapshotów z 4 i 6
    ↓
Sprint 8 (dashboard + website)
    ↓
Sprint 8b (chat AI — konsultant)  ← wymaga website; pełne tools po 2–4
    ↓
Sprint 9+ (produkcja)
```

**Nie przeskakiwać:** operations i PDF przed fleet + bookings + snapshotami cen.

---

## Priorytety biznesowe (z AGENT_CONTEXT)

1. Integralność historyczna (snapshoty, PDF)
2. Poprawność cen
3. Poprawność dostępności
4. Poprawność płatności (kaucja ≠ przychód)
5. Mobilne workflow operacyjne
6. Prostota i audytowalność

---

## Szybka checklista „co jest w repo”

| Komponent | W repo | Działa / zintegrowane |
|-----------|--------|------------------------|
| Django + config | ✅ | ✅ |
| Docker Compose | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ |
| Tailwind + HTMX | ✅ | ✅ |
| Pytest / Ruff | ✅ | ✅ |
| `AGENT_CONTEXT.md` | ✅ | — |
| `PROJECT_PLAN.md` | ✅ | — |
| `backend/ARCHITECTURE.md` | ✅ | — |
| `apps/*` szkielet + README | ✅ | ✅ (`django check`) |
| `apps/accounts` — model/auth | ✅ | ✅ |
| Panel `/panel/` + `base_internal.html` | ✅ | ✅ |
| Locale PL + MEDIA/STATIC | ✅ | ✅ |
| `apps/fleet` — modele + panel | ✅ | ✅ |
| `apps/bookings` — Customer, Reservation, panel | ✅ | ✅ |
| `apps/pricing` — modele cennika | ✅ | ✅ (admin) |
| `apps/payments` | ❌ | — |
| `apps/operations` | ❌ | — |
| `apps/documents` | ❌ | — |
| `apps/dashboard` — pełny szkielet | ✅ | ✅ |
| `apps/website` | ✅ | ✅ |
| Chat AI konsultant | ❌ | — (plan: Sprint 8b) |
| `docs/AI_CONSULTANT.md` | ✅ | — |

---

*Plik utrzymywany ręcznie przez zespół. Przy większych zmianach architektury zaktualizuj też `AGENT_CONTEXT.md` §19 (Current Project Status).*
