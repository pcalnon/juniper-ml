#!/usr/bin/env python
"""
F-CANOPY-054 round 2, Lane A2: what `priority` does dash-renderer 4.2.0 actually attach to a queued request?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (executed by Claude Code, consensus Lane A2)
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy#670 (F-CANOPY-054); 2026-09-23_f054_r2_laneA2_slot_contention_pause.py

Why: getPriority (dash_renderer.dev.js :1592-1616) begins each pass with
`callbacks = filter(c => { touched = touchedCbIds[id]; touchedCbIds[id] = true; return touched; }, callbacks)`,
which KEEPS only already-touched callbacks, so the seed is dropped on the first pass and every request should get
"0". Lane B2's census (scratchpad laneB2/canopy_priority_census.py) ports it with the predicate inverted (keeps the
UNtouched ones) and ranks pollers '13' above the replay controls' '11'. This probe reads the value the renderer
actually stores on the request objects (`cb.priority`, set in getCallbacksByInput :1581-1583).

App: button `a` -> callback A (Output store s) -> THREE callbacks (Input s -> Output d0/d1/d2), a fan-out whose
intended-semantics priority would be "13"; button `b` -> callback B (Output div e), no downstream ("0" either way).
Each server callback sleeps 1 s so the requests are observable in the queues.

PREDICTION (before the first run): every observed request carries priority "0", including A's; if A shows "13",
Lane B2's port is right and this file's reading of :1598-1602 is wrong.

Usage: LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python <this> --port 18575
"""

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve()


def serve(port):
    import logging

    import dash
    from dash import Input, Output, dcc, html
    from werkzeug.serving import make_server

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app = dash.Dash("laneA2_priority_probe")
    app.layout = html.Div([html.Button("a", id="a"), html.Button("b", id="b"), dcc.Store(id="s"), html.Div(id="e")] + [html.Div(id=f"d{j}") for j in range(3)])

    @app.callback(Output("s", "data"), Input("a", "n_clicks"), prevent_initial_call=True)
    def cb_a(n):
        time.sleep(1.0)
        return n

    for j in range(3):
        app.callback(Output(f"d{j}", "children"), Input("s", "data"), prevent_initial_call=True)(lambda d, j=j: f"d{j} {d}")

    @app.callback(Output("e", "children"), Input("b", "n_clicks"), prevent_initial_call=True)
    def cb_b(n):
        time.sleep(1.0)
        return n

    make_server("127.0.0.1", port, app.server, threaded=True).serve_forever()


PROBE_JS = r"""
(() => {
  if (window.__PR) { return; }
  const R = window.__PR = {seen: []};
  const h = setInterval(() => {
    if (!window.store) { return; }
    clearInterval(h);
    window.store.subscribe(() => {
      const c = window.store.getState().callbacks;
      for (const L of ['requested', 'prioritized', 'executing', 'watched']) {
        for (const cb of (c[L] || [])) {
          const k = L + '|' + cb.callback.output + '|' + JSON.stringify(cb.priority);
          if (R.seen.indexOf(k) < 0) { R.seen.push(k); }
        }
      }
    });
  }, 2);
})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="run")
    ap.add_argument("--port", type=int, default=18575)
    a = ap.parse_args()
    if a.port < 18500 or a.port in (8051, 8101, 8202):
        sys.exit("refusing port")
    if a.cmd == "serve":
        serve(a.port)
        return
    srv = subprocess.Popen([sys.executable, str(HERE), "serve", "--port", str(a.port)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        from playwright.sync_api import sync_playwright

        time.sleep(3.0)
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            ctx = b.new_context()
            ctx.add_init_script(PROBE_JS)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{a.port}/", wait_until="load")
            page.wait_for_function("() => window.store && window.__PR", timeout=15000)
            time.sleep(0.5)
            page.click("#a")
            page.click("#b")
            time.sleep(2.5)
            seen = page.evaluate("() => window.__PR.seen")
            b.close()
        print(json.dumps(seen, indent=1))
        prios = sorted({s.rsplit("|", 1)[1] for s in seen})
        print("distinct priorities observed:", prios)
    finally:
        srv.terminate()


if __name__ == "__main__":
    main()
