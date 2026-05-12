# Requirements — status: proposed

**Total entries**: 825

**By priority**: P0=44 | P1=424 | P2=324 | P3=33

**By category**: ARCH=343 | WS=125 | SEC=46 | API=44 | TEST=42 | OBS=41 | TOOL=40 | UI=37 | DOC=36 | DEP=19 | PERF=17 | TRAIN=13 | DATA=9 | OPS=7 | LOCK=6

**By owner**: ml=623 | can=105 | dep=25 | cas=21 | ccl=19 | dcl=15 | dat=12 | cwk=5

---

### JR-DEP-OBS-001 — Add juniper_cascor_training_sessions_completed_total counter with closed-set outcome labels.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 808-827)

**Detail**:

juniper_cascor_training_sessions_completed_total does not exist as of 2026-05-03.
Cascor currently exposes only training_sessions_active (Gauge) and training_epochs_total (Counter).
Recommendation: add counter with closed-set outcome ∈ {success, error, aborted} bumped from
training-loop completion handler. ~50 lines, R5.4 PR or separate R5.5a sub-track.

### JR-ML-SEC-001 — All WebSocket endpoints must enforce per-frame size limits: training 4 KB inbound, control 64 KB.

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

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-ML-SEC-002 — Canopy and Cascor must validate WebSocket Origin header against configurable allowlist; reject null origins and wildcards.

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

### JR-ML-SEC-003 — Canopy must implement cookie-session + CSRF first-frame validation before accepting WebSocket connections.

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

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place. 
Must pass immutable copy or deep clone before modification.

### JR-ML-WS-001 — Cascor must add optional seq field to all WebSocket messages and implement replay buffer with ReplayOutOfRange exception.

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

### JR-ML-WS-002 — Cascor training_stream must implement two-phase registration, resume frame handler with replay, and 1 Hz state throttle coalescer.

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

### JR-ML-WS-003 — CascorControlStream must expose async set_params(params, timeout=1.0) method for WebSocket parameter updates.

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

### JR-DEP-OBS-002 — Create Grafana dashboards for CasCor training, Data throughput, and Canopy requests.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 75-119)

**Detail**:

Phase 1 (v0.2.0) observability hardening. Three new dashboards: (1) cascor-training.json
with epoch progress, loss, hidden unit additions, latency histogram; (2) data-service.json
with generation rate, request count by endpoint, response time percentiles, error rate;
(3) canopy-requests.json with HTTP rate, WS connections, response codes, page load times.
Dashboard provider already watches provisioning directory; new JSON files auto-load.

### JR-DEP-OBS-003 — Create Prometheus alerting rules for health, latency, error rate, and restart loop.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 111-119)

**Detail**:

Phase 1. Create prometheus/alerts.yml with recording and alerting rules: service health
endpoint down > 2 min, request error rate > 5%, P95 latency > 2s, container restart loop.
Wire into prometheus/prometheus.yml via rule_files directive. Add Grafana alert contact
point configuration to provisioning.

### JR-ML-SEC-004 — CSWSH (Cross-Site WebSocket Hijacking) attack must be closed by Origin allowlist + CSRF first-frame.

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

### JR-ML-ARCH-001 — Day-1 verification procedure: 5 greps + baseline measurement before any Phase B deploy.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

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

Gate on Phase B entry. Dedup with R4-02, R3-03.

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-CAN-API-001 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

### JR-DEP-OPS-001 — Fix critical AGENTS.md documentation errors: Grafana password, rate limiting defaults.

**Status**: proposed  **Priority**: P0  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 9-26)

**Detail**:

Phase 1 (P0 priority, blocks other work). Step 1.1: Replace GRAFANA_ADMIN_PASSWORD
default 'admin' with GF_SECURITY_ADMIN_PASSWORD__FILE referencing Docker secret.
Step 1.2: Update JUNIPER_CASCOR_RATE_LIMIT_ENABLED and CANOPY_RATE_LIMIT_ENABLED
defaults from false to true (matches docker-compose.yml).

### JR-DCL-DOC-001 — Fix flake8 line-length command in AGENTS.md from 120 to 512.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 37-45)

**Detail**:

AGENTS.md commands section specifies --max-line-length=120, but the project standard is 512.
This discrepancy causes agents to produce false positives against actual project linting rules.
The parent CLAUDE.md explicitly states line-length 512 for all linters (ecosystem standard).
Fix: Update AGENTS.md Quick Reference > Essential Commands section.

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.2) and AGENTS_MD_UPDATE_PLAN (Step 1.2).

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

### JR-CAN-API-002 — Fix metrics format mismatch: flatten nested dashboard metrics contract (metrics.loss, metrics.accuracy) to match service mode output.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Dashboard reads nested metrics (metrics.loss, metrics.accuracy); service-mode adapter emits flat structure. Critical display blocker for metrics charts.

**Notes**:

P5-RC-01; critical display blocker; part of final synthesis

### JR-CAN-UI-004 — Fix network topology format mismatch: convert weight-oriented CasCor structure to graph-oriented visualizer contract.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Service-mode emits weight-oriented topology (input_size, hidden_units: [...]) while visualizer expects graph-oriented structure (input_units, connections). Critical display blocker.

**Notes**:

P5-RC-02; critical display blocker; part of final synthesis

### JR-DCL-DOC-002 — Fix __version__ in juniper_data_client/__init__.py from 0.3.1 to 0.3.2 to match pyproject.toml.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 24-32)

**Detail**:

The __init__.py __version__ string (0.3.1) is out of sync with pyproject.toml (0.3.2).
This is a code bug affecting any code or consumer that reads juniper_data_client.__version__.
Fix: Update juniper_data_client/__init__.py line 10 to __version__ = "0.3.2"

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.1) and AGENTS_MD_UPDATE_PLAN (Step 1.1).

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

### JR-ML-ARCH-002 — **P0: polling eliminated**.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-CAN-SEC-004 — Phase 0 Addendum—Add threading.Lock to TrainingStateMachine.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 258-260)

**Detail**:

HIGH-015: Thread-safe locking required in backend training state machine.
File: src/backend/training_state_machine.py

### JR-CAN-SEC-005 — Phase 0 Pre-Release Security Blockers (6 vulnerabilities).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 30-61)

**Detail**:

0.1.1: Fix path traversal in snapshot endpoints via regex + resolve() check.
0.1.2: Fix timing attack in API key validation via hmac.compare_digest().
0.1.3: Suppress internal exception details; log server-side, return generic message.
0.1.4: Fix rate limiter memory leak with periodic eviction + size cap (10k entries).
0.2.1: Fix thread-unsafe CallbackContextAdapter via contextvars.ContextVar.
0.2.2: Fix threading.Event replacement race with clear() instead of reassign.

### JR-ML-ARCH-003 — Phase 1:.

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

### JR-CAN-API-003 — Phase 1 Release-Critical Quality (15 tasks across API, config, frontend).

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 64-101)

**Detail**:

Step 1.1 (7 tasks): Fix /ws exception loop, enforce max_connections, stop 
broadcast() mutation, remove duplicate cn_patience, define set_params Pydantic model, 
handle malformed Content-Length, restrict CORS.
Step 1.2 (5 tasks): Centralize version, update app_config.yaml/pyproject.toml headers,
use get_settings() in get_rate_limiter(), fix CORS YAML syntax.
Step 1.3 (3 tasks): Replace _api_url() with settings-based, fix screenshot timestamp,
deduplicate accuracy plot logic.

### JR-ML-ARCH-004 — Phase 2:.

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

### JR-ML-WS-004 — Phase B: browser ws_dash_bridge drain, Plotly.extendTraces, connection-status store, polling kill.

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

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

### JR-DEP-OBS-004 — Ship Prometheus burn-rate alerting rules derived from SLO targets with MWMBR pattern.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 102-140)

**Detail**:

Implement Multi-Window Multi-Burn-Rate alerts for the 5 user-facing SLOs (§3).
Fast-burn (5m/1h @ 14.4×) and mid-burn (30m/6h @ 6×) page on-call.
Slow-burn (2h/24h @ 3×) and long-burn (6h/72h @ 1×) create tickets only.
Internal-supporting SLIs (§4) emit log-only-severity alerts with same MWMBR shape.

### JR-CAN-TRAIN-001 — Single-iteration auto-pause after stop+reset due to cleared _pause_event.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 42-42)

**Detail**:

cascor lifecycle manager leaves _pause_event cleared after reset(). 
Fix: one-line change to clear+set instead of reassign.

**PRs**: PR-5 (cascor fix, ordered first in remediation)

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-CCL-DOC-001 — Update AGENTS.md version from 0.1.0 to 0.3.0 to match current package state.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 20-28)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 11-13)

**Detail**:

AGENTS.md declares version 0.1.0 but actual package version is 0.3.0. Misleads agents about
codebase maturity and feature set (missing testing submodule, worker API, snapshot API, dataset API).

**Notes**:

Critical severity: marked P0 as blocking (misleads agents about codebase state)

### JR-CCL-DOC-002 — Update AGENTS.md: correct flake8 line length from 120 to 512 (blocker — agents produce incorrect output).

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 46-46)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 16-17)

**Detail**:

The AGENTS.md file incorrectly specifies flake8 --max-line-length=120, while pyproject.toml and
.pre-commit-config.yaml both specify 512 per Juniper ecosystem standard. This causes agents to
produce false-positive linting failures.

**Notes**:

Critical severity: marked P0 as blocking (agents produce incorrect output)

### JR-ML-ARCH-005 — WebSocket bridge replaces ~3 MB/s REST polling for metrics; achieves >=90% bandwidth reduction.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

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

P0 motivator. Metric: `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Dedup candidate with R3-03.

### JR-ML-OBS-002 — Wire Alertmanager default and tickets receivers (email via Gmail SMTP) to unblock SLO program close-out by 2026-06-02.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 132-142)

**Detail**:

G2 - Alertmanager receivers silently drop alerts routed to default/tickets.
Both receivers exist as no-op placeholders. Soft blocker before 2026-06-02 soak-close.
Recommend Option A: Email-via-Gmail SMTP for both (use existing SOPS-encrypted creds).

### JR-ML-API-001 — /api/v1/training/status returns snapshot_seq + server_instance_id atomically.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 117-117)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-018 — /ws/control handler returns protocol-error envelopes, echoes command_id, NO seq on command_response.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 120-120)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-ARCH-063 — 0-cascor: `git revert` P1.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 342-343)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-064 — 0-cascor: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 339-340)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-065 — 0-cascor: `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 340-341)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-066 — 0-cascor: Rolling cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 341-342)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-067 — 01: Dual metric format removed aggressively.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 375-376)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-068 — 02: Phase B clientside_callback hard to debug.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 376-377)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-069 — 03: Phase C REST+WS ordering race.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 377-378)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-070 — 04: Slow-client blocks broadcasts.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 378-379)

### JR-ML-ARCH-071 — 05: Playwright misses real-cascor regression.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 379-380)

### JR-ML-ARCH-072 — 06: Reconnection storm after cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 380-381)

### JR-ML-ARCH-073 — 07: 50-conn cap hit (multi-tenant).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 381-382)

### JR-ML-ARCH-074 — 08: Demo mode parity breaks.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 382-383)

### JR-ML-ARCH-075 — 09: Phase C unexpected behavior.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 383-384)

### JR-ML-ARCH-076 — 10: Browser memory exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 384-385)

### JR-ML-ARCH-077 — 11: Silent data loss via drop-oldest.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 385-386)

### JR-ML-ARCH-078 — 12: Background tab memory spike.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 386-387)

### JR-ML-ARCH-079 — 13: Orphaned commands after timeout.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 387-388)

### JR-ML-ARCH-080 — 14: Cascor crash mid-broadcast.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 388-389)

### JR-ML-ARCH-081 — 15: **CSWSH attack**.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 389-390)

### JR-ML-ARCH-082 — --: Mid-week deploys for behavior-changing flag flips only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 300-301)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-083 — --: Minimum-viable carveout ~7 days (P0 only).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 301-302)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-084 — --: Phase 0-cascor staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 295-296)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-085 — --: Phase B staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 296-297)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-086 — --: Phase B-pre-b staging soak = 48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 297-298)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-087 — --: Phase C flag-flip canary >= 7 days production data.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 299-300)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-088 — --: Phase D entry gate = B-pre-b in production >=48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 298-299)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-089 — A-SDK: Downgrade cascor-client pin.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 343-344)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-090 — A-SDK: PyPI yank.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 344-345)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-CAN-UI-005 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

### JR-CCL-DOC-005 — Add Architecture section to AGENTS.md documenting class hierarchy, API categories, exception hierarchy, design patterns.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 51-56)

**Detail**:

Document class hierarchy (JuniperCascorClient, CascorTrainingStream, CascorControlStream),
API method categories (health, network, training, metrics, data, snapshots, workers),
exception hierarchy (7 exception classes), design patterns (context manager, callback/observer, retry, envelope).

**Notes**:

High severity: agents have no guidance on codebase structure

### JR-CAN-TEST-005 — Add browser-automation UI test sub-suite with dedicated CI lane.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 45-46)

**Detail**:

No browser automation harness exists. Create pytest sub-suite with ≤5 min 
wall-clock budget via parallel jobs, caching, and slow marker. Skeleton 
in Phase 4 step 1, full coverage in Phase 4 step 2.

**PRs**: PR-4.1 (skeleton with basic page loads), {'PR-4.2 (full coverage': 'param Apply, dataset swap, snapshot restore)'}

### JR-ML-OBS-004 — Add dashboard/alert lint lane to juniper-deploy CI.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 284-290)

**Detail**:

Cross-cutting recommendation: Add CI guardrail to prevent future stale panels.
Run promtool check rules on alert_rules.yml and recording_rules.yml.
JSON-schema validate each dashboard and promtool query instant against synthetic Prometheus.

### JR-CCL-DOC-006 — Add Directory Layout section to AGENTS.md documenting complete directory tree with annotations.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 48-49)

**Notes**:

High severity: required by directives for agent codebase orientation

### JR-DCL-DOC-003 — Add directory structure section to AGENTS.md showing full repository layout.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-56)

**Detail**:

AGENTS.md lacks any description of the directory structure. Must document complex layout including:
juniper_data_client/, juniper_data_client/testing/, tests/, docs/, notes/, scripts/, util/,
.github/workflows/, conf/ with annotations for each directory's purpose.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.1) and AGENTS_MD_UPDATE_PLAN (Step 2.1).

### JR-CAN-TEST-006 — Add integration test suite for real CasCor backend code paths with mocked CascorIntegration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 191-207)

**Detail**:

conftest.py forces CASCOR_DEMO_MODE=1 for all tests; no test exercises cascor_integration paths. Would have caught INT-CRIT-001/002/003.

**Notes**:

Phase 2 high priority; must test control, topology, metrics, statistics, decision boundary, snapshots

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

### JR-DEP-SEC-001 — Add reverse proxy (Traefik or Caddy) with TLS termination to production profile.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 135-152)

**Detail**:

Phase 2. Proxy service in production profile terminates TLS; services communicate
over plaintext on internal networks. Support both self-signed certificates (dev)
and Let's Encrypt (production). Expose only ports 443 (HTTPS) and optionally 80
(redirect) on host.

### JR-ML-SEC-005 — Add security hardening to check_doc_links.py including universal bounds checking, input validation, and traversal depth limits.

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

### JR-ML-API-002 — All WebSocket message envelopes must include optional seq field and preserve backward compatibility.

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

### JR-CAN-DOC-001 — Application version must be centralized via importlib.metadata.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 83-83)

**Detail**:

Issue 1.2.1: Version string currently duplicated across health, status, and
config endpoints. Use importlib.metadata as single source of truth.
File: src/main.py

### JR-ML-ARCH-091 — `audit_log_enabled`: B-pre-a.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 315-316)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-092 — B-pre-a: `JUNIPER_AUDIT_LOG_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 349-350)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-093 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS='*'`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 347-348)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-094 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS=<broader>`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 346-347)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-095 — B-pre-a: `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 348-349)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-096 — B-pre-a: `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 345-346)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-097 — B-pre-b: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 351-352)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-098 — B-pre-b: `JUNIPER_WS_RATE_LIMIT_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 352-353)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-099 — B-pre-b: `JUNIPER_WS_SECURITY_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 350-351)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-100 — B: Hardcoded ring-cap reduction.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 355-356)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-101 — B: `JUNIPER_DISABLE_WS_BRIDGE=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 354-355)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-102 — B: `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 353-354)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-103 — B: URL `?ws=off` diagnostic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 356-357)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-019 — Background _recv_task started on connect; parses inbound, pops future by command_id, set_result(envelope).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 219-219)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-TEST-007 — Bandit configuration must be consolidated to single file.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 121-121)

