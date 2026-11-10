#!/usr/bin/env python3
"""stats_summary.py -- the SS8.3 ``stats.json`` + ``summary.md`` renderers (Wave 2.6).

Project: juniper-ml
Sub-Project: cascor + recurrence CLI test/validation/experimentation program
Application: experiment driver statistics renderers (util/experiments/)
Author: Paul Calnon
License: MIT License

Builds the SS8.3 statistics summary for a single run -- ``artifacts/results/stats.json``
plus the human-readable ``artifacts/results/summary.md`` -- from data the driver already
holds: the assembled SS13.4 manifest dict, the collected ``/v1/metrics`` scalar block
(cascor), the driver's own ``metrics_series.csv`` rows (cascor -- the SOLE source for
candidate correlation and step-duration statistics; neither exists in
``/v1/metrics/history`` rows, SS6.3), and the train/crossval payloads (recurrence).

Honesty notes baked into the output:

* ``training_step_duration`` p50/p95 are computed over the PER-POLL MEAN step duration
  (delta-sum / delta-count between consecutive samples of the histogram's ``_sum`` /
  ``_count`` exposition) -- true per-step quantiles are not recoverable from a sum/count
  pair, and the stats say so rather than pretending otherwise.
* "best candidate correlation per round" groups the sampled correlation gauge by the
  concurrently-sampled ``current_hidden_units`` value -- a round boundary is a
  hidden-unit increment.
* Degraded-mode notes (SS8.3 provenance/health) surface metrics-sampling errors,
  collection errors, per-plot skips, and disabled eval metrics instead of hiding them.
* The regression target summary (W5.5, F-D8 of the equities end-to-end plan) is per split
  over the finite values of the artifact's ``y_reg_<split>`` arrays -- population std
  (ddof=0), and ``finite_fraction`` counts NaN / ±Inf against the split instead of dropping
  them silently. The driver reads the arrays from the dataset artifact (lazy numpy); when it
  cannot, the stats say why in a degraded-mode note rather than omitting the block.
* ``recurrence.theta.note`` names where θ came from: the YAML ``train.theta`` (``explicit``), the
  YAML ``service.default_theta`` (the service default an unset ``train.theta`` resolves to), or
  neither (data-driven). Before, a ``service.default_theta`` run was labelled data-driven.
* A cascor run's eval scalars (juniper-ml#2064) are cascor's FINAL evaluation (``eval_metrics.final``), labelled
  with the ``split`` and ``n_samples`` it scored and ``held_out`` -- true only on the ``test`` split. The
  in-loop values, which ``cascor.eval_scalars`` held unlabelled until then, are kept beside them in
  ``cascor.eval_scalars_in_loop``, labelled with their own split and n. A run with no final evaluation says
  why in ``absent`` and never falls back to the in-loop values. See :func:`cascor_eval_blocks`.

Stdlib only (loaded by ``run_experiment.py`` through the same sibling-module file-path
loader as the plot modules, but with no matplotlib/numpy dependency, so stats render on
any host the driver runs on). ``util/`` is not pre-commit-lint-gated;
``tests/test_run_experiment.py`` is the gate.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, Optional

#: ``/2`` since juniper-ml#2064 (2026-10-27), because ``cascor.eval_scalars`` CHANGED MEANING: under ``/1`` it held
#: the in-loop values, unlabelled; under ``/2`` it is the labelled final evaluation, and the in-loop values moved
#: to ``cascor.eval_scalars_in_loop``. Files written under ``/1`` are not rewritten, so compare eval scalars
#: across the boundary only after checking this (juniper-ml#2034: provenance, not convention).
STATS_SCHEMA = "juniper-experiment-stats/2"

#: juniper-ml#2064: the scalars of the final-evaluation block, in report order. ``accuracy`` is new in
#: juniper-cascor#731; a service without it reports none, so the key stays ``None`` with no ``undefined`` reason.
CASCOR_FINAL_EVAL_METRICS = ("accuracy", "f1", "precision", "recall", "roc_auc")
#: The in-loop scalars: the flat ``/v1/metrics`` fields the live block fills. The live block has no accuracy.
CASCOR_IN_LOOP_METRICS = ("f1", "precision", "recall", "roc_auc")
CASCOR_FINAL_EVAL_BASIS = "eval_metrics.final: the finished model, scored once after the last weight update on the split named here; held out only when that split is test (with no test split loaded, cascor scores validation, the in-loop split)"
CASCOR_IN_LOOP_BASIS = "in-loop: the live eval_metrics block, the last mid-training evaluation on the split named here; a progress signal, never held out"

#: W5.5 (F-D8): the canonical split order of the target summary; other splits follow, sorted.
TARGET_SPLIT_ORDER = ("train", "val", "test")
TARGET_SUMMARY_BASIS = "per split over the finite values of y_reg_<split>; std is the population std (ddof=0); finite_fraction = n_finite / n; NaN and ±Inf count toward n and are excluded from the moments"

CORRELATION_COLUMN = "juniper_cascor_candidate_correlation"
HIDDEN_COLUMN = "current_hidden_units"
STEP_SUM_COLUMN = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT_COLUMN = "juniper_cascor_training_step_duration_seconds_count"

#: ``recurrence.theta.note``: where the fit's θ came from (see :func:`theta_block`).
THETA_NOTE_EXPLICIT = "explicit"
THETA_NOTE_SERVICE_DEFAULT = "service default from service.default_theta; train.theta is unset"
THETA_NOTE_DATA_DRIVEN = "data-driven (resolved from per-window elapsed time)"


def _to_float(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def percentile(values: List[float], q: float) -> Optional[float]:
    """Linear-interpolation percentile (q in 0..100) over an unsorted sample list."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (q / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def _split_order(names: Iterable[str]) -> List[str]:
    known = list(names)
    return [name for name in TARGET_SPLIT_ORDER if name in known] + sorted(name for name in known if name not in TARGET_SPLIT_ORDER)


