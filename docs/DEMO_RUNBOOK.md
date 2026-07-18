# Runbook — wersja demo produkcyjna

> Deploy VPS: [`DEPLOY.md`](./DEPLOY.md) · Zmienne: [`.env.production.example`](../.env.production.example) · Plan: [`PROJECT_PLAN.md`](../PROJECT_PLAN.md)

System działa na publicznym VPS jak produkcja (HTTPS, Docker, backup), ale **płatności są symulowane (mock)**, a regulamin to placeholder. To **zamierzone** dla wersji pokazowej.

---

## Przygotowanie serwera (jednorazowo)

```bash
# 1. Skopiuj i uzupełnij zmienne
cp .env.production.example .env.production
nano .env.production

# 2. Deploy (pull obrazu, migrate, collectstatic, restart)
export WEB_IMAGE=ghcr.io/folg-code/car-rental:latest
./scripts/deploy.sh

# 3. Dane demonstracyjne (18 scenariuszy)
docker compose -f docker-compose.prod.yml exec web python backend/manage.py seed_demo

# 4. Weryfikacja HTTPS
curl -I https://twoja-domena.pl
```

---

## Konta logowania (po `seed_demo`)

| Rola | Login | Hasło | URL |
|------|-------|-------|-----|
| Właściciel (panel) | `admin` | `demo1234` | `/konto/logowanie/` → `/panel/` |
| Kierownik (panel) | `manager` | `demo1234` | `/konto/logowanie/` |
| Klient (portal) | `klient` | `demo1234` | `/konto/logowanie/` → `/konto/` |

Hasła demo są **zamierzone** na wersji pokazowej.

---

## Ścieżka prezentacji A — klient publiczny (15 min)

1. **Strona główna** — `/`
2. **Wyszukiwarka dostępności** — `/flota/dostepnosc/` (daty za 30+ dni, auto np. KR1DEMO7)
3. **Rezerwacja online** — `/rezerwacja/` → status `oczekuje płatności`
4. **Mock płatności** — przekierowanie na `/platnosc/mock/` → „Opłać” → rezerwacja `confirmed`
5. **Potwierdzenie** — `/rezerwacja/potwierdzenie/<id>/`
6. *(Opcjonalnie)* **Asystent AI** — `/asystent/` (mock LLM, FAQ + wycena orientacyjna)

**Co pokazać:** pełny funnel bez panelu — od wyszukiwania do opłaconej rezerwacji.

---

## Ścieżka prezentacji B — panel operacyjny (20 min)

Zaloguj się jako **`admin`** / `demo1234`.

Po logowaniu wybierz tryb:

1. **Wydaj / zwróć pojazd** — praca terenowa (mobile)
2. albo **Panel administratora** — pulpit KPI

| Krok | Moduł | Co pokazać |
|------|-------|------------|
| 1 | **Start** `/panel/` | Kafelki: admin vs teren |
| 2 | **Operacje** `/panel/operacje/` | Kafelki Wydaj / Zwróć |
| 3 | **Kolejka wydań** `/panel/operacje/wydania/` | Wynajem **ops-handover-today** — wydanie dziś |
| 4 | **Wydanie** | Protokół wydania (zdjęcia, podpis) → wynajem `active` |
| 5 | **Kolejka zwrotów** `/panel/operacje/zwroty/` | **ops-return-surcharges** — dopłaty km/paliwo |
| 6 | **Admin** `/panel/admin/` | KPI, nieopłacone, alerty floty (bez kolejek wydania/zwrotu) |
| 7 | **Płatności** `/panel/platnosci/` | Rozliczenie, raporty |
| 8 | **Flota** `/panel/flota/` | Dokumenty wygasające, uszkodzenia, blokada serwisowa KR1DEMO5 |

---

## Ścieżka prezentacji C — portal klienta (5 min)

1. Wyloguj z panelu.
2. Wejdź na `/konto/logowanie-kodem/` — podaj email klienta ze seeda albo numer rezerwacji.
3. Kod OTP wyloguj z konsoli Dockera / outbox (dev) albo skrzynki.
4. Po zalogowaniu: **Portal** `/konto/` — rezerwacje i dokumenty.
5. *(Opcjonalnie)* klasyczne logowanie `klient` / `demo1234` nadal działa.

---

## Scenariusze seed (18) — szybka mapa