**Detail**:

Issue 2.2.1: Multiple bandit config files (.bandit, .pre-commit hook, CI).
Consolidate to .bandit and reference from all invocation points.

### JR-CAN-TEST-008 — Bandit invocations across all CI workflows must be consistent.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 122-122)

**Detail**:

Issue 2.2.2: bandit runs in pre-commit, CI, and manual invocations with
varying flags. Standardize command and flags across all paths.

### JR-DEP-OBS-008 — Bridge juniper_cascor_pending_tasks gauge from worker coordinator queue depth to Prometheus.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 510-532)

**Detail**:

R4.4 worker heartbeat SLO (§4.1) is resolved via WorkerRegistryCollector. But §4.2
(pending-task queue depth) still requires a juniper_cascor_pending_tasks gauge from the
worker coordinator. Small cascor sub-track to add to existing WorkerRegistryCollector,
populated from coordinator's pending-task queue depth.

### JR-ML-OBS-005 — broadcast_from_thread adds Task.add_done_callback(_log_exception) (GAP-WS-29).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 119-119)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-020 — BROKEN: - MISSING — feature does not exist.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 61-62)

### JR-ML-WS-021 — Browser must send ping frame every 30s; expect pong within 5s; close and reconnect on timeout.

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

### JR-ML-ARCH-104 — BUG-CC-01: `create_topology_message()` Not Fully Implemented.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 536-561)

### JR-ML-ARCH-105 — BUG-CC-02: `cascade_add` Correlation Hardcoded to `0.0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 564-578)

### JR-ML-ARCH-106 — BUG-CC-03: `or` Fallback Bugs for Falsy Values in spiral_problem.py.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 581-595)

### JR-ML-ARCH-107 — BUG-CC-04: Version Strings Inconsistent Across File Headers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 598-612)

### JR-ML-ARCH-108 — BUG-CC-05: `remote_client_0.py` Hardcoded Old Monorepo Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 615-641)

### JR-ML-ARCH-109 — BUG-CC-06: 32 Test Files Have Hardcoded `sys.path.append` to Old Monorepo.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 644-658)

### JR-ML-ARCH-110 — BUG-CC-07: `TrainingMonitor.current_phase` Never Updated by State Machine.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 661-675)

### JR-ML-ARCH-111 — BUG-CC-08: Undeclared Global `shared_object_dict`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 678-692)

### JR-ML-ARCH-112 — BUG-CC-09: `validate_training_results` Uninitialized Variable When `max_epochs=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 695-709)

### JR-ML-ARCH-113 — BUG-CC-10: `validate_training` Validation Variables Not Initialized for No-Validation-Data Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 712-726)

### JR-ML-ARCH-114 — BUG-CC-11: Walrus Operator Precedence Bug in `utils.py`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 729-743)

### JR-ML-ARCH-115 — BUG-CC-12: `load_dataset` Uses `yaml.safe_load` Instead of `torch.load`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 746-779)

### JR-ML-ARCH-116 — BUG-CC-13: `RateLimiter._counters` Never Pruned — Unbounded Memory Growth.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 782-796)

### JR-ML-ARCH-117 — BUG-CC-14: `HandshakeCooldown._rejections` Never Pruned for Non-Blocked IPs.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 799-813)

### JR-ML-ARCH-118 — BUG-CC-15: `RequestBodyLimitMiddleware` Reads Full Body Before Size Check.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 816-830)

### JR-ML-ARCH-119 — BUG-CC-16: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 833-841)

### JR-ML-ARCH-120 — BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 844-852)

### JR-ML-ARCH-121 — BUG-CC-18: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 855-863)

### JR-ML-ARCH-122 — BUG-CN-01: `_stop.clear()` Race — `_perform_reset()` Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 868-882)

### JR-ML-ARCH-123 — BUG-CN-02: DashboardManager God Class (3,232 Lines).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 885-907)

### JR-ML-ARCH-124 — BUG-CN-03: 226 `hasattr` Guards in Tests Skip Test Logic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 910-924)

### JR-ML-ARCH-125 — BUG-CN-04: `_api_base_url` Hardcoded to `127.0.0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 927-941)

### JR-ML-ARCH-126 — BUG-CN-05: Service Populate Param Values with Int Defaults.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 944-958)

### JR-ML-ARCH-127 — BUG-CN-06: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 961-976)

### JR-ML-ARCH-128 — BUG-CN-07: Duplicate `APP_VERSION` Assignment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 979-993)

### JR-ML-ARCH-129 — BUG-CN-08: `_demo_snapshots` List Grows Unbounded in Demo Mode.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 996-1010)

### JR-ML-ARCH-130 — BUG-CN-09: `WebSocketManager.active_connections` Not Thread Safe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1013-1027)

### JR-ML-ARCH-131 — BUG-CN-10: `message_count` Increment Not Atomic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1030-1044)

### JR-ML-ARCH-132 — BUG-CN-11: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1047-1055)

### JR-ML-ARCH-133 — BUG-CN-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1058-1066)

### JR-ML-ARCH-134 — BUG-JD-01: `batch_export` Builds Entire ZIP in Memory — OOM Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1071-1093)

### JR-ML-ARCH-135 — BUG-JD-02: `delete()` TOCTOU Race Condition.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1096-1110)

### JR-ML-ARCH-136 — BUG-JD-03: `update_meta` Writes Without Temp File — Partial Data Exposure.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1113-1127)

### JR-ML-ARCH-137 — BUG-JD-04: Deterministic IDs with `seed=None` → Stale Cache Returns.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1130-1144)

### JR-ML-ARCH-138 — BUG-JD-05: `_version_lock` Is Class Variable — Won't Work Across Workers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1147-1169)

### JR-ML-ARCH-139 — BUG-JD-06: `ReadinessResponse.timestamp` Uses Naive `datetime.now()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1172-1186)

### JR-ML-ARCH-140 — BUG-JD-07: `record_dataset_generation()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1189-1203)

### JR-ML-ARCH-141 — BUG-JD-08: `record_access()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1206-1220)

### JR-ML-ARCH-142 — BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1223-1237)

### JR-ML-ARCH-143 — BUG-JD-10: ALL Storage Operations Block Async Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1240-1248)

### JR-ML-ARCH-144 — BUG-JD-11: `record_access` TOCTOU Race on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1251-1259)

### JR-ML-ARCH-145 — C-01: Correlation field is `command_id`, NOT `request_id` -- every repo, every test.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 228-229)

### JR-ML-ARCH-146 — C-02: `command_response` has NO `seq` field; `/ws/control` has no replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 229-230)

### JR-ML-ARCH-147 — C-03: `set_params` default timeout = 1.0 s (not 5.0 s).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 230-231)

### JR-ML-ARCH-148 — C-04: SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 242-243)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-149 — C-05: Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 243-244)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-150 — C-06: `server_instance_id` = programmatic key; `server_start_time` = advisory only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 231-232)

### JR-ML-ARCH-151 — C-07: `replay_buffer_capacity` added to `connection_established`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 232-233)

### JR-ML-ARCH-152 — C-08: Two-phase registration via `_pending_connections` set.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 233-234)

### JR-ML-ARCH-153 — C-09: Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 234-235)

### JR-ML-ARCH-154 — C-10: Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 256-257)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-155 — C-11: GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 257-258)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-156 — C-12: Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 268-269)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-157 — C-13: Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 269-270)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-158 — C-14: Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bri.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 270-271)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-159 — C-15: Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 271-272)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-160 — C-16: rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 272-273)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-161 — C-17: REST fallback cadence during disconnect = 1 Hz (NOT 100 ms).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 244-245)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-162 — C-18: `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 245-246)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-163 — C-19: Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 246-247)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-164 — C-20: GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 273-274)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-165 — C-21: NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 274-275)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-166 — C-22: `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 275-276)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-167 — C-23: REST endpoints preserved FOREVER -- no deprecation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 247-248)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-168 — C-24: Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 258-259)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-169 — C-25: One-resume-per-connection rule (second resume -> close 1003).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 248-249)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-170 — C-26: Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 259-260)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-171 — C-27: **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 260-261)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-172 — C-28: Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 276-277)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-173 — C-29: Debounce lives in Dash clientside callback (NOT SDK), 250 ms.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 249-250)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-174 — C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 250-251)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-175 — C-31: Shadow traffic: rejected.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 261-262)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-176 — C-32: Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 282-283)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-177 — C-33: Per-command HMAC deferred indefinitely.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 262-263)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-178 — C-34: Contract-test pytest marker `contract` runs on every PR in all 3 repos.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 283-284)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-179 — C-35: Latency tests are recording-only in CI; strict assertions local-only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 284-285)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-180 — C-36: Total effort: 13.5 target / 15.75 planning buffer / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 294-295)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-181 — C-37: P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 285-286)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-182 — C-38: Observability-before-behavior rule: metrics + panels + alerts before the behavior change.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 286-287)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-183 — C-39: Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 287-288)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-184 — C-40: Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 235-236)

### JR-ML-ARCH-185 — C-41: `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 236-237)

### JR-ML-ARCH-186 — C-42: Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-relia.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 288-289)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-187 — C: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 357-358)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-188 — C: `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 358-359)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-022 — Caller-cancellation cleans correlation map entry in finally.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 221-221)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-ARCH-189 — Canonical settings table: 25+ configuration variables across cascor/canopy with env vars, types, defaults, validation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

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

Central to Phase execution. All settings present before merge. CI lint enforces documentation + round-trip.

### JR-ML-WS-023 — Canopy adapter must split apply_params into hot (WebSocket) and cold (REST) paths; route hot params via CascorControlStream.set_params.

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

### JR-CAN-API-004 — Canopy must enforce max_connections limit in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 74-74)

**Detail**:

Issue 1.1.2: Currently no enforcement of max_connections. Must track active
connection count and reject new clients when limit reached.

### JR-ML-WS-024 — Canopy must implement _control_stream_supervisor task that maintains persistent WebSocket connection to cascor.

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

### JR-ML-OBS-006 — Canopy must implement JSON audit logger for WebSocket control commands with scrubbing and CRLF escaping.

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

### JR-ML-WS-025 — Canopy training control buttons (start/stop/pause/resume/reset) must route over WebSocket with REST fallback.

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

### JR-ML-SEC-006 — Canopy WebSocket handlers must enforce 120s idle timeout; close with code 1000 on expiry.

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

### JR-ML-SEC-007 — Cascor /ws/control must enforce per-connection command rate limit (leaky bucket, 10/sec).

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

### JR-CAS-API-002 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-ML-SEC-008 — Cascor must enforce per-IP WebSocket connection limit (default 5) to mitigate connection exhaustion.

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

### JR-ML-WS-026 — Cascor Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.

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

### JR-CAS-API-003 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-ML-PERF-002 — Cascor WebSocket send must timeout at 0.5s to prevent indefinite client stalls during backpressure.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_replay_buffer_design.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 286-292)

**Detail**:

Wrap existing await websocket.send_json(message) in asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds).
Default ws_send_timeout_seconds = 0.5 in Settings (range gt=0.0, le=5.0).
On asyncio.TimeoutError / WebSocketDisconnect, log INFO and return False so caller prunes.
Quick-fix mitigation for RISK-04 in Phase A-server (Day 2, commit 3).
Phase E may upgrade to full pump-task backpressure if production telemetry shows RISK-04/11 triggering.

**Notes**:

RISK-04 quick-fix. Phase E (Day 12) full backpressure deferred per R0-03 §7.2 unless production data warrants.

### JR-ML-WS-027 — CascorControlStream.set_params default timeout must be 1.0s (not 5.0s) to prevent visible UI hang.

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

### JR-ML-WS-028 — CascorControlStream.set_params(params, *, timeout=1.0, command_id=None) -> dict.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 217-217)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-ARCH-190 — CCC-01: Wire-format schema evolution — strictly additive, no field rename/retype/remove; rollout state matrix.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 59-146)

**Detail**:

Wire format is additive-only. Every field added in Phase 0-cascor (seq, emitted_at_monotonic, replay_buffer_capacity, server_instance_id)
is present but may be ignored by older clients. No field is renamed, retyped, or removed.
Rollout state matrix documents per-phase per-endpoint compatibility: which fields are present,
which are optional, which old clients tolerate.
Acceptance criteria: rollout doc completed, PR contains state matrix, no surprises in cross-repo CI.

**Notes**:

Cross-cutting. Applies to all phases touching wire. Dedup with R3-03.

### JR-ML-OBS-007 — CCC-02: Observability stack — metrics/logging/tracing/dashboards/alerts before behavior, load-bearing SLO binding.

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

### JR-ML-ARCH-191 — CCC-03: Kill-switch architecture — every phase has config-only reversal, MTTR <=5 min, CI-tested, staging-drilled.

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

### JR-CAN-TEST-009 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

### JR-ML-OBS-008 — _client_latency_ms private field on returned dict.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 223-223)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-OBS-001 — ColoredFormatter must not mutate LogRecord during formatting.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 151-151)

**Detail**:

Issue 3.1.1: ColoredFormatter adds ANSI codes to LogRecord.msg in-place,
affecting file output. Clone record before mutation or use format string.

### JR-DEP-SEC-002 — Complete SOPS secrets management with .env.secrets example and make targets.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 143-152)

**Detail**:

Phase 2. Create .env.secrets.example documenting all secret variables (API keys,
Grafana admin password, Sentry DSNs). Add make secrets-encrypt / make secrets-decrypt
targets wrapping sops commands. Document workflow in docs/SECRETS_GUIDE.md. Ensure CI
does not require decrypted secrets (use ${VAR:-} defaults).

### JR-ML-ARCH-192 — CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4216-4231)

### JR-ML-ARCH-193 — CONC-02: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4234-4249)

### JR-ML-ARCH-194 — CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4252-4275)

### JR-ML-ARCH-195 — CONC-04: ALL Storage Operations Block Async Event Loop (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4278-4301)

### JR-ML-ARCH-196 — CONC-07: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4304-4319)

### JR-ML-ARCH-197 — CONC-08: `is_running` Reads/Writes Inconsistently Locked.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4322-4336)

### JR-ML-ARCH-198 — CONC-09: Fire-and-Forget `asyncio.create_task` Without Stored Reference.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4339-4353)

### JR-ML-ARCH-199 — CONC-10: Health Monitor Deregister/Assign Race Window.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4356-4370)

### JR-ML-ARCH-200 — CONC-12: `record_access` TOCTOU on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4373-4388)

### JR-CAN-DOC-002 — Configuration must have no version string mismatches (app_config.yaml, pyproject.toml).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 84-86)

**Detail**:

Issues 1.2.2, 1.2.3: Update app_config.yaml version to 0.4.0 and pyproject.toml
header version comment to match. Should be single source via importlib.metadata.

### JR-DEP-OBS-009 — Consolidate health check timings and Prometheus scrape intervals into .env variables.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 9-145)

**Detail**:

110+ hardcoded values across docker-compose.yml, Prometheus configs, alert rules, scripts.
~24 are env-configurable, ~85 remain hardcoded. Priority HIGH: health check timings (28 values)
and Prometheus config (7 values). Approach A (RECOMMENDED): Docker Compose extension fields
(x-healthcheck-defaults) + .env expansion. Create scripts/config.sh for shell script defaults.
Add ~20 new variables to .env.example: HEALTHCHECK_INTERVAL, TIMEOUT, START_PERIOD, RETRIES;
PROMETHEUS_SCRAPE_INTERVAL, EVAL_INTERVAL, SCRAPE_TIMEOUT; per-service intervals.

### JR-ML-ARCH-201 — Constitution: 42+ settled positions on wire format, protocol behavior, security, phase order, observability, effort.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

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

Source of truth. All items settled; re-litigation via formal decision change only. Used by Phase 0-cascor through Phase I.

### JR-ML-ARCH-202 — Correctness: no seq gaps.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-203 — Correctness: no state loss.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-CAN-API-005 — CORS configuration YAML syntax must be valid and documented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 87-87)

