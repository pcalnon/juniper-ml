"""Shared pytest fixtures for juniper_config_tools tests.

The helper reads :data:`os.environ` directly, so every test that
touches env state needs isolation. ``clean_env`` deletes a curated
list of test-only env-var names before yielding so the four states
(canonical alone / legacy alone / both / neither) can be set
deterministically.
"""

from __future__ import annotations

import pytest

_TEST_ENV_NAMES: tuple[str, ...] = (
    "JCT_TEST_NEW",
    "JCT_TEST_LEGACY",
    "JCT_TEST_OTHER_NEW",
    "JCT_TEST_OTHER_LEGACY",
)


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Delete all juniper-config-tools test env vars before the test runs."""
    for name in _TEST_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch
