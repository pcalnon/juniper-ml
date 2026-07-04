# Round 3 Proposal R3-02: Decision-Resolved Execution Blueprint

**Angle**: Every decision applied; no alternatives; opinionated execution plan
**Author**: Round 3 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 3 consolidation — input to Round 4
**Inputs consolidated**: R2-01 (best-of synthesis), R2-02 (phase execution contracts), R2-03 (cross-cutting concerns), R2-04 (decision matrix) — R2-04 defaults applied as settled positions
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 0. If you only read one section

This is the **constitution-first blueprint** for the WebSocket migration. Every decision in R2-04 (D-01 through D-62) is resolved to a single position; every phase is written as if those positions are already law. The migration exists to kill a ~3 MB/s `/api/metrics/history` polling bomb (GAP-WS-16, P0). The P0 win lands in Phase B after Phase 0-cascor and Phase B-pre-a prereqs clear. Everything else sequences around that spine. No "consider X or Y", no "TBD", no options — read §1 for the applied positions and the rest of the document is the execution that follows.

The critical-path spine is **P2 (SDK) → P1 (Phase 0-cascor) → P3/P4 (Phase B-pre-a) → P5/P6 (Phase B) → 72h staging soak → P7 (Phase B flag-flip) → production**. Everything else (Phase B-pre-b, C, D, E, F, G, H) branches off once Phase B is in production. Total effort is **15.75 engineering days expected** (±2 days variance) over ~4.5 weeks calendar, with 48-72 hour soak windows between high-risk phases. Rollback MTTR is ≤5 min for every kill switch; untested kill switches are not kill switches (D-53 applied).

The three most load-bearing applied positions are: **(D-02)** the correlation field is `command_id` everywhere, period, no stale `request_id` references survive Round 3; **(D-11)** Phase 0-cascor is carved out of Phase B and cascor main soaks for ≥1 week before canopy consumes the new envelope; **(D-17+D-18)** Phase B ships with the two-flag design `enable_browser_ws_bridge=False` + `disable_ws_bridge=False` with runtime logic `enabled = enable_browser_ws_bridge and not disable_ws_bridge`. These three applied positions dictate the shape of the PR plan, the rollback MTTR, and the cross-repo merge order; the rest of the decisions are important but the migration can survive wrong choices if these three hold.

---

## 1. Constitution: applied decisions (from R2-04)

This section is the "law of the migration." Every subsequent phase references these positions as settled. Order within each subsection is by decision ID for traceability; order across subsections reflects when the position is first binding.

### 1.1 Wire-protocol decisions

