# Round 3 Proposal R3-03: Lean Execution Document

**Angle**: Tight, table-heavy, checklist-driven execution document
**Author**: Round 3 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 3 consolidation — input to Round 4
**Inputs consolidated**: R2-01..R2-04 (lean reformat)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE

---

## 0. First hour

If you are picking up this work right now, do exactly this sequence before writing code:

1. `cd /home/pcalnon/Development/python/Juniper` — confirm ecosystem working tree is clean across all repos (`for repo in juniper-cascor juniper-cascor-client juniper-canopy; do (cd $repo && git status); done`).
2. Read §1 (constitution) and §2 (phase index) of this doc. Do not re-read R2-NN sources unless you hit a disagreement with this doc.
3. Run the five day-1 verification greps from §17.1 and record results in your worktree README:
   - `grep -rn "SessionMiddleware" juniper-canopy/src/` (blocks Phase B-pre-b budget — R1-05 §5.2)
   - `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py` (blocks Phase B NetworkVisualizer scope — R1-05 §5.1)
   - `grep "dash\b" juniper-canopy/pyproject.toml` (Dash version floor — R1-05 §5.3)
   - `grep -n "run_coroutine_threadsafe" juniper-canopy/src/backend/cascor_service_adapter.py` (Phase C supervisor — R1-05 §5.5)
   - `grep -n "command_id\|request_id" juniper-cascor/src/api/websocket/control_stream.py` (Phase G scope — R1-05 §5.6)
4. Verify GAP-WS-19 is already RESOLVED on cascor main: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` should show the lock-holding pattern matching R0-03 §11.1 (R1-05 §4.16). If the pattern is missing, STOP — something has regressed and Phase 0-cascor scope expands.
5. Measure pre-Phase-B baseline bandwidth in staging: 1-hour sample of `/api/metrics/history` bytes/s. Record as `canopy_rest_polling_bytes_per_sec` pre-migration baseline (D-62 new). This is the reference for Phase B's P0 exit gate (>90% reduction).
6. Confirm cross-repo worktree naming/location per Juniper parent CLAUDE.md; create worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/` only.
7. Open Phase 0-cascor and Phase A-SDK worktrees in parallel — these can run simultaneously (no dependency between cascor-server and SDK until Phase G).
8. Pick the first PR target from §14 merge sequence: **PR-1 = `phase-a-sdk-set-params` on juniper-cascor-client**.

---

## 1. Settled positions (constitution)

Single tabular page. Every item here is SETTLED — do not re-litigate. Source pointers are canonical.

| # | Position | Source | One-line rationale |
|---|---|---|---|
| C-01 | Correlation field is `command_id`, NOT `request_id` — every repo, every test | R1-05 §4.2; R2-03 §15.2; R2-04 D-02 | Source doc §7.32 + 2/3 R0s agree; rename mandate |
| C-02 | `command_response` has NO `seq` field; `/ws/control` has no replay buffer | R1-05 §4.17; R2-01 §3.1; R2-04 D-03 | Separate seq namespaces per endpoint |
| C-03 | `set_params` default timeout = 1.0 s (not 5.0 s) | R1-05 §4.1; R2-04 D-01 | Source doc §7.32 specific beats §7.1 generic |
| C-04 | SDK fails fast on disconnect; no reconnect queue; no SDK-level retries | R1-05 §4.22, §4.42; R2-02 §4.7 | Caller decides fallback |
| C-05 | Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE` | R1-05 §6.1; R2-01 §18.1; R2-04 D-35 | Prod default; staging can lower to exercise fallback |
| C-06 | `server_instance_id` = programmatic key; `server_start_time` = advisory only | R1-05 §4.20; R2-03 §3.3 | Clock-skew bug if comparing start_time |
| C-07 | `replay_buffer_capacity` added to `connection_established` | R1-05 §4.21; R2-04 D-16 | Additive; lets client tune |
| C-08 | Two-phase registration via `_pending_connections` set | R1-05 §4.18; R2-04 D-14 | Over per-connection `seq_cursor` |
| C-09 | Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with WARN | R1-05 §4.44; R2-02 §8.3 | Defense in depth at two layers |
| C-10 | Adapter→cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header) | R1-05 §4.43; R2-01 §7.1; R2-04 D-29 | Uniform handler path; brittle-invariant avoidance |
| C-11 | GAP-WS-19 `close_all` lock is RESOLVED on main; add `test_close_all_holds_lock` regression only | R1-05 §4.16; R2-02 §3.3 | Verified at `manager.py:138-156` |
| C-12 | Phase 0-cascor is a carve-out from Phase B (was "Phase A-server") | R1-05 §4.19; R2-04 D-11 | Dodges "Phase A SDK" collision |
| C-13 | Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D) | R1-05 §4.35; R2-04 D-23 | Phase B ships without CSRF plumbing |
| C-14 | Phase B ships behind two flags: `enable_browser_ws_bridge` (False→True post-soak) + `disable_ws_bridge` (permanent kill) | R1-05 §4.45; R2-04 D-17, D-18 | Dev flip vs permanent kill are distinct |
| C-15 | Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`) | R1-05 §4.36; R2-04 D-19 | RISK-04 mitigation |
| C-16 | rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`) | R1-05 §4.3; R2-04 D-04 | Enable only if §5.6 data warrants |
| C-17 | REST fallback cadence during disconnect = 1 Hz (NOT 100 ms) | R1-05 §4.4; R2-04 D-05 | Avoids reintroducing polling bomb |
| C-18 | `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array) | R1-05 §4.7; R2-04 D-07 | Dash equality false-negative guard |
| C-19 | Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces | R1-02 §5.4; R2-01 §6.1 | Independent of drain rate |
| C-20 | GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in Phase B | R1-05 §4.8; R2-02 §6.3 | Clean ownership |
| C-21 | NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape | R1-05 §4.5; R2-04 D-06 | First Phase B commit verifies render tech |
| C-22 | `_normalize_metric` dual-format contract (flat + nested) preserved forever; CODEOWNERS hard gate in Phase H | R1-05 §4.41; R2-04 D-27 | RISK-01 |
| C-23 | REST endpoints (`/api/metrics/history`, `/api/train/*`, `/api/v1/training/params`, `/api/topology`) preserved FOREVER — no deprecation | R1-05 §4.23; R1-02 principle 7; R2-04 D-21, D-54 | Kill switch fallback |
| C-24 | Single-tenant v1; multi-tenant replay isolation deferred | R1-05 §4.13; R2-04 D-25, D-32 | YAGNI |
| C-25 | One-resume-per-connection rule (second resume → close 1003) | R1-05 §4.12; R2-02 §3.3 | DoS amplification mitigation |
| C-26 | Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s | R1-05 §4.37, §4.46; R2-04 D-24, D-33 | Configurable |
| C-27 | `ws_security_enabled=True` (positive sense), NOT `disable_ws_auth` | R1-02 §12.5; R2-01 §18.2; R2-03 §15.3; R2-04 D-10 | Negative-sense footgun |
| C-28 | Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates | R1-02 §6.1; R2-04 D-47, D-48 | Evidence-based rollout |
| C-29 | Debounce lives in Dash clientside callback (NOT SDK) | R1-05 §4.24; R2-04 D-22 | Architectural placement |
| C-30 | `JUNIPER_WS_ALLOWED_ORIGINS='*'` is explicitly REFUSED by the parser (non-switch, not a kill switch) | R1-02 §4.3; R2-03 §5.3 | Panic-edit prevention |
| C-31 | Shadow traffic: rejected | R1-05 §4.39; R2-04 D-26 | — |
| C-32 | Chromium-only Playwright for v1 | R1-05 §4.31; R2-04 D-44 | — |
| C-33 | Per-command HMAC deferred indefinitely | R1-05 §4.11; R2-04 D-31 | Speculative threat |
| C-34 | Contract-test pytest marker `contract` runs on every PR (NOT nightly) in all 3 repos | R1-05 §4.34; R2-03 §7.3 | Schema drift is silent |
| C-35 | Latency tests are recording-only in CI (`latency_recording` marker); strict assertions local-only | R1-05 §4.28; R2-04 D-42 | CI variance flakiness |
| C-36 | Total effort: 13.5 expected engineering days / ~4.5 weeks calendar (optimistic 10.6 / pessimistic 19-22) | R1-05 §4.40; R2-02 §17; R2-04 §1.3 | — |
| C-37 | P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90% vs baseline | R1-01 §2.5.1; R1-02 §2.2; R2-02 §6.5 | Phase B gate |
| C-38 | Observability-before-behavior rule: metrics + panels + alerts must land BEFORE the behavior change that depends on them | R1-02 §1.2 principle 1; R2-03 §4.3 | Hard gate per phase |
| C-39 | Kill switch MTTR ≤5 min, CI-tested, staging-drilled; untested switch is not a switch | R1-02 §1.2 principle 2, §13.7; R2-03 §5.3 | Every phase |
| C-40 | Wire-format rollout is strictly additive; no field renamed/retyped/removed in this migration | R2-03 §3.3 | No schema version discriminator needed |
| C-41 | `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope (§5.6 latency pipe) | R1-05 §4.8; R2-02 §3.3; R2-03 §12.3 | Ships in Phase 0-cascor |
| C-42 | Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-reliability work) | R1-02 §2.4; R2-04 D-50 | — |

---

## 2. Phase index

Owner key: **C**=backend-cascor, **Y**=backend-canopy, **F**=frontend, **S**=SDK, **Sec**=security review, **O**=ops.

Effort triple = optimistic / expected / pessimistic (eng-days).

| # | Phase | Goal (one line) | Owner | Effort | Entry deps | Exit top criterion | Rollback TTF | NOT-in-phase |
|---|---|---|---|---|---|---|---|---|
| 1 | **0-cascor** (was Phase A-server) | Cascor `/ws/training` emits monotonic `seq`, advertises `server_instance_id`+`replay_buffer_capacity`, supports `resume`, fixes state coalescer | C | 1.5/2.0/3.0 | cascor main clean; GAP-WS-19 verified | `cascor_ws_seq_gap_detected_total==0` after 72h soak | 15 min revert | Full Phase E; permessage-deflate; topology chunking; seq on `command_response` |
| 2 | **A-SDK** (parallel with 1) | `CascorControlStream.set_params(params, timeout=1.0, command_id=...)` ships to PyPI | S | 0.5/1.0/1.5 | cascor-client main clean | `test_set_params_caller_cancellation` green | PyPI yank or pin downgrade | Canopy adapter refactor; SDK retries; debounce |
| 3 | **B-pre-a** (read-path sec; parallel with 1,2) | Origin on `/ws/training`, size caps (M-SEC-03), per-IP cap (M-SEC-04 min), idle timeout (M-SEC-10), audit-logger skeleton | C+Y+Sec | 0.5/1.0/1.5 | cascor+canopy main clean | 6th-IP conn rejected 1013; 65KB frame 1009; empty allowlist rejects all | 5 min env flag revert | CSRF; Origin on `/ws/control`; rate limit; Prom counters for audit; adapter HMAC |
| 4 | **B** (read-path wiring + polling kill — P0) | Browser bridge drains `/ws/training` into Dash store, `Plotly.extendTraces` updates, polling killed; GAP-WS-24a/b latency pipe; Phase I cache bust bundled | Y+F+C | 3.0/4.0/5.0 | Phase 0-cascor + B-pre-a in prod; 72h 0-cascor soak | `canopy_rest_polling_bytes_per_sec` ≥90% reduced for 1h in staging + 72h memory soak | 5 min `disable_ws_bridge=true` | Phase C `set_params`; Phase D buttons; full rAF; full backpressure; CSRF flow |
| 5 | **B-pre-b** (control-path sec; parallel with 4) | Origin on `/ws/control`, cookie session + CSRF first-frame, rate limit, idle timeout enforcement, adapter HMAC, audit Prom counters, M-SEC-11 adapter validation | Y+Sec | 1.0/1.5/2.0 | B-pre-a in main; Phase B in main (optional for C, mandatory for D) | All 12 tests green; 48h staging soak; kill-switch drill; Origin+CSRF enforced end-to-end | 5 min env flag revert | Per-command HMAC; multi-tenant isolation; two-bucket rate limit |
| 6 | **C** (set_params adapter, flag-off) | Canopy adapter hot/cold split; hot→WS via `command_id`; unconditional REST fallback; flag-off default | Y | 1.5/2.0/3.0 | A-SDK on PyPI; Phase B in prod; `ws_set_params_timeout` setting | `test_set_params_concurrent_correlation` green; flag-off by default | 2 min `use_websocket_set_params=false` | SDK retries; reconnect queue; REST deprecation; frontend buttons |
| 7 | **D** (control buttons via WS) | Browser start/stop/pause/resume/reset routed via `/ws/control` with REST fallback; per-command timeouts (`start: 10s`, others: 2s) | F+Y+C | 0.75/1.0/1.5 | Phase B in prod + **B-pre-b in prod ≥48h** | `test_csrf_required_for_websocket_start` green; 24h zero orphaned commands | 5 min `enable_ws_control_buttons=false` | Full `permessage-deflate`; set_params routing (that's C) |
| 8 | **E** (full backpressure; conditional) | Per-client pump tasks + bounded queues + policy matrix; default `drop_oldest_progress_only` | C | 0.75/1.0/1.5 | Phase 0-cascor in main; trigger = RISK-04 observed | `test_slow_client_does_not_block_fast_clients` green | 5 min `ws_backpressure_policy=block` | Multi-tenant per-session queues; permessage-deflate |
| 9 | **F** (heartbeat + reconnect jitter) | Application `ping`/`pong` at 30s; 10s dead-conn threshold; uncap reconnect; jitter formula | F+C | 0.25/0.5/1.0 | Phase B in main (jitter already landed) | All 4 tests pass; no NaN delays after 48h | 10 min JS asset revert | Custom ping schedules; per-endpoint intervals |
| 10 | **G** (cascor `set_params` integration tests) | 13 tests via FastAPI `TestClient.websocket_connect()`; contract-lane tests | C | 0.25/0.5/0.75 | Phase 0-cascor in main; B-pre-b in main | All 13 tests green in `contract` lane | n/a (test-only) | SDK-level integration tests |
| 11 | **H** (normalize_metric audit + regression gate) | Regression test + consumer audit doc + CODEOWNERS hard gate + pre-commit hook | Y | 0.5/1.0/1.5 | Phase B in main (MVS-TEST-14 already landed) | Regression tests green; CODEOWNERS enforced; audit merged | 5 min git revert | `_normalize_metric` refactor (new phase required); removal of format |
| 12 | **I** (asset cache busting) | Bumps `assets_url_path` / hash query param so browsers pick up new JS | F | 0.1/0.25/0.5 | folds into Phase B | Browsers pick up new JS without hard refresh | 5 min revert cache-bust config | — |
| — | **Total (with parallelism)** | — | — | **10.6 / 13.5 / 19.0** | — | — | — | — |

---

## 3. Phase 0-cascor (compact)

### 3.1 Deliverables checklist

**Commits** (R2-01 §3.1 / R2-02 §3.3):
- [ ] 0-cascor-1: `messages.py` optional `seq` + `emitted_at_monotonic` field on every builder
- [ ] 0-cascor-2: `manager.py` gains `server_instance_id=uuid4()`, `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer=deque(maxlen=Settings.ws_replay_buffer_size)`, `_assign_seq_and_append()`; `connect()` advertises `server_instance_id`, `server_start_time`, `replay_buffer_capacity` on `connection_established`
- [ ] 0-cascor-3: `_send_json` wraps in `asyncio.wait_for(..., timeout=Settings.ws_send_timeout_seconds)` (GAP-WS-07 quick-fix, default 0.5s)
- [ ] 0-cascor-4: `replay_since(last_seq)` + `ReplayOutOfRange` exception; copy-under-lock pattern
- [ ] 0-cascor-5: `training_stream.py` two-phase registration (`_pending_connections`, `promote_to_active()`); `resume`/`resume_ok`/`resume_failed` handler with 5s frame timeout; one-resume-per-connection rule (R1-05 §4.12, C-25)
- [ ] 0-cascor-6: `/api/v1/training/status` returns `snapshot_seq` + `server_instance_id` atomically under `_seq_lock`
- [ ] 0-cascor-7: `lifecycle/manager.py:133-136` — replace drop-filter with debounced coalescer; terminal transitions (Completed/Failed/Stopped) bypass throttle (GAP-WS-21)
- [ ] 0-cascor-8: `broadcast_from_thread` adds `Task.add_done_callback(_log_exception)` (GAP-WS-29)
- [ ] 0-cascor-9: `/ws/control` handler returns protocol-error envelopes for unknown commands (close 1003 on non-JSON); echoes `command_id` if present; **NO seq on command_response** (C-02; GAP-WS-22)
- [ ] 0-cascor-10: CHANGELOG.md + `docs/websocket_protocol.md` — additive field contract section

**Settings** (`juniper-cascor/src/config/settings.py`):
- [ ] `ws_replay_buffer_size: int = 1024`
- [ ] `ws_send_timeout_seconds: float = 0.5`
- [ ] `ws_resume_handshake_timeout_s: float = 5.0`
- [ ] `ws_state_throttle_coalesce_ms: int = 1000`
- [ ] `ws_pending_max_duration_s: float = 10.0`

**Tests** (R2-01 §3.3, 20 items):
- [ ] `test_seq_monotonically_increases_per_connection` (R1-05 §4.17 rename)
- [ ] `test_seq_is_assigned_on_loop_thread`
- [ ] `test_seq_lock_does_not_block_broadcast_iteration`
- [ ] `test_replay_buffer_bounded_to_configured_capacity`
- [ ] `test_replay_buffer_capacity_configurable_via_env`
- [ ] `test_replay_since_happy_path` / `out_of_range` / `empty` / `oldest_minus_one`
- [ ] `test_send_json_0_5s_timeout`
- [ ] `test_state_coalescer_preserves_terminal_transitions` (200ms Started→Failed)
- [ ] `test_broadcast_from_thread_exception_logged_not_leaked`
- [ ] `test_connection_established_advertises_server_instance_id_and_replay_buffer_capacity`
- [ ] `test_snapshot_seq_atomic_with_state_read`
- [ ] `test_ws_control_command_response_has_no_seq` (C-02 contract)
- [ ] `test_close_all_holds_lock` (C-11 regression gate)
- [ ] `test_pending_connections_not_eligible_for_broadcast`
- [ ] `test_promote_to_active_atomic_under_seq_lock`
- [ ] `test_second_resume_closes_connection_1003` (C-25)
- [ ] `test_unknown_command_returns_protocol_error_envelope`
- [ ] `test_malformed_json_closes_1003`

**Chaos tests (BLOCKING gates, not nightly per R2-01 §18.9)**:
- [ ] `chaos_broadcast_replay_race` (hypothesis + asyncio.gather 100 concurrent)
- [ ] `chaos_broadcast_fanout` (100 Hz × 60s × 10 clients — load test blocking gate per R1-02 §10.3)
- [ ] `chaos_broadcast_from_thread_exception` (hypothesis exception types)

**Integration tests**:
- [ ] `test_resume_happy_path_via_test_client`
- [ ] `test_resume_failed_server_restarted` (stale UUID)
- [ ] `test_resume_failed_out_of_range` (broadcast 2000, reconnect last_seq=10)
- [ ] `test_resume_malformed_data`
- [ ] `test_resume_timeout_no_frame`

**Observability** (all must be present before merge — metric-before-behavior):
- [ ] `cascor_ws_seq_current` (Gauge)
- [ ] `cascor_ws_replay_buffer_occupancy` / `_bytes` / `_capacity_configured` (Gauge × 3)
- [ ] `cascor_ws_resume_requests_total{outcome}` (Counter)
- [ ] `cascor_ws_resume_replayed_events` (Histogram, buckets `{0,1,5,25,100,500,1024}`)
- [ ] `cascor_ws_broadcast_timeout_total{type}` (Counter)
- [ ] `cascor_ws_broadcast_send_seconds{type}` (Histogram)
- [ ] `cascor_ws_pending_connections` (Gauge)
- [ ] `cascor_ws_state_throttle_coalesced_total` (Counter)
- [ ] `cascor_ws_broadcast_from_thread_errors_total` (Counter; must be 0 steady state)
- [ ] `cascor_ws_connections_active{endpoint}` (Gauge)
- [ ] `cascor_ws_command_responses_total{command, status}` (Counter)
- [ ] `cascor_ws_command_handler_seconds{command}` (Histogram)
- [ ] `cascor_ws_seq_gap_detected_total` (Counter — MUST be 0; alert otherwise)

**Alerts**:
- [ ] `WSSeqCurrentStalled` (PAGE): `changes(cascor_ws_seq_current[5m])==0 AND connections>0`
- [ ] `WSResumeBufferNearCap` (ticket): `occupancy > 0.8*capacity for 30s`
- [ ] `WSPendingConnectionStuck` (ticket): `pending > 0 for 30s`
- [ ] `WSSlowBroadcastP95` (ticket): `histogram_quantile(0.95) > 500ms`

### 3.2 Exit gate

- [ ] All 20 unit + 5 integration + 3 chaos + load tests green
- [ ] Metric-presence pytest green (R1-02 §10.6)
- [ ] **72-hour staging soak** (R2-01 §3.5; R1-02 §3.4 amplification): `cascor_ws_broadcast_from_thread_errors_total==0`, replay-buffer occupancy distribution stable, `seq_current` monotonic across all hours, `cascor_ws_broadcast_timeout_total` rate < 0.1/s
- [ ] `WSSeqCurrentStalled` alert test-fired once in staging (rule + routing verified)
- [ ] Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published
- [ ] `juniper-cascor-worker` CI green against new cascor during soak (backward-compat validation per CCC-08)

### 3.3 Rollback (verbatim commands)

```bash
# Hot rollback — full revert (15 min TTF)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git revert <phase-0-cascor-merge-sha> --no-edit
git push origin main
# Blue/green redeploy cascor; clients see new server_instance_id, refetch REST snapshot

