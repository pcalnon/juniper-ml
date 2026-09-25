# Handoff (CONSOLIDATED): defect-register round 42, both lanes. Validations, fix-forwards and the closes PR are owed

**Written:** 2026-09-25, drafted about 01:35Z and brought up to date between 02:10Z and 03:20Z, by session `2fba4397` ("defect reg [24f8d8]"). "At writing" means that window; where a time matters, it is given. The owner's sweeper merges open PRs while you read: trust `gh`, not this file, for any PR's state.
**This file:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`. It is UNTRACKED in `fizzy-hugging-dream` until the consolidation PR ships it. Give this path to any session that asks for the consolidated handoff.

**This document governs round 42's remaining work, in both lanes.** The owner asked on 2026-09-24 at about 23:25Z for three handoffs to be merged into one validated handoff, losing no task and no necessary context. It consolidates:
1. **The register lane's handoff:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
   - Session `2fba4397-7d9b-4929-8ca2-375b8168e1c8`, `ListAgents` name **"defect reg [24f8d8]"**, worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. That session wrote this file.
   - It was validated in three rounds, archived as `reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round{1,2,3}-*.md`. No lane returned a clean PASS: round 1 had one FAIL and two PASS WITH CORRECTIONS, and rounds 2 and 3 all PASS WITH CORRECTIONS. Every correction is applied, both there and here.
2. **The follow-up lane's handoff:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, in juniper-ml#2097 (head `2e4917c2`).
   - Session `bc31e993-97b0-4a01-ae04-cb39593eb647`, **"defect reg [042116]"**, which wrote it and handed off. Never message it: that is its own request, and it overrides document 1's "message it too".
   - It was validated in 5 rounds, archived as `reports/2026-09-24_defect-register-round-42/handoff-followup-lane-round*-*.md`.
   - Its own predecessor, `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`, is carried by it and is not re-read here.
   - The lanes were split by "Split: old does follow-ups", relayed by the register lane (`defect reg [977fa8]`, session `8f86dec2`, which has ended: a `[977fa8]` row is not a successor), and the owner's "Resume both here" in session `bc31e993` is consistent with it.
3. **Their common predecessor:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (session `8f86dec2`, on `main` via #2084). It is stale.

This file's instructions replace those of documents 1 and 2, which become **evidence indexes**. Document 2 tells a Lane F session that it governs until this file is on `main`: First action 3 reconciles that. Appendix I maps every item of all three to where it lives here.

**This file's own consensus validation** is archived as `reports/2026-09-24_defect-register-round-42/handoff-consolidated-round*-*.md`, and the frozen copies its reports cite by line are in `handoff-frozen/` beside them. Both ship in the consolidation PR, on branch `docs/handoff-round42-consolidated`.

**Length:** the Goal is about 1,450 words against the ~1,200-word target, which `~/.claude/CLAUDE.md` calls a median, not a cap. It merges three handoffs and carries two lanes' first actions and live state; what could move to an appendix without loss has moved.

## Goal (paste the WHOLE document, appendices included, as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem.
- The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.

There are two work-streams:
- **Lane R (register):** the register and its closes PR; the API primer; the juniper-data fix-forward of #438; the fork-drift gate (`tests/test_service_fork_drift.py` and its `docs/REFERENCE.md` bullet); `MEMORY.md`; and the later arc items C-A…D-G.
- **Lane F (follow-up):** the cascor and canopy follow-ups, and the four "Key leaks" PRs. The owner's ruling "Fix everywhere now (Recommended)" ends "**Releases stay yours.**" So Lane F validates and fixes forward, and it surfaces releases rather than cutting them.

One successor should own both lanes. If the owner starts two sessions:
- split them by lane, and let each merge only its own lane's PRs;
- address each other by `ListAgents` name with the `[ref]` (several sessions are named "defect reg");
- send each other every PR number, merge SHA, validation summary and owner ruling (verbatim), and every juniper-ml `docs/REFERENCE.md` or root `CHANGELOG.md` section a PR touches;
- Lane F stays out of the register, `tests/test_service_fork_drift.py`, `docs/REFERENCE.md`'s drift-gate section, `util/ad-hoc/2026-09-24_round42_probes/README.md` (#2089), `util/ad-hoc/2026-09-24_archive_round42_reports.py` and Lane R's juniper-data branch (Appendix C). Lane F heads its reports with the archive header and sends Lane R their filenames, agent ids and its session's full UUID (for `SESSION_IDS`; document 2, "Coordination" → "Archiving"); Lane R adds the `MISSING` entries. Lane R stays out of `juniper_data/api/security.py` and Lane F's branches.

**The owner's policy:**
- The PR sweeper is theirs ("Mine: fix forward"): it un-drafts, arms and update-branches open PRs as `pcalnon`, and its merges are intended.
- Commits also appear on open PRs from that account: #2077 got `095a2108`, and canopy#685 got two. Do not draft or disarm a PR to hold it.
- An open PR can merge at any moment. When a validated merge matters, validate BEFORE the change reaches a PR branch (always, for F2 and F4); otherwise, validate after merge and fix forward.
- **Merge approval does NOT carry to a new session** (`feedback_headless_merge_approval_policy.md`). Get the owner's grant in YOUR session before any merge, arm or re-arm, and then only with checks green on the current head and the validators cleared. Just before merging, re-read the PR's commits: the owner's account may have added one since you validated. Merge with `util/safe_merge.py` (Key context, "Merging").

**First actions, in this order:**
1. **Run the verification commands** below.
2. **Is "defect reg [24f8d8]" still live?** Run `ListAgents`, loading it with ToolSearch if it is deferred; if it is unavailable, ask the owner whether that session is open. `ListAgents`' header line names your own session and `[ref]`; [24f8d8] appears among the peer sessions in any state but offline. Its executor finished at 01:49Z (In flight).
   - **Listed:** message it first, with your name and `[ref]`. Say you are its successor (the lane split is settled at First action 3). Ask (1) whether it has opened, or will open, the consolidation PR, and when; (2) whether any of its subagents is still running; (3) whether it still writes in its worktree. If it will open the PR, let it, and wait for the PR: send the message with `notify_when_idle: true`, and if [24f8d8] goes idle or exits with no PR, ask once more, then treat it as silent. Otherwise ask it to launch and ship nothing more. Ask it to forward anything a Lane F successor sends it (document 2's Step 0 messages [24f8d8] first). Start no item it says it is doing.
   - **Listed but silent** (no reply by your next turn): carry on; a handed-off session may stay listed. Before asking the owner to close it (needed only if you must ship its files yourself, First action 5), check that no subagent of it is running: `find /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/ -name '*.jsonl' -mmin -15` must print nothing (`ls -lt` would show local time, UTC-5). Closing a session kills its subagents.
   - **Not listed, or offline:** carry on.
3. **Find the other sessions.** In the same `ListAgents` output, any session already working either lane from documents 1 or 2 is a successor, for example one following #2097's Step 0. Load `SendMessage` with ToolSearch if it is deferred. Tell it this file governs, and agree the split; ask the owner if unsure. Document 2 tells its successor to follow document 2 until the consolidated handoff is on `main`, so until the consolidation PR merges, agree the split explicitly.
4. **Get your own merge approval** from the owner. A handoff cannot carry it: that is the ml#1118 incident. Ask Appendix B's questions in the same turn, all but the releases (which wait for Lane F's juniper-ml F-PR to validate).
5. **Land the three handoff PRs, with your grant:**
   - [F] #2097 (Lane F's evidence), which CodeQL blocks (45 new alerts, 3 high, in probe code: Appendix B);
   - [R] the consolidation PR (this file, document 1, and Lane R's evidence). Land it early: a document-2 successor waits for it;
   - [R] juniper-ml#2089 (Lane R's probes), which CodeQL also blocks.

   Both CodeQL blocks are the owner's call (Appendix B).

   Find the consolidation PR with `gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-consolidated --state all`. If it does not exist, ship Lane R's files yourself (Git status).

**Merged, round 42, since 2026-09-23** (post-merge `main` CI green on all; details in Appendix H):
- **Lane R:** juniper-ml#2088 (`5af9d722`, 23:41:16Z), the second register and primer fix-forward, validated before its PR; juniper-ml#2081 (`7e8c7ff9`, 22:45:08Z), probe provenance; juniper-data#438 (`0f0f7e0e`, 18:52Z), which merged before its fix-in-place landed.
- **Lane F:** juniper-cascor#688 (`7f4a7213`, 18:56:25Z), superseding #686 (CLOSED); juniper-canopy#683 (`7ab994e5`, 19:10:20Z); juniper-canopy#685 (`dc5ea02e`, 23:24:14Z), **UNVALIDATED**; juniper-ml#2086 (`c061a99f`, 20:37:13Z); juniper-ml#2072 and #2077 (`ac912eba`, `6c23fdde`).
- **Lane F, merged by the owner's sweeper while this file was being validated:** juniper-cascor#689 (`b9484fef`) and juniper-data#440 (`26491531`), both validated before they merged; and juniper-cascor#690 (`0fbb447a`), **UNVALIDATED**. Times and CI: Appendix H.
- **juniper-data 0.16.0** is on PyPI (18:35Z).

**Open at writing** (read live state from `gh`, never from this file's SHAs):
- juniper-ml#2089 (`669b2c75`, since the handoff-validation probes were added at 02:39Z and 03:03Z) and #2097 (`2e4917c2`), CodeQL failing on both, neither armed (BEHIND at writing, because `main` moved);
- Lane R's data branch `fix/conditional-requests-round4-followups` (`94ce8b1f`), with no PR yet;
- no open PR in juniper-data, juniper-cascor or juniper-canopy.

**In flight:** nothing, once this file ships; its own validation lanes, subagents of [24f8d8], finish and are archived first (if not, Git status says how to finish them). Executor `a46e715a6801b98ca`, which fixed the data fix-forward's round-1 findings, finished at 01:49Z: one signed commit, `94ce8b1f`, and no PR. Its report, its PR draft and the branch's state are in Appendix C.

**Work.** The numbers are a suggested order, not dependencies: items 2-5 need not wait for item 1, and item 7 waits only for item 6's filing of APD-ECO-013 (data#440 and cascor#689 have merged). Register and primer PRs upload WHOLE files as single-parent signed commits, so keep at most ONE open PR that uploads the register or the primer, each built from fresh `main`. Steps for items 1, 5, 6, 8 and 9 are in Appendix J.
1. **[R] Finish the data fix-forward:** its pre-PR round 2 on `94ce8b1f`, then its PR, then the merge (Appendices C and J).
2. **[F] Validate cascor#690 post-merge** at `0fbb447a` (its commits `c4e002d2` and `78e99414`), then fix forward in a NEW PR from `main` (Appendix D, item 1).
3. **[F] Validate canopy#685 post-merge** at `dc5ea02e`, then fix forward in a NEW PR from `main` (Appendix D, item 2).
4. **[F] The F fix-forwards** from the bytes-compare validation (Appendix D, items 3-4), all as NEW PRs from fresh `main` now that #689 and #440 have merged: one juniper-ml PR for F2, F6, F9, F10 and service-core's F3 and F5; one cascor PR for F3, F4, F5, F7 and F9; one data PR for F3 and F5. Validate each with two lanes, F2 and F4 BEFORE they reach a PR branch.
5. **[R] Validate #2088's one unvalidated delta**, `990ef3f9..2439d049`, with two lanes; archive their reports, then fix forward (Appendix J). It can run beside any other item.
6. **[R] The closes PR,** opened early: its gates are on ROWS, not on the PR (Appendices A and J).
7. **[R] The fork-drift marker** (Appendix E), once item 6 has filed APD-ECO-013.
8. **[R] Verify on the real services, then file** (a) the 422-echo defect, (b) the primer toy's copy of it, and the primer's stale lines 4742-4743 (Appendices A and J).
9. **[R] PATCH the bodies of juniper-ml#2080 and #2088** with `gh api -X PATCH` (Appendix J).
10. **[R/F] Owner decisions:** Appendix B, each tagged with the lane that asks it. Surface them; decide none.

## Key context and traps (part of the prompt)

**Uploads, commits and merges:**
- **Uploads are WHOLE-FILE, and files move under you.**
  - Before every push, `git fetch` and run `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`. Compare with `git show origin/main:<p> | diff - <p>`; `git diff origin/main -- <untracked>` fakes deletions.
  - On an OPEN PR, also re-read the PR head's copy of each file you overwrite (`gh api 'repos/pcalnon/<repo>/contents/<path>?ref=<headRefOid>'`). Update-branch merges and the owner's commits land there (#2077's `095a2108`, canopy#685's two), and a fixup rebuilt from `origin/main`, or from a worktree HEAD that is only a local copy, reverts them.
  - For a shared `CHANGELOG.md` `[Unreleased]`, prove `main`'s lines are a subset of yours.
- **Signed commits have ONE parent** (GraphQL `createCommitOnBranch`), so a textual conflict cannot be merged away. Supersede from fresh `main`, as #686 → #688 did.
- **Signed pushes.** Use `util/push_signed_commit.py --expected-head <FULL 40-hex sha, from gh>`.
  - Never pass `git rev-parse HEAD`: in several worktrees HEAD is a local copy, not the PR head.
  - A run can create nothing, so check the remote ref afterwards. A re-run with the same head is safe.
  - Both pushers take `--commit-body-file`; prefer it to `--commit-body "$(cat f)"`, which is also accepted.
- **Where fixes go.** An OPEN PR gets a signed fixup. A MERGED PR gets a new PR from fresh `main` (`util/open_signed_pr.py`). Read each PR's state with `gh pr view <N> --json state,headRefOid,mergeCommit` at push time. Validate every FIX, whether a fixup or a fix-forward PR, of either lane, with at least two lanes (document 2, OPEN 4); a row closes only once its fix-forward's validation also holds (Appendix A, Gates). Evidence-only commits (archived reports, `MISSING` entries, probes, handoffs) need only the archiver's `--check` and CI.
- **Squash bodies.** The sweeper stores the DEFAULT squash body, and GitHub appends a `Co-authored-by` paragraph.
  - Put waiver trailers (`Allow-Symbol-Loss:`) in a COMMIT body in the range; main-verify's line-scanning regex finds them there.
  - `git log -1 --format='%(trailers:key=…)'` on a squash prints an empty line; check with `grep -c`, or with `juniper-symbol-loss-check --base <parent> --head <sha>`, which scans lines.
  - juniper-data and juniper-cascor squash with `COMMIT_MESSAGES`: the default squash body carries every commit message of the PR.
  - A curated re-arm is `gh pr merge --disable-auto`, then `--auto --squash --match-head-commit <validated sha> --subject … --body-file …`. It needs your grant, and `--auto` on a MERGEABLE PR merges at once; `--match-head-commit` refuses a head that moved since you validated.
- **Merging:** `python3 util/safe_merge.py --repo <repo> --pr <N> --execute` (without `--execute` it is a dry run). Read its `MERGED` line: exit 0 does not mean merged. It takes no subject or body, so a hand-written squash body goes only through the curated re-arm ("Squash bodies").
- **`strict: true`:** after every move on `main`, run `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<the PR's full headRefOid, from gh>` (not `main`'s sha); an armed PR that is BEHIND waits forever.
  - Run update-branch BEFORE building a CHANGELOG over a release cut: a 3-way merge once duplicated `## [0.16.0]` silently.
  - `gh pr edit` is broken; use `gh api -X PATCH`.

