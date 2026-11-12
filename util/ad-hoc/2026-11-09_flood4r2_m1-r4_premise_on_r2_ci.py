#!/usr/bin/env python3
"""
Run round 4's test_gitleaks_config.py against round 2's ci.yml (the premise: each new test must fail there), then restore ci.yml byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (round 4 of the juniper-data pull-request Gitleaks fix: findings R3-01 and R3-02)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
A new test that passes against the workflow it was written to fix pins nothing. This script copies round 2's ci.yml
(the pre-round-4 snapshot) over the carrier's, runs the whole test file with the official engine through
2026-11-09_flood4r2_m1-r4_run_pytest.py, and restores the carrier's ci.yml in a finally block, checking its sha256
against the value read before the swap. It prints the junit verdict for each round-4 test and exits 1 unless every
one of them failed and every other test passed.

Usage:
    python3 <this> --worktree <juniper-data worktree> --r2-ci <pre-round-4 ci.yml> --out <r4 dir> --official <gitleaks 8.24.3>
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess  # nosec B404 - fixed argv: python3 running the round-4 pytest runner
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the junit file pytest itself just wrote
from pathlib import Path

RUNNER = Path(__file__).resolve().parent / "2026-11-09_flood4r2_m1-r4_run_pytest.py"
NEW_TESTS = (
    "test_the_scan_step_refuses_an_octopus_merge",
    "test_the_scan_step_gives_the_engine_a_git_without_remerge_notes",
    "test_real_engine_scan_step_keeps_a_merge_findings_commit_and_path[conflicted-path]",
    "test_real_engine_scan_step_keeps_a_merge_findings_commit_and_path[parent-subject]",
)
TAG = "_premise-on-r2-ci-final"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--r2-ci", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--official", type=Path, required=True)
    args = ap.parse_args()
    ci = args.worktree / ".github" / "workflows" / "ci.yml"
    before = sha256(ci)
    saved = ci.read_bytes()
    try:
        shutil.copyfile(args.r2_ci, ci)
        print(f"swapped in round 2's ci.yml ({sha256(ci)}), carrier's was {before}")
        runner_exit = subprocess.run([sys.executable, str(RUNNER), "--worktree", str(args.worktree), "--out", str(args.out), "--mode", "real-official", "--official", str(args.official), "--tag", TAG], check=False).returncode  # nosec B603
    finally:
        ci.write_bytes(saved)
    after = sha256(ci)
    print(f"restored: {after} ({'identical' if after == before else 'DIFFERENT'}); runner exit {runner_exit}")
    root = ET.parse(args.out / "logs" / f"junit_real-official{TAG}.xml").getroot()  # nosec B314 - pytest's own output
    verdict = {}
    for case in root.iter("testcase"):
        red = case.find("failure") is not None or case.find("error") is not None
        verdict[case.get("name", "")] = "FAILED" if red else ("skipped" if case.find("skipped") is not None else "passed")
    for name in NEW_TESTS:
        print(f"  {verdict.get(name, 'MISSING'):<7} {name}")
    others = {n: v for n, v in verdict.items() if n not in NEW_TESTS}
    print(f"  other tests: {sum(v == 'passed' for v in others.values())} passed, {sum(v != 'passed' for v in others.values())} not")
    ok = after == before and all(verdict.get(n) == "FAILED" for n in NEW_TESTS) and all(v == "passed" for v in others.values())
    print("PREMISE HOLDS" if ok else "PREMISE DOES NOT HOLD")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
