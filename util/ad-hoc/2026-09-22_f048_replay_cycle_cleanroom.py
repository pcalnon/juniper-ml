#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-048 -- does a two-callback CYCLE deadlock the replay block? A clean room.

THE OBSERVATION (2026-09-22, canopy main 9bffaba1, two re-drives plus one intervention):
with the metrics store FULL (80 rows), no replay control ever dispatched its handler.
The server-side census saw ZERO responses writing ``metrics-panel-replay-state`` across
ten clicks, and the position text never left ``0 / 0``. So ``update_replay_ui`` never
applied the fill either. Parking the metrics poll (``interval`` = 1e9 ms, verified
stopped) did NOT unblock it, which is evidence against the "claimed-Input promotion
block by the metrics poll" hypothesis on record.

THE HYPOTHESIS, from source (juniper-canopy ``src/frontend/components/metrics_panel.py``):

  update_replay_ui        Input  replay-state.data   -> Output replay-slider.value
  handle_replay_controls  Input  replay-slider.value -> Output replay-state.data

That is a CYCLE across two callbacks. dash-renderer's ``getReadyCallbacks`` will not
promote a ``requested`` callback while any of its Inputs is an Output claimed by another
pending callback. If both ever sit in ``requested`` together, each holds the other's
Input and neither is ever ready. Canopy runs with ``debug=False``, so the dev-tools
"Circular Dependencies" check that would flag this at load never runs.

This is a HYPOTHESIS until this experiment says otherwise. Handoff trap 11: "an
inconvenient result invites an invented mechanism -- the next step is a measurement,
not a story." Same dash, same env, no canopy, two arms, one variable:

  --mode cycle     B (the controls) takes the slider value as an INPUT: canopy's shape.
  --mode acyclic   identical, except B takes the slider value as STATE, which breaks the
                   cycle and nothing else.

Both arms fill the data store once, 2 s after load, as canopy's metrics store fills
during page load. Each arm then clicks play three times.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.

  CYCLE-DEADLOCKS   cycle: zero B requests on the wire after the clicks AND the position
                    never shows the fill; acyclic: B dispatched and its write applied
                    (the play label toggled). The cycle alone reproduces F-CANOPY-048's
                    signature.
  NO-DEADLOCK       cycle: B dispatched at least once and applied. The cycle is not
                    sufficient; the hypothesis is wrong or incomplete.
  BOTH-DEAD         acyclic also failed. The clean room does not isolate the cycle,
                    and says nothing.
  INDETERMINATE     anything else, e.g. B dispatched but never applied.

RESULT OF THE FIRST RUN (no feeder): NO-DEADLOCK, 2 of 2 in both arms. The cycle alone does
not lock. The data store in that run was a ONE-SHOT fill, pending for a moment.

SECOND HYPOTHESIS (--feeder), from dash_renderer.dev.js ``getReadyCallbacks`` (~:1633) and
``getAllSubsequentOutputsForCallback`` (~:1617). A requested callback is ready only when none
of its Inputs lies in the TRANSITIVE downstream closure of any pending callback, and
``pendingCallbacks`` includes ``requested`` itself (~:3827). A feeder that is ALWAYS pending
(canopy: the metrics-store poll, and the fast-lane WS drain that feeds the metrics store
through ``append_ws_metrics_store``) has a closure that runs
data -> A -> slider.value -> B -> state.data. With the cycle, that closure covers EVERY
Input of the block, so the controls (B) and the play label wait on the feeder forever.
Without the cycle, the closure stops at A, and only A waits.

  --feeder   adds, to BOTH arms, an Interval(1000 ms) whose callback sleeps 1.5 s and rewrites
             ``data``: pending essentially always.

CORRECTED 2026-09-22 BY LANE B (the RESULT stands, this EXPLANATION does not). The feeder writes
``data.data`` with ``allow_duplicate=True``. Dash appends ``@<sha256>`` to that output's PROPERTY
(``dash/_utils.py:159-163``), and the renderer keeps the suffix (``splitIdAndProp`` :5895,
``combineIdAndProp`` :1539). So this feeder's readiness closure is ``{data.data@<hash>}`` and reaches
NOTHING: it is not "upstream of the block". What it does is stay pending at every pass, and that alone
starves the cycle breaker. The acyclic arm's A applying the fill in 7/7 feeder runs is impossible under
the paragraph above and expected under this one. Lane B's 30 discriminating runs
(``2026-09-22_f048_laneB_variants.py``; predictions fixed before the first run, all 30 matched):
  - a PRIMARY writer of an UNRELATED store, always pending, locks the cycle 2/2;
  - a primary writer of ``data``, always pending, also blocks A's fill even without the cycle;
  - a GAPPED feeder (0.2 s) of either kind locks nothing, 4/4.
