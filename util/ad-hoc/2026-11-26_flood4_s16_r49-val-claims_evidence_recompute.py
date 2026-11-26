#!/usr/bin/env python3
"""
Recompute, from carrier r49's raw run files, every figure its texts quote: verdicts, latencies, stop lengths, threads.

For each run label it reads the JUnit XML(s) and the r49 stall-plugin record (<label>.r49.jsonl) under the builder's
runs/ tree, and reports: tests run / passed / failed, the failure messages (and the latencies the old test printed),
injected stop lengths (min, max, count), get_status calls on the main thread (pytest-asyncio's loop thread) against
the total, and for the "held" injections whether each test's first call lasted longer than that test's stop (the stop
fell inside the hold). Lane labels are read from their run.json. Nothing in the carrier is modified.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the builder's own local JUnit files
from pathlib import Path

LAT_RE = re.compile(r"/v1/health/live took ([0-9.]+)s")


def junit_stats(paths: list[Path]) -> dict:
    out = {"files": len(paths), "tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "messages": {}, "latencies": [], "by_name": {}}
    for path in paths:
        root = ET.parse(path).getroot()  # nosec B314 - local file written by pytest
        for case in root.iter("testcase"):
            out["tests"] += 1
            name = re.sub(r"\[.*\]$", "", case.get("name", ""))
            slot = out["by_name"].setdefault(name, {"passed": 0, "failed": 0, "errors": 0, "skipped": 0})
            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")
            if failure is not None:
                out["failed"] += 1
                slot["failed"] += 1
                msg = (failure.get("message") or "").split("\n")[0]
                m = LAT_RE.search(msg)
                if m:
                    out["latencies"].append(float(m.group(1)))
                    msg = LAT_RE.sub("/v1/health/live took <x>s", msg)
                out["messages"][msg[:220]] = out["messages"].get(msg[:220], 0) + 1
            elif error is not None:
                out["errors"] += 1
                slot["errors"] += 1
                msg = (error.get("message") or "")[:220]
                out["messages"][msg] = out["messages"].get(msg, 0) + 1
            elif skipped is not None:
                out["skipped"] += 1
                slot["skipped"] += 1
            else:
                out["passed"] += 1
                slot["passed"] += 1
    if out["latencies"]:
        out["latency_min"], out["latency_max"] = min(out["latencies"]), max(out["latencies"])
    del out["latencies"]
    return out


def record_stats(path: Path) -> dict:
    stops, calls, on_main, held = [], 0, 0, []
    first_call: dict[str, float] = {}
    stop_by_test: dict[str, float] = {}
    modules = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            kind = rec.get("kind")
            if kind == "stop":
                stops.append(rec["seconds"])
                stop_by_test[rec["test"]] = rec["seconds"]
            elif kind == "call":
                calls += 1
                on_main += 1 if rec.get("on_main_thread") else 0
            elif kind == "call_end" and rec.get("first"):
                first_call[rec["test"]] = rec["seconds_in_call"]
            elif kind == "modules":
                modules = {k: rec.get(k) for k in ("test_module", "main", "admission")}
    for test, stop in stop_by_test.items():
        if test in first_call:
            held.append(round(first_call[test] - stop, 4))
    out = {"stops": len(stops), "calls": calls, "calls_on_main_thread": on_main, "modules": modules}
    if stops:
        out["stop_min"], out["stop_max"] = min(stops), max(stops)
    if held:
        out["first_call_minus_stop_min"], out["first_call_minus_stop_max"] = min(held), max(held)
        out["first_call_longer_than_stop"] = sum(1 for h in held if h > 0)
        out["first_call_seconds_min"] = min(first_call[t] for t in stop_by_test if t in first_call)
        out["first_call_seconds_max"] = max(first_call[t] for t in stop_by_test if t in first_call)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="recompute carrier r49's quoted figures from its raw run files")
    ap.add_argument("--runs", required=True, help="the builder's runs/ directory")
    ap.add_argument("--out", required=True, help="JSON report to write")
    args = ap.parse_args()
    runs = Path(args.runs)
    report: dict = {}
    for r49 in sorted(runs.glob("*/*.r49.jsonl")):
        label = r49.name[: -len(".r49.jsonl")]
        # The builder names a record after its run label; this lens's runs name it t1..t4 beside one label's JUnit.
        junits = sorted(r49.parent.glob(f"{label}.junit.xml")) or sorted(r49.parent.glob(f"{label}.run*.junit.xml")) or sorted(r49.parent.glob("*.junit.xml"))
        entry = {"dir": r49.parent.name, "record": record_stats(r49)}
        if junits:
            entry["junit"] = junit_stats(junits)
        report[label] = entry
    for run_json in sorted(runs.glob("lane*/*.run.json")):
        with run_json.open(encoding="utf-8") as fh:
            rec = json.load(fh)
        report[run_json.name[: -len(".run.json")]] = {"dir": run_json.parent.name, "lane": {k: rec.get(k) for k in ("raw_exit", "bash_exit", "ci_effective_exit", "seconds", "junit", "coverage_percent", "per_file_gate_exit", "connects_total", "connects_juniper_ports", "connects_child_processes", "cwd")}}
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for label, entry in report.items():
        j = entry.get("junit", {})
        r = entry.get("record", {})
        lane = entry.get("lane")
        if lane:
            print(f"{label:34s} LANE exit={lane['ci_effective_exit']} junit={lane['junit']} cov={lane['coverage_percent']} gate={lane['per_file_gate_exit']} juniper_connects={lane['connects_juniper_ports']} cwd={lane['cwd']}")
            continue
        print(f"{label:34s} tests={j.get('tests')} pass={j.get('passed')} fail={j.get('failed')} err={j.get('errors')} lat={j.get('latency_min')}-{j.get('latency_max')} stops={r.get('stops')} {r.get('stop_min')}-{r.get('stop_max')} calls={r.get('calls')} on_main={r.get('calls_on_main_thread')} held_margin={r.get('first_call_minus_stop_min')}-{r.get('first_call_minus_stop_max')} longer={r.get('first_call_longer_than_stop')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
