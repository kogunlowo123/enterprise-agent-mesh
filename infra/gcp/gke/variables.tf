variable "cluster_name" { description = "GKE cluster name"; type = string }
variable "project_id" { description = "GCP project ID"; type = string }
variable "region" { description = "GCP region"; type = string; default = "us-central1" }
variable "kubernetes_version" { description = "Kubernetes version"; type = string; default = "1.29" }
variable "network_name" { description = "VPC network name"; type = string }
variable "subnet_name" { description = "Subnet name"; type = string }
variable "node_count" { description = "Initial node count"; type = number; default = 3 }
variable "node_max_count" { description = "Max node count"; type = number; default = 10 }
variable "machine_type" { description = "Machine type"; type = string; default = "n2-standard-4" }
variable "master_authorized_networks" {
  description = "Master authorized networks"
  type        = list(object({ cidr_block = string; display_name = string }))
  default     = []
}
