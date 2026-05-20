# Plan prac — Car Rental Operations Platform

> **Jak używać tego pliku**
> - Aktualizuj sekcję **Status projektu** po każdej większej zmianie.
> - Zaznaczaj `[x]` przy ukończonych zadaniach; zostaw `[ ]` dla otwartych.
> - Nowe bieżące zadania dopisuj w **Aktywne TODO**; po zakończeniu przenoś do **Zrobione**.
> - Szczegóły architektury i reguły biznesowe: [`AGENT_CONTEXT.md`](./AGENT_CONTEXT.md).

---

## Status projektu

| Pole | Wartość |
|------|---------|
| **Aktualny etap** | Sprint 0 — fundament (ukończony) |
| **Następny sprint** | Sprint 1 — struktura aplikacji + accounts |
| **Postęp ogólny** | ~15% (infrastruktura; brak domeny biznesowej) |
| **Ostatnia aktualizacja** | 2026-05-20 |
| **Branch** | `main` |
| **Repozytorium** | 3 commity; `backend/apps/` lokalnie, nie w git |

### Legenda postępu sprintu

- `⬜ nie rozpoczęty`
- `🟡 w toku`
- `✅ ukończony`

| Sprint | Nazwa | Status | Postęp |
|--------|-------|--------|--------|
| 0 | Fundament techniczny | ✅ | 100% |
| 1 | Struktura apps + accounts | ⬜ | 0% |
| 2 | fleet (flota) | ⬜ | 0% |
| 3 | bookings (rezerwacje) | ⬜ | 0% |
| 4 | pricing (cennik + snapshoty) | ⬜ | 0% |
| 5 | Rental + payments MVP | ⬜ | 0% |
| 6 | operations (wydanie/zwrot) | ⬜ | 0% |
| 7 | documents (PDF, faktury) | ⬜ | 0% |
| 8 | dashboard + website | ⬜ | 0% |
| 9+ | Produkcja i integracje | ⬜ | backlog |

---

## Aktywne TODO

<!-- Bieżące zadania — edytuj na bieżąco -->

- [ ] Zdecydować: zachować `apps/core` czy usunąć na rzecz docelowych appów
- [ ] Dodać `backend/apps/` do gita i podłączyć w `INSTALLED_APPS`
- [ ] Rozpocząć Sprint 1 (accounts + layout wewnętrzny)

---

## Zrobione (ostatnie)

<!-- Przenoś tu ukończone TODO z sekcji powyżej -->

- [x] Bootstrap Django + PostgreSQL
- [x] Docker Compose (db + web)
- [x] TailwindCSS + HTMX w szablonie bazowym
- [x] Pytest + Ruff + pre-commit
- [x] Dokumentacja architektury (`AGENT_CONTEXT.md`)
- [x] Strona startowa `/` + Django admin

---

## Dziennik postępów

<!-- Krótkie wpisy: data — co zrobiono -->

| Data | Sprint | Opis |
|------|--------|------|
| 2026-05-20 | 0 | Utworzono plan prac; potwierdzono stan: infrastruktura gotowa, domena 0% |
| | | |
| | | |

---

## Blokery i notatki

<!-- Problemy, decyzje, ryzyka -->

| Data | Opis | Status |
|------|------|--------|
| 2026-05-20 | `backend/apps/core/` — szkielet lokalny, niezacommitowany, nie w `INSTALLED_APPS` | otwarty |
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

# Sprint 1 — Struktura aplikacji + accounts ⬜

**Cel:** gotowa baza pod domenę — auth, layout wewnętrzny, konwencje kodu.

### Struktura projektu

- [ ] Uporządkować `backend/apps/` (usunąć lub przekształcić `core`)
- [ ] Konwencja nazw: `apps.<nazwa>` w `INSTALLED_APPS`
- [ ] Szkielet katalogów: `services/`, `selectors/` (wzorzec dla kolejnych appów)
- [ ] Commit i push struktury apps

### App `accounts`

- [ ] Model użytkownika (custom `User` lub rozszerzenie)
- [ ] Role: owner, manager, employee, accountant, customer
- [ ] Login / logout
- [ ] Uprawnienia bazowe (kto widzi panel wewnętrzny)

