"""Cross-service observability contract constants.

These constants pin down the wire format established by METRICS-MON
R1.1, R1.2, and R1.3 across juniper-data, juniper-cascor, and
juniper-canopy. Pulling them into a single module ensures that any
future contract change happens in one place and ripples to every
consumer at version-bump time.

References:
- juniper-ml notes/legacy/METRICS_MONITORING_R1.1_*: cardinality (archived 2026-05-05)
- juniper-ml notes/legacy/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md (archived 2026-05-05)
- juniper-ml notes/legacy/METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md (archived 2026-05-05)
"""

from typing import Final

# METRICS-MON R1.1 / seed-01: when a request does not match any
# registered Starlette route template, the Prometheus middleware emits
# this single bucket value for the ``endpoint`` label and increments a
# separate ``http_unmatched_requests_total{method}`` counter so the
# label cardinality stays bounded under attacker-controlled paths.
UNMATCHED_ENDPOINT_LABEL: Final[str] = "_unmatched"

# METRICS-MON R1.2 / seed-02: response header that mirrors the readiness
# body status. Lets ``kubectl describe pod`` and ``curl -I`` surface the
# state without parsing JSON.
READINESS_HEADER: Final[str] = "X-Juniper-Readiness"

# METRICS-MON R1.2 / seed-03: liveness tick must complete within this
# wall-clock budget (milliseconds). Helm ``timeoutSeconds`` (5–10s)
# wraps this with headroom; the budget catches event-loop stalls and
# CPU starvation that the previous no-op probe could not.
LIVENESS_TICK_BUDGET_MS: Final[int] = 250

# METRICS-MON R1.2 / seed-03: heartbeat staleness threshold for
# services that bump a per-second liveness counter (e.g.,
# juniper-cascor's lifecycle manager). A staleness > 30s reliably
# indicates a wedged process.
LIVENESS_STALENESS_SECONDS: Final[float] = 30.0

# Standard request-id header propagated through ``RequestIdMiddleware``.
HEADER_X_REQUEST_ID: Final[str] = "X-Request-ID"
