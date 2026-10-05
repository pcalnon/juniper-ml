#!/usr/bin/env python3
"""Reconciler re-derivation for round 2 (Lane B1-r2 F2 / F4 / F5 / F9) of the W5.1 note's consensus review.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use measurement script)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc; written for notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md
             (procedure §5.2). Puts an ARTIFACT behind every number v1.1.0 of the note quoted from a lane's
             appendix only, and adds the embargoed in-era control Lane B1-r2 asked for.

  F10  train + val only (1,522 windows), embargo 2: rff/1.0 (seed 0), rff/gcv, linear/0.0.
  F11  embargo 64 (>= lookback): the same three cells on the full view and on train + val only.
  F12  the RFF rung (1.0 and gcv) on the same three shuffled fold-4-size draws F2 used (no embargo; leaky).
  F13  mint B (Scenario B's data-store copy): rff/1.0 and rff/gcv; rff/gcv per RFF seed 0..2 on mint A.
  F14  linear/0.0 fold 0 and fold 4: three row-order permutations of the train rows; a float32 round-trip
       of the design.
  F15  block-held-out IN-ERA control with a 64-window embargo on BOTH sides: eval = rows 849..1131 (fold 2's
       eval block, inside fold 4's training era), train = rows [0, 785) U [1196, 1413); both rungs, every
       ridge. Removes drift without the window overlap the shuffled control carries.
  F16  the constant-feature question: per-feature raw std over all steps and windows (is `cost_basis`
       constant? is `total_shares`?), from the arrays, not the memory block.

Run:
    /opt/miniforge3/envs/JuniperCascor1/bin/python \
        util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive_b1r2.py \
        --out reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive-b1r2.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence._readout import build_lmu_regressor
from juniper_recurrence_model import readouts as ro
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model.model import LMURegressor, _regression_metrics

AUDIT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/artifacts/recurrence-equities-audit")
NPZ_A = AUDIT / "scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz"
NPZ_B = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/scratch/data-store/equities_seq-6.0.0-15505731cba5b86d.npz")
FEATS = ["open", "high", "low", "close", "volume", "week52_high", "week52_low", "total_shares", "market_cap", "cost_basis", "dividend", "split_ratio", "days_since_week52_high", "days_since_week52_low", "days_since_report"]


def load(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def r2(y_true, y_pred) -> float:
    return float(_regression_metrics(np.asarray(y_true, float).reshape(-1, 1), np.asarray(y_pred, float).reshape(-1, 1))["r2"])


def fit_eval(seq, aux_all, tr, ev, *, readout: str, ridge, seed: int = 0) -> tuple[float, float]:
    """Fit through the service's factory (so the spec is the route's) and return (train r², eval r²)."""
    aux_tr = {k: v[tr] for k, v in aux_all.items()}
    aux_ev = {k: v[ev] for k, v in aux_all.items()}
    if readout == "rff":
        base = build_lmu_regressor(d=16, theta=None, readout="rff", ridge=ridge, rff_features=256, rff_gamma="median", default_ridge=0.0)
        m = LMURegressor(d=16, theta=None, readout=base._readout_spec, random_seed=seed)  # noqa: SLF001
    else:
        m = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=ridge, default_ridge=0.0)
    m.fit(seq.X[tr], seq.y[tr], **aux_tr)
    return r2(seq.y[tr], m.predict(seq.X[tr], **aux_tr)), r2(seq.y[ev], m.predict(seq.X[ev], **aux_ev))


def three_cells(seq, aux_all, folds, label: str) -> dict:
    out = {}
    for name, kw in (("rff_1.0", dict(readout="rff", ridge=1.0)), ("rff_gcv", dict(readout="rff", ridge="gcv")), ("linear_0.0", dict(readout="linear", ridge=0.0))):
        evs = [fit_eval(seq, aux_all, f.train_idx, f.eval_idx, **kw)[1] for f in folds]
        out[name] = {"folds": evs, "aggregate": float(np.mean(evs)), "cv_r2_std": float(np.std(evs))}
        print(label, name, [round(x, 4) if abs(x) < 100 else round(x) for x in evs], round(float(np.mean(evs)), 4), flush=True)
    out["fold_sizes"] = [[int(len(f.train_idx)), int(len(f.eval_idx))] for f in folds]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out: dict = {}

    a = load(NPZ_A)
    seq = sequence_data_from_arrays(a, "full")
    aux_all = seq.fit_kwargs()
    n = int(seq.X.shape[0])
    n_tv = int(a["X_train"].shape[0] + a["X_val"].shape[0])
    folds2 = walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=2)

    # F10 — train + val only, embargo 2 (the view W5.2 will govern, single entity)
    out["F10_trainval_embargo2"] = three_cells(seq, aux_all, walk_forward_folds(n_tv, n_folds=5, scheme="expanding", embargo=2), "F10")
    out["F10_trainval_embargo2"]["n_windows"] = n_tv

    # F11 — embargo 64, full and train + val
    out["F11_full_embargo64"] = three_cells(seq, aux_all, walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=64), "F11-full")
    out["F11_trainval_embargo64"] = three_cells(seq, aux_all, walk_forward_folds(n_tv, n_folds=5, scheme="expanding", embargo=64), "F11-tv")

    # F12 — RFF rung on the SAME three shuffled fold-4 draws F2 used (default_rng(0), three permutations)
    f4 = folds2[4]
    pool = np.concatenate([np.asarray(f4.train_idx), np.asarray(f4.eval_idx)])
    rng = np.random.default_rng(0)
    draws = []
    for _ in range(3):
        p = rng.permutation(pool)
        draws.append((np.sort(p[: len(f4.train_idx)]), np.sort(p[len(f4.train_idx) :])))
    out["F12_shuffled_fold4_rff"] = {
        "linear_0.0": [fit_eval(seq, aux_all, tr, ev, readout="linear", ridge=0.0)[1] for tr, ev in draws],
        "rff_1.0": [fit_eval(seq, aux_all, tr, ev, readout="rff", ridge=1.0)[1] for tr, ev in draws],
        "rff_gcv": [fit_eval(seq, aux_all, tr, ev, readout="rff", ridge="gcv")[1] for tr, ev in draws],
        "note": "no embargo: adjacent windows share 61 of 64 days, so this control removes drift AND adds near-duplicate rows (Lane B1-r2 F4); see F15 for the embargoed in-era control",
    }
    print("F12", json.dumps(out["F12_shuffled_fold4_rff"]), flush=True)

    # F13 — mint B (Scenario B's copy): rff/1.0 and rff/gcv; rff/gcv per seed on mint A
    b = load(NPZ_B)
    seq_b = sequence_data_from_arrays(b, "full")
    aux_b = seq_b.fit_kwargs()
    folds_b = walk_forward_folds(int(seq_b.X.shape[0]), n_folds=5, scheme="expanding", embargo=2)
    out["F13_mintB"] = {}
    for name, kw in (("rff_1.0", dict(readout="rff", ridge=1.0)), ("rff_gcv", dict(readout="rff", ridge="gcv"))):
        evs = [fit_eval(seq_b, aux_b, f.train_idx, f.eval_idx, **kw)[1] for f in folds_b]
        out["F13_mintB"][name] = {"folds": evs, "aggregate": float(np.mean(evs))}
    out["F13_rff_gcv_per_seed_mintA"] = {}
    for seed in range(3):
        evs = [fit_eval(seq, aux_all, f.train_idx, f.eval_idx, readout="rff", ridge="gcv", seed=seed)[1] for f in folds2]
        out["F13_rff_gcv_per_seed_mintA"][str(seed)] = {"folds": evs, "aggregate": float(np.mean(evs))}
    print("F13", json.dumps(out["F13_mintB"]), json.dumps(out["F13_rff_gcv_per_seed_mintA"]), flush=True)

    # F14 — row-order permutations and a float32 round-trip of the design (linear/0.0, folds 0 and 4)
    out["F14_rounding_probes"] = {}
    for i in (0, 4):
        f = folds2[i]
        tr, ev = np.asarray(f.train_idx), np.asarray(f.eval_idx)
        base_ev = fit_eval(seq, aux_all, tr, ev, readout="linear", ridge=0.0)[1]
        perms = []
        for s in range(3):
            p = np.random.default_rng(s).permutation(len(tr))
            perms.append(fit_eval(seq, aux_all, tr[p], ev, readout="linear", ridge=0.0)[1])
        # float32 round-trip of the exact design the solve sees
        aux_tr = {k: v[tr] for k, v in aux_all.items()}
        aux_ev = {k: v[ev] for k, v in aux_all.items()}
        m = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=0.0, default_ridge=0.0)
        m.fit(seq.X[tr], seq.y[tr], **aux_tr)
        M_tr = m._memory_block(np.asarray(seq.X[tr], float), aux_tr.get("dt"), None, aux_tr.get("seq_lengths"))  # noqa: SLF001
        M_ev = m._memory_block(np.asarray(seq.X[ev], float), aux_ev.get("dt"), None, aux_ev.get("seq_lengths"))  # noqa: SLF001
        D_tr = ro._assemble_design(M_tr, m._side_channel(aux_tr.get("target_dt"), len(tr)))  # noqa: SLF001
        D_ev = ro._assemble_design(M_ev, m._side_channel(aux_ev.get("target_dt"), len(ev)))  # noqa: SLF001
        y_tr = np.asarray(seq.y[tr], float).reshape(len(tr), -1)
        coef32, *_ = np.linalg.lstsq(D_tr.astype(np.float32).astype(np.float64), y_tr, rcond=None)
        f32 = r2(seq.y[ev], D_ev @ coef32)
        out["F14_rounding_probes"][f"fold{i}"] = {"baseline_eval_r2": base_ev, "row_permutation_eval_r2": perms, "row_permutation_max_rel_move": float(max(abs(x - base_ev) for x in perms) / abs(base_ev)), "float32_roundtrip_eval_r2": f32, "float32_rel_move": float(abs(f32 - base_ev) / abs(base_ev))}
    print("F14", json.dumps(out["F14_rounding_probes"]), flush=True)

    # F15 — block-held-out IN-ERA control with a 64-window embargo on both sides (inside fold 4's train era)
    ev_blk = np.arange(849, 1132)
    tr_blk = np.concatenate([np.arange(0, 849 - 64), np.arange(1132 + 64, 1413)])
    out["F15_inera_block_embargo64"] = {"eval_rows": [849, 1131], "train_rows": [[0, 784], [1196, 1412]], "n_train": int(len(tr_blk)), "n_eval": int(len(ev_blk))}
    for name, kw in (("linear_0.0", dict(readout="linear", ridge=0.0)), ("linear_1.0", dict(readout="linear", ridge=1.0)), ("linear_gcv", dict(readout="linear", ridge="gcv")), ("rff_1.0", dict(readout="rff", ridge=1.0)), ("rff_gcv", dict(readout="rff", ridge="gcv"))):
        tr_r2, ev_r2 = fit_eval(seq, aux_all, tr_blk, ev_blk, **kw)
        out["F15_inera_block_embargo64"][name] = {"train_r2": tr_r2, "eval_r2": ev_r2}
    # the chronological fold whose eval block this is (fold 2) for comparison
    out["F15_inera_block_embargo64"]["chronological_fold2_eval_r2"] = {name: fit_eval(seq, aux_all, folds2[2].train_idx, folds2[2].eval_idx, **kw)[1] for name, kw in (("linear_0.0", dict(readout="linear", ridge=0.0)), ("rff_1.0", dict(readout="rff", ridge=1.0)))}
    print("F15", json.dumps(out["F15_inera_block_embargo64"]), flush=True)

    # F16 — constant features in the RAW arrays (all steps, all windows, full view)
    X_full = np.concatenate([a["X_train"], a["X_val"], a["X_test"]], axis=0).astype(np.float64)
    flat = X_full.reshape(-1, X_full.shape[2])
    out["F16_raw_feature_stats"] = {FEATS[j]: {"min": float(flat[:, j].min()), "max": float(flat[:, j].max()), "std": float(flat[:, j].std()), "cv": float(flat[:, j].std() / abs(flat[:, j].mean())) if flat[:, j].mean() != 0 else None} for j in range(15)}
    print("F16", json.dumps({k: {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in out["F16_raw_feature_stats"].items() if k in ("cost_basis", "total_shares", "split_ratio", "dividend")}), flush=True)

    Path(args.out).write_text(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
