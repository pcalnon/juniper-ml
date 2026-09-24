#!/usr/bin/env python3
"""rows.py ALIAS -- parse every section-4 table row: id, sev, fixed?, section. Also check cell counts per table."""
import os
import re
import sys
from collections import Counter, defaultdict

S = os.path.dirname(os.path.abspath(__file__))
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
ALIASES = {"hreg": os.path.join(S, "head", REG), "breg": os.path.join(S, "base", REG)}
path = ALIASES.get(sys.argv[1], sys.argv[1])
lines = open(path, encoding="utf-8").read().split("\n")


def split_cells(line):
    # split on unescaped pipes
    parts = re.split(r"(?<!\\)\|", line)
    return parts[1:-1] if line.strip().endswith("|") else parts[1:]


section = None
sec4 = False
rows = []
for i, line in enumerate(lines, 1):
    m = re.match(r"^(#{2,4}) (.*)", line)
    if m:
        section = m.group(2)[:40]
        if m.group(1) == "## ":
            pass
        sec4 = section.startswith("4") or section.startswith("4.")
        if line.startswith("## 5") or line.startswith("## 6"):
            sec4 = False
        if line.startswith("## 4"):
            sec4 = True
        continue
    if sec4 and line.startswith("| APD-"):
        cells = split_cells(line)
        rid = cells[0].strip()
        sev = cells[2].strip() if len(cells) > 2 else "?"
        fixed = "**FIXED" in line
        rows.append((i, section, rid, sev, fixed, len(cells)))

bysec = defaultdict(list)
for r in rows:
    bysec[r[1]].append(r)
for sec, rs in bysec.items():
    cc = Counter(r[5] for r in rs)
    print(f"{sec}: {len(rs)} rows, cell counts {dict(cc)}")
print()
mode = sys.argv[2] if len(sys.argv) > 2 else "open"
for (i, sec, rid, sev, fixed, nc) in rows:
    if mode == "all" or (mode == "open" and not fixed) or (mode == sev):
        print(f"L{i} [{sec[:14]}] {rid:18} sev={sev:3} fixed={fixed} cells={nc}")
print()
print("OPEN by sev:", Counter(r[3] for r in rows if not r[4]))
print("OPEN S rows:", [r[2] for r in rows if not r[4] and r[3] == "S"])
print("OPEN C rows:", [r[2] for r in rows if not r[4] and r[3] == "C"])
print("total rows", len(rows), "fixed", sum(1 for r in rows if r[4]), "open", sum(1 for r in rows if not r[4]))
