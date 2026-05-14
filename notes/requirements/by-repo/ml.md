# Requirements — juniper-ml (ml)

**Total entries**: 1353

**By status**: proposed=1122 | designed=109 | in-progress=9 | shipped=37 | deferred=31 | rejected=17 | superseded=28

**By priority**: P0=114 | P1=535 | P2=665 | P3=39

**By category**: ARCH=318 | SEC=220 | WS=176 | OBS=142 | TRAIN=99 | API=96 | UI=75 | TOOL=48 | DEP=46 | TEST=42 | DATA=41 | PERF=25 | DOC=13 | OPS=11 | LOCK=1

---

### JR-ML-OBS-001 — 15.2 4 stale dashboard panels post audit-PR closes.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 826-876)

**Detail**:

**Finding.** Four dashboard text / inference panels are stale relative

### JR-ML-SEC-001 — 3.3 OBS-ROUTE-CRED — Alertmanager `tickets` receiver real-credentials rotation.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 124-156)

**Detail**:

**Severity:** P1 (soft-blocker) · **Owner repo:** juniper-deploy · **Status:** open

### JR-ML-DEP-001 — 3.4 LIFT-01 — R5.4 alert log-only-severity gate lift.

**Status**: shipped  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 156-182)

**Detail**:

**Severity:** P1 · **Owner repo:** juniper-deploy · **Status:** blocked (gated on CALIB-01 + OBS-ROUTE-CRED)

### JR-ML-SEC-002 — 3.5 Phase 1 Deferred Items — STATUS UPDATE (2026-04-10, REVISED).

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 216-266)

**Detail**:

> - 2026-04-10 second revision: NEW-01 and canopy-set_params markings reverted as

### JR-ML-TRAIN-001 — Fix activation function mismatch: use tanh instead of sigmoid in demo mode.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 87-103)

**Detail**:

Tanh critical for CasCor algorithm: outputs ∈ {-1,+1} create binary partitions; sigmoid ∈ {0,1} can produce constant features with zero gradient. Sigmoid mean-shift also biases output layer.

**Notes**:

Root cause RC-1; doc status indicates implementation complete

### JR-ML-TRAIN-002 — Fix drain thread race condition in cascor lifecycle manager for candidate progress monitoring.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 121-142)

**Detail**:

Progress queue drain thread checks for queue before it exists in grow_network(). Fix: deferred queue discovery in drain thread or pre-create queue before original_grow().

**Notes**:

Status marked COMPLETE (Section 1, line 7-8); Phase 1 critical fix

### JR-ML-TRAIN-003 — Fix grow progress bar denominator to use max_hidden_units instead of max_epochs.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 104-118)

**Detail**:

Demo mode passes max_epochs (10000) as progress denominator instead of max_hidden_units (10), causing 0.12% → 0% display. Fix: use max_hidden_units in Canopy progress handler, cap at 100%.

**Notes**:

Phase 1 critical fix; doc status COMPLETE

### JR-ML-TRAIN-004 — Fix loss function: use MSE on raw output instead of BCE with sigmoid.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 104-117)

**Detail**:

BCE residuals bounded [-1,1]; MSE residuals unbounded. MSE gradient stronger; residual magnitude larger. CasCor candidate training mathematically designed around MSE residuals.

**Notes**:

Root cause RC-2; doc status indicates implementation complete

### JR-ML-TRAIN-005 — Increase output retraining from 50 mini-batch steps to full-batch training after hidden unit installation.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 118-131)

**Detail**:

Demo: ~1,600 sample evaluations; CasCor: ~2,000,000 (1,250× difference). New hidden unit weight initialized ~0.1; needs ample optimization time. Current 50 steps insufficient (~0.125 total change).

**Notes**:

Root cause RC-3; doc status indicates implementation complete

### JR-ML-TRAIN-006 — Use Adam optimizer instead of vanilla SGD for output training.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 225-242)

**Detail**:

Adam adapts per-parameter effective learning rates using first/second moment estimates. Vanilla SGD shares same lr across all params; new hidden unit columns converge poorly.

**Notes**:

Root cause RC-9; Phase 3 investigation finding; doc status indicates implementation complete

### JR-ML-TRAIN-007 — Use full-batch training between cascade additions instead of mini-batch.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 243-258)

**Detail**:

Mini-batch between cascades (960 evals) undoes full-batch retrain (40,000 evals). High gradient variance causes random walk of carefully retrained weights. Fix: full-batch for 30 epochs instead of mini-batch.

**Notes**:

Root cause RC-10; Phase 3 finding; ~40× weaker training; doc status indicates implementation complete

### JR-ML-OBS-002 — Fix 7 stale Grafana dashboard panels in juniper-cascor.json and juniper-overview.json - 3 inference panels and 4 placeholder texts.

**Status**: in-progress  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 125-135)

**Detail**:

G1 - Stale panels:
- 3 cascor inference panels query removed juniper_cascor_inference_* metrics
- 4 worker-bridge placeholder text panels never replaced with real PromQL
In-flight branch audit-fixup/stale-dashboard-panels exists as of 2026-05-06.

**Notes**:

Operational blocker. Recommend Option A - land in-flight PR + add dashboard-lint CI guardrail.

### JR-ML-OBS-003 — 5.6 Phase 3 Success Criteria.

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 556-574)

**Detail**:

- [x] Dashboard shows per-epoch loss during output training phases — `train_output_layer` callback wired in cascor `manager.py:237-248`; demo mode emits via `_emit_training_metrics()` (verified 2026-04-09)

### JR-ML-OBS-004 — 6.0 Phase 4 Execution Results (2026-04-10, REVISED).

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 574-619)

**Detail**:

> - 2026-04-10 first pass: typed contract landed (PR #140); P5-RC-05 marked DEFERRED

### JR-ML-SEC-003 — Issue Remediations, Section 4.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_a_security_concurrency_error.md` (lines 9-59)

**Detail**:

#### SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel

### JR-ML-SEC-004 — Issue Remediations, Section 7.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 9-59)

**Detail**:

#### CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode

### JR-ML-SEC-005 — Issue Remediations, Section 8.

**Status**: designed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 127-177)

**Detail**:

#### Phase E: Backpressure Pump Tasks

### JR-ML-SEC-006 — 15.3 juniper-cascor-worker.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 396-434)

**Detail**:

| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker | 🔴 Open |

### JR-ML-OBS-005 — 7.0 Critical and High-Priority Enhancements (v3.0.0).

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 193-203)

### JR-ML-SEC-007 — 9.4 Validation status.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 574-624)

**Detail**:

arbitrary file paths). Tracked as **AMTOOL-CI** (P3) on the

### JR-ML-OBS-006 — Additional completed work (not in original plan).

**Status**: deferred  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 184-228)

**Detail**:

## 8. Critical Bug Fixes (Phase 1)

### JR-ML-SEC-008 — Closing PRs.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 648-676)

**Detail**:

| **A.1 / A.2a–e (cascor training metrics dead-defined)** | juniper-cascor#204 (OBS-WIRE-01) — wired 5 emission sites |

### JR-ML-SEC-009 — Issue Remediations, Section 13.

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 428-478)

**Detail**:

#### DEPLOY-01: Docker Secret Name/Path Mismatch

### JR-ML-API-001 — Storage & Infrastructure.

**Status**: deferred  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 348-398)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 273-317)

**Detail**:

## 11. Cross-Repository Alignment Issues

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-010 — v3.0.0 Cross-Referenced Source Documents (34 total).

**Status**: deferred  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 513-563)

**Detail**:

| 1  | `notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md`                              | juniper-ml     |

### JR-ML-SEC-011 — 3.3 Operating Mode Options for Microservices.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 388-438)

**Detail**:

#### Option 1: Runtime Feature Flag (Current Approach, Enhanced)

### JR-ML-SEC-012 — By Category.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 421-436)

### JR-ML-SEC-013 — `_create_optimizer` references undefined `OptimizerConfig` attributes — crashes on non-default optimizer types.

**Status**: rejected  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 648-680)

### JR-ML-OBS-007 — 1.1 WebSocket Topology Broadcast Gap.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 57-93)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

### JR-ML-OBS-008 — 15.1 `juniper_data_datasets_cached` is defined-and-emitted in tests but has no production caller.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 787-826)

**Detail**:

**Finding.** The metric `juniper_data_datasets_cached` (Gauge, no labels)

### JR-ML-DATA-001 — 15.2 juniper-data-client.

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 479-488)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 387-396)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-014 — 2.1 juniper-cascor.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 256-283)

**Detail**:

| CC-01 | **Critical** | `api/websocket/messages.py`       | 72–79   | `create_topology_message()` exists but is never called — topology changes not broadcast via WS                            |

### JR-ML-DEP-002 — 2.2 Per-Client/Worker Inventory.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 127-152)

**Detail**:

- **Type**: Pure HTTP client library

### JR-ML-SEC-015 — 3.1 Current State: `juniper_plant_all.bash`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 152-202)

**Detail**:

**Location**: `juniper-ml/util/juniper_plant_all.bash` (319 lines)

### JR-ML-OBS-009 — 3.1 SLO catalog target calibration against soak-window data.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 70-97)

**Detail**:

- **Status**: open (30-day soak underway)

### JR-ML-DEP-003 — 3.2 Alertmanager `tickets` receiver placeholder.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 97-126)

**Detail**:

- **Status**: open — operational gap

### JR-ML-SEC-016 — 3.2 Current State: `juniper_chop_all.bash`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 208-243)

**Detail**:

**Location**: `juniper-ml/util/juniper_chop_all.bash` (226 lines)

### JR-ML-TEST-001 — 4.1 Bugs.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 220-229)

**Detail**:

| ID        | Severity     | File:Line                       | Description

### JR-ML-OBS-010 — 4.2 Dimension B — PromQL + scrape correctness.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 260-275)

**Detail**:

**Scope**: Verify alert/dashboard/scrape configs are technically correct.

### JR-ML-SEC-017 — 4.3 Issues Identified.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 328-341)

### JR-ML-API-002 — 4.3 Test Coverage Gaps.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 239-246)

**Detail**:

- **Critical**: FakeDataClient accepts `"circle"` and `"moon"` — masks the server mismatch. All unit tests pass but would fail against real server.

### JR-ML-DATA-002 — 6.1 Critical: Generator Name Mismatch (XREPO-01 — confirmed STILL PRESENT).

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 324-340)

**Detail**:

**Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400.

### JR-ML-SEC-018 — 6.2 juniper-cascor-worker.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 396-414)

**Detail**:

**Critical deployment gap.** The worker is the only distributed component that runs on remote machines but has zero deployment infrastructure:

### JR-ML-SEC-019 — 6.4 Phase 4 Success Criteria.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 664-714)

**Detail**:

- [x] Demo and service backends return structurally identical data — `demo_backend.apply_params()` standardized to `{ok, data}` envelope to match service backend; other methods already converged (verified 2026-04-10)

### JR-ML-SEC-020 — 7.1 Immediate (Critical/High).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 523-533)

**Detail**:

1. **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `create_topology_message()` and broadcasts

### JR-ML-OBS-011 — 7.1 Rules by severity label.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 446-456)

### JR-ML-DATA-003 — 8.1 Critical (Fix Immediately).

**Status**: proposed  **Priority**: P0  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 433-442)

**Detail**:

| 3 | juniper-data-client | Update `FakeDataClient._GENERATOR_CATALOG` to match server registry                           |

### JR-ML-OBS-012 — 8.3 Critical Individual Gaps (from WebSocket Architecture Review).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 257-280)

**Detail**:

## 9. Microservices and Infrastructure

### JR-ML-DEP-004 — 9.1 Completed Phases.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 280-289)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 216-225)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-021 — 9.1 Receivers.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 539-558)

**Detail**:

| `default` | `alerts-default@example.com` | **PLACEHOLDER** (`CHANGE_BEFORE_PRODUCTION_USE` flagged) |

### JR-ML-ARCH-001 — 9.2 Route tree.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 558-569)

**Detail**:

route: receiver=default, group_by=[alertname,service], group_wait=30s, group_interval=5m, repeat_interval=4h

### JR-ML-SEC-022 — `_accuracy` assumes one-hot encoded targets — broken for `output_size=1`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 803-821)

### JR-ML-SEC-023 — `ActivationWithDerivative.__setstate__` silently falls back to ReLU for unrecognized activation names.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 746-766)

### JR-ML-SEC-024 — `add_unit` initializes new hidden unit output weights with random values instead of zero.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 718-746)

**Detail**:

Add an `init_output_weights` flag with enumerated values including, but not necessarily limited to, the following: zero and random.
    The flag should be used to determine output node initialization behavior: using `torch.zeros` for the new row(s) vs `toch.randn * 0.1`.
    The flag should have defaults defined in appropriate constants class and local config files.
    Flag default should be accessed by juniper-cascor durring all network initialization locations in the code.
    The flag value

### JR-ML-DEP-005 — Aggregate Results.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 14-28)

**Detail**:

| juniper-ml            | 0.3.0   | 88 pass          | N/A (meta) | 16/16 pass   | 1        | 4      | 3      | 8      |

### JR-ML-SEC-025 — All WebSocket endpoints must enforce per-frame size limits: training 4 KB inbound, control 64 KB.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 145-180)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 681-703)

**Detail**:

Cascor training_stream.py: max_size=4096 on receive.
Cascor control_stream.py: maintain 64 KB cap (regression test).
Canopy /ws/training and /ws/control: audit every receive_*() call; add max_size parameter per control table.

**Notes**:

M-SEC-03 (P0). Must precede Phase B per R1-03. Phase B-pre-a (Day 5 of runbook).

### JR-ML-ARCH-002 — By Severity.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 411-421)

### JR-ML-SEC-026 — Canopy and Cascor must validate WebSocket Origin header against configurable allowlist; reject null origins and wildcards.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 100-145)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 489-550)

**Detail**:

Cascor: new src/api/websocket/origin.py with validate_origin(ws, allowlist) → bool.
Rules: case-insensitive scheme+host, exact port, strip trailing slash, reject null origin, no wildcard support.
Canopy: mirror implementation in src/backend/ws_security.py (do not cross-import).
Cascor default: [http://localhost:8201, https://localhost:8201, http://127.0.0.1:8201, https://127.0.0.1:8201]
Canopy default: [http://localhost:8050, https://localhost:8050, http://127.0.0.1:8050, https://127.0.0.1:8050]

**Notes**:

M-SEC-01 (canopy), M-SEC-01b (cascor). RISK-15 CSWSH mitigation. Env var JUNIPER_WS_ALLOWED_ORIGINS. Phase B-pre (Day 4).

### JR-ML-UI-001 — Canopy dashboard must implement WS-aware polling toggle: skip /api/metrics/history polling when connected.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 250-350)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1087-1159)

**Detail**:

Refactor _update_metrics_store_handler (dashboard_manager.py:2388-2421) to read ws-connection-status via State.
If ws_status.connected: return no_update (WS driving).
Else if (n % 10) != 0: return no_update (slow fallback to 1 Hz).
Else: call /api/metrics/history?limit=1000.
Apply same pattern to _handle_training_state_poll, _handle_candidate_progress_poll, _handle_topology_poll.

**Notes**:

GAP-WS-16, GAP-WS-25. Bandwidth elimination dependent on extendTraces. Phase B (Day 9). Acceptance criterion: <400 KB over 10s.

### JR-ML-UI-002 — Canopy dashboard must implement ws_dash_bridge.js ring buffers and drain callbacks for live WebSocket metrics.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 970-1045)

**Detail**:

New src/frontend/assets/ws_dash_bridge.js (~200 lines): module-scope closure with on(type, ...) handlers
(metrics, state, topology, cascade_add, candidate_progress) and onStatus(...).
Typed JS ring buffers: MAX_METRICS_BUFFER=1000, MAX_EVENT_BUFFER=500.
Bound-in-handler invariant: every push does splice-to-cap (load-bearing for RISK-12).
Expose ONE global: window._juniperWsDrain with drainMetrics, drainState, drainTopology, drainCascadeAdd, drainCandidateProgress, peekStatus, _introspect.
rAF coalescer scaffold disabled per R0-01 disagreement #1 (_scheduleRaf noop, commented structure).
Try-catch wrapper on every handler (FR-RISK-10).

**Notes**:

GAP-WS-04, GAP-WS-05. Bound-in-handler cap non-negotiable per R0-01 §3.2.5. rAF disabled. Phase B (Day 8).

### JR-ML-UI-003 — Canopy metrics panels must migrate from full figure replace to Plotly.extendTraces clientside callback.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 150-250)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1049-1158)

**Detail**:

Metrics panel: new dcc.Store(id='metrics-panel-figure-signal') for clientside callback.
Clientside callback: Input ws-metrics-buffer.data, State metrics-panel-figure-signal.data.
Extract epochs/losses/accs/vlosses/vaccs from buffer_data.events.
Call Plotly.extendTraces("metrics-panel-figure", update, [0,1,2,3,4], 5000).
Guard with document.getElementById('metrics-panel-figure') check (FR-RISK-02).
Wrap in try-catch (FR-RISK-10).
Mirror for candidate_metrics_panel with maxPoints=5000.
Initial figure layout must have uirevision="metrics-panel-v1" (prevents pan/zoom reset).

**Notes**:

GAP-WS-14. P0 bandwidth kill (3 MB/s→<400 KB over 10s). Dummy output pattern per R0-01 §3.3.4. Phase B (Day 9).

### JR-ML-SEC-027 — Canopy must implement cookie-session + CSRF first-frame validation before accepting WebSocket connections.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 145-230)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 604-705)

**Detail**:

Canopy src/main.py: add SessionMiddleware with secret_key from env JUNIPER_CANOPY_SESSION_SECRET.
New /api/csrf endpoint returns {"csrf_token": ...}, mints on first request, rotates hourly.
/ws/training and /ws/control: after accept, receive_json(timeout=5.0) for first frame.
First frame must be type="auth" with csrf_token matching session token (hmac.compare_digest).
On failure: close code 4001 "Authentication failed".
Frontend: inject window.__canopy_csrf in layout, send auth frame immediately in websocket_client.js onopen.

**Notes**:

M-SEC-02 (P0). CSWSH second-line defense. Env var JUNIPER_CANOPY_SESSION_SECRET. Phase B-pre (Day 5).

### JR-ML-SEC-028 — `CascadeCorrelationNetwork._roll_sequence_number` stores all discarded values in a list.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 628-648)

### JR-ML-WS-001 — Cascor bounded 1024-entry replay buffer for lossless reconnect.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 81-131)

### JR-ML-SEC-029 — CasCor distributed training must enforce TLS encryption, worker authentication, multi-tier protection, and comprehensive data validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 370-393)

**Detail**:

SR-1/2/3: Protect network, workers, and primary from threats. SR-5: TLS for all in-transit data. SR-6: Worker authentication. SR-7: Data validation.

### JR-ML-WS-002 — Cascor must add optional seq field to all WebSocket messages and implement replay buffer with ReplayOutOfRange exception.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 233-299)
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 352-420)

**Detail**:

4 commits: (1) optional seq parameter to message builders; (2) WebSocketManager replay buffer with server_instance_id
and _assign_seq_and_append under lock; (3) 0.5s send timeout on _send_json; (4) replay_since() method.
Replay buffer bounded to configurable size (default 1024, range 256-16384).
ReplayOutOfRange raised when last_seq < oldest_available - 1.

**Design**:

- self._seq_lock = asyncio.Lock(), self._next_seq: int = 0
- self._replay_buffer: deque[tuple[int, dict]] = deque(maxlen=replay_buffer_size)
- server_instance_id: str = str(uuid.uuid4())
- async _assign_seq_and_append(message) holds lock, assigns seq, appends to deque
- broadcast() and broadcast_from_thread() routed through _assign_seq_and_append before iteration
- async replay_since(last_seq) returns list[dict] under copy-under-lock pattern

**Notes**:

GAP-WS-13. Carved out from Phase B per R0-03. Phase A-server (Days 2-3 of runbook). Request_id field is additive per R0-04 §12.2.

### JR-ML-TRAIN-008 — CasCor remote workers must support dynamic joining/leaving, tolerate intermittent connections, and provide task redistribution on failure.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 329-360)

**Detail**:

FR-1: Workers connect before/after training. FR-3: Tolerate intermittent connections. FR-6: Dynamic join/leave during rounds. FR-7: Automatic task redistribution on worker failure.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-WS-003 — Cascor replay_since() method for lossless reconnect protocol.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 200-243)

### JR-ML-WS-004 — Cascor server_instance_id UUID generation and advertisement.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 281-333)

### JR-ML-WS-005 — Cascor snapshot_seq in status endpoint under same lock as seq counter.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 787-820)

### JR-ML-WS-006 — Cascor training_stream must implement two-phase registration, resume frame handler with replay, and 1 Hz state throttle coalescer.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 363-450)
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 416-475)

**Detail**:

5 commits: (5) async connect_pending(), promote_to_active() with atomic move under _seq_lock;
(6) training_stream resume handler with 5s timeout for optional resume frame, server_instance_id check, replay_since() call;
(7) snapshot_seq endpoint on /api/v1/training/status; (8) state coalescer replaces 1 Hz drop filter;
(9) protocol error responses on /ws/control with JSON decode error handling.

**Design**:

- Two-phase registration: connect_pending(ws) sends connection_established, adds to _pending_connections
- promote_to_active(ws) atomically moves pending→active under _seq_lock
- Resume handler: await asyncio.wait_for(ws.receive_json(), timeout=5.0), branch on first_frame.type
- Emit resume_ok + replayed messages OR resume_failed with reason (server_restarted/out_of_range/malformed)
- State coalescer: buffer latest pending, flush max 1/sec, bypass throttle for terminal transitions
- Atomic snapshot_seq in status endpoint under _seq_lock

**Notes**:

GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29. R0-03 §8 scenario handling. Phase A-server (Days 2-3).

### JR-ML-WS-007 — Cascor two-phase connection registration with pending set.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 407-453)

### JR-ML-WS-008 — Cascor WebSocketManager emit monotonic sequence numbers on every message.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 133-200)

### JR-ML-WS-009 — CascorControlStream must expose async set_params(params, timeout=1.0) method for WebSocket parameter updates.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 98-103)
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 159-170)

**Detail**:

Adds async set_params(params, *, timeout=1.0, request_id=None) to CascorControlStream in juniper-cascor-client.
Implements per-request correlation map with background recv task for concurrent callers.
Preserves existing command() API. Includes latency instrumentation via _client_latency_ms field.

**Design**:

- Background recv task (_recv_loop) parses JSON responses and maps via request_id
- _pending: Dict[str, asyncio.Future[Dict]]for correlation
- Default 1.0s timeout; raises JuniperCascorTimeoutError on timeout
- Latency measurement: envelope["_client_latency_ms"] = (t_acked - t_sent) * 1000

**Notes**:

GAP-WS-01. Cross-round dup with ml-B/R3-03 which would have surfaced this. Phase A (Day 1 of runbook).

### JR-ML-SEC-030 — Coverage tests bypass actual `fit()` method to avoid timeouts — false coverage confidence.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 969-1002)

**Detail**:

Both Option A and Option B.
    Option A will allow accurate, critical code path coverage checks with non-limiting runtimes.
    Option B will allow the more rigorous checks needed for this application critical code path.

### JR-ML-TEST-002 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 48-53)

**Detail**:

**C-ML-1: Missing git tags for v0.2.1 and v0.3.0**

### JR-ML-SEC-031 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 115-131)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 287-298)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 350-355)

**Detail**:

**C-JD-1: Version mismatch across 4 files:**

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-API-003 — Critical Issues.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 176-187)

**Detail**:

**C-JDC-1: Version doesn't reflect API changes**

### JR-ML-API-004 — Cross-Cutting Themes.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 28-41)

**Detail**:

1. **Changelog debt is universal**: Every application has significant undocumented changes. This is the single most common blocker.

### JR-ML-SEC-032 — CSWSH (Cross-Site WebSocket Hijacking) attack must be closed by Origin allowlist + CSRF first-frame.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 450-520)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 489-550)

**Detail**:

First line: M-SEC-01 (Origin allowlist) lands Day 4.
Second line: M-SEC-02 (CSRF first-frame) lands Day 5.
Combined mitigation closes RISK-15 per R0-02 §10.1.
M-SEC-01 alone blocks third-party page from initiating; M-SEC-02 blocks cross-site session hijacking.
Origin validation must happen pre-accept (fail-closed).

**Notes**:

RISK-15 (High). Mandatory close per R1-03 as page-on-call alert, not ticket. Phase B-pre (Days 4-5).

### JR-ML-WS-010 — Day-1 verification procedure: 5 greps + baseline measurement before any Phase B deploy.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-02_executive_ready_deliverable.md` (lines 28-66)

**Detail**:

Pre-flight checks (must complete before Phase B PR): (1) Confirm ecosystem clean across 3 repos (git status);
(2) Verify GAP-WS-19 resolved at manager.py:138-156; (3) Record 5 scope-determining greps:
  - SessionMiddleware presence (B-pre-b budget);
  - NetworkVisualizer render tech (cytoscape vs Plotly, Phase B scope);
  - Dash version floor;
  - run_coroutine_threadsafe usage (Phase C supervisor);
  - command_id vs request_id in cascor control (Phase G contract).
(4) Measure 1-hour baseline canopy_rest_polling_bytes_per_sec in staging (denominator for >90% reduction acceptance gate).
(5) Create worktrees per Juniper convention (/home/pcalnon/Development/python/Juniper/worktrees/ format <repo>--<branch>--<YYYYMMDD-HHMM>--<shorthash>).
(6) Open Phase 0-cascor + A-SDK worktrees in parallel (no cross-repo dep until Phase G).
(7) Begin with PR-1 (phase-a-sdk-set-params on cascor-client).

**Notes**:

[v2 ARCH→WS re-bucket] Gate on Phase B entry. Dedup with R4-02, R3-03.

### JR-ML-SEC-033 — Duplicate forward-pass logic in `train_output_layer` vs `forward()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 821-841)

### JR-ML-SEC-034 — Early stopping patience state not propagated between `grow_network` iterations.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 591-628)

### JR-ML-SEC-035 — Global singleton initialization race in `get_api_key_auth()` and `get_rate_limiter()`.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 330-362)

### JR-ML-SEC-036 — Hidden unit activation function not wrapped in `ActivationWithDerivative` after HDF5 deserialization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 700-718)

### JR-ML-WS-011 — High Issues.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 298-306)

**Detail**:

**H-JCW-1: `worker.py` at 68.23% coverage**

### JR-ML-SEC-037 — `InlineDataset` allows unbounded array sizes in training start request.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 571-591)

### JR-ML-PERF-001 — JS ring buffers must cap at bound on every push (not in drain callback) to enforce memory invariant.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 550-600)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 976-982)

**Detail**:

ws_dash_bridge.js: bound-in-handler invariant—every push does splice-to-cap (MAX_METRICS_BUFFER=1000, etc).
Load-bearing for RISK-12: DO NOT move the cap into the drain callback.
Ensures memory is bounded even if drain callback is never called or crashes.

**Notes**:

R0-01 §3.2.5 load-bearing. Non-negotiable. Phase B (Day 8). Memory safety for long-running dashboards.

### JR-ML-SEC-038 — juniper-data P0: path traversal fix in csv_import with JUNIPER_DATA_IMPORT_DIR validation.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md` (lines 25-40)

### JR-ML-SEC-039 — Key Categories of Missing Items.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 594-614)

**Detail**:

| Active Bugs (cascor)   | 3         | `TrainingMonitor.current_phase` never updated, uninitialized variable crash    |

### JR-ML-OBS-013 — Low Priority (Future Phases).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 375-408)

**Detail**:

| Phase 5: Observability & Hardening | MICROSERVICES_STARTUP_CODE_REVIEW | AlertManager receivers, alert rules, health standardization                 |

### JR-ML-SEC-040 — `_NoOpLogger` session fixture masks logging-related bugs in production code.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1022-1040)

### JR-ML-ARCH-003 — **P0: polling eliminated**.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-OBS-014 — P2 — Quality / correctness (real but lower-impact).

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 380-391)

**Detail**:

| **A.5** | juniper-cascor | `juniper_cascor_inference_*` (counter + histogram) dead → 4 dashboard panels show flat zeros | Wire `record_inference()` if cas

### JR-ML-ARCH-004 — Phase 1:.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 25-97)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 24-96)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 10-46)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 51-100)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-OBS-015 — Phase 1: Critical Bug Fixes (OI-1 + OI-4) — COMPLETE.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 644-658)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-SEC-041 — Phase 1: Critical Fixes (P0) -- COMPLETED.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 714-732)

**Detail**:

**Goal**: Make existing host-mode startup/shutdown reliable.

### JR-ML-SEC-042 — Phase 1: Critical Startup/Shutdown Fixes — ✅ COMPLETE (commit `03aec86`).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 228-243)

**Detail**:

| 1.1  | `wait_for_health()` function — polls `/v1/health` with configurable timeout | ✅ Implemented |

### JR-ML-ARCH-005 — Phase 2:.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 100-127)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 99-126)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 49-65)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 103-153)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-WS-012 — Phase A-server cascor prerequisites for browser WebSocket migration.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 931-1016)

### JR-ML-OPS-001 — Phase B-pre gate (after Day 6) requires 8 criteria: all M-SEC-NN landed, audit logger, 24h staging, risk sheet.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-06_ops_phasing_risk.md` (lines 79-110)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 850-870)

**Detail**:

1. M-SEC-01 landed (Day 4)
2. M-SEC-01b landed (Day 4)
3. M-SEC-02 landed (Day 5)
4. M-SEC-03 landed (Day 5)
5. M-SEC-04 + M-SEC-05 + M-SEC-10 landed (Day 6)
6. Audit logger exporting counters
7. Staging deployment ≥ 24h (calendar-day gap recommended)
8. Runbook published + RISK-15 marked "in production" in risk tracking sheet

**Notes**:

All 8 must be true before Phase D PR eligible. Per R0-06 §3.2. Non-parallelizable gate.

### JR-ML-WS-013 — Phase B: browser ws_dash_bridge drain, Plotly.extendTraces, connection-status store, polling kill.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 433-594)

**Detail**:

