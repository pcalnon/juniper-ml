#!/usr/bin/env python3
"""
Lane A3 post-hoc diagnostic: does "a tick of its own interval arrived before the page processed the response" separate landed from not-landed?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (POST-HOC diagnostic over the Lane A3 artifacts; NOT the pre-registered verdict,
        which lives in 2026-09-22_laneA3_candidate_tick_period_test.py and is not affected by this script)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-22_laneA3_candidate_tick_period_test.py;
         reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA3_candidate_tick_period_run*.json

For every fetch_training_state request answered HTTP 200 with a state-store timestamp, classify:
  tick_inside : an n_intervals transition of candidate-metrics-panel-update-interval falls in
                (t_start, t_body - shave), where t_body is the in-page parse of the response clone
                (the renderer's own parse resolves ~0.05-0.5 s earlier, hence the shave sensitivity);
  landed      : the response's timestamp is ever observed in the renderer's layout for the store.
Prints the 2x2 table per artifact and per shave. Perfect separation = every tick_inside request is
not-landed and every no-tick request landed.

Usage:
  python3 util/ad-hoc/2026-09-22_laneA3_tick_inside_window_contingency.py [artifact.json ...]
"""

import bisect
import glob
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEFAULT_GLOB = os.path.join(_REPO, "reports", "e2e-canopy-2026-09-02", "transcripts", "2026-09-22_laneA3_candidate_tick_period_run*.json")


def table(path: str, shave_ms: float) -> dict:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    ev = d["raw"]["ev"]
    wire = d["raw"]["wire"]
    ticks = sorted(e["t"] for e in ev if e["k"] == "n" and isinstance(e["v"], int))
    observed = {e["v"] for e in ev if e["k"] == "ts" and isinstance(e["v"], (int, float))}
    tab = {"tick_inside_landed": 0, "tick_inside_not_landed": 0, "no_tick_landed": 0, "no_tick_not_landed": 0}
    exceptions = []
    for r in wire:
        if r.get("http") != 200 or r.get("t_body") is None or not isinstance(r.get("ts"), (int, float)):
            continue
        end = r["t_body"] - shave_ms
        i = bisect.bisect_right(ticks, r["t_start"])
        tick_inside = i < len(ticks) and ticks[i] < end
        landed = r["ts"] in observed
        key = ("tick_inside_" if tick_inside else "no_tick_") + ("landed" if landed else "not_landed")
        tab[key] += 1
        if (tick_inside and landed) or (not tick_inside and not landed):
            nxt = round((ticks[i] - r["t_start"]) / 1000.0, 3) if i < len(ticks) else None
            exceptions.append({"seq": r["seq"], "t_start_s": round(r["t_start"] / 1000.0, 3), "page_rtt_s": round((r["t_body"] - r["t_start"]) / 1000.0, 3), "next_tick_after_start_s": nxt, "landed": landed})
    return {"artifact": os.path.basename(path), "lifecycle_reader": d.get("lifecycle_reader"), "shave_s": shave_ms / 1000.0, **tab, "exceptions": exceptions}


def main() -> int:
    paths = sys.argv[1:] or sorted(glob.glob(DEFAULT_GLOB))
    for p in paths:
        for shave in (0.0, 500.0):
            print(json.dumps(table(p, shave)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
