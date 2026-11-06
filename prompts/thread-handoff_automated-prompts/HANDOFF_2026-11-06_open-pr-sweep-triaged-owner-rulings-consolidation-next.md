# Handoff: the open-PR sweep is triaged and the owner has ruled; next, the consolidated PRs (three repos) and the flood-4 record

**Date**: 2026-11-06 (UTC)

**Arc**: the open-PR sweep and the launcher arc's follow-ups, in session `3323e446-bec4-4448-8f15-a6de7d182e36` (named `launcher-prompt-guard-claudey-defaults-open-pr-sweep-next`). It continued `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-04_launcher-prompt-guard-claudey-defaults-open-pr-sweep-next.md` (cited below as the 11-04 handoff), on the owner's "merge approval granted".

**Host**: the Linux host.

**Git status**:

- **The primary checkout** (`/home/pcalnon/Development/python/Juniper/juniper-ml`) is on `main` and clean, at `87181fed`, 4 behind `origin/main`.
  - The owner moved it there from the key-escrow branch, and another actor fast-forwarded it at 13:20:47Z.
  - Its `util/fleet_triage/predict_merge.py` is therefore the OLD copy. Run `origin/main`'s.
  - Fast-forward it only if the owner asks. The 11-04 handoff's deferred `git fetch --prune` is still deferred.
