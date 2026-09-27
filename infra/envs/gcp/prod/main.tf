terraform {
  required_version = ">= 1.8.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "enterprise-agent-mesh-tfstate-gcp"
    prefix = "prod/terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "network" {
  source = "../../gcp/network"

  cluster_name = local.cluster_name
  project_id   = var.project_id
  region       = var.region
}

module "gke" {
  source = "../../gcp/gke"

  cluster_name   = local.cluster_name
  project_id     = var.project_id
  region         = var.region
  network_name   = module.network.network_name
  subnet_name    = module.network.subnet_name
  node_count     = 3
  node_max_count = 10
}

locals {
  cluster_name = "enterprise-agent-mesh-prod"
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  default     = "us-central1"
}
