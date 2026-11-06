# Handoff: launcher arc. The prompt goes after `--` and claudey's defaults are in (juniper-ml#2405, #2438); next, the sweep of every open PR in the nine repositories

**Date**: 2026-11-04 (UTC)

**Arc**: the `scripts/wake_the_claude.bash` / `claudey` launcher arc, in session `856140dc-d1b5-46cb-b0d6-7163d63ded7b`. It began with the owner's request to fix and merge juniper-ml#2396, then took up the follow-ups juniper-ml#2405 reported. On 2026-11-04 the owner ruled:

- "merge approval granted for all work arc PRs including #2405";
- "let's fix the prompt issue …";
- "the -u flag should display the usage function and exit with a non-zero (failing) exit code … let the version flag match only the claude-version flag";
- when asked about remote control together with skipped permissions: "Keep both on".

**Predecessor**: none archived. The arc started in this session.

**Host**: the Linux host.

**Git status**:

- The primary checkout `/home/pcalnon/Development/python/Juniper/juniper-ml` is on `main`, clean, at `b22126a4`, behind `origin/main`. This session pulled it once, to `6201f94b`, at the owner's request. Other actors have moved it since.
- No local commit was made in this arc. The arc's own commits are GitHub-signed `createCommitOnBranch` commits. `b7382bfa` and `98fc8b2b` are merge commits from `update-branch`, made by GitHub.
- The arc's three worktrees are listed under A4.

---

## Goal

```text
Continue from the handoff juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-04_launcher-prompt-guard-claudey-defaults-open-pr-sweep-next.md. The primary checkout is
behind, so read it from origin/main:
  git -C /home/pcalnon/Development/python/Juniper/juniper-ml fetch -q origin && git -C /home/pcalnon/Development/python/Juniper/juniper-ml show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-04_launcher-prompt-guard-claudey-defaults-open-pr-sweep-next.md
Until its PR merges, the same file is at /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/856140dc-d1b5-46cb-b0d6-7163d63ded7b/scratchpad/followups/handoff/.

Completed so far:
- juniper-ml#2396 merged (6201f94b), after this session's repair commit b7e3312c.
- juniper-ml#2405 merged (db131f7b): wake_the_claude.bash's -v sets its own version, the nohup-log and
  claude-not-found errors print with debug off, and LauncherScriptVariableTests was added.
- juniper-ml#2438 merged (1c18106d, 2026-11-04T21:31:17Z; main-verify run 41916861704 succeeded): the
  owner's 2026-11-04 rulings, plus two Cursor review findings.
  wake_the_claude.bash:
  - sends the prompt last, after "--", whichever flag supplied it;
  - the word after a prompt flag is the prompt, whatever it starts with;
  - --remote-control goes bare and refuses a value;
  - --version, -V and --claude-version report Claude Code's version; -v / --script-version the
    script's;
  - -u exits 1;
  - an empty or unreadable prompt file stops the launch.
  claude_interactive.bash (claudey):
  - worktree and remote control are on by default, both bare; --no-worktree / --no-remote-control turn
    them off;
  - -w's name is optional;
  - a flag missing its value exits 1 instead of looping forever.

Remaining work:
- A. This arc:
  - ask the owner the four A2 questions;
  - bring the owner a proposal for each of the five Cursor launcher drafts (#2403, #2404, #2406, #2407,
    #2440);
  - propose JR-ML-ARCH-263's status change (A5);
  - clean up the three worktrees and branches, but only on the owner's word (A4).
- B. Every open PR in the nine repositories: 58 at 21:14Z (juniper-ml 41, juniper-data 9,
  juniper-canopy 8, none elsewhere), 55 of them Cursor drafts, all opened 2026-11-04. No session owns
  this batch. Ask the owner how to record it, triage read-only (B2), then evaluate, fix and test.
  Every merge, close, retarget or update-branch needs the owner's explicit approval, per PR or named
  group.

Key context:
- No approval carries over from this session or this document (auto-memory
  feedback_headless_merge_approval_policy.md).
- ARMED: juniper-ml#2360 (DIRTY on purpose) and #2271 (BEHIND). Making either mergeable merges it.
  Never resolve, update or disarm either without the owner.
- util/safe_merge.py never checks a PR's base branch. canopy#796's base is
  fix/mnist-declared-params-778 (its PR, canopy#788, merged, but the branch still exists). Merging #796
  would put it into that dead branch, with no checks. Never merge a PR whose base is not main.
- Commits only through util/open_signed_pr.py (a new branch) or util/push_signed_commit.py (an existing
  branch, --expected-head <full 40-character SHA>). A local `git commit` hangs on the YubiKey in a
  headless session.
- Verification has invariants. If one fails, stop, re-derive it from GitHub or the repo, and report
  before acting. PRs opened after 21:14Z are expected, and are not a failure.
```

