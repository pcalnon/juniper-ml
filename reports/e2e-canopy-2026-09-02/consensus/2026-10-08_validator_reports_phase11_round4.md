<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 4 — validator reports (verbatim)

Round 4 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen adcba49f (round 3's pass applied to 7af6a381), 2026-10-08. Two lanes from one brief, reports/e2e-canopy-2026-09-02/drafts/lane11R4_phase11_ledger_brief.md, briefed on round 3's corrections only. Each report below is the lane's final message, verbatim (each lane ran once, so the archiver's round-1 mode applies). The orchestrator's dispositions are in the ledger's Phase 11 Consensus record; the correction pass is util/ad-hoc/2026-10-08_phase11_ledger_round4_corrections.py.

## Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections)

*agent `a787c1b146b28dbbe` · round 1 · last-assistant-text (not resumed) · 14821 chars*

**Lane 11-R4A** (measurement re-creation, artifact-first, on round 3's corrections)

**VERDICT: SOUND-WITH-FIXES.** Round 3's pass replays byte for byte on all four files, with no hand edit. Every number it introduced comes out the same from my own reader and from the repo's rederive script. The readers' output did not change. The CodeQL edits change nothing any probe computes, and the CodeQL fix pass also replays exactly. One MINOR finding changes an action: the ruling's reach leaves out F-CANOPY-012, which Lane 11-R3A's report had named. Four NITs change nothing.

Names used below:
- **L** is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `adcba49f`.
- **R** is `reports/e2e-canopy-2026-09-02/f058-census-v2/README.md`.
- **N** is `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`.
- **R3** is `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md`.
- **$S** is my `mktemp -d` directory, `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11R4A.mG5yhk`.
- My reader, `$S/myreader.py`, is written from the shim's JavaScript only. It walks `raw.lane` in push order (a record whose `before` equals the current state is a change; any other record is a re-log) and folds `raw.req` into one record per request.

**TABLE** (values are "first run ; second run")

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | Round 3's pass on the four `7af6a381` files gives `adcba49f` | All four identical (sha256 `ad1aca79…`, `ee3221a9…`, `4466f472…`, `4246182f…`). It printed "18 substitutions … README: 1; readers: 3". `--check` wrote nothing, and a second run refuses ("not the round-3 freeze"). | MATCH, no hand edit | `$S/replay_check.py` |
| 2 | Triage: 79/53/1/2/23, 7 open P1, 16 open P2; F-065 and F-068 read as P1 | Identical at `adcba49f` and at `7af6a381`. `_PRI_RE` takes the first P-token, "P1 if …". | MATCH | `e2e_finding_triage.py --note` |
| 3 | The two limbs: F-068's header, the Summary and the Rating lead give limb 2; "Unresolved" and the Matrix give limb 1 as a promise "of something a user sees"; F-065's header names the design plan | All as stated, and every rating comes out the same under any ruling. But Phase 10's record (L:10316) and F-065's header and Severity bullet give limb 1 without the qualifier. L:10930 attributes the qualified form to "Phase 10's question". L:10724-10728 and item 0 (L:11073) still call F-068's CHANGELOG text a "promise". | holds; NIT F2 | L |
| 4 | "Moving those two alone": 7/16, 6/17, 5/18 | Arithmetic is right | MATCH | triage |
| 5 | F-057 through N | "Implemented" (N:3), the quoted promise (N:18-19) and "every CAN-015g item has merged to `main`" (N:47) are all there. cascor#187 merged into `feature/can-015g-2-replay-weight-cache` and #190 into `…-v2` (gh GET), so g-3 never reached `main`. The manual (`docs/USER_MANUAL.md:765-766`) and the FAQ's status note disclaim the stream: absent in `f2147403^1`, present in `f2147403` (canopy#684). | MATCH | gh; canopy object store |
| 6 | F-018 through canopy's 0.6.0 toast entry, "the entry F-CANOPY-065 rests on"; canopy#533 merged 2026-08-28, re-drive owed | The N5 entry sits under `[0.6.0] - 2026-07-28` (`CHANGELOG.md:2023-2045` at `60ae1870`) and is the text F-065 quotes. #533 merged 2026-08-28T05:09:29Z. L:6154 owes the re-drive. | MATCH | gh; canopy |
| 7 | "No other open finding has been checked … two open P2s are already known to be within reach"; item 26: "Start with F-CANOPY-057 and F-CANOPY-018" | Of the other open entries, only F-060 cites canopy's CHANGELOG, and only for a fact. But Lane 11-R3A's report names F-012 and F-013 as unsettled against N's CAN-015h half, and F-012 contradicts N:627. | omits (F1) | L; N; R3:102 |
| 8 | F-058's trigger bullet: the 8 trigger-started evictions came 1.2–2.4 s after the trigger; the 21 after a late release came 1.4–2.6 s after it | The 8 (7 fires and the gate write at 7,253): 1,214–2,392 ms from the fire or gate record, or 1,214–2,391 ms from the lane change. The 21: 1,422–2,553 ms, each after its evicted predecessor's eviction; four are above 2.4 s (2,444, 2,452, 2,552 and 2,553). The repo's rederive script gives the same figures. | MATCH | `$S/myreader.py`; `…round3_rederive.py` |
| 9 | Events bullet: "each 1.4–2.6 s after the late release"; F-068's Effect: "each 1.4–2.4 s after the fire" | 1,422–2,553 ms; the 7 evicting fires 1,418–2,392 ms | MATCH | same |
| 10 | Trigger lag: T-gate 1.3–1.4 s; T-mode's next request 2.1–2.5 s; T-tab's clicks 0.7–1.0 s and 2.3–2.9 s; the wait 1.6–1.9 s; click to gate write 0.3–1.9 s; overall 1.3–4.2 s; flight age at firing 1.6–2.9 s | 1,336 ; 1,367. 2,148 ; 2,503. 993, 2,936 ; 708, 2,313. 1,943 ; 1,605. 311, 460 ; 873, 1,890. 1,336–4,203. 1,633–2,914. | MATCH | the transcripts' `triggers` and `raw` |
| 11 | "Stamped after the click's own handling"; a trigger sent from Python lands "at most the 0.7–1.0 s" later | `CLICK_TAB` returns `Date.now()` after `t.click()` (`…_live.py:127-128`). `t_ms` is stamped inside `OPEN_SINCE` (`:120`), so the interval to the first click holds the round trip plus the click's handling. | holds (an upper bound, one sample per run) | `…_live.py` |
| 12 | R:69-71: the delay is one "the transcript does not split between the driver and the page" | L:10847-10855 does split T-tab's delay in part (each gate write came 0.3–1.9 s after its click had returned in the page) and bounds the driver's share at 0.7–1.0 s | overreaches (NIT F5) | R; L |
| 13 | The readers' output at `adcba49f` against `7af6a381` | The trace's report, its `--self-test` and the replay, on both transcripts: 6 of 6 runs identical in stdout, stderr and exit code. All five self-tests pass; 0 breaks; 0 AMBIGUOUS. | MATCH | `$S/readers_compare.py` |
| 14 | The guard text (L:10823-10827) | With one innermost record dropped, the report exits 2, the replay refuses with exit 2, and `--self-test` exits 0 with PASS. With a disable/enable pair re-typed as non-thunk: 0 breaks, the timeline goes 617 → 615 (610 → 608), and both readers exit 0. The push-order walk equals the type selection: 617 ; 610 changes. | holds | `$S/guard_test.py` |
| 15 | L:11014: "Only the trace's report exits 2 on an alternation break" | The replay also exits 2 | breaks as worded (NIT F3) | same |
| 16 | Round-3 record against R3 | Verdicts, attributions, "no slips" and the 19 archived probes (11 + 8) all match. On the interruption, I printed timestamps only. Both transcripts start 2026-10-05T23:07Z, carry a usage-limit message naming "weekly" at 23:18Z and 23:20Z, then show a 58.9 h gap, with the resume at 2026-10-08T10:13Z. The final messages (15,035 and 15,650 chars) are verbatim in R3. The record leaves out Lane 11-R3A's F-012/F-013 lead. | MATCH except F1 | `$S/lane_interrupt.py` |
| 17 | The CodeQL edits change nothing computed; "51 edits in 44 probes" | The 37 round-1/2 probes are AST-equivalent to `7af6a381` once the `with` wrapping is undone. None of the 16 dropped names (12 imports, 3 locals, 1 global) is read anywhere. The 7 edited round-3 probes are AST-equivalent to the lanes' scratch originals, and the other 12 are byte-identical to them. Replaying the fix pass on `7af6a381` plus the archiver's `--round 3` output makes all 76 probes byte-identical to `adcba49f`. The comparator catches a mutation. | MATCH | `$S/ast_compare.py`, `r3_probe_compare.py`, `codeql_replay.py` |
| 18 | Side effect of the edits | `…r3_b_verify_archive_r2.py` reads the live tree and now prints "3 of 16 match" (it printed 16). `…r3_a_probe_archive_check.py` pins `7af6a381` and still prints 16. | holds; no ledger claim rests on re-running either | run with `-B` |
| 19 | The prescreen reproduces #2157's 20 threads, finds nothing in Phase 10's 33 scripts, and nothing in this phase's | `--known-answer` passes. Its predicted file, rule and line equal the 20 CodeQL threads from a gh GET, with every line 2 higher because of the amended header. 0 alerts on the 33 (and all 35) `.py` files of `200c1393`, and 0 on all 91 `.py` files this branch added or changed. It does fire: 44 alerts on the round-1/2 probes at `7af6a381`, 7 on the round-3 originals. | MATCH | `$S/prescreen_sweep.py`, `ka_lines.py` |
| 20 | The rederive script's docstring cites the round-3 reports | `…/consensus/2026-10-05_validator_reports_phase11_round3.md` does not exist | MISMATCH (NIT F4) | `…round3_rederive.py:13` |

**FINDINGS**

1. **MINOR: the ruling's reach leaves out F-CANOPY-012, which Lane 11-R3A's report named.**
   - **Quoted (L):**
     - L:11050-11052: "No other open finding has been checked against canopy's CHANGELOG or the design plans, and two open P2s are already known to be within reach of the first limb".
     - Item 26 (L:11091-11092): "Start with F-CANOPY-057 and F-CANOPY-018".
     - The record (L:11004-11007): "… and no other open finding has been checked".
   - **Evidence:**
     - Lane 11-R3A's "what you could not check" (R3:102) reads: "F-012 and F-013 against that note's CAN-015h half are not settled." Lane 11-R3B's could-not-check item, F-018, became "known to be within reach"; Lane 11-R3A's two were dropped.
     - N is marked "Implemented", with h-5 merged as canopy#224. It promises an "Output-layer 'Patch weights' expander as a separate card" (N:627).
     - F-012 (L:3833-3835) says `output_weights`, the panel's default target, "is structurally impossible to patch from the UI". That puts it on the same footing as F-057, through the same note. F-013's footing is weaker, since N promises no message text.
     - **Pre-existing, not round 3's:** canopy's own manual has listed `output_weights` under Patch Weights, entered as "comma-, semicolon-, or newline-separated floats", since before F-012 was filed (`docs/USER_MANUAL.md:405-414` at `28da69f8^1`; `:448-455` at `60ae1870`). That is the kind of text that made F-057 and F-064 P1. Item 26 checks only CHANGELOGs and design plans, so it would not catch this.
     - F-012's fix, canopy#535, merged on 2026-08-28T04:54:55Z and awaits a re-drive, as F-018's does.
   - **Fix:** Name F-012 beside F-057 and F-018 in the Matrix bullet, in item 26 and in the record, and record Lane 11-R3A's unsettled F-013. Have item 26 also check F-012 against canopy's manual.
   - **Changes a number, disposition or action?** Action: yes, the reach and item 26's start list (round 3's own record counts the reach as an action). Number: no, as round 3 scopes its counts. F-012's rating would change only if the pre-existing manual point is upheld.

