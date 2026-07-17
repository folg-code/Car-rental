#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
	echo "Usage: $0 --confirm <backup_dir_or_timestamp>" >&2
	echo "  Destructive: replaces DB and media from backup." >&2
	exit 1
}

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"

CONFIRM=false
if [ "${1:-}" = "--confirm" ]; then
	CONFIRM=true
	shift
fi

BACKUP_ARG="${1:-}"
[ -z "$BACKUP_ARG" ] && usage
[ "$CONFIRM" = true ] || usage

cd "$APP_DIR"

if [ -d "$BACKUP_ARG" ]; then
	SRC="$BACKUP_ARG"
elif [ -d "$BACKUP_DIR/$BACKUP_ARG" ]; then
	SRC="$BACKUP_DIR/$BACKUP_ARG"
else
	echo "ERROR: backup not found: $BACKUP_ARG" >&2
	exit 1
fi

if [ ! -f "$SRC/database.dump" ]; then
	echo "ERROR: missing $SRC/database.dump" >&2
	exit 1
fi

compose_project() {
	docker compose -f "$COMPOSE_FILE" ls -q 2>/dev/null | head -n 1
}

restore_volume() {
	local volume_suffix="$1"
	local source_dir="$2"
	local project

	[ -d "$source_dir" ] || return 0
	[ "$(ls -A "$source_dir" 2>/dev/null || true)" ] || return 0

	project=$(compose_project)
	[ -n "$project" ] || {
		echo "WARN: could not resolve compose project — skipped $volume_suffix" >&2
		return 0
	}

	echo "==> Restore volume ${volume_suffix}"
	docker run --rm \
		-v "${project}_${volume_suffix}:/data" \
		-v "$source_dir:/backup:ro" \
		alpine sh -c "rm -rf /data/* && cp -a /backup/. /data/"
}

echo "==> Stop application containers"
docker compose -f "$COMPOSE_FILE" stop web celery 2>/dev/null || true

echo "==> Restore database from $SRC/database.dump"
docker compose -f "$COMPOSE_FILE" cp "$SRC/database.dump" db:/tmp/restore.dump
docker compose -f "$COMPOSE_FILE" exec -T db sh -c '
	set -e
	dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB"
	createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
	pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl /tmp/restore.dump
	rm -f /tmp/restore.dump
'

restore_volume media_data "$SRC/media"
restore_volume private_documents_data "$SRC/private_documents"

echo "==> Restore finished from $SRC"
echo "    Start stack: docker compose -f $COMPOSE_FILE up -d"
