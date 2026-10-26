# Thread Handoff — Recurrence × Equities: `[servers]`'s security-patch path corrected; plans v1.7.21 / v1.15.3; juniper-ml 0.11.3 at the owner's `pypi` gate

**Date**: 2026-10-26 (UTC; this revision ran from about 11:00Z)
**Host**: the Linux host, worktree `.claude/worktrees/stateless-giggling-nygaard`. Commits are signed only through the API: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-published-plans-v1-7-20-v1-15-2.md`, written by this same session and landed by juniper-ml#2347. Start from this file instead. The superseded file is now wrong in four places:
- its line 14 says 0.11.2 carries "`[servers]`'s security floors". The data floor carries none for `[servers]`, and the cascor floor's security content is cascor 0.12.0's own fixes (below);
- its line 50 says the parent `Juniper/AGENTS.md` sentence "the patches arrive via cascor 0.12.0 alone" becomes history once 0.11.3 publishes. That sentence was never true, and session "draft PRs" has already corrected the bullet;
- 0.11.3 is no longer "being cut": it is cut and waits at the owner's gate;
- its verification block expects versions 1.7.20 and 1.15.2 and `--check` exit 0. Both scripts now exit 1, by design.

**Plans**, both revised by the PR that lands this file (branch `docs/plans-v1-7-21-v1-15-3-servers-patch-path-corrected`):
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (the recurrence plan) goes to **v1.7.21**.
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (the consolidated plan) goes to **v1.15.3**. Every line stays at or under 512 characters, the owner's condition for v1.15.2; the longest is exactly 512.

---

## Goal

Continue the recurrence × equities arc. **Its release work is done.** What remains:
- the owner's items, which you surface but do not act on;
- the follow-ups. The first, the first live run of `save_model`'s snapshot path, is **blocked on the owner's W0.1 item** (follow-up 1 below).

## Completed since the superseded handoff

- **The correction.** Session "draft PRs" (`uds:/run/user/1000/cc-socks/3407104.sock`) relayed it; it had started the claim in juniper-ml#2326. Everything below was re-probed against PyPI's `requires_dist` on 2026-10-26 before it was written:
  - juniper-canopy 0.9.0, the only canopy release at or above `[servers]`'s floor, floors `juniper-observability>=0.4.1,<0.5.0` and `juniper-service-core>=0.7.1,<0.8.0` with no extra marker.
  - juniper-ml 0.11.0, 0.11.1 and 0.11.2 each require `juniper-canopy>=0.9.0` under `[servers]`, and `[all]` includes `[servers]`.
  - So `[servers]` and `[all]` installs have carried both shared patches since 0.11.0.
    - cascor 0.12.0, whose floors are also unconditional, added a second path in 0.11.2.
    - cascor 0.11.0 floors only `>=0.4.0` and `>=0.5.0,<0.8.0`.
    - juniper-data 0.17.0 and 0.17.1 put their floors under `[api]` only.
  - **0.11.2's security content for `[servers]` and `[all]` is therefore cascor 0.12.0's own fixes**, all merged after cascor 0.11.0 (PyPI 2026-09-10) and all in juniper-cascor's `CHANGELOG.md` `[0.12.0]` (read at the tag `v0.12.0`):
    - juniper-cascor#659: `APIKeyAuth` checks every configured key;
    - #689: a non-ASCII API key is a 401, not a 500 that hands Sentry the real key;
    - #710: `FailedAuthThrottle.check()` no longer inserts every unseen source IP.
- **The recurrence plan, v1.7.21**, is written by `util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py`, which takes `--plan` and `--check`. It adds:
  - a Status-line record and a Progress bullet;
  - **Next**'s head, rewritten for 0.11.3 at the gate with both deadlines;
  - the 1.7.21 Change Log row.

  v1.7.17's sentence ("…so a `[servers]` install gets the patches through cascor 0.12.0, whose floors are unconditional.") stays where it is, in all three copies, each followed by a correction note.
- **The consolidated plan, v1.15.3**, is written by `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`, which takes `--root` and `--check` and refuses to write any line over 512 characters. In §5:
  - R-ML-TOOLS's audience drops `[all]`;
  - R-ML-SERVERS's content names cascor 0.12.0's own fixes, and its audience drops data 0.17.0;
  - the notes gain a correction note and a 0.11.3 pointer.

  It also updates the Date, Status, Validation record and "Changed by this plan" lines, and points XC-P12's item 6 at v1.7.21's **Next**. v1.15.0 introduced both wrong cells (juniper-ml#2325, found with `git log -S`).
- **Already corrected by "draft PRs", and re-read here:**
  - the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` bullet, lines 242–250;
  - auto-memory `project_recurrence_equities_p0_arc_2026-10-04.md`, lines 48–53, and `project_juniper_data_registry_needs_api_extra.md`;
  - its flood-3 record, `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`;
  - comments on juniper-ml#2326 and #2333.

  Its own handoff PR, juniper-ml#2352, merged at 11:34:06Z as `87892acc`. It touches neither plan.

## Remaining work, in order

