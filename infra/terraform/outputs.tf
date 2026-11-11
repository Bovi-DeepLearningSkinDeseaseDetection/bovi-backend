output "api_public_ip" {
  description = "IP elástica de la API: el registro A de domain_name debe apuntar aquí."
  value       = aws_eip.api.public_ip
}

output "api_instance_id" {
  description = "Para entrar sin SSH: aws ssm start-session --target <id>"
  value       = aws_instance.api.id
}

output "rds_endpoint" {
  value = aws_db_instance.main.address
}

output "rds_identifier" {
  description = "Para los backups y la prueba de restauración (docs/despliegue.md)."
  value       = aws_db_instance.main.identifier
}

output "images_bucket" {
  value = aws_s3_bucket.images.bucket
}

output "ssm_prefix" {
  description = "Ruta de la configuración de la API en Parameter Store."
  value       = local.ssm_prefix
}
