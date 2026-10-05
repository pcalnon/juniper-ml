#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Re-derive the selection arc's O2 by EXECUTING canopy's metrics path on cascor-shaped rows.

O2 (``reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`` § "Observations"):
both metric charts plot ``metric["epoch"]`` as x, and that field is not one axis.

cascor's monitor (``src/api/lifecycle/monitor.py``, ``on_epoch_end``) writes two numberings into the
same field and tells them apart with ``kind``:

  kind="training_step"  epoch = the 1-based completed-step index (the history drain; carries accuracy)
  kind="output_epoch"   epoch = the inner epoch within the current output pass, ~every 25th
                        (the ``epoch_end`` handler; ``accuracy=None``)

This script builds rows in exactly that shape, passes them through canopy's REAL relay
(``CascorServiceAdapter._normalize_metric`` then ``_to_dashboard_metric``) and REAL panel
(``MetricsPanel._update_metrics_display_handler``), from a canopy tree extracted at a pinned commit,
and reports:

  * the x extent of each chart, and the x extent of the points that carry an accuracy value;
  * the "Training Step" tile, mid-pass (the last row is an ``output_epoch`` row);
  * the same two readings with ``kind`` kept (the rows handed to the panel directly), as the control,
    because the panel's step filter keys on ``kind`` and the relay may drop it.

Could it have answered otherwise? The control arm differs from the relay arm only in whether ``kind``
survives, so a relay that carried ``kind`` would make the two step tiles equal.

Usage (canopy env, LIBTORCH cleared):
    env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-10-04_phase10_o2_rederive.py --canopy-src <canopy tree at 1b2dd438>/src
"""

from __future__ import annotations

import argparse
import sys


def cascor_row(epoch: int, kind: str, phase: str, loss: float, accuracy, hidden_units: int) -> dict:
    """One row as cascor's TrainingMonitor.on_epoch_end builds it (monitor.py, the ``metrics`` dict)."""
    return {
        "epoch": epoch,
        "timestamp": "2026-10-04T00:00:00",
        "loss": loss,
        "accuracy": accuracy,
        "learning_rate": 0.01,
        "hidden_units": hidden_units,
        "phase": phase,
        "validation_loss": None,
        "validation_accuracy": None,
        "kind": kind,
        "f1": None,
        "precision": None,
        "recall": None,
        "roc_auc": None,
    }


def synthetic_run(output_epochs: int = 10000, steps: int = 3) -> list:
    """An initial output pass, then grow iterations, each ending in its training-step row.

    Inner-epoch samples are every 25th epoch from 1, as CCN's throttled callback emits them; the run is
    cut mid-way through the last pass, so the newest row is an ``output_epoch`` row.
    """
    rows = []
    for step in range(1, steps + 1):
        for inner in range(1, output_epochs + 1, 25):
            rows.append(cascor_row(inner, "output_epoch", "output", 0.5 / step, None, step - 1))
        rows.append(cascor_row(step, "training_step", "output", 0.4 / step, 0.5 + 0.1 * step, step - 1))
    for inner in range(1, 2526, 25):  # the next pass, still running
        rows.append(cascor_row(inner, "output_epoch", "output", 0.1, None, steps))
    return rows


def extents(fig) -> dict:
    """x extent over every trace, and over the points that carry a y value on trace 0."""
    xs_all = [x for tr in fig.data for x in (tr.x or ()) if x is not None]
    tr0 = fig.data[0]
    xs_valued = [x for x, y in zip(tr0.x or (), tr0.y or (), strict=False) if y is not None]
    return {"x_all": (min(xs_all), max(xs_all)) if xs_all else None, "x_valued_trace0": (min(xs_valued), max(xs_valued)) if xs_valued else None, "n_valued_trace0": len(xs_valued)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy-src", required=True, help="the src/ directory of a canopy tree at the pinned commit")
    args = ap.parse_args()
    sys.path.insert(0, args.canopy_src)

    from backend.cascor_service_adapter import CascorServiceAdapter
    from frontend.components.metrics_panel import MetricsPanel

    raw = synthetic_run()
    relayed = [CascorServiceAdapter._to_dashboard_metric(CascorServiceAdapter._normalize_metric(r)) for r in raw]
    kept = [dict(rel, kind=r["kind"]) for rel, r in zip(relayed, raw, strict=True)]
    panel = MetricsPanel({}, component_id="o2-rederive")

    print(f"rows: {len(raw)}  (last row: kind={raw[-1]['kind']} epoch={raw[-1]['epoch']}; last training_step epoch={max(r['epoch'] for r in raw if r['kind'] == 'training_step')})")
    print(f"relay keeps 'kind': {'kind' in relayed[0]}")
    for label, rows in (("relay (as canopy serves it)", relayed), ("control (kind kept)", kept)):
        loss_fig, acc_fig, step_tile, *_ = panel._update_metrics_display_handler(metrics_data=rows)
        print(f"\n== {label}")
        print(f"   loss chart     : {extents(loss_fig)}")
        print(f"   accuracy chart : {extents(acc_fig)}")
        print(f"   Training Step tile: {step_tile!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
