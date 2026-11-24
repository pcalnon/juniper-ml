"""
Print the removed lines a tree_status result recorded, and for each the closest added line of the same diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --status <tree_status json> --diff-dir <dir of unified diffs> [--width 260]
"""

import argparse
import difflib
import json
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--status", required=True)
    parser.add_argument("--diff-dir", required=True)
    parser.add_argument("--width", type=int, default=260)
    args = parser.parse_args(argv)
    with open(args.status, encoding="utf-8") as fh:
        status = json.load(fh)
    for path, row in sorted(status["removed_lines"].items()):
        removed = row["removed"]
        print("== %s: %d removed, %d added" % (path, len(removed), row["added_count"]))
        diff_file = Path(args.diff_dir) / (path.replace("/", "__") + ".diff")
        added = [line[1:] for line in diff_file.read_text(encoding="utf-8").splitlines() if line.startswith("+") and not line.startswith("+++")]
        for line in removed:
            print("  - " + line[: args.width])
            close = difflib.get_close_matches(line, added, n=1, cutoff=0.3)
            if close:
                print("  + " + close[0][: args.width])
                differ = [op for op in difflib.SequenceMatcher(None, line, close[0]).get_opcodes() if op[0] != "equal"]
                for tag, i1, i2, j1, j2 in differ[:6]:
                    print("      %s: %r -> %r" % (tag, line[i1:i2][:120], close[0][j1:j2][:120]))
            else:
                print("  (no close added line)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
