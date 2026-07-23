terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # Azure equivalent of DigitalOcean's `digitalocean/digitalocean` provider.
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote state in an Azure Storage Account blob container.
  # This is the Azure equivalent of the DO Spaces (S3) backend.
  #
  # CHICKEN-AND-EGG: the storage account + container below must EXIST before
  # `terraform init` can use them. You bootstrap them ONCE, out-of-band, with
  # the Azure CLI (see azure/README-bootstrap below in this folder), then
  # everything else is managed by Terraform.
  #
  # Auth for the backend comes from your `az login` session (Azure CLI) or the
  # ARM_* service-principal env vars — NOT hardcoded here.
  backend "azurerm" {
    resource_group_name  = "hivebox-tfstate-rg"
    storage_account_name = "hiveboxtfstatearash" # 3-24 chars, lowercase+digits only, GLOBALLY unique
    container_name       = "tfstate"
    key                  = "iac-azure/terraform.tfstate"

    # State locking on Azure is automatic via blob leases — no DynamoDB-style
    # lock table needed (DO Spaces needed `use_lockfile`; Azure gives it free).
    use_azuread_auth = true
  }
}
