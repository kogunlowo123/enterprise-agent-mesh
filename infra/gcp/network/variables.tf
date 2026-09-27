variable "cluster_name" { description = "GKE cluster name"; type = string }
variable "project_id" { description = "GCP project ID"; type = string }
variable "region" { description = "GCP region"; type = string; default = "us-central1" }
variable "subnet_cidr" { description = "Subnet CIDR"; type = string; default = "10.2.0.0/24" }
variable "pod_cidr" { description = "Pod CIDR"; type = string; default = "10.2.4.0/22" }
variable "service_cidr" { description = "Service CIDR"; type = string; default = "10.2.8.0/22" }
