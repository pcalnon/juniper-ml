#!/usr/bin/env python3
"""Stop-then-start race probe: what a start sent right after a stop does to ServiceLifecycleManager.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); juniper-ml#2531, whose PR body lists what
             it left; juniper-service-core/tests/test_lifecycle_stop_then_start.py

Imports ``juniper_service_core`` from ``--service-core`` (a ``juniper-service-core`` directory:
``main``'s, or a fixed tree's) and ``juniper_model_core`` from ``--model-core``, and drives two
scenarios with a scripted model whose ``fit`` parks at named gates. Every wait is on a
``threading.Event`` with a deadline; nothing sleeps. One negative check (that a parked ``fit`` has
not moved) waits 0.5 s for something that must not happen.

- ``overlap``: start run 1, stop it while its ``fit`` is parked before its next event, start run 2
  at once. Records whether that start was accepted, how many ``fit`` calls were running at once,
  and, after run 1's ``fit`` is let go, whether its ``phase_change`` / ``epoch_end`` /
  ``training_end`` reached the manager's monitor and state machine while run 2 was current.
- ``pause_gate``: as above, then pause run 2, let run 1 reach its next event, and let run 2's
  ``fit`` return while paused. Records whether run 1's ``fit`` waited at the shared pause gate,
  whether run 2's paused completion released it with no command, whether its event landed in the
  completed run's monitor, and whether a third start was then accepted beside it.

Prints one JSON object. Exit status: 0 when the probe ran (whatever it observed), 2 when a setup
step failed (a gate never reached, a thread that did not end).

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_race_probe.py --service-core <dir> --model-core <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path
from typing import Any

_PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "phase_change": {"phase": "candidate"},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}


class ProbeError(Exception):
    """A setup step did not happen as designed, so no observation would mean anything."""


def _build_model_class(trainable_model: type, training_event: type, train_result: type, interrupted: type) -> type:
    """Define the scripted model against the imported model-core classes."""

    class GatedModel(trainable_model):
        def __init__(self, *scripts: tuple[tuple[str, str], ...]) -> None:
            self.task_type = "regression"
            self.random_seed = 0
            self.fits = 0
            self.peak = 0
            self.threads: list[threading.Thread] = []
            self.delivered: dict[int, list[str]] = {}
            self.interrupted: list[int] = []
            self.emitting: dict[str, threading.Event] = {}
            self._running = 0
            self._scripts = scripts
            self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
            self._lock = threading.Lock()

        def _gate(self, name: str) -> tuple[threading.Event, threading.Event]:
            with self._lock:
                return self._gates.setdefault(name, (threading.Event(), threading.Event()))

        def began(self, name: str) -> threading.Event:
            with self._lock:
                return self.emitting.setdefault(name, threading.Event())

        def reached(self, name: str, timeout: float = 5.0) -> bool:
            return self._gate(name)[1].wait(timeout)

        def open(self, name: str) -> None:
            self._gate(name)[0].set()

        def open_all(self) -> None:
            with self._lock:
                gates = [gate for gate, _ in self._gates.values()]
            for gate in gates:
                gate.set()

        def running_now(self) -> int:
            with self._lock:
                return self._running

        def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw):
            with self._lock:
                self.fits += 1
                call = self.fits
                script = self._scripts[call - 1] if call <= len(self._scripts) else ()
                self.threads.append(threading.current_thread())
                self.delivered[call] = []
                self._running += 1
                self.peak = max(self.peak, self._running)
            try:
                for kind, arg in script:
                    if kind == "emit" and on_event is not None:
                        self.began(f"{call}:{arg}").set()
                        on_event(training_event(arg, dict(_PAYLOADS[arg]), 0))
                        with self._lock:
                            self.delivered[call].append(arg)
                    elif kind == "gate":
                        gate, reached = self._gate(arg)
                        reached.set()
                        gate.wait(timeout=10.0)
            except interrupted:
                with self._lock:
                    self.interrupted.append(call)
                raise
            finally:
                with self._lock:
                    self._running -= 1
            return train_result(final_metrics={"mse": 0.25}, n_epochs=1)

        def predict(self, X, **kw):
            raise NotImplementedError

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

    return GatedModel


def _need(ok: bool, what: str) -> None:
    if not ok:
        raise ProbeError(what)


def _try_start(mgr: Any, X: Any, y: Any) -> dict[str, Any]:
    try:
        status = mgr.start_training(X, y)
    except RuntimeError as exc:
        return {"accepted": False, "error": str(exc)}
    return {"accepted": True, "status": status["state_machine"]["status"]}


def _snapshot(mgr: Any) -> dict[str, Any]:
    status = mgr.get_status()
    return {
        "state_machine": status["state_machine"],
        "monitor_status": status["monitor"].get("status"),
        "monitor_phase": status["monitor"].get("phase"),
        "history_len": len(mgr.get_metrics_history()),
    }


def _finish(model: Any, mgr: Any) -> None:
    model.open_all()
    mgr.shutdown()
    for thread in model.threads:
        thread.join(timeout=5.0)
        _need(not thread.is_alive(), "a fit thread did not end at cleanup")


def _overlap(manager_cls: type, model_cls: type, np: Any) -> dict[str, Any]:
    X, y = np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32)
    model = model_cls(
        (("emit", "training_start"), ("gate", "old"), ("emit", "phase_change"), ("emit", "epoch_end"), ("emit", "training_end"), ("gate", "old-end")),
        (("emit", "training_start"), ("gate", "new")),
    )
    mgr = manager_cls(model)
    out: dict[str, Any] = {}
    try:
        mgr.start_training(X, y)
        _need(model.reached("old"), "run 1 never reached its gate")
        mgr.stop_training()
        out["second_start"] = _try_start(mgr, X, y)
        if out["second_start"]["accepted"]:
            _need(model.reached("new"), "run 2 never reached its gate")
            out["fits_running_at_once"] = model.running_now()
            model.open("old")  # run 1's fit emits phase_change, epoch_end and training_end
            _need(model.reached("old-end"), "run 1 never reached its end gate")
            out["run1_interrupted"] = 1 in model.interrupted
            out["run1_events_delivered_while_run2_current"] = model.delivered[1][1:]
            out["while_run2_trains"] = _snapshot(mgr)
        else:
            model.open("old")
            model.threads[0].join(timeout=5.0)
            _need(not model.threads[0].is_alive(), "run 1's thread did not end")
            out["run1_interrupted"] = 1 in model.interrupted
            out["run1_events_delivered_after_the_stop"] = model.delivered[1][1:]
            out["after_run1_ended"] = _snapshot(mgr)
            out["start_after_run1_ended"] = _try_start(mgr, X, y)
            _need(model.reached("new"), "run 2 never reached its gate")
            out["fits_running_at_once"] = model.running_now()
    finally:
        _finish(model, mgr)
    out["peak_fits_running_at_once"] = model.peak
    return out


def _pause_gate(manager_cls: type, model_cls: type, np: Any) -> dict[str, Any]:
    X, y = np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32)
    model = model_cls(
        (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("gate", "old-after")),
        (("emit", "training_start"), ("gate", "new")),
        (("emit", "training_start"), ("gate", "third")),
    )
    mgr = manager_cls(model)
    out: dict[str, Any] = {}
    try:
        mgr.start_training(X, y)
        _need(model.reached("old"), "run 1 never reached its gate")
        mgr.stop_training()
        out["second_start"] = _try_start(mgr, X, y)
        if not out["second_start"]["accepted"]:
            model.open("old")
            model.threads[0].join(timeout=5.0)
            _need(not model.threads[0].is_alive(), "run 1's thread did not end")
            out["run1_interrupted_at_its_next_event"] = 1 in model.interrupted
            return out
        _need(model.reached("new"), "run 2 never reached its gate")
        out["pause_run2"] = mgr.pause_training()["state_machine"]["status"]
        model.open("old")  # run 1's next event: its stop was cleared, so it goes to the pause gate
        _need(model.began("1:epoch_end").wait(5.0), "run 1 never began its next event")
        out["run1_held_at_the_shared_pause_gate"] = not model.reached("old-after", timeout=0.5)
        model.open("new")  # run 2's fit returns while paused: the paused completion opens the gate
        _need(mgr.join(timeout=5.0), "run 2's thread did not end")
        out["run2_after_its_paused_completion"] = _snapshot(mgr)
        out["run1_released_with_no_command"] = model.reached("old-after")
        out["run1_epoch_landed_in_run2_monitor"] = "epoch_end" in model.delivered[1]
        out["completed_run_after_run1_released"] = _snapshot(mgr)
        out["third_start"] = _try_start(mgr, X, y)
        if out["third_start"]["accepted"]:
            _need(model.reached("third"), "run 3 never reached its gate")
            out["fits_running_at_once_after_third_start"] = model.running_now()
    finally:
        _finish(model, mgr)
    out["peak_fits_running_at_once"] = model.peak
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--service-core", required=True, type=Path, help="a juniper-service-core directory (holds the juniper_service_core package)")
    parser.add_argument("--model-core", required=True, type=Path, help="a juniper-model-core directory (holds the juniper_model_core package)")
    args = parser.parse_args(argv)
    sys.path[:0] = [str(args.service_core.resolve()), str(args.model_core.resolve())]

    import numpy as np
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult

    from juniper_service_core.lifecycle import manager as manager_module

    model_cls = _build_model_class(TrainableModel, TrainingEvent, TrainResult, manager_module.TrainingInterrupted)
    report: dict[str, Any] = {"manager_file": manager_module.__file__}
    try:
        report["overlap"] = _overlap(manager_module.ServiceLifecycleManager, model_cls, np)
        report["pause_gate"] = _pause_gate(manager_module.ServiceLifecycleManager, model_cls, np)
    except ProbeError as exc:
        print(f"probe setup failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
