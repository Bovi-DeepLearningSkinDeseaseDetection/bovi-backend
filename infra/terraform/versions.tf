terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # El estado guarda la contraseña de RDS y el secreto JWT: queda en local y fuera de git
  # (.gitignore). Si trabajan dos personas, muévanlo a un bucket S3 cifrado con bloqueo.
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "bovi"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Las métricas de los health checks de Route 53 solo existen en us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "bovi"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
