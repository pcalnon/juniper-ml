# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/check_lines.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens
# (CodeQL py/file-not-always-closed on juniper-ml#2157); what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py.
# ---------------------------------------------------------------------------
"""Print each line the Phase 10 text cites, so every reference can be eyeballed against its claim."""
import os
import sys

T = sys.argv[1]
REFS = [
    ("juniper-canopy/src/frontend/components/metrics_panel.py", [1951, 2259, 2264, 1664, 1610, 1624, 1015]),
    ("juniper-canopy/src/backend/cascor_service_adapter.py", [463, 479, 778, 1885, 1960, 1369, 1383, 1296, 1439]),
    ("juniper-canopy/src/backend/state_sync.py", [150]),
    ("juniper-canopy/src/frontend/dashboard_manager.py", [8404, 8410, 8442, 8443, 2365, 2366, 8359, 8381, 4149, 7798, 3260, 1329, 1331]),
    ("juniper-cascor/src/api/lifecycle/manager.py", [245, 4270, 2058, 2065, 2078, 2091, 2092, 2115, 2144, 2145, 5446, 5448, 4841]),
    ("juniper-cascor/src/api/lifecycle/monitor.py", [282, 298]),
    ("juniper-cascor/src/api/websocket/messages.py", [193]),
    ("juniper-cascor-client/juniper_cascor_client/ws_client.py", [822]),
    ("juniper-canopy/src/settings.py", [347]),
    ("juniper-canopy/src/backend/recurrence_backend.py", [58, 60, 163]),
    ("juniper-canopy/src/canopy_constants.py", [35, 48, 668, 674]),
    ("juniper-canopy/src/security.py", [378, 386, 391, 497]),
    ("juniper-canopy/src/tests/unit/test_security.py", [700]),
    ("juniper-canopy/src/main.py", [532, 1579, 1626]),
    ("juniper-canopy/src/tests/unit/frontend/test_n6_counter_semantics.py", [51]),
    ("juniper-canopy/src/tests/unit/frontend/test_dataset_shortfall_prompt.py", [36, 45]),
    ("juniper-data/juniper_data/core/limits.py", [135, 149, 168]),
    ("juniper-canopy/docs/USER_MANUAL.md", [266, 271, 293]),
]
for rel, lines in REFS:
    with open(os.path.join(T, rel), encoding="utf-8") as fh:
        src = fh.read().splitlines()
    for n in lines:
        print(f"{rel.split('/', 1)[1]}:{n}: {src[n - 1].strip()[:150]}")
