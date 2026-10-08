#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. Print the hunk layout of saved PR diffs: per file, each hunk's header
# and its first added line, so insertion points shared by several PRs are visible at a glance.
# Usage: 2026-10-08_flood3_canopy_docs_hunks.py <diff> [<diff> ...]
"""Hunk layout of saved unified diffs."""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    for name in argv:
        print(f"######## {Path(name).name}")
        cur_file = None
        first_add_pending = False
        for line in Path(name).read_text(encoding="utf-8").splitlines():
            if line.startswith("+++ b/"):
                cur_file = line[6:]
                print(f"  FILE {cur_file}")
            elif line.startswith("@@"):
                print(f"    {line[:160]}")
                first_add_pending = True
            elif first_add_pending and line.startswith("+") and not line.startswith("+++"):
                print(f"        + {line[1:120]}")
                first_add_pending = False
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
