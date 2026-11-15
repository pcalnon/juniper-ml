#!/usr/bin/env python3
"""Run the ml-propose carrier's tests against an OLDER propose.py (main's, or the carrier's first build) and restore.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (the Cursor flood-4 round-2 "ml-propose" carrier, second build after validation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2507; owner ruling "Carry + extend propose.py"; the round-2 validators' findings
         (claims lens F2-F4, code lens F1, F2, F5, F7); util/ad-hoc/2026-11-08_flood4r2_ml-propose_mutation_check.py

A fix's tests must fail on the code it fixes. This swaps ``--old`` in for ``<worktree>/util/release_train/propose.py``
(a whole-file "mutant"), deletes the ``__pycache__`` next to it and next to the tests, runs the named unittest
selectors in a fresh process, and restores the file byte for byte (sha256 compared; a mismatch exits 3). It prints
and records which selected tests fail. The selection is passed as ``--test`` arguments (dotted unittest names).

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_ml-propose_r2_tests_vs_old_code.py --worktree <carrier root> \\
        --old <older propose.py> --log <file> --test tests.test_release_train_propose.SomeTest.test_x [--test ...]

Exit codes: 0 when the run completed and the file was restored (read the log for the failures), 2 on an invocation
error, 3 when the restore check fails.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for cache in (root / "util" / "release_train" / "__pycache__", root / "tests" / "__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--old", required=True, help="the older propose.py to swap in")
    ap.add_argument("--log", required=True)
    ap.add_argument("--test", action="append", required=True, help="a dotted unittest selector (repeatable)")
    args = ap.parse_args(argv)
    root = Path(args.worktree).resolve()
    target = root / "util" / "release_train" / "propose.py"
    old = Path(args.old).resolve()
    if not target.is_file() or not old.is_file():
        print("ERROR: --worktree has no util/release_train/propose.py, or --old is missing", file=sys.stderr)
        return 2
    original = target.read_bytes()
    before = _sha(target)
    argv_run = [sys.executable, "-B", "-m", "unittest", "-v", *args.test]
    try:
        target.write_bytes(old.read_bytes())
        _clear_pycache(root)
        proc = subprocess.run(argv_run, cwd=root, capture_output=True, text=True, check=False, timeout=900)  # nosec B603 - fixed argv
    finally:
        target.write_bytes(original)
        _clear_pycache(root)
    after = _sha(target)
    out = proc.stderr or ""
    failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+) \(", out, re.MULTILINE)))
    summary = [ln for ln in out.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    with open(args.log, "w", encoding="utf-8") as fh:
        fh.write(f"# {' '.join(argv_run)}\n# with propose.py = {old} (sha256 {_sha(old)})\n# rc={proc.returncode}\n")
        fh.write(f"# restored: sha256 {before} -> {after} ({'identical' if before == after else 'MISMATCH'})\n")
        fh.write(f"# failing tests ({len(failing)}): {failing}\n\n{out}\n")
    print(f"rc={proc.returncode} {' / '.join(summary)} failing={len(failing)} restored={'yes' if before == after else 'NO'}")
    for name in failing:
        print(f"  {name}")
    return 0 if before == after else 3


if __name__ == "__main__":
    sys.exit(main())
