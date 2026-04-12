# Round 1 Proposal R1-01: Critical-Path / Minimum-Viable WebSocket Migration

**Angle**: Minimum scope to eliminate the P0 polling waste safely
**Author**: Round 1 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 1 consolidation — input to Round 2
**Inputs consolidated**: R0-01, R0-02, R0-03, R0-04, R0-05, R0-06
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope and goal

### 1.1 The P0 outcome

The single outcome this proposal delivers: **eliminate the ~3 MB/s `/api/metrics/history` polling waste** described in the source doc §1.1 and R0-06 §2 (row "§1.1, §1.2, §1.3 | Motivation (the 3 MB/s REST polling bomb)"). Everything else the 6 R0 proposals describe is out of scope for v1.

This is tracked as **GAP-WS-16 (P0)** in the source doc. Its fix is a two-step physical chain:

1. Cascor must emit per-message sequence numbers and advertise a `server_instance_id` so the browser can subscribe losslessly (**Phase A-server**, R0-03 §7.1).
2. The canopy browser must actually drain the already-existing `/ws/training` push into a Dash store, render it via `Plotly.extendTraces`, and gate the polling handler on a WebSocket-health flag (**Phase B**, R0-01 §3.2-§3.4).

Before step 2 can ship to production, the browser WebSocket surface must not be exploitable via CSWSH. That is **Phase B-pre** (R0-02). The minimum-viable subset of Phase B-pre is the smallest set of M-SEC controls that makes shipping step 2 defensible.

### 1.2 What "minimum-viable" means here

Minimum-viable = **the smallest coherent set of changes that, once merged to main and deployed, reduces `/api/metrics/history` bandwidth by >90% in staging without introducing a new exploitable attack surface and without losing correctness on reconnect**.

This proposal explicitly:

- Ships a working read-side WebSocket pipeline (cascor → canopy → browser).
- Ships the security gate that the source doc and R0-02 treat as a *hard* prerequisite for exposing the new browser-side attack surface.
- Ships enough test coverage to catch the specific regressions that would undo the P0 win.
- Ships the observability to prove the P0 win happened.

It explicitly does NOT:

- Ship set_params over WebSocket (Phase C, R0-04) — deferred, see §3.1.
- Ship control buttons over WebSocket (Phase D) — deferred, see §3.2.
- Ship backpressure, heartbeat, metric format audit, asset cache busting as standalone phases (E/F/H/I) — deferred, see §3.3.
- Ship the full reconnect+replay hardening beyond the minimum required for no-data-loss on a short blip (see §3.4).
- Ship the full audit logger, per-command rate limit, per-command timeouts, or adapter-inbound-validation beyond what the CSWSH gate requires (see §3.5).

### 1.3 Why this carveout is safe

Three observations from cross-reading the 6 R0 proposals:

1. **R0-06 §3.2** explicitly distinguishes "Phase B-pre is a Phase D hard prerequisite" (CSWSH guards for `/ws/control`) from "Phase B-pre max_size guards (M-SEC-03) are a Phase B hard prerequisite." This means the minimum-viable Phase B-pre is a strict subset of the full R0-02 Phase B-pre. We can defer the CSWSH/CSRF/audit-logger subset until Phase D lands.
2. **R0-01 §3.4** shows that the `/api/metrics/history` elimination works cleanly with the already-existing (broken) `/ws/training` path plus a `ws-connection-status` store and a `no_update` return in the REST polling handler. It does not require `set_params`, control buttons, or topology chunking.
3. **R0-03 §7.1** carves out "Phase A-server" as a 2-day commit chain that delivers `seq`, `server_instance_id`, replay buffer, `resume` handler, `snapshot_seq`, and the `_send_json` 0.5 s quick-fix. That chain stands alone and is exactly what Phase B needs on the server side.

The composition of these three carveouts *is* the minimum-viable set.

### 1.4 Anchor to the source doc identifiers

| Source-doc anchor | In scope (minimum-viable)? |
|---|---|
| §1.1 motivation (3 MB/s polling) | **yes — the P0 goal** |
| §1.3 Option B drain caveat | **yes — pattern for Phase B** |
| §2.9.2 M-SEC-01 (canopy Origin) | partial — see §2.2 |
| §2.9.2 M-SEC-01b (cascor Origin parity) | partial — see §2.2 |
| §2.9.2 M-SEC-02 (cookie+CSRF) | **deferred — see §3.5** |
| §2.9.2 M-SEC-03 (max_size) | **yes — hard prereq for Phase B per R0-06 §3.2** |
| §2.9.2 M-SEC-04 (per-IP cap) | partial — see §2.2 |
| §2.9.2 M-SEC-05 (rate limit) | **deferred — see §3.5** |
| §5.6 latency instrumentation (GAP-WS-24) | **yes, minimal — see §2.3** |
| §6.3 polling toggle pattern | **yes — core of P0 fix** |
| §6.4 disconnection taxonomy | **yes** |
| §6.5 reconnect+replay protocol | **yes, minimal — see §2.1** |
| §6.5.2 snapshot↔live atomicity | **yes — avoids data loss** |
| §7 GAP-WS-01 SDK set_params | **deferred — see §3.1** |
| §7 GAP-WS-02/03/04/05 browser bridge plumbing | **yes — Phase B** |
| §7 GAP-WS-13 replay buffer | **yes — Phase A-server** |
| §7 GAP-WS-14 extendTraces | **yes — Phase B** |
| §7 GAP-WS-15 rAF coalescing | **deferred as scaffold-only** — R0-01 §3.3.3 self-deferred |
| §7 GAP-WS-16 REST polling | **yes — the P0 goal** |
| §7 GAP-WS-18 topology chunking | **deferred — see §3.6** |
| §7 GAP-WS-19 close_all lock | already fixed on main (R0-03 §11) |
| §7 GAP-WS-21 state throttle coalescer | **yes — Phase A-server** (folded in by R0-03 §7.1) |
| §7 GAP-WS-22 protocol error responses | **yes, minimal** — see §2.1 |
| §7 GAP-WS-24 latency instrumentation | **yes, minimal** — see §2.3 |
| §7 GAP-WS-25 polling toggle | **yes — core of P0 fix** |
| §7 GAP-WS-26 connection indicator | **yes, minimal** — see §2.3 |
| §7 GAP-WS-27 per-IP cap | **partial — see §2.2** |
| §7 GAP-WS-29 broadcast_from_thread exception | **yes — Phase A-server** |
| §7 GAP-WS-30 reconnect jitter | **yes — Phase B folds from Phase F** |
| §7 GAP-WS-31 uncapped reconnect | **deferred** — see §3.4 |
| §7 GAP-WS-32 per-command timeouts/correlation | **deferred** — see §3.1 |
| §7 GAP-WS-33 demo mode failure visibility | **yes, minimal** |
| Phase A (SDK set_params) | **deferred — see §3.1** |
| Phase A-server (cascor prereqs) | **yes** |
| Phase B-pre (security gate) | **yes, minimum subset** |
| Phase B (browser bridge) | **yes — minimum subset** |
| Phase C (set_params adapter) | **deferred — see §3.1** |
| Phase D (control buttons) | **deferred — see §3.2** |
| Phase E (backpressure full fix) | **deferred, except quick-fix** |
| Phase F (heartbeat + jitter) | **folded minimally into Phase B** |
| Phase G (cascor set_params integration test) | **deferred** — see §3.1 |
| Phase H (normalize_metric audit) | **deferred, but regression test folded** |
| Phase I (asset cache busting) | **yes — bundled with Phase B** |

The rest of this document is organized as R0-0x → in-scope extraction, then a deferrals section with justifications.

---

## 2. What's IN scope (the minimum-viable set)

### 2.1 Phase A-server minimum (from R0-03)

**Target**: deliver a cascor server that emits `seq` on every broadcast envelope, advertises `server_instance_id`, supports a lossless 1024-event replay buffer with a `resume` handler, exposes `snapshot_seq` from the REST status endpoint, and will not stall fan-out on a single slow client. This is the exact carveout R0-03 §7.1 labels "Phase A-server."

**Scope clarification**: minimum-viable does **not** change how the canopy adapter talks to cascor. The adapter continues to use the existing `X-API-Key` HTTP header pattern on its long-lived WebSocket client to cascor (R0-02 §3.6). The new surface is **browser → canopy** on `/ws/training`. The new cascor work described below exists because canopy's adapter relays cascor's envelopes verbatim to canopy's own `/ws/training`, and the browser-facing Phase B work requires `seq` + `server_instance_id` + `resume` handling to be present end-to-end.

The minimum-viable commit chain is R0-03's 10-commit list distilled to the ones that directly serve the P0 goal. Every commit below is traceable to a R0-03 §7.1 commit number:

| Minimum-viable commit | R0-03 §7.1 origin | Why included |
|---|---|---|
| **A-srv-1** `messages.py` adds optional `seq` field on every builder | commit 1 | Enables step 2 |
| **A-srv-2** `WebSocketManager` gains `_next_seq`, `_seq_lock`, `_replay_buffer` (deque maxlen=1024), `server_instance_id`, `server_start_time`, `_assign_seq_and_append()` helper; `connect()` advertises the ID fields in `connection_established` | commit 2 | Enables resume and restart detection |
| **A-srv-3** `_send_json` wraps in `asyncio.wait_for(..., timeout=0.5)` (quick-fix GAP-WS-07) | commit 3 | Prevents a single browser tab from stalling broadcast for all clients — this is required for Phase B to scale beyond 1 connected dashboard |
| **A-srv-4** `replay_since(last_seq)` helper + `ReplayOutOfRange` exception | commit 4 | Needed by resume handler |
| **A-srv-5** `training_stream.py` two-phase registration (pending set → resume handler → promote) + `resume` / `resume_ok` / `resume_failed` flow (§6.5) | commit 5 | Lossless reconnect for short blips; correctness floor for Phase B |
| **A-srv-6** `/api/v1/training/status` returns `snapshot_seq` and `server_instance_id` (atomic read under `_seq_lock`) | commit 6 | Prevents the torn-snapshot bug on initial load (§6.5.2 atomicity) |
| **A-srv-7** `lifecycle/manager.py` 1 Hz state throttle → debounced coalescer with terminal-state bypass (GAP-WS-21) | commit 7 | The source doc flags this as a correctness bug that silently drops state transitions; fixing it is tiny and avoids a nasty Phase B regression where terminal states go missing |
| **A-srv-8** `broadcast_from_thread` attaches a done_callback for exception logging (GAP-WS-29) | commit 8 | 3-line change; prevents silent swallowing of exceptions that would hide Phase B regressions |
| **A-srv-9** `/ws/control` protocol error responses (GAP-WS-22) — at minimum the "unknown command → error response" + "non-JSON → close 1003" entries | commit 9 | Required so the minimum Phase B-pre error-handling contract is consistent |

**Commit 10 (docs/CHANGELOG) is included** but I am not bothering to number it separately because every PR that touches cascor runs it as part of the standard workflow.

**Effort estimate (R0-03 §7.1)**: 2 engineering days for the full 10-commit chain. I believe this is accurate because the commits are individually small and individually test-green.

**What Phase A-server does NOT include at minimum-viable**:

- Per-client pump task + bounded queue + policy matrix (R0-03 §5.2 full fix). **Deferred** — the 0.5 s quick fix is sufficient for Phase B's read-side traffic. See §3.3.
- `permessage-deflate` negotiation (GAP-WS-17). Deferred.
- Topology chunking (GAP-WS-18). Deferred. See §3.6.
- Full command_id correlation on `/ws/control` (GAP-WS-32). Deferred with Phase C/D.
- The `_VALID_COMMANDS` whitelist guard that R0-04 requires for `set_params`. Not needed — `set_params` is deferred to Phase C.

### 2.2 Phase B-pre minimum security gate (from R0-02 and R0-06)

R0-02 describes a comprehensive security hardening suite (M-SEC-01 through M-SEC-12, 1.5–2 day effort, 40+ test cases, dedicated audit logger). R0-06 §3.2 makes the critical observation that **some of these controls gate Phase B and others gate Phase D**, not all at once.

The minimum-viable Phase B-pre is the set that gates Phase B only. Phase D's additional requirements (CSWSH prevention for control commands, cookie+CSRF, audit logging) are explicitly deferred with Phase D itself. See §3.5.

