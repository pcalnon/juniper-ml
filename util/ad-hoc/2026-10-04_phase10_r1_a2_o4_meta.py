# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/o4_meta.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""O4: installed juniper-canopy metadata version and editable flag in the running interpreter's env."""
import json
from importlib import metadata

d = metadata.distribution("juniper-canopy")
print("version:", d.version)
raw = d.read_text("direct_url.json")
if raw is None:
    print("direct_url.json: absent")
else:
    du = json.loads(raw)
    print("editable:", (du.get("dir_info") or {}).get("editable"))
    print("url is the primary canopy checkout:", du.get("url") == "file:///home/pcalnon/Development/python/Juniper/juniper-canopy")
