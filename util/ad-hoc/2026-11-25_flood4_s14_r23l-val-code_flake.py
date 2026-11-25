"""
Repeat-run carrier r23l's lifecycle tests in separate pytest processes, optionally at a tiny GIL switch interval.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23l-val-code: independent validation of carrier r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Each repetition is its own process (a child of this script) that sets ``sys.setswitchinterval`` when asked and
then runs ``pytest.main`` on the given test files from ``--cwd`` with a JUnit report, so a flake shows up as a
failing test id in one run. At most ``--jobs`` children run at once (capped at 4).

Usage: python <this file> --python <venv>/bin/python --cwd <clone>/juniper-service-core --scratch DIR --json-out FILE
       --tests tests/a.py,tests/b.py [--repeat 50] [--switch-interval 1e-6] [--jobs 4]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def child(argv: list[str]) -> int:
    interval = float(argv[0])
    if interval > 0:
        sys.setswitchinterval(interval)
    import pytest

    return int(pytest.main(argv[1:]))


def one(index: int, args: argparse.Namespace) -> dict:
    run_dir = Path(args.scratch) / f"run{index:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    junit = run_dir / "junit.xml"
    cmd = [args.python, __file__, "--child", str(args.switch_interval or 0.0), "-p", "no:cacheprovider", "-q", f"--junitxml={junit}", f"--basetemp={run_dir / 'basetemp'}", *args.tests.split(",")]
    proc = subprocess.run(cmd, cwd=args.cwd, capture_output=True, text=True, check=False, timeout=600)
    failed, passed = [], 0
    if junit.is_file():
        for case in ET.parse(junit).getroot().iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                failed.append(f"{case.get('classname')}::{case.get('name')}")
            elif case.find("skipped") is None:
                passed += 1
    if proc.returncode != 0:
        (run_dir / "pytest.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {"run": index, "exit": proc.returncode, "passed": passed, "failed": failed}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        return child(sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--python", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--repeat", type=int, default=50)
    parser.add_argument("--switch-interval", type=float, default=None)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        runs = list(pool.map(lambda i: one(i, args), range(args.repeat)))
    flaky = sorted({test for run in runs for test in run["failed"]})
    out = {
        "python": args.python,
        "switch_interval": args.switch_interval,
        "repeat": args.repeat,
        "tests": args.tests.split(","),
        "runs_ok": sum(1 for run in runs if run["exit"] == 0),
        "tests_passed_total": sum(run["passed"] for run in runs),
        "tests_failed_total": sum(len(run["failed"]) for run in runs),
        "failing_tests": flaky,
        "runs": runs,
    }
    Path(args.json_out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
