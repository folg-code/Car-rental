#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

cd "$APP_DIR"

if [ ! -f .env.production ]; then
	echo "ERROR: .env.production not found in $APP_DIR" >&2
	exit 1
fi

TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/$TIMESTAMP"
mkdir -p "$DEST"

echo "==> Backup database to $DEST/database.dump"
docker compose -f "$COMPOSE_FILE" exec -T db \
	sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' >"$DEST/database.dump"

echo "==> Backup media files"
mkdir -p "$DEST/media"
if docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -qx web; then
	docker compose -f "$COMPOSE_FILE" cp web:/app/media/. "$DEST/media/" \
		|| echo "WARN: media backup incomplete"
else
	echo "WARN: web not running — skipped media backup"
fi

echo "==> Backup private documents"
mkdir -p "$DEST/private_documents"
if docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -qx celery; then
	docker compose -f "$COMPOSE_FILE" cp celery:/app/private_documents/. "$DEST/private_documents/" \
		|| echo "WARN: private_documents backup incomplete"
else
	echo "WARN: celery not running — skipped private_documents backup"
fi

cat >"$DEST/manifest.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "created_at_utc": "$(date -u -Iseconds)"
}
EOF

echo "==> Prune backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} + 2>/dev/null || true

echo "==> Backup finished: $DEST"
