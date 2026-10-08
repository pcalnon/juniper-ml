#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/old_replay.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Run the alias replay as of 1b7cf44b on both transcripts (to check the round-1 record's 'were 2 to 4')."""
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path(__file__).resolve().parent
src = subprocess.run(["git", "show", "1b7cf44b:util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"], cwd=W, check=True, capture_output=True).stdout
p = S / "old_alias_replay_1b7cf44b.py"
p.write_bytes(src)
for t in ("reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json", "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json"):
    r = subprocess.run([sys.executable, "-B", str(p), f"{W}/{t}"], capture_output=True, text=True)
    print(t.split("/")[-2], "exit", r.returncode)
    for line in r.stdout.splitlines():
        if "6000" in line or "7500" in line or "5000" in line:
            print("  ", line)
