#!/usr/bin/env python3
"""Lane A3 consensus review -- numpy-only checks on the E-H equities NPZ, and a digit-level comparison.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use consensus-review script)
Author:      Paul Calnon
Version:     0.3.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc; Lane A3 of the independent-agent consensus review of
             notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md.

Two subcommands:

``checks``   Reads one NPZ (and optionally the audit's archived copy) with numpy alone -- no
             juniper_data_client, no juniper_recurrence_model, no model-core -- and recomputes the
             dataset-level facts the note states in section 0.1 / 1.1 / 2.1 / 2.3 so that they are
             checked by an instrument that shares no code with the one that produced them:
               * key count and per-key shape / dtype;
               * n_windows per partition and the ``full`` view size, rebuilt here as
                 concat(train, val, test) followed by a STABLE argsort on ``ticker_code`` (the
                 documented entity-major rule), plus whether that order is the identity;
               * the expanding walk-forward cut exactly as stated: fold_size = n // (n_folds + 1),
                 train rows [0, fold_size*(i+1) - embargo), eval rows [fold_size*(i+1),
                 fold_size*(i+2)), n_folds=5, embargo=2;
               * sum(dt) per window: min / max / mean / std over the full view and its median per
                 train fold and per eval fold;
               * the regression target (``y_reg``) mean / std overall and per fold;
               * last-step feature column stds and means (float64 and float32 reductions);
               * optional: a key-by-key comparison against a second NPZ (np.array_equal AND
                 tobytes() equality, sha256 per array and per file) and the ``checksum`` /
                 ``created_at`` of both meta JSON files.

``fold-threads``  Re-fits the service-defaults cell (linear, ridge 0.0) from an NPZ under whatever
             OMP/OPENBLAS/MKL thread env the caller sets, recording every metric at full precision and
             the threadpool in force. USES the model instruments (labelled); a bitwise comparison across
             thread settings tests section 2.4's "BLAS reduction order, thread count" mechanism.

``compare``  Reads the replay / matrix / conditioning / datasets JSON written by the two
             2026-10-04 instruments into MY run dir and into the predecessor's evidence dir and
             reports, number by number, whether the value reproduces EXACTLY (bitwise float
             equality), to N significant digits, only in class (same sign, within 10x), or not at
             all. Writes a JSON and a markdown table. Reads the predecessor's files; never writes
             there.

Run (any interpreter with numpy):
    python util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py checks \
        --npz <run-dir>/data/equities_seq-6.0.0-15505731cba5b86d.npz \
        --meta <run-dir>/data/equities_seq-6.0.0-15505731cba5b86d.meta.json \
        --archive-npz <audit-archive>/data/equities_seq-6.0.0-15505731cba5b86d.npz \
        --archive-meta <audit-archive>/data/equities_seq-6.0.0-15505731cba5b86d.meta.json \
        --out reports/<lane-dir>/30-numpy-checks.json
    python util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py compare \
        --mine reports/<lane-dir> --ref reports/2026-10-04_recurrence-equities-cv-matrix \
        --out-json reports/<lane-dir>/40-compare.json --out-md reports/<lane-dir>/41-compare.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

SPLITS = ("train", "val", "test")


# ================================================================================================ checks
def _stats(a: np.ndarray) -> dict[str, float]:
    a = np.asarray(a, dtype=float).ravel()
    return {"min": float(a.min()), "max": float(a.max()), "mean": float(a.mean()), "std": float(a.std()), "median": float(np.median(a)), "n": int(a.size)}


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def full_view(arrays: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """concat(train, val, test) per base key, then stable-argsort by ticker_code (entity-major)."""
    bases = sorted({k[: -len("_train")] for k in arrays if k.endswith("_train")})
    composable = [b for b in bases if all(f"{b}_{s}" in arrays for s in SPLITS)]
    out: dict[str, np.ndarray] = {}
    for b in composable:
        out[b] = np.concatenate([np.asarray(arrays[f"{b}_{s}"]) for s in SPLITS], axis=0)
    info: dict[str, Any] = {"composable_bases": composable, "ticker_code_present": "ticker_code" in out}
    if "ticker_code" in out:
        tc = out["ticker_code"].reshape(-1)
        order = np.argsort(tc, kind="stable")
        info["order_is_identity"] = bool(np.array_equal(order, np.arange(tc.shape[0])))
        info["n_unique_ticker_codes"] = int(np.unique(tc).size)
        out = {k: v[order] for k, v in out.items()}
    return out, info


def fold_cuts(n: int, n_folds: int = 5, embargo: int = 2) -> list[dict[str, Any]]:
    fold_size = n // (n_folds + 1)
    folds = []
    for i in range(n_folds):
        eval_start = (i + 1) * fold_size
        eval_stop = (i + 2) * fold_size
        train_end = eval_start - embargo
        folds.append({"fold": i, "train_start": 0, "train_end_excl": train_end, "eval_start": eval_start, "eval_stop_excl": eval_stop, "n_train": train_end, "n_eval": eval_stop - eval_start})
    return folds


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def compare_arrays(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> dict[str, Any]:
    keys_a, keys_b = set(a), set(b)
    rows = {}
    for k in sorted(keys_a | keys_b):
        if k not in a or k not in b:
            rows[k] = {"present_in_both": False, "in_a": k in a, "in_b": k in b}
            continue
        xa, xb = a[k], b[k]
        rows[k] = {
            "present_in_both": True,
            "shape_a": list(xa.shape),
            "shape_b": list(xb.shape),
            "dtype_a": str(xa.dtype),
            "dtype_b": str(xb.dtype),
            "array_equal": bool(xa.shape == xb.shape and xa.dtype == xb.dtype and np.array_equal(xa, xb)),
            "tobytes_equal": bool(xa.tobytes() == xb.tobytes()),
            "sha256_a": sha256_bytes(xa.tobytes()),
            "sha256_b": sha256_bytes(xb.tobytes()),
        }
    return {
        "n_keys_a": len(keys_a),
        "n_keys_b": len(keys_b),
        "keys_only_a": sorted(keys_a - keys_b),
        "keys_only_b": sorted(keys_b - keys_a),
        "n_array_equal": sum(1 for r in rows.values() if r.get("array_equal")),
        "n_tobytes_equal": sum(1 for r in rows.values() if r.get("tobytes_equal")),
        "all_identical": all(r.get("array_equal") and r.get("tobytes_equal") for r in rows.values()) and keys_a == keys_b,
        "per_key": rows,
    }


def meta_fields(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    m = json.loads(path.read_text())
    keep = ("dataset_id", "generator", "generator_version", "checksum", "created_at", "last_accessed_at", "access_count", "n_samples", "n_features", "n_train", "n_val", "n_test", "task_type", "n_classes", "lookback")
    return {k: m.get(k) for k in keep}


def cmd_checks(args: argparse.Namespace) -> int:
    report: dict[str, Any] = {"npz": str(args.npz), "npz_sha256_file": sha256_bytes(args.npz.read_bytes()), "npz_size_bytes": args.npz.stat().st_size}
    arrays = load_npz(args.npz)
    report["n_keys"] = len(arrays)
    report["keys"] = {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in sorted(arrays.items())}
    report["partitions"] = {s: int(arrays[f"X_{s}"].shape[0]) for s in SPLITS if f"X_{s}" in arrays}
    report["partition_sum"] = int(sum(report["partitions"].values()))
    report["has_full_family_in_file"] = any(k.endswith("_full") for k in arrays)

    full, info = full_view(arrays)
    report["full_view"] = info
    X = full["X"]
    n, lookback, n_feat = X.shape
    report["full_view"].update({"n_windows": int(n), "lookback": int(lookback), "n_features": int(n_feat), "X_dtype": str(X.dtype), "X_all_finite": bool(np.all(np.isfinite(X)))})

    dt = np.asarray(full["dt"], dtype=float)
    sum_dt = dt.sum(axis=1)
    report["sum_dt_full"] = _stats(sum_dt)
    report["dt_first_col_all_zero"] = bool(np.all(dt[:, 0] == 0))
    report["dt_any_negative"] = bool(np.any(dt < 0))

    y_key = "y_reg" if "y_reg" in full else "y"
    y = np.asarray(full[y_key], dtype=float).reshape(n, -1)
    report["target_key"] = y_key
    report["target_full"] = _stats(y)
    report["target_all_finite"] = bool(np.all(np.isfinite(y)))

    folds = fold_cuts(n, args.n_folds, args.embargo)
    report["fold_cut_rule"] = f"fold_size = n // (n_folds+1) = {n // (args.n_folds + 1)}; train rows [0, fold_size*(i+1) - {args.embargo}); eval rows [fold_size*(i+1), fold_size*(i+2)); i in 0..{args.n_folds - 1}"
    for f in folds:
        tr = slice(f["train_start"], f["train_end_excl"])
        ev = slice(f["eval_start"], f["eval_stop_excl"])
        f["sum_dt_median_train"] = float(np.median(sum_dt[tr]))
        f["sum_dt_median_eval"] = float(np.median(sum_dt[ev]))
        f["target_train"] = _stats(y[tr])
        f["target_eval"] = _stats(y[ev])
        if "window_end_date" in full:
            wed = full["window_end_date"].reshape(-1)
            f["train_last_window_end_date"] = str(wed[tr][-1])
            f["eval_first_window_end_date"] = str(wed[ev][0])
            f["eval_last_window_end_date"] = str(wed[ev][-1])
    report["folds"] = folds

    last64 = X[:, -1, :].astype(np.float64)
    stds = last64.std(axis=0)
    means = last64.mean(axis=0)
    stds32 = X[:, -1, :].astype(np.float32).std(axis=0)  # the matrix instrument reduces in the array's own float32
    report["X_last_step_full_per_feature_std_float64"] = [float(s) for s in stds]
    report["X_last_step_full_per_feature_std_float32"] = [float(s) for s in stds32]
    report["X_last_step_full_per_feature_mean_float64"] = [float(m) for m in means]
    report["X_last_step_std_min"] = float(stds.min())
    report["X_last_step_std_min_nonzero"] = float(stds[stds > 0].min()) if np.any(stds > 0) else None
    report["X_last_step_std_max"] = float(stds.max())
    report["X_last_step_std_argmin"] = int(stds.argmin())
    report["X_last_step_std_argmax"] = int(stds.argmax())
    report["X_last_step_n_zero_std_columns"] = int(np.sum(stds == 0.0))
    report["X_last_step_zero_std_columns_value"] = [float(last64[0, j]) for j in range(n_feat) if stds[j] == 0.0]
    report["X_all_steps_n_zero_std_columns"] = int(np.sum(X.reshape(-1, n_feat).astype(np.float64).std(axis=0) == 0.0))

    if "window_end_date" in full:
        wed = full["window_end_date"].reshape(-1)
        report["window_end_date_monotone_nondecreasing"] = bool(np.all(wed[1:] >= wed[:-1]))
        report["window_end_date_first"] = str(wed[0])
        report["window_end_date_last"] = str(wed[-1])

    report["meta"] = meta_fields(args.meta)

    if args.archive_npz is not None:
        if args.archive_npz.exists():
            arch = load_npz(args.archive_npz)
            report["archive"] = {
                "npz": str(args.archive_npz),
                "npz_sha256_file": sha256_bytes(args.archive_npz.read_bytes()),
                "npz_size_bytes": args.archive_npz.stat().st_size,
                "npz_file_bytes_identical": bool(args.archive_npz.read_bytes() == args.npz.read_bytes()),
                "comparison": compare_arrays(arrays, arch),
                "meta": meta_fields(args.archive_meta),
            }
        else:
            report["archive"] = {"npz": str(args.archive_npz), "status": "NO ARTIFACT"}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str))

    print(f"npz: {args.npz}  keys={report['n_keys']}  file sha256={report['npz_sha256_file'][:16]}…  size={report['npz_size_bytes']}")
    print(f"partitions: {report['partitions']}  sum={report['partition_sum']}  full view n={n} lookback={lookback} features={n_feat} dtype={X.dtype}  order_is_identity={info.get('order_is_identity')}")
    s = report["sum_dt_full"]
    print(f"sum(dt) full: min={s['min']:.1f} max={s['max']:.1f} mean={s['mean']:.3f} std={s['std']:.3f} median={s['median']:.1f}")
    t = report["target_full"]
    print(f"target ({y_key}) full: mean={t['mean']:.5f} std={t['std']:.5f} min={t['min']:.4f} max={t['max']:.4f}")
    print(report["fold_cut_rule"])
    for f in folds:
        print(f"  fold {f['fold']}: train [{f['train_start']},{f['train_end_excl']}) n={f['n_train']}  eval [{f['eval_start']},{f['eval_stop_excl']}) n={f['n_eval']}  median sum(dt) train={f['sum_dt_median_train']:.1f} eval={f['sum_dt_median_eval']:.1f}  target eval mean={f['target_eval']['mean']:.5f} std={f['target_eval']['std']:.5f}  train std={f['target_train']['std']:.5f}")
    print(f"last-step feature std (float64): min={stds.min():.3e} (col {stds.argmin()}) min-nonzero={report['X_last_step_std_min_nonzero']:.3e} max={stds.max():.3e} (col {stds.argmax()}) zero-std cols={int(np.sum(stds == 0.0))} value={report['X_last_step_zero_std_columns_value']}")
    print("  per-column std float64: " + ", ".join(f"{v:.3e}" for v in stds))
    print("  per-column std float32: " + ", ".join(f"{v:.3e}" for v in stds32))
    if report.get("meta"):
        print(f"meta: checksum={report['meta']['checksum']} created_at={report['meta']['created_at']} n_train/val/test={report['meta']['n_train']}/{report['meta']['n_val']}/{report['meta']['n_test']}")
    if "archive" in report:
        a = report["archive"]
        if a.get("status") == "NO ARTIFACT":
            print("archive: NO ARTIFACT")
        else:
            c = a["comparison"]
            print(f"archive: {a['npz']}  keys={c['n_keys_b']} (today {c['n_keys_a']})  array_equal={c['n_array_equal']}/{len(c['per_key'])}  tobytes_equal={c['n_tobytes_equal']}/{len(c['per_key'])}  all_identical={c['all_identical']}  only_a={c['keys_only_a']} only_b={c['keys_only_b']}")
            print(f"archive file sha256={a['npz_sha256_file'][:16]}… size={a['npz_size_bytes']}  file-bytes identical to today's: {a['npz_file_bytes_identical']}")
            if a.get("meta"):
                print(f"archive meta: checksum={a['meta']['checksum']} created_at={a['meta']['created_at']}")
    print(f"written: {args.out}")
    return 0


# ================================================================================================ compare
def _cmp(a: Any, b: Any) -> dict[str, Any]:
    """Classify how well scalar ``a`` (mine) reproduces ``b`` (reference)."""
    if a is None or b is None:
        return {"mine": a, "ref": b, "class": "MISSING"}
    if isinstance(a, str) or isinstance(b, str):
        return {"mine": a, "ref": b, "class": "EXACT" if a == b else "DIFFERENT"}
    a, b = float(a), float(b)
    if a == b:
        return {"mine": a, "ref": b, "class": "EXACT", "rel": 0.0, "sig_digits": None}
    denom = max(abs(a), abs(b))
    rel = abs(a - b) / denom if denom > 0 else 0.0
    sig = int(math.floor(-math.log10(rel))) if rel > 0 else None
    same_sign = (a < 0) == (b < 0)
    within_10x = same_sign and a != 0 and b != 0 and abs(math.log10(abs(a) / abs(b))) < 1.0
    if sig is not None and sig >= 3:
        cls = f"DIGITS({sig})"
    elif within_10x:
        cls = "CLASS"
    else:
        cls = "NO"
    return {"mine": a, "ref": b, "class": cls, "rel": rel, "sig_digits": sig}


def _load(path: Path) -> Any:
    return json.loads(path.read_text()) if path.exists() else None


def _cell_key(c: dict[str, Any]) -> str:
    return f"{c['readout']}|{c['ridge']}|{'on' if c['normalize'] else 'off'}|{c['theta']}"


def cmd_compare(args: argparse.Namespace) -> int:
    mine, ref = Path(args.mine), Path(args.ref)
    out: dict[str, Any] = {"mine_dir": str(mine), "ref_dir": str(ref), "replay": {}, "matrix": {}, "conditioning": {}, "datasets": {}}
    md: list[str] = ["# Lane A3 — digit-level comparison: my fresh run vs the 2026-10-04 evidence", "", f"- mine: `{mine}`", f"- ref: `{ref}`", "", "Classes: EXACT = bitwise-equal floats; DIGITS(k) = agree to k significant digits (k ≥ 3); CLASS = same sign and within 10×; NO = neither; MISSING = absent on one side.", ""]

    # ---- replay ------------------------------------------------------------------------------
    md += ["## Replay (HTTP `POST /v1/crossval`)", "", "| label | fold | metric | mine | ref | class | rel |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for label in ("eh-rff", "service-defaults"):
        m, r = _load(mine / f"10-crossval-{label}.json"), _load(ref / f"10-crossval-{label}.json")
        if m is None or r is None:
            out["replay"][label] = {"status": "MISSING", "mine": m is not None, "ref": r is not None}
            md.append(f"| {label} | - | - | {'present' if m else 'MISSING'} | {'present' if r else 'MISSING'} | MISSING | |")
            continue
        rec: dict[str, Any] = {"http_status": _cmp(m.get("http_status"), r.get("http_status")), "request_equal": m.get("request") == r.get("request"), "dataset_id": _cmp(m["request"]["dataset"]["dataset_id"], r["request"]["dataset"]["dataset_id"]), "wall_seconds": {"mine": m.get("wall_seconds"), "ref": r.get("wall_seconds")}, "folds": []}
        mr, rr = m["response"], r["response"]
        for fm, fr in zip(mr.get("folds", []), rr.get("folds", [])):
            row = {"fold": fm.get("fold"), "n_train": _cmp(fm.get("n_train"), fr.get("n_train"))}
            for side in ("train_metrics", "eval_metrics"):
                for k in ("r2", "rmse", "mae", "mse"):
                    row[f"{side}.{k}"] = _cmp(fm[side].get(k), fr[side].get(k))
                    if k in ("r2", "rmse"):
                        c = row[f"{side}.{k}"]
                        md.append(f"| {label} | {fm.get('fold')} | {side}.{k} | {c['mine']!r} | {c['ref']!r} | {c['class']} | {c.get('rel', '')} |")
            rec["folds"].append(row)
        for k in ("r2", "rmse", "mae"):
            rec[f"eval_aggregate.{k}"] = _cmp(mr["eval_aggregate"].get(k), rr["eval_aggregate"].get(k))
            rec[f"eval_std.{k}"] = _cmp(mr["eval_std"].get(k), rr["eval_std"].get(k))
            c = rec[f"eval_aggregate.{k}"]
            md.append(f"| {label} | agg | eval_aggregate.{k} | {c['mine']!r} | {c['ref']!r} | {c['class']} | {c.get('rel', '')} |")
            c = rec[f"eval_std.{k}"]
            md.append(f"| {label} | agg | eval_std.{k} | {c['mine']!r} | {c['ref']!r} | {c['class']} | {c.get('rel', '')} |")
        out["replay"][label] = rec
    md.append("")

    # ---- matrix ------------------------------------------------------------------------------
    mc, rc = _load(mine / "21-matrix-cells.json"), _load(ref / "21-matrix-cells.json")
    md += ["## Matrix (24 cells, in-process)", ""]
    if mc is None or rc is None:
        out["matrix"] = {"status": "MISSING", "mine": mc is not None, "ref": rc is not None}
        md.append(f"matrix: mine {'present' if mc else 'MISSING'}, ref {'present' if rc else 'MISSING'}")
    else:
        mref = {_cell_key(c): c for c in rc}
        rows = []
        md += ["| cell (readout/ridge/normalize/theta) | agg r² mine | agg r² ref | agg class | per-fold eval r² class (0..4) | worst fold rel | train r² class | θ class | γ class | ridge-resolved mine / ref | mem-z class |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        gcv_mine_at_ceiling = 0
        gcv_ref_at_ceiling = 0
        gcv_folds = 0
        for c in mc:
            key = _cell_key(c)
            r = mref.get(key)
            if r is None or "error" in c or "error" in r:
                rows.append({"cell": key, "status": "MISSING_OR_ERROR", "mine_error": c.get("error"), "ref_error": (r or {}).get("error")})
                md.append(f"| {key} | {c.get('error', '?')} | {(r or {}).get('error', 'MISSING')} | MISSING | | | | | | | |")
                continue
            agg = _cmp(c["eval_aggregate"]["r2"], r["eval_aggregate"]["r2"])
            folds = []
            worst = 0.0
            for fm, fr in zip(c["folds"], r["folds"]):
                fo = {
                    "fold": fm["fold"],
                    "eval_r2": _cmp(fm["eval_metrics"]["r2"], fr["eval_metrics"]["r2"]),
                    "eval_rmse": _cmp(fm["eval_metrics"]["rmse"], fr["eval_metrics"]["rmse"]),
                    "train_r2": _cmp(fm["train_metrics"]["r2"], fr["train_metrics"]["r2"]),
                    "theta": _cmp(fm["theta_resolved"], fr["theta_resolved"]),
                    "gamma": _cmp(fm["gamma_resolved"], fr["gamma_resolved"]),
                    "ridge_resolved": _cmp(fm["ridge_resolved"], fr["ridge_resolved"]),
                    "sum_dt_median_train": _cmp(fm["sum_dt_median_train"], fr["sum_dt_median_train"]),
                    "memory_max_abs_z": _cmp(fm["memory_z_eval_vs_train"]["max_abs_z"], fr["memory_z_eval_vs_train"]["max_abs_z"]),
                    "pred_eval_std": _cmp(fm["pred_eval"]["std"], fr["pred_eval"]["std"]),
                    "pred_eval_max_abs": _cmp(max(abs(fm["pred_eval"]["min"]), abs(fm["pred_eval"]["max"])), max(abs(fr["pred_eval"]["min"]), abs(fr["pred_eval"]["max"]))),
                }
                worst = max(worst, fo["eval_r2"].get("rel", 0.0) or 0.0)
                folds.append(fo)
                if c["ridge"] == "gcv":
                    gcv_folds += 1
                    gcv_mine_at_ceiling += int(float(fm["ridge_resolved"]) == 1000.0)
                    gcv_ref_at_ceiling += int(float(fr["ridge_resolved"]) == 1000.0)
            rows.append({"cell": key, "readout": c["readout"], "ridge": c["ridge"], "normalize": c["normalize"], "theta": c["theta"], "agg_r2": agg, "agg_rmse": _cmp(c["eval_aggregate"]["rmse"], r["eval_aggregate"]["rmse"]), "worst_fold_eval_r2_rel": worst, "folds": folds, "wall_seconds": {"mine": c.get("wall_seconds"), "ref": r.get("wall_seconds")}})
            fcls = " / ".join(f["eval_r2"]["class"] for f in folds)
            tcls = " / ".join(f["train_r2"]["class"] for f in folds)
            thcls = " / ".join(f["theta"]["class"] for f in folds)
            gcls = " / ".join(f["gamma"]["class"] for f in folds)
            rg = " / ".join(f"{f['ridge_resolved']['mine']}" for f in folds) + " vs " + " / ".join(f"{f['ridge_resolved']['ref']}" for f in folds)
            mz = " / ".join(f["memory_max_abs_z"]["class"] for f in folds)
            md.append(f"| {key} | {agg['mine']:+.6g} | {agg['ref']:+.6g} | {agg['class']} | {fcls} | {worst:.2e} | {tcls} | {thcls} | {gcls} | {rg} | {mz} |")
        out["matrix"] = {"n_cells_mine": len(mc), "n_cells_ref": len(rc), "gcv_folds": gcv_folds, "gcv_mine_at_ceiling_1000": gcv_mine_at_ceiling, "gcv_ref_at_ceiling_1000": gcv_ref_at_ceiling, "cells": rows}
        md.append("")
        md.append(f"GCV folds at the grid ceiling (λ = 1000.0): mine {gcv_mine_at_ceiling}/{gcv_folds}, ref {gcv_ref_at_ceiling}/{gcv_folds}.")
        # prediction of §2.4: ridge-0 digits move, RFF ridge-1 digits stable
        by_ridge: dict[str, list[float]] = {}
        for row in rows:
            if "agg_r2" in row:
                by_ridge.setdefault(f"{row['readout']}/{row['ridge']}", []).append(row["agg_r2"].get("rel", 0.0) or 0.0)
        out["matrix"]["agg_r2_rel_by_readout_ridge"] = {k: {"n": len(v), "max_rel": max(v), "all_exact": all(x == 0.0 for x in v)} for k, v in by_ridge.items()}
        md.append("")
        md.append("Aggregate eval r² relative difference by readout/ridge (the §2.4 prediction: ridge 0 moves, RFF ridge 1 stable):")
        for k, v in out["matrix"]["agg_r2_rel_by_readout_ridge"].items():
            md.append(f"- {k}: n={v['n']} max rel={v['max_rel']:.3e} all_exact={v['all_exact']}")
    md.append("")

    # ---- conditioning --------------------------------------------------------------------------
    mcnd, rcnd = _load(mine / "23-linear-conditioning.json"), _load(ref / "23-linear-conditioning.json")
    md += ["## Linear-design conditioning (per fold)", ""]
    if mcnd is None or rcnd is None:
        out["conditioning"] = {"status": "MISSING", "mine": mcnd is not None, "ref": rcnd is not None}
        md.append(f"conditioning: mine {'present' if mcnd else 'MISSING'}, ref {'present' if rcnd else 'MISSING'}")
    else:
        md += ["| artifact | fold | n_train | rank mine/ref | cond mine | cond ref | cond class | ‖coef‖ mine / ref (class) | amp p99 train mine/ref (class) | amp p99 eval mine/ref (class) |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for art in ("normalize=False", "normalize=True"):
            rows = []
            for fm, fr in zip(mcnd[art]["folds"], rcnd[art]["folds"]):
                row = {"fold": fm["fold"], "n_train": _cmp(fm["n_train"], fr["n_train"]), "design_cols": _cmp(fm["design_cols"], fr["design_cols"]), "numerical_rank_eps": _cmp(fm["numerical_rank_eps"], fr["numerical_rank_eps"]), "cond_2norm": _cmp(fm["cond_2norm"], fr["cond_2norm"]), "sigma_max": _cmp(fm["sigma_max"], fr["sigma_max"]), "sigma_min": _cmp(fm["sigma_min"], fr["sigma_min"]), "coef_2norm": _cmp(fm["coef_2norm"], fr["coef_2norm"]), "weak_dir_amp_train_p99": _cmp(fm["weak_dir_amp_train_p99"], fr["weak_dir_amp_train_p99"]), "weak_dir_amp_eval_p99": _cmp(fm["weak_dir_amp_eval_p99"], fr["weak_dir_amp_eval_p99"]), "weak_dir_amp_eval_max": _cmp(fm["weak_dir_amp_eval_max"], fr["weak_dir_amp_eval_max"]), "n_sv_below_1e-8_rel": _cmp(fm["n_singular_values_below_1e-8_rel"], fr["n_singular_values_below_1e-8_rel"])}
                rows.append(row)
                md.append(f"| {art} | {fm['fold']} | {fm['n_train']} | {fm['numerical_rank_eps']}/{fr['numerical_rank_eps']} | {fm['cond_2norm']:.3g} | {fr['cond_2norm']:.3g} | {row['cond_2norm']['class']} | {fm['coef_2norm']:.3g} / {fr['coef_2norm']:.3g} ({row['coef_2norm']['class']}) | {fm['weak_dir_amp_train_p99']:.3g} / {fr['weak_dir_amp_train_p99']:.3g} ({row['weak_dir_amp_train_p99']['class']}) | {fm['weak_dir_amp_eval_p99']:.3g} / {fr['weak_dir_amp_eval_p99']:.3g} ({row['weak_dir_amp_eval_p99']['class']}) |")
            out["conditioning"][art] = {"dataset_id": _cmp(mcnd[art]["dataset_id"], rcnd[art]["dataset_id"]), "folds": rows}
    md.append("")

    # ---- datasets --------------------------------------------------------------------------------
    mds, rds = _load(mine / "20-matrix-datasets.json"), _load(ref / "20-matrix-datasets.json")
    md += ["## Matrix datasets record", ""]
    if mds is None or rds is None:
        out["datasets"] = {"status": "MISSING", "mine": mds is not None, "ref": rds is not None}
        md.append(f"datasets: mine {'present' if mds else 'MISSING'}, ref {'present' if rds else 'MISSING'}")
    else:
        for art in ("normalize=False", "normalize=True"):
            a, b = mds[art], rds[art]
            rec = {"dataset_id": _cmp(a["dataset_id"], b["dataset_id"]), "n_windows_full": _cmp(a["n_windows_full"], b["n_windows_full"]), "partitions": [_cmp(a[k], b[k]) for k in ("n_train_partition", "n_val_partition", "n_test_partition")], "theta_cfg": _cmp(a["theta_configured_full_median_sum_dt"], b["theta_configured_full_median_sum_dt"]), "sum_dt_full": {k: _cmp(a["sum_dt_full"][k], b["sum_dt_full"][k]) for k in a["sum_dt_full"]}, "target_full": {k: _cmp(a["target_full"][k], b["target_full"][k]) for k in a["target_full"]}, "X_last_step_std_equal": a["X_last_step_full_per_feature_std"] == b["X_last_step_full_per_feature_std"], "X_last_step_std_mine": a["X_last_step_full_per_feature_std"], "X_last_step_std_ref": b["X_last_step_full_per_feature_std"], "meta_checksum": {"mine": (a.get("meta") or {}).get("checksum"), "ref": (b.get("meta") or {}).get("checksum")}, "meta_created_at": {"mine": (a.get("meta") or {}).get("created_at"), "ref": (b.get("meta") or {}).get("created_at")}, "folds_equal": a["folds"] == b["folds"]}
            out["datasets"][art] = rec
            md.append(f"- {art}: dataset_id {rec['dataset_id']['class']} ({a['dataset_id']}); n_full {a['n_windows_full']} vs {b['n_windows_full']} ({rec['n_windows_full']['class']}); folds equal {rec['folds_equal']}; theta_cfg {a['theta_configured_full_median_sum_dt']} vs {b['theta_configured_full_median_sum_dt']}; last-step std lists equal {rec['X_last_step_std_equal']}; meta checksum mine {rec['meta_checksum']['mine']} ref {rec['meta_checksum']['ref']}")
            md.append(f"  - last-step std mine: {', '.join(f'{v:.3e}' for v in a['X_last_step_full_per_feature_std'])}")
            md.append(f"  - last-step std ref:  {', '.join(f'{v:.3e}' for v in b['X_last_step_full_per_feature_std'])}")
    md.append("")

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(out, indent=2, default=str))
    Path(args.out_md).write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"written: {args.out_json}, {args.out_md}")
    return 0


# ================================================================================================ fold-threads
def cmd_fold_threads(args: argparse.Namespace) -> int:
    """Re-fit the service-defaults cell (linear readout, ridge 0.0, d 16, data-driven theta) on every
    expanding fold straight from an NPZ file, through the SAME objects the service and the matrix use,
    and record every metric at full precision together with the BLAS / thread configuration in force.
    The caller varies OMP_NUM_THREADS / OPENBLAS_NUM_THREADS / MKL_NUM_THREADS between invocations;
    comparing the outputs bitwise tests the note's section 2.4 claim that at cond ~1e32 the digits are
    decided by "BLAS reduction order, thread count". This subcommand USES the instruments (model code)
    and is labelled so; the ``checks`` subcommand does not.
    """
    import os
    import platform

    from juniper_model_core.crossval import walk_forward_folds
    from juniper_recurrence._readout import build_lmu_regressor
    from juniper_recurrence_model import sequence_data_from_arrays
    from juniper_recurrence_model.model import _regression_metrics

    arrays = load_npz(args.npz)
    seq = sequence_data_from_arrays(arrays, "full")
    n = int(seq.X.shape[0])
    folds = walk_forward_folds(n, n_folds=args.n_folds, scheme="expanding", embargo=args.embargo)
    aux_all = seq.fit_kwargs()
    threadpool: Any = None
    try:
        from threadpoolctl import threadpool_info

        threadpool = threadpool_info()
    except Exception as exc:  # threadpoolctl absent or failing is itself a fact worth recording
        threadpool = f"unavailable: {type(exc).__name__}: {exc}"
    env = {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    openblas_threads: Any = None
    try:
        import ctypes

        _blas = ctypes.CDLL(os.path.join(sys.prefix, "lib", "libblas.so.3"))
        openblas_threads = int(_blas.openblas_get_num_threads())
    except Exception as exc:
        openblas_threads = f"unavailable: {type(exc).__name__}: {exc}"
    out: dict[str, Any] = {"npz": str(args.npz), "label": args.label, "env": env, "cpu_count": os.cpu_count(), "openblas_get_num_threads": openblas_threads, "platform": platform.platform(), "numpy": np.__version__, "threadpool_info": threadpool, "cell": "readout=linear ridge=0.0 d=16 theta=None default_ridge=0.0", "folds": []}
    print(f"[{args.label}] openblas_get_num_threads={openblas_threads} env={env}", flush=True)
    if args.via_matrix_data_url:
        # A/B isolation: the 2026-10-04 matrix module's own load path (juniper-data-client over HTTP,
        # validate_npz_contract, sequence_data_from_arrays) and its own run_cell with its exact kwargs,
        # in THIS process, next to the np.load path below. Same arrays -> any gap is the fit path.
        from functools import partial
        from importlib import import_module

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        _m = import_module("2026-10-04_recurrence_equities_cv_matrix")
        dataset_id, seq2, arrays2, _meta2 = _m._load_full(args.via_matrix_data_url, dict(_m.E_H_DATASET_PARAMS))
        folds2 = walk_forward_folds(int(seq2.X.shape[0]), n_folds=args.n_folds, scheme="expanding", embargo=args.embargo)
        same_arrays = sorted(arrays2) == sorted(arrays) and all(np.array_equal(np.asarray(arrays2[k]), np.asarray(arrays[k])) for k in arrays)
        variants = {
            "matrix-module-http-load+run_cell(matrix kwargs)": (seq2, partial(build_lmu_regressor, d=16, theta=None, readout="linear", ridge=0.0, rff_features=None, rff_gamma=None, default_ridge=0.0)),
            "npz-load+run_cell(matrix kwargs)": (seq, partial(build_lmu_regressor, d=16, theta=None, readout="linear", ridge=0.0, rff_features=None, rff_gamma=None, default_ridge=0.0)),
            "npz-load+run_cell(probe kwargs)": (seq, partial(build_lmu_regressor, d=16, theta=None, readout="linear", ridge=0.0, default_ridge=0.0)),
        }
        out["ab_isolation"] = {"dataset_id": dataset_id, "http_arrays_equal_npz_arrays": bool(same_arrays), "variants": {}}
        for name, (sq, mk) in variants.items():
            cell = _m.run_cell(sq, folds2 if sq is seq2 else folds, mk, name)
            r2s = [f["eval_metrics"]["r2"] for f in cell["folds"]]
            out["ab_isolation"]["variants"][name] = {"fold_eval_r2": r2s, "fold_train_r2": [f["train_metrics"]["r2"] for f in cell["folds"]], "agg_eval_r2": cell["eval_aggregate"]["r2"]}
            print(f"[{args.label}] A/B {name}: fold0 eval r2={r2s[0]!r} agg={cell['eval_aggregate']['r2']!r}", flush=True)
        print(f"[{args.label}] A/B http arrays == npz arrays: {same_arrays}", flush=True)
    for i, fold in enumerate(folds):
        tr, ev = fold.train_idx, fold.eval_idx
        aux_tr = {k: v[tr] for k, v in aux_all.items()}
        aux_ev = {k: v[ev] for k, v in aux_all.items()}
        model = build_lmu_regressor(d=16, theta=None, readout="linear", ridge=0.0, default_ridge=0.0)
        model.fit(seq.X[tr], seq.y[tr], **aux_tr)
        m_tr = _regression_metrics(seq.y[tr], model.predict(seq.X[tr], **aux_tr))
        m_ev = _regression_metrics(seq.y[ev], model.predict(seq.X[ev], **aux_ev))
        coef = model._readout.coef  # noqa: SLF001 - diagnostic read, same as the 2026-10-04 instruments
        out["folds"].append({"fold": i, "n_train": int(len(tr)), "theta_resolved": float(model.theta), "train_metrics": m_tr, "eval_metrics": m_ev, "coef_2norm": float(np.linalg.norm(coef)) if coef is not None else None, "coef_sha256": sha256_bytes(np.ascontiguousarray(coef).tobytes()) if coef is not None else None})
        print(f"[{args.label}] fold {i}: n_train={len(tr)} train r2={m_tr['r2']!r} eval r2={m_ev['r2']!r} eval rmse={m_ev['rmse']!r} coef sha256={out['folds'][-1]['coef_sha256'][:16]}…", flush=True)
    evals = [f["eval_metrics"]["r2"] for f in out["folds"]]
    out["eval_aggregate_r2"] = float(np.mean(evals))
    print(f"[{args.label}] aggregate eval r2={out['eval_aggregate_r2']!r}  env={env}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=str))
    print(f"written: {args.out}")
    return 0


# ================================================================================================ main
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("checks", help="numpy-only dataset checks (+ optional archive comparison)")
    c.add_argument("--npz", required=True, type=Path)
    c.add_argument("--meta", type=Path, default=None)
    c.add_argument("--archive-npz", type=Path, default=None)
    c.add_argument("--archive-meta", type=Path, default=None)
    c.add_argument("--n-folds", type=int, default=5)
    c.add_argument("--embargo", type=int, default=2)
    c.add_argument("--out", required=True, type=Path)
    c.set_defaults(func=cmd_checks)
    k = sub.add_parser("compare", help="digit-level comparison of my instrument outputs vs the reference evidence dir")
    k.add_argument("--mine", required=True)
    k.add_argument("--ref", required=True)
    k.add_argument("--out-json", required=True)
    k.add_argument("--out-md", required=True)
    k.set_defaults(func=cmd_compare)
    t = sub.add_parser("fold-threads", help="re-fit the service-defaults cell from an NPZ under the caller's thread env (USES the model instruments)")
    t.add_argument("--npz", required=True, type=Path)
    t.add_argument("--label", required=True)
    t.add_argument("--n-folds", type=int, default=5)
    t.add_argument("--embargo", type=int, default=2)
    t.add_argument("--out", required=True, type=Path)
    t.add_argument("--via-matrix-data-url", default=None, help="A/B isolation: also run the 2026-10-04 matrix module's own load path + run_cell in this process against this juniper-data URL")
    t.set_defaults(func=cmd_fold_threads)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
