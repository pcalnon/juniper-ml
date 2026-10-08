#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/open_basis.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""For each OPEN finding, extract its entry block(s) and list lines mentioning CHANGELOG or a design/defects plan."""
import re
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
L = (W / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md").read_text().splitlines()
OPEN = ["F-CANOPY-055", "F-CANOPY-058", "F-CANOPY-064", "F-CANOPY-065", "F-CANOPY-068", "F-CASCOR-001", "F-CASCOR-002",
        "F-CANOPY-001", "F-CANOPY-012", "F-CANOPY-013", "F-CANOPY-018", "F-CANOPY-028", "F-CANOPY-032", "F-CANOPY-033",
        "F-CANOPY-034", "F-CANOPY-049", "F-CANOPY-051", "F-CANOPY-057", "F-CANOPY-060", "F-CANOPY-063", "F-CANOPY-066",
        "F-CANOPY-067", "F-ML-002"]
hdr = re.compile(r"^\*\*(F-[A-Z]+-\d+[a-z]?) — ")
starts = [(i, hdr.match(l).group(1)) for i, l in enumerate(L) if hdr.match(l)]
heads = [i for i, l in enumerate(L) if l.startswith("#")]
for fid in OPEN:
    for i, f in starts:
        if f != fid:
            continue
        # entry ends at next finding header or next markdown heading
        nxt = [j for j, _ in starts if j > i] + [h for h in heads if h > i] + [len(L)]
        end = min(nxt)
        block = L[i:end]
        hits = [(i + k + 1, ln.strip()[:170]) for k, ln in enumerate(block) if re.search(r"CHANGELOG|design plan|design-plan|_PLAN\.md|-PLAN|DESIGN\.md|defects plan", ln)]
        print(f"== {fid} (line {i+1}, {end-i} lines): {len(hits)} hits")
        for n, t in hits[:8]:
            print(f"   {n}: {t}")
