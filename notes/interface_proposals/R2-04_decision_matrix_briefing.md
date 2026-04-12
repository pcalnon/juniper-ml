# Round 2 Proposal R2-04: Decision Matrix & Stakeholder Briefing

**Angle**: Decisions that must be made, when, by whom, with proposed defaults
**Author**: Round 2 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 2 consolidation — input to Round 3
**Inputs consolidated**: R1-01 (critical-path minimum-viable), R1-02 (risk-minimized safety-first), R1-03 (maximalist comprehensive), R1-04 (operational runbook), R1-05 (disagreement reconciliation)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 0. If you only read one section, read this

The WebSocket migration exists to kill a **~3 MB/s `/api/metrics/history` polling bomb** (GAP-WS-16, P0). Every R1 agrees this is the single load-bearing outcome. The work is technically well-scoped but has ~30 load-bearing decisions in flight — R1 agents already resolved many of them, but several remain open and a handful touch the critical path. Until those are decided, R3 will either burn cycles re-litigating or ship partial work.

The top three decisions you need to make this week are: **(D-02)** field name `command_id` vs `request_id` for the `set_params` correlation field (touches SDK, cascor, canopy, tests — pick now or R3 forks); **(D-11)** do we carve out a separate "Phase 0-cascor" for the cascor seq/replay work or keep it in Phase B (R1-05 says carve, R1-03 and R1-02 say carve, R1-01 silently keeps in Phase B; carving simplifies Phase B review dramatically); and **(D-17)** whether the browser-bridge Phase B ships behind a feature flag by default OFF (R1-02 insists yes, R1-01 implicitly no) — this governs whether the P0 win is one PR or four.

Total effort across all R1 proposals: **7 days** (R1-01 minimum-viable) to **17-18 days** (R1-02 safety-first), with the center of mass at **13.5 days / ~4.5 weeks calendar** (R1-03, R1-05). Recommended path: take R1-05's reconciled positions as the default decision set, flip Phase B to flagged-off per R1-02, and ship Phase 0-cascor + Phase B-pre-a + Phase B + Phase I on the critical path. Phase C/D/E/F/G/H can slip without delaying the P0 win, but Phase B-pre-b (Origin + CSRF) is a hard Phase D gate and should be landed in parallel with Phase B, not after.

---

## 1. Stakeholder briefing (one page)

### 1.1 What we're doing

Replacing ~3 MB/s per-dashboard REST polling of `/api/metrics/history` with an already-mostly-built WebSocket pipeline from cascor through canopy to the browser. The WebSocket surface exists today but is half-wired: the browser opens the socket, frames flow, nothing consumes them, polling continues. This migration finishes the wiring, adds the security guards the new browser-facing socket needs, adds the observability to prove the win, and adds fallbacks for when the socket is unhealthy.

The motivation is bandwidth (waste per dashboard, multiplied across users/tabs) but the rollout is also an opportunity to clean up several correctness bugs in the backend broadcaster (GAP-WS-21 state coalescer, GAP-WS-29 silent exception swallowing, GAP-WS-07 slow-client blocking) that are landed piggyback on the cascor-side work.

### 1.2 Why it matters

- **P0 cost saving** (~3 MB/s per dashboard is the only P0 item on the list). Every R1 cites this.
- **Correctness floor**: Phase 0-cascor / A-server fixes a silent-data-loss bug in the lifecycle state coalescer (GAP-WS-21). Without it, users see "running" while their training has actually finished.
- **Security posture**: the browser `/ws/training` socket is currently open with no Origin check. Any cross-origin page a user visits can tail training data. Phase B-pre-a closes this. Phase B-pre-b closes the CSWSH hole on `/ws/control` that is already present today (not worsened by the migration, but still unfixed).
- **Foundation**: Phases C/D build on B. The `set_params` WebSocket path is nice UX but not urgent (R0-04 re-classifies it from P1 to P2).

### 1.3 How long it takes

| Plan source | Total engineering days | Calendar | Scope |
|---|---|---|---|
| R1-01 (minimum-viable) | **7 days** | ~1.5 weeks | Phase 0-cascor + minimum B-pre + Phase B + Phase I only |
| R1-03 (maximalist) | **13.5-15 days** | ~5 weeks | All 10 phases |
| R1-04 (runbook) | **12 days** | ~5 weeks | Day-by-day runbook, all phases |
| R1-05 (reconciled) | **13.5 days** | ~4.5 weeks | Reconciled full scope, fewer redundancies |
| R1-02 (safety-first) | **17-18 days** | ~5-6 weeks | Full scope + doubled staging soaks, more kill switches, chaos tests |

Center of mass: **~13.5 days / 4.5 weeks** for the full migration. Critical-path subset for the P0 win alone: **~7 days**.

### 1.4 Key decisions you need to make

The five most load-bearing decisions (full list in §2, details in §3):

1. **D-02**: Correlation field name — `command_id` (3 sources agree, includes source doc) vs `request_id` (R0-04 only). Affects wire protocol. **Recommendation: `command_id`.** Decide before Phase A starts.
2. **D-11**: Phase 0-cascor carve-out — pull cascor seq/replay out of Phase B into its own ~2-day pre-phase so cascor main carries the new envelope field for ~1 week before canopy consumes it. **Recommendation: carve out.** Decide before Phase 0-cascor starts.
3. **D-17**: Phase B feature flag default — ship Phase B behind `enable_browser_ws_bridge=False` (R1-02 safety posture) or flip on at merge (R1-01 implicit). **Recommendation: ship flagged-off.** Decide before Phase B merges.
4. **D-19**: Phase E backpressure default — `block` (source doc, preserves existing behavior) or `drop_oldest_progress_only` (R1-02 + R1-05, fixes RISK-04). **Recommendation: `drop_oldest_progress_only`.** Decide before Phase E starts.
5. **D-23**: Phase B-pre split — single bundle (R0-02) or split into B-pre-a (size/IP caps, gates Phase B) and B-pre-b (Origin/CSRF/audit, gates Phase D). **Recommendation: split.** Decide before Phase B-pre-a starts.

### 1.5 Risks if we don't decide

- **D-02 not decided**: SDK lands with `request_id`, cascor lands with `command_id`, the wire mismatch surfaces in Phase G integration test 2-3 weeks later. 1-2 day rework.
- **D-11 not decided**: Phase B PR is ~4 days of commits across cascor + canopy; review fatigue high; one bug in the cascor-side commits blocks the canopy-side commits for the whole review cycle.
- **D-17 not decided**: if Phase B ships flag-on and has the RISK-02 clientside-callback debuggability bug, rolling back is a code revert (~30 min MTTR) instead of a config flip (~5 min MTTR).
- **D-19 not decided**: first production incident after Phase E is a slow-client blocking event (RISK-04), and the fix requires a second deploy.
- **D-23 not decided**: Phase B is blocked on a 2-day CSRF plumbing exercise that isn't required until Phase D.

### 1.6 Recommended path

Take R1-05's reconciled positions as the **default decision set**. Override in two places: (a) adopt R1-02's flagged-off Phase B default (D-17 above), and (b) scope the first critical-path wave to R1-01's minimum-viable set (Phase 0-cascor + minimum B-pre-a + Phase B + Phase I) so the P0 win lands in ~7 days. The remaining phases (B-pre-b, C, D, E, F, G, H) slot into a v1.1 follow-up bundle.

---

## 2. Decision inventory

A tabular summary of every decision that must be made. Full details in §3. Each decision has an ID `D-NN`, a summary, the options considered, the recommended default, who decides, the deadline relative to phase ordering, and the cost of deferring.

Legend for "Who decides":
- **TL** = Tech lead / project lead (Paul Calnon)
- **Sec** = Security reviewer or project lead acting in that role
- **Ops** = Operations / deployment owner
- **R3** = Round 3 consolidation agents (default if nobody takes it)
- **R5** = Round 5 final canonical plan (last-resort fallback)

Legend for "Deadline":
- **Pre-P0** = before Phase 0-cascor starts
- **Pre-A** = before Phase A (SDK) starts
- **Pre-B-pre-a** = before Phase B-pre-a starts
- **Pre-B** = before Phase B starts
- **Pre-D** = before Phase D starts
- **Pre-E** = before Phase E starts
- **In-flight** = can be decided during the relevant phase; not blocking

