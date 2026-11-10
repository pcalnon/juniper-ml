# Handoff: flood-4 round 1 complete — six carriers merged, 68 census drafts closed; next, the disposition record, then rounds 2 and 3

**Date**: 2026-11-08 (UTC; written 03:30Z)

**Arc**: the Cursor flood-4 consolidation, in session `7ceca543-4d37-4c1d-b2fc-3b49758514af` (named `open-pr-sweep-triaged-owner-rulings-consolidation-next`, worktree `.claude/worktrees/humming-stargazing-papert`). It continued `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md` (the 11-06 handoff), on the owner's "merge approval granted" of 2026-11-07.

**Host**: the Linux host.

**Git status**:

- **This session's worktree** (`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`) is on branch `worktree-humming-stargazing-papert` at `303ccc0b`, which is behind `origin/main`. Nothing is committed; all of the following is UNCOMMITTED:
  - `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, the record draft (§0–§4 and §6–§8 written; §5 and §9 pending; Status/Updated lines to finalize);
  - this file;
  - about 80 `util/ad-hoc/2026-11-07_flood4_*.py` provenance scripts;
  - `tmp/flood4/` (scratch, unversioned): `STATE.txt` (the running log), `OPEN_ITEMS.txt`, the two briefs, `push/<repo>-<carrier>/` (every PR's frozen snapshot, push log and close log), validator findings, and `render_config.json`.
- **This arc's agent worktrees**, under `juniper-ml/.claude/worktrees/`:
  - `agent-a7674bdaf3240b78b` (the ml tests builder) and `agent-ab56f3c71e4f75377` (the ml docs builder) hold their `util/ad-hoc/2026-11-07_flood4_ml_*` scripts, untracked, and `tmp/flood4/ml-{tests,docs}/`: the manifests and the frozen rebase copies.
  - Validators: `agent-a4d5218b39ee8273c`, `agent-aa05f5bd8126623da`, `agent-a80754b707aae7b98`, `agent-adfe0777292754a5c`, `agent-a3c73385122d55e37` and `agent-af5444824ef90bc24`. Each may hold `util/ad-hoc/2026-11-07_flood4_val_*` scripts.
  - The other `agent-*` and named worktrees there are NOT this arc's. Never touch them; `curious-plotting-hummingbird` is DO NOT SWEEP.
- **Centralized worktrees this arc made**, all under `/home/pcalnon/Development/python/Juniper/worktrees/`. Remove them only on the owner's word:
  - `juniper-data--{test,docs}--flood4-consolidated-*--20261107-1701--28078558`;
  - `juniper-canopy--{test,docs}--flood4-consolidated-*--20261107-1700--af650373`;
  - `juniper-ml--val-fidelity-clean-main--20261107-1800--303ccc0b`.
- **The primary checkout** (`/home/pcalnon/Development/python/Juniper/juniper-ml`) is on `main` and behind `origin/main` (12 commits at 03:40Z). Its `util/fleet_triage/predict_merge.py` is the old copy, so run `origin/main`'s. Fast-forward it only on the owner's word; the 11-04 handoff's `git fetch --prune` is still deferred.
- **No local commit was made in this arc.** Every commit went through `util/open_signed_pr.py` or `util/push_signed_commit.py`. Local refs `refs/flood4/pr/<N>` hold the drafts' heads in each repo.

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md. If it is not on origin/main, read it at
/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md
(uncommitted; that worktree also holds the record draft, the provenance scripts and tmp/flood4/STATE.txt).
To work in it, EnterWorktree(path=<that worktree>) once its session has ended (check the lock with
`git worktree list --porcelain`). Run the Verification block first. If an invariant fails, stop, re-derive
it from GitHub and report. New Cursor drafts since 2026-11-08 03:30Z are expected, and are not a failure.

FIRST ask the owner (no approval carries over from the previous session; auto-memory
feedback_headless_merge_approval_policy.md):
1. This session's approval: to merge the record PR (and the round-2 carriers, when they exist), to close the
   drafts they carry, and to update-branch.
2. M-6: scripts/wake_the_claude.bash:259 defaults to `--effort auto`, which the real Claude Code CLI rejects
   ("Unknown --effort value 'auto' -- ignoring it", 2.1.316-2.1.319). What should the default be: a valid
   level, or no flag at all?
3. OI-1 (the owner's own note, 2026-11-07): juniper-ml#2271 shows "Closed with unmerged commits". Its branch
   feat/disable-idle-compress-setting-for-claude-code adds only `"idleCompaction": false` to the repo-root
   settings.local.json, a file Claude Code does not read. Re-land it signed where Claude Code reads it (first
   verify that idleCompaction is a real setting), or delete the remote branch?
4. Whether the consolidation ruling extends to the drafts no ruling covers: juniper-ml #2512-#2515 (opened
   after the second wave's range #2469-#2509 was set), juniper-data #520-#524 and juniper-canopy #798-#801.
   The fleet opened those while our carriers were OPEN, and it will do the same for the record PR.
5. The open defect calls in record sec 4: fix now, file, or leave as documented?
   - the paused-fit wedge (M-3);
   - resume_ok missing broadcasts, both the no-client case and the replay race (M-4, M-7);
   - gitleaks-action's unpaginated commit list (M-1).
   Also, host state: JuniperCanopy1 is stale, and the host's juniper-ci-tools is 0.8.0 against CI's 0.9.1.
6. Worktree cleanup: this arc's (Git status above), and the 11-06 handoff's five, still owed:
   juniper-ml--fix--wake-the-claude-followups--20261104-0331--b22126a4, --fix--wake-the-claude-prompt-guard--
   20261104-0550--b7382bfa, --docs--handoff-2026-11-04-launcher-arc--20261104-1532--1c18106d,
   --feat--launcher-v-follows-claude-claudey-file--20261106-0348--8d553b41 and
   --fix--predict-merge-scratch-alternates--20261106-0707--87181fed. Never use util/remove_stale_worktrees.bash.
The 11-07 grant's own terms: no Cursor draft is merged, retargeted or un-drafted directly; drafts are carried.

Completed so far (round 1 of 3; rulings in the table below):
- juniper-data: #518 (tests) merged as 4f04fc8d and #519 (docs) as 4d8380dd. The 9 census drafts
  (#509-#517) are closed with carrier comments.
- juniper-canopy: #797 (tests) merged as 733b6a3e and #802 (docs) as 63a2f3d7. The 8 census drafts
  (#789-#796) are closed with carrier comments.
- juniper-ml: #2517 (tests) merged as 7bc9d3e2, and its 28 drafts are closed. #2519 (docs, 21 drafts carried)
  merged as 8d73d441, and its 23 drafts are closed. #2424 and #2432, whose Test Suite Reference lines rode in
  #2517, were closed too early, reopened, and closed again after #2519 merged.
- ROUND 1 IS COMPLETE. Of the 74-PR census, only juniper-ml #2360 (another arc) and #2404 / #2406 (round 3)
  are still open.
- Each carrier was validated by independent agents in 2 to 6 rounds before it opened (record sec 2).

Remaining work:
1. (done in the previous session: #2519 merged, its drafts closed)
2. The record PR (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md):
   a. Render sec 5: util/ad-hoc/2026-11-07_flood4_disposition_render.py --config tmp/flood4/render_config.json.
   b. Write sec 9 from the six carriers' file lists.
   c. Set Status/Updated, and the M-6 / OI-1 rulings if given.
   d. Refresh the record's stale text:
      - sec 4's "(pending)" rows: #2519 has merged;
      - sec 2's counts, adding the ml docs rounds 3-6;
      - sec 6 and sec 8 against the then-current facts.
   e. Harvest every util/ad-hoc/2026-11-07_flood4_* script from the worktrees above. That is about 174 copies
      under about 152 names. Where a name occurs in several worktrees, diff the copies and take the builder's
      newest (three differ; agent-adfe0777292754a5c's are older).
   f. Screen the scripts for /tmp literals (owner rule; G-TMP lands with #2360), and run
      util/ad-hoc/2026-10-05_codeql_python_prescreen.py (an unresolved CodeQL thread blocks merge).
   g. Build the record PR's CHANGELOG.md entry on CURRENT main (fetch, then 3-way). Never upload the session
      worktree's 303ccc0b copies. Pass --base-sha as the main sha the files were built from.
      2026-11-07_flood4_signed_push_batches.py refuses an existing branch; for a three-step, use
      util/push_signed_commit.py directly.
   h. Include THIS handoff file in the record PR, so it lands on main.
   i. Validate with independent agents (the record AND the scripts' headers), then open it signed and merge on
      green. Batch the upload: about 155 files. Before every push to an open PR, run
      `gh pr view N --json autoMergeRequest,isDraft`, because the owner's sweeper may arm it.
3. Round 2 (owner, 2026-11-07, "Second wave"): triage the 35 juniper-ml drafts #2469-#2509 against the new
   main, then consolidate them the same way: a tests carrier, a docs carrier, and one code carrier for
   #2480/#2493/#2502/#2504. Known shape, from the 11-06 handoff:
   - follow-ups to #2474: #2476, #2480, #2481, #2484, #2494, #2496. #2480 looks superseded, because main
     already copies .git/shallow. #2484 is stacked on a cursor/ branch: never merge a non-main base.
   - follow-ups to #2468: #2471, #2472, #2478, #2479, #2495, #2503, #2504. For the launcher tests, check what
     the REAL CLI makes of an argv (auto-memory reference_claude_cli_optional_flag_eats_the_prompt.md).
   Ask the owner for round 2's merge approval when its carriers exist.
4. Round 3 (owner, 2026-11-07): consider juniper-ml #2404 and #2406 individually.
5. Archive the next handoff.

Key context:
- Never touch juniper-ml #2360 (armed, DIRTY on purpose; it merges last).
- util/safe_merge.py never checks a PR's base. Read its MERGED line: exit 0 does not mean merged.
- Commits go only through util/open_signed_pr.py or util/push_signed_commit.py (a local commit hangs on the
  YubiKey). Push from a frozen snapshot with util/ad-hoc/2026-11-07_flood4_signed_push_batches.py, which
  refuses any path main changed since the base.
- Every ruleset is strict, and juniper-ml main moves often: four merges landed during this arc.
- A builder or validator agent must never commit or push. They worked in isolated worktrees, and their
  scratch files are .txt/.json only (the doc-link hook scans tmp/ until #2360 lands).
```