def regression_target_summary(targets_by_split: Mapping[str, Iterable[Any]]) -> Optional[Dict[str, Any]]:
    """W5.5 (F-D8): mean / std / min / max / finite fraction of a regression target, per split.

    ``targets_by_split`` maps a split name to its target values -- any iterable of numbers; the
    driver hands over each ``y_reg_<split>`` array of the dataset artifact flattened to one value
    per window. Per split: ``n`` counts every value, ``n_finite`` the finite ones, and the moments
    are over the finite ones only (population std, ddof=0), so NaN / ±Inf lower
    ``finite_fraction`` instead of poisoning the mean. A split with no finite values keeps its
    ``n`` and reports ``None`` moments; an empty split reports ``finite_fraction`` ``None`` (0/0 is
    not 0). Splits are ordered train / val / test, then the rest sorted. Returns ``None`` when
    there are no splits at all, so a caller can tell "no regression target" from "a target with
    no finite values". Stdlib only.
    """
    if not targets_by_split:
        return None
    splits: Dict[str, Any] = {}
    for split in _split_order(targets_by_split):
        n = 0
        finite: List[float] = []
        for raw in targets_by_split[split]:
            n += 1
            value = raw if isinstance(raw, float) else _to_float(raw)
            if value is not None and math.isfinite(value):
                finite.append(value)
        block: Dict[str, Any] = {"n": n, "n_finite": len(finite), "finite_fraction": (len(finite) / n) if n else None, "mean": None, "std": None, "min": None, "max": None}
        if finite:
            mean = math.fsum(finite) / len(finite)
            block.update(mean=mean, std=math.sqrt(math.fsum((value - mean) ** 2 for value in finite) / len(finite)), min=min(finite), max=max(finite))
        splits[split] = block
    return {"basis": TARGET_SUMMARY_BASIS, "splits": splits}