| ID | Applied position | Source |
|---|---|---|
| **D-01** | `set_params` default timeout = **1.0 s** (SDK kwarg default); callers needing longer pass explicitly | R2-04 §3.1, R2-02 §1.1 |
| **D-02** | Correlation field is **`command_id`** — EVERYWHERE: SDK kwarg, wire envelope field on `/ws/control` inbound, cascor echo in `command_response`, canopy drain callback, all tests. Any surviving `request_id` reference is a pre-merge defect | R2-04 §3.2, R2-03 §3.3 item 1, R2-02 §1.1 |
| **D-03** | `command_response` on `/ws/control` carries **no `seq` field**. Separate seq namespaces: `/ws/training` has seq-bearing broadcast with replay; `/ws/control` is personal RPC, correlation via `command_id` only | R2-04 §3.3, R2-02 §1.1, R2-03 §3.3 item 3 |
| **D-14** | Two-phase registration uses **`_pending_connections: set[WebSocket]`** + `connect_pending()` + `promote_to_active()` helper in `training_stream.py`. No per-connection `seq_cursor`. | R2-04 §3.14, R2-02 §3.3 A-srv-5a |
| **D-15** | **`server_instance_id` is the programmatic comparison key** for server-restart detection. `server_start_time` is advisory/human-readable only, never used for equality | R2-04 §3.15, R2-03 §3.3 item 4 |
| **D-16** | `connection_established` advertises **`replay_buffer_capacity: int`** as an additive field. Clients ignore if absent (defaults to 1024 in client-side reasoning) | R2-04 §3.16, R2-02 §3.3 A-srv-2b |
| **D-34** | Unclassified `set_params` keys route **both ways at different layers**: cascor server-side Pydantic `extra="forbid"` rejects unknown keys on wire; canopy adapter routes unclassified keys to REST with WARN log | R2-04 §3.34, R2-03 §3.3 item 7 |
| **D-35** | Replay buffer default **1024 entries**, tunable via `JUNIPER_WS_REPLAY_BUFFER_SIZE` env var | R2-04 §3.35, R2-02 §18.1 |
| **D-36** | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` is a **supported kill-switch value** (disables replay entirely; all reconnects return `out_of_range`) | R2-04 §3.36, R2-03 §5.4 |
| **D-46** | `JUNIPER_WS_SEND_TIMEOUT_SECONDS` is **env-var configurable**, default 0.5 s. Kill-switch lever for slow-client behavior | R2-04 §3.46, R2-03 §5.4 |

### 1.2 Phase-ordering decisions

| ID | Applied position | Source |
|---|---|---|
| **D-11** | **Phase 0-cascor is carved out** of Phase B as a separate ≈2-day server-only PR. Cascor main carries the new envelope fields (`seq`, `server_instance_id`, `replay_buffer_capacity`, `emitted_at_monotonic`, `resume` frame family) for **≥1 week** before canopy Phase B consumes them. The 1-week soak is the additive-contract validation window | R2-04 §3.11, R2-02 §1.2 |
| **D-13** | **GAP-WS-19 (`close_all` lock) is RESOLVED on main.** Verified at `juniper-cascor/src/api/websocket/manager.py:138-156`. Not in any phase scope. Only a regression test `test_close_all_holds_lock` lands (belt-and-suspenders) in Phase 0-cascor | R2-04 §3.13, R2-02 §1.2 |
| **D-23** | **Phase B-pre is split into B-pre-a and B-pre-b.** B-pre-a = frame-size caps + per-IP caps + `/ws/training` Origin + audit logger skeleton; gates Phase B. B-pre-b = `/ws/control` Origin + CSRF first-frame + rate limit + idle timeout + adapter HMAC + audit Prometheus counters; gates Phase D. B-pre-a is ~0.5 day; B-pre-b is ~1.5-2 days. Phase B-pre-b runs **in parallel with Phase B**, not before it | R2-04 §3.23, R2-02 §1.2 |
| **D-55** | Source-doc text patches (D-01, D-02, D-11, D-12, D-13, D-15, D-16, D-19, D-20, D-24, D-25, D-26, D-37, D-38, D-39) are **batched in Round 5** as a single v1.4 patch PR to `WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` | R2-04 §3.55 |
| **D-56 (implicit)** | **REST deprecation is never planned.** "Preserve forever" means permanent. A future RFC is required for any REST removal | R2-04 §5.1 |
| **D-61 (implicit)** | **Mid-week deploys only for behavior-changing flag flips** (D-17 P7, D-47, D-49). Phase 0-cascor, Phase A-SDK, and B-pre-a can deploy any day | R2-04 §5.6 |

### 1.3 Default-state (feature-flag & security) decisions

| ID | Applied position | Source |
|---|---|---|
| **D-04** | **rAF coalescer ships as a scaffold, disabled by default.** `Settings.enable_raf_coalescer=False`. One-line flip later if `§5.6` instrumentation proves frame-budget pressure | R2-04 §3.4, R2-02 §1.1 |
| **D-05** | **REST polling fallback cadence during disconnect = 1 Hz** (`n % 10 != 0` check against 100 ms fast-update-interval). Not 100 ms. | R2-04 §3.5 |
| **D-06** | **NetworkVisualizer Phase B scope = minimum WS wiring only.** Deep render migration deferred to Phase B+1. First Phase B commit records render-tech verification (`grep -l "cytoscape\|plotly"` result) in PR description | R2-04 §3.6, R2-02 §1.2 |
| **D-07** | `ws-metrics-buffer` store is a **structured object** `{events: [...], gen: int, last_drain_ms: float}`, not a bare array. `gen` counter makes Dash change-detection deterministic | R2-04 §3.7, R2-02 §1.2 |
| **D-08** | **GAP-WS-24 is split into 24a and 24b.** 24a = browser emitter (`ws_latency.js`, frontend lane). 24b = canopy backend `/api/ws_latency` endpoint + Prometheus histogram (canopy-backend lane). Both ship in Phase B | R2-04 §3.8, R2-02 §1.2 |
| **D-10** | **Security flag stays negative-sense `disable_ws_auth`** per R1-05 §4.10 source-doc fidelity, BUT a CI guardrail in `juniper-deploy` refuses `JUNIPER_DISABLE_WS_AUTH=true` in any production compose/Helm file. The footgun is closed by the guardrail, not by a rename | R2-02 §1.2 (R2-04 §3.10 flagged the conflict; R3-02 applies R2-02's compromise) |
| **D-17** | **Phase B ships with `Settings.enable_browser_ws_bridge=False`** as the merge default. Staging flips to True via ops env var; canary runs with True; production default flip (True) is a separate one-line PR (P7) after 72-hour staging soak | R2-04 §3.17, R2-02 §1.2, R2-03 §5.3 item 6 |
| **D-18** | **Permanent kill switch `Settings.disable_ws_bridge=False`** ships alongside `enable_browser_ws_bridge`. Runtime check: `enabled = enable_browser_ws_bridge and not disable_ws_bridge` | R2-04 §3.18, R2-03 §15.4 |
| **D-20** | **SDK fails fast on `set_params` timeout/disconnect.** No retries, no reconnect queue; caller decides via REST fallback | R2-04 §3.20, R2-02 §1.1 |
| **D-21** | **REST paths (`update_params`, `/api/metrics/history`, `/api/train/{command}`) are preserved forever.** No deprecation schedule, no removal plan. A future RFC is required to even consider removal | R2-04 §3.21 |
| **D-22** | **Slider debounce lives in the Dash clientside callback**, not the SDK. 250 ms debounce. Non-canopy SDK consumers get unthrottled dispatch | R2-04 §3.22 |
| **D-24** | **Per-IP cap default = 5 per IP**, tunable via `Settings.ws_max_connections_per_ip` | R2-04 §3.24 |
| **D-25** | **Single-tenant v1 deployment topology.** Multi-tenant is future work. Replay buffer is not partitioned by session | R2-04 §3.25 |
| **D-26** | **Shadow traffic rejected.** Polling-toggle pattern (GAP-WS-25) achieves most of the shadow benefit without state duplication | R2-04 §3.26 |
| **D-28** | **Dedicated `canopy.audit` logger** with JSON formatter, `TimedRotatingFileHandler` (30-day retention dev / 90-day prod), scrub allowlist. Skeleton in Phase B-pre-a; Prometheus counters in Phase B | R2-04 §3.28, R2-03 §4.3 item 10 |
| **D-29** | **Adapter-to-cascor auth uses HMAC CSRF token**: `hmac.new(api_key.encode(), b"adapter-ws", sha256).hexdigest()` sent as the first frame on `/ws/control`. No `X-Juniper-Role: adapter` header skip. Uniform handler logic | R2-04 §3.29, R2-02 §1.1 |
| **D-30** | **One resume per connection rule enforced.** Track `resume_consumed: bool` per connection; second resume attempt closes 1003 | R2-04 §3.30, R2-02 §3.3 |
| **D-31** | **Per-command HMAC (M-SEC-02 point 3) deferred indefinitely.** XSS defense lives in CSP, not per-command HMAC | R2-04 §3.31 |
| **D-32** | **Multi-tenant replay isolation deferred** (v1 is single-tenant per D-25) | R2-04 §3.32 |
| **D-33** | **Rate limit: single bucket 10 cmd/s.** Two-bucket split deferred unless starvation observed | R2-04 §3.33 |
| **D-47** | **`Settings.use_websocket_set_params=False`** Phase C default (unanimous across R1s) | R2-04 §3.47 |
| **D-48** | **Phase C flag-flip criteria are enumerated hard gates**: ≥7 days production data, p99 delta ≥50 ms (REST minus WS), zero orphaned commands, zero correlation-map leaks, canary ≥7 days, zero page-severity alerts in canary window | R2-04 §3.48 |
| **D-49** | **Phase D ships with `Settings.enable_ws_control_buttons=False`.** Staged rollout with kill switch | R2-04 §3.49 |
| **D-54** | **REST polling handler `_update_metrics_store_handler` preserved forever** as the kill switch | R2-04 §3.54 |

### 1.4 Deferral decisions

| ID | Applied position | Source |
|---|---|---|
| **D-19** | **Phase E default backpressure policy = `drop_oldest_progress_only`.** Progress events (metrics, candidate_progress) drop oldest on full queue; state-bearing events (state, topology, cascade_add, connection_established) close 1013 for slow clients. `block` and `close_slow` remain opt-in alternatives via `Settings.ws_backpressure_policy` | R2-04 §3.19, R2-02 §1.1 |
| **D-27** | **CODEOWNERS rule for `_normalize_metric` is enforced** (hard merge gate, not advisory). Combined with pre-commit hook blocking format-removal commits and regression test pinning shape hash | R2-04 §3.27, R2-03 §15.6 |
| **D-40** | **Chaos tests run nightly-only, never in per-PR fast lane.** Corpus checked into repo so regressions can be replayed as unit tests | R2-04 §3.40 |
| **D-41** | **Load tests (100 Hz broadcast, 10-client rolling reconnect) are blocking gates for Phase 0-cascor** | R2-04 §3.41 |
| **D-42** | **Browser frame-budget tests are recording-only in CI.** Strict assertions are `@pytest.mark.latency_strict` local lane only | R2-04 §3.42 |
| **D-43** | **`contract` pytest marker is added** to all three `pyproject.toml` files (cascor, canopy, cascor-client). Contract tests run on every PR via a dedicated lane | R2-04 §3.43, R2-03 §7.3 item 1 |
| **D-44** | **Chromium-only browser matrix for v1.** Firefox and WebKit are post-migration work | R2-04 §3.44 |
| **D-45** | **User research study skipped for v1.** Optional, not blocking | R2-04 §3.45 |

### 1.5 Observability & operational decisions

| ID | Applied position | Source |
|---|---|---|
| **D-12** | **M-SEC-10 (idle timeout) and M-SEC-11 (adapter inbound validation) adopted as new canonical IDs.** M-SEC-12 (log injection escaping) folded into M-SEC-07 | R2-04 §3.12 |
| **D-37** | **Metrics-presence CI test is enforced as a PR blocker** (fast lane). Scrapes `/metrics` endpoint and asserts every metric in the canonical catalog is present | R2-04 §3.37 |
| **D-38** | **Phase 0-cascor staging soak = 72 hours.** Seq monotonicity bugs are latent | R2-04 §3.38 |
| **D-39** | **Phase B staging soak = 72 hours.** RISK-10 browser memory leak needs multi-hour observation | R2-04 §3.39 |
| **D-50** | **Error-budget-burn freeze rule enforced.** A commit that lands during an active SLO budget burn must be either reliability-related or explicitly approved | R2-04 §3.50 |
| **D-51** | **`WSOriginRejection` alert severity = page.** Repeated Origin rejection from an unknown hash is the CSWSH-probe canary | R2-04 §3.51 |
| **D-52** | **`WSSeqCurrentStalled` alert severity = page.** Stalled seq counter with active connections = broadcast-loop hang | R2-04 §3.52 |
| **D-53** | **Every kill switch MTTR is tested in staging** before the phase enters production. Untested kill switches are not kill switches. An untested or failing kill switch is an abandon trigger | R2-04 §3.53 |

### 1.6 Implicit decisions (D-56..D-62)

| ID | Applied position | Source |
|---|---|---|
| **D-56** | REST deprecation = **never** (see §1.2 above) | R2-04 §5.1 |
| **D-57** | `juniper-ml` meta-package extras pin bump is a **same-day follow-up PR** after every SDK release | R2-04 §5.2 |
| **D-58** | CI runtime budget: **≤25% runtime increase acceptable**; revisit if nightly >30 min or fast lane >10 min | R2-04 §5.3 |
| **D-59** | Browser JS error pipeline: **new `/api/ws_browser_errors` POST endpoint**, counted server-side into `canopy_ws_browser_js_errors_total` Prometheus counter. Same pattern as `/api/ws_latency` | R2-04 §5.4 |
| **D-60** | **One worktree per phase per repo** per Juniper ecosystem worktree policy. Phases spanning repos = multiple worktrees (e.g., Phase B = one cascor worktree for P5 + one canopy worktree for P6) | R2-04 §5.5 |
| **D-61** | Deploy-freeze = **mid-week only for behavior-changing flag flips** (see §1.2) | R2-04 §5.6 |
| **D-62** | **Bandwidth baseline must be measured** for 1 hour in production before Phase B deploy. Record in `canopy_rest_polling_bytes_per_sec` gauge as reference for the >90% reduction AC | R2-04 §5.7 |

### 1.7 Resolutions for R2-04 §6 unresolved items

R2-04 §6 listed 6 items as "Round 3 cannot resolve without user input" + 7 new open questions surfaced in R2. R3-02 resolves each as a default-of-last-resort so no item remains TBD. Every resolution is justified by the "apply R2-04 recommended default unless a different R2 already resolved it" rule.

| # | Open item | Resolved position | Rationale | Who verifies |
|---|---|---|---|---|
| 1 | NetworkVisualizer render tech (cytoscape vs Plotly) | **Assume cytoscape.** First Phase B commit runs `grep -l "cytoscape\|plotly" juniper-canopy/src/frontend/components/network_visualizer.py` and records the answer in the PR description. If Plotly, upgrade Phase B pessimistic estimate to +1 day and migrate via `extendTraces`. If cytoscape, ship minimum WS wiring and defer render migration to Phase B+1 | R2-04 §6.1 item 1 / R2-02 §6.2 contingent resolution | Phase B implementer in first commit |
| 2 | Canopy FastAPI `SessionMiddleware` presence | **Assume absent.** Phase B-pre-b budgets +0.5 day for adding middleware from scratch. First Phase B-pre-b commit runs `grep -rn "SessionMiddleware" juniper-canopy/src/` and records the result. If present, reclaim 0.5 day | R2-04 §6.1 item 2, R2-02 §17.1 | Phase B-pre-b implementer |
| 3 | Dash version (`set_props` availability) | **Does not affect plan.** Option B (Interval drain callback) is chosen regardless per R2-02 §1.1. Record Dash version in Phase B PR description for changelog traceability | R2-04 §6.1 item 3 | Phase B implementer |
| 4 | Plotly.js version (`extendTraces(maxPoints)` signature) | **Does not affect plan.** `extendTraces(graphId, update, [0,1,2,3], 5000)` signature works on Plotly 1.x and 2.x. Record version in PR description | R2-04 §6.1 item 4 | Phase B implementer |
| 5 | Canopy adapter `run_coroutine_threadsafe` usage | **Assume not yet used.** Phase C ships the pattern fresh as part of the hot/cold split adapter refactor. If the pattern already exists, reuse it | R2-04 §6.1 item 5 | Phase C implementer |
| 6 | Cascor `/ws/control` handler `command_id` passthrough | **Cascor must be modified** to explicitly echo `command_id` in `command_response`. Phase 0-cascor deliverable A-srv-9 includes this modification (echoes when present, omits when absent for backward compat with pre-SDK clients). Phase G test `test_set_params_echoes_command_id` is the contract enforcer | R2-04 §6.1 item 6 | Phase 0-cascor implementer |
| 7 (D-29) | Adapter auth: HMAC vs header-skip | **Resolved: HMAC CSRF token** per D-29 applied position above | R2-04 §6.2 item 7 | Settled |
| 8 (D-17) | Phase B feature flag default | **Resolved: flag-off** per D-17 applied position above | R2-04 §6.2 item 8 | Settled |
| 9 (D-19) | Phase E backpressure default | **Resolved: `drop_oldest_progress_only`** per D-19 applied position above | R2-04 §6.2 item 9 | Settled |
| 10 (D-10) | Security flag naming | **Resolved: negative-sense stays, CI guardrail closes footgun** per D-10 applied position above (R2-02 compromise) | R2-04 §6.2 item 10 | Settled |
| 11 (D-35) | Replay buffer default size | **Resolved: 1024 tunable** per D-35 applied position above | R2-04 §6.2 item 11 | Settled |
| 12 | Effort estimate confidence (13.5 vs 17-18) | **Expected = 15.75 days** per R2-02 §17 (+2.25 over R1-05 baseline). Optimistic 10.6 days; pessimistic 22.25 days. 4.5 weeks calendar with soak windows | R2-04 §6.2 item 12 | Settled |
| 13 (D-62) | Bandwidth baseline measurement | **Resolved: measure 1 hour pre-Phase-B** per D-62 applied position above | R2-04 §6.2 item 13 | Settled |

All 13 items have resolved positions. **No item in this blueprint is TBD.**

---

## 2. Phase 0-cascor: SDK + cascor server prerequisites (RESOLVED)

### 2.1 Resolved scope

Phase 0-cascor is the cascor-server-only prerequisite phase carved out from Phase B per **D-11**. It ships `seq` numbers, `server_instance_id`, `replay_buffer_capacity`, the `resume` frame family, `snapshot_seq` on REST, the `emitted_at_monotonic` field (for §5.6 latency pipe per D-08), the `_send_json` 0.5-second timeout quick-fix (RISK-04 quick-fix), the state coalescer fix (GAP-WS-21), the `broadcast_from_thread` exception logging fix (GAP-WS-29), the `/ws/control` protocol-error responses (GAP-WS-22), and the "one resume per connection" security rule (**D-30**). This phase is purely additive — existing clients that ignore `seq` keep working.

**In parallel**: Phase A-SDK ships `juniper-cascor-client.CascorControlStream.set_params()` with the `command_id` correlation map. Phase A-SDK has no runtime dependency on Phase 0-cascor; it can merge on day 1.

### 2.2 Entry gate (no decisions remaining)

- [ ] `juniper-cascor` main branch clean; baseline tests green (`cd juniper-cascor/src/tests && bash scripts/run_tests.bash`)
- [ ] GAP-WS-19 resolved state verified via direct file inspection (**D-13**; `manager.py:138-156` lock-holding pattern)
- [ ] No concurrent cascor Phase-0-scope PR open (merge-queue check)
- [ ] Prometheus namespace reservations: `cascor_ws_broadcast_send_duration_seconds`, `cascor_ws_replay_buffer_occupancy`, `cascor_ws_replay_buffer_capacity_configured`, `cascor_ws_resume_replayed_events`, `cascor_ws_resume_failed_total{reason}`, `cascor_ws_pending_connections`, `cascor_ws_seq_gap_detected_total`, `cascor_ws_state_throttle_coalesced_total`, `cascor_ws_broadcast_from_thread_errors_total`, `cascor_ws_broadcast_timeout_total`, `cascor_ws_audit_log_bytes_written_total`
- [ ] Constitution §1 committed to this blueprint and Round 3 review complete
- [ ] `juniper-cascor-worker` CI wired to run against cascor main (CCC-04 backward-compat gate, **D-25** single-tenant scoping confirmed)

### 2.3 Deliverables (functional + cross-cutting)

**Server-side code changes** (10 commits, single squash-merged PR per **R2-02 §3.3**):

- **A-srv-1** — `juniper-cascor/src/api/websocket/messages.py`: add optional `seq: Optional[int] = None` and `emitted_at_monotonic: Optional[float] = None` on every envelope builder
- **A-srv-2a** — `manager.py`: add `server_instance_id: str = str(uuid.uuid4())`, `server_start_time: float = time.time()`, `_next_seq: int`, `_seq_lock: asyncio.Lock`, `_replay_buffer: deque[tuple[int, dict]]` with `maxlen=Settings.ws_replay_buffer_size`, `_assign_seq_and_append()` helper
- **A-srv-2b** — `connect()` sends `connection_established` with `{server_instance_id, server_start_time, replay_buffer_capacity}` in `data` (**D-16** additive)
- **A-srv-3** — `_send_json()` wraps `ws.send_json(msg)` in `asyncio.wait_for(..., timeout=Settings.ws_send_timeout_seconds)` (default 0.5 s, **D-46** env var configurable); exception logged; metric `cascor_ws_broadcast_timeout_total` incremented (RISK-04 quick-fix)
- **A-srv-4** — `replay_since(last_seq: int) -> list[dict]` helper + `ReplayOutOfRange` exception class
- **A-srv-5a** — `training_stream.py`: `_pending_connections: set[WebSocket]` (**D-14**), `connect_pending()`, `promote_to_active()` (two-phase registration)
- **A-srv-5b** — `/ws/training` handler: `resume` frame handler with 5 s frame timeout → `resume_ok` (replays events since `last_seq`) or `resume_failed` (reason = `out_of_range | server_restarted | second_resume`). Server-restart detection via `server_instance_id` mismatch (**D-15**). "One resume per connection" rule enforced via `resume_consumed: bool` flag; second resume → close 1003 (**D-30**)
- **A-srv-6** — `/api/v1/training/status` REST endpoint: add `snapshot_seq` and `server_instance_id` fields, read atomically under `_seq_lock`
- **A-srv-7** — `lifecycle/manager.py:133-136`: replace 1 Hz drop-filter with debounced coalescer; terminal transitions (`Completed`, `Failed`, `Stopped`) bypass throttle (GAP-WS-21)
- **A-srv-8** — `broadcast_from_thread`: attach `asyncio.Task.add_done_callback(_log_exception)` (GAP-WS-29)
- **A-srv-9** — `/ws/control` handler: unknown-command and non-JSON → protocol-error envelope (close 1003, GAP-WS-22). **Echo `command_id` from inbound when present, omit when absent. Does NOT carry `seq`** (**D-03** per-endpoint seq namespaces)
- **A-srv-10** — `CHANGELOG.md` + `docs/websocket_protocol.md` update describing the additive field contract and protocol version state matrix (old/new × cascor/canopy)

**Tests** (20 unit/integration tests committed with the PR):

- `test_seq_monotonically_increases_across_broadcasts` (renamed from R0-05 per D-03 clarification)
- `test_seq_is_assigned_on_loop_thread`
- `test_seq_lock_does_not_block_broadcast_iteration`
- `test_replay_buffer_bounded_to_configured_capacity`
- `test_replay_buffer_capacity_configurable_via_env` (overrides to 256 via `JUNIPER_WS_REPLAY_BUFFER_SIZE`)
- `test_replay_buffer_size_zero_disables_replay_returns_out_of_range` (**D-36** kill-switch value)
- `test_resume_replays_events_after_last_seq`
- `test_resume_failed_out_of_range`
- `test_resume_failed_server_restarted` (server_instance_id mismatch)
- `test_second_resume_closes_connection_1003` (**D-30**)
- `test_connection_established_advertises_instance_id_and_capacity` (**D-16**)
- `test_snapshot_seq_atomic_with_state_read` (concurrency: REST read while broadcast ongoing)
- `test_slow_client_send_timeout_does_not_block_fanout` (0.5 s quick-fix)
- `test_send_timeout_env_override_behavior` (**D-46**)
- `test_state_coalescer_flushes_terminal_transitions` (GAP-WS-21)
- `test_broadcast_from_thread_exception_logged` (GAP-WS-29 via caplog)
- `test_unknown_command_returns_protocol_error_envelope` (GAP-WS-22)
- `test_malformed_json_closes_1003`
- `test_ws_control_command_response_has_no_seq` (**D-03** contract test)
- `test_pending_connections_not_eligible_for_broadcast`
- `test_promote_to_active_atomic_under_seq_lock`
- `test_close_all_holds_lock` (**D-13** regression guard)

**Contract tests** (CCC-05, D-43 marker):

- `test_replay_buffer_capacity_advertised` (in `juniper-cascor/src/tests/contract/test_connection_established_fields.py`)
- `test_seq_present_on_ws_training_broadcast_only` (canopy-side, but test asserts producer contract; lives in canopy per R2-03 §7.3)
- `test_cascor_command_response_shape_matches_sdk_parser`

**Load tests** (**D-41** blocking gate): 100 Hz broadcast for 60 seconds; 10-client rolling reconnect for 60 seconds; both must pass before the PR is mergeable

**Observability** (CCC-02, D-37 metrics-presence test enforces):

- `cascor_ws_broadcast_send_duration_seconds` histogram (fed by `_send_json` timing; buckets `{0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0}`)
- `cascor_ws_broadcast_timeout_total` counter
- `cascor_ws_replay_buffer_occupancy` gauge
- `cascor_ws_replay_buffer_bytes` gauge
- `cascor_ws_replay_buffer_capacity_configured` gauge (one-shot at startup; makes operational tunable visible)
- `cascor_ws_resume_requests_total{outcome}` counter (outcome = `success|out_of_range|server_restarted|second_resume|malformed|no_resume_timeout`)
- `cascor_ws_resume_replayed_events` histogram (buckets `{0, 1, 5, 25, 100, 500, 1024}`)
- `cascor_ws_pending_connections` gauge
- `cascor_ws_seq_current` gauge (monitored by `WSSeqCurrentStalled` page alert, **D-52**)
- `cascor_ws_seq_gap_detected_total` counter (must be 0)
- `cascor_ws_state_throttle_coalesced_total` counter (GAP-WS-21 observability)
- `cascor_ws_broadcast_from_thread_errors_total` counter (GAP-WS-29 observability)

**Alerts**:

- `WSSeqCurrentStalled` (page, **D-52**): `changes(cascor_ws_seq_current[5m]) == 0 AND cascor_ws_connections_active > 0` — test-fired once in staging before prod
- `WSReplayBufferFull` (ticket): `cascor_ws_replay_buffer_occupancy / cascor_ws_replay_buffer_capacity_configured > 0.9 for 10m`
- `WSBroadcastTimeout` (ticket): `increase(cascor_ws_broadcast_timeout_total[5m]) > 0`

**Documentation**:

- `juniper-cascor/CHANGELOG.md` entry citing GAP-WS-07, GAP-WS-13, GAP-WS-21, GAP-WS-22, GAP-WS-29, GAP-WS-32; references D-02, D-03, D-11, D-14, D-15, D-16
- `juniper-cascor/docs/websocket_protocol.md` — new section "Sequence numbers, replay, and reconnection" with old/new × cascor/canopy compat matrix
- `juniper-cascor/notes/runbooks/ws-migration-rollback.md` — initial version

### 2.4 Pull request plan

Single PR, squash-merged. The 10 commits are tightly coupled (resume handler depends on replay buffer depends on seq field) and splitting forces multiple cross-repo windows.

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P1** | `phase-0-cascor-seq-replay-resume` | `feat(ws): seq numbers, replay buffer, resume protocol, state coalescer` | backend-cascor | `juniper-cascor` main |

Branch naming follows the Juniper centralized worktree convention (**D-60**).

**In parallel** (independent PR in a separate repo):

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P2** | `phase-a-sdk-set-params` | `feat(sdk): CascorControlStream.set_params with command_id correlation` | SDK | `juniper-cascor-client` main |

P2 can merge and publish to PyPI on day 1, independent of P1 progress.

**Phase A-SDK deliverables summary** (fully specified in R2-02 §4.3):

- New method `async def set_params(self, params: dict, *, timeout: float = 1.0, command_id: Optional[str] = None) -> dict` (**D-01** default 1.0 s; **D-02** kwarg name; **D-20** fail-fast)
- Correlation map: `_pending: Dict[str, asyncio.Future]` keyed by `command_id`
- Background `_recv_task` correlates on `command_id` echo; cancellation-safe (`finally:` cleanup per R1-02 §10.4 mandatory gate)
- `_client_latency_ms` private field on returned dict
- Bounded correlation map at 256 entries with `JuniperCascorOverloadError` on overflow
- 10 unit tests including `test_set_params_caller_cancellation_cleans_correlation_map` (mandatory gate per R1-05 §4.25) and `test_set_params_fails_fast_on_disconnect`
- `juniper-cascor-client` **minor** version bump (new public method)
- Same-day `juniper-ml` extras pin bump follow-up PR (**D-57**)
- Metric: `juniper_cascor_client_ws_set_params_total{status}` (status = `success|timeout|connection_error|server_error|overload`)

### 2.5 Exit gate (measurable, no ambiguity)

**Phase 0-cascor** (P1):

1. All 20 unit tests + 3 contract tests + load tests pass in CI
2. `/ws/training` staging broadcasts observed for 60 s show strictly monotonically increasing `seq` values
3. `/api/v1/training/status` REST response includes `snapshot_seq` and `server_instance_id` (verified via `curl` against staging)
4. `cascor_ws_broadcast_send_duration_seconds` p95 < 100 ms in staging under load
5. A `resume` frame with `last_seq=N-5` after forced disconnect replays exactly 5 events in seq order
6. A forced cascor restart followed by reconnect triggers `resume_failed{outcome=server_restarted}` and the client falls back to REST snapshot
7. `cascor_ws_replay_buffer_capacity_configured == 1024` in production config; `== 256` in staging config (proves tunable)
8. **72-hour** staging soak (**D-38**) with a long-running training job shows `cascor_ws_seq_gap_detected_total == 0`
9. `juniper-cascor-worker` CI passes against the new cascor main during the soak (CCC-04 additive-contract validation)
10. `WSSeqCurrentStalled` alert synthetically test-fired in staging (**D-53**)
11. Every kill switch in the Phase 0-cascor kill-switch row of §13 flipped in staging and validated via its metric
12. Source doc patch list items updated in R5 tracking branch (**D-55**)

**Phase A-SDK** (P2):

1. All 10 SDK unit tests pass, including `test_set_params_caller_cancellation_cleans_correlation_map` as a mandatory gate (**R1-05 §4.25**)
2. `pip install juniper-cascor-client==<new>` from PyPI succeeds in a fresh venv
3. Draft canopy adapter can `import` and call `set_params` against a local `FakeCascorServerHarness`
4. `juniper-cascor-client/CHANGELOG.md` entry merged
5. `juniper-ml/pyproject.toml` extras pin bump follow-up PR opened (**D-57**)

**Going/no-go**: if step 8 shows any seq gap or step 9 fails, halt and investigate before Phase B starts.

### 2.6 Rollback

1. **Hot revert** (15 min TTF): `git revert` P1, blue/green redeploy cascor. Clients with cached `server_instance_id` get `resume_failed{server_restarted}` and fetch REST snapshot (pre-Phase-0 behavior).
2. **Env override** (2 min TTF): if the issue is specifically `_send_json` timeout causing false drops, set `JUNIPER_WS_SEND_TIMEOUT_SECONDS=30` to effectively disable the timeout without rollback.
3. **Replay-buffer disable** (2 min TTF, **D-36**): `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` forces all reconnects to snapshot-refetch path.
4. **SDK rollback** (Phase A-SDK independent): `pip yank` the new version from PyPI; downstream canopy pins to prior version. P2 is effectively a no-op for users until Phase C flips the flag, so the rollback blast radius is contained.

### 2.7 NOT in this phase

- **Full Phase E backpressure** (per-client pump task + bounded queue + policy matrix). Only the 0.5-second `_send_json` quick-fix lands here
- **`permessage-deflate` negotiation** (GAP-WS-17) — deferred
- **Topology chunking** (GAP-WS-18) — deferred
- **`seq` on `command_response`** — explicitly excluded per **D-03**
- **GAP-WS-19 re-fix** — already on main per **D-13**; only the regression test
- **M-SEC-01..06 security controls** — those are Phase B-pre-a/b
- **Multi-tenant per-session replay buffers** — deferred per **D-32**
- **Canopy adapter `command_id` consumption** — that is Phase C
- **Canopy-side `canopy_ws_delivery_latency_ms_bucket` histogram** (GAP-WS-24b) — that is Phase B
- **NetworkVisualizer changes** — that is Phase B
- **Phase B feature flag** — that is Phase B

---

## 3. Phase B-pre-a: read-path security (RESOLVED)

### 3.1 Resolved scope

Close the minimum set of security holes that exposing browser→canopy `/ws/training` traffic opens: frame-size caps (M-SEC-03, max 4096 bytes on inbound control frames), per-IP connection caps (M-SEC-04 minimal, **D-24** 5 per IP), `/ws/training` Origin allowlist (M-SEC-01b — R2-02 §5.1 allocation: training-path Origin is B-pre-a because cross-origin `/ws/training` is a live-data exfil vector), audit logger skeleton (M-SEC-07 — **D-28** dedicated `canopy.audit` logger, Prometheus counters deferred to Phase B), and "one resume per connection" (**D-30**, already in Phase 0-cascor but counted here for audit).

Phase B-pre-a is explicitly split from B-pre-b per **D-23**. B-pre-a is ~0.5 day and gates Phase B. B-pre-b is ~1.5-2 days, runs **in parallel with Phase B**, and gates Phase D.

### 3.2 Entry gate (no decisions remaining)

- [ ] `juniper-cascor` and `juniper-canopy` main branches clean
- [ ] Phase 0-cascor (P1) merged to cascor main (so the 1-week additive-soak window starts)
- [ ] No concurrent security-focused PR open on either repo
- [ ] Prometheus namespace reservations for `canopy_ws_origin_rejected_total{origin_hash, endpoint}`, `canopy_ws_oversized_frame_rejected_total{endpoint}`, `canopy_ws_per_ip_cap_rejected_total{endpoint}`, `canopy_audit_events_total{event_type}` (counter only; Prometheus hookup in Phase B)
- [ ] `canopy.audit` logger name not already used: `grep -rn "canopy.audit" juniper-canopy/`
- [ ] Constitution §1 applied decisions locked in as current branch positions (no re-litigation)

### 3.3 Deliverables (functional + cross-cutting)

**Cascor side** (P3 branch `phase-b-pre-a-cascor-security`):

- **MVS-SEC-01**: `juniper-cascor/src/api/websocket/origin.py` new module with `validate_origin(ws, allowlist: list[str]) -> bool`. Case-insensitive host compare, port-significant, null origin rejected, empty allowlist = reject-all (fail closed), `*` value refused at parser level
- **MVS-SEC-02**: unit tests covering exact-match, case-insensitive, trailing-slash strip, null origin, port mismatch, scheme mismatch, wildcard rejection, empty allowlist
- **MVS-SEC-03**: wire `validate_origin` into `training_stream_handler` pre-accept upgrade
- **MVS-SEC-04**: `Settings.ws_allowed_origins: list[str] = []` (empty = fail-closed), env var `JUNIPER_WS_ALLOWED_ORIGINS`
- **MVS-SEC-08**: `_per_ip_counts: Dict[str, int]` under `_lock` in `WebSocketManager`, increment in `connect()`, decrement in `disconnect()` `finally:` block
- **MVS-SEC-09**: `Settings.ws_max_connections_per_ip: int = 5` (**D-24**)
- **MVS-SEC-11**: `max_size=4096` on every `receive_*()` call in `training_stream.py`

**Canopy side** (P4 branch `phase-b-pre-a-canopy-security`):

- **MVS-SEC-05**: `juniper-canopy/src/backend/ws_security.py` — copy `validate_origin` helper from cascor (explicit duplication, no cross-repo import, per CCC-05 §7.3 item 4)
- **MVS-SEC-06**: wire into `/ws/training` route handler in `main.py` (approx line 355)
- **MVS-SEC-07**: `Settings.allowed_origins` in canopy config with concrete localhost defaults: `["http://localhost:8050", "http://127.0.0.1:8050", "https://localhost:8050", "https://127.0.0.1:8050"]`
- **MVS-SEC-12**: `max_size=4096` on canopy's `/ws/training` receive
- **Audit logger skeleton** (**D-28**): new `canopy.audit` logger in `juniper-canopy/src/backend/audit.py`. JSON formatter with fields `{ts, actor, action, command, params_before, params_after, outcome, request_ip, user_agent}`. `TimedRotatingFileHandler` with daily rotation, 30-day retention dev / 90-day prod. Scrub allowlist (no raw payloads). **No Prometheus counters yet** — those land in Phase B per R2-02 §18.3
- **`test_close_all_holds_lock`**: regression test for GAP-WS-19 (**D-13**) — belt-and-suspenders

**Tests**:

- `test_per_frame_size_limit_1009_on_ws_training` (cascor and canopy both)
- `test_per_ip_connection_cap_6th_rejected_1013`
- `test_per_ip_counter_decrements_on_disconnect`
- `test_per_ip_counter_decrements_on_exception` (race regression)
- `test_origin_allowlist_accepts_configured_origin`
- `test_origin_allowlist_rejects_third_party`
- `test_origin_allowlist_rejects_missing_origin`
- `test_origin_allowlist_case_insensitive_host`
- `test_origin_allowlist_wildcard_refused` (the explicit "non-switch" CI test per CCC-07 §9.3 item 10)
- `test_canopy_origin_rejection_matrix`
- `test_empty_allowlist_rejects_all_with_fail_closed`
- `test_audit_log_format_and_scrubbing` (**D-28**)
- `test_audit_log_rotates_daily` (mocked time)
- `test_per_ip_cap_env_override` (kill-switch flip validation per **D-53**)
- `test_audit_log_env_override`
- `test_allowed_origins_env_override_works`

**Observability** (metrics landed in B-pre-a; dashboards/Prometheus hookup in Phase B per **R2-02 §18.3**):

- `canopy_ws_origin_rejected_total{origin_hash, endpoint}` counter (hashed origin so probes correlate without logging raw)
- `canopy_ws_oversized_frame_rejected_total{endpoint}` counter
- `canopy_ws_per_ip_cap_rejected_total{endpoint}` counter
- `canopy_audit_events_total{event_type}` counter (metric name reserved; Prometheus hookup in Phase B)
- `canopy_ws_handshake_attempts_total{outcome}` funnel counter (R1-02 §2.3 amplification)

**Alerts**:

- `WSOriginRejection` (**D-51** page severity): `increase(canopy_ws_origin_rejected_total{origin_hash=unknown}[5m]) > 0` — CSWSH probe canary, test-fired in staging before prod
- `WSOversizedFrame` (ticket): `increase(canopy_ws_oversized_frame_rejected_total[5m]) > 0`

**Documentation**:

- `juniper-canopy/notes/runbooks/ws-audit-log-troubleshooting.md` — audit log disk-full/permission errors (R2-03 §8.3)

### 3.4 Pull request plan

Two PRs, P3 must merge before P4 (canopy's origin helper is a copy of cascor's; cascor reference is the canonical source).

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P3** | `phase-b-pre-a-cascor-security` | `feat(security): origin allowlist + max_size + per-IP cap on /ws/training (M-SEC-03/04/01b)` | backend-cascor + security | `juniper-cascor` main |
| **P4** | `phase-b-pre-a-canopy-security` | `feat(security): origin + max_size on /ws/training + audit logger skeleton (M-SEC-03/07 skeleton)` | backend-canopy + security | `juniper-canopy` main |

### 3.5 Exit gate (measurable, no ambiguity)

1. All 16 tests pass
2. Cross-origin probe from `http://evil.example.com` rejected by both cascor and canopy `/ws/training`
3. 65 KB frame on either `/ws/training` → close code 1009
4. 6 simultaneous connections from same IP to cascor → 6th rejected with 1013
5. Kill cascor mid-broadcast; per-IP counters return to zero within `disconnect()` cleanup (leak regression)
6. `canopy_ws_origin_rejected_total` counter increments on manual rejection
7. `canopy_audit_events_total{event_type="origin_rejected"}` counter increments
8. Empty `JUNIPER_WS_ALLOWED_ORIGINS` in staging config rejects all connections (fail-closed test); this is a **halt condition** if it ever fails open
9. Audit log file appears at expected path, contains JSON entries, rotates on day boundary
10. `WSOriginRejection` alert synthetically test-fired in staging (**D-53**)
11. `test_allowed_origins_wildcard_refused` green (parser rejection of `*`)
12. Every kill switch in Phase B-pre-a row of §13 flipped in staging and validated via its metric

