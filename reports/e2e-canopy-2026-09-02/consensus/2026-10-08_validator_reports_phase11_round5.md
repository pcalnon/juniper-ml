<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 5 — validator reports (verbatim)

Round 5 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen 684d70bc (round 4's pass applied to adcba49f), 2026-10-08. Two lanes from one brief, reports/e2e-canopy-2026-09-02/drafts/lane11R5_phase11_ledger_brief.md, briefed on round 4's corrections only. Each report below is the lane's final message, verbatim (each lane ran once, so the archiver's round-1 mode applies). The orchestrator's dispositions are in the ledger's Phase 11 Consensus record; the correction pass is util/ad-hoc/2026-10-08_phase11_ledger_round5_corrections.py.

## Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections)

*agent `abbb8479da1ec5a2f` · round 1 · last-assistant-text (not resumed) · 13181 chars*

Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections)

**VERDICT: SOUND-WITH-FIXES.** Round 4's pass replays byte for byte on all three files, with no hand edit. My own reader of the two transcripts gives every trigger-lag number the pass added or changed. The triage counts hold, and under each of the three rulings every statement gives the same ratings and counts. The CodeQL pass's second run changes nothing a probe computes, and the prescreen reports nothing on the branch's 110 added or changed Python files. One MINOR finding changes an action: the canopy manual check that round 4 added covers F-CANOPY-012 only, but the manual section it cites also documents the behaviour F-CANOPY-013 breaks. Three NITs change nothing.

