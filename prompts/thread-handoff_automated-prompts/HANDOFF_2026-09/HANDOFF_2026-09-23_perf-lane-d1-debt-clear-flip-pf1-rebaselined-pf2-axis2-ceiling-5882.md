# HANDOFF 2026-09-23 — D1's debt paid (CLEAR) and the flip shipped; PF-1 re-baselined, PF-3 re-shaped, PF-2 axis 2 built at a 5,882 ceiling

Successor to
[`HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md`](HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md)
(ml#2013). **That handoff is CONSUMED item by item in §2 below.** Its §8 carried items and §9
loaded-host design are still live, and so are the handoffs it points through (09-11, 09-10,
09-09, 09-07).

> **NOTHING IS RUNNING from this session** except the merge wait on this handoff's own PR (§6). No listener,
> no port, no experiment stack. Check for strays anyway:
> `ps -eo pid,etimes,cmd --no-headers | grep -E "[r]un_suite|[d]1_epoch_count_sweep|[s]afe_merge"`.
> Peers' cascor stacks will also show up (`:8202` has held one for days). Discriminate by
> `etimes`.

Documents of record, all changed or created this session:
[`notes/JUNIPER_2026-09-23_JUNIPER-ECOSYSTEM_PERF-LANE-D1-EPOCH-COUNT-DEBT.md`](../../notes/JUNIPER_2026-09-23_JUNIPER-ECOSYSTEM_PERF-LANE-D1-EPOCH-COUNT-DEBT.md)
("the debt note", new);
[`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](../../notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md)
("the rulings", new §5);
[`notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`](../../notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md)
("the PF-2 re-spec", second §1 correction);
[`notes/JUNIPER_2026-09-17_JUNIPER-ECOSYSTEM_PERF-LANE-EPOCHS-COMPLETED-SPREAD.md`](../../notes/JUNIPER_2026-09-17_JUNIPER-ECOSYSTEM_PERF-LANE-EPOCHS-COMPLETED-SPREAD.md)
("the 09-17 note", rescued and committed by ml#2031).

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session:

- got the owner's rulings on all four `Not decided:` clauses;
- paid D1's epoch-count debt (verdict **CLEAR**) and shipped the flip;
- minted PF-1's successor baseline;
- re-shaped PF-3 and passed D3's one-cell check;
- built PF-2 axis 2;
- shipped D6's advisory gate.

The owner rulings, recorded in §5 of the rulings, are final. Do **not** re-ask them:

- **D2**: `runtime.blas_threads` / `num_processes` / `eval_metrics_enabled` are ratified as-is,
  with no second knob.
- **D4 axis 2**: "10,000 now, in-process later". The in-process follow-up fires only on a knee.
- **D6**: advisory first.
- **D1**: "pay the debt, then flip". It was paid, and the flip is juniper-cascor#683.

### Work list, in priority order

1. **Nothing to confirm; every PR landed.** ml#2031, ml#2047, cascor#682 and cascor#683 are all
   MERGED (§6), and cascor's post-merge verification passed on the flip. The only open item is
   this handoff's own PR. Converge the session worktree after it merges (git state below).
2. **PF-2 axis 2 is RUN, with no knee. Record it; nothing further fires.**
   - All 18 cells succeeded over 3 round-robin passes at load 5–8. Evidence:
     `~/.local/state/juniper-experiments/suites/pf2-axis2-cascor-dataset-range-20260923T142812Z/`.
     Reducer: `util/ad-hoc/2026-09-23_pf2_axis2_reduce.py`.
   - **Wall time is flat**: a median of 24.1 s at 250 points per spiral against 24.4 s at 5,800
     (×1.01). It is overhead-dominated.
   - **Training compute (`step_sum`) grows only ×1.31** over the 23× range, with log-log slopes
     of −0.15 to 0.31 between neighbours.
   - **No knee, so the owner's in-process follow-up does NOT fire** (the rulings §5, D4).
   - This holds at `spiral-smoke`'s budgets only (2 hidden units, `output_epochs` 50, and a
     budget-bound `step_count` of 8). A larger-budget workload is a different question.
   - **Recorded in this handoff's own PR**, cut after ml#2047 merged: the PF-2 re-spec §3
     RESULT block and its §5 row, the suite header, the README row and the CHANGELOG.
     Nothing is left to do here.
3. **Decide PF-3's host time.** The suite is ready: 14 cells, about 7 h per pass. The loaded-host
   design needs round-robin passes, which means a LEADING repeat key; axis 2 shows how. That is
   about 21 h for 3 passes. Or wait for a 1-minute load under 3. Thresholds are still unratified.
4. **The micro timing cut is still not taken** (seventh session). Cut a fresh **3.14** reference,
   report-only, with `--benchmark-compare=<N>` and never `--benchmark-compare-fail`. The procedure
   is at the ABSOLUTE path
   `/home/pcalnon/Development/python/Juniper/juniper-cascor/docs/testing/REFERENCE.md` § Micro
   timing reference. The runnable block is §8 of
   `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`. Load was 4.8–10
   for stretches today; that is not idle, but record it and cut if it holds low.
5. **Build the thread-width helper** ("prose warnings do not bind", debt 2 of the predecessor).
   One shared module should read the ICV through the MAPPED libgomp (from `/proc/self/maps`, not
   `CDLL("libgomp.so.1")`) and install a guard that makes `torch.get_num_threads()` raise off the
   main thread. Deferred this session because it needs `ci.yml`'s hand-maintained test list,
   `docs/REFERENCE.md`'s suite list and the AGENTS.md count: the highest-conflict files.
6. **Count D6 firings.** cascor#682's advisory writes a `::warning` annotation titled
   `D6 advisory - epochs_completed drift`. Count it across real cascor PRs:
   `gh api repos/pcalnon/juniper-cascor/check-runs/<id>/annotations`, or
   `grep -F '##[warning]D6 advisory - epochs_completed drift'` over job logs. The count decides
   whether it blocks, and that decision is the OWNER's.
7. **Hand the juniper-data defect to the defect-register owner.** It is not filed. When requested
   `n_points_per_spiral` × 1.7 (additive val+test sizing) exceeds `MAX_POINTS`, generation raises
   a pydantic `ValidationError`. The field check passed, so the API returns a generic **400
   "Invalid request parameters"** with the cause logged only at DEBUG. The PF-2 re-spec's second
   §1 correction has the mechanism and the bisection (5,882 / 5,883).
8. **Carried items**: the predecessor's §8 table, unchanged. Two notes on it: the wall-ordering
   survey should now be run over the NEW axis-2 suite, and P2 item 4.2's open half is untouched.

### Do NOT do these

- **Do not quote any `fit_seconds` / wall figure from the debt run or the scope probe.** They
  were taken at 1-minute loads of 8–31, and `none`'s own fit time ranged 99–232 s across its
  three repeats. Only counts and numerics are results there.
- **Do not cite load 54.49** for D6. #2015 withdrew it as unsourced. The sourced loads are 12.08,
  19.50 and 32.26. The D6 agent cited 54.49 from a stale copy; cascor#682 was corrected.
- **Do not read `run_suite --only`'s exit 1 as a failed check.** Exit 0 means the FULL expansion
  succeeded; that is documented design, and the docstring now says so. Read the manifest.
- **Do not treat a budget-bound count as evidence.** Hidden units, output epochs and `step_count`
  under `spiral-smoke` all equal their budgets. The scope probe's "invariant holds" at
  `step_count` 8 is exactly that non-finding.
- **Do not describe the ceiling as 10,000.** The request ceiling is 5,882 at the suite's split;
  10,000 is the TOTAL rows per spiral.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. The predecessor's work list, consumed

| # | item | state |
|---|---|---|
| 1 | cut one new PF-1 baseline | **DONE**: `pf1-2026-09-23-blas2`, capped, cascor `0d2d826`, `step_count` 1770 in 5/5, speed sd 3.1%. It PASSes on a load-16 run and REFUSEs against `-04b` on `thread_budget`, as designed |
| 2 | PF-3 re-shape + D3 one-cell | **DONE**: 14-cell triangle (np > pool dropped; np=1 kept as the sequential control; np extended to 8/16). D3 PASSED on c001: `CASCOR_NUM_PROCESSES` "2", and the log shows `Training 2 candidates with 2 processes` |
| 3 | D4 axis 2 to the owner | **RULED** "10k now, in-process later"; **BUILT**, with the ceiling at 5,882; **RUN**: no knee, so the in-process follow-up does not fire |
| 4 | commit or retire the 09-17 D6 work | **COMMITTED** (ml#2031) minus one unused import (CodeQL). The worktree was NOT locked |
| 5 | micro timing cut | **NOT DONE**: work list item 4 |
| 6 | cascor thread-pin defect | **RULED and SHIPPED**: the process default, cap 2, opt-out `0`/`off`/`none` (cascor#683) |
| 7 | carried items | unchanged; work list item 8 |
| debt 1 | D1/D2 epoch counts | **PAID**: the debt note, verdict CLEAR |
| debt 2 | the thread-width helper | **NOT DONE**: work list item 5 |

## 3. Key context, new this session

- **The debt verdict** (the debt note §3). The instrument is
  `util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py`: 5 arms × 3 interleaved repeats, cascor
  `0d2d826`.
  - Budgets were calibrated first: `candidate_epochs` 2000 gives 94/100 emergent counts. The
    09-16 sweep's counts were all budget-bound.
  - **`env2` (the flip) and `env16` are bit-identical to the old default**: final loss
    0.0067392201 in every repeat.
  - `thread16` diverges at phase 20 (one candidate 1450→1442), and the seed control diverges
    from phase 0. So #531's channel is real, but it needs width SUSTAINED through the later
    passes. Why phase 20 is untested (a hypothesis in the debt note).
  - A same-day **scope probe** at a ~60× larger first pass (5,800/spiral on the suite path) gave
    bit-identical final metrics across widths 2 and unset. Its counts are budget-bound, and the
    debt note says so.
- **The flip** (cascor#683): `configure_blas_threads()` defaults to 2, with `setdefault`
  semantics, so the experiment launcher's `runtime.blas_threads` still wins. `0`/`off`/`none`
  opt out. **Deployment consequence**: a service container that exports none of these variables
  now runs BLAS 2 wide. juniper-deploy's compose sets none of them.
- **D6 advisory** (cascor#682): it is a `unit`-marked test, because CI never runs `performance`.
  It never blocks, and genuine errors still fail. The annotation mechanism needs
  `capsys.disabled` plus a leading newline. The agent corrected two premises of the brief:
  writing to `sys.__stdout__` does NOT get past pytest's capture, and the job log drops the
  annotation title.
- **Owner-menu lesson**: my first D1 menu described the process default as new work. It already
  existed, with the opposite default. Memory: `feedback_ground_owner_menus_in_the_code`.

## 4. Verification commands

```bash
git fetch origin && gh pr view 2031 --json state -q .state && gh pr view 2047 --json state -q .state
gh pr view 682 --repo pcalnon/juniper-cascor --json state -q .state
gh pr view 683 --repo pcalnon/juniper-cascor --json state,mergeCommit -q '.state + " " + .mergeCommit.oid'
gh api repos/pcalnon/juniper-cascor/commits/f7a6d57347dad86d830bbf80b735ba6e54bb3868 --jq .commit.message | grep Allow-Symbol-Loss   # must print (#683's squash)
python3 util/ad-hoc/2026-09-23_d1_epoch_debt_reduce.py ~/.local/state/juniper-experiments/suites/d1-epoch-debt-20260923 | tail -6
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-23-blas2 --suite ~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260923T125905Z   # PASS
python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf2-axis2-cascor-dataset-range.yaml --dry-run | head -2   # 18 cells
python3 -m unittest -q tests.test_run_suite tests.test_experiment_suite_yamls
```

## 5. Traps this session paid for

1. **From a session worktree, the experiment stack cannot find cascor.** `PROJECT_DIR` derives
   to `.claude/worktrees`. Export `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`,
   and pin code with `JUNIPER_EXP_CASCOR_SRC_DIR=<detached cascor worktree>/src`. The base CONFIG
   still comes from the primary via the rebase, so check the two agree.
2. **`git reset --soft` leaves edits STAGED, so `git diff <path>` is empty.** An empty patch plus
   `git checkout --` destroyed an edit. It was recovered only because the edit was scripted. Save
   with `git diff HEAD`. Recorded in the memory `reference_open_signed_pr_whole_file_clobber`.
3. **A 245 KB `CHANGELOG.md` in `open_signed_pr.py` hit a GraphQL error.** The BRANCH was created
   with no commit. Retry with `util/push_signed_commit.py --expected-head <that branch sha>`, then
   create the PR with `gh api -X POST …/pulls`.
4. **A same-file test RENAME is symbol LOSS.** cascor's Sequence Safety FAILed on two renamed
   test methods. The waiver must be in the PR's SINGLE commit, because cascor squashes with first-commit
   semantics. Fix it WITHOUT re-cutting: create a temp branch at main, commit once with the
   trailer as the last paragraph, force-move the PR ref, delete the temp branch. The PR keeps its
   number. Disarm any auto-merge first: its stored body is an arm-time snapshot.
5. **CodeQL "unused import" blocks a merge with every check green.** Fix, don't suppress. The
   thread auto-resolves as outdated.
6. **A reducer that compares whole records needs its volatile fields excluded.** `timestamp`
   made four bit-identical runs read "DIFFER".
7. **A behaviour "fix" to documented design gets reverted.** `run_suite --only`'s exit code
   looked like a bug and is REFERENCE-documented design. Read the reference before changing a
   contract; this session changed the docstring instead.
8. **`update-branch` on a CHANGELOG-heavy PR conflicts** whenever another PR inserts at the same
   spot. Append at the END of `[Unreleased]`, away from other sessions' top-of-list insertions,
   and the merge stays clean (ml#2047 vs ml#2031). **A release cut is the exception:** v0.10.0
   was cut under this handoff's PR (ml#2049 closed `[Unreleased]` into `[0.10.0]`, released
   15:10Z). The PR went DIRTY, and its entry was moved into a fresh `[Unreleased]`. Never
   resolve such a conflict into the released heading: its notes cannot be re-cut.
9. **GitHub's squash splits a trailer block.** On cascor#683's squash commit each trailer landed
   in its own paragraph, so `git interpret-trailers --parse` sees only the last one
   (`Co-authored-by`). The symbol screen reads the
   body instead, and still honored `Allow-Symbol-Loss` (verified against `f7a6d573`, and by
   post-merge verification). To judge whether a waiver survived, re-run the screen on main's
   commit; git's trailer parser answers a different question.

## 6. Merges in flight at hand-off

| PR | state when this was written | what it carries |
|---|---|---|
| ml#2013 | **MERGED** | the predecessor handoff |
| ml#2015 | **MERGED** (`d52daef6`) | the predecessor's corrections: 54.49 withdrawn, and two numbers fixed |
| ml#2047 | **MERGED** (`a77e69b6`, 14:45Z) | rulings §5; the debt note, instrument and reducer; the scope probe; PF-1 docs; PF-3 re-shape; PF-2 axis 2 suite and 5,882 correction; `run_suite` docstring |
| cascor#682 | **MERGED** (`b118e62e`, 14:39Z) | the D6 advisory gate |
| ml#2031 | **MERGED** (`9d6c2eba`, 14:55Z) | the 09-17 D6 instrument and note |
| cascor#683 | **MERGED** (`f7a6d573`, 15:01Z) | the D1 flip, as ONE commit carrying the `Allow-Symbol-Loss` waiver. On `main`, **all five workflows are SUCCESS**: Post-Merge Main Verification, Golden Regression, Conformance, CodeQL and CI/CD Pipeline |
| (this PR) | open | this handoff; the PF-2 axis 2 RESULT in re-spec §3, the suite header, the README and the CHANGELOG; `util/ad-hoc/2026-09-23_pf2_axis2_reduce.py` |

**The waiver survived, though git no longer calls it a trailer.** GitHub's squash put each
trailer line of `f7a6d573` in its own paragraph, so `git log --format='%(trailers)'` does not see
`Allow-Symbol-Loss` on `main`. `juniper-symbol-loss-check` reads the line from the body and still
WAIVED both findings on that exact commit, and cascor's post-merge verification agreed (§5 trap 9).

## 7. Retained state — do not delete

- Everything in the predecessor's §5, except that the `optimized-giggling-koala` entry is now
  moot: its two files are committed (ml#2031). It was never locked, and the worktree is not
  this lane's to remove.
- `~/.local/state/juniper-experiments/baselines/pf1-2026-09-23-blas2/`: the current PF-1 tag.
- `~/.local/state/juniper-experiments/suites/d1-epoch-debt-20260923/`: 15 arm JSONs plus
  `debt.json`, the CLEAR evidence.
- `~/.local/state/juniper-experiments/suites/d1-scope-large-first-pass-20260923T142003Z/`: the
  scope probe.
- `~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260923T125905Z/`: the
  baseline's source runs. `…-20260923T013257Z/` holds the load-16 run, evidence that the work
  half is load-immune.
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b`:
  detached, clean, pinned at `0d2d826`. **It is the tree every measurement above ran against.**
  Remove it only once nothing cites a re-run against it; the SHA is what matters.

## Git state at hand-off

- **juniper-ml**: the session worktree `.claude/worktrees/reflective-mixing-pearl` is on branch
  `worktree-reflective-mixing-pearl` at `a77e69b6` (then `main`). Its uncommitted files are
  exactly this handoff PR's; they reach GitHub through the API, and the local branch is never
  pushed. **After this PR merges, converge before any other work** (this session converges it
  if the merge lands while it is still open, so check `git status` first):
  1. Hash-check every file against `origin/main` with ONE plain command:
     `git diff --stat origin/main -- <paths>`. **Fetch first, as a separate command**; a stale
     `origin/main` makes every file look different.
  2. `git checkout --` the tracked files, then `rm` the new ones BY NAME.
  3. `git merge --ff-only origin/main`.

  Never use `git clean`.
- **juniper-cascor**: the primary checkout was never touched by this session.
  - `worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b`: detached, clean.
    **RETAIN** (§7).
  - The flip and D6 worktrees (`…perf--d1-blas-default-two…` and
    `…test--d6-epochs-completed-advisory…`) are **REMOVED**. Their contents were first proven
    identical to post-merge `main`. The local branches are deleted and the metadata pruned; the
    remote branches had already auto-deleted on merge.
- **`.claude/worktrees/optimized-giggling-koala`**: not this session's, and not touched. Its two
  09-17 files are committed by ml#2031 (merged).
