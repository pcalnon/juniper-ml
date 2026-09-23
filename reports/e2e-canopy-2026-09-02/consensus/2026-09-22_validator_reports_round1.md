<!-- markdownlint-disable -->

# Canopy E2E arc — validator reports, 2026-09-22 (verbatim)

Archived by `util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py` from the session's subagent
transcripts. Each section is the agent's final report exactly as delivered; they are EVIDENCE for
Phase 7 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, not conclusions — the
reconciliation, including where a report was itself corrected, is in that phase.

## Lane A1 — F-CANOPY-053, DOM against the server (growth window 58→62)

*agent `a52c9cc62e2d76ef9` · last-assistant-text · 4920 chars*

**Verdict: REPRODUCED, with one qualifier: the freeze is not specific to this panel.** During my one growth window, canopy's `/api/state` said `candidate_pool_status: "Training"` without a break from +20.00 to +32.01 s. The badge, phase and pool size read "Inactive" / "Idle" / "0" in every sample, and a continuous in-page change recorder logged no change to them at any point. The Candidate Metrics tab was confirmed active in all samples. My DOM reader can see a change: a control element on the same page changed 5 of 5 times, once inside the Training interval. So under §2 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this is a real observation, not a blind reader.

**Counts**
- **Samples:** 32 paired DOM + `/api/state` reads over about 98 s. The median gap was 2.5 s, not the 1 s asked for, because each DOM read took 2.2 s median (11.2 s worst). A separate 1 Hz server poll and the change recorder cover the gaps.
- **Server said Training:** in 4 of the 32 paired samples, and in 13 of 106 polls from the 1 Hz server timeline.
- **Distinct DOM values:** badge 1 ("Inactive"), phase 1 ("Idle"), pool size 1 ("0"). The server said pool size 8 in all 32 samples, idle included.
- **Tab check:** exactly one `<a role="tab">` matched "Candidate Metrics". On every sample it had class `active nav-link`, the badge's pane had class `active show`, the badge was visible, and it was the only active tab. Each element ID I read exists exactly once in the page.
- **Positive controls:**
  - *Top status bar (your suggestion): 1 distinct value.* It showed "Stopped" / "0" hidden units throughout, while `/api/status` went COMPLETED → STARTED → COMPLETED and 58 → 62 hidden units. It also never moved in my two idle dry runs.
  - *Active control (added): 2 distinct values.* I clicked the Pool History header, whose icon flips ▼/▶ via a one-shot server callback. All 5 clicks were each followed by one request, one response and one icon change. One change landed at +20.60 s, inside Training; each took 9–15 s from click to DOM.
- **Wire traffic (secondary):**
  - The panel's store fetch was requested 51 times and answered 50 times. Four of the response bodies I read after the run carried "Training", so "Training" did reach the browser.
  - The callback that renders the badge, phase and pool size ran exactly once, at page mount, and never again.
  - Whether the store applied those responses can't be seen from the DOM.

**Canopy and growth**
- **Canopy:** `git_sha 9bffaba12ccc78e62c5f6b437fb0a9eccf46f088`, v0.8.1. The process started from a clean checkout at that commit.
- **Growth:** hidden units went 58 → 62, uuid `1cd15120-8f71-4319-ab7d-a384bfd692a9` unchanged, COMPLETED, exit 0. It was launched once, at +17.66 s (the first loop pass after 15 s), and finished at +36.5 s.

**What in the prompt was false or incomplete**
1. The top status bar is not "known to update". It never updated in any of my three runs, so the freeze covers more than this panel.
2. A non-zero `candidate_pool_size` is not specific to training. `/api/state` reports 8 at idle too, so the DOM's "0" is already wrong before any window.
3. The growth script does more than PATCH and start. It re-stages the dataset first and saves a snapshot afterwards (`snapshot_20260922T202310Z`). cascor now holds 62 units, so the next window needs `--to` above 62.
4. Minor points:
   - The badge starts empty, and "Inactive" is written by its first render.
   - The active tab has no `aria-selected` attribute, only the `active` class.

Everything else checked out: the sha, the version, `role=tab`, 58 units at start, and the Playwright interpreter.

**Remaining uncertainty:** this is one run in one headless chromium, under heavy concurrent load. Load average was about 10 on 16 cores, with 3 other validators' headless browsers and a canopy pytest run going at the same time. Timer-driven page updates were frozen across the whole page in all three of my runs, while click-driven ones landed 9–15 s late. I did not test whether an uncontended or visible browser behaves the same way.

The script's first analysis matched each click to the wrong icon change. I replaced that block in the record with a corrected, recomputed one and kept the old value in the record's `analysis_corrections` field. Nothing is committed.

