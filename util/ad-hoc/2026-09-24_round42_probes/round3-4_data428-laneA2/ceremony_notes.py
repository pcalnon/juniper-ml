"""What would the release ceremony put in the v0.16.0 Release body, from main's CHANGELOG as it stands,
and from the fix report's proposed remedy (delete lines 44-45)? Uses the ceremony's own parser.

Run with PYTHONDONTWRITEBYTECODE=1 so nothing is written into the juniper-ml worktree.
"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map")
sys.path.insert(0, str(WT / "util" / "release_train"))
import ceremony  # noqa: E402

L = Path(__file__).resolve().parent
main_text = (L / "trees/3a76a4c/CHANGELOG.md").read_text(encoding="utf-8")
lines = main_text.splitlines()
assert lines[43] == "## [0.16.0] - 2026-09-23" and lines[44] == "", (lines[43], lines[44])
proposed = "\n".join(lines[:43] + lines[45:]) + "\n"


def show(label: str, text: str) -> None:
    section = ceremony.changelog_version_section(text, "0.16.0")
    print(f"== {label}")
    for cat, bullets in section.items():
        print(f"   {cat}: {len(bullets)} bullets")
        for b in bullets:
            first = b if isinstance(b, str) else str(b)
            print(f"      - {' '.join(first.split())[:95]}")
    flat = " ".join(" ".join(str(b).split()) for bs in section.values() for b in bs)
    print(f"   mentions #428's ETag entry: {'ETag`s and conditional requests' in flat}; mentions the Breaking counter removal: {'access counters are no longer part' in flat}")
    print(f"   mentions #426 / #421 / #429 / #422 / #420: {[n for n in ('#426', '#421', '#429', '#422', '#420') if n in flat]}")


show("main 3a76a4c as it stands (two [0.16.0] headings)", main_text)
show("the fix report's remedy: delete lines 44-45", proposed)
