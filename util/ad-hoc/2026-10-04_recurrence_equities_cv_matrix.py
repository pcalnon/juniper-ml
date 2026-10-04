#!/usr/bin/env python3
"""W0.8 / W0.9 -- recurrence x equities cross-validation replay and controlled matrix.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use measurement script)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-04
Status:      ad-hoc; the measurement it produces is written up as section 1 and section 2 of the
             W5.1 cause-investigation note named in the plan
             notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
             (work items W0.8 and W0.9).

Two modes against a live per-run stack (``util/experiment_stack.bash --up --recurrence``):

``replay``  -- W0.8. Create the E-H dataset on the run's juniper-data (so the cold yfinance/SEC fetch
               happens OUTSIDE the recurrence request and cannot trip the service's 30 s data-client
               default, F-S9), then POST ``/v1/crossval`` twice on the resolved ``dataset_id``:
               once with the request body the E-H suite actually sends (RFF readout, ridge 1.0,
               256 features, median gamma, d 16, data-driven theta) and once with NO model parameters
               (the service defaults the audit measured: linear readout, ridge 0.0). Both responses
               are saved verbatim.

``matrix``  -- W0.9. Fetch the same artifact (and its ``normalize_features: true`` sibling) through
               juniper-data-client, derive the ``full`` view exactly as the service does
               (``sequence_data_from_arrays(arrays, "full")`` -> ``derive_full_split``), cut the same
               walk-forward folds (model-core ``walk_forward_folds``), and fit one fresh model per
               fold per cell of {readout linear/rff} x {ridge 0.0/1.0/gcv} x {normalize off/on} x
               {theta fold-resolved/configured}. Per fold it records what the HTTP route cannot
               return: the resolved theta, the resolved RFF gamma, the selected ridge, the fold's
               median ``sum(dt)``, the eval memory-state z-range against the train fold's column
               statistics, raw-feature drift, and prediction vs target ranges.

The in-process fit path is the service's own: ``juniper_recurrence._readout.build_lmu_regressor``
builds the model, ``LMURegressor.fit`` / ``predict`` with ``SequenceData.fit_kwargs()`` slices mirror
``juniper_model_core.crossval.cross_validate`` (``pass_eval_as_val=False``). The replay/matrix
agreement on the E-H cell is checked and reported.

Run with the recurrence env's interpreter, e.g.
    /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py \
        replay --data-url http://127.0.0.1:8110 --recurrence-url http://127.0.0.1:8260 --out-dir reports/<dir>
    /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py \
        matrix --data-url http://127.0.0.1:8110 --out-dir reports/<dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

# The E-H suite's dataset selector (util/experiments/suites/p4/e-h-recurrence-real-data.yaml) and the
# model block it inherits from juniper-recurrence/conf/experiments/irregular-sine-rff.yaml. ``theta`` is
# null in the YAML; run_experiment._lmu_hyperparams omits None values, so the body carries no theta.
E_H_DATASET_PARAMS: dict[str, Any] = {
    "symbols": ["AAPL"],
    "start_date": "2015-01-01",
    "end_date": "2022-01-01",
    "lookback": 64,
    "regression_target": "log_return",
    "seed": 20260807,
}
E_H_MODEL: dict[str, Any] = {"d": 16, "ridge": 1.0, "readout": "rff", "rff_features": 256, "rff_gamma": "median"}
E_H_CV: dict[str, Any] = {"n_folds": 5, "scheme": "expanding", "embargo": 2}
EXPECTED_DATASET_ID = "equities_seq-6.0.0-15505731cba5b86d"  # the frozen id the audit measured


# ----------------------------------------------------------------------------------------------- HTTP
def http_json(method: str, url: str, body: dict | None = None, timeout: float = 900.0) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - loopback stack
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(payload)
        except ValueError:
            return exc.code, payload


def create_dataset(data_url: str, params: dict[str, Any]) -> dict[str, Any]:
    code, payload = http_json("POST", f"{data_url}/v1/datasets", {"generator": "equities_seq", "params": params, "persist": True}, timeout=900.0)
    if code not in (200, 201) or not isinstance(payload, dict) or not payload.get("dataset_id"):
        raise SystemExit(f"POST /v1/datasets -> HTTP {code}: {payload}")
    return payload


def fold_table(payload: dict[str, Any]) -> str:
    rows = ["| fold | train r2 | train rmse | eval r2 | eval rmse | eval mae |", "| --- | --- | --- | --- | --- | --- |"]
    for fold in payload.get("folds", []):
        tr, ev = fold["train_metrics"], fold["eval_metrics"]
        rows.append(f"| {fold['fold']} | {tr['r2']:+.4f} | {tr['rmse']:.5f} | {ev['r2']:+.1f} | {ev['rmse']:.5f} | {ev['mae']:.5f} |")
    agg, std = payload.get("eval_aggregate", {}), payload.get("eval_std", {})
    rows.append(f"| **aggregate** | | | **{agg.get('r2', float('nan')):+.1f}** (std {std.get('r2', float('nan')):.1f}) | {agg.get('rmse', float('nan')):.5f} | {agg.get('mae', float('nan')):.5f} |")
    return "\n".join(rows)


def cmd_replay(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    created = create_dataset(args.data_url, E_H_DATASET_PARAMS)
    dataset_id = created["dataset_id"]
    print(f"dataset_id = {dataset_id}  (create took {time.perf_counter() - t0:.1f}s; expected {EXPECTED_DATASET_ID}: {'MATCH' if dataset_id == EXPECTED_DATASET_ID else 'DIFFERENT'})")
    (out_dir / "00-dataset-create.json").write_text(json.dumps(created, indent=2, default=str))

    code, health = http_json("GET", f"{args.recurrence_url}/v1/health")
    (out_dir / "01-recurrence-health.json").write_text(json.dumps({"status": code, "body": health}, indent=2, default=str))

    results = {}
    for label, model_kw in (("eh-rff", E_H_MODEL), ("service-defaults", {})):
        body = {"dataset": {"dataset_id": dataset_id}, **E_H_CV, **model_kw}
        t1 = time.perf_counter()
        code, payload = http_json("POST", f"{args.recurrence_url}/v1/crossval", body)
        wall = time.perf_counter() - t1
        record = {"label": label, "request": body, "http_status": code, "wall_seconds": round(wall, 3), "response": payload}
        (out_dir / f"10-crossval-{label}.json").write_text(json.dumps(record, indent=2, default=str))
        results[label] = record
        print(f"\n=== {label}: POST /v1/crossval -> HTTP {code} in {wall:.1f}s ===")
        print(json.dumps(body))
        if code == 200 and isinstance(payload, dict):
            print(f"task_type={payload.get('task_type')} n_folds={payload.get('n_folds')} dataset.n_windows={payload.get('dataset', {}).get('n_windows')} split={payload.get('dataset', {}).get('split')}")
            print(fold_table(payload))
        else:
            print(payload)
    return 0


# -------------------------------------------------------------------------------------------- MATRIX
def _load_full(data_url: str, params: dict[str, Any]):
    from juniper_data_client import JuniperDataClient, validate_npz_contract
    from juniper_recurrence_model import sequence_data_from_arrays

    client = JuniperDataClient(base_url=data_url, timeout=900)
    try:
        created = client.create_dataset(generator="equities_seq", params=params, persist=True)
        dataset_id = created["dataset_id"]
        arrays = client.download_artifact_npz(dataset_id)
    finally:
        client.close()
    validate_npz_contract(arrays)
    seq = sequence_data_from_arrays(arrays, "full")
    meta = created.get("meta") if isinstance(created, dict) else None
    return dataset_id, seq, arrays, meta


def _stats(a: np.ndarray) -> dict[str, float]:
    a = np.asarray(a, dtype=float).ravel()
    return {"min": float(a.min()), "max": float(a.max()), "mean": float(a.mean()), "std": float(a.std())}


def _z_against(ref: np.ndarray, probe: np.ndarray) -> dict[str, float]:
    """Column-standardise ``probe`` by ``ref``'s mean/std (zero-variance guard) and summarise |z|."""
    mean = ref.mean(axis=0)
    std = ref.std(axis=0)
    std = np.where(std > 0.0, std, 1.0)
    z = np.abs((probe - mean) / std)
    return {
        "max_abs_z": float(z.max()),
        "p99_abs_z": float(np.percentile(z, 99)),
        "frac_rows_any_gt5": float(np.mean(np.any(z > 5.0, axis=1))),
        "frac_rows_any_gt10": float(np.mean(np.any(z > 10.0, axis=1))),
    }


