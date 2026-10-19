<!-- markdownlint-disable -->

# Phase 12 ledger validation, round 2 — validator reports (verbatim)

Round 2 of the consensus review of the canopy E2E ledger's Phase 12 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen local commit 190c896c (round 1's pass applied to c626e847), 2026-10-19. Two lanes from one brief, reports/e2e-canopy-2026-09-02/drafts/lane12R2_phase12_ledger_brief.md, briefed on round 1's corrections only. Each report below is the lane's final message, verbatim; each lane ran once. Neither found anything that changes a number, a disposition or an action, so the review ended at this round; the orchestrator's dispositions are in the ledger's Phase 12 Consensus record, and the final wording pass is util/ad-hoc/2026-10-19_phase12_ledger_round2_corrections.py.

## Lane 12-R2A (re-derivation and replay, on round 1's corrections)

**Lane 12-R2A** (re-derivation and replay, on round 1's corrections)
**VERDICT: SOUND-WITH-FIXES** — every corrected number, source claim and credit re-derives; the replay is byte-identical; the four fixes below are wording inside the pass's own sentences and the round-1 record. None changes a number, a disposition or an action, so under §4 this round ends the review.

Worktree `squishy-growing-breeze` at `190c896c`; no tracked file modified; scripts and extracted copies under `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/D227803E-A1C2-4957-9A7C-824C3F8B44BD/scratchpad/lane12R2A/` (`replay.py`, `rawgate` readers, `strand.py`, `renderer.py`, `dm_25c5c887.py`, `diff.patch`).

**TABLE**

| claim or correction | re-derived | result | evidence |
|---|---|---|---|
| Replay: 17 `LEDGER_SUBS` + record, 6 `HANDOFF_SUBS` on `c626e847` → `190c896c` | module imported, `apply()` run on the `git show c626e847:` copies | byte-identical, both files (969,251 and 10,738 bytes); no hand edit; every new anchor occurs once | `replay.py` |
| Diff `c626e847..190c896c` = the pass | 15 ledger hunks, 5 handoff hunks, 188 changed lines | all accounted for by the 23 substitutions (follows from byte identity) | `diff.patch` |
| Gate writes 9/8/8/8; `false` onto enabled lane 7/6/6/6; in flight at 5/5/5/2; one `true`, one `false` onto the disabled lane per run | own reader of `raw.gate` + `raw.req` (W/A pairs) | MATCH; archived `…_analyze.py` per-write list agrees | `pacer-live/f058-census-run{1,2,3-v2,4-final}.json` |
| Clamp held 58.4–59.9 s | `raw.lane` episodes 58,438 / 59,921 / 59,429 / 59,088 ms | MATCH | same |
| "49–52 s" from runs 1–2's max in-flight × 3 | 16,363 × 3 = 49,089; 17,308 × 3 = 51,924 | MATCH | same |
| First renderer runs 17:29–17:41 CDT (pacer), 17:29–17:40 CDT (guard); trigger stamps 17:38:59–17:40:12 | pacer requests 17:28:58–17:41:10, triggers 17:38:59–17:40:08; guard 17:28:59–17:40:17, triggers 17:38:59–17:40:12; `idle_s` 600 | MATCH; file stamps are end times | `…T174112_pacer_run.json`, `…T174018_guard_run.json` |
| Three `extra` requests: issued 3,010 / 4,693 / 3,687 ms, landed 6,695 / 8,047 / 7,397 ms after the mode trigger; "3.6 s round trip" | seq 150/156/162 vs the three `mode` triggers; rtt 3,685 / 3,354 / 3,709 | MATCH (mean 3.58 s) | `…T201631_pacer_run.json` |
| Strand: re-issued 30,999 ms, applied 3,969 ms later ("31.0 s / 35.0 s") | stranded seq 165 began 3,970 ms after `armed_at`; stale seq 166 issued 30,999 ms after it; its `applied` stamp +3,969 ms (its `end` +3,962) | MATCH | same, `applied` list |
| Legs' `build_date` 22:43:05Z / 00:02:18Z / 00:33:31Z vs commits 23:28:34Z / 00:02:02Z / 00:19:57Z / 00:28:03Z / 01:19:15Z; "sixteen seconds after commit 2" | three status-bar census files; `gh api …/pulls/731/commits` committer dates | MATCH; 00:02:18 − 00:02:02 = 16 s | `…status_bar_apply_census_8052_{pacer,pacer_v2,final_2689a207}.json` |
| Merges GitHub-signed; squash: one parent `4f69524b`; 46 success + 7 skipped | all 8 PR commits `verified: true`; `25c5c887` parents `[4f69524b]`, verification valid; check-runs total 53 = 46 success + 7 skipped; PR `merged_at` 02:27:27Z | MATCH | `gh api …/commits/25c5c887`, `…/check-runs?per_page=100`, `…/pulls/731` |
| Gate `not (flags_ok and running)`; `reason = changed ? 'extra' : (acked ? 'tick' : 'stale')`; `n=seq`; no-request-yet rule | `dashboard_manager.py` at `25c5c887`: line 7167; 594; 4924 (`n=seq` from `request.get("seq")`); with no `issued_at` the request is aged from first sighting and returns `no_update` inside the bound, `update_metrics_store` has `prevent_initial_call=False` (acks seq 0) | MATCH | `dm_25c5c887.py` 560–600, 4912–4928, 2676–2700 |
| Mode change waits for the ack plus up to one tick | pacer Inputs: lane `n_intervals` and `metrics-panel-display-mode-store`; `!acked && now − issuedAt < staleMs` → `no_update` | MATCH (mechanism) | same, 2679–2690 |
| Capture's side: 179 callbacks, no `running=`, one `disabled` writer per paced lane, one Input per feeder | own reader of the capture | MATCH | `pacer-live/2026-10-08_final_leg_dash_dependencies_2689a207.json` |
| Phase 9 allow-arm table and Matrix ruling; "demo leg that trains" | ledger 8899–8907 (`:8058` LANDS 13.0 s, `:8059` LANDS 19.7 s), 9673 "stays counted **FIXED**", 9674 "not established"; 8901 "A demo canopy runs its own training" | MATCH | ledger |
| `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` exists; short name does not; `canopy-e2e-arc-state.md` exists in auto-memory | `ls` | MATCH | filesystem |
| Record's lane credits (A1/A2/A3/A4/A5/A6, B1–B9, C1–C4) and "Not applied" (C5 deferred, C6, C7b) | each matched to the verbatim reports | MATCH; C7(a) is "not a defect", nothing to apply | `consensus/2026-10-19_validator_reports_phase12_round1.md` |
| Cross-document: Summary cost ↔ item 18 ↔ "What VERIFIED LIVE rests on"; item 27 ↔ F-055 Status bullet ↔ handoff item 4 ↔ parent item 4; handoff goal (25/28 trio, 27 demo) ↔ items | read in full | consistent | ledger 11259–11705, 8258–8265; both handoffs |
| Triage on `190c896c` | `python3 -B util/ad-hoc/e2e_finding_triage.py` | 79 / 56 / 1 / 2 / 20; 4 open P1; 16 open P2 | output |

**FINDINGS**

1. **MINOR** — the record's provenance sentence is false in letter for two figures the ledger now rests on. Text (ledger, Consensus record, Round 1): "none produced a figure the ledger now rests on that the archived readers do not reproduce." Evidence: the three `extra` delays (3,010 / 4,693 / 3,687; 6,695 / 8,047 / 7,397 ms) appear in no archived score or stdout file (`20261008T201631_pacer_score.json` holds `30998.958…` and `3969.327…` but none of those six), and the `build_date`-against-commit comparison is a raw-JSON and `gh` reading; both come from Lane 12-B's probe, re-derived by the orchestrator (the record says so) and by me from the raw `*_run.json` and the census files. The Instruments bullet already says "the archived readers and Python's `json`". Fix: "…that the archived JSON does not reproduce" (or "the archived readers or a `json` reading of the archived files"). Changes a number, disposition or action? no.

2. **NIT** — "at each trigger" overstates where the enabled-lane writes fall. Text (ledger, F-058 census bullet, corrected by the pass): "`false` onto an enabled lane 7, 6, 6 and 6 times (at page load, at each trigger and at the census's own release after T-apply)". Evidence (`raw.gate` vs `triggers`): run 1's seven are two at load (3.3 s, 15.8 s), one after T-gate, three after T-tab, one after the census's release; runs 2–4 are 2 + 1 + 2 + 1. T-apply's own write is the `true` (the clamp), and T-mode produced no gate write in any run. The totals are right. Fix: "(two at page load, one at T-gate, two or three at T-tab, and one at the census's own release after T-apply)". Changes a number, disposition or action? no.

