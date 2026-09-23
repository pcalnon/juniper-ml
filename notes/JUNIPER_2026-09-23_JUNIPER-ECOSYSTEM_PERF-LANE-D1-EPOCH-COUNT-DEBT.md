# D1's epoch-count debt, paid: a BLAS cap of 2 leaves every count — and every bit — where the old default put it

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-23
**Status**: D1's epoch-count debt PAID — driver verdict **CLEAR**. A cap of 2 (`env2`) reproduces today's default bit-for-bit, in all 3 repeats, while the seed control and a sustained 16-wide training thread both move the counts. The D1 flip is cleared and lands in juniper-cascor (§5).
**License**: MIT License

---

## 0. What this document is

The measurement owner decision **D1** was gated on when it was ruled a second time, on
2026-09-23. The first ruling said "the process-wide default". The session then found that
mechanism already existed as `configure_blas_threads()`, defaulting to "do nothing" for
cascor#531's reason, and put the question again. The owner ruled **"pay the debt, then flip"**:
change the default to a cap of 2 only if an epoch-count measurement shows the cap does not move
the count. The ruling is recorded in §5 and §5.2 of
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md).

**The debt.** The D1 and D2 gates both demanded **epoch counts per phase**. The 09-16 width sweep
([`JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`](JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md))
emitted **stage** counts, so "cascor#531's penalty does not reproduce" rested on wall time alone.
Wall time cannot tell *no effect* from *two effects cancelling*. #531's second channel was the
**count**: a cap changes BLAS reduction order, which changes floating-point results, which moves
where a patience-based loop stops.

Instrument: [`util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py`](../util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py)
(driver and arm in one file). Reducer:
[`util/ad-hoc/2026-09-23_d1_epoch_debt_reduce.py`](../util/ad-hoc/2026-09-23_d1_epoch_debt_reduce.py).
Evidence: `~/.local/state/juniper-experiments/suites/d1-epoch-debt-20260923/`, with one
`r<rep>-<arm>.json` per arm and the driver's `debt.json`.

---

## 1. The 09-16 measurement could not have answered this, for a second reason

Beyond emitting stage counts, **every structural count it had was pinned to its budget**, so none
of them could have moved:

- `max_iterations=4` grew exactly **4 hidden units in all 39 arms**.
- The output loop in `train_output_layer` is `for epoch in range(epochs)` with **no early exit**,
  so output epochs always equal the request, in every arm, by construction.

A count that equals its budget cannot show a count channel. That is the same lesson as D6's
budgets 10 and 50. Adding an `epochs_completed` field to that arm would have been a vacuous
repair.

## 2. The instrument

**Budgets, calibrated before the matrix.** A control arm at `candidate_epochs=400` left **38 of
40** candidates at their budget. At **2000** (with `max_iterations=max_hidden_units=25`),
**94 of 100** stopped early. Per-candidate `epochs_completed` is emergent there. Hidden units
still reach their budget (25/25) and output epochs are budget-bound by construction. Both are
reported, and neither is treated as evidence.

**Five arms**, all with `worker_thread_count=1`, so candidate workers pin themselves to 1 thread
whatever the environment says:

| arm | what it runs |
|---|---|
| `none` | **today's default.** No BLAS variables. The constructor pins only its own thread, so the training thread enters at the runtime default (ICV 16) until the first candidate collection re-pins it to 2 |
| `env2` | **the flip.** `OMP`/`MKL`/`OPENBLAS_NUM_THREADS=2` before torch loads, which is exactly what the new default produces |
| `env16` | the same route at 16 |
| `thread16` | `torch.set_num_threads(16)` on the training thread, which keeps it at 16 for the whole run |
| `seed` | `none` with the network's `random_seed` changed (42 to 7): the **positive control** |

**Compared on COUNTS**: the owner's criterion. A second **numerics** column (the winning candidate
of every phase, best correlations, final loss) explains the counts. Identical numerics is a
stronger statement than identical counts. Wall clock is recorded and never compared. The order
is shuffled each repeat from a recorded seed (20260923); the repeats test determinism. Every
cell ran against cascor **`0d2d826`** from a detached, clean worktree, on JuniperCascor1 (Python
3.14.7, torch 2.11.0).

## 3. Result

**Driver verdict: `CLEAR -- env2 reproduces the default exactly and the seed control moves; the
flip is cleared`.**

- 15 of 15 arms succeeded, and `nondeterministic_arms` is empty.
- In the control, **94 of 100** candidates stopped below the 2000-epoch budget, so the compared
  count is emergent.
- Hidden units (25/25) and output epochs are budget-bound. They are reported below but are not
  evidence.

