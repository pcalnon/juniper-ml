#!/usr/bin/env python3
"""
Audit the defect register's primer line anchors for the three-line shift juniper-ml#1098 introduced.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- read-only audit; the round-42 fix-forward applies what it finds
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The register (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`) cites the API primer by
bare line number in each section-4 row's `Primer` column. It was created at `adbe92b0` (juniper-ml#1092,
2026-08-14 05:10 CDT) against the primer as of `68f62f5b`. Ten hours later juniper-ml#1098 (`f7b89745`)
inserted three lines at primer line 5758, and it is the ONLY commit to touch the primer since. So an
anchor past 5758 that a row has carried unchanged since creation now points three lines early -- onto
a blank line, or the neighbouring question.

This proves each shift by content instead of assuming it: for every such anchor N it checks that line
N of the creation-time primer is line N+3 of the current one. Anchors a row gained after creation were
taken against the shifted primer and are left alone. It prints one line per anchor past 5758 and, with
`--json`, the proposed cell rewrites.

Usage: python3 util/ad-hoc/2026-09-24_register_primer_anchor_audit.py [--ref REF] [--json]
  --ref  the commit whose register and primer to audit (default origin/main)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess

PRIMER = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
REGISTER = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
CREATED = "adbe92b0"  # the register's first commit (#1092)
PRE_SHIFT = "68f62f5b"  # the primer the creation-time anchors were taken against
SHIFT_AT, SHIFT = 5758, 3  # juniper-ml#1098 (f7b89745) inserted three lines at 5758
# An anchor that was already wrong at creation: (row, anchor) -> the creation-time line it meant, which
# is then shifted and content-checked like the rest. APD-DCLIENT-008's 6592 was the blank line after the
# `create_dataset` signature's code fence; its finding ("9 positional-or-keyword params, 3rd a bare
# boolean") is the paragraph at 6593 ("... all nine are positional-or-keyword ... the boolean trap").
MEANT = {("APD-DCLIENT-008", 6592): 6593}
ID_RE = re.compile(r"APD-[A-Z]+-\d{3}[ab]?")
NUM_RE = re.compile(r"\b\d{4,5}\b")


def show(ref: str, path: str) -> list[str]:
    return subprocess.run(["git", "show", f"{ref}:{path}"], check=True, capture_output=True, text=True).stdout.split("\n")


def cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line)
    return [p.strip() for p in parts[1:-1]]


def primer_cells(lines: list[str]) -> dict[str, tuple[int, str]]:
    """Map each section-4 row id to (1-based line number, its Primer cell)."""
    out: dict[str, tuple[int, str]] = {}
    col = None
    for n, line in enumerate(lines, 1):
        if not line.startswith("|"):
            col = None if not line.strip() else col
            continue
        row = cells(line)
        if row and row[0] == "ID":
            col = row.index("Primer") if "Primer" in row else None
            continue
        if col is None or set(line) <= set("|-: "):
            continue
        ident = ID_RE.search(row[0]) if row else None
        if ident and col < len(row):
            out.setdefault(ident.group(0), (n, row[col]))
    return out


def audit(register: list[str], primer: list[str], verbose: bool = True) -> tuple[list[dict], int, int]:
    """Return (cell rewrites, anchors shifted, anchors failing the content check) for `register`'s
    section-4 rows, judged against the current `primer`. The round-42 fix-forward imports this."""
    before = show(PRE_SHIFT, PRIMER)
    created, current = primer_cells(show(CREATED, REGISTER)), primer_cells(register)
    rewrites, moved, bad = [], 0, 0
    say = print if verbose else (lambda *a, **k: None)
    now = primer
    for ident, (n, cell) in current.items():
        born = set(NUM_RE.findall(created.get(ident, (0, ""))[1]))
        nums = [int(x) for x in NUM_RE.findall(cell) if int(x) > SHIFT_AT]
        if not nums:
            continue
        shifted: dict[str, str] = {}
        for num in nums:
            if str(num) not in born:
                say(f"  keep   {ident:16} :{n:<5} {num}: added after creation")
                continue
            meant = MEANT.get((ident, num), num)
            ok = before[meant - 1] == now[meant - 1 + SHIFT] and before[meant - 1].strip() != ""
            blank = now[num - 1].strip() == ""
            bad += not ok
            moved += ok
            note = f" (meant {meant} at creation)" if meant != num else ""
            say(f"  {'shift ' if ok else 'FAIL  '} {ident:16} :{n:<5} {num} -> {meant + SHIFT}{note}  (now {'BLANK' if blank else 'text '} at {num}) {before[meant - 1].strip()[:70]!r}")
            shifted[str(num)] = str(meant + SHIFT)
        # One simultaneous pass: a cell can hold both N and N+3 (a range), and shifting them one at a
        # time would move the first onto the second and then shift both.
        new_cell = NUM_RE.sub(lambda m: shifted.get(m.group(0), m.group(0)), cell)
        if new_cell != cell:
            rewrites.append({"id": ident, "line": n, "old": cell, "new": new_cell})
    return rewrites, moved, bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rewrites, moved, bad = audit(show(args.ref, REGISTER), show(args.ref, PRIMER))
    print(f"{len(rewrites)} row(s) to rewrite, {moved} anchor(s) shifted; {bad} anchor(s) failed the content check")
    if args.json:
        print(json.dumps(rewrites, ensure_ascii=False, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
