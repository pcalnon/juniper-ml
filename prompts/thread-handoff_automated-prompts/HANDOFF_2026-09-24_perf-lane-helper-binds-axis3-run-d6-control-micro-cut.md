# HANDOFF 2026-09-24 — the thread-width helper binds, PF-2 axis 3 runs, D6's zero is proven non-vacuous, and the 3.14 micro reference is cut

Successor to
[`HANDOFF_2026-09-23_perf-lane-d1-debt-clear-flip-pf1-rebaselined-pf2-axis2-ceiling-5882.md`](HANDOFF_2026-09-23_perf-lane-d1-debt-clear-flip-pf1-rebaselined-pf2-axis2-ceiling-5882.md)
(ml#2048). **§2 below consumes that handoff item by item.** Its §5 traps and §7 retained state
still hold, and so do the handoffs it points through (09-22, 09-11, 09-10, 09-09, 09-07). The
09-22 handoff's §8 carried-items table is still the brief for the carried items.

> **NOTHING IS RUNNING from this session**, except the merge wait on this handoff's own PR (§6).
> Check for strays anyway:
> `ps -eo pid,etimes,cmd --no-headers | grep -E "[r]un_suite|[l]oadavg_sampler|[s]afe_merge"`.
> Peers' cascor and juniper-data stacks will show up, and peers run test suites around the clock.
> Tell them apart by `etimes`.

Documents of record, all changed or created this session:

- [`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](../../notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md)
  ("the rulings"): the §5.4 D6 count, and a new §6 holding three rulings.
- [`notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`](../../notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md)
  ("the re-spec"): the status block; the §1 correction and #432; the §2 axis-1 blocker; the §4.2
  and §4.3 results; the §5 rows.
- `util/experiments/suites/perf/README.md`, and the three suite headers named in §6.

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session did the following:

- **Built the thread-width helper** and made CI enforce it.
- **Filed the juniper-data defect** as juniper-data#432, after reproducing it through the real
  route.
- **Counted D6 firings**, and proved with a CI positive control that the zero is real.
- **Built and ran PF-2 axis 3**, which the previous two work lists had dropped. It also probed the
  result's one anomaly over 5 dataset seeds.
- **Cut the Python 3.14 micro reference**, LOADED.
- **Recorded three owner rulings** as the rulings §6.

**The owner rulings in the rulings §5 and §6 are final. Do not re-ask them.**

- **PF-3** waits for a quiet window: no `clamscan` running, and a 1-minute load that STAYS under ~6.
- **The micro cut** is done: it went ahead LOADED.
- **PF-2 axis 1's instrument**: publish `epochs_completed` from cascor as a structured record.
  Do not parse the log.

### Work list, in priority order

1. **Converge this session's worktree after this handoff's PR merges** (git state below). The
   previous session's worktree, `.claude/worktrees/reflective-mixing-pearl`, is already
   converged. This session hashed it against `f8e04b11`: 3,052 tracked files, 0 untracked,
   0 modified, 0 missing, with LFS pointers and symlinks excluded. It is **safe to remove**. This
   session could not remove it, because the classifier refuses git aimed at a sibling worktree.
2. **PF-2 axis 1: publish the candidate count from cascor** (owner ruling, the rulings §6). The
   design sketch is grounded in the code, not built:
   - **Source.** `TrainingResults.epochs_completed` is built per candidate phase in
     `_process_training_results` (`juniper-cascor/src/cascade_correlation/cascade_correlation.py:3033`).
     It is published nowhere.
   - **Transport.** Rows reach `/v1/metrics/history` through `monitor.on_epoch_end()`
     (`src/api/lifecycle/monitor.py`, around `:258-335`). The manager drains engine history into
     `kind="training_step"` rows at `src/api/lifecycle/manager.py:2308`.
     `util/experiments/run_experiment.py:1101` saves `metrics_history.json` verbatim, so the
     driver likely needs no change. Verify that.
   - **Use an additive, nullable field on the existing `training_step` row, NOT a new row kind.**
     The field is `candidate_epochs_completed: list[int] | None`. C7's scalar metrics set the
     precedent: stable keys, always present, null where not computed. **A new kind would break
     canopy.** `juniper-canopy/src/frontend/components/metrics_panel.py:1652` takes its live
     tiles from `metrics_data[-1]`, the latest row of any kind, so a loss-less row would blank
     them.
   - **Check before merging.** Look for API snapshot fixtures under
     `src/tests/fixtures/api_snapshots/`, and for any other consumer of history rows.
   - **Then build the suite.** Set `candidate_epochs` to about 2000 in the base, or the counts are
     budget-bound. D1's debt showed 94 of 100 counts emergent at 2000. The axis-2 sample had 6 of
     8 candidates running the full 400. Add a reducer that reads the new field. The axis-1 keys
     are the re-spec §2's.
3. **PF-3, only in a quiet window.** The launch recipe is §4's last block: one pass, about 7 h,
   with the load sampler running beside it. A window opened at 02:39 local on 2026-09-24
   (4.20 / 4.09 / 3.48) and closed within minutes (8.97, a peer's test run). **Check the load at
   launch, not only before.**
4. **Recount D6** with `util/ad-hoc/2026-09-23_d6_advisory_firing_count.py` as real cascor PRs
   accumulate. At hand-off the count was 0 firings on 6 head SHAs / 28 legs. **Whether it blocks
   is the OWNER's decision, and 28 legs is not a basis for one.**
5. **PF-2 axis 3: nothing fires on its own.** The seed probe settled the 4/5 question: the
   inversion was the seed (re-spec §4.3). It also showed that one seed cannot order adjacent
   spiral counts, because the seed spread is about 5× the gap. If the owner wants a gateable
   axis, the suite needs about 5 dataset seeds per cell, compared paired. The choice of accuracy
   column (roc_auc, raw f1 or chance-adjusted f1) is a threshold decision, and **thresholds are
   the owner's.** Put it as a menu; do not decide it.
6. **Carried items**: the 09-22 handoff's §8 table, with one row now discharged. **Discharged:
   the wall-ordering survey over the new axes.** Axis 2 is OK (2400 > 2000), axis 3 OK
   (1800 > 900), PF-3 OK; 0 INVERTED, 0 EQUAL. The UNRESOLVED rows are other suites, and are the
   known worktree-path trap. Still open:
   - the three ICV residuals (ICV note §7);
   - PF-5/6/7, report-only forever;
   - P2 item 4.2's open half;
   - P2 item 5.2 (juniper-deploy);
   - the CLI-experimentation tail (its title-repair acceptance gate first).
7. **juniper-data#432 belongs to the defect-register lane**, which assigns the `APD-DATA-*` id.
   Nothing is left for this lane.

### Do NOT do these

- **Do not read a run's top-level `f1` / `roc_auc` as test figures.** `metrics_final.json`'s top
  level is the **validation** split, the one training early-stops on. The test figures are
  `eval_metrics.final`, labelled `split == "test"`.
- **Do not read `seed_policy: fixed` repeats as seed variance.** Axis 3's passes were
  bit-identical. They prove determinism and load-insensitivity, nothing more.
- **Do not claim a seed marginal from a suite.** The service exposes no network `random_seed`, so
  a suite can vary only the DATASET seed.
- **Do not compare the 3.14 micro reference with the 3.13 runs.** The store keys on the
  interpreter, and the two-part form `Linux-CPython-3.13-64bit/0003` resolves but is not
  comparable.
- **Do not write `CDLL("libgomp.so.1")` or `torch.get_num_threads()` into a new instrument.** Use
  `util/thread_width.py`. `tests/test_thread_width.py` fails CI otherwise.
- **Do not count the `ci-probe/*` `workflow_dispatch` run as a D6 firing.** The counter excludes it.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. The predecessor's work list, consumed

| # | item | state |
|---|---|---|
| 1 | confirm the merges; converge the worktree | **DONE.** ml#2031, ml#2047, ml#2048, cascor#682 and cascor#683 are all MERGED. #683's squash carries `Allow-Symbol-Loss`. Every §4 reducer and gate reproduces, including PF-1 PASS at `step_count` 1770. `reflective-mixing-pearl` is converged (item 1 above) |
| 2 | PF-2 axis 2 recorded | **DONE** in ml#2048 (`f8e04b11`). This session fixed the suite's stale `description` ("250 -> 10,000") |
| 3 | decide PF-3's host time | **RULED**: wait for a quiet window. **NOT LAUNCHED**, because the window closed within minutes. The PF-3 suite header records this |
| 4 | micro timing cut | **DONE**, LOADED by ruling: `Linux-CPython-3.14-64bit/0001`, cascor `0e016a7`, clean worktree, 71 benchmarks, 1-minute load 5.54–6.55, trace `baselines/cascor-micro/loadavg-20260924.tsv` |
| 5 | build the thread-width helper | **DONE**: `util/thread_width.py` and `tests/test_thread_width.py` (26 tests, 12 of 12 mutants), wired into CI as the 168th suite |
| 6 | count D6 firings | **DONE**: 0 on 6 SHAs / 28 legs. A positive control fired on 4 of 4 legs, so the zero is real. The blocking decision stays open |
| 7 | hand the juniper-data defect over | **DONE**: juniper-data#432, reproduced through the real route |
| 8 | carried items | wall-ordering survey **discharged** for the new axes; the rest are unchanged (work list item 6) |
| residue | PF-2 axes 1 and 3, ruled by D4 and dropped from both work lists | **axis 3 BUILT and RUN** (re-spec §4.2 and §4.3); **axis 1 BLOCKED** on its instrument, now ruled (work list item 2) |

## 3. Key context, new this session

- **The mapped libgomp is torch's BUNDLED copy.** Measured with `util/thread_width.py
  --self-check` in `JuniperCascor1`, torch 2.11.0+cu130: the runtime is
  `site-packages/torch/lib/libgomp.so.1`, NOT the env's `lib/libgomp.so.1.0.0` that the 09-11 ICV
  note recorded. `CDLL("libgomp.so.1")` called BEFORE `import torch` makes torch bind the env's
  copy instead, so the instrument would be choosing the runtime.
- **The getter hazard depends on the environment.** Unset, the raw getter re-pins a fresh thread
  16 → 8. Under `OMP_NUM_THREADS=2`, cascor's default since #683, it is 2 → 2 and invisible. An
  instrument validated in the capped environment would therefore silently corrupt its uncapped
  arm, which is why the guard is unconditional.
- **The D6 positive control.** A throwaway branch, `ci-probe/d6-advisory-positive-control-20260923`
  (cascor `47d15dd`), ran once through `workflow_dispatch` and was then deleted. It fired on 4 of
  4 legs, and every leg passed. CI's CPU-only **torch 2.14.0** observed 68, the reference value.
- **PF-2 axis 3 (re-spec §4.2).** Test roc_auc was 0.961 / 0.834 / 0.672 / 0.746 for 2..5
  spirals, with passes bit-identical. **The seed probe (re-spec §4.3) found the 4/5 inversion was
  the seed.** Over 5 dataset seeds, 4 beats 5 on roc_auc for 4 of 5 (median +0.040), on f1 for
  5 of 5 (median +0.108), and on chance-adjusted f1 for 3 of 5. roc_auc at 4 spirals spans
  0.611–0.830, about 5× the gap. **Only the dataset seed varies**: the service has no network
  `random_seed`.
- **juniper-data#432.** Requests of 5,883..10,000 get a generic 400 with the cause at DEBUG. The
  10,001 control gets a 400 WITH its message. The "422" in both the re-spec §1 and
  `rescale_generator_params`'s docstring is false.

## 4. Verification commands

```bash
git fetch origin && gh pr view 2068 --json state,mergeCommit -q '.state + " " + .mergeCommit.oid'
python3 -m unittest -q tests.test_thread_width tests.test_ci_test_wiring_drift tests.test_experiment_suite_yamls
/opt/miniforge3/envs/JuniperCascor1/bin/python util/thread_width.py --self-check        # all claims OK; hazard "SEEN" unset
python3 util/ad-hoc/2026-09-23_thread_width_mutation_check.py | tail -1                  # all mutations caught
python3 util/ad-hoc/2026-09-23_d6_advisory_firing_count.py | tail -2                     # COUNT line + the control line
/opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_data_additive_overflow_repro.py | tail -1   # "defect as filed"
python3 util/ad-hoc/2026-09-23_pf2_axis3_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-cascor-spiral-count-20260923T202816Z | tail -4
python3 util/ad-hoc/2026-09-24_pf2_axis3_seed_probe_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-seed-probe-20260924T075038Z | tail -5
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.14-64bit/   # 0001_0e016a7c..._20260924_074016.json

# PF-3, ONLY in a quiet window (the rulings §6): check `cat /proc/loadavg` first, and keep the sampler running beside it
python3 util/ad-hoc/2026-09-08_loadavg_sampler.py --out ~/.local/state/juniper-experiments/suites/pf3-loadavg-<date>.tsv --interval 30 &
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_EXP_CASCOR_SRC_DIR=/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b/src \
  python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml
```

## 5. Traps this session paid for

1. **`pkill -f <pattern>` kills its own shell** when the pattern appears in the command line that
   runs it. The call exits 144, and the sampler died with it. Kill by PID, or use `TaskStop` for a
   background task.
2. **A required check pins `AGENTS.md`'s `**Last Updated**:` to today's UTC date** whenever a PR
   touches the file (`Verify AGENTS.md Last Updated`). A one-character count edit needs the bump
   too. Here it cost a second signed commit, `7bdf4d88`, made with `push_signed_commit.py
   --expected-head`. That is safe because `safe_merge.py` merges with `--match-head-commit`.
3. **MD013 applies to table rows** (a known memory, and it bit again). Put the arguments in notes
   under the table.
4. **In a worktree-isolated session, a sibling worktree's state is checkable without git.** Hash
   its files against `git ls-tree -r <sha>` from your own worktree. Exclude LFS-tracked images,
   whose blob is a pointer, and symlinks, whose blob is the link target. The first pass reported
   98 false "modified" files.
5. **`run_suite --dry-run` prints a suite directory but creates nothing.** It does not leave
   debris.
6. **The mutation harness's first run found a survivor**: deleting the staleness check stayed
   green, because nothing was stale. The fix was to make the check testable on constructed input.
   A gate whose real input is clean today needs a synthetic case to prove it can fire.
7. **A 1.28 MB `createCommitOnBranch` payload landed on the first attempt** (ml#2068, 16 files,
   including the 821 KB `docs/REFERENCE.md`). Do not read that as a guarantee: the 499/502 memory
   still applies.
8. **The owner's sweeper applies Copilot Autofix to CodeQL findings, and one autofix BROKE the
   PR.** Commit `884e4dc6` answered "Module is imported with 'import' and 'import from'" by
   deleting `from unittest import mock` and leaving all six `mock.` uses. Every pre-commit leg
   failed on F821. **Fix forward, do not revert:** `import unittest.mock` is a plain import, so
   CodeQL stays satisfied (`09f49795`). Write `unittest.mock.<name>` from the start in this repo.
9. **`safe_merge.py` read a STALE head right after a push.** GitHub's PR object lagged the git
   ref by minutes. The first run armed the net (07:49Z) and was later killed by an external
   `timeout`; its buffered log was lost, so use `python3 -u`. The second run read `a3d133eb`
   while the ref was already `09f49795`, and its own `update-branch` failed with 422. The net
   stayed **armed on a BEHIND PR**, which under `strict:true` waits forever. Recovery: wait until
   `gh pr view --json headRefOid` shows the pushed SHA, then run one `update-branch` with
   `expected_head_sha` set to it.

## 6. Merges in flight at hand-off

| PR | state when this was written | what it carries |
|---|---|---|
| ml#2068 | **MERGED** (`2b53255a`, 09:34:15Z, squash of head `a90851e5`). It first survived a CodeQL autofix that broke it (fixed forward in `09f49795`, trap 8) and four BEHIND refreshes on a busy `main` (trap 9). All 16 files are verified in the squash | helper and gate, CI wiring, D6 count, #432 reproduction, axis-3 suite and reducer, rulings §6, re-spec corrections, micro-reference docs, PF-3 ruling in its header |
| (this PR) | open | this handoff; the seed probe (`util/ad-hoc/2026-09-24_pf2_axis3_seed_probe.yaml` and its reducer); re-spec §4.3; CHANGELOG |

**Outside PRs this session**: juniper-data#432 was filed (an issue). A cascor branch,
`ci-probe/d6-advisory-positive-control-20260923`, was pushed, run and **deleted**, and its run
cancelled after the unit legs finished. Two cascor worktrees were created and **removed**: the
probe worktree and the micro-cut worktree.

## 7. Retained state — do not delete

- Everything in the predecessor's §7.
- `~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.14-64bit/0001_*.json`
  and `loadavg-20260924.tsv`: the 3.14 micro reference and its load trace.
- `~/.local/state/juniper-experiments/suites/pf2-axis3-cascor-spiral-count-20260923T202816Z/`:
  the axis-3 evidence.
- `~/.local/state/juniper-experiments/suites/pf2-axis3-seed-probe-20260924T075038Z/`: the seed probe.
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b`:
  still the tree that PF-1, axis 2, axis 3 and the seed probe ran on. **RETAIN.**

## Git state at hand-off

- **juniper-ml**: the session worktree `.claude/worktrees/idempotent-wibbling-dongarra` is on
  branch `worktree-idempotent-wibbling-dongarra`. It carries **local-only** WIP commits and a merge
  of `origin/main`; the API-authored PRs are what reach GitHub, and the local branch is never
  pushed. **Converge after this handoff's PR merges:**
  1. `git fetch origin`, as a separate command.
  2. `git diff --stat origin/main -- <every path in both PRs>` must be empty.
  3. `git reset --hard origin/main` is safe **only after step 2 proves it**. Otherwise check out
     the differing paths and `rm` the new ones BY NAME.

  Never use `git clean`.
- **juniper-cascor**: the primary checkout was not touched. The only extra worktree is the
  retained `0d2d826` pin.
- **`.claude/worktrees/reflective-mixing-pearl`**: converged and safe to remove (work list
  item 1).
- **`.claude/worktrees/optimized-giggling-koala`**: not this lane's, and untouched.
