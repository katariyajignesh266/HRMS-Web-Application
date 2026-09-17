#!/bin/bash
set -euo pipefail

SITE_NAME="${FRAPPE_SITE_NAME:-hrms.localhost}"
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-123}"
FRAPPE_ADMIN_PASSWORD="${FRAPPE_ADMIN_PASSWORD:-admin}"
HRMS_SEED_BACKUP_DIR="${HRMS_SEED_BACKUP_DIR:-/workspace/docker/seed}"

bench_is_installed() {
    bench --site "$SITE_NAME" list-apps 2>/dev/null | awk '{print $1}' | grep -qx "$1"
}

resolve_seed_backup_dir() {
    if [ ! -d "$HRMS_SEED_BACKUP_DIR" ]; then
        return 1
    fi
    local candidates=("${HRMS_SEED_BACKUP_DIR:-}" "/workspace/backups/seed" "/workspace/docker/seed" "/workspace/.backups")
    for cand in "${candidates[@]}"; do
        [ -z "$cand" ] && continue
        [ ! -d "$cand" ] && continue

    if find "$HRMS_SEED_BACKUP_DIR" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) -print -quit | grep -q .; then
        printf '%s\n' "$HRMS_SEED_BACKUP_DIR"
        return 0
    fi
        if find "$cand" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) -print -quit | grep -q .; then
            printf '%s\n' "$cand"
            return 0
        fi

    find "$HRMS_SEED_BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null \
        | sort -nr \
        | awk 'NR == 1 {sub(/^[^ ]+ /, ""); print}'
        local latest_subdir
        latest_subdir="$(find "$cand" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null \
            | sort -nr \
            | awk 'NR == 1 {sub(/^[^ ]+ /, ""); print}')"
        if [ -n "$latest_subdir" ] && find "$latest_subdir" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) -print -quit | grep -q .; then
            printf '%s\n' "$latest_subdir"
            return 0
        fi
    done
    return 1
}

restore_seed_backup() {
    local backup_dir="$1"
    local sql_file public_file private_file

    sql_file="$(find "$backup_dir" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | sort | head -n 1)"
    if [ -z "$sql_file" ]; then
        return 1
    fi

    public_file="$(find "$backup_dir" -maxdepth 1 -type f -name '*-files.tgz' ! -name '*-private-files.tgz' | sort | head -n 1)"
    private_file="$(find "$backup_dir" -maxdepth 1 -type f -name '*-private-files.tgz' | sort | head -n 1)"

    echo "Creating site ${SITE_NAME} from seed backup at ${backup_dir}..."
    bench new-site "$SITE_NAME" \
      --mariadb-root-password "$MARIADB_ROOT_PASSWORD" \
      --admin-password "$FRAPPE_ADMIN_PASSWORD" \
      --no-mariadb-socket

    restore_args=(bench --site "$SITE_NAME" restore "$sql_file" --db-root-password "$MARIADB_ROOT_PASSWORD" --admin-password "$FRAPPE_ADMIN_PASSWORD" --non-interactive)
    if [ -n "$public_file" ]; then
        restore_args+=(--with-public-files "$public_file")
    fi
    if [ -n "$private_file" ]; then
        restore_args+=(--with-private-files "$private_file")
    fi

    "${restore_args[@]}"
}

if [ -d "/home/frappe/frappe-bench" ] \
    && [ ! -d "/home/frappe/frappe-bench/apps/frappe" ] \
    && [ -n "$(find /home/frappe/frappe-bench -mindepth 1 -maxdepth 1 ! -name sites -print -quit)" ]; then
    echo "Incomplete bench detected at /home/frappe/frappe-bench; refusing to overwrite it." >&2
    echo "Remove only the incomplete Frappe bench volume, then start again." >&2
    exit 1
fi