Files are in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/`:
- `util/ad-hoc/2026-09-22_laneA1_candidate_panel_dom_check.py`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_candidate_panel_dom.json` (the real run)
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_grow_62.json` (the growth record)
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_dryrun_idle.json` (idle dry run, 68 s)
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_dryrun_idle_2.json` (idle dry run, active control)

---

## Lane A2 — F-CANOPY-053, CDP wire + an independent renderer read

*agent `a0e70163886796ab9` · last-assistant-text · 5689 chars*

**Verdict: REPRODUCED.** In every run the writer's responses reached the browser and the renderer's own code parsed them, yet the store never left its mount default `{}`. Two parts of the claim's wording are wrong, listed below.

I did not drive cascor. Canopy is on `main` (`git_sha` 9bffaba12ccc78e62c5f6b437fb0a9eccf46f088, same as local and `origin/main`). Its tree is clean and its build date was the same before and after every run, so it did not restart.

**Numbers** (pass 1, Candidate Metrics tab, about 60 s each)

| | run1 | run2 (perturbation check) | run3 (idle, all instruments) |
|---|---|---|---|
| writer requests | 27 | 25 | 30 |
| carried / no_update / unparsed | 27 / 0 / 0 | not captured | 30 / 0 / 0 |
| distinct delivered timestamps | 27 | – | 30 |
| distinct renderer values, subject (layout walk / fiber) | 1 / 1, both `{}` | 1 / 1, both `{}` | 1 / 1, both `{}` |
| delivered timestamps found anywhere in the layout | 0 of 27 | – | 0 of 30 |
| gap between requests, median (range) | 2.08 s (1.57–3.18) | 2.24 s (1.33–3.76) | 1.90 s (1.45–2.85) |

- **Positive control, same run and read path (run3):** `stream-health-store.data` had 12 values delivered, 9 distinct held, 8 changes on the walk, 9 distinct on the fiber and 8 in the apply log. The panel's Interval `n_intervals` changed 29 times on the same walk.
- **run1 control:** no response-written prop changed on the Candidates tab, so the second pass on Training Metrics served as the control. There, `metrics-panel-training-state-store` was applied twice and three figures changed.
- **run2** had no CDP session and no subscribe listener. The result was unchanged, so my instrument did not cause the discards.
- **The fetch probe (run3) confirms "discarded" directly.** The renderer's own `res.json()` resolved for 30 of 30 subject bodies, each carrying the store, and 0 were applied.
- **Wire classifier can say "not carried":** the tab-away response came back 200 with an empty response map. Unfetched or pending requests occurred only at browser teardown, outside the windows.

**Renderer read path.** A generic walk of `window.store.getState().layout` that finds the node by `props.id` and never uses `state.paths`. Alongside it:
- the committed React fiber tree (`memoizedProps.data`);
- a search of the whole layout for any `/api/state`-shaped payload, wherever it sits;
- a `store.subscribe` log of every change;
- a wrapper on `fetch` and `json()` that sees what the renderer's own code receives.

It could have produced a different answer. Each read registered changes on the controls above. My walk's path equals dash's own `paths.strs` entry (read once at the end, as a diagnostic), so it reads the node an apply would write.

Limits:
- Samples came every 1.7–2.0 s, not 1 s, but the subscribe log covers anything shorter-lived.
- The payload search keys on `candidate_pool_status`. That is adequate for this store but undercounts other stores.
- Everything ran in headless Chromium 147 with the main thread 66–75% busy in long tasks. I did not test a less-loaded browser.

**False or imprecise in the prompt:**
1. **"ONE distinct timestamp" is wrong.** The single held value is `{}`, which has no timestamp. None of about 50 carried responses per session was ever applied, including the two triggered by switching to the tab.
2. **The "about 10 changes on Training Metrics" figure is not stable.** I saw 8 applied of 12 delivered in idle run3, but 2 of 10 in run1, while cascor was training.
3. **The loss is not specific to this writer.** `latency-display.children` delivered 6–10 distinct values and held 1 in every pass I measured. `stream-health-store.data` had 0 of 12 applied in run1 and 8 of 12 in run3.
4. **"Every 1.7–2.0 s":** the medians fit, but the range is wider (1.33–3.76 s). There is exactly one request per Interval tick, and the Interval fires at 0.43–0.51 per second despite its 1000 ms period.

**Context for Lane B, not part of the verdict.** From `fetch()` to parsed JSON took 3.2–5.5 s in the page, against a network leg of about 30 ms. One to three Interval ticks fell inside every subject call, and the subject sat in the renderer's `watched` queue in 35 of 35 samples. That fits tick-boundary eviction, but I did not test the mechanism.

**Conditions and disclosure.**
- Cascor was COMPLETED (idle) when run1 started and was training by the end of its pass 1: that was the other validator's growth window. run2 and run3 were idle throughout.
- I read the memory note `reference_dash_renderer_12_slot_starvation.md`, which describes that mechanism, before measuring.
- I did not read `2026-09-22_state_store_consumer_roundtrip.py` or any `e2e_*` driver.
- I referenced `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 (Lane A) and changed no documents.

