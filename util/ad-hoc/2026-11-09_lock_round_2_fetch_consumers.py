#!/usr/bin/env python3
"""Fetch a fresh ``main`` source tree of each R-OBS-SC-2 lock-round consumer, pinned to one SHA.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why
---
The second lock round edits each consumer's lock files and ``CHANGELOG.md`` and uploads them
whole through ``util/open_signed_pr.py``. A whole-file upload from a stale copy reverts whatever
merged since, and the sibling primaries lag ``origin/main``. So each consumer is fetched as the
GitHub tarball of the exact SHA ``main`` resolves to now, and that SHA is recorded beside it; the
PR step re-resolves ``main`` and refuses if it moved.

A worktree-isolated session may not run ``git`` against a sibling checkout, so this uses the
REST API (``gh api``) and never a working tree.

Output: ``<out>/<repo>/`` (the tree, top directory stripped) and ``<out>/<repo>.sha``.
An existing ``<out>/<repo>/`` is refused unless ``--replace`` is given.

Usage: python3 util/ad-hoc/2026-11-09_lock_round_2_fetch_consumers.py --out tmp/lr2/src [--replace]
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import tarfile
from pathlib import Path

OWNER = "pcalnon"
REPOS = ("juniper-data", "juniper-cascor", "juniper-canopy", "juniper-recurrence")


def _gh_bytes(args: list[str]) -> bytes:
    proc = subprocess.run(["gh", *args], capture_output=True)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} -> exit {proc.returncode}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def _main_sha(repo: str) -> str:
    sha = _gh_bytes(["api", f"repos/{OWNER}/{repo}/commits/main", "--jq", ".sha"]).decode().strip()
    if len(sha) != 40:
        raise SystemExit(f"{repo}: unexpected main sha {sha!r}")
    return sha


def _extract(blob: bytes, dest: Path) -> tuple[int, list[str]]:
    """Extract under ``dest`` with the ``data`` filter; a member it refuses is skipped and named.

    The refused members are symlinks that leave the tree (cascor's and canopy's ``claudey`` point
    into a sibling juniper-ml checkout), which no lock step reads.
    """
    count = 0
    skipped: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        members = tar.getmembers()
        if not members:
            raise SystemExit(f"{dest.name}: empty tarball")
        top = members[0].name.split("/", 1)[0]
        for member in members:
            parts = member.name.split("/", 1)
            if parts[0] != top or len(parts) == 1 or not parts[1]:
                continue
            member.name = parts[1]
            try:
                tar.extract(member, dest, filter="data")
            except tarfile.FilterError as exc:
                skipped.append(f"{member.name} ({type(exc).__name__})")
                continue
            count += 1
    return count, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--replace", action="store_true", help="replace an existing tree")
    parser.add_argument("--repo", action="append", choices=REPOS, help="limit to these repos (repeatable)")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for repo in args.repo or REPOS:
        dest = args.out / repo
        if dest.exists():
            if not args.replace:
                print(f"{repo}: {dest} exists; pass --replace", file=sys.stderr)
                return 1
            shutil.rmtree(dest)
        sha = _main_sha(repo)
        blob = _gh_bytes(["api", f"repos/{OWNER}/{repo}/tarball/{sha}"])
        dest.mkdir(parents=True)
        count, skipped = _extract(blob, dest)
        (args.out / f"{repo}.sha").write_text(sha + "\n")
        print(f"{repo}: main={sha} files={count} -> {dest}")
        for name in skipped:
            print(f"  skipped (outside the tree): {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
