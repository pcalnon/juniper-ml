# HANDOFF 2026-09-10 — PF-8 located and its pair run; the experiment YAML's `runtime:` block binds nothing, and PF-3 is blocked on it

Successor to
[`HANDOFF_2026-09-09_perf-lane-pf8-needs-no-harness-micro-reference-cut-pf2-axis-inert.md`](HANDOFF_2026-09-09_perf-lane-pf8-needs-no-harness-micro-reference-cut-pf2-axis-inert.md).

> **THE PREDECESSOR IS NOT SUPERSEDED.** Its §3 (key context), §5 (retained state), §6 (twelve
> traps) and §7 (what it does not cover) remain live and are not repeated here, and through it the
> 2026-09-07 handoff's (`HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`)
> §3, §4, §6, §7 and §8 remain live too. This document carries only what this session changed or
> learned.
>
> **NOTHING IS RUNNING from this session.** Verify with a process check, not ports:
> `pgrep -c -x sha256sum`,
> `ps -eo pid,cmd --no-headers | grep -E "[r]un_suite|[p]f8_occupancy_sampler|[l]oadavg_sampler|[p]f8_pair_driver"`.
> The samplers were killed by their recorded pid, not by `$!`, and the trace file stopped growing.
> A **peer** session's cascor stack still listens on `:8202` from a cascor worktree — not yours.

Document of record for everything below:
[`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`](../../notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md)
("the probe note"), shipped on `juniper-ml#1877`. Item numbers refer to
[`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
("the P2 plan"); "the re-scope note" is
`notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`;
"the sweep note" is `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`.

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session discharged the predecessor's §1 item 2
and advanced the micro-cut half of its item 3: the occupancy probe ran (twice), the two-arm pair ran because
the probe landed inside the band, and micro reference `0003` was cut at the best condition the arc
has seen — at ambient, not on a quiet host; item 3's PF-3 half is now BLOCKED for a new reason.
`juniper-ml#1877` is **MERGED** and the worktree is clean; this handoff is the only thing left to
land. What remains is **five owner decisions** (one of them, item 4.2's hazard, itself now
optional), one host-bound item, two optional builds, and one standing rule (item 2.3). The
probe note's consensus validation (its §9) overturned or narrowed three of the session's
first-draft claims; every shipped surface, `CHANGELOG.md` included, carries the corrected wording —
read §3 below before quoting any figure.

### Work list, in order

1. **Five owner decisions are open — put them to the owner in the session's closing report (no
   issues, no PRs for them); do NOT take them yourself:**
   - **NEW — the `runtime:` block** (probe note §4, §6 item 4). `runtime.blas_threads` /
     `runtime.num_processes` / `runtime.eval_metrics_enabled`, wherever an experiment YAML carries
     them, are validated
     by the driver, accepted by the cascor service, and **read by nothing on either path**. With
     the process env unpinned the listener's *initial* output pass burns ~11 cores and runs ~8×
     slower than with `OMP/MKL/OPENBLAS_NUM_THREADS=2 CASCOR_NUM_PROCESSES=4` exported (the other
     91% of steps differ by +9.3 to +10.4%; `step_count` identical). Counter-evidence the owner
     must see (probe note §4.3, last bullet): cascor#531 measured a BLAS cap *slowing* the
     candidate phase 1.52× and moving its epoch count — only the output phase is measured here,
     so the decision needs both phases measured under the same budget. Implement (launcher
     exports; every YAML's meaning changes; a new run-tier baseline) or retire the keys. Until
     ruled, **every new scenario must fix its thread budget explicitly** in the shell (those four
     variables; `CASCOR_NUM_PROCESSES=4` is `run_suite.thread_budget_env`'s split for
     `max_parallel: 2` on 16 cores, not a universal value) or it measures the shell — and pinning
     changes `thread_budget`, so a pinned scenario cannot be compared against `pf1-2026-09-04b`;
     it needs its own baseline (item 3).
   - **NEW — PF-3 (item 2.2) is BLOCKED on that decision.** `pf3-cascor-pool-scaling.yaml`'s
     second matrix axis is `runtime.num_processes: [1, 2, 4]`, which nothing reads, so the approved
     ~6.7 h run would be four pool sizes run three times each. Do not launch it as written.
   - **PF-2's inert axis** (carried from the predecessor §1 item 1) — unchanged; the re-scope
     must also fix the budget (above).
   - **Item 4.2's CI hazard** — now **optional**. The pair has run from `util/ad-hoc/`; a
     committed `suites/perf/` pair is needed only for routine re-runs. If wanted, the fix is
     still: move the parallel floor check from `load_suite` to the execution path, fail-closed,
     with negative tests.
   - **`epochs_completed` exact-match** (carried) — unchanged; probe note §1 adds evidence (the
     benchmarks outside ±20.5% between any two micro cuts are dominated by the candidate tier,
     12 of 18).
2. **Needs an IDLE host (still)**: a micro cut at a 1-minute load under 3 — never taken.
   Procedure: `juniper-cascor/docs/testing/REFERENCE.md` § Micro timing reference; the exact
   invocation is the first block of the probe note's §8 (`env -C …/juniper-cascor/src` pytest with
   `--benchmark-autosave` into `baselines/cascor-micro/`). `0003` (1-minute load 5.3 ambient →
   7.1 at save; the trace ran 5.17 → 7.31 over the cut) is the recommended compare target as the
   best-conditioned cut; it does **not** supersede under the quiet-host rule of that same cascor
   reference. `--benchmark-compare=0003`, never `--benchmark-compare-fail`. PF-3 is no longer
   merely host-bound — see the block above.
