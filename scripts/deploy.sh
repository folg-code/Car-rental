#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/car-rental}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
WEB_IMAGE="${WEB_IMAGE:?WEB_IMAGE is required}"

cd "$APP_DIR"

if [ -f .env.production ]; then
	set -a
	# shellcheck disable=SC1091
	source .env.production
	set +a
fi

# Publiczny TLS = /opt/edge na VPS (nie ten Compose).
# Nigdy nie ustawiaj COMPOSE_PROFILES=https — stary profil Caddy
# mapował :80/:443 i zabierał porty edge.
unset COMPOSE_PROFILES
echo "==> App stack only (web/celery/db/redis) — TLS via /opt/edge"

echo "==> Pull latest image"
docker compose -f "$COMPOSE_FILE" pull web celery

echo "==> Start services"
export WEB_IMAGE
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# Usuń legacy kontener Caddy z poprzednich deployów (trzymał 80/443).
legacy="$(docker ps -a --format '{{.Names}}' | grep -E '^car-rental[-_]caddy' || true)"
if [ -n "$legacy" ]; then
	echo "==> Removing legacy app-Caddy container(s): $legacy"
	# shellcheck disable=SC2086
	docker rm -f $legacy 2>/dev/null || true
fi

echo "==> Wait for database"
sleep 10

echo "==> Run migrations"
docker compose -f "$COMPOSE_FILE" run --rm web \
	python backend/manage.py migrate --noinput

echo "==> Ensure writable volume permissions"
docker compose -f "$COMPOSE_FILE" run --rm --user root web \
	sh -c "mkdir -p /app/staticfiles /app/media && chown -R app:app /app/staticfiles /app/media"
docker compose -f "$COMPOSE_FILE" run --rm --user root celery \
	sh -c "mkdir -p /app/private_documents /app/media && chown -R app:app /app/private_documents /app/media"

echo "==> Collect static files"
docker compose -f "$COMPOSE_FILE" run --rm web \
	python backend/manage.py collectstatic --noinput

echo "==> Restart application containers"
docker compose -f "$COMPOSE_FILE" restart web celery

echo "==> Remove dangling images"
docker image prune -f

if [ "${INSTALL_BACKUP_CRON:-1}" = "1" ]; then
	echo "==> Ensure daily backup cron"
	if [ -x "$APP_DIR/scripts/install-backup-cron.sh" ]; then
		APP_DIR="$APP_DIR" COMPOSE_FILE="$COMPOSE_FILE" \
			"$APP_DIR/scripts/install-backup-cron.sh" \
			|| echo "WARN: backup cron install failed (non-fatal)"
	else
		echo "WARN: scripts/install-backup-cron.sh missing — skip cron"
	fi
else
	echo "==> INSTALL_BACKUP_CRON=0 — skipped backup cron"
fi

echo "==> Deploy finished successfully"
