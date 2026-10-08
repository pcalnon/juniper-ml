# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B1.oCpUdY/triggers.py
# Written by Lane 11-B1 (adversarial, dispositions and ratings, fold side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""For each scripted trigger: when its targeted request ended, and the next requests' entry times, relative to the trigger."""
import json
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raw = d["raw"]
req = {}
for t, kind, rid, props in raw["req"]:
    r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
    if kind == "W" and r["tW"] is None:
        r["tW"] = t
    elif kind in ("A", "X") and r["end"] is None:
        r["end"], r["tEnd"] = kind, t
reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
for tr in d["triggers"]:
    t0 = tr.get("t_ms")
    if t0 is None:
        print(tr["name"], "no t_ms", tr.get("verdict"))
        continue
    oid = tr.get("open_request")
    o = req.get(oid) or req.get(str(oid))
    print(f"{tr['name']} @{t0}: targeted req {oid} W {o and o['tW']} ({o and (t0 - o['tW'])} ms into flight) ended {o and o['end']} {o and (o['tEnd'] - t0)} ms after trigger")
    nxt = [r for r in reqs if r["tW"] > t0][:3]
    print("   next W after trigger:", [(r["id"], r["tW"] - t0, r["end"], (r["tEnd"] - t0) if r["tEnd"] else None) for r in nxt])
    gates = [(g[0] - t0, g[1], g[2]) for g in raw["gate"] if t0 <= g[0] <= t0 + 10000]
    print("   gate writes in [t, t+10 s]:", gates)
    if "clicks_ms" in tr:
        print("   clicks:", [c - t0 for c in tr["clicks_ms"]])
