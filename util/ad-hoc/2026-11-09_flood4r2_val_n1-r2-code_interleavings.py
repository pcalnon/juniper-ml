"""
Enumerate forced interleavings of juniper-cascor's run settle against racing pause / resume / stop / reset requests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 11, cascor paused-fit wedge)

Usage: python3 <this> --src <cascor checkout>/src --scenario NAME --out FILE.json [--sample N] [--seed S] [--inner]

How it works. A stub fit (installed as ``mgr.model.fit``, the house pattern) emits training_start,
a checkpointed epoch_end and training_end through the manager's real ``on_event`` sink, then parks.
Optionally the run is paused there (a pause the fit outlives). The fit is then released, and the
settle in ``_run_training`` races one or two request threads calling the real
``pause_training`` / ``resume_training`` / ``stop_training`` / ``reset``. Every manager-level step
of every thread is a YIELD POINT: the state machine's ``is_started`` / ``is_paused`` /
``is_investigating`` / ``handle_command`` / ``mark_completed`` / ``mark_failed``, the pause and stop
events' ``set`` / ``clear`` / ``is_set``, and ``training_state.update_state(status=...)``. With
``--inner`` the call ``_handle_resume`` / ``_handle_start`` make to ``_restore_from_paused`` (made
INSIDE ``handle_command``, i.e. inside the state machine's lock where one exists) is a yield point
too. A scheduler runs exactly one registered thread at a time and grants steps in the order a
schedule gives; every schedule is enumerated (or ``--sample`` of them at random). When a granted
thread blocks on a real lock (the state machine's), the scheduler runs the others until it moves,
and records that as ``blocked``. The code under test is not edited; only its methods are wrapped.

After each schedule: the FSM status, ``training_state`` status, the pause gate, each request's
answer, whether the fit thread is gone, and whether a plain start then runs and completes a new
fit. WEDGE = the FSM is STARTED or PAUSED with no fit behind it, or that start is refused.
"""

import argparse
import itertools
import json
import logging
import random
import sys
import threading
import time
from pathlib import Path

POINT_TIMEOUT = 0.4  # how long a granted thread may take to reach its next point before it counts as blocked
ARRIVE_TIMEOUT = 5.0

_STATUS_FOR_FSM = {"COMPLETED": "Completed", "STOPPED": "Stopped", "FAILED": "Failed", "STARTED": "Started", "PAUSED": "Paused"}


class Scheduler:
    """Run registered threads one step at a time, in a given order."""

    def __init__(self) -> None:
        self.cv = threading.Condition(threading.Lock())
        self.active = False
        self.names = {}
        self.state = {}
        self.at = {}
        self.permit = {}
        self.arrivals = {}
        self.trace = []

    def register(self, tid: str) -> None:
        with self.cv:
            self.names[threading.get_ident()] = tid
            self.state.setdefault(tid, "running")
            self.arrivals.setdefault(tid, 0)
            self.permit.setdefault(tid, False)

    def point(self, label: str) -> None:
        with self.cv:
            tid = self.names.get(threading.get_ident())
            if not self.active or tid is None:
                return
            self.state[tid] = "waiting"
            self.at[tid] = label
            self.arrivals[tid] += 1
            self.cv.notify_all()
            self.cv.wait_for(lambda: self.permit[tid] or not self.active, timeout=60)
            self.permit[tid] = False
            self.state[tid] = "running"
            if self.active:
                self.trace.append(f"{tid}:{label}")

    def done(self, tid: str) -> None:
        with self.cv:
            self.state[tid] = "finished"
            self.cv.notify_all()

    def _grant(self, tid: str) -> str:
        with self.cv:
            if not self.cv.wait_for(lambda: self.state.get(tid) in ("waiting", "finished"), timeout=ARRIVE_TIMEOUT):
                return "not-ready"
            if self.state[tid] == "finished":
                return "finished"
            before = self.arrivals[tid]
            self.permit[tid] = True
            self.cv.notify_all()
            moved = self.cv.wait_for(lambda: self.arrivals[tid] > before or self.state[tid] == "finished", timeout=POINT_TIMEOUT)
            return "ran" if moved else ("blocked", before)

    def step(self, tid: str) -> None:
        result = self._grant(tid)
        if not isinstance(result, tuple):
            return
        _, before = result
        self.trace.append(f"{tid}:BLOCKED")
        for _ in range(20):
            others = [t for t in sorted(self.state) if t != tid and self.state[t] == "waiting"]
            for other in others:
                self._grant(other)
                with self.cv:
                    if self.arrivals[tid] > before or self.state[tid] == "finished":
                        return
            with self.cv:
                if self.cv.wait_for(lambda: self.arrivals[tid] > before or self.state[tid] == "finished", timeout=POINT_TIMEOUT):
                    return
        self.trace.append(f"{tid}:STUCK")

    def stop(self) -> None:
        with self.cv:
            self.active = False
            self.cv.notify_all()


