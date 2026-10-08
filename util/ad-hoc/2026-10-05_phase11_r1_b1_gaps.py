# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B1.oCpUdY/gaps.py
# Written by Lane 11-B1 (adversarial, dispositions and ratings, fold side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Independent re-derivation of applied-answer gaps, run stalls, and per-fire facts from a census v2 transcript."""
import json
import statistics
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raw = d["raw"]
req = {}
for t, kind, rid, props in raw["req"]:
    r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None, "props": None})
    if kind == "W" and r["tW"] is None:
        r["tW"] = t
    elif kind in ("A", "X") and r["end"] is None:
        r["end"], r["tEnd"], r["props"] = kind, t, props
reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
A = sorted(r["tEnd"] for r in reqs if r["end"] == "A")
gaps = [b - a for a, b in zip(A, A[1:])]
print("served", d.get("served_sha"), "requests", len(reqs), "A", len(A), "X", sum(r["end"] == "X" for r in reqs), "open", sum(r["end"] is None for r in reqs))
print("applied gaps ms: median", statistics.median(gaps), "max", max(gaps), "top6", sorted(gaps)[-6:])
withprops = [r for r in reqs if r["end"] == "A" and r["props"]]
print("A answers with props:", len(withprops), [(r["id"], str(r["props"])[:80]) for r in withprops[:3]])
print("triggers:", json.dumps(d.get("triggers"))[:2500])
print("top-level keys:", list(d.keys()))
print("raw keys:", list(raw.keys()))
