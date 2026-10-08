# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/a_to_w.py
# Written by Lane 11-R2B (adversarial, on round 1's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Distribution of answer(k) -> W(k+1) gaps (lane re-enabled by k's own release; next tick makes k+1)."""
import json, sys
for path in sys.argv[1:]:
    with open(path) as fh:
        d = json.load(fh)
    req = {}
    for t, kind, rid, _p in d["raw"]["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    gaps = sorted(b["tW"] - a["tEnd"] for a, b in zip(reqs, reqs[1:]) if a["end"] == "A" and b["tW"] - a["tEnd"] < 10000)
    n = len(gaps)
    pct = lambda p: gaps[min(n - 1, int(p * (n - 1) + 0.5))]
    print(path[-45:], "n", n, "min", gaps[0], "p5", pct(0.05), "p10", pct(0.10), "p25", pct(0.25), "median", pct(0.5), "p75", pct(0.75), "max", gaps[-1])
    for thr in (1450, 1520):
        print("   share <=", thr, ":", sum(1 for g in gaps if g <= thr), "of", n)
    for tr in d["triggers"]:
        if tr.get("name") == "T-mode":
            t = tr["t_ms"]; rid = tr["open_request"]
            r = req[rid]
            nxt = next(x for x in reqs if x["tW"] > r["tEnd"])
            print("   T-mode: targeted", rid, "end", r["end"], "+", r["tEnd"] - t, "next W +", nxt["tW"] - t, "A->W", nxt["tW"] - r["tEnd"])
