# Handoff: defect-register round 42. The second fix-forward merged as ml#2088, the data fix-forward was refuted before its PR and is being fixed, and the closes PR is owed

**From:** session `2fba4397` (`ListAgents` name **"defect reg [24f8d8]"**), in worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. **Written:** 2026-09-25, about 01:10Z.
**This file:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. It is UNTRACKED in that worktree until it ships (Git status).
**Validated** in three rounds of independent lanes, archived as `reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round{1,2,3}-*.md`. No lane returned a clean PASS: round 1 had one FAIL and two PASS WITH CORRECTIONS, and rounds 2 and 3 all PASS WITH CORRECTIONS. Every correction is applied.
**Predecessor:** `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (session `8f86dec2`). Appendix D accounts for every item in it.
**SUPERSEDED** by the consolidated handoff the owner asked for (Remaining 0): `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`, which ships with this file on branch `docs/handoff-round42-consolidated`.
- Work from that file. This one is now its evidence index: its instructions below are replaced by the consolidated file's.
- **State moved after this file was written:** the executor finished and pushed `94ce8b1f` (01:46Z), and the owner's sweeper merged cascor#689 (01:56Z), data#440 (01:57Z) and cascor#690 (02:06Z, unvalidated). The consolidated file carries the current state.
- If you hold only this file, find the consolidated one on `origin/main`, in that branch's PR, or untracked beside this file in the worktree below.

## Goal (paste the WHOLE document, appendices included, as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem.
- The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.
- **The owner's policy:** the PR sweeper is theirs and its merges are intended. Validate a pushed branch before opening its PR when a validated merge matters; otherwise validate after merge and fix forward.
- **Merge approval does NOT carry to a new session** (memory `feedback_headless_merge_approval_policy.md`). The owner granted it to "defect reg [24f8d8]" for this arc. Get your own grant before any merge, arm or re-arm.
- **Never merge** another lane's PRs: data#440, cascor#689, cascor#690, or any the peer lane opens.

**First actions, in this order:**
1. **Run the verification commands** below.
2. **Treat the executor as ALIVE** (In flight 1) while `ListAgents` lists "defect reg [24f8d8]" in any state but offline, unless In flight 1 shows it finished: a live parent can resume a stopped executor. While it is alive, do not touch the juniper-data worktree, do not launch a second executor, and never ask the owner to close that session, which would kill the executor. **If [24f8d8] is listed, message it first** (your name and `[ref]`): ask which items it is still doing, and start none of them.
3. **Re-route the peer lane.** It is handing off too, and its own handoff says never to message its old session, "defect reg [042116]" (session `bc31e993`). It tells ITS successor to message "defect reg [24f8d8]". Unless the consolidated handoff has merged the two lanes into one:
   - message the peer's SUCCESSOR: the other live session working that handoff, found with `ListAgents` (load `ListAgents` and `SendMessage` with ToolSearch if they are deferred); ask the owner if you cannot tell. Give it your name and `[ref]`, and say you replace [24f8d8];
   - if [042116] is still listed, message it too;
   - never wait on a message for the peer's PR. Find it with the `gh pr list … --head docs/handoff-round42-followup-lane` command below.
4. **Ship the uncommitted files** (Git status) only once the executor has FINISHED (In flight 1) AND "defect reg [24f8d8]" is gone or has confirmed it no longer writes here. Handed-off sessions stay listed for days: if it stays listed and silent after the executor has finished, ask the owner to close it. That is safe then, and only then.
   - First re-copy the PR draft (Appendix C).
   - Check that neither `origin/main` nor any open juniper-ml PR carries these paths; `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py` does both. Never use `gh pr view --json files`, which stops at 100. If the consolidation PR carries them, ship nothing.
   - Until they ship, **never `git reset`, `checkout`, `clean`, `stash` or remove this worktree.**

**Completed:**
- **juniper-ml#2088 MERGED at 23:41:16Z as `5af9d722`.** It is the second register and primer fix-forward, from `ml2080-round1-laneA-reprobe.md` / `-laneB-refute.md`.
  - It was validated before its PR opened, in two rounds. Its four reports shipped with it.
  - Round 2's MEDIUM was a regression round 1's own fix introduced: a lone surrogate turned the toy's 422 into a plain-text 500. It is fixed, and so is the same class in the list route.
  - At the head: harness 62/62; mutation check 12/12; probe 27/27; register 136 rows | 100 fixed | 36 open, AGREE.
  - On the pre-merge primer (`c061a99f`), the probe differs in 25 cases under CPython 3.13.13 and 24 under 3.14.2.
  - Post-Merge Main Verification and CodeQL passed. The symbol screen honours its `Allow-Symbol-Loss` waiver (see Traps).
- **juniper-ml#2089 OPEN**, head `a2fa3ad8`, not armed. It preserves the 129 Python probe scripts of this session's six lanes, off tmpfs, in `util/ad-hoc/2026-09-24_round42_probes/<report stem>/`, as #2081 did for `8f86dec2`'s. The 66 shell runners (48 `.bash`, 18 `.sh`) are not kept; the README says why.
  - At the peer's request, its README also carries the peer lane's four directory rows and paragraph. The peer agreed to drop that file from its own PR.
  - **CodeQL FAILED** at 00:27:51Z: 33 new alerts, 4 high (`py/overly-permissive-file`, `…/data438-fixforward-round1-laneB/stripe_probe.py`). This is the owner's call (Appendix B).
- **The juniper-data fix-forward**, branch `fix/conditional-requests-round4-followups` @ `d1c66a112e4bc70ee97496a14265f7b90e10fb88`.
  - Its parent is `0f0f7e0e`, the merge of juniper-data#438. #438 merged at 18:52Z, before its fix-in-place landed.
  - It answers every finding in `data438-round1-lane{A-reprobe,B-refute}.md`, two only partly: M2(b) and L2 of the lane-B report. data438's F8 (#437's breaking marker) is left to the owner; L5 and L7 are disclosed.
  - Its numbers at `d1c66a11`: unit 1901, coverage 97.76%, api+integration 118, harness "PASS: 70 mutations", equivalence 3,495,583 inputs / 0 mismatches.
  - **Validated before any PR, and REFUTED:**
    - lane A (`data438-fixforward-round1-laneA-reprobe.md`): 2 LOW, 9 NIT;
    - lane B (`data438-fixforward-round1-laneB-refute.md`): 1 MEDIUM, 5 LOW, 6 NIT.
  - **The MEDIUM is a regression the branch introduces.** `record_access` runs on the event loop (`call_soon`) and blocks on the process-global `_version_lock`. `save_versioned` now holds that lock for a whole save, and every ecosystem client creates unnamed datasets. One 80 MB create froze the service for 6.6 s, against 0.01 s on `main`: past the readiness probe's 5 s timeout, which acts after three failures.
- **The "Key leaks" ruling is extracted verbatim** into `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`. It was asked at 10:22:00.792Z and answered at 18:30:09.820Z: "Fix everywhere now (Recommended)".
- **Resolved since the predecessor:**
  - juniper-data 0.16.0 on PyPI (18:35Z);
  - juniper-ml#2081 merged 22:45:08Z (`7e8c7ff9`);
  - juniper-ml#2086 merged 20:37:13Z (`c061a99f`);
  - canopy#683 merged 19:10:20Z; canopy#685 merged 23:24:14Z (`dc5ea02e`, NOT yet validated);
  - cascor#688 merged 18:56:25Z (`7f4a7213`).

**In flight** (subagents of "defect reg [24f8d8]"; they die with it):
1. **FINISHED at about 01:48Z, after this file was written:** it pushed signed `94ce8b1fa8e229c92e8674a1074d518e59142488` (parent `d1c66a11`) and opened no PR. Its disposition report is archived as `data438-fixforward-round1-fix-report.md`, and the final PR draft is re-copied. The consolidated handoff carries the state from here; the rest of this item is history.
   **Executor `a46e715a6801b98ca`** was fixing every finding of both data lanes (Appendix C).
   - It pushes ONE signed commit with `--expected-head d1c66a112e4bc70ee97496a14265f7b90e10fb88`, opens no PR, and updates the PR drafts.
   - Its transcript is `/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`.
     - Its **disposition report** is the last assistant message. Read it with `last_report()` from `util/ad-hoc/2026-09-24_archive_round42_reports.py` (load it with `importlib`); never read it with `splitlines()`.
     - Its **brief** is TWO `user` records. 19:37:50.383Z is the task: the regime, the upload proof, an unsigned LOCAL scratch commit, the trailers, the PR prohibitions, and four scratchpad spec files (`data_round3_original_brief.md`, `data_round4_spec.md`, `data_round4_redirect.md`, `old_executor_summary.md`). 23:48:49.313Z is the round-1 fixes, which relies on the first. A third `user` record, at 00:29:28.847Z, is its own compaction summary.
   - **Finished or dead?** `last_report()` returns `""` while a tool call is in flight, and the disposition report once the executor has finished. If it has finished, act on the report; if it stops short of pushing, or claims a push the ref does not show, find out why before relaunching anything.
   - **Dead only if** "defect reg [24f8d8]" is gone, the transcript is 30+ minutes old, AND `last_report()` is not a disposition report. It went 600 s without a write while alive.
   - **If it died:** run `git --no-optional-locks -C <data worktree> status -sb`. Copy the four spec files and both drafts from this session's scratchpad (Appendix C) into your own first; they survive a session's end, not a reboot.
     - Dirty, or clean with `[ahead N]` (the scratch commit, which must NEVER be pushed), and the remote ref still `d1c66a11…`:
     - extract both briefs with a script, then launch a new `task-executor` on that worktree with both briefs, both round-1 reports and the drafts;
     - tell it to review `git diff origin/fix/conditional-requests-round4-followups` first. A dead subagent cannot be resumed from another session.
     - Tell it where the briefs are wrong: brief 1's step 5 (create the branch and push with `--expected-head` of `0f0f7e0e`) is obsolete because the ref exists, so push with `--expected-head d1c66a112e4bc70ee97496a14265f7b90e10fb88`; and brief 2 says to UNSET the DSN variables, which must be set to `""` instead.

**Remaining:**
0. **Consolidate** (the owner's instruction, 2026-09-24 about 23:25Z): merge three handoffs into one, validated by consensus with no task or context lost.
   - The three:
     - this file;
     - the predecessor (on `main`);
     - the peer's `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, FINAL in juniper-ml#2097 (head `2e4917c2`, OPEN, not armed). It was validated in 5 rounds.
   - "defect reg [24f8d8]" agreed the split with the peer at 23:35:52Z: the `surrogatepass` marker and C-A…D-G are this lane's.
   - It began the consolidation once #2097 arrived (about 01:20Z). Look for the result first (header).
   - Already reconciled in #2097: the README rows (on #2089), the canopy forwards, and `APD-ECO-013` (its line 135). Still different: its line 134 says "APD-CASCOR-014 closes when F4 lands", dropping the validation gate, and its line 136 reads APD-ECO-014's condition as met. Keep this file's gates (Appendix A).
