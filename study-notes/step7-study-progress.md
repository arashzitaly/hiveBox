# HiveBox — Step 7 Study Progress

> Progress tracker for the DevOps roadmap. Any agent (Claude Code, Codex, etc.)
> picking up this repo should read this file first to know exactly where we are.
> Rule: nothing is marked DONE without evidence (actual code / applied infra / observed output).

Last updated: 2026-09-27 (Step 7 done and synced to Notion; backup lab resource group and downloaded SSH key absent)

## Position
- Step 6 — HiveBox Phase 4: **DONE**
- Step 7 — Prep: IaC & Monitoring: **DONE (agreed Azure adaptation for Project 3)**
- Roadmap source: `../devops-roadmap.md` (repo root)
- Notion roadmap tracker: https://www.notion.so/DevOps-Learning-Roadmap-327875ec8f1b81ce91d9e3109b6dd863
- Prior knowledge: Kubernetes lessons 1–12 done — notes in `k8s-study-notes.md` (this folder)

## Step 7 contains THREE roadmap.sh projects (in order)
1. IaC (Terraform) — https://roadmap.sh/projects/iac-digitalocean — done on DigitalOcean, then ported to Azure/AKS (primary)
2. Prometheus & Grafana (Monitoring) — https://roadmap.sh/projects/monitoring
3. Automated DB Backups — https://roadmap.sh/projects/automated-backups

## Agreed working method
Per project, run the loop: **Study → Build (code) → verify with evidence → next project.**
Do NOT batch all study first. Finish each project end-to-end before moving on.

1. IaC: study → build DOKS/AKS + remote state → `kubectl get nodes` hits cloud (done on DO, then Azure)
2. Monitoring: study → deploy Prometheus/Grafana on cluster → HiveBox metrics in dashboard
3. Backups: study → automate DB backups → prove a restore works

## Current status by project

### Project 1 — IaC (Terraform): DigitalOcean (original) + Azure/AKS (primary going forward)
Study (theory):
- Lesson 1 — Why Terraform / what IaC means (declarative vs imperative, state): **DONE**
- Lesson 2 — Providers, core workflow (init/plan/apply/destroy), DO auth: **DONE**
- Lesson 3 — Resources, arguments vs attributes, wiring by reference: **DONE**
- Lesson 4 — Variables, outputs, extracting kubeconfig: **DONE**
- Lesson 5 — Remote state (DO Spaces / s3 backend, locking, why local breaks): **DONE**
- Lesson 6 — `terraform destroy`, lifecycle, cost discipline: **DONE**

Study (theory): **COMPLETE** — all 6 lessons done, checkpoints passed.
Build (code): **DONE** — DOKS cluster provisioned via Terraform, verified on the cloud, and torn down.

Build evidence (2026-07-22):
- `terraform/` scaffold: `versions.tf` (s3 backend + `use_lockfile` locking), `variables.tf`
  (`do_token` sensitive/no-default), `main.tf` (provider + `digitalocean_vpc` + `digitalocean_kubernetes_cluster`
  + k8s-version data source), `outputs.tf` (cluster info + sensitive kubeconfig).
- Remote state: DO Spaces bucket `hivebox-tfstate-arash` (fra1), key `iac-digitalocean/terraform.tfstate`,
  S3-native lockfile. Spaces key `hivebox-tfstate` (R/W/D). Creds via gitignored `secrets.env` + `TF_VAR_`/`AWS_*` env.
- Workflow: `init` (backend OK) -> `plan` (2 to add) -> `apply` (2 added). k8s `1.36.0-do.3`.
- CLOUD proof: `kubectl config current-context` = `do-fra1-hivebox-dev`; `kubectl get nodes -o wide` =
  2 nodes `Ready` v1.36.0, VPC internal IPs 10.10.10.3/.4 (matches TF-defined 10.10.10.0/24). Not KIND.
- Cost control: `terraform destroy` destroyed the DOKS cluster (only billable resource — 0 charges left).
  VPC auto-promoted to fra1 *default* (DO forbids deleting default VPCs; VPCs are free), so it was removed
  from state via `terraform state rm digitalocean_vpc.hivebox`. Verified: `terraform state list` empty.
