"""
Probe the worker anomaly-detector and task-reassignment claims carried by the flood-4 docs carrier (#2442, #2464).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 docs carrier validation (claims lens, slice B); drafts juniper-ml#2442 and #2464

Run with PYTHONPATH pointing at this checkout's juniper-service-core/. Read-only: imports the package and
drives it in memory; writes nothing to disk. Prints one line per probed claim: PASS/FAIL plus the observed value.
"""

from __future__ import annotations

import hashlib
import logging
import sys
import time

from juniper_service_core.workers import coordinator as coord_mod
from juniper_service_core.workers.coordinator import JsonTaskProtocol, WorkerCoordinator
from juniper_service_core.workers.registry import WorkerRegistry
from juniper_service_core.workers.security import AnomalyDetector

RESULTS: list[str] = []


def record(label: str, ok: bool, observed: object) -> None:
    line = f"{'PASS' if ok else 'FAIL'} | {label} | observed={observed!r}"
    RESULTS.append(line)
    print(line)


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def probe_anomaly() -> None:
    det = AnomalyDetector()
    r = det.check_result("a", score=0.5, training_duration=0.1, task_id="t")
    record("2442 duration 0.1 is clean", r == [], r)
    r = det.check_result("b", score=0.5, training_duration=0.099, task_id="t")
    record("2442 0.099 flags 'suspiciously_fast: 0.099s (min=0.1s)'", r == ["suspiciously_fast: 0.099s (min=0.1s)"], r)
    r = AnomalyDetector().check_result("c", score=0.999, training_duration=1.0, task_id="t")
    record("2442 score 0.999 is clean", r == [], r)
    r = AnomalyDetector().check_result("d", score=0.9990001, training_duration=1.0, task_id="t")
    record("2442 0.9990001 flags and prints 'perfect_score: 0.999000'", r == ["perfect_score: 0.999000"], r)
    for s in (0.001, -0.001):
        r = AnomalyDetector().check_result("e", score=s, training_duration=1.0, task_id="t")
        record(f"2442 stale bound {s} is clean", r == [], r)
    for s in (0.000999, -0.0005):
        r = AnomalyDetector().check_result("f", score=s, training_duration=1.0, task_id="t")
        record(f"2442 stale {s} flags", any(a.startswith("stale_score") for a in r), r)
    r = AnomalyDetector().check_result("g", score=-0.5, training_duration=1.0, task_id="t")
    record("2442 -0.5 neither stale nor perfect", r == [], r)
    r = AnomalyDetector().check_result("h", score=1.0, training_duration=0.0, task_id="t")
    record("2442 1.0 in 0.0 s is fast AND perfect", [a.split(":")[0] for a in r] == ["suspiciously_fast", "perfect_score"], r)

    det = AnomalyDetector()
    r1 = det.check_result("w", score=0.42, training_duration=1.0, task_id="t1")
    r2 = det.check_result("w", score=0.42, training_duration=1.0, task_id="t2")
    r3 = det.check_result("w", score=0.42, training_duration=1.0, task_id="t3")
    record("2442 two identical clean, third flags", r1 == [] and r2 == [] and any(a.startswith("duplicate_scores") for a in r3), (r1, r2, r3))

    fmt = [f"{x:.6f}" for x in (0.42, 0.4200004, 0.4199995, 0.4200006)]
    record("2442 0.42/0.4200004/0.4199995 print 0.420000; 0.4200006 prints 0.420001", fmt == ["0.420000", "0.420000", "0.420000", "0.420001"], fmt)
    det = AnomalyDetector()
    outs = [det.check_result("w", score=s, training_duration=1.0, task_id=f"t{i}") for i, s in enumerate((0.42, 0.4200004, 0.4199995))]
    record("2442 0.42, 0.4200004, 0.4199995 -> third is duplicate", outs[0] == [] and outs[1] == [] and any(a.startswith("duplicate_scores") for a in outs[2]), outs)
    det = AnomalyDetector()
    outs = [det.check_result("w", score=s, training_duration=1.0, task_id=f"t{i}") for i, s in enumerate((0.42, 0.42, 0.4200006))]
    record("2442 0.4200006 is not a duplicate of 0.42", outs[2] == [], outs)

    det = AnomalyDetector(duplicate_window=3)
    outs = [det.check_result("w", score=s, training_duration=1.0, task_id=f"t{i}") for i, s in enumerate((0.10, 0.50, 0.50, 0.50))]
    stats = det.get_worker_stats("w")["total_results"]
    record("2442 window=3: 0.10,0.50,0.50 no flag; next 0.50 flags; total_results 3", outs[2] == [] and any(a.startswith("duplicate_scores") for a in outs[3]) and stats == 3, (outs, stats))

    det = AnomalyDetector()
    outs = [det.check_result("w", score=s, training_duration=1.0, task_id=f"t{i}") for i, s in enumerate((0.42, 0.42, 0.42, 0.43))]
    record("2442 a later different score clears the flag on that result", any(a.startswith("duplicate_scores") for a in outs[2]) and outs[3] == [], outs)

    det = AnomalyDetector()
    raw = [0.42, 0.4200004, 0.4199995]
    outs = [det.check_result("w", score=s, training_duration=1.0, task_id=f"t{i}") for i, s in enumerate(raw)]
    expected_hash = hashlib.sha256(str(sorted(raw)).encode()).hexdigest()[:8]
    msg = [a for a in outs[2] if a.startswith("duplicate_scores")]
    record("2442 message 'duplicate_scores: 1/3 unique (hash=<sha256(str(sorted(raw)))[:8]>)'", msg == [f"duplicate_scores: 1/3 unique (hash={expected_hash})"], msg)
    det2 = AnomalyDetector()
    outs2 = [det2.check_result("w", score=0.42, training_duration=1.0, task_id=f"t{i}") for i in range(3)]
    msg2 = [a for a in outs2[2] if a.startswith("duplicate_scores")]
    record("2442 two windows printing one score can carry different hashes", msg and msg2 and msg[0] != msg2[0], (msg, msg2))

    det = AnomalyDetector()
    outs = [det.check_result("w", score=0.42, training_duration=1.0, task_id=f"t{i}") for i in range(12)]
    ns = [a.split(" ")[1] for o in outs for a in o if a.startswith("duplicate_scores")]
    record("2442 <n> runs 3 through duplicate_window (10)", ns[0] == "1/3" and ns[-1] == "1/10", ns)
    record("2442 total_results stuck at 10 (default window)", det.get_worker_stats("w")["total_results"] == 10, det.get_worker_stats("w"))
    record("2442 unknown worker -> {'total_results': 0}", AnomalyDetector().get_worker_stats("x") == {"total_results": 0}, AnomalyDetector().get_worker_stats("x"))

    # Edge: duplicate_window=0 (a slice of -0 keeps the whole list)
    det = AnomalyDetector(duplicate_window=0)
    for i in range(5):
        det.check_result("w", score=0.42, training_duration=1.0, task_id=f"t{i}")
    record("2442 EDGE duplicate_window=0 'trimmed to the last duplicate_window records'", det.get_worker_stats("w")["total_results"] == 0, det.get_worker_stats("w")["total_results"])
    det = AnomalyDetector(duplicate_window=2)
    outs = [det.check_result("w", score=0.42, training_duration=1.0, task_id=f"t{i}") for i in range(5)]
    record("2442 EDGE duplicate_window=2 never flags duplicate", all(not o for o in outs), outs)


