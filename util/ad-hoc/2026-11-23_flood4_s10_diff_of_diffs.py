#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_diff_of_diffs.py
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
#     Flood-4 session 10. Check a re-homed change against the change it was rebuilt from: for each path, the lines the
#     OLD change added/removed (old base -> recovered build) against the lines the NEW change adds/removes (new base ->
#     the staged index), as multisets. Prints every line that is in one change and not the other, and checks that the
#     staged blob equals the file in --final. Run from the juniper-ml worktree that holds the staged change. Read-only.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_diff_of_diffs.py --old-base 445ebf4e --new-base origin/main --recovered DIR --final DIR --paths FILE
#####################################################################################################################################################################################################
"""Compare an old change with its rebuild on a new base, line by line."""

import argparse
import collections
import difflib
import hashlib
import os
import subprocess
import sys


def _show(ref, path):
    proc = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, check=False)
    return proc.stdout.decode("utf-8", errors="replace").splitlines() if proc.returncode == 0 else []


def _staged(path):
    proc = subprocess.run(["git", "show", f":{path}"], capture_output=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _delta(before, after):
    added, removed = collections.Counter(), collections.Counter()
    for line in difflib.unified_diff(before, after, lineterm="", n=0):
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith("+"):
            added[line[1:]] += 1
        elif line.startswith("-"):
            removed[line[1:]] += 1
    return added, removed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-base", required=True)
    parser.add_argument("--new-base", required=True)
    parser.add_argument("--recovered", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--paths", required=True)
    args = parser.parse_args(argv)
    with open(args.paths, encoding="utf-8") as handle:
        paths = [p.strip() for p in handle if p.strip()]
    problems = 0
    for path in paths:
        blob = _staged(path)
        final_path = os.path.join(args.final, path)
        final = _read_bytes(final_path) if os.path.isfile(final_path) else None
        same_final = blob is not None and final is not None and hashlib.sha256(blob).digest() == hashlib.sha256(final).digest()
        recovered = _read_bytes(os.path.join(args.recovered, path)).decode("utf-8", errors="replace").splitlines()
        old_added, old_removed = _delta(_show(args.old_base, path), recovered)
        new_added, new_removed = _delta(_show(args.new_base, path), (blob or b"").decode("utf-8", errors="replace").splitlines())
        only_old_add, only_new_add = old_added - new_added, new_added - old_added
        only_old_rem, only_new_rem = old_removed - new_removed, new_removed - old_removed
        clean = not (only_old_add or only_new_add or only_old_rem or only_new_rem)
        status = "same-change" if clean else "DIFFERS"
        print(f"{status:>11}  staged==final:{same_final!s:<5}  +{sum(new_added.values())} -{sum(new_removed.values())}  {path}")
        if not same_final:
            problems += 1
        if not clean:
            for label, counter in (("only-old +", only_old_add), ("only-new +", only_new_add), ("only-old -", only_old_rem), ("only-new -", only_new_rem)):
                for text, count in counter.items():
                    print(f"      {label} x{count}: {text[:150]}")
    print(f"paths={len(paths)} staged-vs-final mismatches={problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
