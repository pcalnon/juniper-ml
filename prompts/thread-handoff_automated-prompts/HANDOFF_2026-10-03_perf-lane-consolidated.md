# HANDOFF 2026-10-03 — Performance lane + `util/experiments/` residue (CONSOLIDATED): all perf PRs merged; PF-2 axis 1 (cascor field) is next, PF-3 waits for a quiet window, five run_suite defects await an owner ruling

**Consolidated sources** (all in `prompts/thread-handoff_automated-prompts/`):

| source | self-declared validation |
|---|---|
| `HANDOFF_2026-09-24_perf-lane-helper-binds-axis3-run-d6-control-micro-cut.md` (primary) | no explicit validation statement; every claim is receipt-style ("verified in the squash", reducers re-run). Treated as validated-by-receipt |
| `HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md` | "Adversarial validation was run … The handoff you are reading was validated the same way" (its §7) |
| `HANDOFF_2026-09-23_perf-lane-d1-debt-clear-flip-pf1-rebaselined-pf2-axis2-ceiling-5882.md` (pointed through: §5 traps, §7 retained state) | receipt-style, no explicit validation round |
| `HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md` (pointed through: §8 carried items, §9 loaded-host design, §5/§6) | receipt-style; corrections recorded inline |
| `HANDOFF_2026-09-11_…burst-terminator…`, `HANDOFF_2026-09-10_…burst-is-libgomp…`, `HANDOFF_2026-09-10_…pf8-located…`, `HANDOFF_2026-09-09_…pf8-needs-no-harness…`, `HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md` (older pointers; only still-relevant traps / retained state / the CLI tail carried) | 09-07, 09-09, 09-10 carry consensus-validation sections; 09-11 was re-probed and amended in place 2026-09-22 |

**Supersedes**: the two assigned sources above (each now carries a SUPERSEDED banner). The pointed-through predecessors are history; everything still live in them is carried here.

**Live probe**: 2026-10-03, approx. 08:15–09:00 UTC, from worktree `.claude/worktrees/snappy-strolling-waterfall` (origin/main `afb02801`).

---

## Goal statement (paste as the new thread's first prompt)

Continue the **juniper-ml performance lane** (PF-1..PF-8 suites, owner decisions D1–D6, the thread-width helper, the micro timing reference) and its **`util/experiments/` harness residue**.

**Completed so far** (all merged; `[VERIFIED 2026-10-03: gh pr view]`):

