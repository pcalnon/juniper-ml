# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: the synthetic app that refuted the F-058 census's eviction count.
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/synth_app.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch synthetic Dash app (lane R2-B): a running=-guarded 1 s Interval feeding a Store.

FEED_MODE=204  -> the callback always returns no_update (HTTP 204), like canopy's feeder on an idle fixture.
FEED_MODE=data -> the callback always returns a new value (HTTP 200 with data).
Server latency LAT seconds. Port from PORT.
"""
import os
import time

import dash
from dash import Dash, Input, Output, dcc, html

MODE = os.environ.get("FEED_MODE", "204")
LAT = float(os.environ.get("LAT", "2.0"))
PORT = int(os.environ.get("PORT", "9487"))

app = Dash(__name__)
app.layout = html.Div([
    dcc.Interval(id="lane", interval=1000, n_intervals=0),
    dcc.Store(id="feed", data=None),
    html.Div(id="out"),
])


@app.callback(
    Output("feed", "data"),
    Input("lane", "n_intervals"),
    running=[(Output("lane", "disabled"), True, False)],
    prevent_initial_call=False,
)
def feeder(n):
    time.sleep(LAT)
    if MODE == "204" and n and n > 0:
        return dash.no_update
    return {"n": n, "t": time.time()}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
