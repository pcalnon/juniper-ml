"""Training-lifecycle subsystem (WS-2 / OUT-11 T2).

The model-agnostic lifecycle machinery for a Juniper model service, all operating against the
:mod:`juniper_model_core` contracts (``TrainableModel`` / ``GrowableModel`` /
``TrainingEvent``) so a single base drives every model:

* :class:`~juniper_service_core.lifecycle.sync.TrainingLifecycle` -- the synchronous body
  (drives ``model.fit`` on the calling thread).
* :class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager` -- the
  background-threaded orchestrator (state machine + monitor + cooperative pause/stop) that
  the generic HTTP routes query. The substantive WS-2 body model-core's
  ``TrainingLifecycleBase`` deferred.
* :class:`~juniper_service_core.lifecycle.state_machine.LifecycleStateMachine` -- the
  deterministic status FSM (``STOPPED → STARTED → {PAUSED, COMPLETED, FAILED}``).
* :class:`~juniper_service_core.lifecycle.monitor.LifecycleMonitor` -- the thread-safe
  ``TrainingEvent`` accumulator + bounded metric history.

This subpackage requires ``juniper-model-core`` but **not** ``fastapi``; the
:mod:`juniper_service_core` top-level package keeps every name here off the eager import path
(PEP 562 lazy export) so ``import juniper_service_core`` stays dependency-free.
"""

from __future__ import annotations

from juniper_service_core.lifecycle.manager import ServiceLifecycleManager, TrainingInterrupted
from juniper_service_core.lifecycle.monitor import LifecycleMonitor
from juniper_service_core.lifecycle.state_machine import (
    LifecycleCommand,
    LifecycleStateMachine,
    LifecycleStatus,
)
from juniper_service_core.lifecycle.sync import EventCollector, TrainingLifecycle

__all__ = [
    "TrainingLifecycle",
    "EventCollector",
    "ServiceLifecycleManager",
    "TrainingInterrupted",
    "LifecycleStateMachine",
    "LifecycleStatus",
    "LifecycleCommand",
    "LifecycleMonitor",
]
