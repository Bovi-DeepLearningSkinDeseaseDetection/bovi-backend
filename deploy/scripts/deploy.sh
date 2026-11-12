#!/bin/sh
# Despliega (o actualiza) la API en la EC2.
#   sh /opt/bovi/app/deploy/scripts/deploy.sh            # rama main
#   REF=feature/x sh /opt/bovi/app/deploy/scripts/deploy.sh
# El contenedor aplica las migraciones al iniciar (RUN_MIGRATIONS=true).
set -eu

REF="${REF:-main}"
APP=/opt/bovi/app
COMPOSE="docker compose -f deploy/docker-compose.prod.yml --env-file /opt/bovi/compose.env"

cd "$APP"
git fetch --prune origin
git checkout "$REF"
git pull --ff-only origin "$REF"
echo "Versión: $(git log -1 --format='%h %s')"

sh deploy/scripts/render-env.sh

$COMPOSE build api
$COMPOSE up -d

# Espera a que el healthcheck del contenedor diga "healthy" (PostgreSQL alcanzable).
for _ in $(seq 1 30); do
    status=$(docker inspect --format '{{.State.Health.Status}}' "$($COMPOSE ps -q api)")
    if [ "$status" = "healthy" ]; then
        echo "API saludable"
        docker image prune -f >/dev/null
        exit 0
    fi
    sleep 2
done

echo "La API no quedó saludable. Últimos registros:" >&2
$COMPOSE logs --tail 50 api >&2
exit 1
