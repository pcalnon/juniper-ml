# Thread Handoff — Recurrence × Equities: P5-11 closed, juniper-cascor 0.13.0 at its gate, consolidated plan v1.15.6

**Date**: 2026-10-28 UTC (this host's clock is local time, UTC−5)
**Session**: `1fc78df5`, the Linux host, worktree `.claude/worktrees/cozy-whistling-dragon`. Commits are signed only through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_recurrence-equities-client-0-3-1-published-plans-v1-7-23-v1-15-5.md` (landed by juniper-ml#2377). Start from this file. That file's item 1 (the post-merge re-check) passed. Its owner items and follow-ups are carried below, each re-checked on 2026-10-28.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Nothing the arc can do alone is open. What remains is the owner's items, which a session surfaces and does not act on, and follow-ups that are blocked or optional.

## Completed this session (each probed here)

- **The predecessor's post-merge re-check passed.** On `main` (`c77b7be5`), both of its scripts' `--check` exit 0, and the plans read 1.7.23 and 1.15.5.
- **`test_accuracy` moved, outside this arc** (the flood-3 session's lane; its handoff is `HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`):
  - juniper-ml#2381 (`c77b7be5`, merged 2026-10-28 03:23:15Z) closed juniper-ml#2064 (P5-11). A cascor run's `stats.json` `cascor.eval_scalars` is now its labelled final evaluation (schema `juniper-experiment-stats/2`). `run_suite.py` fills `test_accuracy` and the other `test_*` columns only from a final block on `test`. It left register row `APD-ML-002` to the owner.
  - juniper-cascor 0.13.0 carries juniper-cascor#731 (`752a797f` is 5 commits behind `v0.13.0`). Proposal cascor#733 merged as `61a67c53`; Release `v0.13.0` was published at 00:25:28Z; archive juniper-ml#2379. GHCR serves `0.13.0` and `0.13` (run 40608671351), TestPyPI returns 200, and PyPI returns 404.
  - Publish run **40608671287** waits at the `pypi` gate (created 00:25:29Z). **The working deadline is 2026-11-27 00:25Z**: GitHub's Actions limits page caps an environment-approval wait at 30 days ("Gate approval time"), and a run can be re-run only within 30 days. The 35-day run limit, **2026-12-02 00:25Z**, is the outer bound.
  - `src/api/secrets.py` is unchanged from `v0.12.0` to `v0.13.0` (16 commits, 39 files), so 0.13.0 carries no cascor F-S10 fix either.
- **Consolidated plan v1.15.5 → v1.15.6** (this handoff's PR), by `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`: 24 edits.
  - They cover the date and status lines, §2's P5 and P6 rows, XC-P12 item 2 (W1.14's "a cascor fix") and action 4, and §4: P5-11, P6, and the Images route's lock pins.
  - The rest: a §5 R-CASCOR note for 0.13.0, §6 A1 and OD-3, three §8 rows, §9 (P5-11 and the F-S10 row's lock pins), Appendix A (T1, T5), Appendix B's menu row, the validation record, and the changed-by lists.
  - Every line stays at or under 512 characters. The script was proved idempotent by applying it twice to a pristine copy.
  - The recurrence plan is unchanged at v1.7.23: its W5.4 rows do not list the metric set, and #2381 changes no recurrence path.
- **Validation**: one independent, read-only fact-checker checked the first draft against `gh`, PyPI, TestPyPI, GHCR and GitHub's docs. It found 0 BLOCKER, 0 MAJOR and no contradiction, plus 4 MINOR and some NITs.
  - All four MINORs are applied:
    - the gate's working deadline is day 30 (the limits page's "Gate approval time"), not day 35, which I re-fetched;
    - two lines had dropped "with a test split";
    - the memory edits the plan names had to exist before landing;
    - two stale "cascor locks pin data-client 0.5.0" lines: they pin 0.6.0 since the lock moves in 0.13.0, and 0.6.0 carries F-S10 too.
  - Three NITs are applied (§2's P6 row, §6 A1, and P6-08 dropped as a pending editor in §8's `run_suite.py` row). §2's P4 row has no room under 512 characters.
  - My own catch, before the check: the first draft said `test_accuracy` "waits on that gate alone", which overclaimed (see Rules).
- **The two kept canopy agent worktrees' `tmp/` is archived** (the predecessor's follow-up 6). 37 files (about 816 KB: lane logs, PR and commit bodies, the probes and their outputs, and the proposed juniper-data notify diff) went to `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/`.
  - `MANIFEST.tsv` there holds each file's sha256, verified identical to the original. `README.md` there lists what was left out (venvs, the PyPI wheel, pytest and torch caches) and the removal commands.
  - **The worktrees were NOT removed**: a worktree-isolated juniper-ml session cannot run git in juniper-canopy. canopy#776 and #777 are merged.
- **`MEMORY.md`**: the arc's three lines are trimmed, 21,121 → 20,885 bytes. Every trimmed detail was first found in its topic file. Then the publish-gate hook was corrected to day 30 (+17 B, 20,902 B). The link set is intact (163 = 163, `util/ad-hoc/2026-09-12_memory_index_linkset.py compare`). The rest of the excess over 20,000 bytes is in other arcs' active lines (canopy E2E 1,486 B, backup 788 B, perf 567 B, the process and worktree trap groups), which are theirs to compact.
- **`project_pypi_publish_workflow_dual_gate.md` is corrected**: a waiting gate may end at day 30 (the limits page's "Gate approval time"), so day 30 is the working deadline and day 35 the outer bound. Its index hook says so too.
- **Merge approval**: the owner granted it in this session ("merge approval granted"). It covered this session's PRs only and does not carry forward.

## Remaining work, in order

1. **Post-merge re-check of this handoff's PR**: on `main`, the v1.15.6 script's `--check` exits 0, and `git grep -n -e '^- \*\*Version\*\*'` on the consolidated plan shows 1.15.6.
2. **The owner's items.** Surface them; do not act on them.
   - **juniper-cascor 0.13.0's `pypi` gate** (run 40608671287; the flood-3 arc's release). The deadlines are above.
     - After it publishes, close register row `APD-ML-002`. That is the owner's five-touch procedure; #2381 left it to them.
     - A wheel probe can then confirm `compute_classification_accuracy` (the flood-3 handoff's item 5).
   - **R-DATA-2: juniper-data 0.17.2** (P3-03, P3-09 and W5.7; W5.7 changes a default, so whether a patch may carry it is the owner's call). PyPI still serves 0.17.1, and no v0.17.2 Release exists (2026-10-28). That release turns canopy#777's drift job red, because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`. Re-capture both snapshots then; the job prints the commands.
   - **juniper-data `notify-consumers.yml`: add juniper-canopy to the matrix.** The matrix on `main` is still `[juniper-recurrence]`. The diff is in canopy#777's body and in the archive (`jd-notify/proposed-juniper-data-notify.diff`). Only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers canopy. After both merge, a `workflow_dispatch` with version `0.17.1` settles it.
   - **The `index.jsonl` correction row** (`~/.local/state/juniper-experiments/index.jsonl` line 482, correcting line 477; still 482 lines) says `degraded`, where the owner's option said `failed`. Ask; append another correction row only on the owner's word, and never rewrite either line.
   - **juniper-config-tools 0.2.0**: `[Unreleased]` is still empty, with four commits since 0.1.0 (PyPI 0.1.0). It must be backfilled before a cut.
   - **W0.1's service-core half.** The preflight still refuses `JuniperCascor1` with 2 findings (service-core 0.5.0, re-run 2026-10-28). Never restart the cascor on `:8202`, and never modify `JuniperCascor1`.
   - **The consolidated plan's §6 A1 and A9 remainders.** A1: P6 OD-2 for APD-ML-003..006, canopy#685 call (a), the data-client source fix, a cascor F-S10 fix, and host recurrence legs. A9: DC-0.6's two numbers.
3. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316): BLOCKED** until W0.1. Recipe: `experiment_stack.bash --up --recurrence --config <abs irregular-sine-rff.yaml>`, then `run_experiment.py`, then `--down <RUN_ID>`. Done means `manifest.json` shows `save_model.source == "snapshot"`.
   2. **A local cascor run fills `test_accuracy` only from a cascor `src/` that carries #731.**
      - `util/experiment_stack.bash` launches uvicorn from `JUNIPER_EXP_CASCOR_SRC_DIR`, whose default is `<ecosystem root>/juniper-cascor/src`.
      - The cascor primary lacks #731: its `classification_metrics.py` has no `compute_classification_accuracy` (2026-10-28), and it is frozen while live stacks import it.
      - So pin `JUNIPER_EXP_CASCOR_SRC_DIR` to a checkout at or after `752a797f` (`v0.13.0` is one), or wait for the primary to move. The PyPI gate does not decide this.
   3. canopy#738 (canopy 0.9.x work; the arc only annotates it) and #751 (waits on Lane B).
   4. From canopy#776's "Left out": the restart modal still shows Noise for `mnist`, which does not declare it. Capturing `mnist`'s declaration would close that, but it is not one entry. canopy's `src/dataset_schema.py` treats `mnist`'s `flatten` as shape-determining (canopy#623) and marks `mnist` as needing juniper-data's optional dataset extra. First check whether the capture tool and canopy#777's drift job can read its schema without that extra. Its training fields also stay cascor-only under recurrence.
   5. Optional, not run: an E-H suite run with `--shared-equities-cache <abs dir>`.
   6. **Removing the two canopy worktrees** (`worktrees/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f`, `worktrees/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f`): the commands are in the archive's `README.md`. This needs a session in juniper-canopy, or the owner.
   7. `MEMORY.md` is still about 885 bytes over 20 KB, in other arcs' lines (above).

