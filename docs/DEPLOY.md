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
- [ ] `docker login ghcr.io` (jeśli obraz prywatny)
- [ ] GitHub Actions: `ENABLE_DEPLOY=true` + secrets SSH
- [ ] `./scripts/deploy.sh`
- [ ] `./scripts/backup-restore-selftest.sh`
- [ ] `./scripts/backup.sh` + cron
- [ ] Offsite sync backupów

---

## Rozwiązywanie problemów

**Caddy nie startuje** — sprawdź `DOMAIN` w `.env.production` i logi: `docker compose logs caddy`.

**Pętla przekierowań HTTPS** — upewnij się, że Caddy przekazuje ruch do `web:8000` (nagłówek `X-Forwarded-Proto` jest obsługiwany w `settings.py`).

**`dropdb` failed during restore** — zatrzymaj aplikację: `docker compose stop web celery`, potem ponów restore.

**Brak certyfikatu** — port 80 musi być dostępny z internetu (HTTP-01 ACME).
