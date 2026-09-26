<!-- Archived verbatim 2026-09-24 from subagent ac06b2699a8d933a3 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS. The HIGH finding and the first five MEDIUM findings (H1, M1–M5) must be fixed before this snapshot is archived or used as a first prompt.

The factual core reproduces from primary sources: every PR state, merge time and merge SHA, all commit parentage, the counts, the lane-report attributions, and the ruling timestamps. The failures are omissions and one stale "open decision", not wrong SHAs.

**Documents** (abbreviations used below):
- **SNAP**: `handoff_session_r1_frozen.md` (sha256 `1e5db1832f6131a8…`, frozen at 23:50:22Z).
- **REG**: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
- **PRIMER**: `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`.
- **PRED** (predecessor handoff): `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.
- **PEER** (peer's draft, worktree `happy-skipping-hollerith`, uncommitted, sha256 prefix `ffd111ef` as read): `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`.
- **H0915**: `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`.
- **H0923**: `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`.
- **Transcript**: `2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl`. **Peer transcript**: `bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl`.
- Reports are in `reports/2026-09-24_defect-register-round-42/`: **LA** = `data438-fixforward-round1-laneA-reprobe.md`, **LB** = `data438-fixforward-round1-laneB-refute.md`.

## Claims table

| SNAP line: claim | What I ran or read | Result |
|---|---|---|
| 11: #2088 merged 23:41:16Z as `5af9d722`; commits `e2f87aae`, `990ef3f9`, `2439d049` plus `1f116c38` | `gh pr view 2088` (merge `5af9d722`, head `1f116c38`, 4 commits); `git log`: `2439d049`^=`990ef3f9`, `990ef3f9`^=`e2f87aae`, `1f116c38` = merge of `2439d049` and `7e8c7ff9` | REPRODUCED |
| 12: Post-Merge Main Verification and CodeQL passed | `actions/runs?head_sha=5af9d722`: both success (23:42:18Z, 23:44:33Z) | REPRODUCED |
| 13: screen over `c061a99f..5af9d722` prints the waiver | ran `cli_symbol_loss_check`: `waived (Allow-Symbol-Loss): const:SESSIONS`, fail=0 | REPRODUCED |
| 14: four round-1/2 reports ship | `git diff --name-status c061a99f 5af9d722 -- reports/`: 4 added | REPRODUCED |
| 15–16: round 2's MEDIUM (surrogate / `ensure_ascii=False`); list route also broken on `main` | `register-fixforward2-round2-laneB-refute.md:36` (M1); Starlette `responses.py:194`; Python repro; probe shows the list 500 on the pre-#2088 primer | REPRODUCED |
| 17, 47–49: `n_samples` 5658-5659; suite arms 6084-6087, 6117-6120; 9880; 9943-9944 | PRIMER read at `5af9d722` | REPRODUCED |
| 18: harness 62/62, mutation 12/12, probe 27/27 (25 differ on `main`), 136/100/36 AGREE | ran the mutation check (12/12 caught, control passes, 62 tests per run); ran the probe (27/27 at `5af9d722`); `main` differs on 25/27 under CPython 3.13.13 but 24/27 under 3.14.2t; ran the register tools | REPRODUCED (N2) |
| 19: `d1c66a11` signed, parent `0f0f7e0e` = #438's merge, no PR | `gh api commits/d1c66a11` (verified, reason valid, 1 parent); `gh pr view 438`; `gh pr list --head` returns empty | REPRODUCED |
| 20–21: answers every finding; F8 to owner; L5/L7 disclosed; M2(b) and L2 only partly fixed | `d1c66a11` commit message; LA disposition section; LB verdict item 3, L-1, L-2 | REPRODUCED |
| 22: unit 1901, coverage 97.76%, api+integration 118, "PASS: 70 mutations", 3,495,583 inputs / 0 mismatches | LA rows 32–38 reproduce them; not re-run (brief forbids whole-tree extraction) | PARTLY |
| 23: ruling asked 10:22:00.792Z, answered 18:30:09.820Z, "Fix everywhere now (Recommended)" | parsed the peer transcript's AskUserQuestion call and its tool_result | REPRODUCED (file list: M2) |
| 24: F-CANOPY-060/061/062 reserved; fourth item in canopy combined's handoff | canopy e2e message 19:40:28.837Z (arrived as a queue-operation); canopy combined 20:45:53.691Z | REPRODUCED |
| 26–30: v0.16.0 PyPI 18:35Z; #2081 22:45:08Z; #2086 20:37:13Z; canopy#683 19:10:20Z; canopy#685 23:24:14Z; cascor#688 18:56:25Z | `gh pr view` for each; PyPI upload 18:35:40Z | REPRODUCED (canopy#685 unvalidated: M3) |
| 33–34: lane A 2 LOW / 9 NIT; lane B 1 MEDIUM / 5 LOW / 6 NIT | read LA and LB | REPRODUCED |
| 35: `call_soon`, process-global lock, whole-save lock including unnamed creates; every client creates unnamed; 6.6 s vs 0.01 s | at `d1c66a11`: `base.py:137`, `:350`, `:578-585`; `datasets.py:1009/1123/1157/1165`. Production creates: cascor `manager.py:4873` and `data_provider.py:189`; canopy `demo_mode.py:1112` and `:2033`; recurrence `data.py:46`. All unnamed; only tests pass `name=`; no production `batch_create` callers. Timings from LB | REPRODUCED (timings not re-measured; N5) |
| 38–41: executor `a46e715a6801b98ca` brief | transcript: Agent launch 19:37:50Z; SendMessage 23:48:49Z | REPRODUCED |
| 44: no lane saw `990ef3f9..2439d049` | transcript Agent launches: only `e2f87aae` and `990ef3f9` lanes | REPRODUCED |
| 45–51: the list of round-2 corrections | diff: 24 primer lines and 6 register lines changed in place | PARTLY (L3) |
| 57: #440 and the fix-forward merge cleanly in either order | LB `:242`; legacy `git merge-tree 0f0f7e0e d1c66a11 0bee089e`: 0 conflict markers | REPRODUCED |
| 59: a marker ahead of a site fails the gate on `main` | `tests/test_service_fork_drift.py`; `ci.yml:500` vs `docs-full-check.yml:259` (cron Monday 06:00 UTC plus dispatch); `docs/REFERENCE.md:2975`; marker greps at all four sites | REPRODUCED (caveats: L4) |
| 61: candidate (a); "primer 4742 says data registers none" | the primer says so, but data `main` `app.py:187-212` has a handler since `f6791d6` (#281); in-process probe | PARTLY (M7) |
| 62: candidate (b) at primer ~2687 | PRIMER `2462`, `2479`, `2684-2687` | REPRODUCED (code read) |
| 63: #2080's rejection was wrong (N6); #2088 applies it as H2 | #2080 body `:69` (unchanged since 10:18:16Z); `ml2080-round1-laneA-reprobe.md:156`; #2088 body `:67` | REPRODUCED |
| 65–70: owner decisions | #437: data `[Unreleased]` still has no BREAKING. APD-ML-008: REG `:1629` awaiting ruling. PyPI: observability 0.4.0, service-core 0.7.0. MEMORY.md now 25,125 B (modified 23:53Z, after the freeze). 403: job log "Resource not accessible by personal access token"; containers ownership per `…wave-4-waits-on-the-token.md:71-76`. **APD-DATA-047 is already ruled** | mostly REPRODUCED; APD-DATA-047 REFUTED (M1) |
| 74–76: squash-trailer trap; empty signed push; editors refuse line moves | trailer lookup prints empty; body ends `---------`, blank, `Co-authored-by`; `grep -c` = 3. Transcript: ref still `990ef3f9` at 23:31:09Z after the first run. Editors' length checks | REPRODUCED |
| 84–89: verification commands | ran as written: 136/100/36; AGREE; 36 OK (only with the uncommitted archiver change); ref `d1c66a11`; open #440, #689, #690 | REPRODUCED |
| 94: Git status | `git status --short` shows 6 paths | REFUTED (M2) |
| 100–101: gates | `gh pr view 690` (open, `78e99414`); REG `:1636-1637` | REPRODUCED (ECO-014 gate missing: M3) |
| 104–119: ECO-013 / ECO-014 / CASCOR-014, peer F2/F3/F4 | peer message 20:35:57Z; cascor `main` `test_cfg_03…py:25`, `main.py:231-242`, `conftest.py:37`; the three ids are unused in REG; the peer report file exists | REPRODUCED (M3, M4, L1) |
| 123–134: residue | peer messages 19:06:26Z, 19:24:36Z, 20:18:49Z, 21:10:27Z; canopy#685 body; `cascor678-postmerge-validation.md:56` | PARTLY (L2, N1, N3) |
| 138–155: Appendix B | H0915 §0 and §0.6; H0923 `:82`; open set | PARTLY (M1, L6) |
| 164–196: Appendix C versus the brief | SendMessage 23:48:49Z; LA; LB; `d1c66a11` `REFERENCE.md:1357-1362`, `constants.py:45-47`, `local_fs.py:200-202`, `datasets.py:1282` | REPRODUCED |
| 198–206: Appendix D | PRED `:21-36`; #2084 (`22a6b7b5`) added the four reports | PARTLY (H1, N7) |

## Findings

### HIGH

**H1. The owner's pending consolidation order, the peer's location and the promised routing are all missing, and the omission creates a circular deferral.**

Quoted: SNAP 56 "Send the PR number to the peer lane." and SNAP 206 "its own handoff carries its lane." A search of SNAP for `happy-skipping|follow-up-lane|consolidat|042116|24f8d8` finds nothing.

Evidence:
- The owner, typed at 23:25:49.935Z in the transcript: "let's consolidate the following three, related handoff prompts: this session's handoff prompt; PRED; PEER … ensuring that no tasks or necessary context are lost".
- This session to the peer at 20:36:26Z: "your successor should message "defect reg [24f8d8]", or … whichever session my handoff names".
- This session to the peer at 23:34:29Z: "the owner has asked THIS session to consolidate".
- PEER `:9`: a newer register-lane handoff on `main` "governs". PEER `:18`: two sessions are named "defect reg".
- PRED `:30` said to re-route the peer by session name.
- PEER has no PR yet.
- Result: the peer lane's gating work (#690 and canopy#685 validation, F2/F3) is carried only by a document SNAP never names, and that document defers back to the register lane.

Replacement:
- Insert before line 37: "**Owner instruction pending (23:25:49Z): after this handoff is validated, consolidate three handoffs into one, validated by consensus, losing no task or context: (1) this file; (2) PRED (on `main` via #2084); (3) PEER, uncommitted in worktree `.claude/worktrees/happy-skipping-hollerith` (session `bc31e993`, "defect reg [042116]"), awaiting its own validation and PR. Consolidate its committed version. If this session ended first, this is your first task.**"
- Line 56: "Send the PR number to the peer. Two sessions are named "defect reg": the peer is `[042116]` (`bc31e993`) and this session is `[24f8d8]` (`2fba4397`). First message the peer, or its successor found with ListAgents, with your own session name so its updates re-route to you."
- Line 206: "…its lane (validate #690 and canopy#685, the F2–F10 fix-forwards, the observability and service-core releases) is carried by PEER (path above, no PR yet)."

### MEDIUM

**M1. APD-DATA-047 is already ruled and closed.**
- Quoted: SNAP 69 "and APD-DATA-047's ceiling"; SNAP 148 "plus `APD-DATA-047`, the 1e11 ceiling, which is an owner decision."
- Evidence: REG `:1284` "FIXED (RATIFIED by the owner, 2026-09-21 — the ceiling STAYS, at `1e11`…)", and `:1421`, `:1661`. It is absent from `register_open_set.py`'s open list. H0915 `:278` "Owner decisions still owed — NONE, as of 2026-09-21" and `:701`. H0923 `:82` lists D-G as "(048/049/051)".
- Replacement:
  - Line 69: "- sequencing C-A…D-G;"
  - Line 148: "- D-G: `APD-DATA-048/-049/-051`. (`APD-DATA-047` was RATIFIED at `1e11` on 2026-09-21 and is closed.)"

**M2. The Git status omits four of the six uncommitted paths.**
- Quoted: SNAP 94 names two paths ("Both are for the next PR"); SNAP 23 says "Both files are uncommitted".
- Evidence: `git status --short` also shows:
  - ` M util/ad-hoc/2026-09-24_archive_round42_reports.py` (adds the MISSING entries `a6afb722d69732ae5` and `a641405b9532742e6`);
  - `?? reports/…/data438-fixforward-round1-laneA-reprobe.md`;
  - `?? …-laneB-refute.md`;
  - `?? prompts/…/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
  - The "36 OK" in SNAP 87 depends on the uncommitted archiver change.
