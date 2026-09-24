#!/usr/bin/env python3
"""
List every primer line number the defect register cites past the juniper-ml#1098 shift, with the text it lands on.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- read-only census; prints a table for a person to read
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

juniper-ml#1098 inserted three lines at primer line 5758, ten hours after the register was built, so every
register citation past 5758 that was taken from the earlier text was three short. Round 42's fix-forward
(juniper-ml#2080) moved the section-4 `Primer` cells through
util/ad-hoc/2026-09-24_register_primer_anchor_audit.py and seven prose citations from a hand list; its
post-merge validation (reports/2026-09-24_defect-register-round-42/ml2080-round1-laneA-reprobe.md H1,
ml2080-round1-laneB-refute.md H1) found five more in three places that neither reached, and showed why a
mechanical check cannot settle the question: "line N of 68f62f5b is line N+3 today" holds for every
non-blank line past 5758, so it cannot tell a right anchor from a wrong one. Only reading can.

So this does not judge. It finds every bare number in the register between 5759 and the primer's last line
that is not a PR/issue number, a `file:line` anchor, a version or part of an identifier, and prints the
register line, the section it sits in, the citation in context, and the primer text at that line (blank
lines flagged), so each one can be read against what its sentence quotes.

Usage: python3 util/ad-hoc/2026-09-24_register_primer_citation_census.py [--register PATH] [--primer PATH]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRIMER = REPO / "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
SHIFT_AT = 5758

# A bare 4-5 digit number, not glued to an identifier, a PR/issue mark, a `file:line` colon, a version dot or a
# URL path segment, and not an RFC number. Both ends of a range ("7950-7951") and every item of a list
# ("7962, 7964") are reported: a first draft excluded numbers after "-" and before "," and so missed the
# second end of every range and every list item but the last -- 7951, 7962 and 7968 on the very line the
# validation named. Thousands groups ("9,863") cannot match, being under four digits.
NUMBER = re.compile(r"(?<![\w#:./])(?<!RFC )(\d{4,5})(?![\w]|\.\d)")
# Deliberately NOT seen: `L7950`, `…PRIMER.md:7950` and `#L7950` shapes (the lookbehind drops them with
# identifiers and `file:line` anchors). None occurs in the register on 2026-09-24; re-check before relying
# on this for a register that has gained one.


def section_of(lines: "list[str]", idx: int) -> str:
    for j in range(idx, -1, -1):
        if lines[j].startswith("#"):
            return lines[j].lstrip("#").strip()[:40]
    return "(preamble)"


def where_of(line: str, section: str) -> str:
    if line.startswith("| **Primer**"):
        return "S3-field"
    if line.startswith("| APD-"):
        # §4 holds the register's own rows; §5's tables are fix records that cite the primer in prose.
        return "S4-cell" if section.startswith("4.") else "S5-row"
    return "prose"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--register", type=Path, default=REG)
    ap.add_argument("--primer", type=Path, default=PRIMER)
    args = ap.parse_args()
    reg = args.register.read_text(encoding="utf-8").split("\n")
    # splitlines(), not split("\n"): a file ending in a newline would otherwise gain a phantom empty last
    # line, and the count printed below said 9983 for the 9,982-line primer until 2026-09-24.
    primer = args.primer.read_text(encoding="utf-8").splitlines()
    last = len(primer)

    numbers = citations = 0
    for i, line in enumerate(reg):
        for m in NUMBER.finditer(line):
            n = int(m.group(1))
            if not SHIFT_AT < n <= last:
                continue
            # A range "A-B" is one citation with two numbers: both ends are printed and read, and only the
            # first counts as a citation.
            numbers += 1
            second_end = m.start() > 0 and line[m.start() - 1] == "-" and bool(re.search(r"\d-$", line[: m.start()]))
            citations += not second_end
            section = section_of(reg, i)
            ctx = line[max(0, m.start() - 70) : m.end() + 40].replace("\n", " ")
            text = primer[n - 1].strip()
            print(f"L{i + 1:<5} {where_of(line, section):8} {n:<5} [{section}]")
            print(f"        cite: ...{ctx}...")
            print(f"        primer {n}: {'<BLANK>' if not text else text[:150]}")
    print(f"{citations} citation(s), {numbers} number(s) counting both ends of a range, past line {SHIFT_AT} in {args.register.name} (primer has {last} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
