#!/usr/bin/env python3
"""Alias wrapper: l.py ALIAS START[-END] ... [--w N]
ALIAS: hreg / breg (register head/base), hprim (primer head), or any path (absolute)."""
import os
import sys

S = os.path.dirname(os.path.abspath(__file__))
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRIM = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
ALIASES = {
    "hreg": os.path.join(S, "head", REG),
    "breg": os.path.join(S, "base", REG),
    "hprim": os.path.join(S, "head", PRIM),
    "href": os.path.join(S, "head", "docs/REFERENCE.md"),
}
args = sys.argv[1:]
width = 400
if "--w" in args:
    i = args.index("--w")
    width = int(args[i + 1])
    del args[i : i + 2]
path = ALIASES.get(args[0], args[0])
with open(path, encoding="utf-8") as fh:
    text = fh.read()
lines = text.split("\n")
if text.endswith("\n"):
    lines = lines[:-1]
print(f"# {path}: {len(lines)} lines")
for spec in args[1:]:
    if "-" in spec:
        a, b = spec.split("-")
        a, b = int(a), int(b)
    else:
        a = b = int(spec)
    for n in range(a, b + 1):
        if 1 <= n <= len(lines):
            print(f"{n}: {lines[n-1][:width]}")
    print("---")
