# Round 1 Proposal R1-02: Risk-Minimized / Safety-First WebSocket Migration

**Angle**: Maximize safety margin and reversibility above delivery speed
**Author**: Round 1 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 1 consolidation — input to Round 2
**Inputs consolidated**: R0-01 (frontend), R0-02 (security), R0-03 (cascor backend), R0-04 (SDK/set_params), R0-05 (testing), R0-06 (ops/phasing/risk)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope and safety principles

### 1.1 What this proposal is

A consolidated, **deliberately conservative** re-plan of the WebSocket migration described in the architecture doc. Every recommendation from R0-01..R0-06 has been refracted through a safety lens. Where a Round 0 author chose a default that optimized for delivery speed, code brevity, or defensibility, this proposal chooses differently whenever a more reversible or more observable alternative exists.

This proposal does NOT redesign the transport, envelope, or API surface. It inherits:

- Phase A (SDK set_params) from R0-04 as the landing site for `CascorControlStream.set_params`.
- Phase A-server (cascor prerequisites) from R0-03 as the seq/replay/server_instance_id implementation.
- Phase B-pre (security hardening) from R0-02 as the CSWSH / Origin / CSRF / max_size / per-IP cap bundle.
- Phase B (browser bridge) from R0-01 as the Option B Interval drain + Plotly extendTraces + polling toggle.
- Phase C (canopy adapter migration) from R0-04 as the hot/cold routing in `apply_params`.
- Phases D/E/F/G/H/I from R0-06 as the ordered tail.

What this proposal adds on top: observability knobs, kill switches, defaults that favor the conservative behavior, canary gates, and a disaster-recovery scenario per phase.

### 1.2 The 8 safety principles

1. **Observability before behavior change.** Every metric and alert that a rollout decision depends on must exist BEFORE the change ships. No "we'll add metrics later." No "the metrics are in the follow-up PR." If the metric is not landed, the behavior change does not ship.

2. **Kill switches for everything.** Every phase must have a documented kill switch that can be flipped in under 5 minutes. Every kill switch is a config flag (not a code change) and has a CI test that proves it takes effect.

3. **Phase B-pre security gate is a hard gate.** It is not negotiable, not parallelizable with Phase D, and not compressible. The full M-SEC-01/01b/02/03/04/05/06/07/10/11 bundle from R0-02 lands and stabilizes in staging before Phase D is eligible for merge. M-SEC-03 (max_size guards) additionally gates Phase B.

4. **No silent fallbacks.** Every failure path increments a prom counter, logs a WARN, and (where user-facing) surfaces in the connection-status badge. A fallback that is not observable is a bug-hider.

5. **Conservative defaults.** Feature flags default OFF even when "safe," until evidence justifies flipping. The evidence bar is explicit per flag (e.g., Phase C requires one week of p95 histogram data).

6. **Production canary.** Every behavior-changing phase rolls dev → staging → canary → full, with explicit gating criteria between stages. Staging soak is ≥24 hours (≥72 hours for Phase B). Canary soak is ≥1 week for Phase C, ≥48 hours for Phase D.

7. **Backwards compatibility forever.** REST paths stay alive as fallback forever. No REST code deletions anywhere in this migration. A future "remove the REST fallback" PR is explicitly out of scope and requires its own risk assessment and separate migration plan.

8. **Disaster recovery per phase.** For each phase, §9 below answers: "what if this is catastrophically wrong — data loss, user lockout, DoS amplification — and what is the documented recovery plan?" No phase ships without a worst-case answer in its runbook.

### 1.3 What "risk-minimized" buys us and what it costs

**Buys us**: a migration we can roll back from at any point. A migration where a P1 incident is ~5 minutes MTTR, not hours. A migration where the first wave of production incidents produces actionable signal, not "something weird happened and we're not sure what."

**Costs us**: ~20-30% longer calendar time versus R0-06's 4.5-week estimate. Roughly ~17-18 engineering days total (vs R0-06's ~13.5). The cost is mostly absorbed by: adding observability plumbing to every phase (not just Phase B), doubling staging soak windows, and serializing Phase B-pre-a and Phase B-pre-b instead of parallelizing them.

---

## 2. Pre-flight: observability before behavior change

This section enumerates every metric, log, and alert that must exist **before** the behavior change it guards is allowed to ship. The rule is strict: metric present in Prometheus + panel in dashboard + alert rule committed + alert has been test-fired in staging once.

### 2.1 Cascor-side metrics (amplifying R0-03 §9.1)

R0-03 §9.1 listed 15 metrics. Safety-first amplification adds the following and tightens labels:

**Mandatory before Phase A-server merges to main**:

