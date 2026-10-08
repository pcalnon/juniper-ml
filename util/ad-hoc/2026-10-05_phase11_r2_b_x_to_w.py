# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/x_to_w.py
# Written by Lane 11-R2B (adversarial, on round 1's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Eviction (X of k) vs the successor's entry into watched (W of k+1): how far 'made' precedes 'entered watched'."""
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
    gaps = []
    for a, b in zip(reqs, reqs[1:]):
        if a["end"] == "X":
            gaps.append(b["tW"] - a["tEnd"])
    gaps.sort()
    print(path[-45:], "X(k) -> W(k+1) ms:", gaps)
    # answered: A(k) -> W(k+1) gaps, to compare with cycle
    ag = sorted(b["tW"] - a["tEnd"] for a, b in zip(reqs, reqs[1:]) if a["end"] == "A")
    print("   A(k) -> W(k+1) ms: min", ag[0], "median", ag[len(ag)//2], "max", ag[-1])