| Klucz seed | Co testuje |
|------------|------------|
| `history-closed-1` | Zamknięty wynajem, rozliczony, **faktura** |
| `history-closed-2` | Historia, płatność częściowa, fotelik |
| `history-weekend` | Dopłata weekendowa w cenniku |
| `ops-returned` | Zwrot bez zamknięcia, należność |
| `ops-return-surcharges` | Zwrot z dopłatami km/paliwo |
| `ops-active` | Aktywny wynajem + kaucja + portal klienta |
| `ops-handover-today` | Wydanie zaplanowane na dziś |
| `ops-scheduled-near` / `far` | Zaplanowane wydania |
| `rental-cancelled` | Anulowany wynajem przed wydaniem |
| `res-confirmed-future` | Rezerwacja bez wynajmu |
| `res-pending-payment` | Oczekuje płatności + intencja mock pending |
| `pay-intent-succeeded` | Płatność online mock succeeded |
| `res-price-list` | Cennik promo |
| `res-custom-total` | Kwota ręczna 999 PLN |
| `res-expired` | Wygasła rezerwacja |
| `res-cancelled` / `res-draft` | Anulowana / szkic |

W panelu szukaj rezerwacji po markerze `DEMO_SEED:<klucz>` w polu notatki lub po kliencie/aut z tabeli powyżej.

---

## Smoke test po deploy (checklist)

### Env na VPS (przed smoke)

Porownaj `.env.production` z `.env.production.example`, potem:

```bash
cd /opt/car-rental
./scripts/check-production-env.sh
# dopisz jesli brakuje:
# CACHE_URL=redis://redis:6379/2
# DEMO_SITE=True
# CELERY_BROKER_URL=redis://redis:6379/0
# CELERY_RESULT_BACKEND=redis://redis:6379/1
# TLS: /opt/edge na VPS (nie DOMAIN/ACME w tym compose)
./scripts/install-backup-cron.sh --check
```

Repo Variables (GitHub): opcjonalnie `SMOKE_BASE_URL=https://<domena>`.

### Smoke funkcjonalny

- [x] `SMOKE_BASE_URL=https://<domena> ./scripts/smoke-health.sh` *(OK 2026-07-18 na car-rental.filipf.online)*
- [x] `curl -I https://<domena>/` → 200
- [x] Logowanie panelu `admin` / `demo1234` *(via `/konto/logowanie/`)*
- [x] Pulpit ładuje KPI bez błędu 500
- [x] Rezerwacja publiczna + mock payment → `confirmed` *(rezerwacja #20, 2026-07-18)*
- [x] Protokół wydania dla wynajmu scheduled → active *(wynajem #9)*
- [x] PDF protokołu dostępny po wydaniu (wolumen `private_documents`) *(wydanie + zwrot)*
- [x] Portal: `klient` / `demo1234` lub `/konto/logowanie-kodem/` *(login + lista #6 + OTP page, 2026-07-18)*
- [ ] `docker compose -f docker-compose.prod.yml logs celery celery-beat --tail 20` — brak crashy
- [x] `./scripts/backup.sh` — backup OK *(20260718_091343)*
- [x] `./scripts/install-backup-cron.sh --check` — cron backup zainstalowany
- [x] Smoke panel 10.9: wydanie → zwrot z dopłatami → płatność → zamknięcie *(wynajem #9, 2026-07-18)*
- [x] Smoke publiczny 10.8: dostępność → rezerwacja → mock Opłać → confirmed *(#20, 2026-07-18)*
- [x] Smoke portal 10.10: `klient` → `/konto/` → rezerwacje → szczegóły *(#6, 2026-07-18)*

---

## Znane ograniczenia demo

| Obszar | Zachowanie |
|--------|------------|
| Płatności | Mock — `/platnosc/mock/`, brak prawdziwej karty/BLIK |
| Regulamin | Placeholder — nie jest dokumentem prawnym |
| SMS | Wyłączone lub mock — logi w bazie, bez wysyłki |
| Chat AI | Mock LLM — bez klucza OpenAI |
| Hasła | Stałe demo (`demo1234`) — nie używać na prawdziwej prod |
| Email | Domyślnie console — maile w `docker compose logs web celery` |

---

## Reset danych demo

Komenda `seed_demo` jest **idempotentna** — ponowne uruchomienie nie duplikuje scenariuszy:

```bash
docker compose -f docker-compose.prod.yml exec web python backend/manage.py seed_demo
```

Pełny reset bazy (ostrożnie — kasuje wszystko):

```bash
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python backend/manage.py migrate
docker compose -f docker-compose.prod.yml exec web python backend/manage.py seed_demo
```

---

## Pomoc techniczna

| Problem | Działanie |
|---------|-----------|
| 502 / brak odpowiedzi | `docker compose -f docker-compose.prod.yml ps` + `logs web` |
| PDF nie wysyła email | Sprawdź wolumen `private_documents` na **web** i **celery** |
| Mock payment nie działa | `PAYMENT_GATEWAY_MOCK_BASE_URL` = publiczny URL HTTPS |
| CSRF przy POST | `CSRF_TRUSTED_ORIGINS` musi zawierać `https://<domena>` |
