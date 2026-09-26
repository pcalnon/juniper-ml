#!/usr/bin/env python3
"""Lane A round 2: my own census of 4-5 digit numbers in (5758, primer_len] in the register at a rev.

Independent of the repo census: every maximal ASCII digit run of 4-5 digits, whatever precedes or follows it
(letters, '#', ':', '/', '.', ',' included), in range. Each is printed with its prefix/suffix class so I can
classify it by hand as a primer citation or not. Ranges (A-B, A–B) are detected on the raw text.
Usage: b04_my_citation_census.py <rev>
"""
import re
import subprocess
import sys

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
rev = sys.argv[1] if len(sys.argv) > 1 else "990ef3f9"


def show(rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout.decode("utf-8")


reg = show(REG).split("\n")
pri = show(PRI).splitlines()
last = len(pri)
RUN = re.compile(r"(?<![0-9])([0-9]{4,5})(?![0-9])")
rows = []
for i, line in enumerate(reg):
    for m in RUN.finditer(line):
        n = int(m.group(1))
        if not 5758 < n <= last:
            continue
        pre = line[max(0, m.start() - 12): m.start()]
        post = line[m.end(): m.end() + 8]
        rows.append((i + 1, n, pre, post, m.start()))
print(f"primer lines: {last}; raw in-range digit runs: {len(rows)}")
for ln, n, pre, post, pos in rows:
    print(f"L{ln:<5} {n:<5} pre={pre!r:18} post={post!r}")