**Detail**:

Issue 1.2.5: app_config.yaml CORS section has syntax errors. Validate and
document expected format. File: conf/app_config.yaml

### JR-CAN-SEC-007 — CORS must be restricted to used methods and headers only.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 79-79)

**Detail**:

Issue 1.1.7: Currently allows all methods and headers. Restrict to
actual API usage (GET, POST, OPTIONS; only necessary headers). File: src/main.py

### JR-DEP-TOOL-001 — Create juniper-ctl CLI wrapper for systemd management (start/stop/restart/logs/health/resources).

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 256-274)

**Detail**:

Management CLI wrapping systemctl --user commands with 10+ subcommands:
start/stop/restart (single or all), status (all services), logs/follow, health (latest checks),
resources (CPU/memory/IO usage), install (symlink units + daemon-reload), enable/disable (auto-start).

### JR-CCL-ARCH-001 — Create production constants module juniper_cascor_client/constants.py with ~30 constants (URLs, timeouts, retries, status codes).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 12-22)

**Detail**:

Sections: Service Configuration (base URLs), HTTP Configuration (timeout, retries, backoff, pool size),
HTTP Status Codes (400, 404, 409, 422, 503), Decision Boundary (resolution default/min/max),
Authentication (header name).

**Design**:

Create juniper_cascor_client/constants.py with logical sections organizing ~30 production constants.
Alternative: split into constants.py (production) and testing/constants.py (test fixtures).

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-ML-OBS-009 — Create register_or_reuse and register_fresh helpers in juniper-observability to centralize idempotent prometheus_client collector construction, eliminating ~10 copy-pasted implementations across consumer repos.

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

### JR-CCL-ARCH-002 — Create testing constants module juniper_cascor_client/testing/constants.py with ~65 constants (hyperparams, scenario params, topology, worker sim).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 23-37)

**Detail**:

Sections: Fake Client Configuration (URL, version, error rate, uptime), Training Hyperparameters
(learning rate, epochs, hidden units, patience), Loss/Accuracy Curve Parameters (per scenario),
Network Topology Generation (bias, weight scales), Decision Boundary Generation, Worker Simulation Data,
Dataset Configuration.

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-ML-ARCH-204 — D-1: Correlation field name (D-02).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 118-119)

### JR-ML-ARCH-205 — D-2: Phase 0-cascor carve-out (D-11).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 119-120)

### JR-ML-ARCH-206 — D-3: Two-flag browser bridge (D-17 + D-18).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 120-121)

### JR-ML-ARCH-207 — D-4: REST paths preserved forever (D-21, D-54, D-56).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 121-122)

### JR-ML-ARCH-208 — D-5: Positive-sense security flag (D-10).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 122-123)

### JR-ML-ARCH-209 — D-6: Phase E backpressure default (D-19).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 123-124)

### JR-ML-ARCH-210 — D-7: Phase C flag-flip criteria (D-48).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 124-125)

### JR-ML-ARCH-211 — D-8: Kill-switch MTTR tested (D-53).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 125-126)

### JR-ML-ARCH-212 — D-**Browser memory leak** (RISK-10): Medium-High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 132-133)

### JR-ML-ARCH-213 — D-**Cascor crash mid-broadcast** (RISK-14): Low.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 135-136)

### JR-ML-ARCH-214 — D-Correctness: no seq gaps: `cascor_ws_seq_gap_detected_total`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-215 — D-Correctness: no state loss: `cascor_ws_dropped_messages_total{type="state"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-ML-ARCH-216 — D-Criterion: Metric.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

### JR-ML-ARCH-217 — D-**CSWSH attack** (RISK-15): High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 131-132)

### JR-ML-ARCH-218 — D-**Dual metric format breakage** (RISK-01): High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 134-135)

### JR-ML-ARCH-219 — D-Observability: full pipe: All canonical metrics present on `/metrics`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-220 — D-**P0: polling eliminated**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-221 — D-Recovery: kill switches work: Every switch flipped in staging.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-ARCH-222 — D-Risk: Severity.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 129-130)

### JR-ML-ARCH-223 — D-Security: CSWSH closed: `canopy_ws_origin_rejected_total` page alert functional.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-ARCH-224 — D-**Silent data loss** (RISK-11): High (low likelihood).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 133-134)

### JR-ML-ARCH-225 — D: `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 359-360)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-226 — D: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 360-361)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-CAN-API-006 — DashboardManager must construct API URLs via settings, not ad-hoc _api_url().

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 91-91)

**Detail**:

Issue 1.3.1: _api_url() helper is error-prone and inconsistent. Replace all
callsites with settings-based URL construction. File: src/frontend/dashboard_manager.py

### JR-DEP-OBS-010 — Decide on per-service vs. shared library approach for MetricsAuthMiddleware.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (lines 1-60)

**Detail**:

juniper-data ships MetricsAuthMiddleware (IP allowlist on /metrics). Cascor and canopy
expose /metrics without in-process auth. Question: lift to juniper-observability shared lib
or keep per-service? Decision (locked 2026-05-02): keep per-service. Cascor/canopy are
network-isolated (ClusterIP, no ingress routing); data is exposed beyond cluster boundary.
Asymmetry is deliberate. Re-open if: cascor/canopy exposed beyond boundary, third service
needs middleware, compliance audit mandates uniform posture, or NetworkPolicy isolation breaks.

### JR-DEP-OBS-011 — Define and document alert rule thresholds as environment-configurable constants.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 55-66)

**Detail**:

Prometheus alert_rules.yml contains 10+ hardcoded thresholds (error rate 0.05, data P95
latency 2.0s, cascor P95 5.0s, dataset gen 30.0s, correlation 0.01, restart count 3, windows
1m/5m/10m/15m/30m). Document all values clearly in YAML comments. Consider envsubst preprocessing
for full configurability across deployment targets. Medium priority per analysis.

### JR-DEP-DEP-003 — Define production Docker Compose profile with resource limits, restart policies, log rotation.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 121-152)

**Detail**:

Phase 2 (v0.3.0) production readiness. Add --profile production to docker-compose.yml
or docker-compose.production.yml override. Per-service resource limits (deploy.resources.limits
for CPU and memory), restart policies (restart: always with deploy.restart_policy),
log rotation (Docker logging driver options max-size, max-file).

### JR-CAN-API-007 — Define Pydantic model for set_params endpoint request body.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 77-77)

**Detail**:

Issue 1.1.5: set_params endpoint lacks formal request schema. Add Pydantic
model for validation. File: src/main.py. Updates OpenAPI documentation.

### JR-ML-ARCH-227 — `disable_ws_auto_reconnect`: F.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 317-318)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-228 — `disable_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 308-309)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-229 — `disable_ws_control_endpoint`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 313-314)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-WS-029 — disconnect() cancels recv task, drains pending with set_exception(JuniperCascorConnectionError).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 220-220)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

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

### JR-DCL-DOC-004 — Document complete JuniperDataClient public API (20+ methods) in AGENTS.md, replacing minimal 3-method snippet.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 79-108)

**Detail**:

Public API section currently shows only 3 methods (health_check, create_spiral_dataset, download_artifact_npz).
Client has grown to 20+ public methods across 9 categories: Health & Readiness (3), Generator Discovery (2),
Dataset Creation (2), Dataset Versioning (2), Dataset Operations (3), Artifact Download (2), Preview (1),
Batch Operations (4), Resource Management (2). Must replace snippet with full categorized reference.

**Notes**:

New API added since last AGENTS.md update (2026-02-20): batch_delete, batch_create, batch_update_tags,
batch_export, list_versions, get_latest, list_generators, get_generator_schema, get_preview, is_ready,
wait_for_ready. Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.3) and AGENTS_MD_UPDATE_PLAN (Step 2.3).

### JR-DCL-DOC-005 — Document juniper_data_client.testing submodule in AGENTS.md (FakeDataClient, generators).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-57)

**Detail**:

Testing submodule (juniper_data_client/testing/) contains FakeDataClient (715 lines) and 4 synthetic
generators (generate_spiral, generate_xor, generate_circle, generate_moon) in generators.py (284 lines).
This is a critical public API surface that ships with the library and is used by consumers (juniper-cascor,
juniper-canopy). Must add "Testing Utilities" section documenting import paths and usage patterns.

**Notes**:

The omission of this submodule from AGENTS.md means agents are unaware of this significant API.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.4) and AGENTS_MD_UPDATE_PLAN (Step 2.4).

### JR-ML-ARCH-230 — E: `JUNIPER_WS_BACKPRESSURE_POLICY=block`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 361-362)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-231 — Effort bounds and calendar: 15.75 expected eng days (~4.5 weeks calendar) with soak windows.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

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

Risks: 0-cascor async race (+risk), A-SDK correlation map iteration (+risk), B-pre-a audit logger name collision (+risk),
B NetworkVisualizer Plotly (+1 day), B-pre-b session middleware absent (+0.5 day), C concurrent-correlation bugs (+risk),
D orphaned-command UI state (+risk), E queue tuning (+risk), F reconnect-cap lift debated.

### JR-DEP-OBS-012 — Emit X-Juniper-Readiness response header on all /v1/health/ready endpoints.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 89-94)

**Detail**:

All four services (cascor, data, canopy, cascor-worker) must emit
X-Juniper-Readiness: ready | degraded | not_ready response header on /v1/health/ready.
Header mirrors body status field byte-for-byte. Constant single-sourced in
juniper-observability (READINESS_HEADER). Cascor-worker uses same literal without import.

### JR-ML-ARCH-232 — `enable_browser_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 307-308)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-233 — `enable_raf_coalescer`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 309-310)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-234 — `enable_ws_control_buttons`: D.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 311-312)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-235 — ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4412-4426)

### JR-ML-ARCH-236 — ERR-02: `response.json()` Unguarded in cascor-client `_request()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4429-4443)

### JR-ML-ARCH-237 — ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4446-4460)

### JR-ML-ARCH-238 — ERR-07: `raise HTTPException` Without `from e` — Broad Except Masks Programming Errors (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4463-4477)

### JR-ML-ARCH-239 — ERR-08: `str(e)` in Batch Create Error Response — Information Disclosure (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4480-4494)

### JR-ML-ARCH-240 — ERR-09: `remote_client_0.process_tasks()` Catches All Exceptions, Only Prints.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4497-4511)

### JR-ML-ARCH-241 — ERR-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4514-4529)

### JR-ML-ARCH-242 — ERR-13: `arc_agi` Generator Silent Fallback on Any Exception.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4532-4546)

### JR-ML-ARCH-243 — ERR-14: `CascorMetricsStream.stream()` Swallows ConnectionClosed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4549-4571)

### JR-CAS-TEST-004 — Establish automated CI/CD pipeline with pytest, coverage, type checking, and linting.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 569-599)

### JR-ML-OPS-002 — Every phase must have kill-switch feature flag; TTF (time to fallback) documented.

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

### JR-DCL-DOC-006 — Expand AGENTS.md Key Files table from 4 entries to ~20 entries covering all significant files.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-76)

**Detail**:

The Key Files table is severely incomplete. Must document: juniper_data_client/testing/ submodule
(fake_client.py, generators.py), docs/ directory (4 files), scripts/ (check_doc_links.py, generate_dep_docs.sh),
util/ (run_all_tests.bash), CI/CD workflows (.github/workflows/ci.yml, publish.yml, security-scan.yml),
configuration files (.pre-commit-config.yaml, .sops.yaml, .env.example, conf/), and project meta files
(CHANGELOG.md, py.typed, README.md, LICENSE).

**Notes**:

Severity: High. Testing submodule is critical public API (ships with library, used by juniper-cascor
and juniper-canopy). Agents working on this codebase are unaware of its existence when omitted from AGENTS.md.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.2) and AGENTS_MD_UPDATE_PLAN (Step 2.2).

### JR-CCL-DOC-007 — Expand AGENTS.md Key Files table with 15+ missing entries (testing submodule, py.typed, CHANGELOG.md, docs/, scripts/, notes/, CI/CD files).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 58-77)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 23-28)

**Detail**:

Missing files include: juniper_cascor_client/testing/ (1,807 LOC), py.typed (PEP 561),
CHANGELOG.md, docs/ (4 files), scripts/ (2 files), notes/, .env.example, .pre-commit-config.yaml,
.github/workflows/ci.yml, publish.yml, CODEOWNERS, dependabot.yml, .sops.yaml, conf/, tests/conftest.py.

**Notes**:

High severity: agents cannot orient themselves or find major code components

### JR-ML-ARCH-244 — F: `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 362-363)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-WS-030 — Fail-fast: no SDK retries on timeout (C-04).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 222-222)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-API-008 — Fix CascorStateSync to read from correct response fields (data.state_machine, data.monitor).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

Sync reads data.state, data.epoch; real cascor has data.state_machine, data.monitor. Causes initial state hydration to fail.

**Notes**:

FIX-5; initial sync reads wrong keys

### JR-DEP-SEC-003 — Fix shell injection vulnerability in wait_for_services.sh and related scripts.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 264-314)

**Detail**:

check_service() interpolates environment-derived URLs directly into inline Python code.
Malicious JUNIPER_DATA_PORT value can break out and execute arbitrary code. Same pattern found
in health_check.sh (line 59-79) and test_health_enhanced.sh (line 66). Affects wait_for_services.sh,
health_check.sh, test_health_enhanced.sh. Remediation: pass URLs via sys.argv[1] instead of
interpolating into code string. Add PORT numeric validation as defense-in-depth.

### JR-ML-ARCH-245 — Flag: Phase.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 305-306)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-WS-031 — GAP-WS-01: and the subsequent canopy-side adapter refactor.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1338-1342)

### JR-ML-WS-032 — GAP-WS-01: through GAP-WS-33), ranging from P0 (security, auth, replay protocol, REST polling bandwid.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 149-153)

### JR-ML-WS-033 — GAP-WS-01: — `juniper-cascor-client` lacks WebSocket `set_params`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1236-1240)

### JR-ML-WS-034 — GAP-WS-02: through GAP-WS-05) | Playwright e2e: `test_browser_receives_metrics_event`, `test_chart_up.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1784-1788)

### JR-ML-WS-035 — GAP-WS-02: — Browser-side `cascorWS` / `cascorControlWS` are dead code.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1249-1253)

### JR-ML-WS-036 — GAP-WS-03: — Parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1257-1261)

### JR-ML-WS-037 — GAP-WS-04: note about background tab throttling.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2003-2007)

### JR-ML-WS-038 — GAP-WS-04: — `ws-metrics-buffer` store never populated.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1265-1269)

### JR-ML-WS-039 — GAP-WS-05: — No clientside callback drains WS stores into chart inputs.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1273-1277)

### JR-ML-WS-040 — GAP-WS-06: — Training control buttons use REST POST instead of WebSocket.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1289-1293)

### JR-ML-WS-041 — GAP-WS-07: (backpressure) sooner. **Decision needed before Phase E.**.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2015-2019)

### JR-ML-WS-042 — GAP-WS-07: backpressure with per-send timeout) lands before or together with Phase B (GAP-WS-13 seque.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1170-1174)

### JR-ML-WS-043 — GAP-WS-07: — No backpressure / slow client handling in cascor `WebSocketManager`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1297-1301)

### JR-ML-WS-044 — GAP-WS-08: — No end-to-end browser test for the WebSocket path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1307-1311)

### JR-ML-WS-045 — GAP-WS-09: integration tests that exercise the failure modes.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1437-1441)

### JR-ML-WS-046 — GAP-WS-09: — No cascor-side integration test for `set_params` on `/ws/control`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1320-1324)

### JR-ML-WS-047 — GAP-WS-10: + the canopy adapter refactor + GAP-WS-32 (per-command timeouts).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1855-1859)

### JR-ML-WS-048 — GAP-WS-10: — No canopy-side integration test for `set_params` round-trip.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1332-1336)

### JR-ML-WS-049 — GAP-WS-11: + §4.4 phased plan.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1923-1927)

### JR-ML-WS-050 — GAP-WS-11: Phase H).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1532-1536)

### JR-ML-WS-051 — GAP-WS-11: — Canopy `_normalize_metric` dual format is undocumented for external consumers.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1340-1344)

