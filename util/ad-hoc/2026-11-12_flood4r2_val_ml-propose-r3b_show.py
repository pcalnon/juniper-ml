#!/usr/bin/env python3
"""
Print one value of a JSON file by a dotted path, or the lines of a text file that match a pattern, cut to a width.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
This host refuses inline Python and pipes around some commands, and the evidence files of this check are large
(a manifest of 138 KB, documents with lines of several thousand characters). This reads them without either.

Usage:
    python3 <this> json <file> <dotted.path> [--width N]
    python3 <this> lines <file> <regex> [--width N] [--context N]
    python3 <this> range <file> <first> <last> [--width N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def dig(value, dotted: str):
    for part in [item for item in dotted.split(".") if item]:
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("mode", choices=("json", "lines", "range"))
    parser.add_argument("file", type=Path)
    parser.add_argument("what", nargs="*")
    parser.add_argument("--width", type=int, default=400)
    parser.add_argument("--context", type=int, default=0)
    args = parser.parse_args()
    text = args.file.read_text(encoding="utf-8")
    if args.mode == "json":
        value = dig(json.loads(text), args.what[0] if args.what else "")
        if isinstance(value, dict) and len(args.what) > 1 and args.what[1] == "keys":
            value = sorted(value)
        print(json.dumps(value, indent=1)[: args.width * 60])
        return 0
    lines = text.split("\n")
    if args.mode == "range":
        first, last = int(args.what[0]), int(args.what[1])
        for number in range(first, min(last, len(lines)) + 1):
            print(f"{number}: {lines[number - 1][: args.width]}")
        return 0
    pattern = re.compile(args.what[0])
    shown = set()
    for index, line in enumerate(lines):
        if pattern.search(line):
            for number in range(max(0, index - args.context), min(len(lines), index + args.context + 1)):
                if number not in shown:
                    shown.add(number)
                    print(f"{number + 1}: {lines[number][: args.width]}")
    print(f"-- {sum(1 for line in lines if pattern.search(line))} matching line(s) of {len(lines)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
