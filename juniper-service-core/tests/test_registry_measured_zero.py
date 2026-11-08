"""A measured zero is a heartbeat, and a worker aged exactly one timeout is stale.

``None`` on an enriched heartbeat field means "the worker did not report this". ``0``,
``0.0``, and ``[]`` mean it did: the worker is idle, the GPU is idle, the last task took
no measurable time, the duration window was cleared, or the task counters were reset.
A truthiness check (``if field:``) keeps the previous busy / hot / failed reading, so
dispatch and the Prometheus scrape keep describing a worker that has gone quiet.

``WorkerRegistration.is_alive`` is a strict ``<`` against the timeout. A heartbeat aged
exactly one timeout is already stale: the worker is not offered work and is eligible to
be reaped. ``<=`` would keep that worker in the idle pool for one more timeout.

The collector has the matching scrape contract. A reported GPU of 0% and a last-task
duration of 0s are emitted. A field that is still ``None`` is omitted, so "no data" and
"measured zero" stay distinct. A one-sample duration window does not invent a percentile
and must not be logged as a malformed snapshot (``statistics.quantiles`` raises below two
points, and that exception would drop the rest of the worker's samples). A heartbeat
timestamp ahead of the scrape clock clamps age at 0. A wired pending-task source that
returns 0 emits 0; only a missing source omits the gauge.

Hermetic. The registry cases are stdlib. The collector case skips when ``prometheus_client``
is absent. Production code is unchanged.
"""

from __future__ import annotations

import logging

import pytest

from juniper_service_core.workers.metrics import WorkerRegistryCollector
from juniper_service_core.workers.registry import WorkerRegistration, WorkerRegistry


def test_measured_zero_overwrites_the_prior_heartbeat() -> None:
    """``0`` / ``0.0`` / ``[]`` replace a prior reading; a later sparse tick keeps those zeros."""
    reg = WorkerRegistration(worker_id="w1")
    reg.record_heartbeat(
        in_flight_tasks=4,
        rss_mb=800.0,
        tasks_completed=9,
        tasks_failed=1,
        last_task_duration_seconds=3.5,
        recent_task_durations_seconds=[3.5, 4.0],
        gpu_utilization_pct=90.0,
        last_task_completed_at=50.0,
    )
    assert reg.health_score == 0.9

    reg.record_heartbeat(
        in_flight_tasks=0,
        rss_mb=0.0,
        tasks_completed=0,
        tasks_failed=4,
        last_task_duration_seconds=0.0,
        recent_task_durations_seconds=[],
        gpu_utilization_pct=0.0,
        last_task_completed_at=0.0,
    )
    assert reg.in_flight_tasks == 0
    assert reg.rss_mb == 0.0
    assert reg.tasks_completed == 0
    assert reg.tasks_failed == 4
    assert reg.health_score == 0.0
    assert reg.last_task_duration_seconds == 0.0
    assert reg.recent_task_durations_seconds == []
    assert reg.gpu_utilization_pct == 0.0
    assert reg.last_task_completed_at == 0.0

    # Both counters cleared: no tasks yet, so health is the neutral 1.0, not "still all failures".
    reg.record_heartbeat(tasks_completed=0, tasks_failed=0)
    assert reg.health_score == 1.0
    assert reg.gpu_utilization_pct == 0.0

    reg.record_heartbeat()
    assert reg.in_flight_tasks == 0
    assert reg.rss_mb == 0.0
    assert reg.tasks_completed == 0
    assert reg.tasks_failed == 0
    assert reg.last_task_duration_seconds == 0.0
    assert reg.recent_task_durations_seconds == []
    assert reg.gpu_utilization_pct == 0.0
    assert reg.last_task_completed_at == 0.0


