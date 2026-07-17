#!/usr/bin/env bash

# Roundtrip test: pg_dump -> pg_restore (task 9.9).
# Uzywany w CI i na VPS przed pierwszym backupem produkcyjnym.

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
SELFTEST_ENV="${SELFTEST_ENV:-$APP_DIR/.env.production.selftest}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/.backup-selftest}"

cd "$APP_DIR"

cleanup() {
	docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" down -v --remove-orphans 2>/dev/null || true
	rm -f "$SELFTEST_ENV"
	rm -rf "$BACKUP_DIR"
}

trap cleanup EXIT

cat >"$SELFTEST_ENV" <<'EOF'
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=selftest-only-not-for-production
POSTGRES_DB=car_rental_selftest
POSTGRES_USER=car_rental
POSTGRES_PASSWORD=selftest-db-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
EOF

cp "$SELFTEST_ENV" .env.production

echo "==> Start database"
docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" up -d db

echo "==> Wait for database health"
for _ in $(seq 1 30); do
	if docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" exec -T db \
		pg_isready -U car_rental -d car_rental_selftest >/dev/null 2>&1; then
		break
	fi
	sleep 2
done

echo "==> Seed marker table"
docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" exec -T db \
	psql -U car_rental -d car_rental_selftest -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE _backup_selftest (
	id integer PRIMARY KEY,
	marker text NOT NULL
);
INSERT INTO _backup_selftest (id, marker) VALUES (1, 'ok');
SQL

export BACKUP_DIR
./scripts/backup.sh

echo "==> Drop marker table (simulate data loss)"
docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" exec -T db \
	psql -U car_rental -d car_rental_selftest -v ON_ERROR_STOP=1 \
	-c "DROP TABLE _backup_selftest;"

LATEST_BACKUP=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
[ -n "$LATEST_BACKUP" ] || {
	echo "ERROR: no backup directory created" >&2
	exit 1
}

./scripts/restore.sh --confirm "$LATEST_BACKUP"

MARKER=$(
	docker compose -f "$COMPOSE_FILE" --env-file "$SELFTEST_ENV" exec -T db \
		psql -U car_rental -d car_rental_selftest -tAc \
		"SELECT marker FROM _backup_selftest WHERE id = 1;"
)

if [ "$(echo "$MARKER" | tr -d '[:space:]')" != "ok" ]; then
	echo "ERROR: restore verification failed (marker=$MARKER)" >&2
	exit 1
fi

echo "==> Backup/restore selftest passed"
