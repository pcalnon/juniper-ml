<!-- Archived verbatim 2026-09-24 from subagent a6664729992745f8d of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS

The snapshot's facts hold up: every merge, SHA, timestamp, count, line anchor and verification output I re-checked matches. The problems are in what a fresh session can act on. Four HIGH corrections should be applied before the handoff is used; none needs a factual rewrite. I made no edits to any repository and my scratch directory is deleted.

**Documents cited:**
- The snapshot: `handoff_session_r1_frozen.md` (sha256 `1e5db1832f6131a8…`, verified).
- Its live archive: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. It is untracked, and already differs from the frozen text in one line (the MEMORY.md item).
- The handoff procedure: `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.
- The predecessor handoff: `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.
- The round-39 handoff: `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`.
- The register: `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
- The primer: `JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.

## Per-item table

| Item | First three actions a fresh session takes | Runnable? (what happened) | Blocker |
|---|---|---|---|
| Verification commands (`handoff_session_r1_frozen.md` L84-89) | Run all six as written | **Yes.** No sandbox refusal, even with `&&`, `|` and `;`. Results: #2088 MERGED 23:41:16Z `5af9d722…`; `136 rows \| 100 fixed \| 36 open`; `AGREE`; `36`; `d1c66a112e4b…`; open PRs data#440, cascor#690, cascor#689. | Command 2 reads the working tree, not `main` (M9). Nothing checks the in-flight state (M9). |
| In flight 1: executor `a46e715a6801b98ca` | (1) Read the data branch's ref. (2) `git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status --short`. (3) Find the executor's disposition report and brief. | (1) Yes: still `d1c66a11`. (2) Yes: **8 modified files**, executor mid-edit. (3) **No path given.** It is `~/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`, still being written at 00:07Z on 2026-09-25. | H3 |
| Remaining 1: #2088 delta | (1) `git diff --stat 990ef3f9 2439d049`. (2) Launch two lanes. (3) Archive with `util/ad-hoc/2026-09-24_archive_round42_reports.py`. | (1) Yes: 11 files. (2) How to run a lane is not stated. (3) The archiver exits "not in SESSION_IDS" for any new session. | M4, L6 |
| Remaining 2: data fix-forward | (1) Verification command 5. (2) Read the disposition report. (3) Open the PR from the drafts. | (1) Yes. (2) Location not stated. (3) The drafts exist only on tmpfs; the promised copy `data438-fixforward-pr-draft.md` does not exist; `util/open_signed_pr.py` refuses an existing branch. | H3, H4, L2, M2 |
| Remaining 3: closes PR | (1) Check the gates: `gh pr view 690 --repo pcalnon/juniper-cascor` gives OPEN `78e99414`. (2) `python3 util/ad-hoc/register_open_set.py`. (3) Write an editor and open a signed PR. | (1) and (2) yes. APD-ECO-013, APD-ECO-014 and APD-CASCOR-014 are free ids; the eight rows to close are all open. (3) How is not stated. | Gates not yet met, which is correct. M3, M6, M8 |
| Remaining 4: fork-drift marker | (1) Check data#440 and cascor#689: both OPEN. (2) Read the `GUARDS` in `tests/test_service_fork_drift.py`. (3) Add a new ENFORCED `Guard`. | Yes. The gating claim is correct: status is per-guard, so a `KNOWN_GAP` would fail at the two sites already merged. The marker text is present at service-core `security.py:88,91` and canopy `src/security.py:52`. | The PRs are open. `docs/REFERENCE.md` has no "drift-gate section"; the text is the suite bullet at L2972 (N7). |
| Remaining 5: two candidates | (1) Read primer lines 4742 and 2687. (2) `git -C …/juniper-data grep RequestValidationError FETCH_HEAD -- juniper_data/api/`. (3) Write a probe. | (1) and (2) yes. **The premise is stale:** juniper-data `main` registers the handler. (3) Not run, because it writes. | M5 |
| Remaining 6: PATCH #2080 | (1) `gh pr view 2080 --json body`. (2) Read `ml2080-round1-laneA-reprobe.md` line 156 (N6). (3) `gh api -X PATCH …/pulls/2080`. | (1) and (2) yes: the "A-nit on `APD-ML-008`" bullet is under "Rejected, with reasons". (3) Not run, because it writes. | None |
| Remaining 7: owner decisions | Check each item is still open, then ask the owner. | **APD-DATA-047 was already RATIFIED** on 2026-09-21. MEMORY.md measures 25,125 bytes / 24,929 characters. | M1 |
| Appendix A | As for Remaining 3, plus finding the peer report. | The peer report is only in worktree `happy-skipping-hollerith`. The cascor anchors resolve at `7f4a7213`: `test_cfg_03_sentry_dsn_resolution.py:25`, `main.py:231`, `conftest.py:37`. | M6, M8, L4 |
| Appendix B | Open the round-39 handoff at §0. | Yes, it is on `main`. Every listed id is open **except APD-DATA-047**. | M1, L9 |
| Appendix C | Check the drafts, then the anchors at `d1c66a11`. | The drafts are on tmpfs. All four anchors resolve, but the bare `constants.py` matches three files. | H4, M7, L3 |
| Appendix D | Diff it against the predecessor. | The item mapping is correct. | Three traps and the peer re-route instruction were dropped (M2, M3). |

