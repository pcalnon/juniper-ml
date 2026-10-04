#!/usr/bin/env python3
"""W0.9 companion -- conditioning of the linear-readout design on the E-H equities artifact.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use measurement script)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-04
Status:      ad-hoc; companion to 2026-10-04_recurrence_equities_cv_matrix.py. Its output is section 2
             evidence in the W5.1 note named in the plan
             notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md.

Why: the service-defaults replay (linear readout, ridge 0.0 -> min-norm ``lstsq``) returned fold-0
eval r2 -83,452 on 2026-10-03 and -93,606 on 2026-10-04 on BYTE-IDENTICAL arrays and the same model
code. A solve whose out-of-sample answer moves by 12 % while its inputs do not is ill-conditioned.
This script measures that directly, per expanding fold, for the design the ``LinearReadout`` actually
solves -- ``[ memory block (F*d = 240 cols) | target_dt | 1 ]`` -- on the raw artifact and on its
``normalize_features: true`` sibling: singular-value spectrum, 2-norm condition number, numerical rank,
and the eval-row projection onto the train design's weakest right-singular directions (how far the
eval memory states leave the training-fold support along the directions the min-norm solution
amplifies most).

Run: /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py \
        --data-url http://127.0.0.1:8110 --out-dir reports/<dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module  # noqa: E402

_matrix = import_module("2026-10-04_recurrence_equities_cv_matrix")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-url", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    from juniper_model_core.crossval import walk_forward_folds
    from juniper_recurrence._readout import build_lmu_regressor

    report: dict = {}
    for normalize in (False, True):
        params = dict(_matrix.E_H_DATASET_PARAMS)
        if normalize:
            params["normalize_features"] = True
        dataset_id, seq, arrays, _meta = _matrix._load_full(args.data_url, params)
        folds = walk_forward_folds(int(seq.X.shape[0]), n_folds=5, scheme="expanding", embargo=2)
        aux_all = seq.fit_kwargs()
        rows = []
        for i, fold in enumerate(folds):
            tr, ev = fold.train_idx, fold.eval_idx
            aux_tr = {k: v[tr] for k, v in aux_all.items()}
            aux_ev = {k: v[ev] for k, v in aux_all.items()}
            model = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=0.0, default_ridge=0.0)
            model.fit(seq.X[tr], seq.y[tr], **aux_tr)
            M_tr = model._memory_block(seq.X[tr], aux_tr.get("dt"), None, aux_tr.get("seq_lengths"))  # noqa: SLF001
            M_ev = model._memory_block(seq.X[ev], aux_ev.get("dt"), None, aux_ev.get("seq_lengths"))  # noqa: SLF001
            side_tr = model._side_channel(aux_tr.get("target_dt"), len(tr))  # noqa: SLF001
            side_ev = model._side_channel(aux_ev.get("target_dt"), len(ev))  # noqa: SLF001
            D_tr = np.concatenate([M_tr, side_tr, np.ones((len(tr), 1))], axis=1)
            D_ev = np.concatenate([M_ev, side_ev, np.ones((len(ev), 1))], axis=1)
            s = np.linalg.svd(D_tr, compute_uv=False)
            _u, s_full, vt = np.linalg.svd(D_tr, full_matrices=False)
            eps_rank = s.max() * max(D_tr.shape) * np.finfo(float).eps
            rank = int(np.sum(s > eps_rank))
            # Eval rows projected onto the train design's weakest 10 right-singular directions, scaled by
            # 1/s (what the min-norm solution does to them), relative to the same quantity on train rows.
            weak = vt[-10:]
            amp_tr = np.abs(D_tr @ weak.T) / s_full[-10:]
            amp_ev = np.abs(D_ev @ weak.T) / s_full[-10:]
            coef = model._readout.coef  # noqa: SLF001
            rows.append(
                {
                    "fold": i,
                    "n_train": int(len(tr)),
                    "design_cols": int(D_tr.shape[1]),
                    "sigma_max": float(s.max()),
                    "sigma_min": float(s.min()),
                    "cond_2norm": float(s.max() / s.min()) if s.min() > 0 else float("inf"),
                    "numerical_rank_eps": rank,
                    "n_singular_values_below_1e-8_rel": int(np.sum(s / s.max() < 1e-8)),
                    "n_singular_values_below_1e-6_rel": int(np.sum(s / s.max() < 1e-6)),
                    "coef_2norm": float(np.linalg.norm(coef)) if coef is not None else None,
                    "weak_dir_amp_train_p99": float(np.percentile(amp_tr, 99)),
                    "weak_dir_amp_eval_p99": float(np.percentile(amp_ev, 99)),
                    "weak_dir_amp_eval_max": float(amp_ev.max()),
                    "singular_values_log10_deciles": [float(x) for x in np.percentile(np.log10(s), [0, 10, 25, 50, 75, 90, 100])],
                }
            )
            print(f"normalize={'on' if normalize else 'off'} fold {i}: n={len(tr)} cols={D_tr.shape[1]} cond={rows[-1]['cond_2norm']:.3g} rank={rank} |coef|={rows[-1]['coef_2norm']:.3g} weak-dir amp p99 train {rows[-1]['weak_dir_amp_train_p99']:.3g} eval {rows[-1]['weak_dir_amp_eval_p99']:.3g} (eval max {rows[-1]['weak_dir_amp_eval_max']:.3g})", flush=True)
        report[f"normalize={normalize}"] = {"dataset_id": dataset_id, "folds": rows}
    (out_dir / "23-linear-conditioning.json").write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
