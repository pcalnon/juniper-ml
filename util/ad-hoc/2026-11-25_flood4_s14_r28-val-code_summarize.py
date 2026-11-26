"""
Summarise one r28-val-code run: JUnit totals and failures, held-call timings, GC passes, injected stalls, threads, leaks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code; inputs written by util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_run.py
    and util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_plugin.py

Usage:
    python <this file> <run dir> <label> [<label> ...] [--json <out.json>]

Reads <run dir>/<label>.run.json, <label>.junit.xml and <label>.r28v.jsonl. Prints one JSON object per label.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this lens's own runs wrote
from collections import Counter
from pathlib import Path


def junit_cases(path: Path) -> list[dict]:
    if not path.exists():
        return []
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):  # nosec B314 - local file written by this lens's run
        outcome, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome, message = tag, (node.get("message") or "")[:300]
        name = re.sub(r"\[rep\d+\]$", "", case.get("name", ""))
        cases.append({"test": name, "outcome": outcome, "time": float(case.get("time", "0") or 0), "message": message})
    return cases


def summarise(run_dir: Path, label: str) -> dict:
    out: dict = {"label": label}
    run = run_dir / f"{label}.run.json"
    if run.exists():
        record = json.loads(run.read_text(encoding="utf-8"))
        out.update({k: record.get(k) for k in ("raw_exit", "ci_effective_exit", "seconds", "junit", "connects_total", "connects_juniper_ports", "coverage_percent", "per_file_gate_exit")})
    cases = junit_cases(run_dir / f"{label}.junit.xml")
    per_test: dict = {}
    for case in cases:
        slot = per_test.setdefault(case["test"], Counter())
        slot[case["outcome"]] += 1
    out["per_test"] = {k: dict(v) for k, v in per_test.items()}
    failures = [c for c in cases if c["outcome"] in ("failure", "error")]
    out["failure_messages"] = Counter(re.sub(r"\d+\.\d+", "N", c["message"]) for c in failures).most_common(8)
    gaps = [float(m) for c in failures for m in re.findall(r"for (\d+\.\d+)s", c["message"])]
    if gaps:
        gaps.sort()
        out["failure_gaps_seconds"] = {"n": len(gaps), "min": gaps[0], "median": gaps[len(gaps) // 2], "max": gaps[-1]}
    rows = []
    jsonl = run_dir / f"{label}.r28v.jsonl"
    if jsonl.exists():
        rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    session = [r for r in rows if r["kind"] == "session"]
    if session:
        out["python"] = session[0]["python"].split()[0]
        out["loads"] = session[0]["loads"]
    files = sorted({r["file"] for r in rows if r["kind"] == "module_file"})
    if files:
        out["code_under_test_files"] = files
    held = [r for r in rows if r["kind"] == "held"]
    if held:
        off = [r for r in held if not r["ran_on_loop_thread"]]
        on = [r for r in held if r["ran_on_loop_thread"]]
        out["held"] = {
            "calls": len(held),
            "off_loop": len(off),
            "off_loop_released": sum(1 for r in off if r["released_by_loop"]),
            "off_loop_max_seconds_in_call": max((r["seconds_in_call"] for r in off), default=None),
            "on_loop": len(on),
            "on_loop_released": sum(1 for r in on if r["released_by_loop"]),
            "stall_injected_values": sorted({r.get("stall_injected", 0.0) for r in held}),
        }
        per: dict = {}
        for r in held:
            per.setdefault(re.sub(r"\[.*\]$", "", (r.get("test") or "").split("::")[-1]), []).append(r["seconds_in_call"])
        out["held"]["per_test_max_seconds_in_call"] = {k: max(v) for k, v in per.items()}
    calls = [r for r in rows if r["kind"] == "call_phase"]
    if calls:
        by: dict = {}
        for r in calls:
            by.setdefault(re.sub(r"\[.*\]$", "", r["test"].split("::")[-1]), []).append(r["seconds"])
        out["call_phase_seconds"] = {k: {"n": len(v), "min": min(v), "max": max(v)} for k, v in by.items()}
    pre = [r["module"] for r in rows if r["kind"] == "preimported"]
    if pre:
        out["preimported"] = pre
    gcs = [r for r in rows if r["kind"] == "gc"]
    if gcs:
        out["gc_passes_ge_threshold"] = {"n": len(gcs), "max": max(r["seconds"] for r in gcs), "generations": dict(Counter(r["generation"] for r in gcs)), "threads": dict(Counter(r["thread"] for r in gcs))}
        x7 = [r for r in gcs if r.get("test") and "test_x7_" in r["test"]]
        out["gc_passes_inside_x7_tests"] = [{"test": r["test"].split("::")[-1], "seconds": r["seconds"], "generation": r["generation"]} for r in x7][:20]
        reg = [r["seconds"] for r in gcs if r.get("test") and "src/tests/regression/" in r["test"] and r["generation"] == 2]
        if reg:
            out["gc_gen2_in_regression_dir"] = sorted(reg)
    stalls = [r for r in rows if r["kind"] == "gilstall"]
    if stalls:
        out["gilstalls"] = {"n": len(stalls), "min": min(r["seconds"] for r in stalls), "max": max(r["seconds"] for r in stalls)}
    leaks = [r for r in rows if r["kind"] == "leak"]
    if leaks:
        named = [(r["test"], [t["target"] or t["name"] for t in r["threads"]]) for r in leaks]
        out["leaks_with_demo_target"] = [n for n in named if any("DemoMode" in t or "demo" in t.lower() for t in n[1])][:20]
        out["leak_events"] = len(leaks)
    setups = [r for r in rows if r["kind"] == "threads_at_setup"]
    if setups:
        demo_counts = Counter(sum(1 for t in r["threads"] if "DemoMode" in (t["target"] or "")) for r in setups)
        out["demo_threads_at_x7_setup"] = dict(demo_counts)
        out["x7_setups"] = len(setups)
    return out


def main() -> int:
    args = sys.argv[1:]
    out_json = None
    if "--json" in args:
        index = args.index("--json")
        out_json = args[index + 1]
        args = args[:index] + args[index + 2 :]
    run_dir, labels = Path(args[0]), args[1:]
    results = [summarise(run_dir, label) for label in labels]
    for result in results:
        print(json.dumps(result, default=str))
    if out_json:
        Path(out_json).write_text(json.dumps(results, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
