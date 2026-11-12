"""
Intersect a coverage term-missing report with the lines a change adds: is any added line missed, or a partial branch's source?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge)

Usage: python3 <this> <coverage report log> <base sha> FILE [FILE ...]

FILE is repo-relative in the N-1 worktree. The added lines are the ``+`` side of
``git diff -U0 <base> -- FILE`` (base -> working tree). From the report's row for FILE, a bare
number or ``a-b`` range is a missed line; ``a->b`` is a partial branch whose source is line a.
Prints, per file, the added-line count, the missed lines and partial-branch sources among them.
Exit 1 when any added line is missed or is a partial branch's source.
"""

import re
import subprocess  # nosec B404 -- fixed-argv git diff
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def added_lines(base: str, rel: str) -> set:
    diff = subprocess.run(["git", "-C", str(TREE), "diff", "-U0", "--no-color", base, "--", rel], check=True, capture_output=True, text=True).stdout  # nosec B603 B607
    lines = set()
    for line in diff.splitlines():
        match = HUNK.match(line)
        if match:
            start, count = int(match.group(1)), int(match.group(2) or "1")
            lines.update(range(start, start + count))
    return lines


def report_row(report: str, rel: str) -> tuple:
    for line in report.splitlines():
        if line.startswith(f"src/{rel.split('src/', 1)[-1]} ") or line.startswith(f"{rel} "):
            missing_text = line.split("%", 1)[1].strip() if "%" in line else ""
            missed, partial = set(), set()
            for item in filter(None, (part.strip() for part in missing_text.split(","))):
                if "->" in item:
                    partial.add(int(item.split("->", 1)[0]))
                elif "-" in item:
                    low, high = item.split("-", 1)
                    missed.update(range(int(low), int(high) + 1))
                else:
                    missed.add(int(item))
            return missed, partial, line[:120]
    raise SystemExit(f"no row for {rel} in the report")


def main() -> int:
    report_path, base, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    with open(report_path, encoding="utf-8") as fh:
        report = fh.read()
    bad = 0
    for rel in files:
        added = added_lines(base, rel)
        missed, partial, row = report_row(report, rel)
        hit_missed, hit_partial = sorted(added & missed), sorted(added & partial)
        bad += len(hit_missed) + len(hit_partial)
        print(f"{rel}: {len(added)} added lines; missed among them {hit_missed}; partial-branch sources among them {hit_partial}")
        print(f"  report row: {row}")
    print(f"{'FAIL' if bad else 'PASS'}: {bad} added line(s) missed or partial")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
