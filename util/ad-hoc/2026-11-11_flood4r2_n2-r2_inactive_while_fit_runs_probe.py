#!/usr/bin/env python3
"""Probe the ways the lifecycle machine can read inactive while a fit it launched is still running.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use investigation)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-11
Status:      ad-hoc -- investigation (round 2 of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race);
             juniper-service-core/juniper_service_core/lifecycle/manager.py (start_training's refusal)

``start_training`` refuses a start while the previous training thread is alive with the stop
pending. This probe drives a scripted model whose ``fit`` parks at ``threading.Event`` gates
(nothing sleeps) through each sequence below and prints what the manager then does, as JSON:

- ``stop_then_start``: start, stop, start. The control: the start is refused.
- ``hung_fit``: a ``fit`` that emits no events and does not return. Start, stop, then start,
  reset + start, attach_model + start: what holds the start back, and what the status says.
- ``fit_that_swallows_the_stop``: a model that catches the interrupt at its next event and
  carries on: the same questions.
- ``replay_stop_resets_a_running_fit``: start_replay, restore_for_retrain (the replay session is
  not torn down), start, then ``replay_control("stop")``, which resets the machine without setting
  the stop: is the next start accepted beside the fit still running?
- ``direct_run``: a ``fit`` driven by the public ``run()`` on another thread, then stop, then start.
- ``stop_then_load``: start, stop, then each snapshot load while the stopped fit still runs; what
  the stopped thread's settle then writes over the loaded state.
- ``stop_then_load_then_the_fit_raises``: the same, with a ``fit`` that raises instead of unwinding.
- ``stop_then_load_with_an_event_inside_the_sink``: an event that had passed the sink's stop check
  when the stop and the load landed: where it is folded.

The last three are the stop-then-load race, which the change this probe accompanies reports and
does not fix. ``--service-core`` and ``--model-core`` name the package directories to import, so
the same probe runs on this tree and on any other. Snapshot bundles go under ``--scratch`` and are
removed.

Exit status: 0 when the probe ran; 2 on a setup error. It asserts nothing: it reports.

Usage (from this worktree's root, under an interpreter with the test dependencies):
    <python> util/ad-hoc/2026-11-11_flood4r2_n2-r2_inactive_while_fit_runs_probe.py \\
        --service-core juniper-service-core --model-core juniper-model-core --scratch <scratch dir>
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import threading
from pathlib import Path


class _FitCounter:
    """How many ``fit`` calls are running at once, and the most there has been since the last reset."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = 0
        self.peak = 0

    def enter(self) -> None:
        with self._lock:
            self.running += 1
            self.peak = max(self.peak, self.running)

    def leave(self) -> None:
        with self._lock:
            self.running -= 1

    def reset(self) -> None:
        with self._lock:
            self.peak = self.running


_FITS = _FitCounter()


def _load(service_core: Path, model_core: Path):
    sys.path[:0] = [str(service_core.resolve()), str(model_core.resolve())]
    import numpy as np
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult
    from juniper_model_core.serialization import ModelSerializer

    from juniper_service_core.lifecycle import ServiceLifecycleManager, TrainingInterrupted

    class Gated(TrainableModel):
        """``fit`` emits ``training_start``, parks at ``gate``, then emits ``epoch_end`` (see the flags)."""

        def __init__(self, *, eventless: bool = False, raises: bool = False, swallows: bool = False, gate_open: bool = False) -> None:
            self.task_type = "regression"
            self.random_seed = 0
            self.eventless = eventless  # emit nothing at all
            self.raises = raises  # raise RuntimeError("boom") once released, instead of emitting
            self.swallows = swallows  # catch the interrupt at the next event and park again
            self.gate = threading.Event()
            if gate_open:
                self.gate.set()
            self.parked = threading.Event()
            self.swallowed = threading.Event()
            self.second_gate = threading.Event()
            self.returned = threading.Event()

        def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw):
            _FITS.enter()
            try:
                if on_event is not None and not self.eventless:
                    on_event(TrainingEvent("training_start", {}, 0))
                self.parked.set()
                self.gate.wait(timeout=20.0)
                if self.raises:
                    raise RuntimeError("boom")
                if on_event is not None and not self.eventless:
                    try:
                        on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 0.5}}, 0))
                    except TrainingInterrupted:
                        if not self.swallows:
                            raise
                        self.swallowed.set()
                        self.second_gate.wait(timeout=20.0)
            finally:
                _FITS.leave()
                self.returned.set()
            return TrainResult(final_metrics={"mse": 0.5}, n_epochs=1)

        def predict(self, X, **kw):
            return np.zeros((X.shape[0], 1))

        def metrics(self):
            return {"mse": 0.5}

        def describe_topology(self):
            return {"model_type": "gated", "nodes": [], "edges": [], "meta": {}}

        @property
        def input_shape(self):
            return (2,)

        @property
        def output_shape(self):
            return (1,)

    class Serializer(ModelSerializer):
        """Stores nothing; every load hands back a fresh gated model and remembers it."""

        def __init__(self) -> None:
            self.loaded: list[Gated] = []

        def save(self, model, path) -> None:
            Path(str(path)).parent.mkdir(parents=True, exist_ok=True)

        def load(self, path):
            self.loaded.append(Gated())
            return self.loaded[-1]

    return np, Gated, Serializer, ServiceLifecycleManager