- Gotcha logged: DO makes the first VPC in a region the default; default VPCs can't be `destroy`ed.
  Also: `source secrets.env` per new shell — a fresh terminal loses env vars ("No valid credential sources").
- Secrets: never committed (`git check-ignore` confirms `secrets.env` ignored; example holds placeholders only).

Azure port evidence (2026-07-23):
- `terraform/azure/` mirrors the DO layout: `versions.tf` (azurerm provider + azurerm blob backend, `use_azuread_auth`),
  `variables.tf` (subscription_id/location/node_size), `main.tf` (provider `features {}` + `azurerm_resource_group`
  + `azurerm_kubernetes_cluster` with SystemAssigned identity), `outputs.tf`. Each file comments the DO→Azure mapping.
- State backend bootstrapped out-of-band via `az`: `hivebox-tfstate-rg` + storage account `hiveboxtfstatearash`
  (North Europe) + `tfstate` container. Keyless auth via role `Storage Blob Data Contributor` + `ARM_USE_AZUREAD=true`.
- CLOUD proof: `terraform apply` created AKS `hivebox-dev` (control plane) + auto-generated `MC_hivebox-dev-rg_...`
  group (VMSS 2× `Standard_B2s_v2`, VNet, NSG, load balancer, public IP, managed identity) in `swedencentral`.
  Verified in portal / `az group list`.
- Cost control: `terraform destroy` removed the cluster + MC_ group (VMSS = only billable resource; 0 charges left).
  `az group list` after destroy = only `hivebox-tfstate-rg` + `NetworkWatcherRG` (both free/pennies, kept by design).
- Trial-subscription gotchas logged: `westeurope` refused new customers; `northeurope`/`swedencentral` restrict VM
  SKUs (no v1 `Standard_B2s` — used `Standard_B2s_v2`). Rule: trust the "available VM sizes" list in the AKS 400 error,
  not `az vm list-skus`. Fresh subs need `az provider register` for Microsoft.Storage/ContainerService (few-min propagation).
- Decoupling: Azure port is independent of the app/k8s/CI-CD (all cloud-agnostic — unchanged). DO config preserved
  in `terraform/digitalocean/` as a reference for side-by-side diffing.

### Project 2 — Prometheus & Grafana (Monitoring)
Study: **COMPLETE** — 6 lessons, checkpoint-gated, all passed (2026-07-26). Interview-defense note in the
Obsidian vault: "Monitoring — Prometheus & Grafana Study Session".
Build: **NOT STARTED**

Study coverage (2026-07-26):
- L1 monitoring/observability (3 pillars; Prometheus = metrics; pull model + its advantages).
- L2 architecture (K8s service discovery → scrape → TSDB point = metric+labels+timestamp+value → PromQL; local-disk
  TSDB trade-off, add Thanos/managed for LT/HA).
- L3 metric types (counter+`rate()`, gauge, histogram=aggregatable percentiles, summary=per-instance) + HiveBox
  plain-text `/metrics`.
- L4 Grafana (display layer; data source; PromQL; separation of concerns vs Prometheus UI).
- L5 alerting (PromQL rule + `for` duration; Prometheus fires → Alertmanager routes/groups/dedups/silences).
- L6 deploy plan: `kube-prometheus-stack` Helm chart + HiveBox `ServiceMonitor` (Operator-driven) → verify
  Prometheus → Status → Targets = UP → Grafana dashboard.

Build: **DONE** (2026-07-26) — deployed and verified on AKS end-to-end, then destroyed for cost.

Build evidence (2026-07-26):
- Cluster: `terraform apply` (AKS `hivebox-dev`, 2× `Standard_B2s_v2`, swedencentral); `az aks get-credentials`;
  2 nodes Ready v1.35.6.
- App: deployed `k8s/deployment.yaml` + `k8s/service.yaml` to `default` ns. Fixed image tag `0.0.1` → `v0.0.6`
  (only `latest`/`v0.0.6` exist in GHCR; 0.0.1 was 404 → ErrImagePull). GHCR package made public. Pod 1/1 Running.