### JR-ML-WS-052 — GAP-WS-12: — No WebSocket heartbeat / ping-pong reciprocity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1348-1352)

### JR-ML-WS-053 — GAP-WS-13: (P1) — Lossless reconnect via sequence numbers and replay buffer.** Required components:.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1142-1146)

### JR-ML-WS-054 — GAP-WS-13: (sequence numbers + replay), GAP-WS-14 (Plotly extendTraces), GAP-WS-15 (rAF coalescing),.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1829-1833)

### JR-ML-WS-055 — GAP-WS-13: a server that doesn't recognize the `resume` command will respond with `command_response`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1214-1218)

### JR-ML-WS-056 — GAP-WS-13: Lossless Reconnect via Sequence Numbers and Replay Buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2177-2188)

### JR-ML-WS-057 — GAP-WS-13: reconnect+replay protocol — `server_start_time` change forces all clients to do a full RES.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2005-2009)

### JR-ML-WS-058 — GAP-WS-13: sequence numbers land). Currently there is no mechanism to reject an outdated client. **De.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2023-2027)

### JR-ML-WS-059 — GAP-WS-13: — Lossless reconnect via sequence numbers and replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1356-1360)

### JR-ML-WS-060 — GAP-WS-14: (`extendTraces`), this keeps the per-frame cost under 17 ms.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1377-1381)

### JR-ML-WS-061 — GAP-WS-14: above. Kept here for reference link integrity.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1442-1446)

### JR-ML-WS-062 — GAP-WS-14: mandates `Plotly.extendTraces(maxPoints=5000)`; ring buffer in `ws-metrics-buffer` (last 1.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2001-2005)

### JR-ML-WS-063 — GAP-WS-14: Plotly `extendTraces` with `maxPoints` Limit.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2146-2160)

### JR-ML-WS-064 — GAP-WS-14: — Plotly chart updates must use `extendTraces` with `maxPoints`.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1364-1368)

### JR-ML-WS-065 — GAP-WS-15: Browser-Side rAF Coalescing for 50Hz Candidate Events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2163-2174)

### JR-ML-WS-066 — GAP-WS-15: — Browser-side rAF coalescing for high-frequency events.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1372-1376)

### JR-ML-WS-067 — GAP-WS-16: `/api/metrics/history` Polling Bandwidth Bomb (~3 MB/s).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2129-2143)

### JR-ML-WS-068 — GAP-WS-16: — `/api/metrics/history` polling is the bandwidth bomb (P0 motivator).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1380-1384)

### JR-ML-WS-069 — GAP-WS-17: — `permessage-deflate` compression not configured.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1388-1392)

### JR-ML-WS-070 — GAP-WS-18: chunking or REST fallback; document the threshold; add a server-side size guard.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2007-2011)

### JR-ML-WS-071 — GAP-WS-18: Topology Message >64KB Causes Connection Teardown.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2219-2238)

### JR-ML-WS-072 — GAP-WS-18: — Topology message can exceed 64 KB silently.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1396-1400)

### JR-ML-WS-073 — GAP-WS-19: in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 229-233)

### JR-ML-WS-074 — GAP-WS-19: — `close_all()` does not hold `_lock` (CR-025 partial).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1404-1408)

### JR-ML-WS-075 — GAP-WS-20: (P3)**: normalize bidirectional envelope to use `{type, timestamp, data}` everywhere. Trac.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 482-486)

### JR-ML-WS-076 — GAP-WS-20: — Bidirectional envelope asymmetry.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1412-1416)

### JR-ML-WS-077 — GAP-WS-21: (P1)** in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 555-559)

### JR-ML-WS-078 — GAP-WS-21: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2241-2246)

### JR-ML-WS-079 — GAP-WS-21: debouncer rewrite) AND state event rate goes >5 Hz.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1528-1532)

### JR-ML-WS-080 — GAP-WS-21: — 1 Hz state throttle drops terminal transitions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1420-1424)

### JR-ML-WS-081 — GAP-WS-22: (P2)** in §7.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 745-749)

### JR-ML-WS-082 — GAP-WS-22: (protocol error responses).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1908-1912)

### JR-ML-WS-083 — GAP-WS-22: — Protocol error responses not specified.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1431-1435)

### JR-ML-WS-084 — GAP-WS-23: (P1)** in §7: clientside chart updates must use `Plotly.extendTraces()` with `maxPoints` p.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1022-1026)

### JR-ML-WS-085 — GAP-WS-23: — `Plotly.extendTraces` with `maxPoints` (alias of GAP-WS-14).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1439-1443)

### JR-ML-WS-086 — GAP-WS-24: (P2)** in §7. Phase B includes the instrumentation; Phase C+ uses the data to validate (or.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1037-1041)

### JR-ML-WS-087 — GAP-WS-24: — Production WebSocket latency instrumentation.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1444-1448)

### JR-ML-WS-088 — GAP-WS-25: (polling toggle).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1385-1389)

### JR-ML-WS-089 — GAP-WS-25: polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1386-1390)

### JR-ML-WS-090 — GAP-WS-25: WebSocket-Health-Aware Polling Toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2191-2202)

### JR-ML-WS-091 — GAP-WS-25: — WebSocket-health-aware polling toggle.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1452-1456)

### JR-ML-WS-092 — GAP-WS-26: Visible Connection Status Indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2205-2216)

### JR-ML-WS-093 — GAP-WS-26: — Visible connection status indicator.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1460-1464)

### JR-ML-WS-094 — GAP-WS-27: — Per-IP connection caps and DoS protection.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1468-1472)

### JR-ML-WS-095 — GAP-WS-28: Multi-Key `update_params` Torn-Write Race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2249-2260)

### JR-ML-WS-096 — GAP-WS-28: — Multi-key `update_params` torn-write race.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1476-1480)

### JR-ML-WS-097 — GAP-WS-29: for the exception-handling path.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1180-1184)

### JR-ML-WS-098 — GAP-WS-29: — `broadcast_from_thread` discards future exceptions.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1484-1488)

### JR-ML-WS-099 — GAP-WS-30: — Reconnect backoff has no jitter (thundering herd risk).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1492-1496)

### JR-ML-WS-100 — GAP-WS-31: Unbounded Reconnect Cap — Stops After 10.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2263-2274)

### JR-ML-WS-101 — GAP-WS-31: — Unbounded reconnect attempts cap (currently capped at 10).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1500-1504)

### JR-ML-WS-102 — GAP-WS-32: per-command correlation IDs + `pending verification` state pending matching `command_respo.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 2004-2008)

### JR-ML-WS-103 — GAP-WS-32: Per-Command Timeouts and Orphaned-Command Resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2277-2288)

### JR-ML-WS-104 — GAP-WS-32: — Per-command timeouts and orphaned-command resolution.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1508-1512)

### JR-ML-WS-105 — GAP-WS-33: — Demo mode failure visibility.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 1516-1520)

### JR-CAN-ARCH-001 — get_rate_limiter() must use get_settings() instead of direct access.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 86-86)

**Detail**:

Issue 1.2.4: Inconsistent settings access pattern. Use get_settings() function
for uniform configuration retrieval. File: src/security.py

### JR-CAN-TEST-010 — GitHub Actions workflow must fix lockfile extras mismatch.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 113-113)

**Detail**:

Issue 2.1.1: .github/workflows/lockfile-update.yml extras specification
conflicts with pyproject.toml. Align definitions.

### JR-CAN-TEST-011 — GitHub publish workflow must add contents:read permission.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 114-114)

**Detail**:

Issue 2.1.2: .github/workflows/publish.yml missing minimal required
permissions. Add contents:read for artifact access.

### JR-ML-ARCH-246 — H: `git revert` P16.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 363-364)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-CAN-OBS-002 — Health checks must use async probes instead of blocking network calls.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 155-155)

**Detail**:

Issue 3.1.5: Health endpoints currently block on cascor connectivity checks.
Use async probes or timeout guards to prevent cascor slowness from blocking
health endpoint response.

### JR-ML-ARCH-247 — I: `git revert` cache-bust commit.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 364-365)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-248 — ID: Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 373-374)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-CAN-API-009 — Implement CascorIntegration.get_network_data() method to return network statistics.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 120-140)

**Detail**:

Method does not exist on CascorIntegration class; callers will receive AttributeError at runtime. Must return dict with keys: input_weights, hidden_weights, output_weights, hidden_biases, output_biases, threshold_function, optimizer.

**Notes**:

Network statistics tab fails when connected to real CasCor backend; blocking P1

### JR-CAN-UI-006 — Implement decision boundary visualization for real CasCor backend in Canopy dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 88-118)

**Detail**:

The /api/decision_boundary endpoint retrieves prediction function from cascor_integration but never computes the grid. Must implement grid computation mirroring demo mode logic.

**Notes**:

Dataset/Decision Boundary tab shows "No data available" when connected to real CasCor backend

### JR-CAN-API-010 — Implement real backend control for Canopy WebSocket endpoint when connected to live CasCor backend.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 55-85)

**Detail**:

The /ws/control endpoint currently rejects all commands when cascor_integration is active with a hardcoded error. Must implement command routing to CascorIntegration methods (start, stop, pause, resume, reset) and add state broadcasting after each command execution.

**Notes**:

Part of Phase 1 critical integration blockers; blocking all real-backend WebSocket control

### JR-CAN-API-011 — Implement save_snapshot() and load_snapshot() methods on CascorIntegration class.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 146-166)

**Detail**:

Methods do not exist; code falls through to minimal HDF5 fallback that only stores metadata, not network state. Must delegate to CasCor's CascadeHDF5Serializer.

**Notes**:

Snapshot save/load in real backend mode produces incomplete snapshots

### JR-ML-WS-106 — lifecycle/manager.py state coalescer; terminal transitions bypass throttle (GAP-WS-21).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 118-118)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAN-OBS-003 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-ML-WS-107 — manager.py gains server_instance_id, server_start_time, _next_seq, _seq_lock, _replay_buffer, _assign_seq_and_append().

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 113-113)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-WS-108 — messages.py optional seq + emitted_at_monotonic field on every builder.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 112-112)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAN-API-012 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

### JR-ML-WS-109 — MISSING: - PARTIAL — feature is partially implemented; some paths work, others don't.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 60-61)

### JR-ML-WS-110 — MISSING: Status: server-side PRESENT (cascor accepts and handles the command); client-side MISSING.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE-1_2026-04-10.md` (lines 729-730)

### JR-CAN-TEST-012 — MyPy strict_optional setting conflict must be resolved.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 123-123)

**Detail**:

Issue 2.2.3: MyPy configuration has conflicting strict_optional directives
in different sections. Consolidate to single authoritative setting.

### JR-CAN-UI-007 — Network visualizer screenshot timestamp must not be static.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 92-92)

**Detail**:

Issue 1.3.2: Screenshot PNG contains hardcoded timestamp instead of actual
capture time. Must update on every screenshot. File: src/frontend/components/network_visualizer.py

### JR-CAN-API-013 — Normalize case-sensitivity for status and phase fields: ensure consistent handling of uppercase values from backends.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 102-116)

**Detail**:

Relay path at cascor_service_adapter.py:222 lacks .lower(); sync path at state_sync.py:70 has it. Asymmetric protection. FakeCascorClient uses uppercase, triggering bug in tests. Future backends may pass uppercase.

**Notes**:

P5-RC-03; retained as HIGH latent bug; defensive measure for future backends

### JR-CAN-API-014 — Normalize ServiceTrainingMonitor to use unwrapped response format for real cascor integration.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

_ServiceTrainingMonitor reads raw JuniperCascorClient responses without calling _unwrap_response(). Must normalize via single boundary in CascorServiceAdapter. Fixes FIX-1,2,3.

**Notes**:

Systemic root cause; affects metrics, is_training flag, response shape

### JR-ML-ARCH-249 — Observability: full pipe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-WS-111 — Phase 0-cascor: Cascor /ws/training emits monotonic seq, advertises server_instance_id+replay_buffer_capacity, supports resume, fixes state coalescer.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-91)

**Notes**:

Phase 0-cascor major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-CAN-ARCH-002 — Phase 1 Addendum—6 backend fixes (KeyError guards, thread safety, connection leaks).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 262-270)

**Detail**:

1.4.1: Guard get_dataset against KeyError on partial data (MED-036).
1.4.2: Fix prepare_dataset_for_visualization None crash (MED-038).
1.4.3: Thread-safe locking for Cassandra singleton (MED-039).
1.4.4: Thread-safe locking for Redis singleton (MED-041).
1.4.5: Fix Redis exception aliases to use sentinel class (MED-042).
1.4.6: Fix Redis force_new=True connection leak (MED-043).

### JR-CAN-TEST-013 — Phase 2 CI/CD Infrastructure Reliability (12 tasks).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 104-138)

**Detail**:

Step 2.1 (5 CI tasks): Fix lockfile extras, add permissions, fix pip-audit, 
define dev extra, add Codecov upload.
Step 2.2 (3 security tasks): Consolidate bandit config, standardize invocations,
fix mypy strict_optional conflict.
Step 2.3 (4 Docker tasks): Create prod config, pin deps via lockfile,
fix service URLs, change log handler to append mode.

### JR-ML-ARCH-250 — Phase 3:.

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

### JR-CAN-ARCH-003 — Phase 3 Addendum—5 backend quality improvements (circuit breaker, lazy imports, API exposure).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 271-277)

**Detail**:

3.5.1: Cache network property or wrap in circuit breaker (MED-034).
3.5.2: Narrow relay loop exception handling (MED-035).
3.5.3: Lazy-import torch in data_adapter.py (MED-037).
3.5.4: Expose public API on CascorServiceAdapter (MED-046).
3.5.5: Don't store Cassandra credentials as plain attributes (MED-040).

### JR-CAN-DOC-003 — Phase 3 Code Quality & Observability (18 tasks).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 141-186)

**Detail**:

Step 3.1 (6 logging): Fix ColoredFormatter mutation, cache logger wrappers,
make Sentry sample rate configurable, normalize Prometheus labels, use async 
health checks, set production log levels.
Step 3.2 (5 dead code): Remove unused candidate pool display, orphaned callbacks,
extract create_empty_plot(), deprecate legacy TrainingMetricsComponent.
Step 3.3 (5 frontend): Extract colors to theme_constants, fix modulo toggle,
fix doc links, remove blocking time.sleep(), split NetworkVisualizer callback.
Step 3.4 (2 perf): Reduce API timeout, begin DashboardManager extraction.

### JR-CAN-TEST-014 — Phase 4 Addendum—6 test quality fixes (context suppression, schema tests, coverage gaps).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 279-287)

**Detail**:

4.3.1: Remove contextlib.suppress(Exception) from assertions (HIGH-016).
4.3.2: Add pytest.fail() guards to WebSocket schema tests (HIGH-017).
4.3.3: Remove hasattr guards from unit tests (HIGH-018).
4.3.4: Rewrite performance test without exception suppression (HIGH-019).
4.3.5: Add dedicated tests for parameters_panel.py (55.3% gap).
4.3.6: Expand candidate_metrics_panel.py callback tests (65.6% gap).

### JR-ML-WS-112 — Phase A-SDK: `CascorControlStream.set_params(params, timeout=1.0, command_id=...)` ships to PyPI.

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

### JR-ML-SEC-009 — Phase B-pre-a: Origin allowlist, per-IP cap, frame-size cap, audit logger skeleton on `/ws/training`.

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

### JR-ML-SEC-010 — Phase B-pre-a: Origin on /ws/training, size caps, per-IP cap, idle timeout, audit-logger skeleton.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-93)

**Notes**:

Phase B-pre-a major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-011 — Phase B-pre-b: Origin on /ws/control, cookie session + CSRF first-frame, rate limit, idle timeout, adapter HMAC, audit Prom counters.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-95)

**Notes**:

Phase B-pre-b major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-SEC-012 — Phase B-pre-b: Origin on `/ws/control`, cookie+CSRF first-frame, rate limit, idle timeout, adapter HMAC, log injection escaping.

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

### JR-ML-UI-005 — Phase B: Browser bridge drains /ws/training into Dash store, Plotly.extendTraces updates, polling killed, GAP-WS-24a/b latency pipe.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-94)

**Notes**:

Phase B major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-113 — Phase C: Canopy adapter hot/cold split; hot→WS via command_id; unconditional REST fallback; flag-off default.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-96)