3. **Optional, S, if the owner rules "implement"**: `util/experiment_stack.bash` exports
   `JUNIPER_CASCOR_BLAS_THREADS` (or the three BLAS variables) from `runtime.blas_threads` and
   `CASCOR_NUM_PROCESSES` from `runtime.num_processes` at cascor bring-up; the driver's
   `environment.thread_env` capture already records the result; a **new baseline** must be cut
   before any comparison (`compare_baseline` correctly REFUSES the old one on `thread_budget`).
4. **Optional, S, the discriminating test the probe note leaves open** (§4.2): a `py-spy` profile
   (`/opt/miniforge3/envs/JuniperCascor1/bin/py-spy`; absent from the other envs and `/usr/bin`)
   of the listener's first output pass, or reading `torch.get_num_threads()` and OpenBLAS's pool
   size from inside the listener during it, to identify which library carries the ~11-core burst.
5. **Item 2.3** stays report-only forever for the closed-form readouts; the MLP readout's
   `n_epochs_` counter is the carve-out (unchanged).

### Do NOT do these

- Do not wire `runtime.blas_threads` into the launcher, cascor, or the driver as a "fix" — it is
  an owner decision, and it changes the speed regime of every service-path figure recorded.
- Do not launch PF-3 (`pf3-cascor-pool-scaling.yaml`) as written — its second axis is a no-op.
- Do not quote the +11.3% as a cost of two **unpinned** runs, or as more than three pairs on one
  day. Two unpinned runs were not measured; the phase structure predicts two start-aligned
  ~11-core first-pass bursts, and that is a prediction.
- Do not say "NumPy's OpenBLAS pool" as an established attribution. It is the leading candidate
  (the three variables remove the burst; torch's pin does not reach NumPy's pool); unpinned torch
  at the real op shape also burns 7.5 cores; no profile exists.
- Do not read "4.52 worker-equivalents" as a sweep-axis fact. It is 4.52 **cores**; the
  worker equation is an assumption §8.4 of the sweep note disclaims; the pair measured the
  externality directly.
- Do not commit `util/ad-hoc/2026-09-10_pf8_two_run_parallel_suite.yaml` (or any parallel cascor
  suite) under `util/experiments/suites/` — §1.5 of the re-scope note, still true.
- Do not fast-forward the juniper-cascor primary without the holder check in §5 — item 2's
  micro cut runs from it, and a peer's stack may be importing it.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. What shipped this session (verified by receipt)

| PR | merged | squash sha | what |
|---|---|---|---|
| `juniper-ml#1877` | 2026-09-10T12:34:17Z | `06226ed3` | everything listed below; nine authored commits (the work, the `AGENTS.md` date, one consensus fix commit per round 1–5, the round-6 close, a two-line CodeQL fix) plus one merge-from-main sync, squashed |
| this handoff — `juniper-ml#1879` | opened with native squash auto-merge armed; merged by the time you read this on `main` | — | this file, and one number in `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (§7's "forty minutes apart" → under four; a post-merge-correction paragraph after its §9 Termination) — see §8 |

`juniper-ml#1877` changed, by filename:

- `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (new — the probe note)
- `util/ad-hoc/2026-09-10_pf8_occupancy_sampler.py`, `2026-09-10_pf8_occupancy_analyse.py`,
  `2026-09-10_pf8_occupancy_probe_suite.yaml`, `2026-09-10_pf8_two_run_parallel_suite.yaml`,
  `2026-09-10_pf8_pair_driver.bash`, `2026-09-10_micro_reference_compare.py`,
  `2026-09-10_torch_thread_pin_probe.py` (all new, all under `util/ad-hoc/`)
- `tests/test_pf8_occupancy_probe.py` (new, 26 tests); wired in `.github/workflows/ci.yml`, the
  `AGENTS.md` test list (with its Last Updated date) and the `docs/REFERENCE.md` test reference
- `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`: rows 2.2 (BLOCKED) / 4.1 (DONE) /
  4.2 (EXECUTED), the §3 graph, a §4 hazard for the `runtime:` block
- `notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`:
  a dated §1.3 blockquote
- `docs/REFERENCE.md` and `util/experiments/suites/perf/README.md`: the PF-8 rows (LOCATED) and the
  PF-3 rows (BLOCKED); `util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml`: a BLOCKED header
  comment only
- `CHANGELOG.md`: one Unreleased entry naming every file above

---

## 3. Key context — new this session

- **One PF-1-shape run consumes 4.52 cores under the default budget** (3 cells, 1.1% spread
  between cells; ~8% by window definition — 4.5 first-to-last poll, 4.9 active portion) — as
  **one contiguous ~11-core block for the initial output pass** (160 of 1770 steps at 92–130 ms,
  before the candidate pool exists; samples 0/1–14/16 of 52) then ~1.8 for the other ten passes;
  the forkserver's children peak at 2.7. Under the four-variable pinned budget: **2.15**, never
  above 3.3 in any second of that suite (3.5 across the day's pinned cells), the first pass at
  11–14 ms per step (8×), the later passes +9.3 to +10.4% slower unpinned (split-dependent);
  pinned is 34% faster overall on the default base, 82–83% of it that one phase; that 34% is a
  between-suite comparison under four minutes apart (09:36:41 and 09:40:28), not interleaved
  cell by cell. `step_count` 1770 either way; `compare_baseline` PASS
  (unpinned) / REFUSED exit 2 on `thread_budget` (pinned), both as designed. Probe note §2; its
  §7 lists the residuals (window definition, the between-suite 34%, the ≥ 60 s cell length not
  met at 35–45 s).
- **The pair**: three aligned parallel pairs (start offsets 0.003 / 0.046 / 0.068 s; 88.7–100%
  of each drive window shared (one pair at 100.0% of both windows, one at 99.9%); each cell's juniper-data
  idle) against six sequential controls (three
  before, three after; before vs after 0.26% apart), same four variables, all twelve cells at 1770
  — **parallel / control = 1.1125, +11.3% per step; +8.5 / +12.7 / +12.6% leaving one pair out;
  p = 1/84**. Inside the sweep note's 20.5% band (the standing rule: below what this host can measure
  across sessions); outside the day's 4.7% / 8.7% within-arm spreads by one pair's margin.
  Advisory. The pair total was 4.01–4.06 cores. Probe note §3.
- **The `runtime:` block trace**: driver `run_experiment.py:171`, `:607-609` (validate only);
  `run_suite.py:306-307`, `:352-359` (writes overrides, hard-codes its own budget); launcher exports
  nothing (`experiment_stack.bash:633`, `:647`); cascor `api/settings.py:142-144` projects
  `service:` only; `main.py:305-320` reads `dataset.params` + `training.params` only;
  `parallelism/blas_threads.py` "do nothing" by policy; `api/__init__.py:14-16` honours
  `JUNIPER_CASCOR_BLAS_THREADS` if set. All 27 sweep run directories (21 reported cells), the 5
  baseline cells and the 7 PF-2 probe cells carry `thread_env` all-`null`. Probe note §4.1.
- **The burst, narrowed not attributed**: `util/ad-hoc/2026-09-10_torch_thread_pin_probe.py` —
  `torch.set_num_threads(2)` bounds a torch matmul to 1.9 cores and leaves a NumPy matmul at 10.9;
  the three variables at 2 (the probe never sets one alone) give 2.0; unpinned torch at the real shape (2→2 linear, 320 rows) burns
  7.5 (Lane B). cascor's parent pin is applied at construction (`cascade_correlation.py:617` →
  `:1179-1180`). Why only the first pass is unknown. Probe note §4.2.
- **Micro reference `0003`** (sha `a51b7c58`, 71 benchmarks, `juniper_run.loadavg` 7.07 / 5.80 /
  5.89 at save, trace 5.17 → 7.31). Against `0002`: median ratio 0.9945, p10–p90 0.874–1.166,
  7 of 71 outside ±20.5%; the loaded pair `0002` vs `0001` differ by as much (0.954, 4 outside).
  Of the 18 out-of-band entries across the three comparisons, 12 are candidate-tier. Probe note §1.
- **Consensus validation** of the probe note (§9; procedure
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`): round 1 —
  Lane A PASS WITH FINDINGS (48 claims, three corrections), Lane B NOT SAFE AS WRITTEN / SAFE WITH
  FIXES (5 HIGH, 7 MEDIUM, 2 LOW — 17 rows with Lane A's three; claim 4
  "NumPy during output passes" REFUTED as stated); all 17 dispositions in the note's §9 table.
  Round 2 on the corrections: PASS WITH FINDINGS — ten defects the fix pass introduced or left
  (the PF-3 block missing from all three operator surfaces; a log sentence an earlier draft had
  wrong;
  ranges that excluded their own observations; the reducer still printing the disclaimed unit),
  all fixed as §9 rows 18–27. Round 3 on those ten: PASS WITH FINDINGS — seven smaller items and a
  bundle of three observations, eight rows (a range carried in one surface and not another; the
  scripts' headlines; the split-dependent remainder figure, now stated with its method as +9.3 to
  +10.4%), fixed as rows 28–35. Round 4 on
  those: PASS WITH FINDINGS — five items down to a miscount (four cells, not five) and a band that
  excluded its own top value, fixed as rows 36–40. Round 5 on those: PASS WITH FINDINGS — one
  docstring line, fixed as row 41. Round 6 on that: PASS — stop rule met.

