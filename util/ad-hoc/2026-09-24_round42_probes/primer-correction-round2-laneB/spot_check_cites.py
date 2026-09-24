#!/usr/bin/env python3
"""Print selected register-cited primer lines at base (dcfc024f) and head (b6129bf8), side by side.

Scratch instrument for round-2 Lane B.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = (HERE / "primer_base.md").read_text(encoding="utf-8").split("\n")
head = (HERE / "primer_head.md").read_text(encoding="utf-8").split("\n")
for n in (757, 1027, 1041, 1058, 1344, 2026, 3399, 3647, 4197, 4200, 4279, 7950, 9466, 9595):
    b, h = base[n - 1], head[n - 1]
    rel = "IDENTICAL" if b == h else ("MARKER APPENDED" if h.startswith(b.rstrip()) else "CHANGED")
    print(f"{n:5d} {rel:16s} {b[:95]!r}")
