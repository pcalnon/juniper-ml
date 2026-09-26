#!/usr/bin/env python3
"""Lane B r2: which touched tool sources hold raw splitlines() breakers (U+2028/U+2029 etc.)?

Compares split("\n") against splitlines() per file, and names each line holding a breaker other than \n.
"""
import sys
from pathlib import Path

BREAKERS = "\r\x0b\x0c\x1c\x1d\x1e\x85  "
root = Path(sys.argv[1])
for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    a = len(t.split("\n"))
    b = len(t.splitlines())
    hits = []
    for i, line in enumerate(t.split("\n"), 1):
        bad = [hex(ord(c)) for c in line if c in BREAKERS]
        if bad:
            hits.append((i, bad))
    flag = "  <-- breakers" if hits else ""
    print(f"{p.relative_to(root)}: split(\\n)={a} splitlines()={b}{flag}")
    for i, bad in hits:
        print(f"    line {i}: {bad}")
