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

The first slice of cascor's generic service infra is now extracted (de-cascored):
API-key auth + rate limiting (:mod:`~juniper_service_core.security`), Docker-secrets
reading (:mod:`~juniper_service_core.secrets`), and the security / body-limit
middleware (:mod:`~juniper_service_core.middleware`). The websocket / worker /
generic-route helpers and the ``TrainingLifecycleBase`` body remain deferred until
``juniper-model-core`` is wired in (later WS-2 follow-ups).
"""

from __future__ import annotations

from juniper_service_core._version import __version__

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
