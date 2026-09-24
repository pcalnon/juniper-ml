"""CHANGELOG checks: lines of main's lost by #428, heading structure, and where #428's entries sit."""

import difflib
from pathlib import Path

T = Path(__file__).resolve().parent / "trees"


def lines(rev: str) -> list[str]:
    return (T / rev / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()


main_before, squash, head = lines("7125e16"), lines("af7831b"), lines("3a76a4c")

print("== lines present in 7125e16 (main before #428) but REMOVED by the squash af7831b:")
removed = [ln for ln in difflib.ndiff(main_before, squash) if ln.startswith("- ")]
for ln in removed:
    print("   ", repr(ln[2:])[:120])
print(f"   total removed: {len(removed)} (blank: {sum(1 for ln in removed if not ln[2:].strip())})")

# Multiset check, independent of diff alignment: every non-blank line of main's must survive.
from collections import Counter

lost = Counter(ln for ln in main_before if ln.strip()) - Counter(ln for ln in squash if ln.strip())
print("== non-blank lines of main's whose multiset count DROPPED in af7831b:", dict(lost))

print("\n== 3a76a4c: the [0.15.0] section's headings")
start = head.index("## [0.15.0] - 2026-09-22")
end = next(i for i in range(start + 1, len(head)) if head[i].startswith("## ["))
print("   ", [(i + 1, h) for i, h in enumerate(head[start:end], start) if h.startswith("### ")])

print("\n== 3a76a4c: what sits between the two '## [0.16.0] - 2026-09-23' headings (bold entry leads)")
idx = [i for i, h in enumerate(head) if h == "## [0.16.0] - 2026-09-23"]
print("   heading line numbers:", [i + 1 for i in idx])
for i in range(idx[0], idx[1]):
    if head[i].startswith("### ") or head[i].startswith("- **"):
        print(f"    {i + 1}: {head[i][:110]}")

print("\n== is the first block byte-identical to bd29376's [Unreleased] body?")
bd = lines("bd29376")
bd_unrel = bd[bd.index("## [Unreleased]") + 1 : bd.index("## [0.16.0] - 2026-09-23")]
main_block = head[idx[0] + 1 : idx[1]]
print("   bd29376 [Unreleased] body == 3a76a4c first-0.16.0 body:", bd_unrel == main_block, len(bd_unrel), len(main_block))

print("\n== proposed fix (delete 3a76a4c lines 44-45): resulting [Unreleased] headings")
fixed = head[:43] + head[45:]
u = fixed.index("## [Unreleased]")
nxt = next(i for i in range(u + 1, len(fixed)) if fixed[i].startswith("## ["))
print("   ", [(i + 1, h) for i, h in enumerate(fixed[u:nxt], u) if h.startswith("### ")], "next:", fixed[nxt])
print("   count of '## [0.16.0] - 2026-09-23' after fix:", fixed.count("## [0.16.0] - 2026-09-23"))