Frontend JS: new `ws_dash_bridge.js` (~200 LOC). Module-scope `window._juniperWsDrain`. Five handlers: metrics, state, topology,
cascade_add, candidate_progress. Per-handler bounded ring buffers. Drain methods: drainMetrics(), drainState(), drainTopology(),
drainCascadeAdd(), drainCandidateProgress(), peekStatus(). Ring bound enforced in handler (not drain callback).
Edit `websocket_client.js`: add `onStatus()` enrichment (connected/reason/reconnectAttempt/ts), jitter to reconnect
(delay = Math.random() * Math.min(CAP, BASE * 2**attempt) with BASE=500ms, CAP=30s), capture `server_instance_id`,
track `seq` (monotonic check + warn gap), emit `resume` frame first on reconnect, fall back to REST snapshot on `resume_failed`.
Delete raw-WS callback in `dashboard_manager.py`.
New `ws_latency.js` (~50 LOC): browser-side latency beacon, records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60 s.
rAF scaffold: `_scheduleRaf` gated function, default disabled per D-03.
Python-side: add `dcc.Store(id='ws-metrics-buffer')` with drain callback on fast-update-interval. Callback reads
`window._juniperWsDrain.drainMetrics()`, writes `{events: [...], gen: int, last_drain_ms: float}`.
Update existing `ws-topology-buffer` + `ws-state-buffer` drain callbacks to read from `window._juniperWsDrain`.
Add `dcc.Store(id='ws-connection-status')` with drain callback that peeks `window._juniperWsDrain.peekStatus()`, emits on change.
Refactor `_update_metrics_store_handler`: read ws-connection-status via State, return no_update when connected, 1 Hz fallback (n % 10 == 0).
Rewrite `MetricsPanel.update_metrics_display()` as clientside_callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`.
Add `uirevision: "metrics-panel-v1"` to layout, hidden `metrics-panel-figure-signal` dummy Store.
Migrate `CandidateMetricsPanel.py` likewise. Apply polling toggle to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`.
**KEEP REST paths** (kill switch + fallback).
NetworkVisualizer minimum wire: wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to cytoscape callback. **If Plotly, convert to extendTraces (+1 day per D-06).**
Connection indicator badge (GAP-WS-26): `html.Div` with clientside_callback reading ws-connection-status, CSS class toggle.
States: connected/reconnecting/offline/demo.
Demo mode (`demo_mode.py`): sets ws-connection-status to `{connected: true, mode: "demo"}` so polling returns no_update, badge shows "demo".
`/api/ws_latency` POST endpoint in `main.py`: increments `canopy_ws_delivery_latency_ms_bucket` histogram AND `canopy_rest_polling_bytes_per_sec` gauge.
Asset cache bust: bump `assets_folder_snapshot` or equivalent so browsers pick up new JS without hard refresh.
Two-flag runtime check: `enabled = Settings.enable_browser_ws_bridge AND NOT Settings.disable_ws_bridge`.
Default `enable_browser_ws_bridge=False` during PR cycle (flip-to-True is separate one-line follow-up P7, not Phase B gate).
Cascor-side residual: None at code level (all cascor work in Phase 0-cascor). Phase B adds Prometheus counters for audit events
deferred from B-pre-a.
Observability: `canopy_rest_polling_bytes_per_sec`, `canopy_ws_delivery_latency_ms_bucket`, `canopy_ws_active_connections`,
`canopy_audit_events_total{event_type}`, `canopy_ws_drain_callback_error_rate`.
Dashboard panels: "WebSocket health" (p50/p95/p99 delivery latency), "Polling bandwidth" (trend).
Tests: 27 total. Unit: `test_ws_dash_bridge.py` (update handlers return no_update when WS connected, fallback REST when disconnected,
connection status reflects cascor WS, metrics buffer bounded). Integration: `test_cascor_adapter_ws.py` (adapter subscribes+forwards,
reconnects, resume_failed handling, demo parity), `test_ws_reconnect_replay.py` (replays 10 missed, stale instance_id triggers snapshot,
no gap, old cascor fallback). Dash_duo e2e: `test_browser_receives_metrics.py` (browser receives event, chart updates per event, no polling
when WS, polling fallback on disconnect, demo parity, buffer bounded, badge reflects state). Playwright e2e: `test_websocket_wire.py`
(frames have seq, resume replays, seq resets on restart, extendTraces used). Phase H regression gate: `test_metrics_dual_format` (BOTH nested
and flat keys present). P0 proof: `test_polling_elimination` (zero `/api/metrics/history` requests after initial load over 60s).
Frame budget: `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` (rAF scaffolded disabled, retargeted to drain callback, marked `latency_recording`).
Fallback 1 Hz: `test_fallback_polling_at_1hz_when_disconnected`. NetworkVisualizer: `test_network_visualizer_updates_on_ws_cascade_add`.
Latency API: `test_canopy_latency_api_aggregates_submissions_into_prom_histogram`. Two-flag interaction: `test_both_flags_interact_correctly`.
Audit Prometheus: `test_audit_log_prometheus_counters` (deferred from B-pre-a).
Runbook: `juniper-canopy/notes/runbooks/ws-bridge-kill.md` (flip `disable_ws_bridge=True`, 5 min TTF).

**Design**:

Drain-based architecture: bounded ring buffers per event type, drain callbacks on fast interval coalesce updates.
Clientside callbacks for Plotly.extendTraces (high-freq updates). Status store drives toggle logic.
Two-flag design: feature gate + permanent kill switch. Default disabled until 72h staging soak validates memory (p95 <=500 MB).

**Notes**:

P0 win. Three-PR sequence: P5 (cascor audit Prom), P6 (canopy drain wiring, flag off), P7 (flag flip post-soak, NOT a gate).
Exit: >90% bandwidth reduction sustained 1 hour, delivery latency histogram live, dashboard panels green, memory p95 <=500 MB after 24h.
Two-flag logic: `enabled = enable_browser_ws_bridge AND NOT disable_ws_bridge`. Rollback: `disable_ws_bridge=true` (2 min TTF).

### JR-ML-OPS-002 — Publish v7.0.1 hotfix to roadmap with verified fixes and shipped CAN-015g/h work.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ROADMAP_AUDIT_2026-05-05.md` (lines 232-242)

### JR-ML-DEP-006 — Rollback Plan.

**Status**: proposed  **Priority**: P0  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 394-412)

**Detail**:

- All git tags can be deleted and recreated: `git tag -d v<VERSION> && git push --delete origin v<VERSION>`

### JR-ML-SEC-043 — `_save_hidden_units` reads activation function name incorrectly from `ActivationWithDerivative` wrapper.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 785-803)

### JR-ML-SEC-044 — `SharedTrainingMemory` shape descriptor only supports tensors up to 2D.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 766-785)

**Detail**:

Immedidately, add validation check rejecting `ndim > 2` with a clear error message.
    - The capacity to allow `ndim > 2` should be documented as an enhancement and added to the development plan.  This feature is required for using some alternate datasets and for the hierarchical network enhancement.

### JR-ML-SEC-045 — Step 6: PR and Worktree Cleanup.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 162-203)

**Detail**:

| `src/frontend/dashboard_manager.py` | UI layout, callback handlers |

### JR-ML-SEC-046 — Triple random seeding in `conftest.py` creates confusing test infrastructure.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1076-1176)

### JR-ML-SEC-047 — `validate_training` has no early stopping path when validation data is absent.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 680-700)

### JR-ML-WS-014 — WebSocket bridge replaces ~3 MB/s REST polling for metrics; achieves >=90% bandwidth reduction.

**Status**: proposed  **Priority**: P0  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 33-40)
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 130-135)

**Detail**:

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope, 
advertises `server_instance_id` + `replay_buffer_capacity` on `connection_established`, supports a 1024-entry 
replay buffer with `resume` handler, exposes `snapshot_seq` atomically on REST. Browser drains `/ws/training` 
into bounded Dash store, renders via Plotly.extendTraces, **stops polling `/api/metrics/history`** when healthy.
Polling kept forever as fallback kill-switch.

**Design**:

Two-phase WebSocket pipeline: Phase 0-cascor (cascor server prerequisites) + Phase B (browser bridge drain).
Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.
Phase B: ws_dash_bridge.js drain module, Plotly extendTraces for metrics panel, connection-status store,
fallback toggle via `enable_browser_ws_bridge` (default False until staging soak) + `disable_ws_bridge` (permanent kill switch).

**Notes**:

[v2 ARCH→WS re-bucket] P0 motivator. Metric: `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Dedup candidate with R3-03.

### JR-ML-SEC-048 — WebSocket control stream documents `set_params` command but does not implement it.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 227-260)

### JR-ML-SEC-049 — `WebSocketManager` `_active_connections` set lacks explicit async synchronization.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 459-490)

### JR-ML-OBS-016 — Who/what closes it.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 699-721)

**Detail**:

- **CALIB-01** (P3) — recommended action: a single calibration PR

### JR-ML-OBS-017 — Wire Alertmanager default and tickets receivers (email via Gmail SMTP) to unblock SLO program close-out by 2026-06-02.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 132-142)

**Detail**:

G2 - Alertmanager receivers silently drop alerts routed to default/tickets.
Both receivers exist as no-op placeholders. Soft blocker before 2026-06-02 soak-close.
Recommend Option A: Email-via-Gmail SMTP for both (use existing SOPS-encrypted creds).

### JR-ML-SEC-050 — 2.1 Current State (Post-Appendix G).

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 54-74)

**Detail**:

- **Cascor side (DONE)**: TrainingState fields populated via `_grow_iteration_callback` and

### JR-ML-SEC-051 — 3.10 WORKER-PENDING-TASKS — `juniper_cascor_pending_tasks` worker→Prometheus bridge gap.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 280-307)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** ✅ **CLOSED 2026-05-04 via juniper-cascor#218**

### JR-ML-TRAIN-009 — Derive candidate_pool_phase from phase_detail in Canopy adapter.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 686-709)

**Detail**:

Adapter derives candidate_pool_status but not candidate_pool_phase. One-line fix: map phase_detail to pool phase (Training/Selecting/Idle).

**Notes**:

Phase 2 P1 fix; doc status COMPLETE; simple derivation gap

### JR-ML-TRAIN-010 — Enhance grow iteration callback with top 2 candidate ID and correlation data.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 148-167)

**Detail**:

Top candidate info never forwarded from CasCor to Canopy; TrainingResults dataclass contains data but callback does not pass it. Fix: add best_candidate_id, best_candidate_uuid, second_candidate fields to callback signature.

**Notes**:

Phase 2 P1 fix; data already available in TrainingResults; doc status COMPLETE

### JR-ML-OBS-018 — Fix Approaches.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 152-202)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 251-301)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 555-605)

**Detail**:

#### Approach A: Return `dash.no_update` on error (RECOMMENDED)

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-DEP-007 — Release juniper-ml v0.4.1 + juniper-observability v0.1.1a: document release steps, validation, tag/publish.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md` (lines 1-50)

### JR-ML-TRAIN-011 — Use Pearson correlation (normalized) instead of raw covariance in candidate training.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 259-283)

**Detail**:

Raw covariance scales with residual magnitude; after first hidden unit, residuals shrink, candidate training gradients weaken (~8× decay observed). Pearson normalized by stddev, scale-invariant.

**Notes**:

Root cause RC-11; Phase 3 finding; doc status indicates implementation complete

### JR-ML-TEST-003 — Complete comprehensive requirements audit and test plan for juniper-canopy with 16 action items.

**Status**: in-progress  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md` (lines 1-100)

**Notes**:

Prerequisite for other canopy development items.

### JR-ML-UI-004 — Fix dataset display bug with comprehensive development plan.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN-FINAL.md` (lines 1-100)

**Notes**:

FINAL revision; check for duplicate with DEVELOPMENT_PLAN.md

### JR-ML-UI-005 — Fix decision boundary visualization in Canopy UI with implementation approach addressing NaN propagation and numerical instability.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md` (lines 1-100)

**Notes**:

V2 revision addressing issues from initial plan.

### JR-ML-OBS-019 — Wire juniper_data_datasets_cached Gauge at every cache mutation site in juniper-data.

**Status**: in-progress  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 142-150)

**Detail**:

G3 - Dead Gauge with no production caller. Defined but never emitted.
In-flight sister PR exists. Add unit test asserting Gauge.value == len(cache) after each operation.

### JR-ML-WS-015 — 0. Document Conventions.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 46-77)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-WS-016 — 0.2 Table of Contents.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 21-45)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-006 — 1. Executive Summary.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 49-50)

### JR-ML-WS-017 — 1. Executive Summary.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 78-79)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-007 — 1.1 Primary Finding.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 51-60)

### JR-ML-ARCH-008 — 1.2 Final Synthesis Outcome.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 61-82)

### JR-ML-ARCH-009 — 1.3 Two Critical Display Blockers.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 83-95)

### JR-ML-ARCH-010 — 1.4 Final Resolution of the Main Divergence.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 96-118)

### JR-ML-WS-018 — 10. Risk Register.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1875-1897)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-011 — 10. Verified Working Paths.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1290-1306)

### JR-ML-ARCH-012 — 11. Consolidated Fix Recommendations.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1307-1357)

### JR-ML-WS-019 — 11. Open Questions for Human Review.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1898-1915)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-013 — 12. Implementation Priority and Ordering.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1409-1464)

### JR-ML-WS-020 — 12. References.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1925-1926)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-014 — 13. Risk Assessment.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1465-1483)

### JR-ML-ARCH-015 — 14. Verification Plan.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1484-1485)

### JR-ML-ARCH-016 — 14.1 Automated Tests.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1486-1504)

### JR-ML-ARCH-017 — 14.2 New Contract Tests (FIX-K).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1505-1554)

### JR-ML-TEST-004 — 14.3 Manual Integration Test.

**Status**: designed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1555-1593)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-ARCH-018 — 14.4 Visual Verification Checklist.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1594-1615)

### JR-ML-ARCH-019 — 15. Files Requiring Modification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1616-1617)

### JR-ML-ARCH-020 — 15.1 juniper-canopy — Required.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1618-1628)

### JR-ML-TRAIN-012 — 15.2 juniper-cascor — Required (cross-repo).

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1629-1635)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-021 — 15.3 Optional / Recommended Cleanup.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1636-1642)

### JR-ML-ARCH-022 — 15.4 Files NOT Requiring Modification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1643-1653)

### JR-ML-ARCH-023 — 16. Post-Synthesis Validation Notes.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1654-1655)

### JR-ML-ARCH-024 — 16.1 Code Validation Results.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1656-1673)

### JR-ML-ARCH-025 — 16.2 Key Reconciliation Decisions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1674-1682)

### JR-ML-ARCH-026 — 16.3 Completeness Assessment.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1683-1733)

### JR-ML-ARCH-027 — 2. Synthesis Methodology and Governing Resolutions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 119-120)

### JR-ML-WS-021 — 2. WebSocket Surface Inventory.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 150-151)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-028 — 2.1 Methodology.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 121-133)

### JR-ML-ARCH-029 — 2.2 Canonical Numbering.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 134-141)

### JR-ML-ARCH-030 — 2.3 Proposal Attribution Legend.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 142-155)

### JR-ML-ARCH-031 — 2.4 Repositories Examined.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 156-165)

### JR-ML-WS-022 — 3. Bidirectional Message Contract.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 437-440)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-032 — 3. Phase 1 / Phase 2 Assessment and Unanimous Findings.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 166-167)

### JR-ML-ARCH-033 — 3.1 Phase 1: Correctly Implemented but Incompletely Validated.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 168-195)

### JR-ML-ARCH-034 — 3.2 Phase 2: Correct but Too Narrow.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 196-207)

### JR-ML-ARCH-035 — 3.3 Unanimous Findings Preserved in Final Document.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 208-221)

### JR-ML-OBS-020 — 3.4 juniper-cascor-worker.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 193-222)

**Detail**:

| Source-of-truth file | `juniper_cascor_worker/http_health.py` (heartbeat HTTP/1.1 server, hand-rolled on `asyncio.start_server`) |

### JR-ML-WS-023 — 4. Nested vs Flat Data Structure Analysis.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 757-758)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-036 — 4. Unified Issue Registry.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 222-223)

### JR-ML-ARCH-037 — 4.1 Final Registry.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 224-248)

### JR-ML-OBS-021 — 4.1 juniper-cascor Performance.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 420-433)

**Detail**:

| **Forward pass**        | ✅ Optimized     | Pre-allocated buffer (OPT-1) eliminates N `torch.cat()` calls                    |

### JR-ML-ARCH-038 — 4.2 Final Classification Notes.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 249-257)

### JR-ML-OBS-022 — 4.2 juniper-canopy Performance.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 433-442)

### JR-ML-API-005 — 4.3 CR-024: Chunked Encoding Body Limit.

**Status**: designed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 402-419)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

### JR-ML-ARCH-039 — 5. Detailed Issue Analysis.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 258-308)

### JR-ML-WS-024 — 5. Latency Tolerance Matrix.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 815-823)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-040 — 6. Cross-Proposal Agreement Matrices.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1016-1017)

### JR-ML-WS-025 — 6. Transport Split Design.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 974-977)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-041 — 6.1 Phase 5 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1018-1042)

### JR-ML-ARCH-042 — 6.2 Phase 4 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1043-1067)

### JR-ML-ARCH-043 — 6.3 Phase 3 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1068-1096)

### JR-ML-ARCH-044 — 7. Disagreements and Final Resolutions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1097-1098)

### JR-ML-WS-026 — 7. Missing / Broken Pieces (Enumerated).

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1128-1131)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-045 — 7.1 Uppercase Status Gap: Removed vs Retained.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1099-1109)

### JR-ML-ARCH-046 — 7.10 State Sync Metrics Severity.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1183-1188)

### JR-ML-ARCH-047 — 7.2 Topology Severity: CRITICAL vs MODERATE.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1110-1118)

### JR-ML-TRAIN-013 — 7.3 CasCor Phase Bug Severity.

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1119-1128)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-048 — 7.4 Hardcoded URL Count: 2 vs 6.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1129-1137)

### JR-ML-ARCH-049 — 7.5 Hardcoded URLs Severity: MODERATE vs LOW.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1138-1146)

### JR-ML-ARCH-050 — 7.6 `/api/metrics` Snapshot: Separate Issue vs Subsumed.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1147-1155)

### JR-ML-DATA-004 — 7.7 Dataset Scatter: Active Bug vs Known Limitation.

**Status**: designed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1156-1164)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-ARCH-051 — 7.8 `candidate_epochs` Mapping Classification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1165-1173)

### JR-ML-ARCH-052 — 7.9 Relay Raw Metrics Severity: MODERATE vs LOW.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1174-1182)

### JR-ML-ARCH-053 — 8. Architectural Root Cause Analysis and Dependency Graph.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1189-1190)

### JR-ML-WS-027 — 8. Browser-Side Verification Strategy.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1426-1427)

**Notes**:

WebSocket/messaging architecture gap or design

### JR-ML-ARCH-054 — 8.1 The Fundamental Problem (Consensus Across All Proposals).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1191-1205)

### JR-ML-ARCH-055 — 8.2 Why the Status Bar Works (All Proposals Agree).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1206-1209)

### JR-ML-ARCH-056 — 8.3 How the Problem Compounds (Best Articulated by P4-D).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1210-1219)

### JR-ML-ARCH-057 — 8.4 Root Cause Dependency Graph.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1220-1258)

### JR-ML-ARCH-058 — 9. False Positives and Retractions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1259-1289)

### JR-ML-ARCH-059 — 9.5 Detailed Design: Improved `juniper_plant_all.bash`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 603-617)

**Detail**:

# 1. wait_for_health() function that polls /v1/health with configurable timeout

### JR-ML-ARCH-060 — 9.6 Detailed Design: Improved `juniper_chop_all.bash`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 617-630)

**Detail**:

# 1. validate_pid() function that checks /proc/<pid>/cmdline

### JR-ML-UI-006 — 9.7 Detailed Design: systemd Units.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 630-669)

**Detail**:

After=network-online.target juniper-data.service

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

### JR-ML-SEC-052 — Issue Remediations, Section 11.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 9-59)

**Detail**:

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

### JR-ML-SEC-053 — Primary.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 439-448)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)

### JR-ML-SEC-054 — 13.2 Unimplemented Roadmap Items.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 419-436)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 330-347)

**Detail**:

| DEPLOY-RD-01 | 0.3.0           | Production compose profile with resource limits          | 🔴 NOT DONE                                                        |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-005 — 14.3 Deferred Roadmap Items.

**Status**: deferred  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 453-466)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 364-377)

**Detail**:

## 15. Client Library Outstanding Items

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-055 — 3.0 Phase 1 Execution Results (2026-04-09).

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 53-82)

**Detail**:

| CR-006 deconflation (fit())                                            | VERIFIED             | `cascade_correlation.py:1450` routes `max_epochs` to `train_output_layer()`; `cascade_correlation.py:1476-1488` routes `max_iterations` to `grow_network()`           |

### JR-ML-DATA-006 — 7.3 juniper-data — Constants Refactor ✅; Roadmap Items Deferred.

**Status**: deferred  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 392-402)

**Detail**:

| HTTP status codes → `starlette.status`                            | ✅ Complete                              |

### JR-ML-SEC-056 — 7.5 juniper-deploy — Multiple Plans Partially Complete.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 409-433)

**Detail**:

| Post-release roadmap: Grafana dashboards, Prometheus alerting | ✅ Done (v0.2.0)                                                         |

### JR-ML-API-006 — CAN-015g/h snapshot-loading endpoints: restore, replay, resume, retrain with FSM state transitions.

**Status**: deferred  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/PHASE_6E_DEFERRED_CAN-015GH_DESIGN.md` (lines 1-100)

### JR-ML-SEC-057 — Issue Remediations, Section 14 — Performance and Roadmap.

**Status**: deferred  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 540-590)

**Detail**:

#### JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

### JR-ML-SEC-058 — 4.0 Phase 2 Execution Results (2026-04-09).

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 336-360)

**Detail**:

`fix/interface-phase2-docs` in juniper-ml. All four issues were verified

### JR-ML-TRAIN-014 — 4.1 CR-023: Whitelist Training Start Parameters.

**Status**: rejected  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 360-378)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: VERIFIED + test added

### JR-ML-SEC-059 — Issue Remediations, Section 18.

**Status**: rejected  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_a_security_concurrency_error.md` (lines 463-513)

**Detail**:

#### ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client)

### JR-ML-API-007 — Issue Remediations, Section 21.

**Status**: rejected  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 692-742)

**Detail**:

#### API-01: Health `status` Value Inconsistent

### JR-ML-DATA-007 — Task 2 (Dataset).

**Status**: rejected  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 374-381)

### JR-ML-API-008 — /api/v1/training/status returns snapshot_seq + server_instance_id atomically.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 117-117)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-028 — /ws/control handler returns protocol-error envelopes, echoes command_id, NO seq on command_response.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 120-120)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TRAIN-015 — 0-cascor: `git revert` P1.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 342-343)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-016 — 0-cascor: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 339-340)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-017 — 0-cascor: `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 340-341)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-018 — 0-cascor: Rolling cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 341-342)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-OBS-023 — 01: Dual metric format removed aggressively.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 375-376)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-061 — 02: Phase B clientside_callback hard to debug.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 376-377)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-062 — 03: Phase C REST+WS ordering race.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 377-378)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-063 — 04: Slow-client blocks broadcasts.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 378-379)

### JR-ML-TEST-005 — 05: Playwright misses real-cascor regression.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 379-380)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TRAIN-019 — 06: Reconnection storm after cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 380-381)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-064 — 07: 50-conn cap hit (multi-tenant).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 381-382)

### JR-ML-ARCH-065 — 08: Demo mode parity breaks.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 382-383)

### JR-ML-ARCH-066 — 09: Phase C unexpected behavior.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 383-384)

### JR-ML-SEC-060 — 1.3 Metaparameter Wiring Gaps.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 146-188)

**Detail**:

**Repositories**: juniper-canopy, juniper-cascor

### JR-ML-ARCH-067 — 10: Browser memory exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 384-385)

### JR-ML-TRAIN-020 — 11: Silent data loss via drop-oldest.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 385-386)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-UI-007 — 12: Background tab memory spike.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 386-387)

**Notes**:

[v2 ARCH→UI re-bucket]

### JR-ML-ARCH-068 — 13: Orphaned commands after timeout.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 387-388)

### JR-ML-API-009 — 14.2 Performance Issues.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 444-453)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 355-364)

**Detail**:

| JD-PERF-01 | **HIGH**   | `api/routes/datasets.py:107`        | Sync `generator.generate()` blocks async event loop. Needs `asyncio.to_thread()`.              |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TRAIN-021 — 14: Cascor crash mid-broadcast.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 388-389)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-WS-029 — 15: **CSWSH attack**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 389-390)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-DATA-008 — 2.1 Documents in `notes/development/`.

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 66-82)

**Detail**:

| DATASET_DISPLAY_BUG_ANALYSIS.md               | Dataset tab blank        | RC-1 stale install, RC-2 FakeClient, CF-1..CF-3 | **FIXED** — `get_dataset_data()` added to client (6ed0fda), FakeClient (be17329), version bumped to 0.3.0 (09adb16), `hasattr` guard + broad exception in adapter (line 707)

### JR-ML-TRAIN-022 — 2.1 juniper-ml: CI & Script Fixes.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 131-171)

**Detail**:

**2.1.1 CI path fix** (`ci.yml:244`):

### JR-ML-OBS-024 — 2.1 Per-Application Inventory.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 51-101)

**Detail**:

| Python entry point             | `juniper_data/__main__.py`                                                                | Active                                      |

### JR-ML-SEC-061 — 2.5 juniper-data.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 327-348)

**Detail**:

| JD-01 | **High**   | `api/security.py`        | 59      | Non-constant-time API key comparison — timing side-channel attack vector                     |

### JR-ML-API-010 — 3.1 Root Cause.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 128-137)

**Detail**:

`ServiceBackend.get_dataset()` (service_backend.py:155-168) returns metadata only. The

### JR-ML-UI-008 — 3.2 Fix — Phase 1: Canopy Graceful Degradation (canopy-only).

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 137-151)

**Detail**:

**File:** `src/frontend/components/dataset_plotter.py`

### JR-ML-OBS-025 — 3.3 Fix — Phase 2: Cross-Repo Dataset Data Endpoint.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 151-187)

**Detail**:

result = {"train_x": self._train_x.detach().cpu().tolist(),

### JR-ML-API-011 — 3.3 Performance.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 178-187)

**Detail**:

| ID         | Severity   | File:Line                    | Description                                                                                          |

### JR-ML-SEC-062 — 4.2 Fix.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 213-263)

**Detail**:

**File:** `src/backend/cascor_service_adapter.py`

### JR-ML-OBS-026 — 4.2 Strengths.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 313-328)

**Detail**:

| **Dependency ordering** | `depends_on` with `condition: service_healthy` ensures proper startup sequence        |

### JR-ML-API-012 — 4.3 Health Check Pattern Recommendation.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 627-655)

**Detail**:

- cascor_service: reachable / unreachable / demo_mode

### JR-ML-API-013 — 4.3 juniper-data Performance.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 442-455)

**Detail**:

| **Sync generation**    | ⚠️ Concern | `generator.generate(params)` blocks event loop in async endpoint  |

### JR-ML-OBS-027 — 5.0 Phase 3 Execution Results (2026-04-09).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 451-491)

**Detail**:

roadmap snapshot and Phase 3 execution. The only real gap was the demo backend,

### JR-ML-TRAIN-023 — 5.1 Define Progress Fields in TrainingState.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 491-505)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor

### JR-ML-API-014 — 5.1 Tag & Release Order.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 351-364)

**Detail**:

1. juniper-data (upstream, no Juniper dependencies)

### JR-ML-API-015 — 5.2 `/api/state` Endpoint.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 306-310)

**Detail**:

Include all 22 meta-parameter fields in the state response. Use `.get()` with `TrainingConstants` defaults for any missing fields to handle backward compatibility when the backend doesn't yet store all parameters.

### JR-ML-SEC-063 — 5.3 Grow-Network State Updates.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 521-534)

**Detail**:

**Effort**: 1-2 days | **Repo**: juniper-cascor

### JR-ML-API-016 — 5.3 juniper-data.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 145-159)

**Detail**:

| BUG-JD-01 | **MEDIUM** | `batch_export` builds entire ZIP in memory — OOM risk           | `api/routes/datasets.py:416-434` | Large dataset exports accumulate entire ZIP in memory before sending response                 |

### JR-ML-DATA-009 — 6.1 Card Structure.

**Status**: proposed  **Priority**: P1  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 331-381)

**Detail**:

dbc.Card (className="mb-3")

### JR-ML-API-017 — 6.1 Risks.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 492-505)

### JR-ML-OBS-028 — 7.1 Canopy Enhancement Backlog (CAN-000 through CAN-021).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 203-237)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 158-192)

**Detail**:

## 8. WebSocket Migration (R5-01 Remaining Phases)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-UI-009 — 7.3 Long-Term (Low/Architectural).

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 549-566)

**Detail**:

12. **Add shared memory startup sweep**: On cascor server startup, remove stale `juniper_train_*` blocks from `/dev/shm`.

### JR-ML-UI-010 — 7.5 UI Overflow.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 448-460)

### JR-ML-SEC-064 — 8.2 New Tests Required.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 302-314)

**Detail**:

| `test_dataset_target_conversion_binary`             | Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax) |

### JR-ML-SEC-065 — 8.3 Visual Verification Checklist.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 314-329)

**Detail**:

- [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training

### JR-ML-OBS-029 — 9.1 juniper-canopy (all phases).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 329-341)

**Detail**:

| `src/backend/cascor_service_adapter.py`          | Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2) | 1, 4  |

### JR-ML-DEP-010 — 9.3 Microservices Architecture Roadmap (Phases 5–9).

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 299-315)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 235-251)

**Detail**:

| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-066 — 9.4 Files NOT Requiring Modification.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 354-366)

**Detail**:

- `network_visualizer.py` — uses count-based positioning, not numeric `layer` field

### JR-ML-ARCH-069 — --: Mid-week deploys for behavior-changing flag flips only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 300-301)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-070 — --: Minimum-viable carveout ~7 days (P0 only).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 301-302)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-024 — --: Phase 0-cascor staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 295-296)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-071 — --: Phase B staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 296-297)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-072 — --: Phase B-pre-b staging soak = 48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 297-298)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-073 — --: Phase C flag-flip canary >= 7 days production data.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 299-300)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-074 — --: Phase D entry gate = B-pre-b in production >=48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 298-299)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-025 — A-SDK: Downgrade cascor-client pin.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 343-344)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-075 — A-SDK: PyPI yank.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 344-345)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-WS-030 — Add async set_params() method to CascorControlStream for WebSocket parameter control.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 94-150)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-OBS-030 — Add dashboard/alert lint lane to juniper-deploy CI.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 284-290)

**Detail**:

Cross-cutting recommendation: Add CI guardrail to prevent future stale panels.
Run promtool check rules on alert_rules.yml and recording_rules.yml.
JSON-schema validate each dashboard and promtool query instant against synthetic Prometheus.

### JR-ML-TEST-006 — Add macOS CI matrix leg to all repos for cross-platform coverage (rss_mb sampling, POSIX assumptions).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 75-125)

**Detail**:

R3.7 Resolution: Use macos-latest (ARM); run all unit tests (not integration/perf); start in continue-on-error mode for 2 weeks, then make required.

**Notes**:

macOS-13 (Intel) removed as deprecated.

### JR-ML-SEC-067 — Add security hardening to check_doc_links.py including universal bounds checking, input validation, and traversal depth limits.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 813-920)

**Detail**:

Existing vulnerability: filesystem existence oracle via crafted links like ../../../../etc/passwd.

Required fixes:
1. Universal bounds check - constrain resolved paths to repo/ecosystem root using Path.is_relative_to()
2. Input validation - reject null bytes and absolute paths before path construction
3. Traversal depth limit - reject links with >5 ../ segments
4. Structural validation in skip mode - ensure cross-repo links don't escape target repo

### JR-ML-SEC-068 — Add security logging remediation across Juniper services.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_LOGGING_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Audit trail and incident response capability.

### JR-ML-SEC-069 — Additional Findings from CasCor Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 54-66)

**Detail**:

1. **`create_topology_message()` is dead code in juniper-cascor** — The message builder exists in `api/websocket/messages.py` (line 35) and is exported in `__init__.py`, but no production code path ever calls it. CasCor only sends `cascade_add` event messages (with event metadata, no topology data).

### JR-ML-SEC-070 — `add_units_as_layer` stores numpy copies of weights in history.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 895-913)

### JR-ML-WS-031 — Adopt WebSocket-based remote worker architecture (Approach A) with phased rollout through Phase 4.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 1496-1520)

**Detail**:

Phases: 1a security fixes, 1b WebSocket endpoint, 2 remote agent, 3 unified distributor, 4 hardening.

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-TEST-007 — Align CI/pre-commit across 8 repos to common baseline: same union of workflows, hooks, pre-commit config.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CI_PIPELINE_ALIGNMENT_PLAN_2026-04-29.md` (lines 28-42)

### JR-ML-UI-011 — All WebSocket JS handlers must wrap body in try-catch to prevent single exception from breaking dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 500-550)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 981-991)

**Detail**:

ws_dash_bridge.js: every on(type, ...) handler body wrapped in try { ... } catch (e) { console.error('[ws_dash_bridge]', e); }.
Clientside callback for extendTraces: try { ... } catch (e) { return window.dash_clientside.no_update; }.
Prevents exceptions from hanging callback chain.

**Notes**:

FR-RISK-10. Phase B (Day 8-9). Defensive coding for dashboard stability.

### JR-ML-API-018 — All WebSocket message envelopes must include optional seq field and preserve backward compatibility.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 194-240)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 262-282)

**Detail**:

Message builders add optional seq: int | None = None parameter.
seq serializes as top-level field when present; omitted when None (backward compat).
Every message type (state, metrics, topology, etc.) flows through _assign_seq_and_append.
Cascade client that does not understand seq field must still function (field is optional in parsers).

**Notes**:

Phase A-server (Day 2). Backward compatibility non-negotiable. Unknown fields must be ignored per schema.

### JR-ML-ARCH-076 — Audit async route handlers; ensure all blocking I/O wrapped in asyncio.to_thread().

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md` (lines 1-50)

