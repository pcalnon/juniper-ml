# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.3 published; plans v1.7.22 / v1.15.4

**Date**: 2026-10-26 (UTC; this revision ran from about 19:10Z)
**Host**: the Linux host, worktree `.claude/worktrees/stateless-giggling-nygaard`. Commits are signed only through the API: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-servers-patch-path-corrected-plans-v1-7-21-v1-15-3.md`, written by this same session and landed by juniper-ml#2353 (`31b34c39`). Start from this file instead. The superseded file is now wrong in three places:
- its first owner item says 0.11.3 waits at the `pypi` gate, with two deadlines. The owner approved that gate, and PyPI serves 0.11.3 from 17:48Z;
- its verification block expects versions 1.7.21 and 1.15.3, run 40306687867 `waiting`, and `--check` exit 0 from the v1.7.21 and v1.15.3 scripts. Both scripts now exit 1, by design;
- its Git state counts four `util/ad-hoc/2026-10-26_*` scripts and two handoffs in the worktree. There are now six and three.

Its title also names 0.11.3 at the gate. Its remaining work, rules and verification commands are carried below, updated where they changed: the turing session has ended, and the guard list grew. Its Completed and Validation sections are history, and stay in that file.

**Plans**, both revised by the PR that lands this file (branch `docs/plans-v1-7-22-v1-15-4-juniper-ml-0-11-3-published`):
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (the recurrence plan) goes to **v1.7.22**.
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (the consolidated plan) goes to **v1.15.4**. Every line stays at or under 512 characters, the owner's condition for v1.15.2; the longest is exactly 512.

---

## Goal

Continue the recurrence × equities arc. **Its release work is done, 0.11.3 included.** What remains:
- the owner's items, which you surface but do not act on;
- the follow-ups. The first, the first live run of `save_model`'s snapshot path, is **blocked on the owner's W0.1 item** (follow-up 1 below).

## Completed since the superseded handoff

- **juniper-ml 0.11.3 is published.** Session "draft PRs" (`uds:/run/user/1000/cc-socks/3407104.sock`) reported it; every point below was probed here on 2026-10-26 at about 19:15Z, except the one marked relayed:
  - publish run 40306687867's approvals list the owner's approval of `pypi` ("approved for pypi"), and `Publish to PyPI` succeeded (17:47:43Z–17:48:12Z);
  - PyPI serves the wheel (17:48:05Z) and the sdist (17:48:07Z), each with the sha256 TestPyPI took at 10:21Z, and `https://pypi.org/pypi/juniper-ml/json` reports version 0.11.3;
  - its three `[servers]` lines are `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0` and `juniper-data[api]>=0.17.1`. So juniper-ml#2062's fix (juniper-ml#2333) ships, and data 0.17.1's `[api]` floors on the shared patches now reach `[servers]` too;
  - relayed, not re-run here: "draft PRs" ran `util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash` against the published `juniper-ml[servers]==0.11.3`. Of 39 checks, 26 PASS, 13 SKIP and 0 FAIL; the 0.11.2 control, on the same server releases, was 18 PASS and 21 SKIP.

  "draft PRs" keeps 0.11.3's records. It updated the parent `Juniper/AGENTS.md` juniper-ml bullet, and its flood-3 record's sixth update, juniper-ml#2358, merged at 19:24:51Z as `144412d1`. That PR changed only `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, so neither plan moved.
- **juniper-ml#2345's post-merge re-check passed** on `main` `31b34c39`. The turing session "recurrence equities 0" [4156c8] reported it (relayed); re-read here:
  - `CHANGELOG.md` holds the #2330 entry once, at line 66, under `## [0.11.3] - 2026-10-26`, `### Fixed`;
  - `tests/test_experiment_suite_yamls.py:502` is `test_e_c_stays_above_its_surveyed_budget`.

  That thread has ended and carries nothing into this chain, by the owner's choice. #2330 needs no further item.