---

## 4. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main   # 06226ed3 or a descendant of it
git log --oneline -2 origin/main -- notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md   # juniper-ml#1879's squash (the §7 correction), then 06226ed3
gh pr view 1877 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit   # MERGED, 06226ed3
python3 -m unittest -q tests/test_pf8_occupancy_probe.py tests/test_ci_test_wiring_drift.py   # 26 + 11 = 37 OK
python3 -m unittest -q tests/test_read_run_metrics.py tests/test_make_baseline.py tests/test_compare_baseline.py   # 118 OK
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T093641Z   # PASS 1770/1770, exit 0
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T094028Z   # REFUSED (thread_budget), exit 2
python3 util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py --parallel ~/.local/state/juniper-experiments/suites/pf8-two-run-parallel-20260910T094518Z ~/.local/state/juniper-experiments/suites/pf8-two-run-parallel-20260910T094629Z ~/.local/state/juniper-experiments/suites/pf8-two-run-parallel-20260910T094736Z \
    --control ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T094028Z ~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T094842Z \
    --trace ~/.local/state/juniper-experiments/suites/pf8-occupancy-trace-20260910.tsv | tail -8   # ratio 1.1125, +11.3%, COMPARABLE
S=~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.13-64bit; python3 util/ad-hoc/2026-09-10_micro_reference_compare.py --base $S/0002_*.json --other $S/0003_*.json | head -5   # median 0.9945, 7 outside
grep -n "runtime.num_processes" util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml   # 3 hits: the header comments at :3 and :7 and the axis at :34, still there until the owner rules
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.13-64bit/   # 0001_*, 0002_*, 0003_a51b7c58*
```

**Stop condition.** If the comparator does not say PASS on the unpinned probe suite, or does not
REFUSE the pinned one, the baseline or the reader drifted — stop.

---

## 5. Retained state — do not delete

- Everything in the predecessor's §5, and §6 of
  `HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`.
- `~/.local/state/juniper-experiments/suites/pf8-occupancy-probe-20260910T{093641,094028,094842}Z/`,
  `suites/pf8-two-run-parallel-20260910T{094518,094629,094736}Z/`,
  `suites/pf8-occupancy-trace-20260910.tsv`, `suites/pf8-pair-analysis-20260910.json`,
  `suites/pf8-pair-driver-20260910T094518Z.log`; `baselines/cascor-micro/` run `0003` and
  `loadavg-20260910.tsv`.
- **The cascor primary is at `a51b7c58` (`origin/main` at session start), clean, and was NOT
  moved** — the holder check was empty and the micro cut and every probe ran from it. Before any
  pull: the holder check `ps -eo pid,cmd | grep "[/]juniper-cascor/src"` must return nothing —
  and because a cascor listener's cmdline carries no path (`python -m uvicorn api.app:create_app
  … --port 8202`), also `readlink /proc/<pid>/cwd` for every uvicorn on an 82xx port and confirm
  none sits under the primary — then measure: `git -C /home/pcalnon/Development/python/Juniper/juniper-cascor rev-list
  --count HEAD..origin/main`, as a standalone call (trap 2); the peer's `:8202` stack runs from
  a worktree.

---

## 6. Traps this session paid for

1. **`@dataclass` in a path-loaded module dies at import** unless the module is registered in
   `sys.modules` before `exec_module` — `dataclasses` resolves the owner module through it and
   gets `None`. Every `_load()` helper in `tests/` that omits the line works only because its
   script has no dataclass.
2. **The worktree classifier refuses `git -C <sibling>` inside an `&&` list but accepts it
   alone** (a `;` list was accepted once), and refuses `VAR=$(…)` before `python3`. Read a sibling repo's HEAD with `cat
   .git/HEAD` + `cat .git/refs/heads/main`; run a sibling's pytest with `env -C <dir> <python>
   -m pytest …` — no `cd`, so the shell's cwd does not move for every parallel call.
3. **A glob does not survive `env -C`**: the shell expands it against the *caller's* cwd, so name
   each file explicitly.
4. **`pgrep -c -f <script>` counts your own shell** (the wrapper's command line contains the
   script name). Use `ps -eo pid,cmd | grep "[p]attern --out"` and read the pid file.
5. **The `Verify AGENTS.md Last Updated` job fails any PR that touches `AGENTS.md` without
   bumping the header date** — even a one-line test-list addition. Bump it in the same commit.
6. **A README table row cannot wrap**: markdownlint's 512-char limit bit three times on one PF-8
   row. Budget the row before writing it.
7. **The reducer's `ambient` for a parallel cell includes its partner run** — `ambient_cores` is
   host-busy minus *this* run's trees. Read that column per arm, not across arms.
8. **Two samplers appending to one TSV double every tick.** Kill by the recorded pid, confirm
   with `ps`, then restart; before trusting a trace check for duplicate (timestamp, run_id)
   pairs — `cut -f1,3 <trace> | sort | uniq -d` must be empty. Duplicate timestamps alone are
   normal: the schema is one row per run per tick.
9. **`JR-ML-EXP-001`, cited by `juniper-ml#1852`, is in no requirements index or by-area file.**
   Do not re-cite it; say "no tracked requirement applies" instead.
