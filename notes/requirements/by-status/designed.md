# Requirements — status: designed

**Total entries**: 113

**By priority**: P0=5 | P1=83 | P2=18 | P3=7

**By category**: ARCH=55 | WS=15 | SEC=12 | OBS=11 | TRAIN=7 | UI=6 | DEP=3 | TEST=1 | API=1 | DATA=1 | TOOL=1

**By owner**: ml=109 | cas=3 | can=1

---

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

### JR-CAS-TOOL-003 — Hardcoded values extraction into constants module; 56 hardcoded values across API layer, lifecycle manager, observability require extraction.

**Status**: designed  **Priority**: P1  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/HARDCODED_VALUES_ANALYSIS.md` (lines 1-100)

**Detail**:

New module cascor_constants/constants_api/constants_api_defaults.py with 43 constants. Target location: cascor_constants/ hierarchy extended. Approach A recommended: extend existing cascor_constants/ pattern (vs. Approach B: centralize in settings.py, Approach C: hybrid). Files requiring modification: 16 (models, lifecycle, observability, routes, service_launcher, middleware, app, workers, candidate_unit, spiral_problem, snapshots, profiling).

**Notes**:

[v2 remap: CL→TOOL]

### JR-ML-SEC-052 — Issue Remediations, Section 11.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_c_crossrepo_clients_api.md` (lines 9-59)

**Detail**:

#### XREPO-01: Generator Name `"circle"` vs Server's `"circles"`

### JR-CAN-UI-007 — Meta Parameters enhancement: rename Training Parameters to Meta Parameters with NN and Candidate Nodes subsections (22 components).

**Status**: designed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/META_PARAMETERS_ENHANCEMENT_PLAN.md` (lines 1-100)

**Detail**:

Restructure parameters card into two collapsible subsections: Neural Network (12 inputs: max iterations, learning rate, hidden units, growth trigger, convergence threshold, spiral params, dataset elements/noise) and Candidate Nodes (10 inputs: pool size, correlation threshold, selected candidates, training radio, iterations, convergence threshold, multi-candidate selection, candidate selection radio, top/random candidates count). Single shared Apply Parameters button. Cross-section checkbox linking (Multi-Node Layers ↔ Multi Candidate Selection).

**Design**:

Collapsible card structure with 22 component IDs, 10 Dash callbacks for toggles/radio/checkbox sync, theme constants (NEW/CHANGED/REMOVED tracking). Test plan includes unit and integration tests.

### JR-ML-SEC-053 — Primary.

**Status**: designed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (lines 439-448)

**Detail**:

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](../legacy/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)

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

### JR-CAS-WS-003 — Thread handoff procedure replaces default compaction; preserves context at 95-99% utilization threshold.

**Status**: designed  **Priority**: P2  **Category**: WS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/THREAD_HANDOFF_IMPLEMENTATION.md` (lines 1-100)

**Detail**:

Two-layer implementation: global ~/.claude/CLAUDE.md + project CLAUDE.md. Trigger: 95-99% context utilization (within 1-5% of compaction threshold). Additional triggers: 15+ tool calls, phase boundary, degraded recall, module transition, user request. 5-step execution protocol: checkpoint, compose goal, present, verify, git status. Exclusions: nearly complete task, sharp thread, tightly coupled work.

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

