# Perf lane — PF-8 needs no harness, the micro timing reference exists, and PF-2 was probed

Successor to the P2 plan's Wave 2 and Wave 4 rows
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md))
and to §1 items 2–4 of the 2026-09-07 handoff
([`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09/HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md)).
Item numbers below refer to the P2 plan unless stated otherwise.

**Three things happened, in the order the handoff required.** Item 4.3 was answered before any
harness was built, and the answer is that **no harness is needed** — the one Wave 4 planned to
build already exists inside `run_suite` (§1). Item 2.4 shipped: a cascor micro-tier **timing
reference** exists for the first time, cut twice on the workstation, report-only by the owner's
2.5 ruling (§2). Item 2.1's **probe ran** — the measurement the handoff said must precede any
epoch number — and §4 records what it found. Three false phrases inherited across two handoffs
were corrected at their sources (§3).

---

## 0. What this closes and what it leaves

| item | state after this document |
|---|---|
| **4.3** | **DONE** — PF-8 reconciled with the sweep; re-scoped in §1 |
| **4.1** | **WITHDRAWN as a build item** — the concurrent-launch harness exists: `run_suite` parallel mode (§1.2). What remains of 4.1 is an occupancy probe, S not L (§1.3) |
| **4.2** | **Re-specified** (§1.4) — a suite *pair*, not a descriptor; blocked on a CI-only hazard the drift gate would otherwise turn red on (§1.5) |
| **2.4** | **DONE** — `juniper-cascor#638` (branch `feat/perf-micro-timing-reference`); reference cut twice, `0001` and `0002`, both provisional (§2) |
| **2.1** | Probe **executed** — §4. One value (4000/4000) clears both ends, trivially: **the dataset axis is inert** across the whole PF-2 range — identical `step_count` and flat step time at 250 and 2000 points — so PF-2 as designed measures an invariant. Re-scoping the scenario is an owner call; the suite file is **not** edited by this document |
| **2.2** | Untouched — still needs the quiet window §5 shows this session did not have |
| **2.3** | Untouched, report-only forever for the closed-form readouts (the MLP readout's `n_epochs_` counter is the carve-out the handoff restored; nothing here changes it) |

---

## 1. Item 4.3 — PF-8 reconciled with the headroom sweep

### 1.1 What the sweep already settles, and what it cannot

§8.4 of the instrument-resolution note
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md))
answers PF-8's two halves very differently.

**The work half is closed.** `step_count` was 804 in all 21 sweep cells, at every load level,
across a 3× span of step duration. A second Juniper run is a load; a load does not move the
count. PF-8 therefore has **no gate content** — it cannot produce a work-gate finding the sweep
has not already produced at strength, and speed is structurally ungated (decision 2 of §7 of the
sweep note, re-confirmed by item 2.5). Whatever PF-8 measures is **advisory**: it informs whether
two runs may share the host without invalidating each other's *speed report*, and nothing else.

**The speed half is characterised but not located.** The sweep gives the response curve in
*synthetic-worker* units — ≤ 6 workers not separable from the 20.5% quiet band, 8 and 10 on a
plateau at +86%, 12 at +182% — and §9 of the same note says why that is not a free-core figure:
ambient occupancy was neither zero nor constant. What is missing is **where one Juniper run sits
on that axis**. A cascor run under `spiral-smoke.yaml` is a uvicorn service, a forkserver, and a
candidate pool of 4 with `runtime.blas_threads: 2`; its worker-equivalent has never been measured.
If it is ≥ 8, the second run's cost is the plateau (+86%) and the sweep already says so; if it is
≤ 6, the cost is below what this host can measure — also already known. **Only if it lands near
the knee does a two-run measurement add information**, and the sweep's own §8.4 warns that a
+19.9% effect against a 20.5% band "carries no information".

That is the re-scope: PF-8's marginal value is not *"what does a second run cost"* in the
abstract — it is **locating one run on the sweep's axis**, and only then, conditionally, a
two-arm measurement.

### 1.2 The harness Wave 4 planned to build already exists

Item 4.1 was sized **L** on the premise (inherited verbatim from §3 of the P1 design,
[`JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`](JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md))
that *"cascor `parallel > 1` is still refused from one checkout"*. **That premise was stale when
the P2 plan was written.** `util/experiments/run_suite.py` lifted the blanket refusal on
2026-08-30 — the first cascor release carrying `JUNIPER_CASCOR_LOG_DIR` (cascor#523, 0.10.0) —
and replaced it with a **fail-closed version floor** read from the tree that will actually be
launched, not from the driver's environment (`CASCOR_PARALLEL_FLOOR = (0, 10, 0)`,
`_cascor_tree_version`). The primary checkout is 0.11.0.

Verified, not inferred. A two-cell parallel cascor suite — PF-1's `(10, 10)` / 4000-epoch cell
twice, `execution: {mode: parallel, max_parallel: 2}` — dry-runs to **exit 0** from this session
worktree with `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` set (the
scratch suite is not committed; §1.5 says why). What the run would get for free:

| PF-8 requirement (item 4.1's wording) | already provided by |
|---|---|
| "disjoint port ranges" | `experiment_stack.bash --up` per cell allocates from `8230–8259` (cascor) / `8110–8139` (data) behind a lock directory, first free port wins |
| "pinned, equal thread budgets" | `thread_budget_env("cascor", 2)` exports `CASCOR_NUM_PROCESSES=4` and the three BLAS variables at `2` to **both** cells; recorded per cell in `registry.jsonl` (`thread_budget`) and in each manifest (`environment.thread_env`) |
| "collect both" | the same `registry.jsonl` / `aggregate.csv` / `REPORT.md` every suite writes |
| "must not reuse the sweep driver's naive teardown" | each cell tears down its own stack by pid file (`--down RUN_ID`); the sweep's `kill -KILL` on a *driver* was the ad-hoc load script's defect, not `run_suite`'s |

So 4.1 as a build item is **withdrawn**. The plan's dependency edge `4.3 → 4.1 → 4.2` collapses
to `4.3 → 4.2`.

**What this reinterprets, stated so a reader of this note alone sees it** (consensus finding,
2026-09-09). §3 of the P1 design phrased PF-8 as needing *two suites at once* and declared
`execution.mode: parallel` insufficient on exactly that ground. Two identical cells of **one**
suite *are* two simultaneous runs, so the requirement is met by reinterpretation, not literally —
the P2 plan's Wave 4 preamble carries the dated correction.

### 1.3 What PF-8 is now — an occupancy probe first, a two-arm suite only if needed

**Step 1 (S, no new tooling).** During one ordinary PF-1 cell, sample the CPU occupancy of the
cascor process tree (the uvicorn pid, its forkserver, and the forkserver's children) at 1 s, and
express the mean as worker-equivalents — one sweep worker is one `sha256sum` process, i.e. one
saturated core. `run_experiment.py` does not record this today; a per-process `/proc/<pid>/stat`
delta over the cell is enough, and `ps %CPU` is **not** (it is a lifetime average). Read the
second run's cost off the sweep curve at that abscissa.

**Step 2 (M, only if step 1 lands in the ~4–8 worker-equivalent band around the sweep's
6–8-worker knee — below 6 the sweep cannot separate, above 8 it is the plateau).** A suite
**pair**:

- *parallel arm* — two identical PF-1-shape cells, `mode: parallel, max_parallel: 2`;
- *control arm* — the same two cells, `mode: sequential`, run with the **same four thread
  variables exported in the shell** (`run_suite` applies `thread_budget_env` only in parallel
  mode, so the control must pin by hand or the arms differ in budget, not only in concurrency —
  `compare_baseline`'s `thread_budget` identity field would refuse the comparison, which is the
  right outcome for a mismatched pair).

Two things the pair does not settle by itself (consensus finding, 2026-09-09). Each parallel cell
brings up its **own** juniper-data instance as well as its own cascor — `experiment_stack.bash
--up` launches data → cascor per cell — so the parallel arm is two data services too; probably
immaterial to what is measured, but unexamined. And start-time alignment is plausible (the
executor submits both cells back-to-back; the only serialisation point is the port lock's `mkdir`)
and unmeasured until a pair actually runs.

> **Measured 2026-09-10 — both steps ran.** Step 1: one PF-1-shape run consumes **4.52 cores**
> under the default budget — one ~11-core block in the listener for the *initial* output pass
> (before the candidate pool exists), then ~1.8 — and **2.15** under the pinned budget; the
> "one core = one sweep worker" equation this section makes is an assumption §8.4 of the sweep
> note disclaims, and the pair below measured the externality directly instead. Step 2, run
> because 4.52 is inside the band (§1.1 above had said ≤ 6 adds nothing, and the result agrees):
> three aligned parallel pairs against six sequential controls, same budget, all twelve cells at
> 1770 — **+11.3% per step, +8.5 to +12.7% leaving one pair out**, inside the 20.5% band, outside the
> day's within-arm spread by one pair's margin. The two unmeasured items above are now measured:
> start offsets were 0.003–0.068 s with ≥ 89% of the drive windows shared, and each parallel
> cell's own juniper-data instance stayed idle during training (its `data` column reads ~0.01
> cores). The ≥ 60 s cell length below was not met (35–45 s); the bridge was off.
> [`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md).

Instrument: **mean step duration** (`step_sum / step_count`) from the resolving instrument, never
`timings.drive` (poll-quantized; §1 of the sweep note). Design controls from §8.1 of the sweep
note carry over unchanged: quiet cells bracket the arms, and **n ≥ 3 per arm** — a 20.5% quiet
band cannot be beaten by one cell per arm. Cells at ≥ 60 s (PF-1's calibrated 4000-epoch pair),
so `step_sum` is fully resolved and the run is scrapeable if the bridge is on.

**What the result can and cannot say.** A parallel/control ratio outside the quiet band is a
located cost; inside it is *"below what this host can measure"* — a different statement from
"free", exactly as §9 of the sweep note says of modest load. Neither outcome changes a gate.

### 1.4 Item 4.2, re-specified

`perf/pf8-two-run-concurrency.yaml` becomes **two files** — `pf8-two-run-concurrency-parallel.yaml`
and `pf8-two-run-concurrency-control.yaml` — identical except for the `execution` block, plus a
README paragraph stating the four variables the control arm must export. Execution and evidence
as before. Size **M → S+M** (S for the pair, M for the runs and the occupancy probe).

### 1.5 The hazard that keeps the parallel suite out of the tree today

`tests/test_experiment_suite_yamls.py::test_every_suite_loads` calls `run_suite.load_suite` on
**every** `util/experiments/suites/**/*.yaml`, and `load_suite` is where the version floor is
enforced. In CI there is no cascor sibling: `_cascor_tree_version()` probes upward for
`juniper-cascor/pyproject.toml`, finds nothing, returns `None`, and the floor check **raises**
(fail-closed — deliberately, and correctly, for a launch). A parallel cascor suite committed under
`suites/perf/` therefore turns the R-6 drift gate **red on every CI run** while passing locally.
The recurrence suites are unaffected (no floor), which is why the gate has never seen this.

Three ways out, for the 4.2 implementer; none is taken here because each changes a gate:

1. **Keep the parallel arm under `util/ad-hoc/`** — the headroom sweep suite's precedent
   (`util/ad-hoc/2026-09-02_headroom_sweep_suite.yaml`). Zero code; PF-8 is then not a
   `suites/perf/` instrument, which contradicts §3 of the P1 design.
2. **Move the floor check from `load_suite` to the execution path** — still before any cell
   launches, still fail-closed, still reported by `--dry-run` — so structural validation (what the
   drift gate exercises) no longer needs a sibling repo. The cleanest fix; touches the guard that
   protects run evidence, so it needs its own negative tests.
3. **Have the drift gate set `JUNIPER_EXP_CASCOR_SRC_DIR`** to a fixture tree carrying a
   `pyproject.toml` at the floor. Hermetic, but it teaches the gate to lie about the tree that
   would launch.

The second is recommended. Until one lands, the dry-run evidence in §1.2 is the only artifact.

---

## 2. Item 2.4 — the micro timing reference exists

### 2.1 What was true before

**No cascor baseline file had ever held a timing figure.** The 2026-09-07 handoff measured the
live `baseline_20260526.json` (10 entries, zero timing keys) and called it *"gitignored with zero
commit history"*. True of that file; **false of the directory**: 21 baseline files
(`baseline_20260331.json` … `baseline_20260525.json`) were tracked and were deleted together in
cascor commit `971d35a` — a dependabot bump that also carried the deletion. Before writing "never"
into a document, every one of the 22 was read
(`util/ad-hoc/2026-09-08_cascor_baseline_history_census.py`): **312 entries, zero timing keys.**
`save_baseline`'s docstring had promised `mean_ms` / `stddev_ms` / `min_ms` / `max_ms` /
`iterations` since 2026-03-31; every caller passed only its parameters. That census reads each
file's final state; a consensus lane (2026-09-09) went further and swept the directory's whole
tracked history — `git log --all -p`, 45 commits — for `mean_ms` / `median_ms` / `stddev_ms` /
`min_ms` / `max_ms`, and found **none anywhere**, closing the added-then-reverted loophole a
snapshot census cannot see.

### 2.2 What shipped (`juniper-cascor#638`, branch `feat/perf-micro-timing-reference`)

- `src/tests/performance/timing_reference.py` — `benchmark_stats_ms` reads pytest-benchmark's
  seconds-denominated `Stats` off a completed `benchmark` fixture and returns the documented
  millisecond summary, `{}` when the fixture ran untimed; `collect_environment` adds `cpu_model`,
  the MKL/OpenBLAS pins, `loadavg_1m` and `git_sha`. Every helper is exception-free by contract.
- Two pytest-benchmark hooks in the performance `conftest.py`. **Identity is compared; condition
  is recorded.** `machine_info.juniper` (`cpu_model`, `cpu_count`, torch/numpy versions, the
  1-thread pin) is what `--benchmark-compare` diffs — a difference warns, mirroring the run tier's
  `HOST.json` refusal in advisory form. `juniper_run` (1/5/15-minute load average at save time,
  UTC, sha) sits beside it and is never compared: a load average inside `machine_info` would make
  every comparison warn, and the warning would stop meaning anything.
- The two forward-pass `save_baseline` calls now record the benchmark's timing, so the dated
  `baseline_*.json` carries `mean_ms` … `iterations` for the first time.
- 13 `unit`-marked tests in `src/tests/unit/` (the performance tier is never collected in CI).
- `.benchmarks/` gitignored, and the reference is cut with `--benchmark-storage` pointed
  **outside every checkout** — a `git worktree remove` deletes ignored files.
- Procedure: cascor `docs/testing/REFERENCE.md` § Micro timing reference; pointer in `AGENTS.md`.

### 2.3 The two cuts, and the condition they were taken under

Storage: `~/.local/state/juniper-experiments/baselines/cascor-micro` (host-local, untracked, the
same convention as the run tier's `pf1-2026-09-04b`). 71 benchmarks per run.

| run | sha | `juniper_run.loadavg` 1m / 5m / 15m at save | load trace during the run (`loadavg-20260909.tsv`, 5 s) |
|---|---|---|---|
| `0001` | `3286b758` (dirty tree) | **9.17** / 5.05 / 3.46 | 40 samples, 1m min / mean / max = 4.22 / 7.41 / 10.91 |
| `0002` | `145fbe92` (the branch commit at cut time; `juniper-cascor#638` squash-merged as `3de89b11`) | **10.22** / 6.51 / 4.32 | 1-minute load 5.2 at start, 9.5 at the end of the ~45 s run |

**Both cuts were taken on a host well above the sweep's ambient band** (4.7–5.9 at the sweep's
quiet blocks). The benchmarks are single-threaded and ten cores were idle, but §8.4's knee is in
worker count, not free cores, and nothing here measured the micro tier's own sensitivity to
ambient load. So the reference is **provisional**: a re-cut on a quieter host supersedes it, the
storage numbers every run, and the load figure travels with each. That is the point of recording
the condition rather than hoping for a quiet one.

### 2.4 What this does not decide

The handoff's §3.3 surfaced an **unexamined option** — a work-style exact-match gate on
`epochs_completed` for the candidate micro-benchmarks, whose count is emergent (early stopping),
foreclosed by reasoning that was wrong rather than by evidence. **Still an owner call.** Nothing in
2.4 builds toward or against it; the reference records timings only.

---

## 3. Source corrections landed

Each phrase below was inherited across at least two documents; each is corrected **at its source**
so the next handoff does not re-inherit it.

| phrase | where | correction |
|---|---|---|
| *"no timing tolerance of any kind"* | P1 design §1 (`…PERF-LANE-P1-DESIGN.md`), P2 item 2.4 | `test_baselines.py` defines `FIT_TIME_THRESHOLD_S = 60.0` and `SERIALIZATION_TIME_THRESHOLD_S = 30.0`, both hard-asserted. They are **fixed absolute ceilings, not baseline comparisons** — the narrower fact the argument actually needs. Dated correction blockquote in the P1 design; row text in the P2 plan |
| *"a 10× dataset range"* | P2 item 2.1 (and the G-17 note's §5, `…G17-BRIDGE-EVIDENCE-AND-HOST-WINDOW.md`) | `n_points_per_spiral: [250, 500, 1000, 2000]` is **8×**. Corrected in the P2 plan; the G-17 note is left as a dated record and is superseded by §4 here |
| *"zero commit history"* | 2026-09-07 handoff §1 item 3 | true of `baseline_20260526.json`, false of its directory — 21 tracked predecessors deleted in `971d35a`. Recorded in §2.1 |
| *"no concurrent-launch harness exists"* / *"cascor `parallel > 1` still refused"* | P1 design §3, P2 Wave 4 preamble and item 4.1 | lifted 2026-08-30 by the version floor; dry-run verified. §1.2 |

---

## 4. Item 2.1 — the PF-2 calibration probe: the dataset axis is inert

Suite `pf2-epoch-calibration-20260909T074828Z` (`util/ad-hoc/2026-09-08_pf2_epoch_calibration_suite.yaml`),
seven cells, sequential, every cell `succeeded` and `early_stopped`, 5 min 35 s launch-to-report
(the per-cell walls sum to 5 min 24 s; the rest is stack bring-up and aggregation). Read with
`util/experiments/read_run_metrics.py`; the dataset sizes below are the resolved artifacts'
`n_train`, not the override (an 8× spread: 500 vs 4000 training rows), confirmed by a distinct
`dataset_id` per size. Load is the 1-minute average sampled at 5 s across each cell's window
(`loadavg.tsv` in the suite directory).

| cell | `n_points_per_spiral` (`n_train`) | epoch pair | `drive` s | `step_sum` s | `step_count` | mean step ms | load 1m mean / max |
|---|---|---|---|---|---|---|---|
| c000 | 200 (400) — bare base cell | 50 / 50 | 10.05 | 4.52 | 8 | 565.5 | 5.5 / 6.0 |
| c001 | 250 (500) | 1000 / 1000 | 35.15 | 29.59 | **450** | 65.8 | 8.5 / 11.8 |
| c002 | 2000 (4000) | 1000 / 1000 | 30.15 | 27.87 | **450** | 61.9 | 12.9 / 14.6 |
| c003 | 250 (500) | 2000 / 2000 | 35.12 | 29.87 | **890** | 33.6 | 13.9 / 15.8 |
| c004 | 2000 (4000) | 2000 / 2000 | 30.13 | 27.40 | **890** | 30.8 | 10.1 / 11.9 |
| c005 | 250 (500) | 4000 / 4000 | 50.20 | 45.63 | **1770** | 25.8 | 8.7 / 10.5 |
| c006 | 2000 (4000) | 4000 / 4000 | 45.18 | 42.13 | **1770** | 23.8 | 7.1 / 8.2 |

**1. The work count does not see the dataset.** At every budget the 250-point and 2000-point cells
report the **same** `step_count` — 450, 890, 1770 — and 1770 at 4000/4000 is exactly PF-1's
invariant (`pf1-2026-09-04b`, `step_count 1770`, at 200 points). This is the load-immune half of
the result: counts are exact, and the host condition in the right-hand column cannot manufacture
an equality. Within this range `step_count` is a function of the epoch budget alone.

> **Why — the mechanism, traced during consensus validation (Lane B1, 2026-09-09), which makes
> the finding structural rather than merely observed, and also bounds it.** Output-layer training
> is full-batch (`cascade_correlation.py:2078-2186`): one forward/backward/step per epoch over the
> whole tensor, and the step counter advances on a throttled per-epoch callback whose condition —
> every 25th epoch plus the last — references only the loop counter and the budget, never the
> data. With `max_iterations: 10` there are eleven such calls per run, and
> 11 × (⌊(E − 1) / 25⌋ + 1) reproduces 450 / 890 / 1770 to within one step. Every cell ends
> `early_stopped` for the same reason too: `max_hidden_units == max_iterations == 10`, so
> `max_units_reached` fires at the last iteration in all six dataset cells (each reached 10 hidden
> units) — the "same termination branch" precondition is met **by construction of this budget**,
> not by data-independent convergence. So "inert" is established for this epoch budget and this
> cascade cap. **Widen the dataset range without revisiting `max_hidden_units` and the
> patience / accuracy criteria, and dataset size can start moving the termination branch, and with
> it the count.** The P1 design's own PF-1 calibration is thin underneath this cross-check
> (a 50-epoch anchor that is a cross-suite n=2 mean with 26% spread, n=1 at 500 / 2000 / 5000 —
> the 2026-09-07 handoff §4), and every probe cell here is n=1 as well; the equality is exact
> regardless, the durations are single samples.

**2. Step time does not see it either.** `step_sum` at 2000 points is 6–8% *lower* than at 250
points at all three budgets — the wrong sign for a scaling effect and well inside the 20.5% quiet
band. The cell order and the load windows do not explain the sign (c002 ran under a *heavier*
window than c001 and was still faster). It is treated as zero.

**3. One epoch value clears both ends — trivially, because n does not matter.** At 4000/4000 the
`drive` is 45–50 s at both ends: above the ~40 s scrapeability floor, short of the ~60 s PF-1
target on this day (PF-1's own 4000-epoch cell read 60.2 s on 2026-09-03, bridged; today's steps
are ~17% faster per step than that baseline, inside the drift band). The 600 s wall the P2 plan
and the handoff worried about is nowhere in reach: the largest cell ran 45 s. If PF-2 is
executed as written, **4000/4000 is the value** — it makes every PF-2 cell do the same 1770 steps
as the PF-1 baseline, so the work column is directly comparable across the two suites.

**4. Consequence: PF-2 as designed measures nothing.** Its axis — `n_points_per_spiral` in
`{250, 500, 1000, 2000}` — moves neither the work count nor the step time. Executing the 4-cell
matrix would produce a well-formed measurement of an invariant, the vacuous-instrument class this
lane keeps finding. To exercise dataset scaling the range has to reach where a step's cost is
data-dominated rather than overhead-dominated — orders of magnitude more points, or a scenario
aimed at the candidate phase, whose correlation computation is what actually grows with n. That
is a change to a §12.3 scenario definition, i.e. an **owner call**; the suite file is left as it
is, and item 2.1 is re-labelled accordingly in the P2 plan.

**5. An observation, with its caveat.** `final_epoch` in the manifests reads 8, 9 or 10 across
cells whose `step_count` is identical. The driver samples `current_epoch` every 5 s and records the
last sample, so a lagging read can under-report a cascade that reached 10; this is not evidence of
different progress and is not pursued here.

**Host condition.** Per-cell 1-minute load ran 5.5–13.9 mean, 15.8 peak — several cells sat past
the sweep's separable knee. Finding 1 is immune to that; finding 2's 6–8% is not, and is read as
noise for exactly that reason; finding 3's absolute durations are the ones a quiet-host repeat
should confirm before 4000/4000 is written into `pf2-cascor-dataset-scaling.yaml`.

---

## 5. Host condition during this session's measurements

The handoff's item 4 asks for an **idle** host. This session did not have one and did not wait for
one: seven to eight peer sessions were live throughout, one holding an idle cascor stack on
`:8202`, and a terminal emulator periodically burst to ~365% CPU. What it had instead was the
sweep's own standard — *ambient, not idle* (§8.2 of the sweep note) — and a **load trace recorded
beside every measurement** (`util/ad-hoc/2026-09-08_loadavg_sampler.py`, 5 s), because
`run_experiment.py` does not record the load average and the sweep driver had to do the same.

| measurement | 1-minute load at start | trace | verdict |
|---|---|---|---|
| micro reference `0001` | 6.0 (5m 3.6) | 4.2 → 10.9, mean 7.4 | loaded; provisional |
| micro reference `0002` | 5.2 (5m 5.3) | 10.2 / 6.5 / 4.3 at save | loaded; provisional |
| PF-2 probe | see §4 | `suites/pf2-epoch-calibration-loadavg-20260909.tsv` | see §4 |

For scale: the sweep's quiet blocks ran at 5.9–18.6 (its ambient rose during the run and never
came back), and the G-17 note declined to run at 14.75 with swap exhausted. This session sat
between those.

---

## 6. What this document does not do

- It does **not** edit `perf/pf2-cascor-dataset-scaling.yaml`. §4 shows the suite's axis is
  inert, so writing 4000/4000 into it would make it *run* correctly while still measuring nothing;
  what the scenario should vary instead is an owner call. If the owner keeps it as written, the
  pair is 4000/4000, confirmed on a quiet host at least once first (n=1 cells choose a budget;
  they do not measure its variance).
- It does **not** run 2.2 (PF-3, ~6.7 h) — no quiet window, per §5.
- It does **not** create the PF-8 suite pair — §1.5.
- It does **not** decide the `epochs_completed` exact-match question — §2.4, owner.

---

## 7. Reproduction

```bash
# Every cascor baseline file that ever existed, with its result keys (exit 0 = no timing key anywhere)
python3 util/ad-hoc/2026-09-08_cascor_baseline_history_census.py

# PF-8: the harness exists — a two-cell parallel cascor suite validates from a session worktree
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  python3 util/experiments/run_suite.py --suite <two-cell parallel suite> --dry-run

# The micro timing reference (cascor worktree, JuniperCascor1)
cd src && python -m pytest tests/performance/test_baselines.py tests/performance/test_micro_*.py \
  --run-performance --benchmark-storage=file://$HOME/.local/state/juniper-experiments/baselines/cascor-micro --benchmark-autosave

# The PF-2 probe (7 cells: the bare base-config cell plus 2 dataset endpoints x 3 epoch budgets)
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  setsid nohup python3 util/experiments/run_suite.py --suite util/ad-hoc/2026-09-08_pf2_epoch_calibration_suite.yaml > pf2_probe.log 2>&1 &
python3 util/ad-hoc/2026-09-08_loadavg_sampler.py --out <suite-dir>/loadavg.tsv --interval 5 &
```
