#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/break_test.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Mutate copies of transcript 1 to (i) one alternation break, (ii) a dropped pair with no break; run both readers at 7af6a381."""
import copy
import json
import subprocess
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
S = Path(__file__).resolve().parent
T1 = W / "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json"
RT = W / "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py"
AR = W / "util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py"
d = json.loads(T1.read_text())
lane = d["raw"]["lane"]
inner_idx = [i for i, rec in enumerate(lane) if rec[3] in ("", "SET_LAYOUT")]
inner_idx.sort(key=lambda i: (lane[i][0], i))
mid = inner_idx[len(inner_idx) // 2]

# (i) drop one innermost record -> a break
m1 = copy.deepcopy(d)
m1["raw"]["lane"] = [rec for i, rec in enumerate(lane) if i != mid]
p1 = S / "mut_break.json"
p1.write_text(json.dumps(m1))
# (ii) drop two consecutive innermost records (a full disable/enable pair) -> no break, but a hole
k = inner_idx.index(mid)
pair = {inner_idx[k], inner_idx[k + 1]}
m2 = copy.deepcopy(d)
m2["raw"]["lane"] = [rec for i, rec in enumerate(lane) if i not in pair]
p2 = S / "mut_pairdrop.json"
p2.write_text(json.dumps(m2))
print("dropped (i):", lane[mid][:4], " (ii):", [lane[i][:4] for i in sorted(pair)])
for name, p in (("one-record drop", p1), ("pair drop", p2)):
    r = subprocess.run([sys.executable, "-B", str(RT), str(p)], capture_output=True, text=True)
    first = [ln for ln in r.stdout.splitlines()[:4]]
    print(f"[{name}] release trace exit {r.returncode}:", " | ".join(first))
    r = subprocess.run([sys.executable, "-B", str(RT), str(p), "--self-test"], capture_output=True, text=True)
    print(f"[{name}] release trace --self-test exit {r.returncode}: {r.stdout.splitlines()[-1] if r.stdout else r.stderr[-200:]}")
    r = subprocess.run([sys.executable, "-B", str(AR), str(p)], capture_output=True, text=True)
    print(f"[{name}] alias replay exit {r.returncode}: stderr={r.stderr.strip()[:160]!r} stdout_lines={len(r.stdout.splitlines())}")
