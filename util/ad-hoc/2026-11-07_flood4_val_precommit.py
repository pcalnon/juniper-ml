"""
Flood-4 validation: run the repo's PINNED pre-commit on every carrier path copied into this worktree,
then prove whether any hook rewrote a file (blob hash vs the carrier's staged tree) and restore any
rewritten file from the tree, so this worktree keeps the carrier's bytes.

Usage: python3 <this> <log> [hook-id]   (hook-id runs one hook, e.g. mypy; default: all hooks)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main() -> int:
    log = Path(sys.argv[1])
    hook = sys.argv[2] if len(sys.argv) > 2 else None
    paths = [p for p in git("diff", "--name-only", "--no-renames", BASE, TREE).splitlines() if not p.startswith("util/ad-hoc/")]
    cmd = [PRE_COMMIT, "run"] + ([hook] if hook else []) + ["--files", *paths]
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    rewritten = []
    for p in paths:
        want = git("rev-parse", f"{TREE}:{p}").strip()
        if blob_sha((HERE / p).read_bytes()) != want:
            rewritten.append(p)
            (HERE / p).write_bytes(subprocess.run(["git", "cat-file", "blob", want], cwd=HERE, check=True, capture_output=True).stdout)
    log.write_text(f"command: {' '.join(cmd[:4])} ... ({len(paths)} paths)\nrc: {r.returncode}\nrewritten_by_hooks_then_restored: {rewritten}\n\n{r.stdout}\n{r.stderr}\n")
    print(f"rc={r.returncode} paths={len(paths)} rewritten={rewritten}")
    for line in r.stdout.splitlines():
        if "Failed" in line or "error" in line.lower():
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