**Going/no-go**: if empty allowlist fails to reject (fail-open), HALT — this is a critical security defect.

### 3.6 Rollback

1. **Env flag relaxation** (2 min TTF): `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` + expanded allowlist — effectively disables guards without code revert
2. **Audit logger disable** (2 min TTF): `JUNIPER_AUDIT_LOG_ENABLED=false`
3. **Revert P4 then P3** (10 min TTF): standard git revert in reverse order

### 3.7 NOT in this phase

- **M-SEC-02 cookie + CSRF first-frame** — Phase B-pre-b
- **Origin allowlist on `/ws/control`** — Phase B-pre-b
- **M-SEC-05 per-command rate limit** — Phase B-pre-b
- **M-SEC-10 idle timeout** — Phase B-pre-b
- **M-SEC-11 adapter inbound validation** — Phase B-pre-b
- **Prometheus counters for audit events** — Phase B (R2-02 §18.3)
- **HMAC adapter auth** — Phase B-pre-b
- **Log injection escaping (M-SEC-07 extended, formerly M-SEC-12)** — Phase B-pre-b

---

## 4. Phase B: frontend + polling elimination (RESOLVED)

### 4.1 Resolved scope

The P0 win. Canopy browser drains `/ws/training` into a bounded Dash store, renders chart updates via `Plotly.extendTraces`, and **stops polling `/api/metrics/history` entirely** when WS is healthy. Polling REST handler is preserved as the kill-switch fallback (**D-21**, **D-54**). Ships behind **D-17** two-flag gating (`enable_browser_ws_bridge=False`, `disable_ws_bridge=False`, runtime `enabled = former AND NOT latter`). Ships with **D-08** GAP-WS-24a/b latency instrumentation. Ships with **D-06** minimum NetworkVisualizer WS wiring (deep render deferred contingent on render tech). Ships with Phase I asset cache busting folded in. Ships with the Phase B-pre-a audit Prometheus counter hookup deferred here per R2-02 §18.3.

### 4.2 Entry gate (no decisions remaining)

- [ ] Phase 0-cascor (P1) merged to cascor main AND deployed to staging AND passed 72-hour soak (**D-38**)
- [ ] `cascor_ws_seq_gap_detected_total == 0` over the full soak window
- [ ] Phase B-pre-a (P3 + P4) merged and deployed to staging
- [ ] Phase A-SDK (P2) published to PyPI and 2-5 min propagation window elapsed (CCC-04)
- [ ] `Settings.enable_browser_ws_bridge` and `Settings.disable_ws_bridge` added to canopy config (default False for both during merge window)
- [ ] NetworkVisualizer render tech recorded in PR description (resolved per §1.7 item 1 — assume cytoscape)
- [ ] **D-62 bandwidth baseline measured**: 1 hour of production-equivalent staging traffic, value recorded in `canopy_rest_polling_bytes_per_sec` gauge history. This is the denominator for the >90% reduction AC
- [ ] `juniper-ml[all]` extras pin bump follow-up for the SDK is merged (**D-57**)

### 4.3 Deliverables (functional + cross-cutting)

**Frontend JS** (`juniper-canopy/src/frontend/assets/`):

- **MVS-FE-01**: `ws_dash_bridge.js` new file (~200 LOC). Module-scope closure exposed as `window._juniperWsDrain`. Handlers for `metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`. Per-handler bounded ring buffers (cap enforced **in the handler**, not the drain, per RISK-12). Drain methods: `drainMetrics()`, `drainState()`, `drainTopology()`, `drainCascadeAdd()`, `drainCandidateProgress()`, `peekStatus()`
- **MVS-FE-02**: edit `websocket_client.js` in place (do NOT delete):
  - `onStatus()` enrichment
  - Jitter on reconnect backoff: `delay = Math.random() * Math.min(CAP, BASE * 2**attempt)` with `BASE=500ms`, `CAP=30s` (GAP-WS-30)
  - Capture `server_instance_id` from `connection_established`
  - Track `seq` with monotonic check; warn on gap
  - On reconnect, emit `resume` frame first with `{last_seq, server_instance_id}`; on `resume_failed`, fall back to REST `/api/v1/training/status`
- **MVS-FE-03**: delete parallel raw-WebSocket clientside callback in `dashboard_manager.py:1490-1526` (GAP-WS-03). Leave placeholder comment citing this blueprint
- **MVS-FE-14**: `ws_latency.js` new file (~50 LOC, GAP-WS-24a). Browser latency beacon, records `received_at_ms - emitted_at_monotonic`, POSTs to `/api/ws_latency` every 60 s. Clock-offset recomputation on reconnect (R2-03 §4.3 item 9). Gated on `Settings.enable_ws_latency_beacon` (default True)
- **rAF scaffold**: implement `_scheduleRaf` as a gated function in `ws_dash_bridge.js`; default disabled per **D-04**

**Python-side store + drain callback** (`juniper-canopy/src/frontend/`):

- **MVS-FE-04**: `dashboard_manager.py` — add `dcc.Store(id='ws-metrics-buffer')` with drain callback firing on `fast-update-interval` tick. Callback reads `window._juniperWsDrain.drainMetrics()` and writes **`{events: [...], gen: int, last_drain_ms: float}`** (**D-07** structured object, NOT bare array)
- **MVS-FE-05**: update existing `ws-topology-buffer` and `ws-state-buffer` drain callbacks to read from `window._juniperWsDrain.drainTopology()` / `drainState()`. Delete references to old `window._juniper_ws_*` globals
- **MVS-FE-06**: add `dcc.Store(id='ws-connection-status')` with peek-based drain callback, emits only on change
- **MVS-FE-07**: refactor `_update_metrics_store_handler` in `dashboard_manager.py:2388-2421`. Read `ws-connection-status` via State, return `no_update` when connected, fallback at **1 Hz** via `n % 10 == 0` check (**D-05**), preserve initial-load REST GET path
- **MVS-FE-08**: rewrite `MetricsPanel.update_metrics_display()` as clientside_callback calling `Plotly.extendTraces(graphId, update, [0,1,2,3], 5000)`. Add `uirevision: "metrics-panel-v1"` to initial figure layout. Add hidden `metrics-panel-figure-signal` dummy Store
- **MVS-FE-09**: same migration for `components/candidate_metrics_panel.py`
- **MVS-FE-10**: polling toggle for `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`. KEEP REST paths (kill-switch fallback, **D-54**)
- **MVS-FE-11**: NetworkVisualizer minimum WS wire — wire `ws-topology-buffer` + `ws-cascade-add-buffer` as Inputs to the cytoscape graph update callback (**D-06**). If grep reveals Plotly, absorb +1 day and migrate via `extendTraces`
- **MVS-FE-12**: connection indicator badge (GAP-WS-26): `html.Div` with clientside_callback reading `ws-connection-status` → CSS class toggling (connected/reconnecting/offline/demo)
- **MVS-FE-13**: demo mode parity (RISK-08) — `demo_mode.py` sets `ws-connection-status` to `{connected: true, mode: "demo"}`
- **MVS-FE-15**: `/api/ws_latency` POST endpoint in `main.py` (GAP-WS-24b). Increments `canopy_ws_delivery_latency_ms_bucket` histogram
- **MVS-FE-15b**: `/api/ws_browser_errors` POST endpoint (**D-59**). Increments `canopy_ws_browser_js_errors_total{component}` counter
- **MVS-FE-16**: Phase I asset cache busting. Bump `assets_folder_snapshot` or equivalent (R2-02 §14 folded into Phase B)
- **Two-flag runtime check**: `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge` gates the entire bridge (**D-17 + D-18**)
- **NormalizeMetric regression gate**: `test_normalize_metric_produces_dual_format` landed here (Phase H folds the gate up to Phase B; Phase H only ships the CODEOWNERS rule and consumer audit)

**Cascor side** (residual Phase B work, landed in its own PR):

- Prometheus hookup for `canopy_audit_events_total` (deferred from Phase B-pre-a per R2-02 §18.3)
- `emitted_at_monotonic` field validation test (already landed in Phase 0-cascor; this is a regression guard)
- `cascor_ws_backend_relay_latency_ms` histogram emission in the canopy adapter relay (R2-03 §12.3 item 2)

**Observability** (all metric-before-behavior gated per CCC-02):