1. **Ship the uncommitted files** with `util/open_signed_pr.py`, after First action 4.
   - Rebuild each file from `origin/main` (Traps), and leave #2089's files out.
   - Put `Allow-Symbol-Loss: const:SESSIONS` in the commit body: the extractor renames `SESSIONS` to `SESSION_IDS`.
   - Merge #2089 only once the owner has resolved its CodeQL block and it is green, with your own grant.
2. **Validate #2088's one unvalidated delta**, `990ef3f9..2439d049` (round 2's corrections): two lanes on the whole range; archive the reports; fix forward.
   - A checklist: primer lines 4199, 5330, 5378, 5399, 5455, 5464, 5600, 5618, 5622, 5658-5659, 5682, 5699, 6084-6087, 6091, 6117-6120, 9880 and 9943-9944.
   - Also the register's `GET /{id}` wording, APD-CASCOR-013's Source cell, the §4 note, the rulings-block ids and APD-DATA-057's park bullet.
   - Also the tools.
3. **Finish the data fix-forward.**
   - Check the executor's commit against both reports and its disposition report. Its MEDIUM fix is a concurrency change.
   - Run round 2 (two lanes, on `d1c66a11..<new head>`) BEFORE opening the PR.
   - Open it with `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<line 1 of the draft, without '# '>" --body-file <a scratch file holding line 3 onward>`. `open_signed_pr.py` refuses an existing branch.
   - Merge with your own grant, archive the round-2 reports, and send the PR number to the peer's successor.
   - data#440 (head `0bee089e`) also edits `CHANGELOG.md` `[Unreleased]`. The two merged cleanly at `d1c66a11`; re-check at the new head.
