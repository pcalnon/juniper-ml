#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-2 axis 3 seed probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Reducer for ``util/ad-hoc/2026-09-24_pf2_axis3_seed_probe.yaml``: over several DATASET seeds, does
4 spirals score above 5 (the order difficulty predicts), or was the 2026-09-23 inversion
(roc_auc 0.6721 at 4 against 0.7458 at 5, one seed) a property of that seed?

It reads TEST metrics only -- ``eval_metrics.final`` with ``split == "test"`` -- because a run's
top-level f1 / roc_auc are the selected-on validation split (the axis-3 reducer's first draft read
those). It pairs cells BY SEED and counts, per metric, the seeds on which 4 beats 5. f1 is also
reported divided by chance (1/n), because raw f1 falls with class count even when nothing got
harder.

Usage::

    python3 util/ad-hoc/2026-09-24_pf2_axis3_seed_probe_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-seed-probe-<stamp>
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

SEED = "dataset.params.seed"
N = "dataset.params.n_spirals"


def _test_metrics(run_dir: Path) -> dict | None:
    try:
        final = json.loads((run_dir / "artifacts" / "results" / "metrics_final.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    test = (final.get("eval_metrics") or {}).get("final") or {}
    return test if test.get("split") == "test" else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite-dir", type=Path, required=True)
    args = parser.parse_args()
    registry = args.suite_dir / "registry.jsonl"
    if not registry.is_file():
        print(f"no registry.jsonl under {args.suite_dir}")
        return 2

    table: dict[int, dict[int, dict]] = {}
    problems = []
    for line in registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cell = json.loads(line)
        seed, n = cell["overrides"].get(SEED), cell["overrides"].get(N)
        if cell.get("outcome") != "succeeded":
            problems.append(f"{cell.get('cell_id')} seed={seed} n={n}: outcome={cell.get('outcome')}")
            continue
        test = _test_metrics(Path(cell["run_dir"]))
        if test is None:
            problems.append(f"{cell.get('cell_id')} seed={seed} n={n}: no test-split eval_metrics")
            continue
        table.setdefault(int(seed), {})[int(n)] = {"roc_auc": test.get("roc_auc"), "f1": test.get("f1"), "f1_vs_chance": (test.get("f1") or 0.0) * int(n)}
    for problem in problems:
        print("NOT USABLE:", problem)

    ns = sorted({n for per_seed in table.values() for n in per_seed})
    print(f"{'seed':>6} | " + " | ".join(f"n={n}: roc_auc   f1  f1/chance" for n in ns))
    for seed in sorted(table):
        row = []
        for n in ns:
            m = table[seed].get(n)
            row.append(f"{m['roc_auc']:.4f} {m['f1']:.4f} {m['f1_vs_chance']:.2f}" if m else "      missing       ")
        print(f"{seed:>6} | " + " | ".join(f"    {r}" for r in row))

    paired = [s for s in sorted(table) if 4 in table[s] and 5 in table[s]]
    print(f"\npaired seeds: {len(paired)}")
    for metric in ("roc_auc", "f1", "f1_vs_chance"):
        wins = sum(table[s][4][metric] > table[s][5][metric] for s in paired)
        diffs = [table[s][4][metric] - table[s][5][metric] for s in paired]
        med = statistics.median(diffs) if diffs else float("nan")
        print(f"  {metric:<13} 4 beats 5 on {wins}/{len(paired)} seeds; median(4 - 5) = {med:+.4f}")
    print("scope: dataset seeds only -- the service fixes the network initialisation; spiral-smoke budgets otherwise")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
