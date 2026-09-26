#!/usr/bin/env python3
"""Lane A round 2: which files in the head tree cite any of the 13 primer lines 990ef3f9 rewrote in place
(4199, 5346, 5377, 5378, 5433, 5434, 5502, 5600, 6117, 6120, 9880, 9943, 9944), by bare number or as the end of
a range that contains one? Prints each hit with context so it can be read against the new text.
Scans .md/.py/.txt under the head extract (excluding the primer itself for self-references shown separately)."""
import re
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head")
LINES = {4199, 5346, 5377, 5378, 5433, 5434, 5502, 5600, 6117, 6120, 9880, 9943, 9944}
RNG = re.compile(r"(?<![0-9A-Za-z_#:./])(\d{4})(?:\s*[-–]\s*(\d{4}))?(?![0-9A-Za-z_])")
PRIMER_NAME = "JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
for f in sorted(HEAD.rglob("*")):
    if not f.is_file() or f.suffix not in {".md", ".py", ".txt"}:
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    # only files that mention the primer (or are the primer) can cite its lines by bare number meaningfully
    if PRIMER_NAME not in text and "primer" not in text.lower():
        continue
    for i, line in enumerate(text.split("\n"), 1):
        for m in RNG.finditer(line):
            a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
            hit = [n for n in LINES if a <= n <= b] if b >= a and b - a < 200 else ([a] if a in LINES else [])
            if hit:
                rel = f.relative_to(HEAD)
                print(f"{rel}:{i}: {m.group(0)} -> {hit} | ...{line[max(0, m.start() - 80): m.end() + 40]}...")