def run_cell(seq, folds, make_model, label: str) -> dict[str, Any]:
    from juniper_recurrence_model.model import _regression_metrics

    aux_all = seq.fit_kwargs()
    per_fold: list[dict[str, Any]] = []
    for fold_index, fold in enumerate(folds):
        tr, ev = fold.train_idx, fold.eval_idx
        aux_tr = {k: v[tr] for k, v in aux_all.items()}
        aux_ev = {k: v[ev] for k, v in aux_all.items()}
        Xtr, ytr, Xev, yev = seq.X[tr], seq.y[tr], seq.X[ev], seq.y[ev]
        model = make_model()
        t0 = time.perf_counter()
        model.fit(Xtr, ytr, **aux_tr)
        fit_s = time.perf_counter() - t0
        pred_tr = model.predict(Xtr, **aux_tr)
        pred_ev = model.predict(Xev, **aux_ev)
        m_tr = _regression_metrics(ytr, pred_tr)
        m_ev = _regression_metrics(yev, pred_ev)
        # diagnostics the route cannot return
        M_tr = model._memory_block(Xtr, aux_tr.get("dt"), None, aux_tr.get("seq_lengths"))  # noqa: SLF001 - diagnostic
        M_ev = model._memory_block(Xev, aux_ev.get("dt"), None, aux_ev.get("seq_lengths"))  # noqa: SLF001
        readout = model._readout  # noqa: SLF001
        per_fold.append(
            {
                "fold": int(fold_index),
                "n_train": int(len(tr)),
                "n_eval": int(len(ev)),
                "fit_seconds": round(fit_s, 3),
                "theta_resolved": float(model.theta),
                "sum_dt_median_train": float(np.median(np.sum(aux_tr["dt"], axis=1))),
                "sum_dt_median_eval": float(np.median(np.sum(aux_ev["dt"], axis=1))),
                "readout_kind": readout.kind,
                "ridge_resolved": readout.ridge if isinstance(readout.ridge, str) else float(readout.ridge),
                "gamma_resolved": (float(readout.gamma) if readout.kind == "rff" else None),
                "train_metrics": m_tr,
                "eval_metrics": m_ev,
                "memory_z_eval_vs_train": _z_against(M_tr, M_ev),
                "memory_z_train_self": _z_against(M_tr, M_tr),
                "raw_last_step_z_eval_vs_train": _z_against(Xtr[:, -1, :], Xev[:, -1, :]),
                "pred_train": _stats(pred_tr),
                "target_train": _stats(ytr),
                "pred_eval": _stats(pred_ev),
                "target_eval": _stats(yev),
            }
        )
    evals = [f["eval_metrics"] for f in per_fold]
    agg = {k: float(np.mean([e[k] for e in evals])) for k in evals[0]}
    std = {k: float(np.std([e[k] for e in evals])) for k in evals[0]}
    return {"label": label, "folds": per_fold, "eval_aggregate": agg, "eval_std": std}


