#!/usr/bin/env bash
# Sprawdza, czy .env.production ma wymagane klucze demo (bez wypisywania wartosci).
# Uzycie na VPS:
#   ./scripts/check-production-env.sh
#   ENV_FILE=/opt/car-rental/.env.production ./scripts/check-production-env.sh

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env.production}"

if [ ! -f "$ENV_FILE" ]; then
	echo "ERROR: brak pliku $ENV_FILE" >&2
	exit 1
fi

required=(
	DEBUG
	SECRET_KEY
	ALLOWED_HOSTS
	CSRF_TRUSTED_ORIGINS
	POSTGRES_DB
	POSTGRES_USER
	POSTGRES_PASSWORD
	POSTGRES_HOST
	CELERY_BROKER_URL
	CELERY_RESULT_BACKEND
	PAYMENT_GATEWAY_PROVIDER
	PUBLIC_SITE_BASE_URL
	DEMO_SITE
)

recommended=(
	CACHE_URL
	RESERVATION_PENDING_PAYMENT_TTL_HOURS
	LOG_LEVEL
	SECURE_SSL_REDIRECT
	# Legacy / opcjonalne — TLS jest na /opt/edge, nie w tym compose
	DOMAIN
	ACME_EMAIL
)

has_key() {
	local key="$1"
	grep -Eq "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE"
}

missing=0
echo "==> Checking required keys in $ENV_FILE"
for key in "${required[@]}"; do
	if has_key "$key"; then
		echo "OK  $key"
	else
		echo "MISSING  $key" >&2
		missing=1
	fi
done

echo "==> Recommended keys"
for key in "${recommended[@]}"; do
	if has_key "$key"; then
		echo "OK  $key"
	else
		echo "WARN  $key (zalecane — patrz .env.production.example)"
	fi
done

if grep -Eq "^[[:space:]]*SECRET_KEY[[:space:]]*=.*django-insecure" "$ENV_FILE"; then
	echo "WARN  SECRET_KEY wyglada na domyslny/insecure — zmien na produkcji" >&2
fi

if grep -Eq "^[[:space:]]*POSTGRES_HOST[[:space:]]*=[[:space:]]*postgres[[:space:]]*$" "$ENV_FILE"; then
	echo "WARN  POSTGRES_HOST=postgres — w compose prod serwis nazywa sie zwykle 'db'" >&2
fi

if [ "$missing" -ne 0 ]; then
	echo "ERROR: uzupelnij brakujace klucze (wzor: .env.production.example)" >&2
	exit 1
fi

echo "==> Env check passed"
