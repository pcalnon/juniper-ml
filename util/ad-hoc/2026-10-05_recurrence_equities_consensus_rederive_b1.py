#!/usr/bin/env python3
"""Reconciler re-derivation of Lane B1's lone measurements (consensus review of the W5.1 note).

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use measurement script)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc; written for notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md
             (procedure §5.2: a lone finding is a lead until the reconciler re-derives it).

Re-derives, with the model's own objects:

  F1  -- the two 2026-10-03 artifacts under one dataset_id: Scenario A's copy (the one the note byte-diffed)
         and Scenario B's data-store copy (the one that produced the audited -18,081). Checksums with
         juniper-data's algorithm (sorted keys, uncompressed np.savez into BytesIO, sha256), the keys and
         feature columns that differ, and the linear / ridge 0.0 solve on the Scenario-B arrays per fold
         (Lane B1: fold 0 -83,451.610 / aggregate -18,081.543 -- every audited digit).
  F5  -- rank of the fold-0 and fold-4 linear designs raw vs column-standardised, and which feature's
         memory columns are exactly constant (Lane B1: split_ratio, not cost_basis / total_shares).
  F7  -- which partition rows each fold's eval covers (Lane B1: fold 4 = 107 val + all 176 test rows).
  F9  -- rff / ridge 1.0 aggregate over RFF seeds 0..5 (Lane B1: -0.115 ... -0.252; seed 0 is the best).
  F2  -- linear / ridge 0.0 on same-pool shuffled splits of fold-4 size (drift removed), 3 draws
         (Lane B1: -0.04 ... -0.21 against the chronological -7,239).

Run:
    /opt/miniforge3/envs/JuniperCascor1/bin/python \
        util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive_b1.py \
        --out reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive-b1.json
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence._readout import build_lmu_regressor
from juniper_recurrence_model import readouts as ro
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model.model import _regression_metrics

AUDIT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/artifacts/recurrence-equities-audit")
NPZ_A = AUDIT / "scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz"
NPZ_B = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/scratch/data-store/equities_seq-6.0.0-15505731cba5b86d.npz")
META_A = AUDIT / "scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.meta.json"
META_B_HTTP = AUDIT / "40-seq-meta-http.txt"
AUDIT_SHADOW = AUDIT / "24-c-crossval-shadow.txt"
FEATS = ["open", "high", "low", "close", "volume", "week52_high", "week52_low", "total_shares", "market_cap", "cost_basis", "dividend", "split_ratio", "days_since_week52_high", "days_since_week52_low", "days_since_report"]


def load(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def checksum(arrays: dict[str, np.ndarray]) -> str:
    """juniper_data.core.artifacts.compute_checksum, re-stated: sorted keys, uncompressed savez, sha256."""
    buf = io.BytesIO()
    np.savez(buf, **{k: arrays[k] for k in sorted(arrays)})
    buf.seek(0)
    return hashlib.sha256(buf.read()).hexdigest()


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(_regression_metrics(np.asarray(y_true, float).reshape(-1, 1), np.asarray(y_pred, float).reshape(-1, 1))["r2"])


def linear_fit_eval(seq, aux_all, tr, ev, ridge=0.0):
    aux_tr = {k: v[tr] for k, v in aux_all.items()}
    aux_ev = {k: v[ev] for k, v in aux_all.items()}
    m = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=ridge, default_ridge=0.0)
    m.fit(seq.X[tr], seq.y[tr], **aux_tr)
    return r2(seq.y[tr], m.predict(seq.X[tr], **aux_tr)), r2(seq.y[ev], m.predict(seq.X[ev], **aux_ev)), m


def rff_fit_eval(seq, aux_all, tr, ev, seed):
    """rff / ridge 1.0 / 256 / median with an explicit RFF seed via the model's own random_seed."""
    from juniper_recurrence_model.model import LMURegressor

    aux_tr = {k: v[tr] for k, v in aux_all.items()}
    aux_ev = {k: v[ev] for k, v in aux_all.items()}
    base = build_lmu_regressor(d=16, theta=None, readout="rff", ridge=1.0, rff_features=256, rff_gamma="median", default_ridge=0.0)
    # the factory never passes random_seed (model default 0); re-use its spec with an explicit seed
    m = LMURegressor(d=16, theta=None, readout=base._readout_spec, random_seed=seed)  # noqa: SLF001
    m.fit(seq.X[tr], seq.y[tr], **aux_tr)
    return r2(seq.y[ev], m.predict(seq.X[ev], **aux_ev))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out: dict = {}

    # ---------------------------------------------------------------- F1: two artifacts under one id
    a, b = load(NPZ_A), load(NPZ_B)
    out["F1"] = {
        "npz_a": str(NPZ_A),
        "npz_b": str(NPZ_B),
        "checksum_a": checksum(a),
        "checksum_b": checksum(b),
        "meta_a_checksum": json.loads(META_A.read_text()).get("checksum") if META_A.exists() else None,
        "keys_equal": sorted(a) == sorted(b),
        "n_keys": len(a),
        "differing_keys": {},
    }
    for k in sorted(a):
        if a[k].shape != b[k].shape or a[k].dtype != b[k].dtype:
            out["F1"]["differing_keys"][k] = {"shape_a": list(a[k].shape), "shape_b": list(b[k].shape), "dtype_a": str(a[k].dtype), "dtype_b": str(b[k].dtype)}
            continue
        if not np.array_equal(a[k], b[k]):
            d = a[k] != b[k]
            entry = {"cells_differ": int(d.sum())}
            if a[k].ndim == 3:
                cols = np.flatnonzero(d.any(axis=(0, 1)))
                entry["columns"] = [f"{int(c)}:{FEATS[int(c)]}" for c in cols]
                entry["a_range_in_cols"] = [[float(np.nanmin(a[k][..., c])), float(np.nanmax(a[k][..., c]))] for c in cols]
                entry["b_range_in_cols"] = [[float(np.nanmin(b[k][..., c])), float(np.nanmax(b[k][..., c]))] for c in cols]
            out["F1"]["differing_keys"][k] = entry
    if META_B_HTTP.exists():
        txt = META_B_HTTP.read_text()
        i = txt.find('"checksum"')
        out["F1"]["meta_b_http_checksum_excerpt"] = txt[i : i + 90] if i >= 0 else None
    if AUDIT_SHADOW.exists():
        out["F1"]["audit_shadow_excerpt_r2"] = [line.strip() for line in AUDIT_SHADOW.read_text().splitlines() if '"r2"' in line][:12]

    seq_b = sequence_data_from_arrays(b, "full")
    aux_b = seq_b.fit_kwargs()
    n_b = int(seq_b.X.shape[0])
    folds_b = walk_forward_folds(n_b, n_folds=5, scheme="expanding", embargo=2)
    rows = []
    for i, f in enumerate(folds_b):
        tr_r2, ev_r2, _ = linear_fit_eval(seq_b, aux_b, f.train_idx, f.eval_idx)
        rows.append({"fold": i, "train_r2": tr_r2, "eval_r2": ev_r2})
    out["F1"]["linear_ridge0_on_B"] = {"folds": rows, "aggregate": float(np.mean([r["eval_r2"] for r in rows]))}
    print("F1", json.dumps({k: v for k, v in out["F1"].items() if k != "audit_shadow_excerpt_r2"}, indent=1), flush=True)

    # ---------------------------------------------------------------- shared: Scenario-A / 10-04 arrays
    seq = sequence_data_from_arrays(a, "full")
    aux_all = seq.fit_kwargs()
    n = int(seq.X.shape[0])
    folds = walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=2)

    # ---------------------------------------------------------------- F7: partition rows per eval fold
    n_tr, n_va, n_te = int(a["X_train"].shape[0]), int(a["X_val"].shape[0]), int(a["X_test"].shape[0])
    out["F7"] = {"n_train": n_tr, "n_val": n_va, "n_test": n_te, "n_full": n, "folds": []}
    for i, f in enumerate(folds):
        ev = np.asarray(f.eval_idx)
        out["F7"]["folds"].append({"fold": i, "eval_first": int(ev[0]), "eval_last": int(ev[-1]), "in_train": int(np.sum(ev < n_tr)), "in_val": int(np.sum((ev >= n_tr) & (ev < n_tr + n_va))), "in_test": int(np.sum(ev >= n_tr + n_va))})
    print("F7", json.dumps(out["F7"]), flush=True)

    # ---------------------------------------------------------------- F5: rank raw vs standardised, constant columns
    out["F5"] = {}
    for i in (0, 4):
        f = folds[i]
        tr = f.train_idx
        aux_tr = {k: v[tr] for k, v in aux_all.items()}
        m = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=0.0, default_ridge=0.0)
        m.fit(seq.X[tr], seq.y[tr], **aux_tr)
        M_tr = m._memory_block(np.asarray(seq.X[tr], dtype=float), aux_tr.get("dt"), None, aux_tr.get("seq_lengths"))  # noqa: SLF001
        side_tr = m._side_channel(aux_tr.get("target_dt"), len(tr))  # noqa: SLF001
        D = ro._assemble_design(M_tr, side_tr)  # noqa: SLF001
        s = np.linalg.svd(D, compute_uv=False)
        eps_rank = s.max() * max(D.shape) * np.finfo(float).eps
        mu, sd = ro._standardize_fit(M_tr)  # noqa: SLF001
        Dz = ro._assemble_design((M_tr - mu) / sd, side_tr)  # noqa: SLF001
        sz = np.linalg.svd(Dz, compute_uv=False)
        eps_rank_z = sz.max() * max(Dz.shape) * np.finfo(float).eps
        col_std = M_tr.std(axis=0)  # 240 memory columns, feature-major (15 x 16)
        const_cols = np.flatnonzero(col_std == 0.0)
        const_feats = sorted({f"{int(c) // 16}:{FEATS[int(c) // 16]}" for c in const_cols})
        per_feat_std = {FEATS[j]: [float(col_std[j * 16 : (j + 1) * 16].min()), float(col_std[j * 16 : (j + 1) * 16].max())] for j in range(15)}
        out["F5"][f"fold{i}"] = {"n_train": int(len(tr)), "raw_sigma_max": float(s.max()), "raw_rank_eps": int(np.sum(s > eps_rank)), "std_sigma_max": float(sz.max()), "std_rank_eps": int(np.sum(sz > eps_rank_z)), "n_constant_memory_columns": int(const_cols.size), "constant_features": const_feats, "per_feature_memory_col_std_min_max": per_feat_std}
    print("F5", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_feature_memory_col_std_min_max"} for k, v in out["F5"].items()}), flush=True)
    print("F5 per-feature memory col std (fold0)", json.dumps(out["F5"]["fold0"]["per_feature_memory_col_std_min_max"]), flush=True)

    # ---------------------------------------------------------------- F9: RFF seed sweep (rff / 1.0 / raw)
    out["F9"] = {"seeds": []}
    for seed in range(6):
        r2s = [rff_fit_eval(seq, aux_all, f.train_idx, f.eval_idx, seed) for f in folds]
        out["F9"]["seeds"].append({"seed": seed, "folds": r2s, "aggregate": float(np.mean(r2s))})
        print("F9 seed", seed, [round(x, 4) for x in r2s], round(float(np.mean(r2s)), 4), flush=True)
    aggs = [s["aggregate"] for s in out["F9"]["seeds"]]
    out["F9"]["aggregate_min_max_mean_std"] = [float(min(aggs)), float(max(aggs)), float(np.mean(aggs)), float(np.std(aggs))]
    out["F9"]["seed0_is_best"] = bool(max(aggs) == aggs[0])

    # ---------------------------------------------------------------- F2: shuffled same-pool split, fold-4 sizes
    f4 = folds[4]
    chrono_tr, chrono_ev, _ = linear_fit_eval(seq, aux_all, f4.train_idx, f4.eval_idx)
    pool = np.concatenate([np.asarray(f4.train_idx), np.asarray(f4.eval_idx)])
    rng = np.random.default_rng(0)
    shuffled = []
    for _draw in range(3):
        p = rng.permutation(pool)
        rtr, rev = np.sort(p[: len(f4.train_idx)]), np.sort(p[len(f4.train_idx) :])
        shuffled.append(linear_fit_eval(seq, aux_all, rtr, rev)[1])
    out["F2"] = {"fold4_chronological_eval_r2": chrono_ev, "fold4_chronological_train_r2": chrono_tr, "fold4_shuffled_eval_r2_3_draws": shuffled}
    print("F2", json.dumps(out["F2"]), flush=True)

    Path(args.out).write_text(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
