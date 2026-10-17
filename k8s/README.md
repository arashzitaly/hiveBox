# Local Phase 5 stack

`kubectl kustomize k8s` renders Valkey, MinIO, a MinIO PVC, and the bucket
initialization Job. HiveBox's Deployment and Service are managed by the Helm
chart in `charts/hivebox`. The root Kustomize configuration uses the local
`hivebox:phase5-local` image for the bucket Job only. The older `deployment.yaml`
and `service.yaml` files are historical references, excluded from active
Kustomize resources; do not apply them over the Helm release. Infrastructure
also has an entry point at `k8s/infra`. This is a single-node learning deployment.

## Connections

All resources and the credentials Secret must be in the same namespace.
HiveBox uses Service DNS `hivebox-valkey:6379` and `hivebox-minio:9000`.
Neither dependency is exposed outside the cluster. MinIO uses HTTP for this
local exercise. Its credentials are injected using `secretKeyRef`, following
the Kubernetes Secret-to-environment pattern. Credentials are not in Git.

Valkey is an ephemeral cache with persistence disabled. MinIO mounts a 1 GiB
PVC using the cluster's default StorageClass. Deleting the cluster can delete
its local storage; the host Docker volume is separate and is not imported.
The MinIO Deployment uses Recreate because it has one writable data volume.
The initialization Job creates `hivebox` if missing. HiveBox can initially
report 503 until this Job and the background loops populate data.

## Run on KIND

Prerequisites: Docker Desktop, KIND, kubectl, and the previously source-built
`hivebox-minio:local` image. The old public MinIO images could not be pulled
in this exercise. No replacement registry image is assumed.

Inspect the intended target first:

```powershell
kind get clusters
kubectl --context kind-hivebox get nodes
```

If the `hivebox` cluster is absent, create it using the existing config:

```powershell
kind create cluster --name hivebox --config k8s/kind-config.yaml
```

That config reserves host ports 8080 and 8443. Stop a local Flask process using
8080 first. It does not install an Ingress controller; ingress and monitoring
manifests are deliberately not included in this stack's resource list.

Build the current application and load the local images:

```powershell
docker build -t hivebox:phase5-local .
kind load docker-image hivebox:phase5-local hivebox-minio:local --name hivebox
```

Set `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in your PowerShell session before
this next command. Choose local exercise credentials; do not paste secrets
into tracked files. The same Secret supplies MinIO root credentials and the
HiveBox client for this lab. Separate limited application credentials remain
a hardening task.

```powershell
kubectl --context kind-hivebox -n default create secret generic hivebox-minio-credentials --from-literal="access-key=$env:MINIO_ACCESS_KEY" --from-literal="secret-key=$env:MINIO_SECRET_KEY" --dry-run=client -o yaml | kubectl --context kind-hivebox -n default apply -f -
kubectl --context kind-hivebox -n default apply -k k8s
kubectl --context kind-hivebox -n default rollout status deployment/hivebox-valkey --timeout=180s
kubectl --context kind-hivebox -n default rollout status deployment/hivebox-minio --timeout=180s
kubectl --context kind-hivebox -n default wait --for=condition=complete job/hivebox-minio-bucket --timeout=300s
$helmExe = Join-Path $env:TEMP 'hivebox-helm-3.20.2\windows-amd64\helm.exe'
& $helmExe upgrade --install hivebox charts/hivebox --kube-context kind-hivebox -n default --wait --timeout 6m
kubectl --context kind-hivebox -n default rollout status deployment/hivebox --timeout=360s
```

After rebuilding MinIO or HiveBox, reload the images and restart the affected
Deployments. Job templates are immutable: delete only the bucket Job before
reapplying a changed Job template; this does not delete the bucket or PVC.

## Verify

```powershell
kubectl --context kind-hivebox -n default get pods,svc,pvc,jobs
kubectl --context kind-hivebox -n default logs job/hivebox-minio-bucket
kubectl --context kind-hivebox -n default port-forward service/hivebox 18080:80
```

In another terminal:

```powershell
curl.exe -i http://127.0.0.1:18080/readyz
curl.exe --fail http://127.0.0.1:18080/store
```

Expected: bucket Job Complete, PVC Bound, HiveBox pod Ready, readiness 200 with
all checks true, and `/store` 200 with an object name. If blocked, inspect pod
events, container logs, the PVC, and Job logs. MinIO PVC contents, not the old
host bucket, supply this deployment's snapshots. Readiness only controls
Service routing and does not restart the process.

If Helm is installed on PATH, use `helm` instead of the temporary binary path.
On a fresh cluster the Helm command creates the application directly. For a
cluster still running the earlier plain Deployment, follow the ownership
handover in `charts/hivebox/README.md` first.
