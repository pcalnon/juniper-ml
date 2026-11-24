#!/usr/bin/env python3
"""
Probe juniper-cascor's lifecycle around a stop: a refused start, a fit with no checkpoint left, a snapshot verb after a stop.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-service-core's fix for its own stop-then-start race (N-2), whose validators found
         three adjacent gaps: (a) a refused start is not a no-op, (b) a fit that never reaches an
         event blocks every later start, (c) the same race for a stop followed by a snapshot
         load, resume or replay. This reports what juniper-cascor does in each case.

Drives the real ``TrainingLifecycleManager`` of the ``--src`` tree with a gated stub
``model.fit`` (events and gates; every wait is bounded), so it needs no data service and spawns
no candidate pool. It REPORTS, it does not judge: one JSON object per probe on stdout and all of
them in ``--out``. Snapshots go to ``--snapshots`` (a fresh directory the caller names; never
the system temp directory), through ``JUNIPER_CASCOR_SNAPSHOTS_DIR``.

Probes:
  a1  a start refused for the FSM state (a run is active): what did it change?
  a2  a start refused for its params, sent after a stop: what did it change, and did the stop hold?
  a3  an accepted start-fresh sent after a stop: what does it rebind while the stopped fit is alive?
  b   a stopped fit that reaches no checkpoint: are later starts accepted, and do they run?
  d   a run stopped while it is queued behind a stopped fit: does it still start, and how far does it get?
  c   stop, then load_snapshot / restore_for_retrain / resume_from_snapshot / start_replay while
      the stopped fit is alive, with and without a checkpoint left in that fit: is the verb
      accepted, and what does the fit's settle then do?

Usage:
  2026-11-11_flood4r2_r17-cascor_adjacent_probes.py --src <cascor src dir> --snapshots <fresh dir> --out <json file>
Exit: 0 when every probe ran to its end, 1 when one raised.
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
RUNS = 4


class _Gate:
    """The gates of one call of the stub fit."""

    def __init__(self) -> None:
        self.parked = threading.Event()
        self.release = threading.Event()
        self.ran_on = threading.Event()


class _Harness:
    """A real manager whose fit is gated, with an ordered trail of what its settles did."""

    def __init__(self, manager_module, event_cls, checkpoint_after_release: bool = True) -> None:
        self.module = manager_module
        self.event_cls = event_cls
        self.checkpoint_after_release = checkpoint_after_release
        self.gates = [_Gate() for _ in range(RUNS)]
        self.calls = 0
        self.trail: list = []
        self._lock = threading.Lock()
        self.mgr = manager_module.TrainingLifecycleManager()
        self.mgr.create_network(input_size=2, output_size=2)
        self.mgr.model.fit = self._fit
        self._wrap()

    def _fit(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        with self._lock:
            index = self.calls
            self.calls += 1
        gate = self.gates[index]
        on_event(self.event_cls("training_start", {"n_samples": int(x.shape[0])}, 0))
        gate.parked.set()
        gate.release.wait(timeout=GATE_TIMEOUT)
        if self.checkpoint_after_release:
            on_event(self.event_cls("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, 1))
        gate.ran_on.set()
        on_event(self.event_cls("training_end", {"metrics": {}}, 2))

    def _wrap(self) -> None:
        sm = self.mgr.state_machine
        state = self.mgr.training_state
        real_handle, real_completed, real_failed, real_update = sm.handle_command, sm.mark_completed, sm.mark_failed, state.update_state
        real_counted = self.module.inc_training_session_completed

        def handle_command(command):
            before = sm.status.name
            accepted = real_handle(command)
            self.trail.append(f"FSM {command.name} from {before} -> {'accepted' if accepted else 'refused'}")
            return accepted

        def mark_completed():
            before = sm.status.name
            accepted = real_completed()
            self.trail.append(f"FSM mark_completed from {before} -> {'accepted' if accepted else 'refused'}")
            return accepted

        def mark_failed(reason="Unknown error"):
            before = sm.status.name
            accepted = real_failed(reason)
            self.trail.append(f"FSM mark_failed from {before} -> {'accepted' if accepted else 'refused'} ({reason})")
            return accepted

        def update_state(**fields):
            if "status" in fields:
                self.trail.append(f"training_state.status := {fields['status']!r}")
            return real_update(**fields)

        def counted(status):
            self.trail.append(f"session counted as {status!r}")
            return real_counted(status)

        sm.handle_command, sm.mark_completed, sm.mark_failed, state.update_state = handle_command, mark_completed, mark_failed, update_state
        self.module.inc_training_session_completed = counted
        self._restore_counter = real_counted
        self.mgr.monitor.register_callback("training_end", lambda **_kwargs: self.trail.append("monitor training_end callbacks fired"))

    def fsm(self) -> str:
        return self.mgr.state_machine.get_state_summary()["status"]

    def start(self, torch, **kwargs):
        x = torch.randn(8, 2)
        y = torch.zeros(8, 2)
        y[:4, 0] = 1
        y[4:, 1] = 1
        self.mgr.start_training(X=x, y=y, **kwargs)
        return x, self.mgr._training_future

    def close(self) -> None:
        for gate in self.gates:
            gate.release.set()
        try:
            self.mgr.shutdown()
        finally:
            self.module.inc_training_session_completed = self._restore_counter


def _answer(request) -> str:
    try:
        request()
        return "accepted"
    except (RuntimeError, ValueError) as exc:
        return f"refused: {type(exc).__name__}: {exc}"


def _settle(future) -> str:
    try:
        future.result(timeout=WAIT)
        return "returned"
    except TimeoutError:
        return "STILL RUNNING after the bounded wait"
    except Exception as exc:  # a failed fit is a finding to report, not an error of the probe
        return f"raised {type(exc).__name__}: {exc}"


def probe_a1(module, torch, event_cls) -> dict:
    """A start refused for the FSM state: does it bind data, apply params or touch the stop signal?"""
    harness = _Harness(module, event_cls)
    try:
        first_x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        rate_before = harness.mgr.network.learning_rate
        signal_before = harness.mgr._stop_event
        new_x = torch.randn(8, 2)
        answer = _answer(lambda: harness.mgr.start_training(X=new_x, y=torch.zeros(8, 2), learning_rate=rate_before * 3 + 0.25))
        return {
            "probe": "a1",
            "what": "start sent while a run is STARTED, with new inline data and a new learning_rate",
            "answer": answer,
            "train_tensors_rebound": harness.mgr._train_x is not first_x,
            "learning_rate_changed": harness.mgr.network.learning_rate != rate_before,
            "run_queued": harness.mgr._training_future is not old_future,
            "newest_stop_signal_replaced": harness.mgr._stop_event is not signal_before,
            "newest_stop_signal_raised": harness.mgr._stop_event.is_set(),
            "fsm": harness.fsm(),
        }
    finally:
        harness.close()


def probe_a2(module, torch, event_cls) -> dict:
    """A start refused for its params, sent after a stop: what it changed, and whether the stop held."""
    harness = _Harness(module, event_cls)
    try:
        _x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        harness.mgr.stop_training()
        new_x = torch.randn(8, 2)
        answer = _answer(lambda: harness.mgr.start_training(X=new_x, y=torch.zeros(8, 2), selected_candidates=0))
        report = {
            "probe": "a2",
            "what": "stop, then a start whose candidate-pool triple cannot hold (the route answers 409)",
            "answer": answer,
            "train_tensors_rebound": harness.mgr._train_x is new_x,
            "run_queued": harness.mgr._training_future is not old_future,
            "fsm_after_refusal": harness.fsm(),
        }
        harness.gates[0].release.set()
        report["stopped_fit"] = _settle(old_future)
        report["stopped_fit_passed_its_next_checkpoint"] = harness.gates[0].ran_on.is_set()
        report["trail_after_stop"] = harness.trail[harness.trail.index("training_state.status := 'Stopped'") + 1 :]
        return report
    finally:
        harness.close()


def probe_a3(module, torch, event_cls) -> dict:
    """An ACCEPTED start-fresh sent after a stop: what it rebinds while the stopped fit is alive."""
    harness = _Harness(module, event_cls)
    mgr = harness.mgr
    create = mgr._create_network_locked

    def _create_and_gate(**config):
        # A start-fresh rebuilds the model; keep its fit the gated stub so no real training runs.
        created = create(**config)
        mgr.model.fit = harness._fit
        return created

    mgr._create_network_locked = _create_and_gate
    try:
        _x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        network_before = mgr.network
        rate = network_before.learning_rate * 3 + 0.25
        mgr.stop_training()
        new_x, new_future = harness.start(torch, start_fresh=True, learning_rate=rate)
        report = {
            "probe": "a3",
            "what": "stop, then an accepted start with start_fresh, new inline data and a new learning_rate, while the stopped fit is parked",
            "stopped_fit_alive_when_the_start_returned": not old_future.done(),
            "run_queued_not_running": not new_future.running() and not new_future.done(),
            "train_tensors_rebound": mgr._train_x is new_x,
            "model_replaced_under_the_fit": mgr.network is not network_before,
            "new_learning_rate_on_the_rebuilt_model": mgr.network.learning_rate == rate,
            "fsm_after_the_start": harness.fsm(),
        }
        harness.gates[0].release.set()
        report["stopped_fit"] = _settle(old_future)
        report["stopped_fit_passed_its_next_checkpoint"] = harness.gates[0].ran_on.is_set()
        assert harness.gates[1].parked.wait(WAIT), "the queued run never entered its fit"
        harness.gates[1].release.set()
        report["new_run"] = _settle(new_future)
        report["fsm_at_the_end"] = harness.fsm()
        return report
    finally:
        harness.close()


def probe_d(module, torch, event_cls) -> dict:
    """A run stopped while it is queued behind a stopped fit: does it still start, and how far does it get?"""
    harness = _Harness(module, event_cls)
    try:
        _x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        harness.mgr.stop_training()
        _new_x, queued_future = harness.start(torch)
        harness.mgr.stop_training()
        mark = len(harness.trail)
        harness.gates[0].release.set()
        stopped_fit = _settle(old_future)
        entered = harness.gates[1].parked.wait(WAIT)
        harness.gates[1].release.set()
        return {
            "probe": "d",
            "what": "stop, start (the run queues behind the stopped fit), stop again; then the stopped fit is let go",
            "stopped_fit": stopped_fit,
            "queued_run_entered_its_fit": entered,
            "queued_run": _settle(queued_future),
            "queued_run_passed_its_first_checkpoint": harness.gates[1].ran_on.is_set(),
            "fits_called": harness.calls,
            "trail_after_the_second_stop": harness.trail[mark:],
            "fsm_at_the_end": harness.fsm(),
        }
    finally:
        harness.close()


def probe_b(module, torch, event_cls) -> dict:
    """A stopped fit that reaches no checkpoint (it stays parked): do later starts run?"""
    harness = _Harness(module, event_cls)
    try:
        _x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        harness.mgr.stop_training()
        first_answer = _answer(lambda: harness.start(torch))
        first_queued = harness.mgr._training_future
        second_answer = _answer(lambda: harness.start(torch))
        second_queued = harness.mgr._training_future
        entered = harness.gates[1].parked.wait(1.0)
        status = harness.mgr.get_status()
        report = {
            "probe": "b",
            "what": "stop while the fit is parked with no checkpoint reached, then two starts; observed for 1.0 s, then reset, observed for 0.5 s more",
            "start_answers": [first_answer, second_answer],
            "queued_runs_entered_their_fit_within_1s": entered,
            "queued_futures_running_or_done": [first_queued.running() or first_queued.done(), second_queued.running() or second_queued.done()],
            "fsm_while_blocked": status["state_machine"]["status"],
            "training_active_while_blocked": status["training_active"],
            "stopped_fit_done": old_future.done(),
        }
        report["reset_answer"] = _answer(harness.mgr.reset)
        report["queued_runs_entered_after_reset_within_0.5s"] = harness.gates[1].parked.wait(0.5)
        report["stopped_fit_done_after_reset"] = old_future.done()
        return report
    finally:
        harness.close()


def _donor_snapshot(module, torch, rows: int) -> str:
    """Save a snapshot of a separate network whose history has ``rows`` rows; return its id."""
    donor = module.TrainingLifecycleManager()
    try:
        donor.create_network(input_size=2, output_size=2)
        history = getattr(donor.network, "history", None)
        if isinstance(history, dict):
            for key in ("train_loss", "value_loss", "train_accuracy", "value_accuracy"):
                history[key] = [0.5 + 0.01 * i for i in range(rows)]
        return donor.save_snapshot(description="flood4r2 r17-cascor adjacent probe donor")["id"]
    finally:
        donor.shutdown()


def probe_c(module, torch, event_cls, verb: str, checkpoint_left: bool, snapshot_id: str) -> dict:
    """Stop, then a snapshot verb while the stopped fit is alive; then let the fit go on and settle."""
    harness = _Harness(module, event_cls, checkpoint_after_release=checkpoint_left)
    mgr = harness.mgr
    try:
        _x, old_future = harness.start(torch)
        assert harness.gates[0].parked.wait(WAIT), "run 0 never entered its fit"
        network_before = mgr.network
        mgr.stop_training()
        result = getattr(mgr, verb)(snapshot_id)
        alive = not old_future.done()
        mark = len(harness.trail)
        rows_at_verb = len(mgr.monitor.get_all_metrics())
        loaded_rows = len((getattr(mgr.network, "history", None) or {}).get("train_loss", []))
        report = {
            "probe": "c",
            "verb": verb,
            "stopped_fit_has_a_checkpoint_left": checkpoint_left,
            "verb_loaded": bool(result.get("loaded")),
            "verb_reason": result.get("reason"),
            "stopped_fit_alive_when_the_verb_returned": alive,
            "fsm_after_verb": harness.fsm(),
            "model_replaced_under_the_fit": mgr.network is not network_before,
            "loaded_history_rows": loaded_rows,
        }
        harness.gates[0].release.set()
        report["stopped_fit"] = _settle(old_future)
        report["fsm_after_the_fit_settled"] = harness.fsm()
        report["training_state_status"] = mgr.get_status()["training_state"].get("status")
        report["settle_trail"] = harness.trail[mark:]
        report["rows_the_fit_added_to_the_monitor_after_the_verb"] = len(mgr.monitor.get_all_metrics()) - rows_at_verb
        return report
    finally:
        if mgr._replay_session is not None:
            mgr.stop_replay()
        harness.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--src", required=True, type=Path, help="the cascor src/ tree to import")
    parser.add_argument("--snapshots", required=True, type=Path, help="a fresh directory for the probe's snapshots")
    parser.add_argument("--out", required=True, type=Path, help="JSON file for the reports")
    args = parser.parse_args()
    snapshots = args.snapshots.resolve()
    snapshots.mkdir(parents=True, exist_ok=True)
    os.environ["JUNIPER_CASCOR_SNAPSHOTS_DIR"] = str(snapshots)
    os.environ.pop("JUNIPER_CASCOR_LOG_DIR", None)
    sys.path.insert(0, str(args.src.resolve()))

    import torch
    from juniper_model_core.events import TrainingEvent

    from api.lifecycle import manager as manager_module

    reports = [{"manager_under_test": manager_module.__file__, "python": sys.version.split()[0]}]
    failed = False
    jobs = [
        ("a1", lambda: probe_a1(manager_module, torch, TrainingEvent)),
        ("a2", lambda: probe_a2(manager_module, torch, TrainingEvent)),
        ("a3", lambda: probe_a3(manager_module, torch, TrainingEvent)),
        ("b", lambda: probe_b(manager_module, torch, TrainingEvent)),
        ("d", lambda: probe_d(manager_module, torch, TrainingEvent)),
    ]
    snapshot_id = _donor_snapshot(manager_module, torch, rows=5)
    for verb in ("load_snapshot", "restore_for_retrain", "resume_from_snapshot", "start_replay"):
        for checkpoint_left in (True, False):
            jobs.append((f"c/{verb}/{'checkpoint' if checkpoint_left else 'no-checkpoint'}", lambda verb=verb, left=checkpoint_left: probe_c(manager_module, torch, TrainingEvent, verb, left, snapshot_id)))
    for name, job in jobs:
        try:
            report = job()
        except Exception:  # report the probe that broke and carry on with the rest
            failed = True
            report = {"probe": name, "probe_error": traceback.format_exc()}
        reports.append(report)
        print(json.dumps(report), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
