#!/usr/bin/env python3
"""Lane B helper: per-line word diff between main and head for a same-length file.

Usage: linediff.py <main file> <head file>
Prints, for every changed line (1-based), the words removed [-...-] and added {+...+}.
"""
import difflib
import sys

a = open(sys.argv[1], encoding="utf-8").read().split("\n")
b = open(sys.argv[2], encoding="utf-8").read().split("\n")
print(f"lines main={len(a)} head={len(b)}")
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    print(f"=== {tag} main[{i1+1}:{i2}] head[{j1+1}:{j2}]")
    if tag == "replace" and (i2 - i1) == (j2 - j1):
        for k in range(i2 - i1):
            la, lb = a[i1 + k], b[j1 + k]
            wa, wb = la.split(" "), lb.split(" ")
            sm2 = difflib.SequenceMatcher(a=wa, b=wb, autojunk=False)
            out = []
            for t2, x1, x2, y1, y2 in sm2.get_opcodes():
                if t2 == "equal":
                    seg = wa[x1:x2]
                    if len(seg) > 12:
                        seg = seg[:5] + ["..."] + seg[-5:]
                    out.append(" ".join(seg))
                else:
                    if x2 > x1:
                        out.append("[-" + " ".join(wa[x1:x2]) + "-]")
                    if y2 > y1:
                        out.append("{+" + " ".join(wb[y1:y2]) + "+}")
            print(f"--- L{j1 + k + 1}:")
            print(" ".join(out))
    else:
        for k in range(i1, i2):
            print(f"-M{k+1}: {a[k]}")
        for k in range(j1, j2):
            print(f"+H{k+1}: {b[k]}")
