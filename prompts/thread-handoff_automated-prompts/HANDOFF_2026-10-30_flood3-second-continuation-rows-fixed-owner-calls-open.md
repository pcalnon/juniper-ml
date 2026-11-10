# Handoff: Cursor flood-3 arc, the owner's second continuation. Every 2026-10-27 row is fixed or resolved; owner calls and a cleanup remain

**Date**: 2026-10-30 (UTC)

**Arc**: The Cursor flood-3 disposition and its follow-ups. This stretch is the owner's request of 2026-10-29: "continue with handoff", with merge approval for this session's PRs.

**Record**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, cited below as `…FLOOD-3-DISPOSITION.md`. This handoff's PR makes the record's ninth update: the header, §4, §6, §7, §8 and §9.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`, cited below as `HANDOFF_2026-10-28_…pypi-gate.md`.

**Host**: the Linux host.
- **This session:** worktree `.claude/worktrees/prancy-whistling-knuth`, ListAgents `flood3-continuation-cascor-0-13-0-at-pypi-gate [048bec]`.
- **A second session continues the same predecessor**, `[901969]`, and is still alive; see item 1.0.
- **Commits** go only through GraphQL `createCommitOnBranch`: `util/open_signed_pr.py`, `util/push_signed_commit.py`, `util/ad-hoc/2026-10-08_fleet_flood3_reset_pr_branch.py`.

---

## Goal

Nothing is owed unless the owner asks. What remains:
- the owner's calls (Remaining work, item 1);
- two watch items (items 2 and 3);
- low rows (item 4);
- a cleanup that needs an owner signal (item 5).

## Completed (verified on GitHub, PyPI or the host)

- **Already done when this pass began** (re-probed 2026-10-29):
  - juniper-ml#2376 (01:21Z), #2380 (01:44Z), #2379 (01:56Z), #2378 (02:08Z) and #2381 (03:23Z) merged on 2026-10-28;
  - juniper-cascor 0.13.0 has been on PyPI since 2026-10-28 11:43Z (publish run 40608671287; `/pypi/juniper-cascor/0.13.0/json` returns 200).
- **The import probe** (`HANDOFF_2026-10-28_…pypi-gate.md` item 5) is `util/ad-hoc/2026-10-29_cascor_0_13_0_wheel_import_probe.py`.
  - **Setup:** a clean venv holding only the sha256-checked wheel and torch 2.15.0+cpu.
  - **Result:** 0.13.0 passed all 22 checks (exit 0). The 0.12.0 control failed 2, with `compute_classification_accuracy` absent from both copies (exit 1).
- **Every row found on 2026-10-27 is fixed or resolved.** Codecov is resolved apart from the Dependabot gap (item 1.1). The juniper-ml docstring rides this PR.

  | PR | Squash | What it fixed |
  |---|---|---|
  | juniper-cascor#735 | `453ff286` | the long lane, the slow-integration lane, the five unmarked tests, the 153-test performance smoke (with its `pytest<9.2` cap), `ci.yml:659`, `AGENTS.md` |
  | juniper-canopy#779 | `d5b73321` | the memory-budget suite, the Codecov `token:` input |
  | juniper-data#500 | `4c3b044c` | the stale claims (in 12 files), `Slow Tests`, the Codecov docs |
  | this PR | | `util/ad-hoc/2026-08-25_p5_port_memory_budget.py` |

- **New rows found and fixed:**
  - juniper-canopy#780 (`18a49c85`): canopy's `ci.yml` installed bare `bandit` and uploaded no SARIF.
  - juniper-cascor#736 (`d042de23`): cascor's conftest forced `os._exit(0)` over pytest's exit status.
- **The owner's rulings of 2026-10-29:**
  - Codecov: the owner chose to add the token, and had already done so: "token has already been added to all repos via github gui".
  - cascor's SARIF upload: "Fail on PRs".
  - cascor's performance tests: "Nightly smoke, no timing", then "Cap pytest in that job".
  - cascor's forced exit: "Fix now, own PR".
  - The slow-integration lane: "Fix in #735".
  - The cleanup: "Yes, remove them".
- **The cleanup** of the inventory in `HANDOFF_2026-10-28_…pypi-gate.md`:
  - **Removed:** four worktrees. The other two, `agent-a8ac272b0d644d1b6` and `agent-a84219c62702dc20b`, were already gone. No removal record exists in any `tmp/worktree-cleanup-*` folder, on `origin/main` or elsewhere in `tmp/`.
  - **Preserved first:** 210 files whose content never existed on `main`.
  - **Branches deleted:** two. `fix/issue-2064-cascor-held-out-eval-block` was at `edbe25c1`. `worktree-agent-af4830ffb939894cb`, at `ff6cc37d`, was deleted with `-d` after the handoff review found it.
  - **The cleanup's own ledger:** `juniper-ml/tmp/worktree-cleanup-2026-10-29/REMOVED.tsv`, with `MANIFEST.tsv` beside it.

## Remaining work

1. **Owner calls.** A session never acts on these without the owner's word.
   0. **Close the duplicate continuation, or tell it to stand down, before answering it.**
      - **Who:** session `0f840224`, forked as `2fc3f4e1` (pid 4148734, worktree `.claude/worktrees/iridescent-sniffing-snail`, ListAgents `[901969]`). The owner started it on 2026-10-28 around 10:14Z with the same request: "continue from handoff: …HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md. merge approval granted."
      - **What it is waiting on:** since 2026-10-28 20:58Z, a question dialog asking about cascor's SARIF upload, Codecov and the cleanup. This pass has since ruled on and done all three.
      - **The risk:** if it is answered, it acts on stale state with merge approval. Its local branch `fix/flood3-backlog-3` has the name that #735, #779 and #500 used as their remote head ref.
      - **Inbox:** five messages wait there unread.
        - Four came from the recurrence-arc sessions, between 2026-10-28 22:07Z and 2026-10-29 21:16Z. They mention merges, the cascor primary and `e8e8bf4d`, and ask for replies.
        - One came from this session (2026-10-29 21:04Z), claiming the flood-3 items. It was written while `[901969]` was still mistaken for the predecessor.
        - Answering its dialog delivers all five, and it may act on them.
   1. **Decide whether to add `CODECOV_TOKEN` to the Dependabot stores** of juniper-data and juniper-canopy, the only two that upload.
      - It is in all nine repositories' Actions secrets (added 2026-10-29 22:08-22:16Z) and in no Dependabot store, so a Dependabot PR's upload stays tokenless.
      - Only the owner can add it, because no session can read the value.
   2. **Decide whether the other repositories' SARIF uploads also fail on PRs**, as cascor's now does. `continue-on-error: true` stands at these lines of each `ci.yml` on `origin/main` (2026-10-30): juniper-data `:606`, juniper-canopy `:581`, juniper-data-client `:611`, juniper-cascor-client `:529` and juniper-cascor-worker `:590`.
      - In data, data-client, cascor-client and cascor-worker, `Bandit` is a required context, so a failed upload already leaves a PR waiting with Security Scans green. data and data-client skip the upload when the SARIF is missing (a `hashFiles` guard).
      - canopy requires `Security Scans` but not `Bandit`, so its broken upload was silent (`…FLOOD-3-DISPOSITION.md` §4).
      - `util/ad-hoc/2026-10-29_sarif_upload_continue_on_error_census.py <Juniper root>` re-derives the list.
   3. **The duplicate session's three worktrees:** `worktrees/juniper-{canopy,cascor,data}--fix--flood3-backlog-3--20261028-0517--*`, cut at 10:17Z on 2026-10-28.
      - The canopy and data ones hold no change.
      - The cascor one holds the uncommitted drain fix to `src/tests/performance/test_concurrency_scaling.py`, which juniper-cascor#735 verified and adopted. It also holds an ignored 7 MB `logs/juniper_cascor.log` and `src/tests/performance/baselines/baseline_20261028.json`.
      - Each local branch, `fix/flood3-backlog-3`, has no commits.
      - Settle item 1.0 first.
   4. **Register row `APD-ML-002`** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`) is the owner's five-touch close.
      - No run has filled `test_accuracy` yet.
      - A stack launched from the canonical checkout serves cascor#731, since the cascor primary moved to `e8e8bf4d` (2026-10-29 20:48:58Z, actor unrecorded, under the live `:8202` stack). `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md` surfaced the move.
      - juniper-deploy still pins 0.12.0.
   5. **Host environments.** Never modify either from a session.
      - `JuniperCanopy1` holds juniper-observability 0.4.0 and juniper-service-core 0.5.0, below canopy's floors (0.4.1 and 0.7.1). Two local test failures follow.
      - `JuniperCascor1`'s editable install still reports juniper-cascor 0.11.0, so cascor's `test_version_matches_pyproject` fails locally.
