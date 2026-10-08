#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice, group G5)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use. Read a unified diff and write it back WITHOUT the hunks whose every changed line is a
# documentation stamp (`**Version**`, `**Last Updated**`, `**Date**`, in the `Key**:` or `Key:**`
# spelling). The consolidation assembler bumps each file's stamps once, so the fleet PRs' own stamp
# edits are noise. Hunks that mix a stamp with content are KEPT and reported, never silently split.
# Usage: 2026-10-08_flood3_g5_drop_stamp_hunks.py <in.diff> <out.diff>
"""Drop stamp-only hunks from a unified diff."""

from __future__ import annotations

import re
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(\*\*:|:\*\*)")


def main(argv: list[str]) -> int:
    src, dst = Path(argv[0]), Path(argv[1])
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    hunk: list[str] = []
    dropped = kept_mixed = 0

    def flush() -> None:
        nonlocal hunk, dropped, kept_mixed
        if not hunk:
            return
        changed = [ln for ln in hunk[1:] if ln[:1] in "+-"]
        if changed and all(STAMP.match(ln[1:]) for ln in changed):
            dropped += 1
        else:
            if any(STAMP.match(ln[1:]) for ln in changed):
                kept_mixed += 1
                print(f"MIXED hunk kept: {hunk[0].strip()}", file=sys.stderr)
            out.extend(hunk)
        hunk = []

    for ln in lines:
        if ln.startswith("@@"):
            flush()
            hunk = [ln]
        elif hunk and (ln[:1] in " +-\\") and not ln.startswith(("--- a/", "+++ b/")):
            hunk.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    # A file header left with no hunks would make `git apply` fail; remove such headers.
    text = "".join(out)
    blocks = re.split(r"(?m)^(?=diff --git )", text)
    kept_blocks = [b for b in blocks if not b.startswith("diff --git ") or "\n@@" in b]
    dst.write_text("".join(kept_blocks), encoding="utf-8")
    print(f"{src.name}: dropped {dropped} stamp-only hunk(s); kept {kept_mixed} mixed hunk(s); files kept {sum(1 for b in kept_blocks if b.startswith('diff --git '))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
