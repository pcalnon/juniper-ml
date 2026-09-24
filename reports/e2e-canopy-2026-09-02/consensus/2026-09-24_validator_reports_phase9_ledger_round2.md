<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 2: Lanes R2-F and R2-B, verbatim

Round 2 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit acf1a93a, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R2-F re-derived the whole phase artifact-first; Lane R2-B attacked round 1's corrections (e624c281..acf1a93a), including the new F-CANOPY-058 census. Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR2F_phase9_ledger_brief.md and laneR2B_phase9_ledger_corrections_brief.md. The orchestrator's re-derivations and the fix pass are recorded in the ledger's Phase 9 consensus record and in util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py.

## Lane R2-F -- full read, artifact-first

*agent `a437541f6019985b0` · round 1 · last-assistant-text (not resumed) · 44197 chars*

**VERDICT: SOUND-WITH-FIXES.** Almost every number, SHA, timestamp and line citation in Phase 9 re-derives exactly from its primary artifact. Two MAJOR defects need fixing before this lands:

- **The merge record leaves out what actually released the merge.** CI failed on `5e52debb`, and the owner's account re-ran it at 01:22:32Z; the merge followed at 01:38:02Z.
- **F-CANOPY-056's claims about the player's session view only hold for sessions built by hand.** With cascor's real `/replay` payload, `render_session` raises `KeyError: 0`.

Nineteen MINOR findings follow, several of which change an action or possibly a disposition: the open P1 count may go from 5 to 6, and there may be a new finding. Under procedure §4 the corrections need another round.

