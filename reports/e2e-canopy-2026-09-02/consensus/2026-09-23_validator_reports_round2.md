<!-- markdownlint-disable -->

# Canopy E2E arc, Phase 8 (canopy#670) — validator reports, round 2, 2026-09-23 (verbatim)

Archived by util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py from the session's subagent transcripts: each is the last report after the agent's round-2 brief, which targeted the round-1 corrections frozen at canopy 85415f3c. EVIDENCE for Phase 8 of notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, not conclusions; the reconciliation is in that phase.

## Lane A2 - independent re-creation: does a pause survive slot contention (v1 vs v2)

*agent `a6a133770ac3da134` · round 2 · last-assistant-text (after its round-2 brief) · 7924 chars*

All my runs finished before I read any other lane's material, and every pre-registered arm matched its prediction. The three claims hold. The one inaccuracy is the "one tick late" wording in v2's comment and CHANGELOG.

## Lane A2, round 2: does a replay pause survive renderer slot contention (canopy#670 v1 vs v2)

**Entry point.** An independent re-creation. I wrote my own harness from the dash-renderer 4.2.0 source and the two builds' git objects. Both builds' JavaScript, their exact Output/Input/State lists and their component props are parsed from `git show <sha>:src/frontend/components/metrics_panel.py` at startup, never from the working tree. The verdict rule and predictions were fixed in the script's docstring at 14:15:16Z (sha256 `118e13f4…`), before the smoke run (14:15:22Z) and the main run (14:17–14:27Z). I read the pdup script, `laneB2/canopy_priority_census.py` and the ledger's Phase 8 only after every run ended (about 14:32Z). I only listed `laneB/`, never read its files.

**Claims, checked against the renderer source and then measured:**
- **Claim 1 holds: clientside callbacks share the 12 slots.** The slot count at :2846 applies to one `prioritized` list that holds server and clientside requests alike. With 12 server calls in flight, the replay requests waited about 4.5 s; with 11, they ran in 16–24 ms.
- **Claim 2 holds: a waiting request is replaced without its trigger, and v1 loses the pause.** At :3024, removal at :3151, a waiting request is dropped when a newer one of the same callback arrives. Trigger lists only merge while both are still in `requested` (:2985–3016). This happened in 20 of 20 contention trials with a running replay timer: the click's request entered `prioritized` 9–16 ms after the click, and the next tick replaced it 249–266 ms after the click.
- **Claim 3 holds, with one correction to its wording.** v2 applies the pause at the next run of the callback. That run only happens when a slot frees: 4.5 s after the click, with 5 ticks in between. So the "applies one tick late" wording in v2's comment (`metrics_panel.py:1192` at `85415f3c`) and its CHANGELOG understates the delay under sustained contention.

**Per-arm table.** The eight arms were pre-registered; n = 5 each, and all 40 trials passed the validity gates.

| Arm | Build | Load at the pause click | Held | Pause latency | Mechanism seen |
|---|---|---|---|---|---|
| A1 | v1 | 12 one-shot 6 s server calls (all 12 slots) | **0/5** | — | replaced 5/5; first run saw only the tick trigger |
| A2 | v2 | same | **5/5** | 4.507–4.513 s | replaced 5/5; pause applied from the click count, at the index shown when clicked |
| A3 | v1 | none (control) | 5/5 | 16–19 ms | click trigger present |
| A4 | v2 | none (control) | 5/5 | 17–19 ms | click trigger present |
| A5 | v1 | 11 calls (one slot free) | 5/5 | 16–24 ms | no wait for a slot |
| A6 | v2 with its count-based recovery removed | 12 calls | 0/5 | — | replaced 5/5 |
| A7 | v1, replay timer stopped | 12 calls | 5/5 | 4.500–4.525 s | click waited, then ran with its own trigger |
| A8 | v1 without my logging wrapper | 12 calls | 0/5 | — | replaced 5/5 (from the queue log) |

Post-hoc arms, designed after seeing the first results and not pooled with the table above:
- **Two pause clicks 1.5 s apart, 12 one-shot calls:** v1 held 0/5; v2 held 5/5, with both clicks consumed in one toggle.
- **12 periodic polls (every 1 s, 3 s latency):** v1 held 1/5; v2 held 5/5, in 0.19–0.93 s. v1's one hold was the trial where a poll freed a slot before the next tick arrived.

