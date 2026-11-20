#!/usr/bin/env python3
"""
Show that a landing of the flood-4 "ml-tests" carrier reverted nothing main gained since the carrier's base.

Run it from the root of the landing worktree (HEAD = the main the carrier was landed on, the landing uncommitted).
For every path of the carrier's manifest that main's HEAD holds, two line sets are read:

  GAINED    the lines main ADDED to the path between the carrier's base and HEAD (other pull requests' work, which
            the landing must keep). Each must still be a line of the landed file; one that is not is classified.
  REMOVED   the lines the landing removes from HEAD's copy. Each is classified too.

A line that is not kept verbatim is one of:
  superset       a line of the landed file holds it in order with text only inserted (a sentence that gained a
                 clause; difflib finds no deletion or replacement in it);
  re-derived     the landed file holds a line equal to it but for its digits (a count, a version, a date);
  carrier edit   (REMOVED only) a line the carrier's own tree also removes from its base: an edit the carrier makes
                 on purpose, the same on every main, never a line another pull request gave main;
  NOT ACCOUNTED  anything else: the landing lost it.

Usage (from the landing worktree's root):
    python3 <carrier>/util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_reverts.py --base <sha> --manifest <manifest.json> --carrier <carrier worktree> --out <json>

Exit 0 when every gained and every removed line is kept, a superset or re-derived; 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, its session-8 fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_land.py (the landing it checks)
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

DIGITS = re.compile(r"\d+")


def _git(*argv: str, cwd: str = ".") -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], capture_output=True, text=True, check=False, cwd=cwd)


def _diff_lines(*argv: str, cwd: str = ".") -> tuple:
    added, removed = [], []
    for line in _git("diff", "--no-color", "-U0", *argv, cwd=cwd).stdout.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    return added, removed


def _superset(line: str, candidates: list) -> bool:
    for candidate in candidates:
        if len(candidate) <= len(line):
            continue
        opcodes = difflib.SequenceMatcher(None, line, candidate, autojunk=False).get_opcodes()
        if all(tag in ("equal", "insert") for tag, *_ in opcodes):
            return True
    return False


def _classify(line: str, landed: set, landed_list: list) -> str:
    if line in landed:
        return "kept"
    if _superset(line, landed_list):
        return "superset"
    shape = DIGITS.sub("#", line)
    if line.strip() and any(DIGITS.sub("#", other) == shape for other in landed_list):
        return "re-derived"
    return "NOT ACCOUNTED"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--carrier", required=True, help="the carrier worktree; its own removals on its base are read there")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    paths = [row["path"] for row in json.loads(Path(args.manifest).read_text(encoding="utf-8"))["files"]]
    rows, bad = [], 0
    for path in paths:
        if _git("cat-file", "-e", f"HEAD:{path}").returncode != 0:
            continue
        landed_list = Path(path).read_text(encoding="utf-8").splitlines()
        landed = set(landed_list)
        gained, _gone = _diff_lines(args.base, "HEAD", "--", path)
        _added, removed = _diff_lines("HEAD", "--", path)
        _own_added, own_removed = _diff_lines(args.base, "--", path, cwd=args.carrier)
        row = {"path": path, "gained_by_main": len(gained), "removed_by_landing": len(removed), "not_verbatim": []}
        for kind, lines in (("gained", gained), ("removed", removed)):
            for line in lines:
                verdict = _classify(line, landed, landed_list)
                if verdict == "NOT ACCOUNTED" and kind == "removed" and line in own_removed:
                    verdict = "carrier edit"
                if verdict != "kept":
                    row["not_verbatim"].append({"set": kind, "verdict": verdict, "line": line[:240]})
                    bad += verdict == "NOT ACCOUNTED"
        rows.append(row)
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['path']}: main gained {row['gained_by_main']}, the landing removes {row['removed_by_landing']}")
        for item in row["not_verbatim"]:
            print(f"    {item['set']:<8} {item['verdict']:<14} {item['line'][:150]}")
    print("NOT ACCOUNTED: " + str(bad) if bad else "every gained and removed line is kept, a superset, re-derived or the carrier's own edit")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