---

## Completed (verified on GitHub)

| PR | Merge commit | What it did | Evidence |
|---|---|---|---|
| juniper-ml#2396 (the owner's branch `feat/enhancements-to-claude-scripts`) | `6201f94b` | The launcher parser rewrite. This session's commit `b7e3312c` repaired its regression suites. | It merged from head `e3824ed7`, on the owner's approval for #2396 alone. |
| juniper-ml#2405 | `db131f7b` (2026-11-04T12:03:38Z) | <ul><li>`SCRIPT_VERSION="1.0.0"`, which no inherited value overrides.</li><li>`--remote-control <name>` restored. #2438 removed it again.</li><li>The nohup-log and claude-not-found errors print to stderr.</li><li>`PROMPT_FILE_DEFAULT` / `PROMPT_PATH_DEFAULT` deleted.</li><li>6 tests added, among them `LauncherScriptVariableTests`.</li></ul> | `safe_merge.py` printed `MERGED #2405 at b7382bfa via squash`. `b7382bfa` is the verified head, not the squash commit. |
| juniper-ml#2438 | `1c18106d` (2026-11-04T21:31:17Z, from the verified head `98fc8b2b`) | The 2026-11-04 rulings and the two review findings. Its PR body has the before/after table. | <ul><li>Commits `8711c41d` and `9b390d74`, both GitHub-verified.</li><li>107 tests pass on the head and on `main`.</li><li>Against #2405's scripts, 45 of the 107 fail, all 17 new or rewritten tests among them.</li><li>The three tests for the review fix also fail against `8711c41d`.</li><li>Pre-commit: for the second commit, the final pass's log shows exit 0. The first commit's passing re-run was not logged. CI's Pre-commit jobs passed on both heads.</li><li>CodeQL prescreen: 0 alerts.</li><li>Symbol-loss: one LOST finding, the renamed remote-control test, waived by `Allow-Symbol-Loss` in both commits. The waiver appears twice, mid-message, in the squash body.</li><li>`main-verify` run `41916861704`: success.</li></ul> |

**#2438's review.** Two Cursor threads (2026-11-04 12:19Z) blocked the first merge. `safe_merge.py` refused with "2 unresolved review thread(s)" and disarmed.

- **The `--prompt` thread:** a value starting with `--` was parsed as a flag, so `--prompt --dangerously-skip-permissions` injected that flag. Fixed in `9b390d74`.
- **The remote-control thread:** it was about remote control combined with the `--dangerously-skip-permissions` that claudey's shipped `DEBUG=TRUE` adds. The owner answered "Keep both on", and the reply cites that ruling.

Both threads are resolved.

**How the prompt bug was established.**

- `claude --help` (2.1.318) declares `-w, --worktree [name]`, `--remote-control [name]`, `-r, --resume [value]` and `-v, --version`.
- commander 15.0.0 (`~/.npm/_npx/10f54a790ecaa614/node_modules/commander`), given those declarations, parses `["--worktree","hello"]` as `worktree:"hello"` with no prompt. `["--worktree","--","hello"]` gives `worktree:true` and the prompt `"hello"`.
- On the real binary, `claude '---name: x' --bogus-zzz` fails with `error: unknown option '---name: x'`.
- The suites' stub `claude` records argv, so it cannot see these failures. The tests pin the `--`. The probe is `promptfix/commander_probe.js` (listed under Evidence).

---

## Remaining work

### A. This arc

