#!/usr/bin/env python3
"""Which fixed ids does the crosscheck's §2 reading see MORE THAN ONCE in the status line (so dropping the
enumerated entry is invisible)? Compare base and head."""
import collections
import os
import re

S = os.path.dirname(os.path.abspath(__file__))
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
ID_RE = re.compile(r"APD-[A-Z]+-\d+[ab]?")
for which in ("base", "head"):
    text = open(os.path.join(S, which, REG), encoding="utf-8").read()
    lines = text.splitlines()
    status = next(l for l in lines if l.startswith("**Seventy") or "have since been fixed**" in l)
    c = collections.Counter(ID_RE.findall(status))
    multi = {k: v for k, v in c.items() if v > 1}
    print(f"{which}: status line has {len(c)} distinct ids; ids mentioned >1 time: {multi}")
    # show context of each extra mention
    for k in multi:
        for m in re.finditer(re.escape(k), status):
            a = max(0, m.start() - 90)
            print(f"    {k} @col{m.start()}: ...{status[a:m.end()+30]}...")