#### 2.2.1 Required M-SEC controls for Phase B

From R0-06 §3.2 (which cites R0-02's own §9.2):

> "treat M-SEC-03 as a Phase B prerequisite (must land in the same wave as Phase B) and treat M-SEC-01/01b/02 as Phase D prerequisites. This matches the architecture doc's §9.2 spec exactly."

Applying that reading carefully:

**M-SEC-03 (per-frame size caps) — REQUIRED for Phase B**. Rationale: Phase B opens up new browser→canopy traffic on `/ws/training`. Without a `max_size` guard, a malformed or malicious client can send a 100 MB frame and exhaust memory. R0-06 RISK-16 also cites this as a DoS vector. The implementation is trivial — add `max_size=` to every `receive_*()` call — and the test is trivial (`test_oversized_frame_rejected_with_1009`). This is non-negotiable.

**M-SEC-01 (canopy Origin allowlist) — REQUIRED for Phase B**, minimal form. Rationale: while CSWSH's *highest* severity is on `/ws/control` (which is Phase D territory), **merely accepting cross-origin upgrades on `/ws/training` leaks live event data** — training state, topology, metrics — to any attacker page the user happens to visit. R0-02 §3.1 blast-radius item "Information exfiltration" applies to `/ws/training` too. Shipping Phase B without Origin validation on `/ws/training` means any cross-origin attacker page can tail the user's live training metrics.

The minimum Origin allowlist implementation per R0-02 §4.1:
  - Check `ws.headers.get("origin")` against `Settings.allowed_origins` before `ws.accept()`.
  - Default allowlist: `["http://localhost:8050", "http://127.0.0.1:8050", "https://localhost:8050", "https://127.0.0.1:8050"]`.
  - Env var override: `JUNIPER_WS_ALLOWED_ORIGINS`.
  - Rejection: pre-accept `HTTPException(403)` or `ws.close(code=1008)` — verify at implementation time per R0-02 §4.1.
  - Case-insensitive host compare; port significant; null origin rejected; empty allowlist = reject-all (fail-closed).
  - No CSP headers, no SameSite cookie interactions — we are only gating the upgrade header.

**M-SEC-01b (cascor Origin parity)** — **REQUIRED for Phase B**, same minimal form. Rationale: the canopy adapter continues to talk to cascor via `X-API-Key`, but the browser-direct demo/direct-connect topology exists and R0-02 §3.7 flags it. Shipping M-SEC-01 without M-SEC-01b creates an exfiltration path through cascor directly. The cost of adding the same `validate_origin` helper to cascor's `/ws/training` handler is ~30 LOC. R0-02 §6.1 extracts a shared helper; since cascor already has one at `worker_stream.py:41-44`, this is literally "factor out and import."

**M-SEC-04 minimal form (per-IP connection cap)** — **REQUIRED for Phase B**, but ONLY the per-IP cap, NOT the auth-timeout subpart. Rationale: Phase B opens up browser connections that can be flood-attacked. A single attacker opening 10,000 WebSockets to `/ws/training` saturates the global 50-conn cap. Per-IP defaults (5/IP, configurable) solve this with minimal code per R0-02 §4.5 Control 1 + R0-06 RISK-07. The auth-timeout subpart is part of M-SEC-02 CSRF flow, which is deferred. The per-IP cap itself is independent and cheap.

**Everything else in R0-02 is deferred to the Phase D wave** — see §3.5 below for the complete list with rationale.

#### 2.2.2 Concrete implementation steps (Phase B-pre minimum)

Ported from R0-02 §6 and filtered:

| Step ID | File | Change |
|---|---|---|
| **MVS-SEC-01** | `juniper-cascor/src/api/websocket/origin.py` (new) | Extract `validate_origin(ws, allowlist) -> bool` helper from `worker_stream.py:41-44` pattern |
| **MVS-SEC-02** | `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` (new) | Unit tests: exact match, case-insensitive host, trailing-slash strip, null origin, port mismatch, scheme mismatch, wildcard rejection |
| **MVS-SEC-03** | `juniper-cascor/src/api/app.py` or equivalent | Wire `validate_origin` into `training_stream_handler` at the upgrade-accept point |
| **MVS-SEC-04** | `juniper-cascor/src/config.py` | `Settings.ws_allowed_origins: list[str]`, default `[]` = reject-all (fail-closed), env var `JUNIPER_WS_ALLOWED_ORIGINS` |
| **MVS-SEC-05** | `juniper-canopy/src/backend/ws_security.py` (new) | `validate_origin` helper (copy from cascor module; they are not cross-repo deps) |
| **MVS-SEC-06** | `juniper-canopy/src/main.py` (~line 355 per R0-02 §4.1) | Wire `validate_origin` into `/ws/training` route handler |
| **MVS-SEC-07** | `juniper-canopy/src/config.py` | `Settings.allowed_origins` with concrete localhost/127.0.0.1 × http/https defaults (R0-02 §9.3 recommended default) |
| **MVS-SEC-08** | `juniper-cascor/src/api/websocket/manager.py` | Add `_per_ip_counts: Dict[str, int]` under `_lock`, increment in `connect()`, decrement in `disconnect()` finally-block. R0-02 §4.5 Control 1 pattern |
| **MVS-SEC-09** | `juniper-cascor/src/config.py` | `Settings.ws_max_connections_per_ip: int = 5` |
| **MVS-SEC-10** | `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py` (new) | Test: 6th connection from same IP rejected with 1013; connect/disconnect race doesn't leak counters |
| **MVS-SEC-11** | `juniper-cascor/src/api/websocket/training_stream.py` | Add `max_size` to `receive_*()` call(s) — cap at 4 KB (ping/pong only) |
| **MVS-SEC-12** | `juniper-canopy/src/main.py` | Add `max_size=4096` to `/ws/training` inbound receive |
| **MVS-SEC-13** | `juniper-cascor/src/tests/unit/api/test_websocket_size_limits.py` | Test: 65 KB inbound frame on `/ws/training` → close 1009 |
| **MVS-SEC-14** | `juniper-canopy/src/tests/unit/test_ws_security_origin.py` (new) | Test: Origin rejection matrix on canopy `/ws/training` |

**NOT in the minimum-viable Phase B-pre**:

- M-SEC-02 cookie+CSRF flow (deferred to Phase D wave — see §3.5)
- SessionMiddleware wiring in canopy (deferred)
- `/api/csrf` REST endpoint (deferred)
- Dash template CSRF token injection (deferred)
- M-SEC-05 per-command rate limit (deferred — `/ws/control` not in Phase B)
- M-SEC-06 opaque close reasons (deferred — only matters when M-SEC-02 is on)
- M-SEC-07 audit log + logging scrub allowlist (deferred — applies to control plane)
- M-SEC-10 idle timeout (deferred — nice-to-have)
- M-SEC-11 adapter inbound validation (deferred — correctness, not exploit)
- JSON depth guard (deferred — marginal threat)
- Per-frame `SetParamsRequest` Pydantic model (deferred with set_params itself)
- Per-origin handshake cooldown (deferred)
- Prom counters for auth rejections (deferred — only audit logger emits them)

The minimum-viable Phase B-pre is roughly **0.5 engineering days** (14 steps, mostly mechanical, covered by 4 test files), compared to R0-02's full 1.5-2 day estimate.

**Effort saved by the deferrals: ~1 engineering day**, but at the cost of reopening CSWSH remediation when Phase D lands. This is explicitly the trade.

### 2.3 Phase B minimum frontend wiring (from R0-01)

**Target**: browser drains the cascor WebSocket into the Dash store, renders chart updates via `Plotly.extendTraces`, and stops polling `/api/metrics/history` when the WebSocket is healthy.

R0-01 §3 is an 842-line menu. The minimum-viable subset is the parts that directly serve the P0 goal.

#### 2.3.1 Required JS / Python changes

| Step ID | File | Change | R0-01 anchor |
|---|---|---|---|
| **MVS-FE-01** | `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` (new, ~200 LOC) | JS ring-buffer + `window._juniperWsDrain` namespace per R0-01 §3.2.1 skeleton. Five `on(type, ...)` handlers for `metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`. **Enforce ring bound in the handler, not the drain callback** (R0-01 §3.2.5 / RISK-12). | §3.2.1 |
| **MVS-FE-02** | `juniper-canopy/src/frontend/assets/websocket_client.js` (existing) | Clean up in place: add `onStatus()` enrichment (connected/reason/reconnectAttempt/ts), add jitter to reconnect backoff (GAP-WS-30, 3-line change), add `server_instance_id` capture from `connection_established`, add `seq` tracking (monotonic check + warn), read `last_seq` + `server_instance_id` and emit `resume` frame as first frame on reconnect with graceful-degrade if `resume_failed` (falls back to REST snapshot). **Do not delete**. | §3.5.1 |
| **MVS-FE-03** | `juniper-canopy/src/frontend/dashboard_manager.py` | **Delete** the parallel raw-WebSocket clientside callback at ~`1490-1526` (GAP-WS-03). Leave a placeholder comment citing this proposal | §3.5.2 |
| **MVS-FE-04** | `juniper-canopy/src/frontend/dashboard_manager.py` | Add `dcc.Store(id='ws-metrics-buffer')` drain callback that reads `window._juniperWsDrain.drainMetrics()` and writes merged-and-capped `{events, gen, last_drain_ms}` on `fast-update-interval` tick (R0-01 §3.2.2 code block). Rewrite the existing broken init callback | §3.2.2 |
| **MVS-FE-05** | `juniper-canopy/src/frontend/dashboard_manager.py` | Update the existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks to call `window._juniperWsDrain.drainTopology()` / `drainState()` instead of reading `window._juniper_ws_*` globals. Delete references to the old globals | §3.2.2 |
| **MVS-FE-06** | `juniper-canopy/src/frontend/dashboard_manager.py` | Add `dcc.Store(id='ws-connection-status')` with drain callback (R0-01 §3.4.1 code block) that peeks `window._juniperWsDrain.peekStatus()` and emits only on change | §3.4.1 |
| **MVS-FE-07** | `juniper-canopy/src/frontend/dashboard_manager.py` | Refactor `_update_metrics_store_handler` at `~2388-2421` to: (a) read `ws-connection-status` via State; (b) return `no_update` when connected; (c) slow fallback to 1 Hz via `n % 10 == 0` check; (d) preserve initial-load REST GET path | §3.4.2 |
| **MVS-FE-08** | `juniper-canopy/src/frontend/components/metrics_panel.py` | Rewrite `MetricsPanel.update_metrics_display()` at `~648-670` as a clientside_callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"` to the initial figure layout. Add hidden `metrics-panel-figure-signal` dummy Store | §3.3.2 |
| **MVS-FE-09** | `juniper-canopy/src/frontend/components/candidate_metrics_panel.py` | Same extendTraces migration, `maxPoints=5000` | §3.3.2 |
| **MVS-FE-10** | `juniper-canopy/src/frontend/dashboard_manager.py` | Apply the same polling-toggle pattern to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. **Keep the REST paths** — they are the kill switch and the fallback | §3.4.3 |
| **MVS-FE-11** | `juniper-canopy/src/frontend/components/network_visualizer.py` or equivalent | Wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape graph update callback. **Do NOT use extendTraces** (cytoscape is not Plotly). Keep the REST poll as fallback | §3.5 step 16 — in minimum form |
| **MVS-FE-12** | `juniper-canopy/src/frontend/dashboard_manager.py` | Add connection indicator badge (GAP-WS-26). `html.Div` with clientside_callback reading `ws-connection-status` → CSS class toggling. States: connected/reconnecting/offline/demo | §4 step 17 |
| **MVS-FE-13** | `juniper-canopy/src/frontend/demo_mode.py` | Demo mode sets `ws-connection-status` to `{connected: true, mode: "demo"}` so the polling toggle returns `no_update` and the badge shows "demo" (GAP-WS-33, RISK-08) | §4 step 18 |
| **MVS-FE-14** | `juniper-canopy/src/frontend/assets/ws_latency.js` (new, ~50 LOC) | Minimal browser latency histogram: records `received_at_ms - emitted_at_monotonic` per message, POSTs to `/api/ws_latency` every 60 s. Required to **prove the P0 win in production** (GAP-WS-24, R0-06 §6.4) | §4 step 19 |
| **MVS-FE-15** | `juniper-canopy/src/main.py` | Server-side `/api/ws_latency` POST endpoint that increments `canopy_ws_delivery_latency_ms_bucket` Prometheus histogram AND the new `canopy_rest_polling_bytes_per_sec` gauge (R0-06 §6.1) | §4 step 19 |
| **MVS-FE-16** | `juniper-canopy/src/frontend/assets/` | Phase I asset cache busting — bump `assets_folder_snapshot` or equivalent so the browser picks up the new `websocket_client.js` + `ws_dash_bridge.js` without a hard refresh (R0-06 §3.6 Phase I). **Mandatory per R0-06** before Phase B goes to production | — |

#### 2.3.2 Explicit R0-01 deviations (in-scope for minimum)

- **rAF coalescing (GAP-WS-15)**: R0-01 §3.3.3 self-deferred this ("Simplification: for Phase B, ship WITHOUT the rAF path"). I concur. The 100 ms drain interval produces ~10 Hz render rate, well under 60 Hz budget. Scaffold stays in `ws_dash_bridge.js` but is not wired. Revisit if §5.6 instrumentation shows jank.
- **Option B vs Option A**: R0-01 §3.2.3 argues Option B (Interval drain). I concur. Option A (`dash.set_props`) requires Dash 2.18+ and defeats coalescing.
- **Option C (`dash-extensions.WebSocket`) rejected**: R0-01 §3.2.4 rejects it. I concur.
- **Dual-format metrics test**: R0-01 §3.6 prescribes a Playwright wire test pinning `msg.data` to contain both nested and flat keys. I include this in §2.4.

#### 2.3.3 What's explicitly NOT in minimum Phase B frontend

- **Full reconnect backoff cap removal (GAP-WS-31)**: R0-01 §3.5.1 item 4 wants to lift the 10-attempt cap entirely. Minimum-viable **keeps the 10-attempt cap** — if connection fails >10 times, the REST polling fallback takes over anyway. The cap is a bug but fixing it has no bearing on the P0 goal. Deferred with Phase F. Add jitter ONLY.
- **Full bounded JS ring for replay**: R0-01 §3.5.1 item 7 wants a 256-entry FIFO with seq tracking for double-apply protection. Minimum-viable keeps the simpler ring per handler (MVS-FE-01); double-apply is handled by the server-side seq uniqueness (every event has a unique seq and the browser's per-chart renderer is idempotent to duplicate seqs already because `Plotly.extendTraces` appends, and duplicate seqs would just create a visual bump — not a correctness violation). If instrumentation shows it, add in v1.1.
- **Dead-helper cleanup in websocket_client.js** (R0-01 §3.5.1 item 8): keep `getBufferedMessages()` even if unused; deletion has no bearing on the P0 goal and risks breaking a test that reaches for it.

**Effort estimate**: R0-01 does not commit to a number but its 16-step plan plus file sizes suggests **~3 engineering days** for the full MVP frontend subset, which matches R0-06 §9.3 Phase B's 4-day estimate minus the Phase B-pre subset cost that we defer.

### 2.4 Phase B test coverage (from R0-05)

R0-05 is 1038 lines describing a full test pyramid across unit/integration/browser/security/latency lanes. The minimum-viable test set is the subset required to **catch the regressions that would undo the P0 win, catch the security holes in the minimum Phase B-pre, and prove the P0 metric target in CI**.

#### 2.4.1 Required tests

| Test ID | File | Purpose | R0-05 anchor |
|---|---|---|---|
| **MVS-TEST-01** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_manager.py` extension | `test_seq_monotonically_increases_per_connection`, `test_seq_increments_across_all_message_types`, `test_seq_is_assigned_on_loop_thread`, `test_seq_lock_does_not_block_broadcast_iteration` | §4.1 Phase B |
| **MVS-TEST-02** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_replay_buffer.py` (new) | `test_replay_buffer_bounded_1024`, `test_resume_replays_events_after_last_seq`, `test_resume_failed_out_of_range`, `test_resume_failed_server_restarted`, `test_connection_established_advertises_instance_id`, `test_snapshot_seq_atomic_with_state_read` | §4.1 Phase B |
| **MVS-TEST-03** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_manager.py` | `test_slow_client_send_timeout_does_not_block_fanout` — validates the 0.5 s quick-fix (A-srv-3) | §4.1 Phase E subset |
| **MVS-TEST-04** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_size_limits.py` (new) | `test_per_frame_size_limit_1009` for `/ws/training` — validates MVS-SEC-11 | §4.1 Phase B-pre |
| **MVS-TEST-05** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py` (new) | `test_per_ip_connection_cap`, `test_per_ip_counter_decrements_on_disconnect`, `test_per_ip_counter_decrements_on_exception` — validates MVS-SEC-08 and the race regression | §4.1 Phase B-pre |
| **MVS-TEST-06** (cascor unit) | `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` (new) | `test_origin_allowlist_accepts_configured_origin`, `test_origin_allowlist_rejects_third_party`, `test_origin_allowlist_rejects_missing_origin`, `test_origin_header_case_insensitive_host` — validates MVS-SEC-01 through MVS-SEC-04 | §4.1 Phase B-pre |
| **MVS-TEST-07** (cascor unit) | `juniper-cascor/src/tests/unit/lifecycle/test_lifecycle_manager.py` extension | `test_state_coalescer_flushes_terminal_transitions` — validates A-srv-7 (GAP-WS-21 fix) | — (folded from R0-03 §7.1) |
| **MVS-TEST-08** (canopy unit) | `juniper-canopy/src/tests/unit/test_ws_dash_bridge.py` (new) | `test_update_metrics_store_handler_returns_no_update_when_ws_connected`, `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`, `test_ws_connection_status_store_reflects_cascorWS_status`, `test_ws_metrics_buffer_drain_is_bounded` | §4.3 Phase B |
| **MVS-TEST-09** (canopy unit) | `juniper-canopy/src/tests/unit/test_ws_security_origin.py` (new) | Origin rejection matrix on canopy `/ws/training` — validates MVS-SEC-06 | R0-02 §7.2 |
| **MVS-TEST-10** (integration) | `juniper-canopy/src/tests/integration/test_cascor_adapter_ws.py` (new) | `test_adapter_subscribes_to_metrics_and_forwards_to_normalizer`, `test_adapter_reconnects_after_fake_kills_connection`, `test_adapter_handles_resume_failed_by_fetching_snapshot`, `test_adapter_demo_mode_parity` (RISK-08) — uses `FakeCascorServerHarness` from §5.2 | R0-05 §5.2 |
| **MVS-TEST-11** (integration) | `juniper-canopy/src/tests/integration/test_ws_reconnect_replay.py` (new) | `test_reconnect_replays_10_missed_events`, `test_reconnect_with_stale_server_instance_id_triggers_snapshot`, `test_snapshot_seq_bridges_no_gap`, `test_older_cascor_without_resume_command_triggers_fallback` | R0-05 §5.3 |
| **MVS-TEST-12** (dash_duo) | `juniper-canopy/src/tests/e2e/dash_duo/test_browser_receives_metrics.py` (new) | `test_browser_receives_metrics_event`, `test_chart_updates_on_each_metrics_event`, `test_chart_does_not_poll_when_websocket_connected`, `test_chart_falls_back_to_polling_on_websocket_disconnect`, `test_demo_mode_metrics_parity`, `test_ws_metrics_buffer_store_is_ring_buffer_bounded`, `test_connection_indicator_badge_reflects_state` | R0-05 §6.1 Phase B |
| **MVS-TEST-13** (Playwright) | `juniper-canopy/src/tests/e2e/playwright/test_websocket_wire.py` (new) | `test_websocket_frames_have_seq_field`, `test_resume_protocol_replays_missed_events`, `test_seq_reset_on_cascor_restart`, `test_plotly_extendTraces_used_not_full_figure_replace` | R0-05 §6.2 Phase B |
| **MVS-TEST-14** (Playwright metric-format pin) | `juniper-canopy/src/tests/e2e/playwright/test_metrics_dual_format.py` (new) | R0-01 §3.6 wire test: assert `ws-metrics-buffer.events[-1]` contains BOTH flat and nested metric keys — **Phase H regression gate, folded into Phase B so Phase H can be deferred safely** | R0-01 §3.6, R0-05 §4.3 |
| **MVS-TEST-15** (Playwright bandwidth proof) | `juniper-canopy/src/tests/e2e/playwright/test_polling_elimination.py` (new) | Measure `/api/metrics/history` request count over 60 s with WS connected → assert zero requests after initial load. This is the **direct proof of the P0 win**. | Not in R0-05; contribution of this proposal |

#### 2.4.2 Test coverage NOT included at minimum

- **Fuzz testing** (R0-05 §7.3): deferred — nice-to-have but not a P0 gate.
- **Frame budget assertions** (R0-05 §6.3): deferred — R0-05 itself flags these as flaky on CI and recommends "trace-only" fallback. The §5.6 histogram path (MVS-FE-14 + MVS-FE-15) IS the latency gate.
- **All Phase C/D/E/F/G/H tests**: deferred with those phases.
- **Full M-SEC-01 through M-SEC-07 security matrix**: we only have M-SEC-01/01b/03/04 in scope, so the tests are correspondingly narrower.
- **CSWSH Playwright probe** (R0-05 §7.9): the full Origin probe test is a nice-to-have that validates MVS-SEC-06. Include in the must-have list above as MVS-TEST-09.
- **User-research latency validation** (§5.7): deferred indefinitely.
- **Multi-browser matrix**: Chromium only.
- **Nightly latency trend check**: scaffold the CI lane but don't enforce thresholds.

#### 2.4.3 Test fixture requirements (from R0-05 §3)

The minimum-viable plan **requires** the following extensions to the existing fakes, and R0-05 §3.3 already identifies all of these:

- `FakeCascorTrainingStream` gains optional `with_seq=True` mode that emits `seq` + `connection_established` with a synthetic `server_instance_id`.
- `FakeCascorServerHarness` (a new thin FastAPI wrapper) lives in `juniper-cascor-client/juniper_cascor_client/testing/server_harness.py`. This is required for Playwright and `dash_duo` tests to have a real TCP socket to connect to.
- `simulate_disconnect()` / `simulate_reconnect(last_seq)` helpers on the fake for MVS-TEST-11.

NOT required at minimum-viable:
- `on_command(command_name, handler)` correlation scaffolding (set_params-specific — deferred with Phase C).
- `enforce_api_key=True` mode (we're not testing auth header paths at minimum).

### 2.5 Phase B operational rollout (from R0-06)

R0-06 is a 923-line operational wrapper. The minimum-viable rollout applies the parts that directly gate Phase B shipping to production.

#### 2.5.1 Required operational deliverables

| Item | R0-06 anchor | Purpose |
|---|---|---|
| **Feature flag `Settings.disable_ws_bridge: bool = False`** | §5.2 | Kill switch for Phase B. When True, the polling toggle's `ws-connection-status` is forced to "disconnected" and the dashboard falls back to REST polling. 5-minute TTF |
| **Prometheus metric `canopy_rest_polling_bytes_per_sec`** | §6.1 | The proof-of-win metric. Target: >90% reduction after Phase B |
| **Prometheus metric `canopy_ws_delivery_latency_ms_bucket`** | §6.1 | Histogram fed by MVS-FE-14/15 |
| **Prometheus metric `canopy_ws_active_connections`** | §6.1 | Gauge; alert at 80% of cap |
| **Dashboard panel: "WebSocket health"** | §6.4 | Shows p50/p95/p99 per event type |
| **Staging deploy ≥ 48 hours before production** | §7.1 | Long enough to catch RISK-10 overnight browser memory leak |
| **Runbook: `juniper-canopy/notes/runbooks/ws-bridge-kill.md`** | §3.3 | How to flip `disable_ws_bridge=True` and restart |
| **Cross-repo merge order** | §8.1 | 1) cascor Phase A-server (steps 1-4). 2) cascor+canopy Phase B-pre MVS steps. 3) canopy Phase B frontend + instrumentation + cache busting. No SDK dependency = no PyPI waiting |

#### 2.5.2 NOT in minimum rollout

- Canary cohort (R0-06 §7.2) — not needed for read-side Phase B. Becomes relevant in Phase C/D.
- Shadow traffic — R0-06 §7.3 itself rejects it.
- User communication cadence — irrelevant for a read-side no-UX-change migration.
- The full risk-register mitigation map — only RISK-02, RISK-08, RISK-10, RISK-12, RISK-14, RISK-15 (partial), RISK-16 (partial) apply at minimum. See §7 below.
- Helm chart version discipline — applies but is a standing Juniper-wide rule, not Phase-B-specific.

---

## 3. What's explicitly DEFERRED and why

Each deferral cites the R0 file it comes from and explains why the minimum-viable scope is safe without it. Deferrals are **additive** — they can all be picked up in a v1.1 follow-up without re-architecting the minimum-viable scope.

### 3.1 Phase C set_params — DEFERRED (R0-04)

**What's deferred**: everything in R0-04 §4-§7: the new `CascorControlStream.set_params(params, timeout=1.0, request_id=...)` SDK method, the canopy adapter's hot/cold splitter in `apply_params()`, the `Settings.use_websocket_set_params` feature flag, the correlation-map pending-command table, GAP-WS-32 `command_id` echo on cascor's `/ws/control`, the `request_id`-aware error mapping, the fallback-to-REST-on-WS-error logic, and the Phase G cascor integration test (`test_set_params_via_websocket_happy_path`, etc.).

**Why it's safe to defer**: R0-04 §3 is the definitive argument — the source doc itself **relabels Phase C from P1 to P2** based on §5.3.1's ack-vs-effect latency analysis. Concretely:

1. The user-perceived "slider → chart responds" loop has ~7 stages; the REST-vs-WS transport hop is 1 of them.
2. The "next epoch" stage alone can exceed 100 ms, dwarfing the 2 ms vs 60 ms transport delta.
3. For most real workloads, `set_params` over WebSocket is **invisible** to the user versus REST PATCH.

Deferring Phase C preserves the existing working REST `/api/v1/training/params` path (which is already a first-class API per R0-04 §4.4) and simply means the canopy adapter continues to call `self._client.update_params(mapped)` for all parameter changes. Nothing breaks. The slider still works. The latency is what it is today — which nobody has complained about.

**What we lose**: the option to measure whether WebSocket `set_params` is actually faster, because the instrumentation for the A/B comparison lives in Phase C. But we also don't ship dead code awaiting a flag flip.

**Second-order deferrals driven by Phase C deferral**:

- **GAP-WS-01** (SDK `set_params`): deferred. SDK ships no new method. R0-04 §4.1 lands in v1.1.
- **GAP-WS-09** (canopy `set_params` integration test): deferred.
- **GAP-WS-32** (per-command timeouts + correlation): partially deferred — we do NOT echo `command_id` on cascor because we do not send commands. When Phase C lands, cascor adds the echo.
- **R0-02's `SetParamsRequest` Pydantic model** (R0-02 §4.4 Control 3): deferred — we have no `set_params` inbound path to validate in minimum scope.

**Where to pick this up**: in a **Round-2 minimum-viable +1 proposal** (see §8). Phase C is the natural second feature wave.

### 3.2 Phase D control buttons — DEFERRED (R0-06 §3.5, R0-02 §3.1)

**What's deferred**: routing browser `start`/`stop`/`pause`/`resume`/`reset` clicks through `/ws/control` via `window.cascorControlWS.send({command: "start"})`, the clientside callback that wires buttons to WS-with-REST-fallback, `test_csrf_required_for_websocket_start`, orphaned-command pending-verification UI state.

**Why it's safe to defer**: the REST POST endpoints at `/api/train/{command}` already work, are first-class supported APIs per R0-06 §3.5, and are NOT being removed. Users who click the start button today use REST POST; after minimum-viable Phase B ships, they still use REST POST. The P0 goal (polling elimination) has nothing to do with the button click path.

**Critical observation**: deferring Phase D *also* defers the CSWSH attack surface. The CSWSH high-severity scenario in R0-02 §3.1 is "attacker sends `{command: "start"}` to `/ws/control`." If `/ws/control` isn't consumed by the browser in Phase B, then:

1. The Origin check MVS-SEC-06 on `/ws/training` still closes the live-data exfiltration path (the attacker can't tail training metrics cross-origin).
2. The full cookie+CSRF flow (M-SEC-02) becomes a Phase D prerequisite, not a Phase B prerequisite. This is exactly what R0-06 §3.2 says.

The residual `/ws/control` exposure is the same it is today (no auth at all) — this minimum-viable proposal does not make it worse. When Phase D lands, it pulls in the full M-SEC-01/01b/02/05/07 security suite.

**Caveat**: if a malicious page does `new WebSocket("ws://localhost:8050/ws/control").send({command: "stop"})` TODAY, before this proposal ships, it succeeds (canopy's `/ws/control` has no auth). That is already the case and is not a regression introduced by minimum-viable Phase B. But a reviewer might reasonably ask "why not close the existing hole?" — the answer is that closing it correctly requires the full M-SEC-02 CSRF flow, and doing it wrong (e.g., cookie-only without CSRF) is worse than leaving it as-is. R0-02 §3.1 and §4.2 support this reading.

### 3.3 Phases E / F / G / H / I — DEFERRED (R0-06 §3.6)

| Phase | Defer status | What we keep at minimum | What we drop |
|---|---|---|---|
| **E** (backpressure full fix) | mostly deferred | 0.5 s `_send_json` quick-fix (A-srv-3) | Per-client pump task, bounded queue, policy matrix, `ws_backpressure_policy` setting |
| **F** (heartbeat + jitter) | minimal fold-in to Phase B | Jitter in reconnect backoff (GAP-WS-30, 3-line change in websocket_client.js) | Full heartbeat ping/pong contract, ping-interval config, client-side pong timeout logic, `test_ping_pong_reciprocity`, lifting the 10-attempt reconnect cap (GAP-WS-31) |
| **G** (cascor `set_params` integration test) | fully deferred | — | All `test_set_params_*` in cascor test suite — deferred with Phase C |
| **H** (normalize_metric audit) | regression gate folded | MVS-TEST-14 (Playwright dual-format wire pin) locks in the contract | The full audit document, `_normalize_metric` refactor |
| **I** (asset cache busting) | in scope | MVS-FE-16 — bundled with Phase B because browsers will not see new `websocket_client.js` without it | — |

**Why deferring Phase E full-fix is safe**: R0-03 §5.2 and R0-06 §3.6 both agree that the 0.5 s `_send_json` timeout is sufficient for Phase B's read-side traffic at current scale (≤50 clients). The pump-task model is a Phase E+ optimization. R0-03 explicitly says "Skip the full parallelism for MVP. Phase B-server ships with the serial fan-out + 0.5 s per-send timeout (quick fix)." I concur.

**Why deferring Phase F heartbeat is safe**: the WebSocket path has ping/pong at the framework level (uvicorn handles it). The application-level ping is a nice-to-have that detects TCP half-open faster. At minimum-viable, a stale connection is detected at the next `send_json()` attempt (up to 0.5 s) and the client reconnects — which Phase B handles correctly because of jitter + the `resume` protocol. Skipping application-level heartbeat means a dead connection might hang for up to `receive` timeout (~30 s default), but that is acceptable for the read-side path.

**Why deferring Phase G is safe**: Phase G tests `set_params` on cascor's `/ws/control`. We do not ship `set_params` → we don't need the tests.

**Why deferring Phase H full audit is safe**: MVS-TEST-14 pins the dual-format contract at the wire level. Any future refactor that drops a format breaks the test. That is the regression gate R0-06 §3.6 calls for.

### 3.4 Reconnect / replay buffer beyond minimum — DEFERRED

**What we have at minimum** (A-srv-5 + MVS-FE-02):
- `server_instance_id` advertised and checked on reconnect.
- 1024-event replay buffer (~40 s of coverage at steady-state rate).
- `resume` handler with `resume_ok` / `resume_failed` flow.
- `snapshot_seq` atomic read from REST status endpoint for graceful degradation to snapshot.
- Client-side `seq` tracking, monotonic-check warning, `resume` frame on reconnect, fallback to REST snapshot on `resume_failed`.
- Reconnect backoff **with jitter** (GAP-WS-30).

**What's deferred**:
- **GAP-WS-31 uncapped reconnect attempts**: R0-01 §3.5.1 item 4 wants to lift the 10-attempt cap. Minimum-viable keeps the 10-attempt cap. Rationale: after 10 failed attempts, the REST polling fallback takes over (per MVS-FE-07 1 Hz fallback). The dashboard still works. Lifting the cap is a UX nicety, not a P0 requirement.
- **Multi-tenant per-session replay buffers** (R0-02 §3.4 attack 4 / R0-02 §9.7): explicitly deferred by R0-02 itself. Canopy is single-tenant today; the shared replay buffer is fine.
- **Full bounded JS ring with seq dedup** (R0-01 §3.5.1 item 7): minimum-viable keeps simpler per-handler rings. Duplicate-seq double-apply is not a correctness violation for `Plotly.extendTraces`, which is idempotent relative to the chart's `maxPoints` cap.
- **Older-cascor `resume` unknown-command handling**: minimum-viable cascor IS the cascor with `resume`, so the fallback path (R0-05 MVS-TEST-11 `test_older_cascor_without_resume_command_triggers_fallback`) is a belt-and-suspenders test that we keep but never trigger in production.

**Why it's safe**: the replay buffer + `server_instance_id` + `snapshot_seq` triplet is the **correctness floor**. Any disconnect within the 40-second buffer window replays losslessly. Any disconnect beyond the window falls back to REST snapshot, which is exactly the pre-Phase-B behavior. There is no correctness regression — the worst case is a brief REST-equivalent load during long reconnects, which is the same as today.

### 3.5 Audit logging + full M-SEC suite beyond minimum — DEFERRED

**What's deferred** (R0-02 §4.2-§4.8):

- **M-SEC-02** cookie session + CSRF first-frame. Requires SessionMiddleware (may or may not exist in canopy today — R0-02 §10.10 flags this as unverified), `/api/csrf` endpoint, Dash template token injection, WebSocket first-frame handshake, token rotation, constant-time comparison. ~0.75 day of effort and not needed until Phase D.
- **M-SEC-05** per-command rate limit (leaky bucket, 10 cmd/s). Not needed because we do not accept commands in Phase B.
- **M-SEC-06** opaque close reasons. Only matters for auth-failure paths; we don't have auth failures in Phase B.
- **M-SEC-07 audit logger** (`canopy.audit` logger, `TimedRotatingFileHandler`, scrub allowlist, params_before/after diff, CRLF escaping, user-agent logging). ~0.25 day and not needed until Phase D (it's a control-plane audit).
- **M-SEC-10** idle timeout (120 s). Nice-to-have; not required for Phase B read-side because the 0.5 s send timeout + TCP keepalive already close dead connections.
- **M-SEC-11** adapter inbound validation. Correctness-adjacent, not exploit-driven. Deferred as v1.1.
- **M-SEC-12** log injection escaping. Only relevant when the audit logger exists — deferred with M-SEC-07.
- **JSON depth guard** (R0-02 §4.4 Control 2). Marginal threat; the 4 KB frame cap on `/ws/training` inbound already bounds depth practically.
- **Per-origin handshake cooldown** (R0-02 §4.8). Nice-to-have; the per-IP cap (MVS-SEC-08) handles most of the same threat.
- **Prom counters for auth rejections** (R0-02 §4.6 metrics). Emit-side only — the origin rejection is logged but not counter-incremented. Add in v1.1.

**Why deferring is safe**: the minimum Phase B-pre (§2.2) closes the live-data exfiltration path via Origin validation on `/ws/training`. It does **not** close the CSWSH control-plane path on `/ws/control` — but minimum-viable does not use `/ws/control` from the browser, so the existing exposure is not worsened. The full Phase B-pre suite becomes a hard prereq in the same PR wave as Phase D.

**CAVEAT I want to flag loudly**: if R0-06's reading of "CSWSH is only a Phase D concern" is wrong and there is in fact a Phase B-era scenario where an attacker can exploit `/ws/control` *because* canopy is now actively using the WS layer, the minimum-viable proposal has a P0 hole. I believe the reading is correct — the attack surface on `/ws/control` is identical whether or not Phase B ships — but this is the biggest risk in the minimum-viable carveout and deserves explicit review in Round 2.

### 3.6 Topology chunking (GAP-WS-18 / RISK-16) — DEFERRED

**What's deferred**: chunking of topology messages >64 KB per R0-03 scope list and R0-06 RISK-16.

**Why it's safe**: the existing topology REST fallback path handles this. Minimum-viable keeps the REST poll for `_handle_topology_poll` as the fallback (MVS-FE-10 says "Keep the REST paths — they are the kill switch"). A topology event that exceeds 64 KB will be silently dropped by the server's outbound max_size guard (once one is added) OR will crash during JSON serialization (current behavior). Either way, the dashboard continues to render topology via REST polling at 5 s cadence. This is not ideal but does not undo the P0 goal.

**Residual risk** (RISK-16 Medium/Medium for networks >50-100 hidden units): operators running large networks will see topology not updating in real-time. Document in the Phase B runbook. Fix in v1.1.

---

## 4. Reconciled disagreements

The 6 R0 proposals each have a "disagreements with source doc" section. Where R0 proposals contradict each other, this section picks a winner and justifies it.

### 4.1 Phase B-pre scope: is it "1 day" or "1.5-2 days"?

- **R0-02 §9.1** says 1.5-2 days for the full suite.
- **R0-06 §3.6** says 0.5 day for heartbeat+jitter and references §9.2 of source doc (which says 1 day for Phase B-pre).
- **Source doc §9.2** says 1 day.

**Reconciliation**: the minimum-viable Phase B-pre I define in §2.2 is **~0.5 engineering day** because I drop M-SEC-02/05/06/07/10/11/12 from the scope. R0-06 is right about the source doc's 1-day estimate but also right that it is low; R0-02 is right that 1.5-2 days is more realistic for the full scope. Since we are shipping <50% of the full Phase B-pre scope, the effort estimate comes out **below both** at ~0.5 day.

### 4.2 M-SEC-01 gate Phase B or Phase D?

- **R0-02 §9.2** says "Phase B-pre before Phase B (security must precede the browser bridge so the new attack surface is not exposed)" — i.e., M-SEC-01 gates Phase B.
- **R0-06 §3.2** nuances: "treat M-SEC-03 as a Phase B prerequisite ... treat M-SEC-01/01b/02 as Phase D prerequisites."

**Reconciliation**: I side with R0-06's finer-grained reading **for M-SEC-02** (cookie+CSRF) and **for M-SEC-03** (max_size), but I **disagree** with R0-06 on M-SEC-01 (Origin). Rationale:

- **M-SEC-02** (cookie+CSRF) only matters when there's an authenticated command plane to protect. In minimum-viable Phase B there is no command plane, so M-SEC-02 is correctly deferred to Phase D.
- **M-SEC-03** (max_size) is a pure-DoS guard. R0-06 is right that it must land with Phase B because Phase B adds traffic. R0-02 agrees.
- **M-SEC-01** (Origin) is NOT just about CSWSH on `/ws/control`. It also prevents **live-data exfiltration on `/ws/training`**. R0-02 §3.1 "Information exfiltration" blast-radius bullet makes this explicit. R0-06's reading that M-SEC-01 is a Phase D concern only implicitly assumes the data flowing over `/ws/training` is not sensitive. But R0-02 notes that training metrics, topology, and param values can be competitively sensitive (and at minimum are user-specific state). **Landing Phase B without M-SEC-01 on `/ws/training` would be a regression versus current REST behavior**, which at least has `X-API-Key` protection at the HTTP layer (the canopy adapter talks to cascor with a key; the browser talks to canopy, which is less protected but still on localhost).

**Winner**: include M-SEC-01 + M-SEC-01b in minimum Phase B-pre. This adds ~2 hours of effort versus R0-06's "defer to Phase D" reading and eliminates the exfiltration attack class. The full CSRF flow stays deferred.

### 4.3 rAF coalescing: ship or defer?

- **R0-01 §3.3.3** self-deferred: "for Phase B, ship WITHOUT the rAF path ... rAF coalescing is a Phase B+1 optimization if instrumentation shows it is needed."
- **Source doc GAP-WS-15** is P1 and says "browser-side `requestAnimationFrame` coalescing for high-frequency events."
- **R0-01 §7** flags this as a deviation from the source doc.

**Reconciliation**: R0-01's self-deferral is correct. The 100 ms drain interval already achieves 10 Hz render rate. 60 Hz is not the bottleneck. Minimum-viable defers rAF.

**Winner**: defer. Scaffold stays in `ws_dash_bridge.js` but unwired.

### 4.4 `/ws/control` `seq` field: Option 1 or Option 2?

- **R0-03 §6.3** recommends Option 2: `command_response` is personal, does not consume a seq. Separate seq namespaces for `/ws/training` and `/ws/control`.
- Source doc does not prescribe.

**Reconciliation**: R0-03's Option 2 is cleaner. Minimum-viable adopts it. Since we defer `/ws/control` consumption entirely, the decision is moot for v1 but still lands in Phase A-server as a design choice.

### 4.5 `disable_ws_auth` flag naming

- **R0-02 §9.4** proposes `Settings.ws_security_enabled=True` (positive-sense) over `Settings.disable_ws_auth=False`.
- Source doc uses `disable_ws_auth`.

**Reconciliation**: the minimum-viable Phase B-pre doesn't ship cookie+CSRF, so neither flag exists at v1. The question is moot for minimum scope. Flag for Round 2 / Phase D.

### 4.6 Effort estimates

R0-06's 4-day Phase B estimate vs R0-01's implicit ~3-day estimate: reconciled by the minimum carveout. Minimum-viable Phase B frontend is ~3 days; Phase A-server is ~2 days; minimum Phase B-pre is ~0.5 day; tests are ~1 day. **Total: ~6.5 engineering days** for the minimum-viable wave, versus R0-06's §9.11 total of 12 engineering days for A+B-pre+B+C+D+E+F+G+H+I.

This is consistent with carving out half the phases.

### 4.7 Disagreement I am creating: state coalescer (GAP-WS-21) is Phase A-server

- **R0-03 §7.1 commit 7** puts GAP-WS-21 in Phase A-server.
- Source doc does not prescribe a phase for GAP-WS-21; it lives in §3.1.3 as a correctness bug.
- R0-05 does not separately exercise GAP-WS-21.
- R0-06 does not mention GAP-WS-21.

**Decision**: include GAP-WS-21 in minimum Phase A-server. Rationale: the drop-filter bug silently drops terminal state transitions. In Phase B, the browser renders state changes via the same WebSocket path. If the state coalescer is broken, the user's training will appear to complete but the badge will still say "running" because the final `Completed` transition was dropped. This is a user-visible regression that Phase B would reveal. Fixing it in Phase A-server is tiny.

---

## 5. Implementation steps (concrete, ordered)

Numbered, dependency-ordered. Each step is 0.5-2 hours of work. File paths are absolute where R0 proposals cite them. Day-level groupings are aspirational but the *ordering* is binding.

### Day 1: cascor Phase A-server commits 1-4 (manager core)

1. **A-srv-1**: edit `juniper-cascor/src/api/websocket/messages.py` — add optional `seq: Optional[int] = None` to every envelope builder. No callers yet. (R0-03 §7.1 commit 1)
2. **A-srv-2a**: edit `juniper-cascor/src/api/websocket/manager.py` — add `server_instance_id`, `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer: deque[tuple[int, dict]](maxlen=1024)`, `_assign_seq_and_append()`. (R0-03 §3.1, §3.2)
3. **A-srv-2b**: update `connect()` to send `connection_established` with `server_instance_id`, `server_start_time`, `replay_buffer_capacity` in `data`. (R0-03 §4.1)
4. **A-srv-3**: replace `_send_json()` body with `asyncio.wait_for(ws.send_json(msg), timeout=0.5)` wrapped in try/except. (R0-03 §5.2 quick-fix)
5. **A-srv-4**: add `replay_since(last_seq)` method + `ReplayOutOfRange` exception. (R0-03 §3.3)
6. **MVS-TEST-01**: unit tests for seq monotonicity, seq-lock separation from broadcast lock.
7. **MVS-TEST-02**: unit tests for replay buffer bounded-ness, `replay_since` boundary cases, `connection_established` envelope contents.
8. **MVS-TEST-03**: unit test for `_send_json` 0.5 s timeout with a never-resolving fake send.

### Day 2: cascor Phase A-server commits 5-9 (training_stream, protocol errors, coalescer)

9. **A-srv-5a**: edit `juniper-cascor/src/api/websocket/training_stream.py` — add `_pending_connections` set, `connect_pending()`, `promote_to_active()` methods. (R0-03 §5.1 two-phase registration)
10. **A-srv-5b**: add resume handler with 5 s frame timeout, `resume` / `resume_ok` / `resume_failed` dispatch, promotion to active, initial_status send. (R0-03 §6.1 full handler code block)
11. **A-srv-6**: edit `juniper-cascor/src/api/routes/training.py` (or wherever `/api/v1/training/status` lives) — add `snapshot_seq` and `server_instance_id` to response, read atomically under `_seq_lock`. (R0-03 §6.2)
12. **A-srv-7**: edit `juniper-cascor/src/lifecycle/manager.py:133-136` — replace 1 Hz drop filter with debounced coalescer; terminal transitions bypass throttle. (R0-03 §7.1 commit 7)
13. **A-srv-8**: edit `broadcast_from_thread` — add done_callback for exception logging. (R0-03 §7.1 commit 8)
14. **A-srv-9**: edit `juniper-cascor/src/api/websocket/control_stream.py` — minimal protocol error responses (unknown command, non-JSON close 1003). (R0-03 §6.3 table)
15. Unit tests for resume paths (MVS-TEST-02 continuation), state coalescer (MVS-TEST-07), protocol error responses, `snapshot_seq` atomic read.

### Day 3: cascor + canopy Phase B-pre minimum (security gate)

16. **MVS-SEC-01**: create `juniper-cascor/src/api/websocket/origin.py` with `validate_origin` helper. (R0-02 §4.1, §6.1)
17. **MVS-SEC-02**: `juniper-cascor/src/tests/unit/api/test_websocket_origin.py`. (MVS-TEST-06)
18. **MVS-SEC-03**: wire `validate_origin` into `training_stream_handler`. (R0-02 §6.1)
19. **MVS-SEC-04**: add `Settings.ws_allowed_origins` + env var `JUNIPER_WS_ALLOWED_ORIGINS` (default `[]` = reject-all).
20. **MVS-SEC-05**: create `juniper-canopy/src/backend/ws_security.py` with `validate_origin`.
21. **MVS-SEC-06**: wire into `juniper-canopy/src/main.py` `/ws/training` route.
22. **MVS-SEC-07**: add `Settings.allowed_origins` to canopy config with localhost defaults.
23. **MVS-SEC-08**: add per-IP counter to `WebSocketManager` + decrement in disconnect finally. (R0-02 §4.5 Control 1)
24. **MVS-SEC-09**: `Settings.ws_max_connections_per_ip: int = 5`.
25. **MVS-SEC-10**: `test_websocket_per_ip_cap.py` including race test. (MVS-TEST-05)
26. **MVS-SEC-11**: add `max_size=4096` to `/ws/training` receive in cascor `training_stream.py`.
27. **MVS-SEC-12**: same in canopy `main.py` `/ws/training`.
28. **MVS-SEC-13**: `test_websocket_size_limits.py` asserting 1009 close. (MVS-TEST-04)
29. **MVS-SEC-14**: `juniper-canopy/src/tests/unit/test_ws_security_origin.py`. (MVS-TEST-09)

### Day 4: canopy Phase B frontend core wiring (MVS-FE-01 to MVS-FE-05)

30. **MVS-FE-01**: create `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` per R0-01 §3.2.1 skeleton. Implement ring-buffer bound in handler.
31. **MVS-FE-02**: edit `juniper-canopy/src/frontend/assets/websocket_client.js` — add `onStatus()` enrichment, jitter, `server_instance_id` capture, seq tracking, `resume` frame on reconnect, graceful fallback on `resume_failed`.
32. **MVS-FE-03**: delete parallel clientside callback at `dashboard_manager.py:1490-1526`.
33. **MVS-FE-04**: add `ws-metrics-buffer` drain callback per R0-01 §3.2.2.
34. **MVS-FE-05**: update existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks to use `window._juniperWsDrain`. Delete old globals.
35. Canopy unit test: `test_ws_dash_bridge.py` (MVS-TEST-08).

### Day 5: canopy Phase B polling toggle + chart migration (MVS-FE-06 to MVS-FE-16)

36. **MVS-FE-06**: add `ws-connection-status` store + drain callback per R0-01 §3.4.1.
37. **MVS-FE-07**: refactor `_update_metrics_store_handler` for `no_update`-when-connected + 1 Hz fallback.
38. **MVS-FE-08**: rewrite `MetricsPanel.update_metrics_display()` as clientside_callback with `Plotly.extendTraces(maxPoints=5000)`. Add `uirevision`. Add dummy signal Store.
39. **MVS-FE-09**: same for `CandidateMetricsPanel`.
40. **MVS-FE-10**: apply polling toggle to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`.
41. **MVS-FE-11**: wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape graph callback. Keep REST poll as fallback.
42. **MVS-FE-12**: connection indicator badge component.
43. **MVS-FE-13**: demo mode sets `ws-connection-status` to `{connected: true, mode: "demo"}`.
44. **MVS-FE-14**: create `juniper-canopy/src/frontend/assets/ws_latency.js` (~50 LOC, POST to `/api/ws_latency` every 60 s).
45. **MVS-FE-15**: create `/api/ws_latency` POST endpoint in canopy `main.py` + Prom histogram + `canopy_rest_polling_bytes_per_sec` gauge.
46. **MVS-FE-16**: Phase I asset cache busting.

### Day 6: Integration + e2e tests

47. **MVS-TEST-10**: `test_cascor_adapter_ws.py` integration tests using `FakeCascorServerHarness`.
48. **MVS-TEST-11**: `test_ws_reconnect_replay.py` including `test_reconnect_replays_10_missed_events`, `test_reconnect_with_stale_server_instance_id_triggers_snapshot`, `test_snapshot_seq_bridges_no_gap`, `test_older_cascor_without_resume_command_triggers_fallback`.
49. **MVS-TEST-12**: `dash_duo` test suite — `test_browser_receives_metrics.py` with the 7 tests enumerated in §2.4.1.
50. **MVS-TEST-13**: Playwright wire tests.
51. **MVS-TEST-14**: Playwright dual-format regression gate.
52. **MVS-TEST-15**: Playwright bandwidth proof test.

### Day 7: Staging deploy, metrics verification, runbook

53. Deploy to staging.
54. Verify Prometheus is scraping `canopy_rest_polling_bytes_per_sec` + `canopy_ws_delivery_latency_ms_bucket`.
55. Verify "WebSocket health" dashboard panel shows data.
56. Run a 24-hour soak for RISK-10 browser memory observation.
57. Write `juniper-canopy/notes/runbooks/ws-bridge-kill.md`.
58. Sign-off on the P0 metric: `canopy_rest_polling_bytes_per_sec` reduced >90% vs pre-Phase-B baseline.
59. Production deploy via blue/green.

**Total minimum-viable effort**: 7 engineering days end-to-end (including staging soak). Compare to R0-06 §9.11's 12-day total for all phases.

---

## 6. Acceptance criteria for "minimum viable shipped"

Each criterion is concrete and testable. Ordered by phase.

### 6.1 Phase A-server exit criteria

1. `seq` field present and monotonically increasing on every `/ws/training` broadcast envelope (verified by MVS-TEST-01 + MVS-TEST-13 `test_websocket_frames_have_seq_field`).
2. `connection_established` message contains `server_instance_id` (UUID4 string) and `server_start_time` (float) (verified by MVS-TEST-02 `test_connection_established_advertises_instance_id`).
3. Replay buffer bounded at 1024 entries with drop-oldest eviction (verified by MVS-TEST-02 `test_replay_buffer_bounded_1024`).
4. `resume` handler returns replayed events in seq order for in-range `last_seq` (MVS-TEST-02 `test_resume_replays_events_after_last_seq`).
5. `resume_failed` returned for `out_of_range` and `server_restarted` cases (MVS-TEST-02).
6. `/api/v1/training/status` response includes `snapshot_seq` atomically under `_seq_lock` (MVS-TEST-02 `test_snapshot_seq_atomic_with_state_read`).
7. `_send_json` quick-fix: a never-resolving fake send returns False within 0.5-0.6 s and does not block fan-out to other clients (MVS-TEST-03).
8. `lifecycle/manager.py` state coalescer does not drop terminal `Completed`/`Failed`/`Stopped` transitions (MVS-TEST-07).

### 6.2 Phase B-pre minimum exit criteria

9. Origin header mismatch on canopy `/ws/training` is rejected with pre-accept 403 or ws.close(1008) (MVS-TEST-09).
10. Origin header mismatch on cascor `/ws/training` is rejected (MVS-TEST-06).
11. Empty allowlist = reject-all (fail-closed) on both canopy and cascor.
12. 65 KB inbound frame on `/ws/training` closes with 1009 (MVS-TEST-04).
13. 6th connection from same IP to cascor `/ws/training` closes with 1013 (MVS-TEST-05).
14. Per-IP counter returns to zero after all connections close (MVS-TEST-05 race test).

### 6.3 Phase B minimum exit criteria

15. Browser receives `metrics` events over WebSocket and renders them in the metrics panel without REST polling (MVS-TEST-12 `test_chart_updates_on_each_metrics_event`).
16. When WebSocket is healthy, `/api/metrics/history` receives **zero** requests after initial load for 60 seconds (MVS-TEST-15 `test_polling_elimination`).
17. When WebSocket disconnects, dashboard falls back to REST polling at 1 Hz cadence within the next `fast-update-interval` tick (MVS-TEST-12 `test_chart_falls_back_to_polling_on_websocket_disconnect`).
18. Plotly chart uses `extendTraces` (not `react` with full data) (MVS-TEST-13 `test_plotly_extendTraces_used_not_full_figure_replace`).
19. `uirevision` preserves pan/zoom across chart updates.
20. Connection indicator badge reflects `ws-connection-status` store state (MVS-TEST-12 `test_connection_indicator_badge_reflects_state`).
21. Demo mode shows "demo" state on badge and polling toggle returns `no_update` (MVS-TEST-12 `test_demo_mode_metrics_parity` — RISK-08 gate).
22. `ws-metrics-buffer` store is bounded at 1000 events (MVS-TEST-12 `test_ws_metrics_buffer_store_is_ring_buffer_bounded` — RISK-10 gate).
23. 24-hour staging soak completes without browser memory growth exceeding 500 MB p95 (RISK-10 gate).
24. **`metrics` event data contains BOTH flat AND nested metric keys** (MVS-TEST-14 — Phase H regression gate).

### 6.4 Phase B operational exit criteria

25. `canopy_rest_polling_bytes_per_sec` gauge present in Prometheus scrape.
26. `canopy_rest_polling_bytes_per_sec` reduced **>90%** versus pre-Phase-B baseline in staging (measured for 1 hour post-deploy).
27. `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute.
28. "WebSocket health" dashboard panel renders p50/p95/p99 values.
29. `canopy_ws_active_connections` gauge present; alert at 80% of cap.
30. `Settings.disable_ws_bridge=True` kill switch tested manually in staging; flipping it restores pre-Phase-B REST polling behavior within 5 minutes TTF.
31. Runbook `ws-bridge-kill.md` published.

### 6.5 The P0 win, stated concretely

**The P0 win is achieved when criterion #26 is met in production for ≥24 hours with no alerts firing.**

That single criterion is the reason this proposal exists. All 30 other criteria exist to make it safe and measurable.

---

## 7. Risk register (subset of R0-06)

Only risks that apply to the minimum-viable scope. R0-06 has 16 risks; this subset has 8.

| ID | Severity / Likelihood | Phase | Mitigation at minimum scope | Kill switch |
|---|---|---|---|---|
| **RISK-02** — Phase B clientside_callback wiring hard to debug | Medium/High | B | Playwright trace viewer + dash_duo store assertions (MVS-TEST-12/13) + Option B drain pattern + runbook | `disable_ws_bridge=True` (5 min TTF) |
| **RISK-08** — Demo mode parity breaks after migration | Low/Medium | B | `test_demo_mode_metrics_parity` as blocker (MVS-TEST-12) + MVS-FE-13 demo mode sets connection status | Revert PR (10 min TTF) |
| **RISK-10** — Browser memory exhaustion from unbounded chart data | Medium/High | B | `Plotly.extendTraces(maxPoints=5000)` + JS handler ring bound (not drain-callback bound, per R0-01 §3.2.5) + 24-hour staging soak gate | `disable_ws_bridge=True` |
| **RISK-12** — Background tab memory spike when foregrounded | Low/Medium | B | Same as RISK-10 — ring bound in handler, not drain | Same |
| **RISK-14** — Cascor crash mid-broadcast leaves clients inconsistent | Low/Low | B | `server_instance_id` change forces client resync via snapshot (A-srv-2, MVS-FE-02) | Rolling restart canopy (10 min TTF) |
| **RISK-15** — CSWSH attack exploits missing Origin validation | **High/Medium** | B-pre | **Partially mitigated** at minimum: Origin check on `/ws/training` closes exfiltration path; `/ws/control` exposure is unchanged from current state (no regression) | None for control plane; `/ws/control` is not used in Phase B, so the attack surface is not new |
| **RISK-16** — Topology message exceeds 64 KB silently | Medium/Medium | B-pre | **Partially mitigated**: REST fallback for topology polling is preserved (MVS-FE-10). Server-side size guard not added. | REST fallback |
| **RISK-04** — Slow-client blocking manifests in dev workflows | Medium/Medium | E | **Mitigated via quick fix**: A-srv-3 `_send_json` 0.5 s timeout prunes slow clients within 0.5 s | `ws_backpressure_policy=close_slow` (deferred to v1.1; quick-fix is sufficient for minimum scope) |

**Risks explicitly NOT applicable at minimum scope**: RISK-01 (Phase H), RISK-03 (Phase C), RISK-05 (coverage issue for D), RISK-06 (Phase F), RISK-07 (multi-tenant), RISK-09 (Phase C UX), RISK-11 (Phase E full backpressure), RISK-13 (Phase C/D command correlation).

**Biggest residual risk**: RISK-15 on `/ws/control`. This is **not a regression from the current state** but minimum-viable does not improve it either. Document prominently in the runbook and in the PR description. Clear that "this PR does not close CSWSH on `/ws/control`; Phase D will."

---

## 8. Recommended next milestone

After minimum-viable ships and the P0 metric (criterion #26) holds in production for ≥1 week, the recommended second proposal priority is:

### 8.1 Next milestone: Phase C + Phase D + full Phase B-pre (v1.1)

Reason for bundling C, D, and the remaining Phase B-pre into a single v1.1 milestone:

- **Phase D unlocks the full CSWSH remediation** (M-SEC-02 CSRF), which is the largest residual P0 security concern (RISK-15).
- **Phase C brings user-visible `set_params` improvements** that require the same feature flag scaffolding as Phase D.
- **Phase C depends on Phase A (SDK method published to PyPI)** — the SDK work must happen first, which is best scoped together with Phase C.
- **The Phase B-pre backlog** (M-SEC-02, M-SEC-05, M-SEC-06, M-SEC-07 audit logger, M-SEC-10, M-SEC-11) all apply to the `/ws/control` surface, which Phase C and Phase D consume. Landing them together is natural.

### 8.2 v1.1 rough scope

- **SDK Phase A** (R0-04 §4-§5): `CascorControlStream.set_params()` method + PyPI publish.
- **Phase C** (R0-04 §6-§7): canopy adapter hot/cold splitter, `Settings.use_websocket_set_params` flag (default False), per-key routing, fallback to REST on WS error.
- **Phase D**: control buttons over WebSocket with REST fallback, orphaned-command UI state.
- **Full Phase B-pre suite** (R0-02 §4.2-§4.8): cookie+CSRF, `SessionMiddleware`, `/api/csrf` endpoint, full per-command rate limit, opaque close reasons, audit logger with scrub allowlist, idle timeout, adapter inbound validation.
- **Phase G** (R0-03 §7.3, R0-05 §4.1 Phase G): cascor `set_params` integration tests.
- **Phase F remaining**: heartbeat ping/pong contract, lift 10-attempt reconnect cap (GAP-WS-31).

### 8.3 v1.2 and beyond

- **Phase E full backpressure**: per-client pump task, bounded queue, policy matrix, `ws_backpressure_policy` (R0-03 §5.2).
- **Phase H audit**: `_normalize_metric` refactor with the regression gate already in place.
- **Topology chunking (GAP-WS-18 / RISK-16)**.
- **Multi-tenant per-session replay buffers** (R0-02 §9.7).
- **rAF coalescing enabled** (GAP-WS-15) if §5.6 histogram shows jank.
- **Full JS bounded-ring with seq dedup** (R0-01 §3.5.1 item 7).

### 8.4 Iteration rationale

The minimum-viable proposal buys a week of engineering time in exchange for the P0 win and the measurement infrastructure. The measurement infrastructure (§5.6 histograms) is what enables the Phase C flag-flip decision in v1.1 — without the histograms, Phase C is a judgment call. With them, it is evidence-based.

Ship order for v1.1 (if the bundling holds): SDK Phase A PyPI publish → cascor `command_id` echo + full M-SEC-02 → canopy Phase C adapter + Phase D button wiring + full audit logger. All depend on v1.0 being in production.

---

## 9. Disagreements with R0 inputs

### 9.1 Disagreement with R0-06 §3.2: M-SEC-01 is a Phase B prereq, not just Phase D

R0-06 §3.2 treats M-SEC-01/01b/02 as Phase D prerequisites and only M-SEC-03 as a Phase B prerequisite. I disagree on M-SEC-01/01b specifically. Rationale spelled out in §4.2: Origin validation on `/ws/training` closes the live-data exfiltration blast-radius item from R0-02 §3.1. The cost is ~0.5 day; the payoff is closing an entire attack class. R0-06's cost-side reasoning is right that the full M-SEC-02 suite is Phase-D-gated, but M-SEC-01 is narrower and cheaper and should land with Phase B.

### 9.2 Disagreement with R0-01 §3.5.1 item 4: keep 10-attempt reconnect cap

R0-01 §3.5.1 wants to lift the 10-attempt cap (GAP-WS-31). Minimum-viable keeps the cap because the REST polling fallback covers the "WebSocket permanently unreachable" scenario. Lifting the cap is v1.1 work. This is a scope-conservation call, not a disagreement about correctness.

### 9.3 Disagreement with R0-01 §3.5.1 item 8: keep dead helpers

R0-01 wants to delete `getBufferedMessages()` and other dead helpers in `websocket_client.js`. Minimum-viable keeps them. Deletion has no bearing on the P0 goal and risks breaking a test that reaches for the helper. v1.1 cleanup.

### 9.4 Disagreement with R0-02 §9.4 flag naming

R0-02 argues `ws_security_enabled=True` (positive) over `disable_ws_auth=False` (negative). Minimum-viable ships neither flag because M-SEC-02 is deferred. When Phase D lands, I side with R0-02's positive-sense naming, but the decision is deferred with the feature.

### 9.5 Disagreement with R0-03 §5.2 re: Phase B-server vs Phase E-server

R0-03 §5.2 proposes shipping the full backpressure pump-task model as part of "Phase A-server." I cut this: minimum-viable ships only the 0.5 s quick-fix from R0-03 §7.1 commit 3. The full pump-task model is v1.2 (deferred further than v1.1 because it is a correctness improvement that doesn't unlock any P0 feature).

### 9.6 Agreement with R0-04 §3 that Phase C is P2

R0-04 §3 makes the definitive argument that Phase C's ack-latency improvement is invisible inside effect-observation latency. I cite this as the justification for deferring Phase C to v1.1. Not a disagreement — but worth explicitly naming the agreement because R0-01 and R0-06 both reference Phase C as a near-term item.

### 9.7 Disagreement with R0-05 §7.3 fuzz testing recommendation

R0-05 §7.3 recommends `hypothesis`/`atheris` fuzzing of envelope parsers. Minimum-viable does not ship fuzz tests. Rationale: the minimum scope does not expose many new parser paths (we only add `resume` + `seq` fields), and the existing unit tests catch the shapes we care about. Fuzz tests are v1.2+.

### 9.8 Agreement with R0-05 §6.3 re: frame-budget flakiness

R0-05 §6.3 itself flags frame-budget tests as flaky and recommends trace-only fallback. I fully agree and drop frame-budget assertions from minimum scope. The §5.6 histogram (MVS-FE-14) is the actual latency gate.

---

## 10. Self-audit log

First pass produced §1-§9 following the outline. This self-audit captures re-read findings and records what changed.

### 10.1 Did I scope enough out?

Re-read §2 (in-scope) against the P0 goal statement in §1.1:

- **Question**: do we need A-srv-7 (state coalescer) at minimum? **Answer**: yes. Without it, Phase B's WebSocket state updates silently drop terminal transitions, which is a worse user experience than pre-Phase-B REST polling. This is a correctness floor, not a P0-alignment question. Keep.
- **Question**: do we need A-srv-8 (`broadcast_from_thread` exception handling)? **Answer**: 3-line change; leaves silent exceptions in place if deferred. Keep.
- **Question**: do we need A-srv-9 (protocol error responses on `/ws/control`)? **Answer**: `/ws/control` is NOT consumed by the browser in minimum Phase B. Hmm. But the training handler in A-srv-5 references the error pattern. The minimum subset I actually need is "unknown type rejection on `/ws/training`" and "non-JSON close 1003 on `/ws/training`" — both are natural consequences of the two-phase registration handler code block. The `/ws/control` protocol error responses can actually be **deferred** because `/ws/control` is not new attack surface at minimum. **Edit**: I should narrow A-srv-9 scope to cover just `/ws/training` error responses. But R0-03 §7.1 bundles it with `/ws/control`. Keeping the bundle avoids a half-measure; dropping the `/ws/control` half would save ~1 hour. **Decision**: keep the bundle because R0-06 §8.1 wants Phase A-server to ship as a coherent release, and splitting GAP-WS-22 further creates test-ownership confusion.
- **Question**: MVS-TEST-14 (dual-format Playwright test) — is this really minimum? **Answer**: yes. Without it, Phase H can't be deferred safely. The test is ~20 LOC and protects against a costly regression class. Keep.
- **Question**: MVS-TEST-15 (bandwidth proof) — is this minimum? **Answer**: yes. It is the **only** test that directly validates the P0 goal. Without it, we can't claim minimum-viable shipped. Keep.
- **Question**: MVS-FE-11 (cytoscape WS wiring) — could we defer NetworkVisualizer entirely and only wire it to REST polling, treating the WS topology buffer as unused for minimum scope? **Answer**: the topology REST poll is 5 s cadence, not 100 ms, so it does NOT contribute significantly to the 3 MB/s P0 budget. Deferring MVS-FE-11 would save ~0.25 day. **Edit decision**: keep MVS-FE-11 in the minimum. Rationale: the architecture doc's §2.8 shows topology polling as one of the paths that must be WS-toggled. Shipping Phase B without wiring the topology WS path leaves `ws-topology-buffer` as a half-wired feature, which creates confusion when reviewing the PR. The effort is small. Keep.
- **Question**: MVS-FE-16 (asset cache busting) — do we NEED this or can browsers hard-refresh? **Answer**: R0-06 §3.6 Phase I says "Mandatory before Phase B goes to production — otherwise users will see stale `websocket_client.js`." If a stale cache serves the pre-Phase-B JS, the browser opens the WS, fails to handle `resume`, fails to read `seq`, and the polling toggle fires as "disconnected" — polling never stops. Without cache busting, the P0 win does not reach production. **Keep — non-negotiable**.

Verdict: no changes to the in-scope list. The scoping is tight.

### 10.2 Did I scope enough IN?

Re-read §3 (deferrals) against the correctness floor:

- **Question**: am I right that deferring Phase D is safe? **Answer**: yes, provided minimum-viable PR description explicitly states "this PR does not change the security posture of `/ws/control`, which remains unauthenticated." If reviewers accept the current posture of `/ws/control` being unauthenticated (which they do today — no one has shipped a fix), they will accept the unchanged posture. Document loudly in the PR.
- **Question**: am I right that deferring M-SEC-02 (CSRF) is safe? **Answer**: yes because `/ws/control` is not used in minimum. But I'm assuming no Phase B-era code path touches `/ws/control`. Let me double-check: the existing dead `websocket_client.js` has a `window.cascorControlWS` object. MVS-FE-02 cleans up the file but does NOT wire `cascorControlWS` to any clientside callback in minimum scope. The object is exposed but has no callers. That's fine — exposing a JS class in a module scope is not the same as using it. Verdict: safe.
- **Question**: am I right that deferring rAF coalescing is safe? **Answer**: R0-01 §3.3.3 self-defers. The 100 ms drain interval produces ~10 Hz render rate, under the 60 Hz budget. Safe. Flag for v1.2 if §5.6 histogram shows jank.
- **Question**: am I right that the 1024-event replay buffer is enough at minimum? **Answer**: R0-03 §3.1 says 1024 covers ~40 seconds, which covers the typical 5-second WiFi blip. Longer disconnects fall back to REST snapshot (MVS-FE-02 + A-srv-6). That fallback path is well-tested in MVS-TEST-11. Verdict: safe.
- **Question**: am I missing a correctness scenario where the minimum-viable deferrals create data loss? **Answer**: I walked through the critical scenarios:
  - Short blip (<40s): replay buffer covers it. ✓
  - Long blip (>40s): snapshot fallback via REST. ✓
  - Server restart: `server_instance_id` mismatch → resume_failed → snapshot fallback. ✓
  - Client crash: reconnect starts fresh, no `last_seq` → fresh connect. ✓
  - Cascor restart with no clients connected: replay buffer empty at start anyway. ✓
  - Topology >64 KB: silently dropped by outbound max_size (if we had one) — we don't have outbound max_size at minimum, so it uses the framework default. Currently topology just serializes fine regardless of size (Starlette default is 1 MB). Not a data loss risk at minimum. ✓
  - Metric with out-of-order seq: monotonic check warn, but no data loss because `Plotly.extendTraces` renders whatever comes.
  - **Gap identified**: what if two browsers are viewing the same cascor simultaneously, one disconnects and reconnects, and the replay interferes with the other's live stream? R0-03 §5.1 two-phase registration handles this — the reconnecting browser is in `_pending_connections` during replay, not `_active_connections`, so the live broadcast is not affected. ✓
- **Question**: does deferring the per-IP cap auth-timeout subpart (M-SEC-04) leave a hole? **Answer**: the auth-timeout subpart (5-second wait for first frame) only matters if there is an auth flow. Without M-SEC-02 CSRF, there is no auth frame to wait for. The per-IP cap itself protects against connection-count flooding, which is what Phase B scales up. Safe.

Verdict: no scope additions needed.

### 10.3 Are deferrals justified?

Walked §3 top-to-bottom:

- §3.1 Phase C: cited R0-04 §3 P2 downgrade — strong justification.
- §3.2 Phase D: cited R0-06 §3.5 that REST preserves current path — strong justification.
- §3.3 Phases E/F/G/H/I: each has a specific carveout rationale. Phase E quick-fix kept; Phase F jitter kept; Phase I cache busting kept. G/H deferred cleanly.
- §3.4 Reconnect beyond minimum: the correctness floor is preserved. Only UX niceties deferred.
- §3.5 Audit + M-SEC: narrow scoping tied to deferring Phase D.
- §3.6 Topology chunking: REST fallback preserved.

All deferrals have an explicit source citation and an explicit safety argument. None are "we'll get to it someday" hand-waves.

### 10.4 Is the path safe end-to-end?

Trace the critical path from "user opens dashboard" → "polling eliminated":

1. User opens `http://localhost:8050` in browser. Canopy serves Dash page with embedded `websocket_client.js` + `ws_dash_bridge.js` (cache-busted per MVS-FE-16).
2. Page JS evaluates `new window.cascorWS()`. The `cascorWS` constructor opens `ws://localhost:8050/ws/training`.
3. Canopy `main.py` `/ws/training` handler runs `validate_origin(ws, allowlist)` (MVS-SEC-06). Origin matches localhost. Accept proceeds.
4. Canopy's adapter (already working per R0-01 §3.1) is relaying cascor's `/ws/training` to canopy's `/ws/training`. Frames flow.
5. Cascor `WebSocketManager.connect()` runs per-IP cap check (MVS-SEC-08). Passes. Sends `connection_established` with `server_instance_id`, `server_start_time`.
6. Cascor enters two-phase registration (A-srv-5). Client is in `_pending_connections`. Waits 5 s for `resume` frame.
7. Fresh client does not send `resume` → timeout → promoted to `_active_connections`. Initial status sent.
8. Cascor training loop broadcasts `metrics` events via `_assign_seq_and_append` (A-srv-2). Each event gets a monotonic `seq`.
9. Browser receives `metrics` → `ws_dash_bridge.js` handler pushes to `_buffers.metrics[]` (bounded at 1000 per MVS-FE-01).
10. Every 100 ms, `fast-update-interval` fires → Dash drain callback runs (MVS-FE-04) → reads `window._juniperWsDrain.drainMetrics()` → writes to `ws-metrics-buffer` store.
11. `ws-metrics-buffer.data` change triggers the extendTraces clientside callback (MVS-FE-08) → `Plotly.extendTraces('metrics-panel-figure', update, [0,1,2,3], 5000)`.
12. Simultaneously, `_update_metrics_store_handler` (MVS-FE-07) fires on the same tick, reads `ws-connection-status` via State, sees `{connected: true}`, returns `no_update`. **No REST GET fires**.
13. `canopy_rest_polling_bytes_per_sec` gauge drops to near-zero. P0 goal met.

Simulated failure paths:

- **Browser closes tab**: cascor `disconnect()` decrements per-IP counter. Replay buffer keeps the last 1024 events for 40 s. If user reopens within 40 s, reconnect with `last_seq` works via replay.
- **Cascor restarts**: new `server_instance_id`. Browser's saved UUID mismatches. `resume_failed {reason: "server_restarted"}` → browser falls back to REST `/api/v1/training/status` for snapshot + new `last_seq` from `snapshot_seq`. Live stream resumes.
- **WebSocket disconnects mid-stream**: client tries to reconnect with jitter. On success, sends `resume {last_seq: N, server_instance_id: ...}`. Cascor replays events seq > N. Browser receives them via normal `metrics` path. Charts extend with missed events.
- **Cross-origin attack attempt**: attacker page at `evil.example` does `new WebSocket("ws://localhost:8050/ws/training")`. Canopy `validate_origin` rejects. Connection closed pre-accept. Attack fails.
- **100 KB frame injection on `/ws/training`**: framework-level `max_size=4096` (MVS-SEC-12) closes with 1009. Connection pruned. Training stream unaffected for other clients.
- **Single slow client (devtools tab)**: cascor `_send_json` 0.5 s timeout (A-srv-3) prunes the slow client. Other clients continue receiving events.
- **Demo mode**: `ws-connection-status` is `{connected: true, mode: "demo"}` → polling toggle returns `no_update` → charts updated via the demo mode's local event source. Unchanged from pre-Phase-B.

**Verdict**: end-to-end path is safe. One clarifying edit needed — I should explicitly document that the canopy adapter continues to talk to cascor via the existing adapter path, which uses `X-API-Key` (not browser auth). Minimum-viable does not change how canopy talks to cascor; it only changes how the browser talks to canopy.

### 10.5 Edits applied from self-audit

| # | Edit | Section |
|---|---|---|
| 1 | Explicit note that canopy↔cascor path is unchanged; only browser↔canopy is new | Added to §2.1 opening paragraph — see Edit 1 below |
| 2 | Clarified that `/ws/control` protocol error responses (A-srv-9) apply to `/ws/training` at minimum | Added note to §2.1 step A-srv-9 |
| 3 | Added explicit statement of residual RISK-15 posture in §7 | Already present — no change |
| 4 | Added Day 7 staging soak sign-off criterion explicitly tied to criterion #26 | Already present — no change |
| 5 | Verified that the 16 frontend steps MVS-FE-01 through MVS-FE-16 cover all the R0-01 steps 1-19 minus the deferred ones | Traced — complete |
| 6 | Noted that MVS-TEST-15 is a new contribution of this proposal not present in R0-05 | Already noted in §2.4.1 |

### 10.6 Residual open questions for Round 2

These are things Round 2 consolidation should resolve:

- **Q1-R1-01**: verify that canopy currently has or does not have `SessionMiddleware` — R0-02 §10.10 flags this as unverified. If it is NOT present, adding it is part of the Phase D v1.1 effort. If it IS present, the CSRF flow is a smaller delta.
- **Q2-R1-01**: confirm the `/ws/control` unauthenticated exposure is accepted by reviewers as "not worse than today." If reviewers object, pull M-SEC-02 into minimum-viable, which adds ~0.75 day.
- **Q3-R1-01**: confirm the `canopy_rest_polling_bytes_per_sec` gauge is feasible — it requires instrumentation at the `_update_metrics_store_handler` return path to count bytes when REST is actually fetched. May need access to the REST response size, which is cheap to measure.
- **Q4-R1-01**: the R0-05 `FakeCascorServerHarness` is a NEW fixture. Can it land in the `juniper-cascor-client` package alongside minimum-viable, or does it need its own PR? Suggest: bundle with Phase A-server PR.
- **Q5-R1-01**: minimum-viable proposes shipping the R0-06 §6.4 "WebSocket health" Prometheus dashboard panel in Phase B. Does canopy already export Prometheus metrics at all? If not, minimum-viable needs to add `prometheus_client` as a dependency — ~0.1 day.

### 10.7 What this self-audit did NOT do

- Did not run any tests (this is a proposal).
- Did not verify that the cited line numbers (`dashboard_manager.py:1490-1526`, `metrics_panel.py:648-670`, `control_stream.py:97-100`) are still accurate on current `origin/main` — relied on R0-01/R0-02 which cited them.
- Did not read the canopy or cascor source directly — relied on the 6 R0 proposals and the source doc §7 gap list.
- Did not measure the actual current `/api/metrics/history` bandwidth in production (the 3 MB/s figure is from the source doc §1.1).

### 10.8 Final posture

The minimum-viable scope is:
- **7 engineering days** end-to-end.
- **Phase A-server** + **minimum Phase B-pre (M-SEC-01/01b/03/04 only)** + **Phase B frontend (minus rAF, minus uncapped reconnect, minus full cleanup)** + **minimum test suite (15 test files, ~100 new test cases)** + **Phase I cache busting** + **one kill-switch flag** + **one proof-of-win metric**.
- Deferrals are all explicit, cited, and safety-justified.
- Deferrals all land naturally in a v1.1 proposal that should consolidate Phase C + Phase D + full Phase B-pre.

**Recommended Round 2 consolidation treatment**: this proposal is the "narrow and safe" pole of the R1 quintet. Round 2 agents should use it as the lower bound on scope and judge the other R1 proposals against it for scope creep. A Round 2 proposal that exceeds this scope should have an explicit justification for each addition.

---

## 11. Appendix: cross-reference tables

### 11.1 M-SEC controls in minimum-viable scope

| M-SEC ID | In minimum Phase B-pre? | Deferred to | Rationale |
|---|---|---|---|
| M-SEC-01 (canopy Origin) | **yes** | — | Exfiltration prevention on `/ws/training` |
| M-SEC-01b (cascor Origin parity) | **yes** | — | Same; parity with canopy |
| M-SEC-02 (cookie+CSRF) | no | Phase D / v1.1 | Only matters when `/ws/control` is consumed |
| M-SEC-03 (per-frame size cap) | **yes** | — | DoS guard; hard Phase B prereq |
| M-SEC-04 (per-IP cap) | **yes** (partial) | auth-timeout deferred | Connection flood protection |
| M-SEC-05 (command rate limit) | no | Phase D / v1.1 | Commands deferred |
| M-SEC-06 (opaque close reasons) | no | Phase D / v1.1 | Only matters with auth failures |
| M-SEC-07 (audit log scrub) | no | Phase D / v1.1 | Audit logger deferred |
| M-SEC-10 (idle timeout) | no | v1.1 | Nice-to-have |
| M-SEC-11 (adapter inbound validation) | no | v1.2 | Correctness, not security |
| M-SEC-12 (log injection escaping) | no | v1.1 with audit logger | Requires audit logger |

### 11.2 GAP-WS items in minimum-viable scope

| GAP-WS ID | Severity | In minimum? | Phase |
|---|---|---|---|
| GAP-WS-01 (SDK set_params) | P1 | no | v1.1 Phase A |
| GAP-WS-02 (integrate cascorWS) | P1 | yes | B |
| GAP-WS-03 (delete parallel client) | P2 | yes | B |
| GAP-WS-04 (init ws-metrics-buffer) | P1 | yes | B |
| GAP-WS-05 (drain callbacks) | P1 | yes | B |
| GAP-WS-07 (backpressure) | P1 | quick-fix only | A-server |
| GAP-WS-09 (cascor set_params integration test) | P1 | no | v1.1 Phase G |
| GAP-WS-10 (canopy set_params integration test) | P1 | no | v1.1 Phase C |
| GAP-WS-11 (normalize_metric dual format) | P1 | regression gate only | B (via MVS-TEST-14) |
| GAP-WS-12 (heartbeat) | P1 | no (framework-level only) | v1.1 Phase F |
| GAP-WS-13 (replay buffer + seq) | P1 | yes | A-server |
| GAP-WS-14 (extendTraces) | P1 | yes | B |
| GAP-WS-15 (rAF coalescing) | P1 | scaffold only, unwired | v1.2 |
| GAP-WS-16 (polling elimination) | **P0** | **yes — the goal** | B |
| GAP-WS-17 (permessage-deflate) | P2 | no | v1.2 |
| GAP-WS-18 (topology chunking) | P2 | no (REST fallback) | v1.2 |
| GAP-WS-19 (close_all lock) | P2 | already fixed | — |
| GAP-WS-20 (envelope asymmetry) | P3 | no | v1.2+ |
| GAP-WS-21 (state coalescer) | P1 | yes | A-server |
| GAP-WS-22 (protocol error responses) | P2 | minimal | A-server |
| GAP-WS-23 (canopy cascor_service_adapter cleanup) | P3 | no | v1.2 |
| GAP-WS-24 (latency instrumentation) | P2 | yes, minimal | B |
| GAP-WS-25 (polling toggle) | P1 | yes | B |
| GAP-WS-26 (connection indicator) | P1 | yes | B |
| GAP-WS-27 (per-IP cap) | P1 | yes | B-pre |
| GAP-WS-28 (training_lock coverage) | P3 | no | v1.2 |
| GAP-WS-29 (broadcast_from_thread exception) | P2 | yes | A-server |
| GAP-WS-30 (reconnect jitter) | P3 | yes | B (folded from F) |
| GAP-WS-31 (uncapped reconnect) | P2 | no | v1.1 Phase F |
| GAP-WS-32 (per-command timeouts + correlation) | P2 | no | v1.1 Phase C |
| GAP-WS-33 (demo mode failure visibility) | P2 | yes | B |

### 11.3 RISK items in minimum-viable scope

See §7 table above.

### 11.4 R0 proposal file index

| R0 | Topic | Used in | Primary contribution |
|---|---|---|---|
| R0-01 | Frontend performance | §2.3, §2.4, §4.3, §9.2 | Phase B wiring, extendTraces, drain pattern |
| R0-02 | Security hardening | §2.2, §3.5, §4.1, §4.2, §4.5 | Phase B-pre control catalog |
| R0-03 | Cascor backend | §2.1, §4.4, §4.7, §5 Day 1-2 | Phase A-server commit chain |
| R0-04 | SDK set_params | §3.1 | Phase C deferral justification |
| R0-05 | Testing validation | §2.4 | Test plan subset |
| R0-06 | Ops phasing risk | §2.2, §2.5, §3, §4.1, §4.2, §7 | Phase gating, risk register, rollout |

---

**End of R1-01**
