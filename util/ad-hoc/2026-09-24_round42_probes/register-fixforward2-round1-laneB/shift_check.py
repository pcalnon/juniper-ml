#!/usr/bin/env python3
"""Lane B: test the register's §4-note claim that "line N of 68f62f5b is line N+3 today" holds for every
non-blank line past 5758. Run (as it was, inline) against `git show 68f62f5b:<primer>` saved as
primer_68f62f5b.md and head's primer extracted under head/notes/.

Result at e2f87aae: 3,250 non-blank lines past 5758 at 68f62f5b; the identity fails for 10 of them,
head lines [5773, 5774, 5786, 5787, 5838, 5857, 5901, 5945, 6120, 9510] (rewritten in place since).
"""
from pathlib import Path

S = Path(__file__).resolve().parent
old = (S / "primer_68f62f5b.md").read_text(encoding="utf-8").split("\n")
new = (S / "head/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md").read_text(encoding="utf-8").split("\n")
mism = []
nonblank = 0
for n in range(5759, len(old) + 1):
    o = old[n - 1]
    if not o.strip():
        continue
    nonblank += 1
    if n + 3 > len(new) or new[n + 3 - 1] != o:
        mism.append(n + 3)
print("non-blank lines past 5758 at 68f62f5b:", nonblank, "; identity fails for", len(mism), "; head lines:", mism)