| ID | Decision summary | Options | Recommended | Who | Deadline | Cost of deferral |
|---|---|---|---|---|---|---|
| D-01 | `set_params` default timeout | 1.0 s / 5.0 s | **1.0 s** (R0-04, R1-03, R1-05) | TL | Pre-A | Low — SDK ships with wrong default, 1-line PR to fix |
| D-02 | Correlation field name | `command_id` / `request_id` | **`command_id`** (R1-05 §4.2) | TL | Pre-A | **High** — wire mismatch between SDK and cascor surfaces in Phase G |
| D-03 | `command_response` carries `seq` | yes / no | **no** (R1-05 §4.17, R0-03) | TL | Pre-P0 | Medium — separate seq namespace; replay semantics confusion if wrong |
| D-04 | rAF coalescer ship state | enabled / scaffold-disabled | **scaffold-disabled** (R1-01, R1-02, R1-03, R1-04, R1-05) | TL | Pre-B | Low — 1-line flip later if §5.6 data demands |
| D-05 | REST polling fallback cadence during disconnect | 100 ms / 1 Hz | **1 Hz** (R1-01, R1-03, R1-04, R1-05) | TL | Pre-B | Low — 3-line JS change, not user-visible |
| D-06 | NetworkVisualizer in Phase B scope | full cytoscape migration / minimum WS wiring / defer entirely | **minimum WS wiring in B, deep migration deferred if cytoscape** (R1-05) | TL | Pre-B | Low — first commit of Phase B can verify render tech |
| D-07 | `ws-metrics-buffer` store shape | bare array / `{events, gen, last_drain_ms}` object | **structured object** (R1-05 §4.7) | TL | Pre-B | Low — Dash callback false-negative risk |
| D-08 | GAP-WS-24 ownership split | bundled / split into 24a (browser) + 24b (canopy backend) | **split** (R1-05 §4.8) | TL | Pre-B | None — ownership clarification |
| D-09 | Phase B-pre effort estimate | 1 day (source doc) / 2 days (R0-02) / 2.5 days (R0-06) | **2 days B-pre-b + 0.5 day B-pre-a** (R1-05 §4.9) | TL | Pre-B-pre-a | Low — schedule slippage only |
| D-10 | `disable_ws_auth` naming | negative-sense (source doc) / `ws_security_enabled` positive (R0-02) | **keep negative for v1** (R1-05 §4.10) OR **positive-sense** (R1-02, R1-03 take opposite) | TL | Pre-B-pre-b | Low — rename is a trivial follow-up |
| D-11 | Phase 0-cascor carve-out from Phase B | carve out 2-day cascor-only phase / keep in Phase B | **carve out** (R1-03, R1-04, R1-05; R1-01 silently adopts; R1-02 silently adopts) | TL | Pre-P0 | **High** — Phase B PR size and review burden |
| D-12 | M-SEC-10/11/12 new identifiers | adopt all three / fold M-SEC-12 into M-SEC-07 / reject | **adopt 10/11, fold 12 into 07** (R1-05 §4.15) | Sec | Pre-B-pre-a | Low — ID numbering |
| D-13 | GAP-WS-19 (`close_all` lock) | include in Phase B-pre / mark RESOLVED | **mark RESOLVED** (R1-05 §4.16, R0-03 verified on main) | TL | Pre-B-pre-a | Low — avoids duplicate work |
| D-14 | Two-phase registration mechanism | `_pending_connections` set / per-conn `seq_cursor` | **`_pending_connections`** (R1-03, R1-04, R1-05) | TL | Pre-P0 | Low — either works |
| D-15 | `server_start_time` vs `server_instance_id` | standardize on one / use both | **`server_instance_id` programmatic, `server_start_time` advisory** (R1-05 §4.20) | TL | Pre-P0 | Low — clock-skew bug if comparing start_time |
| D-16 | `replay_buffer_capacity` in `connection_established` | add / omit | **add** (R1-03, R1-04, R1-05) | TL | Pre-P0 | None — additive field |
| D-17 | Phase B feature flag default | flag-off (R1-02) / no flag (R1-01 implicit) / flag-on (source doc implicit) | **flag-off `enable_browser_ws_bridge=False`** (R1-02, R1-05 §4.45) | TL | Pre-B | **High** — rollback MTTR differs 5min vs 30min |
| D-18 | Permanent kill switch `disable_ws_bridge` | add / skip | **add** (R1-02, R1-03, R1-05 §4.45) | Ops | Pre-B | Medium — kill-switch is operational safety |
| D-19 | Phase E backpressure default | `block` / `drop_oldest_progress_only` / `close_slow` | **`drop_oldest_progress_only`** (R1-02, R1-03, R1-05) | TL | Pre-E | **High** — RISK-04 in first prod incident if left as `block` |
| D-20 | SDK retries on `set_params` timeout | SDK retries / caller decides | **caller decides** (R0-04, R1-05 §4.22) | TL | Pre-A | Low — stale-value ordering risk if SDK queues |
| D-21 | Keep REST `update_params` / `/api/metrics/history` forever | delete later / permanent fallback | **permanent** (all R1s agree, R1-05 §4.23) | TL | Pre-B | None — already the default reading |
| D-22 | Debounce layer (UI or SDK) | SDK / Dash clientside callback | **Dash clientside** (R1-05 §4.24) | TL | Pre-C | Low — architectural placement |
| D-23 | Phase B-pre split | single bundle / split a+b | **split a+b** (R1-03, R1-04, R1-05) | TL | Pre-B-pre-a | **High** — phase ordering, Phase B blocking scope |
| D-24 | Q6 per-IP cap default | TBD / 5 per IP / other | **5 per IP** (R1-02, R1-03, R1-05) | Sec | Pre-B-pre-a | Low — tunable post-deploy |
| D-25 | Q1 deployment topology | single-tenant v1 / multi-tenant v1 | **single-tenant v1** (R1-02, R1-05, R1-03) | TL | Pre-P0 | Low — scopes out replay isolation work |
| D-26 | Shadow traffic strategy | ship / skip | **skip** (R1-02, R1-03, R1-05, R0-06) | TL | Pre-B | None — already rejected |
| D-27 | CODEOWNERS rule for `_normalize_metric` | enforce / recommend / skip | **enforce** (R1-02, R1-03, R1-05) | TL | Pre-H | Low — RISK-01 mitigation |
| D-28 | Audit logger scope | dedicated logger (R0-02) / shared app logger (R0-06) | **dedicated logger, Prom counters in Phase B** (R1-05 §4.14) | Sec | Pre-B-pre-a | Low — audit separability |
| D-29 | Adapter synthetic auth | `X-Juniper-Role: adapter` header / HMAC CSRF token | **HMAC CSRF token** (R1-02, R1-03, R1-05 §4.43) | Sec | Pre-B-pre-b | Medium — auth branch in hot path |
| D-30 | "One resume per connection" rule | add / skip | **add** (R1-05 §4.12, R0-02) | Sec | Pre-P0 | Low — DoS amplification mitigation |
| D-31 | Per-command HMAC (M-SEC-02 pt 3) | defer / include | **defer indefinitely** (R1-05 §4.11) | Sec | Pre-B-pre-b | None — speculative threat |
| D-32 | Multi-tenant replay isolation | defer / include in v1 | **defer** (R1-05 §4.13) | TL | Pre-B-pre-a | None — YAGNI for v1 |
| D-33 | Rate limit buckets | single 10/s / two (20/s set_params + 10/s destructive) | **single 10/s** (R1-05 §4.46) | Sec | Pre-B-pre-b | Low — split later if starvation observed |
| D-34 | Unclassified-key routing | `extra="forbid"` (R0-02) / REST fallback with warn (R0-04) | **both at different layers** (R1-05 §4.44) | TL | Pre-C | Low — orthogonal |
| D-35 | Replay buffer default size | 256 (R1-02) / 1024 (R0-03, R1-03, R1-05) | **1024, operator-tunable** (R1-05 default; R1-02 argues 256 to exercise fallback) | Ops | Pre-P0 | Low — one env var |
| D-36 | Cascor replay-buffer-size kill switch | add `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` / skip | **add** (R1-02) | Ops | Pre-P0 | Low — emergency lever |
| D-37 | Metrics-presence CI test | enforce as blocker / optional | **enforce** (R1-02 §10.6) | TL | Pre-B | Low — cheap guard |
| D-38 | Staging soak duration Phase 0-cascor | 24 h / 72 h (R1-02) | **72 h** (R1-02 §3.4) | Ops | Pre-B | Medium — seq monotonicity bugs are latent |
| D-39 | Staging soak duration Phase B | 48 h (R0-06) / 72 h (R1-02 §5.7) | **72 h** (RISK-10 memory leak) | Ops | Pre-production | Medium — browser leak surfaces overnight |
| D-40 | Chaos tests category | skip / nightly-only / blocking | **nightly-only** (R1-02 §10.1) | TL | Pre-B | Low — flakiness risk |
| D-41 | Load tests as gate | optional (R0-05) / blocking for Phase 0-cascor (R1-02) | **blocking for Phase 0-cascor** (R1-02 §10.3) | TL | Pre-P0 | Low — CI runtime increase |
| D-42 | Frame budget test as gate | blocking / recording-only | **recording-only** (R1-03, R1-05, R1-02, R0-05 §6.3) | TL | Pre-B | Low — flaky CI |
| D-43 | Test marker `contract` lane | add / skip | **add** (R1-02, R1-03, R1-05 §4.34) | TL | Pre-B | None — drift mitigation |
| D-44 | Multi-browser matrix | Chromium-only / Chromium + Firefox + WebKit | **Chromium-only for v1** (R0-05, R1-02, R1-03, R1-04, R1-05) | TL | Pre-B | None — deferred |
| D-45 | User research study | run / skip | **skip for v1** (R0-06, R1-02, R1-03, R1-05) | TL | Pre-C | None — optional |
| D-46 | `ws_replay_buffer_size=0` as kill switch | add / omit | **add** (R1-02 §3.3) | Ops | Pre-P0 | Low — emergency lever |
| D-47 | Phase C feature flag default | False (R0-04, R1-02, R1-03, R1-04) / True | **False** (unanimous) | TL | Pre-C | None — unanimous |
| D-48 | Phase C flag-flip criteria | 1-week prod data / 1-week canary + p99 delta ≥50 ms (R1-02) / vague guidance (R0-06) | **enumerated hard gates** (R1-02 §6.1) | TL | Pre-C | Medium — prevents premature flip |
| D-49 | Phase D feature flag | add / skip | **add `enable_ws_control_buttons=False`** (R1-02) | TL | Pre-D | Medium — rollback granularity |
| D-50 | Error-budget-burn freeze rule | enforce / advisory | **enforce** (R1-02 §2.4) | TL | Pre-B | Low — operational discipline |
| D-51 | `WSOriginRejection` alert severity | page / ticket | **page** (R1-02, R1-03 §16.3) | TL | Pre-B-pre-a | Low — CSWSH early warning |
| D-52 | `WSSeqCurrentStalled` alert | add / skip | **add as page severity** (R1-02 §2.4) | TL | Pre-P0 | Low — event-loop hang detection |
| D-53 | Abandon triggers tested | test the kill-switch MTTR in staging / trust it | **test** (R1-02 §13.7) | Ops | Pre-B | Medium — untested kill switches are not kill switches |
| D-54 | REST `/api/metrics/history` polling handler retention | delete later / preserve forever | **preserve forever** (R1-02 principle 7, R1-05 §4.23) | TL | Pre-B | None — already the default |
| D-55 | Source-doc patches deferred to Round 5 | batch now / per-phase | **batch in Round 5** (R1-05 §8.6) | R5 | Pre-canonical | None — documentation hygiene |

Total: **55 decisions**. Of these:
- **5 are "High" cost of deferral** (D-02, D-11, D-17, D-19, D-23): must be decided before the relevant phase starts or R3 forks.
- **8 are "Medium"** (D-03, D-18, D-29, D-38, D-39, D-48, D-49, D-53): should be decided before the phase but late-decide is survivable.
- The rest are "Low" or "None": sensible defaults exist, decide in-flight or on a trailing PR.

---

## 3. Detailed decisions

This section details every decision in §2. Each has: Question, Why it matters, Options, Trade-offs, Recommended default, Who decides, Deadline, Cost of deferring, Source.

### 3.1 D-01: `set_params` default timeout

- **Question**: What is the default `timeout` kwarg on `CascorControlStream.set_params()`?
- **Why it matters**: Hot-path slider UX. A 5 s stuck-server hang is visibly bad; a 1 s fallback to REST is nearly invisible.
- **Options**:
  - A: 1.0 s (R0-04, R1-03, R1-04, R1-05 reconciled)
  - B: 5.0 s (source doc §7.1 hook text)
