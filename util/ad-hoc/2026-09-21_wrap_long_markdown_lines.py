#!/usr/bin/env python3
"""
Wrap over-long prose lines of a markdown file at word boundaries (MD013, 512-char limit).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md

Only paragraph and list-item lines are touched. Fenced code blocks, table rows, headings,
HTML comments, link-reference definitions and blockquotes are left exactly as they are
(table rows cannot be wrapped and must be shortened by hand -- the script lists them).
A wrapped list item continues with the item's content indentation so it stays one item.
Soft line breaks inside a paragraph render as spaces, so the rendered text is unchanged.

Usage: 2026-09-21_wrap_long_markdown_lines.py <file.md> [--limit 512] [--target 480] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")


def wrap_line(line: str, target: int) -> list[str]:
    m = LIST_RE.match(line)
    indent = " " * (m.end() if m else len(line) - len(line.lstrip(" ")))
    out = []
    rest = line
    first = True
    while len(rest) > target:
        cut = rest.rfind(" ", len(indent) + 1 if not first else 1, target)
        if cut <= 0:
            break
        head, rest = rest[:cut].rstrip(), rest[cut + 1:].lstrip()
        out.append(head)
        rest = indent + rest
        first = False
    out.append(rest)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--limit", type=int, default=512)
    ap.add_argument("--target", type=int, default=480)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    out: list[str] = []
    in_fence = False
    wrapped = 0
    manual: list[tuple[int, int]] = []
    for n, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or len(line) <= args.limit:
            out.append(line)
            continue
        s = line.lstrip()
        if s.startswith(("|", "#", "<!--", ">", "[")):
            manual.append((n, len(line)))
            out.append(line)
            continue
        pieces = wrap_line(line, args.target)
        if len(pieces) > 1:
            wrapped += 1
            print(f"wrapped line {n} ({len(line)} chars) into {len(pieces)} lines")
        out.extend(pieces)

    for n, length in manual:
        print(f"MANUAL: line {n} ({length} chars) is a table row/heading/comment and was not wrapped")

    if not args.dry_run and wrapped:
        with open(args.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))
    print(f"wrapped {wrapped} line(s); {len(manual)} left for manual attention")
    return 0


if __name__ == "__main__":
    sys.exit(main())
