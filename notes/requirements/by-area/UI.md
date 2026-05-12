# Requirements — UI

**Area**: ui-frontend — Canopy/Dash, UX, visualizations

**Total entries**: 41

**By status**: proposed=37 | shipped=4

**By priority**: P0=7 | P1=7 | P2=24 | P3=3

**By owner**: ml=21 | can=20

---

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

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place. 
Must pass immutable copy or deep clone before modification.

### JR-CAN-UI-002 — Dataset-tab edits don't persist—Phase 1 cold-swap with Cancel button, Phase 2 live in-flight swap.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 38-42)

**Detail**:

Phase 1: add Cancel button, cold-swap via canopy adapter + cascor endpoint. 
Phase 2 (separate doc): live dataset swap behind experimental-functions gate, 
two-step warning modal, History/Snapshots/Replay persistence.

**PRs**: PR-7 (Phase 1, Issue, PR-series P2-1 to P2-7 (Phase 2 live swap, documented separately)

**Notes**:

See ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md for full Phase 2 spec.
Shares root cause with Issue #1.

### JR-CAN-UI-003 — Fix metaparameter edits that silently drop 14 of 29 keys without reaching cascor backend.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Root causes: incomplete adapter mapping, no roundtrip verification. 
Three sub-parts: (C1) surface drops to user, (C2) extend cascor PATCH endpoints, 
(C3) roundtrip verification. Includes candidate-pool invariants atomic validation.

**PRs**: PR-1 (Phase 6A series, Issue

**Notes**:

Blocks Issue

### JR-CAN-UI-004 — Fix network topology format mismatch: convert weight-oriented CasCor structure to graph-oriented visualizer contract.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Service-mode emits weight-oriented topology (input_size, hidden_units: [...]) while visualizer expects graph-oriented structure (input_units, connections). Critical display blocker.

**Notes**:

P5-RC-02; critical display blocker; part of final synthesis

### JR-CAN-UI-005 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

### JR-ML-UI-004 — All WebSocket JS handlers must wrap body in try-catch to prevent single exception from breaking dashboard.

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

### JR-CAN-UI-006 — Implement decision boundary visualization for real CasCor backend in Canopy dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 88-118)

**Detail**:

The /api/decision_boundary endpoint retrieves prediction function from cascor_integration but never computes the grid. Must implement grid computation mirroring demo mode logic.

**Notes**:

Dataset/Decision Boundary tab shows "No data available" when connected to real CasCor backend

### JR-CAN-UI-007 — Network visualizer screenshot timestamp must not be static.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 92-92)

**Detail**:

Issue 1.3.2: Screenshot PNG contains hardcoded timestamp instead of actual
capture time. Must update on every screenshot. File: src/frontend/components/network_visualizer.py

### JR-ML-UI-005 — Phase B: Browser bridge drains /ws/training into Dash store, Plotly.extendTraces updates, polling killed, GAP-WS-24a/b latency pipe.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-94)

**Notes**:

Phase B major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-006 — Phase I: Asset cache busting; bump assets_url_path / hash query param.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-102)

**Notes**:

Phase I major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-CAN-UI-008 — Replace debounce=True with 350ms on numeric inputs to fix perceived typing lag.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 365-499)

**Detail**:

Issue: spinner changes commit immediately but typed values require blur. 
Solution: use debounce=350ms for live feedback without callback churn. 
Also adds clientside blur-on-Apply and validation styling (invalid=True border).

**PRs**: PR-2 (Phase 6B, Issue

### JR-CAN-UI-009 — Must support zero-copy metadata parameter updates between Canopy and Cascor.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Candidate-pool invariants form a constrained triple (selected_candidates, 
top_candidates, random_candidates) that must be validated atomically in cascor.
Post-merge validation required for multi-key PATCH (e.g. {S: 6, T: 4, R: 2}).
Validation helper _validate_candidate_pool_triple() enforces 6 invariants.

**Notes**:

Shipped as part of Phase 6A remediation (Issue #1 / can-001 implementation).
Candidate-pool semantics confirmed 2026-05-09.

### JR-CAN-UI-010 — Phase 3 Wave 1—HDF5 snapshot capabilities (create, restore, history).

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 75-211)

**Detail**:

P3-1: Create new snapshot endpoint (POST /api/v1/snapshots) with auto-generated 
timestamp names and demo mode support. P3-2: Restore endpoint with training state 
validation and WebSocket broadcast. P3-3: History tracking (append-only JSONL log).
Status: all complete as of 2026-01-10.

### JR-CAN-UI-011 — Phase 3 Wave 2—Training Metrics Save/Load layouts and 3D topology visualization.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 402-599)

