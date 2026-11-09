#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only encoding screen of the lines a carrier adds (git diff -U0 origin/main -- <paths>):
#               HTML entities, smart quotes, non-breaking / zero-width / odd spaces, and every non-ASCII code
#               point, each compared with how often main's copy of the same file already uses it. Also checks
#               the file is valid UTF-8, has no BOM, no CRLF, no tabs in added lines, and no trailing whitespace.
"""
Read-only encoding screen of the lines a carrier adds against origin/main: HTML entities, smart quotes, odd or zero-width spaces and every non-ASCII code point (each compared with main's own use), plus UTF-8 validity, BOM, CRLF, tabs and trailing whitespace.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import collections
import re
import subprocess
import sys
import unicodedata

paths = sys.argv[1:]
ENTITY = re.compile(r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")
SUSPECT = {
    "‘": "LEFT SINGLE QUOTE",
    "’": "RIGHT SINGLE QUOTE",
    "“": "LEFT DOUBLE QUOTE",
    "”": "RIGHT DOUBLE QUOTE",
    " ": "NBSP",
    " ": "NARROW NBSP",
    " ": "THIN SPACE",
    "​": "ZERO WIDTH SPACE",
    "‌": "ZWNJ",
    "‍": "ZWJ",
    "﻿": "BOM/ZWNBSP",
    "⁠": "WORD JOINER",
    "­": "SOFT HYPHEN",
}
for p in paths:
    with open(p, "rb") as fh:
        raw = fh.read()
    problems = []
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        problems.append(f"NOT UTF-8: {exc}")
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("BOM at start")
    if b"\r\n" in raw:
        problems.append(f"CRLF count {raw.count(b'\r\n')}")
    main = subprocess.run(["git", "show", f"origin/main:{p}"], capture_output=True, text=True, check=True).stdout
    main_counts = collections.Counter(ch for ch in main if ord(ch) > 127)
    main_entities = collections.Counter(ENTITY.findall(main))
    diff = subprocess.run(["git", "diff", "-U0", "origin/main", "--", p], capture_output=True, text=True, check=True).stdout
    added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    add_counts = collections.Counter(ch for ln in added for ch in ln if ord(ch) > 127)
    add_entities = collections.Counter(e for ln in added for e in ENTITY.findall(ln))
    tabs = sum(1 for ln in added if "\t" in ln)
    trailing = [ln[:80] for ln in added if ln != ln.rstrip()]
    print(f"== {p}: {len(added)} added lines; {' ; '.join(problems) if problems else 'utf-8 ok, no BOM, no CRLF'}")
    print(f"   tabs in added lines: {tabs}; trailing whitespace in added lines: {len(trailing)}")
    for t in trailing[:5]:
        print(f"     trailing: {t!r}")
    print(f"   HTML entities in added lines: {dict(add_entities)} (main has {dict(main_entities)})")
    for ch, n in sorted(add_counts.items(), key=lambda x: -x[1]):
        name = SUSPECT.get(ch) or unicodedata.name(ch, f"U+{ord(ch):04X}")
        flag = "NEW-TO-FILE" if main_counts.get(ch, 0) == 0 else ""
        sus = "SUSPECT" if ch in SUSPECT else ""
        print(f"   U+{ord(ch):04X} {name:<40} added={n:<4} main={main_counts.get(ch, 0):<5} {flag} {sus}")
        if flag or sus:
            for ln in added:
                if ch in ln:
                    i = ln.index(ch)
                    print(f"       e.g. ...{ln[max(0, i - 50):i + 30]!r}")
                    break
