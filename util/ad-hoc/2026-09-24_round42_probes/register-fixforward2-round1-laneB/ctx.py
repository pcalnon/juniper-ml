#!/usr/bin/env python3
"""Lane B helper: print regex matches with context from a file.

Usage: ctx.py FILE REGEX [WIDTH] [LINES...]
If LINES are given, only those 1-based lines are searched.
"""
import re
import sys

path, pat = sys.argv[1], sys.argv[2]
width = int(sys.argv[3]) if len(sys.argv) > 3 else 120
only = {int(x) for x in sys.argv[4:]}
lines = open(path, encoding="utf-8").read().split("\n")
rx = re.compile(pat)
for i, line in enumerate(lines, 1):
    if only and i not in only:
        continue
    for m in rx.finditer(line):
        s = max(0, m.start() - width)
        e = min(len(line), m.end() + width)
        print(f"L{i}@{m.start()}: ...{line[s:e]}...")