4. **The closes PR** (juniper-ml, register): Appendix A.
5. **The fork-drift marker**, this lane's, AFTER data#440 and cascor#689 merge: Appendix E.
6. **Verify on the real services, then file.**
   - (a) A 422 that echoes the input through Starlette's `JSONResponse` (`ensure_ascii=False`) raises `UnicodeEncodeError` on a lone surrogate. That is a `ValueError`, so the outcome depends on the app's handlers (round-2 lane F, measured in-process):
     - FastAPI's default app: a plain-text 500.
     - juniper-data (`juniper_data/api/app.py:187-212`, with its `ValueError` handler at `:214`, at `0f0f7e0e`; `d1c66a11` shifts them to `188-213` and `:215`): **400 `{"detail":"Invalid request parameters"}`**. The 422's per-field detail is silently lost, and no Sentry event is sent. Round 3 re-measured it on data's locked fastapi 0.141.1 / starlette 1.6.0, with a Sentry capture transport: no error event.
     - cascor (`src/api/app.py:856`, `ValueError` handler `:916`): measured by round 3 in-process in JuniperCascor1 (fastapi 0.137.0 / starlette 1.0.0, not its locked pair, and without its lifespan): **400** in cascor's envelope, `error.code` `VALIDATION_ERROR`, message "Invalid request parameters", `detail: null`. The per-field list is lost, and no Sentry event is sent. Re-measure it on the locked pair.
     - File it as a register row in the closes PR. It is a sibling of `APD-DATA-056`, and input to D-C.
   - (b) The primer's `idempotent_jobs.py` example has (a)'s defect in its default-handler form. A lone surrogate in `dataset_id` fails validation (`string_unicode`); the default 422 cannot render it, so the client gets a plain-text 500, again on retry. No key record is ever created, so there is no replay defect.
     - Correct the primer IN PLACE.
     - Correct primer lines 4742-4743 too: stale since data#281, they say juniper-data registers no such handler.
7. **PATCH two PR bodies** with `gh api -X PATCH`.
   - juniper-ml#2080: move the bullet "A-nit on `APD-ML-008`" (body L69, under "Rejected, with reasons", L65) to the applied items, citing #2088 (`ml2080-round1-laneA-reprobe.md` N6).
   - juniper-ml#2088: "Extended beyond the lanes" (the list route) is false; `register-fixforward2-round2-laneB-refute.md` N11 (line 120) named it. `2439d049`'s commit message, "which no lane named", is false too; record that in the closes PR.
8. **Owner decisions:** Appendix B.

