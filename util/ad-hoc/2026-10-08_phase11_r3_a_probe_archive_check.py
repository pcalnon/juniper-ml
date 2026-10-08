#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/probe_archive_check.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Are the 16 round-2 archived probes (at 7af6a381) verbatim copies of the lanes' tmpfs sources (body after the header)?"""
import re
import subprocess
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
SCR = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad")
lanes = {
    "a": ("lane11R2A.sffLXI", ["horizon.py", "jitter_dist.py", "jitter_dist_old.py", "myreader.py", "myreplay.py", "selftest_on_old.py", "stall.py", "trig.py", "types.py"]),
    "b": ("lane11R2B.ChB7s3/tools", ["a_to_w.py", "pairing_blindspot.py", "peek.py", "peek2.py", "reenables.py", "replay_pass.py", "x_to_w.py"]),
}
listed = subprocess.run(["git", "ls-tree", "--name-only", "7af6a381", "util/ad-hoc/"], cwd=W, capture_output=True, text=True, check=True).stdout.split()
r2 = sorted(p for p in listed if re.match(r"util/ad-hoc/2026-10-05_phase11_r2_[ab]_", p))
print("r2 files in tree:", len(r2))
ok = bad = missing = 0
for lane, (d, names) in lanes.items():
    for n in names:
        arch = f"util/ad-hoc/2026-10-05_phase11_r2_{lane}_{n}"
        if arch not in r2:
            print("NOT IN TREE", arch)
            bad += 1
            continue
        a = subprocess.run(["git", "show", f"7af6a381:{arch}"], cwd=W, capture_output=True, text=True, check=True).stdout
        src = SCR / d / n
        if not src.exists():
            missing += 1
            continue
        body = src.read_text(encoding="utf-8")
        if body.startswith("#!"):
            body = body.split("\n", 1)[1]
        if a.endswith(body) and "a probe from round 2" in a:
            ok += 1
        else:
            bad += 1
            print("DIFFERS", arch)
print(f"verbatim {ok}, differing {bad}, source gone {missing}; extra in tree: {sorted(set(r2) - {f'util/ad-hoc/2026-10-05_phase11_r2_{l}_{n}' for l, (_, ns) in lanes.items() for n in ns})}")
