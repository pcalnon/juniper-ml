# Requirements — status: designed

**Total entries**: 98

**By priority**: P0=5 | P1=68 | P2=18 | P3=7

**By category**: ARCH=40 | SEC=12 | OBS=11 | WS=11 | UI=11 | TRAIN=7 | DEP=4 | API=1 | TOOL=1

**By owner**: ml=94 | cas=3 | can=1

---

### JR-ML-OBS-003 — > **REVISION HISTORY**:.

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 574-619)

**Detail**:

> - 2026-04-10 first pass: typed contract landed (PR #140); P5-RC-05 marked DEFERRED

**Notes**:

[v3 brief repaired from cited content; was: '6.0 Phase 4 Execution Results (2026-04-10, REVISED)']

### JR-ML-OBS-004 — [x] Dashboard shows per-epoch loss during output training phases — `train_output_layer` callback wired in cascor `manager.py:237-248`; demo….

**Status**: designed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 556-574)

**Detail**:

- [x] Dashboard shows per-epoch loss during output training phases — `train_output_layer` callback wired in cascor `manager.py:237-248`; demo mode emits via `_emit_training_metrics()` (verified 2026-04-09)

**Notes**:

[v3 brief repaired from cited content; was: '5.6 Phase 3 Success Criteria']

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

### JR-ML-WS-015 — 10. Risk Register.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1875-1897)

**Notes**:

[v3 thin-brief flagged] WebSocket/messaging architecture gap or design

### JR-ML-ARCH-007 — 13. Risk Assessment.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1465-1483)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-008 — 15.1 juniper-canopy — Required.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1618-1628)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-TRAIN-013 — 15.2 juniper-cascor — Required (cross-repo).

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1629-1635)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 thin-brief flagged]

### JR-ML-ARCH-009 — 15.3 Optional / Recommended Cleanup.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1636-1642)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-010 — 2.4 Repositories Examined.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 156-165)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-011 — 4.1 Final Registry.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 224-248)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-OBS-020 — 4.1 juniper-cascor Performance.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 420-433)

**Detail**:

| **Forward pass**        | ✅ Optimized     | Pre-allocated buffer (OPT-1) eliminates N `torch.cat()` calls                    |

**Notes**:

[v3 thin-brief flagged]

### JR-ML-OBS-021 — 4.2 juniper-canopy Performance.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (lines 433-442)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-012 — 6.1 Phase 5 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1018-1042)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-013 — 6.2 Phase 4 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1043-1067)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-014 — 8.3 How the Problem Compounds (Best Articulated by P4-D).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1210-1219)

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-015 — 9.5 Detailed Design: Improved `juniper_plant_all.bash`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 603-617)

**Detail**:

# 1. wait_for_health() function that polls /v1/health with configurable timeout

**Notes**:

[v3 thin-brief flagged]

### JR-ML-ARCH-016 — 9.6 Detailed Design: Improved `juniper_chop_all.bash`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 617-630)

**Detail**:

# 1. validate_pid() function that checks /proc/<pid>/cmdline

**Notes**:

[v3 thin-brief flagged]

### JR-ML-UI-006 — [ ] Loss chart displays live training data (not flat line at 0).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1594-1615)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '14.4 Visual Verification Checklist']

### JR-ML-SEC-052 — [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR….

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 439-448)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)

**Notes**:

[v3 brief repaired from cited content; was: 'Primary']

### JR-ML-WS-016 — [§0 Document Conventions](#0-document-conventions).

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 21-45)

**Notes**:

[v3 brief repaired from cited content; was: '0.2 Table of Contents'] WebSocket/messaging architecture gap or design

### JR-ML-UI-007 — After Tier 0**: Metrics charts display live data. Topology renders. Dashboard is functionally usable.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1409-1464)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '12. Implementation Priority and Ordering']

### JR-ML-ARCH-017 — All line numbers and code patterns in this document were independently verified against the current codebase HEAD:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1656-1673)

**Notes**:

[v3 brief repaired from cited content; was: '16.1 Code Validation Results']

