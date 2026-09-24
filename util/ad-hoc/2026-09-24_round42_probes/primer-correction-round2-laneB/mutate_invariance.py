#!/usr/bin/env python3
"""Negative controls for line_invariance.py: an inserted line, and an in-place edit of cited line 4200.

Scratch instrument for round-2 Lane B. Writes mut_insert.md and mut_edit4200.md next to this file,
and prints the base/head lengths of the head lines longer than 512 characters.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
head = (HERE / "primer_head.md").read_text(encoding="utf-8").split("\n")
base = (HERE / "primer_base.md").read_text(encoding="utf-8").split("\n")

a = head[:]
a.insert(3000, "inserted")
(HERE / "mut_insert.md").write_text("\n".join(a), encoding="utf-8")

b = head[:]
assert "never takes" in b[4199]
b[4199] = b[4199].replace("never takes", "seldom takes")
(HERE / "mut_edit4200.md").write_text("\n".join(b), encoding="utf-8")

for n in (786, 1344, 9481):
    print(n, "base", len(base[n - 1]), "head", len(head[n - 1]), "|", head[n - 1][:100])