**Notes**:

Phase C major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-114 — Phase D: Browser start/stop/pause/resume/reset routed via /ws/control with REST fallback; per-command timeouts.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-97)

**Notes**:

Phase D major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-115 — Phase D: browser start/stop/pause/resume/reset training-control via `/ws/control` with REST fallback.

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

### JR-ML-PERF-003 — Phase E: Per-client pump tasks + bounded queues + policy matrix; default drop_oldest_progress_only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-98)

**Notes**:

Phase E major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-WS-116 — Phase F: Application ping/pong at 30s; 10s dead-conn threshold; uncap reconnect; jitter formula.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-99)

**Notes**:

Phase F major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-TEST-001 — Phase G: Cascor set_params integration tests via FastAPI TestClient.websocket_connect().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-100)

**Notes**:

Phase G major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-251 — Phase H: Normalize_metric audit + regression gate; CODEOWNERS hard gate; pre-commit hook.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-101)

**Notes**:

Phase H major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-UI-006 — Phase I: Asset cache busting; bump assets_url_path / hash query param.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-102)

**Notes**:

Phase I major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-252 — Phase: Switch (env var).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 337-338)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-CAN-TEST-015 — pip-audit in CI must scan full dependency tree, not just top-level.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 115-115)

**Detail**:

Issue 2.1.3: pip-audit command in .github/workflows/ci.yml is incomplete.
Must specify report file and scan transitive dependencies.

### JR-CAN-OBS-004 — Production default log levels must prevent debug spam in production.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 156-156)

**Detail**:

Issue 3.1.6: Default log level may be too verbose in production. Set
production-safe default (INFO/WARNING) independent of dev config.

### JR-CAN-OBS-005 — Prometheus endpoint labels must be normalized to prevent cardinality explosion.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 154-154)

**Detail**:

Issue 3.1.4: Endpoint labels may include query params, causing unbounded cardinality.
Normalize to path template (e.g. /api/v1/params/{id} not /api/v1/params/123).

### JR-CAN-LOCK-001 — pyproject.toml must define 'dev' extra for dependency management.

**Status**: proposed  **Priority**: P1  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 116-116)

**Detail**:

Issue 2.1.4: Missing dev extra for development dependencies. Define
[project.optional-dependencies] with 'dev' key including test/lint tools.

### JR-ML-API-003 — Reconnect protocol must handle resume frames within 5s timeout and emit resume_ok or resume_failed response.

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

### JR-ML-ARCH-253 — Recovery: kill switches work.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-CCL-ARCH-003 — Refactor client.py to use constants module (~20 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-44)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-004 — Refactor testing/fake_client.py to use testing constants (~40 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 50-52)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-005 — Refactor testing/scenarios.py to use testing constants (~50 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 54-56)

**Detail**:

Largest refactor: loss curve parameters, accuracy curve parameters, network topology generation,
decision boundary generation constants.

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-006 — Refactor ws_client.py to use constants module (~4 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-48)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CAN-API-015 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

### JR-CAN-TEST-016 — Replace 8 always-passing assert True tests with real assertions using pytest.raises().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 86-98)

**Detail**:

Tests in performance and integration suites use assert True in both success and exception branches. Provides false confidence; regressions undetectable.

**Notes**:

Category A: 8 critical test issues; Phase 1 critical

### JR-CAN-UI-008 — Replace debounce=True with 350ms on numeric inputs to fix perceived typing lag.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 365-499)

**Detail**:

Issue: spinner changes commit immediately but typed values require blur. 
Solution: use debounce=350ms for live feedback without callback churn. 
Also adds clientside blur-on-Apply and validation styling (invalid=True border).

**PRs**: PR-2 (Phase 6B, Issue

### JR-ML-WS-117 — replay_since(last_seq) + ReplayOutOfRange exception; copy-under-lock pattern.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 115-115)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CCL-TEST-004 — Run full test suite validation after constants refactor to ensure scenario outputs and behaviors unchanged.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 62-71)

**Detail**:

Execute: pytest tests/ -v
Verify scenario generation for two_spiral, xor_converged, and empty scenarios.
Validate metric curves, topology, and decision boundary data match pre-refactor.

**Notes**:

Validation phase of refactor (HIGH priority)

### JR-ML-SEC-013 — SEC-01: API Key Comparison Not Constant-Time — Timing Side-Channel.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 169-184)

### JR-ML-SEC-014 — SEC-02: Rate Limiter Memory Unbounded — DoS Vector.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 187-209)

### JR-ML-SEC-015 — SEC-03: No Per-IP WebSocket Connection Limiting (cascor).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 212-226)

### JR-ML-SEC-016 — SEC-04: Sync Dataset Generation Blocks Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 229-244)

### JR-ML-SEC-017 — SEC-05: Cross-Site WebSocket Hijacking (CSWSH) — No Origin Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 247-261)

### JR-ML-SEC-018 — SEC-06: No Auth on Canopy WS Endpoints.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 264-278)

### JR-ML-SEC-019 — SEC-07: Unvalidated `params` Dict Values in TrainingStartRequest.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 281-295)

### JR-ML-SEC-020 — SEC-10: Sentry `send_default_pii=True` (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 298-312)

### JR-ML-SEC-021 — SEC-11: `pickle.loads` HDF5 Snapshot Data Without RestrictedUnpickler.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 315-337)

### JR-ML-SEC-022 — SEC-12: `/ws` Generic Endpoint Missing Origin/Per-IP Validation (canopy).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 340-354)

### JR-ML-SEC-023 — SEC-13: Auth Secrets Exposed via Query Params (`/api/remote/connect`).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 357-379)

### JR-ML-SEC-024 — SEC-14: Internal Exception Messages Leaked to Clients.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 382-396)

### JR-ML-SEC-025 — SEC-15: Cascor Sentry `send_default_pii=True`.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 399-413)

### JR-ML-SEC-026 — SEC-16: `/metrics` Prometheus Endpoint Bypasses Auth Middleware.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 416-430)

### JR-ML-SEC-027 — SEC-17: Snapshot `snapshot_id` Path Param Unchecked for Traversal.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 433-447)

### JR-ML-SEC-028 — SEC-18: `_decode_binary_frame` No Bounds Check (cascor-worker).

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 450-464)

### JR-ML-ARCH-254 — Security: CSWSH closed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-WS-118 — self._pending: Dict[str, asyncio.Future] correlation map, bounded at 256 with JuniperCascorOverloadError on overflow.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 218-218)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-119 — _send_json wraps in asyncio.wait_for timeout (GAP-WS-07 quick-fix, default 0.5s).

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 114-114)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAN-OBS-006 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

### JR-ML-API-004 — Server must advertise server_instance_id (UUID) in connection_established and snapshot_seq in status endpoint.

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

### JR-CAS-TEST-005 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

### JR-ML-API-005 — SetParamsResponse wire model with extra=allow.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 224-224)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-OBS-010 — Swap PrometheusMiddleware and RequestIdMiddleware order in canopy main.py:312 to fix mis-labeling.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 162-168)

**Detail**:

G5 - Middleware order causes request-id ContextVar to be unset during metric labeling.
One-line fix. Add unit test asserting request-id header present in metric labels.

### JR-DAT-TEST-007 — Test code quality: tests must not be excluded from flake8, mypy, or pytest checks.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 58-76)

**Detail**:

TST-002: Tests excluded from Flake8 (HIGH).
TST-003: Tests excluded from MyPy (HIGH).
TST-004: Pytest warnings suppressed (HIGH).
CFG-001: Excessive Flake8 ignores E722, F401 (HIGH).
33+ flake8 violations hidden (F401 7, F541 5, SIM117 21).

**Notes**:

P1 HIGH issues. 34 total violations currently undetected.

### JR-CWK-TEST-001 — Test import mocking fix: add patch.dict(sys.modules, {"cascade_correlation": None, ...}) to test_connect_without_cascor_raises and test_start_without_cascor_raises to force ImportError regardless of JuniperCascor environment.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/history/FIX_TEST_IMPORT_MOCKING_PLAN.md` (lines 1-50)

**Detail**:

Two tests fail when run in JuniperCascor conda environment where cascade_correlation package is installed: (1) test_connect_without_cascor_raises expects ImportError handler but import succeeds, code attempts real TCP connection to manager (127.0.0.1:50000), gets ConnectionRefusedError wrapped as WorkerConnectionError, regex match fails. (2) test_start_without_cascor_raises bypasses "Not connected" guard, import succeeds, code spawns real forkserver processes, returns normally without raising. Fix: wrap both tests' calls to worker.connect()/start() in patch.dict(sys.modules, {"cascade_correlation": None, "cascade_correlation.cascade_correlation": None}), forcing ImportError on import statement. Matches existing pattern in 6 other tests (lines 87, 115, 134, 161, 186, 307). Setting sys.modules key to None causes Python's import machinery to raise ImportError: import of <module> halted; None in sys.modules.

### JR-CAN-TEST-017 — Test Suite & CI/CD Enhancements (16 epics, 145 total hours).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md`

**Detail**:

Phase 1 (21h): Eliminate false-positive tests (9 assert True), move non-test files,
fix security scan suppression.
Phase 2 (39h): Consolidate conftest.py, re-enable MyPy codes, enable linting on tests.
Phase 3 (50h): Fix weak tests, address unconditional skips, fix exception suppression,
re-enable flake8 checks, remove duplicate test classes, fix bug-documenting tests.
Phase 4 (35h): Configuration standardization, docs, future MyPy, extended suppress review.

### JR-ML-TEST-002 — testing/fake_ws_client.py: on_command(name, handler) auto-scaffold command_response reply.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 225-225)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-WS-120 — training_stream.py two-phase registration, resume/resume_ok/resume_failed handler with 5s timeout.

**Status**: proposed  **Priority**: P1  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 116-116)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-ARCH-255 — `use_websocket_set_params`: C.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 310-311)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-OBS-011 — Wire 9 cascor WS metrics (resume/replay/throttle observability) via OBS-WIRE-02, behind feature flag.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 148-162)

**Detail**:

G4 - 11 dead cascor_ws_* metrics with zero production callers defined but unwired.
OBS-WIRE-02 wires 9 viable metrics. Remove cascor_ws_seq_gap_detected_total and cascor_ws_connections_active as not feasible.
Deploy behind JUNIPER_CASCOR_WS_METRICS_FULL feature flag initially.

### JR-ML-ARCH-256 — `ws_backpressure_policy`: E.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 316-317)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-257 — `ws_rate_limit_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 314-315)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-258 — `ws_security_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 312-313)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-API-008 — 10. Phase 7: Validation and Finalization.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 232-233)

### JR-ML-API-009 — 2. Plan Overview.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 21-22)

### JR-ML-API-010 — 3. Phase 0: Prior Art Assessment.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 60-61)

### JR-ML-API-011 — 4. Phase 1: Codebase Exploration and Discovery.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 85-86)

### JR-ML-API-012 — 5. Phase 2: Deep-Dive API and Model Analysis.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 116-117)

### JR-ML-API-013 — 6. Phase 3: Interface Contract Mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 133-134)

### JR-ML-API-014 — 7. Phase 4: Discrepancy Identification.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 150-151)

### JR-ML-API-015 — 8. Phase 5: Comprehensive Documentation.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 177-178)

### JR-ML-API-016 — 9. Phase 6: Remediation Planning.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 206-207)

### JR-CAN-UI-013 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-ML-TRAIN-011 — Adam Optimizer Pathology: fix Adam optimizer pathology issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_07_ADAM_OPTIMIZER_PATHOLOGY.md` (lines 1-44)

### JR-ML-WS-122 — Adapter→cascor auth = HMAC first-frame, NOT X-Juniper-Role header.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 47-47)

**Notes**:

Settled position C-10 from R3-03 table; cross-round consensus consolidation

### JR-DCL-DOC-007 — Add Architecture & Design Patterns section to AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-118)

**Detail**:

AGENTS.md lacks architecture/design patterns section. For agents working on this codebase, understanding
the following patterns is essential: connection management (requests.Session with HTTPAdapter), retry
strategy (exponential backoff, retries on 429/5xx), URL normalization (scheme addition, trailing slash
removal, /v1 suffix handling), error mapping (HTTP status codes -> specific exception types), API key
handling (constructor param or JUNIPER_DATA_API_KEY env var), context manager pattern.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.1) and AGENTS_MD_UPDATE_PLAN (Step 3.1).

### JR-DCL-DOC-008 — Add CI/CD documentation section to AGENTS.md covering 3 GitHub Actions workflows.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-134)

**Detail**:

AGENTS.md has no CI/CD documentation. Agents making changes should know: ci.yml runs multi-version
tests (Python 3.12, 3.13, 3.14), pre-commit hooks, coverage checks (80% threshold), security scanning;
publish.yml handles PyPI publishing with trusted publishing (OIDC) and build attestations;
security-scan.yml runs weekly Bandit + pip-audit scanning.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.2) and AGENTS_MD_UPDATE_PLAN (Step 3.2).

### JR-CCL-DOC-008 — Add CI/CD Pipeline section to AGENTS.md documenting GitHub Actions workflow structure, quality gates, downstream dispatch.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 57-60)

**Notes**:

Medium severity: improves agent understanding of CI workflows

### JR-DEP-SEC-004 — Add container image security scanning (Trivy or Grype) to CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 197-203)

**Detail**:

Phase 4. Add security-scan job to CI using Trivy or Grype. Scan all locally-built
images after build step. Fail on critical/high CVEs; warn on medium. Cache
vulnerability database to reduce CI time.

### JR-CCL-DOC-009 — Add Environment Variables section to AGENTS.md documenting JUNIPER_CASCOR_API_KEY and CASCOR_SERVICE_URL.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 71-73)

**Notes**:

Medium severity: documents runtime configuration

### JR-CAS-PERF-001 — Add GPU/CUDA support for all tensor operations and training.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 885-912)

### JR-CAN-TEST-018 — Add integration tests for async/sync boundary with WebSocket responsiveness during training.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 168-189)

**Detail**:

No integration tests verify WebSocket responsiveness during active training; schedule_broadcast() uses run_coroutine_threadsafe but has no tests.

**Notes**:

Phase 2 high priority; training callbacks are registered but untested in integration context

### JR-CCL-DOC-010 — Add Linting & Formatting section to AGENTS.md documenting line length (512), tool versions, complexity limits, pre-commit hooks.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 62-64)

**Notes**:

Medium severity: supports local quality enforcement

### JR-ML-OBS-013 — Add phase="input" and phase="candidate" emission sites in cascor training_step_duration_seconds.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 169-178)

**Detail**:

G6 - training_step_duration_seconds only emits phase="output" despite SLO design intent of three phases.
Add input/candidate emission sites at corresponding training stages.

### JR-CCL-DOC-011 — Add Python Version Support note to AGENTS.md documenting >=3.11, tested on 3.11-3.14.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md`
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 78-79)

**Notes**:

Medium severity: clarifies compatibility constraints

### JR-DEP-TEST-001 — Add scheduled weekly integration tests to detect upstream breakage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 184-195)

**Detail**:

Phase 4 (v0.5.0) CI enhancement. Add schedule: cron: '0 6 * * 1' trigger to
.github/workflows/ci.yml or dedicated workflow. Run full Docker integration suite
weekly against main to detect upstream breakage. Notify on failure via GitHub Actions.

### JR-CCL-SEC-002 — Add Security section to AGENTS.md documenting SOPS encryption, Gitleaks, Bandit, pip-audit.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 75-76)

**Notes**:

Medium severity: documents security tooling

### JR-CCL-DOC-012 — Add Test Organization section to AGENTS.md documenting test structure, markers, fixtures, 80% coverage requirement.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md`
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 66-69)

**Notes**:

Medium severity: helps agents understand test conventions

### JR-CAN-PERF-002 — API timeout must be reduced for fast-interval callbacks.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 176-176)

**Detail**:

Issue 3.4.1: Default API timeout too long for frequently-polled endpoints.
Set shorter timeout (2-5s) for metrics/state endpoints, keep longer (10s) for
heavy operations like dataset upload.

### JR-DAT-API-006 — API versioning strategy defines version increment, backward-incompatibility, deprecation policy (2 minor versions notice, 6 months support).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 245-265)

**Notes**:

DATA-009 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-ML-API-017 — API-01: Health `status` Value Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5133-5148)

