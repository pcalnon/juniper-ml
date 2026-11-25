#!/usr/bin/env python3
"""
Read-only probe of the eight primaries' fetch state, by file reads alone (no git), for ruling 7's cleanup script.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 7 worktree cleanup, session 13)
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation (does the cleanup script need to fetch before it compares against origin/main?)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 7);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next.md

What it does
------------
For each primary under ``--juniper-root``: the mtime of ``.git/FETCH_HEAD``, the sha ``refs/remotes/origin/main``
holds (loose ref first, then ``packed-refs``), whether ``.git/shallow`` exists, and the count of registered linked
worktrees (directories under ``.git/worktrees/``). It reads files only: a worktree-isolated session may not run git
in another checkout, and this needs none. Prints one line per primary; writes nothing.

Usage
-----
    python3 util/ad-hoc/2026-11-25_flood4_s13_r7_primaries_probe.py [--juniper-root DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

PRIMARIES = (
    "juniper-ml",
    "juniper-data",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
)


def origin_main(gitdir: Path) -> str:
    """The sha refs/remotes/origin/main names, or '-' when neither the loose ref nor packed-refs holds it."""
    loose = gitdir / "refs" / "remotes" / "origin" / "main"
    if loose.is_file():
        return loose.read_text(encoding="ascii").strip()
    packed = gitdir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split(" ")
            if len(parts) == 2 and parts[1] == "refs/remotes/origin/main":
                return parts[0]
    return "-"


def mtime_utc(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        return "-"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--juniper-root", type=Path, default=Path(os.path.expanduser("~")) / "Development" / "python" / "Juniper")
    args = parser.parse_args()
    for name in PRIMARIES:
        gitdir = args.juniper_root / name / ".git"
        if not gitdir.is_dir():
            print(f"{name:<24} no .git directory")
            continue
        admin = gitdir / "worktrees"
        registered = sum(1 for p in admin.iterdir() if p.is_dir()) if admin.is_dir() else 0
        print(
            f"{name:<24} FETCH_HEAD={mtime_utc(gitdir / 'FETCH_HEAD')}  origin/main={origin_main(gitdir)[:12]:<12}  "
            f"{'SHALLOW' if (gitdir / 'shallow').exists() else 'full'}  registered_worktrees={registered}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