Path roots used below:
- **ML** = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda`
- **CAN** = `/home/pcalnon/Development/python/Juniper/juniper-canopy`
- **CAS** = `/home/pcalnon/Development/python/Juniper/juniper-cascor`

Report abbreviations:
- **r1 / r2 / r3** = `ML/reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round{1,2,3}.md`
- **lr1** = `…/consensus/2026-09-24_validator_reports_phase9_ledger_round1.md`
- **PS** = `ML/reports/e2e-canopy-2026-09-02/phase9-scratch/`
- **TR** = `ML/reports/e2e-canopy-2026-09-02/transcripts/`
- **T259** = the authoring session's transcript `259b4d16`

Canopy line numbers are at `e9053227` and cascor line numbers at `0e016a7c` unless stated otherwise.

## TABLE

### Summary (8486–8521)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8488 | #676 merged 2026-09-24T01:38:02Z as `e9053227`, before this phase landed | timeline `merged` 01:38:02Z (commit date 01:38:01Z); origin/main's ledger has no Phase 9 | MATCH | `issues/676/timeline`; `git show origin/main:…` |
| 8489–90 | held for round 1 (PR comment), then for this phase to land first (PR body only) | comment 19:44:38Z names round 1 + green checks; body L15/L89 "lands before this PR merges" | MATCH | timeline; `gh pr view --json body` |
| 8490–91 | no session readied or armed it; all were "rate-limited or idle" | 0 tool calls 21:41:02Z–01:40Z; no executed ready or arm of canopy#676 in 950 transcripts | MATCH (basis incomplete, F11) | activity script; scans |
| 8491–92 | landed change "byte-identical" to `4b4cfb16` | the two raw diffs (468 lines each) differ in one `index` line only | MATCH | `cmp` |
| 8492–94 | rebuilt from `668380ec`; `ce78e0de` vs `3a6dea95` (the PR's parent then): STRUCTURE/SESSION PASS, LATENCY INCONSISTENT | cherry-pick at 19:18:21Z; `f4d864df^` = `3a6dea95`; JSON verdicts PASS/PASS/INCONSISTENT | MATCH | T259; git; rebuilt JSON |
| 8495 | "prose, plus two test-only changes" | `key=str` (`2fa134f8`); dict-id refusal (`4b4cfb16`) | MATCH (N55) | git diff |
| 8496–97 | round 1 refuted four claims | stop: Lane B #1 (and Lane A); weights: Lane B #2; "2 Hz": Lane A instrument 6; pooled: Lane A | MATCH | r1 :42, :50, :57, :81, :100 |
| 8498 | round 2 found what the corrections broke | "What fails is the record": 1 MAJOR + 6 MINOR | MATCH | r2:11 |
| 8501–13 | F-055 bullets (census rule unchanged; drive non-discriminating; DO-NOT-MERGE; four triggers; B1 added the 4th) | see F-055 rows | MATCH | r1 L248–301; lr1 L176–182 |
| 8515–18 | F-056/057 came from the cuts' round-1 adversarial lane; F-056 widened and re-rated P1 | Lane B findings 1–2 (r1:81-111); B1 finding 4; `e624c281` had P2 | MATCH | reports; triage |
| 8519–20 | F-058 came from F-055's round-1 Lane B; "one mid-request re-request or re-enable starts an eviction cascade" | origin MATCH (r1:244-262); 2 of 5 mid-request fires evicted nothing | MATCH / MISMATCH (F18) | `PS/f055_r1_laneB/run_watchdog_r3.json` |
| 8521 | all three re-derived in source | re-derived here; the orchestrator's act is unrecorded | MATCH / UNTRACEABLE (act) | rows below |

### The rebuild, falsification and suite (8525–8543)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8525–27 | `668380ec` on `723ee812` (a local merge on #670's branch), neither pushed; cherry-picked in a fresh worktree as `ce78e0de`; two conflicts | all three return 422 on GitHub; `723ee812` merges origin/main into `fix/f054-replay-block-clientside` (#670's headRefName); worktree 19:18:18Z; CONFLICT CHANGELOG + metrics_panel.txt | MATCH | `gh api …/commits/<sha>`; `gh pr view 670`; T259 |
| 8528–30 | Y4/Y8/Y7 (#671) kept verbatim; cuts entry below; the branch's F-054 entry dropped | 3a6dea95 CHANGELOG L107/117/127; diff is a pure +27 at L136; the 46-line branch copy was dropped, main's 79-line entry kept | MATCH | git |
| 8531–33 | snapshot regenerated; one 76-character deletion | rm → baseline 19:19:33Z → re-run 19:19:44Z; 7678→7602 chars | MATCH | T259; difflib |
| 8534 | diff identical to `668380ec`'s outside hunk positions (Lane A: cmp 0, same sha256) | 311 stripped lines each; cmp 0; sha256 `718958221bd4…` for both; r1:14 | MATCH | re-run |
| 8536–38 | 7 of 9 fail on `3a6dea95`, each on its own assertion; CLASS names exactly `['metrics-panel-update-interval']`; the premise pins pass on both | 7 FAILED / 2 PASSED; the list is exact; pins pass | MATCH | `PS/cuts_r1_laneA/m3_parent.log` |
| 8540–43 | 6806 passed / 4 skipped / 0 failed; collection 6810; Lane A attributions; archive | progress characters `.`=6806, `s`=4; 6810 across 287 files; r1:23, :66; archive = tmpfs original | MATCH | `PS/orchestrator/cuts_full_suite.log`; `m6_collect_ce78.txt` |

### Live check, run 2 (8544–8579)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8544–45 | rule unchanged; `:8055` 3a6dea95, `:8056` ce78e0de | script blob `c3c9ad57` is identical at ada8e50c, 51993b37 and HEAD; per-window SHAs agree | MATCH | git; rebuilt JSON |
| table | C1 7.12/109/present/no,5 · X1 3.91/170/absent/yes,0 · C2 5.34/127/7 · X2 5.42/136/0 · C3 5.28/131/7 | 7115.1 · 3912.6 · 5336.9 · 5415.8 · 5275.5 ms; every other cell identical | MATCH | rebuilt JSON |
| 8555–58 | X/C 0.79; console errors 0; SESSION at its floor (1.7 s / 5 ticks; 2.5 s / 0) | 0.78932 (mean/mean); rule re-applied (X2 > max(C2, C3)); 0 errors ×5; 1.7/5/2.5/0 | MATCH (N24) | script L188–206 |
| 8559–61 | band 0.60–0.85; CONSISTENT predicted; X2 +1.48% vs C2, +2.66% vs C3; not repeated | both predictions in the docstring; +1.478%, +2.660%; only two live-check JSONs exist | MATCH | docstring |
| 8562–65 | C1 outlier (Lane A); 32–40 s; ~32 s command, first read at 40 s; suite 19:22:18Z–19:30:05Z; without C1, 0.88 | log mtime 19:30:05.5Z; command 19:30:37.9Z (+32.4 s); read_at 19:30:45Z (+40 s); earlier health read 19:30:39Z; 0.87901 | MATCH (N22, N23, N26) | T259; log; JSON |
| 8566–70 | no load field; Lane A NO ARTIFACT; 7.89 at 19:30:31Z; 13.10 ten minutes in; clamscan 84.2/80.8 (lifetime); other sessions' tests | uptime read 19:30:31.055Z; 13.10 at 19:40:52Z; pcpu 84.2 (etimes 117230 s) / 80.8 (30831 s); two pytest processes 7–9 s old | MATCH | T259; r1:61 |
| 8571–73 | Phase 8 pair `668380ec`/`723ee812`; not an ancestor of 3a6dea95; "three of four windows"; one X of two beat both neighbours | run-1 JSON C=723ee812, X=668380ec; merge-base exit 1; 78c057e2 reads "three of four alternating windows across two live checks" | MATCH (N25) | `TR/2026-09-23_idle_cuts_live_check.json` |
| 8575–79 | run 1 UNTRACEABLE (Lane A); `ada8e50c` 16:26:49Z, ~2 h 52 min after; `51993b37` 17:07:01Z, ~3.5 h; run 2 traceable | ada8e50c adds both files, is 422 on GitHub and sits only on local branch `worktree-partitioned-twirling-stream`; C1 read 13:34:45Z; +3 h 32 m; A1 G6 and A2 R1.i | MATCH | git; r1:65; lr1:36, :79 |

### #676 review rounds (8580–8659)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8580–84 | round 1 on f4d864df/ce78e0de; Lane A M1–M6 via `/proc`; M1c wording MISMATCH; M6 indirect | f4d864df `src/` = ce78e0de; r1:13-23, 43-47 | MATCH | rev-parse; r1 |
| 8585–94 | four wording corrections; four instrument gaps | Lane A flagged them (:57-64) and listed more gaps (PROBE id, launch-time git_sha, store ticks) | MATCH (N34) | r1:26-47 |
| 8595–97 | raw records rule out three gaps; the fourth argued improbable "since the `disabled_after_s` read…" | X windows' after_10s is present, n:0, disabled; the stated reason is not in Lane A's text | MATCH / attribution MISMATCH (N27) | JSON; r1:40 |
| 8598–8601 | Lane B MERGE-WITH-FIXES; MAJOR stop; MINOR weights; `_weight_drain_gate` fixed | report; 1 hit at f4d864df, 0 at 2fa134f8/4b4cfb16/e9053227; Lane A also found stop | MATCH (N28) | r1:50-56, 77-111 |
| 8602–03 | `conf/app_config.yaml:170,181`, `docs/USER_MANUAL.md:1344`; predates PR | `metrics_update_interval_ms: 1000` / `update_interval_ms: 1000` / `update_interval_ms: 2000`; unchanged since 3a6dea95; no `src/` reader | MATCH | git |
| 8604–09 | `key=str`; 178 callbacks, single writer; `@hash` renderer lines; dead since 2025-12-12; 17 Intervals + injected one | in 2fa134f8; probe re-run on a ce78e0de extract gives 178 and one writer; dash **4.2.0** splitIdAndProp :5895, getReadyCallbacks :1633; b64f6dfa (12-12) and sibling a7ca240f (12-04); 17 sites; injection output only in tmpfs | MATCH (N33, N36) / NO ARTIFACT (injection, F17) | git; renderer |
| 8610–17 | 2fa134f8 = prose + `key=str`; "Lane A measured … 5–7 ticks per 10 s" | only code change is key=str; C windows 5,7,7 (run 2) and 5,6,7 (run 1), read from the JSON | MATCH | git; JSONs |
| 8618–23 | B2 MERGE-WITH-FIXES; could not check the load or C1's start; MAJOR remedy "ledger first" | B2's limit was "C1 started 40 s after the suite"; its remedy also required committing the run-2 transcript (first entered git in 5a0e4ea9, after the merge) | MATCH / PARTIAL (N31, N32) | r2:11, 27, 105, 115 |
| 8625–31 | "five places"; four comments incl. "set by g-3's `_emit_frame`"; COMMIT_MESSAGES; signed 4b4cfb16 on 0254a7ec | **six** places at 2fa134f8; four comments ("…_ReplaySession._emit_frame"); repo setting COMMIT_MESSAGES; 4b4cfb16 verified, parent 0254a7ec, tree = 040dc5c1's | MISMATCH (N29) / MATCH (N30) | git grep; gh api |
| 8632–36 | 0.88 and 0.80 without C1; dropped from CHANGELOG; dict-id refusal; "32–42% cut" | 0.8790, 0.8042; absent from 4b4cfb16 CHANGELOG; A/B W −41.9 / −32.3 | MATCH | JSONs; `TR/…timer_park_ab_8055_run{1,2}.json` |
| 8637 | "All were applied." | tree and commit only; the PR body still has corrected text | MISMATCH (F10) | PR body |
| 8637–39 | 8 files / 168 passed (no SHA); pre-commit on 4 files, filtered; B3 clean on all 8 | command at 20:35:21Z names 8 files; "168 passed"; grep printed nothing; precommit_head.txt clean (no file list) | MATCH | T259; `PS/orchestrator/cuts_r2_tests.log`; `PS/cuts_r3_laneB3/precommit_head.txt` |
| 8640–43 | B3 MERGE-WITH-FIXES; code NITs no-action; 52+111+321; 7 of 9 on 0254a7ec | r3:11, 39-45; 52 in head_run.txt; **111/321 only in tmpfs**; parent_run 7/2, blobs = 0254a7ec | MATCH / NO ARTIFACT in archive (F17) | PS/cuts_r3_laneB3 |
| 8645–48 | "(two rounds; prose corrections only)" false; PR body 7 files / old parent / two commits; fixed 15 s after B3 read | in 4b4cfb16's message; B3 read 20:39:55.6Z, edit 20:40:10Z (14.4 s, which fixed more) | MATCH (N35) | GraphQL userContentEdits |
| 8650–55 | `replay_player_panel.py:75`; message/name; `ws_dash_bridge.js:113-115`; 45%; 056/057 unpushed; guard only on class test | true at 4b4cfb16 (identical at e9053227); 3.0/6.6; `:120` KeyError, `:127` unhashable | MATCH | git |
| 8656–59 | §4 "changed no disposition"; round-4 decision; no round 4 | B3 marked both MINORs "number: yes; action: yes"; the decision is not in r3; no round-4 file | MISLEADING (F9) / UNTRACEABLE / MATCH | r3:23, 37 |

### The merge, out of order (8660–8716)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8660–62 | actors pcalnon; app null; two retitles | true for events that have an actor; renamed at 20:08:53Z and 20:38:41Z | MATCH (N47) | timeline |
| table | 19:44:37 draft (+comment 1 s later) · 20:38:41 force-push 4b4cfb16 · 22:28:04 ready · 22:28:09 e581b821 · 22:28:12 auto-squash armed · 22:29:31 5e52debb · 01:38:02 merged | every timestamp and SHA exact; e581b821 parents 4b4cfb16 + 9cdfcad4 (#677); e9053227 body = 4b4cfb16's + "(#676)" + moved trailer | MATCH | timeline; git |
| (absent) | — | CI run 35928632707 on 5e52debb: attempt 1 **failed** (macOS 3.12 unit job 22:40:57Z, Quality Gate 22:42:30Z); attempt 2 started **01:22:32Z by pcalnon**, success 01:38:03Z | OMITTED (F1) | `actions/runs?head_sha=…`, `attempts/1` |
| 8671 | 5e52debb came 10 s after #678 moved main | #678 merged 22:29:21Z as 05f2dfc2 | MATCH | timelines |
| 8675–78 | every session active before 21:41Z hit the limit 21:30:11–21:41:01Z; no tool call 21:41:02Z–01:40Z; the only entry is the refused prompt at 00:07:23Z | 259b4d16 and 4 subagents (idle since ≤21:25:49Z) hit nothing; 0 tool calls MATCH; a queued task notice also exists at 21:53:09.035Z | MISMATCH (F11) / MATCH | activity script; entry scan |
| 8679–82 | `gh pr ready 676 --undo` only; handoff prose; last entry 21:01:29Z; 87 min; idle until ~03:27Z; b54e3b3f 21:00:59Z | tool_use 19:44:36.556Z; handoff L71; 21:01:29.583Z; 86.6 min; 03:26:51.9Z; b54e3b3f lines 18-19 — but it is **not an ancestor of acf1a93a** (rebased copy f6861234) | MATCH (F16) | T259; git |
| 8683–85 | no executed ready/arm of canopy#676; the only other match is cascor#676 | cascor#676 `--squash --auto` at 01:34:34Z/01:34:58Z on 09-23 | MATCH | scans |
| 8686–90 | nine PRs 21:47–22:51Z; ready→arm 4–8 s (2059, 2032, 676, 428, 431, 434); ml#2066 armed only; #678 and dc#212 direct | gaps 4, 7, 8, 4, 4, 5 s; drafts from bc31e993, e6c1cb6d, 259b4d16; the account kept acting until 01:22Z | MATCH / incomplete (F1) | timelines |
| 8691–92 | only #676 had an update-branch between ready and arm, "where its 8 s comes from" | true; ml#2032 took 7 s with none | MATCH (N46, N54) | committed events |
| 8693–97 | comment's condition held; checks done by 20:59:25Z | 27 success + 1 skipped, last 20:59:25Z; 5 neutral Cursor runs came after the ready | MATCH | check-runs |
| 8700–02 | diffs equal outside index/hunk lines (445 lines, cmp 0); #677 and #678 overlap only in CHANGELOG | 468 − 8 − 15 = 445; sha256 `164e2bf6…` for both; #677 overlaps nothing | MATCH (N45) | scratch; gh |
| 8703–11 | four statements in e9053227's message; 3.0 of 6.6 = 45%; c0530279 is "#670's head" with the parent's layout; ws `:113-115` | all four verbatim; drain 2.0 + metrics-panel 1.0; 19 identical Interval declarations at c0530279/3a6dea95/0254a7ec/05f2dfc2; c0530279 is #670's **first** commit (final head bc357d09); line 115 | MATCH (N44) | git; `TR/2026-09-23_interval_census_c0530279.json` |
| 8712–16 | PR body stale; dangling citation | body last edited 20:40:10Z; only CHANGELOG.md:161-164 carries "in the juniper-ml E2E evidence ledger" | MATCH (N48) | gh; git grep |

### F-CANOPY-055, first fix (8718–8872)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8720–27 | 884d22fb on ce78e0de (Phase 8's direction); only Input status-bar-interval with `running=[(Output(lane,"disabled"),True,False)]`; (lane, None); per-lane watchdog, 30 s | parent ce78e0de; ledger L8302-8310; exact; `STATUS_BAR_STRAND_TIMEOUT_MS=30000`; separate `__…DisabledSince` clocks | MATCH | git diff; ledger |
| 8723–25 | the commit claimed the clamp "reaches" it and the tab gate never writes it; the fused gate writes it every fire | commit says the clamp "**silences**" it; the gate returns `clamped \|\| tab-mismatch` with `prevent_initial_call=False` | MATCH (N43) | 884d22fb:2479-2497 |
| 8729–37 | 7 tests; subclass + node + separate clocks; one rider; 19 of 94 fail, 75 pass; node test passes both | 5+13+1 = 19 of 7+45+42 = 94; `["handle_button_timeout_and_acks"]` | MATCH | `PS/f055_r1_laneA/parent_junit.xml` |
| 8738–40 | 6823/4 = 6806 + 17; no lane ran it; AST +7, +10, +0 | `.`=6823, `s`=4; ran 20:04:33Z; plain count gives +7/+2/+0; +10 only if inheritance-aware | MATCH (N42) | `PS/orchestrator/f055_full_suite.log` |
| 8741–44 | collection-time defect; per-test lookup; F-029 trap | 19:46:00Z "ERROR collecting … STATUS_BAR_STRAND_TIMEOUT_MS"; `_timeout_ms()`; the module's comment names the F-CANOPY-029 trap (test_poll_gating.py:48-52) | MATCH | T259; 884d22fb |
| 8745–49 | predictions before each run; "the script entered git after the runs"; ahead "at a window's edges" | Edit 19:50:15→run 19:50:25; Edit 19:55:05→run 19:55:08; **script in git since 51993b37 (17:07Z)**; Lane A: edge **or** network failure | MATCH / MISMATCH (F12, N38) | T259; git |
| census table | 30 · 31/0 · 0 · Stopped·0 · NEVER; 7 · 9/8 · 7 · Completed·76·5ms · VOID; 20 · 20/20 · 19 · APPLIES | every cell identical via the AST-extracted `_baseline_verdict` | MATCH | 3 census JSONs |
| 8757–67 | ≥10 predicted; ~7.5 s, 7.4–8.7 s; ~8.6 s = mean gap; completeJob before apply; F-035 5.5–7.3 s; 150 s; 12–25 | docstring L68/L78-80; 7.50/7.50, medians 7.37/7.47, means 8.69/8.04, 60/7 = 8.57; renderer :970-971; ledger L6972 | MATCH (N37) | JSONs |
| 8768–83 | drive; DEMO_MODE opt-in; cascor URL to nothing; drive table (13.0/7.8/137→143; 19.7/2.7); warned in advance; 18.5 s | `${CANOPY_VERIFY_DEMO_MODE:-0}`; `…CASCOR_SERVICE_URL=http://127.0.0.1:9`; identical via `_verdicts`; caveat written 19:35:39Z, run 19:59:28Z; 10 "Stopped" samples to 18.5 s | MATCH (N43) | drive JSON; T259 |
| 8785–95 | Lane A: no MISMATCH; 19; AST; /proc; six mutations; (iv) name collision; (iv_b); (v) node only | r1 L175-194; mut junits (i)1 (ii)4 (iii)2 (iv)9 "found 2" (iv_b)1 (v)2 node (vi)9; 78c057e2 differs only in CHANGELOG | MATCH | `PS/f055_r1_laneA/mut_*` |
| 8796–8813 | Lane A's corrections as 7a4a2e33; "one cycle" is the orchestrator's; 4–7 s p50; 20/20 | in Lane A's report **except** "Shared with #613…"; port/DOM fixes were made by sed in juniper-ml at 20:30:28Z | MATCH / attribution gap (N40) | r1:229-237; git |
| 8814–27 | Lane B BLOCKER 1; completeJob :925-937; runningOff :966-986 | dash 4.2.0 (JuniperCanopy1); calls at 966/970/979/983; no currency check | MATCH | renderer |
| 8828–32 | 7 of 7; 0 of 51; 4 of 4 then 0 of 28 | report only | NO ARTIFACT | r1:271-275 |
| 8833–41 | 352 s; 5 fires/240 s, 3 evicting, 17 of 56; 0 of 21; 37–44/h | 352.2 s re-created (seed 55); fires 57.8/92.8/152.8/187.8/232.8 s, 56 req / 39 applied; 0 of 21 report-only; 44.0/37.6 per h re-created (evicting 32.8/29.4) | MATCH / NO ARTIFACT (0 of 21) | archived scripts; run_watchdog_r3.json |
| 8842–48 | 0 of 24 after release; `test_poll_gating.py:406-408`; not a slowdown; 200 parse | after_release 24/0; :406-408 at 884d22fb (e9053227 :311-313); `res.json().then` has no catch (:939) | MATCH (N41) | run_apply.json |
| 8849–58 | could-not-refute list; CI's six skips, none the node test; no setup-node | r1:322-333; job 107457612196 "6870 passed, 6 skipped, 4 deselected" (skips listed, none poll_gating); ci.yml has no setup-node | MATCH | CI log |
| 8859–61 | no tab switch (default tab), no Apply, watchdog armed, mount write fired | `active_tab="metrics"` (884d22fb:1889); gate `prevent_initial_call=False`; the mount write itself is unrecorded | MATCH (source) | source |
| 8862–63 | P(no fire in 210 s) ≈ 0.15–0.18 "at that rate" | 37–44/h gives 0.116–0.077; 0.15–0.18 needs 29–33 **evicting**/h (A2) | MISMATCH (F3) | Poisson; lr1:118 |
| 8864–72 | 28 of 29; 27 delivered; direction; PR not opened; branch 884d22fb/cf6fb1dc/7a4a2e33 | 8+20, 9+20, 7+20; no PR; remote branch 404; local log | MATCH | gh; git |

