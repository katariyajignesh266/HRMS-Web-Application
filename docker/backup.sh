#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SITE_NAME="${FRAPPE_SITE_NAME:-hrms.localhost}"
BACKUP_DIR="${BACKUP_DIR:-$REPO_ROOT/.backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_DIR="$BACKUP_DIR/$SITE_NAME-$TIMESTAMP"

mkdir -p "$ARCHIVE_DIR"
cd "$SCRIPT_DIR"
COMPOSE_ARGS=()
if [ -f "$REPO_ROOT/.env" ]; then
    COMPOSE_ARGS+=(--env-file ../.env)
fi

docker compose "${COMPOSE_ARGS[@]}" exec -T frappe bash -lc \
  "cd /home/frappe/frappe-bench && runuser -u frappe -- env PYTHONPATH=/home/frappe/.bench:/home/frappe/.local/lib/python3.14/site-packages:/home/frappe/frappe-bench/apps /home/frappe/.local/bin/bench --site '$SITE_NAME' backup --with-files --compress"

docker compose "${COMPOSE_ARGS[@]}" cp \
  "frappe:/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups/." \
  "$ARCHIVE_DIR/"

echo "Backup created at $ARCHIVE_DIR"

if [ "${SEED:-0}" = "1" ]; then
  SEED_DIR="$REPO_ROOT/docker/seed/$SITE_NAME-$TIMESTAMP"
  mkdir -p "$SEED_DIR"
  cp -a "$ARCHIVE_DIR"/. "$SEED_DIR"/
  echo "Seed backup copied to $SEED_DIR"
  echo "Review this folder before committing. Do not commit real employee data or secrets."
fi
