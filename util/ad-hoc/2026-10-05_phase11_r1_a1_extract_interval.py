# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11A1.4njt8I/extract_interval.py
# Written by Lane 11-A1 (measurement re-creation, source-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
import json
base = "/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/dash/dcc/"
for name in ("dash_core_components.js.map", "dash_core_components-shared.js.map"):
    with open(base + name) as f:
        m = json.load(f)
    srcs = m.get("sources", [])
    content = m.get("sourcesContent") or []
    for i, s in enumerate(srcs):
        if "Interval" in s:
            print("==", name, i, s, "has content:", i < len(content) and content[i] is not None)
            if i < len(content) and content[i]:
                print(content[i])
