#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-27_flood3_record_seventh_update.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Applies the seventh update of
#   notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md: the
#   owner's three open items of 2026-10-26 (the 0.11.2 notes erratum, the arc's
#   cleanup, and the §4 backlog). Every edit asserts its exact old text and
#   requires exactly one match, so a record that has drifted is refused rather
#   than half-edited; --check reports what is still owed.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-27_flood3_record_seventh_update.py <record.md> [--check]
# -----------------------------------------------------------------------------
"""Apply the flood-3 record's seventh update (the owner's three open items, 2026-10-26/27)."""

import argparse
import sys
from pathlib import Path

APD_PR = "juniper-ml#2369"  # APD-ML-002, cascor half (option A, --reaggregate, non-finite fails a band)

EDITS: list[tuple[str, str, str]] = []


def edit(what: str, old: str, new: str) -> None:
    EDITS.append((what, old, new))


# ---- header -------------------------------------------------------------------------------
edit(
    "header",
    "has been on PyPI since 2026-10-26 17:48Z (§4, §8, §9)\n",
    "has been on PyPI since 2026-10-26 17:48Z. On the owner's request of 2026-10-26, the 0.11.2 security notes carry an erratum, the arc's worktrees and the flood-3 `cursor/*` branches are cleaned up, and every §4 row that was open is fixed, in nine repositories (§4, §8, §9)\n",
)