1. **#2438 on `main`: done at handoff.** Verification confirms it. If the launcher suites (Verification step 2) fail on a later `main`, the cause is new.
2. **Ask the owner.** #2438 decides none of these, so do nothing without the answers.
   1. **`-v`.** It still prints wake_the_claude.bash's own version, the minimal reading of "a script-version specific flag". Claude Code's CLI uses `-v, --version` for its version. Should `-v` follow `--version`? That means moving `-v` from `SCRIPT_VERSION_FLAGS` to `MODEL_VERSION_FLAGS` in `scripts/wake_the_claude.bash`. Removing it from one list alone makes `-v` exit 1, and `test_no_input_flag_selects_two_parsers` forbids a flag in both. The two tests that use `-v` change too.
   2. **claudey's own `-v` / `--version`.** They print claudey's version (`0.1.1`). Should the "`--version` is Claude Code's" ruling apply to claudey too?
   3. **A prompt file for claudey.** It has none: its parser rejects any argument it does not know. Should it gain `--file` / `--path`? If it does, it must stop sending its default `--prompt` alongside them, because wake_the_claude.bash prefers `--prompt` over a file.
   4. **`default_interactive_session_claude_code.bash`.** It sends a bare `--worktree` but no `--remote-control`. Should it match claudey's new defaults?
3. **The Cursor launcher drafts.** All five touch files #2438 changed. Bring the owner a keep, update or close proposal for each, with the overlap evidence. Close only when the owner confirms that PR: `.claude/agents/fleet-supervisor.md` § Two-key DUP-CLOSE rule ("a false close = LOST REAL WORK").

   | PR | Branched from | Note |
   |---|---|---|
   | #2403 (`tests/test_wake_the_claude.py`) | `b22126a4` | On `main` now, 4 of its tests fail (10 counting subtests), all because the `--` is missing. |
   | #2404 (cheatsheet after #2396) | `b22126a4` | Conflicts with #2438's rewrite of the launcher table in `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`. |
   | #2406 (docs for the #2405 items) | stacked on `fix/wake-the-claude-followups` until 12:03Z, now `main` | It carries `87bbfbdf`, #2405's own pre-squash commit, which causes its `CHANGELOG.md` and `scripts/wake_the_claude.bash` conflicts. Its real content is Cursor's `33a1fac7`, touching four docs files (`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/REFERENCE.md`, `docs/QUICK_START.md`, `docs/DOCUMENTATION_OVERVIEW.md`). **CI has never run on it against `main`**: only the Base-Branch Guard reported. |
   | #2407 (`tests/test_claude_interactive.py`) | `b22126a4` | Conflicts with #2438. Some of its pins predate the on-by-default worktree and remote control. |
   | #2440 (docs: claudey defaults, prompt after `--`, version flags) | stacked on `fix/wake-the-claude-prompt-guard`; retargeted to `main` at 21:31:20Z | DIRTY. Head `a96e4916`. It carries `8711c41d`, so it conflicts in `CHANGELOG.md`, the cheatsheet, `scripts/wake_the_claude.bash` and both launcher test files. |

4. **Cleanup, on the owner's word only.** Never run `util/remove_stale_worktrees.bash`.
   - **Worktree** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--fix--wake-the-claude-followups--20261104-0331--b22126a4`.
     - Branch `fix/wake-the-claude-followups` (#2405, merged; its remote branch is deleted).
     - Clean, with no `tmp/`.
     - Remove with `git worktree remove <path> && git worktree prune && git branch -D fix/wake-the-claude-followups`.
   - **Worktree** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--fix--wake-the-claude-prompt-guard--20261104-0550--b7382bfa`.
     - Branch `fix/wake-the-claude-prompt-guard`, at `b7382bfa`.
     - It holds #2438's six files as uncommitted changes, and `tmp/` is empty.
     - First confirm each changed file's `git hash-object` equals `git rev-parse 1c18106d:<path>`. Then `git worktree remove --force <path> && git worktree prune && git branch -D fix/wake-the-claude-prompt-guard`.
   - **Worktree** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--docs--handoff-2026-11-04-launcher-arc--20261104-1532--1c18106d`.
     - Branch `docs/handoff-2026-11-04-launcher-arc`, where this handoff was checked before upload. Remove it once its PR has merged.
   - **Local branch** `feat/enhancements-to-claude-scripts`, at `5ae5a5ec`, #2396's pre-repair tip. The owner deferred deleting it and running `git fetch --prune` (2026-11-03 22:52Z: "let's defer the branch cleanup for now").
   - **The primary checkout**: fast-forward it only if the owner asks.
5. **JR-ML-ARCH-263** (`notes/requirements/by-area/ARCH.md`).
   - Its source is HSK-21 in `notes/development/JUNIPER_2026-04-23_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V6-REMEDIATION-ANALYSIS.md`, lines 3201-3215: the `# TODO: this isn't going to stderr?????` comment.
   - `599bf93c` removed that comment on 2026-06-14 (01:28Z). #2438 does not touch it.
   - Propose the status change to the owner.

