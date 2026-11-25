"""
Measure over HTTP (FastAPI TestClient) and /ws/control every client answer that carrier r23l says it changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, claims lens r23l-val-claims: an independent check of the carrier's "What changes for a client")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23);
         util/ad-hoc/2026-11-25_flood4_s14_r23l_probe.py (the builder's probe; this one is written independently)

Rows (each on a fresh manager, app and TestClient; a gated model whose ``fit`` parks on a threading.Event):
  W   after POST /v1/training/stop (or /reset) while the stopped fit is parked: each snapshot route with a real id
      and with an unknown id, the status right after, the status once the fit has ended (it unwinds, or raises),
      and the same two requests again then.
  A   during an active run: a snapshot route with an unknown id and with a real one (the active-run 409).
  S   a start in the stop window (the start route's detail, for its prefix).
  R   replay, then retrain or resume, then a start: one replay/control action (each of the seven, and an unknown
      one), then the status and a second start; and replay, restore, replay stop.
  WS  the same race with both starts over /ws/control; the acks of the load and replay command names; and the
      /ws/control answers in the stop window (start, reset, start, and a start once the fit has ended).
  PY  the Python API: stop_replay() during a run and from INVESTIGATING; get_replay_state() after each load that
      follows a replay; attach_model and each load method in the stop window.
  F   frames: a leftover session's seek during a run; and the replay frames a PLAYING replay sends after a load
      (one bounded observation window that only a frame ends early).

Which tree it measures is whatever ``juniper_service_core`` the interpreter imports; the output records that file
and the sha256 of its ``lifecycle/manager.py``. Every wait is a threading.Event with a deadline; nothing sleeps.

Usage: python <this file> --scratch DIR --json-out FILE [--label LABEL]
Exit: 0 when every row ran (whatever it saw); 2 when a row raised.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
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
from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.lifecycle import manager as manager_module
from juniper_service_core.routes import build_routers
from juniper_service_core.websocket import LifecycleCommandExecutor, WebSocketManager, attach_websocket, build_websocket_router

WAIT = 5.0
UNKNOWN_ID = "no-such-snapshot"
ROUTES = ("restore", "resume", "replay", "retrain")
PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}
ONE_EPOCH = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
FIFTY_EPOCHS = (("emit", "training_start"), ("epochs", "50"), ("emit", "training_end"))

_COUNT_LOCK = threading.Lock()
_COUNTS = {"active": 0, "peak": 0}


def _reset_peak() -> None:
    with _COUNT_LOCK:
        _COUNTS["peak"] = _COUNTS["active"]


def _peak() -> int:
    with _COUNT_LOCK:
        return _COUNTS["peak"]


class Gates:
    """Named (open, reached) Event pairs shared by every model of a row."""

    def __init__(self) -> None:
        self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def pair(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self._gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str, timeout: float = WAIT) -> bool:
        return self.pair(name)[1].wait(timeout)

    def open(self, name: str) -> None:
        self.pair(name)[0].set()

    def open_all(self) -> None:
        with self._lock:
            gates = [gate for gate, _ in self._gates.values()]
        for gate in gates:
            gate.set()


class GatedModel(TrainableModel):
    """``fit`` call n follows scripts[n - 1] (emit / epochs / gate / raise); later calls just return."""

    def __init__(self, gates: Gates, *scripts: tuple[tuple[str, str], ...]) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.fits = 0
        self.threads: list[threading.Thread] = []
        self._gates = gates
        self._scripts = scripts
        self._lock = threading.Lock()

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with self._lock:
            self.fits += 1
            call = self.fits
            self.threads.append(threading.current_thread())
        with _COUNT_LOCK:
            _COUNTS["active"] += 1
            _COUNTS["peak"] = max(_COUNTS["peak"], _COUNTS["active"])
        try:
            script = self._scripts[call - 1] if call <= len(self._scripts) else ()
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(PAYLOADS[arg]), 0))
                elif kind == "epochs" and on_event is not None:
                    for index in range(int(arg)):
                        on_event(TrainingEvent("epoch_end", {"epoch": index, "metrics": {"mse": 0.25}}, 0))
                elif kind == "gate":
                    gate, reached = self._gates.pair(arg)
                    reached.set()
                    gate.wait(timeout=10.0)
                elif kind == "raise":
                    raise RuntimeError(arg)
        finally:
            with _COUNT_LOCK:
                _COUNTS["active"] -= 1
        return TrainResult(final_metrics={"mse": 0.25}, n_epochs=1)

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], 1))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.25}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "gated", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return (2,)

    @property
    def output_shape(self) -> tuple[int, ...]:
        return (1,)


class FactorySerializer(ModelSerializer):
    """Writes no model file; every ``load`` returns ``factory()``."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        return self.factory()


