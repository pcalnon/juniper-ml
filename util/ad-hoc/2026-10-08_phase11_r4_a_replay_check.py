#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/replay_check.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: replay round 3's pass on the four files at 7af6a381 in a scratch copy; compare with adcba49f."""
import hashlib
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
R = S / "replay"
FILES = [
    "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md",
    "reports/e2e-canopy-2026-09-02/f058-census-v2/README.md",
    "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py",
    "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py",
]
PASS = "util/ad-hoc/2026-10-08_phase11_ledger_round3_corrections.py"


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=W, check=True, capture_output=True).stdout


def main():
    for p in FILES + [PASS]:
        (R / p).parent.mkdir(parents=True, exist_ok=True)
    for p in FILES:
        (R / p).write_bytes(show("7af6a381", p))
    (R / PASS).write_bytes(show("adcba49f", PASS))
    r = subprocess.run([sys.executable, PASS, "--check"], cwd=R, capture_output=True, text=True)
    print("--check exit", r.returncode, r.stdout.strip(), r.stderr.strip())
    # --check must not write
    for p in FILES:
        assert (R / p).read_bytes() == show("7af6a381", p), f"--check wrote {p}"
    print("--check wrote nothing: OK")
    r = subprocess.run([sys.executable, PASS], cwd=R, capture_output=True, text=True)
    print("apply exit", r.returncode, r.stdout.strip(), r.stderr.strip())
    allok = True
    for p in FILES:
        got = (R / p).read_bytes()
        exp = show("adcba49f", p)
        wt = (W / p).read_bytes()
        same = got == exp
        allok &= same
        print(("IDENTICAL" if same else "DIFFERS"), p, hashlib.sha256(got).hexdigest()[:16], "worktree==adcba49f:", wt == exp, "len", len(got), len(exp))
    # second apply must refuse (idempotence guard)
    r = subprocess.run([sys.executable, PASS, "--check"], cwd=R, capture_output=True, text=True)
    print("re-apply --check exit", r.returncode, r.stdout.strip(), r.stderr.strip())
    print("ALL IDENTICAL" if allok else "MISMATCH")


if __name__ == "__main__":
    main()
