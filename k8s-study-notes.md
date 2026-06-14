# Kubernetes Study Notes — HiveBox Roadmap
> Lessons 1–12 | Beginner to Mid-Level

---

## Lesson 1 — Why Kubernetes is Needed in HiveBox

### Core idea
Docker runs containers. Kubernetes manages desired state across many containers.

Without Kubernetes:
- No automatic restarts if a container crashes
- No traffic routing between containers
- No rollout management
- Manual scaling

With Kubernetes:
- Declare what you want → Kubernetes makes it happen and keeps it that way

### Key distinction
| Docker | Kubernetes |
|---|---|
| Runs a single container | Manages many containers across nodes |
| You start/stop manually | Reconciles desired state continuously |
| No self-healing | Restarts failed containers automatically |

---

## Lesson 2 — KIND Cluster and Why We Used It Locally

### Core idea
KIND (Kubernetes IN Docker) creates a local Kubernetes cluster by running cluster nodes as Docker containers on your machine.

### Why KIND for HiveBox
- No cloud account needed
- Runs fully on your laptop
- Mirrors real cluster behavior closely enough for development and testing

### Key fact
KIND nodes are isolated Docker containers. They have their own image cache — separate from your host Docker. This matters when loading images (see Lesson 10).

```bash
# Create the HiveBox cluster
kind create cluster --name hivebox --config kind-config.yaml

# Verify
kind get clusters          # should return: hivebox
kubectl cluster-info       # should show kind-hivebox context
```

---

## Lesson 3 — kubectl and How We Interact with the Cluster

### Core idea
`kubectl` is the CLI for talking to the Kubernetes API server. Every action you take — viewing state, applying manifests, debugging — goes through `kubectl`.

### Key commands
```bash
kubectl get pods                          # list pods
kubectl get pods -n ingress-nginx         # list pods in a specific namespace
kubectl describe pod <name>               # detailed info + events
kubectl logs <pod-name>                   # container logs
kubectl apply -f k8s/                     # apply all manifests in a directory
kubectl config current-context            # should return: kind-hivebox
```

### Mental model
```
You → kubectl → Kubernetes API server → cluster state
```

---

## Lesson 4 — Kubernetes Manifests and Declarative Configuration

### Core idea
A manifest is a YAML file that describes desired state. You don't tell Kubernetes what to do step by step — you describe what you want and Kubernetes figures out how to get there.

```yaml
# Example: tell Kubernetes you want 2 replicas of your app
spec:
  replicas: 2
```

Kubernetes continuously reconciles: if reality doesn't match the manifest, it fixes it.

### Key fact
`kubectl apply -f k8s/` makes the cluster match everything in your manifest files. Run it again and Kubernetes only changes what's different.

---

## Lesson 5 — Pod vs Deployment

### Core idea
- **Pod** — the smallest unit in Kubernetes. One or more containers running together.
- **Deployment** — manages Pods. Ensures the right number are running, handles rolling updates, enables rollback.

You almost never create Pods directly. You create a Deployment and it manages Pods for you.

### Control flow
```
Deployment → ReplicaSet → Pod(s)
```

- Deployment manages the desired state (replicas, image, update strategy)
- ReplicaSet ensures the correct number of Pods exist
- Pod is where your container actually runs

### Key fact
If a Pod crashes, the ReplicaSet notices and creates a new one. If you delete a Pod manually, the ReplicaSet creates a replacement. To truly remove a Pod, delete the Deployment.

---

## Lesson 6 — Container Image Deployment

### Core idea
Kubernetes does not build Docker images. Your CI/CD pipeline builds the image and pushes it to a registry. Kubernetes then pulls it from the registry when starting a Pod.

### CD flow
```
Code merged → CI builds image → push to GHCR (tagged with git SHA)
→ CD updates Deployment image tag → Kubernetes pulls image → Pod starts
```

### Common error: ImagePullBackOff
Causes:
- Wrong image name or tag
- Image was never pushed to the registry
- Registry is private and pull secret is missing
- Typo in image reference

```bash
kubectl describe pod <name>   # shows the exact pull error in Events
```

### Key fact
In HiveBox, images are tagged with the git commit SHA:
```
ghcr.io/arashzitaly/hivebox:a3f92bc
```
This ensures every deploy has a unique, traceable tag.

---

## Lesson 7 — Readiness Probes

### Core idea
Running ≠ Ready.

- **Running** — the container process exists
- **Ready** — the readiness probe passed; the Pod can receive traffic

A Pod that is Running but not Ready is excluded from Service endpoints. Traffic does not reach it.

### What readiness probe does
- Passes → Pod is added to Service endpoints → traffic flows
- Fails → Pod is removed from Service endpoints → traffic stops (container keeps running)