if [ ! -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Creating new bench..."
    cd /home/frappe
    rm -rf /tmp/frappe-bench-init
    bench init --skip-redis-config-generation /tmp/frappe-bench-init
    cp -a /tmp/frappe-bench-init/. /home/frappe/frappe-bench/
    find /home/frappe/frappe-bench/env -type f -print0 2>/dev/null \
        | xargs -0 -r sed -i 's#/tmp/frappe-bench-init#/home/frappe/frappe-bench#g'
    rm -rf /tmp/frappe-bench-init
fi

cd /home/frappe/frappe-bench
export PYTHONPATH="/home/frappe/frappe-bench/apps:${PYTHONPATH:-}"

if ! /home/frappe/frappe-bench/env/bin/python -c 'import firebase_admin' 2>/dev/null; then
    /home/frappe/frappe-bench/env/bin/pip install --quiet 'firebase-admin>=6.5,<7'
fi

# Keep copied editable package metadata valid after a first-run bootstrap.
find /home/frappe/frappe-bench/env -type f -print0 2>/dev/null \
    | xargs -0 -r sed -i 's#/tmp/frappe-bench-init#/home/frappe/frappe-bench#g'

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile and expose the web server to Docker
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile
sed -i 's/bench serve  --port 8000/bench serve --host 0.0.0.0 --port 8000/' ./Procfile

if [ ! -d "/home/frappe/frappe-bench/apps/erpnext" ]; then
    bench get-app erpnext
fi

if [ -L "/home/frappe/frappe-bench/apps/hrms" ] && [ "$(readlink /home/frappe/frappe-bench/apps/hrms)" = "/workspace/hrms" ]; then
    rm -f /home/frappe/frappe-bench/apps/hrms
fi

if [ ! -d "/home/frappe/frappe-bench/apps/hrms" ]; then
    ln -sfn /workspace /home/frappe/frappe-bench/apps/hrms
fi

ln -sfn ../../node_modules /home/frappe/frappe-bench/apps/frappe/frappe/public/node_modules

if ! /home/frappe/frappe-bench/env/bin/python -c 'import hrms' 2>/dev/null; then
    /home/frappe/frappe-bench/env/bin/pip install --no-deps -e /home/frappe/frappe-bench/apps/hrms
fi

if [ ! -d "/workspace/node_modules/html2canvas" ]; then
    (cd /workspace && yarn install --ignore-scripts)
fi

printf 'frappe\nerpnext\nhrms\n' > sites/apps.txt

if [ ! -d "/home/frappe/frappe-bench/sites/${SITE_NAME}" ]; then
    seed_backup_dir="$(resolve_seed_backup_dir || true)"
    if [ -n "$seed_backup_dir" ]; then
        restore_seed_backup "$seed_backup_dir"
    else
        echo "Creating site ${SITE_NAME}..."
        bench new-site "$SITE_NAME" \
          --mariadb-root-password "$MARIADB_ROOT_PASSWORD" \
          --admin-password "$FRAPPE_ADMIN_PASSWORD" \
          --no-mariadb-socket
    fi
elif [ ! -f "/home/frappe/frappe-bench/sites/${SITE_NAME}/site_config.json" ]; then
    echo "Site directory exists but site_config.json is missing; refusing to recreate ${SITE_NAME}." >&2
    exit 1
fi

if ! bench_is_installed hrms; then
    bench --site "$SITE_NAME" install-app hrms
fi

if [ ! -f "/workspace/hrms/www/hrms.html" ] || [ ! -d "/workspace/hrms/public/frontend" ]; then
    echo "Building HRMS frontend assets..."
    (cd /workspace/frontend && yarn install --ignore-scripts && yarn build)
fi

if [ "${RUN_MIGRATIONS:-0}" = "1" ] || [ ! -f "/home/frappe/frappe-bench/sites/${SITE_NAME}/.migrated" ]; then
    echo "Ensuring site migrations are up-to-date on ${SITE_NAME}..."
    bench --site "$SITE_NAME" migrate --skip-failing
    touch "/home/frappe/frappe-bench/sites/${SITE_NAME}/.migrated"
fi

SMTP_LOGIN="${SMTP_USERNAME:-${SMTP_EMAIL_ACCOUNT:-}}"
SMTP_SECRET="${SMTP_PASSWORD:-${SMTP_EMAIL_PASSWORD:-}}"
if [ -n "$SMTP_LOGIN" ] && [ -n "$SMTP_SECRET" ]; then
    bench --site "$SITE_NAME" execute hrms.api.smtp_config.configure_gmail_smtp_from_env >/dev/null
fi

bench --site "$SITE_NAME" set-config developer_mode 1
bench --site "$SITE_NAME" enable-scheduler
bench --site "$SITE_NAME" clear-cache
bench use "$SITE_NAME"

bench start