# ---- §4 statuses ----------------------------------------------------------------------------
edit(
    "§4 lane A3",
    "after writing its JSON when every last-step feature column is constant | open (low) |",
    "after writing its JSON when every last-step feature column is constant | **fixed** — juniper-ml#2366: the summary prints `none (no column has a std > 0)` and the run exits 0; a test pins the CLI's exit status |",
)
edit(
    "§4 outage wait",
    "a dict-shaped `components` aborts the wait (fails closed; pinned by the harvested suite) | open (low) |",
    "a dict-shaped `components` aborts the wait (fails closed; pinned by the harvested suite) | **fixed** — juniper-ml#2366: the whole shape is checked before any status is read, and anything malformed reads `unknown`, so the wait keeps polling and gives up with exit 2. `main` was not fully fail-closed: a junk entry AFTER an operational Actions entry read as operational |",
)
edit(
    "§4 APD-ML-002",
    "| ml | cascor headline accuracy columns are always empty — the open cascor half of APD-ML-002 | already registered (defect register §4.9) |",
    f"| ml | cascor headline accuracy columns are always empty — the open cascor half of APD-ML-002 | **train / val fixed** — {APD_PR}, on the owner's rulings of 2026-10-26: `train_accuracy` and `val_accuracy` from `build_stats`' `final` block (`val_accuracy` documented as selected-on), `final_accuracy` refused, a new `--reaggregate` that launches nothing, and a non-finite value fails any band. Since juniper-ml#2262 the dead names had also made every cascor acceptance band read `absent`. `test_accuracy` stays, to be fed by cascor: juniper-cascor#731 makes the final evaluation compute `accuracy`, which reaches users with the next juniper-cascor release (the owner's call), and the column fills once ml#2064 carries the labelled block into `stats.json`. The recurrence half was fixed by juniper-ml#2145 (2026-10-04) |",
)
edit(
    "§4 claude.yml clause",
    "Still open (low): the fleet `claude.yml` header says the key is \"set at the org level\", which no user-owned repo can have. The line is `.github/workflows/claude.yml:11` in juniper-data, juniper-cascor, juniper-canopy, juniper-data-client, juniper-cascor-client and juniper-cascor-worker, `:12` in juniper-deploy, and `:12` of juniper-ml's template `notes/templates/ci/claude.yml`; juniper-ml's own workflow does not carry it |",
    "The fleet `claude.yml` header said the key is \"set at the org level\", which no user-owned repo can have; **fixed 2026-10-26** in all eight copies, which now say it is a repository secret: juniper-data#498, juniper-cascor#730, juniper-canopy#775, juniper-data-client#248, juniper-cascor-client#188, juniper-cascor-worker#218, juniper-deploy#265 and juniper-ml#2366 (the template `notes/templates/ci/claude.yml`). The docs that repeated the claim were corrected in the same PRs; juniper-ml's own workflow never carried it |",
)
edit(
    "§4 base64",
    "juniper-deploy, juniper-recurrence and juniper-ml have no such line | open (latent) |",
    "juniper-deploy, juniper-recurrence and juniper-ml have no such line | **fixed** — juniper-data-client#248, juniper-cascor-client#188, juniper-cascor-worker#218, juniper-data#498, juniper-canopy#775 and juniper-cascor#730 (2026-10-26). The encode is its own assignment, which `set -e` catches, and an empty result fails the step before anything is committed. Each step was run with stub `git` / `gh` / `base64`: the old one exits 0 and commits an empty lock (the worker's half-commits its pair), the new one exits 1 and calls nothing. The fix turned juniper-data's required macOS leg red, because its suite runs the step and BSD `base64` has no `-w0` (§6) |",
)
edit(
    "§4 data cheatsheet link",
    "`juniper-check-doc-links` 0.1.2 checks only same-file anchors, which is how it survived | open |",
    "`juniper-check-doc-links` 0.1.2 checks only same-file anchors, which is how it survived | **fixed** — juniper-data#498: the link points at `docs/REFERENCE.md`, where the section now lives; all 110 other cross-file anchors in `docs/`, `notes/`, `AGENTS.md` and `README.md` resolve |",
)
edit(
    "§4 ml stale",
    "`stats_summary.py:251` labelling θ \"data-driven\" even when `service.default_theta` is set | open |",
    "`stats_summary.py:251` labelling θ \"data-driven\" even when `service.default_theta` is set | **fixed** — juniper-ml#2366, each claim re-checked first. `--params` is scoped to the pre-0.6.0 CLI (absent at `juniper-recurrence-v0.5.0`, present at `v0.6.0`); the stale `max_symbols` rows describe the 422 refusal and the annotated cut; θ is labelled explicit, service default or data-driven by a new `theta_block()`, from the YAML's raw `service:` block (the normalized config drops it) |",
)
edit(
    "§4 replay_redrive",
    "and `--snapshot` help says \"instead of the newest\" though the default makes a new save | open (low) |",
    "and `--snapshot` help says \"instead of the newest\" though the default makes a new save | **fixed** — juniper-ml#2366: the check tests the snapshot id, and the BLOCKED row records the save's HTTP status and detail; the help names the explicit save |",
)
edit(
    "§4 pr-budget-alarm",
    "| data, data-client | `pr-budget-alarm.yml` headers say a `jq` failure is downgraded to a warning; the script fails the step | open (low) |",
    "| data, data-client | `pr-budget-alarm.yml` headers say a `jq` failure is downgraded to a warning; the script fails the step | **fixed** — juniper-data#498 and juniper-data-client#248, comments only: only the `gh` call is guarded, the `jq` lines run under `set -euo pipefail`, and existing tests already pin that they fail the step |",
)
edit(
    "§4 data quality gate",
    "| data | the Quality Gate passes when an optional lane is `cancelled` (each such lane is also its own required check, so mitigated) | open (low) |",
    "| data | the Quality Gate passes when an optional lane is `cancelled` (each such lane is also its own required check, so mitigated) | **fixed** — juniper-data#498: the four optional lanes pass only on `success` or `skipped`. `5147f6a` shows the intended rule was \"failure=error, skipped=OK\", so accepting `cancelled` was an accident; the juniper-data#471 suite now asserts that `cancelled` fails |",
)
edit(
    "§4 recurrence memory budget",
    "ruleset `20634527` requires it (found by the 2026-10-08 Sequence Safety sweep) | open |",
    "ruleset `20634527` requires it (found by the 2026-10-08 Sequence Safety sweep) | **fixed** — juniper-recurrence#226; the ruleset, re-read live on 2026-10-26, has required `Memory Budget` since 2026-08-27 |",
)
edit(
    "§4 main-verify",
    "The cascor-client line is confirmed; the other three repos' resolvers are unchecked | open |",
    "The cascor-client line is confirmed; the other three repos' resolvers are unchecked | **fixed** — juniper-cascor-client#188, juniper-cascor-worker#218, juniper-deploy#265 and juniper-recurrence#226, plus juniper-data-client#248, whose header carried the same claim. Each resolver was read first: all five take the newest run whose verdict step passed, then the last successful one |",
)
edit(
    "§4 cascor branch protection",
    "`:67` / `:69` say one approving review and a code-owner review are required; the ruleset requires 0 and `false` | open |",
    "`:67` / `:69` say one approving review and a code-owner review are required; the ruleset requires 0 and `false` | **fixed** — juniper-cascor#730: all 24 required checks of ruleset `15081045` with the workflow and job behind each, both rulesets' pull-request settings and bypass actors, the date read and the `gh api` commands that re-derive them. The same false claims in the `develop` table, the admin table and the setup recipe went too |",
)
edit(
    "§4 cascor reference",
    "| cascor | `ci.yml:988` and `conf/memory_budget.json:36` say cascor has no `docs/REFERENCE.md`; it does | open (low) |",
    "| cascor | `ci.yml:988` and `conf/memory_budget.json:36` say cascor has no `docs/REFERENCE.md`; it does | **fixed** — juniper-cascor#730, comments and `_README` only (juniper-cascor#600 created the file on 2026-08-30); the budget verdict is unchanged |",
)
edit(
    "§4 cascor overview",
    "this arc's own consolidation (cascor#709) bumped the version and date inside a template example instead of the document header | open (low) |",
    "this arc's own consolidation (cascor#709) bumped the version and date inside a template example instead of the document header | **fixed** — juniper-cascor#730: the example shows `X.Y.Z` / `YYYY-MM-DD`, and the header and footer agree again. juniper-canopy had the same defect (the canopy row below) |",
)
edit(
    "§4 data codeql + new rows",
    "`docs/DEVELOPER_CHEATSHEET.md:313`'s workflow list omits `sequence-safety.yml` and `main-verify.yml` | open (low) |\n",
    "`docs/DEVELOPER_CHEATSHEET.md:313`'s workflow list omits `sequence-safety.yml` and `main-verify.yml` | **fixed** — juniper-data#498, grounded in the live ruleset `14748749` (its `code_scanning` rule, and the required `Analyze (python)` and `Bandit` checks). The cheatsheet named 7 of the 14 workflows, not 12; it now names all 14 |\n"
    "| canopy | `docs/DOCUMENTATION_OVERVIEW.md`'s two template examples (`:510-511`, `:965-966`) carried the document's own live stamp (1.0.1 / October 8, 2026), so a stamp bump rewrote them along with the header: the cascor row's twin, found by juniper-cascor#730's lane on 2026-10-26 | **fixed** — juniper-canopy#775 (placeholders; the header moves to 1.0.2) |\n"
    "| cascor | `src/tests/test_memory_budget_check.py` (40 tests) never runs in CI: the unit job collects only `src/tests/unit`, the marker filter would deselect its unmarked tests anyway, and the nightly job selects only `long` (found 2026-10-26) | open |\n"
    "| data | `docs/REFERENCE.md`'s workflow table lists 10 of the 14 workflows; juniper-data#498 left it because juniper-data#494 edits that file (found 2026-10-26) | open (low) |\n"
    "| ml | `docs/REFERENCE.md` § Canopy E2E Topology Driver keeps a \"Three predicates that can PASS the easier half\" subsection saying juniper-ml#1672 is not on `main` (it merged 2026-09-04), and its \"Failed Yahoo downloads still skip.\" is stale against juniper-data `main` (the release that changed it is unchecked) (found 2026-10-26) | open (low) |\n"
    "| ml | `tests/test_replay_redrive_stack_refusal.py` fails 13 tests on this host under the repo-`tmp/` convention: the stack script refuses a temp directory inside the ecosystem root, which is where `TMPDIR` now points. CI passes (found 2026-10-26) | open (low) |\n",
)