## Key context and traps (part of the prompt)
- **Routing:** the 0.16.0 notify-consumers 403 goes to "containers [2703c8]". Canopy-ledger items (F-CANOPY-060…062, and the copies of #687's sentence) went to "canopy combined [577a1c]", which had gone by 01:40Z, as had the canopy E2E session: give them to the next canopy session, or to the owner.
- **Uploads are WHOLE-FILE.** Before every push, run `git fetch` and `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`.
  - Compare with `git show origin/main:<p> | diff - <p>`.
  - For a shared `CHANGELOG.md` `[Unreleased]`, prove `main`'s lines are a subset of yours.
  - This worktree is 5 commits behind `origin/main`.
- **Signed commits have ONE parent,** so a textual conflict cannot be merged away: supersede from fresh `main`.
- **Cutting a release before update-branch can mis-file a CHANGELOG silently:** a 3-way merge duplicated `## [0.16.0]`. Run update-branch first.
- **Never run `util/worktree_cleanup.bash`:** it pushes, and runs `gh pr create`. That is the peer's finding.
- **Never name an OPEN id on the register's §2 status list** (L177, the line beginning "**Eighty-one of the 96 have since been fixed**"; L176 above it is not that line): the crosscheck reads every id on it as closed.
- **/tmp is a ~1M-inode tmpfs** (83% at handoff; it hit 100% on 2026-09-24). Brief every lane to prune.
- **Sentry:** set every DSN variable to `""` in every test run and server: `SENTRY_SDK_DSN` (exported in these shells), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN`, `JUNIPER_CANOPY_SENTRY_DSN`. Set them empty, never unset: `load_dotenv` re-injects an unset one. Never use port 8100, 8201 or 8050.
- **A usage limit kills subagents.** Resume each with SendMessage, from the session that spawned it. An agent the user stopped cannot be resumed.
- **How to run a lane:** as a background `general-purpose` Agent.
  - Launch the lanes in ONE message: A re-derives every claim from source; B refutes, defaulting to REFUTED.
  - Give each its own scratch subdirectory. Tell each: read-only; no secret or email egress; compound shell goes in a script.
  - Report format: as in `register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
- **How to archive a report,** in `util/ad-hoc/2026-09-24_archive_round42_reports.py`:
  - add your session's full UUID to `SESSION_IDS` (the directory above your scratchpad), and the report's `MISSING` entry;
  - `HEADER` hard-codes 2026-09-24, so change it for new reports;
  - run `--check`, then run it without.
- **The primer harness** is `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>`, which gives 62 tests.
  - The venv: CPython 3.13.13 (JuniperCanopy1's interpreter), fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2. This session's copy is `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv`, on tmpfs.
  - `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` needs `--venv` and `--scratch`.
- **The primer is cited by bare line number: edit it in place only.**
  - Model a new editor on `util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py`, which refuses to run twice and refuses any line move.
  - `util/ad-hoc/2026-09-24_register_primer_citation_census.py` counts every bare number past 5758 (69 citations, 82 numbers today), so name a retired anchor in words.
- **GitHub's squash appends a `Co-authored-by` paragraph.** So `git log -1 --format='%(trailers:key=Allow-Symbol-Loss)' 5af9d722` prints an empty line, although the waiver is there. Check with `grep -c`, or with `juniper-symbol-loss-check --base <parent> --head <sha>`, which scans lines.
- **The sweeper's merge stores the default squash body.** Put waiver trailers in a COMMIT body.
  - A curated re-arm is `gh pr merge --disable-auto`, then `--auto --squash --subject … --body-file …`.
  - Re-arming needs your own grant, and `--auto` on a MERGEABLE PR merges at once.
- **Signed pushes:** `util/push_signed_commit.py --expected-head <FULL 40-hex sha>`.
  - A run can create nothing: the first push of `2439d049` printed its plan and made no commit.
  - Check `gh api repos/pcalnon/<repo>/git/ref/heads/<branch>`; a re-run with the same head is safe.
- **`strict: true`:** after every move on `main`, run `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<full sha>`. `gh pr edit` is broken; use `gh api -X PATCH`.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage: a backslash-u escape of U+2028, or of a surrogate pair, arrives as the character. Build such text with `chr()`, and check it with `od -c`.
- **The worktree-isolation guard's refusals are heuristic:** a shell variable or a loop anywhere in a command that also runs git can be refused. It refused, among others (the consolidated handoff has the full list):
  - `$(...)` feeding git or gh; loops around git or gh; backticks inside heredocs;
  - the word "git" inside a `python3 -c` string;
  - variables around `sed`, and a computed `python3` argument;
  - `git -C` into another juniper-ml worktree.

  Use plain separate commands, or a script under `util/ad-hoc/`.

## Verification commands
Run from `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. From another worktree, read its files by absolute path: the guard refuses `git -C` into it.
```
git status --short                     # 17 entries at 01:10Z; each report, handoff and script added since is one more; see Git status
gh pr view 2088 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit
gh pr view 2089 --repo pcalnon/juniper-ml --json state,headRefOid,mergeStateStatus
gh pr checks 2089 --repo pcalnon/juniper-ml | grep -i codeql       # fail at handoff
gh pr list --repo pcalnon/juniper-ml --head docs/handoff-round42-followup-lane --state all   # #2097 since 01:20Z
git fetch origin && python3 util/ad-hoc/register_open_set.py | grep 'rows |'   # 136 rows | 100 fixed | 36 open; reads THIS worktree's register
python3 util/ad-hoc/register_status_crosscheck.py | tail -1                    # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c 'OK    '   # 42 at 01:10Z, +1 per report archived since; 34 on origin/main at 01:10Z, 52 on #2097's head. The count that matters: `grep -c -e DIFFER -e REFUSE` must print 0
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # d1c66a11… until the executor pushes
git --no-optional-locks -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status -sb   # [ahead N] = an unsigned scratch commit: never push it; after a push and a fetch, [ahead 1, behind 1] is expected
find /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/ -name agent-a46e715a6801b98ca.jsonl -mmin -30   # printed = written in the last 30 min
gh pr list --repo pcalnon/juniper-data --state open; gh pr list --repo pcalnon/juniper-cascor --state open
df -i /tmp | tail -1
```

## Git status
- **This worktree:** branch `worktree-fizzy-hugging-dream`.
  - It holds three unsigned LOCAL scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`), made only so the CI screens could run. **Never push or commit here.** Their content is #2088's.
- **For the next juniper-ml PR (nothing else holds these):**
  - `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M): adds `--topic key-leaks`, which exists nowhere else.
  - `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M): the `MISSING` entries for the two data round-1 reports and the six handoff-validation reports, all of session `2fba4397`.
  - In `reports/2026-09-24_defect-register-round-42/`, all untracked:
    - `owner-ruling-key-leaks-verbatim.md`;
    - `data438-fixforward-round1-laneA-reprobe.md` and `data438-fixforward-round1-laneB-refute.md`;
    - the `handoff-2fba4397-round{1,2,3}-*.md` reports;
    - `data438-fixforward-pr-draft.md`, copied at 00:27Z, BEFORE the executor's update.
  - `util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py` (??): the executor's own round-2 stall probe.
  - This file (??), the consolidated handoff (??), its `handoff-consolidated-*` validation reports, and `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py` (??), which opens the consolidation PR carrying all of the above.
