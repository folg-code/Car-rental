#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/car-rental}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
WEB_IMAGE="${WEB_IMAGE:?WEB_IMAGE is required}"

cd "$APP_DIR"

echo "==> Pull latest image"
docker compose -f "$COMPOSE_FILE" pull web

echo "==> Start services"
export WEB_IMAGE
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "==> Wait for database"
sleep 10

echo "==> Run migrations"
docker compose -f "$COMPOSE_FILE" run --rm web \
  python backend/manage.py migrate --noinput

echo "==> Collect static files"
docker compose -f "$COMPOSE_FILE" run --rm web \
  python backend/manage.py collectstatic --noinput

echo "==> Restart web container"
docker compose -f "$COMPOSE_FILE" restart web

echo "==> Remove dangling images"
docker image prune -f

echo "==> Deploy finished successfully"