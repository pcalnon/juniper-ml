#!/usr/bin/env python3
"""Reflow markdown prose lines longer than the repo's MD013 limit (512) at word boundaries.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use documentation formatter)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc. Wraps paragraph and list-item lines only; a table row longer than the limit is
             REPORTED, never wrapped (MD013 applies to table rows and the fix there is shorter cells --
             memory note reference_md013_applies_to_table_rows). Continuation lines of a list item are
             indented so the item stays one item. Fenced code blocks are left alone.

Run:
    python3 util/ad-hoc/2026-10-05_md_reflow_long_lines.py <file.md> [<file.md> ...]
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

LIMIT = 512
_LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")


def reflow(text: str) -> tuple[str, list[str]]:
    out: list[str] = []
    reports: list[str] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or len(line) <= LIMIT:
            out.append(line)
            continue
        if stripped.startswith("|"):
            reports.append(f"line {lineno}: table row of {len(line)} chars left as is (shorten the cell)")
            out.append(line)
            continue
        m = _LIST.match(line)
        if m:
            indent = " " * (len(m.group(1)) + len(m.group(2)) + 1)
            wrapped = textwrap.wrap(line, width=LIMIT, subsequent_indent=indent, break_long_words=False, break_on_hyphens=False)
        else:
            lead = re.match(r"^(\s*)", line).group(1)
            wrapped = textwrap.wrap(line, width=LIMIT, initial_indent="", subsequent_indent=lead, break_long_words=False, break_on_hyphens=False)
        out.extend(wrapped)
        reports.append(f"line {lineno}: wrapped {len(line)} chars into {len(wrapped)} lines")
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), reports


def main(argv: list[str]) -> int:
    for arg in argv:
        path = Path(arg)
        new, reports = reflow(path.read_text())
        path.write_text(new)
        for r in reports:
            print(f"{path.name}: {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
