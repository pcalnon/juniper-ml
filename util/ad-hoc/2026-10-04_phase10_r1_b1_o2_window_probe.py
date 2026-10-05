# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B1.8nGM/o2_window_probe.py
# Written by Lane 10-B1 (adversarial, dispositions and ratings), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-B1 probe: what the Classification Metrics chart and Training Step tile show at canopy's
DEFAULT display mode (sliding window, 500 rows) for a CasCor run labelled as cascor labels it.

cascor (95cdc562 manager.py:2087-2115, :2144-2150): the monitor phase is 'output' for the initial
pass, 'candidate' from the first grow iteration until training_end, and 'output' again at
training_end, where the final drain runs.  Step rows are drained at the next event after a pass
ends, i.e. at the phase_change of the next grow iteration (phase already 'candidate') -- except the
last, drained at training_end (phase 'output').
"""

import sys

sys.path.insert(0, sys.argv[1])

from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402
from frontend.components.metrics_panel import MetricsPanel  # noqa: E402


def row(epoch, kind, phase, acc, hu):
    return {"epoch": epoch, "timestamp": "t", "loss": 0.1, "accuracy": acc, "learning_rate": 0.1, "hidden_units": hu, "phase": phase, "validation_loss": None, "validation_accuracy": None, "kind": kind, "f1": None, "precision": None, "recall": None, "roc_auc": None}


def run(output_epochs=10000, passes=11, cut_mid_last=False):
    rows = []
    for p in range(1, passes + 1):
        phase = "output" if p == 1 else "candidate"
        inner = list(range(1, output_epochs + 1, 25)) + ([output_epochs] if output_epochs % 25 != 1 else [])
        if cut_mid_last and p == passes:
            inner = [e for e in inner if e <= 2501]
        for e in inner:
            rows.append(row(e, "output_epoch", phase, None, p - 1))
        if cut_mid_last and p == passes:
            break
        # step row p drained at the NEXT event: phase_change (candidate) or training_end (output)
        step_phase = "output" if p == passes else "candidate"
        rows.append(row(p, "training_step", step_phase, 0.5 + 0.04 * p, p - 1))
    return rows


def show(label, rows, panel):
    relayed = [CascorServiceAdapter._to_dashboard_metric(CascorServiceAdapter._normalize_metric(r)) for r in rows]
    _, acc_fig, tile, *_ = panel._update_metrics_display_handler(metrics_data=relayed)
    tr0 = acc_fig.data[0]
    valued = [(x, y) for x, y in zip(tr0.x, tr0.y) if y is not None]
    xs = [x for tr in acc_fig.data for x in (tr.x or ()) if x is not None]
    print(f"{label}: rows={len(rows)} x-extent={min(xs)}..{max(xs)} accuracy points={valued} tile={tile!r}")


panel = MetricsPanel({}, component_id="b1")
full = run()
show("full history, completed run, out=10000", full, panel)
show("window 500 (default), completed run, out=10000", full[-500:], panel)
small = run(output_epochs=25)
show("full history, completed run, out=25", small, panel)
show("window 500, completed run, out=25", small[-500:], panel)
mid = run(cut_mid_last=True)
show("window 500, mid-pass of pass 11, out=10000", mid[-500:], panel)