- `canopy_rest_polling_bytes_per_sec` gauge (the P0 win signal; labeled by endpoint per R2-03 §4.5 item 10)
- `canopy_ws_delivery_latency_ms_bucket{type}` histogram with buckets `{50, 100, 200, 500, 1000, 2000, 5000}` ms (R2-03 §12.3 item 5)
- `canopy_ws_backend_relay_latency_ms` histogram (separates cascor→canopy hop)
- `canopy_ws_active_connections` gauge
- `canopy_ws_reconnect_total{reason}` counter
- `canopy_ws_connection_status{status}` gauge
- `canopy_ws_browser_heap_mb` gauge (via beacon)
- `canopy_ws_browser_js_errors_total{component}` counter (via `/api/ws_browser_errors`)
- `canopy_ws_drain_callback_gen{buffer}` gauge (liveness signal for clientside callback death, R2-03 §4.2 R1-02 §2.2)
- `canopy_ws_drain_callback_error_rate` counter
- `canopy_audit_events_total{event_type}` Prometheus hookup (deferred from B-pre-a)

**Dashboards** (committed as JSON to `juniper-canopy/deploy/grafana/ws-health.json`):

- "WebSocket health" panel: p50/p95/p99 delivery latency per event type
- "Polling bandwidth" panel: `canopy_rest_polling_bytes_per_sec` trend
- "Browser memory" panel: `canopy_ws_browser_heap_mb` p95 trend
- Every panel defined in code, committed to repo

**Alerts** (every one test-fired in staging per **D-53** before prod):

- `WSDrainCallbackGenStuck` (page): `canopy_ws_drain_callback_gen` unchanged for 5m with active connections (RISK-02 mitigation)
- `WSBrowserHeapHigh` (ticket): `canopy_ws_browser_heap_mb` p95 > 500 MB for 10m
- `WSJsErrorsRising` (ticket): `increase(canopy_ws_browser_js_errors_total[10m]) > 0`

**Tests** (27 tests across unit/integration/e2e/contract):

- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_ws_connection_status_store_reflects_cascor_ws_status`
- `test_ws_metrics_buffer_drain_is_bounded`
- `test_ws_metrics_buffer_store_shape_is_structured_object` (**D-07**)
- `test_adapter_subscribes_to_metrics_and_forwards_to_normalizer`
- `test_adapter_reconnects_after_fake_kills_connection`
- `test_adapter_handles_resume_failed_by_fetching_snapshot`
- `test_adapter_demo_mode_parity` (RISK-08 gate)
- `test_reconnect_replays_10_missed_events`
- `test_reconnect_with_stale_server_instance_id_triggers_snapshot`
- `test_snapshot_seq_bridges_no_gap`
- `test_older_cascor_without_resume_command_triggers_fallback`
- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected` (the P0 assertion)
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_demo_mode_metrics_parity`
- `test_ws_metrics_buffer_store_is_ring_buffer_bounded`
- `test_connection_indicator_badge_reflects_state`
- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_seq_reset_on_cascor_restart`
- `test_plotly_extendTraces_used_not_full_figure_replace`
- `test_metrics_dual_format` (Phase H regression gate folded into Phase B — MVS-TEST-14)
- `test_polling_elimination` (the P0 proof — measures `/api/metrics/history` request count over 60 s with WS connected, asserts zero requests after initial load)
- `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` (**D-42** recording-only, marked `latency_recording`)
- `test_fallback_polling_at_1hz_when_disconnected` (**D-05**)
- `test_network_visualizer_updates_on_ws_cascade_add`
- `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` (GAP-WS-24b)
- `test_latency_histogram_resilient_to_laptop_sleep` (R2-03 §12.3 item 4 clock offset)
- `test_both_flags_interact_correctly` (**D-17 + D-18** two-flag logic)
- `test_audit_log_prometheus_counters` (deferred hookup)
- `test_enable_browser_ws_bridge_env_override` (kill-switch gate, **D-53**)
- `test_disable_ws_bridge_env_override` (kill-switch gate, **D-53**)

**Contract tests** (run in `contract` lane per **D-43**):

- `test_fake_cascor_message_schema_parity` (CCC-05 §7.3 item 1)
- `test_browser_message_handler_keys_match_cascor_envelope`

**Metrics-presence test** (**D-37**): scrapes canopy `/metrics`, asserts every metric name from the canonical catalog is present. Runs in fast lane. Missing metric = PR blocker.

**Runbooks**:

- `juniper-canopy/notes/runbooks/ws-bridge-kill.md` — 5-min TTF recipe for flipping `disable_ws_bridge=True`
- `juniper-canopy/notes/runbooks/ws-bridge-debugging.md` — diagnose drain-callback death
- `juniper-canopy/notes/runbooks/ws-memory-soak-test-procedure.md` — 72-hour staging soak procedure

### 4.4 Pull request plan

Three-PR sequence. Merge order enforced.

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P5** | `phase-b-cascor-residual` | `feat(cascor): audit-event Prometheus counters + canopy_ws_backend_relay_latency_ms (deferred from B-pre-a)` | backend-cascor | `juniper-cascor` main |
| **P6** | `phase-b-canopy-drain-wiring` | `feat(canopy): ws_dash_bridge drain callbacks, Plotly extendTraces, connection indicator, latency beacons (flag off)` | backend-canopy + frontend | `juniper-canopy` main |
| **P7** | `phase-b-canopy-flag-flip` | `config(canopy): default enable_browser_ws_bridge=True after staging soak` | ops + backend-canopy | `juniper-canopy` main |

Merge order: **P5 → P6 → 72h staging soak → P7**.

P7 is a **separate one-line PR** per R2-02 §6.4 and CCC-09 §11.3 item 6. It lands after Phase B is in staging for 72 hours, the P0 metric is verified, RISK-10 memory-soak check passes, and the production deploy window is mid-week per **D-61**.

### 4.5 Exit gate (measurable, no ambiguity)

**Gates on Phase B merge** (P5 + P6):

1. All 27 tests pass
2. `canopy_rest_polling_bytes_per_sec` in staging **>90% lower** than the pre-Phase-B baseline measured in entry gate (**D-62**) — 1 hour continuous post-deploy
3. `canopy_ws_delivery_latency_ms_bucket` histogram receives ≥1 data point per minute
4. "WebSocket health" dashboard panel renders p50/p95/p99 values
5. Runbook `ws-bridge-kill.md` published and **tested manually** in staging: flipping `disable_ws_bridge=True` restores REST polling within 5 min TTF (**D-53**)
6. **72-hour** staging soak (**D-39**) completes with browser memory p95 <500 MB (RISK-10 gate)
7. Demo mode parity test (`test_demo_mode_metrics_parity`) green in both fast and e2e lanes
8. Metric-format regression (`test_metrics_dual_format`) green — locks the Phase H contract
9. `canopy_ws_origin_rejected_total` from Phase B-pre-a remains responsive
10. `Settings.enable_browser_ws_bridge=False` is the merged default (flip happens only in P7)
11. Metrics-presence CI test green (**D-37**) — every required metric present
12. `test_both_flags_interact_correctly` green
13. Latency clock-offset test green
14. Every kill switch in the Phase B row of §13 flipped in staging and validated (**D-53**)

**Going/no-go for P7** (the flip):

15. 72 hours in staging with `enable_browser_ws_bridge=True` (ops-flipped via env), no page alerts fired
16. `canopy_rest_polling_bytes_per_sec` reduction >90% sustained over the 72 h
17. Browser memory p95 ≤500 MB over the 72 h
18. Mid-week deploy window available (**D-61**)
19. `canopy_ws_drain_callback_gen` shows ongoing progress (no stuck drain)
20. SLO error-budget burn rate inside normal range (**D-50**)

### 4.6 Rollback

1. **Fastest (2 min TTF)**: env var `JUNIPER_DISABLE_WS_BRIDGE=true` — polling REST takes over via the MVS-FE-07 toggle
2. **Code flag flip (5 min TTF)**: set `Settings.enable_browser_ws_bridge=False` in config and redeploy
3. **Full revert (30 min TTF)**: `git revert` P6 + redeploy (requires cache-bust invalidation because assets moved in MVS-FE-16)
4. **Browser-side emergency hatch**: URL query param `?ws=off` forces JS bridge off for a specific user (diagnostic)

### 4.7 NOT in this phase

- **Phase C `set_params`** — WebSocket bridge is read-only in Phase B
- **Phase D control buttons** — buttons remain REST POST
- **Full rAF coalescing enabled** — scaffold disabled per **D-04**
- **Full Phase F heartbeat** — jitter lands here but full ping/pong contract is Phase F
- **Full Phase E per-client pump-task backpressure** — only 0.5 s quick-fix from Phase 0-cascor
- **Topology chunking (GAP-WS-18)** — REST fallback handles large topologies
- **Full M-SEC-02 CSRF flow** — Phase B-pre-b
- **CODEOWNERS for `_normalize_metric`** — Phase H (the regression test lands here; the CODEOWNERS rule lands there)
- **`_normalize_metric` refactor** — Phase H (test-only; refactor deferred)
- **NetworkVisualizer deep render migration** — deferred to Phase B+1 if cytoscape (**D-06**)

---

## 5. Phase B-pre-b: control-path security (RESOLVED)

### 5.1 Resolved scope

Full CSWSH/CSRF protections on `/ws/control`: Origin allowlist on control endpoint, cookie-based session + CSRF first-frame (M-SEC-02), per-command rate limit (**D-33** single bucket 10 cmd/s), idle timeout (M-SEC-10, 120 s), adapter HMAC CSRF auth (**D-29**), adapter inbound validation (M-SEC-11), log-injection escaping (M-SEC-07 extended, formerly M-SEC-12 folded per **D-12**).

Runs **in parallel** with Phase B (not in series). Does not gate Phase B (which is read-only on `/ws/training`). Gates Phase D, which directly exposes the browser to `/ws/control`.

### 5.2 Entry gate (no decisions remaining)

- [ ] Phase B (P5 + P6) merged and in staging (so the browser bridge is already working read-only; adapter hop is tested in isolation)
- [ ] Phase A-SDK (P2) in main (Phase C consumer can use the SDK independent of B-pre-b)
- [ ] Session middleware presence verified per §1.7 item 2 (assume absent; budget +0.5 day if so)
- [ ] `Settings.ws_backpressure_policy` not yet set to Phase-E value
- [ ] **D-29 HMAC approach confirmed** (resolved in §1.7 item 7 — no re-litigation)

### 5.3 Deliverables

**Cookie session + CSRF** (canopy side):

- `juniper-canopy/src/main.py`: add `SessionMiddleware` (reuse if present per entry gate verification)
- `/api/csrf` endpoint returns a CSRF token bound to session, constant-time comparable via `hmac.compare_digest`
- Dash template injects CSRF token via `<div id="csrf-token" data-token="..."/>`
- `/ws/control` handler requires first frame `{"type": "auth", "csrf_token": "..."}` within 5 s; invalid → close 1008, absent → close 1008, expired → close 1008
- Cookie `SameSite=Lax`, `HttpOnly`, `Secure` (in prod)
- M-SEC-06 opaque close reasons: `/ws/control` uses numeric close codes only, no human-readable reason strings

**Origin + rate limit** (cascor side):

- `/ws/control` handler validates Origin against `Settings.ws_allowed_origins` (same allowlist as `/ws/training`)
- **D-33** single-bucket rate limit: 10 cmd/s leaky bucket per connection. 11th command in 1 s → close 1013
- M-SEC-10 idle timeout: connection idle >120 s → close 1008
- `Settings.ws_idle_timeout_seconds: int = 120`
- `Settings.ws_rate_limit_cps: int = 10`

**Adapter (canopy-to-cascor) auth** (**D-29**):

- Canopy adapter `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", hashlib.sha256).hexdigest()` on connect
- First frame: `{"type": "auth", "csrf_token": <hmac>}`
- Cascor `/ws/control` handler derives same value and compares with `hmac.compare_digest`
- Uniform handler logic; no `X-Juniper-Role: adapter` header special case

**M-SEC-11 adapter inbound validation**:

- `cascor_service_adapter.py` wraps inbound frames with Pydantic `CascorServerFrame` (`extra="allow"` — cascor may add new fields additively; reject only if envelope shape is malformed)
- Malformed frame → log + increment `canopy_adapter_inbound_invalid_total` + continue

**Log injection escaping** (M-SEC-07 extended, per **D-12**):

- Audit logger escapes CRLF (`\r`, `\n`) and tab (`\t`) in all logged strings
- Test `test_audit_log_escapes_crlf_injection`

**Security flag CI guardrail** (per **D-10** compromise):

- New CI job in `juniper-deploy` that refuses any compose/Helm file containing `JUNIPER_DISABLE_WS_AUTH=true` in production profile
- Dev compose files exempt via profile marker

**Tests**:

- `test_csrf_required_for_websocket_first_frame`
- `test_csrf_token_binds_to_session_constant_time_compare`
- `test_csrf_kill_switch_works` (**D-53**)
- `test_ws_control_origin_rejected`
- `test_ws_control_rate_limit_11th_command_closes_1013`
- `test_ws_control_idle_timeout_closes_1008`
- `test_canopy_adapter_sends_hmac_csrf_token_on_connect` (**D-29**)
- `test_canopy_adapter_inbound_malformed_frame_logged_and_counted`
- `test_audit_log_escapes_crlf_injection`
- `test_opaque_close_reasons_no_human_readable_strings`
- `test_session_middleware_exists_and_is_wired`
- `test_cascor_rejects_unknown_param_with_extra_forbid` (**D-34**)
- `test_disable_ws_auth_in_prod_compose_refused` (CI guardrail per **D-10**)
- `test_rate_limit_env_override` (kill-switch flip per **D-53**)
- `test_ws_security_env_override` (kill-switch flip per **D-53**)

**Contract test**:

- `test_adapter_synthetic_hmac_auth_frame_shape` (in `juniper-cascor/src/tests/contract/`)

**Observability**:

- `canopy_csrf_validation_failures_total` counter
- `canopy_ws_auth_rejections_total{reason, endpoint}` counter (reasons: `origin_rejected, cookie_missing, csrf_invalid, csrf_expired`)
- `cascor_ws_control_rate_limit_rejected_total` counter
- `cascor_ws_control_idle_timeout_total` counter
- `canopy_adapter_inbound_invalid_total` counter
- `canopy_ws_rate_limited_total{command, endpoint}` counter
- `canopy_ws_command_total{command, status, endpoint}` counter

**Alerts**:

- `WSAuthSpike` (ticket): `increase(canopy_ws_auth_rejections_total[5m]) > 10`
- `WSRateLimitSpike` (ticket): `increase(cascor_ws_control_rate_limit_rejected_total[5m]) > 10`

**Runbooks**:

- `juniper-canopy/notes/runbooks/ws-auth-lockout.md`
- `juniper-canopy/notes/runbooks/ws-cswsh-detection.md`

### 5.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P8** | `phase-b-pre-b-cascor-control-security` | `feat(security): /ws/control origin, rate limit, idle timeout, HMAC adapter auth (M-SEC-01/01b/05/10/11)` | backend-cascor + security | `juniper-cascor` main |
| **P9** | `phase-b-pre-b-canopy-csrf-audit` | `feat(security): cookie session + CSRF first-frame + audit Prometheus + log injection escaping (M-SEC-02/06/07)` | backend-canopy + security | `juniper-canopy` main |

Merge order: **P8 → P9**. P8 must land first because P9's adapter HMAC path depends on cascor accepting the new first-frame.

### 5.5 Exit gate

1. All 15 tests pass
2. Manual test: `/ws/control` without first-frame CSRF → close 1008
3. Manual test: `/ws/control` from wrong origin → close 1008
4. Manual test: 11 commands in 900 ms → 11th closed 1013
5. `SessionMiddleware` detected in canopy stack
6. Canopy adapter reconnects to cascor successfully after P8 + P9 deploy (HMAC handshake works)
7. `canopy_csrf_validation_failures_total` counter increments on rejected probe
8. **48-hour** staging soak with `/ws/control` traffic shows no regression in adapter reconnect rate
9. `WSOriginRejection` page alert test-fired on `/ws/control` (re-uses Phase B-pre-a alert with endpoint label)
10. CI guardrail refusing `DISABLE_WS_AUTH=true` in prod compose tested against sample fixture
11. Every kill switch in Phase B-pre-b row of §13 flipped in staging and validated (**D-53**)

### 5.6 Rollback

1. **Env flag** (2 min TTF): `JUNIPER_DISABLE_WS_AUTH=true` (**D-10** negative-sense stays; guardrail refuses in prod compose, so this is dev/staging-only)
2. **Per-control env flags** (5 min TTF): `JUNIPER_WS_CSRF_REQUIRED=false`, `JUNIPER_WS_RATE_LIMIT_ENABLED=false`, `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=99999`
3. **Revert P9 then P8** (15 min TTF)

### 5.7 NOT in this phase

- **Per-command HMAC (M-SEC-02 point 3)** — deferred indefinitely per **D-31**
- **Per-origin handshake cooldown** — deferred (NAT-hostile per R1-02 §13.10)
- **Two-bucket rate limiting** — deferred per **D-33**
- **Multi-tenant per-session replay** — deferred per **D-32**
- **Browser command buttons over WS** — Phase D

---

## 6. Phase C: set_params (RESOLVED — flag default off)

### 6.1 Resolved scope

