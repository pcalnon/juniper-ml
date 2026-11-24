#!/usr/bin/env python3
"""
Measure juniper-cascor's pause / stop / start overlap: a pause whose FSM check passes just before a stop and a start land.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2: the Overtoad's ruling of 2026-11-13, "Fix it + document")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#756, "What this does not close", seventh item; a successor of probe g in
         util/ad-hoc/2026-11-12_flood4r2_r17-cascor_adjacent_probes.py (kept unedited)

Drives the real ``TrainingLifecycleManager`` of the ``--src`` tree with a gated stub ``model.fit``
(events and gates; every wait is bounded), so it needs no data service and spawns no candidate pool.

The overlap is made deterministic at the manager's own seams, with no sleep deciding it:
``state_machine.is_started`` is wrapped so that, when ``pause_training`` calls it, the pause is held
between its FSM check and whatever follows the check until a stop and a start have landed. When the
tree has a ``_pause_lock`` (the fix), the hold also ends as soon as another thread waits on that lock,
so a start the fix makes wait for the pause cannot deadlock the probe. The pause gate is replaced by a
watched ``threading.Event`` that reports when a fit waits on it while it is closed: that is how a held
run is told from one that passed its checkpoint, without a timer.

Scenarios (one JSON object each, on stdout and in ``--out``):
  seams/<way-out>  the manager driven from threads: run 0 parked in its fit; the pause held after its
                   check; stop; start (run 1 queued); the pause let go. Then run 0 is released, run 1
                   enters and is released, and the probe reports whether run 1 is held at its first
                   checkpoint, what the status fields read, and what <way-out> answers and does:
                   resume | pause-then-resume | stop | reset | start.
  http/<way-out>   the same overlap through the real app (TestClient): the pause over /ws/control
                   (the only verb path that runs on a worker thread, through asyncio.to_thread), stop,
                   start and every way out over the REST routes, with their status codes and bodies.
  rest-only        all three over REST: the REST pause is held inside its check for a bounded time while
                   a stop is sent over REST from another thread; reports whether that stop was served
                   while the pause was held (the routes call the lifecycle on the server's event loop).
  swap-timeout     over REST only: a live swap whose 10 s join on the old fit times out (forced at the
                   old future's ``result``; the fetch and the snapshot writes are stubbed) submits the
                   swapped run behind the still-running old fit, so the FSM still reads STARTED and a
                   plain REST pause is accepted for the old fit. Reports whether the swapped run is then
                   held at its first checkpoint, and what resume and pause-then-resume answer.
  window           the width of the window on an uncontended pause: the time from ``is_started()``
                   returning inside ``pause_training`` to the gate's ``clear()``, over many calls.
  stress           the overlap with no hook at all: a pause on one thread, a stop then a start on
                   another, released together by a barrier, with ``sys.setswitchinterval(1e-6)``,
                   ``--stress-trials`` times (the run the start queues is not executed). Counted: the
                   trials whose pause answered "paused" although its FSM transition was refused, and
                   the trials that left the gate closed under a STOPPED FSM after the start (the
                   condition that holds the queued run at its first checkpoint).

Usage:
  2026-11-15_flood4r2_r32-cascor_overlap_probe.py --src <cascor src dir> --snapshots <fresh dir> --out <json file>
        [--scenarios seams,http,rest-only,swap-timeout,window,stress] [--stress-trials N]
Exit: 1 when any seams/http scenario found run 1 held at its first checkpoint or the stress run found
the closed-gate condition (the defect reproduced); 0 when none did; 2 when a scenario raised.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import threading
import time
import traceback
from pathlib import Path

WAIT = 5.0
GATE_TIMEOUT = 20.0
RUNS = 4
WAYS_OUT = ("resume", "pause-then-resume", "stop", "reset", "start")
AUTH_ENV = ("JUNIPER_CASCOR_API_KEYS", "JUNIPER_CASCOR_API_KEYS_FILE", "JUNIPER_CASCOR_REQUIRE_AUTH", "JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS")
CANOPY_ORIGIN = "http://localhost:8050"


class _WatchedGate(threading.Event):
    """The manager's pause gate, reporting when a fit waits on it while it is closed."""

    def __init__(self, open_now: bool) -> None:
        self.held_a_fit = threading.Event()
        super().__init__()
        if open_now:
            self.set()

    def wait(self, timeout=None):
        if not self.is_set():
            self.held_a_fit.set()
        return super().wait(timeout)


