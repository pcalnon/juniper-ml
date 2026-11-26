"""
Summarise the r49 code lens's verdict records (<prefix>.r49v.jsonl, written by the r49v_stall pytest plugin): per test,
how many runs passed and failed, the distinct failure messages, the injected stops and the stub's verdicts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26), a follow-up of ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16, code lens
    r49-val-code; the plugin is util/ad-hoc/2026-11-26_flood4_s16_r49-val-code_stall.py

Usage: python <this file> [--json OUT] JSONL [JSONL ...]
Prints one JSON line per input file and test (rep suffixes folded), and with --json writes them all to OUT.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict


def _base(nodeid: str) -> str:
    name = re.sub(r"\[rep\d+\]$", "", nodeid)
    return re.sub(r"-rep\d+\]$", "]", name)


def summarise(path: str) -> list[dict]:
    per: dict[str, dict] = defaultdict(lambda: {"runs": 0, "passed": 0, "failed": 0, "errors": Counter(), "stall_seconds": [], "stall_where": Counter(), "stub": Counter(), "seconds": [], "loop_only": []})
    session = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("kind") == "session":
                session = record
            if record.get("kind") != "verdict":
                continue
            row = per[_base(record["test"])]
            row["runs"] += 1
            row["passed" if record["passed"] else "failed"] += 1
            row["seconds"].append(record["seconds"])
            if record.get("error"):
                row["errors"][record["error"][:220]] += 1
            for stall in record.get("stalls", []):
                row["stall_seconds"].append(stall["seconds"])
                row["stall_where"][f"{stall['where']}/{stall['mech']}/{'main' if stall['main_thread'] else stall['thread']}"] += 1
            stub = record.get("stub") or {}
            if isinstance(stub.get("loop_only_seconds"), (int, float)):
                row["loop_only"].append(stub["loop_only_seconds"])
            key = json.dumps({k: stub.get(k) for k in ("calls", "ran_on_loop_thread", "released_by_loop") if k in stub}, sort_keys=True)
            row["stub"][key] += 1
    out = []
    for test, row in sorted(per.items()):
        stalls = row["stall_seconds"]
        out.append(
            {
                "file": path,
                "python": session.get("python", "").split()[0] if session else None,
                "config": {k: session.get(k) for k in ("seconds", "at", "mech", "heap_m", "repeat")} if session else None,
                "test": test,
                "runs": row["runs"],
                "passed": row["passed"],
                "failed": row["failed"],
                "test_seconds_min_max": [min(row["seconds"]), max(row["seconds"])] if row["seconds"] else None,
                "stalls": len(stalls),
                "stall_seconds_min_max": [min(stalls), max(stalls)] if stalls else None,
                "stall_where": dict(row["stall_where"]),
                "loop_only_seconds_min_max": [min(row["loop_only"]), max(row["loop_only"])] if row["loop_only"] else None,
                "errors": dict(row["errors"]),
                "stub_verdicts": dict(row["stub"]),
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    rows = []
    for path in args.paths:
        rows.extend(summarise(path))
    for row in rows:
        print(json.dumps(row, sort_keys=False))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
