#!/usr/bin/env python3
"""Lane A: lay each non-§4-cell primer citation past 5758 beside its sentence, for reading.

Prints, for each named register line, the 260 characters around every 4-digit number in 5759..LAST (skipping
ones preceded by "RFC "), then the head primer's text over the cited span (+/-1 line).
usage: a09_read_prose_citations.py <register> <primer> <regline> [<regline> ...]
"""
import re
import sys

reg = open(sys.argv[1], encoding="utf-8").read().split("\n")
primer = open(sys.argv[2], encoding="utf-8").read().split("\n")
LAST = len(primer)
for ln in map(int, sys.argv[3:]):
    line = reg[ln - 1]
    print(f"\n==== register L{ln}")
    spans = []
    for m in re.finditer(r"(?<!\d)(\d{4})(?:[-–](\d{4}))?(?!\d)", line):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if not 5758 < a <= LAST or line[max(0, m.start() - 4) : m.start()] == "RFC ":
            continue
        ctx = line[max(0, m.start() - 200) : m.end() + 120]
        print(f"  cite {m.group(0)}: ...{ctx}...")
        for k in range(a - 1, b + 2):
            t = primer[k - 1].strip()
            print(f"      {'>>' if a <= k <= b else '  '}{k}: {'<BLANK>' if not t else t[:180]}")
