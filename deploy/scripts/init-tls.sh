#!/bin/sh
# Obtiene el primer certificado de Let's Encrypt, antes de levantar Nginx.
# Ejecutar una sola vez en la EC2, con el puerto 80 libre y el DNS del dominio apuntando a la IP elástica.
#   DOMAIN=api.ejemplo.pe EMAIL=correo@ejemplo.pe sh deploy/scripts/init-tls.sh
set -eu

: "${DOMAIN:?Defina DOMAIN}"
: "${EMAIL:?Defina EMAIL (avisos de vencimiento de Let's Encrypt)}"

mkdir -p /opt/bovi/letsencrypt /opt/bovi/certbot-www

# Al ejecutar este comando se aceptan los términos de servicio de Let's Encrypt (--agree-tos).
docker run --rm -p 80:80 \
    -v /opt/bovi/letsencrypt:/etc/letsencrypt \
    certbot/certbot:latest certonly --standalone \
    --non-interactive --agree-tos --email "$EMAIL" \
    -d "$DOMAIN"

echo "Certificado listo en /opt/bovi/letsencrypt/live/$DOMAIN"
