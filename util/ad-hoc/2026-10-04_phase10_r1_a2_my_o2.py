# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_o2.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-A2 independent reproduction of F-CANOPY-064's relay/tile claims.

Rows are produced by cascor's REAL TrainingMonitor.on_epoch_end (95cdc562), not hand-built.
They are then pushed through each canopy path by driving canopy's REAL code (1b2dd438):
  REST history  : _ServiceTrainingMonitor.get_recent_metrics (fake cascor client returns cascor's REST envelope)
  /api/metrics  : _ServiceTrainingMonitor.get_current_metrics
  WS relay      : CascorServiceAdapter.start_metrics_relay's loop, with a fake training stream that yields
                  frames built by cascor's REAL create_metrics_message, and websocket_manager.broadcast captured
  state sync    : CascorStateSync.sync
and finally through MetricsPanel._update_metrics_display_handler.

Usage: python my_o2.py <canopy src> <cascor src>
"""
import asyncio
import importlib.util
import sys

CANOPY_SRC, CASCOR_SRC = sys.argv[1], sys.argv[2]
sys.path.insert(0, CANOPY_SRC)
# cascor_constants only (a shim dir holding just that package), ahead of site-packages
import os  # noqa: E402

sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))
for _k in [k for k in sys.modules if k == "cascor_constants" or k.startswith("cascor_constants.")]:
    del sys.modules[_k]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mon_mod = load("cascor_monitor_pin", f"{CASCOR_SRC}/api/lifecycle/monitor.py")
msg_mod = load("cascor_messages_pin", f"{CASCOR_SRC}/api/websocket/messages.py")


def run_monitor(budget, stride, steps, cut_inner):
    """Drive cascor's monitor the way the manager does: inner-epoch rows (kind=output_epoch, accuracy=None)
    during each pass, a training_step row when the pass completes; growth passes under phase 'candidate'
    (the manager's phase at the first grow iteration). If cut_inner is set, end mid-pass."""
    m = mon_mod.TrainingMonitor()
    m.on_training_start(retain_metrics=False)
    frames = []
    m.register_callback("epoch_end", lambda metrics, **kw: frames.append(msg_mod.create_metrics_message(metrics)))
    for s in range(1, steps + 1):
        if s == 2:
            m.on_phase_change("candidate")
        inner_points = sorted(set(list(range(1, budget + 1, stride)) + [budget]))
        for inner in inner_points:
            m.on_epoch_end(epoch=inner, loss=1.0 / (s + inner), accuracy=None, learning_rate=0.05, hidden_units=s - 1, kind="output_epoch")
        m.on_epoch_end(epoch=s, loss=0.3 / s, accuracy=0.55 + 0.05 * s, learning_rate=0.05, hidden_units=s - 1, kind="training_step")
    if cut_inner:
        for inner in range(1, cut_inner + 1, stride):
            m.on_epoch_end(epoch=inner, loss=0.01, accuracy=None, learning_rate=0.05, hidden_units=steps, kind="output_epoch")
    return m.get_all_metrics(), frames


class FakeClient:
    def __init__(self, rows):
        self.rows = rows

    def get_metrics_history(self, count=None):
        rows = self.rows if not count else self.rows[-count:]
        return {"status": "success", "data": rows, "meta": {}}

    def get_metrics(self):
        return {"status": "success", "data": self.rows[-1], "meta": {}}

    def get_training_status(self):
        return {"status": "success", "data": {}}

    def get_training_params(self):
        return {"status": "success", "data": {}}

    def get_topology(self):
        return {"status": "success", "data": {}}


from backend import cascor_service_adapter as csa  # noqa: E402
from backend.state_sync import CascorStateSync  # noqa: E402
from communication import websocket_manager as wsm_mod  # noqa: E402
from frontend.components.metrics_panel import MetricsPanel  # noqa: E402


async def drive_ws_relay(frames):
    captured = []

    class FakeTrainingStream:
        def __init__(self, *a, **k):
            pass

        async def connect(self):
            return None

        async def disconnect(self):
            return None

        async def close(self):
            return None

        def stream(self):
            async def gen():
                for f in frames:
                    yield f

            return gen()

    async def capture(message, *a, **k):
        captured.append(message)

    csa.CascorTrainingStream = FakeTrainingStream
    wsm_mod.websocket_manager.broadcast = capture
    adapter = csa.CascorServiceAdapter(service_url="http://127.0.0.1:9", client=FakeClient([]))
    await adapter.start_metrics_relay()
    for _ in range(200):
        if len([c for c in captured if c.get("type") == "metrics"]) >= len(frames):
            break
        await asyncio.sleep(0.01)
    for t in (getattr(adapter, "_relay_task", None), getattr(adapter, "_relay_summary_task", None)):
        if t is not None:
            t.cancel()
    return [c["data"] for c in captured if c.get("type") == "metrics"]


def accuracy_extent(fig):
    tr = fig.data[0]
    pts = [x for x, y in zip(tr.x or (), tr.y or ()) if y is not None]
    xs = [x for t in fig.data for x in (t.x or ()) if x is not None]
    return (min(pts), max(pts), len(pts)) if pts else None, (min(xs), max(xs)) if xs else None


panel = MetricsPanel({}, component_id="lane10a2")
for label, budget, stride, steps, cut in (("mid-pass A", 700, 40, 5, 451), ("mid-pass B", 3000, 25, 2, 1776), ("after run", 700, 40, 5, None)):
    rows, frames = run_monitor(budget, stride, steps, cut)
    client = FakeClient(rows)
    tm = csa._ServiceTrainingMonitor(client)
    rest_rows = tm.get_recent_metrics(count=len(rows))
    current = tm.get_current_metrics()
    ws_rows = asyncio.run(drive_ws_relay(frames))
    synced = CascorStateSync(client).sync(metrics_limit=len(rows)).metrics_history
    print(f"== {label}: budget={budget} stride={stride} steps={steps} cut={cut} rows={len(rows)} frames={len(frames)}; newest raw row kind={rows[-1]['kind']} epoch={rows[-1]['epoch']}; raw rows carry kind: {all('kind' in r for r in rows)}; WS frame data carries kind: {all('kind' in f['data'] for f in frames)}")
    print(f"   kind survives -> REST history: {any('kind' in r for r in rest_rows)} | /api/metrics: {'kind' in current} | WS relay: {any('kind' in r for r in ws_rows)} (relayed {len(ws_rows)}) | state sync: {any('kind' in r for r in synced)}")
    for arm, data in (("REST", rest_rows), ("WS", ws_rows), ("SYNC", synced), ("CONTROL kind restored", [dict(r, kind=o["kind"]) for r, o in zip(rest_rows, rows)])):
        out = panel._update_metrics_display_handler(metrics_data=data)
        acc_pts, acc_axis = accuracy_extent(out[1])
        print(f"   {arm:22} Training Step tile={out[2]!r:8} Accuracy tile={out[4]!r:8} accuracy points (xmin,xmax,n)={acc_pts} x-extent all traces={acc_axis}")
