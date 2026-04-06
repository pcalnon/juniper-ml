# Phase 4: Kubernetes Helm Chart Implementation Plan

**Date**: 2026-04-06
**Phase**: 4 of 5 (Kubernetes Support, P2)
**Target Repo**: juniper-deploy
**Branch**: `feature/phase4-kubernetes`

---

## Context

The Juniper ML platform runs 4 application services (juniper-data, juniper-cascor, juniper-canopy, juniper-cascor-worker) plus infrastructure (Redis, Prometheus, Grafana). Phases 1-3 established Docker Compose orchestration with systemd support. Phase 4 adds Kubernetes deployment via a Helm chart in `juniper-deploy/k8s/helm/juniper/`.

The chart faithfully translates the existing Docker Compose architecture: 4 Docker networks become NetworkPolicies, Docker secrets become Kubernetes Secrets with the existing `_FILE` env var pattern, named volumes become PVCs, Docker health checks become liveness/readiness probes, and worker replicas become an HPA.

---

## Pre-work

1. **Clean up Phase 3 worktrees** -- both PRs (#22 juniper-cascor-worker, #26 juniper-deploy) are merged; remove stale worktrees and prune branches
2. **Create Phase 4 worktree** in juniper-deploy: `feature/phase4-kubernetes` from latest main

---

## Directory Structure

```bash
juniper-deploy/k8s/helm/juniper/
├── Chart.yaml                          # Helm v2, subchart deps (redis, cassandra, kube-prometheus-stack)
├── values.yaml                         # All configuration defaults
├── values-production.yaml              # Production overlay (JSON logs, metrics, TLS)
├── values-demo.yaml                    # Demo overlay (auto-start training)
├── .helmignore
├── templates/
│   ├── _helpers.tpl                    # Naming, labels, service URL helpers
│   ├── NOTES.txt                       # Post-install instructions
│   ├── secret.yaml                     # Single Secret (7 keys), gated on secrets.create
│   │
│   ├── data-deployment.yaml            # juniper-data Deployment
│   ├── data-service.yaml               # ClusterIP :8100
│   ├── data-pvc.yaml                   # datasets volume (5Gi)
│   ├── data-servicemonitor.yaml        # Prometheus ServiceMonitor (conditional)
│   │
│   ├── cascor-deployment.yaml          # juniper-cascor Deployment + wait-for-data initContainer
│   ├── cascor-service.yaml             # ClusterIP :8200
│   ├── cascor-pvc-snapshots.yaml       # snapshots volume (10Gi)
│   ├── cascor-pvc-logs.yaml            # logs volume (2Gi)
│   ├── cascor-servicemonitor.yaml      # Prometheus ServiceMonitor (conditional)
│   │
│   ├── canopy-deployment.yaml          # juniper-canopy Deployment + wait-for-data/cascor initContainers
│   ├── canopy-service.yaml             # ClusterIP :8050 (or LoadBalancer via values)
│   ├── canopy-servicemonitor.yaml      # Prometheus ServiceMonitor (conditional)
│   │
│   ├── worker-deployment.yaml          # juniper-cascor-worker + wait-for-cascor initContainer
│   ├── worker-hpa.yaml                 # HorizontalPodAutoscaler (autoscaling/v2, CPU-based)
│   │
│   ├── ingress.yaml                    # canopy (+ optional cascor) Ingress
│   │
│   ├── networkpolicy-deny-all.yaml     # Default deny + DNS egress for juniper pods
│   ├── networkpolicy-data.yaml         # Ingress from cascor, canopy, prometheus
│   ├── networkpolicy-cascor.yaml       # Ingress from canopy, worker; egress to data
│   ├── networkpolicy-canopy.yaml       # Ingress from all (ingress controller); egress to data, cascor, redis
│   ├── networkpolicy-worker.yaml       # No ingress; egress to cascor only
│   │
│   └── tests/
│       └── test-connection.yaml        # helm test pod: health endpoint checks
│
└── charts/                             # Subchart archives (gitignored, built from Chart.lock)
```

**Total**: ~27 template files + Chart.yaml + values files + .helmignore

---

## Key Design Decisions

### 1. Secrets Management

- **Single Kubernetes Secret** with 7 keys, mounted per-service at `/etc/juniper/secrets/` (read-only)
- **Preserves existing `_FILE` env var pattern** from Docker Compose (e.g., `JUNIPER_DATA_API_KEYS_FILE=/etc/juniper/secrets/juniper_data_api_keys`)
- Each Deployment mounts only the Secret keys it needs via `secret.items` projections
- `secrets.create: true` (chart creates Secret) or `secrets.existingSecret: "name"` (external, e.g., Vault/Sealed Secrets)
- Worker's `CASCOR_AUTH_TOKEN` uses `secretKeyRef` directly (not file-based, matches worker CLI interface)

**Secret keys**:

| Key                       | Used By                              |
|---------------------------|--------------------------------------|
| `juniper_data_api_keys`   | data, cascor                         |
| `juniper_cascor_api_keys` | cascor, canopy                       |
| `canopy_api_key`          | canopy                               |
| `cascor_sentry_dsn`       | cascor                               |
| `grafana_admin_password`  | grafana (subchart)                   |
| `juniper_data_api_key`    | cascor (credential for calling data) |
| `cascor_auth_token`       | worker (WebSocket auth)              |

### 2. Worker Health Probes

- Worker has **no HTTP endpoint** -- uses `exec: ["kill", "-0", "1"]` for both liveness and readiness
- PID 1 is the worker entrypoint process (UID 1000), so `kill -0` succeeds if the process is alive
- Matches the Docker Compose `kill -0 1` health check pattern from Phase 3

### 3. Dependency Ordering

Docker Compose `depends_on: service_healthy` is replaced by **initContainers** polling upstream health endpoints:

| Service               | initContainers                                                   |
|-----------------------|------------------------------------------------------------------|
| juniper-data          | None (no upstream deps)                                          |
| juniper-cascor        | `wait-for-data`: polls `http://<data>:8100/v1/health`            |
| juniper-canopy        | `wait-for-data` + `wait-for-cascor`: polls both health endpoints |
| juniper-cascor-worker | `wait-for-cascor`: polls `http://<cascor>:8200/v1/health`        |

Uses `busybox:1.37` with `wget` for minimal image footprint.

### 4. Security Context (All Pods)

Matching Docker Compose hardening:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
containerSecurityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
```

- `emptyDir` mounted at `/tmp` for Python temp files (required by `readOnlyRootFilesystem`)
- `PYTHONDONTWRITEBYTECODE=1` env var to avoid `.pyc` write failures

### 5. NetworkPolicies

Translates Docker Compose's 4 network topology into explicit per-pod allowlists:

| Policy   | Ingress From               | Egress To                |
|----------|----------------------------|--------------------------|
| deny-all | None                       | DNS only (UDP/TCP 53)    |
| data     | cascor, canopy, prometheus | DNS                      |
| cascor   | canopy, worker, prometheus | data, DNS                |
| canopy   | all (ingress controller)   | data, cascor, redis, DNS |
| worker   | none                       | cascor, DNS              |

All gated on `networkPolicies.enabled` (default: true).

### 6. HPA (Worker Auto-scaling)

- `autoscaling/v2` API (stable since k8s 1.26+)
- CPU-based scaling: 70% target utilization
- Default: 2 min, 8 max replicas
- When HPA enabled, Deployment omits `spec.replicas` to avoid conflict
- Memory-based scaling available but commented out (CPU better reflects training load)

### 7. Subchart Dependencies

Declared in `Chart.yaml` with `condition:` toggles:

| Subchart              | Repository                                           | Condition                       | Default |
|-----------------------|------------------------------------------------------|---------------------------------|---------|
| redis (Bitnami)       | `oci://registry-1.docker.io/bitnamicharts`           | `redis.enabled`                 | true    |
| cassandra (Bitnami)   | `oci://registry-1.docker.io/bitnamicharts`           | `cassandra.enabled`             | false   |
| kube-prometheus-stack | `https://prometheus-community.github.io/helm-charts` | `kube-prometheus-stack.enabled` | false   |

Redis: standalone mode, no auth, no persistence (session/cache only -- matches Docker Compose).

### 8. Ingress

- Single Ingress resource for canopy (public dashboard) + optional cascor API
- juniper-data is **never** exposed via Ingress (internal only)
- Supports `ingressClassName`, annotations, TLS configuration via values

---

## values.yaml Structure

```bash
global:
  imageRegistry             # Override all image registries
  imagePullSecrets          # Pull secrets for private registries
  storageClass              # Default PVC storage class

data:
  enabled, replicaCount, image.{repository,tag,pullPolicy}
  service.{type,port}
  env.*                     # JUNIPER_DATA_HOST, _PORT, _LOG_LEVEL, etc.
  persistence.datasets.{enabled,size,storageClass,accessMode}
  resources.{requests,limits}
  healthcheck.{liveness,readiness}.{path,initialDelaySeconds,periodSeconds,...}
  nodeSelector, tolerations, affinity, podAnnotations

cascor:
  (same structure as data, plus:)
  ingress.{enabled,className,annotations,hosts,tls}
  persistence.{snapshots,logs}.*

canopy:
  (same structure as data, plus:)
  ingress.{enabled,className,annotations,hosts,tls}

worker:
  enabled, replicaCount, image.*, env.*
  autoscaling.{enabled,minReplicas,maxReplicas,targetCPUUtilizationPercentage}
  resources.*

secrets:
  create                    # true = chart creates Secret, false = use existingSecret
  existingSecret            # Name of pre-existing Secret
  data.*                    # 7 secret key values

securityContext.*           # Shared pod-level security defaults
networkPolicies.enabled     # Toggle all NetworkPolicies
serviceMonitor.{enabled,interval,scrapeTimeout,labels}

redis.*                     # Bitnami Redis subchart overrides
cassandra.*                 # Bitnami Cassandra subchart overrides
kube-prometheus-stack.*     # Prometheus Operator subchart overrides
```

---

## Implementation Sequence

### Step 1: Scaffolding

- `Chart.yaml` (metadata, no dependencies yet)
- `_helpers.tpl` (all naming, label, selector, URL helpers)
- `.helmignore`

### Step 2: Core Services

- `secret.yaml`
- `data-deployment.yaml` + `data-service.yaml` + `data-pvc.yaml`
- `cascor-deployment.yaml` + `cascor-service.yaml` + `cascor-pvc-snapshots.yaml` + `cascor-pvc-logs.yaml`
- `canopy-deployment.yaml` + `canopy-service.yaml`
- `worker-deployment.yaml` + `worker-hpa.yaml`

### Step 3: Networking and Observability

- `ingress.yaml`
- All 5 NetworkPolicy files
- 3 ServiceMonitor files

### Step 4: Configuration and Validation

- `values.yaml` (complete with all defaults)
- `values-production.yaml` + `values-demo.yaml`
- `NOTES.txt` + `tests/test-connection.yaml`
- Add subchart dependencies to `Chart.yaml`
- Run `helm lint` and `helm template` to validate

---

## Critical Source Files

| File                                       | Purpose                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------|
| `juniper-deploy/docker-compose.yml`        | Authoritative service definitions, env vars, secrets, networks, volumes |
| `juniper-deploy/AGENTS.md`                 | Complete env var reference, secret mappings, network isolation docs     |
| `juniper-deploy/.env.example`              | Default environment variable values                                     |
| `juniper-deploy/prometheus/prometheus.yml` | Scrape config to mirror in ServiceMonitors                              |
| `juniper-deploy/secrets.example/`          | Secret file templates                                                   |

---

## Verification

```bash
# Lint the chart (no cluster required)
helm lint k8s/helm/juniper/

# Template render (no cluster required)
helm template test-release k8s/helm/juniper/

# Template with production values
helm template test-release k8s/helm/juniper/ -f k8s/helm/juniper/values-production.yaml

# Verify all resource types render
helm template test-release k8s/helm/juniper/ | grep "^kind:" | sort | uniq -c

# Dry-run install (requires cluster)
helm install --dry-run --debug test-release k8s/helm/juniper/
```

---

## Known Considerations

1. **readOnlyRootFilesystem + Python**: Every deployment mounts `emptyDir` at `/tmp` and sets `PYTHONDONTWRITEBYTECODE=1`
2. **initContainer images**: `busybox:1.37` must be pullable; overridable in values for air-gapped environments
3. **Redis URL**: Bitnami subchart creates `<release>-redis-master` service; the `juniper.redis.url` helper accounts for this
4. **kube-prometheus-stack CRDs**: May conflict if CRDs already exist in cluster; subchart's `crds.enabled` is exposed in values
5. **Worker PID namespace**: `shareProcessNamespace` is NOT set, so PID 1 is always the worker process and `kill -0 1` is reliable
6. **Offline rendering**: All templates avoid server-side lookups to ensure `helm template` works without a cluster
