# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/own_accounting.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: completeness of the shim's release log. Every answered request either has a logged own release, or
the lane had already been re-enabled under it (a late release, a fire or a gate write of false) before it ended."""
import importlib.util
import json
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
spec = importlib.util.spec_from_file_location("rt", S / "frozen/util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
for p in (EV / "2026-10-05_census_live.json", EV / "run2/2026-10-05_census_live.json"):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    res = rt.analyze(d)
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    answered = {r["id"] for r in req.values() if r["end"] == "A"}
    with_own = {rid for _t, rid, _g in res["own"]}
    missing = answered - with_own
    reen = [(x["release_ms"], "late") for x in res["late"]] + [(t, "fire") for t, *_ in raw["fires"]] + [(t, "gate") for t, b, v in raw["gate"] if b is True and v is False]
    explained, unexplained = {}, []
    for rid in sorted(missing):
        r = req[rid]
        why = [k for t, k in reen if r["tW"] <= t <= r["tEnd"]]
        if why:
            explained[rid] = why
        else:
            unexplained.append((rid, r["tW"], r["tEnd"]))
    kinds = {}
    for w in explained.values():
        kinds[w[0]] = kinds.get(w[0], 0) + 1
    print(f"{p.parent.name}: answered {len(answered)}, with a logged own release {len(with_own)}, without {len(missing)}; re-enabled under them before their end: {kinds}; unexplained {unexplained}")
