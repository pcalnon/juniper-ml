# Juniper Build-Provenance & Stale-Image Detection — Ecosystem Design

**Project**: Juniper ML Research Platform — cross-repo build-provenance feature (design doc hosted in pcalnon/juniper-ml)
**Repository**: spans pcalnon/{juniper-observability, juniper-data, juniper-cascor, juniper-canopy, juniper-cascor-worker, juniper-deploy}
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (DRAFT — design for review; pre-implementation; **scope = Maximal, ratified 2026-06-14**)
**Last Updated**: 2026-06-14

---

> **What this document is.**
> A single, detailed design + rollout plan for giving every Juniper service **build provenance** — a git SHA and build timestamp baked into each image and surfaced at runtime — and for using it to **detect stale-image drift** automatically. It exists because the "running container is silently behind source" failure mode keeps recurring (most recently: `juniper-canopy` running `0.4.0` while source is `0.5.0`, surfaced 2026-06-14). It is grounded in a file:line inventory of the current state across six repos (Part 3) and specifies the exact change in each (Part 5).
>
> Scope **Maximal** was selected 2026-06-14 (Part 2): git SHA surfaces in `/v1/health`, in OCI image labels, in the Prometheus `*_build` Info metric (Grafana-visible), and in the shared `ReadinessResponse` model — plus a `make doctor` drift checker and a compose-args regression test.

---

> **⚠️ EXECUTION STATUS UPDATE (2026-06-17): SHIPPED.** This design is **fully implemented and live-verified** across all 6 repos — observability **0.4.0** on PyPI (`set_build_info` git_sha/build_date + `ReadinessResponse`); `ARG GIT_SHA`/`BUILD_DATE` in every service Dockerfile; per-service-SHA `make build`; `make doctor` + `scripts/doctor.sh`; the 7-service compose-args regression test. PRs: obs#414, data#180, cascor#333, canopy#360, worker#103, juniper-deploy#118/#119/#122. **OQ-4** (automated drift CI lane) was **declined** by Paul (on-demand `make doctor` suffices). The "0.1.0 (DRAFT — pre-implementation)" header is now **historical**. Current reconciled state: [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md).

## Table of contents

- **Part 1** — Problem statement & motivating evidence
- **Part 2** — Goals, non-goals, the ratified scope
- **Part 3** — Current-state inventory (file:line)
- **Part 4** — Design: the provenance mechanism
- **Part 5** — Per-repo change specification
- **Part 6** — The per-service-SHA build wrinkle
- **Part 7** — Drift detection (`make doctor` + compose test)
- **Part 8** — Rollout & PR sequencing
- **Part 9** — Risk register
- **Part 10** — Open questions
- **Appendix A** — Staleness evidence (2026-06-14)
- **Appendix B** — Decision log

---

## Part 1 — Problem statement & motivating evidence

Juniper services run from `<service>:latest` images built locally from sibling-repo checkouts. `docker compose up` / `restart` **reuse the existing `:latest` image** — they never rebuild on source change. Nothing stamps build provenance into the image, so the only freshness signal is the Docker `.Created` timestamp, which nothing checks. Images rot silently behind healthy-looking `200`s.

The `version` field in `/v1/health` is **not** a sufficient staleness signal: a service can accumulate days of commits (deps, code) without bumping its semver. Evidence from 2026-06-14 (full table in Appendix A):

