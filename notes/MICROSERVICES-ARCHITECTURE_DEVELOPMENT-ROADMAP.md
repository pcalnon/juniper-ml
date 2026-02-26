# Juniper Microservices Architecture — Development Roadmap

**Project**: Juniper ML Research Platform
**Created**: 2026-02-25
**Author**: Paul Calnon / Claude Code
**Status**: Planning — Implementation Roadmap (No Code Changes)
**Reference**: [MICROSERVICES_ARCHITECTURE_ANALYSIS.md](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md) — Sections 2.4, 3.5, 4.3, 5

---

## Table of Contents

- [Overview](#overview)
- [Phase 1: Makefile + Docker Compose (Immediate)](#phase-1-makefile--docker-compose-immediate)
  - [1.1 Objectives](#11-objectives)
  - [1.2 Prerequisites](#12-prerequisites)
  - [1.3 Directory Layout](#13-directory-layout)
  - [1.4 Docker Compose Design](#14-docker-compose-design)
  - [1.5 Makefile Design](#15-makefile-design)
  - [1.6 Environment Configuration](#16-environment-configuration)
  - [1.7 Implementation Tasks](#17-implementation-tasks)
  - [1.8 Verification Procedure](#18-verification-procedure)
  - [1.9 Security Considerations](#19-security-considerations)
  - [1.10 Performance Considerations](#110-performance-considerations)
- [Phase 2: systemd Service Units (Near-Term)](#phase-2-systemd-service-units-near-term)
  - [2.1 Objectives](#21-objectives)
  - [2.2 Prerequisites](#22-prerequisites)
  - [2.3 Unit File Architecture](#23-unit-file-architecture)
  - [2.4 Service Unit Specifications](#24-service-unit-specifications)
  - [2.5 Health Monitoring Integration](#25-health-monitoring-integration)
  - [2.6 Performance Monitoring](#26-performance-monitoring)
  - [2.7 Management Scripts](#27-management-scripts)
  - [2.8 Implementation Tasks](#28-implementation-tasks)
  - [2.9 Verification Procedure](#29-verification-procedure)
  - [2.10 Security Considerations](#210-security-considerations)
  - [2.11 Performance Considerations](#211-performance-considerations)
- [Phase 3: Docker Compose Profiles (Near-Term)](#phase-3-docker-compose-profiles-near-term)
  - [3.1 Objectives](#31-objectives)
  - [3.2 Prerequisites](#32-prerequisites)
  - [3.3 Profile Architecture](#33-profile-architecture)
  - [3.4 Compose File Design](#34-compose-file-design)
  - [3.5 Network Topology](#35-network-topology)
  - [3.6 Volume Strategy](#36-volume-strategy)
  - [3.7 Secrets Management](#37-secrets-management)
  - [3.8 Observability Stack](#38-observability-stack)
  - [3.9 Implementation Tasks](#39-implementation-tasks)
  - [3.10 Verification Procedure](#310-verification-procedure)
  - [3.11 Security Considerations](#311-security-considerations)
  - [3.12 Performance Considerations](#312-performance-considerations)
- [Phase 4: Kubernetes via k3s (Intermediate)](#phase-4-kubernetes-via-k3s-intermediate)
  - [4.1 Objectives](#41-objectives)
  - [4.2 Prerequisites](#42-prerequisites)
  - [4.3 Cluster Architecture](#43-cluster-architecture)
  - [4.4 Namespace Design](#44-namespace-design)
  - [4.5 Manifest Specifications](#45-manifest-specifications)
  - [4.6 Helm Chart Structure](#46-helm-chart-structure)
  - [4.7 Ingress and Networking](#47-ingress-and-networking)
  - [4.8 Secret Management](#48-secret-management)
  - [4.9 GPU Scheduling](#49-gpu-scheduling)
  - [4.10 Implementation Tasks](#410-implementation-tasks)
  - [4.11 Verification Procedure](#411-verification-procedure)
  - [4.12 Security Considerations](#412-security-considerations)
  - [4.13 Performance Considerations](#413-performance-considerations)
- [Modes of Operation — Overview](#modes-of-operation--overview)
- [Phase 5: BackendProtocol Interface Refactor (Immediate)](#phase-5-backendprotocol-interface-refactor-immediate)
  - [5.1 Objectives](#51-objectives)
  - [5.2 Prerequisites](#52-prerequisites)
  - [5.3 Current Branching Analysis](#53-current-branching-analysis)
  - [5.4 BackendProtocol Design](#54-backendprotocol-design)
  - [5.5 DemoBackend Implementation](#55-demobackend-implementation)
  - [5.6 ServiceBackend Implementation](#56-servicebackend-implementation)
  - [5.7 main.py Refactor Pattern](#57-mainpy-refactor-pattern)
  - [5.8 Implementation Tasks](#58-implementation-tasks)
  - [5.9 Verification Procedure](#59-verification-procedure)
  - [5.10 Security Considerations](#510-security-considerations)
  - [5.11 Performance Considerations](#511-performance-considerations)
- [Phase 6: Client Library Fakes (Near-Term)](#phase-6-client-library-fakes-near-term)
  - [6.1 Objectives](#61-objectives)
  - [6.2 Prerequisites](#62-prerequisites)
  - [6.3 FakeCascorClient Design](#63-fakecascorclient-design)
  - [6.4 FakeDataClient Design](#64-fakedataclient-design)
  - [6.5 FakeCascorTrainingStream Design](#65-fakecascortrainingstream-design)
  - [6.6 Package Layout](#66-package-layout)
  - [6.7 Dependency Injection in CascorServiceAdapter](#67-dependency-injection-in-cascorserviceadapter)
  - [6.8 Implementation Tasks](#68-implementation-tasks)
  - [6.9 Verification Procedure](#69-verification-procedure)
  - [6.10 Security Considerations](#610-security-considerations)
  - [6.11 Performance Considerations](#611-performance-considerations)
- [Phase 7: Docker Compose Demo Profile (With Docker)](#phase-7-docker-compose-demo-profile-with-docker)
  - [7.1 Objectives](#71-objectives)
  - [7.2 Prerequisites](#72-prerequisites)
  - [7.3 Profile Architecture](#73-profile-architecture)
  - [7.4 Compose File Modifications](#74-compose-file-modifications)
  - [7.5 Auto-Start Configuration for CasCor](#75-auto-start-configuration-for-cascor)
  - [7.6 Demo Dataset Seeding](#76-demo-dataset-seeding)
  - [7.7 Environment Configuration](#77-environment-configuration)
  - [7.8 Implementation Tasks](#78-implementation-tasks)
  - [7.9 Verification Procedure](#79-verification-procedure)
  - [7.10 Security Considerations](#710-security-considerations)
  - [7.11 Performance Considerations](#711-performance-considerations)
- [Service Discovery and Health Checking — Overview](#service-discovery-and-health-checking--overview)
- [Phase 8: Enhanced Health Checks with Dependency Status (Immediate)](#phase-8-enhanced-health-checks-with-dependency-status-immediate)
  - [8.1 Objectives](#81-objectives)
  - [8.2 Prerequisites](#82-prerequisites)
  - [8.3 Current Health Endpoint Analysis](#83-current-health-endpoint-analysis)
  - [8.4 Enhanced Readiness Response Schema](#84-enhanced-readiness-response-schema)
  - [8.5 Per-Service Implementation Design](#85-per-service-implementation-design)
  - [8.6 Response Envelope Standardization](#86-response-envelope-standardization)
  - [8.7 Startup Health Verification for Canopy](#87-startup-health-verification-for-canopy)
  - [8.8 Implementation Tasks](#88-implementation-tasks)
  - [8.9 Verification Procedure](#89-verification-procedure)
  - [8.10 Security Considerations](#810-security-considerations)
  - [8.11 Performance Considerations](#811-performance-considerations)
- [Configuration Management — Overview](#configuration-management--overview)
- [Phase 9: Configuration Standardization — Pydantic BaseSettings (Near-Term)](#phase-9-configuration-standardization--pydantic-basesettings-near-term)
  - [9.1 Objectives](#91-objectives)
  - [9.2 Prerequisites](#92-prerequisites)
  - [9.3 Current Configuration Divergence](#93-current-configuration-divergence)
  - [9.4 Target Architecture](#94-target-architecture)
  - [9.5 JuniperCanopy Migration Design](#95-junipercanopy-migration-design)
  - [9.6 Environment Variable Prefix Standardization](#96-environment-variable-prefix-standardization)
  - [9.7 Environment Profiles](#97-environment-profiles)
  - [9.8 Backward Compatibility Strategy](#98-backward-compatibility-strategy)
  - [9.9 Implementation Tasks](#99-implementation-tasks)
  - [9.10 Verification Procedure](#910-verification-procedure)
  - [9.11 Security Considerations](#911-security-considerations)
  - [9.12 Performance Considerations](#912-performance-considerations)
- [Cross-Phase Concerns](#cross-phase-concerns)
  - [Health Check Standardization](#health-check-standardization)
  - [Logging and Log Aggregation](#logging-and-log-aggregation)
  - [Configuration Parity](#configuration-parity)
- [Phase Dependency Map](#phase-dependency-map)
- [Document History](#document-history)

---

## Overview

This document provides detailed implementation plans for each of the recommendations selected in [MICROSERVICES_ARCHITECTURE_ANALYSIS.md](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md).

**Coordinated Application Startup** (Section 2.4):

```bash
Phase 1 (Immediate):    Makefile as developer interface + Docker Compose as orchestration engine
Phase 2 (Near-term):    Utilize systemd with unit files, health checks and performance monitoring
Phase 3 (Near-term):    Docker Compose with profiles for dev/demo/full environments
Phase 4 (Intermediate): Kubernetes via k3s when multi-machine or production scale is required
```

**Modes of Operation** (Section 3.5):

```bash
Phase 5 (Immediate):    BackendProtocol interface — unify DemoMode and CascorServiceAdapter
Phase 6 (Near-term):    Client library fakes — FakeCascorClient and FakeDataClient for testing/demo
Phase 7 (With Docker):  Docker Compose demo profile — real CasCor with auto-start configuration
```

**Service Discovery and Health Checking** (Section 4.3):

```bash
Phase 8 (Immediate):    Enhanced /v1/health/ready with dependency status and response standardization
```

**Configuration Management** (Section 5):

```bash
Phase 9 (Near-term):    Migrate JuniperCanopy to Pydantic BaseSettings, standardize prefixes and .env
```

### Current State Reference

| Service           | Port | Entry Point              | Config System                                | Health Endpoint                                     |
|-------------------|------|--------------------------|----------------------------------------------|-----------------------------------------------------|
| **JuniperData**   | 8100 | `python -m juniper_data` | Pydantic `BaseSettings` (`JUNIPER_DATA_*`)   | `/v1/health`, `/v1/health/live`, `/v1/health/ready` |
| **JuniperCascor** | 8200 | `python src/server.py`   | Pydantic `BaseSettings` (`JUNIPER_CASCOR_*`) | `/v1/health`, `/v1/health/live`, `/v1/health/ready` |
| **JuniperCanopy** | 8050 | `python src/main.py`     | YAML + env vars (`CASCOR_*`)                 | `/v1/health`                                        |

### Startup Dependency Chain

```bash
juniper-data (8100)         ← starts first, no dependencies
    │
    ├── juniper-cascor (8200)   ← requires juniper-data healthy
    │
    └── juniper-canopy (8050)   ← requires juniper-data + juniper-cascor healthy
```

### Existing Infrastructure

- **`juniper-deploy/docker-compose.yml`**: Three-service stack with health-gated `depends_on`, Python urllib health checks, non-root containers, `unless-stopped` restart policy
- **`juniper-deploy/scripts/wait_for_services.sh`**: Integration test helper polling all three health endpoints (90s default timeout, 3s interval)
- **`juniper-deploy/.env.example`**: Template with host, port, and log level variables for all services
- **Per-service Dockerfiles**: Multi-stage builds (builder + runtime), Python 3.11/3.12-slim bases, non-root `juniper:1000` user, OCI labels
- **Per-service `conf/docker-compose.yaml`**: Standalone Compose files for JuniperCascor and JuniperCanopy (partial service sets, legacy)

---

## Phase 1: Makefile + Docker Compose (Immediate)

### 1.1 Objectives

- Provide a single-command developer interface to start, stop, and inspect the full Juniper platform
- Consolidate the existing `juniper-deploy/docker-compose.yml` as the canonical orchestration definition
- Create a Makefile that wraps Docker Compose commands with ergonomic, discoverable targets
- Establish the `.env` / `.env.example` pattern for environment configuration
- Deprecate the per-service `conf/docker-compose.yaml` files in favor of the unified definition

### 1.2 Prerequisites

| Requirement       | Version | Verification                            |
|-------------------|---------|-----------------------------------------|
| Docker Engine     | >= 24.0 | `docker --version`                      |
| Docker Compose V2 | >= 2.20 | `docker compose version`                |
| GNU Make          | >= 4.0  | `make --version`                        |
| curl or Python 3  | any     | `curl --version` or `python3 --version` |

Docker Compose V2 is required because the Phase 1 Compose file uses `depends_on: condition: service_healthy`, which is V2-only syntax. Compose V2 ships as a Docker CLI plugin (`docker compose` rather than `docker-compose`).

### 1.3 Directory Layout

```bash
juniper-deploy/
├── docker-compose.yml          # Canonical orchestration file (already exists)
├── Makefile                    # NEW — developer-facing interface
├── .env.example                # Already exists — template for all env vars
├── .env                        # NOT committed — local overrides
├── .gitignore                  # Ensure .env is ignored
├── scripts/
│   ├── wait_for_services.sh    # Already exists — integration test helper
│   └── health_check.sh         # NEW — human-readable health status report
└── README.md                   # NEW — usage documentation
```

No changes to the existing `docker-compose.yml` in this phase. Phase 3 extends it with profiles.

### 1.4 Docker Compose Design

The existing `juniper-deploy/docker-compose.yml` already implements the correct architecture:

**Service dependency chain** (health-gated):

```yaml
juniper-data:      # starts first
juniper-cascor:    depends_on: { juniper-data: condition: service_healthy }
juniper-canopy:    depends_on: { juniper-data: condition: service_healthy,
                                 juniper-cascor: condition: service_healthy }
```

**Health checks** (Python urllib — no curl dependency in container):

```yaml
healthcheck:
  test: ["CMD", "python", "-c",
         "import urllib.request; urllib.request.urlopen('http://localhost:PORT/v1/health', timeout=5)"]
  interval: 15s
  timeout: 10s
  start_period: 10s   # 10s (data), 15s (cascor), 20s (canopy)
  retries: 5
```

**Restart policy**: `unless-stopped` on all services.

**Internal networking**: Services communicate via Docker Compose DNS names (`http://juniper-data:8100`, `http://juniper-cascor:8200`).

**No changes required** to `docker-compose.yml` for Phase 1. The file is already correct and functional.

### 1.5 Makefile Design

The Makefile provides the developer-facing interface. All targets wrap `docker compose` commands with the `juniper-deploy/` directory as context.

**Design principles**:

- All targets are `.PHONY` (no file dependencies)
- `make help` is the default target, displaying all available commands
- Targets use `@` prefix to suppress command echo (cleaner output)
- The `COMPOSE_FILE` variable allows overriding the Compose file path
- Color output for status reporting (with `NO_COLOR` fallback)

**Target inventory**:

| Target           | Command                                   | Purpose                                       |
|------------------|-------------------------------------------|-----------------------------------------------|
| `help`           | —                                         | Print all available targets with descriptions |
| `up`             | `docker compose up -d`                    | Start all services (detached)                 |
| `down`           | `docker compose down`                     | Stop and remove all containers                |
| `restart`        | `docker compose restart`                  | Restart all services                          |
| `logs`           | `docker compose logs -f`                  | Tail logs from all services (follow)          |
| `logs-data`      | `docker compose logs -f juniper-data`     | Tail JuniperData logs                         |
| `logs-cascor`    | `docker compose logs -f juniper-cascor`   | Tail JuniperCascor logs                       |
| `logs-canopy`    | `docker compose logs -f juniper-canopy`   | Tail JuniperCanopy logs                       |
| `status`         | `docker compose ps` + health probe        | Show container status and health              |
| `build`          | `docker compose build`                    | Build/rebuild all images                      |
| `build-no-cache` | `docker compose build --no-cache`         | Full rebuild without cache                    |
| `clean`          | `docker compose down -v --rmi local`      | Remove containers, volumes, and local images  |
| `shell-data`     | `docker compose exec juniper-data bash`   | Shell into JuniperData container              |
| `shell-cascor`   | `docker compose exec juniper-cascor bash` | Shell into JuniperCascor container            |
| `shell-canopy`   | `docker compose exec juniper-canopy bash` | Shell into JuniperCanopy container            |
| `health`         | `scripts/health_check.sh`                 | Detailed health report for all services       |
| `wait`           | `scripts/wait_for_services.sh`            | Block until all services are healthy          |
| `ps`             | `docker compose ps --format table`        | Compact container listing                     |

**Conceptual Makefile structure**:

```makefile
# Juniper Platform — Developer Interface
# Usage: make [target]

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE := docker compose
COMPOSE_FILE ?= docker-compose.yml

# Colors (disabled if NO_COLOR is set)
ifdef NO_COLOR
  GREEN :=
  YELLOW :=
  CYAN :=
  RESET :=
else
  GREEN := \033[0;32m
  YELLOW := \033[0;33m
  CYAN := \033[0;36m
  RESET := \033[0m
endif

.PHONY: help up down restart logs status build clean health wait ps

help:  ## Show this help message
 @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
  awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'

up:  ## Start all services (detached)
 @$(COMPOSE) -f $(COMPOSE_FILE) up -d
 @echo -e "$(GREEN)Services starting. Run 'make logs' to follow output.$(RESET)"

down:  ## Stop and remove all containers
 @$(COMPOSE) -f $(COMPOSE_FILE) down

# ... (remaining targets follow same pattern)
```

### 1.6 Environment Configuration

**`.env.example`** (already exists at `juniper-deploy/.env.example`):

The existing file covers host, port, and log level for all three services. For Phase 1, extend it to include all cross-service variables referenced in Docker Compose:

```bash
# === JuniperData ===
JUNIPER_DATA_HOST=0.0.0.0
JUNIPER_DATA_PORT=8100
JUNIPER_DATA_LOG_LEVEL=INFO
JUNIPER_DATA_STORAGE_PATH=/app/data/datasets

# === JuniperCascor ===
CASCOR_HOST=0.0.0.0
CASCOR_PORT=8200
CASCOR_LOG_LEVEL=INFO
JUNIPER_DATA_URL=http://juniper-data:8100

# === JuniperCanopy ===
CANOPY_HOST=0.0.0.0
CANOPY_PORT=8050
JUNIPER_DATA_URL=http://juniper-data:8100
CASCOR_SERVICE_URL=http://juniper-cascor:8200
# CASCOR_DEMO_MODE=1  # Uncomment for demo mode (no real backend needed)
```

**`.gitignore`**: Ensure `.env` (but not `.env.example`) is ignored. The existing `juniper-deploy/.gitignore` should contain:

```bash
.env
!.env.example
```

### 1.7 Implementation Tasks

| #   | Task                                                                                                                                                                                                                                          | Files                     | Depends On |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|------------|
| 1.1 | Create `juniper-deploy/Makefile` with all targets listed in Section 1.5                                                                                                                                                                       | `Makefile`                | —          |
| 1.2 | Create `juniper-deploy/scripts/health_check.sh` — hit all three `/v1/health/ready` endpoints, format output with service name, status, version, and latency                                                                                   | `scripts/health_check.sh` | —          |
| 1.3 | Extend `juniper-deploy/.env.example` with full variable set (Section 1.6)                                                                                                                                                                     | `.env.example`            | —          |
| 1.4 | Verify `.gitignore` excludes `.env` but not `.env.example`                                                                                                                                                                                    | `.gitignore`              | —          |
| 1.5 | Create `juniper-deploy/README.md` documenting usage: prerequisites, quick start (`make up`), available targets, environment configuration, troubleshooting                                                                                    | `README.md`               | 1.1        |
| 1.6 | Validate full startup cycle: `make build && make up && make wait && make health && make down`                                                                                                                                                 | —                         | 1.1, 1.2   |
| 1.7 | add deprecate msg to: `JuniperCascor/juniper_cascor/conf/docker-compose.yaml`, `JuniperCanopy/juniper_canopy/conf/docker-compose.yaml`, `juniper-cascor/conf/docker-compose.yaml` — after header, link to `juniper-deploy/docker-compose.yml` | 3 files                   | 1.6        |

### 1.8 Verification Procedure

```bash
cd juniper-deploy

# 1. Build all images
make build

# 2. Start the full stack
make up

# 3. Wait for all services to become healthy
make wait
# Expected: "All services healthy" within 60 seconds

# 4. Verify health endpoints
make health
# Expected output (conceptual):
#   juniper-data    ✓ ready  v0.4.0  (12ms)
#   juniper-cascor  ✓ ready  v0.7.3  (18ms)
#   juniper-canopy  ✓ ready  v0.x.x  (25ms)

# 5. Verify service communication
docker compose exec juniper-cascor python -c \
  "import urllib.request; print(urllib.request.urlopen('http://juniper-data:8100/v1/health').read())"
# Expected: {"status": "ok", "version": "..."}

# 6. Verify log output
make logs
# Expected: Interleaved logs from all three services, color-coded by service name

# 7. Clean shutdown
make down

# 8. Verify clean state
docker compose ps
# Expected: No containers running
```

### 1.9 Security Considerations

| Concern                              | Mitigation                                                                                                                              |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| `.env` committed with secrets        | `.gitignore` excludes `.env`; `.env.example` contains only non-sensitive defaults; pre-commit hook can scan for secret patterns         |
| Container images contain build tools | Multi-stage Dockerfiles already separate builder from runtime — no `pip`, `gcc`, or build artifacts in final images                     |
| Containers run as root               | Already mitigated — all Dockerfiles use `USER juniper` (UID 1000)                                                                       |
| CORS set to `["*"]` in all services  | Acceptable for development. Phase 3 profiles should tighten CORS for production (`JUNIPER_DATA_CORS_ORIGINS=["http://localhost:8050"]`) |
| No TLS between services              | Acceptable for Docker internal network (same host). Phase 4 (Kubernetes) adds mTLS via service mesh                                     |
| `make clean` destroys volumes        | Target includes confirmation prompt or `--force` flag                                                                                   |

### 1.10 Performance Considerations

| Concern                 | Impact                                                     | Mitigation                                                                                                                                                     |
|-------------------------|------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Docker image build time | 2-5 min per service (cold), <30s (cached)                  | Multi-stage builds already optimize layers. `make build` builds all three in parallel (Compose default)                                                        |
| Container startup time  | ~10-20s per service (health check start periods)           | Start periods already tuned: 10s (data), 15s (cascor), 20s (canopy). Total stack healthy in ~45-60s                                                            |
| GPU passthrough         | Not available in Phase 1 Docker setup                      | Phase 2 (systemd) provides native GPU. Phase 4 (k3s) provides GPU scheduling. For GPU workloads, run JuniperCascor natively while other services run in Docker |
| Bind mount I/O          | Native on Linux (no performance penalty)                   | Already using named volumes for data, bind mounts only if development hot-reload is needed                                                                     |
| PyTorch in container    | CPU-only wheels in Dockerfiles (~200 MB vs ~2 GB for CUDA) | Correct for dashboard/API. GPU training should use Phase 2 (native) or Phase 4 (k3s with GPU nodes)                                                            |

---

## Phase 2: systemd Service Units (Near-Term)

### 2.1 Objectives

- Define each Juniper service as a systemd unit running natively on the host with the `JuniperPython` conda environment
- Provide dependency ordering via systemd `After=`/`Requires=` directives
- Implement health check integration using systemd watchdog and custom health timers
- Enable performance monitoring via systemd resource accounting (CPU, memory, I/O cgroups)
- Create a `juniper.target` that starts all services as a group
- Provide a management script for common operations (`juniper-ctl`)

### 2.2 Prerequisites

| Requirement            | Version | Verification                                              |
|------------------------|---------|-----------------------------------------------------------|
| systemd                | >= 250  | `systemctl --version`                                     |
| Python (conda)         | >= 3.12 | `/opt/miniforge3/envs/JuniperPython/bin/python --version` |
| curl or Python 3       | any     | For health check scripts                                  |
| User lingering enabled | —       | `loginctl enable-linger pcalnon` (for user units)         |

**Deployment choice**: User units (`~/.config/systemd/user/`) vs system units (`/etc/systemd/system/`).

- **User units** are recommended for development — no `sudo` required, managed by the developer's login session, persist with `loginctl enable-linger`
- **System units** are appropriate for production servers where services should start at boot regardless of user login

This roadmap documents **user units** as primary, with notes on system unit differences.

### 2.3 Unit File Architecture

```bash
~/.config/systemd/user/                   # User unit directory
├── juniper.target                        # Target grouping all services
├── juniper-data.service                  # JuniperData service unit
├── juniper-cascor.service                # JuniperCascor service unit
├── juniper-canopy.service                # JuniperCanopy service unit
├── juniper-data-health.service           # One-shot health check for JuniperData
├── juniper-data-health.timer             # Periodic health check timer
├── juniper-cascor-health.service         # One-shot health check for JuniperCascor
├── juniper-cascor-health.timer           # Periodic health check timer
├── juniper-canopy-health.service         # One-shot health check for JuniperCanopy
└── juniper-canopy-health.timer           # Periodic health check timer

juniper-deploy/
├── systemd/
│   ├── user/                             # Unit file source (committed to repo)
│   │   ├── juniper.target
│   │   ├── juniper-data.service
│   │   ├── juniper-cascor.service
│   │   ├── juniper-canopy.service
│   │   ├── juniper-data-health.service
│   │   ├── juniper-data-health.timer
│   │   ├── juniper-cascor-health.service
│   │   ├── juniper-cascor-health.timer
│   │   ├── juniper-canopy-health.service
│   │   └── juniper-canopy-health.timer
│   └── install.sh                        # Symlinks units into ~/.config/systemd/user/
├── scripts/
│   ├── juniper-ctl                       # Management CLI wrapper
│   └── health_check_systemd.sh           # Health check used by timer units
└── conf/
    └── juniper.env                       # Environment file for all services
```

### 2.4 Service Unit Specifications

#### juniper.target

The target groups all Juniper services. `systemctl --user start juniper.target` starts everything in dependency order.

```ini
[Unit]
Description=Juniper ML Platform — All Services
Documentation=https://github.com/your-org/juniper
After=network-online.target
Wants=network-online.target

[Install]
WantedBy=default.target
```

#### juniper-data.service

```ini
[Unit]
Description=JuniperData — Dataset Generation Service (Port 8100)
Documentation=https://github.com/your-org/juniper-data
After=network-online.target
PartOf=juniper.target

[Service]
Type=exec
WorkingDirectory=/home/pcalnon/Development/python/Juniper/juniper-data
EnvironmentFile=/home/pcalnon/Development/python/Juniper/juniper-deploy/conf/juniper.env
ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m juniper_data \
    --host ${JUNIPER_DATA_HOST} \
    --port ${JUNIPER_DATA_PORT} \
    --log-level ${JUNIPER_DATA_LOG_LEVEL}
ExecStartPost=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/wait_for_health.sh \
    http://localhost:8100/v1/health 30

Restart=on-failure
RestartSec=5
WatchdogSec=60

# Resource Accounting
CPUAccounting=true
MemoryAccounting=true
IOAccounting=true
MemoryMax=2G
CPUQuota=200%

# Security Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/pcalnon/Development/python/Juniper/juniper-data/data
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=juniper-data

[Install]
WantedBy=juniper.target
```

**Key directives explained**:

| Directive               | Purpose                                                                                                                                          |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `Type=exec`             | Modern replacement for `Type=simple`. Process is tracked precisely (requires systemd >= 240)                                                     |
| `EnvironmentFile=`      | Loads environment variables from a shared file (not committed to git)                                                                            |
| `ExecStartPost=`        | Runs after `ExecStart` — waits for the health endpoint to respond, ensuring the service is actually ready before systemd marks it as started     |
| `Restart=on-failure`    | Auto-restart on non-zero exit codes. Does not restart on `systemctl stop`                                                                        |
| `RestartSec=5`          | 5-second delay between restart attempts (prevents tight restart loops)                                                                           |
| `WatchdogSec=60`        | systemd sends SIGABRT if the service doesn't ping the watchdog within 60s. Requires `sd_notify` integration in the application (see Section 2.5) |
| `CPUAccounting=true`    | Enables per-service CPU usage tracking via cgroups v2                                                                                            |
| `MemoryMax=2G`          | Hard memory limit — OOM killer terminates the service if exceeded                                                                                |
| `CPUQuota=200%`         | Allows up to 2 CPU cores (200% of one core)                                                                                                      |
| `ProtectSystem=strict`  | Mounts `/usr`, `/boot`, `/efi` read-only                                                                                                         |
| `ProtectHome=read-only` | Mounts `/home` read-only except `ReadWritePaths`                                                                                                 |
| `ReadWritePaths=`       | Whitelists specific directories for write access                                                                                                 |
| `PrivateTmp=true`       | Private `/tmp` namespace (other services cannot read this service's temp files)                                                                  |
| `SyslogIdentifier=`     | Tag for `journalctl -t juniper-data` filtering                                                                                                   |

#### juniper-cascor.service

```ini
[Unit]
Description=JuniperCascor — Cascade Correlation Training Service (Port 8200)
Documentation=https://github.com/your-org/juniper-cascor
After=network-online.target juniper-data.service
Requires=juniper-data.service
PartOf=juniper.target

[Service]
Type=exec
WorkingDirectory=/home/pcalnon/Development/python/Juniper/juniper-cascor
EnvironmentFile=/home/pcalnon/Development/python/Juniper/juniper-deploy/conf/juniper.env
Environment=PYTHONPATH=/home/pcalnon/Development/python/Juniper/juniper-cascor/src
ExecStartPre=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/wait_for_health.sh \
    http://localhost:8100/v1/health 30
ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python src/server.py
ExecStartPost=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/wait_for_health.sh \
    http://localhost:8200/v1/health 30

Restart=on-failure
RestartSec=5
WatchdogSec=60

# Resource Accounting
CPUAccounting=true
MemoryAccounting=true
IOAccounting=true
MemoryMax=8G
CPUQuota=400%

# Security Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/pcalnon/Development/python/Juniper/juniper-cascor/logs
ReadWritePaths=/home/pcalnon/Development/python/Juniper/juniper-cascor/data
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=juniper-cascor

[Install]
WantedBy=juniper.target
```

**Notable differences from juniper-data**:

| Directive                       | Reason                                                                   |
|---------------------------------|--------------------------------------------------------------------------|
| `After=juniper-data.service`    | Ensures JuniperData starts first                                         |
| `Requires=juniper-data.service` | If JuniperData stops, JuniperCascor is also stopped                      |
| `ExecStartPre=`                 | Blocks startup until JuniperData is healthy (dependency health gate)     |
| `MemoryMax=8G`                  | ML training requires significantly more memory                           |
| `CPUQuota=400%`                 | Allows up to 4 CPU cores for training workloads                          |
| `PYTHONPATH`                    | Required because CasCor's entry point is `src/server.py` (not a package) |

#### juniper-canopy.service

```ini
[Unit]
Description=JuniperCanopy — Real-Time Monitoring Dashboard (Port 8050)
Documentation=https://github.com/your-org/juniper-canopy
After=network-online.target juniper-data.service juniper-cascor.service
Requires=juniper-data.service
Wants=juniper-cascor.service
PartOf=juniper.target

[Service]
Type=exec
WorkingDirectory=/home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy
EnvironmentFile=/home/pcalnon/Development/python/Juniper/juniper-deploy/conf/juniper.env
Environment=PYTHONPATH=/home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy/src
ExecStartPre=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/wait_for_health.sh \
    http://localhost:8100/v1/health 30
ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python src/main.py
ExecStartPost=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/wait_for_health.sh \
    http://localhost:8050/v1/health 30

Restart=on-failure
RestartSec=5
WatchdogSec=60

# Resource Accounting
CPUAccounting=true
MemoryAccounting=true
IOAccounting=true
MemoryMax=2G
CPUQuota=200%

# Security Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy/logs
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=juniper-canopy

[Install]
WantedBy=juniper.target
```

**Notable differences**:

| Directive                         | Reason                                                                                                    |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------|
| `Requires=juniper-data.service`   | Hard dependency — Canopy cannot function without dataset service                                          |
| `Wants=juniper-cascor.service`    | Soft dependency — Canopy can fall back to demo mode if CasCor is unavailable                              |
| `After=...juniper-cascor.service` | Start ordering (waits for CasCor) but doesn't fail if CasCor is missing due to `Wants=` (not `Requires=`) |

### 2.5 Health Monitoring Integration

#### wait_for_health.sh

A reusable script called by `ExecStartPre` and `ExecStartPost` to block until a health endpoint responds.

```bash
#!/usr/bin/env bash
# Usage: wait_for_health.sh <url> <timeout_seconds>
# Exit 0 if healthy within timeout, exit 1 otherwise.

URL="$1"
TIMEOUT="${2:-30}"
ELAPSED=0

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    if python3 -c "import urllib.request; urllib.request.urlopen('${URL}', timeout=3)" 2>/dev/null; then
        exit 0
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "TIMEOUT: ${URL} not healthy after ${TIMEOUT}s" >&2
exit 1
```

#### Health Timer Units

Each service gets a timer that periodically runs a health check and logs the result to the journal. This provides a continuous health record viewable via `journalctl`.

**juniper-data-health.timer**:

```ini
[Unit]
Description=Periodic health check for JuniperData
PartOf=juniper.target

[Timer]
OnActiveSec=30
OnUnitActiveSec=30
AccuracySec=5

[Install]
WantedBy=juniper.target
```

**juniper-data-health.service** (one-shot, triggered by timer):

```ini
[Unit]
Description=Health check for JuniperData

[Service]
Type=oneshot
ExecStart=/home/pcalnon/Development/python/Juniper/juniper-deploy/scripts/health_check_systemd.sh \
    juniper-data http://localhost:8100/v1/health/ready
```

**health_check_systemd.sh**:

```bash
#!/usr/bin/env bash
# Usage: health_check_systemd.sh <service_name> <health_url>
# Logs health status to journal (stdout captured by systemd)

SERVICE="$1"
URL="$2"

RESPONSE=$(python3 -c "
import urllib.request, json, time
start = time.monotonic()
try:
    resp = urllib.request.urlopen('${URL}', timeout=5)
    data = json.loads(resp.read())
    elapsed_ms = int((time.monotonic() - start) * 1000)
    print(json.dumps({'service': '${SERVICE}', 'status': data.get('status', 'unknown'),
                       'latency_ms': elapsed_ms, 'healthy': True}))
except Exception as e:
    print(json.dumps({'service': '${SERVICE}', 'error': str(e), 'healthy': False}))
" 2>&1)

echo "$RESPONSE"

# Exit non-zero if unhealthy (triggers OnFailure= if configured)
echo "$RESPONSE" | python3 -c "import sys, json; sys.exit(0 if json.load(sys.stdin).get('healthy') else 1)"
```

#### sd_notify Watchdog Integration (Optional Enhancement)

For services that implement `sd_notify` (systemd watchdog protocol), systemd can detect hangs — not just crashes. This requires a small application-level change.

**FastAPI lifespan integration** (conceptual — applies to all three services):

```python
# In each service's lifespan or background task
import os
import socket

def notify_watchdog():
    """Notify systemd watchdog that the service is alive."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return  # Not running under systemd
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.connect(addr)
    sock.sendall(b"WATCHDOG=1")
    sock.close()

# Called periodically (e.g., every 30s) from a background task
# WatchdogSec=60 means systemd expects a ping at least every 60s
```

This is an optional enhancement. Without it, `WatchdogSec=` should be removed from the unit files (systemd will only detect process crashes, not hangs).

### 2.6 Performance Monitoring

systemd's cgroup integration provides zero-overhead resource accounting when `CPUAccounting=true`, `MemoryAccounting=true`, and `IOAccounting=true` are set.

**Viewing resource usage**:

```bash
# Current resource usage for a specific service
systemctl --user status juniper-cascor.service
# Shows: CPU, Memory, Tasks (threads), CGroup tree

# Detailed cgroup stats
systemctl --user show juniper-cascor.service \
    --property=CPUUsageNSec,MemoryCurrent,MemoryPeak,IOReadBytes,IOWriteBytes

# Historical resource usage (requires systemd-cgtop or custom logging)
systemd-cgtop -m
```

**Resource limit recommendations**:

| Service        | MemoryMax | CPUQuota       | Rationale                                               |
|----------------|-----------|----------------|---------------------------------------------------------|
| juniper-data   | 2G        | 200% (2 cores) | Dataset generation is I/O-bound, moderate CPU for NumPy |
| juniper-cascor | 8G        | 400% (4 cores) | ML training is compute- and memory-intensive            |
| juniper-canopy | 2G        | 200% (2 cores) | Dashboard is I/O-bound (WebSocket, HTTP)                |

These limits are starting points. Tune based on observed usage via `systemctl show --property=MemoryPeak`.

### 2.7 Management Scripts

#### juniper-ctl

A management CLI that wraps common `systemctl --user` operations:

```bash
#!/usr/bin/env bash
# juniper-ctl — Management interface for Juniper systemd services
# Usage: juniper-ctl <command> [service]

SERVICES="juniper-data juniper-cascor juniper-canopy"

case "$1" in
    start)
        systemctl --user start juniper.target
        ;;
    stop)
        systemctl --user stop juniper.target
        ;;
    restart)
        if [ -n "$2" ]; then
            systemctl --user restart "juniper-${2}.service"
        else
            systemctl --user restart $SERVICES
        fi
        ;;
    status)
        for svc in $SERVICES; do
            systemctl --user status "$svc.service" --no-pager -l
            echo "---"
        done
        ;;
    logs)
        if [ -n "$2" ]; then
            journalctl --user -u "juniper-${2}.service" -f
        else
            journalctl --user -u "juniper-data" -u "juniper-cascor" -u "juniper-canopy" -f
        fi
        ;;
    health)
        for svc in $SERVICES; do
            journalctl --user -u "${svc}-health.service" -n 1 --no-pager -o cat
        done
        ;;
    resources)
        for svc in $SERVICES; do
            echo "=== $svc ==="
            systemctl --user show "$svc.service" \
                --property=CPUUsageNSec,MemoryCurrent,MemoryPeak,IOReadBytes,IOWriteBytes
        done
        ;;
    install)
        # Symlink unit files into systemd user directory
        UNIT_DIR="$HOME/.config/systemd/user"
        mkdir -p "$UNIT_DIR"
        SCRIPT_DIR="$(cd "$(dirname "$0")/../systemd/user" && pwd)"
        for f in "$SCRIPT_DIR"/*; do
            ln -sf "$f" "$UNIT_DIR/$(basename "$f")"
        done
        systemctl --user daemon-reload
        echo "Units installed and reloaded."
        ;;
    enable)
        systemctl --user enable juniper.target
        ;;
    disable)
        systemctl --user disable juniper.target
        ;;
    *)
        echo "Usage: juniper-ctl {start|stop|restart|status|logs|health|resources|install|enable|disable} [service]"
        exit 1
        ;;
esac
```

### 2.8 Implementation Tasks

| #    | Task                                                                                                          | Files         | Depends On    |
|------|---------------------------------------------------------------------------------------------------------------|---------------|---------------|
| 2.1  | Create `juniper-deploy/systemd/user/juniper.target`                                                           | 1 unit file   | —             |
| 2.2  | Create `juniper-deploy/systemd/user/juniper-data.service` with resource limits and security hardening         | 1 unit file   | 2.1           |
| 2.3  | Create `juniper-deploy/systemd/user/juniper-cascor.service` with dependency on juniper-data                   | 1 unit file   | 2.1           |
| 2.4  | Create `juniper-deploy/systemd/user/juniper-canopy.service` with soft dependency on juniper-cascor            | 1 unit file   | 2.1           |
| 2.5  | Create `juniper-deploy/scripts/wait_for_health.sh` — reusable health wait script                              | 1 script      | —             |
| 2.6  | Create health timer + one-shot service for each service (6 unit files total)                                  | 6 unit files  | 2.2, 2.3, 2.4 |
| 2.7  | Create `juniper-deploy/scripts/health_check_systemd.sh` — health check script for timer units                 | 1 script      | —             |
| 2.8  | Create `juniper-deploy/conf/juniper.env` — shared environment file for all services                           | 1 config file | —             |
| 2.9  | Create `juniper-deploy/scripts/juniper-ctl` — management CLI                                                  | 1 script      | 2.1-2.7       |
| 2.10 | Create `juniper-deploy/systemd/install.sh` — installs units via symlinks + daemon-reload                      | 1 script      | 2.1-2.6       |
| 2.11 | Enable user lingering: `loginctl enable-linger pcalnon`                                                       | system config | —             |
| 2.12 | Validate full lifecycle: `juniper-ctl install && juniper-ctl start && juniper-ctl health && juniper-ctl stop` | —             | 2.1-2.10      |
| 2.13 | Validate resource monitoring: `juniper-ctl resources` shows CPU/memory for each service                       | —             | 2.12          |
| 2.14 | Add systemd section to `juniper-deploy/README.md`                                                             | docs          | 2.12          |

### 2.9 Verification Procedure

```bash
# 1. Install unit files
juniper-deploy/scripts/juniper-ctl install

# 2. Verify units are recognized
systemctl --user list-unit-files 'juniper*'
# Expected: 10 unit files (3 services + 1 target + 6 health timer/service pairs)

# 3. Start all services
juniper-deploy/scripts/juniper-ctl start

# 4. Verify startup order (check journal timestamps)
journalctl --user -u juniper-data -u juniper-cascor -u juniper-canopy \
    --since "1 minute ago" --no-pager -o short-iso
# Expected: juniper-data starts first, cascor after data healthy, canopy last

# 5. Check all services are active
juniper-deploy/scripts/juniper-ctl status
# Expected: All three services show "active (running)"

# 6. Verify health monitoring
sleep 35  # Wait for first health timer to fire
juniper-deploy/scripts/juniper-ctl health
# Expected: JSON health reports for each service

# 7. Verify resource accounting
juniper-deploy/scripts/juniper-ctl resources
# Expected: Non-zero CPU and memory values for each service

# 8. Test auto-restart
kill -9 $(systemctl --user show juniper-data.service --property=MainPID --value)
sleep 10
systemctl --user is-active juniper-data.service
# Expected: "active" (restarted automatically)

# 9. Test dependency behavior
systemctl --user stop juniper-data.service
systemctl --user is-active juniper-cascor.service
# Expected: "inactive" (stopped because Requires=juniper-data.service)

# 10. Clean stop
juniper-deploy/scripts/juniper-ctl stop
```

### 2.10 Security Considerations

| Concern                                             | Mitigation                                                                                                                                   |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Services run as login user with full home access    | `ProtectHome=read-only` + `ReadWritePaths=` whitelists only directories each service needs                                                   |
| Service can install packages or modify system files | `ProtectSystem=strict` makes `/usr`, `/boot`, `/efi` read-only                                                                               |
| Child processes can escalate privileges             | `NoNewPrivileges=true` prevents SUID/SGID execution                                                                                          |
| Private temp files visible to other services        | `PrivateTmp=true` gives each service its own `/tmp`                                                                                          |
| Environment file contains secrets                   | `juniper.env` is in `.gitignore`. File permissions: `chmod 600 juniper.env`. Consider `systemd-creds` for encrypted secrets (systemd >= 250) |
| Watchdog timeout causes SIGABRT core dump           | Set `LimitCORE=0` to disable core dumps, or `CoredumpFilter=0` to minimize dump content                                                      |

**Advanced hardening** (optional, for production):

```ini
# Restrict system calls to a safe allowlist
SystemCallFilter=@system-service @network-io @signal
SystemCallErrorNumber=EPERM

# Restrict capabilities to none
CapabilityBoundingSet=

# Restrict address families
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# Restrict namespace creation
RestrictNamespaces=true
```

### 2.11 Performance Considerations

| Concern                        | Impact                                                                | Mitigation                                                                               |
|--------------------------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Zero containerization overhead | Processes run natively — best possible latency and throughput         | This is the primary advantage of systemd over Docker                                     |
| Native GPU access              | No GPU passthrough layer. CUDA/cuDNN libraries are directly available | Ideal for JuniperCascor training workloads                                               |
| cgroup resource accounting     | Negligible overhead (<0.1% CPU) when accounting is enabled            | Always enable — the monitoring value far outweighs the cost                              |
| Memory limits (MemoryMax)      | OOM killer terminates the service if exceeded                         | Set conservative initial limits and tune based on `MemoryPeak` observations              |
| Health timer overhead          | One Python process every 30s per service (~50ms each)                 | Negligible. Total: 3 short-lived processes per 30s cycle                                 |
| Journal logging                | journald is highly efficient, rate-limited by default                 | No special tuning needed. Use `journalctl --vacuum-size=500M` if disk space is a concern |

---

## Phase 3: Docker Compose Profiles (Near-Term)

### 3.1 Objectives

- Extend the Phase 1 Docker Compose file with profiles for distinct operational modes
- Provide one-command startup for each use case: development, demo, full training, integration testing
- Add an observability stack (log aggregation, metrics) as an optional profile
- Introduce Docker network segmentation (frontend/backend networks)
- Implement Docker secrets for sensitive configuration
- Update the Makefile with profile-aware targets

### 3.2 Prerequisites

All Phase 1 prerequisites, plus:

| Requirement      | Version | Verification                                    |
|------------------|---------|-------------------------------------------------|
| Phase 1 complete | —       | `make status` works in `juniper-deploy/`        |
| Docker BuildKit  | enabled | `DOCKER_BUILDKIT=1` or Docker >= 23.0 (default) |

### 3.3 Profile Architecture

Profiles define which services start for each use case. A service can belong to multiple profiles.

| Profile   | Services Started                                          | Use Case                                                    |
|-----------|-----------------------------------------------------------|-------------------------------------------------------------|
| `dev`     | juniper-data, juniper-canopy (demo mode)                  | Frontend development — no backend needed                    |
| `demo`    | juniper-data, juniper-cascor (auto-train), juniper-canopy | Stakeholder demonstration with real (auto-started) training |
| `full`    | juniper-data, juniper-cascor, juniper-canopy              | Real training with manual control                           |
| `test`    | juniper-data, juniper-cascor, juniper-canopy, test-runner | Integration test suite                                      |
| `monitor` | (adds to any) prometheus, grafana                         | Observability stack                                         |

**Startup commands**:

```bash
make dev          # docker compose --profile dev up -d
make demo         # docker compose --profile demo up -d
make full         # docker compose --profile full up -d
make test         # docker compose --profile test up
make monitor      # docker compose --profile full --profile monitor up -d
```

### 3.4 Compose File Design

The Phase 3 Compose file evolves the Phase 1 file. All existing service definitions are preserved; profiles and new services are added.

**Service-to-profile mapping**:

```yaml
services:
  juniper-data:
    profiles: [dev, demo, full, test]
    # ... (unchanged from Phase 1)

  juniper-cascor:
    profiles: [demo, full, test]
    # ... (unchanged from Phase 1)

  juniper-cascor-demo:
    profiles: [demo]
    # Same image as juniper-cascor but with auto-training env vars
    build:
      context: ../juniper-cascor
    environment:
      CASCOR_AUTO_TRAIN: "true"
      CASCOR_DEMO_DATASET: "two_spiral"
      CASCOR_DEMO_EPOCHS: "200"
      JUNIPER_DATA_URL: http://juniper-data:8100
    depends_on:
      juniper-data:
        condition: service_healthy

  juniper-canopy:
    profiles: [full, test]
    # ... (unchanged — connects to real cascor)

  juniper-canopy-dev:
    profiles: [dev]
    # Canopy in demo mode — no cascor dependency
    build:
      context: ../JuniperCanopy/juniper_canopy
    environment:
      CASCOR_DEMO_MODE: "1"
      JUNIPER_DATA_URL: http://juniper-data:8100
    depends_on:
      juniper-data:
        condition: service_healthy
    ports:
      - "8050:8050"

  juniper-canopy-demo:
    profiles: [demo]
    # Canopy in service mode pointing to demo cascor
    build:
      context: ../JuniperCanopy/juniper_canopy
    environment:
      CASCOR_SERVICE_URL: http://juniper-cascor-demo:8200
      JUNIPER_DATA_URL: http://juniper-data:8100
    depends_on:
      juniper-data:
        condition: service_healthy
      juniper-cascor-demo:
        condition: service_healthy
    ports:
      - "8050:8050"

  test-runner:
    profiles: [test]
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      JUNIPER_DATA_URL: http://juniper-data:8100
      CASCOR_SERVICE_URL: http://juniper-cascor:8200
      CANOPY_URL: http://juniper-canopy:8050
    depends_on:
      juniper-data:
        condition: service_healthy
      juniper-cascor:
        condition: service_healthy
      juniper-canopy:
        condition: service_healthy
    # Runs integration tests and exits
    command: pytest tests/integration/ -v --tb=short

  # Observability (optional)
  prometheus:
    profiles: [monitor]
    image: prom/prometheus:latest
    volumes:
      - ./conf/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    profiles: [monitor]
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./conf/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./conf/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  grafana-data:
```

### 3.5 Network Topology

Separate Docker networks prevent unnecessary communication between services that don't need to interact directly.

```yaml
networks:
  backend:
    # JuniperData + JuniperCascor + workers
    driver: bridge
  frontend:
    # JuniperCanopy + JuniperCascor (Canopy needs to reach CasCor)
    driver: bridge
  monitoring:
    # Prometheus + Grafana
    driver: bridge

services:
  juniper-data:
    networks: [backend]

  juniper-cascor:
    networks: [backend, frontend]   # Bridge: reachable from both Canopy and Data

  juniper-canopy:
    networks: [frontend]

  prometheus:
    networks: [backend, frontend, monitoring]  # Scrapes all services

  grafana:
    networks: [monitoring]
```

**Security benefit**: JuniperCanopy cannot directly reach JuniperData on the `backend` network. All data requests from Canopy go through JuniperCascor (or via the `juniper-data-client` if explicitly connected to `backend`). This enforces the intended dependency graph.

**Note**: If JuniperCanopy needs direct access to JuniperData (the current architecture has Canopy using `juniper-data-client` directly), add it to the `backend` network as well. The network design should reflect the actual dependency graph:

```yaml
  juniper-canopy:
    networks: [backend, frontend]  # If Canopy directly calls JuniperData
```

### 3.6 Volume Strategy

```yaml
volumes:
  # Named volumes for persistent data
  juniper-data-datasets:     # Dataset storage (/app/data/datasets in JuniperData)
  juniper-cascor-snapshots:  # HDF5 network snapshots
  juniper-cascor-logs:       # Training logs
  grafana-data:              # Grafana dashboards and state

services:
  juniper-data:
    volumes:
      - juniper-data-datasets:/app/data/datasets

  juniper-cascor:
    volumes:
      - juniper-cascor-snapshots:/app/data
      - juniper-cascor-logs:/app/logs

  # Development overrides (bind mounts for hot reload):
  # Use docker-compose.override.yml for these
```

**`docker-compose.override.yml`** (development bind mounts, not committed):

```yaml
services:
  juniper-data:
    volumes:
      - ../juniper-data/juniper_data:/app/juniper_data:ro
    command: ["python", "-m", "juniper_data", "--reload"]

  juniper-cascor:
    volumes:
      - ../juniper-cascor/src:/app/src:ro

  juniper-canopy:
    volumes:
      - ../JuniperCanopy/juniper_canopy/src:/app/src:ro
```

### 3.7 Secrets Management

Docker Compose secrets provide a more secure alternative to environment variables for sensitive values (API keys, tokens).

```yaml
secrets:
  juniper_data_api_key:
    file: ./secrets/juniper_data_api_key.txt
  cascor_sentry_dsn:
    file: ./secrets/cascor_sentry_dsn.txt

services:
  juniper-data:
    secrets:
      - juniper_data_api_key
    environment:
      # Application reads from /run/secrets/juniper_data_api_key
      JUNIPER_DATA_API_KEY_FILE: /run/secrets/juniper_data_api_key

  juniper-cascor:
    secrets:
      - juniper_data_api_key
      - cascor_sentry_dsn
```

**Application-side change required**: Services currently read API keys from environment variables. To support Docker secrets, add fallback logic:

```python
# In Settings class or equivalent
import os
from pathlib import Path

def get_secret(env_var: str, file_env_var: str | None = None) -> str | None:
    """Read secret from env var, or from file path in a _FILE env var."""
    if file_env_var and (file_path := os.environ.get(file_env_var)):
        return Path(file_path).read_text().strip()
    return os.environ.get(env_var)
```

**Secrets directory** (never committed):

```bash
juniper-deploy/
├── secrets/                    # .gitignore'd
│   ├── juniper_data_api_key.txt
│   └── cascor_sentry_dsn.txt
└── secrets.example/            # Committed — documents required secrets
    ├── juniper_data_api_key.txt  # Contains: "replace-with-real-key"
    └── cascor_sentry_dsn.txt     # Contains: "replace-with-real-dsn"
```

### 3.8 Observability Stack

#### Prometheus Configuration

**`juniper-deploy/conf/prometheus.yml`**:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'juniper-data'
    metrics_path: '/v1/metrics'    # Requires adding /v1/metrics endpoint
    static_configs:
      - targets: ['juniper-data:8100']

  - job_name: 'juniper-cascor'
    metrics_path: '/v1/metrics'
    static_configs:
      - targets: ['juniper-cascor:8200']

  - job_name: 'juniper-canopy'
    metrics_path: '/v1/metrics'
    static_configs:
      - targets: ['juniper-canopy:8050']

  # Health probes (blackbox exporter alternative — simple HTTP check)
  - job_name: 'juniper-health'
    metrics_path: '/probe'
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - 'http://juniper-data:8100/v1/health/ready'
          - 'http://juniper-cascor:8200/v1/health/ready'
          - 'http://juniper-canopy:8050/v1/health'
```

**Note**: Adding `/v1/metrics` endpoints to each service requires application changes (e.g., `prometheus-fastapi-instrumentator` package). This is an optional enhancement. Prometheus can still scrape health endpoints for uptime monitoring without application changes.

#### Grafana Dashboard Provisioning

**`juniper-deploy/conf/grafana/datasources/prometheus.yml`**:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### 3.9 Implementation Tasks

| #    | Task                                                                                     | Files                           | Depends On |
|------|------------------------------------------------------------------------------------------|---------------------------------|------------|
| 3.1  | Add `profiles:` to all existing service definitions in `docker-compose.yml`              | `docker-compose.yml`            | Phase 1    |
| 3.2  | Add `juniper-cascor-demo` service definition with auto-training env vars                 | `docker-compose.yml`            | 3.1        |
| 3.3  | Add `juniper-canopy-dev` service definition with `CASCOR_DEMO_MODE=1`                    | `docker-compose.yml`            | 3.1        |
| 3.4  | Add `juniper-canopy-demo` service definition pointing to demo cascor                     | `docker-compose.yml`            | 3.2        |
| 3.5  | Define `backend`, `frontend`, `monitoring` networks and assign to services               | `docker-compose.yml`            | 3.1        |
| 3.6  | Define named volumes for persistent data                                                 | `docker-compose.yml`            | 3.1        |
| 3.7  | Create `docker-compose.override.yml.example` with dev bind mounts                        | 1 file                          | 3.1        |
| 3.8  | Add secrets definitions and `secrets.example/` directory                                 | `docker-compose.yml`, directory | 3.1        |
| 3.9  | Add `prometheus` and `grafana` services under `monitor` profile                          | `docker-compose.yml`            | 3.5        |
| 3.10 | Create `conf/prometheus.yml` with scrape targets for all Juniper services                | 1 config file                   | 3.9        |
| 3.11 | Create `conf/grafana/datasources/prometheus.yml` for Grafana provisioning                | 1 config file                   | 3.9        |
| 3.12 | Update Makefile with profile-aware targets: `dev`, `demo`, `full`, `test`, `monitor`     | `Makefile`                      | 3.1-3.4    |
| 3.13 | Create `Dockerfile.test` for the `test-runner` service                                   | 1 Dockerfile                    | 3.1        |
| 3.14 | Validate all profiles: `make dev`, `make demo`, `make full`, `make test`, `make monitor` | —                               | 3.1-3.13   |
| 3.15 | Update `juniper-deploy/README.md` with profiles documentation                            | docs                            | 3.14       |

### 3.10 Verification Procedure

```bash
cd juniper-deploy

# 1. Dev profile (Canopy demo mode + JuniperData)
make dev
make wait
curl -sf http://localhost:8050/v1/health    # Canopy should be in demo mode
curl -sf http://localhost:8100/v1/health    # Data should be healthy
curl -sf http://localhost:8200/v1/health    # Should FAIL (cascor not started)
make down

# 2. Demo profile (all services, auto-training)
make demo
make wait
curl -sf http://localhost:8050/v1/health    # Canopy in service mode
curl -sf http://localhost:8200/v1/health    # Demo CasCor auto-training
# Verify training is running by checking WebSocket or metrics endpoint
make down

# 3. Full profile (all services, manual control)
make full
make wait
curl -sf http://localhost:8050/v1/health
curl -sf http://localhost:8200/v1/health
curl -sf http://localhost:8100/v1/health
make down

# 4. Monitor profile (full + Prometheus + Grafana)
make monitor
make wait
curl -sf http://localhost:9090/-/ready      # Prometheus
curl -sf http://localhost:3000/api/health   # Grafana
make down

# 5. Network isolation test
make full
# Verify Canopy can reach CasCor:
docker compose exec juniper-canopy python -c \
  "import urllib.request; print(urllib.request.urlopen('http://juniper-cascor:8200/v1/health').read())"
# Expected: Success
make down
```

### 3.11 Security Considerations

| Concern                                        | Mitigation                                                                                                                                  |
|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| Demo CasCor accessible in production           | Demo service only starts with `--profile demo`. Production uses `--profile full` which starts the real CasCor                               |
| Secrets in environment variables               | Docker secrets mount files at `/run/secrets/` (tmpfs) — never written to disk in the container, not visible in `docker inspect` environment |
| Cross-service network access                   | Docker networks segment traffic. Services only see peers on their assigned networks                                                         |
| Grafana default admin password                 | Change `GF_SECURITY_ADMIN_PASSWORD` in `.env` for any non-local deployment. Use Docker secrets for production                               |
| Prometheus scrape targets exposed              | Prometheus is on the `monitoring` network. In production, do not expose port 9090 externally                                                |
| CORS in production                             | Override `CORS_ORIGINS` per profile: `["http://localhost:8050"]` for full/demo, `["*"]` for dev only                                        |
| `docker-compose.override.yml` with bind mounts | Never commit override files. Add to `.gitignore`. Bind mounts give container write access to host source code — use `:ro` (read-only) flag  |

### 3.12 Performance Considerations

| Concern                                        | Impact                                                                | Mitigation                                                             |
|------------------------------------------------|-----------------------------------------------------------------------|------------------------------------------------------------------------|
| Multiple Canopy variants (dev, demo, full)     | Only one Canopy runs per profile — no waste                           | Profiles are mutually exclusive for port-bound services                |
| Prometheus scraping overhead                   | 3 HTTP requests every 15s                                             | Negligible. Increase `scrape_interval` to 30s if concerned             |
| Grafana memory usage                           | ~100-200 MB                                                           | Low impact. Only starts with `monitor` profile                         |
| Named volume I/O                               | Native performance on Linux (bind mount to volume driver)             | No performance concern                                                 |
| Demo CasCor auto-training CPU                  | Uses same resources as real training                                  | Set `cpus: 2.0` limit on demo CasCor to prevent dominating the machine |
| Image build time with multiple Canopy variants | All variants use the same Dockerfile (same image, different env vars) | No additional build time                                               |

---

## Phase 4: Kubernetes via k3s (Intermediate)

### 4.1 Objectives

- Deploy the full Juniper platform on Kubernetes using k3s (lightweight distribution)
- Implement Kubernetes-native health probes (liveness, readiness, startup)
- Enable horizontal pod autoscaling (HPA) for JuniperCascor workers
- Implement GPU scheduling for training workloads
- Provide Helm charts for repeatable, parameterized deployments
- Establish a path to managed Kubernetes (EKS, GKE, AKS) if needed

### 4.2 Prerequisites

| Requirement         | Version | Verification                                                                   |
|---------------------|---------|--------------------------------------------------------------------------------|
| k3s                 | >= 1.28 | `k3s --version`                                                                |
| kubectl             | >= 1.28 | `kubectl version --client`                                                     |
| Helm                | >= 3.12 | `helm version`                                                                 |
| Container images    | —       | Phase 1/3 Dockerfiles build images. Push to a registry or use k3s local import |
| NVIDIA GPU Operator | latest  | Only if GPU scheduling needed: `kubectl get pods -n gpu-operator`              |

**k3s installation** (single-node, development):

```bash
curl -sfL https://get.k3s.io | sh -
# k3s includes: containerd, CoreDNS, Traefik ingress, local-path-provisioner
# kubeconfig: /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

**Image availability**: k3s uses containerd, not Docker. Images built with Docker must be imported:

```bash
docker save juniper-data:latest | sudo k3s ctr images import -
docker save juniper-cascor:latest | sudo k3s ctr images import -
docker save juniper-canopy:latest | sudo k3s ctr images import -
```

Alternatively, push to a container registry (Docker Hub, GitHub Container Registry, or a local registry).

### 4.3 Cluster Architecture

```bash
┌───────────────────────────────────────────────────────────────────────┐
│                        k3s Cluster (Single Node)                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Namespace: juniper                            │ │
│  │                                                                  │ │
│  │   ┌───────────────┐  ┌────────────────┐  ┌─────────────────┐     │ │
│  │   │ Deployment    │  │ Deployment     │  │ Deployment      │     │ │
│  │   │ juniper-data  │  │ juniper-cascor │  │ juniper-canopy  │     │ │
│  │   │ Replicas: 1   │  │ Replicas: 1    │  │ Replicas: 1     │     │ │
│  │   └───────┬───────┘  └───────┬────────┘  └───────┬─────────┘     │ │
│  │           │                  │                   │               │ │
│  │   ┌───────▼───────┐  ┌───────▼────────┐  ┌───────▼─────────┐     │ │
│  │   │  Service      │  │  Service       │  │  Service        │     │ │
│  │   │  ClusterIP    │  │  ClusterIP     │  │  ClusterIP      │     │ │
│  │   │  :8100        │  │  :8200         │  │  :8050          │     │ │
│  │   └───────────────┘  └────────────────┘  └─────────────────┘     │ │
│  │                                                                  │ │
│  │   ┌───────────────────────────────────────────────────────┐      │ │
│  │   │  Ingress (Traefik)                                    │      │ │
│  │   │    juniper.local → juniper-canopy:8050                │      │ │
│  │   │    juniper.local/api/data → juniper-data:8100         │      │ │
│  │   │    juniper.local/api/cascor → juniper-cascor:8200     │      │ │
│  │   └───────────────────────────────────────────────────────┘      │ │
│  │                                                                  │ │
│  │   ┌──────────────┐  ┌────────────────────────┐                   │ │
│  │   │ ConfigMap    │  │  Secret                │                   │ │
│  │   │ juniper-env  │  │  juniper-secrets       │                   │ │
│  │   └──────────────┘  └────────────────────────┘                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Namespace: monitoring                         │ │
│  │            ┌───────────────┐  ┌────────────────┐                 │ │
│  │            │  Prometheus   │  │  Grafana       │                 │ │
│  │            └───────────────┘  └────────────────┘                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

### 4.4 Namespace Design

| Namespace      | Purpose                                            | Resources                                           |
|----------------|----------------------------------------------------|-----------------------------------------------------|
| `juniper`      | Application workloads                              | Deployments, Services, ConfigMaps, Secrets, Ingress |
| `monitoring`   | Observability stack                                | Prometheus, Grafana (optional Loki for logs)        |
| `gpu-operator` | NVIDIA GPU Operator (if GPU scheduling is enabled) | DaemonSets, device plugins                          |

```bash
kubectl create namespace juniper
kubectl create namespace monitoring
```

### 4.5 Manifest Specifications

#### JuniperData Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juniper-data
  namespace: juniper
  labels:
    app.kubernetes.io/name: juniper-data
    app.kubernetes.io/part-of: juniper
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: juniper-data
  template:
    metadata:
      labels:
        app.kubernetes.io/name: juniper-data
    spec:
      containers:
        - name: juniper-data
          image: juniper-data:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8100
              name: http
          envFrom:
            - configMapRef:
                name: juniper-data-config
            - secretRef:
                name: juniper-data-secrets
                optional: true
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: "2"
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 10
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /v1/health/ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12    # 5 + (5 * 12) = 65s max startup time
          volumeMounts:
            - name: data-storage
              mountPath: /app/data/datasets
      volumes:
        - name: data-storage
          persistentVolumeClaim:
            claimName: juniper-data-pvc
```

**Probe explanation**:

| Probe            | Purpose                                                                                                    | Behavior on Failure                                       |
|------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `startupProbe`   | Allows slow initial startup (up to 65s). While this probe is running, liveness and readiness are paused    | Pod is killed and restarted                               |
| `livenessProbe`  | Detects deadlocks/hangs after startup. If the process is alive but unresponsive, Kubernetes restarts it    | Pod is killed and restarted                               |
| `readinessProbe` | Gates traffic. If the service is temporarily overloaded, it stops receiving new requests until it recovers | Pod is removed from Service endpoints (no traffic routed) |

#### JuniperCascor Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juniper-cascor
  namespace: juniper
  labels:
    app.kubernetes.io/name: juniper-cascor
    app.kubernetes.io/part-of: juniper
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: juniper-cascor
  template:
    metadata:
      labels:
        app.kubernetes.io/name: juniper-cascor
    spec:
      initContainers:
        - name: wait-for-data
          image: busybox:1.36
          command: ['sh', '-c',
            'until wget -qO- http://juniper-data:8100/v1/health/ready; do sleep 2; done']
      containers:
        - name: juniper-cascor
          image: juniper-cascor:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8200
              name: http
          envFrom:
            - configMapRef:
                name: juniper-cascor-config
            - secretRef:
                name: juniper-cascor-secrets
                optional: true
          resources:
            requests:
              cpu: "1"
              memory: 1Gi
              # nvidia.com/gpu: 1    # Uncomment for GPU scheduling
            limits:
              cpu: "4"
              memory: 8Gi
              # nvidia.com/gpu: 1
          livenessProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 15
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /v1/health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 24   # 10 + (5 * 24) = 130s max (PyTorch load is slow)
          volumeMounts:
            - name: cascor-data
              mountPath: /app/data
            - name: cascor-logs
              mountPath: /app/logs
      volumes:
        - name: cascor-data
          persistentVolumeClaim:
            claimName: juniper-cascor-pvc
        - name: cascor-logs
          emptyDir: {}
```

**initContainers**: The `wait-for-data` init container blocks pod startup until JuniperData's readiness endpoint responds. This is the Kubernetes equivalent of Docker Compose's `depends_on: condition: service_healthy`.

#### JuniperCanopy Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juniper-canopy
  namespace: juniper
  labels:
    app.kubernetes.io/name: juniper-canopy
    app.kubernetes.io/part-of: juniper
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: juniper-canopy
  template:
    metadata:
      labels:
        app.kubernetes.io/name: juniper-canopy
    spec:
      initContainers:
        - name: wait-for-data
          image: busybox:1.36
          command: ['sh', '-c',
            'until wget -qO- http://juniper-data:8100/v1/health/ready; do sleep 2; done']
        - name: wait-for-cascor
          image: busybox:1.36
          command: ['sh', '-c',
            'until wget -qO- http://juniper-cascor:8200/v1/health/ready; do sleep 2; done']
      containers:
        - name: juniper-canopy
          image: juniper-canopy:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8050
              name: http
          envFrom:
            - configMapRef:
                name: juniper-canopy-config
            - secretRef:
                name: juniper-canopy-secrets
                optional: true
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: "2"
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 20
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /v1/health/ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /v1/health/live
              port: http
            initialDelaySeconds: 15
            periodSeconds: 5
            failureThreshold: 12
```

#### Service Definitions

```yaml
apiVersion: v1
kind: Service
metadata:
  name: juniper-data
  namespace: juniper
spec:
  selector:
    app.kubernetes.io/name: juniper-dat──a
  ports:
    - port: 8100
      targetPort: http
      protocol: TCP
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: juniper-cascor
  namespace: juniper
spec:
  selector:
    app.kubernetes.io/name: juniper-cascor
  ports:
    - port: 8200
      targetPort: http
      protocol: TCP
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: juniper-canopy
  namespace: juniper
spec:
  selector:
    app.kubernetes.io/name: juniper-canopy
  ports:
    - port: 8050
      targetPort: http
      protocol: TCP
  type: ClusterIP
```

#### ConfigMaps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: juniper-data-config
  namespace: juniper
data:
  JUNIPER_DATA_HOST: "0.0.0.0"
  JUNIPER_DATA_PORT: "8100"
  JUNIPER_DATA_LOG_LEVEL: "INFO"
  JUNIPER_DATA_STORAGE_PATH: "/app/data/datasets"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: juniper-cascor-config
  namespace: juniper
data:
  CASCOR_HOST: "0.0.0.0"
  CASCOR_PORT: "8200"
  CASCOR_LOG_LEVEL: "INFO"
  JUNIPER_DATA_URL: "http://juniper-data:8100"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: juniper-canopy-config
  namespace: juniper
data:
  CANOPY_HOST: "0.0.0.0"
  CANOPY_PORT: "8050"
  JUNIPER_DATA_URL: "http://juniper-data:8100"
  CASCOR_SERVICE_URL: "http://juniper-cascor:8200"
```

**Service discovery**: Kubernetes DNS resolves `juniper-data` to the ClusterIP of the `juniper-data` Service within the `juniper` namespace. The same `JUNIPER_DATA_URL=http://juniper-data:8100` pattern works identically to Docker Compose DNS — no application changes needed.

#### PersistentVolumeClaims

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: juniper-data-pvc
  namespace: juniper
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path    # k3s default provisioner
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: juniper-cascor-pvc
  namespace: juniper
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: local-path
  resources:
    requests:
      storage: 20Gi
```

### 4.6 Helm Chart Structure

A Helm chart parameterizes the manifests above for different environments (dev, staging, production).

```bash
juniper-deploy/
└── helm/
    └── juniper/
        ├── Chart.yaml
        ├── values.yaml                  # Default values
        ├── values-dev.yaml              # Dev overrides
        ├── values-demo.yaml             # Demo mode overrides
        ├── values-production.yaml       # Production overrides
        └── templates/
            ├── _helpers.tpl             # Template helpers
            ├── namespace.yaml
            ├── juniper-data/
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   ├── configmap.yaml
            │   └── pvc.yaml
            ├── juniper-cascor/
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   ├── configmap.yaml
            │   ├── pvc.yaml
            │   └── hpa.yaml             # HorizontalPodAutoscaler
            ├── juniper-canopy/
            │   ├── deployment.yaml
            │   ├── service.yaml
            │   └── configmap.yaml
            ├── ingress.yaml
            └── secrets.yaml
```

**`values.yaml`** (defaults):

```yaml
global:
  namespace: juniper
  imagePullPolicy: IfNotPresent

juniperData:
  enabled: true
  image:
    repository: juniper-data
    tag: latest
  replicas: 1
  resources:
    requests: { cpu: 250m, memory: 256Mi }
    limits: { cpu: "2", memory: 2Gi }
  storage:
    size: 10Gi
    storageClass: local-path
  config:
    host: "0.0.0.0"
    port: 8100
    logLevel: INFO

juniperCascor:
  enabled: true
  image:
    repository: juniper-cascor
    tag: latest
  replicas: 1
  resources:
    requests: { cpu: "1", memory: 1Gi }
    limits: { cpu: "4", memory: 8Gi }
  gpu:
    enabled: false
    count: 1
  autoscaling:
    enabled: false
    minReplicas: 1
    maxReplicas: 4
    targetCPUUtilization: 70
  storage:
    size: 20Gi
    storageClass: local-path
  config:
    host: "0.0.0.0"
    port: 8200
    logLevel: INFO

juniperCanopy:
  enabled: true
  image:
    repository: juniper-canopy
    tag: latest
  replicas: 1
  resources:
    requests: { cpu: 250m, memory: 256Mi }
    limits: { cpu: "2", memory: 2Gi }
  demoMode: false
  config:
    host: "0.0.0.0"
    port: 8050

ingress:
  enabled: true
  host: juniper.local
  tls: false
```

**Usage**:

```bash
# Install with defaults (full mode)
helm install juniper ./helm/juniper -n juniper

# Install with demo mode
helm install juniper ./helm/juniper -n juniper -f ./helm/juniper/values-demo.yaml

# Upgrade after changes
helm upgrade juniper ./helm/juniper -n juniper

# Uninstall
helm uninstall juniper -n juniper
```

### 4.7 Ingress and Networking

k3s ships with Traefik as the default ingress controller.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: juniper-ingress
  namespace: juniper
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  rules:
    - host: juniper.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: juniper-canopy
                port:
                  number: 8050
          - path: /api/data
            pathType: Prefix
            backend:
              service:
                name: juniper-data
                port:
                  number: 8100
          - path: /api/cascor
            pathType: Prefix
            backend:
              service:
                name: juniper-cascor
                port:
                  number: 8200
```

**Local development**: Add `127.0.0.1 juniper.local` to `/etc/hosts` to access the ingress.

**NetworkPolicy** (restrict inter-service communication):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: juniper-data-policy
  namespace: juniper
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: juniper-data
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: juniper-cascor
        - podSelector:
            matchLabels:
              app.kubernetes.io/name: juniper-canopy
      ports:
        - port: 8100
          protocol: TCP
```

This policy restricts JuniperData to only accept connections from JuniperCascor and JuniperCanopy pods — no other pods in the namespace (or cluster) can reach it.

### 4.8 Secret Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: juniper-data-secrets
  namespace: juniper
type: Opaque
stringData:
  JUNIPER_DATA_API_KEY: "replace-with-real-key"
---
apiVersion: v1
kind: Secret
metadata:
  name: juniper-cascor-secrets
  namespace: juniper
type: Opaque
stringData:
  SENTRY_DSN: "replace-with-real-dsn"
```

**Production considerations**:

- Do not commit Secret manifests with real values. Use `kubectl create secret` or Helm `--set` flags
- For managed Kubernetes, use external secret stores: AWS Secrets Manager, HashiCorp Vault, or Kubernetes External Secrets Operator
- Enable encryption at rest: `k3s server --secrets-encryption`

### 4.9 GPU Scheduling

k3s supports the NVIDIA GPU Operator for GPU workloads.

**Installation**:

```bash
# Install NVIDIA GPU Operator (handles driver, container runtime, device plugin)
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm install gpu-operator nvidia/gpu-operator -n gpu-operator --create-namespace
```

**JuniperCascor with GPU** (modify Deployment resources):

```yaml
resources:
  requests:
    cpu: "1"
    memory: 1Gi
    nvidia.com/gpu: 1
  limits:
    cpu: "4"
    memory: 8Gi
    nvidia.com/gpu: 1
```

**Dockerfile change required**: The JuniperCascor Dockerfile currently installs CPU-only PyTorch (`https://download.pytorch.org/whl/cpu`). For GPU support, use the CUDA wheel index:

```dockerfile
# GPU variant
RUN pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Consider maintaining two Dockerfile targets (or build args) for CPU and GPU variants.

### 4.10 Implementation Tasks

| #    | Task                                                                                                                            | Files                  | Depends On         |
|------|---------------------------------------------------------------------------------------------------------------------------------|------------------------|--------------------|
| 4.1  | Install k3s on the development machine                                                                                          | system                 | —                  |
| 4.2  | Create `juniper-deploy/k8s/` directory with raw manifest files (Deployments, Services, ConfigMaps, PVCs) for all three services | ~12 YAML files         | 4.1                |
| 4.3  | Create init containers for dependency ordering (`wait-for-data`, `wait-for-cascor`)                                             | deployment manifests   | 4.2                |
| 4.4  | Configure liveness, readiness, and startup probes for all services                                                              | deployment manifests   | 4.2                |
| 4.5  | Create Ingress manifest with Traefik routing rules                                                                              | `ingress.yaml`         | 4.2                |
| 4.6  | Create NetworkPolicy manifests restricting inter-service communication                                                          | `networkpolicy.yaml`   | 4.2                |
| 4.7  | Import Docker images into k3s: `docker save                                                                                     | k3s ctr images import` | —                  |
| 4.8  | Validate raw manifest deployment: `kubectl apply -f k8s/`                                                                       | —                      | 4.2-4.7            |
| 4.9  | Create Helm chart structure (`juniper-deploy/helm/juniper/`)                                                                    | chart skeleton         | 4.8                |
| 4.10 | Templatize all manifests into Helm templates with `values.yaml` parameterization                                                | templates              | 4.9                |
| 4.11 | Create `values-dev.yaml` (single replica, no GPU, relaxed resources)                                                            | 1 values file          | 4.10               |
| 4.12 | Create `values-demo.yaml` (Canopy demo mode or auto-training CasCor)                                                            | 1 values file          | 4.10               |
| 4.13 | Create `values-production.yaml` (GPU enabled, HPA, tighter resource limits)                                                     | 1 values file          | 4.10               |
| 4.14 | Validate Helm install: `helm install juniper ./helm/juniper -n juniper`                                                         | —                      | 4.10               |
| 4.15 | Test GPU scheduling (if NVIDIA GPU available): enable `gpu.enabled=true` in values                                              | —                      | 4.14, GPU Operator |
| 4.16 | Add Kubernetes section to `juniper-deploy/README.md`                                                                            | docs                   | 4.14               |
| 4.17 | Add `make k8s-up`, `make k8s-down`, `make k8s-status` targets to Makefile                                                       | Makefile               | 4.14               |

### 4.11 Verification Procedure

```bash
# 1. Verify k3s is running
kubectl get nodes
# Expected: Single node with STATUS "Ready"

# 2. Apply manifests (raw or Helm)
kubectl create namespace juniper
helm install juniper ./helm/juniper -n juniper
# OR: kubectl apply -f k8s/ -n juniper

# 3. Watch pod startup
kubectl get pods -n juniper -w
# Expected sequence:
#   juniper-data        Init:0/0 → Running → Ready
#   juniper-cascor      Init:0/1 → Init:1/1 → Running → Ready
#   juniper-canopy      Init:0/2 → Init:1/2 → Init:2/2 → Running → Ready

# 4. Verify services
kubectl get svc -n juniper
# Expected: Three ClusterIP services with correct ports

# 5. Port-forward for local access
kubectl port-forward -n juniper svc/juniper-canopy 8050:8050 &
kubectl port-forward -n juniper svc/juniper-data 8100:8100 &
curl -sf http://localhost:8050/v1/health
curl -sf http://localhost:8100/v1/health

# 6. Verify ingress (if configured)
curl -sf -H "Host: juniper.local" http://localhost/v1/health

# 7. Verify probes are working
kubectl describe pod -n juniper -l app.kubernetes.io/name=juniper-data
# Check Events section for probe success/failure

# 8. Test self-healing
kubectl delete pod -n juniper -l app.kubernetes.io/name=juniper-data
kubectl get pods -n juniper -w
# Expected: New pod created automatically, reaches Ready state

# 9. Test NetworkPolicy (if applied)
kubectl run -n juniper test-pod --rm -it --image=busybox -- wget -qO- http://juniper-data:8100/v1/health
# Expected: Success (pod in same namespace)

# 10. Uninstall
helm uninstall juniper -n juniper
kubectl delete namespace juniper
```

### 4.12 Security Considerations

| Concern                                         | Mitigation                                                                                                                                    |
|-------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| k3s default: no RBAC for default ServiceAccount | Create dedicated ServiceAccounts for each Deployment with minimal permissions. Set `automountServiceAccountToken: false` unless needed        |
| Container images with known CVEs                | Scan images with `trivy image juniper-data:latest`. Build from minimal base images (already using `python:3.12-slim`)                         |
| Secrets stored in etcd unencrypted              | Enable k3s secret encryption: `k3s server --secrets-encryption`. For production: use External Secrets Operator with Vault/AWS Secrets Manager |
| NetworkPolicy not enforced by default           | k3s uses Flannel CNI which supports NetworkPolicy. Verify with test pod connectivity                                                          |
| Ingress exposes services externally             | Use `annotations` to restrict access (IP allowlists, basic auth). For production: enable TLS with cert-manager                                |
| Pods can communicate across namespaces          | Apply default-deny NetworkPolicy per namespace, then allowlist specific traffic                                                               |
| Container runs as non-root                      | Already implemented in Dockerfiles (`USER juniper`). Add `securityContext` to pod spec for defense in depth                                   |

**Pod Security Context** (add to all Deployments):

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: ...
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: [ALL]
```

### 4.13 Performance Considerations

| Concern                       | Impact                                                                            | Mitigation                                                                                   |
|-------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| k3s control plane overhead    | ~500 MB-1 GB RAM, minimal CPU                                                     | Acceptable for a development machine. k3s is the lightest production Kubernetes distribution |
| Container startup time        | Same as Docker Compose + init container wait time                                 | Startup probes allow generous timeouts (65-130s) without failing liveness                    |
| GPU scheduling latency        | NVIDIA device plugin adds ~1s to pod scheduling                                   | Negligible for training workloads that run for minutes/hours                                 |
| Network overhead (kube-proxy) | iptables rules add ~0.1ms per hop for ClusterIP services                          | Negligible for HTTP/WebSocket traffic                                                        |
| PersistentVolume I/O          | k3s `local-path-provisioner` uses host filesystem — native performance            | For production: use CSI drivers for networked storage if multi-node                          |
| HPA scaling delay             | Default HPA loop: 15s. Pod startup: 30-60s. Total: ~45-75s to scale               | Acceptable for ML workloads. Pre-scale during peak times if latency-sensitive                |
| Image pull time               | Local import avoids registry pulls. On managed K8s: use registry close to cluster | `imagePullPolicy: IfNotPresent` avoids re-pulling unless tag changes                         |

---

## Modes of Operation — Overview

This section provides detailed implementation plans for the three-phase modes-of-operation strategy selected in [MICROSERVICES_ARCHITECTURE_ANALYSIS.md](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md), Section 3.5:

```bash
Phase 5 (Immediate):    Refactor DemoMode and CascorServiceAdapter behind a BackendProtocol
Phase 6 (Near-term):    Add FakeCascorClient and FakeDataClient to client libraries
Phase 7 (With Docker):  Add a demo profile to Docker Compose with auto-start configuration
```

### Current State Reference

JuniperCanopy operates in two mutually exclusive modes, controlled by environment variables:

```bash
Priority 1: CASCOR_DEMO_MODE=1      → Demo mode (explicit override)
Priority 2: CASCOR_SERVICE_URL set   → Service mode (REST/WS via CascorServiceAdapter)
Priority 3: Neither set              → Demo mode (default fallback)
```

| Component                 | Location (Legacy)                                        | Lines | Purpose                                               |
|---------------------------|----------------------------------------------------------|-------|-------------------------------------------------------|
| **DemoMode**              | `JuniperCanopy/juniper_canopy/src/demo_mode.py`         | ~1100 | In-process training simulation with synthetic data    |
| **MockCascorNetwork**     | `JuniperCanopy/juniper_canopy/src/demo_mode.py`         | ~80   | Simulated neural network for demo mode                |
| **CascorServiceAdapter**  | `JuniperCanopy/juniper_canopy/src/backend/cascor_service_adapter.py` | ~307  | REST/WS adapter wrapping `juniper-cascor-client`      |
| **Mode selection logic**  | `JuniperCanopy/juniper_canopy/src/main.py`              | ~40+  | Scattered `if demo_mode_instance:` / `if backend:` branching |

### Problem Statement

The current `main.py` contains **40+ conditional branches** that check `demo_mode_instance` or `backend` before dispatching to the appropriate implementation. This pattern:

- Increases cognitive load and maintenance burden
- Makes it easy to add a feature to one mode but forget the other
- Prevents the compiler/type checker from verifying both implementations satisfy the same contract
- Makes unit testing of route handlers dependent on the active mode
- Will not scale if additional modes are added (e.g., recording/replay, offline analysis)

### Modes of Operation Dependency Chain

```bash
Phase 5: BackendProtocol Interface
    │
    ├── Phase 6: Client Library Fakes (depends on protocol for fake backend wiring)
    │
    └── Phase 7: Docker Compose Demo Profile (independent of Phase 5/6 — infrastructure only)
```

Phase 7 is infrastructure-only and can proceed in parallel with Phase 5/6. Phases 5 and 6 are sequential — Phase 6 builds on the protocol defined in Phase 5.

---

## Phase 5: BackendProtocol Interface Refactor (Immediate)

### 5.1 Objectives

- Define a `BackendProtocol` (`typing.Protocol`) that captures the full set of operations `main.py` calls on either `DemoMode` or `CascorServiceAdapter`
- Create a `DemoBackend` class that wraps `DemoMode` and conforms to `BackendProtocol`
- Create a `ServiceBackend` class that wraps `CascorServiceAdapter` and conforms to `BackendProtocol`
- Refactor `main.py` to hold a single `backend: BackendProtocol` reference, eliminating all `if demo_mode_instance:` / `if backend:` branching
- Ensure all 3,215+ existing tests pass without modification (demo mode is the default test backend)
- Enable type checking (`mypy`) to verify both implementations satisfy the protocol

### 5.2 Prerequisites

| Requirement                     | Version   | Verification                                               |
|---------------------------------|-----------|------------------------------------------------------------|
| Python                          | >= 3.12   | `python --version` (Protocol with `@runtime_checkable`)    |
| juniper-cascor-client           | >= 0.1.0  | `pip show juniper-cascor-client`                           |
| Existing test suite green       | —         | `cd src && pytest tests/ -v` (3,215 passed, 0 failed)     |
| mypy                            | >= 1.8    | `mypy --version`                                           |

### 5.3 Current Branching Analysis

The following operations are called on `demo_mode_instance` and/or `backend` in `main.py`, organized by functional category:

**Training control** (called from `/ws/control` handler and Dash callbacks):

| Operation                       | DemoMode Method               | CascorServiceAdapter Method        |
|---------------------------------|-------------------------------|------------------------------------|
| Start training                  | `start(reset=True)`          | `start_training_background()`      |
| Stop training                   | `stop()`                     | `request_training_stop()`          |
| Pause training                  | `pause()`                    | *(not yet implemented)*            |
| Resume training                 | `resume()`                   | *(not yet implemented)*            |
| Reset training                  | `reset()`                    | *(not yet implemented)*            |
| Check if training               | `get_current_state()["is_running"]` | `is_training_in_progress()`   |

**Status and metrics** (called from REST endpoints):

| Operation                       | DemoMode Method               | CascorServiceAdapter Method        |
|---------------------------------|-------------------------------|------------------------------------|
| Get current status              | `get_current_state()`        | `get_training_status()`            |
| Get metrics history             | `get_metrics_history()`      | `training_monitor.get_recent_metrics()` |
| Get current metrics             | `get_current_state()`        | `training_monitor.get_current_metrics()` |

**Network and data** (called from REST endpoints):

| Operation                       | DemoMode Method               | CascorServiceAdapter Method        |
|---------------------------------|-------------------------------|------------------------------------|
| Get network object              | `get_network()`              | `.network` (property)              |
| Get network topology            | *(derived from network)*     | `extract_network_topology()`       |
| Get network data/stats          | *(derived from network)*     | `get_network_data()`               |
| Get dataset                     | `get_dataset()`              | `get_dataset_info()`               |
| Get decision boundary           | *(computed from network)*    | `get_prediction_function()` → None |

**Lifecycle** (called from startup/shutdown):

| Operation                       | DemoMode Method               | CascorServiceAdapter Method        |
|---------------------------------|-------------------------------|------------------------------------|
| Initialize/connect              | `__init__()` + `start()`     | `connect()` (async)                |
| Shutdown                        | `stop()`                     | `shutdown()`                       |
| Training state machine          | `.state_machine` / `.training_state` | *(not applicable — managed by CasCor service)* |
| Apply parameter changes         | `apply_params()`             | *(not yet implemented)*            |

### 5.4 BackendProtocol Design

The protocol captures the **union** of all operations `main.py` needs, with methods returning consistent types regardless of implementation.

**Design principles**:

- Methods return `Dict[str, Any]` for status/metrics (JSON-serializable for REST responses)
- Training control methods return `bool` (success/failure) or `Dict` (new state)
- Network topology and dataset return `Optional[Dict]` (None when unavailable)
- The protocol does not expose internal details (`MockCascorNetwork`, `JuniperCascorClient`, etc.)
- Async methods are kept to a minimum — only where the service adapter genuinely requires async I/O

```python
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class BackendProtocol(Protocol):
    """
    Unified backend interface for JuniperCanopy.

    Both DemoBackend and ServiceBackend implement this protocol.
    Route handlers in main.py call these methods without knowing
    which backend is active.
    """

    # --- Training control ---

    def start_training(self, reset: bool = True, **kwargs: Any) -> Dict[str, Any]:
        """Start or restart training. Returns new training state."""
        ...

    def stop_training(self) -> Dict[str, Any]:
        """Stop training gracefully. Returns final state."""
        ...

    def pause_training(self) -> Dict[str, Any]:
        """Pause training (retaining state). Returns paused state."""
        ...

    def resume_training(self) -> Dict[str, Any]:
        """Resume paused training. Returns resumed state."""
        ...

    def reset_training(self) -> Dict[str, Any]:
        """Reset training to initial state. Returns reset state."""
        ...

    def is_training_active(self) -> bool:
        """Return True if training is currently in progress."""
        ...

    # --- Status and metrics ---

    def get_status(self) -> Dict[str, Any]:
        """Return current backend status (training state, phase, epoch, etc.)."""
        ...

    def get_metrics(self) -> Dict[str, Any]:
        """Return current training metrics snapshot."""
        ...

    def get_metrics_history(self, count: int = 100) -> List[Dict[str, Any]]:
        """Return recent training metrics history."""
        ...

    # --- Network and data ---

    def has_network(self) -> bool:
        """Return True if a neural network exists."""
        ...

    def get_network_topology(self) -> Optional[Dict[str, Any]]:
        """Return network topology for visualization, or None."""
        ...

    def get_network_stats(self) -> Dict[str, Any]:
        """Return network statistics (weights, unit counts, etc.)."""
        ...

    def get_dataset(self) -> Optional[Dict[str, Any]]:
        """Return current dataset info, or None."""
        ...

    def get_decision_boundary(self, resolution: int = 50) -> Optional[Dict[str, Any]]:
        """Return decision boundary grid data, or None if unavailable."""
        ...

    # --- Parameters ---

    def apply_params(self, **params: Any) -> Dict[str, Any]:
        """Apply training parameter changes. Returns updated params."""
        ...

    # --- Lifecycle ---

    async def initialize(self) -> bool:
        """Initialize the backend (connect, start simulation, etc.)."""
        ...

    async def shutdown(self) -> None:
        """Clean shutdown of the backend."""
        ...

    # --- Identity ---

    @property
    def backend_type(self) -> str:
        """Return 'demo' or 'service' for logging/status."""
        ...
```

### 5.5 DemoBackend Implementation

`DemoBackend` wraps the existing `DemoMode` class, adapting its interface to `BackendProtocol`.

**File**: `src/backend/demo_backend.py` (new)

**Design**:

- Delegates all operations to the existing `DemoMode` instance
- Adapts return values to the protocol's `Dict[str, Any]` convention
- No changes required to `demo_mode.py` itself — `DemoBackend` is a thin adapter
- The existing `training_state` / `state_machine` access is encapsulated within the adapter

```python
# Conceptual implementation sketch

class DemoBackend:
    """BackendProtocol implementation wrapping DemoMode."""

    def __init__(self, demo: DemoMode):
        self._demo = demo

    @property
    def backend_type(self) -> str:
        return "demo"

    def start_training(self, reset: bool = True, **kwargs) -> Dict[str, Any]:
        return self._demo.start(reset=reset)

    def stop_training(self) -> Dict[str, Any]:
        self._demo.stop()
        return self._demo.get_current_state()

    def pause_training(self) -> Dict[str, Any]:
        self._demo.pause()
        return self._demo.get_current_state()

    def resume_training(self) -> Dict[str, Any]:
        self._demo.resume()
        return self._demo.get_current_state()

    def reset_training(self) -> Dict[str, Any]:
        return self._demo.reset()

    def is_training_active(self) -> bool:
        return self._demo.get_current_state().get("is_running", False)

    def get_status(self) -> Dict[str, Any]:
        return self._demo.get_current_state()

    def get_metrics(self) -> Dict[str, Any]:
        return self._demo.get_current_state()

    def get_metrics_history(self, count: int = 100) -> List[Dict[str, Any]]:
        return self._demo.get_metrics_history()

    def has_network(self) -> bool:
        return self._demo.get_network() is not None

    def get_network_topology(self) -> Optional[Dict[str, Any]]:
        network = self._demo.get_network()
        if network is None:
            return None
        # Extract topology from MockCascorNetwork
        return {
            "input_size": network.input_size,
            "output_size": network.output_size,
            "hidden_units": len(network.hidden_units),
            "connections": [...]  # Derived from network structure
        }

    def get_network_stats(self) -> Dict[str, Any]:
        network = self._demo.get_network()
        state = self._demo.get_current_state()
        return {
            "hidden_units": len(network.hidden_units) if network else 0,
            "current_epoch": state.get("current_epoch", 0),
            **state
        }

    def get_dataset(self) -> Optional[Dict[str, Any]]:
        return self._demo.get_dataset()

    def get_decision_boundary(self, resolution: int = 50) -> Optional[Dict[str, Any]]:
        # Computed from MockCascorNetwork.forward() — existing demo logic
        ...

    def apply_params(self, **params) -> Dict[str, Any]:
        self._demo.apply_params(**params)
        return params

    async def initialize(self) -> bool:
        self._demo.start()
        return True

    async def shutdown(self) -> None:
        self._demo.stop()
```

### 5.6 ServiceBackend Implementation

`ServiceBackend` wraps the existing `CascorServiceAdapter`, adapting its interface to `BackendProtocol`.

**File**: `src/backend/service_backend.py` (new)

**Design**:

- Delegates to the existing `CascorServiceAdapter` instance
- Adapts method names and return types to the protocol
- Handles async lifecycle (connect, metrics relay start/stop)
- Logs the active backend type at startup

```python
# Conceptual implementation sketch

class ServiceBackend:
    """BackendProtocol implementation wrapping CascorServiceAdapter."""

    def __init__(self, adapter: CascorServiceAdapter):
        self._adapter = adapter

    @property
    def backend_type(self) -> str:
        return "service"

    def start_training(self, reset: bool = True, **kwargs) -> Dict[str, Any]:
        if self._adapter.network is None:
            return {"ok": False, "error": "No network created"}
        if self._adapter.is_training_in_progress():
            return {"ok": False, "error": "Training already in progress"}
        success = self._adapter.start_training_background(**kwargs)
        return {"ok": success, "is_training": success}

    def stop_training(self) -> Dict[str, Any]:
        success = self._adapter.request_training_stop()
        return {"ok": success}

    def pause_training(self) -> Dict[str, Any]:
        # Delegate to CasCor service pause endpoint (when available)
        return {"ok": False, "error": "Pause not yet supported in service mode"}

    def resume_training(self) -> Dict[str, Any]:
        return {"ok": False, "error": "Resume not yet supported in service mode"}

    def reset_training(self) -> Dict[str, Any]:
        return {"ok": False, "error": "Reset not yet supported in service mode"}

    def is_training_active(self) -> bool:
        return self._adapter.is_training_in_progress()

    def get_status(self) -> Dict[str, Any]:
        return self._adapter.get_training_status()

    def get_metrics(self) -> Dict[str, Any]:
        return self._adapter.training_monitor.get_current_metrics()

    def get_metrics_history(self, count: int = 100) -> List[Dict[str, Any]]:
        return self._adapter.training_monitor.get_recent_metrics(count)

    def has_network(self) -> bool:
        return self._adapter.network is not None

    def get_network_topology(self) -> Optional[Dict[str, Any]]:
        return self._adapter.extract_network_topology()

    def get_network_stats(self) -> Dict[str, Any]:
        return self._adapter.get_network_data()

    def get_dataset(self) -> Optional[Dict[str, Any]]:
        return self._adapter.get_dataset_info()

    def get_decision_boundary(self, resolution: int = 50) -> Optional[Dict[str, Any]]:
        # Not available over REST — returns None
        return None

    def apply_params(self, **params) -> Dict[str, Any]:
        return {"ok": False, "error": "Parameter changes not yet supported in service mode"}

    async def initialize(self) -> bool:
        connected = await self._adapter.connect()
        if connected:
            await self._adapter.start_metrics_relay()
        return connected

    async def shutdown(self) -> None:
        await self._adapter.stop_metrics_relay()
        self._adapter.shutdown()
```

### 5.7 main.py Refactor Pattern

The refactored `main.py` replaces all branching with a single `backend` variable of type `BackendProtocol`.

**Before** (current — scattered branching):

```python
# Globals
demo_mode_instance = None
backend = None
demo_mode_active = False

# In a route handler (repeated 40+ times):
@app.get("/api/training/status")
async def get_training_status():
    global demo_mode_instance
    if demo_mode_instance:
        state = demo_mode_instance.get_current_state()
        return {"status": "running" if state["is_running"] else "idle", ...}
    if backend:
        return backend.get_training_status()
    return {"error": "No backend available"}
```

**After** (refactored — single dispatch):

```python
# Single global
backend: BackendProtocol  # Set once at startup

# In a route handler (clean, mode-agnostic):
@app.get("/api/training/status")
async def get_training_status():
    return backend.get_status()
```

**Startup factory**:

```python
# Module-level mode selection (replaces lines 234-256 in current main.py)
def create_backend() -> BackendProtocol:
    """Factory: create the appropriate backend based on environment."""
    force_demo = os.getenv("CASCOR_DEMO_MODE", "0") in ("1", "true", "True", "yes", "Yes")
    service_url = os.getenv("CASCOR_SERVICE_URL")

    if force_demo:
        system_logger.info("Demo mode explicitly enabled via CASCOR_DEMO_MODE")
        return DemoBackend(get_demo_mode(update_interval=1.0))

    if service_url:
        api_key = os.getenv("JUNIPER_DATA_API_KEY")
        system_logger.info(f"Service mode: connecting to CasCor at {service_url}")
        adapter = CascorServiceAdapter(service_url=service_url, api_key=api_key)
        return ServiceBackend(adapter)

    system_logger.info("No CASCOR_SERVICE_URL set — falling back to demo mode")
    return DemoBackend(get_demo_mode(update_interval=1.0))

backend = create_backend()
```

**Impact summary**:

| Metric                         | Before        | After          |
|--------------------------------|---------------|----------------|
| `if demo_mode_instance:` checks | ~40           | 0              |
| `if backend:` checks            | ~15           | 0              |
| Global variables for mode        | 3 (`demo_mode_instance`, `backend`, `demo_mode_active`) | 1 (`backend`) |
| Lines of branching code          | ~120          | ~0             |
| Type safety (mypy)               | No contract   | Full protocol  |

### 5.8 Implementation Tasks

| #   | Task                                                                                                                                             | Files                                       | Depends On |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|------------|
| 5.1 | Define `BackendProtocol` in `src/backend/protocol.py` with all methods from Section 5.4                                                        | `src/backend/protocol.py` (new)             | —          |
| 5.2 | Create `DemoBackend` adapter in `src/backend/demo_backend.py` wrapping `DemoMode`                                                               | `src/backend/demo_backend.py` (new)         | 5.1        |
| 5.3 | Create `ServiceBackend` adapter in `src/backend/service_backend.py` wrapping `CascorServiceAdapter`                                             | `src/backend/service_backend.py` (new)      | 5.1        |
| 5.4 | Create `create_backend()` factory function in `src/backend/__init__.py`                                                                          | `src/backend/__init__.py`                   | 5.2, 5.3   |
| 5.5 | Refactor `main.py` — replace all `demo_mode_instance` / `backend` branching with single `backend: BackendProtocol` dispatch                     | `src/main.py`                               | 5.4        |
| 5.6 | Add `mypy` protocol conformance check: `assert isinstance(DemoBackend(...), BackendProtocol)` and same for `ServiceBackend`                     | `src/backend/protocol.py`                   | 5.2, 5.3   |
| 5.7 | Write unit tests for `DemoBackend` — all protocol methods return expected types                                                                  | `src/tests/unit/test_demo_backend.py` (new) | 5.2        |
| 5.8 | Write unit tests for `ServiceBackend` — all protocol methods return expected types (mocked `CascorServiceAdapter`)                               | `src/tests/unit/test_service_backend.py` (new) | 5.3     |
| 5.9 | Write unit test for `create_backend()` factory — verify correct backend type for each env var combination                                        | `src/tests/unit/test_backend_factory.py` (new) | 5.4     |
| 5.10 | Run full test suite (`pytest tests/ -v`) — verify all 3,215+ tests pass with refactored main.py                                                | —                                           | 5.5        |
| 5.11 | Run `mypy src/ --ignore-missing-imports` — verify no protocol violations                                                                        | —                                           | 5.5        |
| 5.12 | Update `conftest.py` `reset_singletons` fixture if `DemoBackend`/`ServiceBackend` introduce new singletons                                      | `src/tests/conftest.py`                     | 5.5        |

### 5.9 Verification Procedure

```bash
cd JuniperCanopy/juniper_canopy

# 1. Type check — verify both backends conform to protocol
mypy src/backend/protocol.py src/backend/demo_backend.py src/backend/service_backend.py \
  --ignore-missing-imports
# Expected: Success: no issues found

# 2. Run full test suite (demo mode — default)
cd src && pytest tests/ -v
# Expected: 3,215+ passed, 0 failed, 0 errors

# 3. Verify demo mode startup
CASCOR_DEMO_MODE=1 python -c "
from backend import create_backend
b = create_backend()
assert b.backend_type == 'demo'
print(f'Backend type: {b.backend_type}')
print(f'Status: {b.get_status()}')
"
# Expected: Backend type: demo, Status: {...}

# 4. Verify service mode startup (without real CasCor — expect connect failure)
CASCOR_SERVICE_URL=http://localhost:8200 python -c "
from backend import create_backend
b = create_backend()
assert b.backend_type == 'service'
print(f'Backend type: {b.backend_type}')
"
# Expected: Backend type: service

# 5. Verify fallback to demo when no env vars set
python -c "
import os
os.environ.pop('CASCOR_DEMO_MODE', None)
os.environ.pop('CASCOR_SERVICE_URL', None)
from backend import create_backend
b = create_backend()
assert b.backend_type == 'demo'
print('Fallback to demo: OK')
"
# Expected: Fallback to demo: OK

# 6. Run application in demo mode and verify dashboard loads
./demo
# Open http://localhost:8050 — all 4 tabs should display data
```

### 5.10 Security Considerations

| Concern                                   | Mitigation                                                                                                                                     |
|-------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| Demo mode enabled in production           | `create_backend()` logs the active mode at INFO level. Add a WARNING if `CASCOR_DEMO_MODE=1` and `JUNIPER_ENV=production` (future enhancement) |
| Protocol methods expose internal state    | Protocol returns `Dict[str, Any]` — no direct access to `MockCascorNetwork` or `JuniperCascorClient` internals from route handlers            |
| Factory function trusts env vars          | Same security posture as current `main.py` — no regression. Env var validation unchanged                                                      |
| ServiceBackend exposes service URL in logs | Already the case in current implementation. No new exposure                                                                                   |

### 5.11 Performance Considerations

| Concern                              | Impact                                                           | Mitigation                                                                                              |
|--------------------------------------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Additional indirection layer         | ~1 method call overhead per request (~0.001ms)                   | Negligible. Python method dispatch is ~100ns. Dashboard update intervals are 500-1000ms                 |
| DemoBackend wraps DemoMode           | Thin adapter — no data copying, no serialization                 | All methods delegate directly to DemoMode. No performance regression                                    |
| ServiceBackend wraps adapter         | Thin adapter — same as above                                     | All methods delegate directly to CascorServiceAdapter. No performance regression                        |
| Factory called once at startup       | Single call, no ongoing cost                                     | Backend object is created once and reused for the lifetime of the application                            |
| Protocol `isinstance()` check        | Only used in tests/assertions, not in hot paths                  | `@runtime_checkable` adds no overhead to normal method calls                                            |

---

## Phase 6: Client Library Fakes (Near-Term)

### 6.1 Objectives

- Add `FakeCascorClient` to the `juniper-cascor-client` package that implements the same interface as `JuniperCascorClient` with configurable synthetic responses
- Add `FakeDataClient` to the `juniper-data-client` package that implements the same interface as `JuniperDataClient` with configurable synthetic responses
- Add `FakeCascorTrainingStream` to `juniper-cascor-client` for WebSocket stream simulation
- Package fakes in a `testing` submodule within each client library (`juniper_cascor_client.testing`, `juniper_data_client.testing`)
- Enable dependency injection in `CascorServiceAdapter` to accept either real or fake clients
- Improve unit testing across all consuming projects (JuniperCanopy, JuniperCascor)
- Eliminate the need for `DemoMode`'s 1,100-line simulation for testing purposes — fakes provide a lighter-weight alternative

### 6.2 Prerequisites

| Requirement                          | Version   | Verification                                               |
|--------------------------------------|-----------|------------------------------------------------------------|
| Python                               | >= 3.12   | `python --version`                                         |
| Phase 5 complete (BackendProtocol)   | —         | `BackendProtocol` defined and both backends passing tests  |
| juniper-cascor-client                | >= 0.1.0  | `pip show juniper-cascor-client`                           |
| juniper-data-client                  | >= 0.3.0  | `pip show juniper-data-client`                             |
| numpy                                | >= 1.24   | For generating synthetic NPZ artifacts in FakeDataClient   |

### 6.3 FakeCascorClient Design

`FakeCascorClient` provides the same public API as `JuniperCascorClient` but returns configurable in-memory data without making HTTP calls.

**File**: `juniper_cascor_client/testing/fake_client.py` (new)

**Design principles**:

- Every public method of `JuniperCascorClient` has a corresponding implementation in `FakeCascorClient`
- State transitions are realistic: `idle → training → paused → training → complete`
- Configurable via a `scenario` parameter (e.g., `"two_spiral_training"`, `"xor_converged"`, `"empty"`)
- No network calls — all state is in-memory
- Thread-safe (matches the thread safety guarantees of the real client)
- Raises the same exception types (`JuniperCascorClientError` and subclasses) for error scenarios

```python
# Conceptual interface

class FakeCascorClient:
    """
    In-memory fake of JuniperCascorClient for testing and demo use.

    Usage:
        from juniper_cascor_client.testing import FakeCascorClient

        client = FakeCascorClient(scenario="two_spiral_training")
        status = client.get_training_status()
        metrics = client.get_metrics()
    """

    def __init__(
        self,
        scenario: str = "idle",
        base_url: str = "http://fake-cascor:8200",
        api_key: Optional[str] = None,
    ) -> None: ...

    # --- Health & readiness (always healthy) ---
    def health_check(self) -> Dict[str, Any]: ...
    def is_alive(self) -> bool: ...
    def is_ready(self) -> bool: ...
    def wait_for_ready(self, timeout: float = 30.0, poll_interval: float = 0.5) -> bool: ...

    # --- Network management (in-memory state) ---
    def create_network(self, **kwargs: Any) -> Dict[str, Any]: ...
    def get_network(self) -> Dict[str, Any]: ...
    def delete_network(self) -> Dict[str, Any]: ...
    def get_topology(self) -> Dict[str, Any]: ...
    def get_statistics(self) -> Dict[str, Any]: ...

    # --- Training control (state machine) ---
    def start_training(self, epochs: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]: ...
    def stop_training(self) -> Dict[str, Any]: ...
    def pause_training(self) -> Dict[str, Any]: ...
    def resume_training(self) -> Dict[str, Any]: ...
    def reset_training(self) -> Dict[str, Any]: ...
    def get_training_status(self) -> Dict[str, Any]: ...
    def get_training_params(self) -> Dict[str, Any]: ...

    # --- Metrics (pre-generated curves) ---
    def get_metrics(self) -> Dict[str, Any]: ...
    def get_metrics_history(self, count: Optional[int] = None) -> Dict[str, Any]: ...

    # --- Data & visualization ---
    def get_dataset(self) -> Dict[str, Any]: ...
    def get_decision_boundary(self, resolution: int = 50) -> Dict[str, Any]: ...

    # --- Lifecycle ---
    def close(self) -> None: ...
    def __enter__(self) -> "FakeCascorClient": ...
    def __exit__(self, *args) -> None: ...

    # --- Test helpers (not on real client) ---
    def advance_epoch(self, n: int = 1) -> None:
        """Advance the simulated training by n epochs."""
        ...

    def set_state(self, state: str) -> None:
        """Force a training state: 'idle', 'training', 'paused', 'complete'."""
        ...
```

**Scenario presets**:

| Scenario                | Initial State   | Network   | Dataset       | Behavior                                  |
|-------------------------|-----------------|-----------|---------------|-------------------------------------------|
| `"idle"`                | Idle            | None      | None          | Ready for network creation                |
| `"two_spiral_training"` | Training        | 2→1 CasCor | Two spiral    | Generates realistic loss/accuracy curves  |
| `"xor_converged"`       | Complete        | 2→1 CasCor | XOR           | Fully trained, static metrics             |
| `"empty"`               | Idle            | None      | None          | Minimal responses, for negative testing   |
| `"error_prone"`         | Varies          | Varies    | Varies        | Raises exceptions on ~10% of calls        |

### 6.4 FakeDataClient Design

`FakeDataClient` provides the same public API as `JuniperDataClient` but returns configurable in-memory data.

**File**: `juniper_data_client/testing/fake_client.py` (new)

```python
# Conceptual interface

class FakeDataClient:
    """
    In-memory fake of JuniperDataClient for testing and demo use.

    Usage:
        from juniper_data_client.testing import FakeDataClient

        client = FakeDataClient()
        generators = client.list_generators()
        result = client.create_spiral_dataset(n_spirals=2)
    """

    def __init__(
        self,
        base_url: str = "http://fake-data:8100",
        api_key: Optional[str] = None,
    ) -> None: ...

    # --- Health & readiness ---
    def health_check(self) -> Dict[str, Any]: ...
    def is_ready(self) -> bool: ...
    def wait_for_ready(self, timeout: float = 30.0, poll_interval: float = 0.5) -> bool: ...

    # --- Generators (static catalog) ---
    def list_generators(self) -> List[Dict[str, Any]]: ...
    def get_generator_schema(self, name: str) -> Dict[str, Any]: ...

    # --- Dataset CRUD (in-memory) ---
    def create_dataset(self, generator: str, params: Dict, persist: bool = True) -> Dict[str, Any]: ...
    def create_spiral_dataset(self, **kwargs) -> Dict[str, Any]: ...
    def list_datasets(self, limit: int = 100, offset: int = 0) -> List[str]: ...
    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]: ...
    def delete_dataset(self, dataset_id: str) -> bool: ...

    # --- Artifacts (synthetic NumPy arrays) ---
    def download_artifact_bytes(self, dataset_id: str) -> bytes: ...
    def download_artifact_npz(self, dataset_id: str) -> Dict[str, np.ndarray]: ...

    # --- Preview ---
    def get_preview(self, dataset_id: str, n: int = 100) -> Dict[str, Any]: ...

    # --- Lifecycle ---
    def close(self) -> None: ...
    def __enter__(self) -> "FakeDataClient": ...
    def __exit__(self, *args) -> None: ...
```

**Generator presets** (matching real JuniperData generators):

| Generator    | Output Keys                                           | Description                         |
|--------------|-------------------------------------------------------|-------------------------------------|
| `spiral`     | `X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full` | Configurable n_spirals, noise, seed |
| `xor`        | Same                                                  | 4-point XOR with optional noise     |
| `circle`     | Same                                                  | Concentric circles                  |
| `moon`       | Same                                                  | Two interleaving half-moons         |

All artifact downloads return `float32` NumPy arrays matching the NPZ data contract.

### 6.5 FakeCascorTrainingStream Design

`FakeCascorTrainingStream` simulates the async WebSocket training stream without a real connection.

**File**: `juniper_cascor_client/testing/fake_ws_client.py` (new)

```python
# Conceptual interface

class FakeCascorTrainingStream:
    """
    In-memory fake of CascorTrainingStream for testing.

    Yields pre-configured messages on a timer or on-demand.

    Usage:
        from juniper_cascor_client.testing import FakeCascorTrainingStream

        stream = FakeCascorTrainingStream(messages=[...])
        async with stream:
            async for msg in stream.stream():
                print(msg)
    """

    def __init__(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        delay: float = 0.1,
        base_url: str = "ws://fake-cascor:8200",
        api_key: Optional[str] = None,
    ) -> None: ...

    async def connect(self, path: str = "/ws/training") -> None: ...
    async def disconnect(self) -> None: ...
    async def stream(self) -> AsyncIterator[Dict[str, Any]]: ...
    async def listen(self) -> None: ...
    async def send_command(self, command: str, params: Optional[Dict] = None) -> None: ...

    # Callback registration (same as real stream)
    def on_metrics(self, callback: Callable) -> None: ...
    def on_state(self, callback: Callable) -> None: ...
    def on_topology(self, callback: Callable) -> None: ...
    def on_cascade_add(self, callback: Callable) -> None: ...
    def on_event(self, callback: Callable) -> None: ...

    # Async context manager
    async def __aenter__(self) -> "FakeCascorTrainingStream": ...
    async def __aexit__(self, *args) -> None: ...
    def __aiter__(self) -> AsyncIterator[Dict[str, Any]]: ...

    # Test helpers
    def inject_message(self, message: Dict[str, Any]) -> None:
        """Inject a message into the stream (for test control)."""
        ...
```

### 6.6 Package Layout

**juniper-cascor-client** (additions):

```bash
juniper_cascor_client/
├── __init__.py                   # Existing — add testing imports to __all__
├── client.py                     # Existing — JuniperCascorClient
├── ws_client.py                  # Existing — CascorTrainingStream, CascorControlStream
├── exceptions.py                 # Existing
├── py.typed                      # Existing
└── testing/                      # NEW — testing submodule
    ├── __init__.py               # Exports: FakeCascorClient, FakeCascorTrainingStream
    ├── fake_client.py            # FakeCascorClient implementation
    ├── fake_ws_client.py         # FakeCascorTrainingStream implementation
    └── scenarios.py              # Scenario data generators (metrics curves, topologies)
```

**juniper-data-client** (additions):

```bash
juniper_data_client/
├── __init__.py                   # Existing — add testing imports to __all__
├── client.py                     # Existing — JuniperDataClient
├── exceptions.py                 # Existing
├── py.typed                      # Existing
└── testing/                      # NEW — testing submodule
    ├── __init__.py               # Exports: FakeDataClient
    ├── fake_client.py            # FakeDataClient implementation
    └── generators.py             # Synthetic dataset generators (spiral, xor, etc.)
```

**pyproject.toml changes** (both packages):

No new dependencies required for fakes. The `testing` submodule uses only stdlib + numpy (already a dependency). Fakes are shipped as part of the main package — no separate `[test]` extra needed, because consuming projects import them at runtime for demo mode.

### 6.7 Dependency Injection in CascorServiceAdapter

After Phase 5's `BackendProtocol` refactor and Phase 6's fakes, `CascorServiceAdapter` can accept injected clients:

**Before** (current — hardcoded client creation):

```python
class CascorServiceAdapter:
    def __init__(self, service_url: str = "http://localhost:8200", api_key: Optional[str] = None):
        self._client = JuniperCascorClient(base_url=service_url, api_key=api_key)
```

**After** (injectable — accepts any client with the same interface):

```python
class CascorServiceAdapter:
    def __init__(
        self,
        service_url: str = "http://localhost:8200",
        api_key: Optional[str] = None,
        client: Optional[JuniperCascorClient] = None,  # Injectable
    ):
        self._client = client or JuniperCascorClient(base_url=service_url, api_key=api_key)
```

This enables:

```python
# Production use (unchanged)
adapter = CascorServiceAdapter(service_url="http://juniper-cascor:8200")

# Testing with fakes
from juniper_cascor_client.testing import FakeCascorClient
fake = FakeCascorClient(scenario="two_spiral_training")
adapter = CascorServiceAdapter(client=fake)

# ServiceBackend with fake client (no real CasCor needed)
backend = ServiceBackend(adapter)
```

### 6.8 Implementation Tasks

| #   | Task                                                                                                                                           | Files                                                   | Depends On |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|------------|
| 6.1 | Create `juniper_cascor_client/testing/__init__.py` with public exports                                                                        | `testing/__init__.py` (new)                             | —          |
| 6.2 | Create `scenarios.py` — metric curve generators, topology templates, pre-built scenario data                                                   | `testing/scenarios.py` (new)                            | —          |
| 6.3 | Implement `FakeCascorClient` with all methods from Section 6.3, using scenario data from 6.2                                                   | `testing/fake_client.py` (new)                          | 6.1, 6.2   |
| 6.4 | Implement `FakeCascorTrainingStream` with message injection and async iteration                                                                | `testing/fake_ws_client.py` (new)                       | 6.1        |
| 6.5 | Write tests for `FakeCascorClient` — all methods, all scenarios, error cases                                                                   | `tests/test_fake_client.py` (new)                       | 6.3        |
| 6.6 | Write tests for `FakeCascorTrainingStream` — stream, callbacks, injection                                                                      | `tests/test_fake_ws_client.py` (new)                    | 6.4        |
| 6.7 | Create `juniper_data_client/testing/__init__.py` with public exports                                                                           | `testing/__init__.py` (new)                             | —          |
| 6.8 | Create `generators.py` — synthetic dataset generators matching real JuniperData output                                                          | `testing/generators.py` (new)                           | —          |
| 6.9 | Implement `FakeDataClient` with all methods from Section 6.4, using generators from 6.8                                                        | `testing/fake_client.py` (new)                          | 6.7, 6.8   |
| 6.10 | Write tests for `FakeDataClient` — all methods, dataset creation, artifact downloads                                                          | `tests/test_fake_client.py` (new)                       | 6.9        |
| 6.11 | Add `client` parameter to `CascorServiceAdapter.__init__()` for dependency injection (Section 6.7)                                            | `src/backend/cascor_service_adapter.py`                 | 6.3        |
| 6.12 | Write integration test: `ServiceBackend` + `CascorServiceAdapter` + `FakeCascorClient` — full protocol exercised without real CasCor           | `src/tests/integration/test_fake_service_backend.py` (new) | 6.3, 6.11, Phase 5 |
| 6.13 | Verify both client library test suites pass: `cd juniper-cascor-client && pytest tests/ -v` and `cd juniper-data-client && pytest tests/ -v`   | —                                                       | 6.5, 6.6, 6.10 |
| 6.14 | Verify JuniperCanopy test suite passes with no regressions: `cd JuniperCanopy/juniper_canopy/src && pytest tests/ -v`                          | —                                                       | 6.11, 6.12 |

### 6.9 Verification Procedure

```bash
# 1. Verify FakeCascorClient works standalone
cd juniper-cascor-client
python -c "
from juniper_cascor_client.testing import FakeCascorClient
client = FakeCascorClient(scenario='two_spiral_training')
print(f'Health: {client.health_check()}')
print(f'Status: {client.get_training_status()}')
print(f'Metrics: {client.get_metrics()}')
print(f'Topology: {client.get_topology()}')
client.close()
print('FakeCascorClient: OK')
"

# 2. Verify FakeDataClient works standalone
cd juniper-data-client
python -c "
from juniper_data_client.testing import FakeDataClient
client = FakeDataClient()
print(f'Health: {client.health_check()}')
gens = client.list_generators()
print(f'Generators: {[g[\"name\"] for g in gens]}')
result = client.create_spiral_dataset(n_spirals=2, n_points_per_spiral=50)
dataset_id = result['dataset_id']
npz = client.download_artifact_npz(dataset_id)
print(f'NPZ keys: {list(npz.keys())}')
print(f'X_train shape: {npz[\"X_train\"].shape}, dtype: {npz[\"X_train\"].dtype}')
client.close()
print('FakeDataClient: OK')
"

# 3. Verify dependency injection in CascorServiceAdapter
cd JuniperCanopy/juniper_canopy
python -c "
from juniper_cascor_client.testing import FakeCascorClient
from backend.cascor_service_adapter import CascorServiceAdapter
fake = FakeCascorClient(scenario='two_spiral_training')
adapter = CascorServiceAdapter(client=fake)
print(f'Training: {adapter.is_training_in_progress()}')
print(f'Status: {adapter.get_training_status()}')
print('DI injection: OK')
"

# 4. Run all test suites
cd juniper-cascor-client && pytest tests/ -v
cd juniper-data-client && pytest tests/ -v
cd JuniperCanopy/juniper_canopy/src && pytest tests/ -v
# Expected: All green, no regressions

# 5. Verify async stream fake
cd juniper-cascor-client
python -c "
import asyncio
from juniper_cascor_client.testing import FakeCascorTrainingStream
async def test():
    stream = FakeCascorTrainingStream(messages=[
        {'type': 'state', 'data': {'status': 'training'}},
        {'type': 'metrics', 'data': {'epoch': 1, 'loss': 0.5}},
    ])
    async with stream:
        msgs = []
        async for msg in stream.stream():
            msgs.append(msg)
        print(f'Received {len(msgs)} messages')
    print('FakeCascorTrainingStream: OK')
asyncio.run(test())
"
```

### 6.10 Security Considerations

| Concern                                  | Mitigation                                                                                                                     |
|------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Fake clients imported in production      | Fakes are in a `testing` submodule — import path makes intent clear. No runtime guard needed (they are safe, just synthetic)   |
| Synthetic data contains patterns of real data | Fakes generate mathematical curves (sin, spiral), not copies of real training data. No PII or proprietary data risk          |
| FakeDataClient generates NPZ artifacts   | Artifacts contain only synthetic NumPy arrays. No file system access — all in-memory                                          |
| Fake exception raising                   | `error_prone` scenario raises real exception types — consuming code must handle them correctly (this is a feature, not a risk) |

### 6.11 Performance Considerations

| Concern                           | Impact                                                          | Mitigation                                                                                     |
|-----------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| Fake client in demo mode          | Faster than real HTTP calls (~0.001ms vs ~1-10ms per method)    | Performance improvement over current DemoMode in some paths                                    |
| Scenario data generation          | Pre-computed at `__init__` time (~1-10ms depending on scenario) | One-time cost. Negligible for demo or test startup                                             |
| NPZ artifact generation           | NumPy array creation (~1ms for 200-sample dataset)              | Equivalent to current DemoMode dataset generation. No regression                               |
| FakeCascorTrainingStream overhead  | In-memory async iteration (~0.01ms per message)                 | Orders of magnitude faster than real WebSocket I/O                                              |
| Package size increase              | ~5-20 KB per testing submodule                                  | Negligible addition to package size. No new dependencies                                        |

---

## Phase 7: Docker Compose Demo Profile (With Docker)

### 7.1 Objectives

- Add a `demo` profile to `juniper-deploy/docker-compose.yml` that runs real CasCor with auto-start configuration
- Provide a `docker compose --profile demo up` command that launches a self-running demo stack
- Implement auto-start configuration for JuniperCascor: create network, load dataset, begin training on startup
- Seed a demo dataset in JuniperData on first startup
- Eliminate demo-specific code in JuniperCanopy — the dashboard connects to real services that happen to be auto-configured
- Provide the most realistic demo experience for stakeholders

### 7.2 Prerequisites

| Requirement                 | Version   | Verification                                  |
|-----------------------------|-----------|-----------------------------------------------|
| Docker Engine               | >= 24.0   | `docker --version`                            |
| Docker Compose V2           | >= 2.20   | `docker compose version`                      |
| Phase 1 complete            | —         | `juniper-deploy/Makefile` and Compose working |
| juniper-data images built   | —         | `docker images juniper-data`                  |
| juniper-cascor images built | —         | `docker images juniper-cascor`                |
| juniper-canopy images built | —         | `docker images juniper-canopy`                |

Phase 7 is infrastructure-only and does not depend on Phase 5 or Phase 6.

### 7.3 Profile Architecture

Docker Compose profiles define which services start for each operational mode:

```bash
# Full stack (production-like) — all real services
docker compose --profile full up

# Demo stack — real services with auto-configuration
docker compose --profile demo up

# Development stack — real data + cascor, canopy in demo mode (for frontend dev)
docker compose --profile dev up
```

**Profile membership**:

| Service                | `full` | `demo` | `dev` | Notes                                              |
|------------------------|--------|--------|-------|----------------------------------------------------|
| `juniper-data`         | yes    | yes    | yes   | Always needed (real dataset service)               |
| `juniper-cascor`       | yes    | no     | yes   | Real CasCor for full/dev stacks                    |
| `juniper-cascor-demo`  | no     | yes    | no    | Auto-configured CasCor for demo                    |
| `juniper-canopy`       | yes    | no     | no    | Full Canopy (service mode, real CasCor)            |
| `juniper-canopy-demo`  | no     | yes    | no    | Canopy pointing at demo CasCor                     |
| `juniper-canopy-dev`   | no     | no     | yes   | Canopy in demo mode (`CASCOR_DEMO_MODE=1`)         |
| `demo-seed`            | no     | yes    | no    | Init container: seeds demo dataset in JuniperData  |

### 7.4 Compose File Modifications

Extend `juniper-deploy/docker-compose.yml` with profile-aware service definitions:

```yaml
services:
  # === JuniperData (shared across all profiles) ===
  juniper-data:
    profiles: [full, demo, dev]
    build:
      context: ../juniper-data
      dockerfile: Dockerfile
    image: juniper-data:latest
    container_name: juniper-data
    ports:
      - "${JUNIPER_DATA_PORT:-8100}:${JUNIPER_DATA_PORT:-8100}"
    environment:
      JUNIPER_DATA_HOST: "${JUNIPER_DATA_HOST:-0.0.0.0}"
      JUNIPER_DATA_PORT: "${JUNIPER_DATA_PORT:-8100}"
      JUNIPER_DATA_LOG_LEVEL: "${JUNIPER_DATA_LOG_LEVEL:-INFO}"
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8100/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 10s
      retries: 5
    restart: unless-stopped

  # === JuniperCascor (full + dev profiles) ===
  juniper-cascor:
    profiles: [full, dev]
    build:
      context: ../juniper-cascor
      dockerfile: Dockerfile
    image: juniper-cascor:latest
    container_name: juniper-cascor
    ports:
      - "${CASCOR_PORT:-8200}:${CASCOR_PORT:-8200}"
    environment:
      JUNIPER_DATA_URL: "${JUNIPER_DATA_URL:-http://juniper-data:8100}"
      CASCOR_HOST: "${CASCOR_HOST:-0.0.0.0}"
      CASCOR_PORT: "${CASCOR_PORT:-8200}"
      CASCOR_LOG_LEVEL: "${CASCOR_LOG_LEVEL:-INFO}"
    depends_on:
      juniper-data:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8200/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 15s
      retries: 5
    restart: unless-stopped

  # === JuniperCascor Demo (auto-start training) ===
  juniper-cascor-demo:
    profiles: [demo]
    build:
      context: ../juniper-cascor
      dockerfile: Dockerfile
    image: juniper-cascor:latest
    container_name: juniper-cascor-demo
    ports:
      - "${CASCOR_PORT:-8200}:${CASCOR_PORT:-8200}"
    environment:
      JUNIPER_DATA_URL: "http://juniper-data:8100"
      CASCOR_HOST: "0.0.0.0"
      CASCOR_PORT: "8200"
      CASCOR_LOG_LEVEL: "INFO"
      # --- Demo auto-start configuration ---
      CASCOR_AUTO_START: "true"
      CASCOR_AUTO_DATASET: "spiral"
      CASCOR_AUTO_DATASET_PARAMS: '{"n_spirals": 2, "n_points_per_spiral": 200, "noise": 0.15}'
      CASCOR_AUTO_NETWORK: '{"input_size": 2, "output_size": 1, "learning_rate": 0.01}'
      CASCOR_AUTO_TRAIN_EPOCHS: "500"
    depends_on:
      juniper-data:
        condition: service_healthy
      demo-seed:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8200/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 15s
      retries: 5
    restart: unless-stopped

  # === Demo Dataset Seeder (init container) ===
  demo-seed:
    profiles: [demo]
    image: juniper-data:latest
    container_name: juniper-demo-seed
    entrypoint: ["python", "-c", "
import urllib.request, json, time, sys;
base = 'http://juniper-data:8100/v1';
# Wait for data service
for i in range(30):
    try:
        urllib.request.urlopen(f'{base}/health', timeout=5);
        break
    except Exception:
        time.sleep(2)
else:
    sys.exit(1);
# Create demo spiral dataset
params = json.dumps({
    'generator': 'spiral',
    'params': {'n_spirals': 2, 'n_points_per_spiral': 200, 'noise': 0.15, 'seed': 42},
    'persist': True
}).encode();
req = urllib.request.Request(f'{base}/datasets', data=params,
    headers={'Content-Type': 'application/json'});
resp = urllib.request.urlopen(req, timeout=30);
print(f'Demo dataset created: {json.loads(resp.read())}')
"]
    depends_on:
      juniper-data:
        condition: service_healthy
    restart: "no"

  # === JuniperCanopy (full profile — service mode) ===
  juniper-canopy:
    profiles: [full]
    build:
      context: ../JuniperCanopy/juniper_canopy
      dockerfile: Dockerfile
    image: juniper-canopy:latest
    container_name: juniper-canopy
    ports:
      - "${CANOPY_PORT:-8050}:${CANOPY_PORT:-8050}"
    environment:
      JUNIPER_DATA_URL: "http://juniper-data:8100"
      CASCOR_SERVICE_URL: "http://juniper-cascor:8200"
      CANOPY_HOST: "0.0.0.0"
      CANOPY_PORT: "8050"
    depends_on:
      juniper-data:
        condition: service_healthy
      juniper-cascor:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8050/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 20s
      retries: 5
    restart: unless-stopped

  # === JuniperCanopy Demo (pointing at demo CasCor) ===
  juniper-canopy-demo:
    profiles: [demo]
    build:
      context: ../JuniperCanopy/juniper_canopy
      dockerfile: Dockerfile
    image: juniper-canopy:latest
    container_name: juniper-canopy-demo
    ports:
      - "${CANOPY_PORT:-8050}:${CANOPY_PORT:-8050}"
    environment:
      JUNIPER_DATA_URL: "http://juniper-data:8100"
      CASCOR_SERVICE_URL: "http://juniper-cascor-demo:8200"
      CANOPY_HOST: "0.0.0.0"
      CANOPY_PORT: "8050"
    depends_on:
      juniper-data:
        condition: service_healthy
      juniper-cascor-demo:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8050/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 20s
      retries: 5
    restart: unless-stopped

  # === JuniperCanopy Dev (demo mode — no backend needed) ===
  juniper-canopy-dev:
    profiles: [dev]
    build:
      context: ../JuniperCanopy/juniper_canopy
      dockerfile: Dockerfile
    image: juniper-canopy:latest
    container_name: juniper-canopy-dev
    ports:
      - "${CANOPY_PORT:-8050}:${CANOPY_PORT:-8050}"
    environment:
      CASCOR_DEMO_MODE: "1"
      CANOPY_HOST: "0.0.0.0"
      CANOPY_PORT: "8050"
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8050/v1/health', timeout=5)"]
      interval: 15s
      timeout: 10s
      start_period: 20s
      retries: 5
    restart: unless-stopped
```

### 7.5 Auto-Start Configuration for CasCor

JuniperCascor does not currently support auto-start training on startup. This requires adding a startup hook to the CasCor server.

**New environment variables** (added to JuniperCascor):

| Variable                     | Type   | Default | Purpose                                           |
|------------------------------|--------|---------|---------------------------------------------------|
| `CASCOR_AUTO_START`          | bool   | false   | Enable auto-start training on server startup      |
| `CASCOR_AUTO_DATASET`        | string | —       | Dataset generator name (e.g., `"spiral"`)         |
| `CASCOR_AUTO_DATASET_PARAMS` | JSON   | `{}`    | Parameters for the dataset generator              |
| `CASCOR_AUTO_NETWORK`        | JSON   | `{}`    | Network creation parameters (`input_size`, etc.)  |
| `CASCOR_AUTO_TRAIN_EPOCHS`   | int    | 200     | Number of training epochs                         |

**Implementation approach** (in JuniperCascor):

Add a FastAPI `startup` event handler that:

1. Checks if `CASCOR_AUTO_START=true`
2. Waits for JuniperData to be healthy (using `juniper-data-client`)
3. Creates a dataset via JuniperData API
4. Creates a CasCor network with the configured parameters
5. Starts training with the configured epoch count
6. Logs the auto-start sequence at INFO level

```python
# Conceptual startup hook (in juniper-cascor/src/server.py)

@app.on_event("startup")
async def auto_start_training():
    if not os.getenv("CASCOR_AUTO_START", "").lower() in ("true", "1", "yes"):
        return

    logger.info("Auto-start enabled — configuring demo training session")

    # 1. Wait for data service
    data_client = JuniperDataClient(base_url=os.getenv("JUNIPER_DATA_URL"))
    if not data_client.wait_for_ready(timeout=60):
        logger.error("Auto-start failed: JuniperData not ready")
        return

    # 2. Create dataset
    dataset_params = json.loads(os.getenv("CASCOR_AUTO_DATASET_PARAMS", "{}"))
    dataset = data_client.create_dataset(
        generator=os.getenv("CASCOR_AUTO_DATASET", "spiral"),
        params=dataset_params,
    )
    logger.info(f"Auto-start: dataset created: {dataset['dataset_id']}")

    # 3. Create network and start training
    network_params = json.loads(os.getenv("CASCOR_AUTO_NETWORK", "{}"))
    # ... create network, start training via internal API
    logger.info("Auto-start: training initiated")
```

### 7.6 Demo Dataset Seeding

The `demo-seed` init container creates a canonical demo dataset before CasCor starts. This ensures:

- The dataset exists before CasCor's auto-start hook fetches it
- The same dataset is used consistently across demo runs
- The seed is deterministic (`seed: 42`) for reproducible demonstrations

**Seed dataset specification**:

| Parameter                 | Value     | Rationale                                      |
|---------------------------|-----------|-------------------------------------------------|
| Generator                 | `spiral`  | Visually interesting, classic CasCor benchmark  |
| `n_spirals`               | 2         | Binary classification — CasCor's primary use    |
| `n_points_per_spiral`     | 200       | 400 total points — enough for clear boundaries  |
| `noise`                   | 0.15      | Moderate noise — shows CasCor's capability      |
| `seed`                    | 42        | Reproducible across demo runs                   |
| `train_ratio`             | 0.8       | 320 train / 80 test                             |

### 7.7 Environment Configuration

**`.env.demo`** (new file — demo-specific overrides):

```bash
# juniper-deploy/.env.demo
# Demo profile environment — used with: docker compose --profile demo --env-file .env.demo up

# Service ports (same as production defaults)
JUNIPER_DATA_PORT=8100
CASCOR_PORT=8200
CANOPY_PORT=8050

# Log levels (more verbose for demo observation)
JUNIPER_DATA_LOG_LEVEL=INFO
CASCOR_LOG_LEVEL=INFO
```

**Usage pattern**:

```bash
# Demo mode (uses .env.demo if present, falls back to .env or defaults)
docker compose --profile demo up

# With explicit env file
docker compose --profile demo --env-file .env.demo up

# Full production-like stack
docker compose --profile full up
```

### 7.8 Implementation Tasks

| #   | Task                                                                                                                                                          | Files                                                | Depends On  |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|-------------|
| 7.1 | Add `profiles: [full, demo, dev]` to `juniper-data` service in `docker-compose.yml`                                                                          | `docker-compose.yml`                                 | —           |
| 7.2 | Add `profiles: [full, dev]` to `juniper-cascor` service and `profiles: [full]` to `juniper-canopy` service                                                   | `docker-compose.yml`                                 | —           |
| 7.3 | Add `juniper-cascor-demo` service definition with auto-start env vars (Section 7.4)                                                                          | `docker-compose.yml`                                 | 7.1         |
| 7.4 | Add `demo-seed` init container service definition (Section 7.4)                                                                                               | `docker-compose.yml`                                 | 7.1         |
| 7.5 | Add `juniper-canopy-demo` service definition pointing at `juniper-cascor-demo` (Section 7.4)                                                                  | `docker-compose.yml`                                 | 7.3         |
| 7.6 | Add `juniper-canopy-dev` service definition with `CASCOR_DEMO_MODE=1` (Section 7.4)                                                                          | `docker-compose.yml`                                 | 7.1         |
| 7.7 | Implement auto-start training hook in `juniper-cascor/src/server.py` (Section 7.5) — new `CASCOR_AUTO_START` env vars                                        | `juniper-cascor/src/server.py`                       | —           |
| 7.8 | Add auto-start Pydantic settings to JuniperCascor config: `CASCOR_AUTO_START`, `CASCOR_AUTO_DATASET`, `CASCOR_AUTO_NETWORK`, `CASCOR_AUTO_TRAIN_EPOCHS`      | `juniper-cascor/src/config.py` (or settings module)  | —           |
| 7.9 | Create `.env.demo` template in `juniper-deploy/` (Section 7.7)                                                                                               | `.env.demo`                                          | —           |
| 7.10 | Add `demo` target to `juniper-deploy/Makefile`: `docker compose --profile demo up -d`                                                                        | `Makefile`                                           | Phase 1     |
| 7.11 | Add `dev` target to `juniper-deploy/Makefile`: `docker compose --profile dev up -d`                                                                           | `Makefile`                                           | Phase 1     |
| 7.12 | Write integration test: `docker compose --profile demo up && wait_for_services.sh && verify training started`                                                 | `scripts/test_demo_profile.sh` (new)                 | 7.3, 7.4, 7.5, 7.7 |
| 7.13 | Update `juniper-deploy/README.md` with profile usage documentation                                                                                            | `README.md`                                          | 7.10, 7.11  |
| 7.14 | Validate `docker compose config --profiles demo` outputs valid YAML with all expected services                                                                 | —                                                    | 7.1-7.6     |

### 7.9 Verification Procedure

```bash
cd juniper-deploy

# 1. Validate Compose file syntax for all profiles
docker compose --profile demo config --quiet
docker compose --profile full config --quiet
docker compose --profile dev config --quiet
# Expected: No errors

# 2. Build all images
docker compose --profile demo build
# Expected: All images build successfully

# 3. Start demo stack
docker compose --profile demo up -d
# Expected: juniper-data, demo-seed, juniper-cascor-demo, juniper-canopy-demo start

# 4. Wait for services
scripts/wait_for_services.sh
# Expected: "All services healthy" within 90 seconds

# 5. Verify demo-seed completed
docker compose logs demo-seed
# Expected: "Demo dataset created: {dataset_id: ...}"
docker compose ps demo-seed
# Expected: Exited (0)

# 6. Verify auto-start training is running
curl -s http://localhost:8200/v1/training/status | python -m json.tool
# Expected: {"is_training": true, "current_epoch": N, ...}

# 7. Verify Canopy dashboard shows real training data
curl -s http://localhost:8050/v1/health
# Expected: {"status": "ok"}
# Open http://localhost:8050 in browser — should show live training metrics

# 8. Verify training progresses
sleep 10
curl -s http://localhost:8200/v1/training/status | python -m json.tool
# Expected: current_epoch has increased

# 9. Clean shutdown
docker compose --profile demo down
# Expected: All containers removed

# 10. Verify full profile still works independently
docker compose --profile full up -d
scripts/wait_for_services.sh
docker compose --profile full down
# Expected: Full stack starts and stops cleanly
```

### 7.10 Security Considerations

| Concern                                     | Mitigation                                                                                                                                |
|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Demo services accessible on host ports      | Demo profile binds to same ports as production. Do not run demo and full profiles simultaneously                                         |
| Auto-start env vars exposed in Compose file | No secrets in auto-start config. Dataset params and network config are non-sensitive. API keys (if any) come from `.env` file             |
| `demo-seed` container has data service access | Init container runs to completion and exits. No persistent access. `restart: "no"` ensures it doesn't restart                           |
| Demo profile accidentally deployed to production | Profile names make intent explicit. CI/CD should use `--profile full` only. Document the distinction in README                        |
| `CASCOR_AUTO_START` enabled in production   | Default is `false`. Only set to `true` in demo profile env block. Server logs a prominent WARNING if auto-start is enabled                |

### 7.11 Performance Considerations

| Concern                           | Impact                                                                 | Mitigation                                                                                   |
|-----------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Demo stack resource usage         | 3 services + init container (~1.5-2 GB RAM total)                      | Same as full stack. Demo training runs at normal speed — no throttling                       |
| Demo startup time                 | ~30-60s (build images + health checks + seed + auto-start)             | Longer than in-process demo mode (~1s). Acceptable for demo context                         |
| Auto-start training CPU usage     | Real CasCor training uses real CPU (single core, no GPU in container)  | CPU-only PyTorch in container. Training 500 epochs of 400-point spiral: ~30-60s              |
| Demo dataset seed time            | `demo-seed` container runs ~5-10s                                      | One-time init container. Runs before CasCor starts                                           |
| Simultaneous profile conflicts    | Cannot run `demo` and `full` profiles at same time (port conflicts)    | Document in README. `docker compose ps` shows which profile is active                        |

---

## Service Discovery and Health Checking — Overview

This section provides the implementation plan for the health check enhancements recommended in [MICROSERVICES_ARCHITECTURE_ANALYSIS.md](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md), Section 4.3.

**Service discovery** continues with the current direct URL approach (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL` environment variables). Docker Compose DNS and Kubernetes DNS handle resolution automatically in containerized environments. No service registry infrastructure is needed at this scale (Section 4.2).

The health check enhancement requires a single phase:

```bash
Phase 8 (Immediate):  Enhance /v1/health/ready to include dependency health status across all services
```

### Current Health Check State

| Service           | `/v1/health`                  | `/v1/health/live`          | `/v1/health/ready`                                          | Response Format    |
|-------------------|-------------------------------|----------------------------|-------------------------------------------------------------|--------------------|
| **JuniperData**   | `{"status": "ok", "version"}` | `{"status": "alive"}`      | `{"status": "ready", "version"}`                            | Plain dict         |
| **JuniperCascor** | Envelope: `data.status: "ok"` | Envelope: `data.status: "alive"}` | Envelope: `data.status: "ready", data.network_loaded: bool` | Pydantic envelope  |
| **JuniperCanopy** | `{"status": "healthy", ...}`  | `{"status": "alive"}`      | `{"status": "ready", "version", "juniper_data_available"}`  | Plain dict         |

### Gap Analysis

| Gap                                          | Impact                                                                                  |
|----------------------------------------------|-----------------------------------------------------------------------------------------|
| Response format inconsistency                | Consumers must handle both plain dicts and Pydantic envelopes                           |
| No dependency health in readiness            | Orchestrators cannot detect cascading failures (e.g., CasCor healthy but Data down)     |
| JuniperData reports ready unconditionally    | No storage availability check — may report ready while storage is unavailable           |
| JuniperCanopy checks Data only at startup    | Health endpoint reports stale status if Data becomes unavailable mid-session             |
| Canopy has 5 health routes (with aliases)    | Maintenance burden; non-standard `/health` and `/api/health` routes                     |

---

## Phase 8: Enhanced Health Checks with Dependency Status (Immediate)

### 8.1 Objectives

- Enhance `/v1/health/ready` on all three services to report dependency health status
- Standardize health response schemas across all services using a common Pydantic model
- Add startup health verification to JuniperCanopy: probe CasCor health during lifespan startup, log and fall back to demo mode if unreachable (addresses CAN-HIGH-001)
- Consolidate JuniperCanopy's 5 health routes to the standard 3 (`/v1/health`, `/v1/health/live`, `/v1/health/ready`)
- Deprecate JuniperCanopy's non-standard `/health` and `/api/health` routes
- Ensure health checks are fast (< 500ms) and do not block the main event loop

### 8.2 Prerequisites

| Requirement                     | Version   | Verification                                               |
|---------------------------------|-----------|------------------------------------------------------------|
| Python                          | >= 3.12   | `python --version`                                         |
| pydantic                        | >= 2.0    | `pip show pydantic` (already a dependency in all services) |
| All services running and testable | —       | `make up && make health` (Phase 1)                         |
| Existing test suites green      | —         | All service tests passing                                  |

### 8.3 Current Health Endpoint Analysis

**JuniperData** (`juniper_data/api/routes/health.py`):

- Returns plain dicts with `status` and `version` fields
- No dependency checks — always returns ready
- No Pydantic response models
- Should check: storage directory availability

**JuniperCascor** (`src/api/routes/health.py`):

- Uses `ResponseEnvelope` Pydantic model (`status`, `data`, `meta`)
- Readiness checks `app.state.lifecycle.has_network()` to report `network_loaded`
- Should check: JuniperData service reachability, training state

**JuniperCanopy** (`src/main.py` — inline routes):

- Returns plain dicts with varying schemas per endpoint
- 5 different health routes (3 standard + 2 aliases)
- Checks `juniper_data_available` flag (set at startup, not refreshed)
- Should check: CasCor service reachability (live, not just startup), active mode

### 8.4 Enhanced Readiness Response Schema

All services adopt a common readiness response structure:

```python
from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional
from datetime import datetime


class DependencyStatus(BaseModel):
    """Health status of a single dependency."""
    name: str
    status: Literal["healthy", "unhealthy", "degraded", "not_configured"]
    latency_ms: Optional[float] = None  # Round-trip probe time
    message: Optional[str] = None       # Human-readable detail


class ReadinessResponse(BaseModel):
    """Standard /v1/health/ready response for all Juniper services."""
    status: Literal["ready", "degraded", "not_ready"]
    version: str
    service: str                        # e.g., "juniper-data", "juniper-cascor", "juniper-canopy"
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    dependencies: Dict[str, DependencyStatus] = {}
    details: Dict[str, object] = {}     # Service-specific fields (e.g., network_loaded, mode)
```

**Per-service readiness responses**:

**JuniperData**:

```json
{
  "status": "ready",
  "version": "0.4.0",
  "service": "juniper-data",
  "timestamp": 1740000000.123,
  "dependencies": {
    "storage": {
      "name": "Dataset Storage",
      "status": "healthy",
      "message": "/app/data/datasets (42 datasets, 128 MB)"
    }
  },
  "details": {
    "generators_loaded": 4
  }
}
```

**JuniperCascor**:

```json
{
  "status": "ready",
  "version": "0.4.0",
  "service": "juniper-cascor",
  "timestamp": 1740000000.123,
  "dependencies": {
    "juniper_data": {
      "name": "JuniperData Service",
      "status": "healthy",
      "latency_ms": 2.3,
      "message": "http://juniper-data:8100"
    }
  },
  "details": {
    "network_loaded": true,
    "training_state": "idle"
  }
}
```

**JuniperCanopy**:

```json
{
  "status": "ready",
  "version": "0.15.1",
  "service": "juniper-canopy",
  "timestamp": 1740000000.123,
  "dependencies": {
    "juniper_data": {
      "name": "JuniperData Service",
      "status": "healthy",
      "latency_ms": 1.8,
      "message": "http://juniper-data:8100"
    },
    "juniper_cascor": {
      "name": "JuniperCascor Service",
      "status": "healthy",
      "latency_ms": 3.1,
      "message": "http://juniper-cascor:8200"
    }
  },
  "details": {
    "mode": "service",
    "active_connections": 2,
    "training_active": true
  }
```

**Degraded status logic**: A service reports `"degraded"` (not `"not_ready"`) when a non-critical dependency is unhealthy. For example, Canopy is `"degraded"` if CasCor is down but it can fall back to demo mode. A service reports `"not_ready"` only when it genuinely cannot serve requests.

### 8.5 Per-Service Implementation Design

#### JuniperData — Storage Check

Add a storage availability check to the readiness endpoint:

```python
# In juniper_data/api/routes/health.py

import os
from pathlib import Path
from api.settings import get_settings

@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness():
    settings = get_settings()
    storage_path = Path(settings.storage_path)

    if storage_path.is_dir():
        dataset_count = len(list(storage_path.glob("*.npz")))
        storage_dep = DependencyStatus(
            name="Dataset Storage",
            status="healthy",
            message=f"{storage_path} ({dataset_count} datasets)"
        )
    else:
        storage_dep = DependencyStatus(
            name="Dataset Storage",
            status="unhealthy",
            message=f"{storage_path} not found or not a directory"
        )

    overall = "ready" if storage_dep.status == "healthy" else "degraded"
    return ReadinessResponse(
        status=overall,
        version=__version__,
        service="juniper-data",
        dependencies={"storage": storage_dep},
    )
```

#### JuniperCascor — Data Service Check

Add an HTTP probe to JuniperData's health endpoint:

```python
# In src/api/routes/health.py

import time
import urllib.request

@router.get("/health/ready")
async def readiness(request: Request):
    lifecycle = getattr(request.app.state, "lifecycle", None)
    network_loaded = lifecycle.has_network() if lifecycle else False
    training_state = lifecycle.get_training_state() if lifecycle else "unknown"

    # Probe JuniperData
    data_url = os.getenv("JUNIPER_DATA_URL", "http://localhost:8100")
    data_dep = _probe_dependency("JuniperData Service", f"{data_url}/v1/health/live")

    overall = "ready"
    if data_dep.status == "unhealthy":
        overall = "degraded"

    return ResponseEnvelope(data=ReadinessResponse(
        status=overall,
        version=__version__,
        service="juniper-cascor",
        dependencies={"juniper_data": data_dep},
        details={"network_loaded": network_loaded, "training_state": training_state},
    ))
```

#### JuniperCanopy — Full Dependency Check

Canopy probes both upstream services:

```python
# Enhanced readiness in main.py (or extracted to a health module)

@app.get("/v1/health/ready")
async def readiness():
    data_url = os.getenv("JUNIPER_DATA_URL", "http://localhost:8100")
    cascor_url = os.getenv("CASCOR_SERVICE_URL")

    data_dep = _probe_dependency("JuniperData Service", f"{data_url}/v1/health/live")

    if cascor_url:
        cascor_dep = _probe_dependency("JuniperCascor Service", f"{cascor_url}/v1/health/live")
    else:
        cascor_dep = DependencyStatus(
            name="JuniperCascor Service",
            status="not_configured",
            message="CASCOR_SERVICE_URL not set (demo mode)"
        )

    overall = "ready"
    if data_dep.status == "unhealthy" or cascor_dep.status == "unhealthy":
        overall = "degraded"

    return ReadinessResponse(
        status=overall,
        version=__version__,
        service="juniper-canopy",
        dependencies={"juniper_data": data_dep, "juniper_cascor": cascor_dep},
        details={
            "mode": backend.backend_type,  # From Phase 5 BackendProtocol
            "active_connections": websocket_manager.active_connections,
            "training_active": backend.is_training_active(),
        },
    )
```

### 8.6 Response Envelope Standardization

Currently, only JuniperCascor uses a `ResponseEnvelope` wrapper. Two options:

**Option A (Recommended): Adopt envelope in all services**

All services wrap health responses in `ResponseEnvelope`:

```json
{
  "status": "success",
  "data": { /* ReadinessResponse */ },
  "meta": { "timestamp": 1740000000.123, "version": "0.4.0" }
}
```

**Pros**: Consistent parsing across all services. Consumers always expect the same structure.

**Option B: Drop envelope, return flat responses**

All services return `ReadinessResponse` directly (JuniperCascor removes its envelope for health routes).

**Pros**: Simpler. Health endpoints are often consumed by orchestrators (Docker, k8s) that expect flat JSON with a `status` field at the top level.

**Recommendation**: **Option B for health endpoints only**. Orchestrator health checks (Docker `healthcheck`, Kubernetes `httpGet`) work best with a flat `{"status": "ready"}` at the top level. Non-health API endpoints in JuniperCascor continue using the envelope.

This means JuniperCascor's health routes would return `ReadinessResponse` directly (breaking change for health endpoints only, not for API endpoints). The `wait_for_services.sh` script and Docker `healthcheck` commands parse `status` at the top level — this change makes them consistent.

### 8.7 Startup Health Verification for Canopy

When `CASCOR_SERVICE_URL` is set, Canopy should probe the CasCor health endpoint during FastAPI lifespan startup. This addresses the CAN-HIGH-001 roadmap item.

```python
# In main.py lifespan or startup event

async def verify_upstream_services():
    """Probe upstream services at startup. Log and fall back gracefully."""
    data_url = os.getenv("JUNIPER_DATA_URL", "http://localhost:8100")
    cascor_url = os.getenv("CASCOR_SERVICE_URL")

    # Check JuniperData
    data_status = _probe_dependency("JuniperData", f"{data_url}/v1/health/live")
    if data_status.status == "healthy":
        system_logger.info(f"JuniperData reachable at {data_url} ({data_status.latency_ms:.1f}ms)")
    else:
        system_logger.warning(f"JuniperData unreachable at {data_url}: {data_status.message}")

    # Check JuniperCascor (if service mode)
    if cascor_url:
        cascor_status = _probe_dependency("JuniperCascor", f"{cascor_url}/v1/health/live")
        if cascor_status.status == "healthy":
            system_logger.info(f"JuniperCascor reachable at {cascor_url} ({cascor_status.latency_ms:.1f}ms)")
        else:
            system_logger.warning(
                f"JuniperCascor unreachable at {cascor_url} — falling back to demo mode"
            )
            # Switch backend to DemoBackend (using Phase 5 factory)
            global backend
            backend = DemoBackend(get_demo_mode(update_interval=1.0))
```

**Shared probe utility** (used by both startup verification and readiness endpoints):

```python
import time
import urllib.request

def _probe_dependency(name: str, url: str, timeout: float = 5.0) -> DependencyStatus:
    """Probe a dependency health endpoint. Returns status with latency."""
    start = time.monotonic()
    try:
        urllib.request.urlopen(url, timeout=timeout)
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name=name, status="healthy", latency_ms=round(latency, 1), message=url)
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(
            name=name, status="unhealthy", latency_ms=round(latency, 1),
            message=f"{url} — {type(e).__name__}: {e}"
        )
```

### 8.8 Implementation Tasks

| #    | Task                                                                                                                                               | Files                                              | Depends On |
|------|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|------------|
| 8.1  | Create shared Pydantic models: `DependencyStatus`, `ReadinessResponse` — consider a `juniper-common` package or duplicate in each service          | New models file per service                         | —          |
| 8.2  | Implement `_probe_dependency()` utility function in each service (or shared)                                                                       | Utility module per service                          | 8.1        |
| 8.3  | Enhance JuniperData `/v1/health/ready` — add storage directory check, return `ReadinessResponse`                                                   | `juniper_data/api/routes/health.py`                 | 8.1        |
| 8.4  | Enhance JuniperCascor `/v1/health/ready` — add JuniperData probe, return flat `ReadinessResponse` (remove envelope for health routes only)         | `src/api/routes/health.py`                          | 8.1, 8.2   |
| 8.5  | Enhance JuniperCanopy `/v1/health/ready` — add JuniperData + CasCor probes, return `ReadinessResponse`                                            | `src/main.py` (or new `src/health.py`)              | 8.1, 8.2   |
| 8.6  | Deprecate JuniperCanopy's `/health` and `/api/health` aliases — add deprecation warning header, plan removal                                       | `src/main.py`                                       | 8.5        |
| 8.7  | Implement startup health verification in Canopy: probe CasCor, fallback to demo mode (Section 8.7, addresses CAN-HIGH-001)                        | `src/main.py`                                       | 8.2, Phase 5 |
| 8.8  | Update `juniper-deploy/scripts/wait_for_services.sh` to parse new `ReadinessResponse` format                                                      | `scripts/wait_for_services.sh`                      | 8.3, 8.4, 8.5 |
| 8.9  | Update `juniper-deploy/scripts/health_check.sh` (Phase 1) to display dependency status from readiness responses                                   | `scripts/health_check.sh`                           | 8.3, 8.4, 8.5 |
| 8.10 | Write unit tests for `_probe_dependency()` — healthy, unhealthy, timeout scenarios                                                                 | Test files per service                              | 8.2        |
| 8.11 | Write unit tests for enhanced readiness endpoints — all dependency combinations                                                                    | Test files per service                              | 8.3, 8.4, 8.5 |
| 8.12 | Write integration test: start full stack, verify readiness responses include dependency status                                                     | `juniper-deploy/scripts/test_health_enhanced.sh`    | 8.3, 8.4, 8.5 |
| 8.13 | Update Docker Compose `healthcheck` commands if response format changes affect health check parsing                                                | `juniper-deploy/docker-compose.yml`                 | 8.3, 8.4, 8.5 |
| 8.14 | Verify Kubernetes probe compatibility: ensure `httpGet` probes still work with new response format (HTTP 200 = healthy)                             | —                                                   | 8.3, 8.4, 8.5 |

### 8.9 Verification Procedure

```bash
# 1. Verify JuniperData readiness (standalone)
cd juniper-data
python -m juniper_data &
sleep 3
curl -s http://localhost:8100/v1/health/ready | python -m json.tool
# Expected: {"status": "ready", "service": "juniper-data", "dependencies": {"storage": {"status": "healthy", ...}}}
kill %1

# 2. Verify JuniperCascor readiness (with Data running)
cd juniper-deploy && make up
sleep 10
curl -s http://localhost:8200/v1/health/ready | python -m json.tool
# Expected: {"status": "ready", "dependencies": {"juniper_data": {"status": "healthy", "latency_ms": ...}}}

# 3. Verify JuniperCanopy readiness (full stack)
curl -s http://localhost:8050/v1/health/ready | python -m json.tool
# Expected: {"status": "ready", "dependencies": {"juniper_data": {"status": "healthy"}, "juniper_cascor": {"status": "healthy"}}}

# 4. Verify degraded status (stop CasCor, leave others running)
docker compose stop juniper-cascor
sleep 5
curl -s http://localhost:8050/v1/health/ready | python -m json.tool
# Expected: {"status": "degraded", "dependencies": {"juniper_cascor": {"status": "unhealthy", ...}}}

# 5. Verify startup fallback (Canopy with unreachable CasCor)
CASCOR_SERVICE_URL=http://localhost:9999 python src/main.py &
sleep 5
# Expected log: "JuniperCascor unreachable at http://localhost:9999 — falling back to demo mode"
curl -s http://localhost:8050/v1/health/ready | python -m json.tool
# Expected: {"details": {"mode": "demo"}}
kill %1

# 6. Verify Docker healthcheck compatibility
docker compose up -d
docker compose ps
# Expected: All services show "healthy" status (HTTP 200 still returned)

# 7. Run all service test suites
cd juniper-data && pytest tests/ -v
cd juniper-cascor/src/tests && bash scripts/run_tests.bash
cd JuniperCanopy/juniper_canopy/src && pytest tests/ -v
# Expected: All green, no regressions

# 8. Clean up
make down
```

### 8.10 Security Considerations

| Concern                                        | Mitigation                                                                                                          |
|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Health endpoints expose internal service URLs  | URLs are only internal Docker/localhost addresses. In production, restrict health endpoint access via network policy  |
| Dependency probes make outbound HTTP calls     | Probes use `urllib` with 5s timeout. No credentials sent (only `/v1/health/live` which is public)                   |
| Readiness response reveals service versions    | Already exposed in current implementation. Versions are public (PyPI packages). Not a security risk                  |
| Denial-of-service via readiness endpoint       | Probe calls are fast (< 5s timeout). Rate limiting can be added if needed. Health endpoints are lightweight          |
| Startup fallback to demo mode                  | Logged at WARNING level. Demo mode is safe (no external dependencies). Operator can monitor for unexpected fallbacks |

### 8.11 Performance Considerations

| Concern                                  | Impact                                                           | Mitigation                                                                                      |
|------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Dependency probes add latency to readiness | ~1-10ms per dependency (localhost HTTP). Total: ~5-20ms          | Probes run in sequence (max 2 dependencies). Well within Docker healthcheck timeout (10s)       |
| Probe timeout on unhealthy dependency     | Up to 5s if dependency is down and connection hangs              | `timeout=5.0` on `urllib.request.urlopen`. Readiness returns `"degraded"` after timeout          |
| Filesystem check in JuniperData           | `Path.is_dir()` + `glob("*.npz")` — ~1-5ms                     | Single directory listing. Dataset count is informational, not critical-path                       |
| Startup health verification blocks lifespan | ~5-10s if CasCor is unreachable (timeout + fallback)            | Non-blocking in practice — runs once at startup. Lifespan continues after fallback               |
| Concurrent readiness requests             | Each request probes dependencies independently                   | Probes are stateless and idempotent. Could add short-lived caching (~5s) if load is high         |

---

## Configuration Management — Overview

This section provides the implementation plan for configuration standardization recommended in [MICROSERVICES_ARCHITECTURE_ANALYSIS.md](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md), Section 5.

```bash
Phase 9 (Near-term):  Migrate JuniperCanopy to Pydantic BaseSettings and standardize
                       environment variable patterns across all three services
```

### Current Configuration Divergence

| Aspect                    | JuniperData                      | JuniperCascor                    | JuniperCanopy (Legacy)                    |
|---------------------------|----------------------------------|----------------------------------|-------------------------------------------|
| **Framework**             | Pydantic v2 `BaseSettings`       | Pydantic v2 `BaseSettings`       | YAML `ConfigManager` + env var overrides  |
| **Env prefix**            | `JUNIPER_DATA_`                  | `JUNIPER_CASCOR_`                | `CASCOR_`                                 |
| **`.env` file support**   | Yes (automatic via Pydantic)     | Yes (automatic via Pydantic)     | No                                        |
| **Case sensitivity**      | No (case_sensitive=False)        | No (case_sensitive=False)        | Yes                                       |
| **Nesting**               | Flat only                        | Flat only                        | Full (dot-notation, YAML hierarchy)       |
| **Validation**            | Pydantic type coercion           | Pydantic type coercion           | Manual `validate_training_param_value()`  |
| **Config file**           | None (env-only)                  | None (env-only)                  | `conf/app_config.yaml`                    |
| **Env var expansion**     | No                               | No                               | Yes (`${VAR}`, `${VAR:default}`)          |
| **Singleton access**      | `get_settings()` (`@lru_cache`)  | `get_settings()` (`@lru_cache`)  | `ConfigManager()` (singleton pattern)     |

### Key Inconsistencies

1. **Prefix divergence**: `JUNIPER_DATA_*`, `JUNIPER_CASCOR_*`, and `CASCOR_*` — three different naming patterns
2. **Architecture mismatch**: Two services use Pydantic BaseSettings; one uses YAML with manual env overrides
3. **No `.env` support in Canopy**: Requires environment variables set externally or YAML edits
4. **Case sensitivity mismatch**: Canopy is case-sensitive for env vars; others are not
5. **YAML-specific features at risk**: Canopy's nested config access (`config.get("training.parameters.epochs.default")`) and hot reload have no Pydantic equivalent without design work

---

## Phase 9: Configuration Standardization — Pydantic BaseSettings (Near-Term)

### 9.1 Objectives

- Migrate JuniperCanopy from YAML-based `ConfigManager` to Pydantic v2 `BaseSettings`
- Standardize the environment variable prefix to `JUNIPER_CANOPY_*` (matching the `JUNIPER_<SERVICE>_*` pattern)
- Maintain backward compatibility with `CASCOR_*` environment variables during a transition period
- Add `.env` file support to JuniperCanopy
- Create `.env.example` templates for all services with consistent documentation
- Preserve Canopy's training parameter validation and nested config access through Pydantic nested models

### 9.2 Prerequisites

| Requirement                     | Version   | Verification                                               |
|---------------------------------|-----------|------------------------------------------------------------|
| Python                          | >= 3.12   | `python --version`                                         |
| pydantic                        | >= 2.0    | `pip show pydantic`                                        |
| pydantic-settings               | >= 2.0    | `pip show pydantic-settings`                               |
| Existing Canopy tests green     | —         | `cd src && pytest tests/ -v` (3,215+ passed)               |
| Phase 5 complete (BackendProtocol) | —      | Backend factory no longer relies on ConfigManager singleton |

### 9.3 Current Configuration Divergence

**JuniperData settings** (`juniper_data/api/settings.py`):

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JUNIPER_DATA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    storage_path: str = "./data/datasets"
    host: str = "127.0.0.1"
    port: int = 8100
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]
    api_keys: Optional[list[str]] = None
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60
```

**JuniperCascor settings** (`src/api/settings.py`):

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JUNIPER_CASCOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    host: str = "127.0.0.1"
    port: int = 8200
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]
    ws_max_connections: int = 50
    ws_heartbeat_interval_sec: int = 30
```

**JuniperCanopy config** (`src/config_manager.py` + `conf/app_config.yaml`):

- YAML-based with `${VAR:default}` expansion
- Nested access: `config.get("application.server.host")`
- Training parameter validation with min/max/modifiable metadata
- Hot reload: `config.reload()`
- ~500 lines of custom config management code

### 9.4 Target Architecture

All three services use Pydantic v2 `BaseSettings` with consistent patterns:

```python
# Target pattern for all services:
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JUNIPER_<SERVICE>_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
```

**Prefix convention**:

| Service           | Current Prefix       | Target Prefix          |
|-------------------|----------------------|------------------------|
| JuniperData       | `JUNIPER_DATA_`      | `JUNIPER_DATA_` (no change) |
| JuniperCascor     | `JUNIPER_CASCOR_`    | `JUNIPER_CASCOR_` (no change) |
| JuniperCanopy     | `CASCOR_`            | `JUNIPER_CANOPY_`      |

### 9.5 JuniperCanopy Migration Design

Replace `ConfigManager` with a Pydantic `BaseSettings` class that preserves all current functionality.

**New file**: `src/settings.py`

```python
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class TrainingParamConfig(BaseModel):
    """Nested model replacing YAML training parameter config."""
    min: float
    max: float
    default: float
    modifiable_during_training: bool = False

    @field_validator("default")
    @classmethod
    def default_in_range(cls, v, info):
        data = info.data
        if "min" in data and "max" in data:
            if not data["min"] <= v <= data["max"]:
                raise ValueError(f"default {v} not in [{data['min']}, {data['max']}]")
        return v


class TrainingSettings(BaseModel):
    """Nested training parameters (replaces YAML training section)."""
    epochs: TrainingParamConfig = TrainingParamConfig(min=10, max=1000, default=500)
    learning_rate: TrainingParamConfig = TrainingParamConfig(min=0.0001, max=1.0, default=0.01)
    hidden_units: TrainingParamConfig = TrainingParamConfig(min=0, max=100, default=40)


class ServerSettings(BaseModel):
    """Server configuration (replaces YAML application.server section)."""
    host: str = "127.0.0.1"
    port: int = 8050
    debug: bool = False


class WebSocketSettings(BaseModel):
    """WebSocket configuration (replaces YAML backend.communication section)."""
    max_connections: int = 50
    heartbeat_interval: int = 30
    reconnect_attempts: int = 5
    reconnect_delay: int = 2


class Settings(BaseSettings):
    """JuniperCanopy application settings."""
    model_config = SettingsConfigDict(
        env_prefix="JUNIPER_CANOPY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",  # Enables JUNIPER_CANOPY_SERVER__PORT=8051
    )

    # Server
    server: ServerSettings = ServerSettings()

    # Training
    training: TrainingSettings = TrainingSettings()

    # WebSocket
    websocket: WebSocketSettings = WebSocketSettings()

    # Backend
    demo_mode: bool = False
    backend_path: str = "../../JuniperCascor/juniper_cascor"
    juniper_data_url: str = "http://localhost:8100"
    cascor_service_url: Optional[str] = None

    # Demo
    demo_update_interval: float = 1.0
    demo_cascade_every: int = 30

    # Logging
    log_level: str = "INFO"

    def get_training_defaults(self) -> dict:
        """Backward-compatible method matching ConfigManager.get_training_defaults()."""
        return {
            "epochs": self.training.epochs.default,
            "learning_rate": self.training.learning_rate.default,
            "hidden_units": self.training.hidden_units.default,
        }

    def validate_training_param(self, param: str, value: float) -> bool:
        """Backward-compatible validation matching ConfigManager.validate_training_param_value()."""
        config = getattr(self.training, param, None)
        if config is None:
            return False
        return config.min <= value <= config.max


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Nested env var access** (via `env_nested_delimiter="__"`):

```bash
# Flat settings
JUNIPER_CANOPY_LOG_LEVEL=DEBUG
JUNIPER_CANOPY_DEMO_MODE=1
JUNIPER_CANOPY_JUNIPER_DATA_URL=http://juniper-data:8100

# Nested settings (double underscore delimiter)
JUNIPER_CANOPY_SERVER__HOST=0.0.0.0
JUNIPER_CANOPY_SERVER__PORT=8051
JUNIPER_CANOPY_TRAINING__EPOCHS__DEFAULT=300
JUNIPER_CANOPY_WEBSOCKET__MAX_CONNECTIONS=100
```

### 9.6 Environment Variable Prefix Standardization

**Cross-service environment variable reference** (after migration):

| Variable                          | Service       | Purpose                          |
|-----------------------------------|---------------|----------------------------------|
| `JUNIPER_DATA_HOST`               | JuniperData   | Bind address                     |
| `JUNIPER_DATA_PORT`               | JuniperData   | Listen port                      |
| `JUNIPER_DATA_LOG_LEVEL`          | JuniperData   | Log level                        |
| `JUNIPER_DATA_STORAGE_PATH`       | JuniperData   | Dataset storage directory        |
| `JUNIPER_DATA_API_KEYS`           | JuniperData   | Authentication keys              |
| `JUNIPER_CASCOR_HOST`             | JuniperCascor | Bind address                     |
| `JUNIPER_CASCOR_PORT`             | JuniperCascor | Listen port                      |
| `JUNIPER_CASCOR_LOG_LEVEL`        | JuniperCascor | Log level                        |
| `JUNIPER_CANOPY_SERVER__HOST`     | JuniperCanopy | Bind address                     |
| `JUNIPER_CANOPY_SERVER__PORT`     | JuniperCanopy | Listen port                      |
| `JUNIPER_CANOPY_LOG_LEVEL`        | JuniperCanopy | Log level                        |
| `JUNIPER_CANOPY_DEMO_MODE`        | JuniperCanopy | Enable demo mode                 |
| `JUNIPER_CANOPY_CASCOR_SERVICE_URL` | JuniperCanopy | CasCor service URL             |
| `JUNIPER_DATA_URL`                | Shared        | JuniperData URL (used by CasCor + Canopy) |

### 9.7 Environment Profiles

Standardize `.env` file patterns across all services:

**`.env.example`** (per-service template — committed):

```bash
# juniper-data/.env.example
JUNIPER_DATA_HOST=127.0.0.1
JUNIPER_DATA_PORT=8100
JUNIPER_DATA_LOG_LEVEL=INFO
JUNIPER_DATA_STORAGE_PATH=./data/datasets
# JUNIPER_DATA_API_KEYS=["key1","key2"]  # Uncomment to enable auth
```

```bash
# JuniperCanopy/.env.example
JUNIPER_CANOPY_SERVER__HOST=127.0.0.1
JUNIPER_CANOPY_SERVER__PORT=8050
JUNIPER_CANOPY_LOG_LEVEL=INFO
JUNIPER_CANOPY_JUNIPER_DATA_URL=http://localhost:8100
# JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://localhost:8200  # Uncomment for service mode
# JUNIPER_CANOPY_DEMO_MODE=true  # Uncomment for demo mode
```

**`.env`** (per-service — NOT committed, in `.gitignore`):

Developer-specific overrides. Created by copying `.env.example`.

### 9.8 Backward Compatibility Strategy

The migration from `CASCOR_*` to `JUNIPER_CANOPY_*` environment variables requires a transition period.

**Strategy**: Pydantic `@field_validator` checks for legacy `CASCOR_*` variables and uses them as fallbacks:

```python
import os
import warnings

class Settings(BaseSettings):
    # ...

    @field_validator("demo_mode", mode="before")
    @classmethod
    def _check_legacy_demo_mode(cls, v):
        legacy = os.getenv("CASCOR_DEMO_MODE")
        if legacy is not None:
            warnings.warn(
                "CASCOR_DEMO_MODE is deprecated. Use JUNIPER_CANOPY_DEMO_MODE instead.",
                DeprecationWarning, stacklevel=2,
            )
            return legacy in ("1", "true", "True", "yes", "Yes")
        return v

    @field_validator("server", mode="before")
    @classmethod
    def _check_legacy_server_vars(cls, v):
        if isinstance(v, dict):
            if "host" not in v and os.getenv("CASCOR_SERVER_HOST"):
                v["host"] = os.getenv("CASCOR_SERVER_HOST")
                warnings.warn("CASCOR_SERVER_HOST is deprecated. Use JUNIPER_CANOPY_SERVER__HOST.", DeprecationWarning)
            if "port" not in v and os.getenv("CASCOR_SERVER_PORT"):
                v["port"] = int(os.getenv("CASCOR_SERVER_PORT"))
                warnings.warn("CASCOR_SERVER_PORT is deprecated. Use JUNIPER_CANOPY_SERVER__PORT.", DeprecationWarning)
        return v
```

**Deprecation timeline**:

| Phase              | Legacy `CASCOR_*` vars | New `JUNIPER_CANOPY_*` vars | Behavior                           |
|--------------------|------------------------|-----------------------------|------------------------------------|
| Initial migration  | Supported (fallback)   | Primary                     | Legacy vars work but log warnings  |
| +6 months          | Supported (warnings)   | Primary                     | Louder deprecation warnings        |
| +12 months         | Removed                | Only                        | Legacy vars ignored                |

### 9.9 Implementation Tasks

| #    | Task                                                                                                                                          | Files                                                    | Depends On |
|------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|------------|
| 9.1  | Create `src/settings.py` with `Settings` Pydantic BaseSettings class (Section 9.5)                                                           | `src/settings.py` (new)                                  | —          |
| 9.2  | Create nested Pydantic models: `TrainingParamConfig`, `TrainingSettings`, `ServerSettings`, `WebSocketSettings`                               | `src/settings.py`                                        | 9.1        |
| 9.3  | Implement backward-compatible methods: `get_training_defaults()`, `validate_training_param()`                                                  | `src/settings.py`                                        | 9.2        |
| 9.4  | Implement legacy `CASCOR_*` fallback validators with deprecation warnings (Section 9.8)                                                       | `src/settings.py`                                        | 9.1        |
| 9.5  | Create `.env.example` for JuniperCanopy with all `JUNIPER_CANOPY_*` variables documented                                                      | `.env.example` (new)                                     | 9.1        |
| 9.6  | Update `.gitignore` to exclude `.env` but not `.env.example`                                                                                   | `.gitignore`                                             | 9.5        |
| 9.7  | Refactor `main.py` to import `get_settings()` instead of `ConfigManager()` for all configuration access                                       | `src/main.py`                                            | 9.1        |
| 9.8  | Refactor `demo_mode.py` to use `get_settings()` instead of `ConfigManager()` for demo configuration                                           | `src/demo_mode.py`                                       | 9.1        |
| 9.9  | Update all source files that import `ConfigManager` to use `get_settings()` — search for `from config_manager import`                          | Multiple `src/*.py` files                                | 9.1        |
| 9.10 | Write unit tests for `Settings` — default values, env overrides, nested models, validation, legacy fallback                                    | `src/tests/unit/test_settings.py` (new)                  | 9.1        |
| 9.11 | Write migration test: verify `CASCOR_*` env vars produce same behavior as `JUNIPER_CANOPY_*` equivalents                                      | `src/tests/unit/test_settings_migration.py` (new)        | 9.4        |
| 9.12 | Update `conftest.py` — replace `ConfigManager` singleton reset with `get_settings.cache_clear()`                                               | `src/tests/conftest.py`                                  | 9.7        |
| 9.13 | Run full test suite: verify all 3,215+ tests pass with new settings                                                                            | —                                                        | 9.7-9.12   |
| 9.14 | Deprecate `ConfigManager` — mark class as deprecated, add import warning, do NOT delete yet                                                    | `src/config_manager.py`                                  | 9.13       |
| 9.15 | Update JuniperCanopy AGENTS.md configuration sections to reference `JUNIPER_CANOPY_*` variables                                                | `AGENTS.md`                                              | 9.7        |
| 9.16 | Update `juniper-deploy/.env.example` with new `JUNIPER_CANOPY_*` variable names                                                                | `juniper-deploy/.env.example`                            | 9.7        |
| 9.17 | Update `juniper-deploy/docker-compose.yml` Canopy service `environment` block with new variable names                                          | `juniper-deploy/docker-compose.yml`                      | 9.7        |

### 9.10 Verification Procedure

```bash
cd JuniperCanopy/juniper_canopy

# 1. Verify default settings load correctly
python -c "
from settings import get_settings
s = get_settings()
print(f'Host: {s.server.host}')
print(f'Port: {s.server.port}')
print(f'Training defaults: {s.get_training_defaults()}')
print(f'Demo mode: {s.demo_mode}')
print('Settings load: OK')
"

# 2. Verify new env vars work
JUNIPER_CANOPY_SERVER__PORT=8051 JUNIPER_CANOPY_DEMO_MODE=true python -c "
from settings import get_settings
s = get_settings()
assert s.server.port == 8051, f'Expected 8051, got {s.server.port}'
assert s.demo_mode is True
print('New env vars: OK')
"

# 3. Verify legacy CASCOR_* fallback works (with deprecation warning)
CASCOR_DEMO_MODE=1 python -W all -c "
from settings import get_settings
s = get_settings()
assert s.demo_mode is True
print('Legacy fallback: OK (check for deprecation warning above)')
"
# Expected: DeprecationWarning: CASCOR_DEMO_MODE is deprecated. Use JUNIPER_CANOPY_DEMO_MODE instead.

# 4. Verify nested env vars
JUNIPER_CANOPY_TRAINING__EPOCHS__DEFAULT=300 python -c "
from settings import get_settings
s = get_settings()
assert s.training.epochs.default == 300
print(f'Training epochs default: {s.training.epochs.default}')
print('Nested env vars: OK')
"

# 5. Verify validation
python -c "
from settings import get_settings
s = get_settings()
assert s.validate_training_param('epochs', 500) is True
assert s.validate_training_param('epochs', 9999) is False
print('Validation: OK')
"

# 6. Verify .env file loading
echo 'JUNIPER_CANOPY_LOG_LEVEL=DEBUG' > .env
python -c "
from settings import get_settings
s = get_settings()
assert s.log_level == 'DEBUG'
print(f'Log level from .env: {s.log_level}')
print('.env loading: OK')
"
rm .env

# 7. Run full test suite
cd src && pytest tests/ -v
# Expected: 3,215+ passed, 0 failed

# 8. Verify demo mode still works
./demo
# Open http://localhost:8050 — all 4 tabs should display data
```

### 9.11 Security Considerations

| Concern                                          | Mitigation                                                                                                    |
|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| `.env` file committed with secrets               | `.gitignore` excludes `.env`. `.env.example` contains only non-sensitive defaults                             |
| Legacy `CASCOR_*` vars bypass new validation     | Legacy validators apply the same Pydantic validation. No bypass possible                                      |
| Deprecation warnings in production logs          | Warnings are Python `DeprecationWarning` — suppressed by default in production. Visible with `-W all`         |
| Pydantic exposes settings in repr/logging        | Use `Field(repr=False)` for sensitive fields (e.g., `api_key`). Default Pydantic repr is safe for most fields |
| ConfigManager removal breaks downstream tools    | `ConfigManager` is deprecated, not removed. Import warning guides migration. 12-month timeline                |

### 9.12 Performance Considerations

| Concern                              | Impact                                                           | Mitigation                                                                                   |
|--------------------------------------|------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Pydantic model initialization        | ~1-5ms at startup (one-time)                                     | `@lru_cache` on `get_settings()` ensures single initialization                              |
| YAML config loading removed          | Eliminates ~5-10ms YAML parse at startup                         | Net performance improvement — Pydantic env loading is faster than YAML parse + expansion     |
| Nested model validation              | ~0.1ms per access (Pydantic validation is pre-computed at init)  | All validation happens at startup. Runtime access is plain attribute access (~0ns overhead)    |
| Legacy fallback validator overhead   | ~0.1ms per `os.getenv` check at startup                          | Negligible. Runs once. Removed after transition period                                        |
| `.env` file parsing                  | ~1ms at startup (small file)                                     | One-time cost. Faster than YAML parsing                                                       |

---

## Cross-Phase Concerns

### Health Check Standardization

All phases depend on consistent health endpoints. The current implementation is already well-structured:

| Endpoint               | Purpose                                      | Used By                                                |
|------------------------|----------------------------------------------|--------------------------------------------------------|
| `GET /v1/health`       | Combined health check (backward compatible)  | Docker Compose healthcheck, `wait_for_services.sh`     |
| `GET /v1/health/live`  | Liveness — is the process running?           | Kubernetes livenessProbe, systemd watchdog             |
| `GET /v1/health/ready` | Readiness — can the service handle requests? | Kubernetes readinessProbe, Phase 3 Prometheus scraping |

**Enhancement planned**: [Phase 8](#phase-8-enhanced-health-checks-with-dependency-status-immediate) adds dependency health status to `/v1/health/ready` responses with standardized `ReadinessResponse` Pydantic models (see [MICROSERVICES_ARCHITECTURE_ANALYSIS.md, Section 4.3](./MICROSERVICES_ARCHITECTURE_ANALYSIS.md#43-health-check-pattern-recommendation)).

### Logging and Log Aggregation

| Phase   | Logging Method                                                 | Aggregation                                  |
|---------|----------------------------------------------------------------|----------------------------------------------|
| Phase 1 | `docker compose logs -f`                                       | Interleaved, color-coded by service          |
| Phase 2 | `journalctl --user -u juniper-*`                               | systemd journal, filterable by unit          |
| Phase 3 | `docker compose logs -f` + optional Loki                       | Same as Phase 1; Loki for persistent queries |
| Phase 4 | `kubectl logs -n juniper -l app.kubernetes.io/part-of=juniper` | Kubernetes; Loki/EFK for persistence         |

All services should log to **stdout/stderr** (not files) so that the orchestrator captures output. The current implementations already do this when running under uvicorn.

### Configuration Parity

Environment variable names must be consistent across all four phases. The same `JUNIPER_DATA_URL=http://juniper-data:8100` should work whether the service name resolves via:

- `localhost` (Phase 2, systemd — use `http://localhost:8100`)
- Docker Compose DNS (Phase 1/3 — use `http://juniper-data:8100`)
- Kubernetes DNS (Phase 4 — use `http://juniper-data:8100` or `http://juniper-data.juniper.svc.cluster.local:8100`)

The `.env` / `juniper.env` / ConfigMap files differ per phase but use the same variable names. Applications never need to know which orchestrator is in use.

---

## Phase Dependency Map

### Coordinated Application Startup (Phases 1-4)

```bash
Phase 1: Makefile + Docker Compose
    │
    ├── Phase 2: systemd (independent — runs natively, no Docker)
    │
    └── Phase 3: Docker Compose Profiles
            │
            └── Phase 4: Kubernetes (translates Compose/Helm)
```

- **Phase 1 and Phase 2** are independent — they can be implemented in parallel
- **Phase 3** builds on Phase 1 (extends the same `docker-compose.yml`)
- **Phase 4** builds on Phase 3 conceptually (same services, same images, same health endpoints) but the manifests are written from scratch (or generated via `kompose convert`)

### Modes of Operation (Phases 5-7)

```bash
Phase 5: BackendProtocol Interface Refactor
    │
    └── Phase 6: Client Library Fakes (depends on protocol for fake backend wiring)

Phase 7: Docker Compose Demo Profile (independent — infrastructure only)
    │
    └── depends on Phase 1 (Makefile targets) and Phase 3 (Compose profiles)
```

- **Phase 5** is independent of Phases 1-4 — it refactors application code, not infrastructure
- **Phase 6** depends on Phase 5 (the `BackendProtocol` defines the interface fakes must match)
- **Phase 7** depends on Phase 1 (Makefile exists) and Phase 3 (profile infrastructure); independent of Phases 5-6

### Service Discovery and Health Checking (Phase 8)

```bash
Phase 8: Enhanced Health Checks (independent — applies to all services)
    │
    └── benefits from Phase 5 (BackendProtocol provides backend_type for Canopy readiness)
```

- **Phase 8** is independent of infrastructure phases (1-4) — it modifies service application code
- **Phase 8** benefits from Phase 5 (`backend.backend_type` in Canopy's readiness response) but does not require it
- Phase 8's startup health verification (CAN-HIGH-001) requires Phase 5 for graceful backend fallback

### Configuration Management (Phase 9)

```bash
Phase 9: Configuration Standardization (depends on Phase 5 for clean backend factory)
    │
    └── updates Phase 7 Docker Compose env vars (JUNIPER_CANOPY_* prefix)
```

- **Phase 9** depends on Phase 5 — the backend factory must not rely on `ConfigManager` singleton
- **Phase 9** triggers updates to Phase 7's Docker Compose `environment` blocks
- Phase 9 is independent of Phases 1-4 and Phase 8

### Cross-Track Dependencies

```bash
Startup Track:      Phase 1 → Phase 3 → Phase 7 (demo profile extends Compose profiles)
Code Track:         Phase 5 → Phase 6 (protocol defines fake interfaces)
Health Track:       Phase 8 (independent, benefits from Phase 5)
Config Track:       Phase 9 (depends on Phase 5, updates Phase 7)
```

Phase 7 bridges startup and code tracks. Phase 9 bridges code and startup tracks (updates Compose env vars).

**Coexistence**: All nine phases can coexist. A developer can use:

- `make up` (Phase 1/3) for containerized development
- `make demo` (Phase 7) for auto-configured demo stack
- `juniper-ctl start` (Phase 2) for native execution with GPU
- `helm install` (Phase 4) for Kubernetes testing

The same Dockerfiles, health endpoints, and environment variable conventions are shared across all phases.

---

## Document History

| Date       | Author                    | Changes                                                                                                         |
|------------|---------------------------|-----------------------------------------------------------------------------------------------------------------|
| 2026-02-26 | Paul Calnon / Claude Code | Added Health Checks (Phase 8) and Configuration Standardization (Phase 9) roadmaps                             |
| 2026-02-26 | Paul Calnon / Claude Code | Added Modes of Operation roadmap: Phase 5 (BackendProtocol), Phase 6 (Client Fakes), Phase 7 (Demo Profile)    |
| 2026-02-25 | Paul Calnon / Claude Code | Initial creation: detailed development roadmaps for all four startup orchestration phases                       |

---
