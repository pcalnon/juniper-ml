#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: fence-aware heading outline of a markdown file in the worktree vs origin/main.
#               Prints every heading that is NEW (not on main), with its line number and its parent
#               headings, plus the lines immediately before and after it, so placement can be judged.
#               Also prints main headings that are MISSING from the worktree copy.
"""
Read-only: list the headings a markdown file gains against origin/main (line, parent chain and the lines around it; fence-aware) and the main headings it no longer has.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import re
import subprocess
import sys

path = sys.argv[1]
ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 2


def headings(text):
    out = []
    fence = None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^(\s{0,3})(`{3,}|~{3,})", line)
        if m:
            tok = m.group(2)
            if fence is None:
                fence = tok[0] * len(tok)
            elif tok[0] == fence[0] and len(tok) >= len(fence):
                fence = None
            continue
        if fence is None:
            h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
            if h:
                out.append((i, len(h.group(1)), h.group(2)))
    return out


main_text = subprocess.run(["git", "show", f"origin/main:{path}"], capture_output=True, text=True, check=True).stdout
with open(path, encoding="utf-8") as fh:
    new_text = fh.read()
new_lines = new_text.splitlines()
mh = headings(main_text)
nh = headings(new_text)
main_set = {}
for _, lvl, t in mh:
    main_set[(lvl, t)] = main_set.get((lvl, t), 0) + 1
new_set = {}
for _, lvl, t in nh:
    new_set[(lvl, t)] = new_set.get((lvl, t), 0) + 1
missing = [k for k, v in main_set.items() if new_set.get(k, 0) < v]
print(f"main headings: {len(mh)}  worktree headings: {len(nh)}  missing-from-worktree: {len(missing)}")
for k in missing:
    print("  MISSING:", k)
seen = {}
stack = []
for ln, lvl, t in nh:
    while stack and stack[-1][0] >= lvl:
        stack.pop()
    parents = " > ".join(f"{'#' * a} {b}" for a, b, _ in stack)
    stack.append((lvl, t, ln))
    seen[(lvl, t)] = seen.get((lvl, t), 0) + 1
    if seen[(lvl, t)] > main_set.get((lvl, t), 0):
        print("-" * 100)
        print(f"NEW L{ln}: {'#' * lvl} {t}")
        print(f"   parent: {parents}")
        for j in range(max(0, ln - 1 - ctx), ln - 1):
            print(f"   before {j + 1}: {new_lines[j][:160]}")
        for j in range(ln, min(len(new_lines), ln + ctx)):
            print(f"   after  {j + 1}: {new_lines[j][:160]}")
