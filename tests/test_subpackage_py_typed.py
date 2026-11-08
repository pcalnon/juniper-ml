#!/usr/bin/env python3
"""Structural gate: every published sub-package ships a PEP 561 ``py.typed`` marker.

Closes ``APD-SVCCORE-008`` and ``APD-OBS-002`` in the ecosystem defect register,
and the four unrecorded siblings the register never filed -- all six in-repo
sub-packages were affected, not the two on the books.

Without the marker a consumer's type checker refuses to read the package at all::

    error: Skipping analyzing "juniper_service_core.auth_posture": module is
    installed, but missing library stubs or py.typed marker  [import-untyped]

Every annotation is then discarded and every symbol degrades to ``Any``, so a
consumer calling ``enforce_auth_posture(keys, require_auth="yes")`` -- a ``str``
where a ``bool`` is declared -- type-checks clean. The annotations exist
(service-core alone carries 310+ annotated defs plus a 75-line ``TYPE_CHECKING``
block); nothing was reading them.

**The source checks pin two things: the marker file, and its declaration.**
The file is what a wheel cannot do without. The declaration is not what ships
it today: ``build_py`` also packages a ``py.typed`` it finds undeclared
(``_IMPLICIT_DATA_FILES = ('*.pyi', 'py.typed')`` in setuptools 81.0.0 and in
84.2.1, the latest release, which CI's ``setuptools>=68`` resolves to), and a
``juniper-config-tools`` wheel built with the entry emptied still carries the
marker (built in a temporary copy, 2026-11-07). The
declaration is pinned so the packaging states the marker explicitly instead of
resting on that implicit pattern.

The declaration is still not the wheel. At the ``juniper-config-tools-v0.1.0``
tag the package directory held ``__init__.py``, ``__main__.py``,
``_env_aliases.py`` and ``_version.py`` and no ``py.typed``, so the 0.1.0
wheel could not carry one, and a type checker treats such a package as
untyped. ``test_every_built_wheel_ships_py_typed`` builds each wheel and
requires ``<import>/py.typed`` plus the ``Typing :: Typed`` classifier, so a
marker missing from the tree, or a package the build no longer packages,
fails here even while the declaration is intact. There is no omission
control, for the reason above: a wheel built undeclared still ships the marker.

``test_package_data_does_not_swallow_packages_find_keys`` guards a regression
observed while authoring this change: ``[tool.setuptools.package-data]`` was
inserted between ``packages.find``'s ``include`` and ``exclude`` keys, silently
re-homing ``exclude = ["tests*"]`` into the new table and packaging
``juniper-model-core``'s test suite into its wheel. Both tables stay valid TOML,
so nothing failed -- only reading the parsed result showed it.

Run: python3 -m unittest -v tests/test_subpackage_py_typed.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-21
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 -- sys.executable plus a fixed argv, never a shell
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from typing import Any

# The six published in-repo sub-packages. Discovery below is by glob so a
# seventh is covered automatically; this set exists purely to prove the glob
# found something real -- an empty discovery would pass every other test here
# vacuously.
EXPECTED_SUBPACKAGES: frozenset[str] = frozenset(
    {
        "juniper-ci-tools",
        "juniper-config-tools",
        "juniper-doc-tools",
        "juniper-model-core",
        "juniper-observability",
        "juniper-service-core",
    }
)

TYPED_CLASSIFIER = "Typing :: Typed"

# Keys that belong to [tool.setuptools.packages.find]; finding one inside
# [tool.setuptools.package-data] means a table header was inserted mid-table.
PACKAGES_FIND_KEYS: frozenset[str] = frozenset({"include", "exclude", "where", "namespaces"})

# Isolated from the parent interpreter: setuptools keeps build state on the process, and a second
# package built in-process can reuse the first package's discovered files. stdout/stderr stay in the
# parent capture so the build log does not flood the regression step.
_BUILD_WHEEL = r"""
import contextlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path

import setuptools.build_meta as build_meta

project, wheel_dir, out = (Path(arg) for arg in sys.argv[1:4])
os.chdir(project)
sink = io.StringIO()
with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
    wheel_name = build_meta.build_wheel(str(wheel_dir))
with zipfile.ZipFile(wheel_dir / wheel_name) as archive:
    names = archive.namelist()
    metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
    metadata = archive.read(metadata_name).decode("utf-8")