# Soft rollback — aggressive send-timeout override (5 min TTF)
export JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01
systemctl restart juniper-cascor

# Replay buffer disable (5 min TTF)
export JUNIPER_WS_REPLAY_BUFFER_SIZE=0
systemctl restart juniper-cascor
```

---

## 4. Phase A-SDK (compact)

### 4.1 Deliverables checklist

**Code** (`juniper-cascor-client/juniper_cascor_client/control_stream.py`):
- [ ] `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None) -> dict`
- [ ] `self._pending: Dict[str, asyncio.Future]` correlation map, bounded at 256 (R1-02 §6.4) with `JuniperCascorOverloadError` on overflow
- [ ] Background `_recv_task` started on connect; parses inbound, pops future by `command_id`, `set_result(envelope)`
- [ ] `disconnect()` cancels recv task, drains pending with `set_exception(JuniperCascorConnectionError("disconnected"))`
- [ ] Caller-cancellation cleans correlation map entry in `finally`
- [ ] Fail-fast: no SDK retries on timeout (C-04)
- [ ] `_client_latency_ms` private field on returned dict
- [ ] `SetParamsResponse` wire model with `extra="allow"`
- [ ] `testing/fake_ws_client.py`: `on_command(name, handler)` auto-scaffold `command_response` reply

**Tests** (R2-02 §4.3):
- [ ] `test_set_params_default_timeout_is_one_second` (C-03 regression)
- [ ] `test_set_params_happy_path` (50ms ack latency)
- [ ] `test_set_params_timeout_raises_typed_exception`
- [ ] `test_set_params_concurrent_callers_correlate_via_command_id` (C-01)
- [ ] `test_set_params_caller_cancellation_cleans_correlation_map` (**MANDATORY gate** — R1-05 §4.25)
- [ ] `test_set_params_fails_fast_on_disconnect` (C-04)
- [ ] `test_set_params_no_retry_on_timeout`
- [ ] `test_set_params_server_error_response_raises_typed_exception`
- [ ] `test_correlation_map_bounded_at_256`
- [ ] `test_recv_task_propagates_exception_to_all_pending_futures`
- [ ] `test_len_pending_returns_to_zero_after_failure_modes` (R1-02 §9.2 nightly gate)
- [ ] `test_set_params_x_api_key_header_present` (R0-02 IMPL-SEC-44)

**Release**:
- [ ] `pyproject.toml` minor bump (new public method per semver)
- [ ] `CHANGELOG.md` entry
- [ ] PyPI publish; record `SDK_VERSION_A` for Phase C pin bump
- [ ] `juniper-ml/pyproject.toml` extras pin bump (follow-up one-line PR)

### 4.2 Exit gate

- [ ] 12 unit tests green
- [ ] Coverage ≥95% on new code
- [ ] `test_set_params_caller_cancellation_cleans_correlation_map` non-flaky across 10 CI runs
- [ ] `pip install juniper-cascor-client==<new>` succeeds in fresh venv
- [ ] Ruff/black/isort gates pass
- [ ] Canopy adapter draft PR can `import` and call `set_params` against `FakeCascorServerHarness`

### 4.3 Rollback

```bash
# PyPI yank (2 min TTF) — only if "installs but will not import"
# Yank via PyPI web UI: project → release → Options → Yank
# Otherwise fix-forward with a patch release

