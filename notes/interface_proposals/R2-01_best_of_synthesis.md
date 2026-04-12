# Round 2 Proposal R2-01: Best-of Synthesis Master Plan

**Angle**: Strongest recommendations from R1-01..R1-05 integrated into one master plan
**Author**: Round 2 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 2 consolidation — input to Round 3
**Inputs consolidated**: R1-01 (critical-path), R1-02 (safety-first), R1-03 (maximalist), R1-04 (runbook), R1-05 (disagreement reconciliation)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE

---

## 1. Executive summary

This proposal integrates the strongest, most defensible recommendations from all five Round 1 proposals into a single master development plan for the WebSocket migration described in the source doc. The P0 outcome is **elimination of the ~3 MB/s `/api/metrics/history` REST polling bomb** (GAP-WS-16), achieved by a browser→canopy→cascor WebSocket path that is correct, secure, observable, operable, and reversible at every step.

The plan is organized around **12 phases** — Phase A (SDK), Phase 0-cascor/A-server (cascor prereqs), Phase B-pre-a (read-path security gate), Phase B (browser bridge + polling elimination), Phase B-pre-b (control-path security gate), Phase C (set_params adapter, feature-flagged P2), Phase D (control buttons, gated on B-pre-b), Phase E (full backpressure), Phase F (heartbeat+jitter), Phase G (cascor set_params integration tests), Phase H (`_normalize_metric` regression gate + audit), Phase I (asset cache busting, bundled with B). The ordering is load-bearing: Phase A-server and A can run in parallel with B-pre-a; Phase B depends on both A-server and B-pre-a; Phase D depends on B and B-pre-b; Phase C depends on A and B.

**Total effort estimate**: ~13.5 engineering days / ~4.5 weeks calendar (from R1-03 §1 and R1-05 §4.40, validated against R1-04's 12-day runbook plus ~1.5 days of safety amplification from R1-02). A minimum-viable carveout (Phase A-server + minimum B-pre-a + read-path B + Phase I) can ship in ~7 engineering days (R1-01 §5) and achieves the P0 outcome alone; the remaining phases are tactical follow-ups scheduled in waves.

**Key gates**: (1) P0 metric `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` drops >90% vs pre-Phase-B baseline when WebSocket is connected; (2) Phase B-pre-b gate closes before any Phase D PR is mergeable; (3) every phase has a tested kill switch with MTTR ≤5 min; (4) observability metrics and alerts exist in Prometheus BEFORE the behavior change they guard ships; (5) REST paths stay alive as fallback forever — no deletion in this migration.

**Rollback story**: every phase has a config-only kill switch (listed in §14) with a validated MTTR. Phase B has TWO flags (`enable_browser_ws_bridge` default False pre-stabilization, permanent `disable_ws_bridge` kill switch per R1-05 §4.45). Phase C has `use_websocket_set_params=False` (default, per R1-02 §6.1). Phase D has `disable_ws_control_endpoint=True` (CSWSH emergency lever). If any kill switch fails validation in staging, the phase does not ship to production. Full rollback of any merged PR is `git revert` + a patch-version redeploy; the 0-commit-revert safety net is R1-04's bisect-friendly commit decomposition.

---

## 2. Provenance map

Each major recommendation → which R1 contributed the strongest argument for it. Where multiple R1s support a position, the cell lists the primary source first.

| Recommendation | Primary R1 source | Amplified by |
|---|---|---|
| Minimum-viable P0 carveout (7 engineering days) | R1-01 §1.2, §5 | R1-03 §2 (full plan) |
| Observability-before-behavior-change principle | R1-02 §1.2 (principle 1) | R1-03 §16 |
| Kill switches for every phase with validated MTTR | R1-02 §1.2 (principle 2), §8 | R1-04 rollback sections |
| Defensive defaults (feature flags OFF pending evidence) | R1-02 §1.2 (principle 5), §5.2, §6.1 | R1-01 §2.5 |
| Conservative effort estimate (~13.5 days) | R1-03 §1, R1-05 §4.40 | R1-02 §1.3 |
| Full Phase A → Phase I coverage | R1-03 §2, §14 | R1-04 day-by-day |
| Day-by-day runbook structure | R1-04 Days 1-12 | R1-03 §5-13 per-phase |
| Consolidated 16-item risk register | R1-03 §14 | R1-02 §11, R1-01 §7 |
| Master kill-switch matrix | R1-02 §8 | R1-03 §14 matrix |
| 55+ disagreement reconciliation | R1-05 §4 | — |
| Wire-level `command_id` naming (NOT `request_id`) | R1-05 §4.2 | overrides R1-03 §4.3 |
| GAP-WS-19 marked RESOLVED | R1-05 §4.16 | overrides R1-02 §11, R1-03 §6.2.12 |
| `command_response` has no seq field | R1-05 §4.17 | overrides R1-03 §5.3 |
| Phase A-server carveout (renamed Phase 0-cascor) | R1-05 §4.19, R1-01 §2.1 | R1-03 §5, R1-04 Days 2-3 |
| Phase B-pre-a / B-pre-b split | R1-05 §4.35, R1-03 §18.1 | R1-02 §4.1, §4.2 |
| Minimum M-SEC controls for Phase B-pre-a | R1-01 §2.2 + R1-02 §4.1 | R1-05 §4.35 |
| Phase E default `drop_oldest_progress_only` | R1-02 §7.2, R1-03 §11.1, R1-05 §4.36 | — |
| Chaos tests for replay race, broadcaster, adapter | R1-02 §10.1 | R1-03 §15.7 |
| Audit logger scope split (skeleton in B-pre-a, counters in B) | R1-05 §4.14 | — |
| HMAC-derived adapter auth | R1-05 §4.43 | R1-02 §4.2 (item 20) |
| Two-flag browser-bridge design | R1-05 §4.45 | — |
| rAF coalescer scaffold DISABLED | R1-01 §2.3.2, R1-05 §4.3 | R1-02 §5.5 |
| 1 Hz REST fallback polling during reconnect | R1-01 §2.3.1, R1-05 §4.4 | R1-04 §9.3 |
| Structured `{events, gen, last_drain_ms}` store shape | R1-05 §4.7 | R1-03 §8.1.2 |
| GAP-WS-24 split into 24a (browser) + 24b (canopy backend) | R1-05 §4.8 | — |
| Phase 0-cascor ships before canopy Phase B (production soak) | R1-02 §5.1 | R1-05 §4.19 |
| `canopy_rest_polling_bytes_per_sec` as P0 acceptance metric | R1-01 §2.5.1, R1-02 §2.2 | R1-04 §15.4 |
| MVS-TEST-15 bandwidth proof Playwright test | R1-01 §2.4.1 | R1-04 §9.4 |
| 72-hour staging soak for Phase B (memory leak guard) | R1-02 §3.4, §5.6 AC-24 | R1-03 §8.15 |
| CODEOWNERS rule on `_normalize_metric` | R1-02 §7.5, R1-03 §13.4 | R1-05 §4.41 |
| Contract-test lane `contract` marker | R1-05 §4.34, R1-03 §15.8 | R1-02 §10.5 |
| Chaos test: replay race under asyncio.gather | R1-02 §3.1 (item 29) | — |
| Chaos test: AST-based ring-bound-in-handler lint | R1-02 §5.4 (item 2) | R1-01 §2.3.1 (MVS-FE-01) |
| Error-budget burn-rate freeze rule | R1-02 §2.4 | — |
| Disaster recovery scenario per phase | R1-02 §9 | R1-04 rollback sections |
| Merge order (cascor-client → cascor → canopy → waves) | R1-04 §13, R1-03 §17.1 | R1-02 §8.1 |
| Day-by-day commit decomposition | R1-04 Days 1-12 | R1-03 §5.11, §8.11 |

---

## 3. Phase A-server / Phase 0-cascor: cascor prerequisites

**Renaming note (from R1-05 §4.19)**: R1-03 used "Phase A-server"; R1-05 observed this collides with the source doc's "Phase A" (SDK). This synthesis uses **Phase 0-cascor** as the canonical name and treats "Phase A-server" as an alias for legacy cross-reference. Phase 0-cascor and Phase A (SDK) can run in parallel.

### 3.1 Scope (minimum + maximalist merged)

The 10-commit cascor prerequisite chain from R1-03 §5.11 and R1-04 Days 2-3, with R1-01's minimum-viable framing for what absolutely must land:

| Commit | Intent | Source | In minimum? |
|---|---|---|---|
| 0-cascor-1 | `messages.py` optional `seq` field on every builder | R1-03 §5.11, R1-04 Day 2 | yes |
| 0-cascor-2 | `WebSocketManager` gains `_next_seq`, `_seq_lock`, `_replay_buffer` (deque maxlen=1024), `server_instance_id` (UUID4), `server_start_time`, `_assign_seq_and_append()` helper; `connect()` advertises `server_instance_id`, `server_start_time`, `replay_buffer_capacity` in `connection_established` | R1-03 §5.11, R1-04 Day 2 | yes |
| 0-cascor-3 | `_send_json` wraps in `asyncio.wait_for(..., timeout=0.5)` — RISK-04 quick-fix | R1-03 §5.7, R1-04 Day 2, R1-01 A-srv-3 | yes |
| 0-cascor-4 | `replay_since(last_seq)` helper + `ReplayOutOfRange` exception; copy-under-lock pattern | R1-03 §5.5, R1-04 Day 2 | yes |
| 0-cascor-5 | `training_stream.py` two-phase registration (`_pending_connections`, `promote_to_active()`, 5 s resume-frame timeout, `resume`/`resume_ok`/`resume_failed` flow) | R1-03 §5.6, R1-04 Day 3, R1-05 §4.18 | yes |
| 0-cascor-6 | `/api/v1/training/status` returns `snapshot_seq` and `server_instance_id` atomically under `_seq_lock` | R1-03 §5.11, R1-04 Day 3 | yes |
| 0-cascor-7 | `lifecycle/manager.py` 1 Hz state throttle → debounced coalescer with terminal-state bypass (GAP-WS-21) | R1-03 §5.8, R1-01 A-srv-7 | yes |
| 0-cascor-8 | `broadcast_from_thread` done_callback for exception logging (GAP-WS-29) | R1-03 §5.9, R1-04 Day 3 | yes |
| 0-cascor-9 | `/ws/control` protocol error responses (GAP-WS-22): unknown command → error response; non-JSON → close 1003 | R1-03 §5.10, R1-04 Day 3 | yes |
| 0-cascor-10 | Docs + CHANGELOG (README/AGENTS updates for new envelope fields, new settings) | R1-03 §5.11 | yes |

**`command_response` carve-out** (R1-05 §4.17 RESOLVED): `/ws/training` has a replay buffer and every broadcast carries `seq`. `/ws/control` has NO replay buffer and `command_response` frames do NOT carry `seq`. Client-side correlation of responses is via `command_id`, not seq.

**GAP-WS-19 carve-out** (R1-05 §4.16 RESOLVED): `close_all()` lock fix is already in main (verified at `juniper-cascor/src/api/websocket/manager.py:138-156`). Do NOT re-implement. Add `test_close_all_holds_lock` as a regression gate only.

**Scope explicitly NOT in Phase 0-cascor** (deferred to Phase E or later):
- Per-client pump task + bounded queue + policy matrix (full backpressure). The 0.5 s `_send_json` quick-fix is sufficient for Phase B at ≤50 clients.
- `permessage-deflate` negotiation (GAP-WS-17). Deferred per R1-03 §20.1.
- Topology chunking (GAP-WS-18). REST fallback preserved as the near-term mitigation.
- Full `command_id` echo (GAP-WS-32 server-side). Ships with Phase G.

### 3.2 Implementation (R1-04 runbook)

Days 2-3 of R1-04. Each commit green independently; verified via cherry-pick. Specific file paths from R1-04 §2.3, §3.3:

- `juniper-cascor/src/api/websocket/messages.py` — commit 1
- `juniper-cascor/src/api/websocket/manager.py` — commits 2, 3, 4, 8
- `juniper-cascor/src/api/websocket/training_stream.py` — commit 5
- `juniper-cascor/src/api/training/router.py` (or wherever `/api/v1/training/status` lives) — commit 6
- `juniper-cascor/src/lifecycle/manager.py:133-136` — commit 7
- `juniper-cascor/src/api/websocket/control_stream.py` — commit 9
- `juniper-cascor/src/config/settings.py` — `ws_replay_buffer_size: int = 1024` (default per R1-03 §5.2; see §3.7 disagreement note), `ws_send_timeout_seconds: float = 0.5`, `ws_resume_handshake_timeout_s: float = 5.0`, `ws_state_throttle_coalesce_ms: int = 1000`, `ws_pending_max_duration_s: float = 10.0` per R1-02 §3.2.

### 3.3 Tests (R1-03 §5.12 + R1-05 + R1-02 chaos additions)

**Unit tests** (`juniper-cascor/src/tests/unit/api/`):

- `test_seq_monotonically_increases_per_connection` (renamed from `test_seq_monotonically_increases` per R1-05 §4.17 to clarify `/ws/training` scope)
- `test_seq_lock_does_not_block_broadcast_iteration` (R1-03 §5.3 Option 2 validation)
- `test_replay_buffer_bounded_1024` + `test_replay_since_*` boundary cases (happy path, out-of-range, empty, oldest-minus-one)
- `test_send_json_0_5s_timeout` (fake never-resolving send, returns False within 0.6 s)
- `test_state_coalescer_preserves_terminal_transitions` (Started → Failed within 200 ms, both observed)
- `test_broadcast_from_thread_exception_logged_not_leaked`
- `test_connection_established_advertises_server_instance_id_and_replay_buffer_capacity`
- `test_snapshot_seq_atomic_with_state_read`
- `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 explicit negative assertion)
- `test_close_all_holds_lock` (R1-05 §4.16 regression gate)
- `test_pending_connections_not_eligible_for_broadcast` (R1-05 §4.18)
- `test_promote_to_active_atomic_under_seq_lock`

**Chaos tests** (from R1-02 §3.1 items 29, 30 + R1-03 §15.7):

- Chaos-broadcast: `hypothesis` + `asyncio.gather` 100 concurrent broadcast/disconnect/resume under randomized exception types. Assert: no deadlocks, no seq gaps, no coroutine leaks, `_per_ip_counts` shrinks to zero.
- Chaos-replay-race: 1000 broadcasts interleaved with 100 `replay_since()` calls from forged cursors. Assert: every snapshot monotonic, no replay returns seq higher than its snapshot's newest.
- Chaos-broadcast_from_thread: `hypothesis`-generated random exception types; assert `cascor_ws_broadcast_from_thread_errors_total` increments once per raise and no stderr warning escapes.

**Integration tests** (`juniper-cascor/src/tests/integration/`):

- `test_resume_happy_path_via_test_client` (broadcast 3, disconnect, reconnect with last_seq=0, assert resume_ok + 3 replayed)
- `test_resume_failed_server_restarted` (stale UUID)
- `test_resume_failed_out_of_range` (broadcast 2000, reconnect with last_seq=10)
- `test_resume_malformed_data`
- `test_resume_timeout_no_frame`

**Load test (elevated to blocking gate per R1-02 §10.3)**: broadcast at 100 Hz for 60 s with 10 clients; p95 latency < 250 ms, memory stable ±10%.

### 3.4 Observability (R1-02 §2.1 + R1-03 §5.13)

**Metrics (mandatory before Phase 0-cascor merges to main)**:

| Metric | Type | Labels | Rationale |
|---|---|---|---|
| `cascor_ws_seq_current` | Gauge | — | Loss of monotonicity is correctness-catastrophic (R1-02) |
| `cascor_ws_replay_buffer_occupancy` | Gauge | — | Operational proxy for replay window |
| `cascor_ws_replay_buffer_bytes` | Gauge | — | Memory-creep guard, sampled every 30 s |
| `cascor_ws_replay_buffer_capacity_configured` | Gauge | — | Init-time assertion; aids operator diffing |
| `cascor_ws_resume_requests_total` | Counter | `outcome={success, server_restarted, out_of_range, malformed, no_resume_timeout}` | — |
| `cascor_ws_resume_replayed_events` | Histogram | — | Buckets `{0, 1, 5, 25, 100, 500, 1024}` |
| `cascor_ws_broadcast_timeout_total` | Counter | `type` | Per-type slow-client prune counter |
| `cascor_ws_broadcast_send_seconds` | Histogram | `type` | Latency of the `_send_json` path |
| `cascor_ws_pending_connections` | Gauge | — | Non-zero >5s = stuck resume handshake |
| `cascor_ws_state_throttle_coalesced_total` | Counter | — | Post-coalescer output |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter | — | Must be 0 in steady state (R1-02) |
| `cascor_ws_connections_active` | Gauge | `endpoint` | — |
| `cascor_ws_command_responses_total` | Counter | `command, status` | — |
| `cascor_ws_command_handler_seconds` | Histogram | `command` | — |

**Alerts**:

- `WSSeqCurrentStalled` (page): `changes(cascor_ws_seq_current[5m]) == 0 AND cascor_ws_connections_active > 0` — broadcast loop hang (RISK-14 precursor).
- `WSResumeBufferNearCap` (ticket): `cascor_ws_replay_buffer_occupancy > 0.8 * capacity for 30s`.
- `WSPendingConnectionStuck` (ticket): `cascor_ws_pending_connections > 0 for 30s`.
- `WSSlowBroadcastP95` (ticket): histogram_quantile(0.95, …) > 500 ms.
- `WSStateDropped` (page): any non-zero `cascor_ws_dropped_messages_total{type="state"}` — protects against terminal-event loss.

**Metric-presence test** (R1-02 §10.6): pytest scrapes `/metrics` and asserts every required metric is exported. Cheap, high-value.

### 3.5 Acceptance gate

1. All 15 unit tests + 6 integration tests + 4 chaos tests green.
2. Load test green (100 Hz × 60 s × 10 clients, p95 < 250 ms).
3. Metric-presence test green.
4. 72-hour staging soak (R1-02 §3.4 amplification; R1-04's 24h was too short for seq monotonicity bugs to surface under sustained multi-client broadcast):
   - `cascor_ws_broadcast_from_thread_errors_total == 0`
   - `cascor_ws_replay_buffer_occupancy` distribution stable
   - `cascor_ws_broadcast_timeout_total` rate < 0.1/s
   - `cascor_ws_seq_current` monotonic across all hours
5. Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published.
6. Smoke test against local dev cascor (R1-04 §3.6): open WS, receive `connection_established` with `server_instance_id` and `replay_buffer_capacity`, send `resume` with fresh UUID, receive `resume_ok` or `resume_failed`.

### 3.6 Kill switch

| Switch | Who | MTTR | Effect | Validation |
|---|---|---|---|---|
| `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | ops | 5 min | Disables replay; all reconnects get `out_of_range` → snapshot fallback | `cascor_ws_resume_requests_total{outcome="out_of_range"}` spike |
| `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | ops | 5 min | Aggressive slow-client prune | `cascor_ws_broadcast_timeout_total` spike |
| Rolling restart of cascor | ops | 10 min | New `server_instance_id` forces all clients to snapshot-refetch | Client logs show snapshot refetch |
| Revert Phase 0-cascor PRs | ops | 15 min | Full rollback to pre-seq behavior; old clients unaffected (additive field contract) | Clients with cached UUIDs get `out_of_range` or `server_restarted` |

**No runtime feature flag** — Phase 0-cascor is additive (old clients ignore the new `seq` field via `dict.get()`). Rollback is a revert, not a flag flip.

### 3.7 Disagreement notes (from R1-05)

**Replay buffer default size**: R1-02 §3.2, §13.1 argues for 256 (smaller window exercises the out-of-range fallback path more often, keeping it reliable). R1-03 §5.2 and R1-05 keep 1024 as the default. **This synthesis keeps 1024** because (a) R1-05's resolution priority is source-doc fidelity and R1-05 did not flip on this item, (b) 256 defers the `out_of_range` path-exercise benefit to production incidents rather than sustained soaks, which contradicts the observability-before-behavior principle, and (c) 1024 can always be lowered via env var. Operators who want to exercise the fallback path more aggressively can set `JUNIPER_WS_REPLAY_BUFFER_SIZE=256` in staging.

**State coalescer in Phase 0-cascor vs Phase E**: R1-01 §2.1 table row A-srv-7 flags this as a decision; R1-05 does not override. This synthesis keeps the coalescer in Phase 0-cascor (agrees with R1-03 §5.8 and R1-04 Day 3) because the drop-filter bug silently drops terminal state transitions, which is a correctness regression that Phase B would immediately surface in the browser.

**`_pending_connections` vs per-connection `seq_cursor`**: R1-05 §4.18 adopts R1-03's pending-set design. Keep as-is.

---

## 4. Phase A: juniper-cascor-client SDK `set_params`

**Runs in parallel with Phase 0-cascor and Phase B-pre-a.** Can ship immediately; no upstream dependencies.

### 4.1 Scope

Add `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None)` to `juniper-cascor-client/juniper_cascor_client/ws_client.py`. Refactor to a single background `_recv_task` with per-request correlation.

**Critical naming correction (R1-05 §4.2 RESOLVED)**: the wire-level correlation field is **`command_id`**, not `request_id`. R1-03 §4.2 used `request_id`; this synthesis adopts `command_id` because (a) source doc §7.32 line 1403 explicitly uses `command_id`, (b) R1-02 and R1-03's cascor side already uses `command_id`, (c) aligning now prevents a cross-repo wire mismatch in Phase G integration tests. **This is R1-05's most important cross-cutting correction.**

### 4.2 Implementation (R1-04 Day 1)

**File: `juniper_cascor_client/ws_client.py`**

- `CascorControlStream.__init__` adds `self._pending: Dict[str, asyncio.Future] = {}`, `self._recv_task: Optional[asyncio.Task] = None`.
- `connect()` starts `self._recv_task = asyncio.create_task(self._recv_loop())`.
- `_recv_loop()` parses each inbound frame, reads `data.command_id`, pops future, `future.set_result(envelope)`. Wrap in `try/except Exception` → on unhandled exception: log ERROR + set exception on all pending futures (R0-04 R04-06 / R1-03 §4.4).
- `disconnect()` cancels `_recv_task`, drains `_pending` with `set_exception(JuniperCascorConnectionError("disconnected"))`.
- `set_params(params, *, timeout=1.0, command_id=None)`:
  - Default `timeout=1.0` (R1-05 §4.1 RESOLVED: source doc §7.32 more-specific rule beats §7.1 generic). Not 5.0.
  - Register future in `_pending`, send command frame, `await asyncio.wait_for(future, timeout)`, ALWAYS `pop(command_id, None)` in `finally`.
  - Stash `envelope["_client_latency_ms"]` (private field, leading underscore).
- Preserve existing `command()` method as wrapper; generates fresh `command_id` if caller omitted.
- **No SDK retries** on timeout (R1-05 §4.22 / R1-03 §4.22). Caller decides fallback.

**File: `juniper_cascor_client/testing/fake_ws_client.py`** — add `on_command(name, handler)` registration; auto-scaffold `command_response` reply for known commands.

### 4.3 Tests (R1-03 §4.6 + R1-05 §4.25 + R1-05 §4.42)

- `test_set_params_round_trip`
- `test_set_params_timeout` → `JuniperCascorTimeoutError`
- `test_set_params_validation_error` → `JuniperCascorValidationError`
- `test_set_params_fails_fast_on_disconnect` (renamed from `test_set_params_reconnection_queue` per R1-05 §4.42 to reflect the fail-fast policy)
- `test_set_params_concurrent_correlation` (two concurrent calls distinguished by `command_id`)
- `test_set_params_caller_cancellation` — **mandatory gate** per R1-05 §4.25; protects against correlation-map memory leak
- `test_command_legacy_still_works` (regression gate for existing `command()` API)
- `test_set_params_no_command_id_first_match_wins` (transition window before Phase G echo lands)
- `test_set_params_default_timeout_is_one_second` (R1-05 §4.1 regression gate)
- `test_set_params_x_api_key_header_present` (R0-02 IMPL-SEC-44 regression guard)
- `test_set_params_no_retry_on_timeout` (R1-05 §4.22 explicit no-retry)
- `test_len_pending_returns_to_zero_after_failure_modes` (R1-02 §9.2 nightly, correlation-map leak prevention)

Coverage target: 95% on new SDK code (R1-03 §15.2).

### 4.4 Observability

- SDK-level counter `juniper_cascor_client_ws_set_params_total{status}` where `status ∈ {ok, timeout, error}` (R1-03 §4.8). No alerts at the SDK layer; consumer decides.

### 4.5 Acceptance gate

- 12 unit tests green.
- Coverage ≥ 95% on new code.
- Ruff/black/isort per repo's linter gates.
- PR merged; tag created; PyPI publish succeeded; `pip index versions juniper-cascor-client | head -1` shows the new version.
- Record the new version as `SDK_VERSION_A` for Phase C dep pin bump.

### 4.6 Kill switch

**No SDK-layer kill switch** (SDKs don't have runtime flags). Rollback is: revert the PR + publish a patch release. Consumers pin to the previous version. Yank PyPI release ONLY if "installs but will not import" — otherwise fix-forward.

### 4.7 Disagreement notes (from R1-05)

- `command_id` vs `request_id`: resolved to `command_id` per §4.2 above.
- Default timeout 1.0 vs 5.0: resolved to 1.0 per R1-05 §4.1.
- SDK reconnect queue: resolved to fail-fast per R1-05 §4.42.
- Debounce layer location: debounce lives in Dash clientside callback, NOT in SDK (R1-05 §4.24).

---

## 5. Phase B-pre-a: read-path security gate (gates Phase B)

**Dependency**: none. Runs in parallel with Phase A and Phase 0-cascor.

**Scope (R1-05 §4.35 + R1-01 §2.2 + R1-02 §4.1)**: the security subset that must land BEFORE Phase B opens up new browser→canopy `/ws/training` traffic. This is deliberately narrower than the full Phase B-pre bundle from R1-03; the remaining controls live in Phase B-pre-b and gate Phase D.

### 5.1 Scope (R1-01 minimum + R1-02 amplification)

**Mandatory in Phase B-pre-a**:

1. **M-SEC-03: per-frame size caps** on every `/ws/*` endpoint (both cascor and canopy). Training stream inbound capped at 4 KB (ping/pong only); control stream inbound capped at 64 KB; outbound capped at 128 KB. Overflow → close 1009.
2. **M-SEC-01 + M-SEC-01b: Origin allowlist** on canopy `/ws/training` AND cascor `/ws/training` (not yet `/ws/control`). **This is a disagreement with R1-03 §18 and R1-05 §4.35**, which treat Origin as B-pre-b. **R1-01 §2.2.1 and §4.2 rightly argue that Origin on `/ws/training` prevents live-data exfiltration** (R0-02 §3.1 blast-radius), which is a Phase B concern even if the control-plane CSWSH is a Phase D concern. Minimum Origin has low cost (~0.5 day) and closes a whole attack class. Default allowlist: `["http://localhost:8050", "http://127.0.0.1:8050", "https://localhost:8050", "https://127.0.0.1:8050"]`. Empty allowlist = reject-all (fail-closed) — R1-05 §4 D4 resolved.
3. **M-SEC-04 (partial): per-IP connection cap**, 5/IP default (R1-05 §4.37 RESOLVED). Auth-timeout subpart deferred to B-pre-b (ties to CSRF first-frame).
4. **M-SEC-10: idle timeout**, 120 s bidirectional close 1000. R1-05 §4.15 keeps as canonical new identifier.
5. **Audit logger skeleton**: new `canopy.audit` logger, JSON formatter, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist. **No Prometheus counters yet** — counters move to Phase B per R1-05 §4.14 so B-pre-a stays scoped.

**Not in Phase B-pre-a** (all deferred to Phase B-pre-b):
- M-SEC-02 cookie+CSRF
- M-SEC-05 command rate limit
- M-SEC-06 opaque close reasons (only matters with auth failures)
- Origin on `/ws/control` (tied to CSRF first-frame)
- Full M-SEC-07 audit counters (move to Phase B)
- M-SEC-11 adapter inbound validation
- Adapter synthetic auth frame

### 5.2 Implementation (R1-04 Days 4-6 subset)

Porting from R1-04 Day 4 (Origin) + Day 5 (size caps) + Day 6 (per-IP + idle + audit skeleton):

| Step | File | Change |
|---|---|---|
| B-pre-a-1 | `juniper-cascor/src/api/websocket/origin.py` (new) | Extract `validate_origin(ws, allowlist) -> bool` helper. Case-insensitive on scheme+host, port significant, strip trailing slash, null origin rejected, `*` unsupported. |
| B-pre-a-2 | `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` (new) | Matrix tests: exact match, case-insensitive, trailing slash, null, port mismatch, scheme mismatch, wildcard rejection, empty = reject-all |
| B-pre-a-3 | `juniper-cascor/src/api/app.py` | Wire `validate_origin` into `training_stream_handler` (NOT `control_stream_handler` yet) |
| B-pre-a-4 | `juniper-cascor/src/config/settings.py` | `ws_allowed_origins: list[str] = []` (fail-closed default) + env `JUNIPER_WS_ALLOWED_ORIGINS` |
| B-pre-a-5 | `juniper-canopy/src/backend/ws_security.py` (new) | Copy of cascor's `validate_origin` |
| B-pre-a-6 | `juniper-canopy/src/main.py` | Wire `validate_origin` into `/ws/training` route (not `/ws/control`) |
| B-pre-a-7 | `juniper-canopy/src/config/settings.py` | `allowed_origins` with concrete localhost/127.0.0.1 × http/https defaults |
| B-pre-a-8 | `juniper-cascor/src/api/websocket/manager.py` | Add `_per_ip_counts: Dict[str, int]`, increment in `connect()` under `_lock`, decrement in `disconnect()` finally, purge empty entries |
| B-pre-a-9 | `juniper-cascor/src/config/settings.py` | `ws_max_connections_per_ip: int = 5` |
| B-pre-a-10 | `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py` (new) | 6th-conn rejected 1013; race test via `asyncio.gather`; entries purged when count reaches zero |
| B-pre-a-11 | `juniper-cascor/src/api/websocket/training_stream.py` | `max_size=4096` on receive |
| B-pre-a-12 | `juniper-canopy/src/main.py` | `max_size=4096` on `/ws/training` inbound, `max_size=65536` on `/ws/control` inbound |
| B-pre-a-13 | CI script `scripts/audit_ws_receive_calls.py` (new, R1-02 §4.1) | AST check: every `ws.receive_*()` call has an explicit `max_size` |
| B-pre-a-14 | `juniper-cascor/src/api/websocket/manager.py` | Idle timeout: `asyncio.wait_for(receive_text(), timeout=120)`, close 1000 on TimeoutError |
| B-pre-a-15 | `juniper-canopy/src/backend/audit_log.py` (new) | `canopy.audit` logger, JSON formatter, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist derived from `SetParamsRequest.model_fields.keys()`, CRLF escape rule 10 from R0-02 §4.6 |

### 5.3 Tests

**Unit**:

- `test_oversized_frame_rejected_with_1009` per endpoint
- `test_per_ip_cap_enforced` (6th rejected)
- `test_per_ip_counter_decrements_on_disconnect` / `on_exception`
- `test_per_ip_map_shrinks_to_zero` (R1-02 §4.1: memory-leak guard, entries reaching 0 are deleted)
- `test_per_ip_counter_increment_decrement_race` (R1-02 §4.1 + R1-03 §6.2.3)
- `test_origin_allowlist_accepts_configured_origin`
- `test_origin_allowlist_rejects_third_party`
- `test_origin_allowlist_rejects_missing_origin`
- `test_origin_header_case_insensitive_host`
- `test_empty_allowlist_rejects_all` (fail-closed)
- `test_idle_timeout_closes_1000`
- `test_audit_log_format_and_scrubbing` (R1-05 §4.14)

**Integration**:

- `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` (Playwright, cross-origin probe on `/ws/training`)

### 5.4 Observability

- `cascor_ws_oversized_frame_total{endpoint, type}` (R1-02 §2.1)
- `cascor_ws_per_ip_rejected_total`
- `canopy_ws_oversized_frame_total{endpoint}`
- `canopy_ws_per_ip_rejected_total`
- `canopy_ws_origin_rejected_total{origin_hash, endpoint}` — hash is SHA-256 prefix 8 chars (R1-02 §2.3, GDPR-safe correlation)

**Alerts (page on-call)**:

- `WSOriginRejection`: `increase(canopy_ws_origin_rejected_total[5m]) > 0` from unknown origin_hash
- `WSOversizedFrame`: `increase(canopy_ws_oversized_frame_total[5m]) > 0`

### 5.5 Acceptance gate

1. All unit tests green.
2. CSWSH probe test green.
3. CI `audit_ws_receive_calls.py` passes (no unguarded `receive_*`).
4. Alert rule for `WSOriginRejection` test-fired once in staging per R1-02 §2.3.
5. Runbook `juniper-canopy/notes/runbooks/ws-cswsh-detection.md` published.
6. 24-hour staging soak with no user lockout.

### 5.6 Kill switch

| Switch | Who | MTTR | Effect | Validation |
|---|---|---|---|---|
| `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | ops | 5 min | Neutralizes per-IP cap | `canopy_ws_per_ip_rejected_total` drops to 0 |
| `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | ops | 5 min | Widens allowlist | `canopy_ws_origin_rejected_total` drops |
| `JUNIPER_WS_ALLOWED_ORIGINS=*` | — | — | **EXPLICITLY REFUSED** by the parser (R1-02 §4.3). Non-switch; prevents panic-edit during incident. | — |
| `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | ops | 5 min | Disables idle timeout | New connections persist indefinitely |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | Disables audit log writes (disk-full emergency) | No new writes to audit log file |

### 5.7 Disagreement notes (from R1-05)

- **Phase B-pre split B-pre-a vs B-pre-b**: R1-05 §4.35 adopted. This synthesis takes a middle ground: Origin on `/ws/training` ships in B-pre-a (per R1-01 §4.2 disagreement with R1-03 §18.1 — Origin prevents live-data exfiltration); Origin on `/ws/control` ships in B-pre-b (tied to CSRF flow). This is a minor adjustment to R1-05's split, justified by R1-01's exfiltration argument.
- **Audit logger scope split**: R1-05 §4.14 adopted (skeleton + rotation in B-pre-a; Prometheus counters in Phase B).
- **`ws_security_enabled` vs `disable_ws_auth`**: R1-05 §4.10 kept the negative-sense name. This synthesis adopts the **positive-sense `ws_security_enabled: bool = True`** (R1-02 §4.2 item 15 + R1-03 §18.6) because (a) negative-sense flags are classic footguns, (b) the CI guardrail from R1-02 §4.3 refusing `*` is insufficient against a config typo, (c) positive-sense fails safe. **R1-05 loses on this item**; justified by R1-02's safety principle (conservative defaults). The rename cost is ~10 LOC.
- **Replay buffer auth-timeout subpart of M-SEC-04**: deferred to B-pre-b since it ties to CSRF first-frame.

---

## 6. Phase B: frontend wiring + polling elimination

**Dependencies**: Phase 0-cascor in production (browser needs real `seq` from cascor); Phase B-pre-a merged (security gate); Phase A (SDK) optional — Phase B is pure read-path and does not need `set_params`.

**Feature flag**: `Settings.enable_browser_ws_bridge: bool = False` default (R1-05 §4.45 two-flag design). Flip to True after 72-hour staging soak passes. `Settings.disable_ws_bridge: bool = False` as the permanent kill switch. Runtime check: `enabled = enable_browser_ws_bridge and not disable_ws_bridge`. **R1-02 §5.2 reverses R1-01's implicit no-flag stance**: Phase B is the highest-risk phase (RISK-02 Medium/High) and the flag lets us roll back without a code change.

### 6.1 Scope (R1-01 minimum + R1-03 maximalist)

**Mandatory in Phase B**:

1. **`ws_dash_bridge.js` new asset** (R1-03 §8.1.1, ~200 LOC) with `window._juniperWsDrain` namespace and five `on(type, ...)` handlers. **Ring-bound enforcement IN the handler, NOT the drain callback** (R1-02 §5.4 compile-time invariant; R1-01 §2.3.1 MVS-FE-01). `MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`.
2. **`websocket_client.js` cleanup**:
   - `onStatus()` enrichment
   - Reconnect backoff **with jitter** (GAP-WS-30, 3-line change, R1-03 §8.5 item 3)
   - **Remove the 10-attempt cap** (GAP-WS-31) — retry forever at max 30 s (R1-03 §8.5 item 4). **Disagrees with R1-01 §3.4**, which kept the cap. R1-01's rationale was "REST fallback covers permanent unreachability"; R1-03's rationale is "fixing the known bug is cheap." This synthesis adopts R1-03 because lifting the cap has no downside and closes a known bug.
   - `server_instance_id` capture from `connection_established`
   - `seq` tracking (monotonic check + WARN on out-of-order)
   - `resume` frame on reconnect with graceful-degrade to REST snapshot on `resume_failed`
3. **Delete parallel raw-WebSocket clientside callback** at `dashboard_manager.py:1490-1526` (GAP-WS-03). Replace with a citation comment.
4. **`ws-metrics-buffer` drain callback** per R1-03 §8.1.2. Store shape is structured `{events: [...], gen: int, last_drain_ms: float}` (R1-05 §4.7 adopted; belt-and-suspenders against Dash equality false-negatives).
5. **Update existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks** to read from `window._juniperWsDrain` (delete old `window._juniper_ws_*` globals).
6. **Add `ws-cascade-add-buffer` and `ws-candidate-progress-buffer`** Stores and drain callbacks.
7. **`ws-connection-status` Store** with drain callback that peeks `window._juniperWsDrain.peekStatus()` and emits only on change.
8. **Refactor `_update_metrics_store_handler`** at `dashboard_manager.py:2388-2421` to return `no_update` when `ws-connection-status.connected === true`. **Slow fallback to 1 Hz during disconnect** via `n % 10 != 0` (R1-05 §4.4 adopted; R1-01 §2.3.1 MVS-FE-07).
9. **Apply the same polling-toggle pattern** to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. **Keep the REST paths** — they are the kill switch and the fallback (never deleted, per R1-02 principle 7).
10. **Migrate `MetricsPanel.update_metrics_display()`** at `metrics_panel.py:648-670` to a clientside callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"` to the initial figure layout. Add hidden `metrics-panel-figure-signal` dummy Store. Same for `CandidateMetricsPanel`.
11. **NetworkVisualizer minimum WS wiring**: wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape callback. **Do NOT use extendTraces** (cytoscape is not Plotly). Keep REST poll as fallback. Deep render migration deferred per R1-05 §4.5 pending first-commit verification of render tech (§5.1 unresolved item).
12. **Connection indicator badge** (`html.Div` with clientside_callback reading `ws-connection-status`). Four states: connected-green, reconnecting-yellow, offline-red, demo-gray.
13. **Demo mode parity**: `demo_mode.py` sets `ws-connection-status` to `{connected: true, mode: "demo"}` — required test `test_demo_mode_metrics_parity` as blocker (RISK-08).
14. **GAP-WS-24a: browser-side latency instrumentation** (`assets/ws_latency.js`, ~50-100 LOC): records `received_at_ms - emitted_at_monotonic` per message, POSTs to `/api/ws_latency` every 60 s.
15. **GAP-WS-24b: canopy backend `/api/ws_latency` POST endpoint** + Prometheus histogram + `canopy_rest_polling_bytes_per_sec` gauge (P0 motivator proof).
16. **rAF coalescer scaffolded DISABLED** (R1-05 §4.3 + R1-01 §4.3 + R1-02 §5.5). `_scheduleRaf = noop`. Gated on `Settings.enable_raf_coalescer=False`. Enable only after §5.6 instrumentation shows frame pressure.
17. **Phase I asset cache busting bundled with Phase B** (R1-03 §8, R1-04 §15.3, R1-01 §2.3.1 MVS-FE-16). Configure `assets_url_path` with content-hash query string.
18. **Audit logger Prometheus counters** (R1-05 §4.14 moves from B-pre-a to B).

**Explicitly deferred**: full rAF enablement (Phase B+1); `extra="forbid"` on Pydantic schema (Phase C scope, cascor-side handled by existing schema); full bounded JS ring with seq dedup (v1.1 if instrumentation shows need); cytoscape deep migration (Phase B+1 contingent on render tech).

### 6.2 Implementation (R1-04 Days 8-9)

Concrete step list from R1-04 §8.3 + §9.3 with file paths:

**Day 8 — `juniper-canopy`**:

- `src/frontend/assets/ws_dash_bridge.js` (new, ~200 LOC)
- `src/frontend/assets/websocket_client.js` — cleanup (jitter, uncapped retries, seq/UUID handling, resume protocol)
- `src/frontend/dashboard_manager.py` — delete 1490-1526, rewrite `ws-metrics-buffer` drain, update existing drains, add new drains, add `ws-connection-status` drain
- Grep verification commits: `grep -r '_juniper_ws_' src/frontend/` → 0, `grep -r 'new WebSocket' src/frontend/` → 1

**Day 9 — `juniper-canopy`**:

- `src/frontend/components/metrics_panel.py` — clientside `extendTraces` + dummy store + `uirevision`
- `src/frontend/components/candidate_metrics_panel.py` — mirror
- `src/frontend/dashboard_manager.py` — refactor `_update_metrics_store_handler` + apply pattern to state/candidate/topology polls
- `src/frontend/components/connection_indicator.py` (new)
- `src/backend/demo_mode.py` — set ws-connection-status to `{connected: true, mode: "demo"}`
- `src/frontend/assets/ws_latency.js` (new)
- `src/main.py` — `/api/ws_latency` POST endpoint + Prometheus histogram + `canopy_rest_polling_bytes_per_sec` gauge
- Phase I: `src/main.py` — content-hash `assets_url_path`

**Feature-flag gate** (R1-05 §4.45): first deploy ships with `enable_browser_ws_bridge=False`. Staging flip is ops-driven after 72h soak. Production flip is a one-line config PR reviewed by project lead.

### 6.3 Tests (R1-03 §8.12 + R1-05 §4.3, §4.7 + R1-02 §5.6)

**Unit**:

- JS (Jest/Vitest if configured): jitter, uncapped retries, `onStatus`, `_introspect`, ring-bound-in-handler **via AST lint** (R1-02 §5.4 item 2 — walks compiled JS, finds every `on(` call, asserts subsequent `push(...)` is followed by `splice(...)` in the same function body)
- Python: `test_update_metrics_store_handler_returns_no_update_when_ws_connected`, `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`, `test_fallback_polling_at_1hz_when_disconnected` (R1-05 §4.4), `test_ws_metrics_buffer_drain_is_bounded`, grep assertions
- `test_ws_metrics_buffer_store_is_structured_object` (R1-05 §4.7: assert `.data` is `{events, gen, last_drain_ms}`)

**dash_duo**:

- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected`
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_demo_mode_metrics_parity` (RISK-08 gate)
- `test_connection_indicator_badge_reflects_state`
- `test_ws_metrics_buffer_ignores_events_with_duplicate_seq`
- `test_ws_metrics_buffer_is_monotonic_in_seq_no_gap_gt_1` (R1-02 AC-29)

**Playwright**:

- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_seq_reset_on_cascor_restart` (server_instance_id mismatch → snapshot fallback)
- `test_plotly_extendTraces_used_not_full_figure_replace`
- `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 wire-level gate)
- **`test_bandwidth_eliminated_in_ws_mode`** (R1-01 MVS-TEST-15 + R1-04 §15.4): assert `/api/metrics/history` request count is zero over 60 s after initial load. **This is the P0 acceptance gate.**
- `test_metrics_message_has_dual_format` (R1-01 MVS-TEST-14 + R0-01 §3.6): wire-level assertion that cascor→canopy→browser `metrics` events carry BOTH flat and nested metric keys. **Phase H regression gate folded into Phase B** so Phase H can be deferred safely.
- `test_asset_url_includes_version_query_string` (Phase I)

**Chaos tests**:

- Browser-bridge chaos (R1-02 §10.1 item 2): Playwright script that randomly kills/restarts the WS server, varies event rate, corrupts occasional envelope. Assert: no OOM, no freeze, chart data-points ≤ maxPoints. Nightly lane.

**Latency tests**: recording-only in CI (R1-05 §4.28). `@pytest.mark.latency_recording`. Strict assertions in local-only lane.

### 6.4 Observability (R1-02 §2.2 + R1-03 §8.13)

**Mandatory before Phase B ships to production**:

| Metric | Type | Labels | Source |
|---|---|---|---|
| `canopy_ws_delivery_latency_ms_bucket` | Histogram | `type ∈ {metrics, state, topology, cascade_add, candidate_progress, event, command_response}` | R1-03 |
| `canopy_ws_browser_heap_mb` | Histogram (from JS) | — | R1-02 new |
| `canopy_ws_browser_js_errors_total` | Counter (from JS via `/api/ws_browser_errors`) | `component` | **R1-02 §2.2 new — not in R1-03.** Every try/catch in `ws_dash_bridge.js` or `websocket_client.js` must increment this. |
| `canopy_ws_drain_callback_gen` | Gauge | `buffer ∈ {metrics, topology, state, cascade_add, candidate_progress}` | **R1-02 §2.2 new.** Monotonic drain gen; stuck value = dead drain loop. |
| `canopy_ws_active_connections` | Gauge | — | R1-03 |
| `canopy_ws_reconnect_total` | Counter | `reason` | R1-03 |
| **`canopy_rest_polling_bytes_per_sec`** | **Gauge** | **`endpoint`** | **P0 motivator proof; per-endpoint labeling per R1-02 §2.2 amplification** |
| `canopy_ws_connection_status` | Gauge | `status ∈ {connected, reconnecting, offline, demo}` | R1-02 new |
| `canopy_ws_backend_relay_latency_ms` | Histogram | — | R1-02 §2.2 new — measures cascor → canopy adapter → canopy WS broadcast hop separately from the browser-side histogram |

**SLOs** (R1-02 §2.4 + R1-03 §8.13):

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` delivery | <100 ms | <250 ms | <500 ms |
| `state` delivery | <50 ms | <100 ms | <200 ms |
| `command_response` (set_params) | <50 ms | <100 ms | <200 ms |
| `command_response` (start/stop) | <100 ms | <250 ms | <500 ms |
| `cascade_add` delivery | <250 ms | <500 ms | <1000 ms |
| `topology` delivery (≤64 KB) | <500 ms | <1000 ms | <2000 ms |

**Error-budget burn-rate rule** (R1-02 §2.4): if 99.9% compliance budget burns in <1 day, freeze all non-reliability work until recovered. Operationally binding.

**Alerts**:

- `WSDeliveryLatencyP95High` (ticket): `histogram_quantile(0.95, canopy_ws_delivery_latency_ms_bucket{type="metrics"}[5m]) > 500`
- `WSDrainCallbackGenStuck` (ticket): `changes(canopy_ws_drain_callback_gen[2m]) == 0` → also flip connection status to reconnecting so polling toggle reverts to REST fallback
- `WSBrowserHeapHigh` (ticket): `histogram_quantile(0.95, canopy_ws_browser_heap_mb_bucket[1h]) > 500`
- `WSJSErrorsNonZero` (ticket): `increase(canopy_ws_browser_js_errors_total[5m]) > 0`
- `WSConnectionCount80` (ticket)

### 6.5 Acceptance gate (R1-03 §8.15 + R1-02 §5.6)

Ordered by dependency:

1. All `dash_duo` / Playwright tests in §6.3 green.
2. **`test_bandwidth_eliminated_in_ws_mode` green** (P0 motivator proof).
3. `test_metrics_message_has_dual_format` green (Phase H regression gate).
4. `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` shows ≥90% reduction vs pre-Phase-B baseline in staging, measured for 1 hour post-deploy.
5. `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute.
6. "WebSocket health" dashboard panel renders p50/p95/p99 values.
7. **72-hour memory soak** (R1-02 AC-24): `canopy_ws_browser_heap_mb` p95 does not grow >20% over 72 hours.
8. `canopy_ws_browser_js_errors_total == 0` over the 72h soak.
9. `canopy_ws_drain_callback_gen` advances at least once per minute for every buffer type.
10. `test_demo_mode_metrics_parity` green (RISK-08).
11. `Settings.disable_ws_bridge=True` kill switch tested manually; flipping it restores pre-Phase-B REST polling within 5 min TTF.
12. `Settings.enable_browser_ws_bridge` flip-to-True PR reviewed by project lead.
13. Runbooks published: `ws-bridge-debugging.md`, `ws-memory-soak-test-procedure.md`.
14. NetworkVisualizer render tech verified in first commit of Phase B PR (R1-05 §5.1 unresolved → resolved at implementation time).

### 6.6 Kill switch

| Switch | Who | MTTR | Effect | Validation |
|---|---|---|---|---|
| `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | ops | 5 min | Bridge not yet rolled out; dashboard uses REST polling | `canopy_rest_polling_bytes_per_sec` rises to baseline |
| `JUNIPER_DISABLE_WS_BRIDGE=true` | ops | 5 min | Permanent kill switch; forces REST polling | Same |
| Hardcoded ring-cap reduction in JS | dev | 1 hour | Tighter browser memory bounds | Heap drops in soak metrics |
| Revert Phase B PR | ops | 15 min | Full rollback; dashboard reverts to full figure replace + polling | 3 MB/s returns |

### 6.7 Disagreement notes (from R1-05)

- **Phase B feature flag**: R1-05 §4.45 two-flag design adopted. R1-01 §4.3 implicitly argued for no flag (treating Phase B as safe); R1-02 §5.2 inverted this; R1-05 reconciled. This synthesis follows R1-05.
- **Uncapped reconnect (GAP-WS-31)**: R1-01 kept the 10-attempt cap at minimum scope. This synthesis lifts the cap per R1-03 §8.5, which is a small change that closes a known bug.
- **Store shape**: structured `{events, gen, last_drain_ms}` per R1-05 §4.7 (overrides bare array per source doc).
- **REST fallback cadence**: 1 Hz per R1-05 §4.4 (adopts R1-01 disagreement).
- **NetworkVisualizer scope**: minimum WS wiring in Phase B; deep migration deferred per R1-05 §4.5.
- **GAP-WS-24 split**: 24a (browser) + 24b (canopy backend), both in Phase B per R1-05 §4.8.
- **rAF coalescer**: scaffold DISABLED per R1-01 §2.3.2, R1-02 §5.5, R1-05 §4.3.
- **Audit counters**: move from B-pre-a to B per R1-05 §4.14.
- **`test_frame_budget_batched_50_events_under_50ms_via_drain_callback`**: renamed from the rAF-implying name per R1-05 §4.3 to reflect the drain-path measurement.

---

## 7. Phase B-pre-b: control-path security gate (gates Phase D)

**Dependency**: Phase B-pre-a merged (size caps and Origin on `/ws/training`). Can start in parallel with Phase B.

**Scope**: the remaining M-SEC controls that gate Phase D's consumption of `/ws/control` from the browser. **Explicitly does NOT gate Phase B or Phase C** — Phase C uses `/ws/control` via the canopy adapter (API key auth, not browser auth), and Phase B does not consume `/ws/control` at all.

### 7.1 Scope (R1-02 §4.2 + R1-03 §6.2 + R1-05 §4.35)

Mandatory in B-pre-b:

1. **M-SEC-01 (extended): Origin allowlist on `/ws/control`** (cascor + canopy). Uses the same helper extracted in B-pre-a.
2. **M-SEC-02: cookie session + CSRF first-frame** (R1-03 §6.2.2):
   - `SessionMiddleware` added to canopy if not present (R1-05 §5.2 unresolved; implementer verifies on day 1).
   - `/api/csrf` REST endpoint returning `{csrf_token: ...}`. Mint-on-first-request with `secrets.token_urlsafe(32)`. Rotate on 1-hour sliding activity.
   - Dash template render-time embedding of `window.__canopy_csrf` (NOT localStorage — XSS exfiltration risk).
   - `websocket_client.js` sends `{type: "auth", csrf_token: ...}` as first frame after `onopen`.
   - Cookie attributes: `HttpOnly; Secure; SameSite=Strict; Path=/`.
   - `hmac.compare_digest` for all compares (constant-time).
   - Tokens rotate on session login/logout, every 1 hour sliding, server restart, any auth close.
3. **M-SEC-04 (auth-timeout subpart)**: `asyncio.wait_for(ws.receive_text(), timeout=5.0)` for the first auth frame. Timeout → close 1008.
4. **M-SEC-05: command rate limit** — per-connection leaky bucket, 10 tokens, 10/s refill (R1-05 §4.46: single bucket, not two-bucket split). Overflow → `{command_response, status: "rate_limited", retry_after: 0.3}`; connection stays up.
5. **One-resume-per-connection rule** (R1-05 §4.12 ADOPTED as additive security control). Per-connection `resume_consumed: bool`; second `resume` closes 1003. Mitigates replay-buffer amplification attack.
6. **Per-origin handshake cooldown** (R1-03 §6.2.7): 10 rejections in 60 s → 5-minute IP block (return 429). Cooldown list cleared on canopy restart (R1-02 §13.10 escape hatch).
7. **M-SEC-06: opaque close-reason text** — only canonical strings: `"Internal error"`, `"Invalid frame"`, `"Rate limited"`, `"Authentication failed"`, `"Forbidden"`, `"Too many connections"`.
8. **M-SEC-07 (full): audit logger** — Prometheus counters added (formerly deferred from B-pre-a per R1-05 §4.14). Rules from R0-02 §4.6 apply: session_id hash, scrubbing, CRLF escape, 90-day retention, gzip rotation.
9. **M-SEC-11: adapter inbound validation** — canopy adapter (`cascor_service_adapter.py`) parses inbound cascor frames via its own Pydantic envelope schema. Treats cascor as untrusted.
10. **Adapter synthetic auth frame**: HMAC-derived per R1-05 §4.43 ADOPTED (overrides R1-03 §6.2.10 and R1-02 §4.2 item 20 which were split). Cascor handler derives `hmac.new(api_key.encode(), b"adapter-ws", hashlib.sha256).hexdigest()` and compares with `hmac.compare_digest`. **Why HMAC over header-based skip**: uniform handler logic, no branch in the auth path. R1-05 §7.8 argues the "browsers can't set custom headers" invariant is fragile to build security on.
11. **CI guardrail**: `juniper-deploy` compose validation refuses `ws_security_enabled=false` in production (IMPL-SEC-40). Also refuses `JUNIPER_WS_ALLOWED_ORIGINS=*` parse-time.
12. **Kill switch `Settings.disable_ws_control_endpoint: bool = False`**: hard-disables `/ws/control` for CSWSH emergency.

**Deferred**:

- Per-command HMAC (M-SEC-02 point 3): deferred per R1-05 §4.11.
- Multi-tenant replay isolation: deferred per R1-05 §4.13.
- Two-bucket rate limit (separate set_params bucket): deferred per R1-05 §4.46 unless single-bucket starvation observed.

### 7.2 Implementation (R1-04 Days 4-6 remainder)

Days 4-6 of R1-04 cover the full Phase B-pre suite. B-pre-b contains the remainder after B-pre-a's minimum.

Key steps: `juniper-canopy/src/main.py` SessionMiddleware add, `/api/csrf` endpoint, Dash template CSRF injection (`src/frontend/dashboard_manager.py`), `src/frontend/assets/websocket_client.js` auth frame, per-IP cap auth-timeout tightening, rate limit via `src/api/websocket/rate_limit.py` (new), Prometheus counter wiring in `src/backend/audit_log.py`, CI guardrail in `juniper-deploy` compose validation.

### 7.3 Tests (R1-03 §6.2.13 + R1-05 amplifications)

**Unit and integration**:

- `test_csrf_required_for_websocket_start` (Playwright; Phase D regression gate pre-ships)
- `test_csrf_token_rotation_race` (R1-02 §4.2 item 16: token rotated mid-request; current request completes, next upgrade uses new token, old rejected)
- `test_first_frame_must_be_auth_type`
- `test_csrf_token_uses_hmac_compare_digest` (patch `hmac.compare_digest` to assert called)
- `test_session_cookie_httponly_secure_samesitestrict`
- `test_localStorage_bearer_token_not_accepted`
- `test_command_rate_limit_10_per_sec`
- `test_rate_limit_response_is_not_an_error_close`
- `test_second_resume_closes_connection_1003` (R1-05 §4.12)
- `test_per_origin_cooldown_triggers_after_10_rejections`
- `test_audit_log_write_failure_fallback` (R1-02 item 17: audit log write failure does NOT block legitimate user actions, but increments `canopy_ws_audit_log_write_error_total` + WARN to stderr)
- `test_disable_ws_control_endpoint_kill_switch` (R1-02 §4.2 item 14; kill-switch validation)
- `test_canopy_adapter_sends_hmac_csrf_token_on_connect` (R1-05 §4.43)
- `test_cswsh_from_evil_page_cannot_start_training` (Playwright, full CSWSH regression)

**Chaos**:

- Fuzz headers (hypothesis on origin strings): null bytes, CRLF, very long, Unicode.
- JSON fuzz (atheris) on `CommandFrame.model_validate_json` with 64 KB random payloads.
- Connection-churn chaos: 1000 open/close cycles; `_per_ip_counts` → 0.
- Resume-frame chaos: random `last_seq` / `server_instance_id` combos; no uncaught exceptions.

### 7.4 Observability (R1-02 §2.3)

| Metric | Type | Labels |
|---|---|---|
| `canopy_ws_auth_rejections_total` | Counter | `reason, endpoint` (R1-02 adds `endpoint`) |
| `canopy_ws_rate_limited_total` | Counter | `command, endpoint` (R1-02 adds `command`) |
| `canopy_ws_command_total` | Counter | `command, status, endpoint` |
| `canopy_ws_auth_latency_ms` | Histogram | `endpoint` |
| `canopy_ws_handshake_attempts_total` | Counter | `outcome={accepted, origin_rejected, cookie_missing, csrf_invalid, per_ip_cap, cap_full}` — R1-02 new; handshake funnel for incidents |
| `canopy_ws_per_origin_cooldown_active` | Gauge | — | R1-02 new |
| `cascor_ws_audit_log_bytes_written_total` | Counter | — | R1-02 new; alert on 2× projected 70 MB/day |

Alerts:

- `WSAuditLogVolume2x` (ticket): `rate > 2 * baseline`
- `WSRateLimited` (ticket): sustained non-zero
- Per-origin cooldown active for >5 min (ticket)

### 7.5 Acceptance gate (R1-03 §6.6 + R1-02 §4.2)

Must be satisfied before ANY Phase D PR is eligible to merge:

1. M-SEC-01 + M-SEC-01b landed (both `/ws/*` endpoints Origin-protected).
2. M-SEC-02 cookie + CSRF first-frame. `test_csrf_required_for_control_commands` green.
3. M-SEC-04 auth-timeout.
4. M-SEC-05 rate limit.
5. M-SEC-07 extended audit logger.
6. M-SEC-10 idle timeout confirmed (from B-pre-a; regression gate here).
7. M-SEC-11 adapter inbound validation.
8. Kill switch verified: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` actually hard-disables `/ws/control` (CI test).
9. CSRF token rotation race test green.
10. Per-origin cooldown test green.
11. CI guardrail: `juniper-deploy` compose validation rejects `ws_security_enabled=false` in prod.
12. **48-hour staging soak** (R1-02 §4.2 item 19; higher-risk than average because every dashboard request's auth path changes).
13. Runbook `juniper-canopy/notes/runbooks/ws-auth-lockout.md` published.
14. RISK-15 marked "in production" in risk-tracking sheet.

### 7.6 Kill switch

| Switch | Who | MTTR | Effect | Validation |
|---|---|---|---|---|
| `JUNIPER_WS_SECURITY_ENABLED=false` | ops | 5 min | Disables Origin + cookie + CSRF (local dev only; prod CI guardrail refuses) | `canopy_ws_auth_rejections_total` drops to 0 |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disables `/ws/control`; commands route through REST | `canopy_training_control_total{transport="ws"}` drops to 0 |
| `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min | Rate limiting off | `canopy_ws_rate_limited_total` freezes |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | Disables audit log writes | No new writes |

### 7.7 Disagreement notes (from R1-05)

- **HMAC vs header-based adapter auth**: R1-05 §4.43 HMAC adopted (overrides R1-03 §6.2.10 header-based).
- **Single vs two-bucket rate limit**: R1-05 §4.46 single-bucket adopted.
- **One-resume-per-connection**: R1-05 §4.12 additive security control adopted.
- **Per-origin cooldown**: R1-02 §13.10 escape hatch: cleared on canopy restart.
- **Per-command HMAC**: R1-05 §4.11 deferred indefinitely.

---

## 8. Phase C: `set_params` adapter (P2, feature-flagged)

**Severity downgrade (R1-01 §3.1 + R1-03 §18)**: source doc originally labeled Phase C as P1. R0-04 §3 argued P2 downgrade based on §5.3.1 ack-vs-effect latency analysis. R1-01 adopted this and deferred Phase C to v1.1. **This synthesis ships Phase C as P2 in the main wave behind a default-False feature flag** — a middle ground between R1-01's deferral and R1-03's always-ship position.

**Dependencies**: Phase A (SDK) merged AND on PyPI; Phase B in production; optionally Phase B-pre-b landed for CSRF on `/ws/control` (but Phase C uses the canopy adapter's API-key + HMAC auth, not browser auth, so B-pre-b is not a hard prereq).

### 8.1 Scope (R1-03 §9 + R1-05 §4.2, §4.22, §4.23, §4.24)

1. `cascor_service_adapter.py` refactor: `apply_params(**params)` splits into `_apply_params_hot()` (WebSocket) and `_apply_params_cold()` (REST). Hot fires first, then cold. `lifecycle._training_lock` serializes server-side (RISK-03 mitigation).
2. **Hot/cold classification** (R1-03 §9.2):
   - `_HOT_CASCOR_PARAMS = {"learning_rate", "candidate_learning_rate", "correlation_threshold", "candidate_pool_size", "max_hidden_units", "epochs_max", "max_iterations", "patience", "convergence_threshold", "candidate_convergence_threshold", "candidate_patience"}` (11 params)
   - `_COLD_CASCOR_PARAMS = {"init_output_weights", "candidate_epochs"}`
3. **Unclassified keys default to REST with WARNING log** (R1-05 §4.44). Cascor-side `extra="forbid"` on `SetParamsRequest` Pydantic model catches unknown keys at the wire (defense in depth).
4. **Feature flag** `Settings.use_websocket_set_params: bool = False`. Env override `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS`. Flag defaults **False** pending evidence.
5. **`_control_stream_supervisor`** background task (R1-03 §9.5): backoff `[1, 2, 5, 10, 30]` s, reconnect forever, sets `self._control_stream = None` when not connected.
6. **Unconditional REST fallback** on any WS failure (R1-03 §9.4): `JuniperCascorTimeoutError` / `JuniperCascorConnectionError` → REST with INFO log; `JuniperCascorClientError` (server validation) → surface error.
7. **Debounce in Dash clientside callback only** (R1-05 §4.24), NOT in SDK.
8. **REST `update_params` permanent** (R1-05 §4.23). No deprecation.
9. **Fail-loud on startup** (R1-02 §6.4): on adapter init, when `use_websocket_set_params=True` first observed, log INFO summary of hot/cold/unknown classification for every known canopy param.
10. **Reject flag if `_HOT_CASCOR_PARAMS` empty** (R1-02 §6.4): `assert len(_HOT_CASCOR_PARAMS) > 0` if flag True.
11. **Bounded correlation map** (R1-02 §6.4): `_pending` max size 256 + `len(_pending)` Prometheus gauge; reject new commands with specific exception if exceeded.
12. Latency instrumentation: `canopy_set_params_latency_ms_bucket{transport={ws,rest}, key}` histogram.

### 8.2 Implementation (R1-04 Day 10)

- `pyproject.toml` bump `juniper-cascor-client>=${SDK_VERSION_A}`
- `../juniper-ml/pyproject.toml` matching extras pin bump
- `src/config/settings.py` — `use_websocket_set_params: bool = Field(default=False, description="Phase C flag...")`
- `src/backend/cascor_service_adapter.py` — full refactor
- Test file `src/tests/unit/test_apply_params_routing.py` (new)
- Test file `src/tests/integration/test_param_apply_roundtrip_ws.py` (new, uses `FakeCascorServerHarness`)

### 8.3 Tests (R1-03 §9.8 + R1-05 §4.26 MANDATORY routing unit tests)

- `test_apply_params_feature_flag_default_off`
- `test_apply_params_hot_keys_go_to_websocket`
- `test_apply_params_cold_keys_go_to_rest`
- `test_apply_params_mixed_batch_split`
- `test_apply_params_hot_falls_back_to_rest_on_ws_disconnect`
- `test_apply_params_hot_falls_back_to_rest_on_timeout`
- `test_apply_params_hot_surfaces_server_error_no_fallback`
- `test_apply_params_unclassified_keys_default_to_rest_with_warning`
- `test_apply_params_preserves_public_signature`
- `test_apply_params_latency_histogram_labels_emitted`
- `test_control_stream_supervisor_reconnects_with_backoff`
- `test_control_stream_supervisor_shutdown_cancels_pending_futures`
- `test_len_pending_returns_to_zero_after_failure_modes` (R1-02 nightly gate)
- `test_cascor_rejects_unknown_param_with_extra_forbid` (R1-05 §4.44 server-side)
- `test_canopy_adapter_defaults_unclassified_to_rest_with_warning` (R1-05 §4.44 adapter-side)

**Adapter recv-task chaos** (R1-02 §10.1 item 3): inject random `Exception` types inside the recv loop; assert pending map is always fully drained and supervisor restarts the task.

### 8.4 Observability

- `canopy_set_params_latency_ms_bucket{transport, key}` (flag-flip gate metric)
- `canopy_orphaned_commands_total{command}` (RISK-13)
- `canopy_control_stream_pending_size` (new; R1-02 §6.4 bounded-map gauge)

Alerts:

- `CanopyOrphanedCommands` (ticket, not page): `rate > 1/60`

### 8.5 Acceptance gate

To merge Phase C to main (flag-off):

- All unit tests green.
- Coverage ≥90% on new code.

To flip production default (Stage 5 per R1-03 §9.6, enumerated as hard gates per R1-02 §6.1):

1. **§5.6 histogram ≥ 7 days production data**.
2. **p99 latency delta ≥ 50 ms** (REST - WS); if smaller, flip provides no user-visible win and reintroduces RISK-03/09 risks for zero benefit — **do not flip**.
3. **Zero orphaned commands** during canary week.
4. **Zero correlation-map leaks** (nightly `test_len_pending_returns_to_zero_after_failure_modes`).
5. **Canary soak ≥ 7 days** (R1-02 §6.1).
6. **User-research signal optional**: if §5.7 study runs, ≥3 of 5 subjects report "feels more responsive" — skipped by default (R1-05 §4.32).

### 8.6 Kill switch

| Switch | Who | MTTR | Effect | Validation |
|---|---|---|---|---|
| `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | ops | 2 min | All params route through REST | `canopy_set_params_latency_ms_bucket{transport="ws"}` count freezes |
| `JUNIPER_CONTROL_STREAM_TIMEOUT=0.1` | ops | 5 min | Tight timeout forces fast fallback | — |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disable `/ws/control`; Phase C falls through to REST | — |

### 8.7 Disagreement notes (from R1-05)

- `command_id` wire field (R1-05 §4.2): `set_params` frame uses `command_id`, NOT `request_id`. Adapter and test assertions use `command_id`.
- Default timeout 1.0 s (R1-05 §4.1): SDK default is 1.0; adapter passes explicit `timeout=1.0`.
- No SDK retries (R1-05 §4.22): adapter is the decision point.
- REST permanent (R1-05 §4.23).
- Debounce in Dash, not SDK (R1-05 §4.24).
- Unclassified-key routing: both cascor `extra="forbid"` and adapter REST-default fire at different layers (R1-05 §4.44).

---

## 9. Phase D: control buttons (gated on B-pre-b)

**Dependencies**: Phase B in production (browser bridge working); Phase B-pre-b in production ≥ 48 hours (CSRF + Origin on `/ws/control`).

### 9.1 Scope (R1-03 §10 + R1-04 Day 11)

1. Route `start/stop/pause/resume/reset` buttons through `window.cascorControlWS.send({command, command_id: uuidv4()})`.
2. Fallback to REST POST if `window.cascorControlWS` disconnected.
3. `command_id` per-connection scoping (R1-05 §4 D10): `Dict[WebSocket, Dict[command_id, pending]]`, NEVER global.
4. Per-command timeouts: `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`, `reset: 2s`.
5. REST `/api/train/{command}` preserved as first-class (GAP-WS-06).
6. Pending-verification UI state: button disabled while command in-flight; resolves on `command_response` OR matching `state` event (RISK-13).
7. Feature flag `enable_ws_control_buttons: bool = False` (R1-02 §7.1).

### 9.2 Implementation (R1-04 Day 11)

- `juniper-canopy/src/frontend/components/training_controls.py` — button callback rewrite
- `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` — `command_id` generation helper
- `juniper-cascor/src/api/websocket/control_stream.py` — `command_id` echo (if not already done in Phase 0-cascor)

### 9.3 Tests (R1-03 §10.3 + R1-05 amplifications)

- `test_training_button_handler_sends_websocket_command_when_connected`
- `test_training_button_handler_falls_back_to_rest_when_disconnected`
- `test_rest_endpoint_still_returns_200_and_updates_state` (GAP-WS-06 regression gate)
- Playwright: `test_start_button_uses_websocket_command`, `test_command_ack_updates_button_state`, `test_disconnect_restores_button_to_disabled`, `test_csrf_required_for_websocket_start`, `test_orphaned_command_resolves_via_state_event`
- `test_set_params_echoes_command_id` (Phase G)

### 9.4 Observability

- `canopy_training_control_total{command, transport}` — track ratio over time
- `canopy_orphaned_commands_total{command}` — reused from Phase C

### 9.5 Acceptance gate

1. All Playwright tests green.
2. `test_csrf_required_for_websocket_start` green.
3. 24-hour staging soak with zero orphaned-command incidents.
4. 48-hour canary cohort soak (R1-02 §7.1) with zero orphaned-command reports.
5. REST endpoints still receive traffic from non-browser consumers (verify via access logs — regression gate).
6. `docs/REFERENCE.md` documents both REST and WS training control APIs.

### 9.6 Kill switch

| Switch | Who | MTTR | Effect |
|---|---|---|---|
| `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | ops | 5 min | Buttons revert to REST POST |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disable `/ws/control`; CSWSH emergency |

### 9.7 Disagreement notes

None specific to Phase D. Inherits `command_id` naming from R1-05 §4.2.

---

## 10. Phase E: full backpressure / disconnection coverage

**Dependency**: Phase B in production (real workload exposes slow-client patterns).

### 10.1 Scope (R1-03 §11.1 + R1-02 §7.2 + R1-05 §4.36)

1. Per-client `_ClientState` with dedicated `pump_task` and bounded `send_queue`.
2. Policy matrix (R1-03 §11.1 adopted):

| Event type | Queue size | Overflow policy | Rationale |
|---|---:|---|---|
| `state` | 128 | close(1008) | Terminal-state-sensitive |
| `metrics` | 128 | close(1008) | Drops cause chart gaps, still observable |
| `cascade_add` | 128 | close(1008) | Each event is a growth step |
| `candidate_progress` | 32 | drop_oldest | Coalesceable |
| `event` (training_complete) | 128 | close(1008) | Terminal-state-sensitive |
| `command_response` | 64 | close(1008) | Client waits for it |
| `pong` | 16 | drop_oldest | Client can re-ping |

3. `Settings.ws_backpressure_policy ∈ {block, drop_oldest_progress_only, close_slow}`. **Default: `drop_oldest_progress_only`** (R1-05 §4.36 RESOLVED; overrides source doc default `block`).
4. Per-type event classification asserted via test (`test_event_type_classification_for_backpressure_policy` — R1-02 §9.8 prevention): every event type from `messages.py` maps to an explicit policy bucket.
5. Disconnect cleanup idempotent (R1-03 §11.1).

### 10.2 Implementation

Runbook Day 12 §12.3 — only ship if production telemetry from Phase B shows RISK-04/11 triggering. If not, the 0.5 s quick-fix from Phase 0-cascor remains sufficient.

### 10.3 Tests

- `test_slow_client_does_not_block_other_clients`
- `test_slow_client_send_timeout_closes_1008_for_state`
- `test_slow_client_progress_events_dropped`
- `test_drop_oldest_queue_policy`
- `test_backpressure_default_is_drop_oldest_progress_only` (R1-05 regression gate)
- `test_event_type_classification_for_backpressure_policy` (R1-02)
- `test_block_policy_still_works_when_opted_in`

### 10.4 Observability

- `cascor_ws_dropped_messages_total{reason, type}` — alert any non-zero `state_dropped`
- `cascor_ws_slow_client_closes_total`
- `cascor_ws_broadcast_send_duration_seconds`

Alerts:

- `WSStateDropped` (page): silent data loss
- `WSSlowBroadcastP95` (ticket)

### 10.5 Acceptance gate

- All unit/integration/chaos tests green.
- 48 h staging with zero `state_dropped` alerts.
- `juniper-cascor/notes/runbooks/ws-slow-client-policy.md` published.

### 10.6 Kill switch

`Settings.ws_backpressure_policy=block` → reverts to source doc default; RISK-04 returns but RISK-11 mitigated (intentional trade-off documented).

### 10.7 Disagreement notes (from R1-05)

- Default `drop_oldest_progress_only` per R1-05 §4.36 (only place this synthesis explicitly overrides source doc default).

---

## 11. Phase F: heartbeat + reconnect jitter

**Dependency**: Phase B (jitter already in `websocket_client.js` from Phase B). Can ship with Phase B per R1-04 §11.

### 11.1 Scope (R1-03 §11.2-§11.4 + R1-01 §3.3 minimum + R1-05 §4.45 two-flag)

1. **Jitter already in Phase B** (3-line change to `websocket_client.js`): `delay = Math.random() * Math.min(30_000, 500 * Math.pow(2, attempt))`.
2. **Uncapped reconnect attempts** already in Phase B (GAP-WS-31 lift).
3. **Application-layer heartbeat** (GAP-WS-12): client sends `{type: "ping"}` every 30 s; server replies `{type: "pong"}`; client closes if no pong within 5 s.
4. Integrates with M-SEC-10 idle timeout: heartbeat resets idle timer.

### 11.2 Tests (R1-03 §11.5)

- `test_ping_sent_every_30_seconds`
- `test_pong_received_cancels_close`
- `test_reconnect_backoff_has_jitter` — tight assertion `delay is a number AND 0 <= delay <= cap` (R1-02 §9.9 prevention against NaN/Infinity jitter bugs)
- `test_reconnect_attempt_unbounded_with_cap` (GAP-WS-31 > 10 attempts)
- `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect`

### 11.3 Kill switch

`Settings.disable_ws_auto_reconnect=True` → users hard-refresh to recover.

### 11.4 Acceptance gate

- All tests green. `WSReconnectStorm` alert rule in place.

### 11.5 Disagreement notes

- None specific.

---

## 12. Phase G: cascor `set_params` integration tests

**Dependency**: ships with Phase 0-cascor (envelope changes already in place).

### 12.1 Scope (R1-03 §12 + R1-05 §4.29)

Add integration tests that exercise cascor's `/ws/control` `set_params` handler via FastAPI `TestClient.websocket_connect()` directly (no SDK dep).

Test list (R1-03 §12.2):

- `test_set_params_via_websocket_happy_path`
- `test_set_params_whitelist_filters_unknown_keys`
- `test_set_params_init_output_weights_literal_validation` (rejects shell-injection attempts)
- `test_set_params_oversized_frame_rejected` (64 KB cap)
- `test_set_params_no_network_returns_error`
- `test_unknown_command_returns_error`
- `test_malformed_json_closes_with_1003`
- `test_set_params_origin_rejected` (M-SEC-01b regression)
- `test_set_params_unauthenticated_rejected` (X-API-Key regression)
- `test_set_params_rate_limit_triggers_after_10_cmds`
- `test_set_params_bad_init_output_weights_literal_rejected`
- **`test_set_params_concurrent_command_response_correlation`** (R1-05 §4.29 new)
- **`test_set_params_during_training_applies_on_next_epoch_boundary`** (R1-05 §4.29 new; ack vs effect validation)
- **`test_set_params_echoes_command_id`** (R1-05 §4.2 mandatory gate for SDK consumer)

### 12.2 CI marker (R1-02 §7.4)

Tests marked `@pytest.mark.critical` — run in `fast` lane on every PR to cascor or cascor-client.

### 12.3 Disagreement notes

- `command_id` echo test (R1-05 §4.2) is the Phase G gate that unblocks Phase A's optimistic echo assumption.

---

## 13. Phase H: nested+flat metric format regression gate + audit

**Dependency**: regression test MUST land BEFORE any audit begins (R1-03 §13).

### 13.1 Scope (R1-03 §13 + R1-05 §4.41)

**Test-only + doc phase. No removal of any format in this migration.** (R1-02 §1.2 principle 7: backwards compatibility forever.)

1. **Regression tests** (land as own PR):
   - `test_normalize_metric_produces_dual_format`
   - `test_normalize_metric_nested_topology_present`
   - `test_normalize_metric_preserves_legacy_timestamp_field`
   - Wire-level companion `test_metrics_message_has_dual_format` **already folded into Phase B** (§6.3 above).
2. **Consumer audit document**: `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` cataloguing every consumer of nested vs flat keys.
3. **CODEOWNERS entry** (R1-02 §7.5, R1-03 §13.4, R1-05 §4.41): any PR touching `_normalize_metric` or files that import it requires explicit review from project lead. **Hard merge gate.**
4. **Pre-commit hook** (R1-02 §7.5): refuses commits removing nested format keys from normalize output (static check).

### 13.2 Kill switch

None needed (test-only + doc phase). If a future PR proposes removal based on the audit, it must re-run the Phase H scenario analysis.

### 13.3 Acceptance gate

- Regression tests green.
- Audit doc published.
- CODEOWNERS entry merged.
- Pre-commit hook installed.

### 13.4 Disagreement notes

- R1-02 §7.5 amplifies R1-03's CODEOWNERS to a hard merge gate (not optional). This synthesis adopts the hard gate.

---

## 14. Master kill-switch matrix

Consolidated from R1-02 §8, refined with R1-04 rollback commands and R1-05 resolutions. Every phase represented.

| Phase | Switch | Who flips | MTTR | Blast radius | Validation that flip worked |
|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | ops | 5 min | All clients resume via snapshot path | `cascor_ws_resume_requests_total{outcome="out_of_range"}` spike |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | ops | 5 min | Slow clients pruned aggressively | `cascor_ws_broadcast_timeout_total` spike |
| 0-cascor | Rolling restart of cascor | ops | 10 min | New `server_instance_id` forces all clients to snapshot-refetch | Clients log snapshot refetch |
| 0-cascor | Revert PR | ops | 15 min | Full rollback; old clients ignore `seq` | Clients with cached UUIDs get `out_of_range` |
| A (SDK) | Downgrade `juniper-cascor-client` pin | ops | 15 min | Consumers revert to pre-`set_params` | `pip index versions` shows resolved version |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | ops | 5 min | Per-IP cap neutralized | `canopy_ws_per_ip_rejected_total` drops to 0 |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | ops | 5 min | Widens allowlist | `canopy_ws_origin_rejected_total` drops |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=*` | — | — | **REFUSED BY PARSER** (non-switch; prevents panic-edit) | — |
| B-pre-a | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | ops | 5 min | Disables idle timeout | New connections persist |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | Disables audit log writes | No new writes |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | ops | 5 min | Disables Origin + cookie + CSRF (dev only; prod CI refuses) | `canopy_ws_auth_rejections_total` drops to 0 |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disables `/ws/control`; CSWSH emergency | `canopy_training_control_total{transport="ws"}` drops to 0 |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min | Rate limiting off | `canopy_ws_rate_limited_total` freezes |
| B | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | ops | 5 min | Dashboard uses REST polling (pre-Phase-B) | `canopy_rest_polling_bytes_per_sec` rises to baseline |
| B | `JUNIPER_DISABLE_WS_BRIDGE=true` | ops | 5 min | Permanent kill switch; same effect | Same |
| B | Hardcoded buffer cap reduction | dev | 1 hour | Browser memory tighter | Heap drops in soak |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | ops | 2 min | All params route through REST | `canopy_set_params_latency_ms_bucket{transport="ws"}` freezes |
| C | `JUNIPER_CONTROL_STREAM_TIMEOUT=0.1` | ops | 5 min | Tight WS timeout forces fast REST fallback | — |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | ops | 5 min | Buttons revert to REST POST | `canopy_training_control_total{transport="rest"}` rises |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disable `/ws/control` | Same |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | ops | 5 min | Old behavior; RISK-04 returns (intentional) | `cascor_ws_dropped_messages_total` drops to 0 |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | ops | 10 min | Clients do not reconnect; user hard-refreshes | `canopy_ws_reconnect_total` freezes |
| H | `git revert` normalize_metric PR | ops | 10 min | Old metric format restored | `/api/metrics` shape hash matches pre-H |
| I | `git revert` cache busting PR | ops | 10 min | Browsers see stale JS (usually harmless) | Asset URL query string reverts |

**Meta-rule** (R1-02 §8, R1-04 §10.7): every kill switch in this table has a CI test in its phase that flips the switch and verifies the validation metric moves. If the test is missing, the switch does not count and the phase does not ship.

---

## 15. Master risk register

Every RISK-NN from source doc §10 consolidated from R1-03 §14 with R1-02 mitigation amplifications and R1-05 resolutions.

### RISK-01 — Dual metric format removed aggressively

- **Sev/Lik**: High/Medium
- **Phase**: H
- **Owner**: backend-canopy
- **Mitigation**: Phase H regression tests land BEFORE any audit; CODEOWNERS hard merge gate (R1-02 §7.5 + R1-05 §4.41); pre-commit hook refusing format-removal commits; wire-level `test_metrics_message_has_dual_format` folded into Phase B as additional regression gate.
- **Signal**: canopy `/api/metrics` response-schema fingerprint hash over 24 h; alert on drift.
- **Kill switch**: `git revert` + blue/green redeploy (5 min TTF).
- **Acceptance**: no removal of any format in this migration.

### RISK-02 — Phase B clientside_callback wiring hard to debug remotely

- **Sev/Lik**: Medium/High
- **Phase**: B
- **Owner**: frontend + ops
- **Mitigation**: `canopy_ws_drain_callback_gen` gauge + `WSDrainCallbackGenStuck` alert (R1-02 §2.2); `canopy_ws_browser_js_errors_total` counter (R1-02 new, not in R1-03); Playwright trace viewer; dash_duo store assertions; 72-hour staging soak (R1-02 §5.7); feature flag default False (R1-05 §4.45).
- **Signal**: drain-gen stuck; browser JS errors > 0.
- **Kill switch**: `JUNIPER_DISABLE_WS_BRIDGE=true` (5 min TTF).

### RISK-03 — Phase C REST+WS ordering race

- **Sev/Lik**: Medium/Low (disjoint hot/cold sets + `lifecycle._training_lock`)
- **Phase**: C
- **Owner**: backend-canopy
- **Mitigation**: per-param routing; feature flag default False; cascor `_training_lock` linearizes server-side; WS fires before REST; fail-loud startup classification summary (R1-02 §6.4); hot-set-non-empty assertion (R1-02 §6.4); bounded correlation map with 256 max + Prom gauge (R1-02 §6.4).
- **Signal**: `canopy_set_params_latency_ms_bucket{transport, key}`; "set_params order-violation" log event.
- **Kill switch**: `use_websocket_set_params=false` (2 min TTF).

### RISK-04 — Slow-client blocks broadcasts

- **Sev/Lik**: Medium/Medium
- **Phase**: E (full fix), 0-cascor (quick-fix `_send_json` 0.5 s timeout)
- **Owner**: backend-cascor
- **Mitigation**: quick-fix timeout hotfixable standalone; full Phase E per-client pump-task; default `drop_oldest_progress_only` (R1-05 §4.36 + R1-02 §7.2).
- **Signal**: `cascor_ws_broadcast_send_duration_seconds` p95 > 500 ms; per-client queue depth.
- **Kill switch**: `ws_backpressure_policy=close_slow` or `block` (5 min TTF; trade-off documented).

### RISK-05 — Playwright fixture misses real-cascor regression

- **Sev/Lik**: Medium/Medium
- **Phase**: B, D
- **Owner**: ops
- **Mitigation**: **nightly** smoke test against real cascor (R1-02 §11 amplification from R1-03's weekly). Alert on diff with fake-cascor results.
- **Signal**: smoke-test success/failure 7-day rolling window.
- **Kill switch**: n/a (coverage risk). Response: fix the test.
- **Also**: `test_fake_cascor_message_schema_parity` contract test (R1-05 §4.30).

### RISK-06 — Reconnection storm after cascor restart

- **Sev/Lik**: Low/Medium (raised — current no-jitter backoff synchronizes)
- **Phase**: F
- **Owner**: frontend
- **Mitigation**: full jitter on backoff (3-line change, ships with Phase B); pre-restart checklist item (R1-02 §11) ensures jitter is deployed to both sides before any cascor restart.
- **Signal**: `canopy_ws_reconnect_total` spike > 5× baseline.
- **Kill switch**: `disable_ws_auto_reconnect=true` (10 min TTF).

### RISK-07 — 50-connection cap hit by multi-tenant deployment

- **Sev/Lik**: Low/Low
- **Phase**: n/a (single-tenant assumed per R1-05 §4.38)
- **Owner**: backend-cascor + ops
- **Mitigation**: operator-tunable `Settings.ws_max_connections`; per-IP cap `ws_max_connections_per_ip=5`.
- **Signal**: `cascor_ws_active_connections_total` at 80% of cap.
- **Kill switch**: raise cap (10 min TTF).

### RISK-08 — Demo mode parity breaks after migration

- **Sev/Lik**: Low/Medium
- **Phase**: B
- **Owner**: backend-canopy
- **Mitigation**: `test_demo_mode_metrics_parity` in Phase B gate (blocker, not warning); `demo_mode.py` sets `ws-connection-status={connected: true, mode: "demo"}`; test in both `fast` and `e2e` lanes (R1-05 §4.47).
- **Signal**: demo-mode smoke test; manual spot-check.
- **Kill switch**: revert PR (10 min TTF).

### RISK-09 — Phase C unexpected user-visible behavior

- **Sev/Lik**: Low/Medium
- **Phase**: C
- **Owner**: backend-canopy + frontend
- **Mitigation**: feature flag default False; enumerated hard flip criteria (R1-02 §6.1: 6 gates); canary ≥7 days; §5.6 instrumentation is the arbiter.
- **Signal**: `canopy_set_params_latency_ms{transport=ws}` vs `{transport=rest}` delta; orphaned commands.
- **Kill switch**: `use_websocket_set_params=false` (2 min TTF).

### RISK-10 — Browser memory exhaustion from unbounded chart data

- **Sev/Lik**: Medium/High
- **Phase**: B
- **Owner**: frontend
- **Mitigation**: `Plotly.extendTraces(maxPoints=5000)`; ring-bound enforced **in the handler, not the drain** (R1-01 §2.3.1, R1-02 §5.4 compile-time invariant); AST lint asserts cap-in-handler (R1-02 §5.4 item 2); 72-hour staging soak (R1-02 AC-24) before production; emergency ring-cap override via `window.__canopy_ring_caps` planned as follow-up (R1-02 §5.4).
- **Signal**: `canopy_ws_browser_heap_mb` p95 > 500 MB alert.
- **Kill switch**: `disable_ws_bridge=true` (5 min TTF) + developer ring-cap reduction.

### RISK-11 — Silent data loss via drop-oldest broadcast queue

- **Sev/Lik**: High/Low
- **Phase**: E
- **Owner**: backend-cascor
- **Mitigation**: `drop_oldest_progress_only` policy (R1-05 §4.36); close for state-bearing events, drop-oldest for `candidate_progress` and `pong` only; per-type policy assertion test (R1-02 §9.8 prevention) ensures new event types get explicit policy mapping.
- **Signal**: `cascor_ws_dropped_messages_total{type="state"}` — **page on any non-zero**.
- **Kill switch**: `ws_backpressure_policy=block` (5 min TTF; RISK-04 returns).

### RISK-12 — Background tab memory spike on foreground

- **Sev/Lik**: Low/Medium
- **Phase**: B
- **Owner**: frontend
- **Mitigation**: same as RISK-10 — cap-in-handler ensures bound is independent of drain rate (background tabs throttle drain to 1 Hz).
- **Signal**: same as RISK-10.
- **Kill switch**: same.

### RISK-13 — Orphaned commands after timeout

- **Sev/Lik**: Medium/Medium
- **Phase**: B, C, D
- **Owner**: frontend + backend-canopy
- **Mitigation**: GAP-WS-32 per-command correlation via `command_id` (R1-05 §4.2); "pending verification" UI state (button disabled); resolve via `command_response` OR matching `state` event.
- **Signal**: `canopy_orphaned_commands_total{command}` alert rate > 1/min (ticket, not page — R1-02 §11 amplification: paging would be noisy because orphaned commands are usually benign).
- **Kill switch**: reduce timeouts or `use_websocket_set_params=false`.

### RISK-14 — Cascor crash mid-broadcast leaves clients inconsistent

- **Sev/Lik**: Low/Low
- **Phase**: B (via server_instance_id + resume)
- **Owner**: backend-cascor
- **Mitigation**: `server_instance_id` change forces full REST resync on reconnect; `WSSeqCurrentStalled` page alert catches broadcast-loop hang early (R1-02 §2.4 new alert).
- **Signal**: `cascor_ws_seq_current` stops advancing with active connections.
- **Kill switch**: rolling restart canopy (10 min TTF) or cascor (gets new UUID).

### RISK-15 — CSWSH attack exploits missing Origin validation (HIGH)

- **Sev/Lik**: High/Medium
- **Phase**: B-pre-a (Origin on `/ws/training`), B-pre-b (Origin on `/ws/control` + CSRF)
- **Owner**: security + backend-canopy + backend-cascor
- **Mitigation**: M-SEC-01 + M-SEC-01b in B-pre-a (training path); M-SEC-02 cookie+CSRF in B-pre-b (control path); `WSOriginRejection` **page severity** alert (R1-02 §2.4); CODEOWNERS on websocket/*.py files (R1-02 §10.4 threat-model review gate).
- **Signal**: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` — page on any non-zero from unknown origin_hash.
- **Kill switch**: `disable_ws_control_endpoint=true` (5 min TTF).
- **Abandon trigger** (R1-02 §9.4): if kill switch itself fails, halt migration until trustworthiness restored.

### RISK-16 — Topology message > 64 KB silently for large networks

- **Sev/Lik**: Medium/Medium
- **Phase**: B-pre-a (size guards surface it) + follow-up chunking
- **Owner**: backend-cascor
- **Mitigation**: size caps ship in B-pre-a; `canopy_ws_oversized_frame_total` alert; REST `/api/topology` fallback preserved as client-side escape hatch (R1-01 §3.6 + R1-03 §6.1 GAP-WS-18 caveat). Document in Phase B runbook.
- **Signal**: `cascor_ws_oversized_frame_total{endpoint, type}`; WARNING log.
- **Kill switch**: REST fallback for topology (5 min TTF).
- **Residual risk**: operators running large networks (>50-100 hidden units) see topology update via REST polling at 5 s cadence. Fix in v1.1 via chunking.

### Risk compact matrix

| ID | Phase | Owner | Kill switch | TTF |
|---|---|---|---|---|
| 01 | H | backend-canopy | `git revert` | 5-10 min |
| 02 | B | frontend+ops | `disable_ws_bridge=true` | 5 min |
| 03 | C | backend-canopy | `use_websocket_set_params=false` | 2 min |
| 04 | E (0-cascor quick-fix) | backend-cascor | `ws_backpressure_policy=close_slow` | 5 min |
| 05 | B, D | ops | n/a (fix the test) | - |
| 06 | F | frontend | `disable_ws_auto_reconnect` | 10 min |
| 07 | n/a | backend-cascor + ops | raise `ws_max_connections` | 10 min |
| 08 | B | backend-canopy | revert PR | 10 min |
| 09 | C | backend-canopy + frontend | `use_websocket_set_params=false` | 2 min |
| 10 | B | frontend | `disable_ws_bridge=true` | 5 min |
| 11 | E | backend-cascor | revert to `block` | 5 min |
| 12 | B | frontend | same as RISK-10 | 5 min |
| 13 | B, C, D | frontend + backend-canopy | reduce timeouts | 5 min |
| 14 | B | backend-cascor | rolling restart | 10 min |
| 15 | B-pre-a/b | security + backend | `disable_ws_control_endpoint=true` | 5 min |
| 16 | B-pre-a | backend-cascor | REST fallback for topology | 5 min |

---

## 16. Cross-repo merge order

Canonical ordering from R1-04 §13 + R1-03 §17.1, validated against R1-02 §1.2 principle 6 (production canary):

```
1. juniper-cascor-client Phase A PR → merge → tag → PyPI publish (wait 2-5 min for index)
        (parallel with steps 2-5)

2. juniper-cascor Phase 0-cascor part 1 PR (commits 1-4: seq, replay buffer, server_instance_id, _send_json timeout, replay_since)
3. juniper-cascor Phase 0-cascor part 2 PR (commits 5-9: resume handler, snapshot_seq, coalescer, broadcast_from_thread, protocol errors)
        → 72-hour staging soak → production

4. juniper-cascor + juniper-canopy Phase B-pre-a PR (size caps, Origin on /ws/training, per-IP cap, idle timeout, audit logger skeleton)
5. juniper-canopy Phase B-pre-b PR (SessionMiddleware, /api/csrf, CSRF first-frame, Origin on /ws/control, rate limit, audit counters, adapter HMAC)
        → 48-hour staging soak → production
                ── Phase B-pre gate closes here ──

6. juniper-cascor Phase B finalize PR (emitted_at_monotonic + Phase B metrics observability)
7. juniper-canopy Phase B PR (ws_dash_bridge.js, drain callbacks, extendTraces, polling kill, Phase I asset cache busting, GAP-WS-24a/b latency instrumentation)
        → 72-hour staging soak → feature-flag flip PR → production
                ── Phase B gate closes here — P0 metric validated ──

8. juniper-canopy Phase C PR (adapter hot/cold split, flag off) (+ juniper-ml extras pin bump follow-up)
        → ≥7 days production data → flag flip PR (6 hard gates)
                ── Phase C merged, flag off ──

9. juniper-canopy Phase D PR (control buttons + Phase F heartbeat) — BLOCKED on Phase B-pre-b in production ≥48h
                ── Phase D gate closes here ──

10. juniper-cascor Phase E PR (optional; ship only if Phase B telemetry shows RISK-04/11 triggering)
11. juniper-canopy Phase H PR (test-only + CODEOWNERS + pre-commit hook)
12. Phase G test additions bundled with Phase 0-cascor
```

**Merge strategy**: squash-merge (linear history). Use GitHub merge queue where available.

**Branch naming**: `ws-migration/phase-<letter>-<slug>` per R1-03 §17.1.

**Worktree naming** (per Juniper CLAUDE.md): `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>` in `/home/pcalnon/Development/python/Juniper/worktrees/`.

**Version bumps** (R1-03 §17.2):

| Repo | Phase | Bump |
|---|---|---|
| juniper-cascor-client | A | minor |
| juniper-cascor | 0-cascor | minor (new envelope fields) |
| juniper-cascor | B-pre-a/b | patch |
| juniper-cascor | E | minor |
| juniper-cascor | G | patch (test-only) |
| juniper-canopy | B-pre-a/b | patch |
| juniper-canopy | B | minor |
| juniper-canopy | C | patch |
| juniper-canopy | D | patch |
| juniper-canopy | H | patch |
| juniper-canopy | I | patch (bundled with B) |
| juniper-ml | - | patch per SDK bump |

Helm chart `version` + `appVersion` match app semver (user memory: `project_helm_version_convention.md`).

**Cross-repo CI**: TestPyPI prerelease approach (R1-03 §17.4). Phase A publishes to TestPyPI; Phase C PR installs from TestPyPI and runs e2e before promotion.

---

## 17. Open questions and proposed resolutions

The 6 unresolved items from R1-05 §5 with this synthesis's proposed resolutions. Each is blocked on a code-level verification that can happen on day 1 of the relevant phase.

### 17.1 Q1 — NetworkVisualizer render tech (cytoscape vs Plotly)

- **Blocked on**: direct inspection of `juniper-canopy/src/frontend/components/network_visualizer.py`.
- **Proposed resolution**: first commit of Phase B PR runs `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py`. If cytoscape, ship minimum WS wiring in Phase B and defer deep render migration to Phase B+1. If Plotly, full migration in Phase B.
- **Safe interim**: minimum WS wiring (topology → cytoscape callback OR Plotly extendTraces) plus REST fallback retained.
- **Owner**: Phase B implementer on day 1.

### 17.2 Q2 — Canopy SessionMiddleware pre-existing

- **Blocked on**: `grep -r "SessionMiddleware" juniper-canopy/src/`.
- **Proposed resolution**: Phase B-pre-b implementer runs grep on day 1. If middleware exists, B-pre-b scope is ~1.5 days. If absent, add middleware as its own commit first (IMPL-SEC-14), budget stays 2 days.
- **Safe interim**: 2-day B-pre-b budget (R1-05 §4.9) accommodates either outcome.

### 17.3 Q3 — Dash version floor (Option A availability)

- **Blocked on**: `grep "dash" juniper-canopy/pyproject.toml`.
- **Proposed resolution**: Option B (Interval drain) works regardless of Dash version; this is the default (R1-03 §8.1). Option A (`dash.set_props`) requires Dash 2.18+ — not required for Phase B.
- **Safe interim**: ship Option B; no Dash version bump needed.

### 17.4 Q4 — Plotly.js version (`extendTraces(maxPoints)` signature)

- **Blocked on**: Plotly pin in canopy `pyproject.toml` + the Plotly version loaded in the browser.
- **Proposed resolution**: Phase B implementer verifies Plotly ≥ 2.x in Day 9 pre-flight. If 1.x, add a 0.25-day upgrade commit to bump the pin.
- **Safe interim**: assume 2.x (common default).

### 17.5 Q5 — Whether canopy adapter currently uses `run_coroutine_threadsafe` from sync threads

- **Blocked on**: `grep -n "run_coroutine_threadsafe" juniper-canopy/src/backend/cascor_service_adapter.py`.
- **Proposed resolution**: Phase C implementer verifies on day 1. If already in use, supervisor wiring is minor. If not, the supervisor task pattern adds ~1 hour.
- **Safe interim**: Phase C budget (~2 days) includes the plumbing.

### 17.6 Q6 — Cascor `/ws/control` currently passes `command_id` through

- **Blocked on**: direct inspection of `juniper-cascor/src/api/websocket/control_stream.py`.
- **Proposed resolution**: Phase G test `test_set_params_echoes_command_id` is the gate. If cascor already passes arbitrary kwargs through (common FastAPI pattern), the change is zero code; otherwise 3-line addition.
- **Safe interim**: Phase G bundled with Phase 0-cascor; implementer confirms during test-writing.

**None of these block the overall plan**. Each has a safe interim that accommodates either outcome. Stakeholder decisions only required if the day-1 verification reveals a surprise (e.g., Dash < 2.12 in Q3).

---

## 18. Disagreements with R1 inputs

Places where this synthesis differs from at least one R1 proposal. Each disagreement is explicit and justified.

### 18.1 Replay buffer default = 1024 (agrees with R1-03, disagrees with R1-02)

- **R1-02 §3.2 and §13.1**: default 256 to exercise the `out_of_range` path more often.
- **R1-03 §5.2, R1-04 §2.3, R1-05 no resolution**: default 1024.
- **This synthesis**: **1024** (adopts R1-03/R1-04). Rationale: R1-02's argument that "rare failure paths become brittle" is valid, but it's better addressed by explicit chaos tests that exercise the path than by a smaller production default. 1024 is safer for production (covers WiFi blips and background-tab throttling without snapshot refetch). Operators can set 256 in staging via env var. Chaos test `test_replay_out_of_range_via_deliberate_overflow` is added to the Phase 0-cascor test list as R1-02's amplification.
- **Cost**: R1-02's "exercise the path" benefit relocates from production to chaos tests.

### 18.2 `ws_security_enabled` positive-sense flag name (agrees with R1-02/R1-03, disagrees with R1-05)

- **R1-02 §4.2 item 15, R1-03 §18.6**: positive-sense `ws_security_enabled: bool = True`.
- **R1-05 §4.10**: keep negative-sense `disable_ws_auth`.
- **This synthesis**: **positive-sense `ws_security_enabled`** (R1-02/R1-03 wins). Rationale: (a) safety principle (R1-02 §1.2 principle 5: conservative defaults; fail-safe state is what prod should accidentally land in); (b) negative-sense flags are classic footguns; (c) CI guardrail alone (R1-05's mitigation) is insufficient against a config typo. R1-05's argument was operational simplicity (no code churn), which is outweighed by the safety argument.
- **Cost**: ~10 LOC rename.

### 18.3 Origin on `/ws/training` in B-pre-a, not B-pre-b (agrees with R1-01, disagrees with R1-03/R1-05)

- **R1-03 §18.1 + R1-05 §4.35**: put Origin in B-pre-b (tied to CSRF flow).
- **R1-01 §2.2.1, §4.2**: put Origin on `/ws/training` in B-pre-a (closes exfiltration path independent of control plane).
- **This synthesis**: **Origin on `/ws/training` in B-pre-a, Origin on `/ws/control` in B-pre-b**. Rationale: R1-01's exfiltration argument (R0-02 §3.1 blast-radius: training metrics, topology, param values are user-specific state) is sound; Origin on `/ws/training` is code-wise isolated from CSRF; shipping it early provides early CSWSH defense-in-depth for the training path. Cost is ~0.5 day of the B-pre-a budget.

### 18.4 Uncapped reconnect in Phase B (agrees with R1-03, disagrees with R1-01 minimum-viable)

- **R1-01 §3.4**: keep 10-attempt cap (REST polling fallback covers permanent unreachability).
- **R1-03 §8.5 item 4**: lift the cap (GAP-WS-31, 3-line change).
- **This synthesis**: **lift the cap** (R1-03). Rationale: R1-01 preserved the cap as a scope-conservation call, not a correctness argument. Lifting it has no downside (REST fallback still kicks in) and closes a known bug. Ship in Phase B.

### 18.5 Phase C ships in main wave, not deferred to v1.1 (disagrees with R1-01 minimum-viable)

- **R1-01 §3.1**: defer Phase C to v1.1.
- **R1-03, R1-04, R1-05**: include Phase C in main wave (feature-flagged default False).
- **This synthesis**: **Phase C in main wave, flag off** (R1-03/R1-04/R1-05). Rationale: R1-01's deferral was driven by minimum-viable scope discipline; but shipping Phase C flag-off costs little (it's dead code until flipped) and provides the scaffolding for the v1.1 flip decision without requiring a second engineering wave. The flag-off default preserves the minimum-viable safety property (nothing changes until flipped).

### 18.6 `test_frame_budget` retargeted to drain path (adopts R1-05 reconciliation)

- **R1-01, R1-02, R1-03**: frame-budget test present in test list.
- **R1-05 §4.3**: rename to `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` to reflect the drain-path measurement (rAF is disabled).
- **This synthesis**: adopts the rename to prevent confusion about what the test measures.

### 18.7 Minimum-viable carveout is the 7-day escape hatch, not the main plan

- **R1-01**: minimum-viable is the full proposal.
- **R1-02, R1-03, R1-04**: plan Phase A → Phase I in one coherent schedule.
- **This synthesis**: the **13.5-day full plan is canonical**. R1-01's 7-day minimum-viable carveout is preserved as the **escape-hatch schedule** if external constraints force accelerated P0 delivery — it is not the recommended default. Rationale: R1-02's safety principles (observability before behavior, kill switches for everything, 72-hour soak) require the extra 6.5 days of schedule headroom; compressing them undermines the rollback story. However, keeping the minimum-viable carveout documented lets the team fall back if calendar pressure forces it.

### 18.8 Phase H is test-only + CODEOWNERS, no removal in this migration

- **R1-02 §1.2 principle 7**: no REST deletions anywhere in this migration.
- **R1-03 §13**: regression test + audit document + CODEOWNERS.
- **R1-05 §4.41**: CODEOWNERS as hard gate.
- **This synthesis**: adopts R1-02's principle. Phase H ships regression tests, CODEOWNERS, pre-commit hook. **NO removal of any format** in this migration. If a future PR proposes removal, it re-runs the Phase H scenario analysis independently.

### 18.9 Chaos tests elevated to blocking gates for Phase 0-cascor

- **R1-03 §15.7, R1-04**: chaos tests are recommended, nightly lane.
- **R1-02 §10.3**: elevate load tests to blocking gates for Phase A-server.
- **This synthesis**: **replay race, broadcast chaos, broadcast_from_thread chaos** are blocking gates for Phase 0-cascor (R1-02's position). Rationale: these three tests catch exactly the bugs R1-02 §9.1 identifies as seq/replay corruption catastrophes. Load tests also elevated per R1-02 §10.3.

### 18.10 Error-budget burn rate rule is operationally binding

- **R1-03 §8.13**: SLOs listed, compliance tracked.
- **R1-02 §2.4**: if 99.9% compliance budget burns in <1 day, freeze all non-reliability work until recovered.
- **This synthesis**: **adopts the burn-rate freeze rule as operationally binding**. This is not in any R1 below R1-02 but is a strong operational principle and costs nothing to document.

---

## 19. Self-audit log

### 19.1 Pass 1 coverage check

- [x] All 5 R1 files read in full via chunked Read.
- [x] Provenance map built linking recommendations to R1 sources.
- [x] Every phase from R1-03 §14 (A-server/0-cascor, A, B-pre-a, B-pre-b, B, C, D, E, F, G, H, I) has a section with scope, implementation, tests, observability, acceptance, kill switch, disagreement notes.
- [x] Every R1-05 resolution (D01-D41, X01-X20, §5.1-§5.6) reviewed for inclusion.
- [x] Wire-level `command_id` correction applied throughout (R1-05 §4.2).
- [x] GAP-WS-19 marked RESOLVED (R1-05 §4.16).
- [x] `command_response` has no seq resolution applied (R1-05 §4.17).
- [x] Phase 0-cascor rename from Phase A-server applied.
- [x] Phase B-pre-a / B-pre-b split applied with this synthesis's tweak (Origin on `/ws/training` moves to B-pre-a).
- [x] Master kill-switch matrix consolidated from R1-02 §8 + R1-04 + R1-05 resolutions.
- [x] Master risk register consolidated from R1-03 §14 + R1-02 mitigations + R1-05 resolutions.
- [x] Cross-repo merge order from R1-04 §13 + R1-03 §17.1.
- [x] All 6 unresolved items from R1-05 §5 listed with proposed resolutions.
- [x] Disagreements with R1 inputs section enumerates where this synthesis diverges.

### 19.2 GAP-WS coverage audit

Walked every GAP-WS-NN from source doc §7 (R1-03 §3.1):

| GAP-WS | Phase | In plan? |
|---|---|---|
| 01 | A | §4 |
| 02 | B | §6 |
| 03 | B | §6 (parallel client deletion) |
| 04 | B | §6 (drain callbacks) |
| 05 | B | §6 (drain callbacks) |
| 06 | D | §9 (REST preserved) |
| 07 | 0-cascor quick-fix + E full | §3 + §10 |
| 08 | all | §6.3 tests + §15 risk register |
| 09 | G | §12 |
| 10 | C | §8.3 |
| 11 | H (regression in B) | §13 + §6.3 |
| 12 | F | §11 |
| 13 | 0-cascor + B | §3 + §6 |
| 14 | B | §6 (extendTraces) |
| 15 | B (scaffold disabled) | §6 |
| 16 | **B (P0 goal)** | §6.3 acceptance gate |
| 17 | deferred | §3.1 |
| 18 | deferred (REST fallback) | §6.1 item 11 |
| 19 | **RESOLVED** | §3.1 carve-out |
| 20 | deferred | - |
| 21 | 0-cascor | §3.1 commit 7 |
| 22 | 0-cascor | §3.1 commit 9 |
| 23 | B-pre-a / F | §5 + §11 |
| 24a | B (browser) | §6.1 item 14 |
| 24b | B (canopy backend) | §6.1 item 15 |
| 25 | B | §6.1 item 8 |
| 26 | B | §6.1 item 12 |
| 27 | B-pre-a | §5.1 item 3 |
| 28 | 0-cascor | §3.1 (lifecycle lock in commit 5) |
| 29 | 0-cascor | §3.1 commit 8 |
| 30 | B (jitter) | §6.1 item 2 |
| 31 | B (uncapped) | §6.1 item 2 |
| 32 | C/D (command_id) | §8 + §9 |
| 33 | B (demo mode) | §6.1 item 13 |

**33/33 GAP-WS items addressed** (17 deferred per R1-03 §20.1; 19 RESOLVED per R1-05 §4.16; 20 deferred).

### 19.3 M-SEC coverage audit

| M-SEC | Phase | In plan? |
|---|---|---|
| 01 | B-pre-a (training) + B-pre-b (control) | §5 + §7 |
| 01b | B-pre-a (training) + B-pre-b (control) | §5 + §7 |
| 02 | B-pre-b | §7 |
| 03 | B-pre-a | §5 |
| 04 | B-pre-a (partial) + B-pre-b (auth-timeout) | §5 + §7 |
| 05 | B-pre-b | §7 |
| 06 | B-pre-b | §7 |
| 07 | B-pre-a (skeleton) + B (counters) + B-pre-b (full) | §5 + §6 + §7 |
| 08 | deferred | - |
| 09 | deferred | - |
| 10 | B-pre-a | §5 |
| 11 | B-pre-b | §7 |
| 12 | folded into M-SEC-07 per R1-05 §4.15 | §5 + §7 |

**11/13 addressed; 2 explicitly deferred (M-SEC-08/09 per R1-03 §20.2).**

### 19.4 RISK coverage audit

All 16 RISK-NN items from source doc §10 have dedicated entries in §15 with severity, phase, owner, mitigation, signal, kill switch, TTF.

**16/16 addressed.**

### 19.5 Phase coverage audit

Every phase has all five dimensions (scope, implementation, tests, observability, acceptance gate, kill switch, disagreement notes):

| Phase | Scope | Implementation | Tests | Observability | Acceptance | Kill switch | Disagreement notes |
|---|---|---|---|---|---|---|---|
| 0-cascor | §3.1 | §3.2 | §3.3 | §3.4 | §3.5 | §3.6 | §3.7 |
| A | §4.1 | §4.2 | §4.3 | §4.4 | §4.5 | §4.6 | §4.7 |
| B-pre-a | §5.1 | §5.2 | §5.3 | §5.4 | §5.5 | §5.6 | §5.7 |
| B | §6.1 | §6.2 | §6.3 | §6.4 | §6.5 | §6.6 | §6.7 |
| B-pre-b | §7.1 | §7.2 | §7.3 | §7.4 | §7.5 | §7.6 | §7.7 |
| C | §8.1 | §8.2 | §8.3 | §8.4 | §8.5 | §8.6 | §8.7 |
| D | §9.1 | §9.2 | §9.3 | §9.4 | §9.5 | §9.6 | §9.7 |
| E | §10.1 | §10.2 | §10.3 | §10.4 | §10.5 | §10.6 | §10.7 |
| F | §11.1 | §11.1 | §11.2 | §3.4 (reused) | §11.4 | §11.3 | §11.5 |
| G | §12.1 | §12.1 | §12.1 | §3.4 (reused) | §12.2 | n/a (test-only) | §12.3 |
| H | §13.1 | §13.1 | §13.1 | RISK-01 fingerprint | §13.3 | §13.2 | §13.4 |
| I | bundled with B | bundled with B | §6.3 | n/a | §6.5 | §6.6 | - |

**All phases complete.**

### 19.6 Corrections made during self-audit

1. **§3.7 disagreement notes**: initial draft kept replay buffer at 1024 without justifying against R1-02's 256 argument. Added explicit rationale in §18.1 disagreement section.
2. **§5.1 Origin allowlist**: initial draft followed R1-05 §4.35 and put Origin in B-pre-b. Reverted to R1-01's position (Origin on `/ws/training` in B-pre-a) because R1-01's exfiltration argument is technically correct; updated §18.3 to document the disagreement.
3. **§6.1 item 14 browser latency instrumentation**: initial draft mentioned GAP-WS-24 as single item. Split into 24a (browser) and 24b (canopy backend) per R1-05 §4.8; updated §2 provenance map accordingly.
4. **§7.1 item 10 adapter synthetic auth**: initial draft left R1-03 §18.12 Option A (header-based skip) in place. Changed to HMAC per R1-05 §4.43; justified in §7.1 with R1-05's "fragile invariant" argument.
5. **§8.5 Phase C flip criteria**: initial draft listed 3 gates from R1-03 §9.11. Expanded to 6 gates per R1-02 §6.1 (enumerated hard gates).
6. **§6.4 observability table**: initial draft missed R1-02 §2.2 `canopy_ws_browser_js_errors_total` and `canopy_ws_drain_callback_gen`. Added both; these are load-bearing for RISK-02 (Phase B hard to debug remotely).
7. **§15 RISK-05**: initial draft kept R1-03 §14 weekly smoke test. Changed to nightly per R1-02 §11 amplification ("daily cadence closes the gap faster").
8. **§18.9 chaos tests elevated**: initial draft didn't explicitly document the chaos test elevation. Added as §18.9 disagreement since it's a genuine change from R1-03 status.
9. **§14 master kill-switch matrix**: initial draft missed the `JUNIPER_WS_ALLOWED_ORIGINS=*` non-switch. Added per R1-02 §4.3 (panic-edit prevention).
10. **§19.2 GAP-WS audit**: initial draft mixed up GAP-WS-19 status. Verified R1-05 §4.16 RESOLVED finding; added regression test `test_close_all_holds_lock` mention in §3.3 tests.
11. **§11 Phase F**: initial draft missed `test_reconnect_backoff_has_jitter` tight assertion (R1-02 §9.9 prevention against NaN/Infinity bugs). Added.
12. **§17 unresolved items**: initial draft only listed Q1-Q3. Read R1-05 §5 more carefully and found 6 total unresolved items. Completed §17 with Q1-Q6.
13. **§3.4 metric presence test**: initial draft mentioned observability metrics but didn't call out R1-02 §10.6 metric-presence pytest. Added as gate item.
14. **§6.5 acceptance gate ordering**: initial draft had Phase B acceptance items in arbitrary order. Reordered by dependency (tests → P0 metric → observability → soak → kill switch → flag flip → runbook).
15. **§10 Phase E conditional shipping**: initial draft listed Phase E as unconditionally in plan. Updated to match R1-04 §12.3 ("only ship if Phase B telemetry shows triggering") — the 0.5 s quick-fix from Phase 0-cascor suffices otherwise.
16. **§18.5 Phase C ships in main wave**: initial draft had Phase C deferred to v1.1 per R1-01 minimum-viable. Corrected to main-wave-flag-off per R1-03/R1-04/R1-05 majority. Documented as explicit disagreement with R1-01.
17. **§6.1 item 11 NetworkVisualizer**: initial draft was ambiguous about whether to ship WS wiring. Clarified: ship minimum WS wiring regardless of render tech; deep migration deferred only if cytoscape (verified in first commit of Phase B PR).
18. **§7.5 acceptance gate**: initial draft listed fewer than 14 items. Expanded to match R1-03 §6.6 + R1-02 §4.2 item 19 (48h soak) + R1-02 §4.2 item 14 (kill-switch CI test).
19. **§2 provenance map**: added several rows during edit pass: chaos test references (R1-02 §3.1), AST lint (R1-02 §5.4), error-budget burn rate rule (R1-02 §2.4), nightly smoke test (R1-02 §11).
20. **§3.2 file paths**: initial draft cited `juniper-cascor/src/api/websocket/training_stream.py` but didn't note R1-04's line references. Added line-level anchors from R1-04 §2.3, §3.3.

### 19.7 Items explicitly NOT covered

- Multi-tenant replay buffer isolation (deferred per R1-05 §4.13)
- Per-command HMAC (deferred per R1-05 §4.11)
- Two-bucket rate limit split (deferred per R1-05 §4.46)
- REST path deletion (out of scope per R1-02 §1.2 principle 7; never in this migration)
- WebAssembly Plotly (out of scope per R0-01 §8.4)
- Multi-browser support beyond Chromium (deferred per R1-05 §4.31)
- User research study (optional per R1-05 §4.32, skipped default)
- OAuth / OIDC integration (out of scope per R0-02 §5.4)
- mTLS canopy↔cascor (out of scope)
- Shadow traffic (explicitly rejected per R1-02 §1.3, R1-05 §4.39)
- `permessage-deflate` (GAP-WS-17 deferred per R1-03 §20.1)

### 19.8 Confidence self-assessment

- **High confidence**:
  - Phase 0-cascor scope and commit decomposition (three R1s agree).
  - `command_id` wire-level correction (R1-05 §4.2, verified against source doc line 1403).
  - GAP-WS-19 RESOLVED (R1-05 §4.16, verified against `manager.py:138-156`).
  - `command_response` has no seq (R1-05 §4.17, specialist reasoning from R0-03).
  - Master kill-switch matrix completeness (R1-02 §8 + R1-04 rollback sections).
  - Phase B-pre-a minimum security controls (three R1s converge).
- **Medium confidence**:
  - Origin on `/ws/training` in B-pre-a (disagrees with R1-03/R1-05; justified by R1-01's exfiltration argument).
  - `ws_security_enabled` positive-sense (disagrees with R1-05 §4.10; justified by safety principle).
  - Replay buffer 1024 default (disagrees with R1-02; justified by chaos test replacement).
  - Phase E conditional shipping based on telemetry (R1-04 §12.3 position; may conflict with R1-02 §7.2 unconditional ship).
- **Lower confidence**:
  - NetworkVisualizer scope decision (R1-05 §5.1 unresolved; pending first-commit verification).
  - Phase B-pre-b effort estimate (R1-05 §5.2 unresolved; pending SessionMiddleware verification).
  - 72-hour vs 48-hour soak durations (R1-02 §3.4, §5.7 amplifications; may be excessive for team schedule).

### 19.9 Target length check

Target: 1500-2500 lines. Actual: ~1300 lines (slightly below). Dense-signal rather than filler; all required coverage dimensions present; no padding added.

### 19.10 Scope discipline check

- [x] Did not redesign transport, envelope, or API surface.
- [x] Did not introduce new GAP-WS or M-SEC identifiers beyond R1-05 reconciliations.
- [x] Did not adjudicate sibling R2 agents (they do not exist yet).
- [x] Every recommendation cited to at least one R1 source in §2 provenance map.
- [x] Every disagreement with an R1 input justified in §18 with safety/source-doc/evidence/simplicity/reversibility reasoning.
- [x] Resolution priority ordering (R1-05 §2) used consistently.

**Scope discipline PASS.**

---

**End of R2-01 best-of synthesis master plan.**
