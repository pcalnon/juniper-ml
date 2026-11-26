"""
Summarize flood-4 r49 test runs: per label, the junit verdicts and failure messages, the injected stops, where the
stub's get_status ran, the long GC passes, and the connect census.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; inputs written by
    util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py (<label>.junit.xml, .run.json, .connects.jsonl) and
    util/ad-hoc/2026-11-26_flood4_s16_r49_stall_plugin.py (<label>.r49.jsonl)

Usage:
    python3 -I <this file> --dir <run dir> [--label L ...] [--json-out <file>]
Without --label, every <label>.run.json (or <label>.runNN.run.json group) in --dir is summarized. Prints one JSON
object per label; --json-out also writes them all as one JSON document.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses junit files this session's own pytest runs wrote
from pathlib import Path

LATENCY_RE = re.compile(r"took (\d+\.\d+)s")


def junit_cases(path: Path) -> list[dict]:
    if not path.exists():
        return []
    root = ET.parse(path).getroot()  # nosec B314 - local junit written by this session's pytest
    cases = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        outcome = "failed" if failure is not None else "error" if error is not None else "skipped" if skipped is not None else "passed"
        node = failure if failure is not None else error
        message = (node.get("message") or "") if node is not None else ""
        cases.append({"name": case.get("name"), "classname": case.get("classname"), "time": float(case.get("time") or 0), "outcome": outcome, "message": message[:400]})
    return cases


def jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def spread(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"n": len(values), "min": round(min(values), 4), "median": round(statistics.median(values), 4), "max": round(max(values), 4)}


def summarize(directory: Path, label: str) -> dict:
    run_files = sorted(directory.glob(f"{label}.run.json")) or sorted(directory.glob(f"{label}.run[0-9][0-9].run.json"))
    tags = [p.name[: -len(".run.json")] for p in run_files]
    cases, connects, exits = [], [], []
    for tag in tags:
        cases += junit_cases(directory / f"{tag}.junit.xml")
        connects += jsonl(directory / f"{tag}.connects.jsonl")
        record = json.loads((directory / f"{tag}.run.json").read_text(encoding="utf-8"))
        exits.append(record.get("ci_effective_exit"))
    r49 = jsonl(directory / f"{label}.r49.jsonl")
    outcomes: dict[str, int] = {}
    for case in cases:
        outcomes[case["outcome"]] = outcomes.get(case["outcome"], 0) + 1
    messages: dict[str, int] = {}
    latencies = []
    for case in cases:
        if case["outcome"] in ("failed", "error"):
            short = LATENCY_RE.sub("took <s>s", case["message"].splitlines()[0] if case["message"] else "")[:220]
            messages[short] = messages.get(short, 0) + 1
            match = LATENCY_RE.search(case["message"])
            if match:
                latencies.append(float(match.group(1)))
    calls = [r for r in r49 if r["kind"] == "call"]
    stops = [r["seconds"] for r in r49 if r["kind"] == "stop"]
    gcs = [r for r in r49 if r["kind"] == "gc"]
    # A stop injected while the call is held lands inside the hold when the first call's time in the call covers it.
    first_end = {r["test"]: r["seconds_in_call"] for r in r49 if r["kind"] == "call_end" and r.get("first")}
    stop_by_test = {r["test"]: r["seconds"] for r in r49 if r["kind"] == "stop"}
    covered = [first_end[t] - s for t, s in stop_by_test.items() if t in first_end]
    session = next((r for r in r49 if r["kind"] == "session"), None)
    modules = next((r for r in r49 if r["kind"] == "modules"), None)
    return {
        "label": label,
        "processes": len(tags),
        "ci_effective_exits": sorted(set(exits)),
        "cases": len(cases),
        "outcomes": outcomes,
        "failure_messages": messages,
        "failure_latency_s": spread(latencies),
        "stub_calls": len(calls),
        "stub_calls_on_main_thread": sum(1 for c in calls if c["on_main_thread"]),
        "stops_s": spread(stops),
        "stop_kinds": sorted({f"{r.get('stop_kind')}@{r.get('point')}" for r in r49 if r["kind"] == "stop"}),
        "first_call_seconds_in_call": spread(list(first_end.values())),
        "tests_whose_first_call_outlasted_the_stop": sum(1 for d in covered if d >= 0),
        "first_call_minus_stop_s": spread(covered),
        "gc_passes_ge_min": spread([g["seconds"] for g in gcs]),
        "gc_generations": sorted({g["generation"] for g in gcs}),
        "gc_threads": sorted({g["thread"] for g in gcs}),
        "connects": len(connects),
        "connects_refused": sum(1 for c in connects if c.get("refused")),
        "connects_juniper_ports": sum(1 for c in connects if c.get("refused") == "juniper"),
        "python": (session or {}).get("python", "").split(" ")[0] if session else None,
        "modules": modules,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    directory = Path(args.dir)
    labels = args.label
    if not labels:
        found = set()
        for path in directory.glob("*.run.json"):
            name = path.name[: -len(".run.json")]
            found.add(re.sub(r"\.run\d\d$", "", name))
        labels = sorted(found)
    results = [summarize(directory, label) for label in labels]
    for result in results:
        print(json.dumps(result))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
