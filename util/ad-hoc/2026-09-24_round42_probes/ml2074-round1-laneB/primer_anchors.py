#!/usr/bin/env python3
"""List every primer-line anchor > 5758 cited in the register (Primer column of section-4 tables,
**Primer** field of section-3 details, and bare 'NNNN' numbers in prose near 'primer'), and show
the primer text at N and N+3 so an off-by-3 anchor is visible."""
import re
import sys

reg_path, primer_path = sys.argv[1], sys.argv[2]
reg = open(reg_path, encoding="utf-8").read().split("\n")
pr = open(primer_path, encoding="utf-8").read().split("\n")


def pline(n):
    if 1 <= n <= len(pr):
        return pr[n - 1][:150]
    return "<out of range>"


hits = []
for i, line in enumerate(reg, 1):
    cells = [c.strip() for c in line.split("|")] if line.startswith("|") else None
    if cells and len(cells) >= 7 and re.match(r"APD-[A-Z]+-\d+", cells[1] or ""):
        # section-4 tables: | ID | Finding | Sev | Source | Primer | Conf |
        primer_cell = cells[-3]
        for m in re.finditer(r"\b(\d{4})(?:-(\d{4}))?\b", primer_cell):
            a = int(m.group(1))
            if a > 5758:
                hits.append((i, cells[1], primer_cell, a))
    if line.startswith("| **Primer**"):
        for m in re.finditer(r"\b(\d{4})(?:-(\d{4}))?\b", line):
            a = int(m.group(1))
            if a > 5758:
                hits.append((i, "detail", line.strip()[:120], a))

for i, rid, cell, a in hits:
    print(f"reg:{i} {rid} [{cell[:60]}] -> primer {a}: {pline(a)!r}")
    print(f"      primer {a+3}: {pline(a+3)!r}")
