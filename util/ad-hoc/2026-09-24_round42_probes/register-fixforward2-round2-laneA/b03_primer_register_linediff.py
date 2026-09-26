#!/usr/bin/env python3
"""Lane A round 2: positional line diff of primer + register between e2f87aae and 990ef3f9.

Primer: count of changed lines, line counts (wc -l style and splitlines), breakers in changed lines.
Register: which lines changed, line counts, pipe counts on changed table rows.
"""
import subprocess
import difflib

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
BRK = "\r\x0b\x0c\x1c\x1d\x1e\x85  "


def show(rev, rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout.decode("utf-8")


for rel in (PRI, REG):
    a, b = show("e2f87aae", rel), show("990ef3f9", rel)
    al, bl = a.split("\n"), b.split("\n")
    print(f"== {rel}")
    print(f"   newline-count (wc -l): {a.count(chr(10))} -> {b.count(chr(10))}; splitlines: {len(a.splitlines())} -> {len(b.splitlines())}; split: {len(al)} -> {len(bl)}")
    if len(al) == len(bl):
        ch = [i + 1 for i, (x, y) in enumerate(zip(al, bl)) if x != y]
        print(f"   positional changes: {len(ch)}: {ch}")
        for n in ch:
            bad = [("U+%04X" % ord(c)) for c in bl[n - 1] if c in BRK]
            if bad:
                print(f"   BREAKER on new line {n}: {bad}")
            if bl[n - 1].startswith("|"):
                print(f"   line {n} pipes: {al[n - 1].count('|')} -> {bl[n - 1].count('|')}  (unescaped: {al[n - 1].replace(chr(92) + '|', '').count('|')} -> {bl[n - 1].replace(chr(92) + '|', '').count('|')})")
    else:
        sm = difflib.SequenceMatcher(a=al, b=bl, autojunk=False)
        for op in sm.get_opcodes():
            if op[0] != "equal":
                print("  ", op)
    # breakers anywhere in the new file
    allb = [(i + 1, "U+%04X" % ord(c)) for i, line in enumerate(bl) for c in line if c in BRK]
    print(f"   breakers anywhere in 990ef3f9 file: {allb}")