10. **A mean of a bimodal trace read against a convex curve is not the curve's answer** — and a
    "~30% of the window" that is one contiguous block at the start is a *phase*, not a mixture.
    Look at the per-second series before naming a share (Lane B, §9 of the probe note).
11. **A magnitude match is not an attribution.** Two candidate mechanisms (an unpinned torch loop
    at a tiny op shape, an unpinned NumPy matmul) bracket the observed 11 cores; the probe that
    "confirmed" one of them was run at an op shape the workload never uses. Profile the process,
    or say "leading candidate".
12. **Three simultaneous pairs are three observations, not six.** Within-pair spread 0.2–1.3%
    against between-pair 7.9%; quote leave-one-out, not n = 6.

---

## 7. What this handoff does NOT cover

The predecessor's §7, and §8 of
`HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md` (CLI-experimentation arc
tail), are untouched and still open; the backup, canopy E2E, defect register, P5, soak, partition
and service-core arcs have other owners. The probe note's §7 lists eight residual uncertainties
(the window-definition ~8%, the between-suite 34%, the ≥ 60 s cell departure, n = 3 on one day
among them) — read it before quoting any figure from §3 into a new document.

---

## 8. Consensus validation

The probe note carries its own record (§9) under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`: one Lane A (artifact-first execution, 48 claims,
independent per-role recomputation from the raw trace) and one Lane B (refutation of the four
headline claims, consumer hunt, amputation check) against the tree frozen at `84143b1e`; 17
findings, every one fixed in the round-1 correction commit (`e38caf06`); round 2 on the
corrections only found ten more (rows 18–27, fixed in `a97fb91f`); round 3 on those ten found
seven smaller ones plus a bundle of three observations (eight rows, 28–35, fixed in `526d0842`); round 4 on those found five (rows 36–40,
fixed in `e1a7c72f`); round 5 on those found one docstring line (row 41, fixed in `d7a0168a`);
round 6 on that found nothing that changes a number, a disposition or an action, so the
rounds stopped at six (`80677610` records it). The rounds converged from five HIGH findings to a miscount, a
rounding and a docstring; each round's record was written after it reported. Every fix pass
introduced or left at least one defect until the last — that procedure's warning that the fix
pass is the least trustworthy part held every time. Nine authored commits on the PR (the work,
the `AGENTS.md` date, one fix commit per round 1–5, the round-6 close, a two-line CodeQL fix —
an unused import and an uncommented `except`, which held the merge behind two unresolved review
threads while every check was green) plus one merge-from-main sync, squashed on merge.

After that merge, this handoff's own validators found one number the six rounds had carried: §7's
"forty minutes apart" for suites taken at 09:36:41 and 09:40:28. Corrected in `juniper-ml#1879`,
with a post-merge-correction paragraph after the note's §9 Termination; no disposition or action
changed.

