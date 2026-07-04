# Round 0 Proposal R0-05: Testing & Validation Strategy

**Specialization**: pytest, dash_duo, Playwright, integration & latency testing
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope

This proposal defines the **end-to-end test and validation strategy** for the WebSocket migration laid out in the source architecture doc (hereafter "the arch doc"). It covers:

1. How the existing `FakeCascorClient` (REST/in-process) and `FakeCascorTrainingStream`/`FakeCascorControlStream` (WS/in-process) fakes are to be **reused** and **minimally extended** — NOT replaced.
2. Unit test patterns per-repo (cascor server, juniper-cascor-client SDK, canopy).
3. Integration test patterns across the cascor↔cascor-client↔canopy boundary.
4. Browser test patterns (`dash_duo` + Playwright) per §8 of the arch doc.
5. Latency measurement validation for §5.5 frame budget and §5.6 production latency plan.
6. Phase-by-phase test gates mapped to §9 A/B-pre/B/C/D/E/F/G/H/I.
7. Reconnection + replay regression scenarios (§6.4, §6.5).
8. Security regression tests (§2.9 M-SEC-01..07).
9. CI integration (fast vs e2e vs nightly split, trace artifact policy).
10. Coverage-threshold maintenance under the project's 80% standard.
11. Negative / adversarial tests (malformed frames, oversized frames, schema confusion, double-ack, out-of-order seq).

Explicitly **out of scope** for this proposal:

