# DevOps Learning Roadmap

## Meta
- **Main project:** HiveBox (https://devopsroadmap.io/projects/hivebox/)
- **Skill-specific projects:** roadmap.sh (https://roadmap.sh/devops/projects)
- **Strategy:** HiveBox is the spine. roadmap.sh projects are prep before each HiveBox phase.
- **Level:** Starting as beginner, progressing to mid-level
- **Goal:** Cloud/DevOps Engineer role

---

## Shortcuts (for Claude)
- `/roadmap` → Show full roadmap overview
- `/phase [n]` → Show details for that phase number
- `/current` → Show what I am currently working on
- `/next` → Show the next phase or prep project to tackle
- `/checkpoint` → Show the 3 milestone checkpoints and their status
- `/status [phase n] [done|in-progress|todo]` → Update status of a phase

---

## Roadmap Overview

| Step | Type | Name | Status |
|------|------|------|--------|
| 1 | Prep | Docker basics (Basic Dockerfile) | done |
| 2 | HiveBox | Phase 2 — First app + container | done |
| 3 | Prep | CI/CD basics (GitHub Pages Deployment) | done |
| 4 | HiveBox | Phase 3 — Real API + CI pipeline | todo |
| — | Milestone | Checkpoint 1 — Working API in CI | todo |
| 5 | Prep | Containers & multi-service (Dockerized Service + Multi-Container App) | todo |
| 6 | HiveBox | Phase 4 — Kubernetes + CD pipeline | todo |
| 7 | Prep | IaC & monitoring (IaC on DigitalOcean + Prometheus & Grafana + Automated DB Backups) | todo |
| 8 | HiveBox | Phase 5 — Production-grade | todo |
| — | Milestone | Checkpoint 2 — Production-grade system | todo |
| 9 | Prep | Networking & security (Bastion Host + Linux Server Setup + Blue-Green Deployment) | todo |
| 10 | HiveBox | Phase 6 — GitOps & optimization | todo |
| 11 | HiveBox | Phase 7 — Capstone (your own project) | todo |
| — | Milestone | Checkpoint 3 — Cloud/DevOps Engineer ready | todo |

---

## Foundation

---

### Step 1 — Prep: Docker basics
**Source:** roadmap.sh
**Project:** Basic Dockerfile
**URL:** https://roadmap.sh/projects/basic-dockerfile
**Status:** todo

**Why this comes first:**
HiveBox Phase 2 requires you to write a Dockerfile and run a container locally.
This project teaches you that workflow in isolation before the HiveBox codebase adds complexity.

**What you will learn:**
- Writing a Dockerfile (FROM, WORKDIR, COPY, RUN, CMD)
- Building an image with `docker build`
- Running a container with `docker run`
- Difference between an image and a container

**Prerequisites:**
- Docker Desktop installed and working (`docker run hello-world`)
- Basic terminal/command line comfort

**Done when:**
- You can build a Docker image from scratch and run it locally

---

### Step 2 — HiveBox Phase 2: First app + container
**Source:** HiveBox
**Roadmap module:** Welcome to the DevOps World
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-2
**Status:** todo

**Goal:**
Build a minimal Python app, containerize it, and run it locally.

**Tasks:**
- Fork the HiveBox repository on GitHub
- Create a GitHub Kanban board for the project
- Write a Python script that prints the app version (`v0.0.1`)
- Write a Dockerfile that containerizes the app
- Build the image and run it locally
- Verify the container prints the correct version
- Open each phase as a Pull Request against your own `main` branch (never push directly)
- Document how to test the app in the README

**Tools:**
- Git
- VS Code
- Docker

**Done when:**
- Container runs locally and returns the correct version output
- Phase is merged via Pull Request

---

### Step 3 — Prep: CI/CD basics
**Source:** roadmap.sh
**Project:** GitHub Pages Deployment
**URL:** https://roadmap.sh/projects/github-actions-deployment-workflow
**Status:** todo

**Why this comes before Phase 3:**
HiveBox Phase 3 requires you to write a GitHub Actions CI workflow.
This project gives you hands-on practice with Actions syntax and workflow structure first.

**What you will learn:**
- GitHub Actions workflow YAML structure
- Triggers (on: push, pull_request)
- Jobs and steps
- Deploying a static site automatically on push

**Done when:**
- A GitHub Actions workflow runs automatically on push and deploys a static site

---

### Step 4 — HiveBox Phase 3: Real API + CI pipeline
**Source:** HiveBox
**Roadmap module:** Start — Laying the Base
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-3
**Status:** todo

**Goal:**
Build real API endpoints, write unit tests, and wire up a full CI pipeline.

**Tasks:**
- Use Conventional Commits for all Git commits from this point forward
- Implement `/version` endpoint — returns the deployed app version
- Implement `/temperature` endpoint — returns average temperature from openSenseMap (data must be no older than 1 hour)
- Write unit tests for all endpoints
- Apply Docker best practices to the Dockerfile
- Create a GitHub Actions CI workflow that:
  - Lints the code (Pylint) and Dockerfile (Hadolint)
  - Builds the Docker image
  - Runs unit tests
  - Calls `/version` endpoint and verifies the response
- Set up OpenSSF Scorecard GitHub Action

**Tools:**
- Python Flask or FastAPI
- Pylint
- Hadolint
- GitHub Actions
- openSenseMap API (https://docs.opensensemap.org/)

**SenseBox IDs to use:**
- 5eba5fbad46fb8001b799786
- 5c21ff8f919bf8001adf2488
- 5ade1acf223bd80019a1011c

**Done when:**
- Two endpoints working and tested
- CI pipeline passes on every Pull Request

---

### Checkpoint 1 — Working API in CI
**Status:** todo

You have a real containerized Python API with a passing GitHub Actions CI pipeline.
The project is documented on GitHub with a clear README.
This is already a solid portfolio item for a Junior DevOps role.

---

## Intermediate

---

### Step 5 — Prep: Containers & multi-service
**Source:** roadmap.sh
**Projects:**
- Dockerized Service — https://roadmap.sh/projects/dockerized-service-deployment
- Multi-Container Application — https://roadmap.sh/projects/multi-container-service
**Status:** todo

**Why this comes before Phase 4:**
HiveBox Phase 4 introduces Kubernetes. Before dealing with Kubernetes manifests,
you need to be comfortable with multi-container deployments and Docker Compose.

**What you will learn:**
- Deploying a Dockerized app via GitHub Actions to a remote server
- Docker Compose for running multiple containers together
- Networking between containers
- Environment variable configuration across services

**Done when:**
- You can run a multi-container app locally with Docker Compose
- You understand how services communicate inside a Compose network

---

### Step 6 — HiveBox Phase 4: Kubernetes + CD pipeline
**Source:** HiveBox
**Roadmap module:** Expand — Constructing a Shell
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-4
**Status:** todo

**Goal:**
Deploy the app on a local Kubernetes cluster and build a full CD pipeline.

**Tasks:**
- Implement `/metrics` endpoint — returns default Prometheus metrics
- Update `/temperature` endpoint to include a status field:
  - Less than 10 → Too Cold
  - 11–36 → Good
  - More than 37 → Too Hot
- Make senseBox IDs configurable via environment variables
- Write integration tests
- Create a KIND cluster configuration with Ingress-Nginx
- Create Kubernetes core manifests to deploy the app
- Add to CI pipeline:
  - Integration tests
  - SonarQube for code quality and security analysis
  - Terrascan for Kubernetes manifest misconfiguration scanning
- Create a CD GitHub Actions workflow that:
  - Pushes a versioned Docker image to GitHub Container Registry

**Tools:**
- KIND (Kubernetes in Docker)
- kubectl
- SonarQube
- Terrascan
- GitHub Container Registry

**Done when:**
- App runs on local Kubernetes cluster
- Versioned Docker image pushed to registry on every release
- CI + CD pipelines both pass

---

### Step 7 — Prep: IaC & monitoring
**Source:** roadmap.sh
**Projects:**
- IaC on DigitalOcean (Terraform) — https://roadmap.sh/projects/iac-digitalocean
- Prometheus and Grafana — https://roadmap.sh/projects/monitoring
- Automated DB Backups — https://roadmap.sh/projects/automated-backups
**Status:** todo

**Why this comes before Phase 5:**
HiveBox Phase 5 uses Terraform to provision a real Kubernetes cluster and
Grafana to visualize metrics. These projects give you hands-on practice first.

**What you will learn:**
- Terraform basics: providers, resources, state, apply/destroy
- Prometheus scraping and alerting
- Grafana dashboards and data sources
- Scheduled automation (cron jobs, workflows)

**Done when:**
- You can write basic Terraform to provision cloud infrastructure
- You can set up a Prometheus + Grafana stack and create a dashboard

---

### Step 8 — HiveBox Phase 5: Production-grade
**Source:** HiveBox
**Roadmap module:** Transform — Finishing the Structure
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-5
**Status:** todo

**Goal:**
Add caching, storage, Helm packaging, Terraform infrastructure, and end-to-end tests.

**Tasks:**
- Add Redis-compatible caching layer using Valkey
- Add S3-compatible storage using MinIO — store data every 5 minutes automatically
- Implement `/store` endpoint — triggers immediate data store to MinIO
- Extend `/metrics` with custom Prometheus metrics
- Implement `/readyz` endpoint — returns HTTP 200 unless:
  - 50%+1 of senseBoxes are not accessible AND cache is older than 5 minutes
- Configure `/readyz` as Kubernetes readiness probe
- Create a Helm chart for the application
- Create Kustomize manifests for infrastructure resources
- Review and apply Kubernetes security best practices
- Deploy Grafana agent to collect logs and metrics (use Grafana Cloud free tier)
- Provision a Kubernetes cluster using Terraform
- Add end-to-end tests using Venom
- Run full E2E test suite in CI: spin up KIND cluster → deploy app → run tests

**Tools:**
- Valkey (Redis-compatible)
- MinIO (S3-compatible)
- Helm
- Kustomize
- Terraform
- Grafana Cloud (free tier)
- Venom (E2E testing)

**Done when:**
- Full stack running: API → caching → storage → Kubernetes → IaC → monitoring → CI/CD
- All tests pass end-to-end

---

### Checkpoint 2 — Production-grade system
**Status:** todo

Full stack project: Python API, Docker, Kubernetes, Helm, Terraform, Prometheus, Grafana, CI/CD.
The GitHub repository documents the entire SDLC.
This is an interview-ready portfolio for a DevOps Engineer role.

---

## Advanced

---

### Step 9 — Prep: Networking & security
**Source:** roadmap.sh
**Projects:**
- Bastion Host — https://roadmap.sh/projects/bastion-host
- Linux Server Setup — https://roadmap.sh/projects/linux-server-setup
- Blue-Green Deployment — https://roadmap.sh/projects/blue-green-deployment
**Status:** todo

**Why this comes before Phase 6:**
HiveBox Phase 6 introduces production DNS, certificates, and policy-as-code.
These projects build the networking and security foundation you need.

**What you will learn:**
- Managing access to private infrastructure via a bastion host
- Hardening a Linux server (firewall, SSH config, fail2ban)
- Zero-downtime deployments with blue-green strategy

**Done when:**
- You understand how to secure access to cloud infrastructure
- You can implement a blue-green deployment strategy

---

### Step 10 — HiveBox Phase 6: GitOps & optimization
**Source:** HiveBox
**Roadmap module:** Optimize — Keep Improving
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-6
**Status:** todo

**Goal:**
Move to a fully declarative GitOps deployment model and harden the system.

**Recommended tasks:**
- Deploy the application using ArgoCD in declarative GitOps style
- Set up ExternalDNS for automatic DNS management
- Set up Cert-Manager for automatic TLS certificate provisioning
- Automate dependency updates with Dependabot
- Set up Kyverno for Policy as Code

**Optional advanced tasks:**
- Move all external services (Grafana Cloud, Terraform Cloud) onto the cluster using open-source alternatives
- Build multi-environment clusters (Dev, Stage, Prod) with Terraform and Kustomize
- Use TestKube for better test execution
- Develop a Kubernetes Operator for app operations

**Tools:**
- ArgoCD
- ExternalDNS
- Cert-Manager
- Dependabot
- Kyverno

**Done when:**
- Application deploys declaratively via ArgoCD on every Git push
- DNS and certificates are automated
- At least one Kyverno policy is enforced

---

### Step 11 — HiveBox Phase 7: Capstone project
**Source:** HiveBox
**Roadmap module:** Capstone Project
**URL:** https://devopsroadmap.io/projects/hivebox/#phase-7
**Status:** todo

**Goal:**
Design and build your own original project using everything you have learned.
You choose the idea and the tech stack.

**Requirements:**
- Follow the same SDLC structure as HiveBox (planning → code → containers → CI/CD → IaC → monitoring)
- Document everything as if someone else will read it
- Present it as a public GitHub repository

**Done when:**
- Original project is live, documented, and publicly available on GitHub

---

### Checkpoint 3 — Cloud/DevOps Engineer ready
**Status:** todo

Two complete projects on GitHub: HiveBox (end-to-end DevOps) + your own original capstone.
Full GitOps pipeline, Kubernetes expertise, IaC, monitoring, and security hardening.
Ready to target mid-level DevOps and Cloud Engineering roles.

---

## Tools master list

| Tool | First introduced | Phase |
|------|-----------------|-------|
| Git + GitHub | Foundation | Step 1 |
| Docker | Foundation | Step 1 |
| Python (Flask/FastAPI) | Foundation | Step 4 |
| GitHub Actions | Foundation | Step 3 |
| Pylint / Hadolint | Foundation | Step 4 |
| Docker Compose | Intermediate | Step 5 |
| Kubernetes / KIND / kubectl | Intermediate | Step 6 |
| Prometheus | Intermediate | Step 6 |
| SonarQube / Terrascan | Intermediate | Step 6 |
| Helm | Intermediate | Step 8 |
| Kustomize | Intermediate | Step 8 |
| Terraform | Intermediate | Step 7 |
| Grafana | Intermediate | Step 7 |
| Valkey (Redis) | Intermediate | Step 8 |
| MinIO (S3) | Intermediate | Step 8 |
| ArgoCD | Advanced | Step 10 |
| Cert-Manager / ExternalDNS | Advanced | Step 10 |
| Kyverno | Advanced | Step 10 |

---

## Notes
- Each HiveBox phase must be opened as a Pull Request — never push directly to main
- Use Conventional Commits from Phase 3 onward
- Document as you go — always write README updates alongside code changes
- The three checkpoints are natural stopping points if life gets busy
- Consistency over speed — one focused session per week beats sporadic marathons