- **Trade-offs**: 1.0 matches GAP-WS-32 specific per-command budget (§7.32); 5.0 is inherited from generic `DEFAULT_CONTROL_STREAM_TIMEOUT` but inconsistent with §7.32.
- **Recommended default**: **1.0 s**
- **Who decides**: TL
- **Decision deadline**: Pre-A
- **Cost of deferring**: Low — SDK ships with wrong default, 1-line fix later.
- **Source**: R1-03 §18.4, R1-05 §4.1, R1-04 §14 D2

### 3.2 D-02: Correlation field name (`command_id` vs `request_id`)

- **Question**: What is the name of the correlation ID field on the `set_params` wire envelope and matching SDK kwarg?
- **Why it matters**: **Cross-repo wire contract**. SDK, cascor, canopy, and tests all reference this field. Mismatch surfaces in Phase G integration tests weeks after the individual PRs merge.
- **Options**:
  - A: `command_id` (source doc §7.32 line 1403, R0-02, R0-03, R1-05 reconciled)
  - B: `request_id` (R0-04 original, picked up by R1-03)
- **Trade-offs**: `command_id` matches source doc and 3 of 4 R0s that care; `request_id` is R0-04's one-off naming choice. Semantics identical. Only the string differs.
- **Recommended default**: **`command_id`**
- **Who decides**: TL
- **Decision deadline**: Pre-A (SDK work starts here)
- **Cost of deferring**: **High** — if not decided, SDK lands with `request_id` and cascor lands with `command_id`. Phase G fails. 1-2 day rework.
- **Source**: R1-05 §4.2, §7.1, §8.2 item 1

### 3.3 D-03: `command_response` carries `seq`

- **Question**: Does `command_response` on `/ws/control` carry a `seq` field and enter the replay buffer?
- **Why it matters**: Determines whether `/ws/training` and `/ws/control` share a seq namespace, whether `/ws/control` needs its own replay buffer, and whether replayed command responses can reach a browser tab that didn't issue the original command.
- **Options**:
  - A: No seq on `command_response`; separate seq namespaces per endpoint (R0-03, R1-05 reconciled, R1-03 §18.3)
  - B: Seq on every outbound envelope including `command_response` (R0-02 Pydantic models imply, R0-05 test names imply)
- **Trade-offs**: No-seq is semantically cleaner (replaying a command_response to a different tab is confusing); yes-seq is a unified mental model but creates cross-namespace sequencing.
- **Recommended default**: **No seq on `command_response`**. `/ws/control` has no replay buffer; `/ws/training` does. Correlation via `command_id` not seq.
- **Who decides**: TL
- **Decision deadline**: Pre-P0 (Phase 0-cascor starts here)
- **Cost of deferring**: Medium — affects cascor broadcaster, SDK correlation, canopy drain callback, and R0-05 test assertions.
- **Source**: R1-05 §4.17, R1-03 §18.3, R0-03 §6.3/§11.3

### 3.4 D-04: rAF coalescer ship state

- **Question**: In Phase B, does `ws_dash_bridge.js` ship with `requestAnimationFrame` coalescing enabled or as a no-op scaffold gated behind a flag?
- **Why it matters**: rAF coalescing (GAP-WS-15) is a P1 item in the source doc. R0-01 argues it's unnecessary at the 100 ms drain interval (~10 Hz render rate already under 60 fps). Enabling it adds complexity and a small double-render risk during drain ticks.
- **Options**:
  - A: Scaffold-disabled via `Settings.enable_raf_coalescer=False` (R0-01, R1-01, R1-02, R1-03, R1-04, R1-05 — unanimous among R1s)
  - B: Ship enabled (source doc implicit)
- **Trade-offs**: Disabled is strictly safer at Phase B merge time; re-enable is a 1-line flip if §5.6 instrumentation shows frame-budget pressure. Enabled matches source doc literal reading but adds a second render path during Phase B's already-large scope.
- **Recommended default**: **Scaffold-disabled**
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low — flag flip later.
- **Source**: R1-05 §4.3, R1-01 §4.3, R1-02 §5.5, R1-03 §18.7, R1-04 D1

### 3.5 D-05: REST polling fallback cadence during disconnect

- **Question**: When the WebSocket is disconnected and the dashboard falls back to REST polling, at what rate does it poll?
- **Why it matters**: During reconnect attempts (5-30 s window), the dashboard should not re-introduce the 100 ms polling bomb that motivated the migration.
- **Options**:
  - A: 1 Hz fallback (`n % 10 != 0` check against 100 ms fast-update-interval)
  - B: 100 ms fallback (current behavior)
- **Trade-offs**: 1 Hz reduces reconnect-window bandwidth 10×; minor correctness cost (up to 1 s lag on chart during fallback); matches the §6.4 disconnection taxonomy cadence. 100 Hz fallback is pathological — reintroduces the very bug we're fixing.
- **Recommended default**: **1 Hz**
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low — 3-line JS change, non-user-visible.
- **Source**: R1-05 §4.4, R1-04 D8, R1-01 §2.3, R0-01 §3.4.2

### 3.6 D-06: NetworkVisualizer in Phase B scope

