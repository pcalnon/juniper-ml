#!/usr/bin/env python
"""F-CANOPY-054 -- a late ``replay_tick`` response undoes a pause. A clean room for the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (F-CANOPY-054, Phase 8);
         juniper-canopy src/frontend/components/metrics_panel.py (the replay block, main 2f973ca2)

THE FINDING (ledger Phase 7). ``replay_tick`` (Input ``replay-interval.n_intervals``; State
``replay-state``, ``metrics-store``; an ``allow_duplicate`` writer of ``replay-state``) computes the
next state from the State read when its request was SENT. With the page's delivery latency L at
~5 s and a 1 s tick, a tick request is in flight when the user pauses, and its response -- computed
from pre-click State -- lands after the pause. The ledger recorded two fix directions and one
prohibition: make the tick clientside, or version the state; do NOT fold the tick into the merged
controls callback, because same-identity eviction would drop the ticks.

WHAT THIS SCRIPT TESTS. That recorded direction is incomplete, from a reading of dash 4.2.0's
renderer (``dash_renderer.dev.js``):

* Eviction. The requestedCallbacks observer removes an in-flight (``watched``/``executing``)
  callback whenever a NEW request of the same callback enters ``requested`` (the
  ``wDuplicates``/``eDuplicates`` step, ~:3024-3027; removal ~:3151), and a response whose
  callback is no longer ``watched`` is dropped (executingCallbacks observer, ~:2699).
* The merged controls callback on canopy main has ``replay-state.data`` as an INPUT, so that a
  tick re-renders the slider. A CLIENTSIDE tick writes the state every tick, which re-requests
  the merged callback every tick. If the merged callback is still server-side, every tick evicts
  any click in flight. With L > the tick period, a pause during playback should never apply.
* A clientside callback has no in-flight window a macrotask can enter. ``executeCallback`` fills
  Inputs and State and runs the function synchronously (~:1173-1260, ``handleClientside`` ~:591);
  what follows is a chain of promise resolutions, so it is applied inside the same macrotask's
  microtask checkpoint. A timer tick, a click or a network response is a later macrotask. So the
  prohibition on folding holds for a SERVER-side merged callback and not for a clientside one.
* Readiness. ``getReadyCallbacks`` (~:1633-1665) will not promote a callback while any of its
  INPUTS lies in the downstream closure of a pending callback; State is never checked. A
  clientside controls callback that takes ``metrics-store.data`` as an Input therefore still
  waits on the store's always-pending primary writer; one that takes it as State never waits.

ARMS -- one app, one latency knob L (a server-side sleep in every server callback), four shapes:

  current        canopy main 2f973ca2: server merged controls callback H (Inputs play, slider,
                 state, metrics), server ``replay_tick`` T, server play-label callback.
  cs_tick        the ledger's first direction: T moved clientside, a line-for-line port; H and the
                 label stay server-side.
  cs_all         the proposed fix: ONE clientside callback M is the only writer of the state and
                 handles play, the slider AND the tick, and renders the slider, the position and
                 the label; ``metrics`` is State. A second clientside callback R (Input metrics,
                 State state) re-renders the position text on a refill. No server callback.
  cs_all_input   cs_all with ``metrics`` as an INPUT of M. One variable: tests the readiness claim.

Every arm has the same FEEDER: the primary writer of ``metrics``, a server callback on a 500 ms
Interval, ``running=``-guarded as canopy's metrics poll is, sleeping L. It fills the store once and
then returns ``no_update``, which is canopy's idle behaviour since F-CANOPY-038's suppression; so
it is pending about L / (L + 0.5 s) of the time, and writes nothing after the fill.

SCENARIO, per run: load; wait until the position shows the fill; install a Redux-store
subscription that records every change of the state store's (mode, index) and of
``interval.disabled`` with a wall-clock stamp; click play; wait PLAY_S; click play again (pause);
watch SETTLE_S. The verdict reads the STORE, not the DOM. A DOM-only reading would score cs_tick a
pass: every server refresh of the label and the position is evicted during playback, so the page
freezes on a label of the mount value and a stale position, which looks exactly like a pause.

VERDICT RULE, per run -- FIXED BEFORE THE FIRST RUN.

  PAUSE-HELD      a 'paused' state was applied after the pause click, no 'playing' state was applied
                  after it, the final mode is not 'playing', and the index did not change in the last
                  8 s of the settle.
  F054-UNDONE     a 'paused' state was applied after the click, and a 'playing' state after that.
  CLICK-DROPPED   no 'paused' state was applied within the settle.
  OTHER           anything else.

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (L = 2.5 s, tick 1000 ms, feeder 500 ms, 120 rows,
PLAY_S = 10, SETTLE_S = 16, 3 runs per arm):

  current        F054-UNDONE in 3/3. The index advances by at most 1 during play (each T request is
                 evicted by the next tick before it lands) and by exactly 1 after the pause (the last
                 T is never evicted, because the pause disabled the interval). Final: mode 'playing'
                 with the interval disabled.
  cs_tick        CLICK-DROPPED in 3/3. The index advances 8-10 during play and keeps advancing after
                 the click. The DOM disagrees with the store at the end.
  cs_all         PAUSE-HELD in 3/3; every pause applied within 0.5 s of the click; the largest single
                 index step is 1; the index advances 8-10 during play; the DOM agrees with the store.
  cs_all_input   PAUSE-HELD in 3/3; the median pause latency is above 0.5 s (it waits for the feeder);
                 at least 2 of 3 runs show a single index step of 2 or more (merged ticks caught up by
                 the tick delta); the DOM agrees with the store.

A result that contradicts a prediction is recorded as such, and the explanation is revised, never
the rule.

RUN LOG.
  smoke (1 run, current + cs_all, ``…_SMOKE.json``): the store reader found nothing -- dash 4.2.0
      keeps the layout under ``layout.components``, and the walk followed only ``props.children``
      -- so both arms scored CLICK-DROPPED on an empty series. Not scored. Its DOM reads already
      showed cs_all at ``▶ 10 / 119`` and current at ``⏸ 1 / 119``. Walker replaced by a generic one.
  scored run 1 (aborted): current, run 1 = F054-UNDONE (pause applied at +2.9 s, then undone; 0
      steps during play, +1 after; final playing with the interval disabled). Then the second arm
      tried port 8202, the live cascor leg, and the run died (see ``_free_port``). No JSON written.
  scored run 2: ``2026-09-23_f054_tick_cleanroom_run2.json``, from port 18501.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_replay_tick_cleanroom.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_tick_cleanroom.json
"""

