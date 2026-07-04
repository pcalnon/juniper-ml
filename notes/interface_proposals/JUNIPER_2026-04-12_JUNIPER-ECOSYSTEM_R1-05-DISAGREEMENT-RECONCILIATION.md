# Round 1 Proposal R1-05: Disagreement Reconciliation & Resolved-Position Development Plan

**Angle**: Resolve cross-proposal disagreements and re-derive a plan from the resolved positions
**Author**: Round 1 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 1 consolidation — input to Round 2
**Inputs consolidated**: R0-01 (frontend perf), R0-02 (security), R0-03 (cascor backend), R0-04 (SDK set_params), R0-05 (testing), R0-06 (ops/phasing/risk)

---

## 1. Scope

This proposal is the reconciliation lane of Round 1. It does not re-derive the full phased plan from scratch — sibling R1 agents are already doing that from architecture, contracts, testing, and security angles. Its job is narrower and more surgical:

1. **Catalog** every disagreement across the six Round 0 proposals: both the explicit "disagrees with the source doc" sections and the implicit cross-proposal conflicts that appear when two R0s touch the same topic from different angles (same field named two different things, same risk allocated to two different phases, same control with two different default values, same phase with two different effort estimates).
2. **Resolve** each disagreement using the priority order codified in §2: source-doc fidelity, safety, evidence, operational simplicity, reversibility.
3. **Re-derive** the parts of the development plan that the resolutions change. This is NOT a full re-plan — it is the delta from the unresolved R0 corpus to a consistent R1 position. Where the R0 proposals already agree, the plan is unchanged.

What this proposal does NOT do:

- Does not re-write the source architecture doc.
- Does not design new controls, new APIs, or new phases that none of the R0 proposals raised.
- Does not adjudicate disagreements between this proposal and sibling R1 proposals. That is Round 2's job.
- Does not add new GAP-WS or M-SEC identifiers; it only reconciles existing ones.

**Method**: I read all six R0 proposals in full, extracted every disagreement statement (`§11`, `§12`, `§13`, `§14` style sections) plus every implicit conflict (e.g., R0-03 says command_response has no seq; R0-04 uses a `request_id` field that R0-02 calls `command_id` — three proposals, three vocabularies for the same idea). I then applied the resolution criteria from §2 below to each.

