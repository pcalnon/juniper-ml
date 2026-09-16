#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-2 axis-3 calibration
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Reducer for the PF-2 spiral-capacity calibration
(``util/ad-hoc/2026-09-12_pf2_spiral_capacity_calibration.yaml``).

THE QUESTION, AND WHY THE SUITE AGGREGATE CANNOT ANSWER IT
---------------------------------------------------------
The suite's own ``aggregate.csv`` reports ``step_count``, ``wall_seconds`` and mean step duration.
None of those can settle whether a DIFFICULTY axis expresses, for a measured reason: ``step_count``
is invariant to dataset size (that is the PF-2 finding this whole re-spec exists to escape), and
``n_spirals`` changes dataset size. Reading ``step_count`` across ``n_spirals`` therefore re-measures
the known invariant and reports "no difference" no matter what the network did.

The quantities that CAN move with difficulty live in the per-run evidence:

  hidden_units  -- how much structure the network had to grow
  epoch         -- growth iterations actually used
  f1 / roc_auc  -- whether the problem was solved at all

**Read accuracy first.** If every cell sits at chance, difficulty cannot express in ANY column and
the axis is untestable at that budget -- a capacity-bound result, not an inert axis. Those two
conclusions are opposite and the numbers alone do not separate them.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite-dir", type=Path, required=True, help="a completed suite directory")
    args = parser.parse_args()

    registry = args.suite_dir / "registry.jsonl"
    if not registry.is_file():
        print(f"no registry.jsonl under {args.suite_dir}")
        return 2

    rows = []
    for line in registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        run_dir = Path(entry.get("run_dir") or "")
        final = _load(run_dir / "artifacts" / "results" / "metrics_final.json")
        meta = next(iter((run_dir / "data").glob("*.meta.json")), None)
        dataset = _load(meta) if meta else {}
        ev = (final.get("eval_metrics") or {}).get("final") or {}
        rows.append(
            {
                "cell": entry.get("cell_id", "")[:4],
                "n_spirals": entry.get("overrides", {}).get("dataset.params.n_spirals"),
                "max_hidden": entry.get("overrides", {}).get("training.params.max_hidden_units"),
                "n_samples": dataset.get("n_samples"),
                "hidden_units": final.get("hidden_units"),
                "epoch": final.get("epoch"),
                "f1": final.get("f1"),
                "test_f1": ev.get("f1"),
                "test_roc_auc": ev.get("roc_auc"),
                "n_classes": ev.get("n_classes"),
            }
        )
    rows.sort(key=lambda r: (r["max_hidden"] or 0, r["n_spirals"] or 0))

    cols = ["cell", "n_spirals", "max_hidden", "n_samples", "hidden_units", "epoch", "f1", "test_f1", "test_roc_auc"]
    widths = {c: max(len(c), 12) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    for row in rows:
        out = []
        for c in cols:
            v = row[c]
            out.append(("" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))).ljust(widths[c]))
        print("  ".join(out))

    # The discriminations, stated rather than left to the reader.
    #
    # ⚠ THIS BLOCK'S FIRST DRAFT KEYED ITS VERDICT ON hidden_units ALONE and concluded "this
    # budget does NOT let spiral count express" -- which is false. hidden_units is pinned to the
    # BUDGET (the network saturates its capacity at every spiral count), so it can never
    # discriminate anything; reading a constant column and reporting "no difference" is the
    # instrument answering an adjacent question. Difficulty expresses in ACCURACY. Both columns
    # are judged below, separately, and the structural one is labelled as the non-discriminator
    # it is.
    print()
    for budget in sorted({r["max_hidden"] for r in rows if r["max_hidden"] is not None}):
        arm = sorted((r for r in rows if r["max_hidden"] == budget), key=lambda r: r["n_spirals"] or 0)
        grown = {r["hidden_units"] for r in arm}
        aucs = [r["test_roc_auc"] for r in arm if isinstance(r["test_roc_auc"], float)]
        print(f"max_hidden_units={budget}:")
        print(f"    hidden_units grown = {sorted(x for x in grown if x is not None)}", end="")
        if len(grown) == 1:
            print(f"  -> PINNED AT THE BUDGET; cannot discriminate (network saturates at every n_spirals)")
        else:
            print("  -> varies")
        if aucs:
            spread = max(aucs) - min(aucs)
            detail = ", ".join(f"{r['n_spirals']}sp={r['test_roc_auc']:.3f}" for r in arm if isinstance(r["test_roc_auc"], float))
            print(f"    test roc_auc       = {detail}   spread {spread:.3f}")
            print(f"    -> {'DIFFICULTY EXPRESSES in accuracy' if spread >= 0.05 else 'accuracy flat too -- axis truly inert here'}")

    # Chance is roc_auc ~ 0.5. Judge SOLVABILITY per spiral count, not globally: a global range
    # that spans 0.54..0.96 hides that only the smallest problem was ever solved.
    print()
    for n in sorted({r["n_spirals"] for r in rows if r["n_spirals"] is not None}):
        best = max((r["test_roc_auc"] for r in rows if r["n_spirals"] == n and isinstance(r["test_roc_auc"], float)), default=None)
        if best is None:
            continue
        verdict = "SOLVED" if best >= 0.85 else ("partial" if best >= 0.65 else "NEAR CHANCE -- unsolved at any budget tried")
        print(f"n_spirals={n:>3}: best test roc_auc {best:.4f}  -> {verdict}")

    out_csv = args.suite_dir / "capacity_reduction.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else cols)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