- **NOT for the next PR:** #2089's files. That is `util/ad-hoc/2026-09-24_round42_probes/`, `…_copy_round42_session2fba4397_probe_scripts.py` and `…_open_round42_session2fba4397_probes_pr.py`. They are byte-identical to `a2fa3ad8`, and re-adding them would collide with #2089.
- **The juniper-data worktree:** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2`. Its name says round3, but it holds `fix/conditional-requests-round4-followups` with the executor's work. **Do not remove it.**
- **Older register-lane worktrees,** waiting for the owner's explicit cleanup signal:
  - `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`
  - `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6`
  - `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6`
  - `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f`

## Appendix A: the closes PR

**Gates.** Close a row only after its PR merges AND its own validation holds.
- `APD-CASCOR-008` / `-013`: cascor#688 merged; its validation asked for cascor#690, which is OPEN at `78e99414` and unvalidated. The peer lane validates it.
- `APD-DATA-017` / `-029` / `-032` / `-057`: data#438 merged; its fix-forward (Remaining 3) must merge and validate.
- `APD-ECO-014`, canopy's half of `APD-ECO-013`, and F-CANOPY-061/-062's FIXED-BY: canopy#685 merged UNVALIDATED. The peer lane validates it.

**File:**
- **`APD-ECO-013` (S).** A non-ASCII `X-API-Key` makes the `str` `compare_digest` raise; the 500 goes to Sentry, and its local-variable capture records the real key.
  - Fixes: juniper-ml#2086 (merged), canopy#685 (merged), data#440 and cascor#689 (open).
  - **It closes** once data#440 and cascor#689 merge, #685's validation holds, and the peer's F2 and F3 are fixed. The peer's final handoff (juniper-ml#2097) states the same condition, under "Coordination with the register lane" → "What it holds on your outputs".
  - Source for F2 and F3: `bytes-compare-ml2086-data440-cascor689-validation.md`, untracked in `…/happy-skipping-hollerith/reports/2026-09-24_defect-register-round-42/` until the peer ships it.
    - F2 (ml#2086): no `before_send_transaction`, so with `send_pii=True` a sampled transaction carries the raw `x-api-key`.
    - F3: no CI test checks that `compare_digest` is used at all.
  - **Residue on the row unless fixed first** (the peer's successor fixes these and says which landed):
    - **F5, for service-core, data and cascor only** (that report's lines 63-64 and 131). Add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`, to each `_ENCODING_PROBES`, and fix its false "only total AND injective" comment. It is not U+1F511, which every copy already holds. Canopy has no `_ENCODING_PROBES`.
    - F6: no observability test frame has `in_app: False`.
    - F7: cascor's AST test matches only the spelling `sentry_sdk.init`.
    - The peer's F8 (a `break` after `matched = True` survives every suite): Remaining 5.
    - F9: `juniper-service-core/CHANGELOG.md:57-58` says the handshake "closes 4001"; it should say "rejected: ASGI close 4001, HTTP 403 on the wire". Also in cascor#689's text; not in data#440.
    - F10: observability's CHANGELOG line "Consumers inherit both on upgrade, with no code change" is false.
  - **Releases.** The frame-locals fix reaches no running service until juniper-observability is released and every consumer's `==0.4.0` lock moves:
    - data `requirements.lock:88`;
    - cascor `requirements.lock:63` **and `requirements-cpu.lock:129`, the lock its image installs** (`Dockerfile:41-42`);
    - canopy `requirements.lock:79`, capped `<0.5.0`.
    - cascor#689 fixes only cascor's CLI init (`main.py`), not the service path at `src/api/app.py:335`, which goes through the shared `configure_sentry`.
    - Recurrence has no Sentry. It needs only the service-core release and a move of `juniper-recurrence/requirements.lock:74` (`==0.7.0`), which its cap `<0.8.0` (`juniper-recurrence/pyproject.toml:51`) blocks.
    - The peer's handoff lists further `<0.8.0` service-core caps, and the observability `<0.5.0` caps (canopy `:109`, recurrence `:79`, and the recurrence client `:41/:46`, the recurrence ones in optional extras). The consolidated handoff's Appendix D carries them all.
    - Record why `surrogatepass` was chosen over `surrogateescape`, from the peer's report.
