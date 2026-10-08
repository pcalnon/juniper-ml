#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/prescreen_ph11.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Run the prescreen on every Phase 11 script (added or modified since Phase 10's merge 200c1393)."""
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
files = [l for l in Path(__file__).with_name("ph10_scripts.txt").read_text().split() if l.endswith(".py")]
print(len(files), "files;", sum(1 for f in files if "phase11_r" in f), "lane probes")
r = subprocess.run([sys.executable, "util/ad-hoc/2026-10-05_codeql_python_prescreen.py"] + files, cwd=W, capture_output=True, text=True)
print(r.stdout[-1500:], r.stderr[-500:], "rc", r.returncode)
