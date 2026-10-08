# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/late_to_x.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""For every re-enable that preceded an eviction in Phase 11's runs: the 8 trigger re-enables (fires, gate writes)
and the late releases (an evicted request's discarded response re-enabling the lane under its successor), the time
from that re-enable to the eviction it led to. Uses the 7af6a381 release trace's analyze() for the late releases."""
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location("rt", "/tmp/tmp.cIFAKjB6BD/7af/release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
allv = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    res = rt.analyze(d)
    rq = res["req_times"]
    lr = []
    for x in res["late"]:
        if x["under_end"] == "X":
            succ_x = rq[x["under"]][1]
            lr.append((x["release_ms"], x["evicted"], x["under"], succ_x - x["release_ms"]))
    print(path.split("/")[-2], "late release -> successor's eviction (ms):", [v for *_r, v in lr])
    allv += [v for *_r, v in lr]
    for r in lr:
        if r[3] > 2400:
            print("   > 2.4 s:", r)
print("late-release re-enables that evicted:", len(allv), "range", min(allv), "-", max(allv), "; above 2,400 ms:", sorted(v for v in allv if v > 2400))
