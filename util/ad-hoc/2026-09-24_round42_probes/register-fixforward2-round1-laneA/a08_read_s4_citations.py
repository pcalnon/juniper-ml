#!/usr/bin/env python3
"""Lane A: lay each §4 Primer-cell citation past 5758 beside its row's finding, for reading.

For every §4 row (a table whose header has `ID` and `Primer` columns) whose Primer cell cites a line > 5758,
print the row id, the first 260 chars of the finding, and the head primer's lines n-1..n+2 for each cited n
(ranges: both ends). This lays out text; the judgement is mine, recorded in the report.
"""
import re
import sys

reg = open(sys.argv[1], encoding="utf-8").read().split("\n")
primer = open(sys.argv[2], encoding="utf-8").read().split("\n")
col = None
for i, line in enumerate(reg, 1):
    if line.startswith("|") and len(line.split("|")) > 2 and line.split("|")[1].strip() == "ID" and "Primer" in line:
        cells = [c.strip() for c in line.split("|")]
        col = cells.index("Primer")
        continue
    if not line.startswith("|"):
        col = None if not line.strip() else col
    if col is None or not line.startswith("| APD-"):
        continue
    cells = [c.strip() for c in line.split("|")]
    if len(cells) <= col:
        continue
    cell = cells[col]
    nums = [int(x) for x in re.findall(r"(?<!\d)\d{4}(?!\d)", cell)]
    nums = [n for n in nums if 5758 < n <= len(primer)]
    if not nums:
        continue
    finding = re.sub(r"\s+", " ", cells[2])[:260]
    print(f"\nL{i} {cells[1]} | Primer cell {cell!r}\n   FINDING: {finding}")
    for n in nums:
        for k in range(n - 1, n + 3):
            t = primer[k - 1].strip()
            mark = ">>" if k == n else "  "
            print(f"   {mark}{k}: {'<BLANK>' if not t else t[:170]}")
