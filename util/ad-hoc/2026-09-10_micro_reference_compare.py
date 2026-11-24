#!/usr/bin/env python3
"""
Compare two saved pytest-benchmark runs of the cascor micro timing reference offline, benchmark by benchmark, without re-running anything.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc — investigation (perf lane P2 item 2.4 follow-up: the quieter re-cut `0003` against the two loaded cuts `0001` / `0002`)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md

WHY THIS EXISTS

`pytest --benchmark-compare=NNNN` re-runs every benchmark to produce its comparison, which puts
~40 s of load on the host and produces a FOURTH run to explain. The saved JSON already holds every
statistic; this reads two of them and prints the per-benchmark ratio of medians, its distribution,
and how many benchmarks moved outside the run tier's 20.5% quiet band — a report, never a gate
(Overtoad decision 2026-09-07, P2 item 2.5).

    python3 util/ad-hoc/2026-09-10_micro_reference_compare.py --base PATH/0002_*.json --other PATH/0003_*.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

QUIET_BAND_PCT = 20.5


def load_run(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    benches = {b["fullname"]: b["stats"] for b in doc.get("benchmarks", [])}
    return {"path": str(path), "benchmarks": benches, "juniper_run": doc.get("juniper_run"), "machine": (doc.get("machine_info") or {}).get("juniper")}


def compare(base: dict, other: dict, stat: str = "median") -> dict:
    """Per-benchmark other/base ratio of ``stat`` over the benchmarks both runs carry."""
    rows = []
    for name, b in base["benchmarks"].items():
        o = other["benchmarks"].get(name)
        if o is None or not b.get(stat):
            continue
        rows.append({"name": name, "base": b[stat], "other": o[stat], "ratio": o[stat] / b[stat]})
    ratios = [r["ratio"] for r in rows]
    outside = [r for r in rows if abs(r["ratio"] - 1.0) * 100.0 > QUIET_BAND_PCT]
    summary = {
        "compared": len(rows),
        "only_in_base": sorted(set(base["benchmarks"]) - set(other["benchmarks"])),
        "only_in_other": sorted(set(other["benchmarks"]) - set(base["benchmarks"])),
        "ratio_median": round(statistics.median(ratios), 4) if ratios else None,
        "ratio_p10": round(sorted(ratios)[max(0, int(round(0.10 * (len(ratios) - 1))))], 4) if ratios else None,
        "ratio_p90": round(sorted(ratios)[max(0, int(round(0.90 * (len(ratios) - 1))))], 4) if ratios else None,
        "faster_count": sum(1 for r in ratios if r < 1.0),
        "slower_count": sum(1 for r in ratios if r > 1.0),
        "outside_quiet_band": len(outside),
        "outside_quiet_band_names": sorted((r["name"], round(r["ratio"], 3)) for r in outside),
    }
    return {"stat": stat, "rows": rows, "summary": summary}


def render(base: dict, other: dict, result: dict) -> str:
    s = result["summary"]
    lines = [
        f"base : {Path(base['path']).name}  loadavg {base.get('juniper_run', {}).get('loadavg')}",
        f"other: {Path(other['path']).name}  loadavg {other.get('juniper_run', {}).get('loadavg')}",
        f"machine identity identical: {base.get('machine') == other.get('machine')}",
        f"{result['stat']} ratio other/base over {s['compared']} shared benchmarks: median {s['ratio_median']}  p10 {s['ratio_p10']}  p90 {s['ratio_p90']}  ({s['faster_count']} faster, {s['slower_count']} slower)",
        f"outside the {QUIET_BAND_PCT}% band: {s['outside_quiet_band']}",
    ]
    for name, ratio in s["outside_quiet_band_names"]:
        lines.append(f"  {ratio:6.3f}  {name}")
    if s["only_in_base"] or s["only_in_other"]:
        lines.append(f"only in base: {s['only_in_base']}  only in other: {s['only_in_other']}")
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--other", type=Path, required=True)
    parser.add_argument("--stat", default="median", choices=("median", "mean", "min"))
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    base, other = load_run(args.base), load_run(args.other)
    result = compare(base, other, args.stat)
    print(render(base, other, result))
    if args.json is not None:
        args.json.write_text(json.dumps({"base": base["path"], "other": other["path"], **result}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
