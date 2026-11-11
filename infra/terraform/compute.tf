# EC2 t3.small con Docker Compose: Nginx (HTTPS) -> API (FastAPI).

data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

data "aws_caller_identity" "current" {}

locals {
  ssm_prefix = "/bovi/${var.environment}"
}

# --- Rol de la instancia: sin access keys en el servidor (RNF6) ---

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${local.name}-api"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "api" {
  # Las URLs prefirmadas actúan con los permisos de quien las firma: la API necesita
  # PutObject para que la app pueda subir y GetObject para que pueda descargar.
  statement {
    sid       = "EvaluationPhotos"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${aws_s3_bucket.images.arn}/evaluaciones/*"]
  }

  # Sin ListBucket, HeadObject de una foto que no existe responde 403 en lugar de 404.
  statement {
    sid       = "ListForHeadObject"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.images.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["evaluaciones/*"]
    }
  }

  statement {
    sid     = "ReadConfiguration"
    actions = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
    resources = [
      "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}",
      "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*",
    ]
  }

  statement {
    sid       = "DecryptSecureStrings"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "api" {
  name   = "${local.name}-api"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api.json
}

# Session Manager: entrar al servidor sin abrir el puerto 22.
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "api" {
  name = "${local.name}-api"
  role = aws_iam_role.api.name
}

# --- Instancia ---

resource "aws_instance" "api" {
  ami                    = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.api.id]
  iam_instance_profile   = aws_iam_instance_profile.api.name
  key_name               = var.ssh_key_name == "" ? null : var.ssh_key_name

  # IMDSv2 obligatorio: protege las credenciales del rol frente a SSRF.
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2 # los contenedores también leen las credenciales del rol
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    domain     = var.domain_name
    region     = var.region
    ssm_prefix = local.ssm_prefix
  })

  # Cambiar user_data no debe reemplazar el servidor en marcha.
  lifecycle {
    ignore_changes = [ami, user_data]
  }

  tags = { Name = "${local.name}-api" }
}

resource "aws_eip" "api" {
  instance = aws_instance.api.id
  domain   = "vpc"
  tags     = { Name = "${local.name}-api" }
}