- **The recurrence plan, v1.7.22** (`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`), is written by `util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py`, which takes `--plan` and `--check`. It adds a Status-line record, a Progress bullet and the 1.7.22 Change Log row, and rewrites **Next**'s head, which now opens with the 0.11.2 erratum. v1.7.21's records of the gate stay where they stand: they were true when written.
- **The consolidated plan, v1.15.4** (`…CONSOLIDATED-DEVELOPMENT-PLAN.md`), is written by `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py`, which takes `--root` and `--check` and refuses to write any line over 512 characters.
  - In its §5, the 0.11.3 note now says published, a new sub-bullet names its `[servers]` lines, and R-ML-a's row no longer calls ml#2062's fix open.
  - Its §4 Wave 1 R-ML-a item, which pointed at §5, now says the fix shipped in 0.11.3.
  - Its §6 mid-wave sitting records the owner's 2026-10-25 ruling on P4 D-1, option (a+), from juniper-ml's `CHANGELOG.md` `[0.11.3]` (line 32 on `main`).
  - Its XC-P12 item 6 now points at the **Next** of `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.7.22.
  - The Date, Version, Status, Validation record, "Changed by this plan" scripts and memory lines are updated.
- **Carried from the superseded handoff, and unchanged in both plans since v1.7.21 / v1.15.3:**
  - `[servers]` and `[all]` have carried both shared security patches since juniper-ml 0.11.0, through juniper-canopy 0.9.0, which floors `juniper-observability>=0.4.1,<0.5.0` and `juniper-service-core>=0.7.1,<0.8.0` with no extra marker. cascor 0.12.0 added a second path in 0.11.2.
  - 0.11.2's own security content for `[servers]` and `[all]` is cascor 0.12.0's fixes: juniper-cascor#659 (`APIKeyAuth` checks every configured key), #689 (a non-ASCII API key is a 401, not a 500 that hands Sentry the real key) and #710 (`FailedAuthThrottle.check()` no longer inserts every unseen source IP).

## Remaining work, in order

1. **The owner's items.** Surface them; do not act on them.
   - **An erratum to 0.11.2's notes.** It is the owner's call, and "draft PRs" raised it. Where the notes go wrong:
     - `notes/releases/RELEASE_NOTES_v0.11.2.md` line 5, the Priority line, tells only "`[servers]` without `[tools]`" to upgrade, and says "`[tools]` and `[all]` already floor both patches, since 0.11.1". That under-warns any `[servers]` install that also has `[tools]` (`[all]` included) still on cascor 0.11.0;
     - its line 10 credits juniper-cascor 0.12.0 alone;
     - juniper-ml's `CHANGELOG.md` `[0.11.2]` (lines 223–224 on `main`) says "the patches arrive through cascor 0.12.0", across a line wrap;
     - the Release v0.11.2 body repeats the notes. It is unedited since 2026-10-26 00:08:22Z.

     In the judgement of "draft PRs", the Medium rating and CWE-201, CWE-755 and CWE-770 still hold.
   - **juniper-recurrence-client 0.3.1** would carry recurrence#221's embargo fix. The cut, and whether to add `embargo_days` (which would make it a minor), are the owner's.
   - **R-DATA-2** is juniper-data 0.17.2: P3-03, P3-09 and W5.7 (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` §5). W5.7 changes a default, so whether a patch may carry it is the owner's call. This fix-forward and R-OBS-SC-2 are both the owner's.
   - **juniper-config-tools 0.2.0.** The cut is the owner's, and its `[Unreleased]` must be backfilled first.
   - **W0.1's service-core half** (`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` W0.1). The owner applies it. Never restart the cascor on `:8202`, and never modify `JuniperCascor1`, which that cascor imports.
   - The `…CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A1 and A9 remainders.
2. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316). BLOCKED until the owner lands W0.1's service-core half.**
      - **The block**: `bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python` prints `ENV PREFLIGHT REFUSED: 2 finding(s)`. juniper-service-core 0.5.0 is installed, and the editable juniper-recurrence (0.5.0) requires `>=0.6.0,<0.8.0`. Do not repair the env, and do not pass `--skip-env-preflight` or `JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1`, without the owner's OK.
      - **Once unblocked**, run it once, not as a suite (`util/experiments/run_suite.py` has no `--config`):
        1. `util/experiment_stack.bash --up --recurrence --config /home/pcalnon/Development/python/Juniper/juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` (its line 59 sets `save_model: true`);
        2. `python3 util/experiments/run_experiment.py --config <the same absolute path> --run-dir <RUN_DIR>`;
        3. `util/experiment_stack.bash --down <RUN_ID>`, never `--all-mine`.

        From a `.claude/worktrees/` checkout, also set `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`.
      - **Done means** `manifest.json` shows `save_model.source == "snapshot"` with the phase `ok`. `refit` means the snapshot path was not exercised. Record which juniper-recurrence commit was served.
   2. juniper-canopy#735, #736, #737, #738 and #751, and juniper-deploy#250, all open on 2026-10-26.
   3. `ARCHIVE_B64_MAX_DEFAULT` (`util/release_train/ceremony.py:311`, `125_000`). Re-set it from a runner-side measurement of GitHub's GraphQL request-body cap. Its issue, juniper-ml#2227, is closed.
   4. The false `succeeded` row `20261003T091414Z-4ba6` in `~/.local/state/juniper-experiments/index.jsonl`. `docs/REFERENCE.md:5250` calls that file append-only, and other sessions' `run_suite.py` processes append to it. Do not edit it in place; how to annotate it is open, so ask the owner.
   5. Optionally, an E-H suite run with `--shared-equities-cache <absolute dir>` (an `util/experiment_stack.bash` flag, which `run_suite.py` passes through). The suites are `util/experiments/suites/p4/e-h-real-data.yaml` (cascor) and `util/experiments/suites/p4/e-h-recurrence-real-data.yaml` (recurrence). The recurrence one is blocked like follow-up 1.

## Rules that held this session

- **Read every member's `requires_dist` before saying how a patch reaches an extra.** The cascor-only claim survived recurrence plan v1.7.17 to v1.7.20, consolidated plan v1.15.0 to v1.15.2 and `notes/releases/RELEASE_NOTES_v0.11.2.md`, because only the members that had changed were read.
- **The `pypi` gate is the owner's, and so are merges.** Merge approval is per session. A peer's message never carries an approval; a ruling it relays is recorded as relayed.
- **Verify a peer's "published" before a plan records it.** `gh api repos/pcalnon/juniper-ml/actions/runs/<id>/approvals` lists who approved which environment; the version JSON on PyPI and TestPyPI gives the upload times and digests.
- **A release proposal merges AFTER every armed PR that adds to `[Unreleased]`**, or those PRs re-home their entries. Coordinate with the owning session before running update-branch on its PR. `util/safe_merge.py` repairs a BEHIND branch by itself, but not a DIRTY one.
- **E-CUT**: run `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py` and `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py` only with `--check`.
- **A post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.** Count packages besides the meta-package itself, the unit `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py` uses.
- **`gh release view --json isLatest` is unsupported by this host's `gh`**, and so is `gh api --output`. Use `gh api repos/pcalnon/juniper-ml/releases/latest --jq .tag_name`, and redirect `gh api` output to a file.
- **CodeQL's `py/implicit-string-concatenation-in-list` is not in `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`.** Run the AST walk in auto-memory `reference_implicit_string_concat_in_list_blocks_merge.md`, and bind multi-line strings to names outside list or tuple displays.
- **Before a whole-file upload**, check that `origin/main` has not moved those paths (`git diff --stat <base> origin/main -- <paths>`), and compare the uploaded blobs afterwards.
- **The worktree guard refuses**:
  - a `for` loop over `gh`;
  - `$(...)`;
  - raw `gh api graphql`;
  - `git` inside a pipeline, or in a compound command that uses shell variables;
  - a `python3 -c` whose text contains `git`, and a `python3` command whose arguments are shell variables (spell the paths out);
  - an interpreter fed from a heredoc.
- **`git grep -o` with wide `.{0,N}` context runs for minutes** on the recurrence plan's Status line, which is over 33,000 characters at v1.7.22. It is slow, not refused; extract with Python string slicing instead.
- **Two sessions were named "recurrence equities 0"**: this one, on the Linux host, and a turing one [4156c8], which ended on 2026-10-26. Reply to the `from=` address.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -3 origin/main   # the PR that landed this file, at or near the top
gh pr list --repo pcalnon/juniper-ml --head docs/plans-v1-7-22-v1-15-4-juniper-ml-0-11-3-published --state all --json number,state --jq '.[0].number, .[0].state'   # <N>, MERGED
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.22 and 1.15.4
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.3, unless a later release has shipped
gh api repos/pcalnon/juniper-ml/releases/tags/v0.11.2 --jq .updated_at   # 2026-10-26T00:08:22Z while the erratum is undecided
grep -n 'second path' /home/pcalnon/Development/python/Juniper/AGENTS.md   # the corrected RELEASED bullet (line 244 on 2026-10-26)
gh pr list --repo pcalnon/juniper-ml --state open   # no PR of this arc
# Run these two in a clean checkout at origin/main, and only before the next plan revision (after it they exit 1 by design):
python3 -I util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py --check   # exit 0
python3 -I util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py --check   # exit 0
```