# ---- §6 traps -------------------------------------------------------------------------------
edit(
    "§6 traps",
    "  - The owner approved both inside the window, on 2026-10-23 and 2026-10-25. When handing a gate over, quote both dates, computed from the run's `created_at`.\n",
    "  - The owner approved both inside the window, on 2026-10-23 and 2026-10-25. When handing a gate over, quote both dates, computed from the run's `created_at`.\n"
    "- **Making a swallowed failure loud can break a test that passed only because of it** (2026-10-26, juniper-data#498).\n"
    "  - juniper-data's suite runs the lockfile commit step on the REQUIRED macOS leg, where BSD `base64` has no `-w0`. Before the base64 fix the step \"passed\" there by committing an empty payload; after it, the encode stops the step (exit 64) and the leg went red.\n"
    "  - The remedy is in the tests, not the workflow (which runs only on `ubuntu-latest`): juniper-data#498 and juniper-data-client#248 install a stand-in for exactly `base64 -w0 FILE` when the runner's `base64` fails a probe of that form. A BSD-like simulation without the stand-in reproduces CI's failures, so the pass is not vacuous. Skipping macOS would have hidden the platform from the one check that proved useful.\n"
    "- **A worktree-isolated session can remove sibling worktrees but cannot inspect `.claude/worktrees/agent-*`** (2026-10-26 cleanup).\n"
    "  - `git worktree remove --force <literal path>` is allowed from the session's own worktree, and `cd <a non-target centralized worktree> && git worktree remove …` for the siblings. `cd` into an agent worktree to run a status is refused.\n"
    "  - So the dirty test is git's own refusal (`remove` without `--force`), then `util/ad-hoc/2026-10-26_worktree_blob_classify.py`, which hashes the files and compares them with `main` and with every object in `main`'s history. Only a blob that never existed on `main` (UNIQUE) needs preserving before `--force` deletes it, ignored files included.\n"
    "  - An mtime test (\"newer than the `.git` pointer\") is useless: a checkout writes every tracked file after the pointer.\n"
    "- **`safe_merge.py` ended twice without merging, and a re-run fixed both** (2026-10-26). GitHub's GraphQL answered two merges with \"Something went wrong while executing your query\": the log ended `ERROR: gh pr merge … failed`, with exit 0 and the PR still CLEAN. And juniper-canopy's CI outlasted the 3000 s window (`absent: Quality Gate`), so the net was disarmed; the gate went green minutes later. Read the `MERGED` line, never the exit status.\n"
    "- **`JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` from a centralized worktree reads the lagging primaries.** `tests/test_service_fork_drift.py` finds sibling repos by walking up from its own file, so from `worktrees/` it reaches the parent `Juniper/` directory and silently checks the primary checkouts instead of skipping. juniper-ml#2365 ran it against a scratch root of fresh clones.\n",
)

