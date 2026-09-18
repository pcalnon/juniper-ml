#!/usr/bin/env python3
"""Does the published juniper-cascor-worker wheel carry every module it imports?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release verification
Author:      Paul Calnon
Created:     2026-09-17
Version:     0.1.0
License:     MIT License
Status:      SUPERSEDED -- retained as provenance, do not rely on its verdict.

SUPERSEDED BY ``2026-09-17_wheel_import_completeness.py``. THIS VERSION IS PARTIALLY BLIND.
It recognises a first-party import only when the imported name is PREFIXED with the
distribution's own package name, so a module the wheel FORGOT TO SHIP is invisible to it --
the forgotten name cannot appear in the wheel, so nothing keys on it. Run against
juniper-canopy 0.8.0, where ten top-level modules are known to be missing, it finds ONE (and
only because that one happens to be imported relatively). Its clean verdict on the worker was
therefore weaker than it read. The successor resolves bare imports against the wheel's own
declared ``Requires-Dist`` set and is calibrated against canopy as a positive control before
its verdict on anything else is believed.

Why this exists
---------------
The canopy defect of 2026-09-15: EVERY published juniper-canopy wheel back to 0.5.0 omits 10
top-level ``src/*.py`` modules that 13 of its own shipped files import, so
``pip install juniper-canopy`` cannot import its dashboard. ``packages.find`` collects
PACKAGES (directories with ``__init__.py``) and silently drops loose top-level MODULES, and
``pip check`` cannot see it because it validates dependency metadata, not importability.

That is a packaging-configuration class, not a canopy bug, so it is worth asking of any
sibling wheel. This asks it of the worker's, statically -- no venv, no torch download (the
worker's real dependency tree is multi-GB, which is exactly why nobody checks this by hand).

Method: parse every packaged module with ``ast``, collect its ABSOLUTE first-party imports
(``juniper_cascor_worker.X``) and its RELATIVE imports (``from . import X``), resolve each to
the module path it requires, and assert that path is present in the wheel.

Limits, stated rather than implied: this proves the wheel is SELF-CONSISTENT, not that it
runs -- a third-party dependency missing from ``[project.dependencies]`` would not show up
here. It is the omission class the canopy defect belongs to, nothing wider.

Usage:
    python3 util/ad-hoc/2026-09-17_check_worker_wheel_completeness.py
    python3 util/ad-hoc/2026-09-17_check_worker_wheel_completeness.py --version 0.5.0

Exit status:
    0  every first-party import resolves inside the wheel
    1  at least one imported module is NOT packaged (the canopy class)
    2  could not fetch or parse the wheel
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile

PKG = "juniper-cascor-worker"
TOP = "juniper_cascor_worker"


def fetch_wheel(version: str) -> dict[str, bytes]:
    try:
        with urllib.request.urlopen(  # noqa: S310 - fixed https host
            f"https://pypi.org/pypi/{PKG}/{version}/json", timeout=60
        ) as resp:
            data = json.load(resp)
        url = next(u["url"] for u in data["urls"] if u["packagetype"] == "bdist_wheel")
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 - PyPI CDN
            blob = resp.read()
    except (urllib.error.URLError, StopIteration, ValueError, KeyError) as exc:
        print(f"could not fetch the {PKG} {version} wheel: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

    out = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            if not info.is_dir():
                out[info.filename] = zf.read(info)
    return out


def module_exists(members: set[str], dotted: str) -> bool:
    """Is `dotted` (e.g. juniper_cascor_worker.config) packaged, as module or package?"""
    path = dotted.replace(".", "/")
    return f"{path}.py" in members or f"{path}/__init__.py" in members


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="0.6.0")
    args = ap.parse_args()

    files = fetch_wheel(args.version)
    members = set(files)
    py_files = sorted(n for n in members if n.startswith(f"{TOP}/") and n.endswith(".py"))

    print(f"{PKG} {args.version}: {len(members)} wheel members, {len(py_files)} packaged modules\n")
    if not py_files:
        print("no packaged .py modules found -- refusing to report success", file=sys.stderr)
        return 2

    missing: list[tuple[str, str]] = []
    checked = 0

    for name in py_files:
        try:
            tree = ast.parse(files[name].decode("utf-8"), filename=name)
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"  could not parse {name}: {exc}", file=sys.stderr)
            return 2

        # The module's own package, for resolving relative imports.
        parts = name[: -len(".py")].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        pkg_parts = parts[:-1] if parts[-1] != TOP else parts

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == TOP or alias.name.startswith(f"{TOP}."):
                        checked += 1
                        if not module_exists(members, alias.name):
                            missing.append((name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative: from . import X / from .mod import Y
                    base = pkg_parts[: len(pkg_parts) - (node.level - 1)] if node.level > 1 else pkg_parts
                    target = ".".join(base + ([node.module] if node.module else []))
                    for alias in node.names:
                        candidate = f"{target}.{alias.name}"
                        checked += 1
                        # `from .mod import thing` -- thing may be a NAME in mod, not a module.
                        # Only flag when neither the submodule nor its parent is packaged.
                        if not module_exists(members, candidate) and not module_exists(members, target):
                            missing.append((name, candidate))
                elif node.module and (node.module == TOP or node.module.startswith(f"{TOP}.")):
                    checked += 1
                    if not module_exists(members, node.module):
                        missing.append((name, node.module))

    print(f"  first-party import references checked: {checked}")
    if checked == 0:
        print("\n  !! zero first-party imports found -- this check proved nothing.", file=sys.stderr)
        print("     Either the package is a single flat module or the parser is wrong.", file=sys.stderr)
        return 1

    if missing:
        print(f"\n  !! {len(missing)} import(s) reference modules NOT in the wheel "
              "(the canopy omission class):")
        for src, dotted in missing:
            print(f"       {src}  ->  {dotted}")
        return 1

    print(f"\n  OK: all {checked} first-party import references resolve inside the wheel.")
    print("      No sign of the canopy packaging-omission class here.")
    print("      (Self-consistency only -- this does not prove third-party deps are declared.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
