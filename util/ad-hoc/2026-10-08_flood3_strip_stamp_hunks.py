#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc
# File Name:     2026-10-08_flood3_strip_stamp_hunks.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#    Single-use helper for the Cursor flood #3 evaluation (cascor-deploy slice). Reads a unified
#    diff and neutralises every documentation STAMP edit (`**Version**`, `**Last Updated**`,
#    `**Date**` lines, in both the `**X**:` and `**X:**` spellings): a removed stamp line becomes a
#    context line and an added stamp line is dropped. Hunk headers are recomputed; hunks and file
#    sections left with no change are dropped. The brief forbids stamp edits in prepared docs (the
#    assembler bumps each file once), and N fleet PRs that each bump the same stamp otherwise
#    conflict with one another on that line alone.
#
#    Usage: 2026-10-08_flood3_strip_stamp_hunks.py <in.diff> <out.diff>
#    Prints one line per stamp line neutralised, so the drop is counted rather than silent.
#####################################################################################################################################################################################################
from __future__ import annotations

import re
import sys

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(\*\*:|:\*\*)")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def is_stamp(body: str) -> bool:
    return bool(STAMP.match(body))


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    out: list[str] = []
    i = 0
    file_header: list[str] = []
    file_hunks: list[str] = []
    current_path = ""
    neutralised = 0

    def flush_file() -> None:
        if file_header and file_hunks:
            out.extend(file_header)
            out.extend(file_hunks)

    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            flush_file()
            file_header = [line]
            file_hunks = []
            current_path = line.split(" b/", 1)[-1]
            i += 1
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff --git "):
                file_header.append(lines[i])
                i += 1
            continue
        m = HUNK.match(line)
        if m:
            old_start = int(m.group(1))
            new_start = int(m.group(3))
            tail = m.group(5)
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff --git "):
                body.append(lines[i])
                i += 1
            new_body: list[str] = []
            for b in body:
                if b.startswith("-") and is_stamp(b[1:]):
                    new_body.append(" " + b[1:])
                    neutralised += 1
                    print(f"neutralised stamp in {current_path}: {b[1:].strip()[:80]}")
                elif b.startswith("+") and is_stamp(b[1:]):
                    continue
                else:
                    new_body.append(b)
            # trailing empty string from the final split is not part of a hunk
            while new_body and new_body[-1] == "" and (i >= len(lines)):
                new_body.pop()
            if not any(x.startswith(("+", "-")) for x in new_body):
                continue
            # "\ No newline at end of file" markers start with "\" and count toward neither side.
            old_len = sum(1 for x in new_body if x.startswith((" ", "-")) or x == "")
            new_len = sum(1 for x in new_body if x.startswith((" ", "+")) or x == "")
            file_hunks.append(f"@@ -{old_start},{old_len} +{new_start},{new_len} @@{tail}")
            file_hunks.extend(new_body)
            continue
        i += 1
    flush_file()
    text = "\n".join(out)
    if not text.endswith("\n"):
        text += "\n"
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"total stamp lines neutralised: {neutralised}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
