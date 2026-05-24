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
| **Aktualny etap** | Sprint 7 — documents (PDF, faktury, email) |
| **Następny krok** | Task 7.9 — `InvoiceService` MVP |
| **Postęp ogólny** | ~78% (Sprint 0–6 zamkniete) |
| **Ostatnia aktualizacja** | 2026-05-20 |
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
| 4 | pricing (cennik + snapshoty) | ✅ | 100% |
| 5 | Rental + payments MVP | ✅ | 100% |
| 6 | operations (wydanie/zwrot) | ✅ | 100% |
| 7 | documents (PDF, faktury) | 🟡 | ~10% |
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
6. ~~**Sprint 4 — pricing**~~ ✅ — cennik, snapshoty, tryb ceny na rezerwacji, kaucja na kategorii
7. ~~**Sprint 5 — rental + payments**~~ ✅ — wynajem operacyjny, rejestracja platnosci (reczna)
8. ~~**Sprint 6 — operations**~~ ✅ — protokoly wydania/zwrotu, snapshoty szkod
9. **Sprint 7–8** — documents, website
10. **Sprint 8b — Chat AI** — po podstawowym `website` (lub MVP FAQ wcześniej) — [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md)

---

## Aktywne TODO

<!-- Bieżące zadania — edytuj na bieżąco -->

