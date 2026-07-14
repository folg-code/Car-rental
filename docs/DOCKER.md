# Docker — środowisko lokalne i produkcja

> Stack uruchomieniowy: [`docker-compose.yml`](../docker-compose.yml) (dev), [`docker-compose.prod.yml`](../docker-compose.prod.yml) (prod).

---

## Obecny stack

| Serwis | Obraz / build | Rola |
|--------|---------------|------|
| `db` | `postgres:16` | Baza danych |
| `redis` | `redis:7-alpine` | Broker Celery (+ opcjonalnie result backend) |
| `web` | `Dockerfile` | Django (`runserver` dev / Gunicorn prod) |
| `celery` | `Dockerfile` | Worker Celery — zadania async (email w 9.8) |
| `tailwind` | `node:20` | Build CSS (tylko dev, jednorazowo) |

**Poza kontenerem (dev):** pytest, migracje — `docker compose run --rm web …`

**Wolumeny prod:** `postgres_data`, `redis_data`, `media_data`, `static_data`, `private_documents_data`.

---

## Celery + Redis (Sprint 9.7)

### Uruchomienie (dev)

```bash
docker compose up -d db redis web celery
```

Worker:

```bash
docker compose logs -f celery
```

Test task (w kontenerze web):

```bash
docker compose exec web python backend/manage.py shell -c "from apps.documents.tasks import ping; print(ping.delay().get())"
```

### Konfiguracja

| Plik | Opis |
|------|------|
| `backend/config/celery.py` | Aplikacja Celery, autodiscover tasków |
| `backend/config/settings.py` | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| `apps/documents/tasks.py` | Taski async (ping + email w 9.8) |

### Zmienne środowiskowe

| Zmienna | Przykład (Docker dev) |
|---------|------------------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` |

### Testy (pytest)

`CELERY_TASK_ALWAYS_EAGER=True` — bez Redis w CI.

### Kolejny krok (9.10)

Testy płatności — pełna integracja mock gateway + webhook + website flow.

### Produkcja (9.9)

HTTPS (Caddy), backup PostgreSQL + media, restore — [`docs/DEPLOY.md`](./DEPLOY.md).

---

## Powiązane pliki

- [`docs/CICD.md`](./CICD.md) — build obrazu, deploy
- [`docs/DEPLOY.md`](./DEPLOY.md) — HTTPS (Caddy), backup, restore
- [`PROJECT_PLAN.md`](../PROJECT_PLAN.md) — Sprint 9
- [`AGENT_CONTEXT.md`](../AGENT_CONTEXT.md) — decyzje techniczne
