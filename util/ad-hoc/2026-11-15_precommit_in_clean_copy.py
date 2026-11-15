#!/usr/bin/env python3
"""Run pre-commit on named files in a fresh copy of a checkout that carries NO .git of its own (nor any tmp/).

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the release-train gap fixes and the one-artifact publish ports)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py (the variant this one fixes)

Why
---
``precommit_in_copy.py`` copies a tree and runs ``git init`` + ``git add -A`` in the copy. A git WORKTREE's ``.git`` is
a FILE naming the main repository's per-worktree directory, so a copy of it carries that file, ``git init`` re-inits the
real repository, and ``git add -A`` stages the copy's files into the real worktree's index. That helper was written for
tarball trees, which have no ``.git``; this one leaves ``.git`` (and every ``tmp`` directory) out of the copy, so the
``git init`` makes a new, private repository. pre-commit then sees every named file, tracked or not (``--files`` on an
untracked file in a real checkout is skipped by some hooks), and a hook's rewrite lands only in the copy.

    python3 -I util/ad-hoc/2026-11-15_precommit_in_clean_copy.py SRC_TREE DEST_DIR PRE_COMMIT_BIN FILE [FILE ...]

Prints pre-commit's output, each named file a hook changed, then exit=<code>. Exit status: pre-commit's; 2 when refused.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    src, dest, pre_commit = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
    files = sys.argv[4:]
    if dest.exists():
        print(f"REFUSED: {dest} exists")
        return 2
    if src == dest or src in dest.parents and not any(part == "tmp" for part in dest.relative_to(src).parts):
        print(f"REFUSED: {dest} would be copied into itself (put it under a tmp/ directory of the source)")
        return 2
    shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns("tmp", ".git"))
    if (dest / ".git").exists():
        print("REFUSED: the copy holds a .git")
        return 2
    before = {f: digest(dest / f) for f in files}
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        proc = subprocess.run(argv, cwd=dest, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"{' '.join(argv)} failed: {proc.stderr}")
            return 2
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=dest, capture_output=True, text=True, check=False).stdout.strip()
    if Path(top).resolve() != dest:
        print(f"REFUSED: git in the copy resolves to {top!r}, not the copy")
        return 2
    proc = subprocess.run([pre_commit, "run", "--files", *files], cwd=dest, capture_output=True, text=True, check=False)
    print(proc.stdout)
    print(proc.stderr)
    changed = [f for f in files if digest(dest / f) != before[f]]
    print("changed by hooks: " + (", ".join(changed) if changed else "none"))
    print(f"exit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
