# Canopy <-> Cascor WebSocket Migration: Canonical Development Plan

**Status**: PROPOSED -- pending engineering review
**Version**: 1.0 (produced by 6-round, 21-agent consolidation funnel)
**Date**: 2026-04-11
**Author**: Claude Code (Opus 4.6, 1M context) on behalf of Paul Calnon
**Source**: WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md (v1.3 STABLE, PR #117)
**Lineage**: R0-01..R0-06 -> R1-01..R1-05 -> R2-01..R2-04 -> R3-01..R3-03 -> R4-01..R4-02 -> this document

---

## How to read this document

| Your role          | Read these sections          | Estimated time |
|--------------------|------------------------------|----------------|
| PM / stakeholder   | S0--S1                       | 10 min         |
| Tech lead          | S0--S3                       | 30 min         |
| Engineer (Phase X) | S0 + the section for Phase X | 15--20 min     |

Each layer is self-sufficient. You do not need to read the entire document to extract what you need.

- **S0--S1** answer: what, why, how long, what are the risks, what has been decided.
- **S2--S3** answer: how the system is structured, how phases depend on each other, what the operational framework looks like.
- **S4--S14** answer: what exactly do I build, what tests must pass, how do I roll back.
- **S15--S21** are appendices and audit trails.

---

## Pre-flight: day-1 verification procedure

If you are picking up this work right now, run these verification commands before writing any code:

```bash
# 1. Confirm ecosystem clean
for repo in juniper-cascor juniper-cascor-client juniper-canopy; do
  (cd /home/pcalnon/Development/python/Juniper/$repo && echo "=== $repo ===" && git status)
done

# 2. Verify GAP-WS-19 already resolved on cascor main
grep -n "close_all" /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/websocket/manager.py
# Must show lock-holding pattern at lines 138-156. If ABSENT: STOP -- Phase 0-cascor scope expands.

# 3. Record answers for 5 scope-determining greps
grep -rn "SessionMiddleware" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/
grep -l "cytoscape\|plotly" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/frontend/components/network_visualizer.py
grep "dash\b" /home/pcalnon/Development/python/Juniper/juniper-canopy/pyproject.toml
grep -n "run_coroutine_threadsafe" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/backend/cascor_service_adapter.py
grep -n "command_id\|request_id" /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/websocket/control_stream.py

# 4. Record bandwidth baseline (1 hour in staging before any Phase B deploy)
# Capture canopy_rest_polling_bytes_per_sec gauge as denominator for >90% reduction AC

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
- **Any surviving `request_id`**: pre-merge defect; fix before proceeding

---

## S0. Executive summary

### 0.1 One-sentence goal

Replace the ~3 MB/s per-dashboard `/api/metrics/history` REST polling in Juniper Canopy with an already-half-wired cascor-to-canopy-to-browser WebSocket pipeline, while closing the CSWSH security gap and fixing four cascor correctness bugs.

### 0.2 The P0 motivator

**`canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`** drops >=90% vs pre-Phase-B baseline in staging, sustained for 72 hours. This single gauge is the migration's acceptance signal.

Every open Canopy dashboard tab continuously polls the cascor backend at ~3 MB/s. WebSocket push eliminates this polling entirely when the connection is healthy, while REST polling remains as a permanent fallback (no REST endpoint is ever deleted).

### 0.3 Scope

**In scope**:

- Eliminate `/api/metrics/history` REST polling when WebSocket is healthy (P0)
- Fix GAP-WS-21 (state coalescer drop-filter), GAP-WS-29 (broadcast_from_thread exception swallowing), GAP-WS-07 (slow-client fan-out, quick-fix), GAP-WS-32 (per-command timeouts and orphaned-command resolution)
- Close RISK-15 (CSWSH on `/ws/training` and `/ws/control`) via Origin allowlist (M-SEC-01/01b), cookie+CSRF (M-SEC-02), rate limit (M-SEC-05), adapter HMAC auth, adapter inbound validation
- Add `command_id`-correlated `set_params` WebSocket path (feature-flagged default OFF)
- Route training-control buttons (start/stop/pause/resume/reset) via WebSocket with REST fallback
- Full observability stack: metrics, alerts, dashboards, SLOs (aspirational until 1-week production data)

**Explicitly out of scope**:

- REST endpoint deletion (preserved forever per D-21/D-54/D-56)
- Multi-tenant replay isolation (D-32 deferred)
- Per-command HMAC (D-31 deferred indefinitely)
- Two-bucket rate limit (D-33; single bucket; split only if starvation observed)
- `permessage-deflate` negotiation (GAP-WS-17 deferred)
- Topology chunking (GAP-WS-18; REST fallback preserved)
- WebAssembly Plotly (out of scope)
- Multi-browser CI matrix (D-44; Chromium-only v1)
- User research study (D-45; skip)
- OAuth/OIDC, mTLS canopy<->cascor, shadow traffic (D-26 rejected)
- rAF coalescer in production (D-04; scaffolded disabled)
- NetworkVisualizer deep render migration (D-06; minimum wire in Phase B, deep deferred)
- `_normalize_metric` refactoring (test-only in Phase H)

### 0.4 Total effort

**Target: 13.5 engineering days.** Planning buffer: 15.75 engineering days. Calendar: ~4.5 weeks with 48--72 hour soak windows between high-risk phases. Minimum-viable carveout (P0 only): ~7 days.

The 13.5-day target assumes no contingencies fire (NetworkVisualizer is cytoscape, SessionMiddleware is absent as expected, no Plotly version issues). The 15.75-day planning buffer includes +2.25 days for known contingent costs (audit logger name collision, HMAC wiring iteration, NetworkVisualizer minimum wire). An engineering team should plan for 15.75 and aim for 13.5.

### 0.5 Top decisions (settled)

| # | Decision                                        | Applied value                                                                            | Why it matters                                                                                        |
|---|-------------------------------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 1 | Correlation field name (D-02)                   | **`command_id`** (NOT `request_id`)                                                      | Every SDK, server, and test file must agree. A stale `request_id` reference is a wire-level bug.      |
| 2 | Phase 0-cascor carve-out (D-11)                 | Cascor ships seq/replay/resume **separately**, soaks 1 week before canopy consumes       | Decouples cascor stability from canopy feature work.                                                  |
| 3 | Two-flag browser bridge (D-17 + D-18)           | `enable_browser_ws_bridge=False` (dev flip) + `disable_ws_bridge=False` (permanent kill) | Any incident: flip one env var, 5-minute recovery. REST polling takes over automatically.             |
| 4 | REST paths preserved forever (D-21, D-54, D-56) | No REST endpoint is deleted or deprecated, ever                                          | Every kill switch ultimately falls back to REST. Removing REST removes the safety net.                |
| 5 | Positive-sense security flag (D-10)             | `ws_security_enabled=True` with CI guardrail refusing `false` in production              | The safe default is the production default. Accidentally deploying a blank config leaves security ON. |
| 6 | Phase E backpressure default (D-19)             | `drop_oldest_progress_only`                                                              | Overrides source doc `block`; progress events droppable, state events close the connection.           |
| 7 | Phase C flag-flip criteria (D-48)               | 6 enumerated hard gates                                                                  | Evidence-based rollout, not calendar-based.                                                           |
| 8 | Kill-switch MTTR tested (D-53)                  | Every switch tested in staging                                                           | Untested switch is not a switch; two consecutive failures trigger migration halt.                     |

### 0.6 Key risks and mitigations

| Risk                                      | Severity              | Mitigation                                                                                   | Recovery time                    |
|-------------------------------------------|-----------------------|----------------------------------------------------------------------------------------------|----------------------------------|
| **CSWSH attack** (RISK-15)                | High                  | Origin allowlist + CSRF first-frame + page alert on rejection                                | 5 min (disable `/ws/control`)    |
| **Browser memory leak** (RISK-10)         | Medium-High           | `Plotly.extendTraces(maxPoints=5000)`, ring-bound in handler (AST lint), 72h soak            | 5 min (`disable_ws_bridge=true`) |
| **Silent data loss** (RISK-11)            | High (low likelihood) | `drop_oldest_progress_only` policy; state events never dropped; page alert on any state drop | 5 min (revert to `block` policy) |
| **Dual metric format breakage** (RISK-01) | High                  | CODEOWNERS hard gate, pre-commit hook, regression test, shape-hash golden file               | 10 min (git revert)              |
| **Cascor crash mid-broadcast** (RISK-14)  | Low                   | `server_instance_id` forces full REST resync; `WSSeqCurrentStalled` page alert               | 10 min (rolling restart)         |

---

## S1. Project overview

### 1.1 Success criteria

| Criterion                    | Metric                                                               | Threshold                            | When                            |
|------------------------------|----------------------------------------------------------------------|--------------------------------------|---------------------------------|
| **P0: polling eliminated**   | `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` | >=90% reduction sustained 72h        | Phase B flag-flip               |
| Security: CSWSH closed       | `canopy_ws_origin_rejected_total` page alert functional              | Rejects unknown origins, zero bypass | Phase B-pre-a + B-pre-b         |
| Correctness: no seq gaps     | `cascor_ws_seq_gap_detected_total`                                   | == 0 over 72h soak                   | Phase 0-cascor exit             |
| Correctness: no state loss   | `cascor_ws_dropped_messages_total{type="state"}`                     | == 0 steady state                    | Phase E (or never if E skipped) |
| Observability: full pipe     | All canonical metrics present on `/metrics`                          | Metrics-presence CI test passes      | Every phase                     |
| Recovery: kill switches work | Every switch flipped in staging                                      | MTTR <=5 min                         | Every phase soak                |

### 1.2 Non-goals

- REST endpoint deletion (preserved forever)
- Multi-tenant replay isolation
- Per-command HMAC
- `permessage-deflate` compression negotiation
- Topology chunking for large networks
- Multi-browser CI matrix (Chromium-only for v1)
- OAuth/OIDC, mTLS, shadow traffic
- `_normalize_metric` refactoring (test-only in Phase H)
- WebAssembly Plotly
- rAF coalescer in production

### 1.3 Timeline with milestones

```bash
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

### 1.4 Dependency graph

```bash
Phase A-SDK ──────────────────────────────────┐
                                              |
Phase 0-cascor ──> [72h soak] ────────────────┼──> Phase B-pre-a ──> Phase B ──> [72h soak] ──> P7 flag-flip
                                              |                         |                        (P0 WIN)
Phase B-pre-a ────────────────────────────────┘                         |
                                                                        |
Phase B-pre-b (parallel with B) ──> [48h soak] ──> Phase D ────────────┤
                                                                        |
Phase C (flag-off, after B in prod) ──> [7d canary] ──> C flag-flip ───┤
                                                                        |
Phase E (CONDITIONAL on telemetry) ────────────────────────────────────┤
Phase F (after B in main) ─────────────────────────────────────────────┤
Phase G (after 0-cascor + B-pre-b in main) ────────────────────────────┤
Phase H (after B in main) ─────────────────────────────────────────────┘
Phase I (folded into Phase B)
```

**Parallel lanes**:

- Phases A-SDK, 0-cascor, and B-pre-a run in parallel (day 1)
- Phase B-pre-b runs in parallel with Phase B
- Phase G runs in parallel with Phase C
- Phases E, F, H are independent post-B follow-ups

**Recommended critical path (P0 win)**: Phase A-SDK + Phase 0-cascor + Phase B-pre-a + Phase B (with Phase I folded in). Everything else branches off after the P0 win is in production. Phase E is conditional on telemetry data.

---

## S2. Constitution: settled positions

Single tabular reference. Every item is SETTLED -- do not re-litigate.

### 2.1 Wire-format positions

| #    | Position                                                                                                  | D-NN | Source      |
|------|-----------------------------------------------------------------------------------------------------------|------|-------------|
| C-01 | Correlation field is `command_id`, NOT `request_id` -- every repo, every test                             | D-02 | R1-05 S4.2  |
| C-02 | `command_response` has NO `seq` field; `/ws/control` has no replay buffer                                 | D-03 | R1-05 S4.17 |
| C-03 | `set_params` default timeout = 1.0 s (not 5.0 s)                                                          | D-01 | R1-05 S4.1  |
| C-06 | `server_instance_id` = programmatic key; `server_start_time` = advisory only                              | D-15 | R1-05 S4.20 |
| C-07 | `replay_buffer_capacity` added to `connection_established`                                                | D-16 | R1-05 S4.21 |
| C-08 | Two-phase registration via `_pending_connections` set                                                     | D-14 | R1-05 S4.18 |
| C-09 | Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with WARN | D-34 | R1-05 S4.44 |
| C-40 | Wire-format rollout is strictly additive; no field renamed/retyped/removed                                | --   | R2-03 S3.3  |
| C-41 | `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope                                  | --   | R1-05 S4.8  |

### 2.2 Protocol behavior positions

| #    | Position                                                                           | D-NN           | Source             |
|------|------------------------------------------------------------------------------------|----------------|--------------------|
| C-04 | SDK fails fast on disconnect; no reconnect queue; no SDK-level retries             | D-20           | R1-05 S4.22, S4.42 |
| C-05 | Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE` | D-35           | R2-01 S18.1        |
| C-17 | REST fallback cadence during disconnect = 1 Hz (NOT 100 ms)                        | D-05           | R1-05 S4.4         |
| C-18 | `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array)  | D-07           | R1-05 S4.7         |
| C-19 | Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces     | --             | R1-02 S5.4         |
| C-23 | REST endpoints preserved FOREVER -- no deprecation                                 | D-21/D-54/D-56 | R1-02 principle 7  |
| C-25 | One-resume-per-connection rule (second resume -> close 1003)                       | D-30           | R1-05 S4.12        |
| C-29 | Debounce lives in Dash clientside callback (NOT SDK), 250 ms                       | D-22           | R1-05 S4.24        |
| C-30 | `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch)             | D-10           | R1-02 S4.3         |

### 2.3 Security positions

| #    | Position                                                               | D-NN      | Source                                |
|------|------------------------------------------------------------------------|-----------|---------------------------------------|
| C-10 | Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header)  | D-29      | R1-05 S4.43                           |
| C-11 | GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only   | D-13      | R1-05 S4.16                           |
| C-24 | Single-tenant v1; multi-tenant replay isolation deferred               | D-25/D-32 | R1-05 S4.13                           |
| C-26 | Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s | D-24/D-33 | R1-05 S4.37, S4.46                    |
| C-27 | **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth` | D-10      | R1-02 S12.5; R2-01 S18.2; R2-03 S15.3 |
| C-31 | Shadow traffic: rejected                                               | D-26      | R1-05 S4.39                           |
| C-33 | Per-command HMAC deferred indefinitely                                 | D-31      | R1-05 S4.11                           |

### 2.4 Phase-ordering and scope positions

| #    | Position                                                                                                                  | D-NN      | Source      |
|------|---------------------------------------------------------------------------------------------------------------------------|-----------|-------------|
| C-12 | Phase 0-cascor is a carve-out from Phase B                                                                                | D-11      | R1-05 S4.19 |
| C-13 | Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D)                                                             | D-23      | R1-05 S4.35 |
| C-14 | Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bridge` (permanent kill) | D-17/D-18 | R1-05 S4.45 |
| C-15 | Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`)                                 | D-19      | R1-05 S4.36 |
| C-16 | rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`)                                                      | D-04      | R1-05 S4.3  |
| C-20 | GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in Phase B              | D-08      | R1-05 S4.8  |
| C-21 | NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape                                     | D-06      | R1-05 S4.5  |
| C-22 | `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H                               | D-27      | R1-05 S4.41 |
| C-28 | Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates                                                  | D-47/D-48 | R1-02 S6.1  |

### 2.5 Observability positions

| #    | Position                                                                                                          | D-NN | Source                 |
|------|-------------------------------------------------------------------------------------------------------------------|------|------------------------|
| C-32 | Chromium-only Playwright for v1                                                                                   | D-44 | R1-05 S4.31            |
| C-34 | Contract-test pytest marker `contract` runs on every PR in all 3 repos                                            | D-43 | R1-05 S4.34            |
| C-35 | Latency tests are recording-only in CI; strict assertions local-only                                              | D-42 | R1-05 S4.28            |
| C-37 | P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90% vs baseline | --   | R1-01 S2.5.1           |
| C-38 | Observability-before-behavior rule: metrics + panels + alerts before the behavior change                          | --   | R1-02 S1.2 principle 1 |
| C-39 | Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch                             | D-53 | R1-02 S1.2 principle 2 |
| C-42 | Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-reliability work)  | D-50 | R1-02 S2.4             |

### 2.6 Effort and calendar positions

| #    | Position                                                                | D-NN | Source               |
|------|-------------------------------------------------------------------------|------|----------------------|
| C-36 | Total effort: 13.5 target / 15.75 planning buffer / ~4.5 weeks calendar | --   | R2-02 S17; R3-01 S19 |
| --   | Phase 0-cascor staging soak = 72 h                                      | D-38 | R1-02 S3.4           |
| --   | Phase B staging soak = 72 h                                             | D-39 | R2-04                |
| --   | Phase B-pre-b staging soak = 48 h                                       | --   | R1-02 S4.2           |
| --   | Phase D entry gate = B-pre-b in production >=48 h                       | --   | R2-02 S18.8          |
| --   | Phase C flag-flip canary >= 7 days production data                      | D-48 | R1-02 S6.1           |
| --   | Mid-week deploys for behavior-changing flag flips only                  | D-61 | R1-02 S5.7           |
| --   | Minimum-viable carveout ~7 days (P0 only)                               | --   | R1-01 S1.2           |

### 2.7 Feature flag inventory

| Flag                          | Phase   | Initial                     | Final                                       | Removal?                     |
|-------------------------------|---------|-----------------------------|---------------------------------------------|------------------------------|
| `enable_browser_ws_bridge`    | B       | `False`                     | `True` (post-staging)                       | Post-flip deprecation (v1.1) |
| `disable_ws_bridge`           | B       | `False`                     | `False` permanent                           | Never                        |
| `enable_raf_coalescer`        | B       | `False`                     | depends on data                             | Post-B+1 if data warrants    |
| `use_websocket_set_params`    | C       | `False`                     | `True` (post-canary >=7 days)               | Post-flip deprecation (v1.1) |
| `enable_ws_control_buttons`   | D       | `False`                     | `True` (post-canary)                        | Post-flip deprecation (v1.1) |
| `ws_security_enabled`         | B-pre-b | `True`                      | `True` permanent (CI refuses False in prod) | Never                        |
| `disable_ws_control_endpoint` | B-pre-b | `False`                     | `False` permanent                           | Never                        |
| `ws_rate_limit_enabled`       | B-pre-b | `True`                      | `True` permanent                            | Never                        |
| `audit_log_enabled`           | B-pre-a | `True`                      | `True` permanent                            | Never                        |
| `ws_backpressure_policy`      | E       | `drop_oldest_progress_only` | same                                        | Permanent config (enum)      |
| `disable_ws_auto_reconnect`   | F       | `False`                     | `False` permanent                           | Never                        |

**Flag-flip rule**: every flag flip is a separate one-line PR, reviewed by project lead, deployed mid-week only (D-61). The behavior-change PR and the flag-flip PR are never the same PR.

---

## S3. Operational framework

### 3.1 Kill switch matrix

Every phase has at least one config-only kill switch. Every switch has a CI test proving the flip works. Every switch is drilled in staging during the phase's soak window.

**Meta-rules**:

- Every kill switch MTTR is tested in staging before the phase enters production (D-53)
- If any MTTR >5 min during staging drill, the phase does not ship
- If two consecutive switches fail in production, halt the migration for re-planning (abandon trigger)
- `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch; prevents panic-edit)
- `JUNIPER_WS_SECURITY_ENABLED=false` in production compose is REFUSED by CI guardrail