**Files** (created, uncommitted). The JSONs are 50–220 KB, larger than the directory's usual files, mostly per-sample raw series:
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA2_cdp_store_apply_run1.json`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA2_cdp_store_apply_run2_perturbation-nowire-noapplylog.json`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA2_cdp_store_apply_run3_full-with-fetch-probe.json`

---

## Lane A3 — F-CANOPY-053, source + one-variable period test

*agent `aba22c1e0f0b539b6` · last-assistant-text · 9042 chars*

All three runs returned **PERIOD-BOUND**. Writes land at 10000 ms, never at 1000 ms, and the tick is the evictor. One premise in the brief is misleading: the ~30 ms round trip is true on the wire, but the page processes each response 4–8 s later, and that delay is the window the eviction happens in.

The verdict rule's sha256 was `81eff334…` before run 1 and is identical in all three artifacts. The probe was edited once between runs 1 and 2, only to add network-layer timing outside the rule block. Everything ran on :8051 serving 9bffaba1, with cascor idle throughout. I made only GETs and did no PATCH. I didn't read the other validators' untracked 2026-09-22 `consumer_rt_*` / `fixture_grow_*` files in this worktree, to keep my entry point independent.

## Source findings (canopy origin/main 9bffaba1; I also read the served `/_dash-dependencies`)

**(a) Inputs, State, Outputs and their writers.** In `candidate_metrics_panel.py:247-268`:
- **Outputs:** `-training-state-store.data`, `-pool-history-store.data`
- **Inputs:** `-update-interval.n_intervals`, `visualization-tabs.active_tab`
- **State:** `-pool-history-store.data`
- `prevent_initial_call=False`, no `running=`.

Writers of each Input:
- **`n_intervals`:** only the Interval itself. No registered callback writes it, and none has it downstream.
- **`active_tab`:** the user's click, plus three `allow_duplicate` writers, none periodic:
  - the restore callback (`dashboard_manager.py:4042-4059`), which has an equality guard;
  - the tutorial trigger (`:4026-4036`), fed only by a click handler at `context_menus.js:112-117`;
  - the snapshot-op confirm (`hdf5_snapshots_panel.py:1265-1275`), fired by a click.
- There is no `persistence=` on the Tabs (`:1868-1875`).
- The CAN-000 gate (`:2459-2477`, list at `:463-487`, this interval at `:481`) *reads* `active_tab` and writes `disabled`. It does not write `active_tab`.
- One caveat: `layout-state-store` is `storage_type="local"` (`:1898-1902`), and dcc.Store listens for `storage` events. Another page in the same browser profile could therefore drive the restore callback. That is cross-page, not periodic.
- Live, every run showed exactly one `active_tab` change (my click).

**(b) Interval sharing and `disabled`.** The interval is not shared. The only callbacks that touch it are `fetch_training_state` (Input) and the gate (the sole writer of `disabled`).
- The gate's Inputs are `apply-in-flight.data` and `active_tab`.
- `apply-in-flight` is written at `:3956-3967`, `:3968-3980`, `:3985-4000` and `:5395-5403`, all apply-related.
- Live, `disabled` flipped once per run, at the tab switch.
- Nothing writes `interval` after layout. It is the 1000 ms default from `candidate_metrics_panel.py:93`.

**(c) Other re-requests under the same identity.** `getUniqueIdentifier` (`dash_renderer.dev.js:1715-1726`) hashes the callback's own inputs, outputs and state. So any trigger of this callback shares one identity. The possible sources are:
- its own tick;
- any `active_tab` write (apply re-requests on every returned prop even when the value is unchanged, `:2509-2511`);
- a remount when the tab children are rebuilt (`dashboard_manager.py:2727-2734`, only on a model-class change);
- a page reload.

Live, the interval's layout path never changed, so there was no remount. No other callback can hold it back: only four callbacks have `active_tab` downstream, all click-driven. The 12-slot pool was not binding either (`watched` 6–9, `executing` 0, `prioritized` 0 at tick times).

**Renderer sites, with their enclosing functions checked:**
- `:2676` moves executing entries to `watched` (executingCallbacks observer).
- `:2689-2699` awaits the response, then discards it if the entry is no longer in `watched`. The `find` is at `:2699`, not `:2698`.
- `:3024-3027` computes the duplicates inside the requestedCallbacks observer, after `wait(0)` at `:2962`. The actual removal is dispatched at `:3151`.
- The page serves `dash_renderer.min.js`. I grepped it and it has the same logic.

## Causal test (one variable: `interval`, set through the Interval's own `setProps`)

Scored, tick-driven writes landed / issued:

| run | 1000 ms | 4000 ms | 10000 ms | verdict |
|---|---|---|---|---|
| run1 | 0/74 | 0/13 | 8/8 | PERIOD-BOUND |
| run2 | 0/67 | 1/13 | 7/8 | PERIOD-BOUND |
| run3 (lighter reader) | 0/84 | 4/13 | 8/8 | PERIOD-BOUND |

- **The change took.** Delivered tick gaps were 1.69–2.26 s at 1000 ms, 4.14–4.24 s at 4000 ms and 9.87–10.0 s at 10000 ms, and the interval read back correctly each time.
- **Distinct store timestamps seen in the renderer.** At 10000 ms: 9, 8 and 9. In the 1000 ms phases: 0. The only exceptions are three single values from requests issued in the previous, longer phase, and those were not scored.
- **The effect reverses.** Returning to 1000 ms after the 10 s phase stopped landing again every time, so this is not a time trend.
- **Positive control.** The end-of-run sentinel, written through the Store's own `setProps`, was seen in all three runs, and the reader also saw the real 10 s writes. The tab-switch write never landed in any run, because it is itself a 1000 ms casualty.
- **Visible symptom at idle.** The panel isn't frozen at an old value; it stays at its empty-state defaults. It showed Pool Size "0" while `/api/state` said 8, and showed "8" after the 10 s phase.

Diagnostic evidence for the mechanism (not part of the pre-set verdict):
- **Lifecycle reader.** Every in-flight entry at 1000 ms and 4000 ms (161/161 in run 1, 153/153 in run 2) left `watched` with a new instance of the same callback queued, a median 65 ms after its own tick.
- **Per-request split, all three runs.** A tick inside the window meant no landing in 477 cases and a landing in 2, both within 0.14 s of the measurement boundary. No tick inside the window meant a landing in 36 of 36.
- **Timing.** The network layer shows 27–35 ms median total per request. The page processes headers 1.4–2.9 s after they arrive and finishes the body 4.3–7.7 s (median) after the network is done, up to 11.6 s at the worst.

## Would `running=` (canopy#613's pattern) fix it?

Predicted yes, but I did not test it, since that needs a code change and a restart.
- **Why it should work:** the only evictor observed is this callback's own tick. `running=` disables the interval when the request is sent (`:818-820`) and re-enables it in `completeJob()` (`:925-935`, called at `:966-971`, just before the promise resolves). The discard check at `:2699` then follows with no timer gap in between, so no own tick can land inside the window.
- **Residual risks:**
  - The Interval only clears its timer when React re-renders it, so under this page's multi-second stalls a tick could still slip through. Unmeasured.
  - The CAN-000 gate is a second writer of this `disabled` and would re-enable it on any tab or apply change. A mid-flight tab change also re-requests the callback through `active_tab` directly.
  - The error path (`:987-998`) never calls `completeJob`, so a network failure would leave the interval disabled. The existing strand watchdog (`dashboard_manager.py:2509-2537`) only covers `metrics-store-interval`.
- **Cost:** a refresh roughly every 6–10 s (the 4–8 s page-side delay plus one tick). The page-side lag itself, which is what makes every poller's window long, would remain.

## What in the brief is false or imprecise

- **"Round trip ~30 ms":** true only on the wire. The window that matters is 4–8 s of page-side processing.
- **"Discard decided at APPLY time":** the eviction happens when the tick is processed (median 65 ms after it). `:2699` only enforces it when the response is finally handled, and apply never runs.
- **"0.7–7.0 s":** here the page-side lag had medians of 4.3–7.7 s and a maximum of about 11.6 s.
- **"Frozen":** the panel shows its empty-state defaults, not a stale value.
- **Minor:** `:2698` should be `:2699`; the served bundle is the minified one, not dev; F-052's victim was a figure, not a store; "every response carries a new value" holds only for the state store, since pool-history is written only when it changes.

## Files (none committed, no canopy file modified)

Documents referenced: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (§2) and `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (Phase 6).

