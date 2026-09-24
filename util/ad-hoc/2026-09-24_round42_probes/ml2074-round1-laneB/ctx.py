#!/usr/bin/env python3
"""ctx.py ALIAS PATTERN [WIDTH] -- print every occurrence of regex PATTERN with WIDTH chars of context."""
import os
import re
import sys

S = os.path.dirname(os.path.abspath(__file__))
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
ALIASES = {
    "hreg": os.path.join(S, "head", REG),
    "breg": os.path.join(S, "base", REG),
    "href": os.path.join(S, "head", "docs/REFERENCE.md"),
    "bref": os.path.join(S, "base", "docs/REFERENCE.md"),
}
path = ALIASES.get(sys.argv[1], sys.argv[1])
pat = re.compile(sys.argv[2])
width = int(sys.argv[3]) if len(sys.argv) > 3 else 160
text = open(path, encoding="utf-8").read()
lines = text.split("\n")
n = 0
for i, line in enumerate(lines, 1):
    for m in pat.finditer(line):
        n += 1
        a = max(0, m.start() - width)
        b = min(len(line), m.end() + width)
        print(f"[{n}] L{i} col{m.start()}: ...{line[a:b]}...")
print(f"# {n} hits")
