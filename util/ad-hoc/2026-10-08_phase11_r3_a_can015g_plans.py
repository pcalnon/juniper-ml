#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/can015g_plans.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Where do design/plan documents mention CAN-015g? canopy c7876f5a (notes/, docs/) and juniper-ml 7af6a381 (notes/). Read-only."""
import subprocess

for repo, rev, paths in (
    ("/home/pcalnon/Development/python/Juniper/juniper-canopy", "c7876f5a", ["notes", "docs"]),
    ("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite", "7af6a381", ["notes"]),
):
    r = subprocess.run(["git", "grep", "-n", "-i", "-I", "CAN-015g", rev, "--", *paths], cwd=repo, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if "E2E-VALIDATION-EVIDENCE" not in l]
    files = {}
    for l in lines:
        f = l.split(":", 2)[1]
        files[f] = files.get(f, 0) + 1
    print(repo.split("/")[-1] if "worktrees" not in repo else "juniper-ml", rev, "files mentioning CAN-015g (excluding the E2E ledger):")
    for f, n in sorted(files.items()):
        print(f"  {n:3d}  {f}")
