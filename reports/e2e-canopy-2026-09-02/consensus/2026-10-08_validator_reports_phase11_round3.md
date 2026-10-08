<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 3 — validator reports (verbatim)

Round 3 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen 7af6a381 (round 2's pass applied to b3c54692). Two lanes from one brief, reports/e2e-canopy-2026-09-02/drafts/lane11R3_phase11_ledger_brief.md, briefed on round 2's corrections only. Both lanes started on 2026-10-05 and stopped part-way when the API's weekly usage limit was reached; on 2026-10-08 each was resumed with its context by a message that begins 'Resume Lane 11-R3…: your run was cut off by an API usage limit'. The archiver splits each transcript at that message, so 'after its round-3 brief' below means after the resume message, and each report is the lane's final message, verbatim. The orchestrator's dispositions are in the ledger's Phase 11 Consensus record; the correction pass is util/ad-hoc/2026-10-08_phase11_ledger_round3_corrections.py.

## Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections)

*agent `ad8dc12fc07b898dc` · round 3 · last-assistant-text (after its round-3 brief) · 15035 chars*

**Lane 11-R3A** (measurement re-creation, artifact-first, on round 2's pass)

**VERDICT: SOUND-WITH-FIXES.** Round 2's pass replays byte for byte, with no hand edit. Every number it introduced or changed comes out the same from my own reader. The new AMBIGUOUS flag, the fifth self-test, the exit status of 2 and the replay's refusal all behave as described in report mode. Two MINOR findings change a disposition, a number or an action, so under §4 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` the review does not end at this round. The other three findings are NITs.

**TABLE**

Names used below:
- **L** is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `7af6a381`.
- **R** is `reports/e2e-canopy-2026-09-02/f058-census-v2/README.md` at `7af6a381`.
- **RT** is `util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py`, and **AR** is `util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py`.
- **T1 ; T2** are the two transcripts, first run then second.
- **$S** is my `mktemp -d` directory, `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11R3A.THYyw0`.
- `myhorizon.py` is my own reader, written from the shim's JavaScript: W, A and X come from `raw.req`; a re-enable is a fire, or a gate write of `false`, whose lane-before value is `true`; "in flight" means W ≤ t < end.

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | Round 2's pass applied to both files at `b3c54692` gives `7af6a381` | Both files identical (sha256 `aed5c5a0…` and `7c565f2f…`). The pass printed "14 substitutions … README: 2". A second run refuses: "not the round-2 freeze". | MATCH, no hand edit | `$S/replay.py` |
| 2 | "14 substitutions in the ledger and 2 in the evidence README" | 14 and 2 | MATCH | same run |
| 3 | 79 / 53 / 1 / 2 / 23 findings; 7 open P1 and 16 open P2 | Identical | MATCH | `e2e_finding_triage.py --note` run on L |
| 4 | F-065's condition in Phase 11 (Matrix, Unresolved bullet): "a shipped CHANGELOG or design-plan promise" | Matches F-065's Severity bullet (L:10130-10133) and Phase 10's question (L:10315). F-065's own header (L:10086) still says "a shipped CHANGELOG promise". | MATCH (the header gap is Finding 1) | L |
| 5 | Two limbs in the Rating bullet, the Matrix and the Consensus record | F-068's header (L:10713), the Summary's "Filed" bullet (L:10569) and the Rating's bold lead (L:10759) still give the one-limb condition | breaks (F1) | L |
| 6 | Counts per ruling: 7/16, 6/17, 5/18 | Correct for F-065 and F-068. F-055, F-058, F-064, F-CASCOR-001 and F-CASCOR-002 rest on no CHANGELOG or design-plan promise. F-057 was never checked against limb 1's design-plan half. | overreaches (F2) | `$S/rating_basis.py`; the CAN-015g/h design note |
| 7 | Dissent: Lane 11-B1 rated F-068 P2, on the code comment, as drift; its brief never showed it the CHANGELOG | B1's row 2: the contract "counts under §6.3 only as drift (P2)". Its brief contains no "CHANGELOG". | MATCH | `…_validator_reports_phase11_round1.md`; `lane11B1_phase11_ledger_brief.md` |
| 8 | 32 mid-request re-enables (28 fires, 4 gate writes), 8 of them evicting | 32 (28 + 4); 8 evicting (7 fires plus the gate write at 7,253). The clamp releases at 726,055 ; 721,354 had nothing in flight. | MATCH | `myhorizon.py` |
| 9 | "The 8 evicted 1.2–2.4 s after the re-enable"; the trigger bullet's 1.2–2.4 s | 1,214–2,392 ms | MATCH | same |
| 10 | "after the other 24 the answer had landed first, 0.1–2.2 s after it" | 104–2,164 ms. The three gate writes in this group: 1,103, 1,114 and 1,763 ms. | MATCH | same |
| 11 | Next request entered `watched` 1.3–3.7 s after a re-enable; the three longest came at T-tab activity; without them 1.3–2.6 s | 1,314–3,663 ms. The top three are 3,365 ms (T1's fire at 476,732, 568 ms before T-tab fired; the wait spans its first click and gate write), and 3,553 and 3,663 ms (the two T-tab second-click writes). Without them: 1,314–2,563 ms. | MATCH | same |
| 12 | F-068's Effect "1.4–2.4 s after the fire" against F-058's 1.2–2.4 s | Evicting fires: 1,418–2,392 ms, which sits inside 1,214–2,392 ms for all eight evictions. The two agree on evictions. The Effect's wording scope is Finding 4. | holds (NIT F4) | same |
| 13 | T-gate's write at 1.3–1.4 s; T-mode's next request at 2.1–2.5 s; T-tab's clicks at 0.7–1.0 and 2.3–2.9 s; the 1 s wait took 1.6–1.9 s; each click-to-write 0.3–1.9 s | 1,336 ; 1,367. 2,148 ; 2,503. 993, 2,936 ; 708, 2,313. 1,943 ; 1,605. 311, 460 ; 873, 1,890. `clicks_ms` is page time read right after `t.click()` returns (live.py, `CLICK_TAB`). | MATCH; no attribution left in L | `$S/extra_checks.py` |
| 14 | Item 25's method: an in-page trigger run as its own task, every action timed in the page, validated on the synthetic check first | Sound as stated. The scoring rule also covers the second Input's direct re-request. | holds | L:10846-10850, L:11005-11010 |
| 15 | R:69-71 trigger-lag sentence | Still says "partly through the renderer's queue and, for T-tab, mostly through the driver's own late clicks", citing L's Instruments | breaks (F3) | R |
| 16 | AMBIGUOUS flag count 0 in both runs; pairings forced | Both reports print 0. My independent check: at every late release, no other evicted request was still unreleased. | MATCH | RT output; `$S/pending_check.py` |
| 17 | The flag catches Lane 11-R2B's case | R2B's exact mutation (req 177's release moved to 905,500, req 178's at 905,789 dropped) pairs 905,500 with 178 and flags it with [177]. The later release in the same run, 908,397, is also flagged, which is by design. Without the drop, the moved release is still flagged and 178's real release shows as unassigned. | holds; it cannot fire falsely under its own definition | `$S/extra_checks.py` |
| 18 | Five self-tests pass on both transcripts | (a) to (e) all True; SELF-TEST PASS twice; exit 0. Case (e) uses req 17/18 ; 73/74, the same construction as R2B's mutation. | MATCH | RT `--self-test` |
| 19 | An alternation break makes RT exit 2 and the replay refuse | With one innermost record dropped: the report exits 2 and AR prints "refusing" with exit 2. `--self-test` prints PASS with exit 0. Dropping a disable/enable pair produces 0 breaks. | holds for the report only (NIT F5) | `$S/break_test.py` |
| 20 | Innermost records alternate with no break | 0 breaks in both runs. My push-order walk gives the same 617 ; 610 changes as the type selection, and no change is carried only by a non-thunk record. | MATCH | `$S/extra_checks.py` |
| 21 | AR medians: 5–16 (median 9) and 3–18 (median 7) in phase; random median 1 ; 1; no fire in 94 and 102 of 500; 1 to 3.5 at 6,000 and 7,500 ms (were 2 to 4) | AR at `7af6a381` prints all of these. AR at `1b7cf44b` gives 2, 2 ; 4, 2 in phase and 2, 3 ; 3, 4 at random, which is 2 to 4. | MATCH | `$S/ar*.txt`, `$S/old_replay.py` |
| 22 | "165,942 in the first run" | `raw.dispatches` is 165,942 (150,376 in the second run) | MATCH | T1 |
| 23 | Source of the minutes: "(Lanes B and B1)" | The entry's own Lane B (352 s) and Lane B1 (0 of 45 over 90 s) | MATCH | L:9159-9177 |
| 24 | R's self-test count "five" and its trio sentence | "five" matches RT. The trio sentence itself says no file records the reading. | holds; the reading is UNTRACEABLE by its own words | R:25-26, R:51 |
| 25 | Round 2 record: verdicts, effects, attributions, dissent, slips, "16 files" | All match `…_validator_reports_phase11_round2.md`. 16 probes are in the tree, each verbatim against the lanes' tmpfs sources. R2B F4's "Action: minor (item 24's instrument)" is not mentioned, which changes nothing. | MATCH | `$S/probe_archive_check.py` |

**FINDINGS**

1. **MINOR. Round 2's two-limbed question was not carried into F-CANOPY-068's header, the Summary or the Rating's bold lead.**
   - **Quoted (L):**
     - Header (L:10713): "(P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question; …)".
     - Summary (L:10569): "**Filed: F-CANOPY-068 (P1 if a shipped CHANGELOG promise counts as documented, else P2; OPEN)**".
     - Rating lead (L:10759): "**Rating: P1 if a shipped CHANGELOG promise counts as documented, else P2**, the owner's question that F-CANOPY-065 already carries".
     - Against these, the Matrix (L:10982-10984) says "F-CANOPY-068 only if a CHANGELOG's description of an internal mechanism does … F-CANOPY-065 alone, 6 and 17", and the Unresolved bullet (L:10922-10925) says the same.
   - **Evidence:** Take the Matrix's own 6/17 ruling: shipped CHANGELOG promises of what a user sees count, and descriptions of internal mechanisms do not. The header's condition is then met, so the header reads P1, while the Matrix counts F-068 P2. The Rating bullet now also says both that F-068 rests on "the owner's question that F-CANOPY-065 already carries" and that "a ruling for F-CANOPY-065 does not by itself settle it". A related gap predates round 2: F-065's header (L:10086) still says "a shipped CHANGELOG promise", narrower than its own Severity bullet (L:10130-10133), which Phase 11 now quotes.
   - **Fix:** In the header, the Summary and the Rating lead, write "P1 if a CHANGELOG's description of an internal mechanism counts as documented behaviour (the owner's question, second limb), else P2", and drop "that F-CANOPY-065 already carries". Make F-065's header read "a shipped CHANGELOG or design-plan promise".
   - **Changes a number, disposition or action?** Disposition: yes, the condition F-068's rating is stated to depend on. Number: no; the triage still reads P1.

2. **MINOR. The counts per ruling assume limb 1 cannot reach F-CANOPY-057, which the ledger never checked.**
   - **Quoted (L:10982-10984):** "F-CANOPY-065 is P1 only if a shipped CHANGELOG or design-plan promise counts as documented … By ruling: both P1, 7 open P1 and 16 open P2 …; F-CANOPY-065 alone, 6 and 17".
   - **Evidence:**
     - The design note `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md` promises "decision-boundary animation with per-unit weight evolution" (:17-19). Its status line reads "Implemented" (:3). It records "every CAN-015g item has merged to `main`" (:47-49), including g-7, "Decision-boundary + network-evolution renderers consume V2 weight payloads" (:93).
     - That is exactly the stream F-CANOPY-057 says "never reaches the page" (L:9086).
     - It is the same kind of document as F-065's design-plan basis, the T3 line of `notes/JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md:311` ("canopy renders both sets").
     - F-057's entry rests only on the manual and the FAQ (L:9121-9123), and L cites the CAN-015g/h note nowhere.
     - canopy's released CHANGELOG sections carry no such promise at `60ae1870` or `c7876f5a`; every match sits under `[Unreleased]`, and those lines disclaim the stream. So only the design-plan half of limb 1 reaches F-057.
     - The other four P1s that do not turn on the question (F-055, F-058, F-064, F-CASCOR-001/002) rest on no such promise, so the 5/18 count for "neither" stands.
   - **Fix:** Either name F-057 in limb 1 and give its counts (if design plans count: 8 and 15 with F-068 P1, 7 and 16 without), or state why a design note that records the stream as delivered is not a design-plan promise.
   - **Changes a number, disposition or action?** Number: yes, two branch counts. Action: yes, the scope of the owner's question.

3. **NIT. The README still makes the lag attribution that round 2 withdrew from the ledger.**
   - **Quoted (R:69-71):** "Its scripted triggers take effect 1.3–4.2 s after they fire, partly through the renderer's queue and, for T-tab, mostly through the driver's own late clicks … (the ledger's Phase 11, Instruments)".
   - **Evidence:** L's Instruments now says "the transcript does not separate the driver's round trip from the renderer's queue" (L:10839-10841). It states T-tab's delays only conditionally: "if T-tab's delays above are the driver's" (L:10849). No driver-side timestamp exists to support the README's split.
   - **Fix:** "Its scripted triggers took effect 1.3–4.2 s after they fired, a delay the transcript does not split between the driver and the renderer, so as written …".
   - **Changes a number, disposition or action?** No.

4. **NIT. F-CANOPY-068's Effect gives the 1.4–2.4 s range as when the next request is made after any fire.**
   - **Quoted (L:10753-10755):** "if the response in flight has not landed when the next request is made, 1.4–2.4 s after the fire in these runs, that response is evicted".
   - **Evidence:** The range holds only for the 7 evicting fires (1,418–2,392 ms). For the other 21, the transcript has no record of when the next request was made. After T1's fire at 476,732, the next request entered `watched` 3,365 ms later, and in the 8 re-enable evictions an eviction preceded its successor's `watched` by at most 397 ms. L:10660 itself says "anywhere from 1.4 s to more than 2.2 s".
   - **Fix:** "… that response is evicted; the seven that were evicted were evicted 1.4–2.4 s after the fire."
   - **Changes a number, disposition or action?** No.

5. **NIT. The exit-2 claim holds for the report only.**
   - **Quoted:** L:10821-10822, "An alternation break in the innermost records makes it exit 2"; and the Round 2 record, L:10961, "an exit status of 2 on any alternation break".
   - **Evidence:**
     - On a transcript with a break, `--self-test` prints PASS and exits 0.
     - Dropping a full disable/enable pair produces no break at all; neither run has such a change, by my push-order walk.
     - `self_test`'s docstring (RT:293) still says "Two mutated copies".
   - **Fix:** Write "makes its report exit 2", and say five in the docstring.
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- The trio's pids and start times "read then". No artifact records them, and under the port rule I did not probe them live.
- When the next request was made after the 24 re-enables that evicted nothing. The shim never sees `AddRequested`.
- Whether an in-page `setTimeout(0)` trigger avoids reordering in practice. I drove no browser, and I did not examine dash 4.4.1.
- A full sweep of the 16 open P2s against canopy's CHANGELOG and the design plans. I checked each entry's stated basis, and F-057 against the CAN-015g/h note. F-012 and F-013 against that note's CAN-015h half are not settled.
- The synthetic check, which I did not re-run because it starts apps. Of round 1's reports, I read only Lane 11-B1's section.

**SECRETS/PII:** No environment values, tokens, credential files or e-mail addresses were printed, requested or sent. I ran no `git show --stat` and no author or body log format; git use was `git log --format='%h %s'`, `git diff`, `git show <rev>:<path>`, `git ls-tree` and `git grep`. canopy was read from its object store, with no fetch. I touched no port, service or browser. No repository file was changed, and all scratch work is in `$S`. No slips.

---

## Lane 11-R3B (adversarial, on round 2's correction pass)

*agent `a013bab17436e8456` · round 3 · last-assistant-text (after its round-3 brief) · 15650 chars*

**Lane 11-R3B** (adversarial on round 2's correction pass)

**VERDICT: SOUND-WITH-FIXES.** Round 2's pass replays byte for byte. Every figure it introduced re-derives within the scope it is stated for, and both readers behave as `…E2E-VALIDATION-EVIDENCE.md` says. The pass did leave three problems. It split the owner's question in only some places: F-CANOPY-068's header, the Summary and the Rating bullet's lead still give the old single condition. F-CANOPY-058's trigger bullet now applies the 8 trigger evictions' range to all 29 evictions. And `f058-census-v2/README.md` still attributes the trigger lag, although the ledger no longer does. Findings 1 and 2 change a number or an action, so §4 of `…INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires another round.

**TABLE** (line numbers are at `7af6a381`; values are "T1 ; T2")

| # | Claim or correction | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | The pass on both `b3c54692` files gives both `7af6a381` files | Identical. It printed "ledger: 14 substitutions, 895143 -> 901155 chars; README: 2" | MATCH, no hand edit | `cmp` and sha256 (`aed5c5a0…`, `7c565f2f…`) in a scratch tree |
| 2 | The record's "14 substitutions … and 2" | 14 and 2 | MATCH | `len(SUBS)`, `len(README_SUBS)` |
| 3 | Counts 79/53/1/2/23, 7 P1 and 16 P2; by ruling 7/16, 6/17, 5/18 | Identical. Of the open P1s, only F-065 and F-068 have a conditional header | MATCH (arithmetic) | `e2e_finding_triage.py --note` on the `7af6a381` ledger; own header scan |
| 4 | F-065's condition quoted as "a shipped CHANGELOG or design-plan promise" | Matches its Severity bullet (`…E2E-VALIDATION-EVIDENCE.md:10132-10133`) and Phase 10's question (`:10315`). Its own header (`:10086`) says only "a shipped CHANGELOG promise" | MATCH; the header mismatch predates round 2 | Finding 1 |
| 5 | The Rating bullet's second limb agrees with the Matrix, the Consensus record and the header | Agrees with the Matrix (`:10982-10984`) and "Unresolved" (`:10922-10925`). Disagrees with the header (`:10713`), the Summary (`:10569`) and the bullet's own lead (`:10759-10760`) | breaks | Finding 1 |
| 6 | "The 8 evicted 1.2–2.4 s after the re-enable" | 1,214 (the gate write at 7,253), 1,582, 1,907, 2,392 ; 1,418, 1,988, 2,001, 2,285 ms | MATCH | own reader on raw `req`, `fires` and `gate` |
| 7 | "After the other 24 the answer had landed first, 0.1–2.2 s after it" | 104–2,164 ms; the three gate writes 1,103 and 1,114 ; 1,763 | MATCH | same |
| 8 | Next request entered `watched` 1.3–3.7 s after a re-enable; the three longest at T-tab activity; 1.3–2.6 s without them | 1,314–3,663 ms. The three longest are 3,365 (the fire at 476,732, T1), 3,553 (the T-tab write at 478,476, T2) and 3,663 (the T-tab write at 480,696, T1). The next longest is 2,563 | MATCH | same; T-tab fired at 477,300 ; 474,273 |
| 9 | F-058's trigger bullet: "the evictions came 1.2–2.4 s after the re-enable" | The 8 trigger-started evictions: 1,214–2,392 ms. The 21 that followed a late release: 1,422–2,553 ms, four of them above 2.4 s. All 29: 1.2–2.6 s | MISMATCH as worded | Finding 2 |
| 10 | F-068's Effect, "1.4–2.4 s after the fire", against the 8 evictions' 1.2–2.4 s | The 7 evicting fires: 1,418–2,392 ms, so the two agree. For the other 21 fires, when the next request was made is not logged | MATCH for the evicting fires; UNTRACEABLE as a claim about every fire | Finding 5 |
| 11 | Release trace report on both runs | 0 breaks, 0 AMBIGUOUS, 18 + 11 evictions paired, 0 unassigned, exit 0 | MATCH | `…release_trace.py` at `7af6a381` |
| 12 | `--self-test`: all five pass on both transcripts | (a)–(e) all True. Case (e) flags 86,025 (req 18, with 17) ; 406,681 (req 74, with 73). Exit 0 | MATCH | same |
| 13 | The flag catches Lane 11-R2B's case | Its exact mutation (177's release moved to 905,500, 178's dropped): 905,500 is paired with 178 and flagged AMBIGUOUS with 177. The flag never fires on the real runs. One displaced release flags 7 releases: itself and the 6 after it in its run | holds | `r2b_case.py` |
| 14 | Exit 2 on an alternation break; the replay refuses | One change re-typed as non-thunk: trace exit 2, replay exit 2. A pair re-typed (one enabled stretch): 0 breaks, both readers exit 0, and fire @81,743 silently moves. `--self-test` on a transcript with a break prints PASS and exits 0 | holds as the ledger states it; the docstrings claim more than the guard does | Finding 8 |
| 15 | Replay figures and "1 to 3.5 at 6,000 and 7,500 ms (were 2 to 4)" | Identical to the ledger. At 6,000/7,500 ms, in phase 1, 2 ; 3.5, 2 and random 2, 3 ; 2, 3. "2 to 4" is `1b7cf44b`'s `:10719` | MATCH | `…alias_replay.py` at `7af6a381` |
| 16 | Item 25's method | Firing from a separate task after the shim's wrapper returns cannot reorder the dispatch it is measuring. Timing in the page and validating on the synthetic check first are both sound | holds | the shim's wrapper (`…_shim.py:69-101`) |
| 17 | The lag is "no longer attributed" | T-mode's 2.1–2.5 s is still given as the trigger's effect. T-tab's click times are stamped after `t.click()` returns. The 1.0–2.9 s bound includes page-side lag | overreaches | Finding 4 |
| 18 | The README's lag sentence | `f058-census-v2/README.md:69-71` still attributes the lag | breaks | Finding 3 |
| 19 | The README's trio sentence; "five known-answer mutations" | Matches the ledger; five | MATCH | — |
| 20 | The minutes were reached "only in synthetic repros (Lanes B and B1)" | Lane B: 352 s. Lane B1: 0 of 45 applied over 90 s, synthetic | holds | F-058's entry |
| 21 | "(165,942 in the first run)" | `raw.dispatches` is 165,942 | MATCH; but "wraps every dispatch" is wrong | Finding 6 |
| 22 | Round 2 record against `…phase11_round2.md` | Verdicts, slips and the B1 dissent all match. The dissent is at `…phase11_round1.md:270`, and B1's brief has no "CHANGELOG" | MATCH except Findings 3 and 7 | — |
| 23 | 16 archived probes | 16 of 16 byte-identical to their tmpfs sources, rebuilt with the archiver's own `header()` | MATCH | `verify_archive_r2.py` |

**FINDINGS**

1. **MINOR: the owner's question is still stated two ways.** Round 2 split it only in the Matrix, the Consensus record and the body of the Rating bullet.
   - **Quoted** (all in `…E2E-VALIDATION-EVIDENCE.md`):
     - F-068's header (`:10713`) and F-065's header (`:10086`) carry the identical condition: "P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question".
     - The Summary (`:10569`): "Filed: F-CANOPY-068 (P1 if a shipped CHANGELOG promise counts as documented, else P2; OPEN)".
     - The Rating bullet's lead (`:10759-10760`): "the owner's question that F-CANOPY-065 already carries". The bullet's own new sentence (`:10764-10766`) denies this: "a ruling for F-CANOPY-065 does not by itself settle it".
   - **Evidence:**
     - The ledger itself calls F-068's CHANGELOG text a shipped promise: "canopy's CHANGELOG makes the promise to its readers" (`:10723-10724`) and "canopy's shipped CHANGELOG promises the behaviour" (`:10761`).
     - Limb 1 as put to the owner (`:10922`) is not limited to promises of something a user sees.
     - So take a ruling that CHANGELOG promises count but descriptions of internal mechanisms do not. F-068's header makes it P1, giving 7 open P1 and 16 open P2. The Matrix's "F-CANOPY-065 alone" makes it P2, giving 6 and 17.
     - F-065's header is also narrower than the "CHANGELOG or design-plan" the Matrix quotes. That mismatch predates round 2.
     - The round-1 record (`:10884-10885`) still says "the owner's question F-CANOPY-065 already carries". It is history, but it now reads as current.
   - **Fix:**
     - In "Unresolved" and the Matrix, limit limb 1 to promises of user-visible behaviour.
     - Restate F-068's header, the Summary and the Rating lead as the second limb: "P1 if a shipped CHANGELOG's description of an internal mechanism counts as documented behaviour, else P2". Drop "that F-CANOPY-065 already carries".
     - Align F-065's header with its Severity bullet.
     - Note in the round-1 bullet that round 2 split the question.
   - **Changes a number, disposition or action?** Yes. Under one ruling it changes F-068's rating and the counts, and it changes the question as put to the owner.

2. **MINOR: F-CANOPY-058's trigger bullet applies the 8 trigger evictions' range to every eviction.**
   - **Quoted** (`…E2E-VALIDATION-EVIDENCE.md:9153-9156`): "(in Phase 11's runs, the evictions came 1.2–2.4 s after the re-enable)". The same bullet calls a late completion a re-enable: "The evicted request's late completion then re-enables the lane under its successor".
   - **Evidence:**
     - 21 of the 29 evictions followed a late release. They came 1,422–2,553 ms after it.
     - Four came after 2.4 s: 2,452 and 2,553 ms in T1 (176→177, 179→180), and 2,552 and 2,444 ms in T2 (81→82, 270→271).
     - All 29 together span 1,214–2,553 ms.
     - Two independent readers agree: one built on the trace's `analyze()`, and one using no repo code.
     - The Status bullet (`:9136-9139`) and the events bullet (`:10661-10663`) are limited to the 32 trigger re-enables, and they hold.
   - **Fix:** "the 8 evictions a fire or gate write started came 1.2–2.4 s after it; within the runs, 1.4–2.6 s after the late release before each". Or say 1.2–2.6 s without the scope.
   - **Changes a number?** Yes, as worded.

3. **MINOR: the README still attributes the lag that round 2 withdrew in the ledger.**
   - **Quoted** (`f058-census-v2/README.md:69-71`): "partly through the renderer's queue and, for T-tab, mostly through the driver's own late clicks".
   - **Evidence:**
     - The ledger now says the transcript "does not separate the driver's round trip from the renderer's queue", and makes T-tab's share conditional (`…E2E-VALIDATION-EVIDENCE.md:10839-10849`).
     - The round-2 record (`:10957-10959`) says the lag is "no longer attributed to the renderer's queue".
     - The README says the ledger governs (`f058-census-v2/README.md:5-6`).
   - **Fix:** "1.3–4.2 s after they fire; the transcript does not say how much of that is the driver's".
   - **Changes a number, disposition or action?** No.

4. **MINOR: the Instruments section still attributes lag that the transcript cannot attribute.**
   - **(a) T-mode.** `…E2E-VALIDATION-EVIDENCE.md:10839-10841` gives "2.1–2.5 s to the next request" as T-mode's effect. But T-mode's own row (`:10616`) says "the transcript does not record what made it", so the request may simply be the Interval's tick. Lane 11-R2B's fix for this, "State each lag without attributing it", was not applied.
   - **(b) T-tab.** The ledger says "0.7–1.0 s and 2.3–2.9 s passed before its clicks ran in the page" (`:10841-10842`). But `CLICK_TAB` stamps the time after `t.click()` returns (`2026-10-04_f058_census_v2_live.py:127-128`), so each figure includes the click's own handling. Lane 11-R2A said so in round 2.
   - **(c) The 1.0–2.9 s bound.** "A trigger sent from Python then may land 1.0–2.9 s into the flight, if T-tab's delays above are the driver's" (`:10848-10849`). The bound is 0.7–1.0 s of click lag plus 0.3–1.9 s from click to gate write. The second part happens in the page, cannot be the driver's, and a trigger fired in the page would pay it too.
   - **Fix:**
     - "The next request entered 2.1–2.5 s after T-mode fired; the transcript does not record what made it."
     - "T-tab's clicks had returned by +0.7–1.0 s and +2.3–2.9 s."
     - "A trigger sent from Python adds up to 0.7–1.0 s."
   - **Changes a number, disposition or action?** No. Item 25 already covers the action.

5. **NIT: F-068's Effect gives the evicting fires' range as if it held for every fire.**
   - **Quoted** (`…E2E-VALIDATION-EVIDENCE.md:10753-10755`): "when the next request is made, 1.4–2.4 s after the fire in these runs".
   - **Evidence:** the range is right for the 7 evicting fires. For the other 21, when the next request was made is not logged (`AddRequested` bypasses the wrapper), and the next request entered `watched` up to 3,365 ms after a fire.
   - **Fix:** "(1.4–2.4 s after the fire, for the 7 that evicted)".
   - **Changes anything?** No.

6. **NIT: "wraps every dispatch" contradicts the Instruments section.**
   - **Quoted** (`…E2E-VALIDATION-EVIDENCE.md:10931-10932`): "the shim, which wraps every dispatch (165,942 in the first run)". The Instruments section says the opposite (`:10833-10834`): "actions dispatched inside a thunk, such as `AddRequested`, bypass its wrapper".
   - **Fix:** "wraps the store's `dispatch` (165,942 calls)".
   - **Changes anything?** No.

7. **NIT: the round-2 record misplaces one of the three longest waits.**
   - **Quoted** (`…E2E-VALIDATION-EVIDENCE.md:10955-10956`): "the three longest after the census's own T-tab activity".
   - **Evidence:** the third began with the fire at 476,732, 0.57 s before T-tab fired at 477,300. Lane 11-R2B's report says "0.6 s before T-tab fired". The ledger's body text, "came at" (`:10663`), is correct.
   - **Fix:** "at", not "after".
   - **Changes anything?** No.

8. **NIT: the alternation-break guard catches less than the docstrings say.**
   - The ledger's own sentence (`…E2E-VALIDATION-EVIDENCE.md:10821-10822`) is true.
   - The trace's docstring and the replay's comment imply that any lane change logged only by a non-thunk record is caught. A pair of such changes is not.
   - I re-typed the enabled stretch 79,312→81,451 (T1) as non-thunk. Both readers then report 0 breaks and exit 0. Fire @81,743 now reads a 6,379 ms episode and 10,963 ms enabled, outside the ledger's 0.3–3.6 s and 11.0–14.9 s.
   - `--self-test` exits 0 on a transcript with a break.
   - `self_test`'s docstring still says "Two mutated copies".
   - Lane 11-R2A's walk found no such hidden change in these runs.
   - **Fix:** compare the push-order walk with the type-based selection and exit 2 on any difference; also check for breaks in `--self-test`.
   - **Changes anything?** No number or disposition. Minor action: item 24's instrument.

**WHAT YOU COULD NOT CHECK**
- **The counts for each ruling hold only if F-065 and F-068 are the only findings the owner's ruling moves.** No sweep of the open P2s against canopy's CHANGELOG and design plans exists. For example, F-CANOPY-018 concerns the same apply toast that CHANGELOG 0.6.0 promises.
- Whether `…phase11_round2.md` holds the lanes' final messages verbatim.
- How the lag splits between the driver and the page. Nothing logs it.
- How long T-tab's click handling took. Nothing stamps the time before the click.
- When the next request was made after the 21 non-evicting fires. It is not logged.
- I did not re-run the synthetic check, examine dash 4.4.1, drive a browser, or check the trio's processes.
- My probe scripts exist only in `/tmp/tmp.cIFAKjB6BD`: `horizon.py`, `late_to_x.py`, `reenable_to_x.py`, `r2b_case.py`, `altbreak_mut.py`, `verify_archive_r2.py`, `p1_headers.py` and the `*.sh` runners. Copy them to `util/ad-hoc/` if they should be kept.

**SECRETS/PII**
- No environment values, tokens, credentials or e-mail addresses were printed, requested or sent.
- Git commands were limited to:
  - in juniper-ml: `log --format='%h %s'`, `diff`, `show <commit>:<path>`, `status --short` and `rev-parse`;
  - in canopy's object store: `cat-file -t` and `show 60ae1870:<path>`.
- I ran no `git show --stat`, no author or body log format, and no fetch.
- I touched no port, service or browser.
- To verify the archive I read round 2's lane scratch files and printed only match status.
- No repository file was changed; all work is in the `mktemp -d` directory `/tmp/tmp.cIFAKjB6BD`. No slips.

---
