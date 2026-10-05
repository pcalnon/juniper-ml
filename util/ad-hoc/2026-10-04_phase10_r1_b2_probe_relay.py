# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/probe_relay.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-B2 probe: does every path canopy relays cascor rows through drop ``kind``?

Executes, from trees extracted at the pinned commits:
  * cascor 95cdc562: TrainingMonitor (rows), create_metrics_message, create_initial_metrics_message
  * canopy 1b2dd438: CascorServiceAdapter.start_metrics_relay (the REAL relay loop) over a fake
    CascorTrainingStream that yields one ``metrics`` frame and one ``initial_metrics`` frame;
    websocket_manager.broadcast is captured, never sent.
  * canopy: DashboardManager._append_ws_metrics_store_handler + MetricsPanel._update_metrics_display_handler
    on the rows the browser bridge would push (the bridge itself is run in node by probe_bridge.js).

No socket is opened: the fake stream never connects anywhere, and the control supervisor is
disabled through canopy's own setting.
"""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import os
import sys
import types

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CANOPY_SRC, CASCOR_SRC = sys.argv[1], sys.argv[2]
os.chdir(SCRATCH)  # no stray .env is read by canopy's settings
os.environ["JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS"] = "false"  # do not start the control supervisor
os.environ["JUNIPER_CANOPY_WS_RELAY_SUMMARY_INTERVAL_SECONDS"] = "0"
sys.path.insert(0, CANOPY_SRC)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# cascor's monitor imports one constant from its constants package; read the real value from the tree.
consts_src = open(os.path.join(CASCOR_SRC, "cascor_constants/constants_api/constants_api_defaults.py")).read()
buf = None
for node in ast.parse(consts_src).body:
    if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "_PROJECT_API_METRICS_BUFFER_SIZE":
        buf = ast.literal_eval(node.value)
pkg = types.ModuleType("cascor_constants")
sub = types.ModuleType("cascor_constants.constants_api")
sub._PROJECT_API_METRICS_BUFFER_SIZE = buf
pkg.constants_api = sub
sys.modules["cascor_constants"] = pkg
sys.modules["cascor_constants.constants_api"] = sub

monitor_mod = load("cascor_monitor_95cdc562", os.path.join(CASCOR_SRC, "api/lifecycle/monitor.py"))
msgs = load("cascor_messages_95cdc562", os.path.join(CASCOR_SRC, "api/websocket/messages.py"))

# Rows exactly as cascor's monitor writes them: an initial-pass sample, the step row, then a growth-pass sample.
mon = monitor_mod.TrainingMonitor()
mon.on_training_start(retain_metrics=False)
mon.on_phase_change("output")
mon.on_epoch_end(epoch=1, loss=0.50, accuracy=None, learning_rate=0.1, hidden_units=0, kind="output_epoch")
mon.on_epoch_end(epoch=26, loss=0.45, accuracy=None, learning_rate=0.1, hidden_units=0, kind="output_epoch")
mon.on_phase_change("candidate")
mon.on_epoch_end(epoch=1, loss=0.40, accuracy=0.60, learning_rate=0.1, hidden_units=1)  # training_step (drained at the phase_change)
mon.on_epoch_end(epoch=2501, loss=0.30, accuracy=None, learning_rate=0.1, hidden_units=1, kind="output_epoch")
rows = mon.get_all_metrics()

metrics_frame = msgs.create_metrics_message(rows[-1], seq=7)
burst_frame = msgs.create_initial_metrics_message(rows, current_seq=7)

import backend.cascor_service_adapter as csa  # noqa: E402
from communication.websocket_manager import websocket_manager  # noqa: E402

CAPTURED: list = []


async def capture(message, *a, **k):
    CAPTURED.append(json.loads(json.dumps(message, default=str)))


websocket_manager.broadcast = capture


class FakeStream:
    connects = 0

    def __init__(self, base_url=None, api_key=None, **kw):
        self.api_key = api_key

    async def connect(self):
        FakeStream.connects += 1
        if FakeStream.connects > 1:
            await asyncio.Event().wait()  # park the reconnect; the probe cancels it

    def stream(self):
        async def gen():
            for f in (burst_frame, metrics_frame):
                yield f

        return gen()

    async def disconnect(self):
        return None


csa.CascorTrainingStream = FakeStream


async def main():
    adapter = csa.CascorServiceAdapter(service_url="http://127.0.0.1:9", api_key=None)
    await adapter.start_metrics_relay()
    for _ in range(50):
        await asyncio.sleep(0.05)
        if len(CAPTURED) >= 2:
            break
    await adapter.stop_metrics_relay()


asyncio.run(main())

print(f"relay connects: {FakeStream.connects}; broadcasts captured: {[m.get('type') for m in CAPTURED]}")
by_type = {m.get("type"): m for m in CAPTURED}
relayed_metrics = by_type["metrics"]["data"]
relayed_burst_rows = by_type["initial_metrics"]["data"]["metrics"]
print(f"metrics frame as relayed     : keeps kind={'kind' in relayed_metrics}; flat loss={'loss' in relayed_metrics}; keys={sorted(relayed_metrics)}")
print(f"initial_metrics as relayed   : {len(relayed_burst_rows)} rows; kinds={[r.get('kind') for r in relayed_burst_rows]}; nested 'metrics' dict={'metrics' in relayed_burst_rows[0]}; flat loss={'loss' in relayed_burst_rows[0]}")
json.dump(CAPTURED, open(os.path.join(SCRATCH, "relayed_frames.json"), "w"))

from frontend.components.metrics_panel import MetricsPanel  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402

panel = MetricsPanel({}, component_id="probe")
mode = {"mode": "window", "window_size": 500}
for label, events in (("relayed metrics frames only", [relayed_metrics]), ("relayed initial_metrics burst rows", relayed_burst_rows)):
    store = DashboardManager._append_ws_metrics_store_handler(None, ws_metrics_buffer={"events": events}, display_mode_state=mode, current_metrics=[])
    loss_fig, acc_fig, step_tile, loss_str, acc_str, *_ = panel._update_metrics_display_handler(metrics_data=store)
    loss_y = [y for tr in loss_fig.data for y in (tr.y or ())]
    acc_y = list(acc_fig.data[0].y or ())
    print(f"store <- {label:<36}: rows={len(store)} kinds_in_store={[m.get('kind') for m in store]} Training Step tile={step_tile!r} loss tile={loss_str!r} loss y={loss_y} acc trace0 y={acc_y}")

# Extract the clientside extendTraces fast path's JS from metrics_panel.py for the node probe.
mp_src = open(os.path.join(CANOPY_SRC, "frontend/components/metrics_panel.py")).read()
js = None
for node in ast.walk(ast.parse(mp_src)):
    if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "clientside_callback" and node.args:
        a0 = node.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and "extendTraces(lossEl" in a0.value:
            js = a0.value
            print(f"extendTraces clientside callback found at metrics_panel.py:{node.lineno}")
open(os.path.join(SCRATCH, "extend_traces_fn.js"), "w").write(js)
