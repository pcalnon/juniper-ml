#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-6 validation
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Render-check the markdown tables that hold the round-6 subject's lines:
for each target line, find its enclosing table, and report the heading above
it, the header's column count, and every row whose column count differs
(pipes inside backtick code spans and escaped pipes are not counted).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 6 (findings: tmp/flood4/ml-docs/val-round6/)

Usage: python3 -I <this> <carrier_root> <out_txt>
"""
import re
import sys

TARGETS = {
    "docs/REFERENCE.md": [6646, 8923, 8952, 9151, 9152, 9154, 9862],
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md": [1132],
    "docs/DOCUMENTATION_OVERVIEW.md": [119],
}


def cols(line):
    s = re.sub(r"`[^`]*`", "", line).replace("\\|", "")
    return s.count("|")


def main():
    root, out_path = sys.argv[1], sys.argv[2]
    out = []
    for rel, targets in TARGETS.items():
        with open(root + "/" + rel, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for t in targets:
            i = t - 1
            if not lines[i].startswith("|"):
                out.append("%s:%d NOT A TABLE ROW: %s" % (rel, t, lines[i][:80]))
                continue
            a = i
            while a > 0 and lines[a - 1].startswith("|"):
                a -= 1
            b = i
            while b + 1 < len(lines) and lines[b + 1].startswith("|"):
                b += 1
            h = a
            while h > 0 and not lines[h].startswith("#"):
                h -= 1
            hdr = cols(lines[a])
            sep_ok = bool(re.match(r"^\|[\s:|-]+\|$", lines[a + 1]))
            bad = [(k + 1, cols(lines[k])) for k in range(a, b + 1) if cols(lines[k]) != hdr]
            out.append("%s:%d table L%d-%d under '%s' (L%d): header %d pipes, separator ok=%s, mismatched rows=%s; blank before=%s after=%s" % (
                rel, t, a + 1, b + 1, lines[h][:70], h + 1, hdr, sep_ok, bad, lines[a - 1].strip() == "", (b + 1 >= len(lines)) or lines[b + 1].strip() == ""))
    with open(out_path, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