- Replacement for line 94: "**Uncommitted, six paths, all for the next juniper-ml PR:** the archiver (M: the data round-1 MISSING entries), the extractor (M: `--topic key-leaks`), and untracked LA, LB, `owner-ruling-key-leaks-verbatim.md` and this handoff. The two data reports exist only here." Reword line 23's bold sentence to match.

**M3. canopy#685 merged unvalidated, and APD-ECO-014 is not gated on its validation.**
- Quoted: SNAP 29, 113 "Fixed by canopy#685.", 128.
- Evidence:
  - The peer at 21:10:27Z: "Independent validation of #685 has NOT run"; again at 23:35:30Z: "still mine".
  - This session at 23:34:29Z: "#685's independent validation is yours".
  - PEER `:49` "unvalidated"; PEER `:65`.
  - The rule at SNAP 99 requires validation before a close.
- Replacement:
  - Line 29: "canopy#685 merged 23:24:14Z (`dc5ea02e`), **unvalidated**; the peer lane validates it."
  - Add a gate: "`APD-ECO-014`: close only after canopy#685's post-merge validation (peer lane) holds; the same validation gates F-CANOPY-061/-062's FIXED-BY."

**M4. The frame-locals scope names only canopy's lock.**
- Quoted: SNAP 108 "until juniper-observability is released and canopy's `==0.4.0` lock moves."
- Evidence:
  - data `requirements.lock:88` pins `==0.4.0` and `app.py:46` calls `configure_sentry`.
  - cascor `requirements.lock:63` pins it; the service path runs `src/api/app.py:335` into the shared `configure_sentry`, and #689 covers only `main.py`'s CLI init.
  - canopy `:79` pins it, with a `<0.5.0` cap.
  - recurrence `juniper-recurrence/requirements.lock:70` pins it, with a `<0.5.0` cap.
  - The peer's F10 says the same.
