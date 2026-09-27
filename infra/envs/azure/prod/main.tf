terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "enterprise-agent-mesh-tfstate"
    storage_account_name = "agentmeshtfstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

module "network" {
  source = "../../azure/network"

  cluster_name = local.cluster_name
  location     = var.location
  tags         = local.common_tags
}

module "aks" {
  source = "../../azure/aks"

  cluster_name        = local.cluster_name
  location            = var.location
  resource_group_name = module.network.resource_group_name
  node_subnet_id      = module.network.node_subnet_id
  pod_subnet_id       = module.network.pod_subnet_id
  tags                = local.common_tags
}

locals {
  cluster_name = "enterprise-agent-mesh-prod"
  common_tags = {
    Environment = "prod"
    Project     = "enterprise-agent-mesh"
  }
}

variable "location" {
  description = "Azure region"
  default     = "eastus"
}
