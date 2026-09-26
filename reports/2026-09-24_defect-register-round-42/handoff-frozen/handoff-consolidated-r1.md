# Handoff (CONSOLIDATED): defect-register round 42, both lanes. Validations, fix-forwards and the closes PR are owed

**Written:** 2026-09-25, about 01:35Z, by session `2fba4397` ("defect reg [24f8d8]"). Every "at writing" below means then.

**This document governs round 42's remaining work, in both lanes.** The owner asked on 2026-09-24 at about 23:25Z for three handoffs to be merged into one validated handoff, losing no task and no necessary context. It consolidates:
1. **The register lane's handoff:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
   - Session `2fba4397-7d9b-4929-8ca2-375b8168e1c8`, `ListAgents` name **"defect reg [24f8d8]"**, worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. That session wrote this file.
   - It was validated in three rounds, archived as `reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round*-*.md`.
2. **The follow-up lane's handoff:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, in juniper-ml#2097 (head `2e4917c2`).
   - Session `bc31e993-97b0-4a01-ae04-cb39593eb647`, **"defect reg [042116]"**, which wrote it and handed off. Never message it.
   - It was validated in 5 rounds, archived as `reports/2026-09-24_defect-register-round-42/handoff-followup-lane-round*-*.md`.
   - Its own predecessor, `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`, is carried by it and is not re-read here.
   - The lanes were split by "Split: old does follow-ups", relayed by the register lane (`defect reg [977fa8]`), and the owner's "Resume both here" in session `bc31e993` is consistent with it.
