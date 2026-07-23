variable "subscription_id" {
  description = "Azure Subscription ID (not a secret credential — safe to keep here). The azurerm provider can also auto-detect it from your `az login` session. Override via TF_VAR_subscription_id if you switch accounts."
  type        = string
  default     = "16233628-d9b6-4a08-bdea-71a95e716ead"
}

variable "location" {
  description = "Azure region for the resource group and AKS cluster. NOTE for this trial subscription: westeurope refuses new customers, and northeurope only permits confidential-compute VM sizes (no cheap Standard_B2s). swedencentral is a European region that allows Standard_B2s, so we use it. (State backend stays in northeurope — backend region is independent.)"
  type        = string
  default     = "swedencentral"
}

variable "cluster_name" {
  description = "Name of the AKS cluster (also used to derive the resource-group name)."
  type        = string
  default     = "hivebox-dev"
}

variable "node_size" {
  description = "Azure VM size for the worker nodes. Standard_B2s_v2 = burstable v2 (2 vCPU / 8 GiB), cheap, fine for learning. NOTE: swedencentral only offers the v2 B-series — the older Standard_B2s (v1) does NOT exist there. Pick from the region's offered sizes if you change region. (DO used a droplet slug like s-1vcpu-2gb.)"
  type        = string
  default     = "Standard_B2s_v2"
}

variable "node_count" {
  description = "Number of worker nodes in the default pool."
  type        = number
  default     = 2
}
