# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: canopy's watchdog JavaScript over a 40 s lane.
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/synth_app2.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch synthetic Dash app 2 (lane R2-B): canopy's strand watchdog, verbatim, over a slow guarded lane.

The feeder's server latency (LAT, default 40 s) exceeds the watchdog's 30 s threshold, so the watchdog
FIRES. The fire branch also bumps window.__groundTruthFires (the only line not in canopy's JS).
"""
import os
import time

from dash import Dash, Input, Output, State, dcc, html

LAT = float(os.environ.get("LAT", "40.0"))
PORT = int(os.environ.get("PORT", "9489"))

app = Dash(__name__)
app.layout = html.Div([
    dcc.Interval(id="lane", interval=1000, n_intervals=0),
    dcc.Interval(id="slow", interval=5000, n_intervals=0),
    dcc.Store(id="apply", data=None),
    dcc.Store(id="feed", data=None),
])


@app.callback(
    Output("feed", "data"),
    Input("lane", "n_intervals"),
    running=[(Output("lane", "disabled"), True, False)],
    prevent_initial_call=False,
)
def feeder(n):
    time.sleep(LAT)
    return {"n": n, "t": time.time()}


app.clientside_callback(
    """
    function(n, disabled, applyInFlight) {
        var NU = window.dash_clientside.no_update;
        if (!disabled || Boolean(applyInFlight)) {
            window.__metricsStoreDisabledSince = null;
            return NU;
        }
        var now = Date.now();
        if (!window.__metricsStoreDisabledSince) {
            window.__metricsStoreDisabledSince = now;
            return NU;
        }
        if (now - window.__metricsStoreDisabledSince < 30000) {
            return NU;
        }
        window.__metricsStoreDisabledSince = null;
        window.__groundTruthFires = (window.__groundTruthFires || 0) + 1;
        return false;
    }
    """,
    Output("lane", "disabled", allow_duplicate=True),
    Input("slow", "n_intervals"),
    [State("lane", "disabled"), State("apply", "data")],
    prevent_initial_call=True,
)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
