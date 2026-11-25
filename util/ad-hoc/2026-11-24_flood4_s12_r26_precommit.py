#!/usr/bin/env python3
"""Run a repository's pinned pre-commit hooks on one installed ruling-26 set, and prove no file was rewritten (flood-4 session 12).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the fix pass before ruling 26's six PRs land; tmp/flood4/session12/r26/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s12_r26_fixpass.py (the sets); util/ad-hoc/2026-11-24_flood4_s12_r26_reprove.py
    (which leaves each set installed in its clone)

For --clone and --set: checks every file of --set/paths.txt in the clone against --set/final.sha256 (stop on a
mismatch: the clone must hold exactly the set), runs `pre-commit run --files <paths>` in the clone with the
pre-commit on PATH (its version is recorded), then re-checks the sha256s, so a hook that rewrote a file is a failure.
Writes --log (pre-commit's output, its version and the counts). Exit 0 when pre-commit exits 0 and nothing changed.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r26_precommit.py --clone DIR --set DIR --log FILE
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # nosec B404 -- runs pre-commit with a fixed argv
import sys
from pathlib import Path


def _sums(clone: Path, set_dir: Path) -> list[str]:
    bad = []
    for line in (set_dir / "final.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        got = hashlib.sha256((clone / rel.strip()).read_bytes()).hexdigest()
        if got != digest:
            bad.append(f"{rel.strip()}: {got} != {digest}")
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--set", dest="set_dir", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    before = _sums(args.clone, args.set_dir)
    if before:
        print("STOP: the clone does not hold the set:\n  " + "\n  ".join(before))
        return 2
    paths = [line.strip() for line in (args.set_dir / "paths.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    version = subprocess.run(["pre-commit", "--version"], capture_output=True, text=True, check=False).stdout.strip()  # nosec B603 B607
    run = subprocess.run(["pre-commit", "run", "--files", *paths], cwd=args.clone, capture_output=True, text=True, check=False)  # nosec B603 B607
    after = _sums(args.clone, args.set_dir)
    lines = run.stdout.splitlines()
    counts = {word: sum(1 for line in lines if line.rstrip().endswith(word)) for word in ("Passed", "Failed", "Skipped")}
    summary = f"{version}; exit {run.returncode}; {len(paths)} files; hooks {counts}; rewritten: {after or 'none'}"
    args.log.write_text(f"{summary}\n\n{run.stdout}\n--- stderr ---\n{run.stderr}", encoding="utf-8")
    print(summary)
    for line in lines:
        if line.rstrip().endswith("Failed") or "files were modified" in line:
            print("  " + line)
    return 0 if run.returncode == 0 and not after else 1


if __name__ == "__main__":
    sys.exit(main())
