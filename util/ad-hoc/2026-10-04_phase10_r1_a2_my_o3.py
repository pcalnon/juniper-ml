# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_o3.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-A2 independent reproduction of F-CANOPY-065: drive canopy's REAL apply_params (1b2dd438),
not a re-implementation of its merge.

  WS leg   : a stand-in control supervisor whose set_params returns the frame cascor's REAL
             create_control_ack_message (95cdc562) builds -- the WHOLE frame, which is what
             cascor-client's recv loop resolves (ws_client.py:822, 3adc061f and the installed 0.8.0).
  REST leg : a stand-in client whose update_params returns cascor's REST envelope
             (success_response(update_params(...)): {"status","data":{echo..., applied, skipped},"meta"}).
  Partition: computed by cascor's rule (_apply_params_unlocked: a key outside updatable_keys is
             skipped not-updatable -- epochs_max since C2b).
Request: the A-N2 caps, as the driver posted them to /api/set_params.

Usage: python my_o3.py <canopy src> <cascor src>
"""
import asyncio
import importlib.util
import logging
import os
import sys
import threading

CANOPY_SRC, CASCOR_SRC = sys.argv[1], sys.argv[2]
sys.path.insert(0, CANOPY_SRC)
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


msg_mod = load("cascor_messages_pin", f"{CASCOR_SRC}/api/websocket/messages.py")

UPDATABLE = {"learning_rate", "candidate_learning_rate", "correlation_threshold", "candidate_pool_size", "max_hidden_units", "max_iterations", "patience", "convergence_threshold", "candidate_convergence_threshold", "candidate_patience", "candidate_epochs", "output_epochs", "init_output_weights", "optimizer_type", "activation_function_name"}
LIVE = {"max_iterations": 8, "output_epochs": 60, "candidate_epochs": 40, "max_hidden_units": 32, "learning_rate": 0.1}


def cascor_update_params(params):
    applied = [k for k in params if k in UPDATABLE]
    skipped = [{"key": k, "reason": "not-updatable"} for k in params if k not in UPDATABLE]
    echo = dict(LIVE, epochs_max=860)
    echo.update({"applied": applied, "skipped": skipped})
    return echo


class FakeRest:
    def update_params(self, params):
        return {"status": "success", "data": cascor_update_params(params), "meta": {"timestamp": 0.0, "version": "x"}}

    def get_training_params(self):
        return {"status": "success", "data": dict(LIVE, epochs_max=860), "meta": {}}


class FakeSupervisor:
    def __init__(self, unwrap=False):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.is_connected = True
        self.unwrap = unwrap

    async def set_params(self, params, *, timeout=1.0):
        frame = msg_mod.create_control_ack_message("set_params", "success", data=cascor_update_params(params), command_id="cid-x")
        return frame["data"]["result"] if self.unwrap else frame


logging.basicConfig(level=logging.INFO, format="   log: %(message)s")
from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402

REQUEST = {"nn_max_iterations": 8, "nn_output_epochs": 60, "nn_max_total_epochs": 60, "cn_training_iterations": 40, "nn_max_hidden_units": 32}
frame = msg_mod.create_control_ack_message("set_params", "success", data=cascor_update_params({"max_iterations": 8}), command_id="cid-x")
print("real cascor ack frame keys:", sorted(frame), "| data keys:", sorted(frame["data"]), "| partition at data.result:", "applied" in frame["data"]["result"])
for label, unwrap in (("as canopy receives it (whole frame)", False), ("CONTROL: supervisor returns data.result (unwrapped)", True)):
    a = CascorServiceAdapter(service_url="http://127.0.0.1:9", client=FakeRest())
    a._control_supervisor = FakeSupervisor(unwrap=unwrap)
    out = a.apply_params(**REQUEST)
    print(f"== {label}: ok={out.get('ok')} applied={out.get('applied')} skipped_detail={out.get('skipped_detail')}")