3. **Their common predecessor:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (session `8f86dec2`, on `main` via #2084). It is stale.

Documents 1 and 2 are now **evidence indexes**; this file's instructions replace theirs. Appendix I maps every item of all three to where it lives here.

**This file's own consensus validation** is archived as `reports/2026-09-24_defect-register-round-42/handoff-consolidated-round*-*.md`. It ships in the consolidation PR, on branch `docs/handoff-round42-consolidated`.

## Goal (paste the WHOLE document, appendices included, as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem.
- The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.

There are two work-streams:
- **Lane R (register):** the register and its closes PR; the API primer; the juniper-data fix-forward of #438; the fork-drift gate (`tests/test_service_fork_drift.py` and its `docs/REFERENCE.md` bullet); `MEMORY.md`; and the later arc items C-A…D-G.
- **Lane F (follow-up):** the cascor and canopy follow-ups, and the four "Key leaks" PRs. The owner's ruling "Fix everywhere now (Recommended)" ends "**Releases stay yours.**" So Lane F validates and fixes forward, and it surfaces releases rather than cutting them.

One successor should own both lanes. If the owner starts two sessions:
- split them by lane, and let each merge only its own lane's PRs;
- address each other by `ListAgents` name with the `[ref]` (several sessions are named "defect reg");
- send each other every PR number, merge SHA, validation summary and owner ruling (verbatim);
- Lane F stays out of the register, `tests/test_service_fork_drift.py`, `docs/REFERENCE.md`'s drift-gate section, `util/ad-hoc/2026-09-24_round42_probes/README.md` (#2089) and Lane R's juniper-data branch (Appendix C). Lane R stays out of `juniper_data/api/security.py` and Lane F's branches.

**The owner's policy:**
- The PR sweeper is theirs ("Mine: fix forward"): it un-drafts, arms and update-branches open PRs as `pcalnon`, and its merges are intended.
- Commits also appear on open PRs from that account: #2077 got `095a2108`, and canopy#685 got two. Do not draft or disarm a PR to hold it.
- An open PR can merge at any moment. When a validated merge matters, validate BEFORE the change reaches a PR branch (always, for F2 and F4); otherwise, validate after merge and fix forward.
- **Merge approval does NOT carry to a new session** (`feedback_headless_merge_approval_policy.md`). Get the owner's grant in YOUR session before any merge, arm or re-arm, and then only with checks green on the current head and the validators cleared.

**First actions, in this order:**
1. **Run the verification commands** below.
2. **Liveness.** While `ListAgents` lists "defect reg [24f8d8]" in any state but offline, treat its juniper-data executor as ALIVE (In flight 1): a live parent can resume a stopped executor. Until then:
   - do not touch the juniper-data worktree, and do not launch a second executor;
   - do not ship that session's uncommitted files;
   - never ask the owner to close that session, which would kill the executor.
3. **Find the other sessions.** Run `ListAgents`, loading it with ToolSearch if it is deferred.
   - Any session already working either lane from documents 1 or 2 is a successor, for example one following #2097's Step 0. Tell it this file governs, and agree the split; ask the owner if unsure.
   - Message "defect reg [24f8d8]" only if it is still listed.
4. **Get your own merge approval** from the owner.
5. **Land the three handoff PRs, with your grant:**
   - #2097 (Lane F's evidence);
   - the consolidation PR (this file, document 1, and Lane R's evidence);
   - juniper-ml#2089 (Lane R's probes), which is blocked by CodeQL; that is the owner's call (Appendix B).

   Find the consolidation PR with `gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-consolidated --state all`. If it does not exist, ship Lane R's files yourself (Git status).

**Merged, round 42, since 2026-09-23** (post-merge `main` CI green on all; details in Appendix H):
- **Lane R:** juniper-ml#2088 (`5af9d722`, 23:41:16Z), the second register and primer fix-forward, validated before its PR; juniper-ml#2081 (`7e8c7ff9`, 22:45:08Z), probe provenance; juniper-data#438 (`0f0f7e0e`, 18:52Z), which merged before its fix-in-place landed.
- **Lane F:** juniper-cascor#688 (`7f4a7213`, 18:56:25Z), superseding #686 (CLOSED); juniper-canopy#683 (`7ab994e5`, 19:10:20Z); juniper-canopy#685 (`dc5ea02e`, 23:24:14Z), **UNVALIDATED**; juniper-ml#2086 (`c061a99f`, 20:37:13Z); juniper-ml#2072 and #2077 (`ac912eba`, `6c23fdde`).
- **juniper-data 0.16.0** is on PyPI (18:35Z).

**Open at writing** (read live state from `gh`, never from this file's SHAs):
- juniper-ml#2089 (`a2fa3ad8`) and #2097 (`2e4917c2`);
- cascor#689 (`97341680`) and cascor#690 (`78e99414`);
- data#440 (`0bee089e`);
- Lane R's data branch `fix/conditional-requests-round4-followups` (`d1c66a11`), with no PR yet.

**In flight** (subagents of "defect reg [24f8d8]"; they die with it):
1. **Executor `a46e715a6801b98ca`** is fixing the data fix-forward's round-1 findings (Appendix C). One of them is a MEDIUM regression: `record_access` runs on the event loop, blocking on a lock that a whole save now holds, and one 80 MB create froze the service for 6.6 s.
   - It pushes ONE signed commit with `--expected-head d1c66a112e4bc70ee97496a14265f7b90e10fb88`, and opens no PR.
   - At about 01:15Z it had made its local scratch commit (`[ahead 1]`) and was verifying.
   - Its transcript is `/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`.
     - Its **disposition report** is the last assistant message. Read it with `last_report()` from `util/ad-hoc/2026-09-24_archive_round42_reports.py`, loaded with `importlib`; never read it with `splitlines()`.
     - Its **brief** is TWO `user` records. 19:37:50.383Z is the task: the regime, the upload proof, an unsigned LOCAL scratch commit, the trailers, the PR prohibitions, and four scratchpad spec files. 23:48:49.313Z is the round-1 fixes, which relies on the first.
   - **Dead only if** "defect reg [24f8d8]" is gone AND the transcript is 30+ minutes old. It went 600 s without a write while alive.
   - **If it died:** run `git -C <data worktree> status -sb`.
     - A dirty tree, or `[ahead N]` (an unsigned scratch commit: NEVER push it), with the remote ref still `d1c66a11…`, means the work is unfinished.
     - Extract both briefs with a script, then launch a new `task-executor` on that worktree with them, both round-1 reports and the drafts.
     - Tell it to review `git diff origin/fix/conditional-requests-round4-followups` first, and to push with the full `--expected-head`. A dead subagent cannot be resumed from another session.

**Work, in order** (details in the appendices):
1. **[R] Finish the data fix-forward** (Appendix C).
   - Check the executor's commit against both reports and its disposition report. Its MEDIUM fix is a concurrency change.
   - Run round 2 (two lanes, on `d1c66a11..<new head>`) BEFORE opening the PR.
   - Open it with `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<draft line 1, without '# '>" --body-file <line 3 onward>`. `open_signed_pr.py` refuses an existing branch.
   - Merge it with your grant, and archive the reports.
   - It and data#440 both edit `CHANGELOG.md` `[Unreleased]`: re-check that they merge cleanly.
2. **[F] Validate cascor#690**, both commits (`c4e002d2`, `78e99414`), then fix forward (Appendix D, item 1).
3. **[F] Validate canopy#685 post-merge** at `dc5ea02e`, then fix forward in a NEW PR from `main` (Appendix D, item 2).
4. **[F] The F fix-forwards** from the bytes-compare validation (Appendix D, items 3-4):
   - one juniper-ml PR for F2, F6, F9, F10 and service-core's F3 and F5;
   - cascor#689 fixups for F3, F4, F5, F7 and F9;
   - data#440 fixups for F3 and F5.

   Validate each with two lanes. F2 and F4 are validated BEFORE they reach a PR branch.
5. **[R] Validate #2088's one unvalidated delta**, `990ef3f9..2439d049` (round 2's corrections), with two lanes over the whole range; archive their reports, then fix forward. The checklist:
   - primer lines 4199, 5330, 5378, 5399, 5455, 5464, 5600, 5618, 5622, 5658-5659, 5682, 5699, 6084-6087, 6091, 6117-6120, 9880 and 9943-9944;
   - the register's `GET /{id}` wording, APD-CASCOR-013's Source cell, the §4 note, the rulings-block ids and APD-DATA-057's park bullet;
   - the tools.
6. **[R] The closes PR** (Appendix A), gated on items 1-4.
7. **[R] The fork-drift marker** (Appendix E), after data#440 and cascor#689 merge.
8. **[R] Verify on the real services, then file** (Appendix A, "To file after verifying"):
   - (a) the 422-echo defect;
   - (b) the primer toy's copy of it;
   - the primer's stale lines 4742-4743.
9. **[R] PATCH two PR bodies** with `gh api -X PATCH`:
   - juniper-ml#2080: the "A-nit on `APD-ML-008`" bullet (body L69, under "Rejected, with reasons", L65) moves to the applied items, citing #2088 (`ml2080-round1-laneA-reprobe.md` N6).
   - juniper-ml#2088: "Extended beyond the lanes" is false, because `register-fixforward2-round2-laneB-refute.md` N11 (line 120) named the list-route defect. Record in the closes PR that `2439d049`'s commit message ("which no lane named") is false too.
10. **Owner decisions:** Appendix B. Surface them; decide none.

## Key context and traps (part of the prompt)

**Uploads, commits and merges:**
- **Uploads are WHOLE-FILE, and files move under you.**
  - Before every push, `git fetch` and run `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`. Compare with `git show origin/main:<p> | diff - <p>`.
  - For a shared `CHANGELOG.md` `[Unreleased]`, prove `main`'s lines are a subset of yours.
- **Signed commits have ONE parent** (GraphQL `createCommitOnBranch`), so a textual conflict cannot be merged away. Supersede from fresh `main`, as #686 → #688 did.
- **Signed pushes.** Use `util/push_signed_commit.py --expected-head <FULL 40-hex sha, from gh>`.
  - Never pass `git rev-parse HEAD`: in several worktrees HEAD is a local copy, not the PR head.
  - A run can create nothing, so check the remote ref afterwards. A re-run with the same head is safe.
  - `--commit-body "$(cat f)"` is accepted.
- **Where fixes go.** An OPEN PR gets a signed fixup. A MERGED PR gets a new PR from fresh `main` (`util/open_signed_pr.py`). Read each PR's state with `gh pr view <N> --json state,headRefOid,mergeCommit` at push time.
- **Squash bodies.** The sweeper stores the DEFAULT squash body, and GitHub appends a `Co-authored-by` paragraph.
  - Put waiver trailers (`Allow-Symbol-Loss:`) in a COMMIT body in the range; main-verify's line-scanning regex finds them there.
  - `git log -1 --format='%(trailers:key=…)'` on a squash prints an empty line; check with `grep -c`.
  - A curated re-arm is `gh pr merge --disable-auto`, then `--auto --squash --subject … --body-file …`. It needs your grant, and `--auto` on a MERGEABLE PR merges at once.
- **`strict: true`:** after every move on `main`, run `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<full sha>`.
  - Run update-branch BEFORE building a CHANGELOG over a release cut: a 3-way merge once duplicated `## [0.16.0]` silently.
  - `gh pr edit` is broken; use `gh api -X PATCH`.

**The register and the primer:**
- **Never name an OPEN id on the register's §2 status line** (about L176): the crosscheck reads every id there as closed.
- **The primer is cited by bare line number: edit it in place only.**
  - Model a new editor on `util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py`, which refuses to run twice and refuses any line move.
  - `util/ad-hoc/2026-09-24_register_primer_citation_census.py` counts every bare number past 5758 (69 citations, 82 numbers today). Name a retired anchor in words.
  - The harness is `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>`, which gives 62 tests. `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` needs `--venv` and `--scratch`.
  - The venv: CPython 3.13.13 (JuniperCanopy1's interpreter), fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2. The copy at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv` is on tmpfs.

**Running lanes and archiving their reports:**
- **How to run a lane:** a background `general-purpose` Agent.
  - Launch the lanes in ONE message: A re-derives every claim from source; B refutes, defaulting to REFUTED.
  - Give each its own scratch subdirectory.
  - Tell each: read-only; no secret or email egress; compound shell in a script; prune `/tmp`.
  - Report format: as in `register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
- **Archiving** uses `util/ad-hoc/2026-09-24_archive_round42_reports.py`.
  - Add your session's full UUID (the directory above your scratchpad) to `SESSION_IDS`, and each report to `MISSING`.
  - `HEADER` hard-codes 2026-09-24: change it for new reports.
  - Run `--check`, then run it without. The header is `<!-- Archived verbatim YYYY-MM-DD from subagent a<16 hex> of session <8 hex> (final message). -->` followed by a blank line.
  - Four Lane F reports are headed "(turn-ending report k of 5 …)", and `--check` skipping them is expected: `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`. Byte-compare those against their agents' transcripts by hand before citing them.
- **Agents.** A usage limit kills subagents; resume each with SendMessage, only from the session that spawned it. An agent the USER stopped cannot be resumed: relaunch it fresh from its WIP.

**Environment:**
- **Sentry:** set `SENTRY_SDK_DSN` (this shell exports it), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to `""` in every test run and server. Set them empty, never unset: `load_dotenv` re-injects. Never use port 8100, 8201 or 8050.
- **/tmp is a ~1M-inode tmpfs** (83% at writing; it hit 100% on 2026-09-24). Extract only what you need, prune, and keep probes in `util/ad-hoc/`.
- **`pkill -f '<pattern>'` also matches the shell running it.** Use `pkill -A -f …`, or bracket one character (`'…1879[7]'`). A pattern that starts with `-` needs `--`.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage (a backslash-u escape of U+2028, or of a surrogate pair). Build such text with `chr()`, and check it with `od -c`.
- **The worktree sandbox's refusals are heuristic.** Refused this round:
  - `$(...)` feeding git or gh; loops around git or gh, or a `for` loop with a variable inside a `gh` argument;
  - backticks inside heredocs;
  - the word "git", in any case, inside a `python3 -c` string or a `for` word list;
  - a `-C` path relative to a `cd`, and sometimes a computed `git -C "$d"`;
  - variables around `sed` or `find`; sometimes, `env -u` inside a compound command;
  - `bash -c` with computed text;
  - `git -C`, or `cd … &&` git, into the shared juniper-ml checkout or another worktree under `juniper-ml/.claude/worktrees/`. Read files there with `cat`.

  Use plain separate commands with absolute paths, or a script under `util/ad-hoc/`.
- **Never run** `util/worktree_cleanup.bash` (it pushes and runs `gh pr create`, which recreates deleted remote branches with unsigned commits), nor `util/remove_stale_worktrees.bash` (it has no staleness predicate).
- **Other sessions:** "canopy combined [577a1c]" and "containers [2703c8]". The canopy E2E session has exited.

## Verification commands
Run them from any juniper-ml worktree. Where a path is absolute, `cat` it; do not use `git -C` into another juniper-ml worktree.
```
gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-consolidated --state all --json number,state,mergeCommit   # this file's PR
gh pr view 2097 --repo pcalnon/juniper-ml --json state,headRefOid,mergeCommit    # Lane F's evidence; OPEN at writing
gh pr view 2089 --repo pcalnon/juniper-ml --json state,headRefOid,mergeStateStatus   # OPEN, BLOCKED (CodeQL) at writing
gh api graphql -f query='query { a: repository(owner:"pcalnon", name:"juniper-cascor") { p690: pullRequest(number:690) { state headRefOid mergeCommit { oid } } p689: pullRequest(number:689) { state headRefOid mergeCommit { oid } } } b: repository(owner:"pcalnon", name:"juniper-canopy") { p685: pullRequest(number:685) { state headRefOid mergeCommit { oid } } } c: repository(owner:"pcalnon", name:"juniper-data") { p440: pullRequest(number:440) { state headRefOid mergeCommit { oid } } } }'
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # d1c66a11… until the executor pushes
gh pr list --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --state all   # none at writing
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status -sb   # [ahead N] = an unsigned scratch commit: never push it
find /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/ -name agent-a46e715a6801b98ca.jsonl -mmin -30   # printed = written in the last 30 min
cat /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md | head -3   # document 1, until it ships
gh pr checks 2089 --repo pcalnon/juniper-ml | grep -i codeql   # fail at writing
gh pr list --repo pcalnon/juniper-data --state open; gh pr list --repo pcalnon/juniper-cascor --state open
git fetch origin && python3 util/ad-hoc/register_open_set.py | grep 'rows |'    # 136 rows | 100 fixed | 36 open, until the closes PR; reads YOUR worktree's register
python3 util/ad-hoc/register_status_crosscheck.py | tail -1   # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c -e DIFFER -e REFUSE   # 0; it exits early if a cited transcript is gone
python3 -m unittest tests/test_service_fork_drift.py   # 11 OK, 3 skipped; with JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 and the siblings pulled: 11 OK
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -e shortfall-mixed -e secret-leaks -e bytes-compare -e blank-key-678 -e sentry-locals -e round3-followups   # Lane F's six, plus Lane R's data worktree
df -i /tmp | tail -1
```

## Git status at writing
- **Lane R, worktree `fizzy-hugging-dream`** (branch `worktree-fizzy-hugging-dream`).
  - It holds three unsigned LOCAL scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`): **never push or commit here.** Their content is #2088's.
  - Its uncommitted files ship in the consolidation PR. They are:
    - the extractor `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (`--topic key-leaks`);
    - the archiver's new `MISSING` entries;
    - `reports/2026-09-24_defect-register-round-42/{owner-ruling-key-leaks-verbatim, data438-fixforward-round1-laneA-reprobe, data438-fixforward-round1-laneB-refute, data438-fixforward-pr-draft}.md`;
    - the `handoff-2fba4397-*` and `handoff-consolidated-*` validation reports;
    - the executor's `util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py`;
    - documents 1 and this file.
  - #2089's files are also untracked there, and must stay OUT of every other PR: `util/ad-hoc/2026-09-24_round42_probes/`, `…_copy_round42_session2fba4397_probe_scripts.py` and `…_open_round42_session2fba4397_probes_pr.py`, byte-identical to `a2fa3ad8`.
  - **To ship them yourself:** use `util/open_signed_pr.py`. The worktree is 5 commits behind `origin/main`, so rebuild each file from `origin/main` first. Check that no open juniper-ml PR carries these paths. Put `Allow-Symbol-Loss: const:SESSIONS` in the commit body: the extractor renames `SESSIONS` to `SESSION_IDS`.
  - Until the consolidation PR has merged, never `reset`, `checkout`, `clean`, `stash` or remove that worktree.
- **Lane R, juniper-data worktree** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2`. Its name says round3, but it holds `fix/conditional-requests-round4-followups` with the executor's work. **Do not remove it.**
- **Lane F, worktree `happy-skipping-hollerith`**: fast-forwarded to `5af9d722`, clean. Every new file of Lane F is in #2097.
- **Worktrees and stale branches:** Appendix F. Remove any only with the owner's go-ahead in your session.

## Appendix A: the closes PR (Lane R)

**Gates.** Close a row only after its PR merges AND its own validation holds.
- `APD-CASCOR-008` / `-013`: they wait for cascor#690 to merge and validate (Work 2).
- `APD-DATA-017` / `-029` / `-032` / `-057`: data#438 merged; the fix-forward (Work 1) must merge and validate.
- `APD-ECO-014`, canopy's half of `APD-ECO-013`, and F-CANOPY-061/-062's FIXED-BY: canopy#685's post-merge validation (Work 3).

**File** (the three ids are reserved, not yet filed):
- **`APD-ECO-013` (S).** A non-ASCII `X-API-Key` makes the `str` `compare_digest` raise; the 500 goes to Sentry, and its local-variable capture records the real key.
  - Fixes: juniper-ml#2086 and canopy#685 (merged); data#440 and cascor#689 (open).
  - **It stays open until** data#440 and cascor#689 merge, #685's validation holds, and F2 and F3 are fixed. Both lane handoffs agree.
  - F5-F10 go on the row as residue unless they are fixed first (Appendix D, item 4).
  - Source: `bytes-compare-ml2086-data440-cascor689-validation.md` (#2097).
- **`APD-ECO-014` (S):** canopy's padded outbound keys leaked into logs, into Sentry and into a 409 body, including an ANONYMOUS read of the cascor key via `POST /api/train/start` with auth on. File it OPEN, with canopy#685 as its fix; close it once #685's validation is cited.
- **`APD-CASCOR-014` (S),** Lane F's F4: cascor tests that `import main` start the REAL Sentry SDK when a DSN is exported. 9 files sent 25 envelopes to a sink.
  - The cause: `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` → `src/main.py:231`.
  - The fix: F4 (Appendix D).
  - cascor#689's `include_local_variables=False` strips the locals, but the events are still sent.
  - File it OPEN; close it when F4's fix merges and its validation holds.

**Update, do not close:** `APD-DATA-055`. #438 fixed its lock half: at data `0f0f7e0e`, `batch_delete` and `delete_expired` go through `delete_under_lock`. Its `If-Match` half awaits the owner's ruling.

**Quote** the "Key leaks" ruling verbatim from `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`, extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks`. It was asked at 10:22:00.792Z and answered at 18:30:09.820Z: "Fix everywhere now (Recommended)".

**Residue to record:**
- **cascor shortfall messages.** The flag-off 422 is no longer shown as a shortfall (#688). A juniper-data 400 for a bad param still is. cascor#690 fixes that by keying on "Re-submit with allow_truncation=true". It also makes `_as_bool_stance` parse as juniper-data's `str_as_bool` does; the old reader read `"f"` and `"n"` as true.
- **Auto-start binds wholesale** (`cascor686-fixup-implementation-report.md` item 2; `pending-items-snapshot-2026-09-24T1110Z.md:40`).
- **`current_dataset` after a partial inline start** names the fetch, as the ruling intends; canopy reads only `.dataset_type`. Record, no row.
- **canopy#683 item 3** is a disclosed behaviour change: a whitespace-only env key makes `/docs` answer 200.
- **A retire condition met.** juniper-canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its condition. Record only: retiring an ad-hoc script is the owner's decision.
- **Already recorded:** cascor#678's stale squash message (register, about L1616).
- **F9's residue:** cascor squashes with `COMMIT_MESSAGES`, so #689's first commit message ("4001 close") reaches `main` anyway.
- **Canopy items,** which go to the canopy E2E ledger, not the register:
  - F-CANOPY-060, -061 and -062 were reserved at 19:40:28Z in `…/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md:53-66`. It is untracked there, and its bytes are on branch `docs/canopy-e2e-handoff-2026-09-24`, with no PR.
    - 060: the refusal cut at `" The resulting dataset"` (`dashboard_manager.py:8410`) drops juniper-data's last sentence. It has no owner.
    - 061 and 062: LOW3 and LOW4, fixed by #685, pending its validation.
  - The fourth item, with no id, recorded by canopy combined at 20:45:53Z: canopy's copies of #687's "Nothing was loaded" sentence, at canopy `7ab994e5` `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` and `src/frontend/dashboard_manager.py:8381`.
    - They go stale when #690 merges: cascor `main` emits the sentence at `manager.py:4766`, and #690 rewords it at `:4841`.
    - Recorded in `…/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`.
  - All of these are in other sessions' worktrees: read only.
- **canopy#685's residue:**
  - the frame-locals gap until the release (Appendix B);
  - the owner calls (a)-(c) (Appendix B);
  - the anonymous rate-limiter 500 needs `rate_limit_enabled`, which is off by default;
  - a stale comment at canopy `test_cascor_service_adapter_gate_coverage.py:49-50` says CI installs only the stub cascor client. It installs the real one. It can ride any later canopy PR.
- **data428 round 3** (`data428-round3-laneA1-security.md`). F3 is `APD-DATA-056`. F2 (the 8,192-byte cap, parsed under `_version_lock`) and F4 (header limits) are recorded nowhere: file or decline each, with a reason.
- **Cite Lane F's archived reports** (#2097) by filename.

**To file after verifying on the real services** (Work 8; measured in-process by `handoff-2fba4397-round2-laneF-reprobe.md`):
- **(a)** A 422 that echoes the input through Starlette's `JSONResponse` (`ensure_ascii=False`) raises `UnicodeEncodeError` on a lone surrogate. That is a `ValueError`, so the outcome depends on the app's handlers:
  - FastAPI's default app: a plain-text 500.
  - juniper-data (`juniper_data/api/app.py:187-212`, `ValueError` handler `:214`): 400 `{"detail":"Invalid request parameters"}`. The per-field detail is lost, and no Sentry event is sent.
  - cascor (`src/api/app.py:856`, `:916`): expected to be the same, but not run.
  - It is a sibling of `APD-DATA-056`, and input to D-C.
- **(b)** The primer's `idempotent_jobs.py` has (a)'s default-handler form. A lone surrogate in `dataset_id` fails validation (`string_unicode`); the default 422 cannot render it, so the client gets a plain-text 500, again on retry. No key record is ever created, so there is no replay defect. Correct the primer IN PLACE, together with its lines 4742-4743, which say juniper-data registers no such handler, stale since data#281.

## Appendix B: owner decisions (surface them; decide none)

Ask each with verbatim options. Record the question, the options and the answer in the register.
- **The releases. "Releases stay yours."** Until juniper-observability and juniper-service-core ship, and the consumers' locks move, the frame-locals fix reaches no running service. `canopy685-implementation-report.md` measured it: any unhandled exception during a keyed request records the caller's key.
  - **Ask only after Lane F's juniper-ml F-PR validates.** An earlier release ships F2's leak and F10's false sentence.
  - The options:
    1. the owner prepares and cuts both releases; or
    2. an agent opens version-bump and release-notes PRs at versions the owner names, and the owner cuts the Releases.
  - Ask separately who opens the cap, lock and floor PRs (Appendix D, "Release facts").
  - Never approve a deploy gate (`feedback_deploy_approvals_paul_manages.md`).
- **canopy#685's judgement calls:**
  - (a) An error that carries an HTTP status still passes its upstream text through. Making it type-only is a one-line change in `src/outbound_errors.py:57-61`.
  - (b) The key rule refuses a space or tab inside a key, which the clients would send.
  - (c) A blank `*_API_KEY_FILE` that shadows a real env var now sends no key.
- **Two stray canopy branches,** `pr-63` and `pr-683`, both at the unsigned `4caf9389`, the #685 worktree's local commit.
  - They were pushed at 22:55Z, have no PR, and no agent transcript records the push.
  - That worktree's upstream is `refs/heads/pr-683`. A plain `git push` refuses; an IDE push, or `HEAD:pr-683`, lands on it.
  - Do not delete them unasked.
- **The live Sentry project may hold this round's test events.** One run ended "Sentry is attempting to send 2 pending events".
- **#437's breaking marker.** Data's `[Unreleased]` carries `equities_seq` 6.0.0 (a `dataset_id` change), and the notes renderer computes breaking = NO.
- **APD-ML-008's silent-path remedy:** a variable only the drift step sets.
- **#2089's CodeQL block, and #2081's.**
  - #2089: 33 new alerts, 4 high (`py/overly-permissive-file` in `…/data438-fixforward-round1-laneB/stripe_probe.py`).
  - For #2081, two probe redactions were committed (`73dc109c`, `f9964d78`), its two highs were dismissed as "mitigated", and it merged. The `pcalnon` account that did this is shared by the owner and every session. Its 59 lesser alerts are still open on `main`.
  - The predecessor's options (a `paths-ignore` config, dismissal, or a tarball) were never ruled.
  - Never dismiss alerts or edit preserved probes yourself. If the owner edits one, the README's "copied as the lanes wrote them" becomes false for it.
  - #2089's README also carries Lane F's four probe-directory rows (#2097's probes), so those rows land only when #2089 does.
- **The next juniper-data release.** 0.16.0 ships the defects #438 fixed. The next release carries #438, the fix-forward, data#440 and X8.
- **MEMORY.md** is 24,929 characters (`wc -m`), about 70 under the HARD ~25,000-character load limit, past which the harness drops the tail. So every new row must be paid for. Compact by retiring entries (`feedback_memory_index_target_is_20kb.md`); only a structural change is the owner's.
- **Worktree and branch cleanup** (Appendix F).
- **FYI:** 0.16.0's notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. The containers session owns it.
- **The later arc items.** All are ruled; Lane R carries them. D-B is in flight: its rows stay open until the data fix-forward validates. C-A was started, and its forks were killed. The rest have not started. The order is §0 of `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`; the owner decides when.
  - **juniper-data:**
    - D-C, the error surface (`APD-DATA-030/-031/-022`): RFC 9457 from all three sources. Work 8's (a) belongs here.
    - D-D, lists and pagination (`APD-DATA-026/-027/-028/-008`).
    - D-E, idempotency (`APD-ECO-001`), after D-F.
    - D-F, storage pushdown (`APD-DATA-019`), after the data fix-forward merges, which rewrites `save_versioned` and the lock stripes.
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

**State.** Branch `fix/conditional-requests-round4-followups` @ `d1c66a112e4bc70ee97496a14265f7b90e10fb88`, whose parent is #438's merge.
- It answers every finding in `data438-round1-lane{A-reprobe,B-refute}.md`, two only partly (lane B's M2(b) and L2). data438's F8 is left to the owner; L5 and L7 are disclosed.
- Its numbers: unit 1901, coverage 97.76%, api+integration 118, harness "PASS: 70 mutations", equivalence 3,495,583 / 0.
- **Round 1 of its pre-PR validation REFUTED it:**
  - `data438-fixforward-round1-laneA-reprobe.md`: 2 LOW, 9 NIT;
  - `data438-fixforward-round1-laneB-refute.md`: 1 MEDIUM, 5 LOW, 6 NIT.
- **The MEDIUM is a regression the branch introduces.** `record_access` runs on the event loop (`call_soon`) and blocks on the process-global `_version_lock`, which `save_versioned` now holds for a whole save; every ecosystem client creates unnamed datasets. One 80 MB create froze the service for 6.6 s, against 0.01 s on `main`: past the readiness probe's 5 s timeout, which acts after three failures.

**PR text.**
- The drafts are on tmpfs: `data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md` in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/`. The executor updates them.
- The durable copy is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md` (`# <title>`, a blank line, the body). It was taken at 00:27Z, before the executor's update. Re-copy it with a script once the executor finishes.
- If neither survives, rebuild the body from the two reports and the executor's disposition report.
- The old title's "a storage fault is a 500" is true only of a file that leads out of the storage root.

**What the executor was asked to fix.** The evidence is in the two reports, and the probes are on #2089.

MEDIUM:
- **Lane B M-1, with lane A L-2 and lane B L-4:** nothing on the event loop may wait on `_version_lock` or a stripe. Two creates stalled it 10.5 s.
  - Move `record_access` to a small dedicated executor, shut down in lifespan. `to_thread` would share the default pool.
  - Log its exceptions by type only.
  - Consider writing the temp files before taking the locks; if that is too wide, say why and document the cost. Its probe `util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py` shows it chose a staged save.
  - Pin it with a test: a read stays fast while another thread holds the lock.
  - Correct juniper-data's `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/constants.py:45-47` and `juniper_data/storage/local_fs.py:200-202`, and state the cost in `CHANGELOG.md`.

LOW:
- **Lane B L-1:** deletes on a volume out of inodes.
  - Add a lock fallback that needs no inode.
  - Remove legacy `*.meta.json.lock` files at startup: only files matching that exact pattern, directly inside the root.
  - Make the test double fail `mkdir` too.
  - Scope `CHANGELOG.md:93-94` and `docs/REFERENCE.md:1374-1375`.
- **Lane B L-2 / lane A N-4:** open `locks/` once, with `O_DIRECTORY|O_NOFOLLOW`, and open each stripe through `dir_fd`. Test live-target symlinks and the containment refusal (MX13, MX14, MX23, MX24).
- **Lane B L-3 / lane A L-1:** scope "a storage fault is a 500" in the title, `CHANGELOG.md:117-118` and `juniper_data/api/routes/datasets.py:546-547`. Optional: map unparseable metadata to a 500, and refuse timezone-naive cursors. If skipped, record them as known issues.
- **Lane B L-5:** a two-process create test, a late named create, and a late create with different content (MX10, MX1, MX9).

NIT:
- lane B N-1 to N-6;
- lane A N-1, N-3, N-5, N-7, N-8 and N-9;
- `juniper_data/api/routes/datasets.py:1282`: `record_access` fires only on `GET /{id}` and the artifact download;
- the PR body's counts: 16 of 17 base failures are their own defect, and `[0.16.0]` is 261 lines;
- `[0.16.0]` stays byte-identical to the `v0.16.0` tag.

**The verification bar:**
- unit; coverage; api+integration;
- the harness, extended with an arm per new fix; the harness-coverage counter;
- `juniper-symbol-loss-check --scope 'juniper_data/**' --base 0f0f7e0e`, and the docs screen;
- lane B's probes, against `d1c66a11` and the new head.

**Out of scope:**
- data438's F8 (#437's breaking marker, the owner's);
- L7 (a known issue);
- data428 round-3 A1 F2-F4 (the closes PR files or declines them);
- `juniper_data/api/security.py`, which Lane F's data#440 edits.

Lane R's branch owns `http_cache.py`, `routes/datasets.py`, `storage/*`, `test_conditional_requests.py`, `api/app.py`, `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, and it edits data's `CHANGELOG.md`. Lane F stays out of those.

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

**Item 1: validate cascor#690** (branch `fix/shortfall-688-validation`; commits `c4e002d2` and `78e99414`).
- **What it is:** #688's fix-forward, answering the 2 MEDIUM, 3 LOW and 2 NIT findings in `cascor688-validation.md`.
- **How:** at least two lanes on each commit. The implementer's evidence is not independent:
  - its reports: `cascor690-implementation-report.md` and `cascor690-fixup-implementation-report.md`;
  - harnesses for `c4e002d2`: `2026-09-24_cascor688_fixforward_mutation_check.py` and `…_cascor688_realjd_error_texts.py`;
  - harnesses for `78e99414`: `2026-09-24_cascor690_bool_stance_producer_table.py`, `…_realjd_probe.py` and `…_as_bool_stance_mutation_check.py`. The last imports the `cascor688_fixforward` harness by path.
- **Probes:** `…/cascor688-v688/`. The `probe_realjd_*.py` probes and both `realjd` harnesses need a live juniper-data. Serve one with `bash util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash <tree> <scratch-dir> <port>`.
  - `<tree>` must be a scratch export, never a checkout: `git -C <juniper-data clone> fetch origin main`, then `mkdir -p <tree>`, then `git -C <juniper-data clone> archive origin/main | tar -x -C <tree>`.
  - The script refuses a checkout. It keeps storage and imports in scratch, with the probes' `big.csv`, and inherits no keys, CSV-import cap or truncation switch. Metrics, rate limiting and Sentry are off.
  - Its final version was tested at 01:17Z with lower-case variants of the auth and cap variables set: `/v1/health` and an anonymous `/v1/generators` answered 200, the over-cap `csv_import` got juniper-data's real 422 refusal, and the checkout stayed clean.
  - Stop it with `pkill -A -f …`.
- **Then:** fix forward. Once it merges and validates, CASCOR-008 and -013 can close.

**Item 2: validate canopy#685 post-merge at `dc5ea02e`**, with at least two lanes, and fix forward in a NEW PR from `main`.
- **What it closes:**
  - APD-ECO-014;
  - canopy's half of APD-ECO-013: the `str` `compare_digest` at `security.py:115`, `:273` and `csrf.py:91` became bytes at `:137`, `:300` and `csrf.py:97`;
  - `canopy683-validation.md`'s LOW3 and LOW4 (F-CANOPY-061/-062).
- **Report:** `canopy685-implementation-report.md`.
- The #685 worktree lacks the two probe-script commits, so validate `dc5ea02e` from a fresh tree.

**Item 3: cascor#689 (`97341680`) and data#440 (`0bee089e`),** both on branch `fix/bytes-compare-no-500`, open and VALIDATED:
- 0 failures over U+0000–U+10FFFF;
- 0 responses of 500 on real uvicorn;
- a timing profile that depends only on the configured key's length.

**Item 4: the F fix-forwards.** F1 was fixed by canopy#685. F8 (a `break` after `matched = True`) is killed by F3.

| Item | Sev. | Where | Fix |
|---|---|---|---|
| F2 | MEDIUM | observability `sentry.py` | `before_send_transaction=_strip_sensitive_headers`, with a test. Transactions skip `before_send`, so under `send_pii=True` (juniper-data only) they carry the raw `x-api-key`. |
| F3 | MEDIUM | service-core, data, cascor (canopy has one) | A spy test: 2 or more keys, the match first, `len(calls) == len(keys)`, bytes arguments. In data, mark the existing and new spy tests `unit`, or use the marked `TestNonAsciiApiKey` (`:206`). `TestAPIKeyAuth` (`test_security.py:37`) is unmarked, and CI's `-m "unit and not slow"` (`ci.yml:287`) deselects it. |
| F4 | MEDIUM | cascor `src/tests/conftest.py` | After `import sysconfig` (line 37), set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN` and `SENTRY_DSN` to `""`. Do not unset them: `load_dotenv` re-injects. |
| F5 | LOW | `_ENCODING_PROBES` in service-core `tests/test_security.py:101`, data `juniper_data/tests/unit/test_security.py:34` (#440) and cascor `src/tests/unit/api/test_api_security.py:31` (#689) | Add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`, NOT U+1F511, which all three hold. The two collide under UTF-16-LE with `surrogatepass`, which is what kills the mutant. The "only total AND injective" comment is false. Check with `od -c`. Canopy is out of scope: its `NON_ASCII` (`:172`) is checked only against a fixed `"key1"`. Source: `bytes-compare-…-validation.md:63-64`, `:131`. |
| F6 | LOW | observability `tests/test_sentry.py` `_frames` | Add frames with `in_app: False`, plus one wire test with `in_app_exclude`. |
| F7 | LOW | cascor `test_main_sentry_no_local_variables.py` | Replace the AST match (`:33-35`) with a behavioural subprocess test: `get_client().options["include_local_variables"] is False`. This is a symbol loss: put `Allow-Symbol-Loss:` in a COMMIT body. |
| F9 | NIT | `juniper-service-core/CHANGELOG.md:57-58`; cascor#689's CHANGELOG and PR body | Write "rejected: ASGI close 4001, HTTP 403 on the wire". Correct it in the fixup's commit body too. data#440 carries no such text. |
| F10 | NIT | observability `CHANGELOG.md` | "Consumers inherit both on upgrade, with no code change" is false: every lock pins `==0.4.0`. |

**Release facts** (for Appendix B):
- **Locks** at `==0.4.0` (observability) / `==0.7.0` (service-core):
  - data `requirements.lock:88/:90`;
  - cascor `requirements.lock:63/:65`, and `requirements-cpu.lock:129/:133`, the lock its image installs (`Dockerfile:41-42`);
  - canopy `requirements.lock:79/:81`;
  - recurrence `juniper-recurrence/juniper-recurrence/requirements.lock:70/:74`.
- **Caps:**
  - observability `<0.5.0`: canopy `pyproject.toml:109`, recurrence `:79` and its client `:41/:46`;
  - service-core `<0.8.0`: data `:110`, cascor `:105`, canopy `:119`, recurrence `:51`, juniper-ml `pyproject.toml:94` (`[tools]`).
- **Recurrence initialises no Sentry,** so for it the frame-locals fix is moot; it needs the service-core release.
- cascor#689 fixes only cascor's CLI init (`main.py`), not the service path at `src/api/app.py:335`, which goes through the shared `configure_sentry`.
- **Order** (`feedback_semver_beats_consumer_cap_2026-09-05.md`): a cap PR that a bump crosses lands BEFORE the Release. The lock and floor PRs come after the wheel is on PyPI.
- Record why `surrogatepass` was chosen over `surrogateescape`, from `bytes-compare-…-validation.md`.

## Appendix E: the fork-drift marker (Lane R, after data#440 and cascor#689 merge)

Measured by `handoff-2fba4397-round{1,2}-laneF-reprobe.md`; re-verify before coding. Lane R agreed with Lane F (2026-09-25 00:21Z) to correct the gate's comment in this change.
- **Pin a PAIR:** `encode("utf-8", "surrogatepass")` and `compare_digest(presented,`.
  - Not the bare word `surrogatepass`. Every copy also carries it in a comment or docstring (service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`), and the matcher is a whole-file substring test (`tests/test_service_fork_drift.py:289`).
  - The code-only anchors: service-core `juniper_service_core/security.py:88`/`:91`; canopy `src/security.py:52`/`:137`; data#440 `:115`/`:118`; cascor#689 `:84`/`:87`.
- **Canopy's `.encode` sits only in `_compare_bytes`** (`:42-52`), which `:300` also uses. A revert to `presented = api_key` that keeps `_compare_bytes` passes even the literal pair; F3's spy test, with its bytes-argument check, catches it.
- **Canopy's CSRF compare** (`src/csrf.py:91`, `:97`) is outside the site file.
- **Mutation-check the guard:** delete each site's `.encode(...)` call in a copy, and confirm the guard fails.
- **PR CI will not catch a premature marker.** `ci.yml:500` runs the file but skips every fork site without siblings, so a premature marker merges green and fails the next weekly `docs-full-check` on `main`. Test with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and the siblings at `origin/main` (11 OK today).
- **The same change:**
  - corrects `tests/test_service_fork_drift.py:205-209`, "no behavioural test can tell them apart", which the F3 spy refutes;
  - cites APD-ECO-013, so it lands with or after the closes PR;
  - updates every guard count: juniper-ml `docs/REFERENCE.md` about L2977, and the register about L240, L252, L1106 and L1751, plus its §2.3 guard table.

## Appendix F: worktrees and branches (remove only with the owner's go-ahead in your session)

All are under `/home/pcalnon/Development/python/Juniper/worktrees/`. Before removing one, re-check `git status` and `gh pr view <N> --json state,mergedAt`.

| Worktree | Lane | State at writing |
|---|---|---|
| `juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2` | R | Holds the data fix-forward branch and the executor's work. **Keep it.** |
| `juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c` | F | HEAD is #690's head. Keep it until #690 merges and validates. |
| `juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac` | F | #685 merged. HEAD is the unsigned `4caf9389`, tree-equal to `4a8af2a0`; the stray branches point there. |
| `juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb` | F | #689 is open. HEAD is the signed local `24103c23`, tree-equal to `97341680`. |
| `juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480` | F | #440 is open. HEAD is the unsigned `5bd5eec5`, tree-equal to `0bee089e`. |
| `juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227` | F | #683 merged; clean. |
| `juniper-ml--fix--sentry-locals-and-bytes-compare--20260924-1337--48fc09e5` | F | ml#2086 merged; clean. |
| `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2` | R | Older; awaits the cleanup signal. |
| `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6` | R | Older; awaits the cleanup signal. |
| `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6` | R | Older; awaits the cleanup signal. |
| `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f` | R | Older; awaits the cleanup signal. |

- **To remove one:** `git -C <owning repo> worktree remove <path>`, then `git branch -D <branch>`, then `git worktree prune`. For a juniper-ml worktree, run `git worktree remove <path>` from your own juniper-ml worktree. `worktree remove` also deletes ignored files, such as `logs/` and `snapshots/`.
- **Stale branches,** under the same gate:
  - the remote `fix/shortfall-mixed-provenance-and-678-followups` (`e452a660`, from the closed #686), and the local cascor branches of that name and its `-v2`. #686's commits stay at `refs/pull/686/head`, but deleting its head blocks reopening it.
  - canopy's `pr-63` and `pr-683` (Appendix B).

## Appendix G: documents the two sessions created or changed

- **Lane R** (session `2fba4397`): Appendix F of document 1 lists them:
  - #2088's 14 files;
  - #2089's 132;
  - its uncommitted files;
  - five memory files: `reference_git_trailer_must_be_last_paragraph.md`, `reference_typed_escapes_become_real_characters.md` (new), `reference_backticks_eaten_in_shell_messages.md`, `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md` and `MEMORY.md`.
  - This consolidation adds this file and its `handoff-consolidated-*` reports.
- **Lane F** (session `bc31e993`): #2097's 95 files, and its merged PRs (cascor#688, canopy#683, canopy#685, juniper-ml#2086, #2072 and #2077).

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

## Appendix I: where each source item lives

- **Document 3 (the predecessor, stale),** as document 1's Appendix D mapped it:

  | Document 3 | Now |
  |---|---|
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
- **Document 1 (Lane R):**

  | Document 1 | Here |
  |---|---|
  | Header and Goal | Header, Goal and the owner's policy |
  | First actions 1-4 | First actions 1-5 |
  | Completed | Merged, Open at writing, Appendices C and H |
  | In flight | In flight |
  | Remaining 0 | This consolidation |
  | Remaining 1 | First action 5, Git status |
  | Remaining 2 | Work 5 |
  | Remaining 3 | Work 1, Appendix C |
  | Remaining 4 | Work 6, Appendix A |
  | Remaining 5 | Work 7, Appendix E |
  | Remaining 6 | Work 8, Appendix A |
  | Remaining 7 | Work 9 |
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
  | Coordination | the lane split, and Appendices A and C |
  | Canopy ledger | Appendix A, Residue |
  | Release facts | Appendix D |
  | Traps | Key context and traps |
  | Worktrees and branches | Appendix F |
  | Verification commands | Verification commands |
  | Git status | Git status |
