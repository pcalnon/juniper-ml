<!-- markdownlint-disable -->

# Phase 11 ledger validation, round 1 — validator reports (verbatim)

Round 1 of the consensus review of the canopy E2E ledger's Phase 11 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen 1b7cf44b, 2026-10-05. Five lanes, briefed separately with different entry points; briefs in reports/e2e-canopy-2026-09-02/drafts/lane11{A1,A2,A3,B1,B2}_phase11_ledger_brief.md. Each report below is the lane's final message, verbatim. The orchestrator's dispositions are in the ledger's Phase 11 Consensus record; the correction pass is util/ad-hoc/2026-10-05_phase11_ledger_round1_corrections.py.

## Lane 11-A1 (measurement re-creation, source-first)

*agent `a7e7b167940f0d074` · round 1 · last-assistant-text (not resumed) · 10669 chars*

**VERDICT: SOUND.** Every source-level claim in Phase 11 that I re-derived matches the code at the pinned commits. The only finding is a NIT in an instrument's docstring, which changes no number.

**TABLE** (canopy = `/home/pcalnon/Development/python/Juniper/juniper-canopy`; renderer = `/opt/miniforge3/envs/JuniperCanopy1/.../dash/dash-renderer/build/dash_renderer.dev.js`, dash 4.2.0, per `dash-4.2.0.dist-info/METADATA`)

| # | Claim | Re-derived value | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Watchdog `dashboard_manager.py:2497-2555`, its logic, comment `:2519-2522`, constants | The clientside fn is at 2529-2546. Wiring: Input `slow-update-interval.n_intervals`, States `metrics-store-interval.disabled` and `apply-in-flight.data`, Output `allow_duplicate=True` at :2548 (`_METRICS_STORE_INTERVAL` = "metrics-store-interval", :460). Logic: `!disabled \|\| Boolean(applyInFlight)` clears the clock; the first disabled sample sets it; `now-since < 30000` returns NU, otherwise it clears and returns `false`. The comment at 2519-2522 is the quoted text. Constants: `canopy_constants.py` :371 = 5000, :410 = 1000, :421-424 rationale, :425 = 30000, :572 = 60000. | MATCH | `git -C canopy show 60ae1870:src/frontend/dashboard_manager.py \| sed -n 2497,2555p`; same for `src/canopy_constants.py` |
| 2 | Feeder `running=` (:4752); handler :7879-7990 replaces and never appends; :7984-7985; ws gate; modulus | :4752 is exactly `running=[(Output(_METRICS_STORE_INTERVAL,"disabled"),True,False)]`. The handler returns the fetched `metrics` (or `[]`/`no_update`) and never concatenates. :7984-7985 returns `no_update` when the fetch equals the store. :7920-7921 skips while `ws_live and not full_fetch`. :7926 refetches only when `n % FULL_HISTORY_POLL_TICK_MODULUS == 0` (modulus = 5, `canopy_constants.py:491`); a mode switch fetches at once. | MATCH | sed of 4746-4769 and 7879-7990 at 60ae1870 |
| 3a | Contradicted text :467-472, :4734-4737, `test_poll_gating.py:313` | All three are verbatim. The :313 quote spans 312-313. At 60ae1870 the lane has two registered writers: the gate at :2489 and the watchdog at :2548. The test at :202 itself expects 2. | MATCH | sed 440-500 and 4723-4745; `show 60ae1870:src/tests/unit/frontend/test_poll_gating.py` |
| 3b | `:194-197` "continuously True … pin"; `TestStrandWatchdog` :213-297 runs no predicate | The text is verbatim; the class spans 213-297. Its 7 tests check registration and wiring, string presence (`"return false;"`, `"Boolean(applyInFlight)"`, the threshold digits) and constant arithmetic. None executes JS. | MATCH | sed 180-330 |
| 3c | Universal: does any test at 60ae1870 execute the watchdog's JS? | No test executes it as its subject. **Search 1:** `git grep -n -E 'shutil\.which\("node(js)?"\)' 60ae1870` finds 6 files: two F-042, F-054, idle cuts, Y4, `test_phase_b_bridge.py`. Grepping those for the lane, slow lane, apply-in-flight, DisabledSince, watchdog or STRAND returns nothing. **Search 2:** no in-process JS engine (MiniRacer, quickjs, js2py, dukpy, execjs) in any test. **Search 3:** the terms `__metricsStoreDisabledSince` and `METRICS_STORE_STRAND_TIMEOUT_MS` appear only in `test_poll_gating.py` (string checks). **Caveat:** the opt-in Playwright suite `src/tests/ui` (excluded by default, `pyproject.toml:454 --ignore=src/tests/ui`) boots the whole page, so a UI test lasting more than 5 s runs the watchdog incidentally. No UI test references or asserts on it. The ledger's narrower wording ("none runs the predicate"; "No node-gated test…") holds. | MATCH | commands as listed |
| 4 | E-3 watchdog :4242-4257 | Input `apply-watchdog-interval`, State `apply-in-flight`. It returns `false` when `Date.now()-inFlight.since > 60000`. | MATCH | sed 4205-4257 |
| 5a | `completeJob()` releases on OK, PREVENT_UPDATE and error with no currency check; cited at :925-937 and :966-986 | `completeJob` is at 925-937 and dispatches `sideUpdate(runningOff,…)` unconditionally. It is called at 966 and 970 (OK), 979 (PREVENT_UPDATE) and 983 (non-OK). `handleError` (987-998) does not call it. | MATCH | Read renderer 807-1004 |
| 5b | A watched request is pruned by a same-identity request; its response is discarded | :3027 sets `wDuplicates` to `concat(watched, requested)` grouped by `getUniqueIdentifier` (inputs, outputs and state, not the trigger, :1715-1728) and sliced `[0:-1]`, so the newcomer wins. :3151 dispatches `removeWatchedCallbacks`. :2699-2704 returns without `AddExecuted` when the request is no longer in watched. | MATCH | Read 2953-3160, 2666-2721 |
| 5c | How the `running` update reaches a `window.store.dispatch` wrapper | **The chain:** `sideUpdate` returns a thunk (:746-747). It is dispatched with `handleServerside`'s `dispatch` (:819, :932). That comes from `executeCallback` (:1330), which gets it from the prioritized observer's `_ref2.dispatch` (:2837). `StoreObserver.notify` calls `o.observer(store)` (:382) on the same object assigned to `window.store` (:3762-3763, :3798), and canopy uses HTTP, not websocket (no websocket config in `dash.Dash(...)` at :621). So the shim's wrapper sees the outer thunk, which `flatten` logs with empty types. **What it does not see:** inner dispatches go through redux-thunk's `middlewareAPI.dispatch` to the closure `_dispatch` (:46772-46783), so the wrapper never sees `onPropChange` (its only dispatch site is :7091, inside the `updateProps` thunk). **Order:** the shim records after `orig.apply` returns (shim :79-98) and observers re-read `store.dispatch` synchronously, so nested records come first and the outer comes last, with outer t ≤ inner t. The release itself is a top-level thunk, dispatched from the fetch promise. **Transcript cross-check** (done after the source reading): zero `ON_PROP_CHANGE` labels in both runs. True-to-False records with empty types: 308 and 304; outer `RemoveWatched+AddExecuted` records: 17 and 17. Each of the 17 outers is immediately preceded by an empty-typed thunk with t ≥ the outer's t, 0-1 ms apart. False-to-True thunks = requests + 1 (307+1 and 304+1). The frozen release trace reproduces 291/287 releases, own 273+276 = 549 (13-89 ms), late 18+11 = 29, unassigned 0, flight 2,355-5,448 ms, successors 8 answered and 21 evicted, gaps 433-2,031 ms. Its self-test passes on both runs. Fires: 28/28 in flight, enabled 10,424-14,705 ms, episode 312-3,797 ms; the third field is always null. | MATCH (release-trace reading is correct) | renderer reads; `python3 -B` scripts in the mktemp dir over `git show 1b7cf44b:` copies |
| 6 | dcc `Interval`: a write of `false` restarts the timer whatever the writer | `handleTimer` clears the timer while `disabled` is true and starts a fresh `setInterval` when it is false and no timer exists. It is called from `componentDidMount` and `UNSAFE_componentWillReceiveProps` and reads only props. The minified bundle matches: `setInterval(this.reportInterval,e.interval)`. dcc 4.2.0. | MATCH | sourcesContent of `dash/dcc/dash_core_components.js.map` (`Interval.react.js`) plus a bundle excerpt |
| 7 | #705/#722 touch no cited code; #722's hunk is a tooltip bound; 60ae1870 = #702, parent 1b2dd438 | The compare shows ahead_by 2: `fe6a9348` (#705, `.github/workflows/claude.yml`) and `c7876f5a` (#722). Neither `canopy_constants.py` nor `test_poll_gating.py` changed. `dashboard_manager.py` +5/-4 at `@@ -7341` sets `_FAILURE_REASON_TOOLTIP_MAX_CHARS` 400 → 480. A raw fetch at c7876f5a diffed against 60ae1870 differs only at 7344-7348, so lines after 7341 shift +1; the ledger cites them "at 60ae1870", which is correct. Local log: `60ae1870 1b2dd438 … (#702)`. Also MATCH: `requirements.lock:32 dash==4.4.1`, and Phase 10 pins 1b2dd438 (ledger line 9806). | MATCH | `gh api …/compare/60ae1870...c7876f5a --jq` (sha, subject, files only); `gh api -H 'Accept: application/vnd.github.raw' '…/contents/src/frontend/dashboard_manager.py?ref=c7876f5a'` |

