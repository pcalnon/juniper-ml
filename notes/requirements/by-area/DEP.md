# Requirements — DEP

**Area**: deployment-config — Docker, Compose, K8s, Helm, image build

**Total entries**: 61

**By status**: proposed=52 | designed=3 | shipped=5 | deferred=1

**By priority**: P0=6 | P1=16 | P2=31 | P3=8

**By owner**: ml=46 | dep=6 | can=6 | dat=1 | cwk=1 | cas=1

---

### JR-ML-DEP-001 — 3.4 LIFT-01 — R5.4 alert log-only-severity gate lift.

**Status**: shipped  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 156-182)

**Detail**:

**Severity:** P1 · **Owner repo:** juniper-deploy · **Status:** blocked (gated on CALIB-01 + OBS-ROUTE-CRED)

### JR-ML-DEP-002 — 2.2 Per-Client/Worker Inventory.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 127-152)

**Detail**:

- **Type**: Pure HTTP client library

### JR-ML-DEP-003 — 3.2 Alertmanager `tickets` receiver placeholder.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 97-126)

**Detail**:

- **Status**: open — operational gap

### JR-ML-DEP-004 — 9.1 Completed Phases.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 280-289)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 216-225)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DEP-005 — Aggregate Results.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 14-28)

**Detail**:

| juniper-ml            | 0.3.0   | 88 pass          | N/A (meta) | 16/16 pass   | 1        | 4      | 3      | 8      |

### JR-ML-DEP-006 — Rollback Plan.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 394-412)

**Detail**:

- All git tags can be deleted and recreated: `git tag -d v<VERSION> && git push --delete origin v<VERSION>`

### JR-DAT-DEP-001 — Dockerfile implements multi-stage build, python:3.11-slim, non-root UID 1000, port 8100, HEALTHCHECK.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 154-181)

**Notes**:

DATA-006 complete. .dockerignore excludes development artifacts.

### JR-ML-DEP-007 — Release juniper-ml v0.4.1 + juniper-observability v0.1.1a: document release steps, validation, tag/publish.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md` (lines 1-50)

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

### JR-ML-DEP-008 — 9.8 Detailed Design: Worker Dockerfile.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 669-689)

**Detail**:

FROM python:3.14-slim AS builder

### JR-ML-DEP-009 — 9.9 Detailed Design: Worker in Docker Compose.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 689-714)

**Detail**:

context: ../juniper-cascor-worker

### JR-ML-DEP-010 — 9.3 Microservices Architecture Roadmap (Phases 5–9).

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 299-315)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 235-251)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-DEP-DEP-001 — Add juniper-cascor-worker service to docker-compose.yml under full profile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 154-180)

**Detail**:

Phase 3 (v0.4.0) worker integration. Add juniper-cascor-worker service with build context
../juniper-cascor-worker, environment variables (CASCOR_SERVICE_URL, WORKER_ID, WORKER_LOG_LEVEL).
Attach to backend bridge network (same as cascor). Add depends_on: juniper-cascor: condition: service_healthy.
Define health check endpoint or process check. Add deploy.replicas for horizontal scaling (default 1).
Add WORKER_REPLICAS env var for override. Document scaling in README.

### JR-DEP-DEP-002 — Add juniper.target and per-service systemd unit files with dependency ordering.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 89-165)

**Detail**:

juniper.target groups all services. juniper-data.service runs first (MemoryMax=2G, CPUQuota=200%).
juniper-cascor.service depends on data (MemoryMax=8G, CPUQuota=400%). juniper-canopy.service
wants cascor softly (falls back to demo mode). All use ExecStartPost wait_for_health.sh gate.
Security hardening: NoNewPrivileges=true, ProtectSystem=strict, ProtectHome=read-only.

### JR-DEP-DEP-003 — Define production Docker Compose profile with resource limits, restart policies, log rotation.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 121-152)

**Detail**:

Phase 2 (v0.3.0) production readiness. Add --profile production to docker-compose.yml
or docker-compose.production.yml override. Per-service resource limits (deploy.resources.limits
for CPU and memory), restart policies (restart: always with deploy.restart_policy),
log rotation (Docker logging driver options max-size, max-file).