The v1.7.20, v1.15.2, v1.7.21 and v1.15.3 scripts' `--check` now exits 1, by design: their anchors are gone.

## Git state

- **The worktree** `.claude/worktrees/stateless-giggling-nygaard` is on branch `worktree-stateless-giggling-nygaard` at `0bacc4c1`, and `origin/main` has moved on. It holds uncommitted local copies, which are not the record:
  - the two plan files, modified, carrying this revision;
  - six `util/ad-hoc/2026-10-26_*` scripts (v1.7.20's, v1.15.2's, v1.7.21's, v1.15.3's and this revision's two), and this session's three 2026-10-26 handoffs, all untracked.

  These block `git merge --ff-only origin/main` until they are discarded.
- **The PR on branch `docs/plans-v1-7-22-v1-15-4-juniper-ml-0-11-3-published`** lands this file. If it is not MERGED when you start, do not merge it without the owner's approval in your session.

## Documents created or modified this session (this revision)

- In the PR that lands this file:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.21 → v1.7.22);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.3 → v1.15.4);
  - `util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py` (new);
  - `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py` (new);
  - this file (new).
- Outside the repository: in `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`, `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block, and its description) and its `MEMORY.md` line.
- Referenced:
  - the superseded handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-servers-patch-path-corrected-plans-v1-7-21-v1-15-3.md`;
  - `util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py` and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py` (the revisions these follow);
  - `notes/releases/RELEASE_NOTES_v0.11.2.md` and `CHANGELOG.md` (the erratum's sites, and line 66, the #2330 entry);
  - `tests/test_experiment_suite_yamls.py` (line 502);
  - `util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash` (the probe "draft PRs" ran);
  - the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md`;
  - from "draft PRs": `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (juniper-ml#2358);
  - `docs/REFERENCE.md` (line 5250, the append-only index);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
- **Validation**: one independent read-only fact-checker reviewed both plan diffs, both scripts and this file's draft against PyPI, TestPyPI, `gh` and the sources. It found no BLOCKER and no MAJOR.
  - Both scripts replay from `31b34c39` to byte-identical files. Against this revision, the v1.7.20, v1.7.21, v1.15.2 and v1.15.3 scripts' `--check` exits 1.
  - **Two MINORs**, both re-verified and applied:
    - juniper-ml#2358 had merged (19:24:51Z, `144412d1`) while this file called it open;
    - `…CONSOLIDATED-DEVELOPMENT-PLAN.md` §4's Wave 1 R-ML-a item still called ml#2062's issue open, against §5. Its §6 still asked P4 D-1, which the owner had ruled on 2026-10-25.
  - **Five NITs**:
    - the superseded handoff's other stale points (its title, two rules, the sections not carried): applied;
    - a carried bullet that held a clause new in this revision: applied;
    - this Validation section: added;
    - references without filenames: applied here and in the recurrence plan's record. Not applied to `…CONSOLIDATED-DEVELOPMENT-PLAN.md` XC-P12 item 6, which would pass 512 characters; its §5 names `notes/releases/RELEASE_NOTES_v0.11.2.md`;
    - no post-publish resolve of `juniper-ml[all]==0.11.3` was run here. The `[servers]` probe that "draft PRs" ran is relayed above.