def probe_coordinator_anomaly() -> None:
    cap = _Capture()
    for name in ("juniper_service_core.workers.coordinator", "juniper_service_core.workers.security"):
        lg = logging.getLogger(name)
        lg.addHandler(cap)
        lg.setLevel(logging.DEBUG)
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, JsonTaskProtocol())
    record("2442 coordinator default detector is None", coord.anomaly_detector is None, coord.anomaly_detector)
    coord2 = WorkerCoordinator(reg, JsonTaskProtocol(), anomaly_detector=AnomalyDetector())
    record("2442 constructor kwarg also wires a detector (not only assignment)", isinstance(coord2.anomaly_detector, AnomalyDetector), type(coord2.anomaly_detector).__name__)

    coord.anomaly_detector = AnomalyDetector()
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")
    cap.records.clear()
    ok = coord.submit_result("w1", {"task_id": tid, "score": 0.5}, {})
    warn = [(r.levelname, r.name, r.getMessage()) for r in cap.records if r.levelno >= logging.WARNING]
    record("2442 score w/o duration: accepted, logs suspiciously_fast 0.000s at WARNING from both loggers", ok is True and any("suspiciously_fast: 0.000s" in m for _, _, m in warn) and {n for _, n, _ in warn} == {"juniper_service_core.workers.coordinator", "juniper_service_core.workers.security"} and all(lv == "WARNING" for lv, _, _ in warn), warn)

    (tid2,) = coord.submit_tasks("r2", [{"c": 0}])
    coord.get_next_assignment("w1")
    cap.records.clear()
    ok = coord.submit_result("w1", {"task_id": tid2, "score": None, "duration": 0.0}, {})
    record("2442 JSON null score skips the check (no ANOMALY log)", ok is True and not any("ANOMALY" in r.getMessage() for r in cap.records), [r.getMessage() for r in cap.records])

    # Default coordinator (no detector): a scored result with no duration logs nothing about anomalies.
    reg3 = WorkerRegistry()
    reg3.register("w9", {})
    coord3 = WorkerCoordinator(reg3, JsonTaskProtocol())
    (tid3,) = coord3.submit_tasks("r3", [{"c": 0}])
    coord3.get_next_assignment("w9")
    cap.records.clear()
    ok = coord3.submit_result("w9", {"task_id": tid3, "score": 0.5}, {})
    record("2442 default (no detector): scored result without duration logs NO suspiciously_fast", ok is True and not any("suspiciously_fast" in r.getMessage() for r in cap.records), [r.getMessage() for r in cap.records])
    for name in ("juniper_service_core.workers.coordinator", "juniper_service_core.workers.security"):
        logging.getLogger(name).removeHandler(cap)


