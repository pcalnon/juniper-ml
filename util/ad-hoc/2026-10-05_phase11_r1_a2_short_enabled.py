# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/short_enabled.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Enabled stretches shorter than 1.2 s (innermost timeline), what started and ended them; requests < 1 s in flight."""
import importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)
for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    print(p)
    st = []
    for a, b in zip(phys, phys[1:]):
        if a[2] is False and b[1] is False and a[3] != "layout":
            st.append((b[0] - a[0], a[0], a[3], b[3]))
    st.sort()
    print("  enabled stretches < 1200 ms:", [x for x in st if x[0] < 1200])
    print("  count < 1000 ms: %d of %d" % (sum(1 for x in st if x[0] < 1000), len(st)))
    print("  requests in flight < 1000 ms:", [(r["id"], r["tEnd"] - r["tW"], r["end"]) for r in ordered if r["end"] and r["tEnd"] - r["tW"] < 1000])
