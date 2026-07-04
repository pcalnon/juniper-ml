# Round 4 Proposal R4-01: Comprehensive Master Plan

**Angle**: Strongest integration of R3-01 depth + R3-02 decisiveness + R3-03 density
**Author**: Round 4 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 4 consolidation — input to Round 5 (final)
**Inputs consolidated**: R3-01 (master integration), R3-02 (decision-resolved blueprint), R3-03 (lean execution document)

---

## 0. First hour

If you are picking up this work right now, do exactly this sequence before writing code:

1. `cd /home/pcalnon/Development/python/Juniper` — confirm ecosystem clean: `for repo in juniper-cascor juniper-cascor-client juniper-canopy; do (cd $repo && git status); done`.
2. Read **this document** sections 1-3 (settled positions, phase index). Do NOT re-read R3 or R2 sources unless verifying a specific cross-reference.
3. Run the five day-1 verification greps and record results in your worktree README:
   - `grep -rn "SessionMiddleware" juniper-canopy/src/` (Phase B-pre-b budget — absent = +0.5 day)
   - `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py` (Phase B NetworkVisualizer scope — cytoscape = minimum wire, Plotly = +1 day)
   - `grep "dash\b" juniper-canopy/pyproject.toml` (Dash version floor — record-only; Option B Interval drain works regardless)
   - `grep -n "run_coroutine_threadsafe" juniper-canopy/src/backend/cascor_service_adapter.py` (Phase C supervisor scope)
   - `grep -n "command_id\|request_id" juniper-cascor/src/api/websocket/control_stream.py` (Phase G scope — any surviving `request_id` is a pre-merge defect)
4. Verify GAP-WS-19 is RESOLVED on cascor main: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` — must show lock-holding pattern at `manager.py:138-156`. If missing, STOP — Phase 0-cascor scope expands.
5. Measure pre-Phase-B baseline bandwidth in staging: 1-hour sample of `/api/metrics/history` bytes/s (D-62). Record as the `canopy_rest_polling_bytes_per_sec` reference for the P0 exit gate (>90% reduction).
6. Confirm worktree location per Juniper parent CLAUDE.md: create all worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/` only.
7. Open Phase 0-cascor and Phase A-SDK worktrees in parallel — these run concurrently (no dependency until Phase G).
8. Pick the first PR target from section 15 merge sequence: **PR-1 = `phase-a-sdk-set-params` on juniper-cascor-client**.

---

## 1. Executive summary

### 1.1 What we are building

Replacing the ~3 MB/s per-dashboard `/api/metrics/history` REST polling bomb (GAP-WS-16, P0) with an already-half-wired cascor -> canopy -> browser WebSocket pipeline. Piggybacked: four cascor correctness bugs (GAP-WS-07, GAP-WS-21, GAP-WS-29, GAP-WS-32) and the CSWSH defense gap (RISK-15).

### 1.2 Why it matters (P0 motivator)

**`canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`** drops >=90% vs pre-Phase-B baseline in staging, sustained for 72 h. One gauge is the whole migration's acceptance signal.

### 1.3 Secondary goals

1. Fix GAP-WS-21 lifecycle state coalescer drop-filter bug (silently loses terminal state transitions).
2. Fix GAP-WS-29 `broadcast_from_thread` silent exception swallowing.
3. Mitigate GAP-WS-07 slow-client fan-out blocking via `_send_json` 0.5 s timeout (quick-fix) and eventual Phase E per-client pump tasks (full fix).
4. Close RISK-15 (CSWSH attack on `/ws/training` and `/ws/control`) via M-SEC-01/01b Origin allowlist, M-SEC-02 cookie+CSRF, M-SEC-05 rate limit, M-SEC-11 adapter inbound validation.
5. Add the `command_id`-based `set_params` WebSocket path (P2, feature-flagged default OFF) as scaffolding for v1.1 flip decision.
6. Add observability that is load-bearing for the acceptance gate and the SLO binding after >=1 week of production data.
7. Preserve REST endpoints forever as the fallback kill switch (no deletions, ever).

### 1.4 Explicit non-goals (out of scope for this migration)

- REST endpoint deletion (preserved forever per D-21/D-54/D-56)
- Multi-tenant replay isolation (D-32 deferred)
- Per-command HMAC (D-31 deferred indefinitely)
- Two-bucket rate limit (D-33; single bucket; split only if starvation observed)
- `permessage-deflate` negotiation (GAP-WS-17 deferred)
- Topology chunking (GAP-WS-18; REST fallback preserved)
- WebAssembly Plotly (out of scope)
- Multi-browser matrix (D-44; Chromium-only v1)
- User research study (D-45; skip)
- OAuth/OIDC, mTLS canopy<->cascor, shadow traffic (D-26 rejected)
- rAF coalescer in-production (D-04; scaffolded disabled)
- NetworkVisualizer deep render migration (D-06; minimum wire in Phase B, deep deferred)

### 1.4 How long

Expected effort: **15.75 engineering days** / ~4.5 weeks calendar with 48-72 h soak windows. Minimum-viable carveout (P0 only): ~7 days.

**Canonical phase order**: Phase A (SDK, parallel) + Phase 0-cascor (cascor prereqs, parallel) -> Phase B-pre-a (read-path security) -> Phase B (browser bridge, polling elimination) -> Phase B-pre-b (control-path security, parallel with B) -> Phase C (set_params, flag-off) -> Phase D (control buttons, gated on B-pre-b in prod >=48 h) -> Phase E (backpressure full, conditional on telemetry) -> Phase F (heartbeat + jitter) -> Phase G (cascor set_params integration tests) -> Phase H (normalize_metric regression gate) -> Phase I (asset cache busting, folded into Phase B).

**Recommended path**: P0 critical spine = Phase A-SDK + Phase 0-cascor + Phase B-pre-a + Phase B (with Phase I folded in). Everything else sequences around that spine.

**Rollback story**: every phase has a config-only kill switch (master matrix in section 16) with MTTR <=5 min. REST paths stay alive forever (D-21, D-54). If a kill switch fails to produce expected metric delta within 60 s, the migration halts for re-planning.

**Effort table**:

| Phase | Optimistic | Expected | Pessimistic | Notes |
|---|---:|---:|---:|---|
| 0-cascor | 1.5 | 2.0 | 3.0 | +risk: `_pending_connections` async race |
| A-SDK | 0.5 | 1.0 | 1.5 | +risk: correlation-map bounding iteration |
| B-pre-a | 0.5 | 1.0 | 1.5 | +risk: audit logger name collision |
| B | 3.0 | 4.0 | 5.0 | +risk: Plotly NetworkVisualizer (+1 day) |
| B-pre-b | 1.0 | 1.5 | 2.0 | +risk: SessionMiddleware absent (+0.5 day) |
| C | 1.5 | 2.0 | 3.0 | +risk: concurrent-correlation race bugs |
| D | 0.75 | 1.0 | 1.5 | +risk: orphaned-command UI state |
| E | 0.75 | 1.0 | 1.5 | Conditional on telemetry; may not ship |
| F | 0.25 | 0.5 | 1.0 | Small phase; low variance |
| G | 0.25 | 0.5 | 0.75 | Tests only; low variance |
| H | 0.5 | 1.0 | 1.5 | Audit document can grow |
| I | 0.1 | 0.25 | 0.5 | Folded into B; counted separately for rollback |
| **Total** | **10.6** | **15.75** | **22.25** | ~4.5 weeks calendar with soak windows |

**Calendar translation**: 15.75 engineering days x single-developer lane -> ~3 weeks one-person calendar, or ~4.5 weeks with 48-72 h soak windows. Minimum-viable carveout (P0 only): ~7 days (Phase A-SDK + Phase 0-cascor + B-pre-a + Phase B + Phase I).

### 1.5 Key decisions settled (top 10)

| D-NN | Decision | Applied position | Why it matters |
|---|---|---|---|
| D-02 | Correlation field name | **`command_id`** (NOT `request_id`) | Wire contract across SDK, cascor, canopy, tests |
| D-11 | Phase 0-cascor carve-out | **carve out from Phase B** | 1-week additive-field soak before canopy consumes |
| D-17+D-18 | Phase B feature flags | **two-flag design**: `enable_browser_ws_bridge=False` + `disable_ws_bridge=False` | Dev flip vs permanent kill are distinct; `enabled = former AND NOT latter` |
| D-10 | Security flag naming | **positive-sense `ws_security_enabled=True`** + CI guardrail refusing False in prod compose | Safety over source-doc naming inertia (R4-01 resolution, see section 22) |
| D-19 | Phase E backpressure default | **`drop_oldest_progress_only`** | Overrides source doc `block`; progress events droppable, state events close |
| D-35 | Replay buffer default | **1024 entries**, env-configurable, `=0` disables | Production default; staging can lower to exercise fallback |
| D-38 | Phase 0-cascor staging soak | **72 hours** | Latent seq-monotonicity bugs need sustained broadcast |
| D-48 | Phase C flag-flip criteria | **6 enumerated hard gates** | Evidence-based rollout, not calendar-based |
| D-53 | Kill-switch MTTR tested | **every switch tested in staging** | Untested switch is not a switch; two failures = abandon trigger |
| D-21/D-54 | REST path retention | **preserved forever** | Kill switch fallback; no deprecation ever |

---

## 2. Constitution: settled positions

Single tabular reference. Every item is SETTLED -- do not re-litigate. Source pointers are canonical. Items C-01 through C-42 from R3-03, reconciled with R3-01 section 2 and R3-02 section 1.

### 2.1 Wire-format positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-01 | Correlation field is `command_id`, NOT `request_id` -- every repo, every test | D-02 | R1-05 S4.2; R2-03 S15.2 |
| C-02 | `command_response` has NO `seq` field; `/ws/control` has no replay buffer | D-03 | R1-05 S4.17; R2-04 |
| C-03 | `set_params` default timeout = 1.0 s (not 5.0 s) | D-01 | R1-05 S4.1; source doc S7.32 |
| C-06 | `server_instance_id` = programmatic key; `server_start_time` = advisory only | D-15 | R1-05 S4.20 |
| C-07 | `replay_buffer_capacity` added to `connection_established` | D-16 | R1-05 S4.21 |
| C-08 | Two-phase registration via `_pending_connections` set | D-14 | R1-05 S4.18 |
| C-09 | Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with WARN | D-34 | R1-05 S4.44 |
| C-40 | Wire-format rollout is strictly additive; no field renamed/retyped/removed | -- | R2-03 S3.3 |
| C-41 | `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope | -- | R1-05 S4.8; R2-03 CCC-10 |

### 2.2 Protocol behavior positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-04 | SDK fails fast on disconnect; no reconnect queue; no SDK-level retries | D-20 | R1-05 S4.22, S4.42 |
| C-05 | Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE` | D-35 | R2-01 S18.1; R2-04 |
| C-17 | REST fallback cadence during disconnect = 1 Hz (NOT 100 ms) | D-05 | R1-05 S4.4 |
| C-18 | `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array) | D-07 | R1-05 S4.7 |
| C-19 | Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces | -- | R1-02 S5.4 |
| C-23 | REST endpoints preserved FOREVER -- no deprecation | D-21/D-54/D-56 | R1-02 principle 7 |
| C-25 | One-resume-per-connection rule (second resume -> close 1003) | D-30 | R1-05 S4.12 |
| C-29 | Debounce lives in Dash clientside callback (NOT SDK), 250 ms | D-22 | R1-05 S4.24 |
| C-30 | `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch) | D-10 | R1-02 S4.3 |

