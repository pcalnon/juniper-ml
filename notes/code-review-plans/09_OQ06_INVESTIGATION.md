# Open Question #6 — Defined-but-unused Prometheus metrics

**Question**: Of the ~29 metrics declared but never emitted across the
ecosystem, do we (A) wire every one, (B) delete the declarations and
ship "HTTP + build only", or (C) keep them and emit a startup warning?

**Source**: `00_ECOSYSTEM_ROADMAP.md` §5.9 + §9 question 6
**Investigation date**: 2026-04-24
**Companion data**: `08_METRIC_CATALOG.md`

---

## 1. Recommendation

**Hybrid: Option A′ — "wire what's wirable now, delete what's vapor,
defer what needs design."**

Concretely, partition the 26 unused cascor + canopy metrics into three
buckets:

| Bucket | Action | Count |
|--------|--------|-------|
| **Wire-now** (release-blocker) | Implement emission this cycle | **20 metrics (~10 hr engineering)** |
| **Defer-with-ticket** | Existing-feature-but-needs-design; file backlog ticket; do NOT advertise the metric on dashboards yet | **3 metrics** |
| **Delete-now** | Declarations reference a feature that does not exist; keeping them misleads operators | **3 metrics** |

This is the only honest answer the evidence supports. Pure Option A
costs ~60 hours of cascor engineering for two metrics whose emission
sites do not exist (inference endpoint never shipped). Pure Option B
destroys 20 metrics whose wire-up is genuinely trivial. Option C is
unhelpful — operators would still see empty dashboards plus a noisy
warning.

---

## 2. Evidence

### 2.1 juniper-cascor — 23 metrics, partitioned

Source: parallel investigation agent on
`/home/pcalnon/Development/python/Juniper/juniper-cascor/`.

**Wire-now (17 metrics, ~8 hr)**:

Trivial (≤30 min each):

- `juniper_cascor_training_sessions_active` — call site exists at `lifecycle/manager.py:549, :562`
- `cascor_ws_seq_current` — `websocket/manager.py:286` (`_assign_seq_and_buffer`)
- `cascor_ws_replay_buffer_occupancy` — same site
- `cascor_ws_replay_buffer_capacity_configured` — `websocket/manager.py:100` (`__init__`)
- `cascor_ws_resume_replayed_events` — `websocket/training_stream.py:195` (after replay)
- `cascor_ws_broadcast_timeout_total` — `websocket/manager.py:378` (existing TimeoutError block)
- `cascor_ws_broadcast_from_thread_errors_total` — `websocket/manager.py:358` (exception handler)
- `cascor_ws_command_handler_seconds` — `websocket/control_stream.py:257–267` (existing wait_for wrap)

Small (≤2 hr each):

- `juniper_cascor_training_epochs_total` — needs forwarding from `cascade_correlation.py:1674+`
- `juniper_cascor_training_loss` — same loop, line 1620+
- `juniper_cascor_candidate_correlation` — same loop, line 1674+
- `cascor_ws_resume_requests_total` — `training_stream.py:176` (`_handle_resume` branches)
- `cascor_ws_replay_buffer_bytes` — needs new helper + `sys.getsizeof(deque)`
- `cascor_ws_broadcast_send_duration_seconds` — needs timing wrapper around `_send_json`
- `cascor_ws_pending_connections` — needs inc/dec pair (`connect_pending` + `promote_to_active`)
- `cascor_ws_seq_gap_detected_total` — needs gap-detection logic in `replay_since`
- `cascor_ws_connections_active` — call from `connect`/`disconnect` (4 sites)

**Defer-with-ticket (3 metrics)**:

- `juniper_cascor_training_accuracy_ratio` (M) — accuracy is not currently exposed to the `fit()` callback; widening the callback interface is a Medium-effort change that may have ripple effects on cascor-client/canopy contract. File ticket; do NOT block release.
- `juniper_cascor_hidden_units_total` (M) — requires observer on `add_hidden_unit`; touches the cascade core. Same: defer.
- `cascor_ws_state_throttle_coalesced_total` (M) — the throttle mechanism the metric counts does not yet exist. Designing throttle is its own decision (separate from observability).