**The register and the primer:**
- **Never name an OPEN id on the register's §2 status list** (L177, the line beginning "**Eighty-one of the 96 have since been fixed**"; L176 above it is not that line): `util/ad-hoc/register_status_crosscheck.py` reads every id on it as closed.
- **The primer is cited by bare line number: edit it in place only.**
  - Model a new editor on `util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py`, which refuses to run twice and refuses any line move.
  - `util/ad-hoc/2026-09-24_register_primer_citation_census.py` counts every bare number past 5758 (69 citations, 82 numbers today). Name a retired anchor in words.
  - The harness is `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>`, which gives 62 tests. `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` needs `--venv` and `--scratch`.
  - The venv: CPython 3.13.13 (JuniperCanopy1's interpreter), fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2. The copy at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv` is on tmpfs. Build your own in your scratchpad: `/opt/miniforge3/envs/JuniperCanopy1/bin/python -m venv <dir>`, then `<dir>/bin/pip install fastapi==0.141.1 starlette==1.6.0 pydantic==2.13.4 httpx==0.28.1 pytest==8.4.2`.

**Running lanes and archiving their reports:**
- **How to run a lane:** a background `general-purpose` Agent.
  - Launch the lanes in ONE message: A re-derives every claim from source; B refutes, defaulting to REFUTED.
  - Give each its own scratch subdirectory.
  - Tell each: read-only; no secret or email egress; compound shell in a script; prune `/tmp`.
  - Report format: as in `register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
- **Archiving** uses `util/ad-hoc/2026-09-24_archive_round42_reports.py`.
  - Add your session's full UUID (the directory above your scratchpad) to `SESSION_IDS`, and each report to `MISSING`.
  - Until the consolidation PR merges, fizzy holds an unshipped copy of this file with many more `MISSING` entries than `main`'s. Archive nothing into another juniper-ml PR until it merges: a second copy of the file makes whichever PR merges second conflict, and a single-parent signed commit cannot resolve that. Otherwise build your entries on the consolidation PR head's copy, and ship them as a fixup on that PR.
  - `HEADER` hard-codes 2026-09-24: change it for new reports.
  - It refuses a report holding credential-shaped text or the owner's email. A REFUSE can be a false positive: on 2026-09-25 a handoff filename matched the PyPI pattern, and a report quoting the bare `AgEIcHlwaS` pattern matched that one; both are narrowed to a token's shape (fizzy's copy only, until the consolidation PR merges). Characterize a match without printing it (length, case, prefix); never edit an archived report to pass the scan. Fizzy's copy names an email match "owner-email"; `main`'s older copy prints the pattern, which IS the address, so never paste its raw REFUSE line anywhere.
  - Run `--check`, then run it without. The header is `<!-- Archived verbatim YYYY-MM-DD from subagent a<16 hex> of session <8 hex> (final message). -->` followed by a blank line.
  - Four Lane F reports are headed "(turn-ending report k of 5 …)", and `--check` skipping them is expected: `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`. Byte-compare those against their agents' transcripts by hand before citing them.
- **Agents.** A usage limit kills subagents; resume each with SendMessage, only from the session that spawned it. An agent the USER stopped cannot be resumed: relaunch it fresh from its WIP.

**Environment:**
- **Sentry:** set `SENTRY_SDK_DSN` (this shell exports it), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to `""` in every test run and server. Set them empty, never unset: `load_dotenv` re-injects. Never use port 8100, 8201 or 8050.
- **/tmp is a ~1M-inode tmpfs** (83% at writing; it hit 100% on 2026-09-24). Extract only what you need, prune, and keep probes in `util/ad-hoc/`.
- **`pkill -f '<pattern>'` also matches the shell running it.** Use `pkill -A -f …`, or bracket one character (`'…1879[7]'`) and run pkill as its own command. A pattern that starts with `-` needs `--`.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage (a backslash-u escape of U+2028, or of a surrogate pair). Build such text with `chr()`, and check it with `od -c`.
- **The worktree sandbox's refusals are heuristic:** a shell variable or a loop anywhere in a command that also runs git can be refused. Refused this round:
  - `$(...)` feeding git or gh; loops around git or gh, or a `for` loop with a variable inside a `gh` argument;
  - backticks inside heredocs, and a heredoc inside a compound command (write the file with the Write tool instead);
  - the word "git", in any case, inside a `python3 -c` string or a `for` word list;
  - a `-C` path relative to a `cd`, and sometimes a computed `git -C "$d"`;
  - variables around `sed` or `find`; sometimes, `env -u` inside a compound command;
  - a computed `python3` argument, and process substitution in a compound git command;
  - `bash -c` with computed text;
  - `git -C`, or `cd … &&` git, into the shared juniper-ml checkout or another worktree under `juniper-ml/.claude/worktrees/`. Read files there with `cat`.

  Use plain separate commands with absolute paths, or a script under `util/ad-hoc/`.
- **Never run** `util/worktree_cleanup.bash` (it pushes and runs `gh pr create`, which recreates deleted remote branches with unsigned commits), nor `util/remove_stale_worktrees.bash` (it has no staleness predicate).
- **Other sessions.** At 01:37Z `ListAgents` listed one other live session, "containers [2703c8]"; it handed off at 01:39Z in juniper-ml#2100 (`HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`, whose item 2 carries the 0.16.0 notify-consumers 403). At 02:31Z no live defect-register, canopy or containers session was listed ("containers [5b005d]" and "canopy e2e phase 1 seg 9 [33ec49]" were listed offline): "defect reg [042116]" (Lane F's author), "canopy combined [577a1c]" and the canopy E2E session had gone too. Canopy-ledger items (Appendix A) go to the next canopy session; if there is none, record them in the ledger yourself.

## Verification commands
Run them from your own juniper-ml worktree, fast-forwarded to `origin/main` first (a new worktree can start behind it). Where a path is absolute, `cat` it; do not use `git -C` into another juniper-ml worktree.
```
git fetch origin && git merge-base --is-ancestor 5af9d722 HEAD && echo at-or-after-2088   # must print; if not, fast-forward your clean worktree to origin/main first
gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-consolidated --state all --json number,state,mergeCommit   # this file's PR
gh pr view 2097 --repo pcalnon/juniper-ml --json state,headRefOid,mergeStateStatus,mergeCommit   # Lane F's evidence; OPEN at writing, BEHIND because main moved (BEHIND masks BLOCKED); the next line shows CodeQL failing
gh pr checks 2097 --repo pcalnon/juniper-ml | grep -i codeql   # fail at writing
gh pr view 2089 --repo pcalnon/juniper-ml --json state,headRefOid,mergeStateStatus   # OPEN at writing, BEHIND (BEHIND masks BLOCKED); CodeQL fails (below)
gh api graphql -f query='query { a: repository(owner:"pcalnon", name:"juniper-cascor") { p690: pullRequest(number:690) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } p689: pullRequest(number:689) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } } b: repository(owner:"pcalnon", name:"juniper-canopy") { p685: pullRequest(number:685) { state headRefOid mergeCommit { oid } } } c: repository(owner:"pcalnon", name:"juniper-data") { p440: pullRequest(number:440) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } mergeCommit { oid } } } }'   # at writing all MERGED: #690 0fbb447a, #689 b9484fef, #685 dc5ea02e, #440 26491531
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # 94ce8b1f… at writing
gh pr list --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --state all   # none at writing
git --no-optional-locks -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status -sb   # in sync with origin and clean at writing; never push from it. [ahead N] = an unsigned scratch commit: never push it; after a signed push and a fetch, [ahead 1, behind 1] is expected
cat /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md | head -3   # document 1, until it ships
gh pr checks 2089 --repo pcalnon/juniper-ml | grep -i codeql   # fail at writing
gh pr list --repo pcalnon/juniper-data --state open; gh pr list --repo pcalnon/juniper-cascor --state open; gh pr list --repo pcalnon/juniper-canopy --state open   # none at writing
python3 util/ad-hoc/register_open_set.py | grep 'rows |'    # 136 rows | 100 fixed | 36 open, until the closes PR; reads YOUR worktree's register
python3 util/ad-hoc/register_status_crosscheck.py | tail -1   # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c 'OK    '   # positive (53 in fizzy at 03:05Z; 34 in a worktree at origin/main until the consolidation PR merges); 0 means it exited early (a cited transcript is gone)
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check 2>&1 | grep -c -e DIFFER -e REFUSE -e Traceback -e '^session ' -e 'no assistant message'   # 0; a crash or an early exit is counted, not hidden
ls /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42/ | grep -c -e data438-fixforward -e handoff-2fba4397 -e handoff-consolidated -e owner-ruling-key-leaks   # 21 at 03:05Z, after round 3; +1 per later validation report of this file: Lane R's reports that ship in the consolidation PR
python3 -m unittest tests/test_service_fork_drift.py   # "Ran 11 tests … OK (skipped=3)"; with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1: "Ran 11 … OK". It reads source only, so the Sentry rule does not bite
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -e shortfall-mixed -e secret-leaks -e bytes-compare -e blank-key-678 -e sentry-locals -e round3-followups   # Lane F's six, plus Lane R's data worktree
df -i /tmp | tail -1
```

## Git status at writing
- **Lane R, worktree `fizzy-hugging-dream`** (branch `worktree-fizzy-hugging-dream`).
  - It holds three unsigned LOCAL scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`): **never push or commit here.** Their content is #2088's.
  - Its uncommitted files ship in the consolidation PR. They are:
    - the extractor `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (`--topic key-leaks`);
    - the archiver's new `MISSING` entries;
    - `reports/2026-09-24_defect-register-round-42/{owner-ruling-key-leaks-verbatim, data438-fixforward-round1-laneA-reprobe, data438-fixforward-round1-laneB-refute, data438-fixforward-round1-fix-report, data438-fixforward-pr-draft}.md`;
    - the `handoff-2fba4397-round{1,2,3}-*` and `handoff-consolidated-*` validation reports, and `handoff-frozen/` (the frozen copies they cite, plus its `README.md`);
    - the executor's `util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py`;
    - the PR opener `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py`;
    - documents 1 and this file.
  - **Until the consolidation PR merges, these files exist ONLY in fizzy.** Read them with `cat`, and give your lanes their absolute paths (`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/<path>`). Once the PR is open, `git show origin/docs/handoff-round42-consolidated:<path>` also works; #2089's probes read the same way from `origin/chore/round42-probe-provenance-session-2fba4397`.
  - #2089's files are also untracked there, and must stay OUT of every other PR: `util/ad-hoc/2026-09-24_round42_probes/`, `…_copy_round42_session2fba4397_probe_scripts.py`, `…_open_round42_session2fba4397_probes_pr.py` and `…_push_round42_handoff_probes_to_2089.py`, byte-identical to its head `669b2c75`.
  - **To ship them yourself** (only if the consolidation PR does not exist, and only once [24f8d8] is gone or has confirmed it no longer writes there): run the opener from fizzy BY ABSOLUTE PATH, dry run first: `python3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py --title '<title>' --message '<headline>' --commit-body-file <ABSOLUTE path> --body-file <ABSOLUTE path> --dry-run`, then again without `--dry-run`. The body files must be ABSOLUTE paths: it runs `util/open_signed_pr.py` from fizzy, so a relative path is read there. It finds the repository from its own location, so it ships fizzy's files; it wraps `util/open_signed_pr.py`. Write the title and both bodies yourself, listing every shipped file by name (Appendix G). It names the files, leaves #2089's out, and refuses a missing file, a stale base (any file whose `HEAD` copy differs from `origin/main`'s: for an untracked file, any path `origin/main` already holds; the two tracked files, the archiver and the extractor, upload unless `main` has changed them. It reads your LOCAL `origin/main`, so fetch first; the worktree was 8 commits behind at 02:30Z), any path an open PR already carries (it reads every file of every open PR, not `gh pr view --json files`, which stops at 100), and the owner's email address. Put `Allow-Symbol-Loss: const:SESSIONS` in the commit body's last paragraph: the extractor renames `SESSIONS` to `SESSION_IDS`. If the consolidation PR already carries these files, ship nothing.
  - Nothing is staged there. Its three scratch commits were made only so the CI screens could run.
  - **Unarchived validation reports** (only once [24f8d8] is gone or has confirmed it no longer writes in fizzy). List the lanes' transcripts with `grep -l consolidated_r /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/*.jsonl`; every agent id there that is not a `MISSING` key in fizzy's archiver is unarchived.
    - Archive one only if its transcript ENDS with its report: the last record is an `assistant` message whose content is text only, with no `tool_use`. A lane that did not finish died with its session and cannot be resumed from yours: do not archive its last message; re-run that lane fresh if its verdict is still needed.
    - Name each file `handoff-consolidated-round<k>-lane<X>-<role>.md` (F `reprobe`, O `amputation`, P `fresh-session`), add its `MISSING` entry, and run fizzy's archiver BY ABSOLUTE PATH, `--check` first and then without (it writes into fizzy).
    - If the consolidation PR does not exist yet, the opener's report globs ship them; if it is open, ship them and the archiver as a fixup on it.
  - **Their probes, too.** Every validation lane leaves its probe scripts in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc<k>/lane<X>/` (tmpfs only). Rounds 1-3's are on #2089 (Appendix B). For any later round with no `handoff-consolidated-round<k>-lane<X>/` directory in #2089's file list (`gh api --paginate repos/pcalnon/juniper-ml/pulls/2089/files --jq '.[].filename'`): add the lane to `LANES` in fizzy's `util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py` and to `DIRS` in `…_push_round42_handoff_probes_to_2089.py`, add a README row, run the copier, and push with the pusher (`--expected-head` = #2089's full head, from gh; rebuild `README.md` from that head first). Do it while the scratchpad survives, and only once [24f8d8] is gone or has confirmed it no longer writes there.
  - **Land the consolidation PR before any other PR touches a file it carries,** above all `util/ad-hoc/2026-09-24_archive_round42_reports.py` (every archiving run edits it) and `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py`. The opener compares fizzy's HEAD, which must not move until that PR merges, with `origin/main`: once another PR changes either file on `main`, the opener refuses it for good. Then ship with `util/open_signed_pr.py --branch docs/handoff-round42-consolidated` directly, rebuilding those two files from `git show origin/main:<file>` plus fizzy's additions (read fizzy's copy with `cat`).
  - Never `reset`, `checkout`, `clean`, `stash` or remove that worktree while "defect reg [24f8d8]" is listed, or before the consolidation PR has merged AND everything written there after it opened has shipped (compare the directory's files, read with `ls` and `cat`, against the PR's file list; ship anything newer in a follow-up with `util/open_signed_pr.py`; the opener refuses every path that PR already shipped). After that, removing it still needs the owner's go-ahead (Appendix F). For all these rules, an offline [24f8d8] row counts as gone.
- **Lane R, juniper-data worktree** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2`. Its name says round3, but it holds `fix/conditional-requests-round4-followups` at `94ce8b1f`, clean and in sync with `origin`. **Do not remove it** until the data fix-forward's PR merges.
- **Lane F, worktree `happy-skipping-hollerith`**: fast-forwarded to `5af9d722`, with no tracked changes. Its 95 untracked files are #2097's, byte-identical to `2e4917c2`: do not remove it before #2097 merges.
- **Worktrees and stale branches:** Appendix F. Remove any only with the owner's go-ahead in your session.

## Appendix A: the closes PR (Lane R)

**Gates.** Close a row only after its PR merges AND its own validation holds.
- `APD-CASCOR-008` / `-013`: cascor#690 merged UNVALIDATED at 02:06:36Z (`0fbb447a`); they wait for its post-merge validation (Work 2).
- `APD-DATA-017` / `-029` / `-032` / `-057`: data#438 merged; the fix-forward (Work 1) must merge and validate.
- `APD-ECO-014`, canopy's half of `APD-ECO-013`, and F-CANOPY-061/-062's FIXED-BY: canopy#685's post-merge validation (Work 3).

**File** (the three ids are reserved, not yet filed). Re-verify every row against source at `main` before filing it. The filing evidence for ECO-013 and ECO-014 is `pending-items-snapshot-2026-09-24T1110Z.md:11-20` (canopy `security.py:113-117` at `8917fdac`, the sentry-sdk run on real uvicorn, the ERROR sites, the 409 bodies, the anonymous `GET /api/csrf` → `POST /api/train/start` recipe) and `canopy685-implementation-report.md`.
- **`APD-ECO-013` (S).** A non-ASCII `X-API-Key` makes the `str` `compare_digest` raise; the 500 goes to Sentry, and its local-variable capture records the real key.
  - Fixes, all merged: juniper-ml#2086, canopy#685, data#440 (`26491531`) and cascor#689 (`b9484fef`).
  - **It stays open until** #685's validation holds and F2 and F3 are fixed. Both lane handoffs set this condition, whose other half (data#440 and cascor#689 merged) was met at 01:57Z.
  - F5-F10 go on the row as residue unless they are fixed first (Appendix D, item 4).
  - Source: `bytes-compare-ml2086-data440-cascor689-validation.md` (#2097).
- **`APD-ECO-014` (S):** canopy's padded outbound keys leaked into client errors, logs, Sentry and API bodies (the 409 at `main.py:3712/:3714`, `recurrence_backend.py:219` → `:287`, and the adapter's `{"error": str(e)}`), including an ANONYMOUS read of the cascor key via `POST /api/train/start` with auth on. File it OPEN, with canopy#685 as its fix; close it once #685's validation is cited.
- **`APD-CASCOR-014` (S),** Lane F's F4: cascor tests that `import main` start the REAL Sentry SDK when a DSN is exported. 9 files sent 25 envelopes to a sink.
  - The cause: `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` → `src/main.py:231`.
  - The fix: F4 (Appendix D).
  - cascor#689's `include_local_variables=False` strips the locals, but the events are still sent.
  - File it OPEN; close it when F4's fix merges and its validation holds.
- #2097 says "APD-CASCOR-014 closes when F4 lands", which drops F4's validation gate. Its "APD-ECO-014's condition is met; its validation is yours" keeps the gate, but gives #685's validation to the register lane; here it is Work 3 [F]. These gates govern.

**Update, do not close:** `APD-DATA-055`. #438 fixed its lock half: at data `0f0f7e0e`, `batch_delete` and `delete_expired` go through `delete_under_lock`. Its `If-Match` half awaits the owner's ruling.

**Quote** the "Key leaks" ruling verbatim from `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`, extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks`. It was asked at 10:22:00.792Z and answered at 18:30:09.820Z: "Fix everywhere now (Recommended)".

**Residue to record:**
- **cascor shortfall messages.** The flag-off 422 is no longer shown as a shortfall (#688). A juniper-data 400 for a bad param still was. cascor#690 (merged unvalidated) fixes that by keying on "Re-submit with allow_truncation=true". It also makes `_as_bool_stance` parse a string exactly as juniper-data's pydantic model does (pydantic-core's `str_as_bool`); the old reader read `"f"` and `"n"` as true.
- **Auto-start binds wholesale** (`cascor686-fixup-implementation-report.md` item 2; `pending-items-snapshot-2026-09-24T1110Z.md:40`).
- **`current_dataset` after a partial inline start** names the fetch, as the mixed-provenance ruling intends (`reports/2026-09-24_defect-register-round-42/owner-rulings-verbatim.md`); canopy reads only `.dataset_type`. Record, no row.
- **canopy#683 item 3** is a disclosed behaviour change: a whitespace-only env key makes `/docs` answer 200.
- **A retire condition met.** juniper-canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its condition. Record only: retiring an ad-hoc script is the owner's decision.
- **Already recorded:** cascor#678's stale squash message (register, about L1616).
- **F9's residue:** cascor squashes with `COMMIT_MESSAGES`, so #689's commit message ("4001 close") reached `main` in `b9484fef`.
- **Canopy items,** which go to the canopy E2E ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`), not the register:
  - F-CANOPY-060, -061 and -062 were reserved at 19:40:28Z in `…/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md:53-66`. It is untracked there, and its bytes are on branch `docs/canopy-e2e-handoff-2026-09-24`, with no PR.
    - 060: the refusal cut at `" The resulting dataset"` (`dashboard_manager.py:8410`) drops juniper-data's last sentence (`juniper_data/core/limits.py:168`). The fix is to cut only at `" To accept it,"`. It has no owner.
    - 061 and 062: LOW3 and LOW4, fixed by #685, pending its validation.
  - The fourth item, with no id, recorded by canopy combined at 20:45:53Z: canopy's copies of #687's "Nothing was loaded" sentence, at canopy `7ab994e5` `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` and `src/frontend/dashboard_manager.py:8381`.
    - They went stale when #690 merged at 02:06Z: before it, cascor `main` emitted the sentence at `manager.py:4766`, and #690 rewords it (`:4841` at `78e99414`).
    - Recorded in `…/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`.
  - All of these are in other sessions' worktrees: read only.
  - **Their keeper now:** the canopy-combined handoff, juniper-ml#2096 (OPEN, auto-merge armed, head `00e9eb2d`, opened 01:19Z; `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md`). It carries all four items (its F9, F10 and A2(a)), and byte-identical copies of both records: `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` and `…/r1/DRAFT_r1.md:165-170`. Cite those paths once #2096 merges. Its F10 says to record 061/062 as FIXED-BY #685 when they are filed (the ledger has no F-CANOPY-060…062 yet), so send #685's validation outcome to whichever session takes #2096's handoff (its author, "canopy combined [577a1c]", had gone by 01:37Z), and tell it that cascor#690 merged at 02:06:36Z (`0fbb447a`), so canopy's copies of the fourth item are now stale. If no canopy session exists, record both in the ledger yourself.
- **canopy#685's residue:**
  - the frame-locals gap until the release (Appendix B);
  - the owner calls (a)-(c) (Appendix B);
  - the anonymous rate-limiter 500 needs `rate_limit_enabled`, which is off by default;
  - a stale comment at canopy `test_cascor_service_adapter_gate_coverage.py:49-50` says CI installs only the stub cascor client. It installs the real one. It can ride any later canopy PR.
- **data428 round 3** (`data428-round3-laneA1-security.md`). F3 is `APD-DATA-056`. F2 (the 8,192-byte cap, parsed under `_version_lock`) and F4 (header limits) are recorded nowhere: file or decline each, with a reason.
- **Cite Lane F's archived reports** (#2097) by filename. They reach `main` only when #2097 does (Appendix B).

**To file after verifying on the real services** (Work 8; measured in-process by `handoff-2fba4397-round2-laneF-reprobe.md`, and re-measured by `handoff-2fba4397-round3-laneF-reprobe.md`, whose probes are on #2089 as `util/ad-hoc/2026-09-24_round42_probes/handoff-2fba4397-round3-laneF/probe_{data,cascor,primer}.py`):
- **(a)** A 422 that echoes the input through Starlette's `JSONResponse` (`ensure_ascii=False`) raises `UnicodeEncodeError` on a lone surrogate. That is a `ValueError`, so the outcome depends on the app's handlers:
  - FastAPI's default app: a plain-text 500.
  - juniper-data (`juniper_data/api/app.py:187-212`, `ValueError` handler `:214`, at `0f0f7e0e` and on data `main` `26491531`; the data fix-forward (`94ce8b1f`) moves them to `:193-218` and `:220`, where they will sit once it merges): 400 `{"detail":"Invalid request parameters"}`. The per-field detail is lost, and no Sentry error event is sent. Round 3 re-measured it on data's locked fastapi 0.141.1 / starlette 1.6.0 with a Sentry capture transport.
  - cascor (`src/api/app.py:858`, `ValueError` handler `:918` at `0fbb447a`; round 3 measured at `:856`/`:916`, before #690): measured in-process by round 3 in JuniperCascor1 (fastapi 0.137.0 / starlette 1.0.0, not its locked pair, and without its lifespan): **400** in cascor's envelope, `error.code` `VALIDATION_ERROR`, message "Invalid request parameters", `detail: null`. The per-field list is lost, and no Sentry event is sent. Re-measure it on the locked pair.
  - Source: `handoff-2fba4397-round3-laneF-reprobe.md`.
  - It is a sibling of `APD-DATA-056`, and input to D-C.
- **(b)** The primer's `idempotent_jobs.py` has (a)'s default-handler form. A lone surrogate in `dataset_id` fails validation (`string_unicode`); the default 422 cannot render it, so the client gets a plain-text 500, again on retry. No key record is ever created, so there is no replay defect. Correct the primer IN PLACE, together with its lines 4742-4743, which say juniper-data registers no such handler, stale since data#281.

## Appendix B: owner decisions (surface them; decide none)

Ask each as a question with its options (yes or no where none are listed), and record the question, the options and the answer verbatim in the register. Ask them all at First action 4, together with the merge grant, except the releases, which wait for Lane F's juniper-ml F-PR to validate. Each is tagged with the lane that asks it: after a split, only that lane asks, and the other records the answer it is sent, verbatim, and never asks again.
- **[F] The releases. "Releases stay yours."** Until juniper-observability and juniper-service-core ship, and the consumers' locks move, the frame-locals fix reaches no running service. `canopy685-implementation-report.md` measured it: any unhandled exception during a keyed request records the caller's key.
  - **Ask only after Lane F's juniper-ml F-PR validates.** An earlier release ships F2's leak and F10's false sentence.
  - The options:
    1. the owner prepares and cuts both releases; or
    2. an agent opens version-bump and release-notes PRs at versions the owner names, and the owner cuts the Releases.
  - Ask separately who opens the cap, lock and floor PRs (Appendix D, "Release facts").
  - Never approve a deploy gate (`feedback_deploy_approvals_paul_manages.md`).
- **[F] canopy#685's judgement calls** (each can change Work 3's fix-forward):
  - (a) An error that carries an HTTP status still passes its upstream text through. Making it type-only is a one-line change in `src/outbound_errors.py:57-61`.
  - (b) The key rule refuses a space or tab inside a key, which the clients would send.
  - (c) A blank `*_API_KEY_FILE` that shadows a real env var now sends no key.
- **[F] Two stray canopy branches,** `pr-63` and `pr-683`, both at the unsigned `4caf9389`, the #685 worktree's local commit.
  - They were pushed at 22:55Z, have no PR, and no agent transcript records the push.
  - That worktree's upstream is `refs/heads/pr-683`. A plain command-line `git push` refuses there, because the branch names differ; an IDE push, or `HEAD:pr-683`, lands on it.
  - Do not delete them unasked.
- **[F] Purge this round's test events from the live Sentry project?** (yes or no). One run ended "Sentry is attempting to send 2 pending events", and the shell exports `SENTRY_SDK_DSN`.
- **[R] #437's breaking marker.** Data's `[Unreleased]` carries `equities_seq` 6.0.0 (a `dataset_id` change), and the notes renderer computes breaking = NO.
- **[R] `APD-DATA-055`'s `If-Match` half** (Appendix A).
- **[R] APD-ML-008's silent-path remedy:** a variable only the drift step sets.
- **[R] The register's five parked rows.** Its §4 notes (about L1626-L1630) park `APD-DATA-054`, `-055` and `-056`, and `APD-ML-007` and `-008`, as "filed 2026-09-24; awaiting an owner ruling, do not action". No round-42 handoff records asking them. This file carries `-055`'s `If-Match` half and `-008`'s remedy (above); ask all five together, each with its row's own question (the rows are at about L1301-L1305).
- **[R] The CodeQL blocks on #2089 and #2097, and #2081's** (Lane R asks for both open PRs, #2097's included).
  - #2089 (not armed): CodeQL failed at 00:27:51Z with 33 new alerts, 4 high (`py/overly-permissive-file` in `…/data438-fixforward-round1-laneB/stripe_probe.py`). It keeps 129 Python probes of six lanes; the 66 shell runners (48 `.bash`, 18 `.sh`) are not kept, and its README says why. The README also carries Lane F's four directory rows and its paragraph. At 02:39Z its second commit, `a64d72fe` (signed), added 73 probes of this session's six handoff-validation lanes (`handoff-2fba4397-round{1,2,3}-laneF`, `handoff-consolidated-round{1,2}-laneF`, `handoff-consolidated-round2-laneP`), among them `handoff-2fba4397-round3-laneF/probe_{data,cascor,primer}.py`, which measured Appendix A's (a) and (b). On `a64d72fe` CodeQL failed again at 02:43:16Z: 68 new alerts, the same 4 high. At 03:03Z a third commit, `669b2c75` (signed), added the round-3 lanes' 10 probes (`handoff-consolidated-round3-lane{F,P}`), for 216 files; its CodeQL runs again.
  - #2097 (Lane F's; not armed): at 01:23:44Z, 45 new alerts, 3 high (`py/clear-text-logging-sensitive-data` at `surrogate_config_probe.py:29` and `sentry_deep_probe.py:196`, `:201`, probe code logging values the probe sets itself). The same options and the same prohibition apply.
  - For #2081, two probe redactions were committed (`73dc109c`, `f9964d78`), its two highs were dismissed as "mitigated", and it merged. The `pcalnon` account that did this is shared by the owner and every session. Its 59 lesser alerts are still open on `main`.
  - The predecessor's options (a `paths-ignore` config, dismissal, or a tarball) were never ruled. For the first: `.github/workflows/codeql.yml` is advanced setup with `+security-and-quality`, and has no config file or `paths-ignore`.
  - Never dismiss alerts or edit preserved probes yourself. If the owner edits one, the README's "copied as the lanes wrote them" becomes false for it, and you must re-read #2089's head before any push to it.
  - #2089's README also carries Lane F's four probe-directory rows (#2097's probes), so those rows land only when #2089 does. If #2089 is ever rebuilt, keep them.
- **[R] The next juniper-data release.** 0.16.0 ships the defects #438 fixed. The next release carries #438, the fix-forward, data#440 and X8.
- **[R] FYI, not a question: MEMORY.md** is 24,929 characters (`wc -m`), about 70 under the HARD ~25,000-character load limit, past which the harness drops the tail. So every new row must be paid for. Compact by retiring entries (`feedback_memory_index_target_is_20kb.md`); only a structural change is the owner's.
- **[R/F] Worktree and branch cleanup** (Appendix F), each lane for its own worktrees.
- **FYI:** 0.16.0's notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. #2100's handoff (containers) carries it, as its item 2: route anything about it to that handoff's successor. The next data release will fail the same way until the owner fixes the token.
- **[R] The later arc items.** All are ruled; Lane R carries them. D-B (caching: data#428 and #438 merged, the fix-forward in flight) is under way: its rows stay open until the data fix-forward validates. C-A was started, and its forks were killed. The rest have not started. The order is §0 of `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`; the owner decides when.
  - **juniper-data:**
    - D-C, the error surface (`APD-DATA-030/-031/-022`): RFC 9457 from all three sources. Work 8's (a) belongs here.
    - D-D, lists and pagination (`APD-DATA-026/-027/-028/-008`).
    - D-E, idempotency (`APD-ECO-001`), after D-F.
    - D-F, storage pushdown (`APD-DATA-019`), after the data fix-forward merges, which rewrites `save_versioned` and the lock stripes in `storage/base.py` and `storage/local_fs.py`.
    - D-G (`APD-DATA-048/-049/-051`). `APD-DATA-047` was RATIFIED at 1e11 on 2026-09-21 and is closed.
    - D-B…D-D share `routes/datasets.py`; sequence them.
  - **The clients:**
    - C-A, a per-call timeout (`APD-ECO-003`): relaunch it fresh.
    - C-B, TypedDict responses (`APD-ECO-004`).
    - C-C, the recurrence client using its server's models (`APD-RCLIENT-004`).
    - C-A and C-B collide on 38 `def` lines; sequence them.
  - **Round 39 §0.4's two no-row items:**
    - `equities_seq`'s `data_quality` has no consumer in juniper-recurrence;
    - `val_ratio`'s removal from canopy's sidebar is recorded only in the register's §4.9 preamble.

## Appendix C: the data fix-forward (Lane R)

**State.** Branch `fix/conditional-requests-round4-followups` @ `94ce8b1fa8e229c92e8674a1074d518e59142488`, two signed commits on #438's merge `0f0f7e0e`, both pushed by executor `a46e715a6801b98ca`, which opened no PR. The data worktree is clean at `94ce8b1f`, in sync with `origin`.
- **`d1c66a11`** (its first push, at 20:45Z) answers every finding in `data438-round1-lane{A-reprobe,B-refute}.md`, two only partly (lane B's M2(b) and L2). data438's F8 is left to the owner; L5 and L7 are disclosed. Its numbers: unit 1901, coverage 97.76%, api+integration 118, harness "PASS: 70 mutations", equivalence 3,495,583 / 0.
- **Round 1 of the pre-PR validation REFUTED `d1c66a11`:**
  - `data438-fixforward-round1-laneA-reprobe.md`: 2 LOW, 9 NIT;
  - `data438-fixforward-round1-laneB-refute.md`: 1 MEDIUM, 5 LOW, 6 NIT.
  - **The MEDIUM was a regression the branch introduced.** `record_access` ran on the event loop (`call_soon`) and blocked on the process-global `_version_lock`, which `save_versioned` held for a whole save; every ecosystem client creates unnamed datasets. One 80 MB create froze the service for 6.6 s, against 0.01 s on `main`: past the readiness probe's 5 s timeout, which acts after three failures.
- **`94ce8b1f`** (parent `d1c66a11`, `verified: true`, pushed 01:46:46Z; the executor finished at 01:49Z) is the executor's answer to that round, **not yet validated** (Work 1). Its disposition report, `reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-fix-report.md`, says every finding is handled:
  - M-1 both halves: a create compresses and writes its artifact before taking any lock (`stage_save`), and `record_access` runs on its own single-thread executor, shut down on exit; `GET /{id}/access` waits for pending recordings.
  - It also found and fixed a regression of its own: holding the storage root open broke writes after the directory was deleted and recreated. The store now reopens the root by path (a new test and harness arm M86).
  - L-3 / lane A L-1 were documented, not remapped. Unparseable metadata stays a 400, and a timezone-naive cursor or `created_after` stays a 500; both are recorded as known issues, as is lane A N-9.
  - Its numbers: unit 1923 passed (7 subtests); coverage 97.60% (1783 passed, 140 deselected); api+integration 118; harness 89 arms PASS (132 caught, 0 vacuous, 135 controls OK); coverage counter 111/111 tests named, 100 must-fail; pre-commit on its 12 files; symbol-loss screen 2 findings, both waived; docs screen 19 warnings, 0 fail. The new test files fail 17 of 123 on `d1c66a11` and 39 on `0f0f7e0e`, each classified in the PR body. The equivalence sweep was not re-run: `http_cache.py` is untouched.
  - Lane B's probes, `d1c66a11` → `94ce8b1f`: slowest read during a create (the throughout-read variant, `util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py`) 7.4 s → 0.66-0.74 s; `xproc_stall_probe.py` GET 4.693 s → 0.011 s, health 4.686 s → 0.014 s; `stripe_probe.py` deletes on a full volume fail → succeed; `access_suppression_probe.py` count 0 → 1; `fault_survey.py` the same status on all 95 rows. `stall_probe2.py` cannot measure the new head.
- **Noticed by the executor, not changed** (round 2 weighs them):
  - a large create still blocks the event loop once, for about 0.73 s: `compute_checksum` runs on the loop (`datasets.py:446`; `:392` on `main`);
  - while `locks/` cannot be created, every lock repeats its warning;
  - `/access` and shutdown wait for the recorder with no time limit;
  - `local_fs.py` lines 175, 183, 237, 243-248 and 325-326 are untested defensive branches;
  - batch-create still logs a traceback for a symlinked metadata file, as `main` does;
  - a process that forks while a store is open shares the root's lock with its child;
  - the ad-hoc harness would reformat under `ruff format`.

**The squash body.** juniper-data squashes with `COMMIT_MESSAGES`, so the default squash body carries both commit messages. That keeps `94ce8b1f`'s waiver, but it also carries `d1c66a11`'s subject, whose "a storage fault is a 500" is the unscoped claim lane B L-3 and lane A L-1 scoped. Either merge with the default body and record that subject as residue, or hand-write the body, keeping the `Allow-Symbol-Loss:` line verbatim.

**PR text.** The final draft is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md`: `# <title>`, a blank line, then the body, re-copied at 01:50Z from the executor's last update (01:48Z). The tmpfs originals (`data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md` in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/`) hold the same text; the durable copy is the one to use. The body describes both commits; round 2's reports must be added to it before the PR opens.

**What `94ce8b1f` was asked to fix** (the spec round 2 checks against). The evidence is in the two round-1 reports, and their probes are on #2089.

MEDIUM:
- **Lane B M-1, with lane A L-2 and lane B L-4:** nothing on the event loop may wait on `_version_lock` or a stripe. Two creates stalled it 10.5 s.
  - Move `record_access` to a small dedicated executor, shut down in lifespan. `to_thread` would share the default pool with the routes' store I/O.
  - Log its exceptions by type only.
  - Consider writing the temp files before taking the locks; if that is too wide, say why and document the cost. (It chose a staged save.)
  - Pin it with a test: a read stays fast while another thread holds the lock.
  - Correct juniper-data's `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/constants.py:45-47` and `juniper_data/storage/local_fs.py:200-202`, and state the cost in `CHANGELOG.md`.

LOW:
- **Lane B L-1:** deletes on a volume out of inodes.
  - Add a lock fallback that needs no inode.
  - Remove legacy `*.meta.json.lock` files at startup: only files matching that exact pattern, directly inside the root.
  - Make the test double fail `mkdir` too.
  - Scope `CHANGELOG.md:93-94` and juniper-data's `docs/REFERENCE.md:1374-1375`.
- **Lane B L-2 / lane A N-4:** open `locks/` once, with `O_DIRECTORY|O_NOFOLLOW`, and open each stripe through `dir_fd`. Test live-target symlinks and the containment refusal (MX13, MX14, MX23, MX24).
- **Lane B L-3 / lane A L-1:** "a storage fault is a 500" is true only of a stored file that leads out of the storage root; scope it in the title, `CHANGELOG.md:117-118` and `juniper_data/api/routes/datasets.py:546-547`. Optional: map unparseable metadata to a 500, and refuse timezone-naive cursors. If skipped, record them as known issues.
- **Lane B L-5:** a two-process create test, a late named create, and a late create with different content (MX10, MX1, MX9).

NIT:
- lane B N-1 to N-6;
- lane A N-1, N-3, N-5, N-7, N-8 and N-9;
- `juniper_data/api/routes/datasets.py:1282`: `record_access` fires only on `GET /{id}` and the artifact download;
- the PR body's counts: 16 of 17 base failures are their own defect, and `[0.16.0]` is 261 lines;
- `[0.16.0]` stays byte-identical to the `v0.16.0` tag (`util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py`, on juniper-ml's `main`, can check it).

**The verification bar** (the executor's results are under State; round 2 re-runs what it can):
- unit; coverage; api+integration;
- the harness, extended with an arm per new fix; the harness-coverage counter;
- `juniper-symbol-loss-check --scope 'juniper_data/**' --base 0f0f7e0e`, and the docs screen;
- lane B's probes, against `d1c66a11` and the new head. As preserved on #2089 they do not run: `data438-fixforward-round1-laneB/common.py` pins `S` to the author's tmpfs scratch and starts servers through `S/scripts/run_in_tree.bash`, which is not kept. Re-point `S` at your lane's scratch. There, build its `head` and `main` trees with `git archive`, copy the preserved `serve.py` to `S/scripts/serve.py` (#2089 keeps it at the lane root, but `common.py:44` runs it from `S/scripts/`), and recreate `S/scripts/run_in_tree.bash`. The runner `cd`s into the tree; sets `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, `JUNIPER_DATA_API_KEYS=""` and the six DSN variables to `""`; checks that `juniper_data` imports from the tree; and execs JuniperData's python;
- pre-commit on every changed file, and the equivalence runs if `http_cache.py` is touched.

**Out of scope:**
- data438's F8 (#437's breaking marker, the owner's);
- L7 (a known issue);
- data428 round-3 A1 F2 and F4 (the closes PR files or declines them; A1's F3 is already `APD-DATA-056`);
- `juniper_data/api/security.py`, which Lane F's data#440 edits.

Lane R's branch owns juniper-data's `http_cache.py`, `routes/datasets.py`, `storage/*`, `test_conditional_requests.py`, `api/app.py`, `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, and it edits data's `CHANGELOG.md`. Lane F stays out of those. Lane F's data PR (F3, F5) also adds a `CHANGELOG.md` `[Unreleased]` entry: open it only after the fix-forward merges, or build it on the fix-forward's head, and update-branch before any merge.

## Appendix D: Lane F's work, in detail

**Evidence (#2097).**
- The reports, in `reports/2026-09-24_defect-register-round-42/`:
  - `bytes-compare-ml2086-data440-cascor689-{implementation-report,validation}.md`
  - `canopy683-{implementation-report,validation}.md`
  - `canopy685-implementation-report.md`
  - `cascor686-{implementation-report,fixup-implementation-report,validation}.md`
  - `cascor688-{implementation-report,validation}.md`
  - `cascor690-{implementation-report,fixup-implementation-report}.md`
  - `handoff-followup-lane-round*-*.md`
- **The 63 probes,** in `util/ad-hoc/2026-09-24_round42_probes/{cascor686-v686,canopy683-v683,cascor688-v688,bytes-compare-ml2086-data440-cascor689-vbytes}/`. Their README rows ride #2089. Treat them as evidence, and read each one's arguments before running it:
  - most take a tree (and a URL) as arguments, and some write under a `work/` or `out/` directory beside themselves;
  - `make_nv1_tree.py` deletes its second argument;
  - `fix_probe_pairs.py` rewrites a `compare_probe.py` in the working directory;
  - pass only fresh scratch paths.
- **The five harnesses:** `util/ad-hoc/2026-09-24_cascor688_*.py` and `2026-09-24_cascor690_*.py`.
- **The four scripts:** `2026-09-24_copy_followup_lane_probe_scripts.py`, `…_archive_followup_handoff_validation.py`, `…_open_followup_handoff_pr.py`, `…_serve_scratch_juniper_data.bash`.
- **Until #2097 merges,** none of these is in your worktree: read them from its branch with `git show origin/docs/handoff-round42-followup-lane:<path>`. Extract the cascor688 and cascor690 harnesses into ONE directory, because one imports another by path. The serve script runs `/opt/miniforge3/envs/JuniperData/bin/python` under `timeout 1500`, so it exits after 25 minutes.

**Item 1: validate cascor#690 post-merge** (branch `fix/shortfall-688-validation`; commits `c4e002d2` and `78e99414`, then the owner's account's merge of `main`, `81154187`; squash-merged UNVALIDATED at 02:06:36Z as `0fbb447a`).
- **What it is:** #688's fix-forward, answering the 2 MEDIUM, 3 LOW and 2 NIT findings in `cascor688-validation.md`.
- **How:** at least two lanes on the merged result, covering each commit's change. The implementer's evidence is not independent:
  - its reports: `cascor690-implementation-report.md` and `cascor690-fixup-implementation-report.md`;
  - harnesses for `c4e002d2`: `2026-09-24_cascor688_fixforward_mutation_check.py` and `…_cascor688_realjd_error_texts.py`;
  - harnesses for `78e99414`: `2026-09-24_cascor690_bool_stance_producer_table.py`, `…_realjd_probe.py` and `…_as_bool_stance_mutation_check.py`. The last imports the `cascor688_fixforward` harness by path.
- **Probes:** `…/cascor688-v688/`. The `probe_realjd_*.py` probes and both `realjd` harnesses need a live juniper-data. Serve one with `bash util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash <tree> <scratch-dir> <port>`.
  - `<tree>` must be a scratch export, never a checkout: `git -C <juniper-data clone> fetch origin main`, then `mkdir -p <tree>`, then `git -C <juniper-data clone> archive origin/main | tar -x -C <tree>`.
  - The script refuses a checkout. It keeps storage and imports in scratch, with the probes' `big.csv`, and inherits no keys, CSV-import cap or truncation switch. Metrics, rate limiting and Sentry are off.
  - Its final version was tested at 01:18Z with lower-case variants of the auth and cap variables set: `/v1/health` and an anonymous `/v1/generators` answered 200, the over-cap `csv_import` got juniper-data's real 422 refusal, and the checkout stayed clean.
  - Stop it with `pkill -A -f …`.
- **Then:** fix forward in a NEW PR from fresh `main`. Once its validation holds, CASCOR-008 and -013 can close.

**Item 2: validate canopy#685 post-merge at `dc5ea02e`**, with at least two lanes, and fix forward in a NEW PR from `main`.
- **What it closes:**
  - APD-ECO-014;
  - canopy's half of APD-ECO-013: the `str` `compare_digest` at `security.py:115`, `:273` and `csrf.py:91` became bytes at `:137`, `:300` and `csrf.py:97`;
  - `canopy683-validation.md`'s LOW3 and LOW4 (F-CANOPY-061/-062).
- **Report:** `canopy685-implementation-report.md`.
- The #685 worktree lacks the two probe-script commits, so validate `dc5ea02e` from a fresh tree.
- Fold into the fix-forward the stale comment at canopy `test_cascor_service_adapter_gate_coverage.py:49-50` (it says CI installs only the stub cascor client; it installs the real one), and any of the owner's calls (a)-(c) that change behaviour (Appendix B).

**Item 3: cascor#689 (`97341680`) and data#440 (`0bee089e`),** both from branch `fix/bytes-compare-no-500`, were VALIDATED before they merged (cascor#689 as `b9484fef` at 01:56:52Z, data#440 as `26491531` at 01:57:38Z):
- 0 failures over U+0000–U+10FFFF;
- 0 responses of 500 on real uvicorn;
- a timing profile that depends only on the configured key's length.

**Item 4: the F fix-forwards.** F1 was fixed by canopy#685. F8 (a `break` after `matched = True`) is killed by F3.

| Item | Sev. | Where | Fix |
|---|---|---|---|
| F2 | MEDIUM | observability `sentry.py` | `before_send_transaction=_strip_sensitive_headers`, with a test. Transactions skip `before_send`, so under `send_pii=True` (juniper-data only) they carry the raw `x-api-key`. |
| F3 | MEDIUM | service-core, data, cascor (canopy has one) | No CI test checks that `compare_digest` is used at all. Add a spy test: 2 or more keys, the match first, `len(calls) == len(keys)`, bytes arguments. In data, mark the existing and new spy tests `unit`, or use the marked `TestNonAsciiApiKey` (`:206`). `TestAPIKeyAuth` (`test_security.py:37`) is unmarked, and CI's `-m "unit and not slow"` (`ci.yml:287`) deselects it. |
| F4 | MEDIUM | cascor `src/tests/conftest.py` | After `import sysconfig` (line 37), set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN` and `SENTRY_DSN` to `""`. Do not unset them: `load_dotenv` re-injects. |
| F5 | LOW | `_ENCODING_PROBES` in service-core `tests/test_security.py:101`, data `juniper_data/tests/unit/test_security.py:34` (#440) and cascor `src/tests/unit/api/test_api_security.py:31` (#689) | Add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`, NOT U+1F511, which all three hold. The two collide under UTF-16-LE with `surrogatepass`, which is what kills the mutant. The "only total AND injective" comment is false. Check the file with `od -c`: the Write, Edit and SendMessage paths turn a typed escape into U+1F511. Canopy is out of scope: its `NON_ASCII` (`:172`) is checked only against a fixed `"key1"`, so the pair is inert there. Source: `bytes-compare-…-validation.md:63-64`, `:131`. |
| F6 | LOW | observability `tests/test_sentry.py` `_frames` | Add frames with `in_app: False` (the real frame is library code), plus one wire test with `in_app_exclude`. |
| F7 | LOW | cascor `test_main_sentry_no_local_variables.py` | Its AST test matches only the spelling `sentry_sdk.init`. Replace the AST match (`:33-35`) with a behavioural subprocess test: `get_client().options["include_local_variables"] is False`. This is a symbol loss: put `Allow-Symbol-Loss:` in a COMMIT body. |
| F9 | NIT | `juniper-service-core/CHANGELOG.md:57-58`; cascor's `CHANGELOG.md` (from #689) and #689's PR body | Write "rejected: ASGI close 4001, HTTP 403 on the wire", in the new cascor PR and its commit body; PATCH #689's body. data#440 carried no such text. |
| F10 | NIT | observability `CHANGELOG.md` | "Consumers inherit both on upgrade, with no code change" is false: every lock pins `==0.4.0`. |

**Release facts** (for Appendix B):
- **Locks** at `==0.4.0` (observability) / `==0.7.0` (service-core):
  - data `requirements.lock:88/:90`;
  - cascor `requirements.lock:63/:65`, and `requirements-cpu.lock:129/:133`, the lock its image installs (`Dockerfile:41-42`);
  - canopy `requirements.lock:79/:81`;
  - recurrence `juniper-recurrence/juniper-recurrence/requirements.lock:70/:74`.
- **Caps:**
  - observability `<0.5.0`: canopy `pyproject.toml:109`, recurrence `:79` and its client `:41/:46` (the recurrence ones in optional extras);
  - service-core `<0.8.0`: data `:110`, cascor `:105`, canopy `:119`, recurrence `:51`, juniper-ml `pyproject.toml:94` (`[tools]`).
- **Recurrence initialises no Sentry,** so for it the frame-locals fix is moot; it needs the service-core release.
- cascor#689 fixes only cascor's CLI init (`main.py`), not the service path at `src/api/app.py:335`, which goes through the shared `configure_sentry`.
- **Order** (`feedback_semver_beats_consumer_cap_2026-09-05.md`): a cap PR that a bump crosses lands BEFORE the Release. The lock and floor PRs come after the wheel is on PyPI.
- Record why `surrogatepass` was chosen over `surrogateescape`, from `bytes-compare-…-validation.md`.

## Appendix E: the fork-drift marker (Lane R; data#440 and cascor#689 have merged)

Measured by `handoff-2fba4397-round{1,2}-laneF-reprobe.md` at the PR heads (`0bee089e`, `97341680`); re-verify every anchor at `main` before coding. The "data#440" and "cascor#689" anchors below are those PRs' lines, now merged. Lane R agreed with Lane F (2026-09-25 00:21Z) to correct the gate's comment in this change.
- **Pin a PAIR:** `encode("utf-8", "surrogatepass")` and `compare_digest(presented,`.
  - Not the bare word `surrogatepass`. Every copy also carries it in a comment or docstring (service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`), and the matcher is a whole-file substring test (`tests/test_service_fork_drift.py:289`).
  - The code-only anchors: service-core `juniper_service_core/security.py:88`/`:91`; canopy `src/security.py:52`/`:137`; data#440 `:115`/`:118`; cascor#689 `:84`/`:87`.
- **Canopy's `.encode` sits only in `_compare_bytes`** (`:42-52`), which `:300` also uses. A revert to `presented = api_key` plus `compare_digest(presented, candidate)` at `:134-137`, keeping `_compare_bytes`, passes even the literal pair; F3's spy test, with its bytes-argument check, catches it. (A lone `presented = api_key` raises `TypeError` instead.)
- **Canopy's CSRF compare** (`src/csrf.py:91`, `:97`) is outside the site file.
- **Mutation-check the guard:** delete EVERY `.encode("utf-8", "surrogatepass")` in a copy of each site file (two each in service-core, data#440 and cascor#689; one in canopy, `:52`), and confirm the guard fails. The matcher is a substring test, so deleting only the first call leaves the marker in place.
- **PR CI will not catch a premature marker.** `ci.yml:500` runs the file but skips every fork site without siblings, so a premature marker merges green and fails the next weekly `docs-full-check` on `main`. Test with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` against a SCRATCH ecosystem root (11 OK today). The test walks up to the ecosystem root, and the shared juniper-data, juniper-cascor and juniper-canopy checkouts lag `origin/main`, so build the root: `git -C <clone> fetch origin main`, then `git -C <clone> archive origin/main | tar -x -C <root>/<repo>` for data, cascor and canopy, with your tree at `<root>/juniper-ml`.
- **The same change:**
  - corrects `tests/test_service_fork_drift.py:205-209`, "no behavioural test can tell them apart", which the F3 spy refutes: it counts `compare_digest` calls, so it kills F8 (a `break` after `matched = True`), which survives every suite today;
  - cites APD-ECO-013, so it lands with or after the closes PR;
  - updates every guard count: juniper-ml `docs/REFERENCE.md` about L2977, and the register about L240, L252, L1106 and L1751, plus its §2.3 guard table.

## Appendix F: worktrees and branches (remove only with the owner's go-ahead in your session)

The owner's go-ahead is required by `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md`. The table's worktrees are under `/home/pcalnon/Development/python/Juniper/worktrees/`; the two session worktrees are under `juniper-ml/.claude/worktrees/`. Before removing one, re-check `git status` and `gh pr view <N> --json state,mergedAt`.
- `juniper-ml/.claude/worktrees/fizzy-hugging-dream` (Lane R, "defect reg [24f8d8]"): holds three unsigned local scratch commits (never push them) and, until the consolidation PR merges, Lane R's files (Git status).
- `juniper-ml/.claude/worktrees/happy-skipping-hollerith` (Lane F, session `bc31e993`): no tracked changes; its 95 untracked files are #2097's. Keep it until #2097 merges.
- `juniper-ml/.claude/worktrees/hazy-beaming-map` (session `8f86dec2`, ended): document 3's worktree. No work would be lost; a cleanup candidate under this gate. Measured by round 3's lane F (`handoff-consolidated-round3-laneF-reprobe.md`, N-3):
  - its 16 `util/ad-hoc/2026-09-24_*` entries are 1 tracked script, 14 untracked scripts and 1 untracked directory. 12 of the untracked scripts are byte-identical to `origin/main`; the other two are earlier `main` versions (the archiver as at `22a6b7b5`, the pin check as at `f4d050c6`);
  - the directory, `2026-09-24_round42_probes/`, holds 203 files: 201 identical to `main`, and 2 pre-redaction copies that #2081 replaced (`73dc109c`, `f9964d78`);
  - its three tracked edits (register, primer, `docs/REFERENCE.md`) equal `5af9d722^1`, i.e. `main` just before #2088.
- **Dirty worktrees** (the four older rows below): diff each entry against the merged content of its PR, and name what removal would lose before you ask. `worktree remove` refuses a dirty tree; never `--force`.

| Worktree | Lane | State at writing |
|---|---|---|
| `juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2` | R | Holds the data fix-forward branch at `94ce8b1f`, clean. **Keep it** until that PR merges. |
| `juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c` | F | #690 merged. HEAD is `78e99414`, the PR's last commit before the owner's merge of `main`. Keep it until #690's validation holds. |
| `juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac` | F | #685 merged. HEAD is the unsigned `4caf9389`, tree-equal to `4a8af2a0`; the stray branches point there. |
| `juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb` | F | #689 merged. HEAD is the signed local `24103c23`, tree-equal to `97341680`. |
| `juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480` | F | #440 merged. HEAD is the unsigned `5bd5eec5`, tree-equal to `0bee089e`. |
| `juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227` | F | #683 merged. HEAD `8917fdac` is #683's commit; clean. |
| `juniper-ml--fix--sentry-locals-and-bytes-compare--20260924-1337--48fc09e5` | F | ml#2086 merged; clean. |
| `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2` | R | Older; awaits the cleanup signal. Dirty: 1 entry. |
| `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6` | R | Older; awaits the cleanup signal. Dirty: 16 entries. |
| `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6` | R | Older; awaits the cleanup signal. Dirty: 1 entry. |
| `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f` | R | Older; awaits the cleanup signal. Dirty: 5 entries. |

- **To remove one:** `git -C <owning repo> worktree remove <path>`, then `git branch -D <branch>`, then `git worktree prune`. For a juniper-ml worktree, run `git worktree remove <path>` from your own juniper-ml worktree. `worktree remove` also deletes ignored files, such as `logs/` and `snapshots/`.
- **Stale branches,** under the same gate:
  - the remote `fix/shortfall-mixed-provenance-and-678-followups` (`e452a660`, from the closed #686), and the local cascor branches of that name and its `-v2`. #686's commits stay at `refs/pull/686/head`, but deleting its head blocks reopening it.
  - canopy's `pr-63` and `pr-683` (Appendix B).

## Appendix G: documents the two sessions created or changed

- **Lane R** (session `2fba4397`):
  - **Merged in #2088 (14 files):**
    - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` and `docs/REFERENCE.md`;
    - `reports/2026-09-24_defect-register-round-42/register-fixforward2-round{1,2}-lane{A-reprobe,B-refute}.md`;
    - in `util/ad-hoc/`: `2026-09-24_register_round42_second_fixforward{,_corrections,_round2}.py`, `2026-09-24_register_primer_citation_census.py`, `2026-09-24_primer_toy_error_paths_probe.py`, `2026-09-24_primer_toy_pin_mutation_check.py` and `2026-09-24_archive_round42_reports.py`.
  - **On #2089 (216 files at `669b2c75`):** `util/ad-hoc/2026-09-24_round42_probes/README.md` and fourteen lane directories (`register-fixforward2-round{1,2}-lane{A,B}`, `data438-fixforward-round1-lane{A,B}`, and the eight handoff-validation directories), `util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py`, `util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py` and `util/ad-hoc/2026-09-24_push_round42_handoff_probes_to_2089.py`.
  - **In the consolidation PR:** the files listed under Git status, including this file. Among them is `reports/2026-09-24_defect-register-round-42/handoff-frozen/`: the eight frozen handoff copies the validation reports cite by line ("L<n>"), which were on tmpfs, and a `README.md` mapping each report's scratch path and sha256 to its file.
  - **Memory, outside the repo:** `reference_git_trailer_must_be_last_paragraph.md`, `reference_typed_escapes_become_real_characters.md` (new; linked from `reference_backticks_eaten_in_shell_messages.md`), `reference_backticks_eaten_in_shell_messages.md`, `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md` and `MEMORY.md`.
  - **On juniper-data's branch** `fix/conditional-requests-round4-followups` (its executor's): the 12 files of `94ce8b1f`, listed in `data438-fixforward-round1-fix-report.md`.
- **Lane F** (session `bc31e993`): #2097's 95 files; its merged PRs (cascor#688, #689 and #690, canopy#683 and #685, data#440, juniper-ml#2086, #2072 and #2077); and its memory edits: `feedback_validate_handoff_prompts_independently.md` (appended 2026-09-25 01:21Z) and, earlier in round 42, `MEMORY.md` and `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`.

## Appendix H: merge details

- **juniper-ml#2088** (`5af9d722`): from `ml2080-round1-laneA-reprobe.md` / `-laneB-refute.md`.
  - It was validated in two rounds before its PR opened, and its four reports shipped with it. Round 2's MEDIUM was a regression round 1's own fix introduced: a lone surrogate turned the primer toy's 422 into a plain-text 500. It is fixed, and so is the same class in the toy's list route.
  - At its head: harness 62/62; mutation check 12/12; probe 27/27; register 136 rows | 100 fixed | 36 open, AGREE. On the pre-merge primer (`c061a99f`) the probe differs in 25 cases under CPython 3.13.13, and 24 under 3.14.2.
  - Post-merge main verification and CodeQL passed, and the symbol screen honours its `Allow-Symbol-Loss` waiver.
- **juniper-ml#2081** (`7e8c7ff9`): the probe scripts of session `8f86dec2`'s lanes, off tmpfs.
- **juniper-data#438** (`0f0f7e0e`): #428's round-3 follow-ups.
- **juniper-cascor#688** (`7f4a7213`): #678's follow-up, carrying the owner's ruling "Keep while fetched splits stay (Recommended)". It supersedes #686: #687 conflicted, and the signing path cannot create the merge commit that would resolve that.
- **juniper-canopy#683** (`7ab994e5`): merged from `34e06747`, the validated `8917fdac` plus a `main` merge that overlaps it only in `CHANGELOG.md`, whose 60 non-blank lines all sit under `[Unreleased]`.
- **juniper-canopy#685** (`dc5ea02e`): merged from `e70b54dc`; the two commits after `4a8af2a0` touch only a probe script.
- **juniper-ml#2086** (`c061a99f`): service-core and observability. The bytes compare, `include_local_variables=False`, and frame `vars` dropped.
- **juniper-ml#2072 and #2077** (`ac912eba`, `6c23fdde`): Lane F's previous handoff and its reports, and the #686 and #688 harnesses. #2077's squash includes `095a2108`.
- **Merged by the owner's sweeper while this file was being validated (2026-09-25):**
  - **juniper-cascor#689** (`b9484fef`, 01:56:52Z) and **juniper-data#440** (`26491531`, 01:57:38Z), both validated before they merged.
  - **juniper-cascor#690** (`0fbb447a`, 02:06:36Z), **UNVALIDATED** (Work 2). The owner's account merged `main` into it (`81154187`) and armed it at 01:57Z.
  - Post-merge CI is green on data `26491531` and on cascor `0fbb447a` (02:16:38Z), which contains `b9484fef`. #690's push cancelled `b9484fef`'s own run.

## Appendix I: where each source item lives

- **Document 3 (the predecessor, stale),** as document 1's Appendix D mapped it:

  | Document 3 | Now |
  |---|---|
  | Completed (#2074, #2080, #2075, #438, v0.16.0, the archiving) | History: all merged or published. |
  | Remaining 1 (validate #438's fix) | Overtaken: #438 merged unfixed, so its fixes became the fix-forward (Work 1). |
  | Remaining 2 | Done as #2088. |
  | Remaining 3 | Appendix A. |
  | Remaining 4 (the canopy nit) | Handed off as F-CANOPY-060, reserved (Appendix A). |
  | Remaining 5 | Done by #2084. |
  | Remaining 6 | v0.16.0 is published, and #2081 merged; its CodeQL question and the rest are Appendix B. |
  | In flight 1 (executor `adf9f5dbe46b1b03c`) | Killed when `8f86dec2` ended; its work was rescued into the fix-forward branch. |
  | In flight 2 (#2081's CodeQL) | #2081 merged at 22:45:08Z (Appendix B). |
  | In flight 3 (Lane F) | Work 2-4, Appendices B and D. |
  | Traps | Key context and traps. |
  | C-A…D-G | Appendix B. |
  | Verification commands | Overtaken by this file's. |
  | Git status (worktree `hazy-beaming-map`) | Its scripts are all on `main`; the worktree is a cleanup candidate (Appendix F's gate). |
  | Appendix: `pending-items-snapshot-2026-09-24T1110Z.md` | Its "SECOND fix-forward" became #2088; its closes and residue items are Appendix A; its CodeQL items are Appendix B; the rest is done. |
- **Document 1 (Lane R):**

  | Document 1 | Here |
  |---|---|
  | Header and Goal | Header, Goal and the owner's policy |
  | First actions 1-4 | First actions 1-5 |
  | Completed | Merged, Open at writing, and Appendices A (the ruling), B (#2089's CodeQL), C and H |
  | In flight | In flight (finished) and Appendix C |
  | Remaining 0 | This consolidation |
  | Remaining 1 | First action 5, Git status |
  | Remaining 2 | Work 5, Appendix J |
  | Remaining 3 | Work 1, Appendices C and J |
  | Remaining 4 | Work 6, Appendices A and J |
  | Remaining 5 | Work 7, Appendix E |
  | Remaining 6 | Work 8, Appendices A and J |
  | Remaining 7 | Work 9, Appendix J |
  | Remaining 8 and Appendix B | Appendix B |
  | Appendix A | Appendix A |
  | Appendix C | Appendix C |
  | Appendix D | Appendix I, document 3 |
  | Appendix E | Appendix E |
  | Appendix F | Appendix G |
  | Traps | Key context and traps |
  | Verification commands | Verification commands |
  | Git status | Git status, Appendix F |

- **Document 2 (Lane F):**

  | Document 2 | Here |
  |---|---|
  | Header, "Which document governs" | Header |
  | Evidence | Appendix D, Evidence |
  | Step 0 | First actions 3 and 4, and the owner's policy |
  | Goal and split | Goal |
  | Merged | Merged, Appendix H |
  | OPEN 1-4 | Work 2-4, Appendix D |
  | OPEN 5 | Appendix B |
  | Coordination | the lane split, Appendices A, C and E, and Key context ("Archiving") |
  | Canopy ledger | Appendix A, Residue |
  | Release facts | Appendix D |
  | Traps | Key context and traps |
  | Worktrees and branches | Appendix F |
  | Verification commands | Verification commands |
  | Git status | Git status |

## Appendix J: steps for Work 1, 5, 6, 8 and 9

**Work 1: finish the data fix-forward** (Lane R; state in Appendix C).
- Run round 2 BEFORE opening the PR: two lanes on `94ce8b1f`, taking the new commit (`d1c66a11..94ce8b1f`) in full and the branch against `main` (`0f0f7e0e..94ce8b1f`) for regressions. Check it against both round-1 reports and the executor's disposition report. Its MEDIUM fix is a concurrency change: creates now stage before they lock, and `record_access` runs on its own single-thread executor.
- Open it with `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<draft line 1, without '# '>" --body-file <line 3 onward>`. Paste the title literally: `$(…)` feeding gh is refused. `open_signed_pr.py` refuses an existing branch.
- Merge it with your grant, and archive the reports. `94ce8b1f`'s message alone carries its waiver, `Allow-Symbol-Loss: method:LocalFSDatasetStore.save func:_file_lock_is_held`. The default squash message keeps it; a hand-written squash body that drops it turns `main` red (Appendix C, "The squash body").
- It and data#440 both edit `CHANGELOG.md` `[Unreleased]`, and #440 merged at 01:57Z (`26491531`). The executor found the two merge cleanly in either order; `strict: true` will make the PR update-branch onto `main`, so round 2 should also check the trial merge with data `main`.
- **If round 2 refutes, or returns corrections you apply before the PR** (LOW and NIT findings may instead be disclosed in the PR body as residue): brief a new `task-executor` in YOUR session on the same worktree. It makes one signed commit, with `--expected-head` set to the pushed head, and opens no PR; then run round 3. Its inputs: the round-2 reports, both round-1 reports, `data438-fixforward-round1-fix-report.md`, and `git diff 0f0f7e0e <head>`. Model its brief on the first executor's two `user` records, at 19:37:50.383Z (the regime: the upload proof, an unsigned LOCAL scratch commit so the screens can run, never pushed; a whole-file signed upload; the trailers; no PR) and 23:48:49.313Z (the round-1 fixes; a third plain-text record, at 00:29:28.847Z, is its compaction summary, not a brief), in `/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`; extract them with a script, never with `splitlines()`. Also pass the four tmpfs spec files if they still exist (`data_round3_original_brief.md`, `data_round4_spec.md`, `data_round4_redirect.md`, `old_executor_summary.md` in the author's scratchpad). Correct two things: `--expected-head` is the branch's current head, not brief 1's step 5, and the DSN variables are set to `""`, never unset (brief 2 says unset).
- **Where reports go:** archive them into the consolidation PR as a fixup while it is open (Archiving); otherwise into the closes PR or its follow-up.
- In the PR text, "round 2" must name the pre-PR validation round's reports (`data438-fixforward-round2-lane{A-reprobe,B-refute}.md`); the draft's own "## Round 2" heading is the executor's second fix round.

**Work 5: #2088's one unvalidated delta**, `990ef3f9..2439d049` (round 2's corrections). Its branch was deleted on merge; both commits stay reachable through `refs/pull/2088/head` (`1f116c38`, which is `2439d049` plus a `main` merge). Two lanes over the whole range; nothing waits on it and it waits on nothing. The checklist:
- primer lines 4199, 5330, 5378, 5399, 5455, 5464, 5600, 5618, 5622, 5658-5659, 5682, 5699, 6084-6087, 6091, 6117-6120, 9880 and 9943-9944;
- the register's `GET /{id}` wording, APD-CASCOR-013's Source cell, the §4 note, the rulings-block ids and APD-DATA-057's park bullet;
- the tools: the seven `util/ad-hoc/` files that `git diff --stat 990ef3f9 2439d049` lists.

Its fix-forward either merges before the closes PR opens, or rides in it, or, once the closes PR has merged, goes in the ONE register/primer follow-up from fresh `main`.

**Work 6: the closes PR** (Appendix A). Open it early. In it:
- file the three reserved rows OPEN, and make the APD-DATA-055 update;
- record the residue, Work 9's note on `2439d049`, and every Appendix B answer received by then;
- file Work 8's findings if they are verified by then.

Close each row only when its Appendix A gate clears (Work 1-4): in this PR while it is open, or later in ONE follow-up from fresh `main` at a time. The same holds for Work 7's register counts and for Appendix B answers that arrive after it merges.

Validate every register PR with two lanes: A re-derives every filed row and residue item from source at `main`; B refutes. A PR that only files rows OPEN and closes none may be validated after it merges, with a fix-forward. A PR that CLOSES a row is validated BEFORE it reaches a PR branch, because the sweeper merges a green PR. (Round 42's earlier register PRs: #2074 and #2080 were validated after merge and both refuted; #2088 was validated in two rounds before its PR opened.)

**Work 8: verify on the real services, then file** in the closes PR before it merges, or in a follow-up (Appendix A, "To file after verifying").
- (a) The 422-echo defect. Serve juniper-data with `util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash` (Appendix D); it runs JuniperData's python (fastapi 0.137.0, starlette 0.50.0), so record the pair you measured on. (Round 2 of this file's validation re-ran round 3's requests on that interpreter in-process: the same 400.) No cascor launcher is recorded: build one (an `origin/main` export in scratch, uvicorn on a free port, the DSN variables set to `""`), with a venv from cascor's `requirements-cpu.lock` for its locked pair (it pulls torch), or file cascor's half as measured in-process on 0.137.0 / 1.0.0.
- (b) The primer toy's copy of it; correct the primer IN PLACE.
- The primer's stale lines 4742-4743, in the same in-place edit.

**Work 9: PATCH two PR bodies** with `gh api -X PATCH`.
- juniper-ml#2080: the "A-nit on `APD-ML-008`" bullet (body L69, under "Rejected, with reasons", L65) was right (`ml2080-round1-laneA-reprobe.md` N6), and #2088 applied it. Delete body L69, and add this row to the "## Corrected" table (body L19-L41, columns `Finding (lane) | Where | Now`): `| A-nit | APD-ML-008: "the service-core sites still run" | Applied by #2088 (ml2080-round1-laneA-reprobe.md N6) |`.
- juniper-ml#2088: in body L47, replace "**Extended beyond the lanes:**" with "**Named by round-2 lane B** (`register-fixforward2-round2-laneB-refute.md` N11, line 120):". Record in the closes PR that `2439d049`'s commit message ("which no lane named") is false too.
