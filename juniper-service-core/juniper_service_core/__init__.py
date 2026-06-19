"""``juniper-service-core`` -- shared service-tier scaffolding for Juniper ML model services.

A genuinely-shared abstraction (the ``-core`` suffix): the minimal, model-agnostic
FastAPI plumbing every Juniper model service needs -- an app factory
(:func:`create_app`), a pydantic-settings base (:class:`SettingsBase`), and a generic
liveness/readiness health router. WS-2 of the model/middleware refactor
(``notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`` in the
juniper-ml repo).

**Dependency-free top-level import.** Importing this top-level package pulls **no**
third-party runtime dependency. Only :data:`__version__` is exposed eagerly; the rest
of the public surface (``create_app``, ``SettingsBase``, the security helpers, the
secrets helper, and the middleware classes) is imported lazily on attribute access
(PEP 562 ``__getattr__``) from submodules that *do* require ``fastapi`` /
``pydantic-settings`` / ``starlette``. This is what lets the TestPyPI publish-verify
run a clean ``--no-deps`` ``import juniper_service_core`` check.

cascor's generic service infra extracted so far (de-cascored): API-key auth + rate
limiting (:mod:`~juniper_service_core.security`), Docker-secrets reading
(:mod:`~juniper_service_core.secrets`), the security / body-limit middleware
(:mod:`~juniper_service_core.middleware`), the subprocess service launcher
(:mod:`~juniper_service_core.launcher`), the **synchronous** and **threaded-orchestrator**
lifecycle bodies (:mod:`~juniper_service_core.lifecycle` -- ``TrainingLifecycle`` and
``ServiceLifecycleManager``, which drive a ``juniper-model-core`` ``TrainableModel`` through a
status FSM + a ``TrainingEvent`` monitor), and the **generic HTTP routes**
(:mod:`~juniper_service_core.routes` -- training control, metrics, dataset, and model
introspection over the injected lifecycle). The websocket / worker subsystems -- and the
worker-coordinated lifecycle body (OQ-11) -- remain deferred (later T2 follow-ups; OUT-11
steps 2-3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from juniper_service_core._version import __version__

if TYPE_CHECKING:
    # Static-analysis-only imports. ``TYPE_CHECKING`` is False at run time, so these never
    # execute -- the dependency-free top-level import is preserved and the PEP 562
    # ``__getattr__`` below does the real lazy resolution. Their purpose is to make every
    # lazily-exported name resolvable for type checkers and for CodeQL's ``py/undefined-export``
    # query, which cannot see through ``__getattr__``.
    from juniper_service_core.app import create_app
    from juniper_service_core.launcher import ManagedService, start_service, wait_for_health
    from juniper_service_core.lifecycle import (
        EventCollector,
        LifecycleCommand,
        LifecycleMonitor,
        LifecycleStateMachine,
        LifecycleStatus,
        ReplaySession,
        ServiceLifecycleManager,
        SnapshotNotFoundError,
        SnapshotStore,
        TrainingLifecycle,
    )
    from juniper_service_core.middleware import (
        RequestBodyLimitMiddleware,
        SecurityHeadersMiddleware,
        SecurityMiddleware,
    )
    from juniper_service_core.routes import (
        ResponseEnvelope,
        build_routers,
        error_response,
        get_lifecycle,
        success_response,
    )
    from juniper_service_core.secrets import get_secret
    from juniper_service_core.security import (
        APIKeyAuth,
        RateLimiter,
        api_key_header,
        build_api_key_auth,
        build_rate_limiter,
    )
    from juniper_service_core.settings import SettingsBase

__all__ = [
    "__version__",
    "create_app",
    "SettingsBase",
    # Security (lazy, from .security)
    "APIKeyAuth",
    "RateLimiter",
    "api_key_header",
    "build_api_key_auth",
    "build_rate_limiter",
    # Secrets (lazy, from .secrets)
    "get_secret",
    # Middleware (lazy, from .middleware)
    "SecurityHeadersMiddleware",
    "RequestBodyLimitMiddleware",
    "SecurityMiddleware",
    # Launcher (lazy, from .launcher -- stdlib-only)
    "ManagedService",
    "start_service",
    "wait_for_health",
    # Lifecycle (lazy, from .lifecycle -- requires juniper-model-core)
    "TrainingLifecycle",
    "EventCollector",
    "ServiceLifecycleManager",
    "LifecycleStateMachine",
    "LifecycleStatus",
    "LifecycleCommand",
    "LifecycleMonitor",
    "SnapshotStore",
    "SnapshotNotFoundError",
    "ReplaySession",
    # Generic routes (lazy, from .routes -- requires fastapi)
    "build_routers",
    "get_lifecycle",
    "success_response",
    "error_response",
    "ResponseEnvelope",
]

# Maps each lazily-resolved public name to the submodule that defines it. Keeping
# these imports out of module top level preserves the dependency-free
# ``import juniper_service_core`` guarantee: ``fastapi`` / ``pydantic-settings`` /
# ``starlette`` are only imported when one of these names is actually accessed.
# (``.secrets`` is stdlib-only, but is routed here too for uniformity.)
_LAZY_EXPORTS = {
    "create_app": "juniper_service_core.app",
    "SettingsBase": "juniper_service_core.settings",
    "APIKeyAuth": "juniper_service_core.security",
    "RateLimiter": "juniper_service_core.security",
    "api_key_header": "juniper_service_core.security",
    "build_api_key_auth": "juniper_service_core.security",
    "build_rate_limiter": "juniper_service_core.security",
    "get_secret": "juniper_service_core.secrets",
    "SecurityHeadersMiddleware": "juniper_service_core.middleware",
    "RequestBodyLimitMiddleware": "juniper_service_core.middleware",
    "SecurityMiddleware": "juniper_service_core.middleware",
    # .launcher is stdlib-only (asyncio / subprocess / urllib), but is routed
    # through the lazy path too so the PEP 562 pattern stays uniform.
    "ManagedService": "juniper_service_core.launcher",
    "start_service": "juniper_service_core.launcher",
    "wait_for_health": "juniper_service_core.launcher",
    # .lifecycle requires juniper-model-core; kept lazy so the top-level import stays
    # dependency-free and the --no-deps publish-verify still works.
    "TrainingLifecycle": "juniper_service_core.lifecycle",
    "EventCollector": "juniper_service_core.lifecycle",
    "ServiceLifecycleManager": "juniper_service_core.lifecycle",
    "LifecycleStateMachine": "juniper_service_core.lifecycle",
    "LifecycleStatus": "juniper_service_core.lifecycle",
    "LifecycleCommand": "juniper_service_core.lifecycle",
    "LifecycleMonitor": "juniper_service_core.lifecycle",
    "SnapshotStore": "juniper_service_core.lifecycle",
    "SnapshotNotFoundError": "juniper_service_core.lifecycle",
    "ReplaySession": "juniper_service_core.lifecycle",
    # .routes requires fastapi; kept lazy so the top-level import stays dependency-free.
    "build_routers": "juniper_service_core.routes",
    "get_lifecycle": "juniper_service_core.routes",
    "success_response": "juniper_service_core.routes",
    "error_response": "juniper_service_core.routes",
    "ResponseEnvelope": "juniper_service_core.routes",
}


def __getattr__(name: str):
    """Lazily resolve the third-party-dependent public surface (PEP 562).

    Keeping these imports out of module top level preserves the dependency-free
    ``import juniper_service_core`` guarantee: ``fastapi`` / ``pydantic-settings`` /
    ``starlette`` are only imported when one of the lazy exports is accessed.
    """
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        from importlib import import_module

        return getattr(import_module(module_name), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
