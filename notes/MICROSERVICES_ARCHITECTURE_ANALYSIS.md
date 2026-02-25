# Juniper Microservices Architecture Analysis

**Project**: Juniper ML Research Platform
**Created**: 2026-02-25
**Author**: Paul Calnon / Claude Code
**Status**: Planning — Analysis Only (No Code Changes)
**Scope**: Coordinated startup, operating modes, and architectural evaluation

---

## Table of Contents

- [1. Current Architecture Summary](#1-current-architecture-summary)
- [2. Coordinated Application Startup](#2-coordinated-application-startup)
  - [2.1 Current State](#21-current-state)
  - [2.2 Startup Orchestration Options](#22-startup-orchestration-options)
  - [2.3 Comparative Evaluation](#23-comparative-evaluation)
  - [2.4 Recommendation](#24-recommendation)
- [3. Modes of Operation](#3-modes-of-operation)
  - [3.1 Current Implementation](#31-current-implementation)
  - [3.2 Purpose and Analysis of Current Modes](#32-purpose-and-analysis-of-current-modes)
  - [3.3 Operating Mode Options for Microservices](#33-operating-mode-options-for-microservices)
  - [3.4 Comparative Evaluation](#34-comparative-evaluation)
  - [3.5 Recommendation](#35-recommendation)
- [4. Service Discovery and Health Checking](#4-service-discovery-and-health-checking)
  - [4.1 Current Health Endpoints](#41-current-health-endpoints)
  - [4.2 Discovery Approach Evaluation](#42-discovery-approach-evaluation)
  - [4.3 Health Check Pattern Recommendation](#43-health-check-pattern-recommendation)
- [5. Configuration Management](#5-configuration-management)
- [6. Architectural Growth Path](#6-architectural-growth-path)
- [7. Summary of Recommendations](#7-summary-of-recommendations)

---

## 1. Current Architecture Summary

### Service Topology

```
┌─────────────────────┐     REST/WS      ┌──────────────────────┐
│   JuniperCanopy     │ ◄──────────────► │    JuniperCascor     │
│   (Dashboard)       │                  │    (Training Svc)    │
│   Port 8050         │                  │    Port 8200         │
│                     │                  │                      │
│   Uses:             │     REST         │    Uses:             │
│   - cascor-client   │ ◄──────────────► │    - data-client     │
│   - data-client     │                  │    - cascor-worker   │
└─────────────────────┘                  └──────────┬───────────┘
         │                                          │
         │ REST                              Task/Result Queues
         ▼                                          │
┌─────────────────────┐                  ┌──────────▼───────────┐
│   JuniperData       │                  │   Remote Workers     │
│   (Dataset Svc)     │                  │   (N instances)      │
│   Port 8100         │                  │                      │
└─────────────────────┘                  └──────────────────────┘
```

### Service Inventory

| Service | Port | Entry Point | Framework | Startup Method |
| --- | --- | --- | --- | --- |
| **JuniperData** | 8100 | `python -m juniper_data` | FastAPI + uvicorn | CLI with `--host`, `--port`, `--log-level` flags |
| **JuniperCascor** | 8200 | `python src/server.py` | FastAPI + uvicorn | Pydantic Settings (`JUNIPER_CASCOR_*` env vars) |
| **JuniperCanopy** | 8050 | `uvicorn src.main:app` | FastAPI + Dash + uvicorn | YAML config (`src/conf/app_config.yaml`) + env vars |

### Client Packages (PyPI)

| Package | Version | Purpose |
| --- | --- | --- |
| `juniper-data-client` | 0.3.0 | HTTP client for JuniperData API |
| `juniper-cascor-client` | 0.1.0 | HTTP/WS client for CasCor service |
| `juniper-cascor-worker` | 0.1.0 | Remote candidate training worker |
| `juniper-ml` | 0.1.0 | Meta-package (installs all of the above) |

### Dependency Graph (Runtime)

```
JuniperCanopy ──REST──► JuniperData       (via juniper-data-client)
JuniperCanopy ──REST/WS──► JuniperCascor  (via juniper-cascor-client)
JuniperCascor ──REST──► JuniperData       (via juniper-data-client)
Remote Workers ──Queues──► JuniperCascor   (via juniper-cascor-worker)
```

### Existing Infrastructure

- **Docker Compose**: Partial — `JuniperCanopy/conf/docker-compose.yaml` defines `juniper-data`, `juniper_canopy`, and `redis` services; `JuniperCascor/conf/docker-compose.yaml` defines `juniper-data` only
- **Dockerfiles**: JuniperData (multi-stage, Python 3.11-slim, non-root), JuniperCanopy (Python 3.9-slim)
- **Health Endpoints**: All three services implement `/v1/health`, `/v1/health/live`, `/v1/health/ready`
- **Environment**: Shared `JuniperPython` conda environment on development machine
- **Git**: 7 independent repos with SSH deploy keys, all on `main` branch

---

## 2. Coordinated Application Startup

### 2.1 Current State

There is no unified multi-service startup mechanism. Each service is started independently:

```bash
# Terminal 1: JuniperData
cd JuniperData/juniper_data && python -m juniper_data

# Terminal 2: JuniperCascor
cd juniper-cascor/src && python server.py

# Terminal 3: JuniperCanopy
cd JuniperCanopy/juniper_canopy && uvicorn src.main:app --port 8050
```

The Canopy Docker Compose (`conf/docker-compose.yaml`) can start JuniperData + Canopy + Redis together, but it does not include JuniperCascor, and it uses Docker networking rather than the conda environment.

**Gaps**: No startup ordering, no dependency health verification, no unified log aggregation, no single command to start the full platform.

### 2.2 Startup Orchestration Options

#### Option A: Docker Compose (Unified)

Create a single ecosystem-level `docker-compose.yml` that defines all services with proper dependency ordering.

```yaml
# Conceptual structure
services:
  juniper-data:
    ports: [8100:8100]
    healthcheck: { test: curl -f http://localhost:8100/v1/health }

  juniper-cascor:
    ports: [8200:8200]
    depends_on:
      juniper-data: { condition: service_healthy }
    healthcheck: { test: curl -f http://localhost:8200/v1/health }

  juniper-canopy:
    ports: [8050:8050]
    depends_on:
      juniper-data: { condition: service_healthy }
      juniper-cascor: { condition: service_healthy }
    healthcheck: { test: curl -f http://localhost:8050/v1/health/live }

  redis:
    image: redis:7-alpine
    ports: [6379:6379]
```

**Orchestration quality**: Excellent. Declarative dependency ordering with health-gated startup (`depends_on: condition: service_healthy`) ensures services start in the correct order. One command starts everything: `docker compose up`. Profiles enable selective startup: `docker compose --profile monitoring up` could include Prometheus/Grafana.

**Scalability**: Strong. Adding a new service is a new block in the YAML. Docker Compose scales to 20+ services comfortably. Compose files translate to Kubernetes manifests via tools like Kompose when the time comes. Docker Swarm provides multi-machine scaling without leaving the Compose ecosystem.

**Best practices**: Docker Compose is the FastAPI-recommended approach for multi-service development. Aligns with 12-Factor App methodology. De facto industry standard for local multi-service orchestration.

**Security**: Container isolation (namespaces, cgroups) limits blast radius of a compromised service. Multi-stage builds minimize attack surface. Non-root container users. Secrets via `docker compose secrets` (file-backed) rather than environment variables. Network segmentation via separate Docker networks (frontend/backend).

**Performance**: Containerization adds minimal overhead on Linux (native cgroups, no VM). GPU passthrough requires NVIDIA Container Toolkit. Conda environments inside Docker produce large images (2-5 GB) — mitigated with Miniforge and multi-stage builds. Bind mount performance for source code is native on Linux.

#### Option B: Process Manager (supervisord)

Use supervisord to manage all services as a process group on the host.

```ini
[group:juniper]
programs=juniper-data,juniper-cascor,juniper-canopy

[program:juniper-data]
command=/opt/miniforge3/envs/JuniperPython/bin/python -m juniper_data
directory=/home/pcalnon/Development/python/Juniper/JuniperData/juniper_data
autorestart=true
startsecs=5

[program:juniper-cascor]
command=/opt/miniforge3/envs/JuniperPython/bin/python server.py
directory=/home/pcalnon/Development/python/Juniper/juniper-cascor/src
autorestart=true
startsecs=5

[program:juniper-canopy]
command=/opt/miniforge3/envs/JuniperPython/bin/uvicorn src.main:app --port 8050
directory=/home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy
autorestart=true
startsecs=5
```

**Orchestration quality**: Moderate. supervisord starts all programs in a group but has no dependency ordering or health-gated startup — all services start simultaneously. Auto-restart on crash is a significant benefit. The `supervisorctl` CLI and optional web UI provide process monitoring.

**Scalability**: Moderate for single machine. Adding a new service is a new `[program:]` block. Does not extend to multi-machine without external configuration management (Ansible). No built-in concept of service profiles or selective startup.

**Best practices**: Proven and mature (20+ years). Common in traditional Python deployments. Less aligned with modern cloud-native practices but pragmatic for single-machine research.

**Security**: No isolation — all processes run as the invoking user with full host access. No network segmentation. Process-level hardening requires wrapping with `setpriv` or similar. Lower attack surface than Docker (no container runtime vulnerabilities).

**Performance**: Zero overhead — processes run natively with the conda environment. Native GPU access. Best possible performance for ML training workloads.

#### Option C: Makefile + Procfile Hybrid

A Makefile as the developer-facing interface, with a Procfile for simple multi-process startup via honcho.

```makefile
# Makefile
.PHONY: up down status logs

up:
	honcho start -f Procfile

down:
	honcho stop || pkill -f "juniper_data|server.py|uvicorn"

status:
	@curl -sf http://localhost:8100/v1/health | jq .status || echo "data: DOWN"
	@curl -sf http://localhost:8200/v1/health | jq .status || echo "cascor: DOWN"
	@curl -sf http://localhost:8050/v1/health/live | jq .status || echo "canopy: DOWN"
```

```
# Procfile
data: cd /path/to/juniper-data && python -m juniper_data
cascor: cd /path/to/juniper-cascor/src && python server.py
canopy: cd /path/to/juniper-canopy && uvicorn src.main:app --port 8050
```

**Orchestration quality**: Basic. honcho starts all processes and provides color-coded, interleaved log output in a single terminal — excellent for development visibility. No dependency ordering, no health-gated startup, no auto-restart on crash. The Makefile provides a discoverable interface (`make up`, `make down`, `make status`).

**Scalability**: Low. Adding a service is a new Procfile line. Does not extend to multi-machine. No profiles or selective startup. Suitable for up to ~5-7 services before log output becomes unwieldy.

**Best practices**: Good as a lightweight development tool. honcho/foreman is the standard Procfile runner for Python projects. Not production-grade. Best when it wraps a more capable tool (e.g., `make up` calls `docker compose up`).

**Security**: No isolation. All processes share the host environment. Scripts can accidentally hardcode secrets.

**Performance**: Zero overhead (native processes). Same performance characteristics as Option B.

#### Option D: systemd Service Units

Define each service as a systemd unit with a `juniper.target` to start them as a group.

```ini
# /etc/systemd/system/juniper-data.service
[Unit]
Description=JuniperData Dataset Service
After=network.target

[Service]
Type=simple
User=pcalnon
WorkingDirectory=/home/pcalnon/Development/python/Juniper/JuniperData/juniper_data
ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m juniper_data
Restart=on-failure
RestartSec=5
ProtectSystem=strict
ProtectHome=read-only
NoNewPrivileges=true

[Install]
WantedBy=juniper.target
```

**Orchestration quality**: Good. systemd provides dependency ordering (`After=`, `Requires=`, `Wants=`), automatic restart (`Restart=on-failure`), resource limits (CPU, memory via cgroups), and watchdog timers. A `juniper.target` groups all services: `systemctl start juniper.target` starts everything in dependency order.

**Scalability**: Moderate for single machine. Adding a service is a new unit file. Multi-machine requires configuration management (Ansible/Salt) to distribute units.

**Best practices**: Excellent for Linux production servers. Native to the OS init system. Provides the most granular security hardening of any non-container option (`ProtectSystem=`, `ProtectHome=`, `NoNewPrivileges=`, `CapabilityBoundingSet=`, `SystemCallFilter=`).

**Security**: systemd sandboxing is more granular than Docker for single-host deployments. `DynamicUser=yes` creates ephemeral users. `SystemCallFilter=` restricts syscalls (similar to seccomp). However, no network namespace isolation by default.

**Performance**: Zero overhead. Native GPU access. Best for production single-machine deployments.

#### Option E: Kubernetes (k3s)

Deploy all services as Kubernetes Deployments with Services, using k3s (lightweight Kubernetes distribution) for a single-machine setup.

**Orchestration quality**: Excellent. Kubernetes provides declarative desired-state management, self-healing (automatic pod restart, rescheduling), liveness/readiness/startup probes, and init containers for dependency ordering. Helm charts or Kustomize enable environment-specific configuration.

**Scalability**: Unmatched. Native multi-machine, auto-scaling via HPA, GPU scheduling (`nvidia.com/gpu` resource requests), service mesh (Istio) for observability. The destination architecture if Juniper grows to production scale.

**Best practices**: Industry gold standard for production container orchestration.

**Security**: Network policies, RBAC, pod security standards, secret encryption. Most comprehensive security model.

**Performance**: Control plane overhead (~500 MB-1 GB RAM for k3s). Container overhead is minimal on Linux. GPU scheduling is native and sophisticated.

**Assessment**: Premature for a 3-service research platform on a single machine. The complexity-to-benefit ratio is poor at this scale. Recommended only when multi-machine deployment or multi-user production use becomes a real requirement.

### 2.3 Comparative Evaluation

| Criterion | Docker Compose | supervisord | Makefile+Procfile | systemd | Kubernetes |
| --- | --- | --- | --- | --- | --- |
| **Orchestration quality** | Excellent | Moderate | Basic | Good | Excellent |
| **Dependency ordering** | Health-gated | None | None | Unit-based | Probe-gated |
| **Auto-restart** | Yes (policy) | Yes | No | Yes (policy) | Yes (self-healing) |
| **Dev experience** | Good | Fair | Excellent | Fair | Poor (alone) |
| **Production readiness** | Good | Good | Poor | Excellent | Excellent |
| **Setup complexity** | Medium | Low | Very Low | Medium | Very High |
| **GPU support** | NVIDIA Toolkit | Native | Native | Native | Native (scheduling) |
| **Multi-machine** | Swarm | No | No | Ansible | Yes (native) |
| **Security isolation** | Containers | None | None | Sandboxing | Full (namespaces + RBAC) |
| **Performance overhead** | Minimal (Linux) | Zero | Zero | Zero | ~500 MB control plane |
| **Adding a new service** | YAML block | INI block | Procfile line | Unit file | Manifest set |
| **Log aggregation** | `docker compose logs` | supervisorctl tail | Interleaved stdout | journalctl | kubectl logs / EFK |

### 2.4 Recommendation

**Recommended approach: Layered strategy with Docker Compose as the primary orchestrator.**

```
Phase 1 (Immediate):  Makefile as developer interface + Docker Compose as orchestration engine
Phase 2 (Near-term):  Docker Compose with profiles for dev/demo/full environments
Phase 3 (If needed):  Kubernetes via k3s when multi-machine or production scale is required
```

**Rationale**:

1. Docker Compose is the only option that provides health-gated dependency ordering, process supervision, network isolation, and reproducibility in a single tool
2. The Makefile wrapping layer preserves developer ergonomics (`make up`, `make down`, `make logs`, `make status`)
3. Existing Dockerfiles and docker-compose.yaml files provide a foundation — the work is consolidation, not creation from scratch
4. The transition path to Kubernetes is well-defined and incremental

**What to build**:

- A single `docker-compose.yml` at the ecosystem level (e.g., `Juniper/docker-compose.yml`) that defines all 3 services + Redis
- A `Makefile` at the same level with targets: `up`, `down`, `logs`, `status`, `restart`, `build`
- Docker Compose profiles: `default` (data + canopy), `full` (data + cascor + canopy + redis), `demo` (canopy in demo mode only)
- A `.env.example` with all cross-service configuration variables

---

## 3. Modes of Operation

### 3.1 Current Implementation

JuniperCanopy implements a two-mode activation system in `src/main.py` (lines 213-247):

```
Priority 1: CASCOR_DEMO_MODE=1      → Demo mode (explicit override)
Priority 2: CASCOR_SERVICE_URL set   → Service mode (REST/WS via CascorServiceAdapter)
Priority 3: Neither set              → Demo mode (default fallback)
```

**Demo mode**: A `DemoMode` instance (`src/demo_mode.py`) generates simulated training data — synthetic metrics, network topology, and training state transitions. It runs in-process on a background timer, broadcasting updates to WebSocket clients. No external services required.

**Service mode**: A `CascorServiceAdapter` (`src/backend/cascor_service_adapter.py`, 306 lines) wraps `juniper-cascor-client` to communicate with a running CasCor service via REST/WebSocket. Requires JuniperCascor to be running and reachable.

### 3.2 Purpose and Analysis of Current Modes

#### Demo Mode

**Purpose**:
- Showcase Canopy's dashboard features without requiring a running CasCor backend
- Enable frontend development and testing in isolation
- Provide a zero-dependency demonstration for stakeholders
- Serve as CI test backend (all 3,130+ tests run with `CASCOR_DEMO_MODE=1`)

**Strengths**:
- Zero external dependencies — starts instantly with `CASCOR_DEMO_MODE=1`
- Simulates realistic training lifecycle: idle → training → paused → complete
- WebSocket broadcasting works identically to real mode
- Covers the full Canopy API surface (metrics, topology, status, decision boundary)

**Weaknesses**:
- Demo data is static/formulaic — does not reflect real CasCor training dynamics
- Demo code paths diverge from real code paths; changes to the dashboard may work in demo but fail in service mode
- `if demo_mode_instance:` / `if backend:` branching throughout `main.py` increases cognitive load and maintenance burden
- No mechanism to verify that demo behavior stays in sync with real CasCor service API evolution
- Demo mode cannot showcase CasCor-specific features (real convergence behavior, actual candidate pool dynamics)

#### Service Mode

**Purpose**:
- Production operation: monitor real CasCor neural network training
- Integration testing against a live backend
- Full-featured demonstration with real training runs

**Strengths**:
- Exercises the real API contract — issues are caught early
- Enables monitoring of actual training runs with real data
- Leverages all CasCor service capabilities (snapshots, decision boundary, worker management)

**Weaknesses**:
- Requires JuniperCascor and JuniperData to be running and healthy
- Startup is more complex (3 services, correct env vars, port availability)
- No graceful degradation if CasCor becomes unavailable mid-session

### 3.3 Operating Mode Options for Microservices

#### Option 1: Runtime Feature Flag (Current Approach, Enhanced)

Keep the `CASCOR_DEMO_MODE` environment variable toggle but refactor the branching.

**Enhancement**: Instead of scattered `if demo_mode_instance:` checks, use a common backend interface. Both `DemoMode` and `CascorServiceAdapter` implement the same protocol. The route handlers call `backend.get_status()` regardless of mode.

```
┌──────────────────────┐
│  Canopy main.py      │
│  (route handlers)    │
│                      │
│  backend.get_status() ◄─── uniform interface
│  backend.start()     │
│  backend.get_metrics()│
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼───┐   ┌────▼────────────┐
│DemoMode│   │CascorService   │
│(local) │   │Adapter (REST)  │
└────────┘   └────────────────┘
```

**Best practices**: Clean separation of concerns. Strategy pattern. Easy to test each backend implementation independently.

**Security**: Demo mode flag should be validated at startup and logged prominently. Consider disallowing `CASCOR_DEMO_MODE=1` when `JUNIPER_ENV=production`. No bypass of authentication even in demo mode.

**Performance**: Zero overhead. No additional processes or network calls in demo mode.

**Scalability**: Moderate. Adding a new backend (e.g., a recording/replay backend) requires implementing the interface. The flag approach doesn't compose well — `CASCOR_DEMO_MODE` is binary, but future modes may not be.

**Transparency**: High. The active mode is logged at startup. Route handlers are agnostic to the active backend.

**Maintainability**: Good if the backend interface is well-defined and tested. Risk of interface drift if demo mode doesn't keep up with new service mode capabilities.

#### Option 2: Mock Service Containers (External Fakes)

Replace the in-process `DemoMode` with a lightweight mock service container that implements the CasCor API contract. JuniperCanopy always runs in "service mode" — it just points at the mock instead of the real service.

```
Demo scenario:
  CASCOR_SERVICE_URL=http://mock-cascor:8200
  → Canopy talks to mock container (same API, canned responses)

Real scenario:
  CASCOR_SERVICE_URL=http://juniper-cascor:8200
  → Canopy talks to real CasCor service
```

The mock container can be auto-generated from the CasCor OpenAPI spec (FastAPI generates `/openapi.json` automatically). Tools: Prism (Stoplight), WireMock, or a minimal FastAPI stub.

**Best practices**: Eliminates all branching in Canopy — there is only one code path (service mode). The mock is a deployment concern, not an application concern. This is the standard microservices testing pattern.

**Security**: Mock containers must not be deployable in production. Use Docker Compose profiles to ensure mock services only start in dev/demo profiles. Mock data must not contain real secrets.

**Performance**: Adds network round-trip overhead even in demo mode (localhost HTTP is ~0.1ms per call). Requires a running container. Slightly more resource-intensive than in-process demo.

**Scalability**: Excellent. The same pattern applies to any service — mock JuniperData, mock CasCor, mock workers. Adding a new service mock is automatic if OpenAPI specs are maintained.

**Transparency**: Excellent. `docker compose --profile demo up` makes it explicit that mocks are in use. Canopy's code has no concept of "demo mode" — it's always in service mode.

**Maintainability**: Excellent. One code path in Canopy. Mock containers auto-generated from specs stay in sync with the real API. No demo-specific code to maintain.

#### Option 3: Client Library Fakes (In-Process Stubs)

Ship fake implementations with the client libraries themselves. `juniper-cascor-client` includes a `FakeCascorClient` that returns configurable synthetic data. `juniper-data-client` includes a `FakeDataClient`.

```python
# In juniper-cascor-client package
from juniper_cascor_client.testing import FakeCascorClient

# In Canopy's startup
if demo_mode:
    client = FakeCascorClient(scenario="two_spiral_training")
else:
    client = CascorClient(base_url=service_url)

backend = CascorServiceAdapter(client=client)
```

**Best practices**: Aligns with the testing pyramid — fakes are the standard approach for unit testing client-dependent code. The Strategy pattern naturally supports swappable backends. Co-locating fakes with client libraries ensures they're maintained alongside the real implementation.

**Security**: Minimal risk. Fakes are in-process, no new network surface. Ensure fake data generators don't use real credentials or PII.

**Performance**: Zero network overhead. Fastest possible demo mode — purely in-memory.

**Scalability**: Good. Each client library owns its own fake. Adding a new client package means adding a new fake to that package.

**Transparency**: Medium. Requires reading the code or startup logs to know a fake is in use. Less obvious than a separate mock container.

**Maintainability**: Good if fakes are tested alongside the real client (e.g., both run against the same test suite with different backends). Risk of drift if fakes are an afterthought.

#### Option 4: Recorded Responses (VCR/Cassette Pattern)

Record real HTTP interactions during a live session and replay them deterministically. Python libraries: `vcrpy`, `responses`, `respx`.

```python
# Record a real training session
with vcr.VCR().use_cassette('training_session.yaml'):
    response = client.start_training(config)
    # ... all HTTP calls recorded to YAML

# Replay in demo/test mode
with vcr.VCR().use_cassette('training_session.yaml', record_mode='none'):
    response = client.start_training(config)  # Returns recorded response
```

**Best practices**: Provides the highest-fidelity demo data — it's real CasCor output. Cassettes serve as API contract documentation. Standard approach for integration test fixtures.

**Security**: **Critical risk** — cassettes may capture API keys, tokens, or sensitive training data. Must implement scrubbing hooks (`before_record_request`, `before_record_response`) to strip headers and sensitive fields. Cassettes should be reviewed before committing to version control.

**Performance**: Very fast replay (no network calls). Cassette file I/O is negligible.

**Scalability**: Moderate. Cassettes become stale when APIs change — must re-record periodically. Large training sessions produce large cassette files. Better suited for testing than for live demo mode.

**Transparency**: High. Cassette files are visible in the repository and clearly document expected interactions.

**Maintainability**: Medium. Requires a process for re-recording cassettes when the CasCor API evolves. CI can detect stale cassettes by running against real services periodically.

#### Option 5: Separate Demo Environment (Docker Compose Profile)

Maintain a completely separate Docker Compose profile that runs pre-configured demo instances of all services with synthetic datasets.

```yaml
# docker-compose.yml
services:
  juniper-data:
    profiles: [full, demo]
    # ...

  juniper-cascor:
    profiles: [full]
    # ... real CasCor service

  juniper-cascor-demo:
    profiles: [demo]
    image: juniper-cascor:demo
    environment:
      - CASCOR_AUTO_TRAIN=true           # Auto-start a training session
      - CASCOR_DEMO_DATASET=two_spiral   # Pre-loaded dataset
    # ...

  juniper-canopy:
    profiles: [full, demo]
    environment:
      - CASCOR_SERVICE_URL=http://juniper-cascor-demo:8200  # Points to demo CasCor
    # ...
```

```bash
# Demo: auto-training CasCor with pre-loaded data
docker compose --profile demo up

# Real: full platform with real training
docker compose --profile full up
```

**Best practices**: Complete isolation between demo and real environments. Canopy always runs the same code — only the upstream service differs. The demo CasCor is the real CasCor, just with auto-start configuration. This is the most realistic demo possible.

**Security**: Strong isolation. Demo environment cannot accidentally affect production data. Demo secrets are separate from production secrets.

**Performance**: Runs real services, so resource consumption matches production. Heavier than in-process demo mode.

**Scalability**: Excellent. Adding a new service to the demo profile is a YAML block. The pattern extends to any number of services.

**Transparency**: Excellent. `docker compose --profile demo up` makes the intent unmistakable. The demo is a real training session — it's just auto-configured.

**Maintainability**: Good. No demo-specific code in any application. The demo profile just configures real services differently. When CasCor changes, the demo changes automatically.

### 3.4 Comparative Evaluation

| Criterion | Option 1: Feature Flag | Option 2: Mock Containers | Option 3: Client Fakes | Option 4: VCR | Option 5: Demo Profile |
| --- | --- | --- | --- | --- | --- |
| **Code complexity in Canopy** | Medium (branching) | None | Low (DI only) | Low (fixture loading) | None |
| **Demo realism** | Low (formulaic) | Medium (canned) | Medium (configurable) | High (recorded real) | Very High (real services) |
| **Infrastructure overhead** | None | Container(s) | None | None | Full service stack |
| **Resource usage** | Minimal | Low | Minimal | Minimal | Full |
| **Startup speed (demo)** | Instant | ~5-10s (containers) | Instant | Instant | ~15-30s (full stack) |
| **API drift risk** | High | Low (if spec-gen) | Medium | Low (until stale) | None |
| **CI/CD test utility** | Low | High | High | Very High | Medium |
| **Stakeholder demo quality** | Medium | Medium | Medium | Medium-High | Excellent |
| **Maintenance burden** | High | Low | Medium | Medium | Low |
| **Security risk** | Flag bypass | Mock in prod | Minimal | Cassette secrets | Minimal |

### 3.5 Recommendation

**Recommended approach: Phased adoption combining Options 1, 3, and 5.**

```
Phase 1 (Immediate):  Refactor Option 1 — unify DemoMode and CascorServiceAdapter
                       behind a common BackendProtocol interface. Eliminate scattered
                       if/else branching in main.py.

Phase 2 (Near-term):  Adopt Option 3 — add FakeCascorClient and FakeDataClient to
                       client libraries. Use dependency injection in CascorServiceAdapter
                       to swap real and fake clients. This also improves unit testing.

Phase 3 (With Docker): Adopt Option 5 — add a demo profile to Docker Compose that
                        runs real CasCor with auto-start configuration. This provides
                        the most realistic demo experience for stakeholders.
```

**Rationale**:

1. The immediate refactor (Phase 1) reduces maintenance burden and makes the codebase cleaner without any infrastructure changes
2. Client library fakes (Phase 2) improve testability across all consuming projects, not just Canopy
3. The Docker Compose demo profile (Phase 3) provides a zero-code-change path to realistic demos that stay in sync with real services automatically
4. VCR/cassettes (Option 4) should be adopted independently for integration test fixtures but are not suitable as a primary demo mechanism

---

## 4. Service Discovery and Health Checking

### 4.1 Current Health Endpoints

All three services already implement Kubernetes-compatible health probes:

| Service | Liveness | Readiness | Combined |
| --- | --- | --- | --- |
| **JuniperData** | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ...}` | `GET /v1/health` |
| **JuniperCascor** | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ..., "network_loaded": ...}` | `GET /v1/health` |
| **JuniperCanopy** | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ...}` | — |

This is a strong foundation. The liveness/readiness separation follows the standard cloud-native pattern.

### 4.2 Discovery Approach Evaluation

| Approach | Complexity | Suitability for Juniper | When to Adopt |
| --- | --- | --- | --- |
| **Direct URL (env vars)** | Very Low | Excellent (current) | Now — already in place |
| **Docker Compose DNS** | Zero (automatic) | Excellent | When Docker Compose is adopted |
| **Consul/etcd** | Very High | Overkill | Only if 10+ services or multi-datacenter |
| **Kubernetes DNS** | Zero (automatic) | Excellent | When Kubernetes is adopted |

**Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle discovery automatically when containerization is adopted. No service registry infrastructure is needed at this scale.

### 4.3 Health Check Pattern Recommendation

**Enhance readiness checks to include dependency health**:

```
JuniperCanopy /v1/health/ready should report:
  - self: alive
  - cascor_service: reachable / unreachable / demo_mode
  - data_service: reachable / unreachable
  - mode: service | demo

JuniperCascor /v1/health/ready should report:
  - self: alive
  - data_service: reachable / unreachable
  - network: loaded / not_loaded
  - training: idle / active / paused

JuniperData /v1/health/ready should report:
  - self: alive
  - storage: available / unavailable
```

**Add startup health verification to Canopy**: When `CASCOR_SERVICE_URL` is set, perform an HTTP GET to the CasCor health endpoint during lifespan startup. Log a warning if unreachable and fall back to demo mode (this addresses roadmap item CAN-HIGH-001).

---

## 5. Configuration Management

### Current State

| Service | Config Approach | Config Source |
| --- | --- | --- |
| **JuniperData** | Pydantic `BaseSettings` | Env vars with `JUNIPER_DATA_*` prefix |
| **JuniperCascor** | Pydantic `BaseSettings` | Env vars with `JUNIPER_CASCOR_*` prefix |
| **JuniperCanopy** | YAML config + env vars | `src/conf/app_config.yaml` + `${VAR:default}` substitution |

### Evaluation

The mixed approach (Pydantic Settings for two services, YAML for one) creates inconsistency. All three services are FastAPI-based, so Pydantic `BaseSettings` is the natural fit.

**Recommendation**: Standardize on Pydantic `BaseSettings` across all services. This provides:

- Type-safe, validated configuration
- Automatic environment variable loading
- `.env` file support
- Self-documenting defaults
- Consistent pattern across the ecosystem

**Environment profiles**: Use `JUNIPER_ENV` to select `.env` files:

```
.env.example    # Template with placeholder values (committed)
.env.dev        # Development defaults (committed, no secrets)
.env.prod       # Production configuration (NEVER committed)
```

---

## 6. Architectural Growth Path

```
                         Current                Near-Term              Future
                    ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
Orchestration:      │ Manual       │  →   │ Docker Compose   │ → │ Kubernetes   │
                    │ (3 terminals)│      │ (unified YAML)   │   │ (k3s/managed)│
                    └──────────────┘      └──────────────────┘   └──────────────┘

Discovery:          ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
                    │ Env vars     │  →   │ Compose DNS      │ → │ K8s DNS      │
                    │ (manual URLs)│      │ (automatic)      │   │ (automatic)  │
                    └──────────────┘      └──────────────────┘   └──────────────┘

Demo Mode:          ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
                    │ Feature flag │  →   │ Client fakes +   │ → │ Demo profile │
                    │ (in-process) │      │ BackendProtocol  │   │ (real svcs)  │
                    └──────────────┘      └──────────────────┘   └──────────────┘

Configuration:      ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
                    │ Mixed (YAML/ │  →   │ Pydantic Settings│ → │ ConfigMaps + │
                    │ env vars)    │      │ + .env files     │   │ Secrets      │
                    └──────────────┘      └──────────────────┘   └──────────────┘

Monitoring:         ┌──────────────┐      ┌──────────────────┐   ┌──────────────┐
                    │ Per-service  │  →   │ docker compose   │ → │ Prometheus + │
                    │ logs         │      │ logs + health UI │   │ Grafana      │
                    └──────────────┘      └──────────────────┘   └──────────────┘
```

Each transition is incremental — no "big bang" migration required. Docker Compose services translate to Kubernetes manifests. Health endpoints work across all orchestrators. Pydantic Settings reads from any environment variable source.

---

## 7. Summary of Recommendations

### Immediate (No Infrastructure Changes)

1. **Refactor Canopy's backend branching**: Define a `BackendProtocol` that both `DemoMode` and `CascorServiceAdapter` implement. Eliminate scattered `if demo_mode_instance:` checks in `main.py`.
2. **Add startup health check**: When `CASCOR_SERVICE_URL` is set, probe the health endpoint during lifespan startup. Log and fall back gracefully (addresses CAN-HIGH-001).
3. **Enhance readiness endpoints**: Include dependency health status in each service's `/v1/health/ready` response.

### Near-Term (Docker Compose Adoption)

4. **Create ecosystem-level `docker-compose.yml`**: Define all 3 services + Redis with health-gated dependency ordering. Place at `Juniper/docker-compose.yml` (or `Juniper/juniper/docker-compose.yml`).
5. **Add Docker Compose profiles**: `default` (data + canopy), `full` (all services), `demo` (canopy in demo mode).
6. **Create ecosystem-level Makefile**: `make up`, `make down`, `make logs`, `make status`, `make build` targets wrapping Docker Compose.
7. **Add client library fakes**: Ship `FakeCascorClient` in `juniper-cascor-client` and `FakeDataClient` in `juniper-data-client` for testing and lightweight demo mode.
8. **Standardize configuration**: Migrate Canopy from YAML config to Pydantic `BaseSettings`. Create `.env.example` with all cross-service variables.

### Future (If Scale Demands)

9. **Docker Compose demo profile**: Run real CasCor with auto-start training for stakeholder demos.
10. **Kubernetes migration**: When multi-machine or multi-user production deployment is needed, transition Docker Compose definitions to Kubernetes manifests via k3s.
11. **Centralized secret management**: Adopt HashiCorp Vault or Kubernetes Secrets when API key management and rotation become operational concerns.

---

## Document History

| Date | Author | Changes |
| --- | --- | --- |
| 2026-02-25 | AI Agent | Initial creation: startup orchestration, operating modes, service discovery, configuration, and growth path analysis |
