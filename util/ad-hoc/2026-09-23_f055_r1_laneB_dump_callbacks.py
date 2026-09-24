# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: dumps the built app's callback map.
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/dump_callbacks.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Build DashboardManager({}) from a frozen tree and dump the lane-related registrations.

usage: python dump_callbacks.py <tree-root> <out.json>
"""

import json
import os
import sys

root = os.path.abspath(sys.argv[1])
out_path = sys.argv[2]
src = os.path.join(root, "src")
sys.path.insert(0, src)
os.chdir(root)

import frontend.dashboard_manager as dmmod  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402

assert os.path.abspath(dmmod.__file__).startswith(src), dmmod.__file__
dm = DashboardManager({})
app = dm.app

LANES = ("status-bar-interval", "metrics-store-interval", "fast-update-interval", "slow-update-interval")


def deps(entry, key):
    return [f"{d['id']}.{d['property']}" for d in entry.get(key, [])]


def touches(entry):
    blob = json.dumps(
        {"o": str(entry["output"]), "i": deps(entry, "inputs"), "s": deps(entry, "state"), "r": entry.get("running")},
        default=str,
    )
    return any(lane in blob for lane in LANES)


inline = "\n".join(app._inline_scripts)
records = []
for idx, entry in enumerate(app._callback_list):
    if not touches(entry):
        continue
    rec = {
        "idx": idx,
        "output": str(entry["output"]),
        "inputs": deps(entry, "inputs"),
        "state": deps(entry, "state"),
        "prevent_initial_call": entry.get("prevent_initial_call"),
        "running": entry.get("running"),
        "clientside": entry.get("clientside_function"),
    }
    cs = entry.get("clientside_function")
    if cs and cs.get("namespace") == "_dashprivate_clientside_funcs":
        fn = cs["function_name"]
        start = inline.find(fn)
        rec["js_found"] = start >= 0
    records.append(rec)

payload = {
    "module": dmmod.__file__,
    "n_callbacks": len(app._callback_list),
    "gated": [list(x) for x in dmmod._GATED_POLL_INTERVALS],
    "records": records,
    "inline_scripts": app._inline_scripts,
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=1, default=str)
print("module:", dmmod.__file__)
print("callbacks:", len(app._callback_list), "lane-touching:", len(records))
for r in records:
    print(r["idx"], "| OUT", r["output"][:160], "| IN", r["inputs"], "| ST", r["state"], "| PIC", r["prevent_initial_call"], "| RUN", r["running"], "| CS", (r["clientside"] or {}).get("function_name", "")[:12])
