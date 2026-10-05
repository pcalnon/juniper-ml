# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_o2_burst_panel.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Feed an initial_metrics burst (raw cascor rows, as the relay forwards them) through canopy's REAL
_append_ws_metrics_store_handler and MetricsPanel handler (1b2dd438): what do the panel's charts read
for those rows?"""
import importlib.util
import logging
import os
import sys

CANOPY_SRC, CASCOR_SRC = sys.argv[1], sys.argv[2]
sys.path.insert(0, CANOPY_SRC)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))
spec = importlib.util.spec_from_file_location("cascor_monitor_pin", f"{CASCOR_SRC}/api/lifecycle/monitor.py")
mon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mon)
from backend.cascor_service_adapter import CascorServiceAdapter as A  # noqa: E402
from frontend.components.metrics_panel import MetricsPanel  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402

m = mon.TrainingMonitor()
for inner in (1, 26, 51):
    m.on_epoch_end(epoch=inner, loss=0.5, accuracy=None, learning_rate=0.1, hidden_units=0, kind="output_epoch")
m.on_epoch_end(epoch=1, loss=0.4, accuracy=0.7, learning_rate=0.1, hidden_units=0, kind="training_step")
raw = m.get_all_metrics()
rest_rows = [A._to_dashboard_metric(A._normalize_metric(r)) for r in raw]  # what the REST poll put in the store
dm = object.__new__(DashboardManager)
dm.logger = logging.getLogger("x")
store = dm._append_ws_metrics_store_handler(ws_metrics_buffer={"events": raw, "gen": 1}, display_mode_state={"mode": "window", "window_size": 100}, current_metrics=rest_rows)
panel = MetricsPanel({}, component_id="burst")
loss_fig, acc_fig, step, loss_s, acc_s, *_ = panel._update_metrics_display_handler(metrics_data=store)
tr = acc_fig.data[0]
print("store rows:", len(store), "| burst rows keep kind:", [r.get("kind") for r in store[4:]])
print("accuracy trace (x, y):", list(zip(tr.x, tr.y)))
print("loss trace 0 (x, y):", list(zip(loss_fig.data[0].x, loss_fig.data[0].y)))
print("tiles: step", step, "loss", loss_s, "accuracy", acc_s)
