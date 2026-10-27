#!/usr/bin/env bash
# Lekki smoke po deployu: health (+ opcjonalnie strona glowna).
# Uzycie:
#   SMOKE_BASE_URL=https://example.com ./scripts/smoke-health.sh

set -Eeuo pipefail

BASE_URL="${SMOKE_BASE_URL:-}"
if [ -z "$BASE_URL" ]; then
	echo "Usage: SMOKE_BASE_URL=https://your-domain ./scripts/smoke-health.sh" >&2
	exit 2
fi

BASE_URL="${BASE_URL%/}"
HEALTH_URL="$BASE_URL/health/"

echo "==> GET $HEALTH_URL"
code="$(curl -fsS -o /tmp/car-rental-health.json -w "%{http_code}" "$HEALTH_URL")"
if [ "$code" != "200" ]; then
	echo "ERROR: health returned HTTP $code" >&2
	cat /tmp/car-rental-health.json >&2 || true
	exit 1
fi
echo "OK health ($code)"

echo "==> GET $BASE_URL/"
home_code="$(curl -fsS -o /dev/null -w "%{http_code}" "$BASE_URL/")"
if [ "$home_code" != "200" ]; then
	echo "ERROR: home returned HTTP $home_code" >&2
	exit 1
fi
echo "OK home ($home_code)"
echo "==> Smoke finished"
