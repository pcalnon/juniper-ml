# Perf lane — PF-8 located: one run consumes 4.5 cores unpinned and 2.2 pinned, a second concurrent pinned run costs +8.5 to +12.7% per step, and the experiment YAML's `runtime:` block binds nothing

Successor to §1.3 of the re-scope note
([`JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`](JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md))
and to §1 items 2 and 3 of the 2026-09-09 handoff
([`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_perf-lane-pf8-needs-no-harness-micro-reference-cut-pf2-axis-inert.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_perf-lane-pf8-needs-no-harness-micro-reference-cut-pf2-axis-inert.md)).
Item numbers refer to the P2 plan
([`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md))
unless stated otherwise; "the sweep note" is
[`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md);
"the re-scope note" and "the 2026-09-09 handoff" are the two documents linked above. Validated
under the consensus procedure; the record and every correction it produced are in §9.

**Four things happened, in the order §1.3 of the re-scope note required.** The micro timing
reference was re-cut at the best condition this arc has seen (§1). The occupancy probe — step 1
of §1.3 — ran, twice: once under cascor's default thread budget and once under the four-variable
budget `run_suite` pins for a parallel arm, and the two answers differ by 2× (§2). Because the
default-budget figure landed inside the ~4–8 band, step 2 ran too: the two-arm concurrency pair,
three parallel pairs bracketed by six sequential controls, all twelve cells at `step_count` 1770
(§3). And the probe's most consequential finding is a wiring fact: the `runtime:` block every
experiment YAML carries — `blas_threads`, `num_processes` — is validated by the driver, accepted by
the service, and **read by nothing on either path**, which among other things makes the second
matrix axis of the approved PF-3 suite a no-op (§4). What the cascor listener burns for the first
seventeen seconds of every unpinned run is an ~11-core burst confined to the **initial** output
pass, which the three BLAS environment variables remove and which `torch.set_num_threads` does not
reach; which library carries it is narrowed, not identified (§4.2).

---

## 0. What this closes and what it leaves

| item | state after this document |
|---|---|
| **4.1 residue** (occupancy probe, S) | **DONE** — §2. One PF-1-shape run under the default budget consumes **4.52** cores during training (cpu-seconds per wall-second; 3 cells, 1.1% spread), as one ~11-core block for the initial output pass followed by ~1.8 for the other ten passes. Under the pinned budget, **2.15**, never above 3.5 in any pinned cell of the day. The sweep-worker unit those figures are read against is assumed, not measured (§2.1) |
| **4.2** (the two-arm pair) | **EXECUTED from `util/ad-hoc/`** — §3. Parallel / control mean step = 1.1125, **+11.3% per step at the pinned budget; +8.5 to +12.7% leaving one of the three pairs out**; inside the sweep's 20.5% quiet band, outside today's within-arm spread by a margin one pair wide. Advisory, as 4.3 said it could only be. Where a *committed* instrument would live (the §1.5 CI hazard) is still the owner's call, and is now **optional** — §6 |
| **2.4 follow-up** (quiet re-cut `0003`) | **DONE at ambient, not idle** — §1. Cut at 1-minute load 5.3 → 7.1 against 9–10 for `0001` / `0002`; the micro tier does not see that difference (median ratio 0.99). It does **not** supersede under the cascor procedure's quiet-host rule; it is recommended as the compare target as the best-conditioned cut |
| **2.1** (PF-2's inert axis) | Untouched — owner. §4 adds one constraint: fix the thread budget explicitly in any re-scope, because the budget moves step time and `step_count` not at all |
| **2.2** (PF-3, ~6.7 h, approval standing) | **BLOCKED — its second matrix axis is inert.** `pf3-cascor-pool-scaling.yaml` varies `runtime.num_processes: [1, 2, 4]`, which nothing reads (§4.1, §4.3), so as written the approved run is four pool sizes run three times each and cannot produce its speedup curve. Do not launch it until the `runtime:` block is ruled — §6 |
| `epochs_completed` exact-match (2026-09-09 handoff §1 item 1, third bullet) | Untouched — owner. §1 adds evidence: in every pairwise comparison of the three micro cuts, the benchmarks outside ±20.5% are dominated by the candidate tier, whose epoch count is emergent |
| **NEW owner question** | Implement or retire the `runtime:` block — §4.3, §6 item 4. It changes what every existing YAML means, so it is a baseline-cutting decision, not a fix |

---

## 1. Micro timing reference `0003`

Cut 2026-09-10T09:35Z from the clean cascor primary at `a51b7c58` (`origin/main`; the holder check
the 2026-09-09 handoff's §5 requires came back empty), with `util/ad-hoc/2026-09-08_loadavg_sampler.py`
recording beside it (`~/.local/state/juniper-experiments/baselines/cascor-micro/loadavg-20260910.tsv`).
77 tests passed in 39.5 s (the pytest summary of the session's run; the saved JSON records only
the 71 benchmark stats); 71 benchmarks saved, the same 71 as `0001` and `0002`; `machine_info.juniper`
identical to both.

| run | sha | 1m / 5m / 15m load at save | trace during the run (1-minute, 5 s samples) |
|---|---|---|---|
| `0001` | `3286b758` (dirty) | 9.17 / 5.05 / 3.46 | 4.22 → 10.91, mean 7.41 |
| `0002` | `145fbe92` | 10.22 / 6.51 / 4.32 | 5.2 → 9.5 |
| **`0003`** | **`a51b7c58`** | **7.07 / 5.80 / 5.89** | **5.17 → 7.31**, back to 5.48 within a minute of the end |

**This is not a quiet host** — the sweep note's own quiet blocks ran at 5.9–18.6, and the
1-minute figure at save is the benchmarks' own load on top of a ~5.3 ambient. The cascor
procedure's rule (`juniper-cascor/docs/testing/REFERENCE.md` § Micro timing reference) is that
*re-cutting on a quiet host* supersedes an earlier cut; `0003` is not that cut, and does not
supersede under that rule. It is the best-conditioned of the three, and this document recommends
it as the compare target on that basis, until a cut at a 1-minute load under 3 exists:
`--benchmark-compare=0003`, never `--benchmark-compare-fail` (owner, item 2.5).

**What the three cuts say about each other**, benchmark by benchmark from the saved JSON
(`util/ad-hoc/2026-09-10_micro_reference_compare.py`; median of each benchmark's rounds; no re-run):

| pair | 1-minute load at save | median ratio (other / base) | p10 – p90 | faster / slower | outside ±20.5% |
|---|---|---|---|---|---|
| `0003` vs `0002` | 7.1 vs 10.2 | **0.9945** | 0.874 – 1.166 | 37 / 34 | 7 |
| `0003` vs `0001` | 7.1 vs 9.2 | 0.9613 | 0.834 – 1.117 | 50 / 21 | 7 |
| `0002` vs `0001` | 10.2 vs 9.2, three minutes apart | 0.9542 | 0.846 – 1.102 | 47 / 24 | 4 |

Two readings. **The micro tier does not see the difference between a 1-minute load of 7 and one
of 10**: the quieter cut is not systematically faster (median ratio 0.99 against `0002`), and the
two loaded cuts differ from each other by as much as either differs from the quiet one. The
per-benchmark scatter between *any* two cuts is about ±15% at p10–p90 — the run tier's 13–20.5%
band, reproduced one tier down. And **the benchmarks that leave the band are the candidate ones**:
of the 18 out-of-band entries across the three comparisons, 12 are `test_micro_candidate.py` or
`test_baselines.py::TestCandidateTrainingBaseline` (the largest, `test_activation_comparison[sigmoid]`,
at 1.58× and 1.44×), against 2 correlation, 3 forward-pass / residual-error, 1 output-training. That is
the tier whose epoch count is emergent (2026-09-09 handoff §3.3), so a timing comparison of it is
partly a comparison of how many epochs each cut happened to run — evidence for, not a decision on,
the owner's `epochs_completed` exact-match question.

---

## 2. Step 1 — the occupancy probe

### 2.1 The instrument, its unit, and its limits

`util/ad-hoc/2026-09-10_pf8_occupancy_sampler.py` watches the run root for run directories, reads
each run's `juniper-cascor.pid` / `juniper-data.pid` once the launcher writes them, finds the driver
by its `--run-dir` argument, and once a second walks `/proc/<pid>/stat` for the three process trees,
writing cpu-seconds per role per interval: `cascor_uvicorn` (the listener), `cascor_forkserver`,
`cascor_workers` (the forkserver's descendants — the candidate pool), `cascor_other`, `data`,
`driver`, plus the whole host's busy cores from `/proc/stat` and the 1-minute load. It is `/proc`
deltas, not `ps %CPU`, which is a lifetime average; a process's `stat` aggregates all its threads,
so a wide BLAS pool inside the listener is captured. `util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py`
aligns the trace with each cell's drive window (the first and last `ts_unix` of the driver's
`metrics_series.csv`) and reduces it. `tests/test_pf8_occupancy_probe.py` pins the arithmetic
(26 tests, CI-wired).

**The unit.** Occupancy is cpu-seconds per wall-second — **cores consumed by this run**. §1.3 of
the re-scope note equates one core with one sweep worker (a `sha256sum` process), and this
document reads its figures on the sweep's axis in §2.2. That equation is an assumption the sweep
note does not license: its §8.4 says the knee is *"located in worker count, not in cores"* and
that converting one to the other *"would need per-core occupancy sampled during each cell, which
this sweep does not collect"*. The sweep's abscissa is additional saturated workers on top of an
ambient; the probe's is a run's own consumption; equating them assumes a run's consumption equals
its externality on a neighbour — true of a steady CPU-bound worker, untested for a listener that
runs one ~11-core burst and then idles at two. The measurement stands in cores; the sweep-axis
reading is conditional on that assumption, and §3 measured the externality directly instead.

**The window.** The driver's first-to-last poll trails the last training activity by four or five
1-second samples of near-zero occupancy (about one driver poll), so the same trace read over the
active portion only gives **4.9** rather than 4.5 for the default budget (Lane B, §9). Neither
reading crosses 6.

**What it loses.** A pid that exits inside an interval takes its last partial second with it. The
`vanished` column counts those: 3–5 per cell across the day (3 in each default cell), all at the
release of the candidate pool at the end of `fit()` — at or just after the last active sample,
*inside* the analyser's window by 3–4 s in the default cells and by 0–5 s across the day (in four
of the fifteen cells on the window's final sample) — so the lost tails belong to idle or nearly idle workers and
are bounded at under five cpu-seconds per run.

The workload is PF-1's cell shape exactly — `spiral-smoke.yaml` at `(10, 10)` / 4000 / 4000
(`util/ad-hoc/2026-09-10_pf8_occupancy_probe_suite.yaml`, three repeats as a matrix axis) — so that
`compare_baseline` can say whether the probe measured the baseline's workload. It did:
**`PASS`, `step_count` 1770 / 1770 against `pf1-2026-09-04b`** (speed reported −21.1%, not gated).

### 2.2 Under cascor's default thread budget: 4.52, as one block and a floor

Suite `pf8-occupancy-probe-20260910T093641Z`, no thread variable set (the manifests record all four
as `null`), so the listener ran with the runtime-default pools and the candidate pool with cascor's
own default of `min(candidate_pool_size 4, cores) − 1 = 3` processes.

| cell | `step_count` | mean step ms | `drive` s | cascor tree, cores | p95 / max (1 s) | share of window ≥ 6 / ≥ 8 | occupancy ≥ 6 / < 6 | ambient cores | load 1m |
|---|---|---|---|---|---|---|---|---|---|
| c000 | 1770 | 28.36 | 55.20 | **4.524** | 11.57 / 12.38 | 0.31 / 0.31 | 10.64 / 1.80 | 3.63 | 7.54 |
| c001 | 1770 | 28.39 | 55.19 | **4.541** | 12.61 / 12.78 | 0.29 / 0.27 | 11.42 / 1.75 | 4.21 | 8.76 |
| c002 | 1770 | 27.89 | 55.21 | **4.490** | 12.33 / 12.66 | 0.29 / 0.27 | 11.20 / 1.77 | 3.71 | 8.93 |

**Mean 4.52 cores, spread 1.1%** across three cells — the occupancy of this workload is as
reproducible as its step count. **But the mean is the mean of one block and a floor, not of a
scattered mixture.** In every cell the high mode is a single contiguous run of samples at the start
of the window — indices 0/1 to 14/16 of 52, about seventeen seconds — during which no candidate
worker is alive and `current_hidden_units` is 0: it is the **initial output-layer pass**, 160 of
the 1770 steps, at 92–130 ms per step (per-poll `step_sum / step_count` from the series). The
moment the first candidate pool appears (three forkserver children) the listener drops to ≤ 2
cores and stays there through the remaining ten output passes, which run at ~20 ms per step; the
forkserver's children peak at 2.7 cores in any second, the `data` tree never exceeds 0.01, and the
`driver` stays below 0.05 until its final in-window sample, where its post-training collect
reaches 0.6–1.4. So the "bimodality" is a phase structure: one pass at ~11 cores, ten at ~2.

Read on the sweep's axis under §2.1's assumption, 4.52 is below the 6-worker point, where §8.4 of
the sweep note measured +19.9% inside a 20.5% band — "below what this host can measure", not
"free" — and inside the ~4–8 band §1.3 of the re-scope note set for running step 2. That test
was applied as written, and §3 exists because it passed. Two things must be said beside it. A load
of ~11 for a third of the window and ~1.8 for the rest, read against a curve that rises from +19.9%
at 6 to +86% at 8, is not the same as a steady 4.5: for its first seventeen seconds a second
start-aligned unpinned run would put about 22 cores on 16, past the plateau, and for the rest it
would sit far below the knee. And §1.1 of the same re-scope note had already said that a run at
≤ 6 workers adds nothing the sweep did not know — the pair's result in §3 agrees with §1.1.

### 2.3 Under the budget `run_suite` pins for a parallel arm: 2.15, and the first pass 8× faster

The same suite file with the four variables `thread_budget_env("cascor", 2)` would export on this
host — `OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CASCOR_NUM_PROCESSES=4` — set in the
shell (suite `pf8-occupancy-probe-20260910T094028Z`; the manifests record all four).

| cell | `step_count` | mean step ms | `drive` s | cascor tree, cores | p95 / max | share ≥ 6 | ambient cores | load 1m |
|---|---|---|---|---|---|---|---|---|
| c000 | 1770 | 18.44 | 35.12 | **2.150** | 3.03 / 3.11 | 0 | 4.40 | 6.63 |
| c001 | 1770 | 18.48 | 35.16 | **2.130** | 2.96 / 3.10 | 0 | 4.65 | 8.01 |
| c002 | 1770 | 18.88 | 35.13 | **2.169** | 3.04 / 3.21 | 0 | 4.95 | 6.95 |

Three things, each with its own weight:

1. **2.15 cores, never above 3.3 in any second of this suite** (3.5 across the day's pinned
   cells). The block is gone: with the pools capped, the run is a near-constant load of about two
   cores from its first sample. Below the band, so by §1.3's
   rule alone the pair would *not* have been worth running at this budget (§3.1).
2. **The pinned run is faster — mean step 18.4–18.9 ms against 27.9–28.4, i.e. 34% faster per
   step, `drive` 35 s against 55 — and the gap is one phase.** The initial output pass runs at
   11–14 ms per step pinned against 92–130 unpinned, about **8×**, and those 160 steps — 9% of
   1770 — carry 82–83% of the step-sum difference. Over the other 1610 steps the arms differ by
   **+9.3 to +10.4%** (default slower), depending on the split: at step 160 of each cell's
   per-poll cumulative series with within-poll interpolation, the three default cells against
   this suite's three pinned cells give +9.7% and against all six pinned controls +9.3%; at the
   last poll before `current_hidden_units` first exceeds 0, the three default cells against all
   six pinned controls give +10.4% — every version inside both the 20.5% quiet band and the 13%
   between-run drift (§9, rounds 2–4). Same day, same workload, n = 3
   against 3, the direction the same in every cell. Report-only, as all speed is (decision 2 of §7
   of the sweep note). What it says about the lane's historical figures is narrower than "34%
   inflated": every service-path run's *initial pass* was oversubscribed about eightfold, and its
   later passes were within a tenth of the pinned rate.
3. **`step_count` is 1770 in all six cells.** The thread budget moves the step *time* and the work
   count by nothing — exactly the split the gate was designed around. And `compare_baseline`
   **REFUSED** this suite against `pf1-2026-09-04b` (exit 2: *"host identity differs from the
   baseline (thread_budget)"*), which is the identity precondition doing precisely what §2.2 of the
   P2 plan says it must: a pinned run is a different regime, not a 48% speed-up.

---

## 3. Step 2 — the two-run pair

### 3.1 Design, and what authorised it

Per §1.3–§1.4 of the re-scope note, executed by `util/ad-hoc/2026-09-10_pf8_pair_driver.bash`
(one background launch, one log, the load average around every suite):

- **Parallel arm**: `util/ad-hoc/2026-09-10_pf8_two_run_parallel_suite.yaml` — two identical
  PF-1-shape cells, `execution: {mode: parallel, max_parallel: 2}`, run **three times** as three
  separate suites so the pairs are aligned (one six-cell suite would stagger cells 3–6 as the pool
  refilled). Each cell brings up its own juniper-data and cascor on its own ports. The suite lives
  under `util/ad-hoc/` for the reason §1.5 of the re-scope note gives: checked in under
  `suites/perf/` it turns `tests/test_experiment_suite_yamls.py` red in CI.
- **Control arm**: the probe suite of §2 — three sequential cells — run once **before** the
  parallel runs (§2.3's suite, `…T094028Z`) and once **after** (`…T094842Z`), with the same four
  variables exported by hand, as §1.3 requires; `run_suite` exports them only in parallel mode.
- **Instrument**: mean step duration (`step_sum / step_count`) from `read_run_metrics`, never
  `drive`. The sampler ran throughout (`suites/pf8-occupancy-trace-20260910.tsv`; a copy as
  `occupancy.tsv` in each suite directory; the reduced pair in `suites/pf8-pair-analysis-20260910.json`).

Two departures from §1.3, stated rather than dropped. It asked for cells of **≥ 60 s**; today's
4000-epoch pair ran 35–45 s of drive (faster than when it was calibrated), no cell met it, and the
reason for it — scrapeability with the Grafana bridge on — did not apply because the bridge was
off; `step_sum` is fully resolved at these lengths (§2 of the sweep note). And the band test that
authorised step 2 was applied to the **default**-budget figure (4.52), while the only arm a
parallel suite can run is the **pinned** one, whose occupancy (2.15, §2.3) sits below the band;
§1.1 of the re-scope note had already said a run at ≤ 6 adds nothing. So the pair's value is the
direct measurement it produced — start alignment, the idle data services, and the cost — not the
band logic that scheduled it.

### 3.2 Result

| arm | cells | `step_count` | mean step ms | min – max | within-arm spread | cascor tree per cell, cores | thread env |
|---|---|---|---|---|---|---|---|
| parallel (3 pairs) | 6 | 1770 in all | **20.72** | 20.15 – 21.91 | 8.7% | 2.02 | pinned, identical to control |
| control (3 before + 3 after) | 6 | 1770 in all | **18.63** | 18.30 – 19.15 | 4.7% | 2.11 | pinned |

**Identity holds before the comparison is read**: the same four-variable budget in all twelve
manifests and the same `step_count` in all twelve cells — two of the checks `compare_baseline`
applies; its others (workload fingerprint, a single completion reason, work countable) hold here
too, since every cell `early_stopped` and the suites differ only in `execution` and the
description.

**Parallel / control = 1.1125: a second concurrent run costs +11.3% per step**, at this budget, on
this day. The two arms do not overlap (the slowest control cell, 19.15 ms, is below the fastest
parallel cell, 20.15 ms), and the two runs together put **4.01–4.06** cores on the host — the pair
total the parallel arm actually imposed, against the 4.52 a *single* unpinned run imposes.

**The parallel arm has three effective observations, not six.** Its six cells are three
simultaneous pairs of an identical seed-fixed config: within-pair spread 0.2–1.3%, between-pair
7.9%. Leaving one pair out, the ratio reads **+8.5% / +12.7% / +12.6%**; an exact one-sided
permutation of the three pair means against the six controls gives p = 1/84. The honest statement
is **+8.5 to +12.7% per step over three pairs**, with +11.3% the point estimate. The control arm's
before and after halves differ by 0.26% (18.60 vs 18.65 ms), so drift did not produce it.

**Start alignment, which the re-scope note left as an assumption, is measured**: the two cells'
drive windows began 0.068 s, 0.046 s and 0.003 s apart and shared 40.1 s in every pair (100% of
both windows in two pairs; 89% of the longer one in the first, whose cell B ran one poll longer).
The parallel executor submits both cells back-to-back and the port lock's `mkdir` is the only
serialisation point; that is enough. Each cell's own juniper-data instance read ≤ 0.01 cores
throughout training.

### 3.3 Two readings, both true

- **By the lane's standing rule** (§8.4 of the sweep note: an effect against a 20.5% quiet band
  "carries no information"; §1.3 of the re-scope note: inside the band is *"below what this host
  can measure"*): +11.3% is inside the band. Across sessions, days and ambient conditions, this
  host cannot distinguish a second run from drift.
- **By today's brackets**: the controls that bracket the parallel runs spread 4.7%, the parallel
  cells 8.7%, the arms are disjoint, and the point estimate clears both — but the leave-one-pair-out
  low end (+8.5%) sits just under the 8.7% within-arm spread, so on the day the cost is resolved
  by three pairs and would not be by two.

PF-8 was never going to change a gate (item 4.3: the work half is settled, speed is ungated), so the
finding is what §1.3 said it would be — **advisory**: two pinned PF-1-shape runs may share this
host at a per-step cost of about a tenth, which is below the band the lane treats as noise between
sessions. Nothing here supports running two *unpinned* runs concurrently: each would burst to ~11
cores for its first seventeen seconds, the start offsets above say those bursts would coincide,
and two of them is ~22 cores on 16 — the plateau of §8.4 or past it. That configuration was not
run, because the parallel arm cannot be unpinned (`run_suite` always exports the budget in parallel
mode), and this document does not guess its number.

### 3.4 Host condition

Ambient (host busy cores minus this run's own trees) was 3.6–4.2 during the default probe,
4.0–5.7 during the six control cells, and 6.0–7.8 during the parallel runs — where the *partner*
run is inside the ambient figure, so the external ambient there was 4.0–5.6, a mean of 4.6
against the controls' 4.8; but within the parallel arm the slowest pair ran with ~1.5 cores more
neighbours than the other two, so the between-pair spread is not independent of ambient (§9,
round 2). Between cells the host ran 4.8 busy cores host-wide, all processes counted,
at a 1-minute load of 6.6 (223 host-only samples) — numerically the same as the controls'
external-ambient mean, a coincidence of two different quantities. The sweep's quiet blocks ran at loads of
5.9–18.6. This was ambient, not idle, throughout; the load was recorded beside every measurement.

---

## 4. Why nothing in the YAML can bound the listener, and what the first-pass burst is and is not

### 4.1 The `runtime:` block is read by nothing

`spiral-smoke.yaml` — the base config of PF-1, PF-2, PF-3 and both probes — declares
`runtime: {blas_threads: 2}`, and §1.1 of the re-scope note
([`JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`](JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md))
describes the workload as *"a candidate pool of 4 with `runtime.blas_threads: 2`"* (an earlier
draft of this paragraph attributed the phrase to the P1 design as well; it is not there — Lane A,
§9). `pf3-cascor-pool-scaling.yaml` goes further and uses `runtime.num_processes: [1, 2, 4]` as
the second axis of its 4×3 matrix. Traced through every consumer on 2026-09-10:

| layer | what it does with `runtime:` | where |
|---|---|---|
| driver `run_experiment.py` | validates the key set (`RUNTIME_KEYS = {num_processes, blas_threads, eval_metrics_enabled}`) and **reads none of them** | `util/experiments/run_experiment.py:171`, `:607-609`; no other line reads any of the three keys (the token `runtime` appears at `:146`, `:171`, `:174` and `:604-609`, none of them a read of a key's value) |
| suite runner `run_suite.py` | writes dotted overrides into the cell YAML; its parallel-mode budget is hard-coded in `thread_budget_env`, never read from the block | `util/experiments/run_suite.py:306`, `:352-359` |
| launcher `experiment_stack.bash` | exports no thread variable; the cascor bring-up line carries `JUNIPER_CASCOR_CONFIG_FILE` and the run's provenance variables only | `util/experiment_stack.bash:647` (the announced command), `:633` |
| cascor service | accepts `runtime` as a known top-level block and projects **only `service:`** into Settings — *"the other blocks belong to the driver / launcher layers and are deliberately ignored here"* | `juniper-cascor/src/api/settings.py:142-144` |
| cascor direct CLI | reads `dataset.params` and `training.params` from the file, nothing else | `juniper-cascor/src/main.py:305-320` |
| cascor thread policy | *"Default: do nothing, leaving the runtime's own choice"*; `JUNIPER_CASCOR_BLAS_THREADS=<n>` opts in (`api/__init__.py:14-16`), and the launcher never sets it | `juniper-cascor/src/parallelism/blas_threads.py` module docstring |

So `runtime.blas_threads`, `runtime.num_processes` and `runtime.eval_metrics_enabled` are
**decorative on both paths**: a documented intent (`settings.py` calls the block "process-env
territory") that no layer ever implemented. The manifests are honest about it —
`environment.thread_env` records all four variables as `null` for every unpinned run, including
all 27 run directories the two headroom-sweep attempts left (21 in the reported run), the five
cells of `pf1-cascor-spiral-repeats-20260903T040803Z` and the seven of the PF-2 probe — but
nothing warns that the YAML asked for something the run did not get.

### 4.2 What the first-pass burst is, and what the evidence does and does not identify

What is established:

1. **It is confined to the initial output-layer pass** (§2.2): `current_hidden_units` 0, no
   candidate pool alive, the listener alone at 10.6–11.4 cores, 92–130 ms per step; the ten later
   output passes in the same process, same environment, run at ~20 ms per step with the listener
   at ≤ 2 cores. cascor's own log for a default cell (`logs/juniper_cascor.log.1` in the run
   directory) shows exactly that block: *"fit: Initial training of output layer"*, four hundred
   `train_output_layer … Epoch N` lines over eighteen seconds, then *"fit: Starting main training
   loop"* — and shows the ten later output passes completing their epochs in one to three seconds
   each at the log's one-second resolution (rounds 2 and 3, §9; an earlier draft called the log
   silent there, which was wrong).
2. **The three BLAS variables remove it** (§2.3): with `OMP/MKL/OPENBLAS_NUM_THREADS=2` in the
   process environment the first pass runs at 11–14 ms per step and the listener never exceeds
   ~2 cores.
3. **cascor's own torch pins are in place before it**: the parent pins `torch.set_num_threads(max(2,
   2 × worker_thread_count))` = 2 in `_init_multiprocessing`, called from the constructor
   (`cascade_correlation.py:617` → `:1179-1180`; `worker_thread_count` defaults to 1), and each
   candidate worker pins itself to 1 (`:4152-4153`) — consistent with the pool's children never
   exceeding 2.7 cores in total.
4. **Direct probes in a fresh interpreter** (`util/ad-hoc/2026-09-10_torch_thread_pin_probe.py`,
   1024² float32 matmuls for 2 s, cpu-seconds per wall-second from `/proc/self/stat`,
   JuniperCascor1: torch 2.11.0+cu130 on MKL 2024.2, numpy 2.4.4 on its bundled `scipy-openblas64`):

   | case | `torch.get_num_threads()` | cores consumed |
   |---|---|---|
   | torch, variables unset, no pin | 8 | 6.7 |
   | torch, variables unset, `torch.set_num_threads(2)` | 2 | **1.9** |
   | torch, `OMP/MKL/OPENBLAS=2` | 2 | 1.9 |
   | **NumPy, variables unset, no pin** | 8 | **11.5** |
   | **NumPy, variables unset, `torch.set_num_threads(2)`** | 2 | **10.9** |
   | NumPy, `OMP/MKL/OPENBLAS=2` | 2 | **2.0** |

   and, at the workload's real shape — a 2→2 linear layer trained over 320 rows — unpinned torch
   burns **7.5 cores for no wall-time gain** (Lane B, §9; the OpenMP pool spins on ops too small
   to parallelise).

What follows, and only this: `torch.set_num_threads(2)` bounds torch's own operators and leaves
NumPy's OpenBLAS pool at the runtime default — an environment variable read once at library load
is the only thing that reaches it — so **the three variables, and only they, bound the burst**.
Its magnitude (10.6–11.4) sits between an unpinned torch loop at the real shape (7.5) and an
unpinned NumPy matmul (11–13), so the probes do not discriminate the library. If the parent pin is
effective inside the listener during the first pass — and it is applied before it — torch is the
less likely source and NumPy's OpenBLAS pool the leading candidate. That is the extent of the
attribution: **not identified** are the call site, why only the initial pass (the same
`train_output_layer` runs ten more times at 2 cores), and whether `torch.get_num_threads()` reads 2
inside the listener while the burst runs. The discriminating test is a profile of the listener's
first pass, or reading both pool sizes from inside the process; neither was done.

> **SUPERSEDED 2026-09-10 — the leading candidate named in this section is REFUTED.** The
> discriminating tests were run the same day and are recorded in
> [`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md).
> The burst is carried by **libgomp — the GNU OpenMP runtime — inside `libtorch_cpu`,
> predominantly under `torch::autograd::Engine`**. NumPy's OpenBLAS pool carries **none** of it:
> pinning `OPENBLAS_NUM_THREADS=2` alone leaves the burst completely intact at 16 threads and
> 13.7 cores (while the OpenBLAS pool demonstrably shrinks — alive threads fall 43 → 29), pinning
> `OMP_NUM_THREADS=2` alone removes it completely (2 threads, 2.0 cores), and `libopenblas`
> appears in **0.0%** of 614 native profile samples against `libgomp`'s 47.6%. The single-variable
> arms this section says were never run ("the probe never sets one alone") are what settled it.
>
> Two further corrections to this section. **(a)** `torch.get_num_threads()` **does** read 2
> inside the process while the burst runs — it reports the library-global setting, not the width
> in force on the thread doing the work, so that question could not have discriminated anything
> on its own.
>
> > **2026-09-11 — (a) is worse than "could not have discriminated": running it would have
> > DESTROYED the measurement.** `torch.get_num_threads()` is not a passive read. It runs torch's
> > per-thread lazy init and **re-pins the calling thread's OpenMP ICV** to the global — proven by
> > two threads identical but for that one call (16 → 16 without it, 16 → **8** with it). Read
> > inside the listener during the burst, as this section proposes, it would have ended the burst
> > and reported a quiet, correctly-pinned thread as evidence that nothing was wrong. The safe
> > instrument is libgomp's `omp_get_max_threads()` through `ctypes`, which returns the calling
> > thread's own width and mutates nothing. See
> > [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
> > §1.1. The "why only the initial pass" question this section also lists as unidentified is
> > answered in that note's §3.3–§3.5.
>
> **(b)** The trigger is that the pass runs on a thread other than the one that
> constructed the network: cascor's parent pin is applied in the constructor
> (`cascade_correlation.py:617` → `:1179-1180`) while the service constructs in
> `_create_network_locked` (`api/lifecycle/manager.py:1538`) on the request thread and trains in
> `_run_training` (`:2476`) on the `cascor-train` executor created at `:2431`. In one process,
> unchanged otherwise, moving the pass off the constructor's thread takes it from 1.53 cores / 2
> threads to 9.45 / 16, and constructing on that same worker thread puts it back to 1.48 / 2.
>
> §2.2's "confined to the initial pass" **stands** and was re-measured independently (a 150 s
> listener census over four growth iterations and 16 `_retrain_output_layer` calls contains
> exactly one ≥10-thread block). Why it is confined, given that later passes run on the same
> thread and nothing re-pins it, is the open residual — see that note's §5.3.
>
> One reading in item 1 above is also corrected there: the "four hundred `train_output_layer …
> Epoch N` lines" are 400 INFO lines at `epoch_display_frequency` = 10, i.e. **4000 epochs**,
> matching the cell's `output_epochs: 4000`. The pass has no early exit.

**The probe does not settle throughput either**: in this session's run the NumPy loop at the
runtime-default width completed fewer matmuls in its two seconds (57) than the 2-thread one (79), but a re-run during
validation reversed that order (94 against 85) while reproducing the core figures (12.8 / 12.2 /
2.0). The single-process probe is a load-sensitive instrument for *which pool* is busy, not for
how fast it is; the 34% of §2.3 rests on the six suite cells, and "oversubscribed on 8 physical
cores with a 4–5-core ambient" is the plausible mechanism for it, not a measured one.

### 4.3 What follows, and what is deliberately not done

- **Every service-path figure in this lane — PF-1's calibration, its five-repeat baseline
  `pf1-2026-09-04b`, the headroom sweep (21 reported cells; 27 run directories with the aborted
  attempt), the PF-2 probe — was taken with the listener's pools at the runtime default.** Their `step_count`s are untouched (1770 in all fifteen probe
  cells of this session, pinned or not). Their *speeds* carry an initial pass that ran about 8×
  slower than pinned and later passes within a tenth of it (§2.3).
- **PF-3 as written cannot produce its deliverable.** Its second matrix axis,
  `runtime.num_processes: [1, 2, 4]`, is inert (§4.1), so the approved ~6.7 h run would be four
  pool sizes run three times each with no process-count variation at all. It must not be launched
  until the block is ruled; if the block is implemented, `CASCOR_NUM_PROCESSES` exported per cell
  from `runtime.num_processes` is exactly the export PF-3 needs.
- **Fixing the block is an owner decision, not a bug fix.** The obvious change — the launcher
  exporting `JUNIPER_CASCOR_BLAS_THREADS` (or the three variables) from `runtime.blas_threads` and
  `CASCOR_NUM_PROCESSES` from `runtime.num_processes` — would make every existing experiment YAML
  mean something different from what it has meant in every run to date, change the speed regime of
  every suite, and require a new run-tier baseline (`compare_baseline` would correctly refuse the
  old one on `thread_budget`). It touches the launcher, the driver's environment capture, cascor's
  policy module, and every document that quotes a service-path timing. Nothing here does it.
- The candidate pool's own budget is a second knob with a measured cost: cascor#531 found a
  BLAS cap *slowed* the candidate phase 1.52× and changed its epoch count. The initial output pass
  measured here moves the other way. Any budget decision needs both phases measured under it; this
  document measured one.

---

## 5. Host condition during this session's measurements

| measurement | when (UTC) | 1-minute load at start → end | trace |
|---|---|---|---|
| micro reference `0003` | 09:34:29 – 09:36:34 | 5.19 → 7.31 → 5.48 | `baselines/cascor-micro/loadavg-20260910.tsv` |
| occupancy probe, default | 09:36:41 – 09:40:00 | 7.5 – 8.9 per cell | `suites/pf8-occupancy-trace-20260910.tsv` |
| occupancy probe, pinned (control before) | 09:40:28 – 09:43:20 | 6.6 – 8.0 | same |
| parallel arm ×3 | 09:45:18 – 09:48:27 | 5.50 → 8.05, 7.76 → 7.69, 6.65 → 7.91 | same + `suites/pf8-pair-driver-20260910T094518Z.log` |
| control after | 09:48:42 – 09:51:09 | 7.13 → 8.65 | same |

A `clamscan` had been holding one core for nineteen CPU-hours since before the session and a
browser content process burst to 170% throughout; seven peer sessions were live, one holding an idle
cascor stack on `:8202`. Ambient, not idle — the sweep's own standard (§8.2 of the sweep note).

---

## 6. Owner decisions — three carried, two new

1. **PF-2's axis** (2026-09-09 handoff §1 item 1, first bullet) — unchanged. One constraint added
   by §2.3: whatever the scenario becomes, its suite must fix the thread budget explicitly, because
   the budget moves step time and the work count not at all; a scenario that inherits "whatever the
   shell had" measures the shell.
2. **Item 4.2's CI hazard** (second bullet) — now **optional**. The pair has run from `util/ad-hoc/`
   (the headroom sweep's precedent) and PF-8's advisory answer is on record. A committed
   `suites/perf/` pair is needed only if PF-8 is to be re-run routinely; if it is, the recommended
   fix stands (move the parallel floor check from `load_suite` to the execution path, still
   fail-closed, with its own negative tests). If it is not, the hazard stays a documented hazard
   (P2 plan §4) and no gate changes.
3. **`epochs_completed` exact-match** (third bullet) — unchanged. §1's evidence: the candidate
   benchmarks are the ones that leave the ±20.5% band between cuts.
4. **NEW — the `runtime:` block.** Implement it (launcher exports; new baseline; every YAML's
   meaning changes) or retire it (drop the keys from the schema so a config cannot ask for what it
   will not get). Either is a decision about what every experiment config *means*; §4.3 says why it
   is not taken here.
5. **NEW — PF-3 (item 2.2) is blocked on that decision.** Its `runtime.num_processes` axis is a
   no-op today; the approved ~6.7 h of host time would measure nothing on that axis. Rule item 4
   first, then re-express or re-approve PF-3.

---

## 7. What this document does not settle

- **n is 3 per probe budget and three effective pairs against six controls, on one day.** The
  1.1% / 1.8% occupancy spreads and the disjoint arms are strong for one day; the leave-one-pair-out
  range (+8.5 to +12.7%) is the honest width, and §3.3's second reading would not survive a
  different day's ambient without repeats.
- **The pair ran only at the pinned budget.** Two unpinned runs — the configuration an operator who
  launches two ordinary PF-1 suites would actually create — were not measured; §3.3 says what the
  phase structure and the start alignment predict for them without claiming it.
- **The first-pass burst is narrowed, not attributed.** NumPy's OpenBLAS pool is the leading
  candidate by the pin logic and the magnitude match; no profile, no call site, and no in-process
  reading of either pool's size (§4.2).
- **The sweep-worker unit is assumed.** A run's cores are not the sweep's synthetic workers (§2.1);
  the pair measured the externality directly, and that measurement is the one to quote.
- **The occupancy figure depends on the window definition by ~8%** (4.5 first-to-last poll, 4.9
  active portion); neither crosses the knee.
- **`0003` is ambient, not quiet.** A cut at a 1-minute load under 3 has still never been taken on
  this host, and `0003` does not supersede under the cascor procedure's quiet-host rule.
- **The 34% pinned-vs-default difference is a between-suite comparison** taken under four minutes
  apart (09:36:41 and 09:40:28) under similar ambient, not interleaved cell-by-cell; and it is
  82–83% one phase (§2.3).
- **§1.3's ≥ 60 s cell length was not met** (35–45 s); the bridge was off, so the reason for it did
  not apply, but it is a departure from the design and is recorded as one.

---

## 8. Reproduction

```bash
# Micro reference 0003 (cascor primary, JuniperCascor1), then compare the cuts offline
env -C /home/pcalnon/Development/python/Juniper/juniper-cascor/src /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest \
  tests/performance/test_baselines.py tests/performance/test_micro_autograd.py tests/performance/test_micro_candidate.py \
  tests/performance/test_micro_correlation.py tests/performance/test_micro_forward_pass.py tests/performance/test_micro_output_training.py \
  --run-performance --benchmark-storage=file:///home/pcalnon/.local/state/juniper-experiments/baselines/cascor-micro --benchmark-autosave
