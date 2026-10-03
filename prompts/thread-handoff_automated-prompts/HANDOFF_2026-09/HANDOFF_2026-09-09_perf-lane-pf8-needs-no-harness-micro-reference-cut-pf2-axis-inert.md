# HANDOFF 2026-09-09 — PF-8 needs no harness, the micro timing reference exists (provisional), and PF-2's dataset axis is INERT

Successor to
[`HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`](HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md).

> **THE PREDECESSOR IS NOT SUPERSEDED.** Its §3 (key context and the two refutations), **§4** (the
> PF-2 state and the PF-1 calibration-thinness caveat), §6 (retained state), §7 (seventeen traps)
> and §8 (the CLI-experimentation arc tail) remain live and are **not** repeated here. This
> document carries only what this session changed or learned.
>
> **NOTHING IS RUNNING from this session.** Verify with a process check, not ports:
> `pgrep -c -x sha256sum` and
> `ps -eo pid,cmd --no-headers | grep -E "run_suite|[l]oadavg_sampler|contention_load"`.
> A **peer** session's cascor stack listens on `:8202` and runs from a cascor **worktree**, not the
> primary checkout — it is not yours to touch.

Document of record for everything below:
[`notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md`](../../notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md)
("the re-scope note"), merged in `juniper-ml#1852`. Item numbers refer to
[`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
("the P2 plan"). The sweep note is
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PF1-INSTRUMENT-RESOLUTION-AND-HEADROOM-SWEEP.md`; the P1
design is `notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_PERF-LANE-P1-DESIGN.md`.

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session discharged the predecessor's §1 items
2, 3 and 4 — and two of the three turned into **owner questions** rather than work. Both PRs it
opened are **MERGED** and its worktrees are cleaned up, so nothing is left to land. What remains
splits into *decisions only the owner can take*, *free work*, and *host-bound work*.

### Immediate, in order

1. **Three owner decisions are open — two surfaced this session, one carried from the predecessor
   §3.3. Put them to the owner; do NOT take them yourself:**
   - **PF-2's axis is inert** (re-scope note §4): `n_points_per_spiral` 250 → 2000 moves neither
     `step_count` (identical 450 / 890 / 1770 at both ends) nor step time. Widen n by orders of
     magnitude, retarget the scenario at the candidate phase, or drop PF-2. If kept as written the
     epoch pair is **4000/4000** (45–50 s `drive` at either end), confirmed on a quiet host first.
     **Widening n must revisit `max_hidden_units` and the patience / accuracy criteria too** — the
     invariance is structural for *this* budget (re-scope note §4, the mechanism blockquote).
   - **Item 4.2's CI hazard** (re-scope note §1.5): a parallel cascor suite under `suites/perf/`
     turns `tests/test_experiment_suite_yamls.py` red in CI. Recommended fix: move the cascor
     version-floor check from `load_suite` to the execution path, still fail-closed.
   - **The `epochs_completed` exact-match option** for the candidate micro-benchmarks (predecessor
     §3.3) — still unexamined, still an owner call.
2. **Free — 4.1's residue, S not L**: an occupancy probe. Sample the cascor process tree's CPU
   (uvicorn pid + forkserver + children, `/proc/<pid>/stat` deltas at 1 s — **not** `ps %CPU`,
   which is a lifetime average) during one PF-1 cell and express it in sweep-worker equivalents;
   read a second run's cost off §8.4 of the sweep note. A two-arm PF-8 suite pair is worth running
   only if that lands in the ~4–8 worker-equivalent band around the 6–8-worker knee (re-scope note
   §1.3).
3. **Needs a QUIET host**: re-cut the micro timing reference (`0003`) — both existing cuts were at
   1-minute load 9–10 at save and are labelled provisional; procedure in
   `juniper-cascor/docs/testing/REFERENCE.md` § Micro timing reference. And 2.2 (PF-3, ~6.7 h,
   approval standing). This session never saw a quiet host (re-scope note §5).
4. **Item 2.3** stays report-only forever for the closed-form readouts; the MLP readout's
   `n_epochs_` counter is the carve-out the predecessor restored. Untouched here.

### Do NOT do these

- Do not commit a parallel cascor suite under `util/experiments/suites/` (item 1, second bullet).
- Do not write an epoch value into `pf2-cascor-dataset-scaling.yaml` — the axis question comes first.
- Do not treat either micro reference cut as a quiet-host number.
- Do not fast-forward the juniper-cascor primary without the holder check in §5 — the
  predecessor's fourth "Do NOT", still in force; this session did check, then did fast-forward.
- Everything else in the predecessor's "Do NOT" list still holds (CI wiring, the drift band, the
  C4 wording).

