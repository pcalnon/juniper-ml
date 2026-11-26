"""
Report on an r28 thread census (util/ad-hoc/2026-11-25_flood4_s14_r28_thread_census.py output): which tests leave
DemoMode training threads (and other threads) running, and how many are alive when each X7 timing test starts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Usage:
    python <this file> --census <run>.census.jsonl [--json <out .json>] [--watch test_x7_]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

MARK = "(_training_loop)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True)
    parser.add_argument("--json", default="")
    parser.add_argument("--watch", default="test_x7_")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.census).read_text(encoding="utf-8").splitlines() if line.strip()]
    leakers = []
    other_leaks = collections.Counter()
    for row in rows:
        demo = [n for n in row.get("leaked", []) if n.endswith(MARK)]
        others = [n for n in row.get("leaked", []) if not n.endswith(MARK)]
        if demo:
            leakers.append({"nodeid": row["nodeid"], "demo_threads_left_running": len(demo), "training_loop_after": row.get("training_loop_after")})
        for name in others:
            base = name.split("-")[0] if name.startswith("Thread-") else name
            other_leaks[(row["nodeid"].split("::")[0], base.split(" ")[0] if base.startswith("Thread") else name)] += 1
    by_file = collections.Counter(entry["nodeid"].split("::")[0] for entry in leakers)
    watched = [{"nodeid": r["nodeid"], "training_loop_at_setup": r.get("training_loop_at_setup"), "alive_at_setup": r.get("alive_at_setup")} for r in rows if args.watch in r["nodeid"]]
    peak = max(rows, key=lambda r: r.get("training_loop_at_setup", 0)) if rows else {}
    report = {
        "tests_recorded": len(rows),
        "tests_leaving_demo_threads_running": len(leakers),
        "demo_threads_left_running_total": sum(e["demo_threads_left_running"] for e in leakers),
        "leaking_files": dict(by_file.most_common()),
        "leakers": leakers,
        "peak_training_loop_at_setup": {"nodeid": peak.get("nodeid"), "count": peak.get("training_loop_at_setup")},
        "watched": watched,
        "other_thread_leaks_by_file_and_name": [{"file": f, "thread": n, "count": c} for (f, n), c in other_leaks.most_common(40)],
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("tests_recorded", "tests_leaving_demo_threads_running", "demo_threads_left_running_total", "leaking_files", "peak_training_loop_at_setup")}, indent=1))
    print("WATCHED:")
    for entry in watched:
        print(f"  {entry['training_loop_at_setup']:>3} demo / {entry['alive_at_setup']:>3} threads  {entry['nodeid']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