### B. Every open PR in the nine repositories

**The census.** It was taken at 21:14Z with `gh pr list` in each repository, and is saved as `open_prs_2026-11-04_round2.tsv`. That file has a header row and records each PR's base and arm state.

- juniper-cascor, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy and juniper-recurrence had no open PRs.
- More Cursor drafts kept arriving afterwards (#2447 at 21:25Z). By 21:49Z, juniper-ml had 43 open PRs, 41 of them drafts.
- No session owns the batch. The flood-3 arc is complete: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` says every one of its 116 drafts was merged or closed. Its last handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-04_flood3-fifth-continuation-checkout-pinned-everywhere-codecov-dependabot-set.md`, says "No other session continues this arc", and its session has ended.

**Ready PRs (juniper-ml):**

| PR | State | Disposition |
|---|---|---|
| #2360 (the repo `tmp/` convention; +3057/−122, 43 files) | ARMED since 2026-10-27; DIRTY (conflicts with `main` in `.github/workflows/ci.yml`, `CHANGELOG.md`, `docs/REFERENCE.md`) | Belongs to the canopy E2E arc. It stays DIRTY on purpose until canopy E2E Phase 16 lands and its baseline is regenerated. The auto-memory `project_canopy_e2e_validation_arc_2026-08-08.md` says: "#2360 last, after Phase 16 lands + its baseline regenerated". A conflict fix would let the armed net merge it. Never resolve, update or disarm it. |
| #2271 (`idleCompaction` local setting, +1) | ARMED since 2026-10-19, every check green, BEHIND | Under the `strict` ruleset, an armed PR that is BEHIND waits forever, and an `update-branch` merges it. Ask the owner. |

juniper-ml#2415 (`0368c3a2`) and #2423 (`834e79aa`) merged after the first census, taken at 12:14Z.

**Cursor drafts (55 at 21:14Z, all `app/cursor`, all opened 2026-11-04):**

- **juniper-ml (38):** #2403, #2404, #2406, #2407, #2409, #2410, #2412–#2414, #2416–#2422, #2424–#2437, #2439–#2446. #2447 and later arrived after the census.
- **juniper-data (9):** #509–#517.
- **juniper-canopy (8):** #789–#796.

**Checks at the first census.** 14 drafts showed a red check:

- juniper-ml: #2404, #2406, #2407, #2410, #2416, #2417, #2420, #2435
- juniper-data: #509, #514
- juniper-canopy: #790, #792, #793, #796

Two caveats:

- **No CI run at all.** ml#2406, data#509 and ml#2435 were opened stacked and only later retargeted to `main` (12:03Z, 09:59Z and 14:24Z). Their only check is the Base-Branch Guard, which failed and then passed. Treat them as unscreened, not green.
- **Still stacked.** canopy#796 is still stacked.

**Groupings to confirm in triage:**

- **#2420 and #2435** share the title "fix(ad-hoc): keep P12 worktree cleanup from deleting uncommitted files".
  - Both carry commits from #2415, which has since merged as a squash. #2420 carries only `34a1d92d`. #2435 carries all four, and its copy matches `main`.
  - Both are DIRTY in `util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash` and the P12 plan. On `main`, `07031df2` makes that check fail closed.
  - Resolving a conflict toward #2420's side would therefore revert #2415's fix. Resolve toward `main`, and re-apply only the Cursor hunks.
- **Test / doc pairs on one finding** (the validators checked these):
  - #2413 + #2417: zero score and zero theta.
  - #2416 + #2424 + #2426: G-SEC `getblockall`.
  - #2419 + #2422: the failed-auth cap.
  - #2430 + #2433: the connection bucket.
  - #2429 + #2432: `stats.json`.
  - #2431 + #2437: a failed snapshot save.
  - #2418 + #2421: the Phase D trial drop-in.
  - #2410 + #2409: `py.typed`.
  - canopy#793 + #794: the AGENTS.md date check.
  - canopy#791 + #795: the Codecov token.
- **Likely pairs, matched by title only** (drafts opened after 12:19Z): #2442 + #2443 (worker anomaly warning), #2439 + #2446 (control channel). #2441, #2444 and #2445 (replay, training resume) may also pair.
- **The docs cluster:**
  - Seventeen docs drafts each touch the same four files: `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md`. They are #2404, #2406, #2409, #2412, #2417, #2418, #2422, #2424, #2426, #2428, #2432, #2433, #2437, #2440, #2442, #2444 and #2446.
  - All 136 pairs conflict.
  - §8 of the flood-3 record makes consolidation the default for such a cluster. Propose one consolidated signed PR to the owner.

**Procedure:**

1. **Ownership.** No session owns the batch. Ask the owner whether its dispositions go into the flood-3 record's next update or into a new record. If another live session turns out to claim it (check `ListAgents` and the owner's word), yield.
2. **Triage (read-only).** Nothing here writes to GitHub.
   - **Fetch** in each primary checkout: `git -C /home/pcalnon/Development/python/Juniper/<repo> fetch -q origin`. If SSH is refused, use `GIT_TERMINAL_PROMPT=0 git -C <that checkout> fetch -q https://github.com/pcalnon/<repo>.git '+refs/heads/*:refs/remotes/origin/*'`, without `--prune`.
   - **Script verdicts.** From the juniper-ml checkout, run `python3 util/fleet_triage/predict_merge.py --batch --json --repo-root /home/pcalnon/Development/python/Juniper/<repo>`. It returns a verdict per PR (MERGE-CLEAN, NEEDS-UPDATE-BRANCH, DAMAGED-FIX-FIRST or CONFLICT), a cluster map and a suggested order. It never judges duplicates. Treat an ERROR or a skip as unscreened.
   - **Duplicate and supersession calls** come from the `fleet-supervisor` agent (`.claude/agents/fleet-supervisor.md`). The owner confirms them under the two-key rule. Use the agent for verdicts only, and never let it delegate a fix to `task-executor`: that agent commits locally, which hangs on the YubiKey here.