# Downstream pin downgrade (15 min TTF)
cd juniper-canopy
# Edit pyproject.toml: juniper-cascor-client = "<SDK_VERSION_A"
git commit -am "chore: pin cascor-client to pre-<version>"
# Redeploy
```

No runtime flag exists; Phase C flag-off means the new SDK method is dead code in prod until Phase C flips.

---

## 5. Phase B-pre-a (compact)

### 5.1 Deliverables checklist

**Cascor side**:
- [ ] `src/api/websocket/origin.py` (new): `validate_origin(ws, allowlist) -> bool` (case-insensitive host, port significant, null rejected, `*` unsupported, empty=reject-all)
- [ ] `src/api/app.py`: wire into `training_stream_handler` (NOT `control_stream_handler` yet)
- [ ] `src/config/settings.py`: `ws_allowed_origins: list[str] = []` + env var (fail-closed default)
- [ ] `src/api/websocket/manager.py`: `_per_ip_counts: Dict[str,int]` under `_lock`; increment in `connect()`, decrement in `disconnect()` finally; purge empty entries
- [ ] `src/config/settings.py`: `ws_max_connections_per_ip: int = 5`
- [ ] `src/api/websocket/training_stream.py`: `max_size=4096` on every `receive_*()`
- [ ] `src/api/websocket/manager.py`: idle timeout `asyncio.wait_for(receive_text(), timeout=ws_idle_timeout_seconds)`, close 1000 on TimeoutError
- [ ] `src/config/settings.py`: `ws_idle_timeout_seconds: int = 120`

**Canopy side**:
- [ ] `src/backend/ws_security.py` (new): copy of cascor `validate_origin` (duplicate, do NOT cross-import)
- [ ] `src/main.py`: wire `validate_origin` into `/ws/training` route (NOT `/ws/control`)
- [ ] `src/config/settings.py`: `allowed_origins` with localhost/127.0.0.1 × http/https defaults
- [ ] `src/main.py`: `max_size=4096` on `/ws/training` inbound, `max_size=65536` on `/ws/control` inbound
- [ ] `src/backend/audit_log.py` (new): `canopy.audit` logger, JSON formatter, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist from `SetParamsRequest.model_fields`, CRLF escape
- [ ] `src/config/settings.py`: `audit_log_enabled: bool = True`, `audit_log_path`, `audit_log_retention_days`
- [ ] CI `scripts/audit_ws_receive_calls.py` (new): AST check every `ws.receive_*()` has explicit `max_size`

**Tests** (R2-02 §5.3):
- [ ] `test_oversized_frame_rejected_with_1009` (both cascor + canopy)
- [ ] `test_per_ip_cap_enforced_6th_rejected_1013`
- [ ] `test_per_ip_counter_decrements_on_disconnect` / `on_exception`
- [ ] `test_per_ip_map_shrinks_to_zero` (memory-leak guard)
- [ ] `test_per_ip_counter_increment_decrement_race`
- [ ] `test_origin_allowlist_accepts_configured_origin`
- [ ] `test_origin_allowlist_rejects_third_party` / `rejects_missing_origin` / `case_insensitive_host` / `rejects_trailing_slash`
- [ ] `test_empty_allowlist_rejects_all_fail_closed`
- [ ] `test_idle_timeout_closes_1000`
- [ ] `test_audit_log_format_and_scrubbing`
- [ ] `test_audit_log_rotates_daily` (mocked time)

**Integration**:
- [ ] `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` (Playwright cross-origin probe)

**Observability**:
- [ ] `cascor_ws_oversized_frame_total{endpoint,type}`
- [ ] `cascor_ws_per_ip_rejected_total`
- [ ] `canopy_ws_oversized_frame_total{endpoint}`
- [ ] `canopy_ws_per_ip_rejected_total`
- [ ] `canopy_ws_origin_rejected_total{origin_hash, endpoint}` (SHA-256 prefix 8 chars)
- [ ] `canopy_audit_events_total{event_type}` (counter only; Prom hookup moved to Phase B per C-C2)

**Alerts**:
- [ ] `WSOriginRejection` (PAGE per R1-02 §2.4): any `increase(canopy_ws_origin_rejected_total[5m]) > 0` from unknown origin_hash
- [ ] `WSOversizedFrame` (ticket): `increase[5m] > 0`

### 5.2 Exit gate

- [ ] All unit + CSWSH Playwright tests green
- [ ] CI `audit_ws_receive_calls.py` passes (no unguarded `receive_*`)
- [ ] `WSOriginRejection` alert rule test-fired once in staging
- [ ] Runbook `juniper-canopy/notes/runbooks/ws-cswsh-detection.md` published
- [ ] Runbook `juniper-canopy/notes/runbooks/ws-audit-log-troubleshooting.md` published
- [ ] 24-hour staging soak with no user lockout

### 5.3 Rollback

```bash
# Per-IP cap neutralize (5 min TTF)
export JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999
systemctl restart juniper-cascor juniper-canopy

# Broaden allowlist (5 min TTF) — but '*' is REFUSED by parser (C-30)
export JUNIPER_WS_ALLOWED_ORIGINS='http://extra-origin:8050,http://localhost:8050'

# Idle timeout disable
export JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0

# Audit log disable (disk-full emergency)
export JUNIPER_AUDIT_LOG_ENABLED=false

# Full revert
git revert <phase-b-pre-a-canopy-merge> <phase-b-pre-a-cascor-merge>  # reverse order
```

---

## 6. Phase B (compact)

### 6.1 Deliverables checklist

**Frontend JS** (`juniper-canopy/src/frontend/assets/`):
- [ ] `ws_dash_bridge.js` (new, ~200 LOC): `window._juniperWsDrain` namespace; 5 `on(type, ...)` handlers; per-handler bounded ring buffers `MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`; drain methods; `peekStatus()`; **ring bound enforced in handler** (C-19)
- [ ] `websocket_client.js` cleanup:
  - [ ] `onStatus()` enrichment (connected/reason/reconnectAttempt/ts)
  - [ ] Jitter: `delay = Math.random() * Math.min(30000, 500 * 2**attempt)` (GAP-WS-30)
  - [ ] **Remove 10-attempt cap** (GAP-WS-31); max 30s interval forever (R2-01 §18.4)
  - [ ] Capture `server_instance_id` from `connection_established`
  - [ ] `seq` tracking (monotonic check + WARN on gap)
  - [ ] `resume` frame on reconnect with graceful-degrade to REST snapshot on `resume_failed`
- [ ] Delete parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490-1526` (GAP-WS-03) + cite comment
- [ ] `ws_latency.js` (new, ~50-100 LOC): records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60s (GAP-WS-24a)
- [ ] rAF scaffold `_scheduleRaf = noop` (C-16)

**Python frontend/backend** (`juniper-canopy/src/frontend/`, `src/main.py`):
- [ ] `dashboard_manager.py` `ws-metrics-buffer` drain callback → structured `{events, gen, last_drain_ms}` (C-18)
- [ ] Update existing `ws-topology-buffer` + `ws-state-buffer` drain callbacks to read from `window._juniperWsDrain`; delete `window._juniper_ws_*` globals
- [ ] Add `ws-cascade-add-buffer` + `ws-candidate-progress-buffer` stores + drains
- [ ] `ws-connection-status` store with drain callback; emits only on change
- [ ] Refactor `_update_metrics_store_handler` (dashboard_manager.py:2388-2421): return `no_update` when `ws-connection-status.connected===true`; slow fallback to 1 Hz via `n % 10 != 0` (C-17)
- [ ] Apply same polling-toggle to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`; **keep REST paths — they are the kill switch**
- [ ] `components/metrics_panel.py:648-670` → clientside_callback `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`; add `uirevision: "metrics-panel-v1"`; hidden `metrics-panel-figure-signal` dummy Store; mirror for `candidate_metrics_panel.py`
- [ ] `components/network_visualizer.py` minimum wire: topology + cascade_add as Inputs to cytoscape callback; keep REST poll fallback; **first Phase B commit verifies render tech** (C-21)
- [ ] `components/connection_indicator.py` (new): html.Div with clientside_callback; states: connected-green, reconnecting-yellow, offline-red, demo-gray
- [ ] `backend/demo_mode.py`: set `ws-connection-status={connected:true, mode:"demo"}`
- [ ] `main.py` `/api/ws_latency` POST endpoint + Prometheus histogram + `canopy_rest_polling_bytes_per_sec{endpoint}` gauge (GAP-WS-24b)
- [ ] Phase I: `main.py` content-hash `assets_url_path` / cache-bust query string
- [ ] Two-flag runtime: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge`

**Settings**:
- [ ] `enable_browser_ws_bridge: bool = False`
- [ ] `disable_ws_bridge: bool = False`
- [ ] `enable_raf_coalescer: bool = False`
- [ ] `enable_ws_latency_beacon: bool = True`

**Cascor side**:
- [ ] Audit-event Prom counters (deferred from B-pre-a per C-C2)

**Tests** (R2-01 §6.3 / R2-02 §6.3):
- [ ] Python unit: `test_update_metrics_store_handler_returns_no_update_when_ws_connected`, `test_ws_metrics_buffer_drain_is_bounded`, `test_fallback_polling_at_1hz_when_disconnected`, `test_ws_metrics_buffer_store_is_structured_object`, `test_both_flags_interact_correctly`
- [ ] JS unit (if configured): jitter, uncapped retries, ring-bound-in-handler **via AST lint** (R1-02 §5.4)
- [ ] dash_duo: `test_browser_receives_metrics_event`, `test_chart_updates_on_each_metrics_event`, `test_chart_does_not_poll_when_websocket_connected`, `test_chart_falls_back_to_polling_on_websocket_disconnect`, `test_demo_mode_metrics_parity` (RISK-08 blocker), `test_connection_indicator_badge_reflects_state`, `test_ws_metrics_buffer_ignores_events_with_duplicate_seq`, `test_ws_metrics_buffer_is_monotonic_in_seq_no_gap_gt_1`
- [ ] Playwright: `test_websocket_frames_have_seq_field`, `test_resume_protocol_replays_missed_events`, `test_seq_reset_on_cascor_restart`, `test_plotly_extendTraces_used_not_full_figure_replace`, `test_ws_control_command_response_has_no_seq` (C-02 wire gate)
- [ ] **`test_bandwidth_eliminated_in_ws_mode`** (P0 acceptance — R1-01 MVS-TEST-15): assert `/api/metrics/history` request count == 0 over 60s after initial load
- [ ] **`test_metrics_message_has_dual_format`** (Phase H regression folded — R1-01 MVS-TEST-14)
- [ ] `test_asset_url_includes_version_query_string` (Phase I)
- [ ] Chaos: browser-bridge nightly lane — random kills/restarts, event rate variance, corrupted envelopes

**Observability** (metric-before-behavior):
- [ ] `canopy_ws_delivery_latency_ms_bucket{type}` (Histogram)
- [ ] `canopy_ws_browser_heap_mb` (Histogram from JS)
- [ ] `canopy_ws_browser_js_errors_total{component}` (Counter; **every try/catch must increment**)
- [ ] `canopy_ws_drain_callback_gen{buffer}` (Gauge; **monotonic; stuck value = dead drain**)
- [ ] `canopy_ws_active_connections` (Gauge)
- [ ] `canopy_ws_reconnect_total{reason}` (Counter)
- [ ] `canopy_rest_polling_bytes_per_sec{endpoint}` (Gauge — P0 win signal)
- [ ] `canopy_ws_connection_status{status}` (Gauge)
- [ ] `canopy_ws_backend_relay_latency_ms` (Histogram — cascor→canopy hop)
- [ ] `canopy_audit_events_total{event_type}` Prom hookup (from B-pre-a skeleton)

**SLOs** (binding after 1 week of data):

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` | <100ms | <250ms | <500ms |
| `state` | <50ms | <100ms | <200ms |
| `command_response (set_params)` | <50ms | <100ms | <200ms |
| `command_response (start/stop)` | <100ms | <250ms | <500ms |
| `cascade_add` | <250ms | <500ms | <1000ms |
| `topology` ≤64KB | <500ms | <1000ms | <2000ms |

**Alerts**:
- [ ] `WSDeliveryLatencyP95High` (ticket)
- [ ] `WSDrainCallbackGenStuck` (ticket; also flips connection status → reconnecting)
- [ ] `WSBrowserHeapHigh` (ticket): p95 > 500 MB
- [ ] `WSJSErrorsNonZero` (ticket): `increase[5m] > 0`
- [ ] `WSConnectionCount80` (ticket)

**Runbooks**:
- [ ] `ws-bridge-kill.md` (5-min TTF recipe)
- [ ] `ws-bridge-debugging.md`
- [ ] `ws-memory-soak-test-procedure.md`
- [ ] "WebSocket health" Grafana panel JSON committed to `deploy/grafana/ws-health.json`
- [ ] "Polling bandwidth" Grafana panel JSON committed

### 6.2 Exit gate

Ordered by dependency (R2-01 §6.5):
- [ ] All 27 tests in §6.1 green
- [ ] **`test_bandwidth_eliminated_in_ws_mode` green** (P0 motivator proof)
- [ ] `test_metrics_message_has_dual_format` green (Phase H fold-in)
- [ ] `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` ≥90% reduction vs baseline, sustained 1h in staging
- [ ] `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute
- [ ] "WebSocket health" dashboard panel renders p50/p95/p99
- [ ] **72-hour memory soak** (RISK-10 gate): `canopy_ws_browser_heap_mb` p95 growth <20% over 72h
- [ ] `canopy_ws_browser_js_errors_total == 0` over 72h soak
- [ ] `canopy_ws_drain_callback_gen` advances at least once per minute for every buffer type
- [ ] `test_demo_mode_metrics_parity` green in both `fast` AND `e2e` lanes (RISK-08)
- [ ] Kill switch `disable_ws_bridge=True` tested manually; restores REST polling within 5 min
- [ ] `Settings.enable_browser_ws_bridge=False` default confirmed in merged code (flip is P7 one-line follow-up PR)
- [ ] NetworkVisualizer render tech verified in first Phase B commit
- [ ] Project-lead review on the flag-flip follow-up PR
- [ ] CODEOWNERS gate on `_normalize_metric` (pre-commit hook refuses format-removal commits — R1-02 §7.5)

### 6.3 Rollback

