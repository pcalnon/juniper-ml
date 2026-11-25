"""
Reproduce flood-4 ruling 23's "Lifecycle races beside N-2" on a juniper-service-core tree, in process.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23l: re-verify both defects on main, then show the fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 11, 19, 23);
         juniper-ml#2557 (N-2, the start refusal this extends)

Defect 1, STOP-THEN-LOAD. After a stop, while the stopped run's ``fit`` is still running, each of
``load_snapshot``, ``resume_from_snapshot``, ``start_replay``, ``restore_for_retrain`` and ``attach_model`` is
tried; then the stopped ``fit`` ends one of three ways (``unwind``: its next event sees the stop; ``raise``: it
raises instead; ``inflight``: an event that was already inside the sink when the stop landed is released). A row
records whether the load was accepted, the state right after it, and the state once that ``fit`` has ended.

Defect 2, A LEFTOVER REPLAY SESSION. A replay is started, then left by a load (retrain, resume, restore) or by
attach / reset / a start; the row records whether the session survived, whether a run could start beside it,
and what the session's ``stop`` (and ``stop_replay()``) then did to a running run. Also: a leftover session's
``seek`` pushing a replay frame into the live frame sink during a run.

Both are driven in process on the manager, through the HTTP routes (FastAPI TestClient), and through
``/ws/control`` (TestClient websocket; its executor reaches start/stop/reset only, and the probe shows that).
Every wait is an Event with a deadline; nothing sleeps. The probe reports; ``defect_seen`` is a per-row
predicate stated in the row. Which tree it measures is whatever ``juniper_service_core`` the interpreter
imports: the row header records that file and the sha256 of its ``lifecycle/manager.py``.

Usage: python <this file> --scratch DIR --json-out FILE [--label LABEL]
Exit: 0 when every row ran (whatever it saw); 2 on a setup error (a row that could not run to its end).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from fastapi.testclient import TestClient
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainableModel, TrainResult
from juniper_model_core.serialization import ModelSerializer

import juniper_service_core
from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager, TrainingInterrupted
from juniper_service_core.lifecycle import manager as manager_module
from juniper_service_core.lifecycle.monitor import LifecycleMonitor
from juniper_service_core.routes import build_routers
from juniper_service_core.websocket import LifecycleCommandExecutor, WebSocketManager, attach_websocket, build_websocket_router

WAIT = 5.0
PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}
COMPLETE = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))


class SetupError(Exception):
    """A row could not run as designed."""


class FitCounter:
    """Counts the ``fit`` calls running at once across every model of one row."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = 0
        self.peak = 0
        self.calls = 0

    def enter(self) -> int:
        with self._lock:
            self.calls += 1
            self.running += 1
            self.peak = max(self.peak, self.running)
            return self.calls

    def leave(self) -> None:
        with self._lock:
            self.running -= 1


class ScriptedModel(TrainableModel):
    """``fit`` call n follows ``scripts[n-1]``: ("emit", type), ("gate", name) parks until opened, ("raise", msg)."""

    def __init__(self, counter: FitCounter, *scripts: tuple[tuple[str, str], ...]) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.counter = counter
        self.scripts = scripts
        self.fits = 0
        self.threads: list[threading.Thread] = []
        self.interrupted: list[int] = []
        self.gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def gate(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self.gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str) -> bool:
        return self.gate(name)[1].wait(WAIT)

    def open(self, name: str) -> None:
        self.gate(name)[0].set()

    def open_all(self) -> None:
        with self._lock:
            gates = [g for g, _ in self.gates.values()]
        for g in gates:
            g.set()

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with self._lock:
            self.fits += 1
            call = self.fits
            self.threads.append(threading.current_thread())
        script = self.scripts[call - 1] if call <= len(self.scripts) else ()
        self.counter.enter()
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(PAYLOADS[arg]), 0))
                elif kind == "gate":
                    opened, reached = self.gate(arg)
                    reached.set()
                    opened.wait(WAIT * 2)
                elif kind == "raise":
                    raise RuntimeError(arg)
        except TrainingInterrupted:
            self.interrupted.append(call)
            raise
        finally:
            self.counter.leave()
        return TrainResult(final_metrics={"mse": 0.25}, n_epochs=1)

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], 1))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.25}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "scripted", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return (2,)

    @property
    def output_shape(self) -> tuple[int, ...]:
        return (1,)


