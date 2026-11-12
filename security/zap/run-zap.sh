#!/bin/sh
# Escaneo OWASP ZAP de la API a partir de su OpenAPI (RNF5: sin hallazgos altos).
# Corre contra el entorno local de docker-compose con un usuario de prueba autenticado:
#   docker compose up -d --build db s3 s3-init api
#   sh security/zap/run-zap.sh
# Deja el reporte en security/zap/reporte.html y security/zap/reporte.md.
set -eu

API_INTERNAL="${API_INTERNAL:-http://api:8000}"
API_HOST="${API_HOST:-http://localhost:8000}"
NETWORK="${NETWORK:-bovi-backend_default}"
HERE=$(cd "$(dirname "$0")" && pwd)

email="zap-$(date +%s)@bovi.test"
token=$(curl -sf -X POST "$API_HOST/api/v1/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"Escaneo ZAP\",\"email\":\"$email\",\"password\":\"establo2026\",\"consent_accepted\":true}" |
    sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
[ -n "$token" ] || { echo "No se pudo crear el usuario de prueba" >&2; exit 1; }

# ZAP envía el token en cada solicitud para escanear también las rutas protegidas.
docker run --rm --network "$NETWORK" \
    -v "$HERE:/zap/wrk:rw" \
    -e ZAP_AUTH_HEADER=Authorization \
    -e ZAP_AUTH_HEADER_VALUE="Bearer $token" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-api-scan.py -t "$API_INTERNAL/openapi.json" -f openapi \
    -c rules.conf -r reporte.html -w reporte.md -I
