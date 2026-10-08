# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe4.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone; py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 4: stalls, flights vs horizons, re-enables vs one-period horizon, local cycle before fires."""
import json
import statistics

for name, path in [("run1", "ev/2026-10-05_census_live.json"), ("run2", "ev/run2/2026-10-05_census_live.json")]:
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    req = {}
    for t, kind, rid, props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    tA = sorted(r["tEnd"] for r in reqs if r["end"] == "A")
    gaps = sorted(((b - a, a, b) for a, b in zip(tA, tA[1:])), reverse=True)[:4]
    print(f"=== {name} top applied gaps (ms, from, to): {gaps}")
    fl = sorted(r["tEnd"] - r["tW"] for r in reqs if r["end"])
    for h in (1000, 1400, 1500, 2000, 2400):
        print(f"  flights <= {h} ms: {sum(1 for x in fl if x <= h)} of {len(fl)}")
    # re-enables mid-request (fires + gate True->False with a request in flight): response landing vs 1 s
    reen = [(t, "fire") for t, b, _s in raw["fires"]] + [(t, "gate") for t, b, v in raw["gate"] if b is True and v is False]
    rows = []
    for t, k in sorted(reen):
        live = [r for r in reqs if r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
        if not live:
            continue
        r = live[-1]
        rows.append((t, k, r["id"], r["end"], r["tEnd"] - t))
    over = [x for x in rows if x[3] == "A" and x[4] > 1000]
    print(f"  mid-request re-enables: {len(rows)}; evicting {sum(1 for x in rows if x[3] == 'X')}; answered >1 s after the re-enable, no eviction: {len(over)} -> {[(x[1], x[0], x[4]) for x in over]}")
    # local cycle (W-to-W mean) in the 35 s before each fire
    Ws = [r["tW"] for r in reqs]
    loc = []
    for t, _b, _s in raw["fires"]:
        w = [x for x in Ws if t - 35000 <= x <= t]
        g = [b - a for a, b in zip(w, w[1:])]
        loc.append(round(statistics.mean(g)) if g else None)
    print(f"  mean W-to-W gap in the 35 s before each fire: {loc}")