---

## The owner's rulings (2026-11-07, this session, verbatim option labels)

| Question | Answer |
|---|---|
| Does the grant cover update-branch and closing carried drafts? | "Merge, update, close (Recommended)" |
| The 35 post-census drafts (#2469–#2509) | "Second wave (Recommended)" |
| #2404 / #2406 | "as a round 3, let's condsider these two draft PRs individually" (the owner's own text) |
| #2271 | Mid-turn note: "Closed with unmerged commits … let's make a note … so it can be addressed when the current tasks are complete" → OI-1 |

The 2026-11-06 rulings in the 11-06 handoff still stand: "Consolidate, incl. post-grant" and "This session, new record".

## Traps

- **A draft split across two carriers.** The tests carrier's manifest also listed docs drafts #2424 and #2432, because their `## Test Suite Reference` lines rode in #2517, so the close script closed them when #2517 merged. Both were reopened with a comment. Close them only after #2519 merges. #2424's claim rides in #2519 via #2426's wording.
- **The signed three-step, as used on #2517 when #2516 merged under it.**
  1. Push `main`'s versions of the conflicting files verbatim (`util/ad-hoc/2026-11-07_flood4_extract_ref_files.py`).
  2. Run `gh api -X PUT …/pulls/N/update-branch -f expected_head_sha=<head>`.
  3. Push the 3-way-merged files, keeping both sides with `main`'s lines first.

  Afterwards, check that the branch tree equals the validated merge-tree. GitHub does NOT resolve a branch-side superset of `main`'s hunks, so pushing the merged files alone leaves the PR `DIRTY`.
- **Validation residue.** Each correction pass introduced new errors: round 2 found a BLOCKER in three of the six carriers. Rounds 3–6 on the ml docs carrier converged only once its version-lineage text was shrunk to per-package first-release facts, read from the published wheels.
- **The Cursor fleet runs on carriers.** A pending `Cursor Automation: Add test coverage` check makes `mergeState` `UNSTABLE`, which is fine when every required context is green. The fleet also opens new drafts about a PR's subjects within minutes of the PR **opening**: data #520–#524 and canopy #798–#801 arrived while our carriers were still open.
- **The isolated session's shell classifier.** It refuses loops, `&&` with a heredoc, `git -C <this repo's checkout>`, and a `grep` pattern containing `git/ref`. Put multi-step logic in a script file. Write/Edit into the primary's `tmp/` is refused, so use this worktree's `tmp/`.
- **Host `TMPDIR`.** Because `TMPDIR` sits inside a checkout, 14 juniper-ml tests fail locally only: 5 regression suites and 9 ci-tools tests. They fail identically on a clean `main` and pass on GitHub.

## Verification (run first; each comment is an invariant)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch -q origin
gh pr view 518 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"#518 \(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 4f04fc8d
gh pr view 519 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"#519 \(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 4d8380dd
gh pr view 797 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"#797 \(.state) \(.mergeCommit.oid[0:8])"' # MERGED 733b6a3e
gh pr view 802 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '"#802 \(.state) \(.mergeCommit.oid[0:8])"' # MERGED 63a2f3d7
gh pr view 2517 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"#2517 \(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 7bc9d3e2
gh pr view 2519 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"#2519 \(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 8d73d441
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json number --jq '[.[].number | select(. <= 2466)] | sort'   # [2360,2404,2406]
gh pr view 2424 --repo pcalnon/juniper-ml --json state --jq .state   # CLOSED (and #2432 likewise)
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json number,autoMergeRequest --jq '"juniper-ml open \(length); armed: \([.[]|select(.autoMergeRequest!=null)|.number])"'   # armed includes 2360
pgrep -af safe_merge.py | grep -v pgrep   # nothing running for a repository you are about to merge in
```

## Documents created or modified in this arc

- **juniper-data#518** (merged), the tests carrier: `CHANGELOG.md` and seven test files under `juniper_data/tests/unit/`:
  - `test_bandit_sarif_upload.py`
  - `test_check_module_coverage.py`
  - `test_run_coverage_gates.py`
  - `test_publish_image_manifest_identity.py`
  - `test_publish_manifest_tag_gates.py`
  - `test_testpypi_install_verify.py`
  - `test_middleware.py`
- **juniper-data#519** (merged), the docs carrier: `CHANGELOG.md`, `docs/{DEVELOPER_CHEATSHEET,DOCUMENTATION_OVERVIEW,QUICK_START,REFERENCE,USER_MANUAL}.md` and `docs/ci_cd/CICD_{MANUAL,QUICK_START,REFERENCE}.md`.
- **juniper-canopy#797** (merged), the tests carrier: `CHANGELOG.md` and four test files:
  - `src/tests/regression/test_bandit_sarif_upload.py`
  - `src/tests/regression/test_codecov_token_upload.py`
  - `src/tests/regression/test_lockfile_regen_empty_payload.py`
  - `src/tests/unit/test_agents_md_date_check.py`
- **juniper-canopy#802** (merged), the docs carrier:
  - `CHANGELOG.md`;
  - `.gitleaks.toml` and `.github/workflows/ci.yml`, comment-only;
  - `docs/ci_cd/CICD_{MANUAL,QUICK_START,REFERENCE,ENVIRONMENT_SETUP}.md`;
  - `docs/{DEVELOPER_CHEATSHEET,QUICK_START,REFERENCE,USER_MANUAL}.md` and `docs/api/API_REFERENCE.md`;
  - `src/tests/regression/test_gitleaks_config.py`, comment-only.
- **juniper-ml#2517** (merged), the tests carrier, 34 paths:
  - `.github/workflows/ci.yml`, `AGENTS.md` (232 suites), `CHANGELOG.md` and `docs/REFERENCE.md` (registrations only);
  - 30 test files under `tests/`, `juniper-service-core/tests/` and `juniper-ci-tools/tests/`. The list is in its PR.
- **juniper-ml#2519** (merged as `8d73d441`), the docs carrier: `CHANGELOG.md`, `docs/{REFERENCE,DEVELOPER_CHEATSHEET_JUNIPER-ML,DOCUMENTATION_OVERVIEW,QUICK_START}.md`, `juniper-config-tools/README.md` and `juniper-service-core/README.md`.
- **Uncommitted, in this session's worktree:**
  - `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (new);
  - this handoff (new);
  - `util/ad-hoc/2026-11-07_flood4_*.py` (new).
