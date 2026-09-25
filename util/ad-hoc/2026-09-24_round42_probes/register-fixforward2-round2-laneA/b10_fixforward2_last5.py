#!/usr/bin/env python3
"""Lane A round 2: the second fix-forward's "last 5 citations" (df21367d -> e2f87aae): which register lines, old ->
new citations, and whether each OLD number landed on a blank primer line (primer at df21367d)."""
import difflib
import re
import subprocess
from collections import Counter

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
NUM = re.compile(r"(?<![0-9A-Za-z_#:./])(\d{4,5})(?:\s*[-–]\s*(\d{4,5}))?(?![0-9A-Za-z_])")


def show(rev, rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout.decode("utf-8")


def cites(text):
    out = []
    for m in NUM.finditer(text):
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else None
        if (5758 < a < 10000 or (b and 5758 < b < 10000)) and text[max(0, m.start() - 4): m.start()] != "RFC ":
            out.append((a, b))
    return out


a, b = show("df21367d", REG).split("\n"), show("e2f87aae", REG).split("\n")
pri = show("df21367d", PRI).split("\n")
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
tot_c = tot_n = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    for k in range(max(i2 - i1, j2 - j1)):
        x = a[i1 + k] if i1 + k < i2 else ""
        y = b[j1 + k] if j1 + k < j2 else ""
        gone = list((Counter(cites(x)) - Counter(cites(y))).elements())
        came = list((Counter(cites(y)) - Counter(cites(x))).elements())
        if gone or came:
            bl = [[n for n in c if n and not pri[n - 1].strip()] for c in gone]
            print(f"old L{i1 + k + 1}/new L{j1 + k + 1}: gone={gone} came={came} blank_old={bl}")