The lock needs the two-callback cycle AND some callback pending at every renderer pass.

VERDICT RULE (--feeder) -- FIXED BEFORE ITS FIRST RUN, computed separately from the rule above.

  FEEDER-CYCLE-LOCK   cycle: zero B requests after the clicks AND the label never toggled;
                      acyclic: B requested after the clicks AND the label toggled at least once.
  NO-LOCK             cycle: B requested after the clicks AND the label toggled.
  BOTH-DEAD           acyclic: no B request after the clicks, or the label never toggled.
  INDETERMINATE       anything else.

RULE v1 WAS MIS-SPECIFIED, AND ITS FIRST RUN IS RECORDED AS INDETERMINATE
(``2026-09-22_f048_cycle_cleanroom_feeder.json``). "The label toggled" was tested as "the label
ever shows ⏸". In the cycle arm, B ran ONCE AT MOUNT, triggered by A's mount write to the slider,
so the label read ⏸ before any click and stayed there. The raw observations were 0 B requests
after the clicks, a label constant across the clicks, and a position that never showed the fill,
in 2/2 cycle runs against 2/2 live acyclic runs; the verdict under the rule as written was still
INDETERMINATE. That run is not re-scored.

VERDICT RULE v2 (--feeder) -- FIXED BEFORE ITS FIRST RUN. A run RESPONDED when B was requested
after the clicks AND the label sequence [label_before] + labels_after_clicks changes at least once.
  FEEDER-CYCLE-LOCK   no cycle run responded AND every acyclic run responded.
  NO-LOCK             some cycle run responded.
  BOTH-DEAD           some acyclic run did not respond.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-22_f048_replay_cycle_cleanroom.py [--feeder] \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_f048_cycle_cleanroom.json