### JR-ML-ARCH-018 — Analysis**: 7/7 consensus on P5-RC-01, P5-RC-04, P5-RC-05 (the original Phase 2 findings). 12 issues found by only 1-2 of the 7 proposals,….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1068-1096)

**Notes**:

[v3 brief repaired from cited content; was: '6.3 Phase 3 Proposal Agreement Matrix']

### JR-ML-ARCH-019 — Both Phase 5 proposals unanimously agree:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 168-195)

**Notes**:

[v3 brief repaired from cited content; was: '3.1 Phase 1: Correctly Implemented but Incompletely Validate']

### JR-ML-ARCH-020 — Both Phase 5 proposals unanimously agree, and this final document adopts without change:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 208-221)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 Unanimous Findings Preserved in Final Document']

### JR-ML-ARCH-021 — Both proposals agree Phase 2 correctly identified:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 196-207)

**Notes**:

[v3 brief repaired from cited content; was: '3.2 Phase 2: Correct but Too Narrow']

### JR-ML-ARCH-022 — cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1486-1504)

**Notes**:

[v3 brief repaired from cited content; was: '14.1 Automated Tests']

### JR-ML-ARCH-023 — cd /home/pcalnon/Development/python/Juniper/juniper-data.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1555-1593)

**Notes**:

[v3 brief repaired from cited content; was: '14.3 Manual Integration Test']

### JR-ML-ARCH-024 — def test_metrics_history_contract_matches_demo():.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1505-1554)

**Notes**:

[v3 brief repaired from cited content; was: '14.2 New Contract Tests (FIX-K)']

### JR-ML-ARCH-025 — Divergence**: Whether the uppercase status normalization gap should be removed (Proposal A) or retained as a latent bug (Proposal B).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 96-118)

**Notes**:

[v3 brief repaired from cited content; was: '1.4 Final Resolution of the Main Divergence']

### JR-ML-WS-017 — Each item below has: a unique ID, severity (P0-P3), location, current state, target state, and a remediation hook.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1128-1131)

**Notes**:

[v3 brief repaired from cited content; was: '7. Missing / Broken Pieces (Enumerated)'] WebSocket/messaging architecture gap or design

### JR-ML-API-005 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 402-419)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.3 CR-024: Chunked Encoding Body Limit']

### JR-ML-ARCH-026 — Final resolution**: **6 confirmed** at lines 1000, 1021, 1155, 1187, 1231, 1274.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1129-1137)

**Notes**:

[v3 brief repaired from cited content; was: '7.4 Hardcoded URL Count: 2 vs 6']

### JR-ML-UI-008 — Final resolution**: **CRITICAL**. The network topology visualization is completely non-functional in service mode — the validation guard….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1110-1118)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '7.2 Topology Severity: CRITICAL vs MODERATE']

### JR-ML-TRAIN-014 — Final resolution**: **Known limitation**. This is not a bug — it is an architectural limitation of CasCor's API. Requires CasCor API….

**Status**: designed  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1156-1164)

**Notes**:

[v2 ARCH→TRAIN re-bucket] [v3 brief repaired from cited content; was: '7.7 Dataset Scatter: Active Bug vs Known Limitation']

### JR-ML-ARCH-027 — Final resolution**: Listed separately as `P5-RC-09` to ensure both code paths are addressed during implementation, but recognized as same….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1147-1155)

**Notes**:

[v3 brief repaired from cited content; was: '7.6 `/api/metrics` Snapshot: Separate Issue vs Subsumed']

### JR-ML-WS-018 — Final resolution**: **LOW (latent)**. The bug is currently inactive because the dashboard doesn't consume WebSocket data (P5-RC-05). The….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1174-1182)

**Notes**:

[v2 ARCH→WS re-bucket] [v3 brief repaired from cited content; was: '7.9 Relay Raw Metrics Severity: MODERATE vs LOW']

### JR-ML-ARCH-028 — Final resolution**: MODERATE structural issue with low current impact. Proposal A correctly lowered current practical impact (no downstream….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1183-1188)

**Notes**:

[v3 brief repaired from cited content; was: '7.10 State Sync Metrics Severity']

