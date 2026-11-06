"""A worker anomaly warning does not reject the result.

The detector unit tests call ``AnomalyDetector.check_result`` directly. They never
drive ``WorkerCoordinator.submit_result``, which is the seam that decides whether a
warning is only a log line.

Two coercions live only on that seam:

* A present ``score`` with no ``duration`` is timed as ``parsed.duration or 0.0``.
  ``0.0`` is under the fast bound, so the log says ``suspiciously_fast`` and the
  result is still stored as a success. Skipping the check when duration is missing
  would hide that payload; rejecting on the warning would drop a real result.
* ``score`` of ``0`` is falsy but not missing. The check is ``parsed.score is not
  None``. A truthiness check would skip the stale-score warning for a stuck worker
  and still look green.

A clean score and duration is the control: the same path stores the result and
emits no anomaly warning.
"""

from __future__ import annotations

import logging

import pytest

from juniper_service_core.workers import AnomalyDetector, JsonTaskProtocol, WorkerCoordinator, WorkerRegistry


def _dispatched() -> tuple[WorkerRegistry, WorkerCoordinator, str]:
    registry = WorkerRegistry()
    registry.register("w1", {})
    coordinator = WorkerCoordinator(registry, JsonTaskProtocol(), anomaly_detector=AnomalyDetector())
    (task_id,) = coordinator.submit_tasks("round-1", [{"payload-key": 1}])
    assignment = coordinator.get_next_assignment("w1")
    assert assignment is not None
    message, frames = assignment
    assert message["task_id"] == task_id
    assert frames == []
    return registry, coordinator, task_id


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING]


def test_missing_duration_warns_fast_and_stores_the_result(caplog: pytest.LogCaptureFixture) -> None:
    """Score without duration is timed as 0.0s, warned, and accepted as a success."""
    registry, coordinator, task_id = _dispatched()
    with caplog.at_level(logging.WARNING):
        accepted = coordinator.submit_result(
            "w1",
            {"task_id": task_id, "success": True, "score": 0.5, "result": {"ok": True}},
            {},
        )

    assert accepted is True
    assert coordinator.collect_results(timeout=0.5) == [{"ok": True}]
    worker = registry.get("w1")
    assert worker is not None
    assert worker.tasks_completed == 1
    assert worker.tasks_failed == 0
    assert worker.idle is True

    detector = coordinator.anomaly_detector
    assert detector is not None
    stats = detector.get_worker_stats("w1")
    assert stats["total_results"] == 1
    assert stats["min_duration"] == 0.0
    assert stats["max_score"] == 0.5

    warnings = _warnings(caplog)
    assert any("ANOMALY:" in message and "suspiciously_fast: 0.000s" in message for message in warnings)
    assert any(f"Anomalies detected for worker w1 on task {task_id}" in message and "suspiciously_fast" in message for message in warnings)
    assert not any("stale_score" in message or "perfect_score" in message for message in warnings)


def test_zero_score_is_checked_for_staleness_and_stored(caplog: pytest.LogCaptureFixture) -> None:
    """A JSON score of 0 is stale, not 'no score', and the result is still stored."""
    registry, coordinator, task_id = _dispatched()
    with caplog.at_level(logging.WARNING):
        accepted = coordinator.submit_result(
            "w1",
            {"task_id": task_id, "success": True, "score": 0, "duration": 1.0, "result": "kept"},
            {},
        )

    assert accepted is True
    assert coordinator.collect_results(timeout=0.5) == ["kept"]
    worker = registry.get("w1")
    assert worker is not None
    assert worker.tasks_completed == 1
    assert worker.tasks_failed == 0

    detector = coordinator.anomaly_detector
    assert detector is not None
    stats = detector.get_worker_stats("w1")
    assert stats["total_results"] == 1
    assert stats["max_score"] == 0
    assert stats["min_duration"] == 1.0

    warnings = _warnings(caplog)
    assert any("stale_score: 0.000000" in message for message in warnings)
    assert any(f"Anomalies detected for worker w1 on task {task_id}" in message and "stale_score" in message for message in warnings)
    assert not any("suspiciously_fast" in message for message in warnings)


def test_clean_result_stores_with_no_anomaly_warning(caplog: pytest.LogCaptureFixture) -> None:
    """A mid score with a real duration is stored and does not warn."""
    registry, coordinator, task_id = _dispatched()
    with caplog.at_level(logging.WARNING):
        accepted = coordinator.submit_result(
            "w1",
            {"task_id": task_id, "score": 0.5, "duration": 1.0, "result": "clean"},
            {},
        )

    assert accepted is True
    assert coordinator.collect_results(timeout=0.5) == ["clean"]
    worker = registry.get("w1")
    assert worker is not None
    assert worker.tasks_completed == 1
    assert worker.tasks_failed == 0

    detector = coordinator.anomaly_detector
    assert detector is not None
    stats = detector.get_worker_stats("w1")
    assert stats["total_results"] == 1
    assert stats["max_score"] == 0.5
    assert stats["min_duration"] == 1.0
    assert _warnings(caplog) == []