**Created**, all under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/`:
- `util/ad-hoc/2026-09-22_laneA3_candidate_tick_period_test.py`: the probe.
- `util/ad-hoc/2026-09-22_laneA3_tick_inside_window_contingency.py`: the after-the-fact per-request split.
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA3_candidate_tick_period_run1.json`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA3_candidate_tick_period_run2.json`
- `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA3_candidate_tick_period_run3_nolifecycle.json`

Run 1's JSON has no network timing; that was added from run 2 on.

---

## Lane B1 — F-CANOPY-053, the case against filing, severity and the matrix changes

*agent `a49508ce07544c118` · last-assistant-text · 11209 chars*

I attacked dispositions 1, 2, 3 and 5. The finding itself holds up, but most of the reasons the draft gives for filing it, for P1, and for flipping the matrix rows do not. All figures below come from the artifact JSONs, canopy source at `9bffaba1`, and the ledger, matrix and plan. I modified no files and ran no browser probes or cascor actions.

Documents referenced:
- Draft: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel/reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_F053_reconciled_measurement_DRAFT.md`
- Ledger: `…/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
- Matrix: `…/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`
- Plan: `…/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`

**Changed**: none.

## Disposition 1 (file as a NEW finding at P1): WEAKENED — filing survives, its supports mostly don't

- **The precedent is misdescribed.** `…VALIDATION-EVIDENCE.md` :6992 heads F-052 "NOT a separate defect — this is F-CANOPY-035's mechanism on the next callback". :646 says F-052 was "first mis-filed as the separate finding". canopy#613's title (b7922569) is F-053's exact mechanism: "the metrics-store poll re-requested over itself, so no response ever applied (F-CANOPY-035)". The precedent supports P1, but it also says this is not a separate finding. The draft can't claim both from it.
- **The draft omits three prior entries.**
  - F-027 (`…VALIDATION-EVIDENCE.md` :345, P0/P1): "three panels stay frozen at mount defaults through a whole live run". It was fixed and re-driven live on 2026-08-24, on this panel and these five rows.
  - F-050 (:6713): the same symptom, filed at **P2** on 2026-09-08 "as the third instance of the F-CANOPY-035 class", then withdrawn for tab bleed. Its re-filing condition is met by A1 (`active_tab_per_sample: {"Candidate Metrics": 32}`), A2 (`active_tab_inputs: {"candidates": 27}`) and A3. That point favours the draft, but it must be cited.
  - F-048 (:6525, still OPEN at **P2**) is described at :6540 as "Same family as F-035, same fix at the trigger". The draft needs to reconcile P1 with it, or re-grade F-048.
- **The contract citation leaves out the row that applies.** F-004's contract (:183–188) has a fourth row: "during-run steady-state polling surfaces — best-effort; **no freshness guarantee**". The panel's refresh during a run falls under that row. The real ground for filing is the scope limit at :190–193 ("does not cover a surface that never renders at all"), the same absent-not-late ground F-035, F-052 and F-037 were filed on.
- **"Permanent" is not established.** What is established: on 9bffaba1, 0 periodic applies in every observed 1000 ms window. The longest is about 3 minutes continuous per A3 run (tab switch at 20.7/25.5/24.1 s, first 10000 ms phase at 204.1/214.6/208.2 s). Every other window is 60–107 s. The result depends on page lag exceeding the tick gap, and that lag responds to load (next section).
- **Wording I'd accept:** "Third victim of the F-035 class (P1 per the F-052 re-disposition), cross-referenced to F-027 and F-050. Outside F-004's contract under its scope limit: of the 11 cited sessions whose DOM state is observed or implied by the store, the panel showed data in only one. No write applied in any observed 1000 ms window, the longest about 3 minutes. Measured only at host load 7.8–15.4, where load was recorded."

## Harness-bound? Partly — it affects the first write and the size of the lag, but doesn't explain the defect away

- **Load was 7.75–15.37, not "5–10".** Recorded values: A1 `preflight.loadavg` 10.11; A1 dry run 2: 8.50; A2 `meta.loadavg_before`/`_after`: run 1 11.47→15.37, run 2 14.74→13.31, run 3 8.88→7.75. No artifact records anything lower.
- **The WebSocket was refused, and the draft doesn't record it.** All three A1 sessions logged repeated handshake 403s on `/ws/training` and `/ws/control`, as did A3 run 2 (`console_error_count` 22). A3 runs 1 and 3 on the same leg logged 0 errors, so the origin allowlist is not the cause. It fits the per-IP cap (`settings.py` `max_connections_per_ip = 5` at 9bffaba1; A1's preflight shows `active_connections: 5` and 3 other renderers). It did not change A3's result (0/67 with the WS refused vs 0/74 and 0/84 with it connected).
- **Apply capacity rises and falls with load.**
  - A2's positive control (`stream-health-store`) applied 0 of 12 in run 1 (load 11.5–15.4) and 8 of 12 in run 3 (load 8.9).
  - A2's own verdict for runs 1 and 2 is `INDETERMINATE` ("controls=0"). The draft quotes only run 3.
  - The first write after tab activation was held in all 4 sessions run outside 20:06–20:43Z, and in 0 of the 10 inside it. Every one of those 10 overlapped at least one other browser on :8051, per the start times and the replay probes' `read_at`. This is an observation, not a controlled comparison.
- **What survives against the harness objection:**
  - Those same 4 lower-concurrency sessions delivered 126 periodic writes and applied no new value after the first.
  - A2 run 2, with its wire capture and apply log turned off, gave the same result at a higher busy fraction (0.747 vs 0.662).
  - The probe's in-page cost is about 3.5 ms (walk) plus 7 ms (fiber) per ~2 s sample, too small to create the lag.

## Disposition 2 (overturn the 09-11 sibling sweep): WEAKENED — right conclusion, wrong reason

- The sweep (`…VALIDATION-EVIDENCE.md` :7306–7339) was about consumers being evicted. The draft's own data clears the consumers: 7.3–9.3 ms round trips, 0 overlaps, one request each. In the growth run the consumer's output did apply (pool size "0" at t=2.9 → "8" at t=10.7).
- What falls is the sweep's premise that the store changes at 1 Hz in the renderer, and its "nothing observed is broken". The sweep was an AST check against ced1dd80 (:7309), but that phrase rested on a 2026-08-24 observation at f9defb4 (:7325–7328).
- **Wording I'd accept:** "The sweep's 'not broken' is superseded (it was based on f9defb4, not ced1dd80). Its consumer analysis is moot on 9bffaba1, not refuted: the store changes at most once per session in the renderer. The defect is upstream, in the writer."

## Disposition 3 (M-CANDIDATES-01/-02/-03/-04/-06 → FAIL): justification REFUTED, conclusion WEAKENED

- **The rows assert content, not liveness** (`…TEST-MATRIX.md` :457–462):
  - -01: "Pool status + colour"
  - -02: "Pool phase; default `"Idle"`"
  - -03: "Pool size; default `"0"`"
  - -04: "Hidden unless `candidate_epoch` **and** `candidate_total_epochs` are present; then … shows `e/T`"
  - -06: "'No active candidate pool' placeholder, or the pool display"

  So -02 and -03 list the mount defaults as expected values, and -06 accepts the placeholder.
- **"The historical PASS was probably scored on mount content" is refuted by the ledger itself.** Phase 2 (`…VALIDATION-EVIDENCE.md` :5564–5607, run `20260824T080426Z`, "five rows proven live") records "badge `Inactive`→`Training` … pool `0`→`40`, progress … `351/400`, pool-info placeholder→Top-2-candidates table". The f9defb4 re-measure from today agrees: `…_idle_baseline_f9defb4.json` holds 3 distinct store values, and DOM pool size goes "0"→"8" at t=23.6.
- **-04 was never read on main.** No probe reads `candidate-metrics-panel-progress-section`, even though the server exposed `candidate_total_epochs: 3000` during A1's candidate window. Its FAIL is inferred from the store, not observed.
- **Wording I'd accept:** "PASS on liveness at f9defb4. Regressed on 9bffaba1: -01/-02/-03/-06 observed frozen through a 13 s server candidate window (A1); -04 inferred only. Amend the expected results to state a tracking criterion, then record FAIL @ 9bffaba1."

## Disposition 5 (record the top status bar, don't file it): REFUTED as classified

- `update_unified_status_bar` is driven by `Input("fast-update-interval", "n_intervals")` (`dashboard_manager.py:3851`) and has no `running=` guard, so it has the same structure as the F-053 writer. Its requests arrive at about 0.47/s, and `latency-display` held 1 of 6–10 delivered values.
- By the draft's own A3 mechanism, this is F-053's failure on a fourth callback, not "F-004's accepted class". Filing the tab panel at P1 while only recording the global status bar is inconsistent in either direction.
- Every top-bar observation comes from A1, which ran with its WebSocket refused and 2–3 other browsers running.

## Universal-quantifier failures

- **"Never applies after mount."** The first write after the tab opened applied in 3 cited sessions (61-key store values at 19:49:20.7, 19:53:16.8 and 19:55:36.6 Z).
- **"No periodic write applies while its tick is faster than the lag."** At 4000 ms the median tick gap (4.1–4.2 s) was shorter than the median round trip (4.3–5.4 s), yet 5 of 39 writes landed. The rule holds per write, not per regime.
- **"0 across every other run's window."** False for the f9defb4 run (3 applied) unless the claim is scoped to 9bffaba1.
- **"36 of 36."** That holds at a 0 ms cut. At the contingency script's own 500 ms cut it is 38 of 43 (re-derived).

## Numbers that don't match their artifacts

1. "Landed in the orchestrator's first two sessions and in no other": it was **three**. `…_growth.json` shows 20 of 20 reads at 61 keys, timestamp 1790106936.63. "One run in five" is really 3 of 10 direct-read runs.
2. "Page-load write": the page-load write is `no_update`. A2 `raw.writer_requests[0]` shows a 28-byte body with no outputs, and the source at 9bffaba1 returns `no_update` when `active_tab != "candidates"`. The first write that carries data is triggered by `visualization-tabs.active_tab`.
3. "Not stale data": in the growth run the DOM showed pool size "8" in 19 of 20 samples. That is stale real data, not mount defaults.
4. "Load 5–10": recorded values are 7.75–15.37.
5. "27/25/30 … all carrying the store": A2 run 2 recorded `outcomes: {"not_captured": 25}`, so nothing is known about its bodies.
6. A2 described as "idle": run 1 ended pass 1 with cascor `STARTED`, because A1's growth run started inside that window.
7. "Tick every 1.3–3.8 s": the orchestrator runs recorded `gap_ms` from 616.8 to 9986.2.
8. "4.3–7.7 s (median)": the per-phase medians span 4.08–7.72 s.

## Single most important correction

The f9defb4 PASS was scored on liveness (ledger Phase 2, 2026-08-24). So F-053 looks like a regression between f9defb4 and 9bffaba1 of the symptom F-027 fixed, not a latent defect the matrix mis-scored. The draft never mentions F-027. This changes the justification for disposition 3, the framing of disposition 1, and adds an action: find what changed in canopy between f9defb4 and 9bffaba1.

## Leads, single-source — please re-derive

`…_candidates_idle_GPU_lowload.json` (20:49Z) is uncited and appeared after the draft, and its load was not recorded. Its store held a 61-key value from t=0.9 s, yet no consumer request fired in 90 s and DOM pool size stayed "0" in all 23 samples. That points to a second blocker between the store and the DOM, consistent with the claimed-Input promotion block the ledger records for F-048. It backs the symptom under lower load, but it undercuts "self-eviction" as the complete mechanism.

---

## Lane B2 — F-CANOPY-053, the fix direction and the mechanism

*agent `a31bd7134aa2dd613` · last-assistant-text · 12340 chars*

I found a regression in Disposition 4, the proposed fix. The mechanism claim holds for the writer, but its wording needs to change. I changed no files.

**Method.** I read the dash 4.2.0 renderer (`dash_renderer.dev.js` in JuniperCanopy1), the `dcc.Interval` source from the shipped `dash_core_components.js.map` (`Interval.react.js`), canopy `origin/main` 9bffaba1, and the diffs of canopy#613 and #614. I re-analysed `2026-09-22_laneA3_candidate_tick_period_run{1,2,3_nolifecycle}.json` with `json.load`. The cadence and cascade figures below come from a Monte Carlo over A3's own distributions:
- **L** (request to page-side body parse): n=518, p50 5.09 s, p90 6.74 s, max 11.58 s.
- **τ** (tick gaps in the 1000 ms phases): n=253, p50 1.98 s.

That Monte Carlo is a model on an idle `Completed` fixture, not a measurement.

## Item 1: Disposition 4 of `2026-09-22_F053_reconciled_measurement_DRAFT.md` (the fix). REFUTED as specified

**1a. Where `running=` releases. WEAKENED.**
- `completeJob()` is defined at `dash_renderer.dev.js:925-937`, inside `handleOutput`, inside `handleServerside` (:807-1004). This is the path taken: `useWebSocket` is false (:1311), the call is at :1330, and A3's wire shows HTTP POSTs.
- It is called at :970 (:966 on the `dist` path, :979 on 204, :983 on non-OK). That is before `finishLine`→`resolve` (:906-924). The `:2699` check (executingCallbacks continuation :2677-2718) and the apply (executed observer, applyProps :2457-2482, triggered synchronously from :2707 via StoreObserver :370-385) both come after it.
- There is no macrotask gap in between. A re-enabled Interval needs a fresh full period before it can tick.
- Corrected wording: "released in `completeJob()` a few microtasks before the discard check and the apply; equivalent for the guarded request."
- The loophole: the release belongs to the HTTP request, not to the `watched` entry. There is no fetch abort (:822-866). An **evicted** request's `completeJob` still writes `runningOff` (:931-932).

**1b. Can a tick slip in during a stall? SURVIVES.**
- `Interval.react.js` only clears its timer in `UNSAFE_componentWillReceiveProps`→`handleTimer`, and `reportInterval` does not check `disabled`.
- But the `running` disable is dispatched synchronously: prioritized observer :2853 → :1330 → :819. The re-render then flushes in a microtask of the same task: `createRoot` :5520, react-redux `useSyncExternalStoreWithSelector` :14179.
- Ticks that arrive before dispatch are merged into one request (:2987-3016), so they do no harm.
- A3 measured tick-to-drop latency at median 60 ms, max 529 ms. This is the `wait(0)` pass at :2962.

**1c. Gate or `active_tab` writing mid-flight. REFUTED.** The draft never mentions that this lane is **tab-gated**: `("candidate-metrics-panel-update-interval","candidates")` at `dashboard_manager.py:481`. #613's lane was not: `(_METRICS_STORE_INTERVAL, None)` at :473.

- **Deterministic tab-gate defeat.**
  - `fetch_training_state` runs on every `active_tab` change (Input at `candidate_metrics_panel.py:254`).
  - Off-tab it returns `no_update` ×2 (:260-261). Dash turns that into a 204 (`dash/_callback.py:604-605`), and the renderer still calls `completeJob` (:979), which sets `disabled=False`.
  - The gate is clientside and writes first; runningOff lands about L later and overwrites it.
  - Measured ordering at page load: the gate wrote `disabled=True` at 2.54 / ≤4.29 / 2.77 s. The first `fetch_training_state` dispatches came at 5.41 / 9.47 / 6.01 s, all after it.
  - Under the fix, the lane would poll forever on the default Training Metrics tab after every page load. That is the pattern `dashboard_manager.py:449-450` forbids ("has already spent the round-trip and the slot").
  - No unit test catches it: `running=` is not a registered writer.
- **Tab activation.**
  - The gate's `disabled=False` landed 0.90 / 0.75 / 0.20 s **after** the tab-switch fetch was dispatched, so it would override the running disable.
  - The first tick (29.58 / 34.13 / 31.67 s) came before that fetch's response was delivered (31.94 / 37.09 / 33.25 s). The tab-switch fetch was evicted in 3 of 3 runs.
  - The evicted request's stale runningOff then re-enables the clock during its successor's flight. #614's "self-healing, bounded to one cycle" is wrong.
  - Model: mean 3.6–4.3 responses discarded per activation. Time to first apply p90 is 34–37 s, and about 7.5% exceed the 40 s fresh-session limit.
- **Apply clamp.** A fetch in flight when an apply starts writes `disabled=False` mid-clamp. This also affects #613's shipped lane.
- **#614's watchdog, extended as it is.**
  - It only stands down while an apply is in flight (`dashboard_manager.py:2513`), so on this tab-gated lane it would force-enable the poll 30 s after the user leaves the Candidates tab.
  - It uses a single shared global (:2515-2526).
  - Its 30 s threshold was sized at 10× a 3.0 s round trip. This lane's observed maximum is 11.58 s, so the margin is only 2.6×.

**1d. Cadence and contract. SURVIVES, with a corrected citation.**
- The 10 s arm did not lower L: median 7.73 / 4.41 s, against 5.81 / 4.53 s in the 1000 ms phases (run2 / run3). Guarding this writer will not shorten L.
- Modelled guarded write cadence: p50 7.1 s, p90 8.9 s, p99 10.9 s.
- The three consumers are serverside, so the badge's data is about 10.3 s old when it paints (p90 12.7 s). About 11% of consumer renders would be evicted by the next store write.
- The F-CANOPY-004 row that governs refresh is "during-run steady-state polling surfaces: best-effort; no freshness guarantee" (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:188`). A 6–10 s refresh is inside the contract.
- Disposition 1 cites the ≤16 s and ≤40 s rows instead. Those govern first paint. The correct basis for filing is the scope-limit clause at :190-193.