- **`APD-ECO-014` (S):** canopy's padded outbound keys leaked into logs, into Sentry and into a 409 body. File it OPEN, with canopy#685 as its fix; close it once #685's validation is cited.
- **`APD-CASCOR-014` (S), the peer's F4, confirmed.** cascor tests that `import main` start the REAL Sentry SDK when a DSN is exported: 9 files sent 25 envelopes to a sink.
  - The cause: `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` → `src/main.py:231`.
  - The fix: in `src/tests/conftest.py`, after line 37, set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN` and `SENTRY_DSN` to `""` (empty, never unset). cascor#689's `include_local_variables=False` strips the locals, but the events are still sent.
  - File it OPEN. It closes when F4's fix (the peer lane) merges and its validation holds.

**Update, do not close:** `APD-DATA-055`. #438 fixed its lock half: at data `0f0f7e0e`, `batch_delete` and `delete_expired` go through `delete_under_lock`. Its `If-Match` half awaits the owner's ruling.

**Quote** the "Key leaks" ruling from `owner-ruling-key-leaks-verbatim.md`.

**Residue to record:**
- **cascor shortfall messages.** The flag-off 422 is no longer shown as a shortfall (#688). A juniper-data 400 for a bad param still is. cascor#690 (OPEN, unvalidated) fixes that by keying on "Re-submit with allow_truncation=true", and also makes `_as_bool_stance` parse as juniper-data does.
- **Auto-start binds wholesale.** Sources: the peer's `cascor686-fixup-implementation-report.md` item 2, and `pending-items-snapshot-2026-09-24T1110Z.md:40`.
- **`current_dataset` after a partial inline start** names the fetch, as the ruling intends; canopy reads only `.dataset_type`. Record, no row.
- **canopy#683 item 3** is a DISCLOSED behaviour change: a whitespace-only env key makes `/docs` answer 200.
- **A retire condition met.** juniper-canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its condition. Record only: retiring an ad-hoc script is the owner's decision.
- **Already recorded:** cascor#678's stale squash message is in the register (about L1616).
- **Canopy items.** Canopy behaviour belongs in the canopy E2E ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`), not the register.
  - F-CANOPY-060 (the truncation-permanence sentence; its fix is unowned), -061 (LOW 3) and -062 (LOW 4) are RESERVED. They were reserved at 19:40:28Z.
  - 061 and 062 are fixed by canopy#685, once its validation holds.
  - The reservation is recorded only in `…/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`. That is branch `docs/canopy-e2e-handoff-2026-09-24`, with no PR.
  - A fourth item, recorded by canopy combined at 20:45:53Z with no id yet: canopy's copies of #687's "Nothing was loaded…" sentence, at canopy `7ab994e5` `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` and `src/frontend/dashboard_manager.py:8381`. They go stale when cascor#690 merges. It is in `…/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`.
  - All of these are untracked, in other sessions' worktrees: read only.
- **canopy#685's residue:**
  - frame locals until the release;
  - owner calls (a), (b) and (c) (Appendix B);
  - the anonymous rate-limiter 500 needs `rate_limit_enabled`.
- **data428 round 3 (`data428-round3-laneA1-security.md`).** F3 is `APD-DATA-056`. F2 (the 8,192-byte cap, parsed under `_version_lock`) and F4 (header limits) are recorded nowhere: file or decline each, with a reason.
- **Cite the peer's archived reports** by filename, and byte-compare each against its agent's transcript. `--check` skips the four headed "turn-ending report": `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`.

## Appendix B: owner decisions, and the later arc items

**This lane surfaces:**
- **#437's breaking marker.** Data's `[Unreleased]` carries #437's `equities_seq` 6.0.0 (a `dataset_id` change), and the notes renderer computes breaking = NO.
- **APD-ML-008's silent-path remedy:** a variable only the drift step sets.
- **#2089's CodeQL block, #2097's, and #2081's.** #2097's CodeQL failed at 01:23:44Z with "45 new alerts including 3 high"; that is the peer lane's PR, and the owner's call too.
  - For #2081, two probe redactions were committed (`73dc109c`, `f9964d78`), the two highs were dismissed as "mitigated", and it merged. The `pcalnon` account that did this is shared by the owner and every session. Its 59 lesser alerts are still open on `main`.
  - The predecessor's options (a `paths-ignore` config, dismissal, a tarball) were never ruled.
  - Never dismiss alerts or edit preserved probes yourself. If the owner edits one, the README's "copied as the lanes wrote them" becomes false for it.
