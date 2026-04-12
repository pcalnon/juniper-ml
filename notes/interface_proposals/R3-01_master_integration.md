# Round 3 Proposal R3-01: Master Integration Development Plan

**Angle**: Comprehensive integration of all R2 angles (best-of, contracts, CCCs, decisions)
**Author**: Round 3 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 3 consolidation — input to Round 4
**Inputs consolidated**: R2-01 (best-of synthesis), R2-02 (phase execution contracts), R2-03 (cross-cutting concerns), R2-04 (decision matrix + stakeholder briefing)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE

---

## 0. If you only read one section, read this

**What we're doing**: replacing the ~3 MB/s per-dashboard `/api/metrics/history` REST polling bomb (GAP-WS-16, P0) with an already-half-wired cascor → canopy → browser WebSocket pipeline. Piggybacked: four cascor correctness bugs (GAP-WS-07, GAP-WS-21, GAP-WS-29, GAP-WS-32) and the CSWSH defense gap (RISK-15).

**P0 outcome**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` drops ≥90% vs pre-Phase-B baseline in staging, sustained for 72 h. One gauge is the whole migration's acceptance signal.

**Top 3 decisions that gate everything else**:

1. **`command_id` (not `request_id`)** for `/ws/control` correlation, applied across SDK, cascor, canopy, tests. **R2-04 D-02 recommended default; applied.** Without this, Phase G integration test fails 2-3 weeks after Phase A ships.
2. **Phase 0-cascor carve-out** from Phase B. The cascor seq/replay/server_instance_id work ships as its own ~2-day PR before canopy Phase B begins, giving cascor main a ~1-week additive-field soak (validated by `juniper-cascor-worker` CI). **R2-04 D-11; applied.**
3. **Phase B ships behind two feature flags** — `enable_browser_ws_bridge: bool = False` (dev flag, flips True after 72 h staging soak via a separate 1-line PR) and `disable_ws_bridge: bool = False` (permanent ops kill switch). Runtime gate: `enabled = enable_browser_ws_bridge and not disable_ws_bridge`. **R2-04 D-17 + D-18; R1-05 §4.45 two-flag design; applied.**

**Effort**: 13.5 engineering days expected / ~4.5 weeks calendar with 48-72 h soak windows. R2-01 center-of-mass; R2-02 pessimistic 19 days. Minimum-viable carveout (P0 only): ~7 days (R1-01 escape hatch, retained for calendar emergencies).

**Canonical phase order**: Phase A (SDK, parallel) + Phase 0-cascor (cascor prereqs, parallel) → Phase B-pre-a (read-path security) → Phase B (browser bridge, polling elimination) → Phase B-pre-b (control-path security, parallel with B) → Phase C (set_params, flag-off) → Phase D (control buttons, gated on B-pre-b in prod ≥48 h) → Phase E (backpressure full, conditional on telemetry) → Phase F (heartbeat + jitter) → Phase G (cascor set_params integration tests) → Phase H (normalize_metric regression gate) → Phase I (asset cache busting, folded into Phase B).

**Recommended path**: take R1-05 + R2-04's reconciled defaults as the decision set, take R2-01's provenance as the feature scope, take R2-02's six-question contracts as the execution shape, weave R2-03's 10 CCCs into every phase. Critical-path subset for P0 win alone: Phase A-SDK, Phase 0-cascor, Phase B-pre-a, Phase B (with Phase I folded in).

**Rollback story**: every phase has a config-only kill switch (master matrix in §14) with MTTR ≤5 min. REST paths stay alive forever (R1-02 principle 7, R2-04 D-21, D-54). If a kill switch fails to produce its expected metric delta within 60 s, the migration halts for re-planning (R1-02 abandon trigger).

---

## 1. Goal and scope

### 1.1 Primary goal

Eliminate `/api/metrics/history` REST polling from the canopy dashboard when WebSocket is healthy, reducing per-dashboard bandwidth by ≥90% sustained in production. This is the only P0 item in the WebSocket migration.

### 1.2 Secondary goals

1. Fix GAP-WS-21 lifecycle state coalescer drop-filter bug (silently loses terminal state transitions).
2. Fix GAP-WS-29 `broadcast_from_thread` silent exception swallowing.
3. Mitigate GAP-WS-07 slow-client fan-out blocking via `_send_json` 0.5 s timeout (quick-fix) and eventual Phase E per-client pump tasks (full fix).
4. Close RISK-15 (CSWSH attack on `/ws/training` and `/ws/control`) via M-SEC-01/01b Origin allowlist, M-SEC-02 cookie+CSRF, M-SEC-05 rate limit, M-SEC-11 adapter inbound validation.
5. Add the `command_id`-based `set_params` WebSocket path (P2, feature-flagged default OFF) as scaffolding for v1.1 flip decision.
6. Add observability that is load-bearing for the acceptance gate and the SLO binding after ≥1 week of production data.
7. Preserve REST endpoints forever as the fallback kill switch (no deletions, ever).

### 1.3 Explicit non-goals (out of scope for this migration)

- REST endpoint deletion. Preserved forever per R1-02 principle 7 / R2-04 D-21/D-54 / R2-03 CCC-08. "No deprecation ever" as explicit source-doc patch.
- Multi-tenant replay isolation (R2-04 D-32; defer per R1-05 §4.13).
- Per-command HMAC (R2-04 D-31; R1-05 §4.11 defer indefinitely).
- Two-bucket rate limit (R2-04 D-33; single bucket per R1-05 §4.46; split only if starvation observed).
- `permessage-deflate` negotiation (GAP-WS-17; deferred per R1-03 §20.1).
- Topology chunking (GAP-WS-18; REST fallback preserved).
- WebAssembly Plotly (out of scope per R0-01 §8.4).
- Multi-browser matrix (R2-04 D-44; Chromium-only v1 per R1-05 §4.31).
- User research study (R2-04 D-45; R1-05 §4.32 skip).
- OAuth/OIDC, mTLS canopy↔cascor, shadow traffic (R2-04 D-26; R1-05 §4.39 rejected).
- rAF coalescer in-production (R2-04 D-04; scaffolded disabled per unanimous R1 agreement).
- NetworkVisualizer deep render migration (R2-04 D-06; minimum wire in Phase B, deep deferred to B+1 contingent on render tech).

### 1.4 Phase map

Canonical phase order with dependencies:

```
Phase A-SDK (parallel) ──┐
                         │
Phase 0-cascor ──────────┼──> Phase B-pre-a ──> Phase B ──> (P0 win)
                         │                          │
Phase B-pre-a ───────────┘                          │
                                                    │
Phase B-pre-b (parallel with B) ────> Phase D ──────┤
                                                    │
                                    Phase C (flag-off, parallel) ──> Phase D
                                                    │
                                                    ├──> Phase E (optional, telemetry-triggered)
                                                    ├──> Phase F (bundled with B; heartbeat follow-on)
                                                    ├──> Phase G (cascor integration tests, bundled with 0-cascor)
                                                    └──> Phase H (normalize_metric regression)