### JR-CAN-DEP-001 — Docker dependencies must be pinned via lockfile, not floating versions.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 128-128)

**Detail**:

Issue 2.3.2: Dockerfile uses floating versions (python:3.11, etc). Pin via
Dockerfile ARG or multi-stage from pinned base images.

### JR-CAN-DEP-002 — Docker log file handler must use append mode, not write mode.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 130-130)

**Detail**:

Issue 2.3.4: Log file handler configured with 'w' (write) instead of 'a'
(append). Causes log truncation on app restart. Use 'a' mode.

### JR-CAN-DEP-003 — Docker must have production configuration or documented env var overrides.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.1: Dockerfile currently dev-centric. Create Dockerfile.prod or
document production override env vars (API_BASE, CASCOR_HOST, etc).

### JR-CAN-DEP-004 — Docker service URLs must have correct defaults for health checks.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.3: HEALTHCHECK instruction uses http://localhost:8000/health
but app may be configured differently. Use env vars or expose-port-agnostic probe.

### JR-ML-DEP-011 — Fix image build bugs: observability images not inheriting base image labels correctly.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/IMAGE_BUILD_BUGS_2026-05-10.md` (lines 1-50)

### JR-ML-DEP-012 — juniper-deploy P0: define SECRETS_DIR and SECRETS_FILES variables in Makefile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md` (lines 47-60)

### JR-ML-DEP-013 — Release readiness checklist: pre-commit compliance, test pass, version sync across 6 applications.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 1-50)

### JR-ML-DEP-014 — 2.1 Current State.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 97-116)

**Detail**:

There is no unified multi-service startup mechanism. Each service is started independently:

### JR-ML-DEP-015 — 2.1 juniper-cascor bind address.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 20-26)

**Detail**:

**Decision**: Bind to `127.0.0.1:8200` (settings default).

### JR-ML-DEP-016 — 2.2 juniper-data: Code Fixes.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 171-188)

**Detail**:

**2.2.1 n_spirals fallback** (`datasets.py:114`):

### JR-ML-DEP-017 — 3.1 CALIB-01 — T+30d SLO target calibration.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 62-97)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

### JR-ML-DEP-018 — 3.4 Port Mapping Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 409-420)

**Detail**:

**Repositories**: juniper-cascor, juniper-deploy

### JR-ML-DEP-019 — 3.5 Recommendation.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 575-604)

**Detail**:

**Recommended approach: Phased adoption combining Options 1, 3, and 5.**

### JR-ML-DEP-020 — 4.2 Discovery Approach Evaluation.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 616-627)

**Detail**:

**Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle discovery automatically when contai

### JR-ML-DEP-021 — 5.1 Current State.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 360-364)

### JR-ML-DEP-022 — 5.3 Post-Release.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 375-386)

**Detail**:

- Update parent CLAUDE.md with new version numbers

### JR-ML-DEP-023 — 6.5 Low: Version Header Drift (Multiple Repos).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 353-363)

**Detail**:

| Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |

### JR-ML-DEP-024 — 7.2 Port Assignments.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 424-434)

**Detail**:

**Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts hardcode 8201. Documentati

### JR-ML-DEP-025 — 9.1 Approach A: Incremental Fix (Recommended).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 504-529)

**Detail**:

Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add missing systemd units and worker deployment config.

### JR-ML-DEP-026 — A.2 Container/Deploy Files.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 831-846)

**Detail**:

