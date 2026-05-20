#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/car-rental}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
WEB_IMAGE="${WEB_IMAGE:?WEB_IMAGE is required}"

cd "$APP_DIR"

echo "==> Pull image: ${WEB_IMAGE}"
docker compose -f "$COMPOSE_FILE" pull web

echo "==> Run migrations and restart"
export WEB_IMAGE
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "==> Collect static files"
docker compose -f "$COMPOSE_FILE" exec -T web python backend/manage.py collectstatic --noinput

echo "==> Deploy finished"
