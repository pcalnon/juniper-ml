<!-- Archived verbatim 2026-09-24 from subagent aac2e54444043de31 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS. No HIGH or MEDIUM finding. The round-2 changes hold up against primary sources, including the new sweeper-merge bullet, Appendix J and the opener, whose `--dry-run` exited 0 with the stated 22 files. There are 7 LOW and 9 NIT findings. The most important LOW: the document misdescribes one of the opener's refusals, and it names "containers [2703c8]" as live and as the owner of the 403 when that session had already handed off in juniper-ml#2100. Two things have moved since 02:10Z.

All "L<n>" references are to the frozen snapshot `hc2/consolidated_r2_frozen.md` (sha256 `79c0abb4b7dbdf15…`, checked; byte-identical to the untracked file in `fizzy-hugging-dream`). Other documents are named in full:
- **document 1:** `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md` (= `hc2/doc1_r2_frozen.md`, sha256 `17ef7db5…`)
- **document 2:** `hc2/doc2_peer_final_2e4917c2.md`
- **document 3:** `hc2/doc3_predecessor_main.md`
- **the round-1 reports:** `handoff-consolidated-round1-lane{F-reprobe,O-amputation,P-fresh-session}.md`
- **the fix report:** `data438-fixforward-round1-fix-report.md`
- **the round-3 reprobe:** `handoff-2fba4397-round3-laneF-reprobe.md`
- **the register:** `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`

I checked between 02:10Z and 02:31Z. Every test ran with the six DSN variables set to "". I printed no environment values: only whether `SENTRY_SDK_DSN` is exported, and the length of `git config user.email`. I started nothing on 8100, 8201 or 8050, and ran no `git fetch`.

## Findings

### HIGH
None.

### MEDIUM
None.

### LOW

**L-1. The opener does not refuse "a file that `origin/main` already holds".**
- **Quoted (L186):** "refuses a missing file, a stale base (the worktree is behind `origin/main`, 7 commits at 02:07Z; a file that `origin/main` already holds is refused)".
- **Evidence:**
  - `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py:91-94` refuses only when `rev-parse origin/main:<f>` exists AND differs from `rev-parse HEAD:<f>`.
  - Two files in the ship set are tracked and are on `origin/main`, with HEAD's blob equal to main's: the archiver (`2eba3703`) and the extractor (`db916f9b`). Both pass the check, and the dry run uploads them from the worktree (22 files, exit 0, "(nothing written)").
  - The check reads the LOCAL `origin/main` ref. The script's docstring says "run `git fetch` first"; L186 does not.
- **Corrected text:** "…a stale base: any file whose `HEAD` copy differs from `origin/main`'s. For an untracked file, that means any path `origin/main` already holds. The two tracked files (the archiver and the extractor) upload unless `main` has changed them. It compares against your LOCAL `origin/main`, so `git fetch` first. (The worktree is behind `origin/main`: 7 commits at 02:07Z.)"

**L-2. The verification annotations say BLOCKED, but `mergeStateStatus` printed BEHIND at writing.**
- **Quoted:**
  - L154: "# Lane F's evidence; OPEN, BLOCKED (CodeQL) at writing"
  - L156: "# OPEN, BLOCKED (CodeQL) at writing"
  - L66: "both BLOCKED by CodeQL".
