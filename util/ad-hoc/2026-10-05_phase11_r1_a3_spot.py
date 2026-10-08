# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/spot.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: spot numbers the ledger states that no named instrument prints."""
import json
import statistics
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
for name, p in (("run1", EV / "2026-10-05_census_live.json"), ("run2", EV / "run2/2026-10-05_census_live.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    a_times = sorted(r["tEnd"] for r in req.values() if r["end"] == "A")
    gaps = sorted(b - a for a, b in zip(a_times, a_times[1:]))
    print(name, "A gaps n", len(gaps), "lower/upper middle", gaps[(len(gaps) - 1) // 2], gaps[len(gaps) // 2], "statistics.median", statistics.median(gaps))
    # the stall around each eviction run: last A before the run's first W, first A after
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    runs, cur = [], []
    for r in reqs:
        if r["end"] == "X":
            cur.append(r)
        elif cur:
            runs.append((cur, r))
            cur = []
    for run, nxt in runs:
        prev_a = max([t for t in a_times if t < run[0]["tW"]] or [0])
        print(f"  run of {len(run)}: last A before {prev_a}, the A that ended it {nxt['tEnd']} -> {nxt['tEnd'] - prev_a} ms without an A")
    for trg in d["triggers"]:
        if trg.get("t_ms") is None:
            continue
        o = req[trg["open_request"]]
        print(f"  {trg['name']}: trigger {trg['t_ms']}, open req {o['id']} ended {o['end']} {o['tEnd'] - trg['t_ms']} ms after; open for {trg['t_ms'] - o['tW']} ms at the trigger")
    # disabled-episode durations exactly as analyze: median
    print("  host span ms", max(t for t, *_ in raw["req"]))
