# Deploy produkcyjny — HTTPS i backup (Sprint 9.9)

> CI/CD: [`CICD.md`](./CICD.md) · Docker stack: [`DOCKER.md`](./DOCKER.md)

---

## Przegląd

| Element | Plik / serwis |
|---------|----------------|
| Reverse proxy HTTPS | `caddy` (profil `https`) + `deploy/Caddyfile` |
| Aplikacja | `web` (Gunicorn), `celery`, `redis`, `db` |
| Deploy | `scripts/deploy.sh` (pull, migrate, collectstatic) |
| Backup | `scripts/backup.sh` |
| Restore | `scripts/restore.sh --confirm <timestamp>` |
| Test odtworzenia | `scripts/backup-restore-selftest.sh` (CI + VPS) |

---

## HTTPS (Caddy)

### 1. DNS

Wskaz `A` / `AAAA` domeny na IP VPS.

### 2. Zmienne w `.env.production`

```env
DEBUG=False
ALLOWED_HOSTS=twoja-domena.pl,www.twoja-domena.pl
DOMAIN=twoja-domena.pl
ACME_EMAIL=admin@twoja-domena.pl
SECRET_KEY=<dlugi-losowy-klucz>
SECURE_SSL_REDIRECT=True
```

Caddy automatycznie wystawia certyfikat Let's Encrypt (porty **80** i **443** muszą być otwarte).

### 3. Uruchomienie ze profilem HTTPS

`scripts/deploy.sh` włącza profil `https`, gdy `DOMAIN` jest ustawione:

```bash
export WEB_IMAGE=ghcr.io/folg-code/car-rental:latest
./scripts/deploy.sh
```

Ręcznie:

```bash
COMPOSE_PROFILES=https docker compose -f docker-compose.prod.yml up -d
```

### 4. Weryfikacja

```bash
curl -I https://twoja-domena.pl
docker compose -f docker-compose.prod.yml logs caddy --tail 50
```

Statyczne pliki (`/static/*`) serwuje Caddy z wolumenu `static_data`.

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

```cron
0 3 * * * cd /opt/car-rental && ./scripts/backup.sh >> /var/log/car-rental-backup.log 2>&1
0 4 * * * cd /opt/car-rental && docker compose -f docker-compose.prod.yml run --rm web python backend/manage.py purge_chat_messages >> /var/log/car-rental-chat-purge.log 2>&1
```

### Offsite (zalecane)

Skopiuj `backups/` poza VPS (np. `rclone` do S3 / Backblaze / innego serwera):

```bash
rclone sync /opt/car-rental/backups remote:car-rental-backups
```

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
- [ ] `.env.production` według `.env.example`
- [ ] `DOMAIN` + `ACME_EMAIL` (HTTPS)
- [ ] `DEBUG=False`, silny `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- [ ] `PAYMENT_GATEWAY_PROVIDER=mock` — **zamierzone** dla wersji demo (strona `/platnosc/mock/`)
- [ ] `EMAIL_BACKEND=smtp` lub `console` (demo: maile w logach wystarczą)
- [ ] `docker login ghcr.io` (jeśli obraz prywatny)
- [ ] GitHub Actions: `ENABLE_DEPLOY=true` + secrets SSH
- [ ] `./scripts/deploy.sh`
- [ ] `docker compose -f docker-compose.prod.yml exec web python backend/manage.py seed_demo`
- [ ] `./scripts/backup-restore-selftest.sh`
- [ ] `./scripts/backup.sh` + cron
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

## Rozwiązywanie problemów

**Caddy nie startuje** — sprawdź `DOMAIN` w `.env.production` i logi: `docker compose logs caddy`.

**Pętla przekierowań HTTPS** — upewnij się, że Caddy przekazuje ruch do `web:8000` (nagłówek `X-Forwarded-Proto` jest obsługiwany w `settings.py`).

**`dropdb` failed during restore** — zatrzymaj aplikację: `docker compose stop web celery`, potem ponów restore.

**Brak certyfikatu** — port 80 musi być dostępny z internetu (HTTP-01 ACME).
