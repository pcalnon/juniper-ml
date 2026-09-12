# PF-2 re-specification: three axes to replace one that measured an invariant

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-12
**Status**: SPEC. Two axes need a calibration probe before any matrix is committed; one carries a path constraint the owner must see.
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
a request past them is a 422, not a clamp.

**Consequences for this spec:**

- The owner's requested **250 → 500,000** points-per-spiral range is reachable **only on the
  in-process path** — it is 50× past juniper-data's cap. `spiral-smoke.yaml` sets
  `auto_start_data_service: false` and `dataset.generator: spiral`, so the perf suites already
  take that path today.
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

---

## 5. What must be true before a matrix is committed

| axis | calibration | blocking? |
|---|---|---|
| 1 — candidate phase | none beyond floor/wall | no — specifiable now |
| 2 — wide dataset range | largest completing cell at a chosen wall | yes, for the upper end only |
| 3 — spiral count | capacity budget that lets 2…10 differentiate | **yes — the axis is meaningless without it** |

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
