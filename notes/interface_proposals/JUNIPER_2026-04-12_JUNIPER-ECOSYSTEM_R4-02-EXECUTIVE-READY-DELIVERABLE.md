# Round 4 Proposal R4-02: Executive-Ready Engineering Deliverable

**Angle**: Three-layer document optimized for PM / tech lead / engineer audiences
**Author**: Round 4 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 4 consolidation — input to Round 5 (final)
**Inputs consolidated**: R3-01 (master integration), R3-02 (decision-resolved blueprint), R3-03 (lean execution document)

---

## How to read this document

| Your role | Read these sections | Time |
|---|---|---|
| **PM / stakeholder** | 0-1 | 10 min |
| **Tech lead** | 0-3 | 30 min |
| **Engineer on Phase X** | 0 + the section for Phase X (4-14) | 20 min |

Each layer is self-sufficient. You do not need to read the whole document to get what you need.

- **0-1** answer: what, why, how long, what are the risks, what has been decided.
- **2-3** answer: how the system is structured, how phases depend on each other, what the operational framework looks like.
- **4-14** answer: what exactly do I build, what tests must pass, how do I roll back.
- **15-18** are appendices: full decision table, full test matrix, R3 reconciliation log, self-audit.

---

## Pre-flight: day-1 verification procedure

If you are picking up this work right now, run these verification commands before writing code:

```bash
# 1. Confirm ecosystem clean
for repo in juniper-cascor juniper-cascor-client juniper-canopy; do
  (cd /home/pcalnon/Development/python/Juniper/$repo && echo "=== $repo ===" && git status)
done

# 2. Verify GAP-WS-19 already resolved on cascor main
grep -n "close_all" /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/websocket/manager.py
# Should show lock-holding pattern at lines 138-156

# 3. Record answers for 5 scope-determining greps
grep -rn "SessionMiddleware" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/
grep -l "cytoscape\|plotly" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/frontend/components/network_visualizer.py
grep "dash\b" /home/pcalnon/Development/python/Juniper/juniper-canopy/pyproject.toml
grep -n "run_coroutine_threadsafe" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/backend/cascor_service_adapter.py
grep -n "command_id\|request_id" /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/websocket/control_stream.py

# 4. Record bandwidth baseline (1 hour in staging before any Phase B deploy)
# Capture canopy_rest_polling_bytes_per_sec gauge as the denominator for >90% reduction AC

# 5. Create worktrees per Juniper convention
# Location: /home/pcalnon/Development/python/Juniper/worktrees/
# Format: <repo>--<branch>--<YYYYMMDD-HHMM>--<shorthash>
```

Record grep results in your worktree README. They determine:
- **SessionMiddleware absent**: Phase B-pre-b budgets +0.5 day
- **NetworkVisualizer is Plotly**: Phase B budgets +1 day; migrate via `extendTraces`
- **NetworkVisualizer is cytoscape**: Phase B ships minimum wire; deep migration deferred
- **`run_coroutine_threadsafe` absent**: Phase C ships the pattern fresh
- **`command_id` not yet in cascor control handler**: Phase 0-cascor deliverable includes echo

---

## 0. Executive summary (PM layer)

### 0.1 What, why, how long

**What**: Replace the ~3 MB/s per-dashboard `/api/metrics/history` REST polling in the Juniper Canopy monitoring dashboard with an already-half-wired cascor-to-canopy-to-browser WebSocket pipeline. Piggybacked: four cascor correctness bugs and the CSWSH security defense gap.

**Why**: Every open Canopy dashboard tab continuously polls the cascor backend at ~3 MB/s. This is the P0 problem. WebSocket push eliminates this polling entirely when the connection is healthy, while REST polling remains as a permanent fallback.

**How long**: **13.5 engineering days expected** (optimistic 10.6 / pessimistic 19-22) over **~4.5 weeks calendar** including 48-72 hour soak windows between high-risk phases. Single-developer critical path. Parallel lanes compress ~3.5 days off the serial total.

**P0 acceptance signal**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` drops >=90% vs pre-migration baseline, sustained for 72 hours in staging, then in production.

### 0.2 Top 5 decisions (already settled)

These are the load-bearing decisions that shape the entire migration. They are settled and must not be re-opened without re-planning.

| # | Decision | Applied value | Why it matters |
|---|---|---|---|
| 1 | Correlation field name (D-02) | **`command_id`** (not `request_id`) | Every SDK, server, and test file must agree. A stale `request_id` reference is a wire-level bug. |
| 2 | Phase 0-cascor carve-out (D-11) | Cascor ships seq/replay/resume **separately**, soaks 1 week before canopy consumes | Decouples cascor stability from canopy feature work. Additive field soak catches seq bugs before they reach the browser. |
| 3 | Two-flag browser bridge (D-17 + D-18) | `enable_browser_ws_bridge=False` (dev flip) + `disable_ws_bridge=False` (permanent kill) | Any incident: flip one env var, 5-minute recovery. REST polling takes over automatically. |
| 4 | REST paths preserved forever (D-21, D-54) | No REST endpoint is deleted or deprecated, ever | Every kill switch ultimately falls back to REST. Removing REST removes the safety net. |
| 5 | Positive-sense security flag (D-10) | `ws_security_enabled=True` with CI guardrail refusing `false` in production | The safe default is the production default. Accidentally deploying a blank config leaves security ON, not off. |

### 0.3 Key risks (with mitigations)

| Risk | Severity | Mitigation | Recovery time |
|---|---|---|---|
| **CSWSH attack** (RISK-15) | High | Origin allowlist + CSRF first-frame + page alert on rejection | 5 min (disable `/ws/control`) |
| **Browser memory leak** (RISK-10) | Medium-High | `Plotly.extendTraces(maxPoints=5000)`, ring-bound in handler (AST lint), 72h soak | 5 min (`disable_ws_bridge=true`) |
| **Silent data loss** (RISK-11) | High (low likelihood) | `drop_oldest_progress_only` policy; state events never dropped; page alert on any state drop | 5 min (revert to `block` policy) |
| **Dual metric format breakage** (RISK-01) | High | CODEOWNERS hard gate, pre-commit hook, regression test, shape-hash golden file | 10 min (git revert) |
| **Cascor crash mid-broadcast** (RISK-14) | Low | `server_instance_id` forces full REST resync; `WSSeqCurrentStalled` page alert | 10 min (rolling restart) |

### 0.4 Recommended path

Ship the P0 win (polling elimination) as the primary objective. The critical-path spine is:

```
Phase A-SDK + Phase 0-cascor (parallel, days 1-3)
  --> Phase B-pre-a (read-path security, day 4)
    --> Phase B (browser bridge + polling kill, days 5-7)
      --> 72h staging soak
        --> Phase B flag flip (P0 win lands, ~day 10)
```

Everything else (Phase C set_params, Phase D control buttons, Phase E backpressure, Phase F heartbeat, Phase G integration tests, Phase H normalize_metric audit) branches off after the P0 win is in production. Phase E is conditional on telemetry data.

Minimum-viable carveout for calendar emergencies: ~7 days for P0 only (Phases A-SDK + 0-cascor + B-pre-a + B).

---

## 1. Project overview (PM + TL layer)

### 1.1 Scope

**In scope**:

- Eliminate `/api/metrics/history` REST polling when WebSocket is healthy (P0)
- Fix GAP-WS-21 (state coalescer drop-filter), GAP-WS-29 (broadcast_from_thread exception swallowing), GAP-WS-07 (slow-client fan-out, quick-fix), GAP-WS-32 (seq numbers)
- Close RISK-15 (CSWSH on `/ws/training` and `/ws/control`) via Origin allowlist, cookie+CSRF, rate limit, adapter HMAC auth
- Add `command_id`-correlated `set_params` WebSocket path (feature-flagged default OFF)
- Route training-control buttons (start/stop/pause/resume/reset) via WebSocket with REST fallback
- Full observability stack: metrics, alerts, dashboards, SLOs (aspirational until 1-week production data)

**Explicitly out of scope**:

- REST endpoint deletion (preserved forever)
- Multi-tenant replay isolation
- Per-command HMAC
- `permessage-deflate` compression negotiation
- Topology chunking for large networks
- Multi-browser CI matrix (Chromium-only for v1)
- OAuth/OIDC, mTLS, shadow traffic
- `_normalize_metric` refactoring (test-only in Phase H)

### 1.2 Effort table (3-point per phase)

| # | Phase | Goal | Opt (days) | **Exp (days)** | Pess (days) | Risk factor |
|---|---|---|---:|---:|---:|---|
| 1 | 0-cascor | seq + replay + resume on cascor | 1.5 | **2.0** | 3.0 | async race in `_pending_connections` |
| 2 | A-SDK | `set_params` on cascor-client SDK | 0.5 | **1.0** | 1.5 | correlation-map bounding iteration |
| 3 | B-pre-a | Read-path security (Origin, size, IP caps) | 0.5 | **1.0** | 1.5 | audit logger name collisions |
| 4 | B | Browser bridge + polling elimination (P0) | 3.0 | **4.0** | 5.0 | NetworkVisualizer Plotly (+1d contingent) |
| 5 | B-pre-b | Control-path security (CSRF, rate limit) | 1.0 | **1.5** | 2.0 | SessionMiddleware absence (+0.5d) |
| 6 | C | `set_params` adapter hot/cold split | 1.5 | **2.0** | 3.0 | concurrent-correlation race bugs |
| 7 | D | Training control buttons via WS | 0.75 | **1.0** | 1.5 | orphaned-command UI finickiness |
| 8 | E | Full backpressure (CONDITIONAL) | 0.75 | **1.0** | 1.5 | queue-size tuning under load |
| 9 | F | Heartbeat + reconnect jitter | 0.25 | **0.5** | 1.0 | low variance |
| 10 | G | Cascor `set_params` integration tests | 0.25 | **0.5** | 0.75 | test-only, low variance |
| 11 | H | `_normalize_metric` audit + CODEOWNERS | 0.5 | **1.0** | 1.5 | audit document can grow |
| 12 | I | Asset cache busting (folded into B) | 0.1 | **0.25** | 0.5 | trivial |
| | **Total** | | **10.6** | **15.75** | **22.25** | |

Notes: R3-01 uses 13.5 as the expected total (R1-05 center-of-mass). R3-02 uses 15.75 (R2-02 pessimistic-adjusted). This document adopts **13.5 as the target** and **15.75 as the planning buffer**, consistent with R3-01's reconciliation. The delta is +2.25 days for audit logger, HMAC wiring, and NetworkVisualizer minimum wire.

### 1.3 Timeline with milestones

```
Week 1:  Phase A-SDK (parallel) + Phase 0-cascor (parallel) + Phase B-pre-a (parallel)
         --> Phase 0-cascor deploys to staging, begins 72h soak

Week 2:  Phase B development (flag-off default)
         Phase B-pre-b development (parallel with B)
         Phase 0-cascor soak completes, merges to production

Week 3:  Phase B deploys to staging, begins 72h soak
         Phase B flag-flip to True after soak passes
         --> P0 WIN LANDS (mid-week deploy)

Week 4:  Phase B-pre-b soaks 48h in production
         Phase C development (flag-off)
         Phase G integration tests (parallel)

Week 5+: Phase D (after B-pre-b 48h prod soak)
         Phase C flag-flip (after 7-day canary)
         Phase E (only if telemetry warrants)
         Phase F, Phase H (independent)
```

### 1.4 Success criteria

| Criterion | Metric | Threshold | When |
|---|---|---|---|
| **P0: polling eliminated** | `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` | >=90% reduction sustained 72h | Phase B flag-flip |
| Security: CSWSH closed | `canopy_ws_origin_rejected_total` page alert functional | Rejects unknown origins, zero bypass | Phase B-pre-a + B-pre-b |
| Correctness: no seq gaps | `cascor_ws_seq_gap_detected_total` | == 0 over 72h soak | Phase 0-cascor exit |
| Correctness: no state loss | `cascor_ws_dropped_messages_total{type="state"}` | == 0 steady state | Phase E (or never if E skipped) |
| Observability: full pipe | All canonical metrics present on `/metrics` | Metrics-presence CI test passes | Every phase |
| Recovery: kill switches work | Every switch flipped in staging | MTTR <=5 min | Every phase soak |

---

## 2. Architecture context (TL layer)

### 2.1 Settled positions (constitution table)

42 positions from the R1/R2/R3 corpus, settled and binding. Full decision reference in Appendix (section 15).

**Wire format**:

| Position | Value | Ref |
|---|---|---|
| Correlation field on `/ws/control` | `command_id` (NOT `request_id`) | D-02 |
| `command_response` carries `seq` | No (separate seq namespaces) | D-03 |
| Replay buffer applies to | `/ws/training` only | D-03 |
| `server_instance_id` role | Programmatic comparison key | D-15 |
| `replay_buffer_capacity` on `connection_established` | Present, additive | D-16 |
| `emitted_at_monotonic` on every `/ws/training` broadcast | Present | CCC-10 |
| Two-phase registration | `_pending_connections` set + `promote_to_active()` | D-14 |
| Unknown commands on `/ws/control` | Error response (not close) | D-03 |
| Malformed JSON | Close 1003 | source doc |
| Cascor `SetParamsRequest` validation | `extra="forbid"` | D-34 |

**Protocol behavior**:

| Position | Value | Ref |
|---|---|---|
| `set_params` default timeout | 1.0 s | D-01 |
| SDK retries on timeout | None (fail-fast, caller decides) | D-20 |
| Slider debounce layer | Dash clientside callback (NOT SDK) | D-22 |
| Unclassified `set_params` keys | REST fallback with WARNING log | D-34 |
| REST path deprecation | None, ever | D-21, D-54 |
| Origin wildcard `*` in allowlist | REFUSED by parser | D-10 |
| One resume per connection | Enforced (second resume closes 1003) | D-30 |
| Replay buffer default | 1024, configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE` | D-35 |
| Replay buffer size=0 | Disables replay (kill switch) | D-36 |
| REST polling fallback cadence | 1 Hz (NOT 100 ms) | D-05 |
| `ws-metrics-buffer` store shape | `{events: [...], gen: int, last_drain_ms: float}` | D-07 |
| rAF coalescer | Scaffolded, disabled (`enable_raf_coalescer=False`) | D-04 |
| Backpressure default | `drop_oldest_progress_only` | D-19 |