def cmd_matrix(args: argparse.Namespace) -> int:
    from juniper_model_core.crossval import walk_forward_folds
    from juniper_recurrence._readout import build_lmu_regressor

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells: list[dict[str, Any]] = []
    datasets: dict[str, Any] = {}
    for normalize in (False, True):
        params = dict(E_H_DATASET_PARAMS)
        if normalize:
            params["normalize_features"] = True
        t0 = time.perf_counter()
        dataset_id, seq, arrays, meta = _load_full(args.data_url, params)
        n = int(seq.X.shape[0])
        folds = walk_forward_folds(n, n_folds=E_H_CV["n_folds"], scheme=E_H_CV["scheme"], embargo=E_H_CV["embargo"])
        theta_cfg = float(np.median(np.sum(seq.dt, axis=1)))
        datasets[f"normalize={normalize}"] = {
            "dataset_id": dataset_id,
            "params": params,
            "n_windows_full": n,
            "n_train_partition": int(arrays["X_train"].shape[0]),
            "n_val_partition": int(arrays["X_val"].shape[0]),
            "n_test_partition": int(arrays["X_test"].shape[0]),
            "lookback": int(seq.X.shape[1]),
            "n_features": int(seq.X.shape[2]),
            "folds": [{"fold": i, "n_train": int(len(f.train_idx)), "n_eval": int(len(f.eval_idx)), "train_last_idx": int(f.train_idx[-1]), "eval_first_idx": int(f.eval_idx[0])} for i, f in enumerate(folds)],
            "theta_configured_full_median_sum_dt": theta_cfg,
            "sum_dt_full": _stats(np.sum(seq.dt, axis=1)),
            "target_full": _stats(seq.y),
            "X_last_step_full_per_feature_std": [float(s) for s in seq.X[:, -1, :].std(axis=0)],
            "X_last_step_full_per_feature_mean": [float(m) for m in seq.X[:, -1, :].mean(axis=0)],
            "load_seconds": round(time.perf_counter() - t0, 2),
            "meta": meta,
        }
        print(f"\n### normalize_features={normalize}: dataset_id={dataset_id} n_full={n} folds={[len(f.train_idx) for f in folds]} theta_cfg={theta_cfg:.2f}", flush=True)
        for readout in ("linear", "rff"):
            for ridge in (0.0, 1.0, "gcv"):
                for theta_label, theta in (("fold-resolved", None), ("configured", theta_cfg)):
                    label = f"readout={readout} ridge={ridge} normalize={'on' if normalize else 'off'} theta={theta_label}"
                    make_model = partial(
                        build_lmu_regressor,
                        d=16,
                        theta=theta,
                        readout=readout,
                        ridge=ridge,
                        rff_features=256 if readout == "rff" else None,
                        rff_gamma="median" if readout == "rff" else None,
                        default_ridge=0.0,
                    )
                    t1 = time.perf_counter()
                    try:
                        cell = run_cell(seq, folds, make_model, label)
                    except Exception as exc:  # record, never abort the matrix
                        cell = {"label": label, "error": f"{type(exc).__name__}: {exc}"}
                    cell.update({"readout": readout, "ridge": ridge, "normalize": normalize, "theta": theta_label, "dataset_id": dataset_id, "wall_seconds": round(time.perf_counter() - t1, 2)})
                    cells.append(cell)
                    if "error" in cell:
                        print(f"  {label}: ERROR {cell['error']}", flush=True)
                    else:
                        ev = [f["eval_metrics"]["r2"] for f in cell["folds"]]
                        tr = [f["train_metrics"]["r2"] for f in cell["folds"]]
                        print(f"  {label}: eval r2 agg {cell['eval_aggregate']['r2']:+.2f}  per-fold {[round(x, 2) for x in ev]}  train r2 {[round(x, 3) for x in tr]}  theta {[round(f['theta_resolved'], 1) for f in cell['folds']]}  ridge {[f['ridge_resolved'] for f in cell['folds']]}", flush=True)
    (out_dir / "20-matrix-datasets.json").write_text(json.dumps(datasets, indent=2, default=str))
    (out_dir / "21-matrix-cells.json").write_text(json.dumps(cells, indent=2, default=str))
    (out_dir / "22-matrix-table.md").write_text("# W0.9 matrix — eval r² per cell (one row per cell; all five folds)\n\n" + render_matrix(cells) + "\n")
    print("\n" + render_matrix(cells))
    return 0


