# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 1, Lane B1: the synthetic app for F-CANOPY-058's second-Input trigger.
# Source: session ddf7847c's tmpfs scratchpad, f058repro.6JTgea/app.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Synthetic repro (Lane B1 review scratch, not repository content).

Mirrors canopy main e9053227's metrics-store wiring (dashboard_manager.py:4710-4717):
a 1 s lane Interval with a running= guard on its own disabled prop, a server feeder whose
Inputs are the lane's n_intervals AND a second Store (the display-mode store), and a
feeder whose response always carries new data (so an apply is observable).

Question: does a mid-request change of the SECOND Input (not a re-enable) start the same
eviction cascade F-CANOPY-058 describes for re-enables?
"""
import sys
import time

import dash
from dash import Input, Output, dcc, html

R = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9471

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        dcc.Interval(id="lane", interval=1000, n_intervals=0),
        dcc.Store(id="mode", data={"mode": "window"}),
        html.Div(id="out", children="init"),
    ]
)


@app.callback(
    Output("out", "children"),
    Input("lane", "n_intervals"),
    Input("mode", "data"),
    running=[(Output("lane", "disabled"), True, False)],
    prevent_initial_call=False,
)
def feeder(n, mode):
    t0 = time.time()
    time.sleep(R)
    return f"n={n} mode={(mode or {}).get('mode')} served={t0:.3f}"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