## Item 2: Is this the right lever? WEAKENED. It is a bridge, not the remedy

- **The cost comes from the rate of state changes.**
  - Every Redux dispatch re-runs every mounted component's selector.
  - `dbc.Tabs` and `dcc.Tabs` set `dashChildrenUpdate`, so `visualization-tabs` walks the whole `layoutHashes` map (:10888-10901) on every dispatch (:5039-5095).
  - The requestedCallbacks pass fires on every `requested`/`completed` change (:3166). Its `getReadyCallbacks` (:1633-1665) re-walks each pending callback's whole downstream closure with no caching (:1617-1632), over six lists (:3827, :3575-3584).
- **Profile** (`2026-09-22_idle_cpu_profile_training_metrics.json`):
  - The layoutHashes selector is 26.6% of self time and `useSyncExternalStoreWithSelector` is 13.3%.
  - `notifyNestedSubs` is 90.5% inclusive and the requestedCallbacks observer (2:173719) is 45.05%.
  - Idle time is 0.1%, and this was recorded on Training Metrics, where the candidate lane is gated off.
- **Case against the per-writer guard.**
  - The page is saturated without this poller, and slowing it did not change L.
  - A per-writer guard makes one writer tolerate the lag without reducing it.
  - Every poller with a period shorter than L stays broken; Disposition 5's status bar and latency-display are two already. The shared fast lane cannot be guarded one rider at a time (#613's own note).
  - `running=` also adds 6 dispatches per request (:795-803).
