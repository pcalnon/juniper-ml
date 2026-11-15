#!/usr/bin/env python3
"""Run ``pre-commit run --files <paths>`` in a worktree, the paths read from a list file, and report hook rewrites.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the pre-commit gate for juniper-data-client#262, juniper-cascor-client#197 and
        juniper-deploy#275)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/py315/GREEN_LEGS_BRIEF.md step 4 ("/opt/miniforge3/bin/pre-commit run --files <changed>")

Why this exists
---------------
This host's session refuses some shell commands that list ``.github/workflows/`` paths, so the paths come from a
file. ``/opt/miniforge3/bin/pre-commit`` is used because the ``pre-commit`` on PATH may be a broken shim. A hook
that rewrites a file leaves the fix in the WORKTREE, not the index, and the API upload sends the worktree copy, so
the sha256 of every listed file is taken before and after and any rewrite is named.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_green_legs_precommit.py --worktree DIR --list FILE --log FILE
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # nosec B404 - runs pre-commit by design
import sys
from pathlib import Path

PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--list", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    args = ap.parse_args()
    paths = [line.strip() for line in args.list.read_text(encoding="utf-8").splitlines() if line.strip()]
    before = {p: digest(args.worktree / p) for p in paths}
    proc = subprocess.run([PRE_COMMIT, "run", "--files", *paths], cwd=args.worktree, capture_output=True, text=True)  # nosec B603
    after = {p: digest(args.worktree / p) for p in paths}
    args.log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    changed = [p for p in paths if before[p] != after[p]]
    print(proc.stdout + proc.stderr)
    print(f"pre-commit exit={proc.returncode}; files rewritten by hooks: {changed or 'none'}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
