# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe1.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 1: grid of the watchdog's fires, feeder cycle stats, W residues, fire positions."""
import json
import statistics
import sys
from collections import Counter

sys.path.insert(0, "util")
import importlib.util

spec = importlib.util.spec_from_file_location("rt", "util/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)


def load(p):
    with open(p) as fh:
        return json.load(fh)


for name, path in [("run1", "ev/2026-10-05_census_live.json"), ("run2", "ev/run2/2026-10-05_census_live.json")]:
    d = load(path)
    raw = d["raw"]
    req = {}
    for t, kind, rid, props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None, "props": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"], r["props"] = kind, t, props
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    fires = [f[0] for f in raw["fires"]]
    print(f"=== {name} served {d.get('served_sha')[:8]}")
    print(" fire residues mod 5000:", [f % 5000 for f in fires])
    print(" fire-to-fire gaps (s):", [round((b - a) / 1000, 1) for a, b in zip(fires, fires[1:])])
    print(" fire-to-fire gaps / 5000:", [round((b - a) / 5000, 2) for a, b in zip(fires, fires[1:])])
    Ws = [r["tW"] for r in reqs]
    gaps = [b - a for a, b in zip(Ws, Ws[1:])]
    print(f" W-to-W gaps: n {len(gaps)} mean {statistics.mean(gaps):.0f} median {statistics.median(gaps):.0f} sd {statistics.pstdev(gaps):.0f} min {min(gaps)} max {max(gaps)}")
    # exclude gaps > 8000 (clamp) and gaps < 4000 (cascade-shortened)
    g2 = [g for g in gaps if g < 8000]
    print(f" W-to-W gaps <8 s: n {len(g2)} mean {statistics.mean(g2):.0f} median {statistics.median(g2):.0f} sd {statistics.pstdev(g2):.0f}")
    # applied answers' gaps
    tA = sorted(r["tEnd"] for r in reqs if r["end"] == "A")
    ga = [b - a for a, b in zip(tA, tA[1:])]
    print(f" applied gaps: median {statistics.median(ga)} mean {statistics.mean(ga):.0f} max {max(ga)}")
    # W residues mod 5000 histogram in 500 ms bins, by segment
    for lo, hi in [(0, 650000), (730000, 2000000)]:
        res = [w % 5000 for w in Ws if lo <= w < hi]
        h = Counter(x // 500 for x in res)
        print(f"  W residue bins (500 ms) in [{lo},{hi}):", [h.get(i, 0) for i in range(10)])
    # flight durations
    dur = [r["tEnd"] - r["tW"] for r in reqs if r["end"]]
    print(f" flights: n {len(dur)} under 1000: {[x for x in dur if x < 1000]}")
    # answered with props
    print(" answered with props:", sum(1 for r in reqs if r["end"] == "A" and r["props"]), "first A props:", [(r["id"], r["props"]) for r in reqs if r["end"] == "A"][:3])
    open_ = [r["id"] for r in reqs if r["end"] is None]
    print(" open at end:", open_)
