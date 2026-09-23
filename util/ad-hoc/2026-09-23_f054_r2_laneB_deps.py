#!/usr/bin/env python
"""canopy#670 round 2 (Lane B): readiness and writer census of the BUILT app at v2 (85415f3c), from a
tree materialised from git objects (never the fix worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 (F-CANOPY-054); util/ad-hoc/2026-09-23_f054_r2_laneB_extract.py

Checks, on the served /_dash-dependencies:
  1. every writer (primary, allow_duplicate, or a ``running=`` side output -- the served format is
     {"running": {"id.prop": v}, "runningOff": {...}}) of any replay-block Input prop;
  2. the renderer's readiness closure (getAllSubsequentOutputsForCallback, @hash kept) of every
     callback, against the controls' checked Inputs;
  3. what the refill (now writing -replay-position-max) can hold, and who holds it;
  4. every consumer (Input or State) of each controls Output, incl. the two new position spans.

Usage (run from the tree's src/):
    python util/ad-hoc/2026-09-23_f054_r2_laneB_deps.py --src <v2 tree>/src
"""

import argparse
import json
import sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.src)
    from frontend.dashboard_manager import DashboardManager

    deps = json.loads(DashboardManager({}).app.server.test_client().get("/_dash-dependencies").data)
    split = lambda o: o[2:-2].split("...") if o.startswith("..") else [o]  # noqa: E731
    base = lambda p: p.rpartition(".")[0] + "." + p.rpartition(".")[2].split("@", 1)[0]  # noqa: E731
    ids = lambda e, k: [f"{d['id']}.{d['property']}" for d in (e.get(k) or [])]  # noqa: E731
    cbs = []
    for i, e in enumerate(deps):
        r = e.get("running") or {}
        run_out = sorted(set((r.get("running") or {}).keys()) | set((r.get("runningOff") or {}).keys())) if isinstance(r, dict) else []
        cbs.append({"i": i, "outputs": [] if e.get("no_output") else split(e["output"]), "inputs": ids(e, "inputs"), "state": ids(e, "state"), "running": run_out, "cs": bool(e.get("clientside_function"))})
    print("callbacks served:", len(cbs), "| with running=:", sum(1 for c in cbs if c["running"]), [c["running"] for c in cbs if c["running"]])
    ctl = [c for c in cbs if "metrics-panel-replay-slider.value" in c["outputs"]]
    assert len(ctl) == 1
    ctl = ctl[0]
    refill = [c for c in cbs if any(o.startswith("metrics-panel-replay-position-max.children@") for o in c["outputs"])]
    assert len(refill) == 1, refill
    refill = refill[0]
    checked = [p for p in ctl["inputs"] if p not in ctl["outputs"]]
    print("controls outputs:", ctl["outputs"])
    print("controls state:", ctl["state"], "| refill inputs/state:", refill["inputs"], refill["state"])
    targets = set(ctl["inputs"]) | set(refill["inputs"])
    print("\n(1) writers of replay-block Input props:")
    for c in cbs:
        hits = sorted({base(o) for o in c["outputs"] if base(o) in targets} | {o for o in c["running"] if o in targets})
        if hits:
            print(f"   cb#{c['i']} clientside={c['cs']} -> {hits}")
    by_input = defaultdict(list)
    for c in cbs:
        for p in c["inputs"]:
            by_input[p].append(c["i"])

    def closure(c):
        touched, frontier = set(), [c]
        while frontier:
            outs = [o for cb in frontier for o in cb["outputs"] if o not in touched]
            touched.update(outs)
            frontier = [cbs[j] for o in outs for j in by_input.get(o, [])]
        return touched

    reach = defaultdict(list)
    for c in cbs:
        cl = closure(c)
        for p in checked:
            if p in cl:
                reach[p].append(c["i"])
    print("\n(2) callbacks whose closure covers a checked controls Input:", dict(reach) or "NONE")
    holders = sorted({c["i"] for c in cbs for p in refill["inputs"] if p not in refill["outputs"] and p in closure(c)})
    held = sorted({c["i"] for c in cbs if c is not refill and any(p in closure(refill) for p in c["inputs"] if p not in c["outputs"])})
    print("\n(3) refill held by:", holders, "| refill can hold:", held or "NONE", "| refill closure:", sorted(closure(refill)))
    print("\n(4) consumers of controls outputs (Input / State):")
    for o in ctl["outputs"]:
        print(f"   {o:48s} Input:{[c['i'] for c in cbs if base(o) in c['inputs'] and c is not ctl]} State:{[c['i'] for c in cbs if base(o) in c['state']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
