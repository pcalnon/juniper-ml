#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/replay.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R3A: replay round 2's pass (at 7af6a381) on both files at b3c54692; compare to 7af6a381 byte for byte."""
import hashlib
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path(__file__).resolve().parent
LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
README = "reports/e2e-canopy-2026-09-02/f058-census-v2/README.md"
PASS = "util/ad-hoc/2026-10-05_phase11_ledger_round2_corrections.py"


def show(rev: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=W, check=True, capture_output=True).stdout


root = S / "replay"
for rel, rev in ((LEDGER, "b3c54692"), (README, "b3c54692"), (PASS, "7af6a381")):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(show(rev, rel))

r = subprocess.run([sys.executable, str(root / PASS)], capture_output=True, text=True)
print("pass stdout:", r.stdout.strip(), "| stderr:", r.stderr.strip(), "| exit:", r.returncode)

for rel in (LEDGER, README):
    got = (root / rel).read_bytes()
    want = show("7af6a381", rel)
    print(rel, "IDENTICAL" if got == want else "DIFFERS", hashlib.sha256(got).hexdigest()[:16], hashlib.sha256(want).hexdigest()[:16], len(got), len(want))
    if got != want:
        import difflib
        for line in difflib.unified_diff(want.decode().splitlines(), got.decode().splitlines(), "7af6a381", "replayed", lineterm="", n=1):
            print(line)

# Also: second run must refuse (guard) -- idempotence check
r2 = subprocess.run([sys.executable, str(root / PASS), "--check"], capture_output=True, text=True)
print("re-run on output:", r2.stdout.strip(), r2.stderr.strip(), "exit", r2.returncode)
