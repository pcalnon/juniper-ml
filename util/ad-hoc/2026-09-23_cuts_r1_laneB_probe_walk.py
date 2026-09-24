# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the idle cuts' round 1, Lane B: the layout walk over every Interval.
# Source: session 259b4d16's tmpfs scratchpad, laneB_probe_walk.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane B review probe (read-only): run the frozen test file's own layout walk against the built app."""

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

from frontend.dashboard_manager import DashboardManager  # noqa: E402

app = DashboardManager({}).app
deps = json.loads(app.server.test_client().get("/_dash-dependencies").data)
layout = app.layout() if callable(app.layout) else app.layout
found = t._intervals(layout, [])
print("walk found", len(found), "Intervals:")
for p in found:
    cons = t._consumers(deps, p["id"])
    print("  ", p["id"], "| interval=", p.get("interval"), "| disabled=", p.get("disabled"), "| max_intervals=", p.get("max_intervals"), "| consumers=", len(cons))

# Independent walk that ALSO descends into dict-valued props (the test's walk does not).
def walk_all(node, out, path="root"):
    if isinstance(node, (list, tuple)):
        for i, c in enumerate(node):
            walk_all(c, out, f"{path}[{i}]")
        return out
    if isinstance(node, dict):
        for k, v in node.items():
            walk_all(v, out, f"{path}.{k}")
        return out
    if node is None or not hasattr(node, "to_plotly_json"):
        return out
    j = node.to_plotly_json()
    if j.get("type") == "Interval":
        out.append((j.get("props", {}).get("id"), path))
    for k, v in j.get("props", {}).items():
        walk_all(v, out, f"{path}.{j.get('type')}.{k}")
    return out

allint = walk_all(layout, [])
print("independent walk (incl. dict props) found", len(allint))
missing = sorted({i for i, _ in allint} - {p["id"] for p in found}, key=str)
print("  seen only by the independent walk:", missing)