Canopy adapter splits parameter updates into hot (learning rate, candidate LR, correlation threshold, pool size, max hidden units) and cold sets. Hot params route over `/ws/control` via `set_params` command with 1.0 s default timeout (**D-01**); cold params stay on REST. Feature-flagged behind `Settings.use_websocket_set_params=False` (**D-47**). REST path preserved forever (**D-21, D-54**). Flag-flip criteria are the **D-48** enumerated hard gates.

### 6.2 Entry gate

- [ ] Phase A-SDK (P2) on PyPI, `juniper-ml` extras pin bumped (**D-57**)
- [ ] Phase B (P5+P6) in main; `enable_browser_ws_bridge=True` in staging for ≥7 days
- [ ] Canopy adapter `run_coroutine_threadsafe` usage verified per §1.7 item 5 (assume ships fresh)
- [ ] Phase B-pre-b not required (Phase C adapter uses existing `X-API-Key` until Phase D shifts browser-side)

### 6.3 Deliverables

**Canopy adapter refactor** (`cascor_service_adapter.py`):

- `_HOT_CASCOR_PARAMS: frozenset[str]` — exhaustive list per R0-04 §5.1
- `_COLD_CASCOR_PARAMS: frozenset[str]` — complement
- `apply_params(**params)` splits → `_apply_params_hot()` (WS) + `_apply_params_cold()` (REST)
- `_apply_params_hot()` uses `CascorControlStream.set_params(params, timeout=1.0)`. On timeout/error → **unconditional REST fallback** (R0-04 §5.1 unconditional, not retry-based)
- Unclassified keys default to REST with WARNING log (**D-34**)
- `_control_stream_supervisor` background task maintains `/ws/control` connection; sends HMAC first-frame (confirms B-pre-b wiring)
- `Settings.use_websocket_set_params: bool = False` (**D-47**)
- `Settings.ws_set_params_timeout: float = 1.0` (**D-01**)
- Dash clientside callback debounce in the slider callback (**D-22**), 250 ms
- Latency instrumentation: `canopy_set_params_latency_ms{transport, key}` histogram (R2-03 §4.4 Phase C row)
- Correlation map bounded at 256 with `len(_pending)` gauge (R1-02 §6.4 amplification)

**Tests**:

- `test_apply_params_routes_hot_to_ws_when_flag_on`
- `test_apply_params_routes_hot_to_rest_when_flag_off`
- `test_apply_params_routes_cold_to_rest_always`
- `test_apply_params_falls_back_to_rest_on_ws_timeout`
- `test_apply_params_falls_back_to_rest_on_ws_connection_error`
- `test_canopy_adapter_defaults_unclassified_to_rest_with_warning` (**D-34**)
- `test_slider_debounce_250ms_collapses_rapid_updates` (**D-22**)
- `test_set_params_latency_histogram_exported` (both transports)
- R0-05 §4.3 Phase C routing unit tests (C1-C13 per R0-04 §10.2)
- `test_control_stream_supervisor_reconnects_on_disconnect`
- `test_control_stream_supervisor_sends_hmac_first_frame`
- `test_set_params_concurrent_correlation` (R1-05 §4.29 — 2 concurrent sliders, correlation correct via `command_id`)
- `test_use_websocket_set_params_env_override` (kill-switch flip, **D-53**)
- `test_ws_set_params_timeout_env_override` (kill-switch flip, **D-53**)

**E2E tests** (`dash_duo` + Playwright):

- `test_slider_drag_routes_to_ws_with_flag_on`
- `test_slider_drag_routes_to_rest_with_flag_off`
- `test_slider_drag_fallback_works_when_cascor_killed_mid_call`

**Contract tests**:

- `test_canopy_adapter_exception_handling_matches_sdk_raises`
- `test_canopy_adapter_defaults_unclassified_to_rest_with_warning` (as contract)

**Observability**:

- `canopy_set_params_latency_ms_bucket{transport, key}` histogram
- `canopy_orphaned_commands_total{command}` counter (RISK-13 signal, ticket severity only)
- `canopy_correlation_map_size` gauge (R1-02 §6.4)

**Runbooks**:

- `juniper-canopy/notes/runbooks/ws-set-params-flip.md` — flag-flip recipe

### 6.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P10** | `phase-c-canopy-set-params-adapter` | `feat(canopy): set_params hot/cold split, ws transport behind flag` | backend-canopy | `juniper-canopy` main |

