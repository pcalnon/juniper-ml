#!/usr/bin/env python3
"""
Show that the rebuild lost nothing round 1 added, and reverted nothing main gained.

Round 1's carrier changed seven files that already existed. Five of them were not merged in round 2 but
re-derived on main's copies by the wiring tools, so this compares, line by line:

  LOST      every line round 1 ADDED to a file (its unified diff against its base, <scratch>/p_diffs/*.diff) must be
            in the rebuilt file. A line that is not is listed; the expected ones are the lines round 2 re-derives
            (the suite count, the document stamp and its history row, the tally sentence, the CHANGELOG entry's
            reworded lines) and the lines round 2 edited on purpose;
  REVERTED  every line the rebuilt file REMOVES from main's copy must be a line the carrier replaces (it is
            listed, with the count), so a line main gained since round 1's base cannot vanish unseen.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_nothing_lost.py --scratch <dir> [--out <json>]

Always exits 0: it is a report to be read, and its expected rows are named in the build's manifest.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_rebuild.py (which wrote p_diffs/)
"""

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    scratch = Path(args.scratch)
    with open(scratch / "rebuild.json", encoding="utf-8") as fh:
        rows = [row for row in json.load(fh)["rows"] if row["in_base"]]
    report = []
    for row in rows:
        path = row["path"]
        flat = path.replace("/", "__")
        added = [line[1:] for line in (scratch / "p_diffs" / f"{flat}.diff").read_text(encoding="utf-8").splitlines() if line.startswith("+") and not line.startswith("+++")]
        rebuilt = Path(path).read_text(encoding="utf-8").splitlines()
        present = set(rebuilt)
        lost = [line for line in added if line not in present]
        main_text = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout.splitlines()
        removed = [line[1:] for line in difflib.unified_diff(main_text, rebuilt, lineterm="", n=0) if line.startswith("-") and not line.startswith("---")]
        report.append({"path": path, "round1_added_lines": len(added), "not_in_the_rebuilt_file": lost, "removed_from_mains_copy": removed})
        print(f"{path}: round 1 added {len(added)} lines, {len(lost)} not in the rebuilt file; the rebuilt file removes {len(removed)} of main's lines")
        for line in lost:
            print(f"    LOST?     {line[:150]}")
        for line in removed:
            print(f"    REMOVED   {line[:150]}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