### Ustawienia i UI

- [ ] `base_internal.html` — layout panelu operacyjnego
- [ ] Nawigacja wewnętrzna (placeholder pod przyszłe moduły)
- [ ] `LANGUAGE_CODE` / `TIME_ZONE` (np. `pl`, `Europe/Warsaw`)
- [ ] `MEDIA_ROOT`, `MEDIA_URL`, `STATIC_ROOT` (przygotowanie pod zdjęcia/PDF)
- [ ] `ALLOWED_HOSTS`, podział settings dev/prod (szkic)

### Testy

- [ ] Test logowania
- [ ] Test dostępu do widoku wewnętrznego

**Definition of Done:** zalogowany pracownik widzi pusty panel wewnętrzny; migracje w Dockerze OK.

---

# Sprint 2 — fleet (flota) ⬜

**Cel:** zarządzanie pojazdami i blokadami dostępności (~15 aut).

### Modele

- [ ] `CarCategory`
- [ ] `Car`
- [ ] `CarImage`
- [ ] `CarDocument`
- [ ] `AvailabilityBlock`
- [ ] `Damage` (historia globalna, niezależna od protokołów)
- [ ] `DamagePhoto`
- [ ] `RepairRecord`

### UI / admin

- [ ] CRUD aut w panelu wewnętrznym
- [ ] CRUD kategorii
- [ ] Zarządzanie blokadami dostępności (serwis, ręczne)
- [ ] Lista i edycja uszkodzeń per auto

### Logika

- [ ] `AvailabilityService` v1 — dostępność **wyliczana**, bez pola `is_available` na `Car`
- [ ] Selektory zapytań (bez mutacji stanu)

### Testy

- [ ] Nakładające się `AvailabilityBlock` — odrzucenie
- [ ] Podstawowe zapytania o wolne auta w przedziale dat

**Definition of Done:** pełna flota w systemie; ręczna blokada serwisowa działa.

---

# Sprint 3 — bookings (rezerwacje + klienci) ⬜

**Cel:** intent rezerwacji z walidacją dostępności.

### Modele

- [ ] `Customer`
- [ ] `Reservation` + statusy: draft, pending_payment, confirmed, cancelled, expired, converted_to_rental

### UI

- [ ] Formularz tworzenia rezerwacji (auto + daty + klient)
- [ ] Lista rezerwacji z filtrami statusów
- [ ] Anulowanie / edycja (wg uprawnień)

### Logika

- [ ] `ReservationService` — create, cancel, expire
- [ ] Walidacja dostępności przez `AvailabilityService`

### Testy

- [ ] Konflikt dat — błąd
- [ ] Przejścia statusów

**Definition of Done:** pracownik zakłada rezerwację z poprawną walidacją dostępności.

---

# Sprint 4 — pricing (cennik + snapshoty) ⬜

**Cel:** naliczanie opłat oddzielone od płatności i faktur (§8 AGENT_CONTEXT).

### Modele

- [ ] `PriceList`, `DailyRate`, `PricingRule`, `ExtraService`
- [ ] `PriceLine` — snapshot przy rezerwacji

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

| Komponent | W repo | Działa |
|-----------|--------|--------|
| Django + config | ✅ | ✅ |
| Docker Compose | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ |
| Tailwind + HTMX | ✅ | ✅ |
| Pytest / Ruff | ✅ | ✅ |
| `AGENT_CONTEXT.md` | ✅ | — |
| `PROJECT_PLAN.md` | ✅ | — |
| `apps/accounts` | ❌ | — |
| `apps/fleet` | ❌ | — |
| `apps/bookings` | ❌ | — |
| `apps/pricing` | ❌ | — |
| `apps/payments` | ❌ | — |
| `apps/operations` | ❌ | — |
| `apps/documents` | ❌ | — |
| `apps/dashboard` | ❌ | — |
| `apps/website` | ❌ | — |

---

*Plik utrzymywany ręcznie przez zespół. Przy większych zmianach architektury zaktualizuj też `AGENT_CONTEXT.md` §19 (Current Project Status).*
