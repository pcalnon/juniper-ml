"""Worker -> Prometheus bridge collector (WS-2 / OUT-11 T2 step 3a).

The de-cascored core of cascor's ``api/workers/metrics.py``. :class:`WorkerRegistryCollector` is a
``prometheus_client``-compatible custom collector that holds a reference to an in-process
:class:`~juniper_service_core.workers.registry.WorkerRegistry` and snapshots it on every
``collect()`` scrape, emitting per-worker gauges:

- ``<prefix>_worker_last_task_duration_seconds{worker_id}`` -- most-recent completed-task duration.
- ``<prefix>_worker_gpu_utilization_pct{worker_id}`` -- best-effort 0-100 reading.
- ``<prefix>_worker_recent_task_duration_seconds_p50{worker_id}`` / ``_p95{worker_id}`` -- percentiles
  over the registration's sliding window.
- ``<prefix>_worker_heartbeat_age_seconds{worker_id}`` -- ``now - last_heartbeat``.
- ``<prefix>_pending_tasks`` -- in-flight tasks, emitted only when a ``pending_tasks_source`` is wired.

The cascor copy hard-coded the ``juniper_cascor_worker_`` metric prefix and read the pending count off
its ``WorkerCoordinator``; this generic version takes a configurable ``metric_prefix`` (default
``juniper_service``) and an optional ``pending_tasks_source`` callable, so it needs no coordinator
import (the coordinator is step 3b). Workers that haven't reported a field (``None``) are NOT
zero-emitted -- a missing series is the correct "no data yet" semantic.

Requires ``prometheus_client`` only inside ``collect()`` (a local import), so importing this module
pulls no third-party runtime dependency -- safe on the dependency-free import path.
"""

from __future__ import annotations

import logging
import statistics
import time
from typing import TYPE_CHECKING, Callable, Iterable

if TYPE_CHECKING:
    from prometheus_client.core import Metric

    from juniper_service_core.workers.registry import WorkerRegistry

__all__ = ["WorkerRegistryCollector"]

logger = logging.getLogger("juniper_service_core.workers.metrics")


