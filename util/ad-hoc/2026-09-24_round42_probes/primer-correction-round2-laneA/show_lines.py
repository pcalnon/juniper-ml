#!/usr/bin/env python3
"""Lane A r2: print numbered line ranges of a scratch primer copy. Usage: show_lines.py <file> a-b [c-d ...]"""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8").split("\n")
for rng in sys.argv[2:]:
    a, b = (int(x) for x in rng.split("-"))
    for i in range(a, b + 1):
        print(f"{i:5d}| {lines[i - 1]}")
    print("   ....")
