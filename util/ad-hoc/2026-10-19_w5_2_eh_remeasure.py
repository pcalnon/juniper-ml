#!/usr/bin/env python3
"""W5.2 re-measurement on the E-H equities artifact: the trainval pool, folds cut by the W5.2 builder.

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.2 -> W5.4 edge: the R5 band is re-measured on train + val)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (the numbers the plan and the W5.4 band quote)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W5.2 Details, "Consequences recorded 2026-10-05"; W5.4 Amended 2026-10-05: re-measure on 1,522
         windows before encoding); util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py (the full-view predecessor)

Usage (an env with juniper-recurrence-model >= 0.6.0 and juniper-recurrence carrying W5.2):

    python util/ad-hoc/2026-10-19_w5_2_eh_remeasure.py [--npz PATH] [--json OUT]

Mirrors ``POST /v1/crossval`` per fold -- ``build_folds`` on the ``trainval`` view with the request
defaults (embargo = look-back, no embargo_days), ``build_lmu_regressor`` with the service's 0.7.0
default (``ridge=None`` -> ``"gcv"``) and the plan's recommended configuration (RFF, ridge 1.0,
256 features, median gamma), each fold's eval r2, the aggregate and its std -- the two numbers the
R5 band keys on (``cv_r2``, ``cv_r2_std``).
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model.model import _regression_metrics

from juniper_recurrence._folds import build_folds
from juniper_recurrence._readout import build_lmu_regressor, readout_diagnostics

DEFAULT_NPZ = pathlib.Path(__file__).resolve().parents[2] / "reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/equities_seq-6.0.0-15505731cba5b86d.npz"

CONFIGS = {
    "bare default (linear, gcv, standardised)": dict(readout=None, ridge=None, rff_features=None, rff_gamma=None),
    "recommended (rff, ridge 1.0, 256, median)": dict(readout="rff", ridge=1.0, rff_features=256, rff_gamma="median"),
}


def run(label: str, cfg: dict, seq, folds, aux_all) -> dict:
    rows = []
    for i, fold in enumerate(folds):
        tr, ev = np.asarray(fold.train_idx), np.asarray(fold.eval_idx)
        atr = {k: v[tr] for k, v in aux_all.items()}
        aev = {k: v[ev] for k, v in aux_all.items()}
        model = build_lmu_regressor(d=16, theta=None, default_ridge="gcv", **cfg)
        model.fit(seq.X[tr], seq.y[tr], **atr)
        r2 = float(_regression_metrics(np.asarray(seq.y[ev], float).reshape(len(ev), -1), model.predict(seq.X[ev], **aev))["r2"])
        diag = readout_diagnostics(model).model_dump()
        rows.append({"fold": i, "n_train": int(len(tr)), "n_eval": int(len(ev)), "eval_r2": r2, "train_r2": float(model.metrics()["r2"]), **diag})
        print(f"{label} fold {i}: n_train {len(tr):4d} n_eval {len(ev):3d} eval r2 {r2:+.4f} train r2 {model.metrics()['r2']:+.4f} lambda {diag['ridge_selected']} at_edge {diag['gcv_at_edge']} null_model {diag['null_model']}")
    r2s = np.array([r["eval_r2"] for r in rows])
    agg, std = float(r2s.mean()), float(r2s.std())
    print(f"{label}: cv_r2 {agg:+.4f}  cv_r2_std {std:.4f}  (R5 band: cv_r2 in [-1.0, +0.5], cv_r2_std <= 0.5 -> {'PASS' if -1.0 <= agg <= 0.5 and std <= 0.5 else 'FAIL'})")
    return {"config": label, "cv_r2": agg, "cv_r2_std": std, "folds": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npz", type=pathlib.Path, default=DEFAULT_NPZ)
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()
    arrays = {k: v for k, v in np.load(args.npz, allow_pickle=False).items()}
    seq = sequence_data_from_arrays(arrays, "trainval")
    folds, spec = build_folds(seq, n_folds=5, scheme="expanding", embargo=None, min_train=None, embargo_days=None)
    print(f"artifact {args.npz.name}: trainval pool {seq.X.shape[0]} windows (train {arrays['X_train'].shape[0]} + val {arrays['X_val'].shape[0]}; test {arrays['X_test'].shape[0]} excluded)")
    print(f"folding: {spec}")
    aux_all = seq.fit_kwargs()
    out = {"npz": str(args.npz), "n_pool": int(seq.X.shape[0]), "folding": spec.__dict__, "runs": [run(label, cfg, seq, folds, aux_all) for label, cfg in CONFIGS.items()]}
    if args.json:
        args.json.write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
