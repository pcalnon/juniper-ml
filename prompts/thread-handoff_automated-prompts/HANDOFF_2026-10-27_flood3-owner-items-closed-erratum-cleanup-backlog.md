# Handoff — Cursor flood-3 arc: the owner's three open items closed (0.11.2 erratum, cleanup, §4 backlog); APD-ML-002's cascor half landed

**Date**: 2026-10-27 (UTC)
**Arc**: the Cursor flood-3 disposition (2026-10-08) and its follow-ups. This stretch is the owner's request of 2026-10-26: "let's address the three open items now".
**Record of the arc**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, written `…FLOOD-3-DISPOSITION.md` below. §4 lists the defects, §6 the traps, §7 the tools, §8 the open items and §9 the files. The PR that lands this file makes its seventh update.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_flood3-followups-servers-extras-fixed-juniper-ml-0-11-3-at-pypi-gate.md` (ml#2352), written `HANDOFF_2026-10-26_…gate.md` below. § Residue closes or carries each of its six items.
**Host**: the Linux host, session worktree `.claude/worktrees/enchanted-sniffing-popcorn`. Commits go only through GraphQL `createCommitOnBranch` (`util/open_signed_pr.py`, `util/push_signed_commit.py`); a local `git commit` hangs on the YubiKey.

---

## Goal

Nothing is owed unless the owner asks. The arc's own work is done; what remains is the owner's (Remaining work). The owner's request, verbatim: "let's address the three open items now". Their rulings (2026-10-26):
- merges: "Yes, all of them";
- erratum: "0.11.2 + 0.11.3";
- remote branches: "Delete flood-3's only";
- backlog: "Fix all; rule on APD-ML-002";
- APD-ML-002: "A now, test later", "Keep test_accuracy via cascor", "Add --reaggregate", and for a non-finite band value "Fix in the same PR".

## Completed (verified on `main`, GitHub or PyPI)

- **The 0.11.2 erratum.** juniper-ml#2362 (`682e72fb`) corrects the Priority line of `notes/releases/RELEASE_NOTES_v0.11.2.md` in place, adds a dated erratum, and adds one clarifying sentence to `RELEASE_NOTES_v0.11.3.md`. It is archive-only, with an `Allow-Archive-Edit` trailer; the trailer is on `main`'s squash. juniper-ml#2363 (`40815bb4`) carries `CHANGELOG.md`, the PyPI probe (9/9 PASS) and the apply script, whose `--check` reports nothing owed on `main`. The Release v0.11.2 and v0.11.3 bodies equal the archives under `diff -B`. No publish run fired, and v0.11.3 is still the latest.
- **The cleanup.** 33 worktrees removed (juniper-ml 24, juniper-data 3, juniper-cascor 3, canopy, recurrence and deploy one each) and 11 local branches deleted, each inspected first (`…FLOOD-3-DISPOSITION.md` §6). 37 files that never existed on `main`, plus one canopy test log, are in juniper-ml's gitignored `tmp/worktree-cleanup-2026-10-26/` with `MANIFEST.tsv`. 89 remote `cursor/*` heads of closed, unmerged flood-3 PRs deleted; each ref and SHA is in `tmp/flood3-deleted-branches.tsv`.
- **The backlog**, one PR per repo, all merged: juniper-cascor#730 (`2dda53e1`), juniper-deploy#265 (`fd8614cc`), juniper-recurrence#226 (`f3e13d43`), juniper-data#498 (`32bd375e`), juniper-cascor-worker#218 (`2926653a`), juniper-data-client#248 (`090f292e`), juniper-cascor-client#188 (`6d0b0aa2`), juniper-canopy#775 (`42fe6eed`) and juniper-ml#2366 (`22e4a4b9`). §4 records each row.
- **The fork-drift guard.** juniper-ml#2365 (`4db48592`) files `APD-ECO-015` (found already fixed) and adds the `ast`-scoped `throttle-check-never-inserts` guard.
- **APD-ML-002, cascor half.** juniper-ml#2369 (option A, `--reaggregate`, a non-finite value fails a band) and juniper-cascor#731 (`752a797f`: cascor's final evaluation computes `accuracy`, using the network's own `_accuracy`).

## Remaining work (the owner's)

1. **A juniper-cascor release** to ship juniper-cascor#731. Until one ships, `test_accuracy` has no source. The release train's traps are in memory `reference_release_train_ceremony_traps_2026-09-09.md`.
2. **ml#2064**: carry the labelled final block into `stats.json`, so `test_*` columns, including `test_accuracy` when the block reads `test`, can be emitted (the owner's "test later", option C). It follows juniper-ml#2369.
3. **The open §4 rows** of `…FLOOD-3-DISPOSITION.md`, all found on 2026-10-26 except where noted:
   - juniper-cascor: `src/tests/test_memory_budget_check.py`'s 40 tests never run in CI (open).
   - juniper-data: `docs/REFERENCE.md`'s workflow table lists 10 of the 14 workflows (open, low).
   - juniper-ml: `docs/REFERENCE.md` § Canopy E2E Topology Driver's stale #1672 subsection and Yahoo line (open, low).
   - juniper-ml: `tests/test_replay_redrive_stack_refusal.py` fails 13 tests locally under the repo-`tmp/` convention; CI passes (open, low).
   - Two unverified leads, not rows: juniper-data's `ci.yml` reads `secrets.CODECOV_TOKEN`, which is not a repository secret; juniper-cascor's `Bandit` upload step may fail while `Bandit` is required.
4. **Cleanup of this pass** (an owner signal is needed; see the inventory).

## Cleanup inventory (this pass)

- **Centralized worktrees** under `/home/pcalnon/Development/python/Juniper/worktrees/`, all detached, every edit landed through the PRs above:
  - `juniper-ml--docs--release-notes-erratum--20261026-1706--a829804b`, `juniper-ml--fix--flood3-backlog--20261026-1710--a829804b`, `juniper-ml--test--throttle-fork-drift-guard--20261026-1711--a829804b`, `juniper-ml--fix--apd-ml-002-cascor-headline--20261026-1753--40815bb4`;
  - `juniper-cascor--fix--flood3-backlog--20261026-1707--2ec3bf31`, `juniper-cascor--feat--final-eval-accuracy--20261026-1754--5b7d10dc`;
  - `juniper-data--fix--flood3-backlog--20261026-1708--97c5aeb8`, `juniper-data-client--fix--flood3-backlog--20261026-1709--66206a3c`, `juniper-cascor-client--fix--flood3-backlog--20261026-1709--c69e1bba`, `juniper-cascor-worker--fix--flood3-backlog--20261026-1709--fd1f95b4`;
  - `juniper-canopy--fix--flood3-backlog--20261026-1709--da08414f`, `juniper-deploy--fix--flood3-backlog--20261026-1709--0d9c71f6`, `juniper-recurrence--fix--flood3-backlog--20261026-1709--23a8691f`.
- **Lane worktrees** `.claude/worktrees/agent-a8c2032598839af1f`, `agent-ada970590dd993c97`, `agent-ac7214da19240fe4d` (branches `worktree-agent-<id>`). Their only unique files were the six `util/ad-hoc/2026-10-26_flood3_*` instruments, which this file's PR commits.
- **This session's worktree** `.claude/worktrees/enchanted-sniffing-popcorn` is locked while the session lives. Afterwards: `git worktree unlock` if still locked, `git worktree remove --force`, then `git branch -d worktree-enchanted-sniffing-popcorn` (its head `2a69b817` is on `main`). Its modified record copy is old: never upload it.
- **Keep until the owner says otherwise:** `juniper-ml/tmp/worktree-cleanup-2026-10-26/` and `juniper-ml/tmp/flood3-deleted-branches.tsv`.
- Inspect before forcing: use `util/ad-hoc/2026-10-26_worktree_blob_classify.py` where `cd` is refused (`…FLOOD-3-DISPOSITION.md` §6).

## Key context and traps

- **Merge approval** is per session: the owner's 2026-10-26 grant covered this pass's PRs only (memory `feedback_headless_merge_approval_policy.md`). Never approve a `pypi` gate from a session.
- **Making a swallowed failure loud can redden a test leg** that passed only because of it: the base64 fix and juniper-data's macOS leg (§6; memory `reference_making_a_silent_failure_loud_breaks_tests_that_relied_on_it.md`).
- **`safe_merge.py`** ended twice without merging (a GraphQL "Something went wrong"; canopy's CI outlasting 3000 s). Read its `MERGED` line; a re-run fixed both.
- **`JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`** from a centralized worktree checks the lagging primaries.
- **`/tmp`**: this session started before the 2026-10-26 hook, so Claude Code's own task output went to `/tmp/claude-1000/`; every file the session wrote went to a repo `tmp/`. A new session should have `TMPDIR` and `CLAUDE_CODE_TMPDIR` set; check with `printenv TMPDIR CLAUDE_CODE_TMPDIR`.
- **Worktree-isolated command limits** (refusals vary by session): avoid `$(…)`, loops and inline Python that mention git; prefer plain single commands and the Write tool.

## Verification

```bash
git fetch origin
git log --oneline -8 origin/main
gh pr view 2362 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'   # MERGED 682e72fb…
gh pr view 2363 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'   # MERGED 40815bb4…
gh pr view 2365 --repo pcalnon/juniper-ml --json state --jq .state   # MERGED
gh pr view 2366 --repo pcalnon/juniper-ml --json state --jq .state   # MERGED
gh pr view 2369 --repo pcalnon/juniper-ml --json state --jq .state   # MERGED (APD-ML-002, cascor half)
gh pr view 731 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'   # MERGED 752a797f…
python3 -I util/ad-hoc/2026-10-26_erratum_0_11_x_security_floor_probe.py   # 9 PASS, exit 0
gh release view v0.11.2 --repo pcalnon/juniper-ml --json body --jq .body | grep -c 'Erratum (2026-10-26)'   # 1
python3 -I util/ad-hoc/2026-10-27_flood3_record_seventh_update.py notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md --check   # OK nothing owed
```

## Residue: the six items of `HANDOFF_2026-10-26_…gate.md`

1. **The 0.11.3 `pypi` gate**: closed. The owner approved it; 0.11.3 has been on PyPI since 2026-10-26 17:48Z.
2. **After it publishes**: closed by juniper-ml#2358 (the record's sixth update; the differential wheel check against the published wheel).
3. **The backlog**: closed by this pass, except the rows found while closing it (Remaining work, item 3) and `test_accuracy` (items 1-2).
4. **Cleanup**: closed by this pass; this pass's own inventory replaces it.
5. **The erratum**: closed (juniper-ml#2362, #2363, the Release bodies).
6. **Not this arc's** (the recurrence arc's owner items): unchanged; that arc recorded 0.11.3 in its plans by juniper-ml#2359.

## Documents created or modified

- This file's PR: this file (new); `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (header, §4, §6, §7, §8, §9); new `util/ad-hoc/2026-10-26_flood3_delete_closed_pr_branches.py`, `util/ad-hoc/2026-10-26_worktree_blob_classify.py`, `util/ad-hoc/2026-10-26_worktree_preserve_unique.py`, `util/ad-hoc/2026-10-27_flood3_record_seventh_update.py`, and the lanes' six `util/ad-hoc/2026-10-26_flood3_*` instruments.
- The other PRs' files are listed in `…FLOOD-3-DISPOSITION.md` §9.
- Unversioned, on this host: memory files `project_worktree_branch_cleanup_playbook.md`, `reference_safe_merge_exits_zero_without_merging.md`, `reference_verification_discipline_hub.md`, `project_juniper_data_registry_needs_api_extra.md`, and the new `reference_making_a_silent_failure_loud_breaks_tests_that_relied_on_it.md`.
- Referenced: `HANDOFF_2026-10-26_…gate.md`; `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (`APD-ML-002`, `APD-ECO-015`, `APD-ML-008`); `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
