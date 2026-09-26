#!/usr/bin/env python3
"""Lane B: two register checks run inline during validation, kept here as the record.

1. Units: the census regex counts both ends of a range ("7953-7954" = 2). Count numbers (census unit)
   against citation items (a range counted once). Result at e2f87aae: 82 numbers, 69 items.
2. Table structure: unescaped `|` count per changed line, main vs head. Result: unchanged on all 24
   changed lines (7 table rows among them).

Needs main/ and head/ extractions of notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md.
"""
import re
from pathlib import Path

S = Path(__file__).resolve().parent
REL = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
head = (S / "head" / REL).read_text(encoding="utf-8").split("\n")
main = (S / "main" / REL).read_text(encoding="utf-8").split("\n")

NUMBER = re.compile(r"(?<![\w#:./])(?<!RFC )(\d{4,5})(?![\w]|\.\d)")
RANGE = re.compile(r"(?<![\w#:./])(\d{4,5})[-–](\d{4,5})(?![\w]|\.\d)")
nums = items = 0
for line in head:
    ends = [m for m in NUMBER.finditer(line) if 5758 < int(m.group(1)) <= 9982]
    rng = [m for m in RANGE.finditer(line) if 5758 < int(m.group(1)) <= 9982]
    nums += len(ends)
    items += len(ends) - len(rng)
print("numbers (census unit):", nums, "| citation items, ranges once:", items)

for i, (x, y) in enumerate(zip(main, head), 1):
    if x != y:
        px = len(re.findall(r"(?<!\\)\|", x))
        py = len(re.findall(r"(?<!\\)\|", y))
        print(i, "pipes main", px, "head", py, "OK" if px == py else "CHANGED")