### JR-ML-ARCH-029 — Final resolution**: **MODERATE**. This is a real cross-repo bug confirmed by validation (only one assignment to `current_phase` exists). It….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1119-1128)

**Notes**:

[v3 brief repaired from cited content; was: '7.3 CasCor Phase Bug Severity']

### JR-ML-DEP-008 — Final resolution**: **MODERATE**. This issue affects deployment portability in Docker, reverse proxy, and non-standard port scenarios — all….

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1138-1146)

**Notes**:

[v2 ARCH→DEP re-bucket] [v3 brief repaired from cited content; was: '7.5 Hardcoded URLs Severity: MODERATE vs LOW']

### JR-ML-ARCH-030 — Final resolution**: **Non-functional runtime mapping**. Not dead code — the mapping executes successfully — but `candidate_epochs` is not….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1165-1173)

**Notes**:

[v3 brief repaired from cited content; was: '7.8 `candidate_epochs` Mapping Classification']

### JR-ML-ARCH-031 — Final resolution**: Retain as `P5-RC-03 HIGH (latent)`.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1099-1109)

**Notes**:

[v3 brief repaired from cited content; was: '7.1 Uppercase Status Gap: Removed vs Retained']

### JR-ML-DEP-009 — FROM python:3.14-slim AS builder.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 669-689)

**Detail**:

FROM python:3.14-slim AS builder

**Notes**:

[v3 brief repaired from cited content; was: '9.8 Detailed Design: Worker Dockerfile']

### JR-ML-ARCH-032 — Given the depth of analysis (7 Phase 3 proposals → 4 Phase 4 proposals → 2 Phase 5 proposals → this final synthesis with code….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1683-1733)

**Notes**:

[v3 brief repaired from cited content; was: '16.3 Completeness Assessment']

### JR-ML-WS-019 — Given the latency tolerance matrix, here is the recommended transport for every operation in scope.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 974-977)

**Notes**:

[v3 brief repaired from cited content; was: '6. Transport Split Design'] WebSocket/messaging architecture gap or design

### JR-CAS-TOOL-003 — Hardcoded values extraction into constants module; 56 hardcoded values across API layer, lifecycle manager, observability require extraction.

**Status**: designed  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 1-100)

**Detail**:

New module cascor_constants/constants_api/constants_api_defaults.py with 43 constants. Target location: cascor_constants/ hierarchy extended. Approach A recommended: extend existing cascor_constants/ pattern (vs. Approach B: centralize in settings.py, Approach C: hybrid). Files requiring modification: 16 (models, lifecycle, observability, routes, service_launcher, middleware, app, workers, candidate_unit, spiral_problem, snapshots, profiling).

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-ARCH-033 — In tables throughout this document:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 142-155)

**Notes**:

[v3 brief repaired from cited content; was: '2.3 Proposal Attribution Legend']

### JR-ML-SEC-053 — Issue Remediations, Section 11.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 9-59)

**Detail**:

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

### JR-ML-WS-020 — `juniper-cascor` — cascor server (FastAPI, async).

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 46-77)

**Notes**:

[v3 brief repaired from cited content; was: '0. Document Conventions'] WebSocket/messaging architecture gap or design

### JR-ML-DEP-010 — juniper-cascor-worker:.

**Status**: designed  **Priority**: P1  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 689-714)

**Detail**:

context: ../juniper-cascor-worker

**Notes**:

[v3 brief repaired from cited content; was: '9.9 Detailed Design: Worker in Docker Compose']

### JR-CAN-UI-007 — Meta Parameters enhancement: rename Training Parameters to Meta Parameters with NN and Candidate Nodes subsections (22 components).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 1-100)

**Detail**:

Restructure parameters card into two collapsible subsections: Neural Network (12 inputs: max iterations, learning rate, hidden units, growth trigger, convergence threshold, spiral params, dataset elements/noise) and Candidate Nodes (10 inputs: pool size, correlation threshold, selected candidates, training radio, iterations, convergence threshold, multi-candidate selection, candidate selection radio, top/random candidates count). Single shared Apply Parameters button. Cross-section checkbox linking (Multi-Node Layers ↔ Multi Candidate Selection).

