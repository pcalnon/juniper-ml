#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-08_flood3_ml_docs_a_eval.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Ad-hoc, read-only evaluation helper for Cursor-fleet flood #3, evaluator slice "ml-docs-a"
#   (12 juniper-ml docs PRs). For each PR head fetched into refs/flood3/mlda/p<N> it reports:
#   own commits (origin/main..head), ahead/behind, merge-base, the merge-tree result against
#   origin/main (clean or the conflicted paths), and the PR's own added lines per file
#   (merge-base..head), excluding Version / Last Updated / Date stamp lines.
#
#   It never mutates any ref, branch, index or working tree. Output goes to stdout (or --out).
#
# Usage:
#   python3 util/ad-hoc/2026-10-08_flood3_ml_docs_a_eval.py summary
#   python3 util/ad-hoc/2026-10-08_flood3_ml_docs_a_eval.py added <N> [--file PATH]
#   python3 util/ad-hoc/2026-10-08_flood3_ml_docs_a_eval.py diff <N> [--file PATH]
#####################################################################################################################################################################################################
"""Read-only flood-3 docs-PR evaluation helper (slice ml-docs-a)."""

import argparse
import re
import subprocess
import sys

PRS = [2119, 2122, 2125, 2128, 2137, 2155, 2158, 2160, 2162, 2167, 2177, 2181]
REF = "refs/flood3/mlda/p{n}"
STAMP_RE = re.compile(r"^\*\*(Version|Last Updated|Date)\*\*:?|^\*\*(Version|Last Updated|Date):\*\*")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def merge_base(n: int) -> str:
    return git("merge-base", "origin/main", REF.format(n=n)).stdout.strip()


def summary() -> None:
    for n in PRS:
        ref = REF.format(n=n)
        head = git("rev-parse", "--short=10", ref).stdout.strip()
        ahead = git("rev-list", "--count", f"origin/main..{ref}").stdout.strip()
        behind = git("rev-list", "--count", f"{ref}..origin/main").stdout.strip()
        mb = merge_base(n)
        log = git("log", "--no-show-signature", "--format=   %h %s", f"origin/main..{ref}").stdout.rstrip()
        mt = git("merge-tree", "--write-tree", "--name-only", "origin/main", ref, check=False)
        lines = mt.stdout.strip().splitlines()
        if mt.returncode == 0:
            mtres = "clean"
        else:
            # first line is the tree; then conflicted file names until a blank line
            conflicted = []
            for ln in lines[1:]:
                if not ln.strip():
                    break
                conflicted.append(ln.strip())
            mtres = "CONFLICT: " + ", ".join(conflicted)
        files = git("diff", "--stat=200", mb, ref).stdout.rstrip()
        print(f"== #{n} head={head} ahead={ahead} behind={behind} merge-base={mb[:10]}")
        print(log)
        print(f"   merge-tree vs origin/main: {mtres}")
        print("\n".join("   " + x for x in files.splitlines()))


def added(n: int, path: str | None) -> None:
    mb = merge_base(n)
    args = ["diff", "-U0", mb, REF.format(n=n)]
    if path:
        args += ["--", path]
    out = git(*args).stdout
    cur = None
    for ln in out.splitlines():
        if ln.startswith("+++ "):
            cur = ln[6:] if ln.startswith("+++ b/") else ln[4:]
            print(f"### {cur}")
            continue
        if ln.startswith("@@"):
            print(ln)
            continue
        if ln.startswith("+") and not ln.startswith("+++"):
            body = ln[1:]
            if STAMP_RE.search(body.strip()):
                print("   [stamp] " + body)
            else:
                print("+" + body)
        elif ln.startswith("-") and not ln.startswith("---"):
            body = ln[1:]
            if STAMP_RE.search(body.strip()):
                print("   [stamp-] " + body)
            else:
                print("-" + body)


def diff(n: int, path: str | None) -> None:
    mb = merge_base(n)
    args = ["diff", mb, REF.format(n=n)]
    if path:
        args += ["--", path]
    sys.stdout.write(git(*args).stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    a = sub.add_parser("added")
    a.add_argument("n", type=int)
    a.add_argument("--file")
    d = sub.add_parser("diff")
    d.add_argument("n", type=int)
    d.add_argument("--file")
    ns = ap.parse_args()
    if ns.cmd == "summary":
        summary()
    elif ns.cmd == "added":
        added(ns.n, ns.file)
    else:
        diff(ns.n, ns.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
