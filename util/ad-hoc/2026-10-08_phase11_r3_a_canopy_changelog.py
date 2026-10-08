#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/canopy_changelog.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Print canopy CHANGELOG.md lines 1218-1226 at 60ae1870 and the 0.6.0 toast promise lines 1975-1980 (read-only, object store)."""
import subprocess

C = "/home/pcalnon/Development/python/Juniper/juniper-canopy"
txt = subprocess.run(["git", "show", "60ae1870:CHANGELOG.md"], cwd=C, capture_output=True, text=True, check=True).stdout.splitlines()
for i in list(range(1217, 1226)) + [None] + list(range(1974, 1981)):
    if i is None:
        print("...")
        continue
    print(f"{i+1}: {txt[i][:240]}")
hdr = [i + 1 for i, l in enumerate(txt) if l.startswith("## [")]
print("release headers around:", [h for h in hdr if 900 < h < 2000][:12])
