#!/usr/bin/env python3
"""Print given line ranges of a file. Usage: lines.py FILE START[-END] [START[-END] ...] [--w WIDTH]"""
import sys

args = sys.argv[1:]
width = 400
if "--w" in args:
    i = args.index("--w")
    width = int(args[i + 1])
    del args[i : i + 2]
path = args[0]
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
