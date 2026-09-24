# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the idle cuts' round 1, Lane B: the exact-envelope probe of _merge_session.
# Source: session 259b4d16's tmpfs scratchpad, laneB_probe_exact.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane B review probe (read-only): exact-id references to the removed interval, and what metrics-store-interval drives."""

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

from frontend.dashboard_manager import DashboardManager  # noqa: E402

app = DashboardManager({}).app
deps = json.loads(app.server.test_client().get("/_dash-dependencies").data)
exact = []
for e in deps:
    for kind in ("inputs", "state"):
        for d in e.get(kind, []):
            if d["id"] == "metrics-panel-update-interval":
                exact.append((kind, e["output"]))
    if "metrics-panel-update-interval." in e["output"].replace("candidate-metrics-panel-update-interval.", ""):
        exact.append(("output", e["output"]))
print("exact references to metrics-panel-update-interval in built deps:", exact)
for e in deps:
    if any(i["id"] == "metrics-store-interval" and i["property"] == "n_intervals" for i in e.get("inputs", [])):
        print("metrics-store-interval drives:", e["output"], "| clientside:", bool(e.get("clientside_function")))
# does any clientside JS body in the app reference the removed id?
print("clientside bodies naming it:", [k for k, v in (getattr(app, "_inline_scripts", None) and {"inline": "\n".join(app._inline_scripts)} or {}).items() if "metrics-panel-update-interval" in v.replace("candidate-metrics-panel-update-interval", "")])
