# Docker — środowisko lokalne i produkcja

> Stan na 2026-05-20. Stack uruchomieniowy: [`docker-compose.yml`](../docker-compose.yml) (dev), [`docker-compose.prod.yml`](../docker-compose.prod.yml) (prod).

---

## Obecny stack

| Serwis | Obraz / build | Rola |
|--------|---------------|------|
| `db` | `postgres:16` | Baza danych |
| `web` | `Dockerfile` | Django (`runserver` dev / Gunicorn prod) |
| `tailwind` | `node:20` | Build CSS (tylko dev, jednorazowo) |

**Poza kontenerem (dev):** pytest, migracje — `docker compose run --rm web …`

**Wolumeny prod:** `postgres_data`, `media_data`, `static_data` (+ docelowo `private_documents` / wspólny volume z `web`).

---

## Cel na przyszłość — Celery + Redis (powiadomienia asynchroniczne)

> **Nie wdrożone w MVP Sprint 7.** Email do klienta po protokole działa **synchronicznie** w `DocumentService` / `EmailService`. Kolejny krok infrastrukturalny: wydzielenie wysyłki i alertów do kolejki zadań.

### Po co

| Odbiorca | Przykładowe powiadomienia |
|----------|---------------------------|
| **Klient** | Email z PDF protokołu wydania/zwrotu, przypomnienie o zwrocie, potwierdzenie rezerwacji |
| **Pracownik** | Nowe wydanie/zwrot w kolejce operacji, nadchodzący zwrot auta, nieopłacony wynajem, wygasające ubezpieczenie/przegląd (z `dashboard`) |

### Docelowe serwisy w Compose

```text
db          PostgreSQL (bez zmian)
redis       Broker + opcjonalnie result backend / cache krótkotrwały
web         Django (HTTP) — enqueue zadań, bez blokowania requestu
celery      Worker — wysyłka emaili, SMS (później), generacja PDF (opcjonalnie)
celery-beat Harmonogram — przypomnienia, digest dla pracowników (opcjonalnie)
```

### Szkic `docker-compose.yml` (dev — planowany)

```yaml
# --- Planowane (Sprint 9+ / infrastruktura) ---
# redis:
#   image: redis:7-alpine
#   ports:
#     - "6379:6379"
#
# celery:
#   build: .
#   command: celery -A config worker -l info
#   env_file:
#     - .env.docker
#   depends_on:
#     - db
#     - redis
#   volumes:
#     - .:/app
#
# celery-beat:
#   build: .
#   command: celery -A config beat -l info
#   env_file:
#     - .env.docker
#   depends_on:
#     - redis
```

### Szkic `docker-compose.prod.yml` (planowany)

```yaml
# redis:
#   image: redis:7-alpine
#   restart: unless-stopped
#   volumes:
#     - redis_data:/data
#
# celery:
#   image: ${WEB_IMAGE:-ghcr.io/folg-code/car-rental:latest}
#   restart: unless-stopped
#   command: celery -A config worker -l info --concurrency=2
#   env_file:
#     - .env.production
#   depends_on:
#     - db
#     - redis
#   volumes:
#     - media_data:/app/media
#     - private_documents_data:/app/private_documents
```

### Integracja z kodem (kierunek)

1. **`config/celery.py`** + `CELERY_BROKER_URL=redis://redis:6379/0`
2. **`EmailService.send_document_email`** → task `send_document_email_task.delay(document_id)` (web tylko enqueue)
3. **`notifications`** (nowy moduł lub rozszerzenie `documents` / `dashboard`):
   - taski: `notify_staff_pending_operations`, `notify_customer_protocol_email`
   - szablony email/SMS oddzielone od logiki HTTP
4. **Retry** — Celery retry + istniejący `EmailLog` (`failed` → ponowienie z panelu lub beat)
5. **Testy** — `CELERY_TASK_ALWAYS_EAGER=True` w pytest (bez Redis w CI)

### Zmienne środowiskowe (plan)

| Zmienna | Przykład |
|---------|----------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` (opcjonalnie) |
| `EMAIL_BACKEND` | SMTP prod / locmem w testach |

### Kiedy wdrożyć

- Po domknięciu **Sprint 7** (PDF + email MVP) i podstawowego **Sprint 8** (dashboard KPI — źródło alertów dla pracowników)
- Gdy synchroniczna wysyłka emaila zacznie blokować request protokołu (mobile / słabe SMTP) lub pojawią się zaplanowane digesty

**Priorytet:** średni (Sprint 9+ / infrastruktura produkcyjna). MVP paperless działa bez kolejki.

---

## Powiązane pliki

- [`docs/CICD.md`](./CICD.md) — build obrazu, deploy
- [`PROJECT_PLAN.md`](../PROJECT_PLAN.md) — Sprint 9+ backlog
- [`AGENT_CONTEXT.md`](../AGENT_CONTEXT.md) — decyzje techniczne (monolit, unikanie przedwczesnego async)
