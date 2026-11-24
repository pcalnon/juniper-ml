#!/usr/bin/env python3
"""
Summarise a frozen landing snapshot against main's copies of the same paths, for the orchestrator's last read before
a signed push: per-file line counts, every stamp line that moved, and the CHANGELOG's inserted block.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: landing the validated carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (writes the <freeze> directory this reads)

Usage:
  2026-11-11_flood4r2_s5_freeze_review.py <freeze dir> [--changelog-chars N] [--show <repo path> ...]

<freeze> holds paths.txt, snapshot/ and main/ (main's copy of every path main has). For each ``add`` path it prints the
lines added and removed against main's copy (an added file counts every line as added) and each changed line that
carries a stamp word (Version, Last Updated, Last Modified). For every CHANGELOG.md it says whether the change is a
pure insertion and prints the first N characters of what was inserted (default 1200). ``--show`` prints a path's whole
unified diff. It reads the freeze and writes nothing. Exit 0 always: this is a reading aid, not a gate.
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

STAMP = re.compile(r"Version|Last Updated|Last Modified")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines() if path.is_file() else []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 0
    freeze = Path(argv[1])
    limit = int(argv[argv.index("--changelog-chars") + 1]) if "--changelog-chars" in argv else 1200
    show = {argv[index + 1] for index, word in enumerate(argv[:-1]) if word == "--show"}
    total_added = total_removed = 0
    for line in read_lines(freeze / "paths.txt"):
        verb, _, path = line.partition(" ")
        if verb != "add":
            print(f"{'DELETE':>14}  {path}")
            continue
        old = read_lines(freeze / "main" / path)
        new = read_lines(freeze / "snapshot" / path)
        matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
        added: list[str] = []
        removed: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("replace", "delete"):
                removed += old[i1:i2]
            if tag in ("replace", "insert"):
                added += new[j1:j2]
        total_added += len(added)
        total_removed += len(removed)
        kind = "NEW FILE" if not (freeze / "main" / path).is_file() else ""
        print(f"+{len(added):<5} -{len(removed):<5}  {path} {kind}")
        for text in removed:
            if STAMP.search(text):
                print(f"        < {text.strip()[:150]}")
        for text in added:
            if STAMP.search(text) and len(text) < 220:
                print(f"        > {text.strip()[:150]}")
        if path.endswith("CHANGELOG.md"):
            print(f"        CHANGELOG: {'pure insertion' if not removed else f'NOT a pure insertion ({len(removed)} line(s) removed or rewritten)'}; {len(added)} line(s) in")
            block = "\n".join(added)
            print("        | " + block[:limit].replace("\n", "\n        | ") + (" …[cut]" if len(block) > limit else ""))
        if path in show:
            for text in difflib.unified_diff(old, new, f"main/{path}", f"snapshot/{path}", lineterm="", n=2):
                print("    " + text)
    print(f"total: +{total_added} -{total_removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
