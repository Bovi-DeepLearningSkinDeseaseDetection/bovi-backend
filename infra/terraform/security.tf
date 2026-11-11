resource "aws_security_group" "api" {
  name        = "${local.name}-api"
  description = "EC2 de la API: HTTPS publico; SSH solo si se define ssh_allowed_cidr"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name}-api" }
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.api.id
  description       = "HTTPS de la app movil"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.api.id
  description       = "HTTP: desafio de Lets Encrypt y redireccion a HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  count             = var.ssh_allowed_cidr == "" ? 0 : 1
  security_group_id = aws_security_group.api.id
  description       = "SSH del administrador"
  cidr_ipv4         = var.ssh_allowed_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "api_all" {
  security_group_id = aws_security_group.api.id
  description       = "Salida: paquetes, imagenes Docker, S3, SSM y RDS"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# RDS: solo acepta conexiones desde la EC2 (arquitectura física, puerto 5432).
resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "PostgreSQL: solo desde la EC2 de la API"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name}-db" }
}

resource "aws_vpc_security_group_ingress_rule" "db_from_api" {
  security_group_id            = aws_security_group.db.id
  description                  = "PostgreSQL desde la API"
  referenced_security_group_id = aws_security_group.api.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