**FINDINGS**

1. **NIT.** The census v2 shim's docstring makes false statements about how writes reach its wrapper. This is in the instrument at the frozen commit, not in the ledger: `util/ad-hoc/2026-10-04_f058_census_v2_shim.py` at 1b7cf44b.
   - **Quoted text:**
     - :36-37: "the action types that carried it: the ``running=`` guard (``ON_PROP_CHANGE``), the gate and the watchdog."
     - :21: "every lifecycle action after page load goes through the wrapper"
     - :32: "a ``no_update`` answer (HTTP 200, empty data)"
   - **Evidence:**
     - In dash 4.2.0, `sideUpdate` (:746-747) and `updateProps` (:7087-7092) are both thunks. `onPropChange` is dispatched only at :7091, through `middlewareAPI.dispatch` (:46772-46776), which the wrapper never sees. Both transcripts carry zero `ON_PROP_CHANGE` labels; the `running=` writes are logged with empty types.
     - `notifyObservers`'s `addRequestedCallbacks` (:7224) also bypasses the wrapper.
     - An all-`no_update` answer is a 204 (`dash/_callback.py:604-605`, `dash/dash.py:760-761`). The PREVENT_UPDATE branch (:978-981) still yields an answered request with props=0, so classification is unaffected.
     - The ledger never relies on these labels, and the release trace's docstring (:21-27) states the correct reading.
   - **Fix:** keep the shim byte-for-byte. Add one correction line to the evidence README's corrections list or to Phase 11's Instruments.
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- dash 4.4.1 line numbers (`completeJob` at :979-991, called at :1020/:1024/:1033/:1037): 4.4.1 is not installed locally and I did not fetch it.
- That the legs actually ran the env's dash 4.2.0 at run time. I checked only the current install.
- Things outside this source-first lane:
  - the alias-replay figures (5-16/3-18; randomized median 2)
  - the leg logs, host load, origin refusals and page times
  - the synth check's 6 of 6
  - the Phase 9/10 cross-references (plan §6.3; BLOCKER 2's 37-44 an hour)
- Note on the brief itself: `c7876f5a` is now in the local canopy object store (it resolves to c7876f5a8d4f…, #722). I still used the `gh api` routes as instructed.

**SECRETS/PII:** None printed or sent. No environment values, tokens, credential files or email addresses were printed. Git output was limited to hashes and subjects, with no `git show` headers or author lines. Disclosure: the brief-prescribed `gh api …/compare` response contains commit objects with author fields on the server side. I filtered it with `--jq` to sha, subject and file fields, so no author or email field was printed. From the transcripts I printed only counts and timings. All scratch work was in a `mktemp -d` directory, with no repo writes and no services or ports touched.

---

## Lane 11-A2 (measurement re-creation, raw-transcript-first)

*agent `aecd8bf8e5ca7cbf7` · round 1 · last-assistant-text (not resumed) · 12456 chars*

**VERDICT: SOUND-WITH-FIXES**

**TABLE**

How each row was derived: the transcripts were extracted with `git -C <worktree> show 1b7cf44b:<path>` into `/tmp/tmp.AFzDbAMY9I` (made with `mktemp -d`). Every script ran as `python3 -B <script> ev/2026-10-05_census_live.json ev/run2/2026-10-05_census_live.json`.

- **R** = `myreader.py`, written from the shim's JavaScript before any repo reader ran. The shim stamps each record with the dispatch's *entry* time but pushes it after `orig.apply` returns. So a nested dispatch is logged first, and each enclosing dispatch logs the same change again at its own, earlier entry time. A thunk logs action types `''`. R therefore takes the innermost record of each chain as the physical change. Its duplicate check found 0 problems and its alternation check 0 breaks, in both runs.
- **M** = `mech.py`, **T** = `triggers.py`, **W** = `windows.py`, **V** = `variants.py`, **E** = `enabled_check.py` (millisecond brute force).
- Values are run 1 ; run 2.

| # | Number | Mine | Ledger | Result | How derived |
|---|---|---|---|---|---|
| 1 | Requests total / answered / evicted / open | 307/289/18/0 ; 304/292/11/1 = 611/581/29/1 | same | MATCH | R. Each id has one W and at most one end (0 anomalies) |
| 2 | In-flight median, max | 2,817, 4,203 ; 2,814, 5,345 | same | MATCH | R |
| 3 | In-flight p90 | 3,633 ; 3,680 using `xs[int(0.9(n−1)+0.5)]`. Nearest-rank gives 3,640 ; 3,680 | 3,633 ; 3,680 | MATCH (depends on rule) | R, V |
| 4 | Only request under 1 s in flight | id 130, 888 ms (run 2). Run 1 minimum is 1,239 | "but one (888 ms)" | MATCH | R |
| 5 | Eviction runs | [1,2,11,4] ; [1,2,4,4] | same | MATCH | R. Entry order equals id order |
| 6 | Gap between applied answers across each run | Run 1: none for the first run (request 1 had no earlier answer), then 9,672, 34,826, 15,213. Run 2: 9,118, 9,357, 15,417, 14,936 | longest 34.8 s | MATCH | R |
| 7 | Gap between applied answers: median, p90 | 4,885.5 (upper median 4,887), p90 5,815–5,858 ; 4,875, p90 5,859 | 4,887 ; 4,875 | MATCH | R |
| 8 | Median disabled episode | 2,707.5 ; 2,741.5 ms. Using the enclosing record's time instead: 2,745.5 ; 2,803 | 2,746 ; 2,803, "about 2.8 s" | MISMATCH, see F1 | R, V |
| 9 | Lane state between episodes | Enabled. Median 2,140 ; 2,085 ms. Every stretch that ended in a tick is ≥ 1.2 s; the only shorter ones (363 ; 601 ms) end at the clamp | "enabled for the rest…" | MATCH | R |
| 10 | Fires; lane before each; feeder in flight | 13 ; 15. Lane `true` before all 28; a feeder request in flight at all 28 | same | MATCH | R |
| 11 | Age of the current disabled episode at each fire | 0.29–2.01 ; 0.40–3.58 s, so 0.3–3.6 s. Enclosing-record time gives 0.31–3.80 | 0.3–3.8 s | MISMATCH, see F1 | R, V |
| 12 | Ms enabled in the 30 s before each fire | 12,260–13,992 ; 11,018–14,891, so 11.0–14.9 s. Enclosing-record time gives 10,424–14,705. All are above 0, so every fire was false | 10.4–14.7 s | MISMATCH, see F1 | R, E |
| 13 | Fire rate | 30.9 ; 35.7 per hour, time base page time 0 to the last request record (1,514.0 ; 1,510.7 s). Combined 33.3/h. Idle window only: 24 ; 48/h | 30.9 ; 35.7 | MATCH | R |
| 14 | Releases (`running=` off) | 291 ; 287. Phantoms exist: every fire and every true-to-false gate write logs a nested `''` true-to-false record that looks exactly like a release (17 ; 17). They sit under their `RemoveWatched+AddExecuted` encloser at +0–1 ms and are excluded | 291 ; 287 | MATCH | R |
| 15 | Own releases, gap to their answer | 273 at 38–54 ms ; 276 at 13–89 ms = 549 | 549, 13–89 ms | MATCH | M |
| 16 | Late releases | 18 ; 11 = 29. Exactly one per evicted request, each inside its immediate successor's flight. None falls within 100 ms before any eviction; none falls with nothing in flight; 0 unassigned. All 16 ; 16 answered requests without a visible own release are explained by a fire (10 ; 11), a late release (4 ; 4) or a gate write (2 ; 1) | 29, one each | MATCH | M. The assignment is the same as the trace's oldest-first assignment |
| 17 | Late release after the evicted request entered `watched` | 2,355–4,375 ; 2,603–5,448 ms | 2.4–5.4 s | MATCH | M |
| 18 | Late release to the successor's answer, when answered | 433, 731, 1,630, 2,031 ; 704, 1,025, 1,112, 1,688 ms | 0.4–2.0 s | MATCH | M. For evicted successors the gap to their eviction is 1,422–2,553 ms, so the release cannot be the successor's own |
| 19 | Successors evicted / answered | 14/4 ; 7/4 = 21/8 | 21/8 | MATCH | M |
| 20 | Evicting fires: fire to eviction, fire to response landing | 3 + 4 = 7. 1,418–2,392 ms ; 1,756–4,955 ms | 1.4–2.4 ; 1.8–5.0 s | MATCH | M |
| 21 | Other fires: fire to answer | 21 fires, 104–2,164 ms | 0.1–2.2 s | MATCH | M |
| 22 | What started the runs | 7 fire-started runs hold 28 evictions. The run of 1 followed the gate's write at 7,253 ms, 186 ms into request 1 | same | MATCH | M, T |
| 23 | Window table: resolved / evicted (10 rows) | Run 1: 52/2, 36/0, 36/0, 38/4, 127/11. Run 2: 44/1, 37/6, 38/0, 41/4, 131/0 | same | MATCH | W |
| 24 | "What happened" timings | **T-gate**: answered +504 ; +83 ms; gate write +1,336 ; +1,367 on an enabled lane. **T-tab**: answered +792 ; +788; second click's write +3,396 ; +4,203, landing 599 ; 1,081 ms into the next request, answered 1,103 ; 1,763 ms later. **T-mode**: answered +629 ; +1,086; next request entered +2,148 ; +2,503. Fire times 81.7, 223.0, 402.7, 437.7, 893.0, 1,358.3, 1,452.6 s; idle fires 4 ; 8 | same | MATCH, except "the mode change's request", which is UNTRACEABLE | T |
| 25 | Trigger latency; how far into the targeted request each trigger fired | 1,304–4,203 ms; 1,633–2,914 ms | 1.3–4.2 s; 1.6–2.9 s | MATCH (see F2) | T |
| 26 | Clamp write vs in-flight answer; clamp length | The clamp's write landed 316 ; 561 ms after requests 139 ; 129 were answered, with nothing in flight. Clamp held 62,252 ; 63,064 ms; no request entered under it | same | MATCH | T |
| 27 | Later gate writes | Run 1: 728,126 (true to false), 2,071 ms after the 726,055 release, 692 ms into request 140 and 1,114 ms before its answer. Run 2: 722,033 (false to false), 687 ms before request 130 entered | 2.1, 0.7, 1.1 s | MATCH | T |
| 28 | Page time zero bound and the E-3 inference (run 1) | Console log alone puts t0 in [05:56:14.000, 05:56:14.764), from the leg line and from the T-tab end line minus (second click 480,236 + 180 s). `raw.t0` = 05:56:14.547 falls inside. So the 726,055 write is no later than 06:08:20.819. The census's release comes after its MISSED line (≥ 06:08:22.000, per `live.py`'s order), so it is ≥ 1.18 s later (1.40 s using `raw.t0`) | ≥ 1.1 s | MATCH | T |
| 29 | Run 2: can the log separate the two releases? | t0 in [16:11:16.000, 16:11:19.414); `raw.t0` = 16:11:19.114. 721,354 lands at 16:23:20.468 and 722,033 at 16:23:21.147. Both are compatible with a release made after 16:23:20.000 | "cannot tell apart" | MATCH (true even using `raw.t0`) | T |
| 30 | T-tab click spacing | 1,943 ; 1,605 ms | 1.9 ; 1.6 s | MATCH | T |
| 31 | Fire record's third field | null in 28 of 28 | always null | MATCH | R |
| 32 | "First version … misread two late releases" | A 1 s window misreads 433 and 731 ms in run 1, and would also misread 704 ms in run 2 | two | MATCH as run-1 history | M |
| 33 | Step 8: the repo's readers | `analyze.py` gives the same counts, medians and maxima, p90 3,633 ; 3,680, episodes 2,746 ; 2,803. `release_trace.py` gives the same 291/287, 273/276 and 18/11, identical assignments and gap lists; its fire age and enabled values are the enclosing-record ones (10,424…). `--self-test` passes on both runs (exit 0). `alias_replay` at 5,000 ms: aligned 5–16 (median 9) ; 3–18 (median 8); jittered median 2 ; 2; zero fires in 87/500 ; 82/500 replays; at 6,000 and 7,500 ms medians 2–4 | as ledger | MATCH | Run from the frozen commit |
| 34 | Leg logs, host load, synthetic check | Page connected 05:56:14.846–06:21:29.193 and 16:11:19.451–16:36:31.208, one start each. Control-stream disconnect warnings 62 ; 55. 16 cores; load averages match. Synthetic check: 6 cases, ALL PASS | same | MATCH | grep counts only |

**FINDINGS**

1. **MINOR. The readers backdate every nested disable of the lane.**
   - **Quoted ledger text:**
     - "the lane had been enabled for 10.4–14.7 s of the 30 s before" (Summary, What the events show, and F-CANOPY-068 Measured)
     - "the lane's current disabled episode was 0.3–3.8 s old" (twice)
     - "disabled for about 2.8 s of it (median disabled episodes 2,746 and 2,803 ms)"
     - "about 2.8 s of each cycle"
   - **Evidence:**
     - All three readers time a nested change at its *enclosing* dispatch's entry time: `analyze.py`'s time-sorted episode builder, and `lane_timeline()` in both `release_trace.py` and `alias_replay.py`.
     - The shim's own reading contradicts this. In run 2, lane records 566/567 are `[949155,false,true,""]` and its encloser `[948936,false,true,"Callbacks.RemoveRequested+Callbacks.RemoveWatched+Callbacks.AddPrioritized"]`. The thunk read the lane `false` at 949,155, yet the readers mark it disabled from 948,936.
     - That one record makes fire 952,733's episode 3,797 ms (the ledger's 3.8 s maximum) instead of 3,578 ms.
     - Across all nested disables, the encloser is earlier by a median of 21 ; 23 ms and at most 217 ; 327 ms, and by more than 100 ms in 7 ; 48 cases.
     - Releases nested in fire or gate writes are off by at most 1 ms, so the release, race and mechanism figures are unaffected.
     - Re-running the alias replay on the corrected timeline gives aligned medians 9 and 7, jittered medians 1 and 1, zero-fire share about one in five, and 1–3.5 at 6,000/7,500 ms. The conclusion does not change.
   - **Fix:** in all three readers, build the timeline from the innermost record of each chain (types `''` plus `SET_LAYOUT`). Then restate the figures as 11.0–14.9 s enabled, 0.3–3.6 s old, medians 2,708 and 2,742 ms ("about 2.7 s"), and the corrected replay numbers.
   - **Changes a number:** yes. **Disposition:** no. **Action:** no. The error understates enabled time, so "every fire false" only gets stronger.

