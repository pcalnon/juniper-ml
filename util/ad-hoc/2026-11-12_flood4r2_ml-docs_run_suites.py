#!/usr/bin/env python3
"""
Run ci.yml's regression list in a given tree, one process per suite, with every Sentry DSN variable emptied.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2); adapted from
         util/ad-hoc/2026-11-07_flood4_run_ci_regression_suites_parallel.py (round 1)

The suite list is read from ``<tree>/.github/workflows/ci.yml``: every ``python3 -m unittest -v tests/<file>``
line, in the workflow's order, each once. Every suite runs as its own ``<python> -m unittest -v <suite>``
process from ``<tree>``, at most ``--jobs`` at a time (capped at 4: the host is shared). A suite that fails
beside others is run again ALONE, and only a failure that repeats alone counts as a failure.

Every process gets the six Sentry DSN variables set to the empty string (set, not unset), so no test run
can report to Sentry (consolidated plan rule H-14). Their inherited values are never printed.

The run is refused when a ``pyproject.toml`` sits under the tree's own ``tmp`` directory:
``tests/test_release_train_registry.py`` walks that directory and would read it as a package.

Usage: 2026-11-12_flood4r2_ml-docs_run_suites.py --tree <root> --out <json> [--jobs 4] [--timeout 1500]
       [--python <interpreter>] [--only <suite> ...]
Exit 0 when every suite passed (beside others or alone), 1 when any failed alone, 2 on a refused run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = (
    "SENTRY_SDK_DSN",
    "SENTRY_DSN",
    "JUNIPER_CASCOR_SENTRY_DSN",
    "JUNIPER_DATA_SENTRY_DSN",
    "CANOPY_SENTRY_DSN",
    "JUNIPER_CANOPY_SENTRY_DSN",
)
SUITE_RE = re.compile(r"python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)")
MAX_JOBS = 4


def suite_list(tree: Path) -> list[str]:
    text = (tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    seen: dict[str, None] = {}
    for suite in SUITE_RE.findall(text):
        seen.setdefault(suite, None)
    return list(seen)


def run_one(tree: Path, python: str, suite: str, timeout: int, env: dict[str, str]) -> dict:
    started = time.monotonic()
    try:
        proc = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=str(tree), capture_output=True, text=True, errors="replace", timeout=timeout, check=False, env=env)
    except subprocess.TimeoutExpired:
        return {"suite": suite, "exit": "timeout", "ran": None, "verdict": f"no result within {timeout} s", "failed": [], "seconds": round(time.monotonic() - started, 1)}
    text = proc.stderr + proc.stdout
    ran = re.findall(r"^Ran (\d+) tests?", text, flags=re.MULTILINE)
    verdict = re.findall(r"^(OK.*|FAILED.*)$", text, flags=re.MULTILINE)
    failed = re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", text, flags=re.MULTILINE)
    return {
        "suite": suite,
        "exit": proc.returncode,
        "ran": int(ran[-1]) if ran else None,
        "verdict": verdict[-1] if verdict else text[-400:],
        "failed": failed,
        "seconds": round(time.monotonic() - started, 1),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run ci.yml's regression list, one process per suite.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=MAX_JOBS)
    parser.add_argument("--timeout", type=int, default=1500)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args(argv)
    tree = args.tree.resolve()
    strays = sorted(str(path) for path in (tree / "tmp").rglob("pyproject.toml")) if (tree / "tmp").is_dir() else []
    if strays:
        print(json.dumps({"refused": "pyproject.toml under tmp/", "paths": strays[:20]}, indent=1))
        return 2
    suites = suite_list(tree)
    if args.only is not None:
        unknown = [suite for suite in args.only if suite not in suites]
        if unknown:
            print(json.dumps({"refused": "suite not in ci.yml's list", "suites": unknown}, indent=1))
            return 2
        suites = list(args.only)
    if not suites:
        print(json.dumps({"refused": "no suite found"}, indent=1))
        return 2
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    jobs = max(1, min(args.jobs, MAX_JOBS))
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        first = list(pool.map(lambda suite: run_one(tree, args.python, suite, args.timeout, env), suites))
    beside = [row for row in first if row["exit"] != 0]
    alone = [run_one(tree, args.python, row["suite"], args.timeout, env) for row in beside]
    failed_alone = [row for row in alone if row["exit"] != 0]
    report = {
        "tree": str(tree),
        "python": args.python,
        "python_version": sys.version.split()[0] if args.python == sys.executable else "see --python",
        "jobs": jobs,
        "suites": len(suites),
        "tests_ran": sum(row["ran"] or 0 for row in first),
        "failed_beside_others": [row["suite"] for row in beside],
        "failed_alone": [row["suite"] for row in failed_alone],
        "sentry_dsn_variables_emptied": list(SENTRY_DSN_NAMES),
        "seconds": round(time.monotonic() - started, 1),
        "first_pass": first,
        "alone_pass": alone,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{len(suites)} suites, {report['tests_ran']} tests, {len(beside)} failed beside others, {len(failed_alone)} failed alone, {report['seconds']} s")
    for row in failed_alone:
        print(f"FAIL {row['suite']}: {row['verdict']} {row['failed'][:6]}")
    return 1 if failed_alone else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
