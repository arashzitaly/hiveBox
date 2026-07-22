# HiveBox — Step 7 Study Progress

> Progress tracker for the DevOps roadmap. Any agent (Claude Code, Codex, etc.)
> picking up this repo should read this file first to know exactly where we are.
> Rule: nothing is marked DONE without evidence (actual code / applied infra / observed output).

Last updated: 2026-07-22 (Project 1 BUILD complete — evidence captured)

## Position
- Step 6 — HiveBox Phase 4: **DONE**
- Step 7 — Prep: IaC & Monitoring: **CURRENT**
- Roadmap source: `../devops-roadmap.md` (repo root)
- Prior knowledge: Kubernetes lessons 1–12 done — notes in `k8s-study-notes.md` (this folder)

## Step 7 contains THREE roadmap.sh projects (in order)
1. IaC on DigitalOcean (Terraform) — https://roadmap.sh/projects/iac-digitalocean
2. Prometheus & Grafana (Monitoring) — https://roadmap.sh/projects/monitoring
3. Automated DB Backups — https://roadmap.sh/projects/automated-backups

## Agreed working method
Per project, run the loop: **Study → Build (code) → verify with evidence → next project.**
Do NOT batch all study first. Finish each project end-to-end before moving on.

1. IaC: study → build DOKS + remote state → `kubectl get nodes` hits cloud
2. Monitoring: study → deploy Prometheus/Grafana on cluster → HiveBox metrics in dashboard
3. Backups: study → automate DB backups → prove a restore works

## Current status by project

### Project 1 — IaC on DigitalOcean (Terraform)
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
  from state via `terraform state rm digitalocean_vpc.hivebox`. Verified: `terraform state list` empty,
  `doctl kubernetes cluster list` empty.
- Gotcha logged: DO makes the first VPC in a region the default; default VPCs can't be `destroy`ed.
  Also: `source secrets.env` per new shell — a fresh terminal loses env vars ("No valid credential sources").
- Secrets: never committed (`git check-ignore` confirms `secrets.env` ignored; example holds placeholders only).

### Project 2 — Prometheus & Grafana (Monitoring)
Study: **NOT STARTED**
Build: **NOT STARTED**

### Project 3 — Automated DB Backups
Study: **NOT STARTED**
Build: **NOT STARTED**

## Overall
Step 7 study section ≈ 1/3 done (Project 1 nearly complete, needs Lesson 6). No code written for any Step 7 project yet.

## Teaching format (for continuity)
Interactive, one lesson at a time. Lesson template:
Simple explanation / What we'll do in HiveBox / Why it's needed / How it connects to previous work /
Commands or config involved / Common mistakes / Checkpoint questions (ask, wait, correct before continuing).
Beginner-to-mid level. Direct, technical, concise. Only roadmap/HiveBox-allowed stack.