3. **NIT** — a kept sentence now sits against a corrected one. Text (ledger, "The live checks, re-derived", unchanged): "The README in `reports/e2e-canopy-2026-09-02/pacer-live/` states what each leg served and how it is known; this phase's readings agree with it." The pass's corrected sentence two bullets later says the README's "which only commit 2 has" "is false in letter since commit 3", and Lane 12-A noted the renderer-check README's "17:40–17:54 CDT" is wrong the same way as the ledger's old times were (both READMEs are outside the review; the pass's "Not applied" names only the pacer-live heading). Fix: "…agree with it on what each leg served; its commit-2 discriminator is qualified below", and list the two README time/discriminator slips under "Not applied" as follow-ups. Changes a number, disposition or action? no.

4. **NIT** — three small imprecisions in the round-1 record. (a) "measured at 3.0–4.7 s to issue in the renderer check": that is the final run; the first run measured 2,005 / 4,012 / 3,690 ms (re-derived), and the phase text correctly says "final run". (b) The gate-write bullet credits "Lanes 12-A and 12-B" for 5, 5, 5 and 2 in flight, but Lane 12-B's report said "4 of 6" for run 2; the orchestrator's 5 is right (own reader: writes at 6,683 / 334,133 / 535,221 / 539,852 / 789,703 ms each had a request open), so the record should say B's run-2 count was not adopted. (c) "Lane 12-A's and Lane 12-B's first findings change numbers … (the gate's writes, and the first renderer runs' times)": the times are Lane 12-A's second finding; and the handoff bullet omits the handoff's item-4 rewrite (the item-27 echo, Lane 12-C's "two handoff echoes"), which the diff holds (handoff hunk at line 56). Fix: wording only. Changes a number, disposition or action? no.