Single PR; cascor-side requires no changes (Phase 0-cascor's `command_id` echo handles that).

### 6.5 Exit gate

1. All 14+ unit tests pass
2. Flag off: `canopy_set_params_latency_ms_bucket{transport="rest"}` has data; `transport="ws"` empty (regression check)
3. Flag on in staging: both transport labels have data; `transport="ws"` p95 lower than `transport="rest"` p95
4. `test_set_params_concurrent_correlation` passes
5. Manual test: slider drag with flag on → updates within 1 s in staging
6. Manual test: kill cascor mid-drag → slider change applies via REST within 2 s
7. Runbook published

**Going/no-go for the flag-flip follow-up PR (P10b)**: **D-48** enumerated hard gates:

1. ≥7 days production data on new code path
2. p99 delta `rest - ws` ≥ 50 ms (the user-visible benefit)
3. Zero orphaned commands per `canopy_orphaned_commands_total`
4. Zero correlation-map leaks (correlation-map-size gauge stable)
5. Canary ≥7 days
6. Zero page-severity alerts in canary window
7. Mid-week deploy window (**D-61**)

### 6.6 Rollback

1. **Env flag** (instant): `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`
2. **Revert P10** (15 min TTF)

### 6.7 NOT in this phase

- SDK-level retries — none per **D-20**
- SDK reconnect queue — none per **D-20**
- REST path deprecation — never per **D-21**
- Two-bucket rate limit — deferred per **D-33**
- Frontend control buttons over WS — Phase D

---

## 7. Phase D: control buttons (RESOLVED)

### 7.1 Resolved scope

Route browser `start/stop/pause/resume/reset` through `/ws/control` with `command_id` correlation. REST POST at `/api/train/{command}` remains first-class forever (**D-21**). Per-command timeouts per source doc §7.32: `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s`, `reset: 2s`. Ships behind `Settings.enable_ws_control_buttons=False` (**D-49**).

### 7.2 Entry gate

- [ ] Phase B-pre-b (P8+P9) **in production** (not just staging)
- [ ] 48-hour production soak of B-pre-b with no CSRF-related incidents
- [ ] Phase B in main with `enable_browser_ws_bridge=True` (so `window.cascorControlWS` is available)
- [ ] Mid-week deploy window per **D-61**

### 7.3 Deliverables

**Frontend**:

- Clientside callback on each button: `window.cascorControlWS.send({command: "start", command_id: uuid.v4()})` if WS connected; REST POST fallback if not
- Per-command client-side correlation map (command_id → button)
- Orphaned-command pending-verification UI: no response within timeout (10s start, 2s others) → REST fallback
- Badge status shows "pending" while awaiting WS ack

**Cascor side**:

- `/ws/control` handler routes inbound `{command, command_id, ...}` to existing REST-POST-backed handler, emits `command_response{command_id, status, error?}`
- Per-command timeout via `asyncio.wait_for(..., timeout=<per-command>)`
- Command whitelist: `start, stop, pause, resume, reset, set_params`. Unknown → `command_response{status: "error", code: "unknown_command"}`

**Tests**:

- `test_csrf_required_for_websocket_start`
- `test_start_button_ws_path_happy`
- `test_start_button_fallback_to_rest_on_ws_disconnect`
- `test_stop_command_ws_path_happy`
- `test_per_command_timeout_start_10s`
- `test_per_command_timeout_stop_2s`
- `test_unknown_command_rejected`
- `test_command_id_echoed_in_response` (**D-02**)
- `test_orphaned_command_falls_back_to_rest_after_timeout`
- `test_enable_ws_control_buttons_env_override` (kill-switch, **D-53**)

**Observability**:

- `canopy_training_control_command_latency_ms{command, transport}` histogram
- `canopy_training_control_total{command, transport}` counter
- `canopy_training_control_orphaned_total{command}` counter
- `cascor_ws_control_command_received_total{command}` counter

**Runbooks**:

- `juniper-canopy/notes/runbooks/ws-control-button-debug.md`

### 7.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P11** | `phase-d-cascor-control-commands` | `feat(cascor): /ws/control command dispatch + per-command timeouts` | backend-cascor | `juniper-cascor` main |
| **P12** | `phase-d-canopy-button-ws-routing` | `feat(canopy): training-control buttons via /ws/control with REST fallback` | frontend + backend-canopy | `juniper-canopy` main |

Merge order: **P11 → P12**.

### 7.5 Exit gate

1. All 10 tests pass
2. Manual: Start click with WS connected → training state within 10 s
3. Manual: kill cascor before click, click Start → REST fallback succeeds
4. Manual: click Start with wrong CSRF → 1008 close (B-pre-b regression)
5. `canopy_training_control_orphaned_total == 0` after 24 h staging
6. Every kill switch in Phase D row of §13 flipped in staging (**D-53**)

### 7.6 Rollback

1. **Env flag**: `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` → REST-only
2. **Revert P12 then P11** (20 min TTF)

### 7.7 NOT in this phase

- `permessage-deflate` — deferred
- `set_params` routing — Phase C
- Two-bucket rate limit — deferred

---

## 8. Phase E: backpressure (RESOLVED — drop_oldest_progress_only)

### 8.1 Resolved scope

Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded queues + backpressure policy matrix. **Default policy: `drop_oldest_progress_only`** (**D-19**), overriding source doc `block`. Alternative policies (`block`, `close_slow`) are configurable via `Settings.ws_backpressure_policy`.

Phase E is optional — ships only if Phase B production telemetry shows RISK-04/11 triggering. The Phase 0-cascor 0.5 s `_send_json` quick-fix is sufficient otherwise.

### 8.2 Entry gate

- [ ] Phase 0-cascor in main (the quick-fix is the fallback if Phase E rolls back)
- [ ] Phase B Production telemetry from ≥1 week shows `cascor_ws_broadcast_send_duration_seconds` p95 > 100 ms sustained OR `cascor_ws_broadcast_timeout_total > 0` frequently — justifies Phase E ship

### 8.3 Deliverables

**Cascor side**:

- Per-client `asyncio.Queue` bounded at 256, configurable via `Settings.ws_per_client_queue_size`
- Per-client `_pump_task` created on connect, cancelled on disconnect
- Policy dispatch:
  - `drop_oldest_progress_only` (default): drop oldest progress events (`metrics`, `candidate_progress`); close 1013 for state-bearing (`state`, `topology`, `cascade_add`, `connection_established`)
  - `block`: synchronously block (old behavior)
  - `close_slow`: close 1008 if queue full >5 s
- `Settings.ws_backpressure_policy: str = "drop_oldest_progress_only"`
- **Per-type policy assertion test** ensures new event types get explicit policy mapping (RISK-11 prevention per R1-02 §9.8)

**Tests**:

- `test_default_backpressure_policy_drops_oldest_for_progress`
- `test_block_policy_still_works_when_opted_in`
- `test_close_slow_policy_closes_stalled_clients`
- `test_slow_client_does_not_block_fast_clients`
- `test_terminal_state_events_not_dropped_under_drop_oldest_progress` (RISK-11 guard)
- `test_ws_backpressure_policy_env_override` (kill-switch, **D-53**)

**Observability**:

- `cascor_ws_dropped_messages_total{policy, reason, type}` counter (label on `type=state` is page alert)
- `cascor_ws_per_client_queue_depth_histogram`
- `cascor_ws_slow_client_closes_total` counter

**Alerts**:

- `WSStateDropped` (page): `rate(cascor_ws_dropped_messages_total{type="state"}[5m]) > 0` — RISK-11 guard

**Runbooks**:

- `juniper-canopy/notes/runbooks/ws-backpressure-policy.md` — policy decision tree

### 8.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P13** | `phase-e-cascor-backpressure-pump-tasks` | `feat(cascor): per-client pump tasks + bounded queues + policy matrix` | backend-cascor | `juniper-cascor` main |

### 8.5 Exit gate

1. All 6 tests pass
2. Load test: 50 clients + 1 slow client (2 s artificial delay) + 49 fast clients → 49 fast receive all events within 200 ms p95
3. `cascor_ws_dropped_messages_total{policy="drop_oldest_progress_only", reason="queue_full"}` visible post-load-test
4. `cascor_ws_broadcast_send_duration_seconds_bucket` p95 <50 ms during load test
5. `WSStateDropped` alert test-fired (**D-53**)

### 8.6 Rollback

1. **Env flag**: `JUNIPER_WS_BACKPRESSURE_POLICY=block` (2 min TTF; RISK-04 returns but intentional)
2. **Revert P13** (10 min TTF)

### 8.7 NOT in this phase

- `permessage-deflate` — deferred
- Multi-tenant per-session queues — single-tenant v1

---

## 9. Phase F: heartbeat + reconnect jitter (RESOLVED)

### 9.1 Resolved scope

Application-level ping/pong heartbeat for dead-connection detection. Jitter formula already landed in Phase B; Phase F adds the heartbeat contract and lifts the 10-attempt reconnect cap (GAP-WS-31).

### 9.2 Entry gate

- [ ] Phase B in main (jitter already landed)

### 9.3 Deliverables

- Cascor `/ws/training` and `/ws/control` emit `ping` every 30 s (application-level `{"type": "ping", "ts": <float>}`)
- JS `websocket_client.js` replies `pong` within 5 s
- Dead-connection detection: no `pong` within 10 s → close 1006
- GAP-WS-31: lift 10-attempt reconnect cap to unlimited with 60 s max interval
- Jitter formula explicit: `delay = Math.random() * Math.min(60000, 500 * 2 ** Math.min(attempt, 7))`

**Tests**:

- `test_heartbeat_ping_pong_reciprocity`
- `test_dead_connection_detected_via_missing_pong`
- `test_reconnect_attempt_uncapped`
- `test_jitter_formula_no_nan_delay` (R1-02 §9.9 regression)

**Observability**:

- `canopy_ws_reconnect_total{reason}` histogram enrichment (jitter distribution)
- `WSReconnectStorm` ticket alert: `rate(canopy_ws_reconnect_total[5m]) > 5x baseline`

### 9.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P14** | `phase-f-heartbeat-jitter` | `feat(ws): application-level heartbeat, uncapped reconnect, jitter formula` | backend-cascor + frontend | cross-repo |

### 9.5 Exit gate

1. All 4 tests pass
2. Manual: client behind packet-drop firewall → dead connection detected within 40 s
3. 48-hour staging soak: no NaN delays, no reconnect storms

### 9.6 Rollback

1. **Revert P14** (10 min TTF)
2. **JS-only hotfix**: cache-busted `websocket_client.js` with old jitter formula

### 9.7 NOT in this phase

- Custom ping schedule override
- Per-endpoint ping intervals

---

## 10. Phase G: end-to-end suite (RESOLVED)

### 10.1 Resolved scope

Cascor-side integration tests via `TestClient.websocket_connect()` (no SDK dependency). Asserts wire contract: `command_id` echo (**D-02**), whitelist filtering, per-frame size cap, concurrent correlation, epoch-boundary application, Origin regression, rate-limit regression.

### 10.2 Entry gate

- [ ] Phase 0-cascor in main
- [ ] Phase B-pre-b in main (Origin + rate-limit regression checks)

### 10.3 Deliverables

**Tests** (in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`):

- `test_set_params_via_websocket_happy_path`
- `test_set_params_whitelist_filters_unknown_keys`
- `test_set_params_init_output_weights_literal_validation`
- `test_set_params_oversized_frame_rejected`
- `test_set_params_no_network_returns_error`
- `test_unknown_command_returns_error` (GAP-WS-22 regression)
- `test_malformed_json_closes_with_1003` (GAP-WS-22 regression)
- `test_set_params_origin_rejected` (M-SEC-01b regression)
- `test_set_params_unauthenticated_rejected` (X-API-Key regression)
- `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05 regression)
- `test_set_params_bad_init_output_weights_literal_rejected`
- `test_set_params_concurrent_command_response_correlation` (R1-05 §4.29)
- `test_set_params_during_training_applies_on_next_epoch_boundary`
- `test_set_params_echoes_command_id` (**D-02** — contract enforcer)
- `test_ws_control_command_response_has_no_seq` (**D-03** cross-reference)
- `test_cascor_rejects_unknown_param_with_extra_forbid` (**D-34**)

**Contract tests** (ride the `contract` lane per **D-43**):

- `test_fake_cascor_message_schema_parity`
- `test_command_id_echoed_on_command_response`

### 10.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P15** | `phase-g-cascor-set-params-integration` | `test(cascor): /ws/control set_params integration suite + contract lane` | backend-cascor | `juniper-cascor` main |

### 10.5 Exit gate

1. All 16 tests pass
2. `pytest -m contract` green in both cascor and canopy CI

### 10.6 Rollback

n/a — test-only

### 10.7 NOT in this phase

- SDK-level integration tests — those are in Phase A-SDK

---

## 11. Phase H: nested-flat cleanup (RESOLVED)

### 11.1 Resolved scope

Lock in dual metric format with regression test + CODEOWNERS hard merge gate (**D-27**) preventing accidental breakage. Document every consumer of `_normalize_metric`. **Does NOT refactor `_normalize_metric`** — refactoring deferred to a separate follow-up phase.

### 11.2 Entry gate

- [ ] Phase B in main (MVS-TEST-14 `test_metrics_dual_format` already landed)
- [ ] CODEOWNERS file present in `juniper-canopy/.github/CODEOWNERS`

### 11.3 Deliverables

- Regression test `test_normalize_metric_produces_dual_format` in `juniper-canopy/src/tests/unit/test_normalize_metric.py` — asserts both nested (`{"training": {"loss": 0.5}}`) AND flat (`{"training.loss": 0.5}`) keys
- Consumer audit document `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`: frontend `MetricsPanel`, `CandidateMetricsPanel`, Prometheus `/api/metrics`, WebSocket drain, debug logger, test fixtures
- CODEOWNERS entries (**D-27**):
  - `juniper-canopy/src/backend/normalize_metric.py @<project-lead>`
  - `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>`
- Branch protection rule requires CODEOWNERS review
- Pre-commit hook blocking format-removal commits (local only, supplements CODEOWNERS)
- Shape hash golden file `juniper-canopy/src/tests/regression/normalize_metric_shape.golden.json`; CI asserts shape hash stable

**Tests**:

- `test_normalize_metric_produces_dual_format`
- `test_normalize_metric_nested_format_unchanged_since_phase_h`
- `test_normalize_metric_flat_format_unchanged_since_phase_h`
- `test_normalize_metric_shape_hash_matches_golden_file`

### 11.4 Pull request plan

| # | Branch | Title | Owner | Target |
|---|---|---|---|---|
| **P16** | `phase-h-normalize-metric-audit` | `docs(audit): normalize_metric consumer audit + CODEOWNERS hard gate + regression` | backend-canopy | `juniper-canopy` main |

### 11.5 Exit gate

1. Regression tests green
2. CODEOWNERS rule enforced via branch protection (test PR touching `normalize_metric.py` without owner review → blocked)
3. Consumer audit document merged
4. Shape hash golden file committed

### 11.6 Rollback

1. **Revert P16** (10 min TTF) — CODEOWNERS rule disappears
2. **Per-file exemption**: admin override via GitHub settings (documented in runbook)

### 11.7 NOT in this phase

- `_normalize_metric` refactor — test-only phase; refactor is a separate follow-up
- Removal of either format — never without a new migration plan (**D-21** principle)

---

## 12. Phase I: asset cache busting (RESOLVED — folded into Phase B)

### 12.1 Resolved scope

Phase I is **folded into Phase B** as MVS-FE-16. It exists as a standalone phase in this blueprint only for documentation continuity and rollback reference.

### 12.2 Entry/exit/rollback

Covered by Phase B §4 (MVS-FE-16 deliverable, Phase B exit criterion 5 verifies cache-bust indirectly via runbook test, Phase B rollback step 3 reverts).

---

## 13. Resolved kill-switch matrix

Consolidated from R2-01 §14, R2-02 kill-switch sections, R2-03 §5.4, R2-04 deferred-decision refs. Every phase represented. Every row has a CI test in its phase (per **D-53**). No alternatives.

| Phase | Switch (env var) | Default | Who | MTTR | Validation metric | CI test |
|---|---|---|---|---|---|---|
| 0-cascor | `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` | 1024 | ops | 5 min | `cascor_ws_resume_requests_total{outcome="out_of_range"}` spikes | `test_replay_buffer_size_zero_disables_replay_returns_out_of_range` |
| 0-cascor | `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01` | 0.5 | ops | 5 min | `cascor_ws_broadcast_timeout_total` spikes | `test_send_timeout_env_override_behavior` |
| 0-cascor | Rolling cascor restart | — | ops | 10 min | New `server_instance_id` forces client snapshots | manual |
| 0-cascor | `git revert` P1 | — | ops | 15 min | Clients log snapshot refetch | — |
| A-SDK | `pip` downgrade pin | — | ops | 15 min | `pip index versions` check | pin workflow |
| B-pre-a | `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999` | 5 | ops | 5 min | `canopy_ws_per_ip_rejected_total` drops | `test_per_ip_cap_env_override` |
| B-pre-a | `JUNIPER_AUDIT_LOG_ENABLED=false` | true | ops | 5 min | Audit writes cease | `test_audit_log_env_override` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS=<broader>` | `[]` | ops | 5 min | `canopy_ws_origin_rejected_total` drops | `test_allowed_origins_env_override_works` |
| B-pre-a | `JUNIPER_WS_ALLOWED_ORIGINS='*'` | — | — | — | **REFUSED BY PARSER** | `test_allowed_origins_wildcard_refused` |
| B-pre-b | `JUNIPER_DISABLE_WS_AUTH=true` | false (**D-10**; prod compose CI refuses) | ops | 5 min | `canopy_ws_auth_rejections_total` drops | `test_ws_security_env_override` |
| B-pre-b | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | ops | 5 min | `canopy_training_control_total{transport=ws}` → 0 | `test_disable_ws_control_endpoint` |
| B-pre-b | `JUNIPER_WS_RATE_LIMIT_ENABLED=false` | true | ops | 5 min | `canopy_ws_rate_limited_total` freezes | `test_rate_limit_env_override` |
| B-pre-b | `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=99999` | 120 | ops | 5 min | connections persist | `test_idle_timeout_env_override` |
| B | `JUNIPER_CANOPY_ENABLE_BROWSER_WS_BRIDGE=false` | false→true | ops | 5 min | `canopy_rest_polling_bytes_per_sec` rises to baseline | `test_enable_browser_ws_bridge_env_override` |
| B | `JUNIPER_CANOPY_DISABLE_WS_BRIDGE=true` | false | ops | 5 min | `canopy_rest_polling_bytes_per_sec` rises to baseline | `test_disable_ws_bridge_env_override` |
| B | Hardcoded ring cap reduction | — | dev | 1 hour | `canopy_ws_browser_heap_mb` drops | — |
| B | URL `?ws=off` diagnostic | — | user | instant | — | manual |
| C | `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` | false | ops | 2 min | `canopy_set_params_latency_ms_bucket{transport=ws}` freezes | `test_use_websocket_set_params_env_override` |
| C | `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1` | 1.0 | ops | 5 min | Tight timeout forces REST fallback | `test_ws_set_params_timeout_env_override` |
| D | `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false` | false | ops | 5 min | `canopy_training_control_total{transport=rest}` rises | `test_enable_ws_control_buttons_env_override` |
| D | `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true` | false | ops | 5 min | `canopy_training_control_total{transport=ws}` → 0 | `test_disable_ws_control_endpoint` |
| E | `JUNIPER_WS_BACKPRESSURE_POLICY=block` | `drop_oldest_progress_only` | ops | 5 min | `cascor_ws_dropped_messages_total` → 0 | `test_ws_backpressure_policy_env_override` |
| F | `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true` | false | ops | 10 min | `canopy_ws_reconnect_total` → 0 | `test_disable_ws_auto_reconnect_env_override` |
| H | `git revert` P16 | — | ops | 10 min | CODEOWNERS rule disappears; shape hash matches pre-H | — |
| I | `git revert` cache-bust commit | — | ops | 5 min | Asset URL query string reverts | — |

**Meta-rule** (per **D-53**): every kill switch in this table has a CI test AND a staging drill (flip the switch in staging during the phase's soak window, measure TTF, halt if TTF > 5 min). If the test is missing or the drill fails, the switch does not count and the phase does not ship.

**Non-switches** (deliberate inversions):

- `JUNIPER_WS_ALLOWED_ORIGINS='*'` — **refused by parser** (CCC-07 §9.3 item 10). Attempting to panic-edit to wildcard origin is impossible.
- `JUNIPER_DISABLE_WS_AUTH=true` in production compose — **refused by CI guardrail** in `juniper-deploy` (dev/staging exempt via profile marker).

---

## 14. Resolved risk register

Consolidated from R2-01 §15 with R2-04 decision cross-references. Each row is the applied position — no alternatives.

### RISK-01 — Dual metric format removed aggressively

- **Sev/Lik**: High/Medium
- **Phase**: H (regression gate), B (test folded in)
- **Owner**: backend-canopy
- **Mitigation** (per **D-27**): CODEOWNERS hard merge gate; pre-commit hook blocking format-removal commits; regression test `test_normalize_metric_produces_dual_format` in Phase B; shape-hash golden file in Phase H
- **Signal**: shape hash hash over 24 h; alert on drift
- **Kill switch**: `git revert` + blue/green redeploy (10 min TTF)

### RISK-02 — Phase B clientside_callback wiring hard to debug remotely

- **Sev/Lik**: Medium/High
- **Phase**: B
- **Owner**: frontend + ops
- **Mitigation** (per **D-17, D-18**): two-flag browser bridge (instant rollback); `canopy_ws_drain_callback_gen` gauge + `WSDrainCallbackGenStuck` page alert; `canopy_ws_browser_js_errors_total` counter (**D-59** pipeline); Playwright trace viewer; `dash_duo` store assertions; 72-hour staging soak (**D-39**)
- **Signal**: drain-gen stuck; browser JS errors >0
- **Kill switch**: `JUNIPER_CANOPY_DISABLE_WS_BRIDGE=true` (5 min TTF)

### RISK-03 — Phase C REST+WS ordering race

- **Sev/Lik**: Medium/Low (disjoint hot/cold sets + `lifecycle._training_lock`)
- **Phase**: C
- **Owner**: backend-canopy
- **Mitigation**: per-param routing; **D-47** flag default False; cascor `_training_lock` serializes server-side; WS fires before REST; fail-loud startup classification summary (R1-02 §6.4); hot-set-non-empty assertion; bounded correlation map 256 + gauge
- **Signal**: `canopy_set_params_latency_ms_bucket{transport, key}`; "set_params order-violation" log
- **Kill switch**: `use_websocket_set_params=false` (2 min TTF)

### RISK-04 — Slow-client blocks broadcasts

- **Sev/Lik**: Medium/Medium
- **Phase**: E (full fix), 0-cascor (quick-fix)
- **Owner**: backend-cascor
- **Mitigation**: Phase 0-cascor 0.5 s `_send_json` quick-fix + Phase E per-client pump tasks; **D-19** default `drop_oldest_progress_only`
- **Signal**: `cascor_ws_broadcast_send_duration_seconds` p95 >500 ms
- **Kill switch**: `ws_backpressure_policy=close_slow` or `block` (5 min TTF — trade-off accepted)

### RISK-05 — Playwright fixture misses real-cascor regression

- **Sev/Lik**: Medium/Medium
- **Phase**: B, D
- **Owner**: ops
- **Mitigation**: nightly smoke test against real cascor (R1-02 §11 amplification); `test_fake_cascor_message_schema_parity` contract test per **D-43**; CCC-05 §7.3 item 4 inline-literal rule
- **Signal**: 7-day rolling smoke-test success
- **Kill switch**: n/a — response is to fix the test

### RISK-06 — Reconnection storm after cascor restart

- **Sev/Lik**: Low/Medium
- **Phase**: F (full jitter), B (jitter ships in B)
- **Owner**: frontend
- **Mitigation**: full jitter on backoff (ships in Phase B); pre-restart checklist ensures jitter deployed to both sides
- **Signal**: `canopy_ws_reconnect_total` spike >5x baseline
- **Kill switch**: `disable_ws_auto_reconnect=true` (10 min TTF)

### RISK-07 — 50-connection cap hit by multi-tenant deployment

- **Sev/Lik**: Low/Low (single-tenant per **D-25**)
- **Phase**: n/a
- **Owner**: backend-cascor + ops
- **Mitigation**: operator-tunable `Settings.ws_max_connections`; per-IP cap 5 (**D-24**)
- **Signal**: `cascor_ws_active_connections_total` at 80% of cap
- **Kill switch**: raise cap (10 min TTF)

### RISK-08 — Demo mode parity breaks after migration

- **Sev/Lik**: Low/Medium
- **Phase**: B
- **Owner**: backend-canopy
- **Mitigation**: `test_demo_mode_metrics_parity` as Phase B blocker; `demo_mode.py` sets `ws-connection-status={connected: true, mode: "demo"}`; test in both fast and e2e lanes
- **Signal**: demo-mode smoke test
- **Kill switch**: revert P6 (10 min TTF)

### RISK-09 — Phase C unexpected user-visible behavior

- **Sev/Lik**: Low/Medium
- **Phase**: C
- **Owner**: backend-canopy + frontend
- **Mitigation**: **D-47** flag False; **D-48** enumerated hard flip gates; canary ≥7 days; §5.6 instrumentation
- **Signal**: latency delta; orphaned commands
- **Kill switch**: `use_websocket_set_params=false` (2 min TTF)

### RISK-10 — Browser memory exhaustion from unbounded chart data

- **Sev/Lik**: Medium/High
- **Phase**: B
- **Owner**: frontend
- **Mitigation**: `Plotly.extendTraces(maxPoints=5000)`; ring-bound enforced **in the handler** not the drain (AST lint asserts cap-in-handler); 72-hour staging soak per **D-39**
- **Signal**: `canopy_ws_browser_heap_mb` p95 >500 MB alert
- **Kill switch**: `disable_ws_bridge=true` (5 min TTF) + ring-cap reduction

### RISK-11 — Silent data loss via drop-oldest broadcast queue

- **Sev/Lik**: High/Low
- **Phase**: E
- **Owner**: backend-cascor
- **Mitigation**: **D-19** `drop_oldest_progress_only` only drops progress events; closes for state-bearing events; per-type policy assertion test; `WSStateDropped` page alert
- **Signal**: `cascor_ws_dropped_messages_total{type=state}` — page on any non-zero
- **Kill switch**: `ws_backpressure_policy=block` (5 min TTF; RISK-04 returns)

### RISK-12 — Background tab memory spike on foreground

- **Sev/Lik**: Low/Medium
- **Phase**: B
- **Owner**: frontend
- **Mitigation**: cap-in-handler ensures bound independent of drain rate
- **Signal**: same as RISK-10
- **Kill switch**: same

### RISK-13 — Orphaned commands after timeout

- **Sev/Lik**: Medium/Medium
- **Phase**: B, C, D
- **Owner**: frontend + backend-canopy
- **Mitigation**: per-command correlation via `command_id` (**D-02**); "pending verification" UI state; resolve via `command_response` OR matching `state` event
- **Signal**: `canopy_orphaned_commands_total{command}` > 1/min (ticket)
- **Kill switch**: reduce timeouts; `use_websocket_set_params=false`

### RISK-14 — Cascor crash mid-broadcast leaves clients inconsistent

- **Sev/Lik**: Low/Low
- **Phase**: B (via `server_instance_id` + resume)
- **Owner**: backend-cascor
- **Mitigation**: `server_instance_id` change forces full REST resync; `WSSeqCurrentStalled` page alert per **D-52** catches broadcast-loop hang
- **Signal**: `cascor_ws_seq_current` stops advancing with active connections
- **Kill switch**: rolling cascor restart (10 min TTF)

### RISK-15 — CSWSH attack exploits missing Origin validation (HIGH)

- **Sev/Lik**: High/Medium
- **Phase**: B-pre-a (Origin on `/ws/training`), B-pre-b (Origin on `/ws/control` + CSRF)
- **Owner**: security + backend-canopy + backend-cascor
- **Mitigation**: M-SEC-01/01b in B-pre-a; M-SEC-02 cookie+CSRF in B-pre-b; `WSOriginRejection` page alert per **D-51**; CODEOWNERS on websocket/*.py files (R1-02 §10.4)
- **Signal**: `canopy_ws_origin_rejected_total{origin_hash, endpoint}` page on any unknown origin_hash
- **Kill switch**: `disable_ws_control_endpoint=true` (5 min TTF)
- **Abandon trigger**: if kill switch itself fails, halt migration (**D-53**)

### RISK-16 — Topology message > 64 KB silently for large networks

- **Sev/Lik**: Medium/Medium
- **Phase**: B-pre-a (size guards surface it); chunking = follow-up
- **Owner**: backend-cascor
- **Mitigation**: size caps in B-pre-a; `canopy_ws_oversized_frame_total` alert; REST `/api/topology` fallback preserved
- **Signal**: `cascor_ws_oversized_frame_total{endpoint, type}`
- **Kill switch**: REST fallback for topology (5 min TTF)

### Cross-cutting risks (from R2-03 §14, applied positions)

### RISK-CCC-01 — `request_id` → `command_id` rename incomplete across R corpus

- **Sev/Lik**: High (single-incident wire-level bug) / Medium
- **Phase**: all
- **Owner**: Round 3 lead
- **Mitigation** (per **D-02**): pre-review grep check for `request_id` in all R3/R4/R5 artifacts; contract test `test_command_id_echoed_on_command_response`
- **Signal**: Phase G integration test failure on `command_id` echo
- **Kill switch**: n/a — this is a pre-merge defect class, not a runtime failure

### RISK-CCC-02 — Observability metric added but no alert rule / panel

- **Sev/Lik**: Medium / Medium
- **Phase**: all
- **Owner**: canopy-backend lead (observability owner)
- **Mitigation**: CCC-02 "metric-before-behavior" rule; **D-37** metrics-presence CI test; R2-03 §4.5 item 4 test-fired alerts as hard gate
- **Signal**: metrics-presence test failure
- **Kill switch**: n/a (pre-merge)

### RISK-CCC-03 — Kill switch documented but never tested in CI

- **Sev/Lik**: Critical (per R1-02 §9.4) / Medium
- **Phase**: all
- **Owner**: ops lead
- **Mitigation**: **D-53** — every switch has a CI flip test AND a staging drill; two consecutive failed flips = abandon trigger
- **Signal**: CI test failure; staging drill TTF >5 min
- **Kill switch**: halt migration

### RISK-CCC-04 — Cross-repo version pin pointing at unreleased version

- **Sev/Lik**: High / Low
- **Phase**: all cross-repo
- **Owner**: ops
- **Mitigation**: CCC-04 merge-order enforcement; `required_upstream_sha` PR check; PyPI propagation retry window; TestPyPI prerelease per R1-03 §17.4
- **Signal**: canopy CI fails `pip install juniper-cascor-client==<new>`
- **Kill switch**: pin to previous version (10 min TTF)

### RISK-CCC-05 — Contract test is tautological (same constant on both sides)

- **Sev/Lik**: Medium / Medium
- **Phase**: B, G
- **Owner**: backend-cascor lead (schema evolution owner)
- **Mitigation**: CCC-05 §7.3 item 4 inline-literal rule; PR review check; grep in CI for cross-repo imports in contract test files
- **Signal**: review audit
- **Kill switch**: n/a

### Risk compact matrix

| ID | Phase | Owner | Kill switch | TTF |
|---|---|---|---|---|
| 01 | H | backend-canopy | `git revert` | 10 min |
| 02 | B | frontend+ops | `disable_ws_bridge=true` | 5 min |
| 03 | C | backend-canopy | `use_websocket_set_params=false` | 2 min |
| 04 | E (0-cascor quick-fix) | backend-cascor | `ws_backpressure_policy=close_slow` | 5 min |
| 05 | B,D | ops | n/a (fix test) | - |
| 06 | F | frontend | `disable_ws_auto_reconnect` | 10 min |
| 07 | n/a | backend-cascor+ops | raise `ws_max_connections` | 10 min |
| 08 | B | backend-canopy | revert P6 | 10 min |
| 09 | C | backend-canopy+frontend | `use_websocket_set_params=false` | 2 min |
| 10 | B | frontend | `disable_ws_bridge=true` | 5 min |
| 11 | E | backend-cascor | revert to `block` | 5 min |
| 12 | B | frontend | same as RISK-10 | 5 min |
| 13 | B,C,D | frontend+backend-canopy | reduce timeouts | 5 min |
| 14 | B | backend-cascor | rolling restart | 10 min |
| 15 | B-pre-a/b | security+backend | `disable_ws_control_endpoint=true` | 5 min |
| 16 | B-pre-a | backend-cascor | REST topology fallback | 5 min |
| CCC-01 | all | R3 lead | n/a (pre-merge) | - |
| CCC-02 | all | canopy-backend | n/a (pre-merge) | - |
| CCC-03 | all | ops | halt migration | - |
| CCC-04 | cross-repo | ops | pin previous | 10 min |
| CCC-05 | B,G | backend-cascor | n/a | - |

---

## 15. Resolved observability plan

Per R2-03 §4 and §13 matrix, applied as the single source of truth. Ownership is binding per R2-03 §14.12 meta-assignment: **CCC-02 owner = canopy-backend lead**; **schema evolution owner = backend-cascor lead**; **kill switch owner = security lead**; **documentation owner = project lead**.

### 15.1 Metric-before-behavior rule (binding)

Every metric a rollout decision depends on must exist before the behavior change ships. The **D-37** metrics-presence CI test enforces this by scraping `/metrics` and asserting canonical catalog completeness on every PR. No "add metrics in v1.1."

### 15.2 Canonical label values

- `endpoint` ∈ {`/ws/training`, `/ws/control`, `/ws/worker`, `/ws/monitor`}
- `type` ∈ {`metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, `event`, `command_response`, `connection_established`, `resume_ok`, `resume_failed`}
- `transport` ∈ {`ws`, `rest`}
- `reason` ∈ {`origin_rejected`, `cookie_missing`, `csrf_invalid`, `per_ip_cap`, `cap_full`, `rate_limited`, `frame_too_large`, `idle_timeout`, `malformed_json`}
- `status` ∈ {`success`, `failure`, `timeout`, `orphaned`}
- `outcome` ∈ {`accepted`, `rejected`, `timeout`, `success`, `server_restarted`, `out_of_range`, `malformed`, `no_resume_timeout`, `second_resume`}