- **Case for it.** It is the only change measured to turn never-apply into apply (#613: 0 → 66 rows on matched legs). The panel currently shows *wrong* values (pool size 0 against 8). The systemic work is larger and already scheduled.
- **Net.** Ship a per-writer bridge that does not write `disabled`, plus cheap cuts to the dispatch rate, and prioritise the structural work.
- **Churn leads found in source** (costs not measured):
  - `metrics-panel-update-interval` (`metrics_panel.py:555`) ticks at 1 Hz and nothing in `src/` consumes it.
  - `replay-player-panel-weight-drain` (`replay_player_panel.py:137`) ticks at 500 ms and is not gated. Its comment at :133-136 says it rides the fast lane; the code gives it its own interval.
  - `fetch_training_state` sends `/api/state` with a fresh `timestamp` on every call, which defeats no-op suppression.

## Item 3: Mechanism wording. SURVIVES for the writer; wording WEAKENED

- **The contingency reproduces** (`util/ad-hoc/2026-09-22_laneA3_tick_inside_window_contingency.py`, shave 0): 2 of 479 landed with a tick inside the window, 36 of 36 without. On its own it is confounded with period and round-trip time.
- **What does separate the mechanisms:**
  - The 10 s arm landed 23 of 24 with equal L, so slow responses do land.
  - Every `watched` drop (161 in run1, 153 in run2) had this callback's own new instance already promoted (`r=0, p=1, e=0`). That is the `:3027`/`:3151` path.
  - Triggers: 172 / 166 / 185 requests came from `n_intervals`, against 1 from `active_tab` per run.
- **"prioritized 0 / executing 0" is verified, for scored windows only.** In all 15 scored phases both were 0 (median and max), and `watched` never exceeded 9.
  - Outside scored windows, 14 tick samples had `watched=12`, the 12-slot cap saturated, with `prioritized` up to 40. These were at page load and 10–25 s after the tab switch.
  - The "executing 0" check cannot tell mechanisms apart: :2676 empties `executing` into `watched` synchronously.
- **`getReadyCallbacks` refusal.** It does not apply to the writer, but it blocks the **consumers**. While the writer is pending, anything taking its output as an Input cannot be promoted (:1641-1664), and today the writer is pending essentially all the time.
  - F-CANOPY-052's own wire census reported "0 loss-plot responses on every non-render" (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:7243-7251`). That fits readiness-blocking, not eviction, and its "rewritten every second" premise contradicts F-053. This is a lead only; I did not open the 09-11 artifacts.
- **Corrected wording.** Replace "own-tick self-eviction" with: "same-identity re-request eviction, triggered by the callback's own ticks, whenever page-global response-delivery latency exceeds the tick period". "Page-side processing" is really main-thread queueing: the renderer applied about 0.05 s before the probe's clone-parse (`wire_to_apply_s_of_landed`).

## Recommended fix plan, in order

1. **Immediate.** Do not put `running=` on `disabled` for this lane, and do not reuse #614's watchdog as it is.
2. **Immediate.** Choose one:
   - (a) Set this panel's `update_interval` to 10000 ms. This is measured (23 of 24 landed) and adds no new writer.
   - (b) `running=[(Output(interval,"max_intervals"), 0, -1)]`. `handleTimer` stops independently on `max_intervals === 0`, so the gate stays the only writer of `disabled`. Add a watchdog that writes `max_intervals` with a threshold of at least 60 s. This option is unmeasured and needs a clean room plus a live leg.
3. **Immediate, same PR.**
   - Return `no_update` when the state is unchanged apart from `timestamp`.
   - Hold the last good value on fetch failure; today `_fetch_training_state` returns `{}` (:465) and the badge flips to Inactive.
   - Make the badge, phase and progress consumers clientside.
   - Verify the badge's cadence in the DOM, and check that the lane's `disabled` stays True on the Training Metrics tab after load.
4. **Structural.** Count dispatches by source. Delete the dead interval, gate the 500 ms drain, trim the fast-lane riders, and re-profile idle time against the 0.1% baseline.
5. **Structural.** Push through the WebSocket plan, JR-CAN-PERF-004, using `dash_clientside.set_props` (:3860-3893). It updates a component with no callback lifecycle, so there is nothing to evict. Canopy already uses it in `context_menus.js:116`.
6. **Record separately.** #613's shipped guard defeats the CAN-000 apply clamp whenever an apply starts mid-fetch.

## Single most important correction

Disposition 4 would regress F-CANOPY-027. `runningOff` sets `disabled=False` from `completeJob` after *every* run of `fetch_training_state`, and it runs on every `active_tab` change and at page load. A3's measured orderings show the gate's write losing that race in 3 of 3 page loads and 3 of 3 tab activations. The lane would then poll on hidden tabs forever, and #614's watchdog would force the same result 30 s after leaving the tab. #613's pattern was safe only because its lane is not tab-gated.

---

## Lane A — juniper-cascor#674 re-derived

*agent `a63636f7aa570693f` · last-assistant-text · 7849 chars*

I re-derived every number in the author's report for PR #674 and all of them hold. Two statements need qualifying (item 4), and neither is a defect in the fix: "16 failed on unmodified main" needs a test-side shim, and "each failure is for the intended reason" is true for 12 of the 16 failures, not all.

I worked from two fresh detached worktrees: PR head `7cfad9fc` and `main` at `05c13d55`, which is also the merge-base, so the PR is not behind main. Everything ran under `JuniperCascor1` (Python 3.14.7, pytest 9.0.3).

**Check on the instrument.** The env has an editable `juniper_cascor` install that maps `api`, `src` and the rest to the **primary checkout**. Tests still import from the worktree only because `src/tests/conftest.py:121` puts the worktree's `src` first on the import path. I confirmed inside the running process, for every test and probe run, that `api.websocket.manager` came from my worktree. The head/main difference and the mutations below also show that. A validator whose runner doesn't do that would silently test the primary instead.

## 1. The new test module
- **PR head:** 17 passed. Same result from `src/` (the AGENTS.md form) with the author's `-W error::RuntimeWarning -W error::pytest.PytestUnraisableExceptionWarning`, and no asyncio "never retrieved" or "destroyed but pending" lines.
- **Unmodified main:** not "16 failed". The module doesn't load at all: `ImportError: cannot import name 'BROADCAST_DROP_CLOSE_CODE'`, 1 error, 0 tests run. The PR body discloses this; the brief's paraphrase dropped it.
- **Main with the two constants copied into the test file:** **16 failed, 1 passed.** The one that passes is `test_a_second_disconnect_releases_no_slot_twice`, as claimed.
- **Why they fail on main (line numbers are the head file's):**
  - **12 fail on the defect itself:** both subscribers dropped (`set() == {…}`, lines 183 and 225); the next broadcast reaches nobody (211); no ERROR line (254); no WARNING line (356); no close (`[] == [1011]` at 382 and 402, no close attempted at 424, never closed at 443 and 469); both handler tests time out, i.e. the socket is left half-open (509, 537).
  - **4 fail only because a new name doesn't exist on main:**
    - `test_what_starlette_accepts_is_not_refused`: `KeyError`. Its real check, that `np.float64` is delivered, passes on main.
    - `test_counter_increments_once_per_message_by_type`: `KeyError` before anything runs.
    - `test_emission_failure_is_swallowed`: the function it patches, `ws_inc_unserializable_messages`, doesn't exist.
    - `test_unserializable_broadcast_is_counted_and_the_subscriber_keeps_receiving`: `KeyError` on its first line. So the only end-to-end test never shows the defect on main.
  - In the personal-send test, `delivered is False` already holds on main. Only the missing ERROR line fails it there.

## 2. CI unit selection on the head
I ran it exactly as `ci.yml` does, from the repo root, which is not AGENTS.md's `cd src` form.
- `collected 5138 items / 15 deselected / 5123 selected`, then **`5123 passed, 15 deselected, 10 warnings in 204.98s`**.
- Coverage **96.48%**, and the 80% gate passed. `manager.py` is at **96.60%**; its only uncovered new branch is the cancelled-close case at line 878.
- Main selects 5106, so the PR adds exactly the 17 new tests, and all of them are picked up by the CI marker filter.
- The author's "21 subtests passed" only prints without `--verbose`, which CI uses. The same three test files show it without the flag and omit it with the flag.
- Quick integration tier: **172 passed, 26 deselected** (from the junit file; CI's extra `-q` hides the summary line).

## 3. Live probe
It binds `127.0.0.1:0`, and the OS picks ports from 32768–60999, so 8201/8202 were never at risk. It served on 56753 for the head and 47619 for main.
- **Head:** all 16 checks passed, `ALL CHECKS PASSED`, exit 0. Key lines:
  - `B: dropped client got close 1011 -- closed_in_time=True close_code=1011 reason='Broadcast send failed or timed out'`
  - `unserializable_messages_total=1`, `send_failures=0`, `uvicorn.error=[]`
- **Main:**
  - `[FAIL] A: both clients received the next broadcast -- a=None b=None`
  - `send_failures=2`, `active_connections=0`, `[FAIL] B: found a's server-side socket`
  - `SOME CHECKS FAILED`, exit 1.
- The probe doesn't assert "neither client sees a close" on main, but the log shows it. Both subscribers were dropped silently at 16:08:07.077, and nothing happened for 6.0 s, which is two 3-second receive timeouts. The sockets were only closed when uvicorn shut down.

## 4. What does not reproduce as stated
- "Unmodified main gives 16 failed, 1 passed": it gives a load error unless the two constants are copied into the test file (item 1).
- "Each failure is for the intended reason": true for 12 of the 16. The other 4 fail on the missing new names.
- The PR body says `test_swap_dataset_live.py` contributes "(1)" test to the integration run. It contributes **39**, and its WebSocket-related tests use a mock manager. The counts of 6 and 21 for the other two files match.
- Run time was 204.98 s against the author's 214.78 s, which is expected machine-to-machine timing variation.

## 5. Mutation check (my head worktree only)
I made each change, ran the module, then restored the file and confirmed it matched the commit. At the end the tree was identical to `7cfad9fc` and the module was back to 17 passed.
- **Removed the pre-broadcast serialisation check** (`manager.py:823-824`): 6 failed. `test_numpy_broadcast_drops_and_closes_nobody` went red at line 183 with `assert set() == {…}`.
- **Removed the `close()` step** (`manager.py:836-837`): 7 failed. `test_send_error_drops_and_closes_only_that_subscriber` went red at line 382 with `assert [] == [1011]`, and both handler tests timed out on the half-open socket.
- Extra checks on the author's "each part is load-bearing" claims, one failure each, all as the author described:
  - Unshielding the close fails `test_close_wait_is_bounded…` (the close gets cancelled).
  - Putting back main's `training_stream.py` fails `test_frame_in_flight…` with `RuntimeError: WebSocket is not connected. Need to call "accept" first.`
  - Closing each subscriber before the others are forgotten fails `test_every_failed_subscriber_is_forgotten_before_any_close`.
  - Dropping the UTF-8 encode step fails `test_undecodable_text_is_refused_the_same_way`.

## Record (§7 of the consensus procedure)
- **Instrument:** the tests and probe can tell fixed code from broken code: head vs main differs, and every mutation went red.
- **Sample:** one run of each tier, and one probe run per side, on one host.
- **Lanes:** one Lane A agent, one round, starting from the two commits rather than the author's worktree.
- **Not re-run:** CI's 3.12/3.13/macOS runs, the golden snapshot test, pre-commit, sequence-safety and CodeQL.
- **What this cannot show** (the author says the same): a genuine slow-consumer timeout on a real socket, a close against a truly unresponsive peer, and canopy's side (F-CANOPY-049).

**Cleanup.** Both worktrees are removed and pruned, nothing was pushed, and the live `:8202` service was never touched. The one thing left behind is the ref from the instructed fetch, `refs/remotes/origin/pr-674`, in the cascor repo.

**Referenced:** juniper-ml `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (§2, §7); juniper-cascor `AGENTS.md`, `.github/workflows/ci.yml`, `pyproject.toml`, `src/tests/conftest.py`; the PR #674 body. AGENTS.md's claim that there is a `src/tests/pytest.ini` is stale; the pytest config lives in `pyproject.toml`. **Changed:** no files in any repo. Raw outputs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2a1ec942-45a0-42ee-a732-5e977907ca7a/scratchpad/pr674/`, which is session-scoped and will be deleted.

---

## Author — juniper-cascor#674 (F-CASCOR-004) implementation report

*agent `ab049d7d774723615` · last-assistant-text · 5235 chars*

I've opened PR #674 for F-CASCOR-004; it is not merged. All 24 required checks pass, the merge state is `CLEAN`, and both commits are GitHub-signed and verified.

**PR:** https://github.com/pcalnon/juniper-cascor/pull/674

**Worktree:** `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--f-cascor-004-ws-drop--20260922-1441--05c13d55`. It is clean at the PR head and should stay until the PR merges.

## Files changed
- `src/api/websocket/manager.py`:
  - **Unserializable message:** checked once per broadcast, before seq assignment, chunking and fan-out. It is logged at ERROR, counted and skipped, with no coercion. Nobody is dropped or closed, no seq is used, nothing is buffered.
  - **`send_personal_message`:** returns `False` for such a message.
  - **`_send_json`:** its generic failure branch now logs a WARNING.
  - **Send error or timeout:** every failed subscriber is forgotten first, then each is closed with code `1011`, errors suppressed.
  - **New counter:** `unserializable_messages_total` in `transport_stats()`.
- `src/api/websocket/training_stream.py`: the receive loop stops once the server has closed the socket.
- `src/api/observability.py`: new Prometheus metric `cascor_ws_unserializable_messages_total{type}`.
- `src/tests/unit/api/test_ws_broadcast_fault_isolation.py` (new): 17 tests, all marked `unit`.
- `util/ad-hoc/2026-09-22_f_cascor_004_live_ws_probe.py` (new): runs a real uvicorn server with real WebSocket clients.
- `CHANGELOG.md`, `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`, `docs/REFERENCE.md`

## Tests
- **New module:** `17 passed`. On unmodified `main` it gives `16 failed, 1 passed`, each for the intended reason; the two handler tests time out because the dropped handler never returns. The one that passes pins `disconnect()` idempotency, which already held.
- **Full CI unit selection:** `5123 passed, 15 deselected, 10 warnings, 21 subtests passed in 214.78s`; `Total coverage: 96.48%`.
- **CI's quick integration tier:** `172 passed, 26 deselected, 1 warning in 25.39s`.
- **Golden transport snapshot:** `1 passed`. The new key ends in `_total`, so the snapshot ignores it as volatile.
- **Pinned pre-commit** passes on all 8 files, and both sequence-safety screens report `findings=0`.
- **Live probe:** `ALL CHECKS PASSED`. The dropped client really receives `close_code=1011 reason='Broadcast send failed or timed out'`. Against `main` the probe reproduces the finding: `a=None b=None`, `send_failures=2`, `active_connections=0`, and no close ever arrives.

## What the tests don't prove
- The live probe injects the send failure; I didn't provoke a genuine slow-consumer timeout on a real socket.
- How long a background close takes against an unresponsive peer is governed by the `websockets` library's own timeout; I didn't measure it.

## Assumptions that were false or incomplete
- **`disconnect()` idempotency:** it already held on `main` (the first call pops the connection record), so that test is a pin, not a fix.
- **The receive loop was not safe after the new close.** Once the server has closed a socket, Starlette raises `RuntimeError` from `receive_text()`, not `WebSocketDisconnect`. A frame from the peer still in flight would have crashed the handler with an unhandled exception. The `training_stream.py` change fixes this, and a test fails without it.
- **Bounding the close with a plain timeout doesn't work.** uvicorn's `websockets` implementation swallows a cancelled `close()` once the close frame is written, and its docs discourage cancelling it. So the broadcast waits at most the send timeout, and the close finishes in the background instead of being cancelled. A test fails with the plain-timeout version.
- **`send_failures` no longer counts serialization failures.** The finding named it as the counter to watch; for this fault, `unserializable_messages_total` replaces it.

## Choices and things not done
- **CodeQL fix-up:** the first push drew two CodeQL alerts on the probe script, which would have blocked the merge. A second signed commit fixes both in the code; both threads auto-resolved and 0 alerts are open.
- **CHANGELOG placement:** open PR #672 also inserts at the top of the same `### Fixed` list. I put my entry at the end of that list; a 3-way merge of the two versions shows 0 conflicts.
- **ERROR log not rate-limited:** a per-epoch producer bug would log once per epoch. I left it unthrottled so the defect stays visible; the counter carries the volume.
- **No check when nobody is subscribed:** a broadcast with no subscribers still returns early before the check, so nothing is logged when nobody could be dropped.
- **Not touched:** the juniper-ml metrics catalogue `notes/JUNIPER_2026-05-08_JUNIPER-ECOSYSTEM_METRICS-DOCUMENTATION.md`, which doesn't list the new metric. Also left alone: the ledger's F-CASCOR-004 status, and canopy's separate F-CANOPY-049.
- **PR body attribution order:** the body ends with the 🤖 line as you asked, with the session URL on the line before it.

The ledger cited is juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (entry F-CASCOR-004). The only PR numbers cited, #632 and #672, were checked with `gh`. No juniper-ml documents were changed.

---
