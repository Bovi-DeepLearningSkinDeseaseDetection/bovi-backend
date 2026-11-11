#!/bin/sh
# Crea los buckets de RustFS si no existen. Reintenta mientras RustFS arranca.
set -u

ENDPOINT="http://s3:9000"
BUCKETS="bovi-evaluaciones bovi-evaluaciones-test"

for bucket in $BUCKETS; do
    attempt=0
    until aws --endpoint-url "$ENDPOINT" s3api head-bucket --bucket "$bucket" 2>/dev/null \
        || aws --endpoint-url "$ENDPOINT" s3api create-bucket --bucket "$bucket" >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 30 ]; then
            echo "No se pudo crear el bucket $bucket" >&2
            exit 1
        fi
        sleep 1
    done
    echo "Bucket listo: $bucket"
done
