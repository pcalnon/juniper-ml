<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 6 — validator reports (verbatim)

Round 6 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen da08f639 (round 5's pass applied to 684d70bc), 2026-10-08. Two lanes from one brief, reports/e2e-canopy-2026-09-02/drafts/lane11R6_phase11_ledger_brief.md, briefed on round 5's corrections only. Each report below is the lane's final message, verbatim (each lane ran once, so the archiver's round-1 mode applies). Neither found anything that changes a number, a disposition or an action, so the review ended at this round; the orchestrator's dispositions are in the ledger's Phase 11 Consensus record, and the final wording pass is util/ad-hoc/2026-10-08_phase11_ledger_round6_corrections.py.

## Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections)

*agent `a5413a6e16401437a` · round 1 · last-assistant-text (not resumed) · 11737 chars*

**Lane 11-R6A** (measurement re-creation, artifact-first, on round 5's corrections)

**VERDICT: SOUND-WITH-FIXES.** Round 5's pass replays byte for byte with no hand edit. Every source claim it introduced re-derives: the manual's step 6 at all three commits, F-CANOPY-013's entry, canopy#532, the credits, the triage counts, and the ratings under each ruling. The CodeQL pass's third run replays exactly and changes nothing a probe computes. I found three NITs. Each is a false or misplaced statement in the consensus records, and none changes a number, a disposition or an action.

L-numbers are the ledger at `da08f639`. $S is my `mktemp -d` directory, `/tmp/tmp.y8saaB4Mk1`.

**TABLE**

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | The pass on `684d70bc` gives `da08f639` | Byte-identical (sha256 `6ecdd1ce…`). It printed "9 substitutions, 914499 -> 918968 chars". `--check` wrote nothing, and a second run refuses ("not the round-5 freeze"). Every hunk is inside Phase 11 (L10729–11199). | MATCH, no hand edit | `$S/replay`, `cmp` |
| 2 | Item 26 and the Matrix agree; nothing still says the manual check covers F-012 alone | Both say: every open finding against the manual first, with no ruling, F-012 and F-013 first, then the CHANGELOG and the design plans with the ruling. Item 26 alone adds "or, if the ruling counts it, a description…". It also dropped "of a kind the ruling counts", which is harmless because "re-rate what the ruling reaches" still bounds the step. Round 4's record, "item 26 now checks that first", is history and still true. | holds | L11164-11165, L11195-11199 |
| 3 | "canopy's manual, which §6.3 already counts" | §6.3 says only "breaks a documented behaviour" (plan :357-360). The ledger has rated findings P1 on the manual under it: L9066 (a replay-controls finding), F-057 (L9122) and F-064 (L10073). F-065's Severity bullet presupposes it (L10133). | holds (by precedent) | plan; L-refs |
| 4 | Step 6's quote and its lines | "6. Use the API response shown in the status alert to confirm the edit." It is under "### Network Editor Tab", **Workflow**, at `3411673c`:387, `28da69f8^` (`58d72c12`):424 and `60ae1870`:465. Also at `c7876f5a`:465 and `359e1bf7^`/`359e1bf7`:424. | MATCH | `$S/canopy_manual.py` |
| 5 | "misreports a successful append"; "the one surface…"; P2 as cosmetic | F-013's header (L3848-3850), the live capture (L4081-4087), and "Cosmetic only… the one surface an operator has for confirming a blind mutation" (L3860-3861) | MATCH | ledger |
| 6 | canopy#532 merged 2026-08-28 as `359e1bf7`, awaits a live re-drive | gh GET: merged 2026-08-28T04:16:14Z, merge sha `359e1bf7…`, base main, title names F-CANOPY-013. Phase 4's status correction says every wave entry still owes its re-drive (L6152-6155), and no later Network Editor re-drive exists. | MATCH | `gh api` GET |
| 7 | Credits on the F-013 bullet | The note's reason, "promises no message text", is Lane 11-R4A's (its F1 and could-not-check). Lane 11-R3A named F-013 (round-3 report :102). The manual came from Lanes 11-R5A F1 and 11-R5B F1. | MATCH | report files |
| 8 | The owner's question after round 5 | The Unresolved bullet (L10933) now matches Phase 10 (L10316) word for word, bar the quotes around "documented". F-065's header and Severity bullet and the Matrix keep "shipped"; both CHANGELOG entries, `[0.6.0]` 2026-07-28 and `[0.8.0]` 2026-09-11, are released. Under neither / first limb only / both, F-065 is P2/P1/P1 and F-068 is P2/P2/P1 in every rating statement (L9856, L10087, L10133-10136, L10316, L10570, L10715, L10761-10772, L10893-10895, L10933-10937, L10960-10963, L11137-11141). That gives 5/18, 6/17 and 7/16. | holds | grep; canopy CHANGELOG |
| 9 | Triage 79/53/1/2/23, 7 P1, 16 P2 | Identical, and its output is unchanged from `684d70bc`. F-012, F-013, F-018 and F-057 are open P2s. | MATCH | `e2e_finding_triage.py --note` |
| 10 | Round 4's record: Verdicts | Lane 11-R4B F1's own words: "The action: the question put to the owner. A number: F-068's rating and the 6/17 count, under one ruling." | MATCH | round-4 report |
| 11 | Round 4's record: first-limb bullet | At `684d70bc` the Unresolved bullet and the Matrix read "a shipped CHANGELOG or design-plan promise", as F-065's header does. The second limb is phrased as a condition ("if it does"). | holds; round 3's record now disagrees (F1) | L11064-11067 vs L11006 |
| 12 | Round 4's record: trigger-lag credit | T-mode's unrecorded effect is from Lane 11-R4B F3. The README's split is from Lane 11-R4A F5 and Lane 11-R4B F3. | MATCH | round-4 report |
| 13 | Round 4's record: Slips | Lane 11-R4B's archiver and fix-pass caches (10:59:24.05Z) fall inside its `codeql_check.py` run without `-B` (10:59:23.946Z), which loads both files by path (`r4_b_codeql_check.py:43-44`). The release-trace cache credited to Lane 11-R4A does not fit Lane 11-R4A's own run. | MISMATCH (F3) | mtimes; agent transcripts |
| 14 | Round-5 record vs the verbatim reports | Both reports are the lanes' last messages verbatim (13,181 and 12,674 chars). Verdicts, the shared MINOR, the replays, the 7 probes, and "Neither lane reported one" all match. Their transcripts show all 21 and 12 `python3` runs with `-B`, and no author-printing git format. | MATCH except F2 | transcripts (flags only) |
| 15 | CodeQL third run: 5 edits in 4 files, nothing computed changes | I ran the archiver with `--round 5` on the lanes' scratch sources, then `--round r5`. All 7 files are byte-identical to `da08f639`. The prescreen gives 5 before (4 unused imports, 1 open) and 0 after. The 4 edited files are AST-equivalent once the `with` block is undone and the dropped `sys`/`re` imports are removed; those names are never read. The other 3 files are untouched. | MATCH | `$S/cq_check.py` |
| 16 | The prescreen reports nothing on the branch | 0 alerts in all 118 `.py` files added or changed from merge-base `200c1393` to `da08f639`. It fires 5 times on the pre-fix r5 probes, and `--known-answer` passes. | MATCH | `$S/prescreen_branch.py` |
| 17 | Fix pass docstring vs code | The `fh` guard runs only for files with an `open` edit. Every check fires before any write. Each anchor must occur once, and every file must compile and pass the prescreen. | holds | `…codeql_fixes.py:24`, `:183` |
| 18 | The archiver's round-5 exclusions | Lane 11-R5A's `nep_28da69f8p.py` hashes equal canopy's `network_editor_panel.py` at `28da69f8^`. Its shell runners (`cq_replay.sh`, `cq_stage.sh`, `replay.sh`) are not archived. | holds | sha256 |

**FINDINGS**

1. **NIT: round 3's record still calls round 4's wording Phase 10's, which round 4's amended record and round 5's record now deny.**
   - **Quoted:**
     - L11006: "The first limb was put as a promise of something a user sees (round 4 restored Phase 10's wording)".
     - Against L11064-11066: "worded as F-CANOPY-065's header and its Severity bullet word it, "shipped" included (… round 5 quotes Phase 10's own wording …)".
     - And L11116: "its first-limb bullet no longer calls the shipped wording Phase 10's".
   - **Evidence:** Both round-5 lanes quoted this parenthetical in the same NIT (Lane 11-R5A F3, Lane 11-R5B F2). The pass fixed L10933 and L11064 but left this one.
   - **Fix:** "(round 4 restored Phase 10's question in F-CANOPY-065's words, round 5 Phase 10's own)".
   - **Changes a number, disposition or action?** No.

2. **NIT: round 5's record places one change in the wrong section and credits two changes too narrowly or too widely.**
   - **Quoted (L11116-11119):** "round 4's record: … calls the second limb a condition, not an exception (Lanes 11-R5A and 11-R5B); … its credits for T-mode's unrecorded effect and for F-CANOPY-013's reason now name the lanes that raised them; … (Lane 11-R5A)".
   - **Evidence:**
     - Round 4's record carries no credit for F-013's reason; it says only "F-CANOPY-013 is recorded as unsettled" (L11062). The diff touches round 4's record only at L11055-11058, L11064-11067, L11070-11071 and L11089-11090.
     - That credit was changed in the Matrix bullet (L11159-11160), and Lane 11-R5B F1 asked for it too ("credit its reason to Lane 11-R4A").
     - Only Lane 11-R5B raised "exception" (its F2). Lane 11-R5A F3 concerned "shipped" only.
   - **Fix:**
     - Credit the F-013 reason in the record's first bullet (the Matrix), to Lanes 11-R5A and 11-R5B.
     - Credit "a condition" to Lane 11-R5B alone.
   - **Changes a number, disposition or action?** No.

3. **NIT: round 4's Slips, as amended, credit Lane 11-R4B's bytecode write to Lane 11-R4A and undercount Lane 11-R4B's.**
   - **Quoted (L11087-11090):** "Lane 11-R4A ran the repo's rederive script once without `-B`, which wrote one git-ignored bytecode file … Lane 11-R4B ran … one probe without `-B`, which wrote two git-ignored bytecode files". Also L11119: "its Slips record Lane 11-R4B's two bytecode files".
   - **Evidence:**
     - `util/ad-hoc/__pycache__/2026-10-05_f058_census_v2_release_trace.cpython-314.pyc` has mtime 2026-10-08T10:51:23.390Z. Its source has mtime 10:41:27Z, so the 10-05 cache was stale.
     - Lane 11-R4B ran `util/ad-hoc/2026-10-08_phase11_round3_rederive.py` without `-B` from 10:51:23.284Z to 10:51:23.448Z. That script loads the trace by path (`:46`).
     - Lane 11-R4A's own run without `-B` came at 10:52:27.272Z, 64 s later, when the cache was already current, so it wrote nothing. No other tool call by any agent in this worktree falls in that window.
     - Lane 11-R4A's report misread 05:51:23 CDT as its own run, and Lane 11-R5A's row 18 accepted it.
     - So Lane 11-R4B wrote three caches, all in `util/ad-hoc/__pycache__/`, and Lane 11-R4A wrote none. Lane 11-R4B ran all 22 of its `python3` runs without `-B`, and Lane 11-R4A 15 of its 23.
   - **Fix:** "Lane 11-R4B ran its Python without `-B`; two runs wrote three git-ignored bytecode files into the worktree, one by the rederive script (10:51:23Z, the file Lane 11-R4A's report claimed; Lane 11-R4A's own run came 64 s later and wrote nothing) and two by one probe (10:59:24Z)." Change "two" to "three" at L11119.
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Whether canopy's manual makes F-012, F-013 or any other open finding P1. That is item 26's work, and canopy#532 and #535 have had no live re-drive.
- What CodeQL itself will report on the PR. The prescreen only predicts it, though it fires and its known answer passes.
- Whether the lanes' scratch sources changed before the archiver ran. They reproduce the archive now.
- The bytecode attribution rests on file mtimes against transcript timestamps, not on observing the write itself.

**SECRETS/PII:**
- **Printed, requested or sent:** no environment values, tokens, credential files or e-mail addresses.
- **juniper-ml git**, through the worktree only: `log --format='%h %s'`, `status --short`, `rev-parse`, `merge-base`, `diff` (including `--name-status`, `--name-only` and a working-tree `--stat`), `show <rev>:<path>`, `ls-tree` and `check-ignore`.
- **canopy git**, from its object store with no fetch: `cat-file -t`, `rev-parse`, `ls-tree` and `show <rev>:<path>`.
- **`gh api`:** one GET of canopy#532, selecting merge fields and the title.
- **Transcripts:** I printed only timestamps, flags, script basenames, tool-call descriptions, lengths and match flags.
- **Python and bytecode:** every Python run used `-B`, and I checked that no bytecode was written into the worktree.
- **Scratch:** I read the round-5 lanes' scratch directories read-only and did not open Lane 11-R6B's.
- **Live systems:** I touched no port, service or browser.
- **Guard refusals:** the shell guard refused two compound commands, which I split.
- No slip.

---

## Lane 11-R6B (adversarial, on round 5's correction pass)

*agent `a710bd76188e5cd07` · round 1 · last-assistant-text (not resumed) · 10682 chars*

**Lane 11-R6B** (adversarial, on round 5's correction pass)

**VERDICT: SOUND-WITH-FIXES.** Round 5's pass replays byte for byte. Item 26 and the Matrix now say the same thing. Every ruling gives one rating each for F-CANOPY-065 and F-CANOPY-068, and the counts and the triage hold. The CodeQL third run changes nothing a probe computes. I found three NITs, none of which changes a number, a disposition or an action:
- the pass left round 3's record contradicting round 4's record as amended;
- the round-5 record puts a credit change in the wrong place;
- the round-4 Slips bullet, which round 5 rewrote, names the wrong lane for a bytecode file.

**TABLE** (L… is the ledger at `da08f639`)

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | The pass on `684d70bc` gives `da08f639`, with "9 substitutions" | I replayed it in scratch: 9 substitutions, 914,499 → 918,968 chars. The result's sha256 (`6ecdd1ce…`) equals both the commit and the worktree. | MATCH, no hand edit | `cmp`, sha256 |
| 2 | Item 26 and the Matrix agree: the manual first for every open finding, F-012 and F-013 first; then, with the ruling, the CHANGELOG and design plans | Both say this (L11164-11165, L11195-11199). The Matrix leaves out the promise/description test but does not contradict it. Nothing else in Phase 11 limits the manual check to F-012. L11062's "item 26 now checks that first" is round 4's history and is still true. | holds | every "manual" in Phase 11 |
| 3 | "canopy's manual, which §6.3 already counts" | §6.3 names no document, but the ledger already rates P1 on the manual (F-CANOPY-056 at L9066; L10317) | holds (by ledger precedent) | plan :357-360 |
| 4 | Step 6 at `3411673c` `:387`, `28da69f8^` `:424`, `60ae1870` `:465` | Text exact at all three, and also at `:424` at `359e1bf7^`. `28da69f8^` (`58d72c12`) already contains canopy#532, but the text is the same before the fix. | MATCH | canopy object store |
| 5 | "misreports a successful append"; the entry's quote; P2 because cosmetic | The entry shows "index None (now None hidden units)" on an append that "fully succeeded", and says "Cosmetic only … the one surface an operator has for confirming a blind mutation" (L3848-3866) | MATCH | ledger |
| 6 | canopy#532 merged 2026-08-28 as `359e1bf7`, and awaits a live re-drive | Merged 2026-08-28T04:16:14Z, merge SHA `359e1bf7`, base `main`, title names F-013. The re-drive is owed at L6154 and L6213; I found no later re-drive. | MATCH | `gh api` GET |
| 7 | Credits: Lane 11-R4A for the note's reason (Lane 11-R3A named it); Lanes 11-R5A and 11-R5B for the manual | Round-4 reports `:58` and `:91`; round-3 reports `:102`; both lanes' round-5 F1. The CAN-015g/h note gives no success-message text. | MATCH | reports; note |
| 8 | Item 4: one rating per ruling, and the counts | Under neither / first limb only / both: F-065 is P2/P1/P1 and F-068 is P2/P2/P1 at L9835, L9856, L10087, L10133-10136, L10316, L10544, L10570, L10715, L10761-10772, L10893, L10933-10937, L10960 and L11137-11141. "shipped" changes nothing: the 0.6.0 toast text is at `v0.6.0:CHANGELOG.md:205`, and canopy#624 is an ancestor of `v0.8.0`. The counts are 5/18, 6/17 and 7/16. | holds | grep; canopy tags |
| 9 | Triage gives 79/53/1/2/23, 7 open P1, 16 open P2 | Identical | MATCH | `e2e_finding_triage.py --note` |
| 10 | "cannot keep to what that entry describes"; the `[0.8.0]` text annotated as a description | `CHANGELOG.md:1221-1225` at `60ae1870` | holds | canopy |
| 11 | Round 4's first-limb bullet ("shipped" included; a condition, not an exception) | True of round 4's text, but L11006 still says "(round 4 restored Phase 10's wording)" | breaks (F1) | L11006, L11064-11066 |
| 12 | Round 4's amended Verdicts and trigger-lag credit split | Lane 11-R4B's F1 claims an action plus F-068's rating and 6/17 under one ruling (`:161`). Lane 11-R4B's F3 raised both T-mode and the README; Lane 11-R4A's F5 raised only the README. | MATCH | round-4 reports |
| 13 | Round 4's Slips as amended | The release-trace cache was written during Lane 11-R4B's run of the rederive script, not Lane 11-R4A's (details in F3) | MISMATCH (F3) | cache headers; transcripts |
| 14 | Round-5 record: lanes, brief, verbatim reports, verdicts, what both found, 7 probes, 5 alerts, no slips | Both archived reports equal each lane's last assistant text (13,181 and 12,674 chars). Both round-5 lanes ran every Python command with `-B`. | MATCH | transcripts |
| 15 | Round-5 record: "What round 5 changed" | All 9 substitutions located. The F-013 reason credit, however, changed in the Matrix, not in round 4's record, and two credits are wrong. | breaks (F2) | `git diff 684d70bc da08f639` |
| 16 | CodeQL third run: 5 edits in 4 files change nothing computed; prescreen is clean on the branch; the docstring is true | I replayed the archiver (`--round 5`) and then the fix pass (`--round r5`): all 7 probes are byte-identical to the commit. Before the fix, 5 alerts in 4 files, all Lane 11-R5A's; after, 0. Each edited probe is AST-equal to its pre-fix form once the edits are undone, and no dropped name is read; a one-token mutation is caught. Prescreen: 0 alerts in all 118 `.py` files changed since `200c1393`, and `--known-answer` passes. The docstring matches the code at `:186-203`. | MATCH | scratch replica |

**FINDINGS**

1. **NIT: round 3's record still says round 4 restored Phase 10's wording, which the amended round-4 record now denies.**
   - **Quoted:**
     - L11006: "(round 4 restored Phase 10's wording)".
     - L11064-11066: "worded as F-CANOPY-065's header and its Severity bullet word it, "shipped" included … round 5 quotes Phase 10's own wording".
     - L11116: "no longer calls the shipped wording Phase 10's".
   - **Evidence:** Both round-5 lanes quoted this same line (at `684d70bc`) in their NITs (Lane 11-R5A's F3, Lane 11-R5B's F2). The pass fixed only the round-4 bullet. Round 4's pass wrote the round-3 annotation (`…round4_corrections.py:153`). Phase 10's question (L10316) has no "shipped".
   - **Fix:** "(round 4 restored Phase 10's question in F-CANOPY-065's wording, "shipped" included; round 5 its own words)".
   - **Changes a number, disposition or action?** No.

2. **NIT: the round-5 record puts a credit change in the wrong place, and two of its credits name the wrong lanes.**
   - **Quoted (L11116-11119):** "round 4's record: … a condition, not an exception (Lanes 11-R5A and 11-R5B); … its credits for … F-CANOPY-013's reason now name the lanes that raised them; … (Lane 11-R5A)".
   - **Evidence:**
     - Round 4's record changed only in its first-limb bullet, Verdicts, trigger-lag credit and Slips. Its one F-013 mention (L11062) is unchanged and gives no reason.
     - The credit actually changed in the Matrix: "(Lane 11-R3A)" became "(Lane 11-R4A; Lane 11-R3A had named it)" (L11159-11160).
     - Lane 11-R5B's F1 fix also asked for that credit, but only Lane 11-R5A is named.
     - "condition, not an exception" came from Lane 11-R5B's F2 alone; Lane 11-R5A's F3 does not raise it.
   - **Fix:** Move the F-013 credit into the record's first bullet, credited to Lanes 11-R5A and 11-R5B. Credit the "condition" wording to Lane 11-R5B alone.
   - **Changes a number, disposition or action?** No.

3. **NIT: round 4's Slips, as round 5 amended them, credit a bytecode file to the wrong lane, and "one probe" is false.**
   - **Quoted (L11087-11090):** "Lane 11-R4A ran the repo's rederive script once without `-B`, which wrote one git-ignored bytecode file … Lane 11-R4B ran … one probe without `-B`, which wrote two git-ignored bytecode files … (Lane 11-R5A)."
   - **Evidence:**
     - `util/ad-hoc/__pycache__/2026-10-05_f058_census_v2_release_trace.cpython-314.pyc` was written at 10:51:23.390Z. It was compiled from the 10:41:27Z source (24,066 bytes) and is still valid for it.
     - Lane 11-R4B ran `python3 util/ad-hoc/2026-10-08_phase11_round3_rederive.py …` without `-B` at 10:51:23.284Z; the result came back at .448Z. The rederive script loads the trace by path (`:39-46`).
     - Lane 11-R4A's identical command ran 64 s later (10:52:27Z) and found a valid cache, so it wrote nothing. Its report dates the file "at 05:51:23", which is the cache's own mtime, not when it ran.
     - The orchestrator made no tool call between 10:43:28Z and 11:12Z.
     - Lane 11-R4B ran all 18 of its `python3 <script>.py` commands without `-B`. Two of them wrote three files: the rederive script one, and `codeql_check.py` (10:59:23.9Z) the other two.
     - Round 5 took this slip from Lane 11-R5A's report alone, without re-deriving it (§5.2).
   - **Fix:** "Lane 11-R4A ran Python without `-B` 11 times before 10:55Z, the rederive script among them, and wrote nothing into the worktree. The file it reported came 64 s earlier, from Lane 11-R4B's run of the same script. Lane 11-R4B ran every Python script without `-B`; two runs wrote three git-ignored bytecode files. No tracked file changed."
   - **Changes a number, disposition or action?** No; it corrects the Slips record only.

**WHAT YOU COULD NOT CHECK**
- Whether the manual makes F-012, F-013 or any other open finding P1. That is item 26's work, and I assessed no rating.
- Whether canopy#532 and #535 fix their findings live. No re-drive was possible.
- What CodeQL itself will report on the PR. The prescreen only predicts it.
- Python runs in the transcripts that do not take the form `python3 <file>.py`.
- Why Lane 11-R4A's 10:52:27Z run exited non-zero. I printed only flags and lengths.

**SECRETS/PII:**
- No environment values, tokens, credential files or e-mail addresses were printed, requested or sent.
- **juniper-ml git**, through the worktree only: `status --short`, `log --format='%h %s'`, `rev-parse`, `diff`, `show <rev>:<path>`, `ls-tree --name-only`, `merge-base` and `check-ignore`.
- **canopy git**, from its object store with no fetch: `rev-parse`, `show <rev>:<path>`, `merge-base --is-ancestor` and `tag --list`.
- **`gh api`:** one GET of canopy#532, selecting number, merge time, merge SHA, base, title and state.
- **Transcripts:** from the round-4 and round-5 lane transcripts and the orchestrator's I printed only timestamps, tool-id suffixes, flags, lengths and script paths, plus 160 characters of three python commands with e-mail shapes masked (none found).
- **Other lanes' scratch:** I read the round-5 lanes' directories read-only, to replay the archiver.
- **Python and scratch:** every Python run used `-B`. No bytecode was written into the worktree and no tracked file changed. All scratch work is in my `mktemp -d` directory, `…/scratchpad/r6b.lTWETu`.
- I touched no port, service or browser. No slips.

---
