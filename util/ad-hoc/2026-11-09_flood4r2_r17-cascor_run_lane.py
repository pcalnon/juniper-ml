#!/usr/bin/env python3
"""
Run one juniper-cascor CI test lane (unit + coverage gate, or quick integration) on a checkout, with provenance.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rules 11 and 14; juniper-cascor .github/workflows/ci.yml
         ("Run Unit Tests", "Enforce Coverage Gate (80%)", "Run Quick Integration Tests")

Mirrors ci.yml's commands from the checkout root, minus ``--maxfail`` (every failure counts), plus
``--junitxml`` into the output directory, ``-p no:cacheprovider`` and a one-function provenance
plugin that prints the ``__file__`` pytest resolved for ``api.lifecycle.manager``. A run whose
provenance is not the checkout's own ``src/api/lifecycle/manager.py`` is reported as such.
``JUNIPER_CASCOR_LOG_DIR`` is dropped from the environment (six tests assert its unset fallback).

Usage:
  2026-11-09_flood4r2_r17-cascor_run_lane.py --tree <checkout> --lane unit|integration --label <name> --out <dir>
Writes <out>/<lane>-<label>.log, .xml (JUnit) and .json (exit codes, counts, failing ids, provenance).
Exit: the pytest exit code (the unit lane: nonzero also when the coverage gate fails).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 -- fixed-argv pytest and coverage runs
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses the JUnit file this run just wrote
from pathlib import Path

PLUGIN_NAME = "_r17_lane_provenance"
PLUGIN_SOURCE = """import sys


def pytest_sessionfinish(session, exitstatus):
    module = sys.modules.get("api.lifecycle.manager")
    print("\\nPROVENANCE " + str(getattr(module, "__file__", None)))
"""


def _junit_summary(path: Path) -> dict:
    """Count the JUnit file's outcomes and list the ids of the failed and errored tests."""
    root = ET.parse(path).getroot()  # nosec B314 -- our own pytest output
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    failing = []
    for case in root.iter("testcase"):
        counts["tests"] += 1
        test_id = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None:
            counts["failures"] += 1
            failing.append(test_id)
        elif case.find("error") is not None:
            counts["errors"] += 1
            failing.append(test_id)
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    return {"counts": counts, "failing": failing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="the juniper-cascor checkout to test")
    parser.add_argument("--lane", required=True, choices=("unit", "integration"))
    parser.add_argument("--label", required=True, help="a name for this run's files")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    args = parser.parse_args()
    tree = args.tree.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    plugin_dir = out / "_plugins"
    plugin_dir.mkdir(exist_ok=True)
    (plugin_dir / f"{PLUGIN_NAME}.py").write_text(PLUGIN_SOURCE, encoding="utf-8")
    for relative in ("logs", "src/logs", "src/tests/reports"):
        (tree / relative).mkdir(parents=True, exist_ok=True)

    stem = f"{args.lane}-{args.label}"
    junit = out / f"{stem}.xml"
    common = ["-p", "no:cacheprovider", "-p", PLUGIN_NAME, f"--junitxml={junit}"]
    if args.lane == "unit":
        argv = [sys.executable, "-m", "pytest", "-m", "unit and not slow", "src/tests/unit", "--verbose", "--timeout=60", "--cov=src", "--cov-report=term-missing", f"--cov-report=xml:{out / f'coverage-{args.label}.xml'}", *common]
    else:
        argv = [sys.executable, "-m", "pytest", "--integration", "-m", "integration and not slow", "src/tests/integration", "--timeout=60", "-q", *common]
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    env["PYTHONPATH"] = str(plugin_dir)

    log = out / f"{stem}.log"
    with log.open("w", encoding="utf-8") as handle:
        handle.write(f"$ (cwd {tree}) {' '.join(argv)}\n")
        handle.flush()
        proc = subprocess.run(argv, cwd=tree, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)  # nosec B603 -- fixed argv
        handle.write(f"\n[pytest exit {proc.returncode}]\n")
        gate_code = None
        if args.lane == "unit":
            handle.write("\n$ python -m coverage report --fail-under=80\n")
            handle.flush()
            gate = subprocess.run([sys.executable, "-m", "coverage", "report", "--fail-under=80"], cwd=tree, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)  # nosec B603 -- fixed argv
            gate_code = gate.returncode
            handle.write(f"\n[coverage gate exit {gate_code}]\n")

    text = log.read_text(encoding="utf-8", errors="replace")
    provenance = [line.split(" ", 1)[1] for line in text.splitlines() if line.startswith("PROVENANCE ")]
    expected = str(tree / "src/api/lifecycle/manager.py")
    total_line = [line for line in text.splitlines() if line.startswith("TOTAL ")]
    result = {
        "tree": str(tree),
        "lane": args.lane,
        "interpreter": sys.executable,
        "python": sys.version.split()[0],
        "argv": argv,
        "pytest_exit": proc.returncode,
        "coverage_gate_exit": gate_code,
        "coverage_total_line": total_line[-1] if total_line else None,
        "provenance": provenance,
        "provenance_ok": provenance == [expected],
        "junit": str(junit),
        "log": str(log),
        **(_junit_summary(junit) if junit.exists() else {"counts": None, "failing": None}),
    }
    (out / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("lane", "pytest_exit", "coverage_gate_exit", "coverage_total_line", "provenance_ok", "counts")}, indent=2))
    if gate_code:
        return proc.returncode or gate_code
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