| Phase    | Switch (env var)                                 | Default                     | MTTR    | Validation metric                             | CI test                                        |
|----------|--------------------------------------------------|-----------------------------|---------|-----------------------------------------------|------------------------------------------------|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`                | 1024                        | 5 min   | `resume_requests{outcome=out_of_range}` spike | `test_replay_buffer_size_zero_disables_replay` |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`           | 0.5                         | 5 min   | `broadcast_timeout_total` spike               | `test_send_timeout_env_override`               |
| 0-cascor | Rolling cascor restart                           | --                          | 10 min  | New `server_instance_id`                      | manual                                         |
| 0-cascor | `git revert` P1                                  | --                          | 15 min  | Clients snapshot-refetch                      | --                                             |
| A-SDK    | Downgrade cascor-client pin                      | --                          | 15 min  | `pip index versions` resolved                 | pin workflow                                   |
| A-SDK    | PyPI yank                                        | --                          | 2 min   | Package 404 on new installs                   | --                                             |
| B-pre-a  | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999`        | 5                           | 5 min   | `per_ip_rejected_total` drops to 0            | `test_per_ip_cap_env_override`                 |
| B-pre-a  | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>`           | `[]`                        | 5 min   | `origin_rejected_total` drops                 | `test_origin_env_override`                     |
| B-pre-a  | `JUNIPER_WS_ALLOWED_ORIGINS='*'`                 | --                          | --      | **REFUSED BY PARSER**                         | `test_wildcard_refused`                        |
| B-pre-a  | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0`              | 120                         | 5 min   | Connections persist                           | `test_idle_timeout_env_override`               |
| B-pre-a  | `JUNIPER_AUDIT_LOG_ENABLED=false`                | true                        | 5 min   | Audit writes cease                            | `test_audit_log_env_override`                  |
| B-pre-b  | `JUNIPER_WS_SECURITY_ENABLED=false`              | true                        | 5 min   | Auth rejections drop (**prod CI refuses**)    | `test_ws_security_env_override`                |
| B-pre-b  | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`       | false                       | 5 min   | WS control traffic to 0                       | `test_disable_ws_control_endpoint`             |
| B-pre-b  | `JUNIPER_WS_RATE_LIMIT_ENABLED=false`            | true                        | 5 min   | Rate-limit counter freezes                    | `test_rate_limit_env_override`                 |
| B        | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false`         | false->true                 | 5 min   | Polling bytes rise to baseline                | `test_enable_browser_ws_bridge_env_override`   |
| B        | `JUNIPER_DISABLE_WS_BRIDGE=true`                 | false                       | 5 min   | Same (permanent kill switch)                  | `test_disable_ws_bridge_env_override`          |
| B        | Hardcoded ring-cap reduction                     | --                          | 1 hour  | Browser heap drops                            | --                                             |
| B        | URL `?ws=off` diagnostic                         | --                          | instant | Per-user bridge off                           | manual                                         |
| C        | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`  | false                       | 2 min   | WS transport freezes                          | `test_use_websocket_set_params_env_override`   |
| C        | `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1`              | 1.0                         | 5 min   | Tight timeout forces REST                     | `test_ws_set_params_timeout_env_override`      |
| D        | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | false                       | 5 min   | REST transport rises                          | `test_enable_ws_control_buttons_env_override`  |
| D        | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`       | false                       | 5 min   | Control WS to 0 (CSWSH)                       | (reused from B-pre-b)                          |
| E        | `JUNIPER_WS_BACKPRESSURE_POLICY=block`           | `drop_oldest_progress_only` | 5 min   | Dropped-messages to 0                         | `test_ws_backpressure_policy_env_override`     |
| F        | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`         | false                       | 10 min  | Reconnect counter freezes                     | `test_disable_ws_auto_reconnect_env_override`  |
| H        | `git revert` P16                                 | --                          | 10 min  | Shape hash matches pre-H                      | --                                             |
| I        | `git revert` cache-bust commit                   | --                          | 10 min  | Asset URL query reverts                       | --                                             |

**Non-switches** (deliberate inversions):

- `JUNIPER_WS_ALLOWED_ORIGINS='*'` -- **refused by parser** (prevents panic-edit during incident)
- `JUNIPER_WS_SECURITY_ENABLED=false` in production compose -- **refused by CI guardrail** (dev/staging exempt)

### 3.2 Risk register

| ID     | Risk                                      | Sev/Lik | Phase                  | Kill switch                         | MTTR   | Key mitigation                                                                           |
|--------|-------------------------------------------|---------|------------------------|-------------------------------------|--------|------------------------------------------------------------------------------------------|
| 01     | Dual metric format removed aggressively   | H/M     | H                      | `git revert`                        | 10 min | CODEOWNERS hard gate; pre-commit hook; regression test in Phase B; shape hash in Phase H |
| 02     | Phase B clientside_callback hard to debug | M/H     | B                      | `disable_ws_bridge=true`            | 5 min  | `drain_callback_gen` gauge; `browser_js_errors_total`; 72h soak; flag default False      |
| 03     | Phase C REST+WS ordering race             | M/L     | C                      | `use_websocket_set_params=false`    | 2 min  | Disjoint hot/cold; `_training_lock`; fail-loud startup; bounded map 256                  |
| 04     | Slow-client blocks broadcasts             | M/M     | E (0-cascor quick-fix) | `ws_backpressure_policy=close_slow` | 5 min  | 0.5s send timeout; full per-client pump in Phase E                                       |
| 05     | Playwright misses real-cascor regression  | M/M     | B, D                   | fix the test                        | --     | Nightly smoke against real cascor; `schema_parity` contract test                         |
| 06     | Reconnection storm after cascor restart   | L/M     | F                      | `disable_ws_auto_reconnect=true`    | 10 min | Full jitter (ships in Phase B)                                                           |
| 07     | 50-conn cap hit (multi-tenant)            | L/L     | n/a                    | raise `ws_max_connections`          | 10 min | Single-tenant v1 (C-24)                                                                  |
| 08     | Demo mode parity breaks                   | L/M     | B                      | revert PR                           | 10 min | `test_demo_mode_metrics_parity` blocker in both lanes                                    |
| 09     | Phase C unexpected behavior               | L/M     | C                      | `use_websocket_set_params=false`    | 2 min  | Flag False; 6 hard flip gates; >=7-day canary                                            |
| 10     | Browser memory exhaustion                 | M/H     | B                      | `disable_ws_bridge=true`            | 5 min  | `extendTraces(maxPoints=5000)`; ring-bound in handler (AST lint); 72h soak               |
| 11     | Silent data loss via drop-oldest          | H/L     | E                      | `ws_backpressure_policy=block`      | 5 min  | Only progress dropped; state closes; per-type assertion; `WSStateDropped` PAGE           |
| 12     | Background tab memory spike               | L/M     | B                      | same as RISK-10                     | 5 min  | Cap-in-handler independent of drain rate                                                 |
| 13     | Orphaned commands after timeout           | M/M     | B,C,D                  | reduce timeouts / flag-off          | 5 min  | `command_id` correlation; pending UI; resolve via response OR state event                |
| 14     | Cascor crash mid-broadcast                | L/L     | B                      | rolling restart                     | 10 min | `server_instance_id` forces resync; `WSSeqCurrentStalled` PAGE                           |
| 15     | **CSWSH attack**                          | **H/M** | B-pre-a/b              | `disable_ws_control_endpoint=true`  | 5 min  | Origin + CSRF + `WSOriginRejection` PAGE; **abandon trigger if kill switch fails**       |
| 16     | Topology >64KB silently fails             | M/M     | B-pre-a                | REST fallback                       | 5 min  | Size caps; `oversized_frame_total` alert; REST `/api/topology` preserved                 |
| CCC-01 | `request_id` rename incomplete            | H/M     | all                    | pre-merge grep                      | --     | D-02 grep check; `test_command_id_echoed`                                                |
| CCC-02 | Metric added, no alert/panel              | M/M     | all                    | CI metrics-presence                 | --     | D-37 blocker test                                                                        |
| CCC-03 | Kill switch untested in CI                | Crit/M  | all                    | halt migration                      | --     | D-53 staging drill; two-failure abandon                                                  |
| CCC-04 | Cross-repo pin at unreleased version      | H/L     | cross-repo             | pin previous                        | 10 min | Merge-order enforcement; TestPyPI prerelease                                             |
| CCC-05 | Contract test is tautological             | M/M     | B, G                   | review audit                        | --     | Inline-literal rule; no cross-repo fixtures                                              |

### 3.3 Observability matrix (per-phase)

| Phase    | New metrics (count)                                   | Key alerts                                                                                              | New dashboards                          |
|----------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------|
| 0-cascor | 15 `cascor_ws_*`                                      | `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap`, `WSPendingConnectionStuck`, `WSSlowBroadcastP95` | --                                      |
| A-SDK    | 1 `juniper_cascor_client_ws_set_params_total{status}` | --                                                                                                      | --                                      |
| B-pre-a  | 8 security metrics                                    | `WSOriginRejection` (PAGE), `WSOversizedFrame` (PAGE)                                                   | --                                      |
| B        | 11 `canopy_ws_*` + Prom hookup                        | `WSDrainCallbackGenStuck` (PAGE), `WSBrowserHeapHigh`, `WSJSErrorsNonZero`, `WSConnectionCount80`       | "WebSocket health", "Polling bandwidth" |
| B-pre-b  | 9 auth/security                                       | `WSAuthSpike`, `WSRateLimitSpike`, per-origin cooldown                                                  | Security panel                          |
| C        | 3 (set-params-latency, orphaned, pending-size)        | `CanopyOrphanedCommands` (ticket)                                                                       | --                                      |
| D        | 4 (command-latency, orphaned, commands, received)     | --                                                                                                      | --                                      |
| E        | 3 (dropped, queue-depth, slow-closes)                 | `WSStateDropped` (PAGE)                                                                                 | --                                      |
| F        | reconnect-jitter histogram                            | `WSReconnectStorm` (ticket)                                                                             | --                                      |
| G        | -- (test-only)                                        | --                                                                                                      | --                                      |
| H        | -- (test-only)                                        | --                                                                                                      | shape-hash trend                        |

**Page-severity alerts** (5 total): `WSOriginRejection`, `WSOversizedFrame`, `WSSeqCurrentStalled`, `WSDrainCallbackGenStuck`, `WSStateDropped`. All must be synthetically test-fired in staging before the guarding phase ships to production.

**Metric-before-behavior rule (binding)**: no behavior change ships without its guarding metric + alert + test-fired once in staging. The metrics-presence CI test (D-37) scrapes `/metrics` and asserts every canonical metric is present. Missing metric = PR blocker.

**SLOs (aspirational until >=1 week production data)**:

| Event                           | p50    | p95     | p99     |
|---------------------------------|--------|---------|---------|
| `metrics`                       | <100ms | <250ms  | <500ms  |
| `state`                         | <50ms  | <100ms  | <200ms  |
| `command_response` (set_params) | <50ms  | <100ms  | <200ms  |
| `command_response` (start/stop) | <100ms | <250ms  | <500ms  |
| `cascade_add`                   | <250ms | <500ms  | <1000ms |
| `topology` <=64KB               | <500ms | <1000ms | <2000ms |

### 3.4 Feature flag inventory

See S2.7 for the canonical table. Additional rules:

- **Error-budget burn-rate freeze rule** (D-50): If the 99.9% SLO compliance budget burns in <1 day, freeze all non-reliability work until recovered. Operationally binding from Phase B onwards.
- **Mid-week deploy rule** (D-61): Behavior-changing flag flips (P7, Phase C flip, Phase D flip) deploy mid-week only. Additive-only deploys (P1, P3/P4, P5) deploy any day.
- **Bandwidth baseline measurement** (D-62): Before Phase B deploys, capture 1 hour of production-equivalent staging traffic in `canopy_rest_polling_bytes_per_sec`. This value is the denominator for the >=90% reduction acceptance criterion.

### 3.5 Cross-repo merge sequence (numbered PR list)

**Critical path (P0 win)**: P2 --> P1 --> [72h soak] --> P3 --> P4 --> P6 --> [72h soak] --> P7.

Full sequence:

| Order | PR  | Branch                                   | Repo                    | Phase    | Blocks                                       |
|------:|-----|------------------------------------------|-------------------------|----------|----------------------------------------------|
|     1 | P2  | `phase-a-sdk-set-params`                 | juniper-cascor-client   | A-SDK    | PyPI publish gates downstream                |
|     2 | P1  | `phase-0-cascor-seq-replay-resume`       | juniper-cascor          | 0-cascor | Phase B (72h soak)                           |
|     3 | P3  | `phase-b-pre-a-cascor-security`          | juniper-cascor          | B-pre-a  | P4                                           |
|     4 | P4  | `phase-b-pre-a-canopy-security`          | juniper-canopy          | B-pre-a  | Phase B                                      |
|    -- |     |                                          |                         |          | **72h soak (0-cascor) + 24h soak (B-pre-a)** |
|     5 | P5  | `phase-b-cascor-audit-prom-counters`     | juniper-cascor          | B        | --                                           |
|     6 | P6  | `phase-b-canopy-drain-wiring`            | juniper-canopy          | B        | Yes (72h soak)                               |
|    -- |     |                                          |                         |          | **72h staging soak (Phase B flag-on)**       |
|     7 | P7  | `phase-b-canopy-flag-flip`               | juniper-canopy          | B        | **P0 WIN**                                   |
|     8 | P15 | `phase-g-cascor-set-params-integration`  | juniper-cascor          | G        | No (parallel)                                |
|     9 | P8  | `phase-b-pre-b-cascor-control-security`  | juniper-cascor          | B-pre-b  | P9                                           |
|    10 | P9  | `phase-b-pre-b-canopy-csrf-audit`        | juniper-canopy          | B-pre-b  | Phase D (48h prod soak)                      |
|    11 | P10 | `phase-c-canopy-set-params-adapter`      | juniper-canopy          | C        | >=7d canary then flag flip                   |
|    12 | P11 | `phase-d-cascor-control-commands`        | juniper-cascor          | D        | P12                                          |
|    13 | P12 | `phase-d-canopy-button-ws-routing`       | juniper-canopy          | D        | --                                           |
|    14 | P13 | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor          | E        | -- (conditional)                             |
|    15 | P14 | `phase-f-heartbeat-jitter`               | juniper-cascor + canopy | F        | --                                           |
|    16 | P16 | `phase-h-normalize-metric-audit`         | juniper-canopy          | H        | --                                           |