**Design**:

Collapsible card structure with 22 component IDs, 10 Dash callbacks for toggles/radio/checkbox sync, theme constants (NEW/CHANGED/REMOVED tracking). Test plan includes unit and integration tests.

### JR-ML-ARCH-034 — `metrics_panel.py` (for P5-RC-01) — fix is in backend, not the panel's access patterns.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1643-1653)

**Notes**:

[v3 brief repaired from cited content; was: '15.4 Files NOT Requiring Modification']

### JR-ML-ARCH-035 — `P5-RC-09` remains listed separately to avoid missing the `/api/metrics` snapshot path during implementation, even though it shares root….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 249-257)

**Notes**:

[v3 brief repaired from cited content; was: '4.2 Final Classification Notes']

### JR-ML-ARCH-036 — P5-RC-18  SYSTEMIC: No canonical backend contract.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1220-1258)

**Notes**:

[v3 brief repaired from cited content; was: '8.4 Root Cause Dependency Graph']

### JR-ML-ARCH-037 — Practical bottom line**:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 83-95)

**Notes**:

[v3 brief repaired from cited content; was: '1.3 Two Critical Display Blockers']

### JR-ML-ARCH-038 — **Priority**: P0 — CRITICAL.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1307-1357)

**Notes**:

[v3 brief repaired from cited content; was: '11. Consolidated Fix Recommendations']

### JR-ML-ARCH-039 — **Severity**: CRITICAL — Primary display blocker.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 258-308)

**Notes**:

[v3 brief repaired from cited content; was: '5. Detailed Issue Analysis']

### JR-ML-ARCH-040 — The final document uses Proposal B's numbering:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 134-141)

**Notes**:

[v3 brief repaired from cited content; was: '2.2 Canonical Numbering']

### JR-ML-ARCH-041 — The following subsystems function correctly in service mode (confirmed by all proposals):.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1290-1306)

**Notes**:

[v3 brief repaired from cited content; was: '10. Verified Working Paths']

### JR-ML-UI-009 — The Juniper Canopy system has **multiple distinct ingress paths** for data into the dashboard, each independently determining its output….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1191-1205)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '8.1 The Fundamental Problem (Consensus Across All Proposals)']

### JR-ML-UI-010 — The juniper-canopy dashboard fails to display metrics and topology from an external juniper-cascor instance because **the service-mode data….

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 51-60)

**Notes**:

[v2 ARCH→UI re-bucket] [v3 brief repaired from cited content; was: '1.1 Primary Finding']

### JR-ML-WS-021 — The original draft had 8 open questions; several have been resolved into recommendations during integration. Remaining genuinely-open….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 1898-1915)

**Notes**:

[v3 brief repaired from cited content; was: '11. Open Questions for Human Review'] WebSocket/messaging architecture gap or design

### JR-ML-ARCH-042 — The status bar path is the exception that proves the rule. `ServiceBackend.get_status()` was specifically designed to produce flat keys….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1206-1209)

**Notes**:

[v3 brief repaired from cited content; was: '8.2 Why the Status Bar Works (All Proposals Agree)']

### JR-ML-OBS-022 — The worker is **heartbeat-only** by design (R1.3 design doc, METRICS-MON.

**Status**: designed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 193-222)

**Detail**:

| Source-of-truth file | `juniper_cascor_worker/http_health.py` (heartbeat HTTP/1.1 server, hand-rolled on `asyncio.start_server`) |

**Notes**:

[v3 brief repaired from cited content; was: '3.4 juniper-cascor-worker']

### JR-ML-ARCH-043 — This document merges both Phase 5 proposals using these rules:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 121-133)

**Notes**:

[v3 brief repaired from cited content; was: '2.1 Methodology']

### JR-ML-ARCH-044 — This final document:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1674-1682)

**Notes**:

[v3 brief repaired from cited content; was: '16.2 Key Reconciliation Decisions']

### JR-ML-ARCH-045 — This final synthesis tracks **20 entries total**:.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 61-82)