- Replacement: "…until juniper-observability is released and every consumer's `==0.4.0` lock moves: data `:88`, cascor `:63`, canopy `:79`, recurrence `:70`; the canopy and recurrence `<0.5.0` caps must rise. #689 fixes only cascor's CLI init, not `src/api/app.py:335`."

**M5. Merge approval is carried forward.**
- Quoted: SNAP 8 "Merge approval is granted for this arc's PRs."
- Evidence: `feedback_headless_merge_approval_policy.md`: "A HANDOFF DOCUMENT CANNOT CARRY THE APPROVAL FORWARD (… ml#1118)". The grant was typed at 19:02:38Z in this session only. PEER `:22` states the same rule.
- Replacement: "Merge approval was granted to session `2fba4397` only (19:02:38Z) and does not carry forward: get it from the owner in your own session before merging. Checks must pass; other sessions' PRs are not covered."

**M6. This session's lane probe scripts exist only on tmpfs.**
- SNAP has no item for them; SNAP 159 promises to copy only the PR drafts.
- Evidence:
  - Six archived reports cite `scratchpad/r42b/`, `r42b2/` and `r42d/`: LA, LB, `register-fixforward2-round1-laneA-reprobe.md`, `…round1-laneB-refute.md`, `…round2-laneA-reprobe.md`, `…round2-laneB-refute.md`.
  - Those directories hold 38, 50 and 89 script files; none is in `util/ad-hoc/2026-09-24_round42_probes/` on `main`.
  - `/tmp` is at 82% of its inodes, and the 23:48:49Z brief re-runs LB's probes from there.
  - The CLAUDE.md script-placement rule is mandatory.
