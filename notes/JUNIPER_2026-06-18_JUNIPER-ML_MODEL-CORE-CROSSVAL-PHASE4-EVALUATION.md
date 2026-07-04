# juniper-model-core — Cross-Validation Phase 4+ Deferreds: Audit & Evaluation

**Project**: juniper-ml — `juniper-model-core` shared model-contract package
**Repository**: pcalnon/juniper-ml (package subdir `juniper-model-core/`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (evaluation; gated on the designed-vs-reality audit in §2)
**Last Updated**: 2026-06-18

---

> **What this is.** The "task A" evaluation of the cross-validation **Phase 4+ deferred items**
> ([`JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md`](JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md)
> §6 Phase 4+, §8) — which to do, in what order, and which to keep parked. Per Paul's instruction it is
> **gated on an audit** of each deferred item's *designed/expected* state against *current project
> reality* (so the evaluation reflects reality, not stale design assumptions). Headline: of the five
> deferreds, **only one — multi-ticker embargo-aware walk-forward — is genuinely unblocked and
> reality-supported today**; one (`map_fn` documentation) is a cheap clarity win; the other four are
> correctly parked with intact triggers.

---

## 1. The deferred set (designed/expected baseline)

From the ratified crossval design ([`…CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md) §8)
and build roadmap (§6 Phase 4+ / §8): parallel/distributed fold execution (WS-8 / OQ-11) ·
classification held-out metrics · multi-ticker embargo-aware walk-forward (via `ticker_code`) ·
server-side fold materialization in juniper-data (#168 scope C) · a `score()` method on the
`TrainableModel` ABC. (The canopy per-fold UI also listed there is WS-5-scoped and is handled in the
WS-5 re-evaluation, not here.)

---

## 2. Audit — designed vs. current reality

Method: three independent, read-only reality-check sub-agents, one per area (worker/WS-8; data/
multi-ticker; classification + ABC), each comparing the deferred design against the actual state of
the relevant repos with `file:line` / doc evidence. Findings are recorded in [Appendix A](#appendix-a--audit-evidence-record).

| Deferred item | Designed/expected | Current reality | Verdict |
|---|---|---|---|
| **Distributed/parallel folds (WS-8/OQ-11)** | deferred to WS-8 worker; `map_fn` seam in place | seam is **built** (a thread-pool `map_fn` drops in today), but cascor-worker is candidate-specific (payload/result/push-architecture) — **not** reusable for generic folds; the per-fold work is a **non-picklable local closure** (blocks process pools); **OQ-11 still "Unknown — investigate"**; WS-8 correctly not-started (trigger = recurrence training cost) | **FAR + not-needed-now** |
| **Classification held-out metrics** | regression-first; `score()` raises `NotImplementedError`; unlock when a classification consumer appears | **no classification `TrainableModel` exists** — cascor isn't one (no model-core import/dep), WS-6 not started and its golden-suite gate doesn't exist; the only implementer is the regression LMU | **not-needed-yet** (zero consumer) |
| **Multi-ticker embargo-aware walk-forward** | deferred; v1 single-series; refine via `ticker_code` | **data is READY** — `equities_seq` emits per-window `ticker_code` + `window_end_date`, the windower already has an `embargo` param, and real 503-ticker S&P data exists; the gap is **pure model-core logic** (multi-entity grouping), **not** blocked on juniper-data | **✅ unblocked + feasible now** |
| **Server-side fold materialization (#168 scope C)** | deferred; superseded by D-CV-4 (client-side folds) | `juniper-data/core/split.py` still single-cut, walk-forward "intentionally not implemented"; zero movement; D-CV-4 makes scope C an optional perf optimization, not a prerequisite | **not-needed** (intentionally optional) |
| **`score()` on the `TrainableModel` ABC** | external scoring; add only "if a second need appears" (D-CV-3 / D9) | still absent; **no second consumer emerged** (canopy's `.evaluate` hits are Playwright JS, unrelated); crossval scores externally via `predict` vs `y` | **not-needed-yet** (YAGNI holds) |

No item has regressed or silently advanced. Notably the **data foundation is ahead of the CV
logic**: `ticker_code` / `window_end_date` / per-window `embargo` already exist, so the multi-ticker
refinement is unblocked.

---

## 3. Prioritization

### DO-NOW — multi-ticker embargo-aware walk-forward

The single deferred item that is unblocked *and* reality-supported. It is also a **correctness**
matter, not just a feature: running the current single-series `walk_forward_folds(order=window_end_date)`
on the 503-ticker `equities_seq` panel pools windows across tickers and applies a global-date embargo,
which does **not** correctly purge per-ticker lookback overlap at the train/eval boundary. It matters
whenever `equities_seq` cross-validation becomes a real use (the recurrence `/v1/crossval` endpoint can
already be pointed at it). Approach in §4.

### CHEAP — document the `map_fn` seam constraints

Not a build; a clarity win surfaced by the audit. The executor's `map_fn` seam works today with an
order-preserving thread-pool map, but the per-fold work is a **non-picklable local closure**, so a
`multiprocessing` / distributed backend needs that work refactored to a top-level/picklable callable
and a picklable `model_factory`. Document this in `crossval/executor.py` so the future WS-8 implementer
knows the exact constraint. (Small docstring task; tracked as task A's second step.)

### KEEP-DEFERRED (triggers intact)

| Item | Keep parked because | Unlock trigger |
|---|---|---|
| Distributed/parallel folds | cascor-worker not reusable; non-picklable work unit; no demand | **OQ-11** resolved **and** recurrence training cost justifies it (WS-8) |
| Classification held-out metrics | no classification `TrainableModel` exists to consume it | **WS-6** (cascor adopts the contract) — itself gated on the golden suite (OUT-12) |
| Server-side fold materialization (#168 C) | client-side folds (D-CV-4) suffice; pure optimization | a measured client-side fold-derivation cost problem |
| `score()` on the ABC | single consumer (crossval) scores externally; YAGNI | a **second** consumer needing held-out scoring on the contract |

Building any of these now would be speculative over-abstraction (RK-4) or risk classification
assumptions leaking into the generic surface (RK-6).

---

## 4. Approach sketch — multi-ticker `walk_forward_folds`

**Goal:** time-ordered, leakage-safe folds over a multi-entity panel, where the embargo purge respects
each entity's own lookback rather than a single global-date rank.

**Inputs already available** (from `equities_seq`): per-window `ticker_code (n,)` and
`window_end_date (n,)`. `walk_forward_folds` today is index-based and shape-agnostic. Note **two
distinct `embargo` mechanisms** at different layers: the generator's `embargo` (`_sequence.py`, a
*bool* that purges windows straddling the single train/test cut) is **not** the crossval-layer
`embargo` (`splits.py`, an *int row-gap* at each fold boundary). The multi-ticker work is in the
latter (the crossval layer); the generator's flag is not reusable for fold generation.

**Proposed API (additive, backward-compatible):** add an optional `groups: np.ndarray | None = None`
(per-sample entity id, e.g. `ticker_code`) to `walk_forward_folds`. When `groups is None` behavior is
unchanged (single-series). When supplied, folds stay **pooled and date-ordered** (train = all entities'
windows up to each date cut; eval = the next block) but the `embargo` purge is applied **per group**.

| Option | What it does | Strengths | Weaknesses |
|---|---|---|---|
| **A — per-ticker folds, union by index** | run the existing single-series generator per entity, then union fold-`i` train/eval across entities | clean per-entity temporal integrity + embargo | uneven window counts across entities make fold sizes ragged; more bookkeeping |
| **B — pooled date-ordered + per-group embargo** *(recommended)* | one pooled date-ordered fold sequence; embargo drops, per group, the windows within the gap of each cut | matches financial panel walk-forward; pooled folds train/eval all entities together by date; minimal API (`groups=`) | embargo logic is per-group (slightly more than the global version) |
| **C — full `groups` strategy object** | a pluggable grouping/splitting strategy | most general / future-proof | over-abstraction (RK-4) for one entity dimension today |

**Recommendation: B**, exposed as `walk_forward_folds(..., groups=ticker_code)`. It is the smallest
correct extension, keeps the index-based/shape-agnostic contract, and is the canonical panel
walk-forward.

**Embargo semantics (the correctness crux).** The per-group purge must drop each entity's eval windows
whose lookback span reaches back across *that entity's* train boundary — i.e. a same-group gap measured
in the entity's own time / lookback length, **not** a fixed count of pooled rows. The global
pooled-row-count embargo is precisely what's wrong on a panel today: because windows interleave across
tickers by date, an `embargo` of *k* rows removes ~*k* mostly-other-ticker windows and fails to purge
the same-ticker lookback overlap at the boundary. Tests: per-group embargo purge (a same-ticker eval
window never shares lookback with its train side), pooled fold counts/ordering, `groups=None` parity
with today, and a determinism check — plus a recurrence-side `equities_seq` integration check when that
consumer lands.

**Packaging:** additive to `crossval/splits.py`; a `juniper-model-core` minor (0.2.x or 0.3.0 — Paul's
call) following the same publish-first + release-convention path as 0.2.0.

---

## 5. Cross-references

- Crossval layer design (deferred list, D-CV-1…5): [`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md).
- Build roadmap (Phase 4+, OPT-D/F, §8 deferreds): [`JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md`](JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md).
- Contract (D3 `**kw`, D9 `evaluate()` deferral): [`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md).
- Implementation targets: `juniper-model-core/juniper_model_core/crossval/{splits,executor}.py`; data: `juniper-data/juniper_data/generators/equities_seq/`.

---

## Appendix A — audit evidence record

Three read-only reality-check sub-agents (2026-06-18), each scoped to one area and reporting with
`file:line` / doc evidence; findings folded into §2.

- **Agent 1 — distributed folds / WS-8:** confirmed the `map_fn` seam shape (`crossval/executor.py`),
  the non-picklable-closure constraint, that cascor-worker is candidate-specific (not reusable), and
  OQ-11 is still "Unknown — investigate" / WS-8 correctly not-started.
- **Agent 2 — data / multi-ticker:** confirmed `split.py` is still single-cut; that `equities_seq`
  emits `ticker_code` + `window_end_date` and the windower has an `embargo` param (real 503-ticker S&P
  data exists) → multi-ticker folds are data-ready and feasible client-side; #168 scope C is intentionally
  optional under D-CV-4.
- **Agent 3 — classification + ABC:** confirmed cascor is not a `TrainableModel` (no model-core
  coupling; WS-6 not started; golden-suite gate absent), the regression-only `score()` stub
  (`crossval/metrics.py`), and no emerging second need for `score()` on the ABC (YAGNI intact).
