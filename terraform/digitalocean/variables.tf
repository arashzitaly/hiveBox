variable "do_token" {
  description = "DigitalOcean API token. Supplied via TF_VAR_do_token env var, never hardcoded."
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region for the VPC and DOKS cluster."
  type        = string
  default     = "fra1"
}

variable "cluster_name" {
  description = "Name of the DOKS cluster."
  type        = string
  default     = "hivebox-dev"
}

variable "node_size" {
  description = "Droplet size slug for the worker nodes."
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "node_count" {
  description = "Number of worker nodes in the default pool."
  type        = number
  default     = 2
}