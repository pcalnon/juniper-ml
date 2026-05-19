"""Shared pytest fixtures for the juniper-doc-tools test suite."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def make_repo(tmp_path: Path):
    """Factory: create a fake repo subdirectory with a given layout.

    Returns a callable that takes a repo name (default ``repo``) and
    returns its Path. Useful when a test wants to set up an ecosystem
    layout (parent dir + multiple sibling "repos").
    """

    def _make(name: str = "repo") -> Path:
        repo = tmp_path / name
        repo.mkdir(parents=True, exist_ok=True)
        return repo

    return _make