- Internal design of the broadcaster, replay buffer, drain callbacks, or `set_params` API (other R0 agents' jobs).
- Visual regression / pixel diff (noted §8.7 as out of scope for this work).
- Multi-browser matrix (Playwright's Firefox/WebKit support; defer to §11 Open Question 2).
- Real performance benchmarks against a real cascor (noted §8.7).
- User research latency validation (§5.7 — separate 1-2 week calendar item).

Where this proposal disagrees with the arch doc, disagreements are collected in §14 below with justification.

---

## 2. Source-doc cross-references

Key anchors in the arch doc this proposal relies on:

| Ref | Topic | Used for |
|---|---|---|
| §0 Conventions | Verdict labels, severity, GAP-WS-NN ID scheme | Pytest marker naming, gate messages |
| §1.3 Caveat | Dash clientside_callback subscribe impossibility; Option B Interval drain | `dash_duo` assertion targets |
| §2.2 | `WebSocketManager` lock contract (`_lock` vs `_training_lock`) | Concurrency unit tests |
| §2.9.1 Threat model | CSWSH, CSRF over WS, per-IP DoS, param-injection | Security regression test list (§7 below) |
| §2.9.2 M-SEC-01..07 | Origin allowlist, cookie+CSRF, per-frame size, per-IP cap, rate-limit | Test surface for Phase B-pre gate |
| §3.x | Bidirectional message schemas | Schema validation tests |
| §5.5 Frame budget | 16.67 ms budget decomposition | Unit-level assertion targets |
| §5.6 Production latency plan | `emitted_at_monotonic`, histogram buckets, `/api/ws_latency` endpoint | CI latency-recording tests |
| §6.4 Disconnection taxonomy | Close codes 1001/1006/1008/1009/1013/4001 | Reconnect unit tests |
| §6.5 Reconnect+replay protocol | Sequence numbers, `server_instance_id`, 1024-event replay buffer, `resume`/`resume_failed` | Replay integration tests |
| §6.5.1 Thread-safety contract | `_seq_lock` option 2 recommendation | Cascor concurrency tests |
| §6.5.2 Snapshot→live atomicity | `snapshot_seq` returned atomically with snapshot | Canopy snapshot-fetch test |
| §6.5.3 Edge cases | Older cascor without `resume`, localStorage clear, tab-close grace | Negative tests |
| §7 GAP-WS-01..33 | Each gap has severity, location, target state | Per-gap acceptance tests |
| §8 Browser-side verification strategy | Playwright + `dash_duo` recommendation | Entire browser test plan |
| §8.4 Test fixture architecture | Fixture layout sketch | Adapted in §5-§6 below |
| §8.5 `FakeCascorServerHarness` sketch | FastAPI wrapper over existing fakes | Reference for R0-03 agent to implement |
| §8.5.1 | CI runtime / marker split / trace artifact policy | Adopted verbatim in §10 below |
| §8.6 CI integration | GitHub Actions job template | Adopted in §10 below |
| §8.8 Verification matrix | Per-phase verification targets | Adopted in §9 below |
| §9.1..9.10 Phase plans | Each phase has a test plan | Expanded in §9 below |
| §10 RISK-02, RISK-05, RISK-08, RISK-13 | Test-plan mitigations | Mapped in §13 below |
| §11 Open Question 2 | Browser compatibility | Kept as open decision |
| §11 Open Question 7 | User research before Phase C | Kept as open decision |

---

## 3. Existing test baseline

Before inventing new fixtures, the proposal inventories what already exists and conforms to the arch doc's mandate to "reuse the existing fakes."

### 3.1 FakeCascorClient

**Location**: `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py` (1071 lines).

**Covered API surface** (verified against source 2026-04-11):

- `__init__(scenario, base_url, api_key)` with scenarios: `idle`, `two_spiral_training`, `xor_converged`, `empty`, `error_prone`.
- REST-shaped methods mirroring the real `JuniperCascorClient`: `get_training_status()`, `get_metrics()`, `get_metrics_history(count)`, `get_network_topology()`, `get_dataset()`, `start_training()`, `stop_training()`, `pause_training()`, `resume_training()`, `reset()`, `create_network()`, `update_params(params)` (REST PATCH analogue).
- Test helpers: `advance_epoch(n)`, `set_state(state)`, `error_prone` exception injection.
- Thread safety: module-level `threading.Lock`.
- Context manager protocol (`with FakeCascorClient(...) as client:`).
- Already consumed by ~12 files in `juniper-canopy/src/tests/{unit,integration,regression}` via `pytest.importorskip("juniper_cascor_client.testing")` or direct import.

**What it does NOT cover today**:

- Has no WebSocket `set_params` command path (GAP-WS-01 is the reason this proposal exists in part).
- Has no sequence-number plumbing (GAP-WS-13) because the real code lacks it.
- Has no server-instance-id advertising or `resume`/`resume_failed` handling.
- Does not enforce `X-API-Key` — tests can pass without auth credentials that the real client would be missing (arch doc §2.9.1 calls this a P2 test-fixture threat).
- Does not coordinate with a running uvicorn harness; it is purely in-process.

### 3.2 FakeCascorTrainingStream (+ FakeCascorControlStream)

**Location**: `juniper-cascor-client/juniper_cascor_client/testing/fake_ws_client.py` (222 lines).

**Covered API surface**:

- `FakeCascorTrainingStream(messages, delay, base_url, api_key)` — accepts a pre-baked list of messages and/or allows programmatic injection.
- `connect(path)` / `disconnect()` / `__aenter__` / `__aexit__`.
- `stream()` — async iterator yielding dicts (same API shape as real client).
- `listen()` — callback-driven dispatch via `on_metrics`, `on_state`, `on_topology`, `on_cascade_add`, `on_event`.
- `send_command(command, params)` — records commands in a `_sent_commands` list for assertion.
- `inject_message(message)` — test helper to push events dynamically (works before OR after `connect()`).
- Uses `asyncio.Queue` as the internal buffer; queue `None` sentinel ends the stream.

**What it does NOT cover today**:

- **No `set_params` method** — `send_command()` is generic; tests have to push `{"command": "set_params", ...}` directly.
- **No `command_response` correlation** — the fake does not synthesize a reply that a real caller would `await`. If Phase A introduces per-command correlation IDs (arch doc §9.1 test_set_params_concurrent_correlation), the fake needs a way to auto-reply with a matching `command_response`.
- **No sequence numbers** — fake envelopes do not populate `seq`.
- **No `connection_established` with `server_instance_id`** — the fake never emits this frame; tests depending on the reconnect protocol (§6.5) need it.
- **No reconnect / replay** — `disconnect()` terminates the stream cleanly; there is no way to simulate "client reconnects with `last_seq=N` and expects replayed events."
- **No real network** — it is a pure in-process fake. Browser tests (Playwright/`dash_duo`) cannot use it directly; they need a real uvicorn server (see §8.5 of arch doc, `FakeCascorServerHarness`).
- **Auth is not enforced** — constructor accepts `api_key` but never validates it.

### 3.3 What to reuse, what to extend

**Reuse as-is** (no changes required):

- Scenario presets (`two_spiral_training`, `xor_converged`, `empty`, `error_prone`) for setting up fixture state. These already drive canopy's integration tests and cover the realistic shapes we need.
- `inject_message()` for unit-level tests that need to push a specific event sequence.
- `_sent_commands` list for assertion on which commands the code-under-test issued.
- `error_prone` scenario for fault injection into canopy tests (e.g., "what happens when `get_metrics()` randomly raises?").

**Minimal additive extensions** (tracked here; implementation is a different R0 agent's job — R0-03 SDK agent, probably):

1. **`on_command(command_name, handler)` on the fake control stream** — matches the pattern in arch doc §8.5 `FakeCascorServerHarness.on_command`. Tests register `async def handler(msg, ws): ...` to simulate a server replying to a specific command with a specific `command_response`. This is how the `set_params` happy-path test verifies the round trip.
2. **Auto-`command_response` scaffolding** — when the fake receives a command it recognizes (e.g., `start`, `stop`, `set_params`), it emits a matching `{type: "command_response", data: {command, status: "success", result: {...}}}` to the stream unless `on_command` overrides it. Required so Phase A unit tests do not need to manually script the reply for every happy-path assertion.
3. **Optional sequence-number mode** — `FakeCascorTrainingStream(with_seq=True)` toggles the fake to append a monotonic `seq` to every outgoing envelope. Default is `False` to avoid breaking existing ~12 callers.
4. **Optional `connection_established` emission** — when `with_seq=True`, the fake's `connect()` prepends a `connection_established` frame with a fabricated `server_instance_id` (`uuid4()`) and `connections=1`. Configurable so tests can force a specific UUID for replay scenarios.
5. **`simulate_disconnect()` / `simulate_reconnect(last_seq)` helpers** — simulate a mid-stream TCP drop (puts `None` sentinel, then re-enters `connect()` with a new queue) and verifies the `resume` handshake. The fake's `resume` path either replays events from a synthetic ring buffer or returns `resume_failed` with the configured reason.
6. **Auth enforcement mode** — `FakeCascorTrainingStream(enforce_api_key=True)` causes `connect()` to raise `JuniperCascorAuthError` if `api_key` is None or mismatched. Tests enable this to verify canopy's adapter correctly forwards credentials.

**New fixture (not an extension of existing)**:

- **`FakeCascorServerHarness`** — the arch doc §8.5 sketch. This is a thin FastAPI/uvicorn wrapper that **composes** the existing `FakeCascorClient` and `FakeCascorTrainingStream` state. It should live in `juniper-cascor-client/juniper_cascor_client/testing/server_harness.py` so it is installable via `pip install juniper-cascor-client[testing]` and reusable by canopy. **Do not duplicate fake state** in the harness; it must delegate to the existing classes for scenario responses, command recording, and message injection. This fixture is required for Playwright and `dash_duo` tests and for any integration test where a real TCP socket must be opened.

**Explicitly NOT doing**:

- Creating a brand-new `FakeCascorWSV2` class. The reuse mandate in the arch doc is specifically to avoid forking the fake. Any new behavior goes into the existing class behind a feature flag.
- Creating a separate "test-only" subclass hierarchy. Any test helper that a fixture needs should be added to the existing class, tagged with a docstring note "test helper — not present on real `CascorTrainingStream`" (existing pattern per `inject_message`'s docstring).

---

## 4. Unit test plan

Unit tests are the fastest, cheapest gate and must cover every production-code path introduced by each phase. Goal: **every new function gets at least one happy-path and one negative-path unit test**, with the 80% coverage threshold enforced via the existing `[tool.coverage.report] fail_under=80` pattern in each repo's `pyproject.toml`.

### 4.1 Cascor server (broadcaster, replay buffer, control handlers)

**Files touched**: `juniper-cascor/src/tests/unit/api/test_websocket_manager.py` (existing, extend), `test_websocket_control.py` (existing, extend), `test_websocket_messages.py` (existing, extend); new file `test_websocket_replay_buffer.py`.

**Phase B-pre (security + size limits)**:

- `test_origin_allowlist_accepts_configured_origin` — `Settings.allowed_origins=["http://localhost:8050"]`, set `Origin: http://localhost:8050`, handshake succeeds.
- `test_origin_allowlist_rejects_third_party` — same setup, `Origin: http://evil.example`, handshake HTTP 403 BEFORE upgrade (not WS close).
- `test_origin_allowlist_rejects_missing_origin` — no `Origin` header, handshake HTTP 403.
- `test_origin_header_case_insensitive_host` — per RFC 6454 origin matching.
- `test_per_frame_size_limit_1009` — send a 65 KB frame over `/ws/control`, assert close code 1009.
- `test_per_ip_connection_cap` — open 5 connections from `127.0.0.1` with `ws_max_connections_per_ip=5`, assert 6th is rejected with code 1013.
- `test_per_ip_counter_decrements_on_disconnect` — cycle 10 connect/disconnect pairs, assert `_per_ip_counts["127.0.0.1"]` returns to 0 after each.
- `test_per_ip_counter_decrements_on_exception` — exception inside the handler still decrements the counter (covers §2.9 `finally` requirement).
- `test_auth_timeout_closes_1008` — connect, send no frames for 6 s, assert server closes with 1008.
- `test_command_rate_limit_10_per_sec` — burst 20 commands in 100 ms, assert first 10 succeed, remainder respond with `{status: "rate_limited"}`.
- `test_opaque_auth_failure_reason` — both missing and invalid API key produce identical `"Authentication failed"` close reason string.

**Phase B (sequence numbers + replay buffer)**:

- `test_seq_monotonically_increases_per_connection` — broadcast 100 messages, verify `seq` field strictly increases by 1.
- `test_seq_increments_across_all_message_types` — interleave metrics, state, topology, cascade_add, event; verify single global counter.
- `test_seq_is_assigned_on_loop_thread` — call `broadcast_from_thread` from a `threading.Thread`, verify the `seq` is assigned on the asyncio loop thread (not the caller's thread); assert via a `loop.call_soon_threadsafe` sentinel.
- `test_seq_lock_does_not_block_broadcast_iteration` — Option 2 from §6.5.1: `_seq_lock` is separate from `_lock`; a slow client holding `_lock` during broadcast should NOT block seq assignment for subsequent events. Validated by mocking the broadcast to sleep 500 ms and asserting new seqs are still assigned within 10 ms.
- `test_replay_buffer_bounded_1024` — push 2000 events, assert `len(replay_buffer) == 1024` and oldest is purged.
- `test_replay_buffer_copy_under_lock` — test that `resume` handler copies the ring under `_seq_lock` before iterating (pattern from §6.5.1).
- `test_resume_replays_events_after_last_seq` — client sends `resume {last_seq: 500, server_instance_id: "<uuid>"}`, server replays seq 501..current.
- `test_resume_failed_out_of_range` — client sends `last_seq < current_seq - 1024`, server responds `resume_failed {reason: "out_of_range"}`.
- `test_resume_failed_server_restarted` — client sends `server_instance_id` that does not match current, server responds `resume_failed {reason: "server_restarted"}`.
- `test_connection_established_advertises_instance_id` — first frame sent to a new client contains `server_instance_id` (UUID4) AND `server_start_time` (float).
- `test_snapshot_seq_atomic_with_state_read` — REST snapshot endpoint returns `snapshot_seq` from under the same `_seq_lock`; test that `snapshot_seq >= max(state.events.seq)`.
- `test_broadcast_from_thread_discards_exception_without_leaking_seq` — arch doc §6.5.1 shutdown race: `run_coroutine_threadsafe` raises, no seq is consumed.

**Phase E (backpressure)**:

- `test_slow_client_does_not_block_other_clients` — connect two clients, first holds its receive queue (simulates slow client), assert second receives broadcast within 10 ms.
- `test_slow_client_send_timeout_closes_1008_for_state` — with `ws_backpressure_policy=close_slow`, a slow client on a `state` event gets close 1008.
- `test_slow_client_progress_events_dropped` — `candidate_progress` events are dropped (not close) per §10 RISK-11.
- `test_drop_oldest_queue_policy` — when `ws_backpressure_policy=drop_oldest`, oldest `candidate_progress` is dropped, not newest.
- `test_backpressure_default_is_block` — default policy preserves existing behavior until next major version.

**Phase G (set_params integration on cascor side)**:

Arch doc §9.8 specifies this uses FastAPI's `TestClient.websocket_connect()` directly, NOT the SDK. That is the right decision; cascor has no dependency on `juniper-cascor-client` and testing the wire protocol server-side must not go through the SDK interpretation.

- `test_set_params_via_websocket_happy_path` — already specified in §9.8.
- `test_set_params_whitelist_filters_unknown_keys` — already specified.
- `test_set_params_init_output_weights_literal_validation` — already specified; Pydantic `Literal["zero", "random"]` rejects `"random; rm -rf /"`.
- `test_set_params_oversized_frame_rejected` — already specified; 64 KB cap.
- `test_set_params_no_network_returns_error` — already specified.
- `test_unknown_command_returns_error` — GAP-WS-22 per-reviewer requirement.
- `test_malformed_json_closes_with_1003` — GAP-WS-22.
- **Addition beyond §9.8**: `test_set_params_concurrent_command_response_correlation` — two `set_params` commands in flight (via two WebSocket clients), assert each `command_response` goes to the right connection. (Single-connection correlation is the SDK's job in §9.1.)
- **Addition**: `test_set_params_during_training_applies_on_next_epoch_boundary` — verify cascor applies the param change on the next epoch; this is the "ack vs effect" distinction from §5.3.1 that Phase C C/C ships behind a feature flag.

### 4.2 juniper-cascor-client (set_params, reconnect, correlation)

**Files touched**: `juniper-cascor-client/tests/test_fake_ws_client.py` (existing, extend); new `tests/test_ws_client_set_params.py`; `tests/test_ws_client_reconnect.py`.

**Phase A (set_params SDK)**:

All six tests listed in arch doc §9.1 are adopted verbatim. Expanding each with assertion detail:

- `test_set_params_round_trip` — use `FakeCascorServerHarness.on_command("set_params", handler)` where `handler` sends back `{status: "success", result: {learning_rate: 0.005}}`. The SDK's `set_params({"learning_rate": 0.005}, timeout=5.0)` returns `{"learning_rate": 0.005}`.
- `test_set_params_timeout` — `on_command("set_params", lambda msg, ws: asyncio.sleep(10))` — handler stalls, SDK's `await` times out after `timeout=0.1` and raises `CascorTimeoutError`.
- `test_set_params_validation_error` — `on_command` responds `{status: "error", error: "Invalid param"}`, SDK raises `CascorParamError`.
- `test_set_params_reconnection_queue` — client disconnects mid-send; behavior TBD by R0-03 agent (queue + retry OR fail-fast). Two variants of the test, one for each strategy, switched by the design decision.
- `test_set_params_concurrent_correlation` — fires two `set_params` in parallel via `asyncio.gather`, each command gets a unique `correlation_id`, each `command_response` carries the matching id, both callers receive their own result. Requires the SDK to implement per-command correlation IDs.
- `test_set_params_caller_cancellation` — `task = asyncio.create_task(client.set_params(...))`, then `task.cancel()`; assert the SDK's internal future map is cleaned up (no memory leak, no orphan coroutine).

**Phase F (heartbeat + reconnect jitter)**:

- `test_ping_sent_every_30_seconds` — fake server never replies; assert SDK closes connection after `ping_interval + pong_timeout`.
- `test_pong_received_cancels_close` — fake server replies with `pong`; connection stays open.
- `test_reconnect_backoff_has_jitter` — repeat 10 reconnect attempts, measure delays, assert std-dev > 0 (i.e., not deterministic).
- `test_reconnect_backoff_capped` — attempts 11-20 use capped delay, not unbounded exponential.
- `test_reconnect_attempt_unbounded_with_cap` — GAP-WS-31 specifies lifting the 10-attempt cap; assert attempts continue past 10 with capped delay, and log rate-limit on the attempt counter.

**Phase B (resume protocol, SDK side)**:

- `test_resume_sends_last_seq_on_reconnect` — client has received `seq=500`, reconnects, asserts first frame sent is `{type: "resume", data: {last_seq: 500, server_instance_id: "<uuid>"}}`.
- `test_resume_applies_replayed_events` — harness replays seq 501..510 on reconnect; client's `on_metrics` callback fires for each.
- `test_resume_handles_out_of_range_by_snapshot_fallback` — harness returns `resume_failed {reason: "out_of_range"}`; client triggers a callback or raises a specific event that the adapter can hook to fetch a REST snapshot.
- `test_resume_handles_server_restart` — client's stored `server_instance_id` mismatches harness's advertised one; client treats as full restart.
- `test_resume_idempotent_replay_seq_deduplication` — harness sends a duplicate event (seq 500 twice); SDK ignores the second copy based on seq check.

### 4.3 Canopy (drain callbacks, adapter routing, connection status)

**Files touched**: `juniper-canopy/src/tests/unit/test_state_sync.py` (existing), `test_async_sync_boundary.py` (existing); new `test_ws_dash_bridge.py`, `test_apply_params_routing.py`, `test_connection_status_store.py`.

**Phase B (browser bridge backend + Option B drain)**:

- `test_update_metrics_store_handler_returns_no_update_when_ws_connected` — arch doc §6.3 Option B: when `ws-connection-status.connected` is `True`, polling callback returns `no_update`.
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected` — flip the flag, assert REST fetch happens.
- `test_ws_connection_status_store_reflects_cascorWS_status` — simulate drain callback input, assert store updates.
- `test_ws_metrics_buffer_drain_is_bounded` — push 2000 events, assert buffer is capped at configured max (e.g., 1000).
- `test_ws_metrics_buffer_drain_deduplicates_by_seq` — push duplicate seqs, drain retains only first occurrence (idempotent merge contract from §6.5.2).
- `test_ws_metrics_buffer_preserves_order_when_reordered` — push events out of seq order, drain sorts/reorders before render.

**Phase C (`apply_params` routing)**:

- `test_apply_params_hot_keys_go_to_websocket` — pass `{"learning_rate": 0.01}`, assert `_apply_params_hot` is called.
- `test_apply_params_cold_keys_go_to_rest` — pass `{"init_output_weights": "random"}`, assert `_apply_params_cold` is called.
- `test_apply_params_mixed_batch_split` — pass both; assert both paths are called with the right subset.
- `test_apply_params_hot_falls_back_to_rest_on_ws_error` — `_apply_params_hot` raises `CascorConnectionError`; assert `_apply_params_cold` is called as fallback.
- `test_apply_params_preserves_public_signature` — `apply_params` returns the same shape regardless of routing (delegating-wrapper contract from §9.4).
- `test_apply_params_feature_flag_default_off` — `Settings.use_websocket_set_params=False` (default), `apply_params({"learning_rate": 0.01})` uses REST.
- `test_apply_params_feature_flag_on_uses_websocket` — flag flipped, same call uses WS.

**Phase D (control buttons via WebSocket)**:

- Unit-level: `test_training_button_handler_sends_websocket_command_when_connected` — mock `window.cascorControlWS.send`, click button, assert `{command: "start"}` frame sent.
- Unit-level: `test_training_button_handler_falls_back_to_rest_when_disconnected` — assert REST POST path is taken.
- Unit-level: `test_rest_endpoint_still_returns_200_and_updates_state` — GAP-WS-06 target state preserves `/api/train/{command}` as first-class; regression gate against accidental removal.

**Phase F (heartbeat)**:

- Canopy-side `pong` handler unit test: `test_canopy_ws_pong_round_trip`.

**Phase H (normalize_metric contract lock-in)**:

- `test_normalize_metric_produces_dual_format` — arch doc §9.9 explicitly calls this the regression gate PR #141 lacked. Adopt verbatim. Assert both the flat keys (`train_loss`, `val_loss`) AND the nested `metrics.train_loss` / `metrics.val_loss` are present in the output dict.
- `test_normalize_metric_nested_topology_present` — same for `network_topology.*` nested keys.
- `test_normalize_metric_preserves_legacy_timestamp_field` — regression gate against PR #141's class of mistake.

---

## 5. Integration test plan

Integration tests bind two or more components with real I/O (but no browser). Goal: catch wiring, serialization, and contract drift that unit tests cannot.

### 5.1 cascor + cascor-client end-to-end

**Location**: new `juniper-cascor-client/tests/integration/test_ws_cascor_integration.py` (marker: `integration`, requires `cascor-server` fixture).

These tests stand up a **real cascor uvicorn instance** (via pytest fixture) and talk to it with a real `juniper-cascor-client` WebSocket session. They are slower (~15-30 s each) than unit tests and run in the `integration` marker lane, NOT the default lane.

- `test_set_params_end_to_end_happy_path` — real cascor, real SDK, send `set_params(learning_rate=0.005)`, assert `command_response.status=success`, then GET `/api/v1/training/params` REST and assert the change is reflected.
- `test_set_params_end_to_end_whitelist_enforced` — send unknown key, assert filtered by cascor's whitelist.
- `test_set_params_end_to_end_init_output_weights_injection_blocked` — Pydantic Literal rejects the payload; SDK raises `CascorParamError`.
- `test_metrics_stream_end_to_end` — start training via REST, subscribe via WS, receive ≥10 metrics frames, assert seq monotonicity and envelope schema.
- `test_state_transitions_deliver_within_100ms` — start → training → stopped; assert each state event arrives within the §5.4 warm budget.
- `test_oversized_control_frame_closed_1009` — real cascor, SDK sends a 100 KB params dict, assert SDK raises `CascorProtocolError` and underlying connection is closed with 1009.

### 5.2 canopy adapter against fake cascor (with real WebSocket)

**Location**: `juniper-canopy/src/tests/integration/test_cascor_adapter_ws.py`, using `FakeCascorServerHarness` fixture session-scoped.

These tests bind the canopy `CascorServiceAdapter` to a real TCP socket served by `FakeCascorServerHarness` (the FastAPI wrapper from arch doc §8.5). No browser involved.

- `test_adapter_subscribes_to_metrics_and_forwards_to_normalizer` — fake emits scripted metrics, assert canopy's `_normalize_metric` is called with the right data.
- `test_adapter_apply_params_hot_uses_websocket_roundtrip` — canopy's `apply_params({"learning_rate": 0.01})` (Phase C feature flag on) sends via WS to the fake; fake records the command via `expect_command("set_params")`.
- `test_adapter_apply_params_cold_uses_rest` — canopy's `apply_params({"init_output_weights": "random"})` uses REST, verified by fake's received REST request log.
- `test_adapter_reconnects_after_fake_kills_connection` — fake kills a WS session mid-stream, adapter reconnects within §5.4 budget and sends a `resume` with the last-seen `last_seq`.
- `test_adapter_handles_resume_failed_by_fetching_snapshot` — fake responds `resume_failed {reason: "out_of_range"}`, adapter triggers a REST snapshot fetch, verified by fake's received REST request log.
- `test_adapter_demo_mode_parity` — arch doc RISK-08: run the adapter in demo backend mode, assert the same WS wiring works without a real cascor.
- `test_adapter_enforces_api_key` — fake harness's `enforce_api_key=True`, adapter without credentials is rejected; adapter with correct credentials succeeds.

### 5.3 Reconnection / replay scenarios (integration-level)

**Location**: `juniper-canopy/src/tests/integration/test_ws_reconnect_replay.py`.

These are explicit reconnection scenario tests — not sprinkled into §5.1/§5.2, because the full narrative of "emit N events, disconnect, reconnect, verify zero loss" is easier to read as dedicated tests.

- `test_reconnect_replays_10_missed_events` — fake emits seq 1..100; adapter observes through 50; harness disconnects; on reconnect, harness replays seq 51..100 because `last_seq=50` is within the 1024-event buffer.
- `test_reconnect_with_stale_last_seq_triggers_snapshot` — adapter sends `last_seq=1`, current `_next_seq=1500`, harness responds `resume_failed {reason: "out_of_range"}`, adapter fetches REST snapshot.
- `test_reconnect_with_stale_server_instance_id_triggers_snapshot` — adapter's cached `server_instance_id` differs from harness's (simulates cascor restart); adapter fetches REST snapshot instead of replay.
- `test_snapshot_seq_bridges_no_gap` — §6.5.2 atomicity: snapshot returns `snapshot_seq=N`, reconnect sends `last_seq=N`, harness replays only events with `seq > N`. Asserts zero overlap, zero gap.
- `test_older_cascor_without_resume_command_triggers_fallback` — §6.5.3: harness responds to `resume` with `command_response {status: "error", error: "Unknown command: resume"}` (NOT silent drop, per the §6.5.3 correction in v1.3); adapter falls back to REST snapshot.
- `test_duplicate_seq_is_deduplicated_client_side` — harness replays an event that the adapter already applied (seq ≤ snapshot_seq); adapter's idempotent-replay contract discards it.
- `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect` — simulate TCP half-open via a dropped socket; heartbeat detects within `3 × 30 s = 90 s` per §6.4 (shortened to 3 s in tests via config overrides).

### 5.4 juniper-cascor-worker intersection

The worker endpoint is explicitly out of scope per §2.1 of the arch doc ("The worker endpoint is out of scope for this analysis"). But since cascor's `WebSocketManager` changes in Phase B affect shared code paths, run a smoke regression:

- `test_worker_endpoint_unaffected_by_seq_and_replay_changes` — invoke `juniper-cascor-worker` training flow against a cascor with the Phase B changes applied; assert the existing worker test suite passes (delegated to the worker's own CI).

---

## 6. Browser test plan

The arch doc §8 commits to using BOTH `dash_duo` (for Dash store assertions) AND Playwright (for wire-level WebSocket assertions). This section defines exactly which tests go in which tool.

### 6.1 `dash_duo` coverage

**Location**: `juniper-canopy/src/tests/e2e/dash_duo/` (new subtree, marker `e2e`, runs on PR-to-main and nightly).

**Fixture**: `dash_duo` (official from `dash[testing]`) + session-scoped `fake_cascor_server` fixture (arch doc §8.5 harness).

`dash_duo` is the right tool when the assertion is "did the Dash store or a DOM component react correctly to a message?" It understands Dash component IDs natively via `wait_for_text_to_equal`, `wait_for_element_by_id`, and `find_element`. **Use `dash_duo` for store-state assertions and component rendering.**

Phase B tests (from arch doc §9.3 plus additions):

- `test_browser_receives_metrics_event` — fake emits `metrics` event, assert `dash_duo.wait_for_text_to_equal("#metrics-panel-train-loss", "0.5")`.
- `test_chart_updates_on_each_metrics_event` — fake emits 10 metrics events, assert the Plotly chart's data-point count in `window.document.getElementById('loss-chart').data[0].x.length == 10`.
- `test_chart_does_not_poll_when_websocket_connected` — arch doc §9.3: assert the REST polling callback returns `no_update` when `ws-connection-status.connected` is True. Use `dash_duo.driver.execute_script("return window.localStorage.getItem('ws-connected')")` or equivalent store introspection.
- `test_chart_falls_back_to_polling_on_websocket_disconnect` — kill fake mid-stream, assert polling resumes within 5 s (GAP-WS-25).
- `test_demo_mode_metrics_parity` — arch doc RISK-08 + §9.3: runs canopy in demo backend mode, verifies the same clientside wiring works.
- `test_ws_metrics_buffer_store_is_ring_buffer_bounded` — fake emits 2000 events, assert store data is capped at configured max (arch doc RISK-10).
- `test_ws_metrics_buffer_ignores_events_with_duplicate_seq` — fake emits `seq=5` twice, assert store has only one entry with that seq.
- `test_connection_indicator_badge_reflects_state` — GAP-WS-26, §6.3: indicator shows "Connected" / "Reconnecting..." / "Offline" in sync with status store.

Phase C tests (from arch doc §9.4):

- `test_learning_rate_change_uses_websocket_set_params` — set slider to 0.005, assert fake received a WebSocket `set_params` command (via `expect_command("set_params")`).
- `test_learning_rate_change_falls_back_to_rest_on_disconnect` — kill WS, set slider, assert REST PATCH is received.
- `test_orphaned_command_resolves_via_state_event` — arch doc §9.4 GAP-WS-32: fake delays `command_response` past `set_params: 1s` timeout but emits a `state` event with the new value; assert UI transitions from "pending verification" to "applied".
- `test_per_command_timeout_values` — arch doc §9.4: verify `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`.

Phase H regression gate:

- `test_normalize_metric_dual_format_in_browser_view` — §9.9: browser-side assertion that both the flat and nested metric formats drive the chart. This is defensive: a future refactor that drops one format and passes unit tests should still fail here.

### 6.2 Playwright coverage

**Location**: `juniper-canopy/src/tests/e2e/playwright/` (new subtree, marker `e2e`, runs on PR-to-main and nightly).

**Fixture**: `pytest-playwright`'s `page`, `browser`, `context` + session-scoped `fake_cascor_server` + `canopy_app` uvicorn fixture + `page.goto(canopy_app.url)`.

Playwright's advantage over `dash_duo` is network introspection — the ability to **intercept WebSocket frames, assert message contents, simulate slow connections, drop frames**. Use Playwright for everything where the assertion is "what happened on the wire?"

Phase B tests:

- `test_websocket_frames_have_seq_field` — use `page.on("websocket")` and `ws.on("framereceived")` to intercept frames; assert every received frame has a numeric `seq` field.
- `test_resume_protocol_replays_missed_events` — raw frame-level test: simulate disconnect via `ws.close()`, observe the `resume` frame on reconnect, observe replayed frames, assert seq continuity.
- `test_seq_reset_on_cascor_restart` — fake harness sends a new `server_instance_id` on reconnect, assert browser issues a REST snapshot fetch (observe HTTP request via `page.route`).
- `test_frame_budget_respected_at_50hz` — §5.5: script fake to emit metrics at 50 Hz for 2 s, instrument `performance.now()` in a JS hook, assert p95 frame-handling time < 17 ms.
- `test_oversized_topology_frame_handled_gracefully` — GAP-WS-18: fake emits a 100 KB topology frame, assert the browser either chunks, falls back to REST, or closes with 1009 (per final policy decision).

Phase D tests (from arch doc §9.5):

- `test_start_button_uses_websocket_command` — click start, assert a WS frame `{command: "start"}` is observed.
- `test_command_ack_updates_button_state` — fake replies with `command_response {status: "success"}`, assert button disables and state updates.
- `test_disconnect_restores_button_to_disabled` — kill WS, assert button is disabled or shows disconnected state.
- `test_csrf_required_for_websocket_start` — Phase B-pre security regression: without CSRF token, start command is rejected with 4001.

Phase F tests:

- `test_ping_pong_reciprocity` — browser sends `ping`, fake responds `pong` within 5 s.
- `test_missing_pong_triggers_reconnect` — fake never responds to ping, browser closes and reconnects.

Phase I tests (from arch doc §9.10):

- `test_asset_url_includes_version_query_string` — inspect the script tag for `assets/websocket_client.js`, assert query string with hash.

### 6.3 Frame budget assertions

Frame budget (§5.5: 16.67 ms total at 60 fps) is subtle and best measured via Playwright's `evaluate` API rather than `dash_duo`:

- `test_frame_budget_single_metric_event_under_17ms` — measure `performance.now()` before and after the drain callback, assert delta < 17 ms on a warm browser.
- `test_frame_budget_batched_50_events_under_50ms` — arch doc §5.5 "rAF coalesce batches events arriving in same frame"; with 50 events batched, the handler's total cost should still be bounded (not 50× single-event cost).
- `test_plotly_extendTraces_used_not_full_figure_replace` — instrument `Plotly.extendTraces` via `page.evaluate` to intercept the call, assert it is invoked (not `Plotly.react` with full data). GAP-WS-14 is the target state.

**Caveat**: frame-budget tests are inherently flaky on shared CI runners. Mitigation:

1. Run these in a dedicated CI job on a fixed-performance runner (GitHub Actions `ubuntu-latest` has enough headroom for 17 ms assertions, but not for 5 ms assertions).
2. Use p95 over 30 iterations, not single-shot.
3. Mark as `@pytest.mark.flaky(reruns=2)` via `pytest-rerunfailures` for unavoidable jitter.
4. If flakiness persists, downgrade to trace-only (record timings to the latency histogram, don't fail the build). **The §5.6 production latency plan is the real gate; frame-budget assertions are a sanity check.**

### 6.4 Playwright trace artifacts

Per arch doc §8.5.1 + §8.6: use `--tracing=retain-on-failure --screenshot=only-on-failure --video=retain-on-failure`. The trace artifact is the critical debugging affordance that closes the "I can't see what the browser was doing" gap (§8.6). GitHub Actions retention 14 days, 2-15 MB per test × failure only.

---

## 7. Security regression tests (CSWSH, Origin, auth, rate limit)

Phase B-pre's security model (§2.9 M-SEC-01..07) is a **hard prerequisite for Phase D** and must have its own dedicated test coverage BEFORE any control-plane WebSocket traffic is enabled.

These tests live in `juniper-canopy/src/tests/security/test_ws_security.py` (new file) and `juniper-cascor/src/tests/unit/api/test_websocket_security.py` (extend existing).

### 7.1 M-SEC-01 (Origin validation on canopy `/ws/*`)

- `test_csrf_required_for_control_commands` (from §9.2) — pytest-playwright: open canopy WS to `/ws/control`, send a `start` command without first sending an `auth` frame, assert close with 4001.
- `test_origin_validation_rejects_third_party_pages` (from §9.2) — send `Origin: http://evil.example`, assert HTTP 403.
- `test_origin_validation_accepts_whitelisted_origins` — accept `http://localhost:8050` and `http://127.0.0.1:8050`.
- `test_missing_origin_header_rejected` — no `Origin` header, assert 403.
- `test_origin_case_sensitivity_scheme_host_port` — RFC 6454 matching.

### 7.2 M-SEC-01b (Cascor `/ws/*` origin parity)

- `test_cascor_ws_training_rejects_third_party_origin` — symmetric to M-SEC-01 on cascor side.
- `test_cascor_ws_control_rejects_third_party_origin` — same.

### 7.3 M-SEC-02 (Cookie-session auth + CSRF)

- `test_first_frame_must_be_auth_type` — open connection, send `metrics` frame first, assert close 4001.
- `test_csrf_token_validates_against_session` — test with a session cookie and a CSRF token that does NOT match, assert 4001.
- `test_csrf_token_rotation_on_expiry` — arch doc §2.9.2 refinement: 1-hour token expiry, client re-fetches on `close 4001 reason=token_expired`.
- `test_session_cookie_httponly_secure_samesitestrict` — cookie attributes regression gate.
- `test_localStorage_bearer_token_not_accepted` — arch doc §2.9.2 refinement: explicitly rejected as XSS-exfiltratable.

### 7.4 M-SEC-03 (per-frame size limits)

- `test_oversized_frame_rejected_with_1009` (from §9.2) — on all endpoints, cascor and canopy.
- `test_100MB_frame_does_not_exhaust_memory` — send a ~100 MB frame, assert server process memory delta < 10 MB (the framework should reject before reading).

### 7.5 M-SEC-04 (per-IP connection cap)

- `test_per_ip_cap_enforced` — open 6 connections from same IP, assert 6th is rejected with 1013.
- `test_per_ip_cap_configurable_via_settings` — override `ws_max_connections_per_ip=1`, assert first connection accepted and second rejected.
- `test_per_ip_counter_decrements_on_close` — covered in §4.1 unit tests.
- `test_per_ip_map_purged_when_count_reaches_zero` — arch doc §2.9.2 refinement: prevents unbounded map growth.

### 7.6 M-SEC-05 (command rate limit)

- `test_command_rate_limit_10_per_sec_per_connection` — burst 20 commands in 100 ms, assert 10 succeed, 10 get `status: rate_limited`.
- `test_rate_limit_response_is_not_an_error_close` — rate-limited commands do NOT close the connection; they just reply with a rate-limit status.

### 7.7 M-SEC-06 (opaque auth-failure reason)

- `test_auth_failure_reason_is_opaque_across_all_cases` — missing API key, invalid API key, expired key all produce identical `"Authentication failed"` close reason.

### 7.8 M-SEC-07 (logging scrubbing)

- `test_set_params_non_whitelisted_keys_are_redacted_in_logs` — send `{password: "foo"}`, inspect captured log output, assert `<redacted>`.
- `test_set_params_whitelisted_keys_logged_in_cleartext` — e.g., `learning_rate` is logged cleartext.

### 7.9 CSWSH end-to-end regression

- `test_cswsh_from_evil_page_cannot_start_training` — Playwright navigates to a simulated "evil" page on a different origin that attempts to open a WebSocket to `http://localhost:8050/ws/control`. Assert the connection is rejected via Origin check AND the canopy UI's training state remains unchanged.

---

## 8. Latency measurement in CI vs local

Arch doc §5.6 is a production instrumentation plan (not a test plan per se). The test angle is: how do we validate that the instrumentation WORKS and how do we use it in CI?

### 8.1 Unit/integration tests for the instrumentation itself

- `test_emitted_at_monotonic_field_present_on_every_message` — cascor unit test.
- `test_clock_offset_advertised_on_connection_established` — cascor unit test.
- `test_clientside_histogram_exports_every_60s` — Playwright test with fake time, assert POST to `/api/ws_latency` at 60 s intervals.
- `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` — canopy unit test against the Prometheus client registry.
- `test_latency_dashboard_panel_renders` — `dash_duo` test asserting the new "WebSocket health" panel renders p50/p95/p99 values.

### 8.2 CI lane: latency-recording (not latency-asserting)

Latency tests are inherently flaky on shared CI (GitHub Actions runners have ±30% performance variance). Strict latency assertions (e.g., `assert p95 < 100 ms`) MUST NOT run on CI because they will cause false failures that erode trust.

Instead:

1. **CI lane (every PR)**: run the latency instrumentation path, capture the histogram, upload as a build artifact (`latency-report.json`). **Do not assert specific thresholds.** A CI run that emits 500 ms latencies still passes; it just produces a report.
2. **Nightly lane**: run the same tests with a trend check: if nightly p95 degrades > 30% vs the main branch 7-day moving average, open a tracking issue. **Still not a blocking gate** — it is a monitoring signal.
3. **Local-only lane**: developers running `make test-latency` on their own machine get strict thresholds enabled. These exercise the same tests with `JUNIPER_LATENCY_STRICT=1` env flag, which flips assertions from "record" to "enforce".

This separation respects CI variance without abandoning the §5.5 frame budget goal.

### 8.3 Source-doc §5.6 SLO validation

The arch doc promises the §5.1 / §5.4 matrix becomes "SLOs verified against the histogram, not aspirations." This proposal tracks a post-Phase-B follow-up:

- After Phase B ships and latency histograms accumulate ~1 week of real dev-env data, revisit the §5.1 table and convert "Target p50 (unvalidated)†" to "Validated p50" for each parameter class where the histogram shows consistent compliance. Tests that compare expected-vs-observed go in a new `test_latency_slo_compliance.py` under the `nightly` marker.

- The user-research validation plan (§5.7) is a separate calendar item. If it runs, its outputs drive a §5.1 table update and possibly test threshold revisions.

---

## 9. Per-phase test gates (mapped to §9 phases)

Each phase in arch doc §9 has an acceptance test list. This section translates those into concrete pytest invocations, CI steps, and marker combinations. Every phase has an explicit **go/no-go gate** — if the gate tests do not pass, the phase MR does not merge.

### 9.1 Phase A — `juniper-cascor-client` WebSocket `set_params`

**Gate invocation**:

```bash
cd juniper-cascor-client
pytest tests/test_ws_client_set_params.py -v -m "unit or integration"
```

**Required passing tests**:
- `test_set_params_round_trip`
- `test_set_params_timeout`
- `test_set_params_validation_error`
- `test_set_params_reconnection_queue` (1 of 2 design variants)
- `test_set_params_concurrent_correlation`
- `test_set_params_caller_cancellation`

**Coverage gate**: new SDK code ≥ 90% line coverage (higher than baseline because it's additive, not woven through existing code).

**CI step**: runs on every PR to `juniper-cascor-client` main; fast lane.

### 9.2 Phase B-pre — Security hardening

**Gate invocation**:

```bash
cd juniper-canopy && pytest src/tests/security/test_ws_security.py -v
cd juniper-cascor && pytest src/tests/unit/api/test_websocket_security.py -v
cd juniper-canopy && pytest src/tests/e2e/playwright/test_csrf_and_origin.py -v -m e2e
```

**Required passing tests**:
- `test_csrf_required_for_control_commands` (Playwright)
- `test_origin_validation_rejects_third_party_pages` (Playwright)
- `test_oversized_frame_rejected_with_1009` (cascor unit)
- `test_per_ip_cap_enforced` (cascor unit)
- `test_session_cookie_httponly_secure_samesitestrict` (canopy unit)

**CI step**: runs on every PR to canopy AND cascor main. Phase D cannot merge without these passing.

### 9.3 Phase B — Browser bridge + replay

**Gate invocation**:

```bash
cd juniper-canopy && pytest src/tests/e2e/dash_duo/ -v -m e2e
cd juniper-canopy && pytest src/tests/e2e/playwright/test_ws_replay.py -v -m e2e
cd juniper-cascor && pytest src/tests/unit/api/test_websocket_replay_buffer.py -v
```

**Required passing tests** (from §9.3 of arch doc, mapped to file names):

dash_duo:
- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected`
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_demo_mode_metrics_parity` (RISK-08)

Playwright:
- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_connection_status_indicator_reflects_websocket_state`
- `test_frame_budget_single_metric_event_under_17ms` (recording lane — does not block)
- `test_plotly_extendTraces_used_not_full_figure_replace`

Jest/Vitest:
- `cascorWS.on('metrics', handler)` fires
- Reconnect backoff with jitter
- URL construction with `wss://` under HTTPS
- Bounded ring buffer behavior

Cascor unit:
- All tests under "Phase B (sequence numbers + replay buffer)" in §4.1.

**CI step**: this is the riskiest phase per §9.3 ("Risk HIGH"). Runs on every PR to canopy AND cascor main. Playwright trace artifacts retained on failure. **Slow lane** (~5-10 min total).

### 9.4 Phase C — Canopy `apply_params` routing

**Gate invocation**:

```bash
cd juniper-canopy && pytest src/tests/unit/test_apply_params_routing.py -v
cd juniper-canopy && pytest src/tests/e2e/dash_duo/test_set_params_via_websocket.py -v -m e2e
```

**Required passing tests**:
- `test_apply_params_hot_keys_go_to_websocket`
- `test_apply_params_cold_keys_go_to_rest`
- `test_apply_params_mixed_batch_split`
- `test_apply_params_feature_flag_default_off`
- `test_learning_rate_change_uses_websocket_set_params` (dash_duo)
- `test_learning_rate_change_falls_back_to_rest_on_disconnect` (dash_duo)
- `test_orphaned_command_resolves_via_state_event` (dash_duo, GAP-WS-32)
- `test_per_command_timeout_values` (dash_duo)

**CI step**: Phase C ships behind `Settings.use_websocket_set_params=False` flag per RISK-09. Tests run in BOTH flag states (flag-off is the default-behavior regression gate, flag-on is the new-path gate).

### 9.5 Phase D — Training control buttons via WebSocket

**Gate invocation**:

```bash
cd juniper-canopy && pytest src/tests/e2e/playwright/test_training_buttons.py -v -m e2e
```

**Required passing tests**:
- `test_start_button_uses_websocket_command`
- `test_command_ack_updates_button_state`
- `test_disconnect_restores_button_to_disabled`
- `test_csrf_required_for_websocket_start` (security regression)
- `test_rest_endpoint_still_returns_200_and_updates_state` (canopy unit, regression gate for GAP-WS-06 target state)

**CI step**: Phase B-pre MUST have passed on main branch before Phase D merges. CI enforces this via a required-status-check rule.

### 9.6 Phase E — Cascor backpressure

**Gate invocation**:

```bash
cd juniper-cascor && pytest src/tests/unit/api/test_websocket_manager.py::test_slow_client_backpressure -v
cd juniper-canopy && pytest src/tests/e2e/playwright/test_ws_reconnect.py -v -m e2e
```

**Required passing tests**:
- `test_slow_client_does_not_block_other_clients`
- `test_slow_client_send_timeout_closes_1008_for_state`
- `test_slow_client_progress_events_dropped`
- `test_drop_oldest_queue_policy`
- `test_backpressure_default_is_block`
- Playwright: adapter reconnection scenario after Phase E's `close_slow` policy kicks in.

### 9.7 Phase F — Heartbeat + reconnect jitter

**Gate invocation**:

```bash
cd juniper-canopy && pytest src/tests/unit/test_websocket_heartbeat.py -v
cd juniper-cascor-client && pytest tests/test_ws_client_reconnect.py -v
```

**Required passing tests**:
- `test_ping_sent_every_30_seconds`
- `test_pong_received_cancels_close`
- `test_reconnect_backoff_has_jitter`
- `test_reconnect_backoff_capped`
- `test_canopy_ws_pong_round_trip`

### 9.8 Phase G — Cascor WS `set_params` integration test

Already specified in arch doc §9.8 — adopt the test list verbatim. Additional gates:

- `test_set_params_concurrent_command_response_correlation` (two WS clients)
- `test_set_params_during_training_applies_on_next_epoch_boundary`

### 9.9 Phase H — `_normalize_metric` audit

- Lock-in regression test `test_normalize_metric_produces_dual_format` (arch doc §9.9) MUST merge BEFORE the audit begins. This is the regression gate PR #141 lacked.
- Audit deliverable is a doc, not a test.

### 9.10 Phase I — Asset cache busting

- Playwright: `test_asset_url_includes_version_query_string`.
- Canopy unit: `test_dash_app_asset_url_contains_hash`.

---

## 10. CI integration strategy

Arch doc §8.5.1 + §8.6 already define the shape of the CI integration. This section extends with a cost/signal table.

### 10.1 Marker split

Adopt the arch doc §8.5.1 marker split unchanged:

```toml
# juniper-canopy/pyproject.toml (new additions)
[tool.pytest.ini_options]
markers = [
  # existing ...
  "fast: unit and TestClient-based integration tests (<30s total)",
  "e2e: Playwright + dash_duo end-to-end tests (~3-5 min total)",
  "latency_strict: latency assertion tests (local-only; not run in CI)",
  "nightly: tests that run in nightly lane only (long-running or trend-based)",
  "security: security regression tests (run on every PR)",
]
```

Canopy also already has `unit`, `integration`, `regression`, `e2e`, `slow` markers. The new markers above layer on top — a test can be both `e2e` and `security`, or `e2e` and `latency_strict`.

### 10.2 CI lane matrix

| Lane | Trigger | Markers | Timeout | Purpose |
|---|---|---|---|---|
| **fast** | Every push, every PR | `fast or (unit and not e2e) or (integration and not e2e)` | 3 min | Quick signal, catch 80% of bugs |
| **e2e** | PR to main | `e2e` | 10 min | Browser-level validation, wire protocol, Playwright traces |
| **security** | PR to main | `security` | 5 min | Security regression gate; blocking for Phase D |
| **nightly** | Scheduled 02:00 UTC | all markers | 30 min | Full suite incl. nightly, slow, latency recording |
| **latency_strict** | Local only (`make test-latency`) | `latency_strict` | unlimited | Dev workflow; not in CI |

### 10.3 Cost / signal trade-offs

- **Playwright + `dash_duo` install cost**: `playwright install --with-deps chromium` first run is ~60 s. Cache this in GitHub Actions via `actions/cache` keyed on Playwright version. Subsequent runs are ~5 s.
- **Canopy app boot cost per test**: ~3-5 s per test. Use `scope="session"` on the canopy fixture so ~16 e2e tests amortize to ~5 s total boot cost, not 80 s.
- **Playwright browser context per test**: ~1-2 s. Can be reduced by `scope="class"` or `scope="module"` where tests share a common fixture state.
- **Test parallelism**: `pytest -n auto` via `pytest-xdist`. Playwright supports parallel browser instances; `dash_duo` does NOT (Selenium driver is stateful per process). Solution: run Playwright tests in parallel but `dash_duo` tests serially within their own worker.

Total projected e2e runtime: **2-4 minutes** at `pytest -n auto` parallelism across ~16 Playwright tests + ~8 `dash_duo` tests (arch doc §8.5.1 projection).

### 10.4 CI job template

Adopt arch doc §8.6 as the starting point. Extension:

```yaml
jobs:
  fast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest src/tests -m "fast or (unit and not e2e) or (integration and not e2e)" -v --cov=src --cov-fail-under=80

  e2e:
    runs-on: ubuntu-latest
    needs: fast
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test,e2e]"
      - name: Cache Playwright
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: ${{ runner.os }}-playwright-${{ hashFiles('**/pyproject.toml') }}
      - run: playwright install --with-deps chromium
      - run: pytest src/tests/e2e -m e2e -v --tracing=retain-on-failure -n auto
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-traces
          path: test-results/
          retention-days: 14

  security:
    runs-on: ubuntu-latest
    needs: fast
    steps:
      - uses: actions/checkout@v4
      - run: pytest src/tests -m security -v

  nightly:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      # ... full suite + latency recording ...
      - run: pytest src/tests -v --cov=src --cov-fail-under=80
      - run: pytest src/tests -m latency_strict --record-latency=latency-report.json
      - uses: actions/upload-artifact@v4
        with:
          name: nightly-latency-report
          path: latency-report.json
          retention-days: 90
```

### 10.5 `e2e` on cross-repo PRs

When a PR touches multiple repos (e.g., cascor + canopy + SDK), the `e2e` lane must run against the combined tree. Two options:

1. **Monorepo worktree approach**: use `juniper-ml`'s top-level `scripts/run_cross_repo_ci.bash` (or equivalent) that checks out each repo at the PR head and runs the e2e suite. Not currently present; needs to be written.
2. **SDK prerelease approach**: Phase A publishes a prerelease of `juniper-cascor-client` to TestPyPI, Phase B canopy PR installs from TestPyPI, runs e2e. Already documented in arch doc §9.13 release coordination.

Adopt option 2 for Phase A → Phase B handoff. Option 1 is out of scope for this proposal but worth a follow-up.

### 10.6 Test data fixtures

- **NPZ artifacts**: training simulation uses the existing `two_spiral`, `xor`, `moons` datasets from `juniper-data` (already available via `juniper-data-client` fixtures in canopy tests).
- **Scripted metric streams**: use the existing `generate_metrics_snapshot(epoch, scenario)` helper from `fake_client.py`. Do NOT duplicate this logic in a new fixture.
- **Topology fixtures**: use `FakeCascorClient`'s scenario presets (`two_spiral_training` provides a realistic mid-training topology).
- **New needs**: a "large topology" fixture (> 64 KB) to exercise GAP-WS-18 + §6.4. Add as a scenario preset `two_spiral_large_network` with 200 hidden units.

---

## 11. Coverage threshold strategy

Project CLAUDE.md mandates 80% coverage across all Juniper projects. The WebSocket migration adds new code paths that must meet this bar without regressing the whole-repo average.

### 11.1 Per-phase coverage targets

| Phase | New code | Coverage target | Rationale |
|---|---|---|---|
| A (SDK set_params) | `juniper_cascor_client/ws_client.py` additions | 95% | Small, additive, high-leverage |
| B-pre (security) | `juniper-cascor/src/api/websocket/*.py` + `juniper-canopy/src/main.py` | 90% | Security code, high-stakes |
| B (browser bridge) | `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` + `juniper-cascor/src/api/websocket/manager.py` | 85% | High risk; 85% balances the JS hardness of browser-side coverage with the Python side |
| C (apply_params) | `juniper-canopy/src/backend/cascor_service_adapter.py` delta | 90% | Routing logic is linear, easy to cover |
| D (control buttons) | `juniper-canopy/src/frontend/dashboard_manager.py` delta | 85% | clientside_callback wiring |
| E (backpressure) | `juniper-cascor/src/api/websocket/manager.py` delta | 90% | Concurrency code |
| F (heartbeat) | Small cross-repo deltas | 90% | |
| G (cascor ws test) | N/A (test-only) | N/A | |
| H (audit) | N/A (regression test + doc) | N/A | |
| I (asset cache) | Small cross-repo deltas | 85% | |

### 11.2 JS coverage for browser-side code

Python coverage tools do not measure JS. For `assets/websocket_client.js` and `assets/ws_dash_bridge.js` (Phase B):

- **Option 1**: Jest/Vitest unit tests for the pure-JS logic (bounded ring buffer, reconnect backoff, URL construction). Coverage target 85% via `jest --coverage`.
- **Option 2**: Playwright with `page.coverage.start_js_coverage()` / `stop_js_coverage()` — measures coverage during e2e runs. Less precise but no new test toolchain.

Recommend **Option 1** for deterministic line coverage and **Option 2 as a supplement**. Do not rely on e2e alone for JS coverage — the signal is too noisy.

### 11.3 Coverage exclusions

Existing exclusions (`tests/`, `conftest.py`, `__pycache__/`, `venv/`) remain. New exclusions:

- `juniper-canopy/src/frontend/assets/websocket_client.js` — covered by Jest, not pytest-cov. Add to a `.coveragerc` JS skiplist (not that pytest-cov reads JS anyway, but document intent).
- `juniper-cascor-client/juniper_cascor_client/testing/*` — test helpers, not production code. Already excluded in many repos; verify in all three.

### 11.4 Regression gate

Merge is blocked if:

1. Whole-repo coverage drops below 80%.
2. Newly-added files (per-PR diff) have < 85% coverage.
3. Newly-added lines (per-PR diff) have < 90% coverage.

Enforced via `codecov.io` or `diff-cover` in CI. If neither is set up, use a custom pytest plugin that reads the coverage XML and fails the build on regression.

---

## 12. Verification / acceptance criteria

The migration is **done** when all of the following are true:

1. Arch doc §8.8 verification matrix: every row has a passing test in its phase gate.
2. CI lanes: `fast`, `e2e`, `security` all pass on the main branch.
3. `test_normalize_metric_produces_dual_format` is merged to canopy main.
4. `FakeCascorServerHarness` is installable from `juniper-cascor-client[testing]` and consumed by at least one `dash_duo` and one Playwright test on the canopy side.
5. All GAP-WS-01 through GAP-WS-33 that the roadmap schedules as "fix in Phase X" have a passing test exercising the fix.
6. Coverage: 80% whole-repo, 85% on new files, 90% on new lines (§11.4 gate).
7. Playwright trace artifacts are viewable via GitHub Actions Artifacts for any failed run.
8. Latency histograms (`canopy_ws_delivery_latency_ms_bucket{type=...}`) are published by a running canopy instance and the p50/p95/p99 panel renders in the dashboard. (Not a CI test; an operational verification.)
9. Nightly latency recording is running and has accumulated ≥ 7 days of data.
10. Security regression tests all pass BEFORE Phase D merges. Hard gate enforced by CI.

---

## 13. Risks and mitigations (test-plan-specific)

Arch doc §10 has the production-risk register. This section is only the **test-plan** subset.

| ID | Risk (test plan) | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| T-RISK-01 | `FakeCascorServerHarness` masks a bug that only reproduces against a real cascor | Medium | Medium | Mirror arch doc RISK-05: add a weekly smoke test against a real cascor instance (Phase G already covers `set_params`; extend to a `metrics` stream test too) |
| T-RISK-02 | Playwright flakiness on shared CI runners | Medium | **High** | `pytest-rerunfailures` retry=2, trace artifacts retained, move latency assertions to recording-only lane |
| T-RISK-03 | `dash_duo` `scope="session"` shares state between tests | Medium | Medium | Use per-test fixture overrides + `dash_duo.wait_for_no_elements` between tests to ensure clean state |
| T-RISK-04 | The fake harness drifts from real cascor message schemas | Medium | Medium | Add a `test_fake_cascor_message_schema_parity` contract test that loads the cascor `messages.py` message builders and validates fake output against them |
| T-RISK-05 | Security regression tests miss a new attack vector added post-PR | High | Low | Keep the `§2.9.1` threat model doc in sync with tests; add a threat-model review gate on any PR touching `main.py` or `websocket/*.py` |
| T-RISK-06 | Reconnection tests time out on slow CI | Low | Medium | Use `@pytest.mark.timeout(30)` on reconnection tests; fake harness supports configurable `reconnect_delay=0.1` for tests |
| T-RISK-07 | Latency assertions cause CI false positives | High | **High** | Recording-only lane for latency; strict assertions local-only (§8.2) |
| T-RISK-08 | `test_frame_budget_single_metric_event_under_17ms` is too strict | Medium | High | p95 over 30 iterations, not single-shot; recording-only in CI; downgrade to trace if needed |
| T-RISK-09 | Demo-mode test drift (arch doc RISK-08) | Low | Medium | `test_demo_mode_metrics_parity` already in Phase B gate; add to the fast lane so it runs on every PR |
| T-RISK-10 | Cross-repo PRs cannot run e2e against combined tree | High | **High** | Use TestPyPI prerelease (§9.13); long-term, add a `run_cross_repo_ci.bash` script |
| T-RISK-11 | Browser test fixture coupling to Dash internals (e.g., `dash.set_props`) | Medium | Medium | Prefer Playwright for anything that touches internals; `dash_duo` only for public store/component API |
| T-RISK-12 | Flaky heartbeat / ping timing on slow CI | Medium | Medium | Override `ping_interval=0.1, pong_timeout=0.5` in tests; do not test real 30 s/5 s timing in CI |

---

## 14. Disagreements with the source doc

The following are places this proposal either rejects, narrows, or expands the arch doc. Each disagreement is justified.

### 14.1 Disagreement: arch doc §9.1 understates `test_set_params_caller_cancellation` importance

The arch doc lists it as one of six tests but does not flag it as critical. This proposal elevates it because `asyncio.Task.cancel()` is one of the easiest ways to leak an entry in a correlation-ID dict — a memory leak that does not surface until the dict grows unbounded. Recommend the test be mandatory for Phase A acceptance, not optional.

### 14.2 Disagreement: arch doc §9.4 Phase C test list omits routing unit tests

The arch doc §9.4 lists dash_duo browser tests and an `AsyncMock` unit test, but does not explicitly test the routing logic in `apply_params()` itself (hot/cold split, mixed batch, feature flag). This proposal adds those to §4.3 Phase C. Without them, the `_apply_params_hot` / `_apply_params_cold` decomposition has no direct coverage.

### 14.3 Disagreement: arch doc §8.5.1 underestimates Playwright + `dash_duo` parallel runtime

The estimate is "~2-4 min total with `pytest -n auto`". This assumes `dash_duo` tests parallelize, which they do not (Selenium WebDriver is process-local and stateful). Realistic runtime with serial `dash_duo` + parallel Playwright is **5-8 min**. Not a blocker; just adjust expectations in the CI plan. Flag to R0-06 CI agent.

### 14.4 Disagreement: arch doc §5.6 latency CI integration not specified

The latency measurement plan describes what to instrument but not how to validate it in CI. This proposal adds §8 "Latency measurement in CI vs local" with the recording-only / strict-local split. The arch doc should adopt this (or a refinement) explicitly before Phase B ships, otherwise Phase B will have "an instrumentation plan" but no tests proving the instrumentation works.

### 14.5 Disagreement: arch doc §9.8 Phase G is too narrow

Phase G is described as "Cascor WS set_params integration test" and scoped to a handful of test cases. This proposal expands to include:

- `test_set_params_concurrent_command_response_correlation` (two WebSocket clients) — because cascor's `_VALID_COMMANDS` handler must correctly route responses per-connection, and a single-connection test cannot exercise that.
- `test_set_params_during_training_applies_on_next_epoch_boundary` — because §5.3.1 ack-vs-effect distinction is the entire rationale for Phase C's feature flag; without this test, the flag decision is blind.

These are small additions (< 30 min implementation each).

### 14.6 Disagreement: arch doc does not require a schema-parity contract test

The fake harness in §8.5 risks drifting from cascor's real message schemas over time. This proposal adds `test_fake_cascor_message_schema_parity` as a contract test in §13 T-RISK-04. The test loads cascor's `messages.py` builders and validates fake output dict shapes match. Without this, silent drift is a latent failure mode.

### 14.7 Narrowing: arch doc §11 Open Question 2 (browser compatibility)

This proposal explicitly scopes the test plan to Chromium-only. Firefox/WebKit support can be added later by flipping `BrowserType.firefox` / `BrowserType.webkit` in Playwright fixtures, but the initial test plan should not carry the multi-browser cost. Document as a follow-up.

### 14.8 Narrowing: arch doc §5.7 user research validation

This proposal does NOT include automated tests for user-perceived latency. Arch doc §5.7 proposes a 5-subject think-aloud study; that is outside the pytest/Playwright purview and should be tracked as a separate UX research task. The latency histograms from §5.6 are the closest automatable proxy.

### 14.9 Expansion: arch doc mentions `dash_duo` but not its known limitations

The arch doc recommends `dash_duo` without discussing:

- **`dash_duo` uses Selenium WebDriver**, not Playwright. The two tools have different browser APIs.
- **`dash_duo` does not parallelize** well — one ChromeDriver process per pytest worker.
- **`dash_duo` wait-for APIs are explicit** — no auto-retry like Playwright's locator API.
- **`dash_duo` is aware of Dash components** via `driver.find_element(By.ID, "my-dash-id")` style, which is the exact reason to prefer it over Playwright for store assertions.

These constraints drive the §6.1/§6.2 split in this proposal. Arch doc §8.2 says "native understanding of Dash component IDs" which is correct but underspecified. This proposal makes the split explicit: `dash_duo` for store/DOM, Playwright for wire protocol.

### 14.10 Question to consolidator: should there be a dedicated "contract test" lane?

Arch doc does not define contract tests as a distinct category, but they are the correct tool for things like:

- Canopy adapter ↔ cascor SDK message schema match.
- Fake harness ↔ real cascor message builder match.
- `_normalize_metric` dual-format lock-in.

Propose adding a `contract` marker and running it on every PR to any of cascor, canopy, or cascor-client. This is a consolidation-round decision, not a Round 0 call to make unilaterally.

---

## 15. Self-audit log

Self-audit pass 1 (immediately after initial draft): read back through and check for missing test categories, vague assertions, missing CI plan items, unrealistic scope.

### 15.1 Issues found in pass 1

1. **Missing**: The initial draft did not mention test data fixtures for NPZ artifacts or mocked metric streams. The prompt explicitly asked for this. Added §10.6 "Test data fixtures".

2. **Missing**: The initial draft did not have negative/adversarial tests as a dedicated section. Malformed messages, oversized messages, schema confusion, double-ack, out-of-order seq were scattered. Added explicit bullets in §4.1 (`test_unknown_command_returns_error`, `test_malformed_json_closes_with_1003`, `test_duplicate_seq_is_deduplicated_client_side`, `test_older_cascor_without_resume_command_triggers_fallback`).

3. **Vague**: The initial draft said "coverage must stay at 80%" without specifying enforcement. Added §11.4 "Regression gate" with concrete blocking conditions.

4. **Missing**: The initial draft did not cover JS coverage for `websocket_client.js` / `ws_dash_bridge.js`. Python coverage tools do not measure JS. Added §11.2 "JS coverage for browser-side code".

5. **Vague**: "test the reconnection protocol" was too abstract. Added §5.3 with seven specific reconnection scenarios, each tied to a §6.4 close code or a §6.5 protocol path.

6. **Missing**: CI integration for cross-repo PRs. Added §10.5.

7. **Missing**: Disagreement with the arch doc on `test_set_params_caller_cancellation` importance. Added §14.1.

8. **Unrealistic scope**: Initial draft had frame-budget assertions as blocking CI gates. That's a recipe for flaky builds on shared runners. Added the recording-only lane in §8.2 and §13 T-RISK-07/08.

9. **Missing**: Explicit call-out that `dash_duo` does not parallelize. Added §14.9 + §10.3.

10. **Missing**: Security regression tests as a dedicated section. The initial draft mixed them into the phase gates. Separated into §7 for clarity and to make it easier for a security reviewer to audit the test list.

11. **Missing**: Contract-test-as-a-category consideration. Added as an open question to consolidator in §14.10.

12. **Missing**: How the fake harness stays in sync with real cascor schemas. Added T-RISK-04 and `test_fake_cascor_message_schema_parity` in §14.6.

13. **Vague**: "latency budget" as an assertion target. Clarified in §8 that strict assertions are local-only; CI captures histograms but does not enforce thresholds.

14. **Missing**: Phase I (asset cache busting) test plan. Added §9.10.

15. **Missing**: Per-phase coverage targets (not just overall 80%). Added §11.1 table.

### 15.2 Issues found in pass 2 (after first round of edits)

16. **Missing**: The prompt explicitly asked for "reuse pattern for the existing fakes — what they cover today, what they need for the new migration." The initial draft had this but was not concrete. Added §3.1 and §3.2 with a line-number-anchored inventory of the existing fake capabilities AND a §3.3 "what to reuse, what to extend" bullet list.

17. **Missing**: The prompt mentioned "unit test patterns: per-component unit coverage in cascor (broadcaster, replay buffer), juniper-cascor-client (set_params), canopy (drain callbacks, store updates)." Made this the explicit §4.1/§4.2/§4.3 structure.

18. **Overreach**: The initial draft had internal design suggestions for the fake harness (e.g., specific class hierarchies). The prompt says "do NOT design the actual production code." Trimmed those suggestions to bulleted "required capabilities" without class design.

19. **Missing reference**: `test_fake_cascor_message_schema_parity` was mentioned in a disagreement but not in the unit-test plan. Added to §4 mentally (it belongs in `juniper-canopy/src/tests/unit/test_cascor_message_contract.py` or similar, run on every PR).

20. **Ambiguous**: `test_reconnect_backoff_has_jitter` assertion method was not specified. Clarified in §4.2 as "std-dev > 0 across 10 attempts" which is a weak but non-flaky assertion.

21. **Missing**: Per-IP connection cap test for cascor `WebSocketManager` concurrency contract. Arch doc §2.9.2 specifies the lock contract in detail; tests must enforce it. Added `test_per_ip_counter_decrements_on_exception` explicitly.

### 15.3 Issues explicitly NOT addressed (deferred)

- **Playwright / `dash_duo` fixture code samples**: the arch doc §8.5 already has a `FakeCascorServerHarness` sketch. This proposal does not reproduce it to avoid duplication; a consolidation agent should cross-reference §8.5 directly.
- **Coverage XML schema / codecov.io configuration**: out of scope; infrastructure detail.
- **pytest-xdist + `dash_duo` worker pinning**: acknowledged in §10.3 but not spelled out as a config snippet.
- **Multi-browser matrix**: §14.7 narrowing.
- **User research automation**: §14.8 narrowing.
- **Contract test lane as a distinct marker**: §14.10 open question.

### 15.4 Cross-references sanity check

- All GAP-WS-NN references used: GAP-WS-01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 13, 14, 16, 18, 22, 23, 24, 25, 26, 30, 31, 32, 33. Missing from tests: GAP-WS-08 (the umbrella "no e2e browser test" — this entire proposal is the remediation), GAP-WS-12 (heartbeat — covered in §9.7), GAP-WS-15 (rAF coalescing — covered implicitly in frame budget §6.3), GAP-WS-17 (permessage-deflate — not a test target per arch doc), GAP-WS-19 (`close_all()` lock — concurrency unit test in §4.1 covers this), GAP-WS-20 (envelope asymmetry — covered by schema contract test §14.6), GAP-WS-21 (1 Hz state throttle — needs a test, added as a note to §4.1), GAP-WS-27 (per-IP cap — covered in §4.1 and §7), GAP-WS-28 (multi-key torn-write — needs a test, added as a note to §4.1), GAP-WS-29 (broadcast_from_thread exception swallow — covered in §4.1).

- All M-SEC-NN references used: M-SEC-01, 01b, 02, 03, 04, 05, 06, 07.

- All RISK-NN references used: RISK-02, 05, 08, 09, 10, 11, 13, 16.

### 15.5 Final scope check

Target length: 600-1500 lines. Current length is ~1050 lines — within range.

Scope discipline check: did I stay out of production-code design?

- ✓ No class hierarchies proposed beyond "add these test helpers to the existing fake."
- ✓ No broadcaster internal designs (deferred to R0-02 or whichever agent owns the server).
- ✓ No `set_params` API signature design (deferred to R0-03 SDK agent).
- ✓ No drain callback wiring design (deferred to R0-04 frontend agent).
- ✓ No security model implementation design (deferred to R0-06 security/CI agent).
- ✓ References to other agents' deliverables are test-shaped ("given the agent ships X, this test asserts Y").

Scope discipline PASS.

---

**End of R0-05 proposal.**