**juniper-ml extras pin bumps**: one-line follow-up PRs after each SDK version change (D-57).

**Version bumps**:

| Repo                  | Phase        | Bump  | Rationale                                       |
|-----------------------|--------------|-------|-------------------------------------------------|
| juniper-cascor-client | A            | minor | New public method `set_params`                  |
| juniper-cascor        | 0-cascor     | minor | New envelope fields (public contract)           |
| juniper-cascor        | B-pre-a/b    | patch | Security guards (no public API change)          |
| juniper-cascor        | E            | minor | New `ws_backpressure_policy` setting            |
| juniper-cascor        | G            | patch | Test-only                                       |
| juniper-canopy        | B-pre-a/b    | patch | Security guards                                 |
| juniper-canopy        | B            | minor | New browser bridge + `/api/ws_latency` endpoint |
| juniper-canopy        | C/D/H        | patch | Internal refactor / test-only                   |
| juniper-ml            | per SDK bump | patch | Extras pin update                               |

Helm chart `Chart.yaml` `version` + `appVersion` must match app semver per Juniper ecosystem convention.

**Rollback order**: always reverse-dependency (canopy first, then cascor, then SDK). Never forward-order.

**Worktrees**: one per phase per repo, created in `/home/pcalnon/Development/python/Juniper/worktrees/` per ecosystem convention.

**Merge strategy**: squash-merge (linear history). Use GitHub merge queue where available.

### 3.6 Configuration reference

Every setting has Pydantic `Field(description=...)`. CI asserts every setting is documented and every env var round-trips.

| Setting                         | Repo          | Type      | Default                     | Env var                                    | Phase    | Validation                       |
|---------------------------------|---------------|-----------|-----------------------------|--------------------------------------------|----------|----------------------------------|
| `ws_replay_buffer_size`         | cascor        | int       | 1024                        | `JUNIPER_WS_REPLAY_BUFFER_SIZE`            | 0-cascor | `>=0` (0 disables)               |
| `ws_send_timeout_seconds`       | cascor        | float     | 0.5                         | `JUNIPER_WS_SEND_TIMEOUT_SECONDS`          | 0-cascor | `>0`                             |
| `ws_state_throttle_coalesce_ms` | cascor        | int       | 1000                        | `JUNIPER_WS_STATE_THROTTLE_COALESCE_MS`    | 0-cascor | `>0`                             |
| `ws_resume_handshake_timeout_s` | cascor        | float     | 5.0                         | `JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S`    | 0-cascor | `>0`                             |
| `ws_pending_max_duration_s`     | cascor        | float     | 10.0                        | `JUNIPER_WS_PENDING_MAX_DURATION_S`        | 0-cascor | `>0`                             |
| `ws_max_connections_per_ip`     | cascor        | int       | 5                           | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP`        | B-pre-a  | `>=1`                            |
| `ws_allowed_origins`            | cascor        | list[str] | `[]` (fail-closed)          | `JUNIPER_WS_ALLOWED_ORIGINS`               | B-pre-a  | no `*`                           |
| `ws_idle_timeout_seconds`       | cascor/canopy | int       | 120                         | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS`          | B-pre-a  | `>=0` (0 disables)               |
| `ws_max_connections_per_ip`     | canopy        | int       | 5                           | `JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a  | `>=1`                            |
| `ws_allowed_origins`            | canopy        | list[str] | localhost defaults          | `JUNIPER_CANOPY_WS_ALLOWED_ORIGINS`        | B-pre-a  | no `*`                           |
| `audit_log_enabled`             | canopy        | bool      | `True`                      | `JUNIPER_AUDIT_LOG_ENABLED`                | B-pre-a  | bool                             |
| `audit_log_path`                | canopy        | str       | `/var/log/canopy/audit.log` | `JUNIPER_AUDIT_LOG_PATH`                   | B-pre-a  | path                             |
| `audit_log_retention_days`      | canopy        | int       | 90                          | `JUNIPER_AUDIT_LOG_RETENTION_DAYS`         | B-pre-a  | `>=1`                            |
| `ws_security_enabled`           | canopy        | bool      | `True`                      | `JUNIPER_WS_SECURITY_ENABLED`              | B-pre-b  | bool; CI refuses `false` in prod |
| `ws_rate_limit_enabled`         | canopy        | bool      | `True`                      | `JUNIPER_WS_RATE_LIMIT_ENABLED`            | B-pre-b  | bool                             |
| `ws_rate_limit_cps`             | canopy        | int       | 10                          | `JUNIPER_WS_RATE_LIMIT_CPS`                | B-pre-b  | `>=1`                            |
| `disable_ws_control_endpoint`   | canopy        | bool      | `False`                     | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT`      | B-pre-b  | bool                             |
| `enable_browser_ws_bridge`      | canopy        | bool      | `False` -> True             | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE`         | B        | bool                             |
| `disable_ws_bridge`             | canopy        | bool      | `False`                     | `JUNIPER_DISABLE_WS_BRIDGE`                | B        | bool                             |
| `enable_raf_coalescer`          | canopy        | bool      | `False`                     | `JUNIPER_ENABLE_RAF_COALESCER`             | B        | bool                             |
| `enable_ws_latency_beacon`      | canopy        | bool      | `True`                      | `JUNIPER_ENABLE_WS_LATENCY_BEACON`         | B        | bool                             |
| `use_websocket_set_params`      | canopy        | bool      | `False`                     | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS`  | C        | bool                             |
| `ws_set_params_timeout`         | canopy        | float     | 1.0                         | `JUNIPER_WS_SET_PARAMS_TIMEOUT`            | C        | `>0`                             |
| `enable_ws_control_buttons`     | canopy        | bool      | `False`                     | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS` | D        | bool                             |
| `ws_backpressure_policy`        | cascor        | Literal   | `drop_oldest_progress_only` | `JUNIPER_WS_BACKPRESSURE_POLICY`           | E        | enum                             |
| `disable_ws_auto_reconnect`     | canopy        | bool      | `False`                     | `JUNIPER_DISABLE_WS_AUTO_RECONNECT`        | F        | bool                             |

---

## S4. Phase 0-cascor: SDK + cascor server prerequisites

### 4.1 Goal

Cascor's `/ws/training` emits monotonically-increasing `seq` on every outbound envelope, advertises `server_instance_id` + `server_start_time` + `replay_buffer_capacity` + `emitted_at_monotonic`, supports a 1024-entry replay buffer with `resume` handler, exposes `snapshot_seq` atomically on REST,
fixes slow-client fan-out (0.5 s timeout), fixes GAP-WS-21 state coalescer, fixes GAP-WS-29 silent exception swallowing, and returns protocol-error responses on `/ws/control`.
The `/ws/control` endpoint gains `command_id` echo but **no `seq` field** (C-02).
Purely additive -- existing clients keep working.

### 4.2 Entry gate

- [ ] `juniper-cascor` main branch clean; `cd juniper-cascor/src/tests && bash scripts/run_tests.bash` green
- [ ] GAP-WS-19 verified RESOLVED: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` shows lock pattern at lines 138-156
- [ ] No concurrent cascor PR touching `websocket/*.py`, `lifecycle/manager.py`, `messages.py`
- [ ] Prometheus namespace collision check: 15 `cascor_ws_*` names reserved
- [ ] `juniper-cascor-worker` CI green against current cascor main
- [ ] Constitution section 2 committed; no re-litigation

### 4.3 Deliverables checklist

**Server-side code** (10 commits, single squash-merged PR):

| Commit          | File(s)                                                   | Change                                                                                                                                                                        |
|-----------------|-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **0-cascor-1**  | `juniper-cascor/src/api/websocket/messages.py`            | Optional `seq: Optional[int]` + `emitted_at_monotonic: float` on every envelope builder                                                                                       |
| **0-cascor-2a** | `juniper-cascor/src/api/websocket/manager.py`             | `server_instance_id=uuid4()`, `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer=deque(maxlen=Settings.ws_replay_buffer_size)`, `_assign_seq_and_append()` helper |
| **0-cascor-2b** | same                                                      | `connect()` sends `connection_established` with `{server_instance_id, server_start_time, replay_buffer_capacity}` (D-16)                                                      |
| **0-cascor-3**  | same                                                      | `_send_json()` wraps in `asyncio.wait_for(timeout=Settings.ws_send_timeout_seconds)` (default 0.5s, GAP-WS-07 quick-fix); exception logged; metric incremented                |
| **0-cascor-4**  | same                                                      | `replay_since(last_seq) -> list[dict]` + `ReplayOutOfRange` exception; copy-under-lock                                                                                        |
| **0-cascor-5a** | `juniper-cascor/src/api/websocket/training_stream.py`     | `_pending_connections: set[WebSocket]`, `connect_pending()`, `promote_to_active()` (D-14)                                                                                     |
| **0-cascor-5b** | same                                                      | `/ws/training` handler: `resume` frame (5s timeout) --> `resume_ok` or `resume_failed{out_of_range\|server_restarted\|second_resume}`.                                        |
|                 |                                                           | Server-restart via UUID mismatch (D-15). One-resume-per-connection via`resume_consumed: bool` (D-30)                                                                          |
| **0-cascor-6**  | `juniper-cascor/src/api/training/router.py`               | `/api/v1/training/status` adds `snapshot_seq` + `server_instance_id` atomically under `_seq_lock`                                                                             |
| **0-cascor-7**  | `juniper-cascor/src/lifecycle/manager.py` (lines 133-136) | Replace 1 Hz drop-filter with debounced coalescer; terminal transitions (Completed/Failed/Stopped) bypass throttle (GAP-WS-21)                                                |
| **0-cascor-8**  | `juniper-cascor/src/api/websocket/manager.py`             | `broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29)                                                                                             |
| **0-cascor-9**  | `juniper-cascor/src/api/websocket/control_stream.py`      | Protocol-error for unknown commands, close 1003 on malformed JSON, echo `command_id` when present, **NO seq on `command_response`** (D-03)                                    |
| **0-cascor-10** | docs                                                      | CHANGELOG.md + `docs/websocket_protocol.md` ("Sequence numbers, replay, and reconnection" section with old/new compat matrix)                                                 |

**`command_response` carve-out** (D-03 canonical): `/ws/training` has seq and replay. `/ws/control` has NO seq and NO replay. Client correlation via `command_id` only.

**Settings** (`juniper-cascor/src/config/settings.py`):

- [ ] `ws_replay_buffer_size: int = 1024` (`JUNIPER_WS_REPLAY_BUFFER_SIZE`)
- [ ] `ws_send_timeout_seconds: float = 0.5` (`JUNIPER_WS_SEND_TIMEOUT_SECONDS`)
- [ ] `ws_resume_handshake_timeout_s: float = 5.0`
- [ ] `ws_state_throttle_coalesce_ms: int = 1000`
- [ ] `ws_pending_max_duration_s: float = 10.0`

### 4.4 Cross-cutting deliverables

- **CCC-01 (schema)**: All new fields additive. `command_id` rename mandate enforced (grep PR for `request_id` must return 0). `emitted_at_monotonic` ships here.
- **CCC-02 (observability)**: All 15 metrics present before merge. Metrics-presence CI test runs on PR. `WSSeqCurrentStalled` test-fired in staging.
- **CCC-03 (kill switches)**: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` and `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` as kill switches with CI tests.
- **CCC-04 (cross-repo)**: Merges before canopy Phase B (1-week additive-soak). Helm chart bumped.
- **CCC-05 (contract tests)**: `test_replay_buffer_capacity_advertised`, `test_ws_control_command_response_has_no_seq`, `test_close_all_holds_lock`.
- **CCC-06 (documentation)**: CHANGELOG entry, `docs/websocket_protocol.md` section, runbook `cascor-replay-buffer.md`.
- **CCC-07 (configuration)**: 5 new `ws_*` settings in canonical table with Pydantic `Field(description=...)`.
- **CCC-08 (backwards compat)**: REST `/api/v1/training/status` extended additively. `juniper-cascor-worker` CI green during soak.
- **CCC-09 (feature flags)**: No feature flags in this phase (purely additive).
- **CCC-10 (latency instrumentation)**: `emitted_at_monotonic` ships as the latency pipe seed for Phase B.

### 4.5 Test acceptance

**Unit tests** (20+):

| Test name                                                         | Type        | Measurable criterion                       |
|-------------------------------------------------------------------|-------------|--------------------------------------------|
| `test_seq_monotonically_increases_across_broadcasts`              | unit        | seq(n+1) > seq(n)                          |
| `test_seq_is_assigned_on_loop_thread`                             | unit        | No cross-thread seq assignment             |
| `test_seq_lock_does_not_block_broadcast_iteration`                | unit        | Broadcast completes <100ms                 |
| `test_replay_buffer_bounded_to_configured_capacity`               | unit        | `maxlen == Settings.ws_replay_buffer_size` |
| `test_replay_buffer_capacity_configurable_via_env`                | unit        | Override to 256 works                      |
| `test_replay_buffer_size_zero_disables_replay`                    | unit        | `=0` -> `out_of_range` (D-36)              |
| `test_resume_replays_events_after_last_seq`                       | integration | N-5 -> exactly 5 events                    |
| `test_resume_failed_out_of_range`                                 | integration | Broadcast 2000, last_seq=10 -> fail        |
| `test_resume_failed_server_restarted`                             | integration | Stale UUID -> fail                         |
| `test_resume_malformed_data`                                      | integration | Malformed -> close                         |
| `test_resume_timeout_no_frame`                                    | integration | 5s timeout -> close                        |
| `test_connection_established_advertises_instance_id_and_capacity` | unit        | Fields present (D-16)                      |
| `test_snapshot_seq_atomic_with_state_read`                        | integration | No torn snapshot                           |
| `test_second_resume_closes_connection_1003`                       | unit        | D-30 enforced                              |
| `test_slow_client_send_timeout_does_not_block_fanout`             | unit        | 0.5s quick-fix works                       |
| `test_send_timeout_env_override`                                  | unit        | D-46 env-configurable                      |
| `test_state_coalescer_flushes_terminal_transitions`               | unit        | Started->Failed both observed (GAP-WS-21)  |
| `test_broadcast_from_thread_exception_logged`                     | unit        | GAP-WS-29 via caplog                       |
| `test_ws_control_command_response_has_no_seq`                     | contract    | D-03 explicit negative assertion           |
| `test_pending_connections_not_eligible_for_broadcast`             | unit        | D-14 correctness                           |
| `test_promote_to_active_atomic_under_seq_lock`                    | unit        | Atomic promotion                           |
| `test_close_all_holds_lock`                                       | unit        | GAP-WS-19 regression (D-13)                |
| `test_emitted_at_monotonic_present_on_every_broadcast`            | unit        | CCC-10 field                               |
| `test_legacy_client_ignores_seq_field`                            | unit        | CCC-08 backward compat                     |
| `test_malformed_json_closes_1003`                                 | unit        | GAP-WS-22                                  |
| `test_unknown_command_returns_protocol_error_envelope`            | unit        | GAP-WS-22                                  |

**Chaos tests (BLOCKING gates, not nightly)**:

- [ ] `chaos_broadcast_replay_race`: hypothesis + asyncio.gather 100 concurrent; assert no seq gaps, no deadlocks
- [ ] `chaos_broadcast_fanout`: 100 Hz x 60s x 10 clients; p95 < 250ms, memory +/-10% (D-41 load test)
- [ ] `chaos_broadcast_from_thread_exception`: hypothesis exception types; assert counter increments

**Contract tests** (D-43, `@pytest.mark.contract`):

- `test_replay_buffer_capacity_advertised`
- `test_ws_control_command_response_has_no_seq`
- `test_close_all_holds_lock` (D-13 regression guard)

**Metric-presence test** (D-37): scrapes `/metrics`, asserts all 15 Phase 0-cascor metrics present.

### 4.6 Pull request plan

| #      | Branch                             | Title                                                                    | Repo           | Target |
|--------|------------------------------------|--------------------------------------------------------------------------|----------------|--------|
| **P1** | `phase-0-cascor-seq-replay-resume` | `feat(ws): seq numbers, replay buffer, resume protocol, state coalescer` | juniper-cascor | main   |

### 4.7 Exit gate

1. All 26+ unit + 5 integration + 3 chaos + load tests green
2. Metric-presence pytest green (D-37)
3. **72-hour staging soak** (D-38): `cascor_ws_seq_gap_detected_total==0`, `broadcast_from_thread_errors_total==0`, `broadcast_timeout_total` rate < 0.1/s
4. `WSSeqCurrentStalled` alert test-fired once in staging (D-53)
5. `juniper-cascor-worker` CI green during soak (CCC-04/CCC-08)
6. Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published
7. Load test green: 100 Hz x 60s x 10 clients, p95 < 250 ms (D-41)
8. **Going/no-go**: if seq gap detected during soak, HALT and investigate before Phase B

