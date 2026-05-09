"""Health-check primitives shared across Juniper services.

Re-exports the model classes and probe utility so consumers can
``from juniper_observability.health import DependencyStatus, ReadinessResponse, probe_dependency``
without reaching into the submodules.
"""

from juniper_observability.health.models import DependencyStatus, ReadinessResponse
from juniper_observability.health.probe import probe_dependency

__all__ = ["DependencyStatus", "ReadinessResponse", "probe_dependency"]
