# `epochs_completed` is deterministic: 100 runs, zero variance — an exact-match gate is safe

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-17
**Status**: D6's gating measurement DONE. The value is stable; the decision to build the gate is the owner's.
**License**: MIT License

---

> ## ⚠ COMMITTED 2026-09-22 BY A LATER SESSION — read this as corroboration, not as the record
>
> This note and its instrument were written 2026-09-17 and **never committed**. For five days
> their only copy sat untracked in `.claude/worktrees/optimized-giggling-koala/`, which the
> 09-11 handoff called locked. **It was not locked**: probed 2026-09-22,
> `.git/worktrees/optimized-giggling-koala/` has no `locked` file. `git worktree remove` would
> have deleted both files.
>
> They are committed so the 09-17 evidence
> (`~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260917/spread.json`) keeps the
> instrument that produced it. That follows the ad-hoc retention policy
> ([`util/ad-hoc/README.md`](../util/ad-hoc/README.md), owner decision 2026-08-25), under which
> retiring a script is owner-directed only. **Everything below this block is verbatim**: the
> original note's sha256 is `acfc899b4cef42326cf8e2ef9bc58ba74a73e4da71ec20239bb517d74744d015`.
> The instrument
> ([`util/ad-hoc/2026-09-17_epochs_completed_spread.py`](../util/ad-hoc/2026-09-17_epochs_completed_spread.py))
> is the worktree copy **minus one line**. CodeQL flagged `import statistics` as unused, which
> blocked the merge, so that import was removed and nothing else changed. The original sha256 was
> `a65150de4daf709251cb3d4051818b12affc95cc4c746002c00d3d2863d1a116`; the committed file's is `0037bc0d80d7463f4f238b2e26a05bcc9c411af8837c4d90094ddd5c3e1cc25c`. The removed line cannot change what the script
> computes.
>
> **The document of record for D6 is
> [`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`](JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md)**.
> It reproduces this result with an instrument that also records the OpenMP ICV in force at each
> cell, and it runs a do-nothing control. Do not quote three things from the body below:
>
> - **§4's "safe to build" is not the whole story.** The 09-22 note §4 adds that the gate's
>   reference is **tree-sensitive by construction**: it fires on any cascor change that moves
>   candidate numerics. Whether that is its value or its cost is unmeasured, and **whether to
>   build the gate at all is still the owner's call**. D6 bought the measurement, not the gate.
> - **This instrument cannot tell an inert axis from a real invariance.** It sets width with
>   `torch.set_num_threads` and reads it back with `torch.get_num_threads()`, which re-pins the
>   caller (the 09-22 note §2.2). It records neither the ICV in force nor a control arm. Its
>   "constant across widths" is therefore corroborated, not established, by this run. The
>   09-22 note §2.1 is what establishes it.
> - **The load figure is not in this note.** The spread.json records 1-minute load **19.50**.
>   The 09-22 note §6 compares that with its own runs at 32.26 and 12.08.

## 0. What this document is

