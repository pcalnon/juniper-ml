#!/usr/bin/env python3
"""
Validator runs for juniper-data's "run the unrun tests" carrier: CI's unit lane with both coverage gates, CI's
integration lane, or a list of node ids, in one tree with one interpreter, with every report redirected to a
scratch directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-data's .github/workflows/ci.yml (the `unit-tests` and `integration-tests` jobs, whose pytest
         arguments are copied below), tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (check D)

Usage:
  2026-11-12_flood4r2_val_d2-data_run_lane.py --python <venv python> --tree <juniper-data tree> --out <dir>
      --lane unit|integration|nodes [--nodes-file <file>] [--deselect-file <file>] [--repeat N] [--jobs J]
      [--no-cov]

- ``unit``: ``pytest -m "unit and not slow" juniper_data/tests/unit --verbose --timeout=60 --maxfail=5`` with the
  job's five report options, then ``coverage report --fail-under=80`` and ``juniper-coverage-gap-map --enforce``
  (``--no-cov`` drops the coverage options and both gates, for a mutant run that only needs pass or fail).
- ``integration``: ``pytest -m "integration and not slow" juniper_data/tests/integration --verbose --timeout=120
  --maxfail=3`` with its JUnit report.
- ``nodes``: the node ids of ``--nodes-file`` (one per line), ``--repeat`` times, ``--jobs`` processes at once.
- ``--deselect-file``: one node id per line, each passed as ``--deselect``. A tree with the carrier laid over it and
  the newly selected tests deselected runs exactly the selection main's lane has; the census proves the two sets
  equal.

Every child runs from the tree's root with the six Sentry DSN variables set to the empty string, a short list of
token variables removed, PYTHONDONTWRITEBYTECODE=1 (no stale bytecode between mutants) and COVERAGE_FILE under the
output directory (so that two runs in one tree do not share a data file). TMPDIR is left as the session gave it.
Writes <out>/result.json; exit status is the worst child status.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_NAMES = ("HF_TOKEN", "PYPI_API_TOKEN", "TEST_PYPI_API_TOKEN", "TWINE_PASSWORD", "GITLEAKS_PARITY_REQUIRED")
SUMMARY = re.compile(r"\b\d+ (?:passed|failed|error|errors|skipped|deselected)\b")


def child_env(out: Path) -> dict:
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["COVERAGE_FILE"] = str(out / ".coverage")
    return env


def read_lines(path: str | None) -> list[str]:
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def run_logged(argv: list[str], tree: Path, env: dict, log: Path, limit: int) -> dict:
    started = time.monotonic()
    with log.open("wb") as handle:
        try:
            status = subprocess.run(argv, cwd=str(tree), env=env, stdout=handle, stderr=subprocess.STDOUT, check=False, timeout=limit).returncode
        except subprocess.TimeoutExpired:
            status = 124
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    summary = next((line.strip().strip("= ") for line in reversed(lines) if SUMMARY.search(line)), "")
    return {"exit": status, "seconds": round(time.monotonic() - started, 2), "summary": summary, "log": str(log)}


def junit_facts(path: Path) -> dict:
    if not path.is_file():
        return {}
    cases = list(ET.parse(path).getroot().iter("testcase"))
    bad = [f"{case.get('classname')}::{case.get('name')}" for case in cases if case.find("failure") is not None or case.find("error") is not None]
    skipped = [f"{case.get('classname')}::{case.get('name')}" for case in cases if case.find("skipped") is not None]
    return {"testcases": len(cases), "failed_or_error": bad, "skipped": len(skipped), "skipped_classes": sorted({name.split("::")[0] for name in skipped}), "test_seconds": round(sum(float(case.get("time") or 0) for case in cases), 2)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--lane", required=True, choices=("unit", "integration", "nodes"))
    parser.add_argument("--nodes-file")
    parser.add_argument("--deselect-file")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--no-cov", action="store_true")
    ns = parser.parse_args()
    tree, out = Path(ns.tree).resolve(), Path(ns.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    env = child_env(out)
    deselect = [item for node in read_lines(ns.deselect_file) for item in ("--deselect", node)]
    pytest = [ns.python, "-m", "pytest", "-p", "no:cacheprovider"]
    probe = subprocess.run([ns.python, "-c", "import sys, juniper_data; print(sys.version.split()[0]); print(juniper_data.__file__)"], cwd=str(tree), env=env, capture_output=True, text=True, check=False)
    result: dict = {"lane": ns.lane, "tree": str(tree), "python": ns.python, "probe": probe.stdout.split(), "deselected_by_file": len(deselect) // 2, "steps": {}}
    worst = 0
    if ns.lane == "unit":
        argv = [*pytest, "-m", "unit and not slow", "juniper_data/tests/unit", "--verbose", "--timeout=60", "--maxfail=5", f"--junitxml={out / 'junit-unit.xml'}"]
        if not ns.no_cov:
            argv += ["--cov=juniper_data", "--cov-report=term-missing", f"--cov-report=xml:{out / 'coverage.xml'}", f"--cov-report=html:{out / 'htmlcov'}", f"--cov-report=json:{out / 'coverage.json'}"]
        result["steps"]["pytest"] = run_logged([*argv, *deselect], tree, env, out / "pytest.log", 3000)
        result["junit"] = junit_facts(out / "junit-unit.xml")
        if not ns.no_cov:
            result["steps"]["aggregate_gate"] = run_logged([ns.python, "-m", "coverage", "report", "--fail-under=80"], tree, env, out / "coverage_report.log", 600)
            result["steps"]["per_file_gate"] = run_logged([str(Path(ns.python).parent / "juniper-coverage-gap-map"), "--coverage-json", str(out / "coverage.json"), "--enforce"], tree, env, out / "gap_map.log", 600)
            if (out / "coverage.json").is_file():
                totals = json.loads((out / "coverage.json").read_text(encoding="utf-8"))["totals"]
                result["coverage_totals"] = {key: totals[key] for key in ("percent_covered", "covered_lines", "num_statements", "missing_lines", "num_branches", "covered_branches") if key in totals}
    elif ns.lane == "integration":
        argv = [*pytest, "-m", "integration and not slow", "juniper_data/tests/integration", "--verbose", "--timeout=120", "--maxfail=3", f"--junitxml={out / 'junit-integration.xml'}"]
        result["steps"]["pytest"] = run_logged([*argv, *deselect], tree, env, out / "pytest.log", 1800)
        result["junit"] = junit_facts(out / "junit-integration.xml")
    else:
        nodes = read_lines(ns.nodes_file)
        result["nodes"] = len(nodes)

        def one(index: int) -> dict:
            return run_logged([*pytest, *nodes, *deselect, f"--junitxml={out / f'junit-run{index:02d}.xml'}"], tree, env, out / f"run{index:02d}.log", 1800)

        with ThreadPoolExecutor(max_workers=max(1, min(ns.jobs, 4))) as pool:
            runs = list(pool.map(one, range(1, ns.repeat + 1)))
        for index, run in enumerate(runs, start=1):
            run["junit"] = junit_facts(out / f"junit-run{index:02d}.xml")
            result["steps"][f"run{index:02d}"] = run
        result["summaries"] = sorted({run["summary"].split(" in ")[0] for run in runs})
    for step in result["steps"].values():
        worst = max(worst, step["exit"])
    result["worst_exit"] = worst
    (out / "result.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for name, step in result["steps"].items():
        print(f"{name:16s} exit={step['exit']} {step['seconds']:8.2f}s | {step['summary']}")
    if "coverage_totals" in result:
        print(f"coverage totals: {result['coverage_totals']}")
    if result.get("junit", {}).get("failed_or_error"):
        print("FAILED:", result["junit"]["failed_or_error"])
    return worst


if __name__ == "__main__":
    sys.exit(main())
