"""Unit tests for the WS-2 / OUT-11 T2 step-3a worker-pool foundations.

Drives the four generic pool-infra primitives -- registry, security (TLS / rate-limit / anomaly),
audit (logger + per-worker metrics), and the Prometheus collector -- with no cascade assumptions
(RK-6). The coordinator + ``/ws/workers`` stream (step 3b) and the cascade-bound task envelope
(WS-8) are out of scope here.
"""

from __future__ import annotations

import ssl

import pytest

from juniper_service_core.workers import (
    AnomalyDetector,
    AuditEventType,
    AuditLogger,
    ConnectionRateLimiter,
    TLSConfig,
    WorkerMetrics,
    WorkerRegistry,
    WorkerRegistryCollector,
    WorkerRegistryFullError,
)

# ======================================================================================
# WorkerRegistry
# ======================================================================================


def test_register_get_and_count() -> None:
    reg = WorkerRegistry()
    r = reg.register("w1", {"gpu": True}, client_name="node-a")
    assert r.worker_id == "w1"
    assert r.client_name == "node-a"
    assert reg.worker_count == 1
    assert reg.get("w1") is r
    assert reg.get("missing") is None


def test_reregister_replaces_without_growing() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    reg.register("w1", {"v": 2})  # re-registration replaces, does not grow
    assert reg.worker_count == 1
    assert reg.get("w1").capabilities == {"v": 2}


def test_capacity_rejects_new_but_allows_reregister() -> None:
    reg = WorkerRegistry(max_workers=1)
    reg.register("w1", {})
    with pytest.raises(WorkerRegistryFullError):
        reg.register("w2", {})
    # Re-registering the existing id bypasses the cap.
    reg.register("w1", {"v": 2})
    assert reg.worker_count == 1


def test_assign_and_complete_task_updates_counts() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    assert reg.assign_task("w1", "t1") is True
    assert reg.assign_task("w1", "t2") is False  # already busy
    assert reg.get("w1").idle is False
    assert reg.complete_task("w1", success=True) is True
    r = reg.get("w1")
    assert r.idle is True
    assert r.tasks_completed == 1
    assert r.health_score == 1.0


def test_idle_workers_sorted_by_health() -> None:
    reg = WorkerRegistry()
    reg.register("good", {})
    reg.register("bad", {})
    # Give "bad" a failed task so its health score drops below "good"'s neutral 1.0.
    reg.assign_task("bad", "t")
    reg.complete_task("bad", success=False)
    idle = reg.get_idle_workers()
    assert [w.worker_id for w in idle] == ["good", "bad"]


def test_heartbeat_enriched_fields_and_snapshot() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    assert reg.heartbeat("w1", gpu_utilization_pct=42.0, recent_task_durations_seconds=[1.0, 2.0, 3.0], last_task_duration_seconds=3.0) is True
    assert reg.heartbeat("missing") is False
    snap = reg.snapshot_for_metrics()
    assert len(snap) == 1
    assert snap[0]["gpu_utilization_pct"] == 42.0
    # The window is returned as an immutable tuple (mutation-safe for the collector).
    assert snap[0]["recent_task_durations_seconds"] == (1.0, 2.0, 3.0)
    assert isinstance(snap[0]["recent_task_durations_seconds"], tuple)


def test_clear_and_invalid_max_workers() -> None:
    reg = WorkerRegistry()
    reg.register("w1", {})
    reg.register("w2", {})
    assert reg.clear() == 2
    assert reg.worker_count == 0
    with pytest.raises(ValueError):
        WorkerRegistry(max_workers=0)


# ======================================================================================
# security: TLSConfig / ConnectionRateLimiter / AnomalyDetector
# ======================================================================================


def test_tls_disabled_returns_no_context() -> None:
    assert TLSConfig(enabled=False).build_ssl_context() is None


def test_tls_enabled_without_certs_builds_context_with_min_version() -> None:
    # Enabled with no cert files: a context is built (no cert chain loaded) at the requested floor.
    ctx = TLSConfig(enabled=True, min_tls_version="TLSv1.3").build_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.minimum_version == ssl.TLSVersion.TLSv1_3


def test_tls_missing_cert_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        TLSConfig(enabled=True, cert_file="/no/such/cert.pem", key_file="/no/such/key.pem").build_ssl_context()


def test_rate_limiter_allows_burst_then_blocks() -> None:
    limiter = ConnectionRateLimiter(max_connections_per_minute=60, burst_size=2)
    assert limiter.allow("ip-1") is True
    assert limiter.allow("ip-1") is True
    assert limiter.allow("ip-1") is False  # burst exhausted
    # A different source has its own bucket.
    assert limiter.allow("ip-2") is True


