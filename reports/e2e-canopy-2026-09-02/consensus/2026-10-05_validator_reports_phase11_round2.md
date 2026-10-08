<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 2 — validator reports (verbatim)

Round 2 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen b3c54692 (round 1's pass applied to 1b7cf44b), 2026-10-05. Two lanes, briefed on round 1's corrections only; briefs in reports/e2e-canopy-2026-09-02/drafts/lane11R2A_phase11_ledger_brief.md and lane11R2B_phase11_ledger_corrections_brief.md. Each report below is the lane's final message, verbatim (each lane ran once, so the archiver's round-1 mode applies). The orchestrator's dispositions are in the ledger's Phase 11 Consensus record; the correction pass is util/ad-hoc/2026-10-05_phase11_ledger_round2_corrections.py.

## Lane 11-R2A (measurement re-creation, on round 1's corrections)

*agent `a80218ff457d628f7` · round 1 · last-assistant-text (not resumed) · 16373 chars*

**VERDICT: SOUND-WITH-FIXES.** The correction pass replays byte for byte. Every number, line, quote and count it introduced or changed in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` re-derives, most of them from my own reader. The instruments print what that ledger says they print, and its new "Round 1" record is faithful to `2026-10-05_validator_reports_phase11_round1.md`. I have two NITs. Neither changes a number, disposition or action in the ledger, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this lane gives no reason for a third round.

**TABLE**

How the rows were derived:
- `$S` is the `mktemp -d` directory `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11R2A.sffLXI`.
- `tree_b1` and `tree_b3` are `git archive` copies of `util/ad-hoc`, the evidence directory and the ledger at `1b7cf44b` and `b3c54692`.
- `myreader.py` is my own reader, written from the shim's JavaScript. It walks the lane records in push order. A record whose `before` equals the current state is a new change, and it is the innermost record of that change. Any other record is an enclosing dispatch logging the same change again.
- I checked that walk against a selection by type (`''` or `SET_LAYOUT`).
- T1 and T2 are the two transcripts. Values are given as "T1 ; T2". Everything ran with `python3 -B`.

| # | Claim at `b3c54692` | Re-derived | Result | Evidence |
|---|---|---|---|---|
| 1 | Replay: the pass at `b3c54692`, applied to both files at `1b7cf44b`, gives both files at `b3c54692` | identical | MATCH | In `$S/replay` the pass printed "ledger: 30 substitutions, 882819 -> 895143 chars; README: 2 substitutions". `cmp` found both files identical (sha256 `cfcb0b41…` and `576f3996…`). A re-run refuses: "the round-1 placeholder is absent". No hand edit. |
| 2 | The record's "30 substitutions in the ledger and 2 in the evidence README" | 30 and 2 | MATCH | same output |
| 3 | The innermost records "alternate with no break in either run" | 617 ; 610 changes. The push-order walk and the type selection give identical lists, with 0 anomalies and 0 breaks. Enclosing re-logs: 367 ; 333 | MATCH | `myreader.py`; release trace at `b3c54692`: "0 alternation breaks" |
| 4 | A change read from its enclosing record is dated early "by a median of about 22 ms and up to 327 ms" | median 21 ; 23 ms, maximum 217 ; 327 ms | MATCH | `myreader.py` |
| 5 | Lane enabled for 11.0–14.9 s of the 30 s before each fire | 12,260–13,992 ; 11,018–14,891 ms | MATCH | `myreader.py`, release-trace fire rows |
| 6 | Disabled episode 0.3–3.6 s old at each fire | 292–2,011 ; 401–3,578 ms | MATCH | same |
| 7 | Median disabled episodes 2,710 and 2,743 ms; `…_analyze.py` prints 2,746 and 2,803 | Upper medians of 308 ; 304 episodes are 2,710 ; 2,743. `statistics.median` gives 2,707.5 ; 2,741.5, which are the lanes' 2,708 and 2,742. `…_analyze.py` prints "median 2746 ms" and "median 2803 ms" | MATCH (the ledger uses the upper median) | `myreader.py`; release trace; `…_analyze.py` |
| 8 | About 2.7 s disabled per cycle, the rest of the ~4.9 s cycle enabled | enabled stretches: median 2,140 ; 2,085 ms | MATCH | `myreader.py` |
| 9 | 5,000 ms sampling in phase: 5–16 and 3–18 fires at every one of 500 phases, medians 9 and 7 | The replay at `b3c54692` prints "min 5, median 9.0, max 16" and "min 3, median 7.0, max 18". My own replay on my own timeline gives the same. | MATCH | `…_watchdog_alias_replay.py`; `myreplay.py` |
| 10 | Randomized phase: median 1 in both runs; no fire in about one replay in five | 1.0 ; 1.0; no fire in 94/500 ; 102/500 | MATCH, but on a knife edge | Pooling the repo's control over 5 seed sets (2,500 replays) still gives median 1 ; 1, with P(≤1) = 0.508 ; 0.515. Single seed sets give 1, 1.5 or 2. The old timeline pools to 2 ; 2, with P(≤1) = 0.482 ; 0.457. The `1b7cf44b` replay printed 9 ; 8 in phase, 2 ; 2 random, and 87 ; 82 of 500 with no fire, so the record's "were 9 and 8, 2, and one in six" holds. |
| 11 | At 6,000 and 7,500 ms, in phase ≈ random, medians 1 to 3.5 | in phase 1.0, 2.0 ; 3.5, 2.0; random 2.0, 3.0 ; 2.0, 3.0 | MATCH | replay at `b3c54692`; `myreplay.py` |
| 12 | 32 mid-request re-enables (28 fires and 4 gate writes), 8 of them evicting | 16 ; 16. Gate re-enables with a request in flight: 7,253, 480,696 and 728,126 (T1) and 478,476 (T2). The clamp releases (726,055 ; 721,354) had nothing in flight. Evicting: the gate write at 7,253, plus fires at 81,743, 893,044, 1,452,572, 222,969, 402,697, 437,666 and 1,358,317. | MATCH | `myreader.py` |
| 13 | "13 of 21 such re-enables" (more than 1,000 ms before the response landed) "did not evict" | 14 (4 evicting, 10 not) + 7 (4 evicting, 3 not) = 21, of which 13 did not evict | MATCH | `myreader.py` |
| 14 | The next request comes 1.3–3.7 s after each re-enable, and a re-enable evicts only if the response has not landed by then | Next request entered `watched` +1,314 to +3,663 ; +1,447 to +3,553 ms (fires alone: 1.4–3.4 s). The rule holds for 32 of 32. | MATCH | `horizon.py`: "rule violations []". Measured at the eviction itself, which comes 21–397 ms before the successor enters `watched`, the page-load case is +1,214 ms. |
| 15 | Four trigger kinds: fires 28 (7 evicting), the page-load gate write 1 (evicting), tab switch 2, an Apply's end 1; the last two evicted nothing | The tab switches are 480,696 and 478,476 (answered +1,103 ; +1,763). The Apply's end is 728,126 (answered +1,114). | MATCH | `myreader.py`, `trig.py` |
| 16 | 7 evicting fires, 6 of them cascades of 2–11; "the seventh stopped at one"; 28 of 29 evictions follow a fire | Fire-started runs [2, 11, 4] ; [1, 2, 4, 4]. In T2, request 39's late release falls under request 40, "which then ended A". The page-load run of 1 is request 1. | MATCH | `myreader.py`, release trace |
| 17 | Gaps between fires: 20 of 26 within 0.3 s of a 5 s multiple, all within 0.75 s except 1.3 s across T1's clamp | 10 + 10 deviations ≤ 300 ms. The rest are 495; 321, 461, 486, 727; and 1,344, which is 893,044 − 601,700, spanning the clamp at 663,803–726,055. | MATCH | `myreader.py` |
| 18 | Longest request 5.4 s from `watched` to its response landing; runs of up to 11 evictions and 34.8 s | T2 request 39: 5,448 ms to its late release; the longest answered request is 5,345 ms. The run of 11 left 34,826 ms without an applied answer. The 65.8 s and 65.9 s gaps are the clamps, not runs. | MATCH | `myreader.py`, `stall.py` |
| 19 | T-gate's write at 1.3–1.4 s; T-mode's next request at 2.1–2.5 s (answered 0.6 ; 1.1 s); T-tab clicks at 0.7–1.0 and 2.3–2.9 s; the 1 s wait took 1.6–1.9 s; each write 0.3–1.9 s after its click; triggers fired 1.6–2.9 s into the flight | 1,336 ; 1,367. 2,148 ; 2,503 (629 ; 1,086). Clicks 993, 2,936 ; 708, 2,313. Spacing 1,943 ; 1,605. Click to write 311, 460 ; 873, 1,890. Into the flight 2,426, 1,633, 1,704 ; 2,914, 2,197, 2,324. | MATCH on the numbers; the attribution is NIT 2 | `trig.py` |
| 20 | "(a trigger sent from Python then would still land 1.0–2.9 s into the flight)" | Reproducible only as T-tab's click lag plus click-to-write: 0.7 + 0.3 to 1.0 + 1.9 | MATCH as a derived bound; no artifact states the derivation | `trig.py` |
| 21 | canopy's `CHANGELOG.md:1222-1225` at `60ae1870`, under `[0.8.0]`, added by canopy#624 (`06d8607e`); 0.8.0 shipped | `## [0.8.0] - 2026-09-11` is at :971, `### Fixed` at :1173. Both quotes are verbatim at :1222-1225. `06d8607e` is "docs(changelog): … ship in v0.8.0 … (#624)", touches only `CHANGELOG.md`, and puts the passage under `[0.8.0]`. It is an ancestor of `v0.8.0`. The GitHub release was published 2026-09-12T21:50:03Z (not a draft), and PyPI 0.8.0 was uploaded 2026-09-13 and is not yanked. | MATCH | `git -C <canopy>` show, log, diff and merge-base; `gh api …/releases/tags/v0.8.0 --jq`; PyPI JSON |
| 22 | `dashboard_manager.py:466`, `:2514-2522`, `canopy_constants.py:412-424` at `60ae1870` | :466 is `("slow-update-interval", None),` in `_GATED_POLL_INTERVALS`, under "apply-clamped only (CAN-000)". :2514-2522 is the watchdog comment ("continuously disabled", "must not re-enable DURING a legitimate fetch"). :412-424 is the strand-timeout comment, with the constant at :425. | MATCH | `git -C <canopy> show 60ae1870:…` |
| 23 | canopy#614 (`5c87f983`) changed three files and added no node-gated test; the node-gated tests on `main` | `git diff --stat`: `canopy_constants.py`, `dashboard_manager.py`, `test_poll_gating.py`, and the test file has no node or JS-engine call. `git grep 'shutil\.which(.node'` at `e9053227` and `60ae1870` finds f042 (2 files), f054, idle_dispatch_cuts, y4 and phase_b_bridge. | MATCH | as listed |
| 24 | `test_poll_gating.py:194-197`, "continuously ``True``" | verbatim | MATCH | `git show 60ae1870:…` |
| 25 | dash 4.2.0 `_callback.py:602`, `:640-645`: an all-`no_update` answer is a 200 | :602 is `has_update = _set_side_update(...) or has_output`; :640 sets `has_output = True` and :645 sets it to `len(output) > 0`. A 204 comes only from the PreventUpdate handlers (`backends/_flask.py:98-100`, `_fastapi.py:193-194`). | MATCH; Lane 11-A1's 204 reading is correctly refuted | the JuniperCanopy1 environment, dash-4.2.0 |
| 26 | The shim's docstring corrections | 0 `ON_PROP_CHANGE` records in either run. Empty-type disable records: 308 ; 305 (requests: 307 ; 304). In the renderer, `sideUpdate` (:746), `updateProps` (:7087-7092) and `notifyObservers`' `addRequestedCallbacks` (:7224) all dispatch through the thunk's own `dispatch`. | MATCH. 21 `AddRequested` actions dispatched outside a thunk do reach the wrapper, so the ledger's "inside a thunk" scope is right. | `types.py`, `sed` of the renderer |
| 27 | Synthetic check: "five fires … the check's rule asks only for one" | The watchdog case logged `fires` 5. Its rule is `len(r["fires"]) >= 1 and all(f[1] is True …)`. | MATCH | the jsonl; `…_synth_check.py:143-144` |
| 28 | The successor pairing gives the same 29 late releases; four self-tests pass on both runs | Old and new eviction lines and release summaries are identical (18 + 11). `--self-test` (a)–(d) are all True, "SELF-TEST PASS" twice. Grafted onto `1b7cf44b`'s oldest-first `analyze`, (c) and (d) FAIL and re-pair all 18 ; 11 evictions, so the tests can fail. | MATCH; the instrument is adequate | release trace; `selftest_on_old.py` |
| 29 | Margins: own releases 13–89 ms before their answers, late releases 0.4–2.0 s before the successor's | own 38–54 ; 13–89 ms; late 433–2,031 ; 704–1,688 ms | MATCH | release trace |
| 30 | Triage: 79 / 53 / 1 / 2 / 23, 7 open P1, 16 open P2; F-CANOPY-068 reads as P1; "else 5 P1 and 18 P2" | Identical. Open P1: 055, 058, 064, 065, 068, CASCOR-001, CASCOR-002. F-CANOPY-064's P1 rests on the manual, so 5 and 18 is right. | MATCH | `e2e_finding_triage.py --note` on the ledger at `b3c54692` |
| 31 | Plan §6.3: P1 means "breaks a documented behaviour" | `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:358-359` | MATCH | `git show b3c54692:…` |
| 32 | The trio's processes, "started 2026-09-22, were still the same after the second run" | Nothing in the repo records the reading taken then. Today the listeners on :8101, :8202 and :8051 have start times of 22 Sep 14:37:41, 14:37:52 and 14:38:00, and are still running. | MATCH as a fact (corroborated live); the original reading is UNTRACEABLE | `ss -ltnpH`, filtered; `ps -o pid=,lstart=,comm=` |
| 33 | `f058-census-v2/README.md` edits (trigger-lag wording; correction 3) | as rows 9, 10 and 19 | MATCH | README line 50 is stale (NIT 1) |
| 34 | The Round 1 record in `…_E2E-VALIDATION-EVIDENCE.md` against `2026-10-05_validator_reports_phase11_round1.md` | Verdicts: 11-A1 SOUND, the other four SOUND-WITH-FIXES. Every "(Lane …)" attribution matches the reports. The 204 refutation is correct. Slips: 11-A2, 11-A3 and 11-B2; 11-A1 and 11-B1 had none. Probes: 5 + 10 + 14 + 5 + 7 = 41. | MATCH | It leaves out that Lane 11-B1 rated F-CANOPY-068 P2, on the code comment, without having seen the CHANGELOG. That is now the rating's "else P2" branch, so no dissent is lost. |

