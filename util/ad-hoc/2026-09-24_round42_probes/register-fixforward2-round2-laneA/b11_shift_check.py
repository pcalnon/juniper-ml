#!/usr/bin/env python3
"""Lane A round 2: the §4 note's shift claim at the head.

"line N of 68f62f5b is line N+3 today ... that check holds for every non-blank line past 5758 that no later commit
rewrote in place". For every N > 5758 (68f62f5b numbering) with a non-blank old line: does head[N+3] == old[N]?
Each mismatch must be a line some later commit rewrote in place. Also: which commits moved lines (length change)?
"""
import difflib
import subprocess

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
REVS = ["8d3d4573", "68f62f5b", "f7b89745", "f4d050c6", "e2f87aae", "990ef3f9"]


def show(rev):
    return subprocess.run(["git", "show", f"{rev}:{PRI}"], cwd=WT, check=True, capture_output=True).stdout.decode("utf-8").splitlines()


T = {r: show(r) for r in REVS}
for r in REVS:
    print(f"{r}: {len(T[r])} lines")

# which revisions changed the line count or moved lines
inplace = {}  # head-numbered line -> commits that rewrote it in place
for a, b in zip(REVS, REVS[1:]):
    x, y = T[a], T[b]
    sm = difflib.SequenceMatcher(a=x, b=y, autojunk=False)
    ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
    moved = [op for op in ops if (op[2] - op[1]) != (op[4] - op[3])]
    print(f"{a}->{b}: {len(ops)} non-equal opcodes, {len(moved)} size-changing: {moved[:6]}")
    for op in ops:
        if (op[2] - op[1]) == (op[4] - op[3]):
            for j in range(op[3], op[4]):
                inplace.setdefault((b, j + 1), True)

old, head = T["68f62f5b"], T["990ef3f9"]
# map a line number at revision b to head numbering: only f7b89745 moves lines (+3 past 5758); after it no moves
def to_head(rev, n):
    return n  # all revisions after f7b89745 share numbering with head

rewritten_later = set()
for (rev, n) in inplace:
    if rev in ("f7b89745", "f4d050c6", "e2f87aae", "990ef3f9"):
        rewritten_later.add(n)

mism = []
for n in range(5759, len(old) + 1):
    if not old[n - 1].strip():
        continue
    if n + 3 > len(head) or head[n + 3 - 1] != old[n - 1]:
        mism.append(n + 3)
print(f"non-blank old lines N>5758 where head[N+3] != old[N]: {len(mism)} -> head lines {mism}")
print("   each rewritten in place by a later commit:", all(m in rewritten_later for m in mism), [m for m in mism if m not in rewritten_later])
