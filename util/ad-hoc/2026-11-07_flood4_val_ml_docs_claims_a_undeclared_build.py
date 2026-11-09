"""
Build juniper-config-tools with its py.typed package-data entry removed and list the wheel (flood-4 docs validator).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-ml docs carrier validation, claims lens slice A (draft #2409's py.typed claim; tests
         draft #2410's negative control)

Usage: <python with setuptools> 2026-11-07_flood4_val_ml_docs_claims_a_undeclared_build.py <repo_root> <out_dir>

Copies <repo_root>/juniper-config-tools to <out_dir>/project (ignoring build artefacts), deletes the
[tool.setuptools.package-data] table, builds a wheel with setuptools.build_meta (no isolation, the running
interpreter's setuptools) into <out_dir>/dist, and prints the setuptools version and the wheel's members.
Nothing under <repo_root> is written.
"""

import os
import re
import shutil
import sys
import zipfile


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    repo, out_dir = argv[1], argv[2]
    project = os.path.join(out_dir, "project")
    dist = os.path.join(out_dir, "dist")
    for path in (project, dist):
        if os.path.exists(path):
            shutil.rmtree(path)
    shutil.copytree(os.path.join(repo, "juniper-config-tools"), project, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__", ".pytest_cache"))
    os.makedirs(dist)
    pyproject = os.path.join(project, "pyproject.toml")
    with open(pyproject, encoding="utf-8") as fh:
        text = fh.read()
    stripped = re.sub(r"(?ms)^\[tool\.setuptools\.package-data\]\n(?:[^\[\n].*\n)*", "", text)
    if stripped == text:
        print("package-data table not found; nothing removed", file=sys.stderr)
        return 1
    with open(pyproject, "w", encoding="utf-8") as fh:
        fh.write(stripped)
    print("package-data table present after edit:", "[tool.setuptools.package-data]" in stripped)
    print("py.typed present in source copy:", os.path.isfile(os.path.join(project, "juniper_config_tools", "py.typed")))
    import setuptools
    import setuptools.build_meta as build_meta

    os.chdir(project)
    wheel = build_meta.build_wheel(dist)
    with zipfile.ZipFile(os.path.join(dist, wheel)) as zf:
        names = zf.namelist()
    print("setuptools", setuptools.__version__, "wheel", wheel)
    print("members:", names)
    print("py.typed in wheel:", "juniper_config_tools/py.typed" in names)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