Phase I asset cache busting ──> folded into Phase B PR
```

Parallel lanes:
- **Phase A-SDK** runs in parallel with Phase 0-cascor and Phase B-pre-a.
- **Phase 0-cascor** and **Phase B-pre-a** run in parallel.
- **Phase B-pre-b** runs in parallel with **Phase B** (pre-b gates Phase D, not Phase B).
- **Phase C** runs in parallel with **Phase D** once B and B-pre-b are in production.
- **Phase E/F/G/H** are independent follow-ups after B is in production.

---

## 2. Source-of-truth applied positions

This section enumerates every settled decision — R1-05 resolutions, R2-04 recommended defaults applied, and the handful of R2-cross disagreements this R3 master plan resolves. Round 4 and later rounds MUST treat these as binding.

### 2.1 Wire-format applied positions

| Item | Applied value | Source |
|---|---|---|
| Correlation field name on `/ws/control` | **`command_id`** (NOT `request_id`) | R1-05 §4.2, R2-04 D-02, R2-03 CCC-01 rename mandate |
| `command_response` on `/ws/control` carries `seq` | **No** (separate seq namespaces) | R1-05 §4.17, R2-04 D-03, R2-03 CCC-01 |
| Replay buffer applies to | **`/ws/training` only** | R1-05 §4.17 |
| `server_instance_id` role | **programmatic comparison key** | R1-05 §4.20, R2-04 D-15 |
| `server_start_time` role | **advisory, human-readable only** | R1-05 §4.20 |
| `replay_buffer_capacity` field on `connection_established` | **present, additive** | R1-05 §4.21, R2-04 D-16 |
| `emitted_at_monotonic` field | **present on every `/ws/training` broadcast envelope** | R2-03 CCC-10, R1-05 §4.8 |
| Two-phase registration mechanism | **`_pending_connections` set + `promote_to_active()`** | R1-05 §4.18, R2-04 D-14 |
| Schema version field in this migration | **NOT added** (additive-only contract) | R2-03 CCC-01 item 6 |
| Unknown commands on `/ws/control` | **error response** (not close) | R1-05 §4.17 |
| Malformed JSON | **close 1003** | R1-03 §5.10 |
| Cascor `/ws/control` Pydantic validation | **`extra="forbid"`** on `SetParamsRequest` | R1-05 §4.44, R2-04 D-34 |

### 2.2 Protocol behavior applied positions

| Item | Applied value | Source |
|---|---|---|
| `set_params` default timeout | **1.0 s** (NOT 5.0 s) | R1-05 §4.1, R2-04 D-01, source doc §7.32 line 1403 |
| SDK retries on timeout | **None** (fail-fast, caller decides) | R1-05 §4.22, §4.42, R2-04 D-20 |
| SDK reconnect queue | **None** (fail-fast per R1-05 §4.42) | R2-04 D-20, R2-02 §4 |
| Slider debounce layer | **Dash clientside callback**, NOT SDK | R1-05 §4.24, R2-04 D-22 |
| Unclassified `set_params` keys (adapter) | **REST fallback with WARNING log** | R1-05 §4.44, R2-04 D-34 |
| REST path deprecation | **None, ever** (backwards compatibility forever) | R1-02 principle 7, R1-05 §4.23, R2-04 D-21/D-54, R2-03 CCC-08 |
| Origin wildcard `*` in `ws_allowed_origins` | **REFUSED by parser** (non-switch) | R1-02 §4.3, R2-04 D-10 |
| "One resume per connection" rule | **enforced** | R1-05 §4.12, R2-04 D-30 |
| Replay buffer default size | **1024, configurable** via `JUNIPER_WS_REPLAY_BUFFER_SIZE` | R1-05 §6.1, R2-04 D-35 **(R2-01 and R2-02 both picked 1024; R2-03 uses 256 in its CCC-07 table — this is an R2-cross disagreement; resolution in §20)** |
| Replay buffer size env override as kill switch | **`JUNIPER_WS_REPLAY_BUFFER_SIZE=0` disables replay** | R1-02 §3.3, R2-04 D-36 |
| Phase E backpressure default | **`drop_oldest_progress_only`** (overrides source doc `block`) | R1-05 §4.36, R2-04 D-19, R2-01 §10 |
| rAF coalescer | **scaffolded, disabled** via `enable_raf_coalescer=False` | R1-05 §4.3, R2-04 D-04 |
| REST polling fallback cadence during disconnect | **1 Hz** (NOT 100 ms) | R1-05 §4.4, R2-04 D-05 |
| `ws-metrics-buffer` Dash store shape | **`{events: [...], gen: int, last_drain_ms: float}`** structured object | R1-05 §4.7, R2-04 D-07 |
| GAP-WS-24 (latency instrumentation) ownership | **Split 24a (browser emitter) + 24b (canopy backend)**, both in Phase B | R1-05 §4.8, R2-04 D-08 |
| NetworkVisualizer in Phase B | **minimum WS wiring**; deep render migration deferred to Phase B+1 contingent on render tech verification in first commit | R1-05 §4.5, R2-04 D-06 |
| Uncapped reconnect attempts (GAP-WS-31) | **cap lifted in Phase B**, max interval 30-60 s | R1-03 §8.5, R2-01 §6 (overrides R1-01) |
| Reconnect backoff jitter (GAP-WS-30) | **present in Phase B** `websocket_client.js` | R1-05 §6.2, R2-01 §6 |

### 2.3 Security applied positions

| Item | Applied value | Source |
|---|---|---|
| GAP-WS-19 (`close_all` lock) | **RESOLVED on main**; regression test only | R1-05 §4.16, R2-04 D-13 |
| Phase B-pre split | **B-pre-a (read-path) + B-pre-b (control-path)** | R1-05 §4.35, R2-04 D-23 |
| Origin on `/ws/training` | **lands in B-pre-a** (live-data exfiltration vector) | R2-01 §5 (overrides R1-05 §4.35 placement) |
| Origin on `/ws/control` | **lands in B-pre-b** (tied to CSRF flow) | R1-05 §4.35 |
| Security flag naming | **positive-sense `ws_security_enabled: bool = True`** (NOT negative `disable_ws_auth`) with CI guardrail refusing production compose files containing `ws_security_enabled=false` | R1-02 §12.5, R1-03 §18.6, R2-01 §18.2, R2-03 §15.3, R2-04 D-10 — **overrides R1-05 §4.10 and R2-02 §1.2 which kept negative sense; this is an R2-cross disagreement; resolution in §20** |
| Per-IP connection cap default | **5** | R1-05 §4.37, R2-04 D-24 |
| Idle timeout (M-SEC-10) | **120 s bidirectional** | R1-05 §4.15, R2-01 §5 |
| Adapter synthetic auth | **HMAC-derived CSRF token** (`hmac(api_key, "adapter-ws", sha256).hexdigest()`), NOT `X-Juniper-Role` header-skip | R1-05 §4.43, R2-04 D-29, R2-01 §7, R2-02 §7 |
| Per-command HMAC | **deferred indefinitely** | R1-05 §4.11, R2-04 D-31 |
| Rate limit | **single bucket, 10 cmd/s per connection** | R1-05 §4.46, R2-04 D-33 |
| Multi-tenant replay isolation | **deferred** | R1-05 §4.13, R2-04 D-32 |
| Audit logger | **dedicated `canopy.audit` logger** with JSON formatter + `TimedRotatingFileHandler` + scrub allowlist; **skeleton in B-pre-a, Prometheus counters in B** | R1-05 §4.14, R2-04 D-28, R2-01 §5, R2-03 §15.4 |
| M-SEC identifier adoption | **adopt M-SEC-10 (idle timeout) and M-SEC-11 (adapter inbound validation); fold M-SEC-12 (log injection) into M-SEC-07** | R1-05 §4.15, R2-04 D-12 |
| Per-origin handshake cooldown | **ship in Phase B-pre-b**, cooldown list cleared on canopy restart (NAT hostile escape hatch) | R1-02 §13.10, R1-03 §6.2.7 |
| Deployment topology | **single-tenant v1** | R1-05 §4.38, R2-04 D-25 |
| Shadow traffic | **rejected** | R1-05 §4.39, R2-04 D-26 |

### 2.4 Observability applied positions

| Item | Applied value | Source |
|---|---|---|
| "Metric before behavior" rule | **operationally binding** — no behavior change ships without its guarding metric + alert + test-fired once in staging | R1-02 §1.2 principle 1, R2-03 CCC-02 |
| `WSSeqCurrentStalled` alert | **page severity** (broadcast loop hang detector) | R1-02 §2.4, R2-04 D-52 |
| `WSOriginRejection` alert | **page severity** (CSWSH canary) | R1-02 §2.4, R2-04 D-51 |
| `WSStateDropped` alert | **page severity** (state-bearing event loss) | R1-02 §2.4, R2-03 CCC-02 |
| `WSOversizedFrame` alert | **page severity** (DoS canary) | R1-02 §2.4, R2-03 CCC-02 |
| `canopy_ws_browser_js_errors_total` counter | **mandatory** in Phase B | R1-02 §2.2, R2-01 §6.4, R2-03 CCC-02 |
| `canopy_ws_drain_callback_gen` gauge | **mandatory** in Phase B (stuck drain detector) | R1-02 §2.2, R2-01 §6.4, R2-03 CCC-02 |
| `canopy_ws_backend_relay_latency_ms` | **separate hop histogram** (cascor→canopy) | R1-02 §2.2, R2-03 CCC-10 |
| Metrics-presence CI test | **enforced blocker** (scrape `/metrics`, assert every required metric present) | R1-02 §10.6, R2-04 D-37 |
| P0 acceptance metric | **`canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`** ≥90% reduction sustained | R1-01 §2.5.1, R1-02 §2.2, R1-04 §15.4 |
| SLO binding | **after ≥1 week of production data** — separate promotion PR | R1-03 §16.5, R2-03 CCC-10 |
| Latency histogram buckets | **`{50, 100, 200, 500, 1000, 2000, 5000}` ms** | R1-03 §16.5 step 6, R2-03 CCC-10 |
| Latency beacon cadence | **60 s** (browser → canopy) | R1-03 §16.5 step 7 |
| CI latency policy | **recording-only** (`latency_recording` marker); strict is local-only | R1-05 §4.28, R2-04 D-42 |
| Clock offset recomputation | **on every reconnect** (laptop-sleep resilience) | R1-03 §16.5 step 5, R2-03 CCC-10 |
| Error-budget burn-rate freeze rule | **operationally binding** (if 99.9% budget burns in <1 day, freeze non-reliability work) | R1-02 §2.4, R2-04 D-50 |

### 2.5 Testing applied positions

| Item | Applied value | Source |
|---|---|---|
| `contract` pytest marker | **added** in all three repos (cascor, canopy, cascor-client); runs every PR | R1-05 §4.34, R2-04 D-43, R2-03 CCC-05 |
| Chaos tests | **nightly lane**; elevated to blocking for **replay race, broadcast_from_thread, broadcaster chaos** in Phase 0-cascor | R1-02 §10.1, R2-01 §18.9, R2-04 D-40 |
| Load tests | **blocking gate** for Phase 0-cascor (100 Hz × 60 s × 10 clients, p95 < 250 ms) | R1-02 §10.3, R2-04 D-41 |
| Frame-budget test | **recording-only** (CI runner variance) | R1-03 §19.3, R2-04 D-42 |
| Multi-browser matrix | **Chromium-only** in CI | R1-05 §4.31, R2-04 D-44 |
| User research study | **optional, skipped for v1** | R1-05 §4.32, R2-04 D-45 |
| Latency tests | **recording-only** in CI | R1-05 §4.28, R2-04 D-42 |
| `test_fake_cascor_message_schema_parity` contract test | **mandatory** | R1-05 §4.30, R2-03 CCC-05 |
| `test_set_params_caller_cancellation_cleans_correlation_map` | **mandatory Phase A gate** | R1-05 §4.25, R2-02 §4 |
| CODEOWNERS rule on `_normalize_metric` | **hard merge gate** | R1-02 §7.5, R1-05 §4.41, R2-04 D-27 |
| Pre-commit hook refusing nested-format-key removal | **installed in Phase H** | R1-02 §7.5, R2-01 §13 |

### 2.6 Effort and calendar applied positions

| Item | Applied value | Source |
|---|---|---|
| Total effort expected | **13.5 engineering days** / ~4.5 weeks calendar | R1-05 §4.40, R2-04 §1.3 |
| Minimum-viable carveout | **~7 days** (Phase A-SDK + Phase 0-cascor + Phase B-pre-a minimum + Phase B + Phase I) — escape hatch only | R1-01 §1.2 |
| R2-02 pessimistic upper bound | **19-22 days** if all contingencies hit | R2-02 §17 |
| Phase 0-cascor staging soak | **72 h** (R1-02 §3.4 amplification; latent seq monotonicity bugs) — **R2-02 argued 24 h; this plan sides with R1-02/R2-01/R2-04 at 72 h; resolution in §20** | R1-02 §3.4, R2-04 D-38 |
| Phase B staging soak | **72 h** (RISK-10 browser memory leak guard) | R1-02 §5.7, R2-04 D-39 |
| Phase B-pre-b staging soak | **48 h** (auth-path critical mass) | R1-02 §4.2, R2-01 §7 |
| Phase D entry gate | **Phase B-pre-b in production ≥48 h** | R1-02 §7.1, R2-02 §18.8, R2-04 §1.3 |
| Phase C flag-flip canary | **≥7 days production data** with 6 enumerated hard gates | R1-02 §6.1, R2-04 D-48 |
| Mid-week deploys for behavior-changing flag flips | **required** | R1-02 §5.7, R2-04 D-61 |

### 2.7 Scope applied positions (phase carve-outs)

| Item | Applied value | Source |
|---|---|---|
| Phase 0-cascor (aka Phase A-server) | **canonical name `Phase 0-cascor`**; carve out from Phase B | R1-05 §4.19, R2-04 D-11 |
| Phase B-pre-a | **read-path security gate**, gates Phase B | R1-05 §4.35, R2-04 D-23 |
| Phase B-pre-b | **control-path security gate**, gates Phase D (NOT B) | R1-05 §4.35, R2-04 D-23 |
| Phase C | **P2 (not P1)** — ships in main wave behind `use_websocket_set_params=False` flag | R0-04 §3, R2-01 §18.5, R2-04 D-47 |
| Phase D | **blocked on B-pre-b in production ≥48 h** | R2-02 §18.8, R2-04 §1.3 |
| Phase E | **ships conditionally** on telemetry showing RISK-04/11 triggering; 0.5 s quick-fix from Phase 0-cascor suffices otherwise | R1-04 §12.3, R2-01 §10 |
| Phase F | **jitter ships with Phase B**; heartbeat ping/pong ships as Phase F proper | R2-01 §11, R2-02 §11 |
| Phase G | **ships bundled with Phase 0-cascor** | R2-01 §12, R2-02 §12 |
| Phase H | **test-only + CODEOWNERS + pre-commit hook**; NO refactoring of `_normalize_metric` in this migration | R1-02 §7.5, R2-01 §13, R2-02 §13, R2-04 D-27 |
| Phase I | **folded into Phase B** (asset cache busting commit) | R1-05 §6.2, R2-01 §6, R2-02 §14 |

### 2.8 Feature flag inventory (applied)

| Flag | Phase | Initial default | Final default | Removal? |
|---|---|---|---|---|
| `enable_browser_ws_bridge` | B | `False` | `True` (post-staging) | Post-flip, single-version deprecation (v1.1) |
| `disable_ws_bridge` | B | `False` | `False` permanent | Never |
| `enable_raf_coalescer` | B | `False` | depends on §5.6 data | Post-B+1 if data warrants |
| `use_websocket_set_params` | C | `False` | `True` (post-canary ≥7 days) | Post-flip deprecation (v1.1) |
| `enable_ws_control_buttons` | D | `False` | `True` (post-canary) | Post-flip deprecation (v1.1) |
| `ws_security_enabled` | B-pre-b | `True` | `True` permanent (CI refuses False in prod) | Never |
| `disable_ws_control_endpoint` | B-pre-b | `False` | `False` permanent | Never |
| `ws_rate_limit_enabled` | B-pre-b | `True` | `True` permanent | Never |
| `audit_log_enabled` | B-pre-a | `True` | `True` permanent | Never |
| `ws_backpressure_policy` | E | `drop_oldest_progress_only` | `drop_oldest_progress_only` | Permanent config (enum value) |
| `disable_ws_auto_reconnect` | F | `False` | `False` permanent | Never |

### 2.9 Configuration / Settings canonical table (applied)

| Setting | Repo | Type | Default | Env var | Phase | Validation |
|---|---|---|---|---|---|---|
| `ws_replay_buffer_size` | cascor | int | 1024 | `JUNIPER_WS_REPLAY_BUFFER_SIZE` | 0-cascor | `>=0` (0 disables replay) |
| `ws_send_timeout_seconds` | cascor | float | 0.5 | `JUNIPER_WS_SEND_TIMEOUT_SECONDS` | 0-cascor | `>0` |
| `ws_state_throttle_coalesce_ms` | cascor | int | 1000 | `JUNIPER_WS_STATE_THROTTLE_COALESCE_MS` | 0-cascor | `>0` |
| `ws_resume_handshake_timeout_s` | cascor | float | 5.0 | `JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S` | 0-cascor | `>0` |
| `ws_pending_max_duration_s` | cascor | float | 10.0 | `JUNIPER_WS_PENDING_MAX_DURATION_S` | 0-cascor | `>0` |
| `ws_max_connections` | cascor | int | 50 | `JUNIPER_WS_MAX_CONNECTIONS` | existing | `>=1` |
| `ws_max_connections_per_ip` | cascor | int | 5 | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a | `>=1` |
| `ws_allowed_origins` | cascor | list[str] | `[]` (fail-closed) | `JUNIPER_WS_ALLOWED_ORIGINS` | B-pre-a (training) + B-pre-b (control) | no `*` |
| `ws_security_enabled` | canopy | bool | `True` | `JUNIPER_WS_SECURITY_ENABLED` | B-pre-b | bool; CI refuses `false` in prod compose |
| `ws_max_connections_per_ip` | canopy | int | 5 | `JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP` | B-pre-a | `>=1` |
| `ws_allowed_origins` | canopy | list[str] | localhost/127.0.0.1 × http/https | `JUNIPER_CANOPY_WS_ALLOWED_ORIGINS` | B-pre-a | no `*` |
| `ws_rate_limit_enabled` | canopy | bool | `True` | `JUNIPER_WS_RATE_LIMIT_ENABLED` | B-pre-b | bool |
| `ws_rate_limit_cps` | canopy | int | 10 | `JUNIPER_WS_RATE_LIMIT_CPS` | B-pre-b | `>=1` |
| `ws_idle_timeout_seconds` | canopy | int | 120 | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS` | B-pre-a | `>=1` |
| `audit_log_enabled` | canopy | bool | `True` | `JUNIPER_AUDIT_LOG_ENABLED` | B-pre-a | bool |
| `audit_log_path` | canopy | str | `/var/log/canopy/audit.log` (prod) | `JUNIPER_AUDIT_LOG_PATH` | B-pre-a | path |
| `audit_log_retention_days` | canopy | int | 90 | `JUNIPER_AUDIT_LOG_RETENTION_DAYS` | B-pre-a | `>=1` |
| `disable_ws_control_endpoint` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT` | B-pre-b | bool |
| `enable_browser_ws_bridge` | canopy | bool | `False` (→ True post-soak) | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE` | B | bool |
| `disable_ws_bridge` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_BRIDGE` | B | bool |
| `enable_raf_coalescer` | canopy | bool | `False` | `JUNIPER_ENABLE_RAF_COALESCER` | B | bool |
| `enable_ws_latency_beacon` | canopy | bool | `True` | `JUNIPER_ENABLE_WS_LATENCY_BEACON` | B | bool |
| `use_websocket_set_params` | canopy | bool | `False` | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS` | C | bool |
| `ws_set_params_timeout` | canopy | float | 1.0 | `JUNIPER_WS_SET_PARAMS_TIMEOUT` | C | `>0` |
| `enable_ws_control_buttons` | canopy | bool | `False` | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS` | D | bool |
| `ws_backpressure_policy` | cascor | Literal | `drop_oldest_progress_only` | `JUNIPER_WS_BACKPRESSURE_POLICY` | E | enum `{block, drop_oldest_progress_only, close_slow}` |
| `disable_ws_auto_reconnect` | canopy | bool | `False` | `JUNIPER_DISABLE_WS_AUTO_RECONNECT` | F | bool |

Every setting has a `Field(..., description=...)` Pydantic docstring; CI asserts every setting is documented and every env var round-trips (R2-03 CCC-07 item 8).

---

## 3. Phase 0-cascor: SDK + cascor server prerequisites

**Note on naming**: this section covers two parallel phases that share a dependency cluster — **Phase 0-cascor** (cascor-server prerequisites) and **Phase A-SDK** (juniper-cascor-client `set_params` method). Both have no cross-dependency and can run concurrently from day 1; they are described in 3.x (Phase 0-cascor proper) and 3.SDK subsections.

### 3.1 Goal

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope, advertises `server_instance_id` + `server_start_time` + `replay_buffer_capacity` + `emitted_at_monotonic` on `connection_established` (and every subsequent broadcast for `emitted_at_monotonic`), supports a 1024-entry replay buffer with a `resume` handler, exposes `snapshot_seq` atomically on the REST `/api/v1/training/status` endpoint, no longer stalls fan-out on a single slow client (0.5 s `_send_json` quick-fix), fixes GAP-WS-21 state coalescer drop-filter, fixes GAP-WS-29 `broadcast_from_thread` silent exception swallowing, and returns protocol-error responses on unknown commands / malformed JSON on `/ws/control`. The `/ws/control` endpoint gains `command_id` echo but **no `seq` field** (R1-05 §4.17 canonical position). The phase is purely additive — existing clients that ignore new fields keep working.

The parallel Phase A-SDK adds `CascorControlStream.set_params(params, *, timeout=1.0, command_id=None)` to `juniper-cascor-client` with per-request `command_id` correlation, caller-cancellation safety, fail-fast behavior on disconnect (no reconnect queue), and no retry logic (caller decides).

### 3.2 Entry gate

- [ ] `juniper-cascor` main branch clean; baseline test suite green (`cd juniper-cascor/src/tests && bash scripts/run_tests.bash`).
- [ ] `juniper-cascor-client` main branch clean; baseline test suite green.
- [ ] GAP-WS-19 state verified: `grep -n "close_all" juniper-cascor/src/api/websocket/manager.py` confirms lock-holding pattern matches R0-03 §11.1 (R1-05 §4.16, R2-04 D-13).
- [ ] No other concurrent cascor PR touching `websocket/*.py`, `lifecycle/manager.py`, `messages.py`.
- [ ] Prometheus namespace collision check: `cascor_ws_seq_current`, `cascor_ws_replay_buffer_occupancy`, `cascor_ws_replay_buffer_bytes`, `cascor_ws_replay_buffer_capacity_configured`, `cascor_ws_resume_requests_total`, `cascor_ws_resume_replayed_events`, `cascor_ws_broadcast_send_duration_seconds`, `cascor_ws_broadcast_timeout_total`, `cascor_ws_pending_connections`, `cascor_ws_state_throttle_coalesced_total`, `cascor_ws_broadcast_from_thread_errors_total`, `cascor_ws_seq_gap_detected_total`, `cascor_ws_connections_active`, `cascor_ws_command_responses_total`, `cascor_ws_command_handler_seconds` — all reserved, no name collisions with existing metric registry.
- [ ] `juniper-cascor-worker` CI green against current cascor main (baseline for post-phase soak).
- [ ] R2-04 decisions D-03, D-11, D-14, D-15, D-16, D-25, D-30, D-35, D-36, D-38, D-41, D-46, D-52 all resolved per §2 applied positions.

### 3.3 Deliverables

#### 3.3.1 Functional (cascor-server, 10 commits)

The commit chain from R1-03 §5.11 / R1-04 Days 2-3, applied to canonical file paths:

| Commit | Intent | File(s) |
|---|---|---|
| 0-cascor-1 | `messages.py` optional `seq: Optional[int] = None` + `emitted_at_monotonic: float` on every envelope builder | `juniper-cascor/src/api/websocket/messages.py` |
| 0-cascor-2a | `WebSocketManager` gains `server_instance_id: str = str(uuid.uuid4())`, `server_start_time: float = time.time()`, `_next_seq: int`, `_seq_lock: asyncio.Lock`, `_replay_buffer: deque[tuple[int, dict]]` with `maxlen=Settings.ws_replay_buffer_size`, `_assign_seq_and_append()` helper | `juniper-cascor/src/api/websocket/manager.py` |
| 0-cascor-2b | `connect()` sends `connection_established` containing `server_instance_id`, `server_start_time`, `replay_buffer_capacity` | same |
| 0-cascor-3 | `_send_json()` wraps `ws.send_json(msg)` in `asyncio.wait_for(..., timeout=Settings.ws_send_timeout_seconds)` with exception logging (GAP-WS-07 quick-fix) | same |
| 0-cascor-4 | `replay_since(last_seq: int) -> list[dict]` helper + `ReplayOutOfRange` exception class; copy-under-lock pattern | same |
| 0-cascor-5a | `training_stream.py` adds `_pending_connections: set[WebSocket]`, `connect_pending()`, `promote_to_active()` (two-phase registration) | `juniper-cascor/src/api/websocket/training_stream.py` |
| 0-cascor-5b | `/ws/training` handler dispatches `resume` frame (5 s frame timeout) → `resume_ok` (replays events since `last_seq`) or `resume_failed` (out_of_range / server_restarted), then promotes to active. Server restart detected via `server_instance_id` mismatch. "One resume per connection" rule via `resume_consumed: bool`. | same |
| 0-cascor-6 | `/api/v1/training/status` REST endpoint adds `snapshot_seq` and `server_instance_id` fields, read atomically under `_seq_lock` | `juniper-cascor/src/api/training/router.py` |
| 0-cascor-7 | `lifecycle/manager.py:133-136` — replace 1 Hz drop-filter with debounced coalescer; terminal transitions (`Completed`, `Failed`, `Stopped`) bypass throttle (GAP-WS-21) | `juniper-cascor/src/lifecycle/manager.py` |
| 0-cascor-8 | `broadcast_from_thread` attaches `asyncio.Task.add_done_callback(_log_exception)` so swallowed exceptions surface in logs (GAP-WS-29) | `juniper-cascor/src/api/websocket/manager.py` |
| 0-cascor-9 | `/ws/control` handler returns protocol-error envelopes for unknown commands and non-JSON frames (close 1003) (GAP-WS-22). Handler uses `command_id` echo if present. **Does NOT carry `seq` on `command_response`** (R1-05 §4.17). | `juniper-cascor/src/api/websocket/control_stream.py` |
| 0-cascor-10 | `CHANGELOG.md` + `docs/websocket_protocol.md` ("Sequence numbers, replay, and reconnection" section) | docs |

Settings (`juniper-cascor/src/config/settings.py`) added in commit 2a:
- `ws_replay_buffer_size: int = Field(default=1024, description="...")` (R2-04 D-35)
- `ws_send_timeout_seconds: float = Field(default=0.5, description="...")`
- `ws_resume_handshake_timeout_s: float = Field(default=5.0, description="...")`
- `ws_state_throttle_coalesce_ms: int = Field(default=1000, description="...")`
- `ws_pending_max_duration_s: float = Field(default=10.0, description="...")`

**`command_response` carve-out** (R1-05 §4.17 canonical): `/ws/training` has a replay buffer and every broadcast carries `seq`. `/ws/control` has NO replay buffer and `command_response` frames do NOT carry `seq`. Client-side correlation of responses is via `command_id`, not seq. (CCC-01 wire-format evolution contract.)

**GAP-WS-19 carve-out** (R1-05 §4.16 canonical): `close_all()` lock fix is already in main. Do NOT re-implement. Add `test_close_all_holds_lock` as a regression gate only.

#### 3.3.2 Functional (Phase A-SDK, parallel)

File: `juniper-cascor-client/juniper_cascor_client/control_stream.py`:

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

Behavior:
- Generates `command_id = str(uuid.uuid4())` if absent (R2-04 D-02 applied: `command_id`, NOT `request_id`).
- Registers future in `self._pending: Dict[str, asyncio.Future]` (max size 256; reject new commands with `JuniperCascorOverloadError` if exceeded — R1-02 §6.4 bounded-map safety).
- Sends `{"type": "command", "command": "set_params", "command_id": ..., "params": ...}`.
- Awaits matching `command_response` via background `_recv_task` per-connection correlation map.
- Raises `JuniperCascorTimeoutError` on timeout, `JuniperCascorConnectionError` on disconnect, `JuniperCascorError` on server error response.
- Default `timeout=1.0` (R1-05 §4.1, R2-04 D-01) — source doc §7.32 more-specific rule beats §7.1 generic.
- ALWAYS `pop(command_id, None)` in `finally` (caller-cancellation safety, R1-05 §4.25).
- **No SDK retries** (R1-05 §4.22, R2-04 D-20).
- Stashes `envelope["_client_latency_ms"]` (private field, leading underscore).

File: `juniper-cascor-client/juniper_cascor_client/testing/fake_ws_client.py`:
- Add `on_command(name, handler)` registration.
- Auto-scaffold `command_response` reply for known commands.
- Mirror the wire schema per CCC-05 contract-test parity.

File: `juniper-cascor-client/juniper_cascor_client/testing/server_harness.py`:
- `FakeCascorServerHarness` class used by canopy Phase B tests. Emits envelopes with the same shape as real cascor's `messages.py`. Contract test `test_fake_cascor_message_schema_parity` lives in canopy (CCC-05 §7.3).

Release artifacts:
- `juniper-cascor-client/pyproject.toml` version **minor bump** (e.g., `0.5.0 → 0.6.0`); new public method warrants minor semver.
- `CHANGELOG.md` Keep-a-Changelog entry citing GAP-WS-01, R04-01, R1-05 §4.2.
- PyPI publish via standard workflow. 2-5 min index propagation wait.
- TestPyPI prerelease artifact for canopy PR iteration (R1-03 §17.4, R2-03 CCC-04 item 6).

#### 3.3.3 Cross-cutting (CCCs woven in)

**CCC-01 (schema evolution)**: all new fields are additive. Rollout state matrix documented in PR description (4 combinations). `command_id` rename mandate enforced — grep for `request_id` in PR description must return 0 matches. `emitted_at_monotonic` field present on every broadcast (GAP-WS-24 alignment for CCC-10).

**CCC-02 (observability)**: all 14 Phase 0-cascor metrics from §2.4 must be present before the phase merges. Metrics-presence CI test runs on PR. `WSSeqCurrentStalled` page alert landed and test-fired once in staging.

**CCC-03 (kill switches)**:
- `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` (disables replay; all reconnects snapshot) — CI test `test_replay_buffer_size_env_override`.
- `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` (aggressive slow-client prune) — CI test `test_send_timeout_env_override`.
- Rolling restart of cascor (forces new `server_instance_id`) — documented as ops lever in runbook.
- Revert PR (15 min MTTR) — additive contract means old clients unaffected.

**CCC-04 (cross-repo version pinning)**: Phase 0-cascor merges before canopy Phase B (gives 1-week additive-field soak window validated by `juniper-cascor-worker` CI). Helm `Chart.yaml` `version` and `appVersion` bumped to match cascor minor bump (user memory `project_helm_version_convention.md`).

**CCC-05 (contract tests)**: `test_replay_buffer_capacity_advertised`, `test_seq_present_on_ws_training_broadcast_only`, `test_cascor_command_response_shape_matches_sdk_parser`, `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 explicit negative assertion), `test_fake_cascor_message_schema_parity` (shared with canopy Phase B). Schema-sync PR-template check active.

**CCC-06 (documentation)**: PR description cites GAP-WS-01, GAP-WS-07, GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29, GAP-WS-32. CHANGELOG entry under Added + Changed + Fixed. `juniper-cascor/docs/websocket_protocol.md` section added. `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` runbook published. `juniper-canopy/notes/runbooks/ws-migration-rollback.md` initial version (reverse-dependency rollback order).

**CCC-07 (configuration)**: 5 new `ws_*` cascor settings in canonical table (§2.9) with Pydantic `Field(description=...)`. Validation tests for each.

**CCC-08 (backwards compat)**: REST `/api/v1/training/status` extended additively (old clients ignore new fields). `juniper-cascor-worker` CI green against new cascor during the 1-week soak. `test_legacy_client_ignores_seq_field` gate.

**CCC-09 (feature flags)**: no feature flags in Phase 0-cascor (purely additive).

**CCC-10 (latency instrumentation)**: `emitted_at_monotonic` field shipped in commit 1 (GAP-WS-24 pipe seed). Phase B consumes it.

### 3.4 Test coverage

**Unit tests** (`juniper-cascor/src/tests/unit/api/`):

- `test_seq_monotonically_increases_across_broadcasts` (renamed per R1-05 §4.17 to clarify `/ws/training` scope)
- `test_seq_is_assigned_on_loop_thread`
- `test_seq_lock_does_not_block_broadcast_iteration`
- `test_replay_buffer_bounded_to_configured_capacity` (asserts `maxlen == Settings.ws_replay_buffer_size`)
- `test_replay_buffer_capacity_configurable_via_env` (override to 256 via env var)
- `test_replay_buffer_size_env_override` (CCC-03 kill-switch test)
- `test_resume_replays_events_after_last_seq` (happy path)
- `test_resume_failed_out_of_range` (broadcast 2000, reconnect with last_seq=10)
- `test_resume_failed_server_restarted` (server_instance_id mismatch)
- `test_resume_malformed_data`
- `test_resume_timeout_no_frame` (5 s frame timeout expired)
- `test_connection_established_advertises_instance_id_and_capacity`
- `test_snapshot_seq_atomic_with_state_read` (concurrency test: read REST status during broadcast)
- `test_second_resume_closes_connection_1003` (R1-05 §4.12 one-resume-per-connection)
- `test_slow_client_send_timeout_does_not_block_fanout` (0.5 s `_send_json` quick-fix)
- `test_send_timeout_env_override` (CCC-03 kill-switch test)
- `test_state_coalescer_flushes_terminal_transitions` (Started → Failed within 200 ms, both observed; GAP-WS-21 fix)
- `test_state_coalescer_preserves_terminal_transitions`
- `test_broadcast_from_thread_exception_logged_not_leaked` (GAP-WS-29 fix, uses caplog)
- `test_unknown_command_returns_protocol_error_envelope` (GAP-WS-22)
- `test_malformed_json_closes_1003`
- `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 **explicit negative assertion** — contract test)
- `test_pending_connections_not_eligible_for_broadcast` (R1-05 §4.18)
- `test_promote_to_active_atomic_under_seq_lock`
- `test_close_all_holds_lock` (GAP-WS-19 regression gate, R1-05 §4.16)
- `test_emitted_at_monotonic_present_on_every_broadcast` (CCC-10)
- `test_legacy_client_ignores_seq_field` (CCC-08 backward-compat gate)

**Chaos tests** (R1-02 §3.1 elevated to blocking per R2-01 §18.9):

- **Chaos-broadcast**: `hypothesis` + `asyncio.gather` 100 concurrent broadcast/disconnect/resume under randomized exception types. Assert: no deadlocks, no seq gaps, no coroutine leaks, `_per_ip_counts` shrinks to zero.
- **Chaos-replay-race**: 1000 broadcasts interleaved with 100 `replay_since()` calls from forged cursors. Assert: every snapshot monotonic, no replay returns seq higher than its snapshot's newest.
- **Chaos-broadcast_from_thread**: `hypothesis`-generated random exception types; assert `cascor_ws_broadcast_from_thread_errors_total` increments once per raise, no stderr warning escapes.

**Integration tests** (`juniper-cascor/src/tests/integration/`):

- `test_resume_happy_path_via_test_client`
- `test_resume_failed_server_restarted`
- `test_resume_failed_out_of_range`
- `test_resume_malformed_data`
- `test_resume_timeout_no_frame`

**Load tests** (elevated to blocking gate per R1-02 §10.3, R2-04 D-41):

- Broadcast at 100 Hz for 60 s with 10 clients; p95 latency < 250 ms; memory stable ±10%.

**Metric-presence test** (R1-02 §10.6, R2-04 D-37): pytest scrapes `/metrics` endpoint and asserts every Phase 0-cascor metric from §2.4 is exported.

**SDK tests** (`juniper-cascor-client/tests/unit/`):

- `test_set_params_default_timeout_is_one_second` (R1-05 §4.1 regression gate)
- `test_set_params_round_trip` (happy path with mocked WS, 50 ms ack latency)
- `test_set_params_timeout` → `JuniperCascorTimeoutError`
- `test_set_params_validation_error` → `JuniperCascorValidationError`
- `test_set_params_fails_fast_on_disconnect` (renamed from `test_set_params_reconnection_queue` per R1-05 §4.42)
- `test_set_params_concurrent_correlation` (two concurrent calls distinguished by `command_id`)
- `test_set_params_caller_cancellation_cleans_correlation_map` (**mandatory Phase A gate** per R1-05 §4.25)
- `test_command_legacy_still_works` (regression gate for existing `command()` API)
- `test_set_params_no_command_id_first_match_wins` (transition window before Phase G echo lands)
- `test_set_params_x_api_key_header_present` (R0-02 IMPL-SEC-44 regression guard)
- `test_set_params_no_retry_on_timeout` (R1-05 §4.22)
- `test_correlation_map_bounded_at_256` (R1-02 §6.4)
- `test_recv_task_propagates_exception_to_all_pending_futures` (R0-04 R04-06)
- `test_len_pending_returns_to_zero_after_failure_modes` (R1-02 §9.2 nightly regression, correlation-map leak prevention)

Coverage target: 95% on new SDK code (R1-03 §15.2).

### 3.5 Observability

**Metrics** (cascor, mandatory before merge):

| Metric | Type | Labels | Rationale |
|---|---|---|---|
| `cascor_ws_seq_current` | Gauge | — | Loss of monotonicity is correctness-catastrophic |
| `cascor_ws_replay_buffer_occupancy` | Gauge | — | Operational proxy for replay window |
| `cascor_ws_replay_buffer_bytes` | Gauge | — | Memory-creep guard, sampled every 30 s |
| `cascor_ws_replay_buffer_capacity_configured` | Gauge | — | Init-time assertion, aids operator diffing |
| `cascor_ws_resume_requests_total` | Counter | `outcome={success, server_restarted, out_of_range, malformed, no_resume_timeout, second_resume}` | — |
| `cascor_ws_resume_replayed_events` | Histogram | — | Buckets `{0, 1, 5, 25, 100, 500, 1024}` |
| `cascor_ws_broadcast_timeout_total` | Counter | `type` | Per-type slow-client prune counter |
| `cascor_ws_broadcast_send_duration_seconds` | Histogram | `type` | Latency of `_send_json` path (Phase E tuning signal) |
| `cascor_ws_pending_connections` | Gauge | — | Non-zero >5s = stuck resume handshake |
| `cascor_ws_state_throttle_coalesced_total` | Counter | — | Post-coalescer output |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter | — | Must be 0 in steady state |
| `cascor_ws_seq_gap_detected_total` | Counter | — | Should always be 0; page alert on non-zero |
| `cascor_ws_connections_active` | Gauge | `endpoint` | — |
| `cascor_ws_command_responses_total` | Counter | `command, status` | — |
| `cascor_ws_command_handler_seconds` | Histogram | `command` | — |

**SDK metric** (emitted by consumers after `import`):

- `juniper_cascor_client_ws_set_params_total{status}` where `status ∈ {ok, timeout, error}`

**Alerts**:

- `WSSeqCurrentStalled` (**page**): `changes(cascor_ws_seq_current[5m]) == 0 AND cascor_ws_connections_active > 0` — broadcast-loop hang (RISK-14 precursor). **Test-fired once in staging** before phase ships to production.
- `WSResumeBufferNearCap` (ticket): `cascor_ws_replay_buffer_occupancy > 0.8 * capacity for 30s`.
- `WSPendingConnectionStuck` (ticket): `cascor_ws_pending_connections > 0 for 30s`.
- `WSSlowBroadcastP95` (ticket): `histogram_quantile(0.95, ...) > 500 ms`.
- `WSStateDropped` (**page**): non-zero `cascor_ws_dropped_messages_total{type="state"}` (Phase E prerequisite alert, defined now).

### 3.6 Pull request plan

| # | Branch | Title | Owner | Target | Merge order |
|---|---|---|---|---|---|
| P1 | `phase-0-cascor-seq-replay-resume` | `feat(ws): seq numbers, replay buffer, resume protocol, state coalescer (GAP-WS-07,13,21,22,29,32)` | backend-cascor | juniper-cascor main | 1 (after P2) |
| P2 | `phase-a-sdk-set-params` | `feat(sdk): CascorControlStream.set_params with command_id correlation (GAP-WS-01)` | SDK | juniper-cascor-client main | 1 (parallel with P1, must publish first) |

Single cascor PR, squash-merged. The 10 commits are tightly coupled; splitting forces multiple cross-repo coordination windows. PR body cross-references GAP-WS-07/13/21/22/29/32, R1-05 §4.12/4.17/4.18/4.19/4.20/4.21, M-SEC-12-folded per R1-05 §4.15.

**Branch naming**: `phase-0-cascor-*` per Juniper centralized worktree convention; worktrees live at `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--phase-0-cascor--<timestamp>--<shorthash>/`.

**Version bumps**:
- `juniper-cascor`: **minor** (new envelope fields are a public contract change)
- `juniper-cascor-client`: **minor** (new public method `set_params`)
- `juniper-ml/pyproject.toml` extras pin: one-line follow-up PR after SDK release (patch bump)
- Helm charts: both `Chart.yaml` `version` and `appVersion` match (user memory convention)

### 3.7 Exit gate (measurable)

Must all be true before Phase 0-cascor exits:

1. All 27+ unit tests, 5 integration tests, 3 chaos tests, load test, metric-presence test green in CI (`cd juniper-cascor/src/tests && bash scripts/run_tests.bash`).
2. `/ws/training` broadcasts observed in staging show strictly monotonically increasing `seq` values over 60 s manual tail.
3. `/api/v1/training/status` REST response includes `snapshot_seq` and `server_instance_id` fields (curl against staging).
4. `cascor_ws_broadcast_send_duration_seconds` p95 < 100 ms in staging baseline.
5. A `resume` frame with `last_seq = N-5` after forced disconnect successfully replays exactly 5 events in seq order.
6. A forced cascor restart followed by reconnect triggers `resume_failed{reason=server_restarted}` and client falls back to REST snapshot.
7. `cascor_ws_replay_buffer_capacity_configured == 1024` in production config; `== 256` in staging config (proves the tunable works).
8. **72-hour staging soak** (R1-02 §3.4, R2-04 D-38) with: `cascor_ws_broadcast_from_thread_errors_total == 0`, `cascor_ws_seq_gap_detected_total == 0`, `cascor_ws_replay_buffer_occupancy` distribution stable, `cascor_ws_broadcast_timeout_total` rate < 0.1/s.
9. `juniper-cascor-worker` CI runs against new cascor main during the 72 h soak and passes (CCC-04, CCC-08 backward-compat validation).
10. Runbook `juniper-cascor/notes/runbooks/cascor-replay-buffer.md` published.
11. `WSSeqCurrentStalled` alert test-fired once in staging via synthetic trigger, verified to reach on-call channel.
12. Metric-presence test green: every metric from §3.5 exported by `/metrics`.
13. CHANGELOG and `docs/websocket_protocol.md` entries reviewed and merged.
14. Load test green (100 Hz × 60 s × 10 clients, p95 < 250 ms).

**SDK exit gate** (Phase A-SDK independent):

1. All 14 SDK tests pass.
2. Coverage ≥ 95% on new code.
3. `pip install juniper-cascor-client==<new version>` from PyPI succeeds in a fresh venv (post 2-5 min index propagation).
4. `test_set_params_caller_cancellation_cleans_correlation_map` passes AND `_pending` len gauge reads 0 after cancellation (inspected via test hook).
5. Record new version as `SDK_VERSION_A` for Phase C dep pin bump.

**Going/no-go**: if criterion 8 (seq gap during soak) shows any gap, HALT and investigate. Do not proceed to Phase B until the gap is understood.

### 3.8 Rollback

| Scenario | Action | MTTR | Validation |
|---|---|---|---|
| Slow-client false-drops | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=30` (temporary env override) | 2 min | `cascor_ws_broadcast_timeout_total` freezes |
| Replay buffer misbehavior | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 5 min | `cascor_ws_resume_requests_total{outcome=out_of_range}` spikes |
| Full rollback | `git revert` Phase 0-cascor PR, blue/green redeploy | 15 min | Clients with cached `server_instance_id` get `resume_failed` → REST snapshot fallback |
| Emergency new UUID | Rolling restart of cascor | 10 min | All clients snapshot-refetch on new `server_instance_id` |
| SDK yank (Phase A) | `twine upload --skip-existing` new version; yank previous | 2 min | `pip index versions` reflects |

**Dangerous edge**: a client caching old `connection_established` shape with a strict schema parser breaks. Fix is on client side, not server rollback. Documented in runbook.

### 3.9 NOT in this phase

- Full Phase E backpressure (per-client pump task + bounded queue + policy matrix). Only 0.5 s `_send_json` quick-fix lands.
- `permessage-deflate` negotiation (GAP-WS-17).
- Topology chunking (GAP-WS-18).
- `seq` on `command_response` (R1-05 §4.17 — explicitly NOT included).
- GAP-WS-19 re-fix (already on main; regression test only).
- M-SEC-01..11 security controls (Phase B-pre-a and B-pre-b).
- Multi-tenant replay buffers (R1-05 §4.13 defer).
- Canopy adapter hot/cold split (Phase C).
- Canopy drain callbacks and polling elimination (Phase B).
- Prometheus histogram for canopy-side delivery latency (Phase B, GAP-WS-24b).
- `set_params` cascor-side integration tests (Phase G, bundled with this).

### 3.10 Decisions blocking entry

All resolved per §2.1-§2.9. Specifically:

- **D-02** (`command_id` naming): applied
- **D-03** (no seq on `command_response`): applied
- **D-11** (Phase 0-cascor carve-out): applied
- **D-14** (`_pending_connections` set): applied
- **D-15** (`server_instance_id` programmatic): applied
- **D-16** (`replay_buffer_capacity` field): applied
- **D-25** (single-tenant v1): applied
- **D-30** (one-resume-per-connection): applied
- **D-35** (replay buffer 1024): applied
- **D-36** (`JUNIPER_WS_REPLAY_BUFFER_SIZE=0` kill switch): applied
- **D-38** (72 h staging soak): applied
- **D-41** (load tests blocking): applied
- **D-46** (`JUNIPER_WS_SEND_TIMEOUT_SECONDS` configurable): applied
- **D-52** (`WSSeqCurrentStalled` page alert): applied

---

## 4. Phase B-pre-a: read-path security gate

### 4.1 Goal

Close the minimum set of security holes that exposing browser→canopy `/ws/training` traffic opens: **frame-size caps** (M-SEC-03, 4 KB inbound on training, 64 KB inbound on control, 128 KB outbound), **Origin allowlist on `/ws/training`** (M-SEC-01 + M-SEC-01b; **this master plan places Origin-on-`/ws/training` in B-pre-a per R2-01's exfiltration argument**, resolving an R2-cross disagreement), **per-IP connection cap** (M-SEC-04 minimal, 5/IP), **idle timeout** (M-SEC-10, 120 s bidirectional), and **audit logger skeleton** (M-SEC-07 skeleton — dedicated `canopy.audit` logger with JSON formatter + `TimedRotatingFileHandler` + scrub allowlist; Prometheus counters land in Phase B per R1-05 §4.14).

Does **not** include CSRF / cookie session / Origin on `/ws/control` / rate limit / full audit counters — those are Phase B-pre-b, which gates Phase D, not Phase B.

### 4.2 Entry gate

- [ ] Main clean on both cascor and canopy.
- [ ] No concurrent security-focused PR open on either repo.
- [ ] `Settings.ws_allowed_origins`, `Settings.ws_max_connections_per_ip`, `Settings.ws_idle_timeout_seconds`, `Settings.audit_log_*` not already used by any other phase.
- [ ] `canopy.audit` logger name reserved (grep returns no prior use).
- [ ] R2-04 decisions D-09, D-12, D-13, D-23, D-24, D-28, D-32, D-51 all resolved per §2.
- [ ] GAP-WS-19 verified RESOLVED on main (D-13).

### 4.3 Deliverables

#### 4.3.1 Functional

**Cascor side**:

| Step | File | Change |
|---|---|---|
| B-pre-a-1 | `juniper-cascor/src/api/websocket/origin.py` (new) | `validate_origin(ws, allowlist: list[str]) -> bool` helper. Case-insensitive host compare, port significant, null origin rejected, `*` unsupported (refused at parser), empty allowlist = reject-all (fail-closed) |
| B-pre-a-2 | `juniper-cascor/src/tests/unit/api/test_websocket_origin.py` (new) | Matrix tests: exact match, case-insensitive, trailing-slash strip, null origin, port mismatch, scheme mismatch, wildcard rejection, empty = reject-all |
| B-pre-a-3 | `juniper-cascor/src/api/app.py` | Wire `validate_origin` into `training_stream_handler` (NOT `control_stream_handler` yet) |
| B-pre-a-4 | `juniper-cascor/src/config/settings.py` | `ws_allowed_origins: list[str] = []` (fail-closed default); env `JUNIPER_WS_ALLOWED_ORIGINS` parser refuses `*` |
| B-pre-a-5 | `juniper-cascor/src/api/websocket/manager.py` | `_per_ip_counts: Dict[str, int]` under `_lock`, increment in `connect()`, decrement in `disconnect()` `finally`, purge empty entries |
| B-pre-a-6 | `juniper-cascor/src/config/settings.py` | `ws_max_connections_per_ip: int = 5` |
| B-pre-a-7 | `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py` (new) | 6th-conn rejected 1013; race test via `asyncio.gather`; entries purged when count reaches zero |
| B-pre-a-8 | `juniper-cascor/src/api/websocket/training_stream.py` | `max_size=4096` on every inbound `receive_*()` call |
| B-pre-a-9 | `juniper-cascor/src/api/websocket/manager.py` | Idle timeout: `asyncio.wait_for(receive_text(), timeout=Settings.ws_idle_timeout_seconds)`, close 1000 on TimeoutError |

**Canopy side**:

| Step | File | Change |
|---|---|---|
| B-pre-a-10 | `juniper-canopy/src/backend/ws_security.py` (new) | Copy (do NOT cross-import) `validate_origin` helper — not shared library by design |
| B-pre-a-11 | `juniper-canopy/src/main.py` | Wire `validate_origin` into `/ws/training` route handler |
| B-pre-a-12 | `juniper-canopy/src/config/settings.py` | `allowed_origins` with concrete localhost/127.0.0.1 × http/https defaults |
| B-pre-a-13 | `juniper-canopy/src/main.py` | `max_size=4096` on `/ws/training` inbound, `max_size=65536` on `/ws/control` inbound |
| B-pre-a-14 | `juniper-canopy/src/backend/audit_log.py` (new) | `canopy.audit` logger, JSON formatter, `TimedRotatingFileHandler(when="midnight", backupCount=90)`, scrub allowlist derived from `SetParamsRequest.model_fields.keys()`, CRLF escape per R0-02 §4.6 |
| B-pre-a-15 | `scripts/audit_ws_receive_calls.py` (new, CI) | AST check: every `ws.receive_*()` call has explicit `max_size` (R1-02 §4.1 item 2) |

**Meta-setting**: `ws_security_enabled: bool = True` (positive-sense, R2-03 §15.3 applied override of R1-05 §4.10) with CI guardrail in `juniper-deploy` compose validation refusing `ws_security_enabled=false` in production profiles.

#### 4.3.2 Cross-cutting (CCCs woven in)

**CCC-01 (schema)**: no new wire fields (security gate is transport-level). `auth` first-frame shape NOT introduced here (it's Phase B-pre-b).

**CCC-02 (observability)**:
- `cascor_ws_oversized_frame_total{endpoint, type}`
- `cascor_ws_per_ip_rejected_total`
- `cascor_ws_idle_timeout_total`
- `canopy_ws_oversized_frame_total{endpoint}`
- `canopy_ws_per_ip_rejected_total`
- `canopy_ws_origin_rejected_total{origin_hash, endpoint}` — origin hash is SHA-256 prefix 8 chars (GDPR-safe correlation)
- `canopy_audit_events_total{event_type}` — counter landed in Phase B-pre-a but Prometheus dashboard wiring deferred to Phase B (R1-05 §4.14)

Alerts (all page severity for Phase B-pre-a):

- **`WSOriginRejection`** (page): `increase(canopy_ws_origin_rejected_total[5m]) > 0` from unknown origin_hash. **Test-fired once in staging** (RISK-15 precursor).
- **`WSOversizedFrame`** (page): `increase(canopy_ws_oversized_frame_total[5m]) > 0`.

**CCC-03 (kill switches)**:

| Switch | Who | MTTR | Validation |
|---|---|---|---|
| `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | ops | 5 min | `canopy_ws_per_ip_rejected_total` drops to 0 |
| `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | ops | 5 min | `canopy_ws_origin_rejected_total` drops |
| `JUNIPER_WS_ALLOWED_ORIGINS=*` | — | — | **REFUSED by parser** (non-switch; prevents panic-edit during incident) |
| `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | ops | 5 min | Idle timeout disabled |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | No new audit log writes |

CI test `test_audit_log_env_override` and `test_allowed_origins_wildcard_refused` installed. Both tests are hard gates for the phase to merge.

**CCC-04 (cross-repo)**: two PRs — cascor first (P3), then canopy (P4) which references cascor's origin helper pattern.

**CCC-05 (contract tests)**: no new wire-level contract tests in B-pre-a (security gate is transport). Existing `test_second_resume_closes_connection_1003` (landed in Phase 0-cascor) is cross-referenced as a security control.

**CCC-06 (documentation)**: PR descriptions cite M-SEC-01, M-SEC-01b, M-SEC-03, M-SEC-04 (partial), M-SEC-10, GAP-WS-27, RISK-15. Runbook `juniper-canopy/notes/runbooks/ws-audit-log-troubleshooting.md` published. Runbook `juniper-canopy/notes/runbooks/ws-cswsh-detection.md` initial version (fuller version in B-pre-b).

**CCC-07 (configuration)**: 4 new cascor + canopy settings in canonical table with validation tests. `ws_security_enabled` positive-sense with CI guardrail.

**CCC-08 (backwards compat)**: REST endpoints continue to serve under `audit_log_enabled=False`. Every kill-switch test asserts REST path functional post-flip.

**CCC-09 (feature flags)**: no per-phase flag; `ws_security_enabled` and `audit_log_enabled` are permanent-on kill levers.

**CCC-10 (latency instrumentation)**: no contribution.

### 4.4 Test coverage

**Unit**:
- `test_oversized_frame_rejected_with_1009` per endpoint (cascor + canopy)
- `test_per_ip_cap_enforced` (6th rejected 1013)
- `test_per_ip_counter_decrements_on_disconnect`
- `test_per_ip_counter_decrements_on_exception`
- `test_per_ip_map_shrinks_to_zero` (memory-leak guard; entries reaching 0 are deleted)
- `test_per_ip_counter_increment_decrement_race` (asyncio.gather race test)
- `test_origin_allowlist_accepts_configured_origin`
- `test_origin_allowlist_rejects_third_party`
- `test_origin_allowlist_rejects_missing_origin`
- `test_origin_header_case_insensitive_host`
- `test_empty_allowlist_rejects_all` (fail-closed)
- `test_allowed_origins_wildcard_refused` (parser-level guardrail)
- `test_idle_timeout_closes_1000`
- `test_audit_log_format_and_scrubbing` (R1-05 §4.14)
- `test_audit_log_rotates_daily` (mocked time)
- `test_audit_log_escapes_crlf_injection` (R1-05 §4.15 M-SEC-12 folded)
- `test_audit_log_write_failure_fallback` (R1-02 §4.2 item 17 — does NOT block legitimate user actions; increments `canopy_ws_audit_log_write_error_total` + WARN to stderr)

**Integration**:
- `test_cswsh_from_evil_page_cannot_exfiltrate_training_stream` (Playwright, cross-origin probe on `/ws/training`)

**CI guardrail**:
- `scripts/audit_ws_receive_calls.py` passes (no unguarded `receive_*`).

### 4.5 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P3 | `phase-b-pre-a-cascor-security` | `feat(security): origin allowlist + max_size + per-IP cap + idle timeout on /ws/training (M-SEC-01b/03/04/10)` | backend-cascor + security | juniper-cascor main |
| P4 | `phase-b-pre-a-canopy-security` | `feat(security): origin allowlist + max_size on /ws/training + audit logger skeleton (M-SEC-01/03/07 skeleton)` | backend-canopy + security | juniper-canopy main |

Merge order: **P3 → P4**. P3 can land alone (additive server-side guards). P4 lands as soon as P3 is in main.

**Version bumps**: patch on both cascor and canopy.

### 4.6 Exit gate (measurable)

1. All 17 unit tests + integration test + CI guardrail green.
2. Manual CSWSH probe from `http://evil.example.com` rejected by both cascor and canopy `/ws/training`.
3. 65 KB frame sent to either `/ws/training` endpoint returns close code 1009.
4. 6 simultaneous connections from same IP rejected with 1013 on the 6th.
5. Kill cascor process mid-broadcast; per-IP counters return to zero within `disconnect()` cleanup window.
6. `canopy_ws_origin_rejected_total` counter increments on manual rejection test.
7. `canopy_audit_events_total{event_type="origin_rejected"}` counter increments on the same event.
8. Empty `JUNIPER_WS_ALLOWED_ORIGINS` in staging rejects all connections (fail-closed test).
9. Audit log file appears at expected path in staging, contains JSON-formatted entries, rotates on day boundary (verified via `ls -la` at day boundary).
10. **24-hour staging soak** with no user lockout (R2-01 §5.5).
11. **`WSOriginRejection` alert test-fired once** in staging per R1-02 §2.3, reached on-call channel.
12. Runbook `ws-audit-log-troubleshooting.md` published.

**Going/no-go**: if empty allowlist fails to reject (fail-open instead of fail-closed), HALT. Critical security defect.

### 4.7 Rollback

| Scenario | Action | MTTR |
|---|---|---|
| Panic-wide origin opening | `JUNIPER_WS_ALLOWED_ORIGINS=<broader-list>` | 5 min |
| Per-IP lockout emergency | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 min |
| Idle-timeout false positives | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | 5 min |
| Audit disk full | `JUNIPER_AUDIT_LOG_ENABLED=false` | 5 min |
| Full revert | `git revert P4; git revert P3`; redeploy | 10 min |

### 4.8 NOT in this phase

- M-SEC-02 cookie + CSRF first-frame (Phase B-pre-b)
- Origin allowlist on `/ws/control` (Phase B-pre-b, tied to CSRF)
- M-SEC-05 per-command rate limit (Phase B-pre-b)
- M-SEC-06 opaque close reasons (Phase B-pre-b)
- Prometheus counters for audit events (Phase B, per R1-05 §4.14)
- M-SEC-11 adapter inbound validation (Phase B-pre-b)
- HMAC adapter auth (Phase B-pre-b)
- Full M-SEC-07 audit counters (Phase B-pre-b)
- Log injection escaping as extended M-SEC-07 (Phase B-pre-b)

### 4.9 Decisions blocking entry

- **D-09** (effort estimate 0.5 day for B-pre-a): applied
- **D-12** (M-SEC-10/11 adoption, M-SEC-12 folded): applied
- **D-13** (GAP-WS-19 RESOLVED): applied
- **D-23** (B-pre split): applied
- **D-24** (5/IP default): applied
- **D-28** (dedicated audit logger, skeleton in B-pre-a): applied
- **D-32** (multi-tenant replay deferred): applied
- **D-51** (`WSOriginRejection` page severity): applied

---

## 5. Phase B: frontend wiring + polling elimination

### 5.1 Goal

The canopy browser drains the `/ws/training` WebSocket stream into bounded Dash stores, renders metric chart updates via `Plotly.extendTraces`, and **stops polling `/api/metrics/history` entirely** when the WebSocket is healthy. This is the P0 win: the ~3 MB/s polling bandwidth is eliminated in staging and production. REST polling path is kept forever as the kill-switch fallback.

This phase also wires `ws-state-buffer`, `ws-topology-buffer`, `ws-cascade-add-buffer`, `ws-candidate-progress-buffer`, `ws-connection-status` stores to consumer callbacks (state panel, NetworkVisualizer minimum, candidate metrics, connection indicator badge).

This phase **folds Phase I** (asset cache busting) and **folds Phase F's jitter-backoff lift** (3-line change to `websocket_client.js`). Heartbeat ping/pong is Phase F proper.

### 5.2 Entry gate

- [ ] Phase 0-cascor merged to `juniper-cascor` main and deployed to staging with 72 h soak green.
- [ ] Phase B-pre-a (P3 + P4) merged to both cascor and canopy main and deployed to staging with 24 h soak green.
- [ ] `Settings.enable_browser_ws_bridge` added to canopy config (default `False` for Phase B PR window).
- [ ] `Settings.disable_ws_bridge` added (permanent kill switch, default `False`).
- [ ] NetworkVisualizer render tech verified in first commit: `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py` → answer recorded in PR description (R1-05 §5.1 unresolved → resolved at implementation time).
- [ ] Dash version verified: `grep "dash" juniper-canopy/pyproject.toml` — record-only check; Option B (Interval drain) works regardless.
- [ ] Plotly.js version verified — record-only check; assume ≥2.x, fail fast if 1.x (adds 0.25-day pin bump commit).
- [ ] **Pre-Phase-B `canopy_rest_polling_bytes_per_sec` baseline measured in staging for 1 h** (the number we're trying to reduce by ≥90% — R2-04 D-62 implicit).
- [ ] Phase A-SDK merged and published to PyPI (for future Phase C consumption; not a hard Phase B dependency).
- [ ] All R2-04 Phase B blocking decisions resolved: D-04, D-05, D-06, D-07, D-08, D-17, D-18, D-21, D-26, D-37, D-39, D-40, D-42, D-43, D-44, D-50, D-53, D-54.

### 5.3 Deliverables

#### 5.3.1 Functional

**Frontend JS** (`juniper-canopy/src/frontend/assets/`):

1. **`ws_dash_bridge.js`** (new, ~200 LOC). Module-scope closure exposed as `window._juniperWsDrain`. Five `on(type, ...)` handlers for `metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`. Per-handler bounded ring buffers. Drain methods: `drainMetrics()`, `drainState()`, `drainTopology()`, `drainCascadeAdd()`, `drainCandidateProgress()`, `peekStatus()`. **Ring-bound enforcement IN the handler, NOT the drain callback** (R1-02 §5.4 compile-time invariant; R1-01 §2.3.1 MVS-FE-01). `MAX_METRICS_BUFFER=1000`, `MAX_EVENT_BUFFER=500`.

2. **`websocket_client.js` edit (do NOT delete)**:
   - Add `onStatus()` enrichment (connected/reason/reconnectAttempt/ts).
   - Add jitter to reconnect backoff: `delay = Math.random() * Math.min(30_000, 500 * Math.pow(2, attempt))` (GAP-WS-30, 3-line change).
   - **Remove the 10-attempt cap** (GAP-WS-31) — retry forever at max 30 s cap. (Overrides R1-01 which kept the cap; this plan sides with R2-01 §18.4 / R1-03 §8.5.)
   - Capture `server_instance_id` from `connection_established`.
   - Track `seq` (monotonic check + WARN on out-of-order).
   - On reconnect, send `resume` frame as first frame with `{last_seq, server_instance_id}`. On `resume_failed`, fall back to REST snapshot (call existing `/api/v1/training/status` endpoint and set new `server_instance_id`).

3. **Delete parallel raw-WebSocket clientside callback** at `dashboard_manager.py:1490-1526` (GAP-WS-03). Replace with citation comment. This is the only deletion in Phase B (dead code).

4. **`ws_latency.js`** (new, ~50 LOC). Browser-side latency beacon. Records `received_at_ms - emitted_at_monotonic` per message, POSTs to `/api/ws_latency` every 60 s. **Gated on `Settings.enable_ws_latency_beacon`** — falls back to no-op if endpoint returns 404. **GAP-WS-24a** (browser emitter half of CCC-10 pipe).

5. **rAF scaffold DISABLED**: `_scheduleRaf = noop` gated on `Settings.enable_raf_coalescer=False` (R1-05 §4.3, R2-04 D-04). Scaffold ships but is gated; enable only after §5.6 instrumentation shows frame pressure.

**Python-side drain callbacks** (`juniper-canopy/src/frontend/`):

6. **`dashboard_manager.py` `ws-metrics-buffer` Store + drain callback**. Drain callback fires on `fast-update-interval` tick (1 s during disconnect fallback, 100 ms during connected). Reads `window._juniperWsDrain.drainMetrics()` and writes **structured `{events: [...], gen: int, last_drain_ms: float}`** (R1-05 §4.7, R2-04 D-07).

7. **Update existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks** to read from `window._juniperWsDrain.drainTopology()` / `drainState()`. Delete references to old `window._juniper_ws_*` globals (replaced, not deleted — they're shims).

8. **Add `ws-cascade-add-buffer` and `ws-candidate-progress-buffer` Stores** and drain callbacks.

9. **`ws-connection-status` Store** with drain callback peeking `window._juniperWsDrain.peekStatus()`; emits only on change.

10. **Refactor `_update_metrics_store_handler`** at `dashboard_manager.py:2388-2421` to return `no_update` when `ws-connection-status.connected === true`. **Slow fallback to 1 Hz during disconnect** via `n % 10 != 0` check (R1-05 §4.4, R2-04 D-05).

11. **Apply same polling-toggle pattern** to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. **Keep REST paths** — they are the kill switch and fallback (never deleted, per R1-02 principle 7, R2-04 D-21/D-54).

12. **Migrate `MetricsPanel.update_metrics_display()`** at `metrics_panel.py:648-670` to clientside callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"` to initial figure layout. Add hidden `metrics-panel-figure-signal` dummy Store.

13. Same for `CandidateMetricsPanel`.

14. **NetworkVisualizer minimum WS wiring**: wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape update callback (if cytoscape) or `extendTraces` (if Plotly). Render-tech verification happens in first commit of this PR. **Deep migration deferred** per R1-05 §4.5 pending first-commit verification.

15. **Connection indicator badge** (`html.Div` with clientside_callback reading `ws-connection-status`). Four states: connected-green, reconnecting-yellow, offline-red, demo-gray.

16. **Demo mode parity**: `demo_mode.py` sets `ws-connection-status` to `{connected: true, mode: "demo"}` — required test `test_demo_mode_metrics_parity` as blocker (RISK-08).

17. **`/api/ws_latency` POST endpoint** in `juniper-canopy/src/main.py`. **GAP-WS-24b** (canopy backend half). Feeds `canopy_ws_delivery_latency_ms_bucket` histogram. Also sets `canopy_rest_polling_bytes_per_sec` gauge (P0 motivator proof). Per-endpoint label (`/api/metrics/history`) per R1-02 §2.2 amplification.

18. **`/api/ws_browser_errors` POST endpoint** in `main.py`. Feeds `canopy_ws_browser_js_errors_total{component}` counter (R2-04 D-59 implicit; pattern mirrors `/api/ws_latency`).

19. **Phase I asset cache busting bundled with Phase B**: configure `assets_url_path` with content-hash query string (R2-01 §6.1 item 17, R2-02 §14).

20. **Audit logger Prometheus counters** (R1-05 §4.14 move from B-pre-a to B): wire `canopy_audit_events_total{event_type}` into Prometheus scrape.

21. **Two-flag runtime gate**: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge`. Default `enable_browser_ws_bridge=False` during Phase B PR window. Staging flip is ops-driven after 72 h soak. Production flip is separate one-line config PR reviewed by project lead.

**Cascor side**: no code changes in Phase B; all cascor-side observability ships in Phase 0-cascor + any residual Prometheus metric wiring (landing with P5 small PR).

#### 5.3.2 Cross-cutting

**CCC-01 (schema)**: browser reads new envelope fields (`seq`, `server_instance_id`, `replay_buffer_capacity`, `emitted_at_monotonic`). Sends `resume` frame on reconnect. No new wire-level contract.

**CCC-02 (observability)** — the biggest Phase B contribution:

| Metric | Type | Labels | Source |
|---|---|---|---|
| **`canopy_rest_polling_bytes_per_sec`** | **Gauge** | **`endpoint`** | **P0 motivator proof** |
| `canopy_ws_delivery_latency_ms_bucket` | Histogram | `type` | R1-03 |
| `canopy_ws_backend_relay_latency_ms` | Histogram | — | R1-02 §2.2 (cascor→canopy hop separate) |
| `canopy_ws_browser_heap_mb` | Histogram | — | R1-02 |
| `canopy_ws_browser_js_errors_total` | Counter | `component` | **R1-02 §2.2** every try/catch in `ws_dash_bridge.js` / `websocket_client.js` increments |
| `canopy_ws_drain_callback_gen` | Gauge | `buffer` | **R1-02 §2.2** monotonic drain gen; stuck = dead drain |
| `canopy_ws_active_connections` | Gauge | — | R1-03 |
| `canopy_ws_reconnect_total` | Counter | `reason` | R1-03 |
| `canopy_ws_connection_status` | Gauge | `status` | R1-02 |
| `canopy_audit_events_total` | Counter | `event_type` | deferred from B-pre-a |
| `canopy_ws_latency_beacon_errors_total` | Counter | — | R2-03 CCC-10 6.6 risk mitigation |

**SLOs** (R1-02 §2.4 + R1-03 §16.4 unified):

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` | <100 ms | <250 ms | <500 ms |
| `state` | <50 ms | <100 ms | <200 ms |
| `command_response` (set_params) | <50 ms | <100 ms | <200 ms |
| `command_response` (start/stop) | <100 ms | <250 ms | <500 ms |
| `cascade_add` | <250 ms | <500 ms | <1000 ms |
| `topology` ≤64 KB | <500 ms | <1000 ms | <2000 ms |

**SLOs are aspirations** until ≥1 week of production data; then separate PR promotes to binding via AlertManager rules (R2-03 CCC-10 item 8).

**Error-budget burn-rate rule** (R1-02 §2.4, R2-04 D-50): if 99.9% compliance budget burns in <1 day, freeze all non-reliability work until recovered. Operationally binding.

**Alerts**:
- `WSDeliveryLatencyP95High` (ticket): p95 > 500 ms for `metrics`.
- `WSDrainCallbackGenStuck` (ticket): `changes(canopy_ws_drain_callback_gen[2m]) == 0` → also flips connection status to reconnecting (polling toggle reverts to REST fallback).
- `WSBrowserHeapHigh` (ticket): p95 > 500 MB.
- `WSJSErrorsNonZero` (ticket): `increase(canopy_ws_browser_js_errors_total[5m]) > 0`.
- `WSConnectionCount80` (ticket): 80% of `ws_max_connections`.

**CCC-03 (kill switches)**:

| Switch | Who | MTTR | Validation |
|---|---|---|---|
| `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | ops | 5 min | `canopy_rest_polling_bytes_per_sec` rises to baseline |
| `JUNIPER_DISABLE_WS_BRIDGE=true` | ops | 5 min | Same (permanent kill switch; `and not` logic) |
| Hardcoded ring-cap reduction | dev | 1 hour | Browser memory drops in soak metrics |
| URL query `?ws=off` | user | instant | Per-user diagnostic hatch |
| Revert P6 | ops | 30 min | Full rollback to pre-Phase-B REST polling |

CI tests `test_enable_browser_ws_bridge_env_override`, `test_disable_ws_bridge_env_override`, `test_both_flags_interact_correctly` (two-flag pattern, R1-05 §4.45).

**Kill-switch drill**: during 72 h staging soak, every switch is flipped once and TTF measured. If any TTF >5 min, the phase does not proceed to production (R1-02 §13.7 abandon trigger, R2-04 D-53).

**CCC-04 (cross-repo)**: canopy pins `juniper-cascor-client>=<SDK_VERSION_A>` (from Phase A-SDK). TestPyPI prerelease available for iteration before PyPI (R1-03 §17.4). **Cross-version CI lane** (R2-03 §15.5 contribution): canopy e2e runs against both current pinned SDK and previous pinned version; both must pass (backward-compat proof).

**CCC-05 (contract tests)**:
- `test_browser_message_handler_keys_match_cascor_envelope` (ws_dash_bridge.js `on(type, ...)` handlers correspond to cascor-emitted types)
- `test_fake_cascor_message_schema_parity` (parity test lives in canopy, fake harness in cascor-client)
- `test_normalize_metric_produces_dual_format` (**Phase H regression gate FOLDED INTO Phase B** so Phase H defers safely; R1-01 MVS-TEST-14)
- Contract tests inline-literal rule: no cross-repo fixture imports (R2-03 §7.3 item 5)

**CCC-06 (documentation)**:
- Runbook `juniper-canopy/notes/runbooks/ws-bridge-kill.md` (5 min TTF recipe)
- Runbook `juniper-canopy/notes/runbooks/ws-bridge-debugging.md`
- Runbook `juniper-canopy/notes/runbooks/ws-memory-soak-test-procedure.md` (72 h soak procedure for browser heap)
- Grafana "WebSocket health" panel JSON committed to `juniper-canopy/deploy/grafana/ws-health.json`
- Grafana "Polling bandwidth" panel JSON (P0 trend)
- PR description cites GAP-WS-02, 03, 04, 05, 14, 15, 16, 24a, 24b, 25, 26, 30, 33

**CCC-07 (configuration)**: 4 new canopy settings (`enable_browser_ws_bridge`, `disable_ws_bridge`, `enable_raf_coalescer`, `enable_ws_latency_beacon`) in canonical table.

**CCC-08 (backwards compat)**: **REST polling handler KEPT FOREVER**. Regression harness `test_rest_endpoints_remain_functional.py` (R2-03 CCC-08) runs in `fast` lane on every PR. Golden shape file committed at `juniper-canopy/src/tests/regression/rest_endpoint_shapes.golden.json`. Every kill-switch test asserts REST path continues to work post-flip.

**CCC-09 (feature flags)**: **two-flag pattern** applied. `enable_browser_ws_bridge` (dev opt-in, flipped post-soak) and `disable_ws_bridge` (permanent kill switch, never flipped). Flip criteria documented in `ws-bridge-kill.md`. Flag flip is **separate PR** (P7), not bundled with feature PR.

**CCC-10 (latency instrumentation)**: **FULL PIPE ACTIVATED** in Phase B. `emitted_at_monotonic` from cascor (already shipped in Phase 0-cascor) → `canopy_ws_backend_relay_latency_ms` (new, cascor→canopy hop) → browser JS beacon → `/api/ws_latency` endpoint → `canopy_ws_delivery_latency_ms_bucket`. Buckets `{50, 100, 200, 500, 1000, 2000, 5000}` ms. 60 s beacon cadence. **Clock offset recomputation on reconnect** (R1-03 §16.5 step 5, R2-03 CCC-10 item 4) via `test_latency_histogram_resilient_to_laptop_sleep`.

### 5.4 Test coverage

**JS unit** (Jest/Vitest if configured):
- jitter backoff formula test (`test_reconnect_backoff_has_jitter` with tight assertion `delay is number AND 0 <= delay <= cap`; R1-02 §9.9 NaN/Infinity regression)
- uncapped reconnect test
- `onStatus()` enrichment test
- `_introspect` test
- **AST lint for ring-bound-in-handler** (R1-02 §5.4 item 2 — walks compiled JS, finds every `on(` call, asserts subsequent `push(...)` is followed by `splice(...)` in the same function body). Hard gate.

**Python unit**:
- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_fallback_polling_at_1hz_when_disconnected` (R1-05 §4.4)
- `test_ws_metrics_buffer_drain_is_bounded`
- `test_ws_metrics_buffer_store_is_structured_object` (R1-05 §4.7 — assert `.data` is `{events, gen, last_drain_ms}`)
- `test_network_visualizer_updates_on_ws_cascade_add`
- `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` (GAP-WS-24b)
- `test_both_flags_interact_correctly` (two-flag logic)
- `test_audit_log_prometheus_counters` (deferred from B-pre-a)
- `test_latency_histogram_resilient_to_laptop_sleep` (CCC-10 clock-offset)
- Grep assertions: `grep -r '_juniper_ws_' src/frontend/` → 0; `grep -r 'new WebSocket' src/frontend/` → 1

**dash_duo (e2e)**:
- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected`
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_demo_mode_metrics_parity` (RISK-08 gate, runs in **both** fast lane AND e2e lane per R1-05 §4.47)
- `test_connection_indicator_badge_reflects_state`
- `test_ws_metrics_buffer_ignores_events_with_duplicate_seq`
- `test_ws_metrics_buffer_is_monotonic_in_seq_no_gap_gt_1`

**Playwright**:
- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_seq_reset_on_cascor_restart` (server_instance_id mismatch → snapshot fallback)
- `test_plotly_extendTraces_used_not_full_figure_replace`
- `test_ws_control_command_response_has_no_seq` (R1-05 §4.17 wire-level gate)
- **`test_bandwidth_eliminated_in_ws_mode`** (R1-01 MVS-TEST-15 + R1-04 §15.4): **THE P0 ACCEPTANCE GATE**. Asserts `/api/metrics/history` request count is zero over 60 s after initial load.
- `test_metrics_message_has_dual_format` (R1-01 MVS-TEST-14, Phase H regression folded into B)
- `test_asset_url_includes_version_query_string` (Phase I fold-in)
- `test_polling_elimination.py`: measures `/api/metrics/history` request count over 60 s with WS connected, asserts zero after initial load

**Chaos (nightly-only, R2-04 D-40)**:
- Browser-bridge chaos: Playwright script randomly kills/restarts WS server, varies event rate, corrupts occasional envelope. Assert: no OOM, no freeze, chart data-points ≤ maxPoints.

**Latency tests** (recording-only in CI per R1-05 §4.28, R2-04 D-42):
- `@pytest.mark.latency_recording` marker. Strict assertions in local-only lane.
- `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` (renamed per R1-05 §4.3 to reflect drain-path measurement; rAF is disabled)

**Runtime**: Playwright runtime estimate 5-8 min due to dash_duo Selenium serialization (R1-05 §4.27). CI uses `pytest -n auto --dist=loadfile`.

### 5.5 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P5 | `phase-b-cascor-audit-prom-counters` | `feat(cascor): audit-event Prometheus counters (deferred from B-pre-a per R1-05 §4.14)` | backend-cascor | juniper-cascor main |
| P6 | `phase-b-canopy-drain-wiring` | `feat(canopy): ws_dash_bridge drain callbacks, Plotly extendTraces, connection indicator, Phase I cache bust, jitter-backoff lift (flag off)` | backend-canopy + frontend | juniper-canopy main |
| P7 | `phase-b-canopy-flag-flip` | `feat(canopy): default enable_browser_ws_bridge=True after staging soak` | ops + backend-canopy | juniper-canopy main (follow-up, NOT Phase B gate) |

Merge order: **P5 → P6 → 72 h staging soak → P7**.

**P7 is NOT a Phase B exit gate**. It is a one-line config PR landing after Phase B is in staging for 72 h and the P0 metric is verified.

**Version bumps**: canopy **minor** (new browser bridge + `/api/ws_latency` endpoint); cascor patch (audit Prom wiring).

### 5.6 Exit gate (measurable)

Ordered by dependency:

1. All 30+ unit tests + 8 dash_duo tests + 9 Playwright tests + AST lint green.
2. **`test_bandwidth_eliminated_in_ws_mode` green** (P0 motivator proof, Playwright).
3. `test_metrics_message_has_dual_format` green (Phase H regression gate).
4. **`canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` shows ≥90% reduction** vs pre-Phase-B baseline in staging, measured for 1 h post-deploy.
5. `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute.
6. "WebSocket health" dashboard panel renders p50/p95/p99 values in Grafana.
7. "Polling bandwidth" dashboard panel shows sustained reduction.
8. **72-hour memory soak** (R1-02 AC-24, R2-04 D-39): `canopy_ws_browser_heap_mb` p95 does not grow >20% over 72 hours.
9. `canopy_ws_browser_js_errors_total == 0` over the 72 h soak.
10. `canopy_ws_drain_callback_gen` advances at least once per minute for every buffer type.
11. `test_demo_mode_metrics_parity` green in **both fast and e2e lanes** (R1-05 §4.47).
12. `Settings.disable_ws_bridge=True` kill switch tested manually in staging; TTF ≤5 min.
13. `Settings.enable_browser_ws_bridge` flip-to-True PR reviewed by project lead.
14. Runbooks published: `ws-bridge-kill.md`, `ws-bridge-debugging.md`, `ws-memory-soak-test-procedure.md`.
15. NetworkVisualizer render tech verified in first commit of Phase B PR (R1-05 §5.1 unresolved → resolved at implementation time).
16. Metrics-presence test green (every Phase B metric exported via `/metrics` per R1-02 §10.6, R2-04 D-37).
17. CI cross-version lane green (canopy e2e against N-1 and N pinned SDK versions, R2-03 §15.5).
18. REST regression harness green (every endpoint in baseline list still serves per CCC-08).
19. AST lint `ring-bound-in-handler` green (R1-02 §5.4).
20. Mid-week deploy window honored (R1-02 §5.7, R2-04 D-61 — no Friday flag flip).

**Going/no-go** for P7 (flag flip):

21. 72 h in staging with `enable_browser_ws_bridge=True` manually set via env, no alerts firing.
22. `canopy_rest_polling_bytes_per_sec` sustained reduction ≥90% for the 72 h.
23. Browser memory p95 ≤ 500 MB over the 72 h.
24. Zero page-severity alerts fired in the canary window.

### 5.7 Rollback

| Scenario | Action | MTTR |
|---|---|---|
| **Fastest** | Env var `JUNIPER_DISABLE_WS_BRIDGE=true` on running canopy | 2 min |
| **Code flag flip** | Set `Settings.enable_browser_ws_bridge=False` in config, redeploy | 5 min |
| **Hardcoded ring cap reduction** | Developer edit + hotfix deploy | 1 h |
| **Full revert** | `git revert` P6, redeploy (requires cache-bust invalidation because assets moved in MVS-FE-16) | 30 min |
| **Per-user diagnostic hatch** | URL query `?ws=off` forces bridge off for specific user | instant |

### 5.8 NOT in this phase

- Phase C `set_params` adapter (read-only bridge in Phase B).
- Phase D control buttons (remain REST POST).
- Full rAF coalescing enabled (scaffold only).
- Phase F heartbeat application-level ping (jitter ships here; heartbeat is Phase F proper).
- Phase E per-client pump task backpressure (quick-fix from Phase 0-cascor only).
- Topology chunking (REST fallback handles large topologies).
- Full M-SEC-02 CSRF flow (Phase B-pre-b).
- CODEOWNERS for `_normalize_metric` (Phase H; regression test already folded in).
- `_normalize_metric` refactor (Phase H is test-only).
- NetworkVisualizer deep render migration (Phase B+1 contingent on render tech).

### 5.9 Decisions blocking entry

- **D-04, D-05, D-06, D-07, D-08, D-17, D-18, D-21, D-26, D-37, D-39, D-40, D-42, D-43, D-44, D-50, D-53, D-54**: all resolved per §2.

---

## 6. Phase B-pre-b: control-path security gate

### 6.1 Goal

Close the remaining M-SEC controls that gate Phase D's consumption of `/ws/control` from the browser: **Origin allowlist on `/ws/control`** (M-SEC-01 extension), **cookie-based session + CSRF first-frame** (M-SEC-02), **command rate limit** (M-SEC-05, single bucket 10 cmd/s), **opaque close-reason text** (M-SEC-06), **full audit logger with Prometheus counters** (M-SEC-07 extended, formerly M-SEC-12 folded per R1-05 §4.15), **adapter inbound validation** (M-SEC-11), **HMAC-derived adapter auth** (R1-05 §4.43), and **per-origin handshake cooldown** (R1-03 §6.2.7 with NAT-hostile escape hatch per R1-02 §13.10).

**Explicitly does NOT gate Phase B or Phase C.** Phase C uses `/ws/control` via the canopy adapter (API-key + HMAC auth, not browser auth), and Phase B does not consume `/ws/control` at all. Phase D is the one that directly exposes the control plane to the browser and is therefore gated on Phase B-pre-b being in **production ≥48 h**.

### 6.2 Entry gate

- [ ] Phase B in main (browser bridge working read-only).
- [ ] Phase A-SDK in main (any Phase C consumer can depend on SDK independent of B-pre-b).
- [ ] Session middleware presence verified: `grep -rn "SessionMiddleware" juniper-canopy/src/` (R1-05 §5.2). If absent, budget 0.5 day extra for adding it.
- [ ] `Settings.ws_backpressure_policy` not yet set to a Phase-E value.
- [ ] R2-04 decisions D-10, D-29, D-31, D-33 all resolved per §2.

### 6.3 Deliverables

#### 6.3.1 Functional

Mandatory in B-pre-b (R1-02 §4.2 + R1-03 §6.2 + R1-05 §4.35):

1. **M-SEC-01 (extended): Origin allowlist on `/ws/control`** (cascor + canopy). Uses helper extracted in B-pre-a.

2. **M-SEC-02: cookie session + CSRF first-frame**:
   - `SessionMiddleware` added to canopy if not present (day-1 verification).
   - `/api/csrf` REST endpoint returning `{csrf_token: ...}`. Mint-on-first-request with `secrets.token_urlsafe(32)`. Rotate on 1-hour sliding activity.
   - Dash template render-time embedding of `window.__canopy_csrf` (NOT localStorage — XSS exfiltration risk).
   - `websocket_client.js` sends `{type: "auth", csrf_token: ...}` as first frame after `onopen`.
   - Cookie attributes: `HttpOnly; Secure; SameSite=Strict; Path=/`.
   - `hmac.compare_digest` for all compares (constant-time).
   - Tokens rotate on session login/logout, every 1 hour sliding, server restart, any auth close.

3. **M-SEC-04 auth-timeout subpart**: `asyncio.wait_for(ws.receive_text(), timeout=5.0)` for first auth frame. Timeout → close 1008.

4. **M-SEC-05: command rate limit** — per-connection leaky bucket, 10 tokens, 10/s refill (single bucket per R1-05 §4.46, R2-04 D-33). Overflow → `{command_response, status: "rate_limited", retry_after: 0.3}`. Connection stays up.

5. **Per-origin handshake cooldown** (R1-03 §6.2.7): 10 rejections in 60 s → 5-minute IP block (return 429). Cooldown list cleared on canopy restart (R1-02 §13.10 NAT-hostile escape hatch).

6. **M-SEC-06: opaque close-reason text** — only canonical strings: `"Internal error"`, `"Invalid frame"`, `"Rate limited"`, `"Authentication failed"`, `"Forbidden"`, `"Too many connections"`.

7. **M-SEC-07 (full): audit logger** — Prometheus counters added (formerly deferred from B-pre-a per R1-05 §4.14). Rules from R0-02 §4.6 apply: session_id hash, scrubbing, CRLF escape (M-SEC-12 folded), 90-day retention, gzip rotation.

8. **M-SEC-11: adapter inbound validation** — canopy adapter parses inbound cascor frames via its own Pydantic envelope schema (`CascorServerFrame`, `extra="allow"`). Treats cascor as untrusted. Malformed → log + increment `canopy_adapter_inbound_invalid_total`.

9. **HMAC-derived adapter synthetic auth frame** (R1-05 §4.43, R2-04 D-29, R2-01 §7, R2-02 §7.3 — **this master plan applies the HMAC resolution to override R1-03 §18.12 header-skip**). Cascor handler derives `hmac.new(api_key.encode(), b"adapter-ws", hashlib.sha256).hexdigest()` and compares with `hmac.compare_digest`. **Why HMAC**: uniform handler logic, no branch in auth path. "Browsers can't set custom headers" is a fragile invariant to build security on.

10. **CI guardrail**: `juniper-deploy` compose validation refuses `ws_security_enabled=false` in production profile (IMPL-SEC-40). Also refuses `JUNIPER_WS_ALLOWED_ORIGINS=*` parse-time.

11. **Kill switch `Settings.disable_ws_control_endpoint: bool = False`**: hard-disables `/ws/control` for CSWSH emergency.

12. **One-resume-per-connection rule**: already landed in Phase 0-cascor; regression test cross-referenced here.

#### 6.3.2 Cross-cutting

**CCC-01**: `auth` first-frame shape with HMAC `csrf_token` (adapter); `command_id` on `/ws/control` inbound (browser side).

**CCC-02**: 10 new auth/security metrics fired:

| Metric | Type | Labels |
|---|---|---|
| `canopy_ws_auth_rejections_total` | Counter | `reason, endpoint` |
| `canopy_ws_rate_limited_total` | Counter | `command, endpoint` |
| `canopy_ws_command_total` | Counter | `command, status, endpoint` |
| `canopy_ws_auth_latency_ms` | Histogram | `endpoint` |
| `canopy_ws_handshake_attempts_total` | Counter | `outcome={accepted, origin_rejected, cookie_missing, csrf_invalid, per_ip_cap, cap_full}` — handshake funnel for incidents |
| `canopy_ws_per_origin_cooldown_active` | Gauge | — |
| `cascor_ws_audit_log_bytes_written_total` | Counter | — (alert on 2× projected 70 MB/day) |
| `canopy_csrf_validation_failures_total` | Counter | — |
| `cascor_ws_control_rate_limit_rejected_total` | Counter | — |
| `cascor_ws_control_idle_timeout_total` | Counter | — |
| `canopy_adapter_inbound_invalid_total` | Counter | — |

Alerts (ticket severity except `WSOriginRejection` which stays page):

- `WSAuditLogVolume2x` (ticket): `rate > 2 * baseline`.
- `WSRateLimited` (ticket): sustained non-zero.
- Per-origin cooldown active for >5 min (ticket).
- `WSOriginRejection` (page, already landed in B-pre-a but now covers `/ws/control` too).

**CCC-03 (kill switches)**:

| Switch | Who | MTTR | Validation |
|---|---|---|---|
| `JUNIPER_WS_SECURITY_ENABLED=false` | ops (dev only; prod CI refuses) | 5 min | `canopy_ws_auth_rejections_total` drops |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min | `canopy_training_control_total{transport="ws"}` drops to 0 |
| `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min | `canopy_ws_rate_limited_total` freezes |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min | No new writes |

CI tests for each flag.

**CCC-04**: two PRs (P8 → P9). Cascor first (P9 depends on P8 for HMAC path).

**CCC-05**: `test_adapter_synthetic_hmac_auth_frame_shape` contract test.

**CCC-06**: PR cites M-SEC-01, M-SEC-01b, M-SEC-02, M-SEC-04, M-SEC-05, M-SEC-06, M-SEC-07, M-SEC-10, M-SEC-11, RISK-15. Threat-model acknowledgement in PR description. Runbook `juniper-canopy/notes/runbooks/ws-auth-lockout.md` + `ws-cswsh-detection.md` published.

**CCC-07**: 6 new canopy settings (`ws_security_enabled`, `ws_allowed_origins`, `ws_rate_limit_enabled`, `ws_rate_limit_cps`, `ws_idle_timeout_seconds`, `disable_ws_control_endpoint`) in canonical table.

**CCC-08**: REST endpoints continue to serve; CSRF only gates WS, not REST.

**CCC-09**: `ws_security_enabled` is **permanent on** (default True, never flips to False in production — CI guardrail enforces).

**CCC-10**: no contribution.

### 6.4 Test coverage

**Unit + integration**:

- `test_csrf_required_for_websocket_start` (Playwright; Phase D regression gate pre-ships)
- `test_csrf_token_rotation_race` (R1-02 §4.2 item 16: token rotated mid-request; current completes, next upgrade uses new, old rejected)
- `test_first_frame_must_be_auth_type`
- `test_csrf_token_uses_hmac_compare_digest` (patch `hmac.compare_digest` to assert called)
- `test_session_cookie_httponly_secure_samesitestrict`
- `test_localStorage_bearer_token_not_accepted`
- `test_command_rate_limit_10_per_sec`
- `test_rate_limit_response_is_not_an_error_close`
- `test_second_resume_closes_connection_1003` (R1-05 §4.12 regression)
- `test_per_origin_cooldown_triggers_after_10_rejections`
- `test_audit_log_write_failure_fallback` (R1-02 item 17)
- `test_disable_ws_control_endpoint_kill_switch` (R1-02 §4.2 item 14)
- `test_canopy_adapter_sends_hmac_csrf_token_on_connect` (R1-05 §4.43)
- `test_cswsh_from_evil_page_cannot_start_training` (Playwright, full CSWSH regression)
- `test_opaque_close_reasons_no_human_readable_strings` (M-SEC-06)
- `test_session_middleware_exists_and_is_wired`
- `test_cascor_rejects_unknown_param_with_extra_forbid` (R1-05 §4.44)
- `test_canopy_adapter_inbound_malformed_frame_logged_and_counted`
- `test_audit_log_escapes_crlf_injection` (M-SEC-12 folded)

**Chaos** (nightly):
- Fuzz headers (hypothesis on origin strings): null bytes, CRLF, very long, Unicode.
- JSON fuzz (atheris) on `CommandFrame.model_validate_json` with 64 KB random payloads.
- Connection-churn chaos: 1000 open/close cycles; `_per_ip_counts` → 0.
- Resume-frame chaos: random `last_seq` / `server_instance_id` combos; no uncaught exceptions.

### 6.5 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P8 | `phase-b-pre-b-cascor-control-security` | `feat(security): /ws/control origin, rate limit, idle timeout, HMAC adapter auth (M-SEC-01/01b/05/10/11)` | backend-cascor + security | juniper-cascor main |
| P9 | `phase-b-pre-b-canopy-csrf-audit` | `feat(security): cookie session + CSRF first-frame + audit log prometheus + M-SEC-07 extended` | backend-canopy + security | juniper-canopy main |

Merge order: **P8 → P9**. P9's adapter HMAC depends on P8's cascor-side accept.

Version bumps: patch on both.

### 6.6 Exit gate (measurable)

Must be satisfied before ANY Phase D PR is eligible to merge:

1. All 18 unit/integration tests green.
2. Manual test: open `/ws/control` without first-frame CSRF auth → close 1008.
3. Manual test: open `/ws/control` from wrong origin → close 1008.
4. Manual test: send 11 commands in 900 ms → close 1013 on 11th.
5. `SessionMiddleware` detected in canopy stack.
6. Canopy adapter reconnects to cascor successfully after P8 + P9 deploy — HMAC handshake works.
7. `canopy_csrf_validation_failures_total` counter increments on rejected probe.
8. **48-hour staging soak** (R1-02 §4.2 item 19; every dashboard request's auth path changes).
9. Runbook `juniper-canopy/notes/runbooks/ws-auth-lockout.md` + `ws-cswsh-detection.md` published.
10. RISK-15 marked "in production" in risk-tracking sheet.
11. Kill switch `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` actually hard-disables (CI test green).
12. CSRF token rotation race test green.
13. Per-origin cooldown test green.
14. CI guardrail: `juniper-deploy` compose validation rejects `ws_security_enabled=false` in prod.
15. CSWSH probe test (`test_cswsh_from_evil_page_cannot_start_training`) green.

### 6.7 Rollback

| Switch | Who | MTTR |
|---|---|---|
| `JUNIPER_WS_SECURITY_ENABLED=false` | ops (dev only; prod CI refuses) | 5 min |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | ops | 5 min |
| `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | ops | 5 min |
| `JUNIPER_AUDIT_LOG_ENABLED=false` | ops | 5 min |
| Revert P9 then P8 | ops | 15 min |

### 6.8 NOT in this phase

- Per-command HMAC (M-SEC-02 point 3): deferred per R1-05 §4.11.
- Multi-tenant replay isolation: deferred per R1-05 §4.13.
- Two-bucket rate limit: deferred unless starvation observed.
- Per-user multi-tenant auth: single-tenant v1.

### 6.9 Decisions blocking entry

- **D-10** (positive-sense `ws_security_enabled` with CI guardrail): applied (overrides R1-05 §4.10)
- **D-29** (HMAC adapter auth): applied (overrides R1-03 §18.12)
- **D-31** (per-command HMAC deferred): applied
- **D-33** (single-bucket rate limit): applied

---

## 7. Phase C: set_params adapter (P2, feature-flagged)

### 7.1 Goal
Canopy adapter splits parameter updates into "hot" (11 params: `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `epochs_max`, `max_iterations`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`) and "cold" (`init_output_weights`, `candidate_epochs`). Hot route over `/ws/control` via `set_params` command with 1.0 s default timeout; cold stay on REST PATCH. Feature-flagged behind `use_websocket_set_params=False`. REST path permanent (R1-05 §4.23, R2-04 D-21).

### 7.2 Entry gate
- [ ] Phase A-SDK merged and on PyPI.
- [ ] Phase B in main and `enable_browser_ws_bridge=True` in staging.
- [ ] `juniper-ml/pyproject.toml` optional-extras pin bumped to new cascor-client version.
- [ ] Adapter `run_coroutine_threadsafe` usage verified (R1-05 §5.5).

### 7.3 Deliverables
- `cascor_service_adapter.py` refactor: `apply_params(**params)` splits → `_apply_params_hot()` (WS) + `_apply_params_cold()` (REST). Hot fires first, then cold. `lifecycle._training_lock` serializes server-side (RISK-03).
- Unclassified keys default to REST with WARNING log (R1-05 §4.44). Cascor-side `extra="forbid"` on `SetParamsRequest` catches unknown keys (defense in depth, R2-04 D-34).
- `_control_stream_supervisor` background task: backoff `[1, 2, 5, 10, 30]` s, reconnect forever, sends HMAC first-frame.
- Unconditional REST fallback on any WS failure.
- Debounce in Dash clientside callback only (R1-05 §4.24, R2-04 D-22), NOT in SDK.
- `canopy_set_params_latency_ms_bucket{transport, key}` histogram.
- `canopy_orphaned_commands_total{command}` counter.
- `canopy_control_stream_pending_size` gauge (R1-02 §6.4 bounded-map, max 256).
- Fail-loud startup classification summary (R1-02 §6.4): log INFO of hot/cold/unknown for every known param.

### 7.4 Cross-cutting
**CCC-02**: latency histograms by transport + orphaned-command counter. **CCC-03**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` (2 min MTTR). **CCC-05**: `test_canopy_adapter_exception_handling_matches_sdk_raises`, `test_canopy_adapter_defaults_unclassified_to_rest_with_warning`. **CCC-06**: runbook `ws-set-params-feature-flag.md`. **CCC-08**: REST `update_params` permanent; adapter falls back to REST on WS failure. **CCC-09**: `use_websocket_set_params` flag with 6 hard flip gates (R1-02 §6.1, R2-04 D-48). **CCC-10**: `canopy_set_params_latency_ms` histogram by transport enables the flip-gate comparison.

### 7.5 Test coverage
Unit: `test_apply_params_feature_flag_default_off`, `test_apply_params_hot_keys_go_to_websocket`, `test_apply_params_cold_keys_go_to_rest`, `test_apply_params_mixed_batch_split`, `test_apply_params_hot_falls_back_to_rest_on_ws_disconnect`, `test_apply_params_hot_falls_back_to_rest_on_timeout`, `test_apply_params_hot_surfaces_server_error_no_fallback`, `test_apply_params_unclassified_keys_default_to_rest_with_warning`, `test_apply_params_preserves_public_signature`, `test_apply_params_latency_histogram_labels_emitted`, `test_control_stream_supervisor_reconnects_with_backoff`, `test_control_stream_supervisor_shutdown_cancels_pending_futures`, `test_len_pending_returns_to_zero_after_failure_modes` (nightly), `test_cascor_rejects_unknown_param_with_extra_forbid`, `test_canopy_adapter_defaults_unclassified_to_rest_with_warning`. Chaos: inject random `Exception` in recv loop; assert pending map fully drained, supervisor restarts.

### 7.6 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P10 | `phase-c-canopy-set-params-adapter` | `feat(canopy): set_params hot/cold split, ws transport behind flag (P2)` | backend-canopy | juniper-canopy main |

Single canopy PR. Version bump: canopy **patch** (internal refactor; public API unchanged).

### 7.7 Exit gate
1. All 15+ unit tests green. Coverage ≥90% on new code.
2. With flag off: `canopy_set_params_latency_ms_bucket{transport="rest"}` has data; `transport="ws"` empty.
3. With flag on (staging): both transport labels have data; `transport="ws"` p95 is lower than `transport="rest"` p95.
4. Manual test: drag slider with flag on, updates arrive within 1 s.
5. Manual test: kill cascor mid-drag, slider change applies via REST fallback within 2 s.
6. Runbook `ws-set-params-feature-flag.md` published.

**Flag-flip criteria** (R1-02 §6.1, R2-04 D-48, 6 hard gates):
1. ≥7 days production data on the WS code path.
2. p99 latency delta ≥50 ms (REST - WS); if smaller, flip provides no user-visible win — **do not flip**.
3. Zero orphaned commands during canary week.
4. Zero correlation-map leaks (nightly `test_len_pending_returns_to_zero_after_failure_modes`).
5. Canary soak ≥7 days.
6. User-research signal: optional; skipped by default (R1-05 §4.32, R2-04 D-45).

### 7.8 Rollback
| Switch | MTTR |
|---|---|
| `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | 2 min |
| `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1` (force REST fallback via tight timeout) | 5 min |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` (Phase C falls through to REST) | 5 min |

### 7.9 NOT in this phase
- SDK-level retries (R1-05 §4.22). SDK reconnect queue (R1-05 §4.42). REST path deprecation (R1-05 §4.23). Two-bucket rate limit. Frontend control buttons (Phase D).

---

## 8. Phase D: control buttons

### 8.1 Goal
Route browser `start`/`stop`/`pause`/`resume`/`reset` training-control clicks through `/ws/control` via `window.cascorControlWS.send({command, command_id: uuidv4()})`. REST POST at `/api/train/{command}` remains first-class forever. Per-command timeouts per source doc §7.32: `start: 10 s`, `stop/pause/resume: 2 s`, `set_params: 1 s`, `reset: 2 s`.

### 8.2 Entry gate
- [ ] **Phase B-pre-b in production ≥48 h** (NOT just staging; this is the CSRF/Origin gate for the browser control plane — R2-02 §18.8, R2-04 §4.7).
- [ ] Phase B in main (browser bridge exists; `window.cascorControlWS` available).
- [ ] Zero CSRF-related incidents during the 48 h production soak of B-pre-b.

### 8.3 Deliverables
- Clientside callback on each button routes to `window.cascorControlWS.send(...)` if WS connected; REST POST if not.
- Per-command client-side `command_id` correlation map (per-connection scoped, R1-05 §4 D10).
- Orphaned-command pending-verification UI: button disabled while command in-flight; resolves on `command_response` OR matching `state` event (RISK-13).
- Feature flag `enable_ws_control_buttons: bool = False` (R1-02 §7.1, R2-04 D-49).
- `canopy_training_control_total{command, transport}` counter.
- `canopy_orphaned_commands_total{command}` counter (reused from Phase C).

### 8.4 Test coverage
- `test_training_button_handler_sends_websocket_command_when_connected`
- `test_training_button_handler_falls_back_to_rest_when_disconnected`
- `test_rest_endpoint_still_returns_200_and_updates_state` (GAP-WS-06 regression gate)
- Playwright: `test_start_button_uses_websocket_command`, `test_command_ack_updates_button_state`, `test_disconnect_restores_button_to_disabled`, `test_csrf_required_for_websocket_start`, `test_orphaned_command_resolves_via_state_event`
- `test_set_params_echoes_command_id` (Phase G cross-reference)

### 8.5 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P11 | `phase-d-cascor-control-commands` | `feat(cascor): /ws/control command dispatch + per-command timeouts` | backend-cascor | juniper-cascor main |
| P12 | `phase-d-canopy-button-ws-routing` | `feat(canopy): training-control buttons route via /ws/control with REST fallback` | frontend + backend-canopy | juniper-canopy main |

Merge order: **P11 → P12**. Version bumps: both patch.

### 8.6 Exit gate
1. All Playwright tests green.
2. `test_csrf_required_for_websocket_start` green.
3. 24 h staging soak with zero orphaned-command incidents.
4. 48 h canary cohort soak with zero orphaned-command reports (R1-02 §7.1).
5. REST endpoints still receive traffic from non-browser consumers (verify via access logs).
6. `docs/REFERENCE.md` documents both REST and WS training control APIs.
7. Mid-week deploy for button-flag flip.

### 8.7 Rollback
| Switch | MTTR |
|---|---|
| `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | 5 min |
| `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` (CSWSH emergency) | 5 min |

### 8.8 NOT in this phase
- `set_params` routing (Phase C). Full backpressure (Phase E). Two-bucket rate limit.

---

## 9. Phase E: backpressure and disconnection

### 9.1 Goal
Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded per-client queues + backpressure policy matrix. Default: `drop_oldest_progress_only` (R1-05 §4.36, R2-04 D-19 — **overrides source doc default `block`**).

### 9.2 Entry gate
- [ ] Phase 0-cascor in main (0.5 s quick-fix is the fallback if Phase E rolls back).
- [ ] **Ship only if production telemetry from Phase B shows RISK-04/11 triggering.** If 0.5 s quick-fix suffices, defer Phase E (R1-04 §12.3 conditional). The decision is made based on `cascor_ws_broadcast_send_duration_seconds` p95 and `cascor_ws_broadcast_timeout_total` rate in production.

### 9.3 Deliverables
- Per-client `_ClientState` with dedicated `pump_task` and bounded `send_queue` (configurable via `Settings.ws_per_client_queue_size`, default 256).
- Policy matrix:

| Event type | Queue size | Overflow policy | Rationale |
|---|---:|---|---|
| `state` | 128 | close(1008) | Terminal-state-sensitive |
| `metrics` | 128 | close(1008) | Drops cause chart gaps |
| `cascade_add` | 128 | close(1008) | Each event is a growth step |
| `candidate_progress` | 32 | drop_oldest | Coalesceable |
| `event` (training_complete) | 128 | close(1008) | Terminal-state-sensitive |
| `command_response` | 64 | close(1008) | Client waits for it |
| `pong` | 16 | drop_oldest | Client can re-ping |

- Per-type event classification asserted via test (`test_event_type_classification_for_backpressure_policy` — R1-02 §9.8) ensuring every event type from `messages.py` maps to an explicit policy bucket.
- `cascor_ws_dropped_messages_total{reason, type}` counter.
- `cascor_ws_slow_client_closes_total` counter.

### 9.4 Test coverage
- `test_slow_client_does_not_block_other_clients`, `test_slow_client_send_timeout_closes_1008_for_state`, `test_slow_client_progress_events_dropped`, `test_drop_oldest_queue_policy`, `test_backpressure_default_is_drop_oldest_progress_only` (R1-05 regression gate), `test_event_type_classification_for_backpressure_policy`, `test_block_policy_still_works_when_opted_in`.

### 9.5 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P13 | `phase-e-cascor-backpressure-pump-tasks` | `feat(cascor): per-client pump tasks + bounded queues + policy matrix (GAP-WS-07 full fix)` | backend-cascor | juniper-cascor main |

Version bump: cascor **minor** (new `ws_backpressure_policy` setting).

### 9.6 Exit gate
1. All 7 tests green.
2. Load test: 50 clients, 1 slow with 2 s delay, 49 fast receive all events within 200 ms p95.
3. `cascor_ws_dropped_messages_total{policy="drop_oldest_progress_only", reason="queue_full"}` visible after load test.
4. 48 h staging soak with zero `WSStateDropped` alerts.
5. Runbook `juniper-cascor/notes/runbooks/ws-slow-client-policy.md` published.

### 9.7 Rollback
`JUNIPER_WS_BACKPRESSURE_POLICY=block` → reverts to old behavior; RISK-04 returns (intentional trade-off documented). 5 min MTTR.

---

## 10. Phase F: heartbeat and reconnect jitter refinement

### 10.1 Goal
Add application-level `ping`/`pong` heartbeat to detect TCP half-open faster than uvicorn framework level (GAP-WS-12). Jitter formula already in Phase B; this phase adds heartbeat contract + reconnect-cap lift finalization.

### 10.2 Entry gate
- [ ] Phase B in main.

### 10.3 Deliverables
- Client sends `{type: "ping", ts: <float>}` every 30 s; server replies `{type: "pong"}`.
- Client closes if no pong within 5 s.
- Integrates with M-SEC-10 idle timeout: heartbeat resets idle timer.
- Jitter formula explicit: `delay = Math.random() * Math.min(60_000, 500 * 2 ** Math.min(attempt, 7))`.
- `test_reconnect_backoff_has_jitter` (R1-02 §9.9 NaN/Infinity regression).

### 10.4 Test coverage
- `test_heartbeat_ping_pong_reciprocity`, `test_dead_connection_detected_via_missing_pong`, `test_reconnect_attempt_uncapped`, `test_jitter_formula_no_nan_delay`, `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect`.

### 10.5 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P14 | `phase-f-heartbeat-jitter` | `feat(ws): application-level heartbeat, uncapped reconnect, jitter formula` | frontend + backend-cascor | juniper-cascor + juniper-canopy main |

### 10.6 Exit gate
1. All 5 tests pass.
2. Manual test: client behind packet-dropping firewall; dead connection detected within 40 s.
3. 48 h staging soak: no NaN delays, no reconnect storms.

### 10.7 Rollback
Revert P14 (10 min). Or `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` (10 min; users hard-refresh).

---

## 11. Phase G: end-to-end correctness suite

### 11.1 Goal
Add cascor-side integration tests exercising `/ws/control` `set_params` via FastAPI `TestClient.websocket_connect()` (no SDK dependency). Assert wire contract: `command_id` echo, whitelist filtering, per-frame size cap, concurrent correlation, epoch-boundary application, Origin regression, rate-limit regression.

### 11.2 Entry gate
- [ ] Phase 0-cascor in main.
- [ ] Phase B-pre-b in main (Origin + rate-limit guards exist to regression-test).

### 11.3 Deliverables (test list)
- `test_set_params_via_websocket_happy_path`
- `test_set_params_whitelist_filters_unknown_keys`
- `test_set_params_init_output_weights_literal_validation`
- `test_set_params_oversized_frame_rejected`
- `test_set_params_no_network_returns_error`
- `test_unknown_command_returns_error` (GAP-WS-22 regression)
- `test_malformed_json_closes_with_1003` (GAP-WS-22 regression)
- `test_set_params_origin_rejected` (M-SEC-01b regression)
- `test_set_params_unauthenticated_rejected`
- `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05 regression)
- `test_set_params_bad_init_output_weights_literal_rejected`
- `test_set_params_concurrent_command_response_correlation` (R1-05 §4.29)
- `test_set_params_during_training_applies_on_next_epoch_boundary` (R1-05 §4.29; ack vs effect validation)
- **`test_set_params_echoes_command_id`** (R1-05 §4.2 mandatory gate for SDK consumer)
- `test_ws_control_command_response_has_no_seq` (R1-05 §4.17; already in Phase 0-cascor, cross-referenced)

Tests marked `@pytest.mark.critical` — run in `fast` lane on every PR to cascor or cascor-client (R1-02 §7.4).

### 11.4 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P15 | `phase-g-cascor-set-params-integration` | `test(cascor): /ws/control set_params integration suite + contract lane` | backend-cascor | juniper-cascor main |

Version bump: cascor **patch** (test-only).

### 11.5 Exit gate
1. All 15 tests pass. 2. `pytest -m contract` lane green in both cascor and canopy CI.

### 11.6 Rollback
n/a (test-only).

---

## 12. Phase H: production rollout guard for nested-vs-flat metric format

### 12.1 Goal
Lock in the dual metric format contract (flat keys and nested keys both present on `metrics` events) with regression test + CODEOWNERS entry + pre-commit hook. Document every consumer of `_normalize_metric` output. **NO removal of any format in this migration.** (R1-02 §1.2 principle 7, R2-01 §18.8.)

### 12.2 Entry gate
- [ ] Phase B in main (MVS-TEST-14 dual-format regression test already landed).
- [ ] CODEOWNERS file present in `juniper-canopy/.github/CODEOWNERS`.

### 12.3 Deliverables
- Regression tests: `test_normalize_metric_produces_dual_format`, `test_normalize_metric_nested_topology_present`, `test_normalize_metric_preserves_legacy_timestamp_field`.
- Wire-level companion `test_metrics_message_has_dual_format` already folded into Phase B.
- Consumer audit document `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`.
- **CODEOWNERS entry** (R1-02 §7.5, R1-05 §4.41, R2-04 D-27): any PR touching `_normalize_metric` or files that import it requires project-lead review. **Hard merge gate.**
- **Pre-commit hook** (R1-02 §7.5): refuses commits removing nested-format keys from normalize output (static check).

### 12.4 Pull request plan
| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| P16 | `phase-h-normalize-metric-audit` | `docs(audit): normalize_metric consumer audit + CODEOWNERS rule + regression gate (RISK-01)` | backend-canopy | juniper-canopy main |

Version bump: canopy **patch**.

### 12.5 Exit gate
1. Regression tests green. 2. CODEOWNERS rule enforced (test PR that touches `_normalize_metric.py` without owner review is blocked). 3. Consumer audit doc reviewed and merged. 4. Pre-commit hook installed.

### 12.6 Rollback
None needed (test-only + doc phase). If future PR proposes removal, re-run Phase H scenario analysis.

---

## 13. Phase I: asset cache busting (folded into Phase B)

This phase is **folded into Phase B** per R1-05 §6.2 and R1-01 §2.3. It does not ship as a standalone phase. Documented here for rollback reference.

**Deliverable**: `assets_url_path` with content-hash query string in canopy's Dash configuration. Browsers pick up new JS without hard refresh. Verified via `test_asset_url_includes_version_query_string` (in Phase B Playwright suite).

**Rollback**: `git revert` the cache-bust commit in P6. Browsers may see stale JS briefly (usually harmless). 10 min TTF.

---

## 14. Master kill-switch matrix

Consolidated from R2-01 §14, R2-02 §5.4, R2-03 CCC-03 §5.4 and refined. Every phase represented. Every switch has a CI test proving the flip has the claimed effect (R1-02 §1.2 principle 2). Every switch is config-only (env var + process restart, ≤5 min MTTR).

| Phase | Switch (env var) | Default | Who | MTTR | Validation metric | CI test |
|---|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 1024 | ops | 5 min | `cascor_ws_resume_requests_total{outcome=out_of_range}` spike | `test_replay_buffer_size_env_override` |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | 0.5 | ops | 5 min | `cascor_ws_broadcast_timeout_total` spike | `test_send_timeout_env_override` |
| 0-cascor | Rolling restart | — | ops | 10 min | New UUID → all clients snapshot-refetch | — |
| 0-cascor | Revert PR | — | ops | 15 min | Old clients ignore `seq` (additive field) | — |
| A (SDK) | Downgrade cascor-client pin | — | ops | 15 min | Canopy uses prior version | `pip index versions` |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 | ops | 5 min | `canopy_ws_per_ip_rejected_total` → 0 | `test_per_ip_cap_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | `[]` | ops | 5 min | `canopy_ws_origin_rejected_total` drops | `test_origin_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=*` | — | — | — | **REFUSED BY PARSER** (non-switch) | `test_allowed_origins_wildcard_refused` |
| B-pre-a | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` | 120 | ops | 5 min | Idle timeout disabled | `test_idle_timeout_env_override` |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | True | ops | 5 min | No new audit writes | `test_audit_log_env_override` |
| B-pre-b | `JUNIPER_WS_SECURITY_ENABLED=false` | True | ops (dev) | 5 min | Auth rejections drop (prod CI refuses) | `test_ws_security_env_override` |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | False | ops | 5 min | WS control traffic → 0 | `test_disable_ws_control_endpoint` |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | True | ops | 5 min | Rate-limit counter freezes | `test_rate_limit_env_override` |
| B | `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false` | False → True | ops | 5 min | Polling bytes rise to baseline | `test_enable_browser_ws_bridge_env_override` |
| B | `JUNIPER_DISABLE_WS_BRIDGE=true` | False | ops | 5 min | Same (permanent kill switch) | `test_disable_ws_bridge_env_override` |
| B | Hardcoded ring-cap reduction | — | dev | 1 h | Browser heap drops in soak | — |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | False | ops | 2 min | WS transport count freezes | `test_use_websocket_set_params_env_override` |
| C | `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1` | 1.0 | ops | 5 min | Tight timeout forces REST fallback | `test_ws_set_params_timeout_env_override` |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | False | ops | 5 min | REST transport rises | `test_enable_ws_control_buttons_env_override` |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | False | ops | 5 min | Control WS → 0 (CSWSH emergency) | (reused from B-pre-b) |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | `drop_oldest_progress_only` | ops | 5 min | Dropped-messages counter → 0 | `test_ws_backpressure_policy_env_override` |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | False | ops | 10 min | Reconnect counter freezes | `test_disable_ws_auto_reconnect_env_override` |
| H | `git revert` normalize-metric PR | — | ops | 10 min | Shape hash matches pre-H | — |
| I | `git revert` cache-busting commit | — | ops | 10 min | Asset URL query reverts | — |

**Meta-rule** (R1-02 §8, R2-03 CCC-03 §5.3 item 5): every kill switch in this table has a CI test that flips the switch and verifies the validation metric moves. If the test is missing, the switch does not count and the phase does not ship.

**Kill switch documentation**: committed as `juniper-canopy/notes/runbooks/ws-kill-switches.md` and `juniper-cascor/notes/runbooks/ws-kill-switches.md` — one per repo, kept in sync with pytest parametrize list by a codegen script (R2-03 CCC-03 §5.5 item 7).

**Kill switch drills**: during every phase soak, every kill switch is flipped once and TTF measured. If any TTF >5 min, phase does not proceed to production (R1-02 §13.7, R2-04 D-53).

**Abandon trigger** (R1-02 §9.4): if a kill-switch flip does not produce the expected metric change within 60 s, escalate. If two switches in sequence fail, **halt the migration for re-planning**. This is the safety net of safety nets.

---

## 15. Master risk register

16 entries covering RISK-01 through RISK-16 from source doc §10, consolidated from R2-01 §15 (R1-03 §14 base + R1-02 mitigations + R1-05 resolutions), with R2-03 CCC cross-cutting risk amplifications.

| ID | Description | Sev/Lik | Phase | Kill switch | TTF | Key mitigation |
|---|---|---|---|---|---|---|
| 01 | Dual metric format removed aggressively | High/Med | H | `git revert` | 5-10 min | Phase H regression tests, CODEOWNERS hard gate, pre-commit hook, wire-level test folded into Phase B |
| 02 | Phase B clientside_callback hard to debug remotely | Med/High | B | `disable_ws_bridge=true` | 5 min | `canopy_ws_drain_callback_gen` gauge, `canopy_ws_browser_js_errors_total` counter, 72 h staging soak, feature flag default False |
| 03 | Phase C REST+WS ordering race | Med/Low | C | `use_websocket_set_params=false` | 2 min | Disjoint hot/cold sets + `lifecycle._training_lock`, fail-loud startup classification, bounded correlation map |
| 04 | Slow-client blocks broadcasts | Med/Med | E (0-cascor quick-fix) | `ws_backpressure_policy=close_slow` | 5 min | 0.5 s send timeout quick-fix, full per-client pump task in Phase E |
| 05 | Playwright fixture misses real-cascor regression | Med/Med | B, D | n/a (fix the test) | — | **Nightly** smoke against real cascor (R1-02 amplification from R1-03 weekly), `test_fake_cascor_message_schema_parity` contract test |
| 06 | Reconnection storm after cascor restart | Low/Med | F | `disable_ws_auto_reconnect=true` | 10 min | Full jitter (ships with Phase B), pre-restart jitter check |
| 07 | 50-connection cap hit by multi-tenant | Low/Low | n/a | raise `ws_max_connections` | 10 min | Operator-tunable, per-IP cap 5 |
| 08 | Demo mode parity breaks | Low/Med | B | revert PR | 10 min | `test_demo_mode_metrics_parity` blocker in both fast and e2e lanes |
| 09 | Phase C unexpected user-visible behavior | Low/Med | C | `use_websocket_set_params=false` | 2 min | Feature flag default False, 6 hard flip gates, ≥7-day canary |
| 10 | Browser memory exhaustion from unbounded chart data | Med/High | B | `disable_ws_bridge=true` | 5 min | `Plotly.extendTraces(maxPoints=5000)`, ring-bound in handler (R1-02 §5.4 AST lint), 72 h staging soak |
| 11 | Silent data loss via drop-oldest broadcast queue | High/Low | E | `ws_backpressure_policy=block` | 5 min | `drop_oldest_progress_only` (only progress events dropped), per-type assertion test, `WSStateDropped` page alert |
| 12 | Background tab memory spike on foreground | Low/Med | B | same as RISK-10 | 5 min | Cap-in-handler ensures bound independent of drain rate |
| 13 | Orphaned commands after timeout | Med/Med | B, C, D | reduce timeouts | 5 min | `command_id` per-command correlation, pending-verification UI, resolve via `command_response` OR `state` event |
| 14 | Cascor crash mid-broadcast leaves clients inconsistent | Low/Low | B | rolling restart | 10 min | `server_instance_id` forces full REST resync, `WSSeqCurrentStalled` page alert |
| 15 | **CSWSH attack exploits missing Origin validation** | **High/Med** | B-pre-a/b | `disable_ws_control_endpoint=true` | 5 min | M-SEC-01/01b + M-SEC-02, `WSOriginRejection` page alert, CODEOWNERS on websocket/*.py |
| 16 | Topology message >64 KB silently fails | Med/Med | B-pre-a | REST fallback for topology | 5 min | Size caps surface it, `canopy_ws_oversized_frame_total` alert, REST `/api/topology` fallback preserved |

---

## 16. Cross-cutting concerns summary

The 10 CCCs from R2-03, with phase touchpoints integrated throughout §3-§13 above. This section lists each CCC's **owning role** (assigned per R2-03 §14.12 recommendation) and its **key acceptance criteria** — the per-phase details are in the individual phase sections.

| # | CCC | Owner | Key acceptance criteria |
|---|---|---|---|
| CCC-01 | Wire-format schema evolution | backend-cascor lead | `command_id` rename enforced; additive-only contract tested; rollout state matrix documented in Phase 0-cascor PR |
| CCC-02 | Observability stack | backend-canopy lead | Metric-before-behavior enforced via CI; SLO panel deployed; page alerts test-fired; metrics-presence test in `fast` lane |
| CCC-03 | Kill switch architecture | security lead | Every phase ≥1 switch; every switch has CI test; kill-switch drills in staging; MTTR ≤5 min |
| CCC-04 | Cross-repo version pinning | project lead | Merge order binding; PyPI propagation tested; TestPyPI prerelease functional; cross-version CI lane green; Helm chart bumps match app semver |
| CCC-05 | Contract testing | backend-cascor lead | `contract` marker in all 3 repos; 11 contract tests per R2-03 inventory; every PR lane; inline-literal rule (no cross-repo fixtures) |
| CCC-06 | Documentation as deliverable | project lead | 11 runbooks per inventory; PR template enforces IDs/threat-model-ack/kill-switch/rollback; CODEOWNERS for all 7 critical paths; post-mortem template before Phase B |
| CCC-07 | Configuration management | ops lead | Canonical settings table (§2.9) in sync with Pydantic Settings classes; CI checks for undocumented settings, wildcard origin refusal, prod compose guardrail |
| CCC-08 | Backwards compatibility | project lead | REST regression harness in `fast` lane; golden shape file; kill-switch tests assert REST post-flip; deprecation policy "no deprecation ever" in source doc |
| CCC-09 | Feature flag lifecycle | project lead | Flag inventory (§2.8) committed; every flag has lifecycle; flip is separate PR with criteria; removal NOT in this migration |
| CCC-10 | Latency instrumentation | frontend lead | `emitted_at_monotonic` in Phase 0-cascor; full pipe in Phase B; Grafana panel; buckets {50..5000} ms; SLO promotion PR after ≥1 week |

---

## 17. Decision matrix with applied defaults

This section lists the R2-04 decisions with their applied defaults in this master plan. Stakeholders should note any decision they wish to override — the default applies unless overridden before the relevant phase starts.

**High cost-of-deferral decisions** (all applied):

| ID | Decision | Applied default | Source |
|---|---|---|---|
| D-02 | Correlation field name | **`command_id`** | R1-05 §4.2 |
| D-11 | Phase 0-cascor carve-out | **carve out** | R1-05 §4.19 |
| D-17 | Phase B feature flag default | **flag-off** | R1-02 §5.2 |
| D-19 | Phase E backpressure default | **`drop_oldest_progress_only`** | R1-05 §4.36 |
| D-23 | Phase B-pre split | **split a+b** | R1-05 §4.35 |

**Medium cost-of-deferral decisions** (all applied):

| ID | Decision | Applied default |
|---|---|---|
| D-03 | `command_response` seq | **no** |
| D-10 | Security flag naming | **positive-sense `ws_security_enabled`** |
| D-18 | Permanent kill switch | **add** |
| D-29 | Adapter auth | **HMAC** |
| D-35 | Replay buffer size | **1024** |
| D-38 | Phase 0-cascor soak | **72 h** |
| D-39 | Phase B soak | **72 h** |
| D-48 | Phase C flip criteria | **enumerated hard gates** |
| D-49 | Phase D feature flag | **add** |
| D-53 | Kill-switch MTTR tested | **test in staging** |

All 55 R2-04 decisions + 7 implicit decisions (D-56..D-62) have been applied. Full decision detail is in R2-04 §3. Stakeholders needing to override any decision should reference R2-04 directly.

---

## 18. Cross-repo merge sequence

Canonical ordered PR list across all repos. Flattened from R2-01 §16, R2-02 §16, R2-03 CCC-04 §6.3.

| Order | PR | Branch | Repo | Phase | Blocking next? |
|---:|---|---|---|---|---|
| 1 | P2 | `phase-a-sdk-set-params` | juniper-cascor-client | A-SDK | Yes (PyPI publish → 2-5 min wait) |
| 2 | P1 | `phase-0-cascor-seq-replay-resume` | juniper-cascor | 0-cascor | Yes (Phase B prereq) |
| 3 | P3 | `phase-b-pre-a-cascor-security` | juniper-cascor | B-pre-a | Yes (P4 references) |
| 4 | P4 | `phase-b-pre-a-canopy-security` | juniper-canopy | B-pre-a | Yes (Phase B prereq) |
| — | — | — | — | — | **72 h staging soak (Phase 0-cascor) + 24 h soak (B-pre-a)** |
| 5 | P5 | `phase-b-cascor-audit-prom-counters` | juniper-cascor | B | No |
| 6 | P6 | `phase-b-canopy-drain-wiring` | juniper-canopy | B | Yes (Phase C prereq) |
| — | — | — | — | — | **72 h staging soak (Phase B flag-on)** |
| 7 | P7 | `phase-b-canopy-flag-flip` | juniper-canopy | B | Yes (Phase C iterates on flag=on) |
| — | — | — | — | — | **P0 metric validated — mission accomplished** |
| 8 | P15 | `phase-g-cascor-set-params-integration` | juniper-cascor | G | No (parallel to C) |
| 9 | P8 | `phase-b-pre-b-cascor-control-security` | juniper-cascor | B-pre-b | Yes (P9 and Phase D) |
| 10 | P9 | `phase-b-pre-b-canopy-csrf-audit` | juniper-canopy | B-pre-b | Yes (Phase D prereq) |
| — | — | — | — | — | **48 h production soak (B-pre-b)** |
| 11 | P10 | `phase-c-canopy-set-params-adapter` | juniper-canopy | C | No (independent of D) |
| 12 | P11 | `phase-d-cascor-control-commands` | juniper-cascor | D | Yes (P12 depends) |
| 13 | P12 | `phase-d-canopy-button-ws-routing` | juniper-canopy | D | No |
| 14 | P13 | `phase-e-cascor-backpressure-pump-tasks` | juniper-cascor | E | No (conditional on telemetry) |
| 15 | P14 | `phase-f-heartbeat-jitter` | juniper-cascor + canopy | F | No |
| 16 | P16 | `phase-h-normalize-metric-audit` | juniper-canopy | H | No |
| — | — | `juniper-ml` extras pin bump | juniper-ml | — | One-line follow-up after each SDK bump |

**Critical path**: P2 → P1 → P3 → P4 → (soak) → P6 → (soak) → P7. That's the "ship the P0 win" spine.

**Parallel lanes**: Phase A-SDK (P2) ∥ Phase 0-cascor (P1) ∥ Phase B-pre-a (P3/P4). Phase G (P15) ∥ Phase C (P10) ∥ Phase B-pre-b (P8/P9). Phases E/F/H are all independent of each other.

**Merge strategy**: squash-merge (linear history). Use GitHub merge queue where available.

**Branch naming**: `ws-migration/phase-<letter>-<slug>` per R1-03 §17.1.

**Worktree naming** (per Juniper parent CLAUDE.md): `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>` in `/home/pcalnon/Development/python/Juniper/worktrees/`.

**Version bumps**:

| Repo | Phase | Bump |
|---|---|---|
| juniper-cascor-client | A | minor |
| juniper-cascor | 0-cascor | minor |
| juniper-cascor | B-pre-a/b | patch |
| juniper-cascor | E | minor |
| juniper-cascor | G | patch (test-only) |
| juniper-canopy | B-pre-a/b | patch |
| juniper-canopy | B | minor |
| juniper-canopy | C | patch |
| juniper-canopy | D | patch |
| juniper-canopy | H | patch |
| juniper-ml | per SDK bump | patch |

Helm chart `version` + `appVersion` match app semver (user memory: `project_helm_version_convention.md`).

**TestPyPI prerelease**: Phase A publishes to TestPyPI on PR; canopy PRs install from TestPyPI and run e2e before PyPI promotion.

**Cross-version CI lane** (R2-03 §15.5 new): canopy e2e runs against both N-1 and N pinned SDK versions; both must pass.

---

## 19. Effort summary

| Phase | Optimistic (days) | Expected (days) | Pessimistic (days) | Notes |
|---|---:|---:|---:|---|
| Phase 0-cascor | 1.5 | 2.0 | 3.0 | Pessimistic if `_pending_connections` design hits async race bugs |
| Phase A-SDK | 0.5 | 1.0 | 1.5 | Pessimistic if correlation-map bounding needs iteration |
| Phase B-pre-a | 0.5 | 1.0 | 1.5 | Pessimistic if audit logger integration surfaces logger name collisions |
| Phase B | 3.0 | 4.0 | 5.0 | Pessimistic if NetworkVisualizer turns out to be Plotly (+1 day) |
| Phase B-pre-b | 1.0 | 1.5 | 2.0 | Pessimistic if SessionMiddleware doesn't exist (+0.5 day) |
| Phase C | 1.5 | 2.0 | 3.0 | Pessimistic if concurrent-correlation test surfaces race bugs |
| Phase D | 0.75 | 1.0 | 1.5 | Pessimistic if orphaned-command UI state management is finicky |
| Phase E | 0.75 | 1.0 | 1.5 | Conditional on telemetry; may not ship |
| Phase F | 0.25 | 0.5 | 1.0 | Small phase; low variance |
| Phase G | 0.25 | 0.5 | 0.75 | Tests only; low variance |
| Phase H | 0.5 | 1.0 | 1.5 | Audit document can grow |
| Phase I | 0.1 | 0.25 | 0.5 | Folded into B; counted separately for rollback |
| **Total** | **10.6** | **15.75** | **22.25** | — |

**R2-02 expected total 15.75 days vs R1-05's 13.5**: the delta is +2.25 days distributed across Phase A (+0.5 for two-phase registration), Phase B (+0.5 for NetworkVisualizer minimum wire), Phase C (+0.5 for HMAC adapter wiring), Phase B-pre-a (+0.25 for audit logger skeleton), Phase B-pre-b (+0.5 for HMAC end-to-end).

**Calendar translation**: 15.75 engineering days × single-developer lane → ~3 weeks one-person calendar, or **~4.5 weeks with 48-72 h soak windows** between B, B-pre-b, D stages. Matches R1-05 §4.40's "~4.5 weeks" target.

**Parallelism savings**: Phase A-SDK (1.0 d), Phase 0-cascor (2.0 d), Phase B-pre-a (1.0 d) all run in parallel → critical-path compression of ~2 days vs serial. Similarly Phase B-pre-b (1.5 d) ∥ Phase B (4.0 d) compresses ~1.5 days.

---

## 20. R2 reconciliation log

This section documents where the 4 R2 proposals contradicted each other and how this master plan resolved the disagreement.

### 20.1 Replay buffer default size (R2-01 = 1024, R2-02 = 1024, R2-03 CCC-07 = 256, R2-04 = 1024)

**Conflict**: R2-03's canonical settings table (§9.3 item 7) lists `ws_replay_buffer_size` default as **256** for both dev and prod, citing R1-02 §3.2 safety-first. R2-01, R2-02, and R2-04 all use **1024** as the production default, matching R1-05 §6.1 and R0-03.

**Resolution**: **1024 in production, configurable**. R2-03's 256 was an error in CCC-07's table that conflated R1-02's staging-testing recommendation with the production default. R1-02 itself says "256 to exercise the fallback path" which is a testing hygiene concern, not a production default. Operators can set `JUNIPER_WS_REPLAY_BUFFER_SIZE=256` in staging. The chaos test `test_replay_out_of_range_via_deliberate_overflow` exercises the path explicitly.

**Winner**: R2-01 / R2-02 / R2-04

### 20.2 Security flag naming: positive-sense vs negative-sense (R2-01 = positive, R2-02 = negative, R2-03 = positive, R2-04 = positive)

**Conflict**: R2-02 (§1.2 settled positions) preserved R1-05 §4.10's negative-sense `disable_ws_auth`. R2-01 (§18.2), R2-03 (§15.3), and R2-04 (§7.1 D-10) all independently argue for positive-sense `ws_security_enabled`.

**Resolution**: **Positive-sense `ws_security_enabled: bool = True`** with CI guardrail refusing `false` in production compose files. Safety argument (R1-02 §1.2 principle 5: conservative defaults, fail-safe state is what prod should accidentally land in) outweighs source-doc naming inertia. R1-05 §4.10 cited "source doc wins naming ties" but the source doc (R0-02 §9.4) raises the footgun as an open question, not a binding stance. When the source doc is ambiguous, safety wins. Cost: ~10 LOC rename.

**Winner**: R2-01 / R2-03 / R2-04 (3:1 majority + safety argument)

### 20.3 Origin allowlist placement for `/ws/training` (R2-01 = B-pre-a, R2-02 = B-pre-a, R2-03 = implied B-pre-a, R2-04 = unspecified)

**Conflict**: R2-01 (§5.7) explicitly argued Origin on `/ws/training` should move to B-pre-a (instead of B-pre-b per R1-05 §4.35), based on R1-01's live-data exfiltration argument. R2-02 (§5.1) adopts this position. R2-03 (CCC-01 §3.4) does not contradict. R2-04 delegates to implementer.

**Resolution**: **Origin on `/ws/training` in B-pre-a; Origin on `/ws/control` stays in B-pre-b.** R2-01's exfiltration argument is sound: training metrics, topology, and param values are user-specific state exposed via `/ws/training`. Closing that exfiltration vector costs ~0.5 day and is independent of CSRF plumbing.

**Winner**: R2-01 / R2-02

### 20.4 Phase 0-cascor staging soak duration (R2-01 = 72 h, R2-02 = 24 h, R2-03 = 72 h implied, R2-04 = 72 h)

**Conflict**: R2-02 (§18.6) explicitly argued **24 h** for Phase 0-cascor soak, reasoning that Phase 0-cascor's additive-field contract means blast radius is low. R2-01 (§3.5 item 4) and R2-04 (D-38) both set **72 h** citing R1-02 §3.4's argument that seq monotonicity bugs are latent.

**Resolution**: **72 h**. Phase 0-cascor is the foundation of the replay/resume protocol. A seq monotonicity bug under sustained multi-client broadcast takes time to surface. The 72 h soak is mostly free (cascor runs unattended in staging) and catches the class of bugs that 24 h misses. R2-02's "additive contract = low blast radius" is true for backwards compat but NOT for seq correctness — seq bugs surface in Phase B reconnection behavior.

**Winner**: R2-01 / R2-04

### 20.5 Chaos tests: nightly vs blocking (R2-01 = blocking for 3 specific tests, R2-02 = not specified, R2-03 = not specified, R2-04 = nightly)

**Conflict**: R2-01 (§18.9) elevates three specific chaos tests (replay race, broadcast chaos, broadcast_from_thread) to **blocking gates** for Phase 0-cascor. R2-04 (D-40) recommends **nightly-only** for chaos tests across the board.

**Resolution**: **Three Phase 0-cascor chaos tests are blocking gates; all other chaos tests are nightly.** R2-01's reasoning is correct that these three tests catch exactly the bugs (seq/replay corruption) that R1-02 §9.1 identifies as correctness-catastrophic. The `hypothesis`-based browser-bridge chaos and header-fuzz chaos (Phase B, B-pre-b) remain nightly per R2-04 due to CI flakiness. This is a targeted elevation, not a blanket one.

**Winner**: R2-01 (for the 3 specific tests); R2-04 (for all others)

---

## 21. Disagreements with R2 inputs

This section lists places where this master integration plan takes a position that differs from an R2 input's position. Each is justified.

### 21.1 R2-02 §1.2: `disable_ws_auth` naming preserved

R2-02 preserved R1-05 §4.10's negative-sense `disable_ws_auth` naming. This plan overrides to positive-sense `ws_security_enabled` per §20.2 justification.

### 21.2 R2-02 §18.6: 24 h Phase 0-cascor soak

R2-02 argued 24 h was sufficient for Phase 0-cascor's additive-field soak. This plan adopts 72 h per §20.4 justification.

### 21.3 R2-03 CCC-07 §9.3: Replay buffer default 256

R2-03's canonical settings table listed 256 for both dev and prod. This plan uses 1024 for production per §20.1 justification.

### 21.4 R2-04 D-40: Chaos tests entirely nightly

R2-04 recommended all chaos tests as nightly-only. This plan elevates 3 Phase 0-cascor chaos tests to blocking per §20.5 justification.

### 21.5 R2-02 §7.7: Per-origin handshake cooldown deferred

R2-02 (§7.7 NOT-in-this-phase) defers per-origin handshake cooldown entirely. R2-01 (§7.1 item 6) includes it in Phase B-pre-b. This plan includes it in Phase B-pre-b (§6.3.1 item 5) because it's a low-cost (~20 LOC) amplification of the Origin defense and the NAT-hostile escape hatch (cleared on restart) makes it safe.

---

## 22. Self-audit log

### 22.1 Phase coverage

Every phase has all required fields:

| Phase | Goal | Entry gate | Deliverables | CCCs woven | Tests | Observability | PR plan | Exit gate | Rollback | NOT-in-phase | Decisions blocking |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-cascor | 3.1 | 3.2 | 3.3 | 3.3.3 | 3.4 | 3.5 | 3.6 | 3.7 | 3.8 | 3.9 | 3.10 |
| B-pre-a | 4.1 | 4.2 | 4.3 | 4.3.2 | 4.4 | 4.3.2 | 4.5 | 4.6 | 4.7 | 4.8 | 4.9 |
| B | 5.1 | 5.2 | 5.3 | 5.3.2 | 5.4 | 5.3.2 | 5.5 | 5.6 | 5.7 | 5.8 | 5.9 |
| B-pre-b | 6.1 | 6.2 | 6.3 | 6.3.2 | 6.4 | 6.3.2 | 6.5 | 6.6 | 6.7 | 6.8 | 6.9 |
| C | 7.1 | 7.2 | 7.3 | 7.4 | 7.5 | 7.4 | 7.6 | 7.7 | 7.8 | 7.9 | — |
| D | 8.1 | 8.2 | 8.3 | — | 8.4 | 8.3 | 8.5 | 8.6 | 8.7 | 8.8 | — |
| E | 9.1 | 9.2 | 9.3 | — | 9.4 | 9.3 | 9.5 | 9.6 | 9.7 | — | — |
| F | 10.1 | 10.2 | 10.3 | — | 10.4 | 10.3 | 10.5 | 10.6 | 10.7 | — | — |
| G | 11.1 | 11.2 | 11.3 | — | 11.3 | — | 11.4 | 11.5 | 11.6 | — | — |
| H | 12.1 | 12.2 | 12.3 | — | 12.3 | RISK-01 | 12.4 | 12.5 | 12.6 | — | — |
| I | 13 (folded) | — | 13 | — | 13 | — | Phase B | Phase B | 13 | — | — |

**All 11 phases covered.**

### 22.2 CCC coverage

All 10 CCCs from R2-03 woven into Phase 0-cascor, B-pre-a, B, B-pre-b explicitly (§3.3.3, §4.3.2, §5.3.2, §6.3.2). Later phases (C-H) reference CCCs per their phase contracts (§7.4, etc.). Summary table in §16 lists owner + acceptance per CCC. Phase x CCC matrix can be reconstructed from the per-phase CCC subsections.

### 22.3 R2-04 decision coverage

All 55 R2-04 decisions (D-01..D-55) + 7 implicit decisions (D-56..D-62) addressed:
- **5 High-cost decisions** (D-02, D-11, D-17, D-19, D-23): all applied in §2.
- **10 Medium-cost decisions**: all applied in §2 and §17.
- **40+ Low/None decisions**: applied via default throughout.
- Full decision table with applied defaults in §17.

### 22.4 R2-cross disagreement coverage

5 R2-cross disagreements identified and resolved in §20:
1. Replay buffer default (R2-03 vs R2-01/02/04) → 1024
2. Security flag naming (R2-02 vs R2-01/03/04) → positive-sense
3. Origin placement for `/ws/training` (R2-01/02 vs implicit others) → B-pre-a
4. Phase 0-cascor soak (R2-02 vs R2-01/04) → 72 h
5. Chaos test blocking scope (R2-01 vs R2-04) → 3 blocking, rest nightly

### 22.5 GAP-WS coverage

All 33 GAP-WS items from source doc addressed:
- 17 resolved in phases (01-06, 07, 09, 10, 12-16, 21-22, 24a/b, 25-27, 28-33)
- 2 RESOLVED on main (GAP-WS-19)
- 3 deferred (GAP-WS-17 permessage-deflate, GAP-WS-18 topology chunking, GAP-WS-20)

### 22.6 M-SEC coverage

11 of 13 M-SEC controls addressed (M-SEC-01 through M-SEC-11). M-SEC-08 and M-SEC-09 explicitly deferred per R1-03 §20.2. M-SEC-12 folded into M-SEC-07 per R1-05 §4.15.

### 22.7 RISK coverage

All 16 RISK-NN entries from source doc §10 have entries in §15 with severity, phase, kill switch, TTF, key mitigation.

### 22.8 Corrections made during self-audit

1. **§2.2 replay buffer default**: initially listed as "1024" without noting R2-03's divergent 256. Added explicit R2-cross flag to §2.2 and full resolution in §20.1.
2. **§2.3 security flag**: initially copied R2-02's negative-sense without noting the 3:1 disagreement. Added explicit R2-cross flag and resolution in §20.2.
3. **§3.7 exit gate item 8 soak duration**: initially said "48 h". Corrected to "72 h" per §20.4 resolution.
4. **§5.3.1 item 18**: initially omitted `/api/ws_browser_errors` endpoint for browser JS error reporting (R2-04 D-59 implicit decision). Added.
5. **§6.3.1 item 5**: initially omitted per-origin handshake cooldown (R2-01 included it, R2-02 deferred it). Added per §21.5 resolution.
6. **§14 kill-switch matrix**: initially had 22 rows. Added 2 missing rows (`JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0` from B-pre-a and `JUNIPER_DISABLE_WS_BRIDGE=true` as distinct from `enable=false`). Final count: 24 rows.
7. **§15 risk register**: initially had RISK-05 weekly smoke. Changed to nightly per R1-02 amplification (consistent with R2-01 §15).
8. **§18 merge sequence**: initially had P7 after P10. Moved P7 before P10 because Phase C iterates on `enable_browser_ws_bridge=True` (needs the flip to be in place).
9. **§19 effort summary**: initially listed total as 13.5 days. Corrected to show R2-02's more conservative 15.75 expected, which includes the 2.25-day delta for audit, HMAC, and NetworkVisualizer work. The 13.5 from R1-05 §4.40 is the parallel-execution compressed estimate.
10. **§3.4 SDK tests**: initially listed 12 tests. Added `test_correlation_map_bounded_at_256` and `test_len_pending_returns_to_zero_after_failure_modes` for 14 total per R2-01 §4.3.
11. **§5.3.2 CCC-08**: initially only mentioned "REST paths kept". Added specific reference to regression harness file and golden shape file per R2-03 CCC-08 §10.3 items 2, 5.
12. **§16 CCC summary**: initially did not assign owners per R2-03 §14.12 recommendation. Added owner-role column.

### 22.9 Confidence assessment

- **High confidence**: Phase 0-cascor scope and commit decomposition (4 R2s agree), `command_id` wire-level correction (verified against source doc), GAP-WS-19 RESOLVED, Phase B-pre split, master kill-switch matrix (R2-01 + R2-03 + R2-04 triangulation), cross-repo merge sequence, effort range.
- **Medium confidence**: Origin on `/ws/training` in B-pre-a (overrides R1-05; justified by exfiltration argument), `ws_security_enabled` positive-sense (overrides R1-05; justified by safety), Phase E conditional shipping (R1-04 §12.3 position; R1-02 §7.2 unconditional), 72 h soak durations (may be excessive for calendar).
- **Lower confidence**: NetworkVisualizer scope (render-tech unverified), Phase B-pre-b effort (SessionMiddleware question), Phase C flip-gate p99 ≥50 ms threshold (may be too strict or too loose depending on actual latency distribution).

### 22.10 Scope discipline

- [x] Read only the 4 R2 files; did not re-read R0 or R1 files.
- [x] Referenced R2-NN identifiers when citing inputs.
- [x] Referenced GAP-WS-NN, M-SEC-NN, RISK-NN identifiers from source doc.
- [x] Applied R2-04 recommended defaults unless strong justification to override (5 overrides justified in §20-§21).
- [x] Every R2-cross disagreement explicit and justified.
- [x] Did not modify other files. Did not commit.
- [x] Did not add emojis.
- [x] Did not add unnecessary new GAP-WS/M-SEC/RISK identifiers.

**Scope discipline PASS.**

---

**End of R3-01 Master Integration Development Plan.**
