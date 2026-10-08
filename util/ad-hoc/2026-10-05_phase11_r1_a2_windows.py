# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/windows.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Recount each window's resolved/evicted with my own request fold (entered in [lo,hi), ended by hi)."""
import importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)
for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    W = [("baseline", d["baseline_window_ms"][0], d["baseline_window_ms"][1])]
    for tr in d["triggers"]:
        if "t_ms" in tr:
            W.append((tr["name"], tr["t_ms"], tr["t_ms"] + 180000))
    W.append(("idle", d["idle_window_ms"][0], d["idle_window_ms"][1]))
    print(p)
    for name, lo, hi in W:
        rows = [r for r in ordered if lo <= r["tW"] < hi and r["end"] is not None and r["tEnd"] <= hi]
        ev = [r["id"] for r in rows if r["end"] == "X"]
        fires = [f[0] for f in d["raw"]["fires"] if lo <= f[0] < hi]
        print("  %-9s [%s, %s) resolved=%d evicted=%d ids=%s fires=%s" % (name, lo, hi, len(rows), len(ev), ev, fires))