def render_matrix(cells: list[dict[str, Any]]) -> str:
    rows = [
        "| readout | ridge | normalize | theta | eval r2 per fold (0..4) | eval r2 agg | eval rmse agg | train r2 per fold | theta resolved per fold | ridge/gamma resolved | eval memory max abs z per fold |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in cells:
        if "error" in c:
            rows.append(f"| {c['readout']} | {c['ridge']} | {'on' if c['normalize'] else 'off'} | {c['theta']} | ERROR | | | | | {c['error']} | |")
            continue
        folds = c["folds"]
        ev = " / ".join(f"{f['eval_metrics']['r2']:+.2f}" for f in folds)
        tr = " / ".join(f"{f['train_metrics']['r2']:+.3f}" for f in folds)
        th = " / ".join(f"{f['theta_resolved']:.1f}" for f in folds)
        rg = " / ".join((f"{f['ridge_resolved']:.3g}" if isinstance(f["ridge_resolved"], float) else str(f["ridge_resolved"])) + (f"/γ{f['gamma_resolved']:.3g}" if f["gamma_resolved"] is not None else "") for f in folds)
        mz = " / ".join(f"{f['memory_z_eval_vs_train']['max_abs_z']:.0f}" for f in folds)
        rows.append(f"| {c['readout']} | {c['ridge']} | {'on' if c['normalize'] else 'off'} | {c['theta']} | {ev} | {c['eval_aggregate']['r2']:+.2f} | {c['eval_aggregate']['rmse']:.4f} | {tr} | {th} | {rg} | {mz} |")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    replay = sub.add_parser("replay", help="W0.8: HTTP replay of the E-H crossval request and the service-defaults control")
    replay.add_argument("--data-url", required=True)
    replay.add_argument("--recurrence-url", required=True)
    replay.add_argument("--out-dir", required=True)
    replay.set_defaults(func=cmd_replay)
    matrix = sub.add_parser("matrix", help="W0.9: in-process controlled matrix with diagnostics")
    matrix.add_argument("--data-url", required=True)
    matrix.add_argument("--out-dir", required=True)
    matrix.set_defaults(func=cmd_matrix)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
