## Summary

**F-CANOPY-055 (P1): the top status bar never applied a response.** Status, phase, step, hidden units and latency held their layout defaults (`Stopped` / `0` / blank) for the life of every page loaded at the dashboard's current latency, and the Live Dataset Switch could never enable.

`update_unified_status_bar` rode the shared 1 Hz `fast-update-interval` with no guard. dash-renderer drops a response when the same callback is requested again before that response is processed (`wDuplicates`), and the bar's round trip exceeded the period. So the next tick evicted every response.

The feeder's eleven outputs include `live-dataset-switch-button.disabled`: canopy#514 computes F-CANOPY-025's gate inside this feeder, and the button ships `disabled=True`. So F-CANOPY-025's allow arm could not land either.

## The fix

F-CANOPY-035's repair (canopy#613), applied to a fourth writer, as the ledger's F-055 entry recorded:

- **Own lane.** The feeder's only Input is a new `status-bar-interval` (1 s, `STATUS_BAR_POLL_INTERVAL_MS`).
- **Guard.** `running=[(Output('status-bar-interval', 'disabled'), True, False)]` stops that lane's clock while a request is in flight, so the feeder can no longer be re-requested over itself.
- **Registered.** `(status-bar-interval, None)` in `_GATED_POLL_INTERVALS`, so the CAN-000 apply clamp reaches it. It is never tab-gated, so F-CANOPY-053's hazard (a guard's fixed `runningOff` re-enabling a lane the *tab* gate closed) cannot arise. F-027's objection to #657 does not reach it for the same reason.
  - **Two known limits, shared with #613's metrics-store lane and both unmeasured** (round-1 Lane A). The fused gate still writes this lane's `disabled` on every tab or apply change, and `runningOff` is unconditional in `completeJob()`:
    - An Apply that begins while a status request is in flight is outlived by the guard, which re-enables the lane for the rest of that Apply, so the clamp does not hold it.
    - A tab change mid-request re-enables the lane and re-opens the eviction window for that one cycle.
    - My first draft said "the tab gate never writes it". That was wrong.
- **Strand watchdog.** A request that never produces a response (`handleError`, no `completeJob`) leaves the guard holding the lane off. #614's watchdog is now one registration per guarded lane, each with its own `window` clock, so this lane is covered (`STATUS_BAR_STRAND_TIMEOUT_MS`, 30 s) and a strand on one lane never resets the other.
  - **Its margin is thinner than the wire suggests** (round-1 Lane A, by reading). The guard holds the lane until the page has *processed* the response, 4–7 s at p50 on a loaded page, and the watchdog samples only on the 5 s slow lane. So disabled samples taken inside several different requests can add up to 30 s and release one request early, at the cost of one evicted response.
  - It was not observed: 20 of 20 responses applied in the 150 s census. The constant's comment says so.
- `fast-update-interval` keeps one server-side rider, `handle_button_timeout_and_acks`, and its clientside consumers.

**The cost, stated:** the bar now updates at the page's own pace. Measured live, the lane clocked itself at ~7.9 s per request, because the guard releases from `completeJob()`, after the page has processed the response, not when the wire answers. That matches F-CANOPY-035's measured 5.5–7.3 s. Before this change the bar updated never.

## Evidence

**The census, rule unchanged** (juniper-ml `util/ad-hoc/2026-09-23_status_bar_apply_census.py`; idle trio, Training Metrics, GPU browser, one at a time, predictions added to the docstring before each run):

| leg | window | delivered | watched / executed | latency-display changes | bar at the end | verdict |
|---|---|---|---|---|---|---|
| parent `ce78e0de` | 60 s | 30 | 31 / **0** | 0 | `Stopped` · `0` · blank | **NEVER-APPLIES** |
| fix `884d22fb` | 60 s | 7 | 9 / 8 | 7 | `Completed — early stopped` · `76` · `Latency: 5ms` | VOID (< 10 delivered) |
| fix `884d22fb` | 150 s | 20 | 20 / **20** | 19 | `Completed — early stopped` · `76` · `Latency: 5ms` | **APPLIES** |

The server reported `is_running: false`, phase `output`, epoch 76, 68 hidden units: the bar on the fix shows it, and the bar on the parent shows the layout defaults.

**My first prediction for the fix was wrong.** I predicted at least 10 responses in 60 s ("round trip + up to 1 s"). The lane clocked itself at ~8.6 s, and the rule's floor, set for a 1 Hz lane, scored the run VOID. The second run lengthened the window to the period arm's 150 s, with the rule unchanged and the prediction (APPLIES, 12–25 responses) fixed first.

**F-CANOPY-025's allow arm, driven on demo legs** (juniper-ml `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`). A demo-mode canopy runs its own training and holds the experimental flag in process, so this needs no cascor, and the shared trio's fixture was never touched:

| leg (demo mode) | ALLOW (button enabled while flag on + run live) | DENY (after stop) | BAR |
|---|---|---|---|
| fix `884d22fb` | **LANDS**, 13.0 s after page load | **RETURNS**, 7.8 s after the stop | **APPLIES** (`Running`, step advancing 137 → 143; `Stopped` after the stop) |
| parent (`78c057e2`, whose `src/` is `ce78e0de`'s) | LANDS, 19.7 s | RETURNS, 2.7 s | APPLIES |

- **This drive does not discriminate, and its docstring said before it ran that it might not.** The parent landed too.
  - The drive records no latency, so why the parent's 1 Hz feeder got a response through is not measured. The parent's bar sat at its defaults for the first 18.5 s.
  - The legs also ran under unequal load: the parent's demo run was training while the fix leg was driven.
  - "13 s" is a lower bound, measured from after the page opened and the modal cleared.
- **What it does show:** F-CANOPY-025's allow arm lands on the fix, and the deny arm returns.
- **What it adds to F-CANOPY-055:** a parent page *can* apply a response, so the freeze is not universal. The ledger's "F-CANOPY-025 inferred regressed" holds for pages like the trio legs'.
- The discriminating evidence is the census above.

## Tests

- New `src/tests/unit/frontend/test_f055_status_bar_own_lane.py`, on the built app: the feeder's lane, its guard, that nothing else rides the lane, the lane's declaration, its registration, and two premise pins (the mount call; the feeder as the Live Switch gate's only writer).
- `test_poll_gating.py`: the lane joins the independently stated registry. Every strand-watchdog test now runs against both guarded lanes (`TestStatusBarStrandWatchdog` subclasses `TestStrandWatchdog`), and a new test executes the registered watchdog JavaScript under node with a controlled clock. A further test pins the two watchdogs' separate clocks.
- `test_stage2_global_lane.py`: the fast-lane shape pin names one rider.

**Falsified against the parent `ce78e0de`:** 19 of the three files' 94 tests fail and 75 pass. The failures are every lane, guard, registry and status-bar-watchdog test. The two premise pins pass on both. So does the metrics-store watchdog's node test, which is the evidence that turning the watchdog into a per-lane loop kept its behaviour.

**A defect in my own first draft of these tests**, caught by the falsification run: the watchdog subclass read its constant at class-definition time. On the parent that turned `test_poll_gating.py` into a collection error in which none of its assertions ran, the F-CANOPY-029 trap this module's registry import exists to avoid. The constant is now looked up per test.

`src/tests/unit/ src/tests/regression/` (CI's path scope) at the local fix commit: **6823 passed, 4 skipped, 0 failed**, which is the parent's 6806 plus exactly the 17 new tests. Pre-commit is clean on all six files.

## Review

<<REVIEW>>

Evidence of record: juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 8 (F-CANOPY-055) and Phase 9.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