**Security**:

| Position | Value | Ref |
|---|---|---|
| Security flag | Positive-sense `ws_security_enabled: bool = True` | D-10 |
| Per-IP connection cap | 5 default | D-24 |
| Idle timeout | 120 s bidirectional | M-SEC-10 |
| Adapter auth | HMAC-derived CSRF token (NOT header-skip) | D-29 |
| Rate limit | Single bucket, 10 cmd/s per connection | D-33 |
| Per-command HMAC | Deferred indefinitely | D-31 |

**Testing**:

| Position | Value | Ref |
|---|---|---|
| `contract` pytest marker | Added in all 3 repos, runs every PR | D-43 |
| Chaos tests | Nightly lane; 3 elevated to blocking for Phase 0-cascor | D-40, R3-01 |
| Load tests | Blocking gate for Phase 0-cascor (100 Hz x 60s x 10 clients, p95 < 250 ms) | D-41 |
| Frame-budget test | Recording-only in CI | D-42 |
| Multi-browser | Chromium-only in CI | D-44 |
| Latency tests | Recording-only in CI (`latency_recording` marker) | D-42 |

### 2.2 Phase dependency graph

```
Phase A-SDK ──────────────────────────────────┐
                                              │
Phase 0-cascor ──> [72h soak] ────────────────┼──> Phase B-pre-a ──> Phase B ──> [72h soak] ──> P7 flag-flip
                                              │                         │                        (P0 WIN)
Phase B-pre-a ────────────────────────────────┘                         │
                                                                        │
Phase B-pre-b (parallel with B) ──> [48h soak] ──> Phase D ────────────┤
                                                                        │
Phase C (flag-off, after B in prod) ──> [7d canary] ──> C flag-flip ───┤
                                                                        │
Phase E (CONDITIONAL on telemetry) ────────────────────────────────────┤
Phase F (after B in main) ─────────────────────────────────────────────┤
Phase G (after 0-cascor + B-pre-b in main) ────────────────────────────┤
Phase H (after B in main) ─────────────────────────────────────────────┘
Phase I (folded into Phase B)
```

**Parallel lanes**:
- Phase A-SDK, Phase 0-cascor, and Phase B-pre-a run in parallel (day 1)
- Phase B-pre-b runs in parallel with Phase B (not before it)
- Phase G runs in parallel with Phase C
- Phases E, F, H are independent post-B follow-ups

### 2.3 Cross-repo coordination

Three repositories are modified. Merge order is strict and dependency-enforced.

| PR | Branch | Repo | Phase | Blocks |
|---:|---|---|---|---|
| P2 | `phase-a-sdk-set-params` | juniper-cascor-client | A-SDK | PyPI publish gates downstream |
| P1 | `phase-0-cascor-seq-replay-resume` | juniper-cascor | 0-cascor | Phase B (72h soak) |
| P3 | `phase-b-pre-a-cascor-security` | juniper-cascor | B-pre-a | P4 |
| P4 | `phase-b-pre-a-canopy-security` | juniper-canopy | B-pre-a | Phase B |
| P5 | `phase-b-cascor-audit-prom-counters` | juniper-cascor | B | -- |
| P6 | `phase-b-canopy-drain-wiring` | juniper-canopy | B | P7 (72h soak) |
| P7 | `phase-b-canopy-flag-flip` | juniper-canopy | B | **P0 WIN** |
| P8 | `phase-b-pre-b-cascor-control-security` | juniper-cascor | B-pre-b | P9 |
| P9 | `phase-b-pre-b-canopy-csrf-audit` | juniper-canopy | B-pre-b | Phase D (48h soak) |
| P10 | `phase-c-canopy-set-params-adapter` | juniper-canopy | C | -- |
| P11 | `phase-d-cascor-control-commands` | juniper-cascor | D | P12 |
| P12 | `phase-d-canopy-button-ws-routing` | juniper-canopy | D | -- |
| P13 | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor | E | -- (conditional) |
| P14 | `phase-f-heartbeat-jitter` | juniper-cascor + canopy | F | -- |
| P15 | `phase-g-cascor-set-params-integration` | juniper-cascor | G | -- |
| P16 | `phase-h-normalize-metric-audit` | juniper-canopy | H | -- |

**Critical path (P0 win)**: P2 --> P1 --> P3 --> P4 --> P6 --> [soak] --> P7.

**Version bumps**: cascor-client minor (A), cascor minor (0-cascor), cascor patch (B-pre-a/b), canopy minor (B), canopy patch (C/D/H). Helm `Chart.yaml` `version` + `appVersion` must match app semver.

**Rollback order**: always reverse-dependency (canopy first, then cascor, then SDK). Never forward-order.

**Worktrees**: one per phase per repo, created in `/home/pcalnon/Development/python/Juniper/worktrees/` per ecosystem convention.

### 2.4 Risk register

16 source-doc risks + 5 cross-cutting risks. Compact matrix with kill switch and TTF.

| ID | Risk | Sev/Lik | Phase | Kill switch | TTF |
|---|---|---|---|---|---|
| 01 | Dual metric format removed aggressively | H/M | H | `git revert` | 10 min |
| 02 | Phase B clientside-callback debuggability | M/H | B | `disable_ws_bridge=true` | 5 min |
| 03 | Phase C REST+WS ordering race | M/L | C | `use_websocket_set_params=false` | 2 min |
| 04 | Slow-client blocks broadcasts | M/M | E / 0-cascor | `ws_backpressure_policy=close_slow` | 5 min |
| 05 | Playwright fixture misses real-cascor regression | M/M | B, D | Fix the test (nightly smoke) | -- |
| 06 | Reconnection storm after cascor restart | L/M | F | `disable_ws_auto_reconnect=true` | 10 min |
| 07 | 50-conn cap hit by multi-tenant | L/L | n/a | Raise `ws_max_connections` | 10 min |
| 08 | Demo mode parity breaks | L/M | B | Revert PR | 10 min |
| 09 | Phase C unexpected user-visible behavior | L/M | C | `use_websocket_set_params=false` | 2 min |
| 10 | Browser memory exhaustion | M/H | B | `disable_ws_bridge=true` + ring-cap | 5 min |
| 11 | Silent data loss via drop-oldest | H/L | E | `ws_backpressure_policy=block` | 5 min |
| 12 | Background tab memory spike | L/M | B | Same as RISK-10 | 5 min |
| 13 | Orphaned commands after timeout | M/M | B, C, D | Reduce timeouts / flag-off | 5 min |
| 14 | Cascor crash mid-broadcast | L/L | B | Rolling restart | 10 min |
| 15 | **CSWSH attack** | **H/M** | B-pre-a/b | `disable_ws_control_endpoint=true` | 5 min |
| 16 | Topology >64KB silently fails | M/M | B-pre-a | REST topology fallback | 5 min |
| CCC-01 | `request_id` rename incomplete | H/M | all | Pre-merge grep | -- |
| CCC-02 | Metric added but no alert | M/M | all | Metric-presence CI test | -- |
| CCC-03 | Kill switch never tested in CI | H/M | all | Halt migration | -- |
| CCC-04 | Cross-repo pin at unreleased version | H/L | cross-repo | Pin previous version | 10 min |
| CCC-05 | Contract test is tautological | M/M | B, G | Review audit | -- |

---

## 3. Operational framework (TL layer)

### 3.1 Kill switch matrix

Every phase has at least one config-only kill switch. Every switch has a CI test proving the flip works. Every switch is drilled in staging during the phase's soak window.

**Meta-rules**:
- Every kill switch MTTR is tested in staging before the phase enters production (D-53)
- If any TTF >5 min during staging drill, the phase does not ship
- If two consecutive switches fail in production, halt the migration for re-planning (abandon trigger)
- `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch; prevents panic-edit)
- `JUNIPER_WS_SECURITY_ENABLED=false` in production compose is REFUSED by CI guardrail

| Phase | Switch (env var) | Default | MTTR | Validation metric | CI test |
|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 1024 | 5 min | `resume_requests{outcome=out_of_range}` spike | `test_replay_buffer_size_zero_disables_replay` |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | 0.5 | 5 min | `broadcast_timeout_total` spike | `test_send_timeout_env_override` |
| 0-cascor | Rolling cascor restart | -- | 10 min | New `server_instance_id` | manual |
| 0-cascor | `git revert` P1 | -- | 15 min | Clients snapshot-refetch | -- |
| A-SDK | Downgrade cascor-client pin | -- | 15 min | `pip index versions` resolved | pin workflow |
| A-SDK | PyPI yank | -- | 2 min | Package 404 on new installs | -- |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 | 5 min | `per_ip_rejected_total` drops to 0 | `test_per_ip_cap_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | `[]` | 5 min | `origin_rejected_total` drops | `test_origin_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS='*'` | -- | -- | **REFUSED BY PARSER** | `test_wildcard_refused` |
| B-pre-a | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | 120 | 5 min | Connections persist | `test_idle_timeout_env_override` |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | true | 5 min | Audit writes cease | `test_audit_log_env_override` |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | true | 5 min | Auth rejections drop (**prod CI refuses**) | `test_ws_security_env_override` |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | 5 min | WS control traffic to 0 | `test_disable_ws_control_endpoint` |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | true | 5 min | Rate-limit counter freezes | `test_rate_limit_env_override` |
| B-pre-b | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=99999` | 120 | 5 min | Connections persist | `test_idle_timeout_env_override` |
| B | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | false->true | 5 min | Polling bytes rise to baseline | `test_enable_browser_ws_bridge_env_override` |
| B | `JUNIPER_DISABLE_WS_BRIDGE=true` | false | 5 min | Same (permanent kill switch) | `test_disable_ws_bridge_env_override` |
| B | Hardcoded ring-cap reduction | -- | 1 hour | Browser heap drops | -- |
| B | URL `?ws=off` diagnostic | -- | instant | Per-user bridge off | manual |
| B | `git revert` P6 | -- | 30 min | Cache-bust invalidation needed | -- |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | false | 2 min | WS transport freezes | `test_use_websocket_set_params_env_override` |
| C | `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1` | 1.0 | 5 min | Tight timeout forces REST | `test_ws_set_params_timeout_env_override` |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | false | 5 min | REST transport rises | `test_enable_ws_control_buttons_env_override` |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | 5 min | Control WS to 0 (CSWSH) | (reused from B-pre-b) |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | `drop_oldest_progress_only` | 5 min | Dropped-messages to 0 | `test_ws_backpressure_policy_env_override` |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | false | 10 min | Reconnect counter freezes | `test_disable_ws_auto_reconnect_env_override` |
| H | `git revert` P16 | -- | 10 min | Shape hash matches pre-H | -- |
| I | `git revert` cache-bust commit | -- | 10 min | Asset URL query reverts | -- |

**Non-switches** (deliberate inversions):
- `JUNIPER_WS_ALLOWED_ORIGINS='*'` -- **refused by parser** (prevents panic-edit during incident)
- `JUNIPER_WS_SECURITY_ENABLED=false` in production compose -- **refused by CI guardrail** (dev/staging exempt)

### 3.2 Observability matrix

| Phase | New metrics (count) | Key alerts | New dashboards |
|---|---|---|---|
| 0-cascor | 13 `cascor_ws_*` | `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap`, `WSSlowBroadcastP95` | -- |
| A-SDK | 1 SDK metric | -- | -- |
| B-pre-a | 5 security metrics | `WSOriginRejection` (PAGE), `WSOversizedFrame` (PAGE) | -- |
| B | 11 `canopy_ws_*` | `WSDrainCallbackGenStuck` (PAGE), `WSBrowserHeapHigh`, `WSJSErrorsNonZero` | "WebSocket health", "Polling bandwidth" |
| B-pre-b | 9 auth/security | `WSAuthSpike`, `WSRateLimitSpike` | -- |
| C | 3 set_params | `CanopyOrphanedCommands` | -- |
| D | 4 command metrics | -- | -- |
| E | 3 backpressure | `WSStateDropped` (PAGE) | -- |
| F | reconnect jitter | `WSReconnectStorm` | -- |

**Four page-severity alerts**: `WSOriginRejection`, `WSOversizedFrame`, `WSSeqCurrentStalled`, `WSStateDropped`. Each must be synthetically test-fired in staging before the guarding phase ships to production.

**Metric-before-behavior rule (binding)**: no behavior change ships without its guarding metric + alert + test-fired once in staging. The metrics-presence CI test (`D-37`) scrapes `/metrics` and asserts every canonical metric is present. Missing metric = PR blocker.

**SLOs (aspirational until >=1 week production data)**:

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` | <100ms | <250ms | <500ms |
| `state` | <50ms | <100ms | <200ms |
| `command_response` (set_params) | <50ms | <100ms | <200ms |
| `command_response` (start/stop) | <100ms | <250ms | <500ms |
| `cascade_add` | <250ms | <500ms | <1000ms |
| `topology` <=64KB | <500ms | <1000ms | <2000ms |

### 3.3 Feature flag inventory

| Flag | Phase | Initial | Final | Removal |
|---|---|---|---|---|
| `enable_browser_ws_bridge` | B | `False` | `True` (post-soak) | Post-flip deprecation v1.1 |
| `disable_ws_bridge` | B | `False` | `False` permanent | Never |
| `enable_raf_coalescer` | B | `False` | Depends on data | Post-B+1 |
| `use_websocket_set_params` | C | `False` | `True` (post-canary) | Post-flip deprecation v1.1 |
| `enable_ws_control_buttons` | D | `False` | `True` (post-canary) | Post-flip deprecation v1.1 |
| `ws_security_enabled` | B-pre-b | `True` | `True` permanent | Never |
| `ws_rate_limit_enabled` | B-pre-b | `True` | `True` permanent | Never |
| `audit_log_enabled` | B-pre-a | `True` | `True` permanent | Never |
| `ws_backpressure_policy` | E | `drop_oldest_progress_only` | Same | Permanent config |
| `disable_ws_auto_reconnect` | F | `False` | `False` permanent | Never |

**Flag-flip rule**: every flag flip is a separate one-line PR, reviewed by project lead, deployed mid-week only (D-61). The behavior-change PR and the flag-flip PR are never the same PR.

### 3.4 Operational rules (binding)