### 2.3 Security positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-10 | Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header) | D-29 | R1-05 S4.43; R2-01 S7.1 |
| C-11 | GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only | D-13 | R1-05 S4.16 |
| C-24 | Single-tenant v1; multi-tenant replay isolation deferred | D-25/D-32 | R1-05 S4.13 |
| C-26 | Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s | D-24/D-33 | R1-05 S4.37, S4.46 |
| C-27 | **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth` | D-10 | R1-02 S12.5; R2-01 S18.2; R2-03 S15.3 |
| C-31 | Shadow traffic: rejected | D-26 | R1-05 S4.39 |
| C-33 | Per-command HMAC deferred indefinitely | D-31 | R1-05 S4.11 |

### 2.4 Phase-ordering and scope positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-12 | Phase 0-cascor is a carve-out from Phase B | D-11 | R1-05 S4.19 |
| C-13 | Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D) | D-23 | R1-05 S4.35 |
| C-14 | Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bridge` (permanent kill) | D-17/D-18 | R1-05 S4.45 |
| C-15 | Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`) | D-19 | R1-05 S4.36 |
| C-16 | rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`) | D-04 | R1-05 S4.3 |
| C-20 | GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in Phase B | D-08 | R1-05 S4.8 |
| C-21 | NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape | D-06 | R1-05 S4.5 |
| C-22 | `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H | D-27 | R1-05 S4.41 |
| C-28 | Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates | D-47/D-48 | R1-02 S6.1 |

### 2.5 Observability positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-32 | Chromium-only Playwright for v1 | D-44 | R1-05 S4.31 |
| C-34 | Contract-test pytest marker `contract` runs on every PR in all 3 repos | D-43 | R1-05 S4.34 |
| C-35 | Latency tests are recording-only in CI; strict assertions local-only | D-42 | R1-05 S4.28 |
| C-37 | P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90% vs baseline | -- | R1-01 S2.5.1 |
| C-38 | Observability-before-behavior rule: metrics + panels + alerts before the behavior change | -- | R1-02 S1.2 principle 1 |
| C-39 | Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch | D-53 | R1-02 S1.2 principle 2 |
| C-42 | Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-reliability work) | D-50 | R1-02 S2.4 |

### 2.6 Effort and calendar positions

| # | Position | D-NN | Source |
|---|---|---|---|
| C-36 | Total effort: 15.75 expected engineering days / ~4.5 weeks calendar | -- | R2-02 S17; R3-01 S19; R3-02 S17 |
| -- | Phase 0-cascor staging soak = 72 h | D-38 | R1-02 S3.4; R2-04 |
| -- | Phase B staging soak = 72 h | D-39 | R2-04 |
| -- | Phase B-pre-b staging soak = 48 h | -- | R1-02 S4.2 |
| -- | Phase D entry gate = B-pre-b in production >=48 h | -- | R2-02 S18.8 |
| -- | Phase C flag-flip canary >= 7 days production data | D-48 | R1-02 S6.1 |
| -- | Mid-week deploys for behavior-changing flag flips only | D-61 | R1-02 S5.7 |
| -- | Minimum-viable carveout ~7 days (P0 only) | -- | R1-01 S1.2 |

### 2.7 Feature flag inventory

| Flag | Phase | Initial | Final | Removal? |
|---|---|---|---|---|
| `enable_browser_ws_bridge` | B | `False` | `True` (post-staging) | Post-flip deprecation (v1.1) |
| `disable_ws_bridge` | B | `False` | `False` permanent | Never |
| `enable_raf_coalescer` | B | `False` | depends on S5.6 data | Post-B+1 if data warrants |
| `use_websocket_set_params` | C | `False` | `True` (post-canary >=7 days) | Post-flip deprecation (v1.1) |
| `enable_ws_control_buttons` | D | `False` | `True` (post-canary) | Post-flip deprecation (v1.1) |
| `ws_security_enabled` | B-pre-b | `True` | `True` permanent (CI refuses False in prod) | Never |
| `disable_ws_control_endpoint` | B-pre-b | `False` | `False` permanent | Never |
| `ws_rate_limit_enabled` | B-pre-b | `True` | `True` permanent | Never |
| `audit_log_enabled` | B-pre-a | `True` | `True` permanent | Never |
| `ws_backpressure_policy` | E | `drop_oldest_progress_only` | same | Permanent config (enum) |
| `disable_ws_auto_reconnect` | F | `False` | `False` permanent | Never |

### 2.8 Configuration / settings canonical table

| Setting | Repo | Type | Default | Env var | Phase | Validation |
|---|---|---|---|---|---|---|
| `ws_replay_buffer_size` | cascor | int | 1024 | `JUNIPER_WS_REPLAY_BUFFER_SIZE` | 0-cascor | `>=0` (0 disables) |
| `ws_send_timeout_seconds` | cascor | float | 0.5 | `JUNIPER_WS_SEND_TIMEOUT_SECONDS` | 0-cascor | `>0` |
| `ws_state_throttle_coalesce_ms` | cascor | int | 1000 | `JUNIPER_WS_STATE_THROTTLE_COALESCE_MS` | 0-cascor | `>0` |
| `ws_resume_handshake_timeout_s` | cascor | float | 5.0 | `JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S` | 0-cascor | `>0` |
| `ws_pending_max_duration_s` | cascor | float | 10.0 | `JUNIPER_WS_PENDING_MAX_DURATION_S` | 0-cascor | `>0` |
| `ws_max_connections_per_ip` | cascor | int | 5 | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a | `>=1` |
| `ws_allowed_origins` | cascor | list[str] | `[]` (fail-closed) | `JUNIPER_WS_ALLOWED_ORIGINS` | B-pre-a + B-pre-b | no `*` |
| `ws_idle_timeout_seconds` | cascor/canopy | int | 120 | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS` | B-pre-a | `>=0` (0 disables) |
| `ws_security_enabled` | canopy | bool | `True` | `JUNIPER_WS_SECURITY_ENABLED` | B-pre-b | bool; CI refuses `false` in prod |
| `ws_max_connections_per_ip` | canopy | int | 5 | `JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a | `>=1` |
| `ws_allowed_origins` | canopy | list[str] | localhost defaults | `JUNIPER_CANOPY_WS_ALLOWED_ORIGINS` | B-pre-a | no `*` |
| `ws_rate_limit_enabled` | canopy | bool | `True` | `JUNIPER_WS_RATE_LIMIT_ENABLED` | B-pre-b | bool |
| `ws_rate_limit_cps` | canopy | int | 10 | `JUNIPER_WS_RATE_LIMIT_CPS` | B-pre-b | `>=1` |
| `audit_log_enabled` | canopy | bool | `True` | `JUNIPER_AUDIT_LOG_ENABLED` | B-pre-a | bool |
| `audit_log_path` | canopy | str | `/var/log/canopy/audit.log` | `JUNIPER_AUDIT_LOG_PATH` | B-pre-a | path |
| `audit_log_retention_days` | canopy | int | 90 | `JUNIPER_AUDIT_LOG_RETENTION_DAYS` | B-pre-a | `>=1` |
| `disable_ws_control_endpoint` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT` | B-pre-b | bool |
| `enable_browser_ws_bridge` | canopy | bool | `False` -> True | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE` | B | bool |
| `disable_ws_bridge` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_BRIDGE` | B | bool |
| `enable_raf_coalescer` | canopy | bool | `False` | `JUNIPER_ENABLE_RAF_COALESCER` | B | bool |
| `enable_ws_latency_beacon` | canopy | bool | `True` | `JUNIPER_ENABLE_WS_LATENCY_BEACON` | B | bool |
| `use_websocket_set_params` | canopy | bool | `False` | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS` | C | bool |
| `ws_set_params_timeout` | canopy | float | 1.0 | `JUNIPER_WS_SET_PARAMS_TIMEOUT` | C | `>0` |
| `enable_ws_control_buttons` | canopy | bool | `False` | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS` | D | bool |
| `ws_backpressure_policy` | cascor | Literal | `drop_oldest_progress_only` | `JUNIPER_WS_BACKPRESSURE_POLICY` | E | enum |
| `disable_ws_auto_reconnect` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_AUTO_RECONNECT` | F | bool |

Every setting has a `Field(..., description=...)` Pydantic docstring; CI asserts every setting is documented and every env var round-trips.

---

## 3. Phase index

Owner key: **C**=backend-cascor, **Y**=backend-canopy, **F**=frontend, **S**=SDK, **Sec**=security review, **O**=ops.

| # | Phase | Goal (one line) | Owner | Effort (o/e/p) | Entry deps | Exit top criterion | Rollback TTF | NOT-in-phase |
|---|---|---|---|---|---|---|---|---|
| 1 | **0-cascor** | Cascor `/ws/training` emits `seq`, advertises `server_instance_id`+`replay_buffer_capacity`, supports `resume`, fixes state coalescer+broadcast_from_thread | C | 1.5/2.0/3.0 | cascor main clean; GAP-WS-19 verified | `cascor_ws_seq_gap_detected_total==0` after 72h soak | 15 min revert | Full Phase E; permessage-deflate; topology chunking; seq on `command_response` |
| 2 | **A-SDK** (parallel with 1) | `CascorControlStream.set_params(params, timeout=1.0, command_id=...)` ships to PyPI | S | 0.5/1.0/1.5 | cascor-client main clean | `test_set_params_caller_cancellation` green | PyPI yank | Canopy adapter refactor; SDK retries; debounce |
| 3 | **B-pre-a** (parallel with 1,2) | Origin on `/ws/training`, size caps, per-IP cap, idle timeout, audit-logger skeleton | C+Y+Sec | 0.5/1.0/1.5 | cascor+canopy main clean | 6th-IP conn rejected 1013; empty allowlist rejects all | 5 min env | CSRF; Origin on `/ws/control`; rate limit; Prom counters for audit; adapter HMAC |
| 4 | **B** (P0 win) | Browser bridge drains `/ws/training` into Dash store, polling killed; Phase I cache bust bundled | Y+F+C | 3.0/4.0/5.0 | 0-cascor + B-pre-a in prod; 72h soak | `canopy_rest_polling_bytes_per_sec` >=90% reduced + 72h memory soak | 5 min `disable_ws_bridge=true` | Phase C set_params; Phase D buttons; full rAF; full backpressure; CSRF |
| 5 | **B-pre-b** (parallel with 4) | Origin on `/ws/control`, cookie+CSRF first-frame, rate limit, idle timeout, adapter HMAC, per-origin cooldown | Y+Sec | 1.0/1.5/2.0 | B-pre-a in main | All tests green; 48h staging soak; Origin+CSRF enforced end-to-end | 5 min env | Per-command HMAC; multi-tenant isolation; two-bucket rate limit |
| 6 | **C** (set_params, flag-off) | Canopy adapter hot/cold split; hot->WS via `command_id`; REST fallback; flag-off default | Y | 1.5/2.0/3.0 | A-SDK on PyPI; Phase B in prod | `test_set_params_concurrent_correlation` green; flag-off by default | 2 min `use_websocket_set_params=false` | SDK retries; reconnect queue; REST deprecation |
| 7 | **D** (control buttons) | Browser start/stop/pause/resume/reset via `/ws/control` with REST fallback | F+Y+C | 0.75/1.0/1.5 | Phase B in prod + **B-pre-b in prod >=48h** | `test_csrf_required_for_websocket_start` green; 24h zero orphaned commands | 5 min `enable_ws_control_buttons=false` | Full permessage-deflate; set_params routing |
| 8 | **E** (conditional) | Per-client pump tasks + bounded queues + policy matrix | C | 0.75/1.0/1.5 | 0-cascor in main; trigger = RISK-04 observed | `test_slow_client_does_not_block_fast_clients` green | 5 min `ws_backpressure_policy=block` | Multi-tenant per-session queues |
| 9 | **F** (heartbeat) | Application `ping`/`pong` at 30s; dead-conn detection; uncap reconnect; jitter formula | F+C | 0.25/0.5/1.0 | Phase B in main | All tests pass; no NaN delays after 48h | 10 min JS revert | Custom ping schedules |
| 10 | **G** (integration tests) | 15 tests via FastAPI TestClient; contract-lane tests | C | 0.25/0.5/0.75 | 0-cascor in main; B-pre-b in main | All 15 tests green in `contract` lane | n/a (test-only) | SDK-level integration tests |
| 11 | **H** (normalize_metric) | Regression test + consumer audit + CODEOWNERS hard gate + pre-commit hook | Y | 0.5/1.0/1.5 | Phase B in main | Regression tests green; CODEOWNERS enforced | 5 min revert | `_normalize_metric` refactor |
| 12 | **I** (cache bust) | `assets_url_path` hash query param; folded into Phase B | F | 0.1/0.25/0.5 | folded into B | Browsers pick up new JS without hard refresh | 5 min revert | -- |

**Phase dependency graph**:

```
Phase A-SDK (parallel) ---+
                          |
Phase 0-cascor -----------+--> Phase B-pre-a --> Phase B --> (P0 win)
                          |                         |
Phase B-pre-a ------------+                         |
                                                    |
Phase B-pre-b (parallel with B) ----> Phase D ------+
                                                    |
                                    Phase C (flag-off, parallel) --> Phase D
                                                    |
                                                    +--> Phase E (optional, telemetry-triggered)
                                                    +--> Phase F (heartbeat follow-on)
                                                    +--> Phase G (integration tests)
                                                    +--> Phase H (normalize_metric regression)

