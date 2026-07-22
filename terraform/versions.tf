terraform {
  required_version = ">= 1.6.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  # Remote state on DigitalOcean Spaces (S3-compatible).
  # Credentials come from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (your Spaces key).
  backend "s3" {
    endpoints = {
      s3 = "https://fra1.digitaloceanspaces.com"
    }
    bucket = "hivebox-tfstate-arash"
    key    = "iac-digitalocean/terraform.tfstate"
    region = "us-east-1" # dummy; DO ignores it but the s3 backend requires a value

    # S3-native state locking (Terraform >= 1.11) — writes a .tflock object
    # in the bucket. No DynamoDB needed, which DO Spaces doesn't have.
    use_lockfile = true

    # DO Spaces is not real AWS — skip AWS-only checks:
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}