"""Tests for the SEC-F01 boot-time auth-posture self-check (``auth_posture``).

Covers the pure key filter, the three posture outcomes (secured / open-warning /
fail-closed-raise), the empty-and-blank-key edge (an empty secret file is not real auth),
and the escape-hatch env var. Hermetic — no network, no real service.
"""

from __future__ import annotations

import logging

import pytest

from juniper_service_core.auth_posture import (
    AuthPostureError,
    auth_is_configured,
    enforce_auth_posture,
    real_keys,
)

_LOGGER = "juniper_service_core.auth_posture"


# --------------------------------------------------------------------------- pure core
def test_real_keys_filters_blank_and_none():
    assert real_keys(None) == []
    assert real_keys([]) == []
    assert real_keys(["", "  ", "\n"]) == []  # an empty secret file resolves to blanks only
    assert real_keys(["k1", "", "k2"]) == ["k1", "k2"]
    assert real_keys(["live-key"]) == ["live-key"]


def test_auth_is_configured():
    assert auth_is_configured(["k"]) is True
    assert auth_is_configured([]) is False
    assert auth_is_configured([""]) is False  # blank-only == not configured
    assert auth_is_configured(None) is False


# --------------------------------------------------------------------------- secured (INFO, no raise)
def test_configured_keys_pass_and_log_info(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        enforce_auth_posture(["real-key"], require_auth=True, service_name="cascor")
    assert any("Auth posture OK" in r.message for r in caplog.records)


# --------------------------------------------------------------------------- fail closed (raise)
def test_require_auth_with_no_keys_raises():
    with pytest.raises(AuthPostureError) as exc:
        enforce_auth_posture([], require_auth=True, service_name="cascor")
    assert "requires API-key authentication" in str(exc.value)


def test_require_auth_with_blank_only_keys_raises():
    # An empty/placeholder secret file resolves to blank(s) -> still fail closed.
    with pytest.raises(AuthPostureError):
        enforce_auth_posture(["   "], require_auth=True, service_name="data")


def test_require_auth_logs_critical(caplog):
    with caplog.at_level(logging.CRITICAL, logger=_LOGGER):
        with pytest.raises(AuthPostureError):
            enforce_auth_posture(None, require_auth=True, service_name="canopy")
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)


# --------------------------------------------------------------------------- open (WARNING, no raise)
def test_no_keys_without_require_warns_not_raises(caplog):
    with caplog.at_level(logging.WARNING, logger=_LOGGER):
        enforce_auth_posture([], require_auth=False, service_name="canopy-demo")  # must not raise
    assert any("running OPEN" in r.message for r in caplog.records)


# --------------------------------------------------------------------------- escape hatch
def test_skip_env_var_bypasses_even_when_required(monkeypatch, caplog):
    monkeypatch.setenv("JUNIPER_SKIP_AUTH_POSTURE_CHECK", "1")
    with caplog.at_level(logging.WARNING, logger=_LOGGER):
        enforce_auth_posture([], require_auth=True, service_name="cascor")  # would raise, but bypassed
    assert any("SKIPPED" in r.message for r in caplog.records)


def test_custom_skip_env_var(monkeypatch):
    monkeypatch.setenv("MY_SKIP", "yes")
    # require_auth + no keys would raise, but the custom skip var bypasses it
    enforce_auth_posture([], require_auth=True, skip_env_var="MY_SKIP")


def test_skip_env_var_falsey_does_not_bypass(monkeypatch):
    monkeypatch.setenv("JUNIPER_SKIP_AUTH_POSTURE_CHECK", "0")
    with pytest.raises(AuthPostureError):
        enforce_auth_posture([], require_auth=True)
