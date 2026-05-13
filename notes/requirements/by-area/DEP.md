# Requirements — DEP

**Area**: deployment-config — Docker, Compose, K8s, Helm, image build

**Total entries**: 21

**By status**: proposed=19 | shipped=2

**By priority**: P1=9 | P2=11 | P3=1

**By owner**: ml=9 | dep=5 | can=5 | dat=1 | cwk=1

---

### JR-DAT-DEP-001 — Dockerfile implements multi-stage build, python:3.11-slim, non-root UID 1000, port 8100, HEALTHCHECK.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 154-181)

**Notes**:

DATA-006 complete. .dockerignore excludes development artifacts.

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

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

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-DEP-DEP-005 — Implement native systemd user-unit deployment mode alongside Docker Compose.

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

### JR-ML-DEP-001 — Phase 1:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 198-398)

### JR-ML-DEP-002 — Phase 2:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 451-651)

### JR-ML-DEP-003 — Phase 3:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1040-1240)

### JR-ML-DEP-004 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

### JR-ML-DEP-005 — Phase 5:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

### JR-ML-DEP-006 — Phase 6:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2870-3070)

### JR-ML-DEP-007 — Phase 7:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 3294-3494)

### JR-ML-DEP-008 — Phase 8:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 3783-3983)

### JR-ML-DEP-009 — Phase 9:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 4251-4451)

### JR-CAN-DEP-005 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

