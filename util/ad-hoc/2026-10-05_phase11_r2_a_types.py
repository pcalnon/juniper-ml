# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/types.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import collections
import json
import sys

for p in sys.argv[1:]:
    with open(p) as fh:
        raw = json.load(fh)["raw"]
    c = collections.Counter()
    for t, b, a, ty in raw["lane"]:
        for x in (ty.split("+") if ty else [""]):
            c[x] += 1
    tf_empty = sum(1 for t, b, a, ty in raw["lane"] if ty == "" and b is False and a is True)
    w = sum(1 for r in raw["req"] if r[1] == "W")
    print(p.split("/")[-2], "ON_PROP_CHANGE:", c.get("ON_PROP_CHANGE", 0), "| AddRequested in lane types:", c.get("Callbacks.AddRequested", 0), "| empty-type F->T:", tf_empty, "W:", w, "| type counts:", dict(c.most_common(12)))