```bash
# Fastest (2 min TTF)
export JUNIPER_DISABLE_WS_BRIDGE=true
systemctl restart juniper-canopy
# polling REST takes over via MVS-FE-07 toggle

# Dev flag off (5 min TTF)
# Config PR: enable_browser_ws_bridge=False, redeploy

# Hardcoded ring-cap reduction (1 hour; dev)
# Edit ws_dash_bridge.js MAX_METRICS_BUFFER; deploy

# Full revert (30 min TTF)
git revert <phase-b-canopy-merge-sha>
git push origin main
# Cache-bust invalidation needed because assets moved

# Browser emergency hatch
# URL query param ?ws=off forces bridge off for a specific user
```

---

## 7. Phase B-pre-b (compact)

### 7.1 Deliverables checklist

**Cookie session + CSRF** (canopy):
- [ ] `main.py` adds `SessionMiddleware` (or reuses existing — verify in §17.1)
- [ ] `/api/csrf` REST endpoint: `secrets.token_urlsafe(32)` mint-on-first-request; rotate on 1h sliding activity, session login/logout, server restart, any auth close
- [ ] Dash template render-time embedding: `window.__canopy_csrf` (NOT localStorage — XSS)
- [ ] `websocket_client.js`: first frame after `onopen` = `{type:"auth", csrf_token:...}`
- [ ] Cookie attrs: `HttpOnly; Secure; SameSite=Strict; Path=/`
- [ ] All compares use `hmac.compare_digest`

**Cascor side**:
- [ ] `/ws/control` Origin validation (uses helper from B-pre-a)
- [ ] M-SEC-04 auth-timeout: `asyncio.wait_for(ws.receive_text(), timeout=5.0)` first frame → close 1008 on TimeoutError
- [ ] M-SEC-05 rate limit: per-connection leaky bucket, 10 tokens, 10/s refill; overflow → `{command_response, status:"rate_limited", retry_after:0.3}`; connection stays up
- [ ] Per-origin handshake cooldown: 10 rejections/60s → 5-min IP block (429); cleared on restart (R1-02 §13.10)
- [ ] M-SEC-06 opaque close reasons: canonical strings only
- [ ] `disable_ws_control_endpoint: bool = False` setting (CSWSH emergency kill)
- [ ] M-SEC-11 adapter inbound validation: canopy adapter parses cascor frames via `CascorServerFrame` Pydantic (`extra="allow"`)

**Adapter HMAC** (canopy adapter → cascor):
- [ ] `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()` on connect
- [ ] First frame: `{type:"auth", csrf_token:<hmac>}`
- [ ] Cascor derives same value, compares with `hmac.compare_digest`

**Audit logger Prometheus counters** (moved from B-pre-a per C-C2):
- [ ] Wire existing `canopy_audit_events_total{event_type}` to Prometheus
- [ ] Log injection escape CRLF (`\r\n\t`) in logged strings

**CI guardrail**:
- [ ] `juniper-deploy` compose validation refuses `ws_security_enabled=false` in prod (IMPL-SEC-40)
- [ ] Refuses `JUNIPER_WS_ALLOWED_ORIGINS=*` parse-time

**Settings**:
- [ ] `ws_security_enabled: bool = True` (positive sense per C-27)
- [ ] `ws_allowed_origins: list[str]` extended to `/ws/control`
- [ ] `ws_rate_limit_enabled: bool = True`
- [ ] `ws_rate_limit_cps: int = 10`
- [ ] `ws_idle_timeout_s: int = 120` (already from B-pre-a)
- [ ] `disable_ws_control_endpoint: bool = False`

**Tests** (R2-01 §7.3):
- [ ] `test_csrf_required_for_websocket_first_frame`
- [ ] `test_csrf_token_rotation_race` (mid-request rotation)
- [ ] `test_csrf_token_uses_hmac_compare_digest` (mock `hmac.compare_digest`)
- [ ] `test_session_cookie_httponly_secure_samesitestrict`
- [ ] `test_localStorage_bearer_token_not_accepted`
- [ ] `test_command_rate_limit_10_per_sec`
- [ ] `test_rate_limit_response_is_not_an_error_close`
- [ ] `test_per_origin_cooldown_triggers_after_10_rejections`
- [ ] `test_audit_log_write_failure_fallback` (write failure → counter increment, WARN to stderr, does NOT block user)
- [ ] `test_disable_ws_control_endpoint_kill_switch`
- [ ] `test_canopy_adapter_sends_hmac_csrf_token_on_connect`
- [ ] `test_ws_control_origin_rejected`
- [ ] `test_ws_control_idle_timeout_closes_1008`
- [ ] `test_audit_log_escapes_crlf_injection`
- [ ] `test_opaque_close_reasons_no_human_readable_strings`
- [ ] `test_cscwsh_from_evil_page_cannot_start_training` (Playwright full CSWSH regression)
- [ ] `test_canopy_adapter_inbound_malformed_frame_logged_and_counted`

**Observability**:
- [ ] `canopy_ws_auth_rejections_total{reason, endpoint}`
- [ ] `canopy_ws_rate_limited_total{command, endpoint}`
- [ ] `canopy_ws_command_total{command, status, endpoint}`
- [ ] `canopy_ws_auth_latency_ms{endpoint}`
- [ ] `canopy_ws_handshake_attempts_total{outcome}` (funnel counter per R1-02 §2.3)
- [ ] `canopy_ws_per_origin_cooldown_active`
- [ ] `cascor_ws_audit_log_bytes_written_total`
- [ ] `canopy_adapter_inbound_invalid_total`
- [ ] `canopy_csrf_validation_failures_total`

**Alerts**:
- [ ] `WSAuditLogVolume2x` (ticket)
- [ ] `WSRateLimited` (ticket, sustained non-zero)
- [ ] Per-origin cooldown active >5min (ticket)

**Runbooks**:
- [ ] `ws-auth-lockout.md`
- [ ] `ws-cswsh-detection.md` (already from B-pre-a alert; expand)

### 7.2 Exit gate

- [ ] All 17 tests green
- [ ] Manual: `/ws/control` without first-frame CSRF → close 1008
- [ ] Manual: wrong origin → close 1008
- [ ] Manual: 11 commands in 900ms → close 1013 (or `rate_limited` response per spec)
- [ ] `SessionMiddleware` wired (verify via debug endpoint or test)
- [ ] Canopy adapter reconnects to cascor via HMAC handshake post-deploy
- [ ] `canopy_csrf_validation_failures_total` increments on rejected probe
- [ ] `test_disable_ws_control_endpoint_kill_switch` green (CI test for kill switch per R1-02 §10.4)
- [ ] CI guardrail: `juniper-deploy` compose validation rejects `ws_security_enabled=false` in prod
- [ ] **48-hour staging soak** — auth path change, high risk
- [ ] Runbook `ws-auth-lockout.md` published
- [ ] RISK-15 marked "in production" in risk-tracking sheet
- [ ] Project-lead sign-off

### 7.3 Rollback

```bash
# Local-dev env flag (5 min TTF)
export JUNIPER_WS_SECURITY_ENABLED=false   # prod CI refuses this
systemctl restart juniper-canopy

# Hard-disable control endpoint (5 min TTF)
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true
systemctl restart juniper-canopy
# commands route through REST automatically

# Rate limiting off
export JUNIPER_WS_RATE_LIMIT_ENABLED=false

# Audit log off
export JUNIPER_AUDIT_LOG_ENABLED=false

# Full revert
git revert <phase-b-pre-b-canopy> <phase-b-pre-b-cascor>  # reverse order
```

---

## 8. Phase C (compact)

### 8.1 Deliverables checklist

**Adapter** (`juniper-canopy/src/backend/cascor_service_adapter.py`):
- [ ] `_HOT_CASCOR_PARAMS: frozenset[str] = {"learning_rate", "candidate_learning_rate", "correlation_threshold", "candidate_pool_size", "max_hidden_units", "epochs_max", "max_iterations", "patience", "convergence_threshold", "candidate_convergence_threshold", "candidate_patience"}` (11 params per R2-01 §8.1)
- [ ] `_COLD_CASCOR_PARAMS: frozenset[str] = {"init_output_weights", "candidate_epochs"}`
- [ ] `apply_params(**params)` splits → `_apply_params_hot()` (WS, fires first) + `_apply_params_cold()` (REST)
- [ ] `_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)` with `command_id` (C-01) and unconditional REST fallback on `JuniperCascorTimeoutError` / `ConnectionError`
- [ ] Unclassified keys default to REST with WARNING log (C-09)
- [ ] `_control_stream_supervisor` background task: backoff `[1,2,5,10,30]`s, reconnect forever
- [ ] Bounded correlation map max 256 + `canopy_control_stream_pending_size` gauge (R1-02 §6.4)
- [ ] Fail-loud startup: INFO summary of hot/cold/unknown classification for every canopy param
- [ ] `assert len(_HOT_CASCOR_PARAMS) > 0 if use_websocket_set_params`

**Dash clientside** (`juniper-canopy/src/frontend/`):
- [ ] 250ms debounce in slider callback (C-29)

**Settings**:
- [ ] `use_websocket_set_params: bool = False` (C-28)
- [ ] `ws_set_params_timeout: float = 1.0` (C-03)

**Dependencies**:
- [ ] `pyproject.toml` bump `juniper-cascor-client>=${SDK_VERSION_A}`
- [ ] `../juniper-ml/pyproject.toml` matching extras pin bump

**Tests** (R2-01 §8.3):
- [ ] `test_apply_params_feature_flag_default_off`
- [ ] `test_apply_params_hot_keys_go_to_websocket`
- [ ] `test_apply_params_cold_keys_go_to_rest`
- [ ] `test_apply_params_mixed_batch_split`
- [ ] `test_apply_params_hot_falls_back_to_rest_on_ws_disconnect`
- [ ] `test_apply_params_hot_falls_back_to_rest_on_timeout`
- [ ] `test_apply_params_hot_surfaces_server_error_no_fallback`
- [ ] `test_apply_params_unclassified_keys_default_to_rest_with_warning` (C-09)
- [ ] `test_apply_params_preserves_public_signature`
- [ ] `test_apply_params_latency_histogram_labels_emitted`
- [ ] `test_control_stream_supervisor_reconnects_with_backoff`
- [ ] `test_control_stream_supervisor_shutdown_cancels_pending_futures`
- [ ] `test_len_pending_returns_to_zero_after_failure_modes` (nightly gate)
- [ ] `test_cascor_rejects_unknown_param_with_extra_forbid` (C-09 server side)
- [ ] `test_slider_debounce_250ms_collapses_rapid_updates`
- [ ] Chaos: adapter recv-task random exception injection (R1-02 §10.1)

**Observability**:
- [ ] `canopy_set_params_latency_ms_bucket{transport, key}` (flag-flip gate metric)
- [ ] `canopy_orphaned_commands_total{command}` (RISK-13)
- [ ] `canopy_control_stream_pending_size` (Gauge)

**Alerts**:
- [ ] `CanopyOrphanedCommands` (ticket, not page per R1-02 §11): `rate > 1/60`

**Runbook**:
- [ ] `ws-set-params-feature-flag.md`: flag flip, orphan command monitoring, revert

### 8.2 Exit gate (to merge Phase C, flag off)

- [ ] All unit tests green
- [ ] Coverage ≥90% on new code
- [ ] Flag-off: `canopy_set_params_latency_ms_bucket{transport="rest"}` has data; `{transport="ws"}` empty
- [ ] `test_set_params_concurrent_correlation` green

### 8.3 Exit gate (to FLIP production default — separate one-line PR per CCC-09)

Six hard gates (R1-02 §6.1):
- [ ] §5.6 histogram ≥ 7 days production data
- [ ] p99 latency delta (REST - WS) ≥ 50 ms (if smaller, do NOT flip — no user-visible win; reintroduces RISK-03/09 for nothing)
- [ ] Zero orphaned commands during canary week
- [ ] Zero correlation-map leaks (nightly `test_len_pending_returns_to_zero_after_failure_modes`)
- [ ] Canary soak ≥ 7 days
- [ ] Optional user research: skip default (C-45)

### 8.4 Rollback

```bash
# Instant
export JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false
systemctl restart juniper-canopy

# Tight timeout forces fast REST fallback (5 min TTF)
export JUNIPER_CONTROL_STREAM_TIMEOUT=0.1

# Hard-disable /ws/control
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert
git revert <phase-c-merge>
```

---

## 9. Phase D (compact)

### 9.1 Deliverables checklist

**Frontend** (`juniper-canopy/src/frontend/components/training_controls.py`):
- [ ] Clientside callback on each button: if `window.cascorControlWS` connected → `send({command, command_id: uuidv4()})`; else REST POST
- [ ] Per-command client-side correlation map
- [ ] Orphaned-command pending verification UI state: button disabled while in-flight; resolves via `command_response` OR matching `state` event
- [ ] Per-command timeouts: `start:10s`, `stop/pause/resume:2s`, `set_params:1s`, `reset:2s`
- [ ] Badge "pending" while awaiting WS ack

**Cascor** (`juniper-cascor/src/api/websocket/control_stream.py`):
- [ ] `/ws/control` handler routes inbound `{command, command_id, ...}` to existing REST-POST-backed handler
- [ ] Emits `command_response{command_id, status, error?}` (NO seq per C-02)
- [ ] Per-command timeout enforcement via `asyncio.wait_for`
- [ ] Command whitelist: `start`, `stop`, `pause`, `resume`, `reset`, `set_params`; unknown → `command_response{status:"error", code:"unknown_command"}`

**Settings**:
- [ ] `enable_ws_control_buttons: bool = False` (C-C9)

