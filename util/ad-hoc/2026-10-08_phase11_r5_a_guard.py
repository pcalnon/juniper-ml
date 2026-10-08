#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R5A.LBVRcz/guard.py
# Written by Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R5A: drop one innermost lane record from a copy of each transcript and record the exit codes of the
trace's report, its --self-test and the replay (the round-3 record's 'Of the trace's two modes, only the report
exits 2 ..., while the replay refuses too'). Also the unmutated exit codes. Prints exit codes and counts only."""
import json
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
TRACE = W / "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py"
REPLAY = W / "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"
for rel in ("reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json", "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json"):
    d = json.loads((W / rel).read_text(encoding="utf-8"))
    inner = [i for i, r in enumerate(d["raw"]["lane"]) if r[3] in ("", "SET_LAYOUT")]
    k = inner[len(inner) // 2]
    mut = json.loads(json.dumps(d))
    del mut["raw"]["lane"][k]
    mp = S / f"mut_{rel.split('/')[-2]}.json"
    mp.write_text(json.dumps(mut), encoding="utf-8")
    for label, path in (("orig", W / rel), ("mut", mp)):
        rc = {}
        for name, cmd in (("report", [sys.executable, "-B", str(TRACE), str(path)]), ("self-test", [sys.executable, "-B", str(TRACE), str(path), "--self-test"]), ("replay", [sys.executable, "-B", str(REPLAY), str(path), "--seeds", "1", "--step", "500"])):
            r = subprocess.run(cmd, cwd=S, capture_output=True, text=True)
            rc[name] = r.returncode
        print(rel.split("/")[-2], label, f"innermost records {len(inner)}", rc)
