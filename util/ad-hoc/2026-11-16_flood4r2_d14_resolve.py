"""
Resolve the conflict hunks a three-way rebuild of the D-14 juniper-ml carrier leaves in docs/REFERENCE.md and
docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: keep main's lines, then add the carrier's own.

- REFERENCE "Running every suite": main's sentence, with the carrier's clause (the drift gate's suite, numbered one
  past main's highest count, dated ``--date``) inserted before ". The drift script above counts".
- REFERENCE Version History: main's row(s), then the carrier's row, renumbered to main's highest version + 1, dated
  ``--date``, its suite count set to ``--count``.
- Every other hunk (the stamp lines of both documents): main's side. The stamps helper then bumps the versions.

Each hunk must have the shape this script expects (it asserts and exits 1 otherwise), so a rebuild onto a main that
moved differently is stopped, not resolved blindly.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_resolve.py --root <juniper-ml carrier> --date YYYY-MM-DD --count N

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import re
import sys
from pathlib import Path

REFERENCE = "docs/REFERENCE.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
GATE = "`tests/test_ws_resume_answer_table_drift.py`"
ROW_RE = re.compile(r"^\| (\d+)\.(\d+)\.(\d+) +\| (\d{4}-\d{2}-\d{2}) \|")


def hunks(lines: list[str]) -> list[tuple[int, int, int]]:
    """(start, middle, end) line indexes of each conflict block."""
    found = []
    start = middle = None
    for index, line in enumerate(lines):
        if line.startswith("<<<<<<< "):
            start, middle = index, None
        elif line.startswith("=======") and start is not None:
            middle = index
        elif line.startswith(">>>>>>> ") and start is not None and middle is not None:
            found.append((start, middle, index))
            start = middle = None
    return found


def resolve_reference(lines: list[str], date: str, count: int) -> list[str]:
    blocks = hunks(lines)
    if len(blocks) != 3:
        raise SystemExit(f"{REFERENCE}: expected 3 conflict hunks, found {len(blocks)}")
    out: list[str] = []
    cursor = 0
    for start, middle, end in blocks:
        out.extend(lines[cursor:start])
        carrier, main = lines[start + 1 : middle], lines[middle + 1 : end]
        if len(carrier) == 1 and len(main) == 1 and carrier[0].startswith("The complete ordered list"):
            sentence = main[0]
            if GATE in sentence or sentence.count(". The drift script above counts") != 1:
                raise SystemExit(f"{REFERENCE}: unexpected 'Running every suite' sentence on main")
            clause = f", **{count}** on {date} with the shared resume table's drift gate, {GATE}"
            out.append(sentence.replace(". The drift script above counts", clause + ". The drift script above counts"))
        elif all(ROW_RE.match(row) for row in carrier + main) and len(carrier) == 1:
            highest = max((tuple(int(part) for part in ROW_RE.match(row).groups()[:3]) for row in main))
            renumbered = f"{highest[0]}.{highest[1]}.{highest[2] + 1}"
            row = ROW_RE.sub(lambda match: f"| {renumbered}  | {date} |", carrier[0], count=1)
            row, swaps = re.subn(r"\(\*\*\d+\*\*\)\. \|\n$", f"(**{count}**). |\n", row)
            if swaps != 1:
                raise SystemExit(f"{REFERENCE}: the carrier's history row does not end with its suite count")
            out.extend(main)
            out.append(row)
        elif len(carrier) == 1 and len(main) == 1 and carrier[0].startswith("**Last Updated:**") and main[0].startswith("**Last Updated:**"):
            out.extend(main)
        else:
            raise SystemExit(f"{REFERENCE}: unexpected hunk at line {start + 1}")
        cursor = end + 1
    out.extend(lines[cursor:])
    return out


def resolve_cheatsheet(lines: list[str]) -> list[str]:
    blocks = hunks(lines)
    if len(blocks) != 2:
        raise SystemExit(f"{CHEATSHEET}: expected 2 conflict hunks, found {len(blocks)}")
    out: list[str] = []
    cursor = 0
    for start, middle, end in blocks:
        carrier, main = lines[start + 1 : middle], lines[middle + 1 : end]
        stamp_lines = ("**Version", "**Date", "**Last Updated")
        if not (carrier and main and all(line.startswith(stamp_lines) for line in carrier + main)):
            raise SystemExit(f"{CHEATSHEET}: unexpected hunk at line {start + 1}")
        out.extend(lines[cursor:start])
        out.extend(main)
        cursor = end + 1
    out.extend(lines[cursor:])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--count", required=True, type=int)
    args = parser.parse_args()

    reference = args.root / REFERENCE
    cheatsheet = args.root / CHEATSHEET
    resolved_reference = resolve_reference(reference.read_text(encoding="utf-8").splitlines(keepends=True), args.date, args.count)
    resolved_cheatsheet = resolve_cheatsheet(cheatsheet.read_text(encoding="utf-8").splitlines(keepends=True))
    for path, lines in ((reference, resolved_reference), (cheatsheet, resolved_cheatsheet)):
        if hunks(lines):
            raise SystemExit(f"{path}: conflict markers remain")
        path.write_text("".join(lines), encoding="utf-8")
        print(f"resolved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