- [ ] Upload zdjec/dokumentow w panelu floty (obecnie admin) — backlog / Sprint 2+
- [ ] **Operations paperless** — pelna roadmapa: [Roadmap — operations (paperless)](#roadmap--operations-paperless) (HTMX kroki, PDF, email, doplaty, zamkniecie wynajmu)

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
- [x] Sprint 4: modele cennika + `PriceLine` + `PricingService` + `PriceSnapshotService`
- [x] Sprint 4: panel `/panel/cenniki/` (CRUD cennikow, stawki, reguly, dodatki)
- [x] Sprint 4: tryb ceny na rezerwacji — auto / wybrany cennik / kwota reczna (`bookings.0004`)
- [x] Sprint 4: `CarCategory.deposit` + edycja kategorii `/panel/flota/kategorie/<id>/edycja/` (`fleet.0002`)
- [x] Sprint 4: rozpis cen na szczegolach rezerwacji, `seed_demo` z cennikiem
- [x] Sprint 4: testy pricing + bookings + fleet (~59 w tych modulach)
- [x] Sprint 4 — **zamkniety** (Definition of Done spelnione)
- [x] Sprint 5: model `Rental` + `RentalService` + `bookings.0005_rental`
- [x] Sprint 5: `ReservationService.convert_to_rental()` z `confirmed` + snapshot ceny
- [x] Sprint 5: panel wynajmow `/panel/rezerwacje/wynajmy/`, cykl scheduled → active → returned → closed
- [x] Sprint 5: dostepnosc — blokada przez wynajem (nie `converted_to_rental` na rezerwacji)
- [x] Sprint 5: `Payment`, `PaymentIntent`, `PaymentProviderEvent` + `payments.0001_initial`
- [x] Sprint 5: `PaymentService` (rental_fee, deposit, refund) + panel `/panel/platnosci/`
- [x] Sprint 5: kaucja ≠ przychod (`REVENUE_PAYMENT_TYPES`, selektory salda)
- [x] Sprint 5: testy bookings (~45) + payments (10)
- [x] Sprint 5 — **zamkniety** (Definition of Done spelnione)
- [x] Sprint 6: `HandoverProtocol`, `ReturnProtocol`, `ProtocolPhoto`, `Signature`, `DamageSnapshot` + `operations.0001_initial`
- [x] Sprint 6: `HandoverService` / `ReturnService` + `DamageSnapshotService` (immutability)
- [x] Sprint 6: panel `/panel/operacje/` (kolejka, formularze mobile, `capture="environment"`)
- [x] Sprint 6: wydanie → `RentalService.start`, zwrot → `mark_returned`; linki z widoku wynajmu
- [x] Sprint 6: usunieto placeholdery `dashboard` dla `/panel/operacje/` i `/panel/platnosci/` (konflikt URL)
- [x] Sprint 6: testy operations (7: serwis + widoki + snapshot)
- [x] Sprint 6 — **zamkniety** (Definition of Done spelnione)
- [x] Sprint 7 / Task 7.1: modele `documents` + `documents.0001_initial` + admin + 6 testow
- [x] Sprint 7 / Task 7.3: `PdfRenderer` (WeasyPrint), szablony PDF, seed szablonow `0004`, 3 testy renderera

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
| 2026-05-20 | 4 | Pricing: modele, `PricingService`, panel cennikow, snapshoty `PriceLine` |
| 2026-05-20 | 4 | Rezerwacja: tryb ceny (auto/cennik/reczna), kaucja na kategorii, edycja kategorii |
| 2026-05-20 | 4 | Domkniecie Sprint 4 — migracje `pricing.0001`, `bookings.0003/0004`, `fleet.0002` |
| 2026-05-20 | 5 | Rental: model, serwis, panel, integracja dostepnosci, `seed_demo` z wynajmem |
| 2026-05-20 | 5 | Payments: `PaymentService`, panel platnosci per wynajem, regula kaucja ≠ przychod |
| 2026-05-20 | 5 | Domkniecie Sprint 5 — migracje `bookings.0005`, `payments.0001` |
| 2026-05-20 | 6 | Operations: protokoly, snapshoty szkod, panel mobilny, integracja z wynajmem |
| 2026-05-20 | 6 | Domkniecie Sprint 6 — migracja `operations.0001`, fix routingu vs dashboard |
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
- [x] CRUD kategorii (lista + tworzenie + edycja `/kategorie/<id>/edycja/`)
- [x] `CarCategory.deposit` — kaucja zwrotna per kategoria (`fleet.0002`)
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
- [x] Formularz tworzenia/edycji rezerwacji (auto + daty + klient + status + tryb ceny)
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

# Sprint 4 — pricing (cennik + snapshoty) ✅

**Cel:** naliczanie opłat oddzielone od płatności i faktur (§8 AGENT_CONTEXT).

### Modele

- [x] `PriceList`, `DailyRate`, `PricingRule`, `ExtraService` — `pricing.0001_initial`
- [x] `PriceLine` — snapshot przy rezerwacji (`bookings.0003_priceline`)
- [x] `Reservation.pricing_mode`, `price_list`, `custom_total` — `bookings.0004`
- [x] `CarCategory.deposit` — kaucja na kategorii (`fleet.0002`)

### Logika

- [x] `PricingService.calculate()` — doba, weekend, sezon/święta, rabat 7+ dni, extras; opcjonalny `price_list`
- [x] `PriceSnapshotService.freeze()` — zapis `PriceLine` (auto / wybrany cennik / kwota reczna)
- [x] Auto-naliczanie przy create/update (szkic, oczekuje platnosci), `confirm` (freeze przed zmiana statusu)
- [x] Panel: „Oblicz” + rozpis cen na szczegółach rezerwacji (bez przeliczania w trybie `custom`)
- [x] `seed_demo` — domyślny cennik, kaucje kategorii, przykładowa rezerwacja z ceną
- [x] Panel `/panel/cenniki/` — lista, edycja cennika, stawki / reguły / dodatki

### UI rezerwacji i floty (uzupelnienie Sprint 4)

- [x] Formularz rezerwacji: wybor trybu ceny (auto / cennik / kwota reczna)
- [x] Szczegoly rezerwacji: tryb ceny, kaucja z kategorii auta
- [x] Panel kategorii: edycja (`/panel/flota/kategorie/<id>/edycja/`), kolumna kaucji na liscie
- [x] Karta auta: wyswietlanie kaucji kategorii

### Testy

- [x] Scenariusz: kilka dni + weekend + extra + rabat długoterminowy
- [x] Zmiana cennika **nie zmienia** istniejącego snapshotu
- [x] Rezerwacja z `custom_total` i z wybranym `price_list`
- [x] Widoki: create rezerwacji, confirm, edycja kategorii (deposit)

**Definition of Done:** rezerwacja ma historyczny rozpis kosztów. — **spełnione**

> **Uwaga:** pole `deposit` na kategorii to przygotowanie pod Sprint 5 — rejestracja kaucji jako platnosci (`deposit` ≠ przychod) nadal w `payments`.

---

# Sprint 5 — Rental + payments MVP ✅

**Cel:** `Reservation → Rental` + rejestracja płatności bez bramki online.

### bookings — wynajem

- [x] Model `Rental` + statusy: scheduled, active, returned, closed, cancelled — `bookings.0005_rental`
- [x] `RentalService` — convert, start, mark_returned, close, cancel (scheduled)
- [x] `ReservationService.convert_to_rental()` tylko z `confirmed` + wymagany `PriceLine`
- [x] Panel `/panel/rezerwacje/wynajmy/` — lista, szczegoly, akcje statusow
- [x] Przycisk „Utworz wynajem” na potwierdzonej rezerwacji
- [x] Dostepnosc: `BLOCKING_RENTAL_STATUSES`; rezerwacja `converted_to_rental` nie blokuje auta
- [x] Pulpit: metryka „Aktywne wynajmy”
- [x] `seed_demo` — przykladowy wynajem z rezerwacji DEMO

### payments

- [x] `Payment`, `PaymentIntent`, `PaymentProviderEvent` — `payments.0001_initial`
- [x] Typy: rental_fee, deposit, refund, extra_charge, damage_charge
- [x] Metody: cash, bank_transfer, card, blik (+ online_gateway w modelu, bez integracji)
- [x] `PaymentService` — record_payment, record_deposit, record_rental_fee, refund_deposit
- [x] Selektory: `get_rental_payment_summary`, `get_rental_revenue_total`, `get_rental_deposit_balance`
- [x] Panel `/panel/platnosci/` + `/panel/platnosci/wynajem/<id>/` (formularz, szybka kaucja/zwrot)
- [x] Podglad platnosci na szczegolach wynajmu
- [x] **Kaucja ≠ przychód** — `REVENUE_PAYMENT_TYPES` bez deposit/refund

### Testy

- [x] Konwersja tylko z `confirmed`, duplikat i nakladanie wynajmow
- [x] Cykl zycia wynajmu (start → zwrot → zamkniecie)
- [x] Depozyt nie wliczany do `revenue_total`; zwrot kaucji z walidacja salda
- [x] Widoki panelu (wynajmy, platnosci)

**Definition of Done:** operacyjny wynajem z opłatą i kaucją w systemie. — **spełnione**

> **Backlog (poza MVP Sprint 5):** bramka online (`PaymentGatewayService`, webhooki `PaymentProviderEvent`).

---

# Sprint 6 — operations (wydanie / zwrot) ✅

**Cel (MVP):** mobilny workflow na tablecie/telefonie — pierwsza wersja protokołów elektronicznych.

**Cel docelowy (wizja produktu):** **całkowicie paperless workflow** — wszystkie protokoły wyłącznie elektroniczne; telefon lub tablet wystarcza do pełnego procesu wydania i zwrotu auta (bez papieru, skanów ani osobnych narzędzi). Szczegóły kroków: [Roadmap — operations (paperless)](#roadmap--operations-paperless).

### Modele

- [x] `HandoverProtocol`, `ReturnProtocol`
- [x] `ProtocolPhoto`, `Signature`
- [x] `DamageSnapshot` — zamrożenie stanu uszkodzeń

### UI (mobile-first)

- [x] Formularze touch-friendly (`/panel/operacje/wydanie/`, `/zwrot/`)
- [x] Upload zdjęć: `capture="environment"`
- [ ] HTMX — partial updates kroków workflow — **backlog**

### Logika

- [x] `HandoverService` — km, paliwo, zdjęcia, podpis, snapshot uszkodzeń, `RentalService.start`
- [x] `ReturnService` — porównanie paliwa/km, nowe szkody, notatki doplat, `mark_returned`
- [ ] Automatyczne doplaty → `payments` — **backlog** (obecnie notatki w protokole)

### Testy

- [x] Protokół niezmienny po edycji `Damage` w flocie

**Definition of Done:** pełny cykl wydania i zwrotu z podpisem i zdjęciami. — **spełnione**

> **Backlog (poza MVP Sprint 6):** patrz [Roadmap — operations (paperless)](#roadmap--operations-paperless).

---

## Roadmap — operations (paperless)

> Stan na 2026-05-20 po Sprint 6 MVP. `[x]` = zaimplementowane; `[ ]` = do zrobienia w kolejnych sprintach (gł. Sprint 7 `documents`, rozszerzenia operations/payments).

### Zasady

- Wszystkie protokoły **elektroniczne** — jedyny kanał w terenie to panel mobilny (`/panel/operacje/`).
- **Telefon/tablet** obsługuje cały proces (wydanie i zwrot) bez drukowania.
- PDF i email budowane ze **snapshotów** protokołu (`DamageSnapshot`, dane protokołu) — nie z live `fleet.Damage`.
- Integracje: PDF/email → `documents`; dopłaty po zwrocie → `pricing` + `payments`.

### Docelowy workflow — wydanie auta

| Krok | Opis | Status |
|------|------|--------|
| 1 | Otworzenie wynajmu na telefonie (kolejka „Do wydania”) | [x] |
| 2 | Rozpoczęcie protokołu wydania | [x] |
| 3 | Wprowadzenie: przebiegu, poziomu paliwa, uwag | [x] |
| 4 | Dodanie zdjęć auta (`capture="environment"`) | [x] |
| 5 | Oznaczenie szkód (snapshot istniejących + nowe z protokołu) | [x] |
| 6 | Podpis klienta palcem (canvas / upload obrazu podpisu) | [x] |
| 7 | Wygenerowanie PDF protokołu wydania | [x] |
| 8 | Automatyczne wysłanie emaila do klienta z PDF | [x] |
| 9 | Automatyczna zmiana statusu `Rental` → **active** | [x] (`HandoverService` → `RentalService.start`) |

**Backlog UX wydania:** formularz krok po kroku (HTMX), walidacja na każdym kroku, offline-tolerant upload zdjęć (opcjonalnie, później).

### Docelowy workflow — zwrot auta

| Krok | Opis | Status |
|------|------|--------|
| 1 | Otworzenie zwrotu (kolejka „Do zwrotu” / wynajem aktywny) | [x] |
| 2 | Wprowadzenie: przebiegu, paliwa, uwag | [x] |
| 3 | Porównanie szkód z wydaniem (`DamageSnapshot` z handover vs stan przy zwrocie) | [x] (snapshoty); UI porównania side-by-side — [ ] |
| 4 | Dodanie nowych szkód | [x] |
| 5 | Wyliczenie dopłat (paliwo, km, szkody — wg cennika) | [ ] → `pricing` + `payments` (obecnie: notatki `surcharge_notes`) |
| 6 | Podpis klienta | [x] |
| 7 | Generacja PDF protokołu zwrotu | [x] |
| 8 | Email do klienta z PDF | [x] |
| 9 | Zamknięcie wynajmu (`returned` → opcjonalnie `closed` po rozliczeniu) | [x] częściowo (`mark_returned`); pełne `close` po płatnościach — [ ] |

**Backlog UX zwrotu:** ekran porównania szkód wydanie/zwrot, podgląd dopłat przed podpisem, HTMX kroki.

### Mapowanie na sprinty

| Obszar | Sprint / moduł |
|--------|----------------|
| PDF protokołów, szablony, private storage | Sprint 7 — `documents` |
| Email po wydaniu/zwrocie, `EmailLog` | Sprint 7 — `documents` |
| HTMX workflow krok po kroku | operations (po 7) |
| Auto-dopłaty → `Payment` | operations + `payments` + `pricing` |
| Zamknięcie wynajmu po rozliczeniu | `bookings.RentalService.close` + panel |

---

# Sprint 7 — documents (PDF, faktury, email) 🟡

**Cel:** artefakty **niemutowalne** — generowane ze snapshotów, nie z live DB. **Kluczowe dla paperless operations:** PDF + email po protokole wydania i zwrotu (patrz [Roadmap — operations (paperless)](#roadmap--operations-paperless)).

### Taski (kolejność implementacji)

| ID | Task | Opis | Status |
|----|------|------|--------|
| **7.1** | Modele domeny | `Document`, `DocumentTemplate`, `EmailLog`, `Invoice`, `InvoiceItem`; migracja; admin; testy modeli | ✅ |
| **7.2** | Private storage | `PrivateDocumentStorage`, `upload_to` pod `documents/private/`; ustawienia | ✅ |
| **7.3** | PDF renderer | Szablony HTML + `PdfRenderer` (WeasyPrint); zależność w `pyproject.toml` | ✅ |
| **7.4** | DTO snapshotów | `HandoverDocumentData` / `ReturnDocumentData` — pakiet danych z protokołu (bez live `Damage`) | ✅ |
| **7.5** | `DocumentService` | `generate_handover_pdf`, `generate_return_pdf` → nowy `Document` + hash pliku | ✅ |
| **7.6** | Hook operations | Po `complete_handover` / `complete_return` — wywołanie generacji PDF | ✅ |
| **7.7** | `EmailService` | Wysyłka z załącznikiem, `EmailLog`, szablony email (wydanie/zwrot) | ✅ |
| **7.8** | Panel documents | Lista/pobranie PDF per wynajem; link z wynajmu i protokołu | ✅ |
| **7.9** | `InvoiceService` MVP | Faktura z `PriceLine` (bez przeliczania cennika); PDF faktury | ⬜ |
| **7.10** | Testy integracyjne | PDF niezmienny po edycji `fleet.Damage`; email failure → `EmailLog` | ⬜ |

### Modele (7.1)

- [x] `Document`, `DocumentTemplate`, `EmailLog`
- [x] `Invoice`, `InvoiceItem` (oddzielone od `Payment`)

### Funkcje (7.3–7.9)

- [ ] PDF protokołu wydania (dane z `HandoverProtocol` + `DamageSnapshot` + zdjęcia)
- [ ] PDF protokołu zwrotu (dane z `ReturnProtocol` + porównanie snapshotów)
- [ ] Prywatne storage mediów
- [x] Email MVP po zakończeniu wydania (PDF w załączniku)
- [x] Email MVP po zakończeniu zwrotu
- [x] Log wysyłek (`EmailLog`)

### Testy (7.10)

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
- [ ] **Celery + Redis** — kolejka powiadomień (klient + pracownik); szczegóły: [`docs/DOCKER.md`](docs/DOCKER.md)

### Powiadomienia asynchroniczne (Celery + Redis)

> MVP (Sprint 7): email do klienta **synchronicznie** w `EmailService`. Docelowo: taski w tle.

- [ ] Serwisy Docker: `redis`, `celery`, opcjonalnie `celery-beat`
- [ ] Task: wysyłka emaila z PDF protokołu (`documents`)
- [ ] Task: alerty dla pracowników — kolejka operacji, nadchodzące zwroty, nieopłacone wynajmy (`dashboard`)
- [ ] Task: przypomnienia dla klienta — zbliżający się zwrot, potwierdzenie rezerwacji
- [ ] Retry + monitoring (`EmailLog`, dead-letter / admin retry)
- [ ] Testy: `CELERY_TASK_ALWAYS_EAGER` w pytest

### Rozszerzenia biznesowe

- [ ] Zaawansowany dynamic pricing
- [ ] Raporty finansowe (przychód vs kaucje vs faktury)
- [ ] Powiadomienia SMS/push (po Celery — adapter obok email)
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
| `apps/fleet` — flota, kategorie (+ deposit), panel | ✅ | ✅ |
| `apps/bookings` — Reservation, `Rental`, `PriceLine`, tryb ceny | ✅ | ✅ |
| `apps/pricing` — cennik, panel, `PricingService` | ✅ | ✅ |
| `apps/payments` — Payment, panel, kaucja ≠ przychod | ✅ | ✅ |
| `apps/operations` — protokoly, panel mobilny | ✅ | ✅ |
| `apps/documents` | ❌ | — |
| `apps/dashboard` — pełny szkielet | ✅ | ✅ |
| `apps/website` | ✅ | ✅ |
| Chat AI konsultant | ❌ | — (plan: Sprint 8b) |
| `docs/AI_CONSULTANT.md` | ✅ | — |

---

*Plik utrzymywany ręcznie przez zespół. Przy większych zmianach architektury zaktualizuj też `AGENT_CONTEXT.md` §19 (Current Project Status).*
