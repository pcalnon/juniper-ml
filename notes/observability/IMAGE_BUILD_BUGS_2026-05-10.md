# Image Build Bugs Surfaced During Stack Verification

**Author**: Paul Calnon
**Date**: 2026-05-10
**Discovered during**: end-to-end Grafana provisioning verification (see `GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md`)
**Stack version**: `juniper-deploy@26f4ae8` (post-PR #65) with `--profile full --profile observability`

Two pre-existing image-build bugs block the `juniper-canopy` and `juniper-cascor-worker` containers from starting under the observability profile. Both are dependency-installation problems, not code bugs.

---

## Bug 1 — `juniper-canopy:latest` is stale, missing `prometheus_client`

### Symptom

Container restart-loops with:

```
File "/app/src/main.py", line 223, in <module>
    app.mount("/metrics", get_prometheus_app())
File "/app/src/observability.py", line 152, in get_prometheus_app
    from prometheus_client import make_asgi_app
ModuleNotFoundError: No module named 'prometheus_client'
```

Triggers when `CANOPY_METRICS_ENABLED=true` (set by `juniper-deploy/.env.observability`). With the default `false`, canopy starts but exports no metrics — the `juniper-canopy` Prometheus scrape target is `down` either way.

### Root cause

`juniper-canopy:latest` was built **2026-03-05**, more than two months before the current commit. The local image predates the addition of `prometheus-client` to the lockfile.

Evidence:

- `docker inspect juniper-canopy:latest --format '{{.Created}}'` → `2026-03-05T18:23:35`
- `docker run --rm --entrypoint pip juniper-canopy:latest list | grep prometheus` → empty
- `juniper-canopy/requirements.lock` *currently* contains `prometheus-client==0.25.0` (with comment `# via juniper-canopy (pyproject.toml)`)
- `juniper-canopy/pyproject.toml` declares `prometheus-client>=0.20.0` under the `observability` extra; the lockfile was compiled with `uv pip compile pyproject.toml --extra juniper-data --extra juniper-cascor --extra observability -o requirements.lock`

So the lockfile is correct and a fresh build will install `prometheus_client`. No source change is required.

### Fix

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
docker build -t juniper-canopy:latest .
# then in juniper-deploy:
docker compose --profile full --profile observability \
  --env-file .env.observability -f docker-compose.yml \
  up -d --force-recreate juniper-canopy
```

### Optional hardening

The canopy code unconditionally `from prometheus_client import make_asgi_app` at line 152 of `src/observability.py` whenever `CANOPY_METRICS_ENABLED=true`. The current declaration places `prometheus-client` under the `observability` extra, which means an install via `pip install juniper-canopy` (no extra) will leave the import broken at runtime. Two equally-valid policies:

- **Promote to required dep** — move `prometheus-client>=0.20.0` from `[project.optional-dependencies] observability` into `[project] dependencies`. Justification: the production Dockerfile installs *all* deps via the lockfile (which includes the extra), so it costs nothing in the container; removes the surprise for anyone consuming `juniper-canopy` as a library.
- **Make the import lazy + guarded** — wrap the import in a try/except inside `get_prometheus_app()` and return a 503 stub if missing. Preserves the "metrics is opt-in" framing.

I'd recommend **promote to required dep** — keeps the image build honest and matches the fact that observability is an explicit production concern, not a dev-time nicety.

---

## Bug 2 — `juniper-cascor-worker:latest` missing `juniper-cascor-protocol`

### Symptom

Both `juniper-deploy-juniper-cascor-worker-1` and `-worker-2` restart-loop with:

```
File ".../juniper_cascor_worker/constants.py", line 25, in <module>
    from juniper_cascor_protocol.worker import WorkerMessageType
ModuleNotFoundError: No module named 'juniper_cascor_protocol'
```

### Root cause

The Dockerfile installs deps from `requirements-cpu.lock`, then installs the project itself with `--no-deps`:

```dockerfile
COPY requirements-cpu.lock ./
RUN pip install --no-cache-dir -r requirements-cpu.lock
COPY pyproject.toml README.md LICENSE ./
COPY juniper_cascor_worker/ ./juniper_cascor_worker/
RUN pip install --no-cache-dir --no-deps .
```

Two lockfiles exist in the repo:

| Lockfile | Used by | Contains `juniper-cascor-protocol`? |
|---|---|---|
| `requirements.lock` | local dev | **yes** (`juniper-cascor-protocol==0.1.0`) |
| `requirements-cpu.lock` | Dockerfile | **no** — the dep is silently absent |

The CPU lockfile was generated via `uv pip compile pyproject.toml --no-emit-package torch -o requirements.lock` (per its own header), but the resulting file is missing the `juniper-cascor-protocol` entry that the parent `requirements.lock` includes. The most likely explanation: the CPU lockfile was generated against a **stale `pyproject.toml`** (before `juniper-cascor-protocol>=0.1.0` was added to `dependencies`) and never re-emitted. `pyproject.toml` clearly shows the dep was added recently — the surrounding comment block references "METRICS-MON R2.2.6 / seed-05" and "juniper-ml#168".

The image build is fresh (2026-05-10, today) so it's not a stale-image problem like Bug 1 — it's a stale-CPU-lockfile problem.

PyPI confirms `juniper-cascor-protocol==0.1.0` is published (`pip index versions juniper-cascor-protocol`), so regeneration will resolve cleanly.

### Fix

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker

# Regenerate the CPU lockfile against current pyproject.toml.
# Compile to /tmp first to avoid the uv self-pin trap (the existing
# file's pins would otherwise be picked up as constraints).
uv pip compile pyproject.toml --no-emit-package torch \
  -o /tmp/requirements-cpu.lock.new
mv /tmp/requirements-cpu.lock.new requirements-cpu.lock

# Sanity-check the regenerated lockfile contains the missing dep:
grep '^juniper-cascor-protocol' requirements-cpu.lock

# Rebuild the image:
docker build -t juniper-cascor-worker:latest .

# Recreate the worker containers:
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
docker compose --profile full --profile observability \
  --env-file .env.observability -f docker-compose.yml \
  up -d --force-recreate juniper-cascor-worker
```

### Cross-cutting follow-up

This bug is the *exact* failure mode the existing memory note **"Lockfile Freshness constraint-mode ecosystem-wide"** is designed to catch. Yet it shipped — meaning the freshness gate is either not running on `juniper-cascor-worker` or only checks `requirements.lock` and not `requirements-cpu.lock`.

Recommended follow-up:

1. Audit `juniper-cascor-worker`'s lockfile-freshness CI lane (whichever workflow currently runs `uv pip compile --constraint requirements.lock`) and extend it to also cover `requirements-cpu.lock`.
2. Add a CI assertion: every dep declared in `pyproject.toml [project] dependencies` appears in `requirements-cpu.lock`.
3. As a stop-gap until #1 lands, document in `juniper-cascor-worker/Dockerfile` (with a comment near the `COPY requirements-cpu.lock` line) that the file MUST be regenerated whenever `pyproject.toml` dependencies change.

---

## Impact on the dashboard verification

Neither bug affects the **provisioning verification result** (PR #65 in `juniper-deploy`):

- The 4 dashboard JSONs load cleanly into Grafana 12.4.0.
- The Prometheus datasource resolves and is healthy.
- `juniper-cascor` and `juniper-data` scrape targets are `up` and exporting metrics.
- Sample PromQL via the Grafana datasource proxy returns live data.

The `juniper-canopy` scrape target shows `down` only because of Bug 1, and the worker bridge is unverified only because of Bug 2. Both will go green once the rebuilds ship.

---

## Status

| Bug | Repo | Fix path | Status |
|---|---|---|---|
| Bug 1 — canopy missing `prometheus_client` | juniper-canopy | promote dep to required + rebuild | **PR pcalnon/juniper-canopy#261 open** (verified locally: container healthy, `/metrics` served) |
| Bug 2 — worker missing `juniper-cascor-protocol` | juniper-cascor-worker | regenerate `requirements-cpu.lock` + rebuild | **MERGED** as `pcalnon/juniper-cascor-worker#58` (worker container now healthy) |
| CI gap — CPU lockfile freshness check | juniper-cascor-worker | new pyproject-deps-in-lockfile assertion in `lockfile-check` job | **MERGED** with worker PR #58 |

---

## Bug 3 (newly surfaced 2026-05-10) — canopy `/metrics` is API-key gated; Prometheus scrape returns 401

After Bug 1 was fixed, the canopy container starts cleanly and `/metrics` is served — but the Prometheus scrape target stays `down` with `server returned HTTP status 401 Unauthorized`.

### Symptom

```
$ curl -sS http://127.0.0.1:8050/metrics
{"detail":"Missing API key. Provide X-API-Key header."}
```

The canopy API-key middleware applies to *all* routes including `/metrics`. The deploy stack's `juniper-deploy/prometheus/prometheus.yml` declares the `juniper-canopy` scrape job with no `authorization` / `bearer_token` / `Authorization` header injection, and the per-juniper-ml memory note "Prometheus / scrape target wiring" claims canopy `/metrics` is unauthenticated on the internal network. Reality differs from documentation.

### Two valid fixes

- **Exempt `/metrics` from API-key auth in canopy.** Cheapest. Mirrors the convention already in `juniper-data` (which carries `MetricsAuthMiddleware` ↔ IP-allowlist on `/metrics` only) and `juniper-cascor` (no auth on `/metrics`). Adds `/metrics` to the canopy auth-middleware exempt-paths set. Fits the "internal network" framing in the existing docs.
- **Wire an API key into Prometheus's scrape config.** Use `authorization` / custom header injection in `prometheus.yml` and surface the key as a Docker secret. Higher-fidelity if metrics are considered sensitive, but adds a secret-rotation surface and diverges from the data + cascor pattern.

Recommendation: **Option 1** — keep the convention of "metrics endpoints are scraper-network-private, all other auth applies". Document the choice in canopy's middleware code and update the deploy-side memory note so the scrape-wiring claim becomes accurate.

This is a separate ticket from Bugs 1 & 2; it's a code change in `juniper-canopy` (not a deploy or worker change) and doesn't block merging the canopy PR for Bug 1.