### What liveness probe does (different)
- Fails → Kubernetes restarts the container

### Key fact
The readiness probe checks the **container port** (8080), not the Service port (80).

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Lesson 8 — Ingress and External Access

### Core idea
A Service gives Pods a stable internal address. Ingress exposes HTTP/HTTPS routes from outside the cluster to Services inside it.

### Traffic flow
```
External request
      ↓
Ingress            ← routing rules (host/path → Service)
      ↓
Service            ← finds Pods by label selector
      ↓
Pod                ← handles the request
```

### Port hops in HiveBox
```
http://localhost:8080      (Windows host browser)
      ↓
KIND port mapping: host:8080 → node:80
      ↓
Ingress-Nginx (node port 80)
      ↓
Service: port 80 → targetPort 8080
      ↓
Pod: container port 8080
```

### Key facts
- Ingress object is just config — a controller must be installed to act on it
- `ingressClassName: nginx` tells Kubernetes which controller handles this Ingress
- The Ingress object must be in the same namespace as the Service it routes to

```yaml
spec:
  ingressClassName: nginx
  rules:
  - host: localhost
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hivebox
            port:
              number: 80
```

---

## Lesson 9 — Ingress-Nginx Controller

### Core idea
The Ingress-Nginx controller is the software that reads Ingress objects and handles actual traffic. Kubernetes does not ship with one — you install it separately.

```
Your Ingress object     ← the rules (what you write)
        ↓
Ingress-Nginx Pod       ← the engine (reads and enforces the rules)
```

### Installation for KIND
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait until ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Verify
kubectl get pods -n ingress-nginx
```

### Key facts
- The controller runs in the `ingress-nginx` namespace, your app runs in `default` — this is normal
- The controller watches Ingress objects cluster-wide across all namespaces
- Use the KIND-specific manifest — there are separate manifests for AWS, GCP, bare-metal
- Check `kubectl get ingressclass` to see registered class names

### Common mistakes
| Mistake | Result |
|---|---|
| Wrong manifest for environment | Controller starts but port binding is wrong |
| No default IngressClass and no `ingressClassName` | Ingress is orphaned, nothing routes it |
| Checking Running but not Ready | Controller may still be initializing |
| Forgetting `-n ingress-nginx` | `kubectl get pods` won't show the controller |

---

## Lesson 10 — Local Kubernetes Testing Flow

### Core idea
The local testing flow is a repeatable sequence you run every time you make a code change. It mirrors exactly what a CD pipeline will automate.

### Why `kind load` is needed
KIND nodes are isolated Docker containers with their own image cache. Building an image on your host does not make it available inside the KIND node.

```
Your laptop Docker     ← image exists here after docker build
KIND node Docker       ← image does NOT exist here automatically
kind load              ← manually copies image from host into KIND node
```

In production, nodes pull directly from a registry. `kind load` is a local workaround only.

### The local flow
```bash
# 1. Build image
docker build -t ghcr.io/arashzitaly/hivebox:local .

# 2. Load into KIND node
kind load docker-image ghcr.io/arashzitaly/hivebox:local --name hivebox

# 3. Apply manifests (first time or after YAML changes)
kubectl apply -f k8s/

# 4. Update running Deployment
kubectl set image deployment/hivebox hivebox=ghcr.io/arashzitaly/hivebox:local

# 5. Wait for rollout to complete
kubectl rollout status deployment/hivebox

# 6. Test
curl http://localhost:8080/version
```

### Why `:latest` is problematic
Kubernetes decides whether to pull a new image based on whether the tag changed. If you always use `:latest`, the tag never changes and Kubernetes keeps using the cached image — even after you load a new one.

Always use a tag that changes: `:local-2`, `:local-3`, or a git commit SHA.

### Rolling update
`kubectl set image` starts a rolling update:
- New Pod starts with new image
- Old Pod keeps serving traffic until new Pod passes readiness probe
- Service switches traffic to new Pod
- Old Pod is terminated

Always run `kubectl rollout status` before testing — it blocks until the new Pod is fully Ready.

---

## Lesson 11 — How This Prepares Us for a CD Pipeline

### Core idea
The local flow you run manually is exactly what a CD pipeline automates. Same steps, same commands, different executor.

### Mapping: local vs CD

| Local (manual) | CD pipeline (automated) |
|---|---|
| `docker build` | Pipeline builds the image |
| Tag with `:local` | Pipeline tags with git commit SHA |
| `kind load` | Pipeline pushes to GHCR |
| `kubectl set image` | Pipeline updates the Deployment |
| `kubectl rollout status` | Pipeline waits for rollout |
| `curl localhost:8080/version` | Pipeline runs smoke tests |

### What changes between local and CD

**No `kind load`** — real cluster nodes have network access to GHCR and pull images directly.

**Real cluster** — `kubectl` in the pipeline talks to a real cluster (EKS, GKE, etc.). Manifests and commands are identical. Infrastructure underneath is different.

### Why git SHA tags matter
1. **Uniqueness** — every commit produces a different tag. Kubernetes always sees a new tag and pulls the new image. No stale cache problem.
2. **Traceability** — you can find exactly what code is running in production:

```bash
kubectl get deployment hivebox -o yaml | grep image
# ghcr.io/arashzitaly/hivebox:a3f92bc

