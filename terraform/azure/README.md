# HiveBox IaC — Azure (AKS)

Azure port of the DigitalOcean config in `../digitalocean/`. Same workload
(HiveBox on managed Kubernetes), different cloud. Keep both side-by-side and
diff the files to see how each concept maps.

## Concept map (DigitalOcean → Azure)

| DigitalOcean | Azure |
|---|---|
| `provider "digitalocean"` + `var.do_token` | `provider "azurerm"` + `az login` / Service Principal |
| (no equivalent) | **Resource Group** — mandatory container |
| `digitalocean_vpc` | (AKS manages its own VNet by default) |
| `digitalocean_kubernetes_cluster` (DOKS) | `azurerm_kubernetes_cluster` (AKS) |
| `node_pool { size = <slug> }` | `default_node_pool { vm_size = "Standard_B2s" }` |
| Spaces / S3 backend | `azurerm` blob backend |

## One-time bootstrap (state backend)

The `azurerm` backend needs a storage account + container that already exist.
Create them ONCE with the CLI, then `terraform init` can use them:

```bash
az login
az group create --name hivebox-tfstate-rg --location westeurope
az storage account create \
  --name hiveboxtfstatearash \
  --resource-group hivebox-tfstate-rg \
  --sku Standard_LRS
az storage container create \
  --name tfstate \
  --account-name hiveboxtfstatearash --auth-mode login
```

> The storage account name in `versions.tf` (`hiveboxtfstatearash`) must be
> **globally unique** across all of Azure. If it's taken, change it in both the
> command above and `versions.tf`.

## Provision the cluster

```bash
cp secrets.env.example secrets.env   # fill in subscription id, or just `az login`
source secrets.env
terraform init
terraform plan
terraform apply
```

## Connect kubectl

```bash
az aks get-credentials --resource-group hivebox-dev-rg --name hivebox-dev
kubectl get nodes
```

Then the app manifests in `../../k8s/` deploy unchanged — Kubernetes is
Kubernetes regardless of cloud.

## Tear down (do this when you're done for the day — AKS nodes cost money)

```bash
terraform destroy
```
