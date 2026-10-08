# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe5.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 5: nested-logging duplicates; raw lane records around late vs own releases."""
import importlib.util
import json
from collections import Counter

spec = importlib.util.spec_from_file_location("rt", "util/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

for name, path in [("run1", "ev/2026-10-05_census_live.json"), ("run2", "ev/run2/2026-10-05_census_live.json")]:
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    res = rt.analyze(d)
    own_ids = Counter(rid for _t, rid, _g in res["own"])
    print(f"=== {name}: own releases {len(res['own'])}, distinct requests {len(own_ids)}, max per request {max(own_ids.values())}")
    rel_t = Counter(t for t, b, a, ty in raw["lane"] if b is True and a is False and ty == "")
    print(f"  thunk True->False records sharing a millisecond: {sum(1 for v in rel_t.values() if v > 1)}")
    types = Counter(ty for _t, _b, _a, ty in raw["lane"])
    print(f"  lane record types: {types.most_common(8)}")
    # raw records within +-150 ms of the first two late releases and two own releases
    lane = raw["lane"]
    picks = [x["release_ms"] for x in res["late"][:2]] + [t for t, _r, _g in res["own"][100:102]]
    for p in picks:
        near = [rec for rec in lane if abs(rec[0] - p) <= 150]
        reqs = [rec for rec in raw["req"] if abs(rec[0] - p) <= 150]
        print(f"  around {p}: lane {near}; req {reqs}")