## Findings

### HIGH

**H1. The Git status lists two of the six uncommitted entries, and nothing stops a successor from "syncing" the worktree and destroying the only copy of the extractor change.**
- **Quote:** "**Uncommitted:** `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M) and `reports/…/owner-ruling-key-leaks-verbatim.md` (??)" (`handoff_session_r1_frozen.md` L94). Also "their reports are archived in `reports/2026-09-24_defect-register-round-42/`" (L32).
- **Evidence:**
  - `git status --short` shows four more entries:
    - `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M), whose only change is the two `MISSING` entries for the data round-1 reports;
    - `data438-fixforward-round1-laneA-reprobe.md` (??);
    - `data438-fixforward-round1-laneB-refute.md` (??);
    - the handoff's own archive (??).
  - Verification command 4's count of 36 includes the two untracked reports.
  - The branch is 3 unsigned scratch commits ahead of `origin/main` and 5 commits behind it (`c32e5f2a`…`5af9d722`).
  - `git grep -e '--topic' origin/main -- util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` finds nothing. The `--topic key-leaks` mode that `owner-ruling-key-leaks-verbatim.md`'s header names exists only in the uncommitted copy.
  - `git reset --hard origin/main` is the natural way to drop "never push" commits and catch up, and it would erase that mode. `git clean` would delete the four untracked files.
- **Replacement for L94:**
  - "**Uncommitted, six entries; ship ALL of them in the next juniper-ml PR:**
    - `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M: adds `--topic key-leaks`, which exists nowhere else);
    - `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M: the two data round-1 `MISSING` entries);
    - untracked `reports/2026-09-24_defect-register-round-42/{owner-ruling-key-leaks-verbatim,data438-fixforward-round1-laneA-reprobe,data438-fixforward-round1-laneB-refute}.md`;
    - this handoff's archive `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
  - **Do not `git reset`, `checkout`, `clean`, `stash` or remove this worktree until those six have shipped.** Never `git commit` or `git push` here.
  - Ship with `util/open_signed_pr.py --repo juniper-ml --branch <new> --add <local>:<repo path> …`, which makes a signed commit on a new branch from `origin/main`. Uploads are whole-file, so check each file against `git show origin/main:<path>` first."
- **Replacement for L32:** "archived (UNTRACKED; see Git status) in `reports/…`".

