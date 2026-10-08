#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/canopy_changelog_057.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Does canopy's CHANGELOG (at 60ae1870 and c7876f5a) promise the CAN-015g replay-weight stream? Read-only, object store.

Prints only matching CHANGELOG lines (truncated), with the release section each falls under.
"""
import re
import subprocess

C = "/home/pcalnon/Development/python/Juniper/juniper-canopy"
PAT = re.compile(r"V2 weight|weight payload|weight buffer|weight ring|per-epoch weight|weight history|decision.boundary anim", re.I)
for rev in ("60ae1870", "c7876f5a"):
    txt = subprocess.run(["git", "show", f"{rev}:CHANGELOG.md"], cwd=C, capture_output=True, text=True, check=True).stdout.splitlines()
    section = None
    hits = []
    for i, line in enumerate(txt, 1):
        if line.startswith("## ["):
            section = line.strip()
        if PAT.search(line):
            hits.append((i, section, line.strip()[:200]))
    print(f"{rev}: {len(hits)} matching lines")
    for h in hits:
        print(f"  {h[0]} [{h[1]}] {h[2]}")