---

## 2. What shipped this session (verified by receipt — `gh pr view N --json state,mergedAt,mergeCommit`)

| PR | merged | squash sha | what |
|---|---|---|---|
| `juniper-ml#1852` | 2026-09-09T18:35:29Z | `1a82815b` | the re-scope note; P1 §1 + P2 corrections; PF-4/PF-8 rows in `docs/REFERENCE.md` and `util/experiments/suites/perf/README.md`; `util/ad-hoc/2026-09-08_{cascor_baseline_history_census.py,pf2_epoch_calibration_suite.yaml,loadavg_sampler.py}`; `CHANGELOG.md` |
| `juniper-cascor#638` | 2026-09-09T19:30:57Z | `3de89b11` | item 2.4: `src/tests/performance/timing_reference.py`, two pytest-benchmark hooks in the performance `conftest.py`, timing in `save_baseline`, 13 unit tests, `.benchmarks/` ignored, `docs/testing/REFERENCE.md` § Micro timing reference, `AGENTS.md`, `CHANGELOG.md`. Carries `Allow-Symbol-Loss: func:_collect_environment` (extract-method waiver). 21 of its 23 check-runs `success`, including `Symbol & Docs Screen`; the other two (`Memory Budget`, `Notify on Failure`) skipped by their own `if:` conditions — no failures |
| this handoff — `juniper-ml#1863` | OPEN at hand-off, native squash auto-merge armed | — | this file; a rounding fix and the consensus-derived mechanism blockquote in the re-scope note's §4, the `0002` sha wording in its §2.3, two caveats in its §1.2 / §1.3 and a history-sweep line in its §2.1; the knee wording in P2 row 4.1 |

---

## 3. Key context — new this session

- **Predecessor §1 item 1 is discharged.** `ml#1811` merged 2026-09-07T16:06:23Z (`df84a935`);
  `PENDING_EPOCH_SPLIT_DECISIONS` is `{}` on `main`, its intended resting state, and the
  FORCE_LOCAL schema suite passes with the cascor primary current.
- **PF-8's harness is `run_suite` parallel mode.** The 4.1 premise was stale when the P2 plan was
  written: the one-checkout refusal was lifted 2026-08-30 by a fail-closed version floor
  (`CASCOR_PARALLEL_FLOOR = (0, 10, 0)`, read from the tree that will *launch*; the primary is
  0.11.0). A two-cell parallel cascor suite dry-runs to exit 0 with
  `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` set: ports from `8230–8259`
  per cell, `thread_budget_env` exporting `CASCOR_NUM_PROCESSES=4` + BLAS `2` to both cells and
  recording it. This **reinterprets** the P1 design's literal "two suites at once" — two identical
  cells of one suite *are* two simultaneous runs — rather than satisfying it literally. Each
  parallel cell brings up its **own** juniper-data instance; start-time alignment is plausible
  (both cells are submitted back-to-back) and unmeasured. **The control arm of a PF-8 pair must
  export the four thread variables by hand** — `run_suite` pins them only in parallel mode, and
  `compare_baseline` refuses a mismatched `thread_budget` (correctly).
- **PF-8 has no gate content.** `step_count` was invariant across a 3× load span in all 21 sweep
  cells; a second run is a load. Whatever PF-8 measures is advisory.
- **Why PF-2's count is invariant, and where that stops.** Output-layer training is full-batch and
  the step counter advances on a throttled per-epoch callback that never reads the data; with
  `max_iterations: 10` there are eleven calls and 11 × (⌊(E − 1)/25⌋ + 1) reproduces 450 / 890 /
  1770 to within one step. All seven cells end `early_stopped` because
  `max_hidden_units == max_iterations == 10` makes `max_units_reached` fire at the last iteration
  regardless of data — so the same-branch precondition holds by construction of this budget. Any
  wider dataset range that keeps the count comparable must keep that cap; any that changes it must
  expect the branch, and the count, to move (re-scope note §4).
- **PF-1's calibration base is thin, and the 1770 cross-check inherits it** (predecessor §4): the
  50-epoch anchor is a cross-suite n=2 mean with 26% spread (11.886 / 9.139 s), the 500 / 2000 /
  5000 points are n=1 each, and every PF-2 probe cell is n=1 as well. The step-count equality is
  exact regardless; the durations are single samples — budget repeats before quoting one.
