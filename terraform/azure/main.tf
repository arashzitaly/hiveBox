provider "azurerm" {
  # The `features {}` block is REQUIRED by the azurerm provider even when empty.
  # (DigitalOcean's provider had no equivalent — this is Azure-specific.)
  features {}

  # Authentication is picked up automatically from, in order:
  #   1. `az login`  (Azure CLI — easiest for learning), or
  #   2. ARM_CLIENT_ID / ARM_CLIENT_SECRET / ARM_TENANT_ID / ARM_SUBSCRIPTION_ID
  #      (Service Principal — how CI/CD authenticates).
  # This replaces DO's single `var.do_token`.
  subscription_id = var.subscription_id
}

# Resource Group — Azure's mandatory logical container for related resources.
# DigitalOcean had NO equivalent; a DO VPC was the closest grouping. In Azure,
# almost everything must live inside a resource group.
resource "azurerm_resource_group" "hivebox" {
  name     = "${var.cluster_name}-rg"
  location = var.location
}

# Managed Kubernetes cluster (AKS) — the equivalent of digitalocean_kubernetes_cluster (DOKS).
resource "azurerm_kubernetes_cluster" "hivebox" {
  name                = var.cluster_name
  location            = azurerm_resource_group.hivebox.location
  resource_group_name = azurerm_resource_group.hivebox.name
  dns_prefix          = var.cluster_name

  # Leaving kubernetes_version unset lets AKS pick a supported default,
  # mirroring how the DO config asked DO for `latest_version`.

  # In DOKS this was `node_pool`. In AKS the primary pool is `default_node_pool`.
  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.node_size # Azure VM size (e.g. Standard_B2s), not a DO slug.
  }

  # AKS needs a cluster identity to manage Azure resources (load balancers, disks).
  # SystemAssigned = Azure creates and manages a Managed Identity for you — the
  # simplest option and a core Azure concept with no DigitalOcean parallel.
  identity {
    type = "SystemAssigned"
  }
}