### F-CANOPY-056 (8876–8911)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8876 | "the player stays in its session view" | with cascor's real session, `render_session` raises | MISMATCH (F2) | below |
| 8878–83 | `if data: new.update(data)`; stop branch only on an empty response; envelope passed through | replay_player_panel.py:839-875; `:376-377`; main.py:3021-3040; adapter :2368-2384; client 0.8.0 client.py:565 | MATCH | source |
| 8884–86 | round 2 corrected round 1's attribution; echo under data/result; `'snap_A'` kept | CAS routes/snapshots.py:455-503, manager.py:6085; probe reproduces; the echo attribution was in the round-1 **corrections** (2fa134f8), not Lane B's report | MATCH / MISMATCH (N49) | r2:47-53 |
| 8887–96 | REPLAYING view kept; slider write-back; B1: speed(−5)→1.0, seek(40)→0, play→None, stop kept id; `{status,data,meta}`; F-013 class | overlay MATCH; ResponseEnvelope (models/common.py:60-73); negative speed documented (USER_MANUAL.md:758); with a real `confirm_snapshot_op` session: KeyError at :532, and `playing` stays False | MATCH / UNTRACEABLE for the real payload (F2, N52) | probe; source |
| 8897–99 | P1 per plan §6.3; manual documents the readouts | plan :357-360; USER_MANUAL.md:757-758 | MATCH | `ML/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` |
| 8900–07 | model select rebuilds the tab bar, empty session, disabled drain (Lane C); test coverage; predates #676 | :3482, :2794, :2740-2742, :2604; tests :250-252, :273-277; `b8618602` (2026-05-02); Lane C report untracked, written after the freeze | MATCH (source) / UNTRACEABLE (F7) | source |