# ---- §7 tools -------------------------------------------------------------------------------
edit(
    "§7 tools",
    "  - `2026-10-26_juniper_ml_0_11_3_cut_cochanges.py`: the 0.11.3 cut's `docs/REFERENCE.md` co-changes, plus the #2062 entry's two controls. Its pin parser strips a PEP 508 extras marker.\n",
    "  - `2026-10-26_juniper_ml_0_11_3_cut_cochanges.py`: the 0.11.3 cut's `docs/REFERENCE.md` co-changes, plus the #2062 entry's two controls. Its pin parser strips a PEP 508 extras marker.\n"
    "- Added by the owner's three open items (2026-10-26/27):\n"
    "  - `2026-10-26_erratum_0_11_x_security_floor_probe.py` (juniper-ml#2363): resolves `[servers]`, `[servers]+[tools]`, `[tools]` and `[all]` for juniper-ml 0.10.0-0.11.3 to their members at the lowest admitted versions, from PyPI's published `requires_dist`, and asserts the erratum's nine claims.\n"
    "  - `2026-10-26_release_notes_erratum_0_11_2_0_11_3.py` (juniper-ml#2363): applies the erratum to the archives, to fetched Release bodies and to the CHANGELOG; `--check` reports what is owed.\n"
    "  - `2026-10-26_flood3_delete_closed_pr_branches.py`: deletes a closed, unmerged flood-3 PR's `cursor/*` head only when the branch is in-repo, its tip equals the PR's final head and no open PR uses it, and logs each ref and SHA for a restore.\n"
    "  - `2026-10-26_worktree_blob_classify.py` and `2026-10-26_worktree_preserve_unique.py`: the cleanup's inspection and preservation (§6).\n"
    "  - The backlog lanes' instruments: `2026-10-26_flood3_backlog_verify.py`, `2026-10-26_flood3_backlog_poll_checks.py`, `2026-10-26_flood3_data_sequence_safety_local_repro.py`, `2026-10-26_flood3_backlog_lockfile_test_harness.py`, `2026-10-26_flood3_backlog_commit_step_probe.py` and `2026-10-26_flood3_backlog_workflow_comment_only_check.py`; with them, juniper-ml#2365's `2026-10-26_throttle_check_guard_mutation_check.py` and juniper-cascor#731's `util/ad-hoc/2026-10-26_final_eval_accuracy_mutation_check.py`.\n"
    "  - `2026-10-27_flood3_record_seventh_update.py`: this update.\n",
)

