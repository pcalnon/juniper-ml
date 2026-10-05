# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/probe_o4.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Read juniper-canopy's installed metadata in the active env (no secrets, no env vars printed)."""
import importlib.metadata as md
import json

d = md.distribution("juniper-canopy")
print("version:", d.version)
direct = d.read_text("direct_url.json")
if direct:
    info = json.loads(direct)
    print("editable:", info.get("dir_info", {}).get("editable"), "url:", info.get("url"))
else:
    print("direct_url.json: absent")
