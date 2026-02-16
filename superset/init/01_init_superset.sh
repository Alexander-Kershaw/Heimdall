set -euo pipefail

echo "[superset-init] Upgrading DB..."
superset db upgrade

echo "[superset-init] Creating admin user..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME}" \
  --firstname "Heimdall" \
  --lastname "Admin" \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" || true

echo "[superset-init] Initializing roles and permissions..."
superset init

echo "[superset-init] Done."
