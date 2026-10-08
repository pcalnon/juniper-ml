#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/stage_cq.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Stage the archiver, the CodeQL fix pass and the prescreen at da08f639 into a scratch tree, plus the committed
round-5 probes, all via `git show <rev>:<path>` run from the worktree (read-only)."""
import subprocess
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite"
S = Path("/tmp/tmp.y8saaB4Mk1")


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=W, capture_output=True, check=True).stdout


for name in ["2026-10-05_archive_phase11_lane_probes.py", "2026-10-05_phase11_probes_codeql_fixes.py", "2026-10-05_codeql_python_prescreen.py"]:
    (S / "cq/util/ad-hoc" / name).write_bytes(show("da08f639", f"util/ad-hoc/{name}"))
names = subprocess.run(["git", "ls-tree", "--name-only", "da08f639", "util/ad-hoc/"], cwd=W, capture_output=True, text=True, check=True).stdout.split()
r5 = [n for n in names if "_phase11_r5_" in n]
for n in r5:
    (S / "committed_r5" / Path(n).name).write_bytes(show("da08f639", n))
print(len(r5), "committed r5 probes:", [Path(n).name for n in r5])