def test_anomaly_detector_flags_and_passes() -> None:
    det = AnomalyDetector(min_training_time=0.1)
    assert det.check_result("w1", score=0.5, training_duration=1.0, task_id="t1") == []
    fast = det.check_result("w1", score=0.5, training_duration=0.0, task_id="t2")
    assert any("suspiciously_fast" in a for a in fast)
    perfect = det.check_result("w1", score=0.9999, training_duration=1.0, task_id="t3")
    assert any("perfect_score" in a for a in perfect)
    stale = det.check_result("w1", score=0.0, training_duration=1.0, task_id="t4")
    assert any("stale_score" in a for a in stale)


def test_anomaly_detector_duplicate_scores() -> None:
    det = AnomalyDetector()
    flagged = []
    for i in range(3):
        flagged = det.check_result("w1", score=0.42, training_duration=1.0, task_id=f"t{i}")
    assert any("duplicate_scores" in a for a in flagged)
    stats = det.get_worker_stats("w1")
    assert stats["total_results"] == 3
    assert stats["max_score"] == 0.42


# ======================================================================================
# audit: AuditLogger / WorkerMetrics
# ======================================================================================


def test_audit_logger_counts_and_reset() -> None:
    audit = AuditLogger()
    audit.log(AuditEventType.AUTH_SUCCESS, worker_id="w1")
    audit.log(AuditEventType.AUTH_SUCCESS, worker_id="w2")
    audit.log(AuditEventType.AUTH_FAILURE, worker_id="w3")
    counts = audit.get_counts()
    assert counts[AuditEventType.AUTH_SUCCESS] == 2
    assert counts[AuditEventType.AUTH_FAILURE] == 1
    audit.reset_counts()
    assert audit.get_counts() == {}


def test_worker_metrics_lifecycle() -> None:
    wm = WorkerMetrics()
    wm.on_register("w1", source_ip="10.0.0.1")
    wm.on_task_complete("w1", success=True, duration=2.0)
    wm.on_task_complete("w1", success=False, duration=4.0)
    wm.on_anomaly("w1", "perfect_score")
    m = wm.get_worker_metrics("w1")
    assert m["tasks_completed"] == 2
    assert m["tasks_succeeded"] == 1
    assert m["tasks_failed"] == 1
    assert m["avg_duration"] == 3.0
    assert m["success_rate"] == 0.5
    assert m["anomaly_count"] == 1
    assert wm.get_worker_metrics("missing") is None
    assert len(wm.get_all_metrics()) == 1


# ======================================================================================
# metrics: WorkerRegistryCollector
# ======================================================================================


def test_collector_emits_per_worker_gauges() -> None:
    pytest.importorskip("prometheus_client")
    reg = WorkerRegistry()
    reg.register("w1", {})
    reg.heartbeat("w1", gpu_utilization_pct=55.0, last_task_duration_seconds=2.5, recent_task_durations_seconds=[1.0, 2.0, 3.0, 4.0])
    reg.register("w2", {})  # only heartbeat-age, no optional fields

    collector = WorkerRegistryCollector(reg, pending_tasks_source=lambda: 7, metric_prefix="testsvc", time_source=lambda: 1_000_000.0)
    families = {fam.name: fam for fam in collector.collect()}

    # Heartbeat age is always emitted (one sample per worker).
    assert "testsvc_worker_heartbeat_age_seconds" in families
    assert len(families["testsvc_worker_heartbeat_age_seconds"].samples) == 2
    # GPU + last-task-duration only for w1 (w2 reported neither -> not zero-emitted).
    assert len(families["testsvc_worker_gpu_utilization_pct"].samples) == 1
    assert len(families["testsvc_worker_last_task_duration_seconds"].samples) == 1
    # Percentiles for w1's 4-sample window.
    assert len(families["testsvc_worker_recent_task_duration_seconds_p50"].samples) == 1
    # Pending-tasks gauge emitted because a source was wired.
    assert "testsvc_pending_tasks" in families
    assert families["testsvc_pending_tasks"].samples[0].value == 7.0


def test_collector_skips_pending_without_source() -> None:
    pytest.importorskip("prometheus_client")
    reg = WorkerRegistry()
    reg.register("w1", {})
    collector = WorkerRegistryCollector(reg, metric_prefix="testsvc")
    families = {fam.name: fam for fam in collector.collect()}
    # No pending_tasks_source wired -> the gauge is omitted (reads as "no data", not zero).
    assert "testsvc_pending_tasks" not in families
    assert "testsvc_worker_heartbeat_age_seconds" in families
