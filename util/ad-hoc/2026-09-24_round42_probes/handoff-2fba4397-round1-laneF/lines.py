#!/usr/bin/env python3
"""Print line ranges of a file: lines.py FILE START-END [START-END ...] [--width N]."""
import sys

args = sys.argv[1:]
width = 240
if "--width" in args:
    i = args.index("--width")
    width = int(args[i + 1])
    del args[i : i + 2]
path = args[0]
with open(path, encoding="utf-8", errors="surrogateescape") as fh:
    text = fh.read()
lines = text.split("\n")
print(f"# {path}: {len(lines) - (1 if text.endswith(chr(10)) else 0)} lines")
for rng in args[1:]:
    a, _, b = rng.partition("-")
    a = int(a)
    b = int(b) if b else a
    print(f"== {a}-{b}")
    for n in range(a, b + 1):
        if 1 <= n <= len(lines):
            s = lines[n - 1]
            print(f"{n:6d}: {s[:width]}")
