output "cluster_name" {
  description = "Name of the DOKS cluster."
  value       = digitalocean_kubernetes_cluster.hivebox.name
}

output "cluster_id" {
  description = "DOKS cluster ID."
  value       = digitalocean_kubernetes_cluster.hivebox.id
}

output "cluster_endpoint" {
  description = "Kubernetes API server endpoint."
  value       = digitalocean_kubernetes_cluster.hivebox.endpoint
}

output "cluster_version" {
  description = "Kubernetes version DOKS provisioned."
  value       = digitalocean_kubernetes_cluster.hivebox.version
}

output "kubeconfig" {
  description = "Raw kubeconfig for the cluster. Sensitive — do not print or commit."
  value       = digitalocean_kubernetes_cluster.hivebox.kube_config[0].raw_config
  sensitive   = true
}