SCHED = Scheduler()


def _yield_event_class():
    class YieldEvent(threading.Event):
        def __init__(self, label: str) -> None:
            super().__init__()
            self._label = label

        def set(self) -> None:
            SCHED.point(f"{self._label}.set")
            super().set()

        def clear(self) -> None:
            SCHED.point(f"{self._label}.clear")
            super().clear()

        def is_set(self) -> bool:
            SCHED.point(f"{self._label}.is_set")
            return super().is_set()

    return YieldEvent


def _wrap(obj, name: str, label_of) -> None:
    original = getattr(obj, name)

    def wrapper(*args, **kwargs):
        label = label_of(*args, **kwargs)
        if label is not None:
            SCHED.point(label)
        return original(*args, **kwargs)

    setattr(obj, name, wrapper)


class GatedFit:
    """Stub ``CascorModel.fit``: emits its events, parks, and on release registers its thread as S."""

    def __init__(self, events) -> None:
        self.events = events
        self.calls = 0
        self.parked = [threading.Event() for _ in range(4)]
        self.release = [threading.Event() for _ in range(4)]
        self.raises = [None] * 4
        self.register_as = [None] * 4

    def __call__(self, x, y, *, X_val=None, y_val=None, on_event=None, **kwargs):
        index = self.calls
        self.calls += 1
        for event in self.events:
            on_event(event)
        self.parked[index].set()
        self.release[index].wait(timeout=20)
        if self.register_as[index]:
            SCHED.register(self.register_as[index])
        if self.raises[index] is not None:
            raise self.raises[index]


def _answer(fn) -> str:
    try:
        fn()
        return "ok"
    except RuntimeError as exc:
        return f"refused: {exc}"


