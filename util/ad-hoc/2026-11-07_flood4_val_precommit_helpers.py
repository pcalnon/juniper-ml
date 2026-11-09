"""
Flood-4 validation: write the carrier's util/ad-hoc helper scripts (from its staged tree) into this worktree,
run the PINNED pre-commit and the G5 whole-scope home-path check on them, and report any hook rewrite
(blob hash vs the tree), restoring the tree's bytes if a hook changed one.

Usage: python3 <this> <log>

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


def blob(ref: str) -> bytes:
    return subprocess.run(["git", "cat-file", "blob", ref], cwd=HERE, check=True, capture_output=True).stdout


def main() -> int:
    log = Path(sys.argv[1])
    names = subprocess.run(["git", "diff", "--name-only", BASE, TREE, "--", "util/ad-hoc/"], cwd=HERE, capture_output=True, text=True, check=True).stdout.split()
    for p in names:
        (HERE / p).write_bytes(blob(f"{TREE}:{p}"))
    r = subprocess.run([PRE_COMMIT, "run", "--files", *names], cwd=HERE, capture_output=True, text=True)
    rewritten = []
    for p in names:
        want = blob(f"{TREE}:{p}")
        if (HERE / p).read_bytes() != want:
            rewritten.append(p)
            (HERE / p).write_bytes(want)
    g5 = subprocess.run([sys.executable, "util/home_path_literal_check.py", *names], cwd=HERE, capture_output=True, text=True)
    sha = {p: hashlib.sha256((HERE / p).read_bytes()).hexdigest()[:12] for p in names}
    log.write_text(f"helpers: {names}\npre-commit rc: {r.returncode}\nrewritten: {rewritten}\n{r.stdout}\n{r.stderr}\nG5 rc {g5.returncode}: {g5.stdout}{g5.stderr}\nsha256: {sha}\n")
    print(f"helpers={len(names)} pre-commit rc={r.returncode} rewritten={rewritten} G5 rc={g5.returncode} {g5.stdout.strip().splitlines()[-1:]}")
    for line in r.stdout.splitlines():
        if "Failed" in line:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
