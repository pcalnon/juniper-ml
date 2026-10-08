# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11A1.4njt8I/lane_types.py
# Written by Lane 11-A1 (measurement re-creation, source-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import json, sys, collections
for p in sys.argv[1:]:
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    c = collections.Counter()
    for t, b, a, ty in raw["lane"]:
        c[(b, a, ty)] += 1
    print(p.rsplit("/", 1)[-1], "served", (d.get("served_sha") or "")[:8], "lane records", len(raw["lane"]), "fires", len(raw["fires"]), "gate", len(raw["gate"]), "errors", len(raw.get("errors", [])), "dispatches", raw.get("dispatches"))
    for k, v in sorted(c.items(), key=lambda kv: -kv[1]):
        print("   ", k, v)
    print("    any ON_PROP_CHANGE label:", any("ON_PROP_CHANGE" in (r[3] or "") for r in raw["lane"]))