### JR-ML-ARCH-077 — `audit_log_enabled`: B-pre-a.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 315-316)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-078 — B-pre-a: `JUNIPER_AUDIT_LOG_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 349-350)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-079 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS='*'`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 347-348)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-080 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS=<broader>`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 346-347)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-081 — B-pre-a: `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 348-349)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-082 — B-pre-a: `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 345-346)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-083 — B-pre-b: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 351-352)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-084 — B-pre-b: `JUNIPER_WS_RATE_LIMIT_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 352-353)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-085 — B-pre-b: `JUNIPER_WS_SECURITY_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 350-351)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-086 — B: Hardcoded ring-cap reduction.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 355-356)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-087 — B: `JUNIPER_DISABLE_WS_BRIDGE=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 354-355)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-088 — B: `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 353-354)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-089 — B: URL `?ws=off` diagnostic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 356-357)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-032 — Background _recv_task started on connect; parses inbound, pops future by command_id, set_result(envelope).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 219-219)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-OBS-031 — broadcast_from_thread adds Task.add_done_callback(_log_exception) (GAP-WS-29).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 119-119)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-033 — BROKEN: - MISSING — feature does not exist.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 61-62)

### JR-ML-WS-034 — Browser must send ping frame every 30s; expect pong within 5s; close and reconnect on timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 400-450)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1313-1318)

**Detail**:

assets/websocket_client.js: send {"type": "ping"} every 30s; expect {"type": "pong"} within 5s.
Close + reconnect on timeout (true heartbeat loss indicates network issue).
Cascor training_stream_handler inbound dispatcher already handles ping → pong (Day 3 handle_training_inbound).

**Notes**:

GAP-WS-12. Phase F (Day 11). Does not bypass auth (heartbeat inside authenticated session).

### JR-ML-ARCH-090 — BUG-CC-01: `create_topology_message()` Not Fully Implemented.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 536-561)

### JR-ML-ARCH-091 — BUG-CC-02: `cascade_add` Correlation Hardcoded to `0.0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 564-578)

### JR-ML-ARCH-092 — BUG-CC-03: `or` Fallback Bugs for Falsy Values in spiral_problem.py.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 581-595)

### JR-ML-ARCH-093 — BUG-CC-04: Version Strings Inconsistent Across File Headers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 598-612)

### JR-ML-ARCH-094 — BUG-CC-05: `remote_client_0.py` Hardcoded Old Monorepo Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 615-641)

### JR-ML-ARCH-095 — BUG-CC-06: 32 Test Files Have Hardcoded `sys.path.append` to Old Monorepo.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 644-658)

### JR-ML-ARCH-096 — BUG-CC-07: `TrainingMonitor.current_phase` Never Updated by State Machine.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 661-675)

### JR-ML-ARCH-097 — BUG-CC-08: Undeclared Global `shared_object_dict`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 678-692)

### JR-ML-ARCH-098 — BUG-CC-09: `validate_training_results` Uninitialized Variable When `max_epochs=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 695-709)

### JR-ML-ARCH-099 — BUG-CC-10: `validate_training` Validation Variables Not Initialized for No-Validation-Data Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 712-726)

### JR-ML-ARCH-100 — BUG-CC-11: Walrus Operator Precedence Bug in `utils.py`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 729-743)

### JR-ML-ARCH-101 — BUG-CC-12: `load_dataset` Uses `yaml.safe_load` Instead of `torch.load`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 746-779)

### JR-ML-ARCH-102 — BUG-CC-13: `RateLimiter._counters` Never Pruned — Unbounded Memory Growth.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 782-796)

### JR-ML-ARCH-103 — BUG-CC-14: `HandshakeCooldown._rejections` Never Pruned for Non-Blocked IPs.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 799-813)

### JR-ML-ARCH-104 — BUG-CC-15: `RequestBodyLimitMiddleware` Reads Full Body Before Size Check.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 816-830)

### JR-ML-ARCH-105 — BUG-CC-16: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 833-841)

### JR-ML-OBS-032 — BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 844-852)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-106 — BUG-CC-18: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 855-863)

### JR-ML-ARCH-107 — BUG-CN-01: `_stop.clear()` Race — `_perform_reset()` Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 868-882)

### JR-ML-ARCH-108 — BUG-CN-02: DashboardManager God Class (3,232 Lines).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 885-907)

### JR-ML-ARCH-109 — BUG-CN-03: 226 `hasattr` Guards in Tests Skip Test Logic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 910-924)

### JR-ML-ARCH-110 — BUG-CN-04: `_api_base_url` Hardcoded to `127.0.0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 927-941)

### JR-ML-ARCH-111 — BUG-CN-05: Service Populate Param Values with Int Defaults.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 944-958)

### JR-ML-ARCH-112 — BUG-CN-06: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 961-976)

### JR-ML-ARCH-113 — BUG-CN-07: Duplicate `APP_VERSION` Assignment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 979-993)

### JR-ML-ARCH-114 — BUG-CN-08: `_demo_snapshots` List Grows Unbounded in Demo Mode.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 996-1010)

### JR-ML-ARCH-115 — BUG-CN-09: `WebSocketManager.active_connections` Not Thread Safe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1013-1027)

### JR-ML-ARCH-116 — BUG-CN-10: `message_count` Increment Not Atomic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1030-1044)

### JR-ML-ARCH-117 — BUG-CN-11: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1047-1055)

### JR-ML-ARCH-118 — BUG-CN-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1058-1066)

### JR-ML-ARCH-119 — BUG-JD-01: `batch_export` Builds Entire ZIP in Memory — OOM Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1071-1093)

### JR-ML-ARCH-120 — BUG-JD-02: `delete()` TOCTOU Race Condition.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1096-1110)

### JR-ML-ARCH-121 — BUG-JD-03: `update_meta` Writes Without Temp File — Partial Data Exposure.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1113-1127)

### JR-ML-ARCH-122 — BUG-JD-04: Deterministic IDs with `seed=None` → Stale Cache Returns.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1130-1144)

### JR-ML-ARCH-123 — BUG-JD-05: `_version_lock` Is Class Variable — Won't Work Across Workers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1147-1169)

### JR-ML-ARCH-124 — BUG-JD-06: `ReadinessResponse.timestamp` Uses Naive `datetime.now()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1172-1186)

### JR-ML-ARCH-125 — BUG-JD-07: `record_dataset_generation()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1189-1203)

### JR-ML-ARCH-126 — BUG-JD-08: `record_access()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1206-1220)

### JR-ML-OBS-033 — BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1223-1237)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-127 — BUG-JD-10: ALL Storage Operations Block Async Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1240-1248)

### JR-ML-ARCH-128 — BUG-JD-11: `record_access` TOCTOU Race on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1251-1259)

### JR-ML-ARCH-129 — C-01: Correlation field is `command_id`, NOT `request_id` -- every repo, every test.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 228-229)

### JR-ML-WS-035 — C-02: `command_response` has NO `seq` field; `/ws/control` has no replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 229-230)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-130 — C-03: `set_params` default timeout = 1.0 s (not 5.0 s).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 230-231)

### JR-ML-ARCH-131 — C-04: SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 242-243)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-036 — C-05: Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 243-244)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-132 — C-06: `server_instance_id` = programmatic key; `server_start_time` = advisory only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 231-232)

### JR-ML-ARCH-133 — C-07: `replay_buffer_capacity` added to `connection_established`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 232-233)

### JR-ML-ARCH-134 — C-08: Two-phase registration via `_pending_connections` set.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 233-234)

### JR-ML-TRAIN-026 — C-09: Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 234-235)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-027 — C-10: Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 256-257)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-037 — C-11: GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 257-258)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-028 — C-12: Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 268-269)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-135 — C-13: Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 269-270)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-136 — C-14: Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bri.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 270-271)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-PERF-002 — C-15: Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 271-272)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-137 — C-16: rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 272-273)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-138 — C-17: REST fallback cadence during disconnect = 1 Hz (NOT 100 ms).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 244-245)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-038 — C-18: `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 245-246)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-139 — C-19: Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 246-247)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-WS-039 — C-20: GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 273-274)

**Notes**:

[v2 ARCH→WS re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-140 — C-21: NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 274-275)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-141 — C-22: `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 275-276)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-142 — C-23: REST endpoints preserved FOREVER -- no deprecation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 247-248)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-143 — C-24: Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 258-259)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-144 — C-25: One-resume-per-connection rule (second resume -> close 1003).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 248-249)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-145 — C-26: Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 259-260)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-146 — C-27: **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 260-261)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-147 — C-28: Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 276-277)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-148 — C-29: Debounce lives in Dash clientside callback (NOT SDK), 250 ms.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 249-250)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-149 — C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 250-251)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-150 — C-31: Shadow traffic: rejected.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 261-262)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TEST-008 — C-32: Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 282-283)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-151 — C-33: Per-command HMAC deferred indefinitely.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 262-263)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TEST-009 — C-34: Contract-test pytest marker `contract` runs on every PR in all 3 repos.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 283-284)

**Notes**:

[v2 ARCH→TEST re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-PERF-003 — C-35: Latency tests are recording-only in CI; strict assertions local-only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 284-285)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-152 — C-36: Total effort: 13.5 target / 15.75 planning buffer / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 294-295)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-OBS-034 — C-37: P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 285-286)

**Notes**:

[v2 ARCH→OBS re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-153 — C-38: Observability-before-behavior rule: metrics + panels + alerts before the behavior change.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 286-287)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-154 — C-39: Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 287-288)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-155 — C-40: Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 235-236)

### JR-ML-WS-040 — C-41: `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 236-237)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-156 — C-42: Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-relia.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 288-289)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-157 — C: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 357-358)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-158 — C: `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 358-359)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-041 — Caller-cancellation cleans correlation map entry in finally.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 221-221)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-API-019 — Canonical settings table: 25+ configuration variables across cascor/canopy with env vars, types, defaults, validation.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 212-242)

**Detail**:

Settings with Pydantic Field(..., description=...). Cascor: ws_replay_buffer_size (int, 1024, env JUNIPER_WS_REPLAY_BUFFER_SIZE, validation >=0),
ws_send_timeout_seconds (float, 0.5, JUNIPER_WS_SEND_TIMEOUT_SECONDS, >0), ws_state_throttle_coalesce_ms (int, 1000, JUNIPER_WS_STATE_THROTTLE_COALESCE_MS, >0),
ws_resume_handshake_timeout_s (float, 5.0, JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S, >0), ws_pending_max_duration_s (float, 10.0, JUNIPER_WS_PENDING_MAX_DURATION_S, >0),
ws_max_connections_per_ip (int, 5, JUNIPER_WS_MAX_CONNECTIONS_PER_IP, >=1), ws_allowed_origins (list[str], [], JUNIPER_WS_ALLOWED_ORIGINS, no '*'),
ws_idle_timeout_seconds (int, 120, JUNIPER_WS_IDLE_TIMEOUT_SECONDS, >=0), ws_backpressure_policy (Literal, drop_oldest_progress_only, JUNIPER_WS_BACKPRESSURE_POLICY, enum).
Canopy: ws_security_enabled (bool, True, JUNIPER_WS_SECURITY_ENABLED, bool; CI refuses False in prod), ws_max_connections_per_ip (int, 5, JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP, >=1),
ws_allowed_origins (list[str], localhost defaults, JUNIPER_CANOPY_WS_ALLOWED_ORIGINS, no '*'), ws_rate_limit_enabled (bool, True, JUNIPER_WS_RATE_LIMIT_ENABLED, bool),
ws_rate_limit_cps (int, 10, JUNIPER_WS_RATE_LIMIT_CPS, >=1), audit_log_enabled (bool, True, JUNIPER_AUDIT_LOG_ENABLED, bool),
audit_log_path (str, /var/log/canopy/audit.log, JUNIPER_AUDIT_LOG_PATH, path), audit_log_retention_days (int, 90, JUNIPER_AUDIT_LOG_RETENTION_DAYS, >=1),
disable_ws_control_endpoint (bool, False, JUNIPER_DISABLE_WS_CONTROL_ENDPOINT, bool), enable_browser_ws_bridge (bool, False→True, JUNIPER_ENABLE_BROWSER_WS_BRIDGE, bool),
disable_ws_bridge (bool, False, JUNIPER_DISABLE_WS_BRIDGE, bool), enable_raf_coalescer (bool, False, JUNIPER_ENABLE_RAF_COALESCER, bool),
enable_ws_latency_beacon (bool, True, JUNIPER_ENABLE_WS_LATENCY_BEACON, bool), use_websocket_set_params (bool, False, JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS, bool),
ws_set_params_timeout (float, 1.0, JUNIPER_WS_SET_PARAMS_TIMEOUT, >0), enable_ws_control_buttons (bool, False, JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS, bool),
disable_ws_auto_reconnect (bool, False, JUNIPER_DISABLE_WS_AUTO_RECONNECT, bool).
CI assert: every setting documented, every env var round-trips.

**Design**:

Pydantic BaseModel with Field(..., description=...) for documentation. Type-safe validation on load.
env var naming: JUNIPER_<SETTING_UPPER> for cascor, JUNIPER_CANOPY_<SETTING_UPPER> or JUNIPER_<SETTING_UPPER> for canopy (varies by context).

**Notes**:

[v2 ARCH→API re-bucket] Central to Phase execution. All settings present before merge. CI lint enforces documentation + round-trip.

### JR-ML-WS-042 — Canopy adapter must split apply_params into hot (WebSocket) and cold (REST) paths; route hot params via CascorControlStream.set_params.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1161-1276)

**Detail**:

Canopy src/config/settings.py: add use_websocket_set_params: bool = Field(default=False, ...).
Env var JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS.
Class constants _HOT_CASCOR_PARAMS and _COLD_CASCOR_PARAMS (enumeration from R0-04 §5.1).
Refactor apply_params(**params): if flag False → _apply_params_cold; if True → split hot/cold, unclassified keys REST+WARNING.
Run hot FIRST, then cold (per R0-04 §5.1 ordering guarantee with lifecycle._training_lock serialization).
_apply_params_hot: check control_stream connected; asyncio.run_coroutine_threadsafe(..., self._event_loop).result(timeout=2.0).
Fall back to REST on JuniperCascorTimeoutError, JuniperCascorConnectionError.
Surface server error (do NOT fall back) on JuniperCascorClientError.

**Notes**:

Phase C (Day 10). Feature flag default False per R0-04 §5.6 ack-vs-effect analysis. Flag remains False in Phase C release.

### JR-ML-WS-043 — Canopy must implement _control_stream_supervisor task that maintains persistent WebSocket connection to cascor.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 100-200)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1217-1260)

**Detail**:

Background task: loop while not shutdown.is_set(): connect → wait_closed() → backoff [1, 2, 5, 10, 30] seconds.
Launched alongside _metrics_relay_task in start_metrics_relay().
Cancelled in stop_metrics_relay().
self._control_stream = None when not connected (used by _apply_params_hot gate).
Latency instrumentation: read envelope["_client_latency_ms"] from set_params ack, observe SET_PARAMS_LATENCY_MS.labels(transport="websocket").

**Notes**:

Enables Phase C and Phase D. Separate from metrics relay (Day 7). Histogram buckets per R0-04 §7.

### JR-ML-OBS-035 — Canopy must implement JSON audit logger for WebSocket control commands with scrubbing and CRLF escaping.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 250-320)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 800-846)

**Detail**:

New src/backend/audit_log.py: canopy.audit logger with JSON formatter, TimedRotatingFileHandler(when="midnight", backupCount=90).
AUDIT_SCRUB_ALLOWLIST auto-derived from SetParamsRequest.model_fields.keys().
audit_log.ws_control(event, ...): logs session_id hash, remote_addr, origin, endpoint, command, request_id, params_keys,
params_scrubbed (before/after), result, seq per R0-02 §4.6 rules 1-11.
CRLF escape every user-controlled field at write-time.
audit_log.ws_auth(...) for auth/origin/cookie failures.
Settings: audit_log_path, audit_log_retention_days.

**Notes**:

IMPL-SEC-32..35. Configurable path and retention. Phase B-pre (Day 6). M-SEC-10 consolidation per R1-03.

### JR-ML-WS-044 — Canopy training control buttons (start/stop/pause/resume/reset) must route over WebSocket with REST fallback.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 250-350)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1278-1355)

**Detail**:

Replace REST POST callback body with clientside callback calling window.cascorControlWS.send({command, command_id: uuidv4()}).
Fallback: if window.cascorControlWS not connected, POST to /api/train/{command}.
Add command_id generation in ws_dash_bridge.js.
Track pending commands in JS map; mark button "pending verification" until command_response or matching state event.
Cascor: accept optional command_id in inbound frames; echo in command_response (pass-through string, no validation).

**Notes**:

GAP-WS-32, RISK-13. Cascor Day 3 verify command_id echo. Phase D (Day 11). BLOCKED on Phase B-pre in production ≥24h.

### JR-ML-SEC-071 — Canopy WebSocket handlers must enforce 120s idle timeout; close with code 1000 on expiry.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 320-360)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 813-821)

**Detail**:

Wrap receive_text() main loop in asyncio.wait_for(..., timeout=120) on both /ws/training and /ws/control.
On asyncio.TimeoutError, close with 1000 "Normal Closure".
Heartbeat from Phase F will reset timer (safe because it ships later but idle timeout defensible alone).
IMPL-SEC-30 checkpoint.

**Notes**:

IMPL-SEC-30. Idle timeout does not force disconnect during long polling; only closes on true inactivity. Phase B-pre (Day 6).

### JR-ML-SEC-072 — Cascor /ws/control must enforce per-connection command rate limit (leaky bucket, 10/sec).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 210-250)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 786-810)

**Detail**:

New src/api/websocket/rate_limit.py: per-connection leaky bucket, capacity 10, refill 10/sec.
control_stream_handler consumes 1 token per command frame.
On empty bucket: reply {"type": "command_response", "data": {"status": "rate_limited", "retry_after": 0.3}}.
Do NOT close on rate limit; allow client to retry.
One-resume-per-connection micro-control: in training_stream resume handler, record connection-scoped resumed_once.
Second resume frame closes with 1003.

**Notes**:

M-SEC-05 (P1), IMPL-SEC-29. Phase B-pre (Day 6).

### JR-ML-WS-045 — Cascor /ws/control protocol error responses per GAP-WS-22.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 916-928)

### JR-ML-WS-046 — Cascor backpressure handling with 0.5s per-send timeout (quick fix).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 454-525)

### JR-ML-WS-047 — Cascor command_id echo in control responses for per-command correlation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 821-915)

### JR-ML-SEC-073 — Cascor must enforce per-IP WebSocket connection limit (default 5) to mitigate connection exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 180-210)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 774-798)

**Detail**:

WebSocketManager.__init__: self._per_ip_counts: Dict[str, int] = {}, reuse self._lock.
In connect(): before accept(), under async with self._lock: increment and check against ws_max_connections_per_ip.
Increment must happen before accept() (fail-closed).
In disconnect(): decrement in finally block to handle exceptions.
Default 5; configurable via JUNIPER_WS_MAX_CONNECTIONS_PER_IP.
Rejection: code 1013 (Try Again Later).

**Notes**:

M-SEC-04 (P1), IMPL-SEC-05..09. RISK-07 mitigation. Phase B-pre (Day 6).

### JR-ML-WS-048 — Cascor Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 128-240)

**Detail**:

10 commits: `messages.py` adds optional `seq: Optional[int]` on every envelope builder.
`manager.py` adds: `server_instance_id: str = uuid4()`, `server_start_time: float`, `_next_seq: int`, 
`_seq_lock: asyncio.Lock`, `_replay_buffer: deque` with `maxlen=Settings.ws_replay_buffer_size` (default 1024).
`connect()` sends `connection_established` with `server_instance_id`, `server_start_time`, `replay_buffer_capacity`.
`_send_json()` wraps in `asyncio.wait_for(..., timeout=0.5)` (GAP-WS-07 quick-fix).
`replay_since(last_seq)` helper + `ReplayOutOfRange` exception.
`training_stream.py` adds `_pending_connections: set`, two-phase registration, `promote_to_active()`.
`/ws/training` handles `resume` frame (5 s timeout) → `resume_ok` or `resume_failed`.
Server restart detected via `server_instance_id` mismatch. One-resume-per-connection rule enforced (second → close 1003).
`/api/v1/training/status` REST returns `snapshot_seq` + `server_instance_id` atomically under `_seq_lock`.
Lifecycle manager: replace throttle with debounced coalescer; terminal transitions bypass throttle (GAP-WS-21 fix).
`broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29 fix).
`/ws/control` returns protocol-error envelopes; echoes `command_id`; **NO seq** (D-03).
CHANGELOG + `docs/websocket_protocol.md` update.

**Design**:

Additive-field design. Existing clients ignoring seq keep working. Resume handler with 5 s timeout; 
one-resume guard prevents replay amplification. Atomic snapshot_seq under seq_lock prevents torn reads.

**Notes**:

Parallel with Phase A-SDK. Entry: cascor main clean, GAP-WS-19 verified. Exit: 20 tests pass, 
seq monotonic in staging, 24h soak zero gaps. Rollback: git revert (15 min TTF).

### JR-ML-PERF-004 — CasCor remote workers must maintain zero regression in local-only throughput and limit remote overhead to < 5% of task execution.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 361-369)

**Detail**:

PR-2: Zero regression in local-only throughput. PR-3: Remote overhead < 5% task time.

### JR-ML-PERF-005 — Cascor WebSocket send must timeout at 0.5s to prevent indefinite client stalls during backpressure.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 286-292)

**Detail**:

Wrap existing await websocket.send_json(message) in asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds).
Default ws_send_timeout_seconds = 0.5 in Settings (range gt=0.0, le=5.0).
On asyncio.TimeoutError / WebSocketDisconnect, log INFO and return False so caller prunes.
Quick-fix mitigation for RISK-04 in Phase A-server (Day 2, commit 3).
Phase E may upgrade to full pump-task backpressure if production telemetry shows RISK-04/11 triggering.

**Notes**:

RISK-04 quick-fix. Phase E (Day 12) full backpressure deferred per R0-03 §7.2 unless production data warrants.

### JR-ML-WS-049 — CascorControlStream.set_params default timeout must be 1.0s (not 5.0s) to prevent visible UI hang.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 1-50)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1482-1492)

**Detail**:

Disagreement D2: R0-04 §12.1 (1.0s) vs arch doc §7.1 (5.0s).
Runbook picks 1.0s (R0-04 wins). Matches GAP-WS-32 per-command table; 5s slider hang is visibly bad.
Callers override explicitly if needed.

**Notes**:

Disagreement D2 per R1-04 §14. Rationale: user experience during parameter adjustment.

### JR-ML-WS-050 — CascorControlStream.set_params(params, *, timeout=1.0, command_id=None) -> dict.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 217-217)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-TRAIN-029 — CCC-01: Wire-format schema evolution — strictly additive, no field rename/retype/remove; rollout state matrix.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 59-146)

**Detail**:

Wire format is additive-only. Every field added in Phase 0-cascor (seq, emitted_at_monotonic, replay_buffer_capacity, server_instance_id)
is present but may be ignored by older clients. No field is renamed, retyped, or removed.
Rollout state matrix documents per-phase per-endpoint compatibility: which fields are present,
which are optional, which old clients tolerate.
Acceptance criteria: rollout doc completed, PR contains state matrix, no surprises in cross-repo CI.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Cross-cutting. Applies to all phases touching wire. Dedup with R3-03.

### JR-ML-OBS-036 — CCC-02: Observability stack — metrics/logging/tracing/dashboards/alerts before behavior, load-bearing SLO binding.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 160-258)

**Detail**:

Principle: observability precedes behavior. Every Phase ships metrics, dashboards, alerts, runbooks **before** the feature flips.
Metrics naming convention: `{repo}_ws_{metric}` for WebSocket, `{repo}_training_{metric}` for training control.
Labels: `endpoint` (path), `event_type` (for audit), `transport` (rest/ws), `policy` (backpressure).
Dashboard panels: "WebSocket health" (latency p50/p95/p99), "Polling bandwidth" trend, "Connection state", "Rate limits",
"Audit events", "Backpressure drops".
Alerts: `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap` (ticket), `WSPendingConnectionStuck` (ticket), `WSSlowBroadcastP95` (ticket),
`CSRFFailureRate` (ticket), `AuditLogRotationFailure` (ticket).
Load-bearing SLO: P0 success metric `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Binding after >=1 week production data.
Acceptance: all metrics present before PR merge, histogram test-fired in staging, gauge queries return non-zero.

**Notes**:

Cross-cutting. Principle from R1-02 principle 1. Dedup with R3-03.

### JR-ML-ARCH-159 — CCC-03: Kill-switch architecture — every phase has config-only reversal, MTTR <=5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 261-340)

**Detail**:

Every behavior change has a kill switch: feature flag (boolean), config enum, or env var.
MTTR (mean time to recovery) <=5 min: flip flag + restart, no code revert needed.
Every switch CI-tested: PR includes test that toggles switch, asserts behavior changes.
Every switch staging-drilled: canary in staging verifies toggle works before production deploy.
Examples: `enable_browser_ws_bridge` (5 min toggle), `use_websocket_set_params` (2 min toggle), `ws_backpressure_policy` (env var),
`ws_allowed_origins` (env list), `disable_ws_bridge` (permanent kill, always available).
Acceptance: if kill switch fails to produce expected metric delta within 60 s, migration halts for re-planning.

**Notes**:

Cross-cutting. Principle from R1-02 principle 2. Dedup with R3-03.

### JR-ML-DOC-001 — CHANGELOG.md + docs/websocket_protocol.md additive field contract section.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 121-121)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-API-020 — Client Packages (PyPI).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 67-76)

**Detail**:

| `juniper-data-client`   | 0.3.0   | HTTP client for JuniperData API          |

### JR-ML-OBS-037 — _client_latency_ms private field on returned dict.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 223-223)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-TEST-010 — Comprehensive testing strategy for WebSocket migration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_validation.md` (lines 1-68)

### JR-ML-ARCH-160 — CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4216-4231)

### JR-ML-ARCH-161 — CONC-02: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4234-4249)

### JR-ML-OBS-038 — CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4252-4275)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-162 — CONC-04: ALL Storage Operations Block Async Event Loop (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4278-4301)

### JR-ML-ARCH-163 — CONC-07: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4304-4319)

### JR-ML-ARCH-164 — CONC-08: `is_running` Reads/Writes Inconsistently Locked.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4322-4336)

### JR-ML-ARCH-165 — CONC-09: Fire-and-Forget `asyncio.create_task` Without Stored Reference.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4339-4353)

### JR-ML-ARCH-166 — CONC-10: Health Monitor Deregister/Assign Race Window.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4356-4370)

### JR-ML-ARCH-167 — CONC-12: `record_access` TOCTOU on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4373-4388)

### JR-ML-WS-051 — Constitution: 42+ settled positions on wire format, protocol behavior, security, phase order, observability, effort.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 112-242)

**Detail**:

C-01: Correlation field `command_id`, NOT `request_id`. C-02: `command_response` NO seq; `/ws/control` no replay buffer.
C-03: `set_params` default timeout 1.0 s (not 5.0 s). C-04: SDK fails fast on disconnect, no reconnect queue, no retries.
C-05: Replay buffer 1024 entries, env-configurable. C-06: `server_instance_id` programmatic key, `server_start_time` advisory.
C-07: `replay_buffer_capacity` on `connection_established`. C-08: Two-phase registration via `_pending_connections`.
C-09: Cascor `SetParamsRequest` `extra="forbid"`; canopy routes unclassified keys to REST with WARN.
C-10: Adapter→cascor HMAC first-frame (NOT `X-Juniper-Role` header). C-11: GAP-WS-19 resolved on main, regression test only.
C-12/C-13: Phase 0-cascor carve-out from Phase B; Phase B-pre splits 0-cascor + B-pre-b.
C-14: Phase B two-flag design (`enable_browser_ws_bridge` + `disable_ws_bridge`). C-15: Phase E default `drop_oldest_progress_only`.
C-16: rAF coalescer scaffolded disabled. C-17: REST fallback 1 Hz during disconnect. C-18: `ws-metrics-buffer` = `{events, gen, last_drain_ms}`.
C-19: Ring bound in handler, not drain callback. C-20: GAP-WS-24 splits 24a (browser) + 24b (canopy endpoint).
C-21: NetworkVisualizer minimum wire Phase B, deep deferred if cytoscape. C-22: `_normalize_metric` dual format preserved, CODEOWNERS Phase H.
C-23: REST endpoints preserved FOREVER, no deprecation. C-24: Per-IP cap 5, single-bucket rate limit 10 cmd/s.
C-25: One-resume-per-connection rule. C-26: Per-command HMAC deferred. C-27: `ws_security_enabled=True` (positive sense).
C-28: Phase C flag `use_websocket_set_params=False` default, 6 hard flip gates.
C-29: Debounce in Dash callback (250 ms), not SDK. C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` REFUSED (non-switch).
C-31: Multi-tenant isolation deferred. C-32: Chromium-only Playwright v1. C-33: Per-command HMAC deferred.
C-34: Contract-test pytest marker. C-35: Latency tests recording-only CI, strict local-only. C-36: Total 15.75 eng days / ~4.5 weeks.
C-37: P0 metric = canopy_rest_polling_bytes_per_sec >=90% reduction. C-38: Observability-before-behavior. C-39: Kill-switch MTTR <=5 min, CI-tested.
C-40: Wire format strictly additive. C-41: `emitted_at_monotonic` on every `/ws/training` broadcast.
C-42: Error-budget burn-rate operationally binding.
Plus D-NN decision mapping, effort table, feature flag inventory.

**Notes**:

[v2 ARCH→WS re-bucket] Source of truth. All items settled; re-litigation via formal decision change only. Used by Phase 0-cascor through Phase I.

### JR-ML-ARCH-168 — Correctness: no seq gaps.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-TRAIN-030 — Correctness: no state loss.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-OBS-039 — Create register_or_reuse and register_fresh helpers in juniper-observability to centralize idempotent prometheus_client collector construction, eliminating ~10 copy-pasted implementations across consumer repos.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md` (lines 1-50)

**Detail**:

Two helpers needed:
1. register_or_reuse(factory, name, *args, **kwargs) - adopts existing collectors
2. register_fresh(factory, name, *args, **kwargs) - unregisters and recreates

Live in juniper_observability/prometheus_helpers.py, re-exported from __init__.
~150 lines code + docstrings + unit tests. Target: juniper-data, juniper-canopy, juniper-cascor-client, juniper-cascor.

**Design**:

Constraints:
- Production path zero-overhead
- Test-isolation honesty (predictable behavior)
- Optional-dependency friendly
- No new private-API surface beyond existing inline guards
- Migration is opt-in

API signature:
def register_or_reuse(factory: Callable, name: str, *args, **kwargs) -> T
def register_fresh(factory: Callable, name: str, *args, **kwargs) -> T

**Notes**:

Part of OBS-COLLECTOR-IDEMPOTENT track. Cascor has drop+recreate; 2026-05 PRs use adopt-existing. This centralizes into single canonical form.

### JR-ML-ARCH-169 — D-1: Correlation field name (D-02).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 118-119)

### JR-ML-TRAIN-031 — D-2: Phase 0-cascor carve-out (D-11).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 119-120)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-170 — D-3: Two-flag browser bridge (D-17 + D-18).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 120-121)

