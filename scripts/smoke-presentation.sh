#!/usr/bin/env bash
# Smoke ścieżki prezentacji: publiczne URL + (opcjonalnie) seed check w kontenerze.
# Użycie:
#   SMOKE_BASE_URL=https://example.com ./scripts/smoke-presentation.sh
#   COMPOSE_FILE=docker-compose.prod.yml ./scripts/smoke-presentation.sh   # + seed --check-only

set -Eeuo pipefail

BASE_URL="${SMOKE_BASE_URL:-}"
if [ -z "$BASE_URL" ]; then
	echo "Usage: SMOKE_BASE_URL=https://your-domain ./scripts/smoke-presentation.sh" >&2
	exit 2
fi

BASE_URL="${BASE_URL%/}"

check_get() {
	local path="$1"
	local url="${BASE_URL}${path}"
	local code
	echo "==> GET $url"
	code="$(curl -fsS -o /dev/null -w "%{http_code}" "$url" || true)"
	if [ "$code" != "200" ]; then
		echo "ERROR: $path returned HTTP $code" >&2
		exit 1
	fi
	echo "OK $path ($code)"
}

check_get "/health/"
check_get "/"
check_get "/flota/"
check_get "/flota/dostepnosc/"
check_get "/asystent/"
check_get "/konto/logowanie/"
check_get "/faq/"

COMPOSE_FILE="${COMPOSE_FILE:-}"
if [ -n "$COMPOSE_FILE" ]; then
	echo "==> seed_demo --check-only (compose: $COMPOSE_FILE)"
	docker compose -f "$COMPOSE_FILE" exec -T web \
		python backend/manage.py seed_demo --check-only
	echo "OK presentation seed check"
fi

echo "==> Presentation smoke finished"