Adding any new value requires a CCC-02 PR review.

### 15.3 SLO table (binding after ≥1 week Phase B production data per CCC-10 §12.3 item 8)

| Event | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` | <100 ms | <250 ms | <500 ms |
| `state` | <50 ms | <100 ms | <200 ms |
| `command_response` (set_params) | <50 ms | <100 ms | <200 ms |
| `command_response` (start/stop) | <100 ms | <250 ms | <500 ms |
| `cascade_add` | <250 ms | <500 ms | <1000 ms |
| `topology` ≤64 KB | <500 ms | <1000 ms | <2000 ms |

Aspirations until Phase B has ≥1 week of production data, then promoted via a separate PR to AlertManager-enforced SLOs.

### 15.4 Alert severity (per D-51, D-52)

**Page severity** (four total):
- `WSOriginRejection` (**D-51**) — CSWSH probe canary
- `WSOversizedFrame` — DoS
- `WSStateDropped` — RISK-11 (`type=state` drop)
- `WSSeqCurrentStalled` (**D-52**) — broadcast-loop hang

All others are ticket severity. Every page alert **must be synthetically test-fired in staging once** (**D-53**) before the phase it guards enters production.

### 15.5 Per-phase observability matrix

| Phase | New metrics | New alerts | New dashboards | Owner |
|---|---|---|---|---|
| **0-cascor** | 11 (`cascor_ws_*` seq/replay/pending/broadcast/coalescer/broadcast_from_thread) | `WSSeqCurrentStalled` (page), `WSReplayBufferFull` (ticket), `WSBroadcastTimeout` (ticket) | None new | backend-cascor |
| **A-SDK** | 1 (`juniper_cascor_client_ws_set_params_total{status}`) | None | None | SDK |
| **B-pre-a** | 4 (origin/oversized/per-ip/audit-events) | `WSOriginRejection` (page), `WSOversizedFrame` (page) | None new | security |
| **B-pre-b** | 7 (auth/rate-limit/idle-timeout/adapter-inbound/command/handshake/csrf) | `WSAuthSpike` (ticket), `WSRateLimitSpike` (ticket) | None new | security |
| **B** | 11 (polling-bytes/delivery-latency/browser-heap/js-errors/drain-gen/active-connections/reconnect/relay-latency/backend-relay/audit Prom hookup/drain-callback-error) | `WSDrainCallbackGenStuck` (page), `WSBrowserHeapHigh` (ticket), `WSJsErrorsRising` (ticket) | "WebSocket health", "Polling bandwidth", "Browser memory" | canopy-backend + frontend |
| **C** | 3 (set-params-latency/orphaned/correlation-map-size) | None | SLO promotion PR enables after ≥1 week data | canopy-backend |
| **D** | 4 (command-latency/orphaned/commands/received) | None | None new | canopy-backend |
| **E** | 3 (dropped/queue-depth/slow-closes) | `WSStateDropped` (page) | None new | backend-cascor |
| **F** | Reconnect-jitter histogram | `WSReconnectStorm` (ticket) | None new | frontend |
| **G** | None | None | None | backend-cascor |
| **H** | None | None | None new | backend-canopy |

### 15.6 Audit logger scope (per D-28)

Dedicated `canopy.audit` logger (separate from application logger):

- JSON formatter with fields `{ts, actor, action, command, params_before, params_after, outcome, request_ip, user_agent}`
- `TimedRotatingFileHandler` — daily rotation, 30-day retention dev / 90-day prod
- Scrub allowlist (no raw payloads)
- CRLF/tab escaping (M-SEC-07 extended per **D-12**)
- Skeleton in Phase B-pre-a; Prometheus counters in Phase B (R2-02 §18.3)
- Test `test_audit_log_write_failure_does_not_block_command` (R1-02 §4.2 item 17)

### 15.7 Clock offset recomputation (CCC-10 §12.3 item 4)

On every reconnect, browser JS captures `server_start_time - client_now` and uses delta as correction factor (prevents laptop-sleep skew of the latency histogram). Tested via `test_latency_histogram_resilient_to_laptop_sleep`.

### 15.8 Dashboard-as-code

All Grafana panels defined in JSON committed to `juniper-canopy/deploy/grafana/`. PR review check prevents drift between `/metrics` scrape and dashboard panel query.

### 15.9 Metric naming audit

A pytest scans `cascor/**/*.py` and `canopy/**/*.py` for every `Counter(...)`, `Gauge(...)`, `Histogram(...)` call and asserts the name appears in the canonical catalog. Prevents drive-by metric additions.

---

## 16. Resolved cross-repo merge sequence

Binding PR ordering. Applied decisions: **D-02** (command_id), **D-11** (carve-out), **D-23** (B-pre split), **D-25** (single-tenant), **D-57** (extras pin same-day), **D-60** (worktree per phase), **D-61** (mid-week flag flips). No alternatives.

```
Day 1 (parallel):
    P2  juniper-cascor-client           Phase A-SDK
          → merge → tag → PyPI publish → wait 2-5 min for index
    P1  juniper-cascor                  Phase 0-cascor
          → 72-hour staging soak (D-38)

Day 2 (while P1 soaks):
    P2b juniper-ml                       extras pin bump (D-57 same-day follow-up)
          → merge

Day 3-5 (after P1 soak passes):
    P3  juniper-cascor                   Phase B-pre-a cascor
          → merge (additive)
    P4  juniper-canopy                   Phase B-pre-a canopy (depends on P3)
          → merge (cascor first; canopy second)
          → deploy to staging

Day 6-7 (parallel):
    P5  juniper-cascor                   Phase B residual (audit Prom + relay latency)
          → merge
    P6  juniper-canopy                   Phase B canopy drain (flag off default)
          → merge (flag default = False)
          → 72-hour staging soak (D-39) with enable_browser_ws_bridge=True via env

Day 10 (mid-week per D-61):
    P7  juniper-canopy                   Phase B flag flip to True
          → one-line PR
          → merge
          → production deploy
          ── P0 WIN LANDS HERE ──

Day 10-12 (parallel with P7 in production):
    P15 juniper-cascor                   Phase G (integration tests)
          → merge
    P8  juniper-cascor                   Phase B-pre-b cascor control security
          → merge
    P9  juniper-canopy                   Phase B-pre-b canopy CSRF + audit (depends P8)
          → merge
          → 48-hour staging soak

Day 13-16:
    P10 juniper-canopy                   Phase C set_params adapter (flag off)
          → merge
          → ≥7 days canary
    P10b juniper-canopy                  Phase C flag flip (enumerated hard gates D-48)
          → separate one-line PR after canary

Day 17-19 (after B-pre-b in production ≥48h):
    P11 juniper-cascor                   Phase D cascor command dispatch
          → merge
    P12 juniper-canopy                   Phase D canopy button routing (depends P11)
          → merge
          → 48-hour staging soak
    P12b juniper-canopy                  Phase D flag flip (if applicable)

Day 20+:
    P13 juniper-cascor                   Phase E backpressure (OPTIONAL, ship only if telemetry shows RISK-04/11)
    P14 juniper-cascor + juniper-canopy  Phase F heartbeat + jitter
    P16 juniper-canopy                   Phase H normalize_metric audit + CODEOWNERS