**FINDINGS**

1. **NIT. The pass left two descriptions stale.**
   - **Quoted:**
     - `reports/e2e-canopy-2026-09-02/f058-census-v2/README.md:50`: `--self-test   # both known-answer mutations`
     - `util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py`, module docstring: "It takes the lane's measured timeline (the ``after`` of the last lane record at each millisecond, as the release trace reads it)".
   - **Evidence:**
     - At `b3c54692` the self-test runs four cases, (a)–(d), and `…_E2E-VALIDATION-EVIDENCE.md` now says "four known answers".
     - Both tools' `lane_timeline` now read only innermost records (`''` or `SET_LAYOUT`). The replay's module docstring still describes the enclosing-record reading that the ledger calls corrected.
     - The pass changed neither line: the README edits touch two other passages, and the replay's diff is `lane_timeline` only.
   - **Fix:** change the comment to "# four known-answer mutations", and the docstring to "(the ``after`` of each change's innermost record, as the release trace reads it)".
   - **Changes a number, disposition or action?** No. Only a count in a comment changes.

2. **NIT. Lag attributed to "the renderer's queue" that the transcript cannot attribute.**
   - **Quoted** (`…_E2E-VALIDATION-EVIDENCE.md`, Instruments): "For T-gate and T-mode that was the renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s to the next request. … (a trigger sent from Python then would still land 1.0–2.9 s into the flight)".
   - **Evidence:**
     - `t_ms` is the page time of the poll that found the open request (`2026-10-04_f058_census_v2_live.py:243`, `:251`).
     - T-gate's and T-mode's `set_props` go out later, in separate `page.evaluate` calls (`:253`, `:265`), and their page time is never logged.
     - The only logged page time of a driver action sent the same way is T-tab's first click (`:257`), at +993 ; +708 ms. That figure also includes the click's own handling in the page.
     - The paragraph's own 1.0–2.9 s bound reproduces only by charging that 0.7–1.0 s to the Python side (0.7 + 0.3 to 1.0 + 1.9). On that same model, up to 0.7–1.0 s of T-gate's 1.3–1.4 s would be the driver's, not the queue's.
   - **Fix:** "For T-gate and T-mode the transcript does not separate the driver's round trip from the renderer's queue: 1.3–1.4 s to the gate's write, and 2.1–2.5 s to the next request." Item 25's "timestamp every action in the page" would settle it.
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Whether `2026-10-05_validator_reports_phase11_round1.md` is verbatim, and whether the 41 archived probes are verbatim and what they leave out. I did not open the other lanes' scratch directories, to stay independent.
- The orchestrator's pid and start-time reading "then". Nothing archives it; only today's read corroborates it.
- Phase 9's observation about CI's six skips at `e9053227`. I did not fetch the CI logs.
- That the legs ran dash 4.2.0 at run time. I checked only the installed environment.
- How T-gate's and T-mode's lag splits between the driver and the renderer. Nothing logs it.
- I did not re-run the synthetic check (I read its jsonl and rule) and did not examine dash 4.4.1.
- My scripts (`myreader.py`, `myreplay.py`, `trig.py`, `horizon.py`, `stall.py`, `types.py`, `jitter_dist*.py`, `selftest_on_old.py`) exist only in `$S` on tmpfs. Copy them to `util/ad-hoc/` if they should be kept.

