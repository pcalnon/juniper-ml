# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: does a re-render re-request the feeder?.
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/rerender_check.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Which callback-rendered containers (Output '<id>.children' or other component-valued props)
enclose the feeder's output components or the status-bar lane? A re-render of such a container
makes dash-renderer re-request the feeder as a layout (initial) callback.

usage: python rerender_check.py <tree-root>
"""

import os
import sys

root = os.path.abspath(sys.argv[1])
src = os.path.join(root, "src")
sys.path.insert(0, src)
os.chdir(root)

from frontend.dashboard_manager import DashboardManager  # noqa: E402

dm = DashboardManager({})
app = dm.app

TARGETS = {
    "status-bar-interval",
    "status-indicator",
    "connection-status",
    "latency-display",
    "top-status-display",
    "top-phase-display",
    "top-epoch-display",
    "top-hidden-units-display",
    "training-status-store",
    "live-dataset-switch-button",
}


def out_props(entry):
    raw = str(entry["output"])
    parts = raw[2:-2].split("...") if raw.startswith("..") and raw.endswith("..") else [raw]
    return [p.split("@", 1)[0] for p in parts]


rendered = {}
for entry in app._callback_list:
    for op in out_props(entry):
        cid, _, prop = op.rpartition(".")
        if prop in ("children", "tabs", "content", "label"):
            rendered.setdefault(cid, set()).add(prop)


def walk(comp, ancestors):
    cid = getattr(comp, "id", None)
    if isinstance(cid, str) and cid in TARGETS:
        hits = [a for a in ancestors if a in rendered]
        print(f"{cid}: re-rendered ancestors = {hits}")
    here = ancestors + ([cid] if isinstance(cid, str) else [])
    kids = getattr(comp, "children", None)
    if kids is None:
        return
    if not isinstance(kids, (list, tuple)):
        kids = [kids]
    for k in kids:
        if hasattr(k, "children") or hasattr(k, "id"):
            walk(k, here)


layout = app.layout() if callable(app.layout) else app.layout
walk(layout, [])
print("callback-rendered containers:", len(rendered))
