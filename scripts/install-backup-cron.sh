#!/usr/bin/env bash
# Idempotentnie instaluje cron: codzienny backup DB/media + purge wiadomości chatu.
# Użycie (na VPS):
#   ./scripts/install-backup-cron.sh
#   ./scripts/install-backup-cron.sh --check

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOG_DIR="${BACKUP_LOG_DIR:-$APP_DIR/logs}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
MARKER_BEGIN="# BEGIN car-rental-managed-cron"
MARKER_END="# END car-rental-managed-cron"

usage() {
	echo "Usage: $0 [--check|--help]" >&2
	echo "  Installs daily backup (03:00) and chat purge (04:00) cron entries." >&2
}

strip_managed_block() {
	awk -v begin="$MARKER_BEGIN" -v end="$MARKER_END" '
		$0 == begin { skip = 1; next }
		$0 == end { skip = 0; next }
		!skip { print }
	'
}

managed_block() {
	cat <<EOF
$MARKER_BEGIN
0 3 * * * cd $APP_DIR && ./scripts/backup.sh >> $LOG_DIR/backup.log 2>&1
0 4 * * * cd $APP_DIR && docker compose -f $COMPOSE_FILE run --rm web python backend/manage.py purge_chat_messages >> $LOG_DIR/chat-purge.log 2>&1
$MARKER_END
EOF
}

check_installed() {
	local current
	current="$(crontab -l 2>/dev/null || true)"
	echo "$current" | grep -Fq "$MARKER_BEGIN" \
		&& echo "$current" | grep -Fq "scripts/backup.sh" \
		&& echo "$current" | grep -Fq "purge_chat_messages"
}

MODE="${1:-install}"
case "$MODE" in
	--help | -h)
		usage
		exit 0
		;;
	--check)
		if check_installed; then
			echo "OK: managed backup cron is installed"
			exit 0
		fi
		echo "MISSING: managed backup cron not found in crontab" >&2
		exit 1
		;;
	install | "")
		;;
	*)
		usage
		exit 2
		;;
esac

if [ ! -f "$APP_DIR/scripts/backup.sh" ]; then
	echo "ERROR: backup.sh not found at $APP_DIR/scripts/backup.sh" >&2
	exit 1
fi
chmod +x "$APP_DIR/scripts/backup.sh" 2>/dev/null || true

mkdir -p "$LOG_DIR"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

{
	crontab -l 2>/dev/null || true
} | strip_managed_block | sed '/^[[:space:]]*$/d' >"$tmp"

{
	cat "$tmp"
	echo
	managed_block
	echo
} | crontab -

echo "==> Installed managed cron for APP_DIR=$APP_DIR"
echo "==> Logs: $LOG_DIR/backup.log , $LOG_DIR/chat-purge.log"
crontab -l | sed -n "/^$MARKER_BEGIN\$/,/^$MARKER_END\$/p"
