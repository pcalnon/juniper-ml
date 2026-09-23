<!-- markdownlint-disable -->

# Canopy E2E arc — validator reports, 2026-09-22 (verbatim)

Archived by `util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py` from the session's subagent
transcripts. Each section is the agent's final report exactly as delivered; they are EVIDENCE for
Phase 7 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, not conclusions — the
reconciliation, including where a report was itself corrected, is in that phase.

## Lane A — F-CANOPY-038 closure and M-METRICS-18 (FAIL vs BLOCKED)

*agent `a2c155c213f8dc626` · last-assistant-text · 8097 chars*

## Lane A report: F-CANOPY-038 and M-METRICS-18

Both claims reproduce. F-CANOPY-038's no-op suppression now fires at idle, and M-METRICS-18 should be scored **FAIL on F-CANOPY-048**, not BLOCKED.

Every run was against canopy `9bffaba1` on `:8051`, before and after. That checkout has no uncommitted changes and the process started after its last source write. I did not touch cascor and did not modify canopy. The only browser-side change was setting `localStorage.juniper_canopy_welcomed=1` in my own browser context, which is exactly what the welcome dialog's "Get Started" button does. The page did get the host GPU: WebGL2 through ANGLE on an RTX 2080. The metrics history stayed at 95 rows (sha `92e4bfae…`) throughout: 57 of my own reads of `/api/metrics/history`, none failed.

