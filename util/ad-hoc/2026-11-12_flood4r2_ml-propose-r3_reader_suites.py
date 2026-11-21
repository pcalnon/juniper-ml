#!/usr/bin/env python3
"""
Run every tests/ suite that reads a named file, in several trees and on several interpreters, and compare counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
tests/test_release_train_propose.py is not the only reader of the files this carrier changes, and
ReferenceCompatibilityMatrixTest is not the only reader of the files a release proposal rewrites. Two uses:

1. the carrier against a clean main: every suite whose source mentions docs/REFERENCE.md, propose.py or the
   release train, on Python 3.12 and on a newer interpreter. A suite must pass wherever it passes on clean main,
   and its test count is reported beside main's;
2. post-proposal sandboxes against a pristine one (--pattern widened to every file a proposal edits): no suite
   that passes before the proposal may fail after it;
3. with --suite, the suites that failed in CI's whole regression list, in the carrier and on a clean main: a
   failure counts against the carrier only when the suite passes on main, and the report says whether the two
   trees fail the same tests.

The suite list is --suite's, or else taken from the FIRST --tree by --pattern. One process per suite (`python -B -m unittest <suite>`), at most
four side by side. A suite is a regression when it passes in the --baseline tree and fails in another tree on the
same interpreter; a suite that fails in the baseline too is reported as such, not as the carrier's.

Usage:
    python3 <this> --tree <label>=<path> [--tree ...] --baseline <label> --python <label>=<interpreter> [--python ...]
                   --out <json> [--jobs 4] [--pattern <regex>|PROPOSAL] [--suite tests/<suite>.py ...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: child interpreters running unittest
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_PATTERN = r"REFERENCE\.md|release_train|propose\.py"
PROPOSAL_PATTERN = r"REFERENCE\.md|release_train|propose\.py|AGENTS\.md|pyproject\.toml|README\.md|CHANGELOG\.md|QUICK_START"


def run_suite(python: str, root: Path, suite: str, timeout: int) -> dict:
    try:
        done = subprocess.run([python, "-B", "-m", "unittest", suite], cwd=root, capture_output=True, text=True, check=False, timeout=timeout)  # nosec B603
    except subprocess.TimeoutExpired:
        return {"rc": None, "ran": None, "verdict": "TIMEOUT"}
    output = done.stdout + done.stderr
    ran = re.search(r"^Ran (\d+) tests?", output, re.MULTILINE)
    verdict = re.search(r"^(OK.*|FAILED.*)$", output, re.MULTILINE)
    failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", output, re.MULTILINE)))
    return {"rc": done.returncode, "ran": int(ran.group(1)) if ran else None, "verdict": verdict.group(1) if verdict else (output.strip().splitlines()[-1:] or [""])[0], "failing": failing}


def labelled(values: list, what: str) -> dict:
    pairs = {}
    for value in values:
        label, _, target = value.partition("=")
        if not target:
            raise SystemExit(f"--{what} wants <label>=<value>, got {value!r}")
        pairs[label] = target
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, action="append")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--python", required=True, action="append")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--pattern", default=DEFAULT_PATTERN, help=f"suites whose source matches this regex (PROPOSAL = {PROPOSAL_PATTERN})")
    parser.add_argument("--suite", action="append", default=[], help="run exactly these suites instead of the pattern's (repeatable): for a suite that failed elsewhere, to see whether it fails on the baseline too")
    args = parser.parse_args()
    trees = {label: Path(path) for label, path in labelled(args.tree, "tree").items()}
    pythons = labelled(args.python, "python")
    if args.baseline not in trees:
        raise SystemExit(f"--baseline {args.baseline!r} is not one of the --tree labels")
    reads = re.compile(PROPOSAL_PATTERN if args.pattern == "PROPOSAL" else args.pattern)
    first = next(iter(trees.values()))
    suites = sorted(args.suite) or sorted(f"tests/{path.name}" for path in (first / "tests").glob("test_*.py") if reads.search(path.read_text(encoding="utf-8", errors="replace")))
    plan = [(suite, tree_label, python_label) for suite in suites for tree_label in trees for python_label in pythons]

    def one(item: tuple) -> tuple:
        suite, tree_label, python_label = item
        if not (trees[tree_label] / suite).is_file():
            return item, {"rc": None, "ran": None, "verdict": "ABSENT"}
        return item, run_suite(pythons[python_label], trees[tree_label], suite, args.timeout)

    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        done = dict(pool.map(one, plan))
    rows = []
    regressions = []
    baseline_failures = []
    count_changes = []
    for suite in suites:
        row = {"suite": suite}
        for python_label in pythons:
            base = done[(suite, args.baseline, python_label)]
            if base["rc"] != 0:
                baseline_failures.append({"suite": suite, "python": python_label, "verdict": base["verdict"], "failing": base.get("failing")})
            for tree_label in trees:
                result = done[(suite, tree_label, python_label)]
                row[f"{tree_label}@{python_label}"] = result
                if tree_label == args.baseline:
                    continue
                if base["rc"] == 0 and result["rc"] != 0:
                    regressions.append({"suite": suite, "tree": tree_label, "python": python_label, "verdict": result["verdict"], "failing": result.get("failing")})
                if base["rc"] != 0 and result["rc"] != 0:
                    row[f"{tree_label}@{python_label} fails the same tests as the baseline"] = result.get("failing") == base.get("failing")
                if result["ran"] != base["ran"]:
                    count_changes.append({"suite": suite, "tree": tree_label, "python": python_label, "baseline_ran": base["ran"], "ran": result["ran"]})
        rows.append(row)
    report = {
        "pattern": reads.pattern,
        "trees": {label: str(path) for label, path in trees.items()},
        "baseline": args.baseline,
        "pythons": pythons,
        "suites": len(suites),
        "runs": len(plan),
        "regressions": regressions,
        "baseline_failures": baseline_failures,
        "count_changes": count_changes,
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"suites={len(suites)} runs={len(plan)} regressions={len(regressions)} baseline_failures={len(baseline_failures)}")
    for item in regressions:
        print("REGRESSION", item)
    for item in baseline_failures:
        print("fails in the baseline too:", item)
    for item in count_changes:
        print("count differs from the baseline:", item)
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