**Notes**:

[v3 brief repaired from cited content; was: '1.2 Final Synthesis Outcome']

### JR-ML-WS-022 — This section documents every message type that crosses each repo boundary. **Asterisks (*) mark fields that are required**; all others are….

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 437-440)

**Notes**:

[v3 brief repaired from cited content; was: '3. Bidirectional Message Contract'] WebSocket/messaging architecture gap or design

### JR-ML-WS-023 — This section tabulates every editable canopy UI element with its latency requirements and the recommended transport.

**Status**: designed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (lines 815-823)

**Notes**:

[v3 brief repaired from cited content; was: '5. Latency Tolerance Matrix'] WebSocket/messaging architecture gap or design

### JR-ML-ARCH-046 — Three false positives were identified and retracted across Phase 3 and Phase 4 analyses. All four Phase 4 proposals documented these….

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1259-1289)

**Notes**:

[v3 brief repaired from cited content; was: '9. False Positives and Retractions']

### JR-ML-UI-011 — Three new systemd user service units following canopy's pattern:.

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 630-669)

**Detail**:

After=network-online.target juniper-data.service

**Notes**:

[v3 brief repaired from cited content; was: '9.7 Detailed Design: systemd Units']

### JR-ML-UI-024 — 2.1 Bugs.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DEEP_AUDIT_FIVE_REPOS_2026-04-19.md` (lines 105-114)

**Detail**:

| ID        | Severity   | File:Line              | Description

**Notes**:

[v3 thin-brief flagged]

### JR-ML-OBS-053 — [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](../legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md).

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 454-465)

**Detail**:

- [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](../legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md)

**Notes**:

[v3 brief repaired from cited content; was: 'Design docs']

### JR-ML-UI-025 — Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/NETWORK_TOPOLOGY_DISPLAY_ANALYSIS_AND_FIXES.md` (lines 536-555)

**Detail**:

Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:

**Notes**:

[v3 brief repaired from cited content; was: 'Design']

### JR-ML-TRAIN-047 — Concurrency Assessment.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` (lines 324-330)

**Detail**:

**WebSocket Mode**: Well-designed single-threaded asyncio with `asyncio.to_thread` for CPU-bound training. No shared mutable state between async loop and training thread

### JR-ML-OBS-054 — Design mini-batch instrumentation for CasCor training observability.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md` (lines 1-100)

**Notes**:

Batch-level metrics collection.

### JR-ML-TRAIN-048 — Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 419-434)

**Detail**:

**Effort**: 0.5 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.4 CR-025: WebSocket Async Lock']

### JR-ML-UI-026 — Implement contextual menu and candidate tab design for Canopy UI.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CONTEXTUAL_MENU_AND_CANDIDATE_TAB_DESIGN.md` (lines 1-100)

### JR-ML-SEC-112 — juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 415-423)

**Detail**:

- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` §2.6, §6 Q6 — provisional-targets caveat and 2026-06-15 revisit deadline

**Notes**:

[v3 brief repaired from cited content; was: 'Cross-repo']

### JR-ML-SEC-113 — Optimizer and `nn.Linear` recreated on every `train_output_layer` call.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 859-877)

### JR-ML-UI-027 — Per audit finding C.1 (juniper-canopy): canopy's `RequestIdMiddleware`.

**Status**: designed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 249-257)

**Detail**:

Per audit finding C.1 (juniper-canopy): canopy's `RequestIdMiddleware`

**Notes**:

[v3 brief repaired from cited content; was: '4.3 RequestIdMiddleware boundary placement']

### JR-ML-SEC-114 — Per-phase entry / design docs.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 728-740)

**Detail**:

- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`

### JR-ML-SEC-115 — Performance test baselines record data but never assert against regression thresholds.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` (lines 1058-1076)

### JR-ML-OBS-055 — Phase B (polling elimination — P0 WIN) — ✅ IMPLEMENTED.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 330-341)

**Detail**:

| Two-flag design: `enable_browser_ws_bridge` + `disable_ws_bridge`   | ✅ In `settings.py`                        |