S=~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.13-64bit
python3 util/ad-hoc/2026-09-10_micro_reference_compare.py --base $S/0002_*.json --other $S/0003_*.json

# Occupancy probe (start the sampler first; stop it by the pid it records)
python3 util/ad-hoc/2026-09-10_pf8_occupancy_sampler.py --out occupancy.tsv --pid-file occ.pid --max-seconds 1800 &
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper python3 util/experiments/run_suite.py --suite util/ad-hoc/2026-09-10_pf8_occupancy_probe_suite.yaml
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CASCOR_NUM_PROCESSES=4 JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
  python3 util/experiments/run_suite.py --suite util/ad-hoc/2026-09-10_pf8_occupancy_probe_suite.yaml
python3 util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py --suite ~/.local/state/juniper-experiments/suites/<probe suite> --trace occupancy.tsv

# The pair (three parallel suites, then one control run), and its reduction
bash util/ad-hoc/2026-09-10_pf8_pair_driver.bash
python3 util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py --parallel <three pf8-two-run-parallel-* dirs> --control <two pf8-occupancy-probe-* dirs> --trace occupancy.tsv
kill "$(cat occ.pid)"

# Identity against the PF-1 baseline: PASS for the unpinned probe, REFUSED (exit 2, thread_budget) for the pinned one
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T093641Z
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T094028Z

