#!/usr/bin/env python3
"""Lane A: does any document in the head tree cite one of the 21 primer lines this commit rewrote?

Scans every .md/.txt/.py file in the head tree (eco/juniper-ml) that mentions the primer (by filename stem or
the word "primer") for a standalone number equal to a rewritten line, or a range covering one; prints hits with
context for reading. The primer itself is included (its own internal line references, e.g. Appendix E's).
"""
import pathlib
import re

S = pathlib.Path(__file__).resolve().parent
ML = S / "eco/juniper-ml"
CHANGED = [1954, 3346, 4224, 5363, 5378, 5400, 5498, 5502, 5631, 5838, 6119, 6120, 9880, 9939, 9940, 9941, 9942, 9943, 9944, 9973, 9974]
PAT = re.compile(r"(?<![\w.#/:-])(\d{4})(?:\s*[-–]\s*(\d{4}))?(?![\w])")
hits = 0
for f in sorted(ML.rglob("*")):
    if not f.is_file() or f.suffix not in (".md", ".txt", ".py"):
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if "PRIMER" not in text and "primer" not in text.lower():
        continue
    for ln, line in enumerate(text.split("\n"), 1):
        for m in PAT.finditer(line):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            if b < a or b - a > 60:
                continue
            cov = [c for c in CHANGED if a <= c <= b]
            if cov:
                hits += 1
                rel = f.relative_to(ML)
                print(f"{rel}:{ln}: cites {m.group(0)} (covers {cov}): ...{line[max(0, m.start() - 110):m.end() + 60]}...")
print("hits:", hits)
