# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_o2_initial_burst.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Does canopy's relay (1b2dd438) forward cascor's on-connect initial_metrics burst with ``kind``?
Rows from cascor's REAL TrainingMonitor; frame from cascor's REAL create_initial_metrics_message;
relay driven as in my_o2.py (fake training stream, captured broadcast)."""
import asyncio
import importlib.util
import os
import sys

CANOPY_SRC, CASCOR_SRC = sys.argv[1], sys.argv[2]
sys.path.insert(0, CANOPY_SRC)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mon = load("cascor_monitor_pin", f"{CASCOR_SRC}/api/lifecycle/monitor.py")
msgs = load("cascor_messages_pin", f"{CASCOR_SRC}/api/websocket/messages.py")
m = mon.TrainingMonitor()
for inner in (1, 26, 51):
    m.on_epoch_end(epoch=inner, loss=0.5, accuracy=None, learning_rate=0.1, hidden_units=0, kind="output_epoch")
m.on_epoch_end(epoch=1, loss=0.4, accuracy=0.7, learning_rate=0.1, hidden_units=0, kind="training_step")
burst = msgs.create_initial_metrics_message(m.get_all_metrics(), current_seq=0)
live = msgs.create_metrics_message(m.get_all_metrics()[-1])

from backend import cascor_service_adapter as csa  # noqa: E402
from communication import websocket_manager as wsm_mod  # noqa: E402

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
            yield burst
            yield live

        return gen()


async def capture(message, *a, **k):
    captured.append(message)


async def main():
    csa.CascorTrainingStream = FakeTrainingStream
    wsm_mod.websocket_manager.broadcast = capture
    a = csa.CascorServiceAdapter(service_url="http://127.0.0.1:9", client=object())
    async def _noop(*x, **k):
        return None

    a._control_supervisor.start = _noop  # keep the control leg from dialling out
    await a.start_metrics_relay()
    for _ in range(200):
        if len(captured) >= 2:
            break
        await asyncio.sleep(0.01)
    for t in (getattr(a, "_relay_task", None), getattr(a, "_relay_summary_task", None)):
        if t is not None:
            t.cancel()


asyncio.run(main())
for c in captured[:2]:
    d = c.get("data")
    if c.get("type") == "initial_metrics":
        rows = d.get("metrics", [])
        print(f"broadcast type=initial_metrics rows={len(rows)} kinds={[r.get('kind') for r in rows]} row keys={sorted(rows[0])[:6]}... has nested 'metrics': {'metrics' in rows[0]}")
    else:
        print(f"broadcast type={c.get('type')} keys={sorted(d)} kind present: {'kind' in d}")
