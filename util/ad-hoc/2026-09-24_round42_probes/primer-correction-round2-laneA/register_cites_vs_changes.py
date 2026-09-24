#!/usr/bin/env python3
"""Lane A r2: which primer lines does the defect register cite, and did PR #2075 change any of them?

Parses three citation forms from the register (main 602094e3 and PR #2074 head 6a9af70c):
  (a) detail rows   `| **Primer** | II.6 — lines 4197-4200, 4275-4279 |`
  (b) summary tables whose header has a `Primer` column (numbers / ranges in that cell)
  (c) prose         `primer line 5758`, `primer lines 3399-3400`
Intersects the cited set with line_invariance.json's changed lines and reports each hit as
MARKER-ONLY (cited text survives verbatim) or REWRITE/INSERT-OTHER (cited text changed).
"""
import json
import re
from pathlib import Path

S = Path(__file__).resolve().parent
changed = json.loads((S / "line_invariance.json").read_text())["lines"]
changed = {int(k): v["cls"] for k, v in changed.items()}
NUM = re.compile(r"(?<![\d.§])(\d{2,4})(?:\s*[-–]\s*(\d{2,4}))?(?![\d.])")


def expand(text):
    out = set()
    for a, b in NUM.findall(text):
        a = int(a)
        b = int(b) if b else a
        if 1 <= a <= 9866 and a <= b <= 9866 and b - a < 60:
            out.update(range(a, b + 1))
    return out


def cites(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    got = set()
    primer_col = None
    for ln in lines:
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if any(c in ("Primer", "**Primer**") for c in cells) and len(cells) > 2:
                primer_col = [i for i, c in enumerate(cells) if c in ("Primer", "**Primer**")][0]
                continue
            if re.match(r"^\|\s*\*\*Primer\*\*\s*\|", ln):
                got |= expand(cells[1].split("—", 1)[-1])
                continue
            if primer_col is not None and len(cells) > primer_col and not set(cells[primer_col]) <= set("-: "):
                got |= expand(cells[primer_col])
        else:
            primer_col = None if not ln.strip() else primer_col
        for m in re.finditer(r"primer(?:'s)?\s+(?:line|lines|L)\s*([\d,\s–-]+)", ln, re.I):
            got |= expand(m.group(1))
    return got


for label, fn in (("main 602094e3", "register_main_602094e3.md"), ("PR#2074 6a9af70c", "register_pr2074_6a9af70c.md")):
    c = cites(S / fn)
    hits = sorted(c & set(changed))
    print(f"{label}: {len(c)} distinct cited primer lines; {len(hits)} of them changed by #2075")
    for h in hits:
        print(f"   L{h}: {changed[h]}")
