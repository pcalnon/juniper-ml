#!/usr/bin/env python3
"""Reconciler re-derivation of Lane B2's lone measurements (consensus review of the W5.1 note).

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use measurement script)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc; written for notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md
             (procedure §5.2: a lone finding is a lead until the reconciler re-derives it).

What it re-derives, on the frozen audit artifact ``equities_seq-6.0.0-15505731cba5b86d`` with the
model's OWN readout functions (not a re-implementation of the solver):

  A. fidelity        -- rff / ridge 1.0 / raw through ``build_lmu_regressor``; expect the note's
                        five folds (-0.0803 / -0.0500 / -0.1020 / -0.0856 / -0.2584).
  B. linear/gcv/raw  -- through ``build_lmu_regressor(ridge="gcv")`` (expect -217.6 ... -975.5,
                        aggregate -246.9) and with ``_GCV_GRID`` extended to 1e12 (Lane B2: ~ -35).
  C. option (ii)     -- the linear rung with the RFF rung's per-fold train-only standardisation
                        (``_standardize_fit``) and the rung's own solvers: lstsq (ridge 0),
                        ``_ridge_solve`` (ridge 1.0), ``_gcv_select`` on the shipped grid, and
                        ``_gcv_select`` on the extended grid (Lane B2: -8.8e12 / -191.9 / -0.195 / -0.019).
  D. GCV vs null     -- for the linear/raw and rff/raw rungs, GCV(lambda) at the capped and extended
                        argmin against GCV(lambda -> inf) (the intercept-only model); Lane B2 says the
                        null model is the optimum in three of five RFF folds and in all linear/raw folds.

The GCV curve helper reproduces ``_gcv_select``'s algebra so the curve can be read off; it is
validated per fold by checking that its argmin on the shipped grid equals the lambda the library's
``_gcv_select`` returns on the same inputs.

Run:
    /opt/miniforge3/envs/JuniperCascor1/bin/python \
        util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive.py \
        --npz /home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz \
        --out reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence._readout import build_lmu_regressor
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model import readouts as ro
from juniper_recurrence_model.model import _regression_metrics

EXT_GRID = np.logspace(-6.0, 12.0, 181)


def gcv_curve(features: np.ndarray, y: np.ndarray, grid: np.ndarray) -> tuple[np.ndarray, float]:
    """GCV(lambda) over ``grid`` with ``_gcv_select``'s algebra, plus GCV(lambda -> inf) (null model)."""
    n = features.shape[0]
    fc = features - features.mean(axis=0)
    yc = y - y.mean(axis=0)
    u, s, _vt = np.linalg.svd(fc, full_matrices=False)
    g = u.T @ yc
    s2 = s**2
    energy = float(np.sum(yc**2))
    perp = energy - float(np.sum(g**2))
    out = []
    for lam in grid:
        tr_h = 1.0 + float(np.sum(s2 / (s2 + lam)))
        shrink = (lam / (s2 + lam)) ** 2
        rss = float(np.sum(shrink[:, None] * (g**2))) + perp
        denom = (n - tr_h) ** 2
        out.append(n * rss / denom if denom > 0 else np.inf)
    null = n * energy / (n - 1.0) ** 2
    return np.asarray(out), null


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(_regression_metrics(y_true, y_pred)["r2"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with np.load(args.npz, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    seq = sequence_data_from_arrays(arrays, "full")
    n = int(seq.X.shape[0])
    folds = walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=2)
    aux_all = seq.fit_kwargs()
    report: dict = {"npz": args.npz, "n_windows_full": n, "folds": []}

    for i, fold in enumerate(folds):
        tr, ev = fold.train_idx, fold.eval_idx
        aux_tr = {k: v[tr] for k, v in aux_all.items()}
        aux_ev = {k: v[ev] for k, v in aux_all.items()}
        Xtr, Xev = seq.X[tr], seq.X[ev]
        ytr, yev = seq.y[tr], seq.y[ev]
        row: dict = {"fold": i, "n_train": int(len(tr)), "n_eval": int(len(ev))}

        # A. fidelity: rff / 1.0 / raw through the service's own factory
        m_rff = build_lmu_regressor(d=16, theta=None, readout="rff", ridge=1.0, rff_features=256, rff_gamma="median", default_ridge=0.0)
        m_rff.fit(Xtr, ytr, **aux_tr)
        row["A_rff_1.0_eval_r2"] = r2(yev, m_rff.predict(Xev, **aux_ev))
        row["A_theta"] = float(m_rff.theta)

        # B. linear / gcv / raw through the factory, shipped grid
        m_lin_gcv = build_lmu_regressor(d=16, theta=None, readout="linear", ridge="gcv", default_ridge=0.0)
        m_lin_gcv.fit(Xtr, ytr, **aux_tr)
        row["B_linear_gcv_capped_eval_r2"] = r2(yev, m_lin_gcv.predict(Xev, **aux_ev))
        row["B_linear_gcv_capped_lambda"] = float(m_lin_gcv._readout.ridge)  # noqa: SLF001

        # memory blocks and side channel exactly as LinearReadout / RFFReadout receive them
        M_tr = m_lin_gcv._memory_block(np.asarray(Xtr, dtype=float), aux_tr.get("dt"), None, aux_tr.get("seq_lengths"))  # noqa: SLF001
        M_ev = m_lin_gcv._memory_block(np.asarray(Xev, dtype=float), aux_ev.get("dt"), None, aux_ev.get("seq_lengths"))  # noqa: SLF001
        side_tr = m_lin_gcv._side_channel(aux_tr.get("target_dt"), len(tr))  # noqa: SLF001
        side_ev = m_lin_gcv._side_channel(aux_ev.get("target_dt"), len(ev))  # noqa: SLF001
        ytr64 = np.asarray(ytr, dtype=float).reshape(len(tr), -1)
        yev64 = np.asarray(yev, dtype=float).reshape(len(ev), -1)

        # helper validation: argmin on the shipped grid must equal the library's selected lambda
        feats_lin = np.concatenate([M_tr, side_tr], axis=1)
        curve_lin, null_lin = gcv_curve(feats_lin, ytr64, ro._GCV_GRID)  # noqa: SLF001
        helper_lam = float(ro._GCV_GRID[int(np.argmin(curve_lin))])  # noqa: SLF001
        row["helper_argmin_matches_library"] = bool(helper_lam == row["B_linear_gcv_capped_lambda"])
        row["helper_lambda"] = helper_lam

        # B (extended grid): linear/raw with _GCV_GRID monkeypatched to 1e12
        saved_grid = ro._GCV_GRID  # noqa: SLF001
        try:
            ro._GCV_GRID = EXT_GRID  # noqa: SLF001
            coef_ext, lam_ext = ro._gcv_select(feats_lin, ytr64)  # noqa: SLF001
        finally:
            ro._GCV_GRID = saved_grid  # noqa: SLF001
        pred_ext = ro._assemble_design(M_ev, side_ev) @ coef_ext  # noqa: SLF001
        row["B_linear_gcv_ext_eval_r2"] = r2(yev64, pred_ext)
        row["B_linear_gcv_ext_lambda"] = float(lam_ext)
        curve_lin_ext, _ = gcv_curve(feats_lin, ytr64, EXT_GRID)
        row["D_linear_gcv_min_over_null_minus_1"] = float(curve_lin_ext.min() / null_lin - 1.0)
        row["D_linear_null_is_below_every_grid_point"] = bool(np.all(curve_lin_ext > null_lin))

        # C. option (ii): standardised linear rung, the rung's own solvers
        mu, sd = ro._standardize_fit(M_tr)  # noqa: SLF001
        Z_tr = (M_tr - mu) / sd
        Z_ev = (M_ev - mu) / sd
        D_tr = ro._assemble_design(Z_tr, side_tr)  # noqa: SLF001
        D_ev = ro._assemble_design(Z_ev, side_ev)  # noqa: SLF001
        coef0, *_ = np.linalg.lstsq(D_tr, ytr64, rcond=None)
        row["C_std_linear_ridge0_eval_r2"] = r2(yev64, D_ev @ coef0)
        row["C_std_linear_ridge0_train_r2"] = r2(ytr64, D_tr @ coef0)
        coef1 = ro._ridge_solve(D_tr, ytr64, 1.0)  # noqa: SLF001
        row["C_std_linear_ridge1_eval_r2"] = r2(yev64, D_ev @ coef1)
        row["C_std_linear_ridge1_train_r2"] = r2(ytr64, D_tr @ coef1)
        feats_std = np.concatenate([Z_tr, side_tr], axis=1)
        coef_g, lam_g = ro._gcv_select(feats_std, ytr64)  # noqa: SLF001
        row["C_std_linear_gcv_capped_eval_r2"] = r2(yev64, D_ev @ coef_g)
        row["C_std_linear_gcv_capped_train_r2"] = r2(ytr64, D_tr @ coef_g)
        row["C_std_linear_gcv_capped_lambda"] = float(lam_g)
        try:
            ro._GCV_GRID = EXT_GRID  # noqa: SLF001
            coef_ge, lam_ge = ro._gcv_select(feats_std, ytr64)  # noqa: SLF001
        finally:
            ro._GCV_GRID = saved_grid  # noqa: SLF001
        row["C_std_linear_gcv_ext_eval_r2"] = r2(yev64, D_ev @ coef_ge)
        row["C_std_linear_gcv_ext_train_r2"] = r2(ytr64, D_tr @ coef_ge)
        row["C_std_linear_gcv_ext_lambda"] = float(lam_ge)

        # D. rff rung GCV vs null, using the fitted rff/1.0 model's own phi (W, b, stats from the fit)
        phi_tr = m_rff._readout._phi(M_tr)  # noqa: SLF001
        phi_ev = m_rff._readout._phi(M_ev)  # noqa: SLF001
        feats_rff = np.concatenate([phi_tr, side_tr], axis=1)
        curve_rff_cap, null_rff = gcv_curve(feats_rff, ytr64, saved_grid)
        curve_rff_ext, _ = gcv_curve(feats_rff, ytr64, EXT_GRID)
        j_cap = int(np.argmin(curve_rff_cap))
        j_ext = int(np.argmin(curve_rff_ext))
        row["D_rff_gcv_capped_lambda"] = float(saved_grid[j_cap])
        row["D_rff_gcv_ext_lambda"] = float(EXT_GRID[j_ext])
        row["D_rff_gcv_ext_at_edge"] = bool(j_ext == len(EXT_GRID) - 1)
        row["D_rff_gcv_ext_min_over_null_minus_1"] = float(curve_rff_ext[j_ext] / null_rff - 1.0)
        coef_r, lam_r = ro._gcv_select(feats_rff, ytr64)  # noqa: SLF001
        row["D_rff_gcv_capped_eval_r2"] = r2(yev64, ro._assemble_design(phi_ev, side_ev) @ coef_r)  # noqa: SLF001
        row["D_rff_gcv_capped_lambda_library"] = float(lam_r)
        try:
            ro._GCV_GRID = EXT_GRID  # noqa: SLF001
            coef_re, lam_re = ro._gcv_select(feats_rff, ytr64)  # noqa: SLF001
        finally:
            ro._GCV_GRID = saved_grid  # noqa: SLF001
        row["D_rff_gcv_ext_eval_r2"] = r2(yev64, ro._assemble_design(phi_ev, side_ev) @ coef_re)  # noqa: SLF001
        row["D_rff_gcv_ext_train_r2"] = r2(ytr64, ro._assemble_design(phi_tr, side_tr) @ coef_re)  # noqa: SLF001
        row["D_rff_gcv_ext_lambda_library"] = float(lam_re)

        report["folds"].append(row)
        print(json.dumps(row), flush=True)

    keys = [k for k in report["folds"][0] if k.endswith("_eval_r2")]
    report["aggregates"] = {k: float(np.mean([f[k] for f in report["folds"]])) for k in keys}
    print("AGGREGATES", json.dumps(report["aggregates"], indent=2), flush=True)
    Path(args.out).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
