#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. Run canopy's required `Sequence Safety` DOCS screen
# (juniper_ci_tools.docs_additions_check, the same classify_file the CI job calls) against an
# UNCOMMITTED working tree: the CI entry point diffs two refs, and the slice must stay uncommitted.
# Input is `git diff --unified=0 <base> -- <file>` (working tree vs base), which is the hunk shape
# file_diff() feeds classify_file() in CI. Scope = the tool's default (AGENTS.md, docs/**, notes/**).
# Run with an interpreter that has juniper-ci-tools installed (e.g. the JuniperCascor1 env).
# Usage: ..._seqsafety_worktree.py --repo <wt> --base <ref> [--min-run 5]
"""Docs deletion-magnitude screen over an uncommitted working tree."""

from __future__ import annotations

import argparse
import subprocess
import sys

from juniper_ci_tools import docs_additions_check as dac


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--min-run", type=int, default=5)
    args = ap.parse_args()
    names = subprocess.run(["git", "-C", args.repo, "diff", "--name-only", args.base], capture_output=True, text=True, check=True).stdout.split()
    fails = warns = screened = 0
    for path in names:
        if not dac.in_docs_scope(path):
            continue
        screened += 1
        diff = subprocess.run(["git", "-C", args.repo, "diff", "--unified=0", "--no-color", args.base, "--", path], capture_output=True, text=True, check=True).stdout
        for f in dac.classify_file(path, dac.parse_hunks(diff), args.min_run):
            # CI's run() exits 1 only on severity FAIL (heading-deletion, deletion-run); WARN never fails.
            if f.severity == "FAIL":
                fails += 1
                print(f"FAIL {path}: {f.reason} {f.detail}")
            else:
                warns += 1
    print(f"screened {screened} in-scope files: {fails} FAIL, {warns} WARN (WARN never fails the job)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