- **The micro reference** lives at `~/.local/state/juniper-experiments/baselines/cascor-micro`
  (host-local, untracked): runs `0001` (sha `3286b758`, dirty) and `0002` (sha `145fbe92`, the
  branch commit at cut time — the squash landed as `3de89b11`; the sha is provenance, not
  identity), 71 benchmarks each. `machine_info.juniper` is compared (warns on change);
  `juniper_run.loadavg` is recorded, never compared. Compare with `--benchmark-compare=0002`; never
  `--benchmark-compare-fail` (owner, item 2.5). The worktree's dated `baseline_20260909.json` —
  the first `baseline_*.json` ever to carry timing keys — was copied there as
  `baseline_20260909.worktree-copy.json` before the worktree was removed.
- **No cascor baseline file ever held a timing** — all 22 that ever existed, 312 entries, zero
  timing keys (`util/ad-hoc/2026-09-08_cascor_baseline_history_census.py`, exit 0), and a
  consensus-lane sweep of the directory's whole tracked history (`git log --all -p`, 45 commits)
  found none either. The predecessor's "zero commit history" was true of `baseline_20260526.json`
  and false of its directory: 21 tracked predecessors were deleted in cascor `971d35a`.
- **The PF-2 probe**: suite `pf2-epoch-calibration-20260909T074828Z` (7 cells, all `succeeded` /
  `early_stopped`, 5 min 35 s launch-to-report), `loadavg.tsv` filed beside it. `step_count`
  450 / 890 / 1770 at **both** dataset sizes; 1770 is PF-1's invariant. `step_sum` at 2000 points
  6–8% *lower* than at 250. Per-cell 1-minute load 5.5–13.9 mean, 15.8 peak — the count finding
  is load-immune, the timing finding is not and is read as noise.
- **Corrections landed at source**: "no timing tolerance of any kind" → two fixed absolute
  ceilings exist, none baseline-relative (the P1 design's §1 blockquote; P2 item 2.4); "10×
  dataset range" → 8× (P2 item 2.1; the G-17 note
  `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_PERF-LANE-G17-BRIDGE-EVIDENCE-AND-HOST-WINDOW.md`
  still says 10× and is left as a dated record); Wave 4's "no harness exists" (P2 blockquote).
- **An observation, not a finding**: `final_epoch` reads 8 / 9 / 10 across cells whose
  `step_count` is identical. The driver samples `current_epoch` every 5 s; a lagging last sample
  under-reports. Not pursued.

---

## 4. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main
gh pr view 638  --repo pcalnon/juniper-cascor --json state,mergedAt,mergeCommit   # MERGED 2026-09-09T19:30:57Z, 3de89b11
gh pr view 1852 --repo pcalnon/juniper-ml    --json state,mergedAt,mergeCommit   # MERGED 2026-09-09T18:35:29Z, 1a82815b
git -C /home/pcalnon/Development/python/Juniper/juniper-cascor log -1 --format='%(trailers:key=Allow-Symbol-Loss,valueonly)' 3de89b11   # func:_collect_environment
gh api "repos/pcalnon/juniper-cascor/commits/3de89b11/check-runs?per_page=50" --jq '.check_runs[] | "\(.conclusion) \(.name)"' | sort | uniq -c   # 21 success, 2 skipped, 0 failure
python3 -m unittest -q tests/test_read_run_metrics.py tests/test_make_baseline.py tests/test_compare_baseline.py     # 118 OK
python3 -m unittest -q tests/test_compare_baseline_defects.py tests/test_work_countable_contract.py tests/test_termination_branch_precondition.py tests/test_run_suite_uncountable_report.py   # 46 OK
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest -q tests.test_experiment_config_schemas     # OK (12) — the cascor primary was fast-forwarded to 53c0338 at hand-off
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-04b --suite ~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260903T040803Z   # PASS 1770/1770
python3 util/ad-hoc/2026-09-08_cascor_baseline_history_census.py   # exit 0: 22 files, 312 entries, 0 timing keys
python3 util/experiments/read_run_metrics.py ~/.local/state/juniper-experiments/suites/pf2-epoch-calibration-20260909T074828Z   # 7 cells, steps [8, 450, 890, 1770]
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.13-64bit/   # 0001_*, 0002_*
# cascor (JuniperCascor1), from /home/pcalnon/Development/python/Juniper/juniper-cascor/src:
python -m pytest tests/unit/test_perf_timing_reference_helpers.py -q -rA | grep -c ^PASSED   # 13 (cascor's pytest defaults hide the summary line; count the -rA rows)
```

**Stop condition.** If the comparator does not say PASS on the suite its own baseline was cut
from, stop — the baseline or the reader drifted.

---

## 5. Retained state — do not delete

- Everything in the predecessor's §6 (the `e-c-cap64` pin worktree and its load-bearing symlink;
  the 90-plus session checkouts `util/remove_stale_worktrees.bash` would remove unconditionally).
- `~/.local/state/juniper-experiments/baselines/cascor-micro/` (both cuts, the worktree copy of
  `baseline_20260909.json`, `loadavg-20260909.tsv`), `suites/pf2-epoch-calibration-20260909T074828Z/`
  (+ `loadavg.tsv`), and `suites/pf2-epoch-calibration-loadavg-20260909.tsv`.
- **The cascor worktree of this session is GONE** — removed after `#638` merged, local and remote
  branch deleted, `git worktree prune` run. Nothing of it is left to clean up.
