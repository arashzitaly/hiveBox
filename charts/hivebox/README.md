# HiveBox Helm chart

Phase 5 packages the application Deployment and ClusterIP Service. Valkey,
MinIO, the PVC, bucket initialization, and credentials Secret remain external
prerequisites managed separately. No credentials are included in chart values.
The chart uses the existing non-root security settings, `/version` liveness,
and `/readyz` readiness. Resource names and selectors follow the release name.

## Values

Edit `values.yaml` or pass `--set` overrides:

| Value | Default | Purpose |
| --- | --- | --- |
| `replicaCount` | `1` | Application replicas |
| `image.repository` / `image.tag` | `hivebox` / `phase5-local` | Locally built Phase 5 image |
| `service.port` | `80` | Service HTTP port; application listens on 8080 |
| `senseboxIds` | Three study IDs | Configured sensor boxes |
| `valkey.host` / `valkey.port` | `hivebox-valkey` / `6379` | Cache Service |
| `minio.endpoint` | `hivebox-minio:9000` | Storage API Service, using HTTP |
| `minio.existingSecret` | `hivebox-minio-credentials` | Existing Secret in the release namespace |
| `minio.accessKeyField` / `minio.secretKeyField` | `access-key` / `secret-key` | Secret keys |

Probe timings and resource requests/limits are configurable too. The bucket
name remains `hivebox` in application code. Each application replica runs its
own background loops and counters; keep one replica for the current exercise.
Registry deployment requires a published Phase 5 image and image value overrides.
The chart does not package the old image `v0.0.6`, which lacks this phase's code.

## Validate

Use Helm from PATH, or the checksum-verified portable binary downloaded for
this session:

```powershell
$helmExe = Join-Path $env:TEMP 'hivebox-helm-3.20.2\windows-amd64\helm.exe'
& $helmExe lint charts/hivebox --strict
& $helmExe template hivebox charts/hivebox
```

The portable binary is temporary and does not modify PATH. For a permanent
installation, follow https://helm.sh/docs/intro/install/.

## Install on the existing KIND stack

The `hivebox:phase5-local` image must be loaded into KIND. The dependency
Services, credentials Secret, and `hivebox` bucket must exist in `default`.
Check them before installing:

```powershell
kubectl --context kind-hivebox -n default get deployment/hivebox service/hivebox
kubectl --context kind-hivebox -n default get deployment/hivebox-minio deployment/hivebox-valkey pvc/hivebox-minio-data job/hivebox-minio-bucket
& $helmExe list --kube-context kind-hivebox -n default
```

For an older stack whose Deployment and Service were created with Kustomize,
hand over only those two objects before the first Helm install. Skip the
ownership commands if release `hivebox` already owns them, or on a fresh cluster
where they do not exist. Install/upgrade the chart with the same name/namespace:

```powershell
kubectl --context kind-hivebox -n default label deployment/hivebox service/hivebox app.kubernetes.io/managed-by=Helm --overwrite
kubectl --context kind-hivebox -n default annotate deployment/hivebox service/hivebox meta.helm.sh/release-name=hivebox meta.helm.sh/release-namespace=default --overwrite
& $helmExe upgrade --install hivebox charts/hivebox --kube-context kind-hivebox -n default --wait --timeout 6m
```

Do not overwrite ownership if inspection shows another Helm release already
owns the objects. After handover, use Helm for the application. The active
`k8s/kustomization.yaml` excludes the application Deployment and Service, so
`kubectl apply -k k8s` now manages only infrastructure and the bucket Job.
Do not apply the historical standalone `k8s/deployment.yaml` or `k8s/service.yaml`.
On a fresh cluster, follow `k8s/README.md` to bootstrap the dependencies and
bucket, then install the chart directly without ownership annotations.

## Verify and recover

```powershell
& $helmExe status hivebox --kube-context kind-hivebox -n default
kubectl --context kind-hivebox -n default rollout status deployment/hivebox --timeout=360s
kubectl --context kind-hivebox -n default port-forward service/hivebox 18080:80
```

In another terminal, check `/readyz` and `/store` on `http://127.0.0.1:18080`.
Both should return 200. Keep only one port-forward using 18080.

For subsequent upgrades, inspect `helm history hivebox` and use `helm rollback`
with the explicit known-good revision if needed, passing the same namespace
and Kubernetes context. The first install has no earlier Helm revision.
`helm uninstall` removes application resources, not the external Secret,
Valkey, MinIO, bucket, or PVC.

Linting and default/override rendering are verified. Live Helm installation
and endpoint checks after ownership handover remain unverified.
