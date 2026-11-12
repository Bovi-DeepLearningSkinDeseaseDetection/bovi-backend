#!/bin/sh
# Escribe /opt/bovi/api.env con la configuración de la API guardada en SSM Parameter Store.
# Corre en la EC2: usa el rol de la instancia, sin access keys.
set -eu

# shellcheck source=/dev/null
. /opt/bovi/deploy.env # AWS_REGION y SSM_PREFIX (los deja el user_data de Terraform)

target=/opt/bovi/api.env
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

aws ssm get-parameters-by-path \
    --region "$AWS_REGION" \
    --path "$SSM_PREFIX" \
    --with-decryption \
    --query 'Parameters[*].[Name,Value]' \
    --output text |
while IFS="$(printf '\t')" read -r name value; do
    printf '%s=%s\n' "${name##*/}" "$value"
done >"$tmp"

for required in DATABASE_URL JWT_SECRET S3_BUCKET; do
    if ! grep -q "^${required}=" "$tmp"; then
        echo "Falta ${SSM_PREFIX}/${required} en Parameter Store" >&2
        exit 1
    fi
done

install -m 600 "$tmp" "$target"
echo "Configuración escrita en $target ($(wc -l <"$target") variables)"