def _start(mgr, X, y) -> str:
    try:
        return "accepted: " + mgr.start_training(X, y)["state_machine"]["status"]
    except RuntimeError as exc:
        return f"refused: {exc}"


def _brief(mgr) -> dict:
    status = mgr.get_status()
    return {"status": status["state_machine"]["status"], "monitor": status["monitor"]["status"], "training_active": status["training_active"], "error": status.get("error"), "history_rows": len(mgr.get_metrics_history()), "keys": sorted(status)}


def _release(mgr, models) -> None:
    for model in models:
        model.gate.set()
        model.second_gate.set()
    mgr.shutdown()


def _held_back(mgr, model, spare, X, y) -> dict:
    """Stop the run, then try a start after the stop, after a reset and after attach_model."""
    mgr.stop_training()
    row = {"after_stop": _start(mgr, X, y), "status_meanwhile": _brief(mgr)}
    mgr.reset()
    row["after_reset"] = _start(mgr, X, y)
    try:
        mgr.attach_model(spare)
        row["after_attach_model"] = _start(mgr, X, y)
    except RuntimeError as exc:  # a tree that accepted one of the starts above has a run active
        row["attach_model"] = f"refused: {exc}"
    row["thread_alive"] = mgr._thread.is_alive()
    return row


def probe(service_core: Path, model_core: Path, scratch: Path) -> dict:
    np, Gated, Serializer, Manager = _load(service_core, model_core)
    X, y = np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32)
    snaps = scratch / "probe-snapshots"
    out: dict = {}

    # stop_then_start (the control)
    _FITS.reset()
    model = Gated()
    mgr = Manager(model)
    mgr.start_training(X, y)
    model.parked.wait(5.0)
    mgr.stop_training()
    out["stop_then_start"] = {"start": _start(mgr, X, y), "peak_fits_at_once": _FITS.peak, "after": _brief(mgr)}
    _release(mgr, [model])

    # hung_fit: no events, and it does not return while the probe looks
    _FITS.reset()
    model, spare = Gated(eventless=True), Gated()
    mgr = Manager(model)
    mgr.start_training(X, y)
    model.parked.wait(5.0)
    row = _held_back(mgr, model, spare, X, y)
    model.gate.set()
    model.returned.wait(5.0)
    mgr.join(5.0)
    row["once_the_fit_returned"] = _start(mgr, X, y)
    row["peak_fits_at_once"] = _FITS.peak
    out["hung_fit"] = row
    _release(mgr, [model, spare])

    # fit_that_swallows_the_stop: the model catches the interrupt and carries on
    _FITS.reset()
    model, spare = Gated(swallows=True), Gated()
    mgr = Manager(model)
    mgr.start_training(X, y)
    model.parked.wait(5.0)
    mgr.stop_training()
    model.gate.set()
    row = {"the_fit_caught_the_interrupt": model.swallowed.wait(5.0)}
    row.update(_held_back(mgr, model, spare, X, y))
    model.second_gate.set()
    model.returned.wait(5.0)
    mgr.join(5.0)
    row["once_the_fit_returned"] = _start(mgr, X, y)
    row["peak_fits_at_once"] = _FITS.peak
    out["fit_that_swallows_the_stop"] = row
    _release(mgr, [model, spare])

    # replay_stop_resets_a_running_fit
    _FITS.reset()
    serializer = Serializer()
    first = Gated()
    mgr = Manager(first, serializer=serializer, snapshot_dir=snaps)
    snapshot_id = mgr.save_snapshot()["id"]
    mgr.start_replay(snapshot_id)
    mgr.restore_for_retrain(snapshot_id)
    row = {"replay_session_survives_the_retrain_load": mgr.get_replay_state() is not None, "before_start": _brief(mgr)["status"]}
    row["start"] = _start(mgr, X, y)
    running = serializer.loaded[-1]
    running.parked.wait(5.0)
    try:
        mgr.replay_control("stop")
        row["replay_control_stop"] = "accepted"
    except RuntimeError as exc:
        row["replay_control_stop"] = f"refused: {exc}"
    row["after_replay_stop"] = _brief(mgr)
    row["stop_event_set"] = mgr._stop_event.is_set()
    row["first_fit_still_running"] = not running.returned.is_set()
    row["second_start"] = _start(mgr, X, y)
    row["peak_fits_at_once"] = _FITS.peak
    out["replay_stop_resets_a_running_fit"] = row
    _release(mgr, [first, *serializer.loaded])

    # direct_run: a fit driven by run() on a caller's thread
    _FITS.reset()
    model = Gated()
    mgr = Manager(model)
    row = {}

    def direct(manager=mgr, report=row) -> None:
        try:
            manager.run(X, y)
            report["the_direct_run_ended"] = "returned"
        except Exception as exc:  # noqa: BLE001 - the probe reports how the direct run ended
            report["the_direct_run_ended"] = f"raised {type(exc).__name__}"

    caller = threading.Thread(target=direct, daemon=True)
    caller.start()
    model.parked.wait(5.0)
    row["status_during_the_direct_run"] = _brief(mgr)["status"]
    mgr.stop_training()
    row["start_after_stop"] = _start(mgr, X, y)
    row["peak_fits_at_once"] = _FITS.peak
    out["direct_run"] = row
    _release(mgr, [model])
    caller.join(5.0)

    # stop_then_load: each load while the stopped fit still runs
    loads = {}
    for name in ("load_snapshot", "resume_from_snapshot", "start_replay", "restore_for_retrain"):
        _FITS.reset()
        serializer = Serializer()
        model = Gated()
        mgr = Manager(model, serializer=serializer, snapshot_dir=snaps)
        snapshot_id = mgr.save_snapshot()["id"]
        mgr.start_training(X, y)
        model.parked.wait(5.0)
        mgr.stop_training()
        try:
            getattr(mgr, name)(snapshot_id)
            row = {"load": "accepted", "after_load": _brief(mgr)}
        except RuntimeError as exc:
            row = {"load": f"refused: {exc}", "after_load": _brief(mgr)}
        row["start_while_the_stopped_fit_runs"] = _start(mgr, X, y)
        row["stop_event_set"] = mgr._stop_event.is_set()
        model.gate.set()
        model.returned.wait(5.0)
        mgr._thread.join(5.0)
        row["after_the_stopped_fit_unwound"] = _brief(mgr)
        row["peak_fits_at_once"] = _FITS.peak
        loads[name] = row
        _release(mgr, [model, *serializer.loaded])
    out["stop_then_load"] = loads

    # stop_then_load_then_the_fit_raises
    serializer = Serializer()
    model = Gated(raises=True)
    mgr = Manager(model, serializer=serializer, snapshot_dir=snaps)
    snapshot_id = mgr.save_snapshot()["id"]
    mgr.start_training(X, y)
    model.parked.wait(5.0)
    mgr.stop_training()
    mgr.resume_from_snapshot(snapshot_id)
    row = {"after_load": _brief(mgr)}
    model.gate.set()
    model.returned.wait(5.0)
    mgr._thread.join(5.0)
    row["after_the_stopped_fit_raised"] = _brief(mgr)
    out["stop_then_load_then_the_fit_raises"] = row
    _release(mgr, [model, *serializer.loaded])

    # stop_then_load_with_an_event_inside_the_sink
    serializer = Serializer()
    model = Gated(gate_open=True)
    mgr = Manager(model, serializer=serializer, snapshot_dir=snaps)
    snapshot_id = mgr.save_snapshot()["id"]
    inside, let_through = threading.Event(), threading.Event()
    fold = mgr.monitor.on_event

    def parked_fold(event) -> None:
        if event.type == "epoch_end":
            inside.set()
            let_through.wait(timeout=20.0)
        fold(event)

    mgr.monitor.on_event = parked_fold
    mgr.start_training(X, y)
    row = {"an_event_is_inside_the_sink": inside.wait(5.0)}
    mgr.stop_training()
    mgr.resume_from_snapshot(snapshot_id)
    row["after_load"] = _brief(mgr)
    let_through.set()
    model.returned.wait(5.0)
    mgr._thread.join(5.0)
    row["after_the_event_was_folded"] = _brief(mgr)
    out["stop_then_load_with_an_event_inside_the_sink"] = row
    _release(mgr, [model, *serializer.loaded])

    shutil.rmtree(snaps, ignore_errors=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--service-core", required=True, type=Path, help="the juniper-service-core directory to import")
    parser.add_argument("--model-core", required=True, type=Path, help="the juniper-model-core directory to import")
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch directory in this worktree's tmp/ (snapshot bundles; removed)")
    args = parser.parse_args(argv)
    if not (args.service_core / "juniper_service_core").is_dir() or not (args.model_core / "juniper_model_core").is_dir():
        print("setup error: --service-core / --model-core do not hold the packages", file=sys.stderr)
        return 2
    logging.disable(logging.CRITICAL)  # the manager logs each scripted failure with a traceback
    result = probe(args.service_core, args.model_core, args.scratch)
    result["python"] = sys.version.split()[0]
    result["service_core"] = str(args.service_core.resolve())
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
