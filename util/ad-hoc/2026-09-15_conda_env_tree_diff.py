#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: environment repair
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHAT THIS IS
------------
Compare the installed distributions of TWO site-packages trees in one conda env, to find what a
Python minor-version upgrade left behind.

WHY IT EXISTS
-------------
On 2026-09-12 ``JuniperCascor1`` was upgraded 3.13 -> 3.14. A conda minor-version upgrade creates
a NEW ``lib/pythonX.Y/site-packages`` and does **not** migrate the old one, so every pip-installed
distribution in the old tree becomes unreachable while still occupying disk. The old *interpreter*
is removed, so ``pip list`` cannot be run against the old tree at all — the only readable record
is the ``*.dist-info`` / ``*.egg-info`` directory names themselves.

``pip`` cannot answer this question and neither can ``conda list`` (which reports the env, not the
per-tree reality). Hence this.

WHAT IT DOES NOT DO
-------------------
It does not install, remove, or modify anything. It prints three lists. **Deliberately** —
deleting an orphaned tree can kill a live process: a service started before the upgrade keeps the
DELETED interpreter open (``/proc/<pid>/exe`` reads ``python3.13 (deleted)``) and lazily imports
from the old tree for its whole lifetime. Check for holders before removing anything::

    ps -eo pid,cmd --no-headers | grep "[J]uniperCascor1"
    readlink /proc/<pid>/exe          # "(deleted)" means it is holding a removed file
    grep -c "python3\\.13" /proc/<pid>/maps

USAGE
-----
    python3 util/ad-hoc/2026-09-15_conda_env_tree_diff.py \\
        --old /opt/miniforge3/envs/JuniperCascor1/lib/python3.13/site-packages \\
        --new /opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

#: ``<name>-<version>.dist-info`` / ``.egg-info``. Names are normalised per PEP 503 so that
#: ``ruamel.yaml`` and ``ruamel_yaml``, or ``Foo-Bar`` and ``foo_bar``, compare equal — otherwise
#: the diff reports dozens of phantom "missing" packages that are simply spelled differently.
_DIST = re.compile(r"^(?P<name>.+?)-(?P<version>[^-]+)\.(dist-info|egg-info)$")


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def read_tree(root: Path) -> dict[str, str]:
    """Map normalised distribution name -> version, from *-info directory names."""
    found: dict[str, str] = {}
    if not root.is_dir():
        return found
    for entry in root.iterdir():
        match = _DIST.match(entry.name)
        if match:
            found[normalise(match.group("name"))] = match.group("version")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--old", type=Path, required=True, help="the orphaned site-packages tree")
    parser.add_argument("--new", type=Path, required=True, help="the live site-packages tree")
    parser.add_argument("--user-site", type=Path, default=None, help="the USER site-packages tree (~/.local/lib/pythonX.Y/site-packages) — see below")
    parser.add_argument("--requirements", type=Path, default=None, help="write the missing set here, pip-installable")
    args = parser.parse_args()

    old = read_tree(args.old)
    new = read_tree(args.new)
    # WHY --user-site EXISTS. The first run of this tool reported colorama / iniconfig / pluggy
    # as "missing from the new tree" and they imported perfectly — because they resolve from
    # ~/.local, which is on sys.path but is NOT part of the environment. Reporting that as
    # "missing" is a false positive; reporting it as "present" would be worse, because the env is
    # then not self-contained and `python -s` (or PYTHONNOUSERSITE=1, or any isolated subprocess)
    # fails. Measured on this host before the repair:
    #     python -s -c "import pytest"  ->  ModuleNotFoundError: No module named 'pluggy'
    # So there are THREE states, not two, and the middle one is the interesting one.
    user = read_tree(args.user_site) if args.user_site else {}

    absent = sorted(set(old) - set(new) - set(user))
    user_only = sorted((set(old) - set(new)) & set(user))
    missing = sorted(set(old) - set(new))
    common_diff = sorted(name for name in set(old) & set(new) if old[name] != new[name])
    only_new = sorted(set(new) - set(old))

    print(f"old tree : {args.old}  ({len(old)} distributions)")
    print(f"new tree : {args.new}  ({len(new)} distributions)")
    if args.user_site:
        print(f"user site: {args.user_site}  ({len(user)} distributions)")
    print()
    if args.user_site:
        print(f"--- ABSENT everywhere ({len(absent)}) — the env is BROKEN for these ---")
        for name in absent:
            print(f"  {name}=={old[name]}")
        print()
        print(f"--- resolvable ONLY from USER SITE ({len(user_only)}) — the env is NOT self-contained ---")
        for name in user_only:
            print(f"  {name}=={user[name]}   (imports today; fails under `python -s` / PYTHONNOUSERSITE=1)")
        print()
    else:
        print(f"--- MISSING from the new tree ({len(missing)}) ---")
        for name in missing:
            print(f"  {name}=={old[name]}")
        print("  NOTE: pass --user-site to tell a REAL absence apart from a package that merely")
        print("        resolves from ~/.local. Both print here; only the first is unimportable.")
        print()
    print(f"--- version DIFFERS ({len(common_diff)}) — informational, the new tree wins ---")
    for name in common_diff:
        print(f"  {name}: old {old[name]}  ->  new {new[name]}")
    print()
    print(f"--- only in the new tree ({len(only_new)}) — gained by the upgrade ---")
    for name in only_new:
        print(f"  {name}=={new[name]}")

    if args.requirements and missing:
        # Names only, no pins: the old versions were built for the OLD interpreter and pinning
        # them invites a resolver failure or an ABI mismatch on the new one. The point is to
        # restore the package SET, letting the resolver pick what fits the new Python.
        args.requirements.write_text("\n".join(missing) + "\n", encoding="utf-8")
        print(f"\nwrote {len(missing)} names (unpinned, deliberately) to {args.requirements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
