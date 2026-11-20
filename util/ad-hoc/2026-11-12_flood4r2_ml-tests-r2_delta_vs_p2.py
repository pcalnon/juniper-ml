#!/usr/bin/env python3
"""
Compare what this rebuilt "ml-tests" carrier changes on its base with what the predecessor tree changed on its own.

The carrier was rebuilt on a newer main from a predecessor's uncommitted tree (read-only to this session). For a
file main did not change in between, the rebuilt file must be the predecessor's, byte for byte. For a file main
did change (the shared documents), the rebuilt file is re-derived by the tools on the new main, so its bytes
differ; what must not differ is the CHANGE: the lines this carrier adds to and removes from its base must be the
lines the predecessor added to and removed from its base, except where a value is derived from main (the document
version and its history row).

For every path of the predecessor's record:
  * sha256 of this tree's file against the predecessor's;
  * when they differ: the zero-context line delta of each side against its own base (`diff -U0 --no-index` of the
    base commit's blob, read from THIS checkout's object store, against the file), compared as multisets. Lines
    only one side adds or removes are listed.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_delta_vs_p2.py --predecessor <abs dir>
        --predecessor-base <sha> --record <its copy_tree_final_bytes.json> --out <json> [--allow REGEX ...]
        [--changed-on-purpose PATH ...]

--allow names a pattern a differing line may match (a stamp derived from main). --changed-on-purpose names a file
this session changed deliberately (a helper): it is reported as differing and its lines are not judged. Exit 0
when every other differing line matches an allowed pattern; 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, the finish of round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_nothing_lost.py (the same question, asked of round 1's tree)
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def _git_bytes(*argv: str) -> bytes:
    return subprocess.run(["git", *argv], capture_output=True, check=False).stdout


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _delta(base_blob: bytes, current: Path, work: Path, tag: str) -> tuple:
    """(added, removed) line multisets of `current` against `base_blob`."""
    base_file = work / f"{tag}.base"
    base_file.write_bytes(base_blob)
    done = subprocess.run(["git", "diff", "-U0", "--no-index", "--no-color", str(base_file), str(current)], capture_output=True, check=False)
    added, removed = Counter(), Counter()
    for raw in done.stdout.decode("utf-8", errors="replace").splitlines():
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            added[raw[1:]] += 1
        elif raw.startswith("-"):
            removed[raw[1:]] += 1
    return added, removed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--predecessor", required=True, type=Path)
    ap.add_argument("--predecessor-base", required=True)
    ap.add_argument("--record", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--changed-on-purpose", action="append", default=[], help="a path this session changed deliberately: reported as differing, its lines not judged")
    args = ap.parse_args()
    allowed = [re.compile(pattern) for pattern in args.allow]
    with open(args.record, encoding="utf-8") as fh:
        record = {row["path"]: row["here"] for row in json.load(fh)["rows"]}
    work = args.out.parent / "delta_vs_p2_work"
    work.mkdir(parents=True, exist_ok=True)
    rows, unexplained = [], []
    for path, theirs_sha in sorted(record.items()):
        mine, theirs = Path(path), args.predecessor / path
        mine_sha = _sha256(mine)
        row = {"path": path, "sha256_here": mine_sha, "sha256_predecessor": theirs_sha, "identical": mine_sha == theirs_sha}
        if not row["identical"] and path in args.changed_on_purpose:
            row["changed_on_purpose"] = True
        elif not row["identical"]:
            flat = path.replace("/", "__")
            mine_added, mine_removed = _delta(_git_bytes("show", f"HEAD:{path}"), mine, work, flat + ".here")
            their_added, their_removed = _delta(_git_bytes("show", f"{args.predecessor_base}:{path}"), theirs, work, flat + ".predecessor")
            differing = {
                "added_only_here": sorted((mine_added - their_added).elements()),
                "added_only_by_the_predecessor": sorted((their_added - mine_added).elements()),
                "removed_only_here": sorted((mine_removed - their_removed).elements()),
                "removed_only_by_the_predecessor": sorted((their_removed - mine_removed).elements()),
            }
            row["lines_added_here"] = sum(mine_added.values())
            row["lines_removed_here"] = sum(mine_removed.values())
            row["lines_added_by_the_predecessor"] = sum(their_added.values())
            row["lines_removed_by_the_predecessor"] = sum(their_removed.values())
            row["differing"] = differing
            for side, lines in differing.items():
                for line in lines:
                    if not any(pattern.search(line) for pattern in allowed):
                        unexplained.append(f"{path}: {side}: {line[:160]}")
        rows.append(row)
    report = {"predecessor": str(args.predecessor), "predecessor_base": args.predecessor_base, "allowed_patterns": args.allow, "paths": len(rows), "identical": sum(1 for row in rows if row["identical"]), "unexplained": unexplained, "rows": rows}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(f"{len(rows)} recorded paths; byte-identical to the predecessor's: {report['identical']}")
    for row in rows:
        if row.get("changed_on_purpose"):
            print(f"DIFFERS {row['path']}: changed on purpose in this session (not judged line by line)")
        elif not row["identical"]:
            print(f"DIFFERS {row['path']}: here +{row['lines_added_here']}/-{row['lines_removed_here']} lines on its base, the predecessor +{row['lines_added_by_the_predecessor']}/-{row['lines_removed_by_the_predecessor']} on its own")
            for side, lines in row["differing"].items():
                for line in lines:
                    print(f"    {side}: {line[:200]}")
    print("VERDICT:", "every differing line is a value derived from main" if not unexplained else f"{len(unexplained)} UNEXPLAINED differing line(s)")
    return 0 if not unexplained else 1


if __name__ == "__main__":
    sys.exit(main())