class Row:
    """One stack: a manager over a gated first model, an app, the gates and every model a load built."""

    def __init__(self, scratch: Path, name: str, first_scripts: tuple, loaded_scripts: tuple = (), *, ws: bool = False) -> None:
        self.gates = Gates()
        self.models: list[GatedModel] = []
        self.first = self._model(*first_scripts)
        snapdir = scratch / name
        snapdir.mkdir(parents=True, exist_ok=True)
        self.mgr = ServiceLifecycleManager(self.first, serializer=FactorySerializer(lambda: self._model(*loaded_scripts)), snapshot_dir=snapdir)
        routers = [*build_routers()]
        if ws:
            routers.append(build_websocket_router())
        self.app = create_app(title="r23l-val-claims", version="0.0.0", routers=routers)
        if ws:
            executor = LifecycleCommandExecutor(self.mgr, start=lambda params: self.mgr.start_training(*_zeros()))
            attach_websocket(self.app, manager=self.mgr, ws_manager=WebSocketManager(), command_executor=executor)
        else:
            self.app.state.lifecycle = self.mgr
        _reset_peak()

    def _model(self, *scripts: tuple) -> GatedModel:
        model = GatedModel(self.gates, *scripts)
        self.models.append(model)
        return model

    def close(self) -> None:
        self.gates.open_all()
        self.mgr.set_frame_sink(None)
        self.mgr.shutdown()
        for model in self.models:
            for thread in model.threads:
                thread.join(timeout=WAIT)


