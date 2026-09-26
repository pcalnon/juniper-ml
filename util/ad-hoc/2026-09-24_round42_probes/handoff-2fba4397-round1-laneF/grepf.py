#!/usr/bin/env python3
"""grep a file with a Python regex: grepf.py FILE REGEX [--width N] [-i] [--ctx N]."""
import re
import sys

args = sys.argv[1:]
width = 260
ctx = 0
flags = 0
if "--width" in args:
    i = args.index("--width")
    width = int(args[i + 1])
    del args[i : i + 2]
if "--ctx" in args:
    i = args.index("--ctx")
    ctx = int(args[i + 1])
    del args[i : i + 2]
if "-i" in args:
    args.remove("-i")
    flags |= re.IGNORECASE
path, pat = args[0], args[1]
rx = re.compile(pat, flags)
with open(path, encoding="utf-8", errors="surrogateescape") as fh:
    lines = fh.read().split("\n")
hits = [i for i, s in enumerate(lines) if rx.search(s)]
shown = set()
for i in hits:
    for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
        if j in shown:
            continue
        shown.add(j)
        mark = ">" if j == i else " "
        print(f"{mark}{j + 1:6d}: {lines[j][:width]}")
    if ctx:
        print("--")
print(f"# {len(hits)} hit(s)")