**Tests** (R2-02 §9.3):
- [ ] `test_training_button_handler_sends_websocket_command_when_connected`
- [ ] `test_training_button_handler_falls_back_to_rest_when_disconnected`
- [ ] `test_rest_endpoint_still_returns_200_and_updates_state` (GAP-WS-06 regression)
- [ ] Playwright: `test_start_button_uses_websocket_command`, `test_command_ack_updates_button_state`, `test_disconnect_restores_button_to_disabled`, `test_csrf_required_for_websocket_start`, `test_orphaned_command_resolves_via_state_event`
- [ ] `test_set_params_echoes_command_id` (Phase G cross-check)
- [ ] `test_per_command_timeout_start_10s`
- [ ] `test_per_command_timeout_stop_2s`
- [ ] `test_unknown_command_rejected`
- [ ] `test_orphaned_command_falls_back_to_rest_after_timeout`

**Observability**:
- [ ] `canopy_training_control_total{command, transport}` (track REST:WS ratio)
- [ ] `canopy_training_control_orphaned_total{command}`
- [ ] `canopy_training_control_command_latency_ms{command, transport}`
- [ ] `cascor_ws_control_command_received_total{command}`

**Runbook**:
- [ ] `ws-control-button-debug.md`

### 9.2 Exit gate

- [ ] All 9 tests green
- [ ] `test_csrf_required_for_websocket_start` green
- [ ] Manual: Start with WS connected → training state within 10s
- [ ] Manual: kill cascor before Start → REST fallback succeeds
- [ ] Manual: click Start with wrong CSRF → 1008 close
- [ ] **24h staging soak zero orphaned commands**
- [ ] **48h canary cohort soak zero orphan reports**
- [ ] REST endpoints still receive traffic from non-browser consumers (access logs)
- [ ] `docs/REFERENCE.md` documents both REST and WS training control APIs
- [ ] **B-pre-b in production ≥48h** (entry gate for Phase D — R2-02 §9.2)

### 9.3 Rollback

```bash
# Buttons revert to REST (5 min TTF)
export JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false
systemctl restart juniper-canopy

# CSWSH emergency
export JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true

# Full revert (20 min TTF)
git revert <phase-d-canopy> <phase-d-cascor>
```

---

## 10. Phase E (compact; CONDITIONAL)

**Conditional ship**: only if Phase B telemetry shows RISK-04/11 triggering. Otherwise the 0.5s quick-fix from Phase 0-cascor is sufficient. (R2-01 §10.2)

### 10.1 Deliverables checklist

**Cascor** (`juniper-cascor/src/api/websocket/manager.py`):
- [ ] Per-client `_ClientState` with dedicated `pump_task` + bounded `send_queue`
- [ ] Per-client `asyncio.Queue` bounded at 256 (configurable via `ws_per_client_queue_size`)

**Policy matrix** (R2-01 §10.1):

| Event type | Queue | Overflow policy |
|---|---:|---|
| `state` | 128 | close(1008) — terminal-state-sensitive |
| `metrics` | 128 | close(1008) — drops cause chart gaps, still observable |
| `cascade_add` | 128 | close(1008) — each event is a growth step |
| `candidate_progress` | 32 | drop_oldest — coalesceable |
| `event` (training_complete) | 128 | close(1008) — terminal-sensitive |
| `command_response` | 64 | close(1008) — client waits |
| `pong` | 16 | drop_oldest — client can re-ping |

**Settings**:
- [ ] `ws_backpressure_policy: Literal["block", "drop_oldest_progress_only", "close_slow"] = "drop_oldest_progress_only"` (C-15)
- [ ] `ws_per_client_queue_size: int = 256`

**Tests** (R2-01 §10.3):
- [ ] `test_slow_client_does_not_block_other_clients`
- [ ] `test_slow_client_send_timeout_closes_1008_for_state`
- [ ] `test_slow_client_progress_events_dropped`
- [ ] `test_drop_oldest_queue_policy`
- [ ] `test_backpressure_default_is_drop_oldest_progress_only` (regression)
- [ ] `test_event_type_classification_for_backpressure_policy` (R1-02 §9.8: every event type maps to explicit policy)
- [ ] `test_block_policy_still_works_when_opted_in`
- [ ] `test_close_slow_policy_closes_stalled_clients`
- [ ] `test_terminal_state_events_not_dropped_under_drop_oldest_progress`

**Observability**:
- [ ] `cascor_ws_dropped_messages_total{reason, type}` — **alert any non-zero `state_dropped`**
- [ ] `cascor_ws_slow_client_closes_total`
- [ ] `cascor_ws_per_client_queue_depth_histogram`

**Alerts**:
- [ ] `WSStateDropped` (PAGE): silent data loss
- [ ] `WSSlowBroadcastP95` (ticket)

**Runbook**:
- [ ] `ws-backpressure-policy.md`

### 10.2 Exit gate

- [ ] All tests green
- [ ] Load test: 50 clients, 1 slow with 2s delay, 49 fast receive all events within 200ms p95
- [ ] `cascor_ws_broadcast_send_duration_seconds_bucket` p95 < 50ms under load
- [ ] 48h staging zero `state_dropped` alerts
- [ ] Runbook published

### 10.3 Rollback

```bash
# Revert to block policy (5 min TTF; RISK-04 returns but RISK-11 mitigated)
export JUNIPER_WS_BACKPRESSURE_POLICY=block
systemctl restart juniper-cascor

# Full revert (10 min)
git revert <phase-e-cascor>
```

---

## 11. Phase F (compact)

### 11.1 Deliverables checklist

- [ ] Cascor `/ws/training` + `/ws/control` emit `{"type":"ping","ts":<float>}` every 30s
- [ ] Client JS (`websocket_client.js`) replies `pong` within 5s
- [ ] Dead-conn detection: no `pong` within 10s of `ping` → close 1006 → trigger reconnect
- [ ] Integrates with M-SEC-10 idle timeout (heartbeat resets timer)
- [ ] GAP-WS-31 lift: uncapped reconnect attempts with 60s max interval once cap hit
- [ ] Jitter formula (explicit): `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))`

### 11.2 Tests

- [ ] `test_ping_sent_every_30_seconds`
- [ ] `test_pong_received_cancels_close`
- [ ] `test_reconnect_backoff_has_jitter` (tight: `0 <= delay <= cap`, prevents NaN/Infinity per R1-02 §9.9)
- [ ] `test_reconnect_attempt_unbounded_with_cap` (GAP-WS-31 > 10 attempts)
- [ ] `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect`
- [ ] `test_dead_connection_detected_via_missing_pong`
- [ ] `test_jitter_formula_no_nan_delay` (R1-02 §9.9 regression)

### 11.3 Exit gate

- [ ] All 7 tests green
- [ ] Manual firewall drop → dead conn detected within 40s (30+10)
- [ ] 48h staging: no NaN delays in JS console; no reconnect storms
- [ ] `WSReconnectStorm` alert rule in place
- [ ] Runbook `ws-reconnect-storm.md`

### 11.4 Rollback

```bash
# Users hard-refresh to recover (10 min)
export JUNIPER_DISABLE_WS_AUTO_RECONNECT=true
# Or push cache-busted JS with old jitter formula (hotfix)
git revert <phase-f-merge>
```

---

## 12. Phase G (compact)

### 12.1 Deliverables checklist

Cascor-side integration tests via FastAPI `TestClient.websocket_connect()`, no SDK dep. 15 tests total in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`:

- [ ] `test_set_params_via_websocket_happy_path`
- [ ] `test_set_params_whitelist_filters_unknown_keys`
- [ ] `test_set_params_init_output_weights_literal_validation` (rejects `"random; rm -rf /"`)
- [ ] `test_set_params_oversized_frame_rejected` (64KB cap)
- [ ] `test_set_params_no_network_returns_error`
- [ ] `test_unknown_command_returns_error` (GAP-WS-22 regression)
- [ ] `test_malformed_json_closes_with_1003`
- [ ] `test_set_params_origin_rejected` (M-SEC-01b regression)
- [ ] `test_set_params_unauthenticated_rejected` (X-API-Key regression)
- [ ] `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05 regression)
- [ ] `test_set_params_bad_init_output_weights_literal_rejected`
- [ ] **`test_set_params_concurrent_command_response_correlation`** (R1-05 §4.29)
- [ ] **`test_set_params_during_training_applies_on_next_epoch_boundary`** (R1-05 §4.29; ack-vs-effect distinction)
- [ ] **`test_set_params_echoes_command_id`** (C-01 mandatory gate for SDK consumer)
- [ ] `test_ws_control_command_response_has_no_seq` (C-02 cross-referenced from Phase 0-cascor)

**Contract-lane test** (C-34):
- [ ] `test_fake_cascor_message_schema_parity` (R1-05 §4.30) — lives in canopy but runs in both repos' `contract` lane

**CI marker**: Tests marked `@pytest.mark.critical` — run in `fast` lane on every PR to cascor or cascor-client (R1-02 §7.4).

### 12.2 Exit gate

- [ ] All 15 tests green
- [ ] `pytest -m contract` lane green in both cascor + canopy CI

### 12.3 Rollback

n/a (test-only).

---

## 13. Phase H (compact)

### 13.1 Deliverables checklist

**Test-only + doc phase. NO removal of any format in this migration (C-22).**

- [ ] `test_normalize_metric_produces_dual_format` (lives in `juniper-canopy/src/tests/contract/test_normalize_metric_dual_format.py`, asserts BOTH nested + flat on every output)
- [ ] `test_normalize_metric_nested_topology_present`
- [ ] `test_normalize_metric_preserves_legacy_timestamp_field`
- [ ] Wire-level `test_metrics_message_has_dual_format` already folded into Phase B (C-22 cross-ref)
- [ ] Consumer audit doc `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`: catalog every consumer (MetricsPanel, CandidateMetricsPanel, Prometheus `/api/metrics`, WS drain, debug logger, test fixtures)
- [ ] `.github/CODEOWNERS` entry: `juniper-canopy/src/backend/normalize_metric.py @<project-lead>`, `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>` — **HARD MERGE GATE** (R1-02 §13.11; C-22)
- [ ] Pre-commit hook refuses commits removing nested format keys from normalize output (R1-02 §7.5)
- [ ] GitHub branch protection updated to require CODEOWNERS review

### 13.2 Exit gate

- [ ] Regression tests green
- [ ] Audit doc published + reviewed
- [ ] CODEOWNERS rule enforced (verified by opening a test PR that touches `normalize_metric.py` without owner review — must block)
- [ ] Pre-commit hook installed

### 13.3 Rollback

```bash
# Restore old metric format (5-10 min)
git revert <phase-h-canopy>
# Audit /api/metrics shape hash matches pre-H
```

None needed for test-only + doc phase. If a future PR proposes removal based on audit, it must re-run Phase H scenario analysis.

---

## 14. Cross-repo merge sequence

Numbered list with branch names. Full order from R2-01 §16 + R2-02 §16.

1. **PR-1**: `phase-a-sdk-set-params` → `juniper-cascor-client` main → tag → **PyPI publish** → wait 2-5 min for index
2. **PR-2**: `phase-0-cascor-seq-replay-resume` → `juniper-cascor` main (10 commits squash-merged)
   - **72-hour staging soak** → production
3. **PR-3**: `phase-b-pre-a-cascor-security` → `juniper-cascor` main
4. **PR-4**: `phase-b-pre-a-canopy-security` → `juniper-canopy` main (depends on PR-3)
5. **PR-5**: `phase-b-cascor-audit-prom-counters` → `juniper-cascor` main
6. **PR-6**: `phase-b-canopy-drain-wiring` → `juniper-canopy` main (pins `juniper-cascor-client>=SDK_VERSION_A`)
   - **72-hour memory soak** → staging → **1-hour P0 measurement** → production deploy
7. **PR-7**: `phase-b-canopy-flag-flip` → `juniper-canopy` main (one-line; `enable_browser_ws_bridge=True` default)
   - ── Phase B gate closes — P0 metric validated ──
8. **PR-15** (parallel with C): `phase-g-cascor-set-params-integration` → `juniper-cascor` main
9. **PR-8**: `phase-b-pre-b-cascor-control-security` → `juniper-cascor` main
10. **PR-9**: `phase-b-pre-b-canopy-csrf-audit` → `juniper-canopy` main (depends on PR-8)
    - **48-hour production soak of B-pre-b** → gate for Phase D
11. **PR-10**: `phase-c-canopy-set-params-adapter` → `juniper-canopy` main (flag off)
    - **≥7 days production data** → **PR-10-flip** (separate) → flag flip
12. **PR-11**: `phase-d-cascor-control-commands` → `juniper-cascor` main
13. **PR-12**: `phase-d-canopy-button-ws-routing` → `juniper-canopy` main (depends on PR-11)
14. **PR-13** (conditional on telemetry): `phase-e-cascor-backpressure-pump-tasks` → `juniper-cascor` main
15. **PR-14**: `phase-f-heartbeat-jitter` → `juniper-cascor` + `juniper-canopy` main
16. **PR-16**: `phase-h-normalize-metric-audit` → `juniper-canopy` main

**Critical path (P0 win)**: PR-1 → PR-2 → PR-3 → PR-4 → PR-6 → soak → PR-7.

**Version bumps**:

| Repo | Phase | Bump |
|---|---|---|
| cascor-client | A | minor (new public method) |
| cascor | 0-cascor | minor (new envelope fields) |
| cascor | B-pre-a/b | patch |
| cascor | E | minor |
| cascor | G | patch (test-only) |
| canopy | B-pre-a/b | patch |
| canopy | B | minor |
| canopy | C/D/H/I | patch |
| juniper-ml | per SDK bump | patch |

**Helm chart**: `Chart.yaml` `version` + `appVersion` must match app semver (Juniper CLAUDE.md memory).

**Branch naming**: `ws-migration/phase-<letter>-<slug>`.

**Worktree naming** (Juniper parent CLAUDE.md): `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>` in `/home/pcalnon/Development/python/Juniper/worktrees/`.

**TestPyPI**: Phase A publishes to TestPyPI on PR; canopy downstream PRs install from TestPyPI for e2e before real publish.

**Cross-version CI lane** (new in R2-03 §15.5): canopy e2e runs against N-1 AND N pinned SDK versions; both must pass.

---

## 15. Kill switch matrix

Every switch below has a CI test (`test_<switch>_env_override`) flipping the flag and asserting the validation metric moves. Untested = doesn't count (C-39).

| Phase | Switch (env var / PR revert) | Default | Who | MTTR | Validation metric |
|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 1024 | ops | 5 min | `cascor_ws_resume_requests_total{outcome="out_of_range"}` spike |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | 0.5 | ops | 5 min | `cascor_ws_broadcast_timeout_total` spike |
| 0-cascor | Rolling restart cascor | — | ops | 10 min | New `server_instance_id`; client logs snapshot refetch |
| 0-cascor | `git revert` PR-2 | — | ops | 15 min | Clients w/ cached UUIDs get `out_of_range` |
| A-SDK | Downgrade `juniper-cascor-client` pin | — | ops | 15 min | `pip index versions` shows resolved version |
| A-SDK | PyPI yank (only if installs-won't-import) | — | ops | 2 min | Package 404 on new installs |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 | ops | 5 min | `canopy_ws_per_ip_rejected_total → 0` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | localhost defaults | ops | 5 min | `canopy_ws_origin_rejected_total` drops |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS='*'` | — | — | — | **REFUSED BY PARSER** (non-switch; panic-edit prevention; C-30) |
| B-pre-a | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | 120 | ops | 5 min | New connections persist indefinitely |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | true | ops | 5 min | No new audit log writes |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | true | ops | 5 min | `canopy_ws_auth_rejections_total → 0` — **prod CI refuses** (CI guardrail) |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | ops | 5 min | `canopy_training_control_total{transport="ws"} → 0` (CSWSH emergency) |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | true | ops | 5 min | `canopy_ws_rate_limited_total` freezes |
| B | `JUNIPER_CANOPY_ENABLE_BROWSER_WS_BRIDGE=false` | false→true post-soak | ops | 5 min | `canopy_rest_polling_bytes_per_sec` rises to baseline |
| B | `JUNIPER_CANOPY_DISABLE_WS_BRIDGE=true` | false | ops | 5 min | Same (permanent kill per C-14) |
| B | Hardcoded ring-cap reduction | — | dev | 1 hour | `canopy_ws_browser_heap_mb` drops in soak |
| B | URL `?ws=off` param | — | user | instant | Per-user bridge off |
| B | `git revert` PR-6 | — | ops | 30 min | Cache-bust invalidate |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | false | ops | 2 min | `canopy_set_params_latency_ms_bucket{transport="ws"}` freezes |
| C | `JUNIPER_CONTROL_STREAM_TIMEOUT=0.1` | 1.0 | ops | 5 min | Tight timeout forces fast REST fallback |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | false | ops | 5 min | `canopy_training_control_total{transport="rest"}` rises |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | ops | 5 min | Same (CSWSH emergency) |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | `drop_oldest_progress_only` | ops | 5 min | `cascor_ws_dropped_messages_total → 0` (RISK-04 returns — documented) |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | false | ops | 10 min | `canopy_ws_reconnect_total` freezes |
| H | `git revert` PR-16 | — | ops | 10 min | `/api/metrics` shape hash matches pre-H |
| I | `git revert` cache bust commit | — | ops | 10 min | Asset URL query string reverts |

**Meta-rule**: staging kill-switch drills during each phase's soak window. If any TTF >5 min, the phase does not ship to production. Two consecutive switch failures → migration halts (R1-02 §9.4 abandon trigger).

---

## 16. Risk register

| ID | Risk | Sev/Lik | Phase | Owner | Kill switch (TTF) | Signal |
|---|---|---|---|---|---|---|
| 01 | Dual metric format removed aggressively | H/M | H | Y | `git revert` (5-10 min) | `/api/metrics` shape hash drift |
| 02 | Phase B clientside-callback debuggability | M/H | B | F+O | `disable_ws_bridge=true` (5 min) | `drain_callback_gen` stuck; `browser_js_errors > 0` |
| 03 | Phase C REST+WS ordering race | M/L | C | Y | `use_websocket_set_params=false` (2 min) | set_params latency delta; order-violation log |
| 04 | Slow-client blocks broadcasts | M/M | E (full) / 0-cascor (quick-fix) | C | `ws_backpressure_policy=close_slow` (5 min) | `broadcast_send_duration_seconds` p95 > 500ms |
| 05 | Playwright fixture misses real-cascor regression | M/M | B, D | O | n/a — fix the test | **Nightly** smoke against real cascor (R1-02 §11 amplification) |
| 06 | Reconnection storm after cascor restart | L/M | F | F | `disable_ws_auto_reconnect=true` (10 min) | `canopy_ws_reconnect_total` > 5× baseline |
| 07 | 50-conn cap hit by multi-tenant deployment | L/L | n/a (single-tenant per C-24) | C+O | raise `ws_max_connections` (10 min) | `ws_active_connections` at 80% cap |
| 08 | Demo mode parity breaks | L/M | B | Y | revert PR (10 min) | `test_demo_mode_metrics_parity` both lanes (RISK-08 blocker) |
| 09 | Phase C unexpected user-visible behavior | L/M | C | Y+F | `use_websocket_set_params=false` (2 min) | Orphaned commands; latency delta |
| 10 | Browser memory exhaustion (unbounded chart data) | M/H | B | F | `disable_ws_bridge=true` (5 min) + ring-cap reduction | `browser_heap_mb` p95 > 500 MB |
| 11 | Silent data loss via drop-oldest broadcast queue | H/L | E | C | `ws_backpressure_policy=block` (5 min; RISK-04 returns) | `dropped_messages_total{type="state"}` — **PAGE on any non-zero** |
| 12 | Background tab memory spike on foreground | L/M | B | F | Same as RISK-10 (5 min) | Same as RISK-10 |
| 13 | Orphaned commands after timeout | M/M | B, C, D | F+Y | reduce timeouts / `use_websocket_set_params=false` | `orphaned_commands_total > 1/min` (ticket, not page — R1-02 §11) |
| 14 | Cascor crash mid-broadcast leaves clients inconsistent | L/L | B | C | rolling restart canopy/cascor (10 min) | `seq_current` stops advancing with active conns → `WSSeqCurrentStalled` PAGE |
| 15 | CSWSH attack exploits missing Origin validation | **H**/M | B-pre-a + B-pre-b | Sec+C+Y | `disable_ws_control_endpoint=true` (5 min) | `origin_rejected_total` PAGE on any non-zero from unknown origin_hash. **Abandon trigger if kill switch itself fails** (R1-02 §9.4) |
| 16 | Topology > 64KB silently for large networks | M/M | B-pre-a + follow-up chunking | C | REST fallback for topology (5 min) | `oversized_frame_total{endpoint,type}`; WARNING log. **Residual risk >50-100 hidden units**; fix v1.1 |
| CCC-01 | `request_id` rename incomplete across corpus | H | all | R3 lead | grep pre-review | stale references survive to Phase G |
| CCC-02 | Metric added but no alert/panel | M | all | CCC-02 owner | metric-before-behavior hard gate | silent metric |
| CCC-03 | Kill switch documented but never tested in CI | H | all | ops | CI flip test mandatory | undocumented switch doesn't work in incident |
| CCC-04 | Cross-repo pin points at unreleased version | H | A→C | ops | `required_upstream_sha` check | CI resolve failure |

---

## 17. Observability matrix

| Phase | New metrics (count, key) | New alerts | Dashboard |
|---|---|---|---|
| 0-cascor | 13 cascor_ws_* (seq_current, replay_occupancy/bytes/capacity, resume_total/replayed, broadcast_send/timeout, pending_connections, state_throttle_coalesced, broadcast_from_thread_errors, connections_active, command_responses_total, seq_gap_detected) | `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap`, `WSPendingConnectionStuck`, `WSSlowBroadcastP95`, `WSStateDropped` (PAGE) | n/a (stack metrics only) |
| A-SDK | 1 sdk: `juniper_cascor_client_ws_set_params_total{status}` | none | n/a |
| B-pre-a | 5 security: `cascor_ws_oversized_frame_total`, `cascor_ws_per_ip_rejected_total`, `canopy_ws_oversized_frame_total`, `canopy_ws_per_ip_rejected_total`, `canopy_ws_origin_rejected_total{origin_hash, endpoint}`, `canopy_audit_events_total` (counter only) | `WSOriginRejection` (PAGE), `WSOversizedFrame` | n/a |
| B | 9 canopy_ws_*: `delivery_latency_ms_bucket`, `browser_heap_mb`, `browser_js_errors_total`, `drain_callback_gen`, `active_connections`, `reconnect_total`, `rest_polling_bytes_per_sec` (**P0**), `connection_status`, `backend_relay_latency_ms`; plus `canopy_audit_events_total` Prom hookup | `WSDeliveryLatencyP95High`, `WSDrainCallbackGenStuck`, `WSBrowserHeapHigh`, `WSJSErrorsNonZero`, `WSConnectionCount80` | **"WebSocket health"** + **"Polling bandwidth"** Grafana JSON committed to `deploy/grafana/` |
| B-pre-b | 9: `auth_rejections_total`, `rate_limited_total`, `command_total`, `auth_latency_ms`, `handshake_attempts_total`, `per_origin_cooldown_active`, `audit_log_bytes_written_total`, `adapter_inbound_invalid_total`, `csrf_validation_failures_total` | `WSAuditLogVolume2x`, `WSRateLimited`, per-origin cooldown | Security panel (append to WS health) |
| C | 3: `set_params_latency_ms_bucket{transport, key}`, `orphaned_commands_total`, `control_stream_pending_size` | `CanopyOrphanedCommands` (ticket, not page per R1-02 §11) | set_params latency panel |
| D | 3: `training_control_total{command, transport}`, `training_control_orphaned_total`, `training_control_command_latency_ms`, `cascor_ws_control_command_received_total` | — | Button latency panel |
| E | 3: `dropped_messages_total{reason, type}`, `slow_client_closes_total`, `per_client_queue_depth_histogram` | `WSStateDropped` (PAGE), `WSSlowBroadcastP95` (promoted from ticket) | Backpressure panel |
| F | reconnect jitter histogram | `WSReconnectStorm` | — |
| G | — (tests only) | — | — |
| H | audit dashboard panel | — | `_normalize_metric` shape-hash trend |

**Metric-presence pytest** (R1-02 §10.6) runs in `fast` lane on every PR. Scrapes cascor + canopy `/metrics`, asserts every canonical metric name is present. Failure blocks merge.

**Label canonical values** (cardinality discipline):
- `endpoint` ∈ {`/ws/training`, `/ws/control`, `/ws/worker`, `/ws/monitor`}
- `type` ∈ {`metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, `event`, `command_response`, `connection_established`, `resume_ok`, `resume_failed`}
- `transport` ∈ {`ws`, `rest`}
- `reason` ∈ {`origin_rejected`, `cookie_missing`, `csrf_invalid`, `per_ip_cap`, `cap_full`, `rate_limited`, `frame_too_large`, `idle_timeout`, `malformed_json`}
- `outcome` ∈ {`accepted`, `rejected`, `timeout`, `success`, `server_restarted`, `out_of_range`, `malformed`, `no_resume_timeout`}

---

## 18. Decision quick-reference

55 decisions from R2-04. Row format: `D-NN | summary | default | source`.

| D | Summary | Applied default | Source |
|---|---|---|---|
| 01 | `set_params` default timeout | **1.0 s** | R1-05 §4.1; C-03 |
| 02 | Correlation field name | **`command_id`** | R1-05 §4.2; C-01 |
| 03 | `command_response` carries seq | **No** | R1-05 §4.17; C-02 |
| 04 | rAF coalescer ship state | **scaffold-disabled** | R1-05 §4.3; C-16 |
| 05 | REST fallback cadence during disconnect | **1 Hz** | R1-05 §4.4; C-17 |
| 06 | NetworkVisualizer Phase B scope | **minimum wire; deep migration deferred if cytoscape** | R1-05 §4.5; C-21 |
| 07 | `ws-metrics-buffer` store shape | **structured `{events, gen, last_drain_ms}`** | R1-05 §4.7; C-18 |
| 08 | GAP-WS-24 split | **24a (browser) + 24b (backend), both in Phase B** | R1-05 §4.8; C-20 |
| 09 | Phase B-pre effort estimate | **0.5 (B-pre-a) + 2 (B-pre-b)** | R1-05 §4.9 |
| 10 | Security flag naming | **positive `ws_security_enabled`** | R1-02; R2-03 §15.3; C-27 |
| 11 | Phase 0-cascor carve-out from Phase B | **carve out** | R1-05 §4.19; C-12 |
| 12 | M-SEC-10/11/12 adoption | **adopt 10/11, fold 12 into 07** | R1-05 §4.15 |
| 13 | GAP-WS-19 status | **RESOLVED (regression test only)** | R1-05 §4.16; C-11 |
| 14 | Two-phase registration | **`_pending_connections`** | R1-05 §4.18; C-08 |
| 15 | `server_start_time` vs `server_instance_id` | **`server_instance_id` programmatic, start_time advisory** | R1-05 §4.20; C-06 |
| 16 | `replay_buffer_capacity` in `connection_established` | **add** | R1-05 §4.21; C-07 |
| 17 | Phase B feature flag default | **flag-off `enable_browser_ws_bridge=False`** | R1-02; R1-05 §4.45; C-14 |
| 18 | Permanent kill switch `disable_ws_bridge` | **add** | R1-05 §4.45; C-14 |
| 19 | Phase E backpressure default | **`drop_oldest_progress_only`** | R1-05 §4.36; C-15 |
| 20 | SDK retries on `set_params` timeout | **caller decides** | R1-05 §4.22; C-04 |
| 21 | REST `update_params` / `/api/metrics/history` retention | **permanent** | R1-05 §4.23; C-23 |
| 22 | Debounce layer | **Dash clientside** | R1-05 §4.24; C-29 |
| 23 | Phase B-pre split | **split a+b** | R1-05 §4.35; C-13 |
| 24 | Q6 per-IP cap default | **5 per IP** | R1-05 §4.37; C-26 |
| 25 | Q1 deployment topology | **single-tenant v1** | R1-05 §4.38; C-24 |
| 26 | Shadow traffic | **skip** | R1-05 §4.39; C-31 |
| 27 | CODEOWNERS `_normalize_metric` | **enforce (hard gate)** | R1-05 §4.41; C-22 |
| 28 | Audit logger scope | **dedicated logger, skeleton B-pre-a, Prom B** | R1-05 §4.14 |
| 29 | Adapter synthetic auth | **HMAC CSRF token** | R1-05 §4.43; C-10 |
| 30 | One resume per connection | **add** | R1-05 §4.12; C-25 |
| 31 | Per-command HMAC | **defer indefinitely** | R1-05 §4.11; C-33 |
| 32 | Multi-tenant replay isolation | **defer** | R1-05 §4.13; C-24 |
| 33 | Rate limit buckets | **single 10/s** | R1-05 §4.46; C-26 |
| 34 | Unclassified-key routing | **both layers (cascor `extra="forbid"` + adapter REST+WARN)** | R1-05 §4.44; C-09 |
| 35 | Replay buffer default size | **1024, env-tunable** | R2-01 §18.1; C-05 |
| 36 | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` kill switch | **add** | R1-02 §3.3; §15 matrix |
| 37 | Metrics-presence CI test | **enforce** | R1-02 §10.6 |
| 38 | Staging soak Phase 0-cascor | **72 h** | R1-02 §3.4; R2-01 §3.5 |
| 39 | Staging soak Phase B | **72 h** | R1-02 §5.7; R2-01 §6.5 |
| 40 | Chaos tests category | **blocking for replay-race/broadcast/broadcast_from_thread; nightly for others** | R2-01 §18.9; R1-02 §10.1 |
| 41 | Load tests as gate | **blocking for 0-cascor** | R1-02 §10.3 |
| 42 | Frame budget test | **recording-only** | R1-05 §4.3; C-35 |
| 43 | `contract` pytest marker | **add** | R1-05 §4.34; C-34 |
| 44 | Multi-browser matrix | **Chromium only v1** | R1-05 §4.31; C-32 |
| 45 | User research study | **skip v1** | R1-05 §4.32 |
| 46 | `JUNIPER_WS_SEND_TIMEOUT_SECONDS` configurable | **yes, default 0.5** | R1-02 §3.2 |
| 47 | Phase C feature flag default | **False** | unanimous; C-28 |
| 48 | Phase C flag-flip criteria | **6 enumerated hard gates** | R1-02 §6.1; C-28 |
| 49 | Phase D feature flag | **add `enable_ws_control_buttons=False`** | R1-02 §7.1 |
| 50 | Error-budget burn freeze rule | **enforce** | R1-02 §2.4; C-42 |
| 51 | `WSOriginRejection` alert severity | **page** | R1-02 §2.4 |
| 52 | `WSSeqCurrentStalled` alert | **add PAGE** | R1-02 §2.4 |
| 53 | Kill-switch MTTR tested in staging | **test every switch** | R1-02 §13.7; C-39 |
| 54 | REST polling handler retention | **preserve forever** | R1-05 §4.23; C-23 |
| 55 | Source-doc patches Round 5 batch | **batch** | R1-05 §8.6 |
| 56 (impl) | REST deprecation policy | **no deprecation planned** | R2-04 §5.1 |
| 57 (impl) | juniper-ml meta-package extras pin bump cadence | **immediate post-A** | R2-04 §5.2 |
| 58 (impl) | CI lane budget tolerance | **≤25% runtime increase** | R2-04 §5.3 |
| 59 (impl) | Browser JS error pipeline | **POST to `/api/ws_browser_errors`** | R2-04 §5.4 |
| 60 (impl) | Worktree/branch policy | **one worktree per phase per repo** | R2-04 §5.5; Juniper CLAUDE.md |
| 61 (impl) | Deploy-freeze window | **mid-week for behavior-changing flag flips** | R1-02 §5.7 |
| 62 (impl) | Bandwidth baseline measurement before Phase B | **measure 1h in staging pre-deploy** | R2-04 §5.7 |

**High cost-of-deferral** (decide before phase starts, not in-flight): **D-02, D-11, D-17, D-19, D-23**.

**Medium cost-of-deferral**: D-03, D-18, D-29, D-38, D-39, D-48, D-49, D-53.

---

## 19. Test acceptance matrix

Canonical test names with phase, type, and measurable criterion. Contract-lane (`@pytest.mark.contract`) runs on every PR.

| Phase | Test name | Type | Measurable criterion |
|---|---|---|---|
| 0-cascor | `test_seq_monotonically_increases_per_connection` | unit | Every broadcast has seq > previous |
| 0-cascor | `test_replay_buffer_bounded_to_configured_capacity` | unit | `maxlen == Settings.ws_replay_buffer_size` |
| 0-cascor | `test_resume_replays_events_after_last_seq` | integration | N-5 last_seq → exactly 5 events |
| 0-cascor | `test_resume_failed_server_restarted` | integration | Stale UUID → `resume_failed{server_restarted}` |
| 0-cascor | `test_snapshot_seq_atomic_with_state_read` | integration | Concurrent read shows no torn snapshot |
| 0-cascor | `test_second_resume_closes_connection_1003` | unit | Second resume on same conn → close 1003 |
| 0-cascor | `test_state_coalescer_preserves_terminal_transitions` | unit | Started→Failed within 200ms, both observed |
| 0-cascor | `test_broadcast_from_thread_exception_logged` | unit | Exception in worker thread → log entry, no silent swallow |
| 0-cascor | `test_ws_control_command_response_has_no_seq` | contract | `/ws/control` command_response frames have no seq field |
| 0-cascor | `test_close_all_holds_lock` | unit | Regression for GAP-WS-19 |
| 0-cascor | chaos_broadcast_replay_race (hypothesis) | chaos | No seq gaps, no deadlocks, no coroutine leaks over 100 gather() cycles |
| 0-cascor | Load: 100 Hz × 60s × 10 clients | load (blocking) | p95 latency < 250ms, memory ±10% |
| A-SDK | `test_set_params_default_timeout_is_one_second` | unit | Default kwarg = 1.0 (regression for C-03) |
| A-SDK | `test_set_params_caller_cancellation_cleans_correlation_map` | unit (**mandatory**) | After caller cancel, `len(_pending) == 0` |
| A-SDK | `test_set_params_concurrent_callers_correlate_via_command_id` | unit | 2 concurrent calls distinguished correctly |
| A-SDK | `test_set_params_fails_fast_on_disconnect` | unit | Disconnect → JuniperCascorConnectionError, no queue |
| A-SDK | `test_correlation_map_bounded_at_256` | unit | 257th call → JuniperCascorOverloadError |
| A-SDK | `test_sdk_command_frame_matches_cascor_parser` | contract | SDK frame parses against cascor Pydantic model |
| B-pre-a | `test_oversized_frame_rejected_with_1009` | unit | 65KB frame → close 1009 |
| B-pre-a | `test_per_ip_cap_enforced_6th_rejected_1013` | unit | 6th same-IP conn → close 1013 |
| B-pre-a | `test_per_ip_map_shrinks_to_zero` | unit | Memory leak guard: entries at 0 are deleted |
| B-pre-a | `test_origin_allowlist_rejects_third_party` | unit | Cross-origin → close 1008 |
| B-pre-a | `test_empty_allowlist_rejects_all_fail_closed` | unit | Empty list = reject all |
| B-pre-a | `test_idle_timeout_closes_1000` | unit | 120s idle → close 1000 |
| B-pre-a | `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` | Playwright e2e | Cross-origin page → WebSocket rejected |
| B-pre-a | `test_audit_log_format_and_scrubbing` | unit | JSON entry shape + sensitive fields scrubbed |
| B | `test_bandwidth_eliminated_in_ws_mode` | **Playwright (P0 gate)** | `/api/metrics/history` request count == 0 over 60s post-load |
| B | `test_metrics_message_has_dual_format` | **Playwright (RISK-01 gate)** | `ws-metrics-buffer.events[-1]` contains BOTH flat + nested keys |
| B | `test_chart_does_not_poll_when_websocket_connected` | dash_duo | REST fetch count stays at 0 while WS connected |
| B | `test_chart_falls_back_to_polling_on_websocket_disconnect` | dash_duo | Disconnect → REST polling resumes at 1 Hz |
| B | `test_demo_mode_metrics_parity` | dash_duo + e2e | Demo mode = real mode (RISK-08 gate; both lanes) |
| B | `test_resume_protocol_replays_missed_events` | Playwright | Disconnect N events, reconnect → N events replayed |
| B | `test_seq_reset_on_cascor_restart` | Playwright | New `server_instance_id` → snapshot refetch |
| B | `test_plotly_extendTraces_used_not_full_figure_replace` | Playwright | Chart uses extendTraces, not full replace |
| B | `test_ws_metrics_buffer_is_monotonic_in_seq_no_gap_gt_1` | dash_duo | Buffer events have no seq gaps |
| B | `test_ws_metrics_buffer_store_is_structured_object` | unit | Store shape `{events, gen, last_drain_ms}` |
| B | `test_fallback_polling_at_1hz_when_disconnected` | unit | Fallback `n % 10 != 0` toggle (C-17) |
| B | `test_both_flags_interact_correctly` | unit | Two-flag logic `enabled = enable_ws_bridge and not disable_ws_bridge` |
| B | `test_browser_message_handler_keys_match_cascor_envelope` | contract | Every `on(type,...)` handler maps to cascor emitter |
| B | `test_fake_cascor_message_schema_parity` | contract | Fake harness envelopes = real cascor envelopes |
| B | 72h memory soak | soak (blocking) | `canopy_ws_browser_heap_mb` p95 growth < 20% |
| B | `test_asset_url_includes_version_query_string` | Playwright | Phase I cache bust |
| B-pre-b | `test_csrf_required_for_websocket_first_frame` | unit | Absent/invalid CSRF → close 1008 |
| B-pre-b | `test_csrf_token_rotation_race` | unit | Mid-request rotation: current completes, next uses new, old rejected |
| B-pre-b | `test_csrf_token_uses_hmac_compare_digest` | unit | Mock asserts constant-time compare |
| B-pre-b | `test_session_cookie_httponly_secure_samesitestrict` | unit | All three attrs set |
| B-pre-b | `test_command_rate_limit_10_per_sec` | unit | 11th command → rate_limited response |
| B-pre-b | `test_rate_limit_response_is_not_an_error_close` | unit | Conn stays up; rate_limited envelope |
| B-pre-b | `test_canopy_adapter_sends_hmac_csrf_token_on_connect` | unit | Adapter first frame = HMAC-derived CSRF |
| B-pre-b | `test_audit_log_escapes_crlf_injection` | unit | `\r\n\t` escaped in logged strings |
| B-pre-b | `test_opaque_close_reasons_no_human_readable_strings` | unit | Close frames = numeric codes only |
| B-pre-b | `test_disable_ws_control_endpoint_kill_switch` | security | Kill-switch CI test (R1-02 §4.2 item 14) |
| B-pre-b | `test_cswsh_from_evil_page_cannot_start_training` | Playwright | Full CSWSH regression |
| B-pre-b | 48h staging soak | soak | Adapter reconnect rate stable |
| C | `test_apply_params_feature_flag_default_off` | unit | Default = False |
| C | `test_apply_params_hot_keys_go_to_websocket` | unit | Hot param → WS path |
| C | `test_apply_params_cold_keys_go_to_rest` | unit | Cold param → REST |
| C | `test_apply_params_mixed_batch_split` | unit | Hot+cold → correct split |
| C | `test_apply_params_hot_falls_back_to_rest_on_ws_timeout` | unit | Timeout → REST fallback (no retries) |
| C | `test_apply_params_unclassified_keys_default_to_rest_with_warning` | unit | Unknown key → REST + WARN log |
| C | `test_cascor_rejects_unknown_param_with_extra_forbid` | contract | Cascor Pydantic rejects unknown keys on wire |
| C | `test_len_pending_returns_to_zero_after_failure_modes` | nightly | Correlation map leak prevention |
| C | Adapter recv-task chaos (hypothesis exception types) | chaos | Pending map fully drained; supervisor restarts task |
| C | 7-day canary production | soak | Flag-flip evidence collection |
| D | `test_csrf_required_for_websocket_start` | Playwright | Regression for B-pre-b |
| D | `test_training_button_handler_falls_back_to_rest_when_disconnected` | unit | Disconnect → REST POST |
| D | `test_rest_endpoint_still_returns_200_and_updates_state` | regression | REST preserved (C-23) |
| D | `test_orphaned_command_resolves_via_state_event` | Playwright | Matching `state` event resolves pending button |
| D | `test_per_command_timeout_start_10s` | unit | Start button timeout = 10s |
| D | 24h staging + 48h canary | soak | Zero orphaned commands |
| E | `test_slow_client_does_not_block_other_clients` | unit | Slow client 2s delay; fast clients unaffected |
| E | `test_drop_oldest_queue_policy` | unit | Queue full → oldest dropped |
| E | `test_terminal_state_events_not_dropped_under_drop_oldest_progress` | unit | `state` events never dropped |
| E | `test_event_type_classification_for_backpressure_policy` | unit | Every event type has explicit policy mapping |
| E | Load: 50 clients, 1 slow × 2s, 49 fast | load | Fast clients p95 < 200ms |
| F | `test_ping_sent_every_30_seconds` | unit | Ping cadence |
| F | `test_dead_connection_detected_via_missing_pong` | unit | No pong 10s → close 1006 |
| F | `test_jitter_formula_no_nan_delay` | unit | 0 ≤ delay ≤ cap; no NaN/Infinity |
| F | `test_reconnect_attempt_unbounded_with_cap` | unit | >10 attempts allowed |
| G | `test_set_params_via_websocket_happy_path` | integration | FastAPI TestClient roundtrip |
| G | `test_set_params_echoes_command_id` | **contract (C-01 mandatory)** | Cascor echoes `command_id` in response |
| G | `test_set_params_concurrent_command_response_correlation` | integration | 2 clients get correct responses |
| G | `test_set_params_during_training_applies_on_next_epoch_boundary` | integration | Ack vs effect distinction |
| G | `test_set_params_rate_limit_triggers_after_10_cmds` | integration | M-SEC-05 regression |
| H | `test_normalize_metric_produces_dual_format` | **contract (C-22 gate)** | Output contains both flat + nested keys |
| H | `test_normalize_metric_nested_format_unchanged_since_phase_h` | unit | Shape hash regression |
| — | Metric-presence pytest | security (every PR) | Scrapes /metrics, asserts canonical names present |
| — | REST regression harness | `fast` (every PR) | Every baseline REST endpoint returns expected shape |

**Test count totals** (R2-02 §15.2): Unit ~97, Integration ~18, E2E (dash_duo + Playwright) ~16, Contract ~11. Contract runtime budget: <50 ms per test, <5 s per suite.

---

## 20. Disagreements with R2 inputs

Brief, explicit. This doc is a lean consolidation so disagreements are minimal; most R2 inputs converge.

1. **Replay buffer default 1024 (not 256)** — R2-01 §18.1 and R2-02 §18.1 pick 1024; R2-03 and R2-04 discuss 256 as R1-02's preferred safety-first value. This doc picks **1024 with env override** (C-05) — all R2 eventually converge here.
2. **`ws_security_enabled` positive sense** — R1-05 kept negative; R2-01 §18.2, R2-03 §15.3, R2-04 D-10 override to positive. This doc picks **positive** (C-27). Justification: safety principle outweighs source-doc fidelity when source doc itself raises footgun as open question.
3. **Origin on `/ws/training` in B-pre-a** — R1-05 §4.35 placed all Origin in B-pre-b; R2-01 §18.3 moves Origin-on-training into B-pre-a (R1-01's exfiltration argument). This doc follows **R2-01** (Origin on `/ws/training` in B-pre-a; Origin on `/ws/control` in B-pre-b).
4. **Uncapped reconnect in Phase B** — R2-01 §18.4 lifts the 10-attempt cap; R1-01 kept it. This doc follows **R2-01** (lift the cap) since REST fallback covers permanent unreachability and the lift is a 3-line change.
5. **Phase C ships in main wave flag-off, not deferred to v1.1** — R2-01 §18.5 adopts main-wave-flag-off; R1-01 argued defer. This doc follows **R2-01** since flag-off costs nothing to ship.
6. **Phase H is test-only + CODEOWNERS, no removal** — R2-01 §18.8 adopts R1-02 principle 7. This doc follows (C-22).
7. **Chaos tests elevated to blocking gates for Phase 0-cascor** — R2-01 §18.9 adopts R1-02's elevation; R2-04 D-40 prefers nightly. This doc **picks R2-01 for the three specific tests** (replay race, broadcast chaos, broadcast_from_thread chaos) which catch seq/replay corruption catastrophes. Other hypothesis-driven chaos is nightly.
8. **Effort: R2-02's expected 15.75 days vs R1-05's 13.5** — this doc preserves **R1-05's 13.5 days** as the target and uses R2-02's as an upper-bound triple. Schedule headroom matters less than achievable target.

---

## 21. Self-audit log

### 21.1 Passes performed

1. **Pass 1**: Read R2-01 (§1-§18), R2-02 (§1-§17), R2-03 (§1-§16), R2-04 (§0-§7) in chunks.
2. **Pass 2**: Built §0 First hour, §1 Constitution, §2 Phase index as first-write material. Everything else references these.
3. **Pass 3**: Built per-phase compact sections §3-§13 using checklist + rollback commands + exit gate format.
4. **Pass 4**: Built cross-cutting sections §14-§19 (merge sequence, kill switches, risks, observability, decisions, tests).
5. **Pass 5**: Self-audit against prompt requirements; applied corrections below.
6. **Pass 6**: Wrote §20 disagreements and this §21.

### 21.2 Corrections applied during self-audit

1. **§0 first hour**: initial draft had only 5 steps; expanded to 8 steps after re-read including the baseline bandwidth measurement (D-62) and `worktree` creation confirmation.
2. **§1 constitution**: initial draft had 36 positions; re-read R2-02 §1 and R2-03 §3.3 and added C-40 (additive rollout) and C-41 (`emitted_at_monotonic` field placement) and C-42 (error-budget burn rule) for 42 total.
3. **§2 phase index**: initial draft omitted the "NOT-in-phase" column. Added. Also reordered rows so 0-cascor / A-SDK / B-pre-a are grouped at the top (parallel tranche).
4. **§3 Phase 0-cascor tests**: initial draft had 15 tests. Re-read R2-02 §3.3 confirmed 20 tests. Added the 5 missing ones (`test_seq_is_assigned_on_loop_thread`, `test_resume_malformed_data`, etc.).
5. **§3 observability**: initial draft had 11 metrics. R2-02 §3.3 + R2-01 §3.4 union is 13 metrics (adds `cascor_ws_seq_gap_detected_total` and `replay_buffer_capacity_configured`). Corrected.
6. **§6 Phase B tests**: initial draft was unclear which Phase H tests are folded in. Explicit cross-reference: `test_metrics_message_has_dual_format` (R1-01 MVS-TEST-14) is the Phase H regression gate folded into Phase B so Phase H can defer safely. Added to the test matrix in §19 with "(RISK-01 gate)" annotation.
7. **§6 72-hour soak**: initial draft said "72 h memory soak" but wasn't clear whether this blocks Phase B PR merge or only the flag-flip PR. Clarified: **72 h blocks the flag-flip follow-up PR (PR-7), NOT the initial Phase B merge (PR-6) which ships flag-off**.
8. **§7 Phase B-pre-b `extra="forbid"`**: initial draft missed listing `test_cascor_rejects_unknown_param_with_extra_forbid`. Added (C-09 server side).
9. **§8 Phase C flip gates**: initial draft had 3 flip gates. R1-02 §6.1 has 6. Corrected to 6 with explicit list.
10. **§14 merge sequence**: initial draft had PR-7 (flag flip) before the 72h soak. Reordered: PR-6 merge → 72h soak → PR-7 flag flip. Reflects the "soak before behavior change" rule.
11. **§15 kill switch matrix**: initial draft had 19 rows. R2-01 §14 has 22 rows. Added missing (rolling restart, revert PR, PyPI yank, hardcoded ring cap, URL `?ws=off`, Phase D CSWSH emergency). Also elevated `JUNIPER_WS_ALLOWED_ORIGINS='*'` to a REFUSED non-switch row per R2-01 §18.
12. **§16 risk register**: initial draft had 16 risks. Added CCC-Risk-01 through CCC-Risk-04 from R2-03 §14 (rename incompleteness, metric-alert decoupling, untested kill switch, upstream pin pointing at unreleased).
13. **§17 observability matrix**: initial draft omitted "New alerts" column. Added.
14. **§18 decision quick-reference**: initial draft had 55 decisions. Added 7 implicit decisions (D-56..D-62) from R2-04 §5. Total 62.
15. **§19 test acceptance matrix**: initial draft had ~40 tests. R2-02 §15.2 total is ~142 tests across all phases. This is too many for the lean doc; R3-03 picks the **load-bearing / measurable / P0-critical** ~75 tests and references R2-02 §15.2 for the full catalog. Added footer citing R2-02 §15.2 for totals.
16. **§20 disagreements**: initial draft only had 5 disagreements. Added 3 more (uncapped reconnect, Phase C main-wave flag-off, Phase H test-only).
17. **Per-phase rollback commands**: initial draft gave rollback as prose only. Expanded to verbatim bash commands per prompt's "rollback procedures — safety-critical" requirement.
18. **Exit gates measurability check**: walked every phase's exit gate. Fixed 3 vague items — Phase B criterion #2 had "polling reduced" → corrected to ">90% reduction sustained 1h in staging measured via `canopy_rest_polling_bytes_per_sec{endpoint='/api/metrics/history'}`". Phase 0-cascor criterion #8 had "seq monotonic" → made it concrete metric name `cascor_ws_seq_gap_detected_total == 0`. Phase B-pre-b criterion #3 had vague "wrong origin rejected" → numeric close code 1008.
19. **Phase E conditional**: initial draft had Phase E unconditional. Clarified per R2-01 §10.2 that Phase E only ships if Phase B telemetry shows RISK-04/11 triggering; otherwise the 0.5s quick-fix from Phase 0-cascor suffices.
20. **Cross-repo merge sequence**: initial draft had Phase G after Phase D. Corrected per R2-02 §16: Phase G ships in parallel with Phase C (bundled with Phase 0-cascor envelope changes already in place).

### 21.3 Coverage check

- [x] §0 first hour: 8-step concrete procedure including baseline measurement
- [x] §1 constitution: 42 settled positions, every row sourced
- [x] §2 phase index: 12 phases, all 8 columns filled including NOT-in-phase
- [x] §3-§13 per-phase: all 11 phases have deliverables checklist, exit gate, rollback commands
- [x] §14 merge sequence: 16 PRs in critical order with branch names
- [x] §15 kill switch matrix: 22 rows covering every phase (+ non-switch row)
- [x] §16 risk register: 16 RISK + 4 CCC-Risk rows
- [x] §17 observability: metrics+alerts+dashboard per phase
- [x] §18 decisions: 62 decisions with applied defaults and sources
- [x] §19 test acceptance: ~75 load-bearing tests with measurable criteria
- [x] §20 disagreements: 8 explicit items with justification
- [x] §21 self-audit: 20 corrections logged

### 21.4 Length check

Target: 1000-1500 lines (lean reformat; ~half of R3-01/R3-02 ≥2000 line target). Actual: ~1400 lines. Within envelope.

### 21.5 Scope discipline

- [x] Did not re-litigate R1-05 resolutions; treated them as settled (C-01..C-42)
- [x] Did not introduce new GAP-WS-NN, M-SEC-NN, RISK-NN identifiers
- [x] Referenced R2-NN sources liberally, did not repeat their full prose
- [x] Used tables and checklists over prose
- [x] Every phase has exit gate with concrete measurable criteria
- [x] Every phase has rollback commands (verbatim bash)
- [x] Every test has a phase + type + criterion

**Scope discipline PASS.**

### 21.6 What this doc intentionally does NOT do

- Does not include full architecture prose — that's R2-01 (best-of synthesis) and R2-03 (cross-cutting)
- Does not include full decision discussion — that's R2-04 §3
- Does not include full cross-cutting concern treatment — that's R2-03 §3-§14
- Does not include 1-week-by-1-week project schedule — that's R2-02 day-by-day contracts
- Does not repeat file-path tables when R2-01/R2-02 already have them — cross-references instead

R3-03 is the **cheat sheet that lives next to the engineer's monitor while they work**. For prose-heavy context, fall through to R2-01; for phase-execution contract detail, fall through to R2-02; for cross-cutting concern ownership, fall through to R2-03; for decision rationale, fall through to R2-04.

---

**End of R3-03 lean execution document.**