2. **NIT: limb 1 is quoted as "Phase 10's question" with a qualifier Phase 10's question does not have.**
   - **Quoted:**
     - L:10930-10931: "Phase 10's question, whether a shipped CHANGELOG's or a design plan's promise of something a user sees counts".
     - The Rating lead (L:10761): "its first limb, from Phase 10's Consensus record".
     - Phase 10's own wording (L:10316): "whether a CHANGELOG or design-plan promise counts as 'documented'".
   - **Evidence:** F-068's "Its own contract" bullet still says the CHANGELOG "makes the promise to its readers … cannot keep that promise" (L:10724-10728), and item 0 says "`[0.8.0]` promise" (L:11073). Read literally, Phase 10's wording would therefore reach F-068 as well, so "carried everywhere" (L:11000) overstates. Every rating still comes out the same if the owner answers Phase 11's statement of the question.
   - **Fix:** Write "Phase 10's question, limited since round 3 to a promise of something a user sees". Optionally write "description" for "promise" at L:10724-10728 and L:11073.
   - **Changes a number, disposition or action?** No.

3. **NIT: the record says only the trace's report exits 2.**
   - **Quoted (L:11014):** "Only the trace's report exits 2 on an alternation break".
   - **Evidence:** The replay exits 2 too. The intended contrast is the report against `--self-test`, which L:10823-10824 states correctly.
   - **Fix:** "Of the trace's two modes, only the report exits 2".
   - **Changes a number, disposition or action?** No.

