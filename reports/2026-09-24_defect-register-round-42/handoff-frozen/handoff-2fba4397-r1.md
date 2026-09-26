# Handoff: defect-register round 42. The second fix-forward merged as ml#2088, the data fix-forward was refuted before its PR and is being fixed, and the closes PR is owed

**From:** session `2fba4397` ("defect reg"), worktree `.claude/worktrees/fizzy-hugging-dream`. **Date:** 2026-09-24, about 23:40Z.
**Predecessor:** `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (session `8f86dec2`). Every item of it is accounted for in Appendix D.

## Goal (paste this as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem. The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`. The owner's policy: the PR sweeper is theirs and its merges are intended. Validate a pushed branch before opening its PR when a validated merge matters; otherwise validate after merge and fix forward. Merge approval is granted for this arc's PRs. Checks must pass, and other sessions' PRs are not covered.

**Completed:**
- **juniper-ml#2088 MERGED at 23:41:16Z as `5af9d722`.** It is the second register and primer fix-forward, from `ml2080-round1-laneA-reprobe.md` / `-laneB-refute.md`. Its commits were `e2f87aae`, `990ef3f9` and `2439d049`, plus the update-branch merge `1f116c38`.
  - Post-Merge Main Verification and CodeQL passed on `5af9d722`.
  - The symbol screen, run over `c061a99f..5af9d722`, prints `waived (Allow-Symbol-Loss): const:SESSIONS`.
  - It was validated before the PR opened, in two rounds. The reports ship on the branch: `register-fixforward2-round{1,2}-lane{A-reprobe,B-refute}.md`.
  - Round 2's MEDIUM was a regression round 1's own fix introduced. A lone surrogate is valid JSON; the numbers-only `params` rule made the 422 echo it; Starlette's `JSONResponse` renders with `ensure_ascii=False`, so the 422 became a plain-text 500. Every problem body is now `json.dumps` (ASCII) output.
  - The list route had the same class through a stored tag, on `main` too. It now renders through `canonical_json`.
  - `n_samples` is bounded to 1..1,000,000. The toy's own suite pins `true`, `null`, a fraction, a surrogate echo and a 15,000-deep cursor.
  - At the head: harness 62/62; `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` 12/12 caught; `util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py` 27/27 (25 differ on `main`); register tools 136 rows | 100 fixed | 36 open, AGREE.