**Detail**:

P3-4: Save/load metric panel configuration as named presets (GET/POST/DELETE 
/api/v1/metrics/layouts endpoints). P3-5: Toggle 2D/3D network topology view 
with layer-based z-axis, circular layout for >4 hidden nodes, weight-based edge coloring.

**PRs**: {'PR-series': 'Wave 2 (37 new tests, coverage maintained 93%+)'}

### JR-CAN-UI-012 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-CAN-UI-013 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-ML-UI-007 — CAN-000: Periodic Updates Pause When Apply Parameters Active.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1990-1994)

### JR-ML-UI-008 — CAN-003: Retain Candidate Pool Data Per Node Addition.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2000-2004)

### JR-ML-UI-009 — CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1912-1926)

### JR-ML-UI-010 — CAN-CRIT-002: Save/Load Snapshot in Adapter — Blocked on `/v1/snapshots/*` API.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1929-1943)

### JR-ML-UI-011 — CAN-DEF-008: Advanced 3D Node Interactions.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1980-1983)

### JR-ML-UI-012 — CAN-HIGH-005: Remote Worker Status Dashboard.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1946-1960)

### JR-ML-UI-013 — Canopy dashboard must display WebSocket connection status badge (connected green, reconnecting yellow, offline red).

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

### JR-ML-UI-014 — Canopy must configure Dash assets_url_path with content-hash query string to bust browser cache on new JS.

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

### JR-CAN-UI-014 — Canopy must use explicit blur-on-Apply to force pending debounced values to commit.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 456-475)

**Detail**:

Clientside callback that blurs active element on Apply button click.
Removes entire class of apply-with-stale-value races where fast typists
submit before debounce commits value. ~10 lines of JS.

**Notes**:

Part of Issue

### JR-ML-UI-015 — Debounce lives in Dash clientside callback, NOT SDK.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 66-66)

**Notes**:

Settled position C-29 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-016 — Demo mode must maintain parity with live WebSocket mode (connection status, metrics updates).

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

### JR-CAN-UI-015 — Hardcoded colors must be extracted to theme_constants.py for DRY.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 168-168)

**Detail**:

Issue 3.3.1: Color strings repeated across components. Extract to
theme_constants.py for centralized management and dark/light theme support.

### JR-ML-UI-017 — KL-1: Dataset Scatter Plot Empty in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1963-1977)

### JR-CAN-UI-016 — Modulo toggle for theme switching must use Dash State, not module-level flag.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 169-169)

**Detail**:

Issue 3.3.2: Theme toggle using module-level variable instead of callback State.
Can cause race conditions in multi-user scenarios. Use dcc.Store for theme state.

### JR-ML-UI-018 — NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 58-58)

**Notes**:

Settled position C-21 from R3-03 table; cross-round consensus consolidation

### JR-CAN-UI-017 — Numeric inputs must use validation styling (red border) for out-of-range values.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 478-499)

**Detail**:

dbc.Input invalid=True property shows red border. Add pattern-matching callback
that watches min/max bounds and sets invalid flag on value change. Provides
immediate feedback without requiring Apply-button interaction.

**Notes**:

Part of Issue

### JR-ML-UI-019 — rAF coalescer must be scaffolded but disabled by default in Phase B; revisit in Phase B+1 if frame pressure detected.

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

### JR-ML-UI-020 — rAF coalescer scaffolded but DISABLED.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 53-53)

**Notes**:

Settled position C-16 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-021 — UI Lock and Visualization: UI locking during training and visualization improvements.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_08_UI_LOCK_AND_VISUALIZATION.md` (lines 1-45)

### JR-CAN-UI-018 — Header title color must be theme-aware (not hardcoded).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 247-247)

**Detail**:

Issue 5.3.6: Header title color hardcoded to light theme. Use theme-aware
color from theme_constants.py for dark/light mode support.

### JR-CAN-UI-019 — Hit rate formatter must verify percentage contract (0.0-1.0 range).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 246-246)

**Detail**:

Issue 5.3.5: _format_hit_rate may receive values outside [0, 1]. Add bounds
check and either clamp or raise error depending on usage context.

### JR-CAN-UI-020 — Left sidebar too wide on Training Metrics tab—use per-tab width from ui_standards.

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Hardcoded dbc.Col(width=3) for all tabs. Move to per-tab config via 
ui_standards.py. Seeds UI_STANDARDS.md documentation.

**PRs**: PR-6 (cosmetic sidebar width), PR-6.5 (UI_STANDARDS doc + Training-Metrics narrowing experiment)

