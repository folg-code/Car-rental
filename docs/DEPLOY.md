# Deploy produkcyjny — HTTPS i backup (Sprint 9.9)

> CI/CD: [`CICD.md`](./CICD.md) · Docker stack: [`DOCKER.md`](./DOCKER.md)

---

## Przegląd

| Element | Plik / serwis |
|---------|----------------|
| Reverse proxy HTTPS | **`/opt/edge`** na VPS (osobny stack Caddy) — nie ten Compose |
| Aplikacja | `web` (Gunicorn `127.0.0.1:8000`), `celery`, `celery-beat`, `redis`, `db` |
| Cache | Redis (`CACHE_URL`, baza /2) — rate limity chatu i portalu |
| Deploy | `scripts/deploy.sh` (pull, migrate, collectstatic) — **bez** Caddy |
| Backup | `scripts/backup.sh` |
| Restore | `scripts/restore.sh --confirm <timestamp>` |
| Test odtworzenia | `scripts/backup-restore-selftest.sh` (CI + VPS) |

---

## HTTPS (edge na VPS)

Publiczny TLS i routing domen prowadzi **`/opt/edge`** (nie `docker-compose.prod.yml`).

| Host | Upstream |
|------|----------|
| `car-rental.filipf.online` | `web:8000` (sieć Dockera `car-rental_default`) |
| `dashboard.filipf.online` | host `:8080` (osobny projekt) |

Źródło prawdy Caddy: `/opt/edge/caddy/Caddyfile` (infra na VPS, poza tym repo).

### Wymagania po recreate edge

- Sieć `car-rental_default` musi być podpięta pod `edge-caddy` (zdefiniowane w `/opt/edge/docker-compose.yml`).
- Edge montuje external volumes: `car-rental_static_data`, `car-rental_media_data`.
- Aplikacja nasłuchuje lokalnie: `127.0.0.1:8000` (oraz `web:8000` w sieci compose).

### Zmienne Django (`.env.production`)

```env
DEBUG=False
ALLOWED_HOSTS=car-rental.filipf.online
CSRF_TRUSTED_ORIGINS=https://car-rental.filipf.online
PUBLIC_SITE_BASE_URL=https://car-rental.filipf.online
SECURE_SSL_REDIRECT=True
SECRET_KEY=<dlugi-losowy-klucz>
```

`DOMAIN` / `ACME_EMAIL` są **legacy** (stary app-Caddy) — nie startują już HTTPS w tym projekcie.

### Deploy aplikacji (bez Caddy)

```bash
export WEB_IMAGE=ghcr.io/folg-code/car-rental:latest
./scripts/deploy.sh
```

Stack podnosi tylko `db`, `web`, `redis`, `celery`, `celery-beat`.  
**Nie** uruchamiaj `COMPOSE_PROFILES=https` — zabierzesz :80/:443 od edge.

### Weryfikacja

```bash
curl -I https://car-rental.filipf.online
curl -fsS https://car-rental.filipf.online/health/
docker compose -f docker-compose.prod.yml ps
# Edge (osobno):
cd /opt/edge && docker compose ps
```

`deploy/Caddyfile` w tym repo to tylko **legacy / local** — nie commitować tu upstreamów dashboardu.

---

## Email (SMTP)

Rezerwacje i dokumenty wysyłają maile przez Celery. Domyślnie w dev: `console` (logi).

### Dev — podgląd w logach

```bash
docker compose logs -f web celery
```

### Wysyłka na prawdziwą skrzynkę (np. Gmail)