- Stack: `helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace`
  — Prometheus 2/2, Grafana 3/3, Alertmanager, Operator, kube-state-metrics, node-exporter all Running.
- Scrape: new `k8s/servicemonitor.yaml` (label `release: monitoring` REQUIRED for kube-prometheus-stack to select it;
  selector `app: hivebox`, port `http`, path `/metrics`). Verified Prometheus → Targets: `serviceMonitor/default/hivebox/0`
  = UP, scraping `10.244.x:8080/metrics`. `up{job="hivebox"}` = 1.
- Dashboard: Grafana (admin creds from `monitoring-grafana` secret), 3 panels — Availability `up{job="hivebox"}`=1,
  CPU `rate(process_cpu_seconds_total{job="hivebox"}[5m])`, Memory `process_resident_memory_bytes{job="hivebox"}` (~43MB).
  Note: HiveBox exposes DEFAULT python/process metrics only (no custom `http_requests_total`).
- Cost: `terraform destroy` → only `hivebox-tfstate-rg` + `NetworkWatcherRG` remain. Total spend for session ≈ pennies.
- Uncommitted repo changes from this build: new `k8s/servicemonitor.yaml`, `k8s/deployment.yaml` image tag → `v0.0.6`.

### Project 3 — Automated DB Backups
Study: **DONE (Azure adaptation)** — discussed backup validation and chose Azure for the server. The upstream project requires a database, a 12-hour backup schedule, and a tarball uploaded to Cloudflare R2. On 2026-09-27, the user intentionally replaced R2 with Azure Blob Storage to keep the lab in Azure and avoid managing a second cloud provider. The user accepted configuring the 12-hour schedule plus a successful manual trigger as sufficient lab evidence, without keeping the VM running until an elapsed scheduled firing. The upstream R2 destination is not met literally; the download-latest-and-restore script is an optional stretch goal.
Build: **DONE (Azure adaptation)** — Azure portal reported deployment complete for `backup-test-vm` in resource group `hivebox-backups-rg` on 2026-09-27. VM Overview showed Status `Running`, Ubuntu 24.04, and size `Standard D2s v3` (2 vCPUs, 8 GiB). SSH login reached the `azureuser@backup-test-vm` shell. After MongoDB installation, `systemctl is-active mongod` returned `active`. `backup_lab.samples` contained two verified records (`one`/`alpha`/2 and `two`/`beta`/5). `mongodump` reported 2 documents; `backup_lab.tar.gz` was 427 bytes and listed `samples.bson` plus metadata. A separate `restore_lab.samples` contained the same two expected records after restoring from the tarball. Azure portal showed storage account `hiveboxbackupsarash27` with private `mongodb-backups` container and Storage Blob Data Contributor assignment to the `backup-test-vm` managed identity. On the VM, `az login --identity --allow-no-subscriptions` returned `systemAssignedIdentity` and Azure subscription 1. `az storage blob upload --auth-mode login` returned 100% and a successful response for `backup_lab.tar.gz` at 2026-09-27T09:08:41+00:00. Azure portal container screenshot showed `backup_lab.tar.gz` as a 427 B block blob with last modified 2026-09-27 11:08:41 AM in portal local time. Later checks below verify the Azure download and installed schedule. A separate restore from the downloaded path and an elapsed cron firing were not run.

SSH error resolved (2026-09-27): Windows OpenSSH rejected the downloaded private key as too broadly readable (`CodexSandboxUsers`). Restricted the key file ACL with `icacls`, then SSH login succeeded. Prevention check: inspect private-key ACLs when OpenSSH reports `UNPROTECTED PRIVATE KEY FILE`.

Azure copy check (2026-09-27): `az storage blob download --auth-mode login` returned the 427-byte `backup_lab.tar.gz` from `mongodb-backups`; SHA-256 matched the locally restored tarball (`5a3d10244edcf807144c9ba4fb402882f7eaf7a30129f9476cd1d994b26824b0`). A separate restore from the downloaded path was not run.

Manual automation check (2026-09-27): Azure VM Run Command output showed `Uploaded backup_lab-20260927T091550Z.tar.gz from 2 source documents`; `mongodump` stderr reported 2 documents and Azure CLI upload reached 100%. Since this ran through Run Command, persistence and ownership of `/home/azureuser/backup-lab/run-backup.sh` remain unverified; the 12-hour schedule is not configured.