This handoff itself was validated independently before archiving, per
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`'s practice of re-probing every
assertion: round 1 by three lenses on the draft (an adversarial fact-checker that executed every §4
command, a fresh-session procedure auditor, the repo's `prompt-validator` agent) — all three FAIL,
converging on the same core (a wrong expected test count, the merge asserted before it happened, a
LOW-count miscount, two consensus-fixed qualifiers dropped, cascor#531's counter-evidence missing, a
self-matching process grep), 30 substitutions; round 2 by two fresh lenses on the corrected draft —
FAIL again (a worktree-removal instruction that
`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` Phase 4 forbids; a range that
excluded its own top value, introduced by round 1; the probe note's own "forty minutes", which six
consensus rounds had carried), all fixed; round 3 by one fresh lens on the archived file — FAIL on
two omissions (this PR's own note correction absent from §2's row and §4's comment), fixed in this
PR's second commit with six minors; every other number, citation, path and link verified clean.
Every finding was re-verified against the primary source before it was applied, and every correction
pass introduced at least one defect the next round caught.

---

## Git state at hand-off

- juniper-ml: branch `perf/pf8-occupancy-probe-2026-09-10` merged as `juniper-ml#1877`
  (squash `06226ed3`); the remote branch was auto-deleted on merge (`delete_branch_on_merge` is
  on) and the local one deleted by hand. This file on branch `docs/handoff-2026-09-10-perf-lane`
  as `juniper-ml#1879`, same remote deletion on merge. The session worktree
  `.claude/worktrees/valiant-doodling-lynx` (Claude Code's session-isolation worktree, locked,
  left on the handoff branch, clean) outlives the session like the other worktrees under
  `.claude/worktrees/`. **Do NOT remove it yourself**: it is locked, and merged-and-clean is not
  idle — Phase 4 of `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`
  requires `util/ad-hoc/2026-08-20_worktree_liveness_probe.py` and
  `util/ad-hoc/2026-09-02_worktree_inuse_probe.py` to pass first and forbids `--force` on
  `git worktree remove`. Leave it to the next authorized sweep. Nothing uncommitted.
- juniper-cascor: primary at `a51b7c58`, clean, untouched.
- Nothing else staged or uncommitted anywhere from this session.
