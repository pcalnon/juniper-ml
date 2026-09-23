#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Insert a drafted markdown section into a document, immediately before a marker line.

Used 2026-09-22 to put the re-evaluation section at the top of
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md``,
ahead of its stale ``## 0. PREFLIGHT``. It refuses when the marker is missing or appears more than
once, or when the section's first line is already in the document (so it cannot run twice).

Usage:
    python3 util/ad-hoc/2026-09-22_splice_section_before_marker.py <doc> <section.md> "<exact marker line>"
"""

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    doc, section, marker = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    lines = doc.read_text(encoding="utf-8").split("\n")
    body = section.read_text(encoding="utf-8").rstrip("\n")
    first = body.split("\n", 1)[0]
    hits = [i for i, line in enumerate(lines) if line == marker]
    if len(hits) != 1:
        print(f"REFUSED: marker {marker!r} found {len(hits)} times", file=sys.stderr)
        return 1
    if first in lines:
        print(f"REFUSED: the section's first line is already present: {first[:80]!r}", file=sys.stderr)
        return 1
    i = hits[0]
    new = lines[:i] + body.split("\n") + ["", "---", ""] + lines[i:]
    doc.write_text("\n".join(new), encoding="utf-8")
    print(f"inserted {len(body.splitlines())} lines before line {i + 1} of {doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
