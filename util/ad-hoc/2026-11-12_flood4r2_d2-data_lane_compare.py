#!/usr/bin/env python3
"""
Compare a before and an after run of juniper-data's CI unit lane: counts, runtime, both coverage gates, per-file moves.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (does running 125 more unit tests move a coverage gate, and what does it cost in runtime?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_d2-data_run.py (writes the result.json this reads)

Usage:
    python3 <this> --result <.../unit-lane_<tag>/result.json> --pair <before job>=<after job> [--pair ...] --out <file>

For each pair it reports the JUnit counts, the wall-clock seconds of the pytest step, the sum of the JUnit test-case
times, the aggregate coverage (statements and branches, as ``coverage report`` gates it) and the per-file gate's
verdict, then every source file whose set of missing statement lines differs between the two runs, and, per test
module, the tests and seconds the after run adds. Reads one JSON file and writes one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _pct(covered: int, total: int) -> float:
    return round(100.0 * covered / total, 3) if total else 100.0


def _side(res: dict) -> dict:
    totals = res.get("coverage_json_totals", {})
    return {
        "exit": res["exit"],
        "summary": res["summary"],
        "pytest_step_seconds": res["seconds"],
        "junit_counts": res["junit"]["counts"],
        "junit_testcase_seconds": res["junit"].get("testcase_seconds"),
        "aggregate_gate_exit": res["aggregate_gate"]["exit"],
        "aggregate_total_line": res["aggregate_gate"]["total_line"],
        "coverage_percent_statements_and_branches": round(totals.get("percent_covered", 0.0), 3),
        "statements": totals.get("num_statements"),
        "missing_statements": totals.get("missing_lines"),
        "per_file_gate_exit": res["per_file_gate"]["exit"],
        "per_file_gate_verdict": res["per_file_gate"]["verdict_lines"],
        "python_version": res.get("python_version"),
        "imported_inside_tree": res.get("imported_inside_tree"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--pair", action="append", required=True, help="<before job>=<after job>")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    with open(args.result, encoding="utf-8") as fh:
        by_job = {r["job"]: r for r in json.load(fh)["results"]}
    report: dict = {"result": str(args.result), "pairs": []}
    for item in args.pair:
        before_name, after_name = item.split("=", 1)
        before, after = by_job[before_name], by_job[after_name]
        moved = []
        files_b, files_a = before.get("coverage_per_file", {}), after.get("coverage_per_file", {})
        for path in sorted(set(files_b) | set(files_a)):
            fb, fa = files_b.get(path), files_a.get(path)
            if fb is None or fa is None or fb["missing_lines"] != fa["missing_lines"] or fb["statements"] != fa["statements"]:
                moved.append({
                    "file": path,
                    "before": None if fb is None else {"statements": fb["statements"], "missing": fb["missing"], "percent": _pct(fb["statements"] - fb["missing"], fb["statements"])},
                    "after": None if fa is None else {"statements": fa["statements"], "missing": fa["missing"], "percent": _pct(fa["statements"] - fa["missing"], fa["statements"])},
                    "lines_newly_covered": sorted(set((fb or {}).get("missing_lines", [])) - set((fa or {}).get("missing_lines", []))),
                    "lines_newly_missing": sorted(set((fa or {}).get("missing_lines", [])) - set((fb or {}).get("missing_lines", []))),
                })
        per_b, per_a = before["junit"]["per_file"], after["junit"]["per_file"]
        added = {}
        for module in sorted(set(per_a) | set(per_b)):
            tb = per_b.get(module, {"tests": 0, "seconds": 0.0})
            ta = per_a.get(module, {"tests": 0, "seconds": 0.0})
            if ta["tests"] != tb["tests"]:
                added[module] = {"tests_before": tb["tests"], "tests_after": ta["tests"], "delta_tests": ta["tests"] - tb["tests"], "seconds_before": tb["seconds"], "seconds_after": ta["seconds"]}
        pair = {
            "before_job": before_name,
            "after_job": after_name,
            "before": _side(before),
            "after": _side(after),
            "delta_tests": after["junit"]["counts"]["tests"] - before["junit"]["counts"]["tests"],
            "delta_pytest_step_seconds": round(after["seconds"] - before["seconds"], 1),
            "delta_junit_testcase_seconds": round((after["junit"].get("testcase_seconds") or 0.0) - (before["junit"].get("testcase_seconds") or 0.0), 2),
            "modules_whose_test_count_changed": added,
            "source_files_whose_coverage_moved": moved,
            "not_passed_after": [b for b in after["junit"].get("not_passed", []) if b["outcome"] != "skipped"],
            "skipped_after": sorted({b["id"].split("::")[0] for b in after["junit"].get("not_passed", []) if b["outcome"] == "skipped"}),
        }
        report["pairs"].append(pair)
        brief = {k: pair[k] for k in ("before_job", "after_job", "delta_tests", "delta_pytest_step_seconds", "delta_junit_testcase_seconds", "not_passed_after")}
        for side in ("before", "after"):
            brief[side] = {k: pair[side][k] for k in ("exit", "summary", "pytest_step_seconds", "junit_testcase_seconds", "aggregate_gate_exit", "aggregate_total_line", "per_file_gate_exit", "per_file_gate_verdict", "python_version", "imported_inside_tree")}
        print(json.dumps(brief, indent=1))
        print("modules whose test count changed:", json.dumps(added))
        print("source files whose coverage moved:")
        for row in moved:
            print("  ", json.dumps(row))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
