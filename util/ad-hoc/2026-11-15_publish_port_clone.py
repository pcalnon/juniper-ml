#!/usr/bin/env python3
"""Clone sibling repos fresh from GitHub's default branch into a directory, for the one-artifact publish ports.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port juniper-cascor#763 / #767's one-artifact publish fix to the other publishing repos)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py (the audit naming the 18 publishers)

Why
---
A worktree-isolated session may not point git at a sibling checkout, and the sibling primaries lag ``origin/main``
(a stale base is how a whole-file upload reverts someone's merge). Each port therefore edits a FRESH clone of the
repo's ``main``, made here; the command line never names ``.github`` paths, which the isolation guard refuses.

    python3 -I util/ad-hoc/2026-11-15_publish_port_clone.py --dest-root tmp/ports/clones juniper-data juniper-canopy ...

Each repo lands in ``<dest-root>/<repo>``. An existing destination is refused, never overwritten. ``--depth`` (default
50) keeps enough history to read recent changes to a workflow. Prints each clone's HEAD sha and commit date.

Exit status: 0 when every clone succeeded; 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

OWNER = "pcalnon"


def run(argv: "list[str]", cwd: "Path | None" = None) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest-root", required=True, type=Path)
    parser.add_argument("--depth", type=int, default=50)
    parser.add_argument("repos", nargs="+")
    args = parser.parse_args(argv)
    args.dest_root.mkdir(parents=True, exist_ok=True)
    failed = 0
    for repo in args.repos:
        dest = args.dest_root / repo
        if dest.exists():
            print(f"REFUSED {repo}: {dest} exists")
            failed += 1
            continue
        proc = run(["gh", "repo", "clone", f"{OWNER}/{repo}", str(dest), "--", f"--depth={args.depth}", "--no-tags"])
        if proc.returncode != 0:
            print(f"FAILED {repo}: {proc.stderr.strip()}")
            failed += 1
            continue
        head = run(["git", "log", "-1", "--format=%H %cI %s"], cwd=dest)
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dest)
        print(f"{repo}: {branch.stdout.strip()} {head.stdout.strip()}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
