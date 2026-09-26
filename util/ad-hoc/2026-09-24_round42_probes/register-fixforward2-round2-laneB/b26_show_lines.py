#!/usr/bin/env python3
"""Lane B r2: print chosen primer lines at main and head, with a character-level diff of each."""
import difflib
import sys
from pathlib import Path

S = Path(sys.argv[1])
main = (S / "hist/primer_df21367d.md").read_text(encoding="utf-8").split("\n")
head = (S / "after/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md").read_text(encoding="utf-8").split("\n")
for n in map(int, sys.argv[2:]):
    a, b = main[n - 1], head[n - 1]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    edits = [(t, a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    print(f"L{n}:")
    for t, x, y in edits:
        print(f"   {t}: {x[:160]!r} -> {y[:200]!r}")
