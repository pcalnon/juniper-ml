# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/p1_headers.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Print the first '(P1…' parenthetical of each open P1 header in the 7af6a381 ledger copy."""
import re

with open("/tmp/tmp.cIFAKjB6BD/7af/ledger.md", encoding="utf-8") as fh:
    text = fh.read()
for fid in ["F-CANOPY-055", "F-CANOPY-058", "F-CANOPY-064", "F-CANOPY-065", "F-CANOPY-068", "F-CASCOR-001", "F-CASCOR-002"]:
    m = re.search(r"^\*\*" + re.escape(fid) + r" — (.*?)\*\*", text, re.M | re.S)
    body = " ".join(m.group(1).split())
    p = re.search(r"\(P1[^;)]*", body)
    print(fid, "->", p.group(0) if p else "(no '(P1' parenthetical)")