def _zeros(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


def _payload() -> dict[str, Any]:
    X, y = _zeros()
    return {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}


def _answer(response) -> dict[str, Any]:
    out: dict[str, Any] = {"code": response.status_code}
    try:
        body = response.json()
    except ValueError:
        return out
    if "detail" in body:
        out["detail"] = body["detail"]
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and isinstance(data.get("state_machine"), dict):
        out["state_machine"] = data["state_machine"]["status"]
    return out


def _status(client: TestClient) -> dict[str, Any]:
    data = client.get("/v1/training/status").json()["data"]
    return {"state_machine": data["state_machine"]["status"], "monitor": data["monitor"]["status"], "phase": data["monitor"]["phase"], "training_active": data["training_active"], "error": data.get("error")}


def _complete_first_run(client: TestClient, row: Row) -> str:
    assert client.post("/v1/training/start", json=_payload()).status_code == 200
    assert row.mgr.join(timeout=WAIT)
    return client.post("/v1/snapshots", json={}).json()["data"]["id"]


# ---------------------------------------------------------------------------------------------------------- rows
def row_window(scratch: Path, route: str, ending: str, fit_end: str) -> dict[str, Any]:
    tail = (("emit", "epoch_end"), ("emit", "training_end")) if fit_end == "unwind" else (("raise", "boom"),)
    second = (("emit", "training_start"), ("gate", "old"), *tail)
    row = Row(scratch, f"W-{route}-{ending}-{fit_end}", (ONE_EPOCH, second), (ONE_EPOCH,))
    out: dict[str, Any] = {"row": f"W {route} after {ending}, the stopped fit then {fit_end}s"}
    try:
        with TestClient(row.app) as client:
            sid = _complete_first_run(client, row)
            assert client.post("/v1/training/start", json=_payload()).status_code == 200
            assert row.gates.reached("old")
            out["ending"] = _answer(client.post(f"/v1/training/{ending}"))
            out["load"] = _answer(client.post(f"/v1/snapshots/{sid}/{route}"))
            out["unknown_id"] = _answer(client.post(f"/v1/snapshots/{UNKNOWN_ID}/{route}"))
            out["status_after_load"] = _status(client)
            row.gates.open("old")
            assert row.mgr.join(timeout=WAIT)
            out["status_once_the_fit_ended"] = _status(client)
            out["status_changed_when_the_fit_ended"] = out["status_after_load"] != out["status_once_the_fit_ended"]
            out["load_again"] = _answer(client.post(f"/v1/snapshots/{sid}/{route}"))
            out["unknown_id_again"] = _answer(client.post(f"/v1/snapshots/{UNKNOWN_ID}/{route}"))
            out["peak_fits"] = _peak()
    finally:
        row.close()
    return out


def row_active(scratch: Path) -> dict[str, Any]:
    running = (("emit", "training_start"), ("gate", "run"), ("emit", "training_end"))
    row = Row(scratch, "A", (ONE_EPOCH, running), (ONE_EPOCH,))
    out: dict[str, Any] = {"row": "A a snapshot route during an active run"}
    try:
        with TestClient(row.app) as client:
            sid = _complete_first_run(client, row)
            assert client.post("/v1/training/start", json=_payload()).status_code == 200
            assert row.gates.reached("run")
            out["unknown_id"] = _answer(client.post(f"/v1/snapshots/{UNKNOWN_ID}/restore"))
            out["real_id"] = _answer(client.post(f"/v1/snapshots/{sid}/restore"))
    finally:
        row.close()
    return out


def row_start_in_window(scratch: Path) -> dict[str, Any]:
    second = (("emit", "training_start"), ("gate", "old"), ("emit", "training_end"))
    row = Row(scratch, "S", (ONE_EPOCH, second), (ONE_EPOCH,))
    out: dict[str, Any] = {"row": "S a start in the stop window"}
    try:
        with TestClient(row.app) as client:
            _complete_first_run(client, row)
            assert client.post("/v1/training/start", json=_payload()).status_code == 200
            assert row.gates.reached("old")
            client.post("/v1/training/stop")
            out["start"] = _answer(client.post("/v1/training/start", json=_payload()))
    finally:
        row.close()
    return out


_RUN_SCRIPTS = ((("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end"), ("emit", "training_end")), (("emit", "training_start"), ("gate", "beside"), ("emit", "training_end")))
_ACTIONS = {
    "status": {"action": "status"},
    "play": {"action": "play"},
    "pause": {"action": "pause"},
    "seek": {"action": "seek", "time_index": 0},
    "speed": {"action": "speed", "value": 2},
    "range": {"action": "range", "start": 0, "end": 1},
    "bogus": {"action": "bogus"},
    "stop": {"action": "stop"},
}


def row_replay_race(scratch: Path, load: str, action: str) -> dict[str, Any]:
    row = Row(scratch, f"R-{load}-{action}", (ONE_EPOCH,), _RUN_SCRIPTS)
    out: dict[str, Any] = {"row": f"R replay, {load}, start, replay/control {action}, start"}
    try:
        with TestClient(row.app) as client:
            sid = _complete_first_run(client, row)
            out["replay"] = _answer(client.post(f"/v1/snapshots/{sid}/replay"))
            out["load"] = _answer(client.post(f"/v1/snapshots/{sid}/{load}"))
            out["start"] = _answer(client.post("/v1/training/start", json=_payload()))
            assert row.gates.reached("run")
            out["control"] = _answer(client.post(f"/v1/snapshots/{sid}/replay/control", json=_ACTIONS[action]))
            out["status_after_control"] = _status(client)
            out["second_start"] = _answer(client.post("/v1/training/start", json=_payload()))
            if out["second_start"]["code"] == 200:
                out["second_fit_parked"] = row.gates.reached("beside")
            out["peak_fits"] = _peak()
    finally:
        row.close()
    return out


def row_replay_restore_stop(scratch: Path) -> dict[str, Any]:
    row = Row(scratch, "R-restore-stop", (ONE_EPOCH,), (ONE_EPOCH,))
    out: dict[str, Any] = {"row": "R replay, restore, replay/control stop"}
    try:
        with TestClient(row.app) as client:
            sid = _complete_first_run(client, row)
            client.post(f"/v1/snapshots/{sid}/replay")
            out["restore"] = _answer(client.post(f"/v1/snapshots/{sid}/restore"))
            out["control_stop"] = _answer(client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "stop"}))
            out["status_after"] = _status(client)
    finally:
        row.close()
    return out


