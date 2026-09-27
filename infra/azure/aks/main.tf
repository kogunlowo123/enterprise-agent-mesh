terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.cluster_name}-logs"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  private_cluster_enabled = true

  default_node_pool {
    name                         = "system"
    node_count                   = var.system_node_count
    vm_size                      = var.system_node_vm_size
    vnet_subnet_id               = var.node_subnet_id
    pod_subnet_id                = var.pod_subnet_id
    os_disk_size_gb              = 50
    type                         = "VirtualMachineScaleSets"
    enable_auto_scaling          = true
    min_count                    = 1
    max_count                    = var.system_node_max_count
    only_critical_addons_enabled = true
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
    outbound_type     = "userAssignedNATGateway"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }

  workload_identity_enabled = true
  oidc_issuer_enabled       = true

  tags = var.tags
}

resource "azurerm_kubernetes_cluster_node_pool" "agents" {
  name                  = "agentpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.agent_node_vm_size
  node_count            = var.agent_node_count
  vnet_subnet_id        = var.node_subnet_id
  pod_subnet_id         = var.pod_subnet_id
  os_disk_size_gb       = 100
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = var.agent_node_max_count

  node_labels = {
    role = "agent-mesh"
  }

  tags = var.tags
}