# The mechanism: torch's pin bounds torch, only the environment variable bounds NumPy's OpenBLAS
/opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-09-10_torch_thread_pin_probe.py

# The arithmetic
python3 -m unittest -v tests/test_pf8_occupancy_probe.py
```

Retained on this host, untracked: `~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T{093641,094028,094842}Z/`,
`suites/pf8-two-run-parallel-20260910T{094518,094629,094736}Z/`, `suites/pf8-occupancy-trace-20260910.tsv`,
`suites/pf8-pair-analysis-20260910.json`, `suites/pf8-pair-driver-20260910T094518Z.log`, and
`baselines/cascor-micro/` run `0003` with `loadavg-20260910.tsv`.

---

## 9. Consensus validation

Validated under
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
Sized as a document of record closing items 4.1 and 4.2 with a novel instrument, universal-shaped
claims ("read by nothing on either path"), and blocks of n ≤ 3: **one Lane A** (artifact-first
execution of every §8 command and every table, plus an independent per-role recomputation from the
raw trace as a check on the reducer) and **one Lane B** (briefed to refute the four headline
claims, to hunt any consumer of the `runtime:` block, and to check amputation against §1.3 of the
re-scope note and the 2026-09-09 handoff). Both ran against the tree frozen at `84143b1e`; the
document was edited only after both had reported. Round 2, briefed on the corrections only, ran
against the corrected tree at `e38caf06`; round 3, briefed on rows 18–27, against `a97fb91f`;
round 4, briefed on rows 28–35, against `526d0842`; round 5, briefed on rows 36–40, against
`e1a7c72f`; round 6, briefed on row 41, against `d7a0168a`. Each
round's record below is written after that round reports.

Verdicts, round 1: **A — PASS WITH FINDINGS** (48 claims, 45 exact matches, three corrections);
**B — NOT SAFE AS WRITTEN, SAFE WITH FIXES** (claim 1 SURVIVES and is understated; claim 2
WEAKENED; claim 3 SURVIVES, WEAKENED; claim 4 REFUTED as stated, PLAUSIBLE-UNPROVEN at its core).

| # | finding | lane | disposition |
|---|---|---|---|
| 1 | control-arm ambient stated 4.4–5.7; the six cells span 4.0–5.7 | A | fixed, §3.4 |
| 2 | "the P1 design and the re-scope note both describe" the workload with `runtime.blas_threads: 2`; only the re-scope note does | A | fixed, §4.1 |
| 3 | the probe's loop count (57 vs 79) reversed on a re-run (94 vs 85) | A, B | fixed — §4.2 now says the probe does not settle throughput |
| 4 | the "sweep-worker" unit is disclaimed by §8.4 of the sweep note, which locates the knee in worker count, not cores | B (HIGH) | fixed — §2.1 states the assumption; §0 and §7 say the pair measured the externality directly |
| 5 | the high mode is one contiguous block — the initial output pass — read as a mean against a convex curve | B (HIGH) | fixed — §2.2 rewritten around the phase structure; the read-off qualified; the unpinned-pair prediction now uses the measured start alignment |
| 6 | the attribution "NumPy's OpenBLAS during output passes" is refuted as stated: ten of eleven passes run at 2 cores, and unpinned torch at the real op shape burns 7.5 cores | B (HIGH) | fixed — §4.2 rewritten: confined to the initial pass; removed by the three variables; library narrowed, not identified; the lead, §0, the CHANGELOG, the P2 plan and the reference rows re-worded |
| 7 | the 34% is 83% one phase (the first 160 steps at 8×); the other 91% of steps differ by +9.2%, inside both bands | B (HIGH) | fixed — §2.3 item 2 and §4.3 localise it |
| 8 | PF-3's second matrix axis is `runtime.num_processes` and is therefore inert; the approved ~6.7 h run cannot produce its deliverable | B (HIGH) | fixed — §0 row 2.2, §4.3, §6 item 5; P2 plan row 2.2 |
| 9 | "none inside a drive window" — the vanished pids are inside the analyser's window in every cell | B (MED) | fixed, §2.1 |
| 10 | `0003` declared superseding under a quiet-host rule whose precondition it fails | B (MED) | fixed — §0, §1, §7: recommended as the compare target, not superseding |
| 11 | "n = 6 against 6" overstates independence: three simultaneous pairs; leave-one-out +8.5 / +12.7 / +12.6% | B (MED) | fixed — §3.2, §3.3, §7 and the title carry the range |
| 12 | §1.3's ≥ 60 s cell control dropped silently | B (MED) | fixed, §3.1 and §7 |
| 13 | the band gate was applied to the default figure while the pinned arm sits outside the band, and §1.1 of the re-scope note had predicted the outcome | B (MED) | fixed, §2.2 and §3.1 |
| 14 | the CHANGELOG entry names two changed documents by role and omits `AGENTS.md` | B (MED) | fixed in `CHANGELOG.md` |
| 15 | "the two checks `compare_baseline` would apply" understates the comparator | B (MED) | fixed, §3.2 |
| 16 | occupancy is window-definition dependent (4.5 vs 4.9); "never exceed ~2" (max 2.7); "16 threads" inferred, not read | B (LOW) | fixed, §2.1, §2.2, §4.2 |
| 17 | the procedure's §7 record (lanes, entry points, iterations, dissent) was absent | B (LOW) | this section |

**Attacks that failed, recorded so they are not re-run**: mean-of-means vs pooled step time
(identical at equal step counts, and `stats_summary` computes the pooled figure); ordering / drift
(before vs after controls 0.26%); ambient asymmetry *across arms* (the parallel arm's external
ambient mean, 4.6 cores, was below the controls' 4.8 — but within the parallel arm the slowest
pair ran with ~1.5 cores more neighbours than the other two, so the 7.9% between-pair spread is
not independent of ambient, and the +8.5% leave-one-out low end carries that); thread aggregation
and double counting in the sampler; the consumer hunt for the `runtime:` block, which found none
and found `eval_metrics_enabled` inert too; the `26 tests, OK` reproduction.

**Round 2 — PASS WITH FINDINGS.** All 17 corrections present in the body and re-derived exactly
(the contiguous block at indices 0/1–14/16 with `n_workers` 0 and `current_hidden_units` 0; 82–83%
and +9.3 to +10.4%; +8.45 / +12.74 / +12.58% and p = 1/84; 4.0–5.7; 2.710; 4.9; twelve source-line
citations; the CHANGELOG's changed-file list against three commits). Ten defects the fix pass
introduced or left, all fixed before round 3:

| # | finding | disposition |
|---|---|---|
| 18 | the PF-3 block reached none of the three operator surfaces — the PF-3 rows of `docs/REFERENCE.md` and `util/experiments/suites/perf/README.md`, and `pf3-cascor-pool-scaling.yaml`'s own header still advertised the `runtime.num_processes` axis | fixed in all three |
| 19 | "+9 to +13%" rounded inward at the low end; the measured range is +8.5 / +12.7 / +12.6% | fixed — every surface carries +8.5 to +12.7% |
| 20 | "cascor's log is silent for that block" was false: the run-dir log carries the initial output-layer training as ~400 epoch lines over 18 s, and the ten later passes finishing in 2–3 s each — evidence *for* the phase reading | fixed, §4.2 |
| 21 | "four or five 5-second polls" — they are 1-second samples, about one driver poll | fixed, §2.1 |
| 22 | "16-thread" survived in §4.2 after row 16 | fixed |
| 23 | "`data` and `driver` never exceed 0.01" — the driver's post-training collect reaches 0.6–1.4 in the last in-window sample | fixed, §2.2 |
| 24 | the reducer still printed the disclaimed unit (`worker-eq`, "1.0 is one sweep worker") | fixed in `2026-09-10_pf8_occupancy_analyse.py` and the sampler's docstring |
| 25 | ranges that excluded observations: first-pass 92 (not 95) ms; pinned first pass 11 (not 12) ms; "never above 3.3" true of one suite, 3.5 across the day; 21 sweep cells vs 27 run directories | fixed, §0, §2.2, §2.3, §4.1, §4.3 |
| 26 | §9 recorded round 2 in the past tense before it ran | fixed — each round's record is written after it reports |
| 27 | "ambient asymmetry" overstated: the arm means favour the null, but within the parallel arm the slowest pair had ~1.5 cores more neighbours | fixed, above and §3.4 |

**Round 3 — PASS WITH FINDINGS** (on rows 18–27 only, against `a97fb91f`). Eight of the ten
dispositions present, correct and consistent on every surface; the measured half re-derived
again (+8.45 / +12.74 / +12.58%; 400 epoch lines over 18 s; trailing samples 4 / 4 / 5; the
driver's last-sample 0.588 / 1.267 / 1.442; external ambient per pair 5.60 / 4.22 / 3.96). Seven
items the round-2 fix pass introduced or left, plus a bundle of three observations (row 35) —
eight rows — all fixed before round 4:

| # | finding | disposition |
|---|---|---|
| 28 | the P2 plan's row 4.1 still said 95–130 ms | fixed |
| 29 | the sampler's and the reducer's headlines still said "worker-equivalents", and the pair report printed it | fixed in both scripts |
| 30 | "+9.2%" (§2.3) against "+9.3%" (§9): the figure depends on which pinned cells and which split — +9.3 to +10.4% | fixed — §2.3 states the method and the range; §9 carries it |
| 31 | §9's preamble and Termination recorded round 3 before it ran | fixed |
| 32 | "+12.57%" for the third leave-one-out value; the artifact gives +12.58% | fixed |
| 33 | "each of the ten later passes in two to three seconds" — one took one second at the log's resolution | fixed, §4.2 |
| 34 | the `runtime` line census omitted `:171` and `:174` | fixed, §4.1 |
| 35 | observations: the vanished margin's scope (default cells vs the day); §2.3's 3.3 vs §0's 3.5; "4.8" for two different quantities in §3.4 | fixed, §2.1, §2.3, §3.4 |

**Round 4 — PASS WITH FINDINGS** (on rows 28–35 only, against `526d0842`). Every one of the
eight re-derived (the split variants at +9.67 / +9.29 / +10.42%; the leave-one-out values to four
decimals; 400 epoch lines and 2, 3, 1, 2, 2, 2, 2, 2, 2, 2 s; the seven `runtime` lines; 22
tables with no column mismatch). Five items, all fixed before round 5:

| # | finding | disposition |
|---|---|---|
| 36 | "five cells on the window's final sample" — the artifact gives four (of fifteen) | fixed, §2.1 |
| 37 | the "+9 to +10%" band excluded its own +10.4% variant | fixed — "+9.3 to +10.4%" on every surface |
| 38 | the poll-boundary variant named neither its control set nor its side of the transition | fixed, §2.3 |
| 39 | §7 still said "83% one phase" beside §2.3's 82–83% | fixed |
| 40 | prose outside the two scripts still said "worker-equivalents" for what the reducer computes (the test's docstring, the probe suite's header) | fixed |

**Round 5 — PASS WITH FINDINGS** (on rows 36–40 only, against `e1a7c72f`). Rows 36–39 re-derived
exactly (four of fifteen cells; +9.67 / +9.29 / +10.42%; 82.44% / 83.02%; the split counts
160 / 148 / 160 under the poll-boundary rule). One residual, fixed before round 6:

| # | finding | disposition |
|---|---|---|
| 41 | one line of the test's docstring (its item 7) still said "worker-equivalent figure" for the cores the reducer computes; and the round-3 record said "seven items" above eight rows without saying row 35 bundles observations | fixed, both |

**Round 6 — PASS** (on row 41 only, against `d7a0168a`). The docstring line, the round-3 wording
and the round-5 record re-verified; the fix commit touched two files and only the intended lines;
the 26 tests and the structure delta (0 regressions) re-run; a sweep of every retired phrase across
the nine changed surfaces found only permitted hits (§9's own historical rows, the "~4–8
worker-equivalent band" that names the sweep's axis, and OpenBLAS sentences that carry their hedge).
Two observations, neither a defect: §1.3 of the re-scope note keeps its pre-probe
"worker-equivalent" wording, which is the dated plan §2.1 disagrees with on the record rather than
rewrites; and §2.3 cites rounds 2–4 for a comparison round 5 also re-derived. No finding changes a
number, a disposition or an action.

**Termination.** Rounds continue until one changes no number, disposition or action; rounds 1–5
each did and round 6 did not, so the rounds stop there. **Residual uncertainty, stated plainly**: the burst's library is a leading candidate, not an identification;
the pair's cost is three pairs on one day, and its between-pair spread is not independent of
ambient; the sweep-axis reading of any occupancy figure rests on an assumption the sweep did not
test.

**Post-merge correction (2026-09-10, `juniper-ml#1879`).** The validators of this session's
handoff found one number the six rounds had carried unchallenged: §7 said the pinned and default
suites were taken "forty minutes apart"; their timestamps are 09:36:41 and 09:40:28, under four
minutes apart, and the whole occupancy trace spans fifteen. Corrected in place. No disposition
or action changes; the comparison stays between-suite and not interleaved, which was the point.