import argparse
import json
import multiprocessing as mp
import statistics
import sys
import time
from pathlib import Path

ROWS = 120
BASE_INTERVAL_MS = 1000
FEEDER_INTERVAL_MS = 500
ARMS = ("current", "cs_tick", "cs_all", "cs_all_input")

# The proposed fix's single controls callback M, written as it is meant to ship in canopy (play and
# the slider only here; canopy adds step, start, end and the three speeds). Its arguments are its
# Inputs then its State, in registration order: play n_clicks, slider value, interval n_intervals,
# then state, metrics.
M_JS = """
function(playClicks, sliderValue, nIntervals, currentState, metricsData) {
    var dc = window.dash_clientside;
    var noUpdate = dc.no_update;
    var ctx = dc.callback_context || {};
    var triggered = (ctx.triggered || []).map(function (t) { return t.prop_id; });
    var maxIndex = (metricsData && metricsData.length) ? metricsData.length - 1 : 0;
    var tickN = (typeof nIntervals === "number") ? nIntervals : 0;
    var state = currentState ? Object.assign({}, currentState) : {mode: "stopped", speed: 1.0, current_index: 0, start_index: 0, end_index: null};
    var controlFired = false;
    var ticked = false;
    for (var k = 0; k < triggered.length; k++) {
        var cid = triggered[k].slice(0, triggered[k].lastIndexOf("."));
        if (cid === "interval") {
            if (state.mode === "playing") {
                var last = (typeof state.tick_n === "number") ? state.tick_n : tickN - 1;
                var steps = Math.max(0, tickN - last);
                var endIndex = state.end_index || maxIndex;
                var next = state.current_index + steps;
                if (next > endIndex) { state.mode = "stopped"; state.current_index = endIndex; } else { state.current_index = next; }
                state.tick_n = tickN;
                ticked = true;
            }
        } else if (cid === "play" || cid === "slider") {
            if (!controlFired) { state.end_index = state.end_index || maxIndex; }
            controlFired = true;
            if (cid === "play") {
                state.mode = (state.mode === "playing") ? "paused" : "playing";
                if (state.mode === "playing") { state.tick_n = tickN; }
            } else {
                var v = (typeof sliderValue === "number") ? sliderValue : 0;
                state.current_index = maxIndex > 0 ? Math.trunc((v / 100) * maxIndex) : 0;
                state.mode = "paused";
            }
        }
    }
    var idx = state.current_index || 0;
    var sliderOut = maxIndex > 0 ? (idx / maxIndex * 100) : 0;
    var position = idx + " / " + maxIndex;
    var label = state.mode === "playing" ? "\\u23f8" : "\\u25b6";
    if (controlFired || ticked) {
        var disabled = state.mode !== "playing";
        var interval = controlFired ? Math.trunc(1000 / state.speed) : noUpdate;
        return [state, disabled, interval, sliderOut, 100, position, label];
    }
    if (triggered.length) { return [noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate, noUpdate]; }
    return [noUpdate, noUpdate, noUpdate, sliderOut, 100, position, label];
}
"""

