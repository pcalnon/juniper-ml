#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_tree_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-11-23
# Last Modified: 2026-11-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     READ-ONLY probe for flood-4 session 10. For each worktree path given, print its branch, HEAD, every
#     uncommitted entry (staged / unstaged / untracked) with mtime (UTC) and the number of occurrences of a
#     substituted token (default "Overtoad", the 2026-11-20..22 blind "owner -> Overtoad" pass), and for each
#     --tmp-subdir the file count, the files carrying the token and the newest mtime. It changes nothing.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_tree_probe.py [--token Overtoad] [--tmp-subdir tmp/flood4-fix] PATH [PATH ...]
#####################################################################################################################################################################################################
"""Read-only uncommitted-state and substitution probe for worktrees."""

import argparse
import datetime as _dt
import os
import subprocess
import sys


def _git(path, *args):
    proc = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def _mtime(path):
    try:
        return _dt.datetime.fromtimestamp(os.lstat(path).st_mtime, tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    except OSError:
        return "-"


def _count(path, token):
    if os.path.islink(path):
        return "link"
    if not os.path.isfile(path):
        return "-"
    try:
        with open(path, "rb") as handle:
            return handle.read().count(token.encode())
    except OSError:
        return "err"


def _summary(path, lines, token, cutoff):
    """Counts per status code; detail only for staged entries and entries older than the cutoff (no file reads otherwise)."""
    counts = {}
    for line in lines:
        counts[line[:2]] = counts.get(line[:2], 0) + 1
    print("  status codes: " + ", ".join(f"'{code}'={n}" for code, n in sorted(counts.items())))
    for line in lines:
        rel = line[3:].split(" -> ", 1)[-1]
        full = os.path.join(path, rel)
        stamp = _mtime(full)
        staged = line[0] not in (" ", "?")
        if staged or stamp < cutoff:
            print(f"    {line[:2]} {stamp} {token}={_count(full, token)!s:>4}  {rel}{'  [STAGED]' if staged else ''}")


def probe(path, token, tmp_subdirs, summary=False, cutoff="2026-11-20"):
    print(f"==== {path}")
    if not os.path.isdir(path):
        print("  MISSING")
        return
    _, branch, _ = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
    _, head, _ = _git(path, "log", "-1", "--format=%h %cI %s")
    print(f"  branch={branch.strip()}  head={head.strip()[:140]}")
    _, status, err = _git(path, "status", "--porcelain=v1", "-uall")
    if err.strip():
        print(f"  status-stderr: {err.strip()[:200]}")
    lines = [ln for ln in status.splitlines() if ln.strip()]
    print(f"  uncommitted entries: {len(lines)}")
    if summary:
        _summary(path, lines, token, cutoff)
        lines = []
    for line in lines:
        rel = line[3:]
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        full = os.path.join(path, rel)
        print(f"    {line[:2]} {_mtime(full)} {token}={_count(full, token)!s:>4}  {rel}")
    for sub in tmp_subdirs:
        root = os.path.join(path, sub)
        if not os.path.isdir(root):
            print(f"  tmp {sub}: absent")
            continue
        total, hits, newest = 0, [], ""
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                full = os.path.join(dirpath, name)
                total += 1
                stamp = _mtime(full)
                newest = max(newest, stamp)
                count = _count(full, token)
                if isinstance(count, int) and count:
                    hits.append((os.path.relpath(full, path), count, stamp))
        print(f"  tmp {sub}: files={total} with-{token}={len(hits)} newest-mtime={newest}")
        for rel, count, stamp in hits[:40]:
            print(f"    HIT {stamp} {count:>4}  {rel}")
        if len(hits) > 40:
            print(f"    ... {len(hits) - 40} more")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", default="Overtoad")
    parser.add_argument("--tmp-subdir", action="append", default=[])
    parser.add_argument("--summary", action="store_true", help="counts per status code; list only staged entries and entries older than --cutoff")
    parser.add_argument("--cutoff", default="2026-11-20", help="UTC date; entries with an older mtime predate the rename pass")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    for path in args.paths:
        probe(path, args.token, args.tmp_subdir, summary=args.summary, cutoff=args.cutoff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
