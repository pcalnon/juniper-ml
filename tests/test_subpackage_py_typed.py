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

**Two independent things must both hold, which is why this gate checks both.**
The marker file existing in the repo does *not* mean it reaches consumers:
setuptools ships it only if it is also declared as package data, and these
packages carry no ``MANIFEST.in``. A gate that checked only the file would go
green while every wheel shipped without it -- the vacuous-pass class.

The declaration is still not the wheel. juniper-config-tools 0.1.0 imported
and printed its version, and the published wheel's file list was
``__init__.py``, ``__main__.py``, ``_env_aliases.py``, ``_version.py`` and
the dist-info: no ``py.typed``. A type checker then treats the package as
untyped. ``test_every_built_wheel_ships_py_typed`` builds each wheel and
requires ``<import>/py.typed`` plus the ``Typing :: Typed`` classifier.
``test_an_undeclared_marker_is_omitted_from_the_wheel`` empties that
package-data list on a copy and requires the marker to be absent while
``__init__.py`` is still packaged, so a build that ignored package-data
cannot pass both tests.

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


def _built_wheel(project: Path, *, drop_py_typed: bool) -> tuple[list[str], str]:
    """Build ``project`` in a temp copy and return ``(wheel member names, METADATA text)``.

    ``drop_py_typed`` rewrites ``<import> = ["py.typed"]`` to an empty list before the build.
    That is the juniper-config-tools 0.1.0 shape: the marker file can sit in the tree and still
    miss the wheel, because these packages have no ``MANIFEST.in``.
    """
    import_name = _import_name(project)
    with tempfile.TemporaryDirectory(prefix=f"py-typed-wheel-{project.name}-") as tmp:
        root = Path(tmp)
        copy = root / "project"
        shutil.copytree(project, copy, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__", ".pytest_cache", ".mypy_cache"))
        if drop_py_typed:
            pyproject = copy / "pyproject.toml"
            needle = f'{import_name} = ["py.typed"]\n'
            text = pyproject.read_text(encoding="utf-8")
            if needle not in text:
                raise AssertionError(f"{project.name}: package-data line {needle!r} not found; the omission check would build the real declaration")
            pyproject.write_text(text.replace(needle, f"{import_name} = []\n", 1), encoding="utf-8")
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
        """The file alone is not enough: undeclared, setuptools omits it from the wheel."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                pkg = _import_name(subdir)
                package_data = self.parsed[subdir.name].get("tool", {}).get("setuptools", {}).get("package-data", {})
                self.assertIn(
                    pkg,
                    package_data,
                    f"{subdir.name}: [tool.setuptools.package-data] does not declare '{pkg}' -- " "the marker exists in the repo but never reaches a wheel (no MANIFEST.in here)",
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
                names, metadata = _built_wheel(subdir, drop_py_typed=False)
                marker = f"{pkg}/py.typed"
                self.assertEqual(names.count(marker), 1, f"{subdir.name}: wheel members containing py.typed: {[name for name in names if 'py.typed' in name]}")
                self.assertIn(f"{pkg}/__init__.py", names, f"{subdir.name}: wheel has no {pkg}/__init__.py -- the build did not package the library")
                self.assertIn(f"Classifier: {TYPED_CLASSIFIER}\n", metadata, f"{subdir.name}: built METADATA has no {TYPED_CLASSIFIER!r} classifier")
                packaged_tests = _tests_packaged(names)
                self.assertFalse(packaged_tests, f"{subdir.name}: wheel packages a tests tree: {packaged_tests}")

    def test_an_undeclared_marker_is_omitted_from_the_wheel(self) -> None:
        """Emptying package-data is the 0.1.0 failure: the file stays in the tree and leaves the wheel."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                pkg = _import_name(subdir)
                names, _metadata = _built_wheel(subdir, drop_py_typed=True)
                self.assertNotIn(f"{pkg}/py.typed", names, f"{subdir.name}: an undeclared py.typed still reached the wheel; the positive test would pass without the declaration")
                self.assertFalse(any(name.endswith("py.typed") for name in names), f"{subdir.name}: py.typed shipped under another path: {[name for name in names if name.endswith('py.typed')]}")
                self.assertIn(f"{pkg}/__init__.py", names, f"{subdir.name}: the omission build did not package the library, so a missing marker would pass vacuously")


if __name__ == "__main__":
    unittest.main()
