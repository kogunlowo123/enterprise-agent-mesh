variable "cluster_name" { description = "AKS cluster name"; type = string }
variable "location" { description = "Azure region"; type = string; default = "eastus" }
variable "resource_group_name" { description = "Resource group name"; type = string }
variable "kubernetes_version" { description = "Kubernetes version"; type = string; default = "1.29" }
variable "node_subnet_id" { description = "Node subnet ID"; type = string }
variable "pod_subnet_id" { description = "Pod subnet ID"; type = string }
variable "system_node_count" { description = "System node count"; type = number; default = 3 }
variable "system_node_vm_size" { description = "System node VM size"; type = string; default = "Standard_D4s_v3" }
variable "system_node_max_count" { description = "System node max count"; type = number; default = 5 }
variable "agent_node_count" { description = "Agent node count"; type = number; default = 3 }
variable "agent_node_vm_size" { description = "Agent node VM size"; type = string; default = "Standard_D4s_v3" }
variable "agent_node_max_count" { description = "Agent node max count"; type = number; default = 10 }
variable "tags" { description = "Tags"; type = map(string); default = {} }
