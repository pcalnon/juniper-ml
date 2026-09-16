#!/usr/bin/env python3
"""Push the round-39 ad-hoc scripts onto the open juniper-ml PR branch as one signed commit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1947

A script rather than a shell loop because a worktree-isolated session refuses a command that builds
``gh``/``git`` arguments at runtime -- exactly the trap the round-39 handoff's 5.13 records.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "docs/register-round-39-validated"

TOP_LEVEL = (
    "register_close_data395.py",
    "register_file_047_to_049.py",
    "register_round39_head_typo.py",
    "register_round39_park_sentences.py",
    "register_file_data_052_truncation_optout.py",
    "register_fix_canopy_valratio_closure_claim.py",
    "register_round39_apply_round2_lanes.py",
    "register_round39_cite_validation_record.py",
    "handoff_round39_apply_laneB2.py",
    "handoff_round39_apply_lanesA_B1.py",
    "2026-09-15_compare_outlier_basis_designs.py",
    "2026-09-15_verify_lower_median_over_cache.py",
    "2026-09-15_ecosystem_agents_md_generator_version_5.py",
    "push_round39_adhoc_scripts.py",
)
NESTED = ("probe_stage1.py", "stage1_fetch_shares.py", "stage3_tests.py", "stage5_version_bump.py")

args: list[str] = [
    sys.executable,
    str(ROOT / "util/ad-hoc/2026-08-26_push_signed_fixup.py"),
    "--repo",
    "juniper-ml",
    "--branch",
    BRANCH,
]
for name in TOP_LEVEL:
    local = ROOT / "util/ad-hoc" / name
    if not local.exists():
        sys.exit(f"missing: {local}")
    args += ["--add", f"{local}:util/ad-hoc/{name}"]
for name in NESTED:
    local = ROOT / "util/ad-hoc/2026-09-11_equities_rulings" / name
    if not local.exists():
        sys.exit(f"missing: {local}")
    args += ["--add", f"{local}:util/ad-hoc/2026-09-11_equities_rulings/{name}"]

args += [
    "--message",
    "chore(ad-hoc): the round-39 register, handoff and measurement scripts",
    "--commit-body",
    "Eighteen scripts, retained as provenance of record per the owner policy of 2026-08-25.\n"
    "\n"
    "Three are worth naming. 2026-09-15_compare_outlier_basis_designs.py is the only\n"
    "instrument that separates the three candidate outlier bases -- the real cache cannot,\n"
    "and 2026-09-15_verify_lower_median_over_cache.py is the whole-cache equivalence check\n"
    "that proves it cannot. 2026-09-15_ecosystem_agents_md_generator_version_5.py is the\n"
    "ONLY record of a change to Juniper/AGENTS.md, which is not in a git repository and so\n"
    "carries no PR, no CI and no history of its own.\n"
    "\n"
    "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
]

print(f"pushing {len(TOP_LEVEL) + len(NESTED)} files to {BRANCH}")
raise SystemExit(subprocess.run(args, check=False).returncode)
