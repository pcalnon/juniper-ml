# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B1.oCpUdY/logconn.py
# Written by Lane 11-B1 (adversarial, dispositions and ratings, fold side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Print only the timestamp prefix and the matched phrase for WS connect/disconnect lines (no other line content)."""
import re
import sys
from pathlib import Path

pat = re.compile(r"(Client (?:connected|disconnected): (?:training|control)-client)")
for i, line in enumerate(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
    m = pat.search(line)
    if m:
        ts = re.match(r"^\S+\s+\S+", line)
        print(i, ts.group(0)[:32] if ts else "", m.group(1))
