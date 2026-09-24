# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the idle cuts' round 1, Lane B: the injected dead Interval the CLASS check must flag.
# Source: session 259b4d16's tmpfs scratchpad, laneB_probe_mutation.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane B review probe (read-only): show where tab-resident Intervals sit, then inject a dead Interval inside a dbc.Tab and confirm the CLASS predicate catches it."""

import importlib.util
import json
import logging
import os
import sys

SRC = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneB_extract/src"
os.chdir(SRC)
sys.path.insert(0, SRC)
os.environ.pop("CANOPY_API_KEY", None)
os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"
os.environ["JUNIPER_CANOPY_RATE_LIMIT_ENABLED"] = "false"
os.environ["JUNIPER_DATA_URL"] = "http://localhost:8100"
logging.disable(logging.CRITICAL)

spec = importlib.util.spec_from_file_location("t_cuts", os.path.join(SRC, "tests/unit/frontend/test_idle_dispatch_cuts.py"))
t = importlib.util.module_from_spec(spec)
sys.modules["t_cuts"] = t
spec.loader.exec_module(t)

from dash import dcc  # noqa: E402

from frontend.dashboard_manager import DashboardManager  # noqa: E402

app = DashboardManager({}).app
deps = json.loads(app.server.test_client().get("/_dash-dependencies").data)
layout = app.layout() if callable(app.layout) else app.layout


def find(node, target, trail):
    if isinstance(node, (list, tuple)):
        for c in node:
            r = find(c, target, trail)
            if r:
                return r
        return None
    if node is None or not hasattr(node, "to_plotly_json"):
        return None
    j = node.to_plotly_json()
    here = trail + [f"{j.get('namespace', '')}.{j.get('type')}"]
    if j.get("props", {}).get("id") == target:
        return here
    for v in j.get("props", {}).values():
        r = find(v, target, here)
        if r:
            return r
    return None


for target in ("replay-player-panel-weight-drain", "metrics-panel-stats-update-interval"):
    path = find(layout, target, [])
    print(target, "ancestors:", [p for p in path if "Tab" in p])

# Mutation: inject a consumer-less Interval as the LAST child of the replay Tab's content.
tab_host = None


def locate_tab(node):
    global tab_host
    if isinstance(node, (list, tuple)):
        for c in node:
            locate_tab(c)
        return
    if node is None or not hasattr(node, "to_plotly_json"):
        return
    j = node.to_plotly_json()
    if j.get("type") == "Tab" and tab_host is None and "replay" in str(j.get("props", {}).get("tab_id", "")):
        tab_host = node
        return
    for v in j.get("props", {}).values():
        locate_tab(v)


locate_tab(layout)
print("replay tab found:", tab_host is not None, getattr(tab_host, "tab_id", None))
kids = tab_host.children if isinstance(tab_host.children, list) else [tab_host.children]
tab_host.children = kids + [dcc.Interval(id="laneb-probe-dead-interval", interval=1000)]
dead = sorted(p["id"] for p in t._intervals(layout, []) if not t._consumers(deps, p["id"]))
print("CLASS predicate after injecting a dead Interval inside the replay Tab ->", dead)