**Delete-now (2 metrics)**:

- `juniper_cascor_inference_requests_total`
- `juniper_cascor_inference_duration_seconds`

Both reference an inference HTTP endpoint that **does not exist** in
juniper-cascor. Wiring them would mean shipping a new HTTP feature
this release just to populate a metric. Keeping the declarations is
worse than deleting — operators see them in `/metrics` and assume
inference is supported. Delete now; if inference ships later, redeclare
the metrics in the same PR.

### 2.2 juniper-canopy — 3 metrics, all wire-now

Source: parallel investigation agent on
`/home/pcalnon/Development/python/Juniper/juniper-canopy/`.

| Metric | Site | Effort | Note |
|--------|------|--------|------|
| `juniper_canopy_websocket_connections_active{channel}` | `websocket_manager.py:256` (connect) + `:317` (disconnect) | T | 2 LOC |
| `juniper_canopy_websocket_messages_total{channel, type}` | `websocket_manager.py:392` (broadcast loop) | T | 1 LOC + 5-min decision on channel-inference (parse `client_id` prefix vs new ctor param) |
| `juniper_canopy_demo_mode_active` | `main.py:2231` (start) + `:2275` (stop) | T | 2 LOC |

Total: **~30–45 min for all three.** Zero blockers.

### 2.3 juniper-data — already counted in plan 01 H1/H14

The 3 unused juniper-data metrics (`record_dataset_generation` ×2 +
`set_datasets_cached`) are already covered by plan 01's H1 + H14.
Recommendation: **wire-now**. The natural emission sites already
exist:

- `record_dataset_generation()` — call from `datasets.py:107` (POST handler, after `.generate()` returns) and `datasets.py:98` (cache-hit branch)
- `set_datasets_cached()` — call from `DatasetStore.create()` and `.delete()` (or compute lazily on `/metrics` scrape via `gauge.set_function()` — preferred to avoid drift)

Effort: ~1 hr.

---

## 3. Why not pure A, B, or C?

**Pure Option A** (wire all):

- Cascor agent estimate: **~60 hours**, including 5 metrics with hard blockers.
- 2 of those blockers (`inference_*`) require shipping a feature that isn't planned for this release.
- 3 require Medium design work that isn't observability work — it's training-loop refactoring or throttle-mechanism design.
- Net effect: this release would couple "metrics & monitoring review" to "ship 3 unrelated features." Wrong scope.

**Pure Option B** (delete all 26):

- Throws away 20 metrics with trivial wire-up.
- Loses design intent baked into the declarations (the WebSocket Phase-0
  metrics in particular reflect deliberate choices about replay-buffer
  observability that are valuable).
- Forces re-derivation later when someone re-implements emission.

**Pure Option C** (keep + warn):

- Operator-hostile: the `/metrics` endpoint still returns nothing for
  these, but startup logs gain noise.
- No remediation; just disclosure.
- Strictly worse than the hybrid.

**Hybrid** removes the bad-faith metrics (inference, which lies),
ships the wireable ones (the bulk), and is honest about what's
deferred (3 training metrics behind a backlog ticket).

---

## 4. Risks and guardrails

### 4.1 Risks

| Risk | Mitigation |
|------|------------|
| Wire-up changes hot-path performance (training loop emit) | Benchmark before/after; Prometheus client emits are O(1) in practice; risk Low |
| Channel-inference choice in canopy WS broadcast (param vs prefix-parse) made under time pressure → wrong abstraction | Document decision; revisit in next minor release if it bites |
| Helper signatures that need adding to observability.py introduce drift | Add helpers in same PR as the call-site change; both reviewed together |
| Deleting 2 inference metrics breaks an external dashboard someone built | Run `grep -r juniper_cascor_inference` against any infra repo before deleting; warn in CHANGELOG |
| Training-metric backlog tickets get forgotten | File against the next-release milestone; mention in roadmap §9 follow-up |

