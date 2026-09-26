#!/usr/bin/env python3
"""List line numbers (in the NEW file) that differ between two same-length versions of a file.

Usage: changed_lines.py OLD NEW
If the line counts differ it also prints a unified diff summary via difflib.
"""
import difflib
import sys

old = open(sys.argv[1], encoding="utf-8", errors="surrogateescape").read().split("\n")
new = open(sys.argv[2], encoding="utf-8", errors="surrogateescape").read().split("\n")
print(f"old={len(old)} new={len(new)} lines")
if len(old) == len(new):
    changed = [i + 1 for i, (a, b) in enumerate(zip(old, new)) if a != b]
    print(f"{len(changed)} changed in place:", changed)
else:
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            print(tag, f"old {i1 + 1}-{i2}", f"new {j1 + 1}-{j2}")
