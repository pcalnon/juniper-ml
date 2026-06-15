"""Tests for :class:`juniper_service_core.settings.SettingsBase`."""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from juniper_service_core.settings import SettingsBase


class _CustomSettings(SettingsBase):
    """A subclass with a service-specific env prefix, mirroring real usage."""

    model_config = SettingsConfigDict(env_prefix="JUNIPER_TESTSVC_", extra="ignore")


def test_defaults():
    settings = _CustomSettings()
    assert settings.service_name == "juniper-service"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.log_level == "INFO"


def test_env_var_is_read_with_subclass_prefix(monkeypatch):
    monkeypatch.setenv("JUNIPER_TESTSVC_SERVICE_NAME", "my-cool-service")
    monkeypatch.setenv("JUNIPER_TESTSVC_PORT", "9123")
    settings = _CustomSettings()
    assert settings.service_name == "my-cool-service"
    assert settings.port == 9123


def test_unrelated_env_var_is_ignored(monkeypatch):
    # extra="ignore" means an unrelated key in the environment must not raise.
    monkeypatch.setenv("JUNIPER_TESTSVC_TOTALLY_UNRELATED", "value")
    settings = _CustomSettings()
    assert settings.service_name == "juniper-service"


def test_base_uses_generic_prefix(monkeypatch):
    monkeypatch.setenv("JUNIPER_SERVICE_HOST", "0.0.0.0")  # noqa: S104 (test-only bind value)
    settings = SettingsBase()
    assert settings.host == "0.0.0.0"  # noqa: S104 (test-only bind value)