**The instrument, and whether it could have given the other answer.** It combines:
- a hook on dash's internal store that logs every change to the replay state, the play click count and the timer;
- a snapshot of each queue on every change, including the replay request's trigger list;
- a click listener that records how many slots are in use at the click;
- a logging wrapper around each build's JavaScript that records the triggers, the state read and the state returned.

It demonstrably could have answered differently:
- The same harness returned held for v1 in 15 of 15 trials without full contention (A3, A5, A7) and lost in 10 of 10 with it (A1, A8).
- Under identical contention it returned lost for v2 once the recovery was removed (A6), against held for real v2 (A2).
- Every trial checked that all 12 slots were in use at the click and that the click was delivered, so a held result can't come from missing contention and a lost one can't come from a missed click.
- The wrapper doesn't change the outcome: A8 without it matches A1.

**Where I differ from the other lanes:**
- **Priority ordering.** The pdup script (citing B2's census) says its pollers outrank the replay controls (`'13'` vs `'11'`). In dash 4.2.0 every request gets priority `"0"`, because the renderer's priority function (:1598–1602) drops its starting callback on the first pass; B2's port inverts that test. A runtime probe confirmed it: all 15 requests observed carried `"0"`, including one with a 3-callback fan-out. The queue is therefore first-in-first-out. B2's and pdup's measured drop counts stand; only that explanation is wrong.
- **Loss rates.** Theirs are lower (pdup: 5 lost out of roughly 42 v1 trials) because their pollers hold all 12 slots only 15–80% of the time. My loads hold them continuously. Once that is accounted for, the results agree.
- **v2 latency.** pdup's recovered pauses applied in 54–1023 ms. The delay is however long it takes a slot to free, not a tick period.

**What the evidence cannot support:**
- **Real-world frequency.** How often canopy's real page holds all 12 slots at a pause click is not measured; my load is synthetic. A loss needs all 12 slots held *and* a tick arriving before any slot frees. A5 and A7 each remove one of those and the pause holds.
- **Coverage.** Only 1x speed, dash 4.2.0, headless Chromium 147 on one host.
- **Harness is not canopy.** It uses plain buttons rather than dbc buttons, has no other canopy callbacks, and keeps the metrics store static, so the refill callback is registered with its exact signature but never ran.
- **Sample size.** 5/5 still allows a true hold rate as low as 48% (95% interval); the mechanism rests on the identical queue trace in every trial, not on n.
- **Timing phase.** The gap from click to next tick was about 250 ms in every main trial. That doesn't matter when slots are held for 4.5 s, but under periodic load it was sampled only 5 times.
- **v2's one-toggle rule.** A pause and a resume that are both pending end paused; that is v2's stated design choice, not something I tested as a defect.

A transient full `/tmp` (from outside my runs) occurred after all trials and did not affect them. Nothing was committed or pushed.

**Changed** (all new, uncommitted, in the `partitioned-twirling-stream` worktree):
- `util/ad-hoc/2026-09-23_f054_r2_laneA2_slot_contention_pause.py`
- `util/ad-hoc/2026-09-23_f054_r2_laneA2_slot_contention_pause_posthoc.py`
- `util/ad-hoc/2026-09-23_f054_r2_laneA2_priority_probe.py`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_slot_contention_pause.json`, with `.stdout.log` and `.server.log`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_slot_contention_pause_SMOKE.json`, with `.server.log` (not counted)
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_slot_contention_pause_posthoc.json`, with `.stdout.log` and `.server.log`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_priority_probe.txt`

**Referenced:**
- canopy `metrics_panel.py` and `CHANGELOG.md` at `c0530279` and `85415f3c`
- `dash_renderer.dev.js` (dash 4.2.0)
- `util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py`
- scratchpad `laneB2/canopy_priority_census.py`
- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 8

v1: 0/5 under contention; v2: 5/5

---

## Lane B - round 2 on the corrections

*agent `a734684513e7f8d2f` · round 2 · last-assistant-text (after its round-2 brief) · 9178 chars*

The premise does not hold. Under the coordinator's own K = 13 load, every request in `prioritized`, both the controls and the pollers, carried priority "0" across 680 samples. Arbitration is therefore by queue order, not the "13 vs 11" depth scores its docstring cites. Its measured results don't depend on that rationale, so this corrects the stated mechanism only.

## Round 2, Lane B: canopy#670 v2 (85415f3c)

**Short version:** v2 fixes all four of my round-1 findings. But one of its corrections creates a new way to undo a pause. A click that the recovery already applied from its count gets applied again when its own trigger arrives. I reproduced this 3/3 in dash-renderer 4.2.0, and a one-line change removes it.

**How I read v2.** I read it from the git object store only (loose and packed objects, decompressed directly with no git process), never from the fix worktree's working tree. All 339 blobs checked hash exactly to their tree entries, and the v1 blob equals my round-1 copy byte for byte.

### (a) Are the round-1 findings fixed? Yes, all four.

Clean room: Playwright route interception with no port bound. Twelve clientside Promise "holder" callbacks fill the renderer's 12 slots on demand. Verdicts read the Redux store. n = 3 per build.

| Finding | v1 (c0530279) | v2 (85415f3c) |
|---|---|---|
| Pause lost under slot saturation | PAUSE-LOST 3/3 | PAUSE-HELD 3/3, applied at +2527/2541/2535 ms (the slot release), index unchanged from the click |
| Cleared slider number box sets NaN | NaN index, "NaN / 119", 3/3 | index 5 kept, slider restored to 4.2017, 3/3 |
| Refill overwrites the index with a stale one | "5 / 239" while state is 6, 3/3 | "6 / 239", 3/3 |
| Absolute claims | — | bounded; one new claim is wrong (see (c)) |

### (b) What the corrections broke

**1. A click is applied twice: once from its count, then again from its own trigger (major, rare).**
- **Cause.** metrics_panel.py:155 applies a triggered button `max(pending, 1)` times, and the play branch (:161-166) toggles regardless of that count.
- **How it happens.** A tick request is waiting in `prioritized` when the user clicks pause. A slot frees before the renderer processes the click's request. The tick run sees the new count and pauses. Then the click's own request runs, its count is already used up, and it toggles back to playing.
- **Reproduction.** In the `double_pause` arm, v2 was PAUSE-UNDONE 3/3: paused at +6/11/12 ms, undone 14/16/18 ms later, still playing at the end. The run trace shows the tick run at +2 ms and the click run at +16 ms. v1 held 3/3 in the same arm. In `double_step`, one step click moves the index by 2 in v2 (3/3) and by 1 in v1 (3/3).
- **The test that pins it.** `test_a_triggered_click_applies_even_when_its_count_matches` encodes this rule. Its justification (a re-created button clicked up to exactly the recorded count) can't happen in canopy: the replay state and the buttons are rebuilt together in one layout chunk, and the controls callback is the state's only writer.
- **How often.** I re-scored the coordinator's own data (`2026-09-23_f054_pdup_cleanroom_v1_v2.json`) for a pause that applies and is then undone: 0 of 48 v2 trials. My first re-score used an 8 s window and wrongly counted the next trial's play click as an undo; I corrected it to the 900 ms window before that click. The race needs a slot to free within milliseconds of the click.
- **Fix, verified.** Use `times = pending[ev]` and skip a button event when it is 0. In the browser this gives 9/9 correct: `lost_pause` still held (about 2.52 s), `double_pause` held, `double_step` +1. On the v2 test suite, only the pinning test fails; the other 55 + 8 pass.

**2. Lost clicks are applied in a fixed control order, not click order (minor).** If the user steps forward and then presses play, and both triggers are lost, v2 ends paused; the user meant playing. Ordering by `n_clicks_timestamp` would fix it, or document it.

**3. One toggle per run (judgment call, no regression).** It loses intent for "pause, then resume" when both clicks are lost: v2 stays paused. It gets "lost pause, then pause again" right, where parity would not. Stock Dash also toggles once for a merged double click.

**Checked with no defect found:**
- Drift: every state-writing path records both `clicks` and `slider_w`, and the no-write path applies nothing.
- False seeks from `slider_w`: none after a history grows, none at the end of the replay, none at mount. When the store shrinks below the index, the slider is written values up to about 139 over 2+ s with no echo, 3/3 per build.
- `n_clicks` None vs 0: handled. Speed buttons: the double application does not affect them.
- A state without the new keys while buttons already have counts applies spurious clicks at the node level, but canopy can't reach that state.

### (c) Are the bounded claims true?

- **"No in-flight window once it runs":** true.
- **"It can lose a trigger before it runs":** true.
- **"No pending callback holds back its readiness":** true. I rechecked it on the built v2 app (177 callbacks, including main's merged changes).
- **"A lost pause applies one tick late":** false as written.
  - It applies at the callback's next run, and that can wait many ticks for a slot: 2.5 tick periods in my runs, and 10 of 16 recovered pauses in the coordinator's data took over one tick (maximum 4.09).
  - Meanwhile the replay does not advance: 3/3 in mine, 15/16 in theirs.
  - Without fix 1, the recovered pause can also be undone.
- **If the request that survives is itself replaced:** the pause still applies at the first run that executes. It just waits longer.
- **At the end of the replay:** the pause lands before the tick that would reach the end, so the replay stops one short of it (node sequence).
- **With the interval disabled:** only another click can replace the queued request, and that is exactly where `double_step` goes +2.

### (d) Verdict

MERGE-WITH-CHANGES. Three changes flip it to MERGE:
1. At metrics_panel.py:155, use `times = pending[ev]` and `continue` when it is 0.
2. Replace `test_a_triggered_click_applies_even_when_its_count_matches` with a double-application regression test: a run that applies the click from its count, then the click's own triggered run with the same count must change nothing.
3. Reword "one tick late" (metrics_panel.py:1192 and the CHANGELOG "Events come from values" item) to: applies at the callback's next run, which can wait for a slot, and the replay does not advance meanwhile.

### Record (§7 minimum)

- **Instruments, and whether they could have answered differently.**
  - Object reader: blob hashes verified, so a decoding error would have shown up.
  - Node sequence harness: shows what the JavaScript does for a given series of runs, not whether the renderer produces that series.
  - Browser clean room: it can discriminate. The same arms give v1 held/+1, v2 undone/+2, and v2+fix held/+1. I fixed one recorder blind spot before the scored runs: clientside runs are only visible in `watched`, not `executing`.
  - Re-score of the coordinator's data: corrected window, as described above.
- **Entry point:** the 723ee812..85415f3c diff; specifically the `times` rule at :155 and the test that pins it.
- **Sample sizes:**
  - Browser runs: 36 sessions (6 arms × 2 builds × 3), 9 v2+fix sessions, 2 diagnostics, and 1 priority census (680 samples).
  - Node: 11 sequences × 2 builds.
  - Tests on the v2 tree: 56 + 8 pass. On the parent 0fca86e9, all 56 fail, which also covers the 2 tests added after the coordinator's 54-test falsification. With my fix, exactly 1 fails.
  - Re-score of the coordinator's data: 85 held trials.
- **What the evidence cannot support:**
  - How often the double application happens on canopy's real page. It depends on main-thread load and on callbacks completing in the millisecond window. Lane B2's delay arms are measuring that window; I did not.
  - Anything about a live canopy run. I never touched :8055/:8056.
  - macOS or other browsers. My clean room uses `html.Button` rather than `dbc.Button`.
  - The coordinator's mutation-check run 3, which I did not see.
- **Process note:** my first launch waited on another lane's browser. It then died on navigation (`TargetClosedError`), and the retry's page crashed (`Target crashed`). The harness also leaked its own browser, which deadlocked the retry. I fixed that with close-in-`finally`, and every scored run completed. Before each launch the harness waits until no other lane's browser is running.

**Changed.** No tracked file in either repo; I did not touch the fix worktree.
- New scripts in `util/ad-hoc/`: `2026-09-23_f054_r2_laneB_gitobj.py`, `…_extract.py`, `…_sequences.py`, `…_variants.py`, `…_deps.py`, `…_cleanroom.py`, `…_rescore_pdup.py`, `…_priority_census.py`.
- New results in `reports/e2e-canopy-2026-09-02/transcripts/`: `2026-09-23_f054_r2_laneB_cleanroom_SMOKE.json`, `…_runs2.json`, `…_v2fix.json`.
- Referenced: `2026-09-23_f054_pdup_cleanroom_v1_v2.py` and its JSON.

**VERDICT: MERGE-WITH-CHANGES.** Make triggered buttons count-idempotent (metrics_panel.py:155), replace the pinning test, and correct "one tick late".

---

## Lane B2 - round 2 on the corrections

*agent `a7e7deb96ecf6b34a` · round 2 · last-assistant-text (after its round-2 brief) · 8936 chars*

## Round 2, Lane B2: canopy#670 v2 (85415f3c). Verdict: **MERGE-WITH-CHANGES**

v2 fixes the lost pause from round 1, but it can apply one click twice. For the play button that means a pause is applied and then undone, which is F-054's symptom through a new path. The fix is two statements.

Everything below was read from git objects only, never the fix worktree's working tree. Sources: v2's JavaScript (`git show 85415f3c:src/frontend/components/metrics_panel.py`), the renderer (`dash_renderer.dev.js`, dash 4.2.0), the source and transcript of `util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py`, and v2's tests (`85415f3c:src/tests/unit/frontend/test_f054_replay_block_clientside.py`). I did not rely on the CHANGELOG or code comments.

### (a) My round-1 points
1. **Count clicks: done, but it over-applies.**
   - Lost triggers are recovered. The adapted run scored v2 48/48 HELD, 0 DROPPED, 16 RECOVERED, against v1 with 5 DROPPED at K≥13. In my own 50 trials, the pause arrived by count 30 times, all HELD.
   - Counting was implemented as "count **or** trigger": `times = Math.max(pending, inTriggers ? 1 : 0)`. That produces finding D1 below.
2. **Absolute claims: done.** The code comment, CHANGELOG and test docstrings now say "no in-flight window once it runs; it can lose a trigger before it runs", and describe readiness only. Two leftovers:
   - The new sentence "a lost pause applies one tick late instead of never" leaves out D1.
   - The review numbers in the CHANGELOG ("3/3 … 2 of 12") and in the code comment ("PAUSE-LOST 3/3") name no transcript, and they don't match my round-1 numbers.
3. **Contended re-verification: done in a clean room, but the instrument cannot see this defect** (see (c)). Nothing has been re-verified on a live leg at 4x in my lane.

### (b) What the corrections broke

**D1 (should-fix before merge): one click applied twice. For the play button: paused, then playing again.**

How it happens in the renderer:
- A tick request T waits in `prioritized` (`:2846`).
- The user clicks. `setProps` writes the new `n_clicks` into the layout immediately. The click's own request C waits in `requested`, because the requested pass is deferred by `await wait(0)`, which is a `setTimeout` (`:2961`, `:4031`).
- If a completion arrives first, the prioritized observer (it watches `completed`, `:2902`) runs T against the current layout. v2 sees the new count and applies the pause by count.
- The deferred requested pass then finds nothing to deduplicate C against (`:3024-3027`). C runs with `times = max(0, 1) = 1` and toggles back to playing.

Evidence, from least to most direct:
- **Logic level:** `util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py` gives:
  - D1: a tick run leaves the replay paused; the click's own run leaves it `playing`, label ⏸.
  - D2: one step-forward click moves the index 20 → 22.
  - D3: a slider trigger carrying v2's own written value seeks one index low for 216,610 of 2,003,000 (idx, max) pairs.
- **The live renderer, with a construction:** `util/ad-hoc/2026-09-23_f054_r2_laneB2_double_apply_cleanroom.py` wraps the function in place and logs every run. In arm `k13_d60` (pollers like the adapted run's; zero-delay timers run 60 ms late, a stand-in for a late requested pass), run 3 trial 0 logged:
  `[k13_d60] trial 0: UNDONE pause_ms=58 undone_ms=202 … runs=[(['replay-interval.n_intervals'], 2, 1, 'playing', 'paused'), (['replay-play.n_clicks'], 2, 2, 'paused', 'playing'), …]`
  - Run 2 of the same arm gave the same sequence (undone at +449 ms) before the page crashed.
  - Totals: `k13_d60` 2 in 11 trials across two runs; `k13_d20` 0/10; `k16t_d60` 0/10.
- **A test pins the defect:** `test_a_triggered_click_applies_even_when_its_count_matches` asserts it. Its reason, a re-created button, cannot happen in canopy: the store and the buttons live in the same layout chunk and are rebuilt together.

**Minor findings:**
- **Order:** controls whose triggers were lost apply in `REPLAY_CONTROL_IDS` order, not click order. If end and then start are both lost, the replay ends at the end. Rare; follow-up.
- **Stale instrument:** `util/ad-hoc/2026-09-22_laneA_f038_m18_check.py:335` reads `replay-position.children` from the store, which is now a list of components rather than a string. Only that instrument is affected.

**Checked, no finding:**
- **`slider_w`:** no false seek around a refill, the end of the replay, a max change or the mount call. Every path that writes the slider also records `slider_w`.
- **Old-shape state:** the only states without the new keys are the layout default and a rebuilt chunk, and both come with fresh buttons.
- **`n_clicks` None vs 0:** `num()` treats them the same. My clean room left `n_clicks` unset, as canopy's buttons are, for 70 trials.
- **Return paths:** every path that applies a control also writes `clicks`. The only case that consumes a count without applying it is the deliberate one-toggle rule.

**The one-toggle rule:** keep it, since it beats parity and matches stock Dash on a merged double click. But its comment overstates what it protects. It only helps when both clicks are pending in the same run. Once a lost pause has already been recovered at the next tick, a repeat click toggles back to playing. And on canopy the DOM lags the state by 1.4–2.4 s, so that is the usual case. The rule also does nothing about D1, which crosses runs.

### (c) The adapted clean room
- **Faithful in wiring:** the 8 outputs in order, the split position spans, the refill's new signature, the load model, and JavaScript read from git objects (the actual run used `--v2-ref 85415f3c`; its default of reading the index is fragile). The instrument check passed: 24/24 K=0 trials executed.
- **Blind to D1:**
  - HELD is scored on the first `paused` record, read immediately.
  - `settle_not_playing` quietly re-pauses an undone replay before the next trial.
  - RECOVERED counts only runs with no trigger naming the play button, so a count-then-trigger double application scores as an ordinary HELD.
  - The page's main thread is idle, unlike canopy's 0.1%-idle page.
- **Re-scored:** `util/ad-hoc/2026-09-23_f054_r2_laneB2_rescore_undone.py` checks each HELD trial for a `playing` record within 1 s of the pause. It found 0 undone in 48 v2 trials, so its V2-HOLDS stands for the regime it sampled.

### §7 minimum record
- **Instruments:**
  - The node repro and the fix check could each have shown v2 staying paused; they didn't.
  - The re-score could have found a `playing` record after a pause; it found none.
  - The per-run wrapper sees a double application directly, whatever the verdict says.
- **Sample sizes, natural timing:** 0 double applications in 50 of my trials, 48 re-scored adapted trials and 10 `k13_d20` trials. The 50 are `k0sat`, `k13`, `k13sat`, `k16sat` and `k16t_d0` (10 each); `sat` is 35 ms of busy work in every 50 ms.
- **What the evidence cannot support:**
  - A D1 rate on canopy. It was never seen at natural timing. The 60 ms delay is a construction, and I did not measure how late canopy's requested pass runs (Phase 7 puts that observer at 45% of main-thread time).
  - Any live-leg claim for v2.
- **Environment hazard:** `/tmp` is at 100% of its inodes (1,048,576), mostly other sessions' scratch directories (798c2868… holds 411k files). It crashed two of my Chromium runs ("Target crashed" and ENOSPC); run 2 and run 3 therefore have logs only, no JSON. Other lanes' browser runs are exposed too.

### Minimal change that makes this a MERGE
Replace `var times = (ev === "replay-slider") ? 1 : Math.max(pending[ev], inTriggers[ev] ? 1 : 0);` with:
- `times = pending[ev]` for a button, skipping the event when `times <= 0`. The trigger then only decides order.
- For the slider, skip a trigger whose value equals `state.slider_w`.

`util/ad-hoc/2026-09-23_f054_r2_laneB2_fix_check.py` shows this fixes D1 (stays paused), D2 (one step) and D3 (no drift). Four cases v2 was built for are unchanged: a lost pause applies at the next tick, merged steps apply twice, one click applies once, and a user seek applies. Also:
- Turn the pinning test into tests of the D1, D2 and D3 sequences.
- Add an UNDONE verdict to the adapted clean room and stop its settle step from hiding one.
- Name the transcripts behind the CHANGELOG and code-comment numbers.

**VERDICT: MERGE-WITH-CHANGES**

**Created** (untracked, juniper-ml worktree `partitioned-twirling-stream`):
- `util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py`
- `util/ad-hoc/2026-09-23_f054_r2_laneB2_double_apply_cleanroom.py`
- `util/ad-hoc/2026-09-23_f054_r2_laneB2_rescore_undone.py`
- `util/ad-hoc/2026-09-23_f054_r2_laneB2_fix_check.py`

Transcripts are in my scratch directory `…/scratchpad/laneB2/r2/`: `double_apply_run1.json` and `.log`, `double_apply_run2.log`, `double_apply_run3.log`. They should be archived before `/tmp` is cleared. **Changed:** no tracked file, and nothing in the canopy worktree.

---