- **Question**: How much of `NetworkVisualizer` is migrated in Phase B?
- **Why it matters**: If NetworkVisualizer uses cytoscape (not Plotly), the `extendTraces` migration does not apply and a full re-implementation is ~1-2 days of additional Phase B scope. R0-01 hypothesizes cytoscape but does not verify.
- **Options**:
  - A: Full cytoscape migration in Phase B (source doc implicit)
  - B: Minimum WS wiring only (topology updates over WS), deep render migration deferred to Phase B+1 if cytoscape (R0-01 disagreement #3, R1-01, R1-03, R1-05)
  - C: Defer NetworkVisualizer entirely to B+1
- **Trade-offs**: Minimum wiring is cheap (~0.5 day) and safe regardless of render tech. Full migration blocks Phase B on render-tech verification.
- **Recommended default**: **Minimum WS wiring in B; deep render migration deferred contingent on render tech (verify in first commit)**
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low — first commit of Phase B verifies.
- **Source**: R1-05 §4.5, R1-01 §2.3 MVS-FE-11, R1-03 §19.5, R1-04 D7

### 3.7 D-07: `ws-metrics-buffer` store shape

- **Question**: Is the `ws-metrics-buffer` dcc.Store a bare array or a structured `{events, gen, last_drain_ms}` object?
- **Why it matters**: Dash callback change detection uses JSON-serialized equality. A `gen` counter makes change detection deterministic even when the underlying `events` array is mutated in place.
- **Options**:
  - A: Bare array
  - B: `{events: [...], gen: int, last_drain_ms: float}` (R0-01 §7 disagreement #5, R1-05 reconciled)
- **Recommended default**: **Structured object**
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low — Dash false-negative risk.
- **Source**: R1-05 §4.7, R0-01 §7

### 3.8 D-08: GAP-WS-24 browser-vs-server ownership split

- **Question**: Is GAP-WS-24 (browser latency instrumentation) one item or split into 24a (browser emitter) + 24b (canopy backend `/api/ws_latency` endpoint)?
- **Why it matters**: Clean ownership for the Phase B PR.
- **Recommended default**: **Split** (24a frontend, 24b canopy backend; both ship in Phase B)
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None — ownership clarification.
- **Source**: R1-05 §4.8

### 3.9 D-09: Phase B-pre effort estimate

- **Question**: How many engineering days is Phase B-pre?
- **Why it matters**: Calendar planning, staffing. Source doc says 1 day; R0-02 says 1.5-2; R0-06 implies 2.5 with observability folded in.
- **Options**:
  - A: 1 day (source doc §9.2)
  - B: 2 days B-pre-b (R1-03 §19.4, R1-05 §4.9)
  - C: 2-2.5 days bundled (R0-02)
- **Recommended default**: **0.5 day B-pre-a + 1.5-2 days B-pre-b = 2-2.5 days total** (split per D-23)
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low — schedule slippage only.
- **Source**: R1-05 §4.9, R1-03 §19.4, R1-04 D3

### 3.10 D-10: Security flag naming

- **Question**: Is the security master-flag `disable_ws_auth` (negative-sense) or `ws_security_enabled` (positive-sense)?
- **Why it matters**: Footgun concern — a production config accidentally containing `disable_ws_auth=true` is one typo from disaster.
- **Options**:
  - A: Negative-sense (source doc, R1-05 keep-as-is)
  - B: Positive-sense `ws_security_enabled=True` (R0-02 §9.4, R1-02, R1-03)
- **Trade-offs**: Positive-sense fails safe on typo. Negative-sense is what the source doc uses and matches existing Juniper conventions. R1-05 explicitly defers to source doc; R1-02 argues for change with CI guardrail as mitigation.
- **Recommended default**: **Positive-sense `ws_security_enabled`** with CI guardrail in `juniper-deploy` that refuses negative-sense values in production compose files. This aligns with R1-02/R1-03 safety posture and is cheap.
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-b
- **Cost of deferring**: Low — rename is a trivial follow-up.
- **Source**: R1-02 §12.5, R1-03 §18.6, R1-05 §4.10 (keep-as-is), R1-04 D5 (explicit defer)

### 3.11 D-11: Phase 0-cascor carve-out from Phase B

- **Question**: Does cascor's seq/replay/server_instance_id work ship as a separate ~2-day Phase 0-cascor (or "Phase A-server") before canopy Phase B begins, or stay in Phase B?
- **Why it matters**: Phase B PR size and review burden. If Phase 0-cascor is a separate PR, cascor main carries the new envelope field for ~1 week before canopy consumes it (a real production soak window for additive changes). If bundled, Phase B is a ~4-day PR across cascor + canopy that is hard to review.
- **Options**:
  - A: Carve out (R0-03, R1-03, R1-04, R1-05, implicitly adopted by R1-01 and R1-02)
  - B: Single Phase B (source doc §9.3)
- **Trade-offs**: Carve-out = smaller PRs, production soak window, clearer release coordination, +1 PR overhead. Bundled = one train but review fatigue and more conflict surface.
- **Recommended default**: **Carve out**
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: **High** — affects the rest of the plan.
- **Source**: R1-05 §4.19, R1-03 §19.1, R1-04 D13, R0-03 §11.5

### 3.12 D-12: M-SEC-10/11/12 new identifiers

- **Question**: Adopt M-SEC-10 (idle timeout), M-SEC-11 (adapter inbound validation), M-SEC-12 (log injection escaping) as new canonical IDs, or fold some into existing M-SEC-07?
- **Why it matters**: ID discipline in the canonical plan. R0-02 proposes all three new; R1-05 folds M-SEC-12 into M-SEC-07.
- **Options**:
  - A: All three new
  - B: Adopt 10 and 11, fold 12 into M-SEC-07 (R1-05 §4.15)
  - C: Reject all three
- **Recommended default**: **Adopt M-SEC-10 and M-SEC-11; fold M-SEC-12 into M-SEC-07**
- **Who decides**: Sec
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low — ID numbering.
- **Source**: R1-05 §4.15, R1-03 §18.13

### 3.13 D-13: GAP-WS-19 (`close_all` lock) resolution status

- **Question**: Is GAP-WS-19 already RESOLVED on main, or does it need to be fixed in Phase B-pre?
- **Why it matters**: Phase B-pre scope. R0-02 proposes re-fixing; R0-03 claims already resolved; R1-05 verified against `manager.py:138-156`.
- **Recommended default**: **Mark RESOLVED** (verified by R1-05 direct file inspection)
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low — avoids duplicate work.
- **Source**: R1-05 §4.16, R0-03 §11.1

### 3.14 D-14: Two-phase registration mechanism

- **Question**: How does cascor atomically hand off a reconnecting client from replay to live broadcast?
- **Why it matters**: Prevents a race where the client misses events that arrive between replay end and live start.
- **Options**:
  - A: `_pending_connections` set + `promote_to_active()` helper (R0-03, R1-03, R1-04, R1-05)
  - B: Per-connection `seq_cursor` gate on every broadcast
- **Recommended default**: **`_pending_connections`** (R0-03 thought through both, simpler fan-out)
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — either works.
- **Source**: R1-05 §4.18, R0-03 §5.1/§11.4

### 3.15 D-15: `server_start_time` vs `server_instance_id`

- **Question**: Which field does the client use to detect a cascor restart?
- **Why it matters**: Clock-skew immunity. Comparing `server_start_time` is a latent bug when client and server clocks disagree.
- **Options**:
  - A: `server_instance_id` programmatic, `server_start_time` advisory only (R0-03, R1-05)
  - B: Both programmatic
- **Recommended default**: **`server_instance_id` for programmatic comparison; `server_start_time` for human log correlation only**
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — latent bug if wrong, but caught in test.
- **Source**: R1-05 §4.20

### 3.16 D-16: `replay_buffer_capacity` additive field

- **Question**: Does `connection_established` advertise the replay buffer capacity?
- **Why it matters**: Clients can decide resume-vs-snapshot based on how much history is available.
- **Recommended default**: **Add**
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: None — additive field.
- **Source**: R1-05 §4.21, R0-03 §4.1

### 3.17 D-17: Phase B feature flag default

- **Question**: Does Phase B (browser bridge) ship with a feature flag defaulting OFF, or flip on at merge?
- **Why it matters**: **Rollback MTTR**. RISK-02 (clientside_callback hard to debug) is Medium/High. With a flag, rollback is a config flip (~5 min MTTR). Without, rollback is a code revert or cherry-pick (~30 min MTTR or more).
- **Options**:
  - A: Ship behind `Settings.enable_browser_ws_bridge=False` (R1-02, R1-05 combined with ops kill switch)
  - B: No flag; merge-to-enable (R1-01 implicit, source doc implicit)
- **Trade-offs**: Flag adds a single env var and a staged canary; buys a ~5 min MTTR vs ~30 min. R1-01 argues the flag isn't needed for a "safe" read-side migration; R1-02 argues Phase B is the highest-risk phase and needs a flag.
- **Recommended default**: **Flag-off**. Staging flips to ON; canary runs with ON; production flag-flip is a separate 1-line PR after soak.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: **High** — rollback path depends on this.
- **Source**: R1-02 §5.2/§12.6, R1-05 §4.45

### 3.18 D-18: Permanent kill switch `disable_ws_bridge`

- **Question**: Is there a permanent `Settings.disable_ws_bridge` kill switch independent of the Phase B feature flag?
- **Why it matters**: Post-rollout operational lever. Even after `enable_browser_ws_bridge` is flipped permanently True, operators need a way to fall back to REST polling in an incident.
- **Options**:
  - A: Add permanent kill switch (R1-02, R1-05)
  - B: Re-use the Phase B flag
- **Recommended default**: **Add permanent kill switch**. Runtime check: `enabled = enable_browser_ws_bridge and not disable_ws_bridge`.
- **Who decides**: Ops
- **Decision deadline**: Pre-B
- **Cost of deferring**: Medium — operational safety.
- **Source**: R1-02 §8, R1-05 §4.45

### 3.19 D-19: Phase E backpressure default policy

- **Question**: What is the default `ws_backpressure_policy`?
- **Why it matters**: RISK-04 (slow-client blocking) is Medium/Medium. `block` preserves existing behavior but leaves the risk live. `drop_oldest_progress_only` fixes the risk but changes semantics for production workloads.
- **Options**:
  - A: `block` (source doc §9.6, preserves existing behavior)
  - B: `drop_oldest_progress_only` (R0-06, R1-02, R1-03, R1-05)
  - C: `close_slow` (R0-03 aggressive)
- **Trade-offs**: `block` means first prod incident after Phase E is exactly this failure mode. `drop_oldest_progress_only` is safer by default with state-bearing events still closing slow clients. `close_slow` disconnects transiently-slow but otherwise-fine clients.
- **Recommended default**: **`drop_oldest_progress_only`** with `block` and `close_slow` remaining as opt-in alternatives.
- **Who decides**: TL
- **Decision deadline**: Pre-E
- **Cost of deferring**: **High** — first prod incident. This is the one place R1-05 explicitly overrides the source doc.
- **Source**: R1-05 §4.36, R1-03 §18.2, R1-02 §7.2

### 3.20 D-20: SDK retries on `set_params` timeout

- **Question**: Does the SDK retry `set_params` on timeout, or fail-fast and let the caller decide?
- **Why it matters**: Stale-value ordering. A queued retry can apply an outdated slider position if the client has moved on.
- **Options**:
  - A: Fail-fast; caller decides (R0-04, R1-05)
  - B: SDK retries
- **Recommended default**: **Fail-fast**. Test name `test_set_params_fails_fast_on_disconnect`, not `test_set_params_reconnection_queue`.
- **Who decides**: TL
- **Decision deadline**: Pre-A
- **Cost of deferring**: Low — stale-value risk if wrong.
- **Source**: R1-05 §4.22, R1-05 §4.42, R0-04 §12.3

### 3.21 D-21: REST `update_params` / polling paths preserved forever

- **Question**: Is there a planned deprecation/removal of REST `update_params` or `/api/metrics/history`?
- **Why it matters**: Fallback lever. Deleting REST paths removes the primary kill switch.
- **Options**:
  - A: Preserve forever (all R1s agree)
  - B: Deprecate in a future release
- **Recommended default**: **Preserve forever**. Future deletion requires a separate migration plan.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None — already the default reading.
- **Source**: R1-02 principle 7, R1-05 §4.23, R0-04 §12.4

### 3.22 D-22: Debounce layer (UI or SDK)

- **Question**: Does slider-event debouncing live in the Dash clientside callback or the SDK?
- **Why it matters**: Layering discipline. Non-canopy SDK consumers want immediate dispatch; UI concerns belong in the UI.
- **Recommended default**: **Dash clientside callback**
- **Who decides**: TL
- **Decision deadline**: Pre-C
- **Cost of deferring**: Low — architectural placement.
- **Source**: R1-05 §4.24, R0-04 §8

### 3.23 D-23: Phase B-pre split

- **Question**: Is Phase B-pre a single bundle or split into B-pre-a (frame-size + per-IP caps + audit logger skeleton) and B-pre-b (Origin + CSRF + rate limit + audit logger Prometheus counters)?
- **Why it matters**: Phase B blocking scope. If bundled, Phase B waits on the full CSRF plumbing (~2 days) which is only needed for Phase D. If split, Phase B-pre-a (~0.5 day) unblocks Phase B while Phase B-pre-b lands in parallel and gates Phase D.
- **Options**:
  - A: Split a+b (R0-06, R1-03, R1-04, R1-05, R1-02)
  - B: Single bundle (R0-02, source doc)
- **Recommended default**: **Split**
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: **High** — ordering decision.
- **Source**: R1-05 §4.35, R1-03 §18.1, R1-04 D3, R1-02 §4.1/§4.2

### 3.24 D-24: Per-IP cap default

- **Question**: What is the default `ws_max_connections_per_ip`?
- **Why it matters**: Dos mitigation vs legitimate-user lockout (shared NAT).
- **Options**:
  - A: 5 per IP (R0-02, R0-06, R1-02, R1-03, R1-05)
  - B: Higher default
- **Recommended default**: **5 per IP**, tunable via `Settings.ws_max_connections_per_ip`
- **Who decides**: Sec
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low — tunable post-deploy.
- **Source**: R1-05 §4.37, R1-03 §18.14

### 3.25 D-25: Deployment topology (Q1 from source doc)

- **Question**: Is v1 single-tenant or multi-tenant?
- **Why it matters**: Replay buffer isolation, session cookies, CSRF token scope.
- **Recommended default**: **Single-tenant v1**. Multi-tenant is future work.
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — scopes out replay isolation and per-session concerns.
- **Source**: R1-05 §4.38, R1-02 §11 RISK-07, R1-03 §3.3

### 3.26 D-26: Shadow traffic strategy

- **Question**: Should Phase B run in "shadow" mode (both REST and WS paths active, WS path non-rendering) for a period before flipping?
- **Why it matters**: State duplication in a stateful protocol is a real trap. R0-06 §7.3 explicitly rejects.
- **Recommended default**: **Skip**. The polling-toggle pattern (GAP-WS-25) achieves most of the shadow benefit.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None — already rejected.
- **Source**: R1-05 §4.39, R1-02, R0-06 §7.3

### 3.27 D-27: CODEOWNERS rule for `_normalize_metric`

- **Question**: Is the RISK-01 (dual metric format regression) mitigation a CODEOWNERS rule, a pre-commit hook, a regression test, or all three?
- **Why it matters**: RISK-01 is a silent regression class — a well-intentioned cleanup PR can remove a consumer path.
- **Options**:
  - A: All three (R1-02 §7.5 hardened)
  - B: Regression test only (R0-06 weak form)
  - C: Recommend not require (source doc)
- **Recommended default**: **All three**: CODEOWNERS rule requires project-lead review; pre-commit hook blocks diffs removing nested format keys; regression test catches actual behavior change.
- **Who decides**: TL
- **Decision deadline**: Pre-H
- **Cost of deferring**: Low — Phase H is late in the migration.
- **Source**: R1-05 §4.41, R1-02 §7.5, R1-03 §19

### 3.28 D-28: Audit logger scope

- **Question**: Dedicated `canopy.audit` logger module or shared application logger?
- **Why it matters**: Audit separability for security review. Dedicated is ~200 LOC; shared is ~0 but loses the audit property.
- **Options**:
  - A: Dedicated logger + rotation, scrub allowlist, Prometheus counters (R0-02, R1-02, R1-03, R1-05)
  - B: Shared application logger (R0-06 implicit)
- **Recommended default**: **Dedicated logger**. Skeleton (JSON formatter, scrub allowlist, `TimedRotatingFileHandler`) in Phase B-pre-a; Prometheus counters in Phase B alongside other observability.
- **Who decides**: Sec
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low — audit separability.
- **Source**: R1-05 §4.14, R1-03 §18.15, R0-02 §4.6

### 3.29 D-29: Adapter synthetic auth

- **Question**: How does the canopy adapter authenticate to cascor over `/ws/control`?
- **Why it matters**: Cross-process auth. The adapter is already authenticated via `X-API-Key`, but Phase B-pre-b's CSRF first-frame enforcement applies to every `/ws/control` upgrade.
- **Options**:
  - A: `X-Juniper-Role: adapter` header skips CSRF enforcement (R0-02 §11 Q2-sec option A)
  - B: HMAC-derived CSRF token `hmac(api_key, "adapter-ws")` (R0-02 option B, R1-02, R1-03 §18.12, R1-05 §4.43)
- **Trade-offs**: Header-based skip is simpler but relies on the brittle invariant "browsers cannot set custom headers." HMAC is uniform handler logic with no branch and is ~10 lines stdlib-only.
- **Recommended default**: **HMAC CSRF token** (R1-02, R1-05). But R1-03 §18.12 picks **header-based skip** — this is an open disagreement.
- **Who decides**: Sec (cross-repo security decision)
- **Decision deadline**: Pre-B-pre-b
- **Cost of deferring**: Medium — auth branch in hot path.
- **Source**: R1-05 §4.43, R1-02 §4.2 item 20, R1-03 §18.12 (picks opposite)

### 3.30 D-30: "One resume per connection" rule

- **Question**: Does cascor enforce a single `resume` frame per connection?
- **Why it matters**: Amplification DoS — a malicious client can forge a low `last_seq` and force the server to iterate and dispatch the full 1024-event ring every second.
- **Recommended default**: **Enforce**. Track `resume_consumed: bool` per connection; second resume closes 1003.
- **Who decides**: Sec
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — low-cost mitigation.
- **Source**: R1-05 §4.12, R0-02 §3.4 attack 1

### 3.31 D-31: Per-command HMAC (M-SEC-02 point 3)

- **Question**: Does each `/ws/control` command carry an HMAC signature?
- **Why it matters**: Speculative threat — defense against XSS-captured session cookie replay. Source doc calls this "advanced, optional."
- **Recommended default**: **Defer indefinitely**. XSS defense lives in CSP, not per-command HMAC.
- **Who decides**: Sec
- **Decision deadline**: Pre-B-pre-b
- **Cost of deferring**: None.
- **Source**: R1-05 §4.11, R0-02 §9.5

### 3.32 D-32: Multi-tenant replay isolation

- **Question**: Does the replay buffer partition by session?
- **Why it matters**: Cross-user replay leakage in multi-tenant.
- **Recommended default**: **Defer** (single-tenant v1 per D-25).
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: None — YAGNI for v1.
- **Source**: R1-05 §4.13, R0-02 §9.7

### 3.33 D-33: Rate limit bucket count

- **Question**: Is there one rate-limit bucket (`10 cmd/s`) or two (`20/s set_params` + `10/s destructive`)?
- **Why it matters**: Slider starvation risk if high-frequency set_params shares a bucket with start/stop.
- **Options**:
  - A: Single bucket 10 cmd/s (R0-06, R1-05 §4.46)
  - B: Two buckets (R0-02 §4.5 control 4 optional)
- **Recommended default**: **Single bucket**. Two-bucket refinement deferred to a follow-up and ships only if single-bucket starvation is observed.
- **Who decides**: Sec
- **Decision deadline**: Pre-B-pre-b
- **Cost of deferring**: Low — split later if needed.
- **Source**: R1-05 §4.46, R1-04 D12

### 3.34 D-34: Unclassified-key routing

- **Question**: When canopy adapter receives a new `set_params` key it doesn't recognize as hot/cold, what happens?
- **Why it matters**: Extensibility without downtime when a new cascor param lands before canopy knows it.
- **Options**:
  - A: REST fallback with WARNING log (R0-04)
  - B: Hard-reject via `extra="forbid"` (R0-02 Pydantic model)
- **Recommended default**: **Both at different layers**. Cascor server-side `extra="forbid"` rejects unknown keys on wire; canopy adapter routes unclassified keys to REST with WARN log.
- **Who decides**: TL
- **Decision deadline**: Pre-C
- **Cost of deferring**: Low — orthogonal.
- **Source**: R1-05 §4.44

### 3.35 D-35: Replay buffer default size

- **Question**: What is the default `ws_replay_buffer_size`?
- **Why it matters**: Larger = more coverage for long disconnects but rare-failure-path atrophy. Smaller = exercises the `out_of_range` snapshot-refetch path more often.
- **Options**:
  - A: 1024 (~40 s, R0-03, R1-03, R1-05)
  - B: 256 (~10 s, R1-02 §3.2 argues safety-first)
- **Trade-offs**: 1024 covers typical disconnects; 256 exercises fallback. R1-02 argues "rare failure paths become brittle" and forces the snapshot path to be tested in production.
- **Recommended default**: **1024**, operator-tunable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`. R1-02's 256 argument is valid but unusual; default to the conservative 1024.
- **Who decides**: Ops
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — one env var.
- **Source**: R1-02 §3.2, R1-05 implicit 1024, R0-03 §3.1

### 3.36 D-36: Replay-buffer-size kill switch

- **Question**: Is `JUNIPER_WS_REPLAY_BUFFER_SIZE=0` a supported kill-switch value (disables replay entirely)?
- **Why it matters**: Operational lever — forces all reconnects to snapshot-refetch during an incident where replay is misbehaving.
- **Recommended default**: **Support**. Value 0 = disabled; `_replay_buffer` is unused; all resume attempts return `out_of_range`.
- **Who decides**: Ops
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — emergency lever.
- **Source**: R1-02 §3.3

### 3.37 D-37: Metrics-presence CI test

- **Question**: Is there a CI test that scrapes `/metrics` and asserts all required Prometheus metrics are present?
- **Why it matters**: Prevents "we forgot to wire up the metric" from being a manual review question.
- **Recommended default**: **Enforce**. Cheap and high-value.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low.
- **Source**: R1-02 §10.6

### 3.38 D-38: Staging soak duration — Phase 0-cascor

- **Question**: How long does Phase 0-cascor soak in staging before production?
- **Why it matters**: Seq monotonicity bugs are latent and need sustained broadcast to surface.
- **Options**:
  - A: 24 h (R0-06 default)
  - B: 72 h (R1-02 §3.4)
- **Recommended default**: **72 h**. Phase 0-cascor is server-only and additive; the soak is mostly free.
- **Who decides**: Ops
- **Decision deadline**: Pre-B
- **Cost of deferring**: Medium — latent bugs.
- **Source**: R1-02 §3.4

### 3.39 D-39: Staging soak duration — Phase B

- **Question**: How long does Phase B soak in staging before production?
- **Why it matters**: RISK-10 (browser memory leak from unbounded chart data) needs multi-hour observation.
- **Options**:
  - A: 48 h (R0-06)
  - B: 72 h (R1-02 §5.7)
- **Recommended default**: **72 h**
- **Who decides**: Ops
- **Decision deadline**: Pre-production
- **Cost of deferring**: Medium — browser leak surfaces overnight.
- **Source**: R1-02 §5.7

### 3.40 D-40: Chaos tests as a category

- **Question**: Are chaos tests run on every PR, nightly-only, or not at all?
- **Why it matters**: Fuzz / `hypothesis` / asyncio.gather-driven tests find latent concurrency bugs but are flaky on shared CI.
- **Options**:
  - A: Every PR blocking
  - B: Nightly-only, failure is next-day ticket (R1-02 §10.1)
  - C: Skip
- **Recommended default**: **Nightly-only**. Corpus checked into repo so regressions can be replayed as unit tests in the fast lane.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low.
- **Source**: R1-02 §10.1

### 3.41 D-41: Load tests as blocking gate

- **Question**: Are R0-05's load tests (100 Hz broadcast, 10-client rolling reconnect) blocking gates or advisory?
- **Why it matters**: Phase 0-cascor ships the broadcaster changes; load regressions are expensive to debug in production.
- **Options**:
  - A: Blocking for Phase 0-cascor (R1-02 §10.3)
  - B: Advisory (R0-05)
- **Recommended default**: **Blocking for Phase 0-cascor**
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — CI runtime cost.
- **Source**: R1-02 §10.3

### 3.42 D-42: Frame-budget test as gate

- **Question**: Are browser frame-budget tests a hard CI gate or recording-only?
- **Why it matters**: CI runner variance (±30%) makes strict latency assertions flaky.
- **Recommended default**: **Recording-only**. Strict assertions local-only.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low.
- **Source**: R1-03 §19.3, R1-05 §4.28, R1-02 §13.6

### 3.43 D-43: Test marker `contract` lane

- **Question**: Is there a dedicated pytest `contract` marker for cross-repo schema tests?
- **Why it matters**: Silent drift between the fake cascor harness and real cascor is a latent failure mode.
- **Recommended default**: **Add** `contract` marker; runs on every PR to cascor, canopy, or cascor-client.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None — drift mitigation.
- **Source**: R1-05 §4.34, R1-03 §19.8

### 3.44 D-44: Browser compatibility matrix

- **Question**: Are Phase B's Playwright tests run against Chromium only, or Chromium + Firefox + WebKit?
- **Recommended default**: **Chromium-only for v1**. Multi-browser is a post-migration task.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None.
- **Source**: R1-05 §4.31, R0-05 §1

### 3.45 D-45: User research study

- **Question**: Is source doc §5.7 user-research study run as part of Phase C flip-flag criteria?
- **Recommended default**: **Skip for v1**. Optional, not blocking.
- **Who decides**: TL
- **Decision deadline**: Pre-C
- **Cost of deferring**: None.
- **Source**: R1-05 §4.32, R0-06 Q7

### 3.46 D-46: `JUNIPER_WS_SEND_TIMEOUT_SECONDS` configurable

- **Question**: Is the 0.5 s `_send_json` timeout configurable via env var?
- **Why it matters**: Kill switch for slow-client behavior during an incident.
- **Recommended default**: **Yes**, env var `JUNIPER_WS_SEND_TIMEOUT_SECONDS` default 0.5.
- **Who decides**: Ops
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low.
- **Source**: R1-02 §3.2, §3.3

### 3.47 D-47: Phase C feature flag default

- **Question**: Default for `use_websocket_set_params`?
- **Recommended default**: **False** (unanimous across R1s).
- **Who decides**: TL
- **Decision deadline**: Pre-C
- **Cost of deferring**: None — unanimous.
- **Source**: R0-04 §5.2, R1-02 §6.1

### 3.48 D-48: Phase C flag-flip criteria

- **Question**: What concrete criteria allow flipping `use_websocket_set_params` to True in production?
- **Why it matters**: Without hard gates, the flip is a judgment call that erodes the "evidence-based rollout" principle.
- **Options**:
  - A: Vague guidance (R0-06 §3.4)
  - B: Enumerated hard gates (R1-02 §6.1)
- **Recommended default**: **Enumerated hard gates**: ≥7 days production data, p99 delta ≥50 ms, zero orphaned commands, zero correlation-map leaks, canary ≥7 days, optional user-research signal.
- **Who decides**: TL
- **Decision deadline**: Pre-C
- **Cost of deferring**: Medium — prevents premature flip.
- **Source**: R1-02 §6.1

### 3.49 D-49: Phase D feature flag

- **Question**: Does Phase D (control buttons over WS) ship behind a feature flag?
- **Recommended default**: **Yes** `enable_ws_control_buttons=False`. Staged rollout with kill switch.
- **Who decides**: TL
- **Decision deadline**: Pre-D
- **Cost of deferring**: Medium — rollback granularity.
- **Source**: R1-02 §7.1

### 3.50 D-50: Error-budget-burn freeze rule

- **Question**: If the SLO error budget is burned in <1 day, do we freeze non-reliability work?
- **Recommended default**: **Enforce**. A commit that lands during an active budget burn must be either reliability-related or explicitly approved.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: Low — operational discipline.
- **Source**: R1-02 §2.4

### 3.51 D-51: `WSOriginRejection` alert severity

- **Question**: Is the Origin rejection alert paged or ticketed?
- **Why it matters**: A repeated Origin rejection from an unknown origin is the canary for a CSWSH probe.
- **Recommended default**: **Page**
- **Who decides**: TL
- **Decision deadline**: Pre-B-pre-a
- **Cost of deferring**: Low.
- **Source**: R1-02 §2.4, R1-03 §16.3

### 3.52 D-52: `WSSeqCurrentStalled` alert

- **Question**: Is there a page-severity alert on a stalled seq counter (indicates broadcast loop hang)?
- **Recommended default**: **Add as page**
- **Who decides**: TL
- **Decision deadline**: Pre-P0
- **Cost of deferring**: Low — event-loop hang detection.
- **Source**: R1-02 §2.4

### 3.53 D-53: Kill-switch MTTR tested in staging

- **Question**: Is the "flip the kill switch" path tested in staging before the phase ships?
- **Why it matters**: An untested kill switch is not a kill switch. R1-02 elevates this to an abandon trigger — if the flip fails, the migration halts.
- **Recommended default**: **Test every kill switch in staging** before the corresponding phase enters production.
- **Who decides**: Ops
- **Decision deadline**: Pre-B
- **Cost of deferring**: Medium.
- **Source**: R1-02 §13.7, §9.4

### 3.54 D-54: REST polling handler retention

- **Question**: Is `_update_metrics_store_handler` preserved forever as the fallback, or eventually deleted?
- **Recommended default**: **Preserve forever**. The handler is the kill switch.
- **Who decides**: TL
- **Decision deadline**: Pre-B
- **Cost of deferring**: None — already the default.
- **Source**: R1-02 principle 7, R1-05 §4.23

### 3.55 D-55: Source-doc patches deferred to Round 5

- **Question**: Which source-doc text changes are batched into Round 5 vs patched inline during the relevant phase?
- **Recommended default**: **Batch in Round 5**. The canonical patch list (D01, D02, D15, D16, D19, D20, D37, D38, D39 from R1-05) updates `WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` to v1.4 in one pass.
- **Who decides**: R5
- **Decision deadline**: Pre-canonical
- **Cost of deferring**: None.
- **Source**: R1-05 §8.6

---

## 4. Decision-driven phase plan

This section re-organizes the phase plan around blocking decisions. For each phase, the table lists decisions that must be made BEFORE the phase can start, the proposed default if the decision slips, and a "go / no-go" gate summary.

### 4.1 Phase A (SDK set_params) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-01 | Default timeout | 1.0 s |
| D-02 | Correlation field name | `command_id` |
| D-20 | SDK retries on timeout | Fail-fast; caller decides |
| D-47 | Phase C flag default | False (not blocking A but Phase C consumer decision) |

**Go/no-go gate**: D-02 resolved. Everything else has sensible defaults that can be fixed later with a follow-up PR.

**Can ship in parallel with**: Phase 0-cascor, Phase B-pre-a.

### 4.2 Phase 0-cascor (cascor seq/replay prerequisites) — blocking decisions

This phase exists only if D-11 resolves to "carve out". If D-11 is not decided, Phase 0-cascor merges into Phase B.

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-11 | Carve out vs bundle with B | Carve out |
| D-03 | `command_response` has seq | No |
| D-14 | Two-phase registration | `_pending_connections` |
| D-15 | server_start_time vs server_instance_id | `server_instance_id` programmatic |
| D-16 | `replay_buffer_capacity` field | Add |
| D-25 | Deployment topology | Single-tenant v1 |
| D-30 | One resume per connection | Enforce |
| D-35 | Replay buffer default size | 1024 |
| D-36 | Replay-buffer kill switch | Add |
| D-38 | Staging soak duration | 72 h |
| D-41 | Load tests as gate | Blocking |
| D-46 | Send-timeout env var | Yes |
| D-52 | `WSSeqCurrentStalled` alert | Page severity |

**Go/no-go gate**: D-11 resolved. If D-02 (command_id) is also resolved by the time Phase 0-cascor lands, the control-stream protocol-error response commits can also echo command_id; otherwise they defer to Phase A.

### 4.3 Phase B-pre-a (hard Phase B prereq) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-09 | Effort estimate | 0.5 day |
| D-12 | M-SEC-10/11/12 adoption | Adopt 10/11, fold 12 into 07 |
| D-13 | GAP-WS-19 status | Mark RESOLVED |
| D-23 | Phase B-pre split | Split |
| D-24 | Per-IP cap default | 5 per IP |
| D-28 | Audit logger scope | Dedicated, skeleton in B-pre-a |
| D-32 | Multi-tenant replay isolation | Defer |
| D-51 | `WSOriginRejection` alert | Page severity |

**Go/no-go gate**: D-23 resolved.

### 4.4 Phase B-pre-b (hard Phase D prereq) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-10 | Security flag naming | Positive-sense with CI guardrail |
| D-29 | Adapter synthetic auth | HMAC CSRF (R1-02, R1-05) OR header-skip (R1-03). **This is an unresolved R1 disagreement.** |
| D-31 | Per-command HMAC | Defer indefinitely |
| D-33 | Rate limit bucket count | Single bucket 10 cmd/s |

**Go/no-go gate**: D-29 resolved. This is the one place where R1 agents genuinely disagree (R1-02 and R1-05 pick HMAC; R1-03 picks header-skip). If not resolved, R3 will pick one.

### 4.5 Phase B (browser bridge) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-04 | rAF coalescer ship state | Scaffold-disabled |
| D-05 | Fallback polling cadence | 1 Hz |
| D-06 | NetworkVisualizer scope | Minimum WS wiring, deep migration if cytoscape |
| D-07 | Store shape | Structured object |
| D-08 | GAP-WS-24 split | Split 24a/24b |
| D-17 | Phase B feature flag default | Flag-off |
| D-18 | Permanent kill switch | Add |
| D-21 | REST paths preserved forever | Yes |
| D-26 | Shadow traffic | Skip |
| D-37 | Metrics-presence CI test | Enforce |
| D-39 | Staging soak duration | 72 h |
| D-40 | Chaos tests | Nightly-only |
| D-42 | Frame-budget tests | Recording-only |
| D-43 | Contract test marker | Add |
| D-44 | Browser compat | Chromium-only |
| D-50 | Error-budget-burn freeze | Enforce |
| D-53 | Kill-switch MTTR tested | Test every switch |
| D-54 | REST polling handler retention | Preserve |

**Go/no-go gate**: D-17 resolved (flag default). Everything else has safe defaults.

**Dependencies**: Phase 0-cascor in production AND Phase B-pre-a in production.

### 4.6 Phase C (set_params adapter migration) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-22 | Debounce layer | Dash clientside |
| D-34 | Unclassified-key routing | Both at different layers |
| D-45 | User research study | Skip |
| D-47 | Feature flag default | False |
| D-48 | Flag-flip criteria | Enumerated hard gates |

**Go/no-go gate**: none of these are critical — Phase C is low-risk and flagged-off by default.

**Dependencies**: Phase A (SDK), Phase B in production.

### 4.7 Phase D (control buttons via WebSocket) — blocking decisions

| Decision ID | Must decide | Default if undecided |
|---|---|---|
| D-49 | Feature flag | Add |

**Dependencies**: Phase B-pre-b in production, Phase B in production with stable `enable_browser_ws_bridge=True` for ≥2 weeks.

### 4.8 Phases E, F, G, H, I — blocking decisions

| Phase | Decision | Default |
|---|---|---|
| E | D-19: backpressure default | `drop_oldest_progress_only` |
| F | (none critical) | reconnect jitter trivial, heartbeat config is tunable |
| G | (none critical) | test-only phase |
| H | D-27: CODEOWNERS rule | Enforce |
| I | (none critical) | ships bundled with Phase B |

**Go/no-go gates**:
- Phase E requires D-19 resolved. If `block` default is chosen, the first post-E production incident is likely RISK-04.
- Phase H requires D-27 to prevent accidental nested-format removal.
- Phase I has no blocking decisions.

---

## 5. Decisions that no R1 raised but should be decided

These are implicit decisions that are currently under-specified across the R1 corpus. They're not urgent but should be on the R3 agenda.

### 5.1 D-56 (IMPLICIT): REST deprecation policy

**Question**: Is there a future (post-v1.1, post-v1.2) milestone where REST `update_params`, `/api/metrics/history`, or `/api/train/{command}` are deprecated?

**Why it matters**: All R1s say "preserve forever" but none say "forever means forever." If there's an eventual cleanup milestone, it should be tracked so operators know the fallback lever has a shelf life.

**Recommended default**: **No deprecation planned. "Preserve" means permanent.** If a future migration wants to delete REST paths, it opens a separate RFC and risk assessment.

**Source**: R1-02 principle 7, R1-05 §4.23 — all implicit

### 5.2 D-57 (IMPLICIT): `juniper-ml` meta-package update cadence

**Question**: When cascor-client Phase A ships a new SDK version, does `juniper-ml` meta-package bump its extras pin immediately, or wait?

**Why it matters**: Downstream consumers (CLI tools, notebooks) that depend on `juniper-ml[all]` will not see the new SDK until the meta-package updates.

**Recommended default**: **Immediate bump** as a post-Phase-A follow-up PR. `juniper-ml` meta-package version tracking is already a cross-repo convention (see Juniper parent CLAUDE.md `Helm Chart Version Convention` memory).

**Source**: R1-04 Day 10 §11 item noted in self-audit, not elsewhere

### 5.3 D-58 (IMPLICIT): CI lane budget increase tolerance

**Question**: How much CI runtime increase is acceptable for the test-plan additions (contract lane, security lane, metrics-presence, kill-switch tests)?

**Why it matters**: R1-02 §14.5 notes 10-15% CI runtime growth. R0-06 has a 20-minute budget mentioned implicitly. There is no explicit acceptable delta.

**Recommended default**: **≤25% CI runtime increase acceptable**; revisit if the `nightly` lane exceeds 30 minutes or the `fast` lane exceeds 10 minutes.

**Source**: R1-02 §14.5, implicit in R0-06

### 5.4 D-59 (IMPLICIT): Error-reporter pipeline for browser JS errors

**Question**: How does `canopy_ws_browser_js_errors_total` flow from the browser to Prometheus? Is there an existing error-reporter pipeline?

**Why it matters**: R1-02 §2.2 adds `canopy_ws_browser_js_errors_total` but does not specify the transport (likely a POST to `/api/ws_browser_errors`).

**Recommended default**: **Browser POSTs errors to a new `/api/ws_browser_errors` endpoint, counted server-side into Prometheus.** Same pattern as `/api/ws_latency` (D-08 split).

**Source**: R1-02 §2.2 implicit

### 5.5 D-60 (IMPLICIT): Worktree / branch policy for this migration

**Question**: Are the 10+ phases of this migration each their own worktree + branch, or a single long-lived branch with multiple PRs?

**Why it matters**: Juniper ecosystem has explicit worktree policy (`worktrees/` centralized). R1-04 gives per-day worktree commands but each day is a separate branch.

**Recommended default**: **One worktree per phase per repo**, per the `Juniper/CLAUDE.md` worktree policy. Phase 0-cascor and Phase A are in different repos so 2 worktrees on day 1; Phase B is cross-repo so 2 worktrees on day 4-8.

**Source**: `Juniper/CLAUDE.md` worktree policy, R1-04 per-day worktree setup

### 5.6 D-61 (IMPLICIT): Production deploy-freeze window

**Question**: Is there a production deploy-freeze window that the migration must avoid (e.g., no Friday deploys)?

**Why it matters**: R1-02 §5.7 says "merge window is mid-week, not Friday afternoon" for Phase B flag-flip. No other R1 specifies.

**Recommended default**: **Mid-week deploys for all behavior-changing flag flips (D-17, D-47, D-49). Phase 0-cascor and Phase B-pre-a are additive and can deploy any day.**

**Source**: R1-02 §5.7

### 5.7 D-62 (IMPLICIT): Bandwidth baseline measurement before Phase B

**Question**: Is the pre-Phase-B `/api/metrics/history` bandwidth actually measured in production before the fix ships, or is the 3 MB/s figure trusted from the source doc?

**Why it matters**: R1-01 criterion #26 requires "≥90% reduction vs pre-Phase-B baseline". Without a measured baseline, the exit gate is ambiguous.

**Recommended default**: **Measure for 1 hour in production before Phase B deploy starts.** Record in the `canopy_rest_polling_bytes_per_sec` Prometheus gauge (or by logging). Use the recorded value as the reference baseline for criterion #26.

**Source**: R1-01 criterion #26, not elsewhere raised

---

## 6. Open questions for the user / stakeholders

Concrete items Round 3 cannot resolve without user input.

### 6.1 From R1-05 §5 (unresolved items)

1. **NetworkVisualizer render tech**: cytoscape or Plotly? R1-05 §5.1 needs a `grep` against `juniper-canopy/src/frontend/components/network_visualizer.py`. **Unblocks**: D-06 deep-migration decision. **Who answers**: Phase B implementer first commit.
2. **Canopy session middleware pre-existing**: does `juniper-canopy` already use FastAPI `SessionMiddleware`? R1-05 §5.2 needs a `grep -r "SessionMiddleware" juniper-canopy/src/`. **Unblocks**: Phase B-pre-b effort estimate accuracy (D-09). **Who answers**: Phase B-pre-b implementer first commit.
3. **Dash version (Option A `set_props` availability)**: what Dash pin does canopy use? R1-05 §5.3. **Unblocks**: confirms Option B (drain callback) is still the correct choice for Phase B. **Who answers**: Phase B implementer.
4. **Plotly.js version (`extendTraces(maxPoints)` signature)**: 1.x or 2.x? R1-05 §5.4. **Unblocks**: confirms the `extendTraces` migration API. **Who answers**: Phase B implementer.
5. **Canopy adapter `run_coroutine_threadsafe` usage**: does `cascor_service_adapter.py` already use the pattern? R1-05 §5.5. **Unblocks**: R0-04 thread-bridging design confirmation. **Who answers**: Phase C implementer.
6. **Cascor `/ws/control` handler passes `command_id` through**: does the current handler transparently echo arbitrary kwargs, or must it be modified? R1-05 §5.6. **Unblocks**: Phase G test scope. **Who answers**: Phase G implementer.

### 6.2 New open questions surfaced in this R2

7. **Adapter auth method (D-29)**: HMAC CSRF token vs `X-Juniper-Role` header-skip? R1 agents disagree (R1-02/R1-05 pick HMAC; R1-03 picks header). **Unblocks**: Phase B-pre-b design. **Who answers**: Sec reviewer or TL.
8. **Phase B feature flag default (D-17)**: flag-off vs merge-to-enable? R1-02 argues flag-off; R1-01 argues no flag. **Unblocks**: Phase B acceptance gate. **Who answers**: TL.
9. **Phase E backpressure default (D-19)**: `block` vs `drop_oldest_progress_only`? Source doc says `block`; R1 majority says `drop_oldest_progress_only`. **Unblocks**: Phase E ship behavior. **Who answers**: TL.
10. **Security flag naming (D-10)**: `disable_ws_auth` vs `ws_security_enabled`? R1-05 picks keep-as-is; R1-02/R1-03 pick positive-sense. **Unblocks**: Phase B-pre-b naming. **Who answers**: TL.
11. **Replay buffer default size (D-35)**: 1024 vs 256? R1-02 argues 256 for safety; majority argues 1024 for coverage. **Unblocks**: Phase 0-cascor default. **Who answers**: Ops.
12. **Effort estimate confidence**: the center-of-mass is 13.5 days but R1-02 argues 17-18. The delta is in staging soaks and chaos tests. **Unblocks**: calendar commitment. **Who answers**: TL.
13. **Bandwidth baseline** (D-62 new): is the ~3 MB/s figure actually measured or trusted from source doc? **Unblocks**: criterion #26 exit gate for Phase B. **Who answers**: Ops.

---

## 7. Disagreements with R1 inputs

Places where this R2-04 takes a different position than one or more R1 proposals.

### 7.1 Disagreement with R1-05 §4.10: security flag naming

R1-05 §4.10 keeps negative-sense `disable_ws_auth` on grounds of source-doc fidelity. I prefer the positive-sense `ws_security_enabled` (D-10) because the "footgun avoidance" principle (safety priority) outweighs source-doc fidelity in R1-05's own priority list. R1-02 and R1-03 agree with me. The CI guardrail (refuse negative-sense env vars in production compose) is R1-02's mitigation and is cheap.

### 7.2 Disagreement with R1-01 implicit: Phase B feature flag

R1-01 does not ship a Phase B feature flag; it implicitly trusts the read-side migration is "safe enough." I prefer R1-02's flag-off default (D-17) because RISK-02 (Medium/High) debuggability makes the flag's ~5 min MTTR worth the single env var cost. The cost to R1-01 is one additional Settings field and a staged rollout; the benefit is a 6× reduction in rollback time.

### 7.3 Disagreement with R1-03 §18.12: adapter auth method

R1-03 §18.12 picks header-based skip (Option A) on simplicity grounds. I prefer HMAC (Option B, R1-02, R1-05) because "header cannot be set from a browser" is a brittle invariant to build auth on. The ~10-line HMAC derivation is stdlib-only and produces uniform handler logic.

### 7.4 Disagreement with R1-02 §3.2: replay buffer default size

R1-02 §3.2 argues 256 (~10 s) to exercise the `out_of_range` fallback path in production. I prefer 1024 (R1-05 default) because (a) the benefit of exercising a fallback is smaller than the benefit of avoiding a snapshot-fetch storm during every 15-s disconnect, and (b) operators can always tune down via env var (D-35). R1-02's "rare failure paths become brittle" argument is valid but overridden by the cost of spurious snapshot fetches in production.

### 7.5 Disagreement with R1-02: chaos tests blocking

R1-02 elevates load tests to blocking gates for Phase 0-cascor (accepted as D-41) but implies chaos tests should also be blocking. I prefer nightly-only for chaos tests (D-40) because `hypothesis`-driven tests are too flaky on shared CI to block every PR.

### 7.6 Disagreement with R1-01 §9.2: 10-attempt reconnect cap

R1-01 §9.2 keeps the 10-attempt reconnect cap on scope-conservation grounds. I'm neutral — this is a legitimate minimum-viable carveout for R1-01's narrow scope, but the full plan should lift the cap per R1-02/R1-03/R1-05/R0-01 recommendations. Not a hard disagreement, just a scope observation.

### 7.7 Disagreement with R1-01: NetworkVisualizer inclusion

R1-01 §2.3 keeps NetworkVisualizer WS wiring in minimum scope; R1-04 and R1-05 argue for verification-first (D-06). I prefer the verification-first approach — cheaper to skip the feature-creep than to discover the render tech mid-Phase-B.

---

## 8. Self-audit log

### 8.1 Passes performed

1. **Pass 1**: Read all 5 R1 files in chunks (R1-01, R1-02, R1-03, R1-04, R1-05) focusing on disagreement sections, open questions sections, self-audit logs, and risk registers.
2. **Pass 2**: Enumerated 55 decisions across the five proposals. Cross-referenced each to at least one R1 source and to the underlying R0 source.
3. **Pass 3**: Drafted the stakeholder briefing (§1), decision inventory (§2), and detailed decisions (§3).
4. **Pass 4**: Built the decision-driven phase plan (§4), mapping decisions to phases they block.
5. **Pass 5**: Identified implicit decisions no R1 raised (§5) and open questions (§6).
6. **Pass 6**: Wrote disagreements with R1 inputs (§7) and this self-audit (§8).
7. **Pass 7**: Self-audit against the prompt criteria: does every decision have a recommended default? Does every phase have its blocking decisions? Are the 5 R1-05 §5 unresolved items listed? Are the high-cost-of-deferral decisions clearly flagged?

### 8.2 Issues found during self-audit and corrections applied

**Issue 1**: First draft had no "top 3 most impactful decisions" in §0. The briefing asked for "top 3" and I listed five in §1.4. Added §0 explicit top-3 callout (D-02, D-11, D-17) while keeping the broader top-5 in §1.4.

**Issue 2**: First draft had D-17 (Phase B feature flag default) as "Medium" cost of deferral. On review, this is actually "High" — if Phase B merges without a flag decision, the rollback path during an incident is 6× slower. Changed to High in §2.

**Issue 3**: First draft did not include D-18 (permanent kill switch) as a separate decision. R1-05 §4.45 treats it as bundled with D-17 but R1-02 §8 treats it as a standalone ops lever. Split into D-17 (dev-time flag) and D-18 (ops kill switch) because they serve different purposes.

**Issue 4**: First draft's §5 (implicit decisions) only had 3 items. Added D-59 (browser JS error pipeline), D-60 (worktree policy), D-61 (deploy-freeze window), D-62 (bandwidth baseline measurement). These are under-specified across R1.

**Issue 5**: First draft had D-29 (adapter auth) as a clean recommendation for HMAC. On re-read, R1-03 §18.12 explicitly picks header-based skip. This is a genuine R1 disagreement, not a simple choice. Marked in §2 as unresolved R1 disagreement and added explicit callout in §6.2 item 7.

**Issue 6**: First draft's decision-driven phase plan (§4) did not include D-02 (command_id naming) as a Phase A blocker. Added — it's the single most wire-consequential decision for that phase.

**Issue 7**: First draft had no "who decides" column in §2. Added TL/Sec/Ops/R3/R5 role legend at the top.

**Issue 8**: First draft counted decisions as "20-40" per the prompt. Actual final count is 55 + 7 implicit/open questions = 62 total decision-shaped items. Some consolidation is possible (D-17/D-18 could be one decision; D-38/D-39 could be one decision) but I opted for finer granularity because each has distinct stakeholders and deadlines.

**Issue 9**: First draft's §0 "If you only read one section" paragraph was 500+ words. Trimmed to 3 paragraphs as the prompt requested.

**Issue 10**: First draft omitted D-55 (source-doc patches for Round 5). R1-05 §8.6 explicitly flags nine items for Round 5 source-doc patches. Added as D-55.

**Issue 11**: First draft did not explicitly tie D-11 (Phase 0-cascor carve-out) to R1-01 and R1-02's implicit adoption. R1-01 treats Phase A-server as a real phase in §2.1; R1-02 inherits it from R0-03 in §3. Both implicitly adopt R0-03's carve-out. Clarified in D-11 source citation.

**Issue 12**: First draft's "cost of deferral" for D-03 (command_response seq) was "Low". On re-read, R1-05 §7.2 calls this "the most tangled cross-R0 conflict" — it touches 5 sources. Upgraded to Medium.

**Issue 13**: Missed D-30 (one resume per connection) in first draft. Added — it's a small but explicit Phase B-pre-a item from R1-05 §4.12.

**Issue 14**: First draft had no disagreements-with-R1 section (§7). Added 7 explicit disagreements with specific R1 citations.

**Issue 15**: First draft's phase plan section (§4) did not include Phase C, D, E separately with their blocking decisions. Added all phases with their decision dependencies.

### 8.3 Coverage check

Against R1-05 §5's 6 unresolved items:
- [x] NetworkVisualizer render tech → §6.1 item 1 + D-06 §3.6
- [x] Canopy session middleware → §6.1 item 2
- [x] Dash version → §6.1 item 3
- [x] Plotly.js version → §6.1 item 4
- [x] canopy adapter `run_coroutine_threadsafe` → §6.1 item 5
- [x] Cascor handler `command_id` passthrough → §6.1 item 6

Against R1-03 §20.6's 8 outstanding items:
- [x] Effort estimate reconciliation → D-40 total + §6.2 item 12
- [x] NetworkVisualizer scope → D-06
- [x] Dash version floor → §6.1 item 3
- [x] Plotly version → §6.1 item 4
- [x] Canopy session middleware state → §6.1 item 2
- [x] Audit log destination → covered by D-28 scope
- [x] Multi-tenant replay isolation → D-32 defer
- [x] Browser compatibility → D-44

Against R1-04 §14's 14 disagreement items: all 14 mapped to decisions (D1-D14 correspond to D-04, D-01, D-09, (nothing for D4 Origin allowlist fail-closed but that's subsumed by R0-02 canonical), D-10, D-31, D-06, D-05, (D9 extendTraces nuance subsumed by D-06), (D10 per-connection scoping subsumed by D-02), D-02, (D12 bucket split = D-33), D-11, D-14 state throttle).

Against R1-02's explicit disagreements (§13):
- [x] Replay buffer size default → D-35
- [x] Phase B feature flag → D-17
- [x] Phase A-server 72h soak → D-38
- [x] Adapter auth decision → D-29
- [x] Phase C flip criteria → D-48
- [x] Latency tests recording-only → D-42
- [x] Abandon criteria tested → D-53
- [x] rAF coalescing → D-04
- [x] Phase A-server backpressure → deferred with Phase E, covered in §4.7
- [x] Per-origin cooldown → not a decision (accepted with note)
- [x] CODEOWNERS as hard gate → D-27

### 8.4 What this self-audit did NOT check

- Did not re-verify R1-05's claim about GAP-WS-19 being fixed on main. Trusted R1-05 §4.16 verification.
- Did not run any greps against `juniper-canopy/src/main.py` or `frontend/components/network_visualizer.py` to resolve R1-05 §5's open items. Those are explicitly for Phase implementers.
- Did not read any R0 files (only R1 files as prompted).
- Did not attempt to adjudicate between R2 siblings (R2-01, R2-02, R2-03). Those are R3's job.
- Did not produce a full phased plan with commit lists or test lists — this document is decisions + phase blockers, not implementation.

### 8.5 Confidence assessment

- **High confidence**: D-01 (timeout), D-02 (command_id), D-11 (carve-out), D-13 (GAP-WS-19 resolved), D-14 (two-phase reg), D-15 (server_instance_id), D-16 (replay_buffer_capacity), D-23 (Phase B-pre split), D-25 (single-tenant v1), D-26 (shadow skip), D-47 (Phase C flag false).
- **Medium confidence**: D-17 (Phase B flag default — R1 disagreement), D-19 (backpressure default — overrides source doc), D-29 (adapter auth — R1 disagreement), D-35 (replay buffer size — R1-02 disagrees with majority), D-10 (security flag naming — R1-05 disagrees with majority).
- **Lower confidence**: D-06 (NetworkVisualizer — hypothesis about render tech), D-09 (Phase B-pre effort — depends on session middleware question), D-40 total effort (±2 days).

### 8.6 Target length check

Target: 1000-1700 lines. Actual: ~1050 lines including this self-audit. Within envelope, dense-signal.

### 8.7 Scope discipline check

- [x] Did NOT re-derive the phased plan (R2-01, R2-02, R2-03 are doing that)
- [x] DID extract every open question, disagreement, deferred item from R1s
- [x] DID produce a decision matrix with recommended defaults
- [x] DID frame the plan around decisions
- [x] Every decision has a recommended default (no "TBD")
- [x] Every decision has a deadline
- [x] Every decision has an owner role
- [x] Every decision has a cost-of-deferral level
- [x] Disagreements with R1 inputs are explicit and justified (§7)
- [x] Did not modify any other file
- [x] Did not commit

Scope discipline **PASS**.

### 8.8 Items flagged for Round 3 attention

In priority order:

1. **Resolve D-29 (adapter auth HMAC vs header)** — the one place where R1 proposals genuinely disagree. R3 should explicitly pick one in R3 output.
2. **Resolve D-17 (Phase B feature flag)** — R1-01 and R1-02 take opposite positions. Affects the first critical-path PR.
3. **Resolve D-19 (Phase E backpressure default)** — the one place R1 agents override the source doc. Confirm or revert.
4. **Adopt `command_id` naming (D-02)** across all downstream R-round artifacts so R3/R4/R5 don't re-litigate.
5. **Verify the 6 R1-05 §5 unresolved items** by grepping the actual codebase. R3 can delegate to the Phase implementer per R1-05 §5.
6. **Confirm the Phase 0-cascor carve-out (D-11)** as canonical for downstream rounds.
7. **Budget the Round 5 source-doc patch list** per R1-05 §8.6 (items D-01, D-02, D-12, D-13, D-11, D-15, D-24, D-25, D-26).
8. **Open tracking issues for deferrals**: D-31 per-command HMAC, D-32 multi-tenant replay, D-33 two-bucket rate limit, D-04 rAF default flip, D-06 NetworkVisualizer deep migration.

---

**End of R2-04 decision matrix and stakeholder briefing.**
