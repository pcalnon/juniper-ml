#!/usr/bin/env python3
"""Does a published wheel carry every module its own code imports?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release verification
Author:      Paul Calnon
Created:     2026-09-17
Version:     0.2.0
License:     MIT License
Status:      single-use, but generic across packages (container-registry arc)

Why this exists
---------------
The canopy defect of 2026-09-15: every published juniper-canopy wheel back to 0.5.0 omits 10
top-level ``src/*.py`` modules that 13 of its own shipped files import, so
``pip install juniper-canopy`` cannot import its dashboard. ``packages.find`` collects
PACKAGES (dirs with ``__init__.py``) and silently drops loose top-level MODULES; ``pip check``
validates dependency metadata, not importability, so it cannot see it.

CALIBRATION, not assumption. v0.1.0 of this check (the worker-specific
``2026-09-17_check_worker_wheel_completeness.py``) keyed only on imports PREFIXED with the
distribution's own package name, and would therefore have MISSED the canopy defect entirely --
canopy's omitted modules are imported BARE (``from layouts import ...``), because they were
top-level in ``src/``. A checker that cannot find the known instance proves nothing about a
clean one. This version resolves bare imports against the wheel's own top-level names and is
run against canopy as a POSITIVE CONTROL before its verdict on anything else is believed.

Method: parse every packaged module with ``ast``; for each import, decide whether it names
something the wheel is responsible for (a sibling top-level module/package, or a dotted path
under one) and, if so, assert that path is present.

Limits: proves the wheel is SELF-CONSISTENT, not that it runs. A third-party dependency
missing from ``[project.dependencies]`` does not show up here.

Usage:
    python3 util/ad-hoc/2026-09-17_wheel_import_completeness.py juniper-cascor-worker 0.6.0
    python3 util/ad-hoc/2026-09-17_wheel_import_completeness.py juniper-canopy 0.8.0   # control

Exit status:
    0  every first-party import resolves inside the wheel
    1  at least one imported module is NOT packaged
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

STDLIB = set(sys.stdlib_module_names)


def fetch_wheel(pkg: str, version: str) -> dict[str, bytes]:
    try:
        with urllib.request.urlopen(  # noqa: S310 - fixed https host
            f"https://pypi.org/pypi/{pkg}/{version}/json", timeout=60
        ) as resp:
            data = json.load(resp)
        url = next(u["url"] for u in data["urls"] if u["packagetype"] == "bdist_wheel")
        with urllib.request.urlopen(url, timeout=180) as resp:  # noqa: S310 - PyPI CDN
            blob = resp.read()
    except (urllib.error.URLError, StopIteration, ValueError, KeyError) as exc:
        print(f"could not fetch the {pkg} {version} wheel: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

    return {i.filename: zf.read(i) for zf in [zipfile.ZipFile(io.BytesIO(blob))] for i in zf.infolist() if not i.is_dir()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("package")
    ap.add_argument("version")
    ap.add_argument("--expect-missing", action="store_true",
                    help="positive control: exit 0 only if omissions ARE found")
    args = ap.parse_args()

    files = fetch_wheel(args.package, args.version)
    members = set(files)
    py_files = sorted(
        n for n in members
        if n.endswith(".py") and ".dist-info/" not in n and ".data/" not in n
    )

    # The names this wheel is responsible for: its top-level modules and packages.
    owned: set[str] = set()
    for n in members:
        if ".dist-info/" in n or ".data/" in n:
            continue
        head = n.split("/", 1)[0]
        if head.endswith(".py"):
            owned.add(head[:-3])
        elif "/" in n:
            owned.add(head)
    owned -= {""}

    print(f"{args.package} {args.version}: {len(members)} members, {len(py_files)} modules")
    print(f"  top-level names owned by this wheel: {sorted(owned)}\n")
    if not py_files:
        print("no packaged modules -- refusing to report success", file=sys.stderr)
        return 2

    def present(dotted: str) -> bool:
        p = dotted.replace(".", "/")
        return f"{p}.py" in members or f"{p}/__init__.py" in members

    # Declared third-party dependencies, from the wheel's own METADATA. An import of
    # one of these is somebody else's problem and must not be reported here.
    declared: set[str] = set()
    for n in members:
        if n.endswith(".dist-info/METADATA"):
            for line in files[n].decode("utf-8", "replace").splitlines():
                if line.startswith("Requires-Dist:"):
                    name = line.split(":", 1)[1].strip()
                    for sep in (" ", ";", "[", "(", "=", "<", ">", "!", "~"):
                        name = name.split(sep, 1)[0]
                    if name:
                        # PyPI name -> import name is not 1:1; keep both spellings.
                        declared.add(name.replace("-", "_").lower())
                        declared.add(name.replace("_", "-").lower())

    def owns(dotted: str) -> bool:
        """Is this wheel responsible for `dotted`?

        A name already packaged here is obviously ours. **So is a name that is neither
        stdlib nor a declared dependency** -- and that second clause is the load-bearing
        one: a module the wheel FORGOT TO SHIP cannot appear in `owned`, so keying only on
        `owned` makes the omission invisible. That is precisely the canopy shape (bare
        `from layouts import ...` against a top-level module `packages.find` dropped), and
        v0.1.0 of this check missed all ten of them for exactly that reason.
        """
        head = dotted.split(".", 1)[0]
        if head in STDLIB:
            return False
        if head in owned:
            return True
        return head.lower() not in declared

    missing: list[tuple[str, str]] = []
    checked = 0

    for name in py_files:
        try:
            tree = ast.parse(files[name].decode("utf-8"), filename=name)
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"  could not parse {name}: {exc}", file=sys.stderr)
            return 2

        parts = name[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        pkg_parts = parts[:-1]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if owns(alias.name):
                        checked += 1
                        if not present(alias.name):
                            missing.append((name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                    target = ".".join(base + ([node.module] if node.module else []))
                    if not target:
                        continue
                    checked += 1
                    if not present(target) and not any(
                        present(f"{target}.{a.name}") for a in node.names
                    ):
                        missing.append((name, target))
                elif node.module and owns(node.module):
                    checked += 1
                    if not present(node.module):
                        missing.append((name, node.module))

    print(f"  first-party import references checked: {checked}")
    if checked == 0:
        print("\n  !! zero first-party imports found -- this check proved nothing.", file=sys.stderr)
        return 1

    if missing:
        uniq = sorted({m for _, m in missing})
        print(f"\n  {len(missing)} import site(s) reference {len(uniq)} module(s) NOT in the wheel:")
        for m in uniq:
            srcs = sorted({s for s, d in missing if d == m})
            print(f"       {m}   <- imported by {len(srcs)} file(s), e.g. {srcs[0]}")
        if args.expect_missing:
            print("\n  CONTROL PASSED: the checker detects the known omission.")
            return 0
        return 1

    if args.expect_missing:
        print("\n  !! CONTROL FAILED: expected to find omissions and found none.", file=sys.stderr)
        return 1
    print(f"\n  OK: all {checked} first-party import references resolve inside the wheel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