| arm | counts = `none` | numerics = `none` | same in all 3 repeats | final loss | ICV at train entry → exit | first divergence from `none` |
|---|---|---|---|---|---|---|
| `none` (today's default) | — | — | yes | 0.0067392201 | 16 → 2 | — |
| **`env2` (the flip)** | **yes** | **yes: bit-identical** | yes | **0.0067392201** | 2 → 2 | none |
| `env16` | yes | yes: bit-identical | yes | 0.0067392201 | 16 → 2 | none |
| `thread16` | **no** | no | yes | 0.0053551188 | 16 → 16 | candidate phase 20: `[2000, 1202, 1450, 1326]` → `[2000, 1202, 1442, 1326]` |
| `seed` (positive control) | **no** | no | yes | 0.0051697553 | 16 → 2 | candidate phase 0: `[474, 462, 497, 462]` → `[476, 476, 452, 446]` |

"Numerics" means the winning candidate of every phase, every phase's best correlation to 10
decimals, and the final loss. The ICV column is `omp_get_max_threads()`, read through `ctypes` on
the training thread. It is what shows each arm really ran at the width it claims: `env2` enters
at 2; `none`, `env16` and `seed` enter at 16 and are re-pinned to 2; `thread16` stays at 16.

Wall time is in every record and is **not** a result here. `fit_seconds` ranged 99–232 s for
`none` alone, across 1-minute loads of 9–23.

## 4. What it means

- **The flip is count-neutral and bit-neutral against today's default on this workload.** `env2`
  reproduces `none`'s counts, winning candidates, correlations and final loss (0.0067392201)
  exactly.
- **The instrument could see a difference.** The `seed` arm diverges from the first candidate
  phase, so an unchanged count here is evidence, not an insensitive instrument.
- **#531's epoch channel is REAL, and it needs sustained width.** `thread16` holds the training
  thread at 16 for every pass. It reproduces `none` for twenty candidate phases, then one
  candidate stops at 1442 epochs instead of 1450 (phase 20), and the final loss moves to
  0.0053551188. `env16` starts at 16 but is re-pinned to 2 like `none`, and it stays
  bit-identical. So the width of the *initial* pass does not reach the numerics on this workload,
  and width held through the later passes does. **The likeliest mechanism is UNTESTED:** by phase
  20 the output layer's input has grown to 22 features, plausibly past the size at which 16
  threads split a reduction differently. Nothing here isolates operation size from the number of
  passes, so treat it as a hypothesis. The conclusion does not depend on it. The flip moves the
  default away from width, and so away from the channel either way.
- **The old default's cost is wall time, not correctness, here.** Its first output pass runs
  16-wide. In repeat 0, at 1-minute load 16–28, the first pass took **12.30 s** under `none` and
  **8.42 s** under `env16`, against **1.49 s** under `env2`. That is one repeat on a loaded host
  and not a figure to quote. The direction agrees with the 09-16 sweep's −49.2%.

### What is NOT claimed

- **Not every workload.** This is one workload: 2 spirals × 200 points, 320 training rows,
  pool 4, 25 units, `candidate_epochs` 2000. A second, independent datum points the same way.
  PF-1's `step_count` is **1770** unpinned (baseline `pf1-2026-09-04b`, cascor at its 09-03 tree)
  and **1770** capped at 2 (`pf1-2026-09-23-blas2`, cascor `0d2d826`). A workload whose FIRST
  output pass is large enough to parallelise could differ between `none` and `env2`. The flip
  would then change its numerics, in the direction of fewer threads.
- **Not a timing result.** Every `fit_seconds` in the evidence was taken at load 16–31.
- **Not "deterministic" in general.** It is invariant here across repeats, within a fixed tree
  and seed.

## 5. What follows

- **The flip lands in juniper-cascor.** `configure_blas_threads()` now defaults to 2. It only
  sets variables that are unset, and `JUNIPER_CASCOR_BLAS_THREADS=0` / `off` / `none` opts out
  to the old behaviour. The PR is juniper-cascor#683 (`perf/d1-blas-default-two`, opened 2026-09-23).
- **D2's gate asked for the same thing and is paid by the same data**, for the environment route
  it ruled for. Its item 4 was "epoch counts per phase". At widths 2 and 16 the environment route
  leaves every count, and every bit, where the default puts it.
- **One question stays open, and it is about scope, not about this workload.** A workload whose
  FIRST output pass is large enough to parallelise could differ between `none` and `env2`.
  PF-2 axis 2's larger datasets are where to look. The test is structural and runs on a loaded
  host: run one cell with the new default and one with `JUNIPER_CASCOR_BLAS_THREADS=off`, then
  compare `step_count`.

## 6. Reproduction

```bash
python3 util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py \
  --cascor-src <juniper-cascor>/src \
  --out-dir ~/.local/state/juniper-experiments/suites/d1-epoch-debt-<YYYYMMDD> \
  --repeats 3 --candidate-epochs 2000 --max-iterations 25 --max-hidden-units 25
python3 util/ad-hoc/2026-09-23_d1_epoch_debt_reduce.py ~/.local/state/juniper-experiments/suites/d1-epoch-debt-<YYYYMMDD>
```

**Stop conditions.** If the `seed` arm reproduces `none`, the verdict is VACUOUS: raise the
budgets. If repeats of one arm disagree, the verdict is NONDETERMINISTIC and an exact comparison
is unsafe. The driver prints either verdict itself.

## 7. Provenance

Measured 2026-09-23 (UTC 13:09 onward) against cascor `0d2d826b2818` from
`worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b`, which was clean
(`git status --porcelain` empty). cascor `main` had moved to `6276c45` by the time of the flip.
The intervening commits (#676, #680, #681) touch `src/api/` and `src/profiling/logging_utils.py`
only, and nothing in `candidate_unit/` or `cascade_correlation/`.
