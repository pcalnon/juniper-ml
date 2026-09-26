#!/usr/bin/env python3
"""Lane B r2: every primer line the branch (main df21367d -> head 990ef3f9) rewrote, classified by region, and
whether Appendix E's intro paragraph (lines 9870-9884 at head) names it."""
import re
import sys
from pathlib import Path

S = Path(sys.argv[1])
main = (S / "hist/primer_df21367d.md").read_text(encoding="utf-8").split("\n")
head = (S / "after/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md").read_text(encoding="utf-8").split("\n")
assert len(main) == len(head)
intro = " ".join(head[9869:9884])
named = {int(x) for x in re.findall(r"\b(\d{4})\b", intro)}
for a, b in re.findall(r"\b(\d{4})-(\d{4})\b", intro):
    named |= set(range(int(a), int(b) + 1))
code_start = next(i for i, l in enumerate(head) if l.strip() == "<!-- example-file: conditional_datasets.py -->") + 1
tests_end = next(i for i in range(code_start, len(head)) if head[i].startswith("Run this example, and the other two")) + 1
for i, (x, y) in enumerate(zip(main, head), 1):
    if x != y:
        region = "II.11 code/tests" if code_start < i < tests_end else ("Appendix E" if i >= 9868 else "prose outside II.11 code")
        print(f"  L{i:<5} {region:26} named in E's intro: {'yes' if i in named else 'NO'}")