class _Clock:
    def __init__(self, t: float) -> None:
        self.t = t

    def time(self) -> float:
        return self.t


def _fresh(timeout: float = 120.0):
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, JsonTaskProtocol(), task_reassignment_timeout=timeout)
    return reg, coord


def probe_timeout() -> None:
    cap = _Capture()
    lg = logging.getLogger("juniper_service_core.workers.coordinator")
    lg.addHandler(cap)
    lg.setLevel(logging.DEBUG)
    real_time = coord_mod.time
    clock = _Clock(1_000_000.0)
    real_monotonic = time.monotonic

    class _TimeShim:
        @staticmethod
        def time() -> float:
            return clock.time()

        @staticmethod
        def monotonic() -> float:
            return real_monotonic()

    coord_mod.time = _TimeShim  # type: ignore[assignment]
    try:
        reg, coord = _fresh()
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        task = coord._pending_tasks[tid]
        record("2464 dispatched_at written at get_next_assignment (== shim now)", task.dispatched_at == clock.t, task.dispatched_at)
        clock.t = task.dispatched_at + 120.0
        cap.records.clear()
        coord._check_task_timeouts()
        record("2464 age == 120.0 stays assigned, no warning, tasks_failed 0, worker busy", task.assigned_worker_id == "w1" and not cap.records and reg.get("w1").tasks_failed == 0 and reg.get("w1").idle is False, (task.assigned_worker_id, [r.getMessage() for r in cap.records], reg.get("w1").tasks_failed))
        ok_eq = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        record("2464 at age == timeout the assignee can still submit and is accepted", ok_eq is True, ok_eq)

        reg, coord = _fresh()
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        task = coord._pending_tasks[tid]
        clock.t = task.dispatched_at + 120.0 + 1e-6
        cap.records.clear()
        coord._check_task_timeouts()
        msgs = [r.getMessage() for r in cap.records if r.levelno >= logging.WARNING]
        record("2464 timeout+1e-6 requeues; warning prints (120.0s); tail append; dispatched_at=now; tasks_failed 1; idle", task.assigned_worker_id is None and coord._unassigned_tasks[-1] == tid and task.dispatched_at == clock.t and reg.get("w1").tasks_failed == 1 and reg.get("w1").idle and any("(120.0s)" in m for m in msgs), (msgs, coord._unassigned_tasks, reg.get("w1").tasks_failed))
        cap.records.clear()
        clock.t += 500.0
        coord._check_task_timeouts()
        record("2464 second sweep while unassigned does nothing", reg.get("w1").tasks_failed == 1 and coord._unassigned_tasks.count(tid) == 1 and not cap.records, (reg.get("w1").tasks_failed, coord._unassigned_tasks))

        # late result after sweep, still queued
        cap.records.clear()
        late = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        record("2464 late result while queued: rejected 'Result for unassigned task'", late is False and any("Result for unassigned task" in r.getMessage() for r in cap.records), [r.getMessage() for r in cap.records])

        # another worker takes it
        reg.register("w2", {})
        coord.get_next_assignment("w2")
        cap.records.clear()
        late2 = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        record("2464 late result once another worker holds it: '(assigned to w2)'", late2 is False and any("rejected (assigned to w2)" in r.getMessage() for r in cap.records), [r.getMessage() for r in cap.records])

        # same worker re-handed the same task: first accepted, second Duplicate
        _reg, coord = _fresh()
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        clock.t = coord._pending_tasks[tid].dispatched_at + 121.0
        coord._check_task_timeouts()
        again = coord.get_next_assignment("w1")
        a = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        cap.records.clear()
        b = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        record("2464 same worker re-handed: first accepted, second 'Duplicate result'", again is not None and a is True and b is False and any("Duplicate result" in r.getMessage() for r in cap.records), (a, b, [r.getMessage() for r in cap.records]))

        # Cross-round edge: duplicate arriving after a new submit_tasks round
        coord.submit_tasks("r-next", [{"c": 1}])
        cap.records.clear()
        c = coord.submit_result("w1", {"task_id": tid, "score": 0.5, "duration": 1.0}, {})
        record("2464 EDGE second copy after the NEXT round started is still 'Duplicate result'", c is False, (c, [r.getMessage() for r in cap.records], len(coord._results)))

        # active_task_id is a different task
        reg, coord = _fresh()
        t1, t2 = coord.submit_tasks("r", [{"c": 0}, {"c": 1}])
        coord.get_next_assignment("w1")  # t1, worker active t1
        coord._pending_tasks[t2].assigned_worker_id = "w1"  # orphan-shaped
        coord._unassigned_tasks.remove(t2)
        clock.t = coord._pending_tasks[t2].dispatched_at + 121.0
        coord._pending_tasks[t1].dispatched_at = clock.t  # keep t1 fresh
        coord._check_task_timeouts()
        record("2464 active_task_id a different task: tasks_failed unchanged, other stays active, requeue", reg.get("w1").tasks_failed == 0 and reg.get("w1").active_task_id == t1 and coord._pending_tasks[t2].assigned_worker_id is None and t2 in coord._unassigned_tasks, (reg.get("w1").tasks_failed, reg.get("w1").active_task_id))

        # worker gone from registry
        reg, coord = _fresh()
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        reg.deregister("w1")
        clock.t = coord._pending_tasks[tid].dispatched_at + 121.0
        coord._check_task_timeouts()
        record("2464 worker gone: no complete_task, same requeue", coord._pending_tasks[tid].assigned_worker_id is None and tid in coord._unassigned_tasks, coord._unassigned_tasks)

        # active_task_id None (registry idle while the coordinator still names it)
        reg, coord = _fresh()
        t1, t2 = coord.submit_tasks("r", [{"c": 0}, {"c": 1}])
        coord.get_next_assignment("w1")  # t1
        nxt = coord.get_next_assignment("w1")  # assign_task refused (busy) but task t2 marked assigned
        record("2464 EDGE get_next_assignment hands a busy worker a 2nd task (assign_task refused, coordinator assigns anyway)", nxt is not None and coord._pending_tasks[t2].assigned_worker_id == "w1" and reg.get("w1").active_task_id == t1, (nxt is not None, reg.get("w1").active_task_id))
        ok1 = coord.submit_result("w1", {"task_id": t1, "score": 0.5, "duration": 1.0}, {})
        clock.t = coord._pending_tasks[t2].dispatched_at + 121.0
        coord._check_task_timeouts()
        record("2464 EDGE registry active_task_id None while task assigned: row not in the docs table (no tasks_failed)", ok1 and reg.get("w1").active_task_id is None and reg.get("w1").tasks_failed == 0 and t2 in coord._unassigned_tasks, (reg.get("w1").active_task_id, reg.get("w1").tasks_failed))

        # timeout 0
        _reg, coord = _fresh(timeout=0.0)
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        clock.t = coord._pending_tasks[tid].dispatched_at
        coord._check_task_timeouts()
        stay = coord._pending_tasks[tid].assigned_worker_id == "w1"
        clock.t += 1.0
        coord._check_task_timeouts()
        record("2464 timeout 0: same instant stays; one second requeues", stay and coord._pending_tasks[tid].assigned_worker_id is None, stay)

        # dispatch pops the head
        reg, coord = _fresh()
        t1, t2, t3 = coord.submit_tasks("r", [{"c": 0}, {"c": 1}, {"c": 2}])
        coord.get_next_assignment("w1")  # t1
        clock.t = coord._pending_tasks[t1].dispatched_at + 121.0
        coord._check_task_timeouts()
        order = list(coord._unassigned_tasks)
        nxt = coord.get_next_assignment("w1")
        record("2464 requeued task goes to the tail; dispatch pops the head (t2 first)", order == [t2, t3, t1] and nxt[0]["task_id"] == t2, (order, nxt[0]["task_id"] == t2))
    finally:
        coord_mod.time = real_time
        lg.removeHandler(cap)

    # monitor waits before the first pass
    reg = WorkerRegistry()
    reg.register("w1", {})
    coord = WorkerCoordinator(reg, JsonTaskProtocol(), task_reassignment_timeout=0.0, health_check_interval=0.6)
    (tid,) = coord.submit_tasks("r", [{"c": 0}])
    coord.get_next_assignment("w1")
    coord._pending_tasks[tid].dispatched_at = time.time() - 10.0
    coord.start_monitor()
    time.sleep(0.25)
    before = coord._pending_tasks[tid].assigned_worker_id
    time.sleep(0.7)
    after = coord._pending_tasks[tid].assigned_worker_id
    coord.stop_monitor()
    record("2464 monitor waits health_check_interval before the first pass", before == "w1" and after is None, (before, after))


