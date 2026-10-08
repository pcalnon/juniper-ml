#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/codeql_replay.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: replay the CodeQL fix pass in scratch.

Tree: $S/cq/util/ad-hoc/ holding the adcba49f archiver, prescreen and fix pass; the round-1/2 probes as frozen at
7af6a381; round 3's probes rebuilt by the archiver (--round 3) from the lanes' scratch sources. Then the fix pass
is run there, and every round-1/2/3 probe is compared byte for byte with adcba49f.
"""
import os
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
CQ = S / "cq" / "util" / "ad-hoc"
CQ.mkdir(parents=True, exist_ok=True)
(S / "cq" / "notes").mkdir(exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def git(*a):
    return subprocess.run(["git", *a], cwd=W, check=True, capture_output=True, text=True).stdout


for name in ("2026-10-05_archive_phase11_lane_probes.py", "2026-10-05_codeql_python_prescreen.py", "2026-10-05_phase11_probes_codeql_fixes.py"):
    (CQ / name).write_text(git("show", f"adcba49f:util/ad-hoc/{name}"))
r12 = [l for l in git("ls-tree", "--name-only", "7af6a381", "util/ad-hoc/").splitlines() if "_phase11_r1_" in l or "_phase11_r2_" in l]
for p in r12:
    (CQ / Path(p).name).write_text(git("show", f"7af6a381:{p}"))
r = subprocess.run([sys.executable, "-B", str(CQ / "2026-10-05_archive_phase11_lane_probes.py"), "--round", "3"], capture_output=True, text=True, env=env)
print("archiver --round 3 exit", r.returncode, "|", r.stdout.strip().count("wrote"), "files |", r.stderr.strip()[:200])
r = subprocess.run([sys.executable, "-B", str(CQ / "2026-10-05_phase11_probes_codeql_fixes.py")], capture_output=True, text=True, env=env)
print("fix pass exit", r.returncode, "|", r.stdout.strip().splitlines()[-2:] if r.stdout.strip() else "", "|", r.stderr.strip()[:300])
allp = [l for l in git("ls-tree", "--name-only", "adcba49f", "util/ad-hoc/").splitlines() if "_phase11_r1_" in l or "_phase11_r2_" in l or "_phase11_r3_" in l]
same = diff = missing = 0
for p in allp:
    q = CQ / Path(p).name
    if not q.exists():
        missing += 1
        print("MISSING", p)
        continue
    if q.read_text() == git("show", f"adcba49f:{p}"):
        same += 1
    else:
        diff += 1
        print("DIFFERS", p)
print(f"probes at adcba49f: {len(allp)}; identical after replay {same}; differing {diff}; missing {missing}")