4. **NIT: the rederive script cites a file that does not exist.**
   - **Evidence:** `util/ad-hoc/2026-10-08_phase11_round3_rederive.py:13` cites `…/consensus/2026-10-05_validator_reports_phase11_round3.md`. The file is `2026-10-08_validator_reports_phase11_round3.md`. The same docstring calls the eviction the moment the next request "entered", where the ledger says "made".
   - **Changes a number, disposition or action?** No.

5. **NIT: the README says the transcript does not split the trigger delay.**
   - **Quoted (R:69-71):** "a delay the transcript does not split between the driver and the page".
   - **Evidence:** L:10847-10855 splits T-tab's delay in part (each gate write came 0.3–1.9 s after its click had returned in the page) and bounds the driver's share at 0.7–1.0 s.
   - **Fix:** "a delay the transcript splits only for T-tab, and only in part".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Whether §6.3 makes F-012 P1 through canopy's manual, and whether canopy#535 fixed it on `main`. No re-drive was possible, and the question predates round 3.
- F-013 against N's CAN-015h half. N promises no message text, so it is not settled.
- The full sweep that item 26 asks for.
- What CodeQL itself will report. The prescreen is only a predictor, though an adequate one: it fires 51 times on the probes before the edits and matches #2157.
- The wording of the resume messages. By rule I printed no transcript text, only timestamps, counts and match flags.
- Whether a trigger fired from the page escapes the page's own queue. I drove no browser.

