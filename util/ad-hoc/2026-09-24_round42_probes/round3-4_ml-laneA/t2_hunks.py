"""Print the round-3 register diff as numbered hunks: each changed line with its line number
in the NEW file (b8b24b41) or OLD file (27e1541d). Usage: t2_hunks.py [first_hunk] [last_hunk]"""

import re
import sys
import textwrap
from pathlib import Path

patch = (Path(__file__).parent / "t2_diff.patch").read_text(encoding="utf-8").splitlines()
hunks = []
cur = None
old_no = new_no = 0
for line in patch:
    m = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
    if m:
        cur = []
        hunks.append(cur)
        old_no, new_no = int(m.group(1)), int(m.group(2))
        continue
    if cur is None:
        continue
    if line.startswith("-"):
        cur.append(("-", old_no, line[1:]))
        old_no += 1
    elif line.startswith("+"):
        cur.append(("+", new_no, line[1:]))
        new_no += 1
    else:
        old_no += 1
        new_no += 1

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 1
hi = int(sys.argv[2]) if len(sys.argv) > 2 else len(hunks)
print(f"{len(hunks)} hunks")
for i, h in enumerate(hunks, start=1):
    if not (lo <= i <= hi):
        continue
    print(f"\n======== HUNK {i}")
    for sign, no, text in h:
        tag = "OLD" if sign == "-" else "NEW"
        wrapped = textwrap.wrap(text, 230) or [""]
        print(f"{sign}{tag}:{no}: {wrapped[0]}")
        for w in wrapped[1:]:
            print(f"      {w}")