L-numbers refer to `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `684d70bc`. Where two values are given, they are run 1 ; run 2. $S is my `mktemp -d` directory, `…/scratchpad/lane11R5A.LBVRcz`.

**TABLE**

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | The round-4 pass on the 3 files at `adcba49f` gives `684d70bc`; "20 … 1 … 2" substitutions | All 3 files identical (sha256 `c8caccb5…`, `4a24d9fb…`, `cf0d8e92…`). It printed "20 substitutions … README: 1; rederive: 2". `--check` wrote nothing, and a second run refuses ("not the round-4 freeze"). | MATCH, no hand edit | `$S/replay.sh` |
| 2 | Triage gives 79/53/1/2/23, 7 open P1, 16 open P2 | Identical. F-012, F-013, F-018 and F-057 are open P2. | MATCH | `e2e_finding_triage.py --note` |
| 3 | The question stated one way; ratings under each ruling | F-065's header and Severity bullet, the Unresolved bullet and the Matrix all read "a shipped CHANGELOG or design-plan promise". F-068's header, the Summary and the Rating lead read "description of an internal mechanism", with the second limb stated as an exception. Under neither / first limb only / both rulings, F-065 is P2/P1/P1 and F-068 is P2/P2/P1 everywhere, which gives 5/18, 6/17 and 7/16. Phase 10's own question (L10316) does not say "shipped". | holds; NIT F3 | grep of every statement |
| 4 | F-068's contract bullet and item 0 now say "description" | L10725, L10729, L11128. Round 1's re-derived list still says "`[0.8.0]` promise" (L10921), but that is a record and gives no rating. | holds | — |
| 5 | F-012 reached through the design note's h-5 row and `:627` | `:104` (h-5, canopy #224, merged); `:47-49` (every CAN-015h item except h-6 merged); `:627` "Output-layer "Patch weights" expander as a separate card" | MATCH | design note at `684d70bc` |
| 6 | The manual at `28da69f8^`, `:407-415`, both quotes | `:407` Patch Weights, `:409` `output_weights`, `:414` "comma-, semicolon-, or newline-separated floats", `:415` "lets CasCor validate the exact target shape". canopy#535 does not touch the manual: the text is unchanged at `c7876f5a:448-456`. | MATCH | canopy object store |
| 7 | canopy#535 merged as `28da69f8` on 2026-08-28; canopy#533 on 2026-08-28; re-drive owed | #535 merged 04:54:55Z with merge sha `28da69f8…`; #533 merged 05:09:29Z; the re-drive is owed at L6154 | MATCH | `gh api` GET |
| 8 | F-012's entry rates it P2 because the failure is "loud, precise, and non-mutating", and does not weigh the manual | P2 in the header; the quote is its "Mitigating" sentence (L3844); no mention of the manual | holds | L3833-3846 |
| 9 | F-013 unsettled: "the note promises no message text (Lane 11-R3A)"; "No open finding has been swept …"; item 26's first step | True of the note, and true that no sweep has run. But the same manual section has a workflow step that F-013 breaks, and item 26 checks only F-012 against the manual. | omits (F1); attribution NIT (F4) | manual `:424` |
| 10 | Gate and tab triggers took effect 1.3–4.2 s after firing, after the targeted request was answered | T-gate write at +1,336 ; +1,367 ms (target answered at +504 ; +83). T-tab writes at +1,304 and +3,396 ; +1,581 and +4,203 (target answered at +792 ; +788). | MATCH | `$S/triglag.py` |
| 11 | T-mode: "targeted requests were answered 0.6 s and 1.1 s after it fired"; next request 2.1–2.5 s later; its effect not recorded | +629 ; +1,086 ms. Next W record at +2,148 ; +2,503. The shim's W records carry no cause, and nothing logs the mode store. | MATCH | same |
| 12 | Flight age at firing 1.6–2.9 s, median flight 2.8 s; clicks returned at 0.7–1.0 s and 2.3–2.9 s; the wait took 1.6–1.9 s; click to gate write 0.3–1.9 s | 1,633–2,914 ms; medians 2,817 ; 2,814; clicks 993, 2,936 ; 708, 2,313; waits 1,943 ; 1,605; click to write 311, 460 ; 873, 1,890 | MATCH | same |
| 13 | README's new sentence | Agrees with rows 10-12. T-gate's delay is not split at all; T-tab's is split only in part. | MATCH | README:69-72 |
| 14 | "Of the trace's two modes, only the report exits 2 …, while the replay refuses too" | The trace has two modes, the report and `--self-test`. With one innermost record dropped (617 ; 610 records), the report exits 2, `--self-test` exits 0 and the replay exits 2. Unmutated, all three exit 0. | MATCH | `$S/guard.py` |
| 15 | Rederive script's docstring | The 10-08 report file exists, and only the docstring changed. Output: the 8 trigger-started evictions at 1,214–2,391 ms, 7 of them by fires at 1,417–2,391 ms, and the 21 in-run evictions at 1,422–2,553 ms. | MATCH | run with `-B` |
| 16 | Round-3 record: "as their transcripts record"; the stamp credited to Lane 11-R2A; the pointer it left out | Each round-3 transcript has a 67-char API error message containing "weekly" and "limit", at 2026-10-05T23:18:52Z ; 23:20:19Z, followed by a 58.9 h gap to the resume at 2026-10-08T10:13Z. Round 2's report file `:77` is Lane 11-R2A's statement on the stamp, and round 3's `:187` credits it. Round 3's `:102` is Lane 11-R3A's pointer. | MATCH | `$S/lane_transcripts.py` |
| 17 | Round-4 record: verdicts, each lane's work, 18 probes | Both lanes SOUND-WITH-FIXES. The final messages (14,821 ; 13,780 chars) are verbatim in the report file. There are 18 top-level probes (10 + 8). The Verdicts bullet omits Lane 11-R4B's F1 claim. | MATCH, except NIT F4 | report file |
| 18 | Round-4 record: the slips | Lane 11-R4A's one bytecode file is recorded correctly. Lane 11-R4B's two are missing. | MISMATCH (omission), F2 | worktree mtimes; transcripts |
| 19 | CodeQL `--round r4`: 7 edits in 6 files, nothing computed changes | Replayed the archiver `--round 4` and then the pass: 18 of 18 files identical to `684d70bc`. The prescreen gives 7 alerts before and 0 after. All 6 edited files are AST-equivalent once the `with` blocks are undone, and `srcs`, `hashlib` and `sys` are never read. | MATCH | `$S/cq_replay.sh`, `cq_ast.py` |
| 20 | Prescreen reports nothing on the branch's Python files | 0 alerts in the 110 files added or changed between `200c1393` and `684d70bc`; `--known-answer` passes | MATCH | `$S/prescreen_branch.py` |
| 21 | F-058's and F-065's entries against Phase 11 | They agree: the 8 at 1.2–2.4 s, the 21 at 1.4–2.6 s and the four trigger kinds; F-065's wording matches the Unresolved bullet and the Matrix | holds | L9133-9157, L10087, L10133 |

**FINDINGS**

1. **MINOR: the manual check that round 4 added covers F-CANOPY-012 only, though the manual section it cites also documents the behaviour F-CANOPY-013 breaks. The Matrix and item 26 also disagree on whether a manual sweep is owed.**
   - **Quoted:**
     - L11097-11098: "No open finding has been swept against canopy's CHANGELOG, the design plans or canopy's manual".
     - L11114: "F-CANOPY-013, the editor's success messages, is unsettled: the note promises no message text (Lane 11-R3A)."
     - L11115: "Item 26 is the sweep, owed with the ruling; it checks F-CANOPY-012 against the manual first."
     - Item 26 (L11145-11148): "First, without waiting for the ruling, check F-CANOPY-012 against canopy's manual … Once the owner rules, check each open finding … for a promise, of a kind the ruling counts".
   - **Evidence:**
     - canopy's `docs/USER_MANUAL.md`, Network Editor workflow step 6: "Use the API response shown in the status alert to confirm the edit."
       - It is at `:424` at `28da69f8^`, nine lines below the pass's `:407-415`.
       - It is also at `:424` at `359e1bf7^`, canopy#532's parent. canopy#532 fixed F-013 and did not touch the manual.
       - It is at `:387` at `3411673c` and at `:465` at `c7876f5a`.
     - F-013's alerts read "Appended unit at index None (now None hidden units)" and "Removed unit 9 (now None hidden units)" (L4086-4087), and rows 09 and 13 are scored "FAIL on status message" (L4146). Its entry calls that alert "the one surface an operator has for confirming a blind mutation" (L3861), yet rates it P2 as "Cosmetic only".
     - Item 26's post-ruling sweep looks only for promises "of a kind the ruling counts", so as written nothing but F-012 is checked against the manual. The Matrix's "the sweep" implies more.
   - **Fix:**
     - In item 26's first step: without waiting for the ruling, check the open findings against canopy's manual, F-CANOPY-012 and F-CANOPY-013 first. Or narrow the Matrix's sentence to match.
     - In the F-013 bullet: it is unsettled against the note, and the manual may reach it without any ruling (`:424` at `28da69f8^`).
   - **Changes a number, disposition or action?** Action: yes (item 26's first step, and the reach put to the owner). Number: no, until the check is made.

2. **NIT: the round-4 Slips bullet leaves out Lane 11-R4B's bytecode writes.**
   - **Quoted (L11083-11085):** "Lane 11-R4A … wrote one git-ignored bytecode file into the worktree … Lane 11-R4B ran one canopy `git log` …"
   - **Evidence:**
     - The worktree holds `util/ad-hoc/__pycache__/2026-10-05_archive_phase11_lane_probes.cpython-314.pyc` and `…_phase11_probes_codeql_fixes.cpython-314.pyc`, both with mtime 2026-10-08 10:59:24Z.
     - Lane 11-R4B's transcript has `python3 <scratch>/codeql_check.py` without `-B` at 10:59:23Z. That probe loads both of those worktree files by path (`…r4_b_codeql_check.py:43-44`).
     - Neither Lane 11-R4A nor the orchestrator ran anything in that window.
     - Lane 11-R4A's report had flagged them: "Two other caches … written at 05:59:24, were not written by my commands."
   - **Fix:** Record Lane 11-R4B's two git-ignored bytecode files; no tracked file changed.
   - **Changes a number, disposition or action?** No.

3. **NIT: "worded as Phase 10, F-CANOPY-065's header and its Severity bullet word it" (L11062), and "(round 4 restored Phase 10's wording)" (L11005).**
   - **Evidence:** Phase 10's question (L10316) reads "a CHANGELOG or design-plan promise counts as "documented"". Phase 11 (L10932, L11093) and F-065 (L10087, L10134) read "a shipped CHANGELOG or design-plan promise". No rating turns on "shipped": both entries in play, 0.6.0 and 0.8.0, shipped.
   - **Fix:** Say "as F-CANOPY-065's header and Severity bullet word it", or drop "shipped".
   - **Changes a number, disposition or action?** No.

4. **NIT: the round-4 record's account of the lanes.**
   - **Evidence:**
     - The Verdicts bullet (L11054-11056) names only the F-012 omission as changing an action. Lane 11-R4B's F1 (MINOR) also said it changes an action (the question put to the owner) and a number (F-068's rating and 6/17, under one ruling).
     - In "the note promises no message text (Lane 11-R3A)" (L11114), the reason is Lane 11-R4A's ("N promises no message text"); Lane 11-R3A said only "not settled".
     - The trigger-lag bullet credits both lanes, but T-mode's unrecorded effect was raised by Lane 11-R4B's F3 alone; Lane 11-R4A's F5 concerned only the README's split.
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Whether the manual makes F-012 or F-013 P1, which is item 26's job, and whether canopy#532 and #535 hold live; no re-drive was possible.
- When T-mode's change took effect in the page. The transcript does not record it, as the ledger says.
- What CodeQL itself reports, including whether a `pass` with a trailing comment clears `py/empty-except`. The prescreen is only a predictor, though an adequate one: it fires 7 times on the pre-fix round-4 archive and passes `--known-answer`.
- The full sweep that item 26 owes.

**SECRETS/PII:**
- No environment values, tokens, credential files or e-mail addresses were printed, requested or sent.
- Git in juniper-ml, through the worktree only: `log --format='%h %s'`, `status --short`, `rev-parse`, `merge-base`, `diff`, `show <rev>:<path>`, `ls-tree` and `check-ignore`.
- Git in canopy's object store: `cat-file -t`, `rev-parse`, `show <rev>:<path>`, `diff --name-only`, a manual-only `diff` and `branch --list`. No fetch.
- `gh api` GETs of canopy PRs 532, 533 and 535, with `--jq` selecting number, merge time, merge sha, base and title.
- From the lane transcripts and the session transcript I printed only timestamps, lengths and match flags, plus the round-4 lanes' Python script names in one two-minute window.
- Every Python run used `-B`, and I checked that no bytecode was written into the worktree.
- I touched no port, service or browser, and did not open Lane 11-R5B's directory.
- No slip.

---

## Lane 11-R5B (adversarial, on round 4's correction pass)

*agent `ae4dfd4f5bbf0e3d0` · round 1 · last-assistant-text (not resumed) · 12674 chars*

**Lane 11-R5B** (adversarial, on round 4's correction pass)

**VERDICT: SOUND-WITH-FIXES.** I replayed round 4's pass and it reproduces all three files byte for byte, with no hand edit. Under every ruling, every rating statement gives the same rating for F-CANOPY-065 and F-CANOPY-068, and the counts 5/18, 6/17 and 7/16 hold. Every trigger-lag figure re-derives from the transcripts with my own reader. The CodeQL edits change nothing any probe computes. One MINOR finding changes an action: the Matrix says no open finding has been checked against canopy's manual and calls item 26 "the sweep", but item 26 checks only F-CANOPY-012 against the manual. F-CANOPY-013, already on the list, breaks a step of the same manual section. Under §4 that requires round 6. There are four NITs.

**TABLE** (L… is the ledger at `684d70bc`; values are "T1 ; T2")

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | Round 4's pass on the 3 files at `adcba49f` gives `684d70bc` | All 3 files byte-identical. It printed "20 substitutions … README: 1; rederive: 2" | MATCH, no hand edit | scratch replay + `cmp` |
| 2 | Triage: 79/53/1/2/23, 7 open P1, 16 open P2 | Identical | MATCH | `e2e_finding_triage.py --open-only` |
| 3 | Ratings by ruling (neither / first limb only / both) | F-065 P2/P1/P1 and F-068 P2/P2/P1 in every statement that rates them: F-065's header (L10087) and Severity (L10133-10135), Phase 10's O3 row and Unresolved (L9856, L10316), the Summary (L10570), F-068's header (L10715), the Rating lead and body (L10761-10766), Phase 11's Unresolved (L10932-10936), the Matrix (L11093-11096) and the round-1 record. Counts 5/18, 6/17, 7/16 | holds | same |
| 4 | Limb 1 "worded as Phase 10, F-CANOPY-065's header and its Severity bullet word it" | Phase 10 (L10316) reads "a CHANGELOG or design-plan promise"; Phase 11 and F-065 read "a **shipped** CHANGELOG or design-plan promise" | breaks by one word (F2) | L10316, L10932, L11062 |
| 5 | The contract bullet and item 0 call the `[0.8.0]` text a description | Yes, both do. L10921 still calls it a "promise", and item 26 sweeps "for a promise" | holds as scoped (F3) | L10725-10729, L11128, L10921, L11147 |
| 6 | F-012 through the design note: its h-5 row and `:627` | h-5 (canopy#224) is recorded merged at `:104`. `:627` reads 'Output-layer "Patch weights" expander as a separate card' | MATCH | the CAN-015g/h note |
| 7 | F-012 through the manual, `:407-415` at `28da69f8^`, both quotes | Both quotes verbatim, lines exact. `28da69f8^` is `58d72c12` (#534). canopy#535 merged 2026-08-28T04:54:55Z as `28da69f8` and did not touch the manual | MATCH | canopy object store; `gh api` GET |
| 8 | F-013 "unsettled: the note promises no message text (Lane 11-R3A)" | The note specifies no success-message text. That reason is Lane 11-R4A's; Lane 11-R3A said only "not settled". The manual's Network Editor workflow step 6 reaches F-013 | holds; incomplete (F1) | the note; round-3 report :102; round-4 report F1 |
| 9 | "No open finding has been swept against canopy's CHANGELOG, the design plans or canopy's manual" … "Item 26 is the sweep" | True that no sweep has been made. But item 26 owes the manual check for F-012 only | breaks against item 26 (F1) | L11097-11099, L11115, L11145-11148 |
| 10 | Summary: gate and tab triggers took effect 1.3–4.2 s after firing, after their targeted request was answered; T-mode's targeted request answered 0.6 s and 1.1 s after it fired | Gate writes: T-gate 1,336 ; 1,367 ms. T-tab 1,304 and 3,396 ; 1,581 and 4,203 ms. Targeted answers: T-gate +504 ; +83, T-tab +792 ; +788, T-mode +629 ; +1,086 ms | MATCH | my own reader, `$S/trig.py` |
| 11 | Instruments lead and its T-mode sentence; flight age 1.6–2.9 s; median flight 2.8 s; TOOK horizons 1.0 s and 2.5 s | Ages 2,426, 1,633, 1,704 ; 2,914, 2,197, 2,324 ms. Medians 2,817 ; 2,814 ms. Next request after T-mode +2,148 ; +2,503 ms. Clicks +993, +2,936 ; +708, +2,313 ms | MATCH | `trig.py`; `…_live.py` |
| 12 | README's new sentence | Only T-tab's delay is split (`clicks_ms`), and only in part. Nothing records T-mode's effect | MATCH | README:69-71 |
| 13 | "The watchdog cannot do what that entry describes" | The watchdog does re-enable a lane continuously disabled for 30 s | overreaches (F4) | L10728-10729 |
| 14 | Round-3 record annotations: "carried further", the omitted pointer, "as their transcripts record", the stamp's attribution | Both round-3 transcripts carry a synthetic API-error record naming "weekly" (23:18:52Z and 23:20:19Z, 2026-10-05). Lane 11-R2A's report says the click time includes the click's own handling (round-2 report :77). Lane 11-R3A's report :102 names F-012/F-013 | holds, except "Phase 10's wording" (F2) | transcripts (only flags and timestamps printed) |
| 15 | Round-4 record against the reports | Both reports are the lanes' final messages verbatim (14,821 and 13,780 chars). Verdicts, attributions, slips, the 18 probes and "20/1/2" all match. The Verdicts bullet leaves out Lane 11-R4B F1's own "changes a number" claim | holds | report file; agent transcripts |
| 16 | CodeQL `--round r4`: 7 edits in 6 files, nothing computed changes | All 18 committed probes equal the lane's source plus the archiver's header plus the 7 edits. The dropped names (`srcs`, `hashlib`, `sys`) are never read. The `with` rewrites and the added comment change nothing | MATCH | `$S/codeql_r4.py` |
| 17 | Prescreen on the branch's Python files | 0 alerts in all 110 `.py` files added or changed since merge-base `200c1393`. It fires 7 times on the unfixed round-4 probes. `--known-answer` passes | MATCH | prescreen |
| 18 | The fix pass's docstring guard on the name `fh` | The guard now runs only for files with an `open` edit. Two of the edited probes already use `fh` | breaks as worded (F5) | `…codeql_fixes.py:23-24`, `:183` |
| 19 | The rederive script's docstring | The cited file exists, and it says "was made". The script still prints 8 trigger-started evictions at 1,214–2,391 ms, 21 within runs at 1,422–2,553 ms, and 29 in all | MATCH | run with `-B` |

**FINDINGS**

1. **MINOR: item 26 owes no sweep of canopy's manual, though the Matrix says none has been made and calls item 26 the sweep. F-CANOPY-013 breaks the same manual section as F-CANOPY-012.**
   - **Quoted:**
     - Matrix (L11097-11098): "No open finding has been swept against canopy's CHANGELOG, the design plans or canopy's manual".
     - Matrix (L11115): "Item 26 is the sweep, owed with the ruling; it checks F-CANOPY-012 against the manual first."
     - Item 26 (L11145-11147): "First, without waiting for the ruling, check F-CANOPY-012 against canopy's manual … Once the owner rules, check each open finding not yet rated on a CHANGELOG or a design plan".
     - F-013 (L11114): "is unsettled: the note promises no message text (Lane 11-R3A)".
   - **Evidence:**
     - The manual section the ledger cites for F-012 says, nine lines lower, "6. Use the API response shown in the status alert to confirm the edit." That is `docs/USER_MANUAL.md:424` at `28da69f8^`, `:465` at `60ae1870`, and `:387` at `3411673c`, when F-013 was filed.
     - F-013 makes that alert read "index None (now None hidden units)" on a fully successful append (L3848-3865, L4083-4088). The ledger nowhere weighs this text.
     - Item 26 sends F-013 only to the half that waits for the ruling. So nothing in the ledger owes a manual check of F-013, or of any open finding except F-012.
     - The brief assumes item 26 owes the full sweep against the manual. Item 26 does not say so.
     - F-013's stated reason is Lane 11-R4A's, not Lane 11-R3A's.
   - **Fix:** Have item 26's first step check every open finding against canopy's manual, starting with F-CANOPY-012 (`:407-415`) and F-CANOPY-013 (`:424`, both at `28da69f8^`). Name the manual in F-013's bullet, and credit its reason to Lane 11-R4A.
   - **Changes a number, disposition or action?** Action: yes, item 26's first step and its scope. Number: only if the manual check upholds a P1.

2. **NIT: Phase 10's question is quoted with a word Phase 10 does not use.**
   - **Quoted:**
     - L10932: "Phase 10's question, whether a shipped CHANGELOG or design-plan promise".
     - L11062-11063: "worded as Phase 10, F-CANOPY-065's header and its Severity bullet word it, and the second limb is stated as its exception: whether it extends to".
     - L11005: "(round 4 restored Phase 10's wording)".
   - **Evidence:** Phase 10 (L10316) reads "whether a CHANGELOG or design-plan promise counts as "documented"", without "shipped". The wording round 4 used is F-065's header's. Also, the record calls "its exception" a clause that the ledger writes as an extension.
   - **Fix:** "Phase 10's question, as F-CANOPY-065's header words it", or drop "shipped". Replace "exception" with "a condition on it".
   - **Changes a number, disposition or action?** No. The 0.6.0 and 0.8.0 entries are both shipped.

3. **NIT: the split between "promise" and "description" is not carried everywhere.**
   - **Quoted:**
     - L10921: "canopy's CHANGELOG `[0.8.0]` promise, at `60ae1870`".
     - L11147: "for a promise, of a kind the ruling counts".
   - **Evidence:** Round 4 renamed the `[0.8.0]` text a description so that the first limb would not reach it, which was Lane 11-R4B F1's point. L10921 still calls it a promise. Under the "both" ruling, item 26's sweep criterion names only promises, which the ledger now says the second limb's kind of text is not.
   - **Fix:** Annotate L10921 "(a description since round 4)". In item 26, write "for a promise, or, if the ruling counts it, a description of an internal mechanism".
   - **Changes a number, disposition or action?** No. Every rating statement routes F-068 through the second limb, and "of a kind the ruling counts" defers to the ruling.

4. **NIT: "The watchdog cannot do what that entry describes" (L10728-10729) overstates.**
   - **Evidence:** The entry describes re-enabling the interval "once it has been continuously disabled for `METRICS_STORE_STRAND_TIMEOUT_MS`" (`CHANGELOG.md:1222-1223` at `60ae1870`). For a real strand the watchdog does exactly that: every 5 s sample finds the lane disabled, so it fires. The synthetic check caught its forced strand at each of five fires (L10807-10808). What the watchdog cannot do is re-enable *only* then. Round 3 had "The threshold cannot keep that promise."
   - **Fix:** "The watchdog cannot keep to what that entry describes".
   - **Changes a number, disposition or action?** No.

5. **NIT: the CodeQL fix pass's docstring states a guard the code no longer applies.**
   - **Quoted** (`util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py:23-24`): "no touched file may already use the name ``fh``, or nothing is written".
   - **Evidence:** The guard now runs only for files with an `open` edit (`:183`). The second run wrote `…r4_a_lane_interrupt.py` (`fh` at `:42-43`) and `…r4_a_prescreen_sweep.py` (`fh` at `:77-88`). Neither edit binds `fh`, so nothing computed changes.
   - **Fix:** "no file with an ``open()`` edit may already use the name ``fh``".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Whether §6.3 makes F-CANOPY-012 or F-CANOPY-013 P1 on the manual. I assessed no rating, and canopy#532 and #535 have had no re-drive.
- What CodeQL itself will report on the PR. The prescreen only predicts it, though it does fire and its known answer passes.
- Whether the lanes' scratch sources changed after they were archived. They match the archive now.
- Whether T-mode's `set_props` had any effect at all. Nothing logs it.
- Anything live: I touched no service, port or browser. I also did not do the full sweep item 26 owes.

**SECRETS/PII:** No environment values, tokens, credential files or e-mail addresses were printed, requested or sent.
- **juniper-ml git**, through the worktree only: `log --format='%h %s'`, `status --short`, `rev-parse`, `merge-base`, `diff` (including `--name-status` and `--word-diff`), `show <rev>:<path>` and `check-ignore`.
- **canopy git**, from its object store with no fetch: `cat-file -t`, `rev-parse`, `rev-list --parents -n 1`, `log --format='%h %s'`, `show <rev>:<path>` and `diff --name-only`.
- **`gh api`:** one GET of canopy#535, selecting merge time, merge SHA, base and title.
- **Transcripts:** in the four round-3 and round-4 lane transcripts I printed only counts, timestamps, record types and match flags.
- **Python and scratch:** I ran Python with `-B` throughout and checked that no bytecode was written. All scratch work is in my `mktemp -d` directory, `…/scratchpad/r5b.KImIJx`. I did not open Lane 11-R5A's directory. No slips.

---
