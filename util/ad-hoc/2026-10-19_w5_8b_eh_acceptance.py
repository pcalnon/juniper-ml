#!/usr/bin/env python3
"""W5.8 (B) acceptance on the E-H equities artifact: a bare request's default readout, fold by fold.

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.8 (B) acceptance, W5.9 flags)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (the measurement the model / service PRs quote)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W5.8 acceptance: "a bare /v1/crossval on the E-H artifact aggregates above -1 and the
         response reports the selected lambda"); reports/2026-10-05_recurrence-equities-cv-consensus/
         laneB2.md Appendix A (the re-derivation this mirrors, including its embargo=2 folds)

Usage (an env holding juniper-recurrence-model with W5.9 + W5.8 (B), juniper-recurrence >= 0.6.1
with W5.10, juniper-model-core[crossval]):

    python util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py [--npz PATH] [--embargo N]

Mirrors what ``POST /v1/crossval`` does per fold -- ``build_lmu_regressor`` with the request's
``ridge=None`` falling back to ``default_ridge``, ``model.fit`` on the fold's train rows with the
artifact's timing kwargs, the fold's eval r2, and ``readout_diagnostics`` off the fitted model --
without the HTTP layer or juniper-data (the artifact is read from disk). Prints each default's
per-fold eval r2, the selected lambda and the W5.9 flags, then the aggregate (mean of folds, the
route's aggregate).
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model.model import _regression_metrics

from juniper_recurrence._readout import build_lmu_regressor, readout_diagnostics

DEFAULT_NPZ = pathlib.Path(__file__).resolve().parents[2] / "reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/equities_seq-6.0.0-15505731cba5b86d.npz"


def run(default_ridge, seq, folds, aux_all, label: str) -> dict:
    rows = []
    for i, fold in enumerate(folds):
        tr, ev = np.asarray(fold.train_idx), np.asarray(fold.eval_idx)
        atr = {k: v[tr] for k, v in aux_all.items()}
        aev = {k: v[ev] for k, v in aux_all.items()}
        model = build_lmu_regressor(d=16, theta=None, readout=None, ridge=None, rff_features=None, rff_gamma=None, default_ridge=default_ridge)
        model.fit(seq.X[tr], seq.y[tr], **atr)
        r2 = _regression_metrics(np.asarray(seq.y[ev], float).reshape(len(ev), -1), model.predict(seq.X[ev], **aev))["r2"]
        diag = readout_diagnostics(model).model_dump()
        rows.append({"fold": i, "n_train": int(len(tr)), "n_eval": int(len(ev)), "eval_r2": float(r2), "train_r2": float(model.metrics()["r2"]), **diag})
        print(f"{label} fold {i}: eval r2 {r2:+.4f}  train r2 {model.metrics()['r2']:+.4f}  ridge_mode {diag['ridge_mode']} lambda {diag['ridge_selected']}  at_edge {diag['gcv_at_edge']}  null_model {diag['null_model']}  theta {diag['theta']}")
    agg = float(np.mean([r["eval_r2"] for r in rows]))
    print(f"{label} aggregate (mean of folds): {agg:+.4f}")
    return {"default_ridge": default_ridge, "aggregate_eval_r2": agg, "folds": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--npz", type=pathlib.Path, default=DEFAULT_NPZ)
    parser.add_argument("--embargo", type=int, default=2, help="windows; lane B2 used 2, the route's request default differs -- both are printed by --both")
    parser.add_argument("--json", type=pathlib.Path, default=None, help="write the rows here")
    args = parser.parse_args()
    arrays = {k: v for k, v in np.load(args.npz, allow_pickle=False).items()}
    seq = sequence_data_from_arrays(arrays, "full")
    n = seq.X.shape[0]
    folds = walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=args.embargo)
    aux_all = seq.fit_kwargs()
    print(f"artifact {args.npz.name}: {n} windows (full view); 5 expanding folds, embargo {args.embargo}")
    out = {"npz": str(args.npz), "n_windows_full": int(n), "embargo": args.embargo, "runs": []}
    out["runs"].append(run(0.0, seq, folds, aux_all, "default_ridge=0.0 (the 0.6.x default)"))
    out["runs"].append(run("gcv", seq, folds, aux_all, "default_ridge='gcv' (W5.8 (B))"))
    if args.json:
        args.json.write_text(json.dumps(out, indent=2) + "\n")
    accepted = out["runs"][1]["aggregate_eval_r2"] > -1.0 and all(r["ridge_selected"] is not None for r in out["runs"][1]["folds"])
    print("ACCEPTANCE (aggregate > -1 and every fold reports its lambda):", "PASS" if accepted else "FAIL")
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
