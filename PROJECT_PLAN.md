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
| **Aktualny etap** | Sprint 10 — smoke 10.10 portal |
| **Następny krok** | 10.10 portal `klient` / `demo1234` na https://car-rental.filipf.online |
| **Postęp ogólny** | Funkcje ~99%; 10.8 ✅ i 10.9 ✅ na domenie |
| **Ostatnia aktualizacja** | 2026-07-18 |
| **Branch** | `feat/*` → `dev` → `main` (deploy) |
| **Repozytorium** | Live VPS; integracja na `dev` |

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
| 7 | documents (PDF, faktury) | ✅ | 100% |
| 8 | dashboard + website | ✅ | 100% |
| 9 | Produkcja i płatności online | ✅ | 100% |
| 8b | Chat AI — konsultant klienta | ✅ | 100% |
| CI/CD | GitHub Actions (CI + deploy) | ✅ | 100% |
| 9+ | Rozszerzenia (raporty, SMS, seed) | ✅ | 100% |
| **10** | **Demo produkcyjne (VPS pokazowy)** | **🟡** | **~98%** |
| 11 | Utrzymanie i observability demo | ✅ | 100% |
| **12** | **Demo polish / UX v2** | **✅** | **100%** |

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
9. ~~**Sprint 7 — documents**~~ ✅
10. ~~**Sprint 8**~~ ✅ — dashboard KPI + website (taski 8.1–8.14)
11. ~~**Sprint 9**~~ ✅ — płatności online + Celery + deploy (taski 9.1–9.10)
12. ~~**Sprint 8b — Chat AI**~~ ✅ — [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md)
13. ~~**Sprint 9+**~~ ✅ — raporty, SMS, rozbudowany `seed_demo`
14. **Sprint 10 — Demo produkcyjne** — VPS, HTTPS, smoke testy, runbook (taski 10.1–10.18)
15. **Sprint 11 — Utrzymanie demo** — health, logging, Celery Beat (opcjonalnie po 10)

---

## Aktywne TODO

<!-- Bieżące zadania — szczegóły w sekcjach sprintów poniżej -->

**Sprint 12:** **12.1–12.11** ✅.

**Sprint 11:** **11.1–11.7** ✅.

**Sprint 10 — domknięcie:** 10.8 ✅ i 10.9 ✅ na domenie; zostało 10.10 portal.

**VPS (zrobione 2026-07-18):** env check ✅, cron backup ✅, `smoke-health` ✅, ręczny `backup.sh` ✅.
**Smoke panel (2026-07-18):** wynajem #9 — wydanie → zwrot z dopłatami → płatność → `closed` + PDF ✅.
**Smoke publiczny (2026-07-18):** rezerwacja #20 → mock Opłać → `confirmed` ✅ (po release #88).

**Gałęzie:** `feat/*` → PR do `dev` → PR `dev` → `main` (deploy).

**Poza zakresem wersji demo:** prawdziwa bramka płatności, regulamin/RODO od prawnika, Twilio SMS prod.

---

## Zrobione (ostatnie)

<!-- Przenoś tu ukończone TODO z sekcji powyżej -->

- [x] Powiadomienia SMS — adapter mock/Twilio, Celery, SmsLog (Sprint 9+)