**SECRETS/PII:**
- No environment values, tokens, credentials or e-mail addresses were printed, requested or sent.
- Git in juniper-ml, through the worktree only: `log --format='%h %s'`, `diff`, `show <rev>:<path>`, `ls-tree`, `rev-parse` and `status --short`.
- Git in canopy's object store: `cat-file -t`, `show <rev>:<path>`, `merge-base --is-ancestor` and `diff --name-only`. No fetch, no `--stat`, no author or body format.
- `gh api` was used for GETs only, with `--jq` selecting merge dates, base refs, titles, and the CodeQL comments' path, line and first line.
- I read the two round-3 lane transcripts but printed only timestamps, counts and match flags.
- I touched no port, service or browser.
- **One slip:** I ran the repo's rederive script without `-B`, and it wrote one git-ignored bytecode file into the worktree, `util/ad-hoc/__pycache__/2026-10-05_f058_census_v2_release_trace.cpython-314.pyc`, at 05:51:23. No tracked file changed, and every later run used `-B`. Two other caches in that directory, written at 05:59:24, were not written by my commands.

---

## Lane 11-R4B (adversarial, on round 3's correction pass)

*agent `abf8c493b595bcdb2` · round 1 · last-assistant-text (not resumed) · 13780 chars*

**Lane 11-R4B** (adversarial, on round 3's correction pass)

**VERDICT: SOUND-WITH-FIXES.** Round 3's pass replays byte for byte, with no hand edit. Every number it added or changed re-derives from my own reader. The readers behave exactly as at `7af6a381`, and the CodeQL edits change nothing any probe computes. The pass still left the owner's question stated two ways, and it left one known open P2 out of the reach list. Both of those change an action, so §4 requires round 5.

**TABLE.** Line numbers (L…) are in `…E2E-VALIDATION-EVIDENCE.md` at `adcba49f`. Values are given as "T1 ; T2". $S is `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/r4b.5mnsCd`.

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | The pass on the 4 files at `7af6a381` gives `adcba49f` | All 4 identical. The pass printed "18 substitutions … README: 1; readers: 3" | MATCH, no hand edit | `$S/replay.py` |
| 2 | Triage: 79/53/1/2/23, 7 P1, 16 P2; F-065 and F-068 read as P1 | Identical | MATCH | `e2e_finding_triage.py --note` |
| 3 | Limb 2 in F-068's header, the Summary and the Rating lead | All three say "a CHANGELOG's description of an internal mechanism" | holds | L10570, L10714, L10760 |
| 4 | Limb 1 stated one way everywhere | F-065's header and Severity bullet, and Phase 10's question, omit "of something a user sees"; Phase 11's Unresolved and Matrix add it. F-068's own entry still calls its text a "promise" | breaks | F1 |
| 5 | "Moving those two alone": 7/16, 6/17, 5/18 | Arithmetic correct | MATCH | — |
| 6 | F-057's reach | Status "Implemented (h-6 in review)" (:3); the quote (:17-19); g-3 recorded as merged (:47, :88); F-057's History; canopy manual :765 and FAQ :24 at `c7876f5a`; `f2147403` is an ancestor | holds | design note; canopy object store |
| 7 | F-018's reach; canopy#533 merged 2026-08-28 | The 0.6.0 N5 toast entry is the one F-065 cites (`:1975-1980` at `1b2dd438`). canopy#533 merged at 2026-08-28T05:09:29Z (`6b55399d`) | holds | `gh api` GET; L6148-6155 |
| 8 | "No other open finding has been checked"; "two open P2s … known" | Lane 11-R3A named F-012 and F-013 against the same note; F-012 is on F-057's footing | overreaches | F2 |
| 9 | Item 26 | Sound and in scope. The g-3 quote is exact. Its start list omits F-012 and F-013 | holds, except F2 | — |
| 10 | Trigger bullet: the 8 trigger-started evictions at 1.2–2.4 s; the 21 after a late release at 1.4–2.6 s | My push-order reader: 1,214–2,391 ms (lane record) or –2,392 (source record). The 21: 1,422–2,553 ms, four above 2.4 s (2,444, 2,452, 2,552, 2,553). The repo's rederive script agrees | MATCH | `$S/myreader.py` |
| 11 | Events bullet: "each 1.4–2.6 s after the late release" | Same 21. Each one's last re-enable is its predecessor's late release (21 of 21) | MATCH | same |
| 12 | F-068's Effect: 7 fires, "each 1.4–2.4 s" | 1,418–2,392 ms | MATCH | same |
| 13 | T-gate 1.3–1.4 s; T-mode's next request 2.1–2.5 s, cause unrecorded | 1,336 ; 1,367 ms. 2,148 ; 2,503 ms. T-mode had no gate write and TOOK was false | MATCH; the lead overreaches (F3) | `$S/triglag.py` |
| 14 | T-tab clicks at 0.7–1.0 s and 2.3–2.9 s; the wait between took 1.6–1.9 s; click to write 0.3–1.9 s; "stamped after the click's own handling" | 993, 2,936 ; 708, 2,313 ms. 1,943 ; 1,605 ms. 311, 460 ; 873, 1,890 ms. `CLICK_TAB` runs the DOM `t.click()` in the page, then reads `Date.now()` | MATCH | live.py; transcripts |
| 15 | "Sent from Python … at most the 0.7–1.0 s" | A valid upper bound on one page→driver→page round trip. The fire stamp is the in-page poll time | holds; attribution in F4 | live.py |
| 16 | README's new sentence | Agrees on 1.3–4.2 s, but says the delay is not split, where the ledger now splits T-tab's | F3 | README:69-71 |
| 17 | Alternation-guard text and item 24 | Break: report exits 2, replay refuses (exit 2), `--self-test` exits 0. A re-typed disable/enable pair: 0 breaks, both readers exit 0. A push-order vs type-selection comparison catches both | holds | `$S/breakmut.py` |
| 18 | Push-order walk equals the type selection | 617 ; 610 changes, identical, 0 breaks, none carried only by a non-thunk record | MATCH | `$S/myreader.py` |
| 19 | Reader outputs at `adcba49f` vs `7af6a381` | Report, `--self-test` and replay on both transcripts: 6 of 6 identical. Code is identical once docstrings are stripped | MATCH | `$S/readers_cmp.py` |
| 20 | Round-3 record vs the verbatim reports | Verdicts, slips and the 19 probes match. Report lengths equal the stated 15,035 / 15,650 chars. Scratch-file times put the work on 10-05 and 10-08. "weekly" appears in no artifact | MATCH except F2 and F4; "weekly" UNTRACEABLE | report file; lane scratch dirs |
| 21 | CodeQL: 51 edits in 44 probes, nothing computed changes | Fix replayed on the probes as they stood before it: 44 of 44 identical to `adcba49f`. The 12 unedited r3 archives equal the archiver's output from the lanes' sources. ASTs are equal after normalising, and no dropped name is ever read | holds | `$S/codeql_check.py` |
| 22 | Prescreen | `--known-answer` passes. juniper-ml#2157 has 20 CodeQL threads (19 not-closed, 1 unused import), matching its table. It reports 0 on Phase 10's 33 scripts and Phase 11's 91 | MATCH | `gh api` GET; prescreen |
| 23 | Round 3's rederive script | Numbers MATCH. Its docstring cites a report file that does not exist | F5 | — |

**FINDINGS**

1. **MINOR: the first limb is still stated two ways, and Phase 11 quotes Phase 10's question in a form Phase 10 never asked.**
   - **Quoted:**
     - F-065's header, rewritten by round 3 (L10087): "(P1 if a shipped CHANGELOG or design-plan promise counts as documented, else P2, the first limb of the owner's question; …". Its Severity bullet (L10133-10135) gives the same condition.
     - Phase 10's question (L10316): "whether a CHANGELOG or design-plan promise counts as "documented" under plan §6.3".
     - Phase 11's Unresolved (L10930-10931): "Phase 10's question, whether a shipped CHANGELOG's or a design plan's promise of something a user sees counts as documented". The Matrix (L11046-11047) says the same.
     - F-068's own entry still calls its CHANGELOG text a promise: "canopy's CHANGELOG makes the promise to its readers … The threshold cannot keep that promise" (L10724-10728). So does item 0: "the shipped CHANGELOG's `[0.8.0]` promise" (L11072-11073).
     - The round-1 record calls "a shipped CHANGELOG promise" "now its second limb" (L10891-10893). The round-3 record says "the two limbs, carried everywhere" (L11000).
   - **Evidence:**
     - Take limb 1 as F-065's header, its Severity bullet and Phase 10 word it. F-068's `[0.8.0]` text, which the ledger itself calls a shipped CHANGELOG promise, meets that condition. Under the Matrix's wording it does not.
     - So for a "yes" to Phase 10's question as asked, the ledger gives F-068 both ways: P1 (7 and 16) by its own "Its own contract", P2 by the Matrix's "F-CANOPY-065 alone, 6 and 17". This is the mechanism of round 3's R3B F1, moved from F-068's header to F-065's.
     - Phase 10 never carries the qualifier "of something a user sees". Round 2's own re-derivation (L10978-10979) records Phase 10's question as naming "CHANGELOG or design-plan promises".
   - **Fix:**
     - State limb 1 once. Either put "of something a user sees" into F-065's header and Severity bullet and add a dated note at Phase 10's Unresolved that Phase 11 narrowed the question, or drop the qualifier and state limb 2 as the explicit exception.
     - In F-068's "Its own contract" and in item 0, call the `[0.8.0]` text a description.
     - In Phase 11's Unresolved, write "narrowed from Phase 10's question".
   - **Changes a number, disposition or action?** Yes. The action: the question put to the owner. A number: F-068's rating and the 6/17 count, under one ruling.

2. **MINOR: the reach list leaves out F-012, which the same design note reaches, and the round-3 record drops Lane 11-R3A's pointer to it.**
   - **Quoted:**
     - Matrix (L11050-11052): "No other open finding has been checked … and two open P2s are already known to be within reach of the first limb".
     - Round-3 record (L11004-11007): "… and F-CANOPY-018 … (named by Lane 11-R3B among what it could not check), and no other open finding has been checked".
     - Item 26 (L11091): "Start with F-CANOPY-057 and F-CANOPY-018".
   - **Evidence:**
     - Lane 11-R3A's report (`…phase11_round3.md:102`) says: "F-012 and F-013 against that note's CAN-015h half are not settled." The record turns Lane 11-R3B's "could not check" item into a known reach and drops Lane 11-R3A's.
     - The CAN-015g/h note is marked "Implemented (h-6 in review)" (:3). It records h-5, the "Network Editor panel + tab", as merged (:104), and specifies an 'Output-layer "Patch weights" expander as a separate card' (:627).
     - F-012, an open P2 (L3833-3835), says `output_weights`, the editor's default patch target, "is structurally impossible to patch from the UI". That is F-057's footing exactly.
     - F-012's fix, canopy#535, merged on 2026-08-28 and awaits a live re-drive (L6148-6155). That is F-018's state exactly.
   - **Fix:** Name F-012 in the reach bullet and in item 26's start list, and F-013 as unsettled per Lane 11-R3A. Record Lane 11-R3A's pointer in the round-3 record.
   - **Changes a number, disposition or action?** Action: yes (the reach put to the owner, and item 26's start list). Number and disposition: no, since the counts are stated for "those two alone".

3. **NIT: the lead, the Summary and the README still say every trigger took effect, and the README says the transcript does not split a delay the ledger now splits for T-tab.**
   - **Quoted:**
     - Summary (L10574): "each took effect 1.3–4.2 s after it fired".
     - Instruments' lead (L10844): "Its scripted triggers took effect 1.3–4.2 s after they fired."
     - README:69-70: "… a delay the transcript does not split between the driver and the page".
     - Against these, the body (L10845-10847): T-mode's next request entered 2.1–2.5 s later, "and the transcript does not record what made it".
   - **Evidence:**
     - T-mode's effect is not in the transcript. T-gate (1,336 ; 1,367 ms) and T-tab (1,304, 3,396 ; 1,581, 4,203 ms) span 1.3–4.2 s on their own, so the range stands.
     - T-tab's gate writes came 311, 460 ; 873, 1,890 ms after each click had already returned in the page, which is page time only. The ledger also bounds the driver's share at 0.7–1.0 s.
   - **Fix:** "T-gate and T-tab took effect 1.3–4.2 s after they fired; T-mode's effect is not recorded." In the README, say the transcript splits the delay only for T-tab.
   - **Changes a number, disposition or action?** No.

4. **NIT: two attributions in round 3's text are wrong.**
   - **(a)** L10849 ("where the stamp is taken, round 3, Lane 11-R3B") and L11011-11013 credit Lane 11-R3B alone with where the click is stamped. Lane 11-R2A reported it in round 2 (`…phase11_round2.md:77`: "That figure also includes the click's own handling in the page"). Lane 11-R3B's F4(b) credits Lane 11-R2A, and Lane 11-R3A's row 13 notes it too.
   - **(b)** L11014 says "Only the trace's report exits 2 on an alternation break". The replay also exits 2 (it refuses with status 2), as the Instruments section and round 2's record say. The intended contrast is with the trace's `--self-test`.
   - **Changes a number, disposition or action?** No.

5. **NIT: the round-3 rederive script's docstring cites a report file that does not exist, and misnames when an eviction happens.**
   - **Quoted** (`util/ad-hoc/2026-10-08_phase11_round3_rederive.py`): ":13 `…/consensus/2026-10-05_validator_reports_phase11_round3.md`" and ":19 … which is when the next request entered".
   - **Evidence:** The file is `2026-10-08_validator_reports_phase11_round3.md`. An eviction happens when the next request is made; that request enters `watched` later (the ledger's own distinction, L10662-10663).
   - **Fix:** Use the 10-08 path, and write "was made".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- **"Weekly" usage limit.** No artifact says "weekly". The resume message quoted in the report file says only "an API usage limit".
- **Verbatim reports.** I had no access to the agents' transcripts, so I could not confirm the archived reports are their final messages. Only their lengths match the stated character counts.
- **CodeQL on this PR.** Whether CodeQL itself will report nothing on Phase 11's PR; the prescreen only predicts it.
- **A full sweep of the reach (item 26's job).** canopy's own manual has listed `output_weights` as a Network Editor patch target since at least 2026-08-11 (USER_MANUAL.md:370-378 at `3411673c`). F-012 may therefore be P1 on the manual alone, without any ruling. I did not assess that rating.
- **Live runs.** I started no service or browser, and did not re-run the synthetic check.

**SECRETS/PII:** No environment values, tokens, credential files or e-mail addresses were printed, requested or sent. Git use was `log --format='%h %s'`, `show <rev>:<path>`, `diff`, `ls-files`, `grep`, `rev-parse`, `rev-list`, `merge-base --is-ancestor` and `cat-file -t`. canopy was read from its object store, with no fetch. One slip: a single canopy `git log` used `--format='%h %ad %s'`, which printed author dates only, with no name or e-mail. I ran no `git show --stat`. `gh api` calls were GETs only and printed only merge fields, paths and first lines. I touched no port, service or browser. I read Lane 11-R3A's and Lane 11-R3B's scratch sources read-only, and did not open Lane 11-R4A's directory. No repository file was changed; all scratch work is in my `mktemp -d` directory.

---
