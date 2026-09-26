# Handoff: defect-register round 42. The second fix-forward merged as ml#2088, the data fix-forward was refuted before its PR and is being fixed, and the closes PR is owed

**From:** session `2fba4397` (`ListAgents` name **"defect reg [24f8d8]"**), in worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. **Written:** 2026-09-24/25, about 00:25Z.
**This file:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`. It is UNTRACKED in that worktree until it ships (Git status).
**Predecessor:** `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (session `8f86dec2`). Appendix D accounts for every item in it.
**Superseded if consolidated:** the owner asked for this handoff to be merged with two others (Remaining 0). If that consolidated handoff exists, work from it instead.

## Goal (paste the WHOLE document, appendices included, as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem.
- The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.
- **The owner's policy:** the PR sweeper is theirs and its merges are intended. Validate a pushed branch before opening its PR when a validated merge matters; otherwise validate after merge and fix forward.
- **Merge approval does NOT carry to a new session** (memory `feedback_headless_merge_approval_policy.md`). The owner granted it to session `2fba4397` for this arc. Get your own grant before any merge action.
- **Never merge** another lane's PRs: data#440, cascor#689, cascor#690, or any the peer lane opens.

**First actions, in this order:**
1. Run the verification commands below.
2. Check the executor's liveness (In flight 1). If it is alive, do not touch the juniper-data worktree.
3. Run `ListAgents`, then SendMessage the peer lane, **"defect reg [042116]"** (session `bc31e993`), your own name and `[ref]`. It sends its PR numbers and SHAs to this session otherwise.
4. Ship the uncommitted files (Git status). Until they ship, **never `git reset`, `checkout`, `clean`, `stash` or remove this worktree.**

**Completed** (this session):
- **juniper-ml#2088 MERGED at 23:41:16Z as `5af9d722`.** It is the second register and primer fix-forward, from `ml2080-round1-laneA-reprobe.md` / `-laneB-refute.md`.
  - It was validated before its PR opened, in two rounds; the four reports ship with it.
  - Round 2's MEDIUM was a regression round 1's own fix introduced: a lone surrogate turned the toy's 422 into a plain-text 500. It is fixed, and so is the same class in the list route.
  - At the head: harness 62/62; mutation check 12/12; probe 27/27; register 136 rows | 100 fixed | 36 open, AGREE.
  - On `main`, the probe differs in 25 cases under CPython 3.13.13, and 24 under 3.14.2, where `main` already answers the deep cursor.
  - Post-Merge Main Verification and CodeQL passed. The symbol screen honours the `Allow-Symbol-Loss` waiver on the merge (see Traps).
- **juniper-ml#2089 OPEN,** head `a2fa3ad8`, not armed at open. It preserves this session's 129 lane probe scripts off tmpfs, in `util/ad-hoc/2026-09-24_round42_probes/<report stem>/`, as #2081 did for `8f86dec2`'s.
  - At the peer's request, its README also carries the peer lane's four probe-directory rows, so the file has one editor. The peer's own PR adds those directories.
  - CodeQL may flag the probes, as it did #2081's.
- **The juniper-data fix-forward** was built on branch `fix/conditional-requests-round4-followups` @ `d1c66a112e4bc70ee97496a14265f7b90e10fb88`.
  - Its parent is `0f0f7e0e`, juniper-data#438's merge. #438 merged at 18:52Z before its fix-in-place landed.
  - The branch answers every finding in `data438-round1-lane{A-reprobe,B-refute}.md`. F8 is left to the owner; L5 and L7 are disclosed.
  - It was then **validated before any PR, and REFUTED.** Lane A (`data438-fixforward-round1-laneA-reprobe.md`): the behaviour reproduces and several text claims do not; 2 LOW, 9 NIT. Lane B (`data438-fixforward-round1-laneB-refute.md`): 1 MEDIUM, 5 LOW, 6 NIT.
  - **The MEDIUM is a regression the branch introduces.** `record_access` runs on the event loop and blocks on the process-global `_version_lock`, which `save_versioned` now holds for a whole save, unnamed creates included. One 80 MB create froze the service for 6.6 s, against 0.01 s on `main`. That is past the readiness probe's 5 s timeout; the probe needs three failures in a row to act.
