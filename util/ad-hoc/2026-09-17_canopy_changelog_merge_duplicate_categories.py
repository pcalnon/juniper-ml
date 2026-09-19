#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release train -- juniper-canopy v0.8.1
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Merge duplicate ``### <Category>`` blocks inside one CHANGELOG version section.

A version-move PR ("take [Unreleased] into [X.Y.Z]") and any PR that adds an entry to
[Unreleased] are a 3-way merge waiting to happen: both edit the top of the file, git
resolves them cleanly, and the result is a version section carrying **two** ``### Fixed``
headings. Nothing complains -- the file renders fine on GitHub.

It is not fine for the release train. ``ceremony.changelog_version_section`` accumulates
into an OrderedDict keyed by category and does ``result[current_cat] = bullets`` on each
heading, so the **second** block silently overwrites the first, and the published Release
body -- which is not re-cuttable -- ships only the last one.

Seen on juniper-canopy 0.8.1: canopy#634 moved [Unreleased] into [0.8.1] while canopy#633
and #635 were merging entries into [Unreleased]. The result had ``### Fixed`` twice, and a
render preview reported ``Fixed: 1`` for a section visibly containing three bullets -- the
packaging fix and the Y1 mount 500 would both have vanished from the notes.

This rewrites the named section with each category appearing once, bullets in first-seen
order, and refuses if it would change the bullet count.

Usage:
  python util/ad-hoc/2026-09-17_canopy_changelog_merge_duplicate_categories.py \\
      --changelog /path/to/CHANGELOG.md --version 0.8.1 --out /tmp/CHANGELOG.md
"""

import argparse
import re
import sys
from collections import OrderedDict
from pathlib import Path

CANONICAL_ORDER = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
BULLET = re.compile(r"^- ", re.M)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--changelog", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    text = Path(args.changelog).read_text(encoding="utf-8")
    head = re.compile(r"^##\s*\[?" + re.escape(args.version) + r"\]?", re.M)
    m = head.search(text)
    if m is None:
        print(f"no '## [{args.version}]' heading", file=sys.stderr)
        return 2
    start = m.start()
    nxt = re.compile(r"^##\s+(?!#)", re.M).search(text, m.end())
    end = nxt.start() if nxt else len(text)
    section, heading_line = text[start:end], text[start:text.index("\n", start)]

    parts = re.split(r"^### +([A-Za-z]+) *$", section, flags=re.M)
    if len(parts) < 3:
        print(f"[{args.version}] has no '### Category' blocks -- nothing to merge")
        return 0

    groups: "OrderedDict[str, list]" = OrderedDict()
    for name, chunk in zip(parts[1::2], parts[2::2]):
        groups.setdefault(name, []).append(chunk.strip("\n"))

    dupes = {k: len(v) for k, v in groups.items() if len(v) > 1}
    if not dupes:
        print(f"[{args.version}]: every category appears once -- nothing to merge")
        return 0

    before = len(BULLET.findall(section))
    out = [heading_line, "\n"]
    for name in list(CANONICAL_ORDER) + [k for k in groups if k not in CANONICAL_ORDER]:
        if name not in groups:
            continue
        body = "\n\n".join(b for b in groups[name] if b.strip())
        out.append(f"\n### {name}\n\n{body.strip()}\n")
    out.append("\n")
    merged = "".join(out)

    after = len(BULLET.findall(merged))
    if before != after:
        print(f"REFUSING: bullet count changed {before} -> {after}", file=sys.stderr)
        return 1

    Path(args.out).write_text(text[:start] + merged + text[end:], encoding="utf-8")
    print(f"[{args.version}]: merged duplicate categories {dupes}; "
          f"{before} bullets preserved; categories now {list(groups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