**SECRETS/PII:**
- No environment values, tokens, credential files or email addresses were printed, requested or sent.
- No git command that prints an author line was run: no `git show --stat` and no `git show <commit>` header. Git output was limited to hashes, subjects, diffs and file contents.
- `gh api` was filtered with `--jq` to tag, draft, prerelease, published_at and assets.
- The PyPI JSON print was limited to version, upload times and yanked. Its info block carries an `author_email` field, which was not printed.
- To check row 32, I read the local listening-socket table and `ps` start times for three pids. I connected to no port, printed no command line, and started or stopped nothing.
- No slips. I changed no repository file; all work was in `$S`.

---

## Lane 11-R2B (adversarial, on round 1's correction pass)

*agent `a75287b001193dc8b` · round 1 · last-assistant-text (not resumed) · 11662 chars*

**VERDICT: SOUND-WITH-FIXES.** The pass replays exactly: running `2026-10-05_phase11_ledger_round1_corrections.py` on copies of `1b7cf44b` reproduces `b3c54692` byte for byte, for both the ledger and the README. Every count and every innermost-record figure reproduces, and the triage tool reads F-CANOPY-068 as OPEN P1, giving 79/53/1/2/23 with 7 open P1 and 16 open P2. The pass did break or overstate four things: the owner's question and its fallback counts, F-CANOPY-058's new horizon, item 25's method, and the release trace's new pairing rule.