3. **Each PR.**
   1. **Classify a red check before fixing.**
      - Run `gh pr checks N --repo pcalnon/<repo> --required` and read the latest run of each check.
      - Only the Base-Branch Guard reported: the PR is unscreened, because it was stacked when CI would have run.
      - The same job is red on `main` (`gh run list --repo pcalnon/<repo> --branch main --workflow '<workflow file>' --limit 5`): it is `main`'s failure.
      - CANCELLED, no runner, or "change detection did not succeed" on a head that was green: it is the platform. Check githubstatus, then rerun.
      - Anything else is the PR's own failure.
   2. **Check the claim against the code, not the title.** When the diff and the title disagree, the diff wins.
   3. **Test on the merged tree.**
      - Run `git -C <checkout> merge-tree --write-tree origin/main <head-sha>`. If it exits non-zero, stop: the tree holds conflict markers.
      - Otherwise extract the tree id from its first line with `git -C <checkout> archive <tree> | tar -x -C "$TMPDIR/<new-dir>"`. Set `TMPDIR` and `GIT_CEILING_DIRECTORIES` to `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp`.
      - Test juniper-data in the `JuniperData` conda environment (`pytest juniper_data/tests/`), juniper-canopy in `JuniperCanopy1` (`cd src && pytest tests/ -v`), and juniper-ml with the command `docs/REFERENCE.md` gives.
      - Confirm the package imports from the extract (`<pkg>.__file__`), not from an editable install.
      - Delete the extract afterwards. Until #2360 lands, juniper-ml's doc-link hook scans `tmp/`.
   4. **Mutation-check every new test** against the code it pins.
   5. **Before any push or update-branch**, run `gh pr view N --repo pcalnon/<repo> --json autoMergeRequest,isDraft`, and stop if the PR is armed. The owner's sweeper un-drafts and arms PRs, and its merges are intended (auto-memory `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`). A fix that turns a draft green can therefore merge it, so push only what you would accept on `main`. An update-branch (`gh api -X PUT repos/pcalnon/<repo>/pulls/N/update-branch`) also starts CI. It is never a rebase, because a rebase re-creates the commits unsigned. Get the owner's go-ahead before running it across the batch.
   6. **Push fixes forward** with `python3 util/push_signed_commit.py --repo <repo> --branch <head-branch> --expected-head <full SHA> --add <local file>:<repo path> --message "<subject>" --commit-body-file <file>`.
      - Build each file from `git -C <checkout> show <expected-head>:<path>`: the base that counts is the branch head's blob, not `main`'s.
      - For a CHANGELOG or cheatsheet conflict, follow auto-memory `reference_changelog_conflict_signed_update_branch.md`.
      - Prove a resolution with `git merge-tree` exiting 0 before you upload.
   7. **Validate with independent agents.** Have each fix-forward or re-land checked by independent agents (auto-memory `feedback_multi_agent_adversarial_validation_sop.md`) before asking for approval.