### JR-ML-ARCH-171 — D-4: REST paths preserved forever (D-21, D-54, D-56).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 121-122)

### JR-ML-SEC-074 — D-5: Positive-sense security flag (D-10).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 122-123)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-PERF-006 — D-6: Phase E backpressure default (D-19).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 123-124)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-ARCH-172 — D-7: Phase C flag-flip criteria (D-48).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 124-125)

### JR-ML-ARCH-173 — D-8: Kill-switch MTTR tested (D-53).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 125-126)

### JR-ML-PERF-007 — D-**Browser memory leak** (RISK-10): Medium-High.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 132-133)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-TRAIN-032 — D-**Cascor crash mid-broadcast** (RISK-14): Low.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 135-136)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-174 — D-Correctness: no seq gaps: `cascor_ws_seq_gap_detected_total`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-TRAIN-033 — D-Correctness: no state loss: `cascor_ws_dropped_messages_total{type="state"}`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-OBS-040 — D-Criterion: Metric.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-WS-052 — D-**CSWSH attack** (RISK-15): High.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 131-132)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-OBS-041 — D-**Dual metric format breakage** (RISK-01): High.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 134-135)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-175 — D-Observability: full pipe: All canonical metrics present on `/metrics`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-176 — D-**P0: polling eliminated**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-177 — D-Recovery: kill switches work: Every switch flipped in staging.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-ARCH-178 — D-Risk: Severity.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 129-130)

### JR-ML-WS-053 — D-Security: CSWSH closed: `canopy_ws_origin_rejected_total` page alert functional.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-TRAIN-034 — D-**Silent data loss** (RISK-11): High (low likelihood).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 133-134)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-179 — D: `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 359-360)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-180 — D: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 360-361)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-API-021 — Define four snapshot endpoints: restore (explore), replay (watch metrics fresh), resume (continue), retrain (new training).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CANOPY_CASCOR_SNAPSHOT_LOAD-TYPES.md` (lines 18-76)

### JR-ML-ARCH-181 — `disable_ws_auto_reconnect`: F.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 317-318)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-182 — `disable_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 308-309)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-183 — `disable_ws_control_endpoint`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 313-314)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-WS-054 — disconnect() cancels recv task, drains pending with set_exception(JuniperCascorConnectionError).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 220-220)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-ARCH-184 — E: `JUNIPER_WS_BACKPRESSURE_POLICY=block`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 361-362)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-035 — Effort bounds and calendar: 15.75 expected eng days (~4.5 weeks calendar) with soak windows.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 76-94)

**Detail**:

Effort table (optimistic/expected/pessimistic): Phase 0-cascor 1.5/2.0/3.0, A-SDK 0.5/1.0/1.5, B-pre-a 0.5/1.0/1.5,
B 3.0/4.0/5.0, B-pre-b 1.0/1.5/2.0, C 1.5/2.0/3.0, D 0.75/1.0/1.5, E 0.75/1.0/1.5, F 0.25/0.5/1.0,
G 0.25/0.5/0.75, H 0.5/1.0/1.5, I 0.1/0.25/0.5. Total 10.6/15.75/22.25 eng days.
Calendar translation: 15.75 days × single-dev lane = ~3 weeks one-person, or ~4.5 weeks with 48-72 h soak windows.
Minimum-viable carveout (P0 only): ~7 days (Phase A-SDK + 0-cascor + B-pre-a + B + I).
Soak windows: 0-cascor 72 h, Phase B 72 h, B-pre-b 48 h, Phase C canary >=7 days.
Phase dependency graph: A-SDK || 0-cascor || B-pre-a → B || B-pre-b → D; C parallel with B/D; E/F/G/H follow.

**Notes**:

[v2 ARCH→TRAIN re-bucket] Risks: 0-cascor async race (+risk), A-SDK correlation map iteration (+risk), B-pre-a audit logger name collision (+risk),
B NetworkVisualizer Plotly (+1 day), B-pre-b session middleware absent (+0.5 day), C concurrent-correlation bugs (+risk),
D orphaned-command UI state (+risk), E queue tuning (+risk), F reconnect-cap lift debated.

### JR-ML-ARCH-185 — `enable_browser_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 307-308)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-186 — `enable_raf_coalescer`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 309-310)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-187 — `enable_ws_control_buttons`: D.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 311-312)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-188 — ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4412-4426)

### JR-ML-TRAIN-036 — ERR-02: `response.json()` Unguarded in cascor-client `_request()`.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4429-4443)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-037 — ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor).

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4446-4460)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-189 — ERR-07: `raise HTTPException` Without `from e` — Broad Except Masks Programming Errors (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4463-4477)

### JR-ML-ARCH-190 — ERR-08: `str(e)` in Batch Create Error Response — Information Disclosure (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4480-4494)

### JR-ML-ARCH-191 — ERR-09: `remote_client_0.process_tasks()` Catches All Exceptions, Only Prints.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4497-4511)

### JR-ML-ARCH-192 — ERR-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4514-4529)

### JR-ML-ARCH-193 — ERR-13: `arc_agi` Generator Silent Fallback on Any Exception.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4532-4546)

### JR-ML-ARCH-194 — ERR-14: `CascorMetricsStream.stream()` Swallows ConnectionClosed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4549-4571)

### JR-ML-OPS-003 — Every phase must have kill-switch feature flag; TTF (time to fallback) documented.

**Status**: proposed  **Priority**: P1  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-02_risk_minimized_safety_first.md` (lines 29-47)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1044-1046)

**Detail**:

Phase A: no feature flag (additive SDK method, cannot be disabled).
Phase A-server: no feature flag (seq is infrastructure, not a feature).
Phase B: disable_ws_bridge=True → forces REST polling. TTF ~2 min.
Phase C: use_websocket_set_params=False (default) → falls back to REST. TTF ~2 min.
Phase D: disable_ws_control_endpoint=True → buttons force REST. TTF ~5 min.
Phase B-pre auth: ws_security_enabled=False (or JUNIPER_CANOPY_DISABLE_WS_AUTH=true per naming debate in §14 D5). TTF ~2 min. Local dev only—never set in prod.

**Notes**:

Kill switches are non-optional per R1-02 §1.2 principle #2. All documented in day rollback sections.

### JR-ML-SEC-075 — Excessive f-string tensor interpolation logging in hot paths.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 877-895)

### JR-ML-SEC-076 — Execute comprehensive security audit of Juniper ecosystem with threat modeling and vulnerability assessment.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECURITY_AUDIT_PLAN.md` (lines 1-100)

**Notes**:

Multi-phase security program.

### JR-ML-ARCH-195 — F: `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 362-363)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-055 — Fail-fast: no SDK retries on timeout (C-04).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 222-222)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-TRAIN-038 — Fix BUG-CC-12: replace yaml.safe_load with torch.load or safetensors in cascor utils.py.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ROADMAP_AUDIT_2026-05-05.md` (lines 71-77)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-PERF-008 — Fix BUG-JD-10: wrap sync storage I/O in asyncio.to_thread in juniper-data batch_update_tags.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ROADMAP_AUDIT_2026-05-05.md` (lines 79-84)

### JR-ML-TRAIN-039 — Fix CasCor demo training error with identified root cause and remediation.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN-OLD.md` (lines 1-100)

**Notes**:

Legacy plan version; check for updates in primary plan.

### JR-ML-SEC-077 — Fix critical security vulnerabilities in CasCor multiprocessing: hardcoded authkey, unpickler, queue sizing, API key comparison.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 809-850)

**Detail**:

Phase 1a: (1) Remove hardcoded PROJECT_MODEL_AUTHKEY, (2) Add RestrictedUnpickler for result queue, (3) Add queue maxsize, (4) Result bounds checking, (5) Use hmac.compare_digest for API key validation.

### JR-ML-TEST-011 — Fix cross-project regression issues with remediation plan.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CROSS_PROJECT_REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

**Notes**:

Active investigation status.

### JR-ML-DEP-011 — Fix image build bugs: observability images not inheriting base image labels correctly.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/IMAGE_BUILD_BUGS_2026-05-10.md` (lines 1-50)

### JR-ML-SEC-078 — Fix Logic Validation.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 886-895)

**Detail**:

| OI-1 | **VALID** | `dash.no_update` confirmed as correct Dash sentinel; already used 26 times in `dashboard_manager.py` |

### JR-ML-TEST-012 — Fix regressions identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-100)

### JR-ML-TRAIN-040 — Fix tensor dimension mismatch issues in CasCor batch processing pipeline.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_TENSOR_DIMENSION_MISMATCH_ANALYSIS.md` (lines 1-100)

**Notes**:

Analysis-based remediation for candidate training.

### JR-ML-TOOL-001 — Fix wake_the_claude.bash session validation failures.

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/wake_the_claude_failure_analysis.md` (lines 1-100)

**Notes**:

Development tooling issue.

### JR-ML-ARCH-196 — Flag: Phase.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 305-306)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-WS-056 — GAP-WS-01: and the subsequent canopy-side adapter refactor.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1338-1342)

### JR-ML-WS-057 — GAP-WS-01: through GAP-WS-33), ranging from P0 (security, auth, replay protocol, REST polling bandwid.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 149-153)

### JR-ML-WS-058 — GAP-WS-01: — `juniper-cascor-client` lacks WebSocket `set_params`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1236-1240)

### JR-ML-WS-059 — GAP-WS-02: through GAP-WS-05) | Playwright e2e: `test_browser_receives_metrics_event`, `test_chart_up.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1784-1788)

### JR-ML-WS-060 — GAP-WS-02: — Browser-side `cascorWS` / `cascorControlWS` are dead code.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1249-1253)

### JR-ML-WS-061 — GAP-WS-03: — Parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1257-1261)

### JR-ML-WS-062 — GAP-WS-04: note about background tab throttling.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2003-2007)

### JR-ML-WS-063 — GAP-WS-04: — `ws-metrics-buffer` store never populated.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1265-1269)

### JR-ML-WS-064 — GAP-WS-05: — No clientside callback drains WS stores into chart inputs.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1273-1277)

### JR-ML-WS-065 — GAP-WS-06: — Training control buttons use REST POST instead of WebSocket.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1289-1293)

### JR-ML-WS-066 — GAP-WS-07: (backpressure) sooner. **Decision needed before Phase E.**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2015-2019)

### JR-ML-WS-067 — GAP-WS-07: backpressure with per-send timeout) lands before or together with Phase B (GAP-WS-13 seque.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1170-1174)

### JR-ML-WS-068 — GAP-WS-07: — No backpressure / slow client handling in cascor `WebSocketManager`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1297-1301)

### JR-ML-WS-069 — GAP-WS-08: — No end-to-end browser test for the WebSocket path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1307-1311)

### JR-ML-WS-070 — GAP-WS-09: integration tests that exercise the failure modes.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1437-1441)

### JR-ML-WS-071 — GAP-WS-09: — No cascor-side integration test for `set_params` on `/ws/control`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1320-1324)

### JR-ML-WS-072 — GAP-WS-10: + the canopy adapter refactor + GAP-WS-32 (per-command timeouts).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1855-1859)

### JR-ML-WS-073 — GAP-WS-10: — No canopy-side integration test for `set_params` round-trip.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1332-1336)

### JR-ML-WS-074 — GAP-WS-11: + §4.4 phased plan.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1923-1927)

### JR-ML-WS-075 — GAP-WS-11: Phase H).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1532-1536)

### JR-ML-WS-076 — GAP-WS-11: — Canopy `_normalize_metric` dual format is undocumented for external consumers.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1340-1344)

### JR-ML-WS-077 — GAP-WS-12: — No WebSocket heartbeat / ping-pong reciprocity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1348-1352)

### JR-ML-WS-078 — GAP-WS-13: (P1) — Lossless reconnect via sequence numbers and replay buffer.** Required components:.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1142-1146)

### JR-ML-WS-079 — GAP-WS-13: (sequence numbers + replay), GAP-WS-14 (Plotly extendTraces), GAP-WS-15 (rAF coalescing),.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1829-1833)

### JR-ML-WS-080 — GAP-WS-13: a server that doesn't recognize the `resume` command will respond with `command_response`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1214-1218)

### JR-ML-WS-081 — GAP-WS-13: Lossless Reconnect via Sequence Numbers and Replay Buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2177-2188)

### JR-ML-WS-082 — GAP-WS-13: reconnect+replay protocol — `server_start_time` change forces all clients to do a full RES.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2005-2009)

### JR-ML-WS-083 — GAP-WS-13: sequence numbers land). Currently there is no mechanism to reject an outdated client. **De.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2023-2027)

### JR-ML-WS-084 — GAP-WS-13: — Lossless reconnect via sequence numbers and replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1356-1360)

### JR-ML-WS-085 — GAP-WS-14: (`extendTraces`), this keeps the per-frame cost under 17 ms.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1377-1381)

### JR-ML-WS-086 — GAP-WS-14: above. Kept here for reference link integrity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1442-1446)

### JR-ML-WS-087 — GAP-WS-14: mandates `Plotly.extendTraces(maxPoints=5000)`; ring buffer in `ws-metrics-buffer` (last 1.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2001-2005)

### JR-ML-WS-088 — GAP-WS-14: Plotly `extendTraces` with `maxPoints` Limit.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2146-2160)

### JR-ML-WS-089 — GAP-WS-14: — Plotly chart updates must use `extendTraces` with `maxPoints`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1364-1368)

### JR-ML-WS-090 — GAP-WS-15: Browser-Side rAF Coalescing for 50Hz Candidate Events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2163-2174)

### JR-ML-WS-091 — GAP-WS-15: — Browser-side rAF coalescing for high-frequency events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1372-1376)

### JR-ML-WS-092 — GAP-WS-16: `/api/metrics/history` Polling Bandwidth Bomb (~3 MB/s).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2129-2143)

### JR-ML-WS-093 — GAP-WS-16: — `/api/metrics/history` polling is the bandwidth bomb (P0 motivator).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1380-1384)

### JR-ML-WS-094 — GAP-WS-17: — `permessage-deflate` compression not configured.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1388-1392)

### JR-ML-WS-095 — GAP-WS-18: chunking or REST fallback; document the threshold; add a server-side size guard.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2007-2011)

### JR-ML-WS-096 — GAP-WS-18: Topology Message >64KB Causes Connection Teardown.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2219-2238)

### JR-ML-WS-097 — GAP-WS-18: — Topology message can exceed 64 KB silently.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1396-1400)

### JR-ML-WS-098 — GAP-WS-19: in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 229-233)

### JR-ML-WS-099 — GAP-WS-19: — `close_all()` does not hold `_lock` (CR-025 partial).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1404-1408)

### JR-ML-WS-100 — GAP-WS-20: (P3)**: normalize bidirectional envelope to use `{type, timestamp, data}` everywhere. Trac.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 482-486)

### JR-ML-WS-101 — GAP-WS-20: — Bidirectional envelope asymmetry.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1412-1416)

### JR-ML-WS-102 — GAP-WS-21: (P1)** in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 555-559)

### JR-ML-WS-103 — GAP-WS-21: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2241-2246)

### JR-ML-WS-104 — GAP-WS-21: debouncer rewrite) AND state event rate goes >5 Hz.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1528-1532)

### JR-ML-WS-105 — GAP-WS-21: — 1 Hz state throttle drops terminal transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1420-1424)

### JR-ML-WS-106 — GAP-WS-22: (P2)** in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 745-749)

### JR-ML-WS-107 — GAP-WS-22: (protocol error responses).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1908-1912)

### JR-ML-WS-108 — GAP-WS-22: — Protocol error responses not specified.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1431-1435)

### JR-ML-WS-109 — GAP-WS-23: (P1)** in §7: clientside chart updates must use `Plotly.extendTraces()` with `maxPoints` p.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1022-1026)

### JR-ML-WS-110 — GAP-WS-23: — `Plotly.extendTraces` with `maxPoints` (alias of GAP-WS-14).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1439-1443)

### JR-ML-WS-111 — GAP-WS-24: (P2)** in §7. Phase B includes the instrumentation; Phase C+ uses the data to validate (or.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1037-1041)

### JR-ML-WS-112 — GAP-WS-24: — Production WebSocket latency instrumentation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1444-1448)

### JR-ML-WS-113 — GAP-WS-25: (polling toggle).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1385-1389)

### JR-ML-WS-114 — GAP-WS-25: polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1386-1390)

### JR-ML-WS-115 — GAP-WS-25: WebSocket-Health-Aware Polling Toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2191-2202)

### JR-ML-WS-116 — GAP-WS-25: — WebSocket-health-aware polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1452-1456)

### JR-ML-WS-117 — GAP-WS-26: Visible Connection Status Indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2205-2216)

### JR-ML-WS-118 — GAP-WS-26: — Visible connection status indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1460-1464)

### JR-ML-WS-119 — GAP-WS-27: — Per-IP connection caps and DoS protection.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1468-1472)

### JR-ML-WS-120 — GAP-WS-28: Multi-Key `update_params` Torn-Write Race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2249-2260)

### JR-ML-WS-121 — GAP-WS-28: — Multi-key `update_params` torn-write race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1476-1480)

### JR-ML-WS-122 — GAP-WS-29: for the exception-handling path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1180-1184)

### JR-ML-WS-123 — GAP-WS-29: — `broadcast_from_thread` discards future exceptions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1484-1488)

### JR-ML-WS-124 — GAP-WS-30: — Reconnect backoff has no jitter (thundering herd risk).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1492-1496)

### JR-ML-WS-125 — GAP-WS-31: Unbounded Reconnect Cap — Stops After 10.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2263-2274)

### JR-ML-WS-126 — GAP-WS-31: — Unbounded reconnect attempts cap (currently capped at 10).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1500-1504)

### JR-ML-WS-127 — GAP-WS-32: per-command correlation IDs + `pending verification` state pending matching `command_respo.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2004-2008)

### JR-ML-WS-128 — GAP-WS-32: Per-Command Timeouts and Orphaned-Command Resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2277-2288)

### JR-ML-WS-129 — GAP-WS-32: — Per-command timeouts and orphaned-command resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1508-1512)

### JR-ML-WS-130 — GAP-WS-33: — Demo mode failure visibility.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1516-1520)

### JR-ML-ARCH-197 — H: `git revert` P16.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 363-364)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-198 — I: `git revert` cache-bust commit.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 364-365)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-199 — ID: Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 373-374)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-TRAIN-041 — Implement root cause fix for CasCor training stall based on proposal analysis.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md` (lines 1-100)

**Notes**:

Blocks training completion.

### JR-ML-SEC-079 — Incomplete implementation of `max_epochs` and `max_iterations` as separate training limits — broken data flow across cascor and canopy.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 60-160)

**Detail**:

Option A, executed as two coordinated PRs (cascor first, then canopy). The canopy side is primarily wiring an existing UI control to an existing param map — the UI already exists and the user already expects it to work. The cascor side is the larger change but follows established patterns for existing fields like `epochs_max`.

Both repos should be updated in the same development cycle to avoid a window where the field exists in cascor but canopy can't drive it.

### JR-ML-OBS-042 — Issue Remediations, Section 17.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_a_security_concurrency_error.md` (lines 297-347)

**Detail**:

#### CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager

### JR-ML-SEC-080 — Issue Remediations, Section 19.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 607-657)

**Detail**:

#### CI-01: cascor-client CI Doesn't Test Python 3.14

### JR-ML-DEP-012 — juniper-deploy P0: define SECRETS_DIR and SECRETS_FILES variables in Makefile.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/RELEASE_DEVELOPMENT_ROADMAP_2026-04-08.md` (lines 47-60)

### JR-ML-WS-131 — lifecycle/manager.py state coalescer; terminal transitions bypass throttle (GAP-WS-21).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 118-118)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TEST-013 — Make sentry-sdk a hard runtime dependency and remove importorskip guards in tests.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 61-65)

**Detail**:

R3.4 Resolution (b): Move sentry-sdk to hard runtime dep across cascor/canopy/data. Drop importorskip guards so SEC-15 before_send hook tests run every CI run.

**Notes**:

Security-critical test coverage.

### JR-ML-WS-132 — manager.py gains server_instance_id, server_start_time, _next_seq, _seq_lock, _replay_buffer, _assign_seq_and_append().

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 113-113)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-SEC-081 — Medium Priority.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 364-375)

**Detail**:

| Task 2 Ph1: Metadata-only graceful handling  | DASHBOARD_AUGMENTATION_PLAN       | Dataset tab metadata-only display for service mode

### JR-ML-WS-133 — messages.py optional seq + emitted_at_monotonic field on every builder.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 112-112)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-134 — MISSING: - PARTIAL — feature is partially implemented; some paths work, others don't.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 60-61)

### JR-ML-WS-135 — MISSING: Status: server-side PRESENT (cascor accepts and handles the command); client-side MISSING.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 729-730)

### JR-ML-ARCH-200 — Observability: full pipe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-WS-136 — Phase 0-cascor: Cascor /ws/training emits monotonic seq, advertises server_instance_id+replay_buffer_capacity, supports resume, fixes state coalescer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-91)

**Notes**:

Phase 0-cascor major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-012 — Phase 1 (canopy-only) — COMPLETE.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 160-168)

**Detail**:

| Fix pre-existing test failures (5 in `test_response_normalization.py`) | ✅ Fixed       | Backlog Sprint 1 |

### JR-ML-API-022 — Phase 2: Backend API.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 528-537)

**Detail**:

1. Update `/api/set_params` endpoint to accept new keys

### JR-ML-ARCH-201 — Phase 3:.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 130-203)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 129-202)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 68-104)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 156-230)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-TRAIN-042 — Phase 3: Layout.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 537-544)

**Detail**:

1. Replace Training Parameters card with Meta Parameters card

### JR-ML-OBS-043 — Phase 6: Finalize.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 563-607)

**Detail**:

1. Run linters (black, isort, flake8)

### JR-ML-WS-137 — Phase A-SDK: `CascorControlStream.set_params(params, timeout=1.0, command_id=...)` ships to PyPI.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 243-331)
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-92)

**Detail**:

New SDK method sends `set_params` command over `/ws/control`, returns response matched via `command_id`.
Generates `command_id = uuid4()` if absent. Raises `JuniperCascorTimeoutError` on timeout (default 1.0 s),
`JuniperCascorConnectionError` on disconnect, `JuniperCascorError` on server error.
Correlation map: `_pending: Dict[str, asyncio.Future]` keyed by `command_id`.
Background `_recv_task` started on first call; cancels cleanly on `close()`, sets exceptions on pending futures.
Caller cancellation safe: removes map entry in `finally`, no memory leak.
`_client_latency_ms` field on response (SDK-private).
No retries, no reconnect queue. Caller decides retry logic.
Pydantic `SetParamsResponse` with `extra="allow"` (additive).
10 tests: happy path, timeout, concurrent correlation, caller cancellation, fails-fast-on-disconnect, no-retry, error response, bounded correlation map (256), recv-task exception propagation.
PyPI publish; `juniper-ml/pyproject.toml` optional-extras pin bumped (follow-up PR).

**Design**:

Correlation map with bounded growth (256 entries). Background recv task handles message routing.
Timeout enforced client-side (no retries). SDK-private latency instrumentation.

**Notes**:

Parallel with Phase 0-cascor. Loose entry gate (SDK ships independent of cascor). Gated by 
`test_set_params_caller_cancellation_cleans_correlation_map` passing. Rollback: PyPI yank or flag-off.

---

Phase A-SDK major milestone from R3-03 Phase index (§2); orchestrates implementation effort

*Merged from 2 extraction candidates (slices: 3b-2, ml-B).*

### JR-ML-SEC-082 — Phase B-pre-a: Origin allowlist, per-IP cap, frame-size cap, audit logger skeleton on `/ws/training`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 334-430)

**Detail**:

Cascor side: Origin validation (M-SEC-01), empty list = fail-closed, case-insensitive host, null origin rejected.
Per-IP connection cap = 5 default, configurable. `_per_ip_counts` dict under lock.
Frame size limit: `max_size=4096` on receive_* calls. Canopy side: duplicate Origin helper (copy, not import).
`Settings.allowed_origins` with localhost/127.0.0.1 defaults. `max_size=4096` on canopy's `/ws/training`.
Audit logger skeleton: `canopy.audit` logger (new module), JSON formatter, TimedRotatingFileHandler daily rotation,
30-day retention, scrub allowlist (no raw payloads). No Prometheus counters yet (land in Phase B).
"One resume per connection" rule: `resume_consumed: bool` per connection, second resume closes 1003.
GAP-WS-19 regression test: `test_close_all_holds_lock`.
Tests: frame size limit 1009, per-IP 6th rejected 1013, origin allowlist matrix, audit log format + rotation, empty allowlist rejects all, second resume closes 1003.
Observability: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` (hashed),
`canopy_ws_oversized_frame_rejected_total{endpoint}`, `canopy_ws_per_ip_cap_rejected_total{endpoint}`,
`canopy_audit_events_total{event_type}`.

**Design**:

Two-PR sequence, cascor→canopy. M-SEC-03 (frame size) + M-SEC-04 (per-IP cap) + M-SEC-07 (audit skeleton).
Origin allowlist on `/ws/training` specifically (read-path). Gates Phase B only.

**Notes**:

Parallel with Phase 0-cascor and A-SDK. Exit gate: empty allowlist = fail-closed (HALT if fail-open).
Rollback: env flags (`JUNIPER_WS_ALLOWED_ORIGINS='*'` ignored by parser; instead use high cap `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=1000`).

### JR-ML-SEC-083 — Phase B-pre-a: Origin on /ws/training, size caps, per-IP cap, idle timeout, audit-logger skeleton.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-93)

**Notes**:

Phase B-pre-a major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-084 — Phase B-pre-b: Origin on /ws/control, cookie session + CSRF first-frame, rate limit, idle timeout, adapter HMAC, audit Prom counters.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-95)

**Notes**:

Phase B-pre-b major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-085 — Phase B-pre-b: Origin on `/ws/control`, cookie+CSRF first-frame, rate limit, idle timeout, adapter HMAC, log injection escaping.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 597-699)

**Detail**:

Cookie session + CSRF (canopy): SessionMiddleware added (or reused if present).
`/api/csrf` endpoint returns CSRF token bound to session (constant-time comparable via `hmac.compare_digest`).
Dash template injects CSRF token via data attribute. `/ws/control` first frame must be `{type: "auth", csrf_token: "..."}` within 5 s;
invalid/absent/expired → close 1008. Cookie: `SameSite=Lax`, `HttpOnly`, `Secure` (prod).
M-SEC-06 opaque close: numeric codes only, no human-readable reasons.
Origin + rate limit (cascor): `/ws/control` validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`).
M-SEC-05 single-bucket rate limit: 10 cmd/s leaky bucket per-connection, 11th → close 1013.
M-SEC-10 idle timeout: >120 s idle → close 1008. Settings: `ws_idle_timeout_seconds = 120`.
Adapter auth: canopy computes `csrf_token = hmac(api_key.encode(), b"adapter-ws", sha256).hexdigest()` on connect.
First frame sent: `{type: "auth", csrf_token: <hmac>}`. Cascor derives same + compares with `hmac.compare_digest`.
Uniform code path (no `X-Juniper-Role` header special case).
M-SEC-11 adapter inbound validation: `cascor_service_adapter.py` wraps inbound with Pydantic `CascorServerFrame` (`extra="allow"`).
Malformed → log + increment `canopy_adapter_inbound_invalid_total` + continue.
M-SEC-07 extended log injection: audit logger escapes CRLF + tab in all logged strings (prevents log forgery).
Tests: CSRF required, binds to session constant-time, kill-switch works, Origin rejected, rate limit 11th cmd closes 1013,
idle timeout closes 1008, adapter sends HMAC on connect, inbound malformed logged+counted, CRLF injection escaped,
opaque close codes, session middleware exists, cascor rejects unknown params via extra="forbid".
Observability: `canopy_csrf_validation_failures_total`, `canopy_audit_events_total{event_type="csrf_failure"}`,
`cascor_ws_control_rate_limit_rejected_total`, `cascor_ws_control_idle_timeout_total`, `canopy_adapter_inbound_invalid_total`.

**Design**:

Two-PR sequence (cascor→canopy). M-SEC-01/01b (Origin) + M-SEC-02 (cookie+CSRF) + M-SEC-05 (rate limit) + M-SEC-10 (idle timeout) +
M-SEC-11 (adapter validation) + M-SEC-07 extended (log escaping). Gates Phase D (browser control buttons).
HMAC first-frame auth uniform with existing SDK auth pattern.

**Notes**:

Parallel with Phase B. Entry: Phase B in main. Merge order strict: P8→P9 (P8 must land first, P9's adapter path depends on P8's handler).
Exit: all tests green, manual Origin/CSRF/rate-limit probes work, SessionMiddleware detected, adapter handshake works, 48h soak.
Rollback: `JUNIPER_DISABLE_WS_AUTH=true` (existing flag, 2 min TTF). Dedup candidate with R3-03.

### JR-ML-UI-013 — Phase B: Browser bridge drains /ws/training into Dash store, Plotly.extendTraces updates, polling killed, GAP-WS-24a/b latency pipe.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-94)

**Notes**:

Phase B major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-138 — Phase C: Canopy adapter hot/cold split; hot→WS via command_id; unconditional REST fallback; flag-off default.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-96)

**Notes**:

Phase C major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-139 — Phase D: Browser start/stop/pause/resume/reset routed via /ws/control with REST fallback; per-command timeouts.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-97)

**Notes**:

Phase D major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-140 — Phase D: browser start/stop/pause/resume/reset training-control via `/ws/control` with REST fallback.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 792-864)

**Detail**:

Frontend: clientside callback on each button sends `{command: "start", command_id: uuid()}` (etc.) to `window.cascorControlWS` if WS connected;
REST POST if not. Per-command correlation map: send remembers `command_id`→button, response match updates button state.
Orphaned-command UI: no response within timeout (start=10s, others=2s) → fallback REST POST after small delay.
Badge status "pending" while awaiting WS ack.
Cascor-side: `/ws/control` routes `{command, command_id, ...}` to existing REST-POST handler, emits `command_response{command_id, status, error?}`.
Per-command timeout async dispatch: `asyncio.wait_for(..., timeout=<per-command>)`.
Command whitelist: start, stop, pause, resume, reset, set_params. Unknown → `{status: "error", code: "unknown_command"}`.
Per-command timeouts: start=10s (per source §7.32), stop/pause/resume/reset=2s, set_params=1s.
Tests: 9 entries. CSRF required (regression), start/stop/pause/resume happy path, per-command timeouts enforced,
unknown commands rejected, command_id echoed, orphaned commands fallback, fallback works on WS disconnect.
Observability: `canopy_training_control_command_latency_ms{command, transport}` histogram,
`canopy_training_control_orphaned_total{command}` counter, `cascor_ws_control_command_received_total{command}` counter.

**Design**:

Two-PR sequence (cascor→canopy). P11 cascor dispatch, P12 canopy button routing. Merge strict order: P11→P12.
Per-command timeouts reflect source doc priority (start longest, others shorter).

**Notes**:

Entry: Phase B in main + Phase B-pre-b in production >=48h (strict). Phase D gated on production because directly exposes control plane.
Exit: 9 tests pass, manual button clicks work via WS + fallback, CSRF enforced, 24h zero orphaned commands.
Rollback: `JUNIPER_CANOPY_BUTTONS_USE_WS=false` (instant) or revert P12→P11. Dedup candidate with R3-03.

### JR-ML-PERF-009 — Phase E: Per-client pump tasks + bounded queues + policy matrix; default drop_oldest_progress_only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-98)

**Notes**:

Phase E major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-141 — Phase F: Application ping/pong at 30s; 10s dead-conn threshold; uncap reconnect; jitter formula.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-99)

**Notes**:

Phase F major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-TEST-014 — Phase G: Cascor set_params integration tests via FastAPI TestClient.websocket_connect().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-100)

**Notes**:

Phase G major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-202 — Phase H: Normalize_metric audit + regression gate; CODEOWNERS hard gate; pre-commit hook.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-101)

