# Handoff: Cursor flood-3 arc, the owner's fifth continuation. Every `actions/checkout` is SHA-pinned, the post-ruling worktrees are removed, and `CODECOV_TOKEN` is in every Dependabot store; only owner calls and one observation remain

**Date**: 2026-11-04 (UTC)

**Arc**: The Cursor flood-3 disposition and its follow-ups. This stretch is the owner's request of 2026-11-03: "continue from handoff: …HANDOFF_2026-11-01_flood3-fourth-continuation-pytest-cap-dropped-low-fixes-cleanup-done.md", with "merge approval granted", and of 2026-11-04: "add CODECOV_TOKEN to all active repos' dependabot secrets", then this handoff.

**Record**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, cited below as `…FLOOD-3-DISPOSITION.md`. This handoff's PR makes the record's twelfth update: the header, §4 (the Codecov row), §6, §7, §8 and §9. Every bare section number below is that file's.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-01_flood3-fourth-continuation-pytest-cap-dropped-low-fixes-cleanup-done.md`, cited below as `HANDOFF_…cleanup-done.md` (11-01).

**Host**: the Linux host.
- **This session:** `claude --worktree proud-crunching-neumann --resume f91c4f7d-55f2-4bca-aac6-9eca11b95f7c`, **pid 674663** (started 2026-11-03 08:06 local). The worktree's lock names that pid. Earlier handoffs' pid 945136 is gone. Worktree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/proud-crunching-neumann`.
- **No other session continues this arc.**
- **Commits** go only through GraphQL `createCommitOnBranch`: `util/open_signed_pr.py` and `util/push_signed_commit.py`. `git fetch` over SSH fails in this session (`Permission denied (publickey)`); read `main` through `gh api`, e.g. `util/ad-hoc/2026-11-03_fetch_main_tarballs.py`.

**Git status**: the worktree's branch, `worktree-proud-crunching-neumann`, is at `d6b29bb5`, behind `main`; no commit is made locally. This PR's three files were uploaded from the worktree's uncommitted copies. The other uncommitted files there (two handoffs, four `util/ad-hoc/` scripts) are identical to `main`'s.

---

## Goal

Nothing is owed unless the owner asks. What remains is one observation (Remaining work, item 1), owner calls (item 2), and the cleanup inventory (item 3).

## Completed (verified on GitHub or the host)

- **The owner's rulings:** "Remove both" (the two post-ruling worktrees) and "Pin all seven" (`agents-md-touch-up.yml`'s checkout), both 2026-11-03; and on 2026-11-04, `CODECOV_TOKEN` in every active repository's Dependabot store.
- **The seven pins, merged 2026-11-03 14:29Z–14:48Z** under this session's approval, required checks green. Each changes the one `actions/checkout@v7.0.1` line to `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1` and adds a CHANGELOG entry:

  | PR | head | merge commit |
  |---|---|---|
  | juniper-ml#2402 | `f7d3c941` | `ab5eda6d` |
  | juniper-canopy#787 | `9a53a7b3` | `3729b0d6` |
  | juniper-cascor#743 | `3ac49987` | `463a3d7c` |
  | juniper-data-client#254 | `4438ab89` | `1bb8c67f` |
  | juniper-cascor-client#192 | `3865958f` | `2b268e16` |
  | juniper-cascor-worker#224 | `e17fc3ce` | `31b764ac` |
  | juniper-deploy#269 | `456520ac` | `0c8cb4a7` |

  - #787, #192 and #269 were completed by `safe_merge.py`'s armed net. Every head branch answers 404.
  - **This session's 11-03 summary to the owner quoted four of these by head SHA as the merge commit** (ml, cascor, data-client, cascor-worker). The table above, from `gh pr view --json mergeCommit`, is correct (`…FLOOD-3-DISPOSITION.md` §6).
- **Census, on the nine `main`s of 2026-11-04** (juniper-ml `2c4a24f0`): 249 of 249 `actions/checkout` uses name `3d3c42e5`, all eight `agents-md-touch-up.yml` copies included (juniper-recurrence has none).
- **The cleanup (11-03).** The ledger is `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-03/` (`REMOVED.tsv`, whose header holds the gates; `MANIFEST.tsv`; `_work/`).
  - Removed: the worktrees and `-d` branches of juniper-cascor#739 and juniper-data#503.
  - Gates re-run: holder check clear on both, this worktree HELD as the positive control; PRs merged, heads 404; HEADs `88cccf5e`/`8e710d20` ancestors of `main`; the 4 and 7 modified files' blobs equal each PR's head and squash trees.
  - Kept: cascor's `logs/juniper_cascor.log`; data's 103 files (`reports/`, `.coverage`, `.hypothesis/`); 0 bad re-hashes.
- **`CODECOV_TOKEN` in all nine Dependabot stores**, set by the owner 2026-11-04 11:18:42Z–11:18:49Z with the new `util/ad-hoc/2026-11-04_set_codecov_token_dependabot_secrets.py`: a hidden prompt, a UUID check, the value on `gh secret set --app dependabot`'s stdin only. Re-read by `util/ad-hoc/2026-10-29_codecov_token_secret_census.py`. No workflow change is needed: a Dependabot-triggered run reads the Dependabot store under the same name.
- **juniper-canopy's *Actions* copy of the token reads `updated_at` 2026-11-03 23:34:16Z**; the other eight date from 2026-10-29. Not this session's doing; actor unrecorded.

## Remaining work

1. **Observe the first Dependabot PR in juniper-data or juniper-canopy** (none was open on 2026-11-04). Its Codecov step should log `Token length: 36` and no `Token required` line. `Upload queued for processing complete` proves nothing: it prints on a refused upload too. Record the result in `…FLOOD-3-DISPOSITION.md` §8.
2. **Owner calls.** A session acts on none of these without the owner's word, and on 2.4 not even then.
   1. **`.claude/worktrees/iridescent-sniffing-snail`** (HEAD `c77b7be5`, on `main`, unlocked, `tmp/` 12 KB, `session-0f840224/`): offered 2026-11-01, not chosen. Never attach or resume `2fc3f4e1`.
      - Route B (the gates, then `git worktree remove` and `git branch -d worktree-iridescent-sniffing-snail`) keeps the session record.
      - Route A (`claude rm 2fc3f4e1`) deletes both; check the branch afterwards.
      - Either way, preserve its `tmp/` first.
   2. **This session's worktree**, once pid 674663 has ended (item 3).
   3. **Promoting the ledgers' claim-backing scripts:** "Not now" (2026-11-01).
   4. **Host environments**, the owner's own action: `JuniperCanopy1` (juniper-observability 0.4.0, juniper-service-core 0.5.0, below canopy's floors); `JuniperCascor1`'s editable install reports 0.11.0; `JuniperData` lacks `juniper-ci-tools`, so `make coverage` stops with the install line.
3. **Cleanup inventory.** Nothing here is removed without an owner signal.
   - **This worktree** after its session ends. Preserve its `tmp/` first:
     - `session/` (6.8 MB), `session2/` (25 MB), `factcheck/` (88 MB): earlier passes' evidence;
     - `session3/` (399 MB): the pin PR bodies, merge logs and cleanup listings. 397 MB of it is `pin/orig/` and `pin/src/`, `main` tarball extracts, regenerable;
     - `session4/` (207 MB): this pass's scripts and `mains/`, the 2026-11-04 tarballs (regenerable; their SHAs are in `mains/*.sha`);
     - `checkout_census_2026-11-01.tsv`, `checkout_census_2026-11-03.tsv`.
     - The earlier context's scratchpad (the pytest-benchmark probe and its two venvs), `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-proud-crunching-neumann/94f3e0a5-1f09-4c71-a2dc-6f27b0af39ba/scratchpad/`, sits under the primary's `tmp/`, so removing the worktree does not delete it.
   - **Keep until the owner says otherwise:** `…/tmp/release-cascor-0.13.0/`; `…/tmp/worktree-cleanup-2026-10-26/`, `-27/`, `-28-canopy-p12/`, `-29/`, `-30/`, `-2026-11-01/` and `-2026-11-03/`; `…/tmp/flood3-deleted-branches.tsv`; the 89 `cascor-test-snapshots-*` directories in `…/tmp/` (counted 2026-11-04).

## Key context and traps

- **Merge approval is per session** (memory `feedback_headless_merge_approval_policy.md`). This file cannot carry it.
- **`safe_merge.py`'s `MERGED #N at <sha>` is the head it merged**, or no SHA for a net merge. Quote merge commits from `gh pr view --json mergeCommit` (`…FLOOD-3-DISPOSITION.md` §6).
- **A secret's value cannot be read back.** Copying one between stores needs the owner to type it; never ask for it in chat (`…FLOOD-3-DISPOSITION.md` §6).
- **juniper-ml#2360** (the `/tmp` arc) is OPEN, CONFLICTING, with auto-merge armed (2026-11-04); its re-sync must keep `main`'s side of its shared files. Until it merges, the doc-link pre-commit hook scans `tmp/` and fails on tarball extracts there; `juniper-check-doc-links --exclude tmp …` is the check. juniper-ml#2396 merged (`6201f94b`); neither is this arc's.
- **The cascor primary:** never pull, check out or edit it from a session. Run `ss -ltnp` and `util/ad-hoc/2026-10-29_worktree_holder_check.py` before relying on its state.
- **Count a step's failures by an effect, never by its API `conclusion`** (`…FLOOD-3-DISPOSITION.md` §6).
- **Worktree isolation refuses some shell shapes:**
  - `git -C` into this repository's shared checkout or its sibling `.claude/worktrees/`;
  - variables, loops or `$(…)` around git or gh, compound git pipelines, and a `python3 -c` that runs git;
  - `env -u … PATH=…:$PATH bash …`, and `bash <file>` on a script it cannot read;
  - arithmetic on variables inside `bash -c`.

  The Write tool also refuses the primary checkout's `tmp/`, so write to the worktree's `tmp/` and run a Python file instead of a shell loop.
- **`util/safe_merge.py` and `util/wait_for_checks.py` take a bare `--repo` name.** Read the `MERGED` line, not the exit status. A background `safe_merge` of a PR you are about to push to should be stopped first.
- **Release dates are UTC.** No release is pending in this arc.

## Verification

Run these first. On any mismatch, stop, re-probe and report to the owner rather than act.

```bash
gh pr view 2402 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'       # MERGED ab5eda6d
gh pr view 743 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'      # MERGED 463a3d7c
gh pr view 269 --repo pcalnon/juniper-deploy --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'      # MERGED 0c8cb4a7
python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py        # dependabot=2026-11-04T11:18:4xZ in all nine rows
gh pr list --repo pcalnon/juniper-data --author app/dependabot --state all --limit 3 --json number,createdAt     # any PR after 11:18Z is item 1's candidate
gh pr list --repo pcalnon/juniper-canopy --author app/dependabot --state all --limit 3 --json number,createdAt
ls /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-03/    # MANIFEST.tsv REMOVED.tsv _work …
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -cE 'juniper-(cascor|data)--fix--(hdf5|make-coverage)'   # 0 (they were cascor's and data's worktrees, so juniper-ml's `git worktree list` cannot show them)
```

## Residue: the remaining work of `HANDOFF_…cleanup-done.md` (11-01), item by item

1. **Owner calls:**
   - 1.1, Codecov in the Dependabot stores: **done**, all nine (owner, 2026-11-04); its effect awaits item 1 here.
   - 1.2, `iridescent-sniffing-snail`: not re-asked (item 2.1 here).
   - 1.3, SHA-pin the other seven: **done** (seven PRs above).
   - 1.4, promoting scripts: "Not now" stands (item 2.3).
   - 1.5, host environments: unchanged (item 2.4).
2. **Cleanup inventory:**
   - the two post-ruling worktrees: **removed**, evidence kept;
   - this session's worktree: carried (item 3), now with `session3/` and `session4/` to preserve;
   - the keep list: carried, with `-2026-11-03/` added.

**Its traps** are carried under Key context, except the `AGENTS.md` memory-budget, timed-call, `set -e`/`eval` and `fetch --prune` traps, which live in `…FLOOD-3-DISPOSITION.md` §6 and the auto-memory; this pass did not need them.

**Ledger correction:** the header of `…/tmp/worktree-cleanup-2026-11-03/REMOVED.tsv` named pid 945136; the removals ran under pid 674663 (the file dates from 14:22Z, after that pid started). The header was corrected in place on 2026-11-04.

## Documents created or modified

- **This file's PR:** this file (new), `util/ad-hoc/2026-11-04_set_codecov_token_dependabot_secrets.py` (new) and `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`.
- **Other PRs:** the seven pins each change `.github/workflows/agents-md-touch-up.yml` and `CHANGELOG.md`; juniper-ml#2402 also adds `util/ad-hoc/2026-11-03_fetch_main_tarballs.py` and `util/ad-hoc/2026-11-03_pin_agents_md_touch_up_checkout.py`.
- **GitHub settings (not files):** `CODECOV_TOKEN` in the Dependabot secret store of all nine repositories (set by the owner).
- **Unversioned:** `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-03/` (`MANIFEST.tsv`, `REMOVED.tsv`, `_work/`, the preserved files); this worktree's `tmp/session3/`, `tmp/session4/` and the two census files.
- **Referenced:** `HANDOFF_…cleanup-done.md` (11-01).