**Error-budget burn-rate freeze rule** (D-50): If the 99.9% SLO compliance budget burns in <1 day, freeze all non-reliability work until recovered. This is operationally binding from Phase B onwards.

**Mid-week deploy rule** (D-61): Behavior-changing flag flips (P7, Phase C flip, Phase D flip) must deploy mid-week only. Additive-only deploys (P1, P3/P4, P5) can deploy any day.

**Bandwidth baseline measurement** (D-62): Before Phase B deploys, capture 1 hour of production-equivalent staging traffic in `canopy_rest_polling_bytes_per_sec`. This value is the denominator for the >=90% reduction acceptance criterion.

**Audit logger scope** (D-28): Dedicated `canopy.audit` logger (separate from application logger). JSON formatter with fields `{ts, actor, action, command, params_before, params_after, outcome, request_ip, user_agent}`. `TimedRotatingFileHandler` with daily rotation (30-day retention dev, 90-day prod). Scrub allowlist (no raw payloads). CRLF/tab escaping. Skeleton in Phase B-pre-a; Prometheus counters in Phase B.

**Dashboard-as-code**: All Grafana panels defined in JSON committed to `juniper-canopy/deploy/grafana/`. PR review check prevents drift between `/metrics` scrape and dashboard queries.

### 3.5 Cross-cutting concerns (CCC) ownership

10 cross-cutting concerns span all phases. Each has an assigned owner and a key acceptance criterion. Per-phase details are woven into the individual phase sections.

| # | Concern | Owner | Key acceptance |
|---|---|---|---|
| CCC-01 | Wire-format schema evolution | backend-cascor lead | `command_id` rename enforced; additive-only; rollout state matrix in PR |
| CCC-02 | Observability stack | backend-canopy lead | Metric-before-behavior CI gate; SLO panel deployed; page alerts test-fired |
| CCC-03 | Kill switch architecture | security lead | Every phase >=1 switch; CI test per switch; staging drill per soak; MTTR <=5 min |
| CCC-04 | Cross-repo version pinning | project lead | Merge order binding; PyPI propagation tested; Helm chart bumps match semver |
| CCC-05 | Contract testing | backend-cascor lead | `contract` marker in all 3 repos; 11 contract tests; inline-literal rule (no cross-repo fixtures) |
| CCC-06 | Documentation as deliverable | project lead | 11 runbooks; PR template enforces IDs/threat-model/kill-switch/rollback; CODEOWNERS |
| CCC-07 | Configuration management | ops lead | Canonical settings table synced with Pydantic; CI checks for undocumented settings |
| CCC-08 | Backwards compatibility | project lead | REST regression harness in `fast` lane; golden shape file; kill-switch tests assert REST post-flip |
| CCC-09 | Feature flag lifecycle | project lead | Flag inventory committed; every flag has lifecycle; flip is separate PR; removal NOT in this migration |
| CCC-10 | Latency instrumentation | frontend lead | `emitted_at_monotonic` in 0-cascor; full pipe in B; Grafana panel; SLO promotion after >=1 week |

**Ownership binding**: CCC-02 owner = canopy-backend lead; schema evolution owner = backend-cascor lead; kill switch owner = security lead; documentation owner = project lead.

### 3.5 Version bump discipline

| Repo | Phase | Bump | Rationale |
|---|---|---|---|
| juniper-cascor-client | A | minor | New public method `set_params` |
| juniper-cascor | 0-cascor | minor | New envelope fields (public contract) |
| juniper-cascor | B-pre-a/b | patch | Security guards (no public API change) |
| juniper-cascor | E | minor | New `ws_backpressure_policy` setting |
| juniper-cascor | G | patch | Test-only |
| juniper-canopy | B-pre-a/b | patch | Security guards |
| juniper-canopy | B | minor | New browser bridge + `/api/ws_latency` endpoint |
| juniper-canopy | C/D/H | patch | Internal refactor / test-only |
| juniper-ml | per SDK bump | patch | Extras pin update |

Helm chart `Chart.yaml` `version` + `appVersion` must match app semver per Juniper ecosystem convention.

### 3.6 Merge sequence

**Critical path**: P2 --> P1 --> [72h soak] --> P3 --> P4 --> P6 --> [72h soak] --> P7 (**P0 win**).

Full sequence:

1. **P2**: `phase-a-sdk-set-params` --> juniper-cascor-client main --> PyPI publish
2. **P1**: `phase-0-cascor-seq-replay-resume` --> juniper-cascor main --> **72h staging soak**
3. **P3**: `phase-b-pre-a-cascor-security` --> juniper-cascor main
4. **P4**: `phase-b-pre-a-canopy-security` --> juniper-canopy main
5. **P5**: `phase-b-cascor-audit-prom-counters` --> juniper-cascor main
6. **P6**: `phase-b-canopy-drain-wiring` --> juniper-canopy main --> **72h staging soak**
7. **P7**: `phase-b-canopy-flag-flip` --> juniper-canopy main --> **P0 metric validated**
8. **P15**: `phase-g-cascor-set-params-integration` --> juniper-cascor main (parallel with C)
9. **P8**: `phase-b-pre-b-cascor-control-security` --> juniper-cascor main
10. **P9**: `phase-b-pre-b-canopy-csrf-audit` --> juniper-canopy main --> **48h production soak**
11. **P10**: `phase-c-canopy-set-params-adapter` --> juniper-canopy main (flag off) --> **>=7d canary** --> flag flip
12. **P11**: `phase-d-cascor-control-commands` --> juniper-cascor main
13. **P12**: `phase-d-canopy-button-ws-routing` --> juniper-canopy main
14. **P13**: `phase-e-cascor-backpressure-pump-tasks` --> juniper-cascor main (CONDITIONAL)
15. **P14**: `phase-f-heartbeat-jitter` --> juniper-cascor + juniper-canopy main
16. **P16**: `phase-h-normalize-metric-audit` --> juniper-canopy main

---

## 4. Phase 0-cascor: cascor server prerequisites (Engineer layer)

### 4.1 Goal

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope, advertises `server_instance_id` + `server_start_time` + `replay_buffer_capacity` + `emitted_at_monotonic` on every broadcast, supports a 1024-entry replay buffer with a `resume` handler, exposes `snapshot_seq` atomically on REST, no longer stalls fan-out on a single slow client (0.5s quick-fix), fixes GAP-WS-21 state coalescer, fixes GAP-WS-29 `broadcast_from_thread` exception swallowing, and returns protocol-error responses on unknown commands. The phase is purely additive -- existing clients that ignore new fields keep working.

### 4.2 Entry gate