The measurement gating owner decision **D6** of
[`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md).

D6 asks whether a work-style **exact-match** gate on `epochs_completed` is safe for the candidate
micro-benchmarks — the micro analogue of the run tier's split gate. The owner ruled **"re-measure
first"**, because the reference looked unstable: the 2026-09-07 validation observed requested-100
completing **52** in one round and **68** in another, and a gate whose reference moves with ambient
conditions is a flaky gate.

Instrument: `util/ad-hoc/2026-09-17_epochs_completed_spread.py`. Evidence:
`~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260917/spread.json`.

---

## 1. The hypothesis, which was not "is it random"

`tests/performance/test_micro_candidate.py` calls `torch.manual_seed(42)` **inside** the
benchmarked closure, and `_make_data` seeds again. The arithmetic is fully seeded, so any variance
is **not** seed noise.

cascor#531 supplies a mechanism that fits exactly: thread count changes BLAS reduction order,
hence floating-point results, hence **where a patience-based early-stopping loop terminates**
(`parallelism/blas_threads.py`). `train_detailed` early-stops when correlation plateaus — precisely
such a loop. So the question was **"is `epochs_completed` a function of thread width?"**, which has
two opposite consequences:

| finding | consequence |
|---|---|
| deterministic at a fixed width, differs across widths | gate is safe **if** it pins the width, and the width joins the reference |
| varies at a fixed width | genuinely nondeterministic; exact-match unsafe, decision closed |

---

## 2. Result: constant everywhere

5 widths × 4 epoch budgets × 5 repeats = **100 runs**. `epochs_completed`, every run:

| requested epochs | width 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| 10 | 10 | 10 | 10 | 10 | 10 |
| 50 | 50 | 50 | 50 | 50 | 50 |
| **100** | **68** | **68** | **68** | **68** | **68** |
| **200** | **68** | **68** | **68** | **68** | **68** |

**Zero variance — within any width, and across all of them.** Neither branch of §1's table
applies: the value is not merely deterministic *given* a width, it is independent of width.

Two things this confirms:

- **The emergent thesis stands.** Requested 100 and requested 200 both complete **68** — two
  different budgets landing on the same early-stopping point, which is what makes `epochs_completed`
  structurally like `step_count` rather than a constant fixed by the test. At 10 and 50 the loop
  never plateaus, so the count equals the budget; the emergence only appears above ~68.
- **cascor#531's epoch-count channel does not reach this benchmark.** Width moves nothing here,
  consistent with the thread-width sweep finding no candidate-phase cost at any cap
  (`JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md` §2).

## 2.1 The gate's operating point is already pinned

`tests/performance/conftest.py:81-84` sets `torch.set_num_threads(BENCHMARK_THREAD_PIN)` **and**
`OMP_NUM_THREADS` / `MKL_NUM_THREADS`, with `BENCHMARK_THREAD_PIN = 1`
(`tests/performance/timing_reference.py:61`). So the suite already pins the one mechanism that
could plausibly have moved the value — and width 1 is measured above at a stable 68.

---

## 3. The 52 does not reproduce, and is not explained

The 2026-09-07 round-1 observation of requested-100 → **52** did not appear in any of these 100
runs. That session's own round 2 could not reproduce it either (it got 68), and its handoff already
said so, flagging the exact numbers as untrustworthy while treating the *thesis* as established.

**The most economical reading is that 52 was an artifact of that single round**, but this document
does not *establish* that — it establishes only that 52 does not occur under any width, at n=100,
on the current tree. Two changes since make a version effect possible and unexcluded: cascor moved
0.9.0 → 0.11.0, and the environment moved Python 3.13.13 / numpy 2.4.4 → 3.14.7 / numpy 2.5.3.

**Consequence for the gate**: this does not weaken the safety case. A work gate is *supposed* to
fire when the algorithm changes the work — that is the whole point — and it would be re-cut on such
a change like any reference.

---

## 4. Recommendation (the decision remains the owner's)

**An exact-match gate on `epochs_completed` is safe to build**, scoped to the candidate
micro-benchmarks:

- The value is stable at n=100 across a 16× width range.
- The suite already pins thread count and the BLAS variables, so the one known mechanism that
  could move it is controlled.
- Only **1 of the 5** cascor micro files is affected; the other four are genuinely fixed-count and
  need no gate either way.
- The useful budgets are **100 and 200**, where the count is emergent (68). At 10 and 50 the gate
  would assert the budget back to itself — a vacuous check that would pass forever and prove
  nothing.

**What it must record alongside the reference**: the cascor version and the thread pin. Without
those, a legitimate algorithm change reads as a flake, which is how work gates get disabled.

---

## 5. What is NOT claimed

- **Not** that 52 was impossible — only that it does not occur in 100 runs on the current tree (§3).
- **Not** that `epochs_completed` is width-independent in general. Measured for *this* benchmark's
  shape (input_size 2, 100 samples, lr 0.005, tanh). cascor#531 measured a width effect on the
  epoch count of the full candidate phase, which is a different workload.
- **Not** a timing claim. Nothing here depends on wall clock, which is why a loaded host is
  acceptable for this measurement where it is not for the width sweep.

---

## 6. Reproduction

```bash
env -C <cascor>/src -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS \
    /opt/miniforge3/envs/JuniperCascor1/bin/python \
    util/ad-hoc/2026-09-17_epochs_completed_spread.py --widths 1 2 4 8 16 --repeats 5
```

**Stop condition.** If any row reports `NO -- VARIES`, the value is not deterministic at a fixed
width and §4's recommendation is void regardless of what the cross-width comparison says.
