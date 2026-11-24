"""
Run the repo-pinned pre-commit on named files in the validator's own juniper-canopy copy, and report whether a hook rewrote any.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

The same wrapper runs any other command from the copy's root (`--` then the command) with a log file, so that a
tool with no change-directory flag can be run without a `cd` in the session shell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--files", nargs="*", default=[], help="repo-relative files to hash before and after")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if "--val--" not in args.copy.name:
        raise SystemExit("refusing: --copy is not a validator worktree")
    command = [part for part in args.command if part != "--"] or ["/opt/miniforge3/bin/pre-commit", "run", "--files", *args.files]
    before = {name: _sha(args.copy / name) for name in args.files}
    proc = subprocess.run(command, cwd=args.copy, capture_output=True, text=True, check=False, timeout=1800)
    after = {name: _sha(args.copy / name) for name in args.files}
    with open(args.log, "w", encoding="utf-8") as fh:
        fh.write(proc.stdout)
        fh.write("\n--- stderr ---\n")
        fh.write(proc.stderr)
    print(proc.stdout[-6000:])
    if proc.stderr.strip():
        print("--- stderr ---")
        print(proc.stderr[-3000:])
    print(json.dumps({"command": command, "exit": proc.returncode, "rewritten": sorted(name for name in args.files if before[name] != after[name]), "sha256": after}, indent=2))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