W `.env.docker` lub `.env.local`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=twoj-email@gmail.com
EMAIL_HOST_PASSWORD=haslo-aplikacji-google
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=twoj-email@gmail.com
```

Po zmianie: `docker compose restart web celery`.

**Gmail:** włącz 2FA i wygeneruj hasło aplikacji w koncie Google.

**SendGrid / inny dostawca:** ustaw `EMAIL_HOST` i port według dokumentacji (TLS 587 lub SSL 465 + `EMAIL_USE_SSL=True`).

### Produkcja

W `.env.production`:

```env
PUBLIC_SITE_BASE_URL=https://twoja-domena.pl
DEFAULT_FROM_EMAIL=noreply@twoja-domena.pl
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.twoj-dostawca.pl
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@twoja-domena.pl
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
```

---

## Backup

### Co jest backupowane

| Zasób | Plik / katalog w backupie |
|-------|---------------------------|
| PostgreSQL | `database.dump` (format custom `pg_dump -Fc`) |
| Media publiczne | `media/` |
| PDF prywatne | `private_documents/` |
| Metadane | `manifest.json` |

Domyślny katalog: `/opt/car-rental/backups/<YYYYMMDD_HHMMSS>/`

### Ręczny backup

```bash
cd /opt/car-rental
./scripts/backup.sh
```

Opcjonalne zmienne:

| Zmienna | Domyślnie |
|---------|-----------|
| `BACKUP_DIR` | `$APP_DIR/backups` |
| `BACKUP_RETENTION_DAYS` | `14` |

Stare backupy (katalogi) są usuwane automatycznie po przekroczeniu retencji.

### Cron (codziennie o 03:00)

Zalecany sposób — idempotentny instalator (uruchamiany też na końcu `deploy.sh`):

```bash
cd /opt/car-rental
./scripts/install-backup-cron.sh
./scripts/install-backup-cron.sh --check
```

Skrypt ustawia:

| Godzina | Zadanie | Log |
|---------|---------|-----|
| 03:00 | `./scripts/backup.sh` | `$APP_DIR/logs/backup.log` |
| 04:00 | `purge_chat_messages` | `$APP_DIR/logs/chat-purge.log` |
| 05:00 | `./scripts/backup-offsite.sh` | `$APP_DIR/logs/backup-offsite.log` |

`backup-offsite.sh` kończy się sukcesem bez syncu, gdy brak `BACKUP_OFFSITE_REMOTE` (świadoma rezygnacja w demo).

Wyłączenie przy deployu: `INSTALL_BACKUP_CRON=0 ./scripts/deploy.sh`.

Ręcznie (crontab):

```cron
0 3 * * * cd /opt/car-rental && ./scripts/backup.sh >> /opt/car-rental/logs/backup.log 2>&1
0 4 * * * cd /opt/car-rental && docker compose -f docker-compose.prod.yml run --rm web python backend/manage.py purge_chat_messages >> /opt/car-rental/logs/chat-purge.log 2>&1
0 5 * * * cd /opt/car-rental && ./scripts/backup-offsite.sh >> /opt/car-rental/logs/backup-offsite.log 2>&1
```

### Offsite (zalecane)

Ustaw w `.env.production` (albo w środowisku crona):

```bash
BACKUP_OFFSITE_REMOTE=remote:car-rental-backups
```

Wymaga zainstalowanego i skonfigurowanego `rclone` na VPS. Ręcznie:

```bash
cd /opt/car-rental
./scripts/backup-offsite.sh
```

Bez `BACKUP_OFFSITE_REMOTE` skrypt wypisuje `SKIP` i wychodzi z kodem 0 — akceptowalne dla wersji demo.

---

## Restore

**Operacja destrukcyjna** — nadpisuje bazę i wolumeny media.

```bash
cd /opt/car-rental
./scripts/restore.sh --confirm 20260714_030000
# lub pełna ścieżka:
./scripts/restore.sh --confirm /opt/car-rental/backups/20260714_030000
```

Po restore uruchom ponownie stack:

```bash
./scripts/deploy.sh
```

---

## Test odtworzenia

Przed pierwszym backupem produkcyjnym (oraz w CI):

```bash
./scripts/backup-restore-selftest.sh
```

Skrypt:

1. Podnosi tymczasową bazę Postgres (tylko `db`).
2. Tworzy tabelę-marker, robi backup, usuwa dane.
3. Przywraca backup i weryfikuje marker.

---

## Checklist pierwszego deployu VPS

- [ ] Docker + Compose plugin
- [ ] Edge TLS na VPS: `/opt/edge` (80/443) + sieć `car-rental_default`
- [ ] `.env.production` według `.env.production.example`
- [ ] `DEBUG=False`, silny `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `PUBLIC_SITE_BASE_URL`
- [ ] `PAYMENT_GATEWAY_PROVIDER=mock` — **zamierzone** dla wersji demo (strona `/platnosc/mock/`)
- [ ] `EMAIL_BACKEND=smtp` lub `console` (demo: maile w logach wystarczą)
- [ ] `docker login ghcr.io` (jeśli obraz prywatny)
- [ ] GitHub Actions: `ENABLE_DEPLOY=true` + secrets SSH
- [ ] `./scripts/deploy.sh` (app stack — **bez** Caddy na 80/443)
- [ ] `docker compose -f docker-compose.prod.yml exec web python backend/manage.py seed_demo`
- [ ] `./scripts/backup-restore-selftest.sh`
- [ ] `./scripts/install-backup-cron.sh` (+ `--check`) albo `./scripts/backup.sh` + ręczny cron
- [ ] Offsite sync backupów (opcjonalnie dla demo)

