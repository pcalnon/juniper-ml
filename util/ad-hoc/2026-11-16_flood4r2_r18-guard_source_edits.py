#!/usr/bin/env python3
"""
Source hygiene for the agent guard's 1.4.0 hardening: invisible characters, their rewrite, and a docstring-only diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — one-off (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/claude_agent_guard.py 1.4.0 (_MASKED, _SPLICED); util/ad-hoc/2026-11-16_flood4r2_r18-guard_mutants.py.

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_source_edits.py scan <file> [...]
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_source_edits.py rewrite-masked <util/claude_agent_guard.py>
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_source_edits.py undo-sha <file> <new text file> <old text file>

``scan`` lists every private-use, byte-order-mark or zero-width character in each file: the editing tools stored
the ``\\ue00N`` escapes written for the guard's placeholders as the invisible characters themselves.
``rewrite-masked`` rewrites the ``_MASKED`` and ``_SPLICED`` lines with ``chr(0xE00N)``, so nothing invisible is
left. ``undo-sha`` prints the sha256 of <file> with the text of <new text file> replaced by the text of <old text
file> (it must occur once): the mutation run's subject (sha256 a491e891...) is the final guard without one
docstring sentence.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

MASKED_LINE = '_MASKED = {"{": chr(0xE001), "}": chr(0xE002), ",": chr(0xE003), ".": chr(0xE004), "$": chr(0xE005)}'
SPLICED_LINE = "_SPLICED = chr(0xE000)  # one computed part of a word (a substitution or a parameter): any text, or none"


def scan(paths: list) -> int:
    found = 0
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        bad = [(number, hex(ord(ch))) for number, line in enumerate(text.splitlines(), 1) for ch in line if 0xE000 <= ord(ch) <= 0xF8FF or ord(ch) in (0xFEFF, 0x200B)]
        found += len(bad)
        print("%s: %s" % (path, bad[:8] if bad else "none"))
    return 1 if found else 0


def rewrite_masked(path: str) -> int:
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    for index, line in enumerate(lines):
        if line.startswith("_MASKED = {"):
            lines[index] = MASKED_LINE
        elif line.startswith("_SPLICED = "):
            lines[index] = SPLICED_LINE
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return 0


def undo_sha(path: str, new_file: str, old_file: str) -> int:
    text = Path(path).read_text(encoding="utf-8")
    new = Path(new_file).read_text(encoding="utf-8").rstrip("\n")
    old = Path(old_file).read_text(encoding="utf-8").rstrip("\n")
    if text.count(new) != 1:
        print("the new text occurs %d times" % text.count(new))
        return 2
    print(hashlib.sha256(text.replace(new, old).encode("utf-8")).hexdigest())
    return 0


def main(argv: list) -> int:
    if len(argv) >= 3 and argv[1] == "scan":
        return scan(argv[2:])
    if len(argv) == 3 and argv[1] == "rewrite-masked":
        return rewrite_masked(argv[2])
    if len(argv) == 5 and argv[1] == "undo-sha":
        return undo_sha(argv[2], argv[3], argv[4])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
