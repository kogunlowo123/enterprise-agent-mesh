terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "enterprise-agent-mesh-tfstate-aws"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "prod"
      Project     = "enterprise-agent-mesh"
      ManagedBy   = "terraform"
    }
  }
}

module "network" {
  source = "../../aws/network"

  cluster_name       = local.cluster_name
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  tags               = local.common_tags
}

module "eks" {
  source = "../../aws/eks"

  cluster_name       = local.cluster_name
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  node_desired_count = 3
  node_min_count     = 1
  node_max_count     = 10
  tags               = local.common_tags
}

locals {
  cluster_name = "enterprise-agent-mesh-prod"
  common_tags = {
    Environment = "prod"
    Project     = "enterprise-agent-mesh"
  }
}

variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}
