output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "vnet_id" {
  description = "Virtual network ID"
  value       = azurerm_virtual_network.main.id
}

output "node_subnet_id" {
  description = "Node subnet ID"
  value       = azurerm_subnet.node.id
}

output "pod_subnet_id" {
  description = "Pod subnet ID"
  value       = azurerm_subnet.pod.id
}
