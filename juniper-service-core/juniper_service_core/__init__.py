"""``juniper-service-core`` -- shared service-tier scaffolding for Juniper ML model services.

A genuinely-shared abstraction (the ``-core`` suffix): the minimal, model-agnostic
FastAPI plumbing every Juniper model service needs -- an app factory
(:func:`create_app`), a pydantic-settings base (:class:`SettingsBase`), and a generic
liveness/readiness health router. WS-2 of the model/middleware refactor
(``notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`` in the
juniper-ml repo).

**Dependency-free top-level import.** Importing this top-level package pulls **no**
third-party runtime dependency. Only :data:`__version__` is exposed eagerly;
``create_app`` and ``SettingsBase`` are imported lazily on attribute access (PEP 562
``__getattr__``) from their submodules, which *do* require ``fastapi`` /
``pydantic-settings``. This is what lets the TestPyPI publish-verify run a clean
``--no-deps`` ``import juniper_service_core`` check.

This first scaffold is intentionally minimal and additive: it does **not** yet extract
the security / middleware / websocket / worker / generic-route helpers from
``juniper-cascor``, and the ``TrainingLifecycleBase`` body is deferred until
``juniper-model-core`` is wired in (a later WS-2 follow-up).
"""

from __future__ import annotations

from juniper_service_core._version import __version__

__all__ = [
    "__version__",
    "create_app",
    "SettingsBase",
]


def __getattr__(name: str):
    """Lazily resolve the third-party-dependent public surface (PEP 562).

    Keeping these imports out of module top level preserves the dependency-free
    ``import juniper_service_core`` guarantee: ``fastapi`` / ``pydantic-settings``
    are only imported when ``create_app`` / ``SettingsBase`` are actually accessed.
    """
    if name == "create_app":
        from juniper_service_core.app import create_app

        return create_app
    if name == "SettingsBase":
        from juniper_service_core.settings import SettingsBase

        return SettingsBase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