### JR-ML-API-018 — API-02: Health Response Schema Diverges.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5151-5165)

### JR-ML-API-019 — API-03: Canopy FSM Lacks Auto-Reset from FAILED/COMPLETED on START.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5168-5182)

### JR-ML-API-020 — API-04: FakeClient State Constants Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5185-5189)

### JR-ML-API-021 — API-05: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5192-5207)

### JR-ML-API-022 — API-06: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5210-5214)

### JR-ML-API-023 — API-07: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5217-5221)

### JR-ML-API-024 — API-08: `set_params` Includes Extraneous `type:command` Field.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5224-5232)

### JR-ML-API-025 — API-09: HTTPException Errors Bypass ResponseEnvelope.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5235-5249)

### JR-CAS-TEST-007 — Backward compatibility testing with old serialized snapshots.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

### JR-CWK-TEST-002 — Bandit B105 pre-commit false positives in test files: suppress B105 (hardcoded_password_string) in test Bandit hook, targeting known-safe test fixture credential values.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 99-106)

**Detail**:

Root cause: auth_token field matches Bandit regex (RE_WORDS includes "token") introduced in WebSocket Phase 2 refactoring after pre-commit config finalized. Original api_key didn't trigger B105 ("key" not in word list). 11 B105 false positives across 3 test files (test_cli.py:4, test_config.py:6, test_worker_agent.py:1) — all test fixtures using dummy credentials. Solution: Add B105 to --skip in .pre-commit-config.yaml test Bandit hook (line 195), maintaining numerical order (--skip=B101,B104,B105,B108,B110,B311). Source Bandit hook unaffected; detect-private-key hook catches real secrets.

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

### JR-ML-TRAIN-012 — Candidate Quality Decay: address candidate quality degradation in long training runs.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_02_CANDIDATE_QUALITY_DECAY.md` (lines 1-40)

### JR-ML-WS-123 — Canopy control buttons must resolve orphaned commands via state event arrival (fallback to explicit timeout).

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

### JR-ML-DATA-001 — Canopy metrics normalization must maintain dual-format backward compatibility (nested + flat metric keys).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-05_testing_plan.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1371-1382)

**Detail**:

Phase H: test test_normalize_metric_produces_dual_format before any audit PR.
test_normalize_metric_nested_topology_present, test_normalize_metric_preserves_legacy_timestamp_field.
Write consumer audit doc listing every consumer of nested vs flat keys across canopy frontend.
Explicit recommendation: do NOT remove either format without landing this test first.

**Notes**:

RISK-01. Phase H (Day 12) regression gate. Must not ship Phase B without test in place.

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

### JR-ML-OBS-014 — Canopy must observe set_params latency separately for WebSocket and REST transports.

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

### JR-ML-ARCH-288 — CAS-006: Auto-Snap Best Network.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2446-2450)

### JR-CAS-API-004 — CasCor service API must support separate network_epochs and candidate_epochs parameters.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 562-566)

**Notes**:

Requires API contract extension; juniper-cascor-client start_training() method update.

### JR-ML-WS-124 — Cascor SetParamsRequest has extra=forbid; canopy adapter routes unclassified keys to REST.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 46-46)

**Notes**:

Settled position C-09 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-289 — CC-01: `_recv_loop` Catches Bare `Exception`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3656-3670)

### JR-ML-ARCH-290 — CC-04: `set_params()` Method Not Documented in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3673-3687)

### JR-ML-ARCH-291 — CC-05: CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3690-3698)

### JR-ML-ARCH-292 — CC-06: `command()` Never Sends `type` Field.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3701-3708)

### JR-ML-ARCH-293 — CC-07: NpzFile Resource Leak in data-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3711-3725)

### JR-ML-ARCH-294 — CC-08: WebSocket Auto-Reconnection Not Implemented.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3728-3742)

### JR-ML-ARCH-295 — CC-13: `_recv_loop` Silently Drops Non-Correlated Server Messages.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3762-3776)

### JR-ML-ARCH-296 — CC-14: `_handle_response()` Calls `response.json()` Unconditionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3779-3793)

### JR-ML-ARCH-297 — CC-15: No TLS/SSL Configuration Support on WS Streams.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3796-3810)

### JR-ML-ARCH-298 — CC-16: `FakeCascorClient.wait_for_ready()` Returns True Immediately.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3813-3827)

### JR-ML-ARCH-299 — CC-17: `FakeCascorClient.wait_for_ready()` Missing `self._lock`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3830-3844)

### JR-ML-ARCH-300 — CFG-01: `torch` Imported but Missing from canopy Dependencies.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4883-4897)

### JR-ML-ARCH-301 — CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4900-4914)

### JR-ML-ARCH-302 — CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4917-4931)

### JR-ML-ARCH-303 — CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4934-4948)

### JR-ML-ARCH-304 — CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4951-4965)

### JR-ML-ARCH-305 — CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4968-4982)

### JR-ML-ARCH-306 — CFG-07: Port 8200 vs 8201 Confusion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4985-4999)

### JR-ML-ARCH-307 — CFG-08: Rate Limiting Defaults Differ Across Services.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5002-5016)

### JR-ML-ARCH-308 — CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5019-5041)

### JR-ML-ARCH-309 — CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5044-5058)

### JR-ML-ARCH-310 — CFG-13: `python-dotenv` in canopy Core Deps but Never Imported.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5061-5075)

### JR-ML-ARCH-311 — CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5078-5092)

### JR-ML-ARCH-312 — CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5095-5109)

### JR-ML-TEST-003 — Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 69-69)

**Notes**:

Settled position C-32 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-313 — CI-01: cascor-client CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4643-4657)

### JR-ML-ARCH-314 — CI-02: cascor-worker CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4660-4664)

### JR-ML-ARCH-315 — CI-03: juniper-deploy CI Runs ZERO Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4667-4681)

### JR-ML-ARCH-316 — CI-04: Missing Weekly security-scan.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4684-4695)

### JR-ML-ARCH-317 — CI-05: Missing lockfile-update.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4698-4709)

### JR-ML-ARCH-318 — CI-06: juniper-deploy No Coverage Configuration.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4712-4723)

### JR-ML-ARCH-319 — CI-07: Inconsistent GitHub Actions Versions Across Repos.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4726-4737)

### JR-ML-ARCH-320 — CI-SEC-01: No Weekly Security Scan for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4838-4842)

### JR-ML-ARCH-321 — CI-SEC-02: No Security Scanning in juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4845-4856)

### JR-ML-TOOL-001 — CLN-CC-01: Delete Legacy `remote_client/` Directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1317-1343)

### JR-ML-TOOL-002 — CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1346-1361)

### JR-ML-TOOL-003 — CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1364-1378)

### JR-ML-TOOL-004 — CLN-CC-04: Enable mypy Strict Mode.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1381-1395)

### JR-ML-TOOL-005 — CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1398-1412)

### JR-ML-TOOL-006 — CLN-CC-06: Remove "Roll" Concept in CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1415-1421)

### JR-ML-TOOL-007 — CLN-CC-07: Candidate Factory Refactor.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1424-1430)

### JR-ML-TOOL-008 — CLN-CC-08: Remove Commented-Out Code Blocks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1433-1439)

### JR-ML-TOOL-009 — CLN-CC-09: Line Length Reduction to 120 Characters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1442-1448)

### JR-ML-TOOL-010 — CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1451-1473)

### JR-ML-TOOL-011 — CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1476-1490)

### JR-ML-TOOL-012 — CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1493-1507)

### JR-ML-TOOL-013 — CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1510-1524)

### JR-ML-TOOL-014 — CLN-CC-14: Empty `# TODO :` Headers in 18+ Files.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1527-1541)

### JR-ML-TOOL-015 — CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1544-1558)

### JR-ML-TOOL-016 — CLN-CN-01: `theme-table` CSS Class Never Implemented.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1563-1588)

### JR-ML-TOOL-017 — CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1591-1605)

### JR-ML-TOOL-018 — CLN-CN-03: Performance Test Suite Minimal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1608-1622)

### JR-ML-TOOL-019 — CLN-CN-04: JuniperData-Specific Error Handling Missing.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1625-1639)

### JR-ML-TOOL-020 — CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1642-1657)

### JR-ML-TOOL-021 — CLN-CN-06: Re-enable Remaining MyPy Disabled Codes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1660-1674)

### JR-ML-TOOL-022 — CLN-CN-07: Real Backend Path Test Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1677-1691)

### JR-ML-TOOL-023 — CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1694-1708)

### JR-ML-TOOL-024 — CLN-CN-09: main.py Coverage Gap (84% vs 95% Target).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1711-1725)

### JR-ML-TOOL-025 — CLN-CN-10: `main.py` Is 2,543 Lines — Second God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1728-1742)

### JR-ML-TOOL-026 — CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1745-1759)

### JR-ML-TOOL-027 — CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1762-1776)

### JR-ML-TOOL-028 — CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1779-1793)

### JR-ML-TOOL-029 — CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1796-1810)

### JR-ML-TOOL-030 — CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1815-1829)

### JR-ML-TOOL-031 — CLN-JD-02: `FakeDataClient.close()` Destroys Data.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1832-1846)

### JR-ML-TOOL-032 — CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1849-1863)

### JR-DEP-SEC-005 — Close secret-leak detection bypass via Gitleaks path-based allowlisting.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SECURITY_REMEDIATION_PLAN.md` (lines 29-91)

**Detail**:

Gitleaks .gitleaks.toml blanket-allows files matching *.env.enc and *.env.secrets.enc,
creating bypass path for plaintext secrets. Root causes: (1) path-based allowlisting exempts
matching files from all rules, (2) pre-commit hook skipped in CI, (3) weak SOPS metadata validation
(only grep "^sops_" check). Remediation: replace path allowlist with content-based ciphertext regex,
remove CI skip, strengthen to multi-field SOPS validation + ciphertext line check.

### JR-ML-WS-125 — command_response has NO seq field; /ws/control has no replay buffer.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 39-39)

**Notes**:

Settled position C-02 from R3-03 table; cross-round consensus consolidation

### JR-CAN-API-016 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-DEP-TOOL-002 — Consolidate demo dataset parameters and shell script timeouts into config.sh.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 93-117)

**Detail**:

Shell scripts have 8 hardcoded timeouts (90s service wait, 3s poll, 3s curl, 5s health,
120s demo test, 3s demo poll, 5s training start, 90s enhanced test). Demo has 7 hardcoded
parameters (n_spirals=2, n_points=200, noise=0.15, seed=42, learning_rate=0.01, 500 epochs).
Source all from scripts/config.sh. Lower priority (LOW) per analysis.

### JR-CAN-TEST-019 — Consolidate duplicate conftest.py fixtures into single configuration file.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 122-128)

**Detail**:

Two conftest.py files (445 + 224 lines) contain overlapping fixtures. Consolidate to avoid duplication and maintenance burden.

**Notes**:

Category D: Duplicate fixtures; DRY principle violation

### JR-ML-TEST-004 — Contract-test pytest marker contract runs on every PR, NOT nightly.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 71-71)

**Notes**:

Settled position C-34 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-013 — Convergence Timing: optimize convergence detection timing.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_04_CONVERGENCE_TIMING.md` (lines 1-46)

### JR-ML-WS-126 — Correlation field is command_id, NOT request_id.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 38-38)

**Notes**:

Settled position C-01 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-322 — COV-01: Deploy Tests Exist but Zero Coverage.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4740-4744)

### JR-ML-ARCH-323 — COV-02: Canopy No Per-Module Coverage Gate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4747-4758)

### JR-ML-ARCH-324 — COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4761-4772)

### JR-DAT-OBS-004 — Coverage reporting must upload to external service (Codecov, Coveralls) for trend tracking.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 68-69)

**Notes**:

INF-002 MEDIUM (P2).

### JR-CAS-OBS-003 — Create baseline py-spy profiles for key operations to enable performance regression detection.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 850-854)

### JR-DCL-ARCH-001 — Create juniper_data_client/constants.py module to centralize ~60 hardcoded values across codebase.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 130-145)

**Detail**:

Codebase contains ~89 hardcoded values across 6 files with no centralized constants module.
Only 3 values are defined as class-level constants on JuniperDataClient (DEFAULT_TIMEOUT, DEFAULT_RETRIES,
DEFAULT_BACKOFF_FACTOR); remaining values (16 API endpoints, connection pool sizes, HTTP status codes,
generator defaults) are inline literals. Create single constants.py organized into 7 sections:
(1) HTTP Configuration, (2) API Endpoints, (3) Timeouts & Polling, (4) Authentication,
(5) Generator Defaults, (6) Generator Mathematics, (7) Data Types.

**Design**:

Recommended structure: single juniper_data_client/constants.py (~60 constants).
Maintain backward compatibility by keeping class-level constants as aliases referencing module constants.
Validate all generator outputs match current behavior with integration tests.
Keep mathematical constants clearly separated from configuration constants.

### JR-DEP-DEP-004 — Create systemd health timer and one-shot units for periodic service health checks.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 185-220)

**Detail**:

Six new units (3 timers + 3 one-shots) for juniper-data, juniper-cascor, juniper-canopy.
Timers fire every 30 seconds (OnActiveSec=30, OnUnitActiveSec=30, AccuracySec=5s).
One-shot units run health_check_systemd.sh, query /v1/health/ready endpoint, parse JSON,
output structured results to journal. Non-zero exit enables OnFailure= triggers.

### JR-ML-ARCH-325 — CW-01: `receive_json()` Doesn't Catch JSONDecodeError.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3906-3920)

### JR-ML-ARCH-326 — CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3923-3937)

### JR-ML-ARCH-327 — CW-03: No Integration Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3940-3954)

### JR-ML-ARCH-328 — CW-04: Timeout Error Sends `candidate_uuid: ""` Instead of Actual UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3957-3971)

### JR-ML-ARCH-329 — CW-05: Dynamic Import `from candidate_unit.candidate_unit import CandidateUnit`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3974-3996)

### JR-ML-ARCH-330 — CW-06: `receive_json()` in Registration Path — No JSONDecodeError Catch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3999-4006)

### JR-ML-ARCH-331 — CW-07: No Validation of `tensor_manifest` Keys Against Received Binary Frames.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4009-4023)

### JR-ML-ARCH-332 — CW-08: Top-Level `import torch` — First-Task Latency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4026-4040)

### JR-CAN-ARCH-004 — DashboardManager must be refactored for extract to <2000 lines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 177-177)

**Detail**:

Issue 3.4.2: DashboardManager is monolithic. Begin extraction of sidebar,
controls, stores, and theme logic into separate modules. Post-refactor target: <2000 lines.

### JR-ML-ARCH-333 — DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles".

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3849-3853)

### JR-ML-ARCH-334 — DC-02: GENERATOR_MOON = "moon" — No Server Generator.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3856-3860)

### JR-ML-ARCH-335 — DC-03: Missing Constants for 5 Server Generators.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3863-3867)

### JR-ML-ARCH-336 — DC-04: `FakeDataClient` Masks Generator Name Bugs.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3870-3884)

### JR-ML-ARCH-337 — DC-05: `FakeDataClient` Missing Lifecycle Methods.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3887-3901)

### JR-ML-UI-015 — Debounce lives in Dash clientside callback, NOT SDK.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 66-66)

**Notes**:

Settled position C-29 from R3-03 table; cross-round consensus consolidation

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

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

### JR-ML-ARCH-338 — DEPLOY-01: Docker Secret Name/Path Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3335-3349)

### JR-ML-ARCH-339 — DEPLOY-02: AlertManager Service Missing from docker-compose.yml.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3352-3366)

### JR-ML-ARCH-340 — DEPLOY-04: K8s Canopy Missing Service URL Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3386-3397)

### JR-DCL-DOC-009 — Document JuniperDataClient exception hierarchy with HTTP status code mapping in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-116)

**Detail**:

Exception hierarchy is mentioned only in Key Files, not fully documented. Must show full exception tree
(JuniperDataClientError parent with 5 specific exceptions) and HTTP status code -> exception type mapping.
Essential context for agents working on error handling and debugging.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.3) and AGENTS_MD_UPDATE_PLAN (Step 3.3).

### JR-ML-OBS-015 — emitted_at_monotonic: float on every /ws/training broadcast envelope.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 78-78)

**Notes**:

Settled position C-41 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-004 — Error-budget burn-rate rule operationally binding.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 79-79)

**Notes**:

Settled position C-42 from R3-03 table; cross-round consensus consolidation

### JR-DEP-TEST-002 — Extend compose validation to cover observability and production profiles.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 205-211)

**Detail**:

Phase 4. validate-compose job in ci.yml already validates full, demo, dev profiles.
Extend to validate observability and production profiles as added. Add JSON schema
validation for Grafana dashboard files (Phase 1 output).

### JR-CAN-ARCH-005 — Extract create_empty_plot() as shared utility across metric panels.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 162-162)

**Detail**:

Issue 3.2.3: create_empty_plot logic duplicated in multiple components.
Extract to plot_utils.py or equivalent shared module.

### JR-ML-DOC-002 — Fix 17 broken markdown links in DEVELOPER_CHEATSHEET.md - 12 self-referencing and 5 missing intra-repo files.

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

### JR-DAT-TEST-008 — Fix 21 SIM117 violations (nested with statements) by combining where Python 3.11+ allows.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 247-266)

**Notes**:

RD-008 LOW priority deferred. Currently in ruff ignore list in pyproject.toml.

### JR-ML-TOOL-033 — Fix broken check_object_pickleability function in utils.py:238 which uses dill not in dependencies.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3580-3590)

**Detail**:

CLN-CC-10: utils.py:238 imports and uses `dill` library which is not in project dependencies.
Function is broken. Fix by either adding dill to deps or refactoring to use pickle only.

### JR-CAS-DOC-002 — Fix import alias mistake: datetime import uses pd instead of dt.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 362-366)

**Detail**:

Line 38 of cascade_correlation.py: 'import datetime as pd' should be 'import datetime as dt'. pd is conventionally pandas; using for datetime misleads developers.

### JR-ML-DOC-003 — Fix semantic error in SECURITY_AUDIT_PLAN.md line 845 - correct deep relative path to ../CLAUDE.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 246-264)

**Detail**:

Category D false-negative: ../../../CLAUDE.md resolves to wrong document via repo-root fallback.
Should be ../CLAUDE.md to reference repo's own CLAUDE.md (symlink to AGENTS.md) containing the same #worktree-procedures-mandatory--task-isolation section.

### JR-CAS-TRAIN-013 — Fix validate_training_results None initialization bug in training loop.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 374-378)

**Detail**:

Variable initialized as None; if training loop doesn't execute (e.g. max_epochs=0), debug log crashes with AttributeError on .early_stop.

### JR-ML-OBS-016 — GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy /api/ws_latency + histogram).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 57-57)

**Notes**:

Settled position C-20 from R3-03 table; cross-round consensus consolidation

### JR-DAT-SEC-003 — GitHub Actions versions must be pinned to SHA, not floating refs.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 62-63)

**Notes**:

SEC-004 MEDIUM (P2). ci.yml:70,73,84, etc.

### JR-CAN-UI-015 — Hardcoded colors must be extracted to theme_constants.py for DRY.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 168-168)

**Detail**:

Issue 3.3.1: Color strings repeated across components. Extract to
theme_constants.py for centralized management and dark/light theme support.

### JR-CWK-ARCH-002 — Hardcoded values refactoring: create juniper_cascor_worker/constants.py to consolidate ~50 hardcoded values (protocol messages, activation functions, training defaults, WebSocket config, validation bounds).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 1-50)

**Detail**:

~50 hardcoded values across 7 source files. Existing infrastructure: config.py WorkerConfig dataclass (8 field defaults, partial coverage). Gaps: protocol message type strings (7), activation function names (3), training hyperparameters (6 — epochs, learning rate, display frequency, value scales), WebSocket config (4), config duplicates across config.py/cli.py/env defaults (6), validation constants (2), error handling (2). Coverage summary: ~3 covered (partial), ~47 not covered. Proposed solution: create constants.py with sections for protocol types, activation functions, training defaults, WebSocket, config defaults, validation, error handling. Update config.py, cli.py, worker.py, task_executor.py, ws_connection.py to import from constants.py. Key benefit: eliminates 3-way duplication between config.py, cli.py, env var defaults.

### JR-DAT-OBS-005 — Histogram R5.1 ratification decides SLO targets p95 <100ms and p99 <1s, optionally collapses low-information buckets.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 71-87)

**Notes**:

Tentative layout pending R5.1 SLO design. HELP-string marker points to rationale doc.

### JR-ML-ARCH-341 — HSK-01: 3 Broken Symlinks in canopy `notes/development/`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2881-2895)

### JR-ML-ARCH-342 — HSK-02: `src/remote_client/` Directory Still Exists.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2898-2902)

### JR-ML-ARCH-343 — HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2905-2909)

### JR-ML-ARCH-344 — HSK-04: 32 Test Files with Hardcoded `sys.path.append`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2912-2916)

### JR-ML-ARCH-345 — HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2919-2933)

### JR-ML-ARCH-346 — HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2936-2940)

### JR-ML-ARCH-347 — HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2943-2947)

### JR-ML-ARCH-348 — HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2950-2954)

### JR-ML-ARCH-349 — HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2957-2982)

### JR-ML-ARCH-350 — HSK-10: `scripts/test.bash` Outdated/Non-Functional.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2985-3010)

### JR-ML-ARCH-351 — HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3013-3028)

### JR-ML-ARCH-352 — HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3031-3045)

### JR-ML-ARCH-353 — HSK-13: 169 Hardcoded ThemeColors Remain in canopy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3048-3062)

### JR-ML-ARCH-354 — HSK-14: `resume_session.bash` Contains Hardcoded Session UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3065-3087)

### JR-ML-ARCH-355 — HSK-15: `util/global_text_replace.bash` Is a No-Op.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3090-3112)

### JR-ML-ARCH-356 — HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3115-3129)

### JR-ML-ARCH-357 — HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3132-3146)

### JR-ML-ARCH-358 — HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3149-3163)

### JR-ML-ARCH-359 — HSK-19: Stale Files in Repo Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3166-3180)

### JR-ML-ARCH-360 — HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3183-3198)

### JR-ML-ARCH-361 — HSK-21: `wake_the_claude.bash:53` Stale TODO Comment.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3201-3215)

### JR-ML-ARCH-362 — HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3218-3232)

### JR-ML-ARCH-363 — HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3235-3249)

### JR-ML-ARCH-364 — HSK-24: Unused Constants in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3252-3277)

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

### JR-CAS-TEST-008 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-ML-DATA-002 — JD-PERF-01: Sync `generator.generate()` Blocks Event Loop.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3534-3538)

### JR-ML-DATA-003 — JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3541-3555)

### JR-ML-DATA-004 — JD-PERF-03: `list_versions` Loads All Metadata.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3558-3569)

### JR-ML-DATA-005 — JD-PERF-04: No Connection Pooling for Postgres.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3572-3586)

### JR-ML-DATA-006 — JD-PERF-05: Readiness Probe Filesystem Glob.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3589-3593)

### JR-ML-DATA-007 — JD-SEC-01: Path Traversal via `dataset_id` in Filesystem Paths.

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3485-3507)

### JR-ML-DATA-008 — JD-SEC-02: API Key Comparison Not Constant-Time (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3510-3518)

### JR-ML-DATA-009 — JD-SEC-03: Rate Limiter Memory Unbounded (data).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3521-3529)

### JR-ML-SEC-030 — JUNIPER_WS_ALLOWED_ORIGINS=* explicitly REFUSED by the parser.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 67-67)

**Notes**:

Settled position C-30 from R3-03 table; cross-round consensus consolidation

### JR-ML-OPS-005 — Kill switch MTTR ≤5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 76-76)

**Notes**:

Settled position C-39 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-017 — KL-1: Dataset Scatter Plot Empty in Service Mode.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1963-1977)

### JR-ML-TEST-005 — Latency tests are recording-only in CI (latency_recording marker); strict assertions local-only.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 72-72)

**Notes**:

Settled position C-35 from R3-03 table; cross-round consensus consolidation

### JR-CAN-UI-016 — Modulo toggle for theme switching must use Dash State, not module-level flag.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 169-169)

**Detail**:

Issue 3.3.2: Theme toggle using module-level variable instead of callback State.
Can cause race conditions in multi-user scenarios. Use dcc.Store for theme state.

### JR-CAN-TEST-020 — Move 5 non-test files (scripts, manual verifiers) out of test directory to util/.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 99-108)

**Detail**:

Files like test_yaml.py, test_dashboard_init.py are print-based scripts with no assertions. Should be moved to util/ for clarity.

**Notes**:

Category B: 5 files; Phase 1 high priority

### JR-CAN-ARCH-006 — NetworkVisualizer callback is overloaded and must be split.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 172-172)

**Detail**:

Issue 3.3.5: Single callback handles too many inputs. Split into separate
callbacks for layout changes, theme changes, and data updates.

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

### JR-ML-OBS-017 — Observability-before-behavior rule: metrics + panels + alerts land BEFORE behavior change.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 75-75)

**Notes**:

Settled position C-38 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-127 — One-resume-per-connection rule (second resume → close 1003).

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 62-62)

**Notes**:

Settled position C-25 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-014 — Output Weight Initialization: improve output layer weight init.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_05_OUTPUT_WEIGHT_INIT.md` (lines 1-38)

### JR-ML-OBS-018 — P0 success metric: canopy_rest_polling_bytes_per_sec reduced >90% vs baseline.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 74-74)

**Notes**:

Settled position C-37 from R3-03 table; cross-round consensus consolidation

### JR-CAN-PERF-003 — Parameter retry logic must not use blocking time.sleep().

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 171-171)

**Detail**:

Issue 3.3.4: Blocking sleep in parameter retry callback blocks event loop.
Use asyncio.sleep() or defer via callback scheduling instead.

### JR-ML-SEC-031 — Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 63-63)

**Notes**:

Settled position C-26 from R3-03 table; cross-round consensus consolidation

### JR-ML-PERF-004 — PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4109-4123)

### JR-ML-PERF-005 — PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4126-4140)

### JR-ML-PERF-006 — PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4143-4157)

### JR-ML-PERF-007 — PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4075-4089)

### JR-ML-PERF-008 — PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4092-4106)

### JR-ML-PERF-009 — PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4160-4182)

### JR-ML-PERF-010 — PERF-JD-02: High-Cardinality Prometheus Labels.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4185-4193)

### JR-ML-TRAIN-015 — Phantom Inter-Cascade Training Phase: remove 1-step/epoch phantom training phase.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_01_PHANTOM_TRAINING_PHASE.md` (lines 30-49)

### JR-ML-ARCH-365 — Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 49-49)

**Notes**:

Settled position C-12 from R3-03 table; cross-round consensus consolidation

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

### JR-ML-ARCH-366 — Phase 4:.

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

### JR-ML-DEP-004 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 1472-1672)

### JR-CAN-TEST-021 — Phase 4 Test Coverage Expansion (14 tasks).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 189-214)

**Detail**:

Step 4.1 (4 gap fills): Test discovery, observability (Prometheus/Sentry),
secrets_util (SOPS paths), middleware edge cases (malformed headers).
Step 4.2 (4 new types): Security tests (auth, injection, CORS), WebSocket load,
circuit breaker resilience, API contract validation.

### JR-ML-DEP-005 — Phase 5:.

**Status**: proposed  **Priority**: P2  **Category**: DEP  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` (lines 2348-2548)

### JR-CAN-DOC-004 — Phase 5 Housekeeping (19 low-priority tasks across config, logging, CI/CD).

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 218-255)

**Detail**:

5.1 (5 config): Deprecation warnings, boolean/int precedence, env var migration,
Black target-version, CPU-only conda env.
5.2 (4 logging): Capture call site, timezone-aware timestamps, replace print(),
resolve FATAL_LEVEL conflict.
5.3 (6 code): AttributeError fix, message size check, exception type narrowing,
parameter forwarding, hit_rate format verification, theme-aware colors.
5.4 (4 CI/CD): Docker health check, shellcheck severity, pre-commit autoupdate,
codecov docs.

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

### JR-ML-WS-128 — Phase B ships behind two flags: enable_browser_ws_bridge + disable_ws_bridge.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 51-51)

**Notes**:

Settled position C-14 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-367 — Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 50-50)

**Notes**:

Settled position C-13 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-129 — Phase C (P2 priority): Canopy adapter hot/cold param split; hot→WS via `command_id`; REST fallback; flag-off default.

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

### JR-ML-ARCH-368 — Phase C flag use_websocket_set_params=False default; 6 hard flip gates.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 65-65)

**Notes**:

Settled position C-28 from R3-03 table; cross-round consensus consolidation

### JR-ML-PERF-011 — Phase E (conditional): Per-client pump tasks + bounded queues + backpressure policy matrix.

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

### JR-ML-PERF-012 — Phase E default backpressure = drop_oldest_progress_only.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 52-52)

**Notes**:

Settled position C-15 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-130 — Phase F (optional): Application-level `ping`/`pong` heartbeat, dead-connection detection, uncapped reconnect.

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

### JR-ML-TEST-006 — Phase G (integration tests): 15 cascor `/ws/control` set_params tests via FastAPI TestClient + contract lane.

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

### JR-ML-DOC-004 — Phase H: `_normalize_metric` dual-format regression test + consumer audit + CODEOWNERS hard gate.

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

### JR-ML-TRAIN-016 — Post-Reset Desynchronization: fix desync after model reset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_10_POST_RESET_DESYNC.md` (lines 1-38)

### JR-DAT-DOC-001 — Production startup must use create_app() factory: uvicorn juniper_data.api.app:create_app --factory or python -m juniper_data.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 239-250)

**Notes**:

D-050 MEDIUM priority. Current docs show direct app reference.

### JR-ML-ARCH-369 — PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5252-5266)

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

### JR-CAN-TEST-022 — Re-enable MyPy error codes currently disabled (15 codes); fix underlying type issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 160-165)

**Detail**:

.pre-commit-config.yaml disables 15 MyPy error codes, reducing type checking effectiveness. Phase 2 work to fix underlying issues, then re-enable codes.

**Notes**:

Category H: 15 codes disabled; type safety issue

### JR-DCL-ARCH-002 — Refactor client.py to import from constants.py module (~25 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 38-41)

**Detail**:

client.py contains ~25 hardcoded values (base URL, endpoints, pool config, status codes) that must be
migrated to constants.py. This refactor depends on dcl-010 (creation of constants.py).

### JR-DCL-ARCH-003 — Refactor testing/fake_client.py to import from constants.py (~20 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-45)

**Detail**:

testing/fake_client.py contains ~20 hardcoded values (URLs, training defaults, worker data) that must be
migrated to constants.py. Depends on dcl-010.

### JR-DCL-ARCH-004 — Refactor testing/generators.py to import from constants.py (~30 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-49)

**Detail**:

testing/generators.py contains ~30 hardcoded values (math constants, dataset defaults) for spiral, xor,
circle, and moon generators that must be migrated to constants.py. Depends on dcl-010.

### JR-ML-TOOL-034 — Remove 9 stale local import traceback statements from cascade_correlation.py by uncomenting top-level import at line 64.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3568-3580)

**Detail**:

CLN-CC-03: 9 local `import traceback` statements scattered in cascade_correlation.py
across lines 2270, 2804, 3775, 3840 and other files. Consolidate via uncommented 
line 64 top-level import. Effort: 30 minutes.

### JR-CAN-DOC-005 — Remove commented-out imports across codebase.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 164-164)

**Detail**:

Issue 3.2.5: Commented imports clutter code. Remove or restore with rationale.

### JR-ML-TOOL-035 — Remove committed .ipynb_checkpoints directories from repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3590-3600)

**Detail**:

CLN-CC-12: Jupyter notebook checkpoint directories committed to repository in 
src/cascade_correlation/.ipynb_checkpoints/, src/candidate_unit/, src/
These should be in .gitignore. Effort: 10 minutes.

### JR-CAN-ARCH-007 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

### JR-CAS-ARCH-005 — Remove direct absolute path hardcoding that breaks on non-development machines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 142-146)

**Notes**:

Use relative paths or environment-relative configuration.

### JR-ML-ARCH-370 — Remove module-level sys.path.append in cascade_correlation.py:69.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3600-3610)

**Detail**:

