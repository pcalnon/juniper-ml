#!/usr/bin/env python3
"""
Record what juniper-cascor's HTTP routes answer around a stop, so two trees can be compared answer by answer.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the carrier's claim "the routes answer as before"; tmp/flood4/BRIEF_VALIDATE_R2.txt

Drives the real FastAPI app of the ``--src`` tree through ``TestClient`` with a gated stub ``model.fit``
(events and gates; every wait is bounded; no data service, no candidate pool). It REPORTS: one JSON object
per scenario, each a list of steps with the route's status code and its body, volatile values replaced.
Run it once per tree and compare the two files with
``2026-11-12_flood4r2_val_r17-cascor-claims_diff_probes.py``.

Scenarios:
  restart        start, stop, status, start (the stopped fit still parked), status, then the fit is let go
  refused        start, stop, a start whose candidate-pool triple cannot hold, and one with an out-of-range value
  controls       start, stop, then pause, resume, stop and reset while the stopped fit is parked, then a start
  start_fresh    start, stop, a start-fresh start with a triple that cannot hold: what a late refusal has changed
  snapshot/<verb> a saved snapshot, start, stop, then restore / retrain / resume / replay while the fit is parked

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_http_probe.py --src <cascor src dir> --snapshots <fresh dir> --out <json file>
Exit: 0 when every scenario ran to its end, 1 when one raised.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import traceback
from pathlib import Path

WAIT = 5.0
GATE_TIMEOUT = 20.0
VOLATILE = ("timestamp", "time", "_at", "id", "path", "uuid", "duration", "elapsed", "created", "checksum", "size", "hostname", "pid")


def _scrub(value, key: str = ""):
    """Replace values that differ run to run (times, ids, paths) so two trees' bodies compare."""
    if isinstance(value, dict):
        return {k: _scrub(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, key) for v in value]
    lowered = key.lower()
    if key and any(mark in lowered for mark in VOLATILE) and not isinstance(value, bool) and value is not None:
        return "<volatile>"
    if isinstance(value, float):
        return round(value, 6)
    return value