- **The "Key leaks" ruling is extracted verbatim** into `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`: asked 10:22:00.792Z, answered 18:30:09.820Z, "Fix everywhere now (Recommended)".
- **Canopy items were handed to the canopy sessions** (Appendix A, Residue).
- **Resolved since the predecessor:**
  - juniper-data 0.16.0 is on PyPI (18:35Z);
  - juniper-ml#2081 merged 22:45:08Z (`7e8c7ff9`);
  - juniper-ml#2086 merged 20:37:13Z (`c061a99f`);
  - canopy#683 merged 19:10:20Z; canopy#685 merged 23:24:14Z (`dc5ea02e`, NOT yet validated);
  - cascor#688 merged 18:56:25Z (`7f4a7213`).

**In flight (this session's subagents die with it):**
1. **Executor `a46e715a6801b98ca`** is fixing every finding of both data lanes on the data branch. Its brief is summarised in Appendix C.
   - It pushes ONE signed commit with `--expected-head d1c66a112e4bc70ee97496a14265f7b90e10fb88`, opens no PR, and updates the PR drafts (Appendix C).
   - **Is it alive?** Run `stat -c '%y %n' /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`. If that file was written in the last ~10 minutes, the old session is still running: do not touch the juniper-data worktree; wait, or ask the owner to close that session.
   - **Its disposition report** is the last assistant message in that file. Read it with `last_report()` from `util/ad-hoc/2026-09-24_archive_round42_reports.py`, and never with `splitlines()`. **Its full brief** is the `user` record at 2026-09-24T23:48:49Z.
   - **If it died, the worktree is dirty and the ref is still `d1c66a11…`:** save that brief, then launch a new `task-executor` on the same worktree with the brief, both round-1 reports and the drafts. Tell it to review the uncommitted diff first. A dead subagent cannot be resumed from another session.

**Remaining:**
0. **Consolidate** (the owner's instruction, 2026-09-24 about 23:25Z). Merge three handoffs into one, validated by consensus with no task or context lost:
   - this file;
   - the predecessor (on `main`);
   - the peer's `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, untracked in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/prompts/thread-handoff_automated-prompts/`. Use the version the peer validates and ships; it sends the path and PR number.
   - This session had begun the consolidation.
1. **Ship this session's uncommitted files** (Git status) in the next juniper-ml PR, with `util/open_signed_pr.py`.
   - Rebuild each file from `origin/main` first (Traps: whole-file uploads).
   - Merge #2089 once it is green, with your own grant.
2. **Validate #2088's one unvalidated delta:** `990ef3f9..2439d049`, round 2's corrections. Give two lanes the whole range, archive their reports, and fix forward. How to run a lane is in Traps.
3. **Finish the data fix-forward.**
   - Check the executor's commit against both reports and its disposition report. Its MEDIUM fix is a concurrency change.
   - Run round 2 (two lanes, on the delta from `d1c66a11`) BEFORE opening the PR.
   - Open it with `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<draft line 1>" --body-file <draft body>`. `open_signed_pr.py` refuses an existing branch.
   - Then merge (your grant), archive the round-2 reports, and send the PR number to "defect reg [042116]".
   - data#440 (head `0bee089e`) also edits `CHANGELOG.md` `[Unreleased]`, and the executor edits it too: re-check that the two merge cleanly.
4. **The closes PR** (juniper-ml, register): Appendix A.
5. **The fork-drift work is this lane's**, AFTER data#440 and cascor#689 merge. Appendix E has the plan and its caveats.
   - A marker added ahead of a site merges green, because PR CI runs only `SharedPackageGuardTest` (`ci.yml:500`). It then fails the next weekly `docs-full-check` run on `main`.
   - In the same change, correct `tests/test_service_fork_drift.py:205-209`, "no behavioural test can tell them apart". The peer's validation refuted it (its F8): a spy that counts `compare_digest` calls tells `any(...)` from the flag loop.
6. **Verify against the real services, then file, two candidates.**
   - (a) A 422 that echoes the rejected input through Starlette's `JSONResponse` (`ensure_ascii=False`) is a plain-text 500 for a lone surrogate.
     - A handoff validator's probe confirmed this in a test app, for FastAPI's default handler and for a copy of it.
     - juniper-data's APD-DATA-013 handler (`juniper_data/api/app.py:187-212`, "byte-identical to FastAPI's built-in handler") is such a copy.
     - cascor has its own handler, at `src/api/app.py:856`.
     - Neither service has been probed.
     - It is a sibling of `APD-DATA-056`, a tag holding a lone surrogate. It is input to D-C.
     - Primer lines 4742-4743 have been stale since data#281: they say juniper-data registers no such handler.
   - (b) The primer's `idempotent_jobs.py` example echoes client strings through `JSONResponse` (primer line 2687). `store.complete` (2686) stores the payload before rendering it, so every replay of that key (2662) fails the same way.
7. **PATCH juniper-ml#2080's body** with `gh api -X PATCH`. Its rejection of the APD-ML-008 nit was wrong (`ml2080-round1-laneA-reprobe.md` N6); #2088 applies the nit.
8. **Owner decisions to surface:** Appendix B.

## Key context and traps (part of the prompt)
- **Routing.** Canopy combined is "canopy combined [577a1c]"; containers is "containers [2703c8]". The canopy E2E session has exited.
- **Uploads are WHOLE-FILE.** Before every push, `git fetch` and run `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`.
  - With untracked files present, compare with `git show origin/main:<p> | diff - <p>`.
  - For a shared `CHANGELOG.md` `[Unreleased]`, prove `main`'s lines are a subset of yours.
  - This worktree is 5 commits behind `origin/main`.
- **Never name an OPEN id on the register's §2 status line** (about L177). The crosscheck reads every id there as closed.
- **/tmp is a ~1M-inode tmpfs**: 82% at handoff, and it hit 100% on 2026-09-24. Brief every lane to prune.
- **Sentry.** Set every DSN variable to `""` in every test run and server: `SENTRY_SDK_DSN` (the peer reports it is exported in these shells), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN`, `JUNIPER_CANOPY_SENTRY_DSN`. Never use port 8100, 8201 or 8050.
- **How to run a lane.** A lane is a background `general-purpose` Agent.
  - Launch both lanes in ONE message: A re-derives every claim from source; B tries to refute and defaults to REFUTED. Give each its own scratch subdirectory. Tell it read-only, no secret or email egress, and compound shell in a script.
  - Report format: as in `register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
- **How to archive a report.**
  - In `util/ad-hoc/2026-09-24_archive_round42_reports.py`, add your session's full UUID to `SESSION_IDS` (the directory above your scratchpad), and the report's `MISSING` entry.
  - `HEADER` hard-codes the date 2026-09-24: change it for new reports.
  - Run `--check`, then run without it.
- **The primer harness** is `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>`, which gives 62 tests.
  - Build the venv with CPython 3.13.13, fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1 and pytest 8.4.2. This session's venv is on tmpfs.
  - `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` needs `--venv` and `--scratch`.
- **The primer is cited by bare line number: edit it in place only.** Model a new editor on `util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py`, which refuses to run twice and refuses any line move. `util/ad-hoc/2026-09-24_register_primer_citation_census.py` counts every bare number past 5758; it reads 69 citations and 82 numbers. So a new mention of a number changes the count: name a retired anchor in words.
- **GitHub's squash appends a `Co-authored-by` paragraph** after the commit messages. So `git log --format='%(trailers:key=Allow-Symbol-Loss)' 5af9d722` prints nothing, although the waiver is there. Check a merged commit with `grep -c`, or with `juniper-symbol-loss-check --base <parent> --head <sha>`, which scans lines.
- **The sweeper's merge stores the default squash body.** Put waiver trailers in a COMMIT body. To re-arm with a curated body: `gh pr merge --disable-auto`, then `--auto --squash --subject … --body-file …`.
- **Signed pushes** go through `util/push_signed_commit.py --expected-head <FULL 40-hex sha>`; an abbreviation is refused. A run can create nothing: the first push of `2439d049` printed its plan and made no commit. Check `gh api repos/pcalnon/<repo>/git/ref/heads/<branch>`; re-running with the same head is safe.
- **`strict: true`:** after every move on `main`, run `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<full sha>`. `gh pr edit` is broken; use `gh api -X PATCH`.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage: a backslash-u escape of U+2028 arrives as U+2028, and so does a surrogate pair's. Build such text with `chr()`, and check the file with `od -c`.
- **The worktree-isolation guard refuses compound shell** around git and gh. Split commands, or use a script under `util/ad-hoc/`.

## Verification commands (run from this worktree)
```
git status --short                     # 13 entries at handoff; see Git status
gh pr view 2088 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit
gh pr view 2089 --repo pcalnon/juniper-ml --json state,headRefOid,mergeStateStatus
git fetch origin && python3 util/ad-hoc/register_open_set.py | grep 'rows |'   # 136 rows | 100 fixed | 36 open; reads THIS worktree's register
python3 util/ad-hoc/register_status_crosscheck.py | tail -1                    # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c 'OK    '   # 39 here; 34 in a fresh checkout until the next PR ships its 5 reports
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # d1c66a11… until the executor pushes
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2 status --short
stat -c '%y %n' /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl
gh pr list --repo pcalnon/juniper-data --state open; gh pr list --repo pcalnon/juniper-cascor --state open
df -i /tmp | tail -1
```

## Git status
- **This worktree:** branch `worktree-fizzy-hugging-dream`.
  - It holds three unsigned LOCAL scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`), made only so the CI screens could run. **Never push or commit here.** Their content is #2088's.
- **Uncommitted: ship ALL of these in the next juniper-ml PR. Nothing else holds them:**
  - `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M): adds `--topic key-leaks`, which exists nowhere else.
  - `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M): the `MISSING` entries for the data round-1 reports and this handoff's validation reports, all of session `2fba4397`.
  - `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`, `data438-fixforward-round1-laneA-reprobe.md` and `data438-fixforward-round1-laneB-refute.md` (??).
  - The handoff-validation reports archived beside them (`handoff-2fba4397-*.md`, ??).
  - `data438-fixforward-pr-draft.md` (??): the PR drafts as copied at 00:27Z (Appendix C), before the executor's update.
  - This file (??).
  - The shipped PR's symbol screen will flag `const:SESSIONS` in the extractor, renamed to `SESSION_IDS`: put `Allow-Symbol-Loss: const:SESSIONS` in the commit body.
  - The files of #2089 (`util/ad-hoc/2026-09-24_round42_probes/`, the copier and the opener) are also untracked here. They are already on #2089's branch.
- **The juniper-data worktree:** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2`.
  - Its name says round3, but it holds `fix/conditional-requests-round4-followups` with the executor's uncommitted work. **Do not remove it.**
- **Older register-lane worktrees**, waiting for the owner's explicit cleanup signal:
  - `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`
  - `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6`
  - `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6`
  - `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f`

## Appendix A: the closes PR

**Gates.** Close a row only after its PR merges AND its own validation holds.
- `APD-CASCOR-008` / `-013`: cascor#688 merged, and its validation asked for cascor#690. #690 is OPEN at `78e99414` and not validated; the peer lane owns that validation.
- `APD-DATA-017` / `-029` / `-032` / `-057`: data#438 merged, and its fix-forward (Remaining 3) must merge and validate.
- `APD-ECO-014`, and canopy's half of `APD-ECO-013`: canopy#685 merged UNVALIDATED; the peer lane owns its validation.

**File:**
- `APD-ECO-013` (S). A non-ASCII `X-API-Key` makes the `str` `compare_digest` raise; the 500 goes to Sentry, and its local-variable capture records the real key.
  - Fixes: juniper-ml#2086 (merged), canopy#685 (merged), data#440 and cascor#689 (open).
  - **It stays open until** data#440 and cascor#689 merge, #685's validation holds, and the peer's F2 and F3 are fixed. Source: `bytes-compare-ml2086-data440-cascor689-validation.md`, untracked in `…/happy-skipping-hollerith/reports/2026-09-24_defect-register-round-42/` until the peer ships it.
    - F2 (ml#2086): no `before_send_transaction`, so with `send_pii=True` a sampled transaction carries the raw `x-api-key`.
    - F3: no CI test checks that `compare_digest` is used at all.
  - **Residue on the row unless fixed first.** The peer's successor fixes these and says which landed.
    - **F5, service-core, data and cascor only.** Add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`, to each `_ENCODING_PROBES`, and fix its false "only total AND injective" comment. It is not U+1F511, which every copy already holds. Canopy has no `_ENCODING_PROBES`.
    - F6: no observability test frame has `in_app: False`.
    - F7: cascor's AST test matches only the spelling `sentry_sdk.init`.
    - F8: see Remaining 5.
    - F9: "ASGI close 4001; HTTP 403 on the wire", in `juniper-service-core/CHANGELOG.md:58` (a juniper-ml PR) and in cascor#689's text; not data#440.
    - F10: observability's CHANGELOG line "Consumers inherit both on upgrade, with no code change" is false.
  - **Releases.** The frame-locals fix reaches no running service until juniper-observability is released and every consumer's `==0.4.0` lock moves:
    - data `requirements.lock:88`, cascor `:63`, canopy `:79`, recurrence `:70`;
    - canopy and recurrence also cap it `<0.5.0`.
    - cascor#689 fixes only cascor's CLI init (`main.py`), not the service path at `src/api/app.py:335`, which goes through the shared `configure_sentry`.
    - The service-core half reaches recurrence only after a service-core release.
    - Record why `surrogatepass` was chosen over `surrogateescape`, from the peer's report.
- `APD-ECO-014` (S): canopy's padded outbound keys leaked into logs, into Sentry and into a 409 body. File it OPEN, with canopy#685 as its fix; close it once #685's validation is cited.
- `APD-CASCOR-014` (S), the peer's F4, confirmed.
  - cascor tests that `import main` start the REAL Sentry SDK when a DSN is exported: 9 files sent 25 envelopes to a sink.
  - The cause is `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` → `src/main.py:231`.
  - The fix: in `src/tests/conftest.py`, after line 37, set the three DSN variables to `""`.
  - File it OPEN. It closes when F4's fix lands (the peer lane, a cascor#689 fixup). If the owner rules it outside "Key leaks", park it.

**Update, do not close:** `APD-DATA-055`. #438 fixed its lock half: at data `0f0f7e0e`, `batch_delete` and `delete_expired` go through `delete_under_lock`. Its `If-Match` half still awaits the owner's ruling.

**Quote** the "Key leaks" ruling from `owner-ruling-key-leaks-verbatim.md`.

**Residue to record:**
- The flag-off 422 is no longer shown as a shortfall (#688). A juniper-data 400 for a bad param still is. cascor#690 (OPEN, unvalidated) fixes that by keying on "Re-submit with allow_truncation=true", and also makes `_as_bool_stance` parse as juniper-data does.
- Auto-start binds wholesale. Sources: the peer's `cascor686-fixup-implementation-report.md` item 2, and `pending-items-snapshot-2026-09-24T1110Z.md:40`.
- After an inline start that replaces only some partitions, `current_dataset` names the fetch, as the ruling intends; canopy reads only its `.dataset_type`. Record it; no row.
- canopy#683 item 3 is a DISCLOSED behaviour change: a whitespace-only env key makes `/docs` answer 200.
- juniper-canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its retire condition. Record only: retiring an ad-hoc script is the owner's decision.
- cascor#678's stale squash message is already recorded in the register (about L1616); do not re-record it.
- **Canopy items** (canopy behaviour belongs in the canopy E2E ledger, not the register):
  - F-CANOPY-060 (the truncation-permanence sentence), -061 (LOW 3) and -062 (LOW 4) are RESERVED. They are recorded only off `main`: in `…/.claude/worktrees/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`, whose branch `docs/canopy-e2e-handoff-2026-09-24` has no PR.
  - 060's fix is unowned. 061 and 062 are fixed by canopy#685.
  - A fourth item, canopy's two stale copies of #687's "Nothing was loaded…" sentence, has no id yet. It sits in `…/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`.
  - Those files are untracked, in other sessions' worktrees: read only.
- **canopy#685's residue:**
  - frame locals until the release above;
  - owner calls (a), (b) and (c): upstream text still passes through on errors that carry a status; spaces and tabs inside a key are refused; a blank `*_API_KEY_FILE` shadowing an env var now sends no key. Quote the owner's rulings verbatim when the peer sends them;
  - the anonymous rate-limiter 500 needs `rate_limit_enabled`.
- **data428 round 3, `data428-round3-laneA1-security.md`:** F3 is `APD-DATA-056`. F2 (the 8,192-byte cap, parsed under `_version_lock`) and F4 (header limits) are recorded nowhere: file or decline each, with a reason.
- **Cite** the peer's archived reports by filename, and byte-compare each against its agent's transcript. `--check` skips the four headed "turn-ending report": `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`.

## Appendix B: owner decisions, and the later arc items

**Owner decisions to surface:**
- **#437's breaking marker.** Data's `[Unreleased]` carries #437's `equities_seq` 6.0.0, a `dataset_id` change, and the notes renderer computes breaking = NO.
- **APD-ML-008's silent-path remedy:** a variable only the drift step sets.
- **Releases:**
  - juniper-observability and juniper-service-core, then every consumer's locks and floors (Appendix A).
  - The next juniper-data release: 0.16.0 ships the defects #438 fixed, and only the next release carries #438, the fix-forward and X8.
- **canopy#685's calls (a), (b) and (c)** (Appendix A).
- **The live Sentry project may hold this round's test events.** The owner may review or purge them.
- **Two stray canopy branches,** `pr-63` and `pr-683`, both at `4caf9389`: the unsigned local commit of the #685 worktree. They were pushed at 22:55Z with no PR, apparently from VS Code. Do not delete them unasked.
- **MEMORY.md** is 24,929 characters (`wc -m`), about 70 under the HARD ~25,000-character load limit, past which the harness drops the tail. So every new row must be paid for.
  - The owner's target is 20 KB (`feedback_memory_index_target_is_20kb.md`).
  - The peer's split gives the compaction to this lane. Any structural change is the owner's.
- **FYI:** 0.16.0's notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. The containers session owns it.

**The later arc items.** All are ruled, and this lane carries them. D-B is in flight: its rows stay open until the data fix-forward validates. C-A was started and its forks were killed. The rest have not started. The order is §0 of `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`, and the owner decides when to start.
- **juniper-data:**
  - D-B (caching): data#428 and #438 merged; the fix-forward is in flight.
  - D-C, the error surface (`APD-DATA-030/-031/-022`): RFC 9457 from all three sources. Candidate 6(a) belongs here.
  - D-D, lists and pagination (`APD-DATA-026/-027/-028/-008`).
  - D-E, idempotency (`APD-ECO-001`): after D-F.
  - D-F, storage pushdown (`APD-DATA-019`): build it after the data fix-forward merges, which rewrites `save_versioned` and the lock stripes in `storage/base.py` and `storage/local_fs.py`.
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
- The drafts are `data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md` in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/`, on tmpfs.
- The executor updates them. The durable copy is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md`: line 1 is `# <title>` (strip the `# ` for `--title`), then a blank line, then the body.
  - It was copied at 00:27Z, BEFORE the executor's update. Re-copy it once the executor finishes.
  - It ships with the Git status files.
- If neither survives, rebuild the body from the two `data438-fixforward-round1-*` reports and the executor's disposition report.
- The old title's "a storage fault is a 500" is true only of a stored file that leads out of the root (lane A L-1).

**The brief, summarised.** Evidence and file:line are in the two reports; the lanes' probes are on #2089.

MEDIUM:
- **Lane B M-1, with lane A L-2 and lane B L-4.** Nothing on the event loop may wait on `_version_lock` or a stripe.
  - Move `record_access` onto a small dedicated executor. `to_thread` would share the default pool with the routes' store I/O.
  - Log its exceptions by type only.
  - Consider writing the temp files before taking the locks.
  - Pin it with a test.
  - Correct `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/constants.py:45-47` and `juniper_data/storage/local_fs.py:200-202`, and state the size of the cost in `CHANGELOG.md`.

LOW:
- **Lane B L-1:** deletes on a volume that is out of inodes.
  - Add a lock fallback that needs no inode.
  - Remove the legacy `*.meta.json.lock` files.
  - Make the test double fail `mkdir` too.
  - Scope `CHANGELOG.md:93-94` and `docs/REFERENCE.md:1374-1375`.
- **Lane B L-2 / lane A N-4:** open `locks/` once, with `O_DIRECTORY|O_NOFOLLOW`, and open each stripe through `dir_fd`. Add tests with live-target symlinks, and for the containment refusal (MX13, MX14, MX23, MX24).
- **Lane B L-3 / lane A L-1:** scope "a storage fault is a 500" in the title, `CHANGELOG.md:117-118` and `juniper_data/api/routes/datasets.py:546-547`. Mapping unparseable metadata to a 500, and refusing timezone-naive cursors, are optional.
- **Lane B L-5:** add a two-process create test, a late named create, and a late create whose content differs (MX10, MX1, MX9).

NIT:
- lane B N-1 through N-6;
- lane A N-1, N-3, N-5, N-7, N-8 and N-9;
- `juniper_data/api/routes/datasets.py:1282` says `record_access` "fires on every metadata read". It fires on the `GET /{id}` read and the artifact download only;
- the PR body's counts: 16 of the 17 base failures are their own defect, and `[0.16.0]` is 261 lines;
- `[0.16.0]` must stay byte-identical to the `v0.16.0` tag.

Out of scope:
- F8 (the owner's);
- L7 (known issue);
- `juniper_data/api/security.py`, which the peer lane owns.

## Appendix D: the predecessor's items

- **Remaining 1 (validate #438's fix):** overtaken. #438 merged unfixed, so its fixes became the fix-forward.
- **Remaining 2:** done as #2088.
- **Remaining 3:** Appendix A.
- **Remaining 4 (canopy nit):** handed off as F-CANOPY-060, reserved.
- **Remaining 5:** done by #2084.
- **Remaining 6:** #2081 and v0.16.0 are resolved; the rest is Appendix B.
- **In flight 1 (executor `adf9f5dbe46b1b03c`, fixing #438 in place):** it was killed when session `8f86dec2` ended. Its uncommitted work was rescued into the fix-forward branch (Completed).
- **In flight 2 (#2081's CodeQL block):** resolved; #2081 merged at 22:45:08Z.
- **In flight 3 (the peer):** its lane is carried by its own handoff (Remaining 0): validating #690 and canopy#685, the F2–F10 fix-forwards, and the releases.
- **Its traps are carried above:** whole-file uploads, the §2 status line, /tmp inodes, `strict: true`, `gh pr edit`, and the curated re-arm.

## Appendix E: the fork-drift marker plan (Remaining 5)

Measured by the handoff validation (`handoff-2fba4397-round1-laneF-reprobe.md`); re-verify before coding.
- **Pin a PAIR of markers, per the file's own rule** (`tests/test_service_fork_drift.py` about :174-182 and :199-203): `surrogatepass` and `compare_digest(presented,`. Both are present at:
  - service-core `juniper_service_core/security.py:88` and `:91`;
  - canopy `src/security.py:52` and `:137`;
  - data#440 about `:118`;
  - cascor#689 about `:87`.
- **Canopy's `surrogatepass` sits only in `_compare_bytes`** (`src/security.py:42-52`), which `:300` also uses. That marker alone would stay green if the loop at `:137` reverted, which is why the pair matters.
- **Canopy's CSRF compare** (`src/csrf.py:91`, `:97`) is outside the site file.
- **A register id.** The guard needs one, and APD-ECO-013 does not exist until the closes PR files it. Land the guard with or after that PR.
- **Two counts change.** Update the "seven guards" counts in `docs/REFERENCE.md` (about L2977) and in the register (about L1751).
- **Test it before pushing.** Run with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and the siblings checked out at `origin/main`.
- The peer's F3 spy tests (one per copy) are the behavioural pin, and they also kill its F8 mutant (a `break` after `matched = True`).

## Appendix F: documents this session created or changed

- **Merged in #2088:**
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`;
  - `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`;
  - `docs/REFERENCE.md`;
  - `reports/2026-09-24_defect-register-round-42/register-fixforward2-round{1,2}-lane{A-reprobe,B-refute}.md`;
  - in `util/ad-hoc/2026-09-24_`: `register_round42_second_fixforward{,_corrections,_round2}.py`, `register_primer_citation_census.py`, `primer_toy_error_paths_probe.py`, `primer_toy_pin_mutation_check.py`, `archive_round42_reports.py`.
- **On #2089:**
  - `util/ad-hoc/2026-09-24_round42_probes/{README.md, six lane directories}`;
  - `util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py`;
  - `util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py`.
- **Uncommitted:** see Git status.
- **Memory (outside the repo):**
  - `reference_git_trailer_must_be_last_paragraph.md`;
  - `reference_typed_escapes_become_real_characters.md` (new, reached through a link from `reference_backticks_eaten_in_shell_messages.md`);
  - `reference_backticks_eaten_in_shell_messages.md`;
  - `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`;
  - `MEMORY.md`.