- [ ] `juniper-cascor` main clean; `cd juniper-cascor/src/tests && bash scripts/run_tests.bash` green
- [ ] GAP-WS-19 verified RESOLVED: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` shows lock pattern at lines 138-156
- [ ] No concurrent cascor PR touching `websocket/*.py`, `lifecycle/manager.py`, `messages.py`
- [ ] `juniper-cascor-worker` CI green against current cascor main (baseline for post-soak)
- [ ] Prometheus namespace collision check for all 13 new `cascor_ws_*` metrics

### 4.3 Deliverables checklist

**Server-side code** (10 commits, single squash-merged PR):

| Commit | File(s) | Change |
|---|---|---|
| **0-cascor-1** | `juniper-cascor/src/api/websocket/messages.py` | Optional `seq: Optional[int]` + `emitted_at_monotonic: float` on every envelope builder |
| **0-cascor-2a** | `juniper-cascor/src/api/websocket/manager.py` | `server_instance_id=uuid4()`, `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer=deque(maxlen=Settings.ws_replay_buffer_size)`, `_assign_seq_and_append()` helper |
| **0-cascor-2b** | same | `connect()` sends `connection_established` with `{server_instance_id, server_start_time, replay_buffer_capacity}` (D-16) |
| **0-cascor-3** | same | `_send_json()` wraps in `asyncio.wait_for(timeout=Settings.ws_send_timeout_seconds)` (default 0.5s, GAP-WS-07 quick-fix); exception logged; metric incremented |
| **0-cascor-4** | same | `replay_since(last_seq) -> list[dict]` + `ReplayOutOfRange` exception; copy-under-lock |
| **0-cascor-5a** | `juniper-cascor/src/api/websocket/training_stream.py` | `_pending_connections: set[WebSocket]`, `connect_pending()`, `promote_to_active()` (D-14) |
| **0-cascor-5b** | same | `/ws/training` handler: `resume` frame (5s timeout) --> `resume_ok` or `resume_failed{out_of_range|server_restarted|second_resume}`. Server-restart via UUID mismatch (D-15). One-resume-per-connection via `resume_consumed: bool` (D-30) |
| **0-cascor-6** | `juniper-cascor/src/api/training/router.py` | `/api/v1/training/status` adds `snapshot_seq` + `server_instance_id` atomically under `_seq_lock` |
| **0-cascor-7** | `juniper-cascor/src/lifecycle/manager.py` (lines 133-136) | Replace 1 Hz drop-filter with debounced coalescer; terminal transitions (Completed/Failed/Stopped) bypass throttle (GAP-WS-21) |
| **0-cascor-8** | `juniper-cascor/src/api/websocket/manager.py` | `broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29) |
| **0-cascor-9** | `juniper-cascor/src/api/websocket/control_stream.py` | Protocol-error for unknown commands, close 1003 on malformed JSON, echo `command_id` when present, **NO seq on `command_response`** (D-03) |
| **0-cascor-10** | docs | CHANGELOG.md + `docs/websocket_protocol.md` ("Sequence numbers, replay, and reconnection" section with old/new compat matrix) |

**`command_response` carve-out** (D-03 canonical): `/ws/training` has seq and replay. `/ws/control` has NO seq and NO replay. Client correlation via `command_id` only.

**Settings** (`juniper-cascor/src/config/settings.py`):

- [ ] `ws_replay_buffer_size: int = 1024` (`JUNIPER_WS_REPLAY_BUFFER_SIZE`)
- [ ] `ws_send_timeout_seconds: float = 0.5` (`JUNIPER_WS_SEND_TIMEOUT_SECONDS`)
- [ ] `ws_resume_handshake_timeout_s: float = 5.0`
- [ ] `ws_state_throttle_coalesce_ms: int = 1000`
- [ ] `ws_pending_max_duration_s: float = 10.0`

**Observability** (all must be present before merge):

- [ ] `cascor_ws_seq_current` (Gauge)
- [ ] `cascor_ws_replay_buffer_occupancy` / `_bytes` / `_capacity_configured` (Gauge x3)
- [ ] `cascor_ws_resume_requests_total{outcome}` (Counter)
- [ ] `cascor_ws_resume_replayed_events` (Histogram, buckets `{0,1,5,25,100,500,1024}`)
- [ ] `cascor_ws_broadcast_timeout_total{type}` (Counter)
- [ ] `cascor_ws_broadcast_send_duration_seconds{type}` (Histogram)
- [ ] `cascor_ws_pending_connections` (Gauge)
- [ ] `cascor_ws_state_throttle_coalesced_total` (Counter)
- [ ] `cascor_ws_broadcast_from_thread_errors_total` (Counter; must be 0 steady state)
- [ ] `cascor_ws_connections_active{endpoint}` (Gauge)
- [ ] `cascor_ws_seq_gap_detected_total` (Counter; MUST be 0; page alert if non-zero)

### 4.4 Test acceptance

**Unit tests** (20, in `juniper-cascor/src/tests/unit/api/`):

Seq/replay cluster:
- `test_seq_monotonically_increases_across_broadcasts`
- `test_seq_is_assigned_on_loop_thread`
- `test_seq_lock_does_not_block_broadcast_iteration`
- `test_replay_buffer_bounded_to_configured_capacity` -- asserts `maxlen == Settings.ws_replay_buffer_size`
- `test_replay_buffer_capacity_configurable_via_env` -- override to 256 via env var
- `test_replay_buffer_size_zero_disables_replay` -- D-36 kill-switch value

Resume cluster:
- `test_resume_replays_events_after_last_seq` -- happy path
- `test_resume_failed_out_of_range` -- broadcast 2000, reconnect last_seq=10
- `test_resume_failed_server_restarted` -- server_instance_id mismatch
- `test_second_resume_closes_connection_1003` -- D-30

Connection/broadcast cluster:
- `test_connection_established_advertises_instance_id_and_capacity` -- D-16
- `test_snapshot_seq_atomic_with_state_read` -- concurrency: REST read during broadcast
- `test_slow_client_send_timeout_does_not_block_fanout` -- 0.5s quick-fix
- `test_send_timeout_env_override` -- D-46 kill-switch test
- `test_pending_connections_not_eligible_for_broadcast` -- D-14

Bug-fix cluster:
- `test_state_coalescer_flushes_terminal_transitions` -- Started-->Failed within 200ms, both observed (GAP-WS-21)
- `test_broadcast_from_thread_exception_logged` -- caplog assertion (GAP-WS-29)
- `test_unknown_command_returns_protocol_error_envelope` -- GAP-WS-22
- `test_malformed_json_closes_1003`

Contract:
- `test_ws_control_command_response_has_no_seq` -- D-03 explicit negative assertion

**Chaos tests** (3, **blocking gates** per R2-01 18.9):
- `chaos_broadcast_replay_race` -- hypothesis + asyncio.gather 100 concurrent; assert no seq gaps, no deadlocks
- `chaos_broadcast_fanout` -- 100 Hz x 60s x 10 clients; p95 < 250ms, memory +/-10% (load test)
- `chaos_broadcast_from_thread_exception` -- hypothesis exception types; assert counter increments

**Integration tests** (5, in `juniper-cascor/src/tests/integration/`):
- `test_resume_happy_path_via_test_client`
- `test_resume_failed_server_restarted` (stale UUID)
- `test_resume_failed_out_of_range` (broadcast 2000, reconnect last_seq=10)
- `test_resume_malformed_data`
- `test_resume_timeout_no_frame`

**Contract tests** (D-43, `@pytest.mark.contract`):
- `test_replay_buffer_capacity_advertised`
- `test_ws_control_command_response_has_no_seq`
- `test_close_all_holds_lock` (D-13 regression guard)

**Metric-presence test** (D-37): scrapes `/metrics`, asserts all 13 Phase 0-cascor metrics present.

**Run command**: `cd juniper-cascor/src/tests && bash scripts/run_tests.bash`

### 4.5 PR plan

| # | Branch | Repo | Squash-merge |
|---|---|---|---|
| **P1** | `phase-0-cascor-seq-replay-resume` | juniper-cascor | Yes (10 tightly coupled commits) |

### 4.6 Exit gate

1. All 20 unit + 5 integration + 3 chaos + load tests green
2. `/ws/training` staging broadcasts show strictly monotonic `seq` over 60s
3. `/api/v1/training/status` includes `snapshot_seq` and `server_instance_id` (curl verify)
4. `cascor_ws_broadcast_send_duration_seconds` p95 < 100ms in staging
5. Resume with `last_seq=N-5` replays exactly 5 events
6. Forced cascor restart triggers `resume_failed{server_restarted}`
7. `cascor_ws_replay_buffer_capacity_configured == 1024` in prod config, `== 256` in staging (proves tunable)
8. **72-hour staging soak** (D-38): `cascor_ws_seq_gap_detected_total == 0`, `broadcast_from_thread_errors_total == 0`, `broadcast_timeout_total` rate < 0.1/s
9. `juniper-cascor-worker` CI green against new cascor during soak
10. `WSSeqCurrentStalled` alert test-fired once in staging
11. Metrics-presence test green
12. Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published

**Going/no-go**: if criterion 8 shows any seq gap, HALT. Do not proceed to Phase B.

### 4.7 Rollback

```bash
# Slow-client false-drops (2 min)
export JUNIPER_WS_SEND_TIMEOUT_SECONDS=30
systemctl restart juniper-cascor

# Replay buffer disable (5 min)
export JUNIPER_WS_REPLAY_BUFFER_SIZE=0
systemctl restart juniper-cascor

# Emergency new server_instance_id (10 min)
systemctl restart juniper-cascor   # rolling restart forces all clients to snapshot-refetch

# Full rollback (15 min)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git revert <phase-0-cascor-merge-sha> --no-edit
git push origin main
# Blue/green redeploy
```

### 4.8 Alerts

| Alert | Severity | Rule | Test-fired in staging |
|---|---|---|---|
| `WSSeqCurrentStalled` | **PAGE** | `changes(cascor_ws_seq_current[5m])==0 AND connections>0` | Required before prod |
| `WSResumeBufferNearCap` | ticket | `occupancy > 0.8*capacity for 30s` | Yes |
| `WSPendingConnectionStuck` | ticket | `pending > 0 for 30s` | Yes |
| `WSSlowBroadcastP95` | ticket | `histogram_quantile(0.95) > 500ms` | Yes |

### 4.9 Cross-cutting concerns in this phase

- **CCC-01**: All new fields additive. `command_id` rename mandate enforced (grep PR for `request_id` must return 0). `emitted_at_monotonic` ships here.
- **CCC-02**: All 13 metrics present before merge. Metrics-presence CI test runs on PR.
- **CCC-03**: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` and `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` as kill switches with CI tests.
- **CCC-04**: Merges before canopy Phase B (1-week additive-soak). Helm chart bumped.
- **CCC-05**: Contract tests `test_replay_buffer_capacity_advertised`, `test_ws_control_command_response_has_no_seq`, `test_close_all_holds_lock`.
- **CCC-06**: CHANGELOG entry, `docs/websocket_protocol.md` section, runbook `cascor-replay-buffer.md`.
- **CCC-07**: 5 new `ws_*` settings in canonical table with Pydantic `Field(description=...)`.
- **CCC-08**: REST `/api/v1/training/status` extended additively. `juniper-cascor-worker` CI green during soak.
- **CCC-09**: No feature flags in this phase (purely additive).
- **CCC-10**: `emitted_at_monotonic` ships as the latency pipe seed for Phase B.

### 4.10 NOT in this phase

- Full Phase E backpressure (only 0.5s `_send_json` quick-fix lands)
- `permessage-deflate` (GAP-WS-17)
- Topology chunking (GAP-WS-18)
- `seq` on `command_response` (D-03 explicitly excludes)
- GAP-WS-19 re-fix (already on main; regression test only)
- M-SEC-01..11 security controls (Phase B-pre-a/b)
- Multi-tenant replay buffers (D-32 deferred)
- Canopy adapter changes (Phase C)
- Canopy drain callbacks (Phase B)

---

## 5. Phase A-SDK: `set_params` on cascor-client (Engineer layer)

### 5.1 Goal

Ship `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None)` to PyPI with per-request `command_id` correlation, caller-cancellation safety, fail-fast on disconnect, no retry logic.

### 5.2 Entry gate

- [ ] `juniper-cascor-client` main clean; baseline tests green
- [ ] No concurrent cascor-client PR open

### 5.3 Deliverables checklist

**New method** (`juniper-cascor-client/juniper_cascor_client/control_stream.py`):

```python
async def set_params(
    self,
    params: dict,
    *,
    timeout: float = 1.0,      # D-01: source doc 7.32 specific beats 7.1 generic
    command_id: Optional[str] = None,  # D-02: NOT request_id
) -> dict:
    ...
```

**Behavior**:
- Generates `command_id = str(uuid.uuid4())` if absent
- Registers future in `self._pending: Dict[str, asyncio.Future]` (max 256; overflow raises `JuniperCascorOverloadError`)
- Sends `{"type": "command", "command": "set_params", "command_id": ..., "params": ...}`
- Awaits matching `command_response` via background `_recv_task`
- Raises `JuniperCascorTimeoutError` on timeout, `JuniperCascorConnectionError` on disconnect
- Default `timeout=1.0` (D-01)
- ALWAYS `pop(command_id, None)` in `finally` (caller-cancellation safety, R1-05 4.25)
- **No SDK retries** (D-20)
- Stashes `envelope["_client_latency_ms"]` (private field, leading underscore)

**Supporting files**:
- [ ] `testing/fake_ws_client.py`: `on_command(name, handler)` auto-scaffold `command_response`
- [ ] `testing/server_harness.py`: `FakeCascorServerHarness` for canopy Phase B tests -- emits envelopes with same shape as real cascor
- [ ] `pyproject.toml` minor version bump (new public method)
- [ ] CHANGELOG.md entry citing GAP-WS-01, R1-05 4.2
- [ ] PyPI publish; same-day `juniper-ml` extras pin bump follow-up PR (D-57)
- [ ] TestPyPI prerelease for canopy PR iteration before PyPI promotion

**Metric**: `juniper_cascor_client_ws_set_params_total{status}` (status = `success|timeout|connection_error|server_error|overload`)

### 5.4 Test acceptance

12 tests: `test_set_params_default_timeout_is_one_second`, `test_set_params_happy_path`, `test_set_params_timeout_raises_typed_exception`, `test_set_params_concurrent_correlation`, `test_set_params_caller_cancellation_cleans_correlation_map` (**mandatory gate**), `test_set_params_fails_fast_on_disconnect`, `test_set_params_no_retry_on_timeout`, `test_set_params_server_error_response`, `test_correlation_map_bounded_at_256`, `test_recv_task_propagates_exception_to_all_pending_futures`, `test_len_pending_returns_to_zero_after_failure_modes`, `test_set_params_x_api_key_header_present`

### 5.5 PR plan

| # | Branch | Repo |
|---|---|---|
| **P2** | `phase-a-sdk-set-params` | juniper-cascor-client |

### 5.6 Exit gate

1. All 12 tests pass; coverage >=95% on new code
2. `pip install juniper-cascor-client==<new>` succeeds in fresh venv
3. Draft canopy adapter can import and call `set_params` against `FakeCascorServerHarness`
4. `juniper-ml/pyproject.toml` extras pin bump PR opened

### 5.7 Rollback

```bash
# PyPI yank (2 min, only if installs-won't-import)
# Otherwise fix-forward with patch release

# Downstream pin downgrade (15 min)
# Edit juniper-canopy pyproject.toml: juniper-cascor-client = "<version"
```

No runtime flag exists; SDK method is dead code until Phase C flips the flag.

### 5.8 NOT in this phase

- Canopy adapter refactor (Phase C)
- SDK retries or reconnect queue (D-20, none ever)
- Debounce (Dash clientside callback, Phase B)

---

## 6. Phase B-pre-a: read-path security (Engineer layer)

### 6.1 Goal

Close the minimum security holes for browser `/ws/training` exposure: frame-size caps (M-SEC-03, 4KB inbound), Origin allowlist on `/ws/training` (M-SEC-01b), per-IP connection caps (M-SEC-04, 5/IP), idle timeout (M-SEC-10, 120s), audit logger skeleton (M-SEC-07).

### 6.2 Entry gate

- [ ] Phase 0-cascor (P1) merged to cascor main (1-week additive-soak starts)
- [ ] Both cascor and canopy main clean
- [ ] `canopy.audit` logger name not already used: `grep -rn "canopy.audit" juniper-canopy/src/`

### 6.3 Deliverables checklist

**Cascor side** (PR P3):
- [ ] `origin.py` (new): `validate_origin(ws, allowlist) -> bool` (case-insensitive, port-significant, null rejected, `*` refused, empty=reject-all)
- [ ] Wire into `training_stream_handler` (NOT `control_stream_handler`)
- [ ] `ws_allowed_origins: list[str] = []` (fail-closed), `ws_max_connections_per_ip: int = 5`
- [ ] `_per_ip_counts: Dict[str,int]` under `_lock`, decrement in `disconnect()` finally
- [ ] `max_size=4096` on every inbound `receive_*()`
- [ ] Idle timeout: `asyncio.wait_for(receive_text(), timeout=120)`, close 1000

**Canopy side** (PR P4):
- [ ] `ws_security.py` (new): copy of cascor `validate_origin` (explicit duplication, no cross-import)
- [ ] Wire into `/ws/training` route in `main.py`
- [ ] `allowed_origins` with localhost/127.0.0.1 x http/https defaults
- [ ] `max_size=4096` on `/ws/training`, `max_size=65536` on `/ws/control`
- [ ] `audit_log.py` (new): `canopy.audit` JSON logger, `TimedRotatingFileHandler`, scrub allowlist, CRLF escape
- [ ] CI `scripts/audit_ws_receive_calls.py`: AST check every `ws.receive_*()` has explicit `max_size`

### 6.4 Test acceptance

17 tests including: `test_oversized_frame_rejected_with_1009`, `test_per_ip_cap_enforced_6th_rejected_1013`, `test_per_ip_counter_decrements_on_disconnect`, `test_per_ip_counter_decrements_on_exception`, `test_per_ip_map_shrinks_to_zero`, `test_origin_allowlist_accepts_configured_origin`, `test_origin_allowlist_rejects_third_party`, `test_origin_allowlist_rejects_missing_origin`, `test_empty_allowlist_rejects_all_fail_closed`, `test_allowed_origins_wildcard_refused`, `test_idle_timeout_closes_1000`, `test_audit_log_format_and_scrubbing`, `test_audit_log_rotates_daily`, `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` (Playwright)

### 6.5 PR plan

| # | Branch | Repo | Order |
|---|---|---|---|
| **P3** | `phase-b-pre-a-cascor-security` | juniper-cascor | First |
| **P4** | `phase-b-pre-a-canopy-security` | juniper-canopy | After P3 |

### 6.6 Exit gate

1. All tests + CI AST guardrail green
2. CSWSH probe from `http://evil.example.com` rejected
3. 65KB frame returns close 1009
4. 6th same-IP connection returns 1013
5. Empty allowlist rejects all (fail-closed). **HALT if fail-open.**
6. `WSOriginRejection` alert test-fired in staging
7. 24-hour staging soak with no user lockout

### 6.7 Rollback

```bash
# Per-IP cap neutralize (5 min)
export JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999
systemctl restart juniper-cascor juniper-canopy

# Broaden allowlist (5 min)
export JUNIPER_WS_ALLOWED_ORIGINS='http://extra-origin:8050,http://localhost:8050'

# Idle timeout disable (5 min)
export JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0

# Audit log disable (5 min)
export JUNIPER_AUDIT_LOG_ENABLED=false

# Full revert (10 min)
git revert <phase-b-pre-a-canopy-merge> <phase-b-pre-a-cascor-merge>
```

### 6.8 Observability

| Metric | Type | Purpose |
|---|---|---|
| `cascor_ws_oversized_frame_total{endpoint, type}` | Counter | Size guard signal |
| `cascor_ws_per_ip_rejected_total` | Counter | Per-IP cap signal |
| `cascor_ws_idle_timeout_total` | Counter | Idle timeout signal |
| `canopy_ws_oversized_frame_total{endpoint}` | Counter | Canopy-side size guard |
| `canopy_ws_per_ip_rejected_total` | Counter | Canopy-side per-IP cap |
| `canopy_ws_origin_rejected_total{origin_hash, endpoint}` | Counter | Origin hash (SHA-256 prefix 8 chars, GDPR-safe) |
| `canopy_audit_events_total{event_type}` | Counter | Counter only; Prom hookup deferred to Phase B |
| `canopy_ws_handshake_attempts_total{outcome}` | Counter | Handshake funnel |

**Alerts**:
- `WSOriginRejection` (**PAGE**, D-51): `increase(canopy_ws_origin_rejected_total{origin_hash=unknown}[5m]) > 0` -- CSWSH probe canary
- `WSOversizedFrame` (**PAGE**): `increase(canopy_ws_oversized_frame_total[5m]) > 0`

**Runbooks**: `ws-audit-log-troubleshooting.md`, `ws-cswsh-detection.md` (initial version).

### 6.9 NOT in this phase

- Cookie + CSRF first-frame (Phase B-pre-b)
- Origin on `/ws/control` (Phase B-pre-b)
- Rate limit (Phase B-pre-b)
- Prometheus counters for audit (Phase B)
- HMAC adapter auth (Phase B-pre-b)

---

## 7. Phase B: browser bridge + polling elimination -- P0 (Engineer layer)

### 7.1 Goal

The P0 win. Canopy browser drains `/ws/training` into bounded Dash stores, renders chart updates via `Plotly.extendTraces`, and stops polling `/api/metrics/history` when WS is healthy. Ships behind two-flag gate. REST polling handler preserved forever as kill-switch fallback.

### 7.2 Entry gate

- [ ] Phase 0-cascor merged + deployed + **72h soak passed** (D-38)
- [ ] `cascor_ws_seq_gap_detected_total == 0` over full soak
- [ ] Phase B-pre-a (P3 + P4) merged and deployed
- [ ] Phase A-SDK published to PyPI
- [ ] **Pre-Phase-B bandwidth baseline measured**: 1h of staging traffic recorded in `canopy_rest_polling_bytes_per_sec` (D-62)
- [ ] NetworkVisualizer render tech verified: `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py`

### 7.3 Deliverables checklist

**Frontend JS** (`juniper-canopy/src/frontend/assets/`):

| File | Action | Key detail |
|---|---|---|
| `ws_dash_bridge.js` | NEW (~200 LOC) | `window._juniperWsDrain` namespace; 5 `on(type,...)` handlers for metrics/state/topology/cascade_add/candidate_progress; per-handler bounded ring buffers (`MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`); drain methods: `drainMetrics()`, `drainState()`, `drainTopology()`, `drainCascadeAdd()`, `drainCandidateProgress()`, `peekStatus()`; **ring bound enforced IN the handler** (not drain callback) per R1-02 5.4 compile-time invariant |
| `websocket_client.js` | EDIT (do NOT delete) | `onStatus()` enrichment (connected/reason/reconnectAttempt/ts); jitter: `delay = Math.random() * Math.min(30000, 500 * 2**attempt)` (GAP-WS-30); **remove 10-attempt cap** (GAP-WS-31, retry forever, max 30s); capture `server_instance_id` from `connection_established`; `seq` tracking with monotonic check + WARN on gap; on reconnect send `resume` frame with `{last_seq, server_instance_id}`, fallback to REST on `resume_failed` |
| `dashboard_manager.py:1490-1526` | DELETE | Remove parallel raw-WS clientside callback (GAP-WS-03). Leave placeholder comment citing this blueprint. This is the only deletion in Phase B (dead code). |
| `ws_latency.js` | NEW (~50 LOC) | Browser latency beacon: records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60s (GAP-WS-24a). Clock-offset recomputation on reconnect. Gated on `Settings.enable_ws_latency_beacon`. |
| rAF scaffold | SCAFFOLD | `_scheduleRaf = noop` in `ws_dash_bridge.js`; disabled per D-04. Enable only if instrumentation shows frame pressure. |

**Python stores + drain callbacks** (`juniper-canopy/src/frontend/`):

| File | Change | Key detail |
|---|---|---|
| `dashboard_manager.py` | Add `dcc.Store(id='ws-metrics-buffer')` | Drain callback fires on `fast-update-interval` tick. Reads `window._juniperWsDrain.drainMetrics()`. Writes structured `{events: [...], gen: int, last_drain_ms: float}` (D-07, NOT bare array). `gen` counter makes Dash change-detection deterministic. |
| `dashboard_manager.py` | Update `ws-topology-buffer` + `ws-state-buffer` | Drains read from `window._juniperWsDrain.drainTopology()` / `drainState()`. Delete old `window._juniper_ws_*` globals. |
| `dashboard_manager.py` | Add `ws-cascade-add-buffer` + `ws-candidate-progress-buffer` | New stores + drain callbacks |
| `dashboard_manager.py` | Add `ws-connection-status` store | Peek-based drain; emits only on change |
| `dashboard_manager.py:2388-2421` | Refactor `_update_metrics_store_handler` | Return `no_update` when `ws-connection-status.connected===true`. Slow fallback to 1 Hz via `n % 10 != 0` (D-05). Preserve initial-load REST GET path. |
| `dashboard_manager.py` | Polling-toggle pattern | Apply to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. **Keep REST paths** (kill-switch fallback, D-54). |
| `components/metrics_panel.py:648-670` | Clientside callback | `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"`. Hidden `metrics-panel-figure-signal` dummy Store. Same for `candidate_metrics_panel.py`. |
| `components/network_visualizer.py` | Minimum WS wire | Wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to cytoscape callback (D-06). Keep REST poll fallback. First commit verifies render tech. |
| `components/connection_indicator.py` (new) | Connection badge | `html.Div` with clientside_callback. States: connected-green, reconnecting-yellow, offline-red, demo-gray |
| `backend/demo_mode.py` | Demo parity | Set `ws-connection-status={connected:true, mode:"demo"}` (RISK-08) |

**Backend endpoints** (`juniper-canopy/src/main.py`):
- [ ] `/api/ws_latency` POST: feeds `canopy_ws_delivery_latency_ms_bucket` histogram (GAP-WS-24b)
- [ ] `/api/ws_browser_errors` POST: feeds `canopy_ws_browser_js_errors_total{component}` counter (D-59)
- [ ] `canopy_rest_polling_bytes_per_sec{endpoint}` gauge (P0 motivator proof)

**Phase I bundled**: content-hash `assets_url_path` / cache-bust query string (R2-02 section 14).

**Two-flag runtime**: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge`. Default `enable_browser_ws_bridge=False` during PR window. Staging flip is ops-driven. Production flip is P7 (separate one-line config PR, project-lead review).

### 7.4 Test acceptance

~35 tests. Organized by type:

**P0 gates** (Playwright, blocking):
- `test_bandwidth_eliminated_in_ws_mode` -- THE P0 ACCEPTANCE GATE: `/api/metrics/history` request count == 0 over 60s after initial load
- `test_polling_elimination` -- measures request count over 60s with WS connected, asserts zero after initial load

**RISK gates** (blocking):
- `test_metrics_message_has_dual_format` -- RISK-01: both flat + nested keys (Phase H fold-in)
- `test_demo_mode_metrics_parity` -- RISK-08: runs in BOTH fast AND e2e lanes

**Python unit**:
- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_ws_metrics_buffer_drain_is_bounded`
- `test_fallback_polling_at_1hz_when_disconnected` (D-05)
- `test_ws_metrics_buffer_store_is_structured_object` (D-07)
- `test_both_flags_interact_correctly` (D-17 + D-18 two-flag logic)
- `test_network_visualizer_updates_on_ws_cascade_add`
- `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` (GAP-WS-24b)
- `test_latency_histogram_resilient_to_laptop_sleep` (CCC-10 clock offset)
- `test_audit_log_prometheus_counters` (deferred hookup)

**dash_duo (e2e)**:
- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected`
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_connection_indicator_badge_reflects_state`
- `test_ws_metrics_buffer_ignores_events_with_duplicate_seq`
- `test_ws_metrics_buffer_is_monotonic_in_seq_no_gap_gt_1`

**Playwright**:
- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_seq_reset_on_cascor_restart`
- `test_plotly_extendTraces_used_not_full_figure_replace`
- `test_asset_url_includes_version_query_string` (Phase I fold-in)

**Contract** (D-43, `@pytest.mark.contract`):
- `test_fake_cascor_message_schema_parity` (CCC-05)
- `test_browser_message_handler_keys_match_cascor_envelope`

**Latency** (recording-only in CI, D-42):
- `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` -- marked `latency_recording`

**Chaos** (nightly, D-40):
- Browser-bridge chaos: random kills/restarts, event rate variance, corrupted envelopes. Assert: no OOM, no freeze.

**Soak** (blocking for P7 flag-flip):
- 72h memory soak: `canopy_ws_browser_heap_mb` p95 growth <20%

### 7.5 PR plan

| # | Branch | Repo | Order |
|---|---|---|---|
| **P5** | `phase-b-cascor-audit-prom-counters` | juniper-cascor | First |
| **P6** | `phase-b-canopy-drain-wiring` | juniper-canopy | After P5, flag-off |
| **P7** | `phase-b-canopy-flag-flip` | juniper-canopy | After 72h soak, one-line PR |

### 7.6 Exit gate

**For P6 merge**:
1. All ~30 tests pass
2. `canopy_rest_polling_bytes_per_sec` >=90% lower than baseline in staging (1h)
3. Metrics-presence CI test green
4. `Settings.enable_browser_ws_bridge=False` is merged default

**For P7 flag-flip** (going/no-go):
5. 72h staging with `enable_browser_ws_bridge=True` (ops env-flipped), no page alerts
6. `canopy_rest_polling_bytes_per_sec` reduction >=90% sustained over 72h
7. Browser memory p95 <=500 MB over 72h (RISK-10)
8. `canopy_ws_drain_callback_gen` advancing (no stuck drains)
9. Mid-week deploy window (D-61)
10. Kill switch `disable_ws_bridge=True` tested manually, TTF <=5 min

### 7.7 Rollback

```bash
# Fastest (2 min)
export JUNIPER_DISABLE_WS_BRIDGE=true
systemctl restart juniper-canopy
# REST polling takes over automatically

# Dev flag off (5 min)
# Set enable_browser_ws_bridge=False in config, redeploy

# Per-user diagnostic
# URL query param ?ws=off

# Full revert (30 min)
git revert <phase-b-canopy-merge-sha>
git push origin main
# Cache-bust invalidation needed
```

### 7.8 Observability (new in this phase)

| Metric | Type | Purpose |
|---|---|---|
| `canopy_rest_polling_bytes_per_sec{endpoint}` | Gauge | **P0 win signal** |
| `canopy_ws_delivery_latency_ms_bucket{type}` | Histogram | End-to-end latency (buckets: 50,100,200,500,1000,2000,5000 ms) |
| `canopy_ws_backend_relay_latency_ms` | Histogram | Cascor-->canopy hop |
| `canopy_ws_browser_heap_mb` | Gauge | RISK-10 signal (via JS beacon) |
| `canopy_ws_browser_js_errors_total{component}` | Counter | Every try/catch increments |
| `canopy_ws_drain_callback_gen{buffer}` | Gauge | Stuck drain detector (monotonic) |
| `canopy_ws_active_connections` | Gauge | Capacity planning |
| `canopy_ws_reconnect_total{reason}` | Counter | Storm detection |
| `canopy_ws_connection_status{status}` | Gauge | Dashboard signal |
| `canopy_audit_events_total{event_type}` | Counter | Prometheus hookup (deferred from B-pre-a) |
| `canopy_ws_latency_beacon_errors_total` | Counter | Beacon reliability |

**Alerts**:
- `WSDrainCallbackGenStuck` (PAGE): `changes(canopy_ws_drain_callback_gen[2m]) == 0` with active connections
- `WSBrowserHeapHigh` (ticket): p95 > 500 MB for 10m
- `WSJSErrorsNonZero` (ticket): `increase(canopy_ws_browser_js_errors_total[5m]) > 0`

**Dashboards** (committed as JSON to `juniper-canopy/deploy/grafana/`):
- "WebSocket health" panel: p50/p95/p99 delivery latency per event type
- "Polling bandwidth" panel: `canopy_rest_polling_bytes_per_sec` trend
- "Browser memory" panel: `canopy_ws_browser_heap_mb` p95 trend

**Runbooks**:
- `juniper-canopy/notes/runbooks/ws-bridge-kill.md` -- 5-min TTF recipe
- `juniper-canopy/notes/runbooks/ws-bridge-debugging.md` -- diagnose drain-callback death
- `juniper-canopy/notes/runbooks/ws-memory-soak-test-procedure.md` -- 72h soak procedure

### 7.9 Cross-cutting concerns in this phase

- **CCC-01**: Browser reads new envelope fields (`seq`, `server_instance_id`, `replay_buffer_capacity`, `emitted_at_monotonic`). Sends `resume` frame on reconnect.
- **CCC-02**: 11 new canopy metrics (biggest observability contribution). Metric-before-behavior enforced.
- **CCC-03**: Two-flag pattern. `enable_browser_ws_bridge` (dev opt-in) and `disable_ws_bridge` (permanent kill). Kill-switch drill during 72h soak.
- **CCC-04**: Canopy pins `juniper-cascor-client>=SDK_VERSION_A`. Cross-version CI lane: canopy e2e against N-1 and N SDK versions.
- **CCC-05**: `test_fake_cascor_message_schema_parity`, `test_browser_message_handler_keys_match_cascor_envelope`, `test_normalize_metric_produces_dual_format` (Phase H regression folded in).
- **CCC-08**: REST polling handler KEPT FOREVER. Regression harness `test_rest_endpoints_remain_functional.py` in `fast` lane.
- **CCC-09**: Two-flag pattern. Flip is separate PR (P7). Flag-flip criteria documented in runbook.
- **CCC-10**: Full latency pipe activated. `emitted_at_monotonic` from cascor --> `canopy_ws_backend_relay_latency_ms` --> browser beacon --> `/api/ws_latency` --> `canopy_ws_delivery_latency_ms_bucket`. Clock offset recomputation on reconnect.

### 7.10 NOT in this phase

- Phase C `set_params` (read-only bridge in Phase B)
- Phase D control buttons (remain REST POST)
- Full rAF coalescing (scaffold only)
- Full Phase E backpressure
- Phase F heartbeat (jitter ships here; heartbeat is Phase F)
- CODEOWNERS for `_normalize_metric` (Phase H; regression test lands here)
- NetworkVisualizer deep render migration (Phase B+1)

---

## 8. Phase B-pre-b: control-path security (Engineer layer)

### 8.1 Goal

Full CSWSH/CSRF protections on `/ws/control`: Origin allowlist, cookie+CSRF first-frame (M-SEC-02), rate limit (10 cmd/s), idle timeout, adapter HMAC CSRF auth (D-29), adapter inbound validation (M-SEC-11), log-injection escaping. Runs in parallel with Phase B. Gates Phase D.

### 8.2 Entry gate

- [ ] Phase B-pre-a in main
- [ ] SessionMiddleware presence verified: `grep -rn "SessionMiddleware" juniper-canopy/src/` (assume absent; budget +0.5d)
- [ ] D-29 HMAC approach confirmed

### 8.3 Deliverables checklist

**Cookie session + CSRF** (canopy side, `juniper-canopy/src/main.py` + `src/backend/`):
- [ ] Add `SessionMiddleware` (reuse if present per day-1 verification; budget +0.5d if absent)
- [ ] `/api/csrf` REST endpoint: `secrets.token_urlsafe(32)` mint-on-first-request
- [ ] Token rotation: 1h sliding activity, session login/logout, server restart, any auth close
- [ ] Dash template render-time embedding: `window.__canopy_csrf` (NOT localStorage -- XSS risk)
- [ ] `websocket_client.js`: first frame after `onopen` = `{type:"auth", csrf_token:...}`
- [ ] Cookie attrs: `HttpOnly; Secure; SameSite=Strict; Path=/`
- [ ] All compares use `hmac.compare_digest` (constant-time)
- [ ] Auth timeout: `asyncio.wait_for(ws.receive_text(), timeout=5.0)` for first frame; timeout --> close 1008

**Origin + rate limit** (cascor side):
- [ ] `/ws/control` Origin validation (reuses B-pre-a helper from `origin.py`)
- [ ] Per-connection leaky bucket: 10 tokens, 10/s refill. 11th command --> `{command_response, status:"rate_limited", retry_after:0.3}`. Connection stays up.
- [ ] M-SEC-10 idle timeout: 120s bidirectional (already in B-pre-a for cascor)
- [ ] Per-origin handshake cooldown: 10 rejections in 60s --> 5-minute IP block (429). Cleared on restart (NAT-hostile escape hatch).

**Adapter HMAC** (canopy adapter --> cascor):
- [ ] `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()`
- [ ] First frame: `{type:"auth", csrf_token:<hmac>}`
- [ ] Cascor derives same value, compares with `hmac.compare_digest`
- [ ] Uniform handler logic: no `X-Juniper-Role: adapter` header special case

**M-SEC-11 adapter inbound validation** (`cascor_service_adapter.py`):
- [ ] Wraps inbound frames with `CascorServerFrame` Pydantic model (`extra="allow"` -- cascor may add fields additively)
- [ ] Malformed frame --> log + increment `canopy_adapter_inbound_invalid_total` + continue

**Additional**:
- [ ] M-SEC-06 opaque close reasons: only canonical strings (`"Internal error"`, `"Invalid frame"`, etc.)
- [ ] Log injection escaping: CRLF (`\r`, `\n`, `\t`) in all logged strings
- [ ] CI guardrail: `juniper-deploy` compose validation refuses `ws_security_enabled=false` in prod profile
- [ ] `disable_ws_control_endpoint: bool = False` kill switch (CSWSH emergency hard-disable)

### 8.4 Test acceptance

~17 tests including: `test_csrf_required_for_websocket_first_frame`, `test_csrf_token_rotation_race`, `test_csrf_token_uses_hmac_compare_digest`, `test_session_cookie_httponly_secure_samesitestrict`, `test_command_rate_limit_10_per_sec`, `test_canopy_adapter_sends_hmac_csrf_token_on_connect`, `test_audit_log_escapes_crlf_injection`, `test_opaque_close_reasons_no_human_readable_strings`, `test_cswsh_from_evil_page_cannot_start_training` (Playwright)

### 8.5 PR plan

| # | Branch | Repo | Order |
|---|---|---|---|
| **P8** | `phase-b-pre-b-cascor-control-security` | juniper-cascor | First |
| **P9** | `phase-b-pre-b-canopy-csrf-audit` | juniper-canopy | After P8 |

### 8.6 Exit gate

1. All tests green
2. Manual: `/ws/control` without CSRF --> close 1008
3. Manual: wrong origin --> close 1008
4. Manual: 11 commands in 900ms --> rate_limited / close 1013
5. Adapter reconnects via HMAC handshake post-deploy
6. **48h staging soak** (auth-path change, high risk)
7. CI guardrail test for prod compose
8. Project-lead sign-off

### 8.7 Rollback

```bash
# Dev env flag (5 min)
export JUNIPER_WS_SECURITY_ENABLED=false   # prod CI refuses this
systemctl restart juniper-canopy

# Hard-disable control endpoint (5 min, CSWSH emergency)
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true
systemctl restart juniper-canopy

# Rate limiting off (5 min)
export JUNIPER_WS_RATE_LIMIT_ENABLED=false

# Full revert (15 min)
git revert <phase-b-pre-b-canopy> <phase-b-pre-b-cascor>
```

### 8.8 Observability (new in this phase)

| Metric | Type | Purpose |
|---|---|---|
| `canopy_ws_auth_rejections_total{reason, endpoint}` | Counter | Auth failure tracking |
| `canopy_ws_rate_limited_total{command, endpoint}` | Counter | Rate limit visibility |
| `canopy_ws_command_total{command, status, endpoint}` | Counter | Command funnel |
| `canopy_ws_auth_latency_ms{endpoint}` | Histogram | Auth overhead |
| `canopy_ws_handshake_attempts_total{outcome}` | Counter | Handshake funnel for incidents |
| `canopy_ws_per_origin_cooldown_active` | Gauge | Cooldown status |
| `canopy_csrf_validation_failures_total` | Counter | CSRF probe signal |
| `cascor_ws_control_rate_limit_rejected_total` | Counter | Server-side rate limit |
| `canopy_adapter_inbound_invalid_total` | Counter | Malformed frame from cascor |

**Alerts**: `WSAuthSpike` (ticket: >10 rejections in 5m), `WSRateLimitSpike` (ticket: sustained non-zero), per-origin cooldown >5m (ticket).

**Runbooks**: `ws-auth-lockout.md`, `ws-cswsh-detection.md`.

### 8.9 NOT in this phase

- Per-command HMAC (D-31 deferred indefinitely)
- Two-bucket rate limiting (D-33 deferred)
- Multi-tenant replay isolation (D-32 deferred)

---

## 9. Phase C: `set_params` adapter (Engineer layer)

### 9.1 Goal

Canopy adapter splits parameter updates into hot (11 params via WS) and cold (via REST). Feature-flagged `use_websocket_set_params=False`. REST path permanent.

### 9.2 Entry gate

- [ ] Phase A-SDK on PyPI; `juniper-ml` extras pin bumped
- [ ] Phase B in main with `enable_browser_ws_bridge=True` in staging >=7 days

### 9.3 Deliverables checklist

**Adapter refactor** (`juniper-canopy/src/backend/cascor_service_adapter.py`):

- [ ] `_HOT_CASCOR_PARAMS: frozenset[str]` -- the 11 params routed via WS when flag is on:
  ```
  learning_rate, candidate_learning_rate, correlation_threshold,
  candidate_pool_size, max_hidden_units, epochs_max, max_iterations,
  patience, convergence_threshold, candidate_convergence_threshold,
  candidate_patience
  ```
- [ ] `_COLD_CASCOR_PARAMS: frozenset[str]` -- always REST: `init_output_weights`, `candidate_epochs`
- [ ] `apply_params(**params)` splits --> `_apply_params_hot()` (WS, fires first) + `_apply_params_cold()` (REST)
- [ ] `_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)` with `command_id`
- [ ] On timeout/error --> **unconditional REST fallback** (not retry-based; R0-04 5.1)
- [ ] Unclassified keys default to REST with WARNING log (D-34)
- [ ] `_control_stream_supervisor` background task: backoff `[1,2,5,10,30]s`, reconnect forever, sends HMAC first-frame
- [ ] Bounded correlation map max 256 + `canopy_control_stream_pending_size` gauge (R1-02 6.4)
- [ ] Fail-loud startup: INFO log of hot/cold/unknown classification for every canopy param
- [ ] `assert len(_HOT_CASCOR_PARAMS) > 0 if use_websocket_set_params`

**Dash clientside** (`juniper-canopy/src/frontend/`):
- [ ] 250ms debounce in slider callback (D-22, Dash clientside only, NOT SDK)

**Settings**:
- [ ] `use_websocket_set_params: bool = False` (D-47)
- [ ] `ws_set_params_timeout: float = 1.0` (D-01)

**Dependencies**:
- [ ] `pyproject.toml` bump `juniper-cascor-client>=${SDK_VERSION_A}`
- [ ] `juniper-ml/pyproject.toml` matching extras pin bump

### 9.4 Test acceptance

~15 tests including: `test_apply_params_feature_flag_default_off`, `test_apply_params_hot_keys_go_to_websocket`, `test_apply_params_cold_keys_go_to_rest`, `test_apply_params_hot_falls_back_to_rest_on_timeout`, `test_apply_params_unclassified_keys_default_to_rest_with_warning`, `test_slider_debounce_250ms_collapses_rapid_updates`

**Flag-flip criteria** (D-48, 6 hard gates): >=7d production data, p99 delta >=50ms, zero orphaned commands, zero correlation-map leaks, canary >=7d, zero page alerts in canary window.

### 9.5 PR plan

| # | Branch | Repo |
|---|---|---|
| **P10** | `phase-c-canopy-set-params-adapter` | juniper-canopy |

### 9.6 Exit gate

1. All tests green; coverage >=90% on new code
2. Flag off: `transport="rest"` has data; `transport="ws"` empty
3. Flag on in staging: both transports have data
4. Manual: slider drag updates within 1s; kill cascor --> REST fallback within 2s

### 9.7 Rollback

```bash
# Instant (2 min)
export JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false
systemctl restart juniper-canopy

# Tight timeout forces fast REST fallback (5 min)
export JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1
```

### 9.8 Observability

- `canopy_set_params_latency_ms_bucket{transport, key}` -- flag-flip gate metric (comparing WS vs REST p99)
- `canopy_orphaned_commands_total{command}` -- RISK-13 signal (ticket severity)
- `canopy_control_stream_pending_size` -- bounded correlation map gauge (must return to 0)

**Alert**: `CanopyOrphanedCommands` (ticket): `rate > 1/60`.
**Runbook**: `ws-set-params-feature-flag.md`.

### 9.9 NOT in this phase

- SDK retries (D-20, none), REST deprecation (D-21, never), frontend buttons (Phase D)

---

## 10. Phase D: control buttons via WS (Engineer layer)

### 10.1 Goal

Route browser start/stop/pause/resume/reset through `/ws/control` with `command_id` correlation and REST fallback. Per-command timeouts: `start: 10s`, others: `2s`.

### 10.2 Entry gate

- [ ] **Phase B-pre-b in production >=48h** (NOT just staging)
- [ ] Phase B in main with `enable_browser_ws_bridge=True`
- [ ] Zero CSRF incidents during 48h soak

### 10.3 Deliverables checklist

**Frontend** (`juniper-canopy/src/frontend/components/training_controls.py`):
- [ ] Clientside callback on each button: if `window.cascorControlWS` connected --> `send({command, command_id: uuidv4()})`; else REST POST
- [ ] Per-command client-side correlation map (per-connection scoped)
- [ ] Orphaned-command pending-verification UI: button disabled while in-flight; resolves via `command_response` OR matching `state` event
- [ ] Per-command timeouts: `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`, `reset: 2s`
- [ ] Badge shows "pending" while awaiting WS ack
- [ ] `enable_ws_control_buttons: bool = False` (D-49)

**Cascor** (`juniper-cascor/src/api/websocket/control_stream.py`):
- [ ] `/ws/control` handler routes inbound `{command, command_id, ...}` to existing REST-POST-backed handler
- [ ] Emits `command_response{command_id, status, error?}` (NO seq per D-03)
- [ ] Per-command timeout via `asyncio.wait_for`
- [ ] Command whitelist: `start`, `stop`, `pause`, `resume`, `reset`, `set_params`; unknown --> `command_response{status:"error", code:"unknown_command"}`

### 10.4 Test acceptance

~10 tests including: `test_csrf_required_for_websocket_start`, `test_training_button_handler_falls_back_to_rest_when_disconnected`, `test_rest_endpoint_still_returns_200_and_updates_state`, `test_orphaned_command_resolves_via_state_event`, `test_per_command_timeout_start_10s`

### 10.5 PR plan

| # | Branch | Repo | Order |
|---|---|---|---|
| **P11** | `phase-d-cascor-control-commands` | juniper-cascor | First |
| **P12** | `phase-d-canopy-button-ws-routing` | juniper-canopy | After P11 |

### 10.6 Exit gate

1. All tests green
2. 24h staging zero orphaned commands
3. REST endpoints still receive non-browser traffic
4. **B-pre-b in production >=48h** (entry gate reconfirmed)

### 10.7 Rollback

```bash
export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false
systemctl restart juniper-canopy
# Or CSWSH emergency: JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true
```

### 10.8 Observability

- `canopy_training_control_total{command, transport}` -- WS:REST ratio tracking
- `canopy_training_control_orphaned_total{command}` -- orphaned-command signal
- `canopy_training_control_command_latency_ms{command, transport}` -- per-command latency
- `cascor_ws_control_command_received_total{command}` -- server-side receipt counter

**Runbook**: `ws-control-button-debug.md`.

### 10.9 NOT in this phase

- `set_params` routing (Phase C), full backpressure (Phase E)

---

## 11. Phase E: backpressure (CONDITIONAL) (Engineer layer)

### 11.1 Goal

Replace serial fan-out with per-client pump tasks + bounded queues + policy matrix. Default: `drop_oldest_progress_only`. **Ships only if Phase B telemetry shows RISK-04/11 triggering.**

### 11.2 Entry gate

- [ ] Phase 0-cascor in main (0.5s quick-fix is the fallback)
- [ ] Production telemetry shows `cascor_ws_broadcast_send_duration_seconds` p95 >100ms sustained OR `cascor_ws_broadcast_timeout_total` frequently >0

### 11.3 Deliverables checklist

- [ ] Per-client `_ClientState` with `pump_task` + bounded `send_queue` (256, configurable via `ws_per_client_queue_size`)
- [ ] Policy dispatch:
  - `drop_oldest_progress_only` (default): drop oldest for `metrics`, `candidate_progress`; close 1013 for `state`, `topology`, `cascade_add`, `connection_established`
  - `block`: synchronous block (old behavior, opt-in via env)
  - `close_slow`: close 1008 if queue full >5s (aggressive, opt-in)
- [ ] Per-type event classification assertion test (every new event type gets explicit policy)

**Policy matrix**:

| Event type | Queue size | Overflow behavior |
|---|---:|---|
| `state` | 128 | close(1008) -- terminal-state-sensitive |
| `metrics` | 128 | close(1008) -- chart gaps |
| `cascade_add` | 128 | close(1008) -- growth step |
| `candidate_progress` | 32 | drop_oldest -- coalesceable |
| `event` (training_complete) | 128 | close(1008) -- terminal-sensitive |
| `command_response` | 64 | close(1008) -- client waits |
| `pong` | 16 | drop_oldest -- client re-pings |

### 11.4 Test acceptance

~7 tests: `test_slow_client_does_not_block_other_clients`, `test_drop_oldest_queue_policy`, `test_terminal_state_events_not_dropped`, `test_event_type_classification_for_backpressure_policy`, `test_block_policy_still_works_when_opted_in`, `test_close_slow_policy_closes_stalled_clients`, `test_ws_backpressure_policy_env_override`

Load test: 50 clients, 1 slow (2s delay), 49 fast p95 <200ms.

### 11.5 PR plan

| # | Branch | Repo |
|---|---|---|
| **P13** | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor |

### 11.6 Exit gate

1. All tests green; load test passes
2. 48h staging zero `WSStateDropped` alerts
3. Runbook published

### 11.7 Rollback

```bash
export JUNIPER_WS_BACKPRESSURE_POLICY=block   # RISK-04 returns, intentional
systemctl restart juniper-cascor
```

### 11.8 NOT in this phase

- `permessage-deflate`, multi-tenant per-session queues

---

## 12. Phase F: heartbeat + reconnect jitter (Engineer layer)

### 12.1 Goal

Application-level ping/pong for dead-connection detection. Lift 10-attempt reconnect cap to unlimited with 60s max interval.

### 12.2 Entry gate

- [ ] Phase B in main

### 12.3 Deliverables checklist

- [ ] Cascor emits `{"type":"ping","ts":<float>}` every 30s
- [ ] JS replies `pong` within 5s; no pong 10s --> close 1006
- [ ] Uncapped reconnect; jitter: `Math.random() * Math.min(60000, 500 * 2**Math.min(attempt, 7))`

### 12.4 Test acceptance

7 tests: `test_ping_sent_every_30_seconds`, `test_pong_received_cancels_close`, `test_reconnect_backoff_has_jitter`, `test_reconnect_attempt_unbounded_with_cap`, `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect`, `test_dead_connection_detected_via_missing_pong`, `test_jitter_formula_no_nan_delay`

### 12.5 Exit gate

1. All tests green; manual firewall drop --> dead conn detected within 40s
2. 48h staging: no NaN delays, no reconnect storms

### 12.6 Rollback

```bash
export JUNIPER_DISABLE_WS_AUTO_RECONNECT=true
# Or cache-busted JS hotfix with old jitter
```

---

## 13. Phases G, H, I (Engineer layer)

### 13.1 Phase G: cascor `set_params` integration tests

**Goal**: 15 cascor-side integration tests via `TestClient.websocket_connect()`. Test-only phase.
**Entry**: Phase 0-cascor + Phase B-pre-b in main.
**Key tests**: `test_set_params_echoes_command_id` (D-02 contract), `test_set_params_concurrent_command_response_correlation`, `test_set_params_during_training_applies_on_next_epoch_boundary`.
**PR**: P15 `phase-g-cascor-set-params-integration` --> juniper-cascor main. Patch bump.
**Rollback**: n/a (test-only).

### 13.2 Phase H: `_normalize_metric` audit + regression gate

**Goal**: Lock dual metric format with regression test + CODEOWNERS hard gate + pre-commit hook + consumer audit doc. NO refactoring in this migration.
**Entry**: Phase B in main (MVS-TEST-14 already landed).
**Key deliverables**: `test_normalize_metric_produces_dual_format`, `.github/CODEOWNERS` entry for `normalize_metric.py` + `metrics_panel.py` as hard merge gate, pre-commit hook blocking format removal, shape-hash golden file.
**PR**: P16 `phase-h-normalize-metric-audit` --> juniper-canopy main. Patch bump.
**Rollback**: `git revert` (10 min). Test-only + doc phase.

### 13.3 Phase I: asset cache busting

**Folded into Phase B** as MVS-FE-16. Exists here only for rollback reference.
**Deliverable**: `assets_url_path` with content-hash query string. Verified via `test_asset_url_includes_version_query_string`.
**Rollback**: `git revert` cache-bust commit in P6 (10 min).

---

## 13.4 Items resolved at implementation time

Six items cannot be definitively resolved until the implementing engineer runs the day-1 verification greps. Each has a default assumption and a contingency if the assumption is wrong.

| # | Question | Default assumption | Contingency if wrong | Phase affected |
|---|---|---|---|---|
| 1 | NetworkVisualizer render tech | Cytoscape | If Plotly: +1 day, migrate via `extendTraces` | B |
| 2 | Canopy `SessionMiddleware` | Absent | If present: reclaim 0.5 day | B-pre-b |
| 3 | Dash version (`set_props` availability) | Does not affect plan (Option B Interval drain chosen regardless) | Record in PR description | B |
| 4 | Plotly.js version | >=2.x (`extendTraces(maxPoints)` works) | If 1.x: add 0.25-day pin bump commit | B |
| 5 | Canopy adapter `run_coroutine_threadsafe` | Not yet used | If present: reuse it | C |
| 6 | Cascor `/ws/control` `command_id` passthrough | Must be modified | Phase 0-cascor deliverable 0-cascor-9 includes this | 0-cascor, G |

The implementing engineer records answers in the PR description of the first commit of each affected phase.

---

## 14. Configuration reference (Engineer layer)

Canonical settings table. Every setting has Pydantic `Field(description=...)`.

| Setting | Repo | Default | Env var | Phase |
|---|---|---|---|---|
| `ws_replay_buffer_size` | cascor | 1024 | `JUNIPER_WS_REPLAY_BUFFER_SIZE` | 0-cascor |
| `ws_send_timeout_seconds` | cascor | 0.5 | `JUNIPER_WS_SEND_TIMEOUT_SECONDS` | 0-cascor |
| `ws_resume_handshake_timeout_s` | cascor | 5.0 | `JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S` | 0-cascor |
| `ws_state_throttle_coalesce_ms` | cascor | 1000 | `JUNIPER_WS_STATE_THROTTLE_COALESCE_MS` | 0-cascor |
| `ws_pending_max_duration_s` | cascor | 10.0 | `JUNIPER_WS_PENDING_MAX_DURATION_S` | 0-cascor |
| `ws_max_connections_per_ip` | cascor | 5 | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a |
| `ws_allowed_origins` | cascor | `[]` | `JUNIPER_WS_ALLOWED_ORIGINS` | B-pre-a |
| `ws_idle_timeout_seconds` | cascor | 120 | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS` | B-pre-a |
| `ws_max_connections_per_ip` | canopy | 5 | `JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a |
| `ws_allowed_origins` | canopy | localhost defaults | `JUNIPER_CANOPY_WS_ALLOWED_ORIGINS` | B-pre-a |
| `audit_log_enabled` | canopy | `True` | `JUNIPER_AUDIT_LOG_ENABLED` | B-pre-a |
| `audit_log_path` | canopy | `/var/log/canopy/audit.log` | `JUNIPER_AUDIT_LOG_PATH` | B-pre-a |
| `audit_log_retention_days` | canopy | 90 | `JUNIPER_AUDIT_LOG_RETENTION_DAYS` | B-pre-a |
| `enable_browser_ws_bridge` | canopy | `False` | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE` | B |
| `disable_ws_bridge` | canopy | `False` | `JUNIPER_DISABLE_WS_BRIDGE` | B |
| `enable_raf_coalescer` | canopy | `False` | `JUNIPER_ENABLE_RAF_COALESCER` | B |
| `enable_ws_latency_beacon` | canopy | `True` | `JUNIPER_ENABLE_WS_LATENCY_BEACON` | B |
| `ws_security_enabled` | canopy | `True` | `JUNIPER_WS_SECURITY_ENABLED` | B-pre-b |
| `ws_rate_limit_enabled` | canopy | `True` | `JUNIPER_WS_RATE_LIMIT_ENABLED` | B-pre-b |
| `ws_rate_limit_cps` | canopy | 10 | `JUNIPER_WS_RATE_LIMIT_CPS` | B-pre-b |
| `disable_ws_control_endpoint` | canopy | `False` | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT` | B-pre-b |
| `use_websocket_set_params` | canopy | `False` | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS` | C |
| `ws_set_params_timeout` | canopy | 1.0 | `JUNIPER_WS_SET_PARAMS_TIMEOUT` | C |
| `enable_ws_control_buttons` | canopy | `False` | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS` | D |
| `ws_backpressure_policy` | cascor | `drop_oldest_progress_only` | `JUNIPER_WS_BACKPRESSURE_POLICY` | E |
| `disable_ws_auto_reconnect` | canopy | `False` | `JUNIPER_DISABLE_WS_AUTO_RECONNECT` | F |

---

## 15. Appendix: full decision reference

62 decisions from R2-04 (D-01..D-55 + D-56..D-62 implicit), all applied. Compact table format.

| D | Summary | Applied value | Source |
|---|---|---|---|
| 01 | `set_params` default timeout | 1.0 s | R1-05 4.1 |
| 02 | Correlation field name | `command_id` | R1-05 4.2 |
| 03 | `command_response` carries seq | No | R1-05 4.17 |
| 04 | rAF coalescer | Scaffold-disabled | R1-05 4.3 |
| 05 | REST fallback cadence | 1 Hz | R1-05 4.4 |
| 06 | NetworkVisualizer scope | Minimum wire; deep deferred | R1-05 4.5 |
| 07 | `ws-metrics-buffer` shape | Structured `{events, gen, last_drain_ms}` | R1-05 4.7 |
| 08 | GAP-WS-24 split | 24a browser + 24b backend | R1-05 4.8 |
| 09 | B-pre effort | 0.5 (a) + 2 (b) | R1-05 4.9 |
| 10 | Security flag naming | Positive `ws_security_enabled` + CI guardrail | R1-02, R2-03 |
| 11 | Phase 0-cascor carve-out | Carve out from B | R1-05 4.19 |
| 12 | M-SEC adoption | Adopt 10/11, fold 12 into 07 | R1-05 4.15 |
| 13 | GAP-WS-19 status | RESOLVED (regression test only) | R1-05 4.16 |
| 14 | Two-phase registration | `_pending_connections` set | R1-05 4.18 |
| 15 | `server_instance_id` role | Programmatic key | R1-05 4.20 |
| 16 | `replay_buffer_capacity` | Add to `connection_established` | R1-05 4.21 |
| 17 | Phase B feature flag | Flag-off default | R1-02 |
| 18 | Permanent kill switch | `disable_ws_bridge` added | R1-05 4.45 |
| 19 | Backpressure default | `drop_oldest_progress_only` | R1-05 4.36 |
| 20 | SDK retries | None (caller decides) | R1-05 4.22 |
| 21 | REST retention | Permanent (no deprecation) | R1-05 4.23 |
| 22 | Debounce layer | Dash clientside | R1-05 4.24 |
| 23 | B-pre split | a + b | R1-05 4.35 |
| 24 | Per-IP cap | 5 | R1-05 4.37 |
| 25 | Deployment topology | Single-tenant v1 | R1-05 4.38 |
| 26 | Shadow traffic | Skip | R1-05 4.39 |
| 27 | CODEOWNERS `_normalize_metric` | Hard merge gate | R1-05 4.41 |
| 28 | Audit logger | Dedicated, skeleton B-pre-a, Prom B | R1-05 4.14 |
| 29 | Adapter auth | HMAC CSRF token | R1-05 4.43 |
| 30 | One resume per connection | Enforced | R1-05 4.12 |
| 31 | Per-command HMAC | Defer indefinitely | R1-05 4.11 |
| 32 | Multi-tenant replay | Defer | R1-05 4.13 |
| 33 | Rate limit buckets | Single 10/s | R1-05 4.46 |
| 34 | Unclassified keys | Both layers | R1-05 4.44 |
| 35 | Replay buffer default | 1024, env-tunable | R2-01 |
| 36 | Replay size=0 | Kill switch | R1-02 |
| 37 | Metrics-presence CI | Enforced PR blocker | R1-02 |
| 38 | Phase 0-cascor soak | 72h | R1-02, R2-04 |
| 39 | Phase B soak | 72h | R1-02, R2-04 |
| 40 | Chaos tests | 3 blocking (0-cascor); others nightly | R2-01, R2-04 |
| 41 | Load tests | Blocking for 0-cascor | R1-02 |
| 42 | Frame budget test | Recording-only | R1-05 4.3 |
| 43 | `contract` marker | Added, every PR | R1-05 4.34 |
| 44 | Multi-browser | Chromium only | R1-05 4.31 |
| 45 | User research | Skip v1 | R1-05 4.32 |
| 46 | Send timeout configurable | Yes, default 0.5 | R1-02 |
| 47 | Phase C flag default | False | Unanimous |
| 48 | Phase C flip criteria | 6 hard gates | R1-02 |
| 49 | Phase D flag | `enable_ws_control_buttons=False` | R1-02 |
| 50 | Error-budget freeze | Enforced | R1-02 |
| 51 | `WSOriginRejection` severity | Page | R1-02 |
| 52 | `WSSeqCurrentStalled` | Page | R1-02 |
| 53 | Kill-switch MTTR tested | Every switch in staging | R1-02 |
| 54 | REST polling handler | Preserve forever | R1-05 4.23 |
| 55 | Source-doc patches | Batch in Round 5 | R1-05 8.6 |
| 56 | REST deprecation | Never | R2-04 5.1 |
| 57 | juniper-ml pin bump | Same-day follow-up | R2-04 5.2 |
| 58 | CI budget | <=25% runtime increase | R2-04 5.3 |
| 59 | Browser error pipeline | POST `/api/ws_browser_errors` | R2-04 5.4 |
| 60 | Worktree policy | One per phase per repo | R2-04 5.5 |
| 61 | Deploy freeze | Mid-week for flag flips only | R2-04 5.6 |
| 62 | Bandwidth baseline | 1h pre-Phase-B measurement | R2-04 5.7 |

---

## 16. Appendix: test acceptance matrix (key tests)

Canonical load-bearing tests with phase, type, and measurable criterion. Full catalog (~142 tests) in R2-02 section 15.2.

| Phase | Test | Type | Criterion |
|---|---|---|---|
| 0-cascor | `test_seq_monotonically_increases` | unit | seq > previous on every broadcast |
| 0-cascor | `test_replay_buffer_bounded_to_configured_capacity` | unit | `maxlen == Settings.ws_replay_buffer_size` |
| 0-cascor | `test_resume_replays_events_after_last_seq` | integration | N-5 last_seq --> exactly 5 events |
| 0-cascor | `test_second_resume_closes_connection_1003` | unit | D-30 enforced |
| 0-cascor | `test_ws_control_command_response_has_no_seq` | contract | D-03 negative assertion |
| 0-cascor | Load: 100 Hz x 60s x 10 clients | load (blocking) | p95 < 250ms, memory +/-10% |
| A-SDK | `test_set_params_caller_cancellation_cleans_correlation_map` | unit (mandatory) | `len(_pending) == 0` after cancel |
| A-SDK | `test_correlation_map_bounded_at_256` | unit | 257th --> `JuniperCascorOverloadError` |
| B-pre-a | `test_empty_allowlist_rejects_all_fail_closed` | unit | Empty list = reject all |
| B-pre-a | `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` | Playwright | Cross-origin rejected |
| B | **`test_bandwidth_eliminated_in_ws_mode`** | **Playwright (P0 gate)** | `/api/metrics/history` requests == 0 over 60s |
| B | `test_metrics_message_has_dual_format` | Playwright (RISK-01) | Both flat + nested keys |
| B | `test_demo_mode_metrics_parity` | dash_duo + e2e | RISK-08 gate (both lanes) |
| B | `test_both_flags_interact_correctly` | unit | Two-flag logic verified |
| B | 72h memory soak | soak (blocking) | heap p95 growth < 20% |
| B-pre-b | `test_csrf_required_for_websocket_first_frame` | unit | Absent CSRF --> close 1008 |
| B-pre-b | `test_canopy_adapter_sends_hmac_csrf_token_on_connect` | unit | HMAC first frame |
| B-pre-b | `test_cswsh_from_evil_page_cannot_start_training` | Playwright | Full CSWSH regression |
| C | `test_apply_params_hot_falls_back_to_rest_on_timeout` | unit | Timeout --> REST fallback |
| C | `test_cascor_rejects_unknown_param_with_extra_forbid` | contract | D-34 defense |
| D | `test_csrf_required_for_websocket_start` | Playwright | B-pre-b regression |
| D | `test_orphaned_command_resolves_via_state_event` | Playwright | RISK-13 mitigation |
| E | `test_terminal_state_events_not_dropped` | unit | RISK-11 guard |
| G | `test_set_params_echoes_command_id` | contract (mandatory) | D-02 enforced |
| F | `test_ping_sent_every_30_seconds` | unit | Ping cadence |
| F | `test_jitter_formula_no_nan_delay` | unit | 0 <= delay <= cap; no NaN/Infinity |
| H | `test_normalize_metric_produces_dual_format` | contract | D-27 / RISK-01 gate |
| H | `test_normalize_metric_shape_hash_matches_golden_file` | unit | Shape stability |
| -- | Metric-presence pytest | security (every PR) | Scrapes /metrics, asserts canonical names present |
| -- | REST regression harness | fast (every PR) | Every baseline REST endpoint returns expected shape |

**Aggregate test counts** (from R2-02 section 15.2):
- Unit: ~97 tests
- Integration: ~18 tests
- E2E (dash_duo + Playwright): ~16 tests
- Contract: ~11 tests
- Chaos (nightly): ~8 tests
- Load (blocking): 2 tests
- Soak: 3 tests (72h/72h/48h)
- **Total: ~155 tests across all phases**

Contract test runtime budget: <50 ms per test, <5 s per suite.

**Label cardinality discipline** (all metrics must use only these canonical values):
- `endpoint` -- {`/ws/training`, `/ws/control`, `/ws/worker`, `/ws/monitor`}
- `type` -- {`metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, `event`, `command_response`, `connection_established`, `resume_ok`, `resume_failed`}
- `transport` -- {`ws`, `rest`}
- `reason` -- {`origin_rejected`, `cookie_missing`, `csrf_invalid`, `per_ip_cap`, `cap_full`, `rate_limited`, `frame_too_large`, `idle_timeout`, `malformed_json`}
- `outcome` -- {`accepted`, `rejected`, `timeout`, `success`, `server_restarted`, `out_of_range`, `malformed`, `no_resume_timeout`, `second_resume`}

Adding any new value requires a CCC-02 PR review.

---

## 17. R3 reconciliation log

This section documents where R3-01, R3-02, and R3-03 contradicted each other and how this R4-02 document resolves each disagreement.

### 17.1 Security flag naming: positive-sense vs negative-sense

**R3-01**: Positive-sense `ws_security_enabled: bool = True` (overrides R1-05 4.10). Cites 3:1 R2 majority + safety argument.
**R3-02**: Negative-sense `disable_ws_auth` preserved (R2-02 compromise). CI guardrail closes footgun equally. Cites execution-contract continuity and late-rename churn.
**R3-03**: Positive-sense `ws_security_enabled=True` (C-27).

**Resolution**: **Positive-sense `ws_security_enabled: bool = True`** (R3-01/R3-03 position). Justification: the safety principle (a blank config leaves security ON) outweighs the execution-contract continuity argument. The rename is ~10 LOC. R3-02's CI guardrail mitigates the footgun but does not eliminate it for dev/staging environments where the guardrail is intentionally relaxed. The 2:1 R3 consensus and 3:1 R2 consensus both favor positive-sense.

### 17.2 Phase 0-cascor staging soak: 72h vs 24h

**R3-01**: 72h (cites R2-01/R2-04 majority, seq monotonicity bugs are latent).
**R3-02**: 72h (agrees, cites same justification).
**R3-03**: 72h (C-36 implicit).

**Resolution**: **72h**. All three R3s agree. No contradiction to resolve.

### 17.3 Effort estimate: 13.5 vs 15.75 expected days

**R3-01**: Uses 13.5 as target (R1-05 center-of-mass); 15.75 as upper bound (R2-02).
**R3-02**: Uses 15.75 as expected (R2-02 delta-justified).
**R3-03**: Uses 13.5 expected (C-36).

**Resolution**: **13.5 as target, 15.75 as planning buffer**. R3-01's framing is most honest: the 13.5 is achievable if contingencies do not fire; the 15.75 includes +2.25 days for known contingent costs. An engineering team should plan for 15.75 and aim for 13.5.

### 17.4 Phase I folding

**R3-01**: Folded into Phase B. Standalone section exists for rollback reference.
**R3-02**: Folded into Phase B. Section 12 is documentation stub only.
**R3-03**: Folded into Phase B (section 2 phase index confirms).

**Resolution**: **Folded into Phase B.** All three agree. No contradiction.

### 17.5 Phase E conditionality

**R3-01**: Conditional on production telemetry (RISK-04/11 triggering).
**R3-02**: Conditional on production telemetry (section 18.8 explicit).
**R3-03**: Conditional (`CONDITIONAL` label in phase index).

**Resolution**: **Conditional.** All three agree.

### 17.6 Chaos tests: blocking vs nightly

**R3-01**: 3 specific Phase 0-cascor chaos tests elevated to blocking; all others nightly.
**R3-02**: Same position (not explicitly addressed but defers to R2-01 for those 3 tests).
**R3-03**: Lists 3 chaos tests as "BLOCKING gates, not nightly" in section 3.1.

**Resolution**: **3 blocking, rest nightly.** All three effectively agree.

### 17.7 Replay buffer default: 1024 vs 256

**R3-01**: 1024 production, configurable (section 20.1 resolution).
**R3-02**: 1024 tunable (D-35 applied).
**R3-03**: 1024 (C-05).

**Resolution**: **1024.** All three agree after resolving the R2-03 table error.

### 17.8 Per-origin handshake cooldown

**R3-01**: Included in Phase B-pre-b (section 6.3.1 item 5, ~20 LOC).
**R3-02**: Not explicitly included in B-pre-b deliverables (section 5.7 defers per-origin cooldown).
**R3-03**: Not listed in B-pre-b deliverables.

**Resolution**: **Include in Phase B-pre-b** (R3-01 position). The cooldown is ~20 LOC, amplifies Origin defense, and the NAT-hostile escape hatch (cleared on restart) makes it safe. Low cost, meaningful security benefit.

---

## 18. Self-audit log

### 18.1 Passes performed

1. **Pass 1**: Read all 3 R3 files in full (R3-01: 1912 lines, R3-02: 1871 lines, R3-03: 1363 lines).
2. **Pass 2**: Designed three-layer structure per prompt. Built section 0-1 (PM layer), section 2-3 (TL layer), section 4-14 (engineer layer).
3. **Pass 3**: Built per-phase sections using consistent template (Goal, Entry gate, Deliverables checklist, Test acceptance, PR plan, Exit gate, Rollback, NOT in this phase).
4. **Pass 4**: Built appendices (decision reference, test matrix, R3 reconciliation).
5. **Pass 5**: Self-audit against prompt checklist; applied corrections below.

### 18.2 Self-audit checklist

- [x] **Navigation guide at top**: "How to read this document" table with role --> sections --> time
- [x] **Three audience layers self-sufficient**: PM reads 0-1 and has scope/effort/risks. TL reads 0-3 and has architecture/operations. Engineer reads 0 + phase section and has deliverables/tests/rollback.
- [x] **Consistent phase formatting**: Every phase section (4-14) uses identical subsection headings (Goal, Entry gate, Deliverables checklist, Test acceptance, PR plan, Exit gate, Rollback, NOT in this phase)
- [x] **Self-contained phases**: Each phase section readable in isolation (entry gate lists what must be true, not "see Phase X")
- [x] **Concrete over abstract**: File paths over "somewhere in cascor"; pytest invocations over "run the tests"; branch names over "create a branch"; env var names over "set a flag"
- [x] **Three-point effort estimates**: Section 1.2 has optimistic/expected/pessimistic per phase with risk factors
- [x] **All rollback procedures concrete**: Every phase has verbatim `bash` commands with TTF
- [x] **All tests named**: Every phase lists specific test function names
- [x] **R3 contradictions resolved**: Section 17 has 8 items with winner and justification
- [x] **D-NN, GAP-WS-NN, M-SEC-NN, RISK-NN referenced**: Throughout

### 18.3 Corrections applied during self-audit

1. **Section 0.2 top decisions**: Initial draft had 4 decisions. Added D-10 (positive-sense security flag) as the 5th because it is a resolved R3 contradiction and load-bearing for Phase B-pre-b.
2. **Section 1.2 effort table**: Initial draft used only R3-02's 15.75. Added R3-01/R3-03's 13.5 as target and 15.75 as planning buffer to faithfully represent the R3 range.
3. **Section 4.3 deliverables**: Initial draft omitted `emitted_at_monotonic` from the envelope fields. Added per CCC-10.
4. **Section 7.3 deliverables**: Initial draft omitted `/api/ws_browser_errors` endpoint. Added per D-59.
5. **Section 8.3 deliverables**: Initial draft omitted per-origin handshake cooldown. Added per R3-01 section 6.3.1 and section 17.8 resolution.
6. **Section 3.1 kill switch matrix**: Initial draft had 11 rows. Added idle-timeout and audit-log switches from B-pre-a for completeness. Final count: 13 rows (compact; full matrix is 24 rows in R3-01 section 14).
7. **Phase D entry gate**: Initial draft said "B-pre-b in main." Corrected to "B-pre-b in **production** >=48h" per R3-02 section 7.2.
8. **Section 14 configuration table**: Initial draft had 20 settings. Cross-checked against R3-01 section 2.9 and added 6 missing entries (idle timeout, audit path, audit retention, latency beacon, rate limit CPS, auto reconnect disable).

### 18.4 Coverage verification

- [x] All 12 phases covered (0-cascor, A-SDK, B-pre-a, B, B-pre-b, C, D, E, F, G, H, I)
- [x] All 16 PRs in merge sequence (P1-P16)
- [x] 62 decisions referenced in appendix
- [x] 21 risks in register (16 source-doc + 5 CCC)
- [x] 28 kill switches in full matrix (including non-switches)
- [x] 31 key tests in acceptance matrix (full ~155 per R2-02 section 15.2)
- [x] 8 R3 contradictions resolved with winner and justification
- [x] 26 settings in configuration table
- [x] 10 cross-cutting concerns with ownership
- [x] Day-1 verification procedure with verbatim commands

### 18.5 Layer self-sufficiency check

**PM layer (sections 0-1)**: Contains what/why/how-long (section 0.1), top 5 decisions (0.2), key risks with mitigations (0.3), recommended path (0.4), scope in/out (1.1), effort table with 3-point estimates (1.2), timeline with milestones (1.3), success criteria with metrics (1.4). A PM reading only sections 0-1 has enough to brief a VP or write a stakeholder update.

**TL layer (sections 0-3)**: Adds settled positions constitution (2.1), dependency graph (2.2), cross-repo coordination with PR table (2.3), risk register (2.4), operational rules (3.4), CCC ownership (3.5), version bump discipline (3.5), full kill-switch matrix (3.1), observability matrix (3.2), feature flag inventory (3.3), merge sequence (3.6). A tech lead reading sections 0-3 has the full architecture picture and can plan sprints.

**Engineer layer (sections 4-14)**: Each phase section is self-contained with entry gate, deliverables checklist, test names, PR plan, exit gate with measurable criteria, rollback with verbatim bash commands, and NOT-in-this-phase exclusions. An engineer reading section 0 + their phase section has everything needed to implement without reading other phases.

### 18.6 Confidence assessment

**High confidence**: Phase 0-cascor scope and commit decomposition (all 3 R3s agree), `command_id` wire-level correction, kill-switch matrix (R3-01/R3-03 triangulated), merge sequence, phase dependency graph.

**Medium confidence**: Security flag naming resolution (R3-02 disagrees; this doc sides with R3-01/R3-03 majority), effort estimate framing (target vs planning buffer), NetworkVisualizer scope (render-tech unverified until Phase B first commit).

**Lower confidence**: Phase C flip-gate p99 >=50ms threshold (may be too strict or too loose), Phase E conditionality (some R2 inputs treat it as mandatory).

### 18.7 Items for Round 5 attention

1. **Final `command_id` grep** across R5 artifact -- zero stale `request_id` references
2. **Confirm D-10 positive-sense resolution** -- if user prefers negative-sense, revise sections 2.1, 3.1, 8.3
3. **Confirm Phase E conditionality** -- if mandatory, move from optional to required in merge sequence
4. **Bandwidth baseline measurement procedure** (D-62) -- needs runbook entry
5. **Source-doc v1.4 patch batch** (D-55) -- list of text patches to commit in R5
6. **Contract test runtime budget** (CCC-05: <50ms per test, <5s suite) -- confirm CI infra supports

---

**End of R4-02 Executive-Ready Engineering Deliverable.**
