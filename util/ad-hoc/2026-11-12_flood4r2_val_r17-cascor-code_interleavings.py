"""
Drive juniper-cascor's lifecycle manager through stop/start interleavings with a gated stub fit and record what each run did.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17, "cascor: stop-then-start")

Usage: <JuniperCascor1 python> <this> <juniper-cascor tree> <out.json> <snapshot scratch dir> [probe name ...]

Imports ``api.lifecycle.manager`` from <tree>/src (asserted), builds a real ``TrainingLifecycleManager``
per probe with ``model.fit`` replaced by a gated stub that sends real ``TrainingEvent`` objects through
the manager's own ``on_event`` sink, and writes one JSON object: probe name -> the facts observed. The
same script runs on a main tree and on the carrier tree; the two JSON files are then compared. Nothing
is written outside <out.json> and <snapshot scratch dir>. Every wait is bounded.
"""

import json
import sys
import threading
import time
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
SNAP_DIR = Path(sys.argv[3]).resolve()
sys.path.insert(0, str(TREE / "src"))

import torch  # noqa: E402
from juniper_model_core.events import TrainingEvent  # noqa: E402

from api.lifecycle import manager as manager_module  # noqa: E402

GATE_TIMEOUT = 20.0
WAIT = 8.0


def _ev(kind: str, seq: int) -> TrainingEvent:
    if kind == "training_start":
        return TrainingEvent("training_start", {"n_samples": 8}, seq)
    if kind == "epoch_end":
        return TrainingEvent("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, seq)
    if kind == "phase_change":
        return TrainingEvent("phase_change", {"detail": {"grow_iteration": 1, "max_iterations": 2, "best_correlation": 0.1, "candidates_trained": 1}}, seq)
    return TrainingEvent("training_end", {"metrics": {}}, seq)


class Run:
    def __init__(self) -> None:
        self.before = ["training_start"]
        self.after = ["epoch_end"]
        self.raise_after = None
        self.parked = threading.Event()
        self.release = threading.Event()
        self.ran_on = threading.Event()
        self.entered = threading.Event()


class GatedFit:
    def __init__(self) -> None:
        self.calls = 0
        self._runs = []
        self._lock = threading.Lock()

    def run(self, index: int) -> Run:
        with self._lock:
            while len(self._runs) <= index:
                self._runs.append(Run())
            return self._runs[index]

    def __call__(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        with self._lock:
            index = self.calls
            self.calls += 1
        run = self.run(index)
        run.entered.set()
        for seq, kind in enumerate(run.before):
            on_event(_ev(kind, seq))
        run.parked.set()
        run.release.wait(timeout=GATE_TIMEOUT)
        if run.raise_after is not None:
            raise run.raise_after
        for seq, kind in enumerate(run.after):
            on_event(_ev(kind, seq + 10))
        run.ran_on.set()
        on_event(_ev("training_end", 99))

    def release_all(self) -> None:
        with self._lock:
            runs = list(self._runs)
        for run in runs:
            run.release.set()


def _xy():
    x = torch.randn(8, 2)
    y = torch.zeros(8, 2)
    y[:4, 0] = 1
    y[4:, 1] = 1
    return x, y


def _answer(request) -> str:
    try:
        request()
        return "ok"
    except (RuntimeError, ValueError) as exc:
        return f"refused: {type(exc).__name__}: {exc}"


class Rig:
    """One manager, its gated fit, and recorders for the session counter, the FSM commands and the status writes."""

    def __init__(self) -> None:
        self.counted = []
        self._real_counter = manager_module.inc_training_session_completed
        manager_module.inc_training_session_completed = self.counted.append
        self.mgr = manager_module.TrainingLifecycleManager()
        self.mgr.create_network(input_size=2, output_size=2)
        self.fit = GatedFit()
        self.mgr.model.fit = self.fit
        self.commands = []
        self.statuses = []
        self.marks = []
        sm = self.mgr.state_machine
        real_handle = sm.handle_command
        real_completed = sm.mark_completed
        real_failed = sm.mark_failed
        real_update = self.mgr.training_state.update_state

        def _handle(command):
            before = sm.status.name
            accepted = real_handle(command)
            self.commands.append([command.name, before, bool(accepted), sm.status.name, threading.current_thread().name.split("_")[0]])
            return accepted

        def _completed():
            before = sm.status.name
            accepted = real_completed()
            self.marks.append(["mark_completed", before, bool(accepted)])
            return accepted

        def _failed(reason="Unknown error"):
            before = sm.status.name
            accepted = real_failed(reason)
            self.marks.append(["mark_failed", before, bool(accepted)])
            return accepted

        def _update(**fields):
            if "status" in fields:
                self.statuses.append(fields["status"])
            return real_update(**fields)

        sm.handle_command = _handle
        sm.mark_completed = _completed
        sm.mark_failed = _failed
        self.mgr.training_state.update_state = _update

    def start(self, **kwargs) -> str:
        x, y = _xy()
        return _answer(lambda: self.mgr.start_training(X=x, y=y, **kwargs))

    def parked(self, index: int) -> bool:
        return self.fit.run(index).parked.wait(timeout=WAIT)

    def fsm(self) -> str:
        return self.mgr.state_machine.status.name

    def ts(self) -> str:
        return self.mgr.training_state.get_state().get("status")

    def join(self, future) -> str:
        try:
            future.result(timeout=WAIT)
            return "returned"
        except TimeoutError:
            return "TIMEOUT"
        except Exception as exc:
            return f"raised {type(exc).__name__}: {exc}"

    def close(self) -> None:
        self.fit.release_all()
        try:
            self.mgr.shutdown()
        finally:
            manager_module.inc_training_session_completed = self._real_counter


def p_basic_stop_start(checkpoint: str):
    rig = Rig()
    try:
        rig.fit.run(0).after = [checkpoint]
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        out["a_parked"] = rig.parked(0)
        e0 = rig.mgr._stop_event
        rig.mgr.stop_training()
        out["fsm_after_stop"] = rig.fsm()
        out["start_b"] = rig.start()
        new_future = rig.mgr._training_future
        out["stop_event_replaced_by_start"] = rig.mgr._stop_event is not e0
        out["old_event_still_set"] = e0.is_set()
        out["fsm_after_start_b"] = rig.fsm()
        out["training_active_after_start_b"] = rig.mgr.get_status()["training_active"]
        out["training_state_after_start_b"] = rig.ts()
        out["b_done_before_a_released"] = new_future.done()
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on_past_checkpoint"] = rig.fit.run(0).ran_on.is_set()
        out["counted_after_a"] = list(rig.counted)
        out["b_parked"] = rig.parked(1)
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(new_future)
        out["b_ran_on"] = rig.fit.run(1).ran_on.is_set()
        out["counted_final"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        out["marks"] = rig.marks
        out["statuses"] = rig.statuses
        return out
    finally:
        rig.close()


def p_stop_start_stop():
    rig = Rig()
    try:
        rig.fit.run(1).before = ["training_start", "epoch_end"]
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        out["stop_2"] = _answer(rig.mgr.stop_training)
        n_status = len(rig.statuses)
        n_cmd = len(rig.commands)
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on"] = rig.fit.run(0).ran_on.is_set()
        out["b_join"] = rig.join(b_future)
        out["b_fit_was_called_although_stopped_while_queued"] = rig.fit.run(1).entered.is_set()
        out["b_passed_its_first_checkpoint"] = rig.fit.run(1).parked.is_set()
        out["statuses_after_stop_2"] = rig.statuses[n_status:]
        out["commands_after_stop_2"] = rig.commands[n_cmd:]
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_two_starts_after_one_stop():
    rig = Rig()
    try:
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        out["start_c"] = rig.start()
        c_future = rig.mgr._training_future
        out["c_is_a_second_queued_run"] = c_future is not b_future
        out["queue_depth_behind_old_fit"] = rig.mgr._executor._work_queue.qsize()
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on"] = rig.fit.run(0).ran_on.is_set()
        out["b_parked"] = rig.parked(1)
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(b_future)
        out["c_parked"] = rig.parked(2)
        rig.fit.run(2).release.set()
        out["c_join"] = rig.join(c_future)
        out["fit_calls"] = rig.fit.calls
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        return out
    finally:
        rig.close()


def p_stop_start_pause():
    rig = Rig()
    try:
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        out["pause_while_b_queued"] = _answer(rig.mgr.pause_training)
        out["pause_gate_open_while_b_queued"] = rig.mgr._pause_event.is_set()
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on"] = rig.fit.run(0).ran_on.is_set()
        out["b_parked"] = rig.parked(1)
        out["pause_once_b_entered"] = _answer(rig.mgr.pause_training)
        out["fsm_paused"] = rig.fsm()
        rig.fit.run(1).release.set()
        time.sleep(0.7)
        out["b_held_at_checkpoint_by_pause"] = not b_future.done()
        out["stop_while_b_paused"] = _answer(rig.mgr.stop_training)
        out["b_join"] = rig.join(b_future)
        out["b_ran_on"] = rig.fit.run(1).ran_on.is_set()
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_reset_after_stop():
    rig = Rig()
    try:
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["reset"] = _answer(rig.mgr.reset)
        out["fsm_after_reset"] = rig.fsm()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on"] = rig.fit.run(0).ran_on.is_set()
        out["b_parked"] = rig.parked(1)
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(b_future)
        out["b_ran_on"] = rig.fit.run(1).ran_on.is_set()
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        return out
    finally:
        rig.close()


def p_stop_start_reset():
    """A reset while the new run is still queued: it must reach the queued run."""
    rig = Rig()
    try:
        rig.fit.run(1).before = ["training_start", "epoch_end"]
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        out["reset"] = _answer(rig.mgr.reset)
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on"] = rig.fit.run(0).ran_on.is_set()
        out["b_join"] = rig.join(b_future)
        out["b_passed_its_first_checkpoint"] = rig.fit.run(1).parked.is_set()
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_old_fit_raises():
    rig = Rig()
    try:
        rig.fit.run(0).raise_after = RuntimeError("probe: the stopped fit raised")
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["b_parked"] = rig.parked(1)
        out["fsm_while_b_runs"] = rig.fsm()
        out["ts_while_b_runs"] = rig.ts()
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(b_future)
        out["b_ran_on"] = rig.fit.run(1).ran_on.is_set()
        out["marks"] = rig.marks
        out["statuses"] = rig.statuses
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_old_fit_raises_no_new_run():
    rig = Rig()
    try:
        rig.fit.run(0).raise_after = RuntimeError("probe: the stopped fit raised")
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["marks"] = rig.marks
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_a_refused_starts():
    """(a) An FSM-refused start binds nothing; a late-refused one has already bound its inline data (and more)."""
    rig = Rig()
    try:
        x1, y1 = _xy()
        out = {"start_a": _answer(lambda: rig.mgr.start_training(X=x1, y=y1))}
        old_future = rig.mgr._training_future
        rig.parked(0)
        x2, y2 = _xy()
        out["fsm_refused_start"] = _answer(lambda: rig.mgr.start_training(X=x2, y=y2))
        out["fsm_refused_start_bound_its_data"] = rig.mgr._train_x is x2
        e0 = rig.mgr._stop_event
        rig.mgr.stop_training()
        x3, y3 = _xy()
        out["late_refused_start"] = _answer(lambda: rig.mgr.start_training(X=x3, y=y3, selected_candidates=0))
        out["late_refused_start_bound_its_data"] = rig.mgr._train_x is x3
        out["late_refused_start_queued_a_run"] = rig.mgr._training_future is not old_future
        out["late_refused_start_replaced_stop_event"] = rig.mgr._stop_event is not e0
        out["stop_still_raised_after_late_refused_start"] = e0.is_set()
        net_before = rig.mgr.network
        monitor_rows_before = len(rig.mgr.monitor.get_recent_metrics(1000)) if hasattr(rig.mgr.monitor, "get_recent_metrics") else None
        x4, y4 = _xy()
        out["late_refused_start_fresh"] = _answer(lambda: rig.mgr.start_training(X=x4, y=y4, start_fresh=True, selected_candidates=0))
        out["late_refused_start_fresh_discarded_the_model_under_the_live_fit"] = rig.mgr.network is not net_before
        out["old_fit_still_alive_then"] = not old_future.done()
        out["monitor_rows_before"] = monitor_rows_before
        # the stub was installed on the discarded model; reinstall it so a later start stays gated
        if rig.mgr.model is not None:
            rig.mgr.model.fit = rig.fit
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on_past_checkpoint"] = rig.fit.run(0).ran_on.is_set()
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_b_no_checkpoint():
    """(b) A fit that reaches no checkpoint holds the single worker: later starts answer ok and never begin."""
    rig = Rig()
    try:
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        t0 = time.monotonic()
        out["start_b"] = rig.start()
        out["start_b_answer_seconds"] = round(time.monotonic() - t0, 3)
        b_future = rig.mgr._training_future
        time.sleep(1.5)
        status = rig.mgr.get_status()
        out["after_1_5s_fit_calls"] = rig.fit.calls
        out["after_1_5s_b_running"] = b_future.running()
        out["after_1_5s_b_done"] = b_future.done()
        out["after_1_5s_old_fit_alive"] = not old_future.done()
        out["after_1_5s_fsm"] = status["state_machine"]["status"]
        out["after_1_5s_training_active"] = status["training_active"]
        out["after_1_5s_training_state_status"] = status["training_state"].get("status")
        out["status_keys_naming_a_queued_run"] = sorted(k for k in status if any(word in k.lower() for word in ("queue", "pending_start", "pending_run", "stopping")))
        out["start_c"] = rig.start()
        out["queue_depth"] = rig.mgr._executor._work_queue.qsize()
        out["stop_2"] = _answer(rig.mgr.stop_training)
        out["queue_depth_after_stop_2"] = rig.mgr._executor._work_queue.qsize()
        out["b_cancelled_by_stop_2"] = b_future.cancelled()
        return out
    finally:
        rig.close()


def p_c_snapshot_under_live_stopped_fit():
    """(c) The snapshot verbs load under a live stopped fit."""
    rig = Rig()
    try:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        rig.mgr._get_snapshots_dir = lambda: SNAP_DIR
        snap = rig.mgr.save_snapshot("probe c")
        out = {"snapshot_saved": bool(snap)}
        out["start_a"] = rig.start()
        old_future = rig.mgr._training_future
        rig.parked(0)
        out["load_while_started"] = rig.mgr.load_snapshot(snap["id"]).get("loaded")
        rig.mgr.stop_training()
        model_before = rig.mgr.model
        result = rig.mgr.load_snapshot(snap["id"])
        out["load_under_live_stopped_fit_loaded"] = result.get("loaded")
        out["old_fit_alive_at_load"] = not old_future.done()
        out["model_replaced_under_live_fit"] = rig.mgr.model is not model_before
        out["fsm_after_load"] = rig.fsm()
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on_past_checkpoint"] = rig.fit.run(0).ran_on.is_set()
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        out["counted"] = list(rig.counted)
        out["marks"] = rig.marks
        return out
    finally:
        rig.close()


def p_c2_queued_run_enters_after_snapshot_load():
    """Stop, start (queued behind the stopped fit), load a snapshot: what does the queued run do when it enters?"""
    rig = Rig()
    try:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        rig.mgr._get_snapshots_dir = lambda: SNAP_DIR
        snap = rig.mgr.save_snapshot("probe c2")
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        result = rig.mgr.load_snapshot(snap["id"])
        out["load_with_a_run_queued_loaded"] = result.get("loaded")
        out["fsm_after_load"] = rig.fsm()
        rig.mgr.model.fit = rig.fit  # the load installed a new model; keep the queued run's fit gated
        n_cmd = len(rig.commands)
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["a_ran_on_past_checkpoint"] = rig.fit.run(0).ran_on.is_set()
        out["b_fit_entered_under"] = rig.fsm() if rig.parked(1) else "b never entered"
        out["b_fit_entered"] = rig.fit.run(1).entered.is_set()
        out["commands_since_load"] = rig.commands[n_cmd:]
        out["ts_while_b_trains"] = rig.ts()
        out["training_active_while_b_trains"] = rig.mgr.get_status()["training_active"]
        out["stop_while_b_trains"] = _answer(rig.mgr.stop_training)
        out["pause_while_b_trains"] = _answer(rig.mgr.pause_training)
        out["second_load_while_b_trains"] = rig.mgr.load_snapshot(snap["id"]).get("loaded")
        if rig.mgr.model is not None:
            rig.mgr.model.fit = rig.fit
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(b_future)
        out["b_ran_on"] = rig.fit.run(1).ran_on.is_set()
        out["marks"] = rig.marks
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_stop_during_final_evaluation():
    """A stop that lands after the fit's post-fit stop check (in the final evaluation), no newer run."""
    rig = Rig()
    try:
        rig.fit.run(0).after = []
        real_final = rig.mgr._compute_final_eval_metrics
        in_final, final_release = threading.Event(), threading.Event()

        def _final_parks():
            in_final.set()
            final_release.wait(timeout=GATE_TIMEOUT)
            return real_final()

        rig.mgr._compute_final_eval_metrics = _final_parks
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.fit.run(0).release.set()
        out["reached_final_eval"] = in_final.wait(timeout=WAIT)
        out["stop"] = _answer(rig.mgr.stop_training)
        final_release.set()
        out["a_join"] = rig.join(old_future)
        out["marks"] = rig.marks
        out["counted"] = list(rig.counted)
        out["fsm_final"] = rig.fsm()
        out["ts_final"] = rig.ts()
        return out
    finally:
        rig.close()


def p_c3_what_stops_a_run_training_under_investigating():
    """After stop, start (queued), restore: the queued run trains under INVESTIGATING. Which request stops it?"""
    rig = Rig()
    try:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        rig.mgr._get_snapshots_dir = lambda: SNAP_DIR
        snap = rig.mgr.save_snapshot("probe c3")
        rig.fit.run(1).after = ["epoch_end"]
        out = {"start_a": rig.start()}
        old_future = rig.mgr._training_future
        rig.parked(0)
        rig.mgr.stop_training()
        out["start_b"] = rig.start()
        b_future = rig.mgr._training_future
        out["restore_loaded"] = rig.mgr.load_snapshot(snap["id"]).get("loaded")
        rig.mgr.model.fit = rig.fit
        rig.fit.run(0).release.set()
        out["a_join"] = rig.join(old_future)
        out["b_training_under"] = rig.fsm() if rig.parked(1) else "b never entered"
        out["stop"] = _answer(rig.mgr.stop_training)
        out["second_start"] = rig.start()
        out["queue_depth_after_second_start"] = rig.mgr._executor._work_queue.qsize()
        out["reset"] = _answer(rig.mgr.reset)
        out["fsm_after_reset"] = rig.fsm()
        rig.fit.run(1).release.set()
        out["b_join"] = rig.join(b_future)
        out["b_ran_on_past_its_checkpoint_after_reset"] = rig.fit.run(1).ran_on.is_set()
        out["counted"] = list(rig.counted)
        out["ts_after_b"] = rig.ts()
        return out
    finally:
        rig.close()


PROBES = [
    ("c3_what_stops_a_run_training_under_investigating", p_c3_what_stops_a_run_training_under_investigating),
    ("basic_stop_start_epoch_end", lambda: p_basic_stop_start("epoch_end")),
    ("basic_stop_start_phase_change", lambda: p_basic_stop_start("phase_change")),
    ("stop_start_stop", p_stop_start_stop),
    ("two_starts_after_one_stop", p_two_starts_after_one_stop),
    ("stop_start_pause", p_stop_start_pause),
    ("reset_after_stop", p_reset_after_stop),
    ("stop_start_reset", p_stop_start_reset),
    ("old_fit_raises", p_old_fit_raises),
    ("old_fit_raises_no_new_run", p_old_fit_raises_no_new_run),
    ("a_refused_starts", p_a_refused_starts),
    ("b_no_checkpoint", p_b_no_checkpoint),
    ("c_snapshot_under_live_stopped_fit", p_c_snapshot_under_live_stopped_fit),
    ("c2_queued_run_enters_after_snapshot_load", p_c2_queued_run_enters_after_snapshot_load),
    ("stop_during_final_evaluation", p_stop_during_final_evaluation),
]


def main() -> int:
    module_file = Path(manager_module.__file__).resolve()
    if TREE not in module_file.parents:
        print(f"PROVENANCE FAILURE: imported {module_file}, not under {TREE}")
        return 2
    results = {"_provenance": str(module_file), "_tree": str(TREE)}
    only = set(sys.argv[4:])
    for name, probe in PROBES:
        if only and name not in only:
            continue
        try:
            results[name] = probe()
        except Exception as exc:
            results[name] = {"PROBE_ERROR": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: done")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(results, fh, indent=2, sort_keys=True, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