**Notes**:

Phase H major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-014 — Phase I: Asset cache busting; bump assets_url_path / hash query param.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-102)

**Notes**:

Phase I major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-203 — Phase: Switch (env var).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 337-338)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-SEC-086 — Process.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 572-588)

**Detail**:

Five specialized validation agents independently cross-referenced the v2.0.0 outstanding development items document against 34 source documents spanning all 8 Juniper ecosystem repositories. Each agent was assigned a focused subset of source documents to ensure thorough coverage:

### JR-ML-API-023 — Reconnect protocol must handle resume frames within 5s timeout and emit resume_ok or resume_failed response.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 420-490)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 389-412)

**Detail**:

training_stream handler: await asyncio.wait_for(ws.receive_json(), timeout=5.0) for optional first frame.
If type=="resume": check server_instance_id, call replay_since(), emit resume_ok + replayed OR resume_failed.
Failure reasons: server_restarted (instance mismatch), out_of_range (seq too old), malformed_resume (missing fields).
If first frame is not resume or timeout: treat as fresh client, route through normal handler.
Promote to active only after resume handling completes.

**Notes**:

Phase A-server (Day 3). R0-03 §6.1 "initial_status race" documented in code comment. Scenarios in §8.

### JR-ML-ARCH-204 — Recovery: kill switches work.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-DEP-013 — Release readiness checklist: pre-commit compliance, test pass, version sync across 6 applications.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 1-50)

### JR-ML-TEST-015 — Remediate cross-project regression issues identified in 2026-04-03 analysis.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/REGRESSION_REMEDIATION_PLAN_2026-04-03.md` (lines 1-100)

### JR-ML-TRAIN-043 — Remediate training stall issue with identified root cause and proposed solution.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_STALL_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Blocking training completion; high priority fix.

### JR-ML-WS-142 — replay_since(last_seq) + ReplayOutOfRange exception; copy-under-lock pattern.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 115-115)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TEST-016 — Resolve CI validation findings: categorize, root-cause, fix per priority (P0/P1/P2/P3).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CI_VALIDATION_FINDINGS_2026-04-29.md` (lines 1-50)

### JR-ML-SEC-087 — SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 169-184)

### JR-ML-SEC-088 — SEC-02: Rate Limiter Memory Unbounded — DoS Vector.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 187-209)

### JR-ML-SEC-089 — SEC-03: No Per-IP WebSocket Connection Limiting (cascor).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 212-226)

### JR-ML-SEC-090 — SEC-04: Sync Dataset Generation Blocks Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 229-244)

### JR-ML-SEC-091 — SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 247-261)

### JR-ML-SEC-092 — SEC-06: No Auth on Canopy WS Endpoints.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 264-278)

### JR-ML-SEC-093 — SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 281-295)

### JR-ML-SEC-094 — SEC-10: Sentry `send_default_pii=True` (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 298-312)

### JR-ML-SEC-095 — SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 315-337)

### JR-ML-SEC-096 — SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 340-354)

### JR-ML-SEC-097 — SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 357-379)

### JR-ML-SEC-098 — SEC-14: Internal Exception Messages Leaked to Clients.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 382-396)

### JR-ML-SEC-099 — SEC-15: Cascor Sentry `send_default_pii=True`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 399-413)

### JR-ML-SEC-100 — SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 416-430)

### JR-ML-SEC-101 — SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 433-447)

### JR-ML-SEC-102 — SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 450-464)

### JR-ML-SEC-103 — Security remediation for identified vulnerability in PR#40.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PR40_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

### JR-ML-SEC-104 — Security remediation for juniper-deploy PR#14.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/JUNIPER_DEPLOY_PR14_SECURITY_REMEDIATION_PLAN.md` (lines 1-100)

**Notes**:

Security issue in deployment pipeline.

### JR-ML-WS-143 — Security: CSWSH closed.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-144 — self._pending: Dict[str, asyncio.Future] correlation map, bounded at 256 with JuniperCascorOverloadError on overflow.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 218-218)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-145 — _send_json wraps in asyncio.wait_for timeout (GAP-WS-07 quick-fix, default 0.5s).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 114-114)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-API-024 — Server must advertise server_instance_id (UUID) in connection_established and snapshot_seq in status endpoint.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 392-410)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 283-299)

**Detail**:

connection_established frame (sent via send_personal_message, bypassing replay buffer) includes server_instance_id, server_start_time, replay_buffer_capacity.
/api/v1/training/status endpoint adds atomic snapshot under _seq_lock: payload["snapshot_seq"] = manager._next_seq - 1.
Also advertise server_instance_id in status endpoint.
Client uses server_instance_id to detect server restarts and reject out-of-date resume attempts.

**Notes**:

Phase A-server (Days 2-3). Atomicity of snapshot_seq with state read is load-bearing (Day 3 commit 6).

### JR-ML-API-025 — SetParamsResponse wire model with extra=allow.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 224-224)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-API-026 — Step 3: Add Regression Tests.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 95-145)

**Detail**:

#### New file: `src/tests/unit/test_convergence_ui_regression.py`

### JR-ML-OBS-044 — Swap PrometheusMiddleware and RequestIdMiddleware order in canopy main.py:312 to fix mis-labeling.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 162-168)

**Detail**:

G5 - Middleware order causes request-id ContextVar to be unset during metric labeling.
One-line fix. Add unit test asserting request-id header present in metric labels.

### JR-ML-SEC-105 — Task 1 (Metrics).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 381-404)

**Detail**:

- Card pattern: `html.Div([html.H5(), html.H2(id=...)])` with flex layout (lines 393-428)

### JR-ML-TEST-017 — testing/fake_ws_client.py: on_command(name, handler) auto-scaffold command_response reply.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 225-225)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-TRAIN-044 — Training Control.

**Status**: proposed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 315-323)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 251-259)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-WS-146 — training_stream.py two-phase registration, resume/resume_ok/resume_failed handler with 5s timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 116-116)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-TEST-018 — Unit tests for apply_params() routing and feature flag.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_validation.md` (lines 252-261)

### JR-ML-TEST-019 — Unit tests for seq numbers, replay buffer, and resume protocol.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_validation.md` (lines 171-207)

### JR-ML-TEST-020 — Unit tests for set_params() method and concurrent correlation.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_validation.md` (lines 212-237)

### JR-ML-ARCH-205 — `use_websocket_set_params`: C.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 310-311)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-SEC-106 — Validate Anthropic API key access patterns across repos; ensure keys not logged or exposed in responses.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ANTHROPIC_API_KEY_ACCESS_VALIDATION_WALKTHROUGH_2026-05-10.md` (lines 1-50)

### JR-ML-TEST-021 — Validate CI pipeline: every workflow runs green, soft-fail jobs promoted per-repo to hard gates after shakedown.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CI_VALIDATION_ROADMAP_2026-04-29.md` (lines 28-51)

### JR-ML-OBS-045 — Wire 9 cascor WS metrics (resume/replay/throttle observability) via OBS-WIRE-02, behind feature flag.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 148-162)

**Detail**:

G4 - 11 dead cascor_ws_* metrics with zero production callers defined but unwired.
OBS-WIRE-02 wires 9 viable metrics. Remove cascor_ws_seq_gap_detected_total and cascor_ws_connections_active as not feasible.
Deploy behind JUNIPER_CASCOR_WS_METRICS_FULL feature flag initially.

### JR-ML-OBS-046 — Work Unit 2: Metrics Panel Table Dark Mode (MEDIUM-HIGH).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 83-129)

**Detail**:

**Issues**: 1E (lines 1759, 1819, 1904)

### JR-ML-API-027 — Work Unit 4: Service Mode Verification (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 144-161)

**Detail**:

Added 5 integration tests to `test_network_stats_endpoint.py` (`TestNetworkStatsServiceMode` class) that mock the backend as service mode with realistic multi-hidden-unit weight data. Tests verify:

### JR-ML-OBS-047 — WS metrics audit A9 + integration 3.2: expose buffer occupancy, connection state, frame sizes as Prometheus gauges.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md` (lines 1-50)

### JR-ML-ARCH-206 — `ws_backpressure_policy`: E.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 316-317)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-207 — `ws_rate_limit_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 314-315)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-208 — `ws_security_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 312-313)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-API-028 — 1.3 Code Quality.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 69-81)

**Detail**:

| ID       | Severity   | File:Line                         | Description

### JR-ML-SEC-107 — 1.5 CI/CD.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 89-105)

**Detail**:

| CC-CI-01 | **Low**  | CI tests Python 3.11-3.13 but `pyproject.toml` classifies 3.14.                                                   |

### JR-ML-UI-015 — 2.7 Step 2.7 (configurable paths) -- already done.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 67-107)

**Detail**:

Paths in `juniper_plant_all.bash` and `juniper_chop_all.bash` are already configurable via environment variables from Phase 1. No additional work needed.

### JR-ML-SEC-108 — 3.12 DASHBOARD-STALE-PANELS — 7 stale Grafana panels post audit-close.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 334-370)

**Detail**:

**Severity:** P1 (operational — dashboards mislead operators) · **Owner repo:** juniper-deploy · **Status:** in-flight (sister PR opened 2026-05-06)

### JR-ML-SEC-109 — 3.2 juniper-cascor.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 96-146)

**Detail**:

| `/metrics` URL | `http://juniper-cascor:8200/metrics` (compose) |

### JR-ML-SEC-110 — 4.1 Dimension A — Metrics surface integrity.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 176-226)

**Detail**:

**Scope**: Verify all metrics referenced in the R5.1 SLO catalog, `alert_rules.yml`,

### JR-ML-API-029 — 4.1 Root Cause.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 200-213)

**Detail**:

**Output weights transposition bug**: ALREADY FIXED (merged). `_transform_topology()` now

### JR-ML-SEC-111 — 4.5 Dimension E — Throttles + tech debt + race conditions.

**Status**: shipped  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 331-370)

**Detail**:

**Scope**: Find hidden throttles beyond the known `cascade_correlation.py:1655`,

### JR-ML-UI-016 — 6.1 juniper-overview.json (14 panels, version 3, title "Juniper Overview").

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 310-330)

**Detail**:

| Request Latency — p50 / p95 / p99 | timeseries | `histogram_quantile(...)` against the shared HTTP duration histogram | |

### JR-ML-OBS-048 — 6.5 Placeholder text panels (intentional gaps — OBS-WIRE-01).

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 424-446)

**Detail**:

| juniper-cascor.json | Worker `last_task_duration_seconds` (JSON-only — Prometheus bridge pending) | **STALE** — bridge shipped via juniper-cascor#188 (`WorkerRegistr

### JR-ML-OBS-049 — Closing PRs that motivated this tracker (reference only).

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 423-433)

**Detail**:

- juniper-cascor#221 — Final E.6 audit follow-up: WorkerRegistry size cap + WS handshake rejection plumbing (MERGED 2026-05-05)

### JR-ML-WS-147 — GAP-WS-19 close_all lock is RESOLVED on main.

**Status**: shipped  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 48-48)

**Notes**:

Settled position C-11 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-030 — _normalize_metric dual-format contract (flat + nested) preserved forever.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 59-59)

**Notes**:

