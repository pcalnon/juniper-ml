#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R5A.LBVRcz/prescreen_branch.py
# Written by Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R5A: run the prescreen (684d70bc copy) on every Python file the branch adds or changes
(200c1393..684d70bc), reading each file's 684d70bc content from git into a scratch tree; also its
--known-answer. Prints counts and any alert lines."""
import importlib.util
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
files = [x for x in (S / "branch_py.txt").read_text().splitlines() if x.strip()]
tree = S / "branch_tree"
tree.mkdir(exist_ok=True)
paths = []
for f in files:
    blob = subprocess.run(["git", "show", f"684d70bc:{f}"], cwd=W, check=True, capture_output=True).stdout
    dst = tree / f
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(blob)
    # the worktree copy must equal 684d70bc's (the worktree is clean)
    if (W / f).read_bytes() != blob:
        print("WORKTREE DIFFERS:", f)
    paths.append(dst)
spec = importlib.util.spec_from_file_location("prescreen", S / "cq" / "util" / "ad-hoc" / "2026-10-05_codeql_python_prescreen.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
total = 0
for p in paths:
    left = mod._scan(p)
    if left:
        total += len(left)
        print(p.relative_to(tree), left)
print(f"{total} predicted alert(s) in {len(paths)} file(s)")