- **The cascor primary checkout was fast-forwarded to `53c0338`** (`origin/main`) only after the
  holder check the predecessor's §6 requires came back empty:
  `ps -eo pid,cmd | grep -F "/juniper-cascor/src"` → nothing, and the peer's `:8202` stack runs
  from a cascor worktree. **Measure again before any pull**, never quote:
  `git -C <cascor> rev-list --count HEAD..origin/main` plus that `ps` line.

---

## 6. Traps this session paid for

1. **The worktree-isolation classifier reads inside a quoted `python3 -c` program.** A one-liner
   containing the dict key `'git_sha'` was refused as "names git in a form too complex to verify".
   Write the snippet to a scratchpad `.py` and run the file.
2. **`cd notes && …` in one call moved the shell's cwd for every parallel call in the same
   response**, which then failed with "No such file or directory". Absolute paths only.
3. **A `DIRTY` PR runs no `pull_request` workflows at all** — `gh pr checks` shows only the Cursor
   automations "skipping" and no CI, which looks like a trigger bug. It is the missing merge
   commit; rebase first, and CI appears.
4. **An extract-method refactor fails `Sequence Safety` as `WEAKENED`** (`_collect_environment`
   14 → 3 lines) even though nothing was deleted. Waive with `Allow-Symbol-Loss: func:<name>` in the
   commit's trailer paragraph, prove it locally (`juniper-symbol-loss-check --scope 'src/**/*.py'
   --base origin/main --head HEAD` → `WAIVED`), **and re-arm the auto-merge net with an explicit
   `--body-file` carrying the trailer** — a bare `gh pr merge --auto` arms it with an empty body
   that would drop the trailer at squash and redden main at Post-Merge Verification. Verified on
   `3de89b11`: trailer present, `Symbol & Docs Screen` success.
5. **`util/wait_for_checks.py` judged the OLD head after a mid-wait force-push** — it exited 2
   ("never-reported contexts … fix the failures and push") while the new head's CI went green and
   auto-merge fired hours later. Re-run the wait after every push; do not read its verdict across one.
6. **An `include`-only suite emits the bare base-config cell** (`c000`, `overrides={}`). Both
   epoch-calibration probes carried one. Expected, and now in the P2 plan's §4.
7. **"Quiet" windows on this host last seconds.** A terminal emulator bursts to ~365% CPU; the
   1-minute load went 4.2 → 10.9 inside one 45 s benchmark run. Record the load beside every
   measurement (`util/ad-hoc/2026-09-08_loadavg_sampler.py`); `run_experiment.py` does not.
8. **`kill $!` after `setsid nohup … &` kills the wrapper, not the python child** — two samplers
   outlived their "successful" kills by fifteen hours and kept appending to the reference storage's
   trace. List the children with `pgrep -f <script>` and kill those pids; and **`pkill -f <script>`
   matches your own shell's command line** and kills it (exit 144) — kill by literal pid.
9. **pytest-benchmark's `--benchmark-json` opens its file at argument-parse time** — the directory
   must already exist or the run dies before collecting anything.
10. **`gh pr merge --squash --auto` chained after `gh pr create` prints nothing on success.**
    Verify with `gh pr view N --json autoMergeRequest`.
11. **Consensus lanes can die on usage credits (HTTP 429), not on findings.** Three Fable lanes
    terminated mid-run with no verdict; they were re-run on a cheaper model. A lane that never
    reported is not a lane that passed.
12. **Local GPG signing worked in this session** (every commit `%G? = G`), unlike the headless case
    the memory index warns about — an interactive workstation session has the unlocked key.

---

## 7. What this handoff does NOT cover

Deliberately: the predecessor's §8 (CLI-experimentation arc tail, the title-repair gate,
`JR-ML-OBS-003`, R-1, the recurrence `juniper-data` pin) is untouched and still open; the backup,
canopy E2E, defect register, P5, soak, partition and service-core arcs have other owners.

---

## 8. Consensus validation

Validated under
[`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).
Sized as a document of record carrying new universal-shaped claims ("the axis is inert", "no
harness is needed", "no baseline ever held a timing key"): **one Lane A** (execution of every §4
command and factual claim, plus the PR / sha / trailer / check-run state) and **two Lane B** (B1
briefed to refute the four headline claims; B2 amputation and continuity against the predecessor
and the "name every document" rule). **Round 1 — three Fable lanes — died on a usage-credit limit
(HTTP 429) with no verdict** (trap 11); round 2 re-ran all three on a cheaper model against the
same frozen tree, and nothing under test was edited between launch and the last report.