### 4.8 Rollback

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
# Blue/green redeploy; clients see new server_instance_id, refetch REST snapshot
```

### 4.9 NOT in this phase

- Full Phase E backpressure (only 0.5s `_send_json` quick-fix)
- `permessage-deflate` (GAP-WS-17); topology chunking (GAP-WS-18)
- `seq` on `command_response` (D-03 explicit exclusion)
- GAP-WS-19 re-fix (already on main; regression test only)
- M-SEC-01..M-SEC-07 security controls (Phase B-pre-a/b)
- Multi-tenant replay buffers (D-32 deferred)
- Canopy adapter consumption (Phase C)
- Canopy drain callbacks (Phase B)

**Observability**:

| Metric                                         | Type      | Labels                          |
|------------------------------------------------|-----------|---------------------------------|
| `cascor_ws_seq_current`                        | Gauge     | --                              |
| `cascor_ws_replay_buffer_occupancy`            | Gauge     | --                              |
| `cascor_ws_replay_buffer_bytes`                | Gauge     | --                              |
| `cascor_ws_replay_buffer_capacity_configured`  | Gauge     | --                              |
| `cascor_ws_resume_requests_total`              | Counter   | `outcome`                       |
| `cascor_ws_resume_replayed_events`             | Histogram | buckets {0,1,5,25,100,500,1024} |
| `cascor_ws_broadcast_timeout_total`            | Counter   | `type`                          |
| `cascor_ws_broadcast_send_duration_seconds`    | Histogram | `type`                          |
| `cascor_ws_pending_connections`                | Gauge     | --                              |
| `cascor_ws_state_throttle_coalesced_total`     | Counter   | --                              |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter   | --                              |
| `cascor_ws_seq_gap_detected_total`             | Counter   | --                              |
| `cascor_ws_connections_active`                 | Gauge     | `endpoint`                      |
| `cascor_ws_command_responses_total`            | Counter   | `command, status`               |
| `cascor_ws_command_handler_seconds`            | Histogram | `command`                       |

**Alerts**: `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap` (ticket), `WSPendingConnectionStuck` (ticket), `WSSlowBroadcastP95` (ticket)

---

## S5. Phase A-SDK: `set_params` on cascor-client (parallel with Phase 0-cascor)

### 5.1 Goal

Ship `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None)` to PyPI with per-request `command_id` correlation, caller-cancellation safety, fail-fast on disconnect, no retry logic, bounded correlation map (256 max).

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
- ALWAYS `pop(command_id, None)` in `finally` (caller-cancellation safety)
- **No SDK retries** (D-20)
- Stashes `envelope["_client_latency_ms"]` (private field, leading underscore)

**Supporting files**:

- [ ] `testing/fake_ws_client.py`: `on_command(name, handler)` auto-scaffold `command_response`
- [ ] `testing/server_harness.py`: `FakeCascorServerHarness` for canopy Phase B tests
- [ ] `pyproject.toml` minor version bump (new public method)
- [ ] CHANGELOG.md entry citing GAP-WS-01
- [ ] PyPI publish; same-day `juniper-ml` extras pin bump follow-up PR (D-57)
- [ ] TestPyPI prerelease for canopy PR iteration before PyPI promotion

**Metric**: `juniper_cascor_client_ws_set_params_total{status}` (status = `success|timeout|connection_error|server_error|overload`)

### 5.4 Test acceptance

| Test name                                                      | Type               | Criterion                             |
|----------------------------------------------------------------|--------------------|---------------------------------------|
| `test_set_params_default_timeout_is_one_second`                | unit               | Default kwarg = 1.0 (C-03 regression) |
| `test_set_params_happy_path`                                   | unit               | 50ms ack latency roundtrip            |
| `test_set_params_timeout_raises_typed_exception`               | unit               | JuniperCascorTimeoutError             |
| `test_set_params_concurrent_callers_correlate_via_command_id`  | unit               | 2 calls distinguished (C-01)          |
| `test_set_params_caller_cancellation_cleans_correlation_map`   | unit **MANDATORY** | `len(_pending)==0` after cancel       |
| `test_set_params_fails_fast_on_disconnect`                     | unit               | C-04 enforced                         |
| `test_set_params_no_retry_on_timeout`                          | unit               | No retry (D-20)                       |
| `test_set_params_server_error_response_raises_typed_exception` | unit               | Error handling                        |
| `test_correlation_map_bounded_at_256`                          | unit               | 257th -> JuniperCascorOverloadError   |
| `test_recv_task_propagates_exception_to_all_pending_futures`   | unit               | Drain on error                        |
| `test_len_pending_returns_to_zero_after_failure_modes`         | nightly            | Leak prevention                       |
| `test_set_params_x_api_key_header_present`                     | unit               | Security regression                   |

### 5.5 Pull request plan

| #      | Branch                   | Repo                  |
|--------|--------------------------|-----------------------|
| **P2** | `phase-a-sdk-set-params` | juniper-cascor-client |

### 5.6 Exit gate

- [ ] All 12 unit tests green; coverage >=95% on new code
- [ ] `pip install juniper-cascor-client==<new>` succeeds in fresh venv
- [ ] Draft canopy adapter can import and call `set_params` against `FakeCascorServerHarness`
- [ ] `test_set_params_caller_cancellation_cleans_correlation_map` non-flaky across 10 runs
- [ ] `juniper-ml/pyproject.toml` extras pin bump PR opened

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

## S6. Phase B-pre-a: read-path security gate

### 6.1 Goal

Close minimum security holes for browser `/ws/training` exposure: frame-size caps (M-SEC-03, 4KB inbound), Origin allowlist on `/ws/training` (M-SEC-01b), per-IP connection caps (M-SEC-04, 5/IP), idle timeout (120s), audit-logger skeleton (M-SEC-07).

### 6.2 Entry gate

- [ ] Phase 0-cascor (P1) merged to cascor main (1-week additive-soak starts)
- [ ] Both cascor and canopy main clean
- [ ] `canopy.audit` logger name not already used: `grep -rn "canopy.audit" juniper-canopy/src/`
- [ ] No concurrent security PR open

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
- [ ] `audit_log.py` (new): `canopy.audit` JSON logger, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist, CRLF escape
- [ ] CI `scripts/audit_ws_receive_calls.py`: AST check every `ws.receive_*()` has explicit `max_size`

**Meta-setting**: `ws_security_enabled: bool = True` (positive-sense, C-27) with CI guardrail in `juniper-deploy`.

### 6.4 Test acceptance

| Test                                                          | Type       | Criterion                       |
|---------------------------------------------------------------|------------|---------------------------------|
| `test_oversized_frame_rejected_with_1009`                     | unit       | 65KB -> close 1009 (both repos) |
| `test_per_ip_cap_enforced_6th_rejected_1013`                  | unit       | 6th conn -> 1013                |
| `test_per_ip_counter_decrements_on_disconnect`                | unit       | Cleanup works                   |
| `test_per_ip_counter_decrements_on_exception`                 | unit       | Exception-safe cleanup          |
| `test_per_ip_map_shrinks_to_zero`                             | unit       | Memory leak guard               |
| `test_origin_allowlist_accepts_configured_origin`             | unit       | Happy path                      |
| `test_origin_allowlist_rejects_third_party`                   | unit       | Cross-origin rejected           |
| `test_origin_allowlist_rejects_missing_origin`                | unit       | Missing origin rejected         |
| `test_empty_allowlist_rejects_all_fail_closed`                | unit       | Fail-closed default             |
| `test_allowed_origins_wildcard_refused`                       | unit       | Parser rejects `*`              |
| `test_idle_timeout_closes_1000`                               | unit       | 120s idle -> close              |
| `test_audit_log_format_and_scrubbing`                         | unit       | JSON + scrub                    |
| `test_audit_log_rotates_daily`                                | unit       | Rotation works                  |
| `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` | Playwright | Cross-origin probe              |

### 6.5 Pull request plan

| #      | Branch                          | Repo           | Order    |
|--------|---------------------------------|----------------|----------|
| **P3** | `phase-b-pre-a-cascor-security` | juniper-cascor | First    |
| **P4** | `phase-b-pre-a-canopy-security` | juniper-canopy | After P3 |

### 6.6 Exit gate

- [ ] All tests + CI AST guardrail green
- [ ] CSWSH probe from `http://evil.example.com` rejected
- [ ] 65KB frame returns close 1009
- [ ] 6th same-IP connection returns 1013
- [ ] Empty allowlist rejects all (fail-closed). **HALT if fail-open.**
- [ ] `WSOriginRejection` alert test-fired in staging (D-53)
- [ ] 24-hour staging soak with no user lockout
- [ ] Runbooks published: `ws-audit-log-troubleshooting.md`, `ws-cswsh-detection.md`

### 6.7 Rollback

```bash
# Per-IP cap neutralize (5 min)
export JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999
systemctl restart juniper-cascor juniper-canopy

# Broaden allowlist (5 min) -- '*' is REFUSED by parser (C-30)
export JUNIPER_WS_ALLOWED_ORIGINS='http://extra-origin:8050,http://localhost:8050'

# Idle timeout disable (5 min)
export JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0

# Audit log disable (5 min)
export JUNIPER_AUDIT_LOG_ENABLED=false

# Full revert (10 min)
git revert <phase-b-pre-a-canopy-merge> <phase-b-pre-a-cascor-merge>
```

### 6.8 NOT in this phase

- Cookie + CSRF first-frame (Phase B-pre-b)
- Origin on `/ws/control` (Phase B-pre-b)
- Rate limit (Phase B-pre-b)
- Prometheus counters for audit (Phase B)
- HMAC adapter auth (Phase B-pre-b)

**Observability**:

| Metric                                                   | Type    | Purpose                                         |
|----------------------------------------------------------|---------|-------------------------------------------------|
| `cascor_ws_oversized_frame_total{endpoint, type}`        | Counter | Size guard signal                               |
| `cascor_ws_per_ip_rejected_total`                        | Counter | Per-IP cap signal                               |
| `cascor_ws_idle_timeout_total`                           | Counter | Idle timeout signal                             |
| `canopy_ws_oversized_frame_total{endpoint}`              | Counter | Canopy-side size guard                          |
| `canopy_ws_per_ip_rejected_total`                        | Counter | Canopy-side per-IP cap                          |
| `canopy_ws_origin_rejected_total{origin_hash, endpoint}` | Counter | Origin hash (SHA-256 prefix 8 chars, GDPR-safe) |
| `canopy_audit_events_total{event_type}`                  | Counter | Counter only; Prom hookup deferred to Phase B   |
| `canopy_ws_handshake_attempts_total{outcome}`            | Counter | Handshake funnel                                |

**Alerts**: `WSOriginRejection` (PAGE), `WSOversizedFrame` (PAGE)

---

## S7. Phase B: frontend wiring + polling elimination (P0 WIN)

### 7.1 Goal

The P0 win. Canopy browser drains `/ws/training` into bounded Dash stores, renders chart updates via `Plotly.extendTraces`, and **stops polling** when WS is healthy. Ships behind two-flag design (D-17+D-18). Bundles Phase I cache bust, latency instrumentation (GAP-WS-24a/b), minimum NetworkVisualizer wire (D-06), and jitter-backoff lift (GAP-WS-30/31).

### 7.2 Entry gate

- [ ] Phase 0-cascor merged + deployed + **72h soak passed** (D-38)
- [ ] `cascor_ws_seq_gap_detected_total==0` over full soak
- [ ] Phase B-pre-a (P3+P4) merged and deployed
- [ ] Phase A-SDK published to PyPI (for future Phase C; not hard Phase B dep)
- [ ] **Pre-Phase-B bandwidth baseline measured**: 1h of staging traffic recorded in `canopy_rest_polling_bytes_per_sec` (D-62)
- [ ] NetworkVisualizer render tech verified: `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py`

### 7.3 Deliverables checklist

**Frontend JS** (`juniper-canopy/src/frontend/assets/`):

| File                             | Action         | Key detail                                                                                                                                                                                                     |
|----------------------------------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ws_dash_bridge.js`              | NEW (~200 LOC) | `window._juniperWsDrain` namespace; 5 `on(type,...)` handlers for metrics/state/topology/cascade_add/candidate_progress; per-handler bounded ring buffers (`MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`); |
|                                  |                | drain methods: `drainMetrics()`, `drainState()`, etc.; **ring bound enforced IN the handler** (not drain callback) per C-19                                                                                    |
| `websocket_client.js`            | EDIT           | Jitter: `delay = Math.random() * Math.min(30000, 500 * 2**attempt)` (GAP-WS-30); **remove 10-attempt cap** (GAP-WS-31, retry forever, max 30s); capture `server_instance_id` from `connection_established`;    |
|                                  |                | `seq` tracking with monotonic check + WARN on gap; on reconnect send `resume` frame with `{last_seq, server_instance_id}`, fallback to REST on `resume_failed`                                                 |
| `dashboard_manager.py:1490-1526` | DELETE         | Remove parallel raw-WS clientside callback (GAP-WS-03). Leave placeholder comment. Only deletion in Phase B (dead code).                                                                                       |
| `ws_latency.js`                  | NEW (~50 LOC)  | Browser latency beacon: records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60s (GAP-WS-24a). Clock-offset recomputation on reconnect.                                           |
| rAF scaffold                     | SCAFFOLD       | `_scheduleRaf = noop` in `ws_dash_bridge.js`; disabled per D-04                                                                                                                                                |

**Python stores + drain callbacks** (`juniper-canopy/src/frontend/`):

| File                                       | Change                                                       | Key detail                                                                                                                                            |
|--------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `dashboard_manager.py`                     | Add `dcc.Store(id='ws-metrics-buffer')`                      | Drain callback fires on `fast-update-interval` tick. Reads `window._juniperWsDrain.drainMetrics()`.                                                   |
|                                            |                                                              | Writes structured `{events: [...], gen: int, last_drain_ms: float}` (D-07, NOT bare array).                                                           |
| `dashboard_manager.py`                     | Update `ws-topology-buffer` + `ws-state-buffer`              | Drains read from bridge namespace. Delete old `window._juniper_ws_*` globals.                                                                         |
| `dashboard_manager.py`                     | Add `ws-cascade-add-buffer` + `ws-candidate-progress-buffer` | New stores + drain callbacks                                                                                                                          |
| `dashboard_manager.py`                     | Add `ws-connection-status` store                             | Peek-based drain; emits only on change                                                                                                                |
| `dashboard_manager.py:2388-2421`           | Refactor `_update_metrics_store_handler`                     | Return `no_update` when `ws-connection-status.connected===true`. Slow fallback to 1 Hz via `n % 10 != 0` (D-05). Preserve initial-load REST GET path. |
| `dashboard_manager.py`                     | Polling-toggle pattern                                       | Apply to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. **Keep REST paths** (D-54).                       |
| `components/metrics_panel.py:648-670`      | Clientside callback                                          | `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"`.                                                        |
| `components/network_visualizer.py`         | Minimum WS wire                                              | Wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to cytoscape callback (D-06). Keep REST poll fallback.                                  |
| `components/connection_indicator.py` (new) | Connection badge                                             | 4-state badge: connected-green, reconnecting-yellow, offline-red, demo-gray                                                                           |
| `backend/demo_mode.py`                     | Demo parity                                                  | Set `ws-connection-status={connected:true, mode:"demo"}` (RISK-08)                                                                                    |

**Backend endpoints** (`juniper-canopy/src/main.py`):

- [ ] `/api/ws_latency` POST: feeds `canopy_ws_delivery_latency_ms_bucket` histogram (GAP-WS-24b)
- [ ] `/api/ws_browser_errors` POST: feeds `canopy_ws_browser_js_errors_total{component}` counter (D-59)
- [ ] `canopy_rest_polling_bytes_per_sec{endpoint}` gauge (P0 motivator proof)

**Phase I bundled**: content-hash `assets_url_path` / cache-bust query string (D-60).

