#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-03_reflow_long_markdown_lines.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-10-03
# Last Modified: 2026-10-03
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Reflow prose lines longer than the markdownlint MD013 limit (512 characters) at word
#    boundaries, keeping the rendered markdown identical: continuation lines of a list item are
#    indented to the item's content column, and blockquote lines keep their "> " prefix.
#    Lines inside fenced code blocks and table rows are never touched (a table row cannot be
#    wrapped; it is reported instead). Written for the 2026-10-03 handoff consolidation.
#
# Usage:
#    python3 util/ad-hoc/2026-10-03_reflow_long_markdown_lines.py [--width 400] [--check] FILE...
#####################################################################################################################################################################################################
import argparse
import re
import sys

LIMIT = 512
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
QUOTE_RE = re.compile(r"^((?:>\s?)+)")


def wrap(text, width, first_prefix, cont_prefix):
    words = text.split(" ")
    out, cur = [], first_prefix
    has_word = False
    for w in words:
        if has_word and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur, has_word = cont_prefix + w, True
        else:
            cur = cur + (" " if has_word else "") + w
            has_word = True
    out.append(cur)
    return out


def reflow_line(line, width):
    m = QUOTE_RE.match(line)
    if m:
        prefix = m.group(1)
        body = line[len(prefix):]
        return [prefix + x for x in reflow_line(body, width - len(prefix))]
    m = LIST_RE.match(line)
    if m:
        lead = m.group(0)
        return wrap(line[len(lead):], width, lead, " " * len(lead))
    indent = re.match(r"^\s*", line).group(0)
    return wrap(line[len(indent):], width, indent, indent)


def process(path, width, check):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    out, in_fence, changed, unfixable = [], False, 0, []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if len(line) <= LIMIT or in_fence:
            if len(line) > LIMIT:
                unfixable.append((i, "fence"))
            out.append(line)
            continue
        if line.lstrip().startswith("|"):
            unfixable.append((i, "table"))
            out.append(line)
            continue
        out.extend(reflow_line(line, width))
        changed += 1
    if not check and changed:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))
    return changed, unfixable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    bad = 0
    for f in a.files:
        changed, unfixable = process(f, a.width, a.check)
        print(f"{f}: {'would reflow' if a.check else 'reflowed'} {changed} line(s)")
        for i, kind in unfixable:
            print(f"  UNFIXABLE line {i} ({kind}) exceeds {LIMIT}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