- [x] Upload zdjec/dokumentow w panelu floty (PR #52)
- [x] Operations paperless — doplaty po zwrocie, wizard zwrotu, porownanie szkod (PR #51–#53)
- [x] Raporty finansowe `/panel/raporty/` (PR #54)
- [x] Fix listy platnosci — rezerwacja bez wynajmu (PR #55)
- [x] Bezpieczne uploady — walidacja typu/rozmiaru (PR #56)
- [x] Rozbudowany `seed_demo` — 18 scenariuszy (Sprint 9+)
- [x] Dokumentacja zakresu demo prod (Sprint 10.2)
- [x] Wolumen `private_documents` na web w prod compose (Sprint 10.1)
- [x] `.env.production.example` + CI deploy check (Sprint 10.3–10.4)
- [x] Runbook demo `docs/DEMO_RUNBOOK.md` (Sprint 10.11)
- [x] Baner demo `DEMO_SITE` (Sprint 10.12)
- [x] Live deploy VPS + HTTPS/domena (Sprint 10.5–10.6)
- [x] Health endpoint `GET /health/` (Sprint 10.15 / PR #61)
- [x] Gałąź `dev` jako integracja sprintów (CI na PR → `dev`)
- [x] `seed_demo` na produkcji (Sprint 10.7)
- [x] Sprint 12.1–12.11 — demo polish / UX v2 (asystent, portal OTP, emaile, ops panel)
- [x] Sprint 10.14 — `install-backup-cron.sh` + hook w `deploy.sh`

---
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
- [x] Email potwierdzenia rezerwacji — `ReservationEmailService` + Celery (pending + confirmed)
- [x] Sprint 6: `HandoverProtocol`, `ReturnProtocol`, `ProtocolPhoto`, `Signature`, `DamageSnapshot` + `operations.0001_initial`
- [x] Sprint 6: `HandoverService` / `ReturnService` + `DamageSnapshotService` (immutability)
- [x] Sprint 6: panel `/panel/operacje/` (kolejka, formularze mobile, `capture="environment"`)
- [x] Sprint 6: wydanie → `RentalService.start`, zwrot → `mark_returned`; linki z widoku wynajmu
- [x] Sprint 6: usunieto placeholdery `dashboard` dla `/panel/operacje/` i `/panel/platnosci/` (konflikt URL)
- [x] Sprint 6: testy operations (7: serwis + widoki + snapshot)
- [x] Sprint 6 — **zamkniety** (Definition of Done spelnione)
- [x] Sprint 7 / Task 7.1: modele `documents` + `documents.0001_initial` + admin + 6 testow
- [x] Sprint 7 / Task 7.3: `PdfRenderer` (WeasyPrint), szablony PDF, seed szablonow `0004`, 3 testy renderera
- [x] Sprint 7: `DocumentService`, `EmailService`, `InvoiceService`, panel `/panel/dokumenty/`, testy integracyjne (7.1–7.10)
- [x] Sprint 7 — **zamknięty** (Definition of Done spelnione)
- [x] Sprint 8 / Task 8.1–8.4: KPI dashboard (metryki, wolne auta, nieoplacone, przychod miesiaca)
- [x] Sprint 8 / Task 8.5–8.7: alerty fleet, UI `panel.html`, testy dashboard (PR #19–#21)
- [x] Sprint 8 / Task 8.8: infrastruktura website — landing `/`, `base_public.html` (PR #23)
- [x] Sprint 8 / Task 8.9: publiczny katalog floty `/flota/` (PR #24)
- [x] Sprint 8 / Task 8.10: wyszukiwarka dostepnosci `/flota/dostepnosc/` (PR #25)
- [x] Sprint 8 / Task 8.13: strony informacyjne placeholder (PR #28)
- [x] Sprint 8 / Task 8.14: testy integracyjne flow publicznego
- [x] Sprint 8 — **zamknięty** (Definition of Done: dashboard KPI + website publiczna)

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
| 2026-05-30 | 7 | Documents: PDF protokolow, email, faktury, panel dokumentow, testy integracyjne |
| 2026-05-30 | 7 | Domkniecie Sprint 7 — `feature/documents` gotowy do merge |
| 2026-05-30 | 8 | Plan Sprint 8: taski 8.1–8.14 (dashboard KPI + website publiczna) |
| 2026-05-30 | 8 | Task 8.1: `dashboard/selectors/metrics.py`, `DashboardMetricsService`, migracja z bookings |
| 2026-07-14 | 8 | Task 8.3: selektor nieoplaconych wynajmow (`count_unpaid_rentals`, `get_rental_balance_due`) |
| 2026-07-14 | 8 | Task 8.5–8.7: alerty fleet, UI pulpitu, testy dashboard (PR #19–#21) |
| 2026-07-14 | 8 | Task 8.8–8.9: website — landing, katalog `/flota/` (PR #23–#24) |
| 2026-07-14 | 8 | Task 8.10: wyszukiwarka dostepnosci (PR #25) |
| 2026-07-14 | 8 | Task 8.12–8.14: rezerwacja online, strony info, testy flow (PR #27–#28) |
| 2026-07-14 | 8 | **Sprint 8 zamknięty** — dashboard + website publiczna |
| 2026-07-14 | 9+ | Paperless rozszerzenia: upload floty, doplaty, wizard zwrotu (PR #51–#53) |
| 2026-07-14 | 9+ | Raporty finansowe, fix platnosci rezerwacja-only, bezpieczne uploady (PR #54–#56) |
| 2026-07-14 | 9+ | Audit log operacji krytycznych — `apps.audit` |
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
- [x] Wizard krok po kroku (JS) — wydanie i zwrot

### Logika

- [x] `HandoverService` — km, paliwo, zdjęcia, podpis, snapshot uszkodzeń, `RentalService.start`
- [x] `ReturnService` — porównanie paliwa/km, nowe szkody, doplaty, `mark_returned`
- [x] Automatyczne doplaty → `payments` (`RentalCharge` + auto-close wynajmu)

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
| 6 | Podpis klienta palcem (canvas / upload obrazu podpisu) | [x] canvas + opcjonalne zdjęcie |
| 7 | Wygenerowanie PDF protokołu wydania | [x] |
| 8 | Automatyczne wysłanie emaila do klienta z PDF | [x] |
| 9 | Automatyczna zmiana statusu `Rental` → **active** | [x] (`HandoverService` → `RentalService.start`) |

**Backlog UX wydania:** formularz krok po kroku (HTMX) — [x] wizard 3-krokowy (JS); walidacja na każdym kroku, offline-tolerant upload zdjęć (opcjonalnie, później).

### Docelowy workflow — zwrot auta

| Krok | Opis | Status |
|------|------|--------|
| 1 | Otworzenie zwrotu (kolejka „Do zwrotu” / wynajem aktywny) | [x] |
| 2 | Wprowadzenie: przebiegu, paliwa, uwag | [x] |
| 3 | Porównanie szkód z wydaniem (`DamageSnapshot` z handover vs stan przy zwrocie) | [x] snapshoty + UI porównania side-by-side |
| 4 | Dodanie nowych szkód | [x] |
| 5 | Wyliczenie dopłat (paliwo, km, szkody — wg cennika) | [x] podgląd HTMX + auto `RentalCharge` → `payments` |
| 6 | Podpis klienta | [x] canvas + opcjonalne zdjęcie |
| 7 | Generacja PDF protokołu zwrotu | [x] |
| 8 | Email do klienta z PDF | [x] |
| 9 | Zamknięcie wynajmu (`returned` → opcjonalnie `closed` po rozliczeniu) | [x] `mark_returned` + auto `close` gdy saldo = 0 |

**Backlog UX zwrotu:** ekran porównania szkód wydanie/zwrot — [x]; podgląd dopłat przed podpisem — [x] (HTMX); wizard 3-krokowy — [x].

### Mapowanie na sprinty

| Obszar | Sprint / moduł |
|--------|----------------|
| PDF protokołów, szablony, private storage | Sprint 7 — `documents` |
| Email po wydaniu/zwrocie, `EmailLog` | Sprint 7 — `documents` |
| HTMX workflow krok po kroku | operations (po 7) |
| Auto-dopłaty → `Payment` | operations + `payments` + `pricing` |
| Zamknięcie wynajmu po rozliczeniu | `bookings.RentalService.close` + panel |

---

# Sprint 7 — documents (PDF, faktury, email) ✅

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
| **7.9** | `InvoiceService` MVP | Faktura z `PriceLine` (bez przeliczania cennika); PDF faktury | ✅ |
| **7.10** | Testy integracyjne | PDF niezmienny po edycji `fleet.Damage`; email failure → `EmailLog` | ✅ |

### Modele (7.1)

- [x] `Document`, `DocumentTemplate`, `EmailLog`
- [x] `Invoice`, `InvoiceItem` (oddzielone od `Payment`)

### Funkcje (7.3–7.9)

- [x] PDF protokołu wydania (dane z `HandoverProtocol` + `DamageSnapshot` + zdjęcia)
- [x] PDF protokołu zwrotu (dane z `ReturnProtocol` + porównanie snapshotów)
- [x] Prywatne storage mediów
- [x] Email MVP po zakończeniu wydania (PDF w załączniku)
- [x] Email MVP po zakończeniu zwrotu
- [x] Log wysyłek (`EmailLog`)
- [x] `InvoiceService` MVP + PDF faktury

### Testy (7.10)

- [x] PDF nie zmienia się po zmianie danych operacyjnych (`fleet.Damage`, `PriceLine`)
- [x] Email failure → `EmailLog` (FAILED), protokol i PDF bez rollbacku

**Definition of Done:** PDF i faktura po zamknięciu wynajmu; dokumenty w private storage.

---

# Sprint 8 — dashboard + website ✅

**Cel:** widoczność operacji dla właściciela + kanał rezerwacji dla klienta.

> **Stan wyjściowy:** podstawowe metryki bookings na pulpicie (Sprint 3) — `get_bookings_dashboard_metrics()` w `bookings/selectors/dashboard.py`. Sprint 8 przenosi agregację do `dashboard`, rozszerza KPI i buduje `website`.

### Taski (kolejność implementacji)

| ID | Task | Opis | Status |
|----|------|------|--------|
| **8.1** | Selektory KPI | `dashboard/selectors/metrics.py` — centralizacja metryk; migracja z `bookings.selectors.dashboard` | ✅ |
| **8.2** | Wolne auta (`AvailabilityService`) | KPI „wolne auta” przez `fleet.AvailabilityService` (as_of=now), nie heurystyka busy | ✅ |
| **8.3** | Nieopłacone wynajmy | Selektor wynajmów z saldem do zapłaty (`payments` summary) | ✅ |
| **8.4** | Przychód okresu | KPI przychodu miesiąca — tylko `REVENUE_PAYMENT_TYPES` (kaucja ≠ przychód) | ✅ |
| **8.5** | Alerty fleet | Wygasające OC/przeglądy z `CarDocument` (np. 30 dni) | ✅ |
| **8.6** | UI pulpitu | Rozszerzenie `panel.html` — widgety KPI, alerty, skróty do kolejek operacji/płatności | ✅ |
| **8.7** | Testy dashboard | pytest selektorów KPI + widoku panelu | ✅ |
| **8.8** | Infrastruktura website | `website/urls.py`, `base_public.html`, landing `/` (zastąpienie placeholder `config.views.home`) | ✅ |
| **8.9** | Katalog floty publiczny | `/flota/` — lista kategorii i aut (selektory `fleet`, bez logiki w szablonie) | ✅ |
| **8.10** | Wyszukiwarka dostępności | Formularz dat → `AvailabilityService` → lista wolnych aut | ✅ |
| **8.11** | Orientacyjna wycena | Kalkulator ceny read-only (`PricingService`) — bez zapisu rezerwacji | ✅ |
| **8.12** | Rezerwacja online | `PublicBookingOrchestrator` + formularz → `ReservationService` + snapshot ceny | ✅ |
| **8.13** | Strony informacyjne | Regulamin, kontakt, FAQ — szablony placeholder (`website`) | ✅ |
| **8.14** | Testy website | pytest widoków publicznych + orchestratora rezerwacji | ✅ |

### Dashboard (8.1–8.7)

- [x] Podstawowe widgety (Sprint 3): aktywne rezerwacje/wynajmy, wolne auta (heurystyka), zwroty w 7 dni
- [x] `DashboardMetricsService` + `selectors/metrics.py` — centralizacja KPI (task 8.1)
- [x] Wolne auta z `AvailabilityService.count_available_cars_at` (task 8.2)
- [x] Nieopłacone wynajmy (saldo z `payments`, task 8.3)
- [x] Przychód miesiąca (bez kaucji, task 8.4)
- [x] Alerty: wygasające ubezpieczenie, przeglądy (`CarDocument`, task 8.5)
- [x] UI pulpitu: widgety KPI, lista alertów, skróty (task 8.6)
- [x] Testy dashboard: selektory + widok panelu (task 8.7)

### Website (8.8–8.14)

- [x] Layout publiczny oddzielony od `/panel/` (task 8.8)
- [x] Publiczna lista floty `/flota/` (task 8.9)
- [x] Wyszukiwarka dostępności `/flota/dostepnosc/` (task 8.10)
- [x] Orientacyjna wycena read-only `/wycena/` (task 8.11)
- [x] Formularz rezerwacji online `/rezerwacja/` (task 8.12)
- [x] Strony statyczne placeholder: `/regulamin/`, `/kontakt/`, `/faq/` (task 8.13)
- [x] Testy website: flow search → quote → reserve (task 8.14)

### Plan domknięcia Sprint 8 (8.12–8.14)

**8.12 — Rezerwacja online** (priorytet)
- `website/services/public_booking.py` — `PublicBookingOrchestrator.submit(...)`:
  1. walidacja dostępności (`AvailabilityService.is_car_available`)
  2. utworzenie / dopasowanie `Customer` (email + telefon, bez konta logowania)
  3. `ReservationService.create(..., status=PENDING_PAYMENT lub CONFIRMED)` — decyzja produktowa
  4. `PriceSnapshotService.freeze()` — snapshot ceny z `PricingService`
- `PublicBookingForm` — dane klienta (min. email/telefon), auto, daty, opcjonalne extras
- Widok `/rezerwacja/` + strona potwierdzenia; deep link z `/wycena/` i `/flota/dostepnosc/`
- Rate limiting / CSRF (POST); brak zapisu `PriceLine` poza serwisami `bookings`

**8.13 — Strony informacyjne**
- Szablony: regulamin, kontakt, FAQ pod `/regulamin/`, `/kontakt/`, `/faq/`
- Linki w `base_public.html` (zastąpić placeholdery)

**8.14 — Testy website**
- `tests/test_public_booking.py` — orchestrator (mock / DB) + widok POST
- Uzupełnienie testów widoków publicznych (integracja flow: search → quote → reserve)

**Definition of Done Sprint 8:** klient przechodzi pełny flow publiczny (szukaj → wycena → rezerwacja); właściciel ma pełny pulpit KPI + alerty.

---

### Opcjonalnie (backlog w Sprint 8 / 8b)

- [x] Portal klienta — historia rezerwacji, pobranie dokumentów (wymaga auth `customer`) — `/konto/`
- [ ] HTMX partial refresh widgetów pulpitu
- [ ] Inicjacja płatności online na stronie (wymaga bramki — Sprint 9+)

**Definition of Done:** właściciel widzi pełny stan firmy na pulpicie (KPI + alerty); klient może wyszukać auto, zobaczyć orientacyjną cenę i złożyć rezerwację online.

---

# Sprint 8b — Chat AI (konsultant klienta) ✅

**Cel:** publiczny asystent AI na stronie — FAQ, pomoc w wyborze auta, prowadzenie do rezerwacji (bez zapisu rezerwacji z czatu).

Dokumentacja techniczna: [`docs/AI_CONSULTANT.md`](docs/AI_CONSULTANT.md)

**Zależności:** Sprint 8 (layout `website`); pełne tool calls po Sprint 2–4 (fleet, bookings, pricing).

### MVP (Faza A — możliwe przed pełnym website)

- [x] `ChatSession`, `ChatMessage` — modele + migracje
- [x] Adapter `LLMClient` + konfiguracja env (`LLM_API_KEY`, `LLM_MODEL`)
- [x] `ConsultantChatService` — FAQ-only, system prompt z polityką firmy
- [x] Widok `/asystent/` + widget na `base_public.html`
- [x] Rate limiting, CSRF, komunikat RODO/disclaimer
- [x] Testy z mockiem LLM

### Rozszerzenie (Faza B — po bookings + pricing)

- [x] Tool `search_available_cars` → `AvailabilityService`
- [x] Tool `estimate_price` → `PricingService` (disclaimer: orientacyjnie)
- [x] Tool `get_my_reservation_status` — tylko zalogowany `customer`
- [x] Deep link do formularza rezerwacji z parametrami dat/auto
- [x] Retencja wiadomości / polityka czyszczenia
- [x] Panel wewnętrzny: podgląd rozmów dla supportu (`/panel/asystent/`)

### Bezpieczeństwo

- [x] Klucze API tylko w secrets / `.env`
- [x] Brak PII innych klientów w kontekście LLM
- [x] Jawny zakaz tworzenia rezerwacji/płatności przez model (prompt + brak tooli mutujących)

**Definition of Done:** klient na stronie publicznej prowadzi rozmowę z botem; bot odpowiada po polsku na FAQ; po Sprint 4 — potrafi podać wolne auta i orientacyjną cenę; konwersja kończy się linkiem do formularza rezerwacji.

---

# Sprint 9 — produkcja i płatności online ✅

**Cel:** zamknięcie pętli **rezerwacja online → płatność → potwierdzenie** oraz fundament produkcyjny (async, deploy).

**Zależności:** Sprint 8 (`pending_payment` na rezerwacji), Sprint 5 (`PaymentIntent`, `PaymentProviderEvent` — szkielet).

> **Luka do 9.1:** `PaymentIntent` ma dziś tylko FK `rental` — rezerwacja publiczna nie ma jeszcze wynajmu. Trzeba dodać powiązanie z `Reservation`.

### Taski (kolejność implementacji)

| ID | Task | Opis | Status |
|----|------|------|--------|
| **9.1** | Intent dla rezerwacji | `PaymentIntent.reservation` (opcjonalny), migracja; intent bez wynajmu | ✅ |
| **9.2** | Adapter bramki | `payments/adapters/gateway.py` — interface + implementacja **mock** (dev/test) | ✅ |
| **9.3** | `PaymentGatewayService` | `create_intent`, obsługa sukcesu/błędu, idempotencja na `PaymentProviderEvent` | ✅ |
| **9.4** | Webhook | endpoint w `payments` (nie `website`), log zdarzeń, weryfikacja podpisu (mock/stripe-ready) | ✅ |
| **9.5** | Inicjacja z website | po rezerwacji: strona „Zapłać” / redirect; tylko orkiestracja w `website` | ✅ |
| **9.6** | Orkiestracja po płatności | sukces → `PaymentService` + `ReservationService.confirm` | ✅ |
| **9.7** | Redis + Celery | serwisy Docker, `config/celery.py`, worker; [`docs/DOCKER.md`](docs/DOCKER.md) | ✅ |
| **9.8** | Email async | task wysyłki PDF (`documents`) zamiast synchronicznego `EmailService` w request | ✅ |
| **9.9** | Deploy produkcyjny | HTTPS (Caddy/Nginx), backup PostgreSQL + media, test odtworzenia | ✅ |
| **9.10** | Testy płatności | pytest: mock gateway, webhook, flow website → intent → confirm | ✅ |

### Płatności online (9.1–9.6)

- [x] Model / serwis intentu dla `Reservation` (nie tylko `Rental`)
- [x] Adapter bramki (mock na start; Stripe/Przelewy24 — adapter wymienny)
- [x] Webhook + `PaymentProviderEvent`
- [x] Strona płatności po publicznej rezerwacji
- [x] Potwierdzenie rezerwacji po zaksięgowaniu wpłaty

### Infrastruktura (9.7–9.9)

- [x] Celery + Redis w Compose
- [x] Powiadomienia email w tle
- [x] Deploy VPS + HTTPS + backup

### Definition of Done Sprint 9

Klient po rezerwacji online może opłacić ją (mock lub prawdziwa bramka w dev); rezerwacja przechodzi w `confirmed`; email z dokumentami idzie asynchronicznie; środowisko produkcyjne ma HTTPS i backup DB.

---

# Sprint 10 — Demo produkcyjne (VPS pokazowy) 🟡

**Cel:** system działa na publicznym VPS jak produkcja (HTTPS, Docker, backup, pełny flow operacyjny), ale **bez prawdziwych płatności i bez dokumentów prawnych**. Mock bramki (`PAYMENT_GATEWAY_PROVIDER=mock`) i placeholder regulaminu są **zamierzone**.

**Zakres wyłączony:** Stripe/P24/PayU, regulamin/RODO od prawnika, Twilio SMS prod.

**Dokumentacja:** [`docs/DEPLOY.md`](docs/DEPLOY.md), [`README.md`](README.md#demo-produkcyjne-vps-pokazowy).

### Taski (kolejność implementacji)

| ID | Task | Opis | Moduł / pliki | Status |
|----|------|------|---------------|--------|
| **10.1** | Wolumeny Docker prod | `private_documents_data` na `web` i `celery` — PDF widoczne dla emaili i backupu | `docker-compose.prod.yml` | ✅ |
| **10.2** | Dokumentacja zakresu demo | Strategia demo prod vs pełna prod; checklist deploy | `PROJECT_PLAN.md`, `DEPLOY.md`, `README.md` | ✅ |
| **10.3** | Szablon `.env.production` | `.env.production.example` + odniesienie w `.env.example` | ✅ |
| **10.4** | CI deploy check | `django check --deploy` w `.github/workflows/ci.yml` | ✅ |
| **10.5** | Pierwszy deploy VPS | `./scripts/deploy.sh`, `ENABLE_DEPLOY=true`, secrets SSH | `scripts/deploy.sh`, `docs/CICD.md` | ✅ |
| **10.6** | HTTPS + domena | Caddy + Let's Encrypt; `DOMAIN`, `ACME_EMAIL` | `docker-compose.prod.yml`, `deploy/Caddyfile` | ✅ |
| **10.7** | Seed na prod | `seed_demo` po deploy; konta `admin`/`manager`/`klient` | `bookings/management/commands/seed_demo.py` | ✅ |
| **10.8** | Smoke: flow publiczny | Wyszukiwarka → rezerwacja → mock payment → `confirmed` → email w logach | domena ✅ rezerwacja #20 (2026-07-18, po #88) | ✅ |
| **10.9** | Smoke: flow panelu | Wydanie → aktywny → zwrot z dopłatami → płatność → zamknięcie | domena ✅ wynajem #9 (2026-07-18) | ✅ |
| **10.10** | Smoke: portal klienta | Login `klient` / `demo1234` → lista rezerwacji → szczegóły | ręcznie na domenie / `website/tests/test_portal_views.py` | 🟡 |
| **10.11** | Runbook demo | Ścieżki testowe, konta, znane ograniczenia mock | `docs/DEMO_RUNBOOK.md` | ✅ |
| **10.12** | Baner „wersja demo” | `DEMO_SITE=True` + baner na `base_public.html` | `settings.py`, `demo_banner.html` | ✅ |
| **10.13** | Etykieta mock checkout | Tekst „wersja demonstracyjna” na `/platnosc/mock/` | `mock_payment_checkout.html` | ✅ |
| **10.14** | Backup po deploy | Cron `backup.sh` + weryfikacja `backup-restore-selftest.sh` na VPS | `scripts/install-backup-cron.sh`, `deploy.sh`, `docs/DEPLOY.md` | ✅ |

### Observability (opcjonalnie w Sprint 10 lub przenieś do 11)

| ID | Task | Opis | Status |
|----|------|------|--------|
| **10.15** | Health endpoint | `GET /health/` — DB + Redis (200/503) | ✅ |
| **10.16** | LOGGING | Konfiguracja `LOGGING` w `settings.py` (stdout, poziom INFO) | ✅ |
| **10.17** | Healthcheck compose | Redis + celery (+ web) w `docker-compose.prod.yml` | ✅ |
| **10.18** | Uptime monitoring | Dokumentacja UptimeRobot / cron `curl /health/` | `docs/DEPLOY.md` | ✅ |

### Definition of Done Sprint 10

- [x] Aplikacja dostępna pod publiczną domeną HTTPS
- [x] `seed_demo` załadowany — 18 scenariuszy do prezentacji
- [x] Pełny flow publiczny (rezerwacja + mock płatność) działa end-to-end *(domena ✅ rezerwacja #20)*
- [x] Pełny flow panelu (wydanie → zwrot → rozliczenie) działa na danych seed *(domena ✅ wynajem #9)*
- [x] Backup DB skonfigurowany (cron) — zweryfikowane na VPS 2026-07-18
- [x] Runbook demo dla prezentacji (`docs/DEMO_RUNBOOK.md`)
- [x] Health smoke (`/health/` + `/`) na https://car-rental.filipf.online

**Szacunek:** domknięcie operacyjne na VPS (10.14 + smoke ręczny 10.8–10.10).

---

# Sprint 11 — Utrzymanie i observability demo ✅

**Cel:** stabilność demo na VPS w czasie — bez zmiany zakresu biznesowego (nadal mock płatności).

**Zależności:** Sprint 10 ukończony (demo live).

### Taski

| ID | Task | Opis | Status |
|----|------|------|--------|
| **11.1** | Health + logging | Domknięcie 10.15–10.16 — **zrobione w Sprint 10** | ✅ |
| **11.2** | Uptime alerty | Monitoring zewnętrzny + alert email przy 5xx | ✅ |
| **11.3** | Celery Beat | Auto-wygasanie rezerwacji `pending_payment` (np. 48 h) | ✅ |
| **11.4** | Redis cache | Zamiana `LocMemCache` na Redis — rate limit chatu między workerami | ✅ |
| **11.5** | Backup offsite | Sync backupów na S3/rsync (dokumentacja + skrypt) | ✅ |
| **11.6** | Purge chat cron | Weryfikacja `purge_chat_messages` na prod | ✅ |
| **11.7** | Smoke test w CI | Opcjonalny job post-deploy (curl health + login panel) | ✅ |

### Definition of Done Sprint 11

- [x] Health endpoint monitorowany zewnętrznie *(docs: UptimeRobot / cron — `docs/DEPLOY.md`)*
- [x] Logi aplikacji czytelne na VPS (`docker compose logs`)
- [x] Rezerwacje `pending_payment` wygasają automatycznie
- [x] Backup offsite skonfigurowany lub udokumentowany jako świadoma rezygnacja demo

**Szacunek:** 2–3 dni roboczych (opcjonalny — po starcie demo).

---

# Sprint 12+ — Backlog (poza wersją demo)

<!-- Rozszerzenia po wdrożeniu demo — priorytetyzuj według potrzeb biznesowych -->

### Demo polish / UX v2

Te zadania są priorytetowe, jeśli demo ma wyglądać jak spójny produkt dla klienta i pracownika, a nie tylko zestaw gotowych modułów.

| ID | Task | Opis |
|----|------|------|
| 12.1 | Asystent klienta v2 | Poprawić rozumienie intencji: dostępność aut, daty względne („jutro”, „weekend”), kaucje, zasady wynajmu; zamiast generycznej odpowiedzi ma zadawać pytania doprecyzowujące albo pokazać auta/link do rezerwacji. | ✅ |
| 12.2 | Panel klienta — dostęp | Logowanie klienta po emailu albo po numerze rezerwacji; wymagane zabezpieczenia przed podglądem cudzych danych (rate limit, weryfikacja email/telefon lub magic link). | ✅ |
| 12.3 | Panel klienta — widoki | Klient może podejrzeć swoje rezerwacje, najmy oraz dokumenty przypięte do najmów/rezerwacji; dokumenty dostępne do pobrania z poziomu panelu. | ✅ |
| 12.4 | Email po rezerwacji klienta | Utworzenie rezerwacji przez klienta wysyła potwierdzenie na email: status, auto/kategoria, termin, cena/kaucja, link do panelu klienta. | ✅ |
| 12.5 | Email po wydaniu/zwrocie | Po zakończeniu wydania albo zwrotu pojazdu klient dostaje email z dokumentem/protokołem; obsługa błędów przez `EmailLog` i retry Celery. | ✅ |
| 12.6 | Panel pracownika — ekran startowy | Po wejściu do panelu pracownik widzi kafelki zamiast od razu dashboardu: „Panel administratora” oraz „Wydaj / zwróć pojazd”. | ✅ |
| 12.7 | Panel administratora bez operacji | Operacje wydania/zwrotu nie są częścią panelu administratora, bo są przeznaczone do pracy mobilnej w terenie. Admin zostaje dla dashboardów, floty, rezerwacji, płatności, dokumentów, raportów i konfiguracji. | ✅ |
| 12.8 | Panel wydaj / zwróć pojazd | Widok mobilny z dwoma kafelkami: „Wydaj pojazd” oraz „Zwróć pojazd”. | ✅ |
| 12.9 | Kolejka zwrotów | Lista wydanych pojazdów do zwrotu posortowana tak, żeby najbliżej kończące się najmy były na górze; najmy przeterminowane wyróżnione. | ✅ |
| 12.10 | Kolejka wydań | Lista rezerwacji/najmów gotowych do wydania, z priorytetem na dzisiaj i zaległe; szybkie wejście w workflow wydania. | ✅ |
| 12.11 | Mobilny panel operacyjny | Przebudować wersję mobilną panelu: obecny sidebar zajmuje zbyt dużo ekranu i jest zbędny na telefonie. Na mobile priorytetem są operacje terenowe, a większość pracy biurowej/adminowej odbywa się stacjonarnie. | ✅ |

#### Definition of Done — Demo polish / UX v2

- [x] Asystent poprawnie obsługuje pytania typu „czy są wolne auta na jutro?” i „sprawdź dostępność samochodów”.
- [x] Klient ma bezpieczny sposób wejścia do swoich rezerwacji, najmów i dokumentów.
- [x] Rezerwacja z kanału publicznego wysyła email potwierdzający.
- [x] Wydanie i zwrot wysyłają klientowi dokument/protokół emailem.
- [x] Pracownik po wejściu do panelu wybiera ścieżkę: administracja albo praca terenowa.
- [x] Operacje wydania/zwrotu są mobile-first i oddzielone od panelu administratora.
- [x] Na telefonie panel operacyjny nie pokazuje dużego sidebara; ekran jest zoptymalizowany pod szybkie wydanie/zwrot pojazdu.

### Płatności (poza zakresem demo)

- [ ] ~~Prawdziwa bramka produkcyjna~~ — **poza zakresem wersji demo**; mock jest docelowy dla wdrożenia pokazowego
- [ ] Stripe / Przelewy24 / PayU — tylko przy przejściu na pełną produkcję biznesową (Sprint 12+)

### Bezpieczeństwo i compliance (poza zakresem demo)

- [x] HTTPS na produkcji (Caddy + Let's Encrypt — task 9.9)
- [ ] Szyfrowane PDF
- [x] Audit log operacji krytycznych — `apps.audit`
- [x] Bezpieczne uploady — PR #56
- [ ] Dokumenty prawne RODO — **poza zakresem demo**
- [x] RBAC per rola (accountant vs employee) — cennik / raporty / zwrot kaucji

### Infrastruktura

- [ ] Monitoring / alerty zaawansowane (Sentry, Prometheus) — częściowo Sprint 11

### Rozszerzenia biznesowe

| ID | Task | Opis |
|----|------|------|
| 12.1 | RBAC granular | `owner_or_manager_required` na cennikach; raporty dla owner/manager/accountant; zwrot kaucji tylko owner/manager | ✅ |
| 12.2 | Dynamic pricing | Zaawansowany cennik sezonowy |
| 12.3 | i18n UI | Wielojęzyczność |
| 12.4 | HTMX dashboard | Partial refresh widgetów pulpitu |
| 12.5 | Chat eskalacja | Eskalacja do człowieka, analityka konwersji |

- [x] Raporty finansowe — `/panel/raporty/` (PR #54)
- [x] Powiadomienia SMS mock — `apps.notifications`

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
Sprint 8b (chat AI — opcjonalnie)
    ↓
Sprint 9 (płatności online + Celery + deploy)
    ↓
Sprint 9+ (raporty, SMS, seed rozbudowany) ✅
    ↓
Sprint 10 (demo produkcyjne — VPS pokazowy) 🟡 (zostało 10.10 portal)
    ↓
Sprint 11 (utrzymanie demo — opcjonalnie)
    ↓
Sprint 12 (demo polish / UX v2)  ← DONE (12.1–12.11)
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
| `apps/documents` | ✅ | ✅ |
| `apps/dashboard` | ✅ | ✅ (KPI + alerty fleet, taski 8.1–8.7) |
| `apps/website` | ✅ | ✅ (8.8–8.14) |
| Chat AI konsultant | ✅ | Sprint 8b |
| `docs/AI_CONSULTANT.md` | ✅ | — |

---

*Plik utrzymywany ręcznie przez zespół. Przy większych zmianach architektury zaktualizuj też `AGENT_CONTEXT.md` §19 (Current Project Status).*
