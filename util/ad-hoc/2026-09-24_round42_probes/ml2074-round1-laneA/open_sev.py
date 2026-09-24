#!/usr/bin/env python3
"""Lane A: severity of every OPEN section-4 row, base vs head -- which open rows are S, and which
juniper-data rows are C (register-wide, primer and post-primer alike)."""
import re
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, S)
from lane_a_count import ID_RE, split_cells  # noqa: E402

for tree in ("base", "head"):
    lines = open(f"{S}/{tree}/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md", encoding="utf-8").read().split("\n")
    s4 = next(i for i, ln in enumerate(lines) if ln.startswith("## 4. Full register"))
    s5 = next(i for i, ln in enumerate(lines) if ln.startswith("## 5. Fixed findings"))
    sub = None
    rows = []
    for i in range(s4, s5):
        ln = lines[i]
        if ln.startswith("### "):
            sub = ln[4:12]
            continue
        if not ln.lstrip().startswith("| APD-"):
            continue
        c = split_cells(ln)
        m = ID_RE.fullmatch(c[0].replace("†", "").strip())
        if not m:
            continue
        rows.append((m.group(0), "**FIXED" in c[1], c[2].strip(), sub))
    open_rows = [r for r in rows if not r[1]]
    print(f"== {tree}: open rows by Sev:", {s: sum(1 for r in open_rows if r[2] == s) for s in "SCRME"})
    print("   open S rows:", [r[0] for r in open_rows if r[2] == "S"])
    print("   open juniper-data C rows:", [(r[0], r[3]) for r in open_rows if r[2] == "C" and r[0].startswith("APD-DATA")])
    print("   open C rows (all):", [r[0] for r in open_rows if r[2] == "C"])