### F-CANOPY-057 (8913–8938)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8915–21 | `weights_at` only in unit tests; `_emit_frame` has no weights; `_to_dashboard_metric` fixed key set; three consumers | CAS manager.py:1182, tests :275, :284, `_emit_frame` :1198-1235; adapter :1942-1972; decision_boundary.py:237, network_evolution.py:164, panel :601-616 | MATCH | git grep |
| 8922–30 | #187 07:31:04Z (d85c9ddd); #190 20:05:12Z (dbc25277); 13 min after #189; 3 ahead / 512 behind; local-fetch artifact; `metrics["weights"]` | #189 merged 19:52:10Z; compare 0e016a7c…dbc25277 = 3/512; absent locally, present on GitHub; the diff adds it | MATCH (N51) | gh |
| 8931–35 | P2 "because the canopy follow-up corrects the docs" | the follow-up is unpushed with no PR; USER_MANUAL.md:764 and REPLAY_V2_FAQ.md:253 still promise the stream | PARTIAL (F7, F8) | git; gh |
| 8936–38 | #676's comment records the two latent gaps | replay_player_panel.py:576-585 | MATCH | source |

### F-CANOPY-058 (8940–8986)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8940, 8950–51 | "any" mid-request re-request or re-enable starts a cascade; "keep evicting" | 2 of 5 fires evicted nothing; 2 of 3 cascades ended by themselves | MISMATCH (F18) | run_watchdog_r3.json |
| 8942–47 | #613 guard; completeJob paths; 4.2.0 lines; lock 4.4.1 at `:979-991`; 200 parse | :4710-4719; `requirements.lock:32 dash==4.4.1`; in 4.4.1, 979-991 is the definition only (calls at :1020/:1024/:1033/:1037) | MATCH / PARTIAL (N50) | renderers |
| 8948–57 | re-enable restarts the timer; gate writes Boolean(apply-in-flight) at tab/Apply-end/mount; watchdog 5 s | dcc handleTimer; :2464-2485; :2515-2542; canopy_constants.py:371, 425 | MATCH | source |
| 8953–55 | mount write qualified | Lane B's own archived mount-write run (23/23, 0 fires) is not cited | omission (F4) | run_watchdog.json |
| 8958–63 | second Input; getUniqueIdentifier; qualification 3; B1 0/45 ×2 vs 23/23 ×2 | :4713, :4702-4705; renderer :1715-1728; B1's figures are report-only (tmpfs app.log fits request counts only) | MATCH / NO ARTIFACT (F17) | lr1:180-183 |
| 8964–72 | clamp defeat; three raw outputs + scripts archived; six figures unbacked; Phase 7 item 7 / Phase 8 item 6 | :931-933; 3 JSONs byte-identical to tmpfs; the six = the README's four + 7 of 7 + 0 of 21; ledger :7853-7856, :8454-8456 | MATCH (N53) | cmp |
| 8973–82 | production `no_update` conditions; F-055 feeder always returns data; "every response after the first is a 204" | dashboard_manager.py:7841-7842, :7847-7848, :7905-7906; no status is recorded anywhere | MATCH / NO ARTIFACT (F21) | source |
| 8983–86 | fix directions | Lane B's; the second-Input clause is B1's | MATCH | r1:269-283 |

### Instruments (8988–9015)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 8992–94 | drive docstring rule/predictions; DEMO_MODE default unchanged | "FIXED BEFORE THE FIRST RUN" (proved by T259, not git); `=0` → `${…:-0}` | MATCH | git diff 68cbf0e3 5a0e4ea9 |
| 8995–96 | census "predictions and results … before and after each run"; rule untouched | the 150 s run has **no result**; stale "~8.6 s" and "F-035 … cadence again"; rule functions unchanged | PARTIAL MISMATCH (F13) / MATCH | census.py:65-80 |
| 8997–9003 | 5 transcripts; round1–3 verbatim | tracked; six final texts byte-exact | MATCH | subagent jsonl |
| 9004 | `ledger_round{1,2}` | round 2 is **absent** at acf1a93a | NO ARTIFACT (F14) | ls-tree |
| 9006–12 | tmpfs archive; README; Lane-B scripts with provenance headers; activity script | 29 files sha256-identical to the still-existing source; 11-line headers, bodies identical | MATCH | sha256 |
| 9013–14 | f058 census: executionPromise; five triggers; not yet run | T-gate/T-tab/T-apply (clamp Store)/idle 600 s/T-mode; no output; first in acf1a93a | MATCH | script |
| 9015 | "this pass, as replayable substitutions" | 56 substitutions reproduce acf1a93a **except** the 19-line block at 9040-9058 | PARTIAL (F15) | replay on a copy |

### Consensus record (9017–9070)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 9019–29 | #676: lanes, verdicts; one test change per round in rounds 1–2; only X/C moved; n=5, one run per pair | all non-test diffs are comments; CHANGELOG the only main-side file | MATCH (F9 for §4) | git; JSONs |
| 9030–35 | F-055 lanes; orchestrator re-derived the mechanism; no round 2 | methods MATCH; the act is unrecorded | MATCH / UNTRACEABLE | r1 |
| 9036–39 | "The census that passed (two fix windows…) … saw neither" | one window VOID; no fires recorded | MISMATCH (wording, N39) | table |
| 9041–46 | four lanes on e624c281; A1/A2 matched every number; B1/B2 SOUND-WITH-FIXES | lr1:3; A1 G6 and A2 R2.e/R2.f/R2.h/R4.a–d/R5.b were **MISMATCHes**; B1/B2 :168, :332 | MISMATCH (F5) / MATCH | lr1 |
| 9047–53 | what round 1 changed | e624c281 had P2 / "4 of the open are P1" / F-025 open; all changed | MATCH | diff |
| 9054–58 | "about forty"; orchestrator re-derived seven items | 56; 5 of 7 have a named method; outputs only in tmpfs | UNTRACEABLE | SUBS labels |
| 9059–70 | no dissent; cannot-support list | A2 #10 has no disposition (F4); headless Chromium + `JUNIPER_E2E_BROWSER_GPU=1` on all four runs; 9064/9069 incomplete (F2, F1) | MATCH (incomplete) | reports; T259 |

### Matrix effect and counts (9072–9081)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 9074–78 | F-055 OPEN; F-025 FIXED (Phase 8 "inferred regressed"); F-056 P1, F-057 P2, F-058 P1 | triage; ledger :8412 | MATCH (F8 contests F-057) | triage |
| 9080–81 | 69 = 48 fixed / 1 accepted / 2 withdrawn / 18 open; 5 open P1s (055, 056, 058, CASCOR-001, -002) | identical | MATCH | `python3 util/ad-hoc/e2e_finding_triage.py` |

### Still owed (9083–9155)
| line | claim | re-derived | status | evidence |
|---|---|---|---|---|
| 9085–90 | renumbering | P8 1→1, 2→0, 3→2 … 12→11, 13+14→12; nothing dropped | MATCH | ledger :8438-8483 |
| 9105–07 | `dashboard_manager.py:467-472`, `:4698-4701`, `test_poll_gating.py:312-313` | :472; :4698-4701; :313 | MATCH | e9053227 |
| 9110, 9114 | L 3.9–5.4 s; MODULUS → 1 owed | 3912.6 / 5415.8 ms; still 5 at canopy_constants.py:491 | MATCH | JSON; git |
| 9118 | "#674 merged … as `894a2cc7`" | that is canopy#674 (FR9); the follow-ups belong to **cascor#674** (f9818b01, 00:45:02Z) | MISMATCH (F6) | gh ×2; ledger :7857 |
| 9124–25 | "the lowest-priority callbacks" | :445 above `_GATED_POLL_INTERVALS` (:463) | MATCH | e9053227 |
| 9130–32 | six gaps (Lane A) | all six are in r1 (:25-40, :61) | MATCH | r1 |
| 9133 | "Owed as one canopy follow-up PR" | branch `fix/idle-cuts-round3-wording` already at 15bd8135 (04:19:25Z) before the freeze | MISMATCH in context (F7) | reflog |
| 9134–41 | lines :75, :120, :127, :138, :193, ws :28, :113-115 at 4b4cfb16; docs claims | all confirmed; USER_MANUAL.md:764, REPLAY_V2_FAQ.md:253, CHANGELOG.md:158, panel :579 | MATCH | git |
| 9145–48 | idle-trio applies rule; ~7.5 s | the applies count discriminated in the F-055 census | MISMATCH (F21) / MATCH | census JSONs |
| 9150–55 | owner question on the pass; seven "served" local-only commits | re-run omitted; all 422; cf6fb1dc and 7a4a2e33 never served; list incomplete | incomplete / MISMATCH (F1, F16) | gh |

