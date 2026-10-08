# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/backdate.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone; py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""How far does each enclosing (outer) lane record backdate its physical change? innermost entry - outermost entry."""
import json, sys
from collections import defaultdict
for p in sys.argv[1:]:
    with open(p) as fh:
        L = json.load(fh)["raw"]["lane"]
    by = defaultdict(list)
    for j, r in enumerate(L):
        if r[3] != "":
            continue
        # walk up the chain
        k = j + 1
        top = None
        while k < len(L) and L[k][3] not in ("", "SET_LAYOUT") and (L[k][1], L[k][2]) == (r[1], r[2]) and L[k][0] <= r[0]:
            top = L[k]
            k += 1
        if top is not None:
            by[(r[1], r[2])].append(r[0] - top[0])
    print(p)
    for k, v in by.items():
        v.sort()
        print("  %s->%s nested=%d backdate ms: min=%d median=%d p90=%d max=%d  >100ms: %d" % (k[0], k[1], len(v), v[0], v[len(v) // 2], v[int(0.9 * (len(v) - 1))], v[-1], sum(1 for x in v if x > 100)))