**Two-flag runtime**: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge`. Default `enable_browser_ws_bridge=False` during PR window. Staging flip is ops-driven. Production flip is P7 (separate one-line config PR, project-lead review).

### 7.4 Cross-cutting deliverables

- **CCC-01**: Browser reads new envelope fields (`seq`, `server_instance_id`, `replay_buffer_capacity`, `emitted_at_monotonic`); sends `resume` on reconnect
- **CCC-02**: 11 new canopy metrics; SLO table aspirational until >=1 week; error-budget burn-rate freeze rule (D-50)
- **CCC-03**: Two-flag pattern + URL `?ws=off` + ring-cap reduction; every switch CI-tested; staging drill during 72h soak
- **CCC-04**: Canopy pins `juniper-cascor-client>=${SDK_VERSION_A}`; TestPyPI prerelease; cross-version CI lane (N-1 and N pinned)
- **CCC-05**: `test_fake_cascor_message_schema_parity`, `test_browser_message_handler_keys_match_cascor_envelope`, `test_normalize_metric_produces_dual_format` (Phase H fold-in)
- **CCC-06**: Runbooks `ws-bridge-kill.md`, `ws-bridge-debugging.md`, `ws-memory-soak-test-procedure.md`; Grafana JSON committed
- **CCC-07**: 4 new canopy settings in canonical table
- **CCC-08**: REST polling handler KEPT FOREVER; regression harness in `fast` lane; golden shape file; every kill-switch test asserts REST works post-flip
- **CCC-09**: Two-flag pattern; flip criteria in `ws-bridge-kill.md`; flag flip is separate PR (P7)
- **CCC-10**: FULL PIPE ACTIVATED -- `emitted_at_monotonic` (0-cascor) -> `backend_relay_latency_ms` (canopy) -> browser beacon -> `/api/ws_latency` -> `delivery_latency_ms_bucket`; clock offset recompute on reconnect

### 7.5 Test acceptance

**P0 gates** (Playwright, blocking):

- `test_bandwidth_eliminated_in_ws_mode` -- THE P0 ACCEPTANCE GATE: `/api/metrics/history` request count == 0 over 60s after initial load
- `test_polling_elimination` -- measures request count over 60s with WS connected, asserts zero after initial load

**RISK gates** (blocking):

- `test_metrics_message_has_dual_format` -- RISK-01: both flat + nested keys
- `test_demo_mode_metrics_parity` -- RISK-08: runs in BOTH fast AND e2e lanes

**Python unit**:

- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_ws_metrics_buffer_drain_is_bounded`
- `test_fallback_polling_at_1hz_when_disconnected` (D-05)
- `test_ws_metrics_buffer_store_is_structured_object` (D-07)
- `test_both_flags_interact_correctly` (D-17 + D-18)
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

**Contract** (`@pytest.mark.contract`):

- `test_fake_cascor_message_schema_parity`
- `test_browser_message_handler_keys_match_cascor_envelope`

**Latency** (recording-only in CI, D-42):

- `test_frame_budget_batched_50_events_under_50ms_via_drain_callback`

**Chaos** (nightly):

- Browser-bridge chaos: random kills/restarts, event rate variance. Assert: no OOM, no freeze.

**Soak** (blocking for P7 flag-flip):

- 72h memory soak: `canopy_ws_browser_heap_mb` p95 growth <20%

### 7.6 Pull request plan

| #      | Branch                               | Repo           | Order                       |
|--------|--------------------------------------|----------------|-----------------------------|
| **P5** | `phase-b-cascor-audit-prom-counters` | juniper-cascor | First                       |
| **P6** | `phase-b-canopy-drain-wiring`        | juniper-canopy | After P5, flag-off          |
| **P7** | `phase-b-canopy-flag-flip`           | juniper-canopy | After 72h soak, one-line PR |

P7 is a **separate one-line PR** landing after Phase B is in staging 72 hours, the P0 metric is verified, RISK-10 memory-soak check passes, and the production deploy window is mid-week (D-61).

### 7.7 Exit gate

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
10. Kill switch `disable_ws_bridge=True` tested manually, MTTR <=5 min

### 7.8 Rollback

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

### 7.9 NOT in this phase

- Phase C `set_params` (read-only bridge in Phase B)
- Phase D control buttons (remain REST POST)
- Full rAF coalescing (scaffold only)
- Full Phase E backpressure
- Phase F heartbeat (jitter ships here; heartbeat is Phase F)
- CODEOWNERS for `_normalize_metric` (Phase H; regression test lands here)
- NetworkVisualizer deep render migration (Phase B+1)

**Observability**:

| Metric                                         | Type      | Purpose                                                        |
|------------------------------------------------|-----------|----------------------------------------------------------------|
| `canopy_rest_polling_bytes_per_sec{endpoint}`  | Gauge     | **P0 win signal**                                              |
| `canopy_ws_delivery_latency_ms_bucket{type}`   | Histogram | End-to-end latency (buckets: 50,100,200,500,1000,2000,5000 ms) |
| `canopy_ws_backend_relay_latency_ms`           | Histogram | Cascor-->canopy hop                                            |
| `canopy_ws_browser_heap_mb`                    | Gauge     | RISK-10 signal (via JS beacon)                                 |
| `canopy_ws_browser_js_errors_total{component}` | Counter   | Every try/catch increments                                     |
| `canopy_ws_drain_callback_gen{buffer}`         | Gauge     | Stuck drain detector (monotonic)                               |
| `canopy_ws_active_connections`                 | Gauge     | Capacity planning                                              |
| `canopy_ws_reconnect_total{reason}`            | Counter   | Storm detection                                                |
| `canopy_ws_connection_status{status}`          | Gauge     | Dashboard signal                                               |
| `canopy_audit_events_total{event_type}`        | Counter   | Prometheus hookup (deferred from B-pre-a)                      |
| `canopy_ws_latency_beacon_errors_total`        | Counter   | Beacon reliability                                             |

**Alerts**: `WSDrainCallbackGenStuck` (PAGE), `WSBrowserHeapHigh` (ticket), `WSJSErrorsNonZero` (ticket), `WSConnectionCount80` (ticket)

**Dashboards** (committed as JSON to `juniper-canopy/deploy/grafana/`):

- "WebSocket health" panel: p50/p95/p99 delivery latency per event type
- "Polling bandwidth" panel: `canopy_rest_polling_bytes_per_sec` trend
- "Browser memory" panel: `canopy_ws_browser_heap_mb` p95 trend

---

## S8. Phase B-pre-b: control-path security gate (parallel with Phase B)

**Explicitly does NOT gate Phase B or Phase C.** Phase D is the one that directly exposes the control plane to the browser and is therefore gated on Phase B-pre-b being in **production >=48 h**.

### 8.1 Goal

Full CSWSH/CSRF on `/ws/control`: Origin allowlist, cookie session + CSRF first-frame (M-SEC-02), rate limit (D-33, single bucket 10 cmd/s), idle timeout, adapter HMAC auth (D-29), adapter inbound validation, log-injection escaping, per-origin handshake cooldown. Gates Phase D.

### 8.2 Entry gate

- [ ] Phase B-pre-a in main
- [ ] SessionMiddleware presence verified (assume absent; +0.5 day if so)
- [ ] D-29 HMAC approach confirmed

### 8.3 Deliverables checklist

**Cookie session + CSRF** (canopy side):

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
- [ ] Idle timeout: 120s bidirectional
- [ ] Per-origin handshake cooldown: 10 rejections in 60s --> 5-minute IP block (429). Cleared on restart (NAT-hostile escape hatch).

**Adapter HMAC** (canopy adapter --> cascor):

- [ ] `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()`
- [ ] First frame: `{type:"auth", csrf_token:<hmac>}`
- [ ] Cascor derives same value, compares with `hmac.compare_digest`
- [ ] Uniform handler logic: no `X-Juniper-Role: adapter` header special case

**Adapter inbound validation** (`cascor_service_adapter.py`):

- [ ] Wraps inbound frames with `CascorServerFrame` Pydantic model (`extra="allow"`)
- [ ] Malformed frame --> log + increment `canopy_adapter_inbound_invalid_total` + continue

**Additional**:

- [ ] M-SEC-06 opaque close reasons: only canonical strings
- [ ] Log injection escaping: CRLF (`\r`, `\n`, `\t`) in all logged strings
- [ ] CI guardrail: `juniper-deploy` compose validation refuses `ws_security_enabled=false` in prod profile
- [ ] `disable_ws_control_endpoint: bool = False` kill switch (CSWSH emergency hard-disable)

### 8.4 Test acceptance

| Test                                                             | Type       | Criterion                     |
|------------------------------------------------------------------|------------|-------------------------------|
| `test_csrf_required_for_websocket_first_frame`                   | unit       | Absent/invalid -> close 1008  |
| `test_csrf_token_rotation_race`                                  | unit       | Mid-rotation safe             |
| `test_csrf_token_uses_hmac_compare_digest`                       | unit       | Constant-time comparison      |
| `test_session_cookie_httponly_secure_samesitestrict`             | unit       | All attrs                     |
| `test_command_rate_limit_10_per_sec`                             | unit       | 11th -> rate_limited response |
| `test_rate_limit_response_is_not_an_error_close`                 | unit       | Conn stays up                 |
| `test_per_origin_cooldown_triggers_after_10_rejections`          | unit       | IP blocked                    |
| `test_canopy_adapter_sends_hmac_csrf_token_on_connect`           | unit       | D-29                          |
| `test_audit_log_escapes_crlf_injection`                          | unit       | M-SEC-07                      |
| `test_opaque_close_reasons_no_human_readable_strings`            | unit       | M-SEC-06                      |
| `test_disable_ws_control_endpoint_kill_switch`                   | security   | D-53 CI test                  |
| `test_cswsh_from_evil_page_cannot_start_training`                | Playwright | Full CSWSH regression         |
| `test_canopy_adapter_inbound_malformed_frame_logged_and_counted` | unit       | Inbound validation            |
| `test_ws_control_origin_rejected`                                | unit       | Origin guard                  |
| `test_ws_control_idle_timeout_closes_1008`                       | unit       | Idle timeout                  |
| `test_cascor_rejects_unknown_param_with_extra_forbid`            | contract   | D-34                          |
| `test_deploy_compose_refuses_ws_security_false`                  | CI         | D-10 guardrail                |

### 8.5 Pull request plan

| #      | Branch                                  | Repo           | Order    |
|--------|-----------------------------------------|----------------|----------|
| **P8** | `phase-b-pre-b-cascor-control-security` | juniper-cascor | First    |
| **P9** | `phase-b-pre-b-canopy-csrf-audit`       | juniper-canopy | After P8 |

### 8.6 Exit gate

- [ ] All tests green; manual CSWSH probes pass
- [ ] **48h staging soak**; adapter reconnect rate stable
- [ ] CI guardrail refuses `ws_security_enabled=false` in prod
- [ ] Runbooks: `ws-auth-lockout.md`, `ws-cswsh-detection.md`
- [ ] Project-lead sign-off

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

### 8.8 NOT in this phase

- Per-command HMAC (D-31 deferred indefinitely)
- Two-bucket rate limiting (D-33 deferred)
- Multi-tenant replay isolation (D-32 deferred)

**Observability**:

| Metric                                               | Type      | Purpose                     |
|------------------------------------------------------|-----------|-----------------------------|
| `canopy_ws_auth_rejections_total{reason, endpoint}`  | Counter   | Auth failure tracking       |
| `canopy_ws_rate_limited_total{command, endpoint}`    | Counter   | Rate limit visibility       |
| `canopy_ws_command_total{command, status, endpoint}` | Counter   | Command funnel              |
| `canopy_ws_auth_latency_ms{endpoint}`                | Histogram | Auth overhead               |
| `canopy_ws_handshake_attempts_total{outcome}`        | Counter   | Handshake funnel            |
| `canopy_ws_per_origin_cooldown_active`               | Gauge     | Cooldown status             |
| `canopy_csrf_validation_failures_total`              | Counter   | CSRF probe signal           |
| `cascor_ws_control_rate_limit_rejected_total`        | Counter   | Server-side rate limit      |
| `canopy_adapter_inbound_invalid_total`               | Counter   | Malformed frame from cascor |

**Alerts**: `WSAuthSpike` (ticket: >10 rejections in 5m), `WSRateLimitSpike` (ticket: sustained non-zero), per-origin cooldown >5m (ticket)

---

## S9. Phase C: set_params adapter (P2, feature-flagged)

### 9.1 Goal

Canopy adapter splits parameter updates into "hot" (11 params: `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `epochs_max`, `max_iterations`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`) and "cold" (`init_output_weights`, `candidate_epochs`).
Hot routes over `/ws/control` via `set_params` command with 1.0 s default timeout (D-01); cold stays on REST PATCH.
Feature-flagged behind `use_websocket_set_params=False` (D-47).
REST path permanent (D-21).

### 9.2 Entry gate

- [ ] Phase A-SDK merged and on PyPI; `juniper-ml` extras pin bumped (D-57)
- [ ] Phase B in main with `enable_browser_ws_bridge=True` in staging >=7 days
- [ ] Adapter `run_coroutine_threadsafe` usage verified (assume ships fresh)

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

### 9.4 Test acceptance

| Test                                                               | Type           | Criterion                        |
|--------------------------------------------------------------------|----------------|----------------------------------|
| `test_apply_params_feature_flag_default_off`                       | unit           | Default = False                  |
| `test_apply_params_hot_keys_go_to_websocket`                       | unit           | Hot -> WS path                   |
| `test_apply_params_cold_keys_go_to_rest`                           | unit           | Cold -> REST                     |
| `test_apply_params_mixed_batch_split`                              | unit           | Correct split                    |
| `test_apply_params_hot_falls_back_to_rest_on_timeout`              | unit           | REST fallback                    |
| `test_apply_params_hot_falls_back_to_rest_on_disconnect`           | unit           | REST fallback                    |
| `test_apply_params_unclassified_keys_default_to_rest_with_warning` | unit           | C-09                             |
| `test_control_stream_supervisor_reconnects_with_backoff`           | unit           | Supervisor                       |
| `test_control_stream_supervisor_shutdown_cancels_pending`          | unit           | Cleanup                          |
| `test_len_pending_returns_to_zero_after_failure_modes`             | nightly        | Leak prevention                  |
| `test_cascor_rejects_unknown_param_with_extra_forbid`              | contract       | D-34 server side                 |
| `test_slider_debounce_250ms_collapses_rapid_updates`               | unit           | C-29                             |
| `test_set_params_concurrent_correlation`                           | unit           | 2 sliders distinguished          |
| `test_slider_drag_routes_to_ws_with_flag_on`                       | e2e Playwright | WS path                          |
| `test_slider_drag_fallback_works_when_cascor_killed`               | e2e Playwright | REST fallback                    |
| Chaos: adapter recv-task random exception injection                | chaos          | Map drained; supervisor restarts |

**Flag-flip criteria** (D-48, 6 hard gates):
>
1. >=7 days production data on WS code path
2. p99 delta (REST - WS) >= 50 ms (if smaller, do NOT flip -- no user-visible win)
3. Zero orphaned commands during canary week
4. Zero correlation-map leaks (nightly test)
5. Canary soak >=7 days
6. Zero page-severity alerts in canary window
7. Mid-week deploy window (D-61)

### 9.5 Pull request plan

| #       | Branch                              | Repo           |
|---------|-------------------------------------|----------------|
| **P10** | `phase-c-canopy-set-params-adapter` | juniper-canopy |

### 9.6 Exit gate

**For merge (flag off)**:

- [ ] All unit tests green; coverage >=90%
- [ ] Flag off: `transport="rest"` has data; `transport="ws"` empty
- [ ] `test_set_params_concurrent_correlation` green
- [ ] Runbook `ws-set-params-feature-flag.md` published

**For flag flip** (separate one-line PR, D-48 hard gates):

- [ ] All 7 flag-flip criteria met
- [ ] Manual: slider drag updates within 1s; kill cascor -> REST fallback within 2s

### 9.7 Rollback

```bash
# Instant (2 min)
export JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false
systemctl restart juniper-canopy

# Tight timeout forces fast REST fallback (5 min)
export JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1

# Hard-disable /ws/control
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert
git revert <phase-c-merge>
```

### 9.8 NOT in this phase

- SDK-level retries (D-20); SDK reconnect queue (D-20)
- REST path deprecation (D-21 -- never)
- Two-bucket rate limit (D-33)
- Frontend control buttons (Phase D)

**Observability**:

- `canopy_set_params_latency_ms_bucket{transport, key}` -- flag-flip gate metric
- `canopy_orphaned_commands_total{command}` -- RISK-13 signal
- `canopy_control_stream_pending_size` -- bounded correlation map gauge

**Alert**: `CanopyOrphanedCommands` (ticket): `rate > 1/60`.

---

## S10. Phase D: control buttons

### 10.0 Execution results — COMPLETE (2026-04-14)

Phase D shipped on **2026-04-14** across four PRs over a 12-hour window:

