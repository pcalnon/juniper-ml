# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/report_lengths.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: lengths of the two round-5 report bodies against the char counts their headers state."""

import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
P = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md")
text = P.read_text(encoding="utf-8")
parts = re.split(r"\n## ", text)
for part in parts[1:]:
    title, rest = part.split("\n", 1)
    m = re.search(r"\*agent `([0-9a-f]+)` · .*? · (\d+) chars\*\n\n", rest)
    body = rest[m.end():]
    body = body.split("\n---\n")[0]
    stated = int(m.group(2))
    for cand in (body, body.rstrip("\n"), body.strip()):
        print(f"{title[:40]!r}: stated {stated}, body {len(cand)} chars")
