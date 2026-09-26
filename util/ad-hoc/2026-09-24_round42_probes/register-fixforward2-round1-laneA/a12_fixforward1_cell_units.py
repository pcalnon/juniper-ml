#!/usr/bin/env python3
"""Lane A: what unit is "43 anchors in 39 rows' Primer cells"? Recount juniper-ml#2080's §4 Primer-cell edits.

Parses §4 Primer cells (tables whose header row has `ID` and `Primer`) at 6aabe4cc (before #2080) and
f2688a95 (after), keyed by (register line text id, row id). Counts changed rows, changed NUMBERS (every range
end separately) and changed CITATIONS (a range counts once). Then does the same for the three places the second
fix-forward moved, at df21367d vs e2f87aae.
"""
import re
import subprocess

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
R = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"


def get(rev):
    return subprocess.run(["git", "show", f"{rev}:{R}"], cwd=W, check=True, capture_output=True).stdout.decode().split("\n")


def cells(lines):
    out, col = {}, None
    for line in lines:
        if line.startswith("|") and len(line.split("|")) > 2 and line.split("|")[1].strip() == "ID" and "Primer" in line:
            col = [c.strip() for c in line.split("|")].index("Primer")
            continue
        if not line.strip():
            col = None
        if col is None or not line.startswith("| APD-"):
            continue
        cs = [c.strip() for c in line.split("|")]
        rid = cs[1]
        key = rid
        k = 2
        while key in out:
            key = f"{rid}#{k}"
            k += 1
        out[key] = cs[col]
    return out


CIT = re.compile(r"(?<!\d)(\d{3,4})(?:[-–](\d{3,4}))?(?!\d)")


def cites(cell):
    return [(int(a), int(b) if b else None) for a, b in CIT.findall(cell)]


before, after = cells(get("6aabe4cc")), cells(get("f2688a95"))
rows = nums = cits = 0
for key in before:
    if key in after and before[key] != after[key]:
        cb, ca = cites(before[key]), cites(after[key])
        if len(cb) != len(ca):
            print("  shape changed:", key, before[key], "->", after[key])
        rows += 1
        for (a0, b0), (a1, b1) in zip(cb, ca):
            if (a0, b0) != (a1, b1):
                cits += 1
                nums += 1 + (1 if b0 is not None else 0)
print(f"#2080 §4 cells: rows changed {rows}; citations changed {cits}; numbers changed {nums}")
# the second fix-forward's three places
b2, a2 = get("df21367d"), get("e2f87aae")
for ln in (527, 1736, 1737):
    old = [c for c in cites(b2[ln - 1]) if c[0] > 5758]
    new = [c for c in cites(a2[ln - 1]) if c[0] > 5758]
    chg = [(o, n) for o, n in zip(old, new) if o != n]
    print(f"L{ln}: citations changed {len(chg)}, numbers changed {sum(1 + (o[1] is not None) for o, n in chg)}: {chg}")
