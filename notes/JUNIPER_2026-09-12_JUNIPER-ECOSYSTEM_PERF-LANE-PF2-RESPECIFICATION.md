# PF-2 re-specification: three axes to replace one that measured an invariant

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-12
**Status** (updated 2026-09-24; §5 has the per-axis table):

- **Axis 2 RUN**, no knee (§3 RESULT).
- **Axis 3 RUN** (§4.2): it separates 2 → 3 → 4 spirals. The seed probe (§4.3) shows 5 does
  rank below 4 on most dataset seeds. Seed spread dominates the gap between neighbours, so
  **one seed cannot order adjacent counts**.
- **Axis 1 BLOCKED on its instrument** (§2 note). The owner ruled 2026-09-24 to publish
  `epochs_completed` from cascor.

*Superseded status line (2026-09-12): "SPEC. Axis 3's calibration is DONE … Axis 2 needs an owner
decision … Axis 1 is specifiable now."*
**⚠ §1 carries a CORRECTION to a claim that shipped wrong in `juniper-ml#1927`** — read it before quoting which generator the experiment path uses.
**License**: MIT License

---

## 0. What this document is

Owner decision **D4** of
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md),
turned into a specification.

PF-2 as written varies `dataset.params.n_points_per_spiral` over `[250, 500, 1000, 2000]` and
**measures an invariant**: `step_count` is identical at 250 and 2000 at every epoch budget
(450 / 890 / 1770), and `step_sum` at 2000 is 6–8% *lower* — inside noise. The owner ruled:
retarget at the candidate phase, and add a wide wall-time characterisation plus a spiral-count
axis.

This document states the three axes, **what was found when each was checked against the real
parameter bounds**, and the calibration each needs. It does **not** commit a matrix, because the
P2 plan's own standing rule applies — *"a guessed number would look like calibration without
being it."*

---

## 1. The constraint that decides axis 2: TWO generators, different limits

`n_points_per_spiral` and `n_spirals` are bounded on one path and unbounded on the other, and
which one an experiment takes depends on how the dataset is supplied.

| path | reached by | `n_points_per_spiral` | `n_spirals` |
|---|---|---|---|
| **cascor in-process** | `POST /v1/training/start` with `dataset.generator: spiral` — `_generate_spiral_data`, `juniper-cascor/src/api/routes/training.py:103` → `:363` | **unbounded** — the params are read as plain ints (`:385-386`) with no validation | **unbounded** |
| **juniper-data** | a *staged* dataset (`POST /v1/training/dataset`), and every generator that is not `spiral` | **`MIN_POINTS` 10 … `MAX_POINTS` 10000** | **`MIN_SPIRALS` 2 … `MAX_SPIRALS` 10** |

juniper-data's bounds are Pydantic field constraints
(`juniper_data/generators/spiral/params.py:70-82`, constants in `…/spiral/defaults.py:26-31`), so
a request past them is refused, not clamped. ~~It is a 422.~~ **It is a 400 that carries the
validation message** (corrected 2026-09-23, measured through the real route: `n_points_per_spiral`
10,001 → `400 "Invalid parameters: 1 validation error for SpiralParams …"`). The request model
types `params` as `dict[str, Any]`, so the boundary cannot check it; the route builds the
generator's params model itself and maps its `ValueError` to 400
(`juniper_data/api/routes/datasets.py:131-138`). The second correction below is the case that
loses the message.