Settled position C-22 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-031 — REST endpoints preserved FOREVER: /api/metrics/history, /api/train/*, /api/v1/training/params, /api/topology.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 60-60)

**Notes**:

Settled position C-23 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-050 — Severity-1 cluster headline.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 421-439)

**Detail**:

cause: the pre-METRICS-MON observability scaffolding in

### JR-ML-OBS-051 — What needs to happen.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 676-699)

**Detail**:

1. **Pull p50 / p95 / p99 from Prometheus** for every SLI in catalog §3

### JR-ML-OBS-052 — 2D. Phase Duration Display.

**Status**: in-progress  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 108-116)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-UI-017 — Fix candidate training display rendering issues in Canopy.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` (lines 1-100)

### JR-ML-UI-018 — Fix Canopy dashboard display issues with layout and rendering.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DASHBOARD_DISPLAY_FIXES.md` (lines 1-100)

### JR-ML-SEC-112 — Step 1: Workspace Setup.

**Status**: in-progress  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 48-70)

**Detail**:

- Branch: `main` with committed Phase 5.1/5.2 fixes

### JR-ML-UI-019 — 2.1 Bugs.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 105-114)

**Detail**:

| ID        | Severity   | File:Line              | Description

### JR-ML-OBS-053 — 4.2 When new items are added.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 378-388)

**Detail**:

- **Audit follow-ups** — if a new audit (e.g. a 2026-Q3 observability re-audit) surfaces findings whose action sits beyond a single PR, add them here with a fresh ID.

### JR-ML-SEC-113 — 4.3 Dimension C — Shared lib + WS schema + middleware.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 275-305)

**Detail**:

**Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6

### JR-ML-UI-020 — 4.3 RequestIdMiddleware boundary placement.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 249-257)

**Detail**:

Per audit finding C.1 (juniper-canopy): canopy's `RequestIdMiddleware`

### JR-ML-TRAIN-045 — 4.4 CR-025: WebSocket Async Lock.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 419-434)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

### JR-ML-TRAIN-046 — 5.4 `settings.py`.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 314-331)

**Detail**:

epochs: TrainingParamConfig = TrainingParamConfig(min=10, max=10000000, default=1000000)

### JR-ML-TRAIN-047 — Concurrency Assessment.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 324-330)

**Detail**:

**WebSocket Mode**: Well-designed single-threaded asyncio with `asyncio.to_thread` for CPU-bound training. No shared mutable state between async loop and training thread

### JR-ML-SEC-114 — Cross-repo.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 415-423)

**Detail**:

- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline

### JR-ML-UI-021 — Design.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 536-555)

**Detail**:

Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:

### JR-ML-OBS-054 — Design docs.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 454-465)

**Detail**:

- [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](../legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md)

### JR-ML-OBS-055 — Design mini-batch instrumentation for CasCor training observability.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md` (lines 1-100)

**Notes**:

Batch-level metrics collection.

### JR-ML-UI-022 — Implement contextual menu and candidate tab design for Canopy UI.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CONTEXTUAL_MENU_AND_CANDIDATE_TAB_DESIGN.md` (lines 1-100)

### JR-ML-SEC-115 — Optimizer and `nn.Linear` recreated on every `train_output_layer` call.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 859-877)

### JR-ML-SEC-116 — Per-phase entry / design docs.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 728-740)

**Detail**:

- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`

### JR-ML-SEC-117 — Performance test baselines record data but never assert against regression thresholds.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1058-1076)

### JR-ML-OBS-056 — Phase B (polling elimination — P0 WIN) — ✅ IMPLEMENTED.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 330-341)

**Detail**:

| Two-flag design: `enable_browser_ws_bridge` + `disable_ws_bridge`   | ✅ In `settings.py`                        |

### JR-ML-WS-148 — Standardize WebSocket frame schema for Canopy↔CasCor training streaming.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md` (lines 1-50)

### JR-ML-OBS-057 — Address residual follow-ups from METRICS-MON program close.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md` (lines 1-100)

**Notes**:

Captured in POST_METRICS_MON_TRACKER; deferred after program closure.

### JR-ML-UI-023 — Canopy dashboard self-call refactor: defer weight display, implement metrics playback, option C trigger conditions.

**Status**: deferred  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/CANOPY_DASHBOARD_SELF_CALL_REFACTOR_2026-05-10.md` (lines 1-50)

### JR-ML-SEC-118 — Per-command HMAC deferred indefinitely.

**Status**: deferred  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 70-70)

**Notes**:

Settled position C-33 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-149 — Phase E-server deferred perper-client queue and backpressure policy matrix.

**Status**: deferred  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_cascor_backend.md` (lines 1017-1029)

### JR-ML-OBS-058 — Re-bucket cascor_ws_command_handler_seconds for better SLO breach-detection precision post-soak.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 173-182)

**Detail**:

G7 - 50 ms SLO target sits one bucket below 100 ms +inf cap, limiting breach-detection precision.
Deferred to R5.1c post-soak calibration per juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md.

### JR-ML-ARCH-209 — Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: deferred  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 61-61)

**Notes**:

Settled position C-24 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-059 — 1.2 Network Topology Visualization Issues.

**Status**: rejected  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 93-143)

**Detail**:

**Repositories**: juniper-cascor, juniper-canopy

### JR-ML-DATA-010 — 2.6 juniper-data-client.

**Status**: rejected  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 348-359)

**Detail**:

| DC-01 | **High**   | `constants.py`           | 91–92   | Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server |

### JR-ML-SEC-119 — 2.7 juniper-deploy.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 359-369)

**Detail**:

| DD-01 | **High** | `docker-compose.yml`           | 129, 298, 349, 386 | Cascor and canopy ports bound to `0.0.0.0` — exposed to network (data correctly uses `127.0.0.1`)                |

### JR-ML-SEC-120 — 2A. Validation Loss/Accuracy Overlay Traces.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 74-88)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-ARCH-210 — 4.2 Cross-Section Checkbox Linking.

**Status**: rejected  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 234-257)

**Detail**:

- Uses `ctx.triggered_id` to determine which checkbox changed

### JR-ML-UI-024 — 7.5 Shutdown Signal Handling.

**Status**: rejected  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 453-468)

**Detail**:

All services handle signals adequately at the application level. The gap is in the orchestration scripts that don't verify shutdown completed.

### JR-ML-SEC-121 — Issue Remediations, Section 15 — juniper-cascor-client.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 323-373)

**Detail**:

#### CC-01: `_recv_loop` Catches Bare `Exception`

### JR-ML-SEC-122 — Issue Remediations, Section 15 — juniper-cascor-worker.

**Status**: rejected  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 561-611)

**Detail**:

#### CW-01: `receive_json()` Doesn't Catch JSONDecodeError

### JR-ML-OPS-004 — Shadow traffic: rejected.

**Status**: rejected  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 68-68)

**Notes**:

Settled position C-31 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-211 — 1. Purpose and Methodology.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 34-51)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 39-64)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-TRAIN-048 — 10. CasCor Algorithm and Feature Enhancements.

**Status**: superseded  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 360-410)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 398-450)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-212 — 11. Cross-Repository Alignment Issues.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 411-438)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 451-486)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-213 — 12. Housekeeping and Broken References.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 439-476)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 487-526)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-214 — 13. juniper-deploy Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 477-526)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 527-581)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-215 — 14. juniper-data Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 527-557)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 582-614)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-216 — 15. Client Library Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 558-606)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 615-666)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-PERF-010 — 16. Performance Issues (v4 new section).

**Status**: superseded  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 607-634)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 667-696)

**Notes**:

[v2 ARCH→PERF re-bucket] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-217 — 17. Concurrency and Thread Safety Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 697-716)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-218 — 17. Source Document Lineage.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 635-657)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-219 — 18. Error Handling and Robustness (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 717-737)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-220 — 18. Validation Methodology (v4.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 658-698)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-221 — 19. Testing and CI/CD Gaps (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 738-780)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-222 — 2. Validation Summary.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 52-75)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 65-92)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-223 — 20. Configuration and Dependency Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 781-804)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-224 — 21. API Contract and Protocol Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 805-825)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-225 — 22. Source Document Lineage (v5.0.0 - v1.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 826-900)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-226 — 23. Validation Methodology (v5.0.0 - v1.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 901-941)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-227 — 3. Items Previously Incomplete — Now Fixed.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 76-100)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 93-119)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-SEC-123 — 4. Security Issues.

**Status**: superseded  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 101-135)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 120-156)

**Notes**:

[v2 ARCH→SEC re-bucket] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-228 — 5. Active Bugs (Confirmed Still Present).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 136-193)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 157-223)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-229 — 6. Code Quality and Cleanup.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 194-244)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 224-276)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-UI-025 — 7. Dashboard Enhancements.

**Status**: superseded  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 245-288)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 277-322)

**Notes**:

[v2 ARCH→UI re-bucket] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-WS-150 — 8. WebSocket Migration (R5-01 Remaining Phases).

**Status**: superseded  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 289-324)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 323-360)

**Notes**:

[v2 ARCH→WS re-bucket] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-230 — 9. Microservices and Infrastructure.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 325-359)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 361-397)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-231 — Table of Contents.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 11-33)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 11-38)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-TRAIN-049 — V6 Partial — Agent B: Active Bugs (CasCor, Canopy, Data).

**Status**: superseded  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_b_active_bugs.md` (lines 1-100)

**Notes**:

[v2 ARCH→TRAIN re-bucket] v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-ML-PERF-011 — V6 Partial — Agent D: Quality, Housekeeping, Performance, Configuration.

**Status**: superseded  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_d_quality_housekeeping_perf_config.md` (lines 1-100)

**Notes**:

[v2 ARCH→PERF re-bucket] v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-ML-OBS-060 — 1.1 Bugs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 52-62)

**Detail**:

| ID        | Severity   | File:Line                    | Description

### JR-ML-SEC-124 — 1.1 juniper-data: Version Synchronization.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 30-41)

**Detail**:

- `juniper_data/__init__.py:17` — change `__version__ = "0.4.2"` to `"0.6.0"`

### JR-ML-SEC-125 — 1.2 juniper-data: CSV Import Path Traversal Fix.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 41-63)

**Detail**:

**Root cause**: `csv_import/generator.py:80-87` passes `file_path` directly to `Path()`.

### JR-ML-SEC-126 — 1.2 Security.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 62-69)

**Detail**:

| ID        | Severity | File:Line           | Description                                                                                                  |

### JR-ML-DATA-011 — 1.3 juniper-data-client: Version Alignment.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 63-73)

**Detail**:

- `pyproject.toml` — bump version to `0.4.0`

### JR-ML-SEC-127 — 1.4 juniper-deploy: Network Isolation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 73-101)

**Detail**:

**File**: `docker-compose.yml` lines 494-503

### JR-ML-API-032 — 1.4 Shared Memory and Multiprocessing Issues.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 188-217)

**Detail**:

#### 1.4.1 Shared Memory Block Leaks

### JR-ML-TRAIN-050 — 1.4 Test Coverage Gaps.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 81-89)

**Detail**:

| `client.py`    | 82.22%   | `wait_for_ready()` polling, JSON decode errors, fallback error message path                                                          |

### JR-ML-SEC-128 — 1.5 juniper-cascor-worker: CHANGELOG & Tags.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 101-113)

**Detail**:

**CHANGELOG changes**: Add sections for v0.1.1, v0.3.0 covering:

### JR-ML-SEC-129 — 1.5 Security Concerns.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 217-256)

**Detail**:

**Repositories**: juniper-data, juniper-deploy

### JR-ML-TRAIN-051 — 1.6 juniper-ml: CHANGELOG & Tags.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 113-131)

**Detail**:

**CHANGELOG changes**: Populate [Unreleased] section, then rename to [0.4.0] covering:

### JR-ML-API-033 — 10. Phase 7: Validation and Finalization.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 232-233)

### JR-ML-SEC-130 — 13.1 Infrastructure Bugs (Confirmed Still Present).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 402-419)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 317-330)

**Detail**:

| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:499-500` vs service env var

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-131 — 14.1 Security Issues (Confirmed Still Present).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 436-444)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 347-355)

**Detail**:

| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can esc

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-012 — 15.1 juniper-cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 466-479)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

### JR-ML-TRAIN-052 — 15.1 juniper-cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 377-387)

**Detail**:

| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                | 🔴 Open            |

### JR-ML-UI-026 — 15.3 juniper-cascor-worker.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 488-504)

**Detail**:

| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker      | 🔴 Open |

### JR-ML-API-034 — 2. Plan Overview.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 21-22)

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

### JR-ML-DATA-013 — 2.1 Neural Network Subsection (12 inputs).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 39-56)

**Detail**:

| 3  | Learning Rate         | `nn-learning-rate-input`                | number (float) | 0.01            | RENAMED (was `learning-rate-input`)           |

### JR-ML-TRAIN-053 — 2.2 Candidate Nodes Subsection (10 inputs).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 56-71)

**Detail**:

| 2   | Correlation Threshold     | `cn-correlation-threshold-input`          | number (float) | 0.001               | NEW         |

### JR-ML-UI-027 — 2.2 juniper-all.target: Wants= vs Requires=.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 26-32)

**Detail**:

**Decision**: Use `Wants=` (not `Requires=`).

### JR-ML-OBS-061 — 2.2 juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 283-298)

**Detail**:

| CN-01 | **Medium** | `dashboard_manager.py`  | 346–349        | `_api_base_url` hardcoded to `127.0.0.1` — Dash REST callbacks break in Docker/remote deployments                                 |

### JR-ML-DEP-016 — 2.2 juniper-data: Code Fixes.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 171-188)

**Detail**:

**2.2.1 n_spirals fallback** (`datasets.py:114`):

### JR-ML-SEC-132 — 2.2 Security.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 114-123)

**Detail**:

| ID        | Severity | File:Line                  | Description

### JR-ML-SEC-133 — 2.2 Startup Orchestration Options.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 116-166)

**Detail**:

#### Option A: Docker Compose (Unified)

### JR-ML-WS-151 — 2.3 Code Quality.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 123-132)

**Detail**:

|    ID    | Severity | File:Line               | Description                                                                                 |

### JR-ML-SEC-134 — 2.3 Comparative Evaluation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 282-299)

### JR-ML-API-035 — 2.3 juniper-cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 298-314)

**Detail**:

| CL-01 | **Medium** | `ws_client.py`              | 231–240  | `command()` vs `set_params()` message format inconsistency — `command()` never sends `"type"` field   |

### JR-ML-SEC-135 — 2.3 juniper-data-client: Test & Retry Fixes.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 188-204)

**Detail**:

**2.3.1 Add PATCH to retry allowed_methods** (`client.py:101`):

### JR-ML-WS-152 — 2.3 Plant/chop systemd mode activation.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 32-38)

**Detail**:

**Decision**: Support both `--systemd` flag and `USE_SYSTEMD=1` env var.

### JR-ML-ARCH-232 — 2.3 Structural IDs.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 71-84)

**Detail**:

| NN section collapse | `nn-subsection-collapse` | dbc.Collapse wrapper      |

### JR-ML-UI-028 — 2.4 CLI naming convention.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 38-46)

**Detail**:

**Decision**: Rename canopy's `juniper-ctl` to `juniper-canopy-ctl` for consistency.

### JR-ML-DATA-014 — 2.4 juniper-cascor-client: Semantic & Coverage Fixes.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 204-214)

**Detail**:

**2.4.1 Fix `wait_for_ready()`** (`client.py:86`):

### JR-ML-API-036 — 2.4 juniper-cascor-worker.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 314-327)

**Detail**:

| CW-01 | **Medium** | `worker.py`        | 225     | Timeout error sends `candidate_uuid: ""` instead of actual UUID from `candidate_data`                |

### JR-ML-UI-029 — 2.4 Removed Component IDs.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 84-99)

**Detail**:

## 3. Constants Changes (`canopy_constants.py`)

### JR-ML-SEC-136 — 2.4 Test Coverage Gaps.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 132-142)

**Detail**:

| `cli.py`           | 90.70%   | Second SIGINT force-exit path; post-`asyncio.run` log line                                |

### JR-ML-SEC-137 — 2.5 CI/CD & Dockerfile.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 142-159)

**Detail**:

| CW-CI-01   | **Low**    | CI tests 3.11-3.13, not 3.14 (Dockerfile uses python:3.14-slim).                                                 |

### JR-ML-TRAIN-054 — 2.5 juniper-cascor-worker: Thread Safety & Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 214-243)

**Detail**:

**2.5.1 Fix signal handler thread safety** (`worker.py:121`, `cli.py:95`):

### JR-ML-OBS-062 — 2.5 Resource limits.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 46-54)

### JR-ML-API-037 — 2.6 juniper-deploy: Makefile & Dockerfile Fixes.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 243-273)

**Detail**:

**2.6.1 Fix Makefile variables** (`Makefile:70-72`):

### JR-ML-SEC-138 — 2.6 Security hardening.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 54-67)

### JR-ML-LOCK-001 — 2.8 juniper-ml.

**Status**: proposed  **Priority**: P2  **Category**: LOCK  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 369-381)

**Detail**:

| ML-01 | **Medium** | `scripts/wake_the_claude.bash` | 37      | `DEBUG="${TRUE}"` hardcoded ON in production — all invocations emit debug output               |

### JR-ML-OBS-063 — 2B. Training Progress Summary Cards.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 88-99)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-OBS-064 — 2C. Learning Rate Metric Card.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 99-108)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-OBS-065 — 2E. Hidden Units Progress Ratio.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 116-128)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`, `src/frontend/dashboard_manager.py`

### JR-ML-API-038 — 3. Phase 0: Prior Art Assessment.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 60-61)

### JR-ML-API-039 — 3.1 Bugs.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 159-169)

**Detail**:

| ID        | Severity   | File:Line                        | Description

### JR-ML-DEP-017 — 3.1 CALIB-01 — T+30d SLO target calibration.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 62-97)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

### JR-ML-SEC-139 — 3.1 Changelog Updates.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 273-286)

**Detail**:

| juniper-ml            | Populate [Unreleased], rename to [0.4.0] | Added, Changed, Fixed, CI                                                   |

### JR-ML-API-040 — 3.1 CR-006: Verify `max_iterations` End-to-End Implementation.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 82-132)

**Detail**:

**Severity**: S1 (largely resolved) | **Effort**: Small (0.5-1 day) | **Repos**: juniper-cascor, juniper-canopy

### JR-ML-OBS-066 — 3.1 Current Implementation.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 328-342)

**Detail**:

JuniperCanopy implements a two-mode activation system in `src/main.py` (lines 213-247):

### JR-ML-DATA-015 — 3.1 Generator Name Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 381-388)

**Detail**:

**Repositories**: juniper-data, juniper-data-client

### JR-ML-SEC-140 — 3.1 juniper-data.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 68-96)

**Detail**:

| `/metrics` URL | `http://juniper-data:8100/metrics` (compose); `http://localhost:8100/metrics` (local) |

### JR-ML-TRAIN-055 — 3.1 Modified Existing Constants.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 99-114)

**Detail**:

DEFAULT_TRAINING_EPOCHS: Final[int] = 1000000    # was 300

### JR-ML-OBS-067 — 3.11 DATA-CACHED-WIRE — `juniper_data_datasets_cached` Gauge has no production caller.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 307-334)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-data · **Status:** in-flight (sister PR opened 2026-05-06)

### JR-ML-TRAIN-056 — 3.2 CR-007: Auto-Reset State Machine on Start.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 154-182)

**Detail**:

**Severity**: S1 | **Effort**: Medium (1 day) | **Repo**: juniper-cascor

### JR-ML-DATA-016 — 3.2 New Neural Network Constants.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 114-149)

**Detail**:

MAX_MAX_ITERATIONS: Final[int] = 100000

### JR-ML-OBS-068 — 3.2 Purpose and Analysis of Current Modes.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 342-388)

**Detail**:

- Simulates realistic training lifecycle: idle → training → paused → complete

### JR-ML-OBS-069 — 3.2 R5.1c-BUCKETS — Cascor sub-ms bucket re-evaluation.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 97-124)

**Detail**:

**Severity:** P2 · **Owner repo:** juniper-cascor · **Status:** open (depends on CALIB-01)

### JR-ML-API-041 — 3.2 README & Documentation Updates.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 286-294)

**Detail**:

| juniper-data-client   | README API table (+6 methods), REFERENCE.md (version + batch/versioning), QUICK_START.md (FakeDataClient class name) |

### JR-ML-SEC-141 — 3.2 Security.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 169-178)

**Detail**:

| ID        | Severity   | File:Line                   | Description

### JR-ML-API-042 — 3.2 Wire Protocol Alignment.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 388-402)

**Detail**:

**Repositories**: juniper-cascor, juniper-cascor-client, juniper-cascor-worker

### JR-ML-API-043 — 3.3 CR-008: Implement WebSocket `set_params`.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 182-207)

**Detail**:

**Severity**: S2 | **Effort**: Small (0.5 day) | **Repo**: juniper-cascor

### JR-ML-SEC-142 — 3.3 Current State: systemd (juniper-canopy only).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 243-265)

**Detail**:

**Service file**: `juniper-canopy/scripts/juniper-canopy.service`

### JR-ML-SEC-143 — 3.3 juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 163-193)

**Detail**:

| `/metrics` URL | `http://juniper-canopy:8050/metrics` |

### JR-ML-TRAIN-057 — 3.3 New Candidate Nodes Constants.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 149-197)

**Detail**:

DEFAULT_CANDIDATE_CORRELATION_THRESHOLD: Final[float] = 0.001

### JR-ML-TRAIN-058 — 3.3 State Name Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 402-409)

**Detail**:

**Repositories**: juniper-cascor, juniper-cascor-client

### JR-ML-API-044 — 3.4 Code Quality.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 187-198)

**Detail**:

| ID       | Severity   | File:Line                           | Description                                                                               |

### JR-ML-SEC-144 — 3.4 Comparative Evaluation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 560-575)

**Detail**:

| Criterion                     | Option 1: Feature Flag | Option 2: Mock Containers | Option 3: Client Fakes | Option 4: VCR         | Option 5: Demo Profile    |

### JR-ML-UI-030 — 3.4 Dependency Update When Adding Client Method.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 187-200)

**Detail**:

Per `DEPENDENCY_UPDATE_WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:

### JR-ML-SEC-145 — 3.4 Individual Application Startup Scripts.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 265-292)

**Detail**:

- **Strength**: Self-contained, handles env setup

### JR-ML-OBS-070 — 3.4 Phase 1 Success Criteria.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 207-216)

**Detail**:

- [x] New tests added for all changes — `test_websocket_control.py` (3 tests), `test_lifecycle_manager.py` (1 test)

### JR-ML-DEP-018 — 3.4 Port Mapping Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 409-420)

**Detail**:

**Repositories**: juniper-cascor, juniper-deploy

### JR-ML-SEC-146 — 3.5 AMTOOL-CI — `amtool check-config` snap-confinement gap.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 182-207)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** open

### JR-ML-DEP-019 — 3.5 Recommendation.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 575-604)

**Detail**:

**Recommended approach: Phased adoption combining Options 1, 3, and 5.**

### JR-ML-API-045 — 3.5 Test Coverage Gaps.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 198-206)

### JR-ML-DATA-017 — 3.6 CI/CD.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 206-220)

**Detail**:

| JD-CI-03 | **Low**    | CI workflow and `.pre-commit-config.yaml` headers say version `0.4.0` — stale. |

### JR-ML-API-046 — 4. Phase 1: Codebase Exploration and Discovery.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 85-86)

### JR-ML-OBS-071 — 4.1 Architecture Overview.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 292-313)

**Detail**:

Profile: observability (additive)

### JR-ML-OBS-072 — 4.1 Callback Summary.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 197-214)

**Detail**:

**Removed callback**: `handle_parameter_changes` - returns `dash.no_update` unconditionally, only logs. Logging can move to `track_param_changes`.

### JR-ML-DATA-018 — 4.1 Create Missing Retroactive Tags.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 305-314)

**Detail**:

| juniper-ml            | v0.2.1, v0.3.0 | Identify from git log |

### JR-ML-API-047 — 4.1 Current Health Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 604-616)

**Detail**:

| **JuniperData**   | `GET /v1/health/live` → `{"status": "alive"}` | `GET /v1/health/ready` → `{"status": "ready", "version": ...}`                        | `GET /v1/health` |

### JR-ML-DOC-002 — 4.1 How this tracker is updated as items close.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 370-378)

**Detail**:

1. Remove its row from §2 (or flip the `Status` column to `closed (PR #N)` if you prefer to keep historical visibility).

### JR-ML-OBS-073 — 4.1 Public symbols.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 222-236)

**Detail**:

- **Constants (R1.1/R1.2/R1.3 contract):**

### JR-ML-OBS-074 — 4.2 Adoption matrix.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 236-249)

**Detail**:

| Repo | Declares dep in `pyproject.toml`? | Imports `juniper_observability`? | Components imported |

### JR-ML-UI-031 — 4.2 Code Quality.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 229-239)

**Detail**:

| ID       | Severity   | File:Line             | Description

### JR-ML-DEP-020 — 4.2 Discovery Approach Evaluation.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 616-627)

**Detail**:

**Recommendation**: Continue with direct URL configuration (`JUNIPER_DATA_URL`, `CASCOR_SERVICE_URL`). Docker Compose DNS will handle discovery automatically when contai

### JR-ML-SEC-147 — 4.2 Pre-Release Validation Checklist.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 314-327)

### JR-ML-SEC-148 — 4.3 Build & Package Validation (PyPI packages only).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 327-337)

### JR-ML-UI-032 — 4.3 Radio Button Enable/Disable Pattern.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 257-267)

**Detail**:

- **NN Growth Trigger**: `"preset_epochs"` enables preset-epochs-input, disables convergence-threshold-input; `"convergence"` reverses

### JR-ML-OBS-075 — 4.3 When the tracker itself can be retired.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 388-409)

**Detail**:

- A successor tracker (e.g. `POST_METRICS_MON_TRACKER_2026-09-01.md` for a 2026-Q3 program close) supersedes it.

### JR-ML-API-048 — 4.4 Applied Params Store Structure.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 267-302)

**Detail**:

"cn_candidate_selection": None,  # no default; sub-group disabled when checkbox unchecked

### JR-ML-SEC-149 — 4.4 CI/CD.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 246-260)

**Detail**:

| DC-CI-01 | **Low**  | Security scan installs `.[dev]` (full dev deps) instead of minimal runtime. |

### JR-ML-API-049 — 4.4 Dimension D — Buckets + test coverage.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 305-331)

**Detail**:

**Scope**: Bucket→SLO alignment, R5.1b coverage of the 2 non-re-bucketed

### JR-ML-SEC-150 — 4.4 MetricsAuthMiddleware confinement.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 257-276)

**Detail**:

`juniper-data/juniper_data/api/observability.py:72` and is **not**

### JR-ML-API-050 — 4.4 Per-Service Dockerfile Review.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 341-360)

**Detail**:

| Base image    | python:3.14-slim         | python:3.14-slim       | python:3.14-slim     |

### JR-ML-ARCH-233 — 4.5 Multi Candidate Sub-Group Enable/Disable.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 214-234)

**Detail**:

Note: Callback #9 (`toggle_cn_selection_inputs`) should also check the checkbox state and keep inputs disabled when the checkbox is unchecked, regardless o

### JR-ML-SEC-151 — 4.5 Phase 2 Success Criteria.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 434-451)

**Detail**:

## 5. Phase 3: Metrics Granularity

### JR-ML-API-051 — 5. Phase 2: Deep-Dive API and Model Analysis.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 116-117)

### JR-ML-API-052 — 5.1 `/api/set_params` Endpoint (`main.py`).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 302-306)

**Detail**:

Expand to accept all 22 parameter keys with `nn_` and `cn_` prefixes. Map `nn_learning_rate`, `nn_max_hidden_units`, `nn_max_total_epochs` to `TrainingState.update_state()` for backward compatibility. Forward all params to `backend.apply_params()`.

### JR-ML-DEP-021 — 5.1 Current State.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 360-364)

### JR-ML-API-053 — 5.1 Docker Compose Issues.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 260-272)

**Detail**:

| DD-DC-01 | **High**   | **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` points to `/run/secrets/juniper_data_api_k

### JR-ML-UI-033 — 5.1 juniper-canopy changes (Step 2.3).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 107-128)

**Detail**:

- ExecStart=/opt/miniforge3/envs/JuniperPython/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050

### JR-ML-SEC-152 — 5.1 juniper-cascor.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 120-134)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` not implemented — No topology changes WS   | `src/api/websocket/messages.py:72`                                                | Defined and exported, no production callers. Only used in tests

### JR-ML-API-054 — 5.1 juniper-cascor.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 107-118)

**Detail**:

| BUG-CC-01 | **MEDIUM** | `create_topology_message()` is dead code — topology changes never broadcast via WS | `src/api/websocket/messages.py:72`                                                | Defined and exported but zero production callers. Only used in tests

### JR-ML-SEC-153 — 5.1 Strengths.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 455-464)

**Detail**:

1. **Clean separation of concerns**: Each repository has a single, well-defined responsibility

### JR-ML-OBS-076 — 5.1 User-facing primary SLIs (release-blocking, 5).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 276-286)

**Detail**:

| 3.1 | Canopy dashboard availability | `99.5%` | 30d rolling | `CanopyDashboardAvailabilityFastBurn` (page) / `CanopyDashboardAvailabilitySlowBurn` (ticket) | Computable; log-only-effective dur

### JR-ML-OBS-077 — 5.2 Internal-supporting SLIs (graphed-only, 8).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 286-310)

**Detail**:

| 4.1 | Worker heartbeat freshness | `< 30s` per worker | n/a (instant) | Computable post juniper-cascor#188 (`WorkerRegistryCollector` ships `juniper_cas

### JR-ML-OBS-078 — 5.2 juniper-canopy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 134-145)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 118-130)

**Detail**:

| BUG-CN-01 | **HIGH**   | `_stop.clear()` race in `_perform_reset()` — outside lock      | `src/demo_mode.py:1617`             | Second call site at L1617 is outside the lock block (lock only covers L1615-1616)                                    |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-154 — 5.2 juniper-data.service (Step 2.1).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 128-178)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data.service`

### JR-ML-SEC-155 — 5.2 Kubernetes/Helm Issues.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 272-281)

**Detail**:

| DD-K8S-01 | **Medium** | `values.yaml:306`     | Redis `auth.enabled: false` — no authentication.

### JR-ML-OBS-079 — 5.2 Option C: Output Training Callback.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 505-521)

**Detail**:

**Effort**: 1-2 days | **Repo**: juniper-cascor

### JR-ML-TEST-022 — 5.2 Per-Application Release Steps.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 364-375)

**Detail**:

1. Create git tag: `git tag -a v<VERSION> -m "Release v<VERSION>"`

### JR-ML-OBS-080 — 5.2 Requirements for K8s Support.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 364-385)

**Detail**:

## 6. Client & Worker Analysis

### JR-ML-UI-034 — 5.2 Weaknesses.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 464-472)

**Detail**:

1. **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creates unnecessary latency and server load.

### JR-ML-OBS-081 — 5.3 Architecture Diagram: WebSocket Message Flow.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 472-492)

**Detail**:

## 6. Risk Assessment and Guardrails

### JR-ML-ARCH-234 — 5.3 `DemoMode.apply_params()` (`demo_mode.py`).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 310-314)

**Detail**:

Extend to accept and store all new `nn_*` and `cn_*` keyword arguments. Unknown keys should be stored and accessible but not cause errors.

### JR-ML-UI-035 — 5.3 juniper-data-ctl (Step 2.4).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 184-195)

**Detail**:

**New file**: `juniper-data/scripts/juniper-data-ctl`

### JR-ML-DEP-022 — 5.3 Post-Release.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 375-386)

**Detail**:

- Update parent CLAUDE.md with new version numbers

### JR-ML-SEC-156 — 5.3 Security.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 281-292)

**Detail**:

| DD-SEC-02 | **Medium** | Cascor port bound to 0.0.0.0 (see DD-DC-04).        |

### JR-ML-UI-036 — 5.4 Canopy Progress Indicators.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 534-543)

**Detail**:

**Effort**: 2 days | **Repo**: juniper-canopy

### JR-ML-SEC-157 — 5.4 juniper-cascor.service (Step 2.2).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 195-245)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor.service`

### JR-ML-OBS-082 — 5.4 Observability Issues.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 292-300)

**Detail**:

| DD-OBS-01 | **High**   | AlertManager config exists but is never deployed (see DD-DC-02).                                  |

### JR-ML-UI-037 — 5.5 juniper-cascor-ctl (Step 2.5).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 253-263)

**Detail**:

**New file**: `juniper-cascor/scripts/juniper-cascor-ctl`

### JR-ML-TRAIN-059 — 5.5 Option A: Candidate Progress Queue.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 543-556)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-cascor

### JR-ML-SEC-158 — 5.5 Test Coverage Gaps.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 300-311)

**Detail**:

| TST-01 | **Medium** | No Helm chart tests in CI (`helm lint` only in pre-commit, not CI).                                                                                                         |

### JR-ML-UI-038 — 5.6 juniper-all.target (Step 2.6).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 263-298)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all.target`

### JR-ML-SEC-159 — 5.6 Scripts/Automation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 311-324)

**Detail**:

| DD-SCR-01 | **Low**  | `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency. |

### JR-ML-API-055 — 5.7 juniper-all-ctl (Step 2.6).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 298-310)

**Detail**:

**New file**: `juniper-ml/scripts/juniper-all-ctl`

### JR-ML-API-056 — 5.8 Plant/chop --systemd mode (Step 2.8).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_SYSTEMD_PHASE2_PLAN_2026-04-06.md` (lines 310-353)

**Detail**:

if [[ "${1:-}" == "--systemd" ]]; then

### JR-ML-API-057 — 6. Phase 3: Interface Contract Mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 133-134)

### JR-ML-SEC-160 — 6.1 juniper-data-client / juniper-cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 385-396)

**Detail**:

**No startup/shutdown/orchestration changes needed.** These libraries are consumers, not producers.

### JR-ML-OBS-083 — 6.1 P5-RC-18: Typed Backend Contract.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 619-649)

**Detail**:

**Effort**: 3-5 days | **Repo**: juniper-canopy

### JR-ML-SEC-161 — 6.2 Guardrails.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 505-523)

### JR-ML-SEC-162 — 6.2 juniper-canopy — Code Quality.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 175-193)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 144-158)

**Detail**:

| CLN-CN-01 | **P2**   | `theme-table` CSS class not yet implemented                        | No `.theme-table` in any CSS file — conditional `is_dark` styling used instead    | S      |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-OBS-084 — 6.2 juniper-canopy.json (18 panels, version 3, title "JuniperCanopy").

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 330-360)

**Detail**:

Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +

### JR-ML-TRAIN-060 — 6.2 Medium: 503 Not Retried (XREPO-02 — confirmed STILL PRESENT).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 340-345)

**Detail**:

**File**: `juniper-cascor-client/constants.py:31`

### JR-ML-OBS-085 — 6.2 P5-RC-14 + P5-RC-05: WebSocket Consumption.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 649-657)

**Detail**:

**Effort**: 3-4 days | **Repo**: juniper-canopy

### JR-ML-TEST-023 — 6.2 Radio Button Sub-field Pattern.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 385-414)

**Detail**:

html.P("Network Growth Triggers:", className="mb-1 fw-bold"),

### JR-ML-OBS-086 — 6.3 juniper-cascor.json (22 panels, version 3, title "JuniperCascor").

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 360-400)

**Detail**:

Categories: 5 RED panels, 5 training panels (sessions, hidden units,

### JR-ML-API-058 — 6.3 KL-1: Dataset Data in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 657-664)

**Detail**:

**Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy

### JR-ML-TRAIN-061 — 6.3 Medium: No FakeCascorControlStream (XREPO-03 — confirmed STILL MISSING).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 345-349)

**Detail**:

`juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for `CascorControlStream`. Consumers testing WebSocket control (e.g., `set_params`) cannot use the testing subpackage.

### JR-ML-OBS-087 — 6.4 juniper-data.json (17 panels, version 3, title "JuniperData").

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 400-424)

**Detail**:

Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

### JR-ML-TRAIN-062 — 6.4 Medium: Protocol Constants Alignment is Manual.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 349-353)

**Detail**:

Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`. Wave 5 verified alignment, but **no automated CI check exists**. A cascor protocol change could silently break worker connectivity.

### JR-ML-DEP-023 — 6.5 Low: Version Header Drift (Multiple Repos).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 353-363)

**Detail**:

| Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |

### JR-ML-SEC-163 — 6.6 High: Docker Infrastructure Gaps (juniper-deploy).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 363-374)

**Detail**:

1. **AlertManager service missing** from docker-compose.yml but referenced by Prometheus

### JR-ML-API-059 — 7. Phase 4: Discrepancy Identification.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 150-151)

### JR-ML-TEST-024 — 7.1 Breaking Changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 414-423)

### JR-ML-API-060 — 7.1 Health Check Consistency.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 414-424)

**Detail**:

**Issue**: Inconsistent endpoint availability. All services should implement the full set: `/v1/health` (basic), `/v1/health/live` (liveness), `/v1/health/ready

### JR-ML-TRAIN-063 — 7.1 juniper-cascor-client — All Planned Work ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 374-381)

**Detail**:

| Hardcoded values refactor → `constants.py` | ✅ Complete (126 lines, 330 test constants)           |

### JR-ML-TEST-025 — 7.2 Circular Dependency Risk.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 423-431)

**Detail**:

The `sync_multi_node_checkboxes` callback has components as both Input and Output. This is safe because:

### JR-ML-TRAIN-064 — 7.2 juniper-cascor-worker — All Planned Work ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 381-392)

**Detail**:

| Hardcoded values refactor → `constants.py`                 | ✅ Complete (~70 replacements) |

### JR-ML-OBS-088 — 7.2 MWMBR burn-rate pairs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 456-472)

**Detail**:

| 3.1 Canopy dashboard availability | `CanopyDashboardAvailabilityFastBurn` | `CanopyDashboardAvailabilitySlowBurn` |

### JR-ML-DEP-024 — 7.2 Port Assignments.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 424-434)

**Detail**:

**Issue**: juniper-cascor uses port 8201 in host mode and Docker published port, but 8200 internally. The `get_cascor_*.bash` scripts hardcode 8201. Documentati

### JR-ML-API-061 — 7.2 Short-Term (Medium).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 533-549)

**Detail**:

5. **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network visualization redraws when weights change during

### JR-ML-UI-039 — 7.3 Conda Environment Mapping.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 434-444)

**Detail**:

**Resolved**: Previously, `juniper_plant_all.bash` used `/opt/miniforge3/envs/JuniperCanopy/bin/python` for all services. Fixed in commit `03aec86` — each service

### JR-ML-API-062 — 7.3 Performance.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 431-439)

### JR-ML-DATA-019 — 7.4 `absent_over_time(...) == 0` inertness guards.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 483-496)

**Detail**:

| `CascorPendingTasksSaturated` (`alert_rules.yml:1050`) | `juniper_cascor_pending_tasks` | The guard was originally placed because the gauge had not yet been bridged from the cascor coordinator to Pr

### JR-ML-API-063 — 7.4 Backward Compatibility.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 439-448)

**Detail**:

| `/api/state` response         | Old fields missing               | Always provide defaults via `.get()` with `TrainingConstants` fallbacks      |

### JR-ML-DATA-020 — 7.4 juniper-data-client — Constants Refactor ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 402-409)

**Detail**:

| Hardcoded values refactor (~89 values → `constants.py`) | ✅ Complete        |

### JR-ML-OBS-089 — 7.4 Logging.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 444-453)

### JR-ML-API-064 — 8. Phase 5: Comprehensive Documentation.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 177-178)

### JR-ML-OBS-090 — 8.1 Automated Tests.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 291-302)

**Detail**:

pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures)

### JR-ML-SEC-164 — 8.1 docker-compose (`juniper-deploy/prometheus/prometheus.yml`).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 496-513)

**Detail**:

| `prometheus` | `localhost:9090` | 15s (global default) | 10s | `/metrics` | `deployment=docker-compose`; per-job `service=prometheus`, `environment=docker` |

### JR-ML-OBS-091 — 8.1 Phases Now Complete.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 237-248)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 192-203)

**Detail**:

| A-SDK    | `CascorControlStream.set_params()` with `command_id` | ✅ Complete                                     |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-065 — 8.1 Priority Matrix.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 468-489)

**Detail**:

| Health-check-based startup in `juniper_plant_all.bash` | High   | Low     | **P0**   | **Resolved** (commit `03aec86`)           |

### JR-ML-TRAIN-065 — 8.1 Unit Tests - Layout Verification.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 460-471)

### JR-ML-API-066 — 8.2 High (Fix Soon).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 442-452)

**Detail**:

| 6 | juniper-deploy | Add AlertManager service to docker-compose.yml                                           |

### JR-ML-OBS-092 — 8.2 Kubernetes (`juniper-deploy/k8s/helm/juniper/templates/*-servicemonitor.yaml`).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 513-539)

**Detail**:

Three ServiceMonitor templates: `data-servicemonitor.yaml`,

### JR-ML-DATA-021 — 8.2 Phases Still Incomplete.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 248-257)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 203-216)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-165 — 8.2 Risk Assessment.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 489-504)

**Detail**:

## 9. Development & Tooling Recommendations

### JR-ML-UI-040 — 8.2 Unit Tests - Callback Handlers.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 471-492)

### JR-ML-API-067 — 8.3 Integration Tests.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 492-503)

**Detail**:

| `DemoMode.apply_params()` accepts all new params  | Backend integration |

### JR-ML-API-068 — 8.3 Medium (Address in Next Sprint).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 452-468)

**Detail**:

| 10 | juniper-data          | Use `hmac.compare_digest()` for API key comparison (SEC-01)    |

### JR-ML-OBS-093 — 8.4 Existing Tests Requiring Updates.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 503-522)

**Detail**:

| `test_convergence_layout.py`         | Update for removed `convergence-enabled-checkbox`, new radio group        |

### JR-ML-SEC-166 — 8.4 Low (Backlog).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 468-487)

**Detail**:

| 21 | All 5 repos    | Bump AGENTS.md and file header versions to match `pyproject.toml` |

### JR-ML-API-069 — 9. Phase 6: Remediation Planning.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 206-207)

### JR-ML-DEP-025 — 9.1 Approach A: Incremental Fix (Recommended).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 504-529)

**Detail**:

Fix the existing `juniper_plant_all.bash` and `juniper_chop_all.bash` scripts with health checks, error handling, and configurability. Add missing systemd units and worker deployment config.

### JR-ML-OBS-094 — 9.2 Approach B: Unified CLI Tool (juniper-ctl).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 529-564)

**Detail**:

**Risk**: Medium. New code means new bugs. Conda activation from Python subprocess is notoriously fragile.

### JR-ML-SEC-167 — 9.2 Phase 5: Observability & Hardening — INCOMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 289-299)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 225-235)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-OBS-095 — 9.3 Approach C: systemd-First + Makefile Enhancement.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 564-591)

**Detail**:

Standardize on systemd user services for host-mode and enhance the juniper-deploy Makefile for container mode. Remove the bash orchestration scripts.

### JR-ML-PERF-012 — 9.3 Inhibit rules.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 569-574)

### JR-ML-UI-041 — A.1 Startup Scripts.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 818-831)

**Detail**:

| `util/juniper_plant_all.bash`    | juniper-ml     | Start all (host)    | Active (overhauled, commit `03aec86`) |

### JR-ML-DEP-026 — A.2 Container/Deploy Files.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 831-846)

**Detail**:

| `docker-compose.yml`                  | juniper-deploy | Primary orchestration | Active     |

### JR-ML-SEC-168 — A.3 Health Check Scripts.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 846-855)

**Detail**:

| `scripts/health_check.sh`         | juniper-deploy | Full stack health          |

### JR-ML-OBS-096 — A.4 CasCor Query Utilities.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 855-866)

**Detail**:

| `util/get_cascor_status.bash`       | juniper-ml | `/v1/training/status`           |

### JR-ML-OBS-097 — A.5 Configuration Files.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 866-880)

**Detail**:

| `.env.example`                  | juniper-deploy | Full config template    |

### JR-ML-API-070 — A.6 Application Entry Points.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 880-895)

**Detail**:

| `juniper_data/__main__.py`     | juniper-data          | `python -m juniper_data` |

### JR-ML-TRAIN-066 — Adam Optimizer Pathology: fix Adam optimizer pathology issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_07_ADAM_OPTIMIZER_PATHOLOGY.md` (lines 1-44)

### JR-ML-WS-153 — Adapter→cascor auth = HMAC first-frame, NOT X-Juniper-Role header.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 47-47)

**Notes**:

Settled position C-10 from R3-03 table; cross-round consensus consolidation

### JR-ML-TEST-026 — Add integration test for Canopy demo mode toggle with juniper_canopy_demo_mode_active metric.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 51-52)

**Detail**:

R3.2: Toggle demo mode; assert metric reflects within one update tick.

### JR-ML-TEST-027 — Add live integration test for juniper-data dataset generation with metrics assertion.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 47-49)

**Detail**:

R3.1: POST /v1/datasets, scrape /metrics, assert juniper_data_dataset_generations_total counter and duration histogram.

### JR-ML-OBS-098 — Add phase="input" and phase="candidate" emission sites in cascor training_step_duration_seconds.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 169-178)

**Detail**:

G6 - training_step_duration_seconds only emits phase="output" despite SLO design intent of three phases.
Add input/candidate emission sites at corresponding training stages.

### JR-ML-TEST-028 — Add replay buffer overflow test for CasCor with eviction verification.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md` (lines 57-59)

**Detail**:

R3.5: Drive API_METRICS_BUFFER_SIZE + 1 updates; assert oldest evicted, newest retained, no exception.

### JR-ML-OBS-099 — Additional Work Completed (not in original plan).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 404-418)

**Detail**:

| GIL contention test fix | 04db7e6 | Rewrote flaky training loop tests to use thread.join instead of polling |

### JR-ML-TOOL-002 — Algorithm Enhancements.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 323-330)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 259-266)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-169 — Analyze juniper-deploy public release feasibility: dependencies, security, CI/CD readiness.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_DEPLOY_GO_PUBLIC_ANALYSIS_2026-05-09.md` (lines 1-50)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-API-071 — API-01: Health `status` Value Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5133-5148)

### JR-ML-API-072 — API-02: Health Response Schema Diverges.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5151-5165)

### JR-ML-API-073 — API-03: Canopy FSM Lacks Auto-Reset from FAILED/COMPLETED on START.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5168-5182)

### JR-ML-API-074 — API-04: FakeClient State Constants Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5185-5189)

### JR-ML-API-075 — API-05: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5192-5207)

### JR-ML-API-076 — API-06: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5210-5214)

### JR-ML-API-077 — API-07: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5217-5221)

### JR-ML-API-078 — API-08: `set_params` Includes Extraneous `type:command` Field.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5224-5232)

### JR-ML-API-079 — API-09: HTTPException Errors Bypass ResponseEnvelope.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5235-5249)

### JR-ML-ARCH-235 — Async route audit follow-up: ensure all storage/network I/O wrapped in asyncio.to_thread().

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/FOLLOWUP_ASYNC_ROUTE_AUDIT.md` (lines 1-50)

### JR-ML-OPS-005 — Audit and update Juniper SOPS (Standard Operating Procedures) documentation.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SOPS_AUDIT_2026-03-02.md` (lines 1-100)

### JR-ML-SEC-170 — `AuditLogger` and `WorkerMetrics` counters lack thread-safety.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 523-541)

### JR-ML-ARCH-236 — Background CascorControlStream supervisor task in canopy adapter.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 447-473)

### JR-ML-UI-042 — CAN-000: Periodic Updates Pause When Apply Parameters Active.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1990-1994)

### JR-ML-UI-043 — CAN-003: Retain Candidate Pool Data Per Node Addition.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2000-2004)

### JR-ML-UI-044 — CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1912-1926)

### JR-ML-UI-045 — CAN-CRIT-002: Save/Load Snapshot in Adapter — Blocked on `/v1/snapshots/*` API.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1929-1943)

### JR-ML-UI-046 — CAN-DEF-008: Advanced 3D Node Interactions.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1980-1983)

### JR-ML-UI-047 — CAN-HIGH-005: Remote Worker Status Dashboard.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1946-1960)

### JR-ML-TRAIN-067 — Candidate Quality Decay: address candidate quality degradation in long training runs.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_02_CANDIDATE_QUALITY_DECAY.md` (lines 1-40)

### JR-ML-WS-154 — Canopy adapter hot/cold parameter splitting (WebSocket vs REST).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 293-352)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-WS-155 — Canopy control buttons must resolve orphaned commands via state event arrival (fallback to explicit timeout).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 350-400)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1307-1340)

**Detail**:

Track pending commands in JS map by command_id.
Button marked "pending verification" until command_response arrives OR a matching state event lands.
If orphaned (no response after explicit timeout, ~5s), resolve as success-assumed per RISK-13 mitigation.
Prevents UI deadlock if server handles command but response WS frame is dropped.

**Notes**:

RISK-13. Phase D (Day 11). Playwright test: test_orphaned_command_resolves_via_state_event.

### JR-ML-UI-048 — Canopy dashboard must display WebSocket connection status badge (connected green, reconnecting yellow, offline red).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 350-400)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1108-1120)

**Detail**:

New src/frontend/components/connection_indicator.py: html.Div(id='ws-connection-indicator').
Clientside callback reads ws-connection-status.data → toggles class connected-green / reconnecting-yellow / offline-red / demo-gray.
CSS rules in assets/styles.css.

**Notes**:

GAP-WS-26 (P2). Also mirrors demo mode parity (RISK-08, GAP-WS-33). Phase B (Day 9).

### JR-ML-DATA-022 — Canopy metrics normalization must maintain dual-format backward compatibility (nested + flat metric keys).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1371-1382)

**Detail**:

Phase H: test test_normalize_metric_produces_dual_format before any audit PR.
test_normalize_metric_nested_topology_present, test_normalize_metric_preserves_legacy_timestamp_field.
Write consumer audit doc listing every consumer of nested vs flat keys across canopy frontend.
Explicit recommendation: do NOT remove either format without landing this test first.

**Notes**:

RISK-01. Phase H (Day 12) regression gate. Must not ship Phase B without test in place.

### JR-ML-UI-049 — Canopy must configure Dash assets_url_path with content-hash query string to bust browser cache on new JS.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 550-600)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1364-1370)

**Detail**:

Configure assets_url_path with query-string content hash so browsers pick up new JS without hard refresh.
Verify: load dashboard; view source; assets/websocket_client.js?v=<sha> visible.
Test: test_asset_url_includes_version_query_string (Playwright).
Should have shipped with Day 8 Phase B per R0-06 §3.6; if not, defer to Day 12.
Do NOT ship Phase B without Phase I in production—stale websocket_client.js will not understand seq.

**Notes**:

Phase I (Day 8 or 12). R0-01 step 30. Acceptance criterion: browsers have <5 day old code in production.

### JR-ML-OBS-100 — Canopy must observe set_params latency separately for WebSocket and REST transports.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 200-250)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1225-1230)

**Detail**:

Histogram canopy_set_params_latency_ms with labels transport="websocket"|"rest".
Buckets: {5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000} ms.
WebSocket: read _client_latency_ms from ack envelope.
REST: measure time.monotonic() delta.

**Notes**:

Per R0-04 §7. Cross-transport comparison informs Phase C feature flag decision (§5.6 ack-vs-effect).

### JR-ML-ARCH-237 — Capture open issues post-V38 release: training stalls, convergence, network growth constraints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/POST_V38_OPEN_ISSUES_PLAN_2026-05-03.md` (lines 1-50)

### JR-ML-ARCH-238 — CAS-006: Auto-Snap Best Network.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2446-2450)

### JR-ML-WS-156 — Cascor SetParamsRequest has extra=forbid; canopy adapter routes unclassified keys to REST.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 46-46)

**Notes**:

Settled position C-09 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-171 — CasCor-Side Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 895-907)

**Detail**:

| `cascade_add` correlation hardcoded to 0.0 | Cosmetic — does not affect topology display |

### JR-ML-ARCH-239 — CC-01: `_recv_loop` Catches Bare `Exception`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3656-3670)

### JR-ML-DOC-003 — CC-04: `set_params()` Method Not Documented in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3673-3687)

**Notes**:

[v2 ARCH→DOC re-bucket]

### JR-ML-ARCH-240 — CC-05: CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3690-3698)

### JR-ML-ARCH-241 — CC-06: `command()` Never Sends `type` Field.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3701-3708)

### JR-ML-ARCH-242 — CC-07: NpzFile Resource Leak in data-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3711-3725)

### JR-ML-WS-157 — CC-08: WebSocket Auto-Reconnection Not Implemented.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3728-3742)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-243 — CC-13: `_recv_loop` Silently Drops Non-Correlated Server Messages.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3762-3776)

### JR-ML-ARCH-244 — CC-14: `_handle_response()` Calls `response.json()` Unconditionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3779-3793)

### JR-ML-SEC-172 — CC-15: No TLS/SSL Configuration Support on WS Streams.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3796-3810)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-ARCH-245 — CC-16: `FakeCascorClient.wait_for_ready()` Returns True Immediately.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3813-3827)

### JR-ML-ARCH-246 — CC-17: `FakeCascorClient.wait_for_ready()` Missing `self._lock`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3830-3844)

### JR-ML-ARCH-247 — CFG-01: `torch` Imported but Missing from canopy Dependencies.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4883-4897)

### JR-ML-ARCH-248 — CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4900-4914)

### JR-ML-ARCH-249 — CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4917-4931)

### JR-ML-ARCH-250 — CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4934-4948)

### JR-ML-ARCH-251 — CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4951-4965)

### JR-ML-ARCH-252 — CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4968-4982)

### JR-ML-ARCH-253 — CFG-07: Port 8200 vs 8201 Confusion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4985-4999)

### JR-ML-ARCH-254 — CFG-08: Rate Limiting Defaults Differ Across Services.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5002-5016)

### JR-ML-ARCH-255 — CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5019-5041)

### JR-ML-ARCH-256 — CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5044-5058)

### JR-ML-ARCH-257 — CFG-13: `python-dotenv` in canopy Core Deps but Never Imported.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5061-5075)

### JR-ML-TRAIN-068 — CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5078-5092)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-258 — CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5095-5109)

### JR-ML-TEST-029 — Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 69-69)

**Notes**:

Settled position C-32 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-069 — CI-01: cascor-client CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4643-4657)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-070 — CI-02: cascor-worker CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4660-4664)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-259 — CI-03: juniper-deploy CI Runs ZERO Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4667-4681)

### JR-ML-SEC-173 — CI-04: Missing Weekly security-scan.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4684-4695)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-TRAIN-071 — CI-05: Missing lockfile-update.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4698-4709)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TEST-030 — CI-06: juniper-deploy No Coverage Configuration.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4712-4723)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-ARCH-260 — CI-07: Inconsistent GitHub Actions Versions Across Repos.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4726-4737)

### JR-ML-SEC-174 — CI-SEC-01: No Weekly Security Scan for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4838-4842)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-SEC-175 — CI-SEC-02: No Security Scanning in juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4845-4856)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-TOOL-003 — CLN-CC-01: Delete Legacy `remote_client/` Directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1317-1343)

### JR-ML-TOOL-004 — CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1346-1361)

### JR-ML-TOOL-005 — CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1364-1378)

### JR-ML-TOOL-006 — CLN-CC-04: Enable mypy Strict Mode.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1381-1395)

### JR-ML-TOOL-007 — CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1398-1412)

### JR-ML-TOOL-008 — CLN-CC-06: Remove "Roll" Concept in CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1415-1421)

### JR-ML-TOOL-009 — CLN-CC-07: Candidate Factory Refactor.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1424-1430)

### JR-ML-TOOL-010 — CLN-CC-08: Remove Commented-Out Code Blocks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1433-1439)

### JR-ML-TOOL-011 — CLN-CC-09: Line Length Reduction to 120 Characters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1442-1448)

### JR-ML-TOOL-012 — CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1451-1473)

### JR-ML-TOOL-013 — CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1476-1490)

### JR-ML-TOOL-014 — CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1493-1507)

### JR-ML-TOOL-015 — CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1510-1524)

### JR-ML-TOOL-016 — CLN-CC-14: Empty `# TODO :` Headers in 18+ Files.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1527-1541)

### JR-ML-TOOL-017 — CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1544-1558)

### JR-ML-TOOL-018 — CLN-CN-01: `theme-table` CSS Class Never Implemented.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1563-1588)

### JR-ML-TOOL-019 — CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1591-1605)

### JR-ML-TOOL-020 — CLN-CN-03: Performance Test Suite Minimal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1608-1622)

### JR-ML-TOOL-021 — CLN-CN-04: JuniperData-Specific Error Handling Missing.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1625-1639)

### JR-ML-TOOL-022 — CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1642-1657)

### JR-ML-TOOL-023 — CLN-CN-06: Re-enable Remaining MyPy Disabled Codes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1660-1674)

### JR-ML-TOOL-024 — CLN-CN-07: Real Backend Path Test Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1677-1691)

### JR-ML-TOOL-025 — CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1694-1708)

### JR-ML-TOOL-026 — CLN-CN-09: main.py Coverage Gap (84% vs 95% Target).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1711-1725)

### JR-ML-TOOL-027 — CLN-CN-10: `main.py` Is 2,543 Lines — Second God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1728-1742)

### JR-ML-TOOL-028 — CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1745-1759)

### JR-ML-TOOL-029 — CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1762-1776)

### JR-ML-TOOL-030 — CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1779-1793)

### JR-ML-TOOL-031 — CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1796-1810)

### JR-ML-TOOL-032 — CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1815-1829)

### JR-ML-TOOL-033 — CLN-JD-02: `FakeDataClient.close()` Destroys Data.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1832-1846)

### JR-ML-TOOL-034 — CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1849-1863)

### JR-ML-SEC-176 — Code Reference Validation.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 880-886)

**Detail**:

Every line number, code snippet, and factual claim about the codebase was verified against the current source files. No shifted, wrong, or missing references found.

### JR-ML-WS-158 — command_response has NO seq field; /ws/control has no replay buffer.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 39-39)

**Notes**:

Settled position C-02 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-101 — Complete baseline metrics and observability inventory analysis.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ANALYSIS_2026-04-25.md` (lines 1-100)

**Notes**:

BASELINE phase of METRICS-MON program.

### JR-ML-TRAIN-072 — Consequence.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 245-251)

### JR-ML-UI-050 — Consequence.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 385-389)

**Detail**:

In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden units. The visualization appears as a standard feedforward network rather than a cascade correlation network.

### JR-ML-OBS-102 — Consequence.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 485-489)

### JR-ML-TEST-031 — Consolidated regression remediation plan.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/CONSOLIDATED_REMEDIATION_PLAN.md` (lines 1-50)

### JR-ML-TEST-032 — Contract-test pytest marker contract runs on every PR, NOT nightly.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 71-71)

**Notes**:

Settled position C-34 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-073 — Convergence Timing: optimize convergence detection timing.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_04_CONVERGENCE_TIMING.md` (lines 1-46)

### JR-ML-WS-159 — Correlation field is command_id, NOT request_id.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 38-38)

**Notes**:

Settled position C-01 from R3-03 table; cross-round consensus consolidation

### JR-ML-TEST-033 — COV-01: Deploy Tests Exist but Zero Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4740-4744)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TEST-034 — COV-02: Canopy No Per-Module Coverage Gate.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4747-4758)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TEST-035 — COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4761-4772)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-UI-051 — Current State.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 655-663)

**Detail**:

| **JuniperCanopy** | YAML config + env vars  | `src/conf/app_config.yaml` + `${VAR:default}` substitution |

### JR-ML-OBS-103 — Current State.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 19-31)

**Detail**:

The Training Parameters card (`dashboard_manager.py` lines 417-512) contains a flat list of 6 inputs:

### JR-ML-ARCH-261 — CW-01: `receive_json()` Doesn't Catch JSONDecodeError.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3906-3920)

### JR-ML-PERF-013 — CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3923-3937)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-ARCH-262 — CW-03: No Integration Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3940-3954)

### JR-ML-ARCH-263 — CW-04: Timeout Error Sends `candidate_uuid: ""` Instead of Actual UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3957-3971)

### JR-ML-ARCH-264 — CW-05: Dynamic Import `from candidate_unit.candidate_unit import CandidateUnit`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3974-3996)

### JR-ML-ARCH-265 — CW-06: `receive_json()` in Registration Path — No JSONDecodeError Catch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3999-4006)

### JR-ML-ARCH-266 — CW-07: No Validation of `tensor_manifest` Keys Against Received Binary Frames.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4009-4023)

### JR-ML-PERF-014 — CW-08: Top-Level `import torch` — First-Task Latency.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4026-4040)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-ARCH-267 — DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles".

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3849-3853)

### JR-ML-ARCH-268 — DC-02: GENERATOR_MOON = "moon" — No Server Generator.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3856-3860)

### JR-ML-ARCH-269 — DC-03: Missing Constants for 5 Server Generators.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3863-3867)

### JR-ML-DATA-023 — DC-04: `FakeDataClient` Masks Generator Name Bugs.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3870-3884)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-DATA-024 — DC-05: `FakeDataClient` Missing Lifecycle Methods.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3887-3901)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-UI-052 — Debounce lives in Dash clientside callback, NOT SDK.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 66-66)

**Notes**:

Settled position C-29 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-177 — Decision boundary computation runs synchronously in async handler, blocking event loop.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 913-931)

### JR-ML-UI-053 — Demo mode must maintain parity with live WebSocket mode (connection status, metrics updates).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 450-500)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1116-1130)

**Detail**:

In src/backend/demo_mode.py, set window.cascorWS status to {connected: true, mode: "demo"} via set_props or peek path.
Dashboard ws-connection-status reflects "demo".
Connection indicator badge shows gray "demo" state.

**Notes**:

RISK-08, GAP-WS-33. Phase B (Day 9). Demo users see same UI feedback as live users.

### JR-ML-UI-054 — Dependency Graph (Runtime).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 76-85)

### JR-ML-SEC-178 — DEPLOY-01: Docker Secret Name/Path Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3335-3349)

**Notes**:

[v2 ARCH→SEC re-bucket]

### JR-ML-OBS-104 — DEPLOY-02: AlertManager Service Missing from docker-compose.yml.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3352-3366)

**Notes**:

[v2 ARCH→OBS re-bucket]

### JR-ML-ARCH-270 — DEPLOY-04: K8s Canopy Missing Service URL Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3386-3397)

### JR-ML-UI-055 — Description.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 532-536)

**Detail**:

The current topology visualization is exclusively **node-centric** — showing nodes and their connections as a graph. A **weight-centric** view would display the raw weight arrays from CasCor, showing the actual numerical structure of the network.

### JR-ML-UI-056 — Design and implement integrated dashboard combining Canopy and CasCor metrics.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/INTEGRATED_DASHBOARD_PLAN.md` (lines 1-100)

### JR-ML-OBS-105 — Design and implement worker heartbeat protocol for CasCor distributed training.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md` (lines 1-50)

### JR-ML-OBS-106 — Document all metrics: Prometheus exposition format, cardinality limits, label guidelines.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_METRICS_DOCUMENTATION.md` (lines 1-50)

### JR-ML-DOC-004 — Documentation audit: standardize link formats, enforce cross-repo resolution, validate all links in CI.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/documentation/DOCUMENTATION_AUDIT_AND_UPGRADE_PLAN.md` (lines 1-50)

### JR-ML-SEC-179 — Dual auth mechanisms — WebSocket endpoints lack middleware-level enforcement and rate limiting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 294-330)

### JR-ML-OBS-107 — emitted_at_monotonic: float on every /ws/training broadcast envelope.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 78-78)

**Notes**:

Settled position C-41 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-074 — Enable Canopy to connect to external CasCor instances with connection orchestration.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_EXTERNAL_CASCOR_PLAN.md` (lines 1-100)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Approved for implementation.

### JR-ML-OPS-006 — Error-budget burn-rate rule operationally binding.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 79-79)

**Notes**:

Settled position C-42 from R3-03 table; cross-round consensus consolidation

### JR-ML-TOOL-035 — Establish 6-type prompt classification (Handoff, Task, Template, Planning, Audit, Infrastructure) with boilerplate analysis.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/PROMPT_ANALYSIS_AND_AUTOMATION_PLAN.md` (lines 326-466)

### JR-ML-OPS-007 — Establish PyPI publish procedure: OIDC trusted publishing, semantic versioning, automated changelog.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/PYPI-PUBLISH-PROCEDURE.md` (lines 1-50)

### JR-ML-API-080 — Evaluation.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 663-713)

**Detail**:

The mixed approach (Pydantic Settings for two services, YAML for one) creates inconsistency. All three services are FastAPI-based, so Pydantic `BaseSettings` is the natural fit.

### JR-ML-OBS-108 — Evidence.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 111-142)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 215-245)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 437-457)

**Detail**:

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-UI-057 — Evidence.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 361-385)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 479-485)

**Detail**:

**File**: `juniper-canopy/src/backend/demo_backend.py`

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-025 — Evidence.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 505-522)

### JR-ML-OBS-109 — Execute metrics and monitoring code review across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md` (lines 1-100)

**Notes**:

PROPOSED phase; awaiting kickoff.

### JR-ML-API-081 — Existing Infrastructure.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 85-97)

**Detail**:

- **Docker Compose**: Partial — `JuniperCanopy/conf/docker-compose.yaml` defines `juniper-data`, `juniper_canopy`, and `redis` services; `JuniperCascor/conf/docker-compose

### JR-ML-ARCH-271 — Feature flag use_websocket_set_params (default False) for Phase C rollout control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 403-432)

### JR-ML-OBS-110 — Fix.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 457-473)

**Detail**:

logger.warning("Failed to extract network topology: %s: %s", type(e).__name__, e)

### JR-ML-API-082 — Fix.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 489-499)

**Detail**:

**Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more comprehensive solution.

### JR-ML-UI-058 — Fix.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 522-532)

**Detail**:

The `get_dataset_data()` method (line 733) already demonstrates the correct pattern: `except Exception as e` with a warning log. Apply the same pattern to the methods listed above that handle data transformation (especially `get_decis

### JR-ML-DOC-005 — Fix 17 broken markdown links in DEVELOPER_CHEATSHEET.md - 12 self-referencing and 5 missing intra-repo files.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 207-244)

**Detail**:

Category B (12 links): self-referencing cross-repo links should be direct relative:
- ../juniper-ml/notes/SOPS_USAGE_GUIDE.md → SOPS_USAGE_GUIDE.md
- ../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md → SOPS_IMPLEMENTATION_PLAN.md
- ../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md → SOPS_AUDIT_2026-03-02.md
- ../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md → SECRETS_MANAGEMENT_ANALYSIS.md
- ../juniper-ml/notes/pypi-publish-procedure.md → pypi-publish-procedure.md
- ../juniper-ml/AGENTS.md → ../AGENTS.md (5 instances)

Category C (5 links): missing files never created, should be removed or redirected:
- Line 491: plan_7.5_7.6_dependency_management.md (remove)
- Line 575: STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md (remove)
- Line 720: PYPI_PUBLISH_PROCEDURE.md → pypi-publish-procedure.md (rename fix)
- Line 720: PYPI_PUBLISH_PLAN_3_PACKAGES.md (remove)
- Line 755: WORKTREE_IMPLEMENTATION_PLAN.md (remove or redirect to WORKTREE_SETUP_PROCEDURE.md)

### JR-ML-UI-059 — Fix Approaches.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 389-431)

**Detail**:

#### Approach A: Add cascade connections to demo backend (RECOMMENDED)

### JR-ML-TOOL-036 — Fix broken check_object_pickleability function in utils.py:238 which uses dill not in dependencies.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3580-3590)

**Detail**:

CLN-CC-10: utils.py:238 imports and uses `dill` library which is not in project dependencies.
Function is broken. Fix by either adding dill to deps or refactoring to use pickle only.

### JR-ML-DOC-006 — Fix semantic error in SECURITY_AUDIT_PLAN.md line 845 - correct deep relative path to ../CLAUDE.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 246-264)

**Detail**:

Category D false-negative: ../../../CLAUDE.md resolves to wrong document via repo-root fallback.
Should be ../CLAUDE.md to reference repo's own CLAUDE.md (symlink to AGENTS.md) containing the same #worktree-procedures-mandatory--task-isolation section.

### JR-ML-SEC-180 — `force_sequential_training` autouse fixture masks all multiprocessing bugs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1002-1022)

### JR-ML-SEC-181 — Future (If Scale Demands).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 735-750)

**Detail**:

1. **Docker Compose demo profile**: Run real CasCor with auto-start training for stakeholder demos.

### JR-ML-OBS-111 — GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy /api/ws_latency + histogram).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 57-57)

**Notes**:

Settled position C-20 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-182 — Hidden unit forward pass recomputed redundantly every output training epoch.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 841-859)

### JR-ML-SEC-183 — High Issues.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 53-67)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 355-373)

**Detail**:

**H-ML-1: CI dependency-docs job references wrong path** (`ci.yml:244`)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-083 — High Issues.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 131-142)

**Detail**:

**H-JD-1: 60+ commits since v0.5.0 not in CHANGELOG**

### JR-ML-DATA-026 — High Issues.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 187-195)

**Detail**:

**H-JDC-1: Real client HTTP tests missing for 6 methods**

### JR-ML-TRAIN-075 — High Issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 228-239)

**Detail**:

**H-JCC-1: CHANGELOG missing v0.2.0 and v0.3.0 entries**

### JR-ML-UI-060 — High Priority.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 356-364)

**Detail**:

| `cascade_add` correlation           | NETWORK_TOPOLOGY_DISPLAY_ANALYSIS | Hardcoded `0.0` instead of actual best candidate correlation             |

### JR-ML-ARCH-272 — HSK-01: 3 Broken Symlinks in canopy `notes/development/`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2881-2895)

### JR-ML-ARCH-273 — HSK-02: `src/remote_client/` Directory Still Exists.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2898-2902)

### JR-ML-ARCH-274 — HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2905-2909)

### JR-ML-ARCH-275 — HSK-04: 32 Test Files with Hardcoded `sys.path.append`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2912-2916)

### JR-ML-TRAIN-076 — HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2919-2933)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-DOC-007 — HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2936-2940)

**Notes**:

[v2 ARCH→DOC re-bucket]

### JR-ML-TRAIN-077 — HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2943-2947)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TEST-036 — HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2950-2954)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-TRAIN-078 — HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2957-2982)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TOOL-037 — HSK-10: `scripts/test.bash` Outdated/Non-Functional.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2985-3010)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-ARCH-276 — HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3013-3028)

### JR-ML-TEST-037 — HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3031-3045)

**Notes**:

[v2 ARCH→TEST re-bucket]

### JR-ML-ARCH-277 — HSK-13: 169 Hardcoded ThemeColors Remain in canopy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3048-3062)

### JR-ML-ARCH-278 — HSK-14: `resume_session.bash` Contains Hardcoded Session UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3065-3087)

### JR-ML-TOOL-038 — HSK-15: `util/global_text_replace.bash` Is a No-Op.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3090-3112)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-039 — HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3115-3129)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-040 — HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3132-3146)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-TOOL-041 — HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3149-3163)

**Notes**:

[v2 ARCH→TOOL re-bucket]

### JR-ML-ARCH-279 — HSK-19: Stale Files in Repo Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3166-3180)

### JR-ML-ARCH-280 — HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3183-3198)

### JR-ML-ARCH-281 — HSK-21: `wake_the_claude.bash:53` Stale TODO Comment.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3201-3215)

### JR-ML-ARCH-282 — HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3218-3232)

### JR-ML-TRAIN-079 — HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3235-3249)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-TRAIN-080 — HSK-24: Unused Constants in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3252-3277)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-API-084 — Immediate (No Infrastructure Changes).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 721-727)

**Detail**:

1. **Refactor Canopy's backend branching**: Define a `BackendProtocol` that both `DemoMode` and `CascorServiceAdapter` implement. Eliminate scattered `if demo_mode_instance:` checks in `main.py

### JR-ML-PERF-015 — Implement performance optimizations from training analysis.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_PERFORMANCE_ANALYSIS_2026-03-20.md` (lines 1-100)

**Notes**:

Throughput and latency improvements.

### JR-ML-TOOL-042 — Implement phased prompt automation: Phase 1 snippets (1 day), Phase 2 discovery scripts (2 days), Phase 3 template rendering (2-3 days).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/PROMPT_ANALYSIS_AND_AUTOMATION_PLAN.md` (lines 1081-1150)

### JR-ML-SEC-184 — Implement secrets management strategy for Juniper ecosystem (analysis-driven).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/SECRETS_MANAGEMENT_ANALYSIS.md` (lines 1-100)

### JR-ML-TOOL-043 — Implement thread handoff procedure: context transfer, worktree state, verification commands.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-50)

### JR-ML-OBS-112 — Implement unified health probe semantics and status code propagation across Juniper services.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md` (lines 1-50)

**Notes**:

R1.2 phase of METRICS-MON program.

### JR-ML-WS-160 — Implement WebSocket remote worker infrastructure: /ws/v1/workers endpoint, WorkerRegistry, WorkerCoordinator, binary protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 852-890)

**Design**:

Phase 1b WebSocket endpoint with JWT auth, binary message frames, task assignment/result collection, worker heartbeat management.

### JR-ML-SEC-185 — Integration tests rely on fixed `time.sleep()` for async training synchronization.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 951-969)

### JR-ML-TRAIN-081 — Investigate V38 grow-network performance; characterize scaling limits and convergence behavior.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/V38_GROW_NETWORK_INVESTIGATION_PLAN_2026-05-02.md` (lines 1-50)

### JR-ML-SEC-186 — Issue Remediations, Section 15 — juniper-data-client.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 506-556)

**Detail**:

#### DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles"

### JR-ML-SEC-187 — Issue Remediations, Section 9.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 343-392)

**Detail**:

#### 5.1: AlertManager Receivers — Placeholders Only

### JR-ML-UI-061 — Issue Summary Table.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 42-54)

**Detail**:

| **OI-5** | LOW | Quality | Initial sync topology never pushed to Dash store | juniper-canopy | **FIXED** (2beea5c) — fallback in `ServiceBackend.get_network_topology()` |

### JR-ML-OBS-113 — Issues Previously Identified and Now Resolved.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 794-809)

**Detail**:

| RC-1: Stale editable install | DATASET_DISPLAY_BUG_ANALYSIS.md | Fixed: `get_dataset_data()` added to client, version bumped to 0.3.0 |

### JR-ML-SEC-188 — Issues Previously Identified and Still Outstanding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 809-859)

**Detail**:

| response.ok returns bad default | DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md Phase 3/5 | OI-1 |

### JR-ML-DATA-027 — JD-PERF-01: Sync `generator.generate()` Blocks Event Loop.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3534-3538)

### JR-ML-DATA-028 — JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3541-3555)

### JR-ML-DATA-029 — JD-PERF-03: `list_versions` Loads All Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3558-3569)

### JR-ML-DATA-030 — JD-PERF-04: No Connection Pooling for Postgres.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3572-3586)

### JR-ML-DATA-031 — JD-PERF-05: Readiness Probe Filesystem Glob.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3589-3593)

### JR-ML-DATA-032 — JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3485-3507)

### JR-ML-DATA-033 — JD-SEC-02: API Key Comparison Not Constant-Time (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3510-3518)

### JR-ML-DATA-034 — JD-SEC-03: Rate Limiter Memory Unbounded (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3521-3529)

### JR-ML-SEC-189 — JUNIPER_WS_ALLOWED_ORIGINS=* explicitly REFUSED by the parser.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 67-67)

**Notes**:

Settled position C-30 from R3-03 table; cross-round consensus consolidation

### JR-ML-DOC-008 — Keep AGENTS.md synchronized with project structure.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md` (lines 1-100)

**Notes**:

Drift analysis identifies documentation gaps.

### JR-ML-OBS-114 — Key Findings.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 38-51)

**Detail**:

1. **Host-mode startup (`juniper_plant_all.bash`)** -- overhauled in commit `03aec86`. Now uses `wait_for_health()` polling, `check_port_available()`, `validate_conda_env()`, per-service Python binaries, `set -euo pipefail`, `trap clean

### JR-ML-OPS-008 — Kill switch MTTR ≤5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 76-76)

**Notes**:

Settled position C-39 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-062 — KL-1: Dataset Scatter Plot Empty in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1963-1977)

### JR-ML-PERF-016 — Latency instrumentation hooks for set_params round-trip measurement.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 539-590)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-TEST-038 — Latency tests are recording-only in CI (latency_recording marker); strict assertions local-only.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 72-72)

**Notes**:

Settled position C-35 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-063 — Low Issues.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 78-89)

**Detail**:

- `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`)

### JR-ML-API-085 — Low Issues.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 150-156)

**Detail**:

- `traces_sample_rate=1.0` sends all Sentry traces

### JR-ML-DATA-035 — Low Issues.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 201-209)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 390-397)

**Detail**:

- `FakeDataClient.close()` doesn't prevent subsequent operations

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-OBS-115 — Low Issues.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 255-265)

**Detail**:

- `response.json()` not protected against non-JSON 200 responses

### JR-ML-TEST-039 — Low Issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 317-324)

**Detail**:

- Sigmoid derivative evaluates `torch.sigmoid` twice per call

### JR-ML-DATA-036 — Medium Issues.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 67-78)

**Detail**:

**M-ML-1: `test_worktree_cleanup.py` not run in CI** (`ci.yml:109-110`)

### JR-ML-OBS-116 — Medium Issues.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 142-150)

**Detail**:

**M-JD-1: Sentry PII enabled by default** (`observability.py:139`)

### JR-ML-API-086 — Medium Issues.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 195-201)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 239-255)

**Detail**:

**M-JDC-1: docs/REFERENCE.md stale** — version header says 0.3.1, missing batch and versioning documentation

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TRAIN-082 — Medium Issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 306-317)

**Detail**:

**M-JCW-1: No task execution timeout** (`worker.py:201`)

### JR-ML-SEC-190 — Medium Issues.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 373-390)

**Detail**:

**M-JDP-1: `redis:7-alpine` floating minor version tag**

### JR-ML-TEST-040 — Multiple regression analysis documents for training defects (01-09).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_ANALYSIS_03_2026-04-02.md` (lines 1-50)

### JR-ML-DEP-027 — Near-Term (Docker Compose Adoption).

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 727-735)

**Detail**:

1. **Create ecosystem-level `docker-compose.yml`**: Define all 3 services + Redis with health-gated dependency ordering. Place at `Juniper/docker-compose.yml` (or `Juniper/juniper/docker-compose.yml`).

### JR-ML-TRAIN-083 — Network Architecture.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 330-337)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 266-273)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-UI-064 — NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 58-58)

**Notes**:

Settled position C-21 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-117 — Observability-before-behavior rule: metrics + panels + alerts land BEFORE behavior change.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 75-75)

**Notes**:

Settled position C-38 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-161 — One-resume-per-connection rule (second resume → close 1003).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 62-62)

**Notes**:

Settled position C-25 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-084 — Output Weight Initialization: improve output layer weight init.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_05_OUTPUT_WEIGHT_INIT.md` (lines 1-38)

### JR-ML-UI-065 — Overview.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 41-48)

**Detail**:

- **Version**: 0.3.0 (pyproject.toml)

### JR-ML-API-087 — Overview.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 108-115)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 169-176)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 221-228)

**Detail**:

- **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile)

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-WS-162 — Overview.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 280-287)

**Detail**:

- **Tests**: 101 passed, 80.13% coverage (barely meets threshold)

### JR-ML-SEC-191 — Overview.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 343-350)

**Detail**:

- **Version**: 0.2.0 (documented in AGENTS.md; no formal release)

### JR-ML-OBS-118 — P0 success metric: canopy_rest_polling_bytes_per_sec reduced >90% vs baseline.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 74-74)

**Notes**:

Settled position C-37 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-119 — P1 — Operationally meaningful (alerts inert, dashboards wrong, SLI math broken).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 370-380)

**Detail**:

| **3.2** | juniper-deploy | Alertmanager `tickets` receiver is a placeholder | Open small PR wiring real notification config (webhook/email/Slack); decide

### JR-ML-SEC-192 — Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 63-63)

**Notes**:

Settled position C-26 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-120 — Per-phase entry plans.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 448-454)

**Detail**:

- [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](../legacy/METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md)

### JR-ML-OBS-121 — Per-repo histogram bucket rationale.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 740-746)

### JR-ML-PERF-017 — PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4109-4123)

### JR-ML-PERF-018 — PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4126-4140)

### JR-ML-PERF-019 — PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4143-4157)

### JR-ML-PERF-020 — PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4075-4089)

### JR-ML-PERF-021 — PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4092-4106)

### JR-ML-PERF-022 — PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4160-4182)

### JR-ML-PERF-023 — PERF-JD-02: High-Cardinality Prometheus Labels.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4185-4193)

### JR-ML-TRAIN-085 — Phantom Inter-Cascade Training Phase: remove 1-step/epoch phantom training phase.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_01_PHANTOM_TRAINING_PHASE.md` (lines 30-48)

### JR-ML-OBS-122 — Phase 0-cascor (seq/replay/resume) — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 302-315)

**Detail**:

| Send timeout (0.5s, GAP-WS-07 quick-fix)                               | ✅                                              |

### JR-ML-TRAIN-086 — Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 49-49)

**Notes**:

[v2 ARCH→TRAIN re-bucket] Settled position C-12 from R3-03 table; cross-round consensus consolidation

### JR-ML-DEP-028 — Phase 1:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 198-398)

### JR-ML-OBS-123 — Phase 1 Tests.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 736-760)

**Detail**:

mock_requests.get.return_value = Mock(ok=False, status_code=503)

### JR-ML-UI-066 — Phase 1: Foundation (Constants + Settings).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 522-528)

**Detail**:

1. Update `canopy_constants.py` with all new and changed constants

### JR-ML-DEP-029 — Phase 2:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 451-651)

### JR-ML-SEC-193 — Phase 2 (metrics UI enhancements).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 168-178)

**Detail**:

| Task 1A: Validation loss/accuracy overlay traces | ❌ NOT STARTED | —       |

### JR-ML-TRAIN-087 — Phase 2 Tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 760-775)

**Detail**:

# Setup: create network with 2+ hidden units

### JR-ML-UI-067 — Phase 2: Demo Backend Cascade Connections (OI-3) — COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 658-672)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-UI-068 — Phase 2: systemd & Service Management (P1) -- COMPLETED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 732-754)

**Detail**:

**Goal**: Provide OS-native service management for all three core services.

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

### JR-ML-DATA-037 — Phase 3 Tests.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 775-794)

**Detail**:

# test_websocket_topology_push.py — New integration test

### JR-ML-SEC-194 — Phase 3: Worker Deployment & Container Integration — ✅ COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 258-270)

**Detail**:

| 3.1  | `juniper-cascor-worker/Dockerfile`                            | ✅ Implemented                                           |

### JR-ML-ARCH-283 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 206-239)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 205-238)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 107-162)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 233-265)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-DEP-032 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

### JR-ML-DEP-033 — Phase 5:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

### JR-ML-SEC-195 — Phase 5: Observability & Hardening (P2-P3) -- Medium-Term.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 804-818)

**Detail**:

| 5.1  | Configure AlertManager receivers (Slack/email)   | `juniper-deploy/alertmanager/alertmanager.yml` | Low             |

### JR-ML-SEC-196 — Phase 5: Observability & Hardening — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 285-302)

**Detail**:

| 5.1  | Configure AlertManager receivers                 | ❌      |

### JR-ML-SEC-197 — Phase 5: Quality Improvements (OI-5, OI-6) — COMPLETE.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 706-736)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-API-088 — Phase 5: Tests.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 555-563)

**Detail**:

1. Update all broken existing tests

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

### JR-ML-TRAIN-088 — Phase A-SDK — ✅ IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 315-322)

**Detail**:

| `CascorControlStream.set_params()` with `command_id` correlation | ✅ In `ws_client.py` |

### JR-ML-WS-163 — Phase B ships behind two flags: enable_browser_ws_bridge + disable_ws_bridge.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 51-51)

**Notes**:

Settled position C-14 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-284 — Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 50-50)

**Notes**:

Settled position C-13 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-198 — Phase B-pre-a (security) — ⚠️ PARTIALLY IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 322-330)

### JR-ML-WS-164 — Phase C (P2 priority): Canopy adapter hot/cold param split; hot→WS via `command_id`; REST fallback; flag-off default.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 706-789)

**Detail**:

Canopy adapter (`cascor_service_adapter.py`) splits params: hot set (learning_rate, candidate_learning_rate, correlation_threshold,
candidate_pool_size, max_hidden_units) → `/ws/control` via `set_params` (1.0 s timeout); cold set → REST PATCH (permanent, never deprecated).
`_HOT_CASCOR_PARAMS` + `_COLD_CASCOR_PARAMS` frozensets. `apply_params(**params)` dispatcher calls `_apply_params_hot()` (WS) or `_apply_params_cold()` (REST).
`_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)`. On timeout/error: **unconditional fallback to REST PATCH** (no retries).
Unclassified keys (not in `_HOT` or `_COLD`) → REST with WARNING log.
`_control_stream_supervisor`: background task maintaining `/ws/control` connection, reconnects on disconnect,
sends HMAC first-frame (wired in B-pre-b, confirmed here).
Settings: `use_websocket_set_params: bool = False` (default), `ws_set_params_timeout: float = 1.0`.
Debounce (250 ms) lives in Dash clientside slider callback, not SDK.
Latency instrumentation: `canopy_set_params_latency_ms{transport, param_name}` histogram (labels: `rest`, `ws`).
Tests: 14+ entries. Routes hot to WS when flag on, to REST when off. Routes cold to REST always.
Falls back to REST on WS timeout + connection error. Defaults unclassified to REST with warning. Slider debounce 250 ms.
Set_params latency histogram exported for both transports. Slider drag routes correct per flag. Control stream supervisor
reconnects + sends HMAC. Concurrent correlation test passes.
Documenation: `juniper-canopy/notes/runbooks/ws-set-params-flip.md` (how to flip, monitor, revert).

**Design**:

Single PR (P10). No cascor-side change (Phase 0-cascor's `command_id` echo handles it).
Adapter refactor centralizes param routing logic. REST fallback unconditional (no retries per R1-05 §4.22).

**Notes**:

Entry: Phase A-SDK on PyPI, Phase B in main + staging. Optional: Phase C can skip until Phase D if timeline tight
(Phase D is gated on B-pre-b, not C). Exit: 14+ tests pass, latency histogram has both transport labels,
flag-off by default (regression check), manual drag test works. Rollback: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.
Canary: 7 days production >=0 orphaned commands before flag flip PR.

### JR-ML-ARCH-285 — Phase C flag use_websocket_set_params=False default; 6 hard flip gates.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 65-65)

**Notes**:

Settled position C-28 from R3-03 table; cross-round consensus consolidation

### JR-ML-PERF-024 — Phase E (conditional): Per-client pump tasks + bounded queues + backpressure policy matrix.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 867-921)

**Detail**:

Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded queues.
Per-client `asyncio.Queue` bounded at 256 (configurable via `Settings.ws_per_client_queue_size`).
Per-client `_pump_task` created on connect, cancelled on disconnect.
Policy dispatch: `drop_oldest_progress_only` (default) drops oldest progress events (metrics, candidate_progress);
closes 1013 for state-bearing events (state, topology, cascade_add, connection_established).
`block` (legacy): synchronously blocks broadcast until queue drains.
`close_slow`: closes 1008 if queue full >5s.
Setting: `ws_backpressure_policy = "drop_oldest_progress_only"` (env: `JUNIPER_WS_BACKPRESSURE_POLICY`).
Tests: 5 entries. Default drops oldest for progress, block policy works when opted-in, close_slow closes stalled,
slow client doesn't block fast clients, terminal state events not dropped.
Observability: `cascor_ws_dropped_messages_total{policy, reason}`, `cascor_ws_per_client_queue_depth_histogram`.

**Design**:

Single PR (P13). Overrides source-doc default (`block`) with production-safer `drop_oldest_progress_only`.
Progress events droppable, state events flow or close (prevent silent loss).

**Notes**:

Conditional phase: enters if RISK-04 (backpressure issue) observed in production. Entry: Phase 0-cascor in main.
May not ship if Phase B load testing shows slow-client impact acceptable. Exit: 5 tests green, load test (50 clients,
1 slow) → fast clients <=200ms p95, dropped counters visible. Priority P2 (default), conditional entry makes it potentially deferred.

### JR-ML-PERF-025 — Phase E default backpressure = drop_oldest_progress_only.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 52-52)

**Notes**:

Settled position C-15 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-165 — Phase F (optional): Application-level `ping`/`pong` heartbeat, dead-connection detection, uncapped reconnect.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 924-973)

**Detail**:

Cascor `/ws/training` + `/ws/control` emit `ping` every 30 s (JSON `{type: "ping", ts: float}`).
JS replies `pong` within 5 s. Dead-connection detection: no `pong` within 10 s of `ping` → close 1006.
GAP-WS-31: lift 10-attempt reconnect cap to unlimited, max interval 60 s once cap reached.
Jitter formula: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))` (explicit, prevents NaN).
Tests: 4 entries. Heartbeat reciprocity, dead-connection detection, uncapped attempts, jitter formula no NaN.

**Design**:

Single PR (P14) across cascor + canopy. Application-level vs framework-level (uvicorn) detects TCP half-open faster.

**Notes**:

Entry: Phase B in main. Priority P2 (default), small phase (0.25-1.0 day). Exit: 4 tests pass,
manual firewall drop → dead conn within 40 s, 48h soak no NaN delays. Rollback: revert P14 (10 min TTF).

### JR-ML-TEST-041 — Phase G (integration tests): 15 cascor `/ws/control` set_params tests via FastAPI TestClient + contract lane.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 976-1029)

**Detail**:

Tests in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`.
15 entries: happy path, whitelist filters unknown keys, init_output_weights literal validation (rejects injection),
oversized frame 64 KB rejected (4 KB per B-pre-a), network error returns error, unknown command error,
malformed JSON closes 1003, origin rejected, unauthenticated rejected, rate limit after 10 cmds,
bad init_output_weights rejected, concurrent command correlation (2 clients, echo routing correct),
set_params during training applies on next epoch (ack vs effect), echoes command_id, command_response no seq.
Contract-lane test: `test_fake_cascor_message_schema_parity` (runs in both cascor + canopy `contract` lane).
No design sketch needed (test-only phase).

**Notes**:

Entry: Phase 0-cascor + Phase B-pre-b in main. Tests via FastAPI TestClient (no SDK dependency).
Exit: all 15 pass, `pytest -m contract` lane green in cascor + canopy. Rollback: n/a (test-only).
Dedup candidate with R3-03.

### JR-ML-DOC-009 — Phase H: `_normalize_metric` dual-format regression test + consumer audit + CODEOWNERS hard gate.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 1032-1077)

**Detail**:

Phase does NOT refactor `_normalize_metric`; locks in dual-format contract (flat keys + nested keys) with regression gate.
Tests in `juniper-canopy/src/tests/unit/test_normalize_metric.py`.
Regression: `test_normalize_metric_produces_dual_format` asserts BOTH nested (`{training: {loss: 0.5}}`) AND flat (`{training.loss: 0.5}`) on output.
Additional tests: nested format unchanged since Phase H, flat format unchanged since Phase H.
Consumer audit document: `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` enumerates every consumer:
frontend MetricsPanel, CandidateMetricsPanel, Prometheus `/api/metrics`, WebSocket drain, debug logger, test fixtures.
CODEOWNERS: `juniper-canopy/src/backend/normalize_metric.py @<project-lead>` + `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>`.
`.github/CODEOWNERS` branch protection enforces owner review.

**Design**:

Single PR (P16). Test-only phase; refactoring deferred to follow-up (gated on audit findings).

**Notes**:

Entry: Phase B in main. Exit: regression tests pass, CODEOWNERS enforced (test via PR without owner review → must block),
consumer audit reviewed + merged. Rollback: revert P16 (10 min TTF); CODEOWNERS rule disappears.
Note: Phase H is NOT a behavior-change gate; it's a documentation + regression-gate phase.

### JR-ML-OBS-124 — Phase R4: Best-practice and ergonomic improvements for observability.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md` (lines 1-50)

**Notes**:

Follows test-coverage closure (R3).

### JR-ML-OBS-125 — Phase R5: SLO/SLI catalog, scrape manifests, Grafana dashboards, and alerting.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md` (lines 1-50)

**Notes**:

Final phase of METRICS-MON program.

### JR-ML-UI-069 — Phases C–H — ❌ NOT STARTED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 341-356)

**Detail**:

## 12. Items Not Yet Implemented

### JR-ML-TRAIN-089 — Post-Reset Desynchronization: fix desync after model reset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_10_POST_RESET_DESYNC.md` (lines 1-38)

### JR-ML-OBS-126 — Primary.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 409-415)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) §6 — residual follow-ups (juniper-ml#192)

### JR-ML-OBS-127 — Primary catalog / program docs.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 721-728)

**Detail**:

- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (juniper-ml#195 / #194)

### JR-ML-SEC-199 — Prometheus metrics unbounded label cardinality on `endpoint` label.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 362-395)

### JR-ML-WS-166 — PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5252-5266)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-UI-070 — rAF coalescer must be scaffolded but disabled by default in Phase B; revisit in Phase B+1 if frame pressure detected.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 50-120)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1475-1485)

**Detail**:

R0-01 §7 disagreement #1: ship scaffolded but DISABLED (wins over arch doc §5.5 which says ship enabled).
Implement _scheduleRaf = function() {} (noop) in ws_dash_bridge.js.
Leave full code structure in commented-out block for easy Phase B+1 enablement.
D1 resolution: rAF coalescer disabled.

**Notes**:

Disagreement D1 per R1-04 §14. Revisit if §5.6 instrumentation shows frame pressure. Phase B (Day 8).

### JR-ML-UI-071 — rAF coalescer scaffolded but DISABLED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 53-53)

**Notes**:

Settled position C-16 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-286 — Refactor CascorControlStream with background recv task and correlation map.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 254-272)

### JR-ML-TEST-042 — Regression analysis and remediation for model training defects.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_ANALYSIS_2026-04-03.md` (lines 1-50)

### JR-ML-DEP-038 — Release Order Risks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 386-394)

### JR-ML-DATA-038 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 95-108)

**Detail**:

1. Create retroactive git tags for v0.2.1 and v0.3.0

### JR-ML-DEP-039 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 156-169)

**Detail**:

1. Synchronize all version references to target release (0.6.0 recommended given post-0.5.0 features)

### JR-ML-API-089 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 209-221)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 265-280)

**Detail**:

1. Bump version to 0.4.0 (new public API surface)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-SEC-200 — Remediation Summary.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 330-343)
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 397-411)

**Detail**:

1. Write CHANGELOG v0.3.0 entry (WebSocket rewrite, auth_token rename, TLS support, etc.)

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-TOOL-044 — Remove 9 stale local import traceback statements from cascade_correlation.py by uncomenting top-level import at line 64.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3568-3580)

**Detail**:

CLN-CC-03: 9 local `import traceback` statements scattered in cascade_correlation.py
across lines 2270, 2804, 3775, 3840 and other files. Consolidate via uncommented 
line 64 top-level import. Effort: 30 minutes.

### JR-ML-TOOL-045 — Remove committed .ipynb_checkpoints directories from repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3590-3600)

**Detail**:

CLN-CC-12: Jupyter notebook checkpoint directories committed to repository in 
src/cascade_correlation/.ipynb_checkpoints/, src/candidate_unit/, src/
These should be in .gitignore. Effort: 10 minutes.

### JR-ML-ARCH-287 — Remove module-level sys.path.append in cascade_correlation.py:69.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3600-3610)

**Detail**:

CLN-CC-13: sys.path manipulation at module level in cascade_correlation.py:69
is an anti-pattern. Refactor to use proper imports or package structure.

### JR-ML-WS-167 — Replay buffer = 1024 entries, env-configurable via JUNIPER_WS_REPLAY_BUFFER_SIZE.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 42-42)

**Notes**:

Settled position C-05 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-168 — replay_buffer_capacity added to connection_established.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 44-44)

**Notes**:

Settled position C-07 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-201 — `RequestBodyLimitMiddleware` relies solely on `Content-Length` header — bypassable with chunked encoding.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 427-459)

### JR-ML-TRAIN-090 — Residual Variance Collapse: address residual variance collapse in training.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_09_RESIDUAL_VARIANCE_COLLAPSE.md` (lines 1-46)

### JR-ML-OBS-128 — Resolve duplicated observability types (DependencyStatus, ReadinessResponse) across repos.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (lines 1-50)

**Notes**:

Establish shared observability library.

### JR-ML-WS-169 — REST fallback cadence during disconnect = 1 Hz.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 54-54)

**Notes**:

Settled position C-17 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-288 — Results.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 588-594)

**Detail**:

- **After deduplication**: ~85 unique items not present in v2.0.0

### JR-ML-WS-170 — Ring-bound enforced in the handler, NOT the drain callback.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 56-56)

**Notes**:

Settled position C-19 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-289 — RISK: Correctness: no seq gaps.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-TRAIN-091 — RISK: Correctness: no state loss.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-290 — RISK: Criterion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

### JR-ML-ARCH-291 — RISK: Observability: full pipe.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-292 — RISK: **P0: polling eliminated**.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-293 — RISK: Recovery: kill switches work.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-WS-171 — RISK: Security: CSWSH closed.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-ARCH-294 — ROBUST-01: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4574-4597)

### JR-ML-OBS-129 — Root Cause.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 107-111)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 207-215)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 433-437)

**Detail**:

`_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty dict flows into the NetworkVisualizer callback where the guard `topology_data.get("input_units", 0) == 0` evaluates to `True`, rendering an empty graph.

*Merged from 3 extraction candidates (slices: 3c-2b).*

### JR-ML-TRAIN-092 — Root Cause.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 357-361)
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 475-479)

**Detail**:

`demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections that are the defining featur

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-DATA-039 — Root Cause.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 501-505)

**Detail**:

Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other unexpected exceptions. This was the original vector for the dataset display bug (RC-2).

### JR-ML-WS-172 — SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 41-41)

**Notes**:

Settled position C-04 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-202 — Security Concerns.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 89-95)

**Detail**:

- `kill_all_pythons.bash`: Dangerous — kills all Python processes system-wide with `sudo kill -9`

### JR-ML-SEC-203 — Serialization & Validation (v3.0.0).

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 337-348)

### JR-ML-WS-173 — server_instance_id = programmatic key; server_start_time = advisory only.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 43-43)

**Notes**:

Settled position C-06 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-090 — Service Inventory.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 59-67)

**Detail**:

| **JuniperCascor** | 8200 | `python src/server.py`   | FastAPI + uvicorn        | Pydantic Settings (`JUNIPER_CASCOR_*` env vars)     |

### JR-ML-OBS-130 — Service Topology.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 37-59)

**Detail**:

│   Uses:             │     REST         │    Uses:             │

### JR-ML-WS-174 — set_params default timeout = 1.0 s.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 40-40)

**Notes**:

Settled position C-03 from R3-03 table; cross-round consensus consolidation

### JR-ML-TOOL-046 — Setup MCP server for Claude integration: Slack, Gmail, Google Calendar adapters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/MCP_SERVER_SETUP_PLAN.md` (lines 1-50)

### JR-ML-OBS-131 — Source of truth files (with current `origin/main` SHA).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 764-787)

**Detail**:

- `juniper-data/juniper_data/api/observability.py` (juniper-data `88149bf`)

### JR-ML-TRAIN-093 — Spiral Complexity: limit spiral depth and complexity growth.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_03_SPIRAL_COMPLEXITY.md` (lines 1-50)

### JR-ML-DOC-010 — Stabilize CI documentation link validation by implementing cross-repo link classification and worktree directory exclusion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 70-175)

**Detail**:

DEVELOPER_CHEATSHEET.md has 124 broken cross-repo links in CI:
- 107 Category A: cross-repo relative links (../juniper-data/..., etc)
- 12 Category B: self-referencing cross-repo (../juniper-ml/...)
- 5 Category C: missing intra-repo files
- 1 Category D: false-negative deep link

Phase 1: Implement --cross-repo flag with skip/warn/check modes; exclude .claude/worktrees from scanning.

**Design**:

Approach 1A: Add --cross-repo flag with three modes:
- skip (default in CI): skip cross-repo links, log count
- warn: report as warnings (non-blocking)
- check: validate as normal (for local with all repos)

_ECOSYSTEM_REPOS hardcoded set with 8 known repos.
_CROSS_REPO_PATTERN regex matches patterns.

**PRs**: juniper-ml PR

**Notes**:

Recommend Phase 1: CI stabilization with --cross-repo skip.
Phase 2: ecosystem-root discovery with fallback.
Phase 3: documentation content cleanup (Approach 2A hybrid links).

### JR-ML-SEC-204 — State machine enters irrecoverable terminal state after FAILED or COMPLETED without enforced reset.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 186-227)

### JR-ML-UI-072 — Step 2: Validate Existing Fixes.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 70-95)

**Detail**:

| B-5.1 | `_apply_parameters_handler` stores `"enabled" in (conv_enabled or [])` → correct boolean. No continuous sync. |

### JR-ML-OBS-132 — Step 4: Commit Strategy.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 146-154)

**Detail**:

1. **Phase 6 training improvements**: Constants, demo_mode algorithm changes, demo_backend, phase6 tests

### JR-ML-SEC-205 — Step 5: Update Plan Document.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 154-162)

**Detail**:

Add Phase 5.3 section to `notes/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` documenting:

### JR-ML-DEP-040 — Tally by severity.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 412-421)

### JR-ML-TRAIN-094 — Tanh Saturation: address tanh saturation issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_06_TANH_SATURATION.md` (lines 1-38)

### JR-ML-ARCH-295 — Target State.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 31-39)

**Detail**:

## 2. Component ID Registry

### JR-ML-TRAIN-095 — Task 3 (Topology).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 366-374)

**Detail**:

- Exact lines confirmed: 582 and 611 in cascor_service_adapter.py

### JR-ML-SEC-206 — `TaskDistributor` dual-path execution is serial, not concurrent.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 931-951)

### JR-ML-SEC-207 — Tests named for `grow_network` testing actually bypass it entirely.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1040-1058)

### JR-ML-SEC-208 — TOCTOU gap in `_check_stale_workers` between snapshot and deregistration.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 541-571)

### JR-ML-OPS-009 — Total effort: 13.5 expected engineering days / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 73-73)

**Notes**:

Settled position C-36 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-096 — TQ-01: 10+ Tests with No Assertions (cascor).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4775-4786)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-296 — TQ-02: 149 `time.sleep` Calls in canopy Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4789-4800)

### JR-ML-ARCH-297 — TQ-03: Worker Config Validation Tests with No Assertions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4803-4814)

### JR-ML-TRAIN-097 — TQ-04: 139 `hasattr` Guards in cascor Tests.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4817-4821)

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-ARCH-298 — TQ-05: 10 Unit Tests Import httpx (Integration-Level).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4824-4835)

### JR-ML-WS-175 — Two-phase registration via _pending_connections set.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 45-45)

**Notes**:

Settled position C-08 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-073 — UI Lock and Visualization: UI locking during training and visualization improvements.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_08_UI_LOCK_AND_VISUALIZATION.md` (lines 1-45)

### JR-ML-SEC-209 — Unvalidated `params` dict in `TrainingStartRequest` passed as `**kwargs` to `network.fit()`.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 395-427)

### JR-ML-UI-074 — v1.0.0–v2.0.0 Primary Sources.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 504-513)

**Detail**:

| 1 | `CONSOLIDATED_DEVELOPMENT_RECORD.md`  | `juniper-ml/notes/development/`     | 2026-04-17 | 91+ items from 16 source documents      |

### JR-ML-SEC-210 — V17/V18 cross-repo dispatch token setup: enable inter-repo CI workflows with OIDC trust.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/V17_V18_CROSS_REPO_DISPATCH_TOKEN_SETUP_2026-05-02.md` (lines 1-50)

### JR-ML-WS-176 — WebSocket fallback to REST for set_params on connection/timeout errors.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 354-382)

**Notes**:

[v2 ARCH→WS re-bucket]

### JR-ML-OBS-133 — Why This Causes the Blank After Hidden Unit Addition.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 142-152)

**Detail**:

When CasCor adds a hidden unit via `grow_network()`, there is a brief transient window where the network state is being reorganized (output weights resized, new unit installed). If the Canopy REST poll hits `/api/topology` during this window and receives a 503 (or timeout), the handler returns `{}`,

### JR-ML-API-091 — Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 77-77)

**Notes**:

Settled position C-40 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-075 — Work Unit 1: Worktree Developer Experience (HIGH).

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 41-83)

**Detail**:

**Impact**: Unblocks all worktree-based development workflows

### JR-ML-API-092 — Work Unit 3: Pre-Existing Test Failures (MEDIUM) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 129-144)

**Detail**:

**Issues**: 3A (9 failing tests in `test_api_state_endpoint.py`)

### JR-ML-OBS-134 — Work Unit 5: Code Cleanup — Remove Redundant Inline Styles (LOW) — IMPLEMENTED.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/REMAINING_ISSUES_REMEDIATION_PLAN.md` (lines 161-201)

**Detail**:

Removed all 13 `style={"backgroundColor": "#f8f9fa"}` attributes from `dbc.CardHeader` instances across 4 files. The CSS rule `.card-header { background-color: var(--bg-secondary) !important;

### JR-ML-SEC-211 — Worker `worker_id` is client-supplied with no server-side validation or uniqueness enforcement.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 490-523)

### JR-ML-OBS-135 — ws-metrics-buffer store shape = {events, gen, last_drain_ms}.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 55-55)

**Notes**:

Settled position C-18 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-212 — ws_security_enabled=True (positive sense), NOT disable_ws_auth.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 64-64)

**Notes**:

Settled position C-27 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-299 — XREPO-01: Generator Name `"circle"` vs Server's `"circles"`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2509-2524)

### JR-ML-ARCH-300 — XREPO-02: 503 Not in `RETRYABLE_STATUS_CODES`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2571-2586)

### JR-ML-ARCH-301 — XREPO-03: No `FakeCascorControlStream` — Testing Gap for WS Control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2589-2604)

### JR-ML-ARCH-302 — XREPO-04: Protocol Constants Alignment Is Manual.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2607-2629)

### JR-ML-ARCH-303 — XREPO-05: State Name Inconsistency — UPPERCASE vs Title-Case vs FSM Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2632-2646)

### JR-ML-ARCH-304 — XREPO-06: `epochs_max` Default Discrepancy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2649-2663)

### JR-ML-ARCH-305 — XREPO-07: `command()` vs `set_params()` Message Format Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2666-2681)

### JR-ML-ARCH-306 — XREPO-08: Three Distinct WS Message Formats.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2684-2692)

### JR-ML-ARCH-307 — XREPO-09: Client `create_dataset()` Missing `tags` and `ttl_seconds`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2695-2709)

### JR-ML-DATA-040 — XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2712-2726)

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-ML-ARCH-308 — XREPO-11: Client Retries Non-Idempotent Mutations (POST, DELETE).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2729-2743)

### JR-ML-ARCH-309 — XREPO-12: `y` Tensor Received but Never Used in Worker.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2746-2760)

### JR-ML-ARCH-310 — XREPO-13: Health Endpoint `status` Value Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2763-2771)

### JR-ML-ARCH-311 — XREPO-14: FakeClient State Constants Use Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2774-2789)

### JR-ML-ARCH-312 — XREPO-15: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2792-2800)

### JR-ML-ARCH-313 — XREPO-16: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2803-2818)

### JR-ML-ARCH-314 — XREPO-17: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2821-2836)

### JR-ML-OBS-136 — 3.6 TRAIN-ARCH-01 — Cascor mini-batch restoration.

**Status**: shipped  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 207-227)

**Detail**:

**Severity:** P3 (user-discretion) · **Owner repo:** juniper-cascor · **Status:** deferred

### JR-ML-DEP-041 — 3.8 R1.3.4-FLAG — Helm chart `worker.healthcheck.enabled` default flip.

**Status**: shipped  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 243-264)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-deploy · **Status:** deferred

### JR-ML-SEC-213 — P3 — Hygiene / future / aspirational.

**Status**: shipped  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 391-412)

**Detail**:

| **3.1** | juniper-deploy | SLO catalog calibration vs soak-window data | Schedule T+30d agent for 2026-06-02; open calibration PR if observed data warrant

### JR-ML-OBS-137 — 3.3 TRAIN-ARCH-01 cascor mini-batch restoration.

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 126-176)

**Detail**:

- **Status**: deferred (user explicitly paused at design-doc stage)

### JR-ML-TRAIN-098 — 3.7 R5.6-THROTTLE — Cascor 25-epoch emit throttle removal.

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 227-243)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** deferred

### JR-ML-SEC-214 — 4.2 CR-026: Server-Assigned Worker IDs.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 378-402)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED

### JR-ML-OBS-138 — Closing PRs (commit hashes verified against current `origin/main`).

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 746-764)

**Detail**:

| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix |

### JR-ML-SEC-215 — Issue Remediations, Section 10.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 392-428)

**Detail**:

All CasCor enhancement items are feature requests. Brief remediation approaches:

### JR-ML-DEP-042 — Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term ✅ COMPLETED.

**Status**: designed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 754-785)

**Detail**:

**Goal**: Enable containerized deployment of the distributed worker.

### JR-ML-OBS-139 — 2.2 Documents in `notes/`.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 82-105)

**Detail**:

| CANOPY_DASHBOARD_DISPLAY_FIXES.md          | 3 display issues (metrics, dataset, topology) | Issue 3 (output weights transposition): **FIXED** (committed in adapter). Issues 1-2: **FIXED** per CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md |

### JR-ML-OBS-140 — 3.9 R2-WORKER-DEDUP — juniper-cascor-worker contract-constant dedup.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 264-280)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor-worker · **Status:** deferred

### JR-ML-TRAIN-099 — 6.1 juniper-cascor — Stale Code Removal.

**Status**: deferred  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V3_VALIDATED.md` (lines 159-175)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS.md` (lines 130-144)

**Detail**:

| CLN-CC-02 | **P2**   | Delete stale `check.py` duplicate (600 lines) — copy of spiral_problem.py                        | `src/spiral_problem/check.py`                                                            | 10 min      |

*Merged from 2 extraction candidates (slices: 3c-2b).*

### JR-ML-API-093 — 7.3 The 25-epoch throttle caveat.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 472-483)

**Detail**:

annotation `description` blocks (`alert_rules.yml:751`, `:819`). The

### JR-ML-DEP-043 — 9.4 Recommended Approach.

**Status**: deferred  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 591-603)

**Detail**:

**Primary: Approach A (Incremental Fix)** with elements of Approach C for systemd units.

### JR-ML-OBS-141 — Defer full worker migration; adopt only R1.2 probe contract constants.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md` (lines 1-100)

**Notes**:

Decided: no full migration now. Use contract constants only.

### JR-ML-API-094 — Ecosystem-Wide Patterns.

**Status**: deferred  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 436-445)

**Detail**:

1. **No application has all git tags**: This is a systemic process gap. Releases are documented in changelogs but tags are not created, meaning GitHub releases and PyPI publishes may not ha

### JR-ML-SEC-216 — Phase 3: WebSocket Topology Push (OI-2) — COMPLETE.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 672-688)

**Detail**:

**Repos**: juniper-canopy only

### JR-ML-SEC-217 — Phase 4: Weight-Centric Topology Toggle (OF-1) — COMPLETE.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 688-706)

**Detail**:

**Repos**: juniper-canopy only (CasCor already returns raw weight-oriented format)

### JR-ML-SEC-218 — Worker security modules (mTLS, anomaly detection, rate limiting, audit) are not integrated into runtime.

**Status**: deferred  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 260-294)

### JR-ML-DEP-044 — 2.4 Recommendation.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_ARCHITECTURE_ANALYSIS.md` (lines 299-328)

**Detail**:

**Recommended approach: Layered strategy with Docker Compose as the primary orchestrator.**

### JR-ML-SEC-219 — 3.3 Release Description Documents.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 294-305)

**Detail**:

Draft release descriptions for each application (templates provided in the code review document). These should be refined and used as GitHub release notes.

### JR-ML-SEC-220 — 4.4 Docker Validation (juniper-deploy).

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/RELEASE_PREPARATION_PLAN_2026-04-08.md` (lines 337-351)

**Detail**:

**Sequence**: After Phase 4 validation

### JR-ML-API-095 — 9.2 juniper-cascor (Phase 4 only).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 341-348)

**Detail**:

| `src/api/lifecycle/manager.py` | Add `get_dataset_data()` method     |

### JR-ML-DATA-041 — 9.3 juniper-cascor-client (Phase 4 only).

**Status**: proposed  **Priority**: P3  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 348-354)

**Detail**:

| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

### JR-ML-DOC-011 — Define issue tracking template: structured fields for requirements, test cases, verification.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/templates/TEMPLATE_ISSUE_TRACKING.md` (lines 1-50)

### JR-ML-OPS-010 — Document and automate manual PyPI setup procedures.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_MANUAL_SETUP_STEPS.md` (lines 1-100)

**Notes**:

Manual steps should be automated in publishing pipeline.

### JR-ML-ARCH-315 — Future: Implement free-threading local tier when PyTorch supports free-threaded Python (Python 3.14+).

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 914-932)

### JR-ML-TOOL-047 — Implement V2 worktree cleanup procedure.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/WORKTREE_CLEANUP_V2_PLAN.md` (lines 1-100)

**Notes**:

Development workflow optimization.

### JR-ML-DOC-012 — Maintain cheatsheet mapping AGENTS.md sections to project/repo; enable rapid reference.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CHEATSHEET_SECTION_TO_PROJECT_MAPPING.md` (lines 1-50)

### JR-ML-DOC-013 — Maintain developer cheatsheet with current tooling and workflow procedures.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md` (lines 1-100)

**Notes**:

Living documentation; should be kept current.

### JR-ML-API-096 — Phase 4 (cross-repo dataset endpoint).

**Status**: proposed  **Priority**: P3  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 178-184)

**Detail**:

| Task 2 Phase 2: `GET /v1/dataset/data` endpoint in cascor | ❌ NOT STARTED |

### JR-ML-ARCH-316 — Phase 4: Callbacks.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 544-555)

**Detail**:

1. Add collapsible toggle callbacks (NN + CN sections)

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

### JR-ML-ARCH-317 — Phase 5:.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 242-263)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 241-262)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 165-187)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 268-323)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-318 — Phase 6:.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 190-220)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

### JR-ML-TOOL-048 — Phase I (folded into Phase B): Asset cache busting for `websocket_client.js` + `ws_dash_bridge.js`.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 1080-1099)

**Detail**:

Bump `assets_folder_snapshot` or equivalent query param in Dash config so browsers pick up new JS without hard refresh.
Included as deliverable MVS-FE-16 in Phase B (§6.3), not a standalone phase.
Verify via browser devtools that JS URL includes cache-bust query parameter changing on deploy.

**Design**:

Part of Phase B PR (P6). Ensures stale JS in browser cache doesn't cause mismatches with new protocol.

**Notes**:

Folded into Phase B per R1-05 §6.2. No independent gate. Rollback: revert cache-bust config (5 min TTF).
Priority P3 (folded, low-visibility change).

### JR-ML-OBS-142 — Plan post-R5 observability program enhancements.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md` (lines 1-100)

**Notes**:

After R5 completion; scope TBD.

### JR-ML-OPS-011 — Transfer all Juniper repositories and PyPI packages from pcalnon to OvertoadResearch GitHub organization.

**Status**: proposed  **Priority**: P3  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/PYPI_DEPLOYMENT_PLAN.md` (lines 339-400)

**Detail**:

Phase 5: Create OvertoadResearch org on GitHub/PyPI, transfer repos with URL redirects, update git remotes/SSH, add org as PyPI maintainer, update OIDC configs.

