"""
Run a set of canopy test files N times across up to four trees in parallel and report, per test, every non-pass (flakes).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage:
    python3 <this file> --trees <tree> [<tree> ...] --python <interpreter> --out <dir> --runs N --paths <test files...> [--focus <ids file>]

Each tree (at most four, each holding the same change set: the caller checks that) runs its share of the N iterations
one after another, so at most len(trees) pytest processes run at once. Every iteration is one
2026-11-25_flood4_s14_r27_run_lane.py --mode files run of all the named files (behind the r27 connect fence, CI's
selector and step variables), whole files, in file order, as the unit lane runs them. The junit of each iteration is
read per test case: passed, failed, error or skipped. --focus names the node ids that matter (one per line: the tests
the fake newly answers, and the new tests); the report gives their outcome counts, and every test of the files that
did not pass in every iteration. Writes <dir>/flakes.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import threading
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_LANE = HERE / "2026-11-25_flood4_s14_r27_run_lane.py"


def junit_outcomes(path: Path) -> dict[str, str]:
    outcomes = {}
    root = ET.parse(path).getroot()  # nosec B314 - our own pytest junit output
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    for case in suite.iter("testcase"):
        classname, name = case.get("classname") or "", case.get("name") or ""
        parts = classname.split(".")
        # junit classname is dotted: src.tests.unit.test_x.TestClass -> src/tests/unit/test_x.py::TestClass::name
        module_end = max(index for index, part in enumerate(parts) if part.startswith("test_")) if any(part.startswith("test_") for part in parts) else len(parts) - 1
        nodeid = "/".join(parts[: module_end + 1]) + ".py::" + "::".join(parts[module_end + 1 :] + [name])
        nodeid = nodeid.replace(".py::::", ".py::")
        outcome = "passed"
        if case.find("failure") is not None:
            outcome = "failed"
        elif case.find("error") is not None:
            outcome = "error"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        outcomes[nodeid] = outcome
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canopy test files N times across up to four trees and report flakes.")
    parser.add_argument("--trees", nargs="+", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--focus", type=Path, default=None)
    args = parser.parse_args()
    if len(args.trees) > 4:
        raise SystemExit("at most four trees: four pytest processes at once")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    iterations = defaultdict(list)
    for index in range(args.runs):
        iterations[index % len(args.trees)].append(index)
    results: dict[int, dict] = {}
    lock = threading.Lock()

    def worker(slot: int) -> None:
        tree = args.trees[slot].resolve()
        for index in iterations[slot]:
            label = f"flake-{index:02d}"
            argv = [sys.executable, str(RUN_LANE), "--tree", str(tree), "--python", args.python, "--label", label, "--out", str(out / "runs"), "--mode", "files", "--paths", *args.paths]
            subprocess.run(argv, check=False, capture_output=True, text=True)  # nosec B603 - fixed argv
            summary = json.loads((out / "runs" / f"{label}.summary.json").read_text(encoding="utf-8"))
            junit = out / "runs" / f"{label}.junit.xml"
            record = {"tree": str(tree), "exit": summary["exit"], "started_utc": summary["started_utc"], "ended_utc": summary["ended_utc"], "result_line": summary.get("result_line"), "guarded_port_connects": summary.get("connects_to_guarded_ports_at_socket_level"), "guard_failed_reports": len(summary.get("guard_failed_reports", [])), "outcomes": junit_outcomes(junit) if junit.exists() else {}}
            with lock:
                results[index] = record
                print(json.dumps({"iteration": index, "tree": tree.name, "exit": record["exit"], "result_line": record["result_line"], "guarded_port_connects": record["guarded_port_connects"]}), flush=True)

    threads = [threading.Thread(target=worker, args=(slot,), name=f"flake-tree-{slot}") for slot in range(len(args.trees))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    per_test: dict[str, Counter] = defaultdict(Counter)
    for record in results.values():
        for nodeid, outcome in record["outcomes"].items():
            per_test[nodeid][outcome] += 1
    focus = [line.strip() for line in args.focus.read_text(encoding="utf-8").splitlines() if line.strip()] if args.focus else []
    not_always_passed = {nodeid: dict(counts) for nodeid, counts in sorted(per_test.items()) if counts.get("passed", 0) != args.runs and counts.get("skipped", 0) != args.runs}
    report = {
        "runs": args.runs,
        "trees": [str(tree) for tree in args.trees],
        "paths": args.paths,
        "iterations": {str(index): {key: value for key, value in record.items() if key != "outcomes"} for index, record in sorted(results.items())},
        "tests_seen": len(per_test),
        "focus_ids": len(focus),
        "focus_missing_from_junit": [nodeid for nodeid in focus if nodeid not in per_test],
        "focus_outcomes": {nodeid: dict(per_test.get(nodeid, Counter())) for nodeid in focus},
        "focus_all_passed_every_run": all(per_test.get(nodeid, Counter()).get("passed", 0) == args.runs for nodeid in focus),
        "not_always_passed": not_always_passed,
        "guarded_port_connects_total": sum(record["guarded_port_connects"] or 0 for record in results.values()),
        "guard_failed_reports_total": sum(record["guard_failed_reports"] for record in results.values()),
    }
    (out / "flakes.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("runs", "tests_seen", "focus_ids", "focus_missing_from_junit", "focus_all_passed_every_run", "guarded_port_connects_total", "guard_failed_reports_total")} | {"not_always_passed": not_always_passed}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
