"""Worker-pool subsystem (WS-2 / OUT-11 T2 step 3a -- pool-infra foundations).

The model-agnostic worker-pool primitives extracted from cascor's ``api/workers/`` (the GENERIC
pool-infra layer the OQ-11 audit cleared, design §5.6):

- :class:`~juniper_service_core.workers.registry.WorkerRegistry` -- thread-safe registration,
  heartbeat tracking, health scoring, and idle/stale queries.
- :class:`~juniper_service_core.workers.security.TLSConfig` /
  :class:`~juniper_service_core.workers.security.ConnectionRateLimiter` /
  :class:`~juniper_service_core.workers.security.AnomalyDetector` -- mTLS, per-source connection
  rate limiting, and result-anomaly detection over a generic quality score.
- :class:`~juniper_service_core.workers.audit.AuditLogger` /
  :class:`~juniper_service_core.workers.audit.WorkerMetrics` -- structured AUDIT-level event
  logging and per-worker counters.
- :class:`~juniper_service_core.workers.metrics.WorkerRegistryCollector` -- a ``prometheus_client``
  custom collector bridging registry snapshots to per-worker gauges.

**Deferred (step 3b):** the ``WorkerCoordinator`` (task dispatch/collect over an injectable
task-protocol seam) and the ``/ws/workers`` stream handler. **Deferred (WS-8):** the cascade-bound
``Task`` / ``TaskResult`` envelope (cascor's ``api/workers/protocol.py`` -- ``candidate_data`` /
``correlation`` / ...) and the correlation-based result reduction, which stay cascor-side.

These primitives are pure stdlib (``prometheus_client`` is imported lazily inside the collector's
``collect()``), so this subpackage adds no third-party runtime dependency; the
:mod:`juniper_service_core` top-level package still keeps every name here off the eager import path
(PEP 562 lazy export) for uniformity with the other T2 subsystems.
"""

from __future__ import annotations

from juniper_service_core.workers.audit import AUDIT_LEVEL, AuditEventType, AuditLogger, WorkerMetrics
from juniper_service_core.workers.metrics import WorkerRegistryCollector
from juniper_service_core.workers.registry import DEFAULT_MAX_WORKERS, WorkerRegistration, WorkerRegistry, WorkerRegistryFullError
from juniper_service_core.workers.security import AnomalyDetector, ConnectionRateLimiter, TLSConfig

__all__ = [
    # Registry
    "WorkerRegistry",
    "WorkerRegistration",
    "WorkerRegistryFullError",
    "DEFAULT_MAX_WORKERS",
    # Security
    "TLSConfig",
    "ConnectionRateLimiter",
    "AnomalyDetector",
    # Audit
    "AuditLogger",
    "WorkerMetrics",
    "AuditEventType",
    "AUDIT_LEVEL",
    # Metrics
    "WorkerRegistryCollector",
]
