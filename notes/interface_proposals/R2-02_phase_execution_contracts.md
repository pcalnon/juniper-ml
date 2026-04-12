# Round 2 Proposal R2-02: Phase Execution Contracts

**Angle**: Each phase as an execution contract with measurable gates, deliverables, PR lists, owner-class assignments, effort bounds, and rollback
**Author**: Round 2 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 2 consolidation — input to Round 3
**Inputs consolidated**: R1-01 (critical path / minimum viable), R1-02 (risk-minimized / safety first), R1-03 (maximalist / comprehensive), R1-04 (operational runbook), R1-05 (disagreement reconciliation — treated as settled positions throughout)

---

## 0. How to read this document

Each phase is specified as a contract between the implementer and the project. Every phase section answers the same six questions:

1. **Goal** — one sentence, what changes in the world when this phase ships.
2. **Entry gate** — the preconditions: dependent phases, code SHAs, env state, artifacts that must already exist.
3. **Deliverables checklist** — the concrete artifacts (files, commits, metrics, tests, docs) that must exist when the phase is "done".
4. **Pull request plan** — branch names, titles, scope boundaries, merge order, owner class.
5. **Exit gate** — measurable acceptance criteria with concrete test names or metric thresholds. Going/no-go decision lives here.
6. **Rollback** — how to undo the phase if something goes wrong after merge.

Every phase also has a **"NOT in this phase"** list. This is load-bearing — it prevents Round 3 from re-importing scope that Round 1 and R1-05 already pushed out.

Owner-class taxonomy used throughout:

- **backend-cascor**: engineers working on `juniper-cascor` (server-side Python, WebSocket handlers, replay buffer, `/ws/training` + `/ws/control`).
- **backend-canopy**: engineers working on `juniper-canopy` Python server (FastAPI, Dash server callbacks, adapter, security middleware).
- **frontend**: engineers working on canopy JavaScript (`assets/*.js`, Dash clientside callbacks, Plotly migration).
- **SDK**: engineers working on `juniper-cascor-client` (`CascorControlStream.set_params`, correlation map, PyPI release).
- **security**: reviewer for CSWSH/M-SEC controls (can be same human as backend-canopy if staffed that way; listed separately so the review lane is explicit).
- **ops**: engineers working on `juniper-deploy`, Helm charts, Prometheus, runbooks, monitoring.

Effort estimates use the pessimistic/expected/optimistic triple, in engineering days. Expected is what R1-05 §4.40 budgets; the variance bounds come from the R1 corpus spread.

Source-doc identifiers (GAP-WS-NN, M-SEC-NN, RISK-NN) cite the canonical `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE.

---

## 1. Settled positions (from R1-05)

R1-05 resolved 47 disagreements among the R0 corpus. Round 2 treats these as settled and does not re-litigate them. The resolutions relevant to this phase-execution plan are bulleted here for quick reference.

### 1.1 Protocol / wire-contract settled positions

- **Correlation field name is `command_id`** (R1-05 §4.2, D02, X01). NOT `request_id`. The SDK kwarg is `command_id`; the wire frame field is `command_id`; cascor echoes it in `command_response`. R1-04's D11 and R1-03 §4.3 that used `request_id` are overridden.
- **`command_response` does NOT carry `seq`** (R1-05 §4.17, D17, X02, X10, X18). `/ws/training` has a seq-bearing broadcast stream with replay. `/ws/control` has personal RPC with no seq and no replay eligibility. Client matches command_response to caller via `command_id` correlation map, not via seq.
- **`set_params` default timeout = 1.0 s** (R1-05 §4.1, D01). NOT 5.0 s. Callers that need a larger window pass it explicitly.
- **SDK fails fast on disconnect** (R1-05 §4.42, X12). No SDK-side reconnect queue. The caller (canopy adapter) retries via REST.
- **Replay buffer capacity: 1024 entries, configurable via `Settings.ws_replay_buffer_size`** (R1-05 §6.1 mentions R0-03 default 1024; R1-02 §12.1 argues 256 to exercise snapshot path). **R2-02 picks 1024** as the production default and makes it configurable so R1-02's safety-first argument can be served by setting `JUNIPER_WS_REPLAY_BUFFER_SIZE=256` in dev/staging without rebuilding cascor. Justification: R0-03's argument is operationally correct for production; R1-02's argument is a dev/test hygiene concern that a configuration lever satisfies. Both views get what they want.
- **Separate seq namespaces per endpoint** (R1-05 §4.17). `/ws/training` seq is independent of `/ws/control` (which has none).
- **Two-phase registration via `_pending_connections` set** (R1-05 §4.18, D18). NOT `seq_cursor` on broadcast.
- **`server_instance_id` is the comparison key** (R1-05 §4.20, D20). `server_start_time` is advisory human-readable only.
- **`replay_buffer_capacity` on `connection_established`** (R1-05 §4.21, D21). Additive field so clients can tune behavior.
- **Cascor `/ws/control` has `extra="forbid"` Pydantic validation** (R1-05 §4.44, X15). Unknown keys rejected on wire. AND canopy adapter defaults unclassified keys to REST with warning.
- **Adapter-to-cascor auth via HMAC first frame** (R1-05 §4.43, X13). `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()`. NOT the `X-Juniper-Role: adapter` header skip.

### 1.2 Phase-structure settled positions

- **GAP-WS-19 is RESOLVED on main** (R1-05 §4.16, D16). Verified at `juniper-cascor/src/api/websocket/manager.py:138-156`. Not included in any phase scope. A regression test (`test_close_all_holds_lock`) lands in Phase A regardless as a guard.
- **Phase 0-cascor is carved out from Phase B** (R1-05 §4.19, D19, X03). Renamed from R0-03's "Phase A-server" to "Phase 0-cascor" to avoid collision with source doc's "Phase A" (SDK). **Note**: this proposal (R2-02) keeps the label "Phase A (cascor-server)" in the Phase index for colloquial compatibility but the PR branch names and code identifiers are "phase-0-cascor-*". See §3.
- **Phase B-pre splits into B-pre-a and B-pre-b** (R1-05 §4.35, D35, X05). B-pre-a = max_size + per-IP cap + audit-logger skeleton (gates Phase B). B-pre-b = Origin + CSRF + cookie + rate limit (gates Phase D). Parallels Phase B, not in series.
- **Phase E default backpressure policy = `drop_oldest_progress_only`** (R1-05 §4.36, D36). NOT `block`. Policy is configurable.
- **rAF coalescing scaffolded-but-disabled in Phase B** (R1-05 §4.3, D03). `Settings.enable_raf_coalescer = False` default. Scaffold ships but is gated.
- **REST polling fallback at 1 Hz during reconnect window** (R1-05 §4.4, D04). Not 100 ms.
- **NetworkVisualizer**: minimum WS wiring in Phase B; deep render migration deferred to Phase B+1 IF cytoscape is confirmed (R1-05 §4.5, D05). First Phase B commit performs the render-tech verification.
- **GAP-WS-24 split into 24a/24b** (R1-05 §4.8, D08). 24a = browser emitter in canopy JS; 24b = canopy `/api/ws_latency` backend endpoint + Prometheus histogram.
- **`ws-metrics-buffer` store shape**: `{events: [...], gen: int, last_drain_ms: float}` (R1-05 §4.7, D07). NOT a bare array.
- **`disable_ws_auth` stays negative-sense** (R1-05 §4.10, D10). No rename. Ops guardrail: CI check that fails if `JUNIPER_DISABLE_WS_AUTH=true` appears in any production compose file.
- **Per-command HMAC (M-SEC-02 point 3) is DEFERRED indefinitely** (R1-05 §4.11, D11).
- **Multi-tenant replay isolation DEFERRED for v1** (R1-05 §4.13, D13). Q1 topology resolved: single-tenant.
- **Per-IP connection cap = 5 default, configurable** (R1-05 §4.37, D37). Resolves Q6.
- **Audit logger scope**: dedicated `canopy.audit` logger with JSON formatter + rotating file handler + scrub allowlist in Phase B-pre-a; Prometheus counters land in Phase B (R1-05 §4.14, D14, X20).
- **M-SEC-10 and M-SEC-11 are new canonical identifiers**; M-SEC-12 folded into M-SEC-07 (R1-05 §4.15, D15).
- **Two-flag browser-bridge design**: `Settings.enable_browser_ws_bridge` (dev flag, default False until B-pre-b lands) + `Settings.disable_ws_bridge` (permanent ops kill switch, default False) (R1-05 §4.45, X16).
- **Contract-test pytest marker** (R1-05 §4.34, D34): new `contract` marker for fake-vs-real parity tests.
- **Single-bucket rate limit** = 10 cmd/s (R1-05 §4.46, X17). Two-bucket is a deferred follow-up.
- **CI runtime split**: recording-only `latency_recording` marker (R1-05 §4.28, D28); strict latency assertions are local-only (not CI gate).
- **Playwright runtime estimate = 5-8 min** due to dash_duo Selenium serialization (R1-05 §4.27, D27). CI uses `pytest -n auto --dist=loadfile`.
- **Fake cascor schema parity test** as new contract test (R1-05 §4.30, D30).
- **Chromium only for v1** (R1-05 §4.31, D31).
- **User research excluded from automated tests** (R1-05 §4.32, D32).
- **Shadow traffic rejected** (R1-05 §4.39, D39). Rollback via feature-flag flip, not dual-transport traffic.
- **CODEOWNERS entry for `_normalize_metric`** in Phase H (R1-05 §4.41, D41).
- **"One resume per connection" security rule** added to Phase B-pre-a (R1-05 §4.12, D12).
- **Total effort: 13.5 engineering days / ~4.5 weeks calendar** (R1-05 §4.40, D40).

### 1.3 Identifiers and flags introduced

From the resolutions, this plan uses the following canonical identifiers:

- `Settings.enable_browser_ws_bridge: bool = False` (dev flag, §1.2 above).
- `Settings.disable_ws_bridge: bool = False` (permanent ops kill switch, §1.2 above).
- `Settings.enable_raf_coalescer: bool = False` (Phase B scaffold flag, §1.2 above).
- `Settings.use_websocket_set_params: bool = False` (Phase C flag).
- `Settings.ws_max_connections_per_ip: int = 5` (§1.2 above).
- `Settings.ws_backpressure_policy: str = "drop_oldest_progress_only"` (§1.2 above).
- `Settings.ws_replay_buffer_size: int = 1024` (§1.1 above).
- `Settings.ws_allowed_origins: list[str] = []` (empty = reject-all, fail closed).
- `Settings.ws_idle_timeout_seconds: int = 120` (M-SEC-10).
- `Settings.enable_ws_latency_beacon: bool = True` (GAP-WS-24a flag).

---

## 2. Phase index

Owner-class key: **C** = backend-cascor, **Y** = backend-canopy (Python), **F** = frontend (canopy JS), **S** = SDK (cascor-client), **Sec** = security review, **O** = ops.

| # | Phase | Owner | Effort (opt/exp/pess, eng-days) | Entry deps | Exit (top criterion) | Rollback TTF |
|---|---|---|---|---|---|---|
| 1 | A (cascor-server prereqs, aka Phase 0-cascor) | C | 1.5 / 2.0 / 3.0 | main branch + GAP-WS-19 verified | `seq` monotonic on every `/ws/training` broadcast, resume + snapshot_seq working end-to-end | 15 min (revert) |
| 2 | A-SDK (parallel with A) | S | 0.5 / 1.0 / 1.5 | main branch; no cross-repo dep | `CascorControlStream.set_params(params, timeout=1.0)` passes caller-cancellation test | PyPI yank or no-op (flag is off) |
| 3 | B-pre-a (read-path security) | C + Y + Sec | 0.5 / 1.0 / 1.5 | main branch (parallel with Phase A) | oversized frame → 1009 close; 6th conn from same IP → 1013 close; audit logger skeleton present | 5 min (env flag revert) |
| 4 | B (frontend wiring + polling elimination) | Y + F + C | 3.0 / 4.0 / 5.0 | Phase A + Phase B-pre-a in main | `canopy_rest_polling_bytes_per_sec` reduced >90% in staging | 5 min (`disable_ws_bridge=True`) |
| 5 | B-pre-b (control-path security) | Y + Sec | 1.0 / 1.5 / 2.0 | Phase B in main (parallel) | Origin spoof → close 1008; CSRF absent → close 1008; rate-limit 11th cmd → close 1013 | 10 min (revert) |
| 6 | C (set_params P2) | Y | 1.5 / 2.0 / 3.0 | Phase A-SDK + Phase B in main | `test_set_params_concurrent_correlation` passes; slider works via WS with flag on | 2 min (`use_websocket_set_params=False`) |
| 7 | D (control buttons) | F + Y + C | 0.75 / 1.0 / 1.5 | Phase B + Phase B-pre-b in main | `test_csrf_required_for_websocket_start` passes; start button WS path works | 5 min (REST fallback) |
| 8 | E (backpressure full) | C | 0.75 / 1.0 / 1.5 | Phase A in main (optional — can ship after Phase B) | `test_slow_client_does_not_block_fast_clients` passes | 5 min (`ws_backpressure_policy=block`) |
| 9 | F (heartbeat + jitter) | F + C | 0.25 / 0.5 / 1.0 | Phase B in main | Jitter-backoff formula test passes; no NaN delays | 10 min (revert JS asset) |
| 10 | G (cascor set_params integration tests) | C | 0.25 / 0.5 / 0.75 | Phase A in main | All 13 Phase G tests green | n/a (test-only) |
| 11 | H (normalize_metric regression gate) | Y | 0.5 / 1.0 / 1.5 | Phase B in main | `test_normalize_metric_produces_dual_format` green; CODEOWNERS enforced | 5 min (git revert normalize PR) |
| 12 | I (asset cache busting) | F | 0.1 / 0.25 / 0.5 | folds into Phase B | Browsers pick up new JS without hard refresh | 5 min (revert cache-bust config) |
| — | **Total (with parallelism)** | — | **10.35 / 13.5 / 19.0** | — | — | — |

The 13.5-day expected total matches R1-05 §4.40. Optimistic assumes all §5 unresolved-evidence items (R1-05 §5.1-5.6) verify favorably; pessimistic assumes session middleware has to be added from scratch and NetworkVisualizer is Plotly-based after all.

---

## 3. Phase A: cascor-server prerequisites (Phase 0-cascor in R1-05 naming)

### 3.1 Goal

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope, advertises `server_instance_id` + `replay_buffer_capacity` on `connection_established`, supports a 1024-entry replay buffer with a `resume` handler, exposes `snapshot_seq` atomically on the REST `/api/v1/training/status` endpoint, and no longer stalls fan-out on a single slow client. The `/ws/control` endpoint gains protocol-error responses but **no seq field**. The state coalescer bug (GAP-WS-21) that silently drops terminal transitions is fixed. This phase is purely additive — existing clients that ignore `seq` keep working (R0-03 §6.5.4 additive-field contract).

### 3.2 Entry gate

- [ ] `juniper-cascor` main branch clean, tests green (baseline confirmed with `cd juniper-cascor/src/tests && bash scripts/run_tests.bash`).
- [ ] GAP-WS-19 state verified: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` confirms lock-holding pattern matches R0-03 §11.1 verification (R1-05 §4.16).
- [ ] No other concurrent Phase A-scope PR open on cascor (merge-queue check).
- [ ] `cascor_ws_replay_buffer_occupancy` and `cascor_ws_broadcast_send_duration_seconds_bucket` metric names reserved in the Prometheus namespace (no name collisions).