- **No local commit** was made in this arc.
- **Five worktrees are owed cleanup, each only on the owner's word.** Never use `util/remove_stale_worktrees.bash`.
  - The 11-04 handoff's three: `…--fix--wake-the-claude-followups--20261104-0331--b22126a4`, `…--fix--wake-the-claude-prompt-guard--20261104-0550--b7382bfa` and `…--docs--handoff-2026-11-04-launcher-arc--20261104-1532--1c18106d`. Every file in them is byte-identical to `main`. On 11-06 the owner did not choose to remove them.
  - This arc's two, both PRs merged and both remote branches deleted. All are under `/home/pcalnon/Development/python/Juniper/worktrees/`.
    - `juniper-ml--feat--launcher-v-follows-claude-claudey-file--20261106-0348--8d553b41` (#2468).
    - `juniper-ml--fix--predict-merge-scratch-alternates--20261106-0707--87181fed` (#2474).
  - Checked 2026-11-06 with `git hash-object` against the merge commits' blobs (fc533642 / 827199b6): every changed file matches except two, whose differences are expected.
    - The launcher worktree's `CHANGELOG.md` predates #2482's re-layout.
    - The predict_merge worktree's `docs/REFERENCE.md` is based on an older `main`.
  - Both PRs' own lines are on `main`, and neither worktree has a `tmp/`.

---

## Goal

```text
Continue the open-PR sweep from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md. Read it from origin/main:
  git -C /home/pcalnon/Development/python/Juniper/juniper-ml fetch -q origin && git -C /home/pcalnon/Development/python/Juniper/juniper-ml show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md
If it is not on origin/main yet, the draft is at /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/3323e446-bec4-4448-8f15-a6de7d182e36/scratchpad/sweep/handoff/.
Run its Verification block first. If an invariant fails, stop, re-derive it from GitHub or the repo,
and report before acting. New PRs opened since the census are expected, and are not a failure.

FIRST, ask the owner:
1. For this session's approval to merge, close, update-branch, retarget and un-draft. No approval
   carries over from the previous session or from this document (auto-memory
   feedback_headless_merge_approval_policy.md). The owner's 2026-11-06 RULINGS do carry over; they
   are quoted below.
2. Whether the consolidation ruling extends to the 32 Cursor drafts opened since the 09:45Z census
   (juniper-ml #2469 and later). The ruling covered the census drafts and post-grant #2455-#2466 only.
3. Whether to close #2404 and #2406 as stale. They fold nothing into a carrier: main contradicts
   their claims.

Completed so far:
- Triage of the 74 open PRs at the 09:45Z census: juniper-ml 57, juniper-data 9, juniper-canopy 8.
  The other six repositories had 0, and still do. The reports are under the scratchpad's sweep/triage/
  (paths below).
- Closed on the owner's rulings: juniper-ml#2271 (unsigned commit 85c66d62, so it can never merge),
  #2420 (duplicates #2435 and would revert #2415's fail-closed fix) and #2435 (moot: the P12 cleanup
  is done). Also deleted the local branch feat/enhancements-to-claude-scripts (was 5ae5a5ec).
- juniper-ml#2468 merged as fc533642. -v follows `claude -v` in both launchers; claudey takes
  --file / --path; the default session adds --remote-control; plus the review fixes, and "Closes
  JR-ML-ARCH-263".
- juniper-ml#2474 merged as 827199b6. predict_merge.py borrows the checkout's objects, because the
  primary is shallow, and refuses a history cut by a shallow boundary.

Remaining work (owner's ruling "Consolidate, incl. post-grant"):
1. Write the new record, notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling:
   "This session, new record"). Lay it out like the flood-3 record (§0-§9), and land it through a
   signed PR.
2. For each of juniper-ml, juniper-data and juniper-canopy, build ONE tests carrier and ONE docs
   carrier from the drafts' verified content, fixed where triage found faults (list below).
3. Validate each carrier with independent agents BEFORE opening its PR: open_signed_pr.py opens a
   ready PR, and the owner's sweeper may arm it. Then merge it after green CI, under the new
   session's approval.
4. Only after its carrier merges, close each carried draft, with a comment naming the carrier.
5. Record each disposition in the flood-4 record. Archive the next handoff.

Key context:
- Never touch #2360 (armed, DIRTY on purpose; it merges last), #2497 (the v0.11.4 release notes) or
  #2498 (the P12 plans). All three are armed and belong to other arcs.
- util/safe_merge.py never checks a PR's base. #2484 (base: a cursor/ branch) and canopy#796 (base:
  fix/mnist-declared-params-778) are stacked. Never merge a PR whose base is not main.
- Never delegate a fix to task-executor: it commits locally, which hangs on the YubiKey. Ignore the
  triage reports' task-executor and rebase advice.
- Commits go only through util/open_signed_pr.py or util/push_signed_commit.py.
- Every repository's ruleset is strict, so each merge leaves the rest BEHIND.
```

---

## The owner's rulings (2026-11-06, verbatim option labels from the session transcript)

| Question | Answer |
|---|---|
| Who owns the sweep, and which record? | "This session, new record (Recommended)" |
| `-v` in both launchers | "Both follow Claude Code (Recommended)" |
| A prompt file for claudey | "Add --file / --path (Recommended)" |
| `default_interactive_session_claude_code.bash` | "Add --remote-control (Recommended)" |
| How the sweep lands | "Consolidate, incl. post-grant (Recommended)". Each repo gets one signed tests PR and one signed docs PR, built from the drafts' verified content and fixed where triage found faults. A carried draft is closed, with a comment naming its carrier, only after that carrier merges. The 12 post-grant drafts (#2455–#2466) are covered on the same terms. |
| #2271 | "Close it (Recommended)", **done** |
| #2420 / #2435 | "Close both (Recommended)", **done** |
| Housekeeping (multi-select) | "Close JR-ML-ARCH-263, Fix predict_merge.py, Delete feat/enhancements-…": **all done**. "Remove the 3 arc worktrees" was **not** chosen. |

## What the carriers must contain or fix (from the triage reports)

**juniper-ml (the census drafts still open):**

- **Clean test PRs.** Their tests pass on the merged tree. Most touch one test file, but:
  - #2466 also edits `ci.yml` and `docs/REFERENCE.md` and adds a new suite;
  - #2413 and #2445 each touch two test files.

  The list: #2466, 2419, 2427, 2430, 2436, 2439, 2441, 2443, 2445, 2447, 2451, 2458, 2461, 2463, 2425, 2413, 2414, 2416, 2429, 2431, 2434.
- **The `ci.yml` group:** #2421, #2448, #2459.
- **Fix before carrying:**
  - #2410: its negative-control test fails on the merged tree, because the wheel ships `py.typed` even without the declaration.
  - #2455: six mypy errors, at `test_release_train_exact_caps.py:167-187`.
  - #2403: 5 of its 6 tests fail on merge (10 failures counting subtests). They expect the argv from before #2438.
  - #2407: mypy at `test_claude_interactive.py:435`, and some of its pins predate the new defaults.
- **Stub-argv tests cannot see Claude Code's own parser.** For the launcher tests, ask what the real CLI makes of an argv (auto-memory `reference_claude_cli_optional_flag_eats_the_prompt.md`).
- **Where new tests must be wired:**
  - A new `tests/test_*.py` must go into `ci.yml`'s regression list AND `docs/REFERENCE.md`'s run-all block; `tests/test_ci_test_wiring_drift.py` gates the first.
  - Sub-package tests run in `ci-service-core.yml` / `ci-ci-tools.yml`.
- **Docs cluster: 25 PRs.**
  - Members: #2404, 2406, 2409, 2412, 2417, 2418, 2422, 2424, 2426, 2428, 2432, 2433, 2437, 2440, 2442, 2444, 2446, 2449, 2452, 2456, 2457, 2460, 2462, 2464, 2465.
  - Every simulated pair conflicts. That is 231 of 231, covering the 22 members that simulate cleanly; 25 members would make 300 pairs.
  - They reduce to about 20 distinct true claims.
  - #2457 must be rewritten: recurrence 0.8.1 has been on PyPI since 11-06 09:35Z.
  - #2404 and #2406 fold nothing (Goal question 3).
  - Write the launcher text against `main` after #2468.
  - #2465 says the root `settings.local.json` is never loaded; verify that before carrying it.
  - #2409 and #2422 also edit two sub-package READMEs.
  - The docs carrier lands after the tests carrier, and both edit `docs/REFERENCE.md`.
- **Confirmed pairs:** #2413+#2417, #2416+#2424+#2426, #2419+#2422, #2430+#2433, #2429+#2432, #2431+#2437, #2439+#2446, #2436+#2442+#2443, #2418+#2421 (the drop-in half only), #2409+#2410 (the `py.typed` point only), #2441+#2444, #2445+#2460, #2447+#2449, #2451+#2456, #2458+#2462, #2461+#2464.

**juniper-data (#509–#517, all unchanged since 11-04):**

- **Tests:** #512, 513, 516, 517, and #514. #514 hard-codes `/usr/bin/bash`, which fails on macOS; it pairs with #513.
- **Docs:**
  - #509: never CI-screened; it leaves a stale `setup-python v7.0.0` row.
  - #510.
  - #511: it jumps 0.4.3 → 0.4.8.
  - #515: its `REFERENCE.md` footer still says 0.4.4.
- On conflicting version stamps, keep the higher one.

**juniper-canopy (#789–#796):**

- **Tests:**
  - #789 and #795.
  - #792: GNU-only `base64 -w0`, which fails on macOS.
  - #794: its fixtures commit with the global signing config. Carry it with `-c commit.gpgsign=false` in the fixture, and run it locally with `GIT_CONFIG_GLOBAL=/dev/null`.
- **Docs:**
  - #790: one line over 512 characters (`CICD_MANUAL.md:807`), and it loses the hard breaks on `CICD_QUICK_START.md` lines 3-5.
  - #791: its DAMAGED verdict came from this host's juniper-ci-tools 0.8.0; CI's 0.9.1 gives NEEDS-UPDATE-BRANCH.
  - #793: four lines over 512 characters.
  - #796: stacked on `fix/mnist-declared-params-778`, whose tree equals `main`. Carry its five docs files (+179/−12, probably three long lines); it needs no retarget.
- **Pairs:** #793+#794, #791+#795.

## New arrivals since the 09:45Z census (not triaged; scope is Goal question 2)

As of 14:25Z, 34 new juniper-ml PRs: 32 Cursor drafts and the owner's #2497 / #2498 (both armed, other arcs). The Cursor drafts are #2469–2472, #2475–2481, #2483–2496 and #2499–2504, plus at least one more.

- **Follow-ups to #2474:** #2476, #2480, #2481, #2484 (stacked), #2494, #2496. #2480's fix looks superseded: `main` already copies `.git/shallow` from `--git-common-dir`.
- **Follow-ups to #2468:** #2471, #2472, #2478, #2479, #2495, #2503, #2504.
- **Code fixes that fit neither a tests nor a docs carrier:** #2480, #2493, #2502, #2504.

## Procedure (carried from the 11-04 handoff, adapted to consolidation)

1. **Fetch** each primary. If SSH is refused, use `GIT_TERMINAL_PROMPT=0 git -C <checkout> fetch -q https://github.com/pcalnon/<repo>.git '+refs/heads/*:refs/remotes/origin/*'`, without `--prune`.
2. **Classify each draft's red check before reusing its content:** unscreened, `main`'s failure, platform, or the PR's own (the 11-04 handoff's procedure 3.1). When a diff and its title disagree, believe the diff.
3. **Build each carrier from `origin/main`** in a worktree. Take each draft's file content from its head blob, fix it, and prove the combination with `git merge-tree --write-tree`.
4. **Test on the merged tree:**
   - juniper-ml: `docs/REFERENCE.md`'s command.
   - juniper-data: `conda run -n JuniperData python -m pytest juniper_data/tests/`.
   - juniper-canopy: `conda run -n JuniperCanopy1`, from `src/`, `pytest tests/`.

   Confirm the package imports from the extract, not from an editable install. Delete the extract afterwards: #2360 has not landed, so the doc-link hook scans `tmp/`.
5. **Mutation-check every carried test** against the code it pins. The triage reports ran few mutants.
6. **Validate** with independent agents (auto-memory `feedback_multi_agent_adversarial_validation_sop.md`), then open the carrier with `util/open_signed_pr.py`.
7. **Before any push or update-branch**, run `gh pr view N --json autoMergeRequest,isDraft`. The owner's sweeper arms PRs, so a green carrier may merge on its own. Push only what you would accept on `main`.
8. **Merge.**
   - Check that the base is `main`.
   - Run `gh pr ready` if the PR is a draft.
   - Start `util/safe_merge.py --pr N --repo <repo> --execute` in the background, only when `pgrep -af safe_merge.py` shows none running for that repository.
   - Read its `MERGED` line: exit 0 does not mean merged.
   - Resolve every Cursor review thread first.
9. **Close each carried draft** after its carrier merges, with a comment naming the carrier.

## Traps

- **CHANGELOG: v0.11.4's notes are cut.**
  - juniper-ml#2482 turned `[Unreleased]` into `[0.11.4]`. Every carrier's entry goes under the NEW `[Unreleased]`.
  - An entry written against the old layout can merge CLEANLY into `[0.11.4]`. Check with `git show <merge-tree>:CHANGELOG.md | grep -n '^## \['`.
  - Two carriers that both add to `[Unreleased]` conflict with each other. Merge them one at a time, and give each later one three steps:
    1. Push `CHANGELOG.md` equal to `main`'s, verbatim.
    2. Run the server-side update-branch.
    3. Push the entry under `[Unreleased]`.
  - Prove each step with `git merge-tree --write-tree` on a local probe commit (`git -c commit.gpgsign=false commit-tree`). A probe commit is valid only if its tree is the PR head's tree with just the changed files replaced. The procedure is in auto-memory `reference_changelog_conflict_signed_update_branch.md`; #2468 and #2474 used it.
- **predict_merge.py.** Run `origin/main`'s copy; the primary's is old. It lints only `.py` files, so it cannot see markdownlint's 512-character limit.
- **The juniper-ml primary is shallow.** It has a stray `.git/shallow` entry. A local `git clone --shared` of it carries no `origin/*` heads (auto-memory `reference_shallow_primary_disables_local_clone.md`). Never `fetch --unshallow` or gc it without the owner.
- **gh 2.46.**
  - It has no `gh pr checks --json`.
  - `gh pr edit --body-file` fails; use `gh api -X PATCH repos/pcalnon/<repo>/pulls/N --input <json>`.
  - GraphQL can answer 502 / 504 (it did on 11-06). Retry, and treat a repository missing from a census as unread, not empty.
- **juniper-ci-tools on this host.** `JuniperCascor1` has 0.8.0, older than CI's 0.9.1. 0.8.0 reads a `#` comment inside a code block as a deleted heading. Upgrading the environment is the owner's call.
- **A symbol-loss waiver** goes in a commit body (`Allow-Symbol-Loss: method:<Class>.<name>`), never in PR prose.
- **Temp paths.** Set `TMPDIR` and `GIT_CEILING_DIRECTORIES` to `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp`, and never write under `/tmp`. Use `LC_ALL=C` for `sort` / `comm`: the default collation produced false census diffs.

## Verification (run first; each comment is an invariant, so stop if one fails)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch -q origin
for n in 2468 2474; do gh pr view $n --repo pcalnon/juniper-ml --json state,mergeCommit --jq "\"#$n \(.state) \(.mergeCommit.oid[0:8])\""; done   # MERGED fc533642 / MERGED 827199b6
for n in 2271 2420 2435; do gh pr view $n --repo pcalnon/juniper-ml --json state --jq "\"#$n \(.state)\""; done   # all CLOSED
for r in juniper-ml juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-canopy juniper-deploy juniper-recurrence; do
  gh pr list --repo "pcalnon/$r" --state open --limit 200 --json number,baseRefName,autoMergeRequest \
    --jq "\"$r: \(length) open; base not main: \([.[]|select(.baseRefName!=\"main\")|.number]); armed: \([.[]|select(.autoMergeRequest!=null)|.number])\""; done
# invariants: juniper-ml's armed set INCLUDES 2360 (2497 / 2498 may have merged since); base-not-main is
# [2484] in juniper-ml (plus any newer stacked draft) and [796] in juniper-canopy; the six other
# repositories show 0 open. More juniper-ml PRs than at the census is expected.
pgrep -af safe_merge.py | grep -v pgrep   # nothing running for a repository you are about to merge in
```

## Evidence (unversioned; keep until no longer needed)

Under `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/3323e446-bec4-4448-8f15-a6de7d182e36/scratchpad/sweep/`:

- **The census:** `census_2026-11-06.tsv`, a header plus 74 rows, taken at 09:45Z.
- **The triage reports:** `triage/juniper-ml_supervisor_2026-11-06.txt` and `triage/data_canopy_supervisor_2026-11-06.txt`.
- **The script output:** `triage/<repo>_2026-11-06.json`. The `_ci-tools-0.9.1` variants are the re-runs with CI's checker version.
- **The triage agent's tools:** `tools/`, including the replica builder. It is no longer needed now that #2474 has merged.
- **Mutation and pre-commit logs:** `mutation*.log`, `launcher_precommit_*.log`, `predict_merge_fix/precommit_*.log`, `predict_merge_fix/mutation_vs_21a9dabc.log`.
- **#2468:** `launcher/` (the commit bodies, PR bodies, CHANGELOG candidates and `safe_merge_2468.log`).
- **#2474:** `predict_merge_fix/`, with the same kinds of files.

## Documents created or modified in this arc

- **juniper-ml#2468 (merged):**
  - `scripts/wake_the_claude.bash`
  - `scripts/claude_interactive.bash`
  - `scripts/default_interactive_session_claude_code.bash`
  - `tests/test_wake_the_claude.py`
  - `tests/test_claude_interactive.py`
  - `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
  - `CHANGELOG.md`
- **juniper-ml#2474 (merged):**
  - `util/fleet_triage/predict_merge.py`
  - `tests/test_predict_merge.py`
  - `docs/REFERENCE.md`
  - `.claude/agents/fleet-supervisor.md`
  - `CHANGELOG.md`
- **This handoff's PR:** this file (new).
- **Auto-memory** (unversioned):
  - `reference_shallow_primary_disables_local_clone.md` (new);
  - `reference_changelog_conflict_signed_update_branch.md` (a 2026-11-06 section appended);
  - `MEMORY.md` (one index line).
