#!/usr/bin/env python3
"""Move MEMORY.md's inline detail into the topic files BEFORE the index is compacted.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc tooling
Author:      Paul Calnon
License:     MIT

The Claude memory index (MEMORY.md) is meant to be one line per memory, but entries
accumulate inline detail until the file approaches the 24.4KB read limit — at which point
the index stops being readable and EVERY session's recall degrades. Compacting it is
therefore necessary, and compacting it by deleting text is not: several facts live ONLY in
the index. Measured 2026-09-11, the 138KB canopy-E2E topic file did not contain
``F-CANOPY-052``, ``:8053``, ``JUNIPER_E2E_CANOPY_URL`` or ``canopy#613``, all of which the
index line carried.

So preservation must be mechanical and complete, and compression is a separate, editorial
step. This script does only the first: for every index line above ``--threshold`` chars it
appends the line VERBATIM to its primary topic file (the first ``[...](name.md)`` target)
under a dated heading. Nothing is deleted, nothing is reworded, and re-running is a no-op
because a line already present in its target is skipped.

The editorial half — rewriting each index line as a short pointer — is done by hand
afterwards, because a script cannot judge which clause is the one worth keeping.

Run:  python util/ad-hoc/2026-09-11_memory_index_preserve.py [--apply]
Default is a dry run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MEMORY_DIR = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory")
INDEX = MEMORY_DIR / "MEMORY.md"

LINK = re.compile(r"\[[^\]]*\]\(([A-Za-z0-9_\-.]+\.md)\)")
HEADING = "## Index digest (moved from MEMORY.md, 2026-09-11)"
PREAMBLE = "The index carried this inline. It is preserved verbatim here so compacting MEMORY.md loses nothing; several of these facts existed nowhere else."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=200, help="preserve index lines longer than this")
    ap.add_argument("--apply", action="store_true", help="write the appends (default: dry run)")
    args = ap.parse_args()

    lines = INDEX.read_text().splitlines()
    planned: list[tuple[int, str, Path]] = []
    skipped_present = 0
    missing_targets: list[tuple[int, str]] = []

    for n, line in enumerate(lines, start=1):
        if not line.startswith("- ") or len(line) <= args.threshold:
            continue
        targets = LINK.findall(line)
        if not targets:
            missing_targets.append((n, line[:80]))
            continue
        primary = MEMORY_DIR / targets[0]
        if not primary.exists():
            missing_targets.append((n, f"target {targets[0]} does not exist"))
            continue
        # The payload is the line minus its leading bullet; store it verbatim.
        if line.strip() in primary.read_text():
            skipped_present += 1
            continue
        planned.append((n, line, primary))

    print(f"index lines over {args.threshold} chars needing preservation: {len(planned)}")
    print(f"already present in their topic file (skipped)            : {skipped_present}")
    if missing_targets:
        print("\nLINES WITH NO USABLE TARGET -- handle by hand, do NOT shorten these blindly:")
        for n, why in missing_targets:
            print(f"  line {n}: {why}")

    by_target: dict[Path, list[tuple[int, str]]] = {}
    for n, line, primary in planned:
        by_target.setdefault(primary, []).append((n, line))

    print(f"\nwould append to {len(by_target)} topic file(s):")
    for primary, entries in sorted(by_target.items()):
        print(f"  {primary.name:58s} <- {len(entries)} line(s): {[n for n, _ in entries]}")

    if not args.apply:
        print("\n(dry run -- pass --apply to write)")
        return 0

    for primary, entries in by_target.items():
        text = primary.read_text()
        block = [""]
        if HEADING not in text:
            block += ["---", "", HEADING, "", PREAMBLE, ""]
        for _n, line in entries:
            block.append(line)
        if not text.endswith("\n"):
            block.insert(0, "")
        primary.write_text(text + "\n".join(block) + "\n")
        print(f"appended {len(entries)} line(s) to {primary.name}")

    print(f"\npreserved {len(planned)} index line(s) across {len(by_target)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
