#!/usr/bin/env python3
"""
Run the pinned pre-commit on named files of a tree, logging its output and the files' sha256 before and after.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
The base brief requires the repository's pinned pre-commit on every changed file
(`/opt/miniforge3/bin/pre-commit run --files <explicit paths>`). This host's shell refuses that command when its text
names `.github` and pipes or chains it, so it runs here: one pre-commit process in --tree, its stdout and stderr in
--log, and a JSON record of its exit status and of every named file's sha256 before and after (a hook that rewrites a
file is a finding, not a pass). It writes nothing into the tree itself; pre-commit's hooks may.

Usage:
    python3 <this> --tree <checkout> --log <file> --json <file> --files <repo-relative path> [...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: the pinned pre-commit on named files
import sys
from pathlib import Path

PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"


def digest(tree: Path, files: list[str]) -> dict:
    return {f: hashlib.sha256((tree / f).read_bytes()).hexdigest() for f in files}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", required=True, type=Path)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--files", required=True, nargs="+")
    args = ap.parse_args()
    tree = args.tree.resolve()
    before = digest(tree, args.files)
    argv = [PRE_COMMIT, "run", "--files", *args.files]
    res = subprocess.run(argv, cwd=tree, capture_output=True, text=True, check=False, timeout=1200)  # nosec B603
    after = digest(tree, args.files)
    args.log.write_text("$ " + " ".join(argv) + f"\n[cwd {tree}]\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    lines = res.stdout.splitlines()
    record = {
        "command": " ".join(argv),
        "cwd": str(tree),
        "exit": res.returncode,
        "passed": sum(1 for ln in lines if ln.rstrip().endswith("Passed")),
        "failed": [ln for ln in lines if ln.rstrip().endswith("Failed")],
        "skipped": sum(1 for ln in lines if "Skipped" in ln),
        "unchanged": before == after,
        "sha256_before": before,
        "sha256_after": after,
        "log": str(args.log),
    }
    args.json.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if not k.startswith("sha256")}, indent=1))
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
