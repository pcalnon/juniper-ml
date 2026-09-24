#!/usr/bin/env python3
"""Show primer lines matching a term set, excluding given line ranges, with truncated text."""
import re
import sys
from pathlib import Path

P = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneB/primer_WT.md")
RX = re.compile(sys.argv[1], re.I)
EXCL = []
for r in sys.argv[2:]:
    a, b = r.split("-")
    EXCL.append((int(a), int(b)))
WIDTH = 400

lines = P.read_text(encoding="utf-8").split("\n")
for i, ln in enumerate(lines, start=1):
    if any(a <= i <= b for a, b in EXCL):
        continue
    if RX.search(ln):
        t = ln if len(ln) <= WIDTH else ln[:WIDTH] + " ..."
        print(f"{i}: {t}")
