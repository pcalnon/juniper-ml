# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the idle cuts' round 1, Lane B: the Stop probe behind F-CANOPY-056.
# Source: session 259b4d16's tmpfs scratchpad, laneB_probe_stop.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane B review probe (read-only): drive dispatch_control('stop') with the proxy's real 200 body, then feed the result to render_session and the gate JS."""

import json
import os
import shutil
import subprocess
import sys
from unittest import mock

SRC = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad/laneB_extract/src"
os.chdir(SRC)
sys.path.insert(0, SRC)
os.environ["JUNIPER_CANOPY_DEMO_MODE"] = "1"

from frontend.components import replay_player_panel as rpp  # noqa: E402


class _App:
    def callback(self, *a, **k):
        return lambda f: f

    def clientside_callback(self, *a, **k):
        pass


panel = rpp.ReplayPlayerPanel({})
panel.register_callbacks(_App())

session = {"snapshot_id": "snap_1", "fsm_state": "REPLAYING", "speed": 1.0, "playing": True, "time_index": {"current": 5, "snapshot_window": {"start_epoch": 0, "end_epoch": 9}}}
# canopy route returns CascorClient._post's full envelope verbatim; cascor's stop payload per routes/snapshots.py
body = {"status": "success", "data": {"snapshot_id": "snap_1", "operation": "replay_control", "action": "stop", "result": {"status": "stopped", "snapshot_id": "snap_1"}, "fsm_state": "STOPPED"}, "meta": {}}
resp = mock.Mock(status_code=200, text=json.dumps(body))
resp.json.return_value = body
with mock.patch.object(rpp.requests, "post", return_value=resp), mock.patch.object(rpp.dash, "callback_context", mock.Mock(triggered=[{"prop_id": "x.data"}])):
    status, new_session = panel._cb_dispatch_control({"action": "stop", "ts": 1}, session)
print("session after a successful Stop:", {k: new_session.get(k) for k in ("snapshot_id", "fsm_state", "status")})
rendered = panel._cb_render_session(new_session)
print("render_session after Stop -> idle.style:", rendered[0], "active.style:", rendered[1], "fsm badge:", rendered[3])

node = shutil.which("node")
driver = "const fn = (" + rpp.WEIGHT_DRAIN_GATE_JS + "); console.log(JSON.stringify(fn(JSON.parse(process.argv[1]))));"
proc = subprocess.run([node, "-e", driver, json.dumps(new_session)], capture_output=True, text=True, timeout=60, check=False)  # nosec B603
print("gate(disabled) after Stop:", proc.stdout.strip(), proc.stderr.strip())