class _Stack:
    """The real app over HTTP with the model's fit gated, and a list the session counter records into."""

    def __init__(self, modules, checkpoint_after_release: bool = True) -> None:
        self.modules = modules
        self.checkpoint_after_release = checkpoint_after_release
        self.parked = [threading.Event() for _ in range(4)]
        self.release = [threading.Event() for _ in range(4)]
        self.ran_on = [threading.Event() for _ in range(4)]
        self.calls = 0
        self.counted: list = []
        self.steps: list = []
        self._lock = threading.Lock()
        manager_module = modules["manager"]
        self._real_counter = manager_module.inc_training_session_completed
        manager_module.inc_training_session_completed = self.counted.append
        app = modules["create_app"](modules["Settings"](auto_start=False))
        self.client = modules["TestClient"](app)
        self.client.__enter__()
        self.post("create network", "/v1/network", {"input_size": 2, "output_size": 2})
        self.lifecycle = self.client.app.state.lifecycle
        self.lifecycle.model.fit = self._fit

    def _fit(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        event = self.modules["TrainingEvent"]
        with self._lock:
            index = self.calls
            self.calls += 1
        on_event(event("training_start", {"n_samples": int(x.shape[0])}, 0))
        self.parked[index].set()
        self.release[index].wait(timeout=GATE_TIMEOUT)
        if self.checkpoint_after_release:
            on_event(event("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, 1))
        self.ran_on[index].set()
        on_event(event("training_end", {"metrics": {}}, 2))

    def post(self, step: str, url: str, body=None) -> dict:
        response = self.client.post(url, json=body) if body is not None else self.client.post(url)
        return self._record(step, "POST " + url, response)

    def status(self, step: str) -> dict:
        response = self.client.get("/v1/training/status")
        data = response.json().get("data", {})
        record = {
            "step": step,
            "request": "GET /v1/training/status",
            "status_code": response.status_code,
            "training_active": data.get("training_active"),
            "state_machine.status": (data.get("state_machine") or {}).get("status"),
            "training_state.status": (data.get("training_state") or {}).get("status"),
        }
        self.steps.append(record)
        return record

    def _record(self, step: str, request: str, response) -> dict:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        record = {"step": step, "request": request, "status_code": response.status_code, "body": _scrub(body)}
        self.steps.append(record)
        return record

    def note(self, step: str, **facts) -> None:
        self.steps.append({"step": step, **facts})

    def inline(self) -> dict:
        torch = self.modules["torch"]
        x = torch.randn(8, 2)
        y = torch.zeros(8, 2)
        y[:4, 0] = 1
        y[4:, 1] = 1
        return {"train_x": x.tolist(), "train_y": y.tolist()}

    def settle(self, future) -> str:
        try:
            future.result(timeout=WAIT)
            return "returned"
        except TimeoutError:
            return "STILL RUNNING after the bounded wait"
        except Exception as exc:  # a failed fit is a fact to report
            return f"raised {type(exc).__name__}: {exc}"

    def close(self) -> None:
        for gate in self.release:
            gate.set()
        try:
            self.client.__exit__(None, None, None)
        finally:
            self.modules["manager"].inc_training_session_completed = self._real_counter


def _begin(stack: _Stack):
    """Start run 0, wait until its fit is parked between checkpoints, and stop it. Return its future."""
    stack.post("start run 0", "/v1/training/start", {"inline_data": stack.inline()})
    old_future = stack.lifecycle._training_future
    assert stack.parked[0].wait(WAIT), "run 0 never entered its fit"
    stack.post("stop", "/v1/training/stop")
    stack.status("status after the stop")
    return old_future


def _finish(stack: _Stack, old_future, new_future=None) -> None:
    stack.release[0].set()
    stack.note("the stopped fit, let go", outcome=stack.settle(old_future), passed_its_next_checkpoint=stack.ran_on[0].is_set(), counted=list(stack.counted))
    if new_future is not None and new_future is not old_future:
        entered = stack.parked[1].wait(WAIT)
        stack.status("status once the new run is in its fit")
        stack.release[1].set()
        stack.note("the new run", entered_its_fit=entered, outcome=stack.settle(new_future), counted=list(stack.counted))
    stack.status("status at the end")


def scenario_restart(modules) -> list:
    stack = _Stack(modules)
    try:
        old_future = _begin(stack)
        stack.post("start sent while the stopped fit is parked", "/v1/training/start", {"inline_data": stack.inline()})
        stack.status("status after that start")
        _finish(stack, old_future, stack.lifecycle._training_future)
        return stack.steps
    finally:
        stack.close()


def scenario_refused(modules) -> list:
    stack = _Stack(modules)
    try:
        old_future = _begin(stack)
        stack.post("start with selected_candidates 200 (above the pool)", "/v1/training/start", {"inline_data": stack.inline(), "params": {"selected_candidates": 200}})
        stack.post("start with selected_candidates 0 (out of the request model's range)", "/v1/training/start", {"inline_data": stack.inline(), "params": {"selected_candidates": 0}})
        stack.note("after the refusals", run_queued=stack.lifecycle._training_future is not old_future)
        _finish(stack, old_future)
        return stack.steps
    finally:
        stack.close()


def scenario_controls(modules) -> list:
    stack = _Stack(modules)
    try:
        old_future = _begin(stack)
        stack.post("pause while the stopped fit is parked", "/v1/training/pause")
        stack.post("resume while the stopped fit is parked", "/v1/training/resume")
        stack.post("a second stop", "/v1/training/stop")
        stack.post("reset", "/v1/training/reset")
        stack.status("status after the reset")
        stack.post("start after the reset", "/v1/training/start", {"inline_data": stack.inline()})
        _finish(stack, old_future, stack.lifecycle._training_future)
        return stack.steps
    finally:
        stack.close()


def scenario_start_fresh(modules) -> list:
    stack = _Stack(modules)
    try:
        old_future = _begin(stack)
        network_before = stack.lifecycle.network
        train_before = stack.lifecycle._train_x
        gate_before = stack.lifecycle._pause_event.is_set()
        stack.post("start-fresh start with selected_candidates 200", "/v1/training/start", {"inline_data": stack.inline(), "start_fresh": True, "params": {"selected_candidates": 200}})
        stack.note(
            "what the refused start-fresh start left",
            run_queued=stack.lifecycle._training_future is not old_future,
            model_replaced=stack.lifecycle.network is not network_before,
            train_tensors_rebound=stack.lifecycle._train_x is not train_before,
            pause_gate_open_before=gate_before,
            pause_gate_open_after=stack.lifecycle._pause_event.is_set(),
        )
        _finish(stack, old_future)
        return stack.steps
    finally:
        stack.close()


def scenario_snapshot(modules, verb: str) -> list:
    stack = _Stack(modules)
    try:
        saved = stack.client.post("/v1/snapshots")
        snapshot_id = (saved.json().get("data") or {}).get("id")
        stack.note("snapshot saved", status_code=saved.status_code, has_id=bool(snapshot_id))
        old_future = _begin(stack)
        stack.post(f"{verb} while the stopped fit is parked", f"/v1/snapshots/{snapshot_id}/{verb}")
        stack.status(f"status after the {verb}")
        stack.release[0].set()
        stack.note("the stopped fit, let go", outcome=stack.settle(old_future), passed_its_next_checkpoint=stack.ran_on[0].is_set(), counted=list(stack.counted))
        stack.status("status at the end")
        if verb == "replay":
            stack.post("replay control stop", f"/v1/snapshots/{snapshot_id}/replay/control", {"action": "stop"})
        return stack.steps
    finally:
        stack.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--snapshots", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    snapshots = args.snapshots.resolve()
    snapshots.mkdir(parents=True, exist_ok=True)
    os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = str(snapshots)
    os.environ.pop("JUNIPER_CASCOR_LOG_DIR", None)
    sys.path.insert(0, str(args.src.resolve()))

    import torch
    from fastapi.testclient import TestClient
    from juniper_model_core.events import TrainingEvent

    from api.app import create_app
    from api.lifecycle import manager as manager_module
    from api.settings import Settings

    modules = {"torch": torch, "TestClient": TestClient, "TrainingEvent": TrainingEvent, "create_app": create_app, "manager": manager_module, "Settings": Settings}
    jobs = [
        ("restart", lambda: scenario_restart(modules)),
        ("refused", lambda: scenario_refused(modules)),
        ("controls", lambda: scenario_controls(modules)),
        ("start_fresh", lambda: scenario_start_fresh(modules)),
    ]
    for verb in ("restore", "retrain", "resume", "replay"):
        jobs.append((f"snapshot/{verb}", lambda verb=verb: scenario_snapshot(modules, verb)))
    reports = [{"name": "provenance", "manager_under_test": manager_module.__file__, "python": sys.version.split()[0]}]
    failed = False
    for name, job in jobs:
        try:
            report = {"name": name, "steps": job()}
        except Exception:  # report the scenario that broke and carry on with the rest
            failed = True
            report = {"name": name, "probe_error": traceback.format_exc()}
        reports.append(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scenarios": len(jobs), "failed": failed, "out": str(args.out)}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
