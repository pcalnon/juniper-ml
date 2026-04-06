# Juniper Microservices Startup/Shutdown Code Review

**Date**: 2026-04-06
**Author**: Claude Code (Principal Engineer Review)
**Scope**: All application startup, shutdown, and orchestration across the Juniper ecosystem
**Version**: 1.0.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Inventory of Startup/Shutdown Mechanisms](#2-inventory-of-startupshutdown-mechanisms)
3. [Service-Mode Analysis (Host-Level)](#3-service-mode-analysis-host-level)
4. [Container-Mode Analysis (Docker Compose)](#4-container-mode-analysis-docker-compose)
5. [Kubernetes Analysis](#5-kubernetes-analysis)
6. [Client & Worker Analysis](#6-client--worker-analysis)
7. [Cross-Cutting Concerns](#7-cross-cutting-concerns)
8. [Gap Analysis Summary](#8-gap-analysis-summary)
9. [Development & Tooling Recommendations](#9-development--tooling-recommendations)
10. [Development Roadmap](#10-development-roadmap)
11. [Appendix: File Inventory](#appendix-file-inventory)

---

## 1. Executive Summary

The Juniper project operates three core microservices (juniper-data, juniper-cascor, juniper-canopy) across three operating modes:

| Mode | Mechanism | Maturity | Gaps |
|------|-----------|----------|------|
| **Host-level services** | Bash scripts + nohup + PID files | Functional but fragile | No health checks, no error handling, hardcoded paths |
| **Docker Compose containers** | juniper-deploy profiles (full/demo/dev/test/observability) | Production-ready | No k8s, alerting receivers unconfigured |
| **Kubernetes** | None | Not implemented | Complete gap |

Additionally, one distributed worker (juniper-cascor-worker) has CLI-based startup but no container or service management configuration.

### Key Findings

1. **Host-mode startup (`juniper_plant_all.bash`)** uses fixed sleep delays instead of health checks, has no error handling, and hardcodes all paths to a single developer workstation.
2. **Host-mode shutdown (`juniper_chop_all.bash`)** uses fragile PID-file + grep-based worker detection, exits on missing workers (which are optional), and has no SIGKILL fallback.
3. **Docker Compose (juniper-deploy)** is well-architected with 5 profiles, health-check-based dependency ordering, secrets management, and observability integration.
4. **systemd integration** exists only for juniper-canopy (a service file + `juniper-ctl` CLI). No systemd units exist for juniper-data or juniper-cascor.
5. **Kubernetes support** does not exist anywhere in the ecosystem.
6. **juniper-cascor-worker** is the only client with startup/shutdown logic but lacks any deployment configuration (no Dockerfile, no systemd, no k8s).

---

## 2. Inventory of Startup/Shutdown Mechanisms

### 2.1 Per-Application Inventory

#### juniper-data (Dataset Generation Service)

| Mechanism | File | Status |
|-----------|------|--------|
| Python entry point | `juniper_data/__main__.py` | Active |
| Application factory + lifespan | `juniper_data/api/app.py` | Active |
| Settings (env vars) | `juniper_data/api/settings.py` | Active |
| Health endpoints | `juniper_data/api/routes/health.py` (`/v1/health`, `/v1/health/live`, `/v1/health/ready`) | Active |
| Dockerfile (multi-stage) | `Dockerfile` | Active |
| systemd unit | -- | **Missing** |
| Startup convenience script | -- | **Missing** (uses `python -m juniper_data`) |
| Shutdown script | -- | **Missing** (relies on SIGTERM) |

#### juniper-cascor (Neural Network Training Service)

| Mechanism | File | Status |
|-----------|------|--------|
| Server entry point | `src/server.py` | Active |
| CLI training entry | `src/main.py` | Active |
| Application factory + lifespan | `src/api/app.py` | Active |
| Settings (env vars) | `src/api/settings.py` | Active |
| Health endpoints | `src/api/routes/health.py` (`/v1/health`, `/v1/health/live`, `/v1/health/ready`) | Active |
| Dockerfile (multi-stage) | `Dockerfile` | Active |
| Launch script | `util/launch_cascor.bash` | Active |
| Companion service launcher | `src/api/service_launcher.py` | Active |
| Docker Compose (deprecated) | `conf/docker-compose.yaml` | Deprecated |
| systemd unit | -- | **Missing** |
| Shutdown script | -- | **Missing** (relies on SIGTERM + atexit) |

#### juniper-canopy (Monitoring Dashboard)

| Mechanism | File | Status |
|-----------|------|--------|
| Main entry point | `src/main.py` | Active |
| Application factory + lifespan | `src/main.py` (lifespan context manager) | Active |
| Settings (env vars) | `src/settings.py` | Active |
| Health endpoints | `src/health.py` (`/health`, `/v1/health`, `/v1/health/ready`) | Active |
| Dockerfile (multi-stage) | `Dockerfile` | Active |
| Alternative Dockerfile | `conf/Dockerfile` (Python 3.12, older) | Legacy |
| Demo startup script | `util/juniper_canopy-demo.bash` (symlink: `./demo`) | Active |
| Production startup script | `util/juniper_canopy.bash` (symlink: `./try`) | Active |
| systemd service unit | `scripts/juniper-canopy.service` | Active |
| Service management CLI | `scripts/juniper-ctl` | Active |
| Docker Compose (deprecated) | `conf/docker-compose.yaml` | Deprecated |
| Shutdown (demo) | Ctrl+C / SIGTERM | Implicit |
| Shutdown (systemd) | `systemctl --user stop juniper-canopy` / `juniper-ctl stop` | Active |

#### juniper-deploy (Orchestration)

| Mechanism | File | Status |
|-----------|------|--------|
| Docker Compose (primary) | `docker-compose.yml` | Active |
| Override template | `docker-compose.override.yml.example` | Template |
| Makefile (23 targets) | `Makefile` | Active |
| Health check script | `scripts/health_check.sh` | Active |
| Service wait script | `scripts/wait_for_services.sh` | Active |
| Demo profile test | `scripts/test_demo_profile.sh` | Active |
| Enhanced health test | `scripts/test_health_enhanced.sh` | Active |
| Environment files | `.env.example`, `.env.demo`, `.env.observability` | Active |
| Prometheus config | `prometheus/prometheus.yml` | Active |
| Grafana provisioning | `grafana/provisioning/` | Active |
| AlertManager config | `alertmanager/alertmanager.yml` | Active (placeholders) |
| Kubernetes manifests | -- | **Missing** |

#### juniper-ml (Meta-Package / Orchestration Utilities)

| Mechanism | File | Status |
|-----------|------|--------|
| Start all services | `util/juniper_plant_all.bash` | Active (fragile) |
| Stop all services | `util/juniper_chop_all.bash` | Active (fragile) |
| Kill all Python | `util/kill_all_pythons.bash` | Emergency only |
| CasCor query utilities | `util/get_cascor_*.bash` (7 scripts) | Active |
| Conda activation | `scripts/activate_conda_env.bash` | Template |

### 2.2 Per-Client/Worker Inventory

#### juniper-data-client

- **Type**: Pure HTTP client library
- **Startup logic**: None (provides `wait_for_ready()` for connecting to running services)
- **Deployment artifacts**: None (no Dockerfile, no systemd, no scripts)

#### juniper-cascor-client

- **Type**: HTTP/WebSocket client library
- **Startup logic**: None (provides `wait_for_ready()`, WebSocket streaming clients)
- **Deployment artifacts**: None

#### juniper-cascor-worker

- **Type**: Distributed training worker with CLI
- **CLI entry point**: `juniper-cascor-worker` command (two modes: WebSocket default, legacy BaseManager)
- **Signal handling**: SIGINT/SIGTERM with graceful shutdown
- **Deployment artifacts**: **None** (no Dockerfile, no systemd, no k8s -- critical gap)

---

## 3. Service-Mode Analysis (Host-Level)

### 3.1 Current State: `juniper_plant_all.bash`

**Location**: `juniper-ml/util/juniper_plant_all.bash` (143 lines)

**What it does**:
1. Sources conda from `/opt/miniforge3/etc/profile.d/conda.sh`
2. Starts juniper-data via `uvicorn` with `PYTHON_GIL=0`, sleeps 10s
3. Starts juniper-cascor via `python server.py`, sleeps 30s
4. Starts juniper-canopy via `python main.py` with `CASCOR_SERVICE_URL`, sleeps 10s
5. Writes PIDs to `juniper-ml/JuniperProject.pid`

**Issues Identified**:

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| S-01 | **Critical** | No health check verification after startup | Services may fail to start but script reports success |
| S-02 | **Critical** | No error handling on `conda activate` or `nohup` | Silent failures, orphaned processes |
| S-03 | **High** | Hardcoded paths (`/opt/miniforge3`, `${HOME}/Development/python/Juniper`) | Not portable, single-machine only |
| S-04 | **High** | Fixed sleep delays (10s, 30s, 10s) instead of health polling | Unreliable timing, wastes time or starts too early |
| S-05 | **High** | Uses `/opt/miniforge3/envs/JuniperCanopy/bin/python` for cascor | Wrong Python binary (should use JuniperCascor env) |
| S-06 | **Medium** | No log directory creation | Fails if `logs/` doesn't exist |
| S-07 | **Medium** | No port availability check before binding | Cryptic errors if port already in use |
| S-08 | **Medium** | No conda environment existence validation | Fails with unclear error if env missing |
| S-09 | **Low** | Missing double-quotes on PID file append lines | Potential word splitting |
| S-10 | **Low** | `get_cascor_dkdk.bash` is incomplete | Dead code in utility set |

### 3.2 Current State: `juniper_chop_all.bash`

**Location**: `juniper-ml/util/juniper_chop_all.bash` (156 lines)

**What it does**:
1. Reads PIDs from `JuniperProject.pid`
2. Sends SIGTERM to each service PID with 10s delay between
3. Searches `ps aux` for "juniper-cascor" processes (worker cleanup)
4. Sends SIGTERM to each worker PID with 2s delay between

**Issues Identified**:

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| D-01 | **Critical** | Exits with error (code 1) if no workers found | Script fails on systems without workers running |
| D-02 | **High** | No SIGKILL fallback after SIGTERM timeout | Processes may survive shutdown |
| D-03 | **High** | Fragile worker detection via `grep "juniper-cascor"` | Matches log viewers, editors, greps -- false positives |
| D-04 | **High** | No verification that processes actually stopped | Reports success even if processes survive |
| D-05 | **Medium** | PID file may contain stale PIDs from crashed services | Sends signals to wrong processes or nonexistent PIDs |
| D-06 | **Medium** | PID file format is space-delimited with colons | Brittle parsing, breaks if format changes |
| D-07 | **Low** | Activates JuniperCascor conda env unnecessarily | Not needed for kill operations |

### 3.3 Current State: systemd (juniper-canopy only)

**Service file**: `juniper-canopy/scripts/juniper-canopy.service`
**CLI**: `juniper-canopy/scripts/juniper-ctl`

**Strengths**:
- Proper systemd user service with security hardening (NoNewPrivileges, ProtectSystem, PrivateTmp)
- Resource limits (MemoryMax=2G, CPUQuota=200%)
- Automatic restart on failure (RestartSec=5)
- Management CLI with start/stop/restart/status/logs/health/resources commands
- Integration with journalctl for logging

**Issues**:

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| Y-01 | **High** | References `JuniperPython` env (should be `JuniperCanopy`) | Wrong conda environment in ExecStart |
| Y-02 | **Medium** | Hardcoded absolute paths in service file | Not portable |
| Y-03 | **Medium** | No systemd units for juniper-data or juniper-cascor | Incomplete service-mode coverage |
| Y-04 | **Low** | No socket activation or watchdog integration | Missing advanced systemd features |

### 3.4 Individual Application Startup Scripts

**juniper-canopy demo** (`util/juniper_canopy-demo.bash`):
- Creates conda env if missing, activates it, installs deps
- Sets `JUNIPER_CANOPY_DEMO_MODE=1`
- Runs uvicorn on port 8050
- **Strength**: Self-contained, handles env setup
- **Gap**: No health check after startup

**juniper-canopy production** (`util/juniper_canopy.bash`):
- Validates conda env, sets env vars
- Requires CASCOR_SERVICE_URL or explicit demo mode
- **Strength**: Input validation
- **Gap**: No dependency service health verification

**juniper-cascor launch** (`util/launch_cascor.bash`):
- Sets port to 8201, enables auto-start
- Calls `python server.py`
- **Gap**: Minimal, no env setup, no health check

---

## 4. Container-Mode Analysis (Docker Compose)

### 4.1 Architecture Overview

The `juniper-deploy` repository provides Docker Compose orchestration with 5 profiles:

```
Profile: full
  juniper-data (8100) ── juniper-cascor (8201) ── juniper-canopy (8050) ── redis (6379)

Profile: demo
  juniper-data (8100) ── demo-seed (init) ── juniper-cascor-demo (8201, auto-train) ── juniper-canopy-demo (8050, demo mode)

Profile: dev
  juniper-data (8100) ── juniper-cascor (8201) ── juniper-canopy-dev (8050, demo mode)

Profile: test
  juniper-data (8100) ── juniper-cascor (8201) ── juniper-canopy (8050) ── redis ── test-runner (exit)

Profile: observability (additive)
  prometheus (9090) ── grafana (3000) ── alertmanager (9093)
```

### 4.2 Strengths

| Area | Details |
|------|---------|
| **Health checks** | All services use HTTP health probes with proper intervals, timeouts, and retry counts |
| **Dependency ordering** | `depends_on` with `condition: service_healthy` ensures proper startup sequence |
| **Secrets management** | File-based Docker secrets with SOPS encryption |
| **Multi-profile** | 5 distinct profiles for different use cases |
| **Observability** | Prometheus + Grafana + AlertManager with auto-provisioned dashboards |
| **Networking** | 4 isolated bridge networks (backend, data, frontend, monitoring) |
| **Volumes** | Named volumes for data persistence |
| **Makefile** | 23 targets covering all common operations |
| **Testing** | Containerized test-runner with integration tests |
| **Documentation** | Comprehensive README, AGENTS.md, and docs/ |

### 4.3 Issues Identified

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| C-01 | **High** | No Kubernetes manifests | Cannot deploy to k8s clusters |
| C-02 | **High** | AlertManager receivers are placeholders | No actual alerting in observability profile |
| C-03 | **Medium** | No `docker compose down` graceful drain | Services may lose in-flight requests |
| C-04 | **Medium** | Cassandra referenced in docs but not in compose file | Stale documentation |
| C-05 | **Medium** | No env file validation before startup | Silent misconfiguration |
| C-06 | **Medium** | `prepare-secrets` creates empty files | Services may start with empty API keys |
| C-07 | **Low** | No volume backup/restore procedures documented | Data loss risk |
| C-08 | **Low** | juniper-cascor host port is 8201 (non-standard) | Potential confusion with docs showing 8200 |

### 4.4 Per-Service Dockerfile Review

All three service Dockerfiles follow a consistent multi-stage pattern:

| Feature | juniper-data | juniper-cascor | juniper-canopy |
|---------|-------------|----------------|----------------|
| Base image | python:3.14-slim | python:3.14-slim | python:3.14-slim |
| Non-root user | juniper:1000 | juniper:1000 | juniper:1000 |
| Health check | `/v1/health` | `/v1/health/ready` | `/v1/health` |
| Start period | 5s | 15s | 20s |
| Entrypoint | `python -m juniper_data` | `python src/server.py` | `python src/main.py` |
| Lockfile | requirements.lock | requirements.lock | requirements.lock |

**Inconsistency**: Health check endpoints differ (`/v1/health` vs `/v1/health/ready`). All should use `/v1/health` for liveness and `/v1/health/ready` for readiness probes in orchestration.

---

## 5. Kubernetes Analysis

### 5.1 Current State

**No Kubernetes manifests exist anywhere in the Juniper ecosystem.**

### 5.2 Requirements for K8s Support

Based on the existing Docker Compose architecture, a k8s deployment would need:

| Resource | Per Service | Notes |
|----------|------------|-------|
| Deployment | 3 (data, cascor, canopy) + 1 (worker) | With readiness/liveness probes |
| Service (ClusterIP) | 3 | Internal service discovery |
| Service (LoadBalancer/Ingress) | 1-2 | External access to canopy + optional data |
| ConfigMap | 3-4 | Environment configuration |
| Secret | 3-4 | API keys, tokens, DSNs |
| PersistentVolumeClaim | 3 | Datasets, snapshots, logs |
| Job | 1 | Demo seed (equivalent to demo-seed init container) |
| HorizontalPodAutoscaler | 1-2 | Worker scaling, optional cascor scaling |
| NetworkPolicy | 3-4 | Replicate Docker network isolation |
| ServiceMonitor (Prometheus Operator) | 3 | Metrics scraping |

---

## 6. Client & Worker Analysis

### 6.1 juniper-data-client / juniper-cascor-client

Both are pure client libraries. They provide:
- `wait_for_ready(timeout, poll_interval)` -- useful for startup scripts
- Health check methods -- useful for monitoring
- Connection retry with exponential backoff
- Exception hierarchies for connection/timeout/validation errors

**No startup/shutdown/orchestration changes needed.** These libraries are consumers, not producers.

### 6.2 juniper-cascor-worker

**Critical deployment gap.** The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:

| What Exists | What's Missing |
|-------------|----------------|
| CLI entry point | Dockerfile |
| Environment config | systemd service unit |
| Signal handling (SIGINT/SIGTERM) | Kubernetes Deployment + HPA |
| TLS/mTLS support | Docker Compose service definition in juniper-deploy |
| Exponential backoff reconnection | Health check endpoint (for k8s probes) |
| Two operating modes | Supervisor/process manager config |
| Comprehensive AGENTS.md | Startup/installation convenience script |

---

## 7. Cross-Cutting Concerns

### 7.1 Health Check Consistency

| Service | `/health` | `/v1/health` | `/v1/health/live` | `/v1/health/ready` |
|---------|-----------|--------------|--------------------|--------------------|
| juniper-data | -- | OK+version | alive | ready+deps |
| juniper-cascor | -- | OK+version | alive | ready+deps |
| juniper-canopy | basic | OK | -- | ready+deps |

**Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live` (liveness), `/v1/health/ready` (readiness with dependency checks).

### 7.2 Port Assignments

| Service | Host Mode | Container Internal | Container Published | Docker Compose |
|---------|-----------|-------------------|--------------------|----|
| juniper-data | 8100 | 8100 | 8100 | 8100 |
| juniper-cascor | 8201 | 8200 | 8201 | 8201 |
| juniper-canopy | 8050 | 8050 | 8050 | 8050 |

**Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts hardcode 8201. Documentation sometimes references 8200.

### 7.3 Conda Environment Mapping

| Service | Conda Env | Python |
|---------|-----------|--------|
| juniper-data | JuniperData | 3.14 |
| juniper-cascor | JuniperCascor | 3.14 |
| juniper-canopy | JuniperCanopy | 3.14 |

**Issue in `juniper_plant_all.bash`**: Uses `/opt/miniforge3/envs/JuniperCanopy/bin/python` as the PYTHON variable for ALL services, but then uses it specifically for cascor and canopy. Should use each service's own conda env Python binary.

### 7.4 Logging

| Mode | Mechanism | Location |
|------|-----------|----------|
| Host (plant script) | nohup redirect to timestamped files | `<service>/logs/` |
| Host (systemd) | journalctl | systemd journal |
| Container | Docker stdout/stderr | `docker compose logs` |
| Observability | Structured JSON + Prometheus | Grafana dashboards |

### 7.5 Shutdown Signal Handling

| Service | SIGTERM | SIGINT | Graceful Cleanup |
|---------|---------|--------|------------------|
| juniper-data | uvicorn handles | uvicorn handles | Lifespan shutdown |
| juniper-cascor | uvicorn handles | uvicorn handles | Lifespan shutdown + managed service cleanup |
| juniper-canopy | uvicorn handles | uvicorn handles | Lifespan shutdown + demo thread stop |
| juniper-cascor-worker | Signal handler | Signal handler | Worker stop + disconnect |

All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown completed.

---

## 8. Gap Analysis Summary

### 8.1 Priority Matrix

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Health-check-based startup in `juniper_plant_all.bash` | High | Low | **P0** |
| Error handling in startup/shutdown scripts | High | Low | **P0** |
| Fix worker-not-found exit in `juniper_chop_all.bash` | High | Trivial | **P0** |
| SIGKILL fallback after SIGTERM timeout | High | Low | **P0** |
| Fix wrong Python binary in plant script | High | Trivial | **P0** |
| systemd units for juniper-data and juniper-cascor | High | Medium | **P1** |
| juniper-cascor-worker Dockerfile | High | Medium | **P1** |
| Worker service in juniper-deploy compose | High | Medium | **P1** |
| Configurable paths in plant/chop scripts | Medium | Medium | **P1** |
| Port availability check before startup | Medium | Low | **P1** |
| Kubernetes manifests | High | High | **P2** |
| juniper-cascor-worker systemd unit | Medium | Medium | **P2** |
| AlertManager receiver configuration | Medium | Low | **P2** |
| Health endpoint standardization across services | Medium | Medium | **P2** |
| Volume backup/restore procedures | Low | Medium | **P3** |
| `get_cascor_dkdk.bash` completion or removal | Low | Trivial | **P3** |

### 8.2 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Service starts but isn't healthy | High | High | Health check polling in startup scripts |
| Orphaned processes after failed shutdown | Medium | High | PID validation + SIGKILL fallback |
| Wrong Python env used for service | High | High | Per-service env resolution |
| Stale PIDs sent to wrong processes | Medium | Medium | PID validation (check `/proc/<pid>/cmdline`) |
| Worker grep matches unrelated processes | Medium | Low | More specific process matching |
| Port conflict on startup | Low | Medium | Pre-flight port check |

---

## 9. Development & Tooling Recommendations

### 9.1 Approach A: Incremental Fix (Recommended)

Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add missing systemd units and worker deployment config.

**Strengths**:
- Minimal disruption to existing workflows
- Preserves familiarity for the developer
- Can be done incrementally
- Low risk of introducing new bugs

**Weaknesses**:
- Bash scripts have inherent limitations for complex orchestration
- No unified interface across modes (host vs container)
- Each fix is localized, not systematic

**Risk**: Low. Changes are additive and backward-compatible.

**Guardrails**:
- All changes must pass shellcheck
- Health check timeouts must be configurable
- Original behavior preserved when no flags are passed

### 9.2 Approach B: Unified CLI Tool (juniper-ctl)

Create a single `juniper-ctl` command (Python Click/Typer CLI) that manages all services across all modes:

```bash
juniper-ctl start [--mode host|docker|k8s] [--profile full|demo|dev]
juniper-ctl stop [--mode host|docker|k8s] [--graceful-timeout 30]
juniper-ctl status [--mode host|docker|k8s]
juniper-ctl health
juniper-ctl logs [service]
```

**Strengths**:
- Unified interface across all operating modes
- Python gives better error handling, logging, and testability
- Can leverage existing client libraries for health checks
- Single source of truth for startup logic
- Extensible for future services

**Weaknesses**:
- Significant new development effort
- New dependency (Click/Typer)
- Learning curve for the developer
- Must handle conda activation from Python (tricky)

**Risk**: Medium. New code means new bugs. Conda activation from Python subprocess is notoriously fragile.

**Guardrails**:
- Comprehensive test suite required before deployment
- Must support `--dry-run` for all operations
- Must work when no conda env is active

### 9.3 Approach C: systemd-First + Makefile Enhancement

Standardize on systemd user services for host-mode and enhance the juniper-deploy Makefile for container mode. Remove the bash orchestration scripts.

**Strengths**:
- Leverages OS-native process management
- Auto-restart on failure built in
- journalctl for unified logging
- Dependency ordering via `After=`/`Requires=`
- Already partially implemented (canopy has a service file)

**Weaknesses**:
- Linux-only (no macOS support)
- Requires `loginctl enable-linger` for user services to persist
- More complex initial setup per machine
- Can't easily handle conda environment activation in ExecStart

**Risk**: Low-Medium. systemd is well-understood, but conda integration adds complexity.

**Guardrails**:
- Service files must use `EnvironmentFile=` for configuration
- All services must have matching `juniper-ctl` wrappers
- ExecStartPre= should validate environment before launching

### 9.4 Recommended Approach

**Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

Rationale:
1. The existing bash scripts work and are understood by the developer
2. The fixes needed are well-defined and low-risk
3. systemd units are a natural next step that canopy already demonstrates
4. A unified CLI tool (Approach B) can be deferred as a P2 enhancement
5. Kubernetes (from any approach) is an independent workstream

### 9.5 Detailed Design: Improved `juniper_plant_all.bash`

```bash
# Key improvements:
# 1. wait_for_health() function that polls /v1/health with configurable timeout
# 2. check_port_available() function using ss or lsof
# 3. validate_conda_env() function that checks env exists
# 4. Per-service conda env Python binaries (not shared)
# 5. Configurable paths via environment variables with defaults
# 6. Error handling: trap ERR for cleanup on failure
# 7. Proper quoting on all variable expansions
# 8. Log directory creation if missing
```

### 9.6 Detailed Design: Improved `juniper_chop_all.bash`

```bash
# Key improvements:
# 1. validate_pid() function that checks /proc/<pid>/cmdline
# 2. graceful_stop() function: SIGTERM -> wait -> SIGKILL
# 3. Worker detection via /proc/<pid>/cmdline instead of grep
# 4. Optional worker shutdown (don't exit if no workers)
# 5. Post-shutdown verification that processes are gone
# 6. Configurable SIGTERM timeout before SIGKILL escalation
# 7. Clean up PID file after successful shutdown
```

### 9.7 Detailed Design: systemd Units

Three new systemd user service units following canopy's pattern:

**juniper-data.service**:
```ini
[Unit]
Description=Juniper Data - Dataset Generation Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Development/python/Juniper/juniper-data
EnvironmentFile=%h/Development/python/Juniper/juniper-data/.env
ExecStart=/opt/miniforge3/envs/JuniperData/bin/python -m juniper_data --host 0.0.0.0 --port 8100
Restart=on-failure
RestartSec=5
```

**juniper-cascor.service**:
```ini
[Unit]
Description=Juniper CasCor - Neural Network Training Service
After=network-online.target juniper-data.service
Wants=network-online.target
Requires=juniper-data.service

[Service]
Type=simple
WorkingDirectory=%h/Development/python/Juniper/juniper-cascor/src
EnvironmentFile=%h/Development/python/Juniper/juniper-cascor/.env
ExecStart=/opt/miniforge3/envs/JuniperCascor/bin/python server.py
Restart=on-failure
RestartSec=5
```

### 9.8 Detailed Design: Worker Dockerfile

```dockerfile
FROM python:3.14-slim AS builder
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN pip install --no-cache-dir --no-deps .

FROM python:3.14-slim
RUN groupadd -g 1000 juniper && useradd -u 1000 -g juniper juniper
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin/juniper-cascor-worker /usr/local/bin/
USER juniper
ENTRYPOINT ["juniper-cascor-worker"]
CMD ["--server-url", "ws://juniper-cascor:8200/ws/v1/workers"]
```

### 9.9 Detailed Design: Worker in Docker Compose

```yaml
juniper-cascor-worker:
  build:
    context: ../juniper-cascor-worker
    dockerfile: Dockerfile
  profiles: ["full", "test"]
  environment:
    CASCOR_SERVER_URL: ws://juniper-cascor:8200/ws/v1/workers
    CASCOR_HEARTBEAT_INTERVAL: "10.0"
  depends_on:
    juniper-cascor:
      condition: service_healthy
  networks:
    - backend
  deploy:
    replicas: 2
  restart: unless-stopped
```

---

## 10. Development Roadmap

### Phase 1: Critical Fixes (P0) -- Immediate

**Goal**: Make existing host-mode startup/shutdown reliable.

| Step | Task | Files | Est. Complexity |
|------|------|-------|-----------------|
| 1.1 | Add `wait_for_health()` function to `juniper_plant_all.bash` | `juniper-ml/util/juniper_plant_all.bash` | Low |
| 1.2 | Add error handling (`set -euo pipefail`, `trap`) to plant script | `juniper-ml/util/juniper_plant_all.bash` | Low |
| 1.3 | Fix Python binary: use per-service conda env paths | `juniper-ml/util/juniper_plant_all.bash` | Trivial |
| 1.4 | Add `validate_pid()` and `graceful_stop()` to chop script | `juniper-ml/util/juniper_chop_all.bash` | Low |
| 1.5 | Fix worker-not-found exit (make optional) | `juniper-ml/util/juniper_chop_all.bash` | Trivial |
| 1.6 | Add SIGKILL fallback with configurable timeout | `juniper-ml/util/juniper_chop_all.bash` | Low |
| 1.7 | Add port availability check to plant script | `juniper-ml/util/juniper_plant_all.bash` | Low |
| 1.8 | Add conda env validation to plant script | `juniper-ml/util/juniper_plant_all.bash` | Low |
| 1.9 | Complete or remove `get_cascor_dkdk.bash` | `juniper-ml/util/get_cascor_dkdk.bash` | Trivial |
| 1.10 | Fix quoting issues in PID file operations | `juniper-ml/util/juniper_plant_all.bash` | Trivial |

### Phase 2: systemd & Service Management (P1) -- Short-Term

**Goal**: Provide OS-native service management for all three core services.

| Step | Task | Files | Est. Complexity |
|------|------|-------|-----------------|
| 2.1 | Create `juniper-data.service` systemd unit | `juniper-data/scripts/juniper-data.service` | Medium |
| 2.2 | Create `juniper-cascor.service` systemd unit | `juniper-cascor/scripts/juniper-cascor.service` | Medium |
| 2.3 | Fix `juniper-canopy.service` env name (JuniperPython -> JuniperCanopy) | `juniper-canopy/scripts/juniper-canopy.service` | Trivial |
| 2.4 | Create `juniper-data-ctl` management CLI (modeled on juniper-ctl) | `juniper-data/scripts/juniper-data-ctl` | Medium |
| 2.5 | Create `juniper-cascor-ctl` management CLI | `juniper-cascor/scripts/juniper-cascor-ctl` | Medium |
| 2.6 | Create `juniper-all.service` systemd target for starting all services | `juniper-ml/scripts/juniper-all.target` | Low |
| 2.7 | Make paths configurable via env vars in plant/chop scripts | `juniper-ml/util/juniper_plant_all.bash`, `juniper-ml/util/juniper_chop_all.bash` | Medium |
| 2.8 | Update plant/chop scripts to optionally use systemctl | `juniper-ml/util/juniper_plant_all.bash`, `juniper-ml/util/juniper_chop_all.bash` | Medium |

### Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term

**Goal**: Enable containerized deployment of the distributed worker.

| Step | Task | Files | Est. Complexity |
|------|------|-------|-----------------|
| 3.1 | Create `juniper-cascor-worker/Dockerfile` | `juniper-cascor-worker/Dockerfile` | Medium |
| 3.2 | Create `requirements.lock` for worker | `juniper-cascor-worker/requirements.lock` | Low |
| 3.3 | Add worker service to `juniper-deploy/docker-compose.yml` | `juniper-deploy/docker-compose.yml` | Medium |
| 3.4 | Create `juniper-cascor-worker.service` systemd unit | `juniper-cascor-worker/scripts/juniper-cascor-worker.service` | Medium |
| 3.5 | Add health check endpoint to worker (optional HTTP sidecar or file-based) | `juniper-cascor-worker/` | High |
| 3.6 | Test worker in Docker Compose full and test profiles | `juniper-deploy/tests/` | Medium |

### Phase 4: Kubernetes Support (P2) -- Medium-Term

**Goal**: Enable k8s deployment of the full stack.

| Step | Task | Files | Est. Complexity |
|------|------|-------|-----------------|
| 4.1 | Create Helm chart structure | `juniper-deploy/k8s/helm/juniper/` | High |
| 4.2 | Define Deployments for data, cascor, canopy, worker | `k8s/helm/juniper/templates/` | High |
| 4.3 | Define Services (ClusterIP + Ingress) | `k8s/helm/juniper/templates/` | Medium |
| 4.4 | Define ConfigMaps and Secrets | `k8s/helm/juniper/templates/` | Medium |
| 4.5 | Define PVCs for data persistence | `k8s/helm/juniper/templates/` | Medium |
| 4.6 | Define HPA for worker auto-scaling | `k8s/helm/juniper/templates/` | Medium |
| 4.7 | Define NetworkPolicies | `k8s/helm/juniper/templates/` | Medium |
| 4.8 | Create values.yaml with all configuration | `k8s/helm/juniper/values.yaml` | Medium |
| 4.9 | Define ServiceMonitors for Prometheus Operator | `k8s/helm/juniper/templates/` | Low |
| 4.10 | Integration testing with kind or minikube | `juniper-deploy/scripts/test_k8s.sh` | High |

### Phase 5: Observability & Hardening (P2-P3) -- Medium-Term

| Step | Task | Files | Est. Complexity |
|------|------|-------|-----------------|
| 5.1 | Configure AlertManager receivers (Slack/email) | `juniper-deploy/alertmanager/alertmanager.yml` | Low |
| 5.2 | Define alert rules for service availability | `juniper-deploy/prometheus/alert_rules.yml` | Medium |
| 5.3 | Standardize health endpoints across all services | All service health.py files | Medium |
| 5.4 | Add volume backup/restore documentation | `juniper-deploy/docs/BACKUP_RESTORE.md` | Low |
| 5.5 | Add startup validation test suite | `juniper-ml/tests/test_startup_scripts.py` | Medium |

---

## Appendix: File Inventory

### A.1 Startup Scripts

| File | Repo | Type | Status |
|------|------|------|--------|
| `util/juniper_plant_all.bash` | juniper-ml | Start all (host) | Active, needs fixes |
| `util/juniper_chop_all.bash` | juniper-ml | Stop all (host) | Active, needs fixes |
| `util/juniper_canopy-demo.bash` | juniper-canopy | Start canopy (demo) | Active |
| `util/juniper_canopy.bash` | juniper-canopy | Start canopy (prod) | Active |
| `util/launch_cascor.bash` | juniper-cascor | Start cascor | Active |
| `scripts/juniper-ctl` | juniper-canopy | systemd CLI | Active |
| `scripts/juniper-canopy.service` | juniper-canopy | systemd unit | Active, needs fix |
| `util/kill_all_pythons.bash` | juniper-ml | Emergency kill | Emergency only |

### A.2 Container/Deploy Files

| File | Repo | Type | Status |
|------|------|------|--------|
| `docker-compose.yml` | juniper-deploy | Primary orchestration | Active |
| `docker-compose.override.yml.example` | juniper-deploy | Dev override template | Template |
| `Makefile` | juniper-deploy | Make targets (23) | Active |
| `Dockerfile` | juniper-data | Service image | Active |
| `Dockerfile` | juniper-cascor | Service image | Active |
| `Dockerfile` | juniper-canopy | Service image | Active |
| `conf/Dockerfile` | juniper-canopy | Legacy image | Deprecated |
| `conf/docker-compose.yaml` | juniper-canopy | Legacy compose | Deprecated |
| `conf/docker-compose.yaml` | juniper-cascor | Legacy compose | Deprecated |
| `Dockerfile.test` | juniper-deploy | Test runner | Active |

### A.3 Health Check Scripts

| File | Repo | Type |
|------|------|------|
| `scripts/health_check.sh` | juniper-deploy | Full stack health |
| `scripts/wait_for_services.sh` | juniper-deploy | Blocking wait |
| `scripts/test_demo_profile.sh` | juniper-deploy | Demo validation |
| `scripts/test_health_enhanced.sh` | juniper-deploy | Enhanced health validation |

### A.4 CasCor Query Utilities

| File | Repo | Endpoint |
|------|------|----------|
| `util/get_cascor_status.bash` | juniper-ml | `/v1/training/status` |
| `util/get_cascor_metrics.bash` | juniper-ml | `/v1/metrics` |
| `util/get_cascor_history.bash` | juniper-ml | `/v1/metrics/history?count=10` |
| `util/get_cascor_history-plus.bash` | juniper-ml | `/v1/metrics/history?count=100` |
| `util/get_cascor_network.bash` | juniper-ml | `/v1/network` |
| `util/get_cascor_topology.bash` | juniper-ml | `/v1/network/topology` |
| `util/get_cascor_dkdk.bash` | juniper-ml | Incomplete |

### A.5 Configuration Files

| File | Repo | Type |
|------|------|------|
| `.env.example` | juniper-deploy | Full config template |
| `.env.demo` | juniper-deploy | Demo profile overrides |
| `.env.observability` | juniper-deploy | Metrics enablement |
| `.env.secrets.example` | juniper-deploy | Secrets template |
| `.env.example` | juniper-data | Service config template |
| `.env.dev` / `.env.prod` | juniper-canopy | Environment templates |
| `prometheus/prometheus.yml` | juniper-deploy | Scrape config |
| `alertmanager/alertmanager.yml` | juniper-deploy | Alert routing |
| `grafana/provisioning/` | juniper-deploy | Dashboard provisioning |

### A.6 Application Entry Points

| File | Repo | Purpose |
|------|------|---------|
| `juniper_data/__main__.py` | juniper-data | `python -m juniper_data` |
| `juniper_data/api/app.py` | juniper-data | App factory + lifespan |
| `src/server.py` | juniper-cascor | Server entry point |
| `src/main.py` | juniper-cascor | CLI training entry |
| `src/api/app.py` | juniper-cascor | App factory + lifespan |
| `src/main.py` | juniper-canopy | Main entry + lifespan |
| `juniper_cascor_worker/cli.py` | juniper-cascor-worker | Worker CLI |

---

*End of Code Review Document*
