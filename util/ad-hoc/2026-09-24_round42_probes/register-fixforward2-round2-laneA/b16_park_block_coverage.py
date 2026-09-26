#!/usr/bin/env python3
"""Lane A round 2: every §4.9 row id (open or fixed) -- is it named, by its full id, in a park-block bullet
(lines between the park header and §5)? Also: any park bullet that names ids by range or ellipsis.
Usage: b16_park_block_coverage.py <register.md>
"""
import re
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8").split("\n")
s49 = next(i for i, l in enumerate(lines) if l.startswith("### 4.9"))
s5 = next(i for i, l in enumerate(lines) if l.startswith("## 5."))
park = next(i for i, l in enumerate(lines) if l.startswith("**Park / actionable status of the open post-primer rows**"))
rows = []
for i in range(s49, park):
    m = re.match(r"\| (APD-[A-Z]+-\d+[ab]?) \|", lines[i])
    if m:
        rows.append((m.group(1), "**FIXED" in lines[i], i + 1))
block = "\n".join(lines[park:s5])
bullets = [(i + 1, l) for i, l in enumerate(lines[park:s5], start=park) if l.startswith("- `APD-")]
print(f"§4.9 rows: {len(rows)}; park header at L{park + 1}; park bullets: {len(bullets)}")
for rid, fixed, ln in rows:
    named = [b for b, l in bullets if re.search(r"`" + re.escape(rid) + r"`", l)]
    anywhere = len(re.findall(r"`" + re.escape(rid) + r"`", block))
    print(f"  {rid:16} L{ln:<5} {'FIXED' if fixed else 'open ':5} bullet-head names it: {named or 'NO'}  (mentions in park block: {anywhere})")
for b, l in bullets:
    if "…" in l.split("—")[0] or re.search(r"`APD-[A-Z]+-\d+` (to|through|-) `APD", l.split("—")[0]):
        print(f"  RANGE-STYLE bullet head at L{b}: {l[:140]}")