Saved script check (2026-09-27): SSH output showed `/home/azureuser/backup-lab/run-backup.sh` exists with `-rwxr-xr-x` permissions, owned by `root:root`; `test -x` as `azureuser` printed `script ready`. Execution as `azureuser` and the schedule remain unverified.

Scheduler-user test (2026-09-27): `azureuser` ran `/home/azureuser/backup-lab/run-backup.sh`; `mongodump` reported 2 documents and the script printed `Uploaded backup_lab-20260927T091923Z.tar.gz from 2 source documents` after Azure CLI reached 100%. Cron entry and scheduled execution remain unverified.

Cron configuration (2026-09-27): VM reported `UTC +0000`; `systemctl is-active cron` returned `active`; `crontab -l` for `azureuser` showed `0 0,12 * * * /home/azureuser/backup-lab/run-backup.sh >> /home/azureuser/backup-lab/cron.log 2>&1`. This proves installation for 00:00 and 12:00 UTC, not an elapsed scheduled run. Error-to-knowledge: typing the cron expression at the shell prompt left `crontab -l` empty; a cron expression is configuration. Fix: `printf '%s\n' '0 0,12 * * * /home/azureuser/backup-lab/run-backup.sh >> /home/azureuser/backup-lab/cron.log 2>&1' | crontab -`. Prevention check: always run `crontab -l` after installing an entry.

Manual cron-command trigger (2026-09-27): running the exact crontab command as `azureuser` returned `exit=0`; `cron.log` recorded `done dumping backup_lab.samples (2 documents)` and `Uploaded backup_lab-20260927T092556Z.tar.gz from 2 source documents`. The earlier `0: command not found` log line came from entering the cron expression at the shell prompt; it was not part of this successful run. Elapsed scheduled execution remains unobserved.

Cost-control checkpoint (2026-09-27): Azure VM Overview screenshot showed `backup-test-vm` status `Stopped (deallocated)`. The Delete pane was open and selected the OS disk, NIC, and public IP as associated resources, but the final deletion confirmation was not selected and deletion was not verified. The separate Azure Blob storage account was not listed for deletion.

Cloud cleanup (2026-09-27): Azure Cloud Shell `az group exists --name hivebox-backups-rg` returned `false`, proving the backup-lab resource group and its resources were deleted. Codex could not delete the downloaded SSH key through its Windows sandbox identity, but a later `Test-Path -LiteralPath 'C:\Users\arash\Downloads\backup-test-vm_key.pem'` returned `False`, proving the local key file is gone.

Tracking sync (2026-09-27): The Notion DevOps Learning Roadmap Step 7 overview and detail now say Done (3 of 3, agreed Azure adaptation). The Notion progress line records the backup, restore, Azure upload, matching download hash, active cron entry, manual trigger, and verified resource cleanup. Notion fetch after update confirmed these edits. The overall Notion project remains In progress because Step 8 and later steps are TODO.

## Overall
Step 7: 3/3 agreed prep projects DONE. Project 1 (IaC) DONE — study + build, DigitalOcean AND Azure/AKS.
Project 2 (Monitoring) DONE — study + build (kube-prometheus-stack + ServiceMonitor + Grafana dashboard on AKS, verified, destroyed).
Project 3 (Automated DB Backups) DONE for the agreed Azure lab: local database, tarball, restore, Azure Blob upload, installed 12-hour schedule, and manual trigger verified. An elapsed scheduled firing was intentionally not observed to avoid VM charges; the optional download-latest-and-restore script was not built.
Next action: Step 8 (HiveBox Phase 5) remains TODO. The backup lab needs no further resource cleanup based on the verified resource group and key checks.

## Teaching format (for continuity)
Interactive, one lesson at a time. Lesson template:
Simple explanation / What we'll do in HiveBox / Why it's needed / How it connects to previous work /
Commands or config involved / Common mistakes / Checkpoint questions (ask, wait, correct before continuing).
Beginner-to-mid level. Direct, technical, concise. Only roadmap/HiveBox-allowed stack.
