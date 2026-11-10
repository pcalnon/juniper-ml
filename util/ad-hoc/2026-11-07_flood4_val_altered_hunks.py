#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: print every -U0 hunk of `git diff origin/main -- <path>` that DELETES a line,
#               with word-level old/new comparison, so each alteration of main text can be justified.
"""
Read-only: print every hunk of `git diff -U0 origin/main -- <path>` that deletes a line, with a word-level old/new comparison, so each alteration of main's text can be justified.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import difflib
import re
import subprocess
import sys

path = sys.argv[1]
width = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
diff = subprocess.run(["git", "diff", "-U0", "origin/main", "--", path], capture_output=True, text=True, check=True).stdout
hunks = []
cur = None
for line in diff.splitlines():
    if line.startswith("@@"):
        cur = {"hdr": line, "old": [], "new": []}
        hunks.append(cur)
    elif cur is not None and line.startswith("-") and not line.startswith("---"):
        cur["old"].append(line[1:])
    elif cur is not None and line.startswith("+") and not line.startswith("+++"):
        cur["new"].append(line[1:])
for h in hunks:
    if not h["old"]:
        continue
    print("=" * 100)
    print(h["hdr"])
    old = "\n".join(h["old"])
    new = "\n".join(h["new"])
    ow = re.findall(r"\S+|\s+", old)
    nw = re.findall(r"\S+|\s+", new)
    sm = difflib.SequenceMatcher(a=ow, b=nw, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        o = "".join(ow[i1:i2])
        n = "".join(nw[j1:j2])
        print(f"  [{tag}] OLD: {o[:width]!r}")
        print(f"  [{tag}] NEW: {n[:width]!r}")