def test_registry_heartbeat_zero_reaches_the_metrics_snapshot() -> None:
    """The public heartbeat path and the scrape snapshot both keep a measured zero."""
    registry = WorkerRegistry()
    registry.register("w1", {})
    assert registry.heartbeat(
        "w1",
        in_flight_tasks=2,
        rss_mb=128.0,
        gpu_utilization_pct=40.0,
        last_task_duration_seconds=1.5,
        recent_task_durations_seconds=[1.0, 1.5],
        tasks_completed=3,
        tasks_failed=1,
    )
    assert registry.heartbeat(
        "w1",
        in_flight_tasks=0,
        rss_mb=0.0,
        gpu_utilization_pct=0.0,
        last_task_duration_seconds=0.0,
        recent_task_durations_seconds=[],
        tasks_completed=0,
        tasks_failed=0,
    )
    live = registry.get("w1")
    assert live is not None
    assert live.in_flight_tasks == 0
    assert live.health_score == 1.0
    assert live.recent_task_durations_seconds == []

    frozen = registry.snapshot_for_metrics()
    assert len(frozen) == 1
    assert frozen[0]["gpu_utilization_pct"] == 0.0
    assert frozen[0]["last_task_duration_seconds"] == 0.0
    assert frozen[0]["recent_task_durations_seconds"] == ()


def test_heartbeat_aged_exactly_one_timeout_is_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    """Age == timeout is not alive. One microsecond inside the window still is."""
    now = 1_000_000.0
    timeout = 30.0
    monkeypatch.setattr("juniper_service_core.workers.registry.time.time", lambda: now)

    registry = WorkerRegistry(heartbeat_timeout=timeout)
    registry.register("edge", {})
    registry.register("inside", {})
    registry.get("edge").last_heartbeat = now - timeout
    registry.get("inside").last_heartbeat = now - timeout + 1e-6

    assert registry.get("edge").is_alive(timeout) is False
    assert registry.get("inside").is_alive(timeout) is True
    assert [worker.worker_id for worker in registry.get_stale_workers()] == ["edge"]
    assert [worker.worker_id for worker in registry.get_idle_workers()] == ["inside"]
    assert registry.available_worker_count == 1


def _sample_values(families: dict, name: str) -> dict[str, float]:
    return {sample.labels["worker_id"]: sample.value for sample in families[name].samples}


def test_collector_emits_measured_zeros_and_clamps_a_future_heartbeat(caplog: pytest.LogCaptureFixture) -> None:
    """0% GPU and a 0s task are scraped. One duration is not a percentile. Future age clamps to 0."""
    pytest.importorskip("prometheus_client")
    now = 1_000_000.0
    registry = WorkerRegistry()
    registry.register("idle", {})
    registry.heartbeat(
        "idle",
        gpu_utilization_pct=0.0,
        last_task_duration_seconds=0.0,
        recent_task_durations_seconds=[0.0],
    )
    registry.register("pair", {})
    registry.heartbeat(
        "pair",
        gpu_utilization_pct=0.0,
        last_task_duration_seconds=0.0,
        recent_task_durations_seconds=[0.0, 0.0],
    )
    registry.register("silent", {})
    # Scrape clock is fixed, so pin the heartbeats against it. idle is ahead (clock skew).
    registry.get("idle").last_heartbeat = now + 5.0
    registry.get("pair").last_heartbeat = now - 10.0
    registry.get("silent").last_heartbeat = now

    collector = WorkerRegistryCollector(
        registry,
        pending_tasks_source=lambda: 0,
        metric_prefix="testsvc",
        time_source=lambda: now,
    )
    with caplog.at_level(logging.ERROR, logger="juniper_service_core.workers.metrics"):
        families = {family.name: family for family in collector.collect()}

    assert not any("malformed snapshot" in record.message for record in caplog.records)

    ages = _sample_values(families, "testsvc_worker_heartbeat_age_seconds")
    assert ages == {"idle": 0.0, "pair": 10.0, "silent": 0.0}

    assert _sample_values(families, "testsvc_worker_gpu_utilization_pct") == {"idle": 0.0, "pair": 0.0}
    assert _sample_values(families, "testsvc_worker_last_task_duration_seconds") == {"idle": 0.0, "pair": 0.0}

    p50 = _sample_values(families, "testsvc_worker_recent_task_duration_seconds_p50")
    p95 = _sample_values(families, "testsvc_worker_recent_task_duration_seconds_p95")
    assert "idle" not in p50
    assert p50 == {"pair": 0.0}
    assert p95 == {"pair": 0.0}

    assert "testsvc_pending_tasks" in families
    assert families["testsvc_pending_tasks"].samples[0].value == 0.0
