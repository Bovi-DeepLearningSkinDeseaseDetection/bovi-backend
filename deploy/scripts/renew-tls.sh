#!/bin/sh
# Recarga Nginx para que tome el certificado que renovó el contenedor certbot.
# Lo ejecuta cron una vez al día (ver docs/despliegue.md):
#   0 4 * * * sh /opt/bovi/app/deploy/scripts/renew-tls.sh >> /var/log/bovi-tls.log 2>&1
set -eu

cd /opt/bovi/app
docker compose -f deploy/docker-compose.prod.yml --env-file /opt/bovi/compose.env \
    exec -T nginx nginx -s reload
echo "$(date -Is) nginx recargado"