# ---- §8 -------------------------------------------------------------------------------------
edit(
    "§8 guard + remaining",
    "- **Not done, deliberately:** a `tests/test_service_fork_drift.py` guard for the `FailedAuthThrottle` fix. That test requires every guard to cite a defect-register `APD-` id, and the register has no row for this defect. Filing one is a new row in §4.9 (\"Filed after the primer\") of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`. The register's \"five touches\" govern closing a row, not filing one; until 2026-10-10 this bullet called the filing the five-touch protocol. Each of the three copies is pinned by its own repo's regression test.\n"
    "- **The remaining open rows in §4**, including the six that the follow-up's Sequence Safety and throttle sweeps found.\n",
    "- **Resolved (2026-10-26/27): the owner's three open items.** The owner asked on 2026-10-26 to \"address the three open items\", granted merge approval for every PR they produced, and ruled each decision (below).\n"
    "  - **The 0.11.2 security-notes erratum** (ruling: \"0.11.2 + 0.11.3\"). juniper-ml#2362 corrects the 0.11.2 Priority line in place and adds a dated erratum to `notes/releases/RELEASE_NOTES_v0.11.2.md`, with one clarifying sentence in `RELEASE_NOTES_v0.11.3.md`; it is archive-only, with an `Allow-Archive-Edit` trailer, as the archive guard requires. juniper-ml#2363 carries the `CHANGELOG.md` half. The Release v0.11.2 and v0.11.3 bodies were edited to match the archives (`diff -B` clean); no publish run fired. 0.11.1's harmless over-warning stays as published.\n"
    "  - **The cleanup** (ruling: also \"Delete flood-3's only\" for the remote branches).\n"
    "    - 33 worktrees removed: juniper-ml 24 (the twelve `agent-*` and `melodic-hugging-rabin` of the 2026-10-10 handoff, and this arc's 11 centralized ones), juniper-data 3, juniper-cascor 3, juniper-canopy, juniper-recurrence and juniper-deploy one each. 11 local branches deleted.\n"
    "    - Each was inspected first (§6). 37 files that never existed on `main`, all evaluator drafts whose corrected versions landed, plus one canopy test log, were copied to juniper-ml's gitignored `tmp/worktree-cleanup-2026-10-26/` with a `MANIFEST.tsv`.\n"
    "    - 89 remote `cursor/*` heads of closed, unmerged flood-3 PRs deleted (juniper-ml 46, juniper-canopy 22, juniper-data 12, juniper-cascor 6, juniper-data-client 3); 23 were already gone. Each ref and SHA is logged in `tmp/flood3-deleted-branches.tsv`; GitHub's \"Restore branch\" on the PR page brings one back.\n"
    "  - **The backlog** (ruling: \"Fix all; rule on APD-ML-002\"). Every row open in §4 was re-probed on `main` first; none had been fixed elsewhere. The fixes, one PR per repo: juniper-cascor#730, juniper-deploy#265, juniper-recurrence#226, juniper-data#498, juniper-cascor-worker#218, juniper-data-client#248, juniper-cascor-client#188, juniper-canopy#775 and juniper-ml#2366. §4 records each row's outcome, and five new rows.\n"
    f"  - **APD-ML-002**, on the owner's rulings: option A now (`train_accuracy`, `val_accuracy` documented as selected-on), `test_accuracy` kept and fed by cascor, a `--reaggregate` mode, and a non-finite value fails any band. {APD_PR} and juniper-cascor#731 (§4).\n"
    "  - **Done: the fork-drift guard for the `FailedAuthThrottle` fix.** juniper-ml#2365 files `APD-ECO-015` (found already fixed) in §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` and adds the `throttle-check-never-inserts` guard. It is scoped by `ast` to `FailedAuthThrottle.check` in all three copies, so it is not `APD-ML-008`'s marker-text form: it fails on each copy's pre-fix code and on 21 marker-preserving regressions that a whole-file marker passes. Until 2026-10-26 this bullet read \"Not done, deliberately\", because the register had no row to cite.\n"
    "- **Still open in §4:** the four rows marked open, all found on 2026-10-26 while closing the backlog, and `test_accuracy`, which waits for a juniper-cascor release and ml#2064. Two leads from the backlog lanes are unverified and are not rows: juniper-data's `ci.yml` reads `secrets.CODECOV_TOKEN`, which is not among the repository's secrets, and juniper-cascor's `Bandit` upload step may fail while `Bandit` is a required check.\n",
)

