#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-2 axis 3
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Reducer for ``util/experiments/suites/perf/pf2-axis3-cascor-spiral-count.yaml``: classification
difficulty against the number of spirals, read on ACCURACY.

WHY NOT THE SUITE'S OWN AGGREGATE
---------------------------------
``aggregate.csv`` / ``REPORT.md`` carry ``step_count``, wall time and mean step duration. The
2026-09-15 calibration (PF-2 re-spec §4.1) showed every structural column is pinned to the budget
on this axis -- hidden units grown == ``max_hidden_units`` and ``epoch`` == ``max_iterations`` + 1 in
every cell -- and ``step_count`` is fixed by ``output_epochs``. Reading any of them across
``n_spirals`` reports "no difference" whatever the network did. Accuracy is the observable, and it
lives in each run's ``artifacts/results/metrics_final.json``.

WHAT IT REPORTS
---------------
* per ``n_spirals``: TEST roc_auc / f1 (``eval_metrics.final``, checked to be labelled
  ``split == "test"``; the top-level figures are the selected-on validation split) and val
  accuracy per pass, with the pass-to-pass spread.
  Accuracy is numeric and the suite is ``seed_policy: fixed``, so passes should AGREE; a spread is
  flagged ``NONDETERMINISTIC`` rather than averaged away.
* the structural columns, each labelled ``BUDGET-BOUND`` when it equals its budget, so a constant
  column is never read as a finding.
* wall time, as context only (load-sensitive).
* a verdict on the ACCURACY column: whether roc_auc declines monotonically with ``n_spirals``, and
  where it first falls within ``--chance-margin`` of 0.5 (macro one-vs-rest chance).

Usage::

    python3 util/ad-hoc/2026-09-23_pf2_axis3_reduce.py --suite-dir ~/.local/state/juniper-experiments/suites/pf2-axis3-cascor-spiral-count-<stamp>
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

KEY = "dataset.params.n_spirals"
BUDGET_KEYS = {"hidden_units": "training.params.max_hidden_units", "epoch": "training.params.max_iterations"}


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _cells(suite_dir: Path) -> list[dict]:
    cells = []
    for line in (suite_dir / "registry.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            cells.append(json.loads(line))
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite-dir", type=Path, required=True)
    parser.add_argument("--chance-margin", type=float, default=0.10, help="roc_auc within this of 0.5 reads NEAR CHANCE (default %(default)s)")
    args = parser.parse_args()
    if not (args.suite_dir / "registry.jsonl").is_file():
        print(f"no registry.jsonl under {args.suite_dir}")
        return 2

    by_n: dict[int, list[dict]] = {}
    not_ok = []
    for cell in _cells(args.suite_dir):
        overrides = cell.get("overrides") or {}
        n = overrides.get(KEY)
        if cell.get("outcome") != "succeeded":
            not_ok.append((cell.get("cell_id"), n, cell.get("outcome")))
            continue
        final = _read_json(Path(cell["run_dir"]) / "artifacts" / "results" / "metrics_final.json")
        # The TOP-LEVEL f1 / roc_auc are the VALIDATION split -- the one training early-stops on,
        # so they are selected-on. The held-out figures are eval_metrics.final, labelled
        # split == "test". This reducer's first draft read the top level and reported 0.9808 for a
        # cell whose test roc_auc is 0.9605. Refuse a record whose label is not "test".
        test = (final.get("eval_metrics") or {}).get("final") or {}
        if test.get("split") != "test":
            not_ok.append((cell.get("cell_id"), n, f"no test-split eval_metrics (split={test.get('split')!r})"))
            continue
        record = {
            "pass": overrides.get("experiment.description", "?"),
            "roc_auc": test.get("roc_auc"),
            "f1": test.get("f1"),
            "val_accuracy": final.get("val_accuracy"),
            "hidden_units": final.get("hidden_units"),
            "epoch": final.get("epoch"),
            "wall": cell.get("wall_seconds"),
            "budgets": {col: overrides.get(key) for col, key in BUDGET_KEYS.items()},
        }
        by_n.setdefault(int(n), []).append(record)

    if not_ok:
        print("NOT SUCCEEDED (read these first):")
        for cell_id, n, outcome in not_ok:
            print(f"  {cell_id}  n_spirals={n}  outcome={outcome}")
        print()
    if not by_n:
        print("no succeeded cells")
        return 2

    print(f"{'n_spirals':>9} {'passes':>6} | {'test roc_auc (per pass)':<28} {'spread':>7} | {'test f1':>7} {'val_acc med':>11} | {'hidden':>10} {'epoch':>9} | {'wall med':>8}")
    medians: dict[int, float] = {}
    nondeterministic = []
    for n in sorted(by_n):
        recs = sorted(by_n[n], key=lambda r: r["pass"])
        aucs = [r["roc_auc"] for r in recs if isinstance(r["roc_auc"], (int, float))]
        f1s = [r["f1"] for r in recs if isinstance(r["f1"], (int, float))]
        vals = [r["val_accuracy"] for r in recs if isinstance(r["val_accuracy"], (int, float))]
        spread = (max(aucs) - min(aucs)) if aucs else float("nan")
        if aucs and spread > 0:
            nondeterministic.append(n)
        medians[n] = statistics.median(aucs) if aucs else float("nan")
        structural = []
        for col in ("hidden_units", "epoch"):
            values = sorted({r[col] for r in recs})
            budget = recs[0]["budgets"][col]
            bound = budget is not None and values and (values == [budget] or (col == "epoch" and values == [budget + 1]))
            structural.append(f"{values}{'*' if bound else ''}")
        auc_text = " ".join(f"{a:.4f}" for a in aucs)
        print(f"{n:>9} {len(recs):>6} | {auc_text:<28} {spread:>7.4f} | {statistics.median(f1s) if f1s else float('nan'):>7.4f} {statistics.median(vals) if vals else float('nan'):>11.4f} | {structural[0]:>10} {structural[1]:>9} | {statistics.median(r['wall'] for r in recs):>8.1f}")
    print("  * = BUDGET-BOUND: equals its budget in every pass, so the column cannot discriminate")
    print()

    ordered = [medians[n] for n in sorted(medians)]
    monotone = all(a >= b for a, b in zip(ordered, ordered[1:]))
    near_chance = [n for n in sorted(medians) if abs(medians[n] - 0.5) <= args.chance_margin]
    print(f"accuracy declines monotonically with n_spirals: {'YES' if monotone else 'NO'}  ({' -> '.join(f'{v:.3f}' for v in ordered)})")
    print(f"first n_spirals within {args.chance_margin} of chance (roc_auc 0.5): {near_chance[0] if near_chance else 'none in range'}")
    print(f"passes agree on roc_auc: {'YES (numeric outcome is load-insensitive here)' if not nondeterministic else 'NO -- NONDETERMINISTIC at n_spirals ' + str(nondeterministic)}")
    print("scope: 'unsolved at this budget' only -- output_epochs 50 and the candidate budget were not varied (re-spec §4.1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