**H2. The heading says to paste only the Goal, but the Goal depends on sections outside it and never names its own file.**
- **Quote:** "## Goal (paste this as the new thread's first prompt)" (`handoff_session_r1_frozen.md` L6). Inside it: "Appendix A has the full checklist", "The brief, condensed, is in Appendix C", "(Git status)".
- **Evidence:**
  - Appendices A–D, the verification commands and the Git status are all separate `##` sections after the Goal.
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` Step 3.1 has the Goal used as the first prompt. juniper-ml `AGENTS.md` requires the verification commands to be "in the handoff prompt".
  - The document names its own archived file nowhere, and that file is untracked in `fizzy-hugging-dream` only.
  - So a successor given only the Goal loses the closes-PR checklist, the executor brief, the draft locations, the juniper-data worktree path and the verification commands.
- **Replacement:**
  - Heading: "## Goal (paste the WHOLE document, appendices included, as the new thread's first prompt)".
  - Add as the Goal's second sentence: "The full handoff, with Appendices A–D, the verification commands and the Git status, is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. It is UNTRACKED in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream` until it ships. Read it and run its verification commands before acting."

**H3. The in-flight executor has no liveness test, no stated location for its report or full brief, and no recovery recipe.**
- **Quote:** "If this session ends first, its uncommitted work stays in the juniper-data worktree (Git status); finish it from there." (`handoff_session_r1_frozen.md` L41). Also "check it against both reports and its own disposition report" (L53).
- **Evidence:**
  - At 00:07Z on 2026-09-25 the executor was alive: its transcript reached 4.87 MB, and the juniper-data worktree had 8 modified files (`app.py`, `routes/datasets.py`, `storage/{base,constants,local_fs}.py` and 3 tests). The ref was still `d1c66a11`.
  - The executor was resumed by SendMessage at **23:48:49Z**, after the snapshot's "about 23:40Z". Its 8,561-character brief exists only as that `user` record in its transcript.
  - An open parent session keeps its subagents running, so a successor may start while the executor is still editing the same worktree.
  - The predecessor `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (In flight 1) gave the report path and said to read it with `last_report()`. This snapshot drops both.
  - The recovery recipe exists only in the memory file `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`.
- **Replacement (append to In flight 1):**
  - "**Is it alive?** Run `stat -c '%y %n' /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`. If it was written within about 10 minutes, the old session is still running: do not touch the juniper-data worktree. Ask the owner to close that session, or wait.
  - **Its disposition report** is the last assistant message in that file; read it with `last_report()` in `util/ad-hoc/2026-09-24_archive_round42_reports.py`. **Its full brief** is the `user` record at 2026-09-24T23:48:49Z; Appendix C is only its summary.
  - **If it died with the worktree dirty and the ref still at `d1c66a112e4bc70ee97496a14265f7b90e10fb88`:** save that brief to your scratchpad. Launch a new `task-executor` in your own session on the same worktree, with the brief, both round-1 reports and the drafts. Tell it to review the uncommitted diff first and to push with that full `--expected-head`. A dead subagent cannot be resumed from another session."

**H4. The PR drafts exist only on tmpfs, the promised copy does not exist, and the executor is still changing the drafts.**
- **Quote:** "That directory is on tmpfs, so this session copies the final drafts to `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md` before it ends." (`handoff_session_r1_frozen.md` L159)
- **Evidence:**
  - The scratchpad holds `data_fixforward_pr_title.txt` (153 B) and `data_fixforward_pr_body.md` (18,298 B). No `data438-fixforward-pr-draft.md` exists anywhere.
  - Line 75 of the executor's 23:48:49Z brief tells it to "Update the drafts … Add a section for this round". It dies when this session ends, so a copy made "before it ends" can predate the executor's edits.
  - The snapshot does not say how one file will hold both title and body, or that the copy must be shipped.
- **Replacement:** "The drafts are `data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md` in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/` (tmpfs). The copy is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md`: the title on line 1, a blank line, then the body. It is UNTRACKED; ship it with the Git status files. It was taken at `<time>` and may predate the executor's round-2 section. If neither copy survives, rebuild the body from the two `data438-fixforward-round1-*` reports and the executor's disposition report (In flight 1)."

### MEDIUM

**M1. APD-DATA-047 is presented as a pending owner decision, but it was ruled on 2026-09-21.**
- **Quote:** "plus `APD-DATA-047`, the 1e11 ceiling, which is an owner decision" (`handoff_session_r1_frozen.md` L148). Also "sequencing C-A…D-G, and APD-DATA-047's ceiling" (L69).
- **Evidence:**
  - `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` L1284 reads "**FIXED (RATIFIED by the owner, 2026-09-21 — the ceiling STAYS, at `1e11`…**", with §5.1 at L1661. The id is not in `register_open_set.py`'s open list.
  - The round-39 handoff that Appendix B cites says "**`APD-DATA-047` is RULED**" (L52) and "Owner decisions still owed — NONE, as of 2026-09-21" (L278).
  - The claim also contradicts Appendix B's own "All are ruled" (L140).
- **Replacement:**
  - L148: "D-G: `APD-DATA-048/-049/-051`. (`APD-DATA-047` was RATIFIED at 1e11 by the owner on 2026-09-21 and is closed; do not re-ask.)"
  - L69: "sequencing C-A…D-G."

**M2. The peer lane is never identified, and the predecessor's re-route instruction was dropped.**
- **Quote:** "Send the PR number to the peer lane." (`handoff_session_r1_frozen.md` L56). Also "the canopy E2E session" (L24), "canopy combined's handoff" (L24) and "The containers session owns it." (L70).
- **Evidence:**
  - The predecessor handoff (In flight 3) named the peer "defect reg [042116]" (session `bc31e993`). It said the peer "sends PR numbers and SHAs to 'defect reg [977fa8]', so **message it with your own session's name to re-route them.**"
  - This snapshot names this session only as "defect reg", with no `[ref]`. The memory file `reference_cross_session_sendmessage_undeliverable.md` says to add the ref because two defect-register sessions share that name.
  - After the handoff, the peer will report to a dead session.
- **Replacement (add to Key context):**
  - "Peers, by `ListAgents` name: the key-leaks and bytes-compare lane is **"defect reg [042116]"** (session `bc31e993`, worktree `happy-skipping-hollerith`). This session is "defect reg [<ref>]".
  - **First action: run `ListAgents`, then SendMessage the peer your own session name so its PR numbers and SHAs reach you.**
  - Name the canopy E2E, canopy combined and containers sessions the same way."

**M3. Three predecessor traps that bear directly on the remaining work were dropped.**
- **Evidence:** the predecessor handoff's Key context had these, and `handoff_session_r1_frozen.md` does not:
  - "Uploads are whole-file. Rebuild every file from `origin/main` right before opening a PR … compare with `git show origin/main:<p> | diff - <p>`." This worktree is now 5 commits behind `origin/main`.
  - "Never name an OPEN id on the register's §2 status line (about L177). The crosscheck reads every id there as closed." The closes PR edits that line.
  - "/tmp is a ~1M-inode tmpfs. Lane trees filled it to 100% today." `df -i /tmp` now reads 81% used, 199,433 free, and four more lanes are owed.
- Appendix D reconciles only the predecessor's In flight and Remaining items, so this loss does not show there.
- **Replacement:** add those three bullets to Key context, using the predecessor's wording above, and add `df -i /tmp | tail -1` to the verification commands.

**M4. How to run a lane and archive its report is not stated.**
- **Quote:** "Run two lanes (re-derive; refute), archive their reports" (L44). Also "add their `MISSING` entries in `util/ad-hoc/2026-09-24_archive_round42_reports.py`" (L55), and "harness 62/62" (L18), all in `handoff_session_r1_frozen.md`.
- **Evidence:**
  - Every earlier lane was a background `general-purpose` Agent; the metadata of `a6afb722d69732ae5` and `a641405b9532742e6` shows this.
  - No lane brief is archived in the repo.
  - `subagents_dir()` exits "not in SESSION_IDS; add its full id" for any session other than `bc31e993`, `8f86dec2` and `2fba4397`.
  - The archiver's `HEADER` hard-codes the date 2026-09-24.
  - "Harness" means `util/ad-hoc/2026-08-13_run_primer_examples.py`, which builds its own venv unless given `--venv`.
  - `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` *requires* `--venv` and `--scratch`. The only such venv is `scratchpad/primer-venv`, on tmpfs.
- **Replacement:**
  - "A lane is a background `general-purpose` Agent. Launch both in ONE message, each with a different lens: A re-derives every claim from source; B tries to refute and defaults to REFUTED.
  - Give each its own scratch subdirectory. Tell it to put any compound shell in a script.
  - Ask for the report format of `register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
  - To archive: add your own session's full UUID (the directory above your scratchpad) to `SESSION_IDS`, add the `MISSING` entries, run with `--check`, then run without it.
  - The harness is `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --keep`. Pass the venv it keeps to the mutation check's `--venv`."

