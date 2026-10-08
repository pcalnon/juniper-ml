# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11A1.4njt8I/write_pairs.py
# Written by Lane 11-A1 (measurement re-creation, source-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import json, sys, bisect
for p in sys.argv[1:]:
    with open(p) as fh:
        d = json.load(fh); raw = d["raw"]
    fires = [t for t, _b, _s in raw["fires"]]
    gate_false = [t for t, _b, v in raw["gate"] if v is False]
    gate_all = [(t, b, v) for t, b, v in raw["gate"]]
    thunk_off = sorted(t for t, b, a, ty in raw["lane"] if b is True and a is False and ty == "")
    outer_off = [(i, t) for i, (t, b, a, ty) in enumerate(raw["lane"]) if b is True and a is False and ty == "Callbacks.RemoveWatched+Callbacks.AddExecuted"]
    gaps = []
    for w in sorted(fires + gate_false):
        j = bisect.bisect_left(thunk_off, w)
        cands = [thunk_off[k] for k in (j - 1, j) if 0 <= k < len(thunk_off)]
        gaps.append(min((c - w for c in cands), key=abs) if cands else None)
    # order check: for each outer AddExecuted True->False record, is the immediately preceding lane record a '' True->False thunk?
    inner_first = 0
    for i, t in outer_off:
        prev = raw["lane"][i - 1] if i > 0 else None
        if prev and prev[1] is True and prev[2] is False and prev[3] == "" and prev[0] >= t:
            inner_first += 1
    print(p.rsplit("/", 1)[-1], "fires", len(fires), "gate writes", len(gate_all), "gate false", len(gate_false), "outer AddExecuted True->False", len(outer_off), "inner-thunk-logged-first-with-t>=outer", inner_first)
    print("   write -> nearest thunk True->False gap ms:", gaps)
