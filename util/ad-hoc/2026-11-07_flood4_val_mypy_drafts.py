"""
Flood-4 validation: run the PINNED mypy hook on the DRAFTS' own versions of the two files the carrier says
it fixed for mypy (#2455's tests/test_release_train_exact_caps.py, #2407's tests/test_claude_interactive.py),
then on the carrier's versions, restoring the carrier's bytes afterwards (sha-checked).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation; juniper-ml#2455, #2407
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"
CASES = [(2455, "tests/test_release_train_exact_caps.py"), (2407, "tests/test_claude_interactive.py"), (2403, "tests/test_wake_the_claude.py")]


def blob(ref: str) -> bytes:
    return subprocess.run(["git", "cat-file", "blob", ref], cwd=HERE, check=True, capture_output=True).stdout


def mypy(paths: list[str]) -> str:
    r = subprocess.run([PRE_COMMIT, "run", "mypy", "--files", *paths], cwd=HERE, capture_output=True, text=True)
    return f"rc={r.returncode}\n{r.stdout}{r.stderr}"


def main() -> int:
    log = Path(sys.argv[1])
    out = []
    try:
        for n, p in CASES:
            (HERE / p).write_bytes(blob(f"refs/flood4/pr/{n}:{p}"))
        out.append("== DRAFT heads ==\n" + mypy([p for _, p in CASES]))
    finally:
        for _, p in CASES:
            (HERE / p).write_bytes(blob(f"{TREE}:{p}"))
    ok = all((HERE / p).read_bytes() == blob(f"{TREE}:{p}") for _, p in CASES)
    out.append(f"carrier bytes restored: {ok}")
    out.append("== CARRIER ==\n" + mypy([p for _, p in CASES]))
    log.write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