**M5. Candidate 5(a)'s premise about juniper-data is stale, and its wording would exclude juniper-data.**
- **Quote:** "(a) Any FastAPI service without its own `RequestValidationError` handler answers a lone-surrogate echo with a 500 … Primer line 4742 says juniper-data registers none." (`handoff_session_r1_frozen.md` L61-62)
- **Evidence:**
  - juniper-data `main` (fetched 2026-09-25) registers `@app.exception_handler(RequestValidationError)` at `juniper_data/api/app.py:187-188` (APD-DATA-013). Its docstring says it is "deliberately byte-identical to FastAPI's built-in handler", and it returns `JSONResponse(content={"detail": jsonable_encoder(exc.errors())})`. So the same failure probably applies to it.
  - Primer lines 4742-4743 describe an older app ("only the `ValueError` and `Exception` ones at `app.py:152` and `:160`").
  - juniper-cascor `main` also registers one, at `src/api/app.py:856`.
- **Replacement:** "(a) Any FastAPI service whose 422 renders through Starlette's `JSONResponse` probably answers a lone-surrogate echo with a 500. That includes FastAPI's default and juniper-data's APD-DATA-013 handler at `juniper_data/api/app.py:187`, which copies the default byte for byte; check cascor's at `src/api/app.py:856` too. Primer lines 4742-4743 are also stale: they say juniper-data registers no such handler."

