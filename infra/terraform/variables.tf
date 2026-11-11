variable "region" {
  description = "Región de AWS. sa-east-1 (São Paulo) es la más cercana a Lima."
  type        = string
  default     = "sa-east-1"
}

variable "environment" {
  description = "Nombre del entorno; se usa en nombres y en la ruta de los parámetros SSM."
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Dominio de la API (por ejemplo api.bovi.pe). Su registro A debe apuntar a la IP elástica."
  type        = string
}

variable "alert_email" {
  description = "Correo que recibe las alarmas y los avisos de presupuesto (hay que confirmar la suscripción)."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Presupuesto mensual; avisa al 80 % del gasto real y al 100 % del pronóstico."
  type        = number
  default     = 50
}

variable "instance_type" {
  description = "Tipo de la EC2 (arquitectura física: t3.small, 2 vCPU y 2 GB)."
  type        = string
  default     = "t3.small"
}

variable "db_instance_class" {
  description = "Clase de RDS PostgreSQL."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  description = "Almacenamiento inicial de RDS; crece solo hasta db_max_allocated_storage_gb."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage_gb" {
  type    = number
  default = 50
}

variable "db_backup_retention_days" {
  description = "Días de backups automáticos y restauración a un punto en el tiempo (RNF15: RPO <= 24 h)."
  type        = number
  default     = 7
}

variable "ssh_allowed_cidr" {
  description = "CIDR con acceso SSH (por ejemplo 200.1.2.3/32). Vacío: sin puerto 22; se entra con SSM Session Manager."
  type        = string
  default     = ""
}

variable "ssh_key_name" {
  description = "Par de llaves EC2 para SSH. Vacío si solo se usa Session Manager."
  type        = string
  default     = ""
}

variable "enable_health_check" {
  description = "Health check de Route 53 sobre https://<dominio>/health con alarma (~0.75 USD/mes)."
  type        = bool
  default     = true
}
