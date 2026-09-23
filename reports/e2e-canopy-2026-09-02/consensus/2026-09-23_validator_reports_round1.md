<!-- markdownlint-disable -->

# Canopy E2E arc, Phase 8 (canopy#670) — validator reports, round 1, 2026-09-23 (verbatim)

Archived by util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py from the session's subagent transcripts, each cut at its round-2 brief. Each section is the agent's round-1 report exactly as delivered. They are EVIDENCE for Phase 8 of notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, not conclusions: the reconciliation, including where a report was itself corrected, is in that phase. Lanes A1 and A2 were killed by the session limit at ~06:33Z before reporting; their sections hold the last text they produced.

## Lane A1 - recompute the Phase 8 numbers (killed by the session limit)

*agent `af915b2324d8279c7` · round 1 · last-assistant-text (not resumed) · 63 chars*

You've hit your session limit · resets 5:10am (America/Chicago)

---

## Lane A2 - independent clean-room recreation (killed by the session limit)

*agent `a6a133770ac3da134` · round 1 · last-assistant-text (before its round-2 brief) · 63 chars*

You've hit your session limit · resets 5:10am (America/Chicago)

---

## Lane A3 - verify the PR, the tests and the waiver claims

*agent `a25f75e8f14098f24` · round 1 · last-assistant-text (not resumed) · 9580 chars*

## Lane A3 report: juniper-canopy PR #670

Every quantitative claim re-derives exactly. Nothing is WRONG or UNTRACEABLE. But the PR cannot merge right now: its branch is behind `main` and one review thread is unresolved.

Subject: signed commit `c0530279`, parent `2f973ca2`, PR head `29cc9622`. The claims come from the PR #670 body, PR comment 5790069447, the `c0530279` commit message, and the entry that commit adds to canopy's `CHANGELOG.md` (lines 45–89).

### Claim table

