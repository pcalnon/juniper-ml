#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/canopy_manual.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Read-only: locate step 6 of canopy's Network Editor workflow in docs/USER_MANUAL.md at several commits."""
import subprocess
import sys

CANOPY = "/home/pcalnon/Development/python/Juniper/juniper-canopy"


def git(*args):
    return subprocess.run(["git", "-C", CANOPY, *args], capture_output=True, text=True, check=True).stdout


NEEDLE = "Use the API response shown in the status alert to confirm the edit"
for rev in ["3411673c", "28da69f8^", "60ae1870", "c7876f5a", "359e1bf7^", "359e1bf7"]:
    full = git("rev-parse", "--short=8", rev).strip()
    try:
        text = git("show", f"{rev}:docs/USER_MANUAL.md")
    except subprocess.CalledProcessError as e:
        print(rev, full, "NO FILE", e.stderr.strip()[:100])
        continue
    lines = text.splitlines()
    hits = [i + 1 for i, ln in enumerate(lines) if NEEDLE in ln]
    print(f"== {rev} ({full}): hits at {hits}")
    for h in hits:
        lo = max(1, h - 20)
        if "-v" in sys.argv:
            for j in range(lo, h + 3):
                print(f"  {j}: {lines[j-1]}")
        else:
            print(f"  {h}: {lines[h-1]}")
