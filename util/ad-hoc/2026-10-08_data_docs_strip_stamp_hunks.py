#!/usr/bin/env python3
"""Neutralise doc-stamp edits in a unified diff so a fleet docs PR can be 3-way applied without them.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. The consolidation brief says `**Version**` / `**Last Updated**` / `**Date**` stamp
edits are noise and must not be carried (the assembler bumps each file once). Every fleet docs PR
rewrites those lines, so applying the PRs one after another conflicts on the stamps alone.

For each hunk:
  * a removed stamp line becomes a context line (the preimage still carries it);
  * an added stamp line is dropped;
  * a hunk left with no +/- lines is dropped, and a file left with no hunks is dropped.

Hunk headers keep their original counts; apply the result with `git apply --recount --3way`.

    python3 util/ad-hoc/2026-10-08_data_docs_strip_stamp_hunks.py IN.diff > OUT.diff
"""

import re
import sys

STAMP = re.compile(r"^\*\*(?:Version|Last Updated|Date)(?:\*\*:|:\*\*)")


def strip(text: str) -> str:
    out: list[str] = []
    file_header: list[str] = []
    file_hunks: list[list[str]] = []
    hunk: list[str] | None = None

    def flush_hunk() -> None:
        nonlocal hunk
        if hunk is not None and any(line[:1] in "+-" for line in hunk[1:]):
            file_hunks.append(hunk)
        hunk = None

    def flush_file() -> None:
        nonlocal file_header, file_hunks
        flush_hunk()
        if file_hunks:
            out.extend(file_header)
            for h in file_hunks:
                out.extend(h)
        file_header, file_hunks = [], []

    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            flush_file()
            file_header = [line]
            continue
        if hunk is None and not line.startswith("@@"):
            file_header.append(line)
            continue
        if line.startswith("@@"):
            flush_hunk()
            hunk = [line]
            continue
        body = line[1:]
        if line.startswith("-") and STAMP.match(body):
            hunk.append(" " + body)
        elif line.startswith("+") and STAMP.match(body):
            continue
        else:
            hunk.append(line)
    flush_file()
    return "".join(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.stdout.write(strip(fh.read()))