**M6. Appendix A leaves the status and owner-gating of two new rows ambiguous.**
- **Quote:** "**File** (ruled, fixes shipped or in flight, so not parked)" (L103). Also "`APD-ECO-014` … Fixed by canopy#685." (L113), and for `APD-CASCOR-014`: "cascor#689's `include_local_variables=False` removes the locals, not the events." (L119). All are in `handoff_session_r1_frozen.md`.
- **Evidence:**
  - The snapshot's gate rule (L99) is "close a row only after its PR merges AND its own validation holds". canopy#685's validation is never stated, so a successor cannot tell whether to file APD-ECO-014 open or FIXED.
  - APD-CASCOR-014 has no fix shipped or in flight. The peer report `bytes-compare-ml2086-data440-cascor689-validation.md` F4 only proposes a `conftest.py` change.
  - The ruling options in `owner-ruling-key-leaks-verbatim.md` name byte comparison and Sentry's local-variable capture, not a test suite that starts the real SDK. So "ruled … not parked" is unsupported for that row.
- **Replacement:** "File `APD-ECO-014` OPEN, with canopy#685 as its fix, and close it once canopy#685's validation is cited. File `APD-CASCOR-014` OPEN and PARKED for an owner ruling: no fix is in flight, and the Key-leaks ruling does not name it."

**M7. This session's lane probe scripts exist only on tmpfs.**
- **Quote:** "Evidence, file:line and probe scripts are in the two round-1 reports." (`handoff_session_r1_frozen.md` L162)
- **Evidence:**
  - The reports only name the scripts. `data438-fixforward-round1-laneB-refute.md` §Scripts says they are in "`/tmp/claude-1000/…/2fba4397-…/scratchpad/r42d/laneB/scripts/`".
  - This session's six lanes left **195** scripts under `scratchpad/r42b`, `r42b2` and `r42d`.
  - The executor's evidence (`scratchpad/r4/*.out`) is also only there. I re-read it: 1901 passed, 97.76%, 118 passed, "PASS: 70 mutations" and 3,495,583 checked / 0 mismatches all reproduce.
  - juniper-ml#2081 set the precedent of preserving probe scripts off tmpfs, but `util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py` is hard-coded to session `8f86dec2`.
