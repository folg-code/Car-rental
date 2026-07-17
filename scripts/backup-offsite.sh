#!/usr/bin/env bash
# Sync lokalnych backupow poza VPS (rclone → S3 / Backblaze / rsync remote).
# Demo: jesli BACKUP_OFFSITE_REMOTE nie jest ustawione, skrypt konczy sie 0 (swiadoma rezygnacja).
#
# Przyklady:
#   BACKUP_OFFSITE_REMOTE=remote:car-rental-backups ./scripts/backup-offsite.sh
#   # w .env.production:
#   # BACKUP_OFFSITE_REMOTE=b2:car-rental-backups

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
LOG_DIR="${BACKUP_LOG_DIR:-$APP_DIR/logs}"

cd "$APP_DIR"
mkdir -p "$LOG_DIR"

if [ -z "${BACKUP_OFFSITE_REMOTE:-}" ] && [ -f .env.production ]; then
	# shellcheck disable=SC1091
	set -a
	# shellcheck disable=SC1091
	source .env.production
	set +a
fi

REMOTE="${BACKUP_OFFSITE_REMOTE:-}"
if [ -z "$REMOTE" ]; then
	echo "SKIP: BACKUP_OFFSITE_REMOTE not set — offsite sync disabled (OK for demo)."
	exit 0
fi

if ! command -v rclone >/dev/null 2>&1; then
	echo "ERROR: rclone not found (install rclone or unset BACKUP_OFFSITE_REMOTE)" >&2
	exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
	echo "ERROR: backup directory missing: $BACKUP_DIR" >&2
	exit 1
fi

echo "==> Offsite sync $BACKUP_DIR → $REMOTE"
rclone sync "$BACKUP_DIR" "$REMOTE" --create-empty-src-dirs
echo "==> Offsite sync finished"
