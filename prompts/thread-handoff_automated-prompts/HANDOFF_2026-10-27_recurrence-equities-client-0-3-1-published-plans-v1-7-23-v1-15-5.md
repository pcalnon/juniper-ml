# Thread Handoff — Recurrence × Equities: juniper-recurrence-client 0.3.1 published, plans v1.7.23 / v1.15.5

**Date**: 2026-10-27 UTC (this session ran from 2026-10-27 ~22:20Z; this host's clock is local time, UTC−5)
**Session**: `77e26938`, the Linux host, worktree `.claude/worktrees/inherited-coalescing-stallman`. Commits are signed only through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_recurrence-equities-followups-closed-client-0-3-1-at-pypi-gate.md` (landed by juniper-ml#2372). Start from this file. That file's remaining-work item 1 (revise both plans) is done, and its first owner item (the client's `pypi` gate) was approved by the owner. Its other owner items and follow-ups are carried below, re-checked.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Nothing the arc can do alone is open: what remains is the owner's items, which a session surfaces and does not act on, and follow-ups that are blocked or optional.

## Completed this session (each probed here)

- **juniper-recurrence-client 0.3.1 is published.** The owner approved the `pypi` gate of publish run 40417898021 (juniper-recurrence), and `Publish to PyPI` succeeded at 2026-10-27 10:20:22Z.
  - PyPI serves the wheel (10:20:18Z) and the sdist (10:20:20Z), each with the sha256 TestPyPI took on 2026-10-26 at 23:21Z, and the same `requires_dist`.
  - **New probe**: `util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py`. It installs the wheel from PyPI (`--no-cache-dir --ignore-installed`) and points it at a stub HTTP server on 127.0.0.1. With 0.3.1, `crossval` without `embargo` sends no `embargo` key, and `embargo=0` / `embargo=7` are sent as given. The 0.3.0 control fails check 1, because it sends `embargo: 0`, and a version mismatch exits 2.
- **The parent `Juniper/AGENTS.md` RELEASED paragraph** now names client 0.3.1 in place of "Unmoved … 0.3.0". It was re-probed against PyPI on 2026-10-27, and every other package it names is unchanged. Its `Last Updated` is now 2026-10-27. The file exists on this host only and is unversioned.
- **Both plans are revised** (the predecessor's item 1), in this handoff's PR:
  - recurrence v1.7.22 → **v1.7.23** (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`), by `util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py`: 8 edits. It adds a Status summary, a Progress bullet and a 1.7.23 row; **Next** is rewritten; and closures are appended to W1.2's and W1.12's status rows, to the turing deploy-smokes note and to the juniper-ml#2227 ruling note;
  - consolidated v1.15.4 → **v1.15.5** (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`), by `util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py`: 26 edits across §2, XC-P12, §4, §5, §6, §8, §9 and Appendices A and B. Every line is at or under 512 characters.
  - **Validated** by one independent read-only fact-checker against PyPI, TestPyPI, `gh` and the sources. It found 0 BLOCKER and 1 MAJOR: v1.15.5's status line said it recorded the follow-ups and the archive cap, but its body did not; an XC-P12 bullet now does. It also found 6 MINOR and about 12 NIT; every MINOR and the actionable NITs are applied. Left by design: append-only remnants, and one dated line number in §5. A focused second pass on the fix delta confirmed 7 of the 8 fixes and caught one new MINOR, which is applied: the fix had put cascor#731, the `test_accuracy` producer, inside the train / val half.
- **APD-ML-002's cascor half is recorded**, after each relayed point was checked against `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9 and the PR bodies:
  - juniper-ml#2369 (`8467225b`, 2026-10-27 01:26Z) and juniper-cascor#731 (`752a797f`, 00:11Z) went in ahead of P5-11 (juniper-ml#2064), under the owner's four rulings of 2026-10-26;
  - ruling (1), "A now, test later", answers what P6 OD-3 asked; §6 A1's P6 OD-2 stays open only for APD-ML-003..006;
  - `test_accuracy` still has no producer: cascor#731 is in no cascor release (11 commits past `v0.12.0`), and juniper-ml#2064 is an open issue;
  - for P12: from #2369, a NaN or infinite value **fails** every W5.4 acceptance band; before it, NaN passed every band.
- **Re-checks**: juniper-deploy#263 merged on 2026-10-27 at 09:34:58Z and touched `scripts/test_recurrence_snapshots.sh`. #264's pull loop, `--no-build` on both `up` calls and exit 2 survive on deploy `main`. canopy#777's drift job passed its first scheduled run (40468348513). The env preflight still refuses `JuniperCascor1`: `ENV PREFLIGHT REFUSED: 2 finding(s)` (service-core 0.5.0).
- **Merge approval**: the owner granted it in this session ("merge approval granted"). It covered this session's PRs only and does not carry forward.

## Remaining work, in order

1. **Post-merge re-check of this handoff's PR**: on `main`, both scripts' `--check` exit 0, and `git grep -n -e '^- \*\*Version\*\*'` on the two plans shows 1.7.23 and 1.15.5.
2. **The owner's items.** Surface them; do not act on them.
   - **R-DATA-2: juniper-data 0.17.2** (P3-03, P3-09 and W5.7; W5.7 changes a default, so whether a patch may carry it is the owner's call). That release turns canopy#777's drift job red, because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`. Re-capture both snapshots then (the job prints the commands).
   - **juniper-data `notify-consumers.yml`: add juniper-canopy to the matrix.** The diff is in canopy#777's body. Only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers canopy. After both merge, a `workflow_dispatch` with version `0.17.1` settles it.
   - **The `index.jsonl` correction row** (`~/.local/state/juniper-experiments/index.jsonl` line 482, correcting line 477) says `degraded`; the owner's option said `failed`. Ask; append another correction row only on the owner's word, and never rewrite either line.
   - **`test_accuracy`**: a juniper-cascor release carrying cascor#731 is the owner's call, and juniper-ml#2064's labelled block must also land.
   - **juniper-config-tools 0.2.0**: its `[Unreleased]` must be backfilled first.
   - **W0.1's service-core half.** Never restart the cascor on `:8202`, and never modify `JuniperCascor1`.
   - **The consolidated plan's §6 A1 and A9 remainders.** A1: P6 OD-2 for APD-ML-003..006, canopy#685 call (a), the data-client source fix, a cascor F-S10 fix, and host recurrence legs. A9: DC-0.6's two numbers.
3. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316): BLOCKED** until W0.1. Recipe: `experiment_stack.bash --up --recurrence --config <abs irregular-sine-rff.yaml>`, then `run_experiment.py`, then `--down <RUN_ID>`. Done means `manifest.json` shows `save_model.source == "snapshot"`.
   2. canopy#738 (canopy 0.9.x work; the arc only annotates it) and #751 (waits on Lane B).
   3. From canopy#776's "Left out": the restart modal still shows Noise for `mnist`, which does not declare it. Capturing `mnist`'s declaration would close that. Also, its training fields stay cascor-only under recurrence.
   4. Optional, not run: an E-H suite run with `--shared-equities-cache <abs dir>`.
   5. `MEMORY.md` is 20,641 bytes, over the owner's 20 KB target (`feedback_memory_index_target_is_20kb.md`). Retire entries; never strip hooks.
   6. Before removing the two kept canopy agent worktrees (`worktrees/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f`, `worktrees/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f`), archive what their `tmp/` holds that is still needed. `git worktree remove` deletes `tmp/`.

## Rules that held this session

- **Grep the whole plan for every item you change, not only the anchors a handoff names.** The predecessor named Next, §5, XC-P12 and two status rows. The items also sat in §2 (three rows), §4 (three places), §6 (A1 and P6's OD-3), §8, §9 and both appendices, and each would have contradicted the edit.
- **A consolidated-plan line has 512 characters, and the script refuses past that.** Dry-run on a copy (`--root <dir>`) first; trim by naming a section rather than restating it.
- **An edit that appends after its anchor contains the anchor.** The v1.7.22-pattern test `new in text and old not in text` never sees such an edit as applied, so every run appends again. Use `new in text and text.count(old) <= text.count(new)`, as the consolidated scripts do, and prove idempotence by applying twice to a pristine copy.
- **A status line that says what a revision "records" must match the body.** The fact-checker's one MAJOR was exactly that.
- **Verify a relay against its primary source before a plan records it**: the PR body, the register row and `gh api …/compare/<tag>...<sha>` for "unreleased".
- **The worktree guard** refuses loops around `gh`, a `$var` where an option may stand, `${PIPESTATUS}`, `;` chains with a heredoc, and Write into the primary's `tmp/` (the scratchpad). Put helpers in the worktree's `tmp/` and run them plainly.
- **Carried, still true**: fetch and re-check `origin/main` against your paths immediately before every whole-file upload; the archive guard's rule 4 (`notes/releases/` alone in a PR); `push_signed_commit.py --expected-head` needs the FULL sha; the `pypi` gate and merges are the owner's, and merge approval is per session; a post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main            # this handoff's PR at or near the top
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.23 and 1.15.5
python3 util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py --check        # 0 edit(s) owed, exit 0
python3 util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py --check; echo $?    # 0
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-recurrence-client/json'))['info']['version'])"   # 0.3.1
gh issue view 2064 --repo pcalnon/juniper-ml --json state --jq .state   # OPEN (an issue, not a PR)
gh run list --repo pcalnon/juniper-canopy --workflow juniper-data-schema-drift.yml --limit 3    # success until juniper-data's next release
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python   # still REFUSED (2 findings) until W0.1
```

## Git state

- **This worktree** (`inherited-coalescing-stallman`) is on `worktree-inherited-coalescing-stallman`, fast-forwarded to `main` `ff6cc37d`. Its uncommitted copies of the five files are what this handoff's PR carries, together with this handoff. The PR was uploaded through `util/open_signed_pr.py`, so the local branch never moved.
- **Gitignored `tmp/s2/`** holds this session's scratch: the two probe venvs (`rc031`, `rc030`) and the downloaded wheels, the replay copies of both plans, the PR body, the canopy PR bodies and the env preflight log. Nothing there is the only copy of a record: the probe is in `util/ad-hoc/`, and its results are in the plans and the PR body.

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23) and `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.5);
  - `util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py`, `util/ad-hoc/2026-10-27_consolidated_plan_v1_15_5_client_0_3_1_published.py` and `util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py` (new);
  - this file.
- **Outside any repo**: the parent `Juniper/AGENTS.md` (the RELEASED paragraph, its re-probe date and `Last Updated`); in auto-memory, `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description) and its `MEMORY.md` line.
- **Referenced, not changed**:
  - the superseded handoff (above);
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` §4.9 (the APD-ML-002 ruling note);
  - `notes/releases/RELEASE_NOTES_juniper-recurrence-client_v0.3.1.md` (the fix the probe checks);
  - `reports/2026-10-04_consolidated-development-plan/extraction-P6-perf.md` (P6 OD-2 and OD-3);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