def _run_one(mods, scenario: dict, schedule, inner: bool) -> dict:
    manager_module, TrainingEvent, torch = mods
    global SCHED
    SCHED = Scheduler()
    YieldEvent = _yield_event_class()
    mgr = manager_module.TrainingLifecycleManager()
    mgr.create_network(input_size=2, output_size=2)
    fit = GatedFit((TrainingEvent("training_start", {"n_samples": 8}, 0), TrainingEvent("epoch_end", {"epoch": 25, "epochs": 50, "metrics": {"loss": 0.5}}, 1), TrainingEvent("training_end", {"metrics": {}}, 2)))
    mgr.model.fit = fit
    mgr._pause_event = YieldEvent("pause_event")
    mgr._pause_event.set()
    mgr._stop_event = YieldEvent("stop_event")
    sm = mgr.state_machine
    for name in ("is_started", "is_paused", "is_investigating"):
        _wrap(sm, name, lambda *a, _n=name, **k: _n)
    _wrap(sm, "handle_command", lambda cmd, *a, **k: f"handle_command({cmd.name})")
    _wrap(sm, "mark_completed", lambda *a, **k: "mark_completed")
    _wrap(sm, "mark_failed", lambda *a, **k: "mark_failed")
    if inner:
        _wrap(sm, "_restore_from_paused", lambda *a, **k: "INNER:_restore_from_paused")
    _wrap(mgr.training_state, "update_state", lambda *a, **k: f"update_state({k['status']})" if "status" in k else None)

    counted = []
    real_count = manager_module.inc_training_session_completed
    manager_module.inc_training_session_completed = counted.append
    x = torch.randn(8, 2)
    y = torch.zeros(8, 2)
    y[:4, 0] = 1
    y[4:, 1] = 1
    if scenario.get("test_split"):
        mgr.start_training(X=x, y=y, X_test=x, y_test=y)
    else:
        mgr.start_training(X=x, y=y)
    assert fit.parked[0].wait(timeout=10), "fit never parked"
    if scenario["paused_before"]:
        mgr.pause_training()
    if scenario.get("fit_raises"):
        fit.raises[0] = RuntimeError("fit failed after its last checkpoint")
    fit.register_as[0] = "S"
    answers = {}
    requests = {"P": mgr.pause_training, "R": mgr.resume_training, "T": mgr.stop_training, "X": mgr.reset}
    threads = []
    for tid in scenario["requests"]:

        def target(_tid=tid):
            SCHED.register(_tid)
            try:
                answers[_tid] = _answer(requests[_tid])
            except (Exception, SystemExit, KeyboardInterrupt, GeneratorExit) as exc:  # recorded so a dead request thread can never pass as a clean schedule
                answers[_tid] = f"CRASHED: {type(exc).__name__}: {exc}"
            finally:
                SCHED.done(_tid)

        threads.append(threading.Thread(target=target, daemon=True, name=f"req-{tid}"))
    SCHED.active = True
    for thread in threads:
        thread.start()
    future = mgr._training_future
    future.add_done_callback(lambda f: SCHED.done("S"))
    fit.release[0].set()
    for tid in schedule:
        SCHED.step(tid)
    SCHED.stop()
    fit_error = None
    try:
        future.result(timeout=10)
    except Exception as exc:  # the fit_raises scenario re-raises from the future
        fit_error = f"{type(exc).__name__}: {exc}"
    for thread in threads:
        thread.join(timeout=10)
    status = mgr.get_status()
    fsm = status["state_machine"]["status"]
    ts = status["training_state"]["status"]
    gate_open = threading.Event.is_set(mgr._pause_event)
    fit_alive = not future.done()
    first_run_counted = list(counted)
    final_score_kept = mgr._final_scalar_metrics is not None
    nxt = _answer(lambda: mgr.start_training(X=x, y=y))
    second = None
    if nxt == "ok":
        if fit.parked[1].wait(timeout=10):
            fit.release[1].set()
            try:
                mgr._training_future.result(timeout=10)
            except Exception as exc:
                second = f"raised {exc}"
            second = second or mgr.get_status()["state_machine"]["status"]
        else:
            second = "never parked"
    for ev in fit.release:
        ev.set()
    mgr.shutdown()
    manager_module.inc_training_session_completed = real_count
    wedge = (fsm in ("STARTED", "PAUSED") and not fit_alive) or nxt != "ok" or second != "COMPLETED"
    valid = sorted(answers) == sorted(scenario["requests"]) and not any(a.startswith("CRASHED") for a in answers.values()) and any(t.startswith("S:") for t in SCHED.trace)
    return {
        "VALID": valid,
        "schedule": "".join(schedule),
        "trace": SCHED.trace,
        "answers": answers,
        "fsm": fsm,
        "training_state": ts,
        "training_active": status["training_active"],
        "gate_open": gate_open,
        "fit_error": fit_error,
        "terminal_counts": first_run_counted,
        "final_score_kept": final_score_kept,
        "next_start": nxt,
        "second_run": second,
        "WEDGE": wedge,
        "STATUS_DIVERGES": _STATUS_FOR_FSM.get(fsm) != ts,
    }


