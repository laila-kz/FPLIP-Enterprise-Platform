#!/bin/sh
set -e

echo "==> Starting Apache Superset for FPLIP..."

ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_FIRSTNAME="${ADMIN_FIRSTNAME:-Admin}"
ADMIN_LASTNAME="${ADMIN_LASTNAME:-User}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@fplip.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"

echo "==> Running Superset database migrations..."
superset db upgrade

echo "==> Creating default admin user (if not exists)..."
superset fab create-admin \
    --username "$ADMIN_USERNAME" \
    --firstname "$ADMIN_FIRSTNAME" \
    --lastname "$ADMIN_LASTNAME" \
    --email "$ADMIN_EMAIL" \
    --password "$ADMIN_PASSWORD" || true

echo "==> Initializing roles and permissions..."
superset init

echo "==> Starting Superset web server on port 8088..."
exec gunicorn \
    --bind "0.0.0.0:8088" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"