def _ws_send(ws, message: dict[str, Any]) -> dict[str, Any]:
    ws.send_json(message)
    while True:
        frame = ws.receive_json()
        if frame.get("type") == "command_response":
            data = frame["data"]
            return {key: data.get(key) for key in ("command", "status", "error", "code", "command_id")}


def row_ws_race(scratch: Path) -> dict[str, Any]:
    row = Row(scratch, "WS-race", (ONE_EPOCH,), _RUN_SCRIPTS, ws=True)
    out: dict[str, Any] = {"row": "WS replay and retrain over HTTP, start over /ws/control, replay stop over HTTP, start over /ws/control"}
    try:
        with TestClient(row.app) as client:
            sid = _complete_first_run(client, row)
            client.post(f"/v1/snapshots/{sid}/replay")
            client.post(f"/v1/snapshots/{sid}/retrain")
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()  # connection_established
                out["ws_start_1"] = _ws_send(ws, {"command": "start", "command_id": "s1"})
                assert row.gates.reached("run")
                out["http_replay_stop"] = _answer(client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "stop"}))
                out["ws_start_2"] = _ws_send(ws, {"command": "start", "command_id": "s2"})
                if out["ws_start_2"]["status"] == "success":
                    out["second_fit_parked"] = row.gates.reached("beside")
            out["peak_fits"] = _peak()
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()
                out["unknown_commands"] = {name: _ws_send(ws, {"command": name}) for name in ("replay", "replay_control", "stop_replay", "restore", "retrain", "load_snapshot", "attach_model")}
    finally:
        row.close()
    return out


def row_ws_window(scratch: Path) -> dict[str, Any]:
    second = (("emit", "training_start"), ("gate", "old"), ("emit", "training_end"))
    row = Row(scratch, "WS-window", (ONE_EPOCH, second), (ONE_EPOCH,), ws=True)
    out: dict[str, Any] = {"row": "WS /ws/control answers in the stop window"}
    try:
        with TestClient(row.app) as client:
            _complete_first_run(client, row)
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()
                out["start_1"] = _ws_send(ws, {"command": "start", "command_id": "s1"})
                assert row.gates.reached("old")
                out["stop"] = _ws_send(ws, {"command": "stop", "command_id": "t1"})
                out["start_in_window"] = _ws_send(ws, {"command": "start", "command_id": "s2"})
                out["reset"] = _ws_send(ws, {"command": "reset", "command_id": "r1"})
                out["start_after_reset"] = _ws_send(ws, {"command": "start", "command_id": "s3"})
                row.gates.open("old")
                assert row.mgr.join(timeout=WAIT)
                out["start_once_ended"] = _ws_send(ws, {"command": "start", "command_id": "s4"})
    finally:
        row.close()
    return out


