# Thread Handoff — Recurrence × Equities: follow-ups closed, juniper-recurrence-client 0.3.1 at the `pypi` gate, archive cap 1 MB

**Date**: 2026-10-27 UTC (this session ran 2026-10-26 ~20:15Z to 2026-10-27 ~01:00Z)
**Session**: "recurrence equities 2", the Linux host, worktree `.claude/worktrees/iridescent-hatching-muffin`. Commits are signed only through the API: `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-3-published-plans-v1-7-22-v1-15-4.md` (landed by juniper-ml#2359). Start from this file. That file's remaining-work list is now wrong in these places:
- its follow-ups 2, 3 and 4 are done (below);
- its owner items "0.11.2 erratum" and "juniper-recurrence-client 0.3.1" are done, the second up to the owner's `pypi` gate.

Its rules and its follow-up 1 are carried below.

**The plans are NOT revised for any of this yet.** Both stay at recurrence plan v1.7.22 (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`) and consolidated plan v1.15.4 (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Revising them is remaining item 1.

---

## Goal

Continue the recurrence × equities arc:
1. Record this session's work in both plans.
2. Surface the owner's items.
3. Carry the follow-ups.

## Completed this session (each probed or merged here unless marked relayed)

- **juniper-deploy#250 is fixed by juniper-deploy#264** (merged 2026-10-26 22:03:29Z, `0d9c71f6`).
  - `scripts/test_recurrence_snapshots.sh` resolves and prints its two images, and pulls a missing one (three attempts, `RECURRENCE_SMOKE_PULL_RETRY_DELAY`). An image that is neither local nor pullable stops the run with exit 2. Both `up` calls pass `--no-build`.
  - New `tests/test_recurrence_snapshot_smoke_images.py` (4 tests, all failing against the old script).
  - Live on this host: 8/8 on the local-image path (recurrence 0.8.0, revision `6a98515e`), and 8/8 on the pull path (0.7.0, which was pulled and then removed).
  - The other session's deploy#263 still merges cleanly (`git merge-tree`).
- **#736's juniper-cascor half: juniper-cascor#729** (22:23:38Z, `5b7d10dc`). A comment-only fix in `TrainingLifecycleManager._translate_staged_config`: flat `equities` declares neither `n_samples` nor `noise` (checked at juniper-data `v0.17.1`). The translation is unchanged on purpose: changing it could move `dataset_id` hashes.
- **Runner-side GraphQL body cap measured** (handoff follow-up 3).
  - From a GitHub-hosted runner (run 40410086979), every body from 100,000 B to 16,777,216 B was accepted. From this host, every body up to 8,388,608 B.
  - The runner run came from throwaway draft juniper-ml#2361, opened against a throwaway base so only the base-branch guard ran. It was closed, and both branches were deleted.
- **Owner rulings, this session, 2026-10-26/27 (AskUserQuestion):**
  1. **Raise `ARCHIVE_B64_MAX_DEFAULT` to 1,000,000.** Done: juniper-ml#2364 (23:02:33Z, `ecc05079`), with the probe `util/ad-hoc/2026-10-26_graphql_body_cap_probe.py`, evidence in `reports/2026-10-26_graphql-body-cap-probe/`, tests, `docs/REFERENCE.md` and the operator runbook 1.2.4.
  2. **Annotate the false `succeeded` row by appending a correction row** (follow-up 4). Done: `~/.local/state/juniper-experiments/index.jsonl` line 482 corrects line 477 (run `20261003T091414Z-4ba6`). **It says `degraded`, not the `failed` my question named.** `degraded` is the outcome today's `run_suite.py` assigns (train and predict succeeded; crossval failed with a 422 on `X_full`). Tell the owner if they want `failed`.
  3. **The 0.11.2 erratum "everywhere".** It was ALREADY DONE by session "draft PRs", under the owner's own ruling there: juniper-ml#2362 (both archives), #2363 (CHANGELOG, `40815bb4`), and both Release bodies (v0.11.2 edited 22:25:54Z). This session found that at upload time, discarded its duplicate and told "draft PRs".
  4. **Cut juniper-recurrence-client 0.3.1, up to the gate.** Done:
     - proposal juniper-recurrence#227 (22:50:34Z, `717f2a80`). `detect.py` proposed 0.4.0, from the repo-wide `feat` confound; the manifest's `proposed_version` override gave 0.3.1;
     - the ceremony ran from a clean juniper-ml worktree at `ecc05079`;
     - Release `juniper-recurrence-client-v0.3.1` at 23:10:24Z, tag at `717f2a80`;
     - archive juniper-ml#2367 auto-merged (23:40:40Z, `edcbb024`);
     - **publish run 40417898021**: TestPyPI OK (wheel and sdist at 23:21Z); `Publish to PyPI` is **waiting** at env `pypi` (id 16691727515). It is re-runnable until **2026-11-25 23:10Z** and cancelled on **2026-11-30 23:10Z**.
  5. **canopy#776: accept the post-swap Confirm change.** Merged 2026-10-27 00:44:30Z as `c7846b4e`, after its re-run CI went green (21/21). #735 and #736 are closed.
  6. **canopy#777: merge as designed, then dispatch once.** Merged 2026-10-27 01:08:22Z as `33619d6d`, and #737 is closed. The first `workflow_dispatch` on `main` (run 40430795877) passed: "no drift: 7 generators in 2 fixture(s) match juniper-data 0.17.1". It already covers #776's flat-`equities` snapshot.
- **canopy#776** (Closes #735, #736; task-executor agent, finished in place after the agent hit the session limit):
  - It keeps the owner's 2026-09-22 restart-modal ruling (§5.6.1 point 4 of `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`): "Confirm re-stages exactly what the modal displays".
  - It fixes a pre-existing breach of that ruling: an untouched Confirm after the `enabled[0]` swap re-staged nothing.
  - The flat `equities` declaration was captured from the published 0.17.1 wheel into `src/tests/fixtures/juniper_data_tabular_generator_schemas.json`.
  - The CHANGELOG conflict with `main` was resolved by moving this PR's entries below an unchanged bullet, then a server-side update-branch.
- **canopy#777** (Closes #737): `util/check_juniper_data_generator_schemas.py` plus `.github/workflows/juniper-data-schema-drift.yml`, daily at 07:17Z plus `repository_dispatch` `juniper-data-published`. Its PR run passed (run 40417272707; 6 generators, no drift against 0.17.1). The `CICD_REFERENCE.md` header conflict was resolved the same way, with 0.29.0 restored afterwards.
- A turing session ("recurrence equities 0" [efd1dd]) relayed that 0.11.3 is published. The reply said it was already recorded in ml#2359.

## Remaining work, in order

1. **Revise both plans** (recurrence v1.7.22 → v1.7.23; consolidated v1.15.4 → v1.15.5, every line ≤512 chars). Record every item above. Follow the script pattern: `util/ad-hoc/2026-10-27_plan_v1_7_23_<slug>.py` with `--plan` / `--check`, and the consolidated one with `--root` / `--check`, refusing any line over 512.
   - **Where these land in each plan**:
     - **Next** (recurrence): drop the 0.11.2 erratum and the client-cut items; add the client's gate and the owner's items below.
     - §5 R-ML rows and XC-P12 (consolidated).
     - The W1.2 / W1.12 status rows (canopy#735–#737 and deploy#250 closed).
   - **Validate** with one independent read-only fact-checker before landing (see the auto-memory `feedback_validate_handoff_prompts_independently.md`).
2. **The owner's items.** Surface them; do not act on them.
   - **Approve juniper-recurrence-client 0.3.1's `pypi` gate** (run 40417898021; the deadlines are above). Then update the parent `Juniper/AGENTS.md` RELEASED paragraph, which names the client as "Unmoved … 0.3.0". That file is on this host only and unversioned.
   - **R-DATA-2: juniper-data 0.17.2** (P3-03, P3-09 and W5.7; W5.7 changes a default). **That release will turn canopy#777's drift job red**: data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`. Re-capture both snapshots then (the job prints the commands).
   - **juniper-data `notify-consumers.yml`: add juniper-canopy to the matrix.** The diff is in canopy#777's body. Only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers canopy. After both merge, a `workflow_dispatch` with version `0.17.1` settles it.
   - **juniper-config-tools 0.2.0**: its `[Unreleased]` must be backfilled first.
   - **W0.1's service-core half.** Never restart the cascor on `:8202`, and never modify `JuniperCascor1`.
   - **The `…CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A1 and A9 remainders.**
3. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316): BLOCKED** until W0.1. `bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python` still prints `ENV PREFLIGHT REFUSED: 2 finding(s)` (re-run 2026-10-26). The recipe is unchanged from the superseded handoff: `experiment_stack.bash --up --recurrence --config <abs irregular-sine-rff.yaml>`, then `run_experiment.py`, then `--down <RUN_ID>`. Done means `manifest.json` shows `save_model.source == "snapshot"`.
   2. canopy#738 (canopy 0.9.x work; the arc only annotates it) and #751 (waits on Lane B).
   3. **From canopy#776's "left out"**: the restart modal still shows Noise for `mnist`, which does not declare it. Capturing `mnist`'s declaration would close that. The modal's training fields are still cascor-only under recurrence.
   4. Optional, not run: an E-H suite run with `--shared-equities-cache <abs dir>`. The canopy replay session was driving live E2E servers here all evening.
   5. `MEMORY.md` is at about 19.9 KB, against the owner's 20 KB target (`feedback_memory_index_target_is_20kb.md`). Retire entries; never strip hooks.

## Rules that held this session

- **Fetch and re-check `origin/main` against your paths immediately before every whole-file upload.**
  - **Twice this session, `main` moved under an open edit**: #2362 changed the 0.11.2 notes, and #2363 changed the CHANGELOG.
  - **The fix**: discard and re-apply on top. `git merge --ff-only origin/main` first.
- **The archive guard is a required check.** Its rule 4 fails any PR that touches `notes/releases/` and also changes another file, even with `Allow-Archive-Edit:`. Split archive edits from everything else.
- **A DIRTY PR under signed commits**: upload a file where `main`'s new text sits verbatim at `main`'s position and yours sits below a line neither side changed. Prove it with `git merge-file` (0 conflicts), then run `gh api -X PUT repos/O/R/pulls/N/update-branch -f expected_head_sha=<head>`. See `reference_changelog_conflict_signed_update_branch.md`.
- **`push_signed_commit.py --expected-head` needs the FULL sha.** Read it with `rev-parse` or the PR's `headRefOid`; never extend a prefix by hand.
- **Subagents die at the account's session limit** (HTTP 429). Their PRs and worktrees survive. Read the PR, finish in place, and do not re-delegate blind.
- **A throwaway PR against a throwaway base branch runs a probe workflow on a GitHub runner without juniper-ml's heavy CI.** Only `pr-base-branch-guard.yml` and path-filtered workflows have no `main` filter. Draft it, close it, and delete both branches.
- **The worktree guard refuses** `$(git …)` nested in a `git worktree add`, `diff <(git show …)`, and Write/Edit into the PRIMARY checkout's `tmp/`. Write into your worktree's `tmp/`; Bash `cp` into the primary is allowed.
- **Carried from the superseded handoff, still true**:
  - read every member's `requires_dist` before saying how a patch reaches an extra;
  - the `pypi` gate and merges are the owner's; merge approval is per session;
  - verify a peer's "published" through the run's approvals and PyPI;
  - a release proposal merges after every armed PR that adds to its `[Unreleased]`;
  - a post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main            # this handoff's PR at or near the top
gh pr view 776 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state'   # MERGED
gh pr view 777 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state'   # MERGED
gh run list --repo pcalnon/juniper-canopy --workflow juniper-data-schema-drift.yml --limit 3   # a workflow_dispatch run, success
gh api repos/pcalnon/juniper-recurrence/actions/runs/40417898021/jobs --jq '.jobs[] | "\(.name) \(.status) \(.conclusion)"'   # PyPI waiting, unless the owner approved
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-recurrence-client/json'))['info']['version'])"   # 0.3.0 until approval, then 0.3.1
git grep -n 'ARCHIVE_B64_MAX_DEFAULT = ' origin/main -- util/release_train/ceremony.py   # 1_000_000
tail -n 1 ~/.local/state/juniper-experiments/index.jsonl | cut -c1-160    # the correction row (may no longer be last)
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.22 and 1.15.4 until item 1 lands
```

## Git state

- **This worktree** (`iridescent-hatching-muffin`) is on `worktree-iridescent-hatching-muffin`, fast-forwarded to `main` `22e4a4b9`. That `main` carries #2365 and #2366 after #2364; both kept #2364's `docs/REFERENCE.md` line and `ARCHIVE_B64_MAX_DEFAULT = 1_000_000` (checked).
- **What is local**:
  - the one file not yet on `main` is this handoff, landed by its own PR;
  - the gitignored `tmp/` holds this session's scratch: the PR and commit bodies, `tmp/eco*` (the release-train manifests and the ceremony log), `tmp/canopy776` / `tmp/canopy777` (the conflict-resolution scripts and candidates) and `tmp/graphql-probe/`.
- **Retention**: the probe evidence is archived in `reports/2026-10-26_graphql-body-cap-probe/`, so nothing in `tmp/` is the only copy of a record.
- **Worktrees created here:**
  - removed: the juniper-deploy worktree (#264 merged; no `tmp/`) and both ceremony worktrees;
  - **kept on purpose**: the agents' canopy worktrees, `worktrees/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f` (#776, merged) and `worktrees/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f` (#777).
- **Why they are kept**: their `tmp/` holds the agents' evidence, namely the unit and integration lane logs, and the juniper-data 0.17.1 wheel environment behind #776's `equities` capture. `git worktree remove` deletes `tmp/`, so by the owner's retention ruling (parent `Juniper/AGENTS.md`, Temporary files) archive what is still needed before removing either. Their working trees show uncommitted edits: the agents landed everything through the API, so the local branches never moved.

## Documents created or modified this session

- **juniper-ml, via PR**:
  - #2364: `util/release_train/ceremony.py`, `tests/test_release_train_ceremony.py`, `docs/REFERENCE.md`, `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`, `CHANGELOG.md`, `util/ad-hoc/2026-10-26_graphql_body_cap_probe.py`, `reports/2026-10-26_graphql-body-cap-probe/{README.md,runner-run-40410086979.log,workstation-linux-host.json}`;
  - #2367 (by the ceremony): `notes/releases/RELEASE_NOTES_juniper-recurrence-client_v0.3.1.md`;
  - this handoff's PR: this file.
- **Other repos**:
  - juniper-deploy#264: `scripts/test_recurrence_snapshots.sh`, `scripts/config.sh`, `tests/test_recurrence_snapshot_smoke_images.py`, `README.md`, `docs/USER_MANUAL.md`, `docs/REFERENCE.md`, `CHANGELOG.md`;
  - juniper-cascor#729: `src/api/lifecycle/manager.py`;
  - juniper-recurrence#227: `AGENTS.md`, `juniper-recurrence-client/CHANGELOG.md`, `juniper-recurrence-client/juniper_recurrence_client/_version.py`;
  - canopy#776 / #777: their files, listed in each PR. This session added only `CHANGELOG.md` (#776) and `docs/ci_cd/CICD_REFERENCE.md` (#777) resolution commits.
- **Outside any repo**:
  - `~/.local/state/juniper-experiments/index.jsonl` (one appended line);
  - in auto-memory, `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description) and its `MEMORY.md` line.
- **Referenced**:
  - the superseded handoff (above);
  - `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` §5.6.1 point 4 and `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §4.5 (the restart-modal ruling);
  - `notes/releases/RELEASE_NOTES_v0.11.2.md` (the erratum by "draft PRs");
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