Path(out).write_text(json.dumps({"names": names, "metadata": metadata, "log": sink.getvalue()}), encoding="utf-8")
"""


def _built_wheel(project: Path) -> tuple[list[str], str]:
    """Build ``project`` in a temp copy and return ``(wheel member names, METADATA text)``."""
    with tempfile.TemporaryDirectory(prefix=f"py-typed-wheel-{project.name}-") as tmp:
        root = Path(tmp)
        copy = root / "project"
        shutil.copytree(project, copy, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__", ".pytest_cache", ".mypy_cache"))
        wheel_dir = root / "dist"
        wheel_dir.mkdir()
        out = root / "wheel.json"
        proc = subprocess.run(  # nosec B603 -- sys.executable and a fixed argv, no shell
            [sys.executable, "-c", _BUILD_WHEEL, str(copy), str(wheel_dir), str(out)],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            if "No module named 'setuptools'" in detail or "No module named setuptools" in detail:
                raise AssertionError("setuptools is required to build the wheel (the Regression Tests job installs setuptools>=68): " + detail[-500:]) from None
            raise AssertionError(f"{project.name}: wheel build failed (exit {proc.returncode}): {detail[-800:]}")
        payload = json.loads(out.read_text(encoding="utf-8"))
        return list(payload["names"]), str(payload["metadata"])


def _tests_packaged(names: list[str]) -> list[str]:
    """Wheel members that are a ``tests`` package. The mid-table header bug shipped one."""
    return [name for name in names if name == "tests" or name.startswith("tests/") or "/tests/" in name]


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _import_name(subdir: Path) -> str:
    """``juniper-service-core`` -> ``juniper_service_core``."""
    return subdir.name.replace("-", "_")


class PyTypedMarkerTests(unittest.TestCase):
    """Each sub-package must both contain and publish its ``py.typed`` marker."""

    repo_root: Path
    subdirs: list[Path]
    parsed: dict[str, dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.subdirs = sorted(p.parent for p in cls.repo_root.glob("juniper-*/pyproject.toml"))
        cls.parsed = {d.name: tomllib.loads((d / "pyproject.toml").read_text(encoding="utf-8")) for d in cls.subdirs}

    def test_discovery_is_not_vacuous(self) -> None:
        """Anti-vacuous guard: every other test here loops over this set."""
        found = {d.name for d in self.subdirs}
        self.assertTrue(found, "no juniper-*/pyproject.toml found -- every other assertion here would pass vacuously")
        missing = EXPECTED_SUBPACKAGES - found
        self.assertFalse(missing, f"known sub-packages not discovered: {sorted(missing)}")

    def test_every_subpackage_ships_a_py_typed_marker(self) -> None:
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                marker = subdir / _import_name(subdir) / "py.typed"
                self.assertTrue(
                    marker.is_file(),
                    f"{subdir.name}: missing PEP 561 marker at {marker.relative_to(self.repo_root)} -- " "consumers will see [import-untyped] and discard every annotation",
                )

    def test_every_subpackage_declares_py_typed_as_package_data(self) -> None:
        """Declared explicitly, so packaging does not rest on setuptools' implicit pattern (81.0.0 and 84.2.1 ship an undeclared marker too)."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                pkg = _import_name(subdir)
                package_data = self.parsed[subdir.name].get("tool", {}).get("setuptools", {}).get("package-data", {})
                self.assertIn(
                    pkg,
                    package_data,
                    f"{subdir.name}: [tool.setuptools.package-data] does not declare '{pkg}' -- " "the marker would reach the wheel only through setuptools' implicit py.typed pattern, not a declaration",
                )
                self.assertIn(
                    "py.typed",
                    package_data[pkg],
                    f"{subdir.name}: '{pkg}' package-data does not list py.typed",
                )

    def test_every_subpackage_declares_the_typed_classifier(self) -> None:
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                classifiers = self.parsed[subdir.name].get("project", {}).get("classifiers", [])
                self.assertIn(
                    TYPED_CLASSIFIER,
                    classifiers,
                    f"{subdir.name}: missing the '{TYPED_CLASSIFIER}' classifier",
                )

    def test_package_data_does_not_swallow_packages_find_keys(self) -> None:
        """A table header inserted mid-table silently re-homes the keys below it."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                setuptools_cfg = self.parsed[subdir.name].get("tool", {}).get("setuptools", {})
                package_data = setuptools_cfg.get("package-data", {})
                strays = PACKAGES_FIND_KEYS & set(package_data)
                self.assertFalse(
                    strays,
                    f"{subdir.name}: {sorted(strays)} appears under [tool.setuptools.package-data] -- " "it belongs to [tool.setuptools.packages.find]; a table header was inserted mid-table, " "so packaging discovery silently lost it",
                )

    def test_every_built_wheel_ships_py_typed(self) -> None:
        """The published artifact, not the declaration: 0.1.0's wheel imported and still had no marker."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                pkg = _import_name(subdir)
                names, metadata = _built_wheel(subdir)
                marker = f"{pkg}/py.typed"
                self.assertEqual(names.count(marker), 1, f"{subdir.name}: wheel members containing py.typed: {[name for name in names if 'py.typed' in name]}")
                self.assertIn(f"{pkg}/__init__.py", names, f"{subdir.name}: wheel has no {pkg}/__init__.py -- the build did not package the library")
                self.assertIn(f"Classifier: {TYPED_CLASSIFIER}\n", metadata, f"{subdir.name}: built METADATA has no {TYPED_CLASSIFIER!r} classifier")
                packaged_tests = _tests_packaged(names)
                self.assertFalse(packaged_tests, f"{subdir.name}: wheel packages a tests tree: {packaged_tests}")


if __name__ == "__main__":
    unittest.main()