### Still owed: can a fresh session act on each item from the text alone?
- **0 — PARTLY.** Missing how to stand up "a leg serving `main`" (command, port, backend) and "a leg where the old code fails".
- **1 and 2 — PARTLY.** The content lives only in Phase 7 items 2 and 3.
- **3 — NOT ACTIONABLE.** No question and no pointer (the content is in Phase 7 item 5).
- **4 — PARTLY.** No file and no decision criterion.
- **5 — ACTIONABLE.**
- **6 — NOT ACTIONABLE.** It points at the wrong #674.
- **7, 8 and 9 — PARTLY.** Only pointers or row IDs; "the owner's question" is undefined here.
- **10, 11 and 12 — ACTIONABLE** via Phase 8.
- **13 — PARTLY.** Missing the existing branch and its state, the stale phrases, an owner for the instrument gaps, and the PR-edit method (`gh api -X PATCH`, since `gh pr edit` is broken on gh 2.46.0).
- **14 — ACTIONABLE**, but see F21.
- **15 — ACTIONABLE** for the owner questions; the push bullet names no ref and omits SHAs.
- **Pointer inconsistency:** items 3, 4, 6, 7, 8 and 9 carry no "(Phase 8 item N)" back-reference.

## FINDINGS

1. **MAJOR: the merge record leaves out the failed CI and the 01:22:32Z re-run that released the merge.**
   - Quoted: the table jumps from "22:29:31 | `5e52debb`" straight to "01:38:02 | merged". Also: "one pass over nine PRs, 21:47Z to 22:51Z"; item 15 "Was the 21:47–22:51Z pass … his?"; line 9069.
   - Evidence: run 35928632707 ("CI/CD Pipeline", head 5e52debb).
     - Attempt 1 failed: "Unit Tests + Coverage (Python 3.12 on macos-latest)" at 22:40:57Z, then Quality Gate at 22:42:30Z.
     - Attempt 2 started at 2026-09-24T01:22:32Z with triggering_actor pcalnon, and succeeded at 01:38:03Z. The merge followed at 01:38:02Z.
     - The account also acted after 22:51Z: update-branches on ml#2066 (23:16:06Z) and data#434 (23:17:08Z); ml#2045 disarmed and re-armed (23:48:47–52Z); cascor-worker#196 merged directly (01:21:37Z).
   - Fix: add both CI rows. Say the armed auto-merge could fire only after the re-run. Widen item 15 and line 9069 to cover the re-run and the later actions.
   - Changes a number / disposition / action? Action: yes.

2. **MAJOR: F-056's claims about the session view hold only for sessions built by hand; with cascor's real payload, `render_session` raises `KeyError: 0`.**
   - Quoted: "the player stays in its session view"; "render_session kept the active view with a REPLAYING badge"; "render_session writes the stale values back into the sliders".
   - Evidence:
     - Cascor's `state_summary()` returns `"range": {"start","end"}`, a dict (CAS manager.py:1156-1165, nested in the response at routes/snapshots.py:449).
     - Canopy's `confirm_snapshot_op` stores that data block as the session (hdf5_snapshots_panel.py:1313-1323).
     - `render_session` then reads `summary.get("range") or [start, end]` (replay_player_panel.py:505-506) and formats `range_value[0]` at `:532`. Nothing in canopy converts the dict to a list (git grep).
     - `summary.get("range")` arrived with canopy#532 (359e1bf7, F-015's fix). This is the exact trap the ledger predicted at 4210-4214: "The obvious one-line fix crashes the panel".
     - F-015's test fixture, labelled "The exact shape measured off the running service", uses `"range": [3, 37]` (test_p2_wave_batch_a.py:179-190).
     - Lane B's probe used a flat session. The probe here reproduced the KeyError; nothing was driven live.
   - Fix: qualify F-056's view claims. Triage the KeyError as a new finding or an F-015 regression; F-015 is still OPEN pending its live re-drive (ledger 6135-6147). Add "sessions built by hand" to line 9064.
   - Changes a number / disposition / action? Disposition: yes. Action: yes.

3. **MINOR: the 0.15–0.18 probability has the wrong basis and the wrong attribution.**
   - Quoted: "(at that rate, no fire in 210 s has a probability of about 0.15–0.18)", inside a paragraph labelled "the orchestrator's reading".
   - Evidence: at the only stated rate (37–44/h), the probability is 0.077–0.116. 0.15–0.18 comes from 29–33 **evicting** fires an hour (r1:298), and was computed by the ledger validation's Lane A2 (lr1:118, R5.b).
   - Fix: restate the basis and credit A2.
   - Changes a number / disposition / action? The number's basis: yes.

4. **MINOR: Lane B's archived no-fire run is left out.**
   - Evidence: `PS/f055_r1_laneB/run_watchdog.json` is at R = 7 ± 1 s with the gate's mount write on and the watchdog on. It applied 23 of 23 with no fires over 201 s.
     - Lane B reported it (r1:297), and A2 #10 flagged its omission (lr1:157); no disposition is recorded.
     - Under the model, P(no fire) is 0.086–0.127. Combined with the census, P ≈ 0.013–0.023, which is not "weak" evidence.
     - It is also a mount-write run that did not cascade, unlike the unarchived "0 of 51".
   - Fix: cite it in F-058 and in "Why the census still passed", and record A2 #10's disposition.
   - Changes a number / disposition / action? Number: yes.

5. **MINOR: "A1 and A2 matched every number they could re-derive" (9045) is false.**
   - Evidence: lr1 :37 (G6), :85-88 (R2.e, R2.f, R2.h), :96-99 (R4.a–d) and :118 (R5.b) are all MISMATCH rows, and all were corrected.
   - Fix: say the mismatches were corrected.
   - Changes a number / disposition / action? No.

6. **MINOR: item 6 cites the wrong #674.**
   - Quoted: "#674 merged on 2026-09-23 as `894a2cc7`".
   - Evidence: the follow-ups belong to juniper-cascor#674 (f9818b01, 2026-09-23T00:45:02Z: the WS-manager swallow-and-forget pattern; ledger 7857-7858). `894a2cc7` is canopy#674 (FR9).
   - Changes a number / disposition / action? Action: yes.

7. **MINOR: the canopy follow-up exists, is never named, and is described as still owed.**
   - Evidence:
     - `CAN` branch `fix/idle-cuts-round3-wording` was created at 03:38:54Z; its head was 15bd8135 (04:19:25Z) before the freeze at 04:36:28Z, and is now 2f2bc203 (04:46:40Z). It is not on GitHub and has no PR.
     - Lane C's report (`consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`) is untracked and was written after the freeze.
     - At 15bd8135, USER_MANUAL.md:669-670 still promised the stream.
   - Fix: name the branch and its state, archive and cite Lane C's report, and reword item 13.
   - Changes a number / disposition / action? Action: yes.

8. **MINOR: F-057's P2 contradicts the §6.3 rule that made F-056 P1.**
   - Evidence: USER_MANUAL.md:764 and REPLAY_V2_FAQ.md:253 promise the weight stream at `e9053227`, and the correction has not merged. The section itself concedes the rule "argues P1".
   - Fix: rate it P1 until the correction merges (open P1s go 5 → 6), or put the question to the owner in item 15.
   - Changes a number / disposition / action? Possibly both disposition and count.

9. **MINOR: "§4: the round changed no disposition" misstates the termination status.**
   - Evidence: B3 marked both MINORs "number: yes; action: yes" (r3:23, :37). Under procedure §4 (`…CONSENSUS-PROCEDURE.md:117-119`) the review had not terminated; the merge ended it.
   - Changes a number / disposition / action? The recorded consensus status: yes.

10. **MINOR: "All were applied." (8637) holds only for the tree and the commit message.**
    - Evidence: the PR body still says "answered a third slower", "all seven files", "`main` `3a6dea95`", "Round 3 … running" and "lands before this PR merges". B2's transcript-commit remedy was overtaken.
    - Fix: correct the sentence and list the stale phrases in item 13.
    - Changes a number / disposition / action? Action: yes.