CLN-CC-13: sys.path manipulation at module level in cascade_correlation.py:69
is an anti-pattern. Refactor to use proper imports or package structure.

### JR-CAN-ARCH-008 — Remove or deprecate legacy TrainingMetricsComponent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 163-163)

**Detail**:

Issue 3.2.4: TrainingMetricsComponent appears unused. Verify no references
and remove, or document deprecation plan and mark with DeprecationWarning.

### JR-CAN-ARCH-009 — Remove orphaned candidate callbacks from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 161-161)

**Detail**:

Issue 3.2.2: Callbacks in MetricsPanel that reference removed candidate display.
Remove or reconnect to active candidate pool UI.

### JR-CAN-TEST-023 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

### JR-CAS-ARCH-006 — Replace Path truthiness checks with explicit None checks.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 394-398)

**Detail**:

Path objects are always truthy even for empty strings. Use 'if x is None' instead of 'or' fallback patterns (lines 3015, 3096, 471).

### JR-ML-WS-131 — Replay buffer = 1024 entries, env-configurable via JUNIPER_WS_REPLAY_BUFFER_SIZE.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 42-42)

**Notes**:

Settled position C-05 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-132 — replay_buffer_capacity added to connection_established.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 44-44)

**Notes**:

Settled position C-07 from R3-03 table; cross-round consensus consolidation

### JR-ML-TRAIN-017 — Residual Variance Collapse: address residual variance collapse in training.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_09_RESIDUAL_VARIANCE_COLLAPSE.md` (lines 1-46)

### JR-ML-WS-133 — REST fallback cadence during disconnect = 1 Hz.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 54-54)

**Notes**:

Settled position C-17 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-134 — Ring-bound enforced in the handler, NOT the drain callback.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 56-56)

**Notes**:

Settled position C-19 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-371 — RISK: Correctness: no seq gaps.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-372 — RISK: Correctness: no state loss.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-ML-ARCH-373 — RISK: Criterion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

### JR-ML-ARCH-374 — RISK: Observability: full pipe.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-375 — RISK: **P0: polling eliminated**.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-376 — RISK: Recovery: kill switches work.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-ARCH-377 — RISK: Security: CSWSH closed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-ARCH-378 — ROBUST-01: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4574-4597)

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-DAT-OBS-006 — SARIF upload must fail on error, not continue-on-error.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 70-71)

**Notes**:

INF-004 MEDIUM (P2). ci.yml:320.

### JR-ML-WS-135 — SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 41-41)

**Notes**:

Settled position C-04 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-136 — server_instance_id = programmatic key; server_start_time = advisory only.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 43-43)

**Notes**:

Settled position C-06 from R3-03 table; cross-round consensus consolidation

### JR-ML-WS-137 — set_params default timeout = 1.0 s.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 40-40)

**Notes**:

Settled position C-03 from R3-03 table; cross-round consensus consolidation

### JR-DAT-TEST-009 — Slow test job must be scheduled separately for integration and performance tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 69-70)

**Notes**:

INF-003 MEDIUM (P2).

### JR-ML-TRAIN-018 — Spiral Complexity: limit spiral depth and complexity growth.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_03_SPIRAL_COMPLEXITY.md` (lines 1-50)

### JR-ML-DOC-005 — Stabilize CI documentation link validation by implementing cross-repo link classification and worktree directory exclusion.

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

### JR-CAS-TRAIN-014 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-ML-TRAIN-019 — Tanh Saturation: address tanh saturation issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_06_TANH_SATURATION.md` (lines 1-38)

### JR-CWK-TEST-003 — Test warning elimination: suppress DeprecationWarnings in test_worker.py (expected legacy API tests), RuntimeWarnings for unawaited CascorWorkerAgent coroutines, enforce warnings-as-errors baseline in pyproject.toml.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 107-144)

**Detail**:

DeprecationWarnings (23): CandidateTrainingWorker.__init__() emits at worker.py:326; test_worker.py exercises deprecated legacy API. Solution: module-level pytestmark filterwarnings in test_worker.py. RuntimeWarnings (3): unawaited CascorWorkerAgent.run() coroutines during mock-based test cleanup. Solution: targeted filterwarnings in pyproject.toml for coroutine pattern. Baseline: filterwarnings = ["error", ...] in pytest config treats all warnings as errors by default with explicit exceptions for known, intentional warnings. Prevents silent warning accumulation; new unexpected warnings cause test failures.

### JR-ML-OPS-006 — Total effort: 13.5 expected engineering days / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 73-73)

**Notes**:

Settled position C-36 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-379 — TQ-01: 10+ Tests with No Assertions (cascor).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4775-4786)

### JR-ML-ARCH-380 — TQ-02: 149 `time.sleep` Calls in canopy Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4789-4800)

### JR-ML-ARCH-381 — TQ-03: Worker Config Validation Tests with No Assertions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4803-4814)

### JR-ML-ARCH-382 — TQ-04: 139 `hasattr` Guards in cascor Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4817-4821)

### JR-ML-ARCH-383 — TQ-05: 10 Unit Tests Import httpx (Integration-Level).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4824-4835)

### JR-ML-WS-138 — Two-phase registration via _pending_connections set.

**Status**: proposed  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 45-45)

**Notes**:

Settled position C-08 from R3-03 table; cross-round consensus consolidation

### JR-ML-UI-021 — UI Lock and Visualization: UI locking during training and visualization improvements.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_08_UI_LOCK_AND_VISUALIZATION.md` (lines 1-45)

### JR-CCL-DOC-013 — Update AGENTS.md and CHANGELOG.md documentation after hardcoded-values refactor completion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 76-79)

**Notes**:

Documentation & release phase (MEDIUM priority)

### JR-DEP-OPS-002 — Update AGENTS.md with directory layout, security architecture, CI pipeline, network topology.

**Status**: proposed  **Priority**: P2  **Category**: OPS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 29-143)

**Detail**:

Phase 2 (P1 priority) add missing major sections: directory layout, security architecture
(networks, container hardening, secrets), CI/CD pipeline (4 jobs, multi-repo checkout, pinned actions),
Docker Compose profiles (profile-to-service mapping), network architecture, Makefile targets.
Phase 3 complete existing sections: expand service ports table, key files table, dependency graph,
environment variables, essential commands. Phase 4 update metadata, add documentation index, testing architecture.

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

### JR-ML-API-026 — Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 77-77)

**Notes**:

Settled position C-40 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-019 — ws-metrics-buffer store shape = {events, gen, last_drain_ms}.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 55-55)

**Notes**:

Settled position C-18 from R3-03 table; cross-round consensus consolidation

### JR-ML-SEC-032 — ws_security_enabled=True (positive sense), NOT disable_ws_auth.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 64-64)

**Notes**:

Settled position C-27 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-384 — XREPO-01: Generator Name `"circle"` vs Server's `"circles"`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2509-2524)

### JR-ML-ARCH-385 — XREPO-02: 503 Not in `RETRYABLE_STATUS_CODES`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2571-2586)

### JR-ML-ARCH-386 — XREPO-03: No `FakeCascorControlStream` — Testing Gap for WS Control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2589-2604)

### JR-ML-ARCH-387 — XREPO-04: Protocol Constants Alignment Is Manual.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2607-2629)

### JR-ML-ARCH-388 — XREPO-05: State Name Inconsistency — UPPERCASE vs Title-Case vs FSM Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2632-2646)

### JR-ML-ARCH-389 — XREPO-06: `epochs_max` Default Discrepancy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2649-2663)

### JR-ML-ARCH-390 — XREPO-07: `command()` vs `set_params()` Message Format Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2666-2681)

### JR-ML-ARCH-391 — XREPO-08: Three Distinct WS Message Formats.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2684-2692)

### JR-ML-ARCH-392 — XREPO-09: Client `create_dataset()` Missing `tags` and `ttl_seconds`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2695-2709)

### JR-ML-ARCH-393 — XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2712-2726)

### JR-ML-ARCH-394 — XREPO-11: Client Retries Non-Idempotent Mutations (POST, DELETE).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2729-2743)

### JR-ML-ARCH-395 — XREPO-12: `y` Tensor Received but Never Used in Worker.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2746-2760)

### JR-ML-ARCH-396 — XREPO-13: Health Endpoint `status` Value Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2763-2771)

### JR-ML-ARCH-397 — XREPO-14: FakeClient State Constants Use Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2774-2789)

### JR-ML-ARCH-398 — XREPO-15: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2792-2800)

### JR-ML-ARCH-399 — XREPO-16: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2803-2818)

### JR-ML-ARCH-400 — XREPO-17: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2821-2836)

### JR-CAN-DOC-006 — Add deprecation warnings to remaining legacy env validators.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 227-227)

**Detail**:

Issue 5.1.1: Legacy env var validators need deprecation warnings.
Use warnings.warn() to alert users of upcoming removal.

### JR-DAT-DOC-002 — AGENTS.md must document current project structure, components, security, dependencies (15+ entries for components).

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 45-64)

**Notes**:

D-001 through D-050 catalogued. 5 CRITICAL issues (version, security, line length, directory, middleware).

### JR-CAN-OBS-008 — All print() statements must be replaced with logger.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 237-237)

**Detail**:

Issue 5.2.3: print() bypasses logging config. Replace with appropriate
logger.info/debug/warning calls throughout codebase.

### JR-CAN-LOCK-002 — Black code formatter must have py314 in target-version.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 230-230)

**Detail**:

Issue 5.1.4: pyproject.toml Black config needs py314 for Python 3.14 compatibility.
Add to target-version list.

### JR-CAN-LOCK-003 — CASCOR_SNAPSHOT_DIR env var must be migrated to JUNIPER_CANOPY_SNAPSHOT_DIR.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 229-229)

**Detail**:

Issue 5.1.3: Old env var still referenced. Support both for compatibility
but document migration path and plan removal date.

### JR-CAN-DOC-007 — Codecov build count assumption must be documented.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 254-254)

**Detail**:

Issue 5.4.4: Codecov configuration makes implicit assumptions about build
frequency. Document in README or config comments what build count limit is
set to and why.

### JR-CAN-LOCK-004 — CPU-only conda environment must be created for deployment without CUDA.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 231-231)

**Detail**:

Issue 5.1.5: Current environment assumes CUDA. Create environment-cpu.yml
with PyTorch CPU variant and document usage.

### JR-CAN-ARCH-010 — Defer true IPC architecture (Cascor-Canopy process separation) to future when triggering conditions are met.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 407-433)

**Detail**:

Current architecture embeds CasCor within Canopy process. Deferral justified by RemoteWorkerClient and async training providing sufficient capability. Revisit if hard cancellation, multiple concurrent jobs, or remote clusters needed.

**Notes**:

Phase 4 deferred; has explicit trigger conditions

### JR-CAN-DEP-005 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

### JR-CAN-ARCH-011 — Environment variable parsing must fix boolean/integer precedence bug.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 228-228)

**Detail**:

Issue 5.1.2: _convert_type checks boolean before integer, causing "0"
to parse as False instead of 0. Reorder checks: int/float before bool.

### JR-CAN-SEC-008 — Exception handling in callback_context must narrow exception types.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 244-244)

**Detail**:

Issue 5.3.3: Bare except: clause catches SystemExit/KeyboardInterrupt.
Narrow to (ValueError, AttributeError, ...); let system signals propagate.

### JR-CAN-OBS-009 — FATAL_LEVEL constant conflict must be resolved.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 238-238)

**Detail**:

Issue 5.2.4: FATAL_LEVEL defined in multiple modules with different values.
Consolidate to single definition in logging module.

### JR-CWK-ARCH-004 — Hardcoded values refactor implementation plan: Phase 1 create constants module, Phase 2 refactor source files, Phase 3 validate test suite and pre-commit, Phase 4 documentation update.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 1-80)

**Detail**:

Phase 1 (HIGH priority): Create constants.py (~30 constants in 7 sections), eliminate config duplication. Phase 2 (HIGH priority): Refactor worker.py (10 protocol strings), task_executor.py (12 training defaults/activation names), ws_connection.py (4 WebSocket strings), config.py (8 dataclass field defaults + 8 env var defaults), cli.py (4 argparse defaults). Phase 3 (HIGH priority): Run full pytest suite, run pre-commit hooks, verify protocol message type strings match cascor server. Phase 4 (MEDIUM priority): Update AGENTS.md, update CHANGELOG.md, create release description. Risk: protocol string mismatch with server (very low, mitigated by constants matching exact current strings + integration test); training defaults change behavior (very low, constants preserve exact values); config duplication elimination error (low, mitigated by unit test); import cycle (very low, constants.py has no imports from other worker modules).

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

### JR-CAN-ARCH-012 — Layout type sprint must forward positional/keyword parameters correctly.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 245-245)

**Detail**:

Issue 5.3.4: _layout_type_sprint helper loses parameters. Use *args, **kwargs
or explicit forwarding to preserve full signature.

### JR-CAN-UI-020 — Left sidebar too wide on Training Metrics tab—use per-tab width from ui_standards.

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Hardcoded dbc.Col(width=3) for all tabs. Move to per-tab config via 
ui_standards.py. Seeds UI_STANDARDS.md documentation.

**PRs**: PR-6 (cosmetic sidebar width), PR-6.5 (UI_STANDARDS doc + Training-Metrics narrowing experiment)

### JR-CAN-OBS-010 — Log timestamps must be timezone-aware (UTC).

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 236-236)

**Detail**:

Issue 5.2.2: Naive timestamps can cause ambiguity in distributed logs.
Use datetime.now(timezone.utc) or equivalent.

### JR-CAN-OBS-011 — Logger must capture real call site instead of logger.py:line-N.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 235-235)

**Detail**:

Issue 5.2.1: _log_with_context wrapper causes all logs to appear from
logger.py instead of actual call site. Use inspect.stack() to get caller.

### JR-CAS-TRAIN-015 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

### JR-ML-ARCH-401 — Phase 5:.

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

### JR-ML-ARCH-402 — Phase 6:.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 190-220)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

### JR-ML-TOOL-036 — Phase I (folded into Phase B): Asset cache busting for `websocket_client.js` + `ws_dash_bridge.js`.

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

### JR-CAN-LOCK-005 — Pre-commit hook suite must be auto-updated.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 253-253)

**Detail**:

Issue 5.4.3: pre-commit hooks may be outdated. Run `pre-commit autoupdate`
to refresh all hook versions and update .pre-commit-config.yaml.

### JR-DAT-TEST-010 — Pre-commit hooks should include pyupgrade for syntax modernization.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 72-73)

**Notes**:

L-01 LOW (P3).

### JR-DAT-TEST-011 — Pre-commit hooks should include shellcheck for shell script validation.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 73-74)

**Notes**:

L-02 LOW (P3).

### JR-CAS-PERF-002 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

### JR-CAS-LOCK-002 — Reconcile version across pyproject.toml, file headers, and API response metadata.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 820-824)

**Detail**:

Consider using single-source-of-truth version via importlib.metadata.version() instead of file header strings.

### JR-CAS-TOOL-002 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

### JR-CAN-ARCH-013 — Settings access must guard against KeyError or use default.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 242-242)

**Detail**:

Issue 5.3.1: config.key access can raise AttributeError. Use get() or
try/except to provide sensible defaults.

### JR-CAN-TEST-024 — Shellcheck severity level should align with ecosystem convention.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 252-252)

**Detail**:

Issue 5.4.2: Current shellcheck invocation uses non-standard severity flag.
Align to standard shellcheck options.

### JR-CAN-WS-001 — Training WebSocket must validate message size to prevent DoS.

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 243-243)

**Detail**:

Issue 5.3.2: WebSocket message handler does not check message size.
Add check: reject messages > 1MB with log and graceful disconnect.

### JR-DCL-DOC-010 — Update AGENTS.md Last Updated date and document utility scripts.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 160-164)

**Detail**:

Low-priority metadata and polish tasks: (1) Update header Last Updated from 2026-02-20 to current date,
(2) Document utility scripts (scripts/check_doc_links.py, scripts/generate_dep_docs.sh, util/run_all_tests.bash),
(3) Add environment variables section documenting JUNIPER_DATA_API_KEY, JUNIPER_DATA_URL, .env.example reference.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Tasks 4.1, 4.2, 4.3) and AGENTS_MD_UPDATE_PLAN (Steps 4.1, 4.2, 4.3).

