#!/usr/bin/env python3
"""
Report every test name a docs carrier cites that exists in none of the given trees.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (flood-4 docs carrier vs tests carrier cross-check)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

WHY THIS EXISTS
The flood-4 docs carrier names tests that only arrive with the tests carrier (and some that live in
sibling repositories). A docs sentence naming a test that does not exist is a false claim. This scans
each root for a file named like the token, or a `def <token>` / `class <token>` in any .py file, and
prints the tokens found nowhere.

Usage:
    2026-11-07_flood4_docs_test_name_xcheck.py --names <file, one token per line> --root <dir> [--root <dir> ...]
Exit 0 always; the report is the output.
"""

import argparse
import os
import re
import sys

SKIP_DIRS = set([".git", "node_modules", "__pycache__", ".venv", "venv", "tmp", ".mypy_cache", ".pytest_cache"])


def scan(root, defs, files):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".claude")]
        for fn in filenames:
            files.setdefault(fn, []).append(os.path.join(dirpath, fn))
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            for m in re.finditer(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M):
                defs.setdefault(m.group(1), []).append(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", required=True)
    ap.add_argument("--root", action="append", required=True)
    args = ap.parse_args()
    with open(args.names, encoding="utf-8") as fh:
        names = [ln.strip() for ln in fh if ln.strip()]
    defs = dict()
    files = dict()
    for root in args.root:
        scan(root, defs, files)
    missing = []
    for tok in names:
        base = tok.split("/")[-1]
        if base.endswith(".py"):
            hit = files.get(base)
        else:
            hit = defs.get(base) or files.get(base + ".py")
        if hit:
            print("FOUND   %s -> %s" % (tok, hit[0]))
        else:
            missing.append(tok)
            print("MISSING %s" % tok)
    print("--- %d tokens, %d missing" % (len(names), len(missing)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
