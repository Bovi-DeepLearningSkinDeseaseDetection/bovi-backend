# BD 2: PostgreSQL 16 en Amazon RDS, en subredes privadas, cifrado y con backups diarios (RNF6, RNF15).

resource "random_password" "db" {
  length  = 32
  special = false # va dentro de DATABASE_URL: sin caracteres que haya que escapar
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_parameter_group" "postgres16" {
  name   = "${local.name}-postgres16"
  family = "postgres16"

  # Solo conexiones cifradas (SQL sobre TLS).
  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot" # como lo registra RDS; la instancia nace ya con este valor
  }

  # Registra las consultas de más de 500 ms (RNF16: p95 <= 500 ms).
  parameter {
    name  = "log_min_duration_statement"
    value = "500"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name}-postgres"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  db_name  = "bovi"
  username = "bovi_admin"
  password = random_password.db.result
  port     = 5432

  allocated_storage     = var.db_allocated_storage_gb
  max_allocated_storage = var.db_max_allocated_storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name
  publicly_accessible    = false
  multi_az               = false # piloto: una zona; RTO <= 4 h con restauración del backup

  # 03:00-03:30 en Lima: backup diario y restauración a cualquier punto de los últimos días.
  backup_retention_period = var.db_backup_retention_days
  backup_window           = "08:00-08:30"
  maintenance_window      = "sun:08:45-sun:09:45"
  copy_tags_to_snapshot   = true

  auto_minor_version_upgrade = true
  deletion_protection        = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${local.name}-postgres-final"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = { Name = "${local.name}-postgres" }
}
