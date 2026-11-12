#!/bin/sh
# Prueba de restauración del backup de RDS (RNF15: RPO <= 24 h, RTO <= 4 h).
# Corre desde la PC del administrador con credenciales de AWS. Crea una instancia temporal
# restaurada al último punto disponible, mide cuánto tarda y la borra al final.
# Costo: unos centavos por la hora que vive la instancia temporal.
#   DB_ID=bovi-prod-postgres sh deploy/scripts/test-restore.sh
set -eu

: "${DB_ID:?Defina DB_ID (output rds_identifier de Terraform)}"
REGION="${AWS_REGION:-sa-east-1}"
TEMP_ID="${DB_ID}-restore-test-$(date +%Y%m%d%H%M)"
aws() { command aws --region "$REGION" "$@"; }

latest=$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].LatestRestorableTime' --output text)
subnet_group=$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].DBSubnetGroup.DBSubnetGroupName' --output text)
security_group=$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
    --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text)

echo "Último punto restaurable: $latest (RPO: tiempo desde ese punto hasta ahora)"
started=$(date +%s)

aws rds restore-db-instance-to-point-in-time \
    --source-db-instance-identifier "$DB_ID" \
    --target-db-instance-identifier "$TEMP_ID" \
    --use-latest-restorable-time \
    --db-subnet-group-name "$subnet_group" \
    --vpc-security-group-ids "$security_group" \
    --no-publicly-accessible \
    --no-multi-az \
    --tags Key=Project,Value=bovi Key=Purpose,Value=restore-test >/dev/null

echo "Restaurando en $TEMP_ID..."
aws rds wait db-instance-available --db-instance-identifier "$TEMP_ID"
elapsed=$(( $(date +%s) - started ))
endpoint=$(aws rds describe-db-instances --db-instance-identifier "$TEMP_ID" \
    --query 'DBInstances[0].Endpoint.Address' --output text)

echo "Restaurada en $((elapsed / 60)) min (RTO objetivo: <= 240 min). Endpoint: $endpoint"
echo
echo "Verifique los datos desde la EC2 (Session Manager) y compare con producción:"
echo "  docker run --rm postgres:16-alpine psql \"postgresql://bovi_admin:<clave>@$endpoint:5432/bovi?sslmode=require\" \\"
echo "    -c 'select (select count(*) from usuario) usuarios, (select count(*) from animal) animales, (select count(*) from evaluacion) evaluaciones'"
echo
printf "Cuando termine, presione Enter para borrar la instancia temporal... "
read -r _

aws rds delete-db-instance --db-instance-identifier "$TEMP_ID" \
    --skip-final-snapshot --delete-automated-backups >/dev/null
echo "Instancia temporal $TEMP_ID en borrado. Registre el RPO y el RTO medidos en docs/despliegue.md."