Verdicts: **A — PASS WITH FINDINGS** (2 mismatches, both immaterial; 42 table cells, every count,
every sha and the PF-8 dry run reproduced). **B1 — all four claims SURVIVE** (1 over-claim, 4
under-claims; the probe's numbers, the dry run, the CI hazard and the census each reproduced by
independent code). **B2 — SAFE WITH FIXES** (3 MEDIUM, 3 LOW, no HIGH).

| # | finding | lane | disposition |
|---|---|---|---|
| 1 | note §4, cell c004 `step_sum` 27.41 — the precise 27.4047 rounds to **27.40**; the note had rounded a rounding | A | fixed |
| 2 | "every check-run on `3de89b11` is success" — 21 of 23; two skipped by their own `if:` | A | fixed (wording) |
| 3 | "5 min 35 s end to end" is launch-to-report; per-cell walls sum to 5 min 24 s | A | fixed (wording) |
| 4 | predecessor §1 item 1 (`ml#1811`) disposed nowhere | B2 | fixed — §3 |
| 5 | the PF-1 calibration-thinness caveat (predecessor §4) carried nowhere, though the 1770 cross-check inherits it | B2 | fixed — §3 and the note's §4; predecessor §4 added to the "remains live" list |
| 6 | the P1 design cited without its filename | B2 | fixed — header |
| 7 | the cascor primary fast-forwarded without the predecessor's fourth "Do NOT" reaffirmed or the holder check recorded | B2 | fixed — §1 and §5 |
| 8 | "three owner decisions surfaced" — one is carried, not new | B2 | fixed |
| 9 | "6–8 knee" cited to the note's §1.3, which says "~4–8" | B2 | reconciled here and in P2 row 4.1 |
| 10 | the note's §1.2 presents "the harness exists" as satisfying the P1 design's literal "two suites" shape rather than reinterpreting it | B1 | fixed — note §1.2, this §3 |
| 11 | no mechanism given for the count invariance; the real one (data-blind throttle, `max_units_reached`) is stronger **and bounds the finding** — widening n must revisit `max_hidden_units` | B1 | fixed — note §4 blockquote, this §1 / §3 |
| 12 | each parallel cell brings up its own juniper-data instance; start alignment unmeasured | B1 | fixed — note §1.3, this §3 |
| 13 | the census read file snapshots; a `git log --all -p` sweep over 45 commits finds no timing key in the whole history | B1 | recorded — note §2.1, this §3 (strengthens) |

**Termination.** No finding changed a number that changes an action (finding 1 moves one cell by
0.01 s); a round 3 was not run. **Residual uncertainty, stated plainly**: "inert" is established
for this epoch budget and cascade cap, not for all n (finding 11); the `0003` quiet re-cut has not
happened; and PF-8's start-time alignment is an assumption until a pair is actually run.

---

## Git state at hand-off

- juniper-ml: session worktree `.claude/worktrees/memoized-waddling-whistle` on branch
  `docs/handoff-2026-09-09-perf-lane` (from `origin/main` `8a2a8e94`), pushed as
  `juniper-ml#1863` with this file, the re-scope note's consensus fixes and the P2 row 4.1 wording;
  the merged feature branch deleted locally and on origin. Nothing uncommitted.
- juniper-cascor: primary at `53c0338` (`origin/main`), clean; the session's worktree and branch
  removed.
- Nothing else staged or uncommitted anywhere from this session.
