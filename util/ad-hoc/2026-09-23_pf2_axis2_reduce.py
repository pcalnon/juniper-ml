#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-2 axis 2
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/experiments/suites/perf/pf2-axis2-cascor-dataset-range.yaml

Reduce a PF-2 axis 2 suite: wall time against ``n_points_per_spiral``.

Two quantities, because they answer different halves of the owner's question:
  * ``wall_seconds`` (end to end, from ``aggregate.csv``). This includes juniper-data generating and
    staging the dataset, which genuinely scales with size. The lane DE-RATIFIED it as a GATE input
    because it absorbs plot rendering and bring-up. Here that is part of what is characterised,
    so it is reported, and read with that caveat.
  * ``step_sum_seconds`` (the service's own step histogram, via ``read_run_metrics.read_run``) --
    training compute only.
``drive`` is omitted: it is quantised to the 5 s poll and useless at these cell lengths.

Per size it prints the three passes' median / min / max, the growth factor against the smallest
size, and the local log-log slope between neighbouring sizes. Slope 1 is linear scaling. A slope
that jumps between neighbours is the "knee" that triggers the owner's in-process follow-up (the
rulings doc §5, D4). ``step_count`` is printed so a reader can see it is budget-bound, and it is
never compared.

Usage::

    python3 util/ad-hoc/2026-09-23_pf2_axis2_reduce.py ~/.local/state/juniper-experiments/suites/pf2-axis2-cascor-dataset-range-<stamp>
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments import read_run_metrics as rrm  # noqa: E402  (path-invoked util import)

RUN_ROOT = Path.home() / ".local/state/juniper-experiments"
KEY = "dataset.params.n_points_per_spiral"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("suite_dir", type=Path)
    args = parser.parse_args()
    rows = list(csv.DictReader((args.suite_dir / "aggregate.csv").open(encoding="utf-8")))
    by_size: dict[int, list[dict]] = {}
    bad = []
    for row in rows:
        if row.get("outcome") != "succeeded":
            bad.append((row.get("cell_id"), row.get(KEY), row.get("outcome")))
            continue
        metrics = rrm.read_run(RUN_ROOT / row["run_id"])
        by_size.setdefault(int(row[KEY]), []).append({"wall": float(row["wall_seconds"]), "step_sum": metrics.get("step_sum_seconds"), "steps": metrics.get("step_count"), "completion": metrics.get("completion_reason")})
    if bad:
        print("NOT SUCCEEDED (read these first -- a breach is a result, a staging failure is not):")
        for cell, size, outcome in bad:
            print(f"  {cell}  n={size}  outcome={outcome}")
        print()
    sizes = sorted(by_size)
    if not sizes:
        print("no succeeded cells")
        return 2
    base = sizes[0]
    base_wall = statistics.median(r["wall"] for r in by_size[base])
    base_step = statistics.median(r["step_sum"] for r in by_size[base] if r["step_sum"] is not None)
    print(f"{'n/spiral':>9} {'passes':>6} {'wall med':>9} {'wall min-max':>15} {'x base':>7} {'slope':>6} | {'step_sum med':>12} {'x base':>7} {'slope':>6} | steps  completion")
    prev = None
    for size in sizes:
        recs = by_size[size]
        walls = [r["wall"] for r in recs]
        steps_sums = [r["step_sum"] for r in recs if r["step_sum"] is not None]
        wall_med = statistics.median(walls)
        step_med = statistics.median(steps_sums) if steps_sums else float("nan")
        slope_w = slope_s = ""
        if prev is not None:
            ps, pw, pst = prev
            slope_w = f"{math.log(wall_med / pw) / math.log(size / ps):.2f}"
            if steps_sums and not math.isnan(pst):
                slope_s = f"{math.log(step_med / pst) / math.log(size / ps):.2f}"
        step_counts = sorted({r["steps"] for r in recs})
        completions = sorted({str(r["completion"]) for r in recs})
        print(f"{size:>9} {len(recs):>6} {wall_med:>9.2f} {min(walls):>7.2f}-{max(walls):<7.2f} {wall_med / base_wall:>7.2f} {slope_w:>6} | {step_med:>12.3f} {step_med / base_step:>7.2f} {slope_s:>6} | {step_counts} {completions}")
        prev = (size, wall_med, step_med)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