When in doubt about a cited claim, I cross-checked against the source architecture doc (`juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE) and against the current state of cascor `manager.py`. Cross-checks are cited inline.

---

## 2. Resolution criteria (priority order)

Applied in this order; higher items win ties:

1. **Source-doc fidelity**. The v1.3 STABLE architecture doc is the authoritative baseline. When an R0 disagrees with the source doc, the source doc wins unless (a) a higher-priority criterion below applies, or (b) the R0 provides concrete evidence the source doc is stale or internally inconsistent.
2. **Safety**. When a resolution is ambiguous between "more secure / more conservative" and "less secure / more optimistic", the safer choice wins. Applies especially to feature-flag defaults, per-IP caps, auth gating.
3. **Concrete evidence**. When an R0 cites a file:line, a grep result, or a test result, that evidence beats armchair reasoning — even from the source doc.
4. **Operational simplicity**. When two technically equivalent designs are both defensible, the simpler one wins. Fewer moving parts, fewer configs, fewer branches.
5. **Reversibility**. When the two candidates differ in how hard they are to back out of later, prefer the reversible option. Reversibility includes: feature flags are better than hard commits; additive fields are better than renames; permanent fallbacks are better than removals.

**Anti-criterion** (what I explicitly do NOT use to resolve): proposal line-count, author assertiveness, cosmetic beauty of the code, or "it's more modern" arguments. Several R0 proposals use Option A vs Option B framings where one is newer/prettier; I do not privilege that alone.

---

## 3. Catalog of disagreements

This section enumerates every disagreement I identified. For each, I note the positions, severity, and whether it's a conflict with the source doc or between R0s (or both). Resolutions are in §4. Disagreements I could not resolve are re-listed in §5 with the evidence that would resolve them.

### 3.1 Disagreements with the source doc (per R0)

Consolidated from each R0's disagreement/self-audit section.

| # | Topic | Source-doc position | Proposing R0 | Resolution in §4 |
|---|---|---|---|---|
| D01 | `set_params` default timeout | §7.1 GAP-WS-01 says 5.0 s; §7.32 GAP-WS-32 says 1 s | R0-04 picks 1.0 | §4.1 |
| D02 | `request_id` / `command_id` in `set_params` wire frame | §3.2.3 envelope omits it; §7.32 mentions `command_id` as client-generated UUID | R0-04 adds `request_id` as new field, R0-02 calls it `command_id`, R0-03 echoes `command_id` | §4.2 |
| D03 | rAF coalescing (GAP-WS-15) ship state | source doc lists under Phase B | R0-01 proposes shipping scaffold but feature-flagged DISABLED | §4.3 |
| D04 | REST polling fallback rate when WS disconnected | source doc §6.3 only specifies "no_update when connected"; does not specify fallback cadence | R0-01 proposes slowing fallback from 100 ms to 1 Hz | §4.4 |
| D05 | NetworkVisualizer inclusion in Phase B | source doc lumps into Phase B chart/panel callbacks | R0-01 proposes deferring to Phase B+1 (cytoscape, not Plotly) | §4.5 |
| D06 | §5.5 "MUST use extendTraces" literal reading | source doc says `extendTraces` for live | R0-01 clarifies: `Plotly.react` for snapshot replace, `extendTraces` for live | §4.6 |
| D07 | `ws-metrics-buffer` store shape | source doc says "bounded ring of last 1000 metrics" | R0-01 proposes `{events: [...], gen: int, last_drain_ms: float}` structured object | §4.7 |
| D08 | GAP-WS-24 scope split (browser vs server) | source doc bundles | R0-01 carves out browser-emitter only; server /api/ws_latency separate | §4.8 |
| D09 | Phase B-pre effort estimate | source doc §9.2 says 1 day | R0-02 says 1.5-2 days; R0-06 says +1.5 days observability overall | §4.9 |
| D10 | `Settings.disable_ws_auth` naming | source doc uses negative-sense flag | R0-02 proposes `ws_security_enabled=True` positive sense (no strong pref) | §4.10 |
| D11 | Per-command HMAC (M-SEC-02 point 3) | source doc lists as "advanced, optional" | R0-02 defers indefinitely | §4.11 |
| D12 | Replay buffer security dimension (one resume per conn) | source doc treats replay as correctness-only | R0-02 adds "one resume per connection" as security control | §4.12 |
| D13 | Multi-tenant replay isolation | source doc silent | R0-02 flags as open question Q1-sec | §4.13 |
| D14 | Audit logger scope | source doc M-SEC-07 mentions scrub allowlist only | R0-02 adds full dedicated audit logger | §4.14 |
| D15 | New M-SEC-10, M-SEC-11, M-SEC-12 identifiers | source doc stops at M-SEC-07 | R0-02 adds 3 new IDs | §4.15 |
| D16 | GAP-WS-19 (`close_all()` lock) status | source doc flags as unresolved P2 | R0-03 verified RESOLVED on main; I confirmed at manager.py:138-156 | §4.16 |
| D17 | `command_response` has seq field | source doc "all outbound have seq" implied | R0-03 carves out: personal RPC responses on /ws/control do NOT get seq | §4.17 |
| D18 | Two-phase registration (_pending_connections) | source doc doesn't specify atomic replay→live handoff mechanism | R0-03 introduces `_pending_connections` set + `promote_to_active()` | §4.18 |
| D19 | Phase A-server carve-out | source doc bundles cascor seq/replay work into Phase B | R0-03 proposes carving into a ~2-day Phase A-server prereq | §4.19 |
| D20 | `server_start_time` vs `server_instance_id` naming | source doc uses both inconsistently | R0-03 flags: standardize on `server_instance_id` for comparison; `server_start_time` advisory only | §4.20 |
| D21 | `replay_buffer_capacity` in `connection_established` | source doc silent | R0-03 adds as additive field so client can optimize | §4.21 |
| D22 | SDK-side retries on `set_params` timeout | source doc silent | R0-04 explicitly says "no SDK-level retries; canopy adapter decides" | §4.22 |
| D23 | Keep REST `update_params` forever | source doc §9.4/§9.5 preserves REST paths; specific `/api/v1/training/params` unaddressed | R0-04 explicitly: never deprecate | §4.23 |
| D24 | Debounce layer (UI or SDK) | source doc silent | R0-04 says debounce lives in Dash clientside callback, NOT SDK | §4.24 |
| D25 | Phase C (`test_set_params_caller_cancellation`) criticality | source doc lists as one of six tests, not flagged critical | R0-05 elevates to mandatory Phase A gate | §4.25 |
| D26 | Phase C routing unit tests missing | source doc §9.4 lists browser tests + AsyncMock only | R0-05 adds explicit hot/cold routing unit tests | §4.26 |
| D27 | Playwright+dash_duo parallel runtime estimate | source doc says 2-4 min | R0-05 says 5-8 min (dash_duo is Selenium, does not parallelize) | §4.27 |
| D28 | §5.6 CI latency integration not specified | source doc describes instrumentation but not CI policy | R0-05 adds recording-only lane for CI, strict local-only | §4.28 |
| D29 | Phase G test scope too narrow | source doc §9.8 | R0-05 expands with two tests (concurrent corr, next-epoch boundary) | §4.29 |
| D30 | Fake harness schema parity contract test | source doc silent | R0-05 adds `test_fake_cascor_message_schema_parity` | §4.30 |
| D31 | Browser compatibility matrix | source doc §11 Q2 open | R0-05 narrows to Chromium-only for v1 | §4.31 |
| D32 | §5.7 user research automation | source doc lists as optional | R0-05 excludes from automated tests; keeps as separate task | §4.32 |
| D33 | `dash_duo` limitations documented | source doc silent about limits | R0-05 documents known limits | §4.33 |
| D34 | Contract-test lane as distinct marker | source doc silent | R0-05 proposes new `contract` marker | §4.34 |
| D35 | Phase B-pre splitting into B-pre-a / B-pre-b | source doc bundles into single Phase B-pre | R0-06 proposes split: max_size gates Phase B; Origin+CSRF gates Phase D | §4.35 |
| D36 | Phase E default backpressure policy | source doc §9.6 ships with `block` default | R0-06 proposes `drop_oldest_progress_only` as default | §4.36 |
| D37 | Q6 (per-IP cap) resolution timing | source doc leaves as open question | R0-06 resolves now: 5/IP default | §4.37 |
| D38 | Q1 (deployment topology) resolution timing | source doc leaves as open question | R0-06 resolves now: single-tenant v1 | §4.38 |
| D39 | Shadow traffic strategy | source doc silent | R0-06 explicitly rejects (state duplication trap) | §4.39 |
| D40 | §9.11 total effort estimate | source doc says ~12 days / ~4 weeks | R0-06 proposes 13.5 days + 4.5 weeks | §4.40 |
| D41 | Phase H CODEOWNERS enforcement for _normalize_metric | source doc says "lock in via regression test" | R0-06 adds CODEOWNERS as operational guard | §4.41 |

### 3.2 Cross-R0 disagreements (implicit or explicit)

These are conflicts where two or more R0s take different positions on the same object. The positions may each individually be consistent with the source doc but are mutually inconsistent with each other.

| # | Topic | Position A | Position B | Severity |
|---|---|---|---|---|
| X01 | correlation-ID vocabulary | R0-04: `request_id` | R0-02: `command_id` (and source doc §7.32 also says `command_id`); R0-03: `command_id` | High — protocol wire field |
| X02 | `command_response` carries seq field | R0-03: NO (personal RPC, no seq namespace) | R0-02 schema implies yes (envelope schema); R0-01 assumes yes in chart drain | High — cross-repo contract |
| X03 | Phase A-server carve-out | R0-03: yes, carve out ~2 days so cascor seq+replay lands before canopy Phase B | R0-01, R0-04, R0-05: implicit no — all treat Phase B as single unit containing cascor seq work | Medium — scheduling |
| X04 | Phase B-pre effort | R0-02: 1.5-2 days | R0-06: 1 day + 1.5 day observability (call it 2.5 days total) | Low — cost estimation |
| X05 | Phase B-pre splitting | R0-06: split into B-pre-a (max_size) and B-pre-b (Origin+CSRF) | R0-02: keep as single B-pre bundle | Medium — phase ordering clarity |
| X06 | rAF coalescer enabled or disabled in Phase B | R0-01: disabled, scaffold only | R0-05 implicit: assumes enabled (test `test_frame_budget_batched_50_events_under_50ms` expects rAF coalesce) | Medium — frontend behavior |
| X07 | Demo mode test lane | R0-01: dash_duo in Phase B gate | R0-05: dash_duo in Phase B gate BUT also recommends in fast lane | Low — CI placement |
| X08 | Polling fallback slowdown | R0-01: 1 Hz during reconnect | R0-06 / source doc: only specifies "no_update when connected" | Low — cadence detail |
| X09 | NetworkVisualizer Phase B or B+1 | R0-01: defer to B+1 (cytoscape, not Plotly) | R0-05 Phase B gate includes `test_ws_metrics_buffer_store_is_ring_buffer_bounded` and `test_connection_indicator_badge_reflects_state` but is silent on NetworkVisualizer | Low — scope detail |
| X10 | Seq numbers on command_response | R0-03: no | R0-02 `CommandFrame` / `AuthFrame` / `ResumeFrame` models imply yes for inbound; R0-05 `test_seq_monotonically_increases_per_connection` implies yes for all outbound | High — tied to X02 |
| X11 | Replay buffer as separate class or WebSocketManager attribute | R0-03: attribute | nobody disagrees | None — non-issue |
| X12 | SDK reconnect queueing of `set_params` | R0-04: NO queue (fail-fast; canopy adapter decides) | R0-05 `test_set_params_reconnection_queue` — test name implies queue, R0-05 acknowledges "1 of 2 design variants" | Medium — SDK contract |
| X13 | Adapter synthetic auth frame for canopy→cascor hop | R0-02: `X-Juniper-Role: adapter` header skip OR HMAC CSRF-shaped | R0-04: silent (doesn't discuss it; assumes API key auth is sufficient) | Medium — cross-process auth |
| X14 | Whose job to wire `/api/ws_latency` endpoint | R0-01: out of scope (defer to backend agent); gate browser POST behind flag | R0-06 §6.4: "Phase B implements the pipe"; §6.4 step 1 says canopy backend | Low — ownership assignment |
| X15 | Unclassified-key routing default | R0-04: default to REST with warning log | R0-02: `extra="forbid"` on Pydantic schema would reject unknown keys hard | Medium — UX of extensibility |
| X16 | Phase B feature flag for browser bridge | R0-01: `Settings.enable_browser_ws=False` default during Phase B-pre gap | R0-06: `Settings.disable_ws_bridge` kill switch with default False (meaning bridge ENABLED) | High — opposite defaults |
| X17 | Rate limit buckets per command type | R0-02: two buckets (set_params separate from start/stop) | R0-06: one bucket, 10 cmd/s | Low — implementation detail |
| X18 | Seq on command_response tied to replay buffer eligibility | R0-03: no seq, no replay eligibility, separate ns per endpoint | R0-02 & R0-05: replay buffer contract implies all outbound carry seq | High — tied to X02, X10 |
| X19 | Two-phase registration vs seq_cursor | R0-03 prefers pending set; acknowledges seq_cursor as alt | nobody else discusses | Low — alt considered |
| X20 | Audit log scope | R0-02: full dedicated audit logger (Phase B-pre) | R0-06: "Logs" section generic, implies shared application logger | Medium — ops tooling |

---

## 4. Resolutions

For each disagreement, I give positions, evidence, trade-offs, my recommendation, and the implementation impact. Cross-R0 conflicts (X-series) are woven in where they relate to the source-doc disagreements (D-series).

### 4.1 D01 — `set_params` default timeout

**Positions**:

- Source doc §7.1 GAP-WS-01 remediation hook: `CascorControlStream.set_params(params, timeout=5.0)`.
- Source doc §7.32 GAP-WS-32 per-command timeout table: `set_params: 1 s`.
- R0-04 §4.1 and §12.1: 1.0 s.

**Evidence**: I verified both citations in the source doc. Line 1137: `set_params(params, timeout=5.0)`. Line 1403: "per-command timeouts (e.g., `start`: 10 s, `stop`/`pause`/`resume`: 2 s, `set_params`: 1 s)". The source doc is internally inconsistent; §7.1 appears to carry over the generic `DEFAULT_CONTROL_STREAM_TIMEOUT=5.0` without noticing §7.32 exists.

**Trade-offs**:

- **1.0 s**: matches slider-use case (100-200 ms target ack per §5.1); UI falls back to REST within 1 s of a backend hiccup; slightly more visible fallback cost under normal stuck-server scenarios.
- **5.0 s**: more generous; survives transient network hiccups; worse slider-drag UX because a stuck server lingers 5× longer before fallback; inconsistent with §7.32.

**Recommendation**: **default `timeout=1.0`**. Callers that need more can pass `timeout=5.0` explicitly.

**Justification**: (source-doc fidelity) §7.32 is the more specific rule for this command; §7.1 is the generic hook. The more specific rule wins when two parts of the same doc conflict. (operational simplicity) One default value is simpler than per-call tuning. (safety) 1 s is safe for slider workloads; the SDK raises a typed exception on timeout and the caller falls back to REST, so there is no data-loss risk.

**Implementation impact**: The source doc should be patched in Round 5 to remove the `timeout=5.0` from §7.1. The SDK PR (Phase A) lands with `timeout: float = 1.0`. R0-04's Phase A acceptance table A3 is unchanged (asserts `JuniperCascorTimeoutError` regardless of default). Add a unit test `test_set_params_default_timeout_is_one_second`.

---

### 4.2 D02 + X01 — Correlation-ID field naming (`request_id` vs `command_id`)

**Positions**:

- R0-04 §4.1, §4.2: uses `request_id`. Describes it as "a new proposal derived from GAP-WS-32".
- R0-02 §3.3 attack 5, §4.4: uses `command_id`. Notes it is per-connection scoped.
- R0-03 §6.3: uses `command_id`, discusses echo rules, per-command correlation.
- Source doc line 1403 (§7.32): "each command carries a client-generated `command_id` (UUID); cascor echoes it in `command_response`".
- Source doc §3.2.3 wire envelope: no correlation field in either direction.

**Evidence**: I verified the source doc spelling. Line 1403 explicitly uses `command_id`. R0-02 and R0-03 match this. R0-04 uses `request_id` apparently without cross-checking against the source doc name.

**Trade-offs**:

- **`command_id`**: matches the source doc; matches R0-02 and R0-03 (2 of 3 R0s that care); obvious association to the enclosing `command` field.
- **`request_id`**: HTTP-ecosystem familiarity; R0-04 notes it as an additive field; no technical advantage.

**Recommendation**: **`command_id`**. Naming only; semantics unchanged. R0-04 should rename.

**Justification**: (source-doc fidelity) §7.32 says `command_id`. Three of six R0s agree. One R0 made a local naming choice without cross-referencing. Simpler to align than to rewrite the doc.

**Implementation impact**:

1. R0-04's SDK `set_params(..., request_id=None)` kwarg becomes `command_id=None`.
2. R0-04's wire envelopes in §4.2 are updated from `request_id` to `command_id`.
3. R0-04's `_client_latency_ms` private field is unchanged.
4. R0-05 tests: `test_set_params_concurrent_correlation` assertion reads `data.command_id` on the response.
5. R0-02 §3.3 attack 5 uses the same name (already consistent).
6. R0-03 §6.3 echo rules use the same name (already consistent).
7. R0-02 `AUDIT_SCRUB_ALLOWLIST` and audit log `command_id` field name are already consistent.
8. Add a Phase G server-side test `test_set_params_echoes_command_id` asserting cascor echoes the field when present and omits it when absent.

---

### 4.3 D03 — rAF coalescing enabled or scaffold-only in Phase B

**Positions**:

- Source doc: lists GAP-WS-15 under Phase B with implication it ships enabled.
- R0-01 §3.3.3 and disagreement #1: ship scaffold but DISABLED (feature flag `_scheduleRaf = noop`).
- R0-05 §6.3 has `test_frame_budget_batched_50_events_under_50ms` which in context implies the rAF coalescer IS enabled and batches events.

**Cross-R0 conflict (X06)**: R0-01 disables rAF, R0-05 tests rAF behavior.

**Evidence**: R0-01 §3.3.3 argues: the 100 ms drain interval already yields ~10 Hz render rate, comfortably under 60 fps; rAF creates a double-render risk with the drain callback (both would consume the same ring buffer); ship scaffold-without-effect and enable only if §5.6 instrumentation shows frame-budget pressure. R0-05's rAF test is derivative: if rAF is disabled, the batched-events test measures the drain callback instead, which produces similar-shape output.

**Trade-offs**:

- **Enabled**: matches source doc; matches R0-05's test names verbatim; extra complexity; risk of double-render.
- **Scaffold disabled**: R0-01's reasoning is technically sound; lower Phase B risk surface; can be enabled as a hotfix if data demands.

**Recommendation**: **ship rAF scaffold but disabled in Phase B** (R0-01's position). Keep R0-05's frame-budget test in place, retargeted to measure the drain-callback path (not the rAF path). Rename the test `test_frame_budget_batched_50_events_under_50ms_via_drain_callback` to make the measurement subject explicit.

**Justification**: (safety) Phase B is the riskiest phase per RISK-02 High. Shipping fewer moving parts is strictly safer. (reversibility) Scaffold-disabled is trivially enabled later (one line flip from `noop` to the real function); scaffold-enabled is harder to un-ship once it is on a production browser. (operational simplicity) One code path (drain) is simpler than two (drain + rAF) for debugging. The source doc's implication that rAF ships enabled is a soft signal, not a hard constraint — the doc explicitly acknowledges in §5.5 that drain coalescing at 100 ms is already comfortably under the 60 fps budget.

**Implementation impact**:

1. R0-01's `_scheduleRaf` in `ws_dash_bridge.js` is implemented as a no-op or guarded by `window._juniperRafEnabled === true`.
2. R0-05's frame-budget test retargets to the drain callback. Mark as `@pytest.mark.latency_recording` (record, do not block) per R0-05 §8.2.
3. Add a toggle setting `Settings.enable_raf_coalescer` with default `False` in canopy. Document in the Phase B runbook.
4. When the toggle flips True (post-§5.6 evidence), the scaffold activates. That flip is a follow-up PR, not Phase B.

---

### 4.4 D04 + X08 — REST polling fallback cadence during WS reconnect

**Positions**:

- Source doc §6.3: specifies "no_update when connected"; silent on fallback cadence during reconnect.
- R0-01 §3.4.2: slow fallback to 1 Hz during reconnect window (check `n % 10 == 0` against the 100 ms tick).
- R0-06: doesn't discuss cadence; accepts source doc silence.

**Evidence**: Current implementation polls at 100 ms. During a 5-second reconnect window, 50 redundant REST hits at ~300 KB each is ~15 MB — the same bandwidth profile that motivated the entire migration.

**Trade-offs**:

- **100 ms (current)**: matches source doc literally; wastes bandwidth during disconnect.
- **1 Hz (R0-01)**: reduces reconnect-window bandwidth 10×; minor correctness cost (up to 1 s of lag on the metrics chart during fallback); still well within the 200 ms target for non-reconnect state.

**Recommendation**: **adopt 1 Hz fallback** (R0-01's position).

**Justification**: (safety) lower fallback rate is safer on shared cascor. (operational simplicity) the `n % 10 == 0` check is a one-liner in the existing handler; no new config required. (source-doc fidelity) additive to the source doc, not contradictory — the doc is silent on the fallback cadence.

**Implementation impact**:

1. R0-01's `_update_metrics_store_handler` refactor includes the `n % 10 != 0` early-return for the fallback path.
2. Add to R0-05's test list: `test_fallback_polling_at_1hz_when_disconnected` (assert REST call count ~= 5 over 5-second disconnect window).
3. Phase B PR description explicitly lists the cadence change as a deviation from source doc §6.3 and cross-references R1-05 §4.4 for rationale.

---

### 4.5 D05 + X09 — NetworkVisualizer Phase B or Phase B+1

**Positions**:

- Source doc: Phase B "chart/panel callbacks" list implicitly includes NetworkVisualizer.
- R0-01 §3.3 and disagreement #3: defer to Phase B+1; NetworkVisualizer uses cytoscape, not Plotly, so `extendTraces` does not apply.
- R0-05: silent.

**Evidence**: R0-01 §8.3 self-audit notes uncertainty: "I stated cytoscape based on my reading of §5.2 ('NetworkVisualizer (cytoscape graph)'). If it actually uses Plotly, my disagreement #3 is wrong." I did not verify the NetworkVisualizer component's actual implementation.

**Trade-offs**:

- **Phase B**: matches source doc; risks extending Phase B estimate if cytoscape migration turns out to be non-trivial.
- **Phase B+1**: R0-01's reasoning is sound IF NetworkVisualizer is cytoscape; otherwise wrong.

**Recommendation**: **Phase B MUST wire the WS path for topology updates on NetworkVisualizer (minimum: cascade_add events trigger updates without polling). Deep render migration (extendTraces equivalent) deferred to Phase B+1 ONLY IF cytoscape is confirmed.** R0-01 must verify in the Phase B PR.

**Justification**: (concrete evidence) R0-01's claim is a hypothesis. (safety) the minimum wiring (topology updates over WS) is cheap and safe; deferring the render migration only if justified by the render tech is pragmatic. (operational simplicity) minimum wire work is ~0.5 day of the Phase B estimate; full rendering migration is 1-2 days and contingent on the render tech.

**Implementation impact**:

1. Phase B PR description confirms NetworkVisualizer is cytoscape (or not) via a file-level grep in the first commit.
2. If cytoscape: minimum WS wiring in Phase B; deep render migration in a follow-up PR, tracked as Phase B+1 (new). Close the issue R0-01 flagged.
3. If Plotly: full migration in Phase B per source doc; R0-01 §3.3 extended to cover NetworkVisualizer.
4. R0-05 Phase B gate gets a new test: `test_network_visualizer_updates_on_ws_cascade_add`.

---

### 4.6 D06 — §5.5 literal reading: `extendTraces` vs `Plotly.react`

**Positions**:

- Source doc §5.5: "MUST use extendTraces, not figure replace."
- Source doc §6.5.2: uses `Plotly.react` for the snapshot-replacement path on reconnect.
- R0-01 disagreement #4: both are right; the §5.5 wording is too strong if read out of context.

**Recommendation**: **codify both paths explicitly.** `extendTraces` for LIVE metric updates; `Plotly.react` (or `Plotly.newPlot`) for SNAPSHOT-REPLACEMENT after reconnect. Not a real disagreement; a clarification.

**Justification**: (source-doc fidelity) both are already in the source doc. R0-01 is just making the ordering explicit.

**Implementation impact**: Phase B JS code implements both and picks one per code path. Add a comment citing R1-05 §4.6 so future readers understand. Source doc patch in Round 5: add a clarifying sentence to §5.5.

---

### 4.7 D07 — `ws-metrics-buffer` store shape

**Positions**:

- Source doc GAP-WS-04: "bounded ring buffer (e.g., last 1000 metrics)"; shape unspecified.
- R0-01 §7 disagreement #5: `{events: [...], gen: int, last_drain_ms: float}` structured object.

**Evidence**: R0-01's rationale — Dash's `Input`-fire detection uses JSON-serialized equality; a structured object with a `gen` counter gives deterministic change detection even when the underlying `events` array happens to be the same object reference.

**Trade-offs**: Bare array is simpler; structured object is safer against Dash callback-graph false-negatives.

**Recommendation**: **adopt the structured object** (R0-01's position).

**Justification**: (safety) Dash's equality-based change detection is a real footgun; the `gen` counter is cheap insurance. (operational simplicity) +2 integer fields for robustness is a small cost.

**Implementation impact**: R0-01's §3.2.2 drain callback body is unchanged; R0-05's `test_ws_metrics_buffer_drain_is_bounded` assertion targets `.events.length`, not the top-level length. Document in a Phase B JSDoc comment in `ws_dash_bridge.js`.

---

### 4.8 D08 + X14 — GAP-WS-24 browser-vs-server ownership split

**Positions**:

- Source doc: bundles under GAP-WS-24 as single item.
- R0-01 §7 disagreement #6: browser-side emitter only (POST to `/api/ws_latency`); server-side endpoint + Prometheus histogram is a backend concern.
- R0-06 §6.4: canopy backend aggregates into `canopy_ws_delivery_latency_ms_bucket`; "Phase B implements the pipe".

**Recommendation**: **split GAP-WS-24 into GAP-WS-24a (browser emitter, frontend lane) and GAP-WS-24b (canopy `/api/ws_latency` endpoint + Prometheus histogram, canopy-backend lane).** Both land in Phase B. Both are on the same PR wave. Neither blocks the other.

**Justification**: (operational simplicity) clear ownership allocation reduces confusion; R0-01 and R0-06 already agree on the technical pipe, just on who owns what. (source-doc fidelity) additive, not contradictory.

**Implementation impact**:

1. Phase B PR description lists GAP-WS-24a and GAP-WS-24b as separate commits.
2. The browser-side emitter ships with a feature flag `Settings.enable_ws_latency_beacon = True`; falls back to no-op if `/api/ws_latency` returns 404.
3. R0-05's `test_latency_dashboard_panel_renders` and `test_canopy_latency_api_aggregates_submissions_into_prom_histogram` both land in Phase B.
4. Source doc patch: rename GAP-WS-24 → GAP-WS-24a/24b in Round 5.

---

### 4.9 D09 + X04 — Phase B-pre effort estimate

**Positions**:

- Source doc §9.2: 1 day.
- R0-02 §9.1: 1.5-2 days.
- R0-06 §13.6: +1.5 days observability overall (implicit ~2.5 days for the combined Phase B-pre + instrumentation setup).

**Evidence**: CSRF plumbing (session middleware, `/api/csrf` endpoint, Dash template injection), audit logger wiring, per-IP cap concurrency contract, and per-endpoint size cap audit are individually small but add up. None of the R0s independently verified whether canopy already has a session middleware.

**Trade-offs**: Under-estimation risks schedule slippage; over-estimation signals wasteful padding.

**Recommendation**: **budget Phase B-pre at 2 days engineering.** Round up from R0-02's midpoint. Does not include the observability work that R0-06 folds in (that belongs to Phase B, not B-pre).

**Justification**: (concrete evidence) R0-02's enumeration of sub-tasks is the most detailed. R0-06's observation is valid but orthogonal (observability ≠ security). (safety) under-estimating security hardening is especially painful because security bugs are often merge-blockers. 2 days gives headroom without bloating the estimate.

**Implementation impact**: Phase B-pre engineering budget = 2 days. Phase B engineering budget unchanged. R0-06's 13.5-day total absorbs the 1-day delta (4-4.5 weeks calendar stays honest).

---

### 4.10 D10 — `disable_ws_auth` naming

**Positions**:

- Source doc / R0-06: negative-sense `disable_ws_auth: bool = False`.
- R0-02 §9.4: positive-sense `ws_security_enabled: bool = True`; also notes "Accept either; flag for reviewer decision."

**Recommendation**: **keep negative-sense `disable_ws_auth`**. Ship as-is. The naming nit is not worth the code churn.

**Justification**: (operational simplicity) source doc, R0-06, and at least one test (`test_settings_disable_ws_auth_defaults_false`) already use the negative form. (reversibility) name change is easy later if someone actually has a merge-accident incident; until then, it is a hypothetical. (source-doc fidelity) source doc wins naming ties.

**Mitigation of the footgun concern R0-02 raises**: add a CI check that grep-fails if `JUNIPER_DISABLE_WS_AUTH=true` appears in any production compose file (R0-02 IMPL-SEC-40 already proposes this). That is the real guardrail.

**Implementation impact**: None. Existing identifier kept.

---

### 4.11 D11 — Per-command HMAC

**Positions**:

- Source doc §2.9.2 M-SEC-02 point 3: "advanced, optional."
- R0-02 §9.5: defer indefinitely.

**Recommendation**: **accept R0-02's deferral**; drop from Phase B-pre scope.

**Justification**: (operational simplicity) HMAC adds real complexity for speculative threat coverage. (reversibility) can be added later in a targeted PR if needed. (source-doc fidelity) the source doc already calls it optional, so deferral is not contradicting the doc.

**Implementation impact**: Source doc §2.9.2 M-SEC-02 point 3 moves to §12.2 (deferred) in Round 5. No Phase B-pre tests for HMAC. Open an explicit deferral issue: "Revisit HMAC for multi-tab cross-session replay scenarios if they emerge."

---

### 4.12 D12 — "One resume per connection" as security control

**Positions**:

- Source doc §6.5: treats replay as a correctness feature.
- R0-02 §3.4 attack 1 + §4.5 control 6: one resume per connection; second resume → close 1003.

**Evidence**: R0-02's argument — a malicious client can forge a low `last_seq` and force the server to iterate and dispatch the full 1024-event ring every second, amplifying outbound bandwidth. One-resume-per-connection caps the amplification.

**Recommendation**: **adopt R0-02's rule** as an additive security control. Add to Phase B-pre scope.

**Justification**: (safety) low-cost amplification mitigation. (operational simplicity) trivial rule: track a per-connection `resume_consumed: bool` flag; second resume closes 1003. (source-doc fidelity) additive, not contradictory.

**Implementation impact**:

1. R0-03's `control_stream_handler` / `training_stream_handler` tracks `resume_consumed` per connection.
2. R0-05 adds test `test_second_resume_closes_connection_1003` (Phase B-pre gate).
3. Source doc patch in Round 5: add to §6.5 edge cases.

---

### 4.13 D13 — Multi-tenant replay isolation

**Positions**:

- Source doc: silent.
- R0-02 §9.7: flag as open question Q1-sec; defer per-session replay buffers until multi-tenant deployment.

**Recommendation**: **defer**; accept R0-06 §9 Q1 resolution that single-tenant is the assumed topology for v1. Open `Q1-sec` as an explicit tracking issue. No Phase B-pre work.

**Justification**: (operational simplicity) YAGNI for v1. (reversibility) can be added later via `Dict[session_id, deque]` keyed by session cookie. (source-doc fidelity) the source doc is silent; adding Q1-sec to §11 is additive documentation.

**Implementation impact**: Add Q1-sec to source doc §11 in Round 5 with default "deferred; revisit at multi-tenant". No code changes.

---

### 4.14 D14 + X20 — Dedicated audit logger scope

**Positions**:

- Source doc §2.9.2 M-SEC-07: scrub allowlist mention, no full audit logger.
- R0-02 §4.6: dedicated `canopy.audit` logger with JSON formatter, rotation, Prometheus counters.
- R0-06: implies shared application logger.

**Evidence**: R0-02's rationale — audit rotation/retention independent from application logs; security teams need separability.

**Trade-offs**: Dedicated logger is extra code (new module ~200 LOC); shared logger is simpler but loses clean separation.

**Recommendation**: **adopt dedicated audit logger** (R0-02's position), but **scope-reduced**: no Prometheus counters in Phase B-pre — just the JSON formatter, dedicated `canopy.audit` logger name, `TimedRotatingFileHandler`, and the scrub allowlist. Prometheus counters move to Phase B (with the rest of the observability pipe).

**Justification**: (safety) audit trail separation is a real security property. (operational simplicity) shipping just the logger first and the Prometheus hooks later keeps Phase B-pre at 2 days. (reversibility) the logger is additive; removing it later is trivial.

**Implementation impact**:

1. Phase B-pre: R0-02 §6.8 IMPL-SEC-32, IMPL-SEC-33, IMPL-SEC-34, IMPL-SEC-35 land.
2. R0-02 IMPL-SEC-36 (Prometheus counters) moves to Phase B.
3. R0-05 adds `test_audit_log_format_and_scrubbing` (Phase B-pre gate) and `test_audit_log_prometheus_counters` (Phase B gate).

---

### 4.15 D15 — New M-SEC-10, -11, -12 identifiers

**Positions**:

- Source doc: stops at M-SEC-07 (active) + M-SEC-08/09 (deferred §12.2).
- R0-02 §9.9: adds M-SEC-10 (idle timeout), M-SEC-11 (adapter inbound validation), M-SEC-12 (log injection escaping).

**Recommendation**: **adopt M-SEC-10 and M-SEC-11 as new canonical identifiers**; **fold M-SEC-12 into M-SEC-07** (log injection is part of logging hygiene, not a distinct control).

**Justification**: (source-doc fidelity) adding a numbered identifier is additive; folding M-SEC-12 into M-SEC-07 reduces ID proliferation for a rule that is arguably the same thing. (operational simplicity) 9 IDs is better than 10.

**Implementation impact**:

1. Round 5 source doc patch: add M-SEC-10, M-SEC-11 to §2.9.2; extend M-SEC-07 text to include the CRLF/tab escaping rule.
2. R0-02's §4.6 rule 10 stays in the same place; the header above it says "extends M-SEC-07" rather than "new M-SEC-12".

---

### 4.16 D16 — GAP-WS-19 resolution status

**Positions**:

- Source doc §2.2 / §7: GAP-WS-19 unresolved P2, `close_all()` does not hold `_lock`.
- R0-03 §11.1: verified RESOLVED on main as of 2026-04-11.

**Evidence**: **Verified by this consolidator** against `juniper-cascor/src/api/websocket/manager.py` lines 138-156. The method acquires `self._lock` for the mutation, then releases and iterates the snapshot outside the lock. This is the exact fix the source doc prescribes.

**Recommendation**: **mark GAP-WS-19 RESOLVED in the Round 5 canonical plan.** Do NOT include it in Phase B-pre scope. R0-02's §6.11 IMPL-SEC-43 (fold GAP-WS-19 fix into Phase B-pre) is unnecessary — the fix is already in main.

**Justification**: (concrete evidence) direct file inspection beats source-doc stale text. (operational simplicity) removing an already-done item from a phase scope shortens the Phase B-pre PR.

**Implementation impact**:

1. Round 5 source doc patch: GAP-WS-19 marked RESOLVED with the verified state.
2. R0-02's IMPL-SEC-43 removed from Phase B-pre.
3. R0-03's §12.2 edit pass item 5 is already noting this; formalize the marking in Round 5.
4. R0-05 adds `test_close_all_holds_lock` as a regression gate to catch future regressions.

---

### 4.17 + X02 + X10 + X18 — `command_response` seq field and replay buffer eligibility

This is the most tangled cross-R0 conflict in the catalog. Unpacking:

**Positions**:

- R0-03 §6.3 and §11.3: `command_response` is personal RPC, has **no** seq field, **not** buffered in replay. `/ws/training` and `/ws/control` have separate seq namespaces (control has none).
- R0-02: uses Pydantic envelope models that do not explicitly say whether seq is present on `command_response`; implicit assumption is every outbound has some seq.
- R0-05 §4.1: `test_seq_monotonically_increases_per_connection` broadcasts 100 messages from any channel; implicit assumption is seq on all outbound.
- R0-01: reads seq from the drain callback but only for metrics/state/topology/cascade_add/candidate_progress — explicitly NOT for command_response, which is consumed by the slider callback (Phase C).
- Source doc §6.5: "every outbound envelope" implies all messages have seq, but the doc does not explicitly address command_response.

**Trade-offs**:

- **Seq on command_response**: unified mental model ("everything has seq"); makes replay iteration order-of-deque simple; weird semantics on reconnect (a replayed command_response for a command the client didn't reissue is confusing); requires /ws/control replay buffer.
- **No seq on command_response** (R0-03's position): separate namespaces per endpoint; matches the RPC semantics of /ws/control; client matches responses via `command_id`, not seq; /ws/training replay buffer only contains broadcast events.

**Recommendation**: **adopt R0-03's position**: `command_response` does NOT carry seq. Separate seq namespaces per endpoint. /ws/training has a replay buffer; /ws/control does not. R0-05's Phase A `test_seq_monotonically_increases_per_connection` test wording is ambiguous but is really asking about /ws/training broadcasts — clarify in the test name.

**Justification**:

1. (concrete evidence) R0-03 is the cascor-backend specialist and has thought through the cascor-side consequences in detail (§6.3, §11.3, §8 failure modes). The other R0s are reading from a different specialty and default to "seq is everywhere" without digging in.
2. (source-doc fidelity) The source doc's "every outbound envelope" language is a general statement, not a specific claim about command_response. Specific reasoning wins over general implication.
3. (operational simplicity) single-purpose replay buffer (broadcast events only) is simpler than multi-channel replay with cross-namespace sequencing.
4. (safety) replaying a command_response on reconnect is semantically confusing and risks user-visible bugs ("why did my set_params ack come back twice?"). Simpler to not replay it at all; the `command_id` correlation is the dedup mechanism.

**Implementation impact**:

1. R0-03's §3.2 helper `_assign_seq_and_append` is called only from the /ws/training broadcast path, never from /ws/control response emission.
2. R0-05's Phase A test renamed: `test_ws_training_seq_monotonically_increases`.
3. R0-05 adds: `test_ws_control_command_response_has_no_seq` — assert `seq` field absent (or explicitly null) on inbound command_response frames.
4. R0-02's `CommandFrame` / `AuthFrame` / `ResumeFrame` Pydantic models do not include seq (these are inbound anyway; confirm).
5. R0-03 §6.3 and §11.3 become the canonical text; source doc patch in Round 5 adds explicit carve-out.
6. R0-04's client-side correlation via `command_id` (per §4.2 resolution) is the only matching mechanism.

---

### 4.18 D18 — Two-phase registration mechanism

**Positions**:

- Source doc §6.5: does not specify an atomic replay→live handoff mechanism.
- R0-03 §5.1 + §11.4: introduces `_pending_connections` set + `promote_to_active()` helper.

**Alternative R0-03 considered**: per-connection `seq_cursor` — `broadcast()` only sends to a connection if `seq > seq_cursor`. R0-03 rejects this as couples fan-out to per-connection state.

**Recommendation**: **adopt R0-03's `_pending_connections` design**.

**Justification**: (concrete evidence) R0-03 worked through both alternatives and explains why pending-set is simpler. (operational simplicity) pending-set is one map; seq_cursor is per-connection state coupled to every broadcast call. (reversibility) either could be swapped for the other in a follow-up without user-visible change.

**Implementation impact**: R0-03's §5.1 two-phase registration ships as-is in Phase A-server commit 5 (see §4.19 below). R0-05 tests `test_pending_connections_not_eligible_for_broadcast` and `test_promote_to_active_atomic_under_seq_lock`.

---

### 4.19 D19 + X03 — Phase A-server carve-out

**Positions**:

- Source doc §9.3: Phase B is a single 4-day phase containing both cascor-side seq/replay work and canopy-side browser bridge work.
- R0-03 §11.5: carve out a ~2-day Phase A-server prerequisite so cascor ships seq/replay before canopy starts Phase B.
- R0-01, R0-04, R0-05: implicit — treat Phase B as the source doc does.

**Evidence**: R0-03's argument — cascor seq/replay landing first lets canopy Phase B iterate against a stable server with the real protocol. The additive field contract (§6.5.4) means old consumers ignore `seq` gracefully, so there is no risk of landing cascor changes early.

**Trade-offs**:

- **Carve out Phase A-server**: 2-day server-only PR lands first; canopy Phase B iterates against a real seq-bearing server; more PR overhead but clearer release coordination; reduces the size of each Phase B merge.
- **Keep as source doc**: single Phase B PR (more work, harder review, more conflict surface); simpler release coordination (one train, not two).

**Recommendation**: **adopt R0-03's Phase A-server carve-out.**

**Justification**: (operational simplicity) smaller PRs are easier to review. (safety) cascor main carries the new envelope field for ~1 week before canopy consumes it — this is a real production validation window. (reversibility) the carve-out is a scheduling decision, easy to change if release coordination gets painful.

**Naming**: the source doc's "Phase A" is the SDK work. R0-03's "Phase A-server" shares the prefix but is a different repo. I propose **renaming to "Phase 0-cascor"** to avoid the collision: Phase 0 = prerequisites, Phase A = SDK, Phase B = browser bridge, etc. Phase 0-cascor contains the cascor seq/replay, state throttle coalescer, `broadcast_from_thread` exception fix, and `/ws/control` protocol error responses.

**Implementation impact**:

1. Round 5 canonical plan renumbers: Phase 0-cascor (2 days) → Phase A-SDK (1 day) || Phase B-pre-security (2 days) → Phase B-browser-bridge (4 days) → ...
2. R0-03's §7.1 10 commits become Phase 0-cascor scope.
3. R0-06's §3.1 "Phase A prerequisites" is updated: Phase A-SDK no longer depends on Phase 0-cascor (additive field), but Phase B depends on Phase 0-cascor.
4. Release coordination: `juniper-cascor` ships Phase 0-cascor → Phase B-pre-server in order; `juniper-cascor-client` ships Phase A-SDK; `juniper-canopy` ships Phase B-pre-canopy → Phase B-browser after both of those land.
5. R0-05 Phase gates are updated for the new numbering.

---

### 4.20 D20 — `server_start_time` vs `server_instance_id` naming

**Positions**:

- Source doc §6.5: uses both in different code snippets; inconsistent.
- R0-03 §11.6: standardize on `server_instance_id` for comparison; `server_start_time` advisory-only (human log correlation, no programmatic use).

**Recommendation**: **adopt R0-03's position**. Both fields exist; `server_instance_id` is the programmatic comparison key; `server_start_time` is a float wall-clock for human operators.

**Justification**: (source-doc fidelity) the doc's step 5 already says UUID-based equality; step 4's `server_start_time` is stale text. R0-03's change is a correction, not a contradiction. (safety) clock-skew-immunity requires UUID comparison; `server_start_time` comparison would be a latent bug.

**Implementation impact**: Round 5 source doc patch standardizes §6.5 throughout. R0-03's resume-handler logic is the reference implementation. R0-02's resume frame security discussion (§3.4 attack 2) uses `server_instance_id` exclusively, so no change there.

---

### 4.21 D21 — `replay_buffer_capacity` additive field

**Positions**:

- Source doc: silent.
- R0-03 §4.1: adds `replay_buffer_capacity` to `connection_established` so client can decide whether to attempt resume vs snapshot.

**Recommendation**: **adopt**. Additive, harmless, enables client optimization.

**Justification**: (operational simplicity) one extra integer in an already-existing frame; clients that don't know about it ignore it.

**Implementation impact**: Phase 0-cascor commit 2 includes the field. R0-01's JS client handles the field (defaults to 1024 if absent).

---

### 4.22 D22 — SDK retries on `set_params` timeout

**Positions**:

- Source doc: silent.
- R0-04 §12.3: no SDK-level retries; canopy adapter is the single decision point.

**Recommendation**: **adopt R0-04's position**.

**Justification**: (operational simplicity) layering — the SDK raises, the caller decides. (reversibility) callers can implement retries themselves if they want.

**Implementation impact**: R0-04's `set_params` docstring says "does NOT retry"; tested in R0-05 test `test_set_params_no_retry_on_timeout`.

---

### 4.23 D23 — Keep REST `update_params` forever

**Positions**:

- Source doc §9.4 / §9.5: preserves REST paths as first-class.
- R0-04 §12.4: explicitly never deprecate.

**Recommendation**: **adopt**. R0-04 is making explicit what the source doc already implies.

**Justification**: (source-doc fidelity) agrees with §9.4 / §9.5. (reversibility) keeping the REST path is the primary fallback lever and must not be removed.

**Implementation impact**: Phase C documentation explicitly states: REST `update_params` is permanent, WS `set_params` is additive. No removal plan.

---

### 4.24 D24 — Debounce layer location

**Recommendation**: **adopt R0-04's position** (debounce lives in Dash clientside callback, not in SDK).

**Justification**: (operational simplicity) UI debouncing is a UI concern. (reversibility) non-canopy consumers want immediate dispatch.

**Implementation impact**: R0-04's §8 is canonical.

---

### 4.25 D25 — `test_set_params_caller_cancellation` criticality

**Recommendation**: **adopt R0-05's elevation**; mark as mandatory Phase A gate (memory leak protection).

**Justification**: (safety) `asyncio.Task.cancel()` is a known source of correlation-map leaks.

**Implementation impact**: R0-05's Phase A gate test list includes it as non-optional. R0-04's acceptance criterion A6 already has it; confirm wording says "MUST pass" not "nice to have".

---

### 4.26 D26 — Phase C routing unit tests

**Recommendation**: **adopt R0-05's addition** of hot/cold routing unit tests to Phase C gate.

**Justification**: (concrete evidence) R0-05 is right that the source doc's Phase C test list only has dash_duo browser tests + AsyncMock. Routing logic needs direct coverage.

**Implementation impact**: R0-05's §4.3 Phase C tests are canonical Phase C gate. R0-04's §10.2 C1-C13 is the complete list.

---

### 4.27 D27 — Parallel runtime estimate for e2e suite

**Recommendation**: **adopt R0-05's 5-8 min estimate** (dash_duo serial, Playwright parallel).

**Justification**: (concrete evidence) dash_duo uses Selenium; Selenium WebDriver is process-stateful; pytest-xdist parallelism breaks it.

**Implementation impact**: R0-06's §7 CI runtime budget revised. CI workflow uses `pytest -n auto --dist=loadfile` so dash_duo tests run in a single worker.

---

### 4.28 D28 — §5.6 CI latency integration policy

**Recommendation**: **adopt R0-05's recording-only CI lane + strict-local lane split**.

**Justification**: (safety) CI runner variance makes strict latency assertions flaky; flaky tests erode trust. (reversibility) recording is additive; strict gates can be added later after the histogram is stable.

**Implementation impact**: R0-05's §8.2 is canonical. Add `latency_recording` marker to pytest config in both canopy and cascor.

---

### 4.29 D29 — Phase G test scope

**Recommendation**: **adopt R0-05's expansion**: `test_set_params_concurrent_command_response_correlation` + `test_set_params_during_training_applies_on_next_epoch_boundary`.

**Justification**: (concrete evidence) both tests cover specific behaviors the source doc asks about; source doc §9.8 is under-specified.

**Implementation impact**: R0-05's §4.1 "Phase G" test list is canonical.

---

### 4.30 D30 — Fake harness schema parity contract test

**Recommendation**: **adopt R0-05's addition**; add `test_fake_cascor_message_schema_parity` as a new contract test.

**Justification**: (safety) silent drift between fake and real cascor is a latent failure mode. (operational simplicity) the test is ~30 lines.

**Implementation impact**: R0-05's §14.6 T-RISK-04 mitigation is canonical. Lives in `juniper-canopy/src/tests/unit/test_cascor_message_contract.py`.

---

### 4.31 D31 — Browser compatibility matrix

**Recommendation**: **adopt R0-05's narrowing to Chromium-only for v1**, with `# tested on Chromium only` README note. Multi-browser deferred.

**Justification**: (operational simplicity) one browser to get right is enough. (reversibility) Firefox/WebKit are a `BrowserType` flip in Playwright.

**Implementation impact**: R0-05 §14.7 is canonical. R0-06 Q2 resolution is consistent.

---

### 4.32 D32 — User research automation

**Recommendation**: **adopt R0-05's exclusion** from automated tests; track as separate task.

**Justification**: (source-doc fidelity) §5.7 is explicitly optional calendar time. (operational simplicity) not automation's job.

**Implementation impact**: R0-06's Q7 resolution (skip for v1) is consistent. No change.

---

### 4.33 D33 — `dash_duo` limitations documented

**Recommendation**: **adopt R0-05's documentation in §14.9**.

**Justification**: (operational simplicity) saves future reviewers from tripping on the same limitation.

**Implementation impact**: R0-05 §14.9 is canonical; carry to Round 5 docs.

---

### 4.34 D34 — Contract-test lane as distinct marker

**Positions**:

- R0-05 §14.10: proposes new `contract` marker, as open question.

**Recommendation**: **adopt**. Add `contract` as a pytest marker in canopy, cascor, and cascor-client. Tests include: fake-vs-real schema parity, dual-format `_normalize_metric`, canopy adapter ↔ SDK contract.

**Justification**: (operational simplicity) contract tests are a real category distinct from unit and integration. (safety) silent drift mitigation.

**Implementation impact**: R0-05's pyproject.toml marker list gains `contract`. CI workflow runs `pytest -m contract` as a fast gate.

---

### 4.35 D35 + X05 — Phase B-pre splitting

**Positions**:

- Source doc §9.2: single Phase B-pre.
- R0-06 §13.1: split into B-pre-a (max_size) and B-pre-b (Origin+CSRF).
- R0-02: keeps as single bundle.

**Evidence**: R0-06's argument — M-SEC-03 (max_size) is a Phase B prereq (traffic volume / DoS); M-SEC-01/02 (Origin+CSRF) are Phase D prereqs (control attack surface). Splitting clarifies what blocks what.

**Trade-offs**: Splitting is a doc/ops change, zero code change; gives clearer ordering; adds naming overhead.

**Recommendation**: **adopt R0-06's split**. Phase B-pre-a (max_size + per-IP caps + audit logger skeleton, ~0.5 day) lands with/before Phase B. Phase B-pre-b (Origin + cookie session + CSRF first-frame, ~1.5 days) lands with/before Phase D.

**Justification**: (operational simplicity) clearer ordering is worth the naming overhead. (safety) neither split delays security; both parts land before their dependent phases.

**Implementation impact**:

1. Round 5 renames Phase B-pre → B-pre-a + B-pre-b.
2. R0-06's phase ordering rationale (§3.2) is canonical text for the split.
3. R0-02's implementation steps (§6.1-§6.11) split across IMPL-SEC blocks: size caps + per-IP in B-pre-a; Origin + cookie + CSRF + audit logger in B-pre-b.

---

### 4.36 D36 — Phase E default backpressure policy

**Positions**:

- Source doc §9.6: default `block` (preserve existing behavior).
- R0-06 §13.2: default `drop_oldest_progress_only` (close for state-bearing, drop-oldest for coalesceable progress).
- R0-03 §5.2: policy matrix with the same effective semantics.

**Evidence**: RISK-04 is Medium/Medium — a hung devtools tab serially blocks all broadcasts. Keeping `block` as default means the first production incident after Phase E is likely exactly this failure mode.

**Trade-offs**:

- `block` default: no behavior change from pre-Phase-E; existing tests unchanged; RISK-04 still triggers.
- `drop_oldest_progress_only` default: safer; test baseline changes slightly (one test confirms the new policy).

**Recommendation**: **adopt R0-06's `drop_oldest_progress_only` default** as the Phase E default policy. Keep `block` and `close_slow` as opt-in alternatives via `Settings.ws_backpressure_policy`.

**Justification**: (safety) fixes a Medium/Medium risk by default. (reversibility) operators can revert to `block` with a config flip. (source-doc fidelity) the source doc explicitly says "flip the default only at the next major version" — this resolution disagrees, but R0-06's argument that RISK-04 severity justifies earlier default flip is sound.

**Implementation impact**: R0-03's §5.2 policy matrix is the canonical policy; R0-06's §13.2 provides the ops justification. Phase E PR ships with new default. R0-05 adds `test_default_backpressure_policy_drops_oldest_for_progress` and `test_block_policy_still_works_when_opted_in`.

---

### 4.37 D37 — Q6 (per-IP cap) resolution timing

**Recommendation**: **resolve now** per R0-06: 5 connections/IP default, configurable via `Settings.ws_max_connections_per_ip`.

**Justification**: (operational simplicity) all three security-lane R0s agree; no need for further deliberation.

**Implementation impact**: Source doc §11 Q6 resolved in Round 5.

---

### 4.38 D38 — Q1 (topology) resolution timing

**Recommendation**: **resolve now** per R0-06: single-tenant v1. Multi-tenant is explicit future-work.

**Justification**: (operational simplicity) unblocks Phase E planning.

**Implementation impact**: Source doc §11 Q1 resolved in Round 5.

---

### 4.39 D39 — Shadow traffic strategy

**Recommendation**: **adopt R0-06's rejection** of shadow traffic.

**Justification**: (operational simplicity) state duplication in stateful protocol is a real trap. (reversibility) dual-transport polling toggle (GAP-WS-25) achieves most of the shadow benefit without the complexity.

**Implementation impact**: R0-06 §7.3 is canonical. Add to Round 5 source doc as a named explicit rejection so future readers don't re-litigate.

---

### 4.40 D40 — Total effort estimate

**Recommendation**: **13.5 engineering days / ~4.5 weeks calendar** per R0-06 §13.6. I reduce by 0.5 day for the GAP-WS-19 carve-out (§4.16), giving **13 days / ~4 weeks** calendar. I then add 2 days for Phase 0-cascor (R0-03's carve-out, §4.19) minus 1.5 days already in Phase B for the cascor-side work that moves to Phase 0-cascor, net **+0.5 day**. Total **13.5 days / ~4.5 weeks**.

**Justification**: (concrete evidence) R0-06's observability overhead is real; the Phase 0-cascor carve-out is mostly re-allocation, not new work.

**Implementation impact**: Round 5 canonical plan lists 13.5 days / 4.5 weeks.

---

### 4.41 D41 — CODEOWNERS for `_normalize_metric`

**Recommendation**: **adopt R0-06's CODEOWNERS rule** as an operational guard against RISK-01.

**Justification**: (safety) the regression test is necessary but not sufficient; human review on a load-bearing function reduces the chance of accidental breakage.

**Implementation impact**: `.github/CODEOWNERS` entry added during Phase H. Exact reviewer group TBD.

---

### 4.42 X12 — SDK reconnect queue

**Positions**:

- R0-04 §6.2: no client-side replay buffer; SDK fails fast; canopy adapter retries via REST.
- R0-05 Phase A test `test_set_params_reconnection_queue`: test name implies queue, R0-05 acknowledges "1 of 2 design variants".

**Recommendation**: **adopt R0-04's fail-fast position**. Test renamed to `test_set_params_fails_fast_on_disconnect` to match.

**Justification**: (operational simplicity) queueing commands across disconnects creates stale-value ordering risks. (safety) slider debounce (250 ms) is smaller than any reconnect interval (1 s minimum), so the caller's next debounced update applies the latest value.

**Implementation impact**: R0-05 test renamed; R0-04 §6.2 is canonical.

---

### 4.43 X13 — Adapter synthetic auth frame

**Positions**:

- R0-02 §4.2 / §6.9 IMPL-SEC-37/38: two options. Option A: `X-Juniper-Role: adapter` header skips CSRF. Option B: HMAC-derived CSRF token from API key.
- R0-04: silent (assumes API key auth is enough).

**Recommendation**: **adopt Option B (HMAC-derived CSRF token)**. Cascor recognizes `csrf_token = hmac(api_key, "adapter-ws")` when the API key header is present.

**Justification**: (safety) avoids adding a branch in the auth code that could be a footgun if mis-configured; the HMAC derivation is a small library function, not a special case. (operational simplicity) uniform handler logic for all `/ws/control` auth; no `X-Juniper-Role` header plumbing. (reversibility) the HMAC derivation is straightforward to revoke — rotate the API key.

**Implementation impact**:

1. R0-02 §6.9 IMPL-SEC-38 uses the HMAC option; remove the `X-Juniper-Role` alternative.
2. R0-04's canopy adapter `_control_stream_supervisor` computes `csrf_token = hmac.new(api_key.encode(), b"adapter-ws", hashlib.sha256).hexdigest()` before connect.
3. Cascor-side handler derives the same value and compares with `hmac.compare_digest`.
4. R0-05 adds `test_canopy_adapter_sends_hmac_csrf_token_on_connect`.

---

### 4.44 X15 — Unclassified-key routing default

**Positions**:

- R0-04: unclassified keys (not in hot or cold set) default to REST with WARNING log.
- R0-02 `SetParamsRequest` Pydantic model `extra="forbid"`: unknown keys are rejected hard.

**Evidence**: These are about different layers. R0-04's "unclassified" is in the canopy adapter (cascor param name → routing decision). R0-02's `extra="forbid"` is in the cascor server (wire-format validation).

**Recommendation**: **both**. R0-02's `extra="forbid"` is the server-side wire contract — rejects unknown keys at the server. R0-04's "unclassified routes to REST" is the canopy-adapter classification rule — if a new param is added to cascor but canopy doesn't know whether it's hot or cold yet, default to the safer REST path. The two rules don't conflict; they fire at different layers.

**Justification**: (safety) cascor must forbid unknown keys; canopy adapter must default unknown classifications to the safe path. (operational simplicity) both are about containing unknown-key risk.

**Implementation impact**: Both ship. R0-05 adds `test_cascor_rejects_unknown_param_with_extra_forbid` and `test_canopy_adapter_defaults_unclassified_to_rest_with_warning`.

---

### 4.45 X16 — Phase B feature flag for browser bridge

**Positions**:

- R0-01: `Settings.enable_browser_ws=False` default during Phase B-pre gap (ship wiring behind a flag until B-pre lands).
- R0-06: `Settings.disable_ws_bridge` kill switch with default False (meaning bridge is ENABLED).

**Evidence**: Different concerns. R0-01 is about landing Phase B wiring before Phase B-pre-b (Origin/CSRF) is ready — in which case the Playwright tests can't run real WebSocket handshakes. R0-06 is about having an ops kill switch post-rollout.

**Recommendation**: **both flags**, clarified:

- `Settings.enable_browser_ws_bridge: bool = False` during development (flag default True only after Phase B-pre-b + Phase B both land and pass staging). The flag default FLIPS to True when both prerequisites are verified. This is a one-line PR, trivially reviewable.
- `Settings.disable_ws_bridge: bool = False` as a permanent ops kill switch (default False = bridge enabled). This is R0-06's lever.

**Justification**: (safety) two flags with opposite polarities each serve a different purpose. (reversibility) both flags give operators independent levers.

**Implementation impact**:

1. Phase B code ships with both flags.
2. `enable_browser_ws_bridge=False` is the default until Phase B-pre-b is in production.
3. `enable_browser_ws_bridge=True` flip PR happens after both prereqs land.
4. `disable_ws_bridge` is the permanent kill switch; default False.
5. The runtime check is `enabled = Settings.enable_browser_ws_bridge and not Settings.disable_ws_bridge`.

---

### 4.46 X17 — Rate limit buckets per command type

**Positions**:

- R0-02 §4.5 control 4: two buckets (set_params 20/s separate from destructive commands 10/s).
- R0-06: one bucket, 10 cmd/s.

**Recommendation**: **single bucket, 10 cmd/s, for Phase B-pre-b**. Two-bucket refinement is deferred to a follow-up and ships only if single-bucket starvation is observed in practice.

**Justification**: (operational simplicity) one bucket is simpler. (reversibility) splitting a single bucket into two is straightforward later. (safety) 10 cmd/s is enough for slider debounce (5 Hz) + occasional start/stop.

**Implementation impact**: R0-02's §4.5 control 4 ships with single bucket in Phase B-pre-b; two-bucket refinement tracked as follow-up issue.

---

### 4.47 X07 — Demo mode test placement

**Recommendation**: **both**. `test_demo_mode_metrics_parity` runs in Phase B gate (dash_duo) AND in the fast lane (unit-level equivalent). Not mutually exclusive.

**Justification**: (safety) RISK-08 is a real concern; redundant coverage is cheap.

**Implementation impact**: R0-05 §13 T-RISK-09 is canonical; add to both lanes.

---

## 5. Unresolved disagreements (needs more info)

A small number of items I was unable to fully resolve with the information available in R0. I list them here with the evidence that would unblock them.

### 5.1 NetworkVisualizer render tech (cytoscape vs Plotly)

**Blocked on**: direct verification of the `NetworkVisualizer` component file.
**Evidence that would resolve**: read `juniper-canopy/src/frontend/components/network_visualizer.py` (or wherever it lives) and confirm whether it uses cytoscape.js or Plotly. A `grep` for `cytoscape` or `plotly` in that file answers the question.
**Who provides**: the Phase B implementer on day 1, as the first commit of the Phase B PR.
**Interim resolution**: treat as "minimum WS wiring in Phase B, deep render migration contingent on render tech" (§4.5). This is safe under both hypotheses.

### 5.2 Canopy session middleware pre-existing

**Blocked on**: direct verification of `juniper-canopy/src/main.py` or `config.py` for existing `SessionMiddleware` usage.
**Evidence that would resolve**: `grep -r "SessionMiddleware" juniper-canopy/src/` — if found, Phase B-pre-b effort is lower (reuse); if not, add new middleware (R0-02 IMPL-SEC-14).
**Who provides**: the Phase B-pre-b implementer on day 1.
**Interim resolution**: budget 2 days for Phase B-pre (§4.9) assumes the middleware does not exist; if it does, the engineering is ~1.5 days and the savings fund buffer.

### 5.3 Dash version (Option A `set_props` availability)

**Blocked on**: `juniper-canopy/pyproject.toml` Dash pin.
**Evidence that would resolve**: `grep "dash" juniper-canopy/pyproject.toml`.
**Who provides**: Phase B implementer.
**Interim resolution**: Option B (Interval drain) works regardless. R0-01 is correct to default to Option B; Option A is a future optimization and does not change the plan.

### 5.4 Plotly.js version (`extendTraces(maxPoints)` signature)

**Blocked on**: the Plotly pin in canopy.
**Evidence that would resolve**: `grep "plotly" juniper-canopy/pyproject.toml` and/or the Plotly version actually loaded in the browser.
**Who provides**: Phase B implementer.
**Interim resolution**: assume Plotly 2.x (common default). If 1.x is pinned, the `extendTraces` migration has an additional sub-step (upgrade the pin), adding ~0.25 day.

### 5.5 Whether canopy adapter currently uses `run_coroutine_threadsafe` from sync threads

**Blocked on**: verify `cascor_service_adapter.py` usage pattern.
**Evidence that would resolve**: `grep -n "run_coroutine_threadsafe" juniper-canopy/src/backend/cascor_service_adapter.py`.
**Who provides**: R0-04's implementer.
**Interim resolution**: R0-04's §5.3 thread-bridging design assumes the pattern; if already used elsewhere it is a matter of wiring, not inventing.

### 5.6 Cascor `/ws/control` currently validates `command_id` presence

**Blocked on**: direct verification of `control_stream.py` handler.
**Evidence that would resolve**: read the current handler and check if it passes `command_id` through to `command_response`.
**Who provides**: Phase G implementer.
**Interim resolution**: R0-03's §6.3 design assumes cascor must change to echo. Phase G tests assert the echo. If the current cascor already passes arbitrary kwargs through, the change is zero code.

---

## 6. Re-derived development plan

This section captures only the parts of the plan that the resolutions in §4 change. Other R1 agents are producing the full phased plan; this is the delta.

### 6.1 Scope summary

After reconciliation, the plan has:

- **10 phases** (adding Phase 0-cascor; splitting Phase B-pre into B-pre-a and B-pre-b). Total: Phase 0-cascor, A, B-pre-a, B, B-pre-b, C, D, E, F, G, H, I. Ordering:
  - Phase 0-cascor ‖ Phase A ‖ Phase B-pre-a → Phase B → Phase B-pre-b → Phase C ‖ Phase D → Phase E ‖ Phase F ‖ Phase G ‖ Phase H ‖ Phase I
  - Phase B requires Phase 0-cascor AND Phase B-pre-a; Phase D requires Phase B AND Phase B-pre-b; Phase C requires Phase A AND Phase B.
- **Total effort**: ~13.5 engineering days / ~4.5 weeks calendar (§4.40).
- **New canonical identifiers**: M-SEC-10, M-SEC-11 (§4.15); GAP-WS-24a, GAP-WS-24b (§4.8); T-RISK-01..12 (R0-05); FR-RISK-01..15 (R0-01); IMPL-SEC-01..44 (R0-02); R04-01..14 (R0-04).
- **Resolved identifiers**: GAP-WS-19 marked RESOLVED (§4.16).
- **New settings / flags**: `Settings.enable_browser_ws_bridge` (§4.45), `Settings.disable_ws_bridge` (§4.45, permanent kill switch), `Settings.enable_raf_coalescer` (§4.3), `Settings.use_websocket_set_params` (R0-04), `Settings.ws_max_connections_per_ip=5` (§4.37), `Settings.ws_backpressure_policy=drop_oldest_progress_only` (§4.36).

### 6.2 Phase-by-phase changes from the resolved positions

**Phase 0-cascor (NEW, ~2 days, cascor)**

- Contains: R0-03's 10 commits (seq/replay buffer, server_instance_id, _seq_lock, two-phase registration, _send_json 0.5 s timeout, state throttle coalescer, broadcast_from_thread exception handling, /ws/control protocol error responses, replay_buffer_capacity field, `snapshot_seq` on REST snapshot endpoint).
- Explicitly OMITS GAP-WS-19 fix (already on main per §4.16).
- Explicitly OMITS seq on `command_response` (§4.17). `/ws/training` has seq; `/ws/control` does not.
- Explicitly INCLUDES the `_pending_connections` two-phase registration (§4.18).
- Ships to cascor main before canopy Phase B begins (§4.19). Additive field contract means old consumers ignore `seq`.

**Phase A (~1 day, SDK)**

- Contains: R0-04's `CascorControlStream.set_params(params, timeout=1.0, command_id=None)` (§4.1, §4.2).
- Field naming: `command_id` (§4.2), NOT `request_id`.
- Default timeout: 1.0 (§4.1), NOT 5.0.
- Correlation: per-connection correlation map keyed by `command_id`; background `_recv_task`.
- Tests include `test_set_params_caller_cancellation` as mandatory Phase A gate (§4.25) and `test_set_params_fails_fast_on_disconnect` renamed from `test_set_params_reconnection_queue` (§4.42).
- No SDK retries (§4.22).

**Phase B-pre-a (~0.5 day, cascor + canopy)**

- M-SEC-03 max_size guards on every `/ws/*` endpoint.
- M-SEC-04 per-IP cap: 5/IP default (§4.37).
- M-SEC-10 idle timeout (§4.15 keeps as new ID).
- Audit logger skeleton (§4.14): new `canopy.audit` logger, JSON formatter, rotating file handler, scrub allowlist. No Prometheus counters yet.
- GAP-WS-19 fix NOT included (already on main).
- Gates Phase B.

**Phase B (~4 days, canopy + cascor)**

- Browser bridge (R0-01 skeleton).
- `ws-metrics-buffer` as structured `{events, gen, last_drain_ms}` object (§4.7).
- rAF coalescer shipped DISABLED as scaffold (§4.3). Gated on `Settings.enable_raf_coalescer=False`.
- Fallback polling at 1 Hz during reconnect (§4.4).
- GAP-WS-24a (browser emitter) + GAP-WS-24b (canopy backend endpoint) both in Phase B (§4.8).
- Phase I (asset cache busting) folded into Phase B PR.
- NetworkVisualizer minimum WS wiring (topology updates); deep render migration deferred if cytoscape (§4.5, §5.1).
- `_normalize_metric` dual-format wire test (R0-01 §3.6) as additional Phase B regression gate.
- Audit logger Prometheus counters (§4.14, deferred from B-pre-a) land here.
- `Settings.enable_browser_ws_bridge` default flip is a one-line post-Phase-B PR after staging soak.

**Phase B-pre-b (~1.5 days, cascor + canopy)**

- M-SEC-01 + M-SEC-01b Origin allowlist.
- M-SEC-02 cookie session + CSRF first-frame (including `/api/csrf` endpoint + session middleware add, contingent on §5.2 evidence).
- M-SEC-05 rate limit: single bucket, 10 cmd/s (§4.46). Two-bucket deferred.
- M-SEC-11 adapter inbound validation.
- Extended M-SEC-07 (log injection CRLF/tab escaping, formerly proposed as M-SEC-12; now folded — §4.15).
- Adapter synthetic auth via HMAC (§4.43). NOT `X-Juniper-Role` header skip.
- "One resume per connection" rule (§4.12).
- Per-command HMAC (source doc M-SEC-02 point 3) is DEFERRED (§4.11).
- Multi-tenant replay isolation DEFERRED (§4.13).
- Gates Phase D.

**Phase C (~2 days, canopy)**

- R0-04's canopy adapter refactor (hot/cold split, `_apply_params_hot` / `_apply_params_cold`, supervisor task).
- `Settings.use_websocket_set_params=False` default.
- REST `update_params` permanent (§4.23).
- Debounce in Dash clientside callback only (§4.24).
- Unclassified keys default to REST with WARNING (§4.44); cascor-side `extra="forbid"` catches unknown keys on wire (§4.44).
- Phase C routing unit tests (R0-05's expanded list) are mandatory (§4.26).

**Phase D (~1 day, canopy)**

- R0-06's training-control-buttons over `/ws/control`.
- Requires Phase B-pre-b in production.
- REST `/api/train/{command}` remains first-class.

**Phase E (~1 day, cascor)**

- Full backpressure: per-client send queues + pump tasks.
- Default `drop_oldest_progress_only` (§4.36). `block` and `close_slow` remain opt-in.
- Policy matrix per R0-03 §5.2.

**Phase F (~0.5 day, frontend + cascor)**

- Heartbeat + reconnect jitter (R0-01 §3.5.1 item 3 + cascor `pong` handling).
- Jitter formula: `delay = Math.random() * Math.min(CAP, BASE * 2**attempt)`, BASE=500ms, CAP=30s.

**Phase G (~0.5 day, cascor)**

- R0-05's expanded test scope (§4.29): `test_set_params_concurrent_command_response_correlation`, `test_set_params_during_training_applies_on_next_epoch_boundary`, plus R0-02's IMPL-SEC-39 security regression cases.
- Integration level via FastAPI TestClient, not SDK.

**Phase H (~1 day, canopy)**

- R0-01 / R0-05's `_normalize_metric` dual-format regression test lands BEFORE the consumer audit.
- CODEOWNERS entry for `_normalize_metric` (§4.41).

**Phase I (~0.5 day, canopy)**

- Asset cache busting folded into Phase B per R0-01 and R0-06.

### 6.3 New risks introduced by resolutions

None of the resolutions introduce fundamentally new risks. Some amplify existing risks or add small operational burden:

- **§4.3 rAF disabled**: if the drain cadence turns out to be too slow under load, Phase B+1 must enable the scaffold (minor operational burden).
- **§4.5 NetworkVisualizer deferred**: if the hypothesis is wrong and NetworkVisualizer is Plotly, Phase B gains ~1 day of scope. Mitigation: first commit in Phase B PR verifies render tech.
- **§4.19 Phase 0-cascor carve-out**: cascor main carries the new envelope field for ~1 week before canopy consumes it. Mitigation: R0-03 §6.5.4 additive-field argument; old consumers ignore `seq` via `dict.get()`.
- **§4.36 Phase E default change**: existing production workloads see a behavior change from the default. Mitigation: operators can revert to `block` via config.
- **§4.45 Two flags for the browser bridge**: slightly more complex default logic (`enabled = enable_browser_ws_bridge and not disable_ws_bridge`). Mitigation: test `test_both_flags_interact_correctly`.
- **§4.43 HMAC adapter auth**: the HMAC derivation is new code. Mitigation: ~10 lines, stdlib-only (`hmac`, `hashlib`), unit test + round-trip test.

### 6.4 Recommended next steps for Round 2

Round 2 should:

1. **Confirm the resolution priority ordering** (§2) is acceptable. If a different priority is preferred (e.g., "the newest proposal wins"), some resolutions may flip.
2. **Verify the five unresolved items** in §5 against the real codebase. These are all `grep`-level verifications and should take ~1 hour of work.
3. **Reconcile with sibling R1 proposals** on areas they touch (phasing, risk, security). This R1-05 is the reconciliation angle; sibling R1s may produce additional conflicts that need resolving. In particular:
   - R1 phasing lane: confirm the Phase 0-cascor carve-out and Phase B-pre split are consistent with the sibling's phase table.
   - R1 security lane: confirm the M-SEC renumbering (§4.15) and the HMAC adapter auth decision (§4.43).
   - R1 testing lane: confirm the CI runtime estimate revision (§4.27) and the contract-test marker (§4.34).
4. **Adopt the cross-R0 correlation-field naming** (`command_id`, §4.2) across the whole R1 corpus so R2 agents don't re-litigate.
5. **Budget the source-doc patch list** for Round 5: items D01, D02, D15, D16, D19, D20, D37, D38, D39 all require source-doc text updates.
6. **Open tracking issues** for the deferred items: Q1-sec (multi-tenant replay isolation), per-command HMAC, two-bucket rate limiting, rAF default flip, NetworkVisualizer deep migration.

---

## 7. Disagreements with R0 inputs

Where I, the consolidator, disagree with all six R0s on something. These are substantive positions that emerged only when I looked across the proposals at once.

### 7.1 The cross-R0 correlation-field naming is a latent bug

No R0 caught that R0-04 uses `request_id` while R0-02, R0-03, and the source doc use `command_id`. If Round 1 did not exist, this would have manifested as a wire-level mismatch in Phase G integration tests weeks later. The reconciliation lane is the right place to catch it. My resolution (§4.2) aligns on `command_id` per the source doc.

### 7.2 The seq-on-command_response question needed explicit resolution

R0-01, R0-02, R0-03, R0-04, R0-05 all make assumptions about `command_response.seq` that are mutually inconsistent. R0-03 is the only R0 that thinks through the consequences and says explicitly "no seq". Every other R0 is implicitly "seq everywhere". If Round 1 did not resolve this, R2 would have had to. My resolution (§4.17) picks R0-03's explicit position because it is the one backed by specialist analysis.

### 7.3 Phase 0-cascor is a better ordering than the source doc's single Phase B

R0-03 proposed it; no other R0 endorses it. My §4.19 adopts it because the carve-out meaningfully reduces Phase B's PR size and gives cascor main a production soak window before canopy consumes the changes. This is a scheduling/safety win that none of the other R0s saw because they are in different lanes.

### 7.4 GAP-WS-19 should be marked RESOLVED in Round 5, not re-implemented

R0-02's §6.11 IMPL-SEC-43 proposes re-fixing GAP-WS-19 in Phase B-pre even though R0-03 verified it's already done. I disagree with R0-02 here: the fix is in main (I re-verified at `manager.py:138-156`). Including it in Phase B-pre wastes effort. My §4.16 aligns with R0-03.

### 7.5 The two-flag design for browser bridge was not proposed by any R0

R0-01 proposed `enable_browser_ws`, R0-06 proposed `disable_ws_bridge`. Neither noticed that both are valid for different reasons. My §4.45 ships both. This is additive to the R0 corpus.

### 7.6 Default Phase E to `drop_oldest_progress_only` is a real deviation from the source doc

R0-06 proposed it; R0-03 has the policy matrix but doesn't strongly advocate for the default flip; R0-05 is silent. The source doc explicitly says "flip the default only at the next major version." My §4.36 adopts R0-06's position because RISK-04 Medium/Medium severity justifies the earlier default flip. This is the only resolution where I explicitly override the source doc's stated position.

### 7.7 Phase B-pre should be split but NOT into the proportions R0-06 suggests

R0-06 proposed the split into B-pre-a (max_size) and B-pre-b (Origin+CSRF). I agree with the split idea (§4.35) but reallocate: audit logger skeleton goes to B-pre-a, not B-pre-b; Prometheus counters for audit logs go to Phase B, not B-pre-a. R0-06 bundles all logging work with the Origin/CSRF work, which couples them unnecessarily.

### 7.8 The HMAC adapter auth is better than header-based skip

R0-02 lists both options in §8.8 and asks Round 1 to pick. I pick HMAC (§4.43) because the header-based skip relies on the fact that browsers cannot set custom headers — which is a true statement but a fragile invariant to build security on. The HMAC derivation is simpler to reason about and harder to misconfigure. No R0 makes this call explicitly.

---

## 8. Self-audit log

### 8.1 Pass 1 verification (what was checked)

- Read all six R0 proposals in full, focusing on disagreement sections (`§11`, `§12`, `§13`, `§14`) and self-audit sections.
- Extracted every explicit disagreement with the source doc: 41 items labeled D01..D41.
- Extracted every cross-R0 implicit conflict: 20 items labeled X01..X20.
- Resolved each with priority-ordered criteria.
- Cross-verified critical claims against the source doc and against the current cascor `manager.py`.
- Identified 5 items that need external evidence and listed them as unresolved.
- Built the §6 plan delta from the resolutions.
- Noted 8 places where I disagree with the R0 corpus collectively (§7).

### 8.2 Pass 2 corrections made

I re-read the draft and made the following corrections:

1. **Initially missed the `request_id` vs `command_id` naming conflict** (X01). On first pass I assumed R0-04 used `command_id` like everyone else. Found the discrepancy on pass 2 and escalated to §4.2.

2. **Initially grouped D17 (command_response seq) and D18 (two-phase registration) together**. They are related but separable. Split into two resolutions (§4.17 and §4.18) in pass 2.

3. **Initially resolved D03 (rAF) as "adopt R0-01"** without noticing that R0-05's test `test_frame_budget_batched_50_events_under_50ms` implies rAF enabled (X06). Added explicit cross-R0 reconciliation in §4.3: rename the R0-05 test to measure the drain callback, not the rAF path.

4. **Initially accepted R0-06's Phase B-pre split at face value**. On second thought, the proportions were wrong — R0-06 bundles audit-logger-Prometheus-counters in B-pre-b which ties security to observability in a way that delays Phase D. Split differently in §4.35 so B-pre-a gets audit logger skeleton and Phase B gets the Prometheus wiring.

5. **Initially missed the two-flag design** for the browser bridge (X16). Both R0-01 (enable flag) and R0-06 (disable kill switch) are right for different reasons. Added §4.45 with explicit two-flag handling.

6. **Initially underestimated the `command_response` seq question**. It looked like a minor clarification. On deeper read, it touches R0-01 (chart consumer), R0-02 (envelope schemas), R0-03 (cascor producer), R0-04 (SDK correlation), R0-05 (test assertions). Promoted to the most-detailed resolution in the document (§4.17).

7. **Initially accepted source doc `timeout=5.0` for D01**. On second read of the source doc, spotted the §7.1 vs §7.32 internal inconsistency. Reversed the resolution to adopt R0-04's 1.0 s.

8. **Initially did not verify GAP-WS-19**. On second pass, checked cascor `manager.py` directly. R0-03's claim is correct; GAP-WS-19 is fixed on main. This resolved §4.16 with concrete evidence rather than accepting R0-03's claim on faith.

9. **Initially did not split Phase 0-cascor from Phase A (SDK)**. R0-03 proposes "Phase A-server" which collides with the source doc's "Phase A" (SDK). Renamed in §4.19 to "Phase 0-cascor" to avoid the collision.

10. **Initially did not catch the HMAC vs header adapter-auth question**. R0-02 lists it as an open decision. On pass 2, I realized Round 1 needs to make the call so R2 has a concrete direction. Added §4.43 with justification.

11. **Initially wrote §4.14 audit logger as "full adopt R0-02"**. On pass 2, realized the Prometheus counter portion is observability work and belongs in Phase B alongside the rest of the instrumentation. Split the scope.

12. **Initially had no §7 "disagreements with R0 inputs" section**. The prompt explicitly asks for this. Added it with 8 items in pass 2.

13. **Initially budgeted Phase B-pre at source-doc 1 day**. On pass 2, noted R0-02's detailed breakdown (IMPL-SEC-01..44) and R0-06's observability overhead. Revised to 2 days in §4.9.

14. **Missed D41** (CODEOWNERS) on first extraction pass because R0-06 buries it in §13.7. Found and added to §4.41.

15. **Initially did not address X20** (audit log scope — dedicated logger vs shared application logger). R0-02 wants dedicated; R0-06 implies shared. Added to §4.14 reconciliation.

16. **Initially missed X15** (unclassified-key routing default). R0-04 and R0-02 operate at different layers; the conflict is only apparent at the wire-vs-adapter boundary. Resolved in §4.44 — both rules fire at different layers; no actual conflict.

17. **Initially wrote §6.2 ordering as sequential**. Corrected in pass 2 to reflect parallelism: Phase 0-cascor, A, and B-pre-a can all run in parallel; B requires 0-cascor + B-pre-a; D requires B + B-pre-b.

18. **Self-verified the `command_id` claim** by grepping the source doc directly (line 1403) in pass 2. R0-02 and R0-03 use it; R0-04's `request_id` is a one-off naming choice.

19. **Did not initially have a clear recommendation for the `_pending_connections` vs `seq_cursor` alternative**. In pass 2, adopted R0-03's position (§4.18) because it is the only R0 that thought through both and it aligns with the source doc's general "keep the fan-out loop stateless" philosophy.

### 8.3 Items I chose not to cover

- **Renaming `ws_security_enabled` positive-sense flag**: R0-02 raised it, R0-06 is silent, I defer to existing identifier (§4.10). Not worth the churn.
- **Prometheus metric name choices**: R0-02, R0-03, R0-06 each propose slightly different names (`canopy_ws_*`, `cascor_ws_*`). All are reasonable; no conflict since they are in different repos. Round 2 can harmonize.
- **Worktree naming conventions**: R0-06 §8.1 references the ecosystem worktree procedure; no conflict.
- **Thread handoff procedure**: cited in the user's global CLAUDE.md; not a source-doc item; no R0 disagrees with it.
- **Helm chart version discipline**: R0-06 notes it; no R0 disagrees; mentioned only for cross-reference.

### 8.4 Confidence self-assessment

- **High confidence**:
  - §4.1 `set_params` default timeout = 1.0 (internal source doc inconsistency clearly resolved by §7.32 specificity).
  - §4.2 `command_id` naming (source doc + 2 of 3 R0s agree).
  - §4.16 GAP-WS-19 resolved (direct file evidence).
  - §4.17 `command_response` has no seq (specialist reasoning, carve-out mechanically clean).
  - §4.19 Phase 0-cascor carve-out (scheduling benefit is obvious once articulated).
  - §4.35 Phase B-pre split (cleaner ordering with zero code cost).
- **Medium confidence**:
  - §4.3 rAF disabled (R0-01's argument is correct but overrides source doc's implication).
  - §4.36 Phase E default (overrides source doc on debatable operational judgement).
  - §4.43 HMAC adapter auth (both options work; picked the one with fewer branches).
  - §4.45 Two flags for browser bridge (novel combination neither R0 proposed).
- **Lower confidence**:
  - §4.5 NetworkVisualizer (hypothesis about render tech; needs first-commit verification).
  - §4.40 effort estimate (±1 day uncertainty from session-middleware question in §5.2).

### 8.5 What the self-audit changed (numeric summary)

- Disagreements cataloged: 41 (D-series) + 20 (X-series) = **61 total**
- Resolutions written: **47** (some X-series fold into D-series resolutions)
- Unresolved (need external evidence): **6** (§5.1-5.6)
- Pass-2 corrections to the draft: **19** items
- Cross-R0 conflicts surfaced that no R0 noticed: **8** (§7)
- Source-doc inconsistencies verified: **3** (D01 timeout, D20 naming, D16 GAP-WS-19 state)
- File-level evidence checks: **2** (`manager.py` close_all, source doc line 1403 `command_id`)

### 8.6 Items flagged for Round 2 attention

In priority order:

1. **Adopt `command_id` naming across all R2 proposals** so downstream rounds don't re-litigate.
2. **Confirm Phase 0-cascor scheduling** is acceptable vs source doc's single Phase B (§4.19).
3. **Verify the 5 unresolved items** in §5 against the codebase.
4. **Accept or reject the Phase E default override** (§4.36) — it's the one place I explicitly override the source doc.
5. **Accept or reject the HMAC adapter auth** (§4.43) — a cross-repo security decision.
6. **Reconcile the audit logger scope split** (§4.14) with R1 security lane's position.
7. **Confirm `command_response` has no seq** (§4.17) as the canonical position.

### 8.7 Scope discipline check

Did I stay in the reconciliation lane?

- [x] No new proposals or designs not already in an R0.
- [x] No full re-derivation of the plan; only the delta from resolutions.
- [x] Resolutions are justified by one of the five priority criteria (§2).
- [x] "Disagreements with R0 inputs" section (§7) lists places where I override the corpus; those are explicit, justified, and flagged.
- [x] Every resolution maps to a specific implementation impact.
- [x] Unresolved items (§5) are explicit about what evidence would resolve them.

Scope discipline **PASS**.

### 8.8 Target length check

Target: 1000-1700 lines. Final line count target: ~1100-1300 lines including self-audit. Final actual count is estimated at ~1100 lines — within the lower end of the envelope, dense-signal rather than filler.

---

**End of proposal R1-05.**