def correlation_per_round(series_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Best sampled candidate correlation per growth round (round = a ``current_hidden_units`` value)."""
    best: Dict[int, float] = {}
    for row in series_rows:
        value = _to_float(row.get(CORRELATION_COLUMN))
        hidden = _to_float(row.get(HIDDEN_COLUMN))
        if value is None or hidden is None:
            continue
        key = int(hidden)
        if key not in best or value > best[key]:
            best[key] = value
    rounds = [{"hidden_units": key, "best_correlation": best[key]} for key in sorted(best)]
    return {
        "per_round": rounds,
        "max": max(best.values()) if best else None,
        "samples": sum(1 for row in series_rows if _to_float(row.get(CORRELATION_COLUMN)) is not None),
    }


def step_duration_stats(series_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Per-poll mean step-duration stats from the sampled histogram ``_sum``/``_count`` pair.

    A (delta-sum / delta-count) sample exists only for polls where the count advanced;
    p50/p95 are over those per-poll means -- true per-step quantiles are NOT recoverable
    from a sum/count exposition, and the ``basis`` field says so.
    """
    per_poll_means: List[float] = []
    prev_sum: Optional[float] = None
    prev_count: Optional[float] = None
    last_sum: Optional[float] = None
    last_count: Optional[float] = None
    for row in series_rows:
        cur_sum = _to_float(row.get(STEP_SUM_COLUMN))
        cur_count = _to_float(row.get(STEP_COUNT_COLUMN))
        if cur_sum is None or cur_count is None:
            continue
        last_sum, last_count = cur_sum, cur_count
        if prev_sum is not None and prev_count is not None and cur_count > prev_count:
            per_poll_means.append((cur_sum - prev_sum) / (cur_count - prev_count))
        prev_sum, prev_count = cur_sum, cur_count
    overall_mean = (last_sum / last_count) if last_sum is not None and last_count else None
    return {
        "basis": "per-poll mean (delta-sum/delta-count); true per-step quantiles are not recoverable from a sum/count exposition",
        "total_steps": int(last_count) if last_count is not None else None,
        "overall_mean_seconds": overall_mean,
        "p50_seconds": percentile(per_poll_means, 50.0),
        "p95_seconds": percentile(per_poll_means, 95.0),
        "poll_samples": len(per_poll_means),
    }


def _dataset_block(manifest: Mapping[str, Any], target_summary: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    dataset = manifest.get("dataset") if isinstance(manifest.get("dataset"), Mapping) else {}
    meta = dataset.get("meta") if isinstance(dataset.get("meta"), Mapping) else {}
    if meta.get("sequence"):
        shapes: Dict[str, Any] = {
            "kind": "sequence",
            "n_windows": meta.get("n_samples"),
            "lookback": meta.get("lookback"),
            "n_features": meta.get("n_features"),
            "n_train": meta.get("n_train"),
            "n_test": meta.get("n_test"),
        }
    else:
        shapes = {
            "kind": "tabular",
            "n_train": meta.get("n_train"),
            "n_test": meta.get("n_test"),
            "n_features": meta.get("n_features"),
            "n_classes": meta.get("n_classes"),
        }
    return {
        "dataset_id": dataset.get("dataset_id"),
        "generator": dataset.get("generator"),
        "generator_version": dataset.get("version"),
        "split": dataset.get("split"),
        "params": dataset.get("params"),
        "task_type": meta.get("task_type"),
        "shapes": shapes,
        "class_distribution": meta.get("class_distribution"),
        # W5.5 (F-D8): the regression counterpart of class_distribution -- None when the artifact
        # carries no y_reg_* arrays (every classification generator) or the driver could not read
        # them (then provenance.degraded_notes says why).
        "target_summary": dict(target_summary) if isinstance(target_summary, Mapping) else None,
    }


def _degraded_notes(manifest: Mapping[str, Any], kind: str, metrics_final: Optional[Mapping[str, Any]], target_summary_error: Optional[str] = None) -> List[str]:
    notes: List[str] = []
    drive_loop = manifest.get("drive_loop") if isinstance(manifest.get("drive_loop"), Mapping) else {}
    sampling_errors = drive_loop.get("metrics_sampling_errors")
    if isinstance(sampling_errors, int) and sampling_errors > 0:
        notes.append(f"/metrics sampling degraded on {sampling_errors} poll(s) (G-3: is JUNIPER_CASCOR_METRICS_ENABLED=true?)")
    for err in manifest.get("collect_errors") or []:
        if isinstance(err, Mapping):
            notes.append(f"collect: {err.get('artifact')} failed ({err.get('error')})")
    driver = manifest.get("driver") if isinstance(manifest.get("driver"), Mapping) else {}
    plots = driver.get("plots") if isinstance(driver.get("plots"), Mapping) else {}
    for skip in plots.get("skipped") or []:
        if isinstance(skip, Mapping):
            notes.append(f"plot {skip.get('name')} skipped: {skip.get('reason')}")
    if kind == "cascor" and isinstance(metrics_final, Mapping):
        eval_block = metrics_final.get("eval_metrics")
        if isinstance(eval_block, Mapping) and eval_block.get("enabled") is False:
            notes.append("scalar eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)")
    g6 = manifest.get("g6_shape_check")
    if isinstance(g6, Mapping) and not g6.get("ok"):
        notes.append("G-6 shape check FAILED: loaded network input width does not match the requested dataset")
    if target_summary_error:
        notes.append(f"regression target summary unavailable: {target_summary_error}")
    return notes


def theta_block(train_config: Optional[Mapping[str, Any]], service_config: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Where the fit's θ came from, for ``stats["recurrence"]["theta"]``.

    juniper-recurrence resolves an omitted ``theta`` as ``settings.default_theta`` when that is set,
    and data-drivenly only when it is not (``routers/training.py``: ``req.theta if req.theta is not
    None else settings.default_theta``). The run's YAML ``service:`` block reaches those settings
    (``JUNIPER_RECURRENCE_CONFIG_FILE``), so ``service.default_theta`` turns an unset ``train.theta``
    into that fixed value. Labelling it data-driven, as this did before, named the wrong θ.
    A ``default_theta`` the service takes from its own environment is not visible here.
    """
    train = train_config if isinstance(train_config, Mapping) else {}
    service = service_config if isinstance(service_config, Mapping) else {}
    if train.get("theta") is not None:
        return {"value": train.get("theta"), "note": THETA_NOTE_EXPLICIT}
    if service.get("default_theta") is not None:
        return {"value": service.get("default_theta"), "note": THETA_NOTE_SERVICE_DEFAULT}
    return {"value": None, "note": THETA_NOTE_DATA_DRIVEN}


def _labelled_eval_block(basis: str, metric_names: Iterable[str], values: Optional[Mapping[str, Any]], meta: Optional[Mapping[str, Any]], held_out: bool, absent: Optional[str]) -> Dict[str, Any]:
    """One labelled eval block. The keys are the same whether or not it holds anything, so a reader never guards."""
    values = values if isinstance(values, Mapping) else {}
    meta = meta if isinstance(meta, Mapping) else {}
    undefined = meta.get("undefined")
    block: Dict[str, Any] = {"basis": basis, "split": meta.get("split"), "n_samples": meta.get("n_samples"), "held_out": held_out, "absent": absent}
    block.update({name: values.get(name) for name in metric_names})
    block.update({"n_classes": meta.get("n_classes"), "average": meta.get("average"), "undefined": dict(undefined) if isinstance(undefined, Mapping) else {}})
    return block


def _final_eval_absent(body: Optional[Mapping[str, Any]], live: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Why a cascor ``/v1/metrics`` body carries no final evaluation, or ``None`` when it carries one."""
    if body is None:
        return "no /v1/metrics body was collected"
    if live is None:
        return "the /v1/metrics body carries no eval_metrics block"
    if live.get("enabled") is False:
        return "eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)"
    if "final" not in live:
        return "the service predates the final evaluation (juniper-cascor#614): eval_metrics has no final block"
    final = live.get("final")
    if final is None:
        return "eval_metrics.final is null: cascor scores the finished model only after a run that completes successfully with a test or validation split loaded"
    if not isinstance(final, Mapping):
        return f"eval_metrics.final is not an object ({type(final).__name__})"
    return None


def cascor_eval_blocks(metrics_final: Optional[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """juniper-ml#2064: a cascor run's two labelled eval blocks, from the ``/v1/metrics`` body the driver collects.

    ``eval_scalars`` is the run's eval scalars: cascor's ``eval_metrics.final`` (juniper-cascor#614), the
    finished model scored ONCE after the last weight update, with the ``split`` and ``n_samples`` it was scored
    on. ``held_out`` is true only when that split is ``test``. With no test split loaded cascor scores
    ``validation``, the in-loop split early stopping reads, so that block is selected-on and ``held_out`` is
    false. ``accuracy`` comes with juniper-cascor#731; ``undefined`` is cascor's own metric -> reason map.

    ``eval_scalars_in_loop`` keeps the flat ``f1`` / ``precision`` / ``recall`` / ``roc_auc`` fields, the
    live mid-training values ``eval_scalars`` held, unlabelled, until juniper-ml#2064. They are labelled with
    the live block's own ``split`` and ``n_samples``, and are never held out.

    A run with no final evaluation keeps every ``eval_scalars`` value ``None`` and says why in ``absent``:
    eval metrics disabled, a run that did not complete successfully, no test or validation split loaded, or
    a service that predates the final evaluation. It never falls back to the in-loop values, which are a
    different quantity on different rows. This one derivation feeds ``stats.json``, ``summary.md`` and
    ``eval_metrics.png``, and ``run_suite`` re-derives the final block from a run's ``metrics_final.json`` when
    its stats.json was written before the block existed.
    """
    body = metrics_final if isinstance(metrics_final, Mapping) else None
    live = body.get("eval_metrics") if body is not None else None
    live = live if isinstance(live, Mapping) else None
    absent = _final_eval_absent(body, live)
    final = live.get("final") if live is not None and absent is None else None
    held = _labelled_eval_block(CASCOR_FINAL_EVAL_BASIS, CASCOR_FINAL_EVAL_METRICS, final, final, isinstance(final, Mapping) and final.get("split") == "test", absent)
    if body is None:
        in_loop_absent: Optional[str] = "no /v1/metrics body was collected"
    elif live is not None and live.get("enabled") is False:
        in_loop_absent = "eval metrics disabled (JUNIPER_CASCOR_EVAL_METRICS_ENABLED)"
    elif all(body.get(name) is None for name in CASCOR_IN_LOOP_METRICS):
        in_loop_absent = "the service reported no in-loop eval scalars"
    else:
        in_loop_absent = None
    in_loop = _labelled_eval_block(CASCOR_IN_LOOP_BASIS, CASCOR_IN_LOOP_METRICS, body if in_loop_absent is None else None, live if in_loop_absent is None else None, False, in_loop_absent)
    return {"eval_scalars": held, "eval_scalars_in_loop": in_loop}


def is_labelled_eval_block(block: Any) -> bool:
    """True for a block :func:`cascor_eval_blocks` writes. A ``juniper-experiment-stats/1`` file's
    ``cascor.eval_scalars`` is the four in-loop values with no ``split``, so it is not one."""
    return isinstance(block, Mapping) and "split" in block and "absent" in block


def eval_caption(block: Any) -> str:
    """``test split, n=120, held out`` -- what ``summary.md`` prints beside a labelled eval block's heading."""
    if not is_labelled_eval_block(block):
        return "unlabelled: a juniper-experiment-stats/1 block, the in-loop values"
    if block.get("absent"):
        return "none"
    split = block.get("split")
    n_samples = block.get("n_samples")
    if block.get("held_out"):
        status = "held out"
    elif split == "validation":
        status = "NOT held out: the in-loop split"
    elif split == "training":
        status = "NOT held out: the training split"
    else:
        status = "NOT held out"
    return f"{split or 'unknown'} split, n={n_samples if n_samples is not None else 'unknown'}, {status}"


def build_stats(
    manifest: Mapping[str, Any],
    kind: str,
    series_rows: Optional[List[Mapping[str, Any]]] = None,
    metrics_final: Optional[Mapping[str, Any]] = None,
    train_summary: Optional[Mapping[str, Any]] = None,
    crossval: Optional[Mapping[str, Any]] = None,
    train_config: Optional[Mapping[str, Any]] = None,
    target_summary: Optional[Mapping[str, Any]] = None,
    target_summary_error: Optional[str] = None,
    service_config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the SS8.3 stats dict from the manifest + kind-specific collected payloads.

    ``target_summary`` is :func:`regression_target_summary`'s result for the run's dataset artifact
    (W5.5) and lands under ``dataset.target_summary``; ``target_summary_error`` is the driver's
    reason when it could not produce one and becomes a degraded-mode note. ``service_config`` is the
    run's YAML ``service:`` block; :func:`theta_block` reads its ``default_theta``.
    """
    git_block = {}
    for repo, info in (manifest.get("git") or {}).items():
        if isinstance(info, Mapping):
            git_block[repo] = {"head_sha": info.get("head_sha"), "dirty": info.get("dirty")} if "head_sha" in info else {"error": info.get("error")}
    packages = {name: (info.get("version") if isinstance(info, Mapping) else info) for name, info in (manifest.get("packages") or {}).items()}

    stats: Dict[str, Any] = {
        "schema": STATS_SCHEMA,
        "identity": {
            "run_id": manifest.get("run_id"),
            "experiment": (manifest.get("experiment") or {}).get("name"),
            "description": (manifest.get("experiment") or {}).get("description"),
            "config_sha256": manifest.get("config_sha256"),
            "seeds": manifest.get("seeds"),
            "git": git_block,
            "packages": packages,
        },
        "dataset": _dataset_block(manifest, target_summary),
        "outcome": {
            "outcome": manifest.get("outcome"),
            "acceptance": manifest.get("acceptance"),
            "wall_seconds": (manifest.get("timings") or {}).get("total"),
            "timings": manifest.get("timings"),
        },
        "provenance": {
            "metrics_scraped": manifest.get("metrics_scraped"),
            "degraded_notes": _degraded_notes(manifest, kind, metrics_final, target_summary_error),
        },
    }

    if kind == "cascor":
        rows = series_rows or []
        final = metrics_final if isinstance(metrics_final, Mapping) else {}
        stats["cascor"] = {
            "final": {name: final.get(name) for name in ("epoch", "train_loss", "train_accuracy", "val_loss", "val_accuracy", "hidden_units")},
            # juniper-ml#2064: `eval_scalars` is the labelled FINAL evaluation, `eval_scalars_in_loop` the live
            # values it held, unlabelled, under juniper-experiment-stats/1. Neither stands in for the other.
            **cascor_eval_blocks(metrics_final),
            "completion_reason": manifest.get("completion_reason"),
            "candidate_correlation": correlation_per_round(rows),
            "training_step_duration": step_duration_stats(rows),
        }
    else:
        train = train_summary if isinstance(train_summary, Mapping) else {}
        cfg = train_config if isinstance(train_config, Mapping) else {}
        cv_block = None
        if isinstance(crossval, Mapping):
            cv_block = {
                "n_folds": crossval.get("n_folds"),
                "task_type": crossval.get("task_type"),
                "eval_aggregate": crossval.get("eval_aggregate"),
                "eval_std": crossval.get("eval_std"),
                "folds": [
                    {"fold": fold.get("fold"), "eval_metrics": fold.get("eval_metrics"), "n_epochs": fold.get("n_epochs")}
                    for fold in (crossval.get("folds") or [])
                    if isinstance(fold, Mapping)
                ],
            }
        stats["recurrence"] = {
            "final_metrics": train.get("final_metrics"),
            "n_epochs": train.get("n_epochs"),
            "stopped_reason": train.get("stopped_reason"),
            "dataset_descriptor": train.get("dataset"),
            "theta": theta_block(cfg, service_config),
            "readout": {"rung": cfg.get("readout") or "linear", "hyperparameters": {key: value for key, value in cfg.items() if key not in {"readout"} and value is not None}},
            "crossval": cv_block,
        }
    return stats


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _metric_lines(block: Optional[Mapping[str, Any]]) -> List[str]:
    if not isinstance(block, Mapping):
        return ["(none)"]
    lines = [f"- {name}: {_fmt(value)}" for name, value in sorted(block.items()) if value is not None]
    return lines or ["(none)"]


def _eval_lines(block: Any, metric_names: Iterable[str], absent_rider: str = "") -> List[str]:
    """A labelled eval block's lines: each metric in report order, an undefined one with cascor's reason, then the basis.

    An absent block prints its reason and nothing else. A ``juniper-experiment-stats/1`` block (no labels)
    renders as it always did, and the heading :func:`eval_caption` writes says what it is.
    """
    if not is_labelled_eval_block(block):
        return _metric_lines(block)
    if block.get("absent"):
        return [f"(none: {block['absent']}{absent_rider})"]
    undefined = block.get("undefined") if isinstance(block.get("undefined"), Mapping) else {}
    lines: List[str] = []
    for name in metric_names:
        value = block.get(name)
        if value is not None:
            lines.append(f"- {name}: {_fmt(value)}")
        elif name in undefined:
            lines.append(f"- {name}: undefined ({undefined[name]})")
        else:
            lines.append(f"- {name}: not reported")
    lines.append(f"- basis: {block.get('basis')}")
    return lines


def render_summary_md(stats: Mapping[str, Any]) -> str:
    """Render the human-readable SS8.3 ``summary.md`` from a :func:`build_stats` dict."""
    identity = stats.get("identity") or {}
    dataset = stats.get("dataset") or {}
    outcome = stats.get("outcome") or {}
    provenance = stats.get("provenance") or {}
    shapes = dataset.get("shapes") or {}
    lines: List[str] = [
        f"# Run summary — {identity.get('run_id')}",
        "",
        f"**Experiment**: {identity.get('experiment')} — {identity.get('description') or '(no description)'}",
        f"**Outcome**: {outcome.get('outcome')} (acceptance ok: {(outcome.get('acceptance') or {}).get('ok')}) in {_fmt(outcome.get('wall_seconds'))}s",
        f"**Config SHA-256**: `{identity.get('config_sha256')}`",
        f"**Seeds**: {identity.get('seeds')}",
        "",
        "## Dataset",
        "",
        f"- generator: {dataset.get('generator')} v{dataset.get('generator_version')} (task: {dataset.get('task_type')})",
        f"- dataset_id: `{dataset.get('dataset_id')}`",
        f"- shapes: {', '.join(f'{key}={_fmt(val)}' for key, val in shapes.items() if val is not None)}",
    ]
    if dataset.get("class_distribution"):
        lines.append(f"- class distribution: {dataset.get('class_distribution')}")
    # W5.5 (F-D8): one line per split; a split with no finite values says so instead of printing None moments.
    target = dataset.get("target_summary")
    if isinstance(target, Mapping) and isinstance(target.get("splits"), Mapping):
        lines.append("- regression target (y_reg) per split:")
        for split, block in target["splits"].items():
            block = block if isinstance(block, Mapping) else {}
            head = f"  - {split}: n={_fmt(block.get('n'))}, finite={_fmt(block.get('n_finite'))} (fraction {_fmt(block.get('finite_fraction'))})"
            if block.get("n_finite"):
                lines.append(head + f", mean={_fmt(block.get('mean'))}, std={_fmt(block.get('std'))}, min={_fmt(block.get('min'))}, max={_fmt(block.get('max'))}")
            else:
                lines.append(head + ", moments unavailable (no finite values)")
        lines.append(f"  - basis: {target.get('basis')}")
    lines += ["", "## Timings", ""]
    lines += [f"- {phase}: {_fmt(seconds)}s" for phase, seconds in sorted((outcome.get("timings") or {}).items())]

    if "cascor" in stats:
        cascor = stats["cascor"] or {}
        lines += ["", "## cascor", "", "### Final metrics", ""]
        lines += _metric_lines(cascor.get("final"))
        # juniper-ml#2064: the run's eval scalars are the labelled final evaluation; the in-loop values follow
        # under their own label. A run without a final evaluation says so here and borrows nothing.
        held, in_loop = cascor.get("eval_scalars"), cascor.get("eval_scalars_in_loop")
        lines += ["", f"### Eval scalars ({'final evaluation: ' if is_labelled_eval_block(held) else ''}{eval_caption(held)})", ""]
        lines += _eval_lines(held, CASCOR_FINAL_EVAL_METRICS, "; the in-loop values below are not the run's eval scalars")
        if in_loop is not None or is_labelled_eval_block(held):
            lines += ["", f"### In-loop eval scalars ({eval_caption(in_loop)})", ""]
            lines += _eval_lines(in_loop, CASCOR_IN_LOOP_METRICS)
        correlation = cascor.get("candidate_correlation") or {}
        lines += ["", "### Candidate correlation (per growth round; from metrics_series.csv)", ""]
        rounds = correlation.get("per_round") or []
        lines += [f"- hidden_units={entry.get('hidden_units')}: best {_fmt(entry.get('best_correlation'))}" for entry in rounds] or ["(no samples)"]
        duration = cascor.get("training_step_duration") or {}
        lines += ["", "### Training step duration", ""]
        lines += [
            f"- total steps: {_fmt(duration.get('total_steps'))}, overall mean: {_fmt(duration.get('overall_mean_seconds'))}s",
            f"- p50: {_fmt(duration.get('p50_seconds'))}s, p95: {_fmt(duration.get('p95_seconds'))}s ({duration.get('basis')})",
        ]
        if cascor.get("completion_reason"):
            lines.append(f"- completion reason: {cascor.get('completion_reason')}")

    if "recurrence" in stats:
        recurrence = stats["recurrence"] or {}
        lines += ["", "## recurrence", "", "### Train", ""]
        lines += _metric_lines(recurrence.get("final_metrics"))
        lines += [
            f"- n_epochs: {_fmt(recurrence.get('n_epochs'))}, stopped_reason: {recurrence.get('stopped_reason')}",
            f"- theta: {(recurrence.get('theta') or {}).get('value')} ({(recurrence.get('theta') or {}).get('note')})",
            f"- readout: {(recurrence.get('readout') or {}).get('rung')} {(recurrence.get('readout') or {}).get('hyperparameters')}",
        ]
        cv_block = recurrence.get("crossval")
        lines += ["", "### Cross-validation", ""]
        if isinstance(cv_block, Mapping):
            lines.append(f"- {cv_block.get('n_folds')} folds ({cv_block.get('task_type')}); aggregate:")
            lines += [f"  - {name}: {_fmt(value)} ± {_fmt((cv_block.get('eval_std') or {}).get(name))}" for name, value in sorted((cv_block.get("eval_aggregate") or {}).items())]
        else:
            lines.append("(disabled or failed)")

    lines += ["", "## Provenance / health", ""]
    scraped = provenance.get("metrics_scraped") or {}
    # Report BOTH facts, and never let the local one stand in for the remote one. A target file
    # written is not a scrape confirmed: five bridged PF-1 runs wrote the file and Prometheus held
    # no series for any of them. ``scrape_confirmed`` is tri-state — None means the question could
    # not be asked (Prometheus unreachable), which is not the same finding as "nothing was scraped".
    # ``present`` is the pre-2026-09-01 key name, read as a fallback so old manifests still render.
    written = scraped.get("target_file_written", scraped.get("present"))
    confirmed = scraped.get("scrape_confirmed", "n/a (pre-2026-09-01 manifest)")
    lines.append(f"- grafana bridge: {scraped.get('grafana_bridge')}, target file written: {written}, scrape confirmed: {confirmed}")
    if scraped.get("reason"):
        lines.append(f"  - {scraped['reason']}")
    notes = provenance.get("degraded_notes") or []
    if notes:
        lines += ["- degraded-mode notes:"] + [f"  - {note}" for note in notes]
    else:
        lines.append("- degraded-mode notes: none")
    lines += ["", "## Git provenance", ""]
    for repo, info in sorted((identity.get("git") or {}).items()):
        if isinstance(info, Mapping) and info.get("head_sha"):
            lines.append(f"- {repo}: `{info['head_sha'][:12]}`{' (DIRTY — not reproducible)' if info.get('dirty') else ''}")
        else:
            lines.append(f"- {repo}: (unavailable)")
    return "\n".join(lines) + "\n"
