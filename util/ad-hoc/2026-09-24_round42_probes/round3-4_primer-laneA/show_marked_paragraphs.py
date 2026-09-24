"""Print each marked line of the primer with its enclosing paragraph (blank-line delimited)."""

from pathlib import Path

PRIMER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")
MARK = "**[Corrected: E.1](#e1-artifact-validator)**"
lines = PRIMER.read_text(encoding="utf-8").split("\n")
marked = [i for i, ln in enumerate(lines, start=1) if MARK in ln]
print("marked lines:", marked, "count", len(marked))
for n in marked:
    i = n - 1
    start = i
    while start > 0 and lines[start - 1].strip() != "":
        start -= 1
    end = i
    while end + 1 < len(lines) and lines[end + 1].strip() != "":
        end += 1
    # nearest heading above
    h = i
    while h >= 0 and not lines[h].startswith("#"):
        h -= 1
    print("=" * 100)
    print(f"LINE {n}  (paragraph {start + 1}-{end + 1}; heading L{h + 1}: {lines[h][:90]})")
    for k in range(start, end + 1):
        print(f"{k + 1:5d}{'*' if k == i else ' '} {lines[k]}")
