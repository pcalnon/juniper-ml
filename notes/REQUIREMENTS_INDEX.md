# Juniper Requirements — Index

**Snapshot date**: 2026-05-12
**Plan doc**: `REQUIREMENTS_IDENTIFICATION_PLAN_2026-05-11.md`
**Schema reference**: `requirements/README.md`

---

## Totals

- **1803 requirements** across **15 of 15 area codes** and **8 of 8 owning repos**.
- **288 duplicates collapsed** during Phase-4 consolidation (raw extraction yielded 2091 candidates).
- **252** unique source files cited.

## By area

| Code | Description | Count | File |
|---|---|---|---|
| `OBS` | observability — metrics, logging, tracing, dashboards, alerting | 192 | [by-area/OBS.md](requirements/by-area/OBS.md) |
| `SEC` | security — authn, authz, secrets, CVEs, hardening | 246 | [by-area/SEC.md](requirements/by-area/SEC.md) |
| `API` | API contracts — schemas, versioning, compatibility, migrations | 153 | [by-area/API.md](requirements/by-area/API.md) |
| `DEP` | deployment-config — Docker, Compose, K8s, Helm, image build | 65 | [by-area/DEP.md](requirements/by-area/DEP.md) |
| `UI` | ui-frontend — Canopy/Dash, UX, visualizations | 114 | [by-area/UI.md](requirements/by-area/UI.md) |
| `DATA` | data-pipeline — dataset generation, NPZ contracts, ingestion | 52 | [by-area/DATA.md](requirements/by-area/DATA.md) |
| `TRAIN` | training — cascor algorithm, candidates, convergence, model state | 154 | [by-area/TRAIN.md](requirements/by-area/TRAIN.md) |
| `WS` | websocket / messaging — Canopy↔Cascor streaming, replay, control plane | 176 | [by-area/WS.md](requirements/by-area/WS.md) |
| `TEST` | testing-and-ci — pytest, fixtures, CI workflows, regression analysis | 130 | [by-area/TEST.md](requirements/by-area/TEST.md) |
| `LOCK` | lockfile-and-deps — uv lockfiles, pyproject pins, dep updates, env rebuilds | 13 | [by-area/LOCK.md](requirements/by-area/LOCK.md) |
| `ARCH` | architecture / cross-cutting design — microservices, polyrepo, interface proposals | 334 | [by-area/ARCH.md](requirements/by-area/ARCH.md) |
| `PERF` | performance / scalability — throughput, latency, parallelization, CUDA | 35 | [by-area/PERF.md](requirements/by-area/PERF.md) |
| `TOOL` | dev tooling / scripts / workflow — worktree procs, claude-code launchers | 66 | [by-area/TOOL.md](requirements/by-area/TOOL.md) |
| `DOC` | documentation / process — link validation, conventions, file headers | 53 | [by-area/DOC.md](requirements/by-area/DOC.md) |
| `OPS` | operations / runbooks / on-call — runbook documents, incident response | 20 | [by-area/OPS.md](requirements/by-area/OPS.md) |

## By owning repo

| Shortcode | Repo | Count | File |
|---|---|---|---|
| `ml` | juniper-ml | 1335 | [by-repo/ml.md](requirements/by-repo/ml.md) |
| `can` | juniper-canopy | 215 | [by-repo/can.md](requirements/by-repo/can.md) |
| `cas` | juniper-cascor | 122 | [by-repo/cas.md](requirements/by-repo/cas.md) |
| `dat` | juniper-data | 44 | [by-repo/dat.md](requirements/by-repo/dat.md) |
| `ccl` | juniper-cascor-client | 31 | [by-repo/ccl.md](requirements/by-repo/ccl.md) |
| `dep` | juniper-deploy | 29 | [by-repo/dep.md](requirements/by-repo/dep.md) |
| `cwk` | juniper-cascor-worker | 16 | [by-repo/cwk.md](requirements/by-repo/cwk.md) |
| `dcl` | juniper-data-client | 11 | [by-repo/dcl.md](requirements/by-repo/dcl.md) |

## By status

| Status | Count | File |
|---|---|---|
| `proposed` | 1444 | [by-status/proposed.md](requirements/by-status/proposed.md) |
| `designed` | 97 | [by-status/designed.md](requirements/by-status/designed.md) |
| `in-progress` | 9 | [by-status/in-progress.md](requirements/by-status/in-progress.md) |
| `shipped` | 168 | [by-status/shipped.md](requirements/by-status/shipped.md) |
| `deferred` | 39 | [by-status/deferred.md](requirements/by-status/deferred.md) |
| `rejected` | 17 | [by-status/rejected.md](requirements/by-status/rejected.md) |
| `superseded` | 29 | [by-status/superseded.md](requirements/by-status/superseded.md) |

## ID lookup

Machine-readable: [requirements/id_assignments.yaml](requirements/id_assignments.yaml) — one row per assigned ID with brief, sources, and merge history.
