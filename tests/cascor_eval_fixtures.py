"""Real cascor ``/v1/metrics`` bodies for the juniper-ml#2064 eval-scalar tests, copied verbatim.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (helpers for util/experiments/stats_summary.py, plots_cascor.py, run_suite.py)
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Shared by ``tests/test_stats_summary_eval_blocks.py`` (the derivation, ``summary.md`` and the plot) and
``tests/test_run_suite.py`` (the ``test_*`` headline columns and the ``--reaggregate`` backfill). Each body
is a run's ``artifacts/results/metrics_final.json`` from the run corpus at
``~/.local/state/juniper-experiments``, read 2026-10-27, so every field name and every shape below is one a
real cascor service produced. The corpus holds 416 cascor bodies: 268 with no ``eval_metrics.final`` key,
84 whose final block scored ``test`` and 64 whose final block scored ``validation``. None carries
``final.accuracy`` yet, because juniper-cascor#731 is in no release.

- ``METRICS_FINAL_TEST_SPLIT`` -- run ``20260916T002848Z-3959``, the run juniper-ml#2064 cites: the in-loop
  scores are on 160 validation rows (f1 0.9187), the final evaluation on 120 test rows (f1 0.8997).
- ``METRICS_FINAL_VALIDATION_SPLIT`` -- run ``20260901T071754Z-ecd4``: no test split was loaded, so the final
  block scored ``validation``, the in-loop split, and repeats the in-loop numbers exactly.
- ``METRICS_FINAL_PRE_SWITCH`` -- run ``20260807T195013Z-32d8``: before juniper-cascor#614 there is no
  ``final`` key at all, and this run's in-loop scores were computed on the TRAINING split.
- ``METRICS_FINAL_NULL_FINAL`` -- juniper-cascor main's golden ``metrics_post_train.json``
  (``src/tests/fixtures/golden/api_snapshots/``, its ``data``): ``final`` is ``null`` because the run had no
  reportable split.
- ``V1_STATS_CASCOR`` -- the ``cascor`` block run ``20260916T002848Z-3959``'s ``stats.json`` was written with
  (``juniper-experiment-stats/1``): its ``eval_scalars`` are the IN-LOOP values, unlabelled.

``with_final_accuracy`` adds the ``accuracy`` juniper-cascor#731 puts in the final block, and the
``undefined`` reason it records when accuracy is undefined. That shape is CONSTRUCTED from juniper-cascor
main's ``_compute_final_eval_metrics`` (``src/api/lifecycle/manager.py``), not observed: no run has it yet.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

METRICS_FINAL_TEST_SPLIT: Dict[str, Any] = {
    "dataset_shortfall": None,
    "epoch": 17,
    "eval_metrics": {
        "average": "macro",
        "enabled": True,
        "final": {"average": "macro", "f1": 0.899749373433584, "final": True, "n_classes": 2, "n_samples": 120, "precision": 0.9020979020979021, "recall": 0.8994165045846069, "roc_auc": 0.9605445957210336, "split": "test", "undefined": {}},
        "n_classes": 2,
        "n_samples": 160,
        "split": "validation",
        "undefined": {},
    },
    "f1": 0.9187214255011527,
    "hidden_units": 16,
    "precision": 0.9193396964481302,
    "recall": 0.91875,
    "roc_auc": 0.98078125,
    "timestamp": "2026-09-15T19:29:23.014446",
    "train_accuracy": 0.905,
    "train_loss": 0.06737957149744034,
    "val_accuracy": 0.91875,
    "val_loss": 0.06876520812511444,
}

METRICS_FINAL_VALIDATION_SPLIT: Dict[str, Any] = {
    "epoch": 3,
    "eval_metrics": {
        "average": "macro",
        "enabled": True,
        "final": {"average": "macro", "f1": 0.34959349593495936, "final": True, "n_classes": 2, "n_samples": 80, "precision": 0.350844277673546, "recall": 0.3500942803268385, "roc_auc": 0.5380263984915148, "split": "validation", "undefined": {}},
        "n_classes": 2,
        "n_samples": 80,
        "split": "validation",
        "undefined": {},
    },
    "f1": 0.34959349593495936,
    "hidden_units": 2,
    "precision": 0.350844277673546,
    "recall": 0.3500942803268385,
    "roc_auc": 0.5380263984915148,
    "timestamp": "2026-09-01T02:18:24.195176",
    "train_accuracy": 0.571875,
    "train_loss": 0.2040208876132965,
    "val_accuracy": 0.35,
    "val_loss": 0.2635728716850281,
}

METRICS_FINAL_PRE_SWITCH: Dict[str, Any] = {
    "epoch": 2,
    "eval_metrics": {"average": "macro", "enabled": True, "n_classes": 2, "n_samples": 200, "split": "training", "undefined": {}},
    "f1": 0.5049876246906173,
    "hidden_units": 1,
    "precision": 0.5050005000500051,
    "recall": 0.505,
    "roc_auc": 0.59045,
    "timestamp": "2026-08-07T14:50:55.981579",
    "train_accuracy": 0.505,
    "train_loss": 0.2405010610818863,
    "val_accuracy": None,
    "val_loss": None,
}

METRICS_FINAL_NULL_FINAL: Dict[str, Any] = {
    "dataset_shortfall": None,
    "epoch": 3,
    "eval_metrics": {"average": "macro", "enabled": True, "final": None, "n_classes": None, "n_samples": None, "split": None, "undefined": {}},
    "f1": None,
    "hidden_units": 2,
    "precision": None,
    "recall": None,
    "roc_auc": None,
    "train_accuracy": 0.48333333333333334,
    "train_loss": 0.4036097526550293,
    "val_accuracy": None,
    "val_loss": None,
}

V1_STATS_CASCOR: Dict[str, Any] = {
    "completion_reason": "early_stopped",
    "eval_scalars": {"f1": 0.9187214255011527, "precision": 0.9193396964481302, "recall": 0.91875, "roc_auc": 0.98078125},
    "final": {"epoch": 17, "hidden_units": 16, "train_accuracy": 0.905, "train_loss": 0.06737957149744034, "val_accuracy": 0.91875, "val_loss": 0.06876520812511444},
}


def with_final_accuracy(body: Dict[str, Any], accuracy: Optional[float], reason: Optional[str] = None) -> Dict[str, Any]:
    """A deep copy of ``body`` whose final block carries juniper-cascor#731's ``accuracy`` (and ``undefined.accuracy`` when ``reason`` is given)."""
    out = copy.deepcopy(body)
    final = out["eval_metrics"]["final"]
    final["accuracy"] = accuracy
    if reason is not None:
        final["undefined"] = {**final.get("undefined", {}), "accuracy": reason}
    return out