> ## ⚠ CORRECTION 2026-09-15 — the bullet immediately below is WRONG, and it shipped that way
> ## in juniper-ml#1927.
>
> **The experiment/driver path does NOT use the in-process generator. It fetches from
> juniper-data, so `MAX_POINTS` and `MAX_SPIRALS` DO bind.** Proven by run evidence, not by
> reading: every cell of the 2026-09-15 calibration wrote
> `<run>/data/spiral-3.0.0-<hash>.meta.json` carrying `"generator_version": "3.0.0"` and the
> full juniper-data param set (`sizing_mode`, `val_percent`, `algorithm`, `radius` — none of
> which cascor's in-process generator emits).
>
> **Therefore the owner's requested 250 → 500,000 range is NOT reachable on the suite path**, and
> axis 2 must either cap at 10,000 (still a 40× range, 5× wider than the inert 8× that was
> tested), raise `MAX_POINTS` in juniper-data as its own decision, or run outside the suite
> harness.
>
> ## ⚠ SECOND CORRECTION 2026-09-23 — the suite path does not reach 10,000 either; it stops at 5,882
>
> The paragraph above, and the owner menu built from it (D4, ruled 2026-09-22 as "10,000 now"),
> treat `MAX_POINTS` as the ceiling on the **request**. It is the ceiling on the **total rows per
> spiral**. juniper-data's additive sizing (`juniper_data/core/split.py`) treats
> `n_points_per_spiral` as the TRAIN count, adds the val and test partitions on top, and
> re-validates the inflated count against `MAX_POINTS`. At the suite's split (`train_ratio` 0.8,
> `test_ratio` 0.2, default `val_percent`) the inflation is 1.7×. So a request of 10,000 becomes
> 17,000 internally and is rejected. Bisected in the JuniperData env: **5,882 accepted, 5,883
> rejected**.
>
> **Found by running the top cell, not by reading.** The 10,000 probe ended `torn_down_early`
> after 17.6 s. juniper-data answered **400 "Invalid request parameters"** and logged the cause
> only at DEBUG. That is not the 422 this section predicted (a prediction itself wrong, corrected
> in its first paragraph on 2026-09-23: an out-of-range request is a 400 WITH its message). The field check passes (10000 ≤
> 10000), generation then raises a pydantic `ValidationError`, and the API's `ValueError`
> handler turns it into a generic 400. A client cannot learn the real bound from the response.
> That is a juniper-data defect in its own right.
>
> **Filed 2026-09-23 as [juniper-data#432](https://github.com/pcalnon/juniper-data/issues/432)**
> for the defect register (no `APD-DATA-*` id assigned yet), after reproducing it through the real
> route with `util/ad-hoc/2026-09-23_data_additive_overflow_repro.py` (FastAPI `TestClient`, the
> driver's exact params). 5,882 → 201; 5,883 and 10,000 → `400 "Invalid request parameters"`, cause
> at DEBUG only; the 10,001 control → 400 **with** the message. That control is what makes it a
> lost diagnostic rather than a policy. Two more findings from the reproduction: the helper's
> docstring promises "a 422 at the API boundary" (`juniper_data/core/partition_params.py:153`),
> which is false; and the test that calls itself "End-to-end" never goes through the route.
>
> Axis 2 is built as `util/experiments/suites/perf/pf2-axis2-cascor-dataset-range.yaml`, capped
> at **5,800** (about 23×; 425 → about 9,860 total rows per spiral). Every "10,000" in this
> document means total rows, not a request.
>
> **How the error was made**, because the shape recurs: the 2026-09-10 probe note correctly
> records that *`POST /v1/training/start` materialises the in-process spiral generator*. That is
> true of **that route**, which the listener probes used directly. The experiment driver stages
> its dataset differently, and `auto_start_data_service: false` was read as "no juniper-data
> involved" when it only means the launcher does not *start* the service. A correct reading of one
> path, generalised to another — and it stood until run evidence contradicted it.

**Consequences for this spec (as originally written — see the correction above):**

- ~~The owner's requested **250 → 500,000** points-per-spiral range is reachable **only on the
  in-process path** — it is 50× past juniper-data's cap. `spiral-smoke.yaml` sets
  `auto_start_data_service: false` and `dataset.generator: spiral`, so the perf suites already
  take that path today.~~
- **This makes axis 2 a characterisation of cascor's compute, not of the juniper-data pipeline.**
  The two generators are separate implementations. That is the right target for a wall-time
  question, but the resulting numbers must not be quoted as juniper-data figures.
- The owner's expectation that the spiral axis is *"certainly ≤ 10 and probably ≤ 6"* matches
  `MAX_SPIRALS = 10` exactly. Above 10 the in-process path would still run while juniper-data
  would refuse — a divergence worth **not** exercising.

---

## 2. Axis 1 — the candidate phase (the retarget)

**Keys**: `training.params.candidate_pool_size`, `training.params.candidate_epochs`.

Both are real, overridable config keys — `candidate_epochs` is projected at
`juniper-cascor/src/main.py:278` and consumed at `cascade_correlation.py:722`.
`spiral-smoke.yaml` sets `candidate_pool_size: 4` and leaves `candidate_epochs` to its constant
default, so the latter must be set explicitly in the base or every cell inherits a fallback.

**Why this axis is expected to move when the dataset axis did not.** `step_count` is invariant
across dataset size, but the candidate phase's epoch count is **emergent** — the same finding
that D6 rests on (`test_micro_candidate.py:52-54`; requested 100 and requested 200 both completed
68). A patience-based early-stopping loop terminates where the numerics take it. That is a
quantity a matrix can actually move.

**Mandatory instrumentation**: record **`epochs_completed` per cell**, not just wall time.
cascor#531's decomposition shows a thread-budget change moving epoch count **1.21× → 1.03×**
independently of throughput; an axis that changes the candidate budget will do the same. A cell
that is faster per epoch and runs more epochs is *slower*, and a wall-time-only reading reports
the opposite.

**Calibration needed**: none beyond the existing floor/wall rule — the candidate phase already
runs at full length under the smoke base (`ml#1069`: the base caps `max_epochs` but not
`candidate_epochs`).

> ## ⚠ 2026-09-23 — the instrument this axis requires does not exist on the suite path
>
> **No structured artifact of a suite run carries a candidate's `epochs_completed`.** Checked on a
> 2026-09-23 axis-2 run (`20260923T142858Z-6371`):
>
> - `metrics_final.json` has no such field;
> - `metrics_history.json`'s records are `output_epoch` / `training_step` kinds only;
> - `metrics_series.csv` has none of the cascor Prometheus columns for it.
>
> cascor computes the count (`TrainingResults.epochs_completed`, `cascade_correlation.py:154`)
> and never publishes it.
>
> **Only the log carries it, and only half of it.** `logs/juniper_cascor.log` has one
> `CandidateUnit: train: Training candidate unit for <E> epochs` line per candidate (the
> request). It has a `CandidateUnit: train: Early stopping at epoch <N>` line only for a candidate
> that stopped early. A candidate that ran its whole budget writes nothing, so its count is an
> inference from an ABSENT line. That run had 8 candidates and 2 stop lines (epochs 55 and 56), so
> **6 of 8 ran the full `candidate_epochs` 400.** Under spiral-smoke the counts are mostly
> budget-bound, as D1's debt measurement predicted: counts were emergent in 94 of 100 candidates
> only at `candidate_epochs` 2000.
>
> **Before this axis is committed, choose the instrument** (a decision this document does not
> take):
>
> 1. **Parse the log.** It works on today's cascor, but log formats are being redesigned right
>    now (the logging arc's P0.4 envelope). Absence is load-bearing, so a format change that drops
>    the stop line would silently read as "every candidate ran its budget".
> 2. **Publish it.** Add a structured per-phase record in cascor, for example a `metrics_history`
>    entry carrying each candidate's `epochs_completed`. This is a small cascor change, and the
>    only option that does not rest on an absent line.
>
> Either way, the base must set `candidate_epochs` to about 2000, or the axis measures its own
> budget.

---

## 3. Axis 2 — wall-time characterisation over a wide dataset range

**Key**: `dataset.params.n_points_per_spiral`, **250 → 500,000**, in-process path only (§1).

This is a characterisation run, not a comparison: the question is the *shape* of wall time against
dataset size, and **where it stops being viable**. Two design consequences:

- **`continue_on_failure: true` and a raised `max_wall_seconds`.** The base sets
  `max_wall_seconds: 600`; the top of this range will exceed it. **That is a result, not a
  failure** — the cell that first breaches the wall is the measurement. A suite that aborts on the
  first breach throws away the answer.
- **Report the breach explicitly.** A run that hit the wall must be distinguishable in the
  aggregate from one that completed, or the curve silently flattens at the budget rather than at
  the machine's limit — the "downstream clamp absorbs the mutation" failure.

**Calibration needed**: the *upper* end. 500,000 × 2 spirals is 1,000,000 rows; the initial output
pass alone is then four orders of magnitude larger than anything this lane has measured. A probe
should establish the largest cell that completes inside a chosen wall before the full sweep is
committed, exactly as PF-1 reached 4000 epochs by probing 500 / 2000 / 5000.

> ## RESULT 2026-09-23 — no knee inside the suite path's range; the in-process follow-up does not fire
>
> Suite: `util/experiments/suites/perf/pf2-axis2-cascor-dataset-range.yaml`. 18 cells (6 sizes ×
> 3 round-robin passes), cascor `0d2d826`, 1-minute load 5–8, all 18 succeeded.
>
> - Reducer: `util/ad-hoc/2026-09-23_pf2_axis2_reduce.py`.
> - Evidence: `~/.local/state/juniper-experiments/suites/pf2-axis2-cascor-dataset-range-20260923T142812Z/`.
>
> | n/spiral | wall, median (s) | `step_sum`, median (s) |
> |---|---|---|
> | 250 | 24.14 | 4.125 |
> | 500 | 21.73 | 4.109 |
> | 1,000 | 23.95 | 4.558 |
> | 2,000 | 24.10 | 4.127 |
> | 4,000 | 24.24 | 5.130 |
> | 5,800 | 24.35 | 5.409 |
>
> - **Wall time is flat**: ×1.01 across the 23× range. It is dominated by stack bring-up, data
>   staging, collection and plots, not by the dataset.
> - **Training compute grows ×1.31.** The log-log slope between neighbouring sizes stays between
>   −0.15 and 0.31: strongly sublinear, **with no knee**.
> - **Under the owner's D4 ruling** ("in-process later, only if the curve shows a knee"), **the
>   in-process follow-up does not fire.**
> - **Scope:** `spiral-smoke`'s budgets. That means 2 hidden units, `output_epochs` 50, and a
>   `step_count` of 8 in every cell, fixed by the budget and never compared. How wall time scales
>   with dataset size at LARGER budgets is a different question from the one ruled on.

---

## 4. Axis 3 — number of spirals (the owner's preferred axis)

**Key**: `dataset.params.n_spirals`, range **2 … 10** (`MAX_SPIRALS`; §1), probably 2 … 6.

This is a **difficulty** axis rather than a size axis, which is why it is expected to be the more
informative one: adding spiral arms makes the classification problem harder in a way that should
move the *emergent* quantities (hidden units grown, candidate epochs, iterations to convergence)
rather than only the per-step cost.

> **⚠ The blocking calibration, and the reason this axis cannot be committed as written.**
> `spiral-smoke.yaml` sets `max_hidden_units: 2` and `max_iterations: 2`. A 10-spiral problem
> cannot be solved with two hidden units — **every high-spiral cell would terminate at the cap**,
> and the suite would measure the cap rather than the difficulty. That is the *same failure class*
> as the inert dataset axis this re-spec exists to replace: a matrix whose cells differ in the
> input and agree in the output.
>
> A capacity calibration must therefore run **first**: find the `max_hidden_units` /
> `max_iterations` budget at which 2 … 10 spirals produce *different* outcomes. If no such budget
> exists inside a tolerable wall, the axis is not viable and should be said so rather than run.

**Mandatory instrumentation**: hidden units grown and iterations completed per cell, alongside
wall time. Those are the quantities difficulty should move.

### 4.1 CALIBRATION RESULT, 2026-09-15 — the axis is VIABLE, but not on the observable expected

Ran: `util/ad-hoc/2026-09-12_pf2_spiral_capacity_calibration.yaml`, 6 cells, all succeeded.
Reduced by `util/ad-hoc/2026-09-15_pf2_capacity_reduce.py`. Evidence:
`~/.local/state/juniper-experiments/suites/pf2-spiral-capacity-calibration-20260916T002823Z/`.

| n_spirals | max_hidden | n_samples | hidden grown | epoch | test f1 | test roc_auc |
|---|---|---|---|---|---|---|
| 2 | 2 | 680 | 2 | 3 | 0.5750 | 0.7202 |
| 6 | 2 | 2040 | 2 | 3 | 0.1556 | 0.5645 |
| 10 | 2 | 3400 | 2 | 3 | 0.0651 | 0.5410 |
| 2 | **16** | 680 | 16 | 17 | **0.8997** | **0.9605** |
| 6 | 16 | 2040 | 16 | 17 | 0.1761 | 0.6130 |
| 10 | 16 | 3400 | 16 | 17 | 0.0854 | 0.5555 |

**1. The structural observables cannot discriminate — they are pinned to the budget.**
`hidden_units` grown equals `max_hidden_units` in **all six** cells, and `epoch` is
`max_iterations + 1` in all six. The network **saturates its capacity at every spiral count**, so
§4's "mandatory instrumentation" above is, on its own, useless here: reading a constant column
across the axis and reporting "no difference" measures nothing. `step_count` is worse still — it
is 8 and 50 purely by budget, invariant across `n_spirals`, which is the *same* size-invariance
PF-2 is being re-specified to escape (`n_spirals` changes dataset size: 680 → 2040 → 3400 rows).

**2. Difficulty DOES express — in accuracy.** `test roc_auc` spread across the spiral axis is
**0.179** at budget 2 and **0.405** at budget 16. That is a large, clean signal and it is
monotone in the right direction. **Accuracy is the observable for this axis.**

**3. The evaluatable range is NARROWER than expected, and capacity does not widen it.** Only
`n_spirals: 2` is solved (roc_auc 0.9605). Six is 0.6130 and ten is 0.5555 — both near chance,
**at the larger budget**. Raising capacity 2 → 16 units rescues only the 2-spiral case
(0.720 → 0.961); at 6 it moves 0.565 → 0.613 and at 10 just 0.541 → 0.556. So the owner's
estimate ("certainly ≤ 10 and probably ≤ 6") is directionally right but **optimistic at these
budgets**: the interesting transition is already complete between 2 and 6.

**Consequences for the axis as specified:**

- **Sample densely at the low end — 2, 3, 4, 5 — not 2, 6, 10.** The transition happens there;
  6 and 10 are both flat near chance and would spend host time confirming the same "unsolved".
- **Gate on accuracy, report the structural columns as context.** The reverse would report an
  inert axis.
- **Something other than hidden-unit capacity binds at ≥ 6 spirals.** The obvious candidates are
  the smoke base's `output_epochs: 50` and its candidate budget, neither varied here. Until that
  is known, "6 spirals is intractable for cascor" is **not** a supported claim — only "6 spirals
  is unsolved at this budget" is.

> **The reducer's own first draft got this wrong**, and the way it did is worth keeping. It keyed
> its verdict on `hidden_units` alone, found the column constant, and printed *"this budget does
> NOT let spiral count express"* — the exact opposite of the truth, from a column that is
> structurally incapable of varying. The verdict now judges accuracy and labels the structural
> column as the non-discriminator it is.

### 4.2 RESULT 2026-09-23: difficulty separates 2 → 3 → 4, and 5 does not rank below 4

- Suite: `util/experiments/suites/perf/pf2-axis3-cascor-spiral-count.yaml`. 12 cells: `n_spirals`
  2, 3, 4 and 5 × 3 round-robin passes, at `max_hidden_units` 16 / `max_iterations` 16.
- Code: cascor `0d2d826` (the retained pin that PF-1 and axis 2 ran on), 1-minute load 8–15.
  All 12 succeeded.
- Reducer: `util/ad-hoc/2026-09-23_pf2_axis3_reduce.py`.
- Evidence: `~/.local/state/juniper-experiments/suites/pf2-axis3-cascor-spiral-count-20260923T202816Z/`.

| `n_spirals` | test roc_auc | test f1 | f1 ÷ chance (1/n) | val accuracy | hidden / epoch | wall, median (s) |
|---|---|---|---|---|---|---|
| 2 | **0.9605** | 0.8997 | 1.80 | 0.9187 | 16* / 17* | 39.1 |
| 3 | **0.8335** | 0.6674 | 2.00 | 0.6333 | 16* / 17* | 39.0 |
| 4 | **0.6721** | 0.3896 | 1.56 | 0.3844 | 16* / 17* | 44.3 |
| 5 | **0.7458** | 0.3380 | 1.69 | 0.3600 | 16* / 17* | 47.2 |

`*` budget-bound, as §4.1 predicted.

- **The three passes are bit-identical**, with test roc_auc spread 0.0000 at every `n_spirals`.
  The accuracy outcome is deterministic under `seed_policy: fixed` and unaffected by load 8–15,
  so this axis's observable does NOT need a quiet host. **The corollary limits every claim
  below:** identical passes measure determinism, not seed variance. This is **n = 1 seed.**
- **Difficulty separates 2 → 3 → 4 cleanly** on every accuracy column. The 2-spiral figure
  reproduces §4.1's budget-16 cell exactly (0.9605).
- **5 spirals does not rank below 4.** Test roc_auc *rises*, 0.672 → 0.746. Raw test f1 still
  falls (0.390 → 0.338), but less than chance does (1/4 → 1/5), so chance-adjusted f1 also rises
  (1.56 → 1.69). With one seed this inversion could be a property of that seed's dataset and
  initialisation, so it is **not** a claim about 5-spiral difficulty. The reducer's "monotone"
  verdict reports NO, correctly.
- **No cell is within 0.10 of chance** (roc_auc 0.5). §4.1's near-chance cells were 6 and 10, so
  the evaluable range at this budget ends somewhere between 5 and 6.
- **What would settle the 4/5 question**: a seed axis (`seed_policy: per_cell`, or an explicit
  seed key) crossed with 4 and 5. Accuracy is load-insensitive, so it can run on a loaded host.
- **Which accuracy column to gate on** (roc_auc, raw f1 or chance-adjusted f1) is a threshold
  question, and thresholds are unratified. The columns already disagree at 4/5, which is the
  argument for deciding before gating.

### 4.3 SEED PROBE 2026-09-24: the 4/5 inversion was the seed, and one seed cannot order neighbours

Probe `util/ad-hoc/2026-09-24_pf2_axis3_seed_probe.yaml`: `n_spirals` 4 and 5 × 5 dataset
seeds, at the same budget and cascor pin, on a loaded host. All 10 cells succeeded. Reducer:
`util/ad-hoc/2026-09-24_pf2_axis3_seed_probe_reduce.py`. Evidence:
`~/.local/state/juniper-experiments/suites/pf2-axis3-seed-probe-20260924T075038Z/`.

**Only the DATASET seed varies.** The cascor service exposes no network `random_seed` on the
training path, so every cell initialises identically. This is a marginal over dataset draws, not
over initialisation.

| dataset seed | 4 spirals: test roc_auc / f1 | 5 spirals: test roc_auc / f1 |
|---|---|---|
| 101 | 0.6954 / 0.3966 | 0.6556 / 0.2882 |
| 202 | 0.8302 / 0.5539 | 0.6815 / 0.3571 |
| 303 | 0.7995 / 0.5800 | 0.6234 / 0.2563 |
| 404 | 0.6108 / 0.2673 | 0.5982 / 0.2415 |
| 505 | 0.6404 / 0.3591 | 0.6586 / 0.2930 |

- **The §4.2 inversion was the seed.** 4 spirals beats 5 on roc_auc for **4 of 5** seeds (median
  4 − 5 = +0.040), and on raw f1 for **5 of 5** (median +0.108). Chance-adjusted f1 is mixed at
  **3 of 5**: the gap between 4 and 5 is small next to the chance-level shift (1/4 → 1/5).
- **The seed spread dwarfs the neighbour gap.** At 4 spirals, roc_auc spans **0.611–0.830** over
  five dataset draws, about **5×** the median 4-vs-5 difference. §4.2's single seed (0.672 at 4)
  sits inside that spread.
- **Consequence for any gate on this axis:** a single-seed accuracy reading cannot order adjacent
  spiral counts. A threshold (unratified) would need several dataset seeds per cell and a paired
  comparison, or it gates on seed luck. The bit-identical passes of §4.2 never tested this,
  because a fixed seed repeats the same draw.
- **Not settled:** initialisation variance, which the service does not expose, and whether a larger
  budget narrows the spread.

---

## 5. What must be true before a matrix is committed

| axis | calibration | status |
|---|---|---|
| 1 — candidate phase | none beyond floor/wall | **BLOCKED on its instrument (2026-09-23, §2 note).** No structured suite artifact carries `epochs_completed`, and the log carries it only for candidates that stop early. **Owner ruled 2026-09-24: publish it in cascor** as a structured per-phase record, rather than parse the log. The base also needs `candidate_epochs` ≈ 2000 |
| 2 — wide dataset range | largest completing cell at a chosen wall | **DONE 2026-09-23.** Ruled "10,000 now, in-process later"; built capped at 5,800 (the suite path's real ceiling is 5,882, per the second §1 correction); **RUN, no knee** (§3 RESULT), so the in-process follow-up does not fire |
| 3 — spiral count | capacity budget that lets 2…10 differentiate | **DONE 2026-09-15 (§4.1)** — axis viable, but gate on **accuracy**; sample 2,3,4,5 not 2,6,10. **RUN 2026-09-23 (§4.2)**: separates 2 → 3 → 4 (test roc_auc 0.961 / 0.834 / 0.672). 5 scores 0.746, above 4, on one seed. Passes are bit-identical, so the observable is load-insensitive. **Seed probe 2026-09-24 (§4.3)**: the inversion was the seed. 4 beats 5 on roc_auc for 4 of 5 dataset seeds and on f1 for 5 of 5, but the seed spread (0.611–0.830 at 4) is about 5× the gap, so **a gate needs several seeds per cell** |

**Host condition.** All three are wall-clock measurements. The host has not been quiet in four
sessions (1-minute load 9–20 across the 2026-09-11 evidence files, with a 21-hour `clamscan`
running). Interleave or randomise arm ordering and repeat, or these measure the shell. Structural
outcomes — `step_count`, `epochs_completed`, hidden units grown — are load-insensitive; **wall
clock is not.**

---

## 6. What this document does not decide

- The cell counts, budgets and wall limits for any axis — those are the calibration above.
- Whether axis 2 should also be run against juniper-data at its own ≤ 10,000 cap, to compare the
  two generators. That is a separate question and a separate suite.
- Whether `MAX_POINTS` should be raised in juniper-data. Nothing here needs it; the in-process
  path already reaches the requested range.
