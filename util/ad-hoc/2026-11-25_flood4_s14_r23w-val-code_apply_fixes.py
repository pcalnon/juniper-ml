"""
Apply a code lens's fixes.json (exact old -> new replacements) to a copy of a tree, refusing any old text that does not occur exactly once.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

ROOT is the directory the fixes' repo-relative "file" paths resolve against (a scratch copy, never a carrier).
Fixes whose file starts with "texts/" resolve against TEXTS_ROOT instead (default: ROOT).

Usage:
  python -I <this file> FIXES_JSON ROOT [--texts-root DIR] [--only ID,ID] [--check]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("fixes", type=pathlib.Path)
    parser.add_argument("root", type=pathlib.Path)
    parser.add_argument("--texts-root", type=pathlib.Path)
    parser.add_argument("--only", default="")
    parser.add_argument("--check", action="store_true", help="only verify every old text occurs exactly once")
    args = parser.parse_args()
    only = {x for x in args.only.split(",") if x}
    with args.fixes.open(encoding="utf-8") as fh:
        fixes = json.load(fh)
    status = 0
    for fix in fixes:
        if only and fix["id"] not in only:
            continue
        base = args.texts_root if (args.texts_root and fix["file"].startswith("texts/")) else args.root
        rel = fix["file"][len("texts/"):] if (args.texts_root and fix["file"].startswith("texts/")) else fix["file"]
        path = base / rel
        text = path.read_text(encoding="utf-8")
        count = text.count(fix["old"])
        verdict = "OK" if count == 1 else f"BAD (old occurs {count} times)"
        if count != 1:
            status = 1
        elif not args.check:
            path.write_text(text.replace(fix["old"], fix["new"], 1), encoding="utf-8")
        print(f'{fix["id"]} {fix["file"]}: {verdict}{"" if args.check or count != 1 else " applied"}')
    return status


if __name__ == "__main__":
    sys.exit(main())
