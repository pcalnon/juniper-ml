# Juniper Project — Outstanding Development Items

**Date**: 2026-04-19
**Version**: 2.0.0
**Status**: Current — Validated against all codebases
**Scope**: All incomplete development work across the Juniper ecosystem
**Sources**: 3 consolidated development records + deep audit of 5 additional repos (cascor-client, cascor-worker, data, data-client, deploy)

---

## Table of Contents

- [1. Purpose and Methodology](#1-purpose-and-methodology)
- [2. Validation Summary](#2-validation-summary)
- [3. Items Previously Incomplete — Now Fixed](#3-items-previously-incomplete--now-fixed)
- [4. Security Issues](#4-security-issues)
- [5. Active Bugs (Confirmed Still Present)](#5-active-bugs-confirmed-still-present)
- [6. Code Quality and Cleanup](#6-code-quality-and-cleanup)
- [7. Dashboard Enhancements](#7-dashboard-enhancements)
- [8. WebSocket Migration (R5-01 Remaining Phases)](#8-websocket-migration-r5-01-remaining-phases)
- [9. Microservices and Infrastructure](#9-microservices-and-infrastructure)
- [10. CasCor Algorithm and Feature Enhancements](#10-cascor-algorithm-and-feature-enhancements)
- [11. Cross-Repository Alignment Issues](#11-cross-repository-alignment-issues)
- [12. Housekeeping and Broken References](#12-housekeeping-and-broken-references)
- [13. juniper-deploy Outstanding Items](#13-juniper-deploy-outstanding-items)
- [14. juniper-data Outstanding Items](#14-juniper-data-outstanding-items)
- [15. Client Library Outstanding Items](#15-client-library-outstanding-items)
- [16. Source Document Lineage](#16-source-document-lineage)

---

## 1. Purpose and Methodology

This document consolidates all **currently incomplete** development work across the Juniper ecosystem by cross-referencing three consolidated development records:

| Source Document                       | Repository     | Items Documented                                      |
|---------------------------------------|----------------|-------------------------------------------------------|
| `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | juniper-ml     | 91+ items across 16 source documents                  |
| `CONSOLIDATED_DEVELOPMENT_HISTORY.md` | juniper-canopy | 99+ issues, 20 P5-RC root causes, Phases 0–3 features |
| `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | juniper-cascor | ~120 items across 12 source documents                 |

**Validation method**: Three specialized sub-agents independently validated every incomplete item against the live codebases (juniper-cascor, juniper-canopy, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy, juniper-ml) using file reads, grep searches, and structural analysis.

**Status legend**:

| Symbol | Meaning                                         |
|--------|-------------------------------------------------|
| ✅     | Fixed since last consolidation (newly resolved) |
| 🔴     | Still open — confirmed not implemented          |
| ⚠️     | Partially fixed — some elements still missing   |
| 🐛     | Bug confirmed still present                     |
| 🔵     | Deferred — explicitly decided to defer          |

---

## 2. Validation Summary

| Category                   | Previously Open | Now Fixed | Still Open | Partially Fixed |
|----------------------------|-----------------|-----------|------------|-----------------|
| Security                   | 4 + 2 new       | 0         | 6          | 0               |
| Active Bugs (cascor)       | 9               | 3         | 6          | 0               |
| Active Bugs (canopy)       | 3               | 0         | 2          | 1               |
| Active Bugs (data/clients) | 0 + 7 new       | 0         | 7          | 0               |
| Dashboard Augmentation     | 5               | 4         | 0          | 1               |
| WebSocket Migration        | 6 phases        | 2         | 4          | 0               |
| Infrastructure             | 7               | 0         | 6          | 1               |
| Deploy Infrastructure      | 0 + 11 new      | 0         | 11         | 0               |
| Cross-Repo Alignment       | 3 + 3 new       | 0         | 6          | 0               |
| Housekeeping               | 4 + 5 new       | 0         | 9          | 0               |
| **Total tracked**          | **41 + 28 new** | **9**     | **60**     | **3**           |

---

## 3. Items Previously Incomplete — Now Fixed

The following items were listed as incomplete in the source documents but are **now verified as implemented** in the current codebase:

| Item                                            | Source                                 | Repo   | Evidence                                                                                                                |
|-------------------------------------------------|----------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------|
| **Task 2 Ph1**: Metadata-only graceful handling | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `dataset_plotter.py:361-364` — renders `"Dataset loaded (metadata only)"` empty plot                                    |
| **Task 1A**: Validation loss/accuracy overlays  | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:1449` — `_add_validation_overlay()` for val_loss (L1378) and val_accuracy (L1623)                     |
| **Task 1C**: Learning rate metric card          | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:441` — LR card with `_update_learning_rate_handler()` at L1041                                        |
| **Task 1D**: Phase duration display             | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:157` — `phase-duration` ID; `_update_phase_duration_handler()` at L1082                               |
| **Phase C**: WebSocket `set_params`             | juniper-ml R5-01                       | canopy | `settings.py:182` — `use_websocket_set_params: bool = True`; `cascor_service_adapter.py:454,642` routes via WS          |
| **Phase D**: WS control buttons                 | juniper-ml R5-01                       | canopy | `settings.py:186` — `enable_ws_control_buttons: bool = True`; `dashboard_manager.py:1898` registers clientside callback |
| **Task 2 Ph2**: Dataset data endpoint           | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `cascor_service_adapter.py:989` — `get_dataset_data()` delegates to client                                              |
| **Per-IP connection cap (canopy)**              | juniper-ml R5-01                       | canopy | `settings.py:99` — `max_connections_per_ip: int = 5`; `websocket_manager.py:269-291` enforces                           |
| **OPT-3**: Persistent output layer              | juniper-cascor dev record              | cascor | `cascade_correlation.py:1603-1607` — intentional fresh nn.Linear per call (documented design decision)                  |

---

## 4. Security Issues

All items confirmed **still open** in current codebases.

| ID     | Severity   | Repository     | Description                                                       | File                                      | Evidence                                                                               |
|--------|------------|----------------|-------------------------------------------------------------------|-------------------------------------------|----------------------------------------------------------------------------------------|
| SEC-01 | **HIGH**   | juniper-data   | API key comparison not constant-time — timing side-channel attack | `juniper_data/api/security.py:59`         | Uses `api_key in self._api_keys` (set membership) — should use `hmac.compare_digest()` |
| SEC-02 | **MEDIUM** | juniper-data   | Rate limiter memory unbounded — DoS vector                        | `juniper_data/api/security.py`            | `_counters` `defaultdict` grows without limit; no eviction, no TTL, no max-size        |
| SEC-03 | **MEDIUM** | juniper-cascor | No per-IP WebSocket connection limiting                           | `src/api/settings.py`                     | Only `ws_max_connections: 50` (global). No `ws_max_connections_per_ip` setting exists  |
| SEC-04 | **LOW**    | juniper-data   | Sync dataset generation blocks event loop                         | `juniper_data/api/routes/datasets.py:107` | `generator_class.generate(params)` is synchronous inside `async def` endpoint          |

---

## 5. Active Bugs (Confirmed Still Present)

### 5.1 juniper-cascor

| ID        | Severity   | Description                                                                        | File(s)                                                                           | Evidence                                                                                                 |
|-----------|------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| BUG-CC-01 | **MEDIUM** | `create_topology_message()` is dead code — topology changes never broadcast via WS | `src/api/websocket/messages.py:72`                                                | Defined and exported but zero production callers. Only used in tests                                     |
| BUG-CC-02 | **MEDIUM** | `cascade_add` correlation hardcoded to `0.0`                                       | `src/api/lifecycle/manager.py:427-430`                                            | `monitor.on_cascade_add(hidden_unit_index=i, correlation=0.0)` — actual correlation is lost              |
| BUG-CC-03 | **MEDIUM** | `or` fallback bugs for falsy values in spiral_problem.py                           | `src/spiral_problem/spiral_problem.py:600-608,1250-1262,1411-1419`                | `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` values silently overridden |
| BUG-CC-04 | **LOW**    | Version strings inconsistent across file headers                                   | `src/main.py` (0.3.1), `cascade_correlation.py` (0.3.2), `pyproject.toml` (0.4.0) | All three disagree                                                                                       |
| BUG-CC-05 | **LOW**    | `remote_client_0.py` has hardcoded old monorepo path                               | `src/remote_client/remote_client_0.py:16`                                         | `sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")`                  |
| BUG-CC-06 | **LOW**    | 32 test files have hardcoded `sys.path.append` to old monorepo                     | `src/tests/` (32 files)                                                           | Stale path references from pre-polyrepo era                                                              |

### 5.2 juniper-canopy

| ID        | Severity   | Description                                                 | File(s)                             | Evidence                                                                                                             |
|-----------|------------|-------------------------------------------------------------|-------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| BUG-CN-01 | **HIGH**   | `_stop.clear()` race in `_perform_reset()` — outside lock   | `src/demo_mode.py:1617`             | Second call site at L1617 is outside the lock block (lock only covers L1615-1616)                                    |
| BUG-CN-02 | **HIGH**   | DashboardManager god class (3,232 lines)                    | `src/frontend/dashboard_manager.py` | Still growing — was 3,007 at code review time, now 3,232                                                             |
| BUG-CN-03 | **MEDIUM** | 226 `hasattr` guards in test files silently skip test logic | `src/tests/` (226 occurrences)      | Top offenders: `test_dashboard_manager.py` (17), `test_config_refactoring.py` (17), `test_decision_boundary.py` (14) |

---

## 6. Code Quality and Cleanup

### 6.1 juniper-cascor — Stale Code Removal

| ID        | Priority | Description                                                                                      | File(s)                                                                                  | Effort      |
|-----------|----------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-------------|
| CLN-CC-01 | **P2**   | Delete legacy `remote_client/` directory (3 files) — superseded by juniper-cascor-worker         | `src/remote_client/`                                                                     | 10 min      |
| CLN-CC-02 | **P2**   | Delete stale `check.py` duplicate (600 lines) — copy of spiral_problem.py                        | `src/spiral_problem/check.py`                                                            | 10 min      |
| CLN-CC-03 | **P2**   | Remove 9 local `import traceback` in cascade_correlation.py — uncomment line 64 top-level import | `cascade_correlation.py:64,1719,1932,2270,2778,2804,2971,3277,3290,3775` + 4 other files | 30 min      |
| CLN-CC-04 | **P2**   | Enable mypy strict mode                                                                          | `pyproject.toml`                                                                         | M           |
| CLN-CC-05 | **P2**   | Legacy spiral code — ~20 trivial getter/setter methods, no `@deprecated` markers                 | `src/spiral_problem/spiral_problem.py` (53 methods)                                      | M           |
| CLN-CC-06 | **P3**   | Remove "Roll" concept in CandidateUnit                                                           | candidate_unit.py                                                                        | 🔵 Deferred |
| CLN-CC-07 | **P3**   | Candidate factory refactor — all creation through `_create_candidate_unit()`                     | cascade_correlation.py                                                                   | 🔵 Deferred |
| CLN-CC-08 | **P3**   | Remove commented-out code blocks                                                                 | Multiple files                                                                           | 🔵 Deferred |
| CLN-CC-09 | **P3**   | Line length reduction to 120 characters                                                          | Multiple files                                                                           | 🔵 Deferred |

### 6.2 juniper-canopy — Code Quality

| ID        | Priority | Description                                             | Evidence                                                                       | Effort |
|-----------|----------|---------------------------------------------------------|--------------------------------------------------------------------------------|--------|
| CLN-CN-01 | **P2**   | `theme-table` CSS class never implemented               | No `.theme-table` in any CSS file — conditional `is_dark` styling used instead | S      |
| CLN-CN-02 | **P2**   | NPZ validation only in DemoMode, not ServiceBackend     | `_validate_npz_arrays()` exists only in `demo_mode.py:767`                     | S      |
| CLN-CN-03 | **P2**   | Performance test suite minimal — only 1 test file       | `src/tests/performance/test_button_responsiveness.py` only                     | M      |
| CLN-CN-04 | **P2**   | JuniperData-specific error handling missing             | Only cascor-client errors caught; no juniper-data-client error classes         | M      |
| CLN-CN-05 | **P3**   | DashboardManager extraction (3,232 → component classes) | Blocked by R5-01 Phase B stability                                             | L      |

---

## 7. Dashboard Enhancements

### 7.1 Canopy Enhancement Backlog (CAN-000 through CAN-021)

All items 🔴 NOT STARTED unless otherwise noted.

| ID       | Module            | Description                                                               | Priority |
|----------|-------------------|---------------------------------------------------------------------------|----------|
| CAN-000  | Meta Param Menu   | Periodic updates pause when Apply Parameters button active                | P2       |
| CAN-001  | Training Metrics  | Training Loss time window toggle/dropdown                                 | P3       |
| CAN-002  | Training Metrics  | Custom rolling time window for Training Loss graph                        | P3       |
| CAN-003  | Training Metrics  | Retain candidate pool data per node addition; expandable "Previous Pools" | P3       |
| CAN-004  | Meta Param Tuning | New Tab for all exposed meta parameters                                   | P3       |
| CAN-005  | Meta Param Tuning | Pin/Unpin meta params from Tuning Tab to left side menu                   | P3       |
| CAN-006  | Meta Param Tuning | Network train epoch count parameter                                       | P3       |
| CAN-007  | Meta Param Tuning | Candidate pool training epoch count parameter                             | P3       |
| CAN-008  | Meta Param Tuning | Candidate pool node count parameter                                       | P3       |
| CAN-009  | Meta Param Tuning | Correlation threshold parameter                                           | P3       |
| CAN-010  | Meta Param Tuning | Optimizer type meta parameter                                             | P3       |
| CAN-011  | Meta Param Tuning | Activation function meta parameter                                        | P3       |
| CAN-012  | Meta Param Tuning | Number of top candidate nodes to select                                   | P3       |
| CAN-013  | Meta Param Tuning | Candidate node integration mode                                           | P3       |
| CAN-014  | Training Metrics  | Snapshot captures tuning values throughout training                       | P3       |
| CAN-015  | Training Metrics  | Snapshot replay with live tuning → new training session                   | P3       |
| CAN-016a | All               | Save/Load dashboard layout state                                          | P3       |
| CAN-016b | Dataset           | Import/Generate new dataset (file, URL, REST)                             | P3       |
| CAN-017  | All               | Tooltips on all dashboard controls                                        | P3       |
| CAN-018  | All               | Right-click tutorial descriptions with doc links                          | P4       |
| CAN-019  | All               | Walk-through style tutorial with highlighted steps                        | P4       |
| CAN-020  | All               | Show network at specific hierarchy level                                  | P4       |
| CAN-021  | All               | Show network in population (ensemble view)                                | P4       |

---

## 8. WebSocket Migration (R5-01 Remaining Phases)

### 8.1 Phases Now Complete

| Phase    | Goal                                                 | Status                                          |
|----------|------------------------------------------------------|-------------------------------------------------|
| 0-cascor | seq/replay/resume on `/ws/training`                  | ✅ Complete                                     |
| A-SDK    | `CascorControlStream.set_params()` with `command_id` | ✅ Complete                                     |
| B-pre-a  | Origin allowlist, per-IP cap, audit logging          | ✅ Complete (canopy); ⚠️ Cascor missing per-IP  |
| B        | Polling elimination — browser WS drain bridge        | ✅ Complete — flag default `True`               |
| C        | WebSocket `set_params` (canopy adapter)              | ✅ Complete — `use_websocket_set_params: True`  |
| D        | Training control buttons via WebSocket               | ✅ Complete — `enable_ws_control_buttons: True` |

### 8.2 Phases Still Incomplete

| Phase | Goal                                           | Status                                         | Priority | Effort |
|-------|------------------------------------------------|------------------------------------------------|----------|--------|
| E     | Backpressure pump tasks                        | 🔴 NOT STARTED — conditional on telemetry data | P3       | M      |
| F     | Heartbeat jitter                               | 🔴 NOT STARTED                                 | P3       | S      |
| G     | Integration tests (cascor `set_params` via WS) | 🔴 NOT STARTED                                 | P2       | M      |
| H     | `_normalize_metric` audit                      | 🔴 NOT STARTED                                 | P3       | S      |

---

## 9. Microservices and Infrastructure

### 9.1 Completed Phases

| Phase   | Description                                          | Status      |
|---------|------------------------------------------------------|-------------|
| Phase 1 | Critical startup/shutdown fixes (plant/chop scripts) | ✅ Complete |
| Phase 2 | systemd service units + ctl scripts (all 4 services) | ✅ Complete |
| Phase 3 | Worker Dockerfile, docker-compose, systemd           | ✅ Complete |
| Phase 4 | Kubernetes Helm chart (23 templates)                 | ✅ Complete |

### 9.2 Phase 5: Observability & Hardening — INCOMPLETE

| Step | Task                                             | Status               | Evidence                                                          |
|------|--------------------------------------------------|----------------------|-------------------------------------------------------------------|
| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |
| 5.2  | Define alert rules for service availability      | ✅ Complete          | `alert_rules.yml` has 6 rule groups, 12 real alerts               |
| 5.3  | Standardize health endpoints across all services | 🔴 NOT STARTED       | Health endpoint formats differ across services                    |
| 5.4  | Volume backup/restore documentation              | 🔴 NOT STARTED       | No backup docs exist                                              |
| 5.5  | Startup validation test suite                    | 🔴 NOT STARTED       | No startup script tests in juniper-ml                             |

### 9.3 Microservices Architecture Roadmap (Phases 5–9)

| Phase | Description                                           | Status                                               |
|-------|-------------------------------------------------------|------------------------------------------------------|
| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |
| 6     | Client Library Fakes                                  | ✅ Complete (FakeCascorClient, FakeDataClient)       |
| 7     | Docker Compose Demo Profile                           | ✅ Complete (demo profile in juniper-deploy)         |
| 8     | Enhanced Health Checks with Dependency Status         | ⚠️ Partial — some services have dependency reporting |
| 9     | Configuration Standardization (Pydantic BaseSettings) | ✅ Complete for cascor and data; canopy migrated     |

---

## 10. CasCor Algorithm and Feature Enhancements

All items 🔴 NOT STARTED.

### Training Control

| ID      | Description                                                | Priority |
|---------|------------------------------------------------------------|----------|
| CAS-002 | Separate epoch limits for full network and candidate nodes | P3       |
| CAS-003 | Max train session iterations meta parameter                | P3       |
| CAS-006 | Auto-snap best network when new best accuracy achieved     | P3       |

### Algorithm Enhancements

| ID      | Description                                           | Priority |
|---------|-------------------------------------------------------|----------|
| ENH-006 | Flexible optimizer system (Adam, SGD, RMSprop, AdamW) | P3       |
| ENH-007 | N-best candidate layer selection                      | P3       |

### Network Architecture

| ID      | Description                                              | Priority |
|---------|----------------------------------------------------------|----------|
| CAS-008 | Network hierarchy management (multi-hierarchical CasCor) | P4       |
| CAS-009 | Network population management (ensemble approaches)      | P4       |

### Storage & Infrastructure

| ID         | Description                                   | Priority       |
|------------|-----------------------------------------------|----------------|
| CAS-010    | Snapshot vector DB storage (indexed by UUID)  | P4             |
| P3-NEW-003 | GPU/CUDA support for training                 | P4 (XL effort) |
| —          | Large file refactoring (no file > 2000 lines) | P3             |
| —          | Auto-generated API docs (MkDocs/Sphinx)       | P3             |

---

## 11. Cross-Repository Alignment Issues

All items confirmed **still open**.

| ID        | Severity     | Repositories           | Description                                                                                                    | Evidence                                                              |
|-----------|--------------|------------------------|----------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| XREPO-01  | **CRITICAL** | data-client ↔ data     | Generator name `"circle"` vs server's `"circles"` — client requests will fail with 400                         | `juniper_data_client/constants.py:90` — `GENERATOR_CIRCLE = "circle"` |
| XREPO-01b | **CRITICAL** | data-client ↔ data     | `GENERATOR_MOON = "moon"` — server has **no moon generator** at all                                            | `juniper_data_client/constants.py:91`                                 |
| XREPO-01c | **MEDIUM**   | data-client ↔ data     | Client missing constants for 5 server generators: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi` | Only `spiral`, `xor`, `circle`, `moon` defined                        |
| XREPO-02  | **MEDIUM**   | cascor-client          | 503 not in `RETRYABLE_STATUS_CODES` — transient unavailability not retried                                     | `constants.py:31` — `RETRYABLE_STATUS_CODES = [502, 504]`             |
| XREPO-03  | **MEDIUM**   | cascor-client          | No `FakeCascorControlStream` — testing gap for WS control                                                      | `testing/` has FakeClient and FakeTrainingStream only                 |
| XREPO-04  | **MEDIUM**   | cascor-worker ↔ cascor | Protocol constants alignment is manual — no CI automation for bit-identity verification                        | Wave 5 verified, but cascor change could silently break worker        |

---

## 12. Housekeeping and Broken References

| ID     | Repository     | Description                                                                         | Priority |
|--------|----------------|-------------------------------------------------------------------------------------|----------|
| HSK-01 | juniper-canopy | 3 broken symlinks in `notes/development/` pointing to deleted juniper-ml files      | P3       |
| HSK-02 | juniper-cascor | `src/remote_client/` directory still exists (3 files) — superseded by cascor-worker | P2       |
| HSK-03 | juniper-cascor | `src/spiral_problem/check.py` — 600-line stale duplicate                            | P2       |
| HSK-04 | juniper-cascor | 32 test files with hardcoded `sys.path.append` to old monorepo paths                | P2       |
| HSK-05 | cascor-client  | AGENTS.md header version 0.3.0, package is 0.4.0                                    | P3       |
| HSK-06 | juniper-data   | AGENTS.md header version 0.5.0, package is 0.6.0                                    | P3       |
| HSK-07 | cascor-client  | File headers (constants.py, testing/*) show versions 0.1.0–0.3.0                    | P3       |
| HSK-08 | data-client    | `tests/conftest.py` version header says 0.3.1, project is 0.4.0                     | P3       |
| HSK-09 | cascor-client  | Dead code: `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes never referenced  | P3       |

---

## 13. juniper-deploy Outstanding Items

### 13.1 Infrastructure Bugs (Confirmed Still Present)

| ID        | Severity   | Description                                                                                                                      | Evidence                                                    |
|-----------|------------|----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:499-500` vs service env var             |
| DEPLOY-02 | **HIGH**   | AlertManager service missing from docker-compose.yml — `prometheus.yml:34` references `alertmanager:9093` but no service defined | `alertmanager/alertmanager.yml` exists but is never used    |
| DEPLOY-03 | **HIGH**   | Prometheus alert/recording rules not mounted — only `prometheus.yml` is volume-mapped, rules files unreachable inside container  | `docker-compose.yml` volume mount vs `prometheus.yml:37-38` |
| DEPLOY-04 | **MEDIUM** | K8s canopy deployment missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars                 | Helm templates                                              |
| DEPLOY-05 | **MEDIUM** | K8s Redis `auth.enabled: false` — no authentication                                                                              | `values.yaml:306`                                           |
| DEPLOY-06 | **MEDIUM** | K8s Grafana admin password is empty string default                                                                               | `values.yaml:334`                                           |
| DEPLOY-07 | **MEDIUM** | No resource limits on any Docker Compose service                                                                                 | Planned for v0.3.0, not implemented                         |
| DEPLOY-08 | **MEDIUM** | Cascor and canopy ports bound to `0.0.0.0` (externally accessible)                                                               | `docker-compose.yml:128-129,297-298`                        |

### 13.2 Unimplemented Roadmap Items

| ID           | Planned Version | Description                                              | Status                                                             |
|--------------|-----------------|----------------------------------------------------------|--------------------------------------------------------------------|
| DEPLOY-RD-01 | 0.3.0           | Production compose profile with resource limits          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-02 | 0.3.0           | TLS termination via reverse proxy                        | 🔴 NOT DONE                                                        |
| DEPLOY-RD-03 | 0.5.0           | Scheduled weekly integration tests                       | 🔴 NOT DONE                                                        |
| DEPLOY-RD-04 | 0.5.0           | Container image security scanning (Trivy/Grype)          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-05 | —               | Phase 2 systemd service units                            | 🔴 ENTIRELY UNSTARTED — no `systemd/` directory                    |
| DEPLOY-RD-06 | —               | Docker integration CI job (build + start + health check) | 🔴 Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from CI |
| DEPLOY-RD-07 | —               | SOPS multi-key per environment (SOPS-002)                | 🔴 Deferred to Phase 5                                             |
| DEPLOY-RD-08 | —               | Docker secrets + SOPS integration (SOPS-014)             | 🔴 Deferred to Phase 5                                             |

---

## 14. juniper-data Outstanding Items

### 14.1 Security Issues (Confirmed Still Present)

| ID        | Severity   | File                        | Description                                                                                                                                                         |
|-----------|------------|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can escape storage directory. |
| JD-SEC-02 | **MEDIUM** | `api/security.py:59`        | API key comparison not constant-time — timing side-channel (SEC-01 from prior audit, still present)                                                                 |
| JD-SEC-03 | **MEDIUM** | `api/security.py:116`       | Rate limiter memory unbounded — no eviction/TTL (SEC-02 from prior audit, still present)                                                                            |

### 14.2 Performance Issues

| ID         | Severity   | File                                | Description                                                                                    |
|------------|------------|-------------------------------------|------------------------------------------------------------------------------------------------|
| JD-PERF-01 | **HIGH**   | `api/routes/datasets.py:107`        | Sync `generator.generate()` blocks async event loop. Needs `asyncio.to_thread()`.              |
| JD-PERF-02 | **MEDIUM** | `storage/base.py:261,317`           | `filter_datasets`/`get_stats` load ALL metadata on every call — O(n) disk reads.               |
| JD-PERF-03 | **MEDIUM** | `storage/base.py:169`               | `list_versions` loads all metadata then filters in Python. No DB-level filtering for Postgres. |
| JD-PERF-04 | **MEDIUM** | `storage/postgres_store.py:125-127` | No connection pooling — `psycopg2.connect()` called per operation.                             |

### 14.3 Deferred Roadmap Items

| ID     | Description                             | Status      |
|--------|-----------------------------------------|-------------|
| RD-008 | Fix SIM117 test code violations         | 🔵 DEFERRED |
| RD-015 | IPC Architecture (ZeroMQ/shared-memory) | 🔵 DEFERRED |
| RD-016 | GPU Acceleration for large datasets     | 🔵 DEFERRED |
| RD-017 | Continuous Profiling infrastructure     | 🔵 DEFERRED |

---

## 15. Client Library Outstanding Items

### 15.1 juniper-cascor-client

| ID    | Severity   | Description                                                                                   | Status             |
|-------|------------|-----------------------------------------------------------------------------------------------|--------------------|
| CC-01 | **MEDIUM** | `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out | 🔴 Open            |
| CC-02 | **MEDIUM** | 503 not in `RETRYABLE_STATUS_CODES`                                                           | 🔴 Open (XREPO-02) |
| CC-03 | **MEDIUM** | No `FakeCascorControlStream`                                                                  | 🔴 Open (XREPO-03) |
| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |
| CC-05 | **LOW**    | CI doesn't test Python 3.14 (classified in pyproject.toml)                                    | 🔴 Open            |

### 15.2 juniper-data-client

| ID    | Severity     | Description                                                        | Status              |
|-------|--------------|--------------------------------------------------------------------|---------------------|
| DC-01 | **CRITICAL** | `GENERATOR_CIRCLE = "circle"` — server has `"circles"` (plural)    | 🔴 Open (XREPO-01)  |
| DC-02 | **CRITICAL** | `GENERATOR_MOON = "moon"` — server has no moon generator           | 🔴 Open (XREPO-01b) |
| DC-03 | **MEDIUM**   | Missing constants for 5 server generators                          | 🔴 Open (XREPO-01c) |
| DC-04 | **MEDIUM**   | `FakeDataClient` masks generator name bugs — accepts invalid names | 🔴 Open             |

### 15.3 juniper-cascor-worker

| ID    | Severity   | Description                                                                                     | Status  |
|-------|------------|-------------------------------------------------------------------------------------------------|---------|
| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker | 🔴 Open |
| CW-02 | **MEDIUM** | `requirements.lock` includes CUDA packages (~2-4GB image bloat)                                 | 🔴 Open |
| CW-03 | **LOW**    | No integration tests (marker defined, zero tests use it)                                        | 🔴 Open |

---

## 16. Source Document Lineage

This document was produced by cross-referencing:

| Document                              | Location                            | Date       | Items                                   |
|---------------------------------------|-------------------------------------|------------|-----------------------------------------|
| `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | `juniper-ml/notes/development/`     | 2026-04-17 | 91+ items from 16 source documents      |
| `CONSOLIDATED_DEVELOPMENT_HISTORY.md` | `juniper-canopy/notes/development/` | 2026-04-17 | 99+ issues from 16 source documents     |
| `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | `juniper-cascor/notes/development/` | 2026-04-17 | ~120 items from 12 source documents     |
| `DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` | `juniper-ml/notes/development/`     | 2026-04-19 | 70+ findings from deep audit of 5 repos |

**Validation agents (v1.0.0)**:

- Cascor validation: 15 items checked → 12 still open, 3 now fixed
- Canopy validation: 16 items checked → 6 now fixed, 4 still open, 3 partially fixed
- Ecosystem validation: 13 items checked → 0 fixed, 8 still open, 3 partially fixed

**Validation agents (v2.0.0 — deep audit)**:

- juniper-cascor-client: 93.52% coverage, 4 medium issues, all notes work complete
- juniper-cascor-worker: 91.47% coverage, 5 medium issues, all notes work complete
- juniper-data: 1 high security (path traversal), 1 high perf (blocking async), 4 deferred roadmap items
- juniper-data-client: 2 critical bugs (generator name mismatch), all notes work complete
- juniper-deploy: 3 high infrastructure bugs (AlertManager missing, rules not mounted, secret mismatch), 8 unimplemented roadmap items

---

*End of outstanding development items document.*
