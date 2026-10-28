# Handoff: Cursor flood-3 arc, the owner's continuation. juniper-cascor 0.13.0 waits at its pypi gate; the 2026-10-26 rows are closed or carried; ml#2064 is in flight

**Date**: 2026-10-28 (UTC)

**Arc**: The Cursor flood-3 disposition and its follow-ups. This stretch is the owner's request of 2026-10-27: "Continue from handoff", with merge approval for this session's PRs.

**Record**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, cited below as `…FLOOD-3-DISPOSITION.md`. This handoff's PR makes the record's eighth update (§4 rows, §6 traps, §8, §9).

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_flood3-owner-items-closed-erratum-cleanup-backlog.md`, cited below as `HANDOFF_2026-10-27_…backlog.md`.

**Host**: the Linux host, session worktree `.claude/worktrees/whimsical-leaping-glacier`. Commits go only through GraphQL `createCommitOnBranch` (`util/open_signed_pr.py`, `util/push_signed_commit.py`).

---

## Goal

Nothing is owed unless the owner asks. What remains is the owner's (Remaining work, items 1-3), and the merges that follow from them (items 2 and 4). The owner's rulings of 2026-10-27:

- the release: "Cut it now";
- the cleanup: "Yes, remove them".

## Completed (verified on GitHub, PyPI or TestPyPI)

- **The cleanup.** The predecessor had already removed 17 of its 18 worktrees, with their unique files preserved in `juniper-ml/tmp/worktree-cleanup-2026-10-27/`. This session removed the 18th, `enchanted-sniffing-popcorn`, and its branch, after its process exited and its 14 unique files matched the preserved copies. `REMOVED.tsv` there records it.
- **pytest 9.2.0** (PyPI 2026-10-27 21:30Z) turned juniper-cascor `main` red, through a test that read a private pytest attribute. juniper-cascor#732 (`54e02310`) fixed it. No other repo's `main` went red on 9.2.0.
- **juniper-cascor 0.13.0.**
  - The proposal is juniper-cascor#733 (`61a67c53`). It includes a CHANGELOG coverage commit: the dependency-lock moves #717, #720 and #726.
  - The Release `v0.13.0` was cut at `61a67c53` with `--target-sha`, gated on that commit's green run 40607398657. It holds the `latest` badge.
  - TestPyPI `/0.13.0/json` returns 200. Publish Container Image succeeded.
  - Publish run **40608671287** (created 2026-10-28 00:25:29Z) waits at the `pypi` gate.
- **The §4 rows found 2026-10-26.**
  - Fixed: juniper-cascor#734 (`68eb4ebf`; the memory-budget suite now runs in the unit legs) and juniper-data#499 (`cce37667`; all 14 workflows in the table).
  - Fix open: juniper-ml#2378 (docs).
  - Carried by the `/tmp` arc: the redrive-test row, which that arc agreed to take (juniper-ml#2360's convention doc, §10).
- **The two §8 leads.**
  - Bandit: does not hold. 165 of 165 SARIF uploads succeeded over 200 runs.
  - Codecov: no repo has `CODECOV_TOKEN`. juniper-data's uploads were silently rejected until 2026-10-27 22:51Z, then accepted without a token from 23:47Z. The change was on Codecov's side.

## Remaining work

1. **The owner's `pypi` gate for juniper-cascor 0.13.0.** Approve run 40608671287 before 2026-11-27 00:25Z, the end of its 30-day re-run window. GitHub cancels it at 2026-12-02 00:25Z. TestPyPI already holds 0.13.0, so a lost run means a new version number. Never approve it from a session.
2. **juniper-ml#2376** is the `/tmp` arc's PR. It fixes `main`'s red Regression Tests: five duplicati tests fail on tmpfs runners. It needs the owner's merge approval. After it lands, update-branch these three:
   - juniper-ml#2378;
   - juniper-ml#2379, the 0.13.0 notes archive, which is armed to auto-merge;
   - this handoff's PR.
   Merge #2378 and this PR with `util/safe_merge.py`. The approval for that does not carry to a new session.
3. **Owner decisions:**
   - Codecov: add `CODECOV_TOKEN`, to the Dependabot store too, or drop the step.
   - cascor `ci.yml:659`: `continue-on-error: ${{ github.event_name != 'pull_request' }}` or leave it.
4. **ml#2064 is juniper-ml#2381**, open at head `edbe25c1`, from the `agent-af4830ffb939894cb` lane.
   - **CI:** red only on the five inherited duplicati tests. The 3.13 leg ran every suite, this PR's included, and passed.
   - **Merge:** after #2376 lands and the branch is updated, with `util/safe_merge.py`. It also edits `ci.yml`, `AGENTS.md`, `docs/REFERENCE.md` and `CHANGELOG.md`, so whichever of it and #2360 merges second needs a re-sync.
   - **For the owner to see:**
     - it bumps `stats.json` to `juniper-experiment-stats/2`, because `eval_scalars` now means the held-out final block;
     - `test_*` columns fill only when that block's split is `test`;
     - register row `APD-ML-002` is left for the owner's close procedure, once cascor 0.13.0 is on PyPI.
5. **After 0.13.0 reaches PyPI:**
   - Check `/pypi/juniper-cascor/0.13.0/json` returns 200.
   - Probe the installed wheel's `compute_classification_accuracy` with `importlib.import_module`.
   - `test_accuracy` fills only once ml#2064 lands, and only against a cascor 0.13.0 service.
6. **Open §4 rows (2026-10-27)**, listed in `…FLOOD-3-DISPOSITION.md` §4:
   - cascor's nightly long lane runs zero tests;
   - 153 performance and five integration tests are selected by no lane;
   - canopy's orphaned memory-budget suite;
   - juniper-data's stale coverage, macOS and `merge_group` claims, and its required `Slow Tests` that cannot fail;
   - two small doc errors.

## Cleanup inventory (this pass)

Nothing in this inventory has been removed. It needs an owner signal plus an API check that each PR is MERGED.

- **Centralized worktrees:**
  - `juniper-cascor--release--v0.13.0--20261027-1816--996134e5`: detached at `61a67c53`. `juniper-ml/tmp/release-cascor-0.13.0/eco/juniper-cascor` symlinks to it. Keep it until 0.13.0 is on PyPI.
  - `juniper-cascor--fix--flood3-backlog-2--20261027-1821--996134e5`: #734 merged. Its ignored `tmp/control-origin-main-996134e5/` is a pristine export, kept under the retention rule.
  - `juniper-data--fix--flood3-backlog-2--20261027-1822--35658ff3`: #499 merged.
- **Lane worktrees under `.claude/worktrees/`:**
  - `agent-a8ac272b0d644d1b6`;
  - `agent-a84219c62702dc20b`, whose `tmp/` holds PR bodies and check-watch output;
  - `agent-af4830ffb939894cb`, #2381's lane. Keep it until #2381 merges; its `tmp/issue2064/` holds the evidence.
- **This session's worktree**, `whimsical-leaping-glacier`, is locked while the session lives.
- **Keep:**
  - `juniper-ml/tmp/release-cascor-0.13.0/`: manifests, the notes preview, the ceremony logs and the pytest 9.2.0 venv. Keep until PyPI publish is verified.
  - `juniper-ml/tmp/worktree-cleanup-2026-10-26/` and `-2026-10-27/`, and `tmp/flood3-deleted-branches.tsv`: keep until the owner says otherwise.
  - About 24 `cascor-test-snapshots-*` directories in `juniper-ml/tmp/`, left there by cascor's test conftest.

## Key context and traps

- **Merge approval is per session** (memory `feedback_headless_merge_approval_policy.md`). This file cannot carry it.
- **The cascor primary is frozen**: live stacks import it. Work in centralized worktrees; `--ecosystem-root` points the train at a scratch root.
- **Worktree isolation refuses some commands**: `git -C`, a `cd` into another `.claude/worktrees/` checkout, loops and `$(…)` around git, and a command name held in a variable. Use plain commands, and `util/ad-hoc/2026-10-26_worktree_blob_classify.py` instead of a status in a sibling worktree.
- **`safe_merge.py`**: read its `MERGED` line, not its exit status.
- **Release dates are UTC.** Open a proposal after 00:00Z when the cut will follow it.

## Verification

```bash
gh release view v0.13.0 --repo pcalnon/juniper-cascor --json tagName,targetCommitish   # v0.13.0, 61a67c53…
gh run view 40608671287 --repo pcalnon/juniper-cascor --json jobs --jq '.jobs[] | "\(.name): \(.status)/\(.conclusion)"'   # TestPyPI success; PyPI waiting (until approved)
curl -s -o /dev/null -w '%{http_code}\n' https://test.pypi.org/pypi/juniper-cascor/0.13.0/json   # 200
gh pr view 2379 --repo pcalnon/juniper-ml --json state,autoMergeRequest --jq '"\(.state) \(.autoMergeRequest != null)"'
gh pr view 2376 --repo pcalnon/juniper-ml --json state --jq .state
```

## Residue: the four remaining-work items of `HANDOFF_2026-10-27_…backlog.md`

1. **A juniper-cascor release:** cut. It is at the gate (item 1 above).
2. **ml#2064:** juniper-ml#2381 is open (item 4 above).
3. **The open §4 rows:** all four are fixed, open in #2378, or carried. Both leads are checked.
4. **The cleanup:** done.

## Documents created or modified

- **This file's PR:**
  - this file (new);
  - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (header, §4, §6, §8, §9).
- **Other PRs:**
  - juniper-ml#2378: `docs/REFERENCE.md`.
  - juniper-ml#2379: `notes/releases/RELEASE_NOTES_juniper-cascor_v0.13.0.md`.
  - juniper-ml#2381: `util/experiments/{stats_summary,plots_cascor,run_experiment,run_suite}.py`, four test suites (two new), two new `util/ad-hoc/2026-10-27_issue_2064_*` scripts, `.github/workflows/ci.yml`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `CHANGELOG.md`, `AGENTS.md`.
  - The record's §9 lists the sibling repos' files.
- **Unversioned:** `juniper-ml/tmp/worktree-cleanup-2026-10-27/REMOVED.tsv` (one appended record).
- **Referenced:**
  - `HANDOFF_2026-10-27_…backlog.md`;
  - `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md` (on #2360's branch);
  - `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`.