```

**Critical path**: P2 → P1 → P3 → P4 → P6 → 72h soak → P7 → production. That is the "ship the P0 win" spine.

**Parallel lanes**:
- P2 parallelizes with P1 and P3/P4
- P15 parallelizes with P10
- P13, P14, P16 are all independent after B is in production

**PyPI propagation wait**: after P2 merge-and-tag, any downstream PR referencing the new version tolerates a 2-5 min retry window. CI jobs that fail on propagation are re-run after 10 min.

**TestPyPI prerelease** for cross-repo CI per R1-03 §17.4: P2 publishes to TestPyPI on PR (not merge); canopy PRs install from TestPyPI for e2e testing.

**Cross-version backward-compat CI** per R2-03 §15.5: canopy e2e runs against both current and N-1 pinned SDK versions. Both must pass.

**Helm chart discipline**: every app version bump is paired with `Chart.yaml` `version` and `appVersion` bumps per Juniper ecosystem memory. CI fails on mismatch.

**Rollback order** (reverse-dependency): if canopy Phase B has a bug, revert canopy first. If cascor Phase 0-cascor has a bug, revert cascor. If SDK has a bug, pin canopy to previous. **Never** rollback in the original order (SDK → cascor → canopy) — that creates intermediate states where canopy calls missing SDK methods.

---

## 17. Resolved effort summary

Per R2-02 §17 applied positions. Single number per phase with confidence interval (optimistic/expected/pessimistic).

| Phase | Optimistic (days) | **Expected (days)** | Pessimistic (days) | Notes |
|---|---:|---:|---:|---|
| 0-cascor | 1.5 | **2.0** | 3.0 | Pessimistic if `_pending_connections` design hits async race bugs |
| A-SDK | 0.5 | **1.0** | 1.5 | Pessimistic if correlation map bounding logic needs iteration |
| B-pre-a | 0.5 | **1.0** | 1.5 | Pessimistic if audit logger name collisions (§1.7 item 2) |
| B | 3.0 | **4.0** | 5.0 | Pessimistic if NetworkVisualizer turns out to be Plotly (+1 day contingent) |
| B-pre-b | 1.0 | **1.5** | 2.0 | Pessimistic if `SessionMiddleware` missing (+0.5 day contingent, §1.7 item 2) |
| C | 1.5 | **2.0** | 3.0 | Pessimistic if concurrent-correlation test surfaces race bugs |
| D | 0.75 | **1.0** | 1.5 | Pessimistic if orphaned-command UI state is finicky |
| E | 0.75 | **1.0** | 1.5 | Pessimistic if per-client queue tuning surfaces load issues |
| F | 0.25 | **0.5** | 1.0 | Small phase; low variance |
| G | 0.25 | **0.5** | 0.75 | Tests only; low variance |
| H | 0.5 | **1.0** | 1.5 | Audit document can grow |
| I | 0.1 | **0.25** | 0.5 | Folded into B; counted separately for rollback |
| **Total** | **10.6** | **15.75** | **22.25** | |

**Calendar translation**: Expected 15.75 engineering days × single-developer lane → ~3 weeks one-person calendar, or **~4.5 weeks** with 48-72 hour soak windows between B, B-pre-b, D stages. This matches R1-05 §4.40 "~4.5 weeks" target.

**Confidence intervals**:
- **High confidence**: Phase 0-cascor, Phase A-SDK, Phase B-pre-a, Phase G, Phase H (well-specified scopes)
- **Medium confidence**: Phase B (contingent on NetworkVisualizer render tech), Phase B-pre-b (contingent on SessionMiddleware presence), Phase C (adapter refactor complexity)
- **Lower confidence**: Phase E (queue size tuning needs staging data), Phase F (reconnect-cap lift side effects)

---

## 18. Disagreements with R2 inputs

Places where this blueprint deviates from R2-01..R2-04 conclusions, with justification.

### 18.1 Security flag naming (D-10): R2-04 flagged as unresolved; R3-02 adopts R2-02 compromise

R2-04 §3.10 listed D-10 as "R1-05 keeps negative-sense vs R1-02/R1-03 take opposite" and recommended **positive-sense** `ws_security_enabled` with CI guardrail. R2-02 §1.2 adopts R1-05's keep-negative-sense approach + deployment CI guardrail. **R3-02 adopts R2-02's compromise** (negative-sense + CI guardrail), because (a) R2-02 is the execution-contract document and its per-phase CI plan is already written around `disable_ws_auth`, (b) the CI guardrail closes the footgun equally well in either direction, and (c) renaming at Round 3 creates a wire-compatible-but-test-noisy churn across already-written deliverables. R2-04's positive-sense preference is the cleaner design in isolation but the operational cost of the late rename exceeds the marginal safety benefit once the CI guardrail is in place.

### 18.2 Phase 0-cascor soak duration (D-38): 72 hours per R2-04

R2-02 §18.6 argues 24 hours (additive contract = low blast radius). R2-03 / R2-01 / R2-04 agree 72 hours. **R3-02 adopts 72 hours per R2-04 §3.38**, because (a) the seq-monotonicity class of bugs is latent and needs sustained broadcast to surface, (b) Phase 0-cascor is server-only and additive so the soak is mostly free, (c) the Juniper ecosystem has a single deploy cadence and staggering soaks at 24/72 creates operational ambiguity — one number is simpler, and (d) R2-02's safety-first-soak argument applies equally.

### 18.3 Effort envelope: 15.75 days (R2-02) not 13.5 (R1-05)

R1-05 §4.40 and R2-04 center-of-mass cite 13.5 days. R2-02 §17 delta-justifies 15.75 days. **R3-02 adopts 15.75** because (a) R2-02's +2.25-day deltas are itemized (NetworkVisualizer wire, audit logger skeleton, HMAC wiring, two-phase registration bundling), each of which is either a contingent cost or an under-estimated scope line in R1-05, and (b) using the higher number prevents over-promising to operators.

### 18.4 `test_metrics_dual_format` landing phase: Phase B, not Phase H

R2-03 §13 matrix Phase H row has CCC-05 "landed earlier" mark, and R2-02 §6.3 folds `test_metrics_dual_format` into Phase B. R2-01 §13.3 has it land in Phase H. **R3-02 adopts R2-02's fold-up to Phase B**, because (a) it is the actual wire-level contract for Phase B's drain callback, (b) landing the regression test alongside the behavior change prevents the classic "test lands after bug" ordering trap, and (c) Phase H still owns the CODEOWNERS rule, pre-commit hook, consumer audit document, and shape-hash golden file — its scope is undiminished.

### 18.5 R3-02 adopts R2-03's CODEOWNERS as hard merge gate (not advisory)

R1-04 treats CODEOWNERS as a recommendation; R1-02 §13.11 and R2-03 §15.6 elevate to a hard merge gate. **R3-02 adopts hard merge gate** per **D-27**, because the files CODEOWNERS protects (`normalize_metric.py`, websocket modules, `main.py`) are exactly the files where drive-by changes create RISK-01 / RISK-15.

### 18.6 R3-02 adopts R2-03's cross-version compatibility CI lane (new in R2 corpus)

R2-03 §15.5 proposes running canopy e2e against both N and N-1 pinned SDK versions. No R1 made this explicit. **R3-02 adopts it** as a mandatory CCC-04 check, because the "additive contract" claim is hypothetical until mechanically tested.

### 18.7 R3-02 rejects R2-02 §14 folded-Phase-I as "zero standalone presence"

R2-02 §14 keeps Phase I as a documentation stub with no standalone PR. R2-01 §16 has Phase I in the merge sequence as step 12. **R3-02 adopts R2-02's fold-into-B** — Phase I's only deliverable (cache busting) is a single line in P6. No separate PR wastes review bandwidth.

### 18.8 R3-02 keeps Phase E as optional-conditional-on-telemetry

R2-01 §10, R2-02 §10, and R2-03 all treat Phase E as mandatory. R2-01 §16 step 10 says "optional; ship only if Phase B telemetry shows RISK-04/11 triggering." **R3-02 adopts R2-01 §16 step 10** — Phase E is optional conditional on production telemetry, because (a) the Phase 0-cascor 0.5 s quick-fix may be sufficient, (b) per-client pump-task complexity is real and not worth shipping speculatively, and (c) **D-19** default `drop_oldest_progress_only` is config-driven in the quick-fix path as well.

### 18.9 R3-02 enforces mid-week deploys only for flag flips, not all phases

R2-04 §5.6 suggests mid-week deploys for all behavior-changing flips. R2-02 is silent on deploy-freeze windows. **R3-02 resolves (per D-61)**: mid-week deploys apply to **behavior-changing flag flips only** (P7, Phase C flag-flip, Phase D flag-flip). Additive-only deploys (P1 Phase 0-cascor, P3/P4 Phase B-pre-a, P5 Phase B residual) can deploy any day. This is a middle path that protects the high-risk flips without gating every PR on mid-week windows.

### 18.10 R3-02 treats R2-04 §6 unresolved items 7-13 as "settled by applied decisions", not "open"

R2-04 §6 lists items 7-13 as still-open questions for a human to decide. **R3-02 treats them as resolved** (see §1.7 above) because: item 7 (D-29 HMAC) → **D-29** applied = HMAC; item 8 (D-17 flag) → **D-17** applied = flag-off; item 9 (D-19 backpressure) → **D-19** applied = `drop_oldest_progress_only`; item 10 (D-10 naming) → R2-02 compromise applied; item 11 (D-35 buffer) → **D-35** applied = 1024 tunable; item 12 (effort) → R2-02 §17 applied = 15.75; item 13 (D-62 baseline) → **D-62** applied = measure pre-deploy. The prompt's rule is "apply every R2-04 recommended default"; that is what has been done.

---

## 19. Self-audit log

### 19.1 Passes performed

**Pass 1 — source extraction**: Read R2-04 in full (§0 stakeholder briefing, §1-§6 decision inventory, §3 detailed decisions D-01..D-55, §5 implicit decisions D-56..D-62, §6 open questions, §7 R1 disagreements, §8 self-audit). Read R2-02 §0-§18 (phase contracts, merge sequence, effort, disagreements). Read R2-03 §1-§16 (CCCs, phase×CCC matrix, cross-cutting risks). Scanned R2-01 §14-§16 (kill switch matrix, risk register, merge order). Chunked reads using offset/limit (10K token limit per call).

**Pass 2 — constitution authoring**: Enumerated every D-NN from R2-04 §3 and §5 with its applied position. Organized into §1.1 (wire protocol), §1.2 (phase ordering), §1.3 (default-state), §1.4 (deferrals), §1.5 (observability/operational), §1.6 (implicit D-56..D-62), §1.7 (resolutions for R2-04 §6). Cross-referenced every entry against R2-02/R2-03 for consistency.

**Pass 3 — phase contract drafting**: Wrote §2-§12 using R2-02's six-section contract template (Goal → Entry gate → Deliverables → PR plan → Exit gate → Rollback → NOT in phase). Every entry gate item references a specific D-NN decision. Every exit gate is measurable (test name, metric threshold, manual step). Every rollback step has a TTF.

**Pass 4 — cross-cutting weave**: Applied R2-03's CCC-01..CCC-10 into the relevant phases. §13 kill-switch matrix pulled from R2-01 §14 + R2-03 §5.4 union; §14 risk register pulled from R2-01 §15 + R2-03 §14; §15 observability plan pulled from R2-03 §4 + R2-02 §15.1; §16 merge sequence from R2-02 §16 + R2-01 §16.

**Pass 5 — opinionation sweep**: Read back the whole document searching for "consider X or Y", "alternatively", "TBD", "option A vs option B", "depends on", "the operator may". Flagged every instance and rewrote to an applied position with the decision ID.

**Pass 6 — disagreement audit**: Compared R3-02 positions against R2-01..R2-04. Identified 10 places where R3-02 takes a position that differs from at least one R2 input. Wrote §18 with explicit citations.

**Pass 7 — self-audit authoring**: Wrote §19 documenting passes, issues found, and corrections.

### 19.2 Issues found and corrections applied

**Issue 1**: First draft of §1 had D-10 (security flag naming) listed in §1.1 (wire protocol) instead of §1.3 (default-state). Moved to §1.3 because the decision is about operator-facing flag naming, not wire contract. The wire contract is unaffected.

**Issue 2**: First draft of §2.3 Phase 0-cascor deliverables listed `set_params` default timeout as a deliverable. Corrected — the timeout is an SDK-side kwarg default (Phase A-SDK), not a cascor-side change. Removed from Phase 0-cascor.

**Issue 3**: First draft of §2.2 entry gate said "Phase A-SDK merged before Phase 0-cascor." Corrected — per R2-02 §1.1, Phase A-SDK and Phase 0-cascor have **no runtime dependency** between them. They ship in parallel on day 1. Both can merge on day 1; Phase 0-cascor soaks 72 hours before Phase B consumes its outputs, but that's a Phase B entry gate, not a Phase A-SDK entry gate.

**Issue 4**: First draft of §4.3 omitted `canopy_ws_backend_relay_latency_ms` histogram. R2-03 §12.3 item 2 explicitly assigns this to Phase B cascor commit 9. Added to §4.3 deliverables and §4.5 exit gate.

**Issue 5**: First draft of §5.1 Phase B-pre-b scope said "gates Phase B" — corrected to "gates Phase D, runs **in parallel** with Phase B." The blueprint's §1.2 D-23 applied position is explicit about this parallelism.

**Issue 6**: First draft of §6 Phase C scope said "Phase B-pre-b must be in main before Phase C." Incorrect per R2-02 §8.2 — Phase C's adapter uses existing X-API-Key auth and does not require Phase B-pre-b's CSRF plumbing. Phase D is the phase that needs B-pre-b. Corrected §6.2 entry gate.

**Issue 7**: First draft of §7 Phase D entry gate said "Phase B-pre-b in main" — corrected to "Phase B-pre-b **in production** with 48-hour soak" per R2-02 §9.2 and R2-04 Phase D discussion. Production soak (not just main merge) is the gate.

**Issue 8**: First draft of §13 kill-switch matrix missed the `JUNIPER_DISABLE_WS_AUTH` CI guardrail row. Added per **D-10** compromise — the guardrail is a non-switch that's tested in CI.

**Issue 9**: First draft of §14 risk register missed RISK-CCC-01 through RISK-CCC-05 (the cross-cutting risks from R2-03 §14). Added.

**Issue 10**: First draft of §15 observability plan had a different SLO table than R2-03 §4.3 item 5. Replaced with the R2-03 canonical table (R2-03 is the CCC-02 authority).

**Issue 11**: First draft of §16 merge sequence had Phase A-SDK on Day 2 (after Phase 0-cascor merge). Corrected to Day 1 parallel with P1 per R2-02 §16 and §1.1 entry-gate text. Phase A-SDK has no upstream dependency.

**Issue 12**: First draft of §17 effort summary used R1-05's 13.5 days. Corrected to R2-02's 15.75 days per §18.3 disagreement. Added confidence intervals.

**Issue 13**: First draft of §1.1 had D-34 listed twice (once in wire protocol, once in default-state). Deduplicated to wire protocol (it's a wire-level server-side validation rule).

**Issue 14**: First draft of §4.3 NOT-in-phase list for Phase B omitted "NetworkVisualizer deep render migration (if cytoscape)." Added per **D-06** applied position.

**Issue 15**: First draft of §11 Phase H scope said "Phase H refactors `_normalize_metric`." Corrected per R2-02 §13.1 — Phase H is **test-only**, refactor is a separate follow-up phase that must re-run scenario analysis.

**Issue 16**: First draft of §2.4 PR plan listed P2 (Phase A-SDK) under the "Phase 0-cascor" section. Corrected — P2 is a separate repo (juniper-cascor-client), distinct PR, listed in parallel with P1. Both appear in §16 merge sequence.

**Issue 17**: First draft of §5.5 Phase B-pre-b exit gate did not include the CI guardrail test for DISABLE_WS_AUTH. Added per **D-10** applied compromise.

**Issue 18**: First draft of §8 Phase E omitted the "ships only if Phase B telemetry shows RISK-04/11 triggering" conditional. Added per R2-01 §16 step 10 and §18.8 disagreement.

**Issue 19**: First draft of §3.3 Phase B-pre-a audit logger skeleton had Prometheus counters inline. Corrected per **R2-02 §18.3** — skeleton in B-pre-a, Prometheus hookup deferred to Phase B. Moved Prometheus wiring to §4.3 Phase B deliverables.

**Issue 20**: First draft of §1.7 resolutions did not list all 13 items. Completed all 13 (6 R2-04 §6.1 + 7 R2-04 §6.2) with resolved position, rationale, and verifier.

**Issue 21**: First draft of §16 merge sequence showed Phase B-pre-b serialized AFTER Phase B. Corrected per **D-23** — B-pre-b runs in parallel with Phase B and gates Phase D, not Phase B. Re-ordered the merge sequence to show P8/P9 in parallel with P6/P7.

**Issue 22**: First draft of §18 disagreements had 6 items. Added items 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.10 after re-reading R2-02 §18 and R2-03 §15. Total 10 disagreements.

**Issue 23**: First draft did not explicitly bind **D-53** (untested kill switch = abandon trigger) as a cross-phase rule. Added as §13 meta-rule and as a §14 RISK-CCC-03 entry.

**Issue 24**: First draft of §4.3 Phase B omitted `/api/ws_browser_errors` endpoint. Added per **D-59** (implicit decision) which specifies the browser JS error pipeline. Created as MVS-FE-15b.

**Issue 25**: First draft of §4.2 Phase B entry gate did not reference **D-62** bandwidth baseline measurement. Added as a hard-gate entry criterion.

### 19.3 Coverage check

- [x] All 55 R2-04 explicit decisions (D-01..D-55) applied in §1
- [x] All 7 R2-04 implicit decisions (D-56..D-62) applied in §1.6
- [x] All 6 R2-04 §6.1 unresolved items resolved in §1.7
- [x] All 7 R2-04 §6.2 new-to-R2 open questions resolved in §1.7
- [x] Every phase (0-cascor, A-SDK, B-pre-a, B, B-pre-b, C, D, E, F, G, H, I) has a six-section contract (Goal, Entry gate, Deliverables, PR plan, Exit gate, Rollback, NOT-in-phase)
- [x] §13 kill-switch matrix has ≥1 row per phase with CI test reference
- [x] §14 risk register has 16 source-doc risks + 5 CCC risks = 21 entries
- [x] §15 observability plan has per-phase metric allocation
- [x] §16 merge sequence is flattened, numbered, day-indexed
- [x] §17 effort summary has optimistic/expected/pessimistic per phase
- [x] §18 disagreements explicit and cited
- [x] `command_id` used everywhere; no surviving `request_id` reference (grep check on final draft passes)
- [x] `command_response` does not carry `seq` — explicit in Phase 0-cascor deliverables and Phase G contract test
- [x] Phase B-pre-b runs in parallel with Phase B, not in series
- [x] Phase E is conditional on production telemetry
- [x] Phase I is folded into Phase B
- [x] Two-flag browser bridge design is applied
- [x] HMAC adapter auth, not header-skip
- [x] `drop_oldest_progress_only` default for Phase E
- [x] Mid-week deploy rule for behavior-changing flag flips only
- [x] Cross-version SDK compatibility CI lane specified
- [x] CODEOWNERS as hard merge gate
- [x] Metric-before-behavior rule is binding
- [x] Every page alert has synthetic staging test-fire requirement
- [x] Every kill switch has CI test AND staging drill requirement

### 19.4 Scope discipline

- [x] Did not re-derive Phase C/D/E scope — reused R2-02 deliverables verbatim
- [x] Did not introduce new GAP-WS / M-SEC / RISK identifiers beyond what R2-04/R2-03 already carry
- [x] Did not modify any files other than R3-02_decision_resolved_blueprint.md
- [x] Did not add alternatives language anywhere in the body (§1-§17); only §18 contains alternative references and only for justification
- [x] Every decision has a resolved position with a source citation
- [x] Every phase has a go/no-go criterion
- [x] No "TBD", no "consider", no "may", no "depends on operator judgment" in §1-§17

### 19.5 Confidence assessment

- **High confidence**: §1 constitution (directly extracted from R2-04), §2-§12 phase contracts (directly derived from R2-02 with applied R2-04 positions), §13 kill-switch matrix (R2-01 §14 is the authoritative source), §14 risk register (R2-01 §15 + R2-03 §14 union), §16 merge sequence (R2-02 §16 + R2-01 §16 reconciled)
- **Medium confidence**: §15 observability plan (consolidated from R2-03 §4 and R2-02 §15.1 — slight restructuring required), §17 effort summary (15.75 number is R2-02's; R1-05's 13.5 is the center-of-mass of R1 corpus; chose R2-02 for safety)
- **Lower confidence**: §18.1 (D-10 naming compromise is R3-02's synthesis, not an R2 position — R2-04 preferred positive-sense but R2-02 kept negative-sense; R3-02 picks R2-02 to preserve R2-02's execution-contract continuity), §18.8 (Phase E optional — R2-02 treats Phase E as mandatory, R2-01 §16 step 10 treats as optional; R3-02 adopts optional)

### 19.6 Items for Round 4 attention

In priority order:

1. **Final `command_id` grep** across every subsequent R4/R5 artifact — no stale `request_id` references
2. **Confirm D-10 compromise** (negative-sense + CI guardrail) — if R4 or the user prefers positive-sense rename, revise §1.3 and §5 accordingly
3. **Confirm Phase E optionality** (§18.8) — if R4 wants Phase E mandatory, move it from optional to required in §16 and add entry gate that doesn't require telemetry
4. **Bandwidth baseline measurement procedure** (**D-62**) — the mechanics of measuring for 1 hour pre-deploy need a runbook entry
5. **Contract test runtime budget** (R2-03 §7.3 item 6: <50 ms per test, <5 s suite) — confirm CI infra supports this budget
6. **Verify the 6 pre-Phase-B grep probes** (NetworkVisualizer tech, SessionMiddleware, Dash version, Plotly version, run_coroutine_threadsafe, cascor handler command_id pass-through) at the first commit of each phase

### 19.7 Target length check

Target: 1700-2500 lines. Actual: approximately 1800-1900 lines including this self-audit. Within envelope. Dense-signal execution content, not narrative.

### 19.8 What this self-audit did NOT check

- Did not re-verify R2-04 recommended defaults against the original R1 sources (trusted R2-04 §3 text as authoritative)
- Did not run any greps against real code (those verifications are delegated to the Phase implementer first commits per §1.7)
- Did not reconcile R2-02 §18 disagreements with R2-03 §15 disagreements beyond the 10 items in §18
- Did not adjudicate between R3-01 (master integration) and R3-02 (this document) or R3-03 — those are Round 4 concerns
- Did not write new contract tests or runbook text — only referenced them by name

### 19.9 Final posture

R3-02 is the "no-alternatives execution blueprint" for the WebSocket migration. It takes R2-04's decision matrix as law and writes the execution plan that follows from those decisions. Every decision has an applied position with a D-NN citation. Every phase has a six-section contract with measurable gates. Every cross-cutting concern is woven into the phase where it lands. The risk register, kill-switch matrix, observability plan, merge sequence, and effort summary are each a single canonical table.

**R3-02's contribution**: commits the ecosystem to a settled decision set so Round 4 can focus on two-way reconciliation with R3-01 and R3-03 rather than re-opening decisions. The disagreement section (§18) is the only place where alternatives are discussed, and each disagreement cites a specific R2 position and a specific justification for the deviation.

---

**End of R3-02 decision-resolved blueprint.**