| Service | Image built | Source HEAD commit | Running ver | Source ver | Verdict |
|---------|-------------|--------------------|-------------|-----------|---------|
| canopy  | 05-29       | 06-03 (#354)       | **0.4.0**   | 0.5.0     | stale (version + code) |
| cascor  | 06-03       | 06-08 (#327)       | 0.5.0       | 0.5.0     | **stale code, identical version** |
| data    | 05-29       | 06-09 (#171)       | 0.6.0       | 0.6.0     | **stale code, identical version** |
| worker  | 06-14       | 06-14              | fresh       | —         | fresh (rebuilt for CW-05) |

cascor and data prove the point: a version-equality check passes them both while they are 5–11 days behind. The reliable signal is **git SHA** (exact) or image-build-time-vs-source-commit-time (fuzzy fallback).

## Part 2 — Goals, non-goals, the ratified scope

**Goals.** (1) Every image carries its source git SHA + build date. (2) The running process reports them at `/v1/health`. (3) An operator command (`make doctor`) reports, per service, whether the running SHA matches the on-disk source HEAD. (4) A regression test prevents the build-arg wiring from being silently dropped (the exact failure class that hit the WS-origin env var, juniper-deploy #102→#103).

**Non-goals.** Auto-rebuild on `up` (too slow; multi-GB). Registry/remote image provenance (local-build stack only, for now). Signing/attestation (out of scope).

**Ratified scope — Maximal (2026-06-14).** Provenance surfaces in four places:
1. **`/v1/health` JSON** — `git_sha` + `build_date` fields (the drift checker's primary source).
2. **OCI image labels** — `org.opencontainers.image.revision` / `.created` / `.version`.
3. **Prometheus `<ns>_build` Info metric** — via `juniper_observability.set_build_info(...)`, Grafana-visible.
4. **Shared `ReadinessResponse` model** — `git_sha` on every `/v1/health/ready`.

## Part 3 — Current-state inventory (file:line)

### 3.1 juniper-observability (0.3.1, PyPI-published)
- `set_build_info(namespace: str, version: str) -> None` — `juniper_observability/prometheus.py:29-50`. Creates `<namespace>_build` Info metric with `version` + auto `python_version`.
- Delegates to `register_info_or_update(name, description, **info_labels: str)` — `prometheus_helpers.py:214-256`. **Accepts arbitrary string labels** (idempotent, overwrites). Adding `git_sha`/`build_date` is friction-free at the helper layer.
- Shared `ReadinessResponse` pydantic model — `juniper_observability/health/models.py:31-41`. Consumed by all three FastAPI services' `/v1/health/ready`.
- **No service passes git_sha/build_date today.** All callers pass `(namespace, version)` only.
- Published via `publish-observability.yml` (tag `juniper-observability-v*`); consumers pin `>=0.2.0`. ⇒ a signature change requires a release + pin bumps (Part 8).

### 3.2 Health endpoints & version source of truth
| Service | `/v1/health` | Version source | Notes |
|---------|--------------|----------------|-------|
| data    | `juniper_data/api/routes/health.py:117` | `__version__` hardcoded — `juniper_data/__init__.py:17` | uses shared `ReadinessResponse` |
| cascor  | `src/api/routes/health.py:53` | `_API_VERSION` hardcoded — `src/api/routes/health.py:35` | uses shared `ReadinessResponse` |
| canopy  | `src/main.py:832` | `APP_VERSION = importlib.metadata.version(...)` fallback `"0.5.0"` — `src/main.py:96-100` | uses shared `ReadinessResponse` |
| worker  | `juniper_cascor_worker/http_health.py:184` | `_resolve_version()` (importlib.metadata, fallback `"0.0.0+unknown"`) — `worker.py:542-556` | **hand-rolled asyncio HTTP server, NOT FastAPI**; no Prometheus metrics; does **not** use the shared model. `__init__.py:15` `__version__="0.3.0"` is stale vs pyproject `0.4.0` (masked because the probe uses importlib.metadata). |

All three FastAPI services call `set_build_info(<ns>, <ver>)` at startup: data `api/app.py:43`, cascor `src/api/app.py:164`, canopy `src/main.py:156`. The main `/v1/health` bodies are **hand-built dicts** per service (the shared model is only on `/ready`), so the `git_sha` field on `/v1/health` is a per-service edit.

### 3.3 Dockerfiles (all 4: 2-stage builder+runtime, `pip install --no-deps .`, zero `ARG` today)
| Service | LABEL block | Version label today | Runtime env-inject point |
|---------|-------------|---------------------|--------------------------|
| data    | `Dockerfile:34-39` | **hardcoded `version="0.6.0"`** | ~`:59-62` |
| cascor  | `Dockerfile:36-40` | none | ~`:64-67` |
| canopy  | `Dockerfile:39-43` | none | ~`:73-78` |
| worker  | `Dockerfile:41-45` | none | ~`:67-68` |

Code arrives via `pip install --no-deps .` — **`.git` is not in the image**, so the SHA must be injected as a build-arg → `ENV`, not read from a repo at runtime.

### 3.4 juniper-deploy
- **7 build blocks**, none with `build.args`: data `118-120`, cascor `165-167`, worker `256-258`, cascor-demo `309-311`, canopy `456-458`, canopy-demo `533-535`, canopy-dev `596-598`.
- Makefile `build` `152-153`, `build-no-cache` `155-156` (compose build across all profiles, single invocation).
- `make health` → `scripts/health_check.sh` prints a `SERVICE | STATUS | VERSION | LATENCY` table (`:62-119`) — natural home for a `GIT_SHA` + `FRESH/STALE` column.
- No `GIT_SHA`/`BUILD_DATE`/`VCS_REF` references anywhere.
- Compose-test house style: text-scrape `_extract_service_env` (`tests/test_compose_ws_origin_env_wired.py:36-66`) and **YAML-parse** (`tests/test_compose_metrics_trusted_ips_wired.py:23-50`). The provenance test should use YAML-parse (asserting `build.args` keys).

## Part 4 — Design: the provenance mechanism

Flow: **build-arg → image (label + env) → process → health/metric → drift check.**

1. **Build:** `docker build --build-arg GIT_SHA=<short-sha> --build-arg BUILD_DATE=<iso8601> …`
2. **Image (runtime stage):**
   - `ARG GIT_SHA` / `ARG BUILD_DATE` (re-declared in the runtime stage; ARGs do not cross stages).
   - `LABEL org.opencontainers.image.revision="$GIT_SHA"`, `…created="$BUILD_DATE"`, `…version="$APP_VERSION"`.
   - `ENV JUNIPER_<SVC>_GIT_SHA=$GIT_SHA` and `JUNIPER_<SVC>_BUILD_DATE=$BUILD_DATE`.
3. **Process:** a tiny provenance accessor per service reads those env vars (empty-string default when run outside Docker / unset → reported as `null`).
4. **Surface:** add `git_sha`/`build_date` to the hand-built `/v1/health`; pass them to `set_build_info(...)`; (FastAPI services) carry `git_sha` on the shared `ReadinessResponse`.
5. **Drift check:** `make doctor` compares each running `/v1/health.git_sha` to `git -C ../<svc> rev-parse --short HEAD`. Exact match → FRESH; mismatch → STALE; missing → UNKNOWN (pre-rollout image).

## Part 5 — Per-repo change specification

### 5.1 juniper-observability → release **0.4.0** (foundation, on critical path)
- Extend the wrapper, fully backward-compatible:
  `set_build_info(namespace: str, version: str, *, git_sha: str | None = None, build_date: str | None = None) -> None` (`prometheus.py:29`). When provided, pass through as extra labels on the `<ns>_build` Info metric (the helper already accepts `**info_labels`). Existing two-arg callers are unaffected.
- Add optional `git_sha: str | None = None` (and `build_date`) to `ReadinessResponse` (`health/models.py:31-41`).
- Tag `juniper-observability-v0.4.0`; publish (dual gate: wait-timer + reviewer).

### 5.2 juniper-data / juniper-cascor / juniper-canopy (one PR each; parallel after 5.1)
- **Dockerfile:** add `ARG GIT_SHA`/`ARG BUILD_DATE` (builder top + runtime re-declare); add/My-standardize the three OCI labels; add the two `ENV` vars. (data: replace its hardcoded `version="0.6.0"` with `$APP_VERSION` build-arg.)
- **App:** a `provenance.py` accessor (reads `JUNIPER_<SVC>_GIT_SHA`/`_BUILD_DATE`); add `git_sha`/`build_date` to the `/v1/health` dict; pass them into the existing `set_build_info(...)` call.
- **Pin:** bump `juniper-observability>=0.4.0` (pyproject + lockfile regen — see memory: `/tmp`+`mv` pattern, constraint-mode gate).
- **(OQ-1)** optionally migrate the hardcoded version constant → `importlib.metadata.version(...)` to kill a separate drift class in the same PR.

### 5.3 juniper-cascor-worker (one PR; parallel — no observability dependency)
- **Dockerfile:** `ARG`/`LABEL`/`ENV` as above (`JUNIPER_CASCOR_WORKER_GIT_SHA`/`_BUILD_DATE`).
- **App:** add `git_sha`/`build_date` to the hand-rolled `/v1/health` handler (`http_health.py:184`). No Prometheus / no shared model.
- **(OQ-5)** fix `__version__` `0.3.0` → `0.4.0` (pyproject parity).

### 5.4 juniper-deploy (1–2 PRs; lands last)
- **compose:** `build.args: { GIT_SHA: "${GIT_SHA:-}", BUILD_DATE: "${BUILD_DATE:-}" }` on all **7** build blocks.
- **Makefile:** `build`/`build-no-cache` rewritten to build **per service** with that repo's SHA (Part 6); shared `BUILD_DATE`.
- **test:** `tests/test_compose_build_provenance_wired.py` (YAML-parse) asserting every build block declares both args — the regression guard.
- **`make doctor`** + `scripts/health_check.sh` column (Part 7).

## Part 6 — The per-service-SHA build wrinkle

A single global `GIT_SHA` env cannot serve a one-shot multi-service `compose build` — each image must carry **its own** repo's SHA. Resolution: `make build` iterates services and builds each with its context's SHA, e.g.

```make
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
build:
	@for svc in juniper-data juniper-cascor juniper-cascor-worker juniper-canopy; do \
	  sha=$$(git -C ../$$svc rev-parse --short HEAD); \
	  GIT_SHA=$$sha BUILD_DATE=$(BUILD_DATE) $(COMPOSE) -f $(COMPOSE_FILE) build $$svc; \
	done
```

Demo/dev variants share their prod counterpart's `context:` (`../juniper-cascor`, `../juniper-canopy`) ⇒ same SHA; build them in the same loop iteration or map them to the parent context. (`BUILD_DATE` is computed once so a single `make build` yields a coherent timestamp across services.) **Known limitation:** building from a dirty working tree labels the image with `HEAD` while the code includes uncommitted changes — mitigated by appending `-dirty` when `git status --porcelain` is non-empty (OQ-2).

## Part 7 — Drift detection

**`make doctor`** (the durable answer to "recurring"): for each service, GET `/v1/health`, read `git_sha`, compare to `git -C ../<svc> rev-parse --short HEAD`. Print `SERVICE | RUNNING SHA | SOURCE HEAD | FRESH/STALE`. Also cross-check the image OCI `revision` label and `.Created` vs source commit time as a fallback when a service predates rollout (`git_sha == null` → UNKNOWN, recommend rebuild). Extend `scripts/health_check.sh`'s existing table with a `GIT_SHA`/`STALE?` column so `make health` shows it too.

**Compose regression test** (CI-safe, no siblings needed): `test_compose_build_provenance_wired.py` asserts each of the 7 build blocks declares `GIT_SHA` + `BUILD_DATE` under `build.args`. This is the guard that the wiring is never silently dropped — precisely the lesson from the WS-origin regression that opened this whole thread.

**CI note:** the *runtime* drift check needs sibling repos on disk (it's an ops/local tool; `docs-full-check.yml` already demonstrates the clone-siblings pattern if a CI lane is later wanted — OQ-4). The compose-args test needs nothing extra and runs in normal CI.

## Part 8 — Rollout & PR sequencing (dependency-ordered, upstream first)

1. **juniper-observability 0.4.0** — §5.1; release to PyPI. *(blocks the 3 FastAPI service PRs)*
2. **data, cascor, canopy** — §5.2; three independent PRs, parallel once 0.4.0 is on PyPI.
3. **worker** — §5.3; independent PR, parallel with step 2 (no observability dep).
4. **juniper-deploy** — §5.4; the compose-args + test can land anytime; `make doctor` is most useful once services expose `git_sha`, so sequence it after step 2/3 land and images are rebuildable.
5. **Rebuild + roll the stack**, then confirm `make doctor` reports all FRESH.

~6–7 PRs across 6 repos. Versioning: observability minor (0.4.0); each service patch/minor (additive). All changes are additive/backward-compatible.

## Part 9 — Risk register

| # | Risk | Mitigation |
|---|------|-----------|
| R1 | `set_build_info` signature change breaks existing callers | New params are keyword-only with `None` defaults; two-arg calls unchanged. Covered by an observability unit test. |
| R2 | Per-service SHA done wrong (one global SHA mislabels all) | Part 6 builds each service with its own context SHA; the compose test + `make doctor` would surface a uniform-SHA mistake. |
| R3 | Dirty-tree builds mislabel provenance | Append `-dirty` suffix when `git status --porcelain` non-empty (OQ-2). |
| R4 | Demo/dev variants left unlabeled | All **7** build blocks get args (§5.4), not just the 4 prod services. |
| R5 | Exposing `git_sha` on an unauthenticated `/v1/health` leaks exact revision | Low-risk: services are loopback-bound; build info on health is standard (k8s). Can gate to `/ready` or behind metrics-auth if desired (OQ-3). |
| R6 | Build-arg change doesn't pull new code (layer cache) | Source change alters the build context hash → the `pip install .` layer rebuilds; the SHA label always reflects build-time HEAD. The point is detection of "forgot to rebuild," which `make doctor` delivers. |
| R7 | Observability publish dual-gate latency on the critical path | Sequence step 1 first; the worker PR (step 3) proceeds in parallel since it has no observability dependency. |
| R8 | Lockfile-regen footguns on the pin bump | Use the documented `/tmp`+`mv` + constraint-mode pattern (ecosystem memory). |

## Part 10 — Open questions

- **OQ-1** — Migrate hardcoded version constants (data `__version__`, cascor `_API_VERSION`) to `importlib.metadata` for single-source-of-truth? *Recommend yes, in each service PR.*
- **OQ-2** — Append `-dirty` for uncommitted-tree builds? *Recommend yes (cheap, prevents false FRESH).*
- **OQ-3** — `git_sha` on `/v1/health` (public) vs `/ready`-only? *Recommend keep on `/v1/health` per Maximal scope; revisit if a service's health is ever exposed beyond loopback.*
- **OQ-4** — Add a juniper-deploy CI lane that checks out siblings and runs the runtime drift check, or keep it local-only? *Recommend local-only now + the CI-safe compose-args test; defer the CI drift lane (trigger: provenance lands in all services).*
- **OQ-5** — Fix worker `__version__` 0.3.0→0.4.0 in the worker PR? *Recommend yes.*
- **DECISION (2026-06-14)** — Scope = **Maximal** (Part 2). Ratified by Paul.

## Appendix A — Staleness evidence (2026-06-14)

| Service | Image built | Container uptime | Source HEAD commit | Running ver | Source ver |
|---------|-------------|------------------|--------------------|-------------|-----------|
| cascor-worker ×2 | 06-14 05:00 | 9h | 06-14 04:53 | fresh | 0.4.0 |
| juniper-cascor | 06-03 16:26 | 28 min | 06-08 16:28 (#327) | 0.5.0 | 0.5.0 |
| juniper-canopy | 05-29 20:03 | 13 days | 06-03 16:36 (#354) | **0.4.0** | 0.5.0 |
| juniper-data | 05-29 17:06 | 13 days | 06-09 13:54 (#171) | 0.6.0 | 0.6.0 |

No image carries a git-SHA or build-date label today; only static OCI metadata exists, and data hardcodes its version label. The only freshness signal available is the Docker `.Created` timestamp.

## Appendix B — Decision log

- **2026-06-14** — Stale-image gotcha investigated after `juniper-canopy` was found running 0.4.0 vs source 0.5.0 (while diagnosing two juniper-deploy test failures). Confirmed version-equality is an insufficient signal (cascor/data are code-stale at matching versions). Scope options Core / Core+Grafana / Maximal presented; **Maximal selected**. This document written as the design of record; implementation PRs (Part 8) to open after design review.