### Wersja demo produkcyjna (pokazowa)

Wdrożenie na VPS **nie wymaga** prawdziwej bramki płatności ani regulaminu od prawnika. System ma demonstrować pełny flow operacyjny:

| Element | Demo prod | Pełna produkcja biznesowa |
|---------|-----------|---------------------------|
| Płatności online | Mock (`/platnosc/mock/`) | Stripe / P24 / PayU |
| Regulamin / RODO | Placeholder w UI | Treści prawne |
| Konta po seedzie | `admin` / `demo1234` | Silne hasła, bez seed_demo |
| SMS | `SMS_ENABLED=False` lub mock | Twilio |

Po deploy uruchom `seed_demo` — 18 scenariuszy (wynajmy, płatności mock, portal klienta). Szczegóły kont: [`README.md`](../README.md#dane-demo-seed_demo). **Runbook prezentacji:** [`docs/DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md).

---

## Monitoring uptime (Sprint 10.18)

Endpoint: `GET https://<DOMAIN>/health/` — zwraca `200` gdy DB i Redis odpowiadają, inaczej `503`.

### Opcja A — UptimeRobot (lub analog)

1. Nowy monitor typu **HTTPS**.
2. URL: `https://twoja-domena.pl/health/`
3. Interval: 5 min.
4. Alert email przy status ≠ 200 (próg 2–3 nieudane sprawdzenia).

Po skonfigurowaniu alertu e-mail task Sprint **11.2** jest spełniony dla demo.

### Opcja B — cron na VPS

```bash
# co 5 minut — log + opcjonalny mail przy błędzie
*/5 * * * * curl -fsS -o /dev/null -w "%{http_code}" https://twoja-domena.pl/health/ \
  | grep -q 200 || logger -t car-rental-health "health check failed"
```

### Smoke po deployu

```bash
SMOKE_BASE_URL=https://twoja-domena.pl ./scripts/smoke-health.sh
```

Sprawdza `GET /health/` oraz `GET /` (HTTP 200).

Logi aplikacji (Gunicorn / Celery) idą na stdout kontenerów — `docker compose -f docker-compose.prod.yml logs -f web celery`. Poziom: `LOG_LEVEL` (domyślnie `INFO`).

---

## Sentry — błędy aplikacji z alertem

Uptime (`/health/`) łapie downtime; **Sentry** łapie wyjątki 500 i błędy Celery, gdy serwis działa.

### Włączenie

1. Załóż projekt [Sentry](https://sentry.io) (platforma **Django**).
2. Skopiuj **DSN** → w `.env.production` na VPS:

```env
SENTRY_DSN=https://…@….ingest.sentry.io/…
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
SENTRY_SEND_DEFAULT_PII=False
```

3. W Sentry: **Alerts → Create Alert** (np. „When an event is seen” → email).
4. Redeploy / restart `web` i `celery` (SDK ładuje się przy starcie Django).

Bez `SENTRY_DSN` (lub puste) integracja jest wyłączona — lokalnie i na demo bez konta nic nie wysyła.

`SENTRY_SEND_DEFAULT_PII=False` (domyślnie) — bez automatycznego wysyłania danych użytkownika (RODO). Opcjonalnie `SENTRY_RELEASE` (np. tag obrazu GHCR) ułatwia grupowanie po deployu.

### Weryfikacja

W shellu kontenera `web` (tylko na chwilę, potem usuń):

```python
import sentry_sdk
sentry_sdk.capture_message("sentry-smoke-test")
```

W Issues w Sentry powinien pojawić się event.

---

## Rozwiązywanie problemów

**502 / brak HTTPS** — sprawdź `/opt/edge` (`docker compose ps`, logi Caddy). Aplikacja ma działać na `127.0.0.1:8000` / `web:8000`; edge musi być w sieci `car-rental_default`.

**Pętla przekierowań HTTPS** — upewnij się, że edge przekazuje ruch do `web:8000` (nagłówek `X-Forwarded-Proto` jest obsługiwany w `settings.py`).

**`dropdb` failed during restore** — zatrzymaj aplikację: `docker compose stop web celery`, potem ponów restore.

**Porty 80/443 zajęte** — nie uruchamiaj app-Caddy (`COMPOSE_PROFILES=https`). Usuń legacy: `docker rm -f` kontenera `car-rental-*-caddy*`.

**Brak certyfikatu** — certy wystawia `/opt/edge` (Let's Encrypt); port 80 musi być wolny dla ACME na edge.