#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/readers_compare.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A CHECK 6: run both readers (report, and the trace's --self-test) at 7af6a381 and at adcba49f on both
transcripts, from scratch copies (no bytecode written), and compare stdout, stderr and exit codes."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
TRACE = "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py"
REPLAY = "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"
T = [W / "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json", W / "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json"]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

for rev in ("7af6a381", "adcba49f"):
    d = S / f"readers_{rev}"
    d.mkdir(exist_ok=True)
    for p in (TRACE, REPLAY):
        (d / Path(p).name).write_text(subprocess.run(["git", "show", f"{rev}:{p}"], cwd=W, capture_output=True, text=True, check=True).stdout)

runs = []
for tr in T:
    tag = "run2" if "run2" in str(tr) else "run1"
    runs.append((f"trace report {tag}", Path(TRACE).name, [str(tr)]))
    runs.append((f"trace --self-test {tag}", Path(TRACE).name, [str(tr), "--self-test"]))
    runs.append((f"replay {tag}", Path(REPLAY).name, [str(tr)]))

for label, script, argv in runs:
    outs = {}
    for rev in ("7af6a381", "adcba49f"):
        r = subprocess.run([sys.executable, "-B", str(S / f"readers_{rev}" / script), *argv], capture_output=True, text=True, env=env)
        outs[rev] = (r.returncode, r.stdout, r.stderr)
        (S / f"out_{rev}_{label.replace(' ', '_')}.txt").write_text(f"exit {r.returncode}\n--stdout--\n{r.stdout}\n--stderr--\n{r.stderr}")
    a, b = outs["7af6a381"], outs["adcba49f"]
    same = a == b
    print(f"{'IDENTICAL' if same else 'DIFFERENT'}  {label}: exit {a[0]}/{b[0]}  stdout sha {hashlib.sha256(b[1].encode()).hexdigest()[:12]} ({len(b[1].splitlines())} lines)  stderr {len(b[2])} chars")
