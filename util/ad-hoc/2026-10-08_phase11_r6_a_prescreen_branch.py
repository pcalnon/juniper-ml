#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/prescreen_branch.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Run the CodeQL prescreen (as committed at da08f639) over every .py file the branch adds or changes, each taken
at da08f639 via `git show`, and also over the 7 pre-fix round-5 probes to show the screen fires."""
import importlib.util
import subprocess
import sys
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path("/tmp/tmp.y8saaB4Mk1")
spec = importlib.util.spec_from_file_location("prescreen", S / "cq/util/ad-hoc/2026-10-05_codeql_python_prescreen.py")
pre = importlib.util.module_from_spec(spec)
sys.modules["prescreen"] = pre
spec.loader.exec_module(pre)

out = S / "branch_tree"
files = (S / "branch_py.txt").read_text().split()
alerts = 0
for rel in files:
    data = subprocess.run(["git", "show", f"da08f639:{rel}"], cwd=W, capture_output=True, check=True).stdout
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    found = pre._scan(dst)
    if found:
        alerts += len(found)
        print(rel, found)
print(f"{len(files)} files at da08f639: {alerts} alerts")
pre_alerts = sum(len(pre._scan(p)) for p in (S / "cq_pre").glob("*.py"))
print(f"control: the 7 pre-fix round-5 probes: {pre_alerts} alerts")