4. **Merge only after the owner approves the named PR or group.**
   - Refuse any PR whose base is not `main`. `safe_merge.py` does not check the base. Retarget first, with the owner's approval (`gh api -X PATCH repos/pcalnon/<repo>/pulls/N -f base=main`), then let CI run.
   - Run `gh pr ready N --repo pcalnon/<repo>`: `safe_merge.py` refuses a draft.
   - Start `python3 util/safe_merge.py --pr N --repo <bare-repo-name> --execute` in the background, and only when `pgrep -af safe_merge.py` shows none running for that repository from any session.
   - Read its `MERGED` line. Exit 0 does not mean merged, and the SHA it prints is the verified head, not the squash commit.
   - A Cursor review thread blocks the merge until it is resolved, as it did on #2438. Fix or answer each thread, then resolve it.
5. **Record each disposition** in the record the owner names. Archive the next handoff in `prompts/thread-handoff_automated-prompts/`.

---

## Key context and traps

- **Signing.** `required_signatures` and strict status checks hold on all nine repositories. One unsigned commit makes a branch unmergeable, and squash does not rescue it. Never use `--no-gpg-sign`.
- **Fetching.** SSH fetches failed in this session with `Permission denied (publickey)`. `GIT_TERMINAL_PROMPT=0 git fetch https://github.com/pcalnon/<repo>.git <refspec>` works, because the repositories are public.
- **Probe commits.** To test uncommitted work against `main`, merge it first, then stop if that exits non-zero:
  ```bash
  T=$(git merge-tree --write-tree origin/main "$(git stash create)" | head -1)
  P=$(git commit-tree "$T" -p origin/main -m probe)
  ```
  Re-parenting the stash tree onto `origin/main` is only valid while HEAD's tree equals `main`'s. Otherwise the probe silently reverts `main`'s newer files, and a later `merge-tree` against it can never conflict.
- **Temp paths for tests.** Export `TMPDIR` and `GIT_CEILING_DIRECTORIES` as `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp`. Never write under `/tmp`.
- **Symbol-loss waiver.** Use `Allow-Symbol-Loss: method:<Class>.<name>` in a commit body, never in PR prose.
- **Stub-argv tests cannot see Claude Code's parser.** The prompt bug passed every suite. Ask what the real CLI makes of an argv, not whether the list matches (auto-memory `reference_claude_cli_optional_flag_eats_the_prompt.md`).
- **`gh` GraphQL errors.** It answered HTTP 502 once at 21:14Z, and a retry worked. Treat a repository missing from a census as unread, not as empty.

---

## Verification (run first; each comment is an invariant, so stop if one fails)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch -q origin || GIT_TERMINAL_PROMPT=0 git fetch -q https://github.com/pcalnon/juniper-ml.git '+refs/heads/main:refs/remotes/origin/main' || echo "FETCH FAILED: stop"
git merge-base --is-ancestor 1c18106d075747476d6f009e409c2fa479d09347 origin/main && echo "#2438 on main"   # invariant: prints "#2438 on main"
gh pr view 2405 --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'                   # invariant: MERGED db131f7b
# 1. the census
for r in juniper-ml juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-canopy juniper-deploy juniper-recurrence; do
  gh pr list --repo "pcalnon/$r" --state open --limit 200 --json number,isDraft,baseRefName,autoMergeRequest \
    --jq "\"$r: \(length) open, \([.[]|select(.isDraft)]|length) draft; base not main: \([.[]|select(.baseRefName!=\"main\")|.number]); armed: \([.[]|select(.autoMergeRequest!=null)|.number])\""; done