R_JS = """
function(metricsData, currentState) {
    var maxIndex = (metricsData && metricsData.length) ? metricsData.length - 1 : 0;
    var idx = (currentState && typeof currentState.current_index === "number") ? currentState.current_index : 0;
    return idx + " / " + maxIndex;
}
"""

# A line-for-line port of canopy's server ``replay_tick`` (main 2f973ca2, metrics_panel.py:1065-1079).
T_JS = """
function(nIntervals, state, metricsData) {
    if (!state || state.mode !== "playing") { return state; }
    var s = Object.assign({}, state);
    var maxIndex = (metricsData && metricsData.length) ? metricsData.length - 1 : 0;
    var endIndex = s.end_index || maxIndex;
    var next = s.current_index + 1;
    if (next > endIndex) { s.mode = "stopped"; s.current_index = endIndex; } else { s.current_index = next; }
    return s;
}
"""


def _serve(arm: str, port: int, latency: float) -> None:
    """Run the app. Child process -- never returns."""
    import dash
    from dash import Input, Output, State, dcc, html, no_update

    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Store(id="state", data={"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}),
            dcc.Store(id="metrics", data=[]),
            dcc.Interval(id="feed", interval=FEEDER_INTERVAL_MS, n_intervals=0),
            dcc.Interval(id="interval", interval=BASE_INTERVAL_MS, disabled=True, n_intervals=0),
            html.Button("▶", id="play", n_clicks=0),
            dcc.Slider(id="slider", min=0, max=100, value=0, updatemode="drag"),
            html.Div(id="pos", children="0 / 0"),
        ]
    )

    filled = {"done": False}

    # The feeder: canopy's metrics poll -- the store's PRIMARY writer, running=-guarded, slow, and
    # no_update once the store holds the history (F-CANOPY-038's suppression at idle).
    @app.callback(Output("metrics", "data"), Input("feed", "n_intervals"), running=[(Output("feed", "disabled"), True, False)], prevent_initial_call=True)
    def feeder(n):  # noqa: ARG001
        time.sleep(latency)
        if filled["done"]:
            return no_update
        filled["done"] = True
        return [{"epoch": i} for i in range(ROWS)]

    if arm in ("current", "cs_tick"):
        # H: canopy's merged handle_replay_controls (play + slider subset), server-side.
        @app.callback(
            [
                Output("state", "data"),
                Output("interval", "disabled"),
                Output("interval", "interval"),
                Output("slider", "value"),
                Output("slider", "max"),
                Output("pos", "children"),
            ],
            [Input("play", "n_clicks"), Input("slider", "value"), Input("state", "data"), Input("metrics", "data")],
            prevent_initial_call=False,
        )
        def controls(play_clicks, slider_value, current_state, metrics_data):  # noqa: ARG001
            time.sleep(latency)
            triggered = [t["prop_id"] for t in dash.callback_context.triggered] if dash.callback_context.triggered else []
            fired = [p.rpartition(".")[0] for p in triggered if p.rpartition(".")[0] in ("play", "slider")]
            max_index = len(metrics_data) - 1 if metrics_data else 0
            if fired:
                state = dict(current_state or {"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None})
                state["end_index"] = state.get("end_index") or max_index
                for control in fired:
                    if control == "play":
                        state["mode"] = "paused" if state["mode"] == "playing" else "playing"
                    else:
                        state["current_index"] = int((slider_value / 100) * max_index) if max_index > 0 else 0
                        state["mode"] = "paused"
                out = (state, state["mode"] != "playing", int(BASE_INTERVAL_MS / state["speed"]))
            else:
                state = current_state
                out = (no_update, no_update, no_update)
            idx = state.get("current_index", 0) if state else 0
            return (*out, (idx / max_index * 100) if max_index > 0 else 0, 100, f"{idx} / {max_index}")

        @app.callback(Output("play", "children"), Input("state", "data"), prevent_initial_call=False)
        def label(state):
            time.sleep(latency)
            return "⏸" if state and state.get("mode") == "playing" else "▶"

        if arm == "current":
            # T: canopy's replay_tick, verbatim bar the sleep.
            @app.callback(Output("state", "data", allow_duplicate=True), Input("interval", "n_intervals"), [State("state", "data"), State("metrics", "data")], prevent_initial_call=True)
            def replay_tick(n_intervals, state, metrics_data):  # noqa: ARG001
                time.sleep(latency)
                if not state or state["mode"] != "playing":
                    return state
                max_index = len(metrics_data) - 1 if metrics_data else 0
                end_index = state.get("end_index") or max_index
                new_index = state["current_index"] + 1
                if new_index > end_index:
                    state["mode"] = "stopped"
                    state["current_index"] = end_index
                else:
                    state["current_index"] = new_index
                return state

        else:
            app.clientside_callback(T_JS, Output("state", "data", allow_duplicate=True), Input("interval", "n_intervals"), [State("state", "data"), State("metrics", "data")], prevent_initial_call=True)

    else:
        metrics_dep = Input("metrics", "data") if arm == "cs_all_input" else State("metrics", "data")
        inputs = [Input("play", "n_clicks"), Input("slider", "value"), Input("interval", "n_intervals")]
        states = [State("state", "data")]
        if arm == "cs_all_input":
            inputs.append(metrics_dep)
        else:
            states.append(metrics_dep)
        # With metrics as an Input it is the fourth argument and state the fifth; M_JS takes
        # (play, slider, n, state, metrics), so the Input arm gets a thin reordering wrapper.
        js = M_JS if arm == "cs_all" else "function(p, s, n, metrics, state) { return (" + M_JS.strip() + ")(p, s, n, state, metrics); }"
        app.clientside_callback(
            js,
            [
                Output("state", "data"),
                Output("interval", "disabled"),
                Output("interval", "interval"),
                Output("slider", "value"),
                Output("slider", "max"),
                Output("pos", "children"),
                Output("play", "children"),
            ],
            inputs,
            states,
            prevent_initial_call=False,
        )
        app.clientside_callback(R_JS, Output("pos", "children", allow_duplicate=True), Input("metrics", "data"), State("state", "data"), prevent_initial_call=True)

    app.run(host="127.0.0.1", port=port, debug=False)


FIND_AND_WATCH = """
() => {
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$') || k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  let st = (window.store && typeof window.store.getState === 'function') ? window.store : null;
  if (!st) {
    for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
      const el = document.querySelector(sel);
      if (!el) continue;
      let f = fiberOf(el), hops = 0;
      while (f && hops < 8000 && !st) {
        const mp = f.memoizedProps;
        if (mp && mp.store && typeof mp.store.getState === 'function') st = mp.store;
        f = f.child || f.sibling || (f.return ? f.return.sibling : null);
        hops++;
      }
      if (st) break;
    }
  }
  if (!st) return {found: false};
  // A generic walk of every nested object (the laneA2 walker's rule): the smoke run's walk, which
  // followed only ``props.children``, never found the stores in dash 4.2.0's layout.
  function findProp(node, id, prop) {
    const stack = [node];
    let n = 0;
    while (stack.length && n < 200000) {
      const v = stack.pop();
      n++;
      if (v === null || typeof v !== 'object') continue;
      if (Array.isArray(v)) { for (const c of v) stack.push(c); continue; }
      if (v.props && typeof v.props === 'object' && v.props.id === id && typeof v.type === 'string') return v.props[prop];
      for (const k in v) { const c = v[k]; if (c !== null && typeof c === 'object') stack.push(c); }
    }
    return undefined;
  }
  window.__rec = {series: [], disabled: []};
  let last = null, lastDis = null;
  const sample = () => {
    const lay = st.getState().layout;
    const s = findProp(lay, 'state', 'data');
    const key = s ? (s.mode + '|' + s.current_index) : 'null';
    if (key !== last) { last = key; window.__rec.series.push([Date.now(), s ? s.mode : null, s ? s.current_index : null]); }
    const d = findProp(lay, 'interval', 'disabled');
    if (d !== lastDis) { lastDis = d; window.__rec.disabled.push([Date.now(), d]); }
  };
  sample();
  st.subscribe(sample);
  return {found: true, via: (window.store === st) ? 'window.store' : 'fiber'};
}
"""


def _drive(port: int, play_s: float, settle_s: float) -> dict:
    from playwright.sync_api import sync_playwright

    wire: dict = {}
    obs: dict = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        page = b.new_context().new_page()

        def on_request(req):
            if "_dash-update-component" in req.url:
                out = str((req.post_data_json or {}).get("output") or "")[:60]
                wire[out] = wire.get(out, 0) + 1

        page.on("request", on_request)
        page.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=30000)
        page.wait_for_function(f"() => {{ const e = document.querySelector('#pos'); return e && e.textContent === '0 / {ROWS - 1}'; }}", timeout=30000)
        found = page.evaluate(FIND_AND_WATCH)
        obs["store"] = found
        if not found.get("found"):
            b.close()
            return {"error": "redux store not found", **obs}
        page.wait_for_timeout(2000)

        obs["t_play_before"] = page.evaluate("Date.now()")
        page.click("#play")
        obs["t_play_after"] = page.evaluate("Date.now()")
        page.wait_for_timeout(int(play_s * 1000))

        obs["t_pause_before"] = page.evaluate("Date.now()")
        page.click("#play")
        obs["t_pause_after"] = page.evaluate("Date.now()")
        dom = []
        t_end = time.time() + settle_s
        while time.time() < t_end:
            dom.append([page.evaluate("Date.now()"), page.text_content("#play"), page.text_content("#pos")])
            page.wait_for_timeout(250)
        obs["dom"] = dom
        rec = page.evaluate("window.__rec")
        obs["series"] = rec["series"]
        obs["disabled"] = rec["disabled"]
        b.close()
    obs["wire"] = wire
    return obs


def _score(obs: dict, settle_s: float) -> dict:
    series = obs["series"]
    t_play, t_pause = obs["t_play_before"], obs["t_pause_before"]
    t_end = t_pause + settle_s * 1000
    before_play = [r for r in series if r[0] < t_play]
    i_start = before_play[-1][2] if before_play else 0
    play_window = [r for r in series if t_play <= r[0] < t_pause]
    playing_seen = [r for r in play_window if r[1] == "playing"]
    i_at_pause = play_window[-1][2] if play_window else i_start
    idx_seq = [i_start] + [r[2] for r in play_window]
    steps = [b - a for a, b in zip(idx_seq, idx_seq[1:]) if a is not None and b is not None]
    after = [r for r in series if r[0] >= t_pause]
    paused_at = next((r for r in after if r[1] == "paused"), None)
    playing_after = [r for r in after if paused_at and r[0] > paused_at[0] and r[1] == "playing"]
    final = series[-1]
    last8 = [r for r in series if r[0] >= t_end - 8000]
    idx_const_last8 = len({r[2] for r in last8}) <= 1
    if paused_at and playing_after:
        verdict = "F054-UNDONE"
    elif paused_at is None:
        verdict = "CLICK-DROPPED"
    elif final[1] != "playing" and idx_const_last8:
        verdict = "PAUSE-HELD"
    else:
        verdict = "OTHER"
    dom_last = obs["dom"][-1] if obs["dom"] else [None, None, None]
    exp_label = "⏸" if final[1] == "playing" else "▶"
    return {
        "verdict": verdict,
        "play_latency_ms": (playing_seen[0][0] - t_play) if playing_seen else None,
        "pause_latency_ms": (paused_at[0] - t_pause) if paused_at else None,
        "steps_during_play": (i_at_pause - i_start) if (i_at_pause is not None and i_start is not None) else None,
        "max_step_during_play": max(steps) if steps else 0,
        "index_after_pause_delta": (final[2] - i_at_pause) if (final[2] is not None and i_at_pause is not None) else None,
        "final_mode": final[1],
        "final_index": final[2],
        "final_interval_disabled": obs["disabled"][-1][1] if obs["disabled"] else None,
        "dom_agrees_with_store": dom_last[1] == exp_label and dom_last[2] == f"{final[2]} / {ROWS - 1}",
        "dom_last": dom_last[1:],
    }


def _free_port(port: int) -> int:
    """The first port at or above ``port`` that nothing is listening on.

    The first scored run started at 8201 and its second arm landed on 8202 -- the arc's LIVE cascor
    leg. The app could not bind, and the browser drove cascor's root page instead (a GET, no state
    change). The run died on the ``#pos`` wait; the traceback was hidden by the log filter.
    """
    import socket

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


def _arm(arm: str, port: int, latency: float, play_s: float, settle_s: float) -> dict:
    port = _free_port(port)
    proc = mp.Process(target=_serve, args=(arm, port, latency), daemon=True)
    proc.start()
    time.sleep(4.0)
    try:
        obs = _drive(port, play_s, settle_s)
    finally:
        proc.terminate()
        proc.join(timeout=5)
    if "error" in obs:
        print(f"  [{arm:12s}] ERROR {obs['error']}", flush=True)
        return {"arm": arm, "port": port, **obs}
    sc = _score(obs, settle_s)
    print(
        f"  [{arm:12s}] {sc['verdict']:13s} play_lat={sc['play_latency_ms']} pause_lat={sc['pause_latency_ms']} "
        f"steps_play={sc['steps_during_play']} max_step={sc['max_step_during_play']} after_pause_delta={sc['index_after_pause_delta']} "
        f"final={sc['final_mode']}/{sc['final_index']} disabled={sc['final_interval_disabled']} dom_agrees={sc['dom_agrees_with_store']} dom={sc['dom_last']}",
        flush=True,
    )
    return {"arm": arm, "port": port, "score": sc, "obs": obs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=18501, help="first port to try; ports in use are skipped")
    ap.add_argument("--runs", type=int, default=3, help="runs per arm")
    ap.add_argument("--latency", type=float, default=2.5, help="server-side sleep, seconds, in every server callback")
    ap.add_argument("--play-s", type=float, default=10.0)
    ap.add_argument("--settle-s", type=float, default=16.0)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import dash

    arms = [a for a in args.arms.split(",") if a]
    res = {"probe": Path(__file__).name, "dash": dash.__version__, "latency_s": args.latency, "play_s": args.play_s, "settle_s": args.settle_s, "rows": ROWS, "runs_per_arm": args.runs, "arms": {a: [] for a in arms}}
    print(f"dash {dash.__version__}  L={args.latency}s  play={args.play_s}s  settle={args.settle_s}s", flush=True)
    port = args.port
    for _ in range(args.runs):
        for arm in arms:
            r = _arm(arm, port, args.latency, args.play_s, args.settle_s)
            res["arms"][arm].append(r)
            port = r["port"] + 1

    summary = {}
    for arm in arms:
        scores = [r["score"] for r in res["arms"][arm] if "score" in r]
        verdicts = [s["verdict"] for s in scores]
        lat = [s["pause_latency_ms"] for s in scores if s["pause_latency_ms"] is not None]
        summary[arm] = {
            "verdicts": verdicts,
            "pause_latency_ms_median": statistics.median(lat) if lat else None,
            "pause_latency_ms_max": max(lat) if lat else None,
            "steps_during_play": [s["steps_during_play"] for s in scores],
            "max_step_during_play": [s["max_step_during_play"] for s in scores],
            "index_after_pause_delta": [s["index_after_pause_delta"] for s in scores],
            "dom_agrees_with_store": [s["dom_agrees_with_store"] for s in scores],
        }
    res["summary"] = summary
    print(json.dumps(summary, indent=2), flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(f"results -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