- **Replacement:** "The probe scripts are only in this session's tmpfs scratchpad (`r42b`, `r42b2`, `r42d`: 195 scripts). Copy them into `util/ad-hoc/2026-09-24_round42_probes/` the way #2081 did, with a copier modelled on `util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py`, and ship them in the next juniper-ml PR."

**M8. Documents owned by other sessions are cited without a path.**
- **Quote:** "canopy combined's handoff" (L24), "Source: `bytes-compare-ml2086-data440-cascor689-validation.md`" (L112) and "F-CANOPY-060, -061 and -062 are reserved" (L24), all in `handoff_session_r1_frozen.md`.
- **Evidence:**
  - The canopy combined handoff is `…/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`. It is untracked and not on `main`.
  - The canopy E2E session's reservation is in `…/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`, also untracked.
  - I found both only with a sweep of every worktree. It finished with exit 0, and those plus a consensus draft beside the first were its only hits outside this session's own handoff.
  - The peer report is untracked, in `…/.claude/worktrees/happy-skipping-hollerith/reports/2026-09-24_defect-register-round-42/`.
  - F-CANOPY-060..062 appear on neither repo's `main`. The canopy E2E ledger, juniper-ml's `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, does not carry them.
- **Replacement:** give each as an absolute path, marked "(untracked, another session's worktree; read only)".

**M9. The verification commands do not cover the in-flight state, and command 2 does not read `main`.**
- **Evidence:**
  - None of the six commands checks the executor, the juniper-data worktree, the drafts, `/tmp` inodes or this worktree's own status.
  - In command 2, `git fetch origin &&` suggests the check reads `main`. `register_open_set.py` actually reads the working tree, which is 5 commits behind `main`. The two are identical today, but will not be once the closes PR merges.
- **Replacement:** add the following. Each ran here, and the sandbox allowed `git -C` into the juniper-data worktree.
  ```
  git status --short   # 6 entries
  git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status --short
  stat -c '%y %n' /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl
  ls -la reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/data_fixforward_pr_*
  df -i /tmp | tail -1
  ```
  Annotate command 2: "reads this worktree's copy; use `git show origin/main:<path>` once `main` moves".

### LOW

- **L1. The abbreviated `--expected-head` would be refused.** Quote: "`--expected-head d1c66a11…`" (L39), and "re-running with the same `--expected-head` is safe" (L75), in `handoff_session_r1_frozen.md`. `util/push_signed_commit.py --help` says the head "must be the FULL 40-hex sha; an abbreviation is refused before any API call". Replace with `d1c66a112e4bc70ee97496a14265f7b90e10fb88`. The executor's own brief already uses the full SHA.
- **L2. Opening the data PR and updating the branch have no stated mechanism.** `util/open_signed_pr.py` refuses a branch that already exists (exit 1). Add: "Open it with `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<line 1>" --body-file <body>`. Update-branch is `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<full sha>`."
- **L3. Appendix C uses bare file names.** `constants.py:45-47` (`handoff_session_r1_frozen.md` L170) matches three juniper-data files; the stripe text is in `juniper_data/storage/constants.py:45-47`. Write the others in full too: `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/local_fs.py:200-202`, `juniper_data/api/routes/datasets.py:1282`. All four resolve at `d1c66a11`.
- **L4. Two adjacent bullets say "#678" and mean different repos.** "#678's squash message is stale" (L126) is cascor#678: squash `0e016a7`, described in `cascor678-postmerge-validation.md` §"Squash message" as "wrong on six counts". "#678's mutation script" (L127) is juniper-canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py`, whose retire condition is "the APD-ECO-008 follow-up to juniper-canopy#660 is merged". Prefix both with the repo, and add "(record only; retiring an ad-hoc script is the owner's decision under `util/ad-hoc/README.md`'s Lifecycle section)".
- **L5. `0bee089e` is never identified, and the re-check is framed as conditional.** Quote: "at `0bee089e`; re-check if either moves" (L57). `0bee089e` is data#440's head. The fix-forward branch *will* move, because the executor edits `CHANGELOG.md`, so the re-check is certain.
- **L6. The traps refer to tools by role only.**
  - "The three editors" (L76) are `util/ad-hoc/2026-09-24_register_round42_second_fixforward{,_corrections,_round2}.py`. Each is single-use and "refuses to run twice", so a successor models a new editor on them rather than re-running one.
  - "The census" (L77) is `util/ad-hoc/2026-09-24_register_primer_citation_census.py`. It now reports "69 citation(s), 82 number(s)".
  - "The symbol screen" (L13, L74) is `juniper-symbol-loss-check --base c061a99f --head 5af9d722`. I re-ran it and it prints the claimed `waived (Allow-Symbol-Loss): const:SESSIONS`.