class _Run:
    """The gates of one call of the stub fit."""

    def __init__(self) -> None:
        self.parked = threading.Event()
        self.release = threading.Event()
        self.ran_on = threading.Event()


class _GatedFit:
    """Stands in for ``CascorModel.fit``: training_start, park, then one checkpointed epoch_end, training_end."""

    def __init__(self, event_cls) -> None:
        self.event_cls = event_cls
        self.runs = [_Run() for _ in range(RUNS)]
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        with self._lock:
            index = self.calls
            self.calls += 1
        run = self.runs[index]
        on_event(self.event_cls("training_start", {"n_samples": int(x.shape[0])}, 0))
        run.parked.set()
        run.release.wait(timeout=GATE_TIMEOUT)
        on_event(self.event_cls("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, 1))
        run.ran_on.set()
        on_event(self.event_cls("training_end", {"metrics": {}}, 2))

    def release_all(self) -> None:
        for run in self.runs:
            run.release.set()


class _SignallingLock:
    """Wraps the fix's ``_pause_lock``: when a second thread has to wait for it, the pause hold lets go."""

    def __init__(self, real, hold: "_PauseHold") -> None:
        self._real = real
        self._hold = hold

    def __enter__(self):
        if not self._real.acquire(blocking=False):
            self._hold.lock_contended.set()
            self._hold.may_go.set()
            self._real.acquire()
        return self

    def __exit__(self, *exc_info):
        self._real.release()
        return False


class _PauseHold:
    """Hold ``pause_training`` right after its FSM check until a start has landed (or waits on the fix's lock)."""

    def __init__(self, mgr) -> None:
        self.mgr = mgr
        self.sm = mgr.state_machine
        self.real_is_started = self.sm.is_started
        self.checked = threading.Event()
        self.may_go = threading.Event()
        self.lock_contended = threading.Event()
        self.real_lock = getattr(mgr, "_pause_lock", None)
        self.sm.is_started = self._is_started
        if self.real_lock is not None:
            mgr._pause_lock = _SignallingLock(self.real_lock, self)

    def _is_started(self) -> bool:
        answer = self.real_is_started()
        if sys._getframe(1).f_code.co_name == "pause_training" and not self.checked.is_set():
            self.checked.set()
            self.may_go.wait(timeout=GATE_TIMEOUT)
        return answer

    def remove(self) -> None:
        self.may_go.set()
        self.sm.is_started = self.real_is_started
        if self.real_lock is not None:
            self.mgr._pause_lock = self.real_lock


def _xy(torch):
    x = torch.randn(8, 2)
    y = torch.zeros(8, 2)
    y[:4, 0] = 1
    y[4:, 1] = 1
    return x, y


def _answer(request) -> str:
    try:
        result = request()
        return f"accepted: {result.get('status') if isinstance(result, dict) else result}"
    except (RuntimeError, ValueError) as exc:
        return f"refused: {type(exc).__name__}: {exc}"


def _fields(mgr) -> dict:
    status = mgr.get_status()
    return {
        "state_machine.status": status["state_machine"]["status"],
        "training_state.status": status["training_state"].get("status"),
        "training_active": status["training_active"],
        "pause_gate_open": mgr._pause_event.is_set(),
    }


def _settle(future) -> str:
    try:
        future.result(timeout=WAIT)
        return "returned"
    except TimeoutError:
        return "STILL RUNNING after the bounded wait"
    except Exception as exc:  # a failed fit is a finding to report, not an error of the probe
        return f"raised {type(exc).__name__}: {exc}"


def _held_or_passed(fit: _GatedFit, gate: _WatchedGate, index: int) -> str:
    """Wait (bounded) until run ``index`` either passes its first checkpoint or waits on the closed gate."""
    deadline = time.monotonic() + WAIT
    while time.monotonic() < deadline:
        if fit.runs[index].ran_on.is_set():
            return "passed its first checkpoint"
        if gate.held_a_fit.is_set():
            return "HELD at its first checkpoint by the closed pause gate"
        fit.runs[index].ran_on.wait(timeout=0.01)
    return "neither within the bounded wait"


def _counted_hook(module, counted: list):
    real = module.inc_training_session_completed

    def counted_fn(status):
        counted.append(status)
        return real(status)

    module.inc_training_session_completed = counted_fn
    return real


def _seams(module, torch, event_cls, way_out: str) -> dict:
    counted: list = []
    real_counter = _counted_hook(module, counted)
    mgr = module.TrainingLifecycleManager()
    mgr.create_network(input_size=2, output_size=2)
    fit = _GatedFit(event_cls)
    mgr.model.fit = fit
    gate = _WatchedGate(open_now=mgr._pause_event.is_set())
    mgr._pause_event = gate
    holds: list = []
    report: dict = {"scenario": f"seams/{way_out}", "fix_lock_present": hasattr(mgr, "_pause_lock")}
    try:
        x, y = _xy(torch)
        mgr.start_training(X=x, y=y)
        old_future = mgr._training_future
        assert fit.runs[0].parked.wait(WAIT), "run 0 never entered its fit"
        report["before"] = _fields(mgr)
        hold = _PauseHold(mgr)
        holds.append(hold)
        pause_answer: dict = {}
        pauser = threading.Thread(target=lambda: pause_answer.update(pause=_answer(mgr.pause_training)), daemon=True)
        pauser.start()
        assert hold.checked.wait(WAIT), "the pause never reached its FSM check"
        report["pause_check_saw"] = "STARTED"
        report["stop"] = _answer(mgr.stop_training)
        report["after_the_stop"] = _fields(mgr)
        x2, y2 = _xy(torch)
        report["start"] = _answer(lambda: mgr.start_training(X=x2, y=y2))
        report["start_waited_on_the_pause_lock"] = hold.lock_contended.is_set()
        new_future = mgr._training_future
        hold.may_go.set()
        pauser.join(WAIT)
        report["pause"] = pause_answer.get("pause", "NO ANSWER within the bounded wait")
        report["after_the_pause"] = _fields(mgr)
        hold.remove()
        fit.runs[0].release.set()
        report["run_0"] = _settle(old_future)
        report["run_0_passed_its_checkpoint"] = fit.runs[0].ran_on.is_set()
        report["run_1_entered_its_fit"] = fit.runs[1].parked.wait(WAIT)
        report["while_run_1_is_parked"] = _fields(mgr)
        fit.runs[1].release.set()
        outcome = _held_or_passed(fit, gate, 1)
        report["run_1"] = outcome
        report["status_then"] = _fields(mgr)
        report["held"] = outcome.startswith("HELD")
        if report["held"]:
            report["way_out"] = _way_out_seams(mgr, fit, gate, new_future, way_out, torch)
        else:
            report["run_1_result"] = _settle(new_future)
        report["counted"] = list(counted)
        report["at_the_end"] = _fields(mgr)
        return report
    finally:
        for pending in holds:  # remove() is idempotent
            pending.remove()
        fit.release_all()
        mgr._pause_event.set()
        mgr.shutdown()
        module.inc_training_session_completed = real_counter


def _way_out_seams(mgr, fit, gate, new_future, way_out: str, torch) -> dict:
    result: dict = {"way_out": way_out}
    if way_out == "resume":
        result["resume"] = _answer(mgr.resume_training)
        result["after"] = _fields(mgr)
        result["run_1_still_held"] = not gate.is_set() and not fit.runs[1].ran_on.is_set()
        result["cleanup_reset"] = _answer(mgr.reset)
        result["run_1_result"] = _settle(new_future)
    elif way_out == "pause-then-resume":
        result["pause"] = _answer(mgr.pause_training)
        result["after_the_pause"] = _fields(mgr)
        result["resume"] = _answer(mgr.resume_training)
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.wait(WAIT)
        result["run_1_result"] = _settle(new_future)
        result["after"] = _fields(mgr)
    elif way_out == "stop":
        result["stop"] = _answer(mgr.stop_training)
        result["run_1_result"] = _settle(new_future)
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.is_set()
        result["after"] = _fields(mgr)
    elif way_out == "reset":
        result["reset"] = _answer(mgr.reset)
        result["run_1_result"] = _settle(new_future)
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.is_set()
        result["after"] = _fields(mgr)
    elif way_out == "start":
        x, y = _xy(torch)
        result["start"] = _answer(lambda: mgr.start_training(X=x, y=y))
        result["after"] = _fields(mgr)
        result["run_1_still_held"] = not gate.is_set() and not fit.runs[1].ran_on.is_set()
        result["cleanup_reset"] = _answer(mgr.reset)
        result["run_1_result"] = _settle(new_future)
    return result


def _status_fields(client) -> dict:
    data = client.get("/v1/training/status").json()["data"]
    return {
        "state_machine.status": data["state_machine"]["status"],
        "training_state.status": data["training_state"].get("status"),
        "training_active": data["training_active"],
    }


def _post(client, path: str, **kwargs) -> dict:
    response = client.post(path, **kwargs)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {"code": response.status_code, "body": body}


def _http(module, torch, event_cls, way_out: str) -> dict:
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.settings import Settings

    counted: list = []
    real_counter = _counted_hook(module, counted)
    app = create_app(Settings(auto_start=False))
    report: dict = {"scenario": f"http/{way_out}"}
    holds: list = []
    try:
        with TestClient(app) as client:
            assert client.post("/v1/network", json={"input_size": 2, "output_size": 2}).status_code == 200
            mgr = client.app.state.lifecycle
            report["fix_lock_present"] = hasattr(mgr, "_pause_lock")
            fit = _GatedFit(event_cls)
            mgr.model.fit = fit
            gate = _WatchedGate(open_now=mgr._pause_event.is_set())
            mgr._pause_event = gate
            x, y = _xy(torch)
            payload = {"inline_data": {"train_x": x.tolist(), "train_y": y.tolist()}}
            try:
                report["start_0"] = _post(client, "/v1/training/start", json=payload)["code"]
                old_future = mgr._training_future
                assert fit.runs[0].parked.wait(WAIT), "run 0 never entered its fit"
                hold = _PauseHold(mgr)
                holds.append(hold)
                # The default /ws/control Origin allowlist is canopy's own origin, which canopy sends.
                with client.websocket_connect("/ws/control", headers={"origin": CANOPY_ORIGIN}) as ws:
                    report["ws_hello"] = ws.receive_json().get("type")
                    ws.send_text(json.dumps({"command": "pause", "command_id": "probe-pause"}))
                    assert hold.checked.wait(WAIT), "the /ws/control pause never reached its FSM check"
                    report["stop"] = _post(client, "/v1/training/stop")
                    report["status_after_the_stop"] = _status_fields(client)
                    report["start_1"] = _post(client, "/v1/training/start", json=payload)
                    report["start_waited_on_the_pause_lock"] = hold.lock_contended.is_set()
                    new_future = mgr._training_future
                    hold.may_go.set()
                    report["ws_pause_ack"] = ws.receive_json()
                hold.remove()
                report["status_after_the_pause"] = _status_fields(client)
                fit.runs[0].release.set()
                report["run_0"] = _settle(old_future)
                report["run_0_passed_its_checkpoint"] = fit.runs[0].ran_on.is_set()
                report["run_1_entered_its_fit"] = fit.runs[1].parked.wait(WAIT)
                fit.runs[1].release.set()
                outcome = _held_or_passed(fit, gate, 1)
                report["run_1"] = outcome
                report["status_then"] = _status_fields(client)
                report["held"] = outcome.startswith("HELD")
                if report["held"]:
                    report["way_out"] = _way_out_http(client, mgr, fit, gate, new_future, way_out, payload)
                else:
                    report["run_1_result"] = _settle(new_future)
                    report["status_at_the_end"] = _status_fields(client)
                report["counted"] = list(counted)
            finally:
                for pending in holds:  # remove() is idempotent
                    pending.remove()
                fit.release_all()
                mgr._pause_event.set()
        return report
    finally:
        module.inc_training_session_completed = real_counter


def _way_out_http(client, mgr, fit, gate, new_future, way_out: str, payload: dict) -> dict:
    result: dict = {"way_out": way_out}
    if way_out == "resume":
        result["resume"] = _post(client, "/v1/training/resume")
        result["status"] = _status_fields(client)
        result["run_1_still_held"] = not gate.is_set() and not fit.runs[1].ran_on.is_set()
        result["cleanup_reset"] = _post(client, "/v1/training/reset")["code"]
        result["run_1_result"] = _settle(new_future)
    elif way_out == "pause-then-resume":
        result["pause"] = _post(client, "/v1/training/pause")
        result["status_after_the_pause"] = _status_fields(client)
        result["resume"] = _post(client, "/v1/training/resume")
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.wait(WAIT)
        result["run_1_result"] = _settle(new_future)
        result["status"] = _status_fields(client)
    elif way_out == "stop":
        result["stop"] = _post(client, "/v1/training/stop")
        result["run_1_result"] = _settle(new_future)
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.is_set()
        result["status"] = _status_fields(client)
    elif way_out == "reset":
        result["reset"] = _post(client, "/v1/training/reset")
        result["run_1_result"] = _settle(new_future)
        result["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.is_set()
        result["status"] = _status_fields(client)
    elif way_out == "start":
        result["start"] = _post(client, "/v1/training/start", json=payload)
        result["status"] = _status_fields(client)
        result["run_1_still_held"] = not gate.is_set() and not fit.runs[1].ran_on.is_set()
        result["cleanup_reset"] = _post(client, "/v1/training/reset")["code"]
        result["run_1_result"] = _settle(new_future)
    return result


def _rest_only(module, torch, event_cls, hold_seconds: float) -> dict:
    """All three over REST: with the pause held inside its check, is a stop sent from another thread served?"""
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.settings import Settings

    app = create_app(Settings(auto_start=False))
    report: dict = {"scenario": "rest-only", "hold_seconds": hold_seconds}
    holds: list = []
    with TestClient(app) as client:
        assert client.post("/v1/network", json={"input_size": 2, "output_size": 2}).status_code == 200
        mgr = client.app.state.lifecycle
        report["fix_lock_present"] = hasattr(mgr, "_pause_lock")
        fit = _GatedFit(event_cls)
        mgr.model.fit = fit
        x, y = _xy(torch)
        payload = {"inline_data": {"train_x": x.tolist(), "train_y": y.tolist()}}
        try:
            report["start_0"] = _post(client, "/v1/training/start", json=payload)["code"]
            assert fit.runs[0].parked.wait(WAIT), "run 0 never entered its fit"
            hold = _PauseHold(mgr)
            holds.append(hold)
            answers: dict = {}
            stop_done = threading.Event()
            pauser = threading.Thread(target=lambda: answers.update(pause=_post(client, "/v1/training/pause")), daemon=True)
            pauser.start()
            assert hold.checked.wait(WAIT), "the REST pause never reached its FSM check"

            def _stop() -> None:
                answers["stop"] = _post(client, "/v1/training/stop")
                stop_done.set()

            stopper = threading.Thread(target=_stop, daemon=True)
            stopper.start()
            report["stop_served_while_the_pause_was_held"] = stop_done.wait(hold_seconds)
            hold.may_go.set()
            pauser.join(WAIT)
            stopper.join(WAIT)
            hold.remove()
            report["pause"] = answers.get("pause")
            report["stop"] = answers.get("stop")
            report["status_after_both"] = _status_fields(client)
        finally:
            for pending in holds:  # remove() is idempotent
                pending.remove()
            fit.release_all()
            mgr._pause_event.set()
    return report


def _swap_timeout(module, torch, event_cls) -> dict:
    """Over REST only: a live swap whose join on the old fit timed out, then a plain pause while the old fit unwinds."""
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.settings import Settings

    counted: list = []
    real_counter = _counted_hook(module, counted)
    app = create_app(Settings(auto_start=False))
    report: dict = {"scenario": "swap-timeout"}
    try:
        with TestClient(app) as client:
            assert client.post("/v1/network", json={"input_size": 2, "output_size": 2}).status_code == 200
            mgr = client.app.state.lifecycle
            report["fix_lock_present"] = hasattr(mgr, "_pause_lock")
            fit = _GatedFit(event_cls)
            mgr.model.fit = fit
            gate = _WatchedGate(open_now=mgr._pause_event.is_set())
            mgr._pause_event = gate
            x, y = _xy(torch)
            payload = {"inline_data": {"train_x": x.tolist(), "train_y": y.tolist()}}
            try:
                report["experimental_on"] = _post(client, "/v1/admin/experimental_functions", json={"enabled": True})["code"]
                report["start_0"] = _post(client, "/v1/training/start", json=payload)["code"]
                old_future = mgr._training_future
                assert fit.runs[0].parked.wait(WAIT), "run 0 never entered its fit"
                real_result = old_future.result
                joins: list = []

                def _join_times_out(timeout=None):
                    if not joins:  # the swap's join only: the old fit is mid-round and reaches no checkpoint in time
                        joins.append(timeout)
                        raise TimeoutError("forced: the swap's join on the old fit timed out")
                    return real_result(timeout)

                def _fetch(**_cfg) -> None:
                    mgr._train_x, mgr._train_y = _xy(torch)

                old_future.result = _join_times_out
                mgr._reload_dataset = _fetch
                mgr.save_snapshot = lambda **_kwargs: {"id": "probe-snap"}
                swap = _post(client, "/v1/training/dataset/live", json={"dataset_type": "spirals"})
                report["swap"] = {"code": swap["code"], "status": swap["body"].get("data", {}).get("status") if isinstance(swap["body"], dict) else swap["body"]}
                report["swap_join_timeouts"] = joins
                swapped_future = mgr._training_future
                report["status_after_the_swap"] = _status_fields(client)
                report["pause"] = _post(client, "/v1/training/pause")
                report["status_after_the_pause"] = _status_fields(client)
                fit.runs[0].release.set()
                report["run_0"] = _settle(old_future)
                report["run_0_passed_its_checkpoint"] = fit.runs[0].ran_on.is_set()
                report["run_1_entered_its_fit"] = fit.runs[1].parked.wait(WAIT)
                fit.runs[1].release.set()
                outcome = _held_or_passed(fit, gate, 1)
                report["run_1"] = outcome
                report["status_then"] = _status_fields(client)
                report["held"] = outcome.startswith("HELD")
                if report["held"]:
                    report["resume"] = _post(client, "/v1/training/resume")
                    report["run_1_still_held_after_resume"] = not gate.is_set() and not fit.runs[1].ran_on.is_set()
                    report["pause_then_resume"] = [_post(client, "/v1/training/pause")["code"], _post(client, "/v1/training/resume")["code"]]
                    report["run_1_passed_its_checkpoint"] = fit.runs[1].ran_on.wait(WAIT)
                report["run_1_result"] = _settle(swapped_future)
                report["status_at_the_end"] = _status_fields(client)
                report["counted"] = list(counted)
            finally:
                fit.release_all()
                mgr._pause_event.set()
        return report
    finally:
        module.inc_training_session_completed = real_counter


class _StampedGate(threading.Event):
    """A pause gate that stamps each ``clear()``."""

    def __init__(self) -> None:
        self.cleared_at: list = []
        super().__init__()
        self.set()

    def clear(self) -> None:
        self.cleared_at.append(time.perf_counter_ns())
        super().clear()


def _window(module, calls: int) -> dict:
    """The time from the check returning inside pause_training to the gate's clear(), uncontended."""
    from api.lifecycle.state_machine import Command

    mgr = module.TrainingLifecycleManager()
    sm = mgr.state_machine
    real_is_started = sm.is_started
    checked_at: list = []

    def _stamped_is_started() -> bool:
        answer = real_is_started()
        if sys._getframe(1).f_code.co_name == "pause_training":
            checked_at.append(time.perf_counter_ns())
        return answer

    gate = _StampedGate()
    mgr._pause_event = gate
    sm.is_started = _stamped_is_started
    try:
        assert sm.handle_command(Command.START)
        for _ in range(calls):
            mgr.pause_training()
            mgr.resume_training()
    finally:
        sm.is_started = real_is_started
        mgr.shutdown()
    gaps = sorted(cleared - checked for checked, cleared in zip(checked_at, gate.cleared_at))
    overhead = []
    for _ in range(calls):
        first = time.perf_counter_ns()
        overhead.append(time.perf_counter_ns() - first)
    overhead.sort()
    return {
        "scenario": "window",
        "calls": calls,
        "pairs": len(gaps),
        "check_to_clear_ns": {"median": statistics.median(gaps), "p99": gaps[int(len(gaps) * 0.99) - 1], "min": gaps[0], "max": gaps[-1]},
        "stamp_pair_overhead_ns_median": statistics.median(overhead),
        "switch_interval_s": sys.getswitchinterval(),
    }


def _stress(module, torch, trials: int) -> dict:
    """The overlap with no hook: count how often it closes the gate under a start, at a 1 us switch interval."""
    from api.lifecycle.state_machine import Command

    mgr = module.TrainingLifecycleManager()
    mgr.create_network(input_size=2, output_size=2)
    mgr._run_training = lambda *args, **kwargs: None  # the queued run is not executed: only the gate is judged
    sm = mgr.state_machine
    real_handle = sm.handle_command
    pause_results: list = []

    def _recording_handle(command):
        accepted = real_handle(command)
        if command is Command.PAUSE:
            pause_results.append(accepted)
        return accepted

    sm.handle_command = _recording_handle
    x, y = _xy(torch)
    tally = {"pause_refused": 0, "pause_accepted_and_paused": 0, "pause_answered_paused_but_its_transition_was_refused": 0, "gate_left_closed_under_a_stopped_fsm_after_the_start": 0, "start_refused": 0}
    previous_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    started = time.monotonic()
    try:
        for _ in range(trials):
            real_handle(Command.RESET)
            real_handle(Command.START)
            mgr._pause_event.set()
            pause_results.clear()
            barrier = threading.Barrier(2)
            answers: dict = {}

            def _pauser() -> None:
                barrier.wait()
                answers["pause"] = _answer(mgr.pause_training)

            def _stop_then_start() -> None:
                barrier.wait()
                mgr.stop_training()
                answers["start"] = _answer(lambda: mgr.start_training(X=x, y=y))

            threads = [threading.Thread(target=_pauser), threading.Thread(target=_stop_then_start)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(WAIT)
            if answers.get("pause", "").startswith("refused"):
                tally["pause_refused"] += 1
            elif pause_results and pause_results[0]:
                tally["pause_accepted_and_paused"] += 1
            else:
                tally["pause_answered_paused_but_its_transition_was_refused"] += 1
            if not answers.get("start", "").startswith("accepted"):
                tally["start_refused"] += 1
            elif not mgr._pause_event.is_set() and sm.status.name == "STOPPED":
                tally["gate_left_closed_under_a_stopped_fsm_after_the_start"] += 1
    finally:
        sys.setswitchinterval(previous_interval)
        sm.handle_command = real_handle
        mgr._pause_event.set()
        mgr.shutdown()
    return {"scenario": "stress", "trials": trials, "switch_interval_s": 1e-6, "seconds": round(time.monotonic() - started, 1), "fix_lock_present": hasattr(mgr, "_pause_lock"), "tally": tally}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--src", required=True, type=Path, help="the cascor src/ tree to import")
    parser.add_argument("--snapshots", required=True, type=Path, help="a fresh directory for any snapshot a run writes")
    parser.add_argument("--out", required=True, type=Path, help="JSON file for the reports")
    parser.add_argument("--scenarios", default="seams,http,rest-only,swap-timeout,window,stress")
    parser.add_argument("--stress-trials", type=int, default=2000)
    parser.add_argument("--window-calls", type=int, default=20000)
    args = parser.parse_args()
    snapshots = args.snapshots.resolve()
    snapshots.mkdir(parents=True, exist_ok=True)
    os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = str(snapshots)
    os.environ.pop("JUNIPER_CASCOR_LOG_DIR", None)
    for name in AUTH_ENV:
        os.environ.pop(name, None)
    sys.path.insert(0, str(args.src.resolve()))

    import torch
    from juniper_model_core.events import TrainingEvent

    from api.lifecycle import manager as manager_module

    wanted = set(args.scenarios.split(","))
    reports = [{"manager_under_test": manager_module.__file__, "python": sys.version.split()[0], "executable": sys.executable}]
    jobs = []
    if "seams" in wanted:
        jobs.extend((f"seams/{way}", lambda way=way: _seams(manager_module, torch, TrainingEvent, way)) for way in WAYS_OUT)
    if "http" in wanted:
        jobs.extend((f"http/{way}", lambda way=way: _http(manager_module, torch, TrainingEvent, way)) for way in WAYS_OUT)
    if "rest-only" in wanted:
        jobs.append(("rest-only", lambda: _rest_only(manager_module, torch, TrainingEvent, 2.0)))
    if "swap-timeout" in wanted:
        jobs.append(("swap-timeout", lambda: _swap_timeout(manager_module, torch, TrainingEvent)))
    if "window" in wanted:
        jobs.append(("window", lambda: _window(manager_module, args.window_calls)))
    if "stress" in wanted:
        jobs.append(("stress", lambda: _stress(manager_module, torch, args.stress_trials)))
    broke = False
    reproduced = False
    for name, job in jobs:
        try:
            report = job()
        except Exception:  # report the scenario that broke and carry on with the rest
            broke = True
            report = {"scenario": name, "scenario_error": traceback.format_exc()}
        if report.get("held"):
            reproduced = True
        if report.get("scenario") == "stress" and report["tally"]["gate_left_closed_under_a_stopped_fsm_after_the_start"]:
            reproduced = True
        reports.append(report)
        print(json.dumps(report), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    if broke:
        return 2
    return 1 if reproduced else 0


if __name__ == "__main__":
    sys.exit(main())