- D2: the experiment YAML `runtime:` block binds (ml#2002, `f8ffaa48`). D6 spread measured zero, premise refuted (ml#2002); D6 advisory gate shipped in cascor (cascor#682, `b118e62e`), and a CI positive control proved its zero non-vacuous (ml#2068).
- D1: epoch-count debt paid, verdict CLEAR; the BLAS default flip to 2 shipped (cascor#683, `f7a6d573`, carries `Allow-Symbol-Loss`).
- PF-1 successor baseline `pf1-2026-09-23-blas2` minted (capped, cascor `0d2d826`). PF-3 re-shaped to 14 cells; D3's one-cell check passed. PF-2 axis 2 built at the 5,882 ceiling and run (no knee, so the in-process follow-up does not fire). PF-2 axis 3 built and run, plus a 5-seed probe (ml#2068, ml#2078).
- `util/thread_width.py` + `tests/test_thread_width.py` built and wired into CI as the 168th suite (ml#2068, `2b53255a`).
- Python 3.14 micro reference cut, LOADED by owner ruling: `Linux-CPython-3.14-64bit/0001` (cascor `0e016a7`).
- juniper-data#432 filed (additive-sizing 400). 09-17 D6 work rescued (ml#2031). Owner rulings recorded in `notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` §5 and §6.
- The 09-24 handoff's own merge-wait PR, **ml#2078, MERGED** 2026-09-24T09:45:51Z as `514b6c24`.

**Owner rulings in the rulings note (`…SIX-OWNER-DECISIONS-RULED.md`) §5 and §6 are FINAL — do not re-ask.** PF-3 waits for a quiet window (no `clamscan`, 1-minute load that STAYS under ~6). PF-2 axis 1's instrument: publish `epochs_completed` from cascor as a structured record; do not parse the log. D2 key names ratified as-is, no second knob. D4 axis 2 "10,000 now, in-process later". D6 advisory first. D1 "pay the debt, then flip" (done).

**Remaining work, in priority order:**

1. **PF-2 axis 1 — publish the candidate count from cascor** (agent-doable, cross-repo cascor PR; owner already ruled the instrument). Source: `TrainingResults.epochs_completed`,
   built in `_process_training_results` (cascor `src/cascade_correlation/cascade_correlation.py`, def now at `:2986`, `epochs_completed` at `:3035`) `[VERIFIED 2026-10-03: gh contents;
   the source's :3033 was imprecise; the file is unchanged since 010d0359]`. Transport: `monitor.on_epoch_end()` (`src/api/lifecycle/monitor.py:258`; its `kind` defaults to
   `"training_step"` at `:267`) `[VERIFIED 2026-10-03: gh contents]`. The drain is `_extract_and_record_metrics` (`src/api/lifecycle/manager.py`, def `:2332`), whose per-row
   `self.monitor.on_epoch_end(...)` call passes no `kind=` and so writes `training_step` rows; that call moved from `:2308` to `:2386` after 4 `manager.py` commits since 09-24
   `[CHANGED SINCE HANDOFF: +78 lines]`. **Do not add the field at `:2058-2076`**: `:2058` is `on_epoch_end(kind="output_epoch")`, and `:2074-2076` are that output-epoch path's
   Prometheus observe and debug log. `util/experiments/run_experiment.py` saves `metrics_history.json` verbatim (now `:1103`, was `:1101`) — verify the
   driver needs no change. **Additive nullable field `candidate_epochs_completed: list[int] | None` on the existing `training_step` row — NOT a new row kind** (canopy
   `src/frontend/components/metrics_panel.py:1652` reads tiles from `metrics_data[-1]`, `[VERIFIED 2026-10-03]`; a loss-less row would blank them). Check
   `src/tests/fixtures/api_snapshots/` and every other history-row consumer before merging. Then build the suite: `candidate_epochs` ≈ 2000 in the base (or counts are
   budget-bound), a reducer reading the new field, keys per `notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md` §2. No cascor PR for this exists yet
   `[VERIFIED 2026-10-03: gh pr list search]`.
2. **PF-3 — only in a quiet window** (owner-gated by ruling; agent launches when the condition holds). One pass ≈ 7 h, load sampler beside it; recipe in Verification commands. **Check load AT launch, not only before.** At probe time load was 6.16 / 4.27 / 3.49 and no `clamscan` ran `[VERIFIED 2026-10-03: /proc/loadavg, ps]` — borderline, not a window. Not launched since 09-24 (only the 09-23 D3 one-cell dir exists) `[VERIFIED 2026-10-03: ls suites/]`. Thresholds remain UNRATIFIED; report, don't gate.
3. **Present the D6 recount to the owner** (owner-gated decision; recount already run 2026-10-03 with `util/ad-hoc/2026-09-23_d6_advisory_firing_count.py`). At 09-24: 0 firings / 6 SHAs / 28 legs. Cascor has merged ≥6 non-dependabot
   PRs since `[VERIFIED 2026-10-03: gh api commits]`. **Recounted 2026-10-03: 0 firings on 36 head SHAs / 168 legs; the positive control still fired on 4 of 4** `[VERIFIED
   2026-10-03: ran the counter, ~9 min]`. Many of the new SHAs are dependabot or CI bumps that do not touch candidate numerics, so the count says little about how often the gate
   fires on intended changes (the tree-sensitivity question in Context §D). **Whether it blocks is the OWNER's decision; present counts, not a recommendation.**
4. **`util/experiments/` defects APD-ML-002..006** `[ALSO P3]` (owner-gated: filed in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9, "UNPARKED, and NOT
   thereby actionable … need an owner decision before code is written" — still so on main `[VERIFIED 2026-10-03: grep register]`). Put them to the owner as one menu; detail in
   Context §C. Sequencing: APD-ML-002 (`_headline_metrics`) ships with first tests for the registry `metrics` columns; APD-ML-003 must repair both `run_suite.py:28-29` and
   `docs/REFERENCE.md`'s exit-code table.
5. **PF-2 axis 3 gating menu** (owner-gated: thresholds are the owner's). One dataset seed cannot order adjacent spiral counts (seed spread ≈ 5× the 4-vs-5 gap). Present as a menu: ~5 dataset seeds per cell compared paired, and the accuracy column choice (roc_auc / raw f1 / chance-adjusted f1). Do not decide it.
6. **Carried items** (from `HANDOFF_2026-09-22_perf-lane-d2-…` §8; substance in Context §D) — all optional / report-only: the three ICV residuals; PF-5/6/7 never executed (report-only forever); P2 item 4.2's open half (should PF-8 get a parallel cascor suite); P2 item 5.2 experiment-scoped alerts (juniper-deploy) `[ALSO P4?]`; the CLI-experimentation tail (title-repair acceptance gate first — still exit 1, 91 artifacts `[VERIFIED 2026-10-03: ran --check unpiped]`).
7. **Housekeeping** (agent-doable but cross-worktree git is refused to an isolated session — owner or a non-isolated session): remove converged worktrees `.claude/worktrees/reflective-mixing-pearl` (HEAD `f8e04b11`) and `.claude/worktrees/idempotent-wibbling-dongarra` (HEAD `514b6c24` = ml#2078's squash, i.e. already reset onto main) after a cleanliness check; both still exist `[VERIFIED 2026-10-03: git worktree list]`. Cleanliness NOT probed (classifier).

**Key context:** never quote wall-clock figures from loaded runs; structural outcomes (`step_count`, `epochs_completed`, thread counts) are load-insensitive, wall clock is not.
`metrics_final.json`'s top level is the VALIDATION split; test figures are `eval_metrics.final` (`split == "test"`). Use `util/thread_width.py`, never `CDLL("libgomp.so.1")` or
`torch.get_num_threads()`, in any new instrument. From a session worktree export `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper` and pin
`JUNIPER_EXP_CASCOR_SRC_DIR`. Full trap list in Context §A.

---

## Dependencies on other paths

- **P3 (defect register)**: APD-ML-002..006 live in its register and need its owner ruling; juniper-data#432 is the register lane's to assign an `APD-DATA-*` id — still OPEN, 0 comments, unlabelled `[VERIFIED 2026-10-03: gh issue view]`. This lane has nothing left on #432, but PF-2 axis 2's 5,882 ceiling is caused by it: if #432 is fixed so the additive val+test sizing stops overflowing `MAX_POINTS`, the axis-2 ceiling note (re-spec §1) must be revisited.
- **P4 (release & distribution)**: the D1 flip (cascor#683) is on cascor `main` only — the latest cascor release is still **v0.11.0 (2026-09-09)** `[VERIFIED 2026-10-03: gh release list]`, so no published wheel/image carries the BLAS-2 default yet. When the next cascor release ships, service containers that export no BLAS vars (juniper-deploy's compose sets none — `[NOT RE-PROBED — from HANDOFF_2026-09-23_…, validated by receipt]`) will run BLAS 2-wide. Worth a release-notes line.
- **Canopy (P2)**: PF-2 axis 1's field must not break canopy's live tiles (`metrics_panel.py:1652`, also `:1887` reads `metrics_data[-1]`) — an additive field on `training_step` is safe; a new row kind is not.
- **P10 / CI tooling**: none required. The structure-screen arc (ml#2000) is closed; see Dispositioned.
- No dependency on P5–P9.

---

## Context the remaining work needs

### A. Traps (carried substance; all still relevant)

1. **Experiment stack from a session worktree cannot find cascor**: `PROJECT_DIR` derives to `.claude/worktrees`; Prometheus targets resolve inside the worktree and fail silently (inverting results). Export `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`; pin code with `JUNIPER_EXP_CASCOR_SRC_DIR=<detached cascor worktree>/src`. Base CONFIG still comes from the primary — check they agree.
2. **`torch.get_num_threads()` re-pins the calling thread** (unset env: fresh thread 16→8; under `OMP_NUM_THREADS=2`, cascor's default since #683, 2→2 and invisible). The mapped libgomp is torch's **bundled** copy (`site-packages/torch/lib/libgomp.so.1`); `CDLL("libgomp.so.1")` before `import torch` makes torch bind the env's copy. Use `util/thread_width.py`; `tests/test_thread_width.py` fails CI otherwise. Carry a do-nothing control arm whenever instrument and measurement touch the same state.
3. **`pkill -f <pattern>` kills its own shell** (exit 144); `pgrep -c -f` counts your own shell; `kill $!` after `setsid nohup … &` kills the wrapper, not the child. Kill by literal PID or `TaskStop`. Two samplers on one TSV double every tick — check `cut -f1,3 <trace> | sort | uniq -d` is empty.
4. **`run_suite --dry-run` prints a suite dir but creates nothing**, and prints neither runtime env nor thread budget (D3 proof needs a real `--only <cell>` run + `manifest.json`). `run_suite --only` exit 1 is documented design (exit 0 = FULL expansion succeeded) — read the manifest. `include`-only suites emit a bare base-config cell `c000`.
5. **Budget-bound counts are not evidence**: under `spiral-smoke` hidden units, output epochs and `step_count` 8 all equal their budgets. `candidate_epochs` 2000 gives 94/100 emergent counts.
6. **The request ceiling is 5,882 per spiral at the suite's split**, not 10,000 (10,000 is total rows; juniper-data#432). The "422" in the re-spec §1 and `rescale_generator_params`'s docstring is false — it is a generic 400.
7. **Do not compare the 3.14 micro reference with 3.13 runs**; `Linux-CPython-3.13-64bit/0003` resolves but is not comparable. PF-4 is report-only on timing permanently (owner
   2.5): `--benchmark-compare=<N>`, never `--benchmark-compare-fail`. The micro procedure lives at the ABSOLUTE path
   `/home/pcalnon/Development/python/Juniper/juniper-cascor/docs/testing/REFERENCE.md` § Micro timing reference (a relative path silently hits juniper-ml's own
   `docs/REFERENCE.md`). pytest-benchmark's `--benchmark-json` dir must pre-exist.
8. **Seeds**: the service exposes no network `random_seed`; suites can vary only the DATASET seed. `seed_policy: fixed` repeats are bit-identical — they prove determinism, not seed variance.
9. **Do not quote `fit_seconds`/wall from the D1 debt run or scope probe** (loads 8–31). Do not cite load 54.49 (withdrawn, ml#2015); sourced loads are 12.08 / 19.50 / 32.26. Do not cite the width sweep's −33% (true first-pass benefit −49.2%); "16 is 5–7× worse" is the `thread` mechanism only (env route ≈1%; true span 4.97–7.42×).
10. **The `ci-probe/*` `workflow_dispatch` run is not a D6 firing** (the counter excludes it).
11. **Merge mechanics**: a required check pins `AGENTS.md` `**Last Updated**:` to today's UTC date whenever a PR touches it. MD013 applies to table rows. The owner's sweeper
    applies Copilot Autofix to CodeQL findings and one autofix broke a PR (deleted `from unittest import mock`) — write `unittest.mock.<name>` with `import unittest.mock`.
    `safe_merge.py` can read a STALE head right after a push; under `strict:true` an armed net on a BEHIND PR waits forever — wait until `headRefOid` shows the pushed SHA, then one
    `update-branch` with `expected_head_sha`. Use `python3 -u` for logs. Same-file test rename = symbol LOSS (waiver must be in cascor's single squashed commit, last paragraph);
    GitHub's squash splits trailer blocks, so judge a waiver by re-running the screen on main, not `git interpret-trailers`. Append CHANGELOG entries at the END of `[Unreleased]`;
    never resolve into a released heading. `git reset --soft` leaves edits STAGED, so `git diff <path>` comes back empty — save with `git diff HEAD`. A large `CHANGELOG.md` payload to
    `open_signed_pr.py` hit a GraphQL error and left a branch with no commit: retry with `util/push_signed_commit.py --expected-head <branch sha>`, then `gh api -X POST …/pulls`.
    To fix a waiver without re-cutting a cascor PR: disarm auto-merge first (its stored body is an arm-time snapshot), create a temp branch at main, commit once with the trailer as
    the last paragraph, force-move the PR ref, delete the temp branch — the PR keeps its number.
12. **Worktree-isolated sessions**: cross-worktree git is refused; check a sibling worktree by hashing its files against `git ls-tree -r <sha>` (exclude LFS pointers and symlinks). Never `git clean`. `open_signed_pr.py` sends whole files — diff the pushed branch against `origin/main` for unexpected deletions. `pre-commit run --files` skips untracked files.
13. **`wall_ordering_survey.py` reports `UNRESOLVED`** for every sibling-repo `base_config` from a session worktree — run it from the primary checkout.
14. **Host-advantaged tests**: a dev box has a cascor sibling and 16 cores; CI has neither. Pin `JUNIPER_EXP_CASCOR_SRC_DIR` at a test-built tree; derive expected thread values from the function, not literals.
15. **Cascor primary checkout**: before any pull, check no live process holds `/home/pcalnon/Development/python/Juniper/juniper-cascor/src` (`ps -eo pid,cmd | grep "[/]juniper-cascor/src"`, plus `readlink /proc/<pid>/cwd` for uvicorns on 82xx). Quote the SHA you ran against, never "main".
16. **The juniper-ml CI test list is hand-maintained**; a new suite must be wired into `.github/workflows/ci.yml`, `docs/REFERENCE.md`'s list and the AGENTS.md count (highest-conflict files).
    Some suites lint OTHER test files (`tests/test_env_repr_safety.py` forbids raw `os.environ`-derived mappings anywhere under `tests/`), so no diff-chosen subset is enough — run
    `util/ad-hoc/2026-09-22_run_ci_regression_list.bash`. Hidden `.claude/worktrees/` dirs defeat "search everywhere" sweeps (dotfile-skipping idioms miss them). A gate whose real
    input is clean today needs a synthetic positive case to prove it can fire (the thread-width mutation harness's first survivor).
17. **A reducer that compares whole records needs its volatile fields excluded**: `timestamp` made four bit-identical runs read "DIFFER". Bears on item 1's new reducer.

### B. Retained state — do not delete (all present `[VERIFIED 2026-10-03: ls]`)

- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b` — detached at `0d2d826`; the tree PF-1, axis 2, axis 3 and the seed probe ran on. **RETAIN** until nothing cites a re-run against it.
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--exp--e-c-cap64--20260828-1922--67d7ea35` + symlink `~/.local/state/juniper-experiments/shadow-ec-cap64/juniper-cascor` → it (load-bearing, fails silently if dangling).
- Under `~/.local/state/juniper-experiments/baselines/`: `pf1-2026-09-23-blas2/` (current PF-1 tag), `pf1-2026-09-04/` and `…-04b/` (superseded BY NAME — never delete; `make_baseline` has no `--force`), `cascor-micro/Linux-CPython-3.14-64bit/0001_0e016a7c…_20260924_074016.json` + `loadavg-20260924.tsv`, the 3.13 store.
- Under `~/.local/state/juniper-experiments/suites/`: `pf2-axis3-cascor-spiral-count-20260923T202816Z/`, `pf2-axis3-seed-probe-20260924T075038Z/`,
  `pf2-axis2-cascor-dataset-range-20260923T142812Z/`, `d1-epoch-debt-20260923/`, `d1-scope-large-first-pass-20260923T142003Z/`, `pf1-cascor-spiral-repeats-20260923T125905Z/` (+ the
  `…013257Z` load-16 run), `d6-epochs-spread-20260922/` and `…20260917/`, `d1-d2-width-sweep-20260917-corrected/`, `pf8-icv-checkpoint-20260911/`,
  `pf8-openmp-attribution-20260910/`, and the 09-09/09-10 PF-8 / epoch-calibration dirs.
- `util/remove_stale_worktrees.bash` has NO staleness predicate — never run it.

### C. The five `util/experiments/` defects (APD-ML-002..006) `[ALSO P3]` `[NOT RE-PROBED — from HANDOFF_2026-09-22_structure-screen-…, validated adversarially]`

The source (structure-screen handoff §1) recommends starting from item 2, `expand_cells` (APD-ML-003), once the owner rules. Also from that handoff's §7 `[ALSO P3]`:
`util/ad-hoc/register_status_crosscheck.py` is keyed only on `**FIXED` and printed `AGREE` while three register §2 counts were stale — it cannot catch count drift.

Line numbers were probed 2026-09-22; `run_suite.py` was rewritten again by ml#2047 (09-23) since, e.g. `_headline_metrics` is now at `:585` (was `:580`) `[VERIFIED 2026-10-03: grep]` — **re-grep every anchor before editing**. The register rows (§4.9) carry the corrected readings.

- **APD-ML-002 `_headline_metrics` can never match.** Reads six names off the top of `stats["cascor"]`/`stats["recurrence"]`; `build_stats` nests them under
  `final`/`eval_scalars`/`final_metrics` — intersection ∅ since its one commit `513e7df2`. **Trap**: only two of six exist at any depth (`cascor.final.val_accuracy`,
  `recurrence.final_metrics.r2`/`crossval.*.r2`); a one-level unwrap harvests 2/6 and looks like a fix. Companion `row.get("metrics") or {}` guards are NOT vacuous (26 of 418
  registry rows lack `metrics`); the fix is type-closed. Ship with the first tests for those columns.
- **APD-ML-003 `expand_cells` raises raw exceptions → exit 1** where the contract says 2. Repro shapes: `base_config: [123]`; `include: [{config: 7, overrides: {}}]` (paired form only); `include: [{overrides: abc}]`; `include: [{overrides: [1,2]}]`. Contract stated in `run_suite.py:28-29` AND `docs/REFERENCE.md` "Resume, `--only`, and exit codes" — repair both.
- **APD-ML-004 `_emit_stats` fails silently** (`run_experiment.py`): sets `manifest["stats_error"]`, exit code untouched (call sites inside `finally:`), no test pins failure, nothing in `.github/` reads it; loses exactly `stats.json` + `summary.md`.
- **APD-ML-005 crossval passthrough**: `stats_summary.py` copies `eval_aggregate`/`eval_std` verbatim and reads them bare, while `plots_recurrence.py` guards the same keys from the same payload — local inconsistency; cost is a silent `summary.md` loss.
- **APD-ML-006 `present` fallback** (`stats_summary.py:340`, unchanged `[VERIFIED 2026-10-03]`) is production-unreachable but test-pinned — **do not delete**; the item is the latent coupling (a disk re-render tool would make every guard validated in ml#2001 live at once).
- Standing decision from that handoff: **do not sweep the remaining falsy guards by count**; the bar is in-file evidence via `util/ad-hoc/2026-09-22_falsy_guard_next_batch.py`. Its
  two genuine candidates are still present: `run_experiment.py:397` and `stats_summary.py:274` `[VERIFIED 2026-10-03: sed]`. Take a floor from ONE tool, never by adding across two.
  `run_suite.py`'s `doc`-reading guards need nothing (gated at `load_suite`) — but ml#2002 added `or {}` sites (incl. a materialised-cell `yaml.safe_load(...) or {}`) that sweep
  never covered; re-take the sweep before quoting that ruling.

### D. Carried items — substance `[NOT RE-PROBED — from HANDOFF_2026-09-22_perf-lane-d2-…, receipt-validated]` unless tagged

- **Three ICV residuals** (`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md` §7): (1) the exact rebuild path in the worker payload
  that re-pins — localised to the `result_queue.get()` unpickling the first `CandidateTrainingResult`; a plain 64² `pickle.loads` does not reproduce; needs a larger/shared-memory
  arm or an `omp_set_num_threads` interposer; (2) why the re-pin is op-shape dependent (512² one-shot no, 1500² sustained yes); (3) the listener has never been measured with this
  instrument (`ptrace_scope`=1; standing rule not to modify cascor → needs a new mechanism).
- **PF-5/6/7** (`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` item 2.3): never executed; REPORT-ONLY forever (`make_baseline` refuses them). Carve-out: "recurrence exposes no work-done counter" is FALSE for the MLP readout (`_readout_mlp.py:77,150` maintains `n_epochs_`); `docs/REFERENCE.md` and the P2 plan still state the unqualified version.
- **P2 item 4.2's open half** (P2 plan): D5 removed its blocker; a parallel cascor suite may be committed under `suites/perf/`; whether PF-8 should get one is open.
- **P2 item 5.2** (P2 plan): experiment-scoped alerts, juniper-deploy, S-sized, the only Wave 5 row without DONE.
- **CLI-experimentation tail** (`notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md`): **title-repair acceptance gate** first —
  `util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check` exit 1, 91 artifacts, all visited by a repair pass `[VERIFIED 2026-10-03]`; 163 of 172 broken titles were
  produced BY a repair pass, so owner must choose the extraction rule before any repair. Also: `JR-ML-OBS-003` (`status: designed` `[VERIFIED 2026-10-03]`); R-1's second clause
  (cascor must not report `succeeded` with zero installable candidates); F-P4-7; E-C's 0.10/0.20 rows at cap 128; W-12/Q-7; F-P1-2; G-16's refusal half; and the owner's standing
  rider on the withdrawn 0.5% threshold ("come back and verify after this gate goes live") — decide and record honoured vs retired.
- **D6 tree-sensitivity question**: the D6 reference is tree-sensitive by construction (fires on any cascor change moving candidate numerics); only 2 of 4 budgets (100, 200 → 68) are emergent. The recount (item 3) is what informs this.
- **Optional: why `thread16` first diverges at candidate phase 20** (one candidate 1450→1442) — an untested hypothesis in
  `notes/JUNIPER_2026-09-23_JUNIPER-ECOSYSTEM_PERF-LANE-D1-EPOCH-COUNT-DEBT.md` `:91`/`:111` `[VERIFIED 2026-10-03: sed]`.
- **Loaded-host design** (`HANDOFF_2026-09-22_perf-lane-d2-…` §9): interleave/round-robin arms with a leading repeat key and enough repeats, record load beside every measurement (`util/ad-hoc/2026-09-08_loadavg_sampler.py`).

### E. Documents of record

`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` (rulings §1–§6), `notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`
(axes; §4.2/§4.3 axis-3 results), `notes/JUNIPER_2026-09-23_JUNIPER-ECOSYSTEM_PERF-LANE-D1-EPOCH-COUNT-DEBT.md`,
`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`, `notes/JUNIPER_2026-09-17_JUNIPER-ECOSYSTEM_PERF-LANE-EPOCHS-COMPLETED-SPREAD.md`,
`notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`, `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`,
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (§8 micro invocation), `util/experiments/suites/perf/README.md` and suite headers,
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9.

---

## Verification commands

```bash
git fetch origin
gh pr view 2078 --json state,mergeCommit        # MERGED 514b6c24
gh pr view 683 -R pcalnon/juniper-cascor --json state,mergeCommit   # MERGED f7a6d573
gh issue view 432 -R pcalnon/juniper-data --json state               # OPEN at 2026-10-03
python3 -m unittest -q tests.test_thread_width tests.test_ci_test_wiring_drift tests.test_experiment_suite_yamls tests.test_run_suite
/opt/miniforge3/envs/JuniperCascor1/bin/python util/thread_width.py --self-check   # all claims OK
python3 util/ad-hoc/2026-09-23_thread_width_mutation_check.py | tail -1         # all mutations caught
python3 -u util/ad-hoc/2026-09-23_d6_advisory_firing_count.py | tail -2           # slow (>8 min on 2026-10-03)
python3 util/experiments/compare_baseline.py --baseline pf1-2026-09-23-blas2 --suite ~/.local/state/juniper-experiments/suites/pf1-cascor-spiral-repeats-20260923T125905Z   # PASS
python3 util/ad-hoc/2026-09-23_pf2_axis3_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-cascor-spiral-count-20260923T202816Z | tail -4
python3 util/ad-hoc/2026-09-24_pf2_axis3_seed_probe_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-seed-probe-20260924T075038Z | tail -5
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.14-64bit/
python3 util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check; echo "exit=$?"   # UNPIPED; exit 1 / 91 today
grep -n '_headline_metrics' util/experiments/run_suite.py                      # re-anchor APD-ML-002

# Stray check (do NOT kill peers' rows; discriminate by etimes)
ps -eo pid,etimes,cmd --no-headers | grep -E "[r]un_suite|[l]oadavg_sampler|[s]afe_merge|[c]lamscan"

# PF-3, ONLY in a quiet window: `cat /proc/loadavg` first and AT launch
python3 util/ad-hoc/2026-09-08_loadavg_sampler.py --out ~/.local/state/juniper-experiments/suites/pf3-loadavg-<date>.tsv --interval 30 &
JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper \
JUNIPER_EXP_CASCOR_SRC_DIR=/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--perf-pf1-baseline-pin--20260922-2036--0d2d826b/src \
  python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml
```

Decide deliberately whether PF-3 should run on the retained `0d2d826` pin (comparable with PF-1/axis 2/axis 3, pre-flip) or a post-flip cascor main (`b2921712` at probe time); quote the SHA either way.

---

## Dispositioned / closed items

| item | source | disposition | evidence |
|---|---|---|---|
| ml#2068 (helper, axis 3, D6 count, micro docs) | 09-24 §6 | MERGED | `2b53255a`, 2026-09-24T09:34Z `[VERIFIED 2026-10-03]` |
| 09-24 handoff's own merge-wait PR | 09-24 §6 | MERGED as ml#2078 | `514b6c24`, 09:45:51Z `[VERIFIED 2026-10-03]` |
| ml#2047, ml#2048, ml#2031, ml#2013, ml#2015, ml#2002 | 09-23 §6, 09-22 §2 | MERGED | `a77e69b6`, `f8e04b11`, `9d6c2eba`, `25b78f55`, `d52daef6`, `f8ffaa48` `[VERIFIED 2026-10-03]` |
| cascor#682 (D6 advisory), cascor#683 (D1 flip) | 09-23 §6 | MERGED | `b118e62e`, `f7a6d573` `[VERIFIED 2026-10-03]` |
| Thread-width helper ("prose warnings do not bind") | 09-22 debt 2, 09-23 item 5 | DONE | `util/thread_width.py`, `tests/test_thread_width.py` on main `[VERIFIED 2026-10-03]` |
| D1/D2 epoch-count debt | 09-22 debt 1 | PAID, CLEAR | `…D1-EPOCH-COUNT-DEBT.md` on main |
| Micro timing cut (7 sessions) | 09-22 item 5, 09-23 item 4 | DONE, LOADED by ruling | `Linux-CPython-3.14-64bit/0001_0e016a7c…` exists `[VERIFIED 2026-10-03]` |
| PF-1 successor baseline | 09-22 item 1 | DONE `pf1-2026-09-23-blas2` | dir exists `[VERIFIED 2026-10-03]` |
| PF-3 re-shape + D3 one-cell | 09-22 item 2 | DONE (14 cells, D3 PASS) | `pf3-cascor-pool-scaling-20260923T130821Z` exists |
| D4 axis 2 owner call / build / run | 09-22 item 3, 09-23 item 2 | RULED, BUILT, RUN — no knee; in-process follow-up does not fire | re-spec §3, ml#2047/#2048 |
| PF-2 axis 3 build + 4/5 inversion | 09-24 residue | DONE — inversion was the seed | re-spec §4.2/§4.3 |
| Commit or retire 09-17 D6 work | 09-22 item 4 | COMMITTED (ml#2031) | merged `[VERIFIED 2026-10-03]` |
| Cascor thread-pin defect repair | 09-22 item 6 | RULED and SHIPPED (process default cap 2, opt-out `0`/`off`/`none`) | cascor#683 |
| Four `Not decided:` clauses (D1/D2/D4/D6) | 09-22 §1 table | RULED 2026-09-23 | rulings §5 |
| Hand juniper-data defect over | 09-23 item 7 | DONE — juniper-data#432 filed; P3's to id | issue OPEN `[VERIFIED 2026-10-03]` |
| Wall-ordering survey over new axes | 09-22 §8 | DISCHARGED (axis 2, axis 3, PF-3 OK; 0 INVERTED) | 09-24 item 6 |
| `reflective-mixing-pearl` convergence | 09-23 git state | Converged (hash-checked 09-24); removal pending → open item 7 | worktree still exists `[VERIFIED 2026-10-03]` |
| `idempotent-wibbling-dongarra` convergence | 09-24 git state | HEAD `514b6c24` = ml#2078 squash → reset onto main done; removal pending → item 7 | `git worktree list` `[VERIFIED 2026-10-03]` |
| `lively-marinating-truffle` unpushed handoff | 09-22 git state | MOOT — handoff merged via ml#2013; HEAD `d721fc78` contained in origin/main | `[VERIFIED 2026-10-03]` |
| `optimized-giggling-koala` lock / rescue | 09-22 item 4, 09-11 | MOOT for this lane — files committed (ml#2031); worktree not this lane's (HEAD `a2db829b` on no remote branch) | `[VERIFIED 2026-10-03]` |
| Cursor-fleet round-2 arc | structure-screen §1 | DISCHARGED (ml#2000, #2001, #2010) | merged `[VERIFIED 2026-10-03]` |
| Markdown structure screen blind to ml#1746 | structure-screen §1 | FIXED by ml#2000 (`_absorbed_openers`); ml#1944's narrowing KEPT — do not widen back | `57e84be8` merged |
| Structure-screen handoff uncommitted | structure-screen §7 | MERGED (ml#2016, `d0582a21`) | `[VERIFIED 2026-10-03]` |
| Filing the five items | structure-screen §7 | FILED as APD-ML-002..006 (ml#2026) → open item 4 | `370c51eb` |
| `epochs_completed` exact-match micro gate (09-07 §3.3) | 09-07, 09-11 | Superseded by D6: advisory gate shipped (cascor#682); blocking is open item 3 | rulings §5 |
| `--benchmark-compare=0003` recipe | 09-11 | RETIRED (interpreter-keyed store) | 3.14 reference cut |
| juniper-recurrence `juniper-data<0.12.0` pin (CLI tail cross-repo) | 09-07 §8 | MOOT `[CHANGED SINCE HANDOFF: now `juniper-data>=0.9.0,<0.17.0`]` | gh contents `juniper-recurrence/pyproject.toml:97` |
| `ml#1811` / `xor-staged` PENDING exemption | 09-07 §3.3 | Not re-probed; pre-dates every later perf handoff, none of which carried it | `[NOT RE-PROBED — from HANDOFF_2026-09-07_…]` |

### Non-perf residue from the structure-screen handoff (kept separate, not perf-lane work)

- **`MEMORY.md` over its 20 KB target** — owner call on which linked closed-arc entries may retire; now **25,125 bytes** `[VERIFIED 2026-10-03: wc -c]`. Compact by retiring entries, never stripping hazard hooks; both existing gates (lossless verifier, link-set check) do not read hook TEXT — fix before reusing. `[ALSO P10?]` — cross-cutting memory hygiene, owned by no single path; reported to the coordinator.
- **`util/env_floor_drift_check.py` reason string**: a malformed pyproject correctly exits 2 but says "no juniper-\* version floors declared" (`:384`, unchanged `[VERIFIED 2026-10-03]`). Small ci-tooling polish `[ALSO P10]`.

---

## Git state (probed 2026-10-03)

- **juniper-ml** origin/main `afb02801`. No commit touching `util/experiments/`, `util/thread_width.py` or any perf-lane note has landed since ml#2078 `[VERIFIED 2026-10-03: git
  log origin/main --since=2026-09-24]`. Lane worktrees still present: `.claude/worktrees/reflective-mixing-pearl` (`f8e04b11`), `.claude/worktrees/idempotent-wibbling-dongarra`
  (`514b6c24`), `.claude/worktrees/lively-marinating-truffle` (`d721fc78`), `.claude/worktrees/gentle-kindling-pascal` (`d594a9d3`, the structure-screen session) — all HEADs
  contained in origin/main; working-tree cleanliness NOT probed (cross-worktree git refused). `.claude/worktrees/optimized-giggling-koala` (`a2db829b`) is not this lane's. The
  lane's PR head branches (`perf/thread-width-helper-pf2-axis3-d6-count-2026-09-24`, `docs/handoff-2026-09-24-perf-lane-axis3-seed-probe`, `perf/d1-debt-paid-…`,
  `docs/handoff-2026-09-23-perf-lane-d1-clear`, `perf/d2-runtime-block-binds-…`) are deleted on origin `[VERIFIED 2026-10-03: git ls-remote --heads returns nothing]`; a local `git
  branch -r` still lists them only because fetch does not prune.
- **juniper-cascor** main `b2921712` (2026-10-02). Since 09-24: `cascade_correlation.py` and `monitor.py` untouched; `manager.py` 4 commits. Retained detached worktrees `…perf-pf1-baseline-pin…0d2d826b` and `…exp--e-c-cap64…67d7ea35` present. Latest release v0.11.0 (pre-flip).
- **juniper-data**: #432 OPEN.
- **Stray processes**: none of this lane's patterns (`run_suite`, `loadavg_sampler`, `safe_merge`, `d6_epochs_completed_spread`, `d1_epoch_count_sweep`) and no `clamscan` running at probe time `[VERIFIED 2026-10-03: ps]`. Nothing was killed.
