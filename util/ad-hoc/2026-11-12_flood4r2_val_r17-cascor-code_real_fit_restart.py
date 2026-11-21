"""
Stop then start against a REAL CascorModel fit (no stub) and time what the stopped fit and the new run do.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17, "cascor: stop-then-start")

Usage: <JuniperCascor1 python> <this> <juniper-cascor tree> <out.json> <seconds before the stop> <seconds to wait for the new run>

The carrier's tests drive a stub fit. This drives the manager's real ``model.fit`` on a small
two-spiral set: start run A, wait, then do canopy's Restart (stop; ``training_active`` false; start),
and record how long the stopped fit took to unwind, how it settled, how long the accepted start waited
before its run began, and the gaps between interrupt checkpoints seen (the bound on that wait). Run on
a main tree and on the carrier tree. Every wait is bounded; the manager is shut down at the end.
"""

import json
import math
import sys
import threading
import time
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
BEFORE_STOP = float(sys.argv[3])
WAIT_NEW = float(sys.argv[4])
# "candidate" as a fifth argument: stop once the FSM phase reads CANDIDATE (waiting at most <seconds before the stop>).
CANDIDATE_MODE = len(sys.argv) > 5 and sys.argv[5] == "candidate"
sys.path.insert(0, str(TREE / "src"))

import torch  # noqa: E402

from api.lifecycle import manager as manager_module  # noqa: E402


def _spirals(n: int):
    xs, ys = [], []
    for label in (0, 1):
        for i in range(n):
            r = i / n * 5.0
            t = 1.75 * i / n * 2 * math.pi + label * math.pi
            xs.append([r * math.sin(t), r * math.cos(t)])
            ys.append([1.0, 0.0] if label == 0 else [0.0, 1.0])
    return torch.tensor(xs, dtype=torch.float32), torch.tensor(ys, dtype=torch.float32)


def main() -> int:
    module_file = Path(manager_module.__file__).resolve()
    if TREE not in module_file.parents:
        print(f"PROVENANCE FAILURE: imported {module_file}")
        return 2
    counted = []
    manager_module.inc_training_session_completed = counted.append
    mgr = manager_module.TrainingLifecycleManager()
    mgr.create_network(input_size=2, output_size=2)
    checkpoints = []
    lock = threading.Lock()
    real_check = mgr._check_for_interrupt

    def _recorded(*args, **kwargs):
        with lock:
            checkpoints.append((time.monotonic(), threading.current_thread().name))
        return real_check(*args, **kwargs)

    mgr._check_for_interrupt = _recorded
    statuses = []
    real_update = mgr.training_state.update_state

    def _update(**fields):
        if "status" in fields:
            statuses.append((round(time.monotonic(), 3), fields["status"]))
        return real_update(**fields)

    mgr.training_state.update_state = _update
    out = {"_provenance": str(module_file)}
    x, y = _spirals(100)
    try:
        t_start = time.monotonic()
        if CANDIDATE_MODE:
            # Short output passes (both knobs, as cascor's AGENTS.md requires), so the fit reaches a candidate round soon.
            mgr.start_training(X=x, y=y, max_epochs=100, output_epochs=100)
        else:
            mgr.start_training(X=x, y=y)
        future_a = mgr._training_future
        if CANDIDATE_MODE:
            phase_deadline = time.monotonic() + BEFORE_STOP
            while time.monotonic() < phase_deadline and mgr.state_machine.phase.name != "CANDIDATE" and not future_a.done():
                time.sleep(0.005)
            time.sleep(0.2)  # well inside the candidate round, not at its edge
        else:
            time.sleep(BEFORE_STOP)
        out["a_done_before_the_stop"] = future_a.done()
        out["phase_at_stop"] = mgr.state_machine.phase.name
        out["hidden_units_at_stop"] = len(mgr.network.hidden_units)
        out["checkpoints_before_stop"] = len(checkpoints)
        t_stop = time.monotonic()
        mgr.stop_training()
        out["training_active_right_after_stop"] = mgr.get_status()["training_active"]
        try:
            mgr.start_training(X=x, y=y)
            out["start_b"] = "ok"
        except (RuntimeError, ValueError) as exc:
            out["start_b"] = f"refused: {exc}"
        out["start_b_answered_after_stop_seconds"] = round(time.monotonic() - t_stop, 4)
        future_b = mgr._training_future
        deadline = time.monotonic() + WAIT_NEW
        a_done_at = None
        b_began_at = None
        while time.monotonic() < deadline:
            if a_done_at is None and future_a.done():
                a_done_at = time.monotonic()
            if b_began_at is None and future_b is not future_a and (future_b.running() or future_b.done()):
                b_began_at = time.monotonic()
            if a_done_at is not None and b_began_at is not None:
                break
            time.sleep(0.01)
        out["stopped_fit_unwound_seconds_after_stop"] = None if a_done_at is None else round(a_done_at - t_stop, 3)
        out["new_run_began_seconds_after_its_200"] = None if b_began_at is None else round(b_began_at - t_stop, 3)
        out["waited_seconds"] = round(time.monotonic() - t_stop, 3)
        out["counted_when_the_new_run_began_or_wait_ended"] = list(counted)
        out["fsm_then"] = mgr.state_machine.status.name
        out["status_writes"] = [status for _when, status in statuses]
        with lock:
            times = [when for when, _name in checkpoints]
        gaps = [later - earlier for earlier, later in zip(times, times[1:])]
        out["checkpoints_seen"] = len(times)
        out["largest_gap_between_checkpoints_seconds"] = round(max(gaps), 3) if gaps else None
        out["seconds_from_start_to_stop"] = round(t_stop - t_start, 3)
    finally:
        mgr.stop_training()
        mgr.shutdown()
    out["counted_final"] = list(counted)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