| # | Claim | Verdict | What I found |
|---|---|---|---|
| 1a | 60 tests removed: 38 from `test_metrics_panel_handlers.py`, 22 from `test_metrics_panel_helpers_coverage.py` | CONFIRMED | An AST diff shows the handlers file going from 140 to 102 tests and helpers-coverage from 70 to 48. Both diffs are pure deletions. |
| 1b | 47 of them, in seven classes, never called production code | CONFIRMED | Handlers file: `TestHandleReplayControls` 13, `TestReplayTick` 5, `TestUpdateReplayUI` 3, `TestUpdatePlayButton` 4. Helpers-coverage: `TestHandleReplayControls` 15, `TestReplayTick` 4, `TestUpdateReplayUI` 3. That is 7 class definitions using 4 distinct names. Every body is logic copied inline. Each test requests the `metrics_panel` fixture, which builds a `MetricsPanel`, but no body uses it. |
| 1c | 12 were guarded with `if func := callbacks.get(...)` and would pass silently once the callbacks were gone | CONFIRMED | 7 guard `handle_replay_controls`, 3 guard `replay_tick`, 2 guard `update_play_button`. On the parent the fixture captures all three names, so these tests were live there (the parent's two files pass 210/210). Run against `c0530279`'s code, all 12 pass without testing anything. |
| 1d | One looked the merged callback up directly | CONFIRMED | `TestRegisteredCallbacks::test_update_replay_ui` uses `callbacks["handle_replay_controls"]`. Against `c0530279` it is the only one of the 60 that fails (KeyError); the other 59 pass. |
| 1e | Did any removed test exercise production code that survives the change? | None | The 13 `TestRegisteredCallbacks` tests exercised `handle_replay_controls`, `_handle_replay_controls_handler`, `replay_tick` and `update_play_button`. All four are deleted. Surviving code (`__init__`, `register_callbacks`) is reached only during fixture setup. |
| 2 | New `test_f054_replay_block_clientside.py` has 43 tests | CONFIRMED | Collect-only in the provided checkout reports 43. A probe plugin confirmed the import came from the checkout's own `metrics_panel.py`, not the main clone's editable install. Run: 43 passed, **0 skipped** (node v24.13.1 is installed). 31 of the 43 are marked `@needs_node` and would skip without node. On CI for head `29cc9622`, all 4 unit jobs ran all 43 with none skipped. |
| 3a | All 43 fail on the parent | CONFIRMED | In a scratch worktree at `2f973ca2` with both test files copied from `c0530279`, 43 of 43 fail. 38 fail on "the replay state's writer is served by the server, not clientside", 2 on "found 0" allow_duplicate writers of the position text, 1 on "2 writers of replay-state", 1 on "server callbacks still write the replay block", and 1 because `handle_replay_controls` is still registered. This depends on node being present; without it, 31 would skip instead of failing. |
| 3b | The two changed readiness tests in `test_f048_replay_cycle.py` fail on the parent too | CONFIRMED | `test_no_replay_callback_blocks_itself` and `test_nothing_pending_can_hold_the_replay_controls` fail. The file's other 6 tests pass there. |
| 4a | 94 FAIL findings (86 distinct keys), all waived by the `Allow-Symbol-Loss` trailer | CONFIRMED | The screen (0.8.0, `--scope "src/**/*.py"`, `2f973ca2..c0530279`) exits 0 with 107 findings: 94 waived and 13 relocated (warnings, not FAILs). The 94 carry 86 distinct keys, because 8 keys appear in both old test files. The trailer has 29 lines holding 86 distinct keys, an exact match (none missing, none extra). The PR's current range `7950bf9e..29cc9622` gives the same result. CI's own run with the pinned 0.9.0 is identical. The docs screen exits 0 on both ranges. |
| 4b | The waiver survives canopy's squash, now that a merge commit sits on top of `c0530279` | CONFIRMED, with conditions | Repo setting: squash messages are built from commit messages (`COMMIT_MESSAGES`). GitHub's default squash body drops the merge commit and keeps `c0530279`'s full body. The screen matches any line starting with `Allow-Symbol-Loss:`, not git trailer parsing. PR #652 had the same shape (one waiver commit plus 3 update-branch merges); its squash `32e7feea` kept all 5 waiver lines verbatim and passed the post-merge "Symbol & Docs Screen". Conditions are in item 2 below. |
| 5a | CI state of head `29cc9622` | GREEN | The rollup is SUCCESS, and all 21 required checks in ruleset 14249530 passed (runs 35826512698, 35826512648, 35826513014). It is still not mergeable; see item 1 below. |
| 5b | Head commits are signature-verified | CONFIRMED | `c0530279` and `29cc9622` both return `verified: true, reason: valid`, signed by GitHub (web-flow). |
| 6a | `REPLAY_CONTROL_IDS`, and the JavaScript dispatches on exact membership | CONFIRMED | 9 entries at `metrics_panel.py:213-223`, injected at registration as a JSON list. The JS checks the id prefix, strips it, and skips anything not found by `controls.indexOf(control)`, which is an exact match. The tick uses `cid === tickId`. `test_dispatch_is_exact_not_substring` passes. |
| 6b | Removed: `replay_tick`, the play-label callback, `MetricsPanel._handle_replay_controls_handler` | CONFIRMED | All three are deleted; the play-label callback was `update_play_button`. The server callback `handle_replay_controls` is also deleted, which the list leaves out. |

### Stale references at `c0530279`

1. **`src/tests/unit/frontend/test_f048_replay_cycle.py:21-28`** still says the file proves SEMANTICS by "a differential check against verbatim copies of both, below", and that every control Input "is one the handler dispatches on". Those tests and copies were removed from this file. **Lines 33-35** say "it is not ready while a primary writer of the metrics store is pending", which this change reverses. The F-054 paragraph appended at lines 41-48 corrects both, so the docstring now contradicts itself.
2. **`CHANGELOG.md:112-116`** (the F-048 entry) says in the present tense that "`metrics-store.data` is an Input of the merged callback". That is false at `c0530279`. The F-054 entry at lines 69-74 says the opposite, and both sit under `## [Unreleased]` (line 10), so both will ship in the same release notes.
3. **`docs/testing/TESTING_MANUAL.md:169-170`, `docs/testing/TESTING_REFERENCE.md:360`, `docs/cascor/CASCOR_BACKEND_MANUAL.md:784`** give `pytest …/test_metrics_panel_handlers.py -k "… or replay …"` as the replay handler test command. On the parent it selected 41 tests in that file; now it selects 9, all about replay visibility. None of the replay-control tests are reachable by it. Minor.

Checked and not stale: `metrics_panel.py:1090, 1107, 1135, 1589`; `test_f048_replay_cycle.py:8-9, 39, 43, 327`; all 15 hits in the new test file; `CHANGELOG.md:47-78`; `notes/history/proposals/phase1/README.md:137-139` (archived); `docs/USER_MANUAL.md:307-310`; `CASCOR_BACKEND_MANUAL.md:286-291`. `AGENTS.md` and the live `notes/` contain no references.

### Anything else wrong

1. **The merge is blocked now, even though every check is green.**
   - **Behind `main`.** `main` gained `39ee09f8` (#664) and `cc3588a8` (#663) after `29cc9622`. The ruleset requires the branch to be current (`strict_required_status_checks_policy: true`), so it needs another update-branch and a full new CI round. The green rollup above is not what would be merged.
   - **Unresolved review thread.** CodeQL flags an unused import (alert 295) at `test_f054_replay_block_clientside.py:46`, and `required_review_thread_resolution: true` makes that thread block the merge. The alert is correct: `import dash` is unused; only line 48's `from dash import …` is used.
   - The merge state read BLOCKED when this session started and BEHIND at the end.
2. **Conditions on 4b.** The waiver survives only if the squash uses GitHub's default message. A custom `--body` / `--body-file`, or auto-merge armed with its own commit body, would replace it (auto-merge is not armed now). Also, in the squash GitHub moves the co-author line into a new final paragraph. On `32e7feea`, git's own trailer parser therefore finds **0** `Allow-Symbol-Loss` trailers. That doesn't affect this screen, but any tool that uses git trailer semantics would miss the waiver.
3. **Docstring imprecision in `test_f054_replay_block_clientside.py:34-36`.** It says "the node tests fail at `_controls_entry`", but `TestRefillPosition` fails at `_refill_entry` instead, as does the wiring test `test_the_refill_callback`. Minor.

### Housekeeping

Everything was read-only. I created two scratch worktrees under `laneA3/` (`wt_parent` at `2f973ca2`, `wt_fix` at `c0530279`), then removed them with `worktree remove --force` and ran `worktree prune`. My first fetch had created a temporary ref, `refs/remotes/origin/pr670-laneA3-readonly`; I deleted it with a guarded `update-ref -d`. The provided checkout's `status --porcelain --ignored` is identical before and after. The only side effect in the main canopy clone is updated remote-tracking refs from `git fetch`.

**Changed:** no repository file. Scripts, JUnit XML, JSON reports and CI logs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/6280349a-397b-4e22-9fc5-a32818ed1f58/scratchpad/laneA3/`.

---

## Lane B - adversarial review of canopy#670

*agent `a734684513e7f8d2f` · round 1 · last-assistant-text (before its round-2 brief) · 10506 chars*

## Lane B verdict on juniper-canopy PR #670 (head 29cc9622; replay code identical to c0530279)

**Bottom line:** claims 1, 3, 4, 5, 6 and 7 survive. Claim 2 is partially refuted. The PR's claim that "nothing is evicted" is false: a pause clicked during playback can still be silently dropped when the renderer's 12-slot pool is full. I also found two smaller regressions. None makes this PR worse than its parent: once a pause applies, it now holds. I would not block the merge, but the false claims should be corrected first.

**Setup checks.** My comparison script shows the local fix checkout reproduces the PR diff byte-for-byte. At 29cc9622 the PR diff is identical to c0530279 apart from `index` lines and offsets, and #665 touches only registry and dataset files. The parent-leg worktree was deleted during my review (not by me). The byte-for-byte parent comparison was already done, and afterwards I rebuilt the parent from the GitHub diff. Renderer line numbers below are `dash_renderer.dev.js` (dash 4.2.0).

### Claim 1 (tick-only clientside would be worse): SURVIVES
- **Mechanism:** a new same-identity request drops the in-flight one: `wDuplicates`/`eDuplicates` at :3026-3027, removed at :3151. The late response then finds nothing in `watched` and is discarded (:2697-2704).
- **Why same identity:** `getUniqueIdentifier` (:1715-1728) hashes the callback's inputs, outputs and state, not what triggered it.
- **Re-run of the PR's own clean room** (ports 18781+): `cs_tick` gave CLICK-DROPPED; the store ended at playing/22 while the DOM showed a stale "▶ 0 / 119". `current` gave F054-UNDONE.
- **Nit:** the code comment at metrics_panel.py:1104 cites `~:3024` for `wDuplicates`. :3024 is actually `pDuplicates`, which is the mechanism behind new defect 1; `wDuplicates` is :3027.

### Claim 2 (no in-flight window; cannot be evicted or read stale): PARTIALLY REFUTED
- **True for the execution window.** `executeCallback` fills Inputs (:1183) and State (:1243) from one layout snapshot and calls the function synchronously (:639). A non-promise return skips the only `await` (:641). The rest is microtasks up to the synchronous `updateProps` (:2475). The only `setTimeout` (`wait(0)`, :2962) comes before promotion.
- **False for the queue before execution:**
  - Clientside callbacks are subject to the 12-slot cap (:2846), so a click can sit in `prioritized`.
  - `pDuplicates` (:3024) then replaces it with the next tick's request. Changed-prop ids are merged only among `requested` duplicates (:3004), so the click's trigger is gone.
  - Replacements are appended to the back of the queue (`AddPrioritized` is a plain `concat`, :3589).
  - Evidence is under new defect 1.
- **Stale snapshot on the `blocked` path.** `dcc.Slider` is an async chunk (`async-slider.js`). A blocked callback later runs with the layout captured when it was prioritized (:2838, :2880). This matters only at mount and is not a regression.

### Claim 3 (nothing pending can hold the controls): SURVIVES, for readiness only
- The test's closure model matches `getAllSubsequentOutputsForCallback` (:1617), including the `@hash` dead end. It is a superset, so it errs on the safe side.
- I rebuilt the check independently against the built app's 177 served callbacks (from a copy of `src`):
  - Nothing outside the block writes the checked Inputs; only the callback itself writes `replay-slider.value`, which is its own output.
  - No closure reaches the checked Inputs.
  - The refill is held only by `update_metrics_store` (#111) and the display-mode callback (#17), and it holds nothing.
  - The app's only `running=` side output is `metrics-store-interval.disabled`. My first `running=` parser was vacuous; I confirmed this from the raw served entry instead.
- **Caveat:** readiness is not the only gate. The test docstring (test_f048_replay_cycle.py:332) says a click is promoted "whatever else is in flight". That is true of promotion, but execution still waits on the 12-slot cap.

### Claim 4 (JS reproduces the old handler): SURVIVES for every input the app can produce
- **Differential beyond the PR's grid:** I ran 335 extra cases against the verbatim old handler.
  - Merged multi-control triggers: 0 of 20 differ.
  - `end_index`=0 and index-beyond-max: identical.
  - Divergences appear only for impossible states: a `{}` state, missing keys, speed 0.
  - The exception is a NaN slider value, which is reachable (new defect 2).
- **Mount path:** page load uses `outputsOnly: true` (:7152), and a tab-rebuild chunk skips the input path when all outputs are inside the chunk (:6986-6991). So `triggered` is `[]`, and the JS handles both `[]` and ".".
- **Real browser:** mount rendered "0 / 119". A drag to 75% landed on index 89 = trunc(0.75×119). A typed 150 is clamped to 100 by the component.

### Claim 5 (refill holds nothing; the stale thumb is the only regression): mostly SURVIVES
- Nothing consumes `replay-state.data` as an Input any more (it is State for callbacks #11 and #12). `toggle_replay_visibility` and the layout are unchanged.
- Refill during playback: playback continued, the text switched to "2 / 239" within 304 ms, and the thumb caught up at the next tick. That matches the documented cost.
- One further regression: new defect 3.

### Claim 6 (60 removed tests): SURVIVES
- The breakdown matches exactly: 38 + 22 = 60.
- **47 inline tests in 7 classes** that never called production code:
  - handlers: TestHandleReplayControls 13, TestReplayTick 5, TestUpdateReplayUI 3, TestUpdatePlayButton 4
  - helpers: TestHandleReplayControls 15, TestReplayTick 4, TestUpdateReplayUI 3
- **12 tests guarded by `if func := callbacks.get(...)`:** 7 for `handle_replay_controls`, 3 for `replay_tick`, 2 for `update_play_button`.
- **1 direct lookup:** `test_update_replay_ui`.
- None covered code still in production, and no surviving test references the removed callbacks.

### Claim 7 (new tests not vacuous): SURVIVES
- Locally: 51 passed, 0 skipped (node v24.13.1).
- CI at 29cc9622 (Python 3.13 leg, run 35826512698): 43 + 8 tests passed; the 5 skips are unrelated.
- The oracles are independent of the code under test. Nine mutations of my own, none from the PR's list, were all caught on a copy.
- On the rebuilt parent, all 43 new tests fail, plus the 2 changed readiness tests.
- **Limit:** these tests cannot see renderer queueing (defects 1 and 3) or the component emitting NaN (defect 2).

## New defects

**1. Major, not a blocker: a pause or other click queued behind the 12-slot cap is dropped by the next tick.**
- **Forced saturation** (12 server callbacks, each sleeping 3 s):

  | Arm | Result (3 runs each) |
  |---|---|
  | Control, no saturation | PAUSE-HELD 3/3, applied in 35–41 ms |
  | Saturated, pause during playback | PAUSE-LOST 3/3 |
  | Saturated, click while paused (no ticks) | Applied late, 2.59–2.63 s |

  In a lost run the trace shows the click in `prioritized` at +34 ms (pool = 12). The tick replaces it at +43 ms, and playback runs on to index 14–15.
- **Dynamic load** (12 `running=`-guarded pollers):

  | Load | Pool full (share of time) | Pauses lost |
  |---|---|---|
  | No pollers | 0% | 0 of 8 |
  | Latency 2.5 s | 4% | 1 of 12 |
  | Latency 4 s | 17.3% | 2 of 12 |

  Both lost trials at 4 s show the same replacement in the trace.
- **Canopy context:** the note `reference_dash_renderer_12_slot_starvation.md` records the pool full 25.5% of the time at idle and 35.3% under training, measured 2026-08-24. I did not measure a live leg.
- **Suggested fix:** derive events from Input values rather than `ctx.triggered`. Keep per-control click counts in the state, the same way `tick_n` is kept, and treat a slider value different from the last one written as a seek. A dropped trigger would then be applied at the next tick.
- Also correct the claims in CHANGELOG ("nothing is evicted"), metrics_panel.py:1110-1115 and test_f048_replay_cycle.py:332.
- Make the verify leg record `executing + watched` at each click and deliberately pause while the pool is at 12.

**2. Minor: clearing the slider's number box sets the replay index to NaN.**
- dash 4.2.0 sliders show a number box by default (`allow_direct_input=True`), and canopy does not disable it.
- Clearing the box sends `value = NaN`. The guard at metrics_panel.py:132 passes NaN because `typeof NaN` is "number".
- Result: the position reads "NaN / 119". After Play, the replay never reaches the end, so it runs indefinitely with the interval on. End or a valid seek recovers it.
- The old server path received `null` and raised TypeError, leaving the state intact, so this is a regression.
- **Fix:** skip the seek unless `Number.isFinite(sliderValue)`, or set `allow_direct_input=False`. The latter also hides the raw float the box displays.

**3. Minor: the refill can overwrite the position with a stale index.**
- When the refill and the controls callback run in the same pass, both read one snapshot. If the controls callback applies first, the refill overwrites the text from the pre-control state.
- Reproduced 2/2 (click, then `set_props` on the store): the state was 6 and the thumb matched 6/239, but the text read "5 / 239". It stays wrong until the next control. The reverse order is consistent.
- This is rare in canopy, since store writes are uncommon while replay is visible.
- **Fix:** have the refill write only the "/ max" part (split the span), or drop the refill.

**4. Informational: drag snapping on short histories.**
- The immediate write-back snaps the thumb to 25% steps while dragging over 5 rows. The final seek is correct.

## Not checked
- No live canopy leg (per constraints), so the real pool occupancy at the moment of a pause and the real loss rate there are unmeasured.
- I did not run the full unit lane locally; I relied on CI.
- Experiments used `html.Button`, not `dbc.Button`, and headless Chromium only.
- The blocked (async-slider) path was read, not exercised.
- The PR's own mutation script edits the checkout in place, so I ran my own mutations on a copy instead.
- The ledger notes and the verify-leg comment (not yet posted) were not reviewed.

**Changed:** no tracked file. I executed inside the fix checkout only for the pytest run the brief instructed. My scripts and results are in `.../scratchpad/laneB/`; the key ones are `exp_prioritized_eviction.py` with `run3.json`, `exp_pool_load.py` with `load_12_l4.json`, `exp_input_box.py`, `exp_same_pass.py`, `deps_check.py`, `my_mutations.py`, `edge_diff.py` and `parent_falsify.py`.

---

## Lane B2 - argue against merging canopy#670

*agent `a7e7deb96ecf6b34a` · round 1 · last-assistant-text (before its round-2 brief) · 8364 chars*

## Lane B2 (opposing brief): juniper-canopy PR #670. Verdict: **HOLD**

The replay code under review is `REPLAY_CONTROLS_JS`, byte-identical at c0530279, 29cc9622 and the current worktree. The PR is a clear improvement on `main`, where the pause is undone 3/3. But its central guarantee, "a clientside callback cannot be evicted", is false in dash 4.2.0, and I reproduced a pause that did not hold.

### Reasons, ranked by weight

**1. BLOCKER: a pause clicked during playback can still be dropped. It is the same thing F-054 reports: the pause does not hold.**
- **Mechanism.** It is in dash 4.2.0's `dash_renderer.dev.js`:
  - Clientside callbacks pass through `prioritized`. That queue is capped at 12 slots (`:2846`) and sorted by priority (`:2847`, `:1592-1616`).
  - When a newer request of the same callback arrives, the older copy waiting in `prioritized` is deleted (`pDuplicates`, `:3024`, removed at `:3151`). Its trigger list is **not merged** into the survivor; merging happens only within `requested` (`:3004-3007`).
  - The JS decides what to do from that trigger list (`metrics_panel.py:79-80`). So a click replaced by the next tick's request is never applied.
- **Canopy's own ranking.** `canopy_priority_census.py` scores the controls callback `'11'`. 19 of 141 server callbacks outrank it, including the metrics poll (`'14'`).
- **Clean room.** `pdup_cleanroom.py` runs the PR's real JS with no ports: Playwright serves Dash through Flask's `test_client`. Each arm adds K extra server pollers that tie up renderer slots.

| K (pool full) | 1x dropped | 4x dropped |
|---|---|---|
| 0, 8 (0%) | – | 0/16 |
| 12 (16–18%) | 0/8 | 2/8 |
| 13 (44–46%) | 3/10 | 5/10 |
| 14 (65%) | 0/10 | 7/10 |
| 16 (81–82%) | 5/8 | 6/8 |
| 16, **click-counting variant** | **0/8** | **0/7** |

- **Every one of the 28 drops has the same trace.** The click waited in `prioritized` (0–588 ms), a tick-only request replaced it, and it never ran while playback continued. Example, K=12 4x trial 1:
  - +0.032 s: the click is promoted;
  - +0.069 s: a tick request arrives;
  - +0.074 s: the click is gone;
  - the index runs 22 → 55.
- **Canopy sits in that range.** Its own census (`reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_slots_training_metrics_idle.txt` and `…_slots_replay_click_requested_census.txt`) was taken on the Training Metrics tab at idle, when the replay bar is visible:
  - pool full in 30.0% and 31.9% of samples;
  - `prioritized` up to 25 entries;
  - ten **clientside** callbacks each spent 473–1331 of 5454 samples in `prioritized` (`clientside_check.py` confirms they are clientside).
- **Caveats.** The clean room shows the mechanism, not canopy's drop rate, which is unmeasured. That census was taken on `9bffaba1`, before #657. A dropped click leaves ⏸ showing with playback moving, so a second click recovers. That is milder than F-054's stuck state.

**2. SHOULD-FIX: false absolute claims would enter the records.**
- `metrics_panel.py:1110-1116` says "a tick cannot evict a click", and `:1122` says "now no pending callback can hold them".
- `CHANGELOG.md:65-66` says "nothing is evicted", and `:71` says "Now nothing pending can hold them".
- The docstring of `test_nothing_pending_can_hold_the_replay_controls` (`test_f048_replay_cycle.py:328-332`) says "promoted on the next renderer pass, whatever else is in flight". Being promoted to the queue is not the same as running.
- The ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` says "cannot be evicted" (L7897-7898) and "nothing pending can hold them" (L7944-7946).
- These still stand in the worktree, which another session is editing now (see Notes).

**3. SHOULD-FIX: the evidence is below the bar in `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §3.** Closing a finding with n=3, one session, new instruments and absolute claims puts this in the top-right cell.
- **Live runs.** Only 4 clicks were made during playback, all pauses at 1x (`2026-09-23_f054_live_pause_8055_fix.json` plus one in the redrive). Every speed, step, start, end and slider step in `2026-09-23_f054_replay_block_redrive_8055_settle16.json` was driven while **paused**, so none was exposed to eviction.
- **The PR's clean room** (`util/ad-hoc/2026-09-23_f054_replay_tick_cleanroom.py`) had one server callback, so the pool was never contended. Its `cs_all` row, labelled "this PR", ran a hand-written port (`M_JS`, lines 126-170), not the registered JS.
- **The missed latency prediction** (1.4–2.4 s) was put down to main-thread saturation (ledger L8032-8034). The `prioritized` queue was never instrumented, although `e2e_f027_slots.py` exists for exactly that.
- **Tick counting was never exercised live.** Every live step was +1.

**4. SHOULD-FIX: the smaller fix is already half in the PR.** The PR counts ticks (`tick_n`) because the renderer merges and drops tick triggers, and clicks need the same treatment. My variant is about 15 lines added after `:79`: it records the `n_clicks` values it has consumed and applies any control whose count advanced even when it is missing from `triggered`. It held 15/15 at 81% pool-full, where the PR's JS dropped 11/16. `node_trigger_demo.py` shows the logic: with `triggered=[tick]` and the play count advanced, the PR's JS returns `playing` and the variant returns `paused`.

**5. FOLLOW-UP: other symptoms with the same root cause.**
- A slider seek during playback is exposed the same way; a fix would compare the slider value against the last value written.
- A merged double step-forward applies once, in both the PR and my variant (node demo).
- "Nothing pending can hold them" is true only of the readiness check. A play click at 81% pool-full waited more than 20 s in the queue, which is the F-027 starvation class.

**6. FOLLOW-UP: the slider thumb is not re-rendered on a refill.** The PR concedes this. It shows mainly after a display-mode or window change.

### Checked and not a reason to hold
- **The 60 deleted tests are vacuous, as the PR says.** Recounted: 38 = 25 re-implemented inline + 12 behind an `if func :=` guard + 1 direct lookup, plus 22 inline.
- **CI ran the node tests.** 6627 passed; the 5 skips are unrelated.
- **Merge mechanics are fine.** The `Allow-Symbol-Loss` trailer is in the non-merge commit's last paragraph.
- **Mount and tab rebuilds are safe.** Page load collects callbacks by output only (`:7152`), and a rebuilt layout chunk skips the by-input path (`:6986-6991`), so the callback sees an empty `triggered`.
- **Holding costs little.** The replay drives no chart (ledger Phase 8 item 11).

### Minimal change that would flip this to MERGE
1. Count clicks as ticks are already counted: the #4 variant, plus one node test where the play count advanced but `triggered` names only the tick, expecting `paused`.
2. Rewrite the absolute claims in #2 as the bounded statement: no stale-state computation, but a queued click can be dropped unless counted.
3. Re-verify with the pool contended: 1x and 4x, n ≥ 5, with `prioritized` instrumented.

If the owner prefers to merge now, the minimum is (2), plus recording F-054 as improved rather than fixed and filing the drop as a new finding.

### Notes
- **Another session is working in the canopy worktree.** Its HEAD is now `723ee812`, an unpushed merge not on the PR, with uncommitted docstring and CHANGELOG edits. `metrics_panel.py` is unchanged from c0530279.
- **Side effects of this lane.** One `git fetch origin` in that worktree updated remote-tracking refs only. No tracked files were changed and no live ports were used; canopy was imported with service URLs pointed at 127.0.0.1:9.
- **To reproduce:** `LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python pdup_cleanroom.py --arms k13_4x:13:speed-4x --trials 10 --out x.json`

**Files created**, all in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/6280349a-397b-4e22-9fc5-a32818ed1f58/scratchpad/laneB2/`:
- `pdup_cleanroom.py`, `run1.json`, `run1.log`, `run2.json`, `run2.log`, `smoke.json`
- `canopy_priority_census.py`, `clientside_check.py`
- `node_trigger_demo.py`, `node_trigger_demo_driver.js`
- `pr670.json`, `metrics_panel.diff`, `d_handlers.diff`, `d_helpers.diff`, `d_f048.diff`
- `old_handlers.py`, `old_helpers_cov.py`, `old_f048.py`
- `ci_unit_313.log`, `c0530279_msg.txt`

---
