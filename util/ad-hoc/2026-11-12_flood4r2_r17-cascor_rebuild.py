#!/usr/bin/env python3
"""
Three-way a carrier's saved files onto a newer base and write the results into its tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt ("A carrier built on an older base: for every
         file that main changed since the carrier's base, rebuild it three-way ... never copy the
         carrier's copy over main's")

For every ``--file`` it takes the carrier's copy from ``--ours`` (a directory holding the files at
their repository paths, saved before the tree was moved), the old base's and the new base's blobs
from ``git show``, and runs ``git merge-file -p <ours> <old base> <new base>`` on copies under
``--work``. With ``--write`` the merged bytes go into the tree. It reads and writes working files
only: no index, HEAD or ref is touched. A file the new base did not change is reported as such
and, with ``--write``, the carrier's own bytes are written back unchanged.

The merge can be clean and still wrong where both sides wrote the same line for two different
reasons (a version stamp both bumped from the same value): the report prints, for each file,
every line on which ours and the new base agree while both differ from the old base, so those
lines can be re-derived by hand.

Usage:
  2026-11-12_flood4r2_r17-cascor_rebuild.py --tree <carrier> --ours <dir> --old-base <sha> --new-base <sha> --work <dir> --out <json> [--write] --file <path> [--file ...]
Exit: 0 when no file has a conflict; 1 otherwise (nothing is written for a conflicted file).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 -- fixed-argv git reads and merge-file runs
import sys
from pathlib import Path


def _blob(tree: Path, ref: str, path: str) -> bytes | None:
    proc = subprocess.run(["git", "-C", str(tree), "show", f"{ref}:{path}"], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv
    return proc.stdout if proc.returncode == 0 else None


def _same_change_lines(ours: bytes, base: bytes, theirs: bytes) -> list:
    """Lines present in ours and in theirs but not in the old base: the same text added on both sides."""
    base_lines = set(base.decode("utf-8", errors="replace").splitlines())
    their_lines = set(theirs.decode("utf-8", errors="replace").splitlines())
    shared = []
    for number, line in enumerate(ours.decode("utf-8", errors="replace").splitlines(), start=1):
        if line.strip() and line not in base_lines and line in their_lines:
            shared.append({"line_in_ours": number, "text": line[:160]})
    return shared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--ours", required=True, type=Path, help="directory holding the carrier's saved copies")
    parser.add_argument("--old-base", required=True)
    parser.add_argument("--new-base", required=True)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--file", action="append", required=True)
    args = parser.parse_args()
    tree = args.tree.resolve()
    work = args.work.resolve()
    report = []
    clean = True
    for path in args.file:
        ours = (args.ours / path).read_bytes()
        base, theirs = _blob(tree, args.old_base, path), _blob(tree, args.new_base, path)
        entry = {"path": path, "ours_sha256": hashlib.sha256(ours).hexdigest(), "new_base_changed_it": base != theirs}
        if base is None or theirs is None:
            entry["three_way"] = "not applicable: the file is not on both bases"
            merged, conflicts = ours, 0
        elif base == theirs:
            entry["three_way"] = "not needed: the new base did not change the file"
            merged, conflicts = ours, 0
        else:
            spot = work / path.replace("/", "__")
            spot.mkdir(parents=True, exist_ok=True)
            for label, data in (("ours", ours), ("base", base), ("theirs", theirs)):
                (spot / label).write_bytes(data)
            proc = subprocess.run(["git", "merge-file", "-p", str(spot / "ours"), str(spot / "base"), str(spot / "theirs")], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv
            merged, conflicts = proc.stdout, proc.returncode
            (spot / "merged").write_bytes(merged)
            entry["three_way"] = {"conflicts": conflicts, "merged_copy": str(spot / "merged")}
            entry["same_text_added_on_both_sides"] = _same_change_lines(ours, base, theirs)
        entry["merged_sha256"] = hashlib.sha256(merged).hexdigest()
        if conflicts != 0:
            clean = False
            entry["written"] = False
        elif args.write:
            (tree / path).write_bytes(merged)
            entry["written"] = True
        report.append(entry)
        print(f"{path}: new base changed it: {entry['new_base_changed_it']}; three-way: {entry['three_way'] if isinstance(entry['three_way'], str) else entry['three_way']['conflicts']}; same text on both sides: {len(entry.get('same_text_added_on_both_sides', []))} line(s); written: {entry.get('written', False)}")
        for same in entry.get("same_text_added_on_both_sides", []):
            print(f"    SAME ON BOTH SIDES (re-derive by hand if it is a stamp): ours line {same['line_in_ours']}: {same['text']}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"tree": str(tree), "old_base": args.old_base, "new_base": args.new_base, "files": report}, indent=2) + "\n", encoding="utf-8")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
