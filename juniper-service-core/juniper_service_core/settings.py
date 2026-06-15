"""Model-agnostic settings base for Juniper service-tier applications.

:class:`SettingsBase` carries the handful of fields every Juniper model service needs
(service name, bind host/port, log level). Concrete services subclass it and set their
own ``env_prefix`` so each service reads its own environment namespace.

Importing this module *does* require ``pydantic-settings``; the top-level
``juniper_service_core`` package keeps it out of its import path (see the package
docstring) so the dependency-free ``import juniper_service_core`` check still holds.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsBase(BaseSettings):
    """Base settings for a Juniper model service.

    Subclasses should override :attr:`model_config` to set a service-specific
    environment prefix, e.g.::

        class CascorSettings(SettingsBase):
            model_config = SettingsConfigDict(env_prefix="JUNIPER_CASCOR_")

    The default ``model_config`` here uses the generic ``JUNIPER_SERVICE_`` prefix and
    ignores unrelated environment variables (``extra="ignore"``) so a shared process
    environment does not raise on unrelated keys.
    """

    model_config = SettingsConfigDict(env_prefix="JUNIPER_SERVICE_", extra="ignore")

    service_name: str = "juniper-service"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
