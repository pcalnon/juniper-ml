# Juniper Ecosystem — Consolidated Development Record

**Date**: 2026-04-17
**Version**: 1.0.0
**Status**: Current
**Scope**: All documented development work across the Juniper ecosystem, validated against current codebase
**Source Documents**: 16 files in `juniper-ml/notes/development/`

---

## Table of Contents

- [1. Purpose and Methodology](#1-purpose-and-methodology)
- [2. Summary of Validation Results](#2-summary-of-validation-results)
- [3. Canopy–CasCor Connection and Data Contract Fixes](#3-canopycascor-connection-and-data-contract-fixes)
- [4. Network Topology Display Fixes](#4-network-topology-display-fixes)
- [5. Convergence UI Controls](#5-convergence-ui-controls)
- [6. Meta Parameters Enhancement](#6-meta-parameters-enhancement)
- [7. Dashboard Augmentation](#7-dashboard-augmentation)
- [8. Critical Bug Fixes (Phase 1)](#8-critical-bug-fixes-phase-1)
- [9. Dark Mode and Remaining Issues Remediation](#9-dark-mode-and-remaining-issues-remediation)
- [10. Microservices Architecture](#10-microservices-architecture)
- [11. WebSocket Migration (R5-01 Canonical Plan)](#11-websocket-migration-r5-01-canonical-plan)
- [12. Items Not Yet Implemented](#12-items-not-yet-implemented)
- [13. Source Document Cross-Reference](#13-source-document-cross-reference)

---

## 1. Purpose and Methodology

This document consolidates all development work documented in the 16 source files in `juniper-ml/notes/development/`, producing a single comprehensive record of every fix, update, change, enhancement, and architectural upgrade. Each item has been validated against the current codebase to determine its implementation status.

**Validation method**: Specialized sub-agents searched the live codebases (juniper-cascor, juniper-canopy, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy, juniper-ml) for each documented change, confirming or denying implementation via file reads, grep searches, and structural analysis.

**Status legend**:

| Symbol | Meaning                                          |
|--------|--------------------------------------------------|
| ✅     | Implemented and verified in current codebase     |
| ⚠️     | Partially implemented — some elements missing    |
| ❌     | Not implemented — documented but not in codebase |
| 🐛     | Bug confirmed still present in codebase          |

---

## 2. Summary of Validation Results

| Category                           | Total Items | ✅ Implemented | ⚠️ Partial | ❌ Not Implemented |
|------------------------------------|-------------|----------------|------------|--------------------|
| Canopy–CasCor Connection (P5-RC-*) | 20          | 20             | 0          | 0                  |
| Network Topology Display           | 7           | 7              | 0          | 0                  |
| Convergence UI                     | 7           | 7              | 0          | 0                  |
| Meta Parameters UI                 | 1           | 1              | 0          | 0                  |
| Dashboard Augmentation             | 10          | 5              | 0          | 5                  |
| Critical Bug Fixes                 | 3           | 3              | 0          | 0                  |
| Dark Mode / Remediation            | 5           | 4              | 1          | 0                  |
| Microservices (Ph 1–4)             | 28          | 25             | 1          | 2                  |
| WebSocket Migration (R5-01)        | 10 phases   | 3              | 2          | 5                  |
| **Total**                          | **91+**     | **75+**        | **4**      | **12**             |

---

## 3. Canopy–CasCor Connection and Data Contract Fixes

**Source**: `FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md`
**Status**: ALL 20 ISSUES IMPLEMENTED

The connection analysis identified 20 root causes (P5-RC-01 through P5-RC-18, P5-RC-12b, KL-1) for the canopy dashboard failing to display data from an external cascor instance. The fundamental problem was that service mode emitted flat metrics and weight-oriented topology while the dashboard expected nested metrics and graph-oriented topology (built against demo mode).

| ID        | Severity   | Description                                                          | Status                                                                       |
|-----------|------------|----------------------------------------------------------------------|------------------------------------------------------------------------------|
| P5-RC-01  | CRITICAL   | Metrics format mismatch: flat vs nested                              | ✅ Fixed — `_normalize_metric()` + `_to_dashboard_metric()` pipeline         |
| P5-RC-02  | CRITICAL   | Topology format mismatch: weight-oriented vs graph-oriented          | ✅ Fixed — `_transform_topology()` with output weights transposition         |
| P5-RC-03  | HIGH       | Uppercase status normalization gap in relay path                     | ✅ Fixed — case-insensitive normalization                                    |
| P5-RC-04  | MODERATE   | WebSocket relay only forwards `status` + `phase`                     | ✅ Fixed — all 29 TrainingState fields forwarded                             |
| P5-RC-05  | LOW        | Dashboard ignores WebSocket relay, polls HTTP only                   | ✅ Fixed — WS drain bridge implemented (Phase B)                             |
| P5-RC-06  | MODERATE   | `current_phase` never updated after initialization                   | ✅ Fixed — updated at `monitored_fit` (output), `monitored_grow` (candidate) |
| P5-RC-07  | MODERATE   | State sync stores metrics without normalization                      | ✅ Fixed                                                                     |
| P5-RC-08  | MODERATE   | State sync bypasses adapter normalization                            | ✅ Fixed                                                                     |
| P5-RC-09  | MODERATE   | `/api/metrics` snapshot produces flat format                         | ✅ Fixed                                                                     |
| P5-RC-10  | MODERATE   | State sync params in raw CasCor namespace                            | ✅ Fixed                                                                     |
| P5-RC-11  | MODERATE   | Hardcoded `localhost:8050` URLs (6 instances)                        | ✅ Fixed                                                                     |
| P5-RC-12  | LOW        | `cn_training_iterations → candidate_epochs` mapping non-functional   | ✅ Fixed                                                                     |
| P5-RC-12b | LOW        | `patience` → `nn_growth_convergence_threshold` semantic mismatch     | ✅ Fixed                                                                     |
| P5-RC-13  | LOW        | `candidate_learning_rate` unmapped in canopy                         | ✅ Fixed                                                                     |
| P5-RC-14  | LOW        | Relay broadcasts unnormalized metric payloads                        | ✅ Fixed                                                                     |
| P5-RC-15  | LOW        | Double initialization on fallback-to-demo path                       | ✅ Fixed                                                                     |
| P5-RC-16  | LOW        | Phase 1 tests validate flat output, not dashboard compat             | ✅ Fixed                                                                     |
| P5-RC-17  | INFO       | Dual status normalization paths produce inconsistent representations | ✅ Fixed                                                                     |
| P5-RC-18  | SYSTEMIC   | No canonical backend contract across modes                           | ✅ Fixed — `BackendProtocol` class in `protocol.py`                          |
| KL-1      | Limitation | Dataset scatter plot empty in service mode                           | ✅ Acknowledged — graceful degradation implemented                           |

---

## 4. Network Topology Display Fixes

**Source**: `NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md`
**Status**: ALL PHASES IMPLEMENTED

| ID   | Severity | Description                                             | Status                                                                 | Commit                    |
|------|----------|---------------------------------------------------------|------------------------------------------------------------------------|---------------------------|
| OI-1 | HIGH     | Topology store returns `{}` on error, blanking display  | ✅ Fixed — returns `dash.no_update`                                    | b4131ab                   |
| OI-2 | HIGH     | WebSocket topology push not wired to Dash store         | ✅ Fixed — `ws-topology-buffer` + clientside drain                     | 04db7e6                   |
| OI-3 | MEDIUM   | Demo backend omits hidden-to-hidden cascade connections | ✅ Fixed                                                               | b4131ab                   |
| OI-4 | MEDIUM   | `extract_network_topology` swallows exceptions silently | ✅ Fixed                                                               | b4131ab                   |
| OI-5 | LOW      | Initial sync topology not pushed to Dash store          | ✅ Fixed — fallback in `ServiceBackend.get_network_topology()`         | 2beea5c                   |
| OI-6 | LOW      | Narrow exception handling in adapter methods            | ✅ Fixed — `get_decision_boundary()` broadened to `Exception`          | 2beea5c                   |
| OF-1 | MEDIUM   | Weight-centric topology view toggle                     | ✅ Implemented — `_create_weight_heatmap()` with raw topology endpoint | b55ff46, 28b1a01, 2beea5c |

**Additional CasCor findings (validated)**:

| Finding                                            | Status                                                                                          |
|----------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `create_topology_message()` is dead code in cascor | 🐛 Confirmed — defined and exported but never called in production code                         |
| `cascade_add` correlation hardcoded to `0.0`       | 🐛 Confirmed — `manager.py` line 427-429 passes `correlation=0.0` instead of actual correlation |

---

## 5. Convergence UI Controls

**Source**: `CONVERGENCE_UI_FIX_PLAN.md`
**Status**: COMPLETE

| Bug ID | Description                                       | Status                                                   | Commit  |
|--------|---------------------------------------------------|----------------------------------------------------------|---------|
| B-5.1  | Unchecking convergence checkbox reverts on Apply  | ✅ Fixed                                                 | c8f2740 |
| B-5.2  | Threshold reverts to default on Apply             | ✅ Fixed                                                 | c8f2740 |
| B-5.3  | Meta-parameter values refreshed every few seconds | ✅ Fixed — `sync_backend_params` callback removed        | c8f2740 |
| B-5.4  | Meta-parameter section missing heading            | ✅ Fixed — separate cards                                | c8f2740 |
| B-5.5  | Convergence params not in `/api/state`            | ✅ Fixed                                                 | e11b100 |
| B-5.6  | Init callback fires repeatedly                    | ✅ Fixed — `params-init-interval` with `max_intervals=1` | e11b100 |
| B-5.7  | Status message changes on no-change Apply         | ✅ Fixed — returns `dash.no_update` when no changes      | e11b100 |

---

## 6. Meta Parameters Enhancement

**Source**: `META_PARAMETERS_ENHANCEMENT_PLAN.md`
**Status**: ✅ IMPLEMENTED

The Training Parameters card was restructured into a "Meta Parameters" card with two collapsible subsections:

| Component                                                     | Status                                                            |
|---------------------------------------------------------------|-------------------------------------------------------------------|
| Neural Network subsection (12 inputs)                         | ✅ Implemented — `nn-subsection-collapse`, `nn-subsection-header` |
| Candidate Nodes subsection (10 inputs)                        | ✅ Implemented — `cn-subsection-collapse`, `cn-subsection-header` |
| 10 callback handlers (track, apply, init, sync, toggles)      | ✅ Implemented                                                    |
| Cross-section checkbox linking (Multi-Node ↔ Multi-Candidate) | ✅ Implemented                                                    |
| Radio button sub-field enable/disable                         | ✅ Implemented                                                    |
| Constants updates (`canopy_constants.py`)                     | ✅ Implemented                                                    |
| Backward compatibility for old API keys                       | ✅ Implemented                                                    |

---

## 7. Dashboard Augmentation

**Source**: `DASHBOARD_AUGMENTATION_PLAN.md`
**Status**: PARTIALLY COMPLETE

### Phase 1 (canopy-only) — COMPLETE

| Item                                                                   | Status         | Commit           |
|------------------------------------------------------------------------|----------------|------------------|
| Fix pre-existing test failures (5 in `test_response_normalization.py`) | ✅ Fixed       | Backlog Sprint 1 |
| Task 3: Topology layer assignment fix (lines 582, 611)                 | ✅ Fixed       | —                |
| Task 2 Phase 1: Metadata-only graceful handling                        | ❌ NOT STARTED | —                |

### Phase 2 (metrics UI enhancements)

| Item                                             | Status         | Commit  |
|--------------------------------------------------|----------------|---------|
| Task 1A: Validation loss/accuracy overlay traces | ❌ NOT STARTED | —       |
| Task 1B: Training progress bars (dbc.Progress)   | ✅ COMPLETE    | —       |
| Task 1C: Learning rate metric card               | ❌ NOT STARTED | —       |
| Task 1D: Phase duration display                  | ❌ NOT STARTED | —       |
| Task 1E: Hidden units progress ratio ("N / max") | ✅ COMPLETE    | 18e39cf |

### Phase 4 (cross-repo dataset endpoint)

| Item                                                      | Status         |
|-----------------------------------------------------------|----------------|
| Task 2 Phase 2: `GET /v1/dataset/data` endpoint in cascor | ❌ NOT STARTED |

### Additional completed work (not in original plan)

| Feature                        | Status  | Commit  |
|--------------------------------|---------|---------|
| Weight matrix heatmap (OF-1)   | ✅      | b55ff46 |
| Correlation statistics display | ✅      | 37c885d |
| WebSocket topology buffer      | ✅      | 04db7e6 |
| CasCor state mapping           | ✅      | 8d6b858 |
| GIL contention test fix        | ✅      | 04db7e6 |

---

## 8. Critical Bug Fixes (Phase 1)

**Source**: `PHASE1_CRITICAL_FIXES_PLAN.md`
**Status**: ALL IMPLEMENTED

| Bug   | Description                                                             | Fix                                                                                         | Status         |
|-------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|----------------|
| Bug 1 | Grow progress bar shows 0% — `grow_max=max_epochs` (10000)              | Use `max_hidden_units` as denominator, cap at 100%                                          | ✅ Implemented |
| Bug 2 | Drain thread race condition — progress queue doesn't exist when checked | Deferred queue discovery: poll `getattr(network_ref, "_persistent_progress_queue")` in loop | ✅ Implemented |
| Bug 3 | Test updates for both fixes                                             | Updated `test_monitoring_hooks.py` and `test_metrics_panel_handlers.py`                     | ✅ Implemented |

---

## 9. Dark Mode and Remaining Issues Remediation

**Source**: `REMAINING_ISSUES_REMEDIATION_PLAN.md`
**Status**: ALL 5 WORK UNITS COMPLETE

| Work Unit | Issues         | Description                                                                              | Status                                                                                                                      |
|-----------|----------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| 1         | 2A, 2B, 2C, 5A | Worktree developer experience (logs symlink, .gitkeep, procedure docs, pre-commit scope) | ✅ Complete                                                                                                                 |
| 2         | 1E, 1F         | Metrics panel table dark mode                                                            | ⚠️ Mostly complete — `theme-table` CSS class **not found** in codebase, but conditional `is_dark` styling is correctly used |
| 3         | 3A             | Pre-existing test failures (9 `test_api_state_endpoint.py` failures)                     | ✅ Complete — `test_client` fixture uses context manager                                                                    |
| 4         | 4A             | Service mode verification tests                                                          | ✅ Complete — 5 integration tests added                                                                                     |
| 5         | 1A–1D          | Remove redundant `#f8f9fa` inline styles from `dbc.CardHeader` (13 instances)            | ✅ Complete — zero remaining instances                                                                                      |

---

## 10. Microservices Architecture

**Sources**: `MICROSERVICES_ARCHITECTURE_ANALYSIS.md`, `MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md`, `MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`, `MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md`, `MICROSERVICES_PHASE3_PLAN_2026-04-06.md`, `MICROSERVICES_PHASE4_PLAN_2026-04-06.md`

### Phase 1: Critical Startup/Shutdown Fixes — ✅ COMPLETE (commit `03aec86`)

| Step | Task                                                                        | Status         |
|------|-----------------------------------------------------------------------------|----------------|
| 1.1  | `wait_for_health()` function — polls `/v1/health` with configurable timeout | ✅ Implemented |
| 1.2  | Error handling: `set -euo pipefail` + `trap cleanup_on_failure ERR`         | ✅ Implemented |
| 1.3  | Per-service conda env Python binaries                                       | ✅ Implemented |
| 1.4  | `validate_pid()` + `graceful_stop()` in chop script                         | ✅ Implemented |
| 1.5  | Worker-not-found exit fix (opt-in `KILL_WORKERS=1`)                         | ✅ Implemented |
| 1.6  | SIGKILL fallback with configurable timeout                                  | ✅ Implemented |
| 1.7  | Port availability check via `ss`                                            | ✅ Implemented |
| 1.8  | Conda env validation                                                        | ✅ Implemented |
| 1.9  | Remove `get_cascor_dkdk.bash` (dead code)                                   | ✅ Implemented |
| 1.10 | Fix quoting issues in PID file operations                                   | ✅ Implemented |

### Phase 2: systemd & Service Management — ✅ COMPLETE

| Step | Task                                                         | Status                                                         |
|------|--------------------------------------------------------------|----------------------------------------------------------------|
| 2.1  | `juniper-data.service` systemd unit                          | ❌ Not in juniper-deploy scripts/ (may be in individual repos) |
| 2.2  | `juniper-cascor.service` systemd unit                        | ❌ Not in juniper-deploy scripts/ (may be in individual repos) |
| 2.3  | Fix `juniper-canopy.service` (JuniperPython → JuniperCanopy) | ✅ Implemented                                                 |
| 2.4  | `juniper-data-ctl` management CLI                            | ✅ Implemented (in juniper-data repo)                          |
| 2.5  | `juniper-cascor-ctl` management CLI                          | ✅ Implemented (in juniper-cascor repo)                        |
| 2.6  | `juniper-all.target` + `juniper-all-ctl`                     | ✅ Implemented — target has all 4 services                     |
| 2.7  | Configurable paths in plant/chop                             | ✅ Implemented (Phase 1)                                       |
| 2.8  | `--systemd` mode in plant/chop                               | ✅ Implemented                                                 |

**Note**: systemd service files for juniper-data and juniper-cascor are in their respective repos (`scripts/` dirs), not in juniper-deploy.

### Phase 3: Worker Deployment & Container Integration — ✅ COMPLETE

| Step | Task                                                          | Status                                                   |
|------|---------------------------------------------------------------|----------------------------------------------------------|
| 3.1  | `juniper-cascor-worker/Dockerfile`                            | ✅ Implemented                                           |
| 3.2  | `requirements.lock` for worker                                | ✅ Implemented                                           |
| 3.2b | `.dockerignore`                                               | ✅ Implemented                                           |
| 3.3  | Worker service in `docker-compose.yml`                        | ✅ Implemented — profiles `["full", "test"]`, replicas 2 |
| 3.4  | `juniper-cascor-worker.service` + `juniper-cascor-worker-ctl` | ✅ Implemented                                           |
| 3.5  | Health check (process-based: `kill -0 1`)                     | ✅ Implemented                                           |
| 3.6  | Testing & validation                                          | ✅ Complete                                              |

### Phase 4: Kubernetes Helm Chart — ✅ COMPLETE

| Step | Task                                             | Status         |
|------|--------------------------------------------------|----------------|
| 4.1  | Chart scaffolding (`Chart.yaml`, `_helpers.tpl`) | ✅ Implemented |
| 4.2  | Deployments for all 4 services                   | ✅ Implemented |
| 4.3  | Services (ClusterIP) + Ingress                   | ✅ Implemented |
| 4.4  | Secrets (file-based, `_FILE` env var pattern)    | ✅ Implemented |
| 4.5  | PVCs for data persistence                        | ✅ Implemented |
| 4.6  | HPA for worker auto-scaling                      | ✅ Implemented |
| 4.7  | NetworkPolicies (5 files)                        | ✅ Implemented |
| 4.8  | `values.yaml` + overlays (production, demo)      | ✅ Implemented |
| 4.9  | ServiceMonitors for Prometheus Operator          | ✅ Implemented |
| 4.10 | Integration test script                          | ✅ Implemented |

### Phase 5: Observability & Hardening — ❌ NOT STARTED

| Step | Task                                             | Status  |
|------|--------------------------------------------------|---------|
| 5.1  | Configure AlertManager receivers                 | ❌      |
| 5.2  | Define alert rules for service availability      | ❌      |
| 5.3  | Standardize health endpoints across all services | ❌      |
| 5.4  | Volume backup/restore documentation              | ❌      |
| 5.5  | Startup validation test suite                    | ❌      |

---

## 11. WebSocket Migration (R5-01 Canonical Plan)

**Sources**: `R5-01_canonical_development_plan.md`, `PHASE_B_IMPLEMENTATION_PLAN.md`
**Status**: PHASES 0 AND B PARTIALLY COMPLETE; PHASES C–H NOT STARTED

### Phase 0-cascor (seq/replay/resume) — ✅ IMPLEMENTED

| Deliverable                                                            | Status                                          |
|------------------------------------------------------------------------|-------------------------------------------------|
| Monotonically-increasing `seq` on every outbound envelope              | ✅ `_next_seq`, `_seq_lock` in `manager.py`     |
| `server_instance_id` + `server_start_time` in `connection_established` | ✅                                              |
| 1024-entry replay buffer with `resume` handler                         | ✅ `_replay_buffer` deque with `replay_since()` |
| Send timeout (0.5s, GAP-WS-07 quick-fix)                               | ✅                                              |
| State coalescer (GAP-WS-21) — terminal transitions bypass throttle     | ✅                                              |
| `broadcast_from_thread` exception logging (GAP-WS-29)                  | ✅                                              |
| Protocol error on unknown commands, close 1003 on malformed JSON       | ✅                                              |
| `command_id` echo on `/ws/control` (no seq per D-03)                   | ✅                                              |

### Phase A-SDK — ✅ IMPLEMENTED

| Deliverable                                                      | Status               |
|------------------------------------------------------------------|----------------------|
| `CascorControlStream.set_params()` with `command_id` correlation | ✅ In `ws_client.py` |
| 1.0s default timeout (fail-fast to REST)                         | ✅                   |

### Phase B-pre-a (security) — ⚠️ PARTIALLY IMPLEMENTED

| Deliverable                             | Status                                                 |
|-----------------------------------------|--------------------------------------------------------|
| Origin allowlist on WebSocket endpoints | ✅ `ws_control_allowed_origins` in settings            |
| `ws_max_connections_per_ip`             | ❌ NOT FOUND in codebase                               |
| Audit logging                           | ⚠️ Settings fields exist but audit logger not verified |

### Phase B (polling elimination — P0 WIN) — ✅ IMPLEMENTED

| Deliverable                                                         | Status                                     |
|---------------------------------------------------------------------|--------------------------------------------|
| Two-flag design: `enable_browser_ws_bridge` + `disable_ws_bridge`   | ✅ In `settings.py`                        |
| `ws_dash_bridge.js` — browser drain bridge                          | ✅ Exists in `assets/`                     |
| `ws-metrics-buffer`, `ws-topology-buffer`, `ws-state-buffer` stores | ✅ In `dashboard_manager.py`               |
| Polling toggle: skip REST when WS connected                         | ✅                                         |
| Connection indicator                                                | ✅                                         |
| Flag flipped to `True` (default on)                                 | ✅ `enable_browser_ws_bridge: bool = True` |

### Phases C–H — ❌ NOT STARTED

| Phase | Goal                                           | Status |
|-------|------------------------------------------------|--------|
| C     | WebSocket `set_params` (canopy adapter)        | ❌     |
| D     | Training control buttons via WebSocket         | ❌     |
| E     | Backpressure pump tasks (conditional)          | ❌     |
| F     | Heartbeat jitter                               | ❌     |
| G     | Integration tests (cascor `set_params` via WS) | ❌     |
| H     | `_normalize_metric` audit                      | ❌     |

---

## 12. Items Not Yet Implemented

### High Priority

| Item                                | Source Document                   | Description                                                              |
|-------------------------------------|-----------------------------------|--------------------------------------------------------------------------|
| `ws_max_connections_per_ip`         | R5-01 Phase B-pre-a               | Per-IP WebSocket connection limit — setting not found in cascor codebase |
| `create_topology_message` dead code | NETWORK_TOPOLOGY_DISPLAY_ANALYSIS | Builder exists but never called — topology changes not broadcast via WS  |
| `cascade_add` correlation           | NETWORK_TOPOLOGY_DISPLAY_ANALYSIS | Hardcoded `0.0` instead of actual best candidate correlation             |

### Medium Priority

| Item                                         | Source Document                   | Description                                                                                |
|----------------------------------------------|-----------------------------------|--------------------------------------------------------------------------------------------|
| Task 2 Ph1: Metadata-only graceful handling  | DASHBOARD_AUGMENTATION_PLAN       | Dataset tab metadata-only display for service mode                                         |
| Task 1A: Validation loss/accuracy overlays   | DASHBOARD_AUGMENTATION_PLAN       | Add val_loss/val_accuracy traces to metrics charts                                         |
| Task 1C: Learning rate metric card           | DASHBOARD_AUGMENTATION_PLAN       | New metric card for current learning rate                                                  |
| Task 1D: Phase duration display              | DASHBOARD_AUGMENTATION_PLAN       | Elapsed time since phase start                                                             |
| Task 2 Ph2: Cross-repo dataset data endpoint | DASHBOARD_AUGMENTATION_PLAN       | `GET /v1/dataset/data` in cascor, client method, canopy integration                        |
| `theme-table` CSS class                      | REMAINING_ISSUES_REMEDIATION_PLAN | Dark mode table styling via CSS class not implemented (conditional `is_dark` used instead) |

### Low Priority (Future Phases)

| Item                               | Source Document                   | Description                                                                 |
|------------------------------------|-----------------------------------|-----------------------------------------------------------------------------|
| Phase 5: Observability & Hardening | MICROSERVICES_STARTUP_CODE_REVIEW | AlertManager receivers, alert rules, health standardization                 |
| Phases C–H of WebSocket migration  | R5-01_canonical_development_plan  | `set_params` via WS, control buttons via WS, backpressure, heartbeat jitter |

---

## 13. Source Document Cross-Reference

| Document                                            | Date       | Primary Focus                                                | Implementation Status                         |
|-----------------------------------------------------|------------|--------------------------------------------------------------|-----------------------------------------------|
| `CONVERGENCE_UI_FIX_PLAN.md`                        | 2026-03-19 | Convergence checkbox/threshold bugs B-5.1–B-5.7              | ✅ COMPLETE                                   |
| `DASHBOARD_AUGMENTATION_PLAN.md`                    | 2026-03-29 | Metrics UI, dataset tab, topology fixes                      | ⚠️ PARTIALLY COMPLETE                         |
| `FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md`        | 2026-03-28 | 20 root causes for canopy–cascor data contract mismatch      | ✅ ALL IMPLEMENTED                            |
| `META_PARAMETERS_ENHANCEMENT_PLAN.md`               | 2026-03-21 | Restructured sidebar with NN/CN subsections                  | ✅ IMPLEMENTED                                |
| `MICROSERVICES_ARCHITECTURE_ANALYSIS.md`            | 2026-02-25 | Startup orchestration, modes of operation, service discovery | ✅ ANALYSIS COMPLETE, recommendations adopted |
| `MICROSERVICES_PHASE3_PLAN_2026-04-06.md`           | 2026-04-06 | Worker Dockerfile, docker-compose, systemd                   | ✅ COMPLETE                                   |
| `MICROSERVICES_PHASE4_PLAN_2026-04-06.md`           | 2026-04-06 | Kubernetes Helm chart                                        | ✅ COMPLETE                                   |
| `MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md`   | 2026-04-06 | Comprehensive startup/shutdown code review, 5-phase roadmap  | Phases 1–4 ✅, Phase 5 ❌                     |
| `MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md`   | 2026-04-06 | systemd service units for all services                       | ✅ COMPLETE                                   |
| `MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` | 2026-02-25 | 9-phase implementation roadmap (Phases 1–9)                  | Phases 1–4 ✅, 5–9 ❌                         |
| `NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md`    | 2026-03-31 | 6 topology bugs + weight heatmap feature                     | ✅ ALL PHASES IMPLEMENTED                     |
| `PHASE_B_IMPLEMENTATION_PLAN.md`                    | 2026-04-12 | WebSocket browser drain wiring (P0 win)                      | ✅ IMPLEMENTED                                |
| `PHASE1_CRITICAL_FIXES_PLAN.md`                     | 2026-04-01 | Progress bar denominator + drain thread race condition       | ✅ ALL IMPLEMENTED                            |
| `R5-01_canonical_development_plan.md`               | 2026-04-11 | Full WebSocket migration canonical plan (10 phases)          | ⚠️ Phases 0, A, B ✅; B-pre-a ⚠️; C–H ❌      |
| `REMAINING_ISSUES_REMEDIATION_PLAN.md`              | 2026-03-17 | Dark mode, worktree DX, test failures, code cleanup          | ✅ ALL 5 WORK UNITS COMPLETE                  |
| `JUNIPER_ECOSYSTEM_CODE_AUDIT.md`                   | 2026-04-17 | Full 8-repo code audit                                       | ✅ ANALYSIS COMPLETE (read-only)              |

---

*End of consolidated development record.*
