#!/bin/sh
# Aplica las migraciones pendientes y levanta la API.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    alembic upgrade head
fi

# --proxy-headers: Nginx termina TLS y reenvía X-Forwarded-For / X-Forwarded-Proto.
exec uvicorn --factory bovi.main:app_factory \
    --host 0.0.0.0 --port 8000 \
    --workers "${WEB_CONCURRENCY:-2}" \
    --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
