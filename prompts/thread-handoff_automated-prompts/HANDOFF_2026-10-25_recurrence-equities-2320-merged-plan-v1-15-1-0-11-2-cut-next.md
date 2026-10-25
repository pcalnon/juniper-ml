# Thread Handoff — Recurrence × Equities: #2210 landed (juniper-ml#2320); consolidated plan v1.15.1; the juniper-ml 0.11.2 cut next

**Date**: 2026-10-25
**Host**: turing (Darwin, Intel x86_64; no commit signing; bash 3.2). Every landing goes through `util/open_signed_pr.py`, `util/push_signed_commit.py` or `util/ad-hoc/2026-10-17_push_signed_with_retry.py`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-24_recurrence-equities-save-model-snapshot-landed-plan-v1-7-16.md`
**Plans**:
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` at **v1.15.1**, landed by this session as juniper-ml#2334 via `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py`.
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at v1.7.17 (#2328) or **v1.7.18** (#2332, from session "recurrence" [c5454d]; check which has merged). The 0.11.2 cut's record is the revision after v1.7.18.

---

## Goal

Run the **juniper-ml 0.11.2 cut**. The owner ruled the version on 2026-10-25: 0.11.2, not the 0.12.0 that `util/release_train/detect.py` proposes. This arc claimed the cut, and session "recurrence equities" [42fe25] told the Linux-host session "equitites recurrence" [ad9009] and the owner so. No other session should open a 0.11.2 proposal.

Then apply the owner's choice for **juniper-ml#2330**.

This session (turing session 11, "recurrence equities" [42fe25], started from the v1.7.16 handoff) did the following:

- **Item 1.** #2316's post-merge re-check passed on `main` `899796d2`: the three greps printed 1, 1 and 2.
- **Item 2, juniper-ml#2210, landed as juniper-ml#2320** (squash `f7a1442d`, 2026-10-25T18:12:16Z).
  - `run_suite` refuses a suite (exit 2, before the first `--up`) when `per_run_timeout_seconds` does not exceed a cell's worst-case driver budget.
  - The new `run_experiment.worst_case_budget` computes that budget. It sums the health waits (2×90), dataset creation, the wall budget for every wall-bounded phase and `save_model` (the larger of `max_wall` and 60 + 600). Recurrence's predict and crossval each get a fresh `max_wall`. On cascor it adds the 30 s teardown settle and `snapshot_at_end`'s 120 s.
  - The rule is strict `>` with no extra margin. The check sits in `main` after materialisation, not in `load_suite` (the D5 precedent).
  - The nine recurrence suites moved 1200/1800 → 4500, against a 3900 s worst case. The 20 cascor suites already cleared theirs; the tightest are pf2-axis2 and pf3, at 2330 vs 2400.
  - `util/ad-hoc/2026-10-25_driver_budget_survey.py --project-dir <Juniper root>` reproduces the survey.
  - The post-merge re-check passed on `main` `c86a5e5e`, and `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --check` is clean there.
- **The out-of-scope finding is juniper-ml#2330**, filed by session [c5454d] at its owner's request. `p4/e-c-cascor-noise-robustness.yaml` fails `WallBudgetContractTest` whenever its sibling base resolves; CI never sees it.
- **Owner ruling, 2026-10-25: the next cut is 0.11.2.** It is recorded in consolidated plan v1.15.1 (#2334) and recurrence plan v1.7.18 (#2332).
- **Consolidated plan v1.15.1** (#2334) records #2320's merge and re-check, #2330 as a §6 Group C owner item, R-ML-SERVERS's floors (ml#2326) and the 0.11.2 ruling.

## Remaining work, in order

1. **juniper-ml#2330: the owner chooses.** The discussion was opened on 2026-10-25, and this session recommended option 1.
   - **Option 1:** `execution.max_wall_seconds: 5400` in `util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml`, plus a comment citing #2330.
     - It is a one-line change. The worst case becomes 180 + 120 + 5400 + 30 + 120 = 5850 s, under its 7200 s timeout.
     - Cell ids and `config_sha256` are unchanged, because the execution block is a forwarded flag.
     - Add a CI pin, like `test_the_recurrence_suites_stay_above_their_surveyed_budget`, because CI cannot judge E-C.
   - **Option 2:** exempt E-C, on its own 517 s/cell measurement.
   - **Option 3:** re-derive the cap threshold, which needs a fresh measurement.
   - Verify with `JUNIPER_EXP_PROJECT_DIR=/Users/pcalnon/Development/python/Juniper python3 -B -m unittest tests.test_experiment_suite_yamls`, which must report 0 failures.
2. **The juniper-ml 0.11.2 cut.** Follow the 0.11.1 cut as the template:
   - the proposal juniper-ml#2319, with `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py` for `docs/REFERENCE.md`'s Version cell, compatibility sentence and 0.11.x row;
   - the release notes juniper-ml#2321 (`notes/releases/RELEASE_NOTES_v0.11.1.md`).

   And the release-train memory: `propose.py --json` dry-run before `--execute`, and the preflight with `util/ad-hoc/2026-10-21_simulate_release_proposal.py`.

   **detect.py has no version override** (its options are `--repo-root`, `--ecosystem-root`, `--owner`, `--registry`, `--package`, `--local-git`, `--json`), and `propose.py` reads the version from detect.py's manifest (`--manifest`).
   - Emit the manifest with `--json` and set juniper-ml's proposed version to 0.11.2 per the ruling. Find the field first; do not guess it.
   - Then preflight: `python3 util/ad-hoc/2026-10-21_simulate_release_proposal.py --package juniper-ml --from-version 0.11.1 --to-version 0.11.2 --sim-dir <scratch>/sim`.
   - Run both tools without `-I`: `propose.py` imports `detect` from its own directory.

   **What 0.11.2 ships:** R-ML-SERVERS's `[servers]` floors (ml#2326, `juniper-cascor>=0.12.0`, `juniper-data>=0.17.1`). It also ships ml#2062's fix, ml#2333 (open on 2026-10-25), if the owner wants to wait for it. Ask before cutting.
   - #2320 and the C9 guard (#2322) are `util/` tooling, which the wheel does not ship, but `CHANGELOG.md` `[Unreleased]` lists them.
   - The proposal inserts `## [0.11.2]` under `## [Unreleased]` (memory `changelog-entry-vs-release-proposal`).

   **The gates:**
   - Merging the proposal needs this new session's own owner approval. The 2026-10-25 approval was given to session [42fe25].
   - The ceremony runs on the tree at the proposal's merge sha.
   - The `pypi` deployment gate is the owner's click (memory `pypi-gate-is-owner-only`). Report the run id and the approval command.
   - Confirm the publish at `https://pypi.org/pypi/juniper-ml/0.11.2/json`.
3. **Re-check #2334 after merge**, about an hour later:
   - `git show origin/main:notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md | grep -c "^- \*\*Version\*\*: 1.15.1"` should print 1, or show a later version that keeps the v1.15.1 lines;
   - `python3 -I util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py --check` on a tree at `main` should exit 0.
4. **Owner items carried** from v1.7.16:
   - the parent `Juniper/AGENTS.md` RELEASED paragraph, now juniper-ml 0.11.1 and later 0.11.2;
   - the recurrence-client 0.3.1 release;
   - juniper-config-tools 0.2.0;
   - the W0.1 service-core half;
   - juniper-data's next release carrying W5.7;
   - refreshing the sibling checkouts.
5. **Follow-ups**: the first live exercise of `save_model`'s snapshot path (v1.7.16 item 4), juniper-canopy#735–738 and #751, juniper-deploy#250, the `ARCHIVE_B64_MAX_DEFAULT` measurement, and an optional E-H run with `--shared-equities-cache`.

## Landing rules learned this session

- **CHANGELOG `[Unreleased]` collisions.**
  - A release proposal inserts `## [x.y.z]` under `## [Unreleased]`. A PR built before the proposal merges lands its entry inside the release section, so let the proposal merge, fast-forward, and re-run the idempotent apply script.
  - Two PRs that each open the empty `[Unreleased]` conflict. #2322 landed first and #2320 rebuilt in four pinned steps: push `main`'s verbatim `CHANGELOG.md`, run update-branch (`gh api -X PUT repos/pcalnon/juniper-ml/pulls/N/update-branch -f expected_head_sha=<head>`), re-apply on a copy of the merged head, and push again.
- **Sequence Safety** fails a renamed or shrunk symbol. Waive it in a commit body with `Allow-Symbol-Loss: <kind>:<qualified.name>[, ...]`, for example `method:TimeoutOrderingContractTest.test_...` or `func:_driver_validator`. The squash keeps it.
- **Attribute macOS failures against a pristine `git archive` export**, run one after the other, never at the same time. On #2320 the 13 affected suites failed the same 13 names (memory `turing-juniper-ml-darwin-test-failures`).
- **Under the worktree guard**, a heredoc append and a `gh` poll loop are refused. Use the Edit tool, and small `python3 -I` pollers in the scratchpad.
- **Check the Wi-Fi link before a large upload.** On 2026-10-25, 5 GHz ch 149 at SNR 24 dB took a 1 MB `REFERENCE.md` in 5 s, on attempt 1.

## Verification commands for the new thread

```bash
gh pr view 2320 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + .mergeCommit.oid'   # MERGED f7a1442d...
gh pr view 2334 --repo pcalnon/juniper-ml --json state -q .state   # MERGED (consolidated plan v1.15.1)
gh pr view 2332 --repo pcalnon/juniper-ml --json state -q .state   # MERGED (recurrence plan v1.7.18)
gh issue view 2330 --repo pcalnon/juniper-ml --json state -q .state   # OPEN until the owner's option lands
gh pr list --repo pcalnon/juniper-ml --state open --search "release juniper-ml v0.11.2"   # empty: nobody else opened the proposal
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.1 until the cut publishes
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/serene-gathering-oasis`, on branch `worktree-serene-gathering-oasis`, fast-forwarded to `main` `c86a5e5e`. Its only working-tree changes are the plan edit, the v1.15.1 script and this handoff, which #2334 and this handoff's PR carry. Once they merge, `git checkout -- . && git clean -fd` on it is safe.
- The sibling checkouts were read only: juniper-recurrence `23a8691f` (equal to GitHub `main`) and juniper-cascor `2ec3bf31`.

## Documents created or modified this session

- juniper-ml#2320:
  - code: `util/experiments/run_experiment.py`, `util/experiments/run_suite.py`;
  - the nine recurrence suites under `util/experiments/suites/`: `recurrence-d-sweep.yaml`; `p4/e-d-recurrence-d-sweep.yaml`, `p4/e-e-recurrence-readout-spectrum.yaml`, `p4/e-f-recurrence-irregularity.yaml`, `p4/e-g-recurrence-cv-scheme.yaml`, `p4/e-h-recurrence-real-data.yaml`; `perf/pf5-recurrence-d-scaling.yaml`, `perf/pf6-recurrence-nsteps-scaling.yaml`, `perf/pf7-recurrence-readout-rungs.yaml`;
  - tests: `tests/test_run_experiment.py`, `tests/test_run_suite.py`, `tests/test_run_suite_acceptance.py`, `tests/test_experiment_suite_yamls.py`;
  - docs: `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `CHANGELOG.md`;
  - new scripts: `util/ad-hoc/2026-10-25_driver_budget_survey.py`, `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py`.
- juniper-ml#2334: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.0 → v1.15.1) and `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py` (new).
- This file (new).
- Referenced:
  - the predecessor handoff above, and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-published-plan-v1-7-15.md` (the handoff the session was started on; superseded);
  - `notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` (D5);
  - `reports/2026-10-04_recurrence-equities-cv-matrix/scenario-a-rerun/c001-manifest.json`;
  - juniper-ml#2319, #2321, #2322, #2326, #2330, #2332, #2333.
