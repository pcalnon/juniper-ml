#!/usr/bin/env python3
"""Print ``--add LOCAL:REPOPATH`` arguments for every modified and untracked file in this worktree.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper for util/open_signed_pr.py)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc. A headless session cannot ``git commit`` (hardware signing key), so a docs PR with
             many files goes through ``util/open_signed_pr.py``, whose ``--add`` is repeatable. This prints
             one ``--add`` per changed file so the call can be ``xargs -a <args-file> python3
             util/open_signed_pr.py ...`` without a shell loop (the worktree-isolation hook refuses loops).

Run (from the worktree root):
    python3 util/ad-hoc/2026-10-05_docs_pr_add_args.py > <scratch>/add-args.txt
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True).stdout.strip())
    modified = subprocess.run(["git", "ls-files", "--modified"], check=True, capture_output=True, text=True, cwd=root).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], check=True, capture_output=True, text=True, cwd=root).stdout.split()
    paths = sorted(set(modified) | set(untracked))
    for rel in paths:
        local = root / rel
        if not local.is_file():
            print(f"skipping non-file {rel}", file=sys.stderr)
            continue
        print(f"--add\n{local}:{rel}")
    print(f"{len(paths)} paths", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
