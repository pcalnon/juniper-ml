#!/usr/bin/env python3
"""Prove the MEMORY.md compaction lost nothing.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc tooling
Author:      Paul Calnon
License:     MIT

Companion to 2026-09-11_memory_index_preserve.py. Compacting the memory index is only
safe if every fact it carried still exists somewhere in the memory directory, and "I moved
the long lines first" is a claim, not a check. This is the check.

For every line of the ORIGINAL index, one of the following must hold:

  1. the line survives byte-identically in the new index; or
  2. the line survives verbatim in some topic file (what the preserve step guarantees); or
  3. every distinctive phrase in the line's prose is still findable somewhere under the
     memory directory.

Anything that satisfies none of the three is reported as a LOSS, with the phrase that
went missing, so it can be restored by hand. Exit 1 if any loss is found.

Phrases are the prose tail split on sentence/clause punctuation, with markdown links and
pure formatting removed, and very short fragments dropped (they match everywhere and would
make the check vacuous -- see the vacuous-pass class in this repo's own memory).

Run:  python util/ad-hoc/2026-09-11_memory_index_verify_lossless.py ORIGINAL_SNAPSHOT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MEMORY_DIR = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory")
INDEX = MEMORY_DIR / "MEMORY.md"

LINK = re.compile(r"\[([^\]]*)\]\([A-Za-z0-9_\-.]+\.md\)")
SPLIT = re.compile(r"[;.]|\s—\s|\s--\s|\*\*")
MIN_PHRASE_CHARS = 24


def corpus() -> str:
    """Every byte of memory, lowercased.

    Case-folded deliberately: folding a standalone entry into a grouped line re-cases its
    display text ("Per-run timeout ordering" -> "per-run timeout ordering"), which is a
    presentation change and not a lost fact. Comparing case-sensitively reports those as
    losses and buries the handful of real ones.
    """
    parts = []
    for path in sorted(MEMORY_DIR.glob("*.md")):
        parts.append(path.read_text())
    return "\n".join(parts).lower()


def phrases(line: str) -> list[str]:
    """Distinctive prose fragments of an index line, links reduced to their display text."""
    text = LINK.sub(r"\1", line).lstrip("- ").strip()
    out = []
    for chunk in SPLIT.split(text):
        chunk = chunk.strip().strip("`*_()[] ")
        if len(chunk) >= MIN_PHRASE_CHARS:
            out.append(chunk)
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    original_lines = [ln for ln in Path(sys.argv[1]).read_text().splitlines() if ln.startswith("- ")]
    new_text = INDEX.read_text()
    new_lines = set(ln for ln in new_text.splitlines())
    haystack = corpus()

    identical = verbatim = phrase_ok = 0
    losses: list[tuple[str, str]] = []

    for line in original_lines:
        if line in new_lines:
            identical += 1
            continue
        if line.strip().lower() in haystack:
            verbatim += 1
            continue
        missing = [p for p in phrases(line) if p.lower() not in haystack]
        if missing:
            for phrase in missing:
                losses.append((line[:70], phrase))
        else:
            phrase_ok += 1

    print(f"original index lines checked : {len(original_lines)}")
    print(f"  survive byte-identically   : {identical}")
    print(f"  survive verbatim in a topic: {verbatim}")
    print(f"  every phrase still findable: {phrase_ok}")
    print(f"  LOSSES                     : {len(losses)}")
    if losses:
        print("\nMISSING PHRASES -- restore these before considering the compaction done:")
        for src, phrase in losses:
            print(f"\n  from: {src}...")
            print(f"  lost: {phrase!r}")
        return 1
    print("\nNo phrase from the original index is missing from the memory directory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