### Claim 1: F-CANOPY-038 — REPRODUCED
- **Counts (two 90 s idle runs, identical results):** the REST poll (`metrics-panel-metrics-store.data`) got 11 responses: 1 carried (the first fill, 95 rows) and 10 `no_update`. The first 60 s after the tab was active held 7 (1 + 6). The steady rate is about one poll per 7 s, roughly 8.4 per 60 s, which matches the orchestrator's 8.
- **Other writer:** the WS-append writer (`…store.data@15586d…`) sent 0 requests. Nothing was unparseable, and only one distinct payload was carried.
- **Branch attribution:** every `no_update` request carried `ws_live=False`, window mode, and a `State` equal (Python `==`) to the handler's own fetch. That leaves only the Stage 2 branch (`dashboard_manager.py:7618`). The canopy log has zero fetch-error warnings, and other `frontend.*` log lines do reach it, so the error branches were not taken.
- **Source:** the condition is `isinstance(current_metrics, list) and metrics == current_metrics`, compared against `State("metrics-panel-metrics-store","data")`. That block is unchanged since canopy#511. What changed is its `State` operand: it was `[]` in the 08-29 probe and is now the full 95-row list. canopy#613 is an ancestor of `9bffaba1`; I did not bisect.
- **Positive control, and whether the opposite answer was possible:** it was. Changing the window size from 500 to 10 produced a second carried write (10 rows), then 5 `no_update` on the new value. The client copy moved `[]` → 95 → 10 rows, and a second instrument (the renderer's own redux store) agreed with the request `State` at all four snapshots. A dead suppression would have shown every poll carried with `State []`.
- **Wording I would accept:** "FIXED (behaviour), attributed to canopy#613, verified live on canopy 9bffaba1 at idle, two runs: 1 carried + 10 `no_update` per 90 s, every `no_update` in the Stage 2 branch; no change to the suppression itself."
- **Two caveats for that wording:**
  - The title's second clause is still true. `test_metrics_identical_fetch_is_no_update` still compares in-process objects, and no browser-level test pins this behaviour. Carry it as a test-gap follow-up.
  - Only idle was measured.

### Claim 2: M-METRICS-18 — REPRODUCED; FAIL is the honest verdict
- **The row's expected result:** "Maps 0-100 → index, mode `paused` (`:1030-1032`)". The citation has drifted; the slider branch is now `metrics_panel.py:1036`.
- **Prerequisite met:** the client store held 95 rows. I read that from request `State` and the renderer store, not from the position text.
- **What happened:**
  - Ten ArrowRight presses and then a real mouse drag moved the slider's own value from 0 to 10 to 41, in both the DOM and the renderer's props.
  - The position text stayed `0 / 0` the whole time. The play button kept the play icon (U+25B6) and never showed pause.
  - Of 559 and 602 captured requests (two runs), **0 named `metrics-panel-replay-state`** in any role. So there were no writes from `handle_replay_controls` or `replay_tick`, and no dispatch of `update_replay_ui` or `update_play_button`.
- **Why nothing reached the wire:** the renderer's queue shows `handle_replay_controls` entering `callbacks.requested` after the first key press and staying there for more than 160 s: never prioritized, never executed. `update_replay_ui` and `update_play_button` sit in `requested` from page load. That fits F-048's "claimed-Input promotion block" hypothesis. The specific cycle explanation (slider value → replay state → slider value) is my inference from the renderer's source and belongs to Lane B.
- **What the server would have returned:** called directly, the same callback gives, for slider 10 on 95 rows, mode `paused`, `current_index` 9 and position `9 / 94`. For play it gives `playing` with the replay interval enabled. The fill alone should already show `0 / 94`, so the replay UI is dead from page load, before any gesture.
- **Positive control, and whether the opposite answer was possible:** it was. The display-mode radio (M-METRICS-19) on the same page dispatched, returned 200 with its write, and hid then re-showed the window-size box within 1–2 s, in both runs.
- **Why not BLOCKED:** the plan's §9 defines BLOCKED as "could not be exercised because a prerequisite failed". Here the row was exercised: the gesture landed and the slider's own callback never ran.
- **Wording I would accept:** "FAIL (F-CANOPY-048): with the store at 95 rows, keyboard and drag moved the slider 0→10→41, but `handle_replay_controls` sat in the renderer's `requested` queue and was never dispatched; position stayed `0 / 0` (expected `9 / 94`, then `38 / 94`)."

### What was false or misleading in the prompt
- **"Current main":** `origin/main` is now `886147b5` (canopy#656). That commit only touches the dataset-availability gate, so the verdicts stand, but the evidence is for `9bffaba1`.
- **Readiness check:** "check the position text's denominator" is circular. That text is written by `update_replay_ui`, which never runs, so it reads `0 / 0` with 95 rows in the store. Using it recreates the stale BLOCKED-by-F-035 verdict.
- **Slider selector:** `.rc-slider-handle` does not exist in Dash 4.2's slider; the handle is `.dash-slider-thumb[role=slider]`.
- **Omitted:** a fresh browser context opens a "Welcome to Juniper Canopy" dialog that blocks every click; my first tab click timed out on it. Also, Training Metrics is already the active tab by default and has no `aria-selected` attribute.
- **Store size:** the store held 95 rows, not 80; the fixture has moved on since the orchestrator's runs.
- **Ledger error (not in the prompt):** the 2026-09-08 section "F-CANOPY-038 re-measured" in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` says the Stage 2 rule is "absent from `_update_metrics_store_handler`". It is present at `:7618` and has never been removed. The same finding entry's `:6724-6725` citations are stale.

Documents referenced: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (§2), `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (the ledger), `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` (the matrix row), and `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (§9, the status definitions).

**Changed:** no documents. I created the script and seven artifacts below; nothing is committed. Two notes on the artifacts:
- Earlier artifacts record older script hashes because I edited the script between runs.
- Claim 2 run 1 has one bad derived field: its `store_ready` snapshot shows `State_len=0`, from a bookkeeping race in my script. I fixed it before run 2. The run's observables are unaffected.

Files are in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/lively-humming-pixel`:
- `util/ad-hoc/2026-09-22_laneA_f038_m18_check.py`
- `reports/e2e-canopy-2026-09-02/transcripts/`
  - `2026-09-22_laneA_f038_m18_deps.json`
  - `2026-09-22_laneA_f038_m18_modal_probe.json`
  - `2026-09-22_laneA_f038_m18_claim1_idle_run1.json`
  - `2026-09-22_laneA_f038_m18_claim1_idle_run2_redux.json`
  - `2026-09-22_laneA_f038_m18_claim2_replay_run1.json`
  - `2026-09-22_laneA_f038_m18_claim2_replay_run2_redux.json`
  - `2026-09-22_laneA_f038_m18_server_eval.json`

---

## Lane B — juniper-cascor#674 adversarial code review

*agent `a0c13d95b3cf0a6fc` · last-assistant-text · 9861 chars*

I finished the review of juniper-cascor PR #674 (head `7cfad9fc`). My recommendation is **merge after a change**. The fix does what the ledger asks, but the background close logs a false ERROR on Python 3.14, and two claims in the PR body are not true on the stack Docker actually runs.

**Which stack I tested on.** The Dockerfile installs `requirements-cpu.lock`: uvicorn 0.53.0, websockets 17.1, starlette 1.6.0, fastapi 0.141.1, on `python:3.14-slim`. There `ws="auto"` selects uvicorn's newer sansio websocket implementation. The local `JuniperCascor1` env (uvicorn 0.46, websockets 16) selects the older legacy implementation. The PR's probe, and its reasoning about how a close behaves when cancelled, cover only the legacy one. I ran everything on both.

The PR's own probe passes on both stacks. I also built a real slow client that stops reading, and ran it on both stacks. On one extracted copy of the PR tree I tested one candidate fix, and on a second copy a candidate fix plus a `training_stream.py` change.

### Per item

**1. Closing a subscriber whose send timed out — RISK, not a regression.**
- On `main` a timed-out subscriber was forgotten forever and left half-open, so a close with code 1011 is strictly better.
- A timeout is hard to trigger. The first one needed about 9 MB of unread backlog: 467 broadcasts of 20 KB random payload over loopback. With compressible payloads, 3,000 broadcasts of 20 KB never tripped it.
- Reconnecting is expensive for canopy:
  - cascor-client 0.8.0 never sends a `resume` frame (`ws_client.py:335-411`). Every reconnect waits 5 s in the pending state (`settings.py:51` → `training_stream.py:257,261`). Broadcasts in that window are never delivered and never replayed.
  - Then cascor resends `initial_status`, `state` and a burst of up to 100 metrics.
- A persistently slow relay could therefore cycle roughly every 5.5 s. canopy's `_relay_loop` resets its backoff to a 0.5 s floor after every successful connect, and nothing in it branches on the close code.
- One plausible cause of slowness in canopy: the relay awaits `extract_network_topology` inline on every `cascade_add` and does not read the socket meanwhile.
- The broadcast that drops a subscriber now takes about 1.0 s instead of 0.5 s (measured), and the closes run one after another (`manager.py:836-837`). The training thread is not blocked.
- Connection caps are fine: `disconnect()` (`manager.py:835` → `536-538`) releases the per-IP and global slots before the close starts.

**2. Background close tasks — DEFECT (low severity, but visible to operators).**
- Garbage collection is fine: the task is held in `_pending_closes` (`:174`, `:866`). Its exception is retrieved (`:875-879`), and shutdown cancellation is handled.
- The defect is `manager.py:869`, `wait_for(asyncio.shield(closing))`. On Python 3.14, when the wait times out, `shield()` attaches its own exception logger to the close task (CPython `asyncio/tasks.py:914-929`, `:994-999`).
- If that close later fails, asyncio logs **`ERROR asyncio - WebSocketDisconnect exception in shielded future`** with a long traceback. `_close_finished` retrieving the exception does not suppress it.
- Scenario: a slow subscriber is dropped, then its peer resets before the backlog drains, for example because canopy restarts. This reproduced on both stacks.
- The PR's tests miss it: the stalled close is always released successfully, and the failing close fails before the timeout.
- **Fix:** replace it with `done, _ = await asyncio.wait({closing}, timeout=...)`, which neither cancels nor shields the close. With that change the PR's 17 tests all pass under `-W error`, and the ERROR count drops to 0 in all runs.
- Secondary point: on the sansio stack a close to a peer that never reads waits indefinitely in `await self.writable.wait()` (`websockets_sansio_impl.py:433`). uvicorn's 10 s close timer only starts once the frame is written (`:520`). So the docstring's "finishes in the background under the server's own close timeout" (`manager.py:850-852`) is false there. I observed the task still pending at 47 s; the legacy stack gave up after about 30 s. This is not a regression, since `main` held such a peer forever.

**3. Serialisation check — cost and equivalence CLEAR; one undisclosed behaviour change (RISK).**
- Cost: one extra serialisation per broadcast, which is +20% with two subscribers. Measured: 14.6 µs for a 543 B metrics frame and 1.17 ms for a 42 KB topology, the same cost as each existing `json.dumps`.
- It uses the same serialiser as Starlette's `send_json` (`json.dumps` with `separators=(",",":"), ensure_ascii=False`, `websockets.py:174`, byte-identical in 1.0.0 and 1.6.0). It also does the UTF-8 encode that both uvicorn implementations do.
- No race with the training thread: the message builders deep-copy through pydantic `model_dump` (verified), and the interpreter is a standard GIL build.
- The behaviour change: the check (`:823`) runs before chunking. On `main`, a message over 60,000 bytes containing a NumPy scalar or a lone surrogate was still delivered, because the chunker coerces with `json.dumps(default=str)` (`:760`). On a real server, `main` delivered 4 chunks for each such message and the PR refuses both.
- No current producer is affected: `get_topology` emits native types (`lifecycle/manager.py:4700-4715`). But the PR body's "refuses nothing Starlette accepts" should note this.

**4. `send_personal_message` returning False — CLEAR.**
- There are 8 callers, all in `training_stream.py` (98, 103, 120, 339, 353, 368, 381, 392), and every one ignores the return value.
- `main` also returned False here, so the body's "not a vacuous True" is inaccurate but changes nothing.

**5. `training_stream.py` receive-loop change — CLEAR on the questions asked; DEFECT against the PR's "receives close 1011" claim.**
- `:189-190` catches nothing; it is a state check. A peer-initiated close still arrives as `WebSocketDisconnect`.
- The defect is on the sansio stack. If the dropped peer sends any frame while its close is still waiting on `writable`, the loop returns. For example, its auto-pong to a heartbeat ping that was queued in the backlog.
- uvicorn then closes the transport before the close frame is written (`sansio:421-422`). The peer sees **1006, not 1011**, and item 2's ERROR fires. This reproduced on sansio; legacy delivers 1011.
- `main`'s `RuntimeError` exit would behave the same, so it is not a regression, and the peer still gets a TCP close, so it is not half-open.
- Candidate fix (probe-tested only, not run through the unit tier): after the server has started the close, keep calling `websocket.receive()` until the `websocket.disconnect` arrives. That gives 1011 on both stacks and no ERROR.

**6. Metric naming and registration — CLEAR.**
- `observability.py:569-574` registers the counter through `juniper_observability.register_or_reuse`, which adopts the existing collector on a "Duplicated timeseries" (`prometheus_helpers.py:94-110`). Registration happens under `_ws_metrics_lock`, so a double import cannot raise.
- The helper at `:685-693` mirrors `ws_inc_broadcast_timeout`, and the call site is wrapped defensively (`manager.py:730-735`).
- Already disclosed in the PR: the juniper-ml metrics catalogue does not list the new metric.

**7. Thread safety — CLEAR.**
- The new counter is updated under `_seq_lock` (`:716-717`) and read under it (`:1105-1110`). `_pending_closes` is only touched on the event loop.
- Minor noise: a concurrent broadcast that took its subscriber snapshot before the drop now gets Starlette's "Cannot call send once a close message has been sent". That adds an extra WARNING and an extra `send_failures` count.

**8. Does it close F-CASCOR-004 as the ledger defines it? — CLEAR on both halves, with a scope RISK.**
- The WARNING is in `_send_json` (`:982-988`), and the close is in the drop path (`:834-837` → `839-873`).
- The same swallow-and-forget pattern survives elsewhere:
  - juniper-ml's shared `juniper-service-core/juniper_service_core/websocket/manager.py:445-460, 503-519` has the silent `except` and no close. No service uses it today, but it is the extraction target, so a migration would bring the defect back.
  - canopy's browser-facing manager (`src/communication/websocket_manager.py:761-762`; `disconnect()` at `:561`) also forgets clients without closing them.
- The ledger's "`send_failures` is the one to read" will be stale once this merges; the PR discloses that.

### Recommendation
Merge after one required change, plus two smaller ones:
1. **Required:** replace `wait_for(shield(...))` at `manager.py:868-873` with `asyncio.wait({closing}, timeout=...)`. It is tested as described in item 2.
2. **Same PR:** correct the "receives 1011" and "server's own close timeout" claims for the sansio stack, or adopt the item 5 receive change. Also disclose the oversized-message change from item 3 and note that the probe only ran on the legacy stack.
3. **Follow-up findings:** the service-core and canopy manager copies of the same pattern.

**Documents referenced:** `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (§2 Lane B) and `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (the F-CASCOR-004 and F-CANOPY-049 entries). **Changed:** none. I made no pushes, comments or repo edits.

The evidence scripts and outputs are in the session scratchpad, which is under `/tmp` and will be reaped. Copy them to `juniper-ml/util/ad-hoc/` if you want to keep them; my brief was read-only, so I did not. They are `slow_consumer_probe.py`, `flow_diag2.py`, `oversize_parity.py`, `laneB-674/facts.sh`, the `pr674_fix/` and `pr674_fix2/` trees, and the `*.txt` outputs, all under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2a1ec942-45a0-42ee-a732-5e977907ca7a/scratchpad/`.

---
