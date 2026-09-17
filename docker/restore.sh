#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup-directory>" >&2
    exit 2
fi

BACKUP_DIR="$1"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory does not exist: $BACKUP_DIR" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_NAME="${FRAPPE_SITE_NAME:-hrms.localhost}"
cd "$SCRIPT_DIR"
COMPOSE_ARGS=()
if [ -f "../.env" ]; then
  COMPOSE_ARGS+=(--env-file ../.env)
fi

echo "Restore is intentionally explicit and must be run against a disposable validation site."
echo "The existing site will not be overwritten automatically."
docker compose "${COMPOSE_ARGS[@]}" exec -T frappe bash -lc \
  "test -d '/home/frappe/frappe-bench/sites/$SITE_NAME' && echo 'Existing site detected; restore aborted.' >&2 && exit 1 || exit 0"

echo "Backup contents found at $BACKUP_DIR"
echo "Create a disposable site, copy the backup files into its private/backups directory, and run bench restore explicitly."