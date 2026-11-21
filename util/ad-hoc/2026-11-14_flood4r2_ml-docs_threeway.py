#!/usr/bin/env python3
"""
Three-way a dead builder's docs carrier onto today's main: extract the base and main copies, diff, merge, report.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)

For every path given, with ``--carrier`` holding the carrier's copies (the predecessor's bytes, snapshotted):

* ``git show <base>:<path>`` and ``git show <main>:<path>`` into ``--scratch``/base and ``--scratch``/main;
* ``diff -u`` base -> carrier (the carrier's own hunks) and base -> main (what main gained since);
* ``git merge-file -p <carrier> <base> <main>`` into ``--scratch``/merged/<path>, with the conflict count.

It never writes into a checkout; the merged copies are inputs for a person to resolve. Run from the worktree root.

Usage: 2026-11-14_flood4r2_ml-docs_threeway.py --base <ref> --main <ref> --carrier <dir> --scratch <dir> <path> ...
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def show(ref: str, path: str, dest: Path) -> None:
    """Write ``ref:path`` to ``dest`` (bytes exactly as git stores them)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = subprocess.run(["git", "show", f"{ref}:{path}"], check=True, capture_output=True).stdout
    dest.write_bytes(data)


def unified(old: Path, new: Path, dest: Path) -> int:
    """``diff -u old new`` into ``dest``; return the number of changed lines (+/- excluding headers)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["diff", "-u", str(old), str(new)], capture_output=True, text=True, encoding="utf-8")
    dest.write_text(result.stdout, encoding="utf-8")
    return sum(1 for line in result.stdout.splitlines() if line[:1] in "+-" and not line.startswith(("+++", "---")))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--base", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)

    report = {"base": args.base, "main": args.main, "carrier": str(args.carrier), "files": []}
    for path in args.paths:
        base_copy = args.scratch / "base" / path
        main_copy = args.scratch / "main" / path
        merged = args.scratch / "merged" / path
        show(args.base, path, base_copy)
        show(args.main, path, main_copy)
        carrier_copy = args.carrier / path
        own = unified(base_copy, carrier_copy, args.scratch / "diffs" / f"own__{path.replace('/', '__')}.diff")
        gained = unified(base_copy, main_copy, args.scratch / "diffs" / f"main__{path.replace('/', '__')}.diff")
        merged.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(carrier_copy), str(base_copy), str(main_copy)],
            capture_output=True,
        )
        merged.write_bytes(result.stdout)
        conflicts = result.returncode if result.returncode > 0 else 0
        row = {"path": path, "own_changed_lines": own, "main_changed_lines": gained, "merge_exit": result.returncode, "conflicts": conflicts}
        report["files"].append(row)
        print(f"{path}: own {own} lines, main gained {gained} lines, merge-file exit {result.returncode}")
    (args.scratch / "threeway_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
