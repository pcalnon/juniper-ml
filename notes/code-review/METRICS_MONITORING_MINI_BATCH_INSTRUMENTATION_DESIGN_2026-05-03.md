# METRICS-MON Mini-Batch Training Instrumentation — Design

<!-- markdownlint-disable MD013 -->

**Project:** Juniper ML
**File Name:** `notes/code-review/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md`
**Description:** Planning-level design for a future METRICS-MON sub-track that closes the per-epoch vs per-step granularity gap surfaced during R5.4-pre. Surveys options, recommends an approach, and proposes sub-track sequencing. Implementation is out of scope; this document is the bridge between R5.4 (per-epoch SLI 3.4) and the eventual per-step instrumentation work.
**Author:** Paul Calnon
**Version:** v1.0.0
**License:** MIT
**Date:** 2026-05-03
**Status:** 🟡 Design — open for review.
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md)
**Companion:** [`METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`](METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md), R5.4-pre (juniper-cascor#188), R5.1 SLO catalog (juniper-deploy#48 — cross-repo).

---

## 1. Purpose & motivation

R5.4-pre (juniper-cascor#188, merged 2026-05-02) introduced the histogram
`juniper_cascor_training_step_duration_seconds{phase}` to satisfy SLO 3.4
("Cascor train-step p95") in the R5.1 SLO catalog. During implementation the
agent of record discovered that the cascor api-lifecycle layer
(`src/api/lifecycle/manager.py`) only sees per-epoch callbacks: there is no
per-mini-batch hook the lifecycle layer can subscribe to. The histogram
therefore measures **per-epoch wall-clock**, not per-step wall-clock.

The R5.1 SLO catalog is being patched in parallel (juniper-deploy fixup branch
`metrics-mon/r5-1-fixup-sli-3-4-rename`) to rename SLI 3.4 to **"Cascor
train-epoch p95"**. That patch acknowledges the granularity gap and defers the
true per-step fix to a future METRICS-MON sub-track. **This document is the
planning artifact for that future sub-track.** Implementation will land in a
later PR after this document is reviewed and accepted.

The motivation for closing the gap, even though the renamed per-epoch SLI is
operationally usable, is threefold:

- **Per-epoch granularity is too coarse to detect intra-epoch slowdowns.** A
  single mini-batch experiencing a GC pause, GPU thermal throttle, or memory
  thrash gets averaged into the surrounding epoch and only surfaces if it
  drags the whole epoch's wall-clock above the p95 SLO threshold. By that
  point the regression is already a multi-batch event.
- **Future SLIs require true per-step granularity.** Step-throughput
  (steps/second), intra-epoch step-duration variance, and per-step
  gradient-norm tracking are all signals that R5.x might define and that
  cannot be derived from a per-epoch metric. Some of these are SLO-bearing;
  others are research signals that the cascor + canopy stack would benefit
  from independent of any external SLO.
- **Why now (timing).** R5.4 ships burn-rate alerts against the per-epoch
  catalog. Those alerts are calibrated to per-epoch p95 thresholds. Once
  per-step instrumentation lands, the alerts can be tightened to true SLO
  targets without re-calibrating against a moving granularity. Doing the
  per-step work after R5.4 closes also avoids invalidating the alerts
  mid-flight (see §6, dependency analysis).

---

## 2. Current state

### 2.1 Where the per-epoch callback fires today

The per-epoch boundary lives at the **trainer → lifecycle-manager seam**:

- `juniper-cascor/src/cascade_correlation/cascade_correlation.py:1638`
  — the output-layer training loop is a plain `for epoch in range(epochs):`
  full-batch SGD loop. After each `optimizer.step()`, a throttled callback
  fires via `_cb(epoch=epoch + 1, epochs=epochs, loss=loss.item())`
  (line 1656). The throttle is `epoch % 25 == 0 or epoch == epochs - 1` so
  observations are emitted every 25th epoch plus the final one.
- `juniper-cascor/src/api/lifecycle/manager.py:681`
  — `_output_training_callback(epoch, epochs, loss)` is the registered
  callback. It calls `monitor.on_epoch_end(...)` and then computes the
  R5.4-pre histogram observation as the delta of two `time.perf_counter()`
  readings between successive callback invocations
  (`observe_training_step_duration("output", now - prev)`, line 706).
- `juniper-cascor/src/api/lifecycle/manager.py:679`
  — the `_step_timer` closure box holds the prior `perf_counter()` reading
  and is reset on each new `fit()` entry (line 718) so the timer never leaks
  across runs.

The metric **shape** is therefore correct (a phase-labeled latency histogram
with documented buckets) but the **semantics** are per-callback-invocation,
which under the current 25-epoch throttle equals per-25-epochs. The R5.4-pre
patch documented the boundary as an "epoch at the api-lifecycle level" and
deferred the per-step refinement to this design.

### 2.2 The bigger surprise: cascor is full-batch end-to-end

The agent of R5.4-pre treated the gap as a missing per-batch hook in an
otherwise mini-batched trainer. Closer reading shows the gap is
**structural, not just hook-shaped**: the output-layer loop
(`cascade_correlation.py:1638`) and the candidate-unit loop
(`candidate_unit.py:564`) both run `for epoch in range(epochs):` with one
full-batch forward + backward + optimizer step per epoch. There is no
`DataLoader`, no `TensorDataset`, no inner mini-batch loop anywhere outside
test code (grep of `src/cascade_correlation/` and `src/api/` confirms zero
matches). The `batch_size` references in the trainer describe the leading
dimension of the **full** input tensor, not a mini-batch dimension.

**This is the load-bearing finding of this design.** "Mini-batch
instrumentation" in a generic PyTorch trainer means hooking a
`for batch in dataloader:` inner loop. Cascor has no such loop. The trainer's
finest-grained natural step is **one epoch == one full-batch step**, and the
R5.4-pre histogram already measures that (modulo a 25-epoch throttle).

This reframes the sub-track's scope: the work is **not** adding a mini-batch
hook (there are no mini-batches), it is **(a) dropping the 25-epoch throttle
on the metric path so every epoch — i.e. every true training step — is
observed, and (b) preserving a separate per-epoch roll-up for backward
compatibility with the R5.4 alerts.**

### 2.3 What metrics currently exist (R5.4-pre)

Defined in `juniper-cascor/src/api/observability.py:232`:

- `juniper_cascor_training_step_duration_seconds{phase}` — Histogram, buckets
  `(0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, +inf)` per
  `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`
  §6 (cross-repo).
- `juniper_cascor_training_epochs_total{phase}` — Counter (line 187).
- `juniper_cascor_training_sessions_completed_total{status}` — Counter
  (line 182, used by SLO 3.3).

The histogram and the epoch counter together let an operator derive
epoch-rate (counter/time) and epoch-latency-p95 (histogram quantile). Neither
gives true per-step variance until the throttle is dropped.

---

## 3. Requirements

### 3.1 Target metric

Propose: a **new** histogram

```text
juniper_cascor_training_step_duration_seconds_per_step{phase}
```

(naming convention: append `_per_step` to make the granularity explicit; the
existing `_seconds` metric is then unambiguously the per-epoch roll-up.) The
exact name is an entry-plan question (Q-name in §6.4) — alternatives include
`_per_minibatch` (rejected: misleading because cascor has no mini-batches) or
a refactor to `_per_epoch_seconds` + `_per_step_seconds` (rejected: breaks
existing dashboards and alerts that already point at the un-suffixed name).

**Cardinality discipline (R1.1):** the only label is `phase` ∈
{`input`, `candidate`, `output`} — same closed-set as the existing histogram.
No per-fit, per-session, or per-network-id labels (those would explode
cardinality). This is consistent with the R1.1 cardinality policy applied to
every histogram in the cascor surface.

The **existing** `juniper_cascor_training_step_duration_seconds` histogram
**MUST NOT be removed**. It continues to serve the renamed SLI 3.4
("train-epoch p95") and any dashboards / alerts already pointing at it. The
per-step metric is **additive**, not a replacement.

### 3.2 Performance constraint

Per-step timing overhead must be **<< per-step compute**. Quantitatively: a
step taking 50 ms must not be slowed by more than 0.5 ms (1%) by
instrumentation. This is achievable with `time.perf_counter()`
(approx. 100 ns per call on x86-64) plus a single `Histogram.observe()` call
(approx. 1–10 µs depending on `prometheus_client` lock contention).

The overhead **constraint** carries into the recommendation in §5: an
in-loop `time.perf_counter()` + `observe()` pair is well inside budget; a
profiler-driven sampling approach (Approach C) has variable and harder-to-
bound overhead.

### 3.3 Test requirement

Unit test (extending the existing api-lifecycle test suite) asserts:

- For an `epochs=N` `fit()` invocation, the histogram's `_count` series
  increases by exactly `N - 1` (the first epoch seeds the timer and emits no
  sample; this matches the R5.4-pre "first callback seeds, no bogus sample"
  contract). Note: under the recommendation in §5 the throttle is dropped,
  so every epoch becomes a step observation, distinct from the current
  R5.4-pre semantics where only every 25th epoch produces a sample.
- The new per-step metric and the existing per-epoch metric **both** observe
  during the same `fit()` (regression test for backward compatibility — §3.5).
- The `phase` label takes values from the closed set
  `{input, candidate, output}` — never an unlabelled or empty value.

### 3.4 Backward compatibility

- Dashboards / alerts referencing `juniper_cascor_training_step_duration_seconds`
  (per-epoch, post-fixup-rename) **MUST keep working** unchanged. The
  per-epoch metric continues to be emitted on the same code path it is
  today.
- The R5.4 burn-rate alerts (multi-window, derived from per-epoch p95) keep
  firing against the per-epoch metric. The per-step metric is initially
  observed only — no alerts derived from it land until R5.x is open and a
  per-step SLO is calibrated against real production data.

### 3.5 SLO impact

Two options for how SLI 3.4 evolves once per-step is live, to be resolved at
sub-track entry-plan time (see §6.4 Q-slo):

- **(option α)** Re-point SLI 3.4 to the per-step metric. Tighter SLO; risks
  invalidating the calibration of the R5.4 alerts.
- **(option β)** Add SLI 3.4b alongside SLI 3.4. SLI 3.4 stays per-epoch
  (continuity for R5.4 alerts); SLI 3.4b is per-step. Both render on the
  cascor dashboard.

The design recommends option β for the **first** sub-track release;
option α can be revisited at a later phase boundary once per-step variance
distributions are characterized in production.

---

## 4. Approach options

Each approach is evaluated on (i) where the timer + `observe()` lives, (ii)
overhead, (iii) blast radius, (iv) test feasibility.

### 4.1 Approach A — Trainer-internal hook in the step loop

Add `time.perf_counter()` brackets directly inside the `for epoch in
range(epochs):` loops in `cascade_correlation.py:1638` (output) and
`candidate_unit.py:564` (candidate). After each `optimizer.step()`, call
`observe_training_step_duration_per_step(phase, dt)` unconditionally — no
25-epoch throttle on the per-step path. The per-epoch roll-up callback
continues to run on the existing throttle.

- **Overhead.** Lowest. Two `perf_counter` calls and one `observe()` per
  step; well under the 1% / 0.5 ms budget for a 50 ms step.
- **Blast radius.** Two trainer files plus a thin emit helper in
  `observability.py`. ~50–80 LOC across 3 files.
- **Coupling.** Couples observability into trainer internals — a direct
  `from api.observability import ...` line in the trainer module.
- **Test feasibility.** High. Reuses the R5.4-pre histogram-test scaffolding.

### 4.2 Approach B — Callback fan-out from api-lifecycle

Extend the lifecycle callback API (`training_monitor.register_callback(...)`)
to emit a new `step_end` event alongside `epoch_end`. The trainer surfaces
per-step events via a callback parameter; the lifecycle manager subscribes
and fires the histogram observation, mirroring R5.4-pre's
`_output_training_callback` but on an un-throttled path.

- **Overhead.** Adds one Python-level callback dispatch per step (under 5 µs
  for a 50 ms step — within budget; non-trivial for sub-ms candidate steps).
- **Blast radius.** Wider. Trainer methods grow an `on_step_end_callback`
  parameter; the lifecycle manager grows a registration; the monitor's
  `_trigger_callbacks` registry grows a new event name. ~150–250 LOC across
  4–5 files; signature changes at the lifecycle/trainer boundary.
- **Coupling.** Cleaner separation: trainer stays observability-agnostic.
  Same architectural pattern R5.4-pre used for the per-epoch metric.
- **Test feasibility.** High but ~3× the test surface (callback contract +
  registration + multiplex behavior + metric shape).

### 4.3 Approach C — Profiler-driven sampling

Use `torch.profiler.profile(...)` or `torch.cuda.Event(enable_timing=True)`
markers around the training loop. Post-process the profiler output (after
`fit()` returns) into a batch of `Histogram.observe()` calls.

- **Overhead.** Lowest in steady-state running (sampling cadence rather than
  every-step), but profiler enable/disable cycles introduce their own
  overhead. `torch.cuda.Event` requires CUDA — unusable for cascor's
  CPU-only test path.
- **Blast radius.** Smallest at the trainer, largest at test/CI — profiler
  interaction is hard to mock and non-deterministic.
- **Coupling.** Loosest, but the metric is **sampled**, not every-step.
  Tail-latency outliers (GC pauses, thermal throttles — the exact things the
  per-step metric should surface) are systematically under-sampled.
- **Test feasibility.** Low. Asserting "histogram observed N times" requires
  a test-only bypass of the profiler.

### 4.4 Approach D — Hybrid phasing

Phase 1: ship Approach A immediately. Phase 2: once production data is in
hand and the per-step SLI is calibrated, optionally refactor toward Approach
B if trainer coupling becomes a maintenance burden. Treats Approach B's
architectural cleanup as an opt-in follow-on rather than a precondition.

---

## 5. Recommendation

**Recommended: Approach A** (trainer-internal hook in the step loop), with
Approach D's phasing left as an optional future cleanup.

Rationale (in order of weight):

- **Performance margin.** Cascor has known fast paths (small candidate
  networks, simple datasets) where a single epoch is sub-millisecond. The
  budget in §3.2 is per-step *absolute*, not per-fit relative; on a
  sub-millisecond step the 0.5 ms ceiling is tight enough that Approach B's
  ~5 µs callback-dispatch overhead, while small in absolute terms, is the
  only meaningful overhead delta between A and B. Approach A is the
  zero-overhead path.
- **Blast radius.** The per-step metric is one signal. Approach A delivers
  it in ~50–80 LOC across three files with a direct test path. Approach B
  delivers it via a new callback contract that other consumers (canopy WS
  broadcast, snapshot manager, replay session) would all eventually want to
  subscribe to — work that is **out of scope for this sub-track** and
  shouldn't gate a single histogram landing.
- **Cascor's full-batch reality.** §2.2 found that cascor has no mini-batch
  loop and the epoch loop is the natural step boundary. The "mini-batch
  hook" abstraction Approach B implies is over-built for a trainer where
  the only finer granularity than "one epoch" is "halfway through one
  forward pass" — which is not a useful boundary to expose. Approach A
  matches the trainer's actual structure; Approach B imposes a callback
  abstraction the trainer doesn't currently need.
- **Test cost.** Approach A reuses the existing R5.4-pre histogram-test
  scaffolding almost verbatim. Approach B needs new tests for the callback
  contract, the registration path, and the multiplex behavior — roughly 3×
  the test surface.

### 5.1 Counter-arguments and rebuttals

- **"Approach A couples the trainer to the observability module."** True,
  and acknowledged. The coupling is a single `from api.observability import
  observe_training_step_duration_per_step` line, behind a defensive
  try/except (mirroring the R5.4-pre pattern at
  `manager.py:707`). If the coupling becomes a real maintenance burden, the
  Approach D phase-2 refactor recovers the clean separation without
  re-litigating the histogram itself.
- **"Approach B is more architecturally pure."** True for a generic
  PyTorch-Lightning-style framework. Cascor is not that framework. Adding a
  generic callback contract for one consumer is the wrong shape; it should
  be added when a second consumer materializes (e.g. canopy wanting per-step
  WS frames).
- **"What if a future trainer rewrite adopts mini-batches?"** Then both A
  and B require a refactor — A trivially (move the in-loop hook into the
  inner mini-batch loop), B less trivially (the callback contract has to
  decide: per-mini-batch fan-out, per-epoch fan-out, or both). This isn't a
  point in B's favor.

---

## 6. Proposed sub-track sequencing

### 6.1 Sub-track ID

**METRICS-MON R5.6 — Per-step training instrumentation.**

(Naming follows the existing R5.x convention. R5.5 is reserved by the R5
entry plan for an as-yet-unspecified follow-on; R5.6 keeps numbering monotone
without colliding. If the R5 program closes before this work starts, the
sub-track can re-number to `METRICS-MON-2 Phase 1` per the R5 entry plan's
post-R5 convention.)

### 6.2 Scope estimate

- **PR count:** 2 (small program).
  - PR 1 (juniper-cascor): add the per-step histogram, drop the 25-epoch
    throttle on the metric-emit path, instrument both training loops, ship
    unit tests. ~150–250 LOC including tests.
  - PR 2 (juniper-deploy): refresh the cascor Grafana dashboard to surface
    the per-step metric panel (alongside the per-epoch panel from R5.3),
    optionally add SLI 3.4b to the SLO catalog per option β. ~50–100 LOC
    JSON/YAML.
- **Lines-of-code rough order of magnitude:** small (under 500 LOC total
  across both PRs).
- **No cascor-worker, juniper-data-client, or juniper-canopy changes
  required.** Worker doesn't run cascor's trainer; clients are
  read-only consumers of the existing metric surface; canopy reads via
  Prometheus / WS frames and gets the new metric for free.

### 6.3 Dependencies

- **Gates on:** R5.4 closing. R5.4 ships per-epoch burn-rate alerts. We do
  not want to land per-step instrumentation while those alerts are still
  being calibrated, because changes to the throttle / emit path could shift
  the per-epoch p95 distribution and force re-calibration mid-flight.
- **Gates on (data):** at least one production-scale run on the per-epoch
  metric so that the per-step bucket layout (entry-plan Q1) can be chosen
  from real data rather than synthetic guesses.
- **Gated by this sub-track:**
  - Future SLI 3.4b / 3.4-tightening work (any per-step SLO).
  - Future per-step gradient-norm tracking (research signal — would reuse
    the same in-loop hook site once it exists).
  - Any canopy "live step rate" panel that wants step-granular data
    (currently only epoch-granular).

### 6.4 Open questions to resolve at sub-track entry-plan time

(Format mirrors the R3/R4/R5 entry-plan-Q convention.)

| ID | Question | Owner | Default if not pinned |
|---|---|---|---|
| **Q1 (buckets)** | What bucket boundaries? Re-use the R5.4-pre layout `(0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, +inf)` or design a new layout calibrated against the production per-epoch data the R5.4 alerts will collect? | METRICS-MON owner | Re-use R5.4-pre layout for v1; revisit at first phase boundary. **Per the parent-task scope, this is out-of-scope for this design doc.** |
| **Q2 (name)** | Final metric name: `..._seconds_per_step`, `..._per_minibatch`, or refactor existing to `..._per_epoch_seconds` + new `..._per_step_seconds`? | METRICS-MON owner | `..._seconds_per_step` (additive, breaks no existing alerts). |
| **Q3 (throttle)** | Drop the 25-epoch throttle entirely on the per-step path, or sample (e.g. every Nth epoch)? Sampling reduces metric volume but defeats the variance-detection use case. | METRICS-MON owner | Drop entirely; rely on histogram bucketing for volume management. |
| **Q4 (slo)** | Per-step SLI strategy at sub-track close: option α (re-point SLI 3.4) or option β (add SLI 3.4b alongside)? | juniper-deploy SLO owner | Option β for v1; revisit after one production calibration cycle. |
| **Q5 (slim-step)** | Some candidate-unit training runs are sub-millisecond per step. Is that overhead-budget regime acceptable, or should the per-step metric be omitted on the candidate phase? (Equivalent: should the `phase=candidate` label be optional?) | METRICS-MON owner | Emit on all phases; rely on `phase` label to let operators filter. |
| **Q6 (gating)** | Land before or after R5.5 (whatever R5.5 turns out to be)? | METRICS-MON program lead | After R5.4 closes, ordering vs R5.5 is independent. |

These map 1:1 to entries in the R5.x roadmap once R5.6 enters its own entry
plan.

---

## 7. Risks & non-goals

### 7.1 Risks and mitigations

- **R-1: Instrumentation overhead breaks small-model latency benchmarks.**
  The candidate-unit pre-training loop runs sub-millisecond per epoch on
  small networks; even Approach A's microsecond-scale `observe()` is a
  measurable fraction of compute time. **Mitigation:** ship a benchmark
  comparison (pre vs post) as part of PR 1's test suite, gating merge on
  <1% wall-clock regression on the existing `tests/performance/` suite. If
  the budget is exceeded, fall back to phase-conditional emission (drop
  per-step on `phase=candidate`).
- **R-2: Per-step metric cardinality balloons.** A poorly-disciplined label
  (e.g. `network_id`, `session_id`, `worker_id`) would explode bucket count
  by N × num_workers × num_sessions. **Mitigation:** keep the **closed-set
  `phase` label only**, matching the R5.4-pre histogram and the R1.1
  cardinality policy. Linter-enforce: extend the R1.1 cardinality regression
  test in cascor's observability test suite to assert the new metric's
  label set.
- **R-3: Throttle removal increases scrape payload size.** Dropping the
  25-epoch throttle on the metric-emit path means every epoch produces a
  histogram observation. The Prometheus client's histogram is
  bucket-bounded (8 finite buckets + `+inf`), so per-emission cost is
  constant. The total metric volume grows with epoch count, not with
  observation count — this is bounded. **Mitigation:** none required at
  the metric layer; verify scrape payload size in PR 1's CI logs.
- **R-4: Per-epoch alerts mis-fire during the cutover window.** While PR 1
  is in flight, the existing per-epoch metric continues to report under
  the 25-epoch throttle (unchanged). Risk is zero unless the per-epoch
  emit path is also touched. **Mitigation:** PR 1 must keep the per-epoch
  emit path byte-identical to its post-R5.4 state; only the per-step
  emit path is new code.

### 7.2 Non-goals

- **Not a refactor of cascor's trainer architecture.** This is an additive
  hook. The `for epoch in range(epochs):` loop remains the structural unit
  of cascor training, full-batch and all. Any move to mini-batched / data-
  loader-based training is a separate, much larger initiative.
- **Not a replacement for the existing per-epoch histogram.** Both metrics
  ship side-by-side. The per-epoch metric remains the authority for SLI
  3.4 (post-fixup-rename) and the R5.4 burn-rate alerts.
- **Not the venue for per-step SLO calibration.** That belongs in R5.x
  follow-on work once production data is in hand. This sub-track ships the
  metric and a panel; it does not pre-commit to a per-step SLO target.
- **Not a callback-API redesign.** Approach B's callback contract is
  explicitly deferred to Approach D phase 2 (or never). This sub-track does
  not block on a generic per-step callback fan-out.
- **Not a juniper-cascor-worker change.** The worker dispatches candidate
  training work but does not host the cascor trainer's epoch loop. Worker
  observability stays as-defined by R1.3 / R4.4.

---

## 8. References

- **juniper-cascor#188** — R5.4-pre cascor training counters + train-step
  histogram + worker→Prometheus bridge. Surfaced the granularity gap this
  document addresses.
- **juniper-deploy#48** — R5.1 SLO catalog
  (`notes/SLO_CATALOG_2026-05-03.md`, cross-repo). Defines SLI 3.4 and the
  surrounding cascor/canopy/data SLO surface.
- **juniper-deploy fixup PR** — branch
  `metrics-mon/r5-1-fixup-sli-3-4-rename` (cross-repo). Renames SLI 3.4
  to "Cascor train-epoch p95" and forward-references this document as the
  bridge to the per-step fix.
- **juniper-cascor source files cited in §2** (cross-repo):
  - `src/api/lifecycle/manager.py:650-720` — per-epoch callback boundary;
    R5.4-pre histogram emit site.
  - `src/api/observability.py:139-238` — histogram registration and bucket
    layout.
  - `src/cascade_correlation/cascade_correlation.py:1638-1656` — output-
    layer training loop and throttled callback.
  - `src/candidate_unit/candidate_unit.py:564-590` — candidate-unit
    training loop (parallel structure to the output loop).
- **juniper-cascor `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`**
  (cross-repo) — per-boundary bucket rationale; would be extended by the
  R5.6 PR 1 with the per-step bucket layout (Q1).
- **juniper-ml `notes/code-review/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`**
  — the R5 phase entry plan; this design doc's parent context.
- **juniper-ml `notes/code-review/METRICS_MONITORING_ROADMAP_2026-04-25.md`**
  — the program-level roadmap. R5.6 will be added to §8 once this design is
  accepted.

---

<!-- markdownlint-enable MD013 -->
