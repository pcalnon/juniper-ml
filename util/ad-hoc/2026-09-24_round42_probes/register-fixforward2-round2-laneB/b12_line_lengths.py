#!/usr/bin/env python3
"""Lane B r2: lengths of every line the delta rewrote (both notes), before vs after, and the pipe count of table rows."""
import sys
from pathlib import Path

S = Path(sys.argv[1])
for rel in ("notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md", "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"):
    a = (S / "before" / rel).read_text(encoding="utf-8").split("\n")
    b = (S / "after" / rel).read_text(encoding="utf-8").split("\n")
    print(f"== {rel.split('/')[-1]}: {len(a)} -> {len(b)} split-lines")
    for i, (x, y) in enumerate(zip(a, b), 1):
        if x != y:
            pipes = f" pipes {x.count('|')}->{y.count('|')}" if y.lstrip().startswith("|") else ""
            print(f"   L{i}: len {len(x)} -> {len(y)}{pipes}")
