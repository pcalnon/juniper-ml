"""Tests for the E-8 boot-time dependency-floor self-check (``dependency_floors``).

Covers the pure checker, the three floor resolvers (explicit / installed Requires-Dist
metadata / source pyproject), the numeric-aware version compare, the fail-loud enforcer,
and the escape-hatch env var. ``metadata.version`` / ``metadata.requires`` are monkeypatched
so the suite is hermetic (no reliance on what happens to be installed).
"""

from __future__ import annotations

import logging
import textwrap
from importlib import metadata

import pytest

from juniper_service_core import dependency_floors as df
from juniper_service_core.dependency_floors import (
    DependencyFloorError,
    FloorViolation,
    check_dependency_floors,
    enforce_dependency_floors,
    floors_from_distribution,
    floors_from_pyproject,
    floors_from_requirements,
)


# --------------------------------------------------------------------------- version compare
def test_vtuple_is_numeric_not_lexical():
    assert df._vtuple("0.10.0") == (0, 10, 0)
    assert df._vtuple("1.2.3-rc1") == (1, 2, 3)
    assert df._vtuple("bogus") == (0,)


def test_below_numeric_ordering():
    assert df._below("0.9.0", "0.10.0") is True  # 0.9 < 0.10, not lexical
    assert df._below("0.10.0", "0.9.0") is False
    assert df._below("1.2.3", "1.2.3") is False


# --------------------------------------------------------------------------- requirement parsing
def test_floors_from_requirements_juniper_only_and_markers_skipped():
    reqs = [
        "juniper-observability>=0.4.0",
        "juniper-model-core (>=0.1.0)",  # older parenthesised form
        "fastapi>=0.110",  # non-juniper -> skipped
        "juniper-data-client>=0.4.1,<0.5.0",  # upper bound ignored, floor kept
        "pytest>=8.0; extra == 'dev'",  # environment marker -> skipped
        "juniper-foo>=1.0; python_version < '3.11'",  # marker -> skipped
        "juniper-nofloor",  # no >= -> skipped
    ]
    assert floors_from_requirements(reqs) == {
        "juniper-observability": "0.4.0",
        "juniper-model-core": "0.1.0",
        "juniper-data-client": "0.4.1",
    }


def test_floors_from_requirements_custom_prefix_and_empty():
    assert floors_from_requirements(["acme-x>=1.0", "juniper-y>=2.0"], prefix="acme-") == {"acme-x": "1.0"}
    assert floors_from_requirements([]) == {}
    assert floors_from_requirements(None) == {}


# --------------------------------------------------------------------------- pure checker
def test_check_satisfied(monkeypatch):
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.5.0")
    assert check_dependency_floors({"juniper-x": "0.4.0"}) == []


def test_check_below_floor(monkeypatch):
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.3.0")
    assert check_dependency_floors({"juniper-x": "0.4.0"}) == [FloorViolation("juniper-x", "0.4.0", "0.3.0")]


def test_check_missing_distribution(monkeypatch):
    def _missing(dist):
        raise metadata.PackageNotFoundError(dist)

    monkeypatch.setattr(df.metadata, "version", _missing)
    assert check_dependency_floors({"juniper-x": "0.4.0"}) == [FloorViolation("juniper-x", "0.4.0", None)]


# --------------------------------------------------------------------------- resolvers
def test_floors_from_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent(
            """
            [project]
            name = "demo"
            dependencies = ["juniper-observability>=0.4.0", "fastapi>=0.110"]
            """
        ),
        encoding="utf-8",
    )
    assert floors_from_pyproject(pyproject) == {"juniper-observability": "0.4.0"}


def test_floors_from_distribution_reads_requires(monkeypatch):
    monkeypatch.setattr(df.metadata, "requires", lambda dist: ["juniper-x>=1.0", "click>=8"])
    assert floors_from_distribution("demo") == {"juniper-x": "1.0"}


def test_floors_from_distribution_no_requires(monkeypatch):
    monkeypatch.setattr(df.metadata, "requires", lambda dist: None)
    assert floors_from_distribution("demo") == {}


# --------------------------------------------------------------------------- enforcer
def test_enforce_raises_naming_dep_floor_installed(monkeypatch):
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.3.0")
    with pytest.raises(DependencyFloorError) as exc:
        enforce_dependency_floors({"juniper-x": "0.4.0"})
    message = str(exc.value)
    assert "juniper-x" in message and "0.4.0" in message and "0.3.0" in message


def test_enforce_passes_when_satisfied(monkeypatch):
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.5.0")
    enforce_dependency_floors({"juniper-x": "0.4.0"})  # must not raise


def test_enforce_missing_distribution_message(monkeypatch):
    def _missing(dist):
        raise metadata.PackageNotFoundError(dist)

    monkeypatch.setattr(df.metadata, "version", _missing)
    with pytest.raises(DependencyFloorError) as exc:
        enforce_dependency_floors({"juniper-x": "0.4.0"})
    assert "NOT INSTALLED" in str(exc.value)


def test_enforce_escape_hatch_skips(monkeypatch, caplog):
    monkeypatch.setenv(df.DEFAULT_SKIP_ENV_VAR, "1")
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.0.1")  # would violate
    with caplog.at_level(logging.WARNING):
        enforce_dependency_floors({"juniper-x": "9.9.9"})  # bypassed -> no raise
    assert any("SKIPPED" in record.message for record in caplog.records)


def test_enforce_escape_hatch_falsey_still_checks(monkeypatch):
    monkeypatch.setenv(df.DEFAULT_SKIP_ENV_VAR, "0")  # falsey -> the check still runs
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.3.0")
    with pytest.raises(DependencyFloorError):
        enforce_dependency_floors({"juniper-x": "0.4.0"})


def test_enforce_requires_a_source():
    with pytest.raises(ValueError):
        enforce_dependency_floors()


def test_enforce_empty_floors_is_noop():
    enforce_dependency_floors({})  # nothing to enforce -> returns cleanly


def test_enforce_via_distribution_path(monkeypatch):
    monkeypatch.setattr(df.metadata, "requires", lambda dist: ["juniper-x>=0.4.0"])
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.5.0")
    enforce_dependency_floors(distribution="demo")  # satisfied -> no raise


def test_enforce_via_pyproject_path(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "d"\ndependencies = ["juniper-x>=0.4.0"]\n', encoding="utf-8")
    monkeypatch.setattr(df.metadata, "version", lambda dist: "0.3.0")
    with pytest.raises(DependencyFloorError):
        enforce_dependency_floors(pyproject_path=pyproject)


def test_public_api_is_importable_from_top_level():
    """The two primary names resolve through the package's lazy PEP 562 surface."""
    import juniper_service_core as jsc

    assert jsc.enforce_dependency_floors is enforce_dependency_floors
    assert issubclass(jsc.DependencyFloorError, RuntimeError)