- **juniper-data#438 merged at 18:52Z, before its fix-in-place landed.** The killed executor's uncommitted work was rescued and finished as signed branch `fix/conditional-requests-round4-followups` @ `d1c66a11` (parent `0f0f7e0e` = #438's merge). No PR yet.
  - It answers every finding in `data438-round1-lane{A-reprobe,B-refute}.md`. F8 (#437's breaking marker) is left to the owner; L5 and L7 are disclosed rather than fixed.
  - Its own validation (next item) found M2(b) and L2 only partly fixed.
  - Its verification: unit 1901, coverage 97.76%, api+integration 118, harness "PASS: 70 mutations", equivalence 3,495,583 inputs / 0 mismatches.
- **The "Key leaks" ruling is extracted verbatim** to `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`: asked 10:22:00.792Z, answered 18:30:09.820Z, "Fix everywhere now (Recommended)". The extractor is `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks`. **Both files are uncommitted in this worktree: ship them in the next juniper-ml PR.**
- **The canopy items are handed off.** F-CANOPY-060, -061 and -062 are reserved by the canopy E2E session (the truncation sentence; LOW 3; LOW 4). A fourth item (canopy's two stale copies of #687's "Nothing was loaded…" sentence) sits in canopy combined's handoff with no id yet (Appendix A).
- **Resolved since the predecessor:**
  - v0.16.0 published to PyPI at 18:35Z;
  - #2081 merged 22:45:08Z (`7e8c7ff9`);
  - ml#2086 merged 20:37:13Z (`c061a99f`);
  - canopy#683 merged 19:10:20Z; canopy#685 merged 23:24:14Z (`dc5ea02e`);
  - cascor#688 merged 18:56:25Z (`7f4a7213`).

- **The data fix-forward was validated before any PR, and REFUTED.** Two lanes ran on `d1c66a11`; their reports are archived in `reports/2026-09-24_defect-register-round-42/`.
  - Lane A (`data438-fixforward-round1-laneA-reprobe.md`): the behaviour claims reproduce, and several text claims do not; 2 LOW, 9 NIT.
  - Lane B (`data438-fixforward-round1-laneB-refute.md`): 1 MEDIUM, 5 LOW, 6 NIT.
  - **The MEDIUM is a regression the branch introduces.** `record_access` runs on the event loop (`call_soon`) and blocks on the process-global `_version_lock`. `save_versioned` now holds that lock for a whole save, unnamed creates included, and every ecosystem client creates unnamed datasets. One 80 MB create froze the service for 6.6 s, against 0.01 s on `main`, past the 5 s readiness probe.

**In flight at handoff (this session's subagents die with it):**
1. **Executor `a46e715a6801b98ca`** is fixing all of both lanes' findings on the data branch.
   - It pushes ONE signed commit with `--expected-head d1c66a11…` and opens no PR.
   - It updates the PR drafts (Appendix C) and ends with a disposition report.
   - The brief, condensed, is in Appendix C. If this session ends first, its uncommitted work stays in the juniper-data worktree (Git status); finish it from there.

**Remaining:**
1. **Validate #2088's one unvalidated delta after merge.** No lane saw `990ef3f9..2439d049`, round 2's corrections. Run two lanes (re-derive; refute), archive their reports and fix forward. The corrections are:
   - the primer toy's ASCII problem bodies;
   - the list route through `canonical_json`;
   - the `n_samples` bound on lines 5658-5659;
   - the suite arms on 6084-6087 and 6117-6120;
   - Appendix E's line 9880 and E.1 item 3 (9943-9944);
   - the register's `GET /{id}` wording, APD-CASCOR-013's writers at `7f4a7213`, the §4 note, the rulings-block ids and APD-DATA-057's park bullet;
   - the tools.
2. **The data fix-forward.**
   - Once the executor's commit is pushed, check it against both reports and its own disposition report. Its fix for the MEDIUM is a concurrency change.
   - Then run round 2 (two lanes, on the delta from `d1c66a11`) BEFORE opening the PR, because the sweeper merges an open PR as soon as it is green.
   - Then open the PR from the drafts (Appendix C), merge, and archive the round-2 reports: add their `MISSING` entries in `util/ad-hoc/2026-09-24_archive_round42_reports.py`, beside the round-1 pair.
   - Send the PR number to the peer lane.
   - data#440 also edits `CHANGELOG.md` `[Unreleased]`. Lane B found the two merge cleanly in either order at `0bee089e`; re-check if either moves.
3. **The closes PR** (juniper-ml, register). Appendix A has the full checklist: gates, rows to close and file, the ruling quote, residue, and the peer's archived report names.
4. **The fork-drift marker is this lane's.** Pin `.encode("utf-8", "surrogatepass")` at the four compare sites (service-core, data, cascor, canopy) in `tests/test_service_fork_drift.py` and `docs/REFERENCE.md`'s drift-gate section. Do it only **after data#440 and cascor#689 merge**; a marker ahead of a site fails the gate on `main`.
5. **Verify, then file, two candidates** (neither is verified yet):
   - (a) Any FastAPI service without its own `RequestValidationError` handler answers a lone-surrogate echo with a 500, because FastAPI's default 422 is a `JSONResponse`. Primer line 4742 says juniper-data registers none. This is input to D-C.
   - (b) The primer's `idempotent_jobs.py` example echoes client strings through `JSONResponse` (around primer line 2687).
6. **PATCH #2080's body** (`gh api -X PATCH`). Its rejection of the APD-ML-008 nit was wrong (ml2080 lane A N6); #2088 applies the nit as H2.
7. **Owner decisions to surface** (Appendix B has C-A…D-G):
   - #437's breaking marker;
   - APD-ML-008's silent-path remedy;
   - the observability and service-core releases that the key-leaks fixes need;
   - MEMORY.md at 25.2 KB against the 20 KB target;
   - sequencing C-A…D-G, and APD-DATA-047's ceiling;
   - FYI: 0.16.0's notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. The containers session owns it.

**Key context and traps:**
- **A subagent dies with its session, and its transcript MOVES.** Find transcripts by session id: `util/ad-hoc/2026-09-24_archive_round42_reports.py`'s `subagents_dir()`. A session limit also kills subagents; resume them with SendMessage, same session only.
- **GitHub's squash appends its own `Co-authored-by` paragraph** after the commit messages (`---------`, then a blank line, then the line). So `git log --format='%(trailers:key=Allow-Symbol-Loss)'` prints NOTHING for `5af9d722`, although the waiver is there. Check with `grep -c`, or run the symbol screen over the merge's range; the screen scans lines, not the trailer block.
- **A signed push can create nothing.** The first `push_signed_commit.py` run for `2439d049` printed its plan and made no commit. Check the ref with `gh api …/git/ref/heads/<branch>`; re-running with the same `--expected-head` is safe.
- **The primer is cited by bare line number.** Edit in place only; the three editors refuse any line move.
- **The census counts every bare number past 5758 in the register.** A new mention of `6592` made it read 70; name a retired anchor without its number.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage (a backslash-u escape of U+2028, or of a surrogate pair). Build such text with `chr()` and check the file with `od -c`.
- **`strict: true`:** after every move on main, run `update-branch` with `expected_head_sha`. `gh pr edit` is broken; use `gh api -X PATCH`.
- **The worktree-isolation guard refuses complex shell.** Split commands, or write a script under `util/ad-hoc/`.

## Verification commands (run from the worktree)
```
gh pr view 2088 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit
git fetch origin && python3 util/ad-hoc/register_open_set.py | grep 'rows |'    # 136 rows | 100 fixed | 36 open (until the closes PR)
python3 util/ad-hoc/register_status_crosscheck.py | tail -1                     # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c 'OK    '   # 36, the two data round-1 reports included
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # d1c66a11… unless corrected
gh pr list --repo pcalnon/juniper-data --state open; gh pr list --repo pcalnon/juniper-cascor --state open
```

## Git status
- **Branch:** `worktree-fizzy-hugging-dream`, with three unsigned LOCAL scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`) that exist only so the CI screens could run. **Never push them.** Their content is #2088's.
- **Uncommitted:** `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M) and `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md` (??). Both are for the next PR.
- **juniper-data worktree:** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2` holds the branch at `d1c66a11`.

## Appendix A: the closes PR

**Gates** (close a row only after its PR merges AND its own validation holds):
- `APD-CASCOR-008` / `-013`: cascor#688 merged; its validation asked for cascor#690 (OPEN, head `78e99414`, not yet validated). The peer lane owns #690's validation.
- `APD-DATA-017` / `-029` / `-032` / `-057`: data#438 merged; its fix-forward (Remaining 2) must merge and validate.

**File** (ruled, fixes shipped or in flight, so not parked):
- `APD-ECO-013` (S). A non-ASCII `X-API-Key` makes the str `compare_digest` raise; the 500 goes to Sentry, and Sentry's local-variable capture records the real key. Its fixes:
  - ml#2086 (merged; service-core and observability);
  - canopy#685 (merged);
  - data#440 and cascor#689 (open).
  - The frame-locals half stays live in shipped builds until juniper-observability is released and canopy's `==0.4.0` lock moves.
  - **It stays open until the peer's F2 and F3 are fixed.**
    - F2, ml#2086: no `before_send_transaction`, so with `send_pii=True` a sampled transaction carries the raw `x-api-key`.
    - F3: no CI test checks that `compare_digest` is used at all.
    - Source: `bytes-compare-ml2086-data440-cascor689-validation.md`.
- `APD-ECO-014` (S). canopy's padded outbound keys leaked into logs, into Sentry and into a 409 body. Fixed by canopy#685.
- `APD-CASCOR-014` (S), the peer's F4, confirmed by measurement.
  - cascor tests that `import main` start the REAL Sentry SDK whenever a DSN is exported: traces 1.0, profiling 1.0, logs on.
  - With a local sink, 9 files sent 25 envelopes.
  - Cause: the import at `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` runs `src/main.py:231`.
  - Fix: in `src/tests/conftest.py`, after line 37, set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN` and `SENTRY_DSN` to `""`. Set them empty rather than deleting them: `load_dotenv` does not override an existing value.
  - cascor#689's `include_local_variables=False` removes the locals, not the events.

**Quote** the "Key leaks" ruling from `owner-ruling-key-leaks-verbatim.md`.

**Residue** to record:
- #688's 422 is resolved with 400s by #690, which also fixes `_as_bool_stance`.
- Auto-start binds wholesale.
- #678's squash message is stale.
- #678's mutation script `2026-09-23_blank_api_key_warning_mutation_check.py` has met its retire condition.
- F-CANOPY-060/061/062 and the fourth canopy item (061 and 062 are fixed by canopy#685).
- canopy#685's own residue:
  - frame locals until the observability release;
  - upstream text still passes through on errors that carry a status (the owner's call);
  - a blank `*_API_KEY_FILE` now sends no key;
  - spaces and tabs inside a key are refused;
  - the anonymous rate-limiter 500 is reachable only with `rate_limit_enabled`.

**Cite** the peer's archived reports by filename, once its handoff PR lands.

## Appendix B: the later arc items (defined in `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` §0)

All are ruled, and none is started. They need the owner's go-ahead on sequencing.

**juniper-data:**
- D-B (caching) is done by data#428, #438 and the fix-forward.
- D-C, the error surface: `APD-DATA-030/-031/-022`, RFC 9457 from all three sources. Candidate 5(a) belongs here.
- D-D, lists and pagination: `APD-DATA-026/-027/-028/-008`.
- D-E, idempotency: `APD-ECO-001`, after D-F.
- D-F, storage pushdown: `APD-DATA-019`. It collides with data#428 on `storage/base.py`, so rebuild it on post-#438 code.
- D-G: `APD-DATA-048/-049/-051`, plus `APD-DATA-047`, the 1e11 ceiling, which is an owner decision.
- D-B…D-D share `routes/datasets.py`; sequence them.

**The clients:**
- C-A, a per-call timeout: `APD-ECO-003`. Relaunch it fresh; the killed forks cannot be resumed.
- C-B, TypedDict response shapes: `APD-ECO-004`.
- C-C, the recurrence client using its server's models: `APD-RCLIENT-004`.
- C-A and C-B collide on 38 `def` lines; run them in sequence.

## Appendix C: the data fix-forward, what the executor was asked to fix, and its PR text

**PR text.** The drafts are `data_fixforward_pr_title.txt` and `data_fixforward_pr_body.md`, in this session's scratchpad: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/`. That directory is on tmpfs, so this session copies the final drafts to `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md` before it ends.
- The title's "a storage fault is a 500" is one of lane A's L-1 wording findings. It is true only of a stored file that leads out of the storage root.

**The brief, condensed.** Evidence, file:line and probe scripts are in the two round-1 reports.

MEDIUM:
- Lane B M-1, with lane A L-2 and lane B L-4. Nothing on the event loop may wait on `_version_lock` or a stripe.
  - Move `record_access` off the loop onto a small dedicated executor: `to_thread` would share the default pool with the routes' store I/O.
  - Log its exceptions by type only.
  - Consider shrinking `save_versioned`'s locked section: write the temp files first; re-check and rename under the locks.
  - Pin it with a test: a read stays fast while another thread holds the lock.
  - Correct the stall and stripe-cost texts (`REFERENCE.md:1357-1362`, `constants.py:45-47`, `local_fs.py:200-202`).

LOW:
- Lane B L-1: deletes on a volume out of inodes before `locks/` exists.
  - Add a lock fallback that needs no inode (`flock` on the storage root's directory descriptor).
  - Remove the legacy `*.meta.json.lock` files.
  - Make the test double also fail `mkdir`.
- Lane B L-2 / lane A N-4: open `locks/` once with `O_DIRECTORY|O_NOFOLLOW`, and open each stripe through `dir_fd`.
- Lane B L-3 / lane A L-1: scope "a storage fault is a 500". A corrupt metadata file is still the caller's 400.
  - Mapping it to 500 is optional.
  - So is refusing timezone-naive cursors, a pre-existing TypeError 500.
- Lane B L-5: two-process create, late named create and differing-content tests. MX10, MX1 and MX9 survive every suite today.

NIT:
- Lane B N-1: a transient metadata error drops an access record.
- Lane B N-2 / lane A N-1: batch-create is a second exception to "500 everywhere".
- Lane B N-3: stripe creation stops at the first bad entry.
- Lane B N-4: a regular file at `locks/` gives a healthy service whose every write fails.
- Lane A N-3, N-5, N-7, N-8 and N-9.
- The `datasets.py:1282` comment says `record_access` "fires on every metadata read". It fires on the `GET /{id}` read and the artifact download only.
- The PR body's counts: 16 of the 17 base failures are their own defect, and `[0.16.0]` is 261 lines.

Out of scope:
- F8 (the owner's ruling);
- L7 (a known issue);
- data428 round-3 A1 F2-F4;
- `juniper_data/api/security.py`, which the peer lane owns.

## Appendix D: the predecessor's items

- **Remaining 1 (validate #438's fix):** overtaken. #438 merged unfixed, so its fixes became the fix-forward (Remaining 2).
- **Remaining 2 (second fix-forward):** done as #2088.
- **Remaining 3 (closes PR):** Appendix A.
- **Remaining 4 (canopy nit):** done (F-CANOPY-060).
- **Remaining 5 (untracked reports):** done by #2084.
- **Remaining 6 (owner decisions):** #2081 and v0.16.0 are resolved; the rest carry forward as Remaining 7.
- **In flight 3 (peer):** its PRs are ml#2086, canopy#685, data#440, cascor#689 and cascor#688/#690; its own handoff carries its lane.
