#!/usr/bin/env python3
"""
Run juniper-cascor-worker's CI pytest lanes in a given tree, the way the workflows invoke them, and record each lane's counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor-worker)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         adapted from 2026-11-14_flood4r2_r10-cascor-client_run_lanes.py (its `lane_argv` rewritten for this repository)

WHY THIS EXISTS
The port adds a test file, and has to say which lane runs it and show the lane's counts against main's. This runs
the pytest commands of juniper-cascor-worker's lanes with their own arguments (read from `.github/workflows/ci.yml`
and `scheduled-tests.yml` at 7a83b024 on 2026-11-15), once per tree, so the two summaries can be compared:

    unit         ci.yml `unit-tests`: `pytest tests/ --verbose --timeout=60 --maxfail=5` plus coverage, no marker filter
    unit-m       docs/DEVELOPER_CHEATSHEET.md's documented unit run: `pytest tests/ -m unit -v`
    integration  ci.yml `integration-tests`: `pytest -m integration tests/ --verbose --timeout=120 --maxfail=5` (exit 5 is a skip)
    scheduled    scheduled-tests.yml: `pytest -m "slow or integration" --tb=short --maxfail=10` (no exit-5 tolerance there)
    selftest     ci.yml `security`, the port's new step: `pytest tests/test_gitleaks_pr_scan.py -v -v --timeout=120`
                 with GITLEAKS_PARITY_REQUIRED=1 and the engine's directory first on PATH, as on a runner

No lane gets a scanner binary except `selftest`: GITLEAKS_BIN is unset and PATH is left alone, as in the unit job.
Each lane's junit report is read for its test-case count and for how many of those cases are the new file's.
Reports, the coverage data file and pytest's basetemp go under --out, never into the tree; no bytecode is written.
The six Sentry DSN variables are set to the empty string in every child.

Usage:
    python3 <this> --tree <checkout> --label <main|port> --out <dir> --python <interpreter> [--lanes unit,unit-m,integration,scheduled] [--engine-dir <dir holding the engine>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: the chosen interpreter running pytest
import sys
import time
import xml.etree.ElementTree as ElementTree  # nosec B405 - parses junit reports pytest itself wrote under --out
from pathlib import Path

COUNT = re.compile(r"(\d+) (passed|failed|skipped|deselected|errors?|xfailed|xpassed|warnings?)")
TOTAL = re.compile(r"^TOTAL\s.*?(\d+(?:\.\d+)?)%\s*$", re.MULTILINE)
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
ENGINE_NAMES = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
NEW_FILE_CLASS = "tests.test_gitleaks_pr_scan"


def junit_path(out: Path, label: str, lane: str) -> Path:
    return out / f"{label}-junit-{lane}.xml"


def lane_argv(lane: str, out: Path, label: str) -> list[str]:
    junit = f"--junitxml={junit_path(out, label, lane)}"
    if lane == "unit":
        return ["tests/", "--verbose", "--timeout=60", "--maxfail=5", junit, "--cov=juniper_cascor_worker", "--cov-report=term-missing", f"--cov-report=json:{out / (label + '-coverage.json')}"]
    if lane == "unit-m":
        return ["tests/", "-m", "unit", "-v", junit]
    if lane == "integration":
        return ["-m", "integration", "tests/", "--verbose", "--timeout=120", "--maxfail=5", junit]
    if lane == "scheduled":
        return ["-m", "slow or integration", "--tb=short", "--maxfail=10", junit]
    if lane == "selftest":
        return ["tests/test_gitleaks_pr_scan.py", "-v", "-v", "--timeout=120", junit]
    raise SystemExit(f"unknown lane {lane!r}")


def junit_counts(path: Path) -> dict:
    """Test cases in the report, and how many of them the new file contributed, by outcome."""
    counts = {"cases": 0, "new_file_cases": 0, "new_file": {"passed": 0, "failed": 0, "error": 0, "skipped": 0}}
    if not path.is_file():
        return counts
    for case in ElementTree.parse(path).getroot().iter("testcase"):  # nosec B314 - pytest's own report
        counts["cases"] += 1
        if case.get("classname", "").startswith(NEW_FILE_CLASS):
            counts["new_file_cases"] += 1
            if case.find("failure") is not None:
                counts["new_file"]["failed"] += 1
            elif case.find("error") is not None:
                counts["new_file"]["error"] += 1
            elif case.find("skipped") is not None:
                counts["new_file"]["skipped"] += 1
            else:
                counts["new_file"]["passed"] += 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--lanes", default="unit,unit-m,integration,scheduled")
    ap.add_argument("--engine-dir", type=Path, help="for the selftest lane: the directory that holds the engine binary")
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for lane in args.lanes.split(","):
        env = {k: v for k, v in os.environ.items() if k not in ENGINE_NAMES}
        env.update({name: "" for name in SENTRY_DSN_NAMES})
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["COVERAGE_FILE"] = str(out / f"{args.label}-{lane}.coverage")
        if lane == "selftest":
            if args.engine_dir is None:
                raise SystemExit("the selftest lane needs --engine-dir")
            env["GITLEAKS_PARITY_REQUIRED"] = "1"
            env["PATH"] = f"{args.engine_dir.resolve()}{os.pathsep}{env.get('PATH', os.defpath)}"
        argv = [args.python, "-m", "pytest", *lane_argv(lane, out, args.label), "-p", "no:cacheprovider", f"--basetemp={out / (args.label + '-basetemp-' + lane)}"]
        started = time.monotonic()
        proc = subprocess.run(argv, cwd=args.tree, env=env, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
        log = out / f"{args.label}-{lane}.log"
        log.write_text("$ " + " ".join(argv) + "\n" + proc.stdout + proc.stderr + f"\n[exit {proc.returncode}]\n", encoding="utf-8")
        summary = next((line for line in reversed(proc.stdout.splitlines()) if COUNT.search(line) and (" in " in line)), "")
        total = TOTAL.search(proc.stdout)
        row = {
            "lane": lane,
            "label": args.label,
            "exit": proc.returncode,
            "seconds": round(time.monotonic() - started, 1),
            "counts": {kind: int(number) for number, kind in COUNT.findall(summary)},
            "summary_line": summary.strip("= "),
            "junit": junit_counts(junit_path(out, args.label, lane)),
            "coverage_total_percent": total.group(1) if total else None,
            "log": str(log),
        }
        results.append(row)
        print(f"{args.label:<5} {lane:<12} exit={row['exit']} {row['summary_line']}  junit cases={row['junit']['cases']} new-file={row['junit']['new_file_cases']} {row['junit']['new_file']}" + (f"  coverage TOTAL {row['coverage_total_percent']}%" if total else ""))
    with open(out / f"{args.label}-lanes.json", "w", encoding="utf-8") as fh:
        json.dump({"tree": str(args.tree), "python": args.python, "results": results}, fh, indent=1)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
