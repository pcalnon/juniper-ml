#!/usr/bin/env python3
"""Show OLD vs NEW text of given line numbers: show_pairs.py OLD NEW N [N ...] [--width W]."""
import sys

args = sys.argv[1:]
width = 700
if "--width" in args:
    i = args.index("--width")
    width = int(args[i + 1])
    del args[i : i + 2]
old = open(args[0], encoding="utf-8", errors="surrogateescape").read().split("\n")
new = open(args[1], encoding="utf-8", errors="surrogateescape").read().split("\n")
for n in map(int, args[2:]):
    print(f"== line {n}")
    print("  OLD:", old[n - 1][:width])
    print("  NEW:", new[n - 1][:width])