# ---- §9 -------------------------------------------------------------------------------------
edit(
    "§9 this pass",
    "- **This record's sixth update**, juniper-ml#2358, records 0.11.3 on PyPI (2026-10-26 17:48Z) and changes only this file.\n",
    "- **This record's sixth update**, juniper-ml#2358, records 0.11.3 on PyPI (2026-10-26 17:48Z) and changes only this file.\n"
    "\n"
    "**The owner's three open items, 2026-10-26/27 (§8):**\n"
    "\n"
    "- **Erratum:** juniper-ml#2362 (`notes/releases/RELEASE_NOTES_v0.11.2.md`, `notes/releases/RELEASE_NOTES_v0.11.3.md`) and juniper-ml#2363 (`CHANGELOG.md`; new `util/ad-hoc/2026-10-26_erratum_0_11_x_security_floor_probe.py` and `util/ad-hoc/2026-10-26_release_notes_erratum_0_11_2_0_11_3.py`). The Release v0.11.2 and v0.11.3 bodies were edited to match.\n"
    "- **Backlog, sibling repos:**\n"
    "  - juniper-cascor#730: `docs/ci_cd/BRANCH_PROTECTION.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `CHANGELOG.md`, `.github/workflows/lockfile-update.yml`, `.github/workflows/ci.yml`, `.github/workflows/claude.yml`, `conf/memory_budget.json`.\n"
    "  - juniper-data#498: `.github/workflows/ci.yml`, `claude.yml`, `lockfile-update.yml`, `pr-budget-alarm.yml`, `CHANGELOG.md`, `docs/DEVELOPER_CHEATSHEET.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/ci_cd/CICD_REFERENCE.md`, `juniper_data/tests/unit/test_lockfile_signed_commit.py`, `juniper_data/tests/unit/test_quality_gate_results.py`.\n"
    "  - juniper-canopy#775: `.github/workflows/lockfile-update.yml`, `.github/workflows/claude.yml`, `docs/ci_cd/CICD_REFERENCE.md`, `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `CHANGELOG.md`.\n"
    "  - juniper-data-client#248: `.github/workflows/pr-budget-alarm.yml`, `lockfile-update.yml`, `claude.yml`, `main-verify.yml`, `tests/test_lockfile_signed_commit.py`, `docs/REFERENCE.md`, `CHANGELOG.md`.\n"
    "  - juniper-cascor-client#188: `.github/workflows/main-verify.yml`, `lockfile-update.yml`, `claude.yml`, `docs/REFERENCE.md`, `CHANGELOG.md`.\n"
    "  - juniper-cascor-worker#218: `.github/workflows/main-verify.yml`, `lockfile-update.yml`, `claude.yml`, `docs/DEVELOPER_CHEATSHEET.md`, `CHANGELOG.md`.\n"
    "  - juniper-deploy#265: `.github/workflows/main-verify.yml`, `.github/workflows/claude.yml`, `docs/REFERENCE.md`, `CHANGELOG.md`.\n"
    "  - juniper-recurrence#226: `.github/workflows/memory-budget.yml`, `.github/workflows/main-verify.yml`.\n"
    "  - juniper-cascor#731 (APD-ML-002's cascor half): `src/api/lifecycle/classification_metrics.py`, `src/api/lifecycle/manager.py`, `src/tests/unit/api/test_classification_metrics.py`, `src/tests/unit/api/test_final_eval_accuracy.py` (new), `util/ad-hoc/2026-10-26_final_eval_accuracy_mutation_check.py` (new), `docs/api/API_SCHEMAS.md`, `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`, `CHANGELOG.md`.\n"
    "- **Backlog, juniper-ml:**\n"
    "  - juniper-ml#2366: `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `docs/QUICK_START.md`, `util/ad-hoc/README.md`, `notes/templates/ci/claude.yml`, `util/ad-hoc/2026-10-04_replay_redrive.py`, `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py`, `util/ad-hoc/2026-10-05_rerun_after_actions_outage.py`, `util/experiments/run_experiment.py`, `util/experiments/stats_summary.py`, and five test suites.\n"
    "  - juniper-ml#2365: `tests/test_service_fork_drift.py`, `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, `docs/REFERENCE.md`, and new `util/ad-hoc/2026-10-26_throttle_check_guard_mutation_check.py`.\n"
    f"  - {APD_PR}: APD-ML-002 (see its body for the files).\n"
    "- **This record's seventh update** rides the arc's closing PR, which changes this file and adds `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-27_flood3-owner-items-closed-erratum-cleanup-backlog.md` and the §7 tools not committed elsewhere.\n",
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("record", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if "NNNN" in APD_PR:
        print("REFUSED: set APD_PR to the APD-ML-002 PR's number first")
        return 2
    text = args.record.read_text(encoding="utf-8")
    owed = []
    for what, old, new in EDITS:
        if new in text:
            continue
        n = text.count(old)
        if n != 1:
            print(f"DRIFT {what}: expected exactly one match of the old text, found {n}")
            return 1
        owed.append(what)
        text = text.replace(old, new)
    long_lines = [i + 1 for i, line in enumerate(text.splitlines()) if len(line) > 4000]
    if long_lines:
        print(f"WARN  lines over 4000 characters: {long_lines}")
    if args.check:
        print("OWED " + ", ".join(owed) if owed else "OK nothing owed")
        return 1 if owed else 0
    args.record.write_text(text, encoding="utf-8")
    print(f"EDIT {len(owed)} section(s): {', '.join(owed)}" if owed else "OK nothing owed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
