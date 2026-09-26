#!/usr/bin/env python3
"""Lane A helper: print every match of a regex in a file with N chars of context. usage: ctx.py <file> <regex> [N] [maxhits]"""
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
n = int(sys.argv[3]) if len(sys.argv) > 3 else 150
mx = int(sys.argv[4]) if len(sys.argv) > 4 else 50
lines_at = [0]
for i, ch in enumerate(text):
    if ch == "\n":
        lines_at.append(i + 1)
import bisect

for k, m in enumerate(re.finditer(sys.argv[2], text)):
    if k >= mx:
        break
    ln = bisect.bisect_right(lines_at, m.start())
    print(f"L{ln}: ...{text[max(0, m.start() - n):m.end() + n]}...".replace("\n", " / "))
    print()