git show a3f92bc   # see exactly what changed
```

### Readiness probe quality matters
`kubectl rollout status` succeeding only means the readiness probe passed. If the probe only checks that the port is open, a broken app can pass the probe and the pipeline reports success while users see errors.

A strong probe hits a real health endpoint that verifies dependencies:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
```

---

## Lesson 12 — Real DevOps / On-Call Relevance

### Core idea
Everything in Lessons 1–11 is the exact mental model you need when something breaks in production at 2am and you're on call.

Three questions to answer fast:
```
1. What is broken?     ← symptoms (alerts, user reports)
2. Where is it broken? ← which layer in the chain
3. How do I fix it?    ← rollback, restart, patch
```

### The full chain
```
CD pipeline → Image in registry → Deployment → ReplicaSet → Pod
→ Readiness probe → Service endpoints → Ingress → User
```

Any link can break. Your job is to find which one.

### Debugging by layer

| Symptom | Where to look | Command |
|---|---|---|
| App unreachable | Ingress or controller | `kubectl get ingress` / `kubectl get pods -n ingress-nginx` |
| 502 / no endpoints | Service has no Ready Pods | `kubectl get endpoints hivebox` |
| Pod not starting | Image pull or crash | `kubectl describe pod <name>` |
| Pod running but no traffic | Readiness probe failing | `kubectl describe pod <name>` → Events |
| New deploy broke the app | Bad image | `kubectl rollout undo deployment/hivebox` |
| Works in staging, fails in prod | Config or secret missing | `kubectl get secret` / env vars |

### Most important on-call commands

```bash
# What is the current state?
kubectl get pods
kubectl get endpoints hivebox
kubectl get ingress

# Why is this Pod not healthy?
kubectl describe pod <pod-name>

# What is the app saying?
kubectl logs <pod-name>
kubectl logs <pod-name> --previous   # logs from crashed/restarted container

# Immediate rollback
kubectl rollout undo deployment/hivebox

# What image is currently running?
kubectl get deployment hivebox -o yaml | grep image

# Rollout history
kubectl rollout history deployment/hivebox
```

### Key rules to remember

**Running ≠ Ready** — check `kubectl get endpoints` to confirm the Service actually has Pods behind it.

**`kubectl rollout undo`** — rolls back to the previous ReplicaSet's pod template using the same rolling update mechanism as a forward deploy, just in reverse.

**`--previous` flag** — `kubectl logs <pod-name> --previous` fetches logs from the terminated container before the restart. Without it, logs from a freshly restarted Pod are empty.

**Readiness probe quality** — `kubectl rollout status` success only means the probe passed. A weak probe (port check only) gives false confidence. Always have a real `/health` endpoint that verifies dependencies.

**First step when Pods are Running but no traffic:**
```bash
kubectl get endpoints hivebox   # <none> confirms readiness probe is failing
kubectl describe pod <name>     # Events section shows exactly why
```

---

## Key Mental Models

### The full chain
```
Code → docker build → Registry → Deployment image tag
→ ReplicaSet → Pod → Readiness probe
→ Service endpoints → Ingress rules → Ingress-Nginx
→ User
```

### Port hops (HiveBox)
```
localhost:8080 (host) → KIND node:80 → Ingress:80 → Service:80 → Pod:8080
```

### Running vs Ready
- Running = container process exists
- Ready = readiness probe passed, Service can send traffic

### Ingress object vs Ingress controller
- Ingress object = the routing rules (just config)
- Ingress controller = the software that enforces them (must be installed)

### Local vs production image delivery
- Local: `kind load` copies image into KIND node cache
- Production: node pulls image from registry directly

### Rollout commands
| Command | Purpose |
|---|---|
| `kubectl set image` | Starts a rolling update |
| `kubectl rollout status` | Blocks until rollout completes |
| `kubectl rollout undo` | Reverts to previous ReplicaSet |
| `kubectl rollout history` | Shows rollout history with revision numbers |
