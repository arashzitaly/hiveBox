# HiveBox — Step 7 Study Progress

> Progress tracker for the DevOps roadmap. Any agent (Claude Code, Codex, etc.)
> picking up this repo should read this file first to know exactly where we are.
> Rule: nothing is marked DONE without evidence (actual code / applied infra / observed output).

Last updated: 2026-07-18

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
- Lesson 6 — `terraform destroy`, lifecycle, cost discipline: **NEXT (not started)**

Build (code): **NOT STARTED** — no .tf written, no apply run, no cluster exists.

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