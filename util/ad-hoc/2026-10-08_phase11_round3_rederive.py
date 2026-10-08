#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — one-off; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Re-derive the numbers behind round 3's findings on the canopy E2E ledger's Phase 11, before they are applied.

Round 3 of Phase 11's validation (``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md``)
found that F-CANOPY-058's trigger bullet gives the 8 trigger-started evictions' range, 1.2–2.4 s after the
re-enable, as if it held for all 29 (Lane 11-R3B). This reads, for every eviction in both transcripts, the last
re-enable before it: the last change of the lane to enabled, in its innermost records, after the evicted request
entered ``watched`` and before the eviction (its ``X``). That re-enable is a watchdog fire, a gate write of
``false``, or the late release of the evicted request before it; the delay is from that re-enable to the eviction,
which is when the next request was made. It also prints, for the 7 evicting fires, the fire-to-eviction range that
F-CANOPY-068's Effect quotes.

It loads ``util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py`` by path and uses its ``lane_timeline`` (the
innermost records) and ``analyze`` (the late releases and their pairing); it refuses a transcript whose innermost
records break alternation.

Usage:
    python3 util/ad-hoc/2026-10-08_phase11_round3_rederive.py <transcript.json> [<transcript.json> ...]
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


rt = _load("f058_release_trace", HERE / "2026-10-05_f058_census_v2_release_trace.py")


def horizons(d):
    raw = d["raw"]
    if rt.alternation_breaks(raw["lane"]):
        raise SystemExit("refusing: the innermost records break alternation")
    res = rt.analyze(d)
    timeline = rt.lane_timeline(raw["lane"])
    fires = {t for t, _b, _s in raw["fires"]}
    gate_false = {t for t, _b, v in raw["gate"] if v is False}
    late_release = {x["release_ms"]: x["evicted"] for x in res["late"]}
    rows = []
    for e in res["evictions"]:
        enables = [t for t, s in timeline if s is False and e["tW"] <= t < e["x_ms"]]
        if not enables:
            rows.append((e["id"], e["x_ms"], None, None, None))
            continue
        t = enables[-1]
        # a fire or gate write is logged by its own record; the lane's change lands within 2 ms of it
        if any(abs(t - f) <= 2 for f in fires):
            kind = "fire"
        elif any(abs(t - g) <= 2 for g in gate_false):
            kind = "gate"
        elif t in late_release:
            kind = f"late release of req {late_release[t]}"
        else:
            kind = "other"
        rows.append((e["id"], e["x_ms"], t, e["x_ms"] - t, kind))
    return rows


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    every = []
    for p in argv:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        rows = horizons(d)
        print(f"== {p}: {len(rows)} evictions")
        for rid, x, t, gap, kind in rows:
            print(f"  req {rid}: evicted @{x}; last re-enable before it @{t} ({kind}); {gap} ms")
        every += rows
    trig = [r[3] for r in every if r[4] in ("fire", "gate")]
    fire = [r[3] for r in every if r[4] == "fire"]
    within = [r[3] for r in every if r[4] and r[4].startswith("late release")]
    other = [r for r in every if r[4] not in ("fire", "gate") and not (r[4] or "").startswith("late release")]
    print(f"started by a fire or gate write: n={len(trig)}, {min(trig)}-{max(trig)} ms")
    print(f"  of which by a fire: n={len(fire)}, {min(fire)}-{max(fire)} ms")
    print(f"within a run (after a late release): n={len(within)}, {min(within)}-{max(within)} ms; above 2,400 ms: {sorted(g for g in within if g > 2400)}")
    print(f"all: n={len(every)}, {min(r[3] for r in every if r[3] is not None)}-{max(r[3] for r in every if r[3] is not None)} ms; unclassified: {other}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
