# Configuración de la API en SSM Parameter Store (nivel estándar: sin costo).
# deploy/scripts/render-env.sh los lee con el rol de la EC2 y escribe /opt/bovi/api.env.
# Ningún secreto queda en el código ni en el repositorio.

resource "random_password" "jwt" {
  length  = 64
  special = false
}

locals {
  plain_parameters = {
    APP_ENV               = "production"
    DOCS_ENABLED          = "false"
    LOG_LEVEL             = "INFO"
    S3_BUCKET             = aws_s3_bucket.images.bucket
    S3_REGION             = var.region
    BCRYPT_ROUNDS         = "12"
    CONSENT_VERSION       = "2026.1"
    WEB_CONCURRENCY       = "2"
    DATABASE_POOL_SIZE    = "5"
    DATABASE_MAX_OVERFLOW = "5"
  }
  secret_parameters = {
    DATABASE_URL = "postgresql+psycopg://${aws_db_instance.main.username}:${random_password.db.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}?sslmode=require"
    JWT_SECRET   = random_password.jwt.result
  }
}

resource "aws_ssm_parameter" "plain" {
  for_each = local.plain_parameters
  name     = "${local.ssm_prefix}/${each.key}"
  type     = "String"
  value    = each.value
}

resource "aws_ssm_parameter" "secret" {
  for_each = nonsensitive(toset(keys(local.secret_parameters)))
  name     = "${local.ssm_prefix}/${each.key}"
  type     = "SecureString"
  value    = local.secret_parameters[each.key]
}
