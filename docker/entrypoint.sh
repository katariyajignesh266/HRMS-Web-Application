#!/usr/bin/env bash
set -euo pipefail

chown -R frappe:frappe /home/frappe/frappe-bench
chmod -R 777 /workspace/hrms/public /workspace/hrms/www 2>/dev/null || true
chown -R frappe:frappe /workspace/hrms/public /workspace/hrms/www 2>/dev/null || true
exec runuser -u frappe -- /workspace/docker/init.sh