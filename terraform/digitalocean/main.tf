provider "digitalocean" {
  token = var.do_token
}

# Ask DO for the latest supported Kubernetes version instead of hardcoding one.
data "digitalocean_kubernetes_versions" "current" {}

# Private network for the cluster.
resource "digitalocean_vpc" "hivebox" {
  name     = "${var.cluster_name}-vpc"
  region   = var.region
  ip_range = "10.10.10.0/24"
}

# Managed Kubernetes cluster (DOKS).
resource "digitalocean_kubernetes_cluster" "hivebox" {
  name     = var.cluster_name
  region   = var.region
  version  = data.digitalocean_kubernetes_versions.current.latest_version
  vpc_uuid = digitalocean_vpc.hivebox.id

  node_pool {
    name       = "default"
    size       = var.node_size
    node_count = var.node_count
  }
}