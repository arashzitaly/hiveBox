output "cluster_name" {
  description = "Name of the AKS cluster."
  value       = azurerm_kubernetes_cluster.hivebox.name
}

output "cluster_id" {
  description = "AKS cluster resource ID."
  value       = azurerm_kubernetes_cluster.hivebox.id
}

output "cluster_endpoint" {
  description = "Kubernetes API server endpoint (host)."
  value       = azurerm_kubernetes_cluster.hivebox.kube_config[0].host
  sensitive   = true
}

output "cluster_version" {
  description = "Kubernetes version AKS provisioned."
  value       = azurerm_kubernetes_cluster.hivebox.kubernetes_version
}

# In DOKS this was kube_config[0].raw_config. In AKS it's kube_config_raw.
output "kubeconfig" {
  description = "Raw kubeconfig for the cluster. Sensitive — do not print or commit. Prefer `az aks get-credentials` for daily use."
  value       = azurerm_kubernetes_cluster.hivebox.kube_config_raw
  sensitive   = true
}