## Rules that held this session

- **A merge plus a gated wheel is not a running service.** Name what fills the column, and do not write that a value "waits on the gate alone". Here, a local run reads whatever `src/` the stack launches. The gate governs wheel users and the register row's close.
- **A waiting `pypi` gate's working deadline is day 30 from the run's `created_at`, not day 35.** GitHub's Actions limits page caps an environment-approval wait at 30 days. The 35-day run limit is the outer bound; state both when handing a gate over.
- **Grep the whole plan for every item you change.** P5-11 alone sat in §2, §4, §6, §8 (three rows), §9 and Appendix A. #2381 also touched `run_suite.py` and `run_experiment.py`, whose §8 rows needed it too.
- **A record of another arc's merge is still a record to verify.** Each fact here came from `gh pr view`, the Release, the run's jobs, the PyPI, TestPyPI and GHCR responses, and the compare, not from the flood-3 handoff.
- **Before trimming a `MEMORY.md` hook, find its detail in the topic file**, in any case. The "yield" hook sits there as "YIELDED", which a case-sensitive search missed. Gate on the link set, not a count.
- **Tooling on this host**: `grep` is ugrep, and a regex with a bounded `.{0,N}` context "exceeds complexity limits", so use a small Python helper in the worktree's `tmp/`. The worktree guard refuses heredocs inside `&&` chains, `gh` with nested-quote `--jq`, and `python3` reading `/dev/stdin` from a pipe. Write a file, then run it plainly.
- **Carried, still true**: fetch and re-check `origin/main` against your paths immediately before every whole-file upload; `push_signed_commit.py --expected-head` needs the FULL sha; the `pypi` gate and merges are the owner's, and merge approval is per session; a post-publish resolve passes `--no-cache-dir` and `--ignore-installed`; a consolidated-plan line has at most 512 characters.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main            # this handoff's PR at or near the top
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.23 and 1.15.6
python3 util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py --check; echo $?    # 0
gh run view 40608671287 --repo pcalnon/juniper-cascor --json status,jobs --jq '.status, (.jobs[] | "\(.name): \(.status)/\(.conclusion)")'   # waiting until the owner approves
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-cascor/json'))['info']['version'])"   # 0.12.0 until the gate
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-data/json'))['info']['version'])"     # 0.17.1 until R-DATA-2
gh run list --repo pcalnon/juniper-canopy --workflow juniper-data-schema-drift.yml --limit 3    # success until juniper-data's next release
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python   # still REFUSED (2 findings) until W0.1
wc -l ~/.local/state/juniper-experiments/index.jsonl                                            # 482 until the owner rules
```

## Git state

- **This worktree** (`cozy-whistling-dragon`) is on `worktree-cozy-whistling-dragon` at `main` `c77b7be5`. Its uncommitted copies of the three files below are what this handoff's PR carries. The PR is uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored `tmp/s3/`** holds this session's scratch: the replay copy of the plan, the v1.15.6 diff, the link-set snapshot, canopy#776's body and canopy's `dataset_schema.py`, and the helpers (`find_ctx.py`, `blob_scan.py`, `archive_manifest.py`). None of it is the only copy of a record.

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.6);
  - `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py` (new);
  - this file (new).
- **Outside any repo**:
  - `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/` (new: the 37 archived files, `MANIFEST.tsv` and `README.md`);
  - in auto-memory, `MEMORY.md` (the arc's three lines and the publish-gate hook), `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description) and `project_pypi_publish_workflow_dual_gate.md` (the day-30 correction).
- **Referenced, not changed**:
  - the superseded handoff (above) and the flood-3 handoff `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`;
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23, unchanged);
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (row `APD-ML-002`, unchanged);
  - `notes/releases/RELEASE_NOTES_juniper-cascor_v0.13.0.md` (the 0.13.0 notes);
  - `util/experiment_stack.bash` (`JUNIPER_EXP_CASCOR_SRC_DIR`);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