### 3.3 Deliverables checklist

Server-side code changes (10 commits per R0-03 §7.1 / R1-03 §5.11):

- [ ] **A-srv-1**: `juniper-cascor/src/api/websocket/messages.py` adds optional `seq: Optional[int] = None` on every envelope builder.
- [ ] **A-srv-2a**: `juniper-cascor/src/api/websocket/manager.py` adds `server_instance_id: str = str(uuid.uuid4())`, `server_start_time: float = time.time()`, `_next_seq: int`, `_seq_lock: asyncio.Lock`, `_replay_buffer: deque[tuple[int, dict]]` with `maxlen=Settings.ws_replay_buffer_size`, `_assign_seq_and_append()` helper.
- [ ] **A-srv-2b**: `connect()` sends `connection_established` containing `server_instance_id`, `server_start_time`, `replay_buffer_capacity` in `data`.
- [ ] **A-srv-3**: `_send_json()` wraps `ws.send_json(msg)` in `asyncio.wait_for(..., timeout=0.5)` with exception logging (R0-03 §5.2 quick-fix; GAP-WS-07).
- [ ] **A-srv-4**: `replay_since(last_seq: int) -> list[dict]` helper + `ReplayOutOfRange` exception class.
- [ ] **A-srv-5a**: `training_stream.py` adds `_pending_connections: set[WebSocket]`, `connect_pending()`, `promote_to_active()` (two-phase registration, R1-05 §4.18 — pending-set design).
- [ ] **A-srv-5b**: `/ws/training` handler dispatches `resume` frame (5 s frame timeout) → `resume_ok` (replays events since `last_seq`) or `resume_failed` (out_of_range / server_restarted), then promotes to active.
  - Server restart detected via `server_instance_id` mismatch (R1-05 §4.20).
  - "One resume per connection" rule (R1-05 §4.12): track `resume_consumed: bool` per connection, second resume → close 1003.
- [ ] **A-srv-6**: `/api/v1/training/status` REST endpoint adds `snapshot_seq` and `server_instance_id` fields, read atomically under `_seq_lock` (§6.5.2 atomicity).
- [ ] **A-srv-7**: `juniper-cascor/src/lifecycle/manager.py:133-136` — replace 1 Hz drop-filter with a debounced coalescer; terminal transitions (`Completed`, `Failed`, `Stopped`) bypass throttle (GAP-WS-21).
- [ ] **A-srv-8**: `broadcast_from_thread` attaches `asyncio.Task.add_done_callback(_log_exception)` so swallowed exceptions surface in logs (GAP-WS-29).
- [ ] **A-srv-9**: `/ws/control` handler returns protocol-error envelopes for unknown commands and non-JSON frames (close 1003) (GAP-WS-22). **Uses `command_id` echo if present, omits it if absent. Does NOT carry `seq`** (R1-05 §4.17).
- [ ] **A-srv-10**: `CHANGELOG.md` + `docs/websocket_protocol.md` update describing the additive field contract.

Tests:

- [ ] `test_seq_monotonically_increases_across_broadcasts` (renamed from R0-05 `test_seq_monotonically_increases_per_connection` per R1-05 §4.17 to clarify subject is `/ws/training`).
- [ ] `test_seq_is_assigned_on_loop_thread`.
- [ ] `test_seq_lock_does_not_block_broadcast_iteration`.
- [ ] `test_replay_buffer_bounded_to_configured_capacity` (asserts `maxlen == Settings.ws_replay_buffer_size`).
- [ ] `test_replay_buffer_capacity_configurable_via_env` (override to 256 via `JUNIPER_WS_REPLAY_BUFFER_SIZE`, assert `_replay_buffer.maxlen == 256`).
- [ ] `test_resume_replays_events_after_last_seq`.
- [ ] `test_resume_failed_out_of_range`.
- [ ] `test_resume_failed_server_restarted` (server_instance_id mismatch).
- [ ] `test_connection_established_advertises_instance_id_and_capacity`.
- [ ] `test_snapshot_seq_atomic_with_state_read` (concurrency test: read REST status while broadcast ongoing; verify no torn snapshot).
- [ ] `test_second_resume_closes_connection_1003` (R1-05 §4.12).
- [ ] `test_slow_client_send_timeout_does_not_block_fanout` (0.5 s `_send_json` quick-fix).
- [ ] `test_state_coalescer_flushes_terminal_transitions` (GAP-WS-21 fix).
- [ ] `test_broadcast_from_thread_exception_logged` (GAP-WS-29 fix — uses caplog).
- [ ] `test_unknown_command_returns_protocol_error_envelope` (GAP-WS-22).
- [ ] `test_malformed_json_closes_1003`.
- [ ] `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 contract test — asserts `seq` absent on `/ws/control` command_response).
- [ ] `test_pending_connections_not_eligible_for_broadcast`.
- [ ] `test_promote_to_active_atomic_under_seq_lock`.
- [ ] `test_close_all_holds_lock` (regression test for GAP-WS-19 — belt-and-suspenders per R1-05 §4.16).

Observability:

- [ ] `cascor_ws_broadcast_send_duration_seconds` histogram exported (fed by `_send_json` timing).
- [ ] `cascor_ws_replay_buffer_occupancy` gauge exported (current buffer size / capacity).
- [ ] `cascor_ws_replay_buffer_capacity_configured` gauge exported once at startup (R1-02 §2.1 — makes operational tunable visible).
- [ ] `cascor_ws_resume_replayed_events` histogram exported, buckets `{0, 1, 5, 25, 100, 500, 1024}`.
- [ ] `cascor_ws_resume_failed_total{reason}` counter exported, reasons = `{out_of_range, server_restarted, second_resume}`.
- [ ] `cascor_ws_seq_gap_detected_total` counter exported (increments if server notices an unexpected seq gap — should always be 0).

Documentation:

- [ ] `juniper-cascor/CHANGELOG.md` entry mentioning GAP-WS-07, GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29, GAP-WS-32 addressed.
- [ ] `juniper-cascor/docs/websocket_protocol.md` section "Sequence numbers, replay, and reconnection" covering the protocol additions.

### 3.4 Pull request plan

Single PR, squash-merged. Reason: the 10 commits are tightly coupled (resume handler depends on replay buffer depends on seq field), and splitting would force multiple cross-repo coordination windows.

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P1 | `phase-0-cascor-seq-replay-resume` | `feat(ws): seq numbers, replay buffer, resume protocol, state coalescer` | C | juniper-cascor main |

Branch naming follows the Juniper centralized worktree convention. The PR body must cross-reference: GAP-WS-07, GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29, GAP-WS-32, M-SEC-12-folded (R1-05 §4.15 log injection escaping), R1-05 §4.12 / §4.17 / §4.18 / §4.19 / §4.20 / §4.21.

### 3.5 Exit gate (measurable)

This phase exits when all of the following are true:

1. All 20 tests listed in §3.3 pass in CI (`cd juniper-cascor/src/tests && bash scripts/run_tests.bash`).
2. `/ws/training` broadcasts observed in staging (manual: connect a WS client and tail 60 s of events) show strictly monotonically increasing `seq` values.
3. `/api/v1/training/status` REST response includes `snapshot_seq` and `server_instance_id` fields (verified via `curl` against staging).
4. `cascor_ws_broadcast_send_duration_seconds` p95 < 100 ms in staging (baseline for Phase E work later).
5. A `resume` frame with `last_seq` N-5 after a forced disconnect successfully replays exactly 5 events in seq order.
6. A forced cascor restart followed by reconnect triggers `resume_failed{reason=server_restarted}` and the client falls back to REST snapshot successfully.
7. `cascor_ws_replay_buffer_capacity_configured == 1024` in production config; `== 256` in staging config (proves the tunable works).
8. 24-hour soak in staging with a long-running training job shows `cascor_ws_seq_gap_detected_total == 0`.
9. `CHANGELOG.md` and `docs/websocket_protocol.md` entries reviewed and merged.

Going/no-go: if criterion 8 shows any seq gap, do NOT proceed to Phase B. Investigate the gap first.

### 3.6 Rollback

1. **Hot rollback (15 min TTF)**: `git revert` the Phase A PR, redeploy cascor via blue/green. Clients with cached `server_instance_id` will observe `resume_failed{reason=server_restarted}` and refetch REST snapshot (pre-Phase-A behavior).
2. **Soft rollback (2 min TTF)**: if the issue is specifically the `_send_json` 0.5 s timeout causing false drops, set `JUNIPER_WS_SEND_TIMEOUT_SECONDS=30` (high value) as a temporary env override to restore pre-quick-fix behavior. This is not a full rollback — it preserves the seq/replay contract.
3. **Dangerous edge**: if a client was caching the old `connection_established` schema and the new field broke a parser, the fix is on the client side, not a server rollback. Document in the runbook.

### 3.7 NOT in this phase

- **Full Phase E backpressure** (per-client pump task + bounded queue + policy matrix). Only the 0.5 s quick-fix lands here. Full fix is Phase E.
- **`permessage-deflate` negotiation** (GAP-WS-17). Deferred.
- **Topology chunking** (GAP-WS-18). Deferred.
- **`seq` on `command_response`** (R1-05 §4.17). Explicitly not included; `/ws/control` has no seq namespace.
- **GAP-WS-19 re-fix** (R1-05 §4.16). Already on main — just add the regression test.
- **M-SEC-01/02/03/04/05 security controls**. Those are Phase B-pre-a/-b.
- **Multi-tenant per-session replay buffers** (R1-05 §4.13). Single buffer is sufficient for single-tenant v1.
- **Cascor client `command_id` correlation map**. That is in the SDK (Phase A-SDK).
- **Prometheus histogram for canopy-side delivery latency** (GAP-WS-24b). That is in Phase B.

---

## 4. Phase A-SDK: `juniper-cascor-client` `set_params` method

### 4.1 Goal

The `juniper-cascor-client` Python SDK exposes a new `CascorControlStream.set_params(params: dict, timeout: float = 1.0, command_id: Optional[str] = None) -> dict` method that sends a `set_params` command over an already-established `/ws/control` WebSocket and returns the `command_response` matched via `command_id`. The SDK ships independently to PyPI and does NOT queue across disconnects (fails fast per R1-05 §4.42).

### 4.2 Entry gate

- [ ] `juniper-cascor-client` main branch clean, tests green.
- [ ] Phase A-SDK does NOT depend on Phase A (cascor-server) at the SDK layer. Justification: the additive `command_id` field is safely ignored by cascor if absent on wire; cascor's echo becomes present only after Phase G tests assert it. But for downstream Phase C consumers, Phase A (cascor-server) should be in main first so the canopy adapter exercises a server that actually honors the contract. **This entry gate is therefore looser than Phase A's**: SDK can ship as soon as Round 2 accepts this plan.
- [ ] No concurrent cascor-client PR touching `control_stream.py`.

### 4.3 Deliverables checklist

SDK code changes:

- [ ] `juniper-cascor-client/juniper_cascor_client/control_stream.py` — new method signature:
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
  Behavior: generates `command_id = str(uuid.uuid4())` if absent, sends `{"type": "command", "command": "set_params", "command_id": ..., "params": ...}`, awaits the matching `command_response` via a background `_recv_task` + per-connection correlation map, returns the response dict. Raises `JuniperCascorTimeoutError` on timeout, `JuniperCascorConnectionError` on disconnect, `JuniperCascorError` on server-side error response.
- [ ] Correlation map: `_pending: Dict[str, asyncio.Future]` keyed by `command_id`.
- [ ] Background `_recv_task` started on first `set_params` call (or on connect — implementation detail); cancels cleanly on `close()` and sets exceptions on all pending futures.
- [ ] **Caller cancellation safety**: if the caller's `await set_params(...)` is cancelled, the correlation map entry is removed in `finally`. No memory leak.
- [ ] `_client_latency_ms` private field on the returned dict captures the round-trip (leading underscore = SDK-private, not wire contract).
- [ ] No retries. On timeout or error, raise — caller decides.
- [ ] Pydantic schema: `SetParamsResponse` wire model (additive, `extra="allow"` so unknown server fields don't break old SDKs).

Tests (in `juniper-cascor-client/tests/unit/`):

- [ ] `test_set_params_default_timeout_is_one_second` (R1-05 §4.1 assert).
- [ ] `test_set_params_happy_path` (mocked WS, 50 ms ack latency).
- [ ] `test_set_params_timeout_raises_typed_exception` (mocked WS, no response).
- [ ] `test_set_params_concurrent_callers_correlate_via_command_id` (R1-05 §4.2).
- [ ] `test_set_params_caller_cancellation_cleans_correlation_map` (R1-05 §4.25, mandatory Phase A gate).
- [ ] `test_set_params_fails_fast_on_disconnect` (renamed from R0-05 `test_set_params_reconnection_queue` per R1-05 §4.42).
- [ ] `test_set_params_no_retry_on_timeout` (R1-05 §4.22).
- [ ] `test_set_params_server_error_response_raises_typed_exception`.
- [ ] `test_correlation_map_bounded_at_256` (R1-02 §6.4 amplification; reject new commands with `JuniperCascorOverloadError` if map grows beyond 256).
- [ ] `test_recv_task_propagates_exception_to_all_pending_futures`.

Observability (SDK emits; consumed by canopy adapter in Phase C):

- [ ] `_client_latency_ms` field on responses (private).
- [ ] Module-level logger with `DEBUG` lines for send/receive events.

Release:

- [ ] `juniper-cascor-client/pyproject.toml` version bump to next minor (e.g., `0.5.0 → 0.6.0`).
- [ ] `CHANGELOG.md` entry.
- [ ] PyPI publish via the standard juniper-cascor-client release workflow.
- [ ] `juniper-ml/pyproject.toml` optional-extras pin bumped to the new version (follow-up PR, not Phase A gate).

### 4.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P2 | `phase-a-sdk-set-params` | `feat(sdk): CascorControlStream.set_params with command_id correlation` | S | juniper-cascor-client main |

### 4.5 Exit gate (measurable)

1. All 10 SDK tests in §4.3 pass.
2. `pip install juniper-cascor-client==<new version>` from PyPI succeeds in a fresh venv.
3. A canopy adapter draft PR can `import` and call `set_params` against a local `FakeCascorServerHarness` successfully.
4. SDK version bump visible in `juniper-cascor-client/CHANGELOG.md`.
5. `test_set_params_caller_cancellation_cleans_correlation_map` passes AND a follow-up `_pending` len gauge reads 0 after cancellation (inspected via test hook).

Going/no-go: if `test_set_params_caller_cancellation_cleans_correlation_map` is flaky on CI, do NOT ship. The R04-01 memory leak scenario is a Canopy-side OOM risk (R1-02 §9.2).

### 4.6 Rollback

1. **SDK yank from PyPI** (2 min TTF): yank the new SDK version. Downstream consumers (canopy) pin to the prior version.
2. **Flag-off rollback** (instant): Phase C's `Settings.use_websocket_set_params=False` flag default means the new SDK method is not called in production until Phase C flips the flag. Phase A-SDK merge is therefore effectively a no-op for users until Phase C acts.

### 4.7 NOT in this phase

- **Canopy adapter hot/cold split**. That is Phase C.
- **SDK-side retries**. R1-05 §4.22 — explicitly none.
- **Reconnect queueing**. R1-05 §4.42 — explicitly none.
- **Debounce logic**. R1-05 §4.24 — lives in Dash clientside callback, not SDK.
- **Cascor-side `command_id` echo**. That is validated in Phase G. Until Phase G lands, the SDK handles the absence of echo by correlating first-match-wins (graceful degrade).

---

## 5. Phase B-pre-a: read-path security (gates Phase B)

### 5.1 Goal

Close the minimum set of security holes that **exposing browser→canopy `/ws/training` traffic** opens: frame-size caps (M-SEC-03), per-IP connection caps (M-SEC-04 minimal), audit-logger skeleton (M-SEC-07 skeleton), and the "one resume per connection" replay amplification guard (R1-05 §4.12). Does **not** include CSWSH / CSRF / Origin-on-`/ws/control` — those are Phase B-pre-b and gate Phase D, not Phase B.

Additional Phase B-pre-a scope (per R1-05 §7.7 re-allocation from R0-06): Origin allowlist on **`/ws/training`** specifically, because R1-01 §4.2 establishes that cross-origin access to `/ws/training` is a live-data exfiltration vector (training metrics, topology, state) even without any command-plane exposure. **Phase B-pre-a owns `/ws/training` Origin. Phase B-pre-b owns `/ws/control` Origin + CSRF.**

### 5.2 Entry gate

- [ ] main branch clean on both cascor and canopy.
- [ ] No concurrent security-focused PR open on either repo.
- [ ] `Settings.ws_allowed_origins` and `Settings.ws_max_connections_per_ip` not already used by any other Phase's scope.
- [ ] Has the `canopy.audit` logger name been reserved? (Grep: `grep -rn "canopy.audit" juniper-canopy/`.)

### 5.3 Deliverables checklist

Code (cascor side):

- [ ] **MVS-SEC-01** (R1-01 §2.2.2): `juniper-cascor/src/api/websocket/origin.py` new module with `validate_origin(ws, allowlist: list[str]) -> bool` helper. Case-insensitive host compare, port significant, null origin rejected, empty allowlist = reject-all (fail closed).
- [ ] **MVS-SEC-02**: `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` covers exact match, case-insensitive, trailing-slash strip, null origin, port mismatch, scheme mismatch, wildcard rejection, empty allowlist.
- [ ] **MVS-SEC-03**: wire `validate_origin` into `training_stream_handler` at the pre-accept upgrade point. (Reject with `HTTPException(403)` or `ws.close(code=1008)` — implementation detail.)
- [ ] **MVS-SEC-04**: `Settings.ws_allowed_origins: list[str] = []` in `config.py` with env var `JUNIPER_WS_ALLOWED_ORIGINS`.
- [ ] **MVS-SEC-08**: `_per_ip_counts: Dict[str, int]` under `_lock` in `WebSocketManager`, increment in `connect()`, decrement in `disconnect()` `finally:` block (prevent counter leak on exception).
- [ ] **MVS-SEC-09**: `Settings.ws_max_connections_per_ip: int = 5` in `config.py`.
- [ ] **MVS-SEC-11**: `max_size=4096` on every `receive_*()` call in `training_stream.py` (inbound control frames; ping/pong only, 4 KB is plenty).

Code (canopy side):

- [ ] **MVS-SEC-05**: `juniper-canopy/src/backend/ws_security.py` new module. Copy (do NOT cross-import) the `validate_origin` helper from cascor — they are not in a shared library by design.
- [ ] **MVS-SEC-06**: wire `validate_origin` into the `/ws/training` route handler in `juniper-canopy/src/main.py` (approx line 355 per R0-02 §4.1).
- [ ] **MVS-SEC-07**: `Settings.allowed_origins` in canopy config with concrete localhost/127.0.0.1 × http/https defaults.
- [ ] **MVS-SEC-12**: `max_size=4096` on canopy's `/ws/training` receive.
- [ ] **Audit logger skeleton (R1-05 §4.14)**: new `canopy.audit` logger in `juniper-canopy/src/backend/audit.py`. JSON formatter. `TimedRotatingFileHandler` with daily rotation, 30-day retention. Scrub allowlist (no raw payloads). **No Prometheus counters yet — those land in Phase B.**
- [ ] **`close_all()` lock regression test**: even though GAP-WS-19 is already fixed on main (R1-05 §4.16), add `test_close_all_holds_lock` to cascor to catch future regressions.
- [ ] **"One resume per connection" rule**: per-connection `resume_consumed: bool` flag, second resume closes 1003. This is actually in Phase A (see §3.3) but is counted here for audit purposes because it's a security control.

Tests:

- [ ] **MVS-TEST-04**: `test_per_frame_size_limit_1009_on_ws_training` for both cascor and canopy.
- [ ] **MVS-TEST-05**: `test_per_ip_connection_cap_6th_rejected_1013`, `test_per_ip_counter_decrements_on_disconnect`, `test_per_ip_counter_decrements_on_exception` (race regression).
- [ ] **MVS-TEST-06**: `test_origin_allowlist_*` (R0-02 §7.2): accepts configured origin, rejects third party, rejects missing origin, case-insensitive host.
- [ ] **MVS-TEST-09**: `test_canopy_origin_rejection_matrix`.
- [ ] `test_audit_log_format_and_scrubbing` (R1-05 §4.14): emit an audit event, verify JSON shape + scrubbed fields.
- [ ] `test_audit_log_rotates_daily` (can be mocked time).
- [ ] `test_empty_allowlist_rejects_all_with_fail_closed`.
- [ ] `test_second_resume_closes_connection_1003` (already counted in Phase A §3.3 — cross-referenced here).

Observability:

- [ ] `canopy_ws_origin_rejected_total{origin_hash, endpoint}` counter exported (hashed origin so repeated probes from same attacker correlate without logging raw origin — R1-02 §2.3).
- [ ] `canopy_ws_oversized_frame_rejected_total{endpoint}` counter exported.
- [ ] `canopy_ws_per_ip_cap_rejected_total{endpoint}` counter exported.
- [ ] `canopy_audit_events_total{event_type}` counter exported (but only the counter — Prometheus dashboards for audit counts land in Phase B).

### 5.4 Pull request plan

Two PRs, parallelizable but B-pre-a-cascor must merge first because canopy's PR references cascor's origin helper pattern (the canopy copy is a copy, not an import).

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P3 | `phase-b-pre-a-cascor-security` | `feat(security): origin allowlist + max_size + per-IP cap on /ws/training (M-SEC-03/04; Origin half)` | C + Sec | juniper-cascor main |
| P4 | `phase-b-pre-a-canopy-security` | `feat(security): origin allowlist + max_size on /ws/training + audit logger skeleton (M-SEC-03/07 skeleton)` | Y + Sec | juniper-canopy main |

Merge order: P3 → P4. P3 can land alone without breaking anything (additive server-side guards). P4 lands as soon as P3 is in main.

### 5.5 Exit gate (measurable)

1. 14 test IDs listed in §5.3 pass (MVS-TEST-04, -05, -06, -09, plus audit-logger and fail-closed tests, plus the pre-existing `test_second_resume_closes_connection_1003`).
2. A manual cross-origin probe from `http://evil.example.com` is rejected by both cascor and canopy `/ws/training`.
3. A 65 KB frame sent to either `/ws/training` endpoint returns close code 1009.
4. 6 simultaneous connections from the same IP to cascor `/ws/training` result in the 6th being rejected with 1013.
5. Kill a cascor process mid-broadcast; per-IP counters return to zero within the `disconnect()` cleanup window.
6. `canopy_ws_origin_rejected_total` counter increments on a manual rejection test.
7. `canopy_audit_events_total{event_type="origin_rejected"}` counter increments on the same event.
8. Empty `JUNIPER_WS_ALLOWED_ORIGINS` in staging config rejects all connections (fail-closed test).
9. Audit log file appears at the expected path in staging, contains JSON-formatted entries, rotates on day boundary (verified by `ls -la` at day boundary).

Going/no-go: if the empty allowlist fails to reject (fail-open instead of fail-closed), HALT — this is a critical security defect.

### 5.6 Rollback

1. **Per-control env flag rollback** (2 min TTF): set `JUNIPER_WS_ALLOWED_ORIGINS=*` (or whatever wildcard the implementation accepts) + `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=1000` to effectively disable the guards without reverting code.
2. **Revert P4 then P3** (10 min TTF): standard `git revert` in reverse order.
3. **Audit logger disable**: set `JUNIPER_DISABLE_AUDIT_LOGGER=true` (feature flag added as part of P4) if the logger itself is causing issues.

### 5.7 NOT in this phase

