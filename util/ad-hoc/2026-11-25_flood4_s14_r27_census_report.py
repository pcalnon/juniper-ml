"""
Report the :8100 census of a fenced canopy run (per test, per file, setup vs call, opening code), and diff it against #815's.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects; juniper-canopy#815's census (its pr_body "Scope choice")

Usage:
    python3 <this file> --census <run>.census.jsonl --port 8100 --out <json> [--pr815-body <pr_body.txt>]

Reads the census 2026-11-25_flood4_s14_r27_fenced_pytest.py wrote. Every connect to the port (any host) is attributed
to the canopy code that opened it: the frames on the connecting stack, else the frames at the httpx request it
serves (the child-task case), each path normalized (a module imported through a `tests/regression/../../` entry is
reported as itself, not as a test frame). The opener is the first canopy source frame outside src/tests/ that is
not health.py, joined with health.py's frame when there is one ("health.py:82:probe_dependency <- main.py:432:lifespan").
With --pr815-body, the per-file counts #815's body lists by name are compared with this run's.
Writes <json> and prints a short text summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


def _norm(frame: str) -> str:
    path, _, rest = frame.partition(":")
    return f"{os.path.normpath(path)}:{rest}"


def opener(record: dict) -> str:
    frames = [_norm(frame) for frame in (record.get("src_frames") or []) + (record.get("test_frames") or [])]
    if not any(not frame.startswith("tests/") for frame in frames):
        frames = [_norm(frame) for frame in (record.get("request_src_frames") or []) + (record.get("request_test_frames") or [])]
    source = [frame for frame in frames if not frame.startswith("tests/")]
    probe = [frame for frame in source if frame.startswith("health.py:")]
    caller = [frame for frame in source if not frame.startswith(("health.py:", "middleware.py:"))]
    parts = probe[:1] + caller[:1]
    if parts:
        return " <- ".join(parts)
    tests = [frame for frame in frames if frame.startswith("tests/") and "_guarded_connect" not in frame]
    return "<no canopy source frame>" + (f" ({tests[0]})" if tests else "")


def pr815_counts(body: Path) -> dict[str, int]:
    text = body.read_text(encoding="utf-8")
    return {name: int(count) for name, count in re.findall(r"`(test_[a-z0-9_]+\.py)` \((\d+)\)", text)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Report the :8100 census of a fenced canopy run.")
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pr815-body", type=Path, default=None)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.census.read_text(encoding="utf-8").splitlines() if line.strip()]
    hits = [record for record in records if record["port"] == args.port]
    per_test: dict[str, Counter] = defaultdict(Counter)
    openers: dict[str, dict] = defaultdict(lambda: {"connects": 0, "tests": set(), "phases": Counter()})
    hosts, requests, threads = Counter(), Counter(), Counter()
    for record in hits:
        nodeid = record["nodeid"] or "<none>"
        per_test[nodeid][record["phase"]] += 1
        slot = openers[opener(record)]
        slot["connects"] += 1
        slot["tests"].add(nodeid)
        slot["phases"][record["phase"]] += 1
        hosts[record["host"]] += 1
        requests[record.get("request") or "<not an httpx async request>"] += 1
        threads["MainThread" if record["thread"] == "MainThread" else "off the main thread"] += 1
    by_phase = defaultdict(set)
    for nodeid, phases in per_test.items():
        for phase in phases:
            by_phase[phase].add(nodeid)
    files = Counter(nodeid.split("::", 1)[0] for nodeid in per_test)
    report = {
        "census": str(args.census),
        "port": args.port,
        "connects": len(hits),
        "refused_by_fence": sum(1 for record in hits if record["refused"]),
        "distinct_tests": len(per_test),
        "distinct_files": len(files),
        "tests_by_phase": {phase: len(tests) for phase, tests in sorted(by_phase.items())},
        "tests_in_setup_and_call": len(by_phase.get("setup", set()) & by_phase.get("call", set())),
        "hosts": dict(hosts),
        "requests": dict(requests.most_common()),
        "threads": dict(threads),
        "openers": {key: {"connects": value["connects"], "distinct_tests": len(value["tests"]), "phases": dict(value["phases"])} for key, value in sorted(openers.items(), key=lambda kv: -kv[1]["connects"])},
        "files_by_test_count": dict(sorted(files.items(), key=lambda kv: (-kv[1], kv[0]))),
        "per_test": {nodeid: dict(phases) for nodeid, phases in sorted(per_test.items())},
        "other_ports": dict(Counter(record["port"] for record in records if record["port"] != args.port)),
    }
    if args.pr815_body:
        named = pr815_counts(args.pr815_body)
        ours = Counter(Path(path).name for path in files.elements())
        report["vs_pr815_named_files"] = {name: {"pr815": count, "now": ours.get(name, 0)} for name, count in sorted(named.items())}
        report["vs_pr815_totals"] = {"pr815": {"connects": 127, "tests": 124, "files": 38, "setup_tests": 93, "call_tests": 32, "both": 1}, "now": {"connects": report["connects"], "tests": report["distinct_tests"], "files": report["distinct_files"], "setup_tests": report["tests_by_phase"].get("setup", 0), "call_tests": report["tests_by_phase"].get("call", 0), "both": report["tests_in_setup_and_call"]}}
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"port {args.port}: {report['connects']} connects, {report['distinct_tests']} tests, {report['distinct_files']} files; tests by phase {report['tests_by_phase']}, in setup and call {report['tests_in_setup_and_call']}")
    for key, value in report["openers"].items():
        print(f"  {value['connects']:4d} connects / {value['distinct_tests']:3d} tests  {key}  {value['phases']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
