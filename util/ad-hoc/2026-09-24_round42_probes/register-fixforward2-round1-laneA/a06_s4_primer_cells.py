#!/usr/bin/env python3
"""Lane A: print the §4 Primer-column cell of named register rows (my own parser: header row with a `Primer` column).

usage: a06_s4_primer_cells.py <register> <ID> [<ID> ...]
"""
import sys

reg = open(sys.argv[1], encoding="utf-8").read().split("\n")
want = set(sys.argv[2:])
col = None
for i, line in enumerate(reg, 1):
    if line.startswith("|") and "Primer" in line and line.split("|")[1].strip() == "ID":
        cells = [c.strip() for c in line.split("|")]
        col = cells.index("Primer")
        continue
    if col is not None and line.startswith("| APD-"):
        cells = [c.strip() for c in line.split("|")]
        rid = cells[1].split()[0]
        if rid in want:
            print(f"L{i} {rid}: Primer cell = {cells[col]!r}")
