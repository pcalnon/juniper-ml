# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/owngaps.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
import importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)
allg = []
for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    offs = [x for x in phys if x[3] == "off"]
    g = []
    for x in offs:
        fl = mr.in_flight(reqs, x[0])
        q = fl[0]
        if q["end"] == "A" and q["tEnd"] - x[0] <= 300:
            g.append(q["tEnd"] - x[0])
    g.sort(); allg += g
    print(p, "own gaps n=%d" % len(g), "min", g[0], "max", g[-1], "lowest 5", g[:5], "highest 8", g[-8:])
    print("  answered with props:", [(r["id"], r["tW"], r["tEnd"]) for r in ordered if r["end"] == "A" and r["props"]])
allg.sort()
print("combined own gaps n=%d min %d max %d" % (len(allg), allg[0], allg[-1]))
