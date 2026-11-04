"""Exact-budget boundaries for ``WorkerCoordinator._check_task_timeouts``.

The sweep reassigns a dispatched task only when its age is *strictly greater* than
``task_reassignment_timeout``. A task that has used exactly its budget is still the
assignee's work: stealing it marks a live worker failed and hands the same task to
someone else. A finished task stays finished no matter how old its dispatch stamp is.
The clock is frozen, so the comparisons are exact and the tests do not sleep.
"""

from __future__ import annotations

import pytest

from juniper_service_core.workers.coordinator import ParsedResult, WorkerCoordinator
from juniper_service_core.workers.registry import WorkerRegistry

_NOW = 1_700_000_000.0
_TIMEOUT = 30.0


class _Clock:
    """A frozen ``time.time`` stand-in. ``WorkerCoordinator`` reads this module's clock."""

    def __init__(self, now: float = _NOW) -> None:
        self.now = now

    def time(self) -> float:
        return self.now


class _AcceptingProtocol:
    """A protocol that accepts every result and never inspects the payload."""

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id}, [])

    def result_attachments(self, msg):
        return []

    def parse_result(self, worker_id, msg, frames):
        return ParsedResult(success=True, result={"task_id": msg["task_id"]}, score=None, duration=None)


def _freeze(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    clock = _Clock()
    monkeypatch.setattr("juniper_service_core.workers.coordinator.time.time", clock.time)
    return clock


def _coordinator(timeout: float) -> tuple[WorkerRegistry, WorkerCoordinator]:
    registry = WorkerRegistry()
    coordinator = WorkerCoordinator(registry, _AcceptingProtocol(), task_reassignment_timeout=timeout)
    return registry, coordinator


def test_elapsed_equal_to_the_budget_keeps_the_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    """A task aged exactly ``task_reassignment_timeout`` is still in flight (``>``, not ``>=``)."""
    clock = _freeze(monkeypatch)
    registry, coordinator = _coordinator(_TIMEOUT)
    registry.register("w1", {})
    (task_id,) = coordinator.submit_tasks("round", [{"n": 0}])
    coordinator.get_next_assignment("w1")
    coordinator._pending_tasks[task_id].dispatched_at = clock.now - _TIMEOUT

    coordinator._check_task_timeouts()

    worker = registry.get("w1")
    task = coordinator._pending_tasks[task_id]
    assert worker is not None
    assert worker.active_task_id == task_id
    assert worker.idle is False
    assert worker.tasks_failed == 0
    assert task.assigned_worker_id == "w1"
    assert task.completed is False
    assert coordinator.has_pending_tasks() is False
    assert coordinator.submit_result("w1", {"task_id": task_id}, {}) is True
    assert worker.tasks_completed == 1
    assert worker.tasks_failed == 0
    assert worker.idle is True


def test_zero_budget_keeps_a_task_dispatched_at_this_instant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout 0 still gives the dispatch instant to the assignee; one second later it does not."""
    clock = _freeze(monkeypatch)
    registry, coordinator = _coordinator(0.0)
    registry.register("w1", {})
    (task_id,) = coordinator.submit_tasks("round", [{"n": 0}])
    coordinator.get_next_assignment("w1")
    assert coordinator._pending_tasks[task_id].dispatched_at == clock.now

    coordinator._check_task_timeouts()

    assert registry.get("w1").active_task_id == task_id
    assert registry.get("w1").tasks_failed == 0
    assert coordinator.has_pending_tasks() is False

    coordinator._pending_tasks[task_id].dispatched_at = clock.now - 1.0
    coordinator._check_task_timeouts()

    assert registry.get("w1").idle is True
    assert registry.get("w1").tasks_failed == 1
    assert coordinator._pending_tasks[task_id].assigned_worker_id is None
    assert task_id in coordinator._unassigned_tasks


def test_one_second_past_the_budget_reassigns_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """One second over the budget frees the worker once and queues the task once.

    A second sweep at the same instant must not fail the worker again or enqueue a duplicate.
    The requeued task is then a normal assignment for a different worker.
    """
    clock = _freeze(monkeypatch)
    registry, coordinator = _coordinator(_TIMEOUT)
    registry.register("w1", {})
    registry.register("w2", {})
    (task_id,) = coordinator.submit_tasks("round", [{"n": 0}])
    coordinator.get_next_assignment("w1")
    coordinator._pending_tasks[task_id].dispatched_at = clock.now - _TIMEOUT - 1.0

    coordinator._check_task_timeouts()
    coordinator._check_task_timeouts()

    task = coordinator._pending_tasks[task_id]
    assert registry.get("w1").idle is True
    assert registry.get("w1").tasks_failed == 1
    assert registry.get("w1").active_task_id is None
    assert task.assigned_worker_id is None
    assert task.dispatched_at == clock.now
    assert task.completed is False
    assert coordinator._unassigned_tasks.count(task_id) == 1

    reassigned = coordinator.get_next_assignment("w2")
    assert reassigned is not None
    assert reassigned[0]["task_id"] == task_id
    assert registry.get("w2").active_task_id == task_id
    assert coordinator.submit_result("w2", {"task_id": task_id}, {}) is True
    assert registry.get("w2").tasks_completed == 1
    assert registry.get("w1").tasks_failed == 1


def test_a_completed_task_older_than_the_budget_is_not_requeued(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepting a result leaves the dispatch stamp set. Age alone must not put that task back in the queue."""
    clock = _freeze(monkeypatch)
    registry, coordinator = _coordinator(_TIMEOUT)
    registry.register("w1", {})
    (task_id,) = coordinator.submit_tasks("round", [{"n": 0}])
    coordinator.get_next_assignment("w1")
    assert coordinator.submit_result("w1", {"task_id": task_id}, {}) is True
    coordinator._pending_tasks[task_id].dispatched_at = clock.now - _TIMEOUT - 10.0

    coordinator._check_task_timeouts()

    task = coordinator._pending_tasks[task_id]
    assert task.completed is True
    assert task.assigned_worker_id == "w1"
    assert task_id not in coordinator._unassigned_tasks
    assert coordinator.has_pending_tasks() is False
    assert registry.get("w1").tasks_completed == 1
    assert registry.get("w1").tasks_failed == 0
    assert registry.get("w1").idle is True
    assert coordinator.collect_results(timeout=0.0) == [{"task_id": task_id}]