class WorkerRegistryCollector:
    """Bridge a :class:`WorkerRegistry` snapshot to Prometheus on each scrape.

    Intentionally NOT a subclass of any ``prometheus_client`` type -- the library duck-types on
    ``collect()``, so a plain class with that one method works everywhere a ``Collector`` does (and
    the unit test can instantiate it directly without registry side-effects).

    Args:
        registry: The :class:`WorkerRegistry` to snapshot. The collector keeps a reference and
            re-reads it on every scrape; it does NOT copy on construction.
        pending_tasks_source: Optional zero-arg callable returning the in-flight task count. When
            provided, the collector additionally emits ``<prefix>_pending_tasks`` on each scrape
            (cascor wires its coordinator's ``pending_tasks_count``); when ``None`` the gauge is
            silently skipped (so a missing series reads as "no data", not a misleading zero).
        metric_prefix: Prefix for every emitted metric name (default ``"juniper_service"``).
        time_source: Optional callable returning the current wall-clock time (default
            :func:`time.time`); injected for deterministic unit tests.
    """

    def __init__(
        self,
        registry: WorkerRegistry,
        *,
        pending_tasks_source: Callable[[], int] | None = None,
        metric_prefix: str = "juniper_service",
        time_source: Callable[[], float] = time.time,
    ) -> None:
        self._registry = registry
        self._pending_tasks_source = pending_tasks_source
        self._now = time_source
        self._m_last_task_duration = f"{metric_prefix}_worker_last_task_duration_seconds"
        self._m_gpu_utilization = f"{metric_prefix}_worker_gpu_utilization_pct"
        self._m_recent_p50 = f"{metric_prefix}_worker_recent_task_duration_seconds_p50"
        self._m_recent_p95 = f"{metric_prefix}_worker_recent_task_duration_seconds_p95"
        self._m_heartbeat_age = f"{metric_prefix}_worker_heartbeat_age_seconds"
        self._m_pending_tasks = f"{metric_prefix}_pending_tasks"

    def collect(self) -> Iterable[Metric]:  # noqa: D401 - prometheus_client interface
        """Snapshot the registry and emit per-worker gauge samples.

        All sample emission is best-effort -- a malformed registration is logged and skipped rather
        than failing the scrape. ``prometheus_client`` is imported locally so it stays optional at
        module import time.
        """
        from prometheus_client.core import GaugeMetricFamily

        last_task_duration = GaugeMetricFamily(self._m_last_task_duration, "Wall-clock duration of the most recently completed task on this worker.", labels=["worker_id"])
        gpu_utilization = GaugeMetricFamily(self._m_gpu_utilization, "Best-effort 0-100 GPU utilization reading on this worker.", labels=["worker_id"])
        recent_p50 = GaugeMetricFamily(self._m_recent_p50, "p50 of the worker's sliding window of recent task durations (seconds).", labels=["worker_id"])
        recent_p95 = GaugeMetricFamily(self._m_recent_p95, "p95 of the worker's sliding window of recent task durations (seconds).", labels=["worker_id"])
        heartbeat_age = GaugeMetricFamily(self._m_heartbeat_age, "Seconds since the worker's last heartbeat.", labels=["worker_id"])

        now = self._now()
        # Take a frozen snapshot of every metric-relevant field under the registry lock (the
        # snapshot returns immutable tuples so percentile computation cannot observe a partial write).
        try:
            snapshots = self._registry.snapshot_for_metrics()
        except Exception:
            logger.exception("WorkerRegistryCollector failed to snapshot registry -- emitting empty scrape")
            snapshots = []

        for snap in snapshots:
            try:
                worker_id = snap["worker_id"]
                # Always emit heartbeat age -- every registration has a populated ``last_heartbeat``.
                heartbeat_age.add_metric([worker_id], max(0.0, now - snap["last_heartbeat"]))

                # Optional fields: skip on None / empty (do NOT zero-emit).
                last_dur = snap["last_task_duration_seconds"]
                if last_dur is not None:
                    last_task_duration.add_metric([worker_id], float(last_dur))

                gpu_util = snap["gpu_utilization_pct"]
                if gpu_util is not None:
                    gpu_utilization.add_metric([worker_id], float(gpu_util))

                # ``statistics.quantiles`` requires >= 2 samples; below that any percentile is
                # degenerate, so omit rather than emit a misleading value.
                window = list(snap["recent_task_durations_seconds"] or ())
                if len(window) >= 2:
                    p50, p95 = _percentiles(window)
                    recent_p50.add_metric([worker_id], p50)
                    recent_p95.add_metric([worker_id], p95)
            except Exception:
                logger.exception("WorkerRegistryCollector skipping malformed snapshot (worker_id=%r)", snap.get("worker_id", "<unknown>") if isinstance(snap, dict) else "<unknown>")

        yield heartbeat_age
        yield last_task_duration
        yield gpu_utilization
        yield recent_p50
        yield recent_p95

        # Pending-tasks gauge: emit only when a source was wired. Missing source reads as "no data"
        # (gauge omitted) rather than zero-emit, so an "absent" alert guard keeps working in test
        # fixtures + lightweight harnesses that don't wire a coordinator.
        if self._pending_tasks_source is not None:
            pending_tasks = GaugeMetricFamily(self._m_pending_tasks, "Number of in-flight tasks tracked by the worker coordinator.")
            try:
                pending_tasks.add_metric([], float(self._pending_tasks_source()))
                yield pending_tasks
            except Exception:
                logger.exception("WorkerRegistryCollector failed to read pending_tasks_source() -- skipping gauge emission")


def _percentiles(samples: list[float]) -> tuple[float, float]:
    """Compute ``(p50, p95)`` over a list of floats.

    Uses :func:`statistics.quantiles` with ``n=20`` so the cut at index 9 is the 50th percentile and
    the cut at index 18 is the 95th. The caller MUST guarantee ``len(samples) >= 2``.
    """
    qs = statistics.quantiles(samples, n=20, method="inclusive")
    return float(qs[9]), float(qs[18])