- **L7. The merge scope is ambiguous for the peer's PRs.** Quote: "Merge approval is granted for this arc's PRs … other sessions' PRs are not covered" (L8). The peer's PRs are both this arc's and another session's. Add: "Never merge data#440, cascor#689 or cascor#690."
- **L8. The juniper-data worktree could be swept by its name.** Its directory says `round3-followups`, but it holds `fix/conditional-requests-round4-followups` with uncommitted work. Add "do not remove".
- **L9. Appendix B omits two §0 items.** It says its items are "defined in … §0" of the round-39 handoff, but leaves out §0.4's two items that have no register row: `equities_seq`'s unread `data_quality`, and `val_ratio` leaving canopy's sidebar. The predecessor handoff dropped them too.

### NIT

- **N1.** The Goal is 1,328 prose words against the procedure's ~1,200 target, which is within its IQR of 778–2,718.
- **N2.** "MEMORY.md at 25.2 KB" (L68) measures 25,125 bytes / 24,929 characters. The live archive has already rewritten this line.
- **N3.** "#2081" (L27) and "#2080" (L63) need a `juniper-ml` prefix.
- **N4.** "`# d1c66a11… unless corrected`" (L88) would read better as "until the executor pushes; after that, a signed commit whose parent is `d1c66a11`".
- **N5.** The extractor's `SESSIONS` → `SESSION_IDS` rename will show `[WARN/LOST] const:SESSIONS` in the symbol screen. I measured this in a throwaway repo: it exits 0 and does not block. #2088 waived the same symbol, and `Allow-Symbol-Loss: const:SESSIONS` in the commit body would keep the screen quiet.
- **N6.** "Auto-start binds wholesale" (L125) gives no source. It comes from the peer's `cascor686-fixup-implementation-report.md` item 2, and from `pending-items-snapshot-2026-09-24T1110Z.md:40`.
- **N7.** `docs/REFERENCE.md` has no "drift-gate section" heading (L59). The text meant is the `tests/test_service_fork_drift.py` bullet at L2972 in its Test Suite Reference.

**Procedure compliance** (`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`):
- Goal length: 1,328 words (N1).
- Verification commands: all six are present, run and match, but they sit outside the Goal (H2) and miss the in-flight state (M9).
- Git status: present but incomplete (H1).
- Archive filename: conforms to Step 4.
- "What to verify first": never stated (H2, H3).

**Sandbox refusals:** one. `git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree list` was refused ("redirects git to the shared checkout via -C"). The snapshot asks for no such command.

## What I could not verify

- The executor's eventual push, its disposition report, and whether a round-2 section lands in the drafts. It was still mid-edit when I finished.
- canopy#685's own validation, and the source of its residue list (`handoff_session_r1_frozen.md` L129-134).
- Whether the owner meant the Key-leaks ruling to cover APD-CASCOR-014.
- The Completed figures that need the tmpfs venv: harness 62/62, 12/12 caught, and 27/27 with 25 differing. The scripts exist and their arguments match.
- The "typed JSON escapes" trap (L78).
- v0.16.0's PyPI time of 18:35Z (the parent `AGENTS.md` states it independently), canopy#683's SHA, and the notify-consumers 403.
- Whether the old session will stay open after the handoff.

**Changed:** no repository file. `git fetch` updated FETCH_HEAD in juniper-cascor, juniper-canopy and juniper-data, and this worktree's own `git fetch origin` ran as part of verification command 2. The scratch scripts and a throwaway git repo under `…/scratchpad/hv1/laneP/` were created and then deleted.