# invariants:
#  - juniper-ml's armed set is exactly [2360,2271];
#  - base-not-main is [796] in juniper-canopy and [] elsewhere;
#  - the six other repositories show 0 open.
#  - Every PR in open_prs_2026-11-04_round2.tsv is still open, or its merge or close is explained.
#    #2438 merged as 1c18106d. Higher numbers are new arrivals, not failures.
# 2. the launcher suites on main (invariant: "Ran 107 tests" and OK)
export TMPDIR=/home/pcalnon/Development/python/Juniper/juniper-ml/tmp GIT_CEILING_DIRECTORIES=/home/pcalnon/Development/python/Juniper/juniper-ml/tmp
W="$TMPDIR/verify-launchers-$$"; mkdir -p "$W" && git archive origin/main | tar -x -C "$W" && (cd "$W" && python3 -m unittest tests/test_wake_the_claude.py tests/test_claude_interactive.py 2>&1 | tail -3); rm -rf "$W"
# 3. this arc's worktrees (invariant: the three under A4, unless the owner had them removed)
git worktree list | grep -E 'wake-the-claude|handoff-2026-11-04-launcher-arc'
# 4. no merge in flight (invariant: no output)
pgrep -af safe_merge.py | grep -v pgrep
```

At 21:54:58Z this block printed exactly what those invariants say. juniper-ml had 43 open PRs, 41 of them drafts. The only census PR no longer open was #2438, merged. Three worktrees were listed, and no `safe_merge` was running.

---

## Evidence kept (unversioned, under the primary's `tmp/`; keep until no longer needed)

Paths are relative to `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/856140dc-d1b5-46cb-b0d6-7163d63ded7b/scratchpad/followups/`.

**The census:**

- `open_prs_2026-11-04.tsv`: 12:14Z, no header row.
- `open_prs_ci_2026-11-04.tsv`: 12:16Z, no header row, per-PR check rollups. It counted superseded failures.
- `open_prs_2026-11-04_round2.tsv`: 21:14Z, with a header row, base and arm state.

**`promptfix/` (the prompt fix):**

- `commander_probe.js`
- `mutation_vs_2405.log`, `mutation_vs_2405_round2.log`, `mutation_review_fix_vs_8711c41d.log`
- `combined2403.log`
- `precommit.log`, `precommit_round2_pass1.log`, `precommit_round2_pass2.log`, `precommit_round2_changelog.log`
- `commit_body.txt`, `commit2_body.txt`, `pr_body.md` (the body as opened), `pr_body_v2.md` (after the review)
- `push_signed_commit2.log`
- `safe_merge_2438.log` (the refused run), `safe_merge_2438_round2.log` (the merge)

**#2405:** `safe_merge_2405.log`, `mutation_vs_main.log`, `combined_2403.log`.

**This handoff:** the draft sits in `handoff/`.

**The validators' scratch directories**, under `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/`: `handoff-audit-20261104-launcher/`, `factcheck-handoff-2438-20261104/`, `prompt-validator-2026-11-04-handoff/` and `review2-handoff-launcher-20261104/`.

- Their full-tree extracts were deleted. So were this session's `promptfix/mutation/` and `promptfix/combined2403/`. All of them can be regenerated, and juniper-ml's doc-link hook scans `tmp/`.
- Three bare clones remain: `factcheck-handoff-2438-20261104/ml.git`, `prompt-validator-2026-11-04-handoff/probe.git` and `review2-handoff-launcher-20261104/ml.git`.

## Documents created or modified in this arc

- **juniper-ml#2396**, repair commit `b7e3312c`:
  - `scripts/wake_the_claude.bash`
  - `scripts/claude_interactive.bash`
  - `tests/test_wake_the_claude.py`
  - `tests/test_claude_interactive.py`
- **juniper-ml#2405** (merged):
  - `scripts/wake_the_claude.bash`
  - `tests/test_wake_the_claude.py`
  - `CHANGELOG.md`
- **juniper-ml#2438** (merged):
  - `scripts/wake_the_claude.bash`
  - `scripts/claude_interactive.bash`
  - `tests/test_wake_the_claude.py`
  - `tests/test_claude_interactive.py`
  - `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
  - `CHANGELOG.md`
- **This handoff's PR**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-04_launcher-prompt-guard-claudey-defaults-open-pr-sweep-next.md` (new).
- **Auto-memory** (unversioned):
  - `reference_claude_cli_optional_flag_eats_the_prompt.md`: new; its status line updated at 21:31Z, after #2438 merged.
  - `reference_verification_discipline_hub.md`: two lines appended.
  - Edited on 2026-11-03: `feedback_never_write_to_tmp_use_repo_tmp.md`, `reference_squash_body_excludes_merge_commits.md`, `feedback_launcher_default_model_switches_periodically.md`.