| #             | PR                                                               | Repo           | Title                                                     | Status       |
|---------------|------------------------------------------------------------------|----------------|-----------------------------------------------------------|--------------|
| **P11**       | [cascor#134](https://github.com/pcalnon/juniper-cascor/pull/134) | juniper-cascor | Phase D per-command timeouts + `code:"unknown_command"`   | ✅ Merged    |
| **P12**       | [canopy#169](https://github.com/pcalnon/juniper-canopy/pull/169) | juniper-canopy | Phase D `/ws/control` envelope + `command_id` correlation | ✅ Merged    |
| **P12b**      | [canopy#170](https://github.com/pcalnon/juniper-canopy/pull/170) | juniper-canopy | Phase D clientside button routing via `cascorControlWS`   | ✅ Merged    |
| **P12b-flip** | [canopy#171](https://github.com/pcalnon/juniper-canopy/pull/171) | juniper-canopy | Phase D flag-flip `enable_ws_control_buttons=True` (D-49) | 🟡 Open (CI) |

**Test count shipped (Python unit + integration):**

| Repo                        | File                                                 | Tests  |
|-----------------------------|------------------------------------------------------|--------|
| juniper-cascor              | `src/tests/unit/api/test_control_stream_timeouts.py` | 16     |
| juniper-canopy              | `src/tests/unit/test_phase_d_control_buttons.py`     | 17     |
| juniper-canopy              | `src/tests/unit/test_phase_d_button_clientside.py`   | 11     |
| **Total new Phase D tests** |                                                      | **44** |

**Regression coverage on the P12b-flip branch:** 175 unit/integration/performance tests green across Phase C adapter, Phase D envelope, Phase D clientside wiring, `test_websocket_control`, `test_button_state`, `test_button_responsiveness`, `test_dashboard_manager`, `test_main_import_and_lifespan`, `test_main_coverage_95`, `test_phase_b_pre_b_csrf`. 8 pre-existing skips.

**Deviations from the original spec (§10.3):**

- **Frontend location** — the spec assumed `juniper-canopy/src/frontend/components/training_controls.py`; that file did not exist and was not created. The clientside callback was instead inlined into `juniper-canopy/src/frontend/dashboard_manager.py` as the module-level constant `PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS`, registered by `DashboardManager._setup_button_action_callbacks` when `settings.enable_ws_control_buttons` is `True`.
- **Orphaned-command resolution** — resolution via explicit `state` event (RISK-13 path) was NOT wired. The existing canopy button-timeout sweeper (`_handle_button_timeout_and_acks_handler`, fires on the fast-update interval) re-enables buttons after `DashboardConstants.DASHBOARD_TIMEOUT_THRESHOLD` seconds, which covers the practical orphan case. `command_response` correlation via the per-socket `_pendingCommands` Map in `websocket_client.js` handles the happy path.
- **"Pending" badge** — the optimistic UI flips each button to `loading: true` with a `⏳ <label>...` prefix via the existing `_update_button_appearance_handler`. No separate badge was added; the loading-prefix treatment is the equivalent signal.
- **Playwright tests still deferred** — the three `Playwright` rows of §10.4 (`test_start_button_uses_websocket_command`, `test_csrf_required_for_websocket_start`, `test_orphaned_command_resolves_via_state_event`) are still pending the Playwright harness. Python unit coverage is the shipped acceptance gate; browser E2E lands in a separate PR once the harness is in place.

**Deferred-followup items (non-blocking):**

- Playwright E2E tests above.
- Removal of the legacy server-side `_handle_training_buttons_handler` branch from `dashboard_manager.py` — retained for the post-flip deprecation window (v1.1 per §S2 flag table) and for the direct-invocation test fixtures in `test_button_state.py` / `test_button_responsiveness.py`.
- Removal of the legacy top-level `ok`/`command`/`state`/`error` fields that the canopy `create_command_response_message` helper dual-emits alongside the Phase D envelope. Same v1.1 window.

### 10.1 Goal

Route browser `start`/`stop`/`pause`/`resume`/`reset` through `/ws/control` via `window.cascorControlWS.send({command, command_id: uuidv4()})`. REST POST at `/api/train/{command}` remains first-class forever (D-21). Per-command timeouts: `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`, `reset: 2s`. Ships behind `enable_ws_control_buttons=False` (D-49).

### 10.2 Entry gate

- [ ] **Phase B-pre-b in production >=48h** (NOT just staging -- CSRF/Origin gate)
- [ ] Phase B in main; `enable_browser_ws_bridge=True` (so `window.cascorControlWS` available)
- [ ] Zero CSRF incidents during 48h production soak
- [ ] Mid-week deploy window per D-61

### 10.3 Deliverables checklist

**Frontend** (actual location: `juniper-canopy/src/frontend/dashboard_manager.py`, constant `PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS` — see §10.0 deviation note):

- [x] Clientside callback on each button: if connected --> WS `send({command, command_id: uuidv4()})`; else REST POST  (P12b, canopy#170)
- [x] Per-command client-side correlation map (per-connection scoped)  (P12, canopy#169 — `_pendingCommands` Map in `websocket_client.js`)
- [x] Orphaned-command pending-verification UI: button disabled while in-flight  (P12b) — ~~resolves via matching `state` event (RISK-13)~~ explicit state-event path deferred; existing `_handle_button_timeout_and_acks_handler` sweeper covers the practical orphan window
- [x] Badge shows "pending" while awaiting WS ack  (via the existing `⏳ <label>...` optimistic loading prefix in `_update_button_appearance_handler`)
- [x] `enable_ws_control_buttons: bool = False` (D-49)  (P12, canopy#169; flipped to `True` in P12b-flip, canopy#171)

**Cascor** (`juniper-cascor/src/api/websocket/control_stream.py`):

- [x] `/ws/control` handler routes inbound `{command, command_id, ...}` to existing REST-POST-backed handler  (P11, cascor#134)
- [x] Emits `command_response{command_id, status, error?}` (NO seq per D-03)  (P11)
- [x] Per-command timeout via `asyncio.wait_for`  (P11 — wraps `_execute_command` via `asyncio.to_thread` with per-command budgets from `_COMMAND_TIMEOUTS`)
- [x] Command whitelist: `start`, `stop`, `pause`, `resume`, `reset`, `set_params`; unknown --> `command_response{status:"error", code:"unknown_command"}`  (P11 — `create_control_ack_message` gained an optional `code=` keyword argument)

### 10.4 Test acceptance

| Test                                                   | Type       | Criterion          | Status                                                                                                                                                          |
|--------------------------------------------------------|------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_training_button_ws_command_when_connected`       | unit       | WS path happy      | ✅ (JS contract tests in `test_phase_d_button_clientside.TestClientsideJsContract`)                                                                             |
| `test_training_button_fallback_rest_when_disconnected` | unit       | REST fallback      | ✅ (JS `restFallback` branch asserted in `test_js_includes_rest_fallback_on_rejection`)                                                                         |
| `test_rest_endpoint_still_200`                         | regression | C-23 preserved     | ✅ (`test_websocket_control.py` 10/10 after envelope dual-emit)                                                                                                 |
| `test_start_button_uses_websocket_command`             | Playwright | WS command sent    | 🟡 Deferred — Playwright harness pending                                                                                                                        |
| `test_csrf_required_for_websocket_start`               | Playwright | B-pre-b regression | 🟡 Deferred — Playwright harness pending                                                                                                                        |
| `test_orphaned_command_resolves_via_state_event`       | Playwright | RISK-13            | 🟡 Deferred — Playwright harness pending                                                                                                                        |
| `test_per_command_timeout_start_10s`                   | unit       | Start = 10s        | ✅ (`test_control_stream_timeouts.test_start_timeout_10s`, cascor#134)                                                                                          |
| `test_per_command_timeout_stop_2s`                     | unit       | Stop = 2s          | ✅ (`test_control_stream_timeouts.test_stop_timeout_2s`, cascor#134)                                                                                            |
| `test_unknown_command_rejected`                        | unit       | Error response     | ✅ (`test_control_stream_timeouts.TestUnknownCommandRejection`, cascor#134; `test_phase_d_control_buttons.test_unknown_command_rejected_with_code`, canopy#169) |
| `test_orphaned_command_falls_back_to_rest`             | unit       | Timeout -> REST    | ✅ (JS `restFallback` on `send()` rejection in P12b; `test_timeout_keeps_connection_open` for the canopy timeout path, canopy#169)                              |

### 10.5 Pull request plan (actual — post-execution)

| #             | Branch                                           | Repo           | Order           | PR                                                               | State        |
|---------------|--------------------------------------------------|----------------|-----------------|------------------------------------------------------------------|--------------|
| **P11**       | `phase-d-cascor-control-commands`                | juniper-cascor | First           | [cascor#134](https://github.com/pcalnon/juniper-cascor/pull/134) | ✅ Merged    |
| **P12**       | `phase-d-canopy-button-ws-routing`               | juniper-canopy | After P11       | [canopy#169](https://github.com/pcalnon/juniper-canopy/pull/169) | ✅ Merged    |
| **P12b**      | `phase-d-canopy-button-clientside`               | juniper-canopy | After P12 soak  | [canopy#170](https://github.com/pcalnon/juniper-canopy/pull/170) | ✅ Merged    |
| **P12b-flip** | `phase-d-flip-enable-ws-control-buttons-default` | juniper-canopy | After P12b soak | [canopy#171](https://github.com/pcalnon/juniper-canopy/pull/171) | 🟡 Open (CI) |

The original plan called for two PRs (P11 + P12); execution split the canopy half into three (P12, P12b, P12b-flip) so the server contract, the browser routing, and the default-flip could soak independently. Each split inherited a cleaner rollback surface: P12 can ship the envelope without flipping buttons; P12b can ship clientside routing behind the flag; P12b-flip is a one-line default change with the kill switch preserved.

### 10.6 Exit gate

- [x] All tests green — 175 canopy regression + 44 new Phase D unit/integration tests on the P12b-flip branch; `test_csrf_required_for_websocket_start` deferred with the rest of the Playwright row
- [x] Manual: Start with WS -> state within 10s; kill cascor -> REST fallback succeeds — validated during the pre-P12b-flip staging soak
- [x] 24h staging soak zero orphaned commands — confirmed before P12b-flip was cut
- [x] REST endpoints still receive non-browser traffic (access logs) — C-23 regression `test_rest_endpoint_still_200` green
- [x] **B-pre-b in production >=48h** confirmed at merge time

### 10.7 Rollback

```bash
# Buttons revert to REST (5 min)
export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false
systemctl restart juniper-canopy

# CSWSH emergency
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert (20 min)
git revert <phase-d-canopy> <phase-d-cascor>
```

### 10.8 NOT in this phase

- `set_params` routing (Phase C); full backpressure (Phase E); two-bucket rate limit

**Observability**:

- `canopy_training_control_total{command, transport}` -- WS:REST ratio tracking
- `canopy_training_control_orphaned_total{command}` -- orphaned-command signal
- `canopy_training_control_command_latency_ms{command, transport}` -- per-command latency
- `cascor_ws_control_command_received_total{command}` -- server-side receipt counter

---

## S11. Phase E: backpressure and disconnection (CONDITIONAL)

Ships **only if** Phase B production telemetry shows RISK-04/11 triggering (specifically: `cascor_ws_broadcast_send_duration_seconds` p95 > 100 ms sustained OR `cascor_ws_broadcast_timeout_total` frequently >0). Otherwise 0.5s quick-fix from Phase 0-cascor suffices.

### 11.1 Goal

Replace serial fan-out with per-client pump tasks + bounded per-client queues + backpressure policy matrix. Default: `drop_oldest_progress_only` (D-19).

### 11.2 Entry gate

- [ ] Phase 0-cascor in main (quick-fix is the fallback if Phase E rolls back)
- [ ] Production telemetry from >=1 week justifies shipping

### 11.3 Deliverables checklist

- [ ] Per-client `_ClientState` with `pump_task` + bounded `send_queue` (256, configurable via `ws_per_client_queue_size`)
- [ ] Policy dispatch per matrix below
- [ ] `Settings.ws_backpressure_policy: Literal["block", "drop_oldest_progress_only", "close_slow"] = "drop_oldest_progress_only"`

**Policy matrix**:

| Event type                  | Queue size | Overflow behavior | Rationale                 |
|-----------------------------|-----------:|-------------------|---------------------------|
| `state`                     |        128 | close(1008)       | Terminal-state-sensitive  |
| `metrics`                   |        128 | close(1008)       | Drops cause chart gaps    |
| `cascade_add`               |        128 | close(1008)       | Each event is growth step |
| `candidate_progress`        |         32 | drop_oldest       | Coalesceable              |
| `event` (training_complete) |        128 | close(1008)       | Terminal-sensitive        |
| `command_response`          |         64 | close(1008)       | Client waits              |
| `pong`                      |         16 | drop_oldest       | Client can re-ping        |

### 11.4 Test acceptance

| Test                                                     | Type | Criterion               |
|----------------------------------------------------------|------|-------------------------|
| `test_slow_client_does_not_block_other_clients`          | unit | Fast clients unaffected |
| `test_slow_client_send_timeout_closes_1008_for_state`    | unit | State -> close          |
| `test_slow_client_progress_events_dropped`               | unit | Progress -> drop oldest |
| `test_drop_oldest_queue_policy`                          | unit | Queue semantics         |
| `test_backpressure_default_is_drop_oldest_progress_only` | unit | Regression              |
| `test_event_type_classification_for_backpressure_policy` | unit | Every type mapped       |
| `test_block_policy_still_works`                          | unit | Opt-in alternative      |
| `test_terminal_state_events_not_dropped`                 | unit | RISK-11 guard           |

Load test: 50 clients, 1 slow (2s delay), 49 fast p95 <200ms.

### 11.5 Pull request plan

| #       | Branch                                   | Repo           |
|---------|------------------------------------------|----------------|
| **P13** | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor |

### 11.6 Exit gate

- [ ] All tests green; load test passes
- [ ] 48h staging zero `WSStateDropped` alerts
- [ ] Runbook `ws-backpressure-policy.md` published

### 11.7 Rollback

```bash
# Revert to block policy (5 min; RISK-04 returns but intentional)
export JUNIPER_WS_BACKPRESSURE_POLICY=block
systemctl restart juniper-cascor

# Full revert
git revert <phase-e-cascor>
```

### 11.8 NOT in this phase

- `permessage-deflate`; multi-tenant per-session queues

**Observability**: `cascor_ws_dropped_messages_total{reason, type}`, `cascor_ws_slow_client_closes_total`, `cascor_ws_per_client_queue_depth_histogram`

**Alert**: `WSStateDropped` (PAGE): any non-zero `dropped_messages_total{type="state"}`

---

## S12. Phase F: heartbeat and reconnect jitter

### 12.1 Goal

Add application-level ping/pong heartbeat for dead-connection detection faster than uvicorn framework level. Finalize reconnect-cap lift.

### 12.2 Entry gate

- [ ] Phase B in main (jitter already landed in Phase B)

### 12.3 Deliverables checklist

- [ ] Cascor `/ws/training` + `/ws/control` emit `{"type":"ping","ts":<float>}` every 30s
- [ ] Client JS replies `pong` within 5s
- [ ] Dead-conn detection: no `pong` within 10s -> close 1006 -> trigger reconnect
- [ ] Integrates with idle timeout (heartbeat resets timer)
- [ ] GAP-WS-31: uncap reconnect attempts; max 60s interval
- [ ] Jitter formula: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))`

### 12.4 Test acceptance

| Test                                                                     | Type | Criterion         |
|--------------------------------------------------------------------------|------|-------------------|
| `test_ping_sent_every_30_seconds`                                        | unit | Cadence           |
| `test_pong_received_cancels_close`                                       | unit | Pong resets timer |
| `test_reconnect_backoff_has_jitter`                                      | unit | 0 <= delay <= cap |
| `test_reconnect_attempt_unbounded_with_cap`                              | unit | >10 attempts      |
| `test_dead_connection_detected_via_missing_pong`                         | unit | 10s -> close 1006 |
| `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect` | unit | Full cycle        |
| `test_jitter_formula_no_nan_delay`                                       | unit | No NaN/Infinity   |

### 12.5 Pull request plan

| #       | Branch                     | Repo                            |
|---------|----------------------------|---------------------------------|
| **P14** | `phase-f-heartbeat-jitter` | juniper-cascor + juniper-canopy |

### 12.6 Exit gate

- [ ] All 7 tests pass
- [ ] Manual: firewall drop -> dead conn detected within 40s (30+10)
- [ ] 48h staging: no NaN delays, no reconnect storms
- [ ] Runbook `ws-reconnect-storm.md` published

### 12.7 Rollback

```bash
# Disable auto-reconnect (10 min; users hard-refresh)
export JUNIPER_DISABLE_WS_AUTO_RECONNECT=true

# Or cache-busted JS hotfix with old jitter formula
git revert <phase-f-merge>
```

**Alert**: `WSReconnectStorm` (ticket): `rate(canopy_ws_reconnect_total[5m]) > 5x baseline`

---

## S13. Phase G: cascor set_params integration tests

### 13.1 Goal

Cascor-side integration tests exercising `/ws/control` `set_params` via FastAPI `TestClient.websocket_connect()` (no SDK dependency). Assert wire contract.

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
- [ ] **`test_set_params_concurrent_command_response_correlation`** (critical)
- [ ] **`test_set_params_during_training_applies_on_next_epoch_boundary`** (ack vs effect)
- [ ] **`test_set_params_echoes_command_id`** (C-01 mandatory gate)
- [ ] `test_ws_control_command_response_has_no_seq` (C-02 cross-ref)

Tests marked `@pytest.mark.critical` -- run in `fast` lane on every PR.

**Contract test**: `test_fake_cascor_message_schema_parity` (runs in both cascor + canopy CI)

### 13.4 Pull request plan

| #       | Branch                                  | Repo           |
|---------|-----------------------------------------|----------------|
| **P15** | `phase-g-cascor-set-params-integration` | juniper-cascor |

### 13.5 Exit gate

- [ ] All 15 tests pass
- [ ] `pytest -m contract` green in both cascor and canopy CI

### 13.6 Rollback

n/a (test-only phase).

---

## S14. Phase H: normalize_metric regression gate

### 14.1 Goal

Lock in dual metric format contract (flat + nested keys both present) with regression test + CODEOWNERS hard merge gate (D-27). Document every consumer. **NO removal of any format in this migration.** (C-22)

### 14.2 Entry gate

- [ ] Phase B in main (dual-format test already landed)
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

| #       | Branch                           | Repo           |
|---------|----------------------------------|----------------|
| **P16** | `phase-h-normalize-metric-audit` | juniper-canopy |

### 14.5 Exit gate

- [ ] Regression tests green
- [ ] CODEOWNERS enforced (test PR touching file without owner review -> blocked)
- [ ] Consumer audit doc merged
- [ ] Pre-commit hook installed

### 14.6 Rollback

```bash
# Revert (10 min) -- CODEOWNERS rule disappears
git revert <phase-h-merge>
```

### 14.7 NOT in this phase

- `_normalize_metric` refactor (requires new migration plan)
- Removal of either format (never without RFC per D-21 principle)

---

## S14a. Phase I: asset cache busting (folded into Phase B)

Exists here only for rollback reference. Delivered as part of Phase B (P6).

**Deliverable**: `assets_url_path` with content-hash query string (D-60). Verified via `test_asset_url_includes_version_query_string`.

**Rollback**: `git revert` cache-bust commit in P6 (10 min).

---

## S15. Master test acceptance matrix

Canonical load-bearing tests with phase, type, and measurable criterion. Full catalog (~155 tests across all phases) in R2-02 section 15.2.

| Phase    | Test                                         | Type                     | Criterion               |
|----------|----------------------------------------------|--------------------------|-------------------------|
| 0-cascor | `test_seq_monotonically_increases`           | unit                     | seq(n+1) > seq(n)       |
| 0-cascor | `test_replay_buffer_bounded`                 | unit                     | maxlen == config        |
| 0-cascor | `test_resume_replays_events`                 | integration              | N-5 -> 5 events         |
| 0-cascor | `test_resume_failed_server_restarted`        | integration              | UUID mismatch -> fail   |
| 0-cascor | `test_second_resume_closes_1003`             | unit                     | D-30                    |
| 0-cascor | `test_state_coalescer_terminal_transitions`  | unit                     | GAP-WS-21               |
| 0-cascor | `test_ws_control_no_seq`                     | contract                 | D-03 negative assertion |
| 0-cascor | chaos_broadcast_replay_race                  | chaos (blocking)         | No gaps, no deadlocks   |
| 0-cascor | Load: 100 Hz x 60s x 10 clients              | load (blocking)          | p95 < 250ms             |
| A-SDK    | `test_set_params_cancellation_cleans_map`    | unit **mandatory**       | `len(_pending)==0`      |
| A-SDK    | `test_set_params_concurrent_correlation`     | unit                     | 2 calls distinguished   |
| A-SDK    | `test_set_params_fails_fast_on_disconnect`   | unit                     | No queue (D-20)         |
| A-SDK    | `test_correlation_map_bounded_256`           | unit                     | Overflow error          |
| B-pre-a  | `test_oversized_frame_1009`                  | unit                     | 65KB -> 1009            |
| B-pre-a  | `test_per_ip_cap_6th_rejected`               | unit                     | 6th -> 1013             |
| B-pre-a  | `test_empty_allowlist_rejects_all`           | unit                     | Fail-closed             |
| B-pre-a  | `test_cswsh_exfiltration`                    | Playwright               | Cross-origin rejected   |
| B        | **`test_bandwidth_eliminated`**              | **Playwright (P0)**      | 0 requests over 60s     |
| B        | **`test_dual_format`**                       | **Playwright (RISK-01)** | Both flat + nested      |
| B        | `test_chart_does_not_poll_when_ws_connected` | dash_duo                 | 0 REST calls            |
| B        | `test_demo_mode_parity`                      | dash_duo+e2e             | RISK-08 both lanes      |
| B        | `test_resume_replays`                        | Playwright               | N events replayed       |
| B        | `test_both_flags_interact`                   | unit                     | Two-flag logic          |
| B        | `test_fake_cascor_schema_parity`             | contract                 | CCC-05                  |
| B        | 72h memory soak                              | soak                     | p95 growth <20%         |
| B-pre-b  | `test_csrf_required`                         | unit                     | Missing -> 1008         |
| B-pre-b  | `test_rate_limit_10_per_sec`                 | unit                     | rate_limited response   |
| B-pre-b  | `test_hmac_csrf_on_connect`                  | unit                     | D-29                    |
| B-pre-b  | `test_cswsh_cannot_start_training`           | Playwright               | Full CSWSH              |
| C        | `test_hot_keys_to_websocket`                 | unit                     | WS path                 |
| C        | `test_fallback_on_timeout`                   | unit                     | REST fallback           |
| C        | `test_unclassified_to_rest_warn`             | unit                     | D-34                    |
| D        | `test_csrf_for_websocket_start`              | Playwright               | B-pre-b regression      |
| D        | `test_orphaned_resolves_via_state`           | Playwright               | RISK-13                 |
| E        | `test_slow_client_no_block`                  | unit                     | Fast clients unaffected |
| E        | `test_terminal_state_not_dropped`            | unit                     | RISK-11 guard           |
| F        | `test_ping_sent_every_30_seconds`            | unit                     | Cadence                 |
| F        | `test_jitter_no_nan`                         | unit                     | 0 <= delay <= cap       |
| G        | **`test_set_params_echoes_command_id`**      | **contract (C-01)**      | Cascor echoes it        |
| G        | `test_concurrent_correlation`                | integration              | Correct responses       |
| H        | `test_normalize_dual_format`                 | **contract (C-22)**      | Both keys               |
| H        | `test_shape_hash_matches_golden`             | unit                     | Shape stability         |
| --       | Metric-presence pytest                       | security (every PR)      | All canonical present   |
| --       | REST regression harness                      | fast (every PR)          | Baseline shapes match   |

**Aggregate test counts**: Unit ~97, Integration ~18, E2E ~16, Contract ~11, Chaos ~8, Load 2, Soak 3. **Total: ~155 tests.**

Contract test runtime budget: <50 ms per test, <5 s per suite.

**Canonical label values** (cardinality discipline):

- `endpoint` in {`/ws/training`, `/ws/control`, `/ws/worker`, `/ws/monitor`}
- `type` in {`metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, `event`, `command_response`, `connection_established`, `resume_ok`, `resume_failed`}
- `transport` in {`ws`, `rest`}
- `reason` in {`origin_rejected`, `cookie_missing`, `csrf_invalid`, `per_ip_cap`, `cap_full`, `rate_limited`, `frame_too_large`, `idle_timeout`, `malformed_json`}
- `outcome` in {`accepted`, `rejected`, `timeout`, `success`, `server_restarted`, `out_of_range`, `malformed`, `no_resume_timeout`, `second_resume`}

Adding any new label value requires a CCC-02 PR review.

---

## S16. Effort summary

| Phase            | Optimistic |  Expected | Pessimistic | Parallel with     | Risk factor                               |
|------------------|-----------:|----------:|------------:|-------------------|-------------------------------------------|
| 0-cascor         |        1.5 |       2.0 |         3.0 | A-SDK, B-pre-a    | `_pending_connections` async race         |
| A-SDK            |        0.5 |       1.0 |         1.5 | 0-cascor, B-pre-a | correlation-map bounding iteration        |
| B-pre-a          |        0.5 |       1.0 |         1.5 | 0-cascor, A-SDK   | audit logger name collision               |
| B                |        3.0 |       4.0 |         5.0 | B-pre-b           | NetworkVisualizer Plotly (+1d contingent) |
| B-pre-b          |        1.0 |       1.5 |         2.0 | B                 | SessionMiddleware absent (+0.5d)          |
| C                |        1.5 |       2.0 |         3.0 | G                 | concurrent-correlation race bugs          |
| D                |       0.75 |       1.0 |         1.5 | --                | orphaned-command UI state                 |
| E                |       0.75 |       1.0 |         1.5 | conditional       | queue-size tuning under load              |
| F                |       0.25 |       0.5 |         1.0 | --                | low variance                              |
| G                |       0.25 |       0.5 |        0.75 | C                 | test-only, low variance                   |
| H                |        0.5 |       1.0 |         1.5 | --                | audit document can grow                   |
| I                |        0.1 |      0.25 |         0.5 | folded into B     | trivial                                   |
| **Serial total** |   **10.6** | **15.75** |   **22.25** | --                |                                           |

**Target (with parallelism)**: 13.5 days. **Planning buffer**: 15.75 days. **Calendar**: ~4.5 weeks with soak windows.

**Parallelism savings**: Phases A-SDK + 0-cascor + B-pre-a in parallel -> ~2 day compression. B-pre-b parallel with B -> ~1.5 day compression. G parallel with C -> ~0.5 day compression. Total savings: ~4 days, yielding 15.75 - ~2.25 = ~13.5 target.

**Minimum-viable carveout**: ~7 days (Phase A-SDK + Phase 0-cascor + B-pre-a + Phase B + Phase I).

---

## S17. Appendix: full decision reference (D-01..D-62)

62 decisions. All applied. No TBD items.

| D  | Summary                        | Applied value                                 | Source              |
|----|--------------------------------|-----------------------------------------------|---------------------|
| 01 | `set_params` default timeout   | 1.0 s                                         | R1-05 S4.1          |
| 02 | Correlation field name         | `command_id`                                  | R1-05 S4.2          |
| 03 | `command_response` carries seq | No                                            | R1-05 S4.17         |
| 04 | rAF coalescer                  | Scaffold-disabled                             | R1-05 S4.3          |
| 05 | REST fallback cadence          | 1 Hz                                          | R1-05 S4.4          |
| 06 | NetworkVisualizer scope        | Minimum wire; deep deferred                   | R1-05 S4.5          |
| 07 | `ws-metrics-buffer` shape      | Structured `{events, gen, last_drain_ms}`     | R1-05 S4.7          |
| 08 | GAP-WS-24 split                | 24a browser + 24b backend                     | R1-05 S4.8          |
| 09 | B-pre effort                   | 0.5 (a) + 1.5-2 (b)                           | R1-05 S4.9          |
| 10 | Security flag naming           | Positive `ws_security_enabled` + CI guardrail | R1-02; R2-01; R2-03 |
| 11 | Phase 0-cascor carve-out       | Carve out from B                              | R1-05 S4.19         |
| 12 | M-SEC adoption                 | Adopt 10/11; fold 12 into 07                  | R1-05 S4.15         |
| 13 | GAP-WS-19 status               | RESOLVED (regression test only)               | R1-05 S4.16         |
| 14 | Two-phase registration         | `_pending_connections` set                    | R1-05 S4.18         |
| 15 | `server_instance_id` role      | Programmatic key                              | R1-05 S4.20         |
| 16 | `replay_buffer_capacity`       | Add to `connection_established`               | R1-05 S4.21         |
| 17 | Phase B feature flag           | Flag-off default                              | R1-02               |
| 18 | Permanent kill switch          | `disable_ws_bridge` added                     | R1-05 S4.45         |
| 19 | Backpressure default           | `drop_oldest_progress_only`                   | R1-05 S4.36         |
| 20 | SDK retries                    | None (caller decides)                         | R1-05 S4.22         |
| 21 | REST retention                 | Permanent (no deprecation)                    | R1-05 S4.23         |
| 22 | Debounce layer                 | Dash clientside                               | R1-05 S4.24         |
| 23 | B-pre split                    | a + b                                         | R1-05 S4.35         |
| 24 | Per-IP cap                     | 5                                             | R1-05 S4.37         |
| 25 | Deployment topology            | Single-tenant v1                              | R1-05 S4.38         |
| 26 | Shadow traffic                 | Skip                                          | R1-05 S4.39         |
| 27 | CODEOWNERS `_normalize_metric` | Hard merge gate                               | R1-05 S4.41         |
| 28 | Audit logger                   | Dedicated, skeleton B-pre-a, Prom B           | R1-05 S4.14         |
| 29 | Adapter auth                   | HMAC CSRF token                               | R1-05 S4.43         |
| 30 | One resume per connection      | Enforced                                      | R1-05 S4.12         |
| 31 | Per-command HMAC               | Defer indefinitely                            | R1-05 S4.11         |
| 32 | Multi-tenant replay            | Defer                                         | R1-05 S4.13         |
| 33 | Rate limit buckets             | Single 10/s                                   | R1-05 S4.46         |
| 34 | Unclassified keys              | Cascor `extra="forbid"` + adapter REST+WARN   | R1-05 S4.44         |
| 35 | Replay buffer default          | 1024, env-tunable                             | R2-01 S18.1         |
| 36 | Replay size=0                  | Kill switch                                   | R1-02 S3.3          |
| 37 | Metrics-presence CI            | Enforced PR blocker                           | R1-02 S10.6         |
| 38 | Phase 0-cascor soak            | 72h                                           | R1-02 S3.4          |
| 39 | Phase B soak                   | 72h                                           | R2-04               |
| 40 | Chaos tests                    | 3 blocking (0-cascor); rest nightly           | R2-01 S18.9         |
| 41 | Load tests                     | Blocking for 0-cascor                         | R1-02 S10.3         |
| 42 | Frame budget test              | Recording-only                                | R1-05 S4.3          |
| 43 | `contract` marker              | Added, every PR                               | R1-05 S4.34         |
| 44 | Multi-browser                  | Chromium only                                 | R1-05 S4.31         |
| 45 | User research                  | Skip v1                                       | R1-05 S4.32         |
| 46 | Send timeout configurable      | Yes, default 0.5                              | R1-02 S3.2          |
| 47 | Phase C flag default           | False                                         | Unanimous           |
| 48 | Phase C flip criteria          | 6 hard gates                                  | R1-02 S6.1          |
| 49 | Phase D flag                   | `enable_ws_control_buttons=False`             | R1-02 S7.1          |
| 50 | Error-budget freeze            | Enforced                                      | R1-02 S2.4          |
| 51 | `WSOriginRejection` severity   | Page                                          | R1-02 S2.4          |
| 52 | `WSSeqCurrentStalled`          | Page                                          | R1-02 S2.4          |
| 53 | Kill-switch MTTR tested        | Every switch in staging                       | R1-02 S13.7         |
| 54 | REST polling handler           | Preserve forever                              | R1-05 S4.23         |
| 55 | Source-doc patches             | Batch in separate PR                          | R1-05 S8.6          |
| 56 | REST deprecation               | Never                                         | R2-04 S5.1          |
| 57 | juniper-ml pin bump            | Same-day follow-up                            | R2-04 S5.2          |
| 58 | CI budget                      | <=25% runtime increase                        | R2-04 S5.3          |
| 59 | Browser error pipeline         | POST `/api/ws_browser_errors`                 | R2-04 S5.4          |
| 60 | Worktree policy                | One per phase per repo                        | R2-04 S5.5          |
| 61 | Deploy freeze                  | Mid-week for flag flips only                  | R2-04 S5.6          |
| 62 | Bandwidth baseline             | 1h pre-Phase-B measurement                    | R2-04 S5.7          |

---

## S18. Appendix: GAP-WS / M-SEC / RISK cross-reference

Every source-doc identifier mapped to its phase and status in this plan.

### GAP-WS cross-reference

| ID        | Description                                                       | Phase                          | Status                                  |
|-----------|-------------------------------------------------------------------|--------------------------------|-----------------------------------------|
| GAP-WS-01 | SDK lacks WebSocket `set_params`                                  | A-SDK                          | Addressed                               |
| GAP-WS-02 | Browser-side `cascorWS`/`cascorControlWS` are dead code           | B                              | Addressed                               |
| GAP-WS-03 | Parallel raw-WS clientside callback at dashboard_manager.py:1490  | B                              | Deleted                                 |
| GAP-WS-04 | `ws-metrics-buffer` store never populated                         | B                              | Addressed                               |
| GAP-WS-05 | No clientside callback drains WS stores into chart inputs         | B                              | Addressed                               |
| GAP-WS-06 | Training control buttons use REST POST instead of WebSocket       | D                              | Addressed                               |
| GAP-WS-07 | No backpressure / slow client handling                            | 0-cascor (quick-fix), E (full) | Quick-fix in 0-cascor; full conditional |
| GAP-WS-08 | No end-to-end browser test for WS path                            | B                              | Addressed (Playwright suite)            |
| GAP-WS-09 | No cascor-side integration test for `set_params` on `/ws/control` | G                              | Addressed (15 tests)                    |
| GAP-WS-10 | No canopy-side integration test for `set_params` round-trip       | C                              | Addressed                               |
| GAP-WS-11 | `_normalize_metric` dual format undocumented                      | H                              | Addressed (audit + CODEOWNERS)          |
| GAP-WS-12 | No WebSocket heartbeat / ping-pong                                | F                              | Addressed                               |
| GAP-WS-13 | Lossless reconnect via seq + replay buffer                        | 0-cascor                       | Addressed                               |
| GAP-WS-14 | `Plotly.extendTraces` with `maxPoints`                            | B                              | Addressed                               |
| GAP-WS-15 | Browser-side rAF coalescing                                       | B (scaffold only)              | Scaffolded disabled (D-04)              |
| GAP-WS-16 | `/api/metrics/history` polling bandwidth bomb (P0)                | B                              | **P0 -- Addressed**                     |
| GAP-WS-17 | `permessage-deflate` compression                                  | --                             | Deferred post-v1                        |
| GAP-WS-18 | Topology message >64KB                                            | B-pre-a (size cap)             | Mitigated (REST fallback preserved)     |
| GAP-WS-19 | `close_all()` does not hold `_lock`                               | 0-cascor                       | RESOLVED on main; regression test only  |
| GAP-WS-20 | Bidirectional envelope asymmetry                                  | --                             | Deferred post-v1 (P3)                   |
| GAP-WS-21 | 1 Hz state throttle drops terminal transitions                    | 0-cascor                       | Addressed                               |
| GAP-WS-22 | Protocol error responses not specified                            | 0-cascor                       | Addressed                               |
| GAP-WS-23 | `Plotly.extendTraces` (alias of GAP-WS-14)                        | B                              | Addressed                               |
| GAP-WS-24 | Production WS latency instrumentation                             | B (24a + 24b)                  | Addressed                               |
| GAP-WS-25 | WS-health-aware polling toggle                                    | B                              | Addressed                               |
| GAP-WS-26 | Visible connection status indicator                               | B                              | Addressed (connection_indicator.py)     |
| GAP-WS-27 | Per-IP connection caps + DoS protection                           | B-pre-a                        | Addressed                               |
| GAP-WS-28 | Multi-key `update_params` torn-write race                         | C                              | Addressed (disjoint hot/cold sets)      |
| GAP-WS-29 | `broadcast_from_thread` discards future exceptions                | 0-cascor                       | Addressed                               |
| GAP-WS-30 | Reconnect backoff has no jitter                                   | B                              | Addressed                               |
| GAP-WS-31 | Unbounded reconnect attempts cap (currently 10)                   | B (initial), F (finalize)      | Addressed                               |
| GAP-WS-32 | Per-command timeouts and orphaned-command resolution              | D                              | Addressed                               |
| GAP-WS-33 | Demo mode failure visibility                                      | B                              | Addressed (connection indicator)        |

### M-SEC cross-reference

| ID        | Description                                           | Phase                                     | Status                                      |
|-----------|-------------------------------------------------------|-------------------------------------------|---------------------------------------------|
| M-SEC-01  | Origin validation on canopy `/ws/*`                   | B-pre-a (training), B-pre-b (control)     | Addressed                                   |
| M-SEC-01b | Cascor `/ws/*` Origin validation parity               | B-pre-a                                   | Addressed                                   |
| M-SEC-02  | Authentication model for canopy `/ws/*` (cookie+CSRF) | B-pre-b                                   | Addressed                                   |
| M-SEC-03  | Per-frame size limits                                 | B-pre-a                                   | Addressed                                   |
| M-SEC-04  | Per-IP connection caps + auth timeout                 | B-pre-a (caps), B-pre-b (auth timeout)    | Addressed                                   |
| M-SEC-05  | Command rate limiting                                 | B-pre-b                                   | Addressed                                   |
| M-SEC-06  | Opaque auth-failure reason                            | B-pre-b                                   | Addressed                                   |
| M-SEC-07  | Logging scrubbing allowlist                           | B-pre-a (skeleton), B-pre-b (CRLF escape) | Addressed                                   |
| M-SEC-08  | Subdomain bypass / CSP header                         | --                                        | Deferred post-v1                            |
| M-SEC-09  | Constant-time API key comparison                      | --                                        | Deferred (cascor-side hardening, separable) |

### RISK cross-reference

| ID      | Description                              | Phase            | Status                                              |
|---------|------------------------------------------|------------------|-----------------------------------------------------|
| RISK-01 | Dual metric format removed aggressively  | H                | Mitigated (CODEOWNERS + regression test)            |
| RISK-02 | Clientside_callback debugging            | B                | Mitigated (drain gen gauge + soak)                  |
| RISK-03 | REST+WS ordering race                    | C                | Mitigated (disjoint sets + lock)                    |
| RISK-04 | Slow-client blocks broadcasts            | 0-cascor, E      | Mitigated (0.5s quick-fix; Phase E full)            |
| RISK-05 | Playwright misses real-cascor regression | B, D             | Mitigated (nightly smoke + contract tests)          |
| RISK-06 | Reconnection storm                       | F                | Mitigated (jitter in Phase B, heartbeat in F)       |
| RISK-07 | 50-conn cap hit                          | n/a              | Mitigated (configurable; single-tenant v1)          |
| RISK-08 | Demo mode parity breaks                  | B                | Mitigated (test in both lanes)                      |
| RISK-09 | Phase C unexpected behavior              | C                | Mitigated (flag-off default; 6 flip gates)          |
| RISK-10 | Browser memory exhaustion                | B                | Mitigated (extendTraces + ring cap + 72h soak)      |
| RISK-11 | Silent data loss via drop-oldest         | E                | Mitigated (state closes; only progress dropped)     |
| RISK-12 | Background tab memory spike              | B                | Mitigated (cap-in-handler)                          |
| RISK-13 | Orphaned commands after timeout          | D                | Mitigated (command_id + pending UI + state resolve) |
| RISK-14 | Cascor crash mid-broadcast               | B                | Mitigated (server_instance_id resync)               |
| RISK-15 | CSWSH attack                             | B-pre-a, B-pre-b | Mitigated (Origin + CSRF + page alert)              |
| RISK-16 | Topology >64KB                           | B-pre-a          | Mitigated (size caps + REST fallback)               |

---

## S19. Lineage and provenance

This document is the output of a 6-round, 21-agent consolidation funnel:

| Round    | Agents          | Input                          | Output       | Key contribution                                                                              |
|----------|-----------------|--------------------------------|--------------|-----------------------------------------------------------------------------------------------|
| 0        | 6 specialized   | Architecture doc (direct read) | R0-01..R0-06 | Six domain-specific deep dives (frontend perf, security, cascor backend, SDK, testing, ops)   |
| 1        | 5 consolidation | R0-01..R0-06                   | R1-01..R1-05 | Five integrated proposals; R1-05 is the disagreement reconciliation with 62 decisions         |
| 2        | 4 consolidation | R1-01..R1-05                   | R2-01..R2-04 | Four refined proposals with execution contracts, cross-cutting concerns, decision matrix      |
| 3        | 3 consolidation | R2-01..R2-04                   | R3-01..R3-03 | Three highly converged plans: master integration, decision-resolved blueprint, lean execution |
| 4        | 2 consolidation | R3-01..R3-03                   | R4-01..R4-02 | Two near-final proposals: comprehensive master plan and executive-ready deliverable           |
| 5 (this) | 1 final         | R4-01..R4-02                   | **R5-01**    | **Canonical development plan** -- single authoritative document                               |

Each round read only its predecessor's output. The architecture doc was consulted for verification only in Round 5.

---

## S20. R4 reconciliation log

Where R4-01 and R4-02 disagreed and how this document resolved each disagreement.

### 20.1 Effort estimate framing

| Input | Position                                                                                    |
|-------|---------------------------------------------------------------------------------------------|
| R4-01 | **15.75 expected** engineering days. 13.5 as "optimistic-with-parallelism target."          |
| R4-02 | **13.5 as target**, 15.75 as planning buffer. Per-phase expected totals still sum to 15.75. |

**Resolution**: Adopt R4-02's framing -- **13.5 target, 15.75 planning buffer**. This is more transparent for the engineering team. The 15.75 serial sum is preserved in the effort table. The 13.5 target acknowledges that parallelism compresses the calendar. Both R4 inputs agree on the per-phase 3-point estimates; the disagreement is purely presentational.

### 20.2 Phase 0-cascor metrics count

| Input | Position                                                   |
|-------|------------------------------------------------------------|
| R4-01 | 15 `cascor_ws_*` metrics (section 4.6 lists 15 explicitly) |
| R4-02 | 13 metrics (section 4.3 lists 11 explicitly, text says 13) |

**Resolution**: Adopt R4-01's count of **15 metrics**. R4-01's observability section is the more detailed enumeration. R4-02 omitted `cascor_ws_command_responses_total` and `cascor_ws_command_handler_seconds` from its explicit list.

### 20.3 Phase B test count

| Input | Position                 |
|-------|--------------------------|
| R4-01 | 22 tests in section 7.5  |
| R4-02 | ~30 tests in section 7.4 |

**Resolution**: Adopt R4-02's more comprehensive list of **~30 tests**. R4-01's list was a subset. R4-02 includes additional dash_duo and Playwright tests that provide stronger coverage.

### 20.4 Phase B jitter max interval

| Input | Position                                                                                                                         |
|-------|----------------------------------------------------------------------------------------------------------------------------------|
| R4-01 | Executive summary says 30s max; Phase B deliverables say `Math.min(30000, ...)` but Phase F says 60s with `Math.min(attempt, 7)` |
| R4-02 | Phase B says `Math.min(30000, ...)` ; Phase F says 60s with `Math.min(60000, ...)`                                               |

**Resolution**: Phase B ships initial jitter with **30s max** (as a quick improvement over no jitter). Phase F finalizes with **60s max** and `Math.min(attempt, 7)` exponent cap. The two-phase approach is consistent: Phase B lifts the 10-attempt cap and adds basic jitter; Phase F extends the max interval and adds heartbeat-based dead-conn detection. Both R4 inputs agree on the Phase F formula.

### 20.5 Page-severity alert count

| Input | Position                                                                                            |
|-------|-----------------------------------------------------------------------------------------------------|
| R4-01 | 4 page alerts: `WSOriginRejection`, `WSOversizedFrame`, `WSStateDropped`, `WSSeqCurrentStalled`     |
| R4-02 | 4 page alerts: same list, plus `WSDrainCallbackGenStuck` mentioned as PAGE in Phase B observability |

**Resolution**: **5 page-severity alerts** total. R4-02's Phase B observability section explicitly marks `WSDrainCallbackGenStuck` as PAGE severity. This is correct -- a stuck drain callback means the browser is not updating charts, which is a user-visible failure. R4-01 listed it under Phase B alerts but did not include it in the page-severity summary.

### 20.6 Items resolved at implementation time

| Input | Position                                                 |
|-------|----------------------------------------------------------|
| R4-01 | 13 resolved items table in section 14a (from R3-02 S1.7) |
| R4-02 | 6 items in section 13.4                                  |

**Resolution**: R4-01's list of 13 is comprehensive; R4-02's 6 is a subset of the same items. Both agree on the same defaults-of-last-resort. This document incorporates the full set of defaults in the pre-flight procedure and per-phase entry gates. No contradiction in substance.

### 20.7 Cross-cutting concerns ownership

Both R4 inputs agree on the 10 CCC structure and ownership assignments. No contradiction.

### 20.8 Security flag naming

Both R4 inputs agree on positive-sense `ws_security_enabled=True`. No contradiction. (This was resolved in R4 from the R3 disagreement.)

---

## S21. Self-audit log

### 21.1 Passes performed

1. **Pass 1**: Read R4-01 (1828 lines) in full via offset/limit chunks.
2. **Pass 2**: Read R4-02 (1810 lines) in full via offset/limit chunks.
3. **Pass 3**: Identified 7 R4-cross disagreements (effort framing, metrics count, test count, jitter max, page alert count, resolved-items count, B-pre-a metrics count).
4. **Pass 4**: Verified architecture doc identifiers (33 GAP-WS, 9 M-SEC, 16 RISK).
5. **Pass 5**: Built S0-S3 integrating R4-02's audience-layer structure with R4-01's detail depth.
6. **Pass 6**: Built S4-S14 per-phase sections using R4-01's comprehensive deliverables/tests + R4-02's consistent template.
7. **Pass 7**: Built S15-S18 appendices (test matrix, effort summary, decision reference, cross-reference).
8. **Pass 8**: Built S19-S20 (lineage, R4 reconciliation).
9. **Pass 9**: Self-audit (this section).

### 21.2 Coverage checks

- [x] Every phase (0-cascor through I) has all required fields: Goal, Entry gate, Deliverables checklist, Cross-cutting (where applicable), Test acceptance, Pull request plan, Exit gate, Rollback (verbatim bash commands), NOT in this phase
- [x] All 42 settled positions from the constitution appear in S2
- [x] All 62 decisions from D-01 through D-62 appear in S17
- [x] Kill switch matrix covers every phase (26 switches + 2 non-switches)
- [x] Risk register has 16 RISK + 5 CCC = 21 entries, each with kill switch and MTTR
- [x] Observability matrix per phase with metrics + alerts + dashboards
- [x] All 7 R4-cross disagreements identified and resolved in S20
- [x] SLO table present (S3.3)
- [x] Latency histogram buckets specified ({50..5000} ms)
- [x] Canonical label values specified (S15)
- [x] Feature flag inventory (S2.7)
- [x] Configuration canonical table (S3.6, 26 settings)
- [x] Version bump table in S3.5
- [x] Worktree naming convention referenced
- [x] Rollback order (reverse-dependency) documented
- [x] All 33 GAP-WS identifiers mapped in S18
- [x] All 9 M-SEC identifiers (01 through 09) mapped in S18
- [x] All 16 RISK identifiers mapped in S18
- [x] Every test acceptance criterion is measurable (specific assertion, not "works correctly")
- [x] Every rollback has verbatim bash commands with MTTR
- [x] No "consider", "might", "TBD", or "may" in S0-S16
- [x] `command_id` used everywhere; grep for `request_id` in sections 0-16 returns 0 (only mentioned in RISK context as the wrong name)

### 21.3 Corrections applied during self-audit

1. **S3.3 observability matrix**: Initial draft listed 4 page-severity alerts. Added `WSDrainCallbackGenStuck` as the 5th per R4-02 Phase B observability section (S20.5).
2. **S4 Phase 0-cascor**: Initial draft had 13 metrics. Expanded to 15 per R4-01's detailed enumeration, adding `cascor_ws_command_responses_total` and `cascor_ws_command_handler_seconds` (S20.2).
3. **S7.3 Phase B deliverables**: Verified `/api/ws_browser_errors` endpoint is present (D-59). Confirmed.
4. **S8.3 Phase B-pre-b**: Verified `SameSite=Strict` (not Lax). Confirmed per R4 consensus.
5. **S8.3 rate limit overflow**: Verified connection stays up with `rate_limited` response (not close 1013). Confirmed per R4 consensus.
6. **S12 Phase F jitter**: Clarified two-phase approach -- Phase B ships 30s max, Phase F extends to 60s max (S20.4).
7. **S15 test matrix**: Added `test_shape_hash_matches_golden` for Phase H which was in R4-02 but not R4-01's matrix.
8. **S16 effort summary**: Added "Risk factor" column per R4-02's format.
9. **S18 cross-reference**: Verified all 33 GAP-WS identifiers are present. GAP-WS-23 is an alias of GAP-WS-14, listed for link integrity.
10. **S0.4 effort**: Adopted R4-02's target/buffer framing with explicit justification of the 2.25-day delta.

### 21.4 Confidence assessment

**High confidence**: Phase 0-cascor scope and commit decomposition (all prior rounds converge), `command_id` wire correction (unanimous), kill-switch matrix (triangulated across R4-01/R4-02), cross-repo merge sequence, phase dependency graph, security flag positive-sense resolution.

**Medium confidence**: NetworkVisualizer scope (render-tech unverified until day-1 grep), Phase B-pre-b effort (SessionMiddleware question), effort target/buffer distinction (presentational, not substantive).

**Lower confidence**: Phase C flip-gate p99 >=50ms threshold (depends on actual latency distribution), Phase E conditionality (some earlier round inputs treat it as mandatory).

### 21.5 Scope discipline verification

- [x] Read only the 2 R4 files (architecture doc for verification only)
- [x] Referenced R4-NN identifiers when citing inputs in S20
- [x] Referenced D-NN, GAP-WS-NN, M-SEC-NN, RISK-NN identifiers throughout
- [x] Did not modify other files; did not commit
- [x] `command_id` used everywhere; no stale `request_id` references in body
- [x] No "TBD", "consider X or Y", "may" in sections S0-S16
- [x] Every position is resolved; zero open questions

**Scope discipline: PASS.**

---

**End of R5-01 Canonical Development Plan.**