| `docker-compose.yml`                  | juniper-deploy | Primary orchestration | Active     |

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-DEP-DEP-005 — Docker Python 3.14 migration plan for juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/history/DOCKER_PYTHON_314_MIGRATION_PLAN.md` (lines 1-50)

### JR-CAN-DEP-005 — Hardcoded localhost:8050 URLs in MetricsPanel; breaks in Docker/reverse-proxy/non-standard host (ISS-10).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 515-538)

**Detail**:

ISS-10 MODERATE. Multiple metrics_panel.py locations use hardcoded http://localhost:8050 URLs: line 1000 (/api/network/stats), line 1021 (/api/state), line 1155-1231 (metrics layout endpoints), line 1274 (layout delete). No dynamic URL construction method (_api_url()) exists in file — all hardcoded. When canopy runs in Docker, behind reverse proxy, or non-standard host/port, requests fail silently with ConnectionError. Affected panels (network stats, training state, metrics layout management) return fallback/empty data or fail to persist customizations.

**Notes**:

Identified by v4. Validation found 4 additional hardcoded localhost URLs beyond initial 2 identified.

### JR-DEP-DEP-006 — Implement native systemd user-unit deployment mode alongside Docker Compose.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 1-30)

**Detail**:

Phase 2 systemd implementation provides zero containerization overhead, direct GPU/CUDA access,
dependency ordering via systemd After=/Requires=, health monitoring via timer-triggered one-shot
services, per-service resource accounting via cgroups v2, and security hardening.
Coexists with Docker Compose deployment. Both methods manage the same 3 core services
(juniper-data, juniper-cascor, juniper-canopy) with independent conda environments.

**Design**:

File layout: systemd/user/*.service (10 unit files), systemd/install.sh, scripts/wait_for_health.sh,
scripts/health_check_systemd.sh, conf/juniper.env.example, scripts/juniper-ctl CLI wrapper.
Tasks 2.1–2.14 define complete implementation with resource limits, health checks, and lifecycle validation.

### JR-ML-DEP-027 — Near-Term (Docker Compose Adoption).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 727-735)

**Detail**:

1. **Create ecosystem-level `docker-compose.yml`**: Define all 3 services + Redis with health-gated dependency ordering. Place at `Juniper/docker-compose.yml` (or `Juniper/juniper/docker-compose.yml`).

### JR-ML-DEP-028 — Phase 1:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 198-398)

### JR-ML-DEP-029 — Phase 2:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 451-651)

### JR-ML-DEP-030 — Phase 2: systemd & Service Management — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 243-258)

**Detail**:

| 2.1  | `juniper-data.service` systemd unit                          | ❌ Not in juniper-deploy scripts/ (may be in individual repos) |

### JR-ML-DEP-031 — Phase 3:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1040-1240)

### JR-ML-DEP-032 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

### JR-ML-DEP-033 — Phase 5:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

### JR-ML-DEP-034 — Phase 6:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2870-3070)

### JR-ML-DEP-035 — Phase 7:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 3294-3494)

### JR-ML-DEP-036 — Phase 8:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 3783-3983)

### JR-ML-DEP-037 — Phase 9:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 4251-4451)

### JR-ML-DEP-038 — Release Order Risks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 386-394)

### JR-ML-DEP-039 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 156-169)

**Detail**:

1. Synchronize all version references to target release (0.6.0 recommended given post-0.5.0 features)

### JR-ML-DEP-040 — Tally by severity.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 412-421)

### JR-ML-DEP-041 — 3.8 R1.3.4-FLAG — Helm chart `worker.healthcheck.enabled` default flip.

**Status**: shipped  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 243-264)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** deferred

### JR-ML-DEP-042 — Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term ✅ COMPLETED.

**Status**: designed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 754-785)

**Detail**:

**Goal**: Enable containerized deployment of the distributed worker.

### JR-ML-DEP-043 — 9.4 Recommended Approach.

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 591-603)

**Detail**:

**Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

### JR-ML-DEP-044 — 2.4 Recommendation.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 299-328)

**Detail**:

**Recommended approach: Layered strategy with Docker Compose as the primary orchestrator.**

### JR-CAN-DEP-006 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

### JR-ML-DEP-045 — Phase 4: Kubernetes Helm Chart — ✅ COMPLETE.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 270-285)

**Detail**:

| 4.1  | Chart scaffolding (`Chart.yaml`, `_helpers.tpl`) | ✅ Implemented |

### JR-ML-DEP-046 — Phase 4: Kubernetes Support (P2) -- DONE.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 785-804)

**Detail**:

**Goal**: Enable k8s deployment of the full stack.

### JR-CAS-DEP-001 — Validate docker-compose configuration for 3-service deployment end-to-end.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 594-603)

**Detail**:

docker-compose config for 3-service deployment not tested end-to-end.