- **Evidence:**
  - juniper-ml `main` moved at 01:47:48Z (#2098) and 02:02:04Z (#2090). Both GraphQL and `gh pr view` return `"mergeStateStatus":"BEHIND"` for #2089 and #2097 (02:13Z and 02:27Z; one transient UNKNOWN between them), with CodeQL still failing on both.
  - BEHIND masks BLOCKED. L155 and L162, the CodeQL `fail` checks, are correct.
- **Corrected text:** "# OPEN; BEHIND at writing (`main` moved at 01:47:48Z and 02:02:04Z; BEHIND masks BLOCKED); the next line shows CodeQL failing".

**L-3. The "other live session" had already handed off, and the listing was at 01:37Z, not 01:40Z.**
- **Quoted:**
  - L147: "At 01:40Z `ListAgents` listed one other live session, "containers [2703c8]", which owns the 0.16.0 notify-consumers 403 (Appendix B)."
  - L284: "The containers session owns it."
- **Evidence:**
  - The transcript of session `2fba4397` records its last `ListAgents` call at 01:37:27.969Z (result 01:37:28.116Z). There is none after it.
  - juniper-ml#2100 was created at 01:39:45Z (commit `afc12c65`, 01:39:42Z). It is OPEN and not armed. Its handoff, `HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`, opens with "session `containers [2703c8]`". Its item 2 (lines 79-80) carries the `Notify consumer repos` 403.
  - This is the same class as round 1's M1: a peer cited as live after it had handed off.
- **Corrected text:**
  - L147: "At 01:37Z `ListAgents` listed one other live session, "containers [2703c8]". It handed off at 01:39Z in juniper-ml#2100 (`HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`, whose item 2 carries the notify-consumers 403)…"
  - L284: "#2100's handoff (containers) owns it."

**L-4. Document 2's ECO-014 sentence is quoted without its second half, which reverses its meaning.**
- **Quoted (L212):** "#2097 says "APD-CASCOR-014 closes when F4 lands" and "APD-ECO-014's condition is met". Both drop a validation gate".
- **Evidence:** document 2 line 136 reads in full: "APD-ECO-014's condition is met; its validation is yours." Line 134 (CASCOR-014) does drop the gate.
- **Corrected text:** "#2097 says "APD-CASCOR-014 closes when F4 lands", which drops F4's validation gate. Its "APD-ECO-014's condition is met; its validation is yours" keeps the gate, but gives #685's validation to the register lane; here it is Work 3 [F]. These gates govern."

**L-5. No ledger records F-CANOPY-061/062 yet.**
- **Quoted (L234):** "Its ledger records 061/062 as FIXED-BY #685".
- **Evidence:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` on `origin/main` has no match for `F-CANOPY-06[0-2]` or `FIXED-BY`.
  - #2096 does not touch the ledger (12 files).
  - #2096's handoff F10 (lines 123-125) says "Record FIXED-BY #685". Its draft (`DRAFT_r1.md:155`) says "061 and 062 are to be FIXED-BY a canopy PR from branch `fix/secret-leaks-683-validation`".
  - The wording came from round-1 lane O's own L1.
- **Corrected text:** "Its F10 says to record 061/062 as FIXED-BY #685 when they are filed".

**L-6. The data fix-forward shifts the handler anchors by six lines, not one.**
- **Quoted (L246):** "`juniper_data/api/app.py:187-212`, `ValueError` handler `:214`, at `0f0f7e0e`; the data fix-forward shifts them by one line".
- **Evidence:** the `exception_handler` decorators sit at 187/214 at `0f0f7e0e`, at 188/215 at `d1c66a11`, and at **193/220 at `94ce8b1f`**, the branch head. "One line" was true of `d1c66a11`.
- **Corrected text:** "…the data fix-forward (`94ce8b1f`) moves them to `:193-218` and `:220`".

**L-7. cascor's 422-echo anchors were stale at writing: #690 edited `src/api/app.py`.**
- **Quoted (L247):** "cascor (`src/api/app.py:856`, `ValueError` handler `:916`)".
- **Evidence:**
  - `compare b9484fef...0fbb447a` lists `src/api/app.py`.
  - At `main` `0fbb447a`, `@app.exception_handler(RequestValidationError)` is at :858 and `@app.exception_handler(ValueError)` is at :918. (`:335` is unchanged.)
- **Corrected text:** "cascor (`src/api/app.py:858`, `ValueError` handler `:918` at `0fbb447a`; round 3 measured at `:856`/`:916`, before #690)".

### NIT
- **N-1.** L44 ("its executor finished at 01:48Z") and L70 ("about 01:48Z"). The executor's last record, its disposition report, is at 01:49:10.537Z. Its push was at 01:46:46Z. Use "01:49Z".
- **N-2.** L71: "It pushed ONE signed commit". The same agent (`agent-a46e715a6801b98ca.jsonl`) also pushed `d1c66a11`: a `push_signed_commit.py --expected-head 0f0f7e0e…` at 20:44:56Z, committed at 20:44:58Z. Use "For the round-1 fixes it pushed one signed commit… (its first push, at 20:45Z, was `d1c66a11`)".
- **N-3.** L46: "handed-off sessions stay listed for days". This round contradicts it:
  - "defect reg [042116]" handed off at about 01:20Z (#2097) and "canopy combined [577a1c]" at about 01:19Z (#2096). Neither is in the 01:37:28Z listing.
  - The instruction ("carry on") stands. Use "a handed-off session may stay listed".
- **N-4.** L51 and L276: "probe code logging the probe's own `SECRET` constant". That is true of `sentry_deep_probe.py:196` and `:201` (`SECRET` is defined at its line 18). `surrogate_config_probe.py` has no `SECRET`: its line 29 prints `lone[0].encode("utf-8", "surrogatepass")`, the lone-surrogate test key the probe sets itself at lines 8-19. Use "probe code logging values the probe sets itself".
- **N-5.** L62: "cascor still running at 02:07Z". At 02:07Z cascor's post-merge `CI/CD Pipeline` on `b9484fef` (#689) was already CANCELLED (run 36084194157, 02:06:57Z, superseded by #690's push). Only `0fbb447a`'s run was running. Now MOVED (MV1).
- **N-6.** L225: "#689's first commit message". #689 had one commit (`97341680`). Use "#689's commit message".
- **N-7.** L354: "(`util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py`, on `main`…)". It is on juniper-ml's `main`, and absent from juniper-data's (`ls-tree` is empty). The section is about juniper-data. Use "on juniper-ml's `main`".
- **N-8.** L451: "at `:135-137`". `presented = _compare_bytes(api_key)` is at canopy `src/security.py:134` (`dc5ea02e`), and the compare is at `:137`. Use `:134-137`. The TypeError clause is right: str against bytes.
- **N-9.** L454: "the shared juniper-data and juniper-canopy checkouts lag `origin/main`".
  - cascor's also lags: local `main` is `7f4a7213`, and its `origin/main` ref is `b9484fef` while the remote is at `0fbb447a`.
  - The recipe `git -C <clone> archive origin/main` therefore needs `git -C <clone> fetch origin main` first, as Appendix D item 1's does.

## Moved since 02:10Z (not errors)
- **MV1.** cascor's post-merge `CI/CD Pipeline` on `0fbb447a` finished **success at 02:16:38Z**. All five workflows on it are green, so L59's "green on all" now holds, through `0fbb447a` (which contains `b9484fef`).
- **MV2.** juniper-ml `main` moved: #2101 merged at 02:17:23Z (`b82d12d7`).
  - `fizzy-hugging-dream` is now 8 behind the remote `main`. Its local `origin/main` ref is still `3055a892`.
  - My dry run resolved its base to `3055a892` at about 02:14Z. Re-fetch before the real run.
  - Unchanged: #2089 and #2097 are still OPEN, BEHIND, unarmed, with CodeQL failing. #2096 and #2100 are OPEN. There is still no consolidation PR, and the data branch is still `94ce8b1f` with no PR.

## Round-1 disposition

| Round-1 finding | r2 | Notes |
|---|---|---|
| F-M1 (canopy peer gone; #2096) | APPLIED | L147, L234 and L227-233 are right. One new clause is wrong (L-5), and L147 repeats the class with "containers" (L-3). |
| F-L1 (happy-skipping-hollerith) | APPLIED correctly | L190. HEAD `5af9d722`; all 95 of #2097's files byte-identical, re-checked. |
| F-L2 (evidence indexes) | APPLIED correctly | L17, L48 |
| F-L3, F-N1 (relaunch brief) | MOOT, correctly dropped | The executor finished; the recipe is gone. No explicit reason is given, but "In flight: nothing" implies it. |
| F-L4 (Lane F memory edits) | APPLIED correctly | L496 |
| F-N2 (str_as_bool) | APPLIED correctly | L219; `manager.py:232` at `0fbb447a` |
| F-N3 (01:18Z) | APPLIED correctly | L400 |
| F-N4 (skipped=3) | APPLIED correctly | L169; re-run |
| F-N5 (dirty counts) | APPLIED correctly | L475-478: 1, 16, 1, 5, re-counted with `--no-optional-locks` |
| F-MV1 through MV6 | APPLIED correctly | 94ce8b1f, merges, #690, draft re-copy, 7 behind (now 8, MV2), opener in the ship list |
| F-MV7 (peer listing) | APPLIED, time wrong | L-3 |
| O-H1 = P-M4 (#2097 CodeQL) | APPLIED | Facts verified (check-run 107905207679; alerts 876-878). The BLOCKED annotation was stale at writing (L-2). The ":29 = SECRET" wording came from O-H1 itself (N-4). |
| O-M1 (worktree guard) | APPLIED correctly | L188. The re-copy step is moot: the draft was re-copied at 01:49:50Z and verified equal. |
| O-M2 (re-read the PR head) | APPLIED correctly | L92 |
| O-M3 (lane tags) | APPLIED correctly | L254 and the [F]/[R] tags |
| O-M4 (closes-PR gate) | APPLIED correctly | L81, Appendix J Work 6 |
| O-M5 = P-M3 (own path) | APPLIED correctly | L4 |
| O-L1 (#2096 keeper) | APPLIED, one clause wrong | L-5 |
| O-L2 (stale canopy comment) | APPLIED correctly | L411; `src/tests/unit/backend/test_cascor_service_adapter_gate_coverage.py:49-50` verified |
| O-L3 (filing evidence) | APPLIED correctly | L200; snapshot lines 11-20 verified |
| O-L4 (COMMIT_MESSAGES) | APPLIED correctly | L103, L325. All four repos squash with COMMIT_MESSAGES. |
| O-L5, O-L6, O-L7, O-L8, O-L9, O-L10 | APPLIED correctly | Work 8; L17 and L48; Appendix G (the 14 files of #2088 verified); L157; L168 (16); L518 and L530-532 |
| O-N1 to N6, N9 to N11, N13 to N22 | APPLIED correctly | N19 has an ambiguity (N-7) |
| O-N7 ("merged cleanly") | APPLIED correctly | L584. The fix report says "clean in either order"; my `git merge-file` of CHANGELOG (base `0f0f7e0e`, `94ce8b1f`, `26491531`) is clean. |
| O-N8 (#2089 details) | APPLIED, with a corrected count | 66 = 48 `.bash` + 18 `.sh` across the six lane dirs, counted. Document 1 said 67; r2 changes it without saying why. |
| O-N12 (not armed) | MOOT | All merged |
| O-N23 | APPLIED | L80 |
| P-H1 (index lock) | APPLIED correctly | L160 |
| P-M1 (liveness) | MOOT / APPLIED | First action 2 rewritten; the executor finished |
| P-M2, M5, M6 | APPLIED correctly | L46 and L186; L150, L152 and L167; L75 and Appendix J |
| P-L1, L2, L4, L5, L7, L8 | APPLIED correctly | #2080 body L19, L23 (header row), L41, L65 and L69, and #2088 body L47, verified; serve script `timeout 1500` (line 75); import by path (line 39) |
| P-L3 (three brief records) | MOOT | Executor finished |
| P-L6 (validation lanes in flight) | NOT APPLIED, no reason given | "In flight: nothing". Partly covered by L168's "+3 per later validation round". |
| P-N1 to N7, N9 | APPLIED correctly | JuniperCanopy1 is 3.13.13 |
| P-N8 (length) | Not factual | The step details moved to Appendix J |

## Claims table

| Claim (line) | What I ran or read | Result |
|---|---|---|
| L3-4: file path, untracked, hash | `git status`; sha256 | CONFIRMED |
| L9: 1 FAIL + 2 PWC, then all PWC | VERDICT lines of the 8 reports | CONFIRMED |
| L11: "Never message it" / "message it too" | document 2 line 3; document 1 | CONFIRMED |
| L14: [977fa8] = `8f86dec2`, ended | document 3 L3; ListAgents 19:03Z and 19:35Z | CONFIRMED |
| L17: document 2 governs until on `main` | document 2 | CONFIRMED |
| L40: safe_merge prints a `MERGED` line | `util/safe_merge.py` | CONFIRMED |
| L44, L70: executor finished 01:48Z | transcript last record 01:49:10Z | REFUTED (N-1) |
| L46: handed-off sessions stay listed for days | ListAgents 01:37:28Z | REFUTED (N-3) |
| L49: ml#1118 | document 2 L29 | CONFIRMED |
| L51, L276: 01:23:44Z, `2e4917c2`, 45/3, rule, three locations | check-run; code-scanning alerts | CONFIRMED |
| L51, L276: "SECRET constant" for all three | probe sources at `2e4917c2` | REFUTED (N-4) |
| L60-61: nine merges, SHAs and times; #686 CLOSED | GraphQL | CONFIRMED |
| L62: #689, #440, #690 merges; `81154187` (parents `78e99414`, `b9484fef`); armed 01:57:06Z | GraphQL; `pulls/690/commits` | CONFIRMED |
| L62, L413: validated before merge | merged heads = `97341680` and `0bee089e` | CONFIRMED |
| L62: data post-merge green | runs on `26491531` | CONFIRMED |
| L62: "cascor still running at 02:07Z" | `b9484fef` CI/CD cancelled 02:06:57Z | REFUTED (N-5) |
| L59: post-merge CI green on all | `0fbb447a` green 02:16:38Z | MOVED (MV1) |
| L66: heads; not armed | GraphQL | CONFIRMED |
| L66, L154, L156: BLOCKED | `mergeStateStatus` BEHIND | REFUTED (L-2) |
| L67, L158-159: branch `94ce8b1f`, no PR | `git/ref`; `pr list` | CONFIRMED |
| L68, L163: no open data, cascor or canopy PR | `pr list` | CONFIRMED |
| L71: `94ce8b1f`, parent, verified, 01:46:46Z, 12 files | commits API | CONFIRMED |
| L71: "ONE signed commit" | transcript push at 20:44:56Z | REFUTED (N-2) |
| L72: fix report verbatim; draft beside it | archiver `--check` OK (agent `a46e…`) | CONFIRMED |
| L73, L160, L189: data worktree clean, in sync, at `94ce8b1f` | `--no-optional-locks status -sb`; `rev-parse` | CONFIRMED |
| L79: F-item to PR mapping | Appendix D table | CONFIRMED |
| L91: untracked diff fakes deletions | git semantics | CONFIRMED |
| L98: both pushers take `--commit-body-file` | both scripts | CONFIRMED |
| L102: the symbol screen scans lines | `symbol_loss_check.py:418` (MULTILINE) | CONFIRMED |
| L103, L325: COMMIT_MESSAGES | repo API | CONFIRMED |
| L110: register L176 and L177 | worktree and `origin/main` | CONFIRMED |
| L113: census 69 / 82 | ran it | CONFIRMED |
| L115: JuniperCanopy1 is 3.13.13 | `--version` | CONFIRMED |
| L131, L270: the shell exports `SENTRY_SDK_DSN` | presence test only | CONFIRMED |
| L147, L284: live "containers" owns the 403; 01:40Z | ListAgents 01:37:28Z; #2100 | REFUTED (L-3) |
| L153: no consolidation PR | `pr list` | CONFIRMED |
| L155, L162: CodeQL fail | `gh pr checks` | CONFIRMED |
| L157: all MERGED, SHAs | GraphQL | CONFIRMED |
| L164-165: 136/100/36; AGREE | ran both | CONFIRMED |
| L166-167: OK positive; 0 errors | 48 OK; 0 | CONFIRMED |
| L168: 16 | ran it | CONFIRMED |
| L169: "Ran 11 … OK (skipped=3)" | ran it | CONFIRMED |
| L170: seven worktrees | ran it | CONFIRMED |
| L171, L132: /tmp at 83% | `df -i` (82% at 02:17Z) | CONFIRMED |
| L176: three local scratch commits | `git log` | CONFIRMED |
| L177-184, L187: ship set = the opener's 22 files; nothing staged | dry run; porcelain status | CONFIRMED |
| L185: #2089's files untracked there | status | CONFIRMED |
| L186: wraps, names, excludes #2089's, missing file, open-PR REST listing, email check active | source; dry run; email length > 0 | CONFIRMED |
| L186: 7 behind at 02:07Z | `rev-list` 3/7 against `3055a892` | CONFIRMED (now 8, MV2) |
| L186: "a file `origin/main` already holds is refused" | blob comparison | REFUTED (L-1) |
| L186: `const:SESSIONS`; the rename | extractor diff; `symbol_loss_check.py:281` | CONFIRMED |
| L190: HEAD `5af9d722`; 95 files identical | ref file; blob hashes against the PR's shas | CONFIRMED |
| L190: no tracked changes, exactly 95 untracked | `git status` is refused there | UNVERIFIABLE |
| L196, L391: #690's commits, merge, squash | GraphQL; commits API | CONFIRMED |
| L200: snapshot lines 11-20 | `git show origin/main:` | CONFIRMED |
| L202-203: ECO-013's fixes merged; 01:57Z | GraphQL | CONFIRMED |
| L212: the quotes exist | document 2 lines 134 and 136 | CONFIRMED |
| L212: "Both drop a validation gate" | document 2 line 136 | REFUTED (L-4) |
| L219: remedy key; `str_as_bool` | `manager.py:245`, `:232` at `0fbb447a` | CONFIRMED |
| L221: `owner-rulings-verbatim.md` exists | reports directory | CONFIRMED |
| L225: "4001 close" in `b9484fef` | commit message | CONFIRMED (N-6) |
| L226: ledger path | `origin/main` | CONFIRMED |
| L231: `:4766` before #690; `:4841` after | `manager.py` at `b9484fef`, `78e99414`, `0fbb447a` | CONFIRMED |
| L234: #2096 state, head, times, filename, blobs `cc267d2b`/`ed4de235`, `:165-170`, F9/F10/A2(a) | GraphQL; files API; hashes | CONFIRMED |
| L234: "Its ledger records…" | ledger on `main`; #2096 files | REFUTED (L-5) |
| L246: anchors at `0f0f7e0e` | `git show` | CONFIRMED |
| L246: "shifts them by one line" | `94ce8b1f` 193/220 | REFUTED (L-6) |
| L246-247: round-3 conditions; locked and env pairs; cascor 400 | round-3 reprobe; data lock; JuniperCascor1 dist-info (0.137.0, 1.0.0) | CONFIRMED |
| L247: cascor `:856`/`:916` | `0fbb447a` 858/918 | REFUTED (L-7) |
| L275: #2089's alerts, 129 probes, 66 runners (48/18), README | alerts; PR files; lane dirs; README | CONFIRMED |
| L278: `codeql.yml` | `main` | CONFIRMED |
| L282: MEMORY.md 24,929 | `wc -m` | CONFIRMED |
| L290: D-F files in the fix-forward | `git diff --name-only` | CONFIRMED |
| L304-309: two signed commits; 6.6 s | commits API; `94ce8b1f` message | CONFIRMED |
| L311-315: fix-report claims and numbers; single-thread executor; `stage_save`; `http_cache.py` untouched | fix report; `datasets.py:112`; diffs | CONFIRMED |
| L317, L320: `compute_checksum` at `:446`/`:392`; defensive lines | `git show` | CONFIRMED |
| L325: `d1c66a11`'s subject; waiver only in `94ce8b1f` | messages | CONFIRMED |
| L327: draft equality; 01:49:50Z / 01:48:13Z; both commits | byte compare; mtimes | CONFIRMED |
| L354: verify script "on main" | juniper-ml `main` yes, juniper-data no | CONFIRMED (N-7) |
| L389: branch; serve script; import by path | contents at `2e4917c2` | CONFIRMED |
| L407, L411: canopy `:137`, `:300`, `csrf.py:97`; stale comment | `dc5ea02e` | CONFIRMED |
| L423-428: F-table anchors; #689 body; no "4001" in #440 | `0fbb447a`; PR bodies | CONFIRMED |
| L432-441: locks and caps (spot check); `app.py:335` | lock files; data `pyproject:110` | CONFIRMED |
| L447-453: marker anchors in all four copies; encode counts 2/2/2/1; `:289` | `main` sources | CONFIRMED |
| L451: `:135-137` | canopy `:134` | REFUTED (N-8) |
| L454: data and canopy checkouts lag | local refs | CONFIRMED (N-9) |
| L456: `:205-209` | test file | CONFIRMED |
| L468-478: Appendix F HEADs, signatures, tree equalities, dirty counts | per-worktree `git` | CONFIRMED |
| L488-495: #2088's 14 files; #2089's 132; the 12 files in the fix report | files API; fix report | CONFIRMED |
| L507-508: #683 from `34e06747`, #685 from `e70b54dc` | GraphQL | CONFIRMED |
| L583: waiver text; the main-verify symbol screen | `94ce8b1f` message; `main-verify.yml:235` | CONFIRMED |
| L584: CHANGELOG merges clean; data `main` still `26491531` | `merge-file`; commits API | CONFIRMED |
| L590: seven `util/ad-hoc/` files | `git diff --stat 990ef3f9 2439d049` | CONFIRMED |
| L607-608: #2080 and #2088 body lines | PR bodies | CONFIRMED |
| L230 (spot check): DATA-055's lock half | `base.py:484`, `:657` at `0f0f7e0e` | CONFIRMED |
| L9: "Every correction is applied" | not re-derived | UNVERIFIABLE |
| L141: refusal observations | one refusal of mine was consistent with it | UNVERIFIABLE |

**Changed:** no repository file. My scratch directory `hc2/laneF/` holds only read-only probe scripts. I deleted every extraction I made.

Counts: 97 claims checked: 80 CONFIRMED, 13 REFUTED, 1 MOVED, 3 UNVERIFIABLE. Findings: 0 HIGH, 0 MEDIUM, 7 LOW, 9 NIT, plus 2 live-state moves.