### JR-ML-SEC-116 — Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6.

**Status**: designed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 275-305)

**Detail**:

**Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6

**Notes**:

[v3 brief repaired from cited content; was: '4.3 Dimension C — Shared lib + WS schema + middleware']

### JR-ML-WS-136 — Standardize WebSocket frame schema for Canopy↔CasCor training streaming.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md` (lines 1-50)

### JR-ML-OBS-056 — This tracker accepts new items in three cases:.

**Status**: designed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 378-388)

**Detail**:

- **Audit follow-ups** — if a new audit (e.g. a 2026-Q3 observability re-audit) surfaces findings whose action sits beyond a single PR, add them here with a fresh ID.

**Notes**:

[v3 brief repaired from cited content; was: '4.2 When new items are added']

### JR-CAS-WS-003 — Thread handoff procedure replaces default compaction; preserves context at 95-99% utilization threshold.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-100)

**Detail**:

Two-layer implementation: global ~/.claude/CLAUDE.md + project CLAUDE.md. Trigger: 95-99% context utilization (within 1-5% of compaction threshold). Additional triggers: 15+ tool calls, phase boundary, degraded recall, module transition, user request. 5-step execution protocol: checkpoint, compose goal, present, verify, git status. Exclusions: nearly complete task, sharp thread, tightly coupled work.

### JR-ML-TRAIN-049 — Update `TrainingSettings` model to include new `TrainingParamConfig` entries:.

**Status**: designed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 314-331)

**Detail**:

epochs: TrainingParamConfig = TrainingParamConfig(min=10, max=10000000, default=1000000)

**Notes**:

[v3 brief repaired from cited content; was: '5.4 `settings.py`']

### JR-ML-TRAIN-101 — Background.** `cascade_correlation.py:1655`'s lifecycle callback fires only on `epoch % 25 == 0 or epoch == epochs - 1`, so the R5.4-pre….

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` (lines 227-243)

**Detail**:

**Severity:** P3 · **Owner repo:** juniper-cascor · **Status:** deferred

**Notes**:

[v3 brief repaired from cited content; was: '3.7 R5.6-THROTTLE — Cascor 25-epoch emit throttle removal']

### JR-ML-OBS-142 — Closing PRs (commit hashes verified against current `origin/main`).

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 746-764)

**Detail**:

| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix |

### JR-CAS-TRAIN-032 — Document workaround for sys.path mutation pattern - long-term fix via IPC.

**Status**: designed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 607-619)

**Detail**:

Canopy uses sys.path.insert(0, cascor_src) to import Cascor directly. Fragile,
creates import order dependencies. Module naming collision resolved (cascor_constants/),
but sys.path mutation remains. Long-term: IPC or make Cascor installable package.

**Notes**:

[v2 ARCH→TRAIN re-bucket]

### JR-ML-SEC-213 — Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` (lines 378-402)

**Detail**:

**Effort**: 1 day | **Repo**: juniper-cascor | **Status**: FIXED

**Notes**:

[v3 brief repaired from cited content; was: '4.2 CR-026: Server-Assigned Worker IDs']

### JR-ML-SEC-214 — Issue Remediations, Section 10.

**Status**: designed  **Priority**: P3  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_e_dashboard_ws_infra_deploy_testing.md` (lines 392-428)

**Detail**:

All CasCor enhancement items are feature requests. Brief remediation approaches:

### JR-ML-DEP-044 — Phase 3: Worker Deployment & Container Integration (P1) -- Short-Term ✅ COMPLETED.

**Status**: designed  **Priority**: P3  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES_STARTUP_CODE_REVIEW_2026-04-06.md` (lines 754-785)

**Detail**:

**Goal**: Enable containerized deployment of the distributed worker.

### JR-ML-OBS-143 — **Status**: deferred (user explicitly paused at design-doc stage).

**Status**: designed  **Priority**: P3  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 126-176)

**Detail**:

- **Status**: deferred (user explicitly paused at design-doc stage)

**Notes**:

[v3 brief repaired from cited content; was: '3.3 TRAIN-ARCH-01 cascor mini-batch restoration']