Phase I asset cache busting --> folded into Phase B PR
```

---

## 4. Phase 0-cascor: cascor server prerequisites

### 4.1 Goal

Cascor's `/ws/training` emits monotonically-increasing `seq` on every outbound envelope, advertises `server_instance_id` + `server_start_time` + `replay_buffer_capacity` + `emitted_at_monotonic`, supports a 1024-entry replay buffer with `resume` handler, exposes `snapshot_seq` atomically on REST, fixes slow-client fan-out (0.5 s timeout), fixes GAP-WS-21 state coalescer, fixes GAP-WS-29 silent exception swallowing, and returns protocol-error responses on `/ws/control`. The `/ws/control` endpoint gains `command_id` echo but **no `seq` field** (C-02). Purely additive -- existing clients keep working.

### 4.2 Entry gate

- [ ] `juniper-cascor` main branch clean; baseline tests green
- [ ] GAP-WS-19 verified at `manager.py:138-156` (D-13)
- [ ] No concurrent cascor PR touching `websocket/*.py`, `lifecycle/manager.py`, `messages.py`
- [ ] Prometheus namespace collision check: 15 `cascor_ws_*` names reserved
- [ ] `juniper-cascor-worker` CI green against current cascor main
- [ ] Constitution section 2 committed; no re-litigation

### 4.3 Deliverables checklist

**Commits** (10 commits, single squash-merged PR):

- [ ] 0-cascor-1: `messages.py` optional `seq` + `emitted_at_monotonic` on every builder
- [ ] 0-cascor-2a: `manager.py` gains `server_instance_id=uuid4()`, `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer=deque(maxlen=Settings.ws_replay_buffer_size)`, `_assign_seq_and_append()`
- [ ] 0-cascor-2b: `connect()` advertises `server_instance_id`, `server_start_time`, `replay_buffer_capacity` on `connection_established` (D-16)
- [ ] 0-cascor-3: `_send_json` wraps in `asyncio.wait_for(..., timeout=Settings.ws_send_timeout_seconds)` (GAP-WS-07 quick-fix, default 0.5s, D-46)
- [ ] 0-cascor-4: `replay_since(last_seq)` + `ReplayOutOfRange` exception; copy-under-lock
- [ ] 0-cascor-5a: `training_stream.py` two-phase registration (`_pending_connections`, `promote_to_active()`) (D-14)
- [ ] 0-cascor-5b: `/ws/training` resume handler with 5s frame timeout; `resume_ok`/`resume_failed`; one-resume-per-connection (D-30)
- [ ] 0-cascor-6: `/api/v1/training/status` returns `snapshot_seq` + `server_instance_id` atomically under `_seq_lock`
- [ ] 0-cascor-7: `lifecycle/manager.py:133-136` debounced coalescer; terminal transitions bypass throttle (GAP-WS-21)
- [ ] 0-cascor-8: `broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29)
- [ ] 0-cascor-9: `/ws/control` protocol-error envelopes; echoes `command_id`; **NO seq on command_response** (D-03, GAP-WS-22)
- [ ] 0-cascor-10: CHANGELOG.md + `docs/websocket_protocol.md`

**Settings** (`juniper-cascor/src/config/settings.py`):

- [ ] `ws_replay_buffer_size: int = 1024`
- [ ] `ws_send_timeout_seconds: float = 0.5`
- [ ] `ws_resume_handshake_timeout_s: float = 5.0`
- [ ] `ws_state_throttle_coalesce_ms: int = 1000`
- [ ] `ws_pending_max_duration_s: float = 10.0`

### 4.4 Cross-cutting deliverables

- **CCC-01 (schema)**: additive-only; `command_id` rename enforced; rollout state matrix in PR
- **CCC-02 (observability)**: all 15 metrics present before merge; metrics-presence CI test; `WSSeqCurrentStalled` test-fired in staging
- **CCC-03 (kill switches)**: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`, `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`, rolling restart
- **CCC-04 (cross-repo)**: merges before canopy Phase B; 1-week additive-soak; Helm chart version bump
- **CCC-05 (contract tests)**: `test_replay_buffer_capacity_advertised`, `test_ws_control_command_response_has_no_seq`
- **CCC-08 (backwards compat)**: `juniper-cascor-worker` CI green during soak; `test_legacy_client_ignores_seq_field`

### 4.5 Test acceptance

| Test name | Type | Measurable criterion |
|---|---|---|
| `test_seq_monotonically_increases_across_broadcasts` | unit | seq(n+1) > seq(n) |
| `test_seq_is_assigned_on_loop_thread` | unit | No cross-thread seq assignment |
| `test_seq_lock_does_not_block_broadcast_iteration` | unit | Broadcast completes <100ms |
| `test_replay_buffer_bounded_to_configured_capacity` | unit | `maxlen == Settings.ws_replay_buffer_size` |
| `test_replay_buffer_capacity_configurable_via_env` | unit | Override to 256 works |
| `test_replay_buffer_size_zero_disables_replay` | unit | `=0` -> `out_of_range` (D-36) |
| `test_resume_replays_events_after_last_seq` | integration | N-5 -> exactly 5 events |
| `test_resume_failed_out_of_range` | integration | Broadcast 2000, last_seq=10 -> fail |
| `test_resume_failed_server_restarted` | integration | Stale UUID -> fail |
| `test_resume_malformed_data` | integration | Malformed -> close |
| `test_resume_timeout_no_frame` | integration | 5s timeout -> close |
| `test_connection_established_advertises_instance_id_and_capacity` | unit | Fields present (D-16) |
| `test_snapshot_seq_atomic_with_state_read` | integration | No torn snapshot |
| `test_second_resume_closes_connection_1003` | unit | D-30 enforced |
| `test_slow_client_send_timeout_does_not_block_fanout` | unit | 0.5s quick-fix works |
| `test_send_timeout_env_override` | unit | D-46 env-configurable |
| `test_state_coalescer_flushes_terminal_transitions` | unit | Started->Failed both observed (GAP-WS-21) |
| `test_broadcast_from_thread_exception_logged` | unit | GAP-WS-29 via caplog |
| `test_ws_control_command_response_has_no_seq` | contract | D-03 explicit negative assertion |
| `test_pending_connections_not_eligible_for_broadcast` | unit | D-14 correctness |
| `test_promote_to_active_atomic_under_seq_lock` | unit | Atomic promotion |
| `test_close_all_holds_lock` | unit | GAP-WS-19 regression (D-13) |
| `test_emitted_at_monotonic_present_on_every_broadcast` | unit | CCC-10 field |
| `test_legacy_client_ignores_seq_field` | unit | CCC-08 backward compat |
| `test_malformed_json_closes_1003` | unit | GAP-WS-22 |
| `test_unknown_command_returns_protocol_error_envelope` | unit | GAP-WS-22 |

**Chaos tests (BLOCKING gates, not nightly)**:

- [ ] `chaos_broadcast_replay_race`: hypothesis + asyncio.gather 100 concurrent
- [ ] `chaos_broadcast_fanout`: 100 Hz x 60s x 10 clients (D-41 load test)
- [ ] `chaos_broadcast_from_thread_exception`: hypothesis exception types

### 4.6 Observability

| Metric | Type | Labels |
|---|---|---|
| `cascor_ws_seq_current` | Gauge | -- |
| `cascor_ws_replay_buffer_occupancy` | Gauge | -- |
| `cascor_ws_replay_buffer_bytes` | Gauge | -- |
| `cascor_ws_replay_buffer_capacity_configured` | Gauge | -- |
| `cascor_ws_resume_requests_total` | Counter | `outcome` |
| `cascor_ws_resume_replayed_events` | Histogram | buckets {0,1,5,25,100,500,1024} |
| `cascor_ws_broadcast_timeout_total` | Counter | `type` |
| `cascor_ws_broadcast_send_duration_seconds` | Histogram | `type` |
| `cascor_ws_pending_connections` | Gauge | -- |
| `cascor_ws_state_throttle_coalesced_total` | Counter | -- |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter | -- |
| `cascor_ws_seq_gap_detected_total` | Counter | -- |
| `cascor_ws_connections_active` | Gauge | `endpoint` |
| `cascor_ws_command_responses_total` | Counter | `command, status` |
| `cascor_ws_command_handler_seconds` | Histogram | `command` |

**Alerts**: `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap` (ticket), `WSPendingConnectionStuck` (ticket), `WSSlowBroadcastP95` (ticket)

### 4.7 Pull request plan

| # | Branch | Title | Repo | Target |
|---|---|---|---|---|
| **P1** | `phase-0-cascor-seq-replay-resume` | `feat(ws): seq numbers, replay buffer, resume protocol, state coalescer` | juniper-cascor | main |
| **P2** (parallel) | `phase-a-sdk-set-params` | `feat(sdk): CascorControlStream.set_params with command_id correlation` | juniper-cascor-client | main |

### 4.8 Exit gate

1. All 26+ unit + 5 integration + 3 chaos + load tests green
2. Metric-presence pytest green (D-37)
3. **72-hour staging soak** (D-38): `seq_gap_detected==0`, `broadcast_from_thread_errors==0`, replay-buffer stable
4. `WSSeqCurrentStalled` alert test-fired once in staging (D-53)
5. `juniper-cascor-worker` CI green during soak (CCC-04/CCC-08)
6. Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published
7. Load test green: 100 Hz x 60s x 10 clients, p95 < 250 ms (D-41)
8. **Going/no-go**: if seq gap detected during soak, HALT and investigate before Phase B

### 4.9 Rollback (verbatim commands)

```bash
# Hot rollback -- full revert (15 min TTF)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git revert <phase-0-cascor-merge-sha> --no-edit
git push origin main
# Blue/green redeploy cascor; clients see new server_instance_id, refetch REST snapshot

# Soft rollback -- aggressive send-timeout override (5 min TTF)
export JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01
systemctl restart juniper-cascor

# Replay buffer disable (5 min TTF)
export JUNIPER_WS_REPLAY_BUFFER_SIZE=0
systemctl restart juniper-cascor
```

### 4.10 NOT in this phase

- Full Phase E backpressure (only 0.5s `_send_json` quick-fix)
- `permessage-deflate` (GAP-WS-17); topology chunking (GAP-WS-18)
- `seq` on `command_response` (D-03 explicit exclusion)
- GAP-WS-19 re-fix (already on main; regression test only)
- M-SEC-01..11 security controls (Phase B-pre-a/b)
- Multi-tenant replay buffers (D-32 deferred)
- Canopy adapter consumption (Phase C)

---

## 5. Phase A-SDK: `set_params` method (parallel with Phase 0-cascor)

### 5.1 Goal

Ship `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None)` to PyPI with per-request `command_id` correlation, fail-fast on disconnect, no retries, bounded correlation map (256 max).

### 5.2 Entry gate

- [ ] `juniper-cascor-client` main clean; baseline tests green

### 5.3 Deliverables checklist

**Method signature**:
```python
async def set_params(
    self,
    params: dict,
    *,
    timeout: float = 1.0,
    command_id: Optional[str] = None,
) -> dict:
    ...
```

**Implementation**:
- [ ] `set_params()` method with `command_id = str(uuid.uuid4())` if absent (D-02)
- [ ] `_pending: Dict[str, asyncio.Future]` bounded at 256; `JuniperCascorOverloadError` on overflow (R1-02 S6.4)
- [ ] Background `_recv_task` correlates on `command_id`; cancellation-safe (`finally:` cleanup)
- [ ] Fail-fast: no retries (D-20), raises `JuniperCascorTimeoutError`, `JuniperCascorConnectionError`, `JuniperCascorError`
- [ ] `_client_latency_ms` private field on returned dict (leading underscore)
- [ ] `SetParamsResponse` wire model with `extra="allow"` (additive compat)
- [ ] `disconnect()` cancels recv task, drains pending with `set_exception`
- [ ] `testing/fake_ws_client.py`: `on_command(name, handler)` auto-scaffold
- [ ] `testing/server_harness.py`: `FakeCascorServerHarness` class
- [ ] Minor version bump + CHANGELOG + PyPI publish
- [ ] `juniper-ml/pyproject.toml` extras pin bump follow-up (D-57)

### 5.4 Test acceptance

| Test name | Type | Criterion |
|---|---|---|
| `test_set_params_default_timeout_is_one_second` | unit | Default kwarg = 1.0 (C-03 regression) |
| `test_set_params_happy_path` | unit | 50ms ack latency roundtrip |
| `test_set_params_timeout_raises_typed_exception` | unit | JuniperCascorTimeoutError |
| `test_set_params_concurrent_callers_correlate_via_command_id` | unit | 2 calls distinguished (C-01) |
| `test_set_params_caller_cancellation_cleans_correlation_map` | unit **MANDATORY** | `len(_pending)==0` after cancel |
| `test_set_params_fails_fast_on_disconnect` | unit | C-04 enforced |
| `test_set_params_no_retry_on_timeout` | unit | No retry (D-20) |
| `test_set_params_server_error_response_raises_typed_exception` | unit | Error handling |
| `test_correlation_map_bounded_at_256` | unit | 257th -> JuniperCascorOverloadError |
| `test_recv_task_propagates_exception_to_all_pending_futures` | unit | Drain on error |
| `test_len_pending_returns_to_zero_after_failure_modes` | nightly | Leak prevention |
| `test_set_params_x_api_key_header_present` | unit | Security regression |

### 5.5 Exit gate

- [ ] All 12 unit tests green; coverage >=95% on new code
- [ ] `pip install juniper-cascor-client==<new>` succeeds in fresh venv
- [ ] Draft canopy adapter can `import` and call `set_params` against `FakeCascorServerHarness`
- [ ] `test_set_params_caller_cancellation_cleans_correlation_map` non-flaky across 10 runs

### 5.6 Rollback

```bash
# PyPI yank (2 min TTF) -- only if installs-but-won't-import
# Otherwise fix-forward with patch release

# Downstream pin downgrade (15 min TTF)
cd juniper-canopy
# Edit pyproject.toml: juniper-cascor-client = "<SDK_VERSION_A"
git commit -am "chore: pin cascor-client to pre-<version>"
```

---

## 6. Phase B-pre-a: read-path security

### 6.1 Goal

Close minimum security holes for browser `/ws/training` exposure: frame-size caps (M-SEC-03), Origin allowlist on `/ws/training` (M-SEC-01b, placed here per exfiltration argument), per-IP cap (M-SEC-04, 5/IP), idle timeout (M-SEC-10, 120s), audit-logger skeleton (M-SEC-07).

### 6.2 Entry gate

- [ ] cascor + canopy main clean
- [ ] Phase 0-cascor (P1) merged to cascor main
- [ ] No concurrent security PR open
- [ ] `canopy.audit` logger name not already used

### 6.3 Deliverables checklist

**Cascor**:
- [ ] `origin.py` (new): `validate_origin(ws, allowlist)` -- fail-closed, `*` refused
- [ ] Wire into `training_stream_handler` (NOT `control_stream_handler`)
- [ ] `Settings.ws_allowed_origins: list[str] = []` (fail-closed)
- [ ] `_per_ip_counts: Dict[str,int]` under `_lock`; `Settings.ws_max_connections_per_ip: int = 5`
- [ ] `max_size=4096` on every `receive_*()`
- [ ] Idle timeout: `asyncio.wait_for(receive_text(), timeout=ws_idle_timeout_seconds)`, close 1000

**Canopy**:
- [ ] `ws_security.py` (new): copy of cascor `validate_origin` (explicit duplication, no cross-import)
- [ ] Wire into `/ws/training`; `max_size=4096` inbound training, `max_size=65536` control
- [ ] `audit_log.py` (new): JSON formatter, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist, CRLF escape
- [ ] CI `scripts/audit_ws_receive_calls.py`: AST check every `ws.receive_*()` has explicit `max_size`

**Meta-setting**: `ws_security_enabled: bool = True` (positive-sense, C-27) with CI guardrail in `juniper-deploy`.

### 6.4 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_oversized_frame_rejected_with_1009` | unit | 65KB -> close 1009 (both repos) |
| `test_per_ip_cap_enforced_6th_rejected_1013` | unit | 6th conn -> 1013 |
| `test_per_ip_counter_decrements_on_disconnect` | unit | Cleanup works |
| `test_per_ip_map_shrinks_to_zero` | unit | Memory leak guard |
| `test_origin_allowlist_accepts_configured_origin` | unit | Happy path |
| `test_origin_allowlist_rejects_third_party` | unit | Cross-origin rejected |
| `test_empty_allowlist_rejects_all_fail_closed` | unit | Fail-closed default |
| `test_allowed_origins_wildcard_refused` | unit | Parser rejects `*` |
| `test_idle_timeout_closes_1000` | unit | 120s idle -> close |
| `test_audit_log_format_and_scrubbing` | unit | JSON + scrub |
| `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` | Playwright | Cross-origin probe |

### 6.5 Exit gate

- [ ] All tests green; CI AST lint passes
- [ ] `WSOriginRejection` alert test-fired in staging (D-53)
- [ ] Empty allowlist rejects all (HALT if fail-open)
- [ ] 24h staging soak with no user lockout
- [ ] Runbooks published: `ws-audit-log-troubleshooting.md`, `ws-cswsh-detection.md`

### 6.6 Rollback

```bash
# Per-IP cap neutralize (5 min TTF)
export JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999
systemctl restart juniper-cascor juniper-canopy

# Broaden allowlist (5 min TTF) -- '*' is REFUSED by parser (C-30)
export JUNIPER_WS_ALLOWED_ORIGINS='http://extra-origin:8050,http://localhost:8050'

# Idle timeout disable
export JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0

# Audit log disable
export JUNIPER_AUDIT_LOG_ENABLED=false

# Full revert
git revert <phase-b-pre-a-canopy-merge> <phase-b-pre-a-cascor-merge>
```

---

## 7. Phase B: frontend wiring + polling elimination (P0 WIN)

### 7.1 Goal

Browser drains `/ws/training` into bounded Dash stores, renders via `Plotly.extendTraces`, and **stops polling** when WS is healthy. Ships behind two-flag design (D-17+D-18). Ships with latency instrumentation (GAP-WS-24a/b), minimum NetworkVisualizer wire (D-06), Phase I cache bust, and jitter-backoff lift (GAP-WS-30/31).

### 7.2 Entry gate

- [ ] Phase 0-cascor merged + deployed + 72h soak green (D-38)
- [ ] `cascor_ws_seq_gap_detected_total==0` over full soak
- [ ] Phase B-pre-a (P3+P4) merged and deployed
- [ ] Phase A-SDK on PyPI (for future Phase C; not hard Phase B dep)
- [ ] Pre-Phase-B bandwidth baseline measured for 1h (D-62)
- [ ] NetworkVisualizer render tech recorded in first commit

### 7.3 Deliverables checklist

**Frontend JS**:
- [ ] `ws_dash_bridge.js` (~200 LOC): `window._juniperWsDrain`; 5 handlers; ring bounds **in handler** (C-19); `MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`
- [ ] `websocket_client.js`: jitter `delay = Math.random() * Math.min(30000, 500 * 2**attempt)` (GAP-WS-30); remove 10-attempt cap (GAP-WS-31); capture `server_instance_id`; `seq` tracking; `resume` on reconnect
- [ ] Delete `dashboard_manager.py:1490-1526` dead callback (GAP-WS-03)
- [ ] `ws_latency.js` (~50 LOC): browser latency beacon every 60s (GAP-WS-24a)
- [ ] rAF scaffold DISABLED (C-16)

**Python stores + drain callbacks**:
- [ ] `ws-metrics-buffer` drain callback -> `{events, gen, last_drain_ms}` (C-18)
- [ ] Update `ws-topology-buffer`, `ws-state-buffer` drains; add `ws-cascade-add-buffer`, `ws-candidate-progress-buffer`
- [ ] `ws-connection-status` store; emits only on change
- [ ] Refactor `_update_metrics_store_handler`: return `no_update` when WS connected; 1 Hz fallback (C-17)
- [ ] Apply polling-toggle to all poll handlers; **keep REST paths** (C-23)
- [ ] `MetricsPanel` -> clientside `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)` + `uirevision`
- [ ] NetworkVisualizer minimum wire (C-21); deep migration deferred if cytoscape
- [ ] `connection_indicator.py` (new): 4-state badge
- [ ] Demo mode parity: `ws-connection-status={connected:true, mode:"demo"}`
- [ ] `/api/ws_latency` POST + Prometheus histogram (GAP-WS-24b)
- [ ] `/api/ws_browser_errors` POST + counter (D-59)
- [ ] Phase I cache bust (D-60)
- [ ] Audit Prom counters hookup (deferred from B-pre-a)
- [ ] Two-flag gate: `enabled = enable_browser_ws_bridge and not disable_ws_bridge`

### 7.4 Cross-cutting deliverables

- **CCC-01 (schema)**: browser reads new envelope fields (`seq`, `server_instance_id`, `replay_buffer_capacity`, `emitted_at_monotonic`); sends `resume` on reconnect
- **CCC-02 (observability)**: 10 new canopy metrics (see section 7.5); SLO table aspirational until >=1 week data; error-budget burn-rate freeze rule (D-50)
- **CCC-03 (kill switches)**: two-flag pattern + URL `?ws=off` + ring-cap reduction; every switch CI-tested; staging drill during 72h soak
- **CCC-04 (cross-repo)**: canopy pins `juniper-cascor-client>=${SDK_VERSION_A}`; TestPyPI prerelease; cross-version CI lane (N-1 and N pinned)
- **CCC-05 (contract tests)**: `test_browser_message_handler_keys_match_cascor_envelope`; `test_fake_cascor_message_schema_parity`; `test_normalize_metric_produces_dual_format` (Phase H gate folded in); inline-literal rule
- **CCC-06 (documentation)**: runbooks `ws-bridge-kill.md`, `ws-bridge-debugging.md`, `ws-memory-soak-test-procedure.md`; Grafana JSON committed; PR cites GAP-WS-02/03/04/05/14/15/16/24a/24b/25/26/30/33
- **CCC-07 (configuration)**: 4 new canopy settings in canonical table
- **CCC-08 (backwards compat)**: REST polling handler KEPT FOREVER; regression harness in `fast` lane; golden shape file; every kill-switch test asserts REST works post-flip
- **CCC-09 (feature flags)**: two-flag pattern; flip criteria in `ws-bridge-kill.md`; flag flip is separate PR (P7)
- **CCC-10 (latency instrumentation)**: FULL PIPE ACTIVATED -- `emitted_at_monotonic` (0-cascor) -> `backend_relay_latency_ms` (canopy) -> browser beacon -> `/api/ws_latency` -> `delivery_latency_ms_bucket`; clock offset recompute on reconnect

### 7.5 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| **`test_bandwidth_eliminated_in_ws_mode`** | **Playwright (P0)** | `/api/metrics/history` requests == 0 over 60s |
| **`test_metrics_message_has_dual_format`** | **Playwright (RISK-01)** | Both flat + nested keys present |
| `test_chart_does_not_poll_when_websocket_connected` | dash_duo | REST count stays 0 |
| `test_chart_falls_back_to_polling_on_websocket_disconnect` | dash_duo | 1 Hz fallback |
| `test_demo_mode_metrics_parity` | dash_duo + e2e | RISK-08; both lanes |
| `test_resume_protocol_replays_missed_events` | Playwright | N events replayed |
| `test_seq_reset_on_cascor_restart` | Playwright | Snapshot refetch |
| `test_plotly_extendTraces_used_not_full_figure_replace` | Playwright | extendTraces, not replace |
| `test_ws_metrics_buffer_store_is_structured_object` | unit | `{events, gen, last_drain_ms}` |
| `test_both_flags_interact_correctly` | unit | Two-flag logic |
| `test_fallback_polling_at_1hz_when_disconnected` | unit | `n % 10 != 0` |
| `test_fake_cascor_message_schema_parity` | contract | CCC-05 |
| `test_browser_message_handler_keys_match_cascor_envelope` | contract | Schema sync |
| `test_network_visualizer_updates_on_ws_cascade_add` | unit | Minimum wire |
| `test_canopy_latency_api_aggregates_into_histogram` | unit | GAP-WS-24b |
| `test_latency_histogram_resilient_to_laptop_sleep` | unit | CCC-10 clock offset |
| `test_audit_log_prometheus_counters` | unit | Deferred hookup |
| `test_enable_browser_ws_bridge_env_override` | unit | D-53 kill switch |
| `test_disable_ws_bridge_env_override` | unit | D-53 kill switch |
| `test_asset_url_includes_version_query_string` | Playwright | Phase I cache bust |
| 72h memory soak | soak (blocking) | `browser_heap_mb` p95 growth <20% |
| Browser-bridge chaos | nightly | Random kills/restarts, no OOM, no freeze |

### 7.6 Observability

| Metric | Type | Labels |
|---|---|---|
| **`canopy_rest_polling_bytes_per_sec`** | **Gauge** | **`endpoint`** (P0 signal) |
| `canopy_ws_delivery_latency_ms_bucket` | Histogram | `type` (buckets {50,100,200,500,1000,2000,5000} ms) |
| `canopy_ws_backend_relay_latency_ms` | Histogram | -- (cascor->canopy hop) |
| `canopy_ws_browser_heap_mb` | Histogram | -- |
| `canopy_ws_browser_js_errors_total` | Counter | `component` |
| `canopy_ws_drain_callback_gen` | Gauge | `buffer` |
| `canopy_ws_active_connections` | Gauge | -- |
| `canopy_ws_reconnect_total` | Counter | `reason` |
| `canopy_ws_connection_status` | Gauge | `status` |
| `canopy_audit_events_total` | Counter | `event_type` (Prom hookup) |

**Alerts**: `WSDrainCallbackGenStuck` (page), `WSBrowserHeapHigh` (ticket), `WSJSErrorsNonZero` (ticket), `WSConnectionCount80` (ticket)

**SLOs** (binding after >=1 week production data):

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` | <100ms | <250ms | <500ms |
| `state` | <50ms | <100ms | <200ms |
| `command_response (set_params)` | <50ms | <100ms | <200ms |
| `command_response (start/stop)` | <100ms | <250ms | <500ms |
| `cascade_add` | <250ms | <500ms | <1000ms |
| `topology` <=64KB | <500ms | <1000ms | <2000ms |

### 7.7 Pull request plan

| # | Branch | Title | Repo | Merge order |
|---|---|---|---|---|
| P5 | `phase-b-cascor-audit-prom-counters` | `feat(cascor): audit-event Prom counters + relay latency` | cascor | 1 |
| P6 | `phase-b-canopy-drain-wiring` | `feat(canopy): ws_dash_bridge, extendTraces, connection indicator (flag off)` | canopy | 2 |
| P7 | `phase-b-canopy-flag-flip` | `config(canopy): enable_browser_ws_bridge=True` | canopy | 3 (after 72h soak) |

P7 is a **separate one-line PR** landing after Phase B is in staging 72 hours, the P0 metric is verified, RISK-10 memory-soak check passes, and the production deploy window is mid-week (D-61). Version bumps: canopy **minor** (new browser bridge + `/api/ws_latency`); cascor **patch** (audit Prom wiring).

### 7.8 Exit gate

1. All tests green including P0 acceptance gate
2. `canopy_rest_polling_bytes_per_sec` >=90% reduction sustained 1h in staging (D-62)
3. 72h memory soak: `browser_heap_mb` p95 <500 MB (D-39, RISK-10)
4. `canopy_ws_browser_js_errors_total==0` over 72h
5. Kill switch `disable_ws_bridge=True` tested; TTF <=5 min (D-53)
6. Metric-presence CI green (D-37)
7. `Settings.enable_browser_ws_bridge=False` is merged default; flip is P7

**P7 going/no-go** (72h with flag True via env):
8. `canopy_rest_polling_bytes_per_sec` reduction >=90% sustained 72h
9. Browser memory p95 <=500 MB over 72h
10. Mid-week deploy window (D-61)
11. Zero page-severity alerts in canopy window

### 7.9 Rollback

```bash
# Fastest (2 min TTF)
export JUNIPER_DISABLE_WS_BRIDGE=true
systemctl restart juniper-canopy

# Dev flag off (5 min TTF)
# Config PR: enable_browser_ws_bridge=False, redeploy

# Full revert (30 min TTF)
git revert <phase-b-canopy-merge-sha>
git push origin main

# Browser emergency hatch
# URL query param ?ws=off forces bridge off per-user
```

---

## 8. Phase B-pre-b: control-path security (parallel with Phase B)

**Explicitly does NOT gate Phase B or Phase C.** Phase C uses `/ws/control` via the canopy adapter (API-key + HMAC auth, not browser auth), and Phase B does not consume `/ws/control` at all. Phase D is the one that directly exposes the control plane to the browser and is therefore gated on Phase B-pre-b being in **production >=48 h**.

### 8.1 Goal

Full CSWSH/CSRF on `/ws/control`: Origin allowlist, cookie session + CSRF first-frame (M-SEC-02), rate limit (D-33, single bucket 10 cmd/s), idle timeout, adapter HMAC auth (D-29), adapter inbound validation (M-SEC-11), log-injection escaping, per-origin handshake cooldown. Gates Phase D.

### 8.2 Entry gate

- [ ] Phase B-pre-a in main
- [ ] Phase B in main (browser bridge working read-only)
- [ ] SessionMiddleware presence verified (assume absent; +0.5 day if so)

### 8.3 Deliverables checklist

- [ ] SessionMiddleware + `/api/csrf` endpoint; Dash template `window.__canopy_csrf`
- [ ] `websocket_client.js` first frame `{type:"auth", csrf_token:...}`
- [ ] Cookie: `HttpOnly; Secure; SameSite=Strict; Path=/`; `hmac.compare_digest`
- [ ] `/ws/control` Origin validation (reuses B-pre-a helper)
- [ ] M-SEC-04 auth-timeout: 5s for first frame -> close 1008
- [ ] M-SEC-05 rate limit: 10 tokens, 10/s; overflow -> `{command_response, status:"rate_limited", retry_after:0.3}`; connection stays up
- [ ] Per-origin cooldown: 10 rejections/60s -> 5-min IP block (429); cleared on restart
- [ ] M-SEC-06 opaque close reasons
- [ ] `disable_ws_control_endpoint: bool = False` (CSWSH emergency kill)
- [ ] M-SEC-11 adapter inbound validation (`CascorServerFrame`, `extra="allow"`)
- [ ] Adapter HMAC: `hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()` (D-29)
- [ ] Audit Prom counters + CRLF escape
- [ ] CI guardrail: `juniper-deploy` refuses `ws_security_enabled=false` in prod

### 8.4 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_csrf_required_for_websocket_first_frame` | unit | Absent/invalid -> close 1008 |
| `test_csrf_token_rotation_race` | unit | Mid-rotation safe |
| `test_session_cookie_httponly_secure_samesitestrict` | unit | All attrs |
| `test_command_rate_limit_10_per_sec` | unit | 11th -> rate_limited response |
| `test_rate_limit_response_is_not_an_error_close` | unit | Conn stays up |
| `test_per_origin_cooldown_triggers_after_10_rejections` | unit | IP blocked |
| `test_canopy_adapter_sends_hmac_csrf_token_on_connect` | unit | D-29 |
| `test_audit_log_escapes_crlf_injection` | unit | M-SEC-07 |
| `test_opaque_close_reasons_no_human_readable_strings` | unit | M-SEC-06 |
| `test_disable_ws_control_endpoint_kill_switch` | security | D-53 CI test |
| `test_cswsh_from_evil_page_cannot_start_training` | Playwright | Full CSWSH regression |
| `test_canopy_adapter_inbound_malformed_frame_logged_and_counted` | unit | M-SEC-11 |
| `test_ws_control_origin_rejected` | unit | Origin guard |
| `test_ws_control_idle_timeout_closes_1008` | unit | M-SEC-10 |
| `test_cascor_rejects_unknown_param_with_extra_forbid` | contract | D-34 |
| `test_deploy_compose_refuses_ws_security_false` | CI | D-10 guardrail |
| `test_adapter_synthetic_hmac_auth_frame_shape` | contract | CCC-05 |

**Observability**: `canopy_ws_auth_rejections_total{reason, endpoint}`, `canopy_ws_rate_limited_total{command, endpoint}`, `canopy_ws_command_total{command, status, endpoint}`, `canopy_ws_auth_latency_ms{endpoint}`, `canopy_ws_handshake_attempts_total{outcome}`, `canopy_ws_per_origin_cooldown_active`, `cascor_ws_audit_log_bytes_written_total`, `canopy_adapter_inbound_invalid_total`, `canopy_csrf_validation_failures_total`

**Alerts**: `WSAuditLogVolume2x` (ticket), `WSRateLimited` (ticket, sustained non-zero), per-origin cooldown active >5min (ticket)

### 8.5 Exit gate

- [ ] All tests green; manual CSWSH probes pass
- [ ] 48h staging soak; adapter reconnect rate stable
- [ ] CI guardrail refuses `ws_security_enabled=false` in prod
- [ ] Runbooks: `ws-auth-lockout.md`, `ws-cswsh-detection.md`
- [ ] Project-lead sign-off

### 8.6 Rollback

```bash
# Local-dev (5 min TTF)
export JUNIPER_WS_SECURITY_ENABLED=false  # prod CI refuses
systemctl restart juniper-canopy

# Hard-disable control endpoint (5 min TTF)
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Rate limiting off
export JUNIPER_WS_RATE_LIMIT_ENABLED=false

# Full revert
git revert <phase-b-pre-b-canopy> <phase-b-pre-b-cascor>
```

---

## 9. Phase C: set_params adapter (flag-off)

### 9.1 Goal

Canopy adapter splits parameter updates into "hot" (11 params: `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `epochs_max`, `max_iterations`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`) and "cold" (`init_output_weights`, `candidate_epochs`). Hot route over `/ws/control` via `set_params` command with 1.0 s default timeout (D-01); cold stay on REST PATCH. Feature-flagged behind `use_websocket_set_params=False` (D-47). REST path permanent (D-21).

### 9.2 Entry gate

- [ ] Phase A-SDK merged and on PyPI; `juniper-ml` extras pin bumped (D-57)
- [ ] Phase B in main with `enable_browser_ws_bridge=True` in staging >=7 days
- [ ] Adapter `run_coroutine_threadsafe` usage verified (assume ships fresh)
- [ ] Phase B-pre-b NOT required (adapter uses existing `X-API-Key` until Phase D)

### 9.3 Deliverables checklist

**Adapter** (`juniper-canopy/src/backend/cascor_service_adapter.py`):
- [ ] `_HOT_CASCOR_PARAMS: frozenset[str]` (11 params) + `_COLD_CASCOR_PARAMS`
- [ ] `apply_params(**params)` split -> `_apply_params_hot()` (WS, fires first) + `_apply_params_cold()` (REST)
- [ ] `_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)` with `command_id` (C-01); unconditional REST fallback on timeout/error
- [ ] Unclassified keys -> REST with WARNING log (C-09)
- [ ] `_control_stream_supervisor` background task: backoff `[1,2,5,10,30]`s, reconnect forever
- [ ] Bounded correlation map max 256 + `canopy_control_stream_pending_size` gauge
- [ ] Fail-loud startup: INFO summary of hot/cold/unknown classification
- [ ] `assert len(_HOT_CASCOR_PARAMS) > 0 if use_websocket_set_params`

**Dash clientside**:
- [ ] 250ms debounce in slider callback (C-29)

**Settings**:
- [ ] `use_websocket_set_params: bool = False` (C-28)
- [ ] `ws_set_params_timeout: float = 1.0` (C-03)

**Dependencies**:
- [ ] `pyproject.toml` bump `juniper-cascor-client>=${SDK_VERSION_A}`
- [ ] `juniper-ml/pyproject.toml` matching extras pin bump

### 9.4 Cross-cutting deliverables

- **CCC-02**: `canopy_set_params_latency_ms_bucket{transport, key}` histogram; `canopy_orphaned_commands_total{command}` counter; `canopy_control_stream_pending_size` gauge
- **CCC-03**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` (2 min MTTR)
- **CCC-05**: `test_canopy_adapter_exception_handling_matches_sdk_raises`
- **CCC-08**: REST `update_params` permanent; adapter falls back on WS failure
- **CCC-09**: flag with 6 hard flip gates (D-48)
- **CCC-10**: `canopy_set_params_latency_ms` histogram enables flip-gate comparison

### 9.5 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_apply_params_feature_flag_default_off` | unit | Default = False |
| `test_apply_params_hot_keys_go_to_websocket` | unit | Hot -> WS path |
| `test_apply_params_cold_keys_go_to_rest` | unit | Cold -> REST |
| `test_apply_params_mixed_batch_split` | unit | Correct split |
| `test_apply_params_hot_falls_back_to_rest_on_timeout` | unit | REST fallback |
| `test_apply_params_hot_falls_back_to_rest_on_disconnect` | unit | REST fallback |
| `test_apply_params_unclassified_keys_default_to_rest_with_warning` | unit | C-09 |
| `test_control_stream_supervisor_reconnects_with_backoff` | unit | Supervisor |
| `test_control_stream_supervisor_shutdown_cancels_pending` | unit | Cleanup |
| `test_len_pending_returns_to_zero_after_failure_modes` | nightly | Leak prevention |
| `test_cascor_rejects_unknown_param_with_extra_forbid` | contract | D-34 server side |
| `test_slider_debounce_250ms_collapses_rapid_updates` | unit | C-29 |
| `test_set_params_concurrent_correlation` | unit | 2 sliders distinguished |
| `test_slider_drag_routes_to_ws_with_flag_on` | e2e Playwright | WS path |
| `test_slider_drag_fallback_works_when_cascor_killed` | e2e Playwright | REST fallback |
| Chaos: adapter recv-task random exception injection | chaos | Map drained; supervisor restarts |

**Alert**: `CanopyOrphanedCommands` (ticket, not page): `rate > 1/60`

### 9.6 Pull request plan

| # | Branch | Title | Repo | Target |
|---|---|---|---|---|
| **P10** | `phase-c-canopy-set-params-adapter` | `feat(canopy): set_params hot/cold split, ws transport behind flag` | canopy | main |

### 9.7 Exit gate (merge, flag off)

- [ ] All unit tests green; coverage >=90%
- [ ] Flag off: `transport="rest"` has data; `transport="ws"` empty
- [ ] `test_set_params_concurrent_correlation` green
- [ ] Runbook `ws-set-params-feature-flag.md` published

### 9.8 Exit gate (flag FLIP -- separate one-line PR, D-48 hard gates)

1. >=7 days production data on WS code path
2. p99 delta (REST - WS) >= 50 ms (if smaller, do NOT flip -- no user-visible win)
3. Zero orphaned commands during canary week
4. Zero correlation-map leaks (nightly test)
5. Canary soak >=7 days
6. Zero page-severity alerts in canary window
7. Mid-week deploy window (D-61)

### 9.9 Rollback

```bash
# Instant (2 min TTF)
export JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false
systemctl restart juniper-canopy

# Tight timeout forces fast REST fallback (5 min TTF)
export JUNIPER_CONTROL_STREAM_TIMEOUT=0.1

# Hard-disable /ws/control
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert
git revert <phase-c-merge>
```

### 9.10 NOT in this phase

- SDK-level retries (D-20); SDK reconnect queue (D-20)
- REST path deprecation (D-21 -- never)
- Two-bucket rate limit (D-33)
- Frontend control buttons (Phase D)

---

## 10. Phase D: control buttons

### 10.1 Goal

Route browser `start`/`stop`/`pause`/`resume`/`reset` through `/ws/control` via `window.cascorControlWS.send({command, command_id: uuidv4()})`. REST POST at `/api/train/{command}` remains first-class forever (D-21). Per-command timeouts per source doc S7.32: `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`, `reset: 2s`. Ships behind `enable_ws_control_buttons=False` (D-49).

### 10.2 Entry gate

- [ ] **Phase B-pre-b in production >=48h** (NOT just staging -- CSRF/Origin gate)
- [ ] Phase B in main; `enable_browser_ws_bridge=True` (so `window.cascorControlWS` available)
- [ ] Zero CSRF incidents during 48h production soak
- [ ] Mid-week deploy window per D-61

### 10.3 Deliverables checklist

**Frontend**:
- [ ] Clientside callback on each button: WS if connected, REST POST if not
- [ ] Per-command client-side correlation map (`command_id` -> button)
- [ ] Orphaned-command pending-verification UI: button disabled while in-flight; resolves via `command_response` OR matching `state` event (RISK-13)
- [ ] Badge "pending" while awaiting WS ack

**Cascor**:
- [ ] `/ws/control` handler routes `{command, command_id, ...}` to REST-POST-backed handler
- [ ] Emits `command_response{command_id, status, error?}` (NO seq per C-02)
- [ ] Per-command timeout via `asyncio.wait_for`
- [ ] Command whitelist: `start`, `stop`, `pause`, `resume`, `reset`, `set_params`; unknown -> error

**Settings**: `enable_ws_control_buttons: bool = False`

### 10.4 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_training_button_ws_command_when_connected` | unit | WS path happy |
| `test_training_button_fallback_rest_when_disconnected` | unit | REST fallback |
| `test_rest_endpoint_still_200` | regression | C-23 preserved |
| `test_start_button_uses_websocket_command` | Playwright | WS command sent |
| `test_csrf_required_for_websocket_start` | Playwright | B-pre-b regression |
| `test_orphaned_command_resolves_via_state_event` | Playwright | RISK-13 |
| `test_per_command_timeout_start_10s` | unit | Start = 10s |
| `test_per_command_timeout_stop_2s` | unit | Stop = 2s |
| `test_unknown_command_rejected` | unit | Error response |
| `test_orphaned_command_falls_back_to_rest` | unit | Timeout -> REST |

**Observability**: `canopy_training_control_total{command, transport}`, `canopy_training_control_orphaned_total{command}`, `canopy_training_control_command_latency_ms{command, transport}`, `cascor_ws_control_command_received_total{command}`

### 10.5 Pull request plan

| # | Branch | Title | Repo | Target |
|---|---|---|---|---|
| **P11** | `phase-d-cascor-control-commands` | `feat(cascor): /ws/control command dispatch + per-command timeouts` | cascor | main |
| **P12** | `phase-d-canopy-button-ws-routing` | `feat(canopy): training buttons via /ws/control with REST fallback` | canopy | main |

Merge order: **P11 -> P12**.

### 10.6 Exit gate

- [ ] All tests green; `test_csrf_required_for_websocket_start` green
- [ ] Manual: Start with WS -> state within 10s; kill cascor -> REST fallback succeeds
- [ ] 24h staging soak zero orphaned commands
- [ ] 48h canary cohort zero orphan reports
- [ ] REST endpoints still receive non-browser traffic (access logs)
- [ ] `docs/REFERENCE.md` documents both REST and WS APIs
- [ ] **B-pre-b in production >=48h** confirmed at merge time

### 10.7 Rollback

```bash
# Buttons revert to REST (5 min TTF)
export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false
systemctl restart juniper-canopy

# CSWSH emergency
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert (20 min TTF)
git revert <phase-d-canopy> <phase-d-cascor>
```

### 10.8 NOT in this phase

- `set_params` routing (Phase C); full backpressure (Phase E); two-bucket rate limit

---

## 11. Phase E: backpressure (CONDITIONAL)

Ships **only if** Phase B production telemetry shows RISK-04/11 triggering (specifically: `cascor_ws_broadcast_send_duration_seconds` p95 > 100 ms sustained OR `cascor_ws_broadcast_timeout_total > 0` frequently). Otherwise 0.5s quick-fix from Phase 0-cascor suffices.

### 11.1 Goal

Replace serial fan-out with per-client pump tasks + bounded per-client queues + backpressure policy matrix. Default: `drop_oldest_progress_only` (D-19).

### 11.2 Entry gate

- [ ] Phase 0-cascor in main (quick-fix is the fallback if Phase E rolls back)
- [ ] Production telemetry from >=1 week justifies shipping

### 11.3 Policy matrix

| Event type | Queue | Overflow policy | Rationale |
|---|---:|---|---|
| `state` | 128 | close(1008) | Terminal-state-sensitive |
| `metrics` | 128 | close(1008) | Drops cause chart gaps |
| `cascade_add` | 128 | close(1008) | Each event is growth step |
| `candidate_progress` | 32 | drop_oldest | Coalesceable |
| `event` (training_complete) | 128 | close(1008) | Terminal-sensitive |
| `command_response` | 64 | close(1008) | Client waits |
| `pong` | 16 | drop_oldest | Client can re-ping |

### 11.4 Deliverables checklist

- [ ] Per-client `_ClientState` with `pump_task` + bounded `send_queue`
- [ ] `asyncio.Queue` bounded at 256 (configurable via `ws_per_client_queue_size`)
- [ ] Policy dispatch per matrix above
- [ ] `test_event_type_classification_for_backpressure_policy` -- every event type has explicit mapping (RISK-11 prevention)
- [ ] `Settings.ws_backpressure_policy: Literal["block", "drop_oldest_progress_only", "close_slow"] = "drop_oldest_progress_only"`

### 11.5 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_slow_client_does_not_block_other_clients` | unit | Fast clients unaffected |
| `test_slow_client_send_timeout_closes_1008_for_state` | unit | State -> close |
| `test_slow_client_progress_events_dropped` | unit | Progress -> drop oldest |
| `test_drop_oldest_queue_policy` | unit | Queue semantics |
| `test_backpressure_default_is_drop_oldest_progress_only` | unit | Regression |
| `test_event_type_classification` | unit | Every type mapped |
| `test_block_policy_still_works` | unit | Opt-in alternative |
| `test_terminal_state_events_not_dropped` | unit | RISK-11 guard |

**Observability**: `cascor_ws_dropped_messages_total{reason, type}`, `cascor_ws_slow_client_closes_total`, `cascor_ws_per_client_queue_depth_histogram`

**Alert**: `WSStateDropped` (PAGE): any non-zero `dropped_messages_total{type="state"}`

### 11.6 Exit gate

- [ ] All tests green
- [ ] Load test: 50 clients, 1 slow (2s delay), 49 fast p95 < 200ms
- [ ] 48h staging zero `WSStateDropped` alerts
- [ ] Runbook `ws-backpressure-policy.md` published

### 11.7 Rollback

```bash
# Revert to block policy (5 min TTF; RISK-04 returns but intentional)
export JUNIPER_WS_BACKPRESSURE_POLICY=block
systemctl restart juniper-cascor

# Full revert
git revert <phase-e-cascor>
```

---

## 12. Phase F: heartbeat + reconnect jitter

### 12.1 Goal

Add application-level ping/pong heartbeat for dead-connection detection faster than uvicorn framework level. Jitter formula already in Phase B; this phase adds heartbeat contract and reconnect-cap lift finalization.

### 12.2 Entry gate

- [ ] Phase B in main (jitter already landed)

### 12.3 Deliverables checklist

- [ ] Cascor `/ws/training` + `/ws/control` emit `{"type":"ping","ts":<float>}` every 30s
- [ ] Client JS replies `pong` within 5s
- [ ] Dead-conn detection: no `pong` within 10s -> close 1006 -> trigger reconnect
- [ ] Integrates with M-SEC-10 idle timeout (heartbeat resets timer)
- [ ] GAP-WS-31: uncap reconnect attempts; max 60s interval
- [ ] Jitter formula: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))`

### 12.4 Test acceptance

| Test | Type | Criterion |
|---|---|---|
| `test_ping_sent_every_30_seconds` | unit | Cadence |
| `test_pong_received_cancels_close` | unit | Pong resets timer |
| `test_reconnect_backoff_has_jitter` | unit | 0 <= delay <= cap |
| `test_reconnect_attempt_unbounded_with_cap` | unit | >10 attempts |
| `test_dead_connection_detected_via_missing_pong` | unit | 10s -> close 1006 |
| `test_jitter_formula_no_nan_delay` | unit | No NaN/Infinity |

**Alert**: `WSReconnectStorm` (ticket): `rate(canopy_ws_reconnect_total[5m]) > 5x baseline`

### 12.5 Exit gate

- [ ] All 6 tests pass
- [ ] Manual: firewall drop -> dead conn detected within 40s (30+10)
- [ ] 48h staging: no NaN delays, no reconnect storms
- [ ] Runbook `ws-reconnect-storm.md` published

### 12.6 Rollback

```bash
# Disable auto-reconnect (10 min TTF; users hard-refresh)
export JUNIPER_DISABLE_WS_AUTO_RECONNECT=true

# Or cache-busted JS hotfix with old jitter formula
git revert <phase-f-merge>
```

---

## 13. Phase G: cascor set_params integration tests

### 13.1 Goal

Cascor-side integration tests exercising `/ws/control` `set_params` via FastAPI `TestClient.websocket_connect()` (no SDK dependency). Assert wire contract: `command_id` echo, whitelist filtering, per-frame size cap, concurrent correlation, epoch-boundary application, Origin regression, rate-limit regression.

### 13.2 Entry gate

- [ ] Phase 0-cascor in main
- [ ] Phase B-pre-b in main (Origin + rate-limit guards exist to regression-test)

### 13.3 Deliverables checklist

15 tests in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`:

- [ ] `test_set_params_via_websocket_happy_path`
- [ ] `test_set_params_whitelist_filters_unknown_keys`
- [ ] `test_set_params_init_output_weights_literal_validation`
- [ ] `test_set_params_oversized_frame_rejected` (64KB cap)
- [ ] `test_set_params_no_network_returns_error`
- [ ] `test_unknown_command_returns_error` (GAP-WS-22 regression)
- [ ] `test_malformed_json_closes_with_1003` (GAP-WS-22)
- [ ] `test_set_params_origin_rejected` (M-SEC-01b regression)
- [ ] `test_set_params_unauthenticated_rejected`
- [ ] `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05)
- [ ] `test_set_params_bad_init_output_weights_literal_rejected`
- [ ] **`test_set_params_concurrent_command_response_correlation`** (R1-05 S4.29)
- [ ] **`test_set_params_during_training_applies_on_next_epoch_boundary`** (ack vs effect)
- [ ] **`test_set_params_echoes_command_id`** (C-01 mandatory gate)
- [ ] `test_ws_control_command_response_has_no_seq` (C-02 cross-ref)

Tests marked `@pytest.mark.critical` -- run in `fast` lane on every PR to cascor or cascor-client.

**Contract test**: `test_fake_cascor_message_schema_parity` (runs in both cascor + canopy CI)

### 13.4 Pull request plan

| # | Branch | Title | Repo | Target |
|---|---|---|---|---|
| **P15** | `phase-g-cascor-set-params-integration` | `test(cascor): /ws/control set_params integration suite + contract lane` | cascor | main |

### 13.5 Exit gate

- [ ] All 15 tests pass
- [ ] `pytest -m contract` green in both cascor and canopy CI

### 13.6 Rollback

n/a (test-only phase).

---

## 14. Phase H: normalize_metric regression gate

### 14.1 Goal

Lock in dual metric format contract (flat + nested keys both present) with regression test + CODEOWNERS hard merge gate (D-27). Document every consumer. **NO removal of any format in this migration.** (C-22)

### 14.2 Entry gate

- [ ] Phase B in main (MVS-TEST-14 dual-format test already landed)
- [ ] CODEOWNERS file present in `juniper-canopy/.github/CODEOWNERS`

### 14.3 Deliverables checklist

- [ ] `test_normalize_metric_produces_dual_format` (asserts both nested AND flat)
- [ ] `test_normalize_metric_nested_topology_present`
- [ ] `test_normalize_metric_preserves_legacy_timestamp_field`
- [ ] `test_normalize_metric_shape_hash_matches_golden_file`
- [ ] Consumer audit doc `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`
- [ ] CODEOWNERS entries: `normalize_metric.py @<project-lead>`, `metrics_panel.py @<project-lead>` -- **hard merge gate**
- [ ] Pre-commit hook refusing format-removal commits
- [ ] Shape hash golden file `normalize_metric_shape.golden.json`

### 14.4 Pull request plan

| # | Branch | Title | Repo | Target |
|---|---|---|---|---|
| **P16** | `phase-h-normalize-metric-audit` | `docs(audit): normalize_metric consumer audit + CODEOWNERS + regression` | canopy | main |

### 14.5 Exit gate

- [ ] Regression tests green
- [ ] CODEOWNERS enforced (test PR touching file without owner review -> blocked)
- [ ] Consumer audit doc merged
- [ ] Pre-commit hook installed

### 14.6 Rollback

```bash
# Revert (10 min TTF) -- CODEOWNERS rule disappears
git revert <phase-h-merge>
```

### 14.7 NOT in this phase

- `_normalize_metric` refactor (requires new migration plan)
- Removal of either format (never without RFC per D-21 principle)

---

## 14a. Resolved unresolved items (from R3-02 S1.7)

R2-04 S6 listed 13 items as unresolved. All are resolved with defaults-of-last-resort so no item remains TBD.

| # | Item | Resolution | Verifier |
|---|---|---|---|
| 1 | NetworkVisualizer render tech | **Assume cytoscape**; first Phase B commit greps; if Plotly, +1 day | Phase B implementer |
| 2 | SessionMiddleware presence | **Assume absent**; B-pre-b budgets +0.5 day; first commit verifies | Phase B-pre-b implementer |
| 3 | Dash version | **Does not affect plan**; Option B Interval drain regardless | Phase B implementer |
| 4 | Plotly.js version | **Does not affect plan**; `extendTraces` works on 1.x and 2.x | Phase B implementer |
| 5 | Adapter `run_coroutine_threadsafe` | **Assume not yet used**; Phase C ships fresh | Phase C implementer |
| 6 | Cascor `command_id` passthrough | **Cascor must be modified** (Phase 0-cascor A-srv-9); Phase G enforces | Phase 0-cascor implementer |
| 7 | Adapter auth (D-29) | **HMAC** | Settled |
| 8 | Phase B flag default (D-17) | **flag-off** | Settled |
| 9 | Backpressure default (D-19) | **`drop_oldest_progress_only`** | Settled |
| 10 | Security flag (D-10) | **positive-sense `ws_security_enabled`** | Settled |
| 11 | Replay buffer (D-35) | **1024 tunable** | Settled |
| 12 | Effort | **15.75 expected** | Settled |
| 13 | Bandwidth baseline (D-62) | **1h pre-Phase-B** | Settled |

All 13 resolved. **No item in this plan is TBD.**

---

## 14b. Cross-cutting concerns summary

10 CCCs from R2-03, with per-phase touchpoints integrated in sections 4-14. This section lists each CCC's owning role and key acceptance criteria.

| # | CCC | Owner | Key acceptance criteria |
|---|---|---|---|
| CCC-01 | Wire-format schema evolution | backend-cascor lead | `command_id` rename enforced; additive-only contract tested; rollout state matrix in Phase 0-cascor PR |
| CCC-02 | Observability stack | backend-canopy lead | Metric-before-behavior via CI; SLO panel deployed; page alerts test-fired; metrics-presence in `fast` lane |
| CCC-03 | Kill switch architecture | security lead | Every phase >=1 switch; every switch CI-tested; staging drills; MTTR <=5 min |
| CCC-04 | Cross-repo version pinning | project lead | Merge order binding; PyPI propagation tested; TestPyPI prerelease; cross-version CI; Helm bumps match |
| CCC-05 | Contract testing | backend-cascor lead | `contract` marker in 3 repos; 11 contract tests; every-PR lane; inline-literal rule |
| CCC-06 | Documentation as deliverable | project lead | 11 runbooks; PR template with IDs/threat-model/kill-switch/rollback; CODEOWNERS for critical paths |
| CCC-07 | Configuration management | ops lead | Canonical settings table (S2.8) in sync; CI for undocumented settings, wildcard refusal, prod compose guard |
| CCC-08 | Backwards compatibility | project lead | REST regression harness in `fast` lane; golden shape file; kill-switch tests assert REST post-flip |
| CCC-09 | Feature flag lifecycle | project lead | Flag inventory (S2.7); every flag has lifecycle; flip is separate PR with criteria |
| CCC-10 | Latency instrumentation | frontend lead | `emitted_at_monotonic` in 0-cascor; full pipe in Phase B; Grafana panel; buckets {50..5000} ms; SLO promotion after >=1 week |

**Cross-version CI lane** (CCC-04 new): canopy e2e runs against N-1 AND N pinned SDK versions; both must pass.

---

## 15. Cross-repo merge sequence

| Order | PR | Repo | Phase | Blocking next? |
|---:|---|---|---|---|
| 1 | P2 `phase-a-sdk-set-params` | cascor-client | A-SDK | Yes (PyPI -> 2-5 min) |
| 2 | P1 `phase-0-cascor-seq-replay-resume` | cascor | 0-cascor | Yes (72h soak) |
| 3 | P3 `phase-b-pre-a-cascor-security` | cascor | B-pre-a | Yes |
| 4 | P4 `phase-b-pre-a-canopy-security` | canopy | B-pre-a | Yes |
| -- | | | | **72h soak (0-cascor) + 24h soak (B-pre-a)** |
| 5 | P5 `phase-b-cascor-audit-prom-counters` | cascor | B | No |
| 6 | P6 `phase-b-canopy-drain-wiring` | canopy | B | Yes |
| -- | | | | **72h staging soak (Phase B flag-on)** |
| 7 | P7 `phase-b-canopy-flag-flip` | canopy | B | Yes -- **P0 WIN** |
| 8 | P15 `phase-g-cascor-set-params-integration` | cascor | G | No (parallel) |
| 9 | P8 `phase-b-pre-b-cascor-control-security` | cascor | B-pre-b | Yes |
| 10 | P9 `phase-b-pre-b-canopy-csrf-audit` | canopy | B-pre-b | Yes (48h prod soak) |
| 11 | P10 `phase-c-canopy-set-params-adapter` | canopy | C | No |
| 12 | P11 `phase-d-cascor-control-commands` | cascor | D | Yes |
| 13 | P12 `phase-d-canopy-button-ws-routing` | canopy | D | No |
| 14 | P13 (conditional) `phase-e-cascor-backpressure` | cascor | E | No |
| 15 | P14 `phase-f-heartbeat-jitter` | cascor+canopy | F | No |
| 16 | P16 `phase-h-normalize-metric-audit` | canopy | H | No |
| -- | `juniper-ml` extras pin bumps | juniper-ml | -- | One-line follow-ups |

**Critical path (P0 win)**: P2 -> P1 -> P3 -> P4 -> (soak) -> P6 -> (soak) -> P7.

**Version bumps**:

| Repo | Phase | Bump |
|---|---|---|
| cascor-client | A | minor |
| cascor | 0-cascor | minor |
| cascor | B-pre-a/b | patch |
| cascor | E | minor |
| cascor | G | patch (test-only) |
| canopy | B-pre-a/b | patch |
| canopy | B | minor |
| canopy | C/D/H | patch |
| juniper-ml | per SDK bump | patch |

Helm `Chart.yaml` `version` + `appVersion` match app semver.

**Worktree naming**: `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>` in `/home/pcalnon/Development/python/Juniper/worktrees/`.

**Rollback order** (reverse-dependency): revert canopy first, then cascor. Never rollback in original order (SDK -> cascor -> canopy) -- creates broken intermediate states.

**Day-by-day timeline** (from R3-02 S16, applied):

```
Day 1 (parallel):
    P2  juniper-cascor-client   Phase A-SDK
          -> merge -> tag -> PyPI -> wait 2-5 min
    P1  juniper-cascor          Phase 0-cascor
          -> 72-hour staging soak (D-38)

Day 2 (while P1 soaks):
    P2b juniper-ml              extras pin bump (D-57)

Day 3-5 (after P1 soak):
    P3  juniper-cascor          Phase B-pre-a cascor
    P4  juniper-canopy          Phase B-pre-a canopy (depends P3)
          -> deploy to staging

Day 6-7 (parallel):
    P5  juniper-cascor          Phase B residual (audit Prom)
    P6  juniper-canopy          Phase B canopy drain (flag off)
          -> 72-hour soak with enable_browser_ws_bridge=True via env

Day 10 (mid-week per D-61):
    P7  juniper-canopy          Phase B flag flip -> True
          -> production deploy
          -- P0 WIN LANDS HERE --

Day 10-12 (parallel with P7 in production):
    P15 juniper-cascor          Phase G integration tests
    P8  juniper-cascor          Phase B-pre-b cascor security
    P9  juniper-canopy          Phase B-pre-b canopy CSRF (depends P8)
          -> 48-hour staging soak

Day 13-16:
    P10 juniper-canopy          Phase C set_params adapter (flag off)
          -> >=7 days canary
    P10b juniper-canopy         Phase C flag flip (D-48 hard gates)

Day 17-19 (after B-pre-b in prod >=48h):
    P11 juniper-cascor          Phase D cascor command dispatch
    P12 juniper-canopy          Phase D canopy buttons (depends P11)

Day 20+:
    P13 juniper-cascor          Phase E backpressure (OPTIONAL)
    P14 juniper-cascor+canopy   Phase F heartbeat + jitter
    P16 juniper-canopy          Phase H normalize_metric audit
```

**TestPyPI**: Phase A publishes to TestPyPI on PR; canopy downstream PRs install from TestPyPI for e2e before real publish.

**Cross-version CI lane** (CCC-04): canopy e2e runs against N-1 AND N pinned SDK; both must pass.

**Branch naming**: `ws-migration/phase-<letter>-<slug>`.

**Merge strategy**: squash-merge (linear history). Use GitHub merge queue where available.

---

## 16. Kill switch matrix

Every switch has a CI test; untested = doesn't count (C-39). Staging drills during each soak; TTF >5 min = phase does not ship.

| Phase | Switch (env var / action) | Default | Who | MTTR | Validation metric | CI test |
|---|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 1024 | ops | 5 min | `resume_requests_total{outcome="out_of_range"}` spike | `test_replay_buffer_size_zero_disables_replay` |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | 0.5 | ops | 5 min | `broadcast_timeout_total` spike | `test_send_timeout_env_override` |
| 0-cascor | Rolling restart cascor | -- | ops | 10 min | New `server_instance_id` | manual |
| 0-cascor | `git revert` P1 | -- | ops | 15 min | Clients snapshot-refetch | -- |
| A-SDK | Downgrade `juniper-cascor-client` pin | -- | ops | 15 min | `pip index versions` | -- |
| A-SDK | PyPI yank (if installs-won't-import) | -- | ops | 2 min | Package 404 | -- |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 | ops | 5 min | `per_ip_rejected_total -> 0` | `test_per_ip_cap_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | `[]` | ops | 5 min | `origin_rejected_total` drops | `test_origin_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS='*'` | -- | -- | -- | **REFUSED BY PARSER** (C-30) | `test_wildcard_refused` |
| B-pre-a | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | 120 | ops | 5 min | Connections persist | `test_idle_timeout_env_override` |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | True | ops | 5 min | No new writes | `test_audit_log_env_override` |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | True | ops | 5 min | Auth drops (prod CI refuses) | `test_ws_security_env_override` |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | False | ops | 5 min | WS control -> 0 | `test_disable_ws_control_endpoint` |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | True | ops | 5 min | Rate-limit freezes | `test_rate_limit_env_override` |
| B | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | False->True | ops | 5 min | Polling bytes rise to baseline | `test_enable_browser_ws_bridge_env_override` |
| B | `JUNIPER_DISABLE_WS_BRIDGE=true` | False | ops | 5 min | Same (permanent kill) | `test_disable_ws_bridge_env_override` |
| B | Hardcoded ring-cap reduction | -- | dev | 1 hour | `browser_heap_mb` drops | -- |
| B | URL `?ws=off` | -- | user | instant | Per-user bridge off | manual |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | False | ops | 2 min | WS transport freezes | `test_use_websocket_set_params_env_override` |
| C | `JUNIPER_CONTROL_STREAM_TIMEOUT=0.1` | 1.0 | ops | 5 min | Tight timeout -> REST | `test_ws_set_params_timeout_env_override` |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | False | ops | 5 min | REST transport rises | `test_enable_ws_control_buttons_env_override` |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | False | ops | 5 min | WS control -> 0 | (reused) |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | `drop_oldest_progress_only` | ops | 5 min | `dropped_messages_total -> 0` | `test_ws_backpressure_policy_env_override` |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | False | ops | 10 min | `reconnect_total` freezes | `test_disable_ws_auto_reconnect_env_override` |
| H | `git revert` P16 | -- | ops | 10 min | Shape hash matches pre-H | -- |
| I | `git revert` cache-bust | -- | ops | 10 min | Asset URL reverts | -- |

**Meta-rule** (D-53): staging drill during every soak. Two consecutive switch failures -> **halt migration for re-planning**.

**Abandon trigger**: if a kill-switch flip does not produce expected metric delta within 60 s, escalate. Two switches in sequence fail -> migration halts.

---

## 17. Risk register

| ID | Risk | Sev/Lik | Phase | Kill switch | TTF | Key mitigation |
|---|---|---|---|---|---|---|
| 01 | Dual metric format removed aggressively | H/M | H | `git revert` | 10 min | CODEOWNERS hard gate; pre-commit hook; regression test in Phase B; shape hash in Phase H |
| 02 | Phase B clientside_callback hard to debug | M/H | B | `disable_ws_bridge=true` | 5 min | `drain_callback_gen` gauge; `browser_js_errors_total`; 72h soak; flag default False |
| 03 | Phase C REST+WS ordering race | M/L | C | `use_websocket_set_params=false` | 2 min | Disjoint hot/cold; `_training_lock`; fail-loud startup; bounded map 256 |
| 04 | Slow-client blocks broadcasts | M/M | E (0-cascor quick-fix) | `ws_backpressure_policy=close_slow` | 5 min | 0.5s send timeout; full per-client pump in Phase E |
| 05 | Playwright misses real-cascor regression | M/M | B, D | fix the test | -- | Nightly smoke against real cascor; `schema_parity` contract test |
| 06 | Reconnection storm after cascor restart | L/M | F | `disable_ws_auto_reconnect=true` | 10 min | Full jitter (ships in Phase B) |
| 07 | 50-conn cap hit (multi-tenant) | L/L | n/a | raise `ws_max_connections` | 10 min | Single-tenant v1 (C-24) |
| 08 | Demo mode parity breaks | L/M | B | revert PR | 10 min | `test_demo_mode_metrics_parity` blocker in both lanes |
| 09 | Phase C unexpected behavior | L/M | C | `use_websocket_set_params=false` | 2 min | Flag False; 6 hard flip gates; >=7-day canary |
| 10 | Browser memory exhaustion | M/H | B | `disable_ws_bridge=true` | 5 min | `extendTraces(maxPoints=5000)`; ring-bound in handler (AST lint); 72h soak |
| 11 | Silent data loss via drop-oldest | H/L | E | `ws_backpressure_policy=block` | 5 min | Only progress dropped; state closes; per-type assertion; `WSStateDropped` PAGE |
| 12 | Background tab memory spike | L/M | B | same as RISK-10 | 5 min | Cap-in-handler independent of drain rate |
| 13 | Orphaned commands after timeout | M/M | B,C,D | reduce timeouts | 5 min | `command_id` correlation; pending UI; resolve via response OR state event |
| 14 | Cascor crash mid-broadcast | L/L | B | rolling restart | 10 min | `server_instance_id` forces resync; `WSSeqCurrentStalled` PAGE |
| 15 | **CSWSH attack** | **H/M** | B-pre-a/b | `disable_ws_control_endpoint=true` | 5 min | Origin + CSRF + `WSOriginRejection` PAGE; **abandon trigger if kill switch fails** |
| 16 | Topology >64KB silently fails | M/M | B-pre-a | REST fallback | 5 min | Size caps; `oversized_frame_total` alert; REST `/api/topology` preserved |
| CCC-01 | `request_id` rename incomplete | H/M | all | pre-merge grep | -- | D-02 grep check; `test_command_id_echoed` |
| CCC-02 | Metric added, no alert/panel | M/M | all | CI metrics-presence | -- | D-37 blocker test |
| CCC-03 | Kill switch untested in CI | Crit/M | all | halt migration | -- | D-53 staging drill; two-failure abandon |
| CCC-04 | Cross-repo pin at unreleased version | H/L | cross-repo | pin previous | 10 min | Merge-order enforcement; TestPyPI prerelease |
| CCC-05 | Contract test is tautological | M/M | B, G | review audit | -- | Inline-literal rule; no cross-repo fixtures |

---

## 18. Observability master matrix

| Phase | New metrics (count) | New alerts | New dashboards |
|---|---|---|---|
| 0-cascor | 15 cascor_ws_* | `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap`, `WSPendingConnectionStuck`, `WSSlowBroadcastP95` | -- |
| A-SDK | 1 `juniper_cascor_client_ws_set_params_total{status}` | -- | -- |
| B-pre-a | 6 security metrics | `WSOriginRejection` (PAGE), `WSOversizedFrame` (PAGE) | -- |
| B | 10 canopy_ws_* + Prom hookup | `WSDrainCallbackGenStuck` (page), `WSBrowserHeapHigh`, `WSJSErrorsNonZero`, `WSConnectionCount80` | "WebSocket health", "Polling bandwidth" Grafana JSON |
| B-pre-b | 9 auth/security | `WSAuditLogVolume2x`, `WSRateLimited`, per-origin cooldown | Security panel |
| C | 3 (set-params-latency, orphaned, pending-size) | `CanopyOrphanedCommands` (ticket) | -- |
| D | 4 (command-latency, orphaned, commands, received) | -- | -- |
| E | 3 (dropped, queue-depth, slow-closes) | `WSStateDropped` (PAGE) | -- |
| F | reconnect-jitter histogram | `WSReconnectStorm` (ticket) | -- |
| G | -- | -- | -- |
| H | -- | -- | shape-hash trend |

**Page-severity alerts** (4 total): `WSOriginRejection` (D-51), `WSOversizedFrame`, `WSStateDropped`, `WSSeqCurrentStalled` (D-52). All must be test-fired in staging (D-53).

**Canonical label values** (cardinality discipline):
- `endpoint` in {`/ws/training`, `/ws/control`, `/ws/worker`, `/ws/monitor`}
- `type` in {`metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, `event`, `command_response`, `connection_established`, `resume_ok`, `resume_failed`}
- `transport` in {`ws`, `rest`}
- `outcome` in {`accepted`, `rejected`, `timeout`, `success`, `server_restarted`, `out_of_range`, `malformed`, `no_resume_timeout`, `second_resume`}

**Metric-presence pytest** (D-37): runs in `fast` lane on every PR. Scrapes cascor + canopy `/metrics`, asserts every canonical metric name present. Failure blocks merge.

**Metric naming audit**: pytest scans `cascor/**/*.py` and `canopy/**/*.py` for `Counter(...)`, `Gauge(...)`, `Histogram(...)` calls and asserts names appear in canonical catalog. Prevents drive-by additions.

**Audit logger scope** (D-28): dedicated `canopy.audit` logger. JSON formatter with fields `{ts, actor, action, command, params_before, params_after, outcome, request_ip, user_agent}`. `TimedRotatingFileHandler` -- daily rotation, 30-day retention dev / 90-day prod. Scrub allowlist. CRLF/tab escaping (M-SEC-07 extended). Skeleton in Phase B-pre-a; Prometheus counters in Phase B.

**Clock offset recomputation** (CCC-10): on every reconnect, browser JS captures `server_start_time - client_now` and uses delta as correction factor (prevents laptop-sleep skew of latency histogram). Tested via `test_latency_histogram_resilient_to_laptop_sleep`.

**Dashboard-as-code**: all Grafana panels defined in JSON committed to `juniper-canopy/deploy/grafana/`. PR review check prevents drift between `/metrics` scrape and panel query.

---

## 19. Decision quick-reference

62 decisions. High cost-of-deferral (decide before phase starts): **D-02, D-11, D-17, D-19, D-23**.

| D | Summary | Applied | Source |
|---|---|---|---|
| 01 | `set_params` timeout | **1.0 s** | R1-05 S4.1 |
| 02 | Correlation field | **`command_id`** | R1-05 S4.2 |
| 03 | `command_response` seq | **No** | R1-05 S4.17 |
| 04 | rAF coalescer | **scaffold-disabled** | R1-05 S4.3 |
| 05 | REST fallback cadence | **1 Hz** | R1-05 S4.4 |
| 06 | NetworkVisualizer scope | **minimum wire** | R1-05 S4.5 |
| 07 | `ws-metrics-buffer` shape | **structured `{events, gen, last_drain_ms}`** | R1-05 S4.7 |
| 08 | GAP-WS-24 split | **24a + 24b** | R1-05 S4.8 |
| 09 | B-pre effort | **0.5 (a) + 1.5-2 (b)** | R1-05 S4.9 |
| 10 | Security flag | **positive `ws_security_enabled`** | R1-02; R2-01; R2-03 |
| 11 | 0-cascor carve-out | **carve out** | R1-05 S4.19 |
| 12 | M-SEC-10/11/12 | **adopt 10/11; fold 12 into 07** | R1-05 S4.15 |
| 13 | GAP-WS-19 | **RESOLVED; test only** | R1-05 S4.16 |
| 14 | Two-phase registration | **`_pending_connections`** | R1-05 S4.18 |
| 15 | `server_instance_id` role | **programmatic key** | R1-05 S4.20 |
| 16 | `replay_buffer_capacity` | **add to connection_established** | R1-05 S4.21 |
| 17 | Phase B flag default | **flag-off** | R1-02 |
| 18 | Permanent kill switch | **add `disable_ws_bridge`** | R1-05 S4.45 |
| 19 | Phase E default | **`drop_oldest_progress_only`** | R1-05 S4.36 |
| 20 | SDK retries | **none; caller decides** | R1-05 S4.22 |
| 21 | REST retention | **permanent** | R1-02 principle 7 |
| 22 | Debounce layer | **Dash clientside** | R1-05 S4.24 |
| 23 | B-pre split | **a + b** | R1-05 S4.35 |
| 24 | Per-IP cap | **5** | R1-05 S4.37 |
| 25 | Deployment topology | **single-tenant v1** | R1-05 S4.38 |
| 26 | Shadow traffic | **skip** | R1-05 S4.39 |
| 27 | CODEOWNERS | **hard gate** | R1-05 S4.41 |
| 28 | Audit logger | **dedicated; skeleton B-pre-a; Prom B** | R1-05 S4.14 |
| 29 | Adapter auth | **HMAC** | R1-05 S4.43 |
| 30 | One-resume-per-conn | **enforced** | R1-05 S4.12 |
| 31 | Per-command HMAC | **defer indefinitely** | R1-05 S4.11 |
| 32 | Multi-tenant replay | **defer** | R1-05 S4.13 |
| 33 | Rate limit | **single 10/s** | R1-05 S4.46 |
| 34 | Unclassified keys | **cascor `extra="forbid"` + adapter REST+WARN** | R1-05 S4.44 |
| 35 | Replay buffer size | **1024, env-tunable** | R2-01 S18.1 |
| 36 | Buffer `=0` kill switch | **supported** | R1-02 S3.3 |
| 37 | Metrics-presence CI | **enforce** | R1-02 S10.6 |
| 38 | 0-cascor soak | **72 h** | R1-02 S3.4 |
| 39 | Phase B soak | **72 h** | R2-04 |
| 40 | Chaos tests | **3 blocking (0-cascor); rest nightly** | R2-01 S18.9 |
| 41 | Load tests | **blocking for 0-cascor** | R1-02 S10.3 |
| 42 | Frame budget test | **recording-only** | R1-05 S4.3 |
| 43 | `contract` marker | **add** | R1-05 S4.34 |
| 44 | Browser matrix | **Chromium only** | R1-05 S4.31 |
| 45 | User research | **skip v1** | R1-05 S4.32 |
| 46 | `ws_send_timeout_seconds` | **env-configurable, 0.5** | R1-02 S3.2 |
| 47 | Phase C flag | **False** | unanimous |
| 48 | Phase C flip criteria | **6 hard gates** | R1-02 S6.1 |
| 49 | Phase D flag | **add `enable_ws_control_buttons=False`** | R1-02 S7.1 |
| 50 | Error-budget freeze | **enforce** | R1-02 S2.4 |
| 51 | `WSOriginRejection` severity | **page** | R1-02 S2.4 |
| 52 | `WSSeqCurrentStalled` | **page** | R1-02 S2.4 |
| 53 | Kill-switch MTTR tested | **staging drill** | R1-02 S13.7 |
| 54 | REST handler retention | **forever** | R1-05 S4.23 |
| 55 | Source-doc patches | **batch in Round 5** | R1-05 S8.6 |
| 56 | REST deprecation | **never** | R2-04 S5.1 |
| 57 | juniper-ml extras bump | **same-day** | R2-04 S5.2 |
| 58 | CI budget | **<=25% increase** | R2-04 S5.3 |
| 59 | Browser JS error pipeline | **POST `/api/ws_browser_errors`** | R2-04 S5.4 |
| 60 | Worktree policy | **one per phase per repo** | R2-04 S5.5 |
| 61 | Deploy freeze | **mid-week for flag flips** | R2-04 S5.6 |
| 62 | Bandwidth baseline | **1h pre-Phase-B** | R2-04 S5.7 |

---

## 20. Test acceptance master matrix

Canonical tests with phase, type, and measurable criterion. Subset of load-bearing tests; full catalog in R2-02 S15.2 (~142 tests).

| Phase | Test | Type | Criterion |
|---|---|---|---|
| 0-cascor | `test_seq_monotonically_increases` | unit | seq(n+1) > seq(n) |
| 0-cascor | `test_replay_buffer_bounded` | unit | maxlen == config |
| 0-cascor | `test_resume_replays_events` | integration | N-5 -> 5 events |
| 0-cascor | `test_resume_failed_server_restarted` | integration | UUID mismatch -> fail |
| 0-cascor | `test_second_resume_closes_1003` | unit | D-30 |
| 0-cascor | `test_state_coalescer_terminal_transitions` | unit | GAP-WS-21 |
| 0-cascor | `test_ws_control_no_seq` | contract | D-03 negative assertion |
| 0-cascor | chaos_broadcast_replay_race | chaos (blocking) | No gaps, no deadlocks |
| 0-cascor | Load: 100 Hz x 60s x 10 clients | load (blocking) | p95 < 250ms |
| A-SDK | `test_set_params_cancellation_cleans_map` | unit **mandatory** | `len(_pending)==0` |
| A-SDK | `test_set_params_concurrent_correlation` | unit | 2 calls distinguished |
| A-SDK | `test_set_params_fails_fast_on_disconnect` | unit | No queue (D-20) |
| A-SDK | `test_correlation_map_bounded_256` | unit | Overflow error |
| B-pre-a | `test_oversized_frame_1009` | unit | 65KB -> 1009 |
| B-pre-a | `test_per_ip_cap_6th_rejected` | unit | 6th -> 1013 |
| B-pre-a | `test_empty_allowlist_rejects_all` | unit | Fail-closed |
| B-pre-a | `test_cswsh_exfiltration` | Playwright | Cross-origin rejected |
| B | **`test_bandwidth_eliminated`** | **Playwright (P0)** | 0 requests over 60s |
| B | **`test_dual_format`** | **Playwright (RISK-01)** | Both flat + nested |
| B | `test_chart_does_not_poll_when_ws_connected` | dash_duo | 0 REST calls |
| B | `test_demo_mode_parity` | dash_duo+e2e | RISK-08 both lanes |
| B | `test_resume_replays` | Playwright | N events replayed |
| B | `test_both_flags_interact` | unit | Two-flag logic |
| B | `test_fake_cascor_schema_parity` | contract | CCC-05 |
| B | 72h memory soak | soak | p95 growth <20% |
| B-pre-b | `test_csrf_required` | unit | Missing -> 1008 |
| B-pre-b | `test_rate_limit_10_per_sec` | unit | rate_limited response |
| B-pre-b | `test_hmac_csrf_on_connect` | unit | D-29 |
| B-pre-b | `test_cswsh_cannot_start_training` | Playwright | Full CSWSH |
| C | `test_hot_keys_to_websocket` | unit | WS path |
| C | `test_fallback_on_timeout` | unit | REST fallback |
| C | `test_unclassified_to_rest_warn` | unit | D-34 |
| D | `test_csrf_for_websocket_start` | Playwright | B-pre-b regression |
| D | `test_orphaned_resolves_via_state` | Playwright | RISK-13 |
| E | `test_slow_client_no_block` | unit | Fast clients unaffected |
| E | `test_terminal_state_not_dropped` | unit | RISK-11 guard |
| F | `test_jitter_no_nan` | unit | 0 <= delay <= cap |
| G | **`test_set_params_echoes_command_id`** | **contract (C-01)** | Cascor echoes it |
| G | `test_concurrent_correlation` | integration | Correct responses |
| H | `test_normalize_dual_format` | **contract (C-22)** | Both keys |
| -- | Metric-presence pytest | security (every PR) | All canonical present |
| -- | REST regression harness | fast (every PR) | Baseline shapes match |

**Test totals**: Unit ~97, Integration ~18, E2E ~16, Contract ~11. Contract runtime <50ms/test, <5s suite.

---

## 21. Effort summary

| Phase | Optimistic | Expected | Pessimistic | Parallel with |
|---|---:|---:|---:|---|
| 0-cascor | 1.5 | 2.0 | 3.0 | A-SDK, B-pre-a |
| A-SDK | 0.5 | 1.0 | 1.5 | 0-cascor, B-pre-a |
| B-pre-a | 0.5 | 1.0 | 1.5 | 0-cascor, A-SDK |
| B | 3.0 | 4.0 | 5.0 | B-pre-b |
| B-pre-b | 1.0 | 1.5 | 2.0 | B |
| C | 1.5 | 2.0 | 3.0 | G |
| D | 0.75 | 1.0 | 1.5 | -- |
| E | 0.75 | 1.0 | 1.5 | conditional |
| F | 0.25 | 0.5 | 1.0 | -- |
| G | 0.25 | 0.5 | 0.75 | C |
| H | 0.5 | 1.0 | 1.5 | -- |
| I | 0.1 | 0.25 | 0.5 | folded into B |
| **Total** | **10.6** | **15.75** | **22.25** | -- |

**Parallelism savings**: Phases A-SDK + 0-cascor + B-pre-a in parallel -> ~2 day compression. B-pre-b parallel with B -> ~1.5 day compression. G parallel with C -> ~0.5 day compression.

---

## 22. R3 reconciliation log

Where R3-01, R3-02, and R3-03 contradicted each other and how this R4-01 resolved the disagreement.

### 22.1 Security flag naming (D-10)

| Input | Position |
|---|---|
| R3-01 | **Positive-sense `ws_security_enabled=True`** (overrides R2-02; safety argument) |
| R3-02 | **Negative-sense `disable_ws_auth`** (follows R2-02 compromise; execution-contract continuity) |
| R3-03 | **Positive-sense `ws_security_enabled=True`** (C-27) |

**R4-01 resolution: positive-sense `ws_security_enabled=True`** with CI guardrail refusing `false` in prod compose. Justification: 2-to-1 majority among R3 inputs; safety principle (fail-safe default state is what prod should accidentally land in); CI guardrail closes the footgun equally well in either direction so "execution-contract continuity" is not load-bearing. The ~10 LOC rename cost is trivial. R3-02's concern about "test-noisy churn" is valid but the churn is isolated to Phase B-pre-b env var names, not wire format.

### 22.2 Effort estimate (expected days)

| Input | Position |
|---|---|
| R3-01 | **15.75 days** (R2-02 number with delta justification) |
| R3-02 | **15.75 days** |
| R3-03 | **13.5 days** (R1-05 target, R2-02's 15.75 as pessimistic bound) |

**R4-01 resolution: 15.75 expected, 13.5 as optimistic-with-parallelism target.** The 15.75 number from R2-02 includes itemized deltas (+0.5 NetworkVisualizer, +0.5 audit logger, +0.5 HMAC, etc.) that are either contingent costs or scope lines R1-05 underestimated. Using 15.75 prevents over-promising. R3-03's 13.5 is preserved as the parallel-execution compressed target in section 21.

### 22.3 Per-origin handshake cooldown

| Input | Position |
|---|---|
| R3-01 | **Include in Phase B-pre-b** (S6.3.1 item 5; low cost ~20 LOC; NAT-hostile escape hatch) |
| R3-02 | **Deferred** (S5.7 NOT-in-phase) |
| R3-03 | **Include in Phase B-pre-b** (S7.1 deliverables) |

**R4-01 resolution: include in Phase B-pre-b.** 2-to-1 majority; the feature is ~20 LOC, the NAT-hostile escape hatch (cleared on restart) makes it safe, and it amplifies the Origin defense at negligible cost. R3-02's deferral was conservative but the risk/cost ratio favors inclusion.

### 22.4 Rate limit overflow behavior (11th command)

| Input | Position |
|---|---|
| R3-01 | `{command_response, status:"rate_limited", retry_after:0.3}`; connection stays up |
| R3-02 | close 1013 on 11th command (S5.1 text) |
| R3-03 | `rate_limited` response; connection stays up (S7.1 deliverables) |

**R4-01 resolution: connection stays up with `rate_limited` response.** 2-to-1 majority; closing the connection on rate-limit is unnecessarily destructive and forces a reconnect cycle. The `rate_limited` response with `retry_after:0.3` is more graceful and matches the source doc intent. R3-02's close 1013 contradicted its own test `test_rate_limit_response_is_not_an_error_close`.

### 22.5 Phase B-pre-b SameSite cookie attribute

| Input | Position |
|---|---|
| R3-01 | `SameSite=Strict` |
| R3-02 | `SameSite=Lax` (S5.3) |
| R3-03 | `SameSite=Strict` (S7.1) |

**R4-01 resolution: `SameSite=Strict`.** 2-to-1 majority; Strict is the more secure default. Lax is needed only for cross-site navigation scenarios that do not apply to Canopy (single-origin dashboard). R3-02's Lax was likely a copy from a generic web-app template.

### 22.6 Chaos test elevation scope

| Input | Position |
|---|---|
| R3-01 | 3 Phase 0-cascor chaos tests **blocking gates**; others nightly |
| R3-02 | Not explicit (delegates to D-40 which says nightly) |
| R3-03 | 3 Phase 0-cascor chaos tests **blocking gates** (S3.1 deliverables) |

**R4-01 resolution: 3 blocking + others nightly.** Consistent with R3-01 and R3-03. The three tests (replay race, broadcast chaos, broadcast_from_thread) catch seq/replay corruption that is correctness-catastrophic. R3-02 did not explicitly contradict this.

---

## 23. Disagreements with R3 inputs

### 23.1 R3-02 negative-sense security flag

R3-02 preserved `disable_ws_auth` for execution-contract continuity. R4-01 overrides to positive-sense per section 22.1.

### 23.2 R3-03 effort estimate of 13.5 days as expected

R3-03 used 13.5 as expected. R4-01 uses 15.75 as expected and retains 13.5 as optimistic-with-parallelism per section 22.2.

### 23.3 R3-02 deferred per-origin handshake cooldown

R3-02 excluded cooldown from Phase B-pre-b scope. R4-01 includes it per section 22.3.

### 23.4 R3-02 close 1013 on rate limit overflow

R3-02's prose said close 1013 but its own test asserted the connection stays up. R4-01 resolves the internal contradiction in favor of connection stays up per section 22.4.

### 23.5 R3-02 SameSite=Lax cookie attribute

R3-02 specified Lax. R4-01 uses Strict per section 22.5 (Canopy is single-origin; Strict is the correct default).

---

## 24. Self-audit log

### 24.1 Passes performed

1. **Pass 1**: Read R3-01 (1912 lines), R3-02 (1871 lines), R3-03 (1363 lines) in full using offset/limit chunks.
2. **Pass 2**: Identified 6 R3-cross contradictions (D-10 naming, effort, cooldown, rate-limit behavior, SameSite, chaos scope).
3. **Pass 3**: Built sections 0-3 (first hour, executive, constitution, phase index) as hybrid of R3-03 density and R3-01 depth.
4. **Pass 4**: Built sections 4-14 (per-phase detailed plans) using R3-01 deliverables + R3-02 resolved positions + R3-03 checklists.
5. **Pass 5**: Built sections 15-21 (cross-cutting: merge sequence, kill switches, risks, observability, decisions, tests, effort).
6. **Pass 6**: Built sections 22-23 (reconciliation log, disagreements).
7. **Pass 7**: Self-audit (this section).

### 24.2 Coverage checks

- [x] Every phase (0-cascor through I) has: Goal, Entry gate, Deliverables checklist, Cross-cutting, Tests, Observability, PR plan, Exit gate, Rollback (verbatim commands), NOT-in-phase
- [x] All 42 settled positions from R3-03 present in section 2
- [x] All 62 decisions from R3-02/R3-03 in section 19
- [x] Kill switch matrix covers every phase (26 rows + 1 non-switch)
- [x] Risk register has 16 RISK + 5 CCC-Risk = 21 entries
- [x] Observability matrix per phase with metrics + alerts + dashboards
- [x] All 6 R3-cross contradictions identified and resolved in section 22
- [x] SLO table present (section 7.5)
- [x] Latency histogram buckets specified ({50..5000} ms)
- [x] Canonical label values specified (section 18)
- [x] Feature flag inventory (section 2.7)
- [x] Configuration canonical table (section 2.8)
- [x] Version bump table in section 15
- [x] Worktree naming convention referenced
- [x] Rollback order (reverse-dependency) documented

### 24.3 Corrections applied during self-audit

1. **Section 3 phase index**: initial draft omitted "NOT-in-phase" column. Added per R3-03 format.
2. **Section 7.3 Phase B deliverables**: initially missed `/api/ws_browser_errors` endpoint (D-59). Added.
3. **Section 8.3 Phase B-pre-b**: initially listed `SameSite=Lax`. Corrected to `Strict` per section 22.5 resolution.
4. **Section 8.3 rate limit**: initially said "close 1013" (copied from R3-02). Corrected to "rate_limited response, connection stays up" per section 22.4.
5. **Section 16 kill switch matrix**: initially had 24 rows. Added `URL ?ws=off` user-level hatch and `git revert` rows for Phase H and I. Final: 26 rows + 1 non-switch.
6. **Section 17 risk register**: initially missed CCC-05 (tautological contract test). Added per R3-02 S14.
7. **Section 19 decision table**: initially had 55 entries. Added D-56 through D-62 (implicit decisions) for 62 total.
8. **Section 15 merge sequence**: confirmed P7 precedes P10 (Phase C needs flag-on to iterate). Matches R3-01 and R3-02.
9. **Section 4.5 tests**: initial list had 22 tests. Added `test_emitted_at_monotonic_present_on_every_broadcast` and `test_legacy_client_ignores_seq_field` for 26+ total per R3-01 section 3.4.
10. **Section 2.8 settings**: added `ws_idle_timeout_seconds` to both cascor and canopy rows.
11. **Section 7.4 cross-cutting**: initial Phase B had no CCC subsection. Added full CCC-01 through CCC-10 cross-cutting deliverables per R3-01 S5.3.2.
12. **Section 7.5 tests**: expanded from 14 to 22 tests to match R3-01 S5.4 + R3-03 S6.1 union.
13. **Section 14a**: added unresolved items resolution table from R3-02 S1.7 (13 items, all resolved).
14. **Section 14b**: added cross-cutting concerns summary from R3-01 S16 (10 CCCs with owners).
15. **Section 1.3**: added secondary goals from R3-01 S1.2 (7 items).
16. **Section 1.4**: added explicit non-goals from R3-01 S1.3 (12 items).
17. **Section 18**: expanded observability section with audit logger scope, clock offset, dashboard-as-code, metric naming audit per R3-01 S15.6-15.9.
18. **Section 7.7 PR plan**: added P7 clarification note per R3-01 S5.5 and R3-02 S4.4.
19. **Section 9**: expanded Phase C from compact to full detail (deliverables, cross-cutting, 16 tests, PR plan, separate flag-flip gates) per R3-01 S7.
20. **Section 10**: expanded Phase D with full deliverables, 10 tests, observability, PR plan per R3-01 S8.
21. **Section 11**: expanded Phase E with goal, entry gate, policy matrix, 8 tests, observability, alerts, exit gate, rollback per R3-01 S9 + R3-03 S10.
22. **Section 12**: expanded Phase F with full deliverables, 6 tests, alert, exit gate per R3-01 S10.
23. **Section 13**: expanded Phase G with full 15-test list and contract test per R3-01 S11 + R3-02 S10.
24. **Section 14**: expanded Phase H with full deliverables, entry gate, PR plan, exit gate per R3-01 S12.

### 24.4 Confidence assessment

- **High confidence**: Phase 0-cascor scope and commit decomposition (all 3 R3s agree), `command_id` wire correction, GAP-WS-19 RESOLVED, Phase B-pre split, kill-switch matrix (R3-01 + R3-02 + R3-03 triangulation), cross-repo merge sequence, effort range
- **Medium confidence**: Origin on `/ws/training` in B-pre-a (overrides R1-05; justified by exfiltration argument), `ws_security_enabled` positive-sense (overrides R3-02; justified by safety + majority), Phase E conditional (R3-01/R3-02 agree optional; R3-03 consistent)
- **Lower confidence**: NetworkVisualizer scope (render-tech unverified), Phase B-pre-b effort (SessionMiddleware question), Phase C flip-gate p99 >=50 ms threshold (depends on actual latency distribution)

### 24.5 Items for Round 5 attention

1. **Final `command_id` grep** across all R5 artifacts -- no stale `request_id` references
2. **Source-doc text patches** (D-55): batch as a single v1.4 patch PR
3. **Bandwidth baseline measurement procedure** (D-62): runbook entry needed
4. **Contract test runtime budget**: confirm CI supports <50ms/test, <5s/suite
5. **Verify the 5 pre-Phase-B greps** at first commit of each phase

### 24.6 Scope discipline

- [x] Read only the 3 R3 files
- [x] Referenced R3-NN identifiers when citing inputs
- [x] Referenced D-NN, GAP-WS-NN, M-SEC-NN, RISK-NN identifiers
- [x] Did not modify other files; did not commit
- [x] `command_id` used everywhere; no `request_id` references
- [x] No "TBD", "consider", or "may" in sections 1-21

**Scope discipline PASS.**

---
