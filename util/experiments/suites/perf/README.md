# PF scenario suites (plan §12.3 — Wave 7.3)

Operator surface (PF-1 matched epoch pair, matrix-axis repeats, scrapeability, PF-3 stall/wall, PF-4/PF-8 not driver suites): [`docs/REFERENCE.md` § PF Scenario Suites](../../../../docs/REFERENCE.md#pf-scenario-suites).

Runnable instruments for the performance-scenario matrix. **Thresholds are deliberately absent**: §12 fixes the reuse decisions and the measurement contract only — the scenario matrix and its thresholds still need a ratification pass of their own. Run any file with:

```bash
python util/experiments/run_suite.py --suite util/experiments/suites/perf/<file>.yaml --dry-run   # inspect first
```

| ID | File | Instrument surface |
| --- | --- | --- |
| PF-1 | `pf1-cascor-spiral-repeats.yaml` | step-duration p50/p95 + wall-clock variance over 5 identical cells. **Compare against `pf1-2026-09-23-blas2`** (minted 2026-09-23, cascor `0d2d826`, `step_count` 1770 in 5/5, speed sd 3.1%). Since ml#2002 its base's `runtime: {blas_threads: 2}` binds, so `pf1-2026-09-04` / `-04b` (recorded unpinned) correctly REFUSE on `thread_budget`. They are retained: supersession is by name |
| PF-2 | `pf2-cascor-dataset-scaling.yaml` | wall-clock vs samples; RSS via the experiments dashboard Performance row. **DO NOT RUN AS WRITTEN — its `n_points_per_spiral` axis MEASURES AN INVARIANT** (`step_count` identical at 250 and 2000 at every epoch budget). Re-specified against three new axes in `notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`; axis 3 is calibrated; axis 2 is built as the row below |
| PF-2 axis 2 | `pf2-axis2-cascor-dataset-range.yaml` | wall time vs `n_points_per_spiral`, 250 → 5,800, three round-robin passes (the repeat key leads the matrix). Owner ruled "10,000 now" (2026-09-22), but the suite path's real ceiling is **5,882**: juniper-data's additive sizing adds val+test on top (1.7×) and `MAX_POINTS` binds the TOTAL, so 10,000 dies as a 400 after ~18 s (juniper-data#432). **RUN 2026-09-23: no knee** (wall x1.01, compute x1.31) |
| PF-2 axis 3 | `pf2-axis3-cascor-spiral-count.yaml` | **accuracy** vs `n_spirals` 2..5 at `max_hidden_units` / `max_iterations` 16, three round-robin passes; read with `util/ad-hoc/2026-09-23_pf2_axis3_reduce.py` (note 1). **RUN 2026-09-23**: test roc_auc 0.961 / 0.834 / 0.672 / 0.746; passes bit-identical, n = 1 seed (re-spec §4.2) |
| PF-3 | `pf3-cascor-pool-scaling.yaml` | speedup curve; oversubscription onset. ~~**BLOCKED 2026-09-10**: `runtime.num_processes` read by nothing~~ — **inert-axis blocker DISCHARGED 2026-09-22** (D2). **Re-shaped 2026-09-23** to a 14-cell triangle, and **D3's one-cell check PASSED** (delivery proven in the service log). Still do not launch the matrix: every number is wall-clock. Reasons in the suite header. **Owner ruled 2026-09-24: wait for a quiet window** (rulings doc §6) |
| PF-4 | — not a driver suite | cascor's in-repo perf suite; report-only timing reference cut with `--benchmark-autosave` outside every checkout (`juniper-cascor` `docs/testing/REFERENCE.md` § Micro timing reference). No `baseline_*.json` ever held timing data. **3.14 reference: `Linux-CPython-3.14-64bit/0001`**, 2026-09-24, cascor `0e016a7`, **LOADED** (note 2) |
| PF-5 | `pf5-recurrence-d-scaling.yaml` | fit time vs `d`; r² vs fit time |
| PF-6 | `pf6-recurrence-nsteps-scaling.yaml` | fit time vs window count |
| PF-7 | `pf7-recurrence-readout-rungs.yaml` | fit time + r² per readout rung |
| PF-8 | — not a sequential suite | two **simultaneous** pinned runs. **Run 2026-09-10** (`util/ad-hoc/2026-09-10_pf8_two_run_parallel_suite.yaml` via `2026-09-10_pf8_pair_driver.bash`): a second concurrent pinned run costs **+11.3%/step, +8.5 to +12.7% over 3 pairs** (vs 6 controls, `step_count` 1770) — advisory. One run consumes 4.52 cores unpinned / 2.15 pinned. Not checked in (fails the R-6 gate in CI; P2 4.2, now optional). `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` |

Notes (the arguments behind two table cells; MD013 applies to table rows):

1. **PF-2 axis 3.** The suite's own aggregate carries only the budget-bound structural columns, and a run's TOP-LEVEL f1 / roc_auc are the selected-on validation split, so the reducer reads `eval_metrics.final` (`split == "test"`). It separates 2 → 3 → 4 spirals; 5 does not rank below 4 on this one seed. The bit-identical passes prove determinism and load-insensitivity, not seed variance.
2. **PF-4's 3.14 reference.** 71 benchmarks from a clean detached cascor worktree, at 1-minute load 5.54–6.55 during the cut (`baselines/cascor-micro/loadavg-20260924.tsv`). It was cut by owner ruling rather than after waiting further (`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` §6). Compare with `--benchmark-compare=0001`, never `--benchmark-compare-fail`; a quieter cut supersedes it by number. The 3.13 runs `0001`–`0003` cannot be compared across the interpreter change.