1. **The owner's items.** Surface them; do not act on them.
   - **juniper-ml 0.11.3**, which carries #2333 (#2062's fix). Release `v0.11.3` was cut at 2026-10-26 10:20:47Z, with its tag at `a771a5b8`; its archive is juniper-ml#2350 (`8b2221d3`).
     - Publish run 40306687867 waits at `pypi` (environment 12341743943). It can be re-run until 2026-11-25 10:20Z, and GitHub cancels it on 2026-11-30 10:20Z.
     - The gate is the owner's, and the cut's records belong to "draft PRs".
     - Before any later revision of either plan, probe `https://pypi.org/pypi/juniper-ml/0.11.3/json` (404 until published). `gh api repos/pcalnon/juniper-ml/releases/latest --jq .tag_name` already prints `v0.11.3`, because the Release is cut, so only the PyPI probe shows publication.
   - **An erratum to 0.11.2's notes.** It is the owner's call, and "draft PRs" raised it. Where the notes go wrong:
     - `notes/releases/RELEASE_NOTES_v0.11.2.md` line 5, the Priority line, tells only "`[servers]` without `[tools]`" to upgrade, and says "`[tools]` and `[all]` already floor both patches, since 0.11.1". That under-warns any `[servers]` install that also has `[tools]` (`[all]` included) still on cascor 0.11.0;
     - its line 10 credits juniper-cascor 0.12.0 alone;
     - juniper-ml's `CHANGELOG.md` `[0.11.2]` (lines 223–224 on `main`) says "the patches arrive through cascor 0.12.0", across a line wrap;
     - the Release v0.11.2 body repeats the notes.

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
  - `git` inside a pipeline;
  - a `python3 -c` whose text contains `git`;
  - an interpreter fed from a heredoc.
- **`git grep -o` with wide `.{0,N}` context runs for minutes** on the recurrence plan's Status line, which is over 31,000 characters at v1.7.21. It is slow, not refused; extract with Python string slicing instead.
- **Two concurrent sessions were named "recurrence equities 0"**, so reply to the `from=` address.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -3 origin/main   # the PR that landed this file, at or near the top
gh pr list --repo pcalnon/juniper-ml --head docs/plans-v1-7-21-v1-15-3-servers-patch-path-corrected --state all --json number,state --jq '.[0].number, .[0].state'   # <N>, MERGED
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.21 and 1.15.3
gh run view 40306687867 --repo pcalnon/juniper-ml --json status --jq .status   # waiting, until the owner approves 0.11.3
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.2, or 0.11.3 once published
grep -n 'second path' /home/pcalnon/Development/python/Juniper/AGENTS.md   # the corrected RELEASED bullet (line 244 on 2026-10-26)
gh pr list --repo pcalnon/juniper-ml --state open   # no PR of this arc
# Run these two in a clean checkout at origin/main, and only before the next plan revision (after it they exit 1 by design):
python3 -I util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py --check   # exit 0
python3 -I util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py --check   # exit 0
```

The v1.7.20 and v1.15.2 scripts' `--check` now exits 1, by design: their anchors are gone.

## Git state

- **The worktree** `.claude/worktrees/stateless-giggling-nygaard` is on branch `worktree-stateless-giggling-nygaard` at `0bacc4c1`, and `origin/main` has moved on. It holds uncommitted local copies, which are not the record:
  - the two plan files, modified, carrying this revision;
  - four `util/ad-hoc/2026-10-26_*` scripts (v1.7.20's, v1.15.2's and this revision's two), and both 2026-10-26 handoffs of this session, all untracked.

  These block `git merge --ff-only origin/main` until they are discarded.
- **The PR on branch `docs/plans-v1-7-21-v1-15-3-servers-patch-path-corrected`** lands this file. If it is not MERGED when you start, do not merge it without the owner's approval in your session.

## Documents created or modified this session (this revision)

- In the PR that lands this file:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.20 → v1.7.21);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.2 → v1.15.3);
  - `util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py` (new);
  - `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py` (new);
  - this file (new).
- Outside the repository: in `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`, `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block, and its description) and its `MEMORY.md` line.
- Referenced:
  - the superseded handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-published-plans-v1-7-20-v1-15-2.md`;
  - `util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py` and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py` (the revisions these follow);
  - `notes/releases/RELEASE_NOTES_v0.11.2.md` and `CHANGELOG.md` (the erratum's sites);
  - the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md`;
  - from "draft PRs": its handoff `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_flood3-followups-servers-extras-fixed-juniper-ml-0-11-3-at-pypi-gate.md` and `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, both landed by juniper-ml#2352 (`87892acc`);
  - `docs/REFERENCE.md` (line 5250, the append-only index);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
- **Validation**: one independent read-only fact-checker reviewed both plan diffs, both scripts and this file's draft against PyPI, `gh` and the sources. The thesis held everywhere, and both scripts replay from `origin/main` to byte-identical files.
  - **Two MAJORs**, both applied:
    - the memory edits that the consolidated plan records had not yet been made;
    - the erratum scope named only `[all]`, but 0.11.2's Priority line under-warns every `[servers]` install that also has `[tools]`.
  - **Ten MINORs**, all applied:
    - the AGENTS.md line range;
    - #2352's landing;
    - four references without filenames;
    - the superseded handoff's four stale points, not two;
    - the `releases/latest` probe, which already names `v0.11.3`;
    - the Status line's length, and that trap's place in the guard list;
    - XC-P12 item 6, which still pointed at v1.7.20;
    - "say the same", which read as agreement;
    - the CHANGELOG quote's line wrap;
    - an unattributed judgement.