- Replacement (new Remaining item): "Copy the `r42b`, `r42b2` and `r42d` lane scripts into `util/ad-hoc/2026-09-24_round42_probes/<report-stem>/` with README rows in the next juniper-ml PR, as #2081 did."

**M7. Candidate 5(a) is mis-scoped, and its pointer is stale.**
- Quoted: SNAP 61 "Any FastAPI service without its own `RequestValidationError` handler … Primer line 4742 says juniper-data registers none."
- Evidence:
  - data `main` `app.py:187-212` has had a handler since `f6791d6` (#281, 2026-08-23), described as "byte-identical to FastAPI's built-in handler": `JSONResponse(... jsonable_encoder(exc.errors()))`.
  - My probe (FastAPI 0.137.0, Python 3.13.13) sent `{"n":"\ud800"}` against `n: int`. Both FastAPI's default handler and a data-style copy answered 500 `text/plain`; the control answered 422 JSON.
  - cascor has its own handler at `src/api/app.py:856`.
  - A related row already exists: REG `:1303` APD-DATA-056.
- Replacement: "(a) A 422 that echoes the rejected input through Starlette's `JSONResponse` is a plain-text 500 for a lone surrogate. That includes FastAPI's default handler and juniper-data's byte-identical one (`app.py:187-212`); a probe gave 500 for both. Primer 4742 has been stale since #281. Check cascor's `:856` separately and cross-reference `APD-DATA-056`."
- Add to (b): "`store.complete` (2686) stores the payload before rendering it, so every replay of that key (2662) fails the same way."

### LOW

- **L1.** SNAP 104-112 omit the ECO-013 residue this session promised the peer at 20:36:26Z ("F5-F10 go on the row as known residue"). Add: "F5–F10 go on the row unless fixed first. F5 as corrected at 23:35:30Z: add the surrogate PAIR `chr(0xD83D)+chr(0xDD11)`, not U+1F511. F6 and F7 are LOW; F8 is killed by F3; F9 and F10 are NITs; F1 was fixed by canopy#685 (unvalidated)."
- **L2.** The residue list (SNAP 123-134) omits the peer's 19:06:26Z item. Add: "- After an inline start that replaces only some partitions, `current_dataset` names the fetch (intended per the ruling; canopy reads only `.dataset_type`)."
- **L3.** The inventory at SNAP 45-51 is incomplete. The delta changes 24 primer lines; the list omits 4199, 5330, 5378, 5600 and 6091. Add: "- primer 4199 (`record_access` scope), 5330 and 6091 (the "every error" scoping), 5378 (the toy docstring), 5600 (the `decode_cursor` comment); full set via `git diff 990ef3f9 2439d049`."
- **L4.** SNAP 59's marker plan needs five caveats:
  - canopy's literal sits only in `_compare_bytes` (`src/security.py:52`), which `:300` also uses, so it stays green if the loop at `:137` reverts;
  - canopy's CSRF compare (`src/csrf.py:91`, `:97`) is outside the site file;
  - the test file's own rule is paired markers (`:174-182`, `:199-203`), and APD-ML-008 (REG `:1305`) is exactly this weakness;
  - PR CI runs only `SharedPackageGuardTest` (`ci.yml:500`; `docs/REFERENCE.md:2975`), so a premature marker merges green and fails the next Monday `docs-full-check` run;
  - the guard needs a register id, and APD-ECO-013 is not filed yet; the "seven guards" counts at `docs/REFERENCE.md:2977` and REG `:1751` must change.

  Replacement: "Pin the pair (`surrogatepass`, `compare_digest(presented,`), which is present at service-core `:91`, canopy `:137`, data#440 `:118` and cascor#689 `:87`. Cite APD-ECO-013, landing with or after the closes PR. Update both counts. Before pushing, run with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` and siblings at `origin/main` (11 OK today). F3's spy tests are the behavioural pin."
- **L5.** Appendix A should update APD-DATA-055 without closing it. On data `0f0f7e0e`, `batch_delete` (`base.py:657`) and `delete_expired` (`:484`) now go through `delete_under_lock` (`:415`). Add: "Update APD-DATA-055: #438 fixed its lock half; the `If-Match` half awaits the ruling."
- **L6.** SNAP 140 "none is started" contradicts SNAP 143 (D-B "done") and C-A's killed forks (H0923 `:82`). D-B's rows are open and gated, and `d1c66a11` also rewrites `storage/base.py` and `local_fs.py`. Replacement: "All are ruled. D-B is in flight (rows open until the data fix-forward validates); C-A was started and its forks were killed; the rest are not started." Also: "D-F rebuilds on the code after the data fix-forward merges."

### NIT

- **N1.** SNAP 126-127: the two "#678"s are different PRs. The stale squash message is cascor#678's (`cascor678-postmerge-validation.md:56`); the mutation script is canopy#678's, at juniper-canopy `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py`. Qualify both.
- **N2.** SNAP 18: "25 differ on `main`" holds under CPython 3.13.13 only; under 3.14.2 it is 24, because `main` already answers the deep cursor with a 400. Say so.
- **N3.** SNAP 124 is garbled. Replacement: "#688 fixed the ordinary-422 misread; the 400s it still misread are fixed by #690 (open, unvalidated), which also fixes `_as_bool_stance`."
- **N4.** SNAP 3 "about 23:40Z": the content runs to 23:48:49Z and the file was frozen at 23:50:22Z.
- **N5.** SNAP 35 "past the 5 s readiness probe": one probe fails, but `values.yaml:86-91` needs three in a row (`failureThreshold 3`).
- **N6.** The Goal runs about 1,328 words against the ~1,200 target.
- **N7.** SNAP 4 "Every item … accounted for": PRED's In-flight 1 and 2 have no Appendix D row (they are covered at SNAP 19 and 27), and In-flight 3's re-route instruction is dropped (H1).

## What I could not verify

- SNAP 22's suite numbers and SNAP 35's timings. I did not re-run them, because the brief forbids whole-tree extraction; LA rows 32–38 and LB's table report them.
- SNAP 77's "reads 70" (the census reads 69 today) and SNAP 78's typed-escape trap (asserted by the peer at 23:35:30Z).
- Candidate (b) is code-read only; I did not execute it. I did not check cascor's `:856` handler for the surrogate echo.
- MEMORY.md's size at freeze time: it was modified after the freeze.

## Side effects and scratch

- I ran `git fetch` in eight sibling checkouts.
- A fetch into `refs/remotes/origin/pr440-laneF` in juniper-data was removed with `git update-ref -d` (0 remaining).
- No repository file was edited.
- I kept 12 small helper scripts in `…/scratchpad/hv1/laneF/`: `lines.py`, `grepf.py`, `tgrep.py`, `twindow.py`, `xsession.py`, `xsession2.py`, `usertyped.py`, `agents.py`, `ruling_check.py`, `changed_lines.py`, `show_pairs.py`, `surrogate_422_probe.py`. All extracted copies are deleted. Preserve or delete the scripts as you see fit.

**Changed:** no repository files, and no report or notes files created.
