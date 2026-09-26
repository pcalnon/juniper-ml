#!/usr/bin/env python3
"""Lane A: structural diff of consecutive primer revisions (difflib opcodes on split('\n')), my own mapping.

Reports, per pair, line counts and every non-equal opcode with sizes, and prints the text of any
insert/delete/unequal-size replace, so "collapsed four lines into one" / "inserted three" / "moved none"
can be read off directly. git runs with cwd = this session's worktree (shared object store).
"""
import difflib
import subprocess

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
P = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
REVS = ["8d3d4573", "68f62f5b", "f7b89745", "f4d050c6", "e2f87aae"]


def get(rev):
    return subprocess.run(["git", "show", f"{rev}:{P}"], cwd=W, check=True, capture_output=True).stdout.decode("utf-8").split("\n")


texts = {r: get(r) for r in REVS}
for a, b in zip(REVS, REVS[1:]):
    A, B = texts[a], texts[b]
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    moved = [o for o in ops if o[0] != "replace" or (o[2] - o[1]) != (o[4] - o[3])]
    print(f"\n{a} -> {b}: lines {len(A)} -> {len(B)}; non-equal opcodes {len(ops)}; size-changing {len(moved)}")
    for tag, i1, i2, j1, j2 in moved:
        print(f"  {tag} {a}[{i1+1}..{i2}] ({i2-i1} lines) -> {b}[{j1+1}..{j2}] ({j2-j1} lines)")
        for k in range(i1, i2):
            print(f"     - {k+1}: {A[k][:150]!r}")
        for k in range(j1, j2):
            print(f"     + {k+1}: {B[k][:150]!r}")
