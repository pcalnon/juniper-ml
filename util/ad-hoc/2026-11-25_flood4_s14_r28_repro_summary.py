"""
Summarise r28 reproduction-probe JSONL (util/ad-hoc/2026-11-25_flood4_s14_r28_repro_test.py output): per contention
cell and procedure, the distribution of the ticker's worst gap, how many runs cross the test's 0.2 s threshold, and
the shape probe's release outcome and latency.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Usage:
    python <this file> <probe .jsonl> [<probe .jsonl> ...] [--json <out .json>] [--threshold 0.2]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def _q(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--json", default="")
    parser.add_argument("--threshold", type=float, default=0.2)
    args = parser.parse_args()
    out = {}
    for name in args.files:
        rows = [json.loads(line) for line in Path(name).read_text(encoding="utf-8").splitlines() if line.strip()]
        per = {}
        for row in rows:
            per.setdefault((row["cell"], row["procedure"]), []).append(row)
        summary = {}
        for (cell, procedure), items in per.items():
            key = f"{cell}/{procedure}"
            if procedure == "cpu":
                summary[key] = {"cores_used": round(items[0].get("cores_used") or 0, 2), "wall_seconds": round(items[0]["wall_seconds"], 1)}
                continue
            entry = {"n": len(items), "demo_threads_alive": sorted({i.get("demo_threads_alive") for i in items})}
            if procedure in ("relay", "null"):
                gaps = [i["worst_gap"] for i in items]
                entry.update({"worst_gap_max": round(max(gaps), 3), "worst_gap_p90": round(_q(gaps, 0.9), 3), "worst_gap_median": round(statistics.median(gaps), 3), "worst_gap_min": round(min(gaps), 3), f"runs_at_or_over_{args.threshold}": sum(1 for g in gaps if g >= args.threshold)})
            if procedure == "relay":
                entry["stub_on_loop_thread"] = sorted({i["stub_on_loop_thread"] for i in items})
                entry["elapsed_max"] = round(max(i["elapsed"] for i in items), 3)
            if procedure == "held":
                latencies = [i["release_latency"] for i in items]
                entry["released_by_loop"] = sorted({str(i["released_by_loop"]) for i in items})
                entry["off_loop"] = sorted({str(i["off_loop"]) for i in items})
                entry.update({"release_latency_max": round(max(latencies), 3), "release_latency_p90": round(_q(latencies, 0.9), 3), "release_latency_median": round(statistics.median(latencies), 3)})
            if procedure == "shape":
                entry["released_by_loop"] = sorted({str(i["released_by_loop"]) for i in items})
                entry["off_loop"] = sorted({str(i["off_loop"]) for i in items})
                entry["elapsed_max"] = round(max(i["elapsed"] for i in items), 3)
                entry["elapsed_median"] = round(statistics.median(i["elapsed"] for i in items), 3)
            summary[key] = entry
        out[name] = summary
        print(f"== {name}")
        for key, entry in summary.items():
            print(f"  {key:22s} {json.dumps(entry)}")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
