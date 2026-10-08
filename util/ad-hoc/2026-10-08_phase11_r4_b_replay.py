#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/replay.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Replay round 3's pass on the four files at 7af6a381 in a mock root; compare to adcba49f byte for byte."""
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path(__file__).resolve().parent / "replay"
FILES = [
    "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md",
    "reports/e2e-canopy-2026-09-02/f058-census-v2/README.md",
    "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py",
    "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py",
]
SCRIPT = "util/ad-hoc/2026-10-08_phase11_ledger_round3_corrections.py"


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=W, check=True, capture_output=True).stdout


for f in FILES + [SCRIPT]:
    p = S / f
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(show("7af6a381" if f != SCRIPT else "adcba49f", f))

r = subprocess.run([sys.executable, str(S / SCRIPT)], cwd=S, capture_output=True, text=True)
print("pass stdout:", r.stdout.strip(), "| stderr:", r.stderr.strip(), "| rc:", r.returncode)
for f in FILES:
    got = (S / f).read_bytes()
    want = show("adcba49f", f)
    print(f, "MATCH" if got == want else f"MISMATCH ({len(got)} vs {len(want)})")
    # also compare against working tree (should equal adcba49f)
    wt = Path(W, f).read_bytes()
    print("   worktree == adcba49f:", wt == want)
