#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Read a ``2026-10-04_f058_census_v2_live.py`` transcript event by event, past its verdicts.

The live census's verdicts are fixed rules over windows. This prints what they summarize, so a reader can see
why each came out as it did, and what preceded each eviction:

  requests   the feeder's in-flight time (W to its end), from the shim's dispatch log
  lane       each disabled episode of the lane (False -> True -> False), from the shim's lane log
  fires      each watchdog fire: the lane's disabled episode at that moment, whether a feeder request was in
             flight, and when that request ended (a response landing more than one 1 s period after a
             re-enable is F-CANOPY-058's condition for an eviction)
  gate       each gate write, with the same three facts
  evictions  every evicted request, grouped into runs of consecutive evictions, each run with the nearest
             re-enable (a fire, or a gate write of ``false`` with the lane disabled before it) in the 10 s
             before its first eviction's request entered ``watched``

Usage:
    python3 <this file> <transcript.json>
"""

import json
import statistics
import sys
from pathlib import Path


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))] if xs else None


def main() -> int:
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = d["raw"]
    # Requests: first W and the first terminal record (A or X), as the shim's classify() folds them.
    req = {}
    for t, kind, rid, props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    done = sorted((r for r in req.values() if r["tW"] is not None and r["end"]), key=lambda r: r["tW"])
    open_end = [r for r in req.values() if r["tW"] is not None and not r["end"]]
    dur = [r["tEnd"] - r["tW"] for r in done]
    print(f"served {d.get('served_sha')}  dispatches {raw['dispatches']}  errors {len(raw['errors'])}")
    print(f"requests: {len(done)} ended ({sum(r['end'] == 'A' for r in done)} A, {sum(r['end'] == 'X' for r in done)} X), {len(open_end)} never ended")
    print(f"  in flight ms: median {statistics.median(dur):.0f}  p90 {pct(dur, 0.9)}  max {max(dur)}")
    # Lane episodes from the lane log, ordered by time: (t, before, after, types).
    lane = sorted(raw["lane"], key=lambda x: x[0])
    episodes, start = [], None
    for t, before, after, _types in lane:
        if after is True and start is None:
            start = t
        elif after is False and start is not None:
            episodes.append((start, t))
            start = None
    ep_len = [b - a for a, b in episodes]
    print(f"lane disabled episodes: {len(episodes)}  median {statistics.median(ep_len):.0f} ms  p90 {pct(ep_len, 0.9)}  max {max(ep_len)}")

    def episode_at(t):
        for a, b in episodes:
            if a <= t <= b:
                return (a, b)
        return None

    def in_flight_at(t):
        return [r for r in req.values() if r["tW"] is not None and r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]

    def describe(label, t):
        ep = episode_at(t)
        fl = in_flight_at(t)
        land = [(r["id"], r["end"], (r["tEnd"] - t) if r["tEnd"] is not None else None) for r in fl]
        print(f"  {label} @{t}: lane episode {ep and (ep[0], ep[1] - ep[0])}, in flight {land}")

    print(f"watchdog fires: {len(raw['fires'])}")
    for t, before, _since in raw["fires"]:
        describe(f"fire (lane before {before})", t)
    print(f"gate writes: {len(raw['gate'])}")
    for t, before, v in raw["gate"]:
        describe(f"gate {before}->{v}", t)
    # Eviction runs, over requests ordered by entry into watched.
    runs, cur = [], []
    for r in done:
        if r["end"] == "X":
            cur.append(r)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    reenables = [(t, "fire") for t, _b, _s in raw["fires"]] + [(t, "gate") for t, b, v in raw["gate"] if b is True and v is False]
    trig = {x["name"]: x.get("t_ms") for x in d["triggers"]}
    print(f"eviction runs: {[len(x) for x in runs]}  (triggers at {trig})")
    for run in runs:
        t0 = run[0]["tW"]
        near = [(t, k) for t, k in reenables if t0 - 10000 <= t <= run[-1]["tEnd"]]
        print(f"  run of {len(run)}: first W {t0}, last end {run[-1]['tEnd']}, re-enables in [first W - 10 s, last end]: {near}")
        print(f"    ids {[r['id'] for r in run]}  in-flight ms {[r['tEnd'] - r['tW'] for r in run]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
