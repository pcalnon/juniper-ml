#!/usr/bin/env python3
"""
List the control and invisible characters in the files of a change, and each file's non-ASCII characters.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
A helper written for this port held a literal byte-order mark inside a regular expression: the escape typed for it
was stored as the character itself, which no diff view shows. This reads each file given and reports any control
character other than newline and tab, and any of the invisible code points listed below, with its line number. It
also prints each file's distinct non-ASCII characters, so an unexpected one can be seen. It changes nothing.

Usage:
    python3 <this> FILE [FILE ...]
Exit 1 when any control or invisible character is found.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: Byte-order mark, zero-width space, the two directional marks, the line and paragraph separators, no-break space, DEL.
INVISIBLE = {0xFEFF, 0x200B, 0x200E, 0x200F, 0x2028, 0x2029, 0xA0, 0x7F}


def main() -> int:
    found = 0
    for name in sys.argv[1:]:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        hits = [(number, hex(ord(char))) for number, line in enumerate(text.split("\n"), start=1) for char in line if (ord(char) < 0x20 and char != "\t") or ord(char) in INVISIBLE]
        others = "".join(sorted({char for char in text if ord(char) > 0x7F and ord(char) not in INVISIBLE}))
        print(f"{path.name}: control/invisible {hits or 'none'}; non-ASCII {others or 'none'}")
        found += len(hits)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