def row_python_api(scratch: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    running = (("emit", "training_start"), ("gate", "run"), ("emit", "training_end"))
    # stop_replay() during a run, with no replay at all
    row = Row(scratch, "PY-stop-replay-run", (running,))
    try:
        row.mgr.start_training(*_zeros())
        assert row.gates.reached("run")
        before = row.mgr.get_status()
        after = row.mgr.stop_replay()
        rows.append({"row": "PY stop_replay() during a run", "before": [before["state_machine"]["status"], before["monitor"]["status"], before["monitor"]["phase"]], "after": [after["state_machine"]["status"], after["monitor"]["status"], after["monitor"]["phase"]]})
    finally:
        row.close()
    # stop_replay() from INVESTIGATING
    row = Row(scratch, "PY-stop-replay-investigating", (ONE_EPOCH,), (ONE_EPOCH,))
    try:
        row.mgr.start_training(*_zeros())
        assert row.mgr.join(timeout=WAIT)
        sid = row.mgr.save_snapshot()["id"]
        before = row.mgr.load_snapshot(sid)
        after = row.mgr.stop_replay()
        rows.append({"row": "PY stop_replay() from INVESTIGATING", "before": [before["state_machine"]["status"], before["monitor"]["status"], before["monitor"]["phase"]], "after": [after["state_machine"]["status"], after["monitor"]["status"], after["monitor"]["phase"]]})
    finally:
        row.close()
    # get_replay_state() after each load that follows a replay
    for load in ("load_snapshot", "resume_from_snapshot", "restore_for_retrain"):
        row = Row(scratch, f"PY-replay-state-{load}", (ONE_EPOCH,), (ONE_EPOCH,))
        try:
            row.mgr.start_training(*_zeros())
            assert row.mgr.join(timeout=WAIT)
            sid = row.mgr.save_snapshot()["id"]
            row.mgr.start_replay(sid)
            getattr(row.mgr, load)(sid)
            rows.append({"row": f"PY get_replay_state() after replay then {load}", "replay_state_is_none": row.mgr.get_replay_state() is None})
        finally:
            row.close()
    # attach_model and each load method in the stop window
    second = (("emit", "training_start"), ("gate", "old"), ("emit", "training_end"))
    for call in ("attach_model", "load_snapshot", "resume_from_snapshot", "start_replay", "restore_for_retrain"):
        row = Row(scratch, f"PY-window-{call}", (ONE_EPOCH, second), (ONE_EPOCH,))
        try:
            row.mgr.start_training(*_zeros())
            assert row.mgr.join(timeout=WAIT)
            sid = row.mgr.save_snapshot()["id"]
            row.mgr.start_training(*_zeros())
            assert row.gates.reached("old")
            row.mgr.stop_training()
            try:
                if call == "attach_model":
                    getattr(row.mgr, call)(GatedModel(row.gates))
                else:
                    getattr(row.mgr, call)(sid)
                outcome = "accepted"
            except RuntimeError as exc:
                outcome = f"RuntimeError: {exc}"
            rows.append({"row": f"PY {call}() in the stop window", "outcome": outcome})
        finally:
            row.close()
    return rows


def row_frames_seek(scratch: Path) -> dict[str, Any]:
    row = Row(scratch, "F-seek", (ONE_EPOCH,), _RUN_SCRIPTS)
    out: dict[str, Any] = {"row": "F replay, retrain, start, the leftover session's seek: replay frames in the sink"}
    try:
        sid_mgr = row.mgr
        sid_mgr.start_training(*_zeros())
        assert sid_mgr.join(timeout=WAIT)
        sid = sid_mgr.save_snapshot()["id"]
        sid_mgr.start_replay(sid)
        sid_mgr.restore_for_retrain(sid)
        sid_mgr.start_training(*_zeros())
        assert row.gates.reached("run")
        frames: list[dict[str, Any]] = []
        sid_mgr.set_frame_sink(frames.append)
        try:
            sid_mgr.replay_control("seek", time_index=0)
            out["seek"] = "accepted"
        except RuntimeError as exc:
            out["seek"] = f"RuntimeError: {exc}"
        out["replay_frames"] = sum(1 for frame in frames if (frame.get("data") or {}).get("replay") is True)
        out["state_machine"] = sid_mgr.get_status()["state_machine"]["status"]
    finally:
        row.close()
    return out


def row_frames_after_a_load(scratch: Path, load: str, window: float) -> dict[str, Any]:
    row = Row(scratch, f"F-play-{load}", (FIFTY_EPOCHS,), (FIFTY_EPOCHS,))
    out: dict[str, Any] = {"row": f"F a playing replay, then {load} with no run after it: replay frames after the load ({window} s window)"}
    lock = threading.Lock()
    state = {"after": False, "before_count": 0, "after_count": 0}
    first_frame = threading.Event()
    frame_after = threading.Event()

    def sink(frame: dict[str, Any]) -> None:
        if (frame.get("data") or {}).get("replay") is not True:
            return
        with lock:
            if state["after"]:
                state["after_count"] += 1
                frame_after.set()
            else:
                state["before_count"] += 1
                if state["before_count"] >= 2:
                    first_frame.set()

    try:
        mgr = row.mgr
        mgr.start_training(*_zeros())
        assert mgr.join(timeout=WAIT)
        sid = mgr.save_snapshot()["id"]
        mgr.set_frame_sink(sink)
        mgr.start_replay(sid)
        mgr.replay_control("speed", value=10)
        mgr.replay_control("play")
        out["playing_before_the_load"] = first_frame.wait(timeout=WAIT)
        with lock:
            state["after"] = True
        started = time.monotonic()
        out["load"] = getattr(mgr, load)(sid)["state_machine"]["status"]
        out["frame_after_the_load"] = frame_after.wait(timeout=window)
        out["waited_seconds"] = round(time.monotonic() - started, 3)
        with lock:
            out["replay_frames_after_the_load"] = state["after_count"]
        out["replay_state_is_none"] = mgr.get_replay_state() is None
    finally:
        row.close()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch dir in a repo tmp/ (snapshot dirs go here)")
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    manager_file = Path(manager_module.__file__).resolve()
    header = {
        "label": args.label,
        "python": sys.version,
        "executable": sys.executable,
        "base_prefix": sys.base_prefix,
        "package": str(Path(juniper_service_core.__file__).resolve()),
        "manager_sha256": hashlib.sha256(manager_file.read_bytes()).hexdigest(),
    }
    rows: list[dict[str, Any]] = []
    errors = 0
    plan: list[tuple[str, Any]] = []
    for route in ROUTES:
        for ending in ("stop", "reset"):
            for fit_end in ("unwind", "raise"):
                plan.append((f"W {route} {ending} {fit_end}", lambda r=route, e=ending, f=fit_end: row_window(args.scratch, r, e, f)))
    plan.append(("A", lambda: row_active(args.scratch)))
    plan.append(("S", lambda: row_start_in_window(args.scratch)))
    for load in ("retrain", "resume"):
        for action in _ACTIONS:
            plan.append((f"R {load} {action}", lambda lo=load, ac=action: row_replay_race(args.scratch, lo, ac)))
    plan.append(("R restore stop", lambda: row_replay_restore_stop(args.scratch)))
    plan.append(("WS race", lambda: row_ws_race(args.scratch)))
    plan.append(("WS window", lambda: row_ws_window(args.scratch)))
    plan.append(("PY", lambda: row_python_api(args.scratch)))
    plan.append(("F seek", lambda: row_frames_seek(args.scratch)))
    for load in ("load_snapshot", "resume_from_snapshot", "restore_for_retrain"):
        plan.append((f"F play {load}", lambda lo=load: row_frames_after_a_load(args.scratch, lo, 1.5)))
    for name, run in plan:
        try:
            result = run()
            rows.extend(result if isinstance(result, list) else [result])
        except Exception:  # noqa: BLE001 - a probe row records its own failure and the probe carries on
            errors += 1
            rows.append({"row": name, "error": traceback.format_exc()})
    args.json_out.write_text(json.dumps({"header": header, "rows": rows, "errors": errors}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(header))
    print(f"rows={len(rows)} errors={errors}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