def probe_late_result_edges() -> None:
    """Two late-result paths the carried text maps to a log line."""
    cap = _Capture()
    lg = logging.getLogger("juniper_service_core.workers.coordinator")
    lg.addHandler(cap)
    lg.setLevel(logging.DEBUG)
    try:
        # (a) another worker already COMPLETED the requeued task: the original worker's late result
        reg = WorkerRegistry()
        reg.register("w1", {})
        reg.register("w2", {})
        coord = WorkerCoordinator(reg, JsonTaskProtocol(), task_reassignment_timeout=1.0)
        (tid,) = coord.submit_tasks("r", [{"c": 0}])
        coord.get_next_assignment("w1")
        coord._pending_tasks[tid].dispatched_at = time.time() - 10.0
        coord._check_task_timeouts()
        coord.get_next_assignment("w2")
        assert coord.submit_result("w2", {"task_id": tid, "result": "w2"}, {}) is True
        cap.records.clear()
        late = coord.submit_result("w1", {"task_id": tid, "result": "w1-late"}, {})
        msgs = [r.getMessage() for r in cap.records]
        record("2464 EDGE late result after ANOTHER worker completed it logs 'Duplicate result' (not 'assigned to')", late is False and any("Duplicate result" in m for m in msgs) and not any("assigned to" in m for m in msgs), msgs)

        # (b) realistic two-copy flow across a round boundary: copy 1 accepted completes round 1,
        # the caller submits round 2, then copy 2 arrives.
        reg = WorkerRegistry()
        reg.register("w1", {})
        coord = WorkerCoordinator(reg, JsonTaskProtocol(), task_reassignment_timeout=1.0)
        (tid,) = coord.submit_tasks("round-1", [{"c": 0}])
        coord.get_next_assignment("w1")
        coord._pending_tasks[tid].dispatched_at = time.time() - 10.0
        coord._check_task_timeouts()
        coord.get_next_assignment("w1")  # same worker handed the same task again
        first = coord.submit_result("w1", {"task_id": tid, "result": "copy-1"}, {})
        round1 = coord.collect_results(timeout=0.1)
        (tid2,) = coord.submit_tasks("round-2", [{"c": 1}])
        cap.records.clear()
        second = coord.submit_result("w1", {"task_id": tid, "result": "copy-2"}, {})
        round2 = coord.collect_results(timeout=0.1)
        msgs = [r.getMessage() for r in cap.records]
        record(
            "2464 EDGE copy 2 after round 2 starts: 'the other is rejected as a Duplicate result'",
            first is True and second is False,
            {"first": first, "round1": round1, "second": second, "round2_results": round2, "round2_task_done": coord._pending_tasks[tid2].completed, "logs": msgs},
        )
    finally:
        lg.removeHandler(cap)


def main() -> int:
    print(sys.version.split()[0])
    probe_anomaly()
    probe_coordinator_anomaly()
    probe_timeout()
    probe_late_result_edges()
    fails = [r for r in RESULTS if r.startswith("FAIL")]
    print(f"TOTAL {len(RESULTS)} FAIL {len(fails)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