### 4.2 Guardrails (must accompany this work)

1. **Cardinality test** — the `cascor_ws_*{type, command, outcome}`
   labels need bounded enumeration. Add a test that scrapes `/metrics`
   after a synthetic load and asserts the number of distinct label
   combinations stays within a documented budget.
2. **Emission test** — for every wired metric, an integration test
   that:
   - drives the relevant code path
   - scrapes `/metrics`
   - asserts the metric value moved
   This is the "test actually checks the metric, not just `200 OK`"
   gate from roadmap §6.1.
3. **CHANGELOG entries** — under `### Added` for the wired metrics and
   `### Removed` for the 2 inference metrics.
4. **Backlog tickets** — three filed against the cascor repo for the
   deferred metrics, each linking back to this memo.

---

## 5. Implementation sequencing

Recommended PR sequence (each ≤200 LOC):

1. **PR 1 — juniper-data wire-up** (~1 hr): hook `record_dataset_generation` + `set_datasets_cached` into the dataset POST and cache flow. Resolves H1 + H14.
2. **PR 2 — juniper-canopy wire-up** (~45 min): all 3 canopy metrics. Channel-inference: pass channel as constructor arg (cleaner than parsing).
3. **PR 3 — cascor WS Phase-0 wire-up — trivials** (~3 hr): the 8 trivial WS metrics (no helper changes). Lowest risk.
4. **PR 4 — cascor WS Phase-0 wire-up — small** (~5 hr): the 6 small-effort WS metrics (4 require new helpers in observability.py).
5. **PR 5 — cascor training metrics wire-up — small** (~3 hr): training_sessions_active, training_loss, training_epochs_total, candidate_correlation. Touch points in `cascade_correlation.py` are localized.
6. **PR 6 — cascor inference deletions** (~30 min): remove the 2 inference metric declarations from observability.py + tests. CHANGELOG `### Removed`.
7. **PR 7 — observability tests** (~3 hr): add the cardinality + emission tests across all 3 services per §4.2.
8. **PR 8 — backlog tickets** (no code, just GitHub issues): file 3 cascor tickets for `training_accuracy_ratio`, `hidden_units_total`, `state_throttle_coalesced_total`.

Total: ~16 hours of engineering time spread across 7 PRs (8 if backlog
counts). Sequence respects dependency: PR 4 introduces helpers PR 3
might also use, so PR 3 first means PR 4 just adds helpers without
touching call sites already wired.

---

## 6. Plan-update implications

If this recommendation is accepted, the affected per-app plans need
small updates to mark hypotheses as having a chosen remediation path:

- **Plan 01** — H1, H14: mark "Remediation: wire-now (PR 1)"
- **Plan 03** — H19: split into H19a (wire-now, 17 metrics, 4 PRs) +
  H19b (defer-with-ticket, 3 metrics) + H19c (delete, 2 metrics)
- **Plan 06** — H20: mark "Remediation: wire-now (PR 2)"
- **Roadmap §5.9**: add a paragraph "Decision (2026-04-24): Hybrid
  Option A′ per `09_OQ06_INVESTIGATION.md`"
- **Roadmap §9 question 6**: mark answered, link to this memo

---

## 7. Open follow-up questions surfaced by this investigation

1. **Inference endpoint roadmap** — is shipping a juniper-cascor inference HTTP endpoint actually planned? If so, the 2 deleted metrics reappear in that work. If not, why are they declared? (Possible: vestigial from an earlier design; worth a quick git-blame investigation when the deletion PR lands.)
2. **Training-callback interface widening** — the deferred `training_accuracy_ratio` blocker is an instance of a broader gap (the `fit()` callback exposes loss but not accuracy). Worth a small design memo for the next release.
3. **State-throttle mechanism** — does the project actually want a throttle on state broadcasts? If yes, that's a design conversation independent of the metric. If no, delete the metric instead of deferring.

These do not block accepting the hybrid recommendation; they are
inputs for the next planning cycle.