11. **MINOR: the "who" statements are overstated.**
    - Quoted: "Every session active before 21:41Z hit…"; "could not have done it"; "the only entry…".
    - Evidence:
      - Session 259b4d16 and four subagents, idle since 21:25:49Z or earlier, hit no limit.
      - A background job of session 317c1df2 updated ml#2058's branch (cdb0a18b) at 21:43:55Z, inside the "no tool call" window (timeline verified).
      - A queued task notice sits at 21:53:09Z.
      - Host reflogs show interactive git activity from about 21:39Z to 00:07Z.
      - None of this readied or armed #676.
    - Fix: "did not"; add the background-job check; add the host activity to item 15.
    - Changes a number / disposition / action? Action: yes.

12. **MINOR: "because the script entered git after the runs" (8746) is wrong.**
    - Evidence: the census script has been in git since 51993b37 (17:07:01Z); only its prediction docstring entered later (5a0e4ea9).
    - Changes a number / disposition / action? No.

13. **MINOR: the census docstring does not match the Instruments bullet.**
    - Evidence: the 150 s run has no result line. The docstring still carries the corrected "~8.6 s" and "F-035's … cadence again".
    - Changes a number / disposition / action? No.

14. **MINOR: `…ledger_round{1,2}.md` is a forward reference.**
    - Evidence: round 2 does not exist at acf1a93a, and the consensus record never says §4 requires it.
    - Fix: record this round before landing.
    - Changes a number / disposition / action? No.

15. **MINOR: the corrections script is not a full replay.**
    - Evidence: a replay omits the 19-line block at 9040-9058, and there are 56 substitutions, not "about forty".
    - Changes a number / disposition / action? No.

16. **MINOR: item 15's commit list.**
    - Evidence:
      - cf6fb1dc and 7a4a2e33 were never served.
      - The list omits canopy's 8990f65c, 5310b81a, c360fb53 and 040dc5c1 (cited by r3 and `drafts/laneB3_cuts_brief.md`), and juniper-ml's ada8e50c and b54e3b3f.
      - b54e3b3f (cited at 8681) is not in acf1a93a's history; its rebased copy is f6861234.
    - Changes a number / disposition / action? Action: yes.

17. **MINOR: evidence still only in tmpfs.**
    - Evidence:
      - B1's second-Input repro (`…/ddf7847c…/scratchpad/f058repro.6JTgea/`): its 0 of 45 and 23 of 23 have no raw output, and the ledger does not say so.
      - Lane B's `laneB_probe_{walk,mutation,stop,exact}.py`.
      - B3's `head_js.txt` (111) and `head_related.txt` (321).
      - Lane A's m1 diffs.
    - Fix: extend `util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence.py`.
    - Changes a number / disposition / action? Action: yes.

18. **MINOR: F-058's class statement is overbroad** (8520, 8940, 8950-51).
    - Evidence: in run_watchdog_r3.json the fires at 57.832 s and 152.833 s evicted nothing, and two of the three cascades ended by themselves.
    - Fix: "a re-enable more than one period before the response lands, or any re-request".
    - Changes a number / disposition / action? No.

19. **MINOR (convention): documents cited without filenames.**
    - Quoted: "§4" (8618, 8656) and "procedure §7" (9017).
    - Evidence: neither names `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, as `Juniper/AGENTS.md` requires.
    - Changes a number / disposition / action? No.

20. **MINOR: item 13's heading contradicts the round-3 bullet.**
    - Quoted: "Round 3's fixes, which the merge left unapplied", against "marked its code-file NITs no-action" (8641).
    - Fix: "Round 3's no-action NITs, now scheduled".
    - Changes a number / disposition / action? No.

21. **MINOR: item 14's rule contradicts the census it draws on.**
    - Quoted: "On the idle trio an applies count cannot…".
    - Evidence: the F-055 census discriminated on applies (0 vs 19 latency changes), because the status-bar feeder always returns data (8978). The 204 premise holds only for #613's feeder, and even there it is inferred from source (also 8981 and item 0).
    - Changes a number / disposition / action? No.

**NITs.** None of these changes a number, disposition or action.

22. "7.89 at the run's start (19:30:31Z)": the run command came at 19:30:37.9Z.
23. "first read came at 40 s": the log's health read is at +34 s.
24. The console-listener caveat: the driver's own listener attaches before `goto` (e2e_w3_params_driver.py:209), and the log has 0 CONSOLE lines.
25. "three of four windows" is paraphrased; quote 78c057e2 verbatim.
26. "~32 s" is A2's figure, not cuts Lane A's.
27. The `disabled_after_s` reason is not in r1:40.
28. Lane A also refuted the stop claim; credit it.
29. The phrase survived in "five places" by B2's count; there were six.
30. The g-3 comment is quoted inexactly.
31. B2's limit was "C1 started 40 s after".
32. B2's remedy also required committing the transcript.
33. The dead timer entered via a7ca240f (2025-12-04).
34. The round-1 gap list has 4 entries, item 13 has 6.
35. The 14.4 s edit fixed more than "two commits".
36. The @hash readiness check was on dash 4.2.0, not 4.4.1.
37. "~8.6 s" is 8.69 (the mean gap) or 8.57 (60/7).
38. "window's edges" should add "or a network failure".
39. "The census that passed … saw neither": one window was VOID, and fires are not recorded.
40. "Shared with #613" is the orchestrator's; the port/DOM corrections were made in juniper-ml, not 7a4a2e33.
41. `:406-408` is correct only at 884d22fb.
42. "+10 by AST" is only true when inheritance is counted.
43. "13.0 s after page load" is a lower bound, and the commit said the clamp "silences" the lane, not "reaches" it.
44. c0530279 is #670's first commit, not its head.
45. #677 overlaps nothing.
46. The "8 s" causal clause: ml#2032 took 7 s without one.
47. Committed events have no actor.
48. Only the CHANGELOG carries the "evidence ledger" phrase.
49. "Round 2 corrected round 1's attribution": that attribution was in the round-1 corrections, not Lane B's report.
50. The 4.4.1 `:979-991` is only the definition; the calls are at :1020–1037.
51. Name the base for "3 ahead, 512 behind" (B1 reported 6/519 against a different base).
52. With a real session, `playing` stays False, not None.
53. The phase9-scratch README lists 4 unbacked Lane B figures; the ledger's 6 is correct.
54. Line 8691 is a lazy continuation of the previous bullet.
55. The "two test-only changes" are not named.

## WHAT I COULD NOT CHECK
- **Nothing live.** No canopy, cascor or browser was run. F2's KeyError rests on source plus a probe.
- **Unrecreated figures.** 7 of 7, 0 of 51, 4 of 4 then 0 of 28, 0 of 21, and B1's 0 of 45 and 23 of 23 would need a synthetic Dash server and Chromium. The 352 s and 37–44/h figures were re-created from the archived seeded scripts.
- **Served SHAs via `/proc`.** Ports were not touched; I relied on the JSONs' per-window SHAs.
- **Who issued the ready, the arm and the 01:22:32Z re-run** (UI, CLI or automation, and from which host). The API shows only pcalnon.
- **Records that do not exist:** the orchestrator's own re-derivations and rule check, the unit behind "about forty", what made up B3's 111 and 321 and which files its "all 8" covered, and the round-4 decision.
- **Untested or unknown:** whether the f058 census's clamp-Store simulation fires the gate (it has never run), and who owned the pytest processes at 19:40:52Z.
- **A table row with no source.** The archived `cascade_sim.py` lacks a "5–9 s → 22.5 s" row that Lane B's report tabulates, so that table came from a version that was not archived. The ledger does not cite the row.

**SECRETS/PII:** No environment variables, tokens, credentials or owner email were printed or sent. Every `gh` call selected fields with `--jq`, and `autoMergeRequest.authorEmail` was never fetched. One commit-message diff was email-redacted. One output showed the `noreply@anthropic.com` co-author trailer, which is not the owner's address. Transcript and reflog scans printed only ids, timestamps, command strings, numbers and one prompt length. Network access was read-only `gh` GETs plus one PyPI JSON GET. No repository was written to; scratch stayed under `…/scratchpad/r2f.xB7Gf1/`.

---

## Lane R2-B -- adversarial, on round 1's corrections

*agent `a217fde4b7a6a43ad` · round 1 · last-assistant-text (not resumed) · 16978 chars*

**VERDICT: SOUND-WITH-FIXES**, but the ledger can't land until finding 1 is fixed. The core dispositions survive: F-056 widened to P1, F-057's PR history, F-058's mechanism and trigger list, and the counts of 18 open with 5 open P1. What fails is newer text. The census that item 0 calls "ready" can't produce a verdict on the leg it names. A wrong wire fact appears three times. The "Who" exclusion rests on a census that misses a session process that acted inside its window. This round changes a number, the basis of one disposition and several actions, so §4 calls for a round 3.

Paths used below:
- **LEDGER** = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `acf1a93a`
- **CENSUS** = `…/graceful-sprouting-panda/util/ad-hoc/2026-09-24_f058_trigger_census.py`
- **README** = `…/graceful-sprouting-panda/util/ad-hoc/README.md`
- **HANDOFF** = `…/graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`
- **DR** = the installed dash 4.2.0 `dash_renderer.dev.js`
- **DM** = canopy `e9053227:src/frontend/dashboard_manager.py`
- **S** = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r2b.SQyNnR/` (my scratch)