- **The next juniper-data release.** 0.16.0 ships the defects #438 fixed. The next release carries #438, the fix-forward, data#440 and X8.
- **The two stray canopy branches** `pr-63` and `pr-683`, both at the unsigned `4caf9389` (the #685 worktree's local commit). They were created at 22:55Z with no PR. Do not delete them unasked.
- **MEMORY.md** is 24,929 characters (`wc -m`), about 70 under the HARD ~25,000-character load limit, past which the harness drops the tail. So every new row must be paid for. Compact by retiring entries (`feedback_memory_index_target_is_20kb.md`); only a structural change is the owner's.
- **FYI:** 0.16.0's notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. The containers session owns it.

**The peer lane asks these; record the answers here.** Its successor sends each question, its options and the answer, verbatim. Do not ask them again.
- The juniper-observability and juniper-service-core releases, then the consumers' locks and floors (Appendix A). **Ask only after the peer's juniper-ml F-PR (F2, F6, F9, F10, and service-core's F3 and F5) validates**: releasing earlier ships F2's leak and F10's false sentence.
- canopy#685's calls:
  - (a) upstream text still passes through on errors that carry a status;
  - (b) spaces and tabs inside a key are refused;
  - (c) a blank `*_API_KEY_FILE` shadowing an env var now sends no key.
- Whether to purge this round's test events from the live Sentry project.

**The later arc items.** All are ruled, and this lane carries them. D-B is in flight: its rows stay open until the data fix-forward validates. C-A was started and its forks were killed. The rest have not started. The order is §0 of `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`; the owner decides when.
- **juniper-data:**
  - D-B (caching): data#428 and #438 merged, and the fix-forward is in flight.
  - D-C, the error surface (`APD-DATA-030/-031/-022`): RFC 9457 from all three sources. Candidate 6(a) belongs here.
  - D-D, lists and pagination (`APD-DATA-026/-027/-028/-008`).
  - D-E, idempotency (`APD-ECO-001`): after D-F.
  - D-F, storage pushdown (`APD-DATA-019`): after the data fix-forward merges, which rewrites `save_versioned` and the lock stripes in `storage/base.py` and `storage/local_fs.py`.
  - D-G (`APD-DATA-048/-049/-051`). `APD-DATA-047` was RATIFIED at 1e11 on 2026-09-21 and is closed.
  - D-B…D-D share `routes/datasets.py`; sequence them.
- **The clients:**
  - C-A, a per-call timeout (`APD-ECO-003`): relaunch it fresh.
  - C-B, TypedDict response shapes (`APD-ECO-004`).
  - C-C, the recurrence client using its server's models (`APD-RCLIENT-004`).
  - C-A and C-B collide on 38 `def` lines; sequence them.
- **Round 39 §0.4's two no-row items,** still without a register row:
  - `equities_seq`'s `data_quality` has no consumer in juniper-recurrence;
  - `val_ratio`'s removal from canopy's sidebar is recorded only in the register's §4.9 preamble.

## Appendix C: the data fix-forward, its brief, and its PR text

**PR text.**
- The drafts are `data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md` in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/`, on tmpfs. The executor updates them.
- The durable copy is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md`: `# <title>`, a blank line, then the body.
  - It was taken at 00:27Z, before the executor's update.
  - Re-copy it with a script once the executor finishes: `"# " + title.strip() + "\n\n" + body`. The rewritten title file ends in a newline.
- If neither survives, rebuild the body from the two `data438-fixforward-round1-*` reports and the executor's disposition report.
- The old title's "a storage fault is a 500" is true only of a stored file that leads out of the root (lane A L-1).

**The brief, summarised.** Evidence and file:line are in the two reports; the lanes' probes are on #2089.

MEDIUM:
- **Lane B M-1, with lane A L-2 and lane B L-4:** nothing on the event loop may wait on `_version_lock` or a stripe. Two creates stalled it 10.5 s.
  - Move `record_access` onto a small dedicated executor, shut down in lifespan. `to_thread` would share the default pool with the routes' store I/O.
  - Log its exceptions by type only.
  - Consider writing the temp files before taking the locks. If that is too wide, say why and document the remaining cost.
  - Pin it with a test: a read stays fast while another thread holds the lock.
  - Correct juniper-data's `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/constants.py:45-47` and `juniper_data/storage/local_fs.py:200-202`, and state the cost in `CHANGELOG.md`.

LOW:
- **Lane B L-1: deletes on a volume that is out of inodes.**
  - Add a lock fallback that needs no inode.
  - Remove legacy `*.meta.json.lock` files at startup: only files matching that exact pattern, directly inside the root.
  - Make the test double fail `mkdir` too.
  - Scope `CHANGELOG.md:93-94` and juniper-data's `docs/REFERENCE.md:1374-1375`.
- **Lane B L-2 / lane A N-4:** open `locks/` once, with `O_DIRECTORY|O_NOFOLLOW`, and open each stripe through `dir_fd`. Add tests with live-target symlinks, and a test for the containment refusal (MX13, MX14, MX23, MX24).
- **Lane B L-3 / lane A L-1:** scope "a storage fault is a 500" in the title, `CHANGELOG.md:117-118` and `juniper_data/api/routes/datasets.py:546-547`. Optional: map unparseable metadata to a 500, and refuse timezone-naive cursors. If skipped, record them as known issues.
- **Lane B L-5:** a two-process create test, a late named create, and a late create whose content differs (MX10, MX1, MX9).

NIT:
- lane B N-1 through N-6;
- lane A N-1, N-3, N-5, N-7, N-8 and N-9;
- `juniper_data/api/routes/datasets.py:1282`: `record_access` fires on the `GET /{id}` read and the artifact download only;
- the PR body's counts: 16 of the 17 base failures are their own defect, and `[0.16.0]` is 261 lines;
- `[0.16.0]` must stay byte-identical to the `v0.16.0` tag.

**The verification bar:**
- unit; coverage; api+integration;
- the harness, extended with an arm per new fix; the harness-coverage counter;
- `juniper-symbol-loss-check --scope 'juniper_data/**' --base 0f0f7e0e`, and the docs screen;
- lane B's probes re-run against `d1c66a11` and against the new head;
- pre-commit on every changed file, and the equivalence runs if `http_cache.py` is touched (brief 2).

**Out of scope:**
- data438's F8 (the owner's);
- L7 (a known issue);
- data428 round-3 A1 F2 and F4 (the closes PR files or declines them; A1's F3 is already `APD-DATA-056`);
- `juniper_data/api/security.py`, which the peer lane owns.

## Appendix D: the predecessor's items

- **Remaining 1 (validate #438's fix):** overtaken. #438 merged unfixed, so its fixes became the fix-forward.
- **Remaining 2:** done as #2088.
- **Remaining 3:** Appendix A.
- **Remaining 4 (canopy nit):** handed off as F-CANOPY-060, reserved.
- **Remaining 5:** done by #2084.
- **Remaining 6:** v0.16.0 is published. #2081 merged, but its CodeQL question is still open (Appendix B). The rest is Appendix B.
- **In flight 1 (executor `adf9f5dbe46b1b03c`):** killed when `8f86dec2` ended. Its work was rescued into the fix-forward branch.
- **In flight 2 (#2081's CodeQL):** #2081 merged at 22:45:08Z (Appendix B).
- **In flight 3 (the peer):** carried by its own handoff (Remaining 0): validating #690 and canopy#685, the F2–F10 fix-forwards, and the releases.
- **Its traps are all carried in Key context and traps.**

## Appendix E: the fork-drift marker plan (Remaining 5)

Measured by the handoff validations (`handoff-2fba4397-round{1,2}-laneF-reprobe.md`). Re-verify before coding.
- **Pin a PAIR:** `encode("utf-8", "surrogatepass")` and `compare_digest(presented,`.
  - **Not the bare word `surrogatepass`.** Every copy also carries it in a comment or docstring (service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`), and the matcher is a whole-file substring test (`tests/test_service_fork_drift.py:289`).
  - The code-only anchors: service-core `juniper_service_core/security.py:88`/`:91`; canopy `src/security.py:52`/`:137`; data#440 `:115`/`:118`; cascor#689 `:84`/`:87`.
- **Canopy's `.encode` sits only in `_compare_bytes`** (`src/security.py:42-52`), which `:300` also uses. A revert to `presented = api_key` plus `compare_digest(presented, candidate)` at `:135-137`, keeping `_compare_bytes`, passes even the literal pair (a lone `presented = api_key` raises `TypeError` instead). The peer's F3 spy test, with its bytes-argument check, catches it.
- **Canopy's CSRF compare** (`src/csrf.py:91`, `:97`) is outside the site file.
- **Mutation-check the guard:** delete EVERY `.encode("utf-8", "surrogatepass")` in a copy of each site file (two each in service-core, data#440 and cascor#689; one in canopy, `:52`), and confirm the guard fails. The matcher is a substring test, so deleting only the first call leaves the marker.
- **PR CI will not catch a premature marker.** `ci.yml:500` runs the whole file but skips every fork site that has no siblings, so it merges green and fails the next weekly `docs-full-check` run on `main`. Test before pushing with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` against a SCRATCH ecosystem root: `git -C <clone> archive origin/main | tar -x -C <root>/<repo>` for data, cascor and canopy, with your tree at `<root>/juniper-ml`. The shared checkouts lag `origin/main`.
- **The same change:**
  - corrects `tests/test_service_fork_drift.py:205-209`, "no behavioural test can tell them apart", which the peer's F3 spy test refutes: it counts `compare_digest` calls, so it kills the F8 mutant (a `break` after `matched = True`) that survives every suite today;
  - cites a register id: APD-ECO-013, so land it with or after the closes PR;
  - updates every guard count: juniper-ml `docs/REFERENCE.md` about L2977, and the register about L240, L252, L1106 and L1751, plus its §2.3 guard table.

## Appendix F: documents this session created or changed

- **Merged in #2088:**
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
  - `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`
  - `docs/REFERENCE.md`
  - `reports/2026-09-24_defect-register-round-42/register-fixforward2-round{1,2}-lane{A-reprobe,B-refute}.md`
  - in `util/ad-hoc/`: `2026-09-24_register_round42_second_fixforward{,_corrections,_round2}.py`, `2026-09-24_register_primer_citation_census.py`, `2026-09-24_primer_toy_error_paths_probe.py`, `2026-09-24_primer_toy_pin_mutation_check.py`, `2026-09-24_archive_round42_reports.py`
- **On #2089:**
  - `util/ad-hoc/2026-09-24_round42_probes/README.md` and six lane directories
  - `util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py`
  - `util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py`
- **Uncommitted:** see Git status.
- **Memory (outside the repo):**
  - `reference_git_trailer_must_be_last_paragraph.md`
  - `reference_typed_escapes_become_real_characters.md` (new; linked from `reference_backticks_eaten_in_shell_messages.md`)
  - `reference_backticks_eaten_in_shell_messages.md`
  - `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`
  - `MEMORY.md`
