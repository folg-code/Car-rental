# CI/CD — GitHub Actions

Repozytorium: [folg-code/Car-rental](https://github.com/folg-code/Car-rental)

> Stack Docker (dev/prod, plan Celery + Redis): [`DOCKER.md`](./DOCKER.md)

## Przegląd

| Workflow | Kiedy | Co robi |
|----------|--------|---------|
| **CI** (`ci.yml`) | Pull request → `dev` lub `main` | Ruff, Tailwind build, `django check`, pytest, test build obrazu Docker |
| **Deploy** (`deploy.yml`) | Push / merge → `main` | Uruchamia CI → buduje obraz → publikuje do GHCR → deploy na VPS (SSH) |

```text
feature/* ──► PR → dev ──► ci.yml (lint + test + docker build)
                              └── merge do dev (integracja)

dev ──► PR → main ──► deploy.yml
                        ├── ci (workflow_call)
                        ├── build-and-push → ghcr.io/folg-code/car-rental:latest
                        └── deploy (SSH) → docker compose prod na VPS
```

### Strategia gałęzi (od Sprint 10+)

| Gałąź | Rola |
|-------|------|
| `feat/*` (robocza) | Implementacja sprintu / taska — tu commitujemy na co dzień |
| `dev` | Integracja — merge z gałęzi roboczych; **bez deployu** |
| `main` | Produkcja live (VPS + domena) — merge z `dev` uruchamia deploy |

```text
feat/* ──► PR → dev ──► ci.yml (bez deployu)
dev    ──► PR → main ──► deploy.yml → VPS
```

**Nie** mergujemy gałęzi roboczej prosto do `main` — każdy update na `dev` nie restartuje produkcji.

## Wymagania w repozytorium

- Plik `.env.ci` — zmienne dla pytest w CI (commitowany, bez sekretów).
- Szablon `.env.example` — dokumentacja zmiennych na serwerze.
- Na VPS: `.env.production` (nie w git) według `.env.example`.

## Konfiguracja GitHub (jednorazowo)

### 1. Secrets (Settings → Secrets and variables → Actions)

| Secret | Opis |
|--------|------|
| `DEPLOY_HOST` | IP lub hostname VPS |
| `DEPLOY_USER` | Użytkownik SSH (np. `deploy`) |
| `DEPLOY_SSH_KEY` | Klucz prywatny SSH (cały plik PEM) |
| `DEPLOY_PATH` | Katalog aplikacji na serwerze (np. `/opt/car-rental`) |
| `GHCR_READ_TOKEN` | (Opcjonalnie) PAT z `read:packages` do `docker pull` na VPS, jeśli obraz prywatny |

`GITHUB_TOKEN` jest dostarczany automatycznie — służy do push obrazu do GHCR.

### 2. Uprawnienia pakietu GHCR

Po pierwszym deployu obraz trafi do **Packages** repozytorium.

- Jeśli pakiet **prywatny**: na VPS wykonaj `docker login ghcr.io` (użyj `GHCR_READ_TOKEN`) albo dodaj secret jak wyżej.
- Jeśli **publiczny**: w ustawieniach pakietu → *Change visibility* → Public.

### 3. Branch protection (zalecane)

Settings → Branches → rule dla `main` i `dev`:

- [x] Require status check: **Lint, build CSS, test**
- [x] Require status check: **Docker image build** (opcjonalnie)
- [x] Require PR before merging

Dzięki temu merge bez przejścia testów nie jest możliwy. Na `main` warto dodatkowo wymagać aktualnego `dev` jako bazę PR (review przed deployem).

### 4. Włączenie / wyłączenie deployu

Deploy na VPS uruchamia się tylko gdy ustawisz **zmienną repozytorium** (nie secret):

Settings → Secrets and variables → Actions → **Variables** → New repository variable:

| Variable | Value |
|----------|--------|
| `ENABLE_DEPLOY` | `true` |

Bez `ENABLE_DEPLOY=true` job **Deploy to VPS** jest pomijany (build obrazu do GHCR i tak się wykona).

> GitHub **nie pozwala** używać `secrets.*` w warunkach `if:` na poziomie joba.

## Przygotowanie VPS (pierwszy raz)

```bash
# Docker + Compose plugin
sudo apt update && sudo apt install -y docker.io docker-compose-plugin

sudo mkdir -p /opt/car-rental
sudo chown $USER:$USER /opt/car-rental
cd /opt/car-rental

# Skopiuj ręcznie lub poczekaj na pierwszy deploy z Actions:
# docker-compose.prod.yml, scripts/deploy.sh, deploy/Caddyfile

nano .env.production   # według .env.example — PRODUKCYJNE wartości
```

Przykład `.env.production`:

```env
DEBUG=False
ALLOWED_HOSTS=twoja-domena.pl,www.twoja-domena.pl
SECRET_KEY=<dlugi-losowy-klucz>
POSTGRES_DB=car_rental
POSTGRES_USER=car_rental
POSTGRES_PASSWORD=<silne-haslo>
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

```bash
# Logowanie do GHCR (jeśli obraz prywatny)
echo "<PAT>" | docker login ghcr.io -u TWOJ_GITHUB_USER --password-stdin

export WEB_IMAGE=ghcr.io/folg-code/car-rental:latest
./scripts/deploy.sh
```

## Ręczny deploy

Actions → **Deploy** → *Run workflow* (workflow_dispatch).

## Lokalne komendy (jak w CI)

```bash
npm ci && npm run build:css:prod
pip install -e ".[dev]"
ruff check backend
ruff format --check backend
python backend/manage.py check
pytest -q
```

## Produkcja — pliki

| Plik | Rola |
|------|------|
| `Dockerfile.prod` | Obraz z Gunicorn |
| `docker-compose.prod.yml` | Postgres + web + Celery + Redis (+ Caddy profil `https`) |
| `scripts/deploy.sh` | Pull + migrate + collectstatic + restart |
| `scripts/backup.sh` | Backup DB + media + private_documents |
| `scripts/install-backup-cron.sh` | Idempotentny cron backup + purge chatu + offsite (`--check`) |
| `scripts/backup-offsite.sh` | Sync backupów przez rclone (`BACKUP_OFFSITE_REMOTE`) |
| `scripts/smoke-health.sh` | Smoke `GET /health/` + `/` po deployu |
| `scripts/restore.sh` | Przywracanie z backupu (`--confirm`) |
| `scripts/backup-restore-selftest.sh` | Test roundtrip backup/restore (CI) |
| `deploy/Caddyfile` | Reverse proxy HTTPS |
| [`docs/DEPLOY.md`](./DEPLOY.md) | Checklist VPS, cron, offsite |

## Rozwiązywanie problemów

**CI pada na Ruff** — `ruff check backend && ruff format backend` lokalnie.

**Deploy pomijany** — sprawdź secret `DEPLOY_HOST`.

**`docker pull` unauthorized na VPS** — ustaw `GHCR_READ_TOKEN` lub upublicznij pakiet.

**Migracje** — uruchamiane przy starcie kontenera `web` w `docker-compose.prod.yml`.
