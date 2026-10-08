#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — instrument check; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""A scratch Dash app with canopy#613's lane wiring, for checking the F-CANOPY-058 census on known answers.

It mirrors, at small scale, what the census measures on canopy (``src/frontend/dashboard_manager.py`` at
``1b2dd438``):

  lane      ``dcc.Interval`` (1 s), canopy's ``metrics-store-interval``.
  feeder    Output ``feed.data``; Inputs ``lane.n_intervals`` and ``mode.data`` (the SECOND Input, canopy's
            ``metrics-panel-display-mode-store``); ``running=[(Output(lane, disabled), True, False)]``;
            sleeps ``LAT`` seconds; answers new data (``FEED_MODE=data``) or ``dash.no_update``
            (``FEED_MODE=noupdate``; canopy's idle feeder).
  gate      clientside, Output ``lane.disabled`` (duplicate), Inputs ``inflight.data`` and ``tabs.value``:
            returns ``Boolean(inflight)`` for this global lane on every fire, mount included (canopy's
            fused CAN-000/tab gate, ``tab === null`` branch).
  watchdog  clientside, Output ``lane.disabled`` (duplicate), Input ``slow.n_intervals`` (5 s), States
            ``lane.disabled`` and ``inflight.data``: canopy's strand watchdog, verbatim except that its
            threshold is ``STRAND_MS`` (canopy: ``METRICS_STORE_STRAND_TIMEOUT_MS``).

The ids are canopy's, so the census runs here unchanged: ``metrics-store-interval``,
``metrics-panel-metrics-store``, ``metrics-panel-display-mode-store``, ``apply-in-flight``,
``visualization-tabs`` (a ``dcc.Tabs`` here; canopy's is a ``dbc.Tabs``, whose prop is ``active_tab``) and
``slow-update-interval``. The watchdog keeps canopy's ``window.__metricsStoreDisabledSince``.

Environment: ``FEED_MODE`` (data | noupdate), ``LAT`` (seconds), ``STRAND_MS``, ``GATE_AT_MOUNT`` (1 | 0), ``PORT``.
"""

import os
import time

import dash
from dash import Dash, Input, Output, State, dcc, html

MODE = os.environ.get("FEED_MODE", "data")
LAT = float(os.environ.get("LAT", "3.0"))
STRAND_MS = int(os.environ.get("STRAND_MS", "30000"))
# 1 (canopy): the gate fires at mount, after the feeder's first request is already in flight. 0: it does not.
GATE_AT_MOUNT = os.environ.get("GATE_AT_MOUNT", "1") == "1"
PORT = int(os.environ.get("PORT", "9491"))

LANE = "metrics-store-interval"

app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.Interval(id=LANE, interval=1000, n_intervals=0),
        dcc.Interval(id="slow-update-interval", interval=5000, n_intervals=0),
        dcc.Store(id="metrics-panel-metrics-store", data=None),
        dcc.Store(id="metrics-panel-display-mode-store", data={"mode": "window", "window_size": 100}),
        dcc.Store(id="apply-in-flight", data=False),
        dcc.Tabs(id="visualization-tabs", value="metrics", children=[dcc.Tab(label="Training Metrics", value="metrics"), dcc.Tab(label="About", value="about")]),
        html.Div(id="out"),
    ]
)


@app.callback(
    Output("metrics-panel-metrics-store", "data"),
    Input(LANE, "n_intervals"),
    Input("metrics-panel-display-mode-store", "data"),
    running=[(Output(LANE, "disabled"), True, False)],
    prevent_initial_call=False,
)
def feeder(n, mode):
    time.sleep(LAT)
    if MODE == "noupdate" and n:
        return dash.no_update
    return {"n": n, "t": time.time(), "mode": mode}


app.clientside_callback(
    """
    function(inFlight, activeTab) {
        return Boolean(inFlight);
    }
    """,
    Output(LANE, "disabled"),
    Input("apply-in-flight", "data"),
    Input("visualization-tabs", "value"),
    prevent_initial_call=not GATE_AT_MOUNT,
)

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
        if (now - window.__metricsStoreDisabledSince < %d) {
            return NU;
        }
        window.__metricsStoreDisabledSince = null;
        return false;
    }
    """
    % STRAND_MS,
    Output(LANE, "disabled", allow_duplicate=True),
    Input("slow-update-interval", "n_intervals"),
    State(LANE, "disabled"),
    State("apply-in-flight", "data"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