class QueueSerializer(ModelSerializer):
    """Writes nothing; each ``load`` hands back the next model the probe queued (then a fresh no-op model)."""

    def __init__(self, counter: FitCounter, *models: ScriptedModel) -> None:
        self.counter = counter
        self.queue = list(models)
        self.handed: list[ScriptedModel] = []

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        model = self.queue.pop(0) if self.queue else ScriptedModel(self.counter)
        self.handed.append(model)
        return model


class HoldingMonitor(LifecycleMonitor):
    """Once armed, holds the first ``hold_type`` event inside ``on_event`` (before it is folded) until released."""

    def __init__(self, hold_type: str) -> None:
        super().__init__()
        self.hold_type = hold_type
        self.armed = False
        self.inside = threading.Event()
        self.release = threading.Event()

    def on_event(self, event: TrainingEvent) -> None:
        if self.armed and event.type == self.hold_type and not self.inside.is_set():
            self.inside.set()
            self.release.wait(WAIT * 2)
        super().on_event(event)


def _xy(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


def _state(mgr: ServiceLifecycleManager) -> dict[str, Any]:
    status = mgr.get_status()
    return {
        "fsm": status["state_machine"]["status"],
        "monitor": status["monitor"]["status"],
        "history": len(mgr.get_metrics_history()),
        "error": status.get("error"),
        "training_active": status["training_active"],
        "replay_session": mgr.get_replay_state() is not None,
    }


def _try(fn, *args, **kwargs) -> tuple[str, Any]:
    try:
        return "accepted", fn(*args, **kwargs)
    except (RuntimeError, ValueError) as exc:
        return f"refused: {exc}", None


def _join(threads: list[threading.Thread]) -> bool:
    for thread in threads:
        thread.join(WAIT)
    return not any(t.is_alive() for t in threads)


# ---------------------------------------------------------------------------------------------- defect 1


def defect1_row(scratch: Path, op: str, ending: str) -> dict[str, Any]:
    """Stop a run while its fit is still running, try ``op``, then let that fit end by ``ending``."""
    counter = FitCounter()
    if ending == "unwind":
        second = (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("emit", "training_end"))
    elif ending == "raise":
        second = (("emit", "training_start"), ("gate", "old"), ("raise", "boom"))
    else:  # inflight: the epoch_end is held inside the sink's fold when the stop lands
        second = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
    model = ScriptedModel(counter, COMPLETE, second)
    serializer = QueueSerializer(counter)
    mgr = ServiceLifecycleManager(model, serializer=serializer, snapshot_dir=scratch / f"d1-{op}-{ending}")
    holding = HoldingMonitor("epoch_end")
    mgr.monitor = holding
    row: dict[str, Any] = {"row": f"D1 {op} after a stop, then the stopped fit ends by {ending}", "op": op, "ending": ending}
    try:
        mgr.start_training(*_xy(), dataset_name="first")
        if not mgr.join(WAIT):
            raise SetupError("the first run did not complete")
        snapshot_id = mgr.save_snapshot()["id"]
        row["snapshot_history"] = len(mgr.get_metrics_history())
        holding.armed = ending == "inflight"
        mgr.start_training(*_xy(), dataset_name="stopped-run")
        if ending == "inflight":
            if not holding.inside.wait(WAIT):
                raise SetupError("the stopped run's epoch_end never reached the sink")
        elif not model.reached("old"):
            raise SetupError("the stopped run's fit never parked")
        mgr.stop_training()
        stopped_thread = model.threads[1]
        row["stopped_fit_alive_at_op"] = stopped_thread.is_alive()
        if op == "attach_model":
            outcome, _ = _try(mgr.attach_model, ScriptedModel(counter))
        else:
            outcome, _ = _try(getattr(mgr, op), snapshot_id)
        row["op_outcome"] = outcome
        row["after_op"] = _state(mgr)
        holding.release.set()
        model.open("old")
        if not _join([stopped_thread]):
            raise SetupError("the stopped run's thread did not end")
        row["after_the_stopped_fit_ended"] = _state(mgr)
        row["peak_fits_at_once"] = counter.peak
        accepted = outcome == "accepted"
        a, b = row["after_op"], row["after_the_stopped_fit_ended"]
        row["defect_seen_predicate"] = "the op was accepted while the stopped fit ran, and that fit's end then changed the loaded state (monitor status, history length or error)"
        row["defect_seen"] = accepted and (a["monitor"] != b["monitor"] or a["history"] != b["history"] or a["error"] != b["error"])
        if not accepted:
            # With the op refused, the same op once the stopped fit has ended must stand (the refusal is transient).
            if op == "attach_model":
                again, _ = _try(mgr.attach_model, ScriptedModel(counter))
            else:
                again, _ = _try(getattr(mgr, op), snapshot_id)
            row["op_once_the_stopped_fit_ended"] = again
            row["after_the_retried_op"] = _state(mgr)
    finally:
        holding.release.set()
        model.open_all()
        mgr.shutdown()
        _join(model.threads)
    return row


# ---------------------------------------------------------------------------------------------- defect 2


def defect2_leftover_row(scratch: Path, leave_by: str) -> dict[str, Any]:
    """Start a replay, leave it by ``leave_by``, start a run if the state allows, then send the replay ``stop``."""
    counter = FitCounter()
    first = ScriptedModel(counter, COMPLETE)
    replay_model = ScriptedModel(counter)
    run_model = ScriptedModel(counter, (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end")), (("emit", "training_start"), ("gate", "second"), ("emit", "epoch_end")))
    serializer = QueueSerializer(counter, replay_model, run_model)
    mgr = ServiceLifecycleManager(first, serializer=serializer, snapshot_dir=scratch / f"d2-{leave_by}")
    row: dict[str, Any] = {"row": f"D2 a replay left by {leave_by}, then the session's stop", "leave_by": leave_by}
    try:
        mgr.start_training(*_xy())
        if not mgr.join(WAIT):
            raise SetupError("the first run did not complete")
        snapshot_id = mgr.save_snapshot()["id"]
        mgr.start_replay(snapshot_id)
        row["after_start_replay"] = _state(mgr)
        if leave_by == "attach_model":
            outcome, _ = _try(mgr.attach_model, run_model)
        elif leave_by == "reset":
            outcome, _ = _try(mgr.reset)
        elif leave_by == "start_training":
            outcome, _ = _try(mgr.start_training, *_xy())
        else:
            outcome, _ = _try(getattr(mgr, leave_by), snapshot_id)
        row["leave_outcome"] = outcome
        row["after_leaving"] = _state(mgr)
        row["session_survived"] = row["after_leaving"]["replay_session"] and row["after_leaving"]["fsm"] != "REPLAYING"
        start_outcome, _ = _try(mgr.start_training, *_xy())
        row["start_after_leaving"] = start_outcome
        # Only run_model's fit parks; after a reset the current model is the replay's, whose fit returns at once.
        run_started = start_outcome == "accepted" and mgr.model is run_model and run_model.reached("run")
        row["run_fit_running"] = bool(run_started)
        stop_outcome, _ = _try(mgr.replay_control, "stop")
        row["replay_stop_outcome"] = stop_outcome
        row["after_replay_stop"] = _state(mgr)
        row["stop_event_set_after_replay_stop"] = mgr._stop_event.is_set()
        run_alive = bool(run_started and run_model.threads and run_model.threads[0].is_alive())
        row["run_fit_alive_after_replay_stop"] = run_alive
        second_outcome, _ = _try(mgr.start_training, *_xy())
        row["second_start"] = second_outcome
        beside = second_outcome == "accepted" and run_alive and run_model.threads[0].is_alive()
        row["second_start_accepted_beside_the_running_fit"] = beside
        if beside:
            run_model.reached("second")
        row["peak_fits_at_once"] = counter.peak
        row["defect_seen_predicate"] = "the session outlived REPLAYING and its stop RESET the machine while a run's fit was running (or a second start was accepted beside that fit); for load_snapshot: the stop moved INVESTIGATING to STOPPED"
        reset_a_run = run_started and stop_outcome == "accepted" and row["after_replay_stop"]["fsm"] == "STOPPED" and run_alive
        left_investigation = leave_by == "load_snapshot" and stop_outcome == "accepted" and row["after_leaving"]["fsm"] == "INVESTIGATING" and row["after_replay_stop"]["fsm"] == "STOPPED"
        row["defect_seen"] = bool(reset_a_run or beside or left_investigation)
    finally:
        for m in (first, replay_model, run_model):
            m.open_all()
        mgr.shutdown()
        _join(first.threads + run_model.threads)
    return row


def defect2_stop_replay_during_run(scratch: Path) -> dict[str, Any]:
    """``stop_replay()`` with no replay at all, while a run is training."""
    counter = FitCounter()
    model = ScriptedModel(counter, (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end")))
    mgr = ServiceLifecycleManager(model)
    row: dict[str, Any] = {"row": "D2 stop_replay() while a run is training (no replay session)"}
    try:
        mgr.start_training(*_xy())
        if not model.reached("run"):
            raise SetupError("the run never parked")
        row["before"] = _state(mgr)
        outcome, _ = _try(mgr.stop_replay)
        row["stop_replay_outcome"] = outcome
        row["after"] = _state(mgr)
        row["defect_seen_predicate"] = "stop_replay relabelled a running run's monitor (status no longer 'running' while the machine reads STARTED)"
        row["defect_seen"] = row["after"]["fsm"] == "STARTED" and row["after"]["monitor"] != row["before"]["monitor"]
    finally:
        model.open_all()
        mgr.shutdown()
        _join(model.threads)
    return row


def defect2_frames_during_run(scratch: Path) -> dict[str, Any]:
    """A session left by a retrain, then a run, then the session's ``seek``: does a replay frame reach the live sink?"""
    counter = FitCounter()
    first = ScriptedModel(counter, COMPLETE)
    run_model = ScriptedModel(counter, (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end")))
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(counter, ScriptedModel(counter), run_model), snapshot_dir=scratch / "d2-frames")
    frames: list[dict[str, Any]] = []
    row: dict[str, Any] = {"row": "D2 a leftover session's seek during a run, with a live frame sink"}
    try:
        mgr.start_training(*_xy())
        if not mgr.join(WAIT):
            raise SetupError("the first run did not complete")
        snapshot_id = mgr.save_snapshot()["id"]
        mgr.start_replay(snapshot_id)
        mgr.restore_for_retrain(snapshot_id)
        mgr.start_training(*_xy())
        if not run_model.reached("run"):
            raise SetupError("the run never parked")
        mgr.set_frame_sink(frames.append)
        outcome, _ = _try(mgr.replay_control, "seek", time_index=0)
        row["seek_outcome"] = outcome
        row["fsm_during"] = mgr.get_status()["state_machine"]["status"]
        row["replay_frames_in_the_live_sink"] = sum(1 for f in frames if (f.get("data") or {}).get("replay") is True)
        row["defect_seen_predicate"] = "a replay frame reached the live frame sink while a run was STARTED"
        row["defect_seen"] = row["fsm_during"] == "STARTED" and row["replay_frames_in_the_live_sink"] > 0
    finally:
        mgr.set_frame_sink(None)
        first.open_all()
        run_model.open_all()
        mgr.shutdown()
        _join(first.threads + run_model.threads)
    return row


# ---------------------------------------------------------------------------------------------- HTTP and /ws/control


def _app(mgr: ServiceLifecycleManager, *, control_start=None):
    app = create_app(title="r23l-probe", version="0.0.0", routers=[*build_routers(), build_websocket_router()])
    executor = LifecycleCommandExecutor(mgr, start=control_start) if control_start is not None else None
    attach_websocket(app, manager=mgr, ws_manager=WebSocketManager(), command_executor=executor)
    return app


def _payload() -> dict[str, Any]:
    X, y = _xy()
    return {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}


def http_defect1_row(scratch: Path, route: str, ending: str) -> dict[str, Any]:
    counter = FitCounter()
    if ending == "raise":
        second = (("emit", "training_start"), ("gate", "old"), ("raise", "boom"))
    else:
        second = (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("emit", "training_end"))
    model = ScriptedModel(counter, COMPLETE, second)
    mgr = ServiceLifecycleManager(model, serializer=QueueSerializer(counter), snapshot_dir=scratch / f"h1-{route}-{ending}")
    row: dict[str, Any] = {"row": f"HTTP D1 POST /v1/snapshots/{{id}}/{route} after POST /v1/training/stop, the stopped fit ends by {ending}"}
    try:
        with TestClient(_app(mgr)) as client:
            if client.post("/v1/training/start", json=_payload()).status_code != 200 or not mgr.join(WAIT):
                raise SetupError("the first run did not complete")
            snapshot_id = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            if client.post("/v1/training/start", json=_payload()).status_code != 200 or not model.reached("old"):
                raise SetupError("the second run never parked")
            row["stop_status"] = client.post("/v1/training/stop").status_code
            response = client.post(f"/v1/snapshots/{snapshot_id}/{route}")
            row["load_status"] = response.status_code
            row["load_detail"] = response.json().get("detail") if response.status_code != 200 else None
            after_load = client.get("/v1/training/status").json()["data"]
            row["after_load"] = {"fsm": after_load["state_machine"]["status"], "monitor": after_load["monitor"]["status"], "error": after_load.get("error")}
            model.open("old")
            if not _join([model.threads[1]]):
                raise SetupError("the stopped run's thread did not end")
            final = client.get("/v1/training/status").json()["data"]
            row["after_the_stopped_fit_ended"] = {"fsm": final["state_machine"]["status"], "monitor": final["monitor"]["status"], "error": final.get("error")}
            row["defect_seen_predicate"] = "the load was a 200 while the stopped fit ran, and GET /v1/training/status changed once that fit ended"
            row["defect_seen"] = response.status_code == 200 and row["after_load"] != row["after_the_stopped_fit_ended"]
    finally:
        model.open_all()
        mgr.shutdown()
        _join(model.threads)
    return row


def http_defect2_row(scratch: Path) -> dict[str, Any]:
    counter = FitCounter()
    first = ScriptedModel(counter, COMPLETE)
    run_model = ScriptedModel(counter, (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end")), (("emit", "training_start"), ("gate", "second"), ("emit", "epoch_end")))
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(counter, ScriptedModel(counter), run_model), snapshot_dir=scratch / "h2")
    row: dict[str, Any] = {"row": "HTTP D2 POST /replay, POST /retrain, POST /v1/training/start, POST /replay/control stop, POST /v1/training/start"}
    try:
        with TestClient(_app(mgr)) as client:
            if client.post("/v1/training/start", json=_payload()).status_code != 200 or not mgr.join(WAIT):
                raise SetupError("the first run did not complete")
            snapshot_id = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            row["replay"] = client.post(f"/v1/snapshots/{snapshot_id}/replay").status_code
            row["retrain"] = client.post(f"/v1/snapshots/{snapshot_id}/retrain").status_code
            row["start"] = client.post("/v1/training/start", json=_payload()).status_code
            if row["start"] != 200 or not run_model.reached("run"):
                raise SetupError("the run never parked")
            stop = client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "stop"})
            row["replay_stop_status"] = stop.status_code
            row["replay_stop_body"] = stop.json().get("data", {}).get("state_machine") if stop.status_code == 200 else stop.json().get("detail")
            status = client.get("/v1/training/status").json()["data"]
            row["status_after_replay_stop"] = {"fsm": status["state_machine"]["status"], "monitor": status["monitor"]["status"], "training_active": status["training_active"]}
            row["run_fit_alive"] = run_model.threads[0].is_alive()
            second = client.post("/v1/training/start", json=_payload())
            row["second_start_status"] = second.status_code
            row["second_start_detail"] = second.json().get("detail") if second.status_code != 200 else None
            if second.status_code == 200:
                run_model.reached("second")
            row["peak_fits_at_once"] = counter.peak
            row["defect_seen_predicate"] = "the replay stop was a 200 that left the machine STOPPED while the run's fit ran, or the second start was a 200"
            row["defect_seen"] = (stop.status_code == 200 and row["status_after_replay_stop"]["fsm"] == "STOPPED" and row["run_fit_alive"]) or second.status_code == 200
    finally:
        first.open_all()
        run_model.open_all()
        mgr.shutdown()
        _join(first.threads + run_model.threads)
    return row


def ws_control_row(scratch: Path) -> dict[str, Any]:
    """Starts over /ws/control, the replay stop over HTTP; and whether /ws/control knows any replay or load command."""
    counter = FitCounter()
    first = ScriptedModel(counter, COMPLETE)
    run_model = ScriptedModel(counter, (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end")), (("emit", "training_start"), ("gate", "second"), ("emit", "epoch_end")))
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(counter, ScriptedModel(counter), run_model), snapshot_dir=scratch / "ws")
    row: dict[str, Any] = {"row": "/ws/control D2: replay over HTTP, retrain over HTTP, start over /ws/control, replay stop over HTTP, start over /ws/control"}
    try:
        app = _app(mgr, control_start=lambda params: mgr.start_training(*_xy()))
        with TestClient(app) as client:
            if client.post("/v1/training/start", json=_payload()).status_code != 200 or not mgr.join(WAIT):
                raise SetupError("the first run did not complete")
            snapshot_id = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            row["replay"] = client.post(f"/v1/snapshots/{snapshot_id}/replay").status_code
            row["retrain"] = client.post(f"/v1/snapshots/{snapshot_id}/retrain").status_code
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()  # connection_established
                unknown = {}
                for command in ("replay", "replay_control", "stop_replay", "restore", "retrain", "resume", "load_snapshot", "attach_model"):
                    ws.send_json({"command": command})
                    ack = ws.receive_json()["data"]
                    unknown[command] = ack.get("code") or ack.get("status")
                row["ws_unknown_commands"] = unknown
                ws.send_json({"command": "start", "command_id": "s1"})
                row["ws_start_ack"] = ws.receive_json()["data"]["status"]
                if not run_model.reached("run"):
                    raise SetupError("the run never parked")
                stop = client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "stop"})
                row["http_replay_stop_status"] = stop.status_code
                row["fsm_after_replay_stop"] = mgr.get_status()["state_machine"]["status"]
                row["run_fit_alive"] = run_model.threads[0].is_alive()
                ws.send_json({"command": "start", "command_id": "s2"})
                ack = ws.receive_json()["data"]
                row["ws_second_start_ack"] = ack["status"] if ack["status"] == "success" else f"{ack['status']}: {ack.get('error')}"
                if ack["status"] == "success":
                    run_model.reached("second")
                row["peak_fits_at_once"] = counter.peak
        row["defect_seen_predicate"] = "the second /ws/control start was a success while the first run's fit still ran"
        row["defect_seen"] = row["ws_second_start_ack"] == "success"
    finally:
        first.open_all()
        run_model.open_all()
        mgr.shutdown()
        _join(first.threads + run_model.threads)
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch dir under the repo's tmp/ (snapshots go here)")
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--label", default="")
    args = parser.parse_args(argv)
    args.scratch.mkdir(parents=True, exist_ok=True)
    manager_file = Path(manager_module.__file__)
    header = {
        "label": args.label,
        "python": sys.version,
        "executable": sys.executable,
        "base_prefix": sys.base_prefix,
        "juniper_service_core": juniper_service_core.__file__,
        "manager_py": str(manager_file),
        "manager_sha256": hashlib.sha256(manager_file.read_bytes()).hexdigest(),
    }
    rows: list[dict[str, Any]] = []
    jobs: list[tuple[str, Any, tuple]] = []
    for op in ("load_snapshot", "resume_from_snapshot", "start_replay", "restore_for_retrain", "attach_model"):
        for ending in ("unwind", "raise", "inflight"):
            jobs.append((f"D1 {op} {ending}", defect1_row, (args.scratch, op, ending)))
    for leave_by in ("restore_for_retrain", "resume_from_snapshot", "load_snapshot", "attach_model", "reset", "start_training", "start_replay"):
        jobs.append((f"D2 {leave_by}", defect2_leftover_row, (args.scratch, leave_by)))
    jobs.append(("D2 stop_replay during a run", defect2_stop_replay_during_run, (args.scratch,)))
    jobs.append(("D2 frames", defect2_frames_during_run, (args.scratch,)))
    for route in ("restore", "resume", "replay", "retrain"):
        for ending in ("unwind", "raise"):
            jobs.append((f"HTTP D1 {route} {ending}", http_defect1_row, (args.scratch, route, ending)))
    jobs.append(("HTTP D2", http_defect2_row, (args.scratch,)))
    jobs.append(("WS D2", ws_control_row, (args.scratch,)))
    failures = 0
    for name, fn, fargs in jobs:
        try:
            row = fn(*fargs)
        except Exception as exc:  # noqa: BLE001 - a row that cannot run is reported and fails the probe
            failures += 1
            row = {"row": name, "setup_error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}
        rows.append(row)
        print(f"{name}\tdefect_seen={row.get('defect_seen')}", flush=True)
    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump({"header": header, "rows": rows}, fh, indent=1, default=str)
    seen = sum(1 for r in rows if r.get("defect_seen"))
    print(f"RESULT {args.label}: {len(rows)} rows, defect_seen in {seen}, setup errors {failures}; manager sha256 {header['manager_sha256'][:12]}")
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
