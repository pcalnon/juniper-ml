#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only, strict carried-line check. For every carried draft PR N and every line the draft
#               ADDS (its own merge-base..head diff, saved as <drafts>/draft_<N>.diff.patch), apply the
#               builder's recorded text fixes (fixes.json: old -> new, same path; own PR first, then any PR)
#               and require the result to appear VERBATIM as a line of the carrier's file (this worktree).
#               Stamp lines and REFERENCE Version History rows are skipped (dropped by design).
#               Prints every expected line that is absent, with the closest carrier line, and flags a
#               carrier line that is a strict PREFIX of the expected line (truncation) or vice versa.
"""
Read-only strict carried-line check: every markdown line a carried draft adds must appear verbatim in the carrier's copy once the builder's recorded fixes are applied; print each that does not, with the closest carrier line and whether it was truncated or extended.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import difflib
import json
import re
import sys

drafts_dir, fixes_path = sys.argv[1], sys.argv[2]
prs = [int(x) for x in sys.argv[3:]]
with open(fixes_path, encoding="utf-8") as fh:
    fixes = [f for f in json.load(fh) if "old" in f]
STAMP = re.compile(r"^\*\*(Version|Date|Last Updated)\*?\*?:?")
HIST = re.compile(r"^\|\s*0\.6\.\d+")
carrier_cache = {}


def carrier_lines(path):
    if path not in carrier_cache:
        with open(path, encoding="utf-8") as fh:
            carrier_cache[path] = fh.read().splitlines()
    return carrier_cache[path]


total = 0
missing = []
for n in prs:
    with open(f"{drafts_dir}/draft_{n}.diff.patch", encoding="utf-8") as fh:
        text = fh.read()
    path = None
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("+++") or not line.startswith("+") or path is None:
            continue
        if not path.endswith(".md"):
            continue
        body = line[1:]
        if not body.strip() or STAMP.match(body) or (path == "docs/REFERENCE.md" and HIST.match(body)):
            continue
        expected = body
        applied = []
        for f in sorted(fixes, key=lambda f: (f["pr"] != n,)):
            if f["path"] == path and f["old"] in expected:
                expected = expected.replace(f["old"], f["new"])
                applied.append(f["pr"])
        total += 1
        lines = carrier_lines(path)
        if expected in lines:
            continue
        # also accept when the expected text is a multi-line replacement that now spans lines
        joined = "\n".join(lines)
        if expected in joined:
            continue
        best = difflib.get_close_matches(expected, lines, n=1, cutoff=0.5)
        b = best[0] if best else ""
        kind = "ABSENT"
        if b and expected.startswith(b) and len(b) < len(expected):
            kind = "TRUNCATED (carrier line is a prefix of the expected line)"
        elif b and b.startswith(expected):
            kind = "EXTENDED (carrier line extends the expected line)"
        elif b:
            kind = "DIFFERS"
        missing.append((n, path, kind, applied, expected, b))

print(f"draft added lines checked: {total}; not found verbatim after fixes: {len(missing)}")
for n, path, kind, applied, exp, best in missing:
    print("=" * 110)
    print(f"#{n} {path}: {kind}; fixes applied from PRs {applied}")
    sm = difflib.SequenceMatcher(a=exp, b=best, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            print(f"   [{tag}] expected: {exp[max(0, i1 - 30):i2 + 30]!r}")
            print(f"   [{tag}] carrier : {best[max(0, j1 - 30):j2 + 30]!r}")
