"""Shared pytest fixtures for juniper_ci_tools tests."""

from __future__ import annotations

import datetime as dt
import textwrap
from pathlib import Path
from typing import Callable

import shutil
import sys

import pytest

# Resolve the submodule via sys.modules. We cannot use the attribute path
# `juniper_ci_tools.generate_dep_docs` because the package's `__init__.py`
# re-exports a function of the same name, which shadows the submodule on
# attribute access. The module object itself is still in sys.modules.
import juniper_ci_tools.generate_dep_docs as _import_to_register  # noqa: F401,E402
_gdd = sys.modules["juniper_ci_tools.generate_dep_docs"]


PYPROJECT = textwrap.dedent(
    """\
    [project]
    name = "test-repo"
    version = "1.2.3"
    """
)

PIP_HEADER = textwrap.dedent(
    """\
    # PIP Header
    # Version: <X.Y.Z  Major, Minor, Point Version for Repo>
    # Last Modified: <YYYY-MM-dd for Current date>
    # Year: <YYYY for Current Year>
    # Python: <Python Version>
    # Pip: <Pip Version>
    """
)

CONDA_HEADER = textwrap.dedent(
    """\
    # Conda Header
    # Version: <X.Y.Z  Major, Minor, Point Version for test-repo>
    # Last Modified: <YYYY-MM-dd for current date>
    # Year: <YYYY for current year>
    # Conda Date: <YYYY.MM.dd for current date>
    # Python: <Python Version>
    name: test-env
    channels:
      - conda-forge
    dependencies:
    """
)


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """A minimal Juniper-shaped repo with pyproject + header templates."""

    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "PIP_DEPENDENCY_FILE_HEADER.md").write_text(PIP_HEADER, encoding="utf-8")
    (tmp_path / "notes" / "CONDA_DEPENDENCY_FILE_HEADER.md").write_text(CONDA_HEADER, encoding="utf-8")
    return tmp_path


@pytest.fixture
def fixed_now() -> dt.datetime:
    """A deterministic datetime to make timestamp strings predictable."""

    return dt.datetime(2026, 5, 20, 14, 30, 45)


@pytest.fixture
def fake_conda(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Install a stub for the conda subprocess call.

    Returns a setter that, when called with a conda-env-export payload string,
    arranges for :func:`juniper_ci_tools.generate_dep_docs._conda_env_export`
    to return that payload and for :func:`shutil.which` to report ``conda``
    as installed at ``/usr/bin/conda`` (a stable fake path).
    """

    state: dict[str, str] = {"payload": ""}

    def _set(payload: str) -> None:
        state["payload"] = payload

    def fake_which(cmd: str) -> str | None:
        if cmd == "conda":
            return "/usr/bin/conda"
        return None

    def fake_conda_export(conda_cmd: str) -> str:  # noqa: ARG001
        return state["payload"]

    monkeypatch.setattr(_gdd.shutil, "which", fake_which)
    monkeypatch.setattr(_gdd, "_conda_env_export", fake_conda_export)
    return _set


@pytest.fixture
def fake_pip(monkeypatch: pytest.MonkeyPatch) -> Callable[[str, str], None]:
    """Stub the pip subprocess calls so tests do not depend on host pip output."""

    state: dict[str, str] = {"freeze": "pkg-a==1.0\npkg-b==2.0\n", "version": "24.0"}

    def _set(freeze: str, version: str) -> None:
        state["freeze"] = freeze
        state["version"] = version

    def fake_pip_list_freeze() -> str:
        return state["freeze"]

    def fake_pip_version() -> str:
        return state["version"]

    monkeypatch.setattr(_gdd, "_pip_list_freeze", fake_pip_list_freeze)
    monkeypatch.setattr(_gdd, "_detect_pip_version", fake_pip_version)
    return _set


@pytest.fixture
def no_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force :func:`shutil.which` to report that conda is not on PATH."""

    monkeypatch.setattr(shutil, "which", lambda cmd: None)