| Metric | Type | Labels | Safety reason |
|---|---|---|---|
| `cascor_ws_seq_current` | Gauge | — | Loss of seq monotonicity (stale `_next_seq`) is a correctness-catastrophic bug; must be watchable live |
| `cascor_ws_replay_buffer_occupancy` | Gauge | — | Operational proxy for "are we within the replay window"; drives the Phase B canary decision |
| `cascor_ws_replay_buffer_bytes` | Gauge | — | Amplified from R0-03: computed every 30 s, not on hot path. Defends against an unnoticed memory creep from a future envelope bloat |
| `cascor_ws_replay_buffer_capacity_configured` | Gauge | — | Emitted at init only. Makes operational tunables visible in the metric store (so operators can diff against what's actually deployed) |
| `cascor_ws_resume_requests_total` | Counter | `outcome={success, server_restarted, out_of_range, malformed, no_resume_timeout}` | Unchanged from R0-03 |
| `cascor_ws_resume_replayed_events` | Histogram | — | Buckets `{0, 1, 5, 25, 100, 500, 1024}`. A spike to the tail is an early indicator of long disconnects / flaky client |
| `cascor_ws_broadcast_timeout_total` | Counter | `type` | Pruned-client counter. Amplified: split by `type` so `state`-bearing drops are distinguishable from `candidate_progress` drops |
| `cascor_ws_broadcast_send_seconds` | Histogram | `type` | Per-type latency of the `_send_json` timeout path. Required to tune the 0.5 s `ws_send_timeout_seconds` without guessing |
| `cascor_ws_pending_connections` | Gauge | — | **New** — number of connections in `_pending_connections` (two-phase registration). A non-zero value sustained >5s means a client is stuck in the resume handshake and is a tight signal for GAP-WS-13 bugs |
| `cascor_ws_state_throttle_dropped_total` | Counter | — | Pre-coalescer baseline; drops to 0 after Phase A-server commit 7. Retained as a regression guard |
| `cascor_ws_state_throttle_coalesced_total` | Counter | — | Post-coalescer value; replaces the drop counter |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter | — | **New** — counts exceptions swallowed by `broadcast_from_thread` (GAP-WS-29 fix). Must be 0 in steady state |

**Assertions at init** (cascor startup):

- `cascor_ws_replay_buffer_capacity_configured` published once with the resolved `Settings.ws_replay_buffer_size`. Aligns with the R0-03 `replay_buffer_capacity` field on `connection_established`, but available in Prometheus for operator diffing.

### 2.2 Canopy-side metrics (amplifying R0-01 + R0-05)

R0-01 §5.6 covered the browser-side latency histogram. Safety-first amplification makes the browser-to-backend reporting more granular:

| Metric | Source | Labels | Safety reason |
|---|---|---|---|
| `canopy_ws_delivery_latency_ms` | Histogram | `type` ∈ {metrics, state, topology, cascade_add, candidate_progress, event, command_response} | R0-06 §6.1 |
| `canopy_ws_browser_heap_mb` | Histogram (from JS) | — | Browser memory reporter; alert p95 > 500 MB |
| `canopy_ws_browser_js_errors_total` | Counter (from JS) | `component` | **New, not in R0-01** — any `try/catch` in `ws_dash_bridge.js` or `websocket_client.js` that traps an exception must increment this counter and emit to `/api/ws_browser_errors`. Closes the "clientside_callback silently dies" debuggability gap flagged in R0-01 FR-RISK-10 |
| `canopy_ws_drain_callback_gen` | Gauge | `buffer` ∈ {metrics, topology, state, cascade_add, candidate_progress} | **New** — monotonic drain gen per buffer. A stuck or regressing value means the drain loop died in the browser. Reported by the browser via `/api/ws_latency` aggregation |
| `canopy_ws_active_connections` | Gauge | — | Count of active canopy-side `/ws/training` connections from browsers |
| `canopy_ws_reconnect_total` | Counter | `reason` | Reconnect rate; spike alert for reconnect storms |
| `canopy_rest_polling_bytes_per_sec` | Gauge | `endpoint` | **Amplified from R0-06** — must be labeled by endpoint (not aggregate) so the P0 motivator proof is per-endpoint, not a cross-endpoint average that can hide a regression |
| `canopy_ws_connection_status` | Gauge | `status` ∈ {connected, reconnecting, offline, demo} | **New** — 1 for the active status, 0 for others. Gives the Phase B connection indicator a server-side counterpart for alerting |
| `canopy_set_params_latency_ms` | Histogram | `transport` ∈ {ws, rest}, `key` | Unchanged from R0-04 §7.2 |
| `canopy_orphaned_commands_total` | Counter | `command` | R0-06 RISK-13 |
| `canopy_ws_backend_relay_latency_ms` | Histogram | — | **New** — latency from cascor → canopy adapter → canopy `/ws/training` broadcast. R0-01's browser-side histogram measures cascor→browser; this measures cascor→canopy separately so a regression in either hop is attributable |

**Mandatory before Phase B ships to production**:
- All 12 metrics above are in Prometheus.
- `canopy_rest_polling_bytes_per_sec` has pre-Phase-B baseline recorded for comparison.
- The "WebSocket health" panel is published in the canopy dashboard.
- One synthetic alert (`WSOriginRejection`) has been test-fired in staging and confirmed to reach the on-call channel.

### 2.3 Security metrics (amplifying R0-02 §4.6)

R0-02 §4.6 listed 6 counters + 1 histogram. Safety-first amplification adds per-endpoint labels and introduces a handshake-attempt signal:

| Metric | Type | Labels | Amplification |
|---|---|---|---|
| `canopy_ws_auth_rejections_total` | Counter | `reason`, `endpoint` | R0-02 had `reason` only; add `endpoint` (`/ws/control` vs `/ws/training`) so an attack localized to the control path is distinguishable |
| `canopy_ws_origin_rejected_total` | Counter | `origin_hash`, `endpoint` | **New** — hash the rejected origin (SHA-256 prefix, 8 chars) so repeated probes from the same attacker are correlatable without logging the raw origin (GDPR-safe, per M-SEC-07) |
| `canopy_ws_frame_too_large_total` | Counter | `endpoint` | R0-02 unchanged |
| `canopy_ws_per_ip_rejected_total` | Counter | `endpoint` | R0-02 unchanged |
| `canopy_ws_rate_limited_total` | Counter | `command`, `endpoint` | R0-02 had no `command`; add because the slider vs button vs reset distinction matters for false-positive analysis |
| `canopy_ws_command_total` | Counter | `command`, `status`, `endpoint` | Unchanged |
| `canopy_ws_auth_latency_ms` | Histogram | `endpoint` | Unchanged |
| `canopy_ws_handshake_attempts_total` | Counter | `outcome={accepted, origin_rejected, cookie_missing, csrf_invalid, per_ip_cap, cap_full}` | **New** — one counter per terminal handshake outcome. Enables "handshake funnel" analysis during an incident |
| `canopy_ws_per_origin_cooldown_active` | Gauge | — | **New** — count of IPs currently in the R0-02 §4.8 per-origin handshake cooldown. Non-zero = active probing |
| `cascor_ws_audit_log_bytes_written_total` | Counter | — | **New** — audit log write volume. Proxy for the 70 MB/day projection in R0-02 §8.4. Alert on 2× projected |

**Mandatory before Phase B-pre merges to main**:

- All above metrics scraped and panels published.
- `WSOriginRejection` alert test-fired once.
- Runbook `juniper-canopy/notes/runbooks/ws-cswsh-detection.md` published with a link to the alert.

### 2.4 SLOs and alerts

SLOs are inherited from R0-06 §6.3 with one tightening: the "error budget burn rate" rule is explicit.

**SLOs (99.9% compliance over 7-day rolling window)**:

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` delivery | <100 ms | <250 ms | <500 ms |
| `state` delivery | <50 ms | <100 ms | <200 ms |
| `command_response` (set_params) | <50 ms | <100 ms | <200 ms |
| `command_response` (start/stop) | <100 ms | <250 ms | <500 ms |
| `cascade_add` delivery | <250 ms | <500 ms | <1000 ms |
| `topology` delivery (≤64 KB) | <500 ms | <1000 ms | <2000 ms |

**Error budget burn rule**: if the 99.9% compliance budget is burned in <1 day, freeze all non-reliability work until recovered. This is R0-06's recommendation made operationally binding: a commit that lands during an active budget burn must be either reliability-related or explicitly approved by the project lead.

**Alert matrix (page vs ticket)**:

| Alert | Condition | Severity |
|---|---|---|
| `WSOriginRejection` | `increase(canopy_ws_auth_rejections_total{reason="origin_rejected"}[5m]) > 0` from unknown origin_hash | **page** |
| `WSOversizedFrame` | `increase(canopy_ws_oversized_frame_total[5m]) > 0` | **page** |
| `WSStateDropped` | `increase(cascor_ws_dropped_messages_total{type="state"}[5m]) > 0` | **page** |
| `WSResumeBufferNearCap` | `cascor_ws_replay_buffer_occupancy > 0.8 * replay_buffer_capacity for 30s` | ticket |
| `WSDeliveryLatencyP95High` | `histogram_quantile(0.95, canopy_ws_delivery_latency_ms_bucket{type="metrics"}[5m]) > 500` | ticket |
| `WSPendingConnectionStuck` | `cascor_ws_pending_connections > 0 for 30s` | ticket |
| `WSDrainCallbackGenStuck` | `changes(canopy_ws_drain_callback_gen[2m]) == 0` | ticket |
| `WSBrowserHeapHigh` | `histogram_quantile(0.95, canopy_ws_browser_heap_mb_bucket[1h]) > 500` | ticket |
| `WSReconnectStorm` | `rate(canopy_ws_reconnect_total[1m]) > 5 * baseline` | ticket |
| `WSSlowBroadcastP95` | `histogram_quantile(0.95, cascor_ws_broadcast_send_duration_seconds[5m]) > 0.5` | ticket |
| `WSAuditLogVolume2x` | `rate(cascor_ws_audit_log_bytes_written_total[1h]) > 2 * baseline` | ticket |
| `WSJSErrorsNonZero` | `increase(canopy_ws_browser_js_errors_total[5m]) > 0` | ticket |
| `WSOrphanedCommand` | `rate(canopy_orphaned_commands_total[5m]) > 1/60` | ticket |
| `WSSeqCurrentStalled` | `changes(cascor_ws_seq_current[5m]) == 0 AND cascor_ws_active_connections > 0` | **page** (indicates a broadcast loop hang — RISK-14 precursor) |

The three page-severity alerts map to the three safety-critical risks: CSWSH probe, DoS frame, and state-dropped data loss. The fourth page alert (`WSSeqCurrentStalled`) is new to this proposal and covers the event-loop-hang disaster in R0-03 §8.5.

---

## 3. Phase A-server with safety amplification

R0-03 defines Phase A-server as the cascor-side prerequisites: seq assignment, replay buffer, server_instance_id, two-phase registration, _send_json timeout, state throttle coalescer, broadcast_from_thread exception handling, /ws/control protocol error responses. 10 commits, ~2 engineering days.

This is a cascor-internal phase with NO canopy or browser user-visible change. Its output is a server that can be validated against Phase B before Phase B touches a browser.

### 3.1 Amplified acceptance gate for Phase A-server

R0-03 §10 listed 27 verification criteria across unit/integration/load/manual. Safety-first amplification adds:

**28. Chaos unit test — `broadcast_from_thread` under fuzzed exceptions.** Use `hypothesis` to generate random exception types inside the scheduled coroutine; assert `cascor_ws_broadcast_from_thread_errors_total` increments once per raise AND no coroutine warning escapes to stderr. (Strengthens R0-03 test 15.)

**29. Chaos unit test — race between `replay_since()` and `broadcast()`.** Under `asyncio.gather`, run 1000 broadcasts interleaved with 100 `replay_since()` calls from forged cursors at random points in the buffer window. Assert: every replay snapshot is internally monotonic; no replay returns a seq higher than its snapshot's newest; `_replay_buffer` size never exceeds `maxlen`. This is the R0-03 §8.4 race condition made into a chaos test.

**30. Metric presence assertion.** Before the PR merges, assert every metric listed in §2.1 above is exported via `/metrics`. Done via a pytest that scrapes `/metrics` and matches against a hardcoded allowlist of expected names.

**31. Replay-buffer configurable-capacity assertion.** Start cascor with `JUNIPER_WS_REPLAY_BUFFER_SIZE=256` (below default). Assert `cascor_ws_replay_buffer_capacity_configured == 256`. Assert `_replay_buffer.maxlen == 256`. Guards against a hardcoded default silently overriding the env.

**32. Kill-switch test — per-send timeout configurable.** Assert that setting `JUNIPER_WS_SEND_TIMEOUT_SECONDS=5.0` makes `_send_json` wait 5 s (measured) rather than 0.5 s. Important because the 0.5 s default is flagged as "lower confidence" in R0-03 §12.4.

### 3.2 Safety knobs Phase A-server adds

Beyond R0-03's config proposals, this phase adds:

| Setting | Default | Tune up if... | Tune down if... |
|---|---|---|---|
| `ws_replay_buffer_size` | **256** (NOT 1024) | `cascor_ws_replay_buffer_occupancy` sustained >80% | Memory pressure (never happens per R0-03 §3.4) |
| `ws_send_timeout_seconds` | 0.5 | `cascor_ws_broadcast_timeout_total` rate > 1/s sustained in healthy conditions | Slow clients becoming stuck |
| `ws_state_throttle_coalesce_ms` | 1000 | — | — |
| `ws_resume_handshake_timeout_s` | 5.0 | — | — |
| `ws_pending_max_duration_s` | 10.0 | **New** — max time a connection can stay in `_pending_connections`. A stuck-in-pending client is kicked with 1013 "Resume handshake timeout" | — |

**Why `ws_replay_buffer_size` defaults to 256, not 1024**: R0-03's 1024 is ~40 seconds of history at steady state, but the safety-first stance is "the smallest buffer that covers the common disconnect + one headroom multiplier." 256 covers ~10 seconds — plenty for WiFi blips, backgrounded-tab throttling, and cascor graceful restart — and exposes the `out_of_range` code path earlier, which is the code path we WANT to shake out in production. The R0-03 default of 1024 makes `out_of_range` rare, which is the opposite of what we want: rare failure paths become brittle. Operators can raise it later if real incidents show the need.

**Disagreement with R0-03** (logged in §13 below): R0-03 §3.1 argues "1024 comfortably covers a 20-second graceful restart." I argue we don't want to cover that; we want the snapshot-refetch path to be exercised so it stays reliable.

### 3.3 Kill switches for Phase A-server

| Switch | Who flips | MTTR | Effect |
|---|---|---|---|
| `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | ops | 5 min | Disables replay entirely; all reconnects get `out_of_range` and fall back to snapshot |
| `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | ops | 5 min | Tightens the slow-client prune. Aggressive but safe — prunes anyone slower than 10 ms |
| Rolling restart of cascor | ops | 10 min | Changes `server_instance_id`, forces all clients to snapshot-refetch |
| Revert Phase A-server PR | ops | 15 min | Full rollback to pre-seq behavior. Clients with cached `server_instance_id` will get `out_of_range` or `server_restarted` and snapshot-refetch |

**No behavior-changing flag needed** because Phase A-server is additive: the `seq` field is new, the replay protocol is new, but the old broadcast path still works. Old clients (e.g., juniper-cascor-client versions before Phase A) continue to receive envelopes and ignore the unknown `seq` field. Rollback is a revert, not a flag flip.

### 3.4 Canary plan for Phase A-server

Phase A-server ships to staging and runs for **72 hours** (not 24) before production. Three reasons:

1. Seq monotonicity bugs are latent. They only surface under sustained multi-client broadcast.
2. `broadcast_from_thread` exception handling only matters when exceptions happen. 72 hours gives the dev loop time to trigger the edge cases.
3. The replay buffer occupancy metric needs a baseline. 72 hours of data is enough to see the natural oscillation and set realistic alert thresholds.

Staging gate: at 72 hours, the following must be true:
- `cascor_ws_broadcast_from_thread_errors_total == 0`
- `cascor_ws_replay_buffer_occupancy` distribution shows a stable mode
- `cascor_ws_broadcast_timeout_total` rate <0.1/s (no slow-client runaway)
- `cascor_ws_seq_current` increases monotonically across all hours

---

## 4. Phase B-pre with safety amplification

R0-02 defines Phase B-pre as the CSWSH / Origin / auth / CSRF / max_size / per-IP / rate-limit / audit log bundle. R0-06 §13.1 correctly observes that M-SEC-03 (max_size) is a Phase B prerequisite while M-SEC-01/02 are Phase D prerequisites. The safety-first stance accepts R0-06's split AND tightens it further.

### 4.1 Phase B-pre-a (M-SEC-03 + M-SEC-04 base): hard Phase B prereq

**Scope**: per-frame inbound size cap (M-SEC-03), per-IP connection cap (M-SEC-04 part 1), origin allowlist on canopy and cascor `/ws/training` only (M-SEC-01 training-side).

**Why this subset first**: these are the DoS defenses. Phase B increases both the traffic volume and the attack surface on `/ws/training`. Without max_size guards, a single malicious 100 MB frame DoSes the server. Without per-IP caps, a single attacker exhausts the global cap. Without training-side origin validation, any page can subscribe to the training stream and exfiltrate state.

**Critically NOT in Phase B-pre-a**: `/ws/control` origin validation. That stays in Phase B-pre-b because it's tied to CSRF first-frame enforcement (they share the auth pathway). Browser-side control is not yet wired in Phase B (that's Phase D), so leaving `/ws/control` in the old state for Phase B-pre-a → Phase B is safe.

**Mandatory acceptance**:

1. Every `ws.receive_*()` call in cascor and canopy has an explicit `max_size` parameter. Audit pass verified by a pytest that `ast.parse()`s the source files and checks argument lists.
2. `cascor_ws_frame_too_large_total` metric present and test-fired in staging.
3. Per-IP cap unit tests cover increment/decrement race under `asyncio.gather` load (R0-02 IMPL-SEC-09). The test failing once is enough evidence to block merge.
4. Origin allowlist on canopy `/ws/training` (not yet `/ws/control`). Default list from R0-02 §4.1 with fail-closed empty-list semantics explicitly documented.
5. Training-stream `max_size = 4096` (not the 64 KB of `/ws/control`). Training is ping/pong only in the inbound direction; anything larger than 4 KB is a malformed client.

**Safety amplification beyond R0-02**:
- The ASCII tests `test_per_ip_counter_decrements_on_exception` (R0-02 IMPL-SEC-09) AND a new `test_per_ip_map_shrinks_to_zero` assertion that the `_per_ip_counts` map does NOT grow unboundedly: entries reaching 0 must be deleted, not left at 0. Guards against memory leak in long-running cascor with high IP churn.
- A pre-merge grep guard: `grep -r "receive_text\|receive_json\|receive_bytes" juniper-cascor/src/api/websocket/ juniper-canopy/src/main.py` must return zero matches where `max_size` is not set on the call. Add this as a tiny CI script `scripts/audit_ws_receive_calls.py`.

### 4.2 Phase B-pre-b (M-SEC-01/01b/02 full + M-SEC-05/06/07/10/11): hard Phase D prereq

**Scope**: full security bundle from R0-02 that was not in Phase B-pre-a. Origin validation for `/ws/control`, cookie + CSRF first-frame auth, rate limiting, opaque close reasons, audit logging, idle timeout, adapter-inbound schema validation.

**Must-have exit criteria (amplified from R0-02 §5.1)**:

All of R0-02 §5.1 criteria 1-13, PLUS:

14. **Kill-switch verified**: `Settings.disable_ws_control_endpoint=True` actually hard-disables `/ws/control` — verified by a test that starts canopy with the flag, attempts a WebSocket upgrade to `/ws/control`, and asserts HTTP 404 or similar. This is the CSWSH emergency lever from R0-06 RISK-15.

15. **`disable_ws_auth` flag direction resolved**: R0-02 §9.4 flagged this as a footgun. Safety-first resolution: rename to `ws_security_enabled: bool = True` (positive sense, default on). Local-dev developers opt OUT via `JUNIPER_WS_SECURITY_ENABLED=false`. A production config accidentally setting `JUNIPER_WS_SECURITY_ENABLED` to anything other than "true" is caught by a `juniper-deploy` CI guardrail per R0-02 IMPL-SEC-40.

16. **CSRF token rotation race test**: token is rotated mid-request; assert the current request completes normally, the next upgrade uses the new token, and the old token is rejected. This is the R0-02 §8.7 flicker risk made into a test.

17. **Audit-log write-failure fallback**: if the audit log file handler raises (disk full, permission denied), the control command IS still accepted BUT a `canopy_ws_audit_log_write_error_total` counter increments and a WARN logs to stderr. Safety-first rationale: a degraded audit log must not block legitimate user actions, but must be observable. Document this explicitly; by default most structured loggers swallow write errors silently.

18. **Per-origin handshake cooldown test**: 10 rejected handshakes from one IP within 60 s triggers the 5-minute cooldown; the 11th upgrade attempt gets HTTP 429. Verify in Playwright.

19. **Pre-merge staging soak of 48 hours** (not 24). Phase B-pre-b is higher-risk than average because it changes the auth path for every single dashboard request.

20. **Adapter synthetic auth frame resolved**: R0-02 §11 Q2-sec. Safety-first decision: the canopy adapter authenticates to cascor via a synthetic first-frame `{type: "auth", csrf_token: hmac(api_key, "adapter-ws")}`. The HMAC approach keeps the cascor handler uniform (no `X-Juniper-Role: adapter` branch). The small added complexity on the adapter side is worth removing a branch from the security-critical handler path.

### 4.3 Kill switches for Phase B-pre

| Switch | Who flips | MTTR | Effect |
|---|---|---|---|
| `JUNIPER_WS_SECURITY_ENABLED=false` | ops | 5 min | Disables Origin, cookie, CSRF checks. Local dev only; prod guardrail rejects this in compose validation |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disables `/ws/control`. CSWSH emergency lever. Forces all control through REST |
| `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | ops | 5 min | Effectively disables the per-IP cap. Only if a legitimate use case hits it (e.g., shared NAT with >5 legitimate users) |
| `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min | Disables command rate limiting. For an incident where the limit itself is the bug |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | Disables audit log writes. For disk-full emergencies |
| `JUNIPER_WS_ALLOWED_ORIGINS=*not allowed*` | ops | never | "*" is explicitly refused by the parser. This is a NON-kill-switch — documented so that an operator panicking during an incident does not try this |

The explicit non-switch for `*` is deliberate safety: during an incident, the temptation to "just allow everything and fix later" is strong. The config parser refusing `*` outright prevents a panic-edit from opening the CSWSH surface.

### 4.4 Disaster recovery: Phase B-pre

**Scenario**: Phase B-pre-b ships to production. Users report mass dashboard lockout. Cause is unknown.

**Recovery**:

1. **T+0**: on-call is paged (cookie/CSRF auth failure rate spikes).
2. **T+1 min**: on-call runs `juniper-canopy/notes/runbooks/ws-auth-lockout.md`. The runbook's first step is to check the lockout metric (`canopy_ws_auth_rejections_total` by `reason`).
3. **T+2 min**: if the metric shows widespread `cookie_missing`, the fix is "session middleware is broken or deployed wrong." Flip `JUNIPER_WS_SECURITY_ENABLED=false` and restart canopy. Users are unblocked.
4. **T+5 min**: users back online. Incident response begins.
5. **T+30 min**: post-mortem opened. Root cause analysis proceeds. The 5-minute MTTR is the kill-switch reason-to-exist.

**Abandon-migration trigger**: if the kill switch fails (flipping it to `false` does NOT restore functionality), we have a code bug in the kill-switch code path itself. This is an immediate abandon trigger per R0-06 §12.3. Rollback to pre-Phase-B-pre-b image.

**Pre-validation requirement**: the runbook and the kill switch are tested in staging during the 48-hour soak. Specifically: flip `JUNIPER_WS_SECURITY_ENABLED` off then on; verify functionality both ways. If this test is skipped in staging, Phase B-pre-b does not proceed to production.

---

## 5. Phase B with safety amplification

R0-01 defines Phase B as the browser bridge: Option B Interval drain, Plotly extendTraces, polling toggle, connection indicator, GAP-WS-24 browser emitter, dead-code removal. R0-01 §4 lists 31 implementation steps. Safety-first amplification adds guardrails, canary gates, and observability that must land alongside or before the behavior change.

### 5.1 Hard dependencies (vs "soft" in R0-01)

R0-01 §3.1 called the `seq` field and Phase B-pre-a "soft" dependencies — "Phase B can still ship" if they slip, behind a feature flag. The safety-first stance tightens this:

- Phase A-server (cascor seq + replay) MUST be in production (not just merged) before Phase B ships to production. Rationale: the whole point of Phase B is the WebSocket-driven dashboard, and without `seq` the reconnect path is non-existent. Staging Phase B against a Phase-A-server-free cascor is possible but not a pathway to production.
- Phase B-pre-a (M-SEC-03 max_size, per-IP cap, training-side origin) MUST be in production before Phase B ships. Rationale: Phase B increases traffic, and without these guards the attack surface is wider.
- Phase B-pre-b is NOT a hard prereq for Phase B, only for Phase D.

### 5.2 Feature-flag default: OFF (reversal from R0-01)

R0-01 implicitly assumes Phase B flips the browser bridge on at merge time (no feature flag on the read path, since it's a read-only migration). The safety-first stance is:

**Phase B ships behind `Settings.enable_ws_bridge: bool = False`.**

With the flag OFF, the dashboard uses the pre-Phase-B REST polling (GAP-WS-16 is not yet fixed — the 3 MB/s regression returns). With the flag ON, the WebSocket bridge is live.

**Why bother with a flag on a "safe" read-side migration**:
1. Phase B is the highest-risk phase per R0-06 RISK-02 (High likelihood). A single clientside_callback bug can hang the dashboard with no server-side signal.
2. The flag lets us canary Phase B across dev / staging / canary cohorts without a code rollback. Rollback is a config flip.
3. The dead-code that Phase B removes (the parallel raw WebSocket client at `dashboard_manager.py:1490-1526` per R0-01 §3.5.2) is NOT deleted in the same PR that ships the flag. Deletion happens in a follow-up PR after Phase B has been in production for one release cycle with the flag ON. This preserves the rollback lever.

**Flag lifecycle**:

| Stage | Default | Trigger |
|---|---|---|
| Merge to main | False | — |
| Staging deploy | True | Ops flips it on; runs for 72h soak |
| Canary (dev + small canopy cohort) | True | After staging pass |
| Production default flip | True | After canary pass; separate config PR |
| Flag removal | — | NOT in this migration. Done in a follow-up PR ≥1 release cycle after prod flip |

### 5.3 REST fallback retention (strengthened from R0-01)

R0-01 §3.4.2 correctly keeps the REST polling handler. Safety-first amplification:

**The REST polling handler must remain reachable for as long as the feature flag exists** AND then remain as the dormant-but-intact fallback for as long as the flag's kill switch exists. That means **forever** per the principle 7 in §1.2.

**No deletion of the REST polling code is in scope for this migration.** R0-01 §3.4.2 slowed polling from 100 ms to 1 Hz during disconnect windows — that is safety-first and accepted. But the polling callback body, the REST endpoint, and the fetch path all stay exactly as they are for the foreseeable future.

**Connection-status-aware drain latency**: R0-01 proposed the 100 ms drain interval. Safety-first accepts this but adds a tripwire: if `canopy_ws_drain_callback_gen` gauge stops advancing for >2 minutes (drain callback has died), fire `WSDrainCallbackGenStuck` alert and flip the connection status to `reconnecting` so the polling toggle reverts to REST fallback. This closes the "clientside callback silently dies" failure mode that R0-01 FR-RISK-10 acknowledges.

### 5.4 Bounded ring: principle-enforced

R0-01 §3.2.5 correctly argues the ring bound lives in the `on('metrics', ...)` handler, not the drain callback, because of background tab throttling. Safety-first agrees and amplifies:

**The ring bound is a compile-time invariant**, meaning:

1. Every `on(type, ...)` handler in `ws_dash_bridge.js` that appends to a ring MUST include the splice-to-cap logic in the handler body. Not in a helper. Not in the drain. In the handler, visible at the append site.
2. A JS unit test (Jest/Vitest) walks the compiled/bundled `ws_dash_bridge.js`, finds every `on(` call site, and asserts the subsequent `push(...)` is followed by a `splice(...)` or `length > MAX_*` check within the same function body. This is an AST-based lint, not a runtime check.
3. The constants `MAX_METRICS_BUFFER = 1000` and `MAX_EVENT_BUFFER = 500` are exported from a single module-scope constant block so they are grep-able and can be lowered in an emergency.

**Emergency lever**: if a browser OOM is observed, operators can ship a 1-line config or env-var override that caps the buffers lower. The JS ring is not server-controlled today; as a follow-up item, add a `window.__canopy_ring_caps = {metrics: 500, events: 250}` override that the bridge reads at init. Not a Phase B requirement; Phase B ships with the hardcoded constants.

### 5.5 rAF coalescing: DISABLED by default (reinforcing R0-01 §7 disagreement #1)

R0-01 §7 disagreement #1 scaffolded rAF coalescing but kept it disabled. Safety-first strongly agrees.

Amplification: the rAF scheduler lives in `ws_dash_bridge.js` as a `_scheduleRaf = function() { /* noop */ }`. Enabling it requires a single-line change AND passing a new gate: `canopy_ws_delivery_latency_ms{type="metrics"}` p95 must be >300 ms for ≥24h AND the browser heap histogram must show no memory cliff. In other words, rAF coalescing is a Phase B+1 optimization triggered by evidence, not scheduled.

### 5.6 Acceptance gate for Phase B (amplified from R0-01 §6)

All 20 acceptance criteria from R0-01 §6, PLUS:

**AC-21 (flag default False)**: with `enable_ws_bridge=False`, Phase B code must NOT affect the dashboard. Regression test.

**AC-22 (kill-switch verified)**: flipping `enable_ws_bridge=True→False` at runtime (requires restart for a Python Settings, acceptable) takes ≤5 minutes end-to-end. Measured in staging.

**AC-23 (REST polling untouched)**: grep-based assertion that `_update_metrics_store_handler` still exists, still calls `requests.get`, and is still wired to `fast-update-interval`. Fence against an over-eager refactor.

**AC-24 (72-hour memory soak)**: staging runs for 72 hours with `enable_ws_bridge=True` and a live training job. `canopy_ws_browser_heap_mb` p95 does not grow by more than 20% over the 72 hours. RISK-10 memory-exhaustion gate.

**AC-25 (drain-gen advances)**: `canopy_ws_drain_callback_gen` gauge for every buffer type advances at least once per minute during an active training run. Guard against a dead callback loop.

**AC-26 (polling reduction proof)**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` drops by ≥90% when `enable_ws_bridge=True` AND WebSocket is healthy, compared to the pre-Phase-B baseline. The P0 motivator is measured per-endpoint, not aggregate.

**AC-27 (demo-mode parity)**: `test_demo_mode_metrics_parity` green. R0-01 already mandates this; it is a hard Phase B gate.

**AC-28 (browser JS error counter zero)**: over the 72-hour soak, `canopy_ws_browser_js_errors_total` == 0. Any non-zero value is a Phase B regression, period. Investigate and fix before production.

**AC-29 (no hidden seq gaps in store)**: a new `dash_duo` test asserts that `ws-metrics-buffer.data.events` is monotonic in `seq` with no gaps >1. Not strictly a Phase B requirement (the drain callback doesn't reorder) but the test is cheap and catches a whole class of Phase A-server regressions from downstream.

### 5.7 Canary plan for Phase B

**Dev**: all developers opt in locally via `JUNIPER_CANOPY_ENABLE_WS_BRIDGE=true` once Phase B is merged. Must be green for 1 week in dev.

**Staging**: 72 hours soak with flag ON, live training job, soak metrics monitored. Specifically watching AC-24 (memory), AC-26 (polling reduction), AC-28 (JS errors).

**Canary cohort**: single-tenant deployment means "canary = Paul's laptop for a week." Multi-tenant future: a feature-flagged subset of dashboards.

**Production flip**: a single-line config PR that sets the default to True. Reviewed explicitly by the project lead. Merge window is mid-week, not Friday afternoon.

### 5.8 Disaster recovery: Phase B

**Scenario**: Phase B is enabled in production. Users report the dashboard is frozen / missing data / the chart doesn't update.

**Recovery**:

1. **T+0**: alert `WSDrainCallbackGenStuck` or `WSDeliveryLatencyP95High` fires.
2. **T+1 min**: on-call runs `juniper-canopy/notes/runbooks/ws-bridge-debugging.md`. First step: check `canopy_ws_connection_status` and `canopy_ws_browser_js_errors_total` panels.
3. **T+3 min**: if JS errors spiked, capture the browser console via the existing canopy error-reporter pipeline. If drain-gen is stuck with no JS errors, the issue is deeper (Dash graph state).
4. **T+5 min**: flip `JUNIPER_CANOPY_ENABLE_WS_BRIDGE=false`. Restart canopy. Users see the dashboard on REST polling within 5-10 seconds of restart.
5. **T+15 min**: incident is contained. Post-mortem opens. 3 MB/s REST polling is back temporarily — not ideal, but users are functional.
6. **T+days**: fix is developed, tested against the regression scenario, re-enabled carefully.

**Abandon trigger**: if two consecutive Phase B rollouts produce the same failure mode, halt the migration. Re-plan the bridge design.

---

## 6. Phase C with safety amplification

R0-04 defines Phase C as the canopy adapter migration: `apply_params` hot/cold split with WS for hot params and REST for cold. Feature-flagged via `use_websocket_set_params=False`. Safety-first amplification is modest because R0-04's design is already conservative.

### 6.1 Flag default: OFF (aligned with R0-04)

R0-04 §5.2 already specifies the flag defaults False and ships with unconditional REST fallback. Safety-first accepts this with one tightening: the flag flip criteria are enumerated below as hard gates, not soft guidance.

**Minimum evidence to flip the production default**:

1. **Metric coverage proven**: `canopy_set_params_latency_ms{transport=rest}` has ≥7 days of production data. `canopy_set_params_latency_ms{transport=ws}` has ≥7 days of canary data.
2. **Delta is meaningful**: p99 latency difference (rest - ws) is ≥50 ms. If it's smaller, the flip provides no user-visible win and introduces RISK-03/09 unnecessarily. Do not flip.
3. **Zero orphaned commands**: `canopy_orphaned_commands_total` is 0 during the canary week. A single orphaned command is enough to delay the flip until investigated.
4. **Zero correlation-map leaks**: R0-04 R04-01. A test of `len(_pending)` after 1000 randomized failure modes shows it returns to 0. Nightly CI asserts.
5. **User-research signal (optional)**: if §5.7 of the arch doc is run, ≥3 of 5 subjects report "feels more responsive." If skipped, the latency delta criterion alone is sufficient.
6. **Canary soak duration**: ≥7 days of `use_websocket_set_params=True` in canary with no incidents.

If any criterion fails, the default stays False. No partial flips.

### 6.2 Kill switches for Phase C

| Switch | Who flips | MTTR | Effect |
|---|---|---|---|
| `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | ops | 2 min | All params route through REST. R0-04's primary rollback |
| Set `Settings.ws_set_params_timeout=0.1` | ops | 5 min | Tight WS timeout forces fast fallback to REST |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | Hard-disable `/ws/control`; Phase C falls back to REST. Reuse of the Phase B-pre kill switch |
| Revert Phase C PR | ops | 15 min | Full rollback of the hot/cold split. REST path preserved intact so no fallback to test |

### 6.3 Disaster recovery: Phase C

**Scenario**: Phase C flag is flipped ON in production. Sliders start misbehaving — changes don't take effect, or take effect on the wrong parameter.

**Recovery**:

1. **T+0**: user reports or `canopy_orphaned_commands_total` spike.
2. **T+1 min**: on-call flips `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`. Restart canopy.
3. **T+2 min**: dashboard falls back to REST. Sliders work. User confirms.
4. **T+5 min**: incident is contained. Latency is back to pre-Phase-C (tolerable per §5.3.1 analysis).
5. **T+days**: fix is developed.

**Abandon trigger**: if the Phase C flag flip triggers RISK-03 (ordering race) in production despite the disjoint hot/cold sets, the root cause is likely a param being added to one set without classification. Document the leak, add a test, re-plan the flip.

### 6.4 Safety amplification on R0-04's design

R0-04 §5.1 correctly defaults unknown keys to REST with a WARNING log. Safety-first adds:

1. **Fail loud on startup, not on first use.** On `cascor_service_adapter` init, when `use_websocket_set_params=True` is first observed, log an INFO-level summary of the hot/cold/unknown classification for every known canopy param. This gives operators a one-shot view of what the migration will route where, before it actually routes anything.

2. **Reject the flag if `_HOT_CASCOR_PARAMS` is empty.** If a refactor silently empties the hot set, the flag becomes a no-op and the rollout would look successful despite shipping nothing. Adapter init asserts `len(_HOT_CASCOR_PARAMS) > 0 when use_websocket_set_params=True`.

3. **Bound the correlation map.** R0-04 §4.5 introduces `_pending: Dict[str, Future]`. Add a max size (e.g., 256) and a `len(_pending)` Prometheus gauge. If it exceeds the max, reject new commands with a specific exception AND alert. This is a belt-and-suspenders against the R04-01 leak.

---

## 7. Phases D/E/F/G with safety amplification

### 7.1 Phase D — Control buttons via WebSocket

**Gated on**: Phase B-pre-b complete (M-SEC-01 `/ws/control` origin, M-SEC-02 CSRF), Phase B in production with `enable_ws_bridge=True` stable for ≥2 weeks.

**Feature flag**: `enable_ws_control_buttons: bool = False`. When False, buttons use the existing REST POST endpoints.

**Acceptance gate**:

- All Playwright tests from R0-05 §9.5 green.
- `test_csrf_required_for_websocket_start` green.
- REST POST endpoints remain functional (regression gate).
- `canopy_training_control_total{transport="rest"}` still receives traffic from non-browser consumers after Phase D merges.
- 48-hour staging soak with the flag ON.
- Canary cohort at flag ON for ≥48 hours with zero orphaned command reports.

**Disaster recovery**: flip the flag off. REST path is preserved. 5-minute MTTR.

### 7.2 Phase E — Backpressure

**Default policy**: the safety-first stance is `drop_oldest_progress_only` (R0-06 §13.2 disagreement, accepted). Rationale: `block` (R0-03's default preserving behavior) leaves RISK-04 in place. `close_slow` (R0-03 aggressive) disconnects transiently-slow clients who are actually fine. `drop_oldest_progress_only` is the middle ground that mitigates RISK-04 and RISK-11 both.

**Feature flag**: `ws_backpressure_policy` default `drop_oldest_progress_only`. Values: `{block, drop_oldest_progress_only, close_slow}`. Operators can revert to `block` via config if the new default misbehaves.

**Canary**: staging for 48 hours with the new default. Watch `cascor_ws_dropped_messages_total{type="state"}` for non-zero (should remain 0 — `state` events close, not drop). Watch `cascor_ws_broadcast_timeout_total` rate.

**Acceptance**: R0-05 §9.6 test list + metric coverage + 48-hour soak.

**Disaster recovery**: flip the config to `block`. Restart cascor. RISK-04 returns but RISK-11 goes away. Documented as a deliberate choice during an incident.

### 7.3 Phase F — Heartbeat + reconnect jitter

**Default**: jitter is always on (trivial 3-line change). Reconnect cap raised from 10 to unbounded per R0-01 §3.5.1 item 4 and R0-06 RISK-06.

**Kill switch**: `disable_ws_auto_reconnect: bool = False`. Set True during a reconnect storm. Users see stale dashboards and must hard-refresh.

**Acceptance**: R0-05 §9.7 test list. `WSReconnectStorm` alert rule in place.

**Disaster recovery**: if a reconnect storm hits production despite jitter, flip `disable_ws_auto_reconnect=true` globally. Users are asked to hard-refresh. 10-minute MTTR.

### 7.4 Phase G — Cascor set_params integration test

**Purpose**: closes GAP-WS-10. Test-only phase; no runtime change.

**Amplification**: the test suite added in Phase G is marked `@pytest.mark.critical` and runs in the `fast` lane on every PR to cascor or cascor-client. Not optional.

**No kill switch, no canary**: this phase is test-only.

### 7.5 Phase H — `_normalize_metric` audit

**Gate**: the regression test `test_normalize_metric_produces_dual_format` MUST merge BEFORE the audit begins. R0-06 §13.7 proposes a CODEOWNERS rule; safety-first accepts and adds:

- CODEOWNERS entry requires explicit review from the project lead on any PR touching `_normalize_metric` or any file that imports it.
- A `pre-commit` hook that refuses commits removing the nested format keys from the normalize output (static check against a hardcoded expected shape).

**Kill switch**: none needed (test-only + doc phase).

**Abandon trigger**: if the audit finds a consumer that relies on the nested format silently, the audit output is expanded to catalogue the consumer and defer removal. Never remove the format based on an incomplete audit.

### 7.6 Phase I — Asset cache busting

**Required co-shipping**: bundled with Phase B per R0-06 §3.6.

**Why this is safety-critical**: without it, browsers see stale `websocket_client.js` and the Phase B flag flip fails to take effect in the browser even though it took effect server-side. This is a pernicious failure mode because the server reports "Phase B is on" and the client is still on the old code.

**Kill switch**: reverting asset cache busting is a revert of the Phase I PR. Harmless because the old behavior (no cache bust) is functional.

**Acceptance**: R0-05 §9.10 + a new assertion: after Phase B ships, `canopy_ws_active_connections` increases by >0 (browsers are actually connecting). If the gauge stays at 0 post-deploy, asset cache busting did not take effect or the flag is not wired.

---

## 8. Kill switch matrix

A single consolidated table. Every phase's kill switch, who flips it, MTTR, blast radius, validation that the flip worked.

| Phase | Switch | Who flips | MTTR | Blast radius | Validation the flip worked |
|---|---|---|---|---|---|
| A-server | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | ops | 5 min | All clients resume via snapshot path | `cascor_ws_resume_requests_total{outcome="out_of_range"}` spike |
| A-server | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | ops | 5 min | Slow clients pruned aggressively | `cascor_ws_broadcast_timeout_total` spike |
| A-server | Revert PR | ops | 15 min | Clients with cached UUIDs get `resume_failed` | Client logs show snapshot refetch |
| A (SDK) | Downgrade `juniper-cascor-client` pin | ops | 15 min | SDK consumers revert to pre-set_params | `pip index versions` shows resolved version |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | ops | 5 min | Per-IP cap neutralized | `canopy_ws_per_ip_rejected_total` drops to 0 |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | ops | 5 min | Auth disabled; dev-only; prod CI guardrail refuses | `canopy_ws_auth_rejections_total` drops to 0 |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | `/ws/control` hard-disabled; commands route through REST | `canopy_training_control_total{transport="ws"}` drops to 0 |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min | Rate limiting off | `canopy_ws_rate_limited_total` freezes |
| B-pre-b | `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | Audit log writes disabled | No new writes to audit log file |
| B | `JUNIPER_CANOPY_ENABLE_WS_BRIDGE=false` | ops | 5 min | Dashboard falls back to REST polling (3 MB/s returns) | `canopy_rest_polling_bytes_per_sec` rises to baseline |
| B | Hardcoded buffer cap reduction | developer | 1 hour | Browser memory tighter, potential data loss | Browser heap drops in soak metrics |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | ops | 2 min | All params route through REST | `canopy_set_params_latency_ms{transport="ws"}` count freezes |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | ops | 5 min | Buttons revert to REST POST | `canopy_training_control_total{transport="rest"}` rises |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | ops | 5 min | Old behavior; RISK-04 returns | `cascor_ws_dropped_messages_total` drops to 0 |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | ops | 10 min | Clients do not reconnect; user hard-refresh | `canopy_ws_reconnect_total` drops to 0 |
| H | `git revert` normalize_metric PR | ops | 10 min | Old metric format restored | Prometheus `/api/metrics` shape hash matches pre-Phase-H |
| I | `git revert` cache busting PR | ops | 10 min | Browsers see stale JS (usually harmless) | Asset URL query string returns to old form |

**Meta-rule**: every kill switch in this table has a CI test in its origin phase's test suite that flips the switch and verifies the validation metric moves. R0-06 §5.3 rule 3 ("tested") is made explicit here: if the test is not present, the switch does not count and the phase does not ship.

---

## 9. Disaster recovery scenarios

For each phase, answer: "what is the worst thing this phase could do, and how do we recover?"

### 9.1 Phase A-server — Worst case: seq/replay corruption causes silent data loss

**Scenario**: a bug in `_assign_seq_and_append` makes seq assignment non-monotonic under concurrent broadcast. Clients de-duplicate by seq and silently drop legitimate events. Dashboards look functional but metrics history has gaps.

**Detection**: `cascor_ws_seq_current` gauge does not advance linearly. `WSSeqCurrentStalled` alert fires. AC-29 test (monotonic seq in store) fails in canary.

**Containment**: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` forces snapshot refetch. Buys time.

**Recovery**: rolling-restart cascor to flush `_next_seq`. All clients reconnect, get fresh `server_instance_id`, snapshot-refetch, proceed.

**Root cause analysis**: the chaos test added in §3.1 (item 29) should have caught this. If it didn't, add it to the test suite before the fix merges.

### 9.2 Phase A (SDK) — Worst case: `_pending` correlation map leaks indefinitely, client process OOMs

**Scenario**: R0-04 R04-01 realized. Adapter calls `set_params` thousands of times. Each leaked entry holds a Future. Canopy process memory grows unbounded.

**Detection**: `canopy_process_resident_memory_bytes` gauge grows linearly over time. `len(_pending)` Prometheus gauge (added in §6.4 amplification) crosses 256.

**Containment**: flip `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`. The leaky code path is quiesced.

**Recovery**: restart canopy. Memory is freed.

**Root cause analysis**: the `test_len_pending_returns_to_zero_after_failure_modes` nightly test should fire. If it didn't, expand the failure modes covered.

### 9.3 Phase B-pre-a — Worst case: per-IP cap misconfigured, valid users locked out

**Scenario**: `JUNIPER_WS_MAX_CONNECTIONS_PER_IP` is accidentally set to 0 via a config typo. Every dashboard is rejected on upgrade.

**Detection**: `canopy_ws_per_ip_rejected_total` spikes. User reports.

**Containment**: flip `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=5` (correct default). Restart canopy.

**Recovery**: users reconnect. 5-minute MTTR.

**Prevention**: add a config validator that refuses `ws_max_connections_per_ip < 1`. Not a runtime-critical bug but closes the footgun.

### 9.4 Phase B-pre-b — Worst case: CSWSH kill switch itself is broken

**Scenario**: a production CSWSH attack is observed. Operator flips `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` and restarts. `/ws/control` is still reachable because the flag code path has a bug.

**Detection**: attack continues after flag flip. Operator is in a very bad place.

**Containment**: rolling-restart with a hardcoded denial in `main.py` (`@app.websocket("/ws/control") async def ...: await ws.close(code=1013)`). Requires a code change; this is the ~30-minute MTTR path.

**Recovery**: after the immediate fix, revert Phase B-pre-b entirely. Investigate the kill-switch bug in the post-mortem.

**Prevention**: the kill-switch test must be part of the PR acceptance criteria (§4.2 item 14 above). If the test was skipped, document and add it retroactively.

**Abandon trigger**: this is the worst case. If it happens, the migration is HALTED until we can demonstrate all kill switches are trustworthy.

### 9.5 Phase B — Worst case: browser bridge causes a memory leak, dashboards become unusable after ~1 hour

**Scenario**: the JS ring buffer has an off-by-one and grows without bound. After ~1 hour, the browser tab hangs.

**Detection**: `canopy_ws_browser_heap_mb` p95 growth > 10 MB/hour. User reports "dashboard froze after running overnight."

**Containment**: flip `JUNIPER_CANOPY_ENABLE_WS_BRIDGE=false`. Dashboards revert to REST polling on next restart (canopy) or next browser refresh.

**Recovery**: users hard-refresh. REST polling is back. 3 MB/s is tolerable as a fallback until the fix.

**Prevention**: AC-24 (72-hour soak) should have caught this. If it didn't, extend the soak to 7 days for future Phase B-like changes.

### 9.6 Phase C — Worst case: slider changes apply to the wrong parameter

**Scenario**: a bug in hot/cold classification routes a hot param to the REST path AND a cold param to the WS path. The WS path's server-side `lifecycle.update_params` accepts both, but because the cold param mutation interleaves with a REST mutation of a different key, the final state is wrong.

**Detection**: `canopy_orphaned_commands_total` spike. User reports "I set learning_rate to 0.005 and the chart shows 0.01."

**Containment**: flip `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`. All params route through REST. Last-write-wins semantics.

**Recovery**: 2-minute MTTR. Investigate classification bug in post-mortem.

### 9.7 Phase D — Worst case: a stuck `/ws/control` session holds a reset command, causing a destructive no-op

**Scenario**: user clicks "reset" while a training run is in progress. The command routes through WS. The WS send succeeds but the ack is slow. The user clicks "start" believing the reset failed. Start executes first, then reset executes, wiping the just-started run.

**Detection**: training state flapping. User frustration.

**Containment**: flip `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`. Buttons revert to REST POST. Each click is a distinct HTTP request, clearer sequencing.

**Recovery**: 5-minute MTTR.

**Prevention**: per-command `pending verification` UI state (GAP-WS-32). The button is disabled while a command is in-flight.

### 9.8 Phase E — Worst case: drop-oldest-progress policy loses a terminal event

**Scenario**: cascor emits a `training_complete` event classified under `candidate_progress` due to a schema bug. The drop-oldest policy drops it. The client never learns the run completed.

**Detection**: training run appears to be in-progress forever. No `WSStateDropped` alert because the event was in the wrong category.

**Containment**: `JUNIPER_WS_BACKPRESSURE_POLICY=block`. Old behavior; terminal events no longer drop.

**Recovery**: 5-minute MTTR. Investigate the schema bug.

**Prevention**: unit test `test_event_type_classification_for_backpressure_policy` asserts every type from `messages.py` maps to the expected policy bucket. If a new event type is added to `messages.py` without an explicit policy mapping, the test fails.

### 9.9 Phase F — Worst case: jitter bug creates NaN delays, no reconnect ever happens

**Scenario**: `Math.random()` interacts with a bug in the jitter formula, producing `NaN`. `setTimeout(NaN)` schedules immediately, triggering a reconnect storm. Or it produces `Infinity`, no reconnect ever.

**Detection**: `canopy_ws_reconnect_total` either spikes or freezes.

**Containment**: flip `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`. Users hard-refresh.

**Recovery**: 10-minute MTTR.

**Prevention**: the `test_reconnect_backoff_has_jitter` test from R0-05 §4.2 needs a tighter assertion: `delay is a number AND 0 <= delay <= cap`.

### 9.10 Phase H — Worst case: audit accidentally removes a format consumer relies on

**Scenario**: the audit concludes no consumer relies on the nested format. The removal PR merges. A consumer (possibly an external integration outside the test coverage) breaks.

**Detection**: external integration failure report.

**Containment**: `git revert` the normalize_metric change. Redeploy canopy.

**Recovery**: 10-minute MTTR.

**Prevention**: Phase H is test-only in this proposal. No removal PR is in scope. If a future PR proposes removal, it must explicitly re-run this scenario analysis.

### 9.11 Phase I — Worst case: cache busting breaks the CDN / dev iteration loop

**Scenario**: the `assets_url_path` query-string scheme does not match the dev server's asset-serving code. Dev server returns 404 for every request. No asset loads.

**Detection**: the app is broken on every page load.

**Containment**: revert Phase I PR.

**Recovery**: 5-minute MTTR.

---

## 10. Test coverage requirements (R0-05 + safety lens)

R0-05 §4-§9 lays out a detailed test plan. Safety-first amplification raises the bar in three places:

### 10.1 Chaos tests (new category)

R0-05 mentions fuzzing for security envelopes. Safety-first adds formal chaos tests:

1. **Cascor broadcaster chaos**: `hypothesis` + `asyncio.gather` driving 100 concurrent broadcast/disconnect/resume operations against the `WebSocketManager`. Assert: no deadlocks, no seq gaps, no leaked coroutines. Runs in the `nightly` lane.

2. **Browser bridge chaos**: Playwright script that randomly kills and restarts the WebSocket server between messages, varies the event rate, and corrupts the occasional envelope. Assert: browser does not OOM, does not freeze, chart data-point count never exceeds `maxPoints`. Runs in `nightly`.

3. **Adapter recv-task chaos**: R0-04 §6.3 worries about `_recv_task` crashing. Chaos test injects random `Exception` types inside the recv loop, asserts the pending map is always fully drained and the supervisor restarts the task.

4. **Replay race chaos**: R0-03 §8.4 race between `replay_since` and ongoing broadcast. Chaos test ran in §3.1 above.

### 10.2 Fuzz tests (amplified)

R0-02 §7.3 lists `hypothesis` and `atheris` targets. Safety-first amplification:

- Every target must run in `nightly` CI (not just "recommended"). Nightly failure is a ticket, not a blocker.
- Fuzz corpus is checked into the repo under `tests/corpus/ws-envelopes/` so a regression can be rerun against the last-failing inputs without re-fuzzing.
- A `test_fuzz_regression` test loads the corpus and replays every case as a standard unit test. Runs in `fast` lane. Ensures corpus inputs remain non-crashing.

### 10.3 Load tests (elevated to gate)

R0-05 §10.4 lists load tests as "recommended but optional." Safety-first elevates:

- R0-05 test 26 (broadcast at 100 Hz for 60 s with 10 clients) becomes a **blocking gate** for Phase A-server. Without it, Phase A-server does not ship.
- R0-05 test 27 (rolling reconnect) becomes blocking for Phase A-server.
- Add: a 10-minute sustained load test with 25 simulated clients. Asserts p95 delivery latency < SLO, memory stable ±10%, no kill-switch triggers fire.

### 10.4 Security regression (hardened)

R0-05 §7 lists per-M-SEC tests. Safety-first adds:

- **Threat-model review gate**: any PR touching `juniper-cascor/src/api/websocket/*.py`, `juniper-canopy/src/main.py`, or `juniper-canopy/src/backend/ws_security.py` must include a one-line threat-model acknowledgement in the PR description. Enforced by a GitHub PR template rule or a CODEOWNERS rule.

- **Kill-switch verification tests** (new): for every kill switch in §8 above, a test that flips the switch, observes the expected metric move, flips it back, observes the reverse. Runs in `security` lane.

### 10.5 CI lane ordering and gates

R0-05 §10 defined `fast`, `e2e`, `security`, `nightly`. Safety-first stance:

- `security` runs on EVERY PR, including drive-by changes to unrelated files. Rationale: a spelling fix that touches `main.py` could accidentally remove an Origin check. Paranoid but cheap.
- `e2e` runs on PR-to-main AND on merges to main. The latter catches a race where two PRs green individually but break when combined.
- `nightly` runs the chaos, fuzz, and soak tests. Failure in nightly is a must-fix within the next business day, not next week.

### 10.6 Metrics-presence test (new)

Before any observability-dependent phase ships, a pytest scrapes Prometheus `/metrics` and asserts every required metric from §2 above is present. This is a cheap, high-value gate that turns "did we remember to wire up the metric" from a manual review question into a CI check.

---

## 11. Risk register reconciliation

All 16 RISK-NN items from R0-06 §4 with safety-first mitigations. Where this proposal tightens or weakens a mitigation versus R0-06, it's noted.

### RISK-01 — Dual metric format removed aggressively

- **Phase**: H
- **Safety stance**: R0-06 mitigations accepted and tightened. CODEOWNERS rule + pre-commit hook + no removal in this migration. Deletion is out of scope.
- **Kill switch**: git revert Phase H PR. 5-minute MTTR.
- **Tighter**: R0-06 allowed Phase H to ship the audit outcomes. Safety-first Phase H is test-and-document only; removal is never in this migration.

### RISK-02 — Phase B clientside_callback wiring hard to debug

- **Phase**: B
- **Safety stance**: added `canopy_ws_drain_callback_gen` metric and `WSDrainCallbackGenStuck` alert (§2.2, §2.4). Added `canopy_ws_browser_js_errors_total` counter (§2.2). Flag default False (§5.2). 72-hour staging soak (§5.7).
- **Kill switch**: `JUNIPER_CANOPY_ENABLE_WS_BRIDGE=false`. 5-minute MTTR.

### RISK-03 — Phase C REST+WS ordering race

- **Phase**: C
- **Safety stance**: R0-04 mitigations accepted. Added §6.4 safety amplification: assertion at startup that hot set is non-empty, bounded correlation map, per-startup classification summary log.
- **Kill switch**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`. 2-minute MTTR.

### RISK-04 — Slow-client blocking

- **Phase**: E
- **Safety stance**: R0-06 §13.2 accepted: Phase E default becomes `drop_oldest_progress_only`. Quick-fix 0.5 s timeout ships in Phase A-server (hotfixable independently).
- **Kill switch**: `ws_backpressure_policy=block`. 5-minute MTTR. Trade-off documented.

### RISK-05 — Playwright fixture misses real-cascor regression

- **Phase**: B, D
- **Safety stance**: weekly smoke test against real cascor (per R0-06). No kill switch (coverage risk).
- **Amplification**: the smoke test runs nightly, not weekly. Daily cadence closes the gap faster.

### RISK-06 — Reconnect storm after cascor restart

- **Phase**: F
- **Safety stance**: jitter always on; reconnect cap lifted to unbounded. Kill switch = `disable_ws_auto_reconnect`. 10-min MTTR.
- **Amplification**: jitter MUST be deployed to both canopy and cascor before any cascor restart is scheduled. Pre-restart checklist item.

### RISK-07 — 50-connection cap in multi-tenant

- **Phase**: parallel; not in this migration
- **Safety stance**: single-tenant assumed (§9 Q1 resolved). Per-IP cap of 5 is the near-term mitigation. Multi-tenant is future work.

### RISK-08 — Demo-mode parity breaks

- **Phase**: B
- **Safety stance**: R0-06 mitigation accepted (test is blocking). `test_demo_mode_metrics_parity` is in AC-27 (§5.6).
- **Amplification**: the demo-mode test is in the `fast` lane, not `e2e`, so it runs on every PR.

### RISK-09 — Phase C unexpected user-visible behavior

- **Phase**: C
- **Safety stance**: feature flag default False; enumerated flip criteria (§6.1). Canary ≥1 week.
- **Kill switch**: `use_websocket_set_params=false`. 2-min MTTR.

### RISK-10 — Browser memory exhaustion

- **Phase**: B
- **Safety stance**: R0-01 mitigations accepted. Added 72-hour soak as AC-24. Ring-bound-in-handler as compile-time invariant. Emergency ring-cap override as follow-up item.
- **Kill switch**: disable bridge + developer-flavored ring cap reduction.

### RISK-11 — Silent data loss via drop-oldest

- **Phase**: E
- **Safety stance**: `drop_oldest_progress_only` is the new default. State-bearing events close the slow client, never drop. Per-type policy assertion test (§9.8 prevention).
- **Kill switch**: revert to `block` (loses RISK-11 mitigation, gains RISK-04).

### RISK-12 — Background tab memory spike

- **Phase**: B
- **Safety stance**: same as RISK-10. Ring-bound-in-handler explicit.

### RISK-13 — Orphaned commands after timeout

- **Phase**: B, C, D
- **Safety stance**: GAP-WS-32 per-command correlation IDs. `pending verification` UI state. `canopy_orphaned_commands_total` alert.
- **Amplification**: alert threshold is 1/min, not "any." R0-06's 1/min is accepted; amplification is that the alert goes to ticket queue, not page, because orphaned commands are usually benign. Paging on 1/min would be noisy.

### RISK-14 — Cascor crash mid-broadcast leaves clients inconsistent

- **Phase**: B (replay protocol) + A-server (server_instance_id)
- **Safety stance**: server_instance_id change forces REST resync on reconnect. `WSSeqCurrentStalled` alert catches the broadcast-loop hang early.
- **Kill switch**: rolling restart of canopy (bounces connections) or cascor (gets new UUID).

### RISK-15 — CSWSH attack

- **Phase**: B-pre
- **Safety stance**: R0-02 mitigations accepted and amplified. M-SEC-01 + 01b + 02 are hard Phase D gates. CODEOWNERS rule on websocket/*.py files. `WSOriginRejection` is **page** severity.
- **Kill switch**: `disable_ws_control_endpoint=true` hard-disables `/ws/control`. 5-min MTTR.

### RISK-16 — Topology >64 KB silent truncation

- **Phase**: B-pre (size guards surface it) + follow-up chunking
- **Safety stance**: size guards ship in Phase B-pre-a. `ws_oversized_frame_total` alert. REST fallback for topology remains as the client-side escape hatch.
- **Kill switch**: fall back to REST `/api/topology`.

---

## 12. Reconciled disagreements

Where Round 0 proposals contradict each other, safety-first picks the safer option and explains the tiebreaker.

### 12.1 Replay buffer size — R0-03 says 1024, this proposal says 256

- **R0-03 §3.1**: 1024 entries = ~40 s of history, comfortable default.
- **R0-01 §3.2.1**: separately uses `MAX_METRICS_BUFFER = 1000` on the browser side for the drain store. R0-01's 1000 is client-side and unrelated to cascor's 1024.
- **Safety-first**: 256 on cascor side (§3.2). Smaller default exercises the `out_of_range` snapshot-refetch code path more often in dev and staging, which keeps it reliable. Operators can raise it later based on production evidence.
- **Tiebreaker**: "rare failure paths become brittle" outweighs "fewer reconnect round-trips to REST snapshot."

### 12.2 Phase C timeout — R0-04 says 1.0 s, R0-03 / arch doc §7.1 say 5.0 s

- **R0-04 §12.1**: 1.0 s aligns with GAP-WS-32 tight-loop budget.
- **Arch doc §7.1**: 5.0 s as default.
- **Safety-first**: accept R0-04's 1.0 s as the SDK default. Callers needing a larger timeout can pass `timeout=5.0` explicitly.
- **Tiebreaker**: a stuck 5 s timeout is a visibly bad slider UX. 1 s is tight but survivable. The kill switch (flip the flag to False) provides the emergency fallback.

### 12.3 Phase E backpressure default — R0-03 says `block`, R0-06 says `drop_oldest_progress_only`

- **R0-03 §5.2**: `block` is the legacy behavior; preserve on major version bump.
- **R0-06 §13.2**: `drop_oldest_progress_only` to avoid RISK-04 immediately.
- **Safety-first**: R0-06's position accepted (§7.2). Shipped with config flag to revert.
- **Tiebreaker**: RISK-04 is Medium likelihood, Medium severity. Shipping the mitigation as the default is safer than shipping the known-broken behavior.

### 12.4 Adapter auth to cascor — R0-02 open question

- **R0-02 §11 Q2-sec**: HMAC of API key OR `X-Juniper-Role: adapter` header skip.
- **Safety-first**: HMAC approach (§4.2 item 20). Keeps the cascor handler uniform (no branch).
- **Tiebreaker**: branches in security-critical handler paths are attractive targets for future bugs. A single uniform path is safer.

### 12.5 `ws_security_enabled` vs `disable_ws_auth` — R0-02 §9.4 open question

- **R0-02 §9.4**: proposes `ws_security_enabled=True` (positive sense) but notes the rename cost.
- **Safety-first**: positive sense accepted (§4.2 item 15). Default True. Rename cost is worth it; negative-sense flags are classic footguns.
- **Tiebreaker**: a prod config accidentally containing `disable_ws_auth=True` is one typo away from disaster. A prod config with `ws_security_enabled=true` is the fail-safe state.

### 12.6 Phase B feature flag — R0-01 implicit no-flag, safety-first adds one

- **R0-01 §4**: Phase B ships without a feature flag (read-only migration, considered safe enough).
- **Safety-first**: Phase B ships behind `enable_ws_bridge=False` (§5.2).
- **Tiebreaker**: R0-06 RISK-02 is "Medium / High" — Phase B wiring is hard to debug. A flag lets us roll back without a code change. The cost is a single env var and a canary cohort week; the benefit is a 5-minute MTTR instead of a 30+ minute rollback.

### 12.7 Phase B-pre split — R0-06 says split a/b, R0-02 says bundle

- **R0-06 §13.1**: split into B-pre-a (max_size, ships with Phase B) and B-pre-b (auth, ships before Phase D).
- **R0-02**: treats Phase B-pre as one bundle.
- **Safety-first**: R0-06 split accepted (§4.1, §4.2). Allows Phase B to proceed sooner without compressing the auth work.
- **Tiebreaker**: smaller PRs are easier to review and roll back.

### 12.8 `command_response` seq field — R0-03 says no, implicit-all says yes

- **R0-03 §11.3**: command_response has no seq (personal RPC).
- **Arch doc §6.5 implicit reading**: all outbound messages have seq.
- **Safety-first**: R0-03's carve-out accepted. Command responses are personal and replay is confusing if applied to them.
- **Tiebreaker**: replaying a command_response for a command the client didn't issue is a user confusion bug. No safety benefit to bundling them.

---

## 13. Disagreements with R0 inputs

Places where the safety-first proposal takes a different stance than the Round 0 input.

### 13.1 R0-03: replay buffer default is too large

- **R0-03 §3.1**: default `maxlen=1024`.
- **Safety-first**: default 256 (§3.2). Rationale in §12.1.

### 13.2 R0-01: Phase B should have a feature flag

- **R0-01 §4**: no flag on the read path.
- **Safety-first**: `enable_ws_bridge=False` default. Rationale in §12.6.

### 13.3 R0-06: Phase A-server staging soak is 24 hours, insufficient

- **R0-06 §7.1**: 24h staging standard, 48-72h for Phase B.
- **Safety-first**: 72h for Phase A-server too (§3.4). Seq monotonicity bugs are latent and need sustained traffic to surface.

### 13.4 R0-02: adapter auth is an open question

- **R0-02 §11 Q2-sec**: undecided.
- **Safety-first**: decide in-plan: HMAC first-frame (§4.2 item 20). Rationale in §12.4.

### 13.5 R0-06: Phase C flip criteria are guidance, should be hard gates

- **R0-06 §3.4**: "≥1 week of data, user-research signal optional."
- **Safety-first**: 6 enumerated hard gates (§6.1). Must-have: ≥7 days production data, p99 delta ≥50 ms, zero orphaned commands, zero correlation-map leaks, canary ≥7 days. User-research is optional.

### 13.6 R0-05: latency tests in CI are recording-only

- **R0-05 §8**: recording only, not assert.
- **Safety-first**: agrees on recording vs asserting, but adds: the recording is a required gate. If the latency-recording test **does not run or does not upload an artifact**, Phase B does not merge. Empty histograms are fine; missing histograms are not.

### 13.7 R0-06: abandon criteria are listed but not tested

- **R0-06 §12.3**: 5 abandon triggers, no test coverage.
- **Safety-first**: the "kill switch MTTR ≤5 min" abandon trigger gets a CI test that times the flip during the canary pass. If the flip exceeds 5 minutes in staging, the phase does not ship (the whole plan depends on the kill switch working fast).

### 13.8 R0-01: rAF coalescing scaffolded-but-disabled

- **R0-01 §3.3.3**: safety-first strongly agrees, amplifies the enable criteria (§5.5).

### 13.9 R0-03: Phase A-server does not include backpressure full fix (pump task)

- **R0-03 §7.2**: full backpressure is Phase E.
- **Safety-first**: agrees. The quick-fix 0.5 s timeout is enough for Phase A-server. Full pump task is Phase E.

### 13.10 R0-02: per-origin handshake cooldown punishes NAT

- **R0-02 §4.8**: 10 rejections in 60 s → 5-min block. Punishes shared NAT.
- **Safety-first**: accept, BUT add: the cooldown list is cleared on canopy restart. Worst-case, a user can force-restart canopy to unblock themselves. This is not a kill switch per se, just a documented escape hatch.

### 13.11 R0-06: CODEOWNERS rule is "operational guard"

- **R0-06 §13.7**: CODEOWNERS as a recommendation.
- **Safety-first**: CODEOWNERS is a **hard merge gate**. No optional language. Any PR touching websocket/*.py or normalize_metric requires explicit project-lead approval.

---

## 14. Self-audit log

### 14.1 Passes performed

1. Read all 6 R0 files (R0-01 through R0-06) in chunks due to size limits.
2. Extracted key safety-relevant recommendations from each, mapping to the 8 safety principles.
3. Drafted §1-§13 in one pass.
4. Re-read the draft looking for: missing observability, missing kill switches, defaults too aggressive, rollback not addressed, abandon triggers vague.
5. Applied corrections via Edit (see §14.4).

### 14.2 Coverage check

All 16 RISK-NN items mapped in §11: yes.
All 10 phases (A-server, A, B-pre-a, B-pre-b, B, C, D, E, F, G, H, I) have: observability (§2), kill switches (§8), disaster recovery (§9), acceptance gates (§§3-7): yes.
All 8 safety principles from §1.2 are applied to every phase: yes.
Every M-SEC-01..11 from R0-02 is covered: yes (§4).
Every GAP-WS-NN mentioned in the source doc has a phase assignment: yes (inherited from R0-06 §3 mapping).

### 14.3 Issues found during self-audit

**Issue 1**: The initial draft did not mention Phase A (SDK) explicitly in the kill-switch matrix. Added row "Downgrade `juniper-cascor-client` pin" (§8).

**Issue 2**: `canopy_ws_backend_relay_latency_ms` was mentioned in §2.2 but not referenced elsewhere. Confirmed it is a new addition from this proposal (not in R0); kept it because the cascor→canopy-backend hop is otherwise invisible in R0-01's browser-side instrumentation.

**Issue 3**: The initial draft's §5.6 Phase B acceptance gate had AC-21 through AC-28 but AC-29 (monotonic seq in store) was a late addition. Verified AC-29 is cheap (a `dash_duo` assertion), added it properly.

**Issue 4**: §9.4 disaster recovery for Phase B-pre-b was initially lacking. Added the "kill switch is broken" scenario because it's the worst case and deserves explicit acknowledgement.

**Issue 5**: The `WSSeqCurrentStalled` alert was mentioned only in §2.4 but not tied to a RISK. Added to RISK-14 (§11).

**Issue 6**: Initial §12 disagreement list had 5 items. Audit found 3 more (Phase B flag, Phase B-pre split, command_response seq). Extended.

**Issue 7**: The `JUNIPER_WS_ALLOWED_ORIGINS=*` explicit non-switch in §4.3 was not initially flagged. Added it because the "panic-edit" scenario is exactly the failure mode a safety-first plan should pre-empt.

**Issue 8**: §10.6 (metrics-presence test) was implicit in §2 but not called out as its own test requirement. Added explicitly.

**Issue 9**: Phase A (SDK) did not have its own §3/§4/§5 section because it's purely additive and doesn't ship server-side behavior. Acknowledged inline in §3 and §8; did not create a separate section because the SDK has no runtime kill switch (consumers choose versions).

**Issue 10**: R0-05 §14.10 asks about a contract-test lane. Initial draft did not address. Decided (implicit in §10): yes, `contract` is a marker layered with `fast`, runs on every PR. Added to §10.5.

**Issue 11**: The TTF-targets in R0-06 are 5-10 minutes. Safety-first requires ≤5 for most kill switches. Adjusted the kill-switch matrix (§8) where R0-06 had 10 minutes.

**Issue 12**: Initial §10.3 (load tests) was inherited from R0-05 as "optional." Safety-first elevates to blocking for Phase A-server.

**Issue 13**: The ring-bound-at-handler principle from R0-01 was strong but not enforced via a test. Added AST lint requirement (§5.4 item 2).

**Issue 14**: §6.4 bounded correlation map — the size limit of 256 was chosen by analogy with R0-03's replay buffer default. Noted but not prescriptive; operators can tune.

**Issue 15**: Initial §2.4 alert list did not distinguish page vs ticket. Added severity column.

### 14.4 Edits applied during self-audit

All issues 1-15 above were corrected in the body of the document via Edit calls where they affected already-written sections, or written directly into the draft where they were adding new content. No external file changes.

### 14.5 Known uncertainties

- **CI runtime budget**: the safety-first stance adds ~10-15% CI runtime (metrics-presence test, kill-switch flip tests, chaos tests in nightly). Not measured; assumed tolerable given the nightly lane absorbs most of the increase.
- **Phase A-server 72h soak**: R0-03 implied ~24h would catch bugs. I chose 72h without hard evidence. If staging capacity is constrained, this may be reduced; document the trade-off.
- **`ws_replay_buffer_size=256` default**: disagrees with R0-03 explicitly. If the Round 2 reconciliation prefers 1024, the argument is in §3.2 and §12.1. Flag for reconsideration.
- **CODEOWNERS as hard gate**: requires a GitHub Teams / org setup that may not exist in the current Juniper repos. If unavailable, fall back to a pre-commit hook that scans PR diffs and a documented manual review rule.

### 14.6 Items explicitly not covered

- **REST path deletion**: out of scope. Never in this migration. Separate plan if ever proposed.
- **Multi-tenant replay isolation**: out of scope per Q1 resolution (single-tenant assumed).
- **WebAssembly Plotly**: out of scope per R0-01 §8.4.
- **Service worker / offline support**: out of scope.
- **OAuth / OIDC integration**: out of scope per R0-02 §5.4.
- **mTLS canopy↔cascor**: out of scope per R0-02 §5.4.
- **Shadow traffic**: explicitly rejected per R0-06 §7.3.
- **User research study**: optional per R0-06; skipped by default in this plan.

### 14.7 Self-confidence assessment

- **High confidence**: kill switch matrix, phased acceptance gates, observability requirements, risk register reconciliation. These are direct applications of the 8 principles to R0 inputs.
- **Medium confidence**: replay buffer default of 256 (disagrees with R0-03), Phase B feature flag addition (disagrees with implicit R0-01), Phase A-server 72h soak (disagrees with R0-06).
- **Lower confidence**: load tests elevated to blocking gates (R0-05 §10.4 was "optional"). This may add CI overhead and slow the Phase A-server timeline. Flag for Round 2 reconsideration if it proves impractical.

### 14.8 Final line count target check

Target: 1000-1700 lines. Current draft is within range.

### 14.9 Scope discipline

- ✓ Refracted R0 inputs through safety lens; did not re-design the transport or envelopes.
- ✓ Inherited R0-01 browser bridge, R0-02 security, R0-03 cascor backend, R0-04 SDK, R0-05 tests, R0-06 phasing. Amplifications, not reinventions.
- ✓ Did not design Plotly rendering, clientside_callback wiring, or broadcaster internals beyond what R0 proposed.
- ✓ Did not touch any other file. This is R1-02 output only.

---

**End of R1-02 proposal.**
