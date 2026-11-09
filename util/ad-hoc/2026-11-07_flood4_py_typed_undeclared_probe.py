"""
Probe: does a sub-package wheel ship py.typed when package-data no longer declares it?

Draft juniper-ml#2410 added a negative control asserting that emptying `<import> = ["py.typed"]`
drops the marker from the built wheel; it failed for every sub-package on the merged tree. This
probe builds each in-repo sub-package twice in a temporary copy -- as committed, and with that
package-data entry emptied -- and prints whether `<import>/py.typed` is in each wheel, plus the
setuptools version and its build_py implicit data patterns. Writes nothing in the repository.

Usage: python3 util/ad-hoc/2026-11-07_flood4_py_typed_undeclared_probe.py   (from the worktree root)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (flood-4 tests carrier build, #2410's negative control)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2410; tests/test_subpackage_py_typed.py
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

import setuptools
import setuptools.build_meta as build_meta
from setuptools.command import build_py

SUBPACKAGES = ["juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core"]


def _import_name(project: Path) -> str:
    with open(project / "pyproject.toml", "rb") as fh:
        data = tomllib.load(fh)
    return next(iter(data["tool"]["setuptools"]["package-data"]))


def _wheel_has_marker(project: Path, import_name: str, *, undeclared: bool) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"py-typed-probe-{project.name}-") as tmp:
        copy = Path(tmp) / "project"
        shutil.copytree(project, copy, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__"))
        if undeclared:
            pyproject = copy / "pyproject.toml"
            needle = f'{import_name} = ["py.typed"]\n'
            text = pyproject.read_text(encoding="utf-8")
            if needle not in text:
                raise SystemExit(f"{project.name}: {needle!r} not found")
            pyproject.write_text(text.replace(needle, f"{import_name} = []\n", 1), encoding="utf-8")
        out = Path(tmp) / "dist"
        out.mkdir()
        cwd = os.getcwd()
        os.chdir(copy)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                name = build_meta.build_wheel(str(out))
        finally:
            os.chdir(cwd)
        with zipfile.ZipFile(out / name) as archive:
            return f"{import_name}/py.typed" in archive.namelist()


def main() -> int:
    print(f"setuptools {setuptools.__version__}; build_py._IMPLICIT_DATA_FILES = {getattr(build_py, '_IMPLICIT_DATA_FILES', None)!r}")
    project = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for sub in [project.name] if project else SUBPACKAGES:
        path = Path(sub).resolve()
        name = _import_name(path)
        declared = _wheel_has_marker(path, name, undeclared=False)
        undeclared = _wheel_has_marker(path, name, undeclared=True)
        print(f"{sub}: declared -> py.typed in wheel: {declared}; package-data emptied -> py.typed in wheel: {undeclared}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