Nothing else: the squash, CI, signatures, dates, the gate and pacer code, the strand, the extras, the build dates, Phase 9's table and ruling, the filenames, the Status bullet, both handoffs' items and the triage all re-derive as the pass states them. "49–52 s" is the census's in-flight figure × 3; the pacer's own `maxRtt` is a lower bound measured at the last unanswered tick, so the live bound would have been up to ~1 s × 3 lower — "about 49–52 s" would be exact, not a change.

**WHAT YOU COULD NOT CHECK**

- Anything live: no service, no trio, no built canopy app; the wiring comparison's symmetric difference and the mutation check (labelled as the session's, as the pass says).
- That `main`'s mode store was an Input of the feeder "and the fetch went out at once" (Phase 11's reading of `main`; not re-fetched here).
- Whether the `:8052` leg hot-reloads (the run-3 provenance assumption, stated in the text); the README's run windows (17:43–18:47, 19:02–19:33, 19:33–20:04 CDT) are consistent with the three build dates.
- The load readings (32.7 at 18:17, 9.9 / 5.9) — README assertions only.
- Lane 12-C's finding 5 (the landing claims in the handoff's Git state / Created lists), deferred by the record until the PR lands; still a 404 branch state is not re-probed here.

**SECRETS/PII:** none read or printed; no `.env*` opened; git used read-only (`show`, `diff`, `log --format='%h %s'`); GitHub queries printed SHAs, dates, booleans and counts only; no e-mail address, token or environment value appears above.

## Lane 12-R2B (adversarial on round 1's corrections)