"""

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

ROWS = 80


def _serve(mode: str, port: int, feeder: bool = False) -> None:
    """Run the app. Child process -- never returns."""
    import dash
    from dash import Input, Output, State, dcc, html

    app = dash.Dash(__name__)
    children = [
        dcc.Store(id="state", data={"mode": "stopped", "i": 0}),
        dcc.Store(id="data", data=[]),
        dcc.Interval(id="fill", interval=2000, n_intervals=0, max_intervals=1),
        dcc.Slider(id="slider", min=0, max=100, value=0),
        html.Div(id="pos", children="0 / 0"),
        html.Button("▶", id="play", n_clicks=0),
    ]
    if feeder:
        children.append(dcc.Interval(id="feed-tick", interval=1000, n_intervals=0))
    app.layout = html.Div(children)

    @app.callback(Output("data", "data"), Input("fill", "n_intervals"), prevent_initial_call=True)
    def fill(n):  # noqa: ARG001
        return list(range(ROWS))

    if feeder:
        # Canopy's always-pending upstream: a poll whose round trip covers its period.
        @app.callback(Output("data", "data", allow_duplicate=True), Input("feed-tick", "n_intervals"), prevent_initial_call=True)
        def feed(n):
            time.sleep(1.5)
            return list(range(ROWS + (n % 2)))

    # A -- canopy's update_replay_ui: state + data in, slider value + position text out.
    @app.callback(
        [Output("slider", "value"), Output("pos", "children")],
        [Input("state", "data"), Input("data", "data")],
        prevent_initial_call=False,
    )
    def ui(state, data):
        mx = len(data) - 1 if data else 0
        i = (state or {}).get("i", 0)
        return ((i / mx * 100) if mx > 0 else 0), f"{i} / {mx}"

    # B -- canopy's handle_replay_controls: clicks (+ the slider) in, state out.
    slider_dep = Input("slider", "value") if mode == "cycle" else State("slider", "value")

    @app.callback(
        Output("state", "data"),
        [Input("play", "n_clicks"), slider_dep],
        [State("state", "data"), State("data", "data")],
        prevent_initial_call=True,
    )
    def controls(n, slider_value, state, data):  # noqa: ARG001
        st = dict(state or {"mode": "stopped", "i": 0})
        st["mode"] = "paused" if st.get("mode") == "playing" else "playing"
        return st

    @app.callback(Output("play", "children"), Input("state", "data"), prevent_initial_call=False)
    def label(state):
        return "⏸" if (state or {}).get("mode") == "playing" else "▶"

    app.run(host="127.0.0.1", port=port, debug=False)


def _drive(port: int) -> dict:
    from playwright.sync_api import sync_playwright

    wire = {"B_requests": 0, "B_responses": 0, "A_requests": 0}
    console: list = []
    obs: dict = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        page = b.new_context().new_page()

        def on_request(req):
            if "_dash-update-component" not in req.url:
                return
            out = str((req.post_data_json or {}).get("output") or "")
            if out == "state.data":
                wire["B_requests"] += 1
            if "pos.children" in out:
                wire["A_requests"] += 1

        def on_response(resp):
            if "_dash-update-component" in resp.url and str((resp.request.post_data_json or {}).get("output") or "") == "state.data":
                wire["B_responses"] += 1

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", lambda m: console.append(f"{m.type}: {m.text[:200]}") if m.type in ("error", "warning") else None)
        page.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=30000)
        page.wait_for_selector("#pos", timeout=15000)
        page.wait_for_timeout(6000)  # the fill lands at ~2 s
        obs["pos_after_fill"] = page.text_content("#pos")
        obs["label_before"] = page.text_content("#play")
        b_before = wire["B_requests"]
        labels = []
        for _ in range(3):
            page.click("#play")
            page.wait_for_timeout(3000)
            labels.append(page.text_content("#play"))
        obs["labels_after_clicks"] = labels
        obs["pos_end"] = page.text_content("#pos")
        obs["B_requests_after_clicks"] = wire["B_requests"] - b_before
        b.close()
    obs.update(wire)
    obs["console"] = console[:20]
    return obs


def _arm(mode: str, port: int, feeder: bool = False) -> dict:
    proc = mp.Process(target=_serve, args=(mode, port, feeder), daemon=True)
    proc.start()
    time.sleep(4.0)
    try:
        res = _drive(port)
    finally:
        proc.terminate()
        proc.join(timeout=5)
    res.update({"mode": mode, "port": port})
    print(f"  [{mode:7s}] pos_after_fill={res['pos_after_fill']!r} labels={res['labels_after_clicks']} "
          f"B_requests_after_clicks={res['B_requests_after_clicks']} B_responses={res['B_responses']} A_requests={res['A_requests']}", flush=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8063)
    ap.add_argument("--runs", type=int, default=2, help="runs per arm")
    ap.add_argument("--out", required=True)
    ap.add_argument("--feeder", action="store_true", help="add an always-pending upstream feeder of the data store (second hypothesis)")
    args = ap.parse_args()

    import dash

    res = {"probe": Path(__file__).name, "dash": dash.__version__, "runs_per_arm": args.runs, "feeder": args.feeder, "arms": {"cycle": [], "acyclic": []}}
    print(f"dash {dash.__version__}  feeder={args.feeder}", flush=True)
    port = args.port
    for _ in range(args.runs):
        for mode in ("cycle", "acyclic"):
            res["arms"][mode].append(_arm(mode, port, args.feeder))
            port += 1

    if args.feeder:
        def b_ran(r):
            return r["B_requests_after_clicks"] > 0

        def toggled(r):
            return any(lbl == "⏸" for lbl in r["labels_after_clicks"])

        cyc, acy = res["arms"]["cycle"], res["arms"]["acyclic"]
        if not all(b_ran(r) and toggled(r) for r in acy):
            verdict = "BOTH-DEAD"
        elif all((not b_ran(r)) and (not toggled(r)) for r in cyc):
            verdict = "FEEDER-CYCLE-LOCK"
        elif any(b_ran(r) and toggled(r) for r in cyc):
            verdict = "NO-LOCK"
        else:
            verdict = "INDETERMINATE"
        res["verdict"] = verdict
        print(f"=> VERDICT (feeder rule v1, mis-specified -- see docstring): {verdict}", flush=True)

        def responded(r):
            seq = [r["label_before"]] + list(r["labels_after_clicks"])
            return r["B_requests_after_clicks"] > 0 and any(a != b for a, b in zip(seq, seq[1:]))

        if not all(responded(r) for r in acy):
            v2 = "BOTH-DEAD"
        elif not any(responded(r) for r in cyc):
            v2 = "FEEDER-CYCLE-LOCK"
        else:
            v2 = "NO-LOCK"
        res["verdict_v2"] = v2
        print(f"=> VERDICT (feeder rule v2): {v2}", flush=True)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
        print(f"results -> {args.out}", flush=True)
        return 0

    def dead(r):
        return r["B_requests_after_clicks"] == 0 and r["pos_after_fill"] != f"0 / {ROWS - 1}"

    def live(r):
        return r["B_requests_after_clicks"] > 0 and any(lbl == "⏸" for lbl in r["labels_after_clicks"])

    cyc, acy = res["arms"]["cycle"], res["arms"]["acyclic"]
    if not all(live(r) for r in acy):
        verdict = "BOTH-DEAD"
    elif all(dead(r) for r in cyc):
        verdict = "CYCLE-DEADLOCKS"
    elif any(live(r) for r in cyc):
        verdict = "NO-DEADLOCK"
    else:
        verdict = "INDETERMINATE"
    res["verdict"] = verdict
    print(f"=> VERDICT: {verdict}", flush=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(f"results -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