## FINDINGS

**1. BLOCKER: the new census scores every answer that applies nothing as EVICTED, and it can never count a watchdog fire.**
- **Quoted:**
  - LEDGER:9096-9097: "`util/ad-hoc/2026-09-24_f058_trigger_census.py` is ready for it."
  - CENSUS:35-37: "a store subscription sees every dispatch, so a record gone from `watched` with no `executed` was evicted. This does NOT depend on the response's content".
  - CENSUS:43: "with the lane `disabled` at the poll before, is a FIRE".
- **Evidence, the eviction count:**
  - I ran CENSUS's own INSTALL JavaScript, extracted with `ast` and unmodified, against a scratch dash 4.2.0 app (`S/synth_app.py`, `S/synth_drive.py`). The app has a 1 s Interval with a `running=` guard, 2 s server latency and no trigger.
  - When the feeder returns `no_update`, the wire shows 13 × HTTP 200 and the census scores **0 APPLIED / 13 EVICTED**.
  - The same app returning data scores **13 APPLIED / 0 EVICTED**.
- **Mechanism:**
  - The renderer's StoreObserver subscribes when the store is created (DR:355-358), long before `st.subscribe(sample)` (CENSUS:161).
  - Observers run synchronously, in registration order (DR:3751-3759). The executedCallbacks observer ends with a synchronous `removeExecutedCallbacks` dispatch (DR:2627).
  - Redux notifies every listener of that nested dispatch before it returns (DR:46360-46385).
  - The only nested dispatch that can expose the `executed` entry first is `applyProps` → `updateProps` (DR:2443-2470), and it runs only when the result carries props.
  - So an answer with no props is already gone from both lists when `sample()` first sees the state, and CENSUS:156 marks it gone (evicted).
- **Evidence, the fire detector:**
  - `S/synth_app2.py` runs canopy's watchdog JavaScript verbatim (DM:2517-2535) over a lane with 40 s latency.
  - There were **2 real fires. The census's own `watchdog_fires()` (CENSUS:224-230, extracted with `ast`) counted 0.**
  - Both resets were logged with the lane flag false (CENSUS:165). The fire's own `false` write is applied in microtasks before the next 100 ms poll. The code reads the lane at the current poll, not "the poll before".
- **Consequence:**
  - On the idle trio, where the ledger says every answer after the first is `no_update`, the baseline reads close to 100% EVICTED. That gives VOID-BASELINE, and every trigger comes out UNSCORED.
  - Idle FIRES is 0 by construction. Any scored window whose answers stop carrying props reads CASCADE.
  - The tool violates item 14's own rule that a census must be able to fail.
- **Fix:** record the executed transition itself. Either wrap `window.store.dispatch` and log `addExecutedCallbacks` entries by `executionPromise`, or install a shim with `add_init_script` before the renderer builds its store. Detect a fire from the lane state before the reset, or by wrapping the watchdog. Re-run a synthetic check before any live run, and reword LEDGER:9013-9014 and 9096-9097.
- **Changes an action:** yes. **Number/disposition:** no.

**2. MAJOR: "every response after the first is a 204" is false for canopy's dash, and nobody re-derived it.**
- **Quoted:** LEDGER:8981, 9095-9096 and 9146; README:726; CENSUS:38 ("a `no_update` answer is a 204").
- **Evidence:**
  - In dash 4.2.0, `_callback.py:601-605` sets `has_update = _set_side_update(...) or has_output`, with `has_output = len(output) > 0` (`:645`). So a normal callback with outputs never raises PreventUpdate from `no_update`.
  - dash 4.4.1, which canopy's `requirements.lock:32` pins, has the same code at `:695-699`.
  - `curl -i -X POST …/_dash-update-component` on the scratch app returns `HTTP/1.1 200 OK … {"multi":true,"response":{}}`.
  - canopy's `src/frontend` and `src/main.py` never use `PreventUpdate`, and the feeder returns `dash.no_update` (DM:7841-7842, 7847-7848, 7905-7906).
  - The claim is round-1 Lane B1's finding 2. The substitutions that introduced it (#46, #52 and #56) are tagged with B1's findings 1, 3 and 6a, never 2.
  - Its presence refutes LEDGER:9056-9058, "re-derived every load-bearing single-lane finding".
- "An applies count cannot tell" survives, but for finding 1's reason, and that reason also defeats the eviction count the ledger prescribes. LEDGER:7496 carries the same error from an earlier phase.
- **Fix:** say "a `no_update` answer is HTTP 200 with an empty `response`, which applies nothing", and cite `_callback.py`.
- **Changes an action:** yes (the discriminator items 0 and 14 prescribe).

**3. MAJOR: the bolded "Who" exclusion is refuted inside its own window.**
- **Quoted:**
  - LEDGER:8675-8678: "No Claude Code session on this host could have done it. Every session active before 21:41Z hit the weekly rate limit … From 21:41:02Z to 01:40Z no session on this host made a single tool call; the only entry is a new prompt the limit refused at 00:07:23Z".
  - README: "It answers 'could any session here have done it?'".
  - LEDGER:9069.
- **Evidence:**
  - The cited tool, run over 21:00:00Z–01:40:00Z, lists session `259b4d16` with 11 tool calls, `limit_hits=0` and a last entry at 21:01:29Z. It lists four subagents with 22–118 tool calls, no limit hits, and last entries at 21:15:57Z–21:25:49Z. So "Every session active before 21:41Z hit the … limit" is false.
  - A full scan of entries from 21:41:02Z to 01:40Z (`S/entries_in_window.py`) finds 5. One is a task notification in session `317c1df2` at 21:53:09.035Z: `Background command "Shepherd #2058: re-sync on BEHIND until it merges" completed (exit code 0)`. Round-1 Lane B2 had reported this entry, and the pass dropped it.
  - That command was launched in the background at 20:39:42Z as `…/2026-09-22_shepherd_automerge.bash 2058 60 180`. The script's only write is `PUT …/pulls/${PR}/update-branch` (script :70).
  - ml#2058 received update-branch `cdb0a18b` at **21:43:55Z**. So a Claude session's process acted on GitHub inside the window the ledger calls free of tool calls.
  - Background launches with no completion notice can't be excluded this way. Examples: `1f771cb0` at 20:09:37Z, "Watch CI for PR 2057"; `e6c1cb6d` at 21:21:04Z, "Wait until #2060 merges or goes BEHIND".
  - For the owner question: a signed content commit `4c496443` (login pcalnon) landed on ml#2058 at 21:45:22Z, before the pass began.
- The conclusion for #676 probably holds: the shepherd exited at 21:53:09Z and only touches #2058. But the stated basis cannot see this class of process.
- **Fix:** replace the two sentences, and cite a check of background launches and their completion notices.
- **Changes a disposition** (the support for the exclusion at LEDGER:9069) **and an action:** yes.

**4. MINOR: the hand-edited consensus bullet misstates round 1.**
- **Quoted:** LEDGER:9045 ("A1 and A2 matched every number they could re-derive"), LEDGER:9056-9058, and LEDGER:9015 ("this pass, as replayable substitutions").
- **Evidence:**
  - The round-1 report (`…consensus/2026-09-24_validator_reports_phase9_ledger_round1.md`) has A1's G6 at :37 as "MISMATCH on the commit and the interval". The pass itself changed "3.5 h" to "2 h 52 min".
  - A2's R2.e and R2.f (:85-86) are mismatches: 29 → 27 responses and 3 → 2 windows, both changed by the pass (LEDGER:9036). R2.h (:88) is another.
  - Replaying the script's 56 substitutions on `e624c281` reproduces `acf1a93a` exactly, except the 19-line hand-edited bullet (LEDGER:9040-9058). A replay on a moved `main` would silently drop it.
- **Changes an action:** minor (the replay path). **Number/disposition:** no.