- **M-SEC-02 cookie + CSRF first-frame**. That is Phase B-pre-b.
- **Origin allowlist on `/ws/control`**. That is Phase B-pre-b.
- **M-SEC-05 per-command rate limit**. That is Phase B-pre-b (gates Phase D's command plane).
- **M-SEC-10 idle timeout**. That is Phase B-pre-b.
- **M-SEC-11 adapter inbound validation**. That is Phase B-pre-b.
- **Prometheus counters for audit events**. Those land in Phase B alongside the rest of the observability wiring (R1-05 §4.14).
- **HMAC adapter auth**. That is the adapter→cascor hop, which only matters when canopy actually uses `/ws/control`. Phase B-pre-b.
- **Log injection escaping (M-SEC-07 extended, formerly M-SEC-12)**. Deferred to Phase B-pre-b because it pertains to command-plane auditing.

---

## 6. Phase B: frontend wiring + polling elimination

### 6.1 Goal

The canopy browser drains the existing `/ws/training` WebSocket stream into a bounded Dash store, renders metric chart updates via `Plotly.extendTraces`, and **stops polling `/api/metrics/history` entirely** when the WebSocket is healthy. This is the P0 win — the ~3 MB/s polling bandwidth is eliminated in staging and production. Polling REST path is kept forever as the kill-switch fallback.

This phase also wires `ws-state-buffer`, `ws-topology-buffer`, `ws-cascade-add-buffer`, `ws-connection-status` stores to their respective consumer callbacks (state panel, NetworkVisualizer minimum, badge).

### 6.2 Entry gate

- [ ] Phase A (cascor-server) merged to cascor main and deployed to staging.
- [ ] Phase B-pre-a (P3 + P4) merged to both cascor and canopy main and deployed to staging.
- [ ] 24-hour Phase A staging soak complete with `cascor_ws_seq_gap_detected_total == 0`.
- [ ] `Settings.enable_browser_ws_bridge` added to canopy config (default `False` for Phase B PR window).
- [ ] NetworkVisualizer render tech verified (first Phase B commit runs `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py` and records the answer in the PR description — R1-05 §5.1).
- [ ] Dash version verified (`grep "dash" juniper-canopy/pyproject.toml`) — R1-05 §5.3 says Option B (Interval drain) works regardless, so this is a record-only check.
- [ ] Plotly.js version verified (R1-05 §5.4) — also record-only.
- [ ] `canopy_rest_polling_bytes_per_sec` baseline measured in staging (the number you're trying to reduce by >90%).

### 6.3 Deliverables checklist

Frontend JS (files in `juniper-canopy/src/frontend/assets/`):

- [ ] **MVS-FE-01**: `ws_dash_bridge.js` new file (~200 LOC). Module-scope closure exposed as `window._juniperWsDrain`. Five `on(type, ...)` handlers for `metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`. Per-handler bounded ring buffers. Drain methods: `drainMetrics()`, `drainState()`, `drainTopology()`, `drainCascadeAdd()`, `drainCandidateProgress()`, `peekStatus()`. Ring bound enforced in the handler (not the drain callback, per R0-01 §3.2.5 / RISK-12).
- [ ] **MVS-FE-02**: edit `websocket_client.js` in place (DO NOT delete):
  - Add `onStatus()` enrichment (connected/reason/reconnectAttempt/ts).
  - Add jitter to reconnect backoff: `delay = Math.random() * Math.min(CAP, BASE * 2 ** attempt)` with `BASE=500ms`, `CAP=30s` (GAP-WS-30).
  - Capture `server_instance_id` from `connection_established`.
  - Track `seq`: monotonic check + warn on gap.
  - On reconnect, emit `resume` frame as first frame with `{last_seq, server_instance_id}`. On `resume_failed`, fall back to REST snapshot (call the existing `/api/v1/training/status` endpoint and set `server_instance_id` to the new value).
- [ ] **MVS-FE-03**: delete the parallel raw-WebSocket clientside callback in `dashboard_manager.py` at approximately lines 1490-1526 (GAP-WS-03). Leave a placeholder comment citing this proposal.
- [ ] **MVS-FE-14**: `ws_latency.js` new file (~50 LOC). Browser-side latency beacon. Records `received_at_ms - emitted_at_monotonic` per message, POSTs to `/api/ws_latency` every 60 s. Gated on `Settings.enable_ws_latency_beacon` — falls back to no-op if the endpoint returns 404. This is GAP-WS-24a (the browser emitter half).
- [ ] **rAF scaffold**: implement `_scheduleRaf` as a gated function in `ws_dash_bridge.js`: `if (window._juniperRafEnabled === true) { /* real rAF */ } else { /* noop */ }`. Default is disabled per R1-05 §4.3.

Python-side store + drain callback (files in `juniper-canopy/src/frontend/`):

- [ ] **MVS-FE-04**: `dashboard_manager.py` — add `dcc.Store(id='ws-metrics-buffer')` with drain callback firing on `fast-update-interval` tick. Callback reads `window._juniperWsDrain.drainMetrics()` and writes `{events: [...], gen: int, last_drain_ms: float}` (structured object per R1-05 §4.7).
- [ ] **MVS-FE-05**: update existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks to read from `window._juniperWsDrain.drainTopology()` / `drainState()`. Delete references to the old `window._juniper_ws_*` globals.
- [ ] **MVS-FE-06**: add `dcc.Store(id='ws-connection-status')` with drain callback that peeks `window._juniperWsDrain.peekStatus()` and emits only on change.
- [ ] **MVS-FE-07**: refactor `_update_metrics_store_handler` in `dashboard_manager.py` (approx lines 2388-2421). Read `ws-connection-status` via State, return `no_update` when connected, slow fallback to 1 Hz via `n % 10 == 0` check (R1-05 §4.4), preserve initial-load REST GET path.
- [ ] **MVS-FE-08**: rewrite `MetricsPanel.update_metrics_display()` in `components/metrics_panel.py` (approx lines 648-670) as a clientside_callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"` to initial figure layout. Add hidden `metrics-panel-figure-signal` dummy Store.
- [ ] **MVS-FE-09**: same migration for `components/candidate_metrics_panel.py`. `maxPoints=5000`.
- [ ] **MVS-FE-10**: apply the polling toggle to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. KEEP the REST paths — they are the kill switch and fallback.
- [ ] **MVS-FE-11**: NetworkVisualizer minimum wire — wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape graph update callback. DO NOT use `extendTraces` (cytoscape is not Plotly). Keep REST poll as fallback. **If grep in entry gate reveals NetworkVisualizer is actually Plotly, convert to extendTraces and absorb the extra ~1 day per R1-05 §4.5 contingency.**
- [ ] **MVS-FE-12**: connection indicator badge (GAP-WS-26). `html.Div` with clientside_callback reading `ws-connection-status` → CSS class toggling. States: connected / reconnecting / offline / demo.
- [ ] **MVS-FE-13**: demo mode (`demo_mode.py`) sets `ws-connection-status` to `{connected: true, mode: "demo"}` so polling returns `no_update` and badge shows "demo" (GAP-WS-33, RISK-08).
- [ ] **MVS-FE-15**: `/api/ws_latency` POST endpoint in `main.py`. Increments `canopy_ws_delivery_latency_ms_bucket` histogram AND the new `canopy_rest_polling_bytes_per_sec` gauge. This is GAP-WS-24b.
- [ ] **MVS-FE-16**: Phase I asset cache busting. Bump `assets_folder_snapshot` or equivalent so browsers pick up new JS without hard refresh (R1-05 §6.2 Phase I folded into Phase B).
- [ ] **Two-flag runtime check**: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge` gates the entire bridge. Default `enable_browser_ws_bridge=False` during the Phase B PR cycle (the flip-to-True PR is a separate one-line follow-up).

Cascor-side (residual Phase B work not already in Phase A):

- [ ] None at code level. All cascor-side work is in Phase A. Phase B does add the Prometheus counters for audit events that were deferred from Phase B-pre-a (R1-05 §4.14).

Observability:

- [ ] `canopy_rest_polling_bytes_per_sec` gauge exported (Python process-side; computed from REST handler byte output).
- [ ] `canopy_ws_delivery_latency_ms_bucket` histogram exported (fed by `/api/ws_latency` POST from browsers).
- [ ] `canopy_ws_active_connections` gauge exported.
- [ ] `canopy_audit_events_total{event_type}` Prometheus counter wired up (deferred from Phase B-pre-a per R1-05 §4.14).
- [ ] `canopy_ws_drain_callback_error_rate` counter exported.
- [ ] Dashboard panel "WebSocket health" showing p50/p95/p99 delivery latency per event type.
- [ ] Dashboard panel "Polling bandwidth" showing `canopy_rest_polling_bytes_per_sec` trend.

Tests:

- [ ] **MVS-TEST-08** (canopy unit): `test_ws_dash_bridge.py`:
  - `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
  - `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
  - `test_ws_connection_status_store_reflects_cascorWS_status`
  - `test_ws_metrics_buffer_drain_is_bounded` (asserts `.events` array bound)
- [ ] **MVS-TEST-10** (integration): `test_cascor_adapter_ws.py`:
  - `test_adapter_subscribes_to_metrics_and_forwards_to_normalizer`
  - `test_adapter_reconnects_after_fake_kills_connection`
  - `test_adapter_handles_resume_failed_by_fetching_snapshot`
  - `test_adapter_demo_mode_parity` (RISK-08)
- [ ] **MVS-TEST-11** (integration): `test_ws_reconnect_replay.py`:
  - `test_reconnect_replays_10_missed_events`
  - `test_reconnect_with_stale_server_instance_id_triggers_snapshot`
  - `test_snapshot_seq_bridges_no_gap`
  - `test_older_cascor_without_resume_command_triggers_fallback`
- [ ] **MVS-TEST-12** (dash_duo, e2e): `test_browser_receives_metrics.py`:
  - `test_browser_receives_metrics_event`
  - `test_chart_updates_on_each_metrics_event`
  - `test_chart_does_not_poll_when_websocket_connected`
  - `test_chart_falls_back_to_polling_on_websocket_disconnect`
  - `test_demo_mode_metrics_parity`
  - `test_ws_metrics_buffer_store_is_ring_buffer_bounded`
  - `test_connection_indicator_badge_reflects_state`
- [ ] **MVS-TEST-13** (Playwright, e2e): `test_websocket_wire.py`:
  - `test_websocket_frames_have_seq_field`
  - `test_resume_protocol_replays_missed_events`
  - `test_seq_reset_on_cascor_restart`
  - `test_plotly_extendTraces_used_not_full_figure_replace`
- [ ] **MVS-TEST-14** (Playwright, Phase H regression gate): `test_metrics_dual_format.py` — asserts `ws-metrics-buffer.events[-1]` contains BOTH flat and nested metric keys. Retained in Phase B so Phase H can defer safely.
- [ ] **MVS-TEST-15** (Playwright, the P0 proof): `test_polling_elimination.py` — measures `/api/metrics/history` request count over 60 s with WS connected and asserts zero requests after initial load.
- [ ] `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` (R1-05 §4.3 — rAF scaffolded disabled, test retargeted to drain callback; marked `latency_recording`).
- [ ] `test_fallback_polling_at_1hz_when_disconnected` (R1-05 §4.4).
- [ ] `test_network_visualizer_updates_on_ws_cascade_add` (R1-05 §4.5).
- [ ] `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` (GAP-WS-24b).
- [ ] `test_both_flags_interact_correctly` (two-flag logic: bridge enabled iff `enable_browser_ws_bridge=True AND disable_ws_bridge=False`).
- [ ] `test_audit_log_prometheus_counters` (deferred from Phase B-pre-a, R1-05 §4.14).

Runbook:

- [ ] `juniper-canopy/notes/runbooks/ws-bridge-kill.md` — how to flip `disable_ws_bridge=True` and restart. 5-minute TTF recipe.

### 6.4 Pull request plan

Three-PR sequence. Cascor-side audit-counter Prometheus PR is small and lands last; canopy drain wiring PR is the large one.

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P5 | `phase-b-cascor-audit-prom-counters` | `feat(cascor): audit-event Prometheus counters (deferred from B-pre-a)` | C | juniper-cascor main |
| P6 | `phase-b-canopy-drain-wiring` | `feat(canopy): ws_dash_bridge drain callbacks, Plotly extendTraces, connection indicator (flag off)` | Y + F | juniper-canopy main |
| P7 | `phase-b-canopy-flag-flip` | `feat(canopy): default enable_browser_ws_bridge=True after staging soak` | O + Y | juniper-canopy main (follow-up, not Phase B gate) |

Merge order: P5 → P6 → (48h staging soak) → P7.

P7 is NOT a Phase B exit gate. It is a one-line config PR that lands after Phase B is in staging for 48 h and the P0 metric is verified.

### 6.5 Exit gate (measurable)

Gates on Phase B merge and production deploy (P5 + P6):

1. All 27 tests listed in §6.3 pass.
2. `canopy_rest_polling_bytes_per_sec` in staging is **>90% lower** than the pre-Phase-B baseline (measured for 1 hour continuous post-deploy).
3. `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute.
4. "WebSocket health" dashboard panel renders p50/p95/p99 values.
5. Runbook `ws-bridge-kill.md` published and tested manually: flipping `disable_ws_bridge=True` restores pre-Phase-B REST polling behavior within 5 minutes TTF.
6. 24-hour staging soak completes with no browser memory growth exceeding 500 MB p95 (RISK-10 gate).
7. Demo mode parity test (`test_demo_mode_metrics_parity`) passes in both fast lane AND e2e lane (R1-05 §4.47).
8. Metric-format regression test (`test_metrics_dual_format`) passes — locks in Phase H contract.
9. `canopy_ws_origin_rejected_total` from Phase B-pre-a remains responsive (a test rejection increments it).
10. `Settings.enable_browser_ws_bridge=False` is the default in the merged code (flip happens in P7 after soak).

Going/no-go for P7 (the flip):

11. 48 hours in staging with `enable_browser_ws_bridge=True` manually set via env, no alerts firing.
12. `canopy_rest_polling_bytes_per_sec` sustained reduction >90% for the 48 h.
13. Browser memory p95 ≤ 500 MB over the 48 h.

### 6.6 Rollback

1. **Fastest (2 min TTF)**: env var `JUNIPER_DISABLE_WS_BRIDGE=true` on the running canopy process. Polling REST takes over instantly via the toggle in MVS-FE-07.
2. **Code flag flip (5 min TTF)**: set `Settings.enable_browser_ws_bridge=False` in config and redeploy. Equivalent to #1 but deployment-driven.
3. **Full revert (30 min TTF)**: `git revert` P6 and redeploy. Requires cache-bust invalidation because assets moved in MVS-FE-16.
4. **Browser-side emergency hatch**: add a URL query param `?ws=off` that forces the JS bridge off for a specific user (diagnostic).

### 6.7 NOT in this phase

- **Phase C `set_params`**. The WebSocket bridge is read-only in Phase B.
- **Phase D control buttons**. Buttons remain REST-POST.
- **Full rAF coalescing enabled**. Scaffold ships disabled (R1-05 §4.3).
- **Phase F heartbeat application-level ping**. Jitter lands in Phase B as part of `websocket_client.js` cleanup, but full heartbeat ping/pong contract is Phase F.
- **Phase E per-client pump task backpressure**. Only 0.5 s quick-fix from Phase A.
- **Topology chunking (GAP-WS-18)**. REST fallback handles large topologies.
- **Full M-SEC-02 CSRF flow**. Phase B-pre-b.
- **CODEOWNERS for `_normalize_metric`**. Phase H.
- **`normalize_metric` refactor**. Phase H (only the regression test lands here; refactor is deferred).
- **NetworkVisualizer deep render migration** (if cytoscape). Deferred to Phase B+1.

---

## 7. Phase B-pre-b: control-path security (gates Phase D)

### 7.1 Goal

Add the full CSWSH/CSRF protections on `/ws/control`: Origin allowlist on the control endpoint, cookie-based session + CSRF first-frame, per-command rate limit, idle timeout, adapter HMAC auth, adapter inbound validation, log-injection escaping (M-SEC-07 extended). This is everything in R0-02's §4 that Phase B-pre-a deferred because it applied only to the command plane.

This phase does NOT need to land before Phase C (set_params) in theory — the SDK already uses `/ws/control` with `X-API-Key` header auth, which works for the adapter hop — but it DOES need to land before Phase D (control buttons), because that is when the browser starts directly using `/ws/control`.

### 7.2 Entry gate

- [ ] Phase B in main (so the browser bridge is already working read-only).
- [ ] Phase A-SDK in main (so any Phase C consumer can depend on the SDK independent of Phase B-pre-b).
- [ ] Session middleware presence verified: `grep -rn "SessionMiddleware" juniper-canopy/src/` (R1-05 §5.2). If absent, budget 0.5 day extra.
- [ ] `Settings.ws_backpressure_policy` not yet set to a Phase-E value (Phase B-pre-b is before Phase E).

### 7.3 Deliverables checklist

Cookie session + CSRF (canopy-side):

- [ ] `juniper-canopy/src/main.py` adds `SessionMiddleware` (or reuses existing per §7.2 probe).
- [ ] New endpoint `/api/csrf` returns a CSRF token bound to the session (constant-time comparable via `hmac.compare_digest`).
- [ ] Dash template injects CSRF token into the WebSocket client via a data attribute (e.g., `<div id="csrf-token" data-token="..."/>`).
- [ ] `/ws/control` handler in `main.py` now requires the first frame to be `{"type": "auth", "csrf_token": "..."}` within 5 s; invalid → close 1008, absent → close 1008, expired → close 1008.
- [ ] Cookie `SameSite=Lax`, `HttpOnly`, `Secure` (in prod).
- [ ] M-SEC-06 opaque close reasons: `/ws/control` close codes use numeric codes only, no human-readable reasons in the close frame.

Origin + rate limit (cascor side):

- [ ] `/ws/control` handler validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`).
- [ ] M-SEC-05 single-bucket rate limit: 10 cmd/s leaky bucket per-connection. 11th command in 1 s → close 1013.
- [ ] M-SEC-10 idle timeout: connection idle >120 s → close 1008.
- [ ] `Settings.ws_idle_timeout_seconds: int = 120`.

Adapter (canopy-to-cascor) auth:

- [ ] Canopy adapter `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", hashlib.sha256).hexdigest()` on connect.
- [ ] First frame sent by adapter is `{"type": "auth", "csrf_token": <hmac>}`.
- [ ] Cascor `/ws/control` handler derives the same value and compares with `hmac.compare_digest`.
- [ ] Uniform code path — no `X-Juniper-Role: adapter` header special case (R1-05 §4.43).

M-SEC-11 adapter inbound validation:

- [ ] `cascor_service_adapter.py` wraps inbound frames from cascor with Pydantic model `CascorServerFrame` (`extra="allow"` because cascor may add new fields additively; reject only if the envelope shape is malformed).
- [ ] Malformed frame → log + increment `canopy_adapter_inbound_invalid_total` counter + continue.

Log injection escaping (M-SEC-07 extended, formerly M-SEC-12 per R1-05 §4.15):

- [ ] Audit logger escapes CRLF (`\r`, `\n`) and tab (`\t`) in all logged strings. Prevents log forgery via attacker-controlled fields.
- [ ] Unit test: `test_audit_log_escapes_crlf_injection`.

Tests:

- [ ] `test_csrf_required_for_websocket_first_frame`.
- [ ] `test_csrf_token_binds_to_session_constant_time_compare`.
- [ ] `test_csrf_kill_switch_works` (per R1-02 §4.4 — test the disable path too).
- [ ] `test_ws_control_origin_rejected`.
- [ ] `test_ws_control_rate_limit_11th_command_closes_1013`.
- [ ] `test_ws_control_idle_timeout_closes_1008`.
- [ ] `test_canopy_adapter_sends_hmac_csrf_token_on_connect` (R1-05 §4.43).
- [ ] `test_canopy_adapter_inbound_malformed_frame_logged_and_counted`.
- [ ] `test_audit_log_escapes_crlf_injection`.
- [ ] `test_opaque_close_reasons_no_human_readable_strings`.
- [ ] `test_session_middleware_exists_and_is_wired` (acceptance test in case §7.2 probe misses).
- [ ] `test_cascor_rejects_unknown_param_with_extra_forbid` (R1-05 §4.44).

Observability:

- [ ] `canopy_csrf_validation_failures_total` counter.
- [ ] `canopy_audit_events_total{event_type="csrf_failure"}` label added to the existing counter.
- [ ] `cascor_ws_control_rate_limit_rejected_total` counter.
- [ ] `cascor_ws_control_idle_timeout_total` counter.
- [ ] `canopy_adapter_inbound_invalid_total` counter.

### 7.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P8 | `phase-b-pre-b-cascor-control-security` | `feat(security): /ws/control origin, rate limit, idle timeout, HMAC adapter auth (M-SEC-01/01b/05/10/11)` | C + Sec | juniper-cascor main |
| P9 | `phase-b-pre-b-canopy-csrf-audit` | `feat(security): cookie session + CSRF first-frame + audit log prometheus + M-SEC-07 extended` | Y + Sec | juniper-canopy main |

Merge order: P8 → P9. P8 must land first because P9's adapter HMAC path depends on cascor accepting the new first-frame.

### 7.5 Exit gate (measurable)

1. All 12 tests listed in §7.3 pass.
2. Manual test: open `/ws/control` without first-frame CSRF auth, observe close 1008.
3. Manual test: open `/ws/control` from wrong origin, observe close 1008.
4. Manual test: send 11 commands in 900 ms, observe close 1013 on the 11th.
5. `SessionMiddleware` detected in canopy stack (via a debug endpoint or test).
6. Canopy adapter reconnects to cascor successfully after P8 + P9 deploy — HMAC handshake works.
7. `canopy_csrf_validation_failures_total` counter increments on a rejected probe.
8. 48-hour staging soak with `/ws/control` traffic shows no regression in adapter reconnect rate.

### 7.6 Rollback

1. **Env flag (2 min TTF)**: `JUNIPER_DISABLE_WS_AUTH=true` — the existing negative-sense flag (R1-05 §4.10). Restores pre-B-pre-b behavior.
2. **Per-control env flags (5 min TTF)**: `JUNIPER_WS_CSRF_REQUIRED=false`, `JUNIPER_WS_RATE_LIMIT_CMDS_PER_SEC=1000`, `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=99999`.
3. **Revert P9 then P8** (15 min TTF).

### 7.7 NOT in this phase

- **Per-command HMAC (M-SEC-02 point 3)**. R1-05 §4.11 — deferred indefinitely.
- **Per-origin handshake cooldown**. R0-02 §4.8 — R1-02 §13.10 flags it as NAT-hostile; deferred.
- **Two-bucket rate limiting**. R1-05 §4.46 — single bucket; split is a follow-up.
- **Multi-tenant per-session replay buffers**. R1-05 §4.13 — single-tenant v1.
- **Browser command buttons over WS**. That's Phase D.

---

## 8. Phase C: set_params (P2 priority per source doc)

### 8.1 Goal

Canopy adapter splits parameter updates into a "hot" set (learning rate, candidate LR, correlation threshold, pool size, max hidden units) and a "cold" set (everything else). Hot params route over `/ws/control` via `set_params` command with 1.0 s default timeout; cold params stay on REST PATCH `/api/v1/training/params`. Feature-flagged behind `Settings.use_websocket_set_params = False`. REST path is permanent and never deprecated (R1-05 §4.23).

### 8.2 Entry gate

- [ ] Phase A-SDK in main and on PyPI (canopy can `pip install` the new SDK version).
- [ ] Phase B in main and `enable_browser_ws_bridge=True` in staging.
- [ ] `juniper-ml/pyproject.toml` optional-extras pin bumped to the new cascor-client version.
- [ ] Canopy adapter's current `run_coroutine_threadsafe` usage pattern verified (R1-05 §5.5): `grep -n "run_coroutine_threadsafe" juniper-canopy/src/backend/cascor_service_adapter.py`.

### 8.3 Deliverables checklist

Canopy adapter refactor (`juniper-canopy/src/backend/cascor_service_adapter.py`):

- [ ] `_HOT_CASCOR_PARAMS: frozenset[str]` = `{learning_rate, candidate_learning_rate, correlation_threshold, candidate_pool_size, max_hidden_units, ...}` (exhaustive list per R0-04 §5.1).
- [ ] `_COLD_CASCOR_PARAMS: frozenset[str]` = the cold complement.
- [ ] `apply_params(**params)` splits inbound params → hot set → `_apply_params_hot()` over `/ws/control`; cold set → `_apply_params_cold()` over REST.
- [ ] `_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)`. On timeout or error, **unconditional fallback to REST PATCH** (R0-04 §5.1 — the REST fallback is unconditional, not "on retry after N tries").
- [ ] Unclassified keys (not in `_HOT` or `_COLD`) default to REST with WARNING log (R1-05 §4.44).
- [ ] `_control_stream_supervisor`: background task that maintains the `/ws/control` connection, reconnects on disconnect, sends HMAC first-frame (already in Phase B-pre-b; confirms supervisor uses it).
- [ ] `Settings.use_websocket_set_params: bool = False` default.
- [ ] Dash clientside callback debounce lives in the slider callback (R1-05 §4.24), not in the SDK. 250 ms debounce.
- [ ] Latency instrumentation: `canopy_set_params_latency_ms{transport, param_name}` Prometheus histogram. Transport labels: `rest`, `ws`.

Tests (canopy unit):

- [ ] `test_apply_params_routes_hot_to_ws_when_flag_on`.
- [ ] `test_apply_params_routes_hot_to_rest_when_flag_off`.
- [ ] `test_apply_params_routes_cold_to_rest_always`.
- [ ] `test_apply_params_falls_back_to_rest_on_ws_timeout`.
- [ ] `test_apply_params_falls_back_to_rest_on_ws_connection_error`.
- [ ] `test_canopy_adapter_defaults_unclassified_to_rest_with_warning` (R1-05 §4.44).
- [ ] `test_slider_debounce_250ms_collapses_rapid_updates`.
- [ ] `test_set_params_latency_histogram_exported{transport}` (both labels).
- [ ] R0-05 §4.3 Phase C routing unit tests (C1 through C13 per R0-04 §10.2).
- [ ] `test_control_stream_supervisor_reconnects_on_disconnect`.
- [ ] `test_control_stream_supervisor_sends_hmac_first_frame` (cross-check Phase B-pre-b).

Tests (canopy e2e, `dash_duo` + Playwright):

- [ ] `test_slider_drag_routes_to_ws_with_flag_on`.
- [ ] `test_slider_drag_routes_to_rest_with_flag_off`.
- [ ] `test_slider_drag_fallback_works_when_cascor_killed_mid_call`.

Documentation:

- [ ] Runbook `juniper-canopy/notes/runbooks/ws-set-params-flip.md`: how to flip `use_websocket_set_params=True`, monitor latency, revert.

### 8.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P10 | `phase-c-canopy-set-params-adapter` | `feat(canopy): set_params hot/cold split, ws transport behind flag` | Y | juniper-canopy main |

Single PR; no cascor-side change (Phase A's `command_id` echo handles that).

### 8.5 Exit gate (measurable)

1. All 14+ tests in §8.3 pass.
2. With flag off: `canopy_set_params_latency_ms_bucket{transport="rest"}` histogram has data points; `transport="ws"` is empty. (Regression check.)
3. With flag on in staging: both transport labels have data points; `transport="ws"` p95 is lower than `transport="rest"` p95 (expected improvement from R0-04 §7.1 — even if not required for go/no-go).
4. `test_set_params_concurrent_correlation` passes (R1-05 §4.29 — 2 concurrent sliders, correlation via `command_id` is correct).
5. Manual test: drag slider with flag on, observe updates arrive within 1 s in staging.
6. Manual test: kill cascor mid-drag, slider change still applies via REST fallback within 2 s.
7. Runbook `ws-set-params-flip.md` published.

Going/no-go for the flag flip PR: 7-day canary in staging with zero orphaned commands per `canopy_set_params_orphaned_total` counter (R1-02 §6.1 criterion).

### 8.6 Rollback

1. **Env flag (instant)**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`. All params route REST.
2. **Revert P10** (15 min TTF).

### 8.7 NOT in this phase

- **SDK-level retries**. R1-05 §4.22 — none.
- **SDK reconnect queue**. R1-05 §4.42 — none.
- **REST path deprecation**. R1-05 §4.23 — never.
- **Two-bucket rate limit**. Deferred follow-up.
- **Frontend control buttons over WS**. Phase D.

---

## 9. Phase D: control buttons

### 9.1 Goal

Route browser `start`/`stop`/`pause`/`resume`/`reset` training-control clicks through `/ws/control` via `window.cascorControlWS.send({command, command_id})`. REST POST at `/api/train/{command}` remains first-class forever. Per-command timeouts per source doc §7.32: `start: 10 s`, `stop/pause/resume: 2 s`, `set_params: 1 s`, `reset: 2 s`.

### 9.2 Entry gate

- [ ] Phase B-pre-b in main and deployed to production (NOT just staging). Phase D is gated on production because it directly exposes the control plane.
- [ ] 48-hour production soak of Phase B-pre-b with no CSRF-related incidents.
- [ ] Phase B in main (browser bridge exists; `window.cascorControlWS` is available).

### 9.3 Deliverables checklist

Frontend (`juniper-canopy/src/frontend/`):

- [ ] Clientside callback on each button routes to `window.cascorControlWS.send({command: "start", command_id: uuid.v4()})` (etc.) if WS connected; REST POST if not.
- [ ] Per-command client-side correlation map: on send, remember `command_id` → button; on `command_response`, match and update button state.
- [ ] Orphaned-command pending-verification UI: if no response within timeout (10 s for start, 2 s for others), fall back to REST POST with a small delay.
- [ ] Badge status shows "pending" while awaiting WS ack.

Cascor-side:

- [ ] `/ws/control` handler routes inbound `{command, command_id, ...}` to the existing REST-POST-backed handler and emits `command_response{command_id, status, error?}`.
- [ ] Per-command timeout enforcement: the cascor handler dispatches commands asynchronously with an `asyncio.wait_for(..., timeout=<per-command>)`.
- [ ] Command whitelist: `start`, `stop`, `pause`, `resume`, `reset`, `set_params`. Unknown commands → `command_response{status: "error", code: "unknown_command"}`.

Tests:

- [ ] `test_csrf_required_for_websocket_start` (R1-01 §3.2 acceptance).
- [ ] `test_start_button_ws_path_happy`.
- [ ] `test_start_button_fallback_to_rest_on_ws_disconnect`.
- [ ] `test_stop_command_ws_path_happy`.
- [ ] `test_per_command_timeout_start_10s`.
- [ ] `test_per_command_timeout_stop_2s`.
- [ ] `test_unknown_command_rejected`.
- [ ] `test_command_id_echoed_in_response` (R1-05 §4.2).
- [ ] `test_orphaned_command_falls_back_to_rest_after_timeout`.

Observability:

- [ ] `canopy_training_control_command_latency_ms{command, transport}` histogram.
- [ ] `canopy_training_control_orphaned_total{command}` counter.
- [ ] `cascor_ws_control_command_received_total{command}` counter.

### 9.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P11 | `phase-d-cascor-control-commands` | `feat(cascor): /ws/control command dispatch + per-command timeouts` | C | juniper-cascor main |
| P12 | `phase-d-canopy-button-ws-routing` | `feat(canopy): training-control buttons route via /ws/control with REST fallback` | F + Y | juniper-canopy main |

Merge order: P11 → P12.

### 9.5 Exit gate (measurable)

1. All 9 tests in §9.3 pass.
2. Manual test: click Start with WS connected, observe training state within 10 s.
3. Manual test: kill cascor before click, click Start, observe REST fallback succeeds.
4. Manual test: click Start with wrong CSRF, observe 1008 close (regression of Phase B-pre-b).
5. `canopy_training_control_orphaned_total == 0` after 24 h of staging traffic.

### 9.6 Rollback

1. **Env flag**: `JUNIPER_CANOPY_BUTTONS_USE_WS=false`. All buttons route REST (pre-Phase-D behavior).
2. **Revert P12 then P11** (20 min TTF).

### 9.7 NOT in this phase

- **Full `permessage-deflate` negotiation**. Deferred.
- **`set_params` routing** (that's Phase C).
- **Two-bucket rate limit**. Deferred follow-up.

---

## 10. Phase E: backpressure + disconnection full fix

### 10.1 Goal

Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded per-client queues + backpressure policy matrix. Default policy: `drop_oldest_progress_only` (R1-05 §4.36). Alternative policies (`block`, `close_slow`) remain opt-in via `Settings.ws_backpressure_policy`.

### 10.2 Entry gate

- [ ] Phase A in main (the 0.5 s quick-fix is the fallback if Phase E rolls back).
- [ ] No outstanding `cascor_ws_broadcast_send_duration_seconds` p95 alerts.

### 10.3 Deliverables checklist

Cascor side:

- [ ] Per-client `asyncio.Queue` bounded at 256 messages (configurable via `Settings.ws_per_client_queue_size`).
- [ ] Per-client `_pump_task` created on connect, cancelled on disconnect.
- [ ] Policy dispatch:
  - `drop_oldest_progress_only` (default): drop oldest progress events (metrics, candidate_progress); close 1013 for state-bearing events (state, topology, cascade_add, connection_established).
  - `block`: synchronously block broadcast until queue drains (old behavior).
  - `close_slow`: close 1008 if queue full for >5 s.
- [ ] `Settings.ws_backpressure_policy: str = "drop_oldest_progress_only"`.
- [ ] Metrics: `cascor_ws_dropped_messages_total{policy, reason}`, `cascor_ws_per_client_queue_depth_histogram`.

Tests:

- [ ] `test_default_backpressure_policy_drops_oldest_for_progress` (R1-05 §4.36).
- [ ] `test_block_policy_still_works_when_opted_in`.
- [ ] `test_close_slow_policy_closes_stalled_clients`.
- [ ] `test_slow_client_does_not_block_fast_clients`.
- [ ] `test_terminal_state_events_not_dropped_under_drop_oldest_progress`.

### 10.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P13 | `phase-e-cascor-backpressure-pump-tasks` | `feat(cascor): per-client pump tasks + bounded queues + policy matrix` | C | juniper-cascor main |

### 10.5 Exit gate (measurable)

1. All 5 tests in §10.3 pass.
2. Load test: 50 clients, 1 slow client with 2 s artificial delay, 49 fast clients receive all events within 200 ms p95.
3. `cascor_ws_dropped_messages_total{policy="drop_oldest_progress_only", reason="queue_full"}` visible after load test.
4. `cascor_ws_broadcast_send_duration_seconds_bucket` p95 stays under 50 ms during load test.

### 10.6 Rollback

1. **Env flag**: `JUNIPER_WS_BACKPRESSURE_POLICY=block` (2 min TTF). Old behavior restored.
2. **Revert P13** (10 min TTF).

### 10.7 NOT in this phase

- **`permessage-deflate`**. Deferred.
- **Multi-tenant per-session queues**. Single-tenant v1.

---

## 11. Phase F: heartbeat + reconnect jitter

### 11.1 Goal

Add application-level `ping`/`pong` heartbeat to detect TCP half-open on `/ws/training` and `/ws/control` faster than the uvicorn framework level. Reconnect backoff already has jitter from Phase B (GAP-WS-30). This phase adds the heartbeat contract and optionally lifts the 10-attempt reconnect cap (GAP-WS-31) — R1-05 §6.2 Phase F includes jitter formula refinement.

### 11.2 Entry gate

- [ ] Phase B in main (jitter already landed there).
- [ ] `websocket_client.js` in its Phase B state.

### 11.3 Deliverables checklist

- [ ] Cascor `/ws/training` and `/ws/control` emit `ping` every 30 s (application-level, JSON `{"type": "ping", "ts": <float>}`); client responds with `pong`.
- [ ] JS `websocket_client.js` replies `pong` within 5 s.
- [ ] Dead-connection detection: if `pong` not received within 10 s of `ping`, close with 1006.
- [ ] GAP-WS-31: lift 10-attempt reconnect cap to unlimited, but with a 60 s max interval once cap is reached.
- [ ] Jitter formula explicit: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))`.

Tests:

- [ ] `test_heartbeat_ping_pong_reciprocity`.
- [ ] `test_dead_connection_detected_via_missing_pong`.
- [ ] `test_reconnect_attempt_uncapped`.
- [ ] `test_jitter_formula_no_nan_delay` (R1-02 §9.9 regression — prevent NaN from breaking reconnect).

### 11.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P14 | `phase-f-heartbeat-jitter` | `feat(ws): application-level heartbeat, uncapped reconnect, jitter formula` | C + F | juniper-cascor + juniper-canopy main |

Two repos in one named phase; split into two PRs inside the branch family if reviewer prefers.

### 11.5 Exit gate (measurable)

1. All 4 tests pass.
2. Manual test: put client behind a firewall that drops packets silently; dead connection detected within 40 s (30 + 10).
3. Staging soak 48 h: no NaN delays in JS console; no reconnect storms.

### 11.6 Rollback

1. **Revert P14** (10 min TTF).
2. **JS-only hotfix**: push a cache-busted `websocket_client.js` with the old jitter formula.

### 11.7 NOT in this phase

- **Custom `ping` schedule override** (nice-to-have).
- **Per-endpoint ping intervals** (default 30 s suffices).

---

## 12. Phase G: end-to-end correctness (cascor set_params integration tests)

### 12.1 Goal

Add cascor-side integration tests that exercise `/ws/control` `set_params` via FastAPI `TestClient.websocket_connect()` (no SDK dependency). Asserts the wire contract: `command_id` echo, whitelist filtering, per-frame size cap, concurrent correlation, epoch-boundary application, Origin regression, rate-limit regression.

### 12.2 Entry gate

- [ ] Phase A in main (cascor `/ws/control` already handles `command_id` echo).
- [ ] Phase B-pre-b in main (Origin + rate-limit guards exist to regression-test).

### 12.3 Deliverables checklist

Tests (`juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`):

- [ ] `test_set_params_via_websocket_happy_path`.
- [ ] `test_set_params_whitelist_filters_unknown_keys`.
- [ ] `test_set_params_init_output_weights_literal_validation` (rejects `"random; rm -rf /"`).
- [ ] `test_set_params_oversized_frame_rejected` (64 KB cap — in fact we reject at 4 KB per Phase B-pre-a, but cascor-side cap on control-plane is likely larger).
- [ ] `test_set_params_no_network_returns_error`.
- [ ] `test_unknown_command_returns_error` (GAP-WS-22 regression).
- [ ] `test_malformed_json_closes_with_1003` (GAP-WS-22 regression).
- [ ] `test_set_params_origin_rejected` (M-SEC-01b regression).
- [ ] `test_set_params_unauthenticated_rejected` (X-API-Key regression).
- [ ] `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05 regression).
- [ ] `test_set_params_bad_init_output_weights_literal_rejected`.
- [ ] `test_set_params_concurrent_command_response_correlation` (R1-05 §4.29 — 2 clients, echo routing correct).
- [ ] `test_set_params_during_training_applies_on_next_epoch_boundary` (R1-05 §4.29 — ack-vs-effect distinction).
- [ ] `test_set_params_echoes_command_id` (R1-05 §4.2 — cascor echoes the field when present, omits when absent).
- [ ] `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 — already in Phase A §3.3; cross-referenced here).

Contract-lane tests (R1-05 §4.34):

- [ ] `test_fake_cascor_message_schema_parity` (R1-05 §4.30) — lives in `juniper-canopy/src/tests/unit/test_cascor_message_contract.py` but is run in both repos' `contract` lane.

### 12.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P15 | `phase-g-cascor-set-params-integration` | `test(cascor): /ws/control set_params integration suite + contract lane` | C | juniper-cascor main |

### 12.5 Exit gate (measurable)

1. All 15 tests pass.
2. `pytest -m contract` lane runs green in both cascor and canopy CI.

### 12.6 Rollback

n/a (test-only).

### 12.7 NOT in this phase

- **SDK-level integration tests**. Those are in Phase A-SDK.

---

## 13. Phase H: nested-flat metric format audit + regression gate

### 13.1 Goal

Lock in the dual metric format contract (flat keys and nested keys both present on `metrics` events) with a regression test and a CODEOWNERS entry preventing accidental breakage. Document every consumer of `_normalize_metric` output. This phase does NOT refactor `_normalize_metric`; it only builds the regression gate. Refactoring is a follow-up gated on the audit's findings.

### 13.2 Entry gate

- [ ] Phase B in main (MVS-TEST-14 `test_metrics_dual_format` regression test already landed).
- [ ] CODEOWNERS file present in `juniper-canopy/.github/CODEOWNERS`.

### 13.3 Deliverables checklist

- [ ] Regression test `test_normalize_metric_produces_dual_format` lives in `juniper-canopy/src/tests/unit/test_normalize_metric.py` with explicit assertions for BOTH nested (`{"training": {"loss": 0.5}}`) AND flat (`{"training.loss": 0.5}`) keys on every output.
- [ ] Consumer audit document `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` enumerating every consumer of `_normalize_metric` output: frontend `MetricsPanel`, `CandidateMetricsPanel`, Prometheus `/api/metrics`, WebSocket drain, debug logger, test fixtures.
- [ ] CODEOWNERS entry: `juniper-canopy/src/backend/normalize_metric.py @<project-lead>` and `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>`.
- [ ] `.github/CODEOWNERS` branch protection rule updated to require review from the listed owners.

Tests:

- [ ] `test_normalize_metric_produces_dual_format` (repeat of Phase B test, re-run here).
- [ ] `test_normalize_metric_nested_format_unchanged_since_phase_h`.
- [ ] `test_normalize_metric_flat_format_unchanged_since_phase_h`.

### 13.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P16 | `phase-h-normalize-metric-audit` | `docs(audit): normalize_metric consumer audit + CODEOWNERS rule + regression gate` | Y | juniper-canopy main |

### 13.5 Exit gate (measurable)

1. Regression tests pass.
2. CODEOWNERS rule enforced via GitHub branch protection (verified by opening a test PR that touches `normalize_metric.py` without the owner's review — it must block).
3. Consumer audit document reviewed and merged.

### 13.6 Rollback

1. **Revert P16** (10 min TTF). CODEOWNERS rule disappears.
2. **Per-file exemption**: if CODEOWNERS blocks an urgent fix, admin override via GitHub settings (documented in the runbook).

### 13.7 NOT in this phase

- **`_normalize_metric` refactor** (R1-02 §7.5 — test-only phase; refactor is a follow-up that re-runs this scenario analysis first).
- **Removal of either nested or flat format** (never, without a new formal migration plan).

---

## 14. Phase I: asset cache busting

### 14.1 Goal

Ensure browsers pick up new `websocket_client.js` + `ws_dash_bridge.js` without requiring a hard refresh. This phase is **FOLDED INTO Phase B** per R1-05 §6.2 and R1-01 §2.3 — it does not ship as a standalone phase. This section exists for documentation continuity and for rollback reference.

### 14.2 Entry gate

Folded into Phase B; no independent entry gate.

### 14.3 Deliverables checklist

Already listed as MVS-FE-16 under §6.3. Summary:

- [ ] `assets_folder_snapshot` or equivalent bump in canopy's Dash configuration.
- [ ] Verify via browser devtools that the JS URL includes a cache-bust query parameter that changes on deploy.

### 14.4 Pull request plan

Folded into P6 (Phase B canopy drain wiring).

### 14.5 Exit gate (measurable)

Covered by Phase B exit gate criterion 4 ("Runbook `ws-bridge-kill.md` published and tested manually: flipping `disable_ws_bridge=True` restores pre-Phase-B REST polling behavior within 5 minutes TTF") — the runbook verifies cache bust indirectly because the flip requires the new JS to be picked up.

### 14.6 Rollback

Revert the cache-bust commit in P6. Browsers may see stale JS briefly (usually harmless).

### 14.7 NOT in this phase

n/a — folded.

---

## 15. Cross-phase deliverables

### 15.1 Observability artifacts (per phase)

Every phase must land its observability before or alongside the behavior change (R1-02 §1.2 safety principle 1: observability before behavior change). The below table enumerates all new metrics and the phase that must ship them.

| Metric name | Type | Phase | Purpose |
|---|---|---|---|
| `cascor_ws_broadcast_send_duration_seconds` | histogram | A | Detect slow clients; Phase E tuning signal |
| `cascor_ws_replay_buffer_occupancy` | gauge | A | Replay buffer fill rate |
| `cascor_ws_replay_buffer_capacity_configured` | gauge | A | Operational tunable visibility |
| `cascor_ws_resume_replayed_events` | histogram | A | Resume trigger frequency |
| `cascor_ws_resume_failed_total{reason}` | counter | A | Diagnose resume failures |
| `cascor_ws_seq_gap_detected_total` | counter | A | Should always be 0; alert if not |
| `canopy_ws_origin_rejected_total{origin_hash, endpoint}` | counter | B-pre-a | CSWSH probe correlation |
| `canopy_ws_oversized_frame_rejected_total{endpoint}` | counter | B-pre-a | DoS detection |
| `canopy_ws_per_ip_cap_rejected_total{endpoint}` | counter | B-pre-a | Flood detection |
| `canopy_audit_events_total{event_type}` | counter | B-pre-a (counter) + B (Prom hookup) | Audit traffic volume |
| `canopy_rest_polling_bytes_per_sec` | gauge | B | P0 win signal |
| `canopy_ws_delivery_latency_ms_bucket` | histogram | B | SLO signal |
| `canopy_ws_active_connections` | gauge | B | Capacity signal |
| `canopy_ws_drain_callback_error_rate` | counter | B | Debug signal |
| `canopy_csrf_validation_failures_total` | counter | B-pre-b | Security signal |
| `cascor_ws_control_rate_limit_rejected_total` | counter | B-pre-b | Security signal |
| `cascor_ws_control_idle_timeout_total` | counter | B-pre-b | Hygiene signal |
| `canopy_adapter_inbound_invalid_total` | counter | B-pre-b | Contract drift signal |
| `canopy_set_params_latency_ms{transport, param_name}` | histogram | C | A/B measurement |
| `canopy_set_params_orphaned_total{command}` | counter | C | Correlation health |
| `canopy_training_control_command_latency_ms{command, transport}` | histogram | D | Button latency SLO |
| `canopy_training_control_orphaned_total{command}` | counter | D | Button health |
| `cascor_ws_control_command_received_total{command}` | counter | D | Throughput |
| `cascor_ws_dropped_messages_total{policy, reason}` | counter | E | Drop visibility |
| `cascor_ws_per_client_queue_depth_histogram` | histogram | E | Backpressure signal |

### 15.2 Test artifacts (per phase)

| Phase | Unit tests | Integration | E2E (dash_duo + Playwright) | Contract |
|---|---:|---:|---:|---:|
| A (cascor-server) | 20 | — | — | 1 (`test_ws_control_command_response_has_no_seq`) |
| A-SDK | 10 | — | — | — |
| B-pre-a | 14 | — | — | — |
| B | 6 unit + 8 integration + 10 e2e | — | (shown left) | 1 (`test_fake_cascor_message_schema_parity`, shared with G) |
| B-pre-b | 12 | — | — | — |
| C | 14 | 3 | 3 | — |
| D | 9 | — | 3 | — |
| E | 5 | — | — | — |
| F | 4 | — | — | — |
| G | — | 15 | — | 1 |
| H | 3 | — | — | — |
| **Total** | **97** | **18** | **16** | **3** |

`pytest -m contract` runs the 3 contract tests on every PR as the fast gate. `pytest -m latency_recording` runs latency-recording tests in CI without strict thresholds.

### 15.3 Documentation artifacts (per phase)

| Phase | Document | Purpose |
|---|---|---|
| A | `juniper-cascor/docs/websocket_protocol.md` (§ seq/replay/resume) | Canonical wire contract |
| A | `juniper-cascor/CHANGELOG.md` entry | Release notes |
| A-SDK | `juniper-cascor-client/CHANGELOG.md` entry | PyPI release notes |
| B-pre-a | Ops note: fail-closed allowlist semantics | Operator hazard brief |
| B | `juniper-canopy/notes/runbooks/ws-bridge-kill.md` | 5-min TTF recipe |
| B | "WebSocket health" Prometheus dashboard JSON | Observability artifact |
| B | "Polling bandwidth" Prometheus dashboard JSON | P0 win trend |
| B-pre-b | Runbook: CSRF flow + session middleware | Security onboarding |
| C | `juniper-canopy/notes/runbooks/ws-set-params-flip.md` | Flag-flip recipe |
| D | Runbook: control-button WS path | Button ops |
| E | Runbook: backpressure policy selection | Policy decision tree |
| F | n/a | Jitter formula in code comments |
| G | n/a | Test suite itself is the artifact |
| H | `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` | Consumer inventory |
| H | `juniper-canopy/.github/CODEOWNERS` entry | Enforcement |

---

## 16. Cross-repo merge sequence

Full ordered PR list, flattened across cascor / cascor-client / canopy:

| Order | PR ID | Branch | Repo | Phase | Blocking next? |
|---:|---|---|---|---|---|
| 1 | P2 | `phase-a-sdk-set-params` | juniper-cascor-client | A-SDK | Yes (PyPI publish) |
| 2 | P1 | `phase-0-cascor-seq-replay-resume` | juniper-cascor | A | Yes (Phase B prereq) |
| 3 | P3 | `phase-b-pre-a-cascor-security` | juniper-cascor | B-pre-a | Yes (P4 references) |
| 4 | P4 | `phase-b-pre-a-canopy-security` | juniper-canopy | B-pre-a | Yes (Phase B prereq) |
| 5 | P5 | `phase-b-cascor-audit-prom-counters` | juniper-cascor | B | No |
| 6 | P6 | `phase-b-canopy-drain-wiring` | juniper-canopy | B | Yes (Phase C prereq) |
| 7 | — | — | — | — | **48-hour staging soak** |
| 8 | P7 | `phase-b-canopy-flag-flip` | juniper-canopy | B | Yes (Phase C iterates on flag=on) |
| 9 | P15 | `phase-g-cascor-set-params-integration` | juniper-cascor | G | No (parallel to C) |
| 10 | P8 | `phase-b-pre-b-cascor-control-security` | juniper-cascor | B-pre-b | Yes (P9 and Phase D) |
| 11 | P9 | `phase-b-pre-b-canopy-csrf-audit` | juniper-canopy | B-pre-b | Yes (Phase D prereq) |
| 12 | P10 | `phase-c-canopy-set-params-adapter` | juniper-canopy | C | No (independent of D) |
| 13 | — | — | — | — | **48-hour production soak of B-pre-b** |
| 14 | P11 | `phase-d-cascor-control-commands` | juniper-cascor | D | Yes (P12 depends) |
| 15 | P12 | `phase-d-canopy-button-ws-routing` | juniper-canopy | D | No |
| 16 | P13 | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor | E | No |
| 17 | P14 | `phase-f-heartbeat-jitter` | juniper-cascor + juniper-canopy | F | No |
| 18 | P16 | `phase-h-normalize-metric-audit` | juniper-canopy | H | No |

**Critical path**: P2 → P1 → P3 → P4 → P6 → (soak) → P7 → P10. That's the "ship the P0 win" spine.

**Parallel lanes**:
- Phase A-SDK (P2) parallelizes with Phase A (P1) and Phase B-pre-a (P3/P4).
- Phase G (P15) parallelizes with Phase C (P10).
- Phase E (P13), Phase F (P14), Phase H (P16) are all independent — can land in any order after B is in production.

**Production deploys**:
- After step 6 (P6 to main): deploy to staging. DO NOT deploy to production until step 8 (P7 flag flip) is done.
- Step 8 is a production deploy.
- Step 11 is a staging deploy, then a 48h soak, then production.
- Step 15 is a staging deploy, then a 48h soak, then production.

---

## 17. Effort summary table

| Phase | Optimistic (days) | Expected (days) | Pessimistic (days) | Notes |
|---|---:|---:|---:|---|
| A (cascor-server) | 1.5 | 2.0 | 3.0 | Pessimistic if `_pending_connections` design hits async race bugs |
| A-SDK | 0.5 | 1.0 | 1.5 | Pessimistic if correlation map bounding logic needs iteration |
| B-pre-a | 0.5 | 1.0 | 1.5 | Pessimistic if audit logger integration surfaces logger name collisions |
| B | 3.0 | 4.0 | 5.0 | Pessimistic if NetworkVisualizer turns out to be Plotly (+1 day) |
| B-pre-b | 1.0 | 1.5 | 2.0 | Pessimistic if SessionMiddleware doesn't exist (+0.5 day) |
| C | 1.5 | 2.0 | 3.0 | Pessimistic if concurrent-correlation test surfaces race bugs |
| D | 0.75 | 1.0 | 1.5 | Pessimistic if orphaned-command UI state management is finicky |
| E | 0.75 | 1.0 | 1.5 | Pessimistic if per-client queue tuning surfaces load issues |
| F | 0.25 | 0.5 | 1.0 | Small phase; low variance |
| G | 0.25 | 0.5 | 0.75 | Tests only; low variance |
| H | 0.5 | 1.0 | 1.5 | Audit document can grow |
| I | 0.1 | 0.25 | 0.5 | Folded into B; counted separately for rollback |
| **Total** | **10.6** | **15.75** | **22.25** | Expected 15.75 vs R1-05's 13.5 — see §17.1 |

### 17.1 Effort delta vs R1-05 §4.40

R1-05 budgets 13.5 days; this proposal's expected is 15.75. The delta is +2.25 days, distributed as:

- +0.5 day on Phase A (R1-05 §3.3 two-phase registration estimated separately from resume handler; R2-02 bundles).
- +0.5 day on Phase B (NetworkVisualizer minimum wire added; R1-05 §4.5 assumed zero-cost deferral).
- +0.5 day on Phase C (R0-04 estimated 2 days; R2-02 adds 0.5 day for the HMAC first-frame adapter wiring).
- +0.25 day on Phase B-pre-a (audit logger skeleton in B-pre-a per R1-05 §7.7 split).
- +0.5 day on Phase B-pre-b (HMAC adapter auth end-to-end wiring).

Operator may optimize toward 13.5 by executing phases strictly in parallel and deferring NetworkVisualizer wire to Phase B+1. R2-02's number is the **expected** value assuming prudent serialization and audit-trail completeness.

### 17.2 Calendar translation

Expected 15.75 engineering days × single-developer lane → ~3 weeks one-person calendar, or ~4.5 weeks with 48-hour soak windows between B, B-pre-b, D stages. Matches R1-05 §4.40's "~4.5 weeks" target.

---

## 18. Disagreements with R1 inputs

Places where R2-02 deviates from the R1 corpus, with justification. Each item names the R1 proposal(s) it disagrees with.

### 18.1 Replay buffer default — R2-02 sides with R1-05 (1024), NOT R1-02 (256)

R1-02 §12.1 argues 256 for snapshot-path hygiene. R1-05 §1 (as I read it) keeps 1024 as production default. R0-03 originally wanted 1024.

**R2-02 resolution**: production default = 1024, configurable. Dev/staging can set `JUNIPER_WS_REPLAY_BUFFER_SIZE=256` to serve R1-02's testing hygiene argument without compromising production resilience. R1-02's concern is real but addressable via configuration.

**Justification**: (reversibility) configuration satisfies both. (safety) 256 would cause `resume_failed` more often under legitimate slow-client conditions, which is a small production regression. (operational simplicity) one code path, one default, one tunable.

### 18.2 Phase B includes NetworkVisualizer minimum wire

R1-01 §3.3 and R1-04 D7 defer NetworkVisualizer entirely to Phase B+1. R1-05 §4.5 resolved it to "minimum WS wiring in Phase B, deep render migration deferred contingent on render tech." R2-02 matches R1-05.

**Justification**: R1-05's contingent resolution is the safest. The 0.5-day minimum-wire cost is a known quantity; deferring the full 1-2 day render migration is contingent on the first-commit verification.

### 18.3 Audit logger Prometheus counters ship in Phase B, not Phase B-pre-a

R1-02 §2.3 puts audit logger Prometheus counters in the security metric table, implying Phase B-pre-a. R1-05 §7.7 re-allocates the Prometheus hookup to Phase B because "security ≠ observability instrumentation cadence."

**R2-02 resolution**: adopts R1-05 §7.7 — the logger itself (JSON formatter + rotating handler + scrub allowlist) lives in B-pre-a; the Prometheus counter hookup lives in B.

**Justification**: (operational simplicity) keeps B-pre-a small and shippable. (reversibility) the Prometheus hookup is a few lines; landing it alongside all the other Phase B metrics is simpler.

### 18.4 R2-02 adds both `enable_browser_ws_bridge` and `disable_ws_bridge`

R1-01 proposed only `disable_ws_bridge`. R1-02 §5.2 proposed a single feature flag. R1-05 §4.45 introduces the two-flag design. R2-02 adopts R1-05's resolution.

**Justification**: R1-05 is correct that the flags serve different purposes: `enable_browser_ws_bridge` is a dev-time "this code is landing but not yet live" signal; `disable_ws_bridge` is a permanent ops kill switch. Treating them as one flag conflates two distinct states.

### 18.5 Phase E default stays `drop_oldest_progress_only`

R1-02 §12.3 keeps `block` as safer; R1-05 §4.36 overrides to `drop_oldest_progress_only`. R2-02 adopts R1-05.

**Justification**: R1-05's explicit override of the source doc is defensible; the RISK-04 medium/medium severity justifies the default flip. R1-02's safer-default argument is served by the policy being configurable — operators can revert to `block` with one env var.

### 18.6 Phase A 24-hour staging soak, not R1-02's 72-hour

R1-02 §13.3 argues 72 hours for Phase A-server staging. R2-02 keeps 24 hours (source doc standard) for Phase A and reserves 48 hours for Phase B (the high-visibility one).

**Justification**: (operational simplicity) Phase A's additive-field contract means the blast radius is low — clients that don't know about `seq` keep working. A 72-hour soak for additive server plumbing is overkill. Phase B, which actually changes user-visible behavior, keeps 48 hours. This is a calibration tradeoff.

### 18.7 Phase H does NOT refactor `_normalize_metric`

R1-02 §7.5 is a "test-only Phase H" (refactor deferred). R1-03 is ambiguous. R2-02 matches R1-02 explicitly: Phase H ships the regression test and consumer audit but does NOT refactor. Any refactor is a new follow-up phase that must re-run the scenario analysis first.

**Justification**: RISK-01 High/Medium severity. Refactoring `_normalize_metric` is one of the most dangerous operations in the whole migration. The regression gate must be hardened first.

### 18.8 Phase D entry gate requires production soak of B-pre-b, not just main merge

R1-04 §11.1 lists "B-pre in prod" as entry; R1-02 elevates to 48-hour soak. R2-02 adopts the 48-hour production soak.

**Justification**: (safety) Phase D is the first phase that directly exposes the browser to the control plane over WS. The CSRF + rate-limit guards MUST have survived a production soak before the browser starts hammering them.

### 18.9 SDK version is a minor bump, not patch

R1-04 §13 implies patch. R2-02 makes it a minor bump because `set_params` is a new public method.

**Justification**: (operational simplicity) semver hygiene — new public methods warrant a minor.

---

## 19. Self-audit log

### 19.1 Pass 1 verification

- Read R1-05 in full (the settled-positions doc).
- Read R1-01 §§1-5 in full (phase structure and deliverables).
- Read R1-02 index + disagreement section (§12, §13) to understand safety-first positions.
- Read R1-03 index + phase effort estimates + §1 (executive summary).
- Read R1-04 index + cross-repo coordination summary (§13).
- Built the phase index (§2).
- Built phase contracts §3 through §14 with six-question structure for each.
- Built cross-phase deliverables (§15), merge sequence (§16), effort summary (§17).
- Wrote §18 disagreements.

### 19.2 Pass 2 corrections applied

1. **Initially used `request_id` in one Phase A-SDK deliverable**. Caught on re-read; renamed to `command_id` throughout R2-02 per R1-05 §4.2.

2. **Initially placed NetworkVisualizer wire in Phase B+1**. Corrected to Phase B minimum-wire + deferred-render-migration-contingent, per R1-05 §4.5. Added the first-commit verification requirement.

3. **Initially placed the audit logger Prometheus counters in Phase B-pre-a**. Corrected to Phase B per R1-05 §7.7; logger skeleton alone is B-pre-a.

4. **Initially omitted the two-flag browser bridge logic in Phase B deliverables**. Added MVS-FE-13+1 test and §1.2 flag-name section.

5. **Initially had `seq` on `command_response`**. Corrected throughout per R1-05 §4.17. Added `test_ws_control_command_response_has_no_seq` to Phase A deliverables.

6. **Initially included GAP-WS-19 re-fix in Phase B-pre-a deliverables**. Removed per R1-05 §4.16; kept only the `test_close_all_holds_lock` regression test.

7. **Initially had replay buffer default at 256** after reading R1-02. Reversed to 1024 (configurable) after re-reading R1-05 §1 and R0-03. Added §18.1 disagreement note.

8. **Initially scheduled Phase C adapter HMAC first-frame separately from Phase B-pre-b**. Consolidated into B-pre-b (where HMAC lives) per R1-05 §4.43. Phase C's only HMAC interaction is the supervisor invoking the already-wired auth path.

9. **Initially left Phase I as a standalone phase**. Folded into Phase B per R1-05 §6.2 and R1-01 §2.3, but kept §14 as a documentation stub with forward-reference to Phase B §6.3.

10. **Initially budgeted Phase B at 4 days matching R1-05**. Raised to 4 days expected + 5 days pessimistic after re-reading R1-01's full 16-step MVS-FE-NN list. The pessimistic case handles the NetworkVisualizer-is-Plotly contingency.

11. **Initially omitted the "One resume per connection" rule**. R1-05 §4.12 makes it explicit; added to Phase A §3.3 deliverables and Phase B-pre-a §5.3 (with cross-reference).

12. **Initially missed the contract-test marker**. Added per R1-05 §4.34 to §15.2 and Phase G §12.3.

13. **Initially did not split Phase A vs Phase A-SDK into separate entries in the phase index**. Separated for clarity; they are parallel but independent. Phase A-SDK is effectively a cascor-client PR, not a cascor PR.

14. **Initially budgeted Phase B-pre-b at 1 day**. Raised to 1.5 days after realizing the cookie session middleware + CSRF endpoint + template token injection + rate limit + idle timeout + adapter HMAC is a lot of discrete pieces, each small. Pessimistic 2 days covers the §5.2 session-middleware-missing contingency.

15. **Initially placed rate limit in Phase B-pre-a**. Moved to Phase B-pre-b because it applies to the command plane, not the read plane. R1-05 §4.46 single-bucket settled.

16. **Initially had Phase E default as unspecified**. Set to `drop_oldest_progress_only` per R1-05 §4.36; added to §1.2 and §10.3.

17. **Initially did not include the Prometheus metrics table**. Added §15.1 after realizing R1-02's safety principle 1 ("observability before behavior change") required explicit per-phase metric allocation.

18. **Initially did not include the CODEOWNERS branch protection verification step** in Phase H. Added per R1-05 §4.41 and R1-02 §13.11.

19. **Initially had Phase G as "optional"**. Upgraded to mandatory after re-reading R1-02 §7.4 ("not optional") and R1-05 §4.26 (Phase C routing tests are mandatory).

20. **Initially missed that `test_set_params_caller_cancellation` is elevated to mandatory Phase A-SDK gate**. Added per R1-05 §4.25.

### 19.3 Self-audit checklist

- [x] Every phase has a goal, entry gate, deliverables, PR plan, exit gate, rollback, and "NOT in this phase" section.
- [x] Every PR has a branch name.
- [x] Every PR has a suggested merge order (§16).
- [x] Every exit criterion is measurable (has a test name or metric threshold).
- [x] Every deliverable lists concrete file paths where available.
- [x] R1-05's settled positions are applied throughout without re-litigation.
- [x] `command_id` used throughout, not `request_id`.
- [x] `command_response` has no `seq` — explicit in Phase A §3.3 and contract test.
- [x] Phase B-pre split into B-pre-a (gates B) and B-pre-b (gates D).
- [x] Replay buffer default justified (1024 prod, configurable via env).
- [x] Phase C SDK timeout 1.0 s default explicit.
- [x] Positive-sense feature flag language used where relevant (`enable_browser_ws_bridge` is positive-sense per R1-05).
- [x] rAF scaffolded but disabled (`Settings.enable_raf_coalescer=False`).
- [x] GAP-WS-19 NOT in any phase scope, only a regression test.
- [x] Two-flag browser bridge logic (`enable_browser_ws_bridge` + `disable_ws_bridge`).
- [x] HMAC adapter auth in B-pre-b, not `X-Juniper-Role` header.
- [x] Phase E default `drop_oldest_progress_only`.
- [x] Audit logger skeleton in B-pre-a; Prometheus hookup in B.
- [x] "One resume per connection" rule in Phase A deliverables.
- [x] Contract-test marker (`contract`) in §15.2.
- [x] CODEOWNERS entry in Phase H.
- [x] `test_set_params_caller_cancellation` marked mandatory Phase A-SDK gate.
- [x] Total effort bounds declared (§17).
- [x] Disagreements explicit and justified (§18).
- [x] No unjustified deviations from R1-05.

### 19.4 Scope discipline check

- [x] Did not propose new GAP-WS or M-SEC identifiers beyond those R1-05 already adopts (M-SEC-10, -11; -12 folded into -07).
- [x] Did not re-design any API surface — only allocated existing R1-accepted APIs to phases.
- [x] Did not modify any source files, only authored this proposal.
- [x] Did not propose new test markers beyond `contract` and `latency_recording` already in R1-05.
- [x] Did not propose new feature flags beyond the ones listed in §1.3.
- [x] Referenced R1-NN and source-doc identifiers throughout.

Scope discipline **PASS**.

### 19.5 Items flagged for Round 3 attention

In priority order:

1. **Validate the 5 R1-05 §5 unresolved items** (NetworkVisualizer render tech, session middleware presence, Dash/Plotly versions, `run_coroutine_threadsafe` usage, `command_id` wire pass-through in current `/ws/control`). First commit in each Phase does the verification.
2. **Confirm P7 (flag flip PR) as a separate one-line PR**, not folded into P6, so reviewers can diff the default change in isolation.
3. **Confirm CODEOWNERS exists as an enforceable mechanism** in the Juniper GitHub org. If it doesn't, §13 falls back to a pre-commit hook (R1-02 §14.5).
4. **Determine the exact Phase B soak duration** — R1-02 wants 72 h for Phase A, R2-02 keeps 24 h. Worth a Round 3 reconciliation.
5. **Verify the merge-queue tooling** — §16's strict ordering assumes a queue. If cascor/canopy don't have GitHub merge queue, a human-enforced ordering rule goes in the ops runbook.

### 19.6 Confidence assessment

- **High confidence**:
  - Phase A deliverables and exit gates (R1-05 §3-4 explicit).
  - Phase B exit gate #2 (the 90% bandwidth reduction) as the primary P0 measurable.
  - The cross-repo merge sequence.
  - The six-question contract structure per phase.
- **Medium confidence**:
  - Phase C effort estimate (2 days expected; depends on adapter refactor complexity).
  - Phase B NetworkVisualizer contingent wire (render tech unverified).
  - Phase B-pre-b session middleware contingency (R1-05 §5.2).
- **Lower confidence**:
  - Phase E tuning (per-client queue size = 256 is a guess; may need staging tuning).
  - Phase F reconnect-cap lift (GAP-WS-31) — debated; kept in.

### 19.7 Known gaps not addressed in R2-02

- **Phase B+1 NetworkVisualizer deep render migration** is not specced here. Deferred to a separate follow-up.
- **Remove-REST follow-up** is explicitly out of scope (R1-02 §1.2 safety principle 7: REST paths stay alive forever).
- **Multi-tenant replay buffer partitioning** — deferred per R1-05 §4.13.
- **Two-bucket rate limit split** — deferred per R1-05 §4.46.
- **rAF flip-to-enabled PR** — deferred per R1-05 §4.3.

### 19.8 Target length check

Target 1200-2000 lines. Final line count target: ~1300-1500 lines after the self-audit edits. Dense signal, no filler prose — every phase contract is structural, not narrative.

---

**End of proposal R2-02.**
