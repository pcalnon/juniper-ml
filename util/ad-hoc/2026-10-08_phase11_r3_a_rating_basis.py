#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/rating_basis.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""For each OPEN finding, print header parenthetical and every line of its entry that bears on its rating basis."""
import re
import sys
from pathlib import Path

L = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md")
lines = L.read_text().splitlines()
ids = sys.argv[1:]
hdr = re.compile(r"^\*\*(F-[A-Z0-9]+-\d{3}) — ")
starts = [(i, hdr.match(l).group(1)) for i, l in enumerate(lines) if hdr.match(l)]
KEY = re.compile(r"CHANGELOG|design.plan|documented|manual|REFERENCE|promise|§6\.3|Severity|Rating|rating|P1|P2", re.I)
for fid in ids:
    occ = [i for i, f in starts if f == fid]
    for i in occ:
        nxt = min([j for j, _ in starts if j > i] + [len(lines)])
        # stop at next heading too
        for k in range(i + 1, nxt):
            if lines[k].startswith("#"):
                nxt = k
                break
        h = lines[i]
        par = h[h.rfind("("):] if "(" in h else h[-200:]
        print(f"=== {fid} @ line {i+1} (entry {nxt - i} lines): header tail: {par[-330:]}")
        for k in range(i + 1, nxt):
            if KEY.search(lines[k]) and re.search(r"CHANGELOG|design.plan|documented|manual|REFERENCE|promise|§6\.3|Severity|Rating", lines[k]):
                print(f"   {k+1}: {lines[k][:220]}")