2. **NIT. T-tab's latency is not all the renderer's queue.**
   - **Quoted:** "Its scripted triggers reached the page 1.3–4.2 s after they fired, through the renderer's queue".
   - **Evidence:**
     - For T-tab the clicks themselves came late: +993/+2,936 ms in run 1 and +708/+2,313 ms in run 2 after firing.
     - That includes the census's own 1 s wait between clicks, which took 1.9 and 1.6 s.
     - The gate writes followed the clicks by only 311/460 ms and 873/1,890 ms.
     - So the 3.4 s and 4.2 s maxima are mostly delay on the census's side.
   - **Fix:** split T-tab's latency into the census's click delay and the click-to-write time, and have item 25's redesign time the clicks in the page.
   - **Changes a number:** no. **Disposition:** no. **Action:** marginally (item 25's scope).

**WHAT YOU COULD NOT CHECK**

- **T-mode cause:** "the mode change's request" is UNTRACEABLE. The transcript records W, A and X for each request, not what triggered it. Requests 269 and 263 entered 1,557 and 1,472 ms after the previous release, inside the normal range for a tick.
- **Canopy and dash source claims:** the Interval's 1 s period and fresh timer on re-enable (consistent with the data: no tick-ended enabled stretch under 1.2 s), the watchdog's predicate and 5 s sampling, E-3's 60 s limit, and the cited file:line references.
- **Gate callback location:** whether it runs clientside or on the server.
- **Watchdog samples:** its non-firing samples were not logged, so the aliasing explanation stays inferred.
- **Clock assumption:** that the browser clock equals the host clock. Every console-log bound and the leg log's page-connect time agree with it.
- **Not examined:** the README's four corrections and Phase 9's synthetic-app claims.
- **My readers:** they live only in `/tmp/tmp.AFzDbAMY9I`, as the brief's `mktemp -d` rule requires, so they will disappear. Copy them to `util/ad-hoc/` if they should be kept.

**SECRETS/PII:** No environment variables, tokens or credential files were printed or sent. Leg-log lines matching secret or email patterns were counted, never printed. One slip: an early `git show 1b7cf44b --stat` printed the commit's Author header, which contains an email address, into local tool output only. It was not sent anywhere or written to any file, and is not repeated here. Nothing was written to any repo.

---

## Lane 11-A3 (measurement re-creation, instrument-adequacy-first)

*agent `ae2299fb7207e6aa7` · round 1 · last-assistant-text (not resumed) · 14615 chars*

**VERDICT: SOUND-WITH-FIXES.** I reviewed Phase 11 of the ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and the evidence README `reports/e2e-canopy-2026-09-02/f058-census-v2/README.md`, both at `1b7cf44b`. Every count Phase 11 states reproduces. Every disposition stands. Several timing figures are off by a little, because of how the shim timestamps its records, and the ledger's item 25 needs a different trigger method.

`$S` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh` (made with `mktemp -d`). My checking scripts are in `$S/tools/`.

**TABLE**

| Instrument / check | What I ran | Result | Rating |
|---|---|---|---|
| Provenance: the six `util/ad-hoc/2026-10-04_f058_census_v2_*.py` scripts and the first run's six files | sha256 of each file at `1b7cf44b` against `backups/2026-10-05_f058_census_v2_final/` and its `run/` | 12 of 12 identical | ADEQUATE |
| Provenance: `run2/` | sha256 against `scratchpad/rerun/` (`…_rerun.json`, `…_rerun.log`, `canopy-8052_rerun.log`, `host_load.txt`) | 4 of 4 identical | ADEQUATE |
| Does run 2's transcript say it ran the same shim? | Read its `probe` and `args` fields; read the header and SHIM constant of the compiled shim (`.pyc`) | **Not from the transcript.** `probe` is only the live script's file name. `args` holds the four window lengths, `adhoc_dir` (this worktree's `util/ad-hoc`) and `out`, with no shim path or hash. **Outside it, yes:** the worktree's `__pycache__/2026-10-04_f058_census_v2_shim.cpython-313.pyc` was written at 16:11:16.81 CDT, the run's first log second. It records the source as 8,623 bytes with mtime 05:47:45, and its SHIM constant is byte-identical to the frozen one (sha256 `e3d17ba0…`). The backup's `.pyc` (05:49:43) matches too. | UNTRACEABLE in the transcript; corroborated |
| Synthetic check (`…synth_check.py` on `…synth_app.py`) | Ran it from my scratch copy in JuniperCanopy1 (dash 4.2.0). A port monitor confirmed all six apps on :9491 were its own children. | **6 of 6 PASS**, close to the archived output:<br>• data-control: 13 answered, all with props; 0 evicted; store took 13 values<br>• noupdate-control: 13 answered, 1 with props; 0 evicted; store took 1 value<br>• data-mode: 22 of 22 evicted after the trigger; store 2<br>• noupdate-mode: 22 of 22 evicted<br>• mount-cascade: gate write true→false at 436 ms; 26 of 26 evicted<br>• watchdog: 5 fires at 15,314 to 75,313 ms, 15,000 ± 1 ms apart, lane disabled before each; 12 evicted after the first<br>**Can it fail?** I fed the check's own pass rules (read from the file, not retyped) the outputs four broken shims would give. v1's "no_update read as evicted" fails noupdate-control. A shim blind to evictions fails all four trigger cases. Reading the lane after the fire's write fails the watchdog case. **A shim that catches only the first fire passes.** | ADEQUATE (NIT 4) |
| Release trace: default and `--self-test` | Both, on both transcripts | **Run 1:** 291 releases = 273 own (38–54 ms before their answer) + 18 late, 0 unassigned. **Run 2:** 287 = 276 own (13–89 ms) + 11 late, 0 unassigned. Late responses landed 2,355–5,448 ms after entering `watched`, and 433–2,031 ms before the successor's answer. 28 of 28 fires had the lane enabled within the 30 s before. Self-tests pass on both. | ADEQUATE on these transcripts (MINOR 3) |
| Release trace: `--own-ms` and `--write-ms` | `--own-ms` 0–2,100; `--write-ms` 0, 1, 2, 5, 50 | **`--own-ms`:**<br>• No classification moves from 89 to 432 ms (run 2: 89 to 703).<br>• At 60 and 88 ms, run 2's own releases at 63, 71 and 89 ms show as *unassigned*, so the failure is visible.<br>• From 433 ms (run 1) and 704 ms (run 2), a late release is read as the successor's own. Every later pairing then shifts, with flights up to 811–915 s, and "none" lands on the transcript's last eviction.<br>**`--write-ms`:** at 0, three fire records (run 1) and one (run 2), 1 ms off their write, show as unassigned. 1–50 changes nothing. | ADEQUATE |
| Is the 100 ms own rule safe? | The sweeps above | Own releases are at most 89 ms before their answer; late releases are at least 433 ms before. Margins are 11 ms and 333 ms. On the own side an overflow surfaces as unassigned. | ADEQUATE |
| Release trace: mutations past the self-test | Shifted every late release into the 50 ms before the successor's answer; dropped one late release | Shift: late 18→14 and 11→7. The trace reports "none" for evictions 293–296 and 268–271, not for the four whose releases moved, and pairs the rest with flights of 7.9–920 s. Drop req 1's late release: still 17 late and 0 unassigned; all 17 remaining pairings shift by one; "none" lands on req 296. | — |
| Is "exactly one late release per eviction" an artifact of the oldest-first rule? | Independent checks of the timeline | **No, on these transcripts:**<br>• Each of the 29 eviction intervals (from X_k to the end of request k+1) holds exactly one non-own release, in all 8 runs, and no non-own release falls outside them. So the pairing is forced by the timeline.<br>• After a late release, the next request entered `watched` a median 2.2 s later, about the same as after an own release (2.1 s).<br>• Every answered request without a logged own release (16 + 16) had a late release, a fire or a gate write re-enable the lane under it first.<br>• Every request entry has its disabling record 1–7 ms before it. | — |
| Watchdog alias replay | Both runs, plus the four tests in the cells below | Reproduces the ledger's figures and the README's figures. | ADEQUATE (figures shift, MINOR 1) |
| Replay: progress-based predicate | Reset on any answer, or any request or answer, since the last sample | 0 fires at every phase, in phase and randomized | — |
| Replay: fixed-cycle synthetic lanes | 4.9 s cycle with 2.8 s disabled; 7.5 s with 2.8 s; 7.5 s with 5.4 s; compared with an independent brute force and closed form | Equal to the brute force at every phase:<br>• 4.9 s / 2.8 s: 24–25 fires (closed form: 4 per 245 s beat, ≈ 24.7)<br>• 7.5 s / 2.8 s: 0 everywhere<br>• 7.5 s / 5.4 s: 0 or 43, zero at 420 of 500 phases. Here the randomized control has median 7 against 0 in phase, so "in phase is much higher than randomized" is not built into the tool. | — |
| Replay: is the randomized ("jittered") control a fair chance baseline? | Compared it with two other chance models on the measured lanes | Same sampling rate (302–303 samples per replay) and independent phase. The other models give medians 2 and 3 and maxima 7–8, so the control reads about one fire low. No chance model reached 13 or 15 in 500 replays. **Supports exactly what the ledger claims, including its lock caveat.** | — |
| Replay: sampling period and sampler jitter | Same replay at 4,900 ms and with ±100 / ±250 / ±500 ms jitter | At 4,900 ms no phase reaches the observed 13 or 15 (maximum 11). At 5,000 ms, 23% and 11% of phases do. With ±100–500 ms jitter the medians are 5–9 and never 0. | — |
| Analyze | Both transcripts | Run 1: 307 requests = 289 answered + 18 evicted, runs of 1, 2, 11, 4, 13 fires. Run 2: 304 = 292 + 11 + 1 open, runs of 1, 2, 4, 4, 15 fires. All match the ledger. | ADEQUATE |
| README "Replaying the reading" | The block, extracted and run verbatim from a clean full `git archive 1b7cf44b` | 8 of 8 commands exit 0, each printing what its comment says | ADEQUATE |
| The lane timeline that analyze, the trace and the replay all read | Compared each record's timestamp with the inner record that actually changed the lane, then re-ran all three on change-time records | Many records are stamped at the start of their dispatch, up to 327 ms before the change (MINOR 1) | INADEQUATE below about 0.3 s |
| Phase 11's list of what the census could not do | Compared trigger times, click times and gate-write times | Leaves out the driver's own latency (MINOR 2) | — |

**FINDINGS**

1. **MINOR. The lane records are stamped at dispatch start, so lane changes read up to 0.33 s early.**
   - **Ledger text** (`…E2E-VALIDATION-EVIDENCE.md`): "the lane had been enabled for 10.4–14.7 s of the 30 s before it"; "the lane's current disabled episode was 0.3–3.8 s old"; "median disabled episodes 2,746 and 2,803 ms"; "(medians 9 and 8) … a median of 2 in both runs, and no fire at all in about one replay in six … medians 2 to 4".
   - **README text** (`…/f058-census-v2/README.md`, correction 3): "median 9 … a median of 2 … median 8".
   - **Evidence:**
     - The shim takes its timestamp before `orig.apply` and pushes the record after it. An outer `Callbacks.*` dispatch therefore carries its start time but reports a change its nested runningOn record made later.
     - This happens to 267 of 367 outer records in run 1 and 293 of 333 in run 2 (more than 5 ms early); the largest gaps are 217 and 327 ms.
     - Example: outer record stamped 727,224; runningOn at 727,431; request 140 enters `watched` at 727,434.
   - **Rebuilt from change-time records**, the figures become:

     | Figure | Ledger | From change times |
     |---|---|---|
     | Lane enabled in the 30 s before a fire | 10.4–14.7 s | 11.0–14.9 s |
     | Age of the current disabled episode at a fire | 0.3–3.8 s | 0.3–3.6 s |
     | Median disabled episode, runs 1 and 2 | 2,746 and 2,803 ms | 2,708 and 2,742 ms |
     | In-phase replay at 5,000 ms, range | 5–16 and 3–18 | unchanged |
     | In-phase replay at 5,000 ms, medians | 9 and 8 | 9 and 7 |
     | Randomized replay, median | 2 in both | 1 in both |
     | Randomized replay, share with no fire | about 1 in 6 | about 1 in 5 (94 and 102 of 500) |
     | 6,000 and 7,500 ms, medians | 2 to 4 | 1 to 3.5 |

     The trace's classifications do not change.
   - **Fix:** build the timeline from change-time records, or stamp records at completion, then restate these figures. Or list the skew under Instruments.
   - Changes a number: yes. Disposition: no; the false-fire conclusion gets stronger.

2. **MINOR. The trigger lag folds in the driver's own latency.**
   - **Ledger text** (`…E2E-VALIDATION-EVIDENCE.md`): "Its scripted triggers reached the page 1.3–4.2 s after they fired, through the renderer's queue"; item 25: "Fire each as a request enters `watched`".
   - **Evidence:**
     - The 3.4 s and 4.2 s figures are T-tab's *second* click, measured from the trigger.
     - 993 and 708 ms passed between the trigger's page timestamp and the first click completing in the page.
     - The clicks were 1,943 and 1,605 ms apart in page time for a scripted 1.0 s wait.
     - Each gate write landed 311/460 ms (run 1) and 873/1,890 ms (run 2) after its own click.
     - The poll fired 1.6–2.9 s into flights for a 1.5 s threshold.
     - Fired at request entry, this driver's write would land about 1.0–2.9 s into the flight. To evict, a re-enable has to precede the response by more than the 1.4–2.4 s the data show.
   - **Fix:** state the lag per action; timestamp each action in the page; make item 25 fire its triggers in-page (for example from the shim's `AddWatched` hook).
   - Changes a number: no, only how it is attributed. Action: yes (item 25's method).

3. **MINOR. The release trace's pairing does not check itself.**
   - **Ledger text** (`…E2E-VALIDATION-EVIDENCE.md`): "This is F-CANOPY-058's mechanism read directly … The trace's self-test removes the late releases … and then reads every eviction as "late release: none"."
   - **Evidence:**
     - A self-test that only deletes records cannot exercise the oldest-first assignment.
     - My shift and drop mutations silently re-paired every later eviction, and put "none" on the wrong requests, while the summary line kept its usual form.
     - On these two transcripts the pairing is forced by the timeline (see the TABLE).
   - **Fix:** require each late release to fall inside its own chain interval, or add that interval check and a shift mutation to `--self-test`, before item 24 reuses the trace.
   - Changes anything: no.

4. **NIT. The synthetic check's watchdog case does not test "each fire".**
   - **Ledger text** (`…E2E-VALIDATION-EVIDENCE.md`): "a forced strand caught at each fire".
   - **Evidence:**
     - The pass rule only needs at least one fire, so a first-fire-only shim passes.
     - The actual output, 5 fires exactly 15,000 ± 1 ms apart, equals the closed form for `STRAND_MS` 8,000 over 78 s. So "each" holds in the output, not in the rule.
     - No case has a mid-request re-enable that must *not* evict. The live runs supply 24 of them, all read as answered.
   - **Fix:** assert 5 fires, and add a case with a late-landing re-enable.
   - Changes anything: no.

5. **NIT. The longest request was 5.4 s, not 5.3 s.**
   - **Ledger text** (`…E2E-VALIDATION-EVIDENCE.md`, F-CANOPY-068): "The longest request took 5.3 s".
   - **Evidence:** analyze's 5,345 ms maximum stops evicted requests at their eviction. Evicted request 39 (run 2) responded 5,448 ms after entering `watched`, and the same ledger says "2.4–5.4 s".
   - **Fix:** 5.4 s.
   - Changes a number: yes. Disposition: no.

**WHAT I COULD NOT CHECK**

- **Run 1's script source.** Its `args.adhoc_dir` names `clever-juggling-spring`, which the brief forbids reading. So I cannot tell whether run 1 loaded the backup's copies or that worktree's. The backup's compiled shim shows the synthetic check ran from the backup.
- **The live script's own bytes, either run.** Transcripts carry no hashes, and a `__main__` script leaves no `.pyc`.
- **Which input triggered a request.** The shim does not log `changedPropIds`, so "the mode change's request entered at 2.1/2.5 s" is inferred from timing: the next request entered 2,148 and 2,503 ms after the trigger.
- **T-apply's `clamp` field.** It is always null, because `set_props` returns undefined. The gate log shows the clamp was applied.
- **The watchdog's real samples.** Fire times mod 5,000 shift about 1 s across run 1's clamp; the gate also disables `slow-update-interval` during the clamp. The replay's single fixed phase is a model.
- **Out of scope by rule:** the live census, the canopy logs, the counts, and canopy code beyond the gate and watchdog registration at `c7876f5a`.

**SECRETS/PII:** One slip. `git show --stat` of `1b7cf44b` and `5689fedd` printed the commits' author line, including an email address, into my local tool output. It was not repeated, stored or sent. I printed no environment values and read no credential files; the port monitor read only process command lines. I touched no Juniper port, started no Juniper service and changed no repo file. Scratch work stayed in `$S`.

---

## Lane 11-B1 (adversarial, dispositions and ratings, fold side)

*agent `a6b438d1883410135` · round 1 · last-assistant-text (not resumed) · 12626 chars*

**VERDICT: SOUND-WITH-FIXES.** I argued the fold/de-escalate side, and every disposition, rating, count and Still-owed change held up. What needs fixing before this lands as a document of record is the text, not the outcomes. F-CANOPY-058's header and Status bullet still claim more than canopy showed. F-CANOPY-068 slightly overstates its own effect counts. One earlier claim about a canopy node test is now contradicted and was never corrected.

References: L = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `1b7cf44b`. T1 and T2 = `reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json` and `…/run2/2026-10-05_census_live.json`. Canopy file:line references are at `60ae1870` unless a commit is named.

**PER-ITEM TABLE**

| Item | Ledger | Mine | Evidence |
|---|---|---|---|
| 1. F-068 as its own finding | Separate id (L:10729-10735) | Separate id: the case for folding it fails | **Case for folding.** The ledger already held this defect under F-058: in its trigger list, with the sampling mechanism (L:9155-9156); in its fix direction, "A progress-based watchdog predicate … addresses the false fires alone" (L:9190); in Phase 9 BLOCKER 2, "The metrics-store watchdog has the same predicate" (L:8957-8962); and in Phase 9, which listed the false-fire rate as an open F-058 question (L:9621). F-068's own text puts all the user-visible harm in F-058 (L:10727-10728), and its item 24 rides item 0's design. Nothing else covers it: the matrix (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`) has no strand-watchdog row (its only watchdog is E-3's apply clamp, C2.9-06, :351), and no other id holds it. **Why the fold fails.** The gate and the second Input also have fixes of their own (L:9190-9192), yet stay inside F-058. The difference is that those writers do what they are specified to do. The watchdog fired 28 of 28 times with a request in flight and the lane enabled for 10.4–14.7 s of the prior 30 s. That breaks its own comment ("re-enables the interval only after it has been continuously disabled", `dashboard_manager.py:2515-2516`; "must not re-enable DURING a legitimate fetch", `:2520-2522`), its constants comment (`canopy_constants.py:421-424`) and its test docstring (`test_poll_gating.py:194-197`). It also has its own residual: 7 evictions before F-058 amplifies them, one of them a lone eviction. There is precedent: F-058 itself became a finding once it was demonstrated (L:9174-9175). |
| 2. F-068 rating | P2 | P2 | **"Not a defect" fails.** The comment names a mid-fetch re-enable as the very harm the watchdog exists to avoid, and 7 of 28 fires evicted a response. **"Below P2" is not available.** Plan §6.3 (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`) has no lower tier, and the ledger's P2 floor already holds F-034 (a dead store, L:633) and F-063 (a stale quote in a test, L:9936). **The "own contract" (a code comment)** counts under §6.3 only as drift (P2), not as documented behaviour (P1). Precedent: F-057 was P1 only while canopy's manual promised the stream (L:9082). |
| 3. F-058 status, rating and header | OBSERVED LIVE; P1; OPEN; header gains "observed live" | Mechanism OBSERVED LIVE: sound. P1: stands. Header and Status: overclaim, see Findings 1–2 | **The mechanism.** The release trace finds late releases 18/18 and 11/11, with 0 unassigned; a request's own release lands 38–54 ms and 13–89 ms before its answer; `--self-test` passes on both transcripts. **The renderer version.** The legs ran dash 4.2.0, but 4.4.1, the version canopy's lockfile ships (read from a uv-cache wheel), has the same unconditional `runningOff` in `completeJob` (`dash_renderer.dev.js:979-991`) and the same `wDuplicates` (`:3243-3245`), so the observation transfers. **Why P1 stands.** Its basis is F-055's repair and slow pages: F-055's guarded lane self-clocked at 7.4–8.7 s (L:8879-8880), against 4.9 s here. An idle page with 2.8 s median requests does not test that regime, and the second-Input trigger (0 of 45, twice) and the clamp defeat remain untested. **The overclaim.** "Minutes" was not reached on canopy: the longest applied-answer gap outside the 62 s clamp was 34,826 ms, and every answer after the first was `no_update`. The synthetic mount cascade did not reproduce (L:10649-10650). |
| 4. Missed or extra findings | None beyond F-068 | None missed, none extra | The false canopy comments and docstrings are already listed as item 0 corrections (L:9688-9690, L:10816-10817), and `:194-197` sits inside F-068; filing them separately would count them twice. E-3 released the census's artificial clamp at 62.3 s, as its 60 s design says (`canopy_constants.py:560-572`); the redundant release that followed was the census's own write. T-tab's mid-request gate write is F-058's listed tab trigger. Its omission from the Status is Finding 2, not a new defect. |
| 5. Counts and Still owed | 79 / 53 / 1 / 2 / 23; 6 P1; 17 P2; item 0's first half DONE; items 24–25 | Correct | `e2e_finding_triage.py` from `1b7cf44b`, run on the frozen ledger, gives: total 79, fixed 53, accepted 1, withdrawn 2, open 23, open P1 6, open P2 17. That is Phase 10's 78/22/16 plus F-068. Item 0's first half (confirm live, counting evictions) is met, and its untested triggers carry over to item 25. |

**FINDINGS**

1. **MINOR. F-058's header and trigger bullet state a trigger condition that Phase 11's data refute, and present "minutes" as observed live.**
   - **Quoted.** Header (L:9127): "a re-enable more than one period before the in-flight response lands, starts an eviction cascade, and the lane's responses can stop applying for minutes (P1, …; observed live on canopy `main` 2026-10-05, Phase 11; OPEN)". Trigger bullet (L:9142-9144): "it ticks one period later and evicts the in-flight request if its response has not landed by then". And L:10670-10671: "they change nothing the entry's rating rests on".
   - **Evidence.** T1 and T2 together hold 32 mid-request re-enables: 28 fires and 4 gate writes.
     - 21 came more than one 1,000 ms period before the in-flight response landed.
     - 8 of those evicted, and 6 of the 8 cascaded.
     - 13 evicted nothing. In T1 the answer landed 1,052–2,164 ms after 8 fires, and 1,103 and 1,114 ms after 2 gate writes. In T2 it landed 1,154 and 1,754 ms after 2 fires, and 1,763 ms after a gate write.
     - Phase 11 says so itself ("a race, with no fixed horizon", L:10641), and F-068's Effect bullet gives the correct condition (L:10722-10724).
     - The Status bullet (L:9129-9135) mentions neither the race, the 34.8 s ceiling, nor the mount cascade's failure to reproduce.
   - **Fix.**
     - Header: "…or a re-enable that lets the next request be made before the in-flight response lands, can start an eviction cascade, and the lane's responses can stop applying for minutes (P1, …; mechanism observed live on canopy `main` 2026-10-05, runs of up to 11 evictions and 34.8 s, Phase 11; minutes only in synthetic repros; OPEN)".
     - Correct the trigger bullet the same way.
     - Add the 34.8 s ceiling, the 13 non-evicting re-enables and the mount-cascade result to the Status bullet.
     - At L:10670 write: "confirm the mechanism; the minutes remain synthetic; P1 rests, as before, on slow pages and on F-055's repair".
   - **Changes a number/disposition/action? No.** P1 and OPEN stand, and the triage tool reads the same token.

2. **MINOR. "Only two triggers occurred" contradicts the phase's own gate log.**
   - **Quoted.** L:10660-10662: "Of the entry's triggers, only two occurred: the watchdog's false fires and the gate's write at page load. A tab switch, the end of an Apply and a second-Input change in mid-request were not tested". The Status bullet (L:9132-9133): "the other triggers below, and the clamp defeat, were not tested".
   - **Evidence.**
     - T1 gate `True->False` at 480,696 ms: T-tab's second click, with req 102 in flight, answered 1,103 ms later.
     - T1 gate `True->False` at 728,126 ms: T-apply's redundant release, with req 140 in flight, answered 1,114 ms later.
     - T2 gate `True->False` at 478,476 ms: T-tab's second click, with req 91 in flight, answered 1,763 ms later.
     - None evicted. Phase 11 records all three itself (L:10650-10652).
     - That is the only canopy evidence on the tab trigger, against its synthetic result of "0 of 28 over ~120 s" (L:8953-8954), and it is left out exactly where the rating is discussed.
   - **Fix.** Write: "Four trigger kinds occurred mid-request: false fires (28, of which 7 evicted), the page-load gate write (1, a run of 1), a tab switch (2, neither evicting) and a clamp release (1, the census's redundant write, not evicting). None was a scored test. The second-Input change and the clamp defeat did not occur." Make the same change in the Status bullet. Item 25 stands.
   - **Changes a number/disposition/action? No.**

3. **NIT. F-068 overstates its own effect.**
   - **Quoted.** L:10689: "7 of the 28 fires started F-CANOPY-058 cascades". L:10724: "through F-CANOPY-058 each became a run". L:10732-10733: "every false fire would still cost a response".
   - **Evidence.** The T2 trace reads: "req 39: W @222476, X @225254, late release @227924 …, under req 40 (which then ended A)". That is a lone eviction, which is the case F-068 itself describes as happening without F-058 (L:10725-10726). The runs started by fires are [2, 11, 4] and [1, 2, 4, 4], so 6 cascades. 21 of the 28 fires evicted nothing (L:10643-10644).
   - **Fix.** Write: "7 of the 28 fires evicted a response, and 6 of those started F-CANOPY-058 cascades". And: "every evicting false fire (7 of 28 here) would still cost a response". The argument for a separate id survives the correction.
   - **Changes a number/disposition/action? Yes, one header count only** (7 → 6 cascades). No disposition or rating changes.

4. **NIT. Two record gaps around F-068's evidence.**
   - **Quoted.** L:8980-8981: "Settled 2026-09-24 for `main`'s node-gated test, #614's metrics-store watchdog". And item 0's list of canopy text to correct (L:10816-10817), which adds only `test_poll_gating.py:194-197`.
   - **Evidence.**
     - canopy#614 (`5c87f983`) touched only `canopy_constants.py`, `dashboard_manager.py` and `test_poll_gating.py`, and that test file has no node call.
     - At `e9053227` and `60ae1870`, the node-gated tests are F-042 (two files), F-054, the idle cuts, Y4 and the phase-B bridge (`git grep which("node")`).
     - So Phase 11's "No node-gated test … runs it either" (L:10704-10705) is right, and Phase 9's line is wrong but still stands uncorrected.
     - The watchdog's own comment makes the same false "continuously disabled" claim (`dashboard_manager.py:2515-2516`; `canopy_constants.py:421-424`), and neither is on item 0's correction list.
   - **Fix.** Add a correction note at L:8980, and add `dashboard_manager.py:2514-2522` and `canopy_constants.py:412-424` to item 0's list.
   - **Changes a number/disposition/action? No.**

**WHAT YOU COULD NOT CHECK**
- **The live runs themselves.** I started no leg and touched no port. Every figure was re-derived from the committed transcripts, using the committed readers (`…_analyze.py`; `…_release_trace.py` and its `--self-test`; `…_watchdog_alias_replay.py`, which reproduces 5–16 and 3–18 in phase and a median of 2 jittered). I also wrote my own scripts for applied-answer gaps, mid-request re-enable outcomes and trigger timings, kept in a `mktemp -d` scratch directory.
- **Whether the shim's dispatch overhead shifted the race.** No uninstrumented control run exists.
- **Aliasing versus a phase lock through the renderer's queue.** The transcripts hold only the fires, not the watchdog's other samples.
- **F-058 live on dash 4.4.1, or at slow-page latency (5–8 s), where "minutes" would have to be shown.** I have only source reading and the synthetic results.
- **Byte-identity of the first run's files with the backup outside the repo.** I did not open it.
- **Canopy's test suite.** Not run; I read the test sources from canopy's object store only.
- **The leg logs.** I confirmed only one page connection per log (05:56:14–06:21:29 and 16:11:19–16:36:31) and the 62 and 55 refusal lines, by line counts.

**SECRETS/PII:** No environment variables, tokens, credential files or email addresses were printed, sent or requested. I read the leg logs only through line counts and a script that prints a timestamp plus the matched phrase. Everything was read-only: juniper-ml through the worktree, canopy only from its object store (`show`, `ls-tree`, `log`, `diff`, `grep`; no fetch). No slips.

---

## Lane 11-B2 (adversarial, claims beyond evidence, escalate side)

*agent `af637a211e51aad4e` · round 1 · last-assistant-text (not resumed) · 11209 chars*

**VERDICT: SOUND-WITH-FIXES.** The mechanism reading and every measured number hold. One rating is wrong (P2 should be a conditional P1), and three passages say more than the phase's own events show.

Citations: `EVIDENCE.md` is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `1b7cf44b`. `PLAN.md` is `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`. Canopy files are read at `60ae1870`.

**CLAIM TABLE**

| Claim | Result | Evidence |
|---|---|---|
| "every fire was false" | holds | Release trace: at 28 of 28 fires a request was in flight, and the lane had been enabled 10,424–14,705 ms of the prior 30 s. The longest flight was 5,345 ms. |
| Every evicted request's discarded response released the guard under its successor; "read directly" | holds | The pairing is not read from the log. The reader assigns each late release to the oldest evicted request by elimination (`2026-10-05_f058_census_v2_release_trace.py:122-146`). Timing confirms the pairing in all 29 cases. Each release fell under the immediate successor (id+1). Release minus the evicted request's entry was 2,355–5,448 ms, the normal flight range. Release minus the successor's entry was 68–2,646 ms, and 28 of 29 were under 1.5 s, where only 6/307 and 15/303 flights were that short. So these cannot be the successor's own releases, and the slow-answer alternative fails. Release minus eviction was 89–2,670 ms, so they are not tied to the eviction. No release record is duplicated or nested, and 0 are unassigned. The nested-logging alternative fails too. |
| "none of its samples fell in those enabled stretches" | holds | This follows from the watchdog code (`dashboard_manager.py:2531-2545`). Reconstructing samples at fire − 5,000k (k = 1..6): 163 of 168 land disabled. The other 5 sit 31–354 ms inside an enabled stretch, which is within sampler jitter. |
| "none runs the predicate" / no node-gated test runs it | holds | None of the 6 node-gated test files references the watchdog. The UI tests load the app but none asserts on the watchdog. |
| "loses no row that the next applied answer carries" | holds | The feeder replaces the store (`dashboard_manager.py:7987`). The WebSocket append opts out in full modes (`:7870`). |
| "a write of `false` re-enables the Interval whichever callback makes it" | holds | In dash 4.2.0's `dash_core_components.js`, `handleTimer` clears the timer while disabled and starts a new `setInterval` when the prop turns false, reading props only. |
| "the run follows from the late release, not from the writer" | holds | Release-trace rows. |
| "Neither changes the code this phase cites" | holds | `git diff 60ae1870 c7876f5a`: #705 touches a workflow file only. #722's one `dashboard_manager.py` hunk is `:7341-7348`; later lines shift by +1. |
| "the fires come from the samples keeping phase with the cycle" | holds, as sufficiency | Replay reproduced: aligned 5–16 / 3–18, jittered median 2, zero fires in 87/500 and 82/500. The watchdog's samples run on an unbroken 5 s grid: fire-to-fire gaps are near-whole multiples of 5,000 ms, minimum 35.0 s (7 periods, the predicate's floor). So the renderer's queue is not pulling the samples onto the feeder's cycle. Observed counts sit at about the 77th and 89th percentiles of aligned phases, so some extra coupling is still possible; the ledger's hedge stands. |
| "each sample falls about 0.1 s later in the cycle" | overreaches | Finding 4b. |
| Enabled stretch = "1 s tick plus the renderer" | holds | Shortest enabled stretch outside the Apply clamp: 1,142 ms. |
| "a re-enable would tick before its response landed" | holds literally | A tick is not an eviction: the next request was made 1.4–3.4 s after a re-enable. About 98% of flights exceed 1.4 s, so the point still stands. |
| T-apply release attributed to canopy's E-3 clamp watchdog | holds | The T-tab console line bounds the page clock's zero (T0) to before 05:56:14.764 CDT. So the census's own release call (`2026-10-04_f058_census_v2_live.py:247-249`) came after 727.24 s page time, later than the 726.055 s write. E-3 is at `dashboard_manager.py:4246`. |
| "A re-enable while a request is in flight is followed by that request's eviction" | false | Finding 2. |
| "only two occurred" / "not tested" | false | Finding 3. |
| "every false fire would still cost a response" | false | Finding 4a. |
| "The replay suggests the rate falls as the cycle moves away from the 5 s sampling period" | overreaches mildly | The replay changed only the sampling period and kept the measured lane's ~57% disabled share. Longer requests would raise that share. Phase 9's own model gave 37–44 an hour at a 7 s request time. Not raised as a finding. |
| "What a user would see" | holds | In the stale-stream and full-view regimes the feeder is the store's only writer (`:7856-7877`, `:7913-7927`). |
| F-CANOPY-058 rated P1 | holds | The 34.8 s idle stall is correctly not claimed as "minutes". The training-run regime is correctly left unmeasured. |
| F-CANOPY-068 rated P2 | wrong | Finding 1. |
| Counts 79/53/1/2/23, 6 open P1, 17 open P2 | reproduced | `e2e_finding_triage.py` on the frozen ledger. Finding 1 changes them. |

**FINDINGS**

**1. MAJOR — F-CANOPY-068's rating never applies plan §6.3's test, and the ledger rates a matching case P1.**
- Quoted: "**Rating: P2.** On its own it delays the chart by a cycle at a time, which plan §6.3 puts under drift" (`EVIDENCE.md:10727-10728`). Also the title's "(P2, …)" (`:10689`) and the counts (`:10560-10561`, `:10804-10807`).
- Evidence:
  - §6.3's test is "P1 (breaks a documented behaviour)" (`PLAN.md:359-360`), not user-visible harm.
  - Canopy's `CHANGELOG.md`, under "## [0.8.0] - 2026-09-11" (`:971`) / "### Fixed" (`:1173`), placed there by canopy#624 (`06d8607e`), says the watchdog "re-enables the interval once it has been continuously disabled for `METRICS_STORE_STRAND_TIMEOUT_MS` (30 s …) … because fast recovery would reopen the eviction window above" (`:1221-1226`).
  - The #613 entry in the same section says `running=` "stops that clock for exactly the duration of each fetch" (`:1198-1199`).
  - Phase 11 measured the first promise broken at 28 of 28 fires, and the second at 7 evicting fires.
  - F-CANOPY-065 is carried as P1 on exactly this footing: a shipped CHANGELOG promise, pending the owner's ruling (`EVIDENCE.md:10114-10121`, `:10302-10304`). It is counted among the 6 open P1.
- Fix: rate F-CANOPY-068 the way F-CANOPY-065 is rated: P1 if a shipped CHANGELOG promise counts as documented, P2 if not. Add it to the same owner question. While F-CANOPY-065 is carried as P1, the counts become 7 open P1 and 16 open P2.
- Changes a number/disposition/action? Yes.

**2. MINOR — Phase 11 claims every mid-request re-enable evicts, and leaves the entry's refuted one-period horizon in place.**
- Quoted: "What is now observed is the class as filed. A re-enable while a request is in flight is followed by that request's eviction" (`EVIDENCE.md:10656-10657`). The title says "a re-enable more than one period before the in-flight response lands, starts an eviction cascade" (`:9127`). The trigger bullet says "ticks one period later and evicts the in-flight request if its response has not landed by then" (`:9142-9144`).
- Evidence:
  - The two transcripts hold 32 mid-request re-enables: 28 fires plus 4 gate writes of `false` with a request in flight (run 1 at 7,253 / 480,696 / 728,126 ms; run 2 at 478,476 ms). Only 8 evicted.
  - 13 of the 24 that did not evict had the in-flight response land 1,052–2,164 ms after the re-enable, i.e. more than one period. Example: the gate write at 728,126 ms; request 140 was answered 1,114 ms later and the next request started at 1,560 ms.
  - The phase itself says "a race, with no fixed horizon" (`:10641`), and F-CANOPY-068's Effect bullet uses the right horizon (`:10722-10724`).
- Fix: say it evicted when the response landed after the next request was made, 8 of 32 here. Change the title and trigger bullet from "one period" to "before the next request is made (1.4–3.4 s here)".
- Changes a number/disposition/action? Yes: the title, the trigger bullet, and the horizon item 0's tests would use. No rating change.

**3. MINOR — The tab-switch and end-of-Apply triggers did occur mid-request; the phase says they were not tested.**
- Quoted: "only two occurred … A tab switch, the end of an Apply and a second-Input change in mid-request were not tested" (`EVIDENCE.md:10660-10662`). The Status bullet: "the other triggers below … were not tested" (`:9132-9133`).
- Evidence:
  - Tab-switch gate write mid-request, twice: run 1 at 480,696 ms (599 ms into request 102, answered 1,103 ms later); run 2 at 478,476 ms (1,081 ms into request 91, answered 1,763 ms later).
  - End-of-Apply gate write mid-request, once: run 1 at 728,126 ms.
  - None evicted. The phase records all three itself (`:10650-10652`).
  - Only the second Input and the clamp defeat went unexercised.
- Fix: say these triggers occurred mid-request three times, incidentally, with no eviction; the targeted tests landed late.
- Changes a number/disposition/action? Yes: the text, and the trigger inventory item 25 starts from.

**4. NIT — three small overreaches.**
- (a) "every false fire would still cost a response" (`:10731-10732`). 21 of 28 fires evicted nothing. Fix: "an evicting false fire (7 of 28 here)".
- (b) "each sample falls about 0.1 s later in the cycle" (`:10712-10713`). That is true only of the run-wide median. Before 9 of run 1's 13 fires the local cycle was over 5 s (mean 5.04–5.32 s over the prior 35 s), and the reconstructed samples fell *earlier* in the cycle before 10 of 13. Run 2 went the other way, with 12 of 15 local cycles under 5 s. Fix: describe the drift without a direction.
- (c) "reached the page 1.3–4.2 s after they fired, through the renderer's queue" (`:10778`). T-tab's 3.4 s and 4.2 s are mostly the driver's own click sequence (`2026-10-04_f058_census_v2_live.py:256-259`). The second click went out 2.94 s and 2.31 s after the trigger; its gate write landed 0.46 s and 1.89 s after the click. Item 25 should therefore fire triggers from inside the page, from the shim, not through a Python round trip.

**WHAT YOU COULD NOT CHECK**
- Which completion caused each release. The log carries no request identity on a release, and no network timings, so the pairing rests on timing.
- The watchdog's non-firing samples. They are not logged; my grid reconstruction assumes samples every 5,000 ms.
- Whether the trio's processes were the same before and after the second run. No artifact records it.
- dash 4.4.1 behaviour, and any training-run regime.
- The owner's ruling on CHANGELOG promises. Finding 1 is conditional on it.
- I did not re-run the 6-of-6 synthetic check, Phase 9's runs, or Lanes B and B1.

**SECRETS/PII:** One slip: my first `git show --stat 1b7cf44b` printed the commit's author line, which contains an email address, into my local tool output. I did not repeat it or send it anywhere. No environment values, tokens or credentials were printed. No repo was written, no service or port was touched, and no browser was driven. My probes are only in my mktemp scratch directory.

---
