"""
Over juniper-cascor's real HTTP routes: stop, start (queued behind the stopped fit), restore a snapshot, then try to stop the run that begins.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17, "cascor: stop-then-start")

Usage: <JuniperCascor1 python> <this> <juniper-cascor tree> <out.json> <snapshot scratch dir>

The lifecycle-level probe (..._interleavings.py, c2 and c3) showed a queued run entering under
INVESTIGATING. This repeats it through ``create_app`` and a ``TestClient`` so the HTTP status codes are
measured, not read off the route table. The fit is a gated stub; every wait is bounded; snapshots go to
the scratch directory given.
"""

import json
import sys
import threading
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
SNAP_DIR = Path(sys.argv[3]).resolve()
sys.path.insert(0, str(TREE / "src"))

import torch  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from juniper_model_core.events import TrainingEvent  # noqa: E402

from api.app import create_app  # noqa: E402
from api.lifecycle import manager as manager_module  # noqa: E402
from api.settings import Settings  # noqa: E402

WAIT = 8.0


class Gate:
    def __init__(self) -> None:
        self.parked = threading.Event()
        self.release = threading.Event()
        self.ran_on = threading.Event()


class GatedFit:
    def __init__(self) -> None:
        self.gates = [Gate(), Gate(), Gate()]
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        with self._lock:
            gate = self.gates[self.calls]
            self.calls += 1
        on_event(TrainingEvent("training_start", {"n_samples": 8}, 0))
        gate.parked.set()
        gate.release.wait(timeout=20.0)
        on_event(TrainingEvent("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, 1))
        gate.ran_on.set()
        on_event(TrainingEvent("training_end", {"metrics": {}}, 2))


def main() -> int:
    module_file = Path(manager_module.__file__).resolve()
    if TREE not in module_file.parents:
        print(f"PROVENANCE FAILURE: imported {module_file}")
        return 2
    out = {"_provenance": str(module_file)}
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    x = torch.randn(8, 2)
    y = torch.zeros(8, 2)
    y[:4, 0] = 1
    y[4:, 1] = 1
    payload = {"inline_data": {"train_x": x.tolist(), "train_y": y.tolist()}}
    fit = GatedFit()
    with TestClient(create_app(Settings(auto_start=False))) as client:
        lifecycle = client.app.state.lifecycle
        lifecycle._get_snapshots_dir = lambda: SNAP_DIR
        try:
            out["create_network"] = client.post("/v1/network", json={"input_size": 2, "output_size": 2}).status_code
            lifecycle.model.fit = fit
            saved = client.post("/v1/snapshots", json={"description": "probe http"})
            out["save_snapshot"] = saved.status_code
            snapshot_id = saved.json()["data"]["id"]
            out["start_a"] = client.post("/v1/training/start", json=payload).status_code
            future_a = lifecycle._training_future
            out["a_parked"] = fit.gates[0].parked.wait(timeout=WAIT)
            out["restore_while_training"] = client.post(f"/v1/snapshots/{snapshot_id}/restore").status_code
            out["stop"] = client.post("/v1/training/stop").status_code
            out["start_b_after_stop"] = client.post("/v1/training/start", json=payload).status_code
            future_b = lifecycle._training_future
            status = client.get("/v1/training/status").json()["data"]
            out["status_after_start_b"] = [status["state_machine"]["status"], status["training_active"], status["training_state"].get("status")]
            out["restore_with_a_run_queued"] = client.post(f"/v1/snapshots/{snapshot_id}/restore").status_code
            lifecycle.model.fit = fit  # the restore installed a new model; keep the queued run's fit gated
            fit.gates[0].release.set()
            future_a.result(timeout=WAIT)
            out["old_fit_ran_on_past_its_checkpoint"] = fit.gates[0].ran_on.is_set()
            out["b_fit_began"] = fit.gates[1].parked.wait(timeout=WAIT)
            status = client.get("/v1/training/status").json()["data"]
            out["status_while_b_trains"] = [status["state_machine"]["status"], status["training_active"], status["training_state"].get("status")]
            stop = client.post("/v1/training/stop")
            out["stop_while_b_trains"] = [stop.status_code, stop.text[:160]]
            out["pause_while_b_trains"] = client.post("/v1/training/pause").status_code
            out["start_while_b_trains"] = client.post("/v1/training/start", json=payload).status_code
            out["reset_while_b_trains"] = client.post("/v1/training/reset").status_code
            fit.gates[1].release.set()
            future_b.result(timeout=WAIT)
            out["b_ran_on_past_its_checkpoint_after_reset"] = fit.gates[1].ran_on.is_set()
            status = client.get("/v1/training/status").json()["data"]
            out["status_final"] = [status["state_machine"]["status"], status["training_active"], status["training_state"].get("status")]
        finally:
            for gate in fit.gates:
                gate.release.set()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
