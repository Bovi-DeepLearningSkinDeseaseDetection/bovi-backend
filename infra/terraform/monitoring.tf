# Alarmas por correo (RNF15) y presupuesto mensual para que AWS no sorprenda con la factura.

resource "aws_sns_topic" "alerts" {
  name = "${local.name}-alertas"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email # AWS envía un correo de confirmación
}

# La EC2 deja de responder: alarma y recuperación automática en otro host físico.
resource "aws_cloudwatch_metric_alarm" "ec2_status" {
  alarm_name          = "${local.name}-ec2-status"
  alarm_description   = "La EC2 de la API falla los chequeos de estado; se intenta recuperar."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed_System"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  dimensions          = { InstanceId = aws_instance.api.id }
  alarm_actions       = [aws_sns_topic.alerts.arn, "arn:aws:automate:${var.region}:ec2:recover"]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "${local.name}-ec2-cpu"
  alarm_description   = "CPU de la API sobre 80 % por 15 minutos."
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { InstanceId = aws_instance.api.id }
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "db_storage" {
  alarm_name          = "${local.name}-rds-almacenamiento"
  alarm_description   = "RDS con menos de 2 GB libres."
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 2 * 1024 * 1024 * 1024
  comparison_operator = "LessThanThreshold"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.main.identifier }
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  alarm_name          = "${local.name}-rds-cpu"
  alarm_description   = "CPU de RDS sobre 80 % por 15 minutos."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.main.identifier }
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# --- Disponibilidad vista desde fuera (RNF15: >= 99 %) ---

resource "aws_route53_health_check" "api" {
  count             = var.enable_health_check ? 1 : 0
  fqdn              = var.domain_name
  type              = "HTTPS"
  port              = 443
  resource_path     = "/health"
  request_interval  = 30
  failure_threshold = 3
  regions           = ["sa-east-1", "us-east-1", "us-west-2"]

  tags = { Name = "${local.name}-health" }
}

resource "aws_sns_topic" "alerts_us_east_1" {
  count    = var.enable_health_check ? 1 : 0
  provider = aws.us_east_1
  name     = "${local.name}-alertas"
}

resource "aws_sns_topic_subscription" "email_us_east_1" {
  count     = var.enable_health_check ? 1 : 0
  provider  = aws.us_east_1
  topic_arn = aws_sns_topic.alerts_us_east_1[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "api_down" {
  count               = var.enable_health_check ? 1 : 0
  provider            = aws.us_east_1
  alarm_name          = "${local.name}-api-caida"
  alarm_description   = "https://${var.domain_name}/health no responde 200."
  namespace           = "AWS/Route53"
  metric_name         = "HealthCheckStatus"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  dimensions          = { HealthCheckId = aws_route53_health_check.api[0].id }
  alarm_actions       = [aws_sns_topic.alerts_us_east_1[0].arn]
  ok_actions          = [aws_sns_topic.alerts_us_east_1[0].arn]
}

# --- Presupuesto ---

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-mensual"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