2. **Watch: drop the pytest cap.** Drop `pytest<9.2` from cascor's `performance-smoke` job (`.github/workflows/scheduled-tests.yml`) once a pytest-benchmark release supports pytest 9.2.
   - 5.3.0 and 5.2.3 both error at setup on 9.2.0: `'Function' object has no attribute '_nodeid'`.
   - Before proposing it, a session reruns a one-line `benchmark` test on the new release. Merging needs the owner's approval in that session.
3. **Watch: the first scheduled cascor nightly after #735 and #736.** Cron is 03:00Z daily; the run must be at `d042de23` or later.
   - **Expected**, matching the dispatch run 40985597827 on #735's head:
     - smoke: `153 passed`;
     - slow integration: 15 passed, 5 golden skipped;
     - long: `1 xfailed`;
     - slow unit: 15 passed.
   - **If red:** a smoke error naming `_nodeid` means the cap was lost. A red `check_junit_executed.py` step means a lane executed nothing or hid a failure. Report either to the owner; never deselect tests to turn it green.
4. **Open §4 rows (low).** A session may fix them on the owner's word.
   - juniper-data#500's leftovers, listed in that PR's body;
   - five cascor docs that still name `pytest.ini`, listed in juniper-cascor#735's body.
5. **Cleanup inventory (this pass).** Nothing here is removed. Each needs an owner signal, then the four gates in the header of `REMOVED.tsv`:
   1. no process holds it (`util/ad-hoc/2026-10-29_worktree_holder_check.py`, with a positive control);
   2. its PR is MERGED and its head branch is gone on GitHub;
   3. its HEAD is an ancestor of `origin/main`, or of the PR's final head for a squash;
   4. every changed file is SAME on `main` or in its history, or else preserved, with a `diff -rq` of the preserved tree. This includes the image and PDF suffixes the classifier skips.

   **Every centralized worktree below is dirty** (the lanes uploaded through the API and never committed locally). Removal needs `--force`, which also deletes its ignored `tmp/`. Those `tmp/` folders hold the lanes' scripts and logs, about 51 scripts in all, behind claims in the record. **Preserve each `tmp/` under `juniper-ml/tmp/worktree-cleanup-<date>/` before removal.** Promoting the claim-backing scripts to each repository's `util/ad-hoc/` is the owner's call.
   - **Centralized worktrees:**
     - `juniper-cascor--fix--flood3-backlog-3-20261029--20261029-1726--e8e8bf4d` (#735): `tmp/flood3-backlog-3/` (logs, scripts, probe venvs).
     - `juniper-cascor--fix--conftest-forced-exit-keeps-status--20261029-2017--e8e8bf4d` (#736's first head, superseded): `tmp/conftest-exit/` (139M). It holds #736's old-versus-fixed exit-status proof (`prove_old_fails.bash`, `exit-status-old.log`, `exit-status-fixed.log`), which the re-sync did not copy.
     - `juniper-cascor--fix--conftest-forced-exit-keeps-status-resync--20261029-2045--453ff286` (#736): `tmp/resync/`.
     - `juniper-canopy--fix--flood3-backlog-3--20261029-1727--7fb3a159` (#779): `tmp/flood3-backlog-3/`.
     - `juniper-canopy--fix--bandit-sarif-extra--20261029-1823--d5b73321` (#780).
     - `juniper-data--fix--flood3-backlog-3--20261029-1727--95ce8190` (#500): `tmp/flood3/`.
   - **Local branches in juniper-cascor**, each checked out in one of the worktrees above: `fix/flood3-backlog-3-20261029`, `fix/conftest-forced-exit-keeps-status` and `fix/conftest-forced-exit-keeps-status-resync`. This pass's canopy and data worktrees are detached.
   - **This session's worktree** stays locked while the session lives. Its `tmp/session/` holds the probe venvs, the downloaded wheels, logs and scratch helpers. The claim-backing helpers are promoted to `util/ad-hoc/` in this PR.
   - **`.claude/worktrees/whimsical-leaping-glacier`:** its session has ended (no lock; the holder check reads it clear), so it is removable under the gates.
     - It is **clean**, so a plain `git worktree remove` succeeds without asking, and deletes its ignored `tmp/` with it.
     - That `tmp/` holds six work folders (17 files, 384K). At least one file there, `tmp/issue2064-fix/cascor_eval_fixtures.py` (blob `9517d689`), is found nowhere in `main`'s history.
     - Preserve that `tmp/` before any removal.
   - **Keep until the owner says otherwise:**
     - `juniper-ml/tmp/release-cascor-0.13.0/`, where `eco/README.txt` replaces the dangling symlink;
     - `tmp/worktree-cleanup-2026-10-26/`, `-27/` and `-29/`;
     - `tmp/flood3-deleted-branches.tsv`;
     - 84 `cascor-test-snapshots-*` directories in `juniper-ml/tmp/`, left by cascor's test conftest. By date: 49 from 10-26, 24 from 10-27, 7 from 10-28 and 4 from 10-29.

## Key context and traps

- **Merge approval is per session** (memory `feedback_headless_merge_approval_policy.md`). This file cannot carry it.
- **juniper-ml#2360** (the `/tmp` arc; OPEN, DIRTY, auto-merge armed) shares five files with `main`'s later work: `.github/workflows/ci.yml`, `AGENTS.md`, `CHANGELOG.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` and `docs/REFERENCE.md`.
  - Since its merge-base `ff6cc37d`, three PRs changed them: juniper-ml#2381 (all five), #2378 (`docs/REFERENCE.md`) and #2356 (`ci.yml`).
  - Its re-sync must keep `main`'s side of every one. A whole-file re-sync that passes CI would merge a revert with no review, because the PR is armed.
- **The cascor primary is imported by live stacks.** The `:8202` uvicorn (pid 2857489, cwd `juniper-cascor/src`) runs from it. Never pull, check out or edit it. Work in centralized worktrees.
- **Worktree isolation refuses some shell shapes:**
  - `git -C` into this repository's shared checkout or its sibling `.claude/worktrees/` checkouts. Use plain `git worktree list`; `git -C` into the other repositories works.
  - loops, and `$(…)` around git or gh;
  - braces with commas inside a quoted argument (a GraphQL query is refused);
  - `sudo`.

  Isolation also refuses Write and Edit into the primary checkout, so session files go in this worktree's `tmp/`.
- **`util/safe_merge.py` and `util/wait_for_checks.py` take a bare `--repo` name** (`juniper-canopy`); they add the owner. Read the `MERGED` line, not the exit status.
- **The blob classifier skips image and PDF suffixes everywhere.** Run `util/ad-hoc/2026-10-29_cleanup_skipped_suffix_sweep.py` and a `diff -rq` before any removal (`…FLOOD-3-DISPOSITION.md` §6).
- **`git worktree remove` without `--force` is no dirty test** for a worktree whose unique files are all ignored: it removes them without asking.
- **On this host a pip torch needs `env -u LD_LIBRARY_PATH -u LIBTORCH`.** Without it, rust_mudgeon's libtorch is loaded first.
- **cascor's `Documentation Links` lint reads a `.py` path in a workflow comment as a script reference.** Pre-commit does not run it.
- **Release dates are UTC.** Open a proposal after 00:00Z when the cut will follow it. This is carried from `HANDOFF_2026-10-28_…pypi-gate.md`; no release is pending in this arc.

## Verification

```bash
gh pr view 735 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'    # MERGED 453ff286
gh pr view 736 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'    # MERGED d042de23
gh pr view 779 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'    # MERGED d5b73321
gh pr view 780 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'    # MERGED 18a49c85
gh pr view 500 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'      # MERGED 4c3b044c
python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py     # actions=<date> in all nine rows; dependabot=- until the owner adds it
gh run list --repo pcalnon/juniper-cascor --workflow scheduled-tests.yml --event schedule --limit 1 --json conclusion,createdAt,headSha
#   first post-fix nightly: createdAt >= 2026-10-30T03:00Z and headSha d042de23 or later; the 2026-10-29T03:00:36Z run is pre-fix
git worktree list --porcelain | grep -A3 'iridescent-sniffing-snail$'    # a "locked claude session … (pid P start S)" line: the duplicate (item 1.0) may be alive
cut -d' ' -f22 /proc/4148734/stat    # alive only if this prints the lock line's start value (438027458 on 2026-10-30); a killed session leaves its lock line behind
```

## Residue: the remaining work of `HANDOFF_2026-10-28_…pypi-gate.md`, item by item

1. **The `pypi` gate:** approved by the owner; 0.13.0 has been on PyPI since 2026-10-28 11:43Z.
2. **juniper-ml#2376, then the update-branch and merge of #2378, #2379 and that handoff's PR (#2380):** all merged on 2026-10-28.
3. **Owner decisions:**
   - Codecov: resolved (token added), except item 1.1.
   - cascor `ci.yml:659`: ruled, and fixed in #735.
4. **ml#2064 = juniper-ml#2381:** merged at 03:23Z.
   - Its owner-facing points stand: the stats schema is `juniper-experiment-stats/2`; `test_*` columns fill only when the final block's split is `test`; `APD-ML-002` is left to the owner (item 1.4).
   - Its re-sync point against juniper-ml#2360 is carried under Key context.
5. **After 0.13.0 reached PyPI:** the JSON returned 200 and the import probe passed. `test_accuracy` waits on a run (item 1.4).
6. **The open §4 rows of 2026-10-27:** all fixed or resolved, as listed above.

**Its cleanup inventory:** four removed and two already gone; `whimsical-leaping-glacier` is carried to item 5. **Its "Keep" list** is carried to item 5, with the snapshots now at 84. **Its traps** are carried under Key context, including the frozen cascor primary and the `git -C` refusal.

## Documents created or modified

- **This file's PR:**
  - this file (new);
  - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`;
  - `util/ad-hoc/2026-08-25_p5_port_memory_budget.py`;
  - new: `util/ad-hoc/2026-10-29_cascor_0_13_0_wheel_import_probe.py`, `2026-10-29_worktree_holder_check.py`, `2026-10-29_cleanup_skipped_suffix_sweep.py`, `2026-10-29_sarif_upload_continue_on_error_census.py`, `2026-10-29_codecov_token_secret_census.py`, `2026-10-29_junit_totals.py` and `2026-10-30_transcript_last_assistant_texts.py`.
- **Other PRs:** juniper-cascor#735 and #736, juniper-canopy#779 and #780, juniper-data#500. Every file is listed in `…FLOOD-3-DISPOSITION.md` §9.
- **Unversioned:**
  - `juniper-ml/tmp/worktree-cleanup-2026-10-29/`: `MANIFEST.tsv`, `REMOVED.tsv`, `_work/` and the preserved files;
  - `juniper-ml/tmp/release-cascor-0.13.0/eco/README.txt`.
- **Referenced:**
  - `HANDOFF_2026-10-28_…pypi-gate.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md`;
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