**TABLE** (ledger = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `b3c54692`)

| Correction | Result | Evidence |
|---|---|---|
| F-068 re-rated to "P1 if a shipped CHANGELOG promise counts…, else P2" (header, Summary, Rating, counts, record) | overreaches (F1) | Triage gives 7 P1 / 16 P2. The quote is at canopy `CHANGELOG.md:1221-1225` at `60ae1870`. It came from `06d8607e` (#624) and is in tag `v0.8.0`. |
| Innermost-record figures: 11.0–14.9 s, 0.3–3.6 s, 2,710/2,743 ms, replay 5–16/3–18, medians 9/7, random 1/1, zero-fire 94/500 and 102/500, 1–3.5 at 6,000/7,500 ms | holds | Corrected trace and replay re-run on both transcripts. 0 alternation breaks. `analyze` prints 2,746/2,803. |
| F-058 header rewrite | holds | Triage still reads P1 OPEN. The condition is the renderer's prune condition. |
| F-058 Status and trigger bullet: the renderer "makes the next request, 1.3–3.7 s after the re-enable" | breaks something (F2) | See F2. |
| 32 mid-request re-enables, 8 evicting; 13 of 21 that came more than a period early did not evict; four trigger kinds; 7 evicting fires, 6 cascades | holds | My `reenables.py`: 28 fires plus gate writes at 7,253 / 480,696 / 728,126 (run 1) and 478,476 (run 2). Run-1 726,055 and run-2 721,354 had nothing in flight. |
| Per-action trigger-lag attribution; item 25 "inside the page, from the shim's `AddWatched` hook" | overreaches (F3) | The numbers reproduce (1,336/1,367 ms; +2,148/+2,503 ms; clicks +993/+2,936 and +708/+2,313 ms). The attribution and the method fail, see F3. |
| Release trace: successor pairing and 4 self-tests; both readers on innermost records | holds here, with a new blind spot (F4) | Same 29 pairings as the old rule (diffed). Self-tests PASS on both runs. |
| 5.4 s longest request; drift with no fixed direction; fire gaps 20 of 26 within 0.3 s, all within 0.75 s except the clamp gap (1.3 s); T-mode row caveat | holds | Request 39's late release at 5,448 ms. Fire gaps computed from the fire times. |
| Phase 9 node-test correction; item 0's list; shim docstring; the 204 claim refuted | holds | canopy#614 touched 3 files. 6 node-gated test files at `e9053227`. `dash/_callback.py:602` reads `… or has_output`. |
| Trio processes "started 2026-09-22 … read then"; Round-1 Consensus record | mostly holds; omissions (F1, F5) | No pid or start-time artifact in the evidence directory. Verdicts, attributions and slips (11-A2, 11-A3, 11-B2) match the reports. 41 probe files. 0 email-shaped strings in the archived reports. |

**FINDINGS**

1. **MINOR: the owner's question and its fallback counts misstate F-065's condition, and treat F-068's promise as the same kind as F-065's.**
   - **Quoted:**
     - "F-CANOPY-065 and F-CANOPY-068 are P1 only if a shipped CHANGELOG promise counts as documented; if not, the counts are 5 open P1 and 18 open P2" (:10922-10923).
     - "whether a shipped CHANGELOG promise counts … which now decides two ratings" (:10907-10908).
   - **F-065's own condition is wider.** Its Severity bullet says its P1 holds if "a shipped CHANGELOG or design-plan promise counts" (:10130-10131), and Phase 10 put the question the same way (:10313). So if design plans count and CHANGELOGs do not, the counts are 6 P1 / 17 P2, not 5/18.
   - **The two promises are of different kinds.** F-065's promise is what the toast shows (:10126-10127). F-068's operative sentence describes an internal predicate on `metrics-store-interval.disabled` (`CHANGELOG.md:1222-1223`). Every earlier documented-behaviour P1 in the ledger rests on something the user sees: F-056 (:9066), F-057 (:9121), F-064 (:10070) and F-065.
   - **For P1:** #624's body shows this section renders the published v0.8.0 Release notes, and "fast recovery would reopen the eviction window" is broken by the 7 evicting fires.
   - **For P2:** §6.3's P2 explicitly covers drift, and a mechanism statement that drifted from the code is drift.
   - **Decision:** the conditional P1 is defensible, but a ruling on F-065's kind of promise does not settle F-068's. Also, Lane 11-B1 rated F-068 P2, arguing a code-level contract is only drift (round-1 reports :270), and its brief never mentioned the CHANGELOG. The record cites 11-B1 only on the fold question (:10872).
   - **Fix:** restate Phase 10's question with both sources, plus a second limb: does a CHANGELOG description of a mechanism count as "behaviour"? Give the counts per branch (5/18, 6/17, 7/16), and record 11-B1's P2 as dissent.
   - **Changes a number or action:** yes (fallback counts; owner question).

2. **MINOR: F-058's corrected horizon labels the wrong event and contradicts F-068's Effect.**
   - **Quoted:** "the renderer makes the next request, 1.3–3.7 s after the re-enable" (:9138) and "the renderer then makes the next request … 1.3–3.7 s" (:9153-9154).
   - **1.3–3.7 s is when the next request entered `watched`.** That is how :10659-10660 words it correctly. The shim never sees `AddRequested`. The eviction marks the making, and it comes 21–397 ms before the successor's W across all 29 evictions.
   - **The 8 evicting re-enables evicted 1,214–2,392 ms after the re-enable.** The page-load gate write at 7,253 evicted at 8,467, which is +1,214 ms, below the stated 1.3 s.
   - **For the other 24 the race was already decided:** the in-flight answer landed +104 to +2,164 ms after the re-enable.
   - **The top three values come from the census's own clicks.** The next requests at 3,365 / 3,553 / 3,663 ms followed the fire at 476,732 (0.6 s before T-tab fired) and the two T-tab second-click writes.
   - **Two ranges for one quantity.** F-068's Effect (:10751) and :10656 give "next request is made, 1.4–2.4 s".
   - **Brief item 3:** the horizon is a property of this page and host (load 1.9–4.6 on 16 cores), with the shim on every dispatch (165,942 in run 1) and no uninstrumented control. It is scoped "in those runs", so no sentence states it as general. But F-058's durable trigger bullet now carries it, mislabelled, and "What the evidence cannot support" (:10911) omits the instrument's presence.
   - **Fix:** say the next request was made 1.2–2.4 s after each evicting re-enable, and that after the other 24 the answer landed first (0.1–2.2 s). Keep the W range only in :10660, with its T-tab top noted.
   - **Changes a number:** yes.

3. **MINOR: item 25's method can reorder what it measures, and the lag split under it is not measured.**
   - **Quoted:** "Fire each inside the page, from the shim's `AddWatched` hook" (:10944) and "For T-gate and T-mode that was the renderer's queue … For T-tab most of it was the driver's own" (:10827-10830).
   - **Reordering.** `AddWatched` is dispatched by the executing observer (`dash_renderer.dev.js:2676`, dash 4.2.0) inside `StoreObserver.notify`, a redux subscriber (:358). `notify` skips observers still marked `triggered` (:376-382). `set_props` dispatches synchronously through the same store (:3860-3891). So a trigger fired synchronously from the wrapper reaches the running observers only on a later dispatch. Also, the wrapper reads the enclosing dispatch's `after` only after the trigger has run (shim :84 then :97).
   - **No timestamp supports the split.** No driver-side or `set_props` timestamp exists. T-gate's and T-mode's `set_props` took the same `page.evaluate` path as T-tab's clicks (live.py :251-265), and T-tab's first click came 0.7–1.0 s after the trigger fired. The corrected T-mode row itself says the cause of the next request is unknown (:10614). Its answer-to-next-W gap (1,519 / 1,417 ms) sits at the 5th–7th percentile of tick gaps, so the data cannot decide. If the 1.3–1.4 s were really the renderer's queue, firing in-page would gain nothing for T-gate.
   - **Fix:** schedule the trigger as its own task (e.g. `setTimeout` 0), timestamp its execution in the page, and validate on the synthetic check first. State each lag without attributing it.
   - **Changes an action:** yes (item 25).

4. **MINOR: the new pairing rule can hide the case the brief names; the ledger does not say so.**
   - **Quoted:** "It pairs each late release with the evicted request whose successor is the request in flight" (:10803).
   - **Mutation (run 1):** I moved request 177's release (902,896) to 905,500, inside 179's flight and after 178's eviction, and dropped 178's release (905,789). That simulates 177's response landing after its successor ended.
   - **New rule:** "req 177 → none; req 178 → release @905500 under req 179 (flight 2708 ms)", 0 unassigned. That looks exactly like the docstring's "limit of the log".
   - **Old rule:** "req 177 → … under req 179 (flight 5610 ms)", so the anomaly was visible. Self-tests (c) and (d) cannot exercise this case.
   - **Innermost filter.** It keeps only record types `''` and `SET_LAYOUT` (`release_trace.py:84`). A change logged only by a non-thunk record would be dropped: the trace counts it as an alternation break and carries on, and the replay does not check at all.
   - **Not triggered here:** 29/29 paired, 0 none, 0 unassigned, 0 breaks. It matters for item 24 and for slow pages.
   - **Fix:** flag a "none" followed in its run by a paired release, make alternation breaks fatal, and state the limit in Instruments.
   - **Changes a number:** no. **Action:** minor (item 24's instrument).

5. **NIT: text the pass left stale.**
   - README :50 still says "both known-answer mutations"; there are now four.
   - README :25 still says "the same before and after it", while the ledger now has different wording. Neither has an artifact behind it.
   - `alias_replay.py:21-22` docstring still describes the old timeline rule.
   - Status :9135 says minutes were reached "only in Lane B's synthetic runs", but 11-B1's 90 s repro sits in the same entry. The header's "synthetic repros" is right.
   - The record's change list omits the 6,000/7,500 ms medians (2 to 4 → 1 to 3.5).
   - **Changes a number:** no.

**WHAT YOU COULD NOT CHECK**
- Whether an in-page trigger actually reorders events. I read the dash 4.2.0 source only and drove no browser.
- Whether the 0.7–1.0 s click delay is the driver's or the page main thread's. No timestamps exist to split it.
- dash 4.4.1's dispatch shape. It is not installed.
- The trio processes' pids. Not touched, and nothing is archived.
- The synthetic check. Not re-run, because it starts apps.
- A full sweep of the open P2s against canopy's CHANGELOG. I spot-checked F-060's "producer's own sentence … survives to the modal" and found it inconclusive.

**SECRETS/PII:** No environment values, tokens or credentials were printed or sent. I never ran `git show --stat` and printed no author line. One slip: `git log --format=%B -1 06d8607e` (canopy) printed that commit's body, whose Co-authored-by trailer holds a generic bot no-reply address, not the owner's. It went to local output only and was not repeated. `%ad` printed author dates only. Email-shaped strings in the archived reports and in the pass's diff were counted at 0 and never printed. I stayed read-only, wrote scratch files only in my `mktemp -d` directory, and touched no ports or services.

---
