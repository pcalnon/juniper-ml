"""
Re-derive flood-4 ruling 23's "Lifecycle races beside N-2" on a juniper-service-core tree and attack its fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23l-val-code: independent validation of carrier r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 19, 23);
         juniper-ml#2557 (N-2, the start refusal the carrier extends)

It measures whichever ``juniper_service_core`` the interpreter imports (point PYTHONPATH at a package copy);
the output records that file and the sha256 of its ``lifecycle/manager.py``. Nothing here binds a port: the HTTP
and /ws/control rows use FastAPI's in-process TestClient.

Rows (``--rows``; default all):
  d1      a stop, then each of load_snapshot / resume_from_snapshot / start_replay / restore_for_retrain /
          attach_model while the stopped fit is still running, the fit then ending three ways (unwind, raise,
          an event already inside the sink); plus the four snapshot routes over HTTP, and an unknown id there.
  d2      a replay left by a load (retrain, resume, restore): does the session survive, does its stop reset a
          run started after the load, does a second start then run beside it; over HTTP and with the starts
          sent over /ws/control; stop_replay() during a run; a leftover session's seek during a run.
  x       attacks on the fix: X1 a replay frame already being produced when a load ends the session (the
          daemon is held, by a ReplaySession subclass, between its stop check and the sink call -- where a
          thread switch can land); X3 an exception inside a load after the snapshot has loaded (a malformed
          sidecar history) while REPLAYING; X4 attach_model during a replay, then every way a run could start
          beside the kept session; X5 a replay that is playing when a load arrives, with no run after it:
          do its frames keep reaching the sink; X7 the cost: an eventless stopped fit holds back loads, attach and start,
          a reset does not release them, and the status shows nothing.
  stale   X2, the same race as X1 with no subclass: N trials of play + load + start, the sink doing a little
          work before it records (as a transport that builds an envelope before broadcasting); counts replay
          frames recorded while the machine reads STARTED.
Stress (``--stress-seconds S``, with ``--switch-interval``): worker threads drive random lifecycle calls on one
manager whose models emit events in a loop; invariants are checked under the manager lock after every call:
I1 a replay session exists only while REPLAYING; I2 at most one fit runs; I4 a fit that is running has its run
active or its stop set; I5 no load or attach completes while a stopped fit is still in fit; I6 no replay frame
reaches the sink while the machine reads STARTED or PAUSED.

Usage: python <this file> --scratch DIR --json-out FILE --label LABEL [--rows d1,d2,x,stale]
       [--stale-trials N] [--stale-sink-work N] [--stress-seconds S] [--stress-workers N] [--switch-interval F]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import threading
import time
import traceback
import types
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
from juniper_service_core.lifecycle import manager as manager_mod
from juniper_service_core.lifecycle.monitor import LifecycleMonitor
from juniper_service_core.lifecycle.replay import ReplaySession
from juniper_service_core.lifecycle.snapshots import SIDECAR_NAME, SnapshotNotFoundError
from juniper_service_core.routes import build_routers
from juniper_service_core.websocket import LifecycleCommandExecutor, WebSocketManager, attach_websocket, build_websocket_router

REFUSAL = "The stopped run's fit is still running"
DEADLINE = 5.0
PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}
SNAPSHOT_RUN = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
LONG_SNAPSHOT_RUN = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "epoch_end"), ("emit", "epoch_end"), ("emit", "epoch_end"), ("emit", "training_end"))
RUN = (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end"), ("emit", "training_end"))
BESIDE = (("emit", "training_start"), ("gate", "beside"), ("emit", "epoch_end"))

RUNNING = {"now": 0, "peak": 0}
RUN_LOCK = threading.Lock()


def zeros(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


class _Base(TrainableModel):
    task_type = "regression"
    random_seed = 0

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], 1))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.25}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "probe", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return (2,)

    @property
    def output_shape(self) -> tuple[int, ...]:
        return (1,)


class GatedModel(_Base):
    """``fit`` call n follows ``scripts[n-1]`` (emit / gate / raise); later calls return at once. Counts fits running at once."""

    def __init__(self, *scripts: tuple[tuple[str, str], ...]) -> None:
        self.fits = 0
        self.peak = 0
        self.running = 0
        self.threads: list[threading.Thread] = []
        self.interrupted: list[int] = []
        self._scripts = scripts
        self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def _gate(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self._gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str, timeout: float = DEADLINE) -> bool:
        return self._gate(name)[1].wait(timeout)

    def open(self, name: str) -> None:
        self._gate(name)[0].set()

    def open_all(self) -> None:
        with self._lock:
            gates = [gate for gate, _ in self._gates.values()]
        for gate in gates:
            gate.set()

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with self._lock:
            self.fits += 1
            call = self.fits
            self.threads.append(threading.current_thread())
            self.running += 1
            self.peak = max(self.peak, self.running)
        script = self._scripts[call - 1] if call <= len(self._scripts) else ()
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(PAYLOADS[arg]), 0))
                elif kind == "gate":
                    gate, reached = self._gate(arg)
                    reached.set()
                    gate.wait(timeout=10.0)
                elif kind == "raise":
                    raise RuntimeError(arg)
        except TrainingInterrupted:
            with self._lock:
                self.interrupted.append(call)
            raise
        finally:
            with self._lock:
                self.running -= 1
        return TrainResult(final_metrics={"mse": 0.25}, n_epochs=1)


class QueueSerializer(ModelSerializer):
    """Writes nothing; each load hands back the next queued model, then fresh GatedModels."""

    def __init__(self, *models: TrainableModel) -> None:
        self._queue = list(models)

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        return self._queue.pop(0) if self._queue else GatedModel()


class HoldingMonitor(LifecycleMonitor):
    """Once armed, holds the first epoch_end inside on_event (before folding it) until released."""

    def __init__(self) -> None:
        super().__init__()
        self.armed = False
        self.inside = threading.Event()
        self.release = threading.Event()

    def on_event(self, event: TrainingEvent) -> None:
        if self.armed and event.type == "epoch_end" and not self.inside.is_set():
            self.inside.set()
            self.release.wait(timeout=10.0)
        super().on_event(event)


def brief(mgr: ServiceLifecycleManager) -> dict[str, Any]:
    status = mgr.get_status()
    return {
        "fsm": status["state_machine"]["status"],
        "monitor": status["monitor"]["status"],
        "error": status.get("error"),
        "history": len(mgr.get_metrics_history()),
        "session": mgr.get_replay_state() is not None,
        "training_active": status["training_active"],
    }


def attempt(fn, *args, **kwargs) -> tuple[str, Any]:
    try:
        return "accepted", fn(*args, **kwargs)
    except (RuntimeError, ValueError, SnapshotNotFoundError) as exc:
        return f"refused: {type(exc).__name__}: {exc}", None


def cleanup(mgr: ServiceLifecycleManager, *models: GatedModel) -> None:
    for model in models:
        model.open_all()
    mgr.set_frame_sink(None)
    mgr.shutdown()
    for model in models:
        for thread in model.threads:
            thread.join(timeout=DEADLINE)


# ---------------------------------------------------------------------------------------------------------------
# d1 -- stop, then a load or an attach while the stopped fit runs
# ---------------------------------------------------------------------------------------------------------------


def row_d1(scratch: Path, op: str, ending: str) -> dict[str, Any]:
    if ending == "unwind":
        second = (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("emit", "training_end"))
    elif ending == "raise":
        second = (("emit", "training_start"), ("gate", "old"), ("raise", "boom"))
    else:
        second = SNAPSHOT_RUN
    model = GatedModel(SNAPSHOT_RUN, second)
    mgr = ServiceLifecycleManager(model, serializer=QueueSerializer(), snapshot_dir=scratch / f"d1-{op}-{ending}")
    hold = HoldingMonitor() if ending == "inflight" else None
    if hold is not None:
        mgr.monitor = hold
    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        sid = mgr.save_snapshot()["id"]
        if hold is not None:
            hold.armed = True
        mgr.start_training(*zeros())
        parked = hold.inside.wait(DEADLINE) if hold is not None else model.reached("old")
        mgr.stop_training()
        old = model.threads[1]
        call = (lambda: mgr.attach_model(GatedModel())) if op == "attach_model" else (lambda: getattr(mgr, op)(sid))
        outcome, _ = attempt(call)
        right_after = brief(mgr)
        if hold is not None:
            hold.release.set()
        model.open_all()
        old.join(DEADLINE)
        final = brief(mgr)
        retry = None
        if outcome != "accepted":
            retry_outcome, _ = attempt(call)
            retry = {"outcome": retry_outcome, "state": brief(mgr)}
        settled_over = outcome == "accepted" and (final["monitor"], final["error"], final["history"]) != (right_after["monitor"], right_after["error"], right_after["history"])
        return {
            "row": f"D1 stop then {op} ({ending})",
            "parked": parked,
            "outcome": outcome,
            "right_after": right_after,
            "after_the_stopped_fit_ended": final,
            "old_thread_ended": not old.is_alive(),
            "retry_once_ended": retry,
            "defect_seen": settled_over,
            "fixed_shape": outcome.startswith("refused") and REFUSAL in outcome and (retry or {}).get("outcome") == "accepted",
        }
    finally:
        if hold is not None:
            hold.release.set()
        cleanup(mgr, model)


def http_app(mgr: ServiceLifecycleManager, *, ws: bool = False, executor: Any = None):
    routers = [*build_routers(), build_websocket_router()] if ws else build_routers()
    app = create_app(title="probe", version="0.0.0", routers=routers)
    app.state.lifecycle = mgr
    if ws:
        app.state.settings = types.SimpleNamespace(
            ws_resume_handshake_timeout_s=0.2,
            ws_initial_metrics_count=50,
            ws_heartbeat_interval_sec=3600,
            ws_heartbeat_pong_timeout_sec=3600,
            ws_control_idle_timeout_sec=3600,
            ws_control_rate_limit_per_sec=50,
        )
        attach_websocket(app, manager=mgr, ws_manager=WebSocketManager(), command_executor=executor)
    return app


def row_d1_http(scratch: Path, route: str) -> dict[str, Any]:
    model = GatedModel(SNAPSHOT_RUN, (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("emit", "training_end")))
    mgr = ServiceLifecycleManager(model, serializer=QueueSerializer(), snapshot_dir=scratch / f"d1-http-{route}")
    X, y = zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}
    try:
        with TestClient(http_app(mgr)) as client:
            client.post("/v1/training/start", json=payload)
            assert mgr.join(DEADLINE)
            sid = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            client.post("/v1/training/start", json=payload)
            parked = model.reached("old")
            client.post("/v1/training/stop")
            in_window = client.post(f"/v1/snapshots/{sid}/{route}")
            unknown = client.post(f"/v1/snapshots/no-such-snapshot/{route}")
            model.open("old")
            assert mgr.join(DEADLINE)
            once_ended = client.post(f"/v1/snapshots/{sid}/{route}")
            return {
                "row": f"D1 HTTP stop then POST /{route}",
                "parked": parked,
                "in_window": [in_window.status_code, in_window.json().get("detail")],
                "unknown_id_in_window": [unknown.status_code, unknown.json().get("detail")],
                "once_the_fit_ended": once_ended.status_code,
                "defect_seen": in_window.status_code == 200,
            }
    finally:
        cleanup(mgr, model)


# ---------------------------------------------------------------------------------------------------------------
# d2 -- a replay session left by a load
# ---------------------------------------------------------------------------------------------------------------


def replayed(scratch: Path, name: str):
    first = GatedModel(SNAPSHOT_RUN)
    run_model = GatedModel(RUN, BESIDE)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(GatedModel(), run_model), snapshot_dir=scratch / name)
    mgr.start_training(*zeros())
    assert mgr.join(DEADLINE)
    sid = mgr.save_snapshot()["id"]
    mgr.start_replay(sid)
    return mgr, sid, first, run_model


def row_d2_load(scratch: Path, load: str) -> dict[str, Any]:
    mgr, sid, first, run_model = replayed(scratch, f"d2-{load}")
    try:
        getattr(mgr, load)(sid)
        survived = mgr.get_replay_state() is not None
        start1, _ = attempt(mgr.start_training, *zeros())
        running = run_model.reached("run", 2.0) if start1 == "accepted" else False
        stop, _ = attempt(mgr.replay_control, "stop")
        after_stop = brief(mgr)
        stop_event_set = mgr._stop_event.is_set()
        start2, _ = attempt(mgr.start_training, *zeros())
        beside = run_model.reached("beside", 2.0) if start2 == "accepted" else False
        peak = run_model.peak
        run_model.open_all()
        mgr.join(DEADLINE)
        return {
            "row": f"D2 replay, {load}, start, replay stop, start",
            "session_survived_the_load": survived,
            "first_start": start1,
            "first_run_parked": running,
            "replay_stop": stop,
            "after_replay_stop": after_stop,
            "stop_event_set_after_replay_stop": stop_event_set,
            "second_start": start2,
            "second_fit_ran_beside": beside,
            "peak_fits": peak,
            "defect_seen": survived or stop == "accepted" or peak > 1,
        }
    finally:
        cleanup(mgr, first, run_model)


def row_d2_http(scratch: Path) -> dict[str, Any]:
    first = GatedModel(SNAPSHOT_RUN)
    run_model = GatedModel(RUN, BESIDE)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(GatedModel(), run_model), snapshot_dir=scratch / "d2-http")
    X, y = zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}
    try:
        with TestClient(http_app(mgr)) as client:
            client.post("/v1/training/start", json=payload)
            assert mgr.join(DEADLINE)
            sid = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            codes = {"replay": client.post(f"/v1/snapshots/{sid}/replay").status_code, "retrain": client.post(f"/v1/snapshots/{sid}/retrain").status_code}
            codes["start"] = client.post("/v1/training/start", json=payload).status_code
            run_model.reached("run", 2.0)
            stop = client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "stop"})
            status = client.get("/v1/training/status").json()["data"]
            second = client.post("/v1/training/start", json=payload)
            beside = run_model.reached("beside", 2.0) if second.status_code == 200 else False
            peak = run_model.peak
            run_model.open_all()
            mgr.join(DEADLINE)
            return {
                "row": "D2 HTTP replay, retrain, start, replay/control stop, start",
                "codes": codes,
                "replay_stop": [stop.status_code, stop.json().get("detail") or stop.json().get("data", {}).get("state_machine", {}).get("status")],
                "status_after_stop": [status["state_machine"]["status"], status["training_active"]],
                "second_start": [second.status_code, second.json().get("detail")],
                "second_fit_ran_beside": beside,
                "peak_fits": peak,
                "defect_seen": stop.status_code == 200 or peak > 1,
            }
    finally:
        cleanup(mgr, first, run_model)


def row_d2_ws(scratch: Path) -> dict[str, Any]:
    first = GatedModel(SNAPSHOT_RUN)
    run_model = GatedModel(RUN, BESIDE)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(GatedModel(), run_model), snapshot_dir=scratch / "d2-ws")
    X, y = zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}
    executor = LifecycleCommandExecutor(mgr, start=lambda params: mgr.start_training(X, y))
    try:
        with TestClient(http_app(mgr, ws=True, executor=executor)) as client:
            client.post("/v1/training/start", json=payload)
            assert mgr.join(DEADLINE)
            sid = client.post("/v1/snapshots", json={}).json()["data"]["id"]
            client.post(f"/v1/snapshots/{sid}/replay")
            client.post(f"/v1/snapshots/{sid}/retrain")
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()
                ws.send_json({"command": "start", "command_id": "s1"})
                ack1 = ws.receive_json()["data"]
                run_model.reached("run", 2.0)
                stop = client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "stop"})
                ws.send_json({"command": "start", "command_id": "s2"})
                ack2 = ws.receive_json()["data"]
                unknown = []
                for command in ("replay", "replay_control", "stop_replay", "restore", "retrain", "load_snapshot", "attach_model"):
                    ws.send_json({"command": command, "command_id": command})
                    unknown.append([command, ws.receive_json()["data"].get("status")])
            beside = run_model.reached("beside", 2.0) if ack2.get("status") == "success" else False
            peak = run_model.peak
            run_model.open_all()
            mgr.join(DEADLINE)
            return {
                "row": "D2 /ws/control start, HTTP replay stop, /ws/control start",
                "ack1": ack1.get("status"),
                "replay_stop": stop.status_code,
                "ack2": [ack2.get("status"), ack2.get("error") or ack2.get("message")],
                "other_commands": unknown,
                "second_fit_ran_beside": beside,
                "peak_fits": peak,
                "defect_seen": stop.status_code == 200 or peak > 1,
            }
    finally:
        cleanup(mgr, first, run_model)


def row_d2_stop_replay_during_run(scratch: Path) -> dict[str, Any]:
    model = GatedModel(RUN)
    mgr = ServiceLifecycleManager(model)
    try:
        mgr.start_training(*zeros())
        model.reached("run")
        before = brief(mgr)
        mgr.stop_replay()
        after = brief(mgr)
        return {"row": "D2 stop_replay() during a run, no replay", "before": before, "after": after, "defect_seen": after["monitor"] != before["monitor"] or after["fsm"] != before["fsm"]}
    finally:
        cleanup(mgr, model)


def row_d2_seek_frame(scratch: Path) -> dict[str, Any]:
    mgr, sid, first, run_model = replayed(scratch, "d2-seek")
    frames: list[dict[str, Any]] = []
    try:
        mgr.restore_for_retrain(sid)
        mgr.start_training(*zeros())
        run_model.reached("run")
        mgr.set_frame_sink(frames.append)
        seek, _ = attempt(mgr.replay_control, "seek", time_index=0)
        replay_frames = [frame for frame in frames if (frame.get("data") or {}).get("replay") is True]
        return {"row": "D2 leftover session seek during a run", "seek": seek, "replay_frames_in_live_sink": len(replay_frames), "defect_seen": bool(replay_frames)}
    finally:
        cleanup(mgr, first, run_model)


# ---------------------------------------------------------------------------------------------------------------
# x -- attacks on the fix
# ---------------------------------------------------------------------------------------------------------------


class ParkingReplaySession(ReplaySession):
    """Holds the playback daemon inside _emit_frame (before the sink call) once armed: a thread switch landing there."""

    armed = threading.Event()
    parked = threading.Event()
    release = threading.Event()

    def _frame_at(self, index: int):
        cls = ParkingReplaySession
        if cls.armed.is_set() and threading.current_thread() is self._thread and not cls.parked.is_set():
            cls.parked.set()
            cls.release.wait(timeout=10.0)
        return super()._frame_at(index)


def row_x1_inflight_frame(scratch: Path) -> dict[str, Any]:
    first = GatedModel(LONG_SNAPSHOT_RUN)
    run_model = GatedModel(RUN)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(GatedModel(), run_model), snapshot_dir=scratch / "x1")
    received: list[tuple[str, bool]] = []
    got = threading.Event()

    def sink(frame: dict[str, Any]) -> None:
        is_replay = (frame.get("data") or {}).get("replay") is True
        received.append((mgr.state_machine.status.name, is_replay))
        if is_replay and mgr.state_machine.status.name == "STARTED":
            got.set()

    saved = manager_mod.ReplaySession
    manager_mod.ReplaySession = ParkingReplaySession
    for event in (ParkingReplaySession.armed, ParkingReplaySession.parked, ParkingReplaySession.release):
        event.clear()
    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        sid = mgr.save_snapshot()["id"]
        mgr.set_frame_sink(sink)
        mgr.start_replay(sid)
        session = mgr._replay_session
        ParkingReplaySession.armed.set()
        mgr.replay_control("speed", value=10.0)
        mgr.replay_control("play")
        parked = ParkingReplaySession.parked.wait(DEADLINE)
        load, _ = attempt(mgr.restore_for_retrain, sid)
        start, _ = attempt(mgr.start_training, *zeros())
        run_parked = run_model.reached("run", 2.0)
        ParkingReplaySession.release.set()
        arrived = got.wait(2.0)
        daemon_ended = session.join(timeout=2.0) if mgr.get_replay_state() is None else "session still open"
        during_run = [r for r in received if r == ("STARTED", True)]
        return {
            "row": "X1 a replay frame in flight when a load ends the session (daemon held between its stop check and the sink)",
            "daemon_parked": parked,
            "load": load,
            "start": start,
            "run_parked": run_parked,
            "session_open_after_load": mgr.get_replay_state() is not None,
            "replay_frames_received_while_STARTED": len(during_run),
            "arrived": arrived,
            "daemon_ended": daemon_ended,
            "residual_seen": len(during_run) > 0,
        }
    finally:
        manager_mod.ReplaySession = saved
        ParkingReplaySession.release.set()
        cleanup(mgr, first, run_model)


def row_x3_malformed_sidecar(scratch: Path, op: str) -> dict[str, Any]:
    first = GatedModel(SNAPSHOT_RUN)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(), snapshot_dir=scratch / f"x3-{op}")
    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        good = mgr.save_snapshot()["id"]
        bad = mgr.save_snapshot()["id"]
        sidecar = scratch / f"x3-{op}" / bad / SIDECAR_NAME
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        record["history"] = [1]
        sidecar.write_text(json.dumps(record), encoding="utf-8")
        mgr.start_replay(good)
        before = brief(mgr)
        model_before = mgr.model
        try:
            getattr(mgr, op)(bad)
            outcome = "accepted"
        except Exception as exc:  # noqa: BLE001 - the probe records whatever the load raises
            outcome = f"raised {type(exc).__name__}: {exc}"
        after = brief(mgr)
        control, _ = attempt(mgr.replay_control, "status")
        start, _ = attempt(mgr.start_training, *zeros())
        recovered = mgr.reset()["state_machine"]["status"]
        return {
            "row": f"X3 {op} of a snapshot whose sidecar history is malformed, while REPLAYING",
            "before": before,
            "outcome": outcome,
            "model_replaced": mgr.model is not model_before,
            "after": after,
            "replay_control_status": control,
            "start": start,
            "reset_recovers_to": recovered,
            "replaying_without_a_session": after["fsm"] == "REPLAYING" and not after["session"],
        }
    finally:
        cleanup(mgr, first)


def row_x4_attach_during_replay(scratch: Path) -> dict[str, Any]:
    mgr, _sid, first, run_model = replayed(scratch, "x4")
    try:
        mgr.attach_model(run_model)
        kept = mgr.get_replay_state() is not None
        tries = {}
        for name, fn in (("start_training", lambda: mgr.start_training(*zeros())), ("pause_training", mgr.pause_training), ("resume_training", mgr.resume_training)):
            tries[name] = attempt(fn)[0]
        tries["stop_training"] = brief(mgr) | {"after": None}
        mgr.stop_training()
        tries["stop_training"] = brief(mgr)
        ran = run_model.fits
        stop, _ = attempt(mgr.replay_control, "stop")
        after_stop = brief(mgr)
        start, _ = attempt(mgr.start_training, *zeros())
        parked = run_model.reached("run", 2.0) if start == "accepted" else False
        session_after_start = mgr.get_replay_state() is not None
        run_model.open_all()
        mgr.join(DEADLINE)
        return {
            "row": "X4 attach_model during a replay keeps the session; can a run start beside it?",
            "session_kept": kept,
            "while_kept": tries,
            "fits_while_session_open": ran,
            "replay_stop": stop,
            "after_replay_stop": after_stop,
            "start_after": start,
            "run_parked": parked,
            "session_during_that_run": session_after_start,
            "hole_seen": ran > 0 or session_after_start,
        }
    finally:
        cleanup(mgr, first, run_model)


def row_x5_playing_replay_then_load(scratch: Path, load: str) -> dict[str, Any]:
    """A replay that is playing when a load arrives, with no run afterwards: do its frames keep reaching the sink?"""
    first = GatedModel(LONG_SNAPSHOT_RUN)
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(), snapshot_dir=scratch / f"x5-{load}")
    after: list[str] = []
    state = {"loaded": False}
    second = threading.Event()

    def sink(frame: dict[str, Any]) -> None:
        if (frame.get("data") or {}).get("replay") is True and state["loaded"]:
            after.append(mgr.state_machine.status.name)
            second.set()

    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        sid = mgr.save_snapshot()["id"]
        mgr.set_frame_sink(sink)
        mgr.start_replay(sid)
        session = mgr._replay_session
        mgr.replay_control("speed", value=10.0)
        mgr.replay_control("play")
        loaded = getattr(mgr, load)(sid)["state_machine"]["status"]
        state["loaded"] = True
        if mgr.get_replay_state() is None:
            session.join(timeout=2.0)
        else:
            second.wait(1.0)
        return {
            "row": f"X5 a playing replay, then {load} (no run follows)",
            "machine_after_load": loaded,
            "session_open_after_load": mgr.get_replay_state() is not None,
            "replay_frames_after_the_load": len(after),
            "states_seen_by_those_frames": sorted(set(after)),
            "replay_kept_streaming": bool(after),
        }
    finally:
        cleanup(mgr, first)


def row_x7_cost(scratch: Path) -> dict[str, Any]:
    model = GatedModel(SNAPSHOT_RUN, (("emit", "training_start"), ("gate", "eventless")))
    mgr = ServiceLifecycleManager(model, serializer=QueueSerializer(), snapshot_dir=scratch / "x7")
    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        sid = mgr.save_snapshot()["id"]
        mgr.start_training(*zeros())
        model.reached("eventless")
        mgr.stop_training()
        mgr.reset()
        held = {
            "load_snapshot": attempt(mgr.load_snapshot, sid)[0],
            "restore_for_retrain": attempt(mgr.restore_for_retrain, sid)[0],
            "attach_model": attempt(mgr.attach_model, GatedModel())[0],
            "start_training": attempt(mgr.start_training, *zeros())[0],
        }
        status = mgr.get_status()
        model.open("eventless")
        mgr.join(DEADLINE)
        after = {"load_snapshot": attempt(mgr.load_snapshot, sid)[0], "attach_model": attempt(mgr.attach_model, GatedModel())[0]}
        return {
            "row": "X7 cost: an eventless stopped fit, then reset",
            "held_back_after_stop_and_reset": held,
            "status_while_held": {"keys": sorted(status), "state_machine": status["state_machine"]["status"], "training_active": status["training_active"], "monitor": status["monitor"]["status"]},
            "once_the_fit_returned": after,
        }
    finally:
        cleanup(mgr, model)


def row_x2_stale(scratch: Path, trials: int, sink_work: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    first = GatedModel(LONG_SNAPSHOT_RUN)
    run_models = [GatedModel(RUN) for _ in range(trials)]
    mgr = ServiceLifecycleManager(first, serializer=QueueSerializer(*[m for pair in zip([GatedModel() for _ in range(trials)], run_models, strict=True) for m in pair]), snapshot_dir=scratch / "x2")
    state = {"trial": -1, "armed": False}
    hits: list[int] = []
    frames_total = {"n": 0}

    def sink(frame: dict[str, Any]) -> None:
        data = frame.get("data") or {}
        if data.get("replay") is not True:
            return
        for _ in range(sink_work):
            json.dumps(data)
        frames_total["n"] += 1
        if state["armed"] and mgr.state_machine.status.name == "STARTED":
            hits.append(state["trial"])

    wait = threading.Event()
    try:
        mgr.start_training(*zeros())
        assert mgr.join(DEADLINE)
        sid = mgr.save_snapshot()["id"]
        mgr.set_frame_sink(sink)
        t0 = time.perf_counter()
        for trial in range(trials):
            state["trial"] = trial
            state["armed"] = False
            mgr.start_replay(sid)
            mgr.replay_control("speed", value=10.0)
            mgr.replay_control("play")
            wait.wait(rng.uniform(0.0, 0.1))
            mgr.restore_for_retrain(sid)
            run_model = run_models[trial]
            mgr.start_training(*zeros())
            state["armed"] = True
            run_model.reached("run", 2.0)
            wait.wait(0.12)
            state["armed"] = False
            run_model.open_all()
            mgr.join(DEADLINE)
        elapsed = time.perf_counter() - t0
        return {"row": "X2 stale replay frame after a load ended the session, no subclass", "trials": trials, "sink_work_json_dumps": sink_work, "replay_frames_total": frames_total["n"], "trials_with_a_replay_frame_while_STARTED": len(set(hits)), "frames_while_STARTED": len(hits), "elapsed_s": round(elapsed, 2), "switch_interval": sys.getswitchinterval()}
    finally:
        cleanup(mgr, first, *run_models)


# ---------------------------------------------------------------------------------------------------------------
# stress -- random interleavings with invariants
# ---------------------------------------------------------------------------------------------------------------


class StressModel(_Base):
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with RUN_LOCK:
            RUNNING["now"] += 1
            RUNNING["peak"] = max(RUNNING["peak"], RUNNING["now"])
        try:
            if on_event is not None:
                on_event(TrainingEvent("training_start", {}, 0))
                for epoch in range(self._rng.randint(5, 40)):
                    if self._rng.random() < 0.08:
                        time.sleep(self._rng.uniform(0.002, 0.02))  # an eventless stretch: a stop waits for the next event
                    on_event(TrainingEvent("epoch_end", {"epoch": epoch, "metrics": {"mse": 0.25}}, 0))
                on_event(TrainingEvent("training_end", {"metrics": {"mse": 0.25}}, 0))
        finally:
            with RUN_LOCK:
                RUNNING["now"] -= 1
        return TrainResult(final_metrics={"mse": 0.25}, n_epochs=1)


class StressSerializer(ModelSerializer):
    def __init__(self) -> None:
        self._n = 0

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        self._n += 1
        return StressModel(10_000 + self._n)


VIOLATIONS: dict[str, int] = {}
SAMPLES: dict[str, list[Any]] = {}


def violate(name: str, sample: Any) -> None:
    VIOLATIONS[name] = VIOLATIONS.get(name, 0) + 1
    SAMPLES.setdefault(name, [])
    if len(SAMPLES[name]) < 3:
        SAMPLES[name].append(sample)


class InstrumentedManager(ServiceLifecycleManager):
    def _load_snapshot_model(self, snapshot_id: str) -> dict[str, Any]:
        sidecar = super()._load_snapshot_model(snapshot_id)
        thread = self._thread
        if thread is not None and thread.is_alive() and self._stop_event.is_set() and RUNNING["now"] > 0:
            violate("I5_load_while_a_stopped_fit_runs", self.state_machine.status.name)
        return sidecar

    def attach_model(self, model: TrainableModel) -> None:
        with self._lock:
            super().attach_model(model)
            thread = self._thread
            if thread is not None and thread.is_alive() and self._stop_event.is_set() and RUNNING["now"] > 0:
                violate("I5_attach_while_a_stopped_fit_runs", self.state_machine.status.name)


def check(mgr: ServiceLifecycleManager) -> None:
    with mgr._lock:
        machine = mgr.state_machine
        if mgr._replay_session is not None and not machine.is_replaying():
            violate("I1_session_outside_REPLAYING", machine.status.name)
        if RUNNING["now"] > 0 and not machine.is_active() and not mgr._stop_event.is_set():
            violate("I4_fit_running_with_run_inactive_and_no_stop", machine.status.name)
    if RUNNING["peak"] > 1:
        VIOLATIONS["I2_peak_fits"] = RUNNING["peak"]


def run_stress(scratch: Path, seconds: float, workers: int, seed: int) -> dict[str, Any]:
    RUNNING.update(now=0, peak=0)
    VIOLATIONS.clear()
    SAMPLES.clear()
    mgr = InstrumentedManager(StressModel(seed), serializer=StressSerializer(), snapshot_dir=scratch / "stress")
    mgr.start_training(*zeros())
    assert mgr.join(10.0)
    sid = mgr.save_snapshot()["id"]
    counts: dict[str, dict[str, int]] = {}
    count_lock = threading.Lock()

    def sink(frame: dict[str, Any]) -> None:
        if (frame.get("data") or {}).get("replay") is True and mgr.state_machine.status.name in ("STARTED", "PAUSED"):
            violate("I6_replay_frame_while_a_run_is_active", mgr.state_machine.status.name)

    mgr.set_frame_sink(sink)
    ops = {
        "start": lambda: mgr.start_training(*zeros()),
        "stop": mgr.stop_training,
        "reset": mgr.reset,
        "load_snapshot": lambda: mgr.load_snapshot(sid),
        "resume_from_snapshot": lambda: mgr.resume_from_snapshot(sid),
        "restore_for_retrain": lambda: mgr.restore_for_retrain(sid),
        "start_replay": lambda: mgr.start_replay(sid),
        "replay_stop": lambda: mgr.replay_control("stop"),
        "replay_play": lambda: (mgr.replay_control("speed", value=10.0), mgr.replay_control("play")),
        "replay_seek": lambda: mgr.replay_control("seek", time_index=0),
        "stop_replay": mgr.stop_replay,
        "attach": lambda: mgr.attach_model(StressModel(random.randint(0, 10**6))),
        "pause": mgr.pause_training,
        "resume": mgr.resume_training,
    }
    names = list(ops) + ["start", "start", "stop", "restore_for_retrain", "start_replay", "replay_stop"]
    deadline = time.monotonic() + seconds
    errors: list[str] = []

    def worker(wseed: int) -> None:
        rng = random.Random(wseed)
        while time.monotonic() < deadline:
            name = rng.choice(names)
            try:
                ops[name]()
                result = "ok"
            except RuntimeError as exc:
                result = "refused_stopped_fit" if REFUSAL in str(exc) else "refused_other"
            except (ValueError, SnapshotNotFoundError):
                result = "refused_other"
            except Exception:  # noqa: BLE001 - recorded, the stress keeps going
                result = "error"
                if len(errors) < 5:
                    errors.append(traceback.format_exc(limit=3))
            with count_lock:
                counts.setdefault(name, {}).setdefault(result, 0)
                counts[name][result] += 1
            check(mgr)

    def checker() -> None:
        while time.monotonic() < deadline:
            check(mgr)

    threads = [threading.Thread(target=worker, args=(seed + i,), daemon=True) for i in range(workers)] + [threading.Thread(target=checker, daemon=True)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(seconds + 30.0)
    hung = [t.name for t in threads if t.is_alive()]
    mgr.set_frame_sink(None)
    mgr.shutdown()
    return {
        "row": "STRESS",
        "seconds": seconds,
        "workers": workers,
        "switch_interval": sys.getswitchinterval(),
        "violations": dict(VIOLATIONS),
        "samples": SAMPLES,
        "peak_fits": RUNNING["peak"],
        "op_counts": counts,
        "errors": errors,
        "hung_threads": hung,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--rows", default="d1,d2,x")
    parser.add_argument("--stale-trials", type=int, default=200)
    parser.add_argument("--stale-sink-work", type=int, default=200)
    parser.add_argument("--stress-seconds", type=float, default=0.0)
    parser.add_argument("--stress-workers", type=int, default=3)
    parser.add_argument("--switch-interval", type=float, default=None)
    parser.add_argument("--seed", type=int, default=20261125)
    args = parser.parse_args()
    if args.switch_interval is not None:
        sys.setswitchinterval(args.switch_interval)
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    manager_file = Path(manager_mod.__file__)
    header = {
        "label": args.label,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "base_prefix": sys.base_prefix,
        "package": juniper_service_core.__file__,
        "manager_sha256": hashlib.sha256(manager_file.read_bytes()).hexdigest(),
        "switch_interval": sys.getswitchinterval(),
    }
    rows: list[dict[str, Any]] = []
    wanted = set(args.rows.split(","))

    def run(fn, *fargs) -> None:
        try:
            rows.append(fn(*fargs))
        except Exception:  # noqa: BLE001 - a setup failure is a row, not a crash
            rows.append({"row": f"{fn.__name__}{fargs[1:]}", "setup_error": traceback.format_exc(limit=5)})

    if "d1" in wanted:
        for op in ("load_snapshot", "resume_from_snapshot", "start_replay", "restore_for_retrain", "attach_model"):
            for ending in ("unwind", "raise", "inflight"):
                run(row_d1, scratch, op, ending)
        for route in ("restore", "resume", "replay", "retrain"):
            run(row_d1_http, scratch, route)
    if "d2" in wanted:
        for load in ("restore_for_retrain", "resume_from_snapshot", "load_snapshot"):
            run(row_d2_load, scratch, load)
        run(row_d2_http, scratch)
        run(row_d2_ws, scratch)
        run(row_d2_stop_replay_during_run, scratch)
        run(row_d2_seek_frame, scratch)
    if "x" in wanted:
        run(row_x1_inflight_frame, scratch)
        for op in ("load_snapshot", "start_replay", "resume_from_snapshot"):
            run(row_x3_malformed_sidecar, scratch, op)
        run(row_x4_attach_during_replay, scratch)
        for load in ("load_snapshot", "resume_from_snapshot", "restore_for_retrain"):
            run(row_x5_playing_replay_then_load, scratch, load)
        run(row_x7_cost, scratch)
    if "stale" in wanted:
        run(row_x2_stale, scratch, args.stale_trials, args.stale_sink_work, args.seed)
    if args.stress_seconds > 0:
        run(run_stress, scratch, args.stress_seconds, args.stress_workers, args.seed)
    out = {"header": header, "rows": rows}
    Path(args.json_out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(header))
    for row in rows:
        keys = [k for k in ("defect_seen", "fixed_shape", "residual_seen", "replaying_without_a_session", "hole_seen", "replay_kept_streaming", "violations", "setup_error") if k in row]
        print(row.get("row"), {k: row[k] if k != "setup_error" else row[k][-300:] for k in keys})
    return 0


if __name__ == "__main__":
    sys.exit(main())