**5. MINOR: the census probability is attached to the wrong rate.**
- **Quoted:** LEDGER:8862-8863, "Lane B's modelled false-fire rate (at that rate, no fire in 210 s has a probability of about 0.15–0.18)", and LEDGER:9038, "could have seen a watchdog false fire".
- **Evidence:**
  - 0.15–0.18 is the rate for Lane B's *evicting* fires, 29–33 an hour (`2026-09-23_validator_reports_phase9_round1.md:298`). The ledger states only 37–44 an hour (LEDGER:8840), which gives **0.08–0.12**. The census could only see evicting fires.
  - A2's finding 10 was neither applied nor declined. It is Lane B's R = 7–8 s run, 0 fires with 23 of 23 applied, archived as `phase9-scratch/f055_r1_laneB/run_watchdog.json`.
- **Changes a number:** yes.

**6. MINOR: the tmpfs rescue is incomplete, and the pass added new evidence that exists only on tmpfs.**
- **Quoted:** LEDGER:8969-8970, "…0 of 21 … 37–44 an hour) have no surviving raw output; its scripts can re-create them". The scratch README (`phase9-scratch/README.md`) lists four such figures; the ledger lists six.
- **Evidence:**
  - The repro's watchdog scenario (`2026-09-23_f055_r1_laneB_repro.py:118-129`) opens `util/ad-hoc/fix/fix_callbacks.json`, which doesn't exist. `_watchdog_alias_sim.js:23` reads the same file from its arguments.
  - The only copy is `259b4d16…/scratchpad/laneB_f055.Iywb95/fix/fix_callbacks.json`, on tmpfs and not in the archive list.
  - B1's second-Input repro, the only evidence for the trigger this pass added, exists only on tmpfs at `ddf7847c…/scratchpad/f058repro.6JTgea/`.
- **Changes an action:** yes (archive both before a reboot).

**7. MINOR: three more places where CENSUS's code does not implement its docstring.**
- **T-apply is scored even when nothing is in flight.** `release_mid_request` (CENSUS:301) is never used. With no request in flight, the release still fires and is scored (CENSUS:302-304, 356-362), which gives CONTAINED by construction. The docstring calls this MISSED.
- **`took()` (CENSUS:270-275) skips the docstring's "still in flight" check,** so the request's own natural completion satisfies it.
- **T-tab's second click comes about 4.5 s after the first, not 1.0 s,** because `open_tab` waits 3.5 s (`e2e_f027_redrive.py:228`).
- **Changes an action:** yes.

**8. MINOR: the handoff's "Superseded in part" note (HANDOFF:6-21) misses what this same pass superseded.**
- Item 3 (:91-93) still says "Run a metrics-store apply census", which LEDGER:9143-9146 now says cannot fail.
- Item 4 (:98) still says "all three triggers"; there are now four.
- The verification comment (:136) still reads "4 open P1"; it is now 5.
- **Changes an action:** yes.

**9. MINOR: F-057's history (LEDGER:8922-8928) contradicts itself.**
- **Quoted:** "both times into a stacked feature branch that never reached `main`", and "was an artifact of a local fetch".
- **Evidence:**
  - #190's base, `…-cache-v2`, is #189's head, and #189 merged to main at 19:52:10Z.
  - #184 merged at 06:03:30Z into g-1's branch, 3 h 57 min after g-1 (#180) landed on main (02:06:37Z). That is the same pattern a third time.
  - `git cat-file -t` still fails for both `d85c9ddd` and `dbc25277` in the local cascor clone. Lane B's observation was true; its "never merged" inference was the error.
- **Changes an action:** minor (#184 joins the sweep).

**10. MINOR: F-057's P2 rests on an unpushed commit.**
- **Quoted:** LEDGER:8933-8935, "P2, because the canopy follow-up corrects the docs … Until that merges … argues P1."
- **Evidence:** the follow-up is local `15bd8135` ("[ahead 1]"). `gh api …/commits/15bd8135` returns 422, "No commit found".
- **Changes a number/disposition:** yes, if applied as written (6 open P1 until it merges).

**11. NIT: smaller precision fixes. None changes a number, disposition or action.**
- LEDGER:8946: `:979-991` covers only `completeJob` in 4.4.1. Its call sites are at `:1020`, `:1024`, `:1033` and `:1037` (the wheel's sha256 matches PyPI).
- LEDGER:8857: `e9053227` contains no F-055 node test. What CI shows is that no node-gated test was skipped.
- LEDGER:8894: "play left `playing` at None" is an artifact of the probe. The snapshots panel's `confirm_snapshot_op` sets it to False.
- LEDGER:9133's heading now covers items that came from Lane C, not round 3.
- LEDGER:9004 cites a round-2 file that does not exist yet.
- LEDGER:8686: "21:47Z to 22:51Z" misses the account's update-branches at 23:16:06Z and 23:17:08Z.
- LEDGER:8694: "every successful or skipped check" hides five Cursor checks that went neutral at 22:28:07–12Z, the seconds of the ready and the arm.
- LEDGER:9103 drops Phase 8's condition "a leg whose training may be started".
- LEDGER:8736: the archived parent junit has 103 tests across 4 files, not 94.

## CORRECTIONS YOU COULD NOT REFUTE
- **F-056 widening.**
  - The response the panel receives (`replay_player_panel.py:376-377`) is the whole cascor envelope. The canopy route, the adapter (`:2368-2385`) and client 0.8.0 all pass it through unchanged.
  - cascor's `snapshots.py:455-503` returns `success_response({snapshot_id, operation, action, result})`.
  - `_merge_session` (`:839-875`) overlays that envelope. `render_session` reads none of the envelope's top-level keys.
  - Only two writers of `replay-player-session` exist.
  - The plan's §6.3 defines P1 as "breaks a documented behaviour" (plan :359-360). The manual documents the readouts at `USER_MANUAL.md:757-758`.
  - The model-select path holds: DM:3462-3483, 2735-2742 and 2604.
- **F-057 PR facts:** #187, #189 and #190 timings, and `d85c9ddd` / `dbc25277`. `compare main...dbc25277` shows 3 ahead and 512 behind, and #190 adds `metrics["weights"]` in `_emit_frame`.
- **F-058 source:**
  - `completeJob` is at DR:925-937 and in 4.4.1 at :979-991.
  - A 200 whose body fails to parse skips it.
  - `getUniqueIdentifier` (DR:1715-1727) ignores which Input fired.
  - The gate's expression (DM:2467-2482), the three `no_update` cases, and the three contradicted canopy lines (DM:467-472, 4698-4701, `test_poll_gating.py:312-313`) all check out.
- **Counts:** the triage gives 69 / 48 / 1 / 2 / 18 with 5 open P1, matching the ledger. The one live finding it now counts as FIXED, F-CANOPY-025, matches the ledger's convention.
- **The nine-PR pass:** every ready, arm and merge time is correct to the second. The drafts came from `bc31e993`, `e6c1cb6d` and `259b4d16`, and #676 is the only PR with an update-branch between its ready and its arm.
- **The checks on `4b4cfb16`:** 27 success and 1 skipped by 20:59:25Z.
- **Timings and host load:** 84.2% and 80.8% CPU, load 7.89 and 13.10. `ada8e50c` is at 16:26:49Z and `51993b37` at 17:07:01Z. The pre-registered band is 0.60–0.85 (`idle_cuts_live_check.py:42`), and "32–40 s" holds.
- **Other:** the head branch was deleted at 01:38:03Z, and there were two retitles. CI's 3.13 unit job reports "6870 passed, 6 skipped" with no node-gated skip. The two test-coverage claims about `_merge_session` hold.

## WHAT YOU COULD NOT CHECK
- Canopy itself. I didn't run canopy or the census, so finding 1 is shown on a synthetic app plus the renderer source.
- Whether any background task without a completion notice was still alive at 22:28Z.
- Who the actor was, and where `4c496443` came from.
- F-056 and the second-Input trigger on a live page.
- Dash 4.4.1's behaviour at runtime (I compared source only).
- **Process note:** during this round, another session wrote three untracked files into the frozen worktree: `2026-09-24_validator_reports_phase9_canopy_followup.md`, `laneC3_canopy_followup_brief.md` and `2026-09-24_idle_cuts_check_mutants.py`. HEAD and the ledger are unchanged.

## SECRETS/PII
No slip. No token, environment variable, credential or email address was printed or sent. Transcript scans printed only session ids, timestamps, record types and bounded substrings (one background command line and one task summary), with token-shaped strings redacted. Network use was GitHub API GETs and one PyPI JSON GET. The scratch apps on 127.0.0.1:9487–9489 are stopped, and no repository file was changed.

---
