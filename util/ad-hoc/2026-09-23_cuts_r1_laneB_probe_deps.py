# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the idle cuts' round 1, Lane B: the built-app dependency probe (the single-writer check over 178 callbacks).
# Source: session 259b4d16's tmpfs scratchpad, laneB_probe_deps.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane B review probe (read-only): interrogate the BUILT app of the frozen extract (canopy ce78e0de)."""

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

from frontend.dashboard_manager import _GATED_POLL_INTERVALS, DashboardManager  # noqa: E402

app = DashboardManager({}).app
deps = json.loads(app.server.test_client().get("/_dash-dependencies").data)
print("n callbacks:", len(deps))


def outs(e):
    o = e["output"]
    return o[2:-2].split("...") if o.startswith("..") else [o]


def fmt(xs):
    return [f"{x['id']}.{x['property']}" for x in xs]


DRAIN = "replay-player-panel-weight-drain"
print("--- every dep mentioning the drain:")
for e in deps:
    if DRAIN in json.dumps(e):
        print("  out=", outs(e), "| in=", fmt(e["inputs"]), "| state=", fmt(e.get("state", [])), "| clientside=", bool(e.get("clientside_function")), "| pic=", e.get("prevent_initial_call"))
print("--- every writer of replay-player-session.*:")
for e in deps:
    for o in outs(e):
        if o.startswith("replay-player-session."):
            print("  ", o, "| in=", fmt(e["inputs"]), "| state=", fmt(e.get("state", [])))
print("--- every reader of replay-player-session.data:")
for e in deps:
    if "replay-player-session" in json.dumps(e.get("inputs", [])) or "replay-player-session" in json.dumps(e.get("state", [])):
        print("  out=", outs(e), "| in=", fmt(e["inputs"]), "| state=", fmt(e.get("state", [])))
print("--- deps mentioning metrics-panel-update-interval:", [outs(e) for e in deps if "metrics-panel-update-interval" in json.dumps(e)])
print("--- drain in tab gate:", [x for x in _GATED_POLL_INTERVALS if x[0] == DRAIN])
print("--- tab gate entries:", _GATED_POLL_INTERVALS)
print("--- writers of ANY Interval .disabled / .interval / .max_intervals:")
for e in deps:
    for o in outs(e):
        prop = o.split(".", 1)[1] if "." in o else ""
        if prop.split("@")[0] in ("disabled", "interval", "max_intervals", "n_intervals"):
            print("  ", o, "| in=", fmt(e["inputs"])[:4], "| clientside=", bool(e.get("clientside_function")))