SCENARIOS = {
    "pause-vs-completing-settle": {"requests": ["P"], "paused_before": False},
    "pause-vs-completing-settle-after-outlived-pause": {"requests": ["P"], "paused_before": True},
    "resume-vs-completing-settle": {"requests": ["R"], "paused_before": True},
    "resume-vs-failing-settle": {"requests": ["R"], "paused_before": True, "fit_raises": True},
    "pause-vs-failing-settle": {"requests": ["P"], "paused_before": False, "fit_raises": True},
    "stop-vs-completing-settle": {"requests": ["T"], "paused_before": False},
    "stop-vs-completing-settle-after-outlived-pause": {"requests": ["T"], "paused_before": True},
    "reset-vs-completing-settle": {"requests": ["X"], "paused_before": False},
    "reset-vs-completing-settle-after-outlived-pause": {"requests": ["X"], "paused_before": True},
    "resume-then-pause-vs-completing-settle": {"requests": ["R", "P"], "paused_before": True},
    "stop-vs-completing-settle-with-test-split": {"requests": ["T"], "paused_before": False, "test_split": True},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--scenario", required=True, help="a scenario name, a comma-separated list, or 'all'")
    parser.add_argument("--out", required=True, help="output directory; one JSON per scenario plus summary.json")
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20261109)
    parser.add_argument("--inner", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(args.src).resolve()))
    logging.basicConfig(level=logging.ERROR)

    import torch
    from juniper_model_core.events import TrainingEvent

    import api.lifecycle.manager as manager_module

    names = sorted(SCENARIOS) if args.scenario == "all" else args.scenario.split(",")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for name in names:
        summaries.append(_explore(args, name, (manager_module, TrainingEvent, torch), out_dir))
    with open(out_dir / "summary.json", "w") as fh:
        json.dump(summaries, fh, indent=1)
    return 0


def _explore(args, name: str, mods, out_dir: Path) -> dict:
    manager_module = mods[0]
    scenario = dict(SCENARIOS[name])
    n_settle = 4
    n_req = 5 if args.inner else 4
    pool = ["S"] * n_settle
    for r in scenario["requests"]:
        pool += [r] * n_req
    schedules = sorted(set(itertools.permutations(pool))) if len(scenario["requests"]) == 1 else None
    if schedules is None:
        rng = random.Random(args.seed)
        seen = set()
        while len(seen) < max(args.sample, 1):
            perm = pool[:]
            rng.shuffle(perm)
            seen.add(tuple(perm))
        schedules = sorted(seen)
    elif args.sample and args.sample < len(schedules):
        schedules = sorted(random.Random(args.seed).sample(schedules, args.sample))
    results = []
    started = time.monotonic()
    for schedule in schedules:
        results.append(_run_one(mods, scenario, schedule, args.inner))
    outcome_classes = {}
    for r in results:
        key = json.dumps({k: r[k] for k in ("VALID", "answers", "fsm", "training_state", "gate_open", "terminal_counts", "final_score_kept", "next_start", "second_run", "WEDGE", "STATUS_DIVERGES")}, sort_keys=True)
        outcome_classes.setdefault(key, {"count": 0, "example_schedule": r["schedule"], "example_trace": r["trace"]})
        outcome_classes[key]["count"] += 1
    summary = {
        "src": str(Path(args.src).resolve()),
        "manager_file": manager_module.__file__,
        "sm_has_lock": hasattr(manager_module.TrainingStateMachine(), "_lock"),
        "scenario": name,
        "inner_yield": args.inner,
        "schedules": len(results),
        "invalid": sum(not r["VALID"] for r in results),
        "wedged": sum(r["WEDGE"] for r in results),
        "status_diverges": sum(r["STATUS_DIVERGES"] for r in results),
        "gate_closed_after_settle": sum(not r["gate_open"] for r in results),
        "blocked_steps": sum(any(t.endswith(":BLOCKED") for t in r["trace"]) for r in results),
        "stuck": sum(any(t.endswith(":STUCK") for t in r["trace"]) for r in results),
        "seconds": round(time.monotonic() - started, 1),
        "outcome_classes": [{"outcome": json.loads(k), **v} for k, v in sorted(outcome_classes.items(), key=lambda kv: -kv[1]["count"])],
    }
    with open(out_dir / f"{name}.json", "w") as fh:
        json.dump({"summary": summary, "results": results}, fh, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("outcome_classes", "src")}))
    for oc in summary["outcome_classes"]:
        print(f"  {oc['count']:4d}  {json.dumps(oc['outcome'], sort_keys=True)}  e.g. {oc['example_schedule']}")
    return summary


if __name__ == "__main__":
    sys.exit(main())