**Lane 12-R2B** (adversarial on round 1's corrections)
**VERDICT: SOUND-WITH-FIXES**

Worktree `squishy-growing-breeze` at `190c896c`; the two reviewed files in the worktree are byte-identical to `190c896c`. No tracked file modified; `git status` shows only the untracked round-2 brief. Own scripts under `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/D227803E-A1C2-4957-9A7C-824C3F8B44BD/scratchpad/lane12R2B/` (`replay.py`, `gate_reader.py`, `renderer_times.py`). Nothing below changes a number, a disposition or an action.

**TABLE**

| claim or correction | re-derived | result | evidence |
|---|---|---|---|
| The pass replays with no hand edit | imported `LEDGER_SUBS`/`HANDOFF_SUBS`/`ROUND1_RECORD`, applied to `git show c626e847:` copies; compared with `git show 190c896c:` | MATCH, byte for byte (963,638 and 10,717 chars); 17 + 6 substitutions, each anchor once | `replay.py` |
| Gate writes 9/8/8/8; `false` onto enabled 7/6/6/6; in flight at 5/5/5/2 | own reader of `raw.gate` + `raw.req` (W/A), and the archived analyzer | MATCH (Lane 12-B's round-1 "4 of 6" for run 2 reproduces on neither reader; the pass's 5 is right) | `gate_reader.py`; `…_analyze.py` |
| "at page load, at each trigger and at the census's own release after T-apply" | gate stamps vs `triggers`: 2 at load, 1 after T-gate, 2–3 after T-tab, 1 after T-apply, **none after T-mode**, all four runs | wording loose (Finding 4) | same |
| Renderer runs 17:29–17:41 / 17:29–17:40 CDT; triggers 17:38:59–17:40:12 | pacer requests 17:28:58–17:41:10, marks start 17:28:58; guard 17:28:59–17:40:17; triggers 17:38:59–17:40:12 | MATCH | `…T174112_pacer_run.json`, `…T174018_guard_run.json` |
| `extra` issued 3,010/4,693/3,687 ms, landed 6,695/8,047/7,397 ms, rtt 3.6 s | identical; rtts 3,685/3,354/3,709; first run 2,005/4,012/3,690 | MATCH | `…T201631_pacer_run.json` |
| Strand "re-issued at 31.0 s, applied at 35.0 s" | `reissue_after_ms` 30,998.96, `applied_after_reissue_ms` 3,969.33 → 34,968 | MATCH | `…T201631_pacer_score.json` |
| "would have set it to 49–52 s" | 3 × 16,363 = 49,089; 3 × 17,308 = 51,924; but `maxRtt` is `seen.t − issued_at`, a lower bound (≥ in-flight − one tick), so 46–52 s | upper estimate (Finding 6) | `dm_25c5c887.py:578–587` |
| Mode change waits for the ack plus up to one tick | `ack` is `State`, Inputs are the Interval and the mode store | MATCH | `dm_25c5c887.py:2679–2700` |
| No request yet → `no_update` until the bound | `seq=0`, `acked=false`, `issuedAt=firstSeen`, returns `NU` | MATCH | `dm_25c5c887.py:571–591` |
| `reason = changed ? 'extra' : (acked ? 'tick' : 'stale')`; `n=seq`; `return not (flags_ok and running)` with `experimental_functions` | lines 594, 4924, 7165–7167 | MATCH | same |
| `build_date` 22:43:05Z / 00:02:18Z / 00:33:31Z vs commits 23:28:34Z, 00:02:02Z, 00:19:57Z, 00:28:03Z, 01:19:15Z | identical | MATCH | status-bar JSON `serving`; `gh api pulls/731/commits` |
| "whose legs are the census runs' legs" | census `canopy` = `:8052`; `t0` 22:48:43Z, 23:17:24Z, 00:04:40Z, 00:35:55Z each after its build and before the next | consistent (inference by port and time; the census JSON carries no `build_date`) | census `raw.t0` |
| `__junPollPacerLastUnacked` "which commit 1 lacks" | 0 occurrences at `7aed1f2b` | MATCH | `gh api contents …?ref=7aed1f2b` |
| `25c5c887`: one parent `4f69524b`; 46 success, 7 skipped | identical (53 check runs); commit date 02:27:26Z, `merged_at` 02:27:27Z | MATCH; "(46 check runs, 7 skipped)" misreads (Finding 5) | `gh api commits/25c5c887`, `/check-runs` |
| Phase 9 table (`:8058` LANDS 13.0 s, `:8059` LANDS 19.7 s) and "stays counted **FIXED**" | ledger 8899–8906, 9673 | MATCH | ledger |
| Cleanup-procedure filename | long name exists, short name does not | MATCH | `ls` |
| Triage 79/56/1/2/20; 4 P1, 16 P2 | identical | MATCH | `e2e_finding_triage.py` |
| Record vs diff | every listed change maps to a substitution; the diff holds nothing unlisted (replay is exact); "five changed files" = 5 | MATCH | `git diff --stat 0e144c3c c626e847` |
| Lane credits | each matches the verbatim reports; the record silently overrides 12-B's run-2 "4 of 6" | MATCH (NIT, Finding 7) | round-1 file |
| Not-applied reasons | 12-C 6 (lint), 7b (README), 5 (deferred) each given a reason; 7a was "not a defect" | MATCH | record |
| Handoff items 25/27/28 venues; filenames; `canopy-e2e-arc-state.md` | consistent with ledger item 27; memory file exists (not in `MEMORY.md`'s index) | MATCH | handoff; `ls` memory dir |

**FINDINGS**

1. **MINOR** — item 27 now claims to be Phase 9 item 0's second half, but drops that item's venue condition. Ledger item 27: "This is the second half of F-CANOPY-055's own verification rule, and of Phase 9's item 0. Drive it on a demo leg serving canopy 0.9.0 or later". Evidence: Phase 9's item 0 (ledger 9716–9718) asks for the arm "re-driven on a leg **where the old code fails** and whose training may be started"; Phase 9's own demo drive (8899–8910) "does not discriminate … the old 1 Hz feeder also got responses through on the demo parent page"; the parent handoff's context block (line 257) still says "on a leg where old code fails and training may start". The F-055 entry's rule (8329–8330) says only "on a leg whose training may be started", so item 27 matches the entry but overstates against Phase 9 item 0 and the parent. Fix: in item 27 and handoff item 4, say the demo drive can show the arm reaches the paced bar but, as Phase 9 found, cannot discriminate from the old code; Phase 9 item 0's "where the old code fails" has no venue (a slow page that trains) and is recorded as unmet by design. Changes a number, disposition or action? no — the drive stays owed; what it can establish is stated more narrowly.

2. **MINOR** — the cost correction was applied to the Summary only. Ledger item 18 (unchanged): "the poll waits out its stale bound, at least 30 s and at most 120 s, counted from the request"; handoff "Completed": "The cost (… waits out the stale bound, 30–120 s)" and "a restart now waits out the stale bound". The corrected Summary: "re-issued only after its stale bound … and answered a tick and a round trip later (… re-issued at 31.0 s, applied at 35.0 s)". Item 28 asks to read "the lane's wait before its first applied answer, against the stale bound", which is bound + tick + round trip by the Summary. Fix: add "then a tick and a round trip" to item 18 and the handoff's two phrases. Changes a number, disposition or action? no.

3. **MINOR** — the record misstates when Lane 12-C's finding 5 is due. Record: "is checked after the PR lands, as that finding asks". Lane 12-C: "re-run against these three checks after landing. Fix: none now; verify **before the PR is marked ready**" — "landing" there is the API commits reaching the branch, not the merge. Fix: "checked once the commits land, before the PR is marked ready". Changes a number, disposition or action? no (the check's timing, not its existence).

4. **NIT** — "at each trigger" in the corrected gate sentence. No gate write follows T-mode in any run (last writes 744,000 / 789,703 / 741,583 / 730,977 ms; T-mode at 1,528,498 / 1,575,475 / 1,525,873 / 1,514,647 ms). Fix: "at T-gate and T-tab". Changes a number, disposition or action? no.

5. **NIT** — "CI on the squash passed (46 check runs, 7 skipped)" reads as 46 in all; there are 53: 46 success, 7 skipped (the record says so). Fix: "53 check runs, 46 successful, 7 skipped". No.

6. **NIT** — "would have set it to 49–52 s" is the top of the range: `maxRtt` is the age at the last pacer run that saw the request unanswered (`seen.t − req.issued_at`, lines 578–587), up to one 1 s tick short of the in-flight time, so 3× gives 46–52 s. Fix: "to as much as 49–52 s". No.

7. **NIT** — record accuracy: (a) "Lane 12-A's and Lane 12-B's first findings change numbers … (the gate's writes, and the first renderer runs' times)": the times are 12-A's finding 2; (b) the gate credit "(Lanes 12-A and 12-B)" omits that 12-B's run-2 "4 of 6" was not reproduced (both readers say 5); (c) "measured at 3.0–4.7 s to issue in the renderer check" is the final run only (the first run: 2.0–4.0 s; the ledger text says "final run" correctly). Fix: three words each. No.

**WHAT YOU COULD NOT CHECK**

Anything live (no service, no trio, no browser); the built-app wiring comparison and the mutation check (need canopy's environment); whether the `:8052` leg hot-reloads (the build-date basis assumes not; run 3 spans commits 3 and 4); the load readings (README only); Lane 12-C's finding 5 (the branch and PR are not on GitHub yet, as expected); the Linux host's worktrees; the lanes' unarchived scratch probes.

**SECRETS/PII:** none read or printed; no `.env*` opened; git used read-only (`show`, `diff --stat`, `log --format='%h %s'`, `status --short`); GitHub queries printed SHAs, dates, counts and code lines only; the auto-memory directory was listed by filename